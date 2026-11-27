"""Versioned, bounded collections for small storefront presentation settings."""
from copy import deepcopy
from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from database import session_scope
from mysql import models as m


@dataclass(frozen=True)
class ContentCollection:
    key: str
    defaults: list
    label: str
    limit: int = 50
    unique_fields: tuple[str, ...] = ()

    def value(self, row):
        value = deepcopy(row.value) if row else {'version': 0, 'items': deepcopy(self.defaults)}
        value['items'].sort(key=lambda item: (item['sort_order'], item['id']))
        return value

    async def read(self, session, public=False):
        value = self.value(await session.get(m.Setting, self.key))
        return [item for item in value['items'] if item['is_active']] if public else value

    async def mutate(self, user_id, version, *, item_id=None, body=None, remove=False):
        conflict = f'{self.label} sudah diubah. Tutup form dan muat ulang sebelum menyimpan.'
        try:
            async with session_scope() as session:
                row = await session.get(m.Setting, self.key, with_for_update=True)
                value = self.value(row)
                if value['version'] != version:
                    raise HTTPException(409, conflict)
                if item_id and not any(item['id'] == item_id for item in value['items']):
                    raise HTTPException(404, f'Item {self.label.lower()} tidak ditemukan')
                if remove:
                    value['items'] = [item for item in value['items'] if item['id'] != item_id]
                else:
                    if not item_id and len(value['items']) >= self.limit:
                        raise HTTPException(422, f'Maksimal {self.limit} item {self.label.lower()}. Hapus item yang tidak digunakan terlebih dahulu.')
                    item = {'id': item_id or uuid4().hex, **body.model_dump(exclude={'version'})}
                    for field in self.unique_fields:
                        if any(old['id'] != item_id and str(old.get(field, '')).casefold() == str(item.get(field, '')).casefold() for old in value['items']):
                            raise HTTPException(422, f'{field} sudah digunakan pada {self.label.lower()} lain')
                    value['items'] = [item if old['id'] == item_id else old for old in value['items']] if item_id else [*value['items'], item]
                value['version'] += 1
                value['items'].sort(key=lambda item: (item['sort_order'], item['id']))
                if row is None:
                    row = m.Setting(key=self.key, is_public=False)
                    session.add(row)
                row.value, row.updated_by, row.is_public = value, user_id, False
                await session.flush()
            return value
        except IntegrityError:
            raise HTTPException(409, conflict) from None
        except OperationalError as exc:
            if getattr(exc.orig, 'args', ()) and exc.orig.args[0] in (1205, 1213):
                raise HTTPException(409, conflict) from None
            raise
