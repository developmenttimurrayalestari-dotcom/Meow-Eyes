"""Canonical Everpro address selection; API keys never reach the browser."""
import logging

from fastapi import HTTPException
from integrations.common import ProviderError
from integrations.everpro import get_everpro_client

logger = logging.getLogger('meow.shipping')


def location_error(error):
    logger.warning('Everpro location lookup failed: %s', error.code)
    message = 'Data wilayah EVERPRO belum dapat dimuat. Silakan coba kembali.'
    if error.code in {'authentication_failed', 'invalid_auth_response'}:
        message = 'Koneksi EVERPRO belum dapat diautentikasi. Hubungi toko untuk memeriksa layanan pengiriman.'
    return HTTPException(503, message)


async def region_options(level, parent_id=None):
    try:
        return await get_everpro_client().regions(level, parent_id)
    except ProviderError as error:
        raise location_error(error) from None


async def selected_location(selection):
    parent, chosen = None, {}
    for level, field in [('provinces', 'province_id'), ('cities', 'city_id'), ('districts', 'district_id'), ('subdistricts', 'subdistrict_id')]:
        options = await region_options(level, parent)
        row = next((row for row in options if row['id'] == getattr(selection, field)), None)
        if row is None:
            raise HTTPException(422, 'Pilihan wilayah tidak sesuai data EVERPRO. Pilih ulang provinsi hingga kelurahan/desa.')
        chosen[level], parent = row, row['id']
    return {'province': chosen['provinces']['name'], 'city': chosen['cities']['name'], 'district': chosen['districts']['name'],
            'subdistrict': chosen['subdistricts']['name'], 'postal_code': chosen['subdistricts']['postal_code'],
            'everpro_destination_id': chosen['subdistricts']['id']}


async def canonical_shipping_location(address, client):
    """Also protect legacy free-text addresses; never guess an ambiguous village.

    Everpro's postal endpoint can return numeric village IDs whereas its
    hierarchy uses opaque strings. Match the complete names and postal code,
    not incompatible ID representations.
    """
    normalize = lambda value: ' '.join(str(value or '').split()).casefold()
    fields = [('province', 'province_name'), ('city', 'city_name'), ('district', 'district_name'), ('subdistrict', 'sub_district_name')]
    try:
        body = await client.locations(address.postal_code)
    except ProviderError as error:
        raise location_error(error) from None
    rows = body.get('data')
    if not isinstance(rows, list):
        raise HTTPException(503, 'Respons wilayah EVERPRO tidak valid. Silakan coba kembali.')
    matches = [row for row in rows if isinstance(row, dict) and str(row.get('postal_code')) == address.postal_code
               and all(normalize(getattr(address, local)) and normalize(getattr(address, local)) == normalize(row.get(remote)) for local, remote in fields)]
    if not matches:
        raise HTTPException(422, 'Wilayah alamat belum sesuai data EVERPRO. Klik Ubah pada alamat, lalu pilih provinsi sampai kelurahan/desa dan simpan kembali.')
    row = matches[0]
    return {local: row[remote] for local, remote in fields} | {'postal_code': str(row['postal_code'])}
