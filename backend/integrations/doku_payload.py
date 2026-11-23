"""Hosted Checkout fields from DOKU's backend-integration contract.

Snapshot prices are allocated in whole rupiah. No card details or dates of
birth are collected. Stored requests already submitted to DOKU stay immutable.
"""
from decimal import Decimal, ROUND_FLOOR
import os
import re
import unicodedata
from urllib.parse import urljoin, urlsplit, quote
from sqlalchemy import select
from fastapi import HTTPException
from mysql import models as m
from phone_identity import normalize_phone

BASIC_METHODS = ['CREDIT_CARD', 'VIRTUAL_ACCOUNT_BCA', 'VIRTUAL_ACCOUNT_BANK_MANDIRI',
    'VIRTUAL_ACCOUNT_BRI', 'VIRTUAL_ACCOUNT_BNI', 'QRIS', 'ONLINE_TO_OFFLINE_ALFA']


def kki_text(value):
    ascii_text = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9 ]', '', ascii_text).strip()[:255] or 'Produk'


def absolute_image(value, settings):
    if not value: return None
    if str(value).startswith('/'):
        value = urljoin(settings.public_api_url or settings.frontend_url, value)
    p = urlsplit(str(value))
    return value if p.scheme in ('http', 'https') and p.hostname and not p.username and not p.password else None


async def enrich_request(s, request, order, user, address, settings):
    try: phone = normalize_phone(address.phone).lstrip('+')
    except ValueError: raise HTTPException(422, 'Nomor telepon alamat belum valid untuk pembayaran DOKU') from None
    customer = request['customer']
    customer.update(phone=phone, state=address.province, city=address.city, postcode=address.postal_code,
        country=address.country_code, address=address.street)
    if len(user.user_id) > 50:
        # Stable hash for imported IDs longer than DOKU's customer.id limit.
        import hashlib
        customer['id'] = hashlib.sha256(user.user_id.encode()).hexdigest()[:50]
    names = user.name.strip().split()
    receiver = address.recipient.strip().split()
    def formatted(parts):
        return {'first_name': parts[0], 'last_name': ' '.join(parts[1:]) or parts[0],
            'address': address.street, 'city': address.city, 'postal_code': address.postal_code,
            'phone': phone, 'country_code': 'IDN'}
    if not names or not receiver: raise HTTPException(422, 'Nama pelanggan dan penerima wajib diisi')
    request['shipping_address'] = formatted(receiver)
    request['billing_address'] = formatted(names)
    items = (await s.scalars(select(m.OrderItem).where(m.OrderItem.order_id == order.id)
        .order_by(m.OrderItem.sort_order))).all()
    if not items: raise HTTPException(409, 'Rincian item pembayaran tidak tersedia')
    products = {p.id: p for p in (await s.scalars(select(m.Product).where(m.Product.id.in_([i.product_id for i in items])))).all()}
    goods = max(0, int(order.total) - int(order.shipping_cost))
    gross = sum((i.subtotal for i in items), Decimal(0))
    allocations = [int((Decimal(goods) * i.subtotal / gross).to_integral_value(rounding=ROUND_FLOOR)) if gross else 0 for i in items]
    # Largest remainders avoid penny drift when discounts span multiple lines.
    fractions = sorted(range(len(items)), key=lambda n: (Decimal(goods) * items[n].subtotal / gross - allocations[n]) if gross else 0, reverse=True)
    for n in fractions[:goods - sum(allocations)]: allocations[n] += 1
    lines, all_images = [], True
    for item, allocated in zip(items, allocations):
        product = products[item.product_id]
        image = absolute_image(item.main_image, settings)
        all_images = all_images and bool(image)
        components = (await s.scalars(select(m.OrderItemComponent).where(m.OrderItemComponent.order_item_id == item.id,
            m.OrderItemComponent.component_type == 'add_on').order_by(m.OrderItemComponent.sort_order))).all()
        label = item.product_name + ((' dengan ' + ' '.join(c.product_name for c in components)) if components else '')
        unit, remainder = divmod(allocated, item.quantity)
        for part, (quantity, price) in enumerate(((item.quantity - remainder, unit), (remainder, unit + 1))):
            if not quantity: continue
            entry = {'id': re.sub(r'[^A-Za-z0-9]', '', item.id) + str(part), 'name': kki_text(label),
                'quantity': quantity, 'price': price, 'sku': item.sku or product.sku,
                'category': 'health-and-personal-care', 'type': 'physical',
                'url': settings.frontend_url + '/products/' + quote(product.slug, safe='')}
            if image: entry['image_url'] = image
            lines.append(entry)
    if order.shipping_cost:
        # Shipping is a positive fee, never a negative discount line.
        fee = {'id': 'SHIPPING', 'name': 'Pengiriman', 'quantity': 1, 'price': int(order.shipping_cost),
            'sku': 'SHIPPING', 'category': 'fee', 'type': 'shipping',
            'url': settings.frontend_url + '/orders'}
        if lines[0].get('image_url'): fee['image_url'] = lines[0]['image_url']
        lines.append(fee)
    if sum(row['quantity'] * row['price'] for row in lines) != int(order.total):
        raise HTTPException(409, 'Rincian pembayaran tidak cocok dengan total pesanan')
    request['order']['line_items'] = lines
    configured = [v.strip() for v in os.getenv('DOKU_PAYMENT_METHOD_TYPES', '').split(',') if v.strip()]
    if user.email and len(user.email) <= 128:
        customer['email'] = user.email
    else:
        customer.pop('email', None)
    # Incomplete legacy contacts can still use basic Hosted Checkout. Methods
    # requiring email/item images are offered only with a complete payload.
    full = bool(customer.get('email')) and all_images
    if configured:
        if not full and any(v.startswith('PEER_TO_PEER_') for v in configured):
            raise HTTPException(422, 'PayLater memerlukan email pelanggan dan gambar produk yang dapat diakses')
        request['payment']['payment_method_types'] = configured
    elif not full:
        request['payment']['payment_method_types'] = BASIC_METHODS
    if len(order.order_number) > 30:
        raise HTTPException(422, 'Nomor invoice lama melebihi batas kartu kredit DOKU; hubungi toko')
    return request
