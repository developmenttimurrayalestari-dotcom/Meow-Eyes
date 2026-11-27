"""Tinting master configuration, server pricing and immutable order snapshots."""
from copy import deepcopy
import json
from pathlib import Path
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator
from sqlalchemy import select
from . import models as m
from .content_collections import ContentCollection

KEY = 'catalog.tinting'
DEFAULTS = json.loads((Path(__file__).resolve().parents[1] / 'data/tinting-catalog.json').read_text(encoding='utf-8'))['items']
STORE = ContentCollection(KEY, DEFAULTS, 'Warna tinting', 300, unique_fields=('code',))
PRODUCT_TYPES = {'frame', 'lens', 'package'}


class TintingInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    version: int = Field(ge=0)
    code: str = Field(min_length=1, max_length=32, pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1, max_length=120)
    kind: Literal['solid', 'gradient'] = 'solid'
    group: Literal['fashion', 'sunglass', 'therapeutic', 'special'] = 'fashion'
    hex_color: str | None = None
    mid_hex_color: str | None = None
    bottom_hex_color: str | None = None
    additional_price: StrictInt = Field(ge=0, le=1_000_000_000)
    is_active: bool = True
    requires_sample: bool = False
    source_note: str = Field(default='', max_length=2000)
    sort_order: int = Field(default=0, ge=0, le=9999)

    @field_validator('code')
    @classmethod
    def uppercase_code(cls, value):
        return value.upper()

    @field_validator('hex_color', 'mid_hex_color', 'bottom_hex_color')
    @classmethod
    def valid_hex(cls, value):
        import re
        if not value: return None
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
            raise ValueError('Gunakan HEX #RRGGBB, misalnya #A1B2C3')
        return value.upper()

    @model_validator(mode='after')
    def active_color(self):
        if self.is_active and (not self.hex_color or self.kind == 'gradient' and not self.bottom_hex_color):
            raise ValueError('Lengkapi warna HEX sebelum mengaktifkan tinting')
        if self.is_active and self.requires_sample:
            raise ValueError('Warna yang memerlukan sampel fisik belum dapat dijual melalui checkout')
        return self


class TintingSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tinting_id: str | None = Field(default=None, min_length=1, max_length=64)


async def catalog(session, *, lock=False):
    row = await session.get(m.Setting, KEY, with_for_update=lock, populate_existing=True)
    return STORE.value(row)


def eligible(product):
    return product.product_type in PRODUCT_TYPES and product.sale_role == 'main'


def snapshot(item):
    return {key: deepcopy(item.get(key)) for key in (
        'id', 'code', 'name', 'kind', 'group', 'hex_color', 'mid_hex_color',
        'bottom_hex_color', 'additional_price')}


async def cart_tintings(session, carts, *, lock=False):
    rows = (await session.scalars(select(m.CartTinting).where(
        m.CartTinting.cart_item_id.in_([cart.id for cart in carts])))).all()
    value = await catalog(session, lock=lock) if rows else {'items':[]}
    colors = {item['id']:item for item in value['items']}
    result = {}
    for row in rows:
        color = colors.get(row.tinting_id)
        available = bool(color and color['is_active'] and not color['requires_sample'] and color['hex_color'])
        # Keep a removed/disabled choice visible in the cart so it can be
        # replaced or removed, but reject it at strict checkout validation.
        result[row.cart_item_id] = {**(snapshot(color) if color else row.details), 'is_available':available}
    return result
