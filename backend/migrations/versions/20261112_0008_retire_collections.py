"""Retire collection masters and product assignments; retain private history."""
import json
from datetime import datetime, timezone
from alembic import context, op
import sqlalchemy as sa

revision = '20261112_0008'
down_revision = '20261112_0007'
branch_labels = depends_on = None
ALL_TABLES = ('categories', 'product_categories', 'products')
RULES = {}

def table_issues(connection):
    inspector = sa.inspect(connection)
    return ['missing_table:'+name for name in ALL_TABLES if not inspector.has_table(name)]

def row_issues(connection):
    queries = {
      'active_collection_remains': "SELECT 1 FROM categories WHERE group_type='collection' AND is_active<>0 LIMIT 1",
      'product_collection_tag_remains': "SELECT 1 FROM product_categories pc JOIN categories c ON c.id=pc.category_id WHERE c.group_type='collection' LIMIT 1",
      'product_primary_collection_remains': "SELECT 1 FROM products p JOIN categories c ON c.id=p.primary_category_id WHERE c.group_type='collection' LIMIT 1",
    }
    return [key for key,sql in queries.items() if connection.exec_driver_sql(sql).first()]

def trigger_definitions(): return {}
def trigger_issues(connection): return []

def retire_collections(connection):
    source = "SELECT id FROM categories WHERE group_type='collection'"
    rows = [dict(row) for row in connection.execute(sa.text('SELECT * FROM categories WHERE group_type=\'collection\'')).mappings()]
    links = [dict(row) for row in connection.execute(sa.text('SELECT * FROM product_categories WHERE category_id IN ('+source+')')).mappings()]
    primaries = [dict(row) for row in connection.execute(sa.text('SELECT id,primary_category_id FROM products WHERE primary_category_id IN ('+source+')')).mappings()]
    rules = [dict(row) for row in connection.execute(sa.text('SELECT * FROM flash_sale_categories WHERE category_id IN ('+source+')')).mappings()]
    item_sources = [dict(row) for row in connection.execute(sa.text('SELECT id,flash_sale_id,source_category_id FROM flash_sale_items WHERE source_category_id IN ('+source+')')).mappings()]
    banners = [dict(row) for row in connection.execute(sa.text('SELECT * FROM banners WHERE link_category_id IN ('+source+')')).mappings()]
    missing = connection.execute(sa.text("SELECT 1 FROM products p WHERE p.primary_category_id IN ("+source+") AND NOT EXISTS (SELECT 1 FROM categories c WHERE c.group_type='product_type' AND c.code=p.product_type) LIMIT 1")).first()
    if missing: raise RuntimeError('Canonical product type master missing; no collection changes applied')
    archive = json.dumps({'categories':rows,'product_tags':links,'primaries':primaries,'flash_rules':rules,'flash_item_sources':item_sources,'banners':banners},default=str)
    connection.execute(sa.text('INSERT INTO settings(`key`,value,description,is_public,updated_at) VALUES(:key,:value,:description,0,:now)'),
        {'key':'taxonomy-0008-retired-collections','value':archive,'description':'Private original collection assignments before retirement','now':datetime.now(timezone.utc).replace(tzinfo=None)})
    connection.execute(sa.text("UPDATE products SET primary_category_id=(SELECT id FROM categories c WHERE c.group_type='product_type' AND c.code=products.product_type) WHERE primary_category_id IN ("+source+")"))
    connection.execute(sa.text('DELETE FROM product_categories WHERE category_id IN ('+source+')'))
    # Existing materialized flash-sale items keep their original price and quota.
    connection.execute(sa.text('UPDATE flash_sale_items SET source_category_id=NULL WHERE source_category_id IN ('+source+')'))
    connection.execute(sa.text('DELETE FROM flash_sale_categories WHERE category_id IN ('+source+')'))
    connection.execute(sa.text("UPDATE banners SET link_type='none',link_url='' WHERE link_type='category' AND link_category_id IN ("+source+")"))
    connection.execute(sa.text('UPDATE banners SET link_category_id=NULL WHERE link_category_id IN ('+source+')'))
    connection.execute(sa.text("UPDATE categories SET is_active=0 WHERE group_type='collection'"))

def upgrade():
    if context.is_offline_mode(): raise RuntimeError('0008 requires online archival and validation of collection references')
    retire_collections(op.get_bind())
    issues = row_issues(op.get_bind())
    if issues: raise RuntimeError('Collection retirement audit failed: '+', '.join(issues))

def downgrade(): raise RuntimeError('Restore a reviewed private archive; automatic restoration could overwrite later assignments')
