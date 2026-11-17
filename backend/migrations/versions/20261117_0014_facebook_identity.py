"""Bind native Facebook sign-in to its stable subject without changing old users."""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20261117_0014'
down_revision = '20261117_0013'
branch_labels = depends_on = None
ALL_TABLES = ('users',)
RULES = {}


def table_issues(connection):
    inspector = sa.inspect(connection)
    if not inspector.has_table('users'):
        return ['missing_table:users']
    columns = {column['name']: column for column in inspector.get_columns('users')}
    column = columns.get('facebook_subject')
    issues = []
    if (not column or not isinstance(column['type'], sa.String) or column['type'].length != 128
            or not column['nullable'] or column['type'].collation != 'utf8mb4_bin'):
        issues.append('facebook_subject_column_missing_or_invalid')
    unique = {item['name']: item for item in inspector.get_unique_constraints('users')}
    if unique.get('uq_users_facebook_subject', {}).get('column_names') != ['facebook_subject']:
        issues.append('facebook_subject_unique_constraint_missing_or_invalid')
    return issues


def row_issues(connection):
    return ['empty_facebook_subject'] if connection.exec_driver_sql(
        "SELECT 1 FROM users WHERE facebook_subject = '' LIMIT 1").first() else []


def trigger_definitions(): return {}
def trigger_issues(connection): return []


def upgrade():
    op.add_column('users', sa.Column('facebook_subject', mysql.VARCHAR(128, collation='utf8mb4_bin'), nullable=True))
    op.create_unique_constraint('uq_users_facebook_subject', 'users', ['facebook_subject'])
    if not context.is_offline_mode():
        issues = table_issues(op.get_bind()) + row_issues(op.get_bind())
        if issues: raise RuntimeError('Native Facebook identity migration audit failed: ' + ', '.join(issues))


def downgrade():
    raise RuntimeError('Removing Facebook account bindings requires a reviewed backup and an identity recovery plan.')
