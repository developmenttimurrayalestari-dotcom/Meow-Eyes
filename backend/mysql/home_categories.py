"""Small, versioned homepage card collection, independent of catalog taxonomy."""
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mysql.content_collections import ContentCollection

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


STORE = ContentCollection(KEY, DEFAULTS, 'Kategori pilihan', LIMIT)


async def cards(session, public=False):
    return await STORE.read(session, public=public)


async def mutate(user_id, version, *, card_id=None, body=None, remove=False):
    return await STORE.mutate(user_id, version, item_id=card_id, body=body, remove=remove)
