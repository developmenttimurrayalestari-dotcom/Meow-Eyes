"""Allow non-expiring game/cashback points without rewriting past awards.

MySQL 5.7 enforces CHECK predicates through frozen BEFORE triggers. Pause
application writers while replacing guards; rerunning this revision is safe.
"""
import re
from alembic import context, op
import sqlalchemy as sa

revision = '20261123_0016'
down_revision = '20261120_0015'
branch_labels = depends_on = None
ALL_TABLES = ('game_rules', 'cashback_events', 'roulette_spins')
EXPECTED_SQL_MODES = {'STRICT_TRANS_TABLES','ERROR_FOR_DIVISION_BY_ZERO','NO_ENGINE_SUBSTITUTION','ONLY_FULL_GROUP_BY','NO_ZERO_DATE','NO_ZERO_IN_DATE'}
RULES = {'cashback_events': (('ck_cashback_events_bounds',
                      'percent > 0 AND percent <= 100 AND expiry_days >= 0 AND end_at > start_at',
                      'NEW.percent > 0 AND NEW.percent <= 100 AND NEW.expiry_days >= 0 AND NEW.end_at > '
                      'NEW.start_at'),),
 'game_rules': (('ck_game_rules_bounds',
                 'cooldown_seconds >= 0 AND expiry_days >= 0 AND max_duration_seconds >= 10 AND '
                 'max_duration_seconds <= 600 AND max_points >= 0 AND points_per_unit > 0',
                 'NEW.cooldown_seconds >= 0 AND NEW.expiry_days >= 0 AND NEW.max_duration_seconds >= 10 '
                 'AND NEW.max_duration_seconds <= 600 AND NEW.max_points >= 0 AND NEW.points_per_unit > '
                 '0'),
                ('ck_game_rules_engine',
                 "engine IN ('matching','slide_puzzle','space_war','roulette')",
                 "NEW.engine IN ('matching','slide_puzzle','space_war','roulette')"))}

def trigger_definitions():
    result = {}
    for table, rules in RULES.items():
        for event, prefix in (('INSERT', 'bi'), ('UPDATE', 'bu')):
            name = 'trg_meow5_' + table + '_' + prefix
            lines = ['BEGIN']
            for rule, _, predicate in rules:
                lines.append("  IF (" + predicate + ") IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Rule " + rule + " failed'; END IF;")
            lines.append('END')
            block = '\n'.join(lines)
            result[name] = {'table': table, 'event': event, 'timing': 'BEFORE', 'body': block,
                'sql': 'CREATE TRIGGER `' + name + '` BEFORE ' + event + ' ON `' + table + '` FOR EACH ROW ' + block}
    return result


def canonical_body(value):
    tokens = re.findall(r"'(?:''|[^'])*'|`(?:``|[^`])*`|[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|[^\s]", value)
    return tuple(token if token.startswith("'") else token.strip('`').lower() for token in tokens)



def table_issues(connection, *, allow_previous=False):
    inspector = sa.inspect(connection)
    issues = []
    for table in ALL_TABLES:
        if not inspector.has_table(table):
            issues.append('missing_table:' + table)
    if inspector.has_table('roulette_spins'):
        column = next((c for c in inspector.get_columns('roulette_spins') if c['name'] == 'expires_at'), None)
        if column is None or (not allow_previous and not column['nullable']):
            issues.append('roulette_spin_expiry_not_nullable')
    return issues


def row_issues(connection):
    issues = []
    for table, rules in RULES.items():
        where = ' OR '.join('(' + predicate + ') IS FALSE' for _, predicate, _ in rules)
        if connection.exec_driver_sql('SELECT 1 FROM `' + table + '` WHERE ' + where + ' LIMIT 1').first():
            issues.append('row_rule_violation:' + table)
    return issues


def trigger_issues(connection):
    rows = connection.execute(sa.text('SELECT TRIGGER_NAME AS name, EVENT_OBJECT_TABLE AS table_name, EVENT_MANIPULATION AS event, ACTION_TIMING AS timing, ACTION_STATEMENT AS body, SQL_MODE AS sql_mode, ACTION_ORDER AS action_order FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()')).mappings()
    actual = {row['name']: row for row in rows}
    issues = []
    for name, expected in trigger_definitions().items():
        row = actual.get(name)
        if not row:
            issues.append('missing_trigger:' + name)
            continue
        if row['table_name'] != expected['table'] or row['event'] != expected['event'] or row['timing'] != 'BEFORE' or canonical_body(row['body']) != canonical_body(expected['body']):
            issues.append('trigger_definition_mismatch:' + name)
        if set(row['sql_mode'].split(',')) != EXPECTED_SQL_MODES: issues.append('trigger_sql_mode_mismatch:' + name)
        last = max(int(i['action_order']) for i in actual.values() if i['table_name'] == row['table_name'] and i['event'] == row['event'] and i['timing'] == 'BEFORE')
        if int(row['action_order']) != last: issues.append('trigger_not_last:' + name)
    return issues



def upgrade():
    offline = context.is_offline_mode()
    if not offline:
        connection = op.get_bind()
        issues = table_issues(connection, allow_previous=True)
        if not issues: issues.extend(row_issues(connection))
        if issues: raise RuntimeError('Point expiry migration preflight failed: ' + ', '.join(issues))
    # Existing dates are retained. Only new point rewards may omit their expiry.
    op.execute(sa.text('ALTER TABLE roulette_spins MODIFY expires_at DATETIME(6) NULL'))
    if offline:
        output = op.get_context().impl.static_output
        output('DELIMITER $$')
        for name, definition in trigger_definitions().items():
            output('DROP TRIGGER IF EXISTS `' + name + '`$$')
            output(definition['sql'] + '$$')
        output('DELIMITER ;')
        return
    for name, definition in trigger_definitions().items():
        op.execute(sa.text('DROP TRIGGER IF EXISTS `' + name + '`'))
        op.execute(sa.text(definition['sql']))
    issues = table_issues(connection) + row_issues(connection) + trigger_issues(connection)
    if issues: raise RuntimeError('Point expiry migration audit failed: ' + ', '.join(issues))


def downgrade():
    raise RuntimeError('Non-expiring point rules require a reviewed backup before downgrade.')
