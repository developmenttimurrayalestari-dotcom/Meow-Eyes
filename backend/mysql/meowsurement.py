"""Account-owned Meowsurement services for MySQL 5.7.

Identity comes from the existing ecommerce session, prescription from the
customer profile, and geometry from the administrator's typed frame catalog.
Historical revisions and their source snapshots are append-only.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
import math
import re
import uuid
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import read_session, session_scope
from mysql import models as m
from mysql.api import json_value
from mysql.base import utcnow
from mysql.commerce import lock_user, save_prescription


ALGORITHM_VERSION = "optifit-local-geometry-1.0.0"
SETTINGS = {"calibrationMethods": ["marker", "frame"], "asymmetryWarningMm": None, "photoRetentionDays": 30}
PARAMETERS = frozenset(("distance_pd", "near_pd", "vertex_right", "vertex_left",
                       "pantoscopic_right", "pantoscopic_left", "wrap_right", "wrap_left"))
VIEWS = frozenset(("frontal", "frontal_near", "three_quarter_left", "three_quarter_right", "lateral_right", "lateral_left"))
MAX_JSON_BYTES = 2 * 1024 * 1024
FRAME_FIELDS = ("a", "b", "dbl", "ed", "temple_length", "symmetric", "enabled", "source_note")
IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
HASH = re.compile(r"^[a-f0-9]{64}$")


def new_id(prefix: str) -> str:
    """Generate full-entropy UUIDs only for the new Meowsurement records."""
    return f"{prefix}_{uuid.uuid4().hex}"


def reject(message: str, code: int = 422):
    raise HTTPException(code, message)


def is_reviewer(user) -> bool:
    return user.role in {"admin", "super_admin"} or (
        user.role == "staff" and "meowsurement.review" in (user.permissions or []))


def today() -> date:
    return datetime.now(ZoneInfo("Asia/Jakarta")).date()


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def bounded_json(value: Any) -> None:
    """Keep annotations bounded and never accept inline photograph payloads."""
    nodes = 0
    def visit(item, depth=0):
        nonlocal nodes
        nodes += 1
        if depth > 24 or nodes > 100000:
            reject("Data pengukuran terlalu kompleks")
        if isinstance(item, dict):
            if any(not isinstance(key, str) or len(key) > 100 for key in item):
                reject("Nama kolom pengukuran tidak valid")
            for child in item.values():
                visit(child, depth + 1)
        elif isinstance(item, list):
            if len(item) > 20000:
                reject("Daftar pengukuran terlalu panjang")
            for child in item:
                visit(child, depth + 1)
        elif isinstance(item, str):
            if len(item) > 16000 or item.lstrip().lower().startswith(("data:", "blob:")):
                reject("Foto harus menggunakan unggahan privat, bukan data inline")
        elif isinstance(item, float) and not math.isfinite(item):
            reject("Angka pengukuran harus terbatas")
        elif item is not None and not isinstance(item, (bool, int, float)):
            reject("Jenis data pengukuran tidak valid")
    visit(value)
    if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_JSON_BYTES:
        reject("Data pengukuran terlalu besar", 413)


def _phone(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    value = value.strip()
    if not re.fullmatch(r"\+?[0-9 ()-]+", value):
        reject("Nomor telepon tidak valid")
    digits = re.sub(r"[ ()-]", "", value)
    if not 8 <= len(digits.lstrip("+")) <= 15:
        reject("Nomor telepon harus berisi 8–15 digit")
    return digits


def _num(value):
    return float(value) if value is not None else None


async def profile_payload(s: AsyncSession, user: m.User) -> dict:
    profile = await s.get(m.CustomerProfile, user.user_id)
    prescription = {"id": None, "date": None, "od": {k: None for k in ("sph", "cyl", "axis", "add")},
                    "os": {k: None for k in ("sph", "cyl", "axis", "add")}, "notes": "",
                    "pd_total": None, "pd_right": None, "pd_left": None}
    if profile and profile.active_prescription_id:
        rx = await s.get(m.Prescription, profile.active_prescription_id)
        if rx is not None and rx.user_id == user.user_id:
            prescription.update(id=rx.id, date=profile.prescription_date.isoformat() if profile.prescription_date else None,
                                notes=rx.notes or "", pd_total=_num(rx.pd_total), pd_right=_num(rx.pd_right), pd_left=_num(rx.pd_left))
            for eye in (await s.scalars(select(m.PrescriptionEye).where(m.PrescriptionEye.prescription_id == rx.id))).all():
                prescription["od" if eye.eye == "right" else "os"] = {
                    k: _num(getattr(eye, k)) for k in ("sph", "cyl", "axis", "add")}
    data = {"user_id": user.user_id, "name": user.name, "email": user.email,
            "phone": profile.phone if profile else None,
            "birth_date": profile.birth_date.isoformat() if profile and profile.birth_date else None,
            "gender": profile.gender if profile else None, "address": profile.address if profile else None,
            "version": profile.version if profile else 0, "prescription": prescription}
    missing = profile_missing(data)
    return {"profile": data, "ready": not missing, "missing_fields": missing}


def profile_missing(profile: dict) -> list[str]:
    missing = [key for key in ("name", "phone", "birth_date") if not nonempty(profile.get(key))]
    prescription = profile.get("prescription") or {}
    if not prescription.get("date"):
        missing.append("prescription.date")
    for side in ("od", "os"):
        eye = prescription.get(side) or {}
        for key in ("sph", "cyl"):
            if not finite(eye.get(key)):
                missing.append(f"prescription.{side}.{key}")
        if finite(eye.get("cyl")) and eye["cyl"] != 0:
            if not finite(eye.get("axis")) or not 1 <= eye["axis"] <= 180:
                missing.append(f"prescription.{side}.axis")
    return missing


async def get_profile(user) -> dict:
    async with read_session() as s:
        row = await s.get(m.User, user.user_id)
        if row is None or not row.is_active:
            reject("Akun tidak tersedia", 403)
        return await profile_payload(s, row)


async def update_profile(user, payload) -> dict:
    async with session_scope() as s:
        row = await lock_user(s, user.user_id)
        before = (await profile_payload(s, row))["profile"]
        if payload.expected_version != before["version"]:
            reject("Profil telah berubah. Muat ulang sebelum menyimpan.", 409)
        profile = await s.get(m.CustomerProfile, user.user_id)
        if profile is None:
            profile = m.CustomerProfile(user_id=user.user_id, version=1)
            s.add(profile)
        else:
            profile.version += 1
        fields = payload.model_fields_set
        if "name" in fields:
            if not payload.name or not payload.name.strip():
                reject("Nama customer wajib diisi")
            row.name = payload.name.strip()
        if "phone" in fields:
            profile.phone = _phone(payload.phone)
        for key in ("birth_date", "gender", "address"):
            if key in fields:
                setattr(profile, key, getattr(payload, key) or None)
        if profile.birth_date and profile.birth_date > today():
            reject("Tanggal lahir tidak boleh di masa depan")
        if "prescription" in fields:
            if payload.prescription is None:
                profile.active_prescription_id = None
                profile.prescription_date = None
            else:
                rx = payload.prescription.model_dump(mode="json")
                old_rx = {key: before["prescription"].get(key) for key in rx}
                if rx != old_rx:
                    flat = {f"{side}_{key}": rx[side][key] for side in ("od", "os") for key in ("sph", "cyl", "axis", "add")}
                    flat.update({key: rx[key] for key in ("notes", "pd_total", "pd_right", "pd_left")})
                    # A replacement record protects previous orders and measurements.
                    stored = await save_prescription(s, user.user_id, flat)
                    profile.active_prescription_id = stored.id
                profile.prescription_date = payload.prescription.date
        if profile.prescription_date and (profile.prescription_date > today() or
                (profile.birth_date and profile.prescription_date < profile.birth_date)):
            reject("Tanggal resep harus sesudah tanggal lahir dan tidak di masa depan")
        await s.flush()
        audit(s, user.user_id, user.user_id, "profile.updated", details={"version": profile.version})
        return await profile_payload(s, row)


def specification_payload(spec, *, version: int | None = None) -> dict:
    result = {key: (json_value(getattr(spec, key)) if spec else (False if key in ("enabled", "symmetric") else None)) for key in FRAME_FIELDS}
    result["version"] = version if version is not None else (spec.version if spec else 0)
    result["missing_fields"] = [key for key in ("a", "b", "dbl") if not finite(result[key]) or result[key] <= 0]
    result["complete"] = not result["missing_fields"]
    return result


async def frame_specification(s: AsyncSession, product_id: str, *, public=False) -> dict:
    product = await s.get(m.Product, product_id)
    if not product or product.product_type != "frame" or (public and not product.is_active):
        reject("Frame tidak ditemukan", 404)
    root = await s.get(m.ProductFrameSpecification, product_id)
    version = root.version if root else 0
    variants = (await s.scalars(select(m.ProductVariant).where(m.ProductVariant.product_id == product_id)
                .order_by(m.ProductVariant.sort_order, m.ProductVariant.id))).all()
    overrides = {item.variant_id: item for item in (await s.scalars(select(m.ProductVariantFrameSpecification)
                 .where(m.ProductVariantFrameSpecification.product_id == product_id))).all()}
    return {"product_id": product_id, "version": version, "specification": specification_payload(root, version=version),
            "variants": [{"variant_id": variant.id, "inherit_default": variant.id not in overrides,
                          "specification": specification_payload(overrides[variant.id], version=version) if variant.id in overrides else None,
                          "effective_specification": specification_payload(overrides.get(variant.id, root), version=version)}
                         for variant in variants if not public or variant.is_active]}


def _assign_spec(row, payload, version: int, actor: str):
    values = payload.model_dump()
    if values["enabled"] and any(values[key] is None for key in ("a", "b", "dbl")):
        reject("A, B, dan DBL wajib lengkap sebelum Meowsurement diaktifkan; ED opsional")
    for key, value in values.items():
        if key in ("a", "b", "dbl", "ed", "temple_length") and value is not None:
            value = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if value <= 0:
                reject("Ukuran frame minimal 0,01 mm")
        setattr(row, key, value)
    row.version = version
    row.updated_by = actor


async def update_specification(user, product_id: str, payload) -> dict:
    async with session_scope() as s:
        product = await s.scalar(select(m.Product).where(m.Product.id == product_id).with_for_update())
        if not product or product.product_type != "frame":
            reject("Frame tidak ditemukan", 404)
        root = await s.get(m.ProductFrameSpecification, product_id)
        current_version = root.version if root else 0
        if payload.expected_version != current_version:
            reject("Spesifikasi telah berubah. Muat ulang sebelum menyimpan.", 409)
        version = current_version + 1
        if root is None:
            root = m.ProductFrameSpecification(product_id=product_id)
            s.add(root)
        _assign_spec(root, payload.specification, version, user.user_id)
        seen = set()
        for entry in payload.variants:
            if entry.variant_id in seen:
                reject("Varian tidak boleh duplikat")
            seen.add(entry.variant_id)
            variant = await s.get(m.ProductVariant, entry.variant_id)
            if not variant or variant.product_id != product_id:
                reject("Varian bukan milik produk ini")
            override = await s.get(m.ProductVariantFrameSpecification, entry.variant_id)
            if entry.inherit_default:
                if entry.specification is not None:
                    reject("Varian yang mengikuti produk tidak boleh memiliki override")
                if override is not None:
                    await s.delete(override)
            else:
                if entry.specification is None:
                    reject("Spesifikasi override varian wajib diisi")
                if override is None:
                    override = m.ProductVariantFrameSpecification(product_id=product_id, variant_id=entry.variant_id)
                    s.add(override)
                _assign_spec(override, entry.specification, version, user.user_id)
        await s.flush()
        audit(s, user.user_id, user.user_id, "catalog.frame_specification.updated", details={"product_id": product_id, "version": version})
        return await frame_specification(s, product_id)


async def list_frames(query: str = "", page: int = 1, page_size: int = 15, product_id: str | None = None):
    async with read_session() as s:
        conditions = [m.Product.is_active.is_(True), m.Product.product_type == "frame"]
        if product_id:
            conditions.append(m.Product.id == product_id)
        if query.strip():
            escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append(or_(m.Product.name.like(f"%{escaped}%", escape="\\"), m.Product.sku.like(f"%{escaped}%", escape="\\")))
        total = await s.scalar(select(func.count()).select_from(m.Product).where(*conditions))
        products = (await s.scalars(select(m.Product).where(*conditions).order_by(m.Product.name, m.Product.id)
                                   .offset((page - 1) * page_size).limit(page_size))).all()
        result = []
        for product in products:
            specification = await frame_specification(s, product.id, public=True)
            variant_specs = {v["variant_id"]: v["effective_specification"] for v in specification["variants"]}
            variant_details = {v["variant_id"]: v for v in specification["variants"]}
            brand = await s.get(m.Brand, product.brand_id) if product.brand_id else None
            variants = (await s.scalars(select(m.ProductVariant).where(m.ProductVariant.product_id == product.id,
                        m.ProductVariant.is_active.is_(True)).order_by(m.ProductVariant.sort_order, m.ProductVariant.id))).all()
            result.append({"id": product.id, "name": product.name, "slug": product.slug, "sku": product.sku,
                "brand": brand.name if brand else "", "main_image": product.main_image,
                "frame_specification": specification["specification"], "specification": specification["specification"],
                "specification_version": specification["version"],
                "variants": [{"id": v.id, "color": v.color, "size": v.size, "sku": v.sku,
                              "inherit_default": variant_details[v.id]["inherit_default"],
                              "specification": variant_details[v.id]["specification"],
                              "frame_specification": variant_specs[v.id], "effective_specification": variant_specs[v.id]} for v in variants]})
        return {"products": result, "page": page, "page_size": page_size, "total": total,
                "total_pages": max(1, math.ceil(total / page_size))}


def audit(s, owner, actor, action, *, session=None, revision=None, details=None):
    s.add(m.MeowsurementAuditEvent(id=new_id("ma"), user_id=owner, actor_id=actor,
          session_id=session.id if session else None, revision_id=revision.id if revision else None,
          action=action, details=details or {}))


def _canonical_rx(profile: dict) -> dict:
    prescription = profile["prescription"]
    return {"od": deepcopy(prescription["od"]), "os": deepcopy(prescription["os"]),
            "notes": prescription.get("notes") or "", "source": "professional_prescription",
            **{key: prescription.get(key) for key in ("id", "date", "pd_total", "pd_right", "pd_left")}}


def _scope(parameters) -> list:
    if (not isinstance(parameters, list) or not parameters or len(parameters) > 8 or
            any(not isinstance(key, str) or key not in PARAMETERS for key in parameters) or len(set(parameters)) != len(parameters)):
        reject("Lingkup pengukuran tidak valid")
    return parameters


def measurement_context(data: dict) -> dict:
    frame = data["frame"]
    return {"frame": {"brand": frame.get("brand") or "", "model": frame.get("model") or "", "productId": frame.get("productId"),
                      **{key: frame.get(key) for key in ("a", "b", "dbl", "ed")},
                      "pdReference": frame.get("pdReference") or "unspecified", "symmetric": frame.get("symmetric") is True},
            "workingDistanceCm": data.get("workingDistanceCm")}


async def authorized_session(s, user, session_id: str, *, editing=False, lock=False):
    query = select(m.MeowsurementSession).where(m.MeowsurementSession.id == session_id)
    if editing or not is_reviewer(user):
        query = query.where(m.MeowsurementSession.user_id == user.user_id)
    session = await s.scalar(query.with_for_update() if lock else query)
    if session is None:
        reject("Sesi tidak ditemukan", 404)
    return session


async def current_revision(s, session, expected_id=None):
    if expected_id is not None and session.current_revision_id != expected_id:
        reject("Revisi telah berubah. Muat ulang sesi sebelum melanjutkan.", 409)
    revision = await s.get(m.MeowsurementRevision, session.current_revision_id) if session.current_revision_id else None
    if revision is None:
        reject("Revisi sesi belum tersedia", 409)
    return revision


def photo_payload(photo) -> dict:
    return {"id": photo.id, "sessionId": photo.session_id, "userId": photo.user_id,
            "hash": photo.sha256, "sourceHash": photo.source_sha256, "mimeType": photo.mime_type,
            "width": photo.width, "height": photo.height, "byteSize": photo.byte_size,
            "expiresAt": json_value(photo.expires_at), "deletedAt": json_value(photo.deleted_at), "createdAt": json_value(photo.created_at)}


def session_payload(session) -> dict:
    return {"id": session.id, "customerId": session.user_id, "patientId": session.user_id,
            "createdBy": session.user_id, "operatorId": session.user_id, "operatorName": session.profile_snapshot.get("name", ""),
            "examinationDate": session.examination_date.isoformat(), "algorithmVersion": session.algorithm_version,
            "device": session.device or {}, "currentRevisionId": session.current_revision_id,
            "latestRevisionId": session.current_revision_id, "status": session.status, "revisionNumber": session.revision_number,
            "createdAt": json_value(session.created_at), "updatedAt": json_value(session.updated_at),
            "productId": session.product_id, "variantId": session.variant_id, "profileVersion": session.profile_version,
            "specVersion": session.spec_version, "frameName": session.frame_snapshot.get("model", ""),
            "customerName": session.profile_snapshot.get("name", "")}


async def detail_payload(s, session) -> dict:
    rows = (await s.scalars(select(m.MeowsurementRevision).where(m.MeowsurementRevision.session_id == session.id)
                           .order_by(m.MeowsurementRevision.revision_number))).all()
    reviews = (await s.scalars(select(m.MeowsurementReview).where(m.MeowsurementReview.session_id == session.id)
                              .order_by(m.MeowsurementReview.created_at, m.MeowsurementReview.id))).all()
    actor_ids = {row.actor_id for row in rows} | {review.reviewer_id for review in reviews}
    actors = {u.user_id: u.name for u in (await s.scalars(select(m.User).where(m.User.user_id.in_(actor_ids)))).all()} if actor_ids else {}
    revisions = [{"id": row.id, "sessionId": row.session_id, "parentRevisionId": row.parent_revision_id,
                  "data": row.data, "reason": row.reason, "actorId": row.actor_id, "actorName": actors.get(row.actor_id, ""),
                  "createdAt": json_value(row.created_at), "algorithmVersion": row.algorithm_version, "revisionNumber": row.revision_number} for row in rows]
    profile = session.profile_snapshot
    patient = {"id": session.user_id, "customerId": session.user_id, "recordNumber": "MEOW-" + session.user_id,
               "fullName": profile.get("name", ""), "birthDate": profile.get("birth_date"), "sex": profile.get("gender") or "",
               "examinationDate": session.examination_date.isoformat(), "phone": profile.get("phone") or "",
               "email": profile.get("email") or "", "address": profile.get("address") or ""}
    photos = (await s.scalars(select(m.MeowsurementPhoto).where(m.MeowsurementPhoto.session_id == session.id)
                             .order_by(m.MeowsurementPhoto.created_at, m.MeowsurementPhoto.id))).all()
    return {"session": session_payload(session), "revision": next((r for r in revisions if r["id"] == session.current_revision_id), None),
            "revisions": revisions, "patient": patient, "settings": deepcopy(SETTINGS),
            "reviews": [{"id": r.id, "sessionId": r.session_id, "revisionId": r.revision_id, "reviewerId": r.reviewer_id,
                         "reviewerName": actors.get(r.reviewer_id, ""), "decision": r.decision, "note": r.note,
                         "evidence": r.evidence, "createdAt": json_value(r.created_at)} for r in reviews],
            "photos": [photo_payload(photo) for photo in photos]}


async def create_session(user, payload) -> dict:
    async with session_scope() as s:
        account = await lock_user(s, user.user_id)
        profile_result = await profile_payload(s, account)
        if not profile_result["ready"]:
            raise HTTPException(422, {"message": "Lengkapi profil dan resep kacamata sebelum menggunakan Meowsurement.",
                                      "missing_fields": profile_result["missing_fields"], "profile_url": "/profile"})
        profile = profile_result["profile"]
        if profile["version"] != payload.expected_profile_version:
            reject("Profil telah berubah. Muat ulang sebelum membuat sesi.", 409)
        if payload.product_id is None:
            # Customer dimensions are a separate immutable source, never a
            # fabricated catalog product or an override of administrator data.
            dimensions = payload.manual_frame.model_dump()
            for key in ("a", "b", "dbl", "ed"):
                if dimensions[key] is not None:
                    dimensions[key] = float(Decimal(str(dimensions[key])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    if dimensions[key] <= 0:
                        reject("Ukuran frame minimal 0,01 mm")
            version, scope, product_id, variant_id = 1, "manual", None, None
            frame = {**dimensions, "symmetric": False, "templeLength": None, "brand": "",
                     "productId": None, "variantId": None, "pdReference": "facial_midline", "sourceVersion": version,
                     "sourceScope": scope, "sourceNote": "Ukuran frame dimasukkan customer.", "color": None, "size": None, "sku": None}
        else:
            # Serialize catalog versions with the administrator's updates.
            product = await s.scalar(select(m.Product).where(m.Product.id == payload.product_id).with_for_update())
            if not product or not product.is_active or product.product_type != "frame":
                reject("Frame tidak tersedia", 404)
            variant = await s.get(m.ProductVariant, payload.variant_id)
            if not variant or variant.product_id != product.id or not variant.is_active:
                reject("Varian frame tidak tersedia", 404)
            default = await s.get(m.ProductFrameSpecification, product.id)
            override = await s.get(m.ProductVariantFrameSpecification, variant.id)
            version = default.version if default else 0
            if version != payload.expected_spec_version:
                reject("Spesifikasi frame telah berubah. Muat ulang pilihan frame.", 409)
            spec = specification_payload(override or default, version=version)
            if not spec["enabled"] or not spec["complete"]:
                reject("Spesifikasi frame belum lengkap atau belum diaktifkan untuk Meowsurement")
            brand = await s.get(m.Brand, product.brand_id) if product.brand_id else None
            scope, product_id, variant_id = "variant" if override else "product", product.id, variant.id
            frame = {key: spec[key] for key in ("a", "b", "dbl", "ed", "symmetric")}
            frame.update(templeLength=spec["temple_length"], brand=brand.name if brand else "", model=product.name,
                         productId=product.id, variantId=variant.id, pdReference="frame_bridge", sourceVersion=version,
                         sourceScope=scope, sourceNote=spec["source_note"] or "", color=variant.color, size=variant.size, sku=variant.sku)
        examination_date = payload.examination_date or today()
        if examination_date > today() or examination_date.isoformat() < profile["birth_date"]:
            reject("Tanggal pemeriksaan tidak valid")
        bounded_json(payload.device)
        session = m.MeowsurementSession(id=new_id("ms"), user_id=user.user_id, product_id=product_id, variant_id=variant_id,
            prescription_id=profile["prescription"]["id"], profile_version=profile["version"], spec_version=version,
            spec_scope=scope, examination_date=examination_date, status="draft",
            current_revision_id=None, revision_number=0, algorithm_version=ALGORITHM_VERSION,
            profile_snapshot=deepcopy(profile), frame_snapshot=deepcopy(frame), device=payload.device)
        s.add(session)
        await s.flush()
        data = {"prescription": _canonical_rx(profile), "frame": frame, "captures": [], "results": {}, "manualMeasurements": {},
                "requiredParameters": _scope(payload.required_parameters), "workingDistanceCm": payload.working_distance_cm,
                "mode": payload.mode, "notes": "", "deviceModel": "", "preparation": [],
                "consents": {"capture": False, "retainPhotos": False, "thumbnail": False, "uploadPhotos": False},
                "examinationDate": examination_date.isoformat(), "algorithmVersion": ALGORITHM_VERSION}
        revision = await append_revision(s, session, user, data, "Sesi dibuat dari profil customer dan ukuran frame " + ("manual." if scope == "manual" else "katalog."))
        audit(s, user.user_id, user.user_id, "session.created", session=session, revision=revision,
              details={"profile_version": profile["version"], "spec_version": version})
        await s.flush()
        return await detail_payload(s, session)


async def get_session(user, session_id):
    async with read_session() as s:
        session = await authorized_session(s, user, session_id)
        return await detail_payload(s, session)


async def list_sessions(user, *, review_queue=False, status=None, page=1, page_size=15):
    if review_queue and not is_reviewer(user):
        reject("Izin review Meowsurement diperlukan", 403)
    async with read_session() as s:
        conditions = [] if review_queue else [m.MeowsurementSession.user_id == user.user_id]
        if status:
            if status not in {"draft", "pending_review", "needs_verification", "needs_remeasure", "approved"}:
                reject("Status tidak valid")
            conditions.append(m.MeowsurementSession.status == status)
        elif review_queue:
            conditions.append(m.MeowsurementSession.status.in_(("pending_review", "needs_verification")))
        total = await s.scalar(select(func.count()).select_from(m.MeowsurementSession).where(*conditions))
        rows = (await s.scalars(select(m.MeowsurementSession).where(*conditions)
                 .order_by(m.MeowsurementSession.updated_at.desc(), m.MeowsurementSession.id)
                 .offset((page - 1) * page_size).limit(page_size))).all()
        return {"sessions": [session_payload(row) for row in rows], "page": page, "page_size": page_size,
                "total": total, "total_pages": max(1, math.ceil(total / page_size))}


def _capture_date(value):
    if not isinstance(value, str) or len(value) > 50:
        reject("Waktu pengambilan gambar tidak valid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if not parsed.tzinfo:
            reject("Zona waktu pengambilan gambar wajib dicatat")
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        reject("Waktu pengambilan gambar tidak valid")


def camera_result(result) -> bool:
    method = str(result.get("method", "")).lower()
    return result.get("source") == "camera" or method.startswith(("calibrated_", "lateral_")) or any(
        word in method for word in ("camera", "marker", "frame", "photogram", "homography"))


async def validate_revision_data(s, session, previous, incoming):
    bounded_json(incoming)
    data = deepcopy(incoming)
    allowed = {"prescription", "frame", "captures", "results", "manualMeasurements", "requiredParameters", "workingDistanceCm",
               "mode", "notes", "deviceModel", "consents", "examinationDate", "preparation", "algorithmVersion"}
    if set(data) - allowed:
        reject("Kolom sesi tidak dikenal; identitas dan status ditetapkan server")
    if data.get("prescription") != _canonical_rx(session.profile_snapshot) or data.get("frame") != session.frame_snapshot:
        reject("Resep dan frame sesi bersifat tetap. Buat sesi baru untuk profil atau frame yang berbeda.")
    if data.get("examinationDate") != session.examination_date.isoformat() or data.get("algorithmVersion") != session.algorithm_version:
        reject("Tanggal pemeriksaan dan versi algoritma sesi tidak dapat diganti")
    _scope(data.get("requiredParameters"))
    if data.get("mode") not in {"manual", "semi_automatic"} or not finite(data.get("workingDistanceCm")) or not 0 < data["workingDistanceCm"] <= 10000:
        reject("Mode atau jarak kerja tidak valid")
    if not isinstance(data.get("consents"), dict) or set(data["consents"]) - {"capture", "retainPhotos", "thumbnail", "uploadPhotos", "confirmedAt"}:
        reject("Persetujuan sesi tidak valid")
    for key in ("capture", "retainPhotos", "thumbnail", "uploadPhotos"):
        if not isinstance(data["consents"].get(key, False), bool):
            reject("Persetujuan harus berupa pilihan eksplisit")
    if data["consents"].get("uploadPhotos") and data["consents"].get("capture") is not True:
        reject("Persetujuan pengambilan gambar diperlukan sebelum mengunggah foto")
    captures = data.get("captures", [])
    if not isinstance(captures, list) or len(captures) > 60:
        reject("Maksimal 60 sampel dalam satu revisi")
    previous_captures = {c["id"]: c for c in previous.data.get("captures", [])}
    ids = set()
    for capture in captures:
        if not isinstance(capture, dict) or not isinstance(capture.get("id"), str) or not IDENTIFIER.fullmatch(capture["id"]) or capture["id"] in ids:
            reject("ID sampel tidak valid atau duplikat")
        ids.add(capture["id"])
        if capture.get("view") not in VIEWS:
            reject("Posisi pengambilan gambar tidak valid")
        for key in ("width", "height"):
            if not isinstance(capture.get(key), int) or isinstance(capture[key], bool) or capture[key] <= 0:
                reject("Dimensi gambar tidak valid")
        if capture["width"] * capture["height"] > 20000000:
            reject("Resolusi gambar melebihi batas")
        _capture_date(capture.get("createdAt"))
        if not isinstance(capture.get("photoHash"), str) or not HASH.fullmatch(capture["photoHash"]):
            reject("Hash sumber foto wajib tersedia")
        old = previous_captures.get(capture["id"])
        if old and any(capture.get(key) != old.get(key) for key in ("view", "photoId", "photoHash", "width", "height", "createdAt", "measurementContext")):
            reject("Sumber asli sampel tidak dapat diganti; ambil sampel baru")
        if old is None and (data["consents"].get("capture") is not True or capture.get("measurementContext") != measurement_context(data)):
            reject("Sampel baru memerlukan persetujuan dan konteks pengukuran yang sesuai")
        photo_id = capture.get("photoId")
        if not isinstance(photo_id, str) or not IDENTIFIER.fullmatch(photo_id):
            reject("Referensi foto tidak valid")
        if not photo_id.startswith("local_"):
            photo = await s.get(m.MeowsurementPhoto, photo_id)
            if not photo or photo.session_id != session.id or photo.user_id != session.user_id:
                reject("Foto tidak tersedia untuk sesi ini", 404)
            if not old and (photo.deleted_at or photo.expires_at <= utcnow()):
                reject("Foto telah dihapus atau kedaluwarsa")
            if capture["photoHash"] != photo.source_sha256 or capture["width"] != photo.width or capture["height"] != photo.height:
                reject("Hash atau dimensi sampel tidak cocok dengan sumber foto")
        spec = capture.get("calibrationSpec") or {}
        if isinstance(spec, dict) and spec.get("scaleSource") == "session_frame":
            dimension = "a" if capture["view"].startswith("frontal") else "b" if capture["view"].startswith("lateral_") else None
            expected_length = session.frame_snapshot.get(dimension) if dimension else None
            if (not dimension or spec.get("method") != "frame" or spec.get("frameDimension") != dimension
                    or not finite(expected_length) or expected_length <= 0 or not finite(spec.get("lengthMm"))
                    or abs(spec["lengthMm"] - expected_length) > 0.000001):
                reject("Acuan frame harus memakai ukuran A/B yang sesuai dari snapshot sesi")
            calibration = capture.get("calibration") or {}
            if isinstance(calibration, dict) and calibration.get("valid") is True:
                geometry = calibration.get("geometry")
                actual_length = geometry.get("lengthMm") if isinstance(geometry, dict) else None
                if calibration.get("method") != "frame" or not finite(actual_length) or abs(actual_length - expected_length) > 0.000001:
                    reject("Panjang kalibrasi harus sesuai ukuran frame sesi")
        for field in ("points", "automaticPoints"):
            points = capture.get(field, {})
            if not isinstance(points, dict) or len(points) > 64:
                reject("Landmark gambar tidak valid")
            for point in points.values():
                if point is not None and (not isinstance(point, dict) or not finite(point.get("x")) or not finite(point.get("y"))
                        or not 0 <= point["x"] <= capture["width"] or not 0 <= point["y"] <= capture["height"]):
                    reject("Landmark harus berada pada koordinat gambar asli")
    for key in ("results", "manualMeasurements"):
        results = data.get(key, {})
        if not isinstance(results, dict) or set(results) - PARAMETERS:
            reject("Parameter hasil tidak dikenal")
        for result in results.values():
            if not isinstance(result, dict):
                reject("Hasil pengukuran tidak valid")
            for field in ("method", "algorithmVersion"):
                if not isinstance(result.get(field, ""), str) or len(result.get(field, "")) > 100:
                    reject("Metode atau versi algoritma tidak valid")
            if result.get("sourceCaptureIds") is not None and (not isinstance(result["sourceCaptureIds"], list) or
                    len(result["sourceCaptureIds"]) > 60 or any(not isinstance(i, str) or i not in ids for i in result["sourceCaptureIds"])):
                reject("Sumber hasil harus terhubung ke sampel dalam revisi ini")
            # These claims cannot be asserted by the customer.
            result["requiresReview"] = True
            result["clinicallyValidated"] = False
            result["uncertainty"] = None
            quality = result.get("quality")
            if isinstance(quality, dict) and finite(quality.get("score")) and not 0 <= quality["score"] <= 100:
                reject("Skor kualitas harus berada dalam 0–100")
            if camera_result(result) and isinstance(quality, dict) and finite(quality.get("score")):
                quality["score"] = max(0, min(69, quality["score"]))
                quality["clinicalAccuracy"] = False
            if isinstance(quality, dict):
                if finite(quality.get("score")):
                    quality["category"] = "high" if quality["score"] >= 80 else "medium" if quality["score"] >= 50 else "low"
                    quality["label"] = {"high": "Tinggi", "medium": "Sedang", "low": "Rendah"}[quality["category"]]
                quality["kind"] = "engineering_evidence"
                quality["clinicallyValidated"] = False
                quality["requiresReview"] = True
                quality["uncertainty"] = None
    return data


async def append_revision(s, session, user, data: dict, reason: str):
    number = session.revision_number + 1
    revision = m.MeowsurementRevision(id=new_id("mr"), session_id=session.id, user_id=session.user_id,
        revision_number=number, parent_revision_id=session.current_revision_id, data=deepcopy(data),
        reason=reason.strip(), actor_id=user.user_id, algorithm_version=session.algorithm_version)
    s.add(revision)
    await s.flush()  # Circular ownership FK and MySQL status guards require this order.
    capture_rows = {}
    for capture in data.get("captures", []):
        photo_id = capture.get("photoId")
        row = m.MeowsurementCapture(id=new_id("mc"), revision_id=revision.id, session_id=session.id, user_id=session.user_id,
            capture_id=capture["id"], view=capture["view"], photo_id=None if photo_id.startswith("local_") else photo_id,
            photo_hash=capture.get("photoHash"), width=capture["width"], height=capture["height"], captured_at=_capture_date(capture["createdAt"]),
            calibration=capture.get("calibration"), landmarks=capture.get("points"), quality=capture.get("quality") or capture.get("analysis"), data=deepcopy(capture))
        s.add(row)
        capture_rows[capture["id"]] = row
    combined = {**data.get("manualMeasurements", {}), **data.get("results", {})}
    measurements = []
    for parameter, result in combined.items():
        row = m.MeowsurementMeasurement(id=new_id("mm"), revision_id=revision.id, session_id=session.id, user_id=session.user_id,
            parameter=parameter, side="right" if parameter.endswith("_right") else "left" if parameter.endswith("_left") else None,
            unit="deg" if parameter.startswith(("pantoscopic_", "wrap_")) else "mm", method=result.get("method") or "unavailable",
            algorithm_version=result.get("algorithmVersion") or session.algorithm_version, valid=result.get("valid") is True,
            values=result.get("values") or {}, quality=result.get("quality"), data=deepcopy(result))
        s.add(row)
        measurements.append((row, result))
    await s.flush()
    for row, result in measurements:
        for capture_id in set(result.get("sourceCaptureIds") or []):
            source = capture_rows[capture_id]
            s.add(m.MeowsurementMeasurementSource(measurement_id=row.id, revision_id=revision.id, capture_row_id=source.id))
    session.current_revision_id = revision.id
    session.revision_number = number
    session.status = "draft"
    session.updated_at = utcnow()
    await s.flush()
    return revision


async def save_revision(user, session_id: str, payload):
    if len(payload.reason.strip()) < 5:
        reject("Alasan perubahan minimal lima karakter")
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        session = await authorized_session(s, user, session_id, editing=True, lock=True)
        previous = await current_revision(s, session, payload.expected_revision_id)
        data = await validate_revision_data(s, session, previous, payload.data)
        revision = await append_revision(s, session, user, data, payload.reason)
        audit(s, session.user_id, user.user_id, "revision.created", session=session, revision=revision,
              details={"revision_number": revision.revision_number})
        await s.flush()
        return await detail_payload(s, session)


def submission_policy(data, *, approval=False):
    from mysql.meowsurement_policy import evaluate_submission
    try:
        return evaluate_submission(data, approval=approval)
    except (AttributeError, KeyError, TypeError, ValueError, IndexError, OverflowError, ZeroDivisionError):
        reject("Struktur bukti pengukuran tidak valid; periksa sampel dan metode")


async def submit_session(user, session_id: str, payload):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        session = await authorized_session(s, user, session_id, editing=True, lock=True)
        revision = await current_revision(s, session, payload.expected_revision_id)
        if session.status == "approved":
            reject("Revisi ini telah disetujui. Buat revisi baru untuk perubahan.", 409)
        policy = submission_policy(revision.data)
        if not policy["valid"]:
            raise HTTPException(422, {"message": "Pengukuran belum dapat diajukan", "errors": policy["errors"]})
        session.status = policy["status"]
        session.updated_at = utcnow()
        audit(s, session.user_id, user.user_id, "session.submitted", session=session, revision=revision,
              details={"status": session.status, "required_parameters": revision.data["requiredParameters"]})
        await s.flush()
        result = await detail_payload(s, session)
        result["policy"] = policy
        return result


async def review_session(user, session_id: str, payload):
    if not is_reviewer(user):
        reject("Izin review Meowsurement diperlukan", 403)
    if len(payload.note.strip()) < 5:
        reject("Catatan review minimal lima karakter")
    bounded_json(payload.evidence)
    allowed_evidence = {"professionalVerified", "comparisonAccepted", "referenceInstrument", "protocolId", "comparisonNotes"}
    if set(payload.evidence) - allowed_evidence:
        reject("Kolom bukti review tidak dikenal")
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        session = await authorized_session(s, user, session_id, lock=True)
        revision = await current_revision(s, session, payload.expected_revision_id)
        if user.user_id in {session.user_id, revision.actor_id}:
            reject("Reviewer harus berbeda dari pembuat sesi dan revisi", 403)
        if session.status not in {"pending_review", "needs_verification"}:
            reject("Sesi belum diajukan atau membutuhkan revisi baru", 409)
        if payload.decision == "approved":
            policy = submission_policy(revision.data, approval=True)
            errors = list(policy["errors"])
            evidence = payload.evidence
            if evidence.get("professionalVerified") is not True:
                errors.append("Verifikasi profesional harus dikonfirmasi")
            for field in ("referenceInstrument", "protocolId", "comparisonNotes"):
                if not nonempty(evidence.get(field)):
                    errors.append(f"Bukti {field} wajib diisi")
            results = {**revision.data.get("manualMeasurements", {}), **revision.data.get("results", {})}
            if any(camera_result(results.get(key, {})) for key in revision.data["requiredParameters"]) and evidence.get("comparisonAccepted") is not True:
                errors.append("Perbandingan hasil kamera dengan alat referensi wajib dikonfirmasi")
            if errors:
                raise HTTPException(422, {"message": "Hasil belum dapat disetujui", "errors": errors})
        review = m.MeowsurementReview(id=new_id("mv"), session_id=session.id, user_id=session.user_id,
            revision_id=revision.id, reviewer_id=user.user_id, decision=payload.decision,
            note=payload.note.strip(), evidence=deepcopy(payload.evidence))
        s.add(review)
        await s.flush()  # The MySQL guard requires this exact review before approval.
        session.status = payload.decision
        session.updated_at = utcnow()
        audit(s, session.user_id, user.user_id, "session.reviewed", session=session, revision=revision,
              details={"review_id": review.id, "decision": review.decision})
        await s.flush()
        return await detail_payload(s, session)


async def authorize_export(user, session_id: str, payload):
    if payload.confirmed is not True:
        reject("Konfirmasi ekspor data pribadi diperlukan")
    if len(set(payload.photo_ids)) != len(payload.photo_ids) or (payload.photo_ids and not payload.include_photos):
        reject("Daftar foto ekspor tidak valid")
    async with session_scope() as s:
        session = await authorized_session(s, user, session_id, lock=True)
        revision = await s.scalar(select(m.MeowsurementRevision).where(m.MeowsurementRevision.id == payload.revision_id,
                                 m.MeowsurementRevision.session_id == session.id, m.MeowsurementRevision.user_id == session.user_id))
        if revision is None:
            reject("Revisi tidak ditemukan", 404)
        if payload.include_photos:
            if revision.data.get("consents", {}).get("thumbnail") is not True or not payload.photo_ids:
                reject("Foto laporan memerlukan persetujuan thumbnail dan pilihan foto")
            allowed = {c.get("photoId") for c in revision.data.get("captures", []) if not c.get("superseded")}
            for photo_id in payload.photo_ids:
                if photo_id.startswith("local_") or photo_id not in allowed:
                    reject("Hanya foto privat tersimpan dari revisi yang dipilih boleh diekspor")
                photo = await s.get(m.MeowsurementPhoto, photo_id)
                if not photo or photo.session_id != session.id or photo.user_id != session.user_id or photo.deleted_at or photo.expires_at <= utcnow():
                    reject("Foto laporan tidak tersedia", 404)
        audit(s, session.user_id, user.user_id, "report.exported", session=session, revision=revision,
              details={"format": payload.format, "include_photos": payload.include_photos, "photo_ids": payload.photo_ids})
        await s.flush()
        return {"authorized": True, "session_id": session.id, "revision_id": revision.id,
                "format": payload.format, "photo_ids": payload.photo_ids, "status": session.status}
