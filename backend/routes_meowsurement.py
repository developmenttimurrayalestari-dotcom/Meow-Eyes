"""Private, account-integrated Meowsurement API and typed frame catalog."""
from __future__ import annotations

from datetime import timedelta
import hashlib
from io import BytesIO
import os
from pathlib import Path
import warnings

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.concurrency import run_in_threadpool

from auth import current_user, require_permission
from database import read_session, session_scope
from meowsurement_schemas import (CustomerProfileInput, ExportInput, ProductSpecificationInput,
    RevisionActionInput, RevisionInput, ReviewInput, SessionCreateInput)
from models import User
from mysql import models as m
from mysql import meowsurement as service
from mysql.base import utcnow
from mysql.commerce import lock_user


PRIVATE_HEADERS = {"Cache-Control": "private, no-store, max-age=0", "Pragma": "no-cache",
                   "Vary": "Cookie, Authorization", "X-Content-Type-Options": "nosniff"}
PRIVATE_PHOTO_ROOT = Path(os.environ.get("MEOWSUREMENT_PRIVATE_ROOT", Path(__file__).parent / "private_uploads" / "meowsurement"))
MAX_PHOTO_BYTES = 8 * 1024 * 1024
PHOTO_RETENTION_DAYS = 30


class PrivateRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request: Request):
            try:
                if request.headers.get("content-type", "").split(";", 1)[0].lower() == "application/json":
                    chunks, length = [], 0
                    async for chunk in request.stream():
                        length += len(chunk)
                        if length > service.MAX_JSON_BYTES:
                            raise HTTPException(413, "Data pengukuran terlalu besar")
                        chunks.append(chunk)
                    request._body = b"".join(chunks)
                response = await original(request)
            except HTTPException as exc:
                response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
            except RequestValidationError as exc:
                # Do not echo prescriptions, image payloads, or raw request inputs.
                response = JSONResponse(status_code=422, content={"detail": "Data formulir tidak valid",
                    "fields": [".".join(str(v) for v in err["loc"][1:]) for err in exc.errors()[:30]]})
            except IntegrityError:
                response = JSONResponse(status_code=409, content={"detail": "Data telah berubah atau terkait dengan data lain. Muat ulang sebelum melanjutkan."})
            except DBAPIError as exc:
                code = (getattr(exc.orig, "args", ()) or (None,))[0]
                response = JSONResponse(status_code=422 if code == 1644 else 409 if code in (1205, 1213) else 503,
                    content={"detail": "Data tidak memenuhi aturan integritas" if code == 1644 else "Data sedang diproses; silakan ulangi permintaan" if code in (1205, 1213) else "Database sementara tidak tersedia"})
            response.headers.update(PRIVATE_HEADERS)
            return response
        return handler


router = APIRouter(route_class=PrivateRoute, tags=["Meowsurement"])


@router.get("/customer/profile")
async def customer_profile(user: User = Depends(current_user)):
    return await service.get_profile(user)


@router.put("/customer/profile")
async def customer_profile_update(payload: CustomerProfileInput, user: User = Depends(current_user)):
    return await service.update_profile(user, payload)


@router.get("/products/{product_id}/frame-specification")
async def public_frame_specification(product_id: str):
    async with read_session() as s:
        return await service.frame_specification(s, product_id, public=True)


@router.get("/admin/products/{product_id}/frame-specification")
async def admin_frame_specification(product_id: str, user: User = Depends(require_permission("product.view"))):
    async with read_session() as s:
        return await service.frame_specification(s, product_id)


@router.put("/admin/products/{product_id}/frame-specification")
async def admin_frame_specification_update(product_id: str, payload: ProductSpecificationInput,
                                          user: User = Depends(require_permission("product.update"))):
    return await service.update_specification(user, product_id, payload)


@router.get("/meowsurement/bootstrap")
async def bootstrap(user: User = Depends(current_user)):
    profile = await service.get_profile(user)
    return {**profile, "user": {"user_id": user.user_id, "name": profile["profile"]["name"], "email": user.email,
            "role": user.role, "permissions": user.permissions or []}, "can_review": service.is_reviewer(user), "settings": service.SETTINGS}


@router.get("/meowsurement/frames")
async def frame_choices(query: str = Query(default="", max_length=120), page: int = Query(default=1, ge=1, le=100000),
                        page_size: int = Query(default=15, ge=1, le=50), product_id: str | None = Query(default=None, max_length=64),
                        user: User = Depends(current_user)):
    return await service.list_frames(query, page, page_size, product_id)


@router.get("/meowsurement/sessions")
async def session_list(page: int = Query(default=1, ge=1, le=100000), page_size: int = Query(default=15, ge=1, le=50),
                       status: str | None = None, user: User = Depends(current_user)):
    return await service.list_sessions(user, status=status, page=page, page_size=page_size)


@router.get("/admin/meowsurement/sessions")
async def review_queue(page: int = Query(default=1, ge=1, le=100000), page_size: int = Query(default=15, ge=1, le=50),
                       status: str | None = None, user: User = Depends(require_permission("meowsurement.review"))):
    return await service.list_sessions(user, review_queue=True, status=status, page=page, page_size=page_size)


@router.post("/meowsurement/sessions", status_code=201)
async def session_create(payload: SessionCreateInput, user: User = Depends(current_user)):
    return await service.create_session(user, payload)


@router.get("/meowsurement/sessions/{session_id}")
async def session_detail(session_id: str, user: User = Depends(current_user)):
    return await service.get_session(user, session_id)


@router.post("/meowsurement/sessions/{session_id}/revisions")
async def revision_create(session_id: str, payload: RevisionInput, user: User = Depends(current_user)):
    return await service.save_revision(user, session_id, payload)


@router.post("/meowsurement/sessions/{session_id}/submit")
async def session_submit(session_id: str, payload: RevisionActionInput, user: User = Depends(current_user)):
    return await service.submit_session(user, session_id, payload)


@router.post("/meowsurement/sessions/{session_id}/reviews")
async def session_review(session_id: str, payload: ReviewInput, user: User = Depends(require_permission("meowsurement.review"))):
    return await service.review_session(user, session_id, payload)


@router.post("/meowsurement/sessions/{session_id}/exports")
async def report_export(session_id: str, payload: ExportInput, user: User = Depends(current_user)):
    return await service.authorize_export(user, session_id, payload)


def _normalized_photo(raw):
    if not raw:
        raise HTTPException(422, "Pilih foto yang akan diunggah")
    if len(raw) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "Foto maksimal 8 MiB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as original:
                if original.format not in {"JPEG", "PNG", "WEBP"} or getattr(original, "n_frames", 1) != 1:
                    raise HTTPException(415, "Gunakan foto JPEG, PNG, atau WEBP satu gambar")
                if original.width < 16 or original.height < 16 or original.width * original.height > 20000000:
                    raise HTTPException(413, "Resolusi foto harus 16 piksel atau lebih dan maksimal 20 megapiksel")
                original.verify()
            with Image.open(BytesIO(raw)) as original:
                original.load()
                oriented = ImageOps.exif_transpose(original).convert("RGBA")
                clean = Image.new("RGB", oriented.size, "white")
                clean.paste(oriented, mask=oriented.getchannel("A"))
                output = BytesIO()
                clean.save(output, "JPEG", quality=95, subsampling=0)
                normalized = output.getvalue()
                if len(normalized) > MAX_PHOTO_BYTES:
                    raise HTTPException(413, "Foto hasil normalisasi melebihi 8 MiB")
                return normalized, clean.width, clean.height
    except HTTPException:
        raise
    except (OSError, ValueError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(415, "Berkas bukan foto yang valid") from None


def _private_root():
    # Reject accidental deployment under the public asset tree.
    from routes_uploads import UPLOAD_ROOT
    root = PRIVATE_PHOTO_ROOT.resolve()
    public = UPLOAD_ROOT.resolve()
    if root == public or public in root.parents or PRIVATE_PHOTO_ROOT.is_symlink():
        raise HTTPException(503, "Penyimpanan foto privat belum dikonfigurasi")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


def _write_photo(photo_id, data):
    path = _private_root() / (photo_id + ".jpg")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _stored_photo_path(photo):
    if not service.IDENTIFIER.fullmatch(photo.id) or photo.storage_path != photo.id + ".jpg":
        raise HTTPException(404, "Foto tidak ditemukan")
    path = _private_root() / photo.storage_path
    if path.is_symlink() or not path.is_file():
        raise HTTPException(404, "Foto tidak ditemukan")
    return path


@router.post("/meowsurement/sessions/{session_id}/photos", status_code=201)
async def photo_upload(session_id: str, file: UploadFile = File(...), consent: bool = Form(default=False),
                       user: User = Depends(current_user)):
    if consent is not True:
        raise HTTPException(422, "Persetujuan unggah foto diperlukan")
    # Check authorization before reading image bytes or decoding user content.
    async with read_session() as s:
        session = await service.authorized_session(s, user, session_id, editing=True)
        revision = await service.current_revision(s, session)
        if any(revision.data.get("consents", {}).get(key) is not True for key in ("capture", "uploadPhotos")):
            raise HTTPException(422, "Aktifkan persetujuan unggah foto pada sesi terlebih dahulu")
    raw = await file.read(MAX_PHOTO_BYTES + 1)
    normalized, width, height = await run_in_threadpool(_normalized_photo, raw)
    photo_id = service.new_id("mp")
    path = None
    try:
        async with session_scope() as s:
            await lock_user(s, user.user_id)
            session = await service.authorized_session(s, user, session_id, editing=True, lock=True)
            revision = await service.current_revision(s, session)
            if any(revision.data.get("consents", {}).get(key) is not True for key in ("capture", "uploadPhotos")):
                raise HTTPException(409, "Persetujuan sesi telah berubah; muat ulang sebelum mengunggah")
            count = await s.scalar(select(func.count()).select_from(m.MeowsurementPhoto).where(
                m.MeowsurementPhoto.session_id == session.id, m.MeowsurementPhoto.deleted_at.is_(None)))
            if count >= 60:
                raise HTTPException(422, "Maksimal 60 foto aktif per sesi")
            path = await run_in_threadpool(_write_photo, photo_id, normalized)
            photo = m.MeowsurementPhoto(id=photo_id, session_id=session.id, user_id=user.user_id,
                storage_path=path.name, sha256=hashlib.sha256(normalized).hexdigest(), source_sha256=hashlib.sha256(raw).hexdigest(),
                mime_type="image/jpeg", width=width, height=height, byte_size=len(normalized), consent=True,
                expires_at=utcnow() + timedelta(days=PHOTO_RETENTION_DAYS))
            s.add(photo)
            await s.flush()
            service.audit(s, session.user_id, user.user_id, "photo.uploaded", session=session, revision=revision,
                          details={"photo_id": photo.id, "explicit_consent": True, "retention_days": PHOTO_RETENTION_DAYS})
            result = {"id": photo.id, "photoId": photo.id, "photo": service.photo_payload(photo)}
        return result
    except BaseException:
        if path is not None:
            path.unlink(missing_ok=True)
        raise


@router.get("/meowsurement/sessions/{session_id}/photos/{photo_id}")
async def photo_read(session_id: str, photo_id: str, user: User = Depends(current_user)):
    async with read_session() as s:
        session = await service.authorized_session(s, user, session_id)
        photo = await s.get(m.MeowsurementPhoto, photo_id)
        if not photo or photo.session_id != session.id or photo.user_id != session.user_id or photo.deleted_at or photo.expires_at <= utcnow():
            raise HTTPException(404, "Foto tidak ditemukan")
        path = _stored_photo_path(photo)
        raw = await run_in_threadpool(path.read_bytes)
        if len(raw) != photo.byte_size or hashlib.sha256(raw).hexdigest() != photo.sha256:
            raise HTTPException(404, "Foto tidak ditemukan")
        return Response(content=raw, media_type="image/jpeg", headers={**PRIVATE_HEADERS, "Content-Disposition": "inline; filename=meowsurement.jpg"})


@router.delete("/meowsurement/sessions/{session_id}/photos/{photo_id}")
async def photo_delete(session_id: str, photo_id: str, user: User = Depends(current_user)):
    path = None
    async with session_scope() as s:
        await lock_user(s, user.user_id)
        session = await service.authorized_session(s, user, session_id, editing=True, lock=True)
        photo = await s.get(m.MeowsurementPhoto, photo_id)
        if not photo or photo.session_id != session.id or photo.user_id != session.user_id:
            raise HTTPException(404, "Foto tidak ditemukan")
        if photo.deleted_at is None:
            photo.deleted_at = utcnow()
            try:
                path = _stored_photo_path(photo)
            except HTTPException:
                pass
            service.audit(s, session.user_id, user.user_id, "photo.deleted", session=session,
                          details={"photo_id": photo.id, "reason": "Permintaan pemilik akun"})
        await s.flush()
        result = {"deleted": True, "photo": service.photo_payload(photo)}
    if path is not None:
        try:
            await run_in_threadpool(path.unlink, missing_ok=True)
        except OSError:
            # The committed tombstone already prevents reads/exports; storage
            # maintenance can retry removal without restoring access.
            pass
    return result


async def expire_private_photos() -> dict:
    """Purge due image bytes, retaining immutable capture metadata and tombstones.

    Keyset batches revisit deleted records whose physical removal failed, and
    do not let previously purged rows starve later expiry candidates. No local
    browser database or customer account is changed by this job.
    """
    cutoff = utcnow()
    after = ""
    expired, removed = 0, 0
    while True:
        async with read_session() as s:
            candidates = (await s.execute(select(m.MeowsurementPhoto.id, m.MeowsurementPhoto.user_id,
                m.MeowsurementPhoto.session_id, m.MeowsurementPhoto.storage_path, m.MeowsurementPhoto.deleted_at).where(
                    m.MeowsurementPhoto.id > after,
                    or_(m.MeowsurementPhoto.expires_at <= cutoff, m.MeowsurementPhoto.deleted_at.is_not(None)))
                .order_by(m.MeowsurementPhoto.id).limit(200))).all()
        if not candidates:
            break
        for candidate in candidates:
            after = candidate.id
            if not service.IDENTIFIER.fullmatch(candidate.id) or candidate.storage_path != candidate.id + ".jpg":
                continue
            path = _private_root() / candidate.storage_path
            if candidate.deleted_at is not None and not path.exists() and not path.is_symlink():
                continue
            async with session_scope() as s:
                # Same ownership/session lock order as uploads and deletion.
                await lock_user(s, candidate.user_id, active=False)
                session = await s.scalar(select(m.MeowsurementSession).where(m.MeowsurementSession.id == candidate.session_id).with_for_update())
                photo = await s.scalar(select(m.MeowsurementPhoto).where(m.MeowsurementPhoto.id == candidate.id).with_for_update())
                if photo is None or (photo.deleted_at is None and photo.expires_at > cutoff):
                    continue
                existed = path.exists() or path.is_symlink()
                # Unlink only this validated leaf; never follow a link to its target.
                # Failure rolls back a new tombstone so the next run retries it.
                await run_in_threadpool(path.unlink, missing_ok=True)
                removed += int(existed)
                if photo.deleted_at is None:
                    photo.deleted_at = cutoff
                    expired += 1
                    service.audit(s, photo.user_id, photo.user_id, "photo.expired", session=session,
                                  details={"photo_id": photo.id, "automated": True, "policy": "30_days"})
        if len(candidates) < 200:
            break
    return {"expired": expired, "removed": removed}
