"""Explicit, server-only integration configuration.

The URLs and protocols are documented in docs/INTEGRATIONS.md. Credentials are
never returned by diagnostics or included in a dataclass representation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
import os
import re
from urllib.parse import urlsplit

from fastapi import HTTPException


def mock_enabled() -> bool:
    return os.environ.get("APP_ENV", "development") in {"development", "test"} and os.environ.get("ENABLE_MOCK_PAYMENTS", "0") == "1"


def payment_provider() -> str:
    value = os.environ.get("PAYMENT_PROVIDER", "mock" if mock_enabled() else "doku").strip().lower()
    if value not in {"doku", "mock", "disabled"}:
        raise HTTPException(503, "Konfigurasi penyedia pembayaran tidak valid")
    if value == "mock" and not mock_enabled():
        raise HTTPException(503, "Pembayaran simulasi tidak tersedia")
    return value


def shipping_provider() -> str:
    value = os.environ.get("SHIPPING_PROVIDER", "mock" if mock_enabled() else "everpro").strip().lower()
    if value not in {"everpro", "mock", "disabled"}:
        raise HTTPException(503, "Konfigurasi penyedia pengiriman tidak valid")
    if value == "mock" and not mock_enabled():
        raise HTTPException(503, "Pengiriman simulasi tidak tersedia")
    return value


def _local_host(host: str | None) -> bool:
    if host == 'localhost':
        return True
    try:
        address = ipaddress.ip_address(host or '')
    except ValueError:
        return False
    networks = ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7')
    return address.is_loopback or any(address.version == network.version and address in network
                                    for network in map(ipaddress.ip_network, networks))


def _http_url(value: str, name: str, *, local: bool = False) -> str:
    try:
        p = urlsplit(value)
        p.port
    except ValueError:
        raise HTTPException(503, f"Konfigurasi {name} tidak valid") from None
    local_http = local and p.scheme == "http" and _local_host(p.hostname)
    if (p.scheme != "https" and not local_http) or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise HTTPException(503, f"Konfigurasi {name} tidak valid")
    return value.rstrip("/")


def _int_env(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        if not lo <= value <= hi:
            raise ValueError
        return value
    except ValueError:
        raise HTTPException(503, f"Konfigurasi {name} tidak valid") from None


@dataclass(frozen=True)
class DokuSettings:
    client_id: str
    secret_key: str = field(repr=False)
    environment: str = "sandbox"
    frontend_url: str = "http://localhost:3000"
    notification_path: str = "/api/webhooks/doku"
    public_api_url: str = ""
    due_minutes: int = 60
    webhook_max_age_seconds: int = 172800

    @property
    def base_url(self) -> str:
        return "https://api.doku.com" if self.environment == "production" else "https://api-sandbox.doku.com"

    @property
    def notification_override_url(self) -> str | None:
        # DOKU's server cannot reach the developer's private LAN. Browser
        # return URLs can still point there during sandbox testing; notification
        # delivery uses the merchant dashboard unless a public URL is supplied.
        if not self.public_api_url or _local_host(urlsplit(self.public_api_url).hostname):
            return None
        return self.public_api_url + self.notification_path

    @classmethod
    def from_env(cls) -> "DokuSettings":
        missing = [key for key in ("DOKU_CLIENT_ID", "DOKU_SECRET_KEY", "PUBLIC_FRONTEND_URL") if not os.environ.get(key)]
        if missing:
            raise HTTPException(503, "Pembayaran DOKU belum dikonfigurasi")
        env = os.environ.get("DOKU_ENVIRONMENT", "sandbox").strip().lower()
        if env not in {"sandbox", "production"}:
            raise HTTPException(503, "Konfigurasi DOKU_ENVIRONMENT tidak valid")
        local = env == "sandbox" and os.environ.get("APP_ENV", "development") in {"development", "test"}
        frontend = _http_url(os.environ["PUBLIC_FRONTEND_URL"], "PUBLIC_FRONTEND_URL", local=local)
        public_api = os.environ.get("PUBLIC_API_URL", "").rstrip("/")
        if public_api:
            public_api = _http_url(public_api, "PUBLIC_API_URL", local=local)
        path = os.environ.get("DOKU_NOTIFICATION_PATH", "/api/webhooks/doku")
        if not re.fullmatch(r"/[A-Za-z0-9/_-]+", path):
            raise HTTPException(503, "Konfigurasi DOKU_NOTIFICATION_PATH tidak valid")
        client_id = os.environ["DOKU_CLIENT_ID"].strip()
        if not client_id or len(client_id) > 191 or any(ord(c) < 33 or ord(c) > 126 for c in client_id):
            raise HTTPException(503, "Konfigurasi DOKU_CLIENT_ID tidak valid")
        return cls(client_id, os.environ["DOKU_SECRET_KEY"], env, frontend, path, public_api,
                   _int_env("DOKU_PAYMENT_DUE_MINUTES", 60, 5, 1440),
                   _int_env("DOKU_WEBHOOK_MAX_AGE_SECONDS", 172800, 300, 604800))


@dataclass(frozen=True)
class EverproSettings:
    client_key: str = field(repr=False)
    client_secret: str = field(repr=False)
    base_url: str = "https://client-api-sandbox.everpro.id"
    environment: str = "sandbox"
    webhook_key: str = field(default="", repr=False)
    origin_postal_code: str = ""
    origin_subdistrict: str = ""
    shipper_name: str = ""
    shipper_phone: str = ""
    shipper_address: str = ""
    shipper_email: str = ""
    shipment_type: str = "DROP"
    package_type_id: int = 3
    length_cm: int = 20
    width_cm: int = 12
    height_cm: int = 8
    insurance: bool = False
    quote_ttl_seconds: int = 600

    @classmethod
    def from_env(cls) -> "EverproSettings":
        required = ("EVERPRO_CLIENT_KEY", "EVERPRO_CLIENT_SECRET", "EVERPRO_ORIGIN_POSTAL_CODE",
                    "EVERPRO_SHIPPER_NAME", "EVERPRO_SHIPPER_PHONE", "EVERPRO_SHIPPER_ADDRESS")
        if any(not os.environ.get(name) for name in required):
            raise HTTPException(503, "Pengiriman Everpro belum dikonfigurasi")
        env = os.environ.get("EVERPRO_ENVIRONMENT", "sandbox").strip().lower()
        if env not in {"sandbox", "production"}:
            raise HTTPException(503, "Konfigurasi EVERPRO_ENVIRONMENT tidak valid")
        # The public specification lists the sandbox host. Production host is
        # supplied during onboarding; do not invent or silently switch it.
        base = os.environ.get("EVERPRO_BASE_URL", "")
        if not base and env == "sandbox":
            base = "https://client-api-sandbox.everpro.id"
        base = _http_url(base, "EVERPRO_BASE_URL")
        host = urlsplit(base).hostname or ""
        if not (host == "everpro.id" or host.endswith(".everpro.id")):
            raise HTTPException(503, "EVERPRO_BASE_URL harus menggunakan host resmi Everpro")
        if env == "production" and "sandbox" in host:
            raise HTTPException(503, "Host sandbox tidak dapat digunakan sebagai Everpro production")
        postal = os.environ["EVERPRO_ORIGIN_POSTAL_CODE"].strip()
        if not re.fullmatch(r"\d{5}", postal):
            raise HTTPException(503, "Konfigurasi kode pos pengirim tidak valid")
        kind = os.environ.get("EVERPRO_SHIPMENT_TYPE", "DROP").upper()
        if kind not in {"DROP", "PICKUP"}:
            raise HTTPException(503, "Konfigurasi EVERPRO_SHIPMENT_TYPE tidak valid")
        phone = os.environ["EVERPRO_SHIPPER_PHONE"].strip()
        if not re.fullmatch(r"(?:\+?62|08)\d{8,12}", phone) or len(phone) > 15:
            raise HTTPException(503, "Konfigurasi telepon pengirim tidak valid")
        name = os.environ["EVERPRO_SHIPPER_NAME"].strip()
        address = os.environ["EVERPRO_SHIPPER_ADDRESS"].strip()
        if len(name) < 3 or not 3 <= len(address) <= 250:
            raise HTTPException(503, "Konfigurasi nama/alamat pengirim tidak valid")
        return cls(
            client_key=os.environ["EVERPRO_CLIENT_KEY"], client_secret=os.environ["EVERPRO_CLIENT_SECRET"],
            base_url=base, environment=env, webhook_key=os.environ.get("EVERPRO_WEBHOOK_KEY", ""),
            origin_postal_code=postal, origin_subdistrict=os.environ.get("EVERPRO_ORIGIN_SUBDISTRICT", ""),
            shipper_name=name, shipper_phone=phone, shipper_address=address,
            shipper_email=os.environ.get("EVERPRO_SHIPPER_EMAIL", ""), shipment_type=kind,
            package_type_id=_int_env("EVERPRO_PACKAGE_TYPE_ID", 3, 1, 5),
            length_cm=_int_env("EVERPRO_PACKAGE_LENGTH_CM", 20, 1, 300),
            width_cm=_int_env("EVERPRO_PACKAGE_WIDTH_CM", 12, 1, 300),
            height_cm=_int_env("EVERPRO_PACKAGE_HEIGHT_CM", 8, 1, 300),
            insurance=os.environ.get("EVERPRO_USE_INSURANCE", "0") == "1",
            quote_ttl_seconds=_int_env("EVERPRO_QUOTE_TTL_SECONDS", 600, 60, 1800),
        )


def require_payment_provider() -> str:
    provider = payment_provider()
    if provider == "doku":
        DokuSettings.from_env()
    elif provider == "disabled":
        raise HTTPException(503, "Pembayaran belum diaktifkan")
    return provider
