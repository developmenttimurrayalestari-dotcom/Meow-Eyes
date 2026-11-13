"""Flatten product masters and backfill explicit many-to-many assignments.

Online data migration: ancestry is read once before dropping its columns.
Back up and pause application writers before running; MySQL DDL commits.
"""
import hashlib
import json
import re
from datetime import datetime
from alembic import context, op
import sqlalchemy as sa

revision = '20261111_0006'
down_revision = '20261111_0005'
branch_labels = depends_on = None
ALL_TABLES = ('categories',)
INITIAL_MASTERS = (
 ('product_type','frame','Frame'),('product_type','lens','Lensa'),('product_type','package','Paket'),
 ('lens_type','single-vision','Single Vision'),('lens_type','bifocal','Bifocal'),('lens_type','progressive','Progresif'),('lens_type','uv420','Anti Radiasi (UV420)'),('lens_type','photochromic','Photochromic'),
 ('gender','pria','Pria'),('gender','wanita','Wanita'),('gender','anak-anak','Anak-anak'),('gender','unisex','Unisex'),
 ('frame_shape','aviator','Aviator'),('frame_shape','cat-eye','Cat Eye'),('frame_shape','geometric','Geometris'),('frame_shape','rectangle','Rectangle'),('frame_shape','rimless','Rimless'),('frame_shape','round','Round'),('frame_shape','square','Square'),('frame_shape','oval','Oval'),
 ('material','acetate','Acetate'),('material','titanium','Titanium'),('material','metal','Metal'),
)
RULES = {'categories': (
 ('ck_categories_group_type', "group_type IN ('product_type','lens_type','gender','frame_shape','material','collection')", "NEW.group_type IN ('product_type','lens_type','gender','frame_shape','material','collection')"),
 ('ck_categories_product_kind', "group_type <> 'product_type' OR code IN ('frame','lens','package')", "NEW.group_type <> 'product_type' OR NEW.code IN ('frame','lens','package')"),
)}
EXPECTED_SQL_MODES = {'STRICT_TRANS_TABLES','ERROR_FOR_DIVISION_BY_ZERO','NO_ENGINE_SUBSTITUTION','ONLY_FULL_GROUP_BY','NO_ZERO_DATE','NO_ZERO_IN_DATE'}

def normalize(value): return re.sub('[^a-z0-9]', '', str(value or '').lower())
def identity(group, code): return 'catm_' + hashlib.sha256((group + ':' + code).encode()).hexdigest()[:32]
def quoted(name): return '`' + name.replace('`','``') + '`'

def plan_rows(categories, products, links, segments, variants=()):
    """Pure deterministic mapping, also exercised with archived source fixtures."""
    by_id = {row['id']: dict(row) for row in categories}
    labels = {(group,code):name for group,code,name in INITIAL_MASTERS}
    aliases = {normalize(name):(group,code) for group,code,name in INITIAL_MASTERS}
    for alias,group,code in (
      ('Frames','product_type','frame'),('Lens','product_type','lens'),('Paket Frame + Lensa','product_type','package'),
      ('Package','product_type','package'),('Bifokal','lens_type','bifocal'),('Progressive','lens_type','progressive'),
      ('Anti Radiasi UV 420','lens_type','uv420'),('Geometric','frame_shape','geometric'),('Geometri','frame_shape','geometric'),
      ('Pria','gender','pria'),('Anak','gender','anak-anak')):
        aliases[normalize(alias)] = (group,code)
    aliases[normalize('Anti Radiasi (Blue Cut)')] = ('lens_type','blue-cut')
    aliases['bluecut'] = ('lens_type','blue-cut')
    paths = {}
    for category_id in by_id:
        path, cursor = [], category_id
        while cursor:
            if cursor in path or cursor not in by_id: raise RuntimeError('Legacy category ancestry is invalid; repair before upgrading')
            path.append(cursor); cursor = by_id[cursor].get('parent_id')
        paths[category_id] = path
    masters, mapping, used_slugs = [], {}, {row['slug'] for row in categories}
    for original in sorted(categories,key=lambda row:row['id']):
        row = dict(original); candidate = aliases.get(normalize(row['name']))
        # A leaf such as Round -> Pria remains a named collection for old URLs
        # and flash-sale scopes; the independent Gender master is added below.
        if candidate and candidate[0] in ('gender','product_type') and row.get('parent_id'): candidate = None
        if not candidate and normalize(row['name']) not in ('pria','wanita','anak','anakanak','unisex') and row.get('category_type') == 'lens' and row.get('parent_id'):
            candidate = ('lens_type', re.sub('[^a-z0-9]+','-',row['name'].lower()).strip('-')[:64])
        if candidate and candidate not in mapping:
            row['group_type'],row['code'] = candidate
            row['name'] = labels.get(candidate, row['name']); mapping[candidate] = row['id']
        else:
            row['group_type'],row['code'] = 'collection','legacy-' + hashlib.sha256(row['id'].encode()).hexdigest()[:32]
            if normalize(row['name']) in ('pria','wanita','anak','anakanak','unisex') and row.get('parent_id'):
                ancestors = [by_id[cid]['name'] for cid in reversed(paths[row['id']][1:]) if normalize(by_id[cid]['name']) not in ('frame','frames','lensa','lens','paketframelensa')]
                row['name'] = (' · '.join(ancestors + [row['name']]))[:255]
        masters.append(row)
    for order,(group,code,name) in enumerate(INITIAL_MASTERS):
        if (group,code) in mapping: continue
        category_id = identity(group,code)
        if category_id in by_id: raise RuntimeError('Generated master identity overlaps an existing category')
        slug = group.replace('_','-') + '-' + code
        if slug in used_slugs: slug += '-' + category_id[-8:]
        used_slugs.add(slug);mapping[(group,code)] = category_id
        masters.append({'id':category_id,'group_type':group,'code':code,'name':name,'slug':slug,'sort_order':order,'is_active':True,'is_featured':False})
    wanted = set(tuple(row) for row in links)
    for product_id,category_id in list(wanted):
        if category_id not in paths: raise RuntimeError('Product references an unknown category')
        wanted.update((product_id,ancestor) for ancestor in paths[category_id])
    for product in products:
        pid,kind = product['id'],product['product_type']
        wanted.add((pid,mapping[('product_type',kind)]))
        primary = product.get('primary_category_id')
        if primary:
            if primary not in paths: raise RuntimeError('Primary category is missing')
            wanted.update((pid,ancestor) for ancestor in paths[primary])
        spec = product.get('spec') or {}
        if isinstance(spec,str): spec = json.loads(spec)
        if isinstance(spec,dict):
            for key,value in spec.items():
                target = 'material' if normalize(key) in ('material','bahan','framematerial') and kind in ('frame','package') else 'frame_shape' if normalize(key) in ('frameshape','shape','bentukframe') else None
                match = aliases.get(normalize(value)) if isinstance(value,str) else None
                if target and match and match[0] == target and match in mapping: wanted.add((pid,mapping[match]))
    for pid,segment in segments:
        match = aliases.get(normalize(segment))
        if match and match[0] == 'gender': wanted.add((pid,mapping[match]))
    for pid,lens_type in variants:
        match = aliases.get(normalize(lens_type))
        if match and match[0] == 'lens_type' and match in mapping: wanted.add((pid,mapping[match]))
    # Repeated old leaves/shapes also receive their independent canonical tag.
    # Keeping the old leaf ID preserves URLs and narrow promotion scopes.
    for pid,cid in list(wanted):
        if cid not in by_id: continue
        match = aliases.get(normalize(by_id[cid]['name']))
        if match and match[0] != 'product_type' and match in mapping:
            wanted.add((pid,mapping[match]))
    return {'masters':masters,'links':sorted(wanted),'initial_ids':{group+':'+code:mapping[(group,code)] for group,code,_ in INITIAL_MASTERS}}

def trigger_definitions():
    result = {}
    for event,prefix in (('INSERT','bi'),('UPDATE','bu')):
        name=prefix+'_categories_mysql57_guard'; lines=[]
        for rule,_,predicate in RULES['categories']:
            lines.append("IF ("+predicate+") IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule "+rule+" failed'; END IF;")
        if event=='UPDATE': lines.append("IF NOT (NEW.group_type <=> OLD.group_type) OR NOT (NEW.code <=> OLD.code) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Master group and code are immutable'; END IF;")
        body='BEGIN\n  '+'\n  '.join(lines)+'\nEND'
        result[name]={'table':'categories','event':event,'timing':'BEFORE','body':body,'sql':'CREATE TRIGGER '+quoted(name)+' BEFORE '+event+' ON categories FOR EACH ROW '+body}
    return result

def canonical_body(value):
    tokens=re.findall(r"'(?:''|[^'])*'|`(?:``|[^`])*`|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|[^\s]",value)
    return tuple(token if token.startswith("'") else token.strip('`').lower() for token in tokens)

def table_issues(connection):
    inspector=sa.inspect(connection)
    if not inspector.has_table('categories'): return ['missing_table:categories']
    columns={column['name']:column for column in inspector.get_columns('categories')}; issues=[]
    if not {'group_type','code'}<=set(columns): issues.append('flat_master_columns_missing')
    if {'parent_id','level','category_type'}&set(columns): issues.append('category_hierarchy_columns_remain')
    if 'code' in columns and columns['code']['nullable']: issues.append('master_code_must_be_not_null')
    if 'uq_categories_group_type_code' not in {item['name'] for item in inspector.get_unique_constraints('categories')}: issues.append('master_group_code_unique_missing')
    if any(item['referred_table']=='categories' for item in inspector.get_foreign_keys('categories')): issues.append('category_self_reference_remains')
    return issues

def row_issues(connection):
    where=' OR '.join('('+predicate+') IS FALSE' for _,predicate,_ in RULES['categories'])
    return ['flat_master_row_rule_violation'] if connection.exec_driver_sql('SELECT 1 FROM categories WHERE '+where+' LIMIT 1').first() else []

def trigger_issues(connection):
    rows=connection.execute(sa.text('SELECT TRIGGER_NAME AS name,EVENT_OBJECT_TABLE AS table_name,EVENT_MANIPULATION AS event,ACTION_TIMING AS timing,ACTION_STATEMENT AS body,SQL_MODE AS sql_mode FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()')).mappings()
    actual={row['name']:row for row in rows};issues=[]
    for name,expected in trigger_definitions().items():
        row=actual.get(name)
        if not row: issues.append('missing_trigger:'+name);continue
        if row['table_name']!='categories' or row['timing']!='BEFORE' or row['event']!=expected['event'] or canonical_body(row['body'])!=canonical_body(expected['body']): issues.append('trigger_definition_mismatch:'+name)
        if set(row['sql_mode'].split(','))!=EXPECTED_SQL_MODES: issues.append('trigger_sql_mode_mismatch:'+name)
    return issues

def upgrade():
    if context.is_offline_mode(): raise RuntimeError('0006 requires an online data mapping. Use a full backup, pause writers, then run alembic upgrade head against MySQL.')
    connection=op.get_bind(); inspector=sa.inspect(connection)
    columns={column['name'] for column in inspector.get_columns('categories')}
    if not {'parent_id','level','category_type'}<=columns or {'group_type','code'}&columns: raise RuntimeError('Unexpected or partial category schema; review before retry')
    categories=[dict(row) for row in connection.execute(sa.text('SELECT * FROM categories ORDER BY id')).mappings()]
    products=[dict(row) for row in connection.execute(sa.text('SELECT id,product_type,primary_category_id,spec FROM products')).mappings()]
    links=list(connection.execute(sa.text('SELECT product_id,category_id FROM product_categories')).all())
    segments=list(connection.execute(sa.text('SELECT product_id,segment FROM product_segments')).all())
    variants=list(connection.execute(sa.text('SELECT product_id,lens_type FROM product_variants WHERE lens_type IS NOT NULL')).all())
    plan=plan_rows(categories,products,links,segments,variants)
    old_ids={row['id'] for row in categories}; original_links=set(tuple(row) for row in links)
    if not original_links<=set(plan['links']): raise RuntimeError('Existing product assignments would be lost')
    archive=json.dumps({'revision':revision,'categories':categories,'initial_ids':plan['initial_ids'],'before_links':len(links),'after_links':len(plan['links'])},default=str)
    connection.execute(sa.text("INSERT INTO settings(`key`,value,description,is_public,updated_at) VALUES('taxonomy-0006-archive',:value,'Original category mapping before flat master migration',0,UTC_TIMESTAMP(6))"),{'value':archive})
    connection.exec_driver_sql("ALTER TABLE categories ADD COLUMN group_type VARCHAR(32) NOT NULL DEFAULT 'collection', ADD COLUMN code VARCHAR(64) NULL")
    for row in plan['masters']:
        if row['id'] in old_ids:
            connection.execute(sa.text('UPDATE categories SET group_type=:group_type,code=:code,name=:name WHERE id=:id'),{key:row[key] for key in ('id','group_type','code','name')})
        else:
            connection.execute(sa.text('INSERT INTO categories(id,group_type,code,name,slug,sort_order,is_active,is_featured,created_at) VALUES(:id,:group_type,:code,:name,:slug,:sort_order,:is_active,:is_featured,UTC_TIMESTAMP(6))'),{key:row[key] for key in ('id','group_type','code','name','slug','sort_order','is_active','is_featured')})
    additions=[{'product_id':pid,'category_id':cid} for pid,cid in plan['links'] if (pid,cid) not in original_links]
    if additions: connection.execute(sa.text('INSERT INTO product_categories(product_id,category_id) VALUES(:product_id,:category_id)'),additions)
    connection.exec_driver_sql('UPDATE flash_sale_categories SET include_descendants=0')
    for name in ('bi_categories_mysql57_guard','bu_categories_mysql57_guard'): connection.exec_driver_sql('DROP TRIGGER IF EXISTS '+quoted(name))
    for key in inspector.get_foreign_keys('categories'):
        if key['constrained_columns']==['parent_id']: connection.exec_driver_sql('ALTER TABLE categories DROP FOREIGN KEY '+quoted(key['name']))
    connection.exec_driver_sql('ALTER TABLE categories DROP INDEX ix_categories_parent_sort, DROP COLUMN parent_id, DROP COLUMN level, DROP COLUMN category_type, MODIFY COLUMN code VARCHAR(64) NOT NULL, ADD CONSTRAINT uq_categories_group_type_code UNIQUE(group_type,code), ADD INDEX ix_categories_group_sort(group_type,sort_order,id)')
    for definition in trigger_definitions().values(): connection.exec_driver_sql(definition['sql'])
    issues=table_issues(connection)+row_issues(connection)+trigger_issues(connection)
    if issues: raise RuntimeError('Flat master migration audit failed: '+', '.join(issues))

def downgrade(): raise RuntimeError('Independent product tags cannot be collapsed back into a hierarchy without data loss. Restore a reviewed backup.')
