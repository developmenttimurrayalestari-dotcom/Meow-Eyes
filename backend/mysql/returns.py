"""Replacement-only RMA with quantity and stock accounting."""
from datetime import timedelta
from collections import defaultdict
import uuid
from fastapi import HTTPException
from sqlalchemy import select, func
from . import models as m
from .base import utcnow
from .api import row_dict

DEFAULT_POLICY = {'window_days': 7, 'return_days': 7, 'recipient': '', 'phone': '', 'address': '', 'notes': 'Cantumkan kode klaim pada paket. Simpan bukti pengiriman.'}

async def policy(s):
    row = await s.get(m.Setting, 'rma_policy')
    return {**DEFAULT_POLICY, **(row.value if row else {})}

async def eligibility(s, order):
    config = await policy(s)
    shipment = await s.scalar(select(m.Shipment).where(m.Shipment.order_id == order.id).order_by(m.Shipment.created_at.desc()).limit(1))
    delivered = shipment.delivered_at if shipment else None
    start = delivered or order.completed_at
    deadline = start + timedelta(days=config['window_days']) if start else None
    allowed = order.payment_status == 'paid' and bool(start) and (order.status == 'completed' or bool(delivered)) and deadline >= utcnow()
    return {'eligible': allowed, 'deadline': deadline.isoformat() if deadline else None, 'window_days': config['window_days'], 'resolution': 'replacement'}

async def payload(s, case):
    data = row_dict(case)
    order, customer = await s.get(m.Order, case.order_id), await s.get(m.User, case.user_id)
    data['order_number'] = order.order_number
    data['customer'] = {'name': customer.name, 'email': customer.email}
    rows = (await s.execute(select(m.ReturnCaseItem, m.OrderItem).join(m.OrderItem, m.OrderItem.id == m.ReturnCaseItem.order_item_id).where(m.ReturnCaseItem.case_id == case.id).order_by(m.OrderItem.sort_order))).all()
    data['items'] = [{**row_dict(row), 'product_name': item.product_name, 'variant_label': item.variant_label, 'sku': item.sku} for row, item in rows]
    evidence = (await s.scalars(select(m.ReturnEvidence).where(m.ReturnEvidence.case_id == case.id).order_by(m.ReturnEvidence.created_at))).all()
    data['evidence'] = [{'id': row.id, 'mime_type': row.mime_type, 'byte_size': row.byte_size, 'url': '/returns/evidence/' + row.id} for row in evidence]
    data['timeline'] = [row_dict(row) for row in (await s.scalars(select(m.ReturnTimeline).where(m.ReturnTimeline.case_id == case.id).order_by(m.ReturnTimeline.created_at, m.ReturnTimeline.id))).all()]
    return data

async def timeline(s, case, actor, status, note=''):
    case.status, case.updated_at = status, utcnow()
    s.add(m.ReturnTimeline(case_id=case.id, actor_id=actor.user_id, status=status, note=note))
    await s.flush()

async def create(s, user, order_id, items, reason):
    order = await s.scalar(select(m.Order).where(m.Order.id == order_id, m.Order.user_id == user.user_id).with_for_update())
    if not order: raise HTTPException(404, 'Pesanan tidak ditemukan')
    if not (await eligibility(s, order))['eligible']: raise HTTPException(409, 'Pesanan belum memenuhi syarat atau periode pengajuan sudah berakhir')
    if not items or len({item['order_item_id'] for item in items}) != len(items): raise HTTPException(422, 'Pilih barang yang akan dikembalikan')
    for item in items:
        purchased = await s.get(m.OrderItem, item['order_item_id'])
        if not purchased or purchased.order_id != order.id: raise HTTPException(422, 'Barang tidak ada pada pesanan')
        claimed = await s.scalar(select(func.coalesce(func.sum(m.ReturnCaseItem.quantity), 0)).join(m.ReturnCase, m.ReturnCase.id == m.ReturnCaseItem.case_id).where(m.ReturnCaseItem.order_item_id == purchased.id, m.ReturnCase.status.notin_(['rejected', 'cancelled'])))
        if claimed + item['quantity'] > purchased.quantity: raise HTTPException(409, 'Jumlah klaim melebihi barang yang dibeli')
    case = m.ReturnCase(reference='RMA-' + utcnow().strftime('%Y%m%d') + '-' + uuid.uuid4().hex[:10].upper(), order_id=order.id, user_id=user.user_id, reason=reason)
    s.add(case); await s.flush()
    for item in items: s.add(m.ReturnCaseItem(case_id=case.id, order_id=order.id, **item))
    await timeline(s, case, user, 'draft', 'Klaim penggantian dibuat; menunggu video unboxing')
    return await payload(s, case)

async def replacement_stock(s, case, admin):
    items = (await s.scalars(select(m.ReturnCaseItem).where(m.ReturnCaseItem.case_id == case.id))).all()
    quantities = defaultdict(int)
    products = {}
    for item in items:
        original = await s.get(m.OrderItem, item.order_item_id)
        components = (await s.scalars(select(m.OrderItemComponent).where(m.OrderItemComponent.order_item_id == item.order_item_id))).all()
        if not components: raise HTTPException(409, 'Komponen stok pesanan lama perlu diperiksa admin sebelum penggantian')
        for component in components:
            if not component.variant_id: raise HTTPException(409, 'Varian penggantian tidak tersedia pada pesanan')
            total = component.quantity * item.quantity
            if total % original.quantity: raise HTTPException(409, 'Jumlah komponen penggantian tidak utuh')
            quantities[component.variant_id] += total // original.quantity
            products[component.variant_id] = component.product_id
    for variant_id in sorted(quantities):
        variant = await s.get(m.ProductVariant, variant_id, with_for_update=True)
        quantity = quantities[variant_id]
        if not variant or variant.stock - variant.reserved < quantity: raise HTTPException(409, 'Stok tersedia belum cukup untuk mengirim produk pengganti')
        variant.stock -= quantity
        s.add(m.StockMovement(product_id=products[variant_id], variant_id=variant_id, order_id=case.order_id, type='rma_replacement',
            quantity=quantity, delta=-quantity, reserved_delta=0, stock_after=variant.stock, reserved_after=variant.reserved, admin_id=admin.user_id, note=case.reference))

async def transition(s, case, actor, target, *, admin=False, note='', courier='', tracking=''):
    if case.status == target: return await payload(s, case)
    customer_edges = {'draft': {'submitted', 'cancelled'}, 'approved': {'return_sent'}}
    admin_edges = {'submitted': {'approved', 'rejected'}, 'return_sent': {'received'}, 'received': {'replacement_shipped'}, 'replacement_shipped': {'completed'}}
    if target not in (admin_edges if admin else customer_edges).get(case.status, set()): raise HTTPException(409, 'Perubahan status klaim tidak sesuai alur')
    if target == 'submitted':
        order = await s.get(m.Order, case.order_id)
        if not (await eligibility(s, order))['eligible']: raise HTTPException(409, 'Periode pengajuan sudah berakhir')
        if not await s.scalar(select(m.ReturnEvidence.id).where(m.ReturnEvidence.case_id == case.id).limit(1)): raise HTTPException(422, 'Video unboxing wajib diunggah sebelum mengajukan klaim')
    if target == 'approved':
        config = await policy(s)
        if not all(config.get(key, '').strip() for key in ('recipient', 'phone', 'address')): raise HTTPException(422, 'Lengkapi alamat retur toko di pengaturan RMA terlebih dahulu')
        case.instructions = {**config, 'reference': case.reference, 'ship_before': (utcnow() + timedelta(days=config['return_days'])).isoformat(), 'resolution': 'replacement'}
    if target == 'rejected' and not note.strip(): raise HTTPException(422, 'Alasan penolakan wajib diisi')
    if target in ('return_sent', 'replacement_shipped'):
        if not courier.strip() or not tracking.strip(): raise HTTPException(422, 'Kurir dan resi pengiriman wajib diisi')
        if target == 'return_sent': case.return_courier, case.return_tracking = courier, tracking
        else:
            await replacement_stock(s, case, actor)
            case.replacement_courier, case.replacement_tracking = courier, tracking
    await timeline(s, case, actor, target, note)
    return await payload(s, case)
