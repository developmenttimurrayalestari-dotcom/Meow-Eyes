"""Public color catalogue, permissioned master CRUD and owned cart choices."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from auth import current_user, require_permission
from database import read_session, session_scope
from models import User
from mysql import models as m
from mysql.commerce import lock_user, priced_cart
from mysql.tinting import STORE, TintingInput, TintingSelection, catalog, eligible, snapshot

router = APIRouter(tags=['tinting'])


@router.get('/tinting')
async def public_tinting():
    async with read_session() as s:
        value = await catalog(s)
        return {'items':[snapshot(item) for item in value['items'] if item['is_active'] and not item['requires_sample']]}


@router.get('/admin/tinting')
async def admin_tinting(admin: User = Depends(require_permission('product.view'))):
    async with read_session() as s:
        return await catalog(s)


@router.post('/admin/tinting')
async def create_tinting(body: TintingInput, admin: User = Depends(require_permission('product.create'))):
    return await STORE.mutate(admin.user_id, body.version, body=body)


@router.put('/admin/tinting/{tinting_id}')
async def update_tinting(tinting_id: str, body: TintingInput, admin: User = Depends(require_permission('product.update'))):
    return await STORE.mutate(admin.user_id, body.version, item_id=tinting_id, body=body)


@router.delete('/admin/tinting/{tinting_id}')
async def delete_tinting(tinting_id: str, version: int = Query(ge=0), admin: User = Depends(require_permission('product.delete'))):
    return await STORE.mutate(admin.user_id, version, item_id=tinting_id, remove=True)


@router.patch('/cart/{cart_item_id}/tinting')
async def select_tinting(cart_item_id: str, body: TintingSelection, user: User = Depends(current_user)):
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        cart = await s.scalar(select(m.CartItem).where(m.CartItem.id == cart_item_id,
            m.CartItem.user_id == user.user_id).with_for_update())
        if cart is None: raise HTTPException(404, 'Item keranjang tidak ditemukan')
        selected = await s.get(m.CartTinting, cart.id)
        if body.tinting_id:
            product = await s.get(m.Product, cart.product_id)
            if product is None or not eligible(product):
                raise HTTPException(422, 'Tinting hanya tersedia untuk produk Frame, Lensa, dan Paket')
            value = await catalog(s, lock=True)
            color = next((item for item in value['items'] if item['id'] == body.tinting_id), None)
            if not color or not color['is_active'] or color['requires_sample'] or not color['hex_color']:
                raise HTTPException(409, 'Warna tinting tidak tersedia. Pilih warna lainnya.')
            if selected is None:
                selected = m.CartTinting(cart_item_id=cart.id, tinting_id=body.tinting_id, details=snapshot(color))
                s.add(selected)
            else:
                selected.tinting_id, selected.details = body.tinting_id, snapshot(color)
        elif selected:
            await s.delete(selected)
        await s.flush()
        items, _ = await priced_cart(s, user.user_id, [cart.id], require_stock=False, skip_unavailable=True)
        if not items: raise HTTPException(409, 'Produk tidak tersedia')
        from routes_shopping import _cart_payload
        return {'cart_item':await _cart_payload(s, items[0])}
