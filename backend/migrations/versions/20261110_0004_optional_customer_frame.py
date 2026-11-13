"""Allow immutable manual-frame sessions without a catalog product.

Preserves all historical rows and reuses the frozen 0003 guard definitions.
MySQL DDL commits implicitly: back up and pause writers before upgrading.
"""
import importlib.util
from pathlib import Path
from alembic import context, op
import sqlalchemy as sa

revision = "20261110_0004"
down_revision = "20261109_0003"
branch_labels = depends_on = None

_spec = importlib.util.spec_from_file_location('_frozen_meow3_for_meow4', Path(__file__).with_name('20261109_0003_customer_meowsurement.py'))
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
_base.RULES = {**_base.RULES, 'meowsurement_sessions': tuple(
    (name, predicate.replace("('product','variant')", "('product','variant','manual')"), trigger.replace("('product','variant')", "('product','variant','manual')"))
    for name, predicate, trigger in _base.RULES['meowsurement_sessions']) + (
        ('ck_meowsurement_sessions_frame_source',
         "(spec_scope = 'manual' AND product_id IS NULL AND variant_id IS NULL) OR (spec_scope IN ('product','variant') AND product_id IS NOT NULL AND variant_id IS NOT NULL)",
         "(NEW.spec_scope = 'manual' AND NEW.product_id IS NULL AND NEW.variant_id IS NULL) OR (NEW.spec_scope IN ('product','variant') AND NEW.product_id IS NOT NULL AND NEW.variant_id IS NOT NULL)"),)}
ALL_TABLES, RULES = _base.ALL_TABLES, _base.RULES
IMMUTABLE, custom_checks = _base.IMMUTABLE, _base.custom_checks
trigger_definitions, trigger_issues, row_issues = _base.trigger_definitions, _base.trigger_issues, _base.row_issues

def table_issues(connection):
    issues = _base.table_issues(connection)
    if 'missing_table:meowsurement_sessions' not in issues:
        nullable = connection.execute(sa.text("SELECT IS_NULLABLE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='meowsurement_sessions' AND COLUMN_NAME='product_id'")).scalar()
        if nullable != 'YES':
            issues.append('manual_frame_product_column_must_be_nullable')
    return issues

def upgrade():
    statements = ["ALTER TABLE meowsurement_sessions MODIFY product_id VARCHAR(64) COLLATE utf8mb4_bin NULL"]
    definitions = {name: definition for name, definition in trigger_definitions().items() if definition['table'] == 'meowsurement_sessions' and definition['event'] in {'INSERT', 'UPDATE'}}
    if context.is_offline_mode():
        output = op.get_context().impl.static_output
        for statement in statements: output(statement + ';')
        output('DELIMITER $$')
        for name, definition in definitions.items():
            output('DROP TRIGGER IF EXISTS `' + name + '`$$')
            output(definition['sql'] + '$$')
        output('DELIMITER ;')
        return
    connection = op.get_bind()
    for statement in statements: connection.exec_driver_sql(statement)
    for name, definition in definitions.items():
        connection.exec_driver_sql('DROP TRIGGER IF EXISTS `' + name + '`')
        connection.exec_driver_sql(definition['sql'])
    issues = table_issues(connection) + row_issues(connection) + trigger_issues(connection)
    if issues: raise RuntimeError('Optional frame migration audit failed: ' + ', '.join(issues))

def downgrade():
    raise RuntimeError('Manual-frame sessions may exist. Restore a reviewed backup rather than dropping customer data.')
