"""Nested v3 request schemas from Everpro's published Swagger doc.json.

This module builds payloads only; it never sends a booking or changes an order.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from integrations.common import ProviderError

PACKAGE_TYPES = {1: 'REGULAR', 2: 'ORGANIC', 3: 'GLASSWARE', 4: 'LIQUID', 5: 'ELECTRONIC'}


def location_id(value):
    if isinstance(value, bool):
        raise HTTPException(503, 'ID wilayah numerik EVERPRO tidak valid')
    text = str(value)
    if not text.isascii() or not text.isdigit() or int(text) <= 0:
        raise HTTPException(503, 'ID wilayah numerik EVERPRO tidak valid')
    return int(text)


async def shipment_location_id(client, location):
    """Translate a canonical shared-master row to the provider's own ID.

    Never fall back to a local primary key if the provider lookup fails or
    matches a different region. The same village name alone is insufficient.
    """
    if getattr(getattr(client, 'settings', None), 'data_source', 'api') != 'database':
        return location_id(location.get('sub_district_id'))
    normalize = lambda value: ' '.join(str(value or '').split()).casefold()
    fields = ('province_name', 'city_name', 'district_name', 'sub_district_name', 'postal_code')
    body = await client.shipment_locations(str(location.get('postal_code', '')))
    rows = body.get('data')
    if not isinstance(rows, list):
        raise ProviderError('everpro', 'invalid_locations_response')
    matches = [row for row in rows if isinstance(row, dict) and all(
        normalize(location.get(field)) and normalize(row.get(field)) == normalize(location.get(field)) for field in fields)]
    if not matches:
        raise HTTPException(422, 'Wilayah pengiriman belum dapat dicocokkan dengan EVERPRO. Periksa alamat asal dan tujuan; hubungi toko jika wilayah sudah benar.')
    identities = {location_id(row.get('sub_district_id')) for row in matches}
    if len(identities) != 1:
        raise HTTPException(422, 'Wilayah pengiriman EVERPRO ambigu; hubungi toko untuk memeriksa alamat.')
    return identities.pop()


async def origin_location(client, settings):
    normalize = lambda value: ' '.join(str(value or '').split()).casefold()
    body = await client.locations(settings.origin_postal_code)
    rows = body.get('data')
    if not isinstance(rows, list):
        raise ProviderError('everpro', 'invalid_locations_response')
    matches = [row for row in rows if isinstance(row, dict)
               and str(row.get('postal_code')) == settings.origin_postal_code
               and normalize(row.get('sub_district_name')) == normalize(settings.origin_subdistrict)]
    if not matches or not settings.origin_subdistrict:
        raise HTTPException(422, 'Kelurahan dan kode pos pengirim belum sesuai data EVERPRO. Periksa alamat asal pengiriman pada Admin > Integrasi.')
    ids = {location_id(row.get('sub_district_id')) for row in matches}
    if len(ids) != 1:
        raise HTTPException(422, 'Wilayah pengirim EVERPRO ambigu; hubungi toko untuk memperbaiki konfigurasi.')
    return {'id': await shipment_location_id(client, matches[0])}


def rate_request(settings, origin, destination, *, weight, price, cod=False, coordinates=None):
    request = {
        'origin': deepcopy(origin), 'destination': {'id': location_id(destination['sub_district_id'])},
        'package': {'weight': float(Decimal(weight) / 1000), 'price': int(price),
                    'type': PACKAGE_TYPES[settings.package_type_id],
                    'dimension': {'length': settings.length_cm, 'width': settings.width_cm, 'height': settings.height_cm}},
        'shipment_type': settings.shipment_type, 'is_use_insurance': settings.insurance,
        'is_use_woodpacking': False,
    }
    if cod: request['payment_type'] = 'COD'
    if coordinates:
        request['origin'].update(latitude=coordinates[0], longitude=coordinates[1])
        request['destination'].update(latitude=coordinates[2], longitude=coordinates[3])
    return request


def surcharge(rate):
    def integer(value):
        try:
            number = Decimal(str(value))
            if isinstance(value, bool) or not number.is_finite() or number < 0 or number != int(number):
                raise ValueError()
            return int(number)
        except (ValueError, TypeError, InvalidOperation, OverflowError):
            raise ProviderError('everpro', 'invalid_rates_response') from None
    total = integer(rate.get('surcharge', 0))
    raw = rate.get('surcharge_details') or {}
    if not isinstance(raw, dict):
        raise ProviderError('everpro', 'invalid_rates_response')
    details = {key: integer(raw.get(key, 0)) for key in ('commodity_surcharge', 'woodpacking_surcharge')}
    if raw and sum(details.values()) != total:
        raise ProviderError('everpro', 'invalid_rates_response')
    return total, details


def booking_payload(order, address, quote, pickup_time):
    saved, rate = quote.request_payload or {}, quote.response_payload or {}
    origin, request = saved.get('origin') or {}, saved.get('rate_request') or {}
    signed = rate.get('signed_key')
    if not isinstance(signed, str) or not signed.strip() or len(signed) > 16384:
        raise HTTPException(409, 'Snapshot signed_key EVERPRO v3 tidak lengkap; pesanan memerlukan rekonsiliasi.')
    if not origin or not all(key in request for key in ('origin', 'destination', 'package')):
        raise HTTPException(409, 'Snapshot ongkir EVERPRO v3 tidak lengkap; pesanan memerlukan rekonsiliasi.')
    extra, details = surcharge(rate)
    # Swagger defines shipment_price as the price returned by Get Rates.
    # Surcharge is its provider breakdown; never add/subtract it again here.
    price = int(quote.cost)
    package = deepcopy(request['package'])
    package.update(description='Kacamata dan aksesori optik', count=1)
    if order.payment_mode == 'cod':
        goods = int(order.total - quote.cost - quote.insurance_cost)
        if goods <= 0 or goods != package['price']:
            raise HTTPException(409, 'Nilai COD tidak cocok dengan penawaran ongkir. Hubungi toko.')
    shipper = {**request['origin'], 'name': origin['name'], 'phone': origin['phone'], 'address': origin['address']}
    if origin.get('email'): shipper['email'] = origin['email']
    receiver = {**request['destination'], 'name': address.recipient, 'phone': address.phone, 'address': address.street}
    payload = {'client_order_no': order.order_number, 'order_reference_id': order.order_number,
               'shipper': shipper, 'receiver': receiver, 'package': package,
               'rate_code': quote.service_code, 'signed_key': signed, 'shipment_type': origin['shipment_type'],
               'shipment_price': price, 'insurance_price': int(quote.insurance_cost),
               'is_use_insurance': bool(request.get('is_use_insurance') or quote.insurance_cost > 0),
               'is_use_woodpacking': False, 'surcharge': extra, 'surcharge_details': details}
    if order.payment_mode == 'cod': payload.update(payment_type='COD', cod_price=int(order.total))
    if payload['shipment_type'] == 'PICKUP':
        if not pickup_time: raise HTTPException(422, 'Pilih waktu penjemputan Everpro')
        payload['pickup_time'] = pickup_time
    return payload
