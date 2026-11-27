"""Cart tinting selections and immutable per-order-item tinting snapshots."""
from alembic import context, op
import sqlalchemy as sa

revision = '20261127_0017'
down_revision = '20261123_0016'
branch_labels = depends_on = None
RULES = {}
ALL_TABLES = ('cart_tintings', 'order_item_tintings')
TABLE_DDL = {
    'cart_tintings': '''CREATE TABLE cart_tintings (
        cart_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
        tinting_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
        details JSON NOT NULL,
        CONSTRAINT pk_cart_tintings PRIMARY KEY (cart_item_id),
        CONSTRAINT fk_cart_tintings_cart_item_id_cart_items_id FOREIGN KEY(cart_item_id) REFERENCES cart_items (id) ON DELETE CASCADE
    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC''',
    'order_item_tintings': '''CREATE TABLE order_item_tintings (
        order_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
        details JSON NOT NULL,
        CONSTRAINT pk_order_item_tintings PRIMARY KEY (order_item_id),
        CONSTRAINT fk_order_item_tintings_order_item_id_order_items_id FOREIGN KEY(order_item_id) REFERENCES order_items (id) ON DELETE RESTRICT
    ) ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC''',
}


def table_issues(connection, *, allow_missing=False):
    inspector, issues = sa.inspect(connection), []
    for table, key, parent, action in (
        ('cart_tintings', 'cart_item_id', 'cart_items', 'CASCADE'),
        ('order_item_tintings', 'order_item_id', 'order_items', 'RESTRICT'),
    ):
        if not inspector.has_table(table):
            if not allow_missing: issues.append('missing_table:' + table)
            continue
        columns = {column['name']:column for column in inspector.get_columns(table)}
        expected = {key, 'details'} | ({'tinting_id'} if table == 'cart_tintings' else set())
        if set(columns) != expected or any(column['nullable'] for column in columns.values()):
            issues.append('tinting_columns_mismatch:' + table)
        if any(name in columns and (not isinstance(columns[name]['type'], sa.String) or columns[name]['type'].length != 64)
               for name in expected - {'details'}):
            issues.append('tinting_id_type_mismatch:' + table)
        if 'details' in columns and not isinstance(columns['details']['type'], sa.JSON):
            issues.append('tinting_snapshot_type_mismatch:' + table)
        if inspector.get_pk_constraint(table)['constrained_columns'] != [key]:
            issues.append('tinting_primary_key_mismatch:' + table)
        fks = inspector.get_foreign_keys(table)
        if not any(fk['constrained_columns'] == [key] and fk['referred_table'] == parent
                   and fk['referred_columns'] == ['id'] and fk.get('options',{}).get('ondelete','RESTRICT').upper() == action for fk in fks):
            issues.append('tinting_fk_mismatch:' + table)
    return issues


def row_issues(connection):
    issues = []
    for table in ALL_TABLES:
        if connection.exec_driver_sql(f"SELECT 1 FROM {table} WHERE JSON_TYPE(details)<>'OBJECT' OR JSON_EXTRACT(details,'$.additional_price') IS NULL OR JSON_EXTRACT(details,'$.additional_price')<0 LIMIT 1").first():
            issues.append('invalid_tinting_snapshot:' + table)
    return issues


def trigger_definitions(): return {}
def trigger_issues(connection): return []


def upgrade():
    if not context.is_offline_mode():
        connection = op.get_bind()
        inspector = sa.inspect(connection)
        if not all(inspector.has_table(table) for table in ('cart_items','order_items')):
            raise RuntimeError('Tinting migration requires cart_items and order_items')
        issues = table_issues(connection, allow_missing=True)
        if issues: raise RuntimeError('Tinting migration schema mismatch: ' + ', '.join(issues))
    for table, sql in TABLE_DDL.items():
        if context.is_offline_mode() or not sa.inspect(op.get_bind()).has_table(table):
            op.execute(sa.text(sql))


def downgrade():
    raise RuntimeError('Tinting snapshots contain order history; restore a reviewed backup instead of dropping these tables')
