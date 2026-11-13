"""Strict, offline MongoDB export -> relational import planning and execution.

This is an ETL tool, never an application database adapter. It accepts a frozen
export, expands known documents into explicit relational rows, and refuses
unknown fields or invalid references. A dry-run creates only an in-memory
SQLite validation database; it never connects to or writes the target MySQL.

Production execution requires Alembic, a stopped application, an empty target
(or the exact same interrupted run), and the MySQL 5.7 integrity guard audit.
No password, token, medical measurement, address or provider payload is emitted
in reports/provenance. Original exports must remain in the operator's backup.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import uuid
from typing import Any, Iterable

from sqlalchemy import (
    Boolean, CheckConstraint, Integer, JSON, Numeric, String, Text,
    UniqueConstraint, create_engine, event, func, select, text,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .base import Base, UTCDateTime, utcnow
from . import models as M
from .database import EXPECTED_SCHEMA_REVISION


TABLES = Base.metadata.tables
COLLECTION_TABLES = {
    "users": "users", "user_sessions": "user_sessions", "addresses": "addresses",
    "products": "products", "categories": "categories", "brands": "brands",
    "lens_indexes": "lens_indexes", "cart_items": "cart_items", "wishlists": "wishlists",
    "product_reviews": "product_reviews", "product_subscriptions": "product_subscriptions",
    "orders": "orders", "order_status_logs": "order_status_logs",
    "stock_reservations": "stock_reservations", "stock_movements": "stock_movements",
    "payment_logs": "payment_logs", "shipment_logs": "shipment_logs",
    "vouchers": "vouchers", "flash_sales": "flash_sales", "games": "games",
    "game_scores": "game_scores", "roulette_rewards": "roulette_rewards",
    "roulette_spins": "roulette_spins", "point_logs": "point_logs",
    "newsletter_subscribers": "newsletter_subscribers", "newsletter_campaigns": "newsletter_campaigns",
    "articles": "articles", "article_categories": "article_categories",
    "product_knowledges": "product_knowledges", "cms_pages": "cms_pages",
    "faq_categories": "faq_categories", "faqs": "faqs", "cms_banners": "banners",
    "banners_v2": "banners", "contact_settings": "contact_settings",
    "contact_messages": "contact_messages", "uploads": "uploads",
}
COLLECTIONS = tuple(sorted(COLLECTION_TABLES))
IMPORT_NAMESPACE = uuid.UUID("f47dc882-4ae7-4ce9-8c48-d276a9bb1c90")
MIGRATION_TABLES = {"migration_runs", "migration_records", "migration_issues"}


class ImportRejected(ValueError):
    """A safe, non-payload-bearing import refusal."""


def stable_id(*parts: Any) -> str:
    return "imp_" + uuid.uuid5(IMPORT_NAMESPACE, json.dumps(parts, ensure_ascii=False)).hex


def json_value(value: Any) -> Any:
    """JSON-safe snapshots keep Decimal values as exact decimal strings."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    return value


def canonical(value: Any) -> str:
    return json.dumps(json_value(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def checksum(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _reject_constant(_: str) -> None:
    raise ValueError("Non-finite JSON number")


def decode_extended_json(value: Any) -> Any:
    """Understand mongoexport's canonical scalar wrappers, not arbitrary BSON.

    Extended BSON kinds not present in the audited schema are explicitly
    rejected; they are never silently flattened or stringified.
    """
    if isinstance(value, list):
        return [decode_extended_json(v) for v in value]
    if not isinstance(value, dict):
        return value
    if len(value) == 1:
        key, raw = next(iter(value.items()))
        if key == "$oid":
            if not isinstance(raw, str) or not re.fullmatch(r"[a-fA-F0-9]{24}", raw):
                raise ValueError("Invalid ObjectId")
            return raw.lower()
        if key in {"$numberInt", "$numberLong"}:
            if not isinstance(raw, str) or not re.fullmatch(r"-?\d+", raw):
                raise ValueError("Invalid extended integer")
            return int(raw)
        if key in {"$numberDecimal", "$numberDouble"}:
            number = Decimal(str(raw))
            if not number.is_finite():
                raise ValueError("Non-finite extended number")
            return number
        if key == "$date":
            if isinstance(raw, dict) and set(raw) == {"$numberLong"}:
                milliseconds = int(raw["$numberLong"])
                return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=milliseconds)
            if isinstance(raw, str):
                return parse_datetime(raw)
            raise ValueError("Invalid extended date")
    if any(str(k).startswith("$") for k in value):
        raise ValueError("Unsupported Extended JSON type")
    return {k: decode_extended_json(v) for k, v in value.items()}


def parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("Timestamp must be an ISO string or Extended JSON date")
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamp has no source timezone")
    result = result.astimezone(timezone.utc)
    if result.year < 1000:
        raise ValueError("Timestamp is outside MySQL DATETIME range")
    return result


@dataclass(frozen=True)
class Issue:
    collection: str
    source_id: str
    field: str
    code: str
    severity: str
    explanation: str


@dataclass(frozen=True)
class Source:
    collection: str
    source_id: str
    checksum: str
    document: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class TargetRow:
    table: str
    values: dict[str, Any] = field(repr=False)
    source: Source = field(repr=False)

    @property
    def key(self) -> dict[str, Any]:
        return {c.name: self.values[c.name] for c in TABLES[self.table].primary_key}

    @property
    def key_text(self) -> str:
        return canonical(self.key)

    @property
    def provenance_id(self) -> str:
        return stable_id(self.source.collection, self.source.source_id, self.table, self.key_text)


@dataclass
class ImportPlan:
    sources: list[Source]
    rows: list[TargetRow]
    issues: list[Issue]
    export_checksum: str
    partial: bool = False
    reconciliation: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    def report(self) -> dict[str, Any]:
        # IDs are references only; no source values enter explanations/report.
        return {
            "format_version": 1, "target": "MySQL 5.7.24-log",
            "schema_revision": EXPECTED_SCHEMA_REVISION,
            "export_checksum": self.export_checksum, "partial_dataset": self.partial,
            "ready_for_apply": not self.errors,
            "warning_acknowledgement_required": bool(self.warnings),
            "source_records": len(self.sources), "target_rows": len(self.rows),
            "source_counts": {c: sum(s.collection == c for s in self.sources) for c in COLLECTIONS},
            "target_counts": dict(sorted(Counter(r.table for r in self.rows).items())),
            "errors": len(self.errors), "warnings": len(self.warnings),
            "issues": [asdict(i) for i in self.issues],
            "reconciliation": self.reconciliation,
            "validation_scope": "Offline typed/FK/unique/CHECK and source accounting checks; target MySQL collation and runtime locking require server validation.",
        }


def load_export(directory: str | Path, *, allow_partial: bool = False) -> tuple[dict[str, list[dict]], list[Issue]]:
    """Read one <collection>.json or .jsonl file per audited collection.

    An empty array file is evidence of an intentionally empty collection.
    Missing files otherwise block a full migration; an explicit partial mode
    can be used for a reviewed subset whose references are self-contained.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ImportRejected("Export directory does not exist")
    documents: dict[str, list[dict]] = {}
    issues: list[Issue] = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in {".bson", ".gz"}:
            issues.append(Issue("inventory", path.name, "file", "unsupported_export_format", "error",
                                "Use uncompressed canonical mongoexport JSON/JSONL; BSON archives are not parsed."))
        elif path.is_file() and path.suffix in {".json", ".jsonl", ".ndjson"} and path.stem not in COLLECTION_TABLES:
            issues.append(Issue("inventory", path.name, "file", "unknown_collection", "error",
                                "An unrecognized collection/file needs an explicit mapping before import."))
    for coll in COLLECTIONS:
        paths = [root / f"{coll}{suffix}" for suffix in (".json", ".jsonl", ".ndjson")]
        present = [p for p in paths if p.exists()]
        if not present:
            if not allow_partial:
                issues.append(Issue(coll, "inventory", "file", "missing_collection_file", "error",
                                    "Supply an export file, including [] for an intentionally empty collection."))
            documents[coll] = []
            continue
        if len(present) != 1 or present[0].is_symlink():
            issues.append(Issue(coll, "inventory", "file", "ambiguous_collection_file", "error",
                                "Exactly one regular, non-symlink JSON/JSONL file is required."))
            documents[coll] = []
            continue
        try:
            raw = present[0].read_text(encoding="utf-8-sig")
            if raw.lstrip().startswith("["):
                values = json.loads(raw, parse_float=Decimal, parse_constant=_reject_constant)
            else:
                values = [json.loads(line, parse_float=Decimal, parse_constant=_reject_constant)
                          for line in raw.splitlines() if line.strip()]
            decoded = decode_extended_json(values)
            if not isinstance(decoded, list) or any(not isinstance(v, dict) for v in decoded):
                raise ValueError("Collection is not an array of documents")
            documents[coll] = decoded
        except (UnicodeError, ValueError, TypeError, OSError, OverflowError, InvalidOperation):
            documents[coll] = []
            issues.append(Issue(coll, "inventory", "file", "invalid_export", "error",
                                "Malformed JSON/Extended JSON, unsupported BSON type, or unreadable export file."))
    if allow_partial:
        issues.append(Issue("inventory", "inventory", "files", "partial_dataset", "warning",
                            "Missing collection files are explicitly treated as empty; this is not proof of a complete source backup."))
    return documents, issues


EXTRA_FIELDS = {
    "categories": {"parent_id", "level", "category_type"},
    "users": {"permissions"}, "user_sessions": {"session_token"},
    "products": {"variants", "category_ids", "segments", "badges", "gallery"},
    "cart_items": {"prescription"},
    "orders": {"items", "address", "roulette_reward_id", "payment_method", "payment_url",
               "tracking_number", "carrier_status", "shipment_checked_at"},
    "order_status_logs": {"admin"}, "stock_movements": {"admin"},
    "flash_sales": {"items"}, "roulette_spins": {"used_order_id"},
    "product_reviews": {"images", "is_approved"}, "articles": {"tags"},
    "product_knowledges": {"pros", "cons", "related_product_ids", "is_published"},
    "cms_banners": {"image", "link"}, "banners_v2": {"reference_id"},
    "contact_settings": {"whatsapp"},
}


def _data_fields(table: str) -> set[str]:
    return {c.name for c in TABLES[table].columns if c.computed is None}


class Planner:
    def __init__(self, documents: dict[str, list[dict]], *, issues: Iterable[Issue] = (), partial: bool = False):
        self.documents = documents
        self.sources: list[Source] = []
        self.rows: list[TargetRow] = []
        self.issues = list(issues)
        self.partial = partial
        self.by_application_id: dict[str, dict[str, Source]] = defaultdict(dict)

    def issue(self, source: Source, field: str, code: str, explanation: str, severity: str = "error") -> None:
        self.issues.append(Issue(source.collection, source.source_id, field, code, severity, explanation))

    def unknown(self, source: Source, data: dict, allowed: set[str], prefix: str = "") -> None:
        for key in sorted(set(data) - allowed):
            self.issue(source, (prefix + key)[:128], "unknown_field", "This field has no reviewed relational mapping; it was not silently discarded.")

    def add(self, source: Source, table: str, values: dict, *, inherited_time: Any = None) -> TargetRow:
        result: dict[str, Any] = {}
        columns = TABLES[table].columns
        for key in values:
            if key not in columns or columns[key].computed is not None:
                self.issue(source, f"{table}.{key}"[:128], "unmapped_target_field", "The target field is not a writable relational column.")
        for col in columns:
            if col.computed is not None:
                continue
            value = values.get(col.name)
            if col.name not in values:
                if isinstance(col.type, UTCDateTime) and col.name in {"created_at", "updated_at"}:
                    value = inherited_time
                    if value is None:
                        self.issue(source, f"{table}.{col.name}", "missing_timestamp", "An original timestamp is required; import never substitutes the current time.")
                        result[col.name] = None
                        continue
                elif col.server_default is not None:
                    arg = str(col.server_default.arg)
                    if arg in {"('')", "''"}:
                        value = ""
                    elif arg.startswith("'") and arg.endswith("'"):
                        value = arg[1:-1]
                    else:
                        value = arg
                elif col.default is not None and col.default.is_scalar:
                    # Honor reviewed literal defaults such as PointLog.note=''.
                    # Never invoke callable ID/time defaults during conversion.
                    value = col.default.arg
                elif col.nullable:
                    value = None
                else:
                    self.issue(source, f"{table}.{col.name}", "missing_required_field", "Required source data is missing; no business value was invented.")
                    result[col.name] = None
                    continue
            if value is None:
                if not col.nullable:
                    self.issue(source, f"{table}.{col.name}", "null_required_field", "Required column is null.")
                result[col.name] = None
                continue
            try:
                if isinstance(col.type, UTCDateTime):
                    value = parse_datetime(value)
                elif isinstance(col.type, Boolean):
                    if value in {"0", "1"} and col.name not in values:
                        value = value == "1"
                    elif not isinstance(value, bool):
                        raise ValueError("Boolean required")
                elif isinstance(col.type, Numeric):
                    if isinstance(value, bool):
                        raise ValueError("Numeric required")
                    number = Decimal(str(value))
                    if not number.is_finite():
                        raise ValueError("Finite numeric required")
                    quantum = Decimal(1).scaleb(-col.type.scale)
                    value = number.quantize(quantum, rounding=ROUND_HALF_UP)
                    if value != number:
                        self.issue(source, f"{table}.{col.name}", "decimal_rounded", "Value rounded to target scale with Decimal ROUND_HALF_UP; review the source before acceptance.", "warning")
                    if abs(value) >= Decimal(10) ** (col.type.precision - col.type.scale):
                        raise ValueError("Decimal overflow")
                elif isinstance(col.type, Integer):
                    if isinstance(value, bool):
                        raise ValueError("Integer required")
                    number = Decimal(str(value))
                    if not number.is_finite() or number != number.to_integral_value():
                        raise ValueError("Integer required")
                    value = int(number)
                    # MySQL signed integral range; SmallInteger and BigInteger matter.
                    bits = 16 if col.type.__class__.__name__ == "SmallInteger" else 64 if col.type.__class__.__name__ == "BigInteger" else 32
                    if not -(2 ** (bits - 1)) <= value < 2 ** (bits - 1):
                        raise ValueError("Integer overflow")
                elif isinstance(col.type, JSON):
                    value = json_value(value)
                    canonical(value)
                    if table in {"payment_logs", "shipment_logs"} and _contains_secret(value):
                        self.issue(source, f"{table}.{col.name}", "provider_secret_present", "Provider snapshot contains a credential-like key; supply an explicitly redacted export.")
                elif isinstance(col.type, (String, Text)):
                    if not isinstance(value, str):
                        raise ValueError("String required")
                    if "\x00" in value:
                        raise ValueError("Null byte not permitted")
                    if col.type.length is not None and len(value) > col.type.length:
                        raise ValueError("String too long")
                    if col.primary_key and not value:
                        raise ValueError("Empty identifier")
                result[col.name] = value
            except (ValueError, TypeError, InvalidOperation, OverflowError):
                self.issue(source, f"{table}.{col.name}", "invalid_column_value", "Type, precision, length, timezone, or numeric range does not fit the target column.")
                result[col.name] = None
        target = TargetRow(table, result, source)
        self.rows.append(target)
        if len(target.key_text) > 255:
            self.issue(source, table, "provenance_key_too_long", "Composite key exceeds the provenance column; review schema before importing this record.")
        return target

    def base(self, source: Source) -> dict[str, Any]:
        table = COLLECTION_TABLES[source.collection]
        self.unknown(source, source.document, _data_fields(table) | EXTRA_FIELDS.get(source.collection, set()) | {"_id"})
        return {k: v for k, v in source.document.items() if k in _data_fields(table)}

    def list(self, source: Source, name: str) -> list[Any]:
        raw = source.document.get(name, [])
        if not isinstance(raw, list):
            self.issue(source, name, "array_required", "Expected an array; null and scalar values are not silently converted.")
            return []
        return raw

    def init_sources(self) -> None:
        for collection in sorted(self.documents):
            if collection not in COLLECTION_TABLES:
                self.issues.append(Issue(collection, "inventory", "collection", "unknown_collection", "error", "No mapping exists for this collection."))
                continue
            seen: set[str] = set()
            for index, doc in enumerate(self.documents[collection]):
                primary = "user_id" if collection == "users" else "session_id" if collection == "user_sessions" else "id"
                app_id = doc.get(primary)
                raw_id = doc.get("_id", app_id)
                if not isinstance(raw_id, (str, int)) or isinstance(raw_id, bool) or not str(raw_id):
                    raw_id = f"invalid-index-{index}"
                source = Source(collection, str(raw_id), checksum(doc), doc)
                self.sources.append(source)
                if len(source.source_id) > 191:
                    self.issue(source, "_id", "source_id_too_long", "Source identity exceeds provenance capacity.")
                if source.source_id in seen:
                    self.issue(source, "_id", "duplicate_source_id", "Two source records have the same provenance identity.")
                seen.add(source.source_id)
                if not isinstance(app_id, str) or not app_id or len(app_id) > 64:
                    self.issue(source, primary, "missing_application_id", "Original application ID must be a nonempty string of at most 64 characters; Mongo _id is not substituted.")
                elif app_id in self.by_application_id[collection]:
                    self.issue(source, primary, "duplicate_application_id", "Application identifier occurs more than once.")
                else:
                    self.by_application_id[collection][app_id] = source

    def build(self) -> ImportPlan:
        self.init_sources()
        for source in self.sources:
            try:
                self.convert(source)
            except (TypeError, KeyError, ValueError, InvalidOperation, OverflowError):
                self.issue(source, "document", "invalid_document_shape", "Nested document shape or scalar is invalid; review the original source record.")
        plan = ImportPlan(self.sources, self.rows, self.issues,
                          checksum([(s.collection, s.source_id, s.checksum) for s in sorted(self.sources, key=lambda s: (s.collection, s.source_id))]), self.partial)
        self.validate(plan)
        return plan

    def convert(self, source: Source) -> None:
        collection, doc = source.collection, source.document
        data = self.base(source)
        inherited_time = doc.get("created_at", doc.get("updated_at"))
        if collection == "categories":
            data.setdefault("group_type", "collection")
            data["code"] = data.get("code") or "legacy-" + checksum(doc.get("id"))[:32]
        if collection == "users":
            self.add(source, "users", data, inherited_time=inherited_time)
            for permission in self.list(source, "permissions"):
                self.add(source, "user_permissions", {"user_id": doc.get("user_id"), "permission": permission})
        elif collection == "user_sessions":
            token = doc.get("session_token")
            if not isinstance(token, str) or not token:
                self.issue(source, "session_token", "invalid_session_token", "A source session token is required for deterministic hashing.")
            else:
                expected = hashlib.sha256(token.encode()).hexdigest()
                if "token_hash" in data and data["token_hash"] != expected:
                    self.issue(source, "token_hash", "session_hash_mismatch", "Existing token hash disagrees with the source token.")
                data["token_hash"] = expected
            self.add(source, "user_sessions", data, inherited_time=inherited_time)
        elif collection == "products":
            self.add(source, "products", data, inherited_time=inherited_time)
            for index, variant in enumerate(self.list(source, "variants")):
                if not isinstance(variant, dict):
                    self.issue(source, f"variants[{index}]", "object_required", "Variant must be an object.")
                    continue
                self.unknown(source, variant, _data_fields("product_variants") - {"product_id"}, f"variants[{index}].")
                if "sort_order" in variant and not _matches_position(variant["sort_order"], index):
                    self.issue(source, f"variants[{index}].sort_order", "conflicting_array_order", "Explicit variant sorting disagrees with the source array order; neither order is silently preferred.")
                self.add(source, "product_variants", {**variant, "product_id": doc.get("id"), "sort_order": index}, inherited_time=inherited_time)
            for field, table, value_key in (("category_ids", "product_categories", "category_id"),
                                            ("segments", "product_segments", "segment"), ("badges", "product_badges", "badge")):
                for value in self.list(source, field):
                    self.add(source, table, {"product_id": doc.get("id"), value_key: value})
            for index, image in enumerate(self.list(source, "gallery")):
                self.add(source, "product_images", {"product_id": doc.get("id"), "sort_order": index, "image_url": image})
        elif collection == "cart_items":
            rx = doc.get("prescription")
            if rx is not None:
                generated_rx_id = self.prescription(source, rx, doc.get("user_id"), "cart", inherited_time)
                if "prescription_id" in data and data["prescription_id"] != generated_rx_id:
                    self.issue(source, "prescription_id", "conflicting_prescription_reference", "Explicit prescription reference differs from the deterministically normalized inline prescription; resolve it before import.")
                data["prescription_id"] = generated_rx_id
            self.add(source, "cart_items", data, inherited_time=inherited_time)
        elif collection == "orders":
            self.order(source, data)
        elif collection in {"stock_movements", "order_status_logs"}:
            if "admin" in doc:
                if "admin_id" in data and data["admin_id"] != doc["admin"]:
                    self.issue(source, "admin", "conflicting_alias", "Legacy and relational administrator references disagree.")
                data["admin_id"] = doc["admin"]
            self.add(source, collection, data, inherited_time=inherited_time)
        elif collection == "flash_sales":
            self.add(source, "flash_sales", data, inherited_time=inherited_time)
            for i, item in enumerate(self.list(source, "items")):
                self.unknown(source, item, {"product_id", "flash_price", "quota", "sold", "reserved", "is_active", "id"}, f"items[{i}].")
                self.add(source, "flash_sale_items", {**item, "id": item["id"] if "id" in item else stable_id(collection, doc.get("id"), "item", i), "flash_sale_id": doc.get("id")})
        elif collection == "roulette_spins":
            self.add(source, "roulette_spins", data, inherited_time=inherited_time)
            used_order = doc.get("used_order_id")
            if used_order:
                order_source = self.by_application_id["orders"].get(used_order)
                if not order_source or order_source.document.get("roulette_reward_id") != doc.get("id"):
                    self.issue(source, "used_order_id", "roulette_order_link_mismatch", "Spin's used-order link is missing or disagrees with the order's spin reference.")
        elif collection == "product_reviews":
            self.review(source, data)
        elif collection == "articles":
            self.add(source, "articles", data, inherited_time=inherited_time)
            for i, tag in enumerate(self.list(source, "tags")):
                self.add(source, "article_tags", {"article_id": doc.get("id"), "tag": tag, "sort_order": i})
        elif collection == "product_knowledges":
            if "is_published" in doc:
                if not isinstance(doc["is_published"], bool):
                    self.issue(source, "is_published", "boolean_required", "Publication flag must be boolean.")
                status = "published" if doc["is_published"] else "unpublished"
                if "status" in data and (data["status"] == "published") != doc["is_published"]:
                    self.issue(source, "status", "publication_conflict", "Publication status and old boolean disagree.")
                data.setdefault("status", status)
            self.add(source, "product_knowledges", data, inherited_time=inherited_time)
            for field, kind in (("pros", "pro"), ("cons", "con")):
                for i, body in enumerate(self.list(source, field)):
                    self.add(source, "product_knowledge_bullets", {"knowledge_id": doc.get("id"), "kind": kind, "sort_order": i, "body": body})
            for i, product_id in enumerate(self.list(source, "related_product_ids")):
                self.add(source, "product_knowledge_products", {"knowledge_id": doc.get("id"), "product_id": product_id, "sort_order": i})
        elif collection in {"cms_banners", "banners_v2"}:
            if collection == "cms_banners":
                for legacy, relational in (("image", "image_desktop"), ("link", "link_url")):
                    if legacy in doc:
                        if relational in data and data[relational] != doc[legacy]:
                            self.issue(source, legacy, "conflicting_banner_alias", "Legacy and relational banner fields disagree; an explicit mapping decision is required.")
                        else:
                            data[relational] = doc[legacy]
                data.setdefault("link_url", "/")
                if "link_type" not in data:
                    data["link_type"] = "external" if str(data["link_url"]).startswith(("https://", "http://")) else "internal"
            reference = doc.get("reference_id")
            if reference is not None:
                field_name = {"product": "link_product_id", "category": "link_category_id", "article": "link_article_id", "flash_sale": "link_flash_sale_id"}.get(data.get("link_type"))
                if field_name:
                    if data.get(field_name) not in {None, reference}:
                        self.issue(source, "reference_id", "conflicting_alias", "Banner references disagree.")
                    data[field_name] = reference
                else:
                    self.issue(source, "reference_id", "unmapped_banner_reference", "Reference ID is set for a banner type that has no matching relational reference.")
            # Both collections share the same ID space; collisions block instead
            # of dropping a banner or secretly remapping public IDs.
            self.add(source, "banners", data, inherited_time=inherited_time)
        elif collection == "contact_settings":
            self.add(source, "contact_settings", data, inherited_time=inherited_time)
            if "whatsapp" in doc:
                # Empty text is deliberately empty; no new marketing text invented.
                self.add(source, "whatsapp_settings", {"id": 1, "phone": doc["whatsapp"], "default_text": "", "is_enabled": False, "updated_at": doc.get("updated_at")})
        else:
            self.add(source, COLLECTION_TABLES[collection], data, inherited_time=inherited_time)

    def prescription(self, source: Source, rx: Any, user_id: str, scope: str, when: Any) -> str:
        rx_id = stable_id(source.collection, source.document.get("id"), "prescription", scope)
        if not isinstance(rx, dict):
            self.issue(source, "prescription", "object_required", "Prescription must be an object.")
            return rx_id
        allowed = {"od_sph", "os_sph", "od_cyl", "os_cyl", "od_axis", "os_axis", "od_add", "os_add", "pd", "pd_total", "pd_right", "pd_left", "notes", "attachment_upload_id"}
        self.unknown(source, rx, allowed, "prescription.")
        def measured(key):
            value = rx.get(key)
            return None if value is None or value == "" else value
        if measured("pd") is not None and measured("pd_total") is not None and str(rx["pd"]) != str(rx["pd_total"]):
            self.issue(source, "prescription.pd", "conflicting_alias", "PD aliases disagree; source must be resolved explicitly.")
        self.add(source, "prescriptions", {"id": rx_id, "user_id": user_id,
                 "pd_total": measured("pd_total") if measured("pd_total") is not None else measured("pd"),
                 "pd_right": measured("pd_right"), "pd_left": measured("pd_left"),
                 "notes": rx.get("notes"), "attachment_upload_id": rx.get("attachment_upload_id"),
                 "is_order_snapshot": scope != "cart"}, inherited_time=when)
        for eye, prefix in (("right", "od"), ("left", "os")):
            values = {key: measured(f"{prefix}_{key}") for key in ("sph", "cyl", "axis", "add")}
            if any(v is not None for v in values.values()):
                self.add(source, "prescription_eyes", {"prescription_id": rx_id, "eye": eye, **values})
        return rx_id

    def order(self, source: Source, data: dict) -> None:
        doc = source.document
        when = doc.get("created_at")
        self.add(source, "orders", data, inherited_time=when)
        address = doc.get("address")
        if not isinstance(address, dict):
            self.issue(source, "address", "missing_order_address", "Original delivery-address snapshot is required; current address-book data is never substituted.")
        else:
            self.unknown(source, address, _data_fields("addresses") | {"_id"}, "address.")
            if address.get("user_id") not in {None, doc.get("user_id")}:
                self.issue(source, "address.user_id", "address_owner_mismatch", "Historical address owner does not match order owner.")
            snapshot = {k: v for k, v in address.items() if k in _data_fields("order_addresses")}
            snapshot.update(order_id=doc.get("id"), source_address_id=address.get("id"),
                            source_created_at=address.get("created_at"), source_is_default=address.get("is_default"))
            self.add(source, "order_addresses", snapshot)
        items = self.list(source, "items")
        if not items:
            self.issue(source, "items", "empty_order", "Order has no original purchase lines.")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                self.issue(source, f"items[{index}]", "object_required", "Order item must be an object.")
                continue
            self.unknown(source, item, _data_fields("order_items") - {"order_id", "sort_order"}, f"items[{index}].")
            self.add(source, "order_items", {**item, "id": item["id"] if "id" in item else stable_id("orders", doc.get("id"), "item", index), "order_id": doc.get("id"), "sort_order": index})
        self.issue(source, "items", "legacy_bundle_details_unknown", "Legacy purchase lines do not record separate lens/index/prescription snapshots; these remain unknown and were not reconstructed from today's catalog.", "warning")
        # Re-home known order fields into deterministic integration snapshots.
        pay_logs = [s for s in self.sources if s.collection == "payment_logs" and s.document.get("order_id") == doc.get("id")]
        providers = {s.document.get("provider") for s in pay_logs if s.document.get("provider")}
        provider = next(iter(providers)) if len(providers) == 1 else "legacy-import"
        self.add(source, "payments", {"id": stable_id("orders", doc.get("id"), "payment"),
                 "order_id": doc.get("id"), "provider": provider, "request_id": stable_id("payment-request", doc.get("id")),
                 "merchant_reference": doc.get("order_number"), "amount": doc.get("total"), "currency": doc.get("currency", "IDR"),
                 "method": doc.get("payment_method"), "payment_url": doc.get("payment_url"),
                 "status": doc.get("payment_status", "pending"), "expires_at": doc.get("reservation_expires_at"),
                 "created_at": when, "updated_at": doc.get("updated_at", when)})
        if len(providers) > 1:
            self.issue(source, "payment_method", "multiple_payment_providers", "Historical logs name multiple providers; order snapshot uses legacy-import and logs stay independent.", "warning")
        if any(doc.get(k) is not None for k in ("tracking_number", "carrier_status", "shipment_checked_at")) or doc.get("shipment_status", "pending") != "pending":
            ship_logs = [s for s in self.sources if s.collection == "shipment_logs" and s.document.get("order_id") == doc.get("id")]
            providers = {s.document.get("provider") for s in ship_logs if s.document.get("provider")}
            provider = next(iter(providers)) if len(providers) == 1 else "legacy-import"
            self.add(source, "shipments", {"id": stable_id("orders", doc.get("id"), "shipment"), "order_id": doc.get("id"),
                     "provider": provider, "request_id": stable_id("shipment-request", doc.get("id")),
                     "courier_code": doc.get("shipping_courier"), "service_code": doc.get("shipping_service"),
                     "tracking_number": doc.get("tracking_number"), "carrier_status": doc.get("carrier_status"),
                     "last_checked_at": doc.get("shipment_checked_at"), "cost": doc.get("shipping_cost"),
                     "status": doc.get("shipment_status", "pending"), "currency": doc.get("currency", "IDR"),
                     "created_at": when, "updated_at": doc.get("updated_at", when)})
        state = "reserved" if doc.get("status", "pending_payment") == "pending_payment" else "released" if doc.get("status") in {"expired", "cancelled", "refunded"} else "redeemed"
        if doc.get("voucher_code"):
            matches = [s for s in self.sources if s.collection == "vouchers" and _ci(s.document.get("code", "")) == _ci(doc["voucher_code"])]
            if len(matches) != 1:
                self.issue(source, "voucher_code", "voucher_reference_missing", "Voucher code must match exactly one exported voucher.")
            else:
                self.add(source, "voucher_redemptions", {"id": stable_id("orders", doc.get("id"), "voucher"),
                         "voucher_id": matches[0].document["id"], "order_id": doc.get("id"), "user_id": doc.get("user_id"),
                         "discount_amount": doc.get("voucher_discount", 0), "status": state, "created_at": when})
        if doc.get("roulette_reward_id"):
            spin_source = self.by_application_id["roulette_spins"].get(doc["roulette_reward_id"])
            if not spin_source:
                self.issue(source, "roulette_reward_id", "spin_reference_missing", "Order field must point to an exported roulette spin, not a reward definition.")
            elif spin_source.document.get("user_id") != doc.get("user_id"):
                self.issue(source, "roulette_reward_id", "spin_owner_mismatch", "Roulette spin belongs to a different customer.")
            else:
                self.add(source, "roulette_redemptions", {"id": stable_id("orders", doc.get("id"), "roulette"),
                         "spin_id": doc["roulette_reward_id"], "order_id": doc.get("id"), "user_id": doc.get("user_id"),
                         "discount_amount": doc.get("roulette_discount", 0), "status": state, "created_at": when})

    def review(self, source: Source, data: dict) -> None:
        doc = source.document
        flag = doc.get("is_approved")
        if "is_approved" in doc and not isinstance(flag, bool):
            self.issue(source, "is_approved", "boolean_required", "Review approval flag must be boolean.")
        if "status" in data and flag is not None and (data["status"] == "approved") != flag:
            self.issue(source, "status", "review_moderation_conflict", "Legacy is_approved and moderation status disagree; resolve visibility before import.")
        data.setdefault("status", "approved" if flag is True else "pending")
        data["verified_purchase"] = False
        if doc.get("order_id"):
            order_source = self.by_application_id["orders"].get(doc["order_id"])
            if not order_source or order_source.document.get("user_id") != doc.get("user_id"):
                self.issue(source, "order_id", "review_owner_mismatch", "Review's claimed purchase is missing or belongs to another customer.")
            else:
                matches = [(i, it) for i, it in enumerate(order_source.document.get("items", [])) if it.get("product_id") == doc.get("product_id")]
                if not matches:
                    self.issue(source, "order_id", "review_product_not_purchased", "Claimed order does not contain the reviewed product.")
                elif order_source.document.get("status") != "completed":
                    self.issue(source, "order_id", "review_order_incomplete", "Claimed purchase is not completed; verification requires manual review.")
                elif len(matches) > 1:
                    self.issue(source, "order_item_id", "review_purchase_line_ambiguous", "Multiple source lines contain the product; do not invent which line was reviewed.")
                else:
                    index, item = matches[0]
                    matched_item_id = item["id"] if "id" in item else stable_id("orders", doc["order_id"], "item", index)
                    if "order_item_id" in data and data["order_item_id"] != matched_item_id:
                        self.issue(source, "order_item_id", "conflicting_review_line", "Explicit purchase-line reference disagrees with the verified exported order line.")
                    data["order_item_id"] = matched_item_id
                    data["verified_purchase"] = True
        else:
            self.issue(source, "order_id", "legacy_unverified_review", "Legacy review has no purchase reference and stays explicitly unverified.", "warning")
        if "verified_purchase" in doc and (not isinstance(doc["verified_purchase"], bool) or doc["verified_purchase"] != data["verified_purchase"]):
            self.issue(source, "verified_purchase", "conflicting_review_verification", "Explicit verification flag disagrees with verifiable source purchase evidence.")
        self.add(source, "product_reviews", data, inherited_time=doc.get("created_at"))
        for index, image in enumerate(self.list(source, "images")):
            self.add(source, "product_review_images", {"review_id": doc.get("id"), "sort_order": index, "image_url": image})

    def validate(self, plan: ImportPlan) -> None:
        if plan.errors:
            return
        # Stable table order gives valid FK insertion and resumable checkpoints.
        ranks = {table.name: i for i, table in enumerate(Base.metadata.sorted_tables)}
        plan.rows.sort(key=lambda r: (ranks[r.table], r.key_text))
        self._unique_keys()
        if not plan.errors:
            self._portable_integrity(plan)
        if not plan.errors:
            self._accounting(plan)

    def _unique_keys(self) -> None:
        # Conservative accent/case-insensitive comparison catches common
        # utf8mb4_unicode_ci collisions. Actual MySQL remains the final authority.
        seen: dict[tuple, Source] = {}
        for row in self.rows:
            table = TABLES[row.table]
            constraints = [table.primary_key] + [c for c in table.constraints if isinstance(c, UniqueConstraint)]
            for con in constraints:
                names = tuple(col.name for col in con.columns)
                values = tuple(row.values.get(name) for name in names)
                if any(v is None for v in values):
                    continue
                normalized = tuple(_ci(value) if isinstance(value, str) and not _binary_column(table.c[name]) else value.rstrip(" ") if isinstance(value, str) else value for name, value in zip(names, values))
                key = (row.table, names, normalized)
                if key in seen:
                    self.issue(row.source, ",".join(names)[:128], "unique_key_collision", "Duplicate relational key or potential MySQL collation collision; no record was merged, renamed or dropped.")
                seen[key] = row.source

    def _portable_integrity(self, plan: ImportPlan) -> None:
        engine = create_engine("sqlite:///:memory:")
        @event.listens_for(engine, "connect")
        def fks(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        try:
            Base.metadata.create_all(engine)
            with engine.begin() as conn:
                for row in plan.rows:
                    try:
                        conn.execute(TABLES[row.table].insert().values(**row.values))
                    except IntegrityError as exc:
                        # No exception text: values could contain customer data.
                        message = str(getattr(exc, "orig", ""))
                        code = "foreign_key_violation" if "FOREIGN KEY" in message else "row_constraint_violation"
                        self.issue(row.source, row.table, code, "The converted row violates a foreign key, unique key, generated-key rule or row predicate.")
                    except SQLAlchemyError:
                        self.issue(row.source, row.table, "portable_validation_failed", "A typed target value failed portable SQL validation.")
        finally:
            engine.dispose()

    def _accounting(self, plan: ImportPlan) -> None:
        groups: dict[str, list[TargetRow]] = defaultdict(list)
        for row in self.rows:
            groups[row.table].append(row)
        items: dict[str, list[TargetRow]] = defaultdict(list)
        for row in groups["order_items"]:
            items[row.values["order_id"]].append(row)
            v = row.values
            expected = (v["unit_price"] * v["quantity"]).quantize(Decimal(".01"))
            if v["subtotal"] != expected:
                self.issue(row.source, "items.subtotal", "order_line_amount_mismatch", "Historical line total differs from quantity × charged unit price; prices were not recomputed.")
        for row in groups["orders"]:
            v = row.values
            line_sum = sum((r.values["subtotal"] for r in items[v["id"]]), Decimal(0))
            if line_sum != v["subtotal"]:
                self.issue(row.source, "subtotal", "order_subtotal_mismatch", "Order subtotal differs from its historical purchase lines.")
            # This is the old application's formula, including floor before shipping.
            expected = max(Decimal(0), v["subtotal"] - v["voucher_discount"] - v["points_discount"] - v["roulette_discount"]) + v["shipping_cost"]
            if expected != v["total"]:
                self.issue(row.source, "total", "order_total_mismatch", "Stored total differs from the audited legacy checkout formula; no price was silently changed.")
            if v["discount"] or v["flash_sale_discount"]:
                self.issue(row.source, "discount", "legacy_discount_semantics_unknown", "Original checkout never populated these discount fields; their nonzero values require a reviewed pricing mapping.")
            if v["status"] in {"paid", "processing", "shipped", "completed"} and v["payment_status"] != "paid":
                self.issue(row.source, "payment_status", "order_payment_state_mismatch", "Fulfilled order has no matching paid state.")
            if v["status"] == "pending_payment":
                if v["payment_status"] != "pending":
                    self.issue(row.source, "payment_status", "order_payment_state_mismatch", "Pending checkout has a conflicting payment state.")
                if v["reservation_expires_at"] is None:
                    self.issue(row.source, "reservation_expires_at", "missing_reservation_expiry", "Pending order has no original expiry; import must not invent or extend a reservation window.")
        active_reserved = Counter()
        order_reserved = Counter()
        for row in groups["stock_reservations"]:
            v = row.values
            if v["status"] == "active":
                order_reserved[(v["order_id"], v["product_id"], v["variant_id"])] += v["quantity"]
                if v["variant_id"] is None:
                    self.issue(row.source, "variant_id", "active_reservation_variant_missing", "Live reservation has no inventory variant; reconcile the original pending order before import instead of inventing a stock identity.")
            if v["status"] == "active" and v["variant_id"]:
                active_reserved[(v["product_id"], v["variant_id"])] += v["quantity"]
            order = next((o for o in groups["orders"] if o.values["id"] == v["order_id"]), None)
            if v["status"] == "active" and order and order.values["status"] != "pending_payment":
                self.issue(row.source, "status", "reservation_order_state_mismatch", "An active stock reservation belongs to a non-pending order.")
        for order in groups["orders"]:
            if order.values["status"] != "pending_payment":
                continue
            expected = Counter()
            for item in items[order.values["id"]]:
                v = item.values
                expected[(v["order_id"], v["product_id"], v["variant_id"])] += v["quantity"]
            actual = Counter({key: value for key, value in order_reserved.items() if key[0] == order.values["id"]})
            if expected != actual:
                self.issue(order.source, "items", "pending_order_reservation_mismatch", "Pending purchase quantities and active exported reservation quantities disagree.")
        for row in groups["product_variants"]:
            v = row.values
            if v["reserved"] != active_reserved[(v["product_id"], v["id"])]:
                self.issue(row.source, "variants.reserved", "inventory_reservation_mismatch", "Variant reserved count differs from active exported reservations.")
        redemptions = Counter(r.values["voucher_id"] for r in groups["voucher_redemptions"] if r.values["status"] != "released")
        for row in groups["vouchers"]:
            if row.values["used_count"] != redemptions[row.values["id"]]:
                self.issue(row.source, "used_count", "voucher_redemption_mismatch", "Voucher used count differs from pending/paid order references.")
        active_spins = {r.values["spin_id"] for r in groups["roulette_redemptions"] if r.values["status"] != "released"}
        for row in groups["roulette_spins"]:
            v = row.values
            if v["id"] in active_spins and not v["used"]:
                self.issue(row.source, "used", "roulette_redemption_mismatch", "A spin assigned to a live order is marked unused.")
            if v["used"] and v["reward_type"] not in {"points", "nothing"} and v["id"] not in active_spins:
                self.issue(row.source, "used", "roulette_usage_unknown", "A consumed shopping reward has no live exported order association.")
        point_groups: dict[str, list[TargetRow]] = defaultdict(list)
        for row in groups["point_logs"]:
            point_groups[row.values["user_id"]].append(row)
        for user in groups["users"]:
            logs = sorted(point_groups[user.values["user_id"]], key=lambda r: (r.values["created_at"], r.values["id"]))
            if logs:
                for previous, current in zip(logs, logs[1:]):
                    if previous.values["balance_after"] + current.values["delta"] != current.values["balance_after"]:
                        self.issue(current.source, "balance_after", "point_ledger_discontinuity", "Point ledger does not reconcile chronologically; source history needs review.")
                if logs[-1].values["balance_after"] != user.values["points_balance"]:
                    self.issue(user.source, "points_balance", "point_balance_mismatch", "Account points differ from its last exported ledger balance.")
                opening = logs[0].values["balance_after"] - logs[0].values["delta"]
                if opening < 0:
                    self.issue(logs[0].source, "balance_after", "negative_opening_balance", "Earliest point entry implies a negative opening balance.")
                elif opening:
                    self.issue(user.source, "points_balance", "unrecorded_opening_points", "Ledger starts with an opening balance not represented by exported transactions; preserved without fabricating logs.", "warning")
            elif user.values["points_balance"]:
                self.issue(user.source, "points_balance", "points_without_history", "Account balance has no exported point history; preserved without generating earnings.", "warning")
        reviews = Counter(r.values["product_id"] for r in groups["product_reviews"] if r.values["status"] == "approved")
        review_stars = Counter()
        for row in groups["product_reviews"]:
            if row.values["status"] == "approved":
                review_stars[row.values["product_id"]] += row.values["rating"]
        paid_order_ids = {r.values["id"] for r in groups["orders"] if r.values["payment_status"] == "paid"}
        purchased_units = Counter()
        for row in groups["order_items"]:
            if row.values["order_id"] in paid_order_ids:
                purchased_units[row.values["product_id"]] += row.values["quantity"]
        for product in groups["products"]:
            identity = product.values["id"]
            mean = (Decimal(review_stars[identity]) / reviews[identity]).quantize(Decimal(".01"), rounding=ROUND_HALF_UP) if reviews[identity] else Decimal(0)
            if product.values["rating_count"] != reviews[identity] or product.values["rating_avg"] != mean:
                self.issue(product.source, "rating_count", "legacy_rating_cache_unreconciled", "Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.", "warning")
            if product.values["sold_count"] != purchased_units[identity]:
                self.issue(product.source, "sold_count", "legacy_sales_cache_unreconciled", "Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.", "warning")
        plan.reconciliation = {
            "orders": len(groups["orders"]),
            "order_total": str(sum((r.values["total"] for r in groups["orders"]), Decimal(0))),
            "order_subtotal": str(sum((r.values["subtotal"] for r in groups["orders"]), Decimal(0))),
            "stock_units": sum(r.values["stock"] for r in groups["product_variants"]),
            "reserved_units": sum(r.values["reserved"] for r in groups["product_variants"]),
            "active_reservation_units": sum(r.values["quantity"] for r in groups["stock_reservations"] if r.values["status"] == "active" and r.values["variant_id"]),
            "user_points": sum(r.values["points_balance"] for r in groups["users"]),
            "point_delta": sum(r.values["delta"] for r in groups["point_logs"]),
            "voucher_used": sum(r.values["used_count"] for r in groups["vouchers"]),
            "note": "Aggregates describe the supplied export only; verified row checksums and totals are checked again on apply/resume.",
        }


def _contains_secret(value: Any) -> bool:
    secret_keys = {"password", "password_hash", "pin", "pin_hash", "authorization", "client_secret", "secret_key", "access_token", "refresh_token", "api_key"}
    if isinstance(value, dict):
        return any(str(k).lower().replace("-", "_") in secret_keys or _contains_secret(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_secret(v) for v in value)
    return False


def _ci(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value).casefold() if not unicodedata.combining(c)).rstrip(" ")


def _matches_position(value: Any, position: int) -> bool:
    try:
        return not isinstance(value, bool) and Decimal(str(value)) == position
    except (ValueError, InvalidOperation):
        return False


def _binary_column(column) -> bool:
    variant = getattr(column.type, "_variant_mapping", {}).get("mysql")
    return bool(variant is not None and getattr(variant, "collation", "") == "utf8mb4_bin")


def build_plan(documents: dict[str, list[dict]], *, issues: Iterable[Issue] = (), partial: bool = False) -> ImportPlan:
    return Planner(documents, issues=issues, partial=partial).build()


def plan_directory(directory: str | Path, *, allow_partial: bool = False) -> ImportPlan:
    documents, issues = load_export(directory, allow_partial=allow_partial)
    return build_plan(documents, issues=issues, partial=allow_partial)


def _where_key(table, key: dict):
    return [table.c[k] == value for k, value in key.items()]


async def _target_row(session: AsyncSession, row: TargetRow) -> dict | None:
    result = await session.execute(select(TABLES[row.table]).where(*_where_key(TABLES[row.table], row.key)))
    record = result.mappings().one_or_none()
    return dict(record) if record is not None else None


def _same_values(expected: dict, actual: dict) -> bool:
    return all(canonical(value) == canonical(actual.get(key)) for key, value in expected.items())


async def inspect_target(plan: ImportPlan, factory: async_sessionmaker[AsyncSession], run_id: str) -> dict[str, Any]:
    """Read-only all-row collision/drift audit; no guessing at resume identity."""
    async with factory() as session:
        runs = TABLES["migration_runs"]
        existing = (await session.execute(select(runs).where(runs.c.id == run_id))).mappings().one_or_none()
        if existing is None:
            # Full exports are loaded into an empty target. Merging into existing
            # business rows is an independent migration requiring its own mapping.
            for table in Base.metadata.sorted_tables:
                if table.name in MIGRATION_TABLES:
                    continue
                if (await session.execute(select(table).limit(1))).first() is not None:
                    raise ImportRejected("Target contains business data; use an empty migrated database, not an in-place merge")
            other = (await session.execute(select(runs.c.id).limit(1))).first()
            if other is not None:
                raise ImportRejected("Target has another migration run; select its exact ID to resume or use a new empty database")
            return {"mode": "new", "verified_rows": 0, "pending_rows": len(plan.rows)}
        if existing["export_checksum"] != plan.export_checksum or existing["schema_revision"] != EXPECTED_SCHEMA_REVISION:
            raise ImportRejected("Run export checksum/schema differs; modified exports cannot resume an earlier run")
        records_table = TABLES["migration_records"]
        records = (await session.execute(select(records_table).where(records_table.c.run_id == run_id))).mappings().all()
        recorded = {(r["source_collection"], r["source_id"], r["target_table"], r["target_id"]): r for r in records}
        expected_keys = {(r.source.collection, r.source.source_id, r.table, r.key_text) for r in plan.rows}
        if set(recorded) - expected_keys:
            raise ImportRejected("Run contains provenance entries outside this plan")
        verified = 0
        for row in plan.rows:
            record = recorded.get((row.source.collection, row.source.source_id, row.table, row.key_text))
            actual = await _target_row(session, row)
            if record is not None:
                if record["source_checksum"] != row.source.checksum or record["status"] not in {"imported", "verified"}:
                    raise ImportRejected("Recorded source checksum/status does not match the plan")
                if actual is None or not _same_values(row.values, actual):
                    raise ImportRejected("Imported row has changed or disappeared; resume will not overwrite it")
                verified += 1
            elif actual is not None:
                raise ImportRejected("Target row exists without matching import provenance; no implicit adoption/overwrite")
        # Tables are reserved for the migration while it runs; count all rows,
        # not just planned IDs, so concurrent/new business writes are noticed.
        expected_counts = Counter(r["target_table"] for r in records)
        for table in Base.metadata.sorted_tables:
            if table.name in MIGRATION_TABLES:
                continue
            count = int((await session.execute(select(func.count()).select_from(table))).scalar_one())
            if count != expected_counts[table.name]:
                raise ImportRejected("Unexpected target rows found; application writers must stay stopped during import")
        return {"mode": "resume", "verified_rows": verified, "pending_rows": len(plan.rows) - verified}


async def apply_plan(plan: ImportPlan, factory: async_sessionmaker[AsyncSession], *,
                     source_label: str, run_id: str | None = None, acknowledge_warnings: bool = False,
                     chunk_size: int = 200) -> dict[str, Any]:
    """Apply in FK order with row and provenance in the same transaction.

    Public CLI checks actual server version/schema and trigger integrity first.
    Accepting a session factory permits portable tests, but callers must never
    bypass production's preflight or run with application writers enabled.
    """
    if plan.errors:
        raise ImportRejected("Source preflight has errors; apply is blocked")
    if plan.warnings and not acknowledge_warnings:
        raise ImportRejected("Source preflight has warnings; review the report and explicitly acknowledge them")
    if not 1 <= chunk_size <= 1000:
        raise ImportRejected("Chunk size must be between 1 and 1000")
    if not source_label or len(source_label) > 255:
        raise ImportRejected("Source label must be 1-255 characters")
    run_id = run_id or stable_id("run", plan.export_checksum)
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id):
        raise ImportRejected("Run ID must contain 1-64 letters, digits, hyphen or underscore")
    # Prevent two import processes sharing the same target on MySQL5.7. The
    # named lock is held on a dedicated connection for the whole operation.
    engine = factory.kw.get("bind")
    if engine is None:
        raise ImportRejected("An engine-bound async session factory is required")
    lock_connection = None
    lock_name = None
    try:
        if engine.dialect.name == "mysql":
            lock_connection = await engine.connect()
            database_name = str((await lock_connection.execute(text("SELECT DATABASE()"))).scalar_one())
            lock_name = "meow-import-" + hashlib.sha256(database_name.encode()).hexdigest()[:45]
            locked = (await lock_connection.execute(text("SELECT GET_LOCK(:name, 0)"), {"name": lock_name})).scalar_one()
            if locked != 1:
                raise ImportRejected("Another migration importer is running for this database")
        status = await inspect_target(plan, factory, run_id)
        runs, records, issues = (TABLES[n] for n in ("migration_runs", "migration_records", "migration_issues"))
        if status["mode"] == "new":
            async with factory() as session, session.begin():
                await session.execute(runs.insert().values(id=run_id, source_label=source_label,
                    export_checksum=plan.export_checksum, schema_revision=EXPECTED_SCHEMA_REVISION,
                    status="running", source_count=len(plan.sources), started_at=utcnow()))
                for index, issue in enumerate(plan.issues):
                    await session.execute(issues.insert().values(id=stable_id(run_id, "issue", index), run_id=run_id,
                        source_collection=issue.collection, source_id=issue.source_id, field_name=issue.field,
                        issue_code=issue.code, severity=issue.severity, explanation=issue.explanation))
        else:
            async with factory() as session, session.begin():
                await session.execute(runs.update().where(runs.c.id == run_id).values(status="running", completed_at=None))
        try:
            for start in range(0, len(plan.rows), chunk_size):
                chunk = plan.rows[start:start + chunk_size]
                async with factory() as session, session.begin():
                    for row in chunk:
                        provenance_id = stable_id(run_id, row.provenance_id)
                        record = (await session.execute(select(records.c.id).where(records.c.id == provenance_id))).first()
                        if record:
                            continue  # All saved records were verified above.
                        if await _target_row(session, row) is not None:
                            raise ImportRejected("Target changed after preflight; migration stopped without overwriting rows")
                        await session.execute(TABLES[row.table].insert().values(**row.values))
                        await session.execute(records.insert().values(id=provenance_id, run_id=run_id,
                            source_collection=row.source.collection, source_id=row.source.source_id,
                            source_checksum=row.source.checksum, target_table=row.table,
                            target_id=row.key_text, status="imported"))
                    # Exact number of source records with at least one completed
                    # target row is a progress count, not final reconciliation.
                    imported_sources = (await session.execute(select(records.c.source_collection, records.c.source_id)
                        .where(records.c.run_id == run_id).distinct())).all()
                    await session.execute(runs.update().where(runs.c.id == run_id).values(migrated_count=len(imported_sources)))
            verification = await inspect_target(plan, factory, run_id)
            if verification["pending_rows"]:
                raise ImportRejected("Import is incomplete after final verification")
            async with factory() as session, session.begin():
                await session.execute(records.update().where(records.c.run_id == run_id).values(status="verified", verified_at=utcnow()))
                await session.execute(runs.update().where(runs.c.id == run_id).values(status="completed", migrated_count=len(plan.sources), completed_at=utcnow()))
            return {"run_id": run_id, "status": "completed", "source_records": len(plan.sources),
                    "verified_target_rows": verification["verified_rows"], "resumed_rows": status["verified_rows"],
                    "export_checksum": plan.export_checksum, "reconciliation": plan.reconciliation}
        except BaseException:
            async with factory() as session, session.begin():
                await session.execute(runs.update().where(runs.c.id == run_id).values(status="failed"))
            raise
    finally:
        if lock_connection is not None:
            try:
                if lock_name:
                    await lock_connection.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})
            finally:
                await lock_connection.close()
