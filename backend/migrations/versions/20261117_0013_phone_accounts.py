"""Allow phone/password accounts with a real optional email and unique canonical phone."""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '20261117_0013'
down_revision = '20261112_0012'
branch_labels = depends_on = None
ALL_TABLES = ('users',)
RULES = {}


def table_issues(connection):
    inspector = sa.inspect(connection)
    if not inspector.has_table('users'): return ['missing_table:users']
    columns = {column['name']: column for column in inspector.get_columns('users')}
    phone = columns.get('phone')
    issues = []
    if not phone or not isinstance(phone['type'], sa.String) or phone['type'].length != 16 or not phone['nullable']:
        issues.append('phone_column_missing_or_invalid')
    if not columns['email']['nullable']: issues.append('email_must_allow_phone_only_accounts')
    unique = {item['name']: item for item in inspector.get_unique_constraints('users')}
    if unique.get('uq_users_phone', {}).get('column_names') != ['phone']: issues.append('phone_unique_constraint_missing')
    return issues


def row_issues(connection):
    sql = "SELECT 1 FROM users WHERE (email IS NULL AND phone IS NULL) OR (phone IS NOT NULL AND phone NOT REGEXP '^[+][1-9][0-9]{7,14}$') LIMIT 1"
    return ['invalid_account_contact'] if connection.exec_driver_sql(sql).first() else []


def trigger_definitions(): return {}
def trigger_issues(connection): return []


def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(16), nullable=True))
    op.create_unique_constraint('uq_users_phone', 'users', ['phone'])
    op.alter_column('users', 'email', existing_type=sa.String(254), existing_nullable=False, nullable=True)
    if not context.is_offline_mode():
        issues = table_issues(op.get_bind()) + row_issues(op.get_bind())
        if issues: raise RuntimeError('Phone account migration audit failed: ' + ', '.join(issues))


def downgrade():
    raise RuntimeError('Phone-only accounts require a reviewed account recovery plan before removing phone support.')
