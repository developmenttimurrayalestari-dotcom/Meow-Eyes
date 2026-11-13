"""Bind native Google sign-in to its stable subject without changing old users."""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20261112_0011'
down_revision = '20261112_0010'
branch_labels = depends_on = None
ALL_TABLES = ('users',)
RULES = {}


def table_issues(connection):
    inspector = sa.inspect(connection)
    if not inspector.has_table('users'):
        return ['missing_table:users']
    columns = {column['name']: column for column in inspector.get_columns('users')}
    column = columns.get('google_subject')
    issues = []
    if (not column or not isinstance(column['type'], sa.String) or column['type'].length != 255
            or not column['nullable'] or column['type'].collation != 'utf8mb4_bin'):
        issues.append('google_subject_column_missing_or_invalid')
    unique = {item['name']: item for item in inspector.get_unique_constraints('users')}
    if unique.get('uq_users_google_subject', {}).get('column_names') != ['google_subject']:
        issues.append('google_subject_unique_constraint_missing_or_invalid')
    return issues


def row_issues(connection):
    return ['empty_google_subject'] if connection.exec_driver_sql(
        "SELECT 1 FROM users WHERE google_subject = '' LIMIT 1").first() else []


def trigger_definitions(): return {}
def trigger_issues(connection): return []


def upgrade():
    op.add_column('users', sa.Column('google_subject', mysql.VARCHAR(255, collation='utf8mb4_bin'), nullable=True))
    op.create_unique_constraint('uq_users_google_subject', 'users', ['google_subject'])
    if not context.is_offline_mode():
        issues = table_issues(op.get_bind()) + row_issues(op.get_bind())
        if issues: raise RuntimeError('Native Google identity migration audit failed: ' + ', '.join(issues))


def downgrade():
    raise RuntimeError('Removing Google account bindings requires a reviewed backup and an identity recovery plan.')
