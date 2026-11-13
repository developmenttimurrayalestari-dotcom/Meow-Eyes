"""Separate product deletion from temporary deactivation; retain history."""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20261112_0007'
down_revision = '20261111_0006'
branch_labels = depends_on = None
ALL_TABLES = ('products',)
RULES = {}


def table_issues(connection):
    inspector = sa.inspect(connection)
    if not inspector.has_table('products'):
        return ['missing_table:products']
    columns = {column['name']: column for column in inspector.get_columns('products')}
    issues = []
    column = columns.get('deleted_at')
    if not column or not isinstance(column['type'], sa.DateTime) or not column['nullable']:
        issues.append('product_deletion_column_missing_or_invalid')
    indexes = {item['name']: item for item in inspector.get_indexes('products')}
    if indexes.get('ix_products_admin_list', {}).get('column_names') != ['deleted_at', 'created_at', 'id']:
        issues.append('product_admin_list_index_missing_or_invalid')
    return issues


def row_issues(connection):
    return ['deleted_product_still_active'] if connection.exec_driver_sql(
        'SELECT 1 FROM products WHERE deleted_at IS NOT NULL AND is_active <> 0 LIMIT 1').first() else []


def trigger_definitions(): return {}
def trigger_issues(connection): return []


def upgrade():
    # Additive migration: all existing products retain their current status.
    op.add_column('products', sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True))
    op.create_index('ix_products_admin_list', 'products', ['deleted_at', 'created_at', 'id'])
    if not context.is_offline_mode():
        issues = table_issues(op.get_bind()) + row_issues(op.get_bind())
        if issues: raise RuntimeError('Product deletion migration audit failed: ' + ', '.join(issues))


def downgrade():
    raise RuntimeError('Removing deletion markers would expose deleted products. Restore a reviewed backup instead.')
