"""MySQL 5.7 reflection and recovery after implicitly committed migration DDL.

The inspector/DDL harness models interrupted deployments without connecting to
an operational database. Frozen SQL exports are also tested in test_migrations.
"""
from copy import deepcopy
import hashlib
import re

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.dialects.mysql.reflection import MySQLTableDefinitionParser

from mysql.base import Base
from mysql.check_integrity import load_growth_revision
from mysql import models  # noqa: F401: populate metadata for reflection fixtures


class Result:
    def __init__(self, rows=(), first=None):
        self.rows = rows
        self.value = first

    def mappings(self):
        return iter(self.rows)

    def first(self):
        return self.value


def reflected_tables(revision):
    """Represent MySQL 5.7: default ON DELETE RESTRICT is absent in reflection."""
    tables = {}
    dialect = mysql.dialect()
    for name in revision.COLUMNS:
        table = Base.metadata.tables[name]
        columns = []
        for column in table.columns:
            kind = column.type.dialect_impl(dialect)
            while isinstance(kind, sa.TypeDecorator):
                kind = kind.impl
            columns.append({'name': column.name, 'type': kind, 'nullable': column.nullable,
                            'default': str(column.server_default.arg) if isinstance(column.server_default, sa.DefaultClause) else None})
        tables[name] = {
            'columns': columns,
            'pk': {'constrained_columns': [column.name for column in table.primary_key]},
            'uniques': [{'name': constraint.name, 'column_names': [column.name for column in constraint.columns]}
                        for constraint in table.constraints if isinstance(constraint, sa.UniqueConstraint)],
            'fks': [{'constrained_columns': [element.parent.name for element in constraint.elements],
                     'referred_table': constraint.elements[0].column.table.name,
                     'referred_columns': [element.column.name for element in constraint.elements],
                     'options': {} if constraint.ondelete == 'RESTRICT' else {'ondelete': constraint.ondelete}}
                    for constraint in table.foreign_key_constraints],
            'indexes': [{'name': index.name, 'column_names': [column.name for column in index.columns],
                         'unique': bool(index.unique)} for index in table.indexes],
        }
    return tables


class Database:
    def __init__(self, revision, *, complete=False):
        self.revision = revision
        self.complete = reflected_tables(revision)
        self.tables = deepcopy(self.complete)
        self.executed = []
        self.triggers = {}
        self.fail_before = None
        self.invalid_tables = set()
        self.referrals = {'legacy': None, 'already-assigned': 'ME_KEEP_THIS_CODE'}
        self.legacy_rows = {'password_hash': 'unchanged', 'points': 27, 'order_total': 125000}
        if not complete:
            for name in revision.TABLE_DDL:
                del self.tables[name]
            for name, added in revision.COLUMNS.items():
                if name in self.tables:
                    self.tables[name]['columns'] = [c for c in self.tables[name]['columns'] if c['name'] not in added]
            self.tables['users']['uniques'] = [c for c in self.tables['users']['uniques'] if c['column_names'] != ['referral_code']]

    def has_table(self, table):
        return table in self.tables

    def get_columns(self, table):
        return self.tables[table]['columns']

    def get_pk_constraint(self, table):
        return self.tables[table]['pk']

    def get_unique_constraints(self, table):
        return self.tables[table]['uniques']

    def get_foreign_keys(self, table):
        return self.tables[table]['fks']

    def get_indexes(self, table):
        return self.tables[table]['indexes']

    def execute(self, statement):
        sql = str(statement)
        if 'information_schema.TRIGGERS' in sql:
            return Result(self.triggers.values())
        if self.fail_before == len(self.executed):
            raise RuntimeError('simulated connection failure after committed DDL')
        if sql.startswith('ALTER TABLE `'):
            table, name = re.match(r'ALTER TABLE `([^`]+)` ADD COLUMN (\w+)', sql).groups()
            assert name not in {column['name'] for column in self.get_columns(table)}, 'duplicate column'
            self.tables[table]['columns'].append(deepcopy(next(c for c in self.complete[table]['columns'] if c['name'] == name)))
        elif sql.startswith('ALTER TABLE users ADD CONSTRAINT'):
            assert not any(c['column_names'] == ['referral_code'] for c in self.get_unique_constraints('users')), 'duplicate unique'
            self.tables['users']['uniques'].append({'name': 'uq_users_referral_code', 'column_names': ['referral_code']})
        elif sql.startswith('CREATE TABLE '):
            table = re.match(r'CREATE TABLE (\w+)', sql).group(1)
            assert not self.has_table(table), 'duplicate table'
            self.tables[table] = deepcopy(self.complete[table])
            self.tables[table]['indexes'] = []  # Separate CREATE INDEX statements follow.
        elif sql.startswith('CREATE INDEX '):
            name, table = re.match(r'CREATE INDEX (\w+) ON (\w+)', sql).groups()
            assert not any(index['name'] == name for index in self.get_indexes(table)), 'duplicate index'
            self.tables[table]['indexes'].append(deepcopy(next(i for i in self.complete[table]['indexes'] if i['name'] == name)))
        elif sql.startswith('UPDATE users SET referral_code='):
            for name, value in self.referrals.items():
                if value is None:
                    self.referrals[name] = 'ME' + hashlib.sha256(name.encode()).hexdigest()[:24].upper()
        elif sql.startswith('DROP TRIGGER IF EXISTS '):
            self.triggers.pop(re.search(r'`([^`]+)`', sql).group(1), None)
        elif sql.startswith('CREATE TRIGGER '):
            name = re.match(r'CREATE TRIGGER `([^`]+)`', sql).group(1)
            assert name not in self.triggers, 'duplicate trigger'
            definition = self.revision.trigger_definitions()[name]
            self.triggers[name] = {'name': name, 'table_name': definition['table'], 'event': definition['event'],
                                   'timing': 'BEFORE', 'body': definition['body'], 'action_order': 1,
                                   'sql_mode': ','.join(sorted(self.revision.EXPECTED_SQL_MODES))}
        else:
            raise AssertionError(sql)
        self.executed.append(sql)
        return Result()

    def exec_driver_sql(self, sql):
        table = re.match(r'SELECT 1 FROM `([^`]+)`', sql)
        if table:
            return Result(first=(1,) if table.group(1) in self.invalid_tables else None)
        if sql.startswith("SELECT 1 FROM users WHERE role='customer'"):
            return Result(first=(1,) if any(not value for value in self.referrals.values()) else None)
        raise AssertionError(sql)


@pytest.fixture
def migration(monkeypatch):
    revision = load_growth_revision()

    def setup(*, complete=False):
        database = Database(revision, complete=complete)
        monkeypatch.setattr(revision.sa, 'inspect', lambda connection: connection)
        monkeypatch.setattr(revision.context, 'is_offline_mode', lambda: False)
        monkeypatch.setattr(revision.op, 'get_bind', lambda: database)
        monkeypatch.setattr(revision.op, 'execute', database.execute)
        return revision, database

    return setup


def test_mysql57_show_create_parser_omits_default_restrict():
    dialect = mysql.dialect()
    parser = MySQLTableDefinitionParser(dialect, dialect.identifier_preparer)
    state = parser.parse('''CREATE TABLE `daily_checkins` (
  `user_id` varchar(64) NOT NULL,
  CONSTRAINT `fk_checkin_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''', 'utf8mb4')
    assert state.fk_constraints[0]['ondelete'] is None


@pytest.mark.parametrize('action', [None, '', 'RESTRICT', 'restrict', 'NO ACTION', ' no   action '])
def test_reflected_default_actions_are_equivalent(migration, action):
    revision, database = migration(complete=True)
    for table in revision.FKS:
        for fk in database.get_foreign_keys(table):
            if not fk['options']:
                fk['options']['ondelete'] = action
    assert revision.table_issues(database) == []


@pytest.mark.parametrize('action', ['CASCADE', 'SET NULL'])
def test_restrict_fk_still_rejects_different_delete_behavior(migration, action):
    revision, database = migration(complete=True)
    database.get_foreign_keys('daily_checkins')[0]['options']['ondelete'] = action
    assert revision.table_issues(database) == ['growth_fk_missing:daily_checkins']


def test_default_action_does_not_replace_required_cascade(migration):
    revision, database = migration(complete=True)
    database.get_foreign_keys('email_verifications')[0]['options'] = {}
    assert revision.table_issues(database) == ['growth_fk_missing:email_verifications']


@pytest.mark.parametrize('defect', ['missing', 'target', 'composite_order'])
def test_real_foreign_key_defects_are_detected(migration, defect):
    revision, database = migration(complete=True)
    fks = database.get_foreign_keys('addon_flash_reservations')
    if defect == 'missing':
        fks.pop()
    elif defect == 'target':
        fks[0]['referred_table'] = 'wrong_table'
    else:
        fks[0]['referred_columns'].reverse()
    assert revision.table_issues(database) == ['growth_fk_missing:addon_flash_reservations']
    with pytest.raises(RuntimeError, match='existing schema mismatch'):
        revision.upgrade()
    assert database.executed == []


def assert_finished(revision, database):
    assert revision.table_issues(database) == []
    assert revision.row_issues(database) == []
    assert revision.trigger_issues(database) == []
    assert len(database.triggers) == 20
    assert database.referrals['already-assigned'] == 'ME_KEEP_THIS_CODE'
    assert database.legacy_rows == {'password_hash': 'unchanged', 'points': 27, 'order_total': 125000}


def test_fresh_upgrade_and_full_replay_preserve_existing_data(migration):
    revision, database = migration()
    revision.upgrade()
    assert_finished(revision, database)
    assert sum(sql.startswith(('ALTER TABLE', 'CREATE TABLE', 'CREATE INDEX')) for sql in database.executed) == 20
    first_codes = dict(database.referrals)
    database.executed.clear()
    revision.upgrade()
    assert_finished(revision, database)
    assert database.referrals == first_codes
    assert not any(sql.startswith(('ALTER TABLE', 'CREATE TABLE', 'CREATE INDEX')) for sql in database.executed)


def test_retry_after_the_reported_post_ddl_preflight_failure(migration):
    revision, database = migration(complete=True)
    # All DDL committed, revision remains 0014 and the new triggers are absent.
    revision.upgrade()
    assert_finished(revision, database)
    assert not any(sql.startswith(('ALTER TABLE', 'CREATE TABLE', 'CREATE INDEX')) for sql in database.executed)


@pytest.mark.parametrize('stop', [0, 3, 9, 12, 16, 19, 20, 22, 28, 60])
def test_retry_after_interrupted_ddl_or_guard_installation(migration, stop):
    revision, database = migration()
    database.fail_before = stop
    with pytest.raises(RuntimeError, match='simulated connection failure'):
        revision.upgrade()
    database.fail_before = None
    revision.upgrade()
    assert_finished(revision, database)


@pytest.mark.parametrize('defect', ['type', 'nullability', 'default', 'precision', 'index', 'primary_key', 'unique', 'unique_name', 'missing_column'])
def test_incompatible_existing_schema_is_rejected_before_writes(migration, defect):
    revision, database = migration(complete=True)
    column = next(c for c in database.get_columns('products') if c['name'] == 'sale_role')
    if defect == 'type':
        column['type'] = sa.String(64)
    elif defect == 'nullability':
        column['nullable'] = True
    elif defect == 'default':
        column['default'] = 'add_on'
    elif defect == 'precision':
        next(c for c in database.get_columns('users') if c['name'] == 'email_verified_at')['type'] = mysql.DATETIME()
    elif defect == 'index':
        database.get_indexes('customer_referrals')[0]['column_names'].reverse()
    elif defect == 'primary_key':
        database.get_pk_constraint('daily_checkins')['constrained_columns'].reverse()
    elif defect == 'unique':
        database.tables['customer_growth_rewards']['uniques'] = []
    elif defect == 'unique_name':
        next(c for c in database.get_unique_constraints('users') if c['column_names'] == ['referral_code'])['column_names'] = ['name']
    else:
        database.tables['daily_checkins']['columns'].pop()
    with pytest.raises(RuntimeError, match='existing schema mismatch'):
        revision.upgrade()
    assert database.executed == []


def test_invalid_rows_still_block_guard_replacement(migration):
    revision, database = migration(complete=True)
    database.invalid_tables.add('orders')
    with pytest.raises(RuntimeError, match='row_rule_violation:orders'):
        revision.upgrade()
    assert not database.triggers
    assert not any(sql.startswith('DROP TRIGGER') for sql in database.executed)
