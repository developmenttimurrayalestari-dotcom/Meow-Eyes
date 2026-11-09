"""Public CMS image files with transactional SQL metadata and bounded uploads."""
from __future__ import annotations
import hashlib
import logging
import mimetypes
import os
import re
from pathlib import Path, PurePosixPath
from typing import Optional
import xml.etree.ElementTree as ET
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, or_, select
from database import read_session, session_scope
from auth import current_user
from models import User
from mysql import models as m
from mysql.api import row_dict
from mysql.base import utcnow
from mysql.catalog import safe_values

log = logging.getLogger("meow.uploads")
UPLOAD_ROOT = Path(os.environ.get("UPLOAD_ROOT", str(Path(__file__).parent / "uploads"))).resolve()
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE_MB = int(os.environ.get("UPLOAD_MAX_MB", "8"))
ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
router = APIRouter(prefix="/uploads", tags=["uploads"])


async def public_upload_file(file_path: str) -> FileResponse:
    """Serve only a registered public local asset at the existing upload URL.

    File presence alone never grants access. Imported private assets remain
    inaccessible even when an operator copied their bytes into the public
    upload directory. Private prescription delivery is a separate service.
    """
    relative = PurePosixPath(file_path)
    if (not file_path or "\\" in file_path or "\x00" in file_path
            or relative.is_absolute() or relative.as_posix() != file_path
            or any(part in {".", ".."} for part in relative.parts)):
        raise HTTPException(404, "File tidak ditemukan")
    base = UPLOAD_ROOT.resolve()
    candidate = base
    try:
        for part in relative.parts:
            candidate /= part
            if candidate.is_symlink():
                raise HTTPException(404, "File tidak ditemukan")
        candidate = candidate.resolve()
        if not candidate.is_relative_to(base):
            raise HTTPException(404, "File tidak ditemukan")
    except (OSError, RuntimeError, ValueError):
        raise HTTPException(404, "File tidak ditemukan") from None
    async with read_session() as s:
        path_match = or_(m.Upload.storage_key == file_path,
            and_(m.Upload.subdir == str(relative.parent), m.Upload.disk_name == relative.name))
        records = (await s.scalars(select(m.Upload).where(m.Upload.storage_provider == "local", path_match)
            .order_by(m.Upload.id))).all()
        # A duplicate private metadata reference must not be bypassed by an
        # older public alias for the same physical file.
        if not records or any(record.visibility != "public" for record in records):
            raise HTTPException(404, "File tidak ditemukan")
        mime = records[0].mime
    if not candidate.is_file():
        raise HTTPException(404, "File tidak ditemukan")
    return FileResponse(candidate, media_type=mime if mime in ALLOWED_MIMES else "application/octet-stream",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store",
                 "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox"})


def _ext_of(filename: str, content_type: str | None) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext in ALLOWED_EXTS:
        return ext
    return {"image/png": ".png", "image/webp": ".webp", "image/gif": ".gif", "image/svg+xml": ".svg"}.get(content_type, ".jpg")


def _require_can_upload(user: User) -> None:
    if user.role not in ("staff", "admin", "super_admin"):
        raise HTTPException(403, "Perlu login staff/admin untuk upload")


def _safe_svg(raw: bytes) -> bytes:
    if re.search(br"<!\s*(?:DOCTYPE|ENTITY)", raw, re.I):
        raise HTTPException(415, "SVG dengan DTD/entity tidak didukung")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise HTTPException(415, "SVG tidak valid") from None
    tags = {"svg", "g", "path", "defs", "use", "symbol", "rect", "circle", "ellipse", "line", "polyline", "polygon",
            "text", "tspan", "title", "desc", "clipPath", "mask", "linearGradient", "radialGradient", "stop", "pattern"}
    attrs = {"id", "version", "viewBox", "preserveAspectRatio", "width", "height", "x", "y", "x1", "y1", "x2", "y2",
             "dx", "dy", "cx", "cy", "r", "rx", "ry", "d", "points", "fill", "fill-rule", "fill-opacity", "stroke",
             "stroke-width", "stroke-opacity", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray",
             "stroke-dashoffset", "opacity", "transform", "clip-path", "clip-rule", "clipPathUnits", "mask", "maskUnits",
             "maskContentUnits", "gradientUnits", "gradientTransform", "spreadMethod", "offset", "stop-color", "stop-opacity",
             "font-family", "font-size", "font-weight", "font-style", "text-anchor", "dominant-baseline", "letter-spacing",
             "textLength", "lengthAdjust", "href", "patternUnits", "patternContentUnits", "patternTransform", "space"}
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise HTTPException(415, "SVG tidak valid")
    count = 0
    for element in root.iter():
        count += 1
        if count > 10000:
            raise HTTPException(413, "SVG terlalu kompleks")
        if element.tag.rsplit("}", 1)[-1] not in tags:
            raise HTTPException(415, "SVG berisi elemen aktif atau tidak didukung")
        for key, value in element.attrib.items():
            name = key.rsplit("}", 1)[-1]
            if name not in attrs or len(value) > 100000:
                raise HTTPException(415, "SVG berisi atribut yang tidak didukung")
            if name == "href" and not re.fullmatch(r"#[A-Za-z_][\w:.-]*", value):
                raise HTTPException(415, "SVG tidak boleh memuat referensi eksternal")
            if re.search(r"url\s*\(", value, re.I) and not re.fullmatch(r"url\(#[A-Za-z_][\w:.-]*\)", value):
                raise HTTPException(415, "Referensi SVG tidak aman")
    # Re-serialization strips processing instructions outside the SVG root.
    return ET.tostring(root, encoding="utf-8")


def _validate_image(raw: bytes, declared: str | None, filename: str) -> tuple[bytes, str, str]:
    if declared and declared not in ALLOWED_MIMES:
        raise HTTPException(415, "Tipe file tidak didukung")
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        mime, ext = "image/png", ".png"
    elif raw.startswith(b"\xff\xd8\xff"):
        mime, ext = "image/jpeg", ".jpg"
    elif raw.startswith((b"GIF87a", b"GIF89a")):
        mime, ext = "image/gif", ".gif"
    elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        mime, ext = "image/webp", ".webp"
    elif declared == "image/svg+xml" or Path(filename).suffix.lower() == ".svg":
        raw = _safe_svg(raw)
        mime, ext = "image/svg+xml", ".svg"
    else:
        raise HTTPException(415, "Isi file bukan gambar yang didukung")
    if declared and declared != mime:
        raise HTTPException(415, "Tipe file tidak sesuai isi gambar")
    return raw, mime, ext


@router.post("")
async def upload_file(file: UploadFile = File(...), user: User = Depends(current_user)):
    _require_can_upload(user)
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise HTTPException(413, f"Maksimum {MAX_FILE_SIZE_MB}MB per file")
    if not raw:
        raise HTTPException(400, "File kosong")
    raw, mime, ext = _validate_image(raw, file.content_type, file.filename or "")
    now = utcnow()
    subdir = now.strftime("%Y-%m")
    (UPLOAD_ROOT / subdir).mkdir(parents=True, exist_ok=True)
    file_id = m.new_id()
    disk_name = file_id + ext
    disk_path = UPLOAD_ROOT / subdir / disk_name
    disk_path.write_bytes(raw)
    try:
        async with session_scope() as s:
            item = m.Upload(**safe_values(m.Upload, {
                "id": file_id, "url": f"/api/uploads-files/{subdir}/{disk_name}",
                "filename": Path(file.filename or disk_name).name, "mime": mime,
                "size": len(raw), "subdir": subdir, "disk_name": disk_name,
                "storage_provider": "local", "storage_key": f"{subdir}/{disk_name}",
                "visibility": "public", "sha256": hashlib.sha256(raw).hexdigest(),
                "uploaded_by": user.user_id, "uploaded_by_name": user.name,
            }))
            s.add(item)
            await s.flush()
            data = row_dict(item)
        return data
    except BaseException:
        disk_path.unlink(missing_ok=True)
        raise


@router.get("")
async def list_uploads(limit: int = Query(60, ge=1, le=200), skip: int = Query(0, ge=0),
                       q: Optional[str] = None, user: User = Depends(current_user)):
    _require_can_upload(user)
    async with read_session() as s:
        conditions = [m.Upload.visibility == "public"]
        if q:
            conditions.append(m.Upload.filename.icontains(q, autoescape=True))
        total = await s.scalar(select(func.count()).select_from(m.Upload).where(*conditions))
        items = (await s.scalars(select(m.Upload).where(*conditions)
            .order_by(m.Upload.created_at.desc(), m.Upload.id).offset(skip).limit(limit))).all()
        return {"items": [row_dict(item) for item in items], "total": total, "skip": skip, "limit": limit}


@router.delete("/{upload_id}")
async def delete_upload(upload_id: str, user: User = Depends(current_user)):
    _require_can_upload(user)
    async with session_scope() as s:
        item = await s.scalar(select(m.Upload).where(m.Upload.id == upload_id,
            m.Upload.visibility == "public").with_for_update())
        if item is None:
            raise HTTPException(404, "File tidak ditemukan")
        disk_path = None
        if item.storage_provider == "local" and item.subdir and item.disk_name:
            candidate = (UPLOAD_ROOT / item.subdir / item.disk_name).resolve()
            if candidate.is_relative_to(UPLOAD_ROOT):
                disk_path = candidate
            else:
                raise HTTPException(409, "Lokasi file tidak valid")
        await s.delete(item)
        await s.flush()  # FK-restricted referenced assets stay intact on disk.
    if disk_path is not None:
        try:
            disk_path.unlink(missing_ok=True)
        except OSError:
            log.warning("Removed upload metadata; local file cleanup requires retry (id=%s)", upload_id)
    return {"ok": True}
