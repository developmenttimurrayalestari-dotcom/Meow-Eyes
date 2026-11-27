"""Public color catalogue, permissioned master CRUD and owned cart choices."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from auth import current_user, require_permission
from database import read_session, session_scope
from models import User
from mysql import models as m
from mysql.commerce import lock_user, priced_cart, MAX_CART_QUANTITY
from mysql.tinting import STORE, TintingInput, TintingSelection, catalog, eligible, snapshot
from pydantic import BaseModel, ConfigDict, Field


class OpticalConfiguration(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lens_index_id: str | None = Field(default=None,max_length=64)
    tinting_id: str | None = Field(default=None,max_length=64)
    prescription: dict | None = None
    replace_lens_product: bool = False
    quantity: int = Field(ge=1,le=MAX_CART_QUANTITY)
    variant_id: str | None = None

router = APIRouter(tags=['tinting'])


@router.patch('/cart/{cart_item_id}/configuration')
async def configure_item(cart_item_id: str,body: OpticalConfiguration,user: User=Depends(current_user)):
    from mysql.lenses import validate_index
    from mysql.commerce import save_prescription, resolve_variant
    from routes_shopping import _cart_payload
    async with session_scope() as s:
        await lock_user(s,user.user_id)
        cart=await s.scalar(select(m.CartItem).where(m.CartItem.id==cart_item_id,m.CartItem.user_id==user.user_id).with_for_update())
        if cart is None: raise HTTPException(404,'Item keranjang tidak ditemukan')
        product=await s.get(m.Product,cart.product_id)
        if not product or not product.is_active or product.deleted_at: raise HTTPException(409,'Produk tidak tersedia')
        await validate_index(s,product,body.lens_index_id,lock=True)
        cart.variant_id=(await resolve_variant(s,product,body.variant_id or cart.variant_id)).id
        cart.quantity,cart.lens_index_id=body.quantity,body.lens_index_id
        if body.replace_lens_product: cart.lens_product_id=cart.lens_variant_id=None
        prescription=await save_prescription(s,user.user_id,body.prescription)
        cart.prescription_id=prescription.id if prescription else None
        selection=await s.get(m.CartTinting,cart.id)
        if body.tinting_id:
            color=next((color for color in (await catalog(s,lock=True))['items'] if color['id']==body.tinting_id),None)
            if not eligible(product) or not color or not color['is_active'] or color['requires_sample']:
                raise HTTPException(409,'Warna tinting tidak tersedia')
            if selection is None:
                s.add(m.CartTinting(cart_item_id=cart.id,tinting_id=color['id'],details=snapshot(color)))
            else: selection.tinting_id,selection.details=color['id'],snapshot(color)
        elif selection: await s.delete(selection)
        await s.flush()
        items,_=await priced_cart(s,user.user_id,[cart.id])
        return {'cart_item':await _cart_payload(s,items[0])}


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
