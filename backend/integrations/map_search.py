"""Explicit address search; independent of shipping regions and Everpro tokens."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
import math
import os
import time
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException

_cache: OrderedDict = OrderedDict()
_last_request = 0.0
_lock = asyncio.Lock()
_TTL = 300
_MAX_CACHE = 128


def _results(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('features'), list):
        raise ValueError('Invalid geocoder response')
    results, seen = [], set()
    for feature in payload['features'][:50]:
        if not isinstance(feature, dict):
            continue
        geometry, props = feature.get('geometry'), feature.get('properties')
        if not isinstance(geometry, dict) or geometry.get('type') != 'Point' or not isinstance(props, dict):
            continue
        coordinates = geometry.get('coordinates')
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            continue
        lng, lat = coordinates[:2]  # GeoJSON order is longitude, latitude.
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (lat, lng)):
            continue
        if not (95 <= lng <= 141.1 and -11.1 <= lat <= 6.2) or str(props.get('countrycode', '')).upper() != 'ID':
            continue
        parts = [props.get(key) for key in ('name', 'street', 'housenumber', 'district', 'city', 'county', 'state', 'postcode')]
        label = ', '.join(dict.fromkeys(part.strip()[:150] for part in parts if isinstance(part, str) and part.strip()))[:600]
        if not label or (lat, lng, label) in seen:
            continue
        seen.add((lat, lng, label))
        results.append({'label': label, 'latitude': lat, 'longitude': lng})
        if len(results) == 5:
            break
    return results


async def search_address(query: str):
    global _last_request
    endpoint = os.getenv('MAP_GEOCODING_URL', 'https://photon.komoot.io/api/').strip()
    url = urlsplit(endpoint)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise HTTPException(503, 'Pencarian peta belum dikonfigurasi dengan benar.')
    normalized = ' '.join(query.split())
    if len(normalized) < 3:
        raise HTTPException(422, 'Ketik minimal 3 karakter untuk mencari alamat.')
    cache_key = (endpoint, normalized.casefold())
    async with _lock:
        now = time.monotonic()
        cached = _cache.get(cache_key)
        if cached and now - cached[0] < _TTL:
            _cache.move_to_end(cache_key)
            return {'results': cached[1]}
        if now - _last_request < 1:
            raise HTTPException(429, 'Pencarian terlalu cepat. Tunggu sebentar lalu tekan Cari lagi.', headers={'Retry-After': '1'})
        _last_request = now
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            response = await client.get(endpoint, params={'q': normalized, 'countrycode': 'ID', 'limit': 5}, headers={'User-Agent': 'MeowEyes-AddressSearch/1.0', 'Accept': 'application/json'})
        response.raise_for_status()
        results = _results(response.json())
    except (httpx.HTTPError, ValueError, TypeError):
        raise HTTPException(503, 'Pencarian alamat belum tersedia. Pilih titik di peta atau gunakan lokasi saya.') from None
    async with _lock:
        _cache[cache_key] = (time.monotonic(), results)
        _cache.move_to_end(cache_key)
        while len(_cache) > _MAX_CACHE:
            _cache.popitem(last=False)
    return {'results': results}
