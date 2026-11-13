"""Store TTB document references for inventory receipt and issue movements."""
from alembic import op
import sqlalchemy as sa
revision='20261112_0009'
down_revision='20261112_0008'
branch_labels=depends_on=None
ALL_TABLES=('stock_movements',)
RULES={}
def table_issues(connection):
    inspector=sa.inspect(connection)
    if not inspector.has_table('stock_movements'):return ['missing_table:stock_movements']
    column=next((c for c in inspector.get_columns('stock_movements') if c['name']=='ttb_number'),None)
    return [] if column and isinstance(column['type'],sa.String) and column['type'].length==128 and column['nullable'] else ['stock_ttb_column_missing_or_invalid']
def row_issues(connection):return []
def trigger_definitions():return {}
def trigger_issues(connection):return []
def upgrade():op.add_column('stock_movements',sa.Column('ttb_number',sa.String(128),nullable=True))
def downgrade():raise RuntimeError('Dropping TTB references loses inventory audit data; restore a reviewed backup')
