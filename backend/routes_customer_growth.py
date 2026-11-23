"""Email verification, member rewards and customer administration."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select, func, or_, delete
from sqlalchemy.exc import IntegrityError
from auth import current_user, current_admin
from database import session_scope, read_session
from models import User
from mysql import models as m
from mysql.api import row_dict, order_dict
from mysql.commerce import lock_user, voucher_amount
from mysql import customer_growth as growth
from mysql import points
from phone_identity import normalize_phone
import verification_mail

router = APIRouter(tags=['customer-growth'])


class VerificationToken(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class CustomerEdit(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = None

    @field_validator('phone')
    @classmethod
    def phone_format(cls, value): return normalize_phone(value) if value else None


@router.post('/auth/verification/resend')
async def resend(user: User = Depends(current_user)):
    await growth.request_verification(user.user_id)
    return {'ok': True, 'retry_after': 60}


@router.post('/auth/verification/confirm')
async def confirm(req: VerificationToken):
    return await growth.verify_email(req.token)


@router.get('/account/benefits')
async def benefits(user: User = Depends(current_user)):
    await growth.deliver_rewards(user.user_id)
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        growth.ensure_code(fresh)
        await points.expire(s, fresh)
        cfg = await growth.config(s)
        today = growth.local_day().isoformat()
        last = await s.scalar(select(m.DailyCheckin).where(m.DailyCheckin.user_id == user.user_id)
            .order_by(m.DailyCheckin.day.desc()).limit(1))
        referrals = await s.scalar(select(func.count()).select_from(m.Referral).where(m.Referral.referrer_id == user.user_id))
        return {'referral_code': fresh.referral_code, 'referral_count': referrals,
            'email': fresh.email, 'email_verified_at': fresh.email_verified_at,
            'email_delivery_ready': verification_mail.ready(), 'points_balance': fresh.points_balance,
            'checkin_today': bool(last and last.day == today), 'last_checkin': row_dict(last) if last else None,
            'config': cfg}


@router.post('/account/check-in')
async def checkin(user: User = Depends(current_user)):
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        row = await growth.checkin(s, fresh)
        return {'checkin': row_dict(row), 'points_balance': fresh.points_balance}


@router.patch('/account/contact')
async def contact(req: CustomerEdit, user: User = Depends(current_user)):
    return await edit_customer(user.user_id, req, self_service=True)


async def edit_customer(uid, req, *, self_service=False):
    try:
        async with session_scope() as s:
            row = await lock_user(s, uid, active=bool(self_service))
            if not self_service and row.role != 'customer':
                raise HTTPException(403, 'Modul ini hanya untuk akun pelanggan')
            email = str(req.email).lower() if req.email else None
            if not email and not req.phone: raise HTTPException(422, 'Email atau telepon wajib diisi')
            if row.email != email:
                row.email_verified_at = None
                await s.execute(delete(m.EmailVerification).where(m.EmailVerification.user_id == uid))
            row.name, row.email, row.phone = req.name.strip(), email, req.phone
            if not row.name: raise HTTPException(422, 'Nama wajib diisi')
            await s.flush()
            return {'ok': True}
    except IntegrityError:
        raise HTTPException(409, 'Email atau nomor telepon telah digunakan akun lain') from None


@router.post('/vouchers/{voucher_id}/claim')
async def claim(voucher_id: str, user: User = Depends(current_user)):
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        voucher = await s.get(m.Voucher, voucher_id)
        if not voucher: raise HTTPException(404, 'Voucher tidak ditemukan')
        voucher_amount(voucher, max(voucher.min_purchase, 0))
        await growth.voucher_eligible(s, fresh, voucher, claim=True)
        return {'ok': True, 'code': voucher.code}


@router.get('/admin/settings/customer-growth')
async def admin_config(admin: User = Depends(current_admin)):
    async with read_session() as s:
        return {'config': await growth.config(s), 'email_delivery_ready': verification_mail.ready()}


@router.put('/admin/settings/customer-growth')
async def save_config(req: growth.GrowthConfig, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        for rule in (req.referrer, req.referee):
            if rule.kind == 'voucher':
                voucher = await s.get(m.Voucher, rule.voucher_id)
                if not voucher or not voucher.is_active or voucher.audience == 'new_member':
                    raise HTTPException(422, 'Pilih voucher aktif yang bukan voucher member baru')
        row = await s.get(m.Setting, 'customer_growth')
        if not row:
            row = m.Setting(key='customer_growth', value={}, is_public=False)
            s.add(row)
        row.value, row.updated_by = req.model_dump(), admin.user_id
    return {'ok': True}


async def customer_list(s, q=None, page=1, page_size=25, verified=None, active=None):
    where = [m.User.role == 'customer']
    if q: where.append(or_(m.User.name.icontains(q, autoescape=True), m.User.email.icontains(q, autoescape=True), m.User.phone.icontains(q, autoescape=True)))
    if verified is not None: where.append(m.User.email_verified_at.is_not(None) if verified else m.User.email_verified_at.is_(None))
    if active is not None: where.append(m.User.is_active == active)
    total = await s.scalar(select(func.count()).select_from(m.User).where(*where))
    rows = (await s.scalars(select(m.User).where(*where).order_by(m.User.created_at.desc(), m.User.user_id)
        .offset((page - 1) * page_size).limit(page_size))).all()
    users = []
    for row in rows:
        data = {key: row_dict(row)[key] for key in ('user_id','name','email','phone','role','is_active','points_balance','email_verified_at','referral_code','created_at')}
        data['referral_count'] = await s.scalar(select(func.count()).select_from(m.Referral).where(m.Referral.referrer_id == row.user_id))
        users.append(data)
    return {'users': users, 'total': total, 'page': page, 'page_size': page_size}


@router.get('/admin/users/{uid}')
async def customer_detail(uid: str, page: int = Query(1, ge=1), admin: User = Depends(current_admin)):
    async with session_scope() as s:
        user = await lock_user(s, uid, active=False)
        if user.role != 'customer': raise HTTPException(404, 'Pelanggan tidak ditemukan')
        wallet = await points.wallet_payload(s, user)
        data = {key: row_dict(user)[key] for key in ('user_id','name','email','phone','is_active','email_verified_at','referral_code','created_at')}
        orders = (await s.scalars(select(m.Order).where(m.Order.user_id == uid).order_by(m.Order.created_at.desc(), m.Order.id).offset((page-1)*20).limit(20))).all()
        total = await s.scalar(select(func.count()).select_from(m.Order).where(m.Order.user_id == uid))
        referrals = await s.scalar(select(func.count()).select_from(m.Referral).where(m.Referral.referrer_id == uid))
        return {'customer': data, 'wallet': wallet, 'referral_count': referrals,
            'orders': [await order_dict(s, row) for row in orders], 'orders_total': total, 'page': page}


@router.patch('/admin/users/{uid}')
async def update_customer(uid: str, req: CustomerEdit, admin: User = Depends(current_admin)):
    return await edit_customer(uid, req)
