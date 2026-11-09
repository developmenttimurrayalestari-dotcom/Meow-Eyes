"""DOKU non-SNAP Checkout API (hosted payment page).

Official protocol: https://developers.doku.com/accept-payments/doku-checkout/integration-guide/backend-integration
Signature: https://developers.doku.com/get-started-with-doku-api/signature-component/non-snap
No card data is collected or stored by this application.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import hmac
import secrets
from typing import Any, Mapping
from urllib.parse import quote, urlsplit

import httpx

from integrations.common import ProviderError, json_bytes, strict_json
from integrations.config import DokuSettings


def signature(secret: str, client_id: str, request_id: str, timestamp: str,
              target: str, body: bytes | None, *, response: bool = False) -> str:
    parts = [f"Client-Id:{client_id}", f"Request-Id:{request_id}",
             f"{'Response' if response else 'Request'}-Timestamp:{timestamp}", f"Request-Target:{target}"]
    if body is not None:
        digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
        parts.append(f"Digest:{digest}")
    digest = hmac.new(secret.encode(), "\n".join(parts).encode(), hashlib.sha256).digest()
    return "HMACSHA256=" + base64.b64encode(digest).decode("ascii")


def verify_notification(settings: DokuSettings, headers: Mapping[str, str], raw: bytes,
                        *, now: datetime | None = None) -> str:
    headers = {k.lower(): v for k, v in headers.items()}
    client, request_id = headers.get("client-id", ""), headers.get("request-id", "")
    timestamp, received = headers.get("request-timestamp", ""), headers.get("signature", "")
    if not hmac.compare_digest(client.encode("utf-8"), settings.client_id.encode("utf-8")) or not 1 <= len(request_id) <= 128:
        raise ProviderError("doku", "invalid_signature", 401)
    if any(not 33 <= ord(c) <= 126 for c in request_id):
        raise ProviderError("doku", "invalid_signature", 401)
    try:
        instant = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ProviderError("doku", "invalid_timestamp", 401) from None
    age = ((now or datetime.now(timezone.utc)) - instant).total_seconds()
    if age < -300 or age > settings.webhook_max_age_seconds:
        raise ProviderError("doku", "expired_signature", 401)
    expected = signature(settings.secret_key, client, request_id, timestamp, settings.notification_path, raw)
    if not hmac.compare_digest(received.encode("utf-8"), expected.encode("utf-8")):
        raise ProviderError("doku", "invalid_signature", 401)
    return request_id


def safe_checkout_url(value: Any) -> str:
    if not isinstance(value, str):
        raise ProviderError("doku", "invalid_payment_url")
    try:
        p = urlsplit(value)
        p.port
    except ValueError:
        raise ProviderError("doku", "invalid_payment_url") from None
    if p.scheme != "https" or not p.hostname or not (p.hostname == "doku.com" or p.hostname.endswith(".doku.com")) or p.username or p.password:
        raise ProviderError("doku", "invalid_payment_url")
    return value


class DokuClient:
    def __init__(self, settings: DokuSettings, *, transport: httpx.AsyncBaseTransport | None = None):
        self.settings, self.transport = settings, transport

    async def _request(self, method: str, target: str, request_id: str, payload: dict | None = None) -> dict:
        raw = json_bytes(payload) if payload is not None else None
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        headers = {
            "Client-Id": self.settings.client_id, "Request-Id": request_id,
            "Request-Timestamp": stamp, "Content-Type": "application/json", "Accept": "application/json",
            "Signature": signature(self.settings.secret_key, self.settings.client_id, request_id, stamp, target, raw),
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5), follow_redirects=False, transport=self.transport) as client:
                response = await client.request(method, self.settings.base_url + target, headers=headers, content=raw)
        except httpx.HTTPError:
            raise ProviderError("doku", "network_error", 503, uncertain=method == "POST") from None
        if response.status_code >= 400:
            code = "duplicate_request" if response.status_code == 409 else "provider_rejected"
            raise ProviderError("doku", code, 503 if response.status_code >= 500 else 502, uncertain=response.status_code >= 500 or response.status_code == 409)
        if response.status_code not in {200, 201} or len(response.content) > 2_000_000:
            raise ProviderError("doku", "invalid_response", uncertain=method == "POST")
        # The authenticated TLS endpoint is always used. Verify the official
        # response signature whenever DOKU supplies one; some Checkout response
        # versions only return the request signature inside response.headers.
        returned_signature = response.headers.get("Signature")
        response_stamp = response.headers.get("Response-Timestamp")
        if returned_signature or response_stamp:
            if not returned_signature or not response_stamp:
                raise ProviderError("doku", "invalid_response_signature", uncertain=method == "POST")
            expected = signature(self.settings.secret_key, self.settings.client_id, request_id, response_stamp,
                                 target, response.content if method == "POST" else None, response=True)
            if not hmac.compare_digest(returned_signature.encode("utf-8"), expected.encode("utf-8")):
                raise ProviderError("doku", "invalid_response_signature", uncertain=method == "POST")
        try:
            return strict_json(response.content)
        except (ValueError, UnicodeError):
            raise ProviderError("doku", "invalid_json", uncertain=method == "POST") from None

    async def create_payment(self, request_id: str, payload: dict) -> dict:
        return await self._request("POST", "/checkout/v1/payment", request_id, payload)

    async def check_status(self, invoice: str) -> dict:
        return await self._request("GET", "/orders/v1/status/" + quote(invoice, safe=""), secrets.token_hex(16))


def get_doku_client() -> DokuClient:
    return DokuClient(DokuSettings.from_env())
