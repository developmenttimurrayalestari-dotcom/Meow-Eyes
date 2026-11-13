"""Relational MySQL 5.7.24-log models for the Meow Eyes application.

Business routers and import services use explicit SQLAlchemy queries over
these tables.  Financial/catalog
relationships are relational; JSON is limited to variable product attributes,
provider envelopes, and deliberately dynamic configuration.

CHECK predicates remain in metadata for documentation and SQLite tests. MySQL
5.7 DDL omits them; the frozen 0002 migration installs BEFORE INSERT/UPDATE
validation triggers. Use Alembic, not metadata.create_all(), for MySQL setup.

Deletion policy: deactivate catalog/users and retain financial records.  A
referenced order/product/variant cannot be hard-deleted.  Simple nonfinancial
child rows may cascade.  Cross-row policies (payment transitions, completed
order eligibility, category cycles, promotion overlap, and inventory locking)
are enforced by transactional application services, in addition to FKs.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
import uuid

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Computed, ForeignKey,
    ForeignKeyConstraint, Index, Integer, JSON, Numeric, SmallInteger,
    String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CONTENT, ID, OPAQUE, TOKEN, UTCDateTime, utcnow

MONEY = Numeric(18, 2)


def new_id() -> str:
    """New SQL entities use full random UUIDs; imported IDs are retained."""
    return uuid.uuid4().hex


class CreatedMixin:
    # MySQL requires default precision to match DATETIME(6). SQLAlchemy
    # renders now(6) on MySQL and CURRENT_TIMESTAMP on SQLite.
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utcnow, server_default=func.now(6), nullable=False
    )


class UpdatedMixin(CreatedMixin):
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utcnow, onupdate=utcnow,
        server_default=func.now(6), nullable=False,
    )


# ----------------------- Identity and address book -----------------------
class User(UpdatedMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('customer','staff','admin','super_admin')", name="role"),
        CheckConstraint("points_balance >= 0", name="points_nonnegative"),
        CheckConstraint("pin_failed_attempts >= 0", name="pin_attempts_nonnegative"),
    )
    user_id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    # Stable Google account identity; email may change. NULL preserves old users.
    google_subject: Mapped[str | None] = mapped_column(
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    pin_hash: Mapped[str | None] = mapped_column(String(255))
    pin_failed_attempts: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    pin_locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime())
    role: Mapped[str] = mapped_column(String(32), server_default="customer", nullable=False)
    provider: Mapped[str] = mapped_column(String(32), server_default="password", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    points_balance: Mapped[int] = mapped_column(BigInteger, server_default="0", nullable=False)


class UserPermission(Base):
    __tablename__ = "user_permissions"
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    permission: Mapped[str] = mapped_column(String(100), primary_key=True)


class UserSession(CreatedMixin, Base):
    __tablename__ = "user_sessions"
    __table_args__ = (Index("ix_user_sessions_expiry", "expires_at"),)
    session_id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    # SHA-256 of the random session token. Existing cookies can survive the
    # migration by hashing their tokens during import and on each lookup.
    token_hash: Mapped[str] = mapped_column(TOKEN, unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Address(CreatedMixin, Base):
    __tablename__ = "addresses"
    __table_args__ = (UniqueConstraint("id", "user_id"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    street: Mapped[str] = mapped_column(Text, nullable=False)
    subdistrict: Mapped[str | None] = mapped_column(String(128))
    district: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    province: Mapped[str] = mapped_column(String(128), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), server_default="ID", nullable=False)
    everpro_destination_id: Mapped[str | None] = mapped_column(String(128))
    is_default: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    default_for_user: Mapped[str | None] = mapped_column(
        ID, Computed("CASE WHEN is_default = 1 THEN user_id ELSE NULL END", persisted=True), unique=True
    )


# ----------------------- Catalog and product options -----------------------
class Category(CreatedMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("group_type IN ('product_type','lens_type','gender','frame_shape','material','collection')", name="group_type"),
        CheckConstraint("group_type <> 'product_type' OR code IN ('frame','lens','package','accessories')", name="product_kind"),
        UniqueConstraint('group_type', 'code'),
        Index('ix_categories_group_sort', 'group_type', 'sort_order', 'id'),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    group_type: Mapped[str] = mapped_column(String(32), server_default='collection', nullable=False)
    code: Mapped[str] = mapped_column(String(64), default=new_id, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(Text)
    banner_image: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(255))
    seo_description: Mapped[str | None] = mapped_column(Text)


class Brand(CreatedMixin, Base):
    __tablename__ = "brands"
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    logo: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


class Product(UpdatedMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("product_type IN ('frame','lens','package','accessories')", name="type"),
        CheckConstraint("price >= 0 AND (discount_price IS NULL OR discount_price >= 0)", name="prices_nonnegative"),
        CheckConstraint("flash_sale_price IS NULL OR flash_sale_price >= 0", name="legacy_flash_nonnegative"),
        CheckConstraint("weight_gram >= 0 AND min_stock_alert >= 0", name="inventory_values"),
        CheckConstraint("rating_avg BETWEEN 0 AND 5 AND rating_count >= 0 AND sold_count >= 0", name="counters"),
        Index("ix_products_shop", "is_active", "product_type", "created_at", "id"),
        Index("ix_products_arrivals", "is_active", "product_type", "is_new_arrival", "created_at", "id"),
        Index("ix_products_admin_list", "deleted_at", "created_at", "id"),
        Index("ix_products_price", "is_active", "price", "id"),
        Index("ft_products_name_description", "name", "description", mysql_prefix="FULLTEXT"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    spec: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    product_type: Mapped[str] = mapped_column(String(16), server_default="frame", nullable=False)
    primary_category_id: Mapped[str | None] = mapped_column(ID, ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    brand_id: Mapped[str | None] = mapped_column(ID, ForeignKey("brands.id", ondelete="RESTRICT"), index=True)
    price: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(MONEY)
    # Retain the old product-level value for reconciliation; the authoritative
    # scheduled price will come from flash_sale_items, never this cache.
    flash_sale_price: Mapped[Decimal | None] = mapped_column(MONEY)
    weight_gram: Mapped[int] = mapped_column(Integer, server_default="100", nullable=False)
    dimension: Mapped[str | None] = mapped_column(String(255))
    main_image: Mapped[str] = mapped_column(Text, nullable=False)
    min_stock_alert: Mapped[int] = mapped_column(Integer, server_default="5", nullable=False)
    rating_avg: Mapped[Decimal] = mapped_column(Numeric(3, 2), server_default="0", nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    sold_count: Mapped[int] = mapped_column(BigInteger, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    is_new_arrival: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    # Deletion is distinct from temporarily disabling a product. Historical
    # orders, inventory, and measurement references retain their original IDs.
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    new_arrival_until: Mapped[datetime | None] = mapped_column(UTCDateTime())
    seo_title: Mapped[str | None] = mapped_column(String(255))
    seo_description: Mapped[str | None] = mapped_column(Text)


class ProductCategory(Base):
    __tablename__ = "product_categories"
    __table_args__ = (Index("ix_product_categories_category", "category_id", "product_id"),)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[str] = mapped_column(ID, ForeignKey("categories.id", ondelete="RESTRICT"), primary_key=True)


class ProductVariant(UpdatedMixin, Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("product_id", "id"),
        CheckConstraint("stock >= 0 AND reserved >= 0 AND reserved <= stock", name="inventory"),
        CheckConstraint("price_override IS NULL OR price_override >= 0", name="price"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    color: Mapped[str | None] = mapped_column(String(128))
    color_hex: Mapped[str | None] = mapped_column(String(16))
    size: Mapped[str | None] = mapped_column(String(100))
    lens_type: Mapped[str | None] = mapped_column(String(128))
    sku: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    price_override: Mapped[Decimal | None] = mapped_column(MONEY)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class ProductImage(Base):
    __tablename__ = "product_images"
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255))


class ProductSegment(Base):
    __tablename__ = "product_segments"
    __table_args__ = (Index("ix_product_segments_segment", "segment", "product_id"),)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    segment: Mapped[str] = mapped_column(String(64), primary_key=True)


class ProductBadge(Base):
    __tablename__ = "product_badges"
    __table_args__ = (Index("ix_product_badges_badge", "badge", "product_id"),)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    badge: Mapped[str] = mapped_column(String(64), primary_key=True)


class LensIndex(Base):
    __tablename__ = "lens_indexes"
    __table_args__ = (CheckConstraint("additional_price >= 0", name="price"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    index_value: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    thickness_level: Mapped[str] = mapped_column(String(32), server_default="medium", nullable=False)
    recommended_power_range: Mapped[str] = mapped_column(String(255), server_default="", nullable=False)
    additional_price: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


# ----------------------- Assets, prescriptions, and try-on -----------------------
class LensIndexType(Base):
    __tablename__ = "lens_index_types"
    lens_index_id: Mapped[str] = mapped_column(ID, ForeignKey("lens_indexes.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[str] = mapped_column(ID, ForeignKey("categories.id", ondelete="RESTRICT"), primary_key=True)
    __table_args__ = (Index("ix_lens_index_types_category", "category_id", "lens_index_id"),)


class Upload(CreatedMixin, Base):
    __tablename__ = "uploads"
    __table_args__ = (
        CheckConstraint("size >= 0", name="size"),
        CheckConstraint("visibility IN ('public','private')", name="visibility"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    url: Mapped[str | None] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime: Mapped[str] = mapped_column(String(128), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    subdir: Mapped[str | None] = mapped_column(String(128))
    disk_name: Mapped[str | None] = mapped_column(String(255))
    storage_provider: Mapped[str] = mapped_column(String(32), server_default="local", nullable=False)
    storage_key: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(16), server_default="public", nullable=False)
    sha256: Mapped[str | None] = mapped_column(TOKEN)
    uploaded_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), index=True)
    uploaded_by_name: Mapped[str | None] = mapped_column(String(255))


class Prescription(UpdatedMixin, Base):
    __tablename__ = "prescriptions"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        CheckConstraint("pd_total IS NULL OR pd_total > 0", name="pd_total"),
        CheckConstraint("pd_right IS NULL OR pd_right > 0", name="pd_right"),
        CheckConstraint("pd_left IS NULL OR pd_left > 0", name="pd_left"),
        CheckConstraint("(pd_right IS NULL AND pd_left IS NULL) OR (pd_right IS NOT NULL AND pd_left IS NOT NULL)", name="pd_pair"),
        CheckConstraint("pd_total IS NULL OR (pd_right IS NULL AND pd_left IS NULL)", name="pd_mode"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), index=True, nullable=False)
    pd_total: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    pd_right: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    pd_left: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    attachment_upload_id: Mapped[str | None] = mapped_column(ID, ForeignKey("uploads.id", ondelete="RESTRICT"))
    notes: Mapped[str | None] = mapped_column(Text)
    is_order_snapshot: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)


class PrescriptionEye(Base):
    __tablename__ = "prescription_eyes"
    __table_args__ = (
        CheckConstraint("eye IN ('right','left')", name="eye"),
        CheckConstraint("axis IS NULL OR axis BETWEEN 0 AND 180", name="axis"),
    )
    prescription_id: Mapped[str] = mapped_column(ID, ForeignKey("prescriptions.id", ondelete="CASCADE"), primary_key=True)
    eye: Mapped[str] = mapped_column(String(5), primary_key=True)
    sph: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    cyl: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    axis: Mapped[int | None] = mapped_column(SmallInteger)
    add: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))


class VirtualTryOnAsset(UpdatedMixin, Base):
    __tablename__ = "virtual_try_on_assets"
    __table_args__ = (
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        CheckConstraint("asset_type IN ('image','glb','gltf')", name="asset_type"),
        CheckConstraint("scale > 0", name="scale"),
        CheckConstraint("status IN ('draft','published','archived')", name="status"),
        CheckConstraint("upload_id IS NOT NULL OR source_url IS NOT NULL", name="source"),
        Index("ix_vto_product_status", "product_id", "status", "sort_order"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id: Mapped[str | None] = mapped_column(ID)
    asset_type: Mapped[str] = mapped_column(String(8), nullable=False)
    upload_id: Mapped[str | None] = mapped_column(ID, ForeignKey("uploads.id", ondelete="RESTRICT"))
    source_url: Mapped[str | None] = mapped_column(Text)
    preview_url: Mapped[str | None] = mapped_column(Text)
    scale: Mapped[Decimal] = mapped_column(Numeric(10, 5), server_default="1", nullable=False)
    offset_x: Mapped[Decimal] = mapped_column(Numeric(10, 5), server_default="0", nullable=False)
    offset_y: Mapped[Decimal] = mapped_column(Numeric(10, 5), server_default="0", nullable=False)
    offset_z: Mapped[Decimal] = mapped_column(Numeric(10, 5), server_default="0", nullable=False)
    rotation_x: Mapped[Decimal] = mapped_column(Numeric(10, 5), server_default="0", nullable=False)
    rotation_y: Mapped[Decimal] = mapped_column(Numeric(10, 5), server_default="0", nullable=False)
    rotation_z: Mapped[Decimal] = mapped_column(Numeric(10, 5), server_default="0", nullable=False)
    calibration: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), server_default="draft", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    updated_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))


# ----------------------- Cart and shipping quotation -----------------------
class CartItem(UpdatedMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["lens_product_id", "lens_variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["prescription_id", "user_id"], ["prescriptions.id", "prescriptions.user_id"], ondelete="RESTRICT"),
        CheckConstraint("quantity > 0", name="quantity"),
        CheckConstraint("lens_variant_id IS NULL OR lens_product_id IS NOT NULL", name="lens_variant_owner"),
        Index("ix_cart_items_user_created", "user_id", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id: Mapped[str | None] = mapped_column(ID)
    quantity: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    lens_product_id: Mapped[str | None] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"))
    lens_variant_id: Mapped[str | None] = mapped_column(ID)
    lens_index_id: Mapped[str | None] = mapped_column(ID, ForeignKey("lens_indexes.id", ondelete="RESTRICT"))
    prescription_id: Mapped[str | None] = mapped_column(ID)


class ShippingQuote(CreatedMixin, Base):
    __tablename__ = "shipping_quotes"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        CheckConstraint("weight_gram > 0 AND cost >= 0 AND insurance_cost >= 0", name="amounts"),
        Index("ix_shipping_quotes_user_expiry", "user_id", "expires_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), server_default="everpro", nullable=False)
    provider_quote_id: Mapped[str | None] = mapped_column(String(191))
    origin_id: Mapped[str] = mapped_column(String(128), nullable=False)
    destination_id: Mapped[str] = mapped_column(String(128), nullable=False)
    courier_code: Mapped[str] = mapped_column(String(64), nullable=False)
    service_code: Mapped[str] = mapped_column(String(64), nullable=False)
    service_label: Mapped[str | None] = mapped_column(String(255))
    weight_gram: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    insurance_cost: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), server_default="IDR", nullable=False)
    estimated_delivery: Mapped[str | None] = mapped_column(String(128))
    cart_fingerprint: Mapped[str] = mapped_column(TOKEN, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    request_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)


# ----------------------- Orders and immutable purchase snapshots -----------------------
class Order(UpdatedMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        ForeignKeyConstraint(["shipping_quote_id", "user_id"], ["shipping_quotes.id", "shipping_quotes.user_id"], ondelete="RESTRICT"),
        CheckConstraint("status IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')", name="status"),
        CheckConstraint("payment_status IN ('pending','paid','failed','expired','cancelled','refunded')", name="payment_status"),
        CheckConstraint("shipment_status IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')", name="shipment_status"),
        CheckConstraint("subtotal >= 0 AND discount >= 0 AND flash_sale_discount >= 0 AND voucher_discount >= 0", name="discount_amounts"),
        CheckConstraint("points_used >= 0 AND points_discount >= 0 AND roulette_discount >= 0 AND shipping_cost >= 0 AND total >= 0", name="amounts"),
        Index("ix_orders_customer_date", "user_id", "created_at", "id"),
        Index("ix_orders_expiry", "status", "reservation_expires_at", "id"),
        Index("ix_orders_payment_date", "payment_status", "created_at"),
        Index("ix_orders_shipment_status", "shipment_status", "updated_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    discount: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    flash_sale_discount: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    voucher_code: Mapped[str | None] = mapped_column(String(128))
    voucher_discount: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    points_used: Mapped[int] = mapped_column(BigInteger, server_default="0", nullable=False)
    points_discount: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    roulette_discount: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    shipping_quote_id: Mapped[str | None] = mapped_column(ID)
    shipping_courier: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_service: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_cost: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    total: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), server_default="IDR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), server_default="pending_payment", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), server_default="pending", nullable=False)
    shipment_status: Mapped[str] = mapped_column(String(32), server_default="pending", nullable=False)
    reservation_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    checkout_idempotency_key: Mapped[str | None] = mapped_column(OPAQUE, unique=True)


class OrderAddress(Base):
    __tablename__ = "order_addresses"
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), primary_key=True)
    # These source references are deliberately snapshots, not live address FKs.
    source_address_id: Mapped[str | None] = mapped_column(ID)
    source_created_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    source_is_default: Mapped[bool | None] = mapped_column(Boolean)
    label: Mapped[str | None] = mapped_column(String(100))
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    street: Mapped[str] = mapped_column(Text, nullable=False)
    subdistrict: Mapped[str | None] = mapped_column(String(128))
    district: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    province: Mapped[str] = mapped_column(String(128), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(16), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), server_default="ID", nullable=False)
    everpro_destination_id: Mapped[str | None] = mapped_column(String(128))


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("id", "order_id"),
        UniqueConstraint("id", "product_id"),
        UniqueConstraint("id", "order_id", "product_id"),
        UniqueConstraint("order_id", "sort_order"),
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        CheckConstraint("quantity > 0 AND unit_price >= 0 AND subtotal >= 0", name="amounts"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    variant_id: Mapped[str | None] = mapped_column(ID)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(128))
    variant_label: Mapped[str | None] = mapped_column(String(255))
    main_image: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class OrderItemComponent(Base):
    __tablename__ = "order_item_components"
    __table_args__ = (
        UniqueConstraint("id", "order_id", "product_id"),
        UniqueConstraint("order_item_id", "sort_order"),
        ForeignKeyConstraint(["order_item_id", "order_id"], ["order_items.id", "order_items.order_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        CheckConstraint("component_type IN ('primary','lens')", name="type"),
        CheckConstraint("quantity > 0 AND unit_price >= 0 AND subtotal >= 0 AND index_surcharge >= 0", name="amounts"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_item_id: Mapped[str] = mapped_column(ID, nullable=False)
    order_id: Mapped[str] = mapped_column(ID, nullable=False)
    component_type: Mapped[str] = mapped_column(String(16), nullable=False)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    variant_id: Mapped[str | None] = mapped_column(ID)
    lens_index_id: Mapped[str | None] = mapped_column(ID, ForeignKey("lens_indexes.id", ondelete="RESTRICT"))
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(128))
    variant_label: Mapped[str | None] = mapped_column(String(255))
    lens_index_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    index_surcharge: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class OrderItemPrescription(Base):
    __tablename__ = "order_item_prescriptions"
    __table_args__ = (
        ForeignKeyConstraint(["order_item_id", "order_id"], ["order_items.id", "order_items.order_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["order_id", "user_id"], ["orders.id", "orders.user_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["prescription_id", "user_id"], ["prescriptions.id", "prescriptions.user_id"], ondelete="RESTRICT"),
    )
    order_item_id: Mapped[str] = mapped_column(ID, primary_key=True)
    order_id: Mapped[str] = mapped_column(ID, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    prescription_id: Mapped[str] = mapped_column(ID, unique=True, nullable=False)


class OrderStatusLog(CreatedMixin, Base):
    __tablename__ = "order_status_logs"
    __table_args__ = (Index("ix_order_status_logs_timeline", "order_id", "created_at", "id"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    admin_id: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))


class StockReservation(CreatedMixin, Base):
    __tablename__ = "stock_reservations"
    __table_args__ = (
        ForeignKeyConstraint(["order_item_id", "order_id"], ["order_items.id", "order_items.order_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        CheckConstraint("quantity > 0", name="quantity"),
        CheckConstraint("status IN ('active','confirmed','expired','cancelled')", name="status"),
        Index("ix_stock_reservations_expiry", "status", "expires_at", "id"),
        Index("ix_stock_reservations_order", "order_id", "status"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    order_item_id: Mapped[str | None] = mapped_column(ID)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id: Mapped[str | None] = mapped_column(ID)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="active", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class StockMovement(CreatedMixin, Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        ForeignKeyConstraint(["product_id", "variant_id"], ["product_variants.product_id", "product_variants.id"], ondelete="RESTRICT"),
        CheckConstraint("quantity >= 0", name="quantity"),
        CheckConstraint("stock_after IS NULL OR stock_after >= 0", name="stock_after"),
        CheckConstraint("reserved_after IS NULL OR reserved_after >= 0", name="reserved_after"),
        Index("ix_stock_movements_product_date", "product_id", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id: Mapped[str | None] = mapped_column(ID)
    order_id: Mapped[str | None] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), index=True)
    reservation_id: Mapped[str | None] = mapped_column(ID, ForeignKey("stock_reservations.id", ondelete="RESTRICT"))
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    ttb_number: Mapped[str | None] = mapped_column(String(128))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int | None] = mapped_column(Integer)
    reserved_delta: Mapped[int | None] = mapped_column(Integer)
    stock_after: Mapped[int | None] = mapped_column(Integer)
    reserved_after: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    admin_id: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))


# ----------------------- Promotions -----------------------
class Voucher(CreatedMixin, Base):
    __tablename__ = "vouchers"
    __table_args__ = (
        CheckConstraint("discount_type IN ('percent','nominal','free_shipping')", name="type"),
        CheckConstraint("discount_value >= 0 AND min_purchase >= 0 AND (max_discount IS NULL OR max_discount >= 0)", name="amounts"),
        CheckConstraint("discount_type <> 'percent' OR discount_value <= 100", name="percentage"),
        CheckConstraint("quota >= 0 AND used_count >= 0 AND used_count <= quota AND quota_per_user >= 0", name="quotas"),
        CheckConstraint("end_at > start_at", name="window"),
        Index("ix_vouchers_window", "is_active", "start_at", "end_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    min_purchase: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    max_discount: Mapped[Decimal | None] = mapped_column(MONEY)
    quota: Mapped[int] = mapped_column(Integer, server_default="100", nullable=False)
    used_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    quota_per_user: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    start_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    end_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


class VoucherRedemption(CreatedMixin, Base):
    __tablename__ = "voucher_redemptions"
    __table_args__ = (
        ForeignKeyConstraint(["order_id", "user_id"], ["orders.id", "orders.user_id"], ondelete="RESTRICT"),
        CheckConstraint("discount_amount >= 0", name="amount"),
        CheckConstraint("status IN ('reserved','redeemed','released')", name="status"),
        Index("ix_voucher_redemptions_quota", "voucher_id", "user_id", "status"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    voucher_id: Mapped[str] = mapped_column(ID, ForeignKey("vouchers.id", ondelete="RESTRICT"), nullable=False)
    order_id: Mapped[str] = mapped_column(ID, unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="reserved", nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class FlashSale(CreatedMixin, Base):
    __tablename__ = "flash_sales"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="window"),
        Index("ix_flash_sales_window", "is_active", "start_at", "end_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    end_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class FlashSaleCategory(Base):
    __tablename__ = "flash_sale_categories"
    __table_args__ = (
        CheckConstraint("discount_type IN ('percent','nominal','fixed_price')", name="type"),
        CheckConstraint("discount_value >= 0 AND quota_per_product >= 0", name="amounts"),
        CheckConstraint("discount_type <> 'percent' OR discount_value <= 100", name="percentage"),
    )
    flash_sale_id: Mapped[str] = mapped_column(ID, ForeignKey("flash_sales.id", ondelete="RESTRICT"), primary_key=True)
    category_id: Mapped[str] = mapped_column(ID, ForeignKey("categories.id", ondelete="RESTRICT"), primary_key=True)
    include_descendants: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    discount_type: Mapped[str] = mapped_column(String(16), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    quota_per_product: Mapped[int] = mapped_column(Integer, nullable=False)


class FlashSaleItem(Base):
    __tablename__ = "flash_sale_items"
    __table_args__ = (
        UniqueConstraint("flash_sale_id", "product_id"),
        UniqueConstraint("id", "product_id"),
        ForeignKeyConstraint(["flash_sale_id", "source_category_id"], ["flash_sale_categories.flash_sale_id", "flash_sale_categories.category_id"], ondelete="RESTRICT"),
        CheckConstraint("flash_price >= 0", name="price"),
        CheckConstraint("quota >= 0 AND sold >= 0 AND reserved >= 0 AND sold + reserved <= quota", name="quota"),
        Index("ix_flash_sale_items_product", "product_id", "flash_sale_id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    flash_sale_id: Mapped[str] = mapped_column(ID, ForeignKey("flash_sales.id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    source_category_id: Mapped[str | None] = mapped_column(ID)
    flash_price: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    quota: Mapped[int] = mapped_column(Integer, nullable=False)
    sold: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


class FlashSaleReservation(CreatedMixin, Base):
    __tablename__ = "flash_sale_reservations"
    __table_args__ = (
        UniqueConstraint("order_item_id", "flash_sale_item_id"),
        ForeignKeyConstraint(["order_item_id", "product_id"], ["order_items.id", "order_items.product_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["flash_sale_item_id", "product_id"], ["flash_sale_items.id", "flash_sale_items.product_id"], ondelete="RESTRICT"),
        CheckConstraint("quantity > 0", name="quantity"),
        CheckConstraint("status IN ('active','confirmed','expired','cancelled')", name="status"),
        Index("ix_flash_sale_reservations_expiry", "status", "expires_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_item_id: Mapped[str] = mapped_column(ID, nullable=False)
    flash_sale_item_id: Mapped[str] = mapped_column(ID, nullable=False)
    product_id: Mapped[str] = mapped_column(ID, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="active", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


# ----------------------- DOKU / Everpro integration state -----------------------
class Payment(UpdatedMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("provider", "request_id"),
        UniqueConstraint("provider", "merchant_reference"),
        UniqueConstraint("provider", "external_id"),
        UniqueConstraint("id", "order_id"),
        CheckConstraint("amount >= 0", name="amount"),
        CheckConstraint("status IN ('pending','paid','failed','expired','cancelled','refunded')", name="status"),
        Index("ix_payments_order_status", "order_id", "status", "created_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), server_default="doku", nullable=False)
    request_id: Mapped[str] = mapped_column(OPAQUE, nullable=False)
    merchant_reference: Mapped[str] = mapped_column(OPAQUE, nullable=False)
    external_id: Mapped[str | None] = mapped_column(OPAQUE)
    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), server_default="IDR", nullable=False)
    method: Mapped[str | None] = mapped_column(String(64))
    channel: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), server_default="pending", nullable=False)
    payment_url: Mapped[str | None] = mapped_column(Text)
    virtual_account_number: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class PaymentLog(CreatedMixin, Base):
    __tablename__ = "payment_logs"
    __table_args__ = (
        ForeignKeyConstraint(["payment_id", "order_id"], ["payments.id", "payments.order_id"], ondelete="RESTRICT"),
        Index("ix_payment_logs_order_date", "order_id", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    payment_id: Mapped[str | None] = mapped_column(ID)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Shipment(UpdatedMixin, Base):
    __tablename__ = "shipments"
    __table_args__ = (
        UniqueConstraint("provider", "request_id"),
        UniqueConstraint("provider", "external_id"),
        UniqueConstraint("id", "order_id"),
        CheckConstraint("cost >= 0", name="cost"),
        CheckConstraint("status IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')", name="status"),
        Index("ix_shipments_order", "order_id", "created_at"),
        Index("ix_shipments_tracking", "provider", "tracking_number"),
        Index("ix_shipments_poll", "status", "last_checked_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), server_default="everpro", nullable=False)
    request_id: Mapped[str] = mapped_column(OPAQUE, nullable=False)
    external_id: Mapped[str | None] = mapped_column(OPAQUE)
    courier_code: Mapped[str] = mapped_column(String(64), nullable=False)
    service_code: Mapped[str] = mapped_column(String(64), nullable=False)
    tracking_number: Mapped[str | None] = mapped_column(OPAQUE)
    label_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), server_default="pending", nullable=False)
    carrier_status: Mapped[str | None] = mapped_column(String(255))
    cost: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), server_default="IDR", nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    shipped_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ShipmentLog(CreatedMixin, Base):
    __tablename__ = "shipment_logs"
    __table_args__ = (
        ForeignKeyConstraint(["shipment_id", "order_id"], ["shipments.id", "shipments.order_id"], ondelete="RESTRICT"),
        Index("ix_shipment_logs_order_date", "order_id", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    shipment_id: Mapped[str | None] = mapped_column(ID)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class IntegrationWebhookEvent(Base):
    __tablename__ = "integration_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_key"),
        CheckConstraint("status IN ('received','processed','failed','ignored')", name="status"),
        CheckConstraint("attempts >= 0", name="attempts"),
        Index("ix_webhook_events_retry", "status", "received_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    event_key: Mapped[str] = mapped_column(OPAQUE, nullable=False)
    payload_hash: Mapped[str] = mapped_column(TOKEN, nullable=False)
    order_id: Mapped[str | None] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"))
    event_type: Mapped[str | None] = mapped_column(String(128))
    signature_verified: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="received", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(128))
    received_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, server_default=func.now(6), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


# ----------------------- Verified product and transaction ratings -----------------------
class ProductReview(UpdatedMixin, Base):
    __tablename__ = "product_reviews"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", "user_id"),
        ForeignKeyConstraint(["order_id", "user_id"], ["orders.id", "orders.user_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["order_item_id", "order_id", "product_id"], ["order_items.id", "order_items.order_id", "order_items.product_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["order_component_id", "order_id", "product_id"], ["order_item_components.id", "order_item_components.order_id", "order_item_components.product_id"], ondelete="RESTRICT"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating"),
        CheckConstraint("status IN ('pending','approved','rejected','hidden')", name="status"),
        CheckConstraint("order_item_id IS NULL OR order_component_id IS NULL", name="one_purchase_line"),
        CheckConstraint("(order_item_id IS NULL AND order_component_id IS NULL) OR order_id IS NOT NULL", name="line_requires_order"),
        CheckConstraint("verified_purchase = 0 OR (order_id IS NOT NULL AND (order_item_id IS NOT NULL OR order_component_id IS NOT NULL))", name="verified_purchase"),
        Index("ix_product_reviews_public", "product_id", "status", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    # Nullable purchase links are only for explicitly unverified legacy reviews.
    # New review services require a confirmed paid purchase and set verified=True.
    order_id: Mapped[str | None] = mapped_column(ID)
    order_item_id: Mapped[str | None] = mapped_column(ID)
    order_component_id: Mapped[str | None] = mapped_column(ID)
    verified_purchase: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="pending", nullable=False)
    admin_reply: Mapped[str | None] = mapped_column(Text)
    moderated_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))
    moderated_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ProductReviewImage(Base):
    __tablename__ = "product_review_images"
    review_id: Mapped[str] = mapped_column(ID, ForeignKey("product_reviews.id", ondelete="CASCADE"), primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)


class OrderReview(UpdatedMixin, Base):
    __tablename__ = "order_reviews"
    __table_args__ = (
        ForeignKeyConstraint(["order_id", "user_id"], ["orders.id", "orders.user_id"], ondelete="RESTRICT"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating"),
        CheckConstraint("status IN ('pending','approved','rejected','hidden')", name="status"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ID, unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), server_default="pending", nullable=False)
    admin_reply: Mapped[str | None] = mapped_column(Text)
    moderated_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))
    moderated_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Wishlist(CreatedMixin, Base):
    __tablename__ = "wishlists"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)


# ----------------------- Games, rewards, and subscriptions -----------------------
class Game(CreatedMixin, Base):
    __tablename__ = "games"
    __table_args__ = (CheckConstraint("max_points >= 0", name="max_points"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    key: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    image: Mapped[str | None] = mapped_column(Text)
    max_points: Mapped[int] = mapped_column(Integer, server_default="50", nullable=False)


class GameScore(Base):
    __tablename__ = "game_scores"
    __table_args__ = (
        CheckConstraint("score >= 0 AND points_awarded >= 0", name="scores"),
        Index("ix_game_scores_daily", "user_id", "game", "played_at"),
        Index("ix_game_scores_leaderboard", "game", "score", "user_id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    game: Mapped[str] = mapped_column(String(32), ForeignKey("games.key", ondelete="RESTRICT"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    points_awarded: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    played_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, server_default=func.now(6), nullable=False)


class RouletteReward(Base):
    __tablename__ = "roulette_rewards"
    __table_args__ = (
        CheckConstraint("type IN ('points','voucher','free_shipping','discount','nothing')", name="type"),
        CheckConstraint("value >= 0 AND probability >= 0", name="amounts"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    color: Mapped[str] = mapped_column(String(16), server_default="#FF6B6B", nullable=False)
    # The old implementation uses a nonnegative *weight*, not a normalized
    # probability, so values above 1 remain valid and are not discarded.
    probability: Mapped[Decimal] = mapped_column(Numeric(18, 8), server_default="0.1", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


class RouletteSpin(CreatedMixin, Base):
    __tablename__ = "roulette_spins"
    __table_args__ = (
        UniqueConstraint("id", "user_id"),
        CheckConstraint("reward_value >= 0", name="value"),
        Index("ix_roulette_spins_user_date", "user_id", "created_at"),
        Index("ix_roulette_spins_eligibility", "user_id", "used", "expires_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    reward_id: Mapped[str] = mapped_column(ID, ForeignKey("roulette_rewards.id", ondelete="RESTRICT"), nullable=False)
    reward_label: Mapped[str] = mapped_column(String(255), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reward_value: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class RouletteRedemption(CreatedMixin, Base):
    __tablename__ = "roulette_redemptions"
    __table_args__ = (
        UniqueConstraint("spin_id", "order_id"),
        ForeignKeyConstraint(["spin_id", "user_id"], ["roulette_spins.id", "roulette_spins.user_id"], ondelete="RESTRICT"),
        ForeignKeyConstraint(["order_id", "user_id"], ["orders.id", "orders.user_id"], ondelete="RESTRICT"),
        CheckConstraint("status IN ('reserved','redeemed','released')", name="status"),
        CheckConstraint("discount_amount >= 0", name="discount"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    spin_id: Mapped[str] = mapped_column(ID, nullable=False)
    order_id: Mapped[str] = mapped_column(ID, unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ID, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="reserved", nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(MONEY, server_default="0", nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    # A released reward may be reused, but two live orders cannot reserve it.
    active_spin_id: Mapped[str | None] = mapped_column(
        ID, Computed("CASE WHEN status IN ('reserved','redeemed') THEN spin_id ELSE NULL END", persisted=True), unique=True
    )


class PointLog(CreatedMixin, Base):
    __tablename__ = "point_logs"
    __table_args__ = (
        CheckConstraint("balance_after >= 0", name="balance"),
        Index("ix_point_logs_user_type_date", "user_id", "type", "created_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    delta: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_id: Mapped[str | None] = mapped_column(ID, ForeignKey("orders.id", ondelete="RESTRICT"))


class NewsletterSubscriber(CreatedMixin, Base):
    __tablename__ = "newsletter_subscribers"
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


class NewsletterCampaign(CreatedMixin, Base):
    __tablename__ = "newsletter_campaigns"
    __table_args__ = (CheckConstraint("sent_count >= 0 AND failed_count >= 0", name="counts"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    segment: Mapped[str] = mapped_column(String(64), server_default="all", nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class ProductSubscription(CreatedMixin, Base):
    __tablename__ = "product_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    notify_stock: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    notify_price_drop: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    notify_flash_sale: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


# ----------------------- Articles, product knowledge, and CMS -----------------------
class ArticleCategory(CreatedMixin, Base):
    __tablename__ = "article_categories"
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class Article(UpdatedMixin, Base):
    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint("status IN ('draft','published','unpublished','archived')", name="status"),
        CheckConstraint("view_count >= 0", name="views"),
        Index("ix_articles_public", "status", "published_at", "id"),
        Index("ix_articles_category", "category_id", "status", "published_at", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    category_id: Mapped[str | None] = mapped_column(ID, ForeignKey("article_categories.id", ondelete="RESTRICT"))
    author_id: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))
    author_name: Mapped[str] = mapped_column(String(255), server_default="Admin Meow", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(CONTENT, nullable=False)
    thumbnail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), server_default="draft", nullable=False)
    view_count: Mapped[int] = mapped_column(BigInteger, server_default="0", nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(255))
    seo_description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ArticleTag(Base):
    __tablename__ = "article_tags"
    article_id: Mapped[str] = mapped_column(ID, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(String(128), primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class ProductKnowledge(UpdatedMixin, Base):
    __tablename__ = "product_knowledges"
    __table_args__ = (
        CheckConstraint("knowledge_type IN ('frame_shape','material','lens_type','lens_index','buying_guide')", name="type"),
        CheckConstraint("status IN ('draft','published','unpublished','archived')", name="status"),
        Index("ix_knowledge_public", "knowledge_type", "status", "sort_order", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    knowledge_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(CONTENT, nullable=False)
    image: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(Text)
    face_shape_recommendation: Mapped[str | None] = mapped_column(Text)
    style_recommendation: Mapped[str | None] = mapped_column(Text)
    filter_param: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="draft", nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(255))
    seo_description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ProductKnowledgeBullet(Base):
    __tablename__ = "product_knowledge_bullets"
    __table_args__ = (CheckConstraint("kind IN ('pro','con')", name="kind"),)
    knowledge_id: Mapped[str] = mapped_column(ID, ForeignKey("product_knowledges.id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(String(3), primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class ProductKnowledgeProduct(Base):
    __tablename__ = "product_knowledge_products"
    knowledge_id: Mapped[str] = mapped_column(ID, ForeignKey("product_knowledges.id", ondelete="CASCADE"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"), primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class FAQCategory(Base):
    __tablename__ = "faq_categories"
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class FAQ(CreatedMixin, Base):
    __tablename__ = "faqs"
    __table_args__ = (Index("ix_faqs_public", "category_id", "is_active", "sort_order"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    category_id: Mapped[str | None] = mapped_column(ID, ForeignKey("faq_categories.id", ondelete="RESTRICT"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class CMSPage(UpdatedMixin, Base):
    __tablename__ = "cms_pages"
    __table_args__ = (
        CheckConstraint("page_type IN ('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')", name="page_type"),
        CheckConstraint("status IN ('draft','published','unpublished','archived')", name="status"),
        CheckConstraint("version > 0", name="version"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    page_type: Mapped[str] = mapped_column(String(32), server_default="custom", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(CONTENT, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="draft", nullable=False)
    version: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(255))
    seo_description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Banner(CreatedMixin, Base):
    __tablename__ = "banners"
    __table_args__ = (
        CheckConstraint("link_type IN ('internal','product','category','shop_now','flash_sale','article','external','none')", name="link_type"),
        CheckConstraint("target_device IN ('desktop','mobile','all')", name="target_device"),
        CheckConstraint("start_at IS NULL OR end_at IS NULL OR end_at > start_at", name="window"),
        Index("ix_banners_display", "position", "is_active", "sort_order", "id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    image_desktop: Mapped[str] = mapped_column(Text, nullable=False)
    image_mobile: Mapped[str | None] = mapped_column(Text)
    link_type: Mapped[str] = mapped_column(String(16), server_default="internal", nullable=False)
    link_url: Mapped[str] = mapped_column(Text, nullable=False)
    link_product_id: Mapped[str | None] = mapped_column(ID, ForeignKey("products.id", ondelete="RESTRICT"))
    link_category_id: Mapped[str | None] = mapped_column(ID, ForeignKey("categories.id", ondelete="RESTRICT"))
    link_article_id: Mapped[str | None] = mapped_column(ID, ForeignKey("articles.id", ondelete="RESTRICT"))
    link_flash_sale_id: Mapped[str | None] = mapped_column(ID, ForeignKey("flash_sales.id", ondelete="RESTRICT"))
    position: Mapped[str] = mapped_column(String(64), server_default="hero", nullable=False)
    target_device: Mapped[str] = mapped_column(String(16), server_default="all", nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    end_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


# ----------------------- Store and WhatsApp configuration -----------------------
class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    updated_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow, server_default=func.now(6), nullable=False)


class WhatsAppSetting(Base):
    __tablename__ = "whatsapp_settings"
    __table_args__ = (CheckConstraint("id = 1", name="singleton"),)
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False, default=1)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    default_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)
    updated_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow, server_default=func.now(6), nullable=False)


class ContactSetting(Base):
    __tablename__ = "contact_settings"
    __table_args__ = (CheckConstraint("singleton_key = 1", name="singleton"),)
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    singleton_key: Mapped[int] = mapped_column(SmallInteger, server_default="1", unique=True, nullable=False)
    store_name: Mapped[str] = mapped_column(String(255), server_default="Meow Eyes", nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    operational_hours: Mapped[str] = mapped_column(String(255), nullable=False)
    instagram: Mapped[str | None] = mapped_column(Text)
    facebook: Mapped[str | None] = mapped_column(Text)
    tiktok: Mapped[str | None] = mapped_column(Text)
    tokopedia: Mapped[str | None] = mapped_column(Text)
    shopee: Mapped[str | None] = mapped_column(Text)
    google_maps_embed: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow, server_default=func.now(6), nullable=False)


class ContactMessage(CreatedMixin, Base):
    __tablename__ = "contact_messages"
    __table_args__ = (
        CheckConstraint("status IN ('new','read','replied')", name="status"),
        Index("ix_contact_messages_inbox", "status", "created_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    subject: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="new", nullable=False)


# ----------------------- Future ETL provenance (no source payloads) -----------------------
class MigrationRun(Base):
    __tablename__ = "migration_runs"
    __table_args__ = (
        CheckConstraint("status IN ('planned','running','validated','failed','completed')", name="status"),
        CheckConstraint("source_count >= 0 AND migrated_count >= 0 AND rejected_count >= 0", name="counts"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    export_checksum: Mapped[str | None] = mapped_column(TOKEN)
    schema_revision: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="planned", nullable=False)
    source_count: Mapped[int] = mapped_column(BigInteger, server_default="0", nullable=False)
    migrated_count: Mapped[int] = mapped_column(BigInteger, server_default="0", nullable=False)
    rejected_count: Mapped[int] = mapped_column(BigInteger, server_default="0", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class MigrationRecord(Base):
    __tablename__ = "migration_records"
    __table_args__ = (
        UniqueConstraint("run_id", "source_collection", "source_id", "target_table", "target_id"),
        CheckConstraint("status IN ('planned','imported','verified','rejected')", name="status"),
        Index("ix_migration_records_source", "source_collection", "source_id"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ID, ForeignKey("migration_runs.id", ondelete="RESTRICT"), index=True, nullable=False)
    source_collection: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(OPAQUE, nullable=False)
    source_checksum: Mapped[str] = mapped_column(TOKEN, nullable=False)
    target_table: Mapped[str] = mapped_column(String(64), nullable=False)
    # Generic provenance intentionally does not create a polymorphic FK.
    # Composite association keys can be encoded here as a canonical JSON string.
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), server_default="planned", nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class MigrationIssue(CreatedMixin, Base):
    __tablename__ = "migration_issues"
    __table_args__ = (
        CheckConstraint("severity IN ('info','warning','error')", name="severity"),
        Index("ix_migration_issues_resolution", "run_id", "severity", "resolved_at"),
    )
    id: Mapped[str] = mapped_column(ID, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ID, ForeignKey("migration_runs.id", ondelete="RESTRICT"), nullable=False)
    record_id: Mapped[str | None] = mapped_column(ID, ForeignKey("migration_records.id", ondelete="RESTRICT"))
    source_collection: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(OPAQUE, nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(128))
    issue_code: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), server_default="error", nullable=False)
    # Store a sanitized explanation only: no credential, prescription image,
    # medical measurement, full source document, or payment secret.
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    resolved_by: Mapped[str | None] = mapped_column(ID, ForeignKey("users.user_id", ondelete="RESTRICT"))


# Customer-owned optical measurements are registered after the ecommerce models.
from .meowsurement_models import (  # noqa: E402,F401
    CustomerProfile, ProductFrameSpecification, ProductVariantFrameSpecification,
    MeowsurementSession, MeowsurementRevision, MeowsurementPhoto,
    MeowsurementCapture, MeowsurementMeasurement, MeowsurementMeasurementSource,
    MeowsurementReview, MeowsurementAuditEvent,
)
from .engagement_models import (PointSettings, PointRateVersion, PointLot, PointHistory, PointRedemption,
    GameRule, PuzzleLevel, GameSession, CashbackEvent, CashbackAward,
    ReturnCase, ReturnCaseItem, ReturnEvidence, ReturnTimeline)  # noqa: E402,F401
