"""Private dispatch address, with legacy env fallback until first admin save."""
from dataclasses import replace
import os
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from mysql import models as m

KEY = 'shipping.origin'
MAPPING = {'name':'shipper_name', 'phone':'shipper_phone', 'address':'shipper_address', 'email':'shipper_email',
           'postal_code':'origin_postal_code', 'subdistrict':'origin_subdistrict', 'latitude':'origin_latitude', 'longitude':'origin_longitude'}
ENV = {'name':'EVERPRO_SHIPPER_NAME', 'phone':'EVERPRO_SHIPPER_PHONE', 'address':'EVERPRO_SHIPPER_ADDRESS', 'email':'EVERPRO_SHIPPER_EMAIL',
       'postal_code':'EVERPRO_ORIGIN_POSTAL_CODE', 'subdistrict':'EVERPRO_ORIGIN_SUBDISTRICT', 'latitude':'EVERPRO_ORIGIN_LATITUDE', 'longitude':'EVERPRO_ORIGIN_LONGITUDE'}

class OriginInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    version: int = Field(default=0, ge=0)
    name: str = Field(min_length=3, max_length=100)
    phone: str = Field(pattern=r'^(?:\+?62|08)\d{8,12}$', max_length=15)
    address: str = Field(min_length=3, max_length=250)
    email: str = Field(default='', max_length=254)
    province_id: str = Field(min_length=1, max_length=128)
    city_id: str = Field(min_length=1, max_length=128)
    district_id: str = Field(min_length=1, max_length=128)
    subdistrict_id: str = Field(min_length=1, max_length=128)
    province: str = ''
    city: str = ''
    district: str = ''
    subdistrict: str = ''
    postal_code: str = ''
    everpro_destination_id: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)

    @model_validator(mode='after')
    def validate_contact(self):
        import re
        if self.email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', self.email):
            raise ValueError('Email pengirim tidak valid')
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError('Isi latitude dan longitude bersama-sama')
        return self

async def origin_data(session):
    row = await session.get(m.Setting, KEY)
    if row:
        return {'origin':row.value, 'source':'admin'}
    origin = {key:os.getenv(env, '') for key,env in ENV.items()}
    for field in ('latitude','longitude'):
        try: origin[field] = float(origin[field]) if origin[field] else None
        except ValueError: origin[field] = None
    return {'origin':{**origin, 'version':0}, 'source':'env' if origin['address'] else 'unconfigured'}

async def effective_shipping_settings(session, settings):
    row = await session.get(m.Setting, KEY, populate_existing=True)
    if row:
        return replace(settings, **{field:row.value.get(key) for key,field in MAPPING.items()})
    # Keep existing shops operational until superadmin saves the address once.
    from integrations.config import EverproSettings
    legacy = EverproSettings.from_env()
    return replace(settings, **{field:getattr(legacy,field) for field in MAPPING.values()})
