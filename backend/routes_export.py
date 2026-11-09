"""Admin Excel exports from normalized SQL tables, without document queries."""
from __future__ import annotations
from datetime import datetime, timezone
from io import BytesIO
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from database import read_session
from auth import current_admin
from models import User
from mysql import models as m
from mysql.api import products_dict, row_dict
from services_excel import build_workbook

router = APIRouter(prefix="/admin/export", tags=["admin-export"])


def _rp(value):
    try:
        return f"Rp {int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)


def _date(value, length=10):
    return value.isoformat()[:length] if value else ""


def _stream(data: bytes, name: str) -> StreamingResponse:
    return StreamingResponse(BytesIO(data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={name}"})


def _report(title, headers, rows, prefix, admin):
    # Names/comments are untrusted text, never Excel formulas.
    safe_rows = [["'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value
                  for value in row] for row in rows]
    data = build_workbook(title, headers, safe_rows, meta={"period": "All", "admin": admin.name})
    return _stream(data, f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx")


@router.get("/sales")
async def export_sales(admin: User = Depends(current_admin)):
    async with read_session() as s:
        orders = (await s.scalars(select(m.Order).order_by(m.Order.created_at.desc(), m.Order.id))).all()
        items = {}
        for item in (await s.scalars(select(m.OrderItem).order_by(m.OrderItem.sort_order, m.OrderItem.id))).all():
            items.setdefault(item.order_id, []).append(f"{item.product_name} x{item.quantity}")
        addresses = {a.order_id: a for a in (await s.scalars(select(m.OrderAddress))).all()}
        shipments = {ship.order_id: ship for ship in (await s.scalars(select(m.Shipment)
            .order_by(m.Shipment.created_at, m.Shipment.id))).all()}
        rows = []
        for i, order in enumerate(orders, 1):
            address, shipment = addresses.get(order.id), shipments.get(order.id)
            rows.append([i, order.order_number, _date(order.created_at), address.recipient if address else "-",
                ", ".join(items.get(order.id, [])), _rp(order.subtotal), _rp(order.voucher_discount), order.points_used,
                _rp(order.roulette_discount), _rp(order.shipping_cost), _rp(order.total), order.payment_status,
                order.status, order.shipping_courier, shipment.tracking_number if shipment else "-"])
    return _report("Laporan Penjualan", ["No", "Order Number", "Tanggal", "Customer", "Items", "Subtotal",
        "Diskon Voucher", "Poin Digunakan", "Reward Roulette", "Ongkir", "Total", "Status Bayar", "Status Order", "Kurir", "Resi"], rows, "sales", admin)


@router.get("/inventory")
async def export_inventory(admin: User = Depends(current_admin)):
    async with read_session() as s:
        products = (await s.scalars(select(m.Product).order_by(m.Product.name, m.Product.id))).all()
        brands = {b.id: b.name for b in (await s.scalars(select(m.Brand))).all()}
        rows = []
        for product in await products_dict(s, products, include_inactive_variants=True):
            for variant in product["variants"] or [None]:
                rows.append([len(rows) + 1, variant["sku"] if variant else product["sku"], product["name"],
                    product["product_type"], brands.get(product["brand_id"], ""),
                    " / ".join(x for x in (variant.get("color"), variant.get("size"), variant.get("lens_type")) if x) or "-" if variant else "-",
                    variant["stock"] - variant["reserved"] if variant else 0, variant["reserved"] if variant else 0,
                    product["sold_count"], product["min_stock_alert"],
                    "Aktif" if product["is_active"] and (variant is None or variant["is_active"]) else "Nonaktif"])
    return _report("Laporan Inventory", ["No", "SKU", "Produk", "Tipe", "Brand", "Varian", "Stok Tersedia",
        "Stok Reserved", "Terjual", "Min Alert", "Status"], rows, "inventory", admin)


@router.get("/flash-sales")
async def export_flash_sales(admin: User = Depends(current_admin)):
    async with read_session() as s:
        results = await s.execute(select(m.FlashSale, m.FlashSaleItem, m.Product.name)
            .join(m.FlashSaleItem, m.FlashSaleItem.flash_sale_id == m.FlashSale.id)
            .join(m.Product, m.Product.id == m.FlashSaleItem.product_id)
            .order_by(m.FlashSale.start_at.desc(), m.FlashSale.id, m.FlashSaleItem.id))
        rows = [[i, f.name, name, _rp(item.flash_price), item.quota, item.sold, _date(f.start_at, 16),
                 _date(f.end_at, 16), "Aktif" if f.is_active and item.is_active else "Nonaktif"]
                for i, (f, item, name) in enumerate(results, 1)]
    return _report("Laporan Flash Sale", ["No", "Nama", "Produk", "Harga Flash", "Kuota", "Terjual", "Mulai", "Selesai", "Status"], rows, "flash-sales", admin)


@router.get("/roulette")
async def export_roulette(admin: User = Depends(current_admin)):
    async with read_session() as s:
        results = await s.execute(select(m.RouletteSpin, m.User.name, m.User.email)
            .join(m.User, m.User.user_id == m.RouletteSpin.user_id)
            .order_by(m.RouletteSpin.created_at.desc(), m.RouletteSpin.id))
        live_redemptions = dict((await s.execute(select(m.RouletteRedemption.spin_id, m.RouletteRedemption.order_id)
            .where(m.RouletteRedemption.status.in_(("reserved", "redeemed"))))).all())
        rows = [[i, name, email, _date(spin.created_at, 19), spin.reward_label, spin.reward_type,
                 float(spin.reward_value), "Ya" if spin.used else "-", live_redemptions.get(spin.id, "-"), _date(spin.expires_at)]
                for i, (spin, name, email) in enumerate(results, 1)]
    return _report("Laporan Roulette", ["No", "Nama User", "Email", "Tanggal", "Reward", "Tipe", "Nilai", "Used", "Order", "Expired"], rows, "roulette", admin)


@router.get("/games")
async def export_games(admin: User = Depends(current_admin)):
    async with read_session() as s:
        results = await s.execute(select(m.GameScore, m.User.name).join(m.User, m.User.user_id == m.GameScore.user_id)
            .order_by(m.GameScore.played_at.desc(), m.GameScore.id))
        rows = [[i, name, score.game, score.score, score.points_awarded, _date(score.played_at, 19)]
                for i, (score, name) in enumerate(results, 1)]
    return _report("Laporan Mini Games", ["No", "Nama User", "Game", "Skor", "Poin", "Tanggal"], rows, "games", admin)


@router.get("/newsletter")
async def export_newsletter(admin: User = Depends(current_admin)):
    async with read_session() as s:
        results = (await s.scalars(select(m.NewsletterSubscriber)
            .order_by(m.NewsletterSubscriber.created_at.desc(), m.NewsletterSubscriber.id))).all()
        rows = [[i, row.email, row.user_id or "-", "Ya" if row.is_active else "Tidak", _date(row.created_at)]
                for i, row in enumerate(results, 1)]
    return _report("Newsletter Subscribers", ["No", "Email", "User ID", "Aktif", "Tanggal Subscribe"], rows, "newsletter", admin)


@router.get("/users")
async def export_users(admin: User = Depends(current_admin)):
    async with read_session() as s:
        users = (await s.scalars(select(m.User).order_by(m.User.created_at.desc(), m.User.user_id))).all()
        rows = [[i, u.name, u.email, u.role, u.provider, u.points_balance, "Ya" if u.is_active else "Tidak", _date(u.created_at)]
                for i, u in enumerate(users, 1)]
    return _report("Daftar Pelanggan", ["No", "Nama", "Email", "Role", "Provider", "Poin", "Aktif", "Tanggal Daftar"], rows, "users", admin)


@router.get("/points")
async def export_points(admin: User = Depends(current_admin)):
    async with read_session() as s:
        results = await s.execute(select(m.PointLog, m.User.name).join(m.User, m.User.user_id == m.PointLog.user_id)
            .order_by(m.PointLog.created_at.desc(), m.PointLog.id))
        rows = [[i, name, _date(log.created_at, 19), log.type, log.delta, log.balance_after, log.note]
                for i, (log, name) in enumerate(results, 1)]
    return _report("Laporan Poin", ["No", "User", "Tanggal", "Tipe", "Delta", "Saldo Setelah", "Catatan"], rows, "points", admin)
