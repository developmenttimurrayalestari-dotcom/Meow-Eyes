"""Private video evidence and replacement case endpoints."""
import asyncio
import hashlib
import os
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from auth import current_user, require_permission
from models import User
from database import read_session, session_scope
from mysql import models as m, returns as rma
from mysql.commerce import lock_user

router = APIRouter(tags=['returns'])
ROOT = (Path(os.environ.get('PRIVATE_UPLOAD_ROOT', str(Path(__file__).parent / 'private_uploads'))) / 'return-evidence').resolve()
MAX_BYTES = 100 * 1024 * 1024

class CaseItem(BaseModel):
    order_item_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=1000)
class CaseInput(BaseModel):
    items: list[CaseItem] = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=10, max_length=4000)
class Action(BaseModel):
    status: str
    note: str = Field(default='', max_length=4000)
    courier: str = Field(default='', max_length=128)
    tracking: str = Field(default='', max_length=128)
class Policy(BaseModel):
    window_days: int = Field(default=7, ge=1, le=365)
    return_days: int = Field(default=7, ge=1, le=90)
    recipient: str = Field(max_length=200)
    phone: str = Field(max_length=40)
    address: str = Field(max_length=2000)
    notes: str = Field(default='', max_length=2000)

async def owned(s, case_id, user, *, admin=False):
    # Always lock customer before case, including admin transitions.
    row = await s.get(m.ReturnCase, case_id)
    if not row or (not admin and row.user_id != user.user_id): raise HTTPException(404, 'Klaim tidak ditemukan')
    await lock_user(s, row.user_id)
    return await s.get(m.ReturnCase, case_id, with_for_update=True, populate_existing=True)

@router.get('/orders/{order_id}/returns')
async def order_returns(order_id: str, user: User = Depends(current_user)):
    async with read_session() as s:
        order = await s.scalar(select(m.Order).where(m.Order.id == order_id, m.Order.user_id == user.user_id))
        if not order: raise HTTPException(404, 'Pesanan tidak ditemukan')
        cases = (await s.scalars(select(m.ReturnCase).where(m.ReturnCase.order_id == order_id).order_by(m.ReturnCase.created_at.desc()))).all()
        return {**await rma.eligibility(s, order), 'cases': [await rma.payload(s, row) for row in cases]}

@router.post('/orders/{order_id}/returns')
async def create_return(order_id: str, body: CaseInput, user: User = Depends(current_user)):
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        return await rma.create(s, fresh, order_id, [item.model_dump() for item in body.items], body.reason)

@router.post('/returns/{case_id}/evidence')
async def upload_evidence(case_id: str, file: UploadFile = File(...), user: User = Depends(current_user)):
    if file.content_type not in ('video/mp4', 'video/webm'): raise HTTPException(422, 'Gunakan video MP4 atau WebM')
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / (uuid.uuid4().hex + ('.mp4' if file.content_type == 'video/mp4' else '.webm'))
    try:
        async with session_scope() as s:
            case = await owned(s, case_id, user)
            if case.status != 'draft': raise HTTPException(409, 'Bukti hanya dapat diunggah saat klaim masih draf')
            if await s.scalar(select(m.ReturnEvidence.id).where(m.ReturnEvidence.case_id == case.id).limit(1)): raise HTTPException(409, 'Video unboxing sudah terlampir')
            size, digest, header = 0, hashlib.sha256(), b''
            with path.open('xb') as stream:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_BYTES: raise HTTPException(413, 'Ukuran video maksimal 100 MB')
                    if len(header) < 64: header += chunk[:64 - len(header)]
                    digest.update(chunk)
                    await asyncio.to_thread(stream.write, chunk)
            valid = (len(header) >= 12 and header[4:8] == b'ftyp') if file.content_type == 'video/mp4' else header.startswith(b'\x1aE\xdf\xa3')
            if not valid or size < 32: raise HTTPException(422, 'Isi berkas bukan video MP4/WebM yang valid')
            evidence = m.ReturnEvidence(case_id=case.id, storage_path=path.name, mime_type=file.content_type, sha256=digest.hexdigest(), byte_size=size)
            s.add(evidence); await s.flush()
        return {'id': evidence.id, 'ok': True}
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    finally: await file.close()

@router.get('/returns/evidence/{evidence_id}')
async def evidence(evidence_id: str, user: User = Depends(current_user)):
    async with read_session() as s:
        row = await s.get(m.ReturnEvidence, evidence_id)
        case = await s.get(m.ReturnCase, row.case_id) if row else None
        staff = user.role in ('admin', 'super_admin') or (user.role == 'staff' and 'order.view' in (user.permissions or []))
        if not case or (case.user_id != user.user_id and not staff): raise HTTPException(404, 'Bukti tidak ditemukan')
        path = (ROOT / row.storage_path).resolve()
        if path.parent != ROOT or not path.is_file(): raise HTTPException(404, 'Video tidak ditemukan')
        return FileResponse(path, media_type=row.mime_type, headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff', 'Content-Disposition': 'inline'})

@router.post('/returns/{case_id}/status')
async def customer_status(case_id: str, body: Action, user: User = Depends(current_user)):
    async with session_scope() as s:
        return await rma.transition(s, await owned(s, case_id, user), user, body.status, note=body.note, courier=body.courier, tracking=body.tracking)

@router.get('/admin/returns/policy')
async def get_policy(admin: User = Depends(require_permission('order.view'))):
    async with read_session() as s: return await rma.policy(s)

@router.put('/admin/returns/policy')
async def save_policy(body: Policy, admin: User = Depends(require_permission('order.update'))):
    async with session_scope() as s:
        await lock_user(s, admin.user_id)
        row = await s.get(m.Setting, 'rma_policy', with_for_update=True)
        if not row: row = m.Setting(key='rma_policy', is_public=False); s.add(row)
        row.value, row.updated_by = body.model_dump(), admin.user_id
        await s.flush(); return row.value

@router.get('/admin/returns')
async def admin_returns(offset: int = Query(0, ge=0), status: str = '', admin: User = Depends(require_permission('order.view'))):
    async with read_session() as s:
        query = select(m.ReturnCase)
        if status: query = query.where(m.ReturnCase.status == status)
        rows = (await s.scalars(query.order_by(m.ReturnCase.updated_at.desc()).offset(offset).limit(30))).all()
        return {'cases': [await rma.payload(s, row) for row in rows], 'next_offset': offset + 30 if len(rows) == 30 else None}

@router.post('/admin/returns/{case_id}/status')
async def admin_status(case_id: str, body: Action, admin: User = Depends(require_permission('order.update'))):
    async with session_scope() as s:
        return await rma.transition(s, await owned(s, case_id, admin, admin=True), admin, body.status, admin=True, note=body.note, courier=body.courier, tracking=body.tracking)
