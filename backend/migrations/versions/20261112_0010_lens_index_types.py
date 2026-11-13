"""Associate lens indexes with independent lens type master data."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20261112_0010'
down_revision = '20261112_0009'
branch_labels = depends_on = None
ALL_TABLES = ('lens_index_types',)
RULES = {}


def table_issues(connection):
    inspector = sa.inspect(connection)
    if not inspector.has_table('lens_index_types'):
        return ['missing_table:lens_index_types']
    columns = {c['name']: c for c in inspector.get_columns('lens_index_types')}
    issues = []
    if set(columns) != {'lens_index_id', 'category_id'} or any(c['nullable'] or not isinstance(c['type'], sa.String) or c['type'].length != 64 for c in columns.values()):
        issues.append('lens_index_types_columns_invalid')
    if inspector.get_pk_constraint('lens_index_types')['constrained_columns'] != ['lens_index_id', 'category_id']:
        issues.append('lens_index_types_primary_key_invalid')
    targets = {(tuple(f['constrained_columns']), f['referred_table'], tuple(f['referred_columns'])) for f in inspector.get_foreign_keys('lens_index_types')}
    if targets != {(('lens_index_id',), 'lens_indexes', ('id',)), (('category_id',), 'categories', ('id',))}:
        issues.append('lens_index_types_foreign_keys_invalid')
    return issues


def row_issues(connection):
    return ['lens_index_type_wrong_master_group'] if connection.exec_driver_sql(
        "SELECT 1 FROM lens_index_types t JOIN categories c ON c.id=t.category_id WHERE c.group_type <> 'lens_type' LIMIT 1").first() else []


def trigger_definitions(): return {}
def trigger_issues(connection): return []


def upgrade():
    op.create_table('lens_index_types',
        sa.Column('lens_index_id', mysql.VARCHAR(64, collation='utf8mb4_bin'), nullable=False),
        sa.Column('category_id', mysql.VARCHAR(64, collation='utf8mb4_bin'), nullable=False),
        sa.ForeignKeyConstraint(['lens_index_id'], ['lens_indexes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('lens_index_id', 'category_id'),
        mysql_engine='InnoDB', mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci', mysql_row_format='DYNAMIC')
    op.create_index('ix_lens_index_types_category', 'lens_index_types', ['category_id', 'lens_index_id'])


def downgrade():
    raise RuntimeError('Removing lens type assignments loses catalog configuration; restore a reviewed backup')
