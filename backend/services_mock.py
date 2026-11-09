"""Mock DOKU payment gateway + EVERPRO shipping aggregator."""
from __future__ import annotations
import secrets
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List


# ---------- DOKU mock ----------
def doku_create_payment(order_number: str, amount: float, method: str = "VA") -> Dict[str, Any]:
    """Simulate creating a DOKU payment / invoice."""
    invoice_id = "DOKU-" + secrets.token_hex(6).upper()
    va_number = "8808" + "".join(random.choices("0123456789", k=12))
    payload = {
        "invoice_id": invoice_id,
        "order_number": order_number,
        "amount": amount,
        "method": method,
        "va_number": va_number,
        "payment_url": f"/payment/confirm/{order_number}",
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "status": "pending",
    }
    return payload


def doku_verify_signature(payload: Dict[str, Any], signature: str) -> bool:
    """Mock signature verification — in a real impl we'd HMAC the payload."""
    return signature == "mock-signature"


# ---------- EVERPRO mock ----------
COURIERS: List[Dict[str, Any]] = [
    {"code": "jne", "name": "JNE", "services": [
        {"code": "REG", "label": "Regular (2-3 hari)", "base": 14000, "etd": "2-3"},
        {"code": "YES", "label": "Yakin Esok Sampai (1 hari)", "base": 22000, "etd": "1"},
    ]},
    {"code": "jnt", "name": "J&T Express", "services": [
        {"code": "EZ", "label": "Reguler (1-3 hari)", "base": 13000, "etd": "1-3"},
    ]},
    {"code": "sicepat", "name": "SiCepat", "services": [
        {"code": "REG", "label": "Reguler (1-3 hari)", "base": 12500, "etd": "1-3"},
        {"code": "BEST", "label": "BEST - Next Day", "base": 19000, "etd": "1"},
    ]},
    {"code": "anteraja", "name": "AnterAja", "services": [
        {"code": "REG", "label": "Reguler (1-2 hari)", "base": 12000, "etd": "1-2"},
    ]},
    {"code": "gosend", "name": "GoSend Instant", "services": [
        {"code": "SAME", "label": "Same Day Instan", "base": 28000, "etd": "0"},
    ]},
]

# Province-based surcharge (very rough mock)
PROV_SURCHARGE = {
    "DKI Jakarta": 0, "Banten": 1000, "Jawa Barat": 2000, "Jawa Tengah": 4000,
    "Jawa Timur": 5500, "DI Yogyakarta": 4000, "Bali": 9000, "Sumatera Utara": 12000,
    "Sumatera Selatan": 10000, "Kalimantan Timur": 15000, "Sulawesi Selatan": 17000,
    "Papua": 28000,
}


def everpro_cost(province: str, weight_gram: int) -> List[Dict[str, Any]]:
    """Return ongkir options for a destination + weight."""
    surch = PROV_SURCHARGE.get(province, 8000)
    weight_kg = max(1, (weight_gram + 999) // 1000)
    out = []
    for c in COURIERS:
        for s in c["services"]:
            cost = int(s["base"] + surch + (weight_kg - 1) * 3500)
            out.append({
                "courier_code": c["code"],
                "courier_name": c["name"],
                "service_code": s["code"],
                "service_label": s["label"],
                "cost": cost,
                "etd": s["etd"],
            })
    return out


def everpro_create_shipment(order_number: str, courier: str, service: str, address: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate creating a shipment, returning awb (tracking number)."""
    awb = courier.upper() + "-" + secrets.token_hex(5).upper()
    return {
        "awb": awb,
        "courier": courier,
        "service": service,
        "status": "created",
        "address": address,
        "order_number": order_number,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def everpro_track(awb: str) -> List[Dict[str, Any]]:
    """Mocked tracking log."""
    base = datetime.now(timezone.utc) - timedelta(hours=12)
    return [
        {"time": (base + timedelta(hours=0)).isoformat(), "status": "Paket diterima di gudang"},
        {"time": (base + timedelta(hours=2)).isoformat(), "status": "Sedang diproses"},
        {"time": (base + timedelta(hours=6)).isoformat(), "status": "Paket dalam perjalanan ke kota tujuan"},
        {"time": (base + timedelta(hours=10)).isoformat(), "status": "Tiba di hub kota tujuan"},
    ]
