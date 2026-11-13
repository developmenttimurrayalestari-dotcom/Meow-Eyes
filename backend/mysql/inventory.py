"""Locked stock adjustments with receipt references and zero-stock initialization."""
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException
from sqlalchemy import select
from . import models as m

def integer(value):
    try:
        result=int(value)
        if isinstance(value,bool) or Decimal(str(value))!=result or not 0 < abs(result) <= 2147483647: raise ValueError
        return result
    except (TypeError,ValueError,InvalidOperation,OverflowError):
        raise HTTPException(422,'Jumlah stok harus bilangan bulat positif') from None

async def adjust_inventory(s, product, payload, admin_id):
    structured = 'adjustment_type' in payload or 'quantity' in payload or 'ttb_number' in payload
    if structured:
        kind=payload.get('adjustment_type')
        if kind not in ('receipt_stock','issue_stock'): raise HTTPException(422,'Pilih Receipt Stock atau Issue Stock')
        quantity=integer(payload.get('quantity'))
        if quantity < 1: raise HTTPException(422,'Jumlah stok harus lebih dari nol')
        ttb=payload.get('ttb_number')
        if not isinstance(ttb,str) or not ttb.strip() or len(ttb.strip())>128: raise HTTPException(422,'Nomor TTB wajib diisi, maksimal 128 karakter')
        ttb=ttb.strip(); delta=quantity if kind=='receipt_stock' else -quantity
        if 'delta' in payload and payload['delta']!=delta: raise HTTPException(422,'Delta tidak sesuai jenis dan jumlah stok')
    else:
        # Existing integrations sending signed deltas remain compatible.
        delta=integer(payload.get('delta')); kind='stock_in' if delta>0 else 'stock_out';ttb=None
    variant_id=payload.get('variant_id')
    if variant_id is not None and (not isinstance(variant_id,str) or not variant_id.strip() or len(variant_id)>64):
        raise HTTPException(422,'ID varian tidak valid')
    if variant_id:
        variant=await s.scalar(select(m.ProductVariant).where(m.ProductVariant.product_id==product.id,m.ProductVariant.id==variant_id).with_for_update())
        if variant is None: raise HTTPException(404,'Varian produk tidak ditemukan')
    else:
        variants=(await s.scalars(select(m.ProductVariant).where(m.ProductVariant.product_id==product.id).order_by(m.ProductVariant.id).with_for_update())).all()
        if len(variants)>1: raise HTTPException(422,'Pilih varian produk yang akan disesuaikan')
        if variants: variant=variants[0]
        else:
            if delta<0: raise HTTPException(409,'Belum ada stok. Gunakan Receipt Stock untuk inisialisasi.')
            sku=product.sku
            if await s.scalar(select(m.ProductVariant.id).where(m.ProductVariant.sku==sku)):
                sku=sku[:80]+'-STK-'+m.new_id()[:16]
            variant=m.ProductVariant(id=m.new_id(),product_id=product.id,sku=sku,stock=0,reserved=0,is_active=True,sort_order=0)
            s.add(variant);await s.flush()
    if not variant.is_active: raise HTTPException(409,'Varian sudah nonaktif dan tidak dapat disesuaikan')
    if variant.stock+delta < variant.reserved: raise HTTPException(409,'Issue Stock melebihi stok tersedia; stok reserved tidak dapat dikeluarkan')
    if variant.stock+delta>2147483647: raise HTTPException(422,'Jumlah stok melebihi batas penyimpanan')
    variant.stock+=delta
    s.add(m.StockMovement(id=m.new_id(),product_id=product.id,variant_id=variant.id,type=kind,ttb_number=ttb,
        quantity=abs(delta),delta=delta,reserved_delta=0,stock_after=variant.stock,reserved_after=variant.reserved,
        note=str(payload.get('note') or ''),admin_id=admin_id))
    await s.flush()
    return {'ok':True,'variant_id':variant.id,'stock':variant.stock,'reserved':variant.reserved,'ttb_number':ttb,'adjustment_type':kind}
