"""Pydantic models for Meow Eyes marketplace.

HTTP DTOs retain the existing string IDs and ISO timestamps for React.
Persistent SQLAlchemy models, UTC datetimes and Decimal money live in mysql/models.py.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid
from mysql.taxonomy_definitions import GroupType, ProductType


def gen_id(prefix: str = "") -> str:
    base = uuid.uuid4().hex[:16]
    return f"{prefix}_{base}" if prefix else base


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Auth / User ----------
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str = Field(default_factory=lambda: gen_id("usr"))
    email: EmailStr
    name: str
    picture: Optional[str] = None
    password_hash: Optional[str] = None
    pin_hash: Optional[str] = None
    pin_failed_attempts: int = 0
    pin_locked_until: Optional[str] = None
    role: Literal["customer", "staff", "admin", "super_admin"] = "customer"
    provider: Literal["password", "google"] = "password"
    is_active: bool = True
    points_balance: int = 0
    permissions: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class UserPublic(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    role: str
    provider: str
    has_pin: bool = False
    points_balance: int = 0
    permissions: List[str] = Field(default_factory=list)
    created_at: str


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PinSetupRequest(BaseModel):
    pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class PinVerifyRequest(BaseModel):
    pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credential: str = Field(min_length=1, max_length=16384)
    nonce: str = Field(min_length=32, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


# ---------- Address ----------
class Address(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("adr"))
    user_id: str
    label: str
    recipient: str
    phone: str
    street: str
    city: str
    province: str
    postal_code: str
    subdistrict: Optional[str] = None
    district: Optional[str] = None
    everpro_destination_id: Optional[str] = None
    is_default: bool = False
    created_at: str = Field(default_factory=now_iso)


class EverproLocationSelection(BaseModel):
    province_id: str = Field(min_length=1, max_length=128)
    city_id: str = Field(min_length=1, max_length=128)
    district_id: str = Field(min_length=1, max_length=128)
    subdistrict_id: str = Field(min_length=1, max_length=128)


class AddressCreate(BaseModel):
    label: str
    recipient: str
    phone: str
    street: str
    city: str
    province: str
    postal_code: str
    subdistrict: Optional[str] = None
    district: Optional[str] = None
    everpro_destination_id: Optional[str] = None
    everpro_location: Optional[EverproLocationSelection] = None
    is_default: bool = False


# ---------- Category / Brand ----------
class Category(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("cat"))
    name: str
    slug: str
    description: Optional[str] = None
    group_type: GroupType = "product_type"
    code: Optional[str] = None
    icon: Optional[str] = None
    banner_image: Optional[str] = None
    sort_order: int = 0
    is_featured: bool = False
    is_active: bool = True
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)


class ProductBulkAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["delete", "deactivate"]
    product_ids: List[str] = Field(min_length=1, max_length=200)


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    group_type: GroupType
    code: Optional[str] = None
    icon: Optional[str] = None
    banner_image: Optional[str] = None
    sort_order: int = 0
    is_featured: bool = False
    is_active: bool = True


class Brand(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("brd"))
    name: str
    slug: str
    logo: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)


class BrandCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


# ---------- Product ----------
class ProductVariant(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("var"))
    color: Optional[str] = None
    color_hex: Optional[str] = None
    size: Optional[str] = None
    lens_type: Optional[str] = None
    sku: str
    stock: int = 0
    reserved: int = 0
    price_override: Optional[float] = None
    is_active: bool = True


class Product(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("prd"))
    name: str
    slug: str
    sku: str
    description: str
    spec: Dict[str, Any] = Field(default_factory=dict)
    product_type: ProductType = "frame"
    category_ids: List[str] = Field(default_factory=list)
    primary_category_id: Optional[str] = None
    brand_id: Optional[str] = None
    segments: List[str] = Field(default_factory=list)  # pria/wanita/anak-anak/unisex
    price: float
    discount_price: Optional[float] = None
    flash_sale_price: Optional[float] = None
    weight_gram: int = 100
    dimension: Optional[str] = None
    main_image: str
    gallery: List[str] = Field(default_factory=list)
    variants: List[ProductVariant] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)  # new, bestseller, flashsale, limited
    min_stock_alert: int = 5
    rating_avg: float = 0
    rating_count: int = 0
    sold_count: int = 0
    is_new_arrival: bool = False
    new_arrival_until: Optional[str] = None
    is_active: bool = True
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    spec: Optional[Dict[str, Any]] = None
    product_type: Optional[ProductType] = None
    category_ids: Optional[List[str]] = None
    primary_category_id: Optional[str] = None
    brand_id: Optional[str] = None
    segments: Optional[List[str]] = None
    price: Optional[float] = None
    discount_price: Optional[float] = None
    flash_sale_price: Optional[float] = None
    weight_gram: Optional[int] = None
    dimension: Optional[str] = None
    main_image: Optional[str] = None
    gallery: Optional[List[str]] = None
    variants: Optional[List[ProductVariant]] = None
    badges: Optional[List[str]] = None
    min_stock_alert: Optional[int] = None
    is_new_arrival: Optional[bool] = None
    new_arrival_until: Optional[str] = None
    is_active: Optional[bool] = None


class ProductCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    sku: Optional[str] = None
    description: str
    spec: Dict[str, Any] = Field(default_factory=dict)
    product_type: ProductType = "frame"
    category_ids: List[str] = Field(default_factory=list)
    primary_category_id: Optional[str] = None
    brand_id: Optional[str] = None
    segments: List[str] = Field(default_factory=list)
    price: float
    discount_price: Optional[float] = None
    flash_sale_price: Optional[float] = None
    weight_gram: int = 100
    dimension: Optional[str] = None
    main_image: str
    gallery: List[str] = Field(default_factory=list)
    variants: List[ProductVariant] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)
    min_stock_alert: int = 5
    is_new_arrival: bool = False
    new_arrival_until: Optional[str] = None
    is_active: bool = True


# ---------- Cart ----------
class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("cit"))
    user_id: str
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    # Lens bundle (optional, when adding a frame with a lens option)
    lens_product_id: Optional[str] = None
    lens_variant_id: Optional[str] = None
    lens_index_id: Optional[str] = None
    prescription: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=now_iso)


class CartItemCreate(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    lens_product_id: Optional[str] = None
    lens_variant_id: Optional[str] = None
    lens_index_id: Optional[str] = None
    prescription: Optional[Dict[str, Any]] = None


class CartUpdate(BaseModel):
    quantity: int


# ---------- Order ----------
class OrderItem(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    product_name: str
    variant_label: Optional[str] = None
    main_image: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float


class Order(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("ord"))
    order_number: str
    user_id: str
    items: List[OrderItem]
    address: Dict[str, Any]
    subtotal: float
    discount: float = 0
    flash_sale_discount: float = 0
    voucher_code: Optional[str] = None
    voucher_discount: float = 0
    points_used: int = 0
    points_discount: float = 0
    roulette_reward_id: Optional[str] = None
    roulette_discount: float = 0
    shipping_courier: str
    shipping_service: str
    shipping_cost: float
    total: float
    status: Literal[
        "pending_payment", "paid", "processing", "shipped",
        "completed", "cancelled", "expired", "refunded"
    ] = "pending_payment"
    payment_status: Literal["pending", "paid", "failed", "expired", "cancelled", "refunded"] = "pending"
    shipment_status: Literal["pending", "created", "picked_up", "in_transit", "delivered", "failed", "returned", "cancelled"] = "pending"
    payment_method: Optional[str] = None
    payment_url: Optional[str] = None
    tracking_number: Optional[str] = None
    reservation_expires_at: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


# ---------- Stock ----------
class StockReservation(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("res"))
    order_id: str
    product_id: str
    variant_id: Optional[str] = None
    quantity: int
    status: Literal["active", "confirmed", "expired", "cancelled"] = "active"
    expires_at: str
    created_at: str = Field(default_factory=now_iso)


# ---------- Payment / Shipment ----------
class PaymentLog(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("pay"))
    order_id: str
    provider: str = "doku-mock"
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    response: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)


class ShipmentLog(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("shp"))
    order_id: str
    provider: str = "everpro-mock"
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    response: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)


# ---------- Promo / Voucher / Flash Sale ----------
class Voucher(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("vch"))
    code: str
    name: str
    discount_type: Literal["percent", "nominal", "free_shipping"] = "percent"
    discount_value: float = 0
    min_purchase: float = 0
    max_discount: Optional[float] = None
    quota: int = 100
    used_count: int = 0
    quota_per_user: int = 1
    start_at: str
    end_at: str
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)


class FlashSale(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("fls"))
    name: str
    start_at: str
    end_at: str
    is_active: bool = True
    items: List[Dict[str, Any]] = Field(default_factory=list)  # [{product_id, flash_price, quota, sold}]
    created_at: str = Field(default_factory=now_iso)


# ---------- Game / Roulette / Points ----------
class GameScore(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("gms"))
    user_id: str
    game: Literal["puzzle", "tetris", "matching", "memory"]
    score: int
    points_awarded: int = 0
    played_at: str = Field(default_factory=now_iso)


class RouletteReward(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("rwd"))
    label: str
    type: Literal["points", "voucher", "free_shipping", "discount", "nothing"]
    value: float = 0
    color: str = "#FF6B6B"
    probability: float = 0.1  # weight 0..1
    is_active: bool = True


class RouletteSpin(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("spn"))
    user_id: str
    reward_id: str
    reward_label: str
    reward_type: str
    reward_value: float
    used: bool = False
    expires_at: str
    created_at: str = Field(default_factory=now_iso)


class PointLog(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("pts"))
    user_id: str
    delta: int
    balance_after: int
    type: str
    note: str = ""
    created_at: str = Field(default_factory=now_iso)


# ---------- Newsletter / Subscriptions ----------
class NewsletterSubscriber(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("nws"))
    email: EmailStr
    user_id: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)


class ProductSubscription(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("psb"))
    user_id: str
    product_id: str
    notify_stock: bool = True
    notify_price_drop: bool = True
    notify_flash_sale: bool = True
    created_at: str = Field(default_factory=now_iso)


# ---------- Review / Wishlist ----------
class ProductReview(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("rev"))
    product_id: str
    user_id: str
    user_name: str
    rating: int
    title: Optional[str] = None
    body: str
    images: List[str] = Field(default_factory=list)
    is_approved: bool = True
    created_at: str = Field(default_factory=now_iso)


class WishlistEntry(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("wsh"))
    user_id: str
    product_id: str
    created_at: str = Field(default_factory=now_iso)


# ---------- Checkout payload ----------
class CheckoutPreview(BaseModel):
    shipping_quote_id: Optional[str] = None
    address_id: str
    courier_code: str = "jne"  # e.g. jne, jnt, sicepat
    service_code: str = "REG"  # REG, YES, etc
    voucher_code: Optional[str] = None
    use_points: int = 0
    roulette_spin_id: Optional[str] = None
    selected_item_ids: List[str] = Field(default_factory=list)


# ---------- Content: Articles / Knowledge / FAQ / Pages / Contact ----------
class ArticleCategory(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("acat"))
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    created_at: str = Field(default_factory=now_iso)


class Article(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("art"))
    category_id: Optional[str] = None
    author_id: Optional[str] = None
    author_name: str = "Admin Meow"
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    thumbnail: Optional[str] = None
    status: Literal["draft", "published", "unpublished", "archived"] = "published"
    view_count: int = 0
    tags: List[str] = Field(default_factory=list)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    published_at: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class ProductKnowledge(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("pk"))
    knowledge_type: Literal["frame_shape", "material", "lens_type", "lens_index", "buying_guide"] = "frame_shape"
    title: str
    slug: str
    description: Optional[str] = None
    content: str
    image: Optional[str] = None
    icon: Optional[str] = None
    face_shape_recommendation: Optional[str] = None
    style_recommendation: Optional[str] = None
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    related_product_ids: List[str] = Field(default_factory=list)
    filter_param: Optional[Dict[str, Any]] = None  # e.g. {"frame_shape": "round"}
    sort_order: int = 0
    is_published: bool = True
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    published_at: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)


class LensIndex(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("lens"))
    name: str  # "1.56 Standard"
    index_value: str  # "1.56"
    description: Optional[str] = None
    thickness_level: str = "medium"  # thin, medium, thick
    recommended_power_range: str = ""  # e.g. "-2.00 to +2.00"
    additional_price: float = 0
    is_active: bool = True
    sort_order: int = 0


class LensIndexInput(LensIndex):
    # Admin classification is stored in a bridge, outside legacy Lens Index exports.
    lens_type_ids: List[str] = Field(default_factory=list, max_length=100)
    additional_price: float = Field(default=0, ge=0, allow_inf_nan=False)


class FAQCategory(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("fqc"))
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class FAQItem(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("faq"))
    category_id: Optional[str] = None
    question: str
    answer: str
    is_active: bool = True
    sort_order: int = 0
    created_at: str = Field(default_factory=now_iso)


class CMSPage(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("pg"))
    page_type: Literal["about", "privacy_policy", "terms_conditions", "refund_policy", "shipping_policy", "custom"] = "custom"
    title: str
    slug: str
    content: str
    status: Literal["draft", "published", "unpublished", "archived"] = "published"
    version: int = 1
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    published_at: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class ContactSetting(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("cs"))
    store_name: str = "Meow Eyes"
    address: str = ""
    email: str = "hello@meoweyes.id"
    phone: str = ""
    whatsapp: str = ""
    operational_hours: str = "Senin-Sabtu 09:00-18:00"
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    tokopedia: Optional[str] = None
    shopee: Optional[str] = None
    google_maps_embed: Optional[str] = None
    updated_at: str = Field(default_factory=now_iso)


class ContactMessage(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("msg"))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str
    status: Literal["new", "read", "replied"] = "new"
    created_at: str = Field(default_factory=now_iso)


class BannerV2(BaseModel):
    id: str = Field(default_factory=lambda: gen_id("ban"))
    title: str
    image_desktop: str
    image_mobile: Optional[str] = None
    link_type: Literal["internal", "product", "category", "shop_now", "flash_sale", "article", "external", "none"] = "internal"
    link_url: str = "/"
    reference_id: Optional[str] = None
    position: str = "hero"  # hero, promo, shop_now, article, footer
    target_device: Literal["desktop", "mobile", "all"] = "all"
    alt_text: Optional[str] = None
    sort_order: int = 0
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)


# Import staging record
class ProductImportRow(BaseModel):
    row_number: int
    data: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)


class CheckoutConfirm(CheckoutPreview):
    pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
