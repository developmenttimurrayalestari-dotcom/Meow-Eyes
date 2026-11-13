from pathlib import Path

p=Path('mysql/database.py');t=p.read_text(encoding='utf-8').replace('EXPECTED_SCHEMA_REVISION = "20261111_0005"','EXPECTED_SCHEMA_REVISION = "20261111_0006"');p.write_text(t,encoding='utf-8')
p=Path('mysql/check_integrity.py');t=p.read_text(encoding='utf-8');anchor='async def audit(*, preflight_only: bool = False) -> dict:'
t=t.replace(anchor,'''def load_flat_master_revision():
    path = Path(__file__).resolve().parents[1] / 'migrations/versions/20261111_0006_flat_product_masters.py'
    spec = importlib.util.spec_from_file_location('_meow_flat_masters', path)
    revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
    return revision

'''+anchor)
anchor='            issues = []\n            for revision in revisions:'
t=t.replace(anchor,'''            installed = []
            if await connection.run_sync(lambda conn: inspect(conn).has_table('alembic_version')):
                installed = (await connection.execute(text('SELECT version_num FROM alembic_version'))).scalars().all()
            if installed == ['20261111_0006']:
                # 0006 replaces the historical category predicates/guards only.
                revisions[0].RULES = {key: value for key,value in revisions[0].RULES.items() if key != 'categories'}
                revisions.append(load_flat_master_revision())
            issues = []
            if not preflight_only and installed != ['20261111_0006']: issues.append('schema_revision_mismatch')
            for revision in revisions:''')
p.write_text(t,encoding='utf-8')

p=Path('tests_mysql/commerce_scenarios.py');t=p.read_text(encoding='utf-8').replace('    async with session_scope() as s:\n        for key in ("alice",','    async with session_scope() as s:\n        from mysql.taxonomy import seed_masters\n        await seed_masters(s)\n        for key in ("alice",',1);p.write_text(t,encoding='utf-8')
p=Path('tests_mysql/test_catalog_sql.py');t=p.read_text(encoding='utf-8').replace('        async with factory.begin() as s:\n            s.add(m.User','        async with factory.begin() as s:\n            from mysql.taxonomy import seed_masters\n            await seed_masters(s)\n            s.add(m.User',1)
t=t.replace('slug="frames", level=0','slug="frames"').replace('parent_id="cat", name="Round", slug="round", level=1','group_type="frame_shape", code="legacy-round", name="Round", slug="round"')
t=t.replace('m.ProductCategory(product_id="product", category_id="child"),','m.ProductCategory(product_id="product", category_id="child"), m.ProductCategory(product_id="product", category_id="cat"),',1)
t=t.replace('== ["cat", "child"]','== ["child"]')
t=t.replace('assert (await s.get(m.Category, "cat")).parent_id is None','assert (await s.get(m.Category, "cat")).group_type == "collection"').replace('assert (await s.get(m.Category, "child")).level == 1','assert (await s.get(m.Category, "child")).group_type == "frame_shape"')
t=t.replace('json={"name": "New", "parent_id": "child"}','json={"name": "New", "group_type": "collection"}').replace('assert created.json()["category"]["level"] == 2','assert created.json()["category"]["group_type"] == "collection"\n            assert "parent_id" not in created.json()["category"]')
p.write_text(t,encoding='utf-8')
p=Path('tests_mysql/test_optical_features.py');t=p.read_text(encoding='utf-8').replace('slug="frames", level=0','slug="frames"').replace('slug="round", parent_id="root_frames", level=1','slug="round"')
t=t.replace('s.add(m.ProductCategory(product_id=d["frame"], category_id="child_frames"))','s.add(m.ProductCategory(product_id=d["frame"], category_id="child_frames"))\n        s.add(m.ProductCategory(product_id=d["frame"], category_id="root_frames"))')
p.write_text(t,encoding='utf-8')
p=Path('tests_mysql/test_importer.py');t=p.read_text(encoding='utf-8').replace('    (lambda d: d["categories"][0].update(parent_id="cat-child"), "category_cycle"),\n','');p.write_text(t,encoding='utf-8')
p=Path('tests_mysql/test_migrations.py');t=p.read_text(encoding='utf-8').replace('generated = offline("upgrade", "head", "--sql")','generated = offline("upgrade", "20261111_0005", "--sql")',1)
t=t.replace('assert f"version_num=\'{EXPECTED_SCHEMA_REVISION}\'" in generated','assert "version_num=\'20261111_0005\'" in generated',1)
t=t.replace('    for table in Base.metadata.sorted_tables:\n        ddl =','    for table in Base.metadata.sorted_tables:\n        if table.name == "categories": continue  # 0006 requires online row mapping before ALTER.\n        ddl =',1)
p.write_text(t,encoding='utf-8')
p=Path('tests_mysql/test_mysql57_guards.py');t=p.read_text(encoding='utf-8').replace('if table.name in revision.ALL_TABLES for check','if table.name in revision.ALL_TABLES and table.name != "categories" for check',1)
t=t.replace('    for table, rules in revision.RULES.items():\n        columns =','    for table, rules in revision.RULES.items():\n        if table == "categories": continue  # Replaced by frozen 0006 guards.\n        columns =',1).replace('assert len(actual) == 97','assert len(actual) == 95',1)
p.write_text(t,encoding='utf-8')
p=Path('tests_mysql/test_meowsurement_schema.py');t=p.read_text(encoding='utf-8').replace('load_revision, load_loyalty_revision','load_revision, load_loyalty_revision, load_flat_master_revision')
t=t.replace('    for revision in (old, new, loyalty):','    old.RULES = {key:value for key,value in old.RULES.items() if key != "categories"}\n    for revision in (old, new, loyalty, load_flat_master_revision()):',1)
p.write_text(t,encoding='utf-8')
