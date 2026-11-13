"""Direct Google Identity Services verification, without an OAuth intermediary."""
from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Request
from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from pydantic import EmailStr, TypeAdapter, ValidationError
import requests


def client_id() -> str:
    return os.environ.get("GOOGLE_CLIENT_ID", "").strip()


def require_google_origin(request: Request) -> None:
    # A JS callback posts JSON to our API. Require an exact trusted Origin as
    # login CSRF protection, also when this endpoint is reached without CORS.
    defaults = "" if os.environ.get("APP_ENV") == "production" else (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173")
    allowed = {value.strip().rstrip("/") for value in os.environ.get("CORS_ORIGINS", defaults).split(",") if value.strip()}
    if request.headers.get("origin") not in allowed or request.headers.get("origin") in (None, "null", "*"):
        raise HTTPException(403, "Asal halaman login Google tidak diizinkan")
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(415, "Login Google memerlukan JSON")


def verify_google_credential(credential: str, nonce: str) -> dict:
    """Run in a worker thread: the official library verifies signature/time/aud/iss.

    Use a separate bounded HTTP transport per call; no DB lock spans network IO.
    Never log or persist the raw Google token.
    """
    audience = client_id()
    if not audience:
        raise HTTPException(503, "Login Google belum dikonfigurasi. Silakan gunakan email dan password.")
    try:
        with requests.Session() as session:
            transport = GoogleRequest(session=session)

            def bounded_request(url, method="GET", **kwargs):
                kwargs["timeout"] = 10
                return transport(url, method=method, **kwargs)

            claims = id_token.verify_oauth2_token(credential, bounded_request, audience=audience)
    except (TransportError, requests.RequestException):
        raise HTTPException(503, "Google sementara tidak dapat dihubungi. Silakan coba lagi.") from None
    except (ValueError, GoogleAuthError):
        raise HTTPException(401, "Identitas Google tidak valid atau sudah kedaluwarsa") from None
    if (claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com")
            or claims.get("aud") != audience or claims.get("azp", audience) != audience
            or claims.get("email_verified") is not True
            or not isinstance(claims.get("sub"), str) or not 1 <= len(claims["sub"]) <= 255
            or not isinstance(claims.get("nonce"), str)
            or not secrets.compare_digest(claims["nonce"].encode(), nonce.encode())):
        raise HTTPException(401, "Identitas Google tidak valid. Silakan masuk ulang.")
    try:
        email = str(TypeAdapter(EmailStr).validate_python(claims.get("email"))).lower()
    except ValidationError:
        raise HTTPException(401, "Email Google tidak valid") from None
    name = claims.get("name")
    picture = claims.get("picture")
    return {
        "subject": claims["sub"], "email": email,
        "name": name.strip()[:255] if isinstance(name, str) and name.strip() else email,
        "picture": picture if isinstance(picture, str) and picture.startswith("https://") and len(picture) <= 2048 else None,
        # Google is authoritative for Gmail and verified Workspace addresses.
        "authoritative_email": email.endswith("@gmail.com") or bool(claims.get("hd")),
    }
