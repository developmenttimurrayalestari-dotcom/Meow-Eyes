"""Enable Accessories in category/product guards without rewriting store data."""
import re
from alembic import context, op
import sqlalchemy as sa

revision = '20261112_0012'
down_revision = '20261112_0011'
branch_labels = depends_on = None
ALL_TABLES = ('products', 'categories')
EXPECTED_SQL_MODES = {'STRICT_TRANS_TABLES','ERROR_FOR_DIVISION_BY_ZERO','NO_ENGINE_SUBSTITUTION','ONLY_FULL_GROUP_BY','NO_ZERO_DATE','NO_ZERO_IN_DATE'}
# Frozen predicates; do not import live application validation into migrations.
RULES = {'products': (('ck_products_counters',
               '`rating_avg` BETWEEN 0 AND 5 AND `rating_count` >= 0 AND `sold_count` >= 0',
               'NEW.`rating_avg` BETWEEN 0 AND 5 AND NEW.`rating_count` >= 0 AND NEW.`sold_count` >= 0'),
              ('ck_products_inventory_values',
               '`weight_gram` >= 0 AND `min_stock_alert` >= 0',
               'NEW.`weight_gram` >= 0 AND NEW.`min_stock_alert` >= 0'),
              ('ck_products_legacy_flash_nonnegative',
               '`flash_sale_price` IS NULL OR `flash_sale_price` >= 0',
               'NEW.`flash_sale_price` IS NULL OR NEW.`flash_sale_price` >= 0'),
              ('ck_products_prices_nonnegative',
               '`price` >= 0 AND (`discount_price` IS NULL OR `discount_price` >= 0)',
               'NEW.`price` >= 0 AND (NEW.`discount_price` IS NULL OR NEW.`discount_price` >= 0)'),
              ('ck_products_type',
               "`product_type` IN ('frame','lens','package','accessories')",
               "NEW.`product_type` IN ('frame','lens','package','accessories')")),
 'categories': (('ck_categories_group_type',
                 "group_type IN ('product_type','lens_type','gender','frame_shape','material','collection')",
                 'NEW.group_type IN '
                 "('product_type','lens_type','gender','frame_shape','material','collection')"),
                ('ck_categories_product_kind',
                 "group_type <> 'product_type' OR code IN ('frame','lens','package','accessories')",
                 "NEW.group_type <> 'product_type' OR NEW.code IN ('frame','lens','package','accessories')"))}


def trigger_definitions():
    result = {}
    for table, rules in RULES.items():
        for event, prefix in (('INSERT', 'bi'), ('UPDATE', 'bu')):
            name = prefix + '_' + table + '_mysql57_guard'
            if table == 'products':
                lines = ['BEGIN']
                for rule, _, predicate in rules:
                    lines.extend(['  IF (' + predicate + ') IS FALSE THEN', "    SIGNAL SQLSTATE '45000'",
                                  "      SET MESSAGE_TEXT = 'Integrity rule " + rule + " failed';", '  END IF;'])
                lines.append('END')
                body = '\n'.join(lines)
                sql = 'CREATE TRIGGER `' + name + '` BEFORE ' + event + ' ON `products`\nFOR EACH ROW\n' + body
            else:
                lines = ["IF (" + predicate + ") IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule " + rule + " failed'; END IF;" for rule, _, predicate in rules]
                if event == 'UPDATE':
                    lines.append("IF NOT (NEW.group_type <=> OLD.group_type) OR NOT (NEW.code <=> OLD.code) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Master group and code are immutable'; END IF;")
                body = 'BEGIN\n  ' + '\n  '.join(lines) + '\nEND'
                sql = 'CREATE TRIGGER `' + name + '` BEFORE ' + event + ' ON categories FOR EACH ROW ' + body
            result[name] = {'table': table, 'event': event, 'timing': 'BEFORE', 'body': body, 'sql': sql}
    return result


def canonical_body(value):
    tokens = re.findall(r"'(?:''|[^'])*'|`(?:``|[^`])*`|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|[^\s]", value)
    return tuple(token if token.startswith("'") else token.strip('`').lower() for token in tokens)


def table_issues(connection):
    inspector = sa.inspect(connection)
    return ['missing_table:' + table for table in ALL_TABLES if not inspector.has_table(table)]


def row_issues(connection):
    issues = []
    for table, rules in RULES.items():
        where = ' OR '.join('(' + predicate + ') IS FALSE' for _, predicate, _ in rules)
        if connection.exec_driver_sql('SELECT 1 FROM `' + table + '` WHERE ' + where + ' LIMIT 1').first():
            issues.append('row_rule_violation:' + table)
    return issues


def trigger_issues(connection, *, accept_previous=False):
    rows = connection.execute(sa.text('SELECT TRIGGER_NAME AS name, EVENT_OBJECT_TABLE AS table_name, EVENT_MANIPULATION AS event, ACTION_TIMING AS timing, ACTION_STATEMENT AS body, SQL_MODE AS sql_mode, ACTION_ORDER AS action_order FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()')).mappings()
    actual = {row['name']: row for row in rows}
    issues = []
    for name, expected in trigger_definitions().items():
        row = actual.get(name)
        if not row:
            issues.append('missing_trigger:' + name); continue
        bodies = [canonical_body(expected['body'])]
        if accept_previous:
            bodies.append(canonical_body(expected['body'].replace("('frame','lens','package','accessories')", "('frame','lens','package')")))
        if (row['table_name'] != expected['table'] or row['event'] != expected['event']
                or row['timing'] != 'BEFORE' or canonical_body(row['body']) not in bodies):
            issues.append('trigger_definition_mismatch:' + name)
        if set(row['sql_mode'].split(',')) != EXPECTED_SQL_MODES:
            issues.append('trigger_sql_mode_mismatch:' + name)
        last = max(int(item['action_order']) for item in actual.values() if item['table_name'] == row['table_name'] and item['event'] == row['event'] and item['timing'] == 'BEFORE')
        if int(row['action_order']) != last: issues.append('trigger_not_last:' + name)
    return issues


def upgrade():
    definitions = trigger_definitions()
    if context.is_offline_mode():
        output = op.get_context().impl.static_output
        output('-- Back up first; pause writers while replacing the four MySQL 5.7 guards.')
        output('DELIMITER $$')
        for name, definition in definitions.items():
            output('DROP TRIGGER `' + name + '`$$')
            output(definition['sql'] + '$$')
        output('DELIMITER ;')
        return
    connection = op.get_bind()
    issues = table_issues(connection) + row_issues(connection) + trigger_issues(connection, accept_previous=True)
    if issues: raise RuntimeError('Accessories preflight failed: ' + ', '.join(issues))
    for name, definition in definitions.items():
        op.execute(sa.text('DROP TRIGGER `' + name + '`'))
        op.execute(sa.text(definition['sql']))
    issues = row_issues(connection) + trigger_issues(connection)
    if issues: raise RuntimeError('Accessories migration audit failed: ' + ', '.join(issues))


def downgrade():
    raise RuntimeError('Removing Accessories support requires a reviewed backup and handling existing accessory products.')
