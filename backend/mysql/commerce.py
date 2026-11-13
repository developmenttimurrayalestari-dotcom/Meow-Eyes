"""Relational commerce services for the existing API (MySQL 5.7).

Every write owns a single transaction. A user row serializes wallet, cart and
checkout mutations; product/variant locks are taken in stable ID order. Money
stays Decimal until the API boundary. Provider calls run outside stock
transactions. Optional local simulations are unavailable in production.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import os
import secrets
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import read_session, session_scope
from models import gen_id
from mysql import models as m
from mysql.api import order_dict, product_dict, row_dict, values_for
from mysql.base import utcnow


RESERVATION_HOURS = 1
ZERO = Decimal("0.00")
MAX_CART_QUANTITY = 10000


def money(value: Any) -> Decimal:
    """Reject non-finite/out-of-range amounts; round currency once, explicitly."""
    try:
        value = Decimal(str(value))
        if not value.is_finite() or abs(value) >= Decimal("10000000000000000"):
            raise ValueError
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (ValueError, InvalidOperation, TypeError):
        raise HTTPException(400, "Nilai uang tidak valid") from None


def integer(value: Any, name: str, minimum: int = 0, maximum: int = 2147483647) -> int:
    try:
        if isinstance(value, bool) or Decimal(str(value)) != int(value):
            raise ValueError
        result = int(value)
        if not minimum <= result <= maximum:
            raise ValueError
        return result
    except (TypeError, ValueError, InvalidOperation, OverflowError):
        raise HTTPException(400, f"{name} tidak valid") from None


def mock_payments_enabled() -> bool:
    return (
        os.environ.get("APP_ENV", "development") in {"development", "test"}
        and os.environ.get("ENABLE_MOCK_PAYMENTS", "0") == "1"
    )


def require_mock_payments() -> None:
    if not mock_payments_enabled():
        raise HTTPException(503, "Pembayaran belum diaktifkan; integrasi DOKU diperlukan")


async def lock_user(s: AsyncSession, user_id: str, *, active: bool = True) -> m.User:
    user = await s.scalar(select(m.User).where(m.User.user_id == user_id).with_for_update())
    if user is None or (active and not user.is_active):
        raise HTTPException(403, "Akun tidak tersedia")
    return user


def _measurement(value: Any, name: str, *, positive: bool = False) -> Decimal | None:
    if value is None or value == "":
        return None
    result = money(value)
    if abs(result) > Decimal("999.99") or (positive and result <= 0):
        raise HTTPException(400, f"{name} tidak valid")
    return result


async def save_prescription(
    s: AsyncSession, user_id: str, payload: dict[str, Any] | None,
    *, is_snapshot: bool = False,
) -> m.Prescription | None:
    """Persist the current storefront's flat measurements in relational rows.

    This is a data adapter for the existing form, not the later private-upload
    UI. Existing private upload IDs are accepted only for their owner.
    """
    if not payload:
        return None
    allowed = {
        "od_sph", "os_sph", "od_cyl", "os_cyl", "od_axis", "os_axis",
        "od_add", "os_add", "pd", "pd_total", "pd_right", "pd_left",
        "notes", "attachment_upload_id",
    }
    if set(payload) - allowed:
        raise HTTPException(400, "Kolom resep tidak dikenal")
    pd = payload.get("pd_total", payload.get("pd"))
    if payload.get("pd") not in (None, "") and payload.get("pd_total") not in (None, ""):
        if money(payload["pd"]) != money(payload["pd_total"]):
            raise HTTPException(400, "PD ganda tidak konsisten")
    pd_total = _measurement(pd, "PD", positive=True)
    pd_right = _measurement(payload.get("pd_right"), "PD kanan", positive=True)
    pd_left = _measurement(payload.get("pd_left"), "PD kiri", positive=True)
    if (pd_right is None) != (pd_left is None) or (pd_total is not None and pd_right is not None):
        raise HTTPException(400, "Isi PD total atau pasangan PD kanan dan kiri")
    attachment = payload.get("attachment_upload_id") or None
    if attachment:
        upload = await s.scalar(select(m.Upload).where(
            m.Upload.id == attachment, m.Upload.uploaded_by == user_id,
            m.Upload.visibility == "private",
        ))
        if upload is None:
            raise HTTPException(400, "Lampiran resep tidak tersedia untuk akun ini")
    notes = payload.get("notes") or None
    if notes is not None and (not isinstance(notes, str) or len(notes) > 10000):
        raise HTTPException(400, "Catatan resep tidak valid")
    prescription = m.Prescription(
        id=gen_id("rx"), user_id=user_id, pd_total=pd_total, pd_right=pd_right,
        pd_left=pd_left, notes=notes, attachment_upload_id=attachment,
        is_order_snapshot=is_snapshot,
    )
    eyes = []
    for prefix, eye in (("od", "right"), ("os", "left")):
        measurements = {
            key: _measurement(payload.get(f"{prefix}_{key}"), f"{eye} {key}")
            for key in ("sph", "cyl", "add")
        }
        axis = payload.get(f"{prefix}_axis")
        measurements["axis"] = None if axis in (None, "") else integer(axis, "AXIS", 0, 180)
        if any(v is not None for v in measurements.values()):
            eyes.append(m.PrescriptionEye(prescription_id=prescription.id, eye=eye, **measurements))
    if not eyes and pd_total is None and pd_right is None and notes is None and attachment is None:
        return None
    s.add(prescription)
    await s.flush()
    s.add_all(eyes)
    await s.flush()
    return prescription


async def prescription_payload(s: AsyncSession, prescription_id: str | None) -> dict[str, Any] | None:
    if not prescription_id:
        return None
    p = await s.get(m.Prescription, prescription_id)
    if p is None:
        return None
    result: dict[str, Any] = {
        "od_sph": "", "os_sph": "", "od_cyl": "", "os_cyl": "",
        "pd": float(p.pd_total) if p.pd_total is not None else "",
        "notes": p.notes or "",
    }
    for eye in (await s.scalars(select(m.PrescriptionEye).where(
        m.PrescriptionEye.prescription_id == p.id
    ))).all():
        prefix = "od" if eye.eye == "right" else "os"
        for key in ("sph", "cyl", "axis", "add"):
            value = getattr(eye, key)
            if value is not None:
                result[f"{prefix}_{key}"] = int(value) if key == "axis" else float(value)
    if p.pd_right is not None:
        result.update(pd_right=float(p.pd_right), pd_left=float(p.pd_left))
    if p.attachment_upload_id:
        result["attachment_upload_id"] = p.attachment_upload_id
    return result


async def copy_prescription(s: AsyncSession, source_id: str, user_id: str) -> m.Prescription:
    source = await s.scalar(select(m.Prescription).where(
        m.Prescription.id == source_id, m.Prescription.user_id == user_id
    ).with_for_update())
    if source is None:
        raise HTTPException(409, "Resep keranjang tidak tersedia")
    snapshot = m.Prescription(
        id=gen_id("rx"), user_id=user_id, pd_total=source.pd_total,
        pd_right=source.pd_right, pd_left=source.pd_left,
        attachment_upload_id=source.attachment_upload_id, notes=source.notes,
        is_order_snapshot=True,
    )
    s.add(snapshot)
    await s.flush()
    for eye in (await s.scalars(select(m.PrescriptionEye).where(
        m.PrescriptionEye.prescription_id == source_id
    ))).all():
        s.add(m.PrescriptionEye(
            prescription_id=snapshot.id, eye=eye.eye, sph=eye.sph,
            cyl=eye.cyl, axis=eye.axis, add=eye.add,
        ))
    await s.flush()
    return snapshot


def variant_label(variant: m.ProductVariant) -> str | None:
    return " · ".join(x for x in (variant.color, variant.size, variant.lens_type) if x) or None


def base_price(product: m.Product, variant: m.ProductVariant) -> Decimal:
    if variant.price_override is not None:
        return money(variant.price_override)
    if product.discount_price is not None:
        return money(product.discount_price)
    return money(product.price)


async def resolve_variant(
    s: AsyncSession, product: m.Product, variant_id: str | None, *, lens: bool = False,
) -> m.ProductVariant:
    rows = (await s.scalars(select(m.ProductVariant).where(
        m.ProductVariant.product_id == product.id,
        m.ProductVariant.is_active.is_(True),
    ).order_by(m.ProductVariant.sort_order, m.ProductVariant.id))).all()
    if variant_id:
        chosen = next((v for v in rows if v.id == variant_id), None)
        if chosen is None:
            raise HTTPException(400, "Varian tidak cocok dengan produk atau sudah nonaktif")
        return chosen
    if len(rows) == 1 or (lens and rows):
        return rows[0]
    if not rows:
        raise HTTPException(400, "Stok varian produk belum dikonfigurasi")
    raise HTTPException(400, "Pilih varian produk")


@dataclass
class PricedItem:
    cart: m.CartItem
    product: m.Product
    variant: m.ProductVariant
    frame_price: Decimal
    lens_product: m.Product | None = None
    lens_variant: m.ProductVariant | None = None
    lens_index: m.LensIndex | None = None
    lens_price: Decimal = ZERO
    index_surcharge: Decimal = ZERO
    flash_item: m.FlashSaleItem | None = None

    @property
    def unit_price(self) -> Decimal:
        return self.frame_price + self.lens_price

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.cart.quantity


@dataclass
class CheckoutQuote:
    address: m.Address
    user: m.User
    items: list[PricedItem]
    subtotal: Decimal
    weight: int
    shipping: dict[str, Any]
    shipping_cost: Decimal
    voucher: m.Voucher | None
    voucher_discount: Decimal
    points_used: int
    points_discount: Decimal
    roulette: m.RouletteSpin | None
    roulette_discount: Decimal
    free_shipping: bool
    total: Decimal
    point_plan: list | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "subtotal": float(self.subtotal),
            "product_subtotal": float(sum((item.frame_price * item.cart.quantity for item in self.items), ZERO)),
            "lens_subtotal": float(sum((item.lens_price * item.cart.quantity for item in self.items), ZERO)),
            "voucher": row_dict(self.voucher) if self.voucher else None,
            "voucher_discount": float(self.voucher_discount),
            "points_used": self.points_used, "points_discount": float(self.points_discount),
            "roulette_spin": row_dict(self.roulette) if self.roulette else None,
            "roulette_discount": float(self.roulette_discount),
            "shipping": {
                "courier_code": self.shipping["courier_code"],
                "service_code": self.shipping["service_code"],
                "cost": float(self.shipping_cost), "label": self.shipping["service_label"],
                "courier_name": self.shipping["courier_name"],
            },
            "free_shipping": self.free_shipping, "total": float(self.total),
            "items_count": len(self.items), "weight_gram": self.weight,
            "flash_sale_exclusive": any(item.flash_item is not None for item in self.items),
        }


async def priced_cart(
    s: AsyncSession, user_id: str, selected_ids: list[str] | None = None,
    *, lock: bool = False, require_stock: bool = True, skip_unavailable: bool = False,
) -> tuple[list[PricedItem], int]:
    query = select(m.CartItem).where(m.CartItem.user_id == user_id)
    if selected_ids:
        query = query.where(m.CartItem.id.in_(set(selected_ids)))
    query = query.order_by(m.CartItem.id)
    if lock:
        query = query.with_for_update()
    carts = list((await s.scalars(query)).all())
    if selected_ids and {c.id for c in carts} != set(selected_ids):
        raise HTTPException(400, "Item pilihan tidak tersedia di keranjang Anda")
    if not carts:
        return [], 0
    product_ids = sorted({pid for c in carts for pid in (c.product_id, c.lens_product_id) if pid})
    product_query = select(m.Product).where(m.Product.id.in_(product_ids)).order_by(m.Product.id)
    variant_query = select(m.ProductVariant).where(
        m.ProductVariant.product_id.in_(product_ids)
    ).order_by(m.ProductVariant.id)
    if lock:
        product_query = product_query.with_for_update()
        variant_query = variant_query.with_for_update()
    products = {p.id: p for p in (await s.scalars(product_query)).all()}
    variants = {v.id: v for v in (await s.scalars(variant_query)).all()}
    # The cart already stores a resolved variant. This also checks legacy
    # imported carts; choosing a different SKU silently at checkout is unsafe.
    demands: dict[str, int] = defaultdict(int)
    now = utcnow()
    flash_query = select(m.FlashSaleItem).join(m.FlashSale).where(
        m.FlashSaleItem.product_id.in_(product_ids),
        m.FlashSaleItem.is_active.is_(True), m.FlashSale.is_active.is_(True),
        m.FlashSale.start_at <= now, m.FlashSale.end_at > now,
    ).order_by(m.FlashSaleItem.flash_price, m.FlashSaleItem.id)
    if lock:
        flash_query = flash_query.with_for_update()
    flash_items = list((await s.scalars(flash_query)).all())
    flash_taken: dict[str, int] = defaultdict(int)
    items: list[PricedItem] = []
    weight = 0
    for cart in carts:
        integer(cart.quantity, "Jumlah", 1, MAX_CART_QUANTITY)
        product = products.get(cart.product_id)
        if product is None or not product.is_active:
            if skip_unavailable:
                continue
            raise HTTPException(400, "Produk keranjang tidak tersedia")
        variant = variants.get(cart.variant_id)
        if cart.variant_id is None:
            candidates = [v for v in variants.values() if v.product_id == product.id and v.is_active]
            if len(candidates) == 1:
                variant = candidates[0]
        if variant is None or not variant.is_active or variant.product_id != product.id:
            if skip_unavailable:
                continue
            raise HTTPException(400, "Varian keranjang tidak tersedia; tambahkan ulang produk")
        frame_price = base_price(product, variant)
        flash_item = next((f for f in flash_items if f.product_id == product.id and
            f.quota - f.sold - f.reserved - flash_taken[f.id] >= cart.quantity), None)
        if flash_item:
            frame_price = money(flash_item.flash_price)
        item = PricedItem(cart=cart, product=product, variant=variant,
                          frame_price=frame_price, flash_item=flash_item)
        if cart.lens_product_id:
            lens = products.get(cart.lens_product_id)
            lv = variants.get(cart.lens_variant_id)
            if product.product_type != "frame" or lens is None or not lens.is_active or lens.product_type != "lens":
                if skip_unavailable:
                    continue
                raise HTTPException(400, "Pasangan frame dan lensa tidak tersedia")
            if cart.lens_variant_id is None:
                candidates = sorted((v for v in variants.values() if v.product_id == lens.id and v.is_active),
                                    key=lambda v: (v.sort_order, v.id))
                lv = candidates[0] if candidates else None
            if lv is None or not lv.is_active or lv.product_id != lens.id:
                if skip_unavailable:
                    continue
                raise HTTPException(400, "Varian lensa tidak tersedia; tambahkan ulang paket")
            item.lens_product, item.lens_variant = lens, lv
            item.lens_price = base_price(lens, lv)
        if cart.lens_index_id:
            from .lenses import validate_index
            try:
                lens_index = await validate_index(s, product, cart.lens_index_id, lock=lock)
            except HTTPException:
                if skip_unavailable:
                    continue
                raise
            item.lens_index = lens_index
            item.index_surcharge = ZERO if product.product_type == 'package' else money(lens_index.additional_price)
            item.lens_price += item.index_surcharge
        demands[variant.id] += cart.quantity
        weight += product.weight_gram * cart.quantity
        if item.lens_product and item.lens_variant:
            demands[item.lens_variant.id] += cart.quantity
            weight += item.lens_product.weight_gram * cart.quantity
        if flash_item:
            flash_taken[flash_item.id] += cart.quantity
        items.append(item)
    if require_stock:
        for variant_id, quantity in demands.items():
            v = variants[variant_id]
            if v.stock - v.reserved < quantity:
                raise HTTPException(409, "Stok produk tidak mencukupi")
    return items, weight


def voucher_amount(voucher: m.Voucher, subtotal: Decimal) -> tuple[Decimal, bool]:
    now = utcnow()
    if not voucher.is_active or not voucher.start_at <= now < voucher.end_at:
        raise HTTPException(400, "Voucher tidak berlaku")
    if subtotal < voucher.min_purchase:
        raise HTTPException(400, f"Minimal pembelian Rp {int(voucher.min_purchase):,}")
    if voucher.used_count >= voucher.quota:
        raise HTTPException(400, "Voucher sudah habis")
    discount = ZERO
    if voucher.discount_type == "percent":
        discount = money(subtotal * voucher.discount_value / 100)
        if voucher.max_discount is not None:
            discount = min(discount, voucher.max_discount)
    elif voucher.discount_type == "nominal":
        discount = voucher.discount_value
    return min(subtotal, money(discount)), voucher.discount_type == "free_shipping"


async def checkout_quote(s: AsyncSession, user: m.User, req: Any, *, lock: bool = False) -> CheckoutQuote:
    from integrations.config import shipping_provider, payment_provider
    address_query = select(m.Address).where(m.Address.id == req.address_id, m.Address.user_id == user.user_id)
    address = await s.scalar(address_query.with_for_update() if lock else address_query)
    if address is None:
        raise HTTPException(404, "Alamat tidak ditemukan")
    items, weight = await priced_cart(s, user.user_id, req.selected_item_ids, lock=lock)
    if not items:
        raise HTTPException(400, "Tidak ada item yang dipilih")
    subtotal = sum((i.subtotal for i in items), ZERO)
    flash_sale_exclusive = any(item.flash_item is not None for item in items)
    if shipping_provider() == "mock":
        from services_mock import everpro_cost
        options = everpro_cost(address.province, max(weight, 100))
        shipping = next((o for o in options if o["courier_code"] == req.courier_code
                         and o["service_code"] == req.service_code), None)
    elif shipping_provider() == "everpro":
        from mysql.integration_services import validated_shipping_quote
        shipping = await validated_shipping_quote(s, user, req, address, items, lock=lock)
    else:
        raise HTTPException(503, "Pengiriman belum diaktifkan")
    if shipping is None:
        raise HTTPException(400, "Layanan pengiriman tidak tersedia")
    shipping_cost = money(shipping["cost"])
    voucher = None
    voucher_discount = ZERO
    free_shipping = False
    if req.voucher_code and not flash_sale_exclusive:
        q = select(m.Voucher).where(m.Voucher.code == req.voucher_code.upper())
        voucher = await s.scalar(q.with_for_update() if lock else q)
        if voucher is None:
            raise HTTPException(404, "Voucher tidak ditemukan")
        voucher_discount, free_shipping = voucher_amount(voucher, subtotal)
        used = await s.scalar(select(func.count()).select_from(m.VoucherRedemption).where(
            m.VoucherRedemption.voucher_id == voucher.id, m.VoucherRedemption.user_id == user.user_id,
            m.VoucherRedemption.status.in_(("reserved", "redeemed")),
        ))
        if int(used or 0) >= voucher.quota_per_user:
            raise HTTPException(400, "Batas penggunaan voucher untuk akun ini tercapai")
    roulette = None
    roulette_discount = ZERO
    if req.roulette_spin_id and not flash_sale_exclusive:
        q = select(m.RouletteSpin).where(m.RouletteSpin.id == req.roulette_spin_id,
                                        m.RouletteSpin.user_id == user.user_id)
        roulette = await s.scalar(q.with_for_update() if lock else q)
        if roulette is None or roulette.used or roulette.expires_at <= utcnow():
            raise HTTPException(400, "Hadiah roulette tidak berlaku")
        if roulette.reward_type == "discount":
            roulette_discount = min(roulette.reward_value, subtotal - voucher_discount)
        elif roulette.reward_type == "free_shipping":
            free_shipping = True
        else:
            raise HTTPException(400, "Hadiah ini tidak dapat digunakan pada checkout")
    from mysql.points import quote as point_quote
    requested_points = integer(req.use_points or 0, "Poin", 0, 9223372036854775807)
    points_used, points_discount, point_plan = await point_quote(s, user, 0 if flash_sale_exclusive else requested_points,
        max(ZERO, subtotal - voucher_discount - roulette_discount))
    if free_shipping:
        shipping_cost = ZERO
    total = money(subtotal - voucher_discount - roulette_discount - points_discount + shipping_cost)
    if payment_provider() == "doku":
        # Hosted Checkout accepts IDR without decimal places. Round the final
        # payable amount once; the preview and persisted invoice agree.
        total = total.quantize(Decimal("1"), rounding=ROUND_HALF_UP).quantize(Decimal("0.01"))
        if total <= 0 or total >= Decimal("1000000000000"):
            raise HTTPException(422, "Total pembayaran DOKU harus Rp1 sampai Rp999.999.999.999")
    return CheckoutQuote(address, user, items, subtotal, weight, shipping, shipping_cost,
                         voucher, voucher_discount, points_used, points_discount,
                         roulette, money(roulette_discount), free_shipping, total, point_plan)


def checkout_identity(user_id: str, req: Any, key: str | None) -> tuple[str | None, str]:
    payload = req.model_dump(exclude={"pin"})
    payload["selected_item_ids"] = sorted(set(req.selected_item_ids))
    if payload.get("voucher_code"):
        payload["voucher_code"] = payload["voucher_code"].upper()
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if key is not None:
        if not 1 <= len(key) <= 128 or any(not 33 <= ord(c) <= 126 for c in key):
            raise HTTPException(400, "Idempotency-Key tidak valid")
        key = "explicit:" + key
    elif req.selected_item_ids:
        # Existing React clients already send the selected cart row IDs. A
        # retried request for those consumed rows returns the original order.
        key = "cart:" + fingerprint
    else:
        return None, fingerprint
    return hashlib.sha256((user_id + "\0" + key).encode()).hexdigest(), fingerprint


async def _save_order(s: AsyncSession, quote: CheckoutQuote, key: str | None, fingerprint: str) -> m.Order:
    from integrations.config import payment_provider, DokuSettings
    now = utcnow()
    provider = "doku-mock" if payment_provider() == "mock" else "doku"
    expires = now + (timedelta(minutes=DokuSettings.from_env().due_minutes) if provider == "doku" else timedelta(hours=RESERVATION_HOURS))
    order = m.Order(
        id=gen_id("ord"), order_number="MEOW-" + now.strftime("%y%m%d") + "-" + secrets.token_hex(6).upper(),
        user_id=quote.user.user_id, subtotal=quote.subtotal,
        voucher_code=quote.voucher.code if quote.voucher else None,
        voucher_discount=quote.voucher_discount, points_used=quote.points_used,
        points_discount=quote.points_discount, roulette_discount=quote.roulette_discount,
        shipping_courier=quote.shipping["courier_code"], shipping_service=quote.shipping["service_code"],
        shipping_cost=quote.shipping_cost, total=quote.total,
        shipping_quote_id=quote.shipping.get("quote_id"),
        reservation_expires_at=expires, checkout_idempotency_key=key,
        status="pending_payment", payment_status="pending", shipment_status="pending",
    )
    s.add(order)
    await s.flush()
    address = quote.address
    snapshot_values = {name: getattr(address, name) for name in (
        "label", "recipient", "phone", "street", "subdistrict", "district", "city",
        "province", "postal_code", "country_code", "everpro_destination_id",
    )}
    s.add(m.OrderAddress(order_id=order.id, source_address_id=address.id,
                         source_created_at=address.created_at, source_is_default=address.is_default,
                         **snapshot_values))
    for position, item in enumerate(quote.items):
        row = m.OrderItem(
            id=gen_id("ori"), order_id=order.id, product_id=item.product.id,
            variant_id=item.variant.id, product_name=item.product.name, sku=item.variant.sku,
            variant_label=variant_label(item.variant), main_image=item.product.main_image,
            quantity=item.cart.quantity, unit_price=item.unit_price,
            subtotal=item.subtotal, sort_order=position,
        )
        s.add(row)
        await s.flush()
        standalone_index = item.lens_index is not None and item.lens_product is None
        primary_surcharge = item.index_surcharge if standalone_index else ZERO
        components = [("primary", item.product, item.variant, item.frame_price + primary_surcharge, primary_surcharge)]
        if item.lens_product and item.lens_variant:
            components.append(("lens", item.lens_product, item.lens_variant,
                               item.lens_price, item.index_surcharge))
        for component_position, (kind, product, variant, price, surcharge) in enumerate(components):
            s.add(m.OrderItemComponent(
                id=gen_id("ocp"), order_item_id=row.id, order_id=order.id,
                component_type=kind, product_id=product.id, variant_id=variant.id,
                lens_index_id=item.lens_index.id if item.lens_index and (kind == "lens" or standalone_index) else None,
                lens_index_name=item.lens_index.name if item.lens_index and (kind == "lens" or standalone_index) else None,
                product_name=product.name, sku=variant.sku, variant_label=variant_label(variant),
                quantity=item.cart.quantity, unit_price=price, index_surcharge=surcharge,
                subtotal=price * item.cart.quantity, sort_order=component_position,
            ))
            reservation = m.StockReservation(
                id=gen_id("res"), order_id=order.id, order_item_id=row.id,
                product_id=product.id, variant_id=variant.id, quantity=item.cart.quantity,
                status="active", expires_at=expires,
            )
            s.add(reservation)
            variant.reserved += item.cart.quantity
            await s.flush()
            s.add(m.StockMovement(
                id=gen_id("mov"), product_id=product.id, variant_id=variant.id,
                order_id=order.id, reservation_id=reservation.id, type="reserved",
                quantity=item.cart.quantity, delta=0, reserved_delta=item.cart.quantity,
                stock_after=variant.stock, reserved_after=variant.reserved,
            ))
        if item.flash_item:
            item.flash_item.reserved += item.cart.quantity
            s.add(m.FlashSaleReservation(
                id=gen_id("fsr"), order_item_id=row.id, flash_sale_item_id=item.flash_item.id,
                product_id=item.product.id, quantity=item.cart.quantity, status="active", expires_at=expires,
            ))
        if item.cart.prescription_id:
            prescription = await copy_prescription(s, item.cart.prescription_id, order.user_id)
            s.add(m.OrderItemPrescription(order_item_id=row.id, order_id=order.id,
                                          user_id=order.user_id, prescription_id=prescription.id))
    if quote.voucher:
        quote.voucher.used_count += 1
        s.add(m.VoucherRedemption(
            id=gen_id("vcr"), voucher_id=quote.voucher.id, order_id=order.id, user_id=order.user_id,
            discount_amount=quote.voucher_discount, status="reserved",
        ))
    if quote.roulette:
        quote.roulette.used = True
        s.add(m.RouletteRedemption(
            id=gen_id("rrd"), spin_id=quote.roulette.id, order_id=order.id, user_id=order.user_id,
            discount_amount=quote.roulette_discount, status="reserved",
        ))
    from mysql.points import reserve as reserve_points, snapshot_cashback
    await reserve_points(s, quote.user, order, quote.point_plan or [])
    await snapshot_cashback(s, order)
    s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order.id,
                          status="pending_payment", note="Order dibuat"))
    await s.execute(delete(m.CartItem).where(
        m.CartItem.user_id == order.user_id, m.CartItem.id.in_([x.cart.id for x in quote.items])
    ))
    payment = m.Payment(
        id=gen_id("pay"), order_id=order.id, provider=provider,
        request_id="checkout:" + order.id, merchant_reference=order.order_number,
        amount=order.total, method="VA" if provider == "doku-mock" else "CHECKOUT", status="pending", expires_at=expires,
    )
    s.add(payment)
    await s.flush()
    s.add(m.PaymentLog(
        id=gen_id("plg"), order_id=order.id, payment_id=payment.id,
        provider=provider, action="checkout_request",
        payload={"fingerprint": fingerprint, "amount": float(order.total)},
    ))
    await s.flush()
    return order


def payment_payload(order: m.Order, payment: m.Payment) -> dict[str, Any]:
    return {
        "invoice_id": payment.external_id, "order_number": order.order_number,
        "amount": float(payment.amount), "method": payment.method,
        "va_number": payment.virtual_account_number, "payment_url": payment.payment_url,
        "expires_at": payment.expires_at.isoformat() if payment.expires_at else None,
        "status": payment.status,
        "provider": payment.provider, "mock": payment.provider == "doku-mock",
    }


async def ensure_mock_payment(order_id: str) -> dict[str, Any]:
    """Complete/retry the locally simulated payment intent after stock commit.

    The future real DOKU adapter must use Payment.request_id as its provider
    idempotency key. This simulator has no network or monetary side effects.
    """
    from services_mock import doku_create_payment
    require_mock_payments()
    async with read_session() as s:
        order = await s.get(m.Order, order_id)
        payment = await s.scalar(select(m.Payment).where(
            m.Payment.order_id == order_id, m.Payment.provider == "doku-mock"
        ).order_by(m.Payment.created_at, m.Payment.id))
        if order is None or payment is None:
            raise HTTPException(409, "Pembayaran order tidak tersedia")
        if payment.external_id:
            return payment_payload(order, payment)
        user_id, number, total = order.user_id, order.order_number, order.total
    # No stock/transaction lock is held while invoking the adapter.
    prepared = doku_create_payment(number, float(total), method="VA")
    async with session_scope() as s:
        await lock_user(s, user_id)
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
        payment = await s.scalar(select(m.Payment).where(
            m.Payment.order_id == order_id, m.Payment.provider == "doku-mock"
        ).with_for_update())
        if payment.external_id is None and order.status == "pending_payment" and payment.status == "pending":
            payment.external_id = prepared["invoice_id"]
            payment.virtual_account_number = prepared["va_number"]
            payment.payment_url = prepared["payment_url"]
            s.add(m.PaymentLog(
                id=gen_id("plg"), order_id=order.id, payment_id=payment.id,
                provider="doku-mock", action="create_payment", payload={"amount": float(order.total)},
                response={**prepared, "expires_at": order.reservation_expires_at.isoformat()},
            ))
            await s.flush()
        return payment_payload(order, payment)


async def create_checkout(user_id: str, req: Any, idempotency_key: str | None = None) -> dict[str, Any]:
    from integrations.config import require_payment_provider
    from mysql.integration_services import ensure_payment
    require_payment_provider()
    if len(req.selected_item_ids) > 200:
        raise HTTPException(400, "Terlalu banyak item checkout")
    key, fingerprint = checkout_identity(user_id, req, idempotency_key)
    async with session_scope() as s:
        user = await lock_user(s, user_id)
        order = None
        if key:
            # The owner row already serializes this customer's retry keys.
            # Locking a *missing* unique key here would take an InnoDB gap
            # lock under REPEATABLE READ and can deadlock unrelated customers
            # who subsequently compete for the same last inventory unit.
            order = await s.scalar(select(m.Order).where(m.Order.checkout_idempotency_key == key))
        if order:
            log = await s.scalar(select(m.PaymentLog).where(
                m.PaymentLog.order_id == order.id, m.PaymentLog.action == "checkout_request"
            ).order_by(m.PaymentLog.created_at, m.PaymentLog.id))
            if order.user_id != user_id or log is None or (log.payload or {}).get("fingerprint") != fingerprint:
                raise HTTPException(409, "Idempotency-Key sudah digunakan untuk permintaan berbeda")
            order_id = order.id
        else:
            quote = await checkout_quote(s, user, req, lock=True)
            order_id = (await _save_order(s, quote, key, fingerprint)).id
    payment_error = None
    try:
        payment = await ensure_payment(order_id)
    except HTTPException as exc:
        # The order already owns stock and promotion reservations. Return its
        # durable identity even when the provider is temporarily unavailable;
        # the customer retries the same payment intent instead of a new order.
        if exc.status_code not in {409, 429, 502, 503, 504}:
            raise
        payment_error = str(exc.detail)
        async with read_session() as s:
            current = await s.get(m.Order, order_id)
            intent = await s.scalar(select(m.Payment).where(m.Payment.order_id == order_id))
            payment = payment_payload(current, intent)
    async with read_session() as s:
        order = await s.get(m.Order, order_id)
        result = {"order": await order_dict(s, order), "payment": payment}
        if payment_error:
            result.update(payment_error=payment_error, requires_retry=True)
        return result


async def _resolve_stock(s: AsyncSession, order: m.Order, *, sold: bool, status: str) -> None:
    # The locked parent order serializes its child rows. Do not take range
    # locks on empty child indexes: under MySQL 5.7 REPEATABLE READ those can
    # block another customer's INSERT before we acquire shared product locks.
    reservations = list((await s.scalars(select(m.StockReservation).where(
        m.StockReservation.order_id == order.id, m.StockReservation.status == "active"
    ).order_by(m.StockReservation.id))).all())
    if sold:
        if any(reservation.variant_id is None for reservation in reservations):
            raise HTTPException(409, "Reservasi lama tanpa varian stok memerlukan rekonsiliasi")
        # A migrated/incomplete order may not carry all reservations. Never
        # silently mark it paid without the stock ledger matching its lines.
        items = list((await s.scalars(select(m.OrderItem).where(m.OrderItem.order_id == order.id))).all())
        components = list((await s.scalars(select(m.OrderItemComponent).where(
            m.OrderItemComponent.order_id == order.id
        ))).all())
        with_components = {component.order_item_id for component in components}
        expected: dict[tuple[str, str | None], int] = defaultdict(int)
        actual: dict[tuple[str, str | None], int] = defaultdict(int)
        for component in components:
            expected[(component.product_id, component.variant_id)] += component.quantity
        for item in items:
            if item.id not in with_components:
                expected[(item.product_id, item.variant_id)] += item.quantity
        for reservation in reservations:
            actual[(reservation.product_id, reservation.variant_id)] += reservation.quantity
        if not items or dict(actual) != dict(expected):
            raise HTTPException(409, "Reservasi stok tidak cocok dengan item order; perlu rekonsiliasi")
    product_ids = sorted({r.product_id for r in reservations})
    variant_ids = sorted({r.variant_id for r in reservations if r.variant_id})
    products = {p.id: p for p in (await s.scalars(select(m.Product).where(
        m.Product.id.in_(product_ids)
    ).order_by(m.Product.id).with_for_update())).all()}
    variants = {v.id: v for v in (await s.scalars(select(m.ProductVariant).where(
        m.ProductVariant.id.in_(variant_ids)
    ).order_by(m.ProductVariant.id).with_for_update())).all()}
    for reservation in reservations:
        variant = variants.get(reservation.variant_id)
        if reservation.variant_id and (variant is None or variant.reserved < reservation.quantity):
            raise HTTPException(409, "Saldo reservasi stok tidak konsisten; perlu rekonsiliasi")
        if variant:
            if sold and variant.stock < reservation.quantity:
                raise HTTPException(409, "Saldo stok tidak konsisten; perlu rekonsiliasi")
            variant.reserved -= reservation.quantity
            if sold:
                variant.stock -= reservation.quantity
        if sold:
            products[reservation.product_id].sold_count += reservation.quantity
        reservation.status, reservation.resolved_at = status, utcnow()
        s.add(m.StockMovement(
            id=gen_id("mov"), product_id=reservation.product_id, variant_id=reservation.variant_id,
            order_id=order.id, reservation_id=reservation.id,
            type="sold" if sold else ("reservation_cancelled" if status == "cancelled" else "reservation_expired"),
            quantity=reservation.quantity, delta=-reservation.quantity if sold else 0,
            reserved_delta=-reservation.quantity if variant else 0,
            stock_after=variant.stock if variant else None,
            reserved_after=variant.reserved if variant else None,
        ))
    # MySQL emits both stock and reserved changes in one UPDATE, so the row's
    # reserved <= stock guard remains true throughout a successful resolution.
    await s.flush()


async def _resolve_promotions(s: AsyncSession, order: m.Order, *, sold: bool, status: str) -> None:
    flash_rows = list((await s.scalars(select(m.FlashSaleReservation).join(
        m.OrderItem, m.FlashSaleReservation.order_item_id == m.OrderItem.id
    ).where(m.OrderItem.order_id == order.id, m.FlashSaleReservation.status == "active")
        .order_by(m.FlashSaleReservation.flash_sale_item_id, m.FlashSaleReservation.id))).all())
    flash_ids = sorted({r.flash_sale_item_id for r in flash_rows})
    flashes = {f.id: f for f in (await s.scalars(select(m.FlashSaleItem).where(
        m.FlashSaleItem.id.in_(flash_ids)
    ).order_by(m.FlashSaleItem.id).with_for_update())).all()}
    for reservation in flash_rows:
        item = flashes[reservation.flash_sale_item_id]
        if item.reserved < reservation.quantity:
            raise HTTPException(409, "Saldo kuota Flash Sale tidak konsisten")
        item.reserved -= reservation.quantity
        if sold:
            item.sold += reservation.quantity
        reservation.status, reservation.resolved_at = status, utcnow()
    voucher_redemption = await s.scalar(select(m.VoucherRedemption).where(
        m.VoucherRedemption.order_id == order.id, m.VoucherRedemption.status == "reserved"
    ))
    if voucher_redemption:
        voucher = await s.scalar(select(m.Voucher).where(
            m.Voucher.id == voucher_redemption.voucher_id
        ).with_for_update())
        if not sold:
            if voucher.used_count < 1:
                raise HTTPException(409, "Saldo penggunaan voucher tidak konsisten")
            voucher.used_count -= 1
        voucher_redemption.status = "redeemed" if sold else "released"
        voucher_redemption.resolved_at = utcnow()
    roulette_redemption = await s.scalar(select(m.RouletteRedemption).where(
        m.RouletteRedemption.order_id == order.id, m.RouletteRedemption.status == "reserved"
    ))
    if roulette_redemption:
        spin = await s.scalar(select(m.RouletteSpin).where(
            m.RouletteSpin.id == roulette_redemption.spin_id
        ).with_for_update())
        if not sold:
            spin.used = False
        roulette_redemption.status = "redeemed" if sold else "released"
        roulette_redemption.resolved_at = utcnow()
    await s.flush()


async def _release_locked(
    s: AsyncSession, order: m.Order, user: m.User, status: str,
    *, note: str | None = None, admin_id: str | None = None, provider_confirmed: bool = False,
) -> bool:
    if order.status != "pending_payment":
        return False
    if order.payment_status == "paid":
        raise HTTPException(409, "Pembayaran sudah diterima; gunakan proses pengembalian dana")
    if not provider_confirmed:
        doku_attempt = await s.scalar(select(m.PaymentLog.id).join(m.Payment, m.PaymentLog.payment_id == m.Payment.id).where(
            m.Payment.order_id == order.id, m.Payment.provider == "doku", m.PaymentLog.action == "doku_attempt"
        ).limit(1))
        if doku_attempt:
            raise HTTPException(409, "Pembayaran DOKU harus dikonfirmasi kedaluwarsa oleh penyedia sebelum reservasi dilepas")
    confirmed = await s.scalar(select(m.StockReservation.id).where(
        m.StockReservation.order_id == order.id, m.StockReservation.status == "confirmed"
    ).limit(1))
    if confirmed:
        raise HTTPException(409, "Order sudah memiliki penjualan stok; perlu rekonsiliasi")
    await _resolve_stock(s, order, sold=False, status=status)
    await _resolve_promotions(s, order, sold=False, status=status)
    from mysql.points import release as release_points
    await release_points(s, user, order, status)
    pending = (await s.scalars(select(m.Payment).where(
        m.Payment.order_id == order.id, m.Payment.status == "pending"
    ))).all()
    for payment in pending:
        payment.status = status
    order.status, order.payment_status, order.updated_at = status, status, utcnow()
    s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order.id, status=status,
                          note=note or "Order " + status, admin_id=admin_id))
    await s.flush()
    return True


async def expire_order(
    order_id: str, status: str = "expired", *, owner_id: str | None = None,
    due_only: bool = False,
) -> bool:
    if status not in {"expired", "cancelled"}:
        raise ValueError("Unsupported reservation release status")
    async with read_session() as s:
        owner = await s.scalar(select(m.Order.user_id).where(m.Order.id == order_id))
    if owner is None or (owner_id is not None and owner_id != owner):
        if owner_id is not None:
            raise HTTPException(404, "Order tidak ditemukan")
        return False
    async with read_session() as s:
        provider = await s.scalar(select(m.Payment.provider).where(m.Payment.order_id == order_id)
                                  .order_by(m.Payment.created_at, m.Payment.id).limit(1))
    if provider == "doku":
        from mysql.integration_services import expire_doku_order
        return await expire_doku_order(order_id, status, owner_id=owner_id, due_only=due_only)
    async with session_scope() as s:
        user = await lock_user(s, owner, active=False)
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
        if order is None:
            return False
        if owner_id is not None and order.status not in {"pending_payment", "cancelled"}:
            raise HTTPException(400, "Order tidak bisa dibatalkan pada status ini")
        if due_only and (order.reservation_expires_at is None or order.reservation_expires_at > utcnow()):
            return False
        return await _release_locked(s, order, user, status)


async def ensure_mock_shipment(order_id: str) -> str | None:
    from services_mock import everpro_create_shipment
    require_mock_payments()
    async with read_session() as s:
        order = await s.get(m.Order, order_id)
        shipment = await s.scalar(select(m.Shipment).where(
            m.Shipment.order_id == order_id, m.Shipment.provider == "everpro-mock"
        ).order_by(m.Shipment.created_at, m.Shipment.id))
        if order is None or shipment is None:
            return None
        if shipment.tracking_number or order.payment_status != "paid" or order.status not in {"paid", "processing"}:
            return shipment.tracking_number
        address = await s.get(m.OrderAddress, order_id)
        owner, number, courier, service = order.user_id, order.order_number, order.shipping_courier, order.shipping_service
        address_payload = row_dict(address)
    prepared = everpro_create_shipment(number, courier, service, address_payload)
    async with session_scope() as s:
        await lock_user(s, owner, active=False)
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
        shipment = await s.scalar(select(m.Shipment).where(
            m.Shipment.order_id == order_id, m.Shipment.provider == "everpro-mock"
        ).with_for_update())
        if not shipment.tracking_number and order.payment_status == "paid" and order.status in {"paid", "processing"}:
            shipment.tracking_number = prepared["awb"]
            shipment.external_id = prepared["awb"]
            shipment.status = "created"
            order.status, order.shipment_status = "processing", "created"
            s.add(m.ShipmentLog(
                id=gen_id("slg"), order_id=order.id, shipment_id=shipment.id, provider="everpro-mock",
                action="create_shipment", payload={"order_number": order.order_number}, response=prepared,
            ))
            s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order.id, status="processing",
                                  note="Pengiriman simulasi dibuat"))
            await s.flush()
        return shipment.tracking_number


async def confirm_mock_payment(order_number: str, actor_id: str, *, admin: bool = False) -> dict[str, Any]:
    require_mock_payments()
    async with read_session() as s:
        order = await s.scalar(select(m.Order).where(m.Order.order_number == order_number))
        if order is None or (not admin and order.user_id != actor_id):
            raise HTTPException(404, "Order tidak ditemukan")
        owner, order_id = order.user_id, order.id
    expired = False
    async with session_scope() as s:
        user = await lock_user(s, owner, active=False)
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
        if order.status in {"cancelled", "expired", "refunded"}:
            raise HTTPException(409, "Order tidak dapat dibayar pada status ini")
        if order.status == "pending_payment":
            if order.reservation_expires_at is None or order.reservation_expires_at <= utcnow():
                await _release_locked(s, order, user, "expired")
                expired = True
            else:
                payment = await s.scalar(select(m.Payment).where(
                    m.Payment.order_id == order.id, m.Payment.provider == "doku-mock"
                ).with_for_update())
                if payment is None or payment.status != "pending" or payment.amount != order.total or payment.currency != order.currency:
                    raise HTTPException(409, "Pembayaran simulasi tidak cocok dengan order")
                await _resolve_stock(s, order, sold=True, status="confirmed")
                await _resolve_promotions(s, order, sold=True, status="confirmed")
                payment.status, payment.paid_at = "paid", utcnow()
                order.status, order.payment_status = "paid", "paid"
                s.add(m.PaymentLog(
                    id=gen_id("plg"), order_id=order.id, payment_id=payment.id,
                    provider="doku-mock", action="webhook_paid",
                    payload={"order_number": order_number}, response={"status": "paid", "mock": True},
                ))
                s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order.id, status="paid",
                                      note="Pembayaran simulasi berhasil"))
                s.add(m.Shipment(
                    id=gen_id("shp"), order_id=order.id, provider="everpro-mock",
                    request_id="shipment:" + order.id, courier_code=order.shipping_courier,
                    service_code=order.shipping_service, cost=order.shipping_cost, status="pending",
                ))
                await s.flush()
        elif order.payment_status != "paid":
            raise HTTPException(409, "Status pembayaran tidak konsisten")
    if expired:
        # Raise after committing the expiry and refunds, not inside the
        # transaction, where an HTTPException would roll them back.
        raise HTTPException(409, "Waktu pembayaran sudah berakhir; reservasi dilepas")
    tracking = await ensure_mock_shipment(order_id)
    async with read_session() as s:
        order = await s.get(m.Order, order_id)
        return {"ok": True, "status": order.status, "tracking_number": tracking}


async def admin_transition_order(
    order_id: str, new_status: str, note: str | None, admin_id: str | None,
) -> dict[str, Any]:
    """Shared admin state machine; manual status changes cannot mark money paid."""
    async with read_session() as s:
        owner = await s.scalar(select(m.Order.user_id).where(m.Order.id == order_id))
    if owner is None:
        raise HTTPException(404, "Order tidak ditemukan")
    if note is not None and (not isinstance(note, str) or len(note) > 5000):
        raise HTTPException(400, "Catatan tidak valid")
    async with session_scope() as s:
        user = await lock_user(s, owner, active=False)
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
        if order.status == new_status:
            return {"ok": True, "status": order.status}
        if new_status in {"cancelled", "expired"}:
            if order.status != "pending_payment":
                raise HTTPException(409, "Pembatalan ini memerlukan proses pengembalian dana")
            await _release_locked(s, order, user, new_status, note=note, admin_id=admin_id)
        else:
            allowed = {
                "paid": {"processing", "shipped", "completed"},
                "processing": {"shipped", "completed"},
                "shipped": {"completed"},
            }
            if order.payment_status != "paid" or new_status not in allowed.get(order.status, set()):
                raise HTTPException(409, "Perubahan status tidak diperbolehkan; gunakan alur pembayaran atau refund")
            order.status, order.updated_at = new_status, utcnow()
            if new_status == "completed":
                order.completed_at = utcnow()
                from mysql.points import complete_order as complete_point_order
                await complete_point_order(s, user, order)
            if new_status == "shipped":
                order.shipment_status = "in_transit"
                shipments = (await s.scalars(select(m.Shipment).where(
                    m.Shipment.order_id == order.id
                ).order_by(m.Shipment.id).with_for_update())).all()
                for shipment in shipments:
                    if shipment.shipped_at is None:
                        shipment.shipped_at = utcnow()
                    if shipment.status in {"pending", "created", "picked_up"}:
                        shipment.status = "in_transit"
            s.add(m.OrderStatusLog(id=gen_id("ols"), order_id=order.id, status=new_status,
                                  note=note or "Status diperbarui admin", admin_id=admin_id))
            await s.flush()
        return {"ok": True, "status": order.status}
