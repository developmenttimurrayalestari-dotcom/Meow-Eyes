"""Read-only TRL region/token tables, using the application's MySQL account.

No external table is declared in app metadata, migrated, seeded or updated.
Only the configured getToken service owns refresh writes to the shared table.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import base64
import json
import re
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import read_session
from integrations.common import ProviderError, strict_json


def normalize_token(value):
    if not isinstance(value, str): return None
    value = value.strip()
    if value.lower() == 'bearer': return None
    if value[:7].lower() == 'bearer ': value = value[7:].strip()
    if not value or len(value) > 16384 or not re.fullmatch(r'[A-Za-z0-9._~+/=-]+', value): return None
    return value


@dataclass(frozen=True)
class SharedToken:
    value: str = field(repr=False)
    expires_at: datetime | None = None

    def remaining(self, now=None):
        if self.expires_at is None: return 30.0
        return (self.expires_at - (now or datetime.now(timezone.utc))).total_seconds()


def jwt_expiry(value):
    """Expiry is only a refresh hint; Everpro still authenticates the bearer."""
    try:
        segment = value.split('.')[1]
        payload = json.loads(base64.urlsafe_b64decode(segment + '=' * (-len(segment) % 4)))
        timestamp = payload.get('exp')
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)): return None
        return datetime.fromtimestamp(timestamp, timezone.utc)
    except (ValueError, TypeError, IndexError, AttributeError, OverflowError, OSError): return None


class EverproReferenceStore:
    def __init__(self, settings, *, session_factory=read_session):
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', settings.reference_database):
            raise ProviderError('everpro', 'reference_configuration_invalid', 503)
        self.master = f'`{settings.reference_database}`.`apieverpro_master`'
        self.keys = f'`{settings.reference_database}`.`apieverpro_key`'
        self.settings, self.session_factory = settings, session_factory

    async def _rows(self, statement, parameters=None):
        try:
            async with self.session_factory() as session:
                return [dict(row) for row in (await session.execute(text(statement), parameters or {})).mappings()]
        except SQLAlchemyError:
            raise ProviderError('everpro', 'reference_database_unavailable', 503) from None

    async def regions(self, level, parent_id=None):
        groups = {'provinces':'province', 'cities':'city', 'districts':'district', 'subdistricts':'sub_district'}
        if level not in groups: raise ValueError('Unknown location level')
        parameters, predicates = {}, []
        if level != 'provinces':
            if not isinstance(parent_id, str) or not parent_id.isascii() or not parent_id.isdigit() or len(parent_id) > 20:
                return []
            parent = await self._rows(f'SELECT province,city,district FROM {self.master} WHERE id=:id', {'id':int(parent_id)})
            if not parent: return []
            count = {'cities':1, 'districts':2, 'subdistricts':3}[level]
            for column in ('province','city','district')[:count]:
                predicates.append(f'`{column}`=:{column}')
                parameters[column] = parent[0][column]
        column = groups[level]
        predicates.append(f"`{column}` IS NOT NULL AND TRIM(`{column}`)<>''")
        where = ' AND '.join(predicates)
        if level == 'subdistricts':
            sql = f'SELECT id,sub_district AS name,post_code AS postal_code FROM {self.master} WHERE {where} ORDER BY sub_district,id'
        else:
            sql = f'SELECT MIN(id) AS id,`{column}` AS name FROM {self.master} WHERE {where} GROUP BY `{column}` ORDER BY `{column}`'
        rows = await self._rows(sql, parameters)
        result = []
        for row in rows:
            item = {'id':str(row['id']), 'name':str(row['name']).strip()}
            if level == 'subdistricts':
                postal = str(row['postal_code'] or '').strip()
                if not re.fullmatch(r'[0-9]{5}', postal):
                    raise ProviderError('everpro', 'invalid_locations_response', 503)
                item['postal_code'] = postal
            result.append(item)
        return result

    async def locations(self, postal_code):
        if not isinstance(postal_code, str) or not re.fullmatch(r'[0-9]{5}', postal_code):
            return {'data':[]}
        rows = await self._rows(f'''SELECT id AS sub_district_id,province AS province_name,city AS city_name,
            district AS district_name,sub_district AS sub_district_name,post_code AS postal_code
            FROM {self.master} WHERE post_code=:postal ORDER BY id''', {'postal':postal_code})
        return {'data':rows}

    async def token(self):
        rows = await self._rows(f'''SELECT security_key,expired,datetime_updatekey FROM {self.keys}
            WHERE LOWER(TRIM(type_key))='bearer' ORDER BY datetime_updatekey DESC,id_key DESC LIMIT 1''')
        if not rows: return None
        row = rows[0]
        token = normalize_token(row['security_key'])
        if not token: return None
        expiries = []
        expiry = jwt_expiry(token)
        if expiry: expiries.append(expiry)
        try:
            updated = row['datetime_updatekey']
            if isinstance(updated, str): updated = datetime.fromisoformat(updated)
            if updated.tzinfo is None: updated = updated.replace(tzinfo=ZoneInfo(self.settings.token_timezone))
            seconds = int(row['expired'])
            if seconds > 0: expiries.append(updated.astimezone(timezone.utc) + timedelta(seconds=seconds))
        except (ValueError, TypeError, AttributeError, OverflowError): pass
        return SharedToken(token, min(expiries) if expiries else None)


async def refresh_shared_token(settings, *, transport=None):
    """Call the user-supplied GET endpoint, not Everpro /auth directly."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5), transport=transport,
                                     follow_redirects=True, max_redirects=3) as client:
            response = await client.get(settings.token_refresh_url, headers={'Accept':'application/json'})
        if response.status_code != 200 or len(response.content) > 100_000:
            raise ProviderError('everpro', 'token_refresh_failed', 503)
        body = strict_json(response.content)
        if body.get('status') is not True:
            raise ProviderError('everpro', 'token_refresh_failed', 503)
        token = normalize_token(body.get('token'))
        if not token: raise ProviderError('everpro', 'invalid_shared_token', 503)
        return SharedToken(token, jwt_expiry(token))
    except httpx.HTTPError:
        raise ProviderError('everpro', 'token_refresh_unavailable', 503) from None
    except (ValueError, UnicodeError):
        raise ProviderError('everpro', 'invalid_shared_token', 503) from None
