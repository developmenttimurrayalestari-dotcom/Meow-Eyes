"""Optical-store features: private prescriptions, ratings, CMS settings and VTO.

This router has no /api prefix; server.py applies the shared API prefix. Private
prescription files are stored outside the public uploads directory and are
served only after an authenticated ownership/fulfilment permission check.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import func, or_, select

from auth import current_admin, current_user, require_permission
from database import read_session, session_scope
from models import FlashSale as FlashSaleDTO, User
from mysql import models as m
from mysql.api import row_dict
from mysql.base import utcnow
from mysql.catalog import apply_fields, flash_dict, get_or_404, safe_values, validate_payload
from mysql.commerce import integer, lock_user, money, prescription_payload, save_prescription
from mysql.features import (normalize_whatsapp_phone, order_can_be_reviewed, published_try_on_conditions,
                            refresh_category_flash_sale, safe_web_url, TRY_ON_PRODUCT_TYPES)

router = APIRouter(tags=["optical-features"])
PRIVATE_UPLOAD_ROOT = Path(os.environ.get("PRIVATE_UPLOAD_ROOT", str(Path(__file__).parent / "private_uploads"))).resolve()
PRESCRIPTION_MAX_BYTES = 8 * 1024 * 1024


class WhatsAppInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    phone_number: str = Field(default="", max_length=40)
    default_text: str = Field(default="", max_length=2000)


def _whatsapp_payload(setting):
    return {"enabled": bool(setting and setting.is_enabled and setting.phone),
            "phone_number": setting.phone if setting else "",
            "default_text": setting.default_text if setting else ""}


@router.get("/settings/whatsapp")
async def whatsapp_public():
    async with read_session() as s:
        return _whatsapp_payload(await s.get(m.WhatsAppSetting, 1))


@router.get("/admin/settings/whatsapp")
async def whatsapp_admin(admin: User = Depends(require_permission("setting.view"))):
    async with read_session() as s:
        return _whatsapp_payload(await s.get(m.WhatsAppSetting, 1))


@router.put("/admin/settings/whatsapp")
async def whatsapp_update(req: WhatsAppInput, admin: User = Depends(require_permission("setting.update"))):
    phone = normalize_whatsapp_phone(req.phone_number, required=req.enabled)
    async with session_scope() as s:
        # The same user lock protects initial singleton creation by one admin;
        # the DB singleton PK also protects concurrent different administrators.
        await lock_user(s, admin.user_id)
        setting = await s.scalar(select(m.WhatsAppSetting).where(m.WhatsAppSetting.id == 1).with_for_update())
        if setting is None:
            setting = m.WhatsAppSetting(id=1, phone=phone, default_text=req.default_text, is_enabled=req.enabled)
            s.add(setting)
        else:
            setting.phone, setting.default_text, setting.is_enabled = phone, req.default_text, req.enabled
        setting.updated_by, setting.updated_at = admin.user_id, utcnow()
        await s.flush()
        return _whatsapp_payload(setting)


def _private_image(raw: bytes) -> bytes:
    try:
        with Image.open(BytesIO(raw)) as source:
            if source.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(415, "Foto resep harus JPEG, PNG, atau WebP")
            if source.width < 1 or source.height < 1 or source.width * source.height > 20_000_000:
                raise HTTPException(413, "Foto resep maksimum 20 megapiksel")
            if getattr(source, "n_frames", 1) != 1:
                raise HTTPException(415, "Foto resep tidak boleh berupa animasi")
            source.verify()
        with Image.open(BytesIO(raw)) as source:
            source.load()
            oriented = ImageOps.exif_transpose(source).convert("RGBA")
            # A new RGB image strips EXIF/GPS and any embedded metadata. White
            # compositing preserves readability of transparent PNG documents.
            clean = Image.new("RGB", oriented.size, "white")
            clean.paste(oriented, mask=oriented.getchannel("A"))
            output = BytesIO()
            clean.save(output, format="JPEG", quality=95, subsampling=0)
            result = output.getvalue()
        if len(result) > PRESCRIPTION_MAX_BYTES:
            raise HTTPException(413, "Foto terlalu besar setelah diproses; gunakan resolusi lebih kecil")
        return result
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(415, "Isi file foto resep tidak valid atau rusak") from None


@router.post("/uploads/prescription")
async def upload_prescription(file: UploadFile = File(...), user: User = Depends(current_user)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Foto resep harus JPEG, PNG, atau WebP")
    raw = await file.read(PRESCRIPTION_MAX_BYTES + 1)
    if not raw or len(raw) > PRESCRIPTION_MAX_BYTES:
        raise HTTPException(413, "Foto resep wajib diisi dan maksimum 8 MB")
    clean = await asyncio.to_thread(_private_image, raw)
    from routes_uploads import UPLOAD_ROOT
    base = PRIVATE_UPLOAD_ROOT.resolve()
    if base.is_relative_to(UPLOAD_ROOT.resolve()):
        raise HTTPException(503, "Penyimpanan resep privat belum dikonfigurasi dengan benar")
    now = utcnow()
    subdir = "prescriptions/" + now.strftime("%Y-%m")
    upload_id = m.new_id()
    disk_name = upload_id + ".jpg"
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = base
    # New private directories/files grant access only to the application user.
    # Refuse symlinks before creating descendants in the configured tree.
    for part in PurePosixPath(subdir).parts:
        parent /= part
        if parent.is_symlink():
            raise HTTPException(503, "Penyimpanan resep privat tidak tersedia")
        parent.mkdir(mode=0o700, exist_ok=True)
    disk_path = parent / disk_name
    created_file = False
    try:
        descriptor = os.open(disk_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created_file = True
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(clean)
        async with session_scope() as s:
            upload = m.Upload(id=upload_id, url=f"/api/prescriptions/uploads/{upload_id}",
                filename=Path(file.filename or "resep.jpg").name[:255] or "resep.jpg", mime="image/jpeg",
                size=len(clean), subdir=subdir, disk_name=disk_name, storage_provider="local",
                storage_key=f"{subdir}/{disk_name}", visibility="private",
                sha256=hashlib.sha256(clean).hexdigest(), uploaded_by=user.user_id, uploaded_by_name=user.name)
            s.add(upload)
            await s.flush()
            return {"id": upload.id, "filename": upload.filename, "mime": upload.mime,
                    "size": upload.size, "url": upload.url, "visibility": "private"}
    except BaseException:
        if created_file:
            disk_path.unlink(missing_ok=True)
        raise


@router.get("/prescriptions/uploads/{upload_id}")
async def prescription_download(upload_id: str, user: User = Depends(current_user)):
    async with read_session() as s:
        upload = await s.scalar(select(m.Upload).where(m.Upload.id == upload_id, m.Upload.visibility == "private"))
        if upload is None:
            raise HTTPException(404, "Lampiran resep tidak ditemukan")
        allowed = upload.uploaded_by == user.user_id or user.role in {"admin", "super_admin"}
        if not allowed and user.role == "staff" and "order.view" in (user.permissions or []):
            allowed = await s.scalar(select(m.OrderItemPrescription.prescription_id).join(m.Prescription,
                m.Prescription.id == m.OrderItemPrescription.prescription_id).where(
                m.Prescription.attachment_upload_id == upload_id, m.Prescription.is_order_snapshot.is_(True)).limit(1)) is not None
        if not allowed or upload.storage_provider != "local" or not upload.storage_key:
            raise HTTPException(404, "Lampiran resep tidak ditemukan")
        key = PurePosixPath(upload.storage_key)
        if key.is_absolute() or key.as_posix() != upload.storage_key or any(p in {".", ".."} for p in key.parts):
            raise HTTPException(404, "Lampiran resep tidak ditemukan")
        base = PRIVATE_UPLOAD_ROOT.resolve()
        path = base
        for part in key.parts:
            path /= part
            if path.is_symlink():
                raise HTTPException(404, "Lampiran resep tidak ditemukan")
        if not path.resolve().is_relative_to(base) or not path.is_file() or upload.mime != "image/jpeg":
            raise HTTPException(404, "Lampiran resep tidak ditemukan")
    return FileResponse(path, media_type="image/jpeg", filename=f"resep-{upload_id}.jpg",
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
                                 "Content-Security-Policy": "default-src 'none'; sandbox"})


@router.get("/cart/{cart_item_id}/lens-options")
async def cart_lens_options(cart_item_id: str, user: User = Depends(current_user)):
    from mysql.lenses import available_indexes, indexes_payload, product_lens_types
    async with read_session() as s:
        item = await s.scalar(select(m.CartItem).where(m.CartItem.id == cart_item_id, m.CartItem.user_id == user.user_id))
        if item is None:
            raise HTTPException(404, "Item keranjang tidak ditemukan")
        product = await s.get(m.Product, item.product_id)
        if product is None or product.deleted_at or not product.is_active:
            raise HTTPException(422, "Produk sudah tidak tersedia")
        types = await product_lens_types(s, product.id)
        return {"items": await indexes_payload(s, await available_indexes(s, product)),
                "included_in_package": product.product_type == 'package',
                "lens_types": [{"id": row.id, "name": row.name} for row in types]}


@router.patch("/cart/{cart_item_id}/prescription")
async def update_cart_prescription(cart_item_id: str, payload: dict[str, Any], user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        item = await s.scalar(select(m.CartItem).where(m.CartItem.id == cart_item_id,
            m.CartItem.user_id == user.user_id).with_for_update())
        if item is None:
            raise HTTPException(404, "Item keranjang tidak ditemukan")
        product = await s.get(m.Product, item.product_id)
        if product is None or product.deleted_at is not None or not product.is_active:
            raise HTTPException(422, "Produk sudah tidak tersedia untuk pengisian resep")
        frame_only = payload.get('frame_only', False)
        if not isinstance(frame_only, bool) or (frame_only and product.product_type != 'frame'):
            raise HTTPException(422, 'Pilihan beli frame saja hanya berlaku untuk produk Frame')
        if frame_only:
            if payload.get('lens_index_id') not in (None, ''):
                raise HTTPException(422, 'Beli frame saja tidak dapat digabung dengan pilihan lensa')
            item.lens_index_id = item.lens_variant_id = item.lens_product_id = None
        elif 'lens_index_id' in payload:
            from mysql.lenses import validate_index
            index = await validate_index(s, product, payload['lens_index_id'], lock=True)
            item.lens_index_id = index.id if index else None
        prescription_fields = {key: value for key, value in payload.items() if key not in {'lens_index_id', 'frame_only'}}
        if prescription_fields or not ({'lens_index_id', 'frame_only'} & payload.keys()):
            prescription = await save_prescription(s, user.user_id, prescription_fields)
            item.prescription_id = prescription.id if prescription else None
        await s.flush()
        from mysql.commerce import priced_cart
        from routes_shopping import _cart_payload
        priced, _ = await priced_cart(s, user.user_id, [item.id], require_stock=False)
        return {"ok": True, "prescription": await prescription_payload(s, item.prescription_id),
                "cart_item": await _cart_payload(s, priced[0])}


@router.get("/orders/{order_id}/review-eligibility")
async def review_eligibility(order_id: str, user: User = Depends(current_user)):
    async with read_session() as s:
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id, m.Order.user_id == user.user_id))
        if order is None:
            raise HTTPException(404, "Pesanan tidak ditemukan")
        allowed = order_can_be_reviewed(order)
        reviews = {r.product_id: row_dict(r) for r in (await s.scalars(select(m.ProductReview).where(
            m.ProductReview.order_id == order_id, m.ProductReview.user_id == user.user_id))).all()}
        order_review = await s.scalar(select(m.OrderReview).where(m.OrderReview.order_id == order_id))
        items = (await s.scalars(select(m.OrderItem).where(m.OrderItem.order_id == order_id)
            .order_by(m.OrderItem.sort_order, m.OrderItem.id))).all()
        products = {}
        for item in items:
            products.setdefault(item.product_id, {"product_id": item.product_id, "name": item.product_name,
                "image": item.main_image, "order_item_id": item.id, "order_component_id": None})
        components = (await s.scalars(select(m.OrderItemComponent).where(m.OrderItemComponent.order_id == order_id)
            .order_by(m.OrderItemComponent.sort_order, m.OrderItemComponent.id))).all()
        for item in components:
            products.setdefault(item.product_id, {"product_id": item.product_id, "name": item.product_name,
                "image": None, "order_item_id": None, "order_component_id": item.id})
        for product in products.values():
            product["review"] = reviews.get(product["product_id"])
            product["eligible"] = allowed and product["review"] is None
        return {"eligible": allowed, "reason": None if allowed else "Ulasan tersedia setelah pembayaran berhasil dikonfirmasi",
                "order_review": row_dict(order_review) if order_review else None,
                "products": list(products.values())}


@router.post("/orders/{order_id}/review")
async def create_order_review(order_id: str, payload: dict[str, Any], user: User = Depends(current_user)):
    rating = integer(payload.get("rating"), "Rating", 1, 5)
    body = payload.get("body") or ""
    if not isinstance(body, str) or len(body) > 10000:
        raise HTTPException(422, "Ulasan maksimum 10000 karakter")
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id,
            m.Order.user_id == user.user_id).with_for_update())
        if order is None:
            raise HTTPException(404, "Pesanan tidak ditemukan")
        if not order_can_be_reviewed(order):
            raise HTTPException(409, "Ulasan tersedia setelah pembayaran berhasil dikonfirmasi")
        if await s.scalar(select(m.OrderReview.id).where(m.OrderReview.order_id == order_id)):
            raise HTTPException(409, "Transaksi ini sudah diberi ulasan")
        review = m.OrderReview(id=m.new_id(), order_id=order.id, user_id=user.user_id,
                              rating=rating, body=body.strip(), status="approved")
        s.add(review)
        await s.flush()
        return {"ok": True, "review": row_dict(review)}


class TryOnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(min_length=1, max_length=64)
    variant_id: str | None = Field(default=None, max_length=64)
    asset_type: str = "image"
    upload_id: str | None = Field(default=None, max_length=64)
    source_url: str | None = Field(default=None, max_length=2048)
    preview_url: str | None = Field(default=None, max_length=2048)
    scale: float = Field(default=1, ge=0.01, le=10, allow_inf_nan=False)
    offset_x: float = Field(default=0, ge=-10, le=10, allow_inf_nan=False)
    offset_y: float = Field(default=0, ge=-10, le=10, allow_inf_nan=False)
    offset_z: float = Field(default=0, ge=-10, le=10, allow_inf_nan=False)
    rotation_x: float = Field(default=0, ge=-360, le=360, allow_inf_nan=False)
    rotation_y: float = Field(default=0, ge=-360, le=360, allow_inf_nan=False)
    rotation_z: float = Field(default=0, ge=-360, le=360, allow_inf_nan=False)
    calibration: dict[str, Any] | None = None
    status: str = "draft"
    sort_order: int = Field(default=0, ge=-100000, le=100000)


async def _validate_try_on(s, payload: dict) -> dict:
    data = validate_payload(TryOnInput, payload)
    if data["asset_type"] not in {"image", "glb", "gltf"} or data["status"] not in {"draft", "published", "archived"}:
        raise HTTPException(422, "Jenis aset atau status Virtual Try-On tidak valid")
    if not await s.scalar(select(m.Product.id).where(m.Product.id == data["product_id"], m.Product.product_type.in_(TRY_ON_PRODUCT_TYPES), m.Product.deleted_at.is_(None))):
        raise HTTPException(422, "Virtual Try-On hanya tersedia untuk produk Frame atau Paket yang belum dihapus")
    if data["variant_id"] and not await s.scalar(select(m.ProductVariant.id).where(
        m.ProductVariant.id == data["variant_id"], m.ProductVariant.product_id == data["product_id"])):
        raise HTTPException(422, "Varian bukan milik produk ini")
    data["upload_id"] = data["upload_id"] or None
    data["source_url"] = data["source_url"] or None
    if bool(data["upload_id"]) == bool(data["source_url"]):
        raise HTTPException(422, "Pilih satu sumber aset: upload_id atau source_url")
    if data["upload_id"]:
        upload = await s.scalar(select(m.Upload).where(m.Upload.id == data["upload_id"], m.Upload.visibility == "public"))
        expected = {"image": {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"},
                    "glb": {"model/gltf-binary"}, "gltf": {"model/gltf+json"}}
        if upload is None or upload.mime not in expected[data["asset_type"]] or not upload.url:
            raise HTTPException(422, "Upload publik tidak sesuai jenis aset Virtual Try-On")
        safe_web_url(upload.url, "URL aset")
    else:
        data["source_url"] = safe_web_url(data["source_url"], "URL aset")
    if data["preview_url"]:
        data["preview_url"] = safe_web_url(data["preview_url"], "URL preview")
    else:
        data["preview_url"] = None
    if data["calibration"] is not None:
        try:
            encoded = json.dumps(data["calibration"], allow_nan=False)
        except (TypeError, ValueError, RecursionError):
            raise HTTPException(422, "Kalibrasi Virtual Try-On harus JSON yang valid") from None
        if len(encoded.encode()) > 8192:
            raise HTTPException(422, "Kalibrasi Virtual Try-On maksimum 8 KB")
    return safe_values(m.VirtualTryOnAsset, data)


async def _try_on_assets(s, assets):
    assets = list(assets)
    upload_ids = [a.upload_id for a in assets if a.upload_id]
    urls = {u.id: u.url for u in (await s.scalars(select(m.Upload).where(
        m.Upload.id.in_(upload_ids), m.Upload.visibility == "public"))).all()} if upload_ids else {}
    data = []
    for asset in assets:
        row = row_dict(asset)
        if asset.upload_id:
            row["source_url"] = urls.get(asset.upload_id)
        if row["source_url"]:
            data.append(row)
    return data


@router.get("/products/{product_id}/try-on")
async def public_try_on(product_id: str, variant_id: str | None = None):
    async with read_session() as s:
        if not await s.scalar(select(m.Product.id).where(m.Product.id == product_id,
            m.Product.is_active.is_(True), m.Product.deleted_at.is_(None), m.Product.product_type.in_(TRY_ON_PRODUCT_TYPES))):
            raise HTTPException(404, "Frame tidak ditemukan")
        stmt = select(m.VirtualTryOnAsset).where(m.VirtualTryOnAsset.product_id == product_id,
                                               *published_try_on_conditions())
        if variant_id:
            if not await s.scalar(select(m.ProductVariant.id).where(m.ProductVariant.id == variant_id,
                m.ProductVariant.product_id == product_id, m.ProductVariant.is_active.is_(True))):
                raise HTTPException(404, "Varian frame tidak tersedia")
            stmt = stmt.where(or_(m.VirtualTryOnAsset.variant_id.is_(None), m.VirtualTryOnAsset.variant_id == variant_id))
        assets = (await s.scalars(stmt.order_by(m.VirtualTryOnAsset.sort_order, m.VirtualTryOnAsset.id).limit(50))).all()
        return {"assets": await _try_on_assets(s, assets)}

@router.get('/try-on/catalog')
async def try_on_catalog(q: str = '', offset: int = Query(0, ge=0)):
    from mysql.features import public_products
    async with read_session() as s:
        supported = select(m.VirtualTryOnAsset.product_id).where(*published_try_on_conditions())
        query = select(m.Product).where(m.Product.product_type.in_(TRY_ON_PRODUCT_TYPES), m.Product.is_active.is_(True), m.Product.deleted_at.is_(None), m.Product.id.in_(supported))
        if q: query = query.where(m.Product.name.contains(q, autoescape=True) | m.Product.sku.contains(q, autoescape=True))
        products = (await s.scalars(query.order_by(m.Product.name, m.Product.id).offset(offset).limit(30))).all()
        data = await public_products(s, products)
        if data:
            rows = (await s.scalars(select(m.VirtualTryOnAsset).where(m.VirtualTryOnAsset.product_id.in_([p.id for p in products]), *published_try_on_conditions()).order_by(m.VirtualTryOnAsset.sort_order, m.VirtualTryOnAsset.id))).all()
            assets = await _try_on_assets(s, rows)
            for product in data: product['try_on_assets'] = [a for a in assets if a['product_id'] == product['id']]
        return {'products': data, 'next_offset': offset + 30 if len(data) == 30 else None}


@router.get("/admin/try-on-assets")
async def admin_try_on_list(product_id: str | None = None, limit: int = Query(200, ge=1, le=500),
                            admin: User = Depends(require_permission("product.view"))):
    async with read_session() as s:
        stmt = select(m.VirtualTryOnAsset)
        if product_id:
            stmt = stmt.where(m.VirtualTryOnAsset.product_id == product_id)
        rows = (await s.scalars(stmt.order_by(m.VirtualTryOnAsset.product_id,
            m.VirtualTryOnAsset.sort_order, m.VirtualTryOnAsset.id).limit(limit))).all()
        return {"assets": await _try_on_assets(s, rows)}


@router.post("/admin/try-on-assets")
async def create_try_on(payload: dict[str, Any], admin: User = Depends(require_permission("product.update"))):
    async with session_scope() as s:
        data = await _validate_try_on(s, payload)
        asset = m.VirtualTryOnAsset(id=m.new_id(), updated_by=admin.user_id, **data)
        s.add(asset)
        await s.flush()
        return {"ok": True, "asset": (await _try_on_assets(s, [asset]))[0]}


@router.patch("/admin/try-on-assets/{asset_id}")
async def update_try_on(asset_id: str, payload: dict[str, Any], admin: User = Depends(require_permission("product.update"))):
    async with session_scope() as s:
        asset = await get_or_404(s, m.VirtualTryOnAsset, asset_id, lock=True)
        fields = set(TryOnInput.model_fields)
        if set(payload) - fields:
            raise HTTPException(422, "Kolom Virtual Try-On tidak dikenal")
        current = {key: value for key, value in row_dict(asset).items() if key in fields}
        # Switching source modes must clear the previous source explicitly.
        if payload.get("upload_id"):
            current["source_url"] = None
        elif payload.get("source_url"):
            current["upload_id"] = None
        data = await _validate_try_on(s, {**current, **payload})
        apply_fields(asset, data, fields)
        asset.updated_by = admin.user_id
        await s.flush()
        return {"ok": True, "asset": (await _try_on_assets(s, [asset]))[0]}


@router.delete("/admin/try-on-assets/{asset_id}")
async def delete_try_on(asset_id: str, admin: User = Depends(require_permission("product.update"))):
    async with session_scope() as s:
        asset = await get_or_404(s, m.VirtualTryOnAsset, asset_id, lock=True)
        await s.delete(asset)
    return {"ok": True}


@router.patch("/admin/flash-sales/{flash_id}")
async def update_flash_sale(flash_id: str, payload: dict[str, Any], admin: User = Depends(current_admin)):
    header_fields = {"name", "start_at", "end_at", "is_active"}
    if set(payload) - (header_fields | {"items"}):
        raise HTTPException(422, "Ubah aturan kategori melalui kampanye baru; refresh menambah produk baru")
    patches = payload.get("items", [])
    if not isinstance(patches, list) or len(patches) > 5000:
        raise HTTPException(422, "Daftar item Flash Sale tidak valid")
    ids = []
    for item in patches:
        if not isinstance(item, dict) or not item.get("id") or set(item) - {"id", "flash_price", "quota", "is_active"}:
            raise HTTPException(422, "Pembaruan item Flash Sale tidak valid")
        if item["id"] in ids:
            raise HTTPException(422, "Item Flash Sale duplikat")
        ids.append(item["id"])
    async with session_scope() as s:
        product_ids = (await s.scalars(select(m.FlashSaleItem.product_id).where(
            m.FlashSaleItem.flash_sale_id == flash_id, m.FlashSaleItem.id.in_(ids)))).all() if ids else []
        if product_ids:
            await s.scalars(select(m.Product).where(m.Product.id.in_(product_ids)).order_by(m.Product.id).with_for_update())
        flash = await get_or_404(s, m.FlashSale, flash_id, lock=True)
        data = validate_payload(FlashSaleDTO, {**row_dict(flash), **{k: v for k, v in payload.items() if k in header_fields}})
        data = safe_values(m.FlashSale, data)
        if not data["name"].strip() or data["end_at"] <= data["start_at"]:
            raise HTTPException(422, "Nama dan rentang waktu Flash Sale tidak valid")
        apply_fields(flash, data, header_fields)
        existing = {item.id: item for item in (await s.scalars(select(m.FlashSaleItem).where(
            m.FlashSaleItem.flash_sale_id == flash_id, m.FlashSaleItem.id.in_(ids))
            .order_by(m.FlashSaleItem.id).with_for_update())).all()} if ids else {}
        if set(existing) != set(ids):
            raise HTTPException(422, "Item bukan milik Flash Sale ini")
        for patch in patches:
            item = existing[patch["id"]]
            if "flash_price" in patch:
                price = money(patch["flash_price"])
                if price < 0:
                    raise HTTPException(422, "Harga Flash Sale tidak boleh negatif")
                if item.flash_price != price:
                    # An explicit admin price becomes a manual product override.
                    item.source_category_id = None
                item.flash_price = price
            if "quota" in patch:
                quota = integer(patch["quota"], "Kuota")
                if quota < item.sold + item.reserved:
                    raise HTTPException(409, "Kuota tidak boleh kurang dari jumlah terjual dan reserved")
                item.quota = quota
            if "is_active" in patch:
                if not isinstance(patch["is_active"], bool):
                    raise HTTPException(422, "is_active harus boolean")
                item.is_active = patch["is_active"]
        await s.flush()
        return {"ok": True, "flash_sale": await flash_dict(s, flash, include_inactive=True)}


@router.post("/admin/flash-sales/{flash_id}/refresh-categories")
async def refresh_flash_sale(flash_id: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        count = await refresh_category_flash_sale(s, flash_id, reprice_existing=True)
        flash = await get_or_404(s, m.FlashSale, flash_id)
        return {"ok": True, "added_products": count,
                "flash_sale": await flash_dict(s, flash, include_inactive=True)}
