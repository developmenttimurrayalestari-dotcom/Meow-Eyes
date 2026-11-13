from pathlib import Path

p=Path('models.py');t=p.read_text(encoding='utf-8');t=t.replace('import uuid\n','import uuid\nfrom mysql.taxonomy_definitions import GroupType\n',1)
t=t.replace('    parent_id: Optional[str] = None\n','').replace('    category_type: str = "product"  # product | frame | lens | package | promo','    group_type: GroupType = "collection"\n    code: Optional[str] = None').replace('    category_type: str = "product"','    group_type: GroupType = "collection"\n    code: Optional[str] = None').replace('    level: int = 0\n','')
t=t.replace('class CategoryCreate(BaseModel):\n','class CategoryCreate(BaseModel):\n    model_config = ConfigDict(extra="forbid")\n',1)
p.write_text(t,encoding='utf-8')

p=Path('mysql/catalog.py');t=p.read_text(encoding='utf-8');a=t.index('    if "category_ids" in payload or "primary_category_id" in payload:');b=t.index('    for field, model, column in (',a)
t=t[:a]+'''    if creating or any(key in payload for key in ('category_ids', 'primary_category_id', 'product_type', 'segments')):
        from .taxonomy import replace_product_tags
        if 'category_ids' in payload: payload['category_ids'] = strings(payload['category_ids'], max_length=64)
        if 'segments' in payload: payload['segments'] = strings(payload['segments'], max_length=64, unique=True)
        await replace_product_tags(session, product, payload)

'''+t[b:]
t=t.replace('        ("segments", m.ProductSegment, "segment"),\n','')
a=t.index('async def category_breadcrumb(');b=t.index('async def articles_dict(',a)
t=t[:a]+'''async def category_breadcrumb(session: AsyncSession, category_id: str | None) -> list[dict]:
    category = await session.get(m.Category, category_id) if category_id else None
    return [row_dict(category)] if category else []


'''+t[b:];p.write_text(t,encoding='utf-8')

p=Path('routes_catalog.py');t=p.read_text(encoding='utf-8').replace('banner_dict, category_breadcrumb, category_descendants,','banner_dict, category_breadcrumb,')
t=t.replace('from mysql.base import utcnow','from mysql.base import utcnow\nfrom mysql.taxonomy_definitions import GROUPS, GroupType\nfrom mysql.taxonomy import master_filter_conditions')
t=t.replace('async def list_categories(is_active: Optional[bool] = True):','async def list_categories(is_active: Optional[bool] = True, group_type: GroupType | None = None):')
t=t.replace('        stmt = select(m.Category)\n','        stmt = select(m.Category)\n        if group_type: stmt = stmt.where(m.Category.group_type == group_type)\n',1)
t=t.replace('return {"categories": [row_dict(row) for row in rows]}','return {"categories": [row_dict(row) for row in rows], "groups": list(GROUPS)}',1)
a=t.index('        by_id = {c.id:');b=t.index('\n\n@router.get("/categories/{slug}")',a)
t=t[:a]+'''        # Legacy URL retained as a flat alias; category ancestry no longer exists.
        return {"tree": [row_dict(row) for row in rows], "groups": list(GROUPS)}
'''+t[b:]
t=t.replace('    page: int = Query(1, ge=1), limit: int = Query(15, ge=1, le=100),','    page: int = Query(1, ge=1), limit: int = Query(15, ge=1, le=100),\n    category_ids: Optional[str] = None,')
t=t.replace('        if category_id:\n','        conditions.extend(await master_filter_conditions(s, category_ids))\n        if category_id:\n',1)
t=t.replace('ids = await category_descendants(s, category.id)','ids = {category.id}')
p.write_text(t,encoding='utf-8')

p=Path('routes_admin.py');t=p.read_text(encoding='utf-8');a=t.index('@router.get("/categories")');b=t.index('@router.get("/brands")',a)
t=t[:a]+'''@router.get("/categories")
async def admin_list_categories(group_type: str | None = None, admin: User = Depends(current_admin)):
    from mysql.taxonomy_definitions import GROUPS
    if group_type and group_type not in {group['key'] for group in GROUPS}: raise HTTPException(422, 'Grup master tidak dikenal')
    async with read_session() as s:
        query = select(m.Category)
        if group_type: query = query.where(m.Category.group_type == group_type)
        rows = (await s.scalars(query.order_by(m.Category.group_type, m.Category.sort_order, m.Category.name, m.Category.id))).all()
        return {'categories': [row_dict(row) for row in rows], 'groups': list(GROUPS)}

def _master_values(req):
    data = req.model_dump(); data['name'] = data['name'].strip()
    if not data['name']: raise HTTPException(422, 'Nama master wajib diisi')
    if data['group_type'] == 'gender' and len(data['name']) > 64: raise HTTPException(422, 'Nama Gender maksimal 64 karakter')
    data['code'] = data['code'] or slugify(data['name'])[:64]
    if len(data['code']) > 64 or not data['code'].strip(): raise HTTPException(422, 'Kode master tidak valid')
    if data['group_type'] == 'product_type' and data['code'] not in ('frame','lens','package'): raise HTTPException(422, 'Jenis Produk yang didukung: Frame, Lensa, Paket')
    return data

@router.post('/categories')
async def create_category(req: CategoryCreate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        data = _master_values(req)
        if await s.scalar(select(m.Category.id).where(m.Category.group_type == data['group_type'], m.Category.code == data['code'])): raise HTTPException(409, 'Master data sudah ada pada grup ini')
        data['slug'] = await unique_slug(s, m.Category, req.slug or data['group_type'].replace('_','-') + '-' + slugify(req.name))
        category = m.Category(id=m.new_id(), **safe_values(m.Category, data)); s.add(category); await s.flush()
        return {'ok': True, 'category': row_dict(category)}

@router.put('/categories/{cid}')
async def update_category(cid: str, req: CategoryCreate, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        category = await get_or_404(s, m.Category, cid, lock=True)
        data = _master_values(req.model_copy(update={'code': req.code or category.code}))
        if data['code'] != category.code or data['group_type'] != category.group_type: raise HTTPException(422, 'Grup dan kode master yang sudah dibuat tidak dapat diubah')
        data['slug'] = req.slug or category.slug
        apply_fields(category, data, set(CategoryCreate.model_fields)); await s.flush()
        return {'ok': True, 'category': row_dict(category)}

@router.delete('/categories/{cid}')
async def delete_category(cid: str, admin: User = Depends(current_admin)):
    async with session_scope() as s:
        category = await get_or_404(s, m.Category, cid, lock=True)
        used = await _count(s, m.ProductCategory, m.ProductCategory.category_id == cid) or await _count(s, m.Product, m.Product.primary_category_id == cid)
        used = used or await _count(s, m.FlashSaleCategory, m.FlashSaleCategory.category_id == cid) or await _count(s, m.FlashSaleItem, m.FlashSaleItem.source_category_id == cid)
        used = used or await _count(s, m.Banner, m.Banner.link_category_id == cid)
        if category.group_type == 'product_type': used = used or await _count(s, m.Product, m.Product.product_type == category.code)
        if used: raise HTTPException(409, 'Master data masih digunakan produk, promo, atau banner. Gunakan Nonaktifkan jika masih diperlukan sebagai riwayat.')
        await s.delete(category)
    return {'ok': True}


'''+t[b:];p.write_text(t,encoding='utf-8')

p=Path('mysql/features.py');t=p.read_text(encoding='utf-8').replace('category_descendants, safe_values','safe_values')
t=t.replace('descendants = raw.get("include_descendants", True)','descendants = raw.get("include_descendants", False)').replace('include_descendants=descendants,','include_descendants=False,')
t=t.replace('ids = await category_descendants(session, category.id) if rule["include_descendants"] else {category.id}','ids = {category.id}')
p.write_text(t,encoding='utf-8')

p=Path('mysql/feature_content.py');t=p.read_text(encoding='utf-8');a=t.index('        parent = await session.scalar(');b=t.index('    for product in new_products:',a)
t=t[:a]+'''        session.add(m.Category(id=m.new_id(), name="New Arrival Frame", slug="frame-new-arrival",
            group_type='collection', code='new-arrival', sort_order=0, is_featured=True, is_active=True,
            description="Frame terbaru yang ditandai New Arrival. Daftar mengikuti status dan periode produk."))
'''+t[b:];p.write_text(t,encoding='utf-8')

p=Path('mysql/importer.py');t=p.read_text(encoding='utf-8').replace('EXTRA_FIELDS = {','EXTRA_FIELDS = {\n    "categories": {"parent_id", "level", "category_type"},',1)
t=t.replace('        inherited_time = doc.get("created_at", doc.get("updated_at"))','        inherited_time = doc.get("created_at", doc.get("updated_at"))\n        if collection == "categories":\n            data.setdefault("group_type", "collection")\n            data["code"] = data.get("code") or "legacy-" + checksum(doc.get("id"))[:32]',1)
t=t.replace('        self._category_cycles()\n','')
a=t.index('        category_depths = self._category_depths()');b=t.index('        self._unique_keys()',a)
t=t[:a]+'''        plan.rows.sort(key=lambda r: (ranks[r.table], r.key_text))
'''+t[b:];a=t.index('    def _category_depths(');b=t.index('    def _unique_keys(',a);t=t[:a]+t[b:];p.write_text(t,encoding='utf-8')

p=Path('mysql/demo_seed.py');t=p.read_text(encoding='utf-8');t=t.replace('            parents = {v["id"]: v for v in docs["categories"]}\n','')
t=t.replace('id=identity, parent_id=parent, name=name, slug=slug,\n                 category_type=kind, level=parents[parent]["level"] + 1 if parent else 0,','id=identity, name=name, slug=slug,\n                 group_type="product_type" if not parent and kind in ("frame", "lens", "package") else "collection",\n                 code=kind if not parent and kind in ("frame", "lens", "package") else slug,')
p.write_text(t,encoding='utf-8')
