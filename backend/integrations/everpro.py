"""Everpro legacy and v3 shipment contracts, with separately versioned auth.

Official Swagger: https://client-api-sandbox.everpro.id/swagger/index.html . Production
host and callback key are supplied by Everpro during merchant onboarding.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from copy import deepcopy
import time
from typing import Any
from urllib.parse import quote

import httpx

from integrations.common import ProviderError, strict_json
from integrations.config import EverproSettings
from integrations.everpro_reference import EverproReferenceStore, refresh_shared_token


def token_rejected(status, body):
    if status == 401: return True
    message = str(body.get('message', '')).lower()
    return status == 403 and any(value in message for value in ('invalid token', 'token expired', 'token is expired', 'expired token'))


class EverproClient:
    def __init__(self, settings: EverproSettings, *, transport: httpx.AsyncBaseTransport | None = None, reference_store=None):
        self.settings, self.transport = settings, transport
        self._token, self._expires = "", 0.0
        self._token_lock = asyncio.Lock()
        self._locations_cache = OrderedDict()
        self.reference_store = reference_store or (EverproReferenceStore(settings) if settings.data_source == 'database' else None)
        self.token_source = None
        self._rejected_token = None

    async def _send(self, method: str, target: str, *, payload: dict | None = None,
                    params: dict | None = None, token: str | None = None) -> tuple[int, dict]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5), follow_redirects=False, transport=self.transport) as client:
                response = await client.request(method, self.settings.base_url + target, headers=headers, json=payload, params=params)
        except httpx.HTTPError:
            raise ProviderError("everpro", "network_error", 503, uncertain=method == "POST" and target in ("/shipment/v1/orders", "/shipment/v3/orders")) from None
        if len(response.content) > 2_000_000:
            raise ProviderError("everpro", "invalid_response", uncertain=method == "POST" and target in ("/shipment/v1/orders", "/shipment/v3/orders"))
        try:
            data = strict_json(response.content)
        except (ValueError, UnicodeError):
            if response.status_code == 401: return 401, {}
            raise ProviderError("everpro", "invalid_response", uncertain=method == "POST" and target in ("/shipment/v1/orders", "/shipment/v3/orders")) from None
        return response.status_code, data

    async def _auth(self, *, force: bool = False, rejected_token=None) -> str:
        async with self._token_lock:
            if force and rejected_token and self._token and self._token != rejected_token and time.monotonic() < self._expires:
                return self._token  # Another concurrent request already replaced the rejected token.
            if not force and self._token and time.monotonic() < self._expires:
                return self._token
            if self.settings.data_source == 'database':
                if rejected_token:
                    self._rejected_token = rejected_token
                    if self._token == rejected_token: self._expires = 0
                candidate = None
                try:
                    candidate = await self.reference_store.token()
                except ProviderError as exc:
                    if exc.code != 'reference_database_unavailable': raise
                rejected = rejected_token or (self._token if force else None)
                if candidate and candidate.remaining() > 5 and candidate.value not in (rejected, self._rejected_token):
                    self._token = candidate.value
                    self._expires = time.monotonic() + min(30, max(1, candidate.remaining() - 5))
                    self.token_source = 'database'
                    return self._token
                candidate = await refresh_shared_token(self.settings, transport=self.transport)
                if candidate.value in (rejected, self._rejected_token) or candidate.remaining() <= 5:
                    raise ProviderError('everpro', 'shared_token_refresh_rejected', 503)
                self._token = candidate.value
                self._expires = time.monotonic() + min(30, max(1, candidate.remaining() - 5))
                self.token_source = 'refresh_api'
                return self._token
            status, body = await self._send("POST", self.settings.auth_path, payload={
                "client_key": self.settings.client_key, "client_secret": self.settings.client_secret,
            })
            data = body.get("data") or {}
            if status != 200 or not isinstance(data, dict) or not isinstance(data.get("token"), str) or data.get("token_type", "Bearer") != "Bearer":
                raise ProviderError("everpro", "authentication_failed", 503)
            try:
                expires = max(30, min(int(data.get("expires", 300)), 86400))
            except (ValueError, TypeError):
                raise ProviderError("everpro", "invalid_auth_response") from None
            self._token, self._expires = data["token"], time.monotonic() + max(1, expires - 30)
            self.token_source = 'everpro_auth'
            return self._token

    async def request(self, method: str, target: str, *, payload: dict | None = None, params: dict | None = None) -> dict:
        token = await self._auth()
        status, body = await self._send(method, target, payload=payload, params=params, token=token)
        if token_rejected(status, body):
            token = await self._auth(force=True, rejected_token=token)
            status, body = await self._send(method, target, payload=payload, params=params, token=token)
        if token_rejected(status, body):
            raise ProviderError('everpro', 'authentication_failed', 503)
        if status not in {200, 201, 202} or body.get("status") in {"error", "failed"}:
            code = "not_found" if status == 404 else "duplicate_order" if status == 409 else "provider_rejected"
            raise ProviderError("everpro", code, status if status in {404, 409} else 502, uncertain=status >= 500)
        return body

    async def locations(self, postal_code: str) -> dict:
        if self.settings.data_source == 'database':
            return await self.reference_store.locations(postal_code)
        return await self._location_request('POST', '/location/v1/postalcode', payload={'postal_code': postal_code})

    async def shipment_locations(self, postal_code: str) -> dict:
        """Resolve provider IDs; shared master primary keys are not Everpro IDs.

        Address dropdowns still use the shared DB. Only shipment ID translation
        needs this cached provider lookup, authenticated with the shared token.
        """
        return await self._location_request('POST', '/location/v1/postalcode', payload={'postal_code': postal_code})

    async def _location_request(self, method, path, *, payload=None, params=None):
        key = (path, tuple(sorted((payload or params or {}).items())))
        cached = self._locations_cache.get(key)
        if cached and cached[0] > time.monotonic():
            self._locations_cache.move_to_end(key)
            return deepcopy(cached[1])
        try:
            result = await self.request(method, path, payload=payload, params=params)
        except ProviderError as exc:
            if exc.code != 'not_found':
                raise
            result = {'data': []}
        if not isinstance(result.get('data'), list):
            raise ProviderError('everpro', 'invalid_locations_response')
        self._locations_cache[key] = (time.monotonic() + 3600, deepcopy(result))
        self._locations_cache.move_to_end(key)
        while len(self._locations_cache) > 256:
            self._locations_cache.popitem(last=False)
        return result

    async def regions(self, level: str, parent_id: str | None = None) -> list[dict]:
        if self.settings.data_source == 'database':
            return await self.reference_store.regions(level, parent_id)
        fields = {'provinces': ('provinces', 'province', None), 'cities': ('cities', 'city', 'province_id'),
                  'districts': ('districts', 'district', 'city_id'), 'subdistricts': ('sub-districts', 'sub_district', 'district_id')}
        path, prefix, parent = fields[level]
        if parent and not parent_id:
            raise ValueError('A parent region is required')
        body = await self._location_request('GET', '/location/v1/' + path, params={parent: parent_id} if parent else None)
        result, seen = [], set()
        for row in body['data']:
            if not isinstance(row, dict):
                raise ProviderError('everpro', 'invalid_locations_response')
            identity, name = row.get(prefix + '_id'), row.get(prefix + '_name')
            if isinstance(identity, bool) or not isinstance(identity, (str, int)) or not str(identity).strip() or len(str(identity)) > 128 or not isinstance(name, str) or not 1 <= len(name.strip()) <= 128:
                raise ProviderError('everpro', 'invalid_locations_response')
            identity = str(identity)
            if identity in seen:
                raise ProviderError('everpro', 'invalid_locations_response')
            seen.add(identity)
            item = {'id': identity, 'name': name.strip()}
            if level == 'subdistricts':
                postal = str(row.get('postal_code', ''))
                if len(postal) != 5 or not postal.isascii() or not postal.isdigit():
                    raise ProviderError('everpro', 'invalid_locations_response')
                item['postal_code'] = postal
            result.append(item)
        return sorted(result, key=lambda row: (row['name'].casefold(), row['id']))

    async def rates(self, payload: dict) -> dict:
        path = '/shipment/v3/rates' if self.settings.api_version == 3 else '/shipment/v2/rates'
        return await self.request("POST", path, payload=payload)

    async def create_shipment(self, payload: dict) -> dict:
        # client_order_no is persisted before the first call and NEVER changed
        # by retries. An ambiguous response is reconciled by GET, not recreated
        # with a new identifier.
        path = '/shipment/v3/orders' if self.settings.api_version == 3 else '/shipment/v1/orders'
        return await self.request("POST", path, payload=payload)

    async def order_detail(self, number: str) -> dict:
        return await self.request("GET", "/shipment/v1/orders/" + quote(number, safe=""))

    async def tracking(self, awb: str) -> dict:
        return await self.request("GET", "/shipment/v1/orders/" + quote(awb, safe="") + "/track")

    async def awb(self, number: str) -> dict:
        return await self.request("GET", "/shipment/v1/orders/" + quote(number, safe="") + "/awb")

    async def label(self, awb: str) -> dict:
        return await self.request("GET", "/shipment/v1/orders/" + quote(awb, safe="") + "/label")

    async def pickup_times(self, rate_code: str) -> dict:
        return await self.request("GET", "/shipment/v1/pickup-times", params={"rate_codes": rate_code, "timezone": "Asia/Jakarta"})


_client: EverproClient | None = None


def get_everpro_client() -> EverproClient:
    global _client
    settings = EverproSettings.from_env(require_origin=False)
    if _client is None or _client.settings != settings:
        _client = EverproClient(settings)
    return _client
