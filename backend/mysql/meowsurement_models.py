"""Customer-owned Meowsurement tables, added by frozen migration 0003.

Existing ecommerce users, prescriptions and product variants remain the source
of identity. There are no organization, local-user or separate patient tables.
CHECK clauses document portable rules; MySQL 5.7 enforces them through 0003
validation triggers. Use Alembic rather than create_all() in production.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
import uuid

from sqlalchemy import (
    Boolean, CheckConstraint, Date, ForeignKey, ForeignKeyConstraint, Index,
    Integer, JSON, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, ID, TOKEN, UTCDateTime, utcnow


def _id() -> str:
    return uuid.uuid4().hex


class _Created:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow,
                                               server_default=func.now(6), nullable=False)


class _Updated(_Created):
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow,
                                               onupdate=utcnow, server_default=func.now(6), nullable=False)


class CustomerProfile(_Updated, Base):
    __tablename__ = "customer_profiles"
    __table_args__ = (
        ForeignKeyConstraint(["active_prescription_id", "user_id"], ["prescriptions.id", "prescriptions.user_id"], ondelete="RESTRICT"),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("gender IS NULL OR gender IN ('male','female','unspecified')", name="gender"),
    )
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), primary_key=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    active_prescription_id: Mapped[str | None] = mapped_column(ID)
    prescription_date: Mapped[date | None] = mapped_column(Date)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)


class _FrameSpecification(_Updated):
    a: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    b: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    dbl: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    ed: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    temple_length: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    symmetric: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    source_note: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    updated_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))


_POSITIVE_SPEC = "(a IS NULL OR a > 0) AND (b IS NULL OR b > 0) AND (dbl IS NULL OR dbl > 0) AND (ed IS NULL OR ed > 0) AND (temple_length IS NULL OR temple_length > 0)"


class ProductFrameSpecification(_FrameSpecification, Base):
    __tablename__ = "product_frame_specifications"
    __table_args__ = (
        CheckConstraint(_POSITIVE_SPEC, name="dimensions"),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("symmetric IN (0,1) AND enabled IN (0,1)", name="flags"),
    )
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)


class ProductVariantFrameSpecification(_FrameSpecification, Base):
    __tablename__ = "product_variant_frame_specifications"
    __table_args__ = (
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="CASCADE"),
        CheckConstraint(_POSITIVE_SPEC, name="dimensions"),
        CheckConstraint("version > 0", name="version"),
        CheckConstraint("symmetric IN (0,1) AND enabled IN (0,1)", name="flags"),
        Index("ix_variant_frame_specs_product", "product_id"),
    )
    variant_id: Mapped[str] = mapped_column(ID, primary_key=True)
    product_id: Mapped[str] = mapped_column(ID, nullable=False)


class MeowsurementSession(_Updated, Base):
    __tablename__ = "meowsurement_sessions"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["prescription_id", "user_id"], ["prescriptions.id", "prescriptions.user_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["id", "user_id", "current_revision_id"], ["meowsurement_revisions.session_id", "meowsurement_revisions.user_id", "meowsurement_revisions.id"], name="fk_meowsurement_current_revision", use_alter=True, ondelete="RESTRICT"),
        CheckConstraint("status IN ('draft','pending_review','needs_verification','needs_remeasure','approved')", name="status"),
        CheckConstraint("profile_version > 0 AND spec_version > 0 AND revision_number >= 0", name="versions"),
        CheckConstraint("spec_scope IN ('product','variant','manual')", name="spec_scope"),
        CheckConstraint("(spec_scope = 'manual' AND product_id IS NULL AND variant_id IS NULL) OR (spec_scope IN ('product','variant') AND product_id IS NOT NULL AND variant_id IS NOT NULL)", name="frame_source"),
        Index("ix_meowsurement_user_history", "user_id", "created_at", "id"),
        Index("ix_meowsurement_review_queue", "status", "updated_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=True)
    variant_id: Mapped[str | None] = mapped_column(ID)
    prescription_id: Mapped[str] = mapped_column(ID, nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    spec_version: Mapped[int] = mapped_column(Integer, nullable=False)
    spec_scope: Mapped[str] = mapped_column(String(16), default="product", server_default="product", nullable=False)
    examination_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="draft", server_default="draft", nullable=False)
    current_revision_id: Mapped[str | None] = mapped_column(ID)
    revision_number: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    frame_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    device: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class MeowsurementRevision(_Created, Base):
    __tablename__ = "meowsurement_revisions"
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", "id"),
        UniqueConstraint("session_id", "revision_number"),
        UniqueConstraint("id", "session_id", "user_id"),
        ForeignKeyConstraint(["session_id", "user_id"], ["meowsurement_sessions.id", "meowsurement_sessions.user_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["session_id", "user_id", "parent_revision_id"], ["meowsurement_revisions.session_id", "meowsurement_revisions.user_id", "meowsurement_revisions.id"], ondelete="RESTRICT"),
        CheckConstraint("revision_number > 0", name="number"),
        CheckConstraint("parent_revision_id IS NULL OR parent_revision_id <> id", name="parent"),
        Index("ix_meowsurement_revision_actor", "actor_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=_id)
    session_id: Mapped[str] = mapped_column(ID, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_revision_id: Mapped[str | None] = mapped_column(ID)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    algorithm_version: Mapped[str | None] = mapped_column(String(100))


class MeowsurementPhoto(_Created, Base):
    __tablename__ = "meowsurement_photos"
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", "id"),
        ForeignKeyConstraint(["session_id", "user_id"], ["meowsurement_sessions.id", "meowsurement_sessions.user_id"], ondelete="RESTRICT"),
        CheckConstraint("width > 0 AND height > 0 AND width * height <= 20000000", name="dimensions"),
        CheckConstraint("byte_size > 0 AND byte_size <= 8388608", name="size"),
        CheckConstraint("consent = 1", name="consent"),
        CheckConstraint("mime_type IN ('image/jpeg','image/png','image/webp')", name="mime"),
        Index("ix_meowsurement_photo_retention", "deleted_at", "expires_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=_id)
    session_id: Mapped[str] = mapped_column(ID, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str] = mapped_column(TOKEN, nullable=False)
    source_sha256: Mapped[str] = mapped_column(TOKEN, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(32), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    consent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class MeowsurementCapture(_Created, Base):
    __tablename__ = "meowsurement_captures"
    __table_args__ = (
        UniqueConstraint("revision_id", "capture_id"),
        UniqueConstraint("revision_id", "id"),
        ForeignKeyConstraint(["revision_id", "session_id", "user_id"], ["meowsurement_revisions.id", "meowsurement_revisions.session_id", "meowsurement_revisions.user_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["session_id", "user_id", "photo_id"], ["meowsurement_photos.session_id", "meowsurement_photos.user_id", "meowsurement_photos.id"], ondelete="RESTRICT"),
        CheckConstraint("view IN ('frontal','frontal_near','three_quarter_left','three_quarter_right','lateral_left','lateral_right')", name="view"),
        CheckConstraint("width > 0 AND height > 0 AND width * height <= 20000000", name="dimensions"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=_id)
    revision_id: Mapped[str] = mapped_column(ID, nullable=False)
    session_id: Mapped[str] = mapped_column(ID, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    capture_id: Mapped[str] = mapped_column(ID, nullable=False)
    view: Mapped[str] = mapped_column(String(32), nullable=False)
    photo_id: Mapped[str | None] = mapped_column(ID)
    photo_hash: Mapped[str | None] = mapped_column(TOKEN)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    calibration: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    landmarks: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    quality: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MeowsurementMeasurement(_Created, Base):
    __tablename__ = "meowsurement_measurements"
    __table_args__ = (
        UniqueConstraint("revision_id", "parameter"),
        UniqueConstraint("revision_id", "id"),
        ForeignKeyConstraint(["revision_id", "session_id", "user_id"], ["meowsurement_revisions.id", "meowsurement_revisions.session_id", "meowsurement_revisions.user_id"], ondelete="RESTRICT"),
        CheckConstraint("parameter IN ('distance_pd','near_pd','vertex_right','vertex_left','pantoscopic_right','pantoscopic_left','wrap_right','wrap_left')", name="parameter"),
        CheckConstraint("side IS NULL OR side IN ('right','left','both')", name="side"),
        CheckConstraint("unit IN ('mm','deg') AND valid IN (0,1)", name="unit_valid"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=_id)
    revision_id: Mapped[str] = mapped_column(ID, nullable=False)
    session_id: Mapped[str] = mapped_column(ID, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    parameter: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str | None] = mapped_column(String(8))
    unit: Mapped[str] = mapped_column(String(8), nullable=False)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(100), nullable=False)
    valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    quality: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MeowsurementMeasurementSource(Base):
    __tablename__ = "meowsurement_measurement_sources"
    __table_args__ = (
        ForeignKeyConstraint(["revision_id", "measurement_id"], ["meowsurement_measurements.revision_id", "meowsurement_measurements.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["revision_id", "capture_row_id"], ["meowsurement_captures.revision_id", "meowsurement_captures.id"], ondelete="RESTRICT"),
    )
    measurement_id: Mapped[str] = mapped_column(ID, primary_key=True)
    capture_row_id: Mapped[str] = mapped_column(ID, primary_key=True)
    revision_id: Mapped[str] = mapped_column(ID, nullable=False)


class MeowsurementReview(_Created, Base):
    __tablename__ = "meowsurement_reviews"
    __table_args__ = (
        ForeignKeyConstraint(["revision_id", "session_id", "user_id"], ["meowsurement_revisions.id", "meowsurement_revisions.session_id", "meowsurement_revisions.user_id"], ondelete="RESTRICT"),
        CheckConstraint("decision IN ('approved','needs_verification','needs_remeasure')", name="decision"),
        CheckConstraint("reviewer_id <> user_id", name="independent"),
        Index("ix_meowsurement_reviews_session", "session_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=_id)
    session_id: Mapped[str] = mapped_column(ID, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    revision_id: Mapped[str] = mapped_column(ID, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MeowsurementAuditEvent(_Created, Base):
    __tablename__ = "meowsurement_audit_events"
    __table_args__ = (
        ForeignKeyConstraint(["session_id", "user_id"], ["meowsurement_sessions.id", "meowsurement_sessions.user_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["revision_id", "session_id", "user_id"], ["meowsurement_revisions.id", "meowsurement_revisions.session_id", "meowsurement_revisions.user_id"], ondelete="RESTRICT"),
        CheckConstraint("revision_id IS NULL OR session_id IS NOT NULL", name="revision_owner"),
        Index("ix_meowsurement_audit_owner", "user_id", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(ID)
    revision_id: Mapped[str | None] = mapped_column(ID)
    actor_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
