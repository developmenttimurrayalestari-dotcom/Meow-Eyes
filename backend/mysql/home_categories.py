"""Small, versioned homepage card collection, independent of catalog taxonomy."""
from copy import deepcopy
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError

from database import session_scope
from mysql import models as m

KEY = 'homepage.category_cards'
LIMIT = 50
DEFAULTS = [
    dict(id='home-frame', title='Frame', description='Stylish & premium', link_url='/category/frame', icon='frame', theme='coral', sort_order=0, is_active=True, background_image=''),
    dict(id='home-lens', title='Lensa', description='Blue Cut, Photochromic', link_url='/category/lensa', icon='lens', theme='amber', sort_order=1, is_active=True, background_image=''),
    dict(id='home-package', title='Paket Hemat', description='Frame + Lensa', link_url='/category/paket-frame-lensa', icon='package', theme='mint', sort_order=2, is_active=True, background_image=''),
    dict(id='home-leinz', title='Leinz Series', description='Best of 2026', link_url='/category/leinz', icon='sparkles', theme='midnight', sort_order=3, is_active=True, background_image=''),
]


def safe_url(value):
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise ValueError('URL tidak valid') from None
    if value.startswith('//') or '\\' in value or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError('URL harus path internal atau URL HTTP/HTTPS yang valid')
    if not value.startswith('/') and (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or parsed.password is not None):
        raise ValueError('URL harus path internal atau URL HTTP/HTTPS yang valid')
    return value


class CardInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    version: int = Field(ge=0)
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default='', max_length=180)
    link_url: str = Field(min_length=1, max_length=2048)
    background_image: str = Field(default='', max_length=2048)
    icon: Literal['frame', 'lens', 'package', 'sparkles', 'tag'] = 'frame'
    theme: Literal['coral', 'amber', 'mint', 'midnight'] = 'coral'
    sort_order: int = Field(default=0, ge=0, le=9999)
    is_active: bool = True

    @field_validator('link_url')
    @classmethod
    def validate_link(cls, value):
        return safe_url(value)

    @field_validator('background_image')
    @classmethod
    def validate_image(cls, value):
        return safe_url(value) if value else value


def collection(row):
    value = deepcopy(row.value) if row else {'version': 0, 'items': deepcopy(DEFAULTS)}
    value['items'].sort(key=lambda item: (item['sort_order'], item['id']))
    return value


async def cards(session, public=False):
    value = collection(await session.get(m.Setting, KEY))
    if public:
        return [item for item in value['items'] if item['is_active']]
    return value


async def mutate(user_id, version, *, card_id=None, body=None, remove=False):
    try:
        async with session_scope() as session:
            row = await session.get(m.Setting, KEY, with_for_update=True)
            value = collection(row)
            if value['version'] != version:
                raise HTTPException(409, 'Kategori pilihan sudah diubah. Tutup form dan muat ulang sebelum menyimpan.')
            existing = next((item for item in value['items'] if item['id'] == card_id), None) if card_id else None
            if card_id and existing is None:
                raise HTTPException(404, 'Card kategori pilihan tidak ditemukan')
            if remove:
                value['items'] = [item for item in value['items'] if item['id'] != card_id]
            else:
                if not card_id and len(value['items']) >= LIMIT:
                    raise HTTPException(422, 'Maksimal 50 card kategori pilihan. Hapus card yang tidak digunakan terlebih dahulu.')
                item = {'id': card_id or uuid4().hex, **body.model_dump(exclude={'version'})}
                value['items'] = [item if old['id'] == card_id else old for old in value['items']] if card_id else [*value['items'], item]
            value['version'] += 1
            value['items'].sort(key=lambda item: (item['sort_order'], item['id']))
            if row is None:
                row = m.Setting(key=KEY, is_public=False)
                session.add(row)
            row.value, row.updated_by, row.is_public = value, user_id, False
            await session.flush()
        return value
    except IntegrityError:
        raise HTTPException(409, 'Kategori pilihan sudah diubah. Muat ulang lalu coba lagi.') from None
