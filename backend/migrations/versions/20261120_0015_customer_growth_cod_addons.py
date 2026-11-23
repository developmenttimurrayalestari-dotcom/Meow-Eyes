"""Email verification, member growth, COD, coordinates and cart Add Ons.

Frozen schema and MySQL 5.7 guard definitions. Back up before upgrading and
pause application writers while guards are replaced. No old transactions,
wallet lots, credential hashes or product prices are rewritten.
"""
import re
from alembic import context, op
import sqlalchemy as sa

revision = '20261120_0015'
down_revision = '20261117_0014'
branch_labels = depends_on = None
EXPECTED_SQL_MODES = {'STRICT_TRANS_TABLES','ERROR_FOR_DIVISION_BY_ZERO','NO_ENGINE_SUBSTITUTION','ONLY_FULL_GROUP_BY','NO_ZERO_DATE','NO_ZERO_IN_DATE'}
ALL_TABLES = ('users',
 'products',
 'addresses',
 'order_addresses',
 'orders',
 'vouchers',
 'email_verifications',
 'customer_referrals',
 'customer_growth_rewards',
 'customer_voucher_grants',
 'daily_checkins',
 'cart_item_addons',
 'addon_flash_reservations')
TABLE_DDL = {'email_verifications': 'CREATE TABLE email_verifications (\n'
                        '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\ttoken_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                        '\temail VARCHAR(254) NOT NULL, \n'
                        '\texpires_at DATETIME(6) NOT NULL, \n'
                        '\tused_at DATETIME(6), \n'
                        '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                        '\tCONSTRAINT pk_email_verifications PRIMARY KEY (id), \n'
                        '\tCONSTRAINT fk_email_verifications_user_id_users_user_id FOREIGN KEY(user_id) '
                        'REFERENCES users (user_id) ON DELETE CASCADE, \n'
                        '\tCONSTRAINT uq_email_verifications_token_hash UNIQUE (token_hash)\n'
                        ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'customer_referrals': 'CREATE TABLE customer_referrals (\n'
                       '\treferee_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                       '\treferrer_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                       '\trule_snapshot JSON NOT NULL, \n'
                       '\trewarded_at DATETIME(6), \n'
                       '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                       '\tCONSTRAINT pk_customer_referrals PRIMARY KEY (referee_id), \n'
                       '\tCONSTRAINT fk_customer_referrals_referee_id_users_user_id FOREIGN KEY(referee_id) '
                       'REFERENCES users (user_id) ON DELETE RESTRICT, \n'
                       '\tCONSTRAINT fk_customer_referrals_referrer_id_users_user_id FOREIGN KEY(referrer_id) '
                       'REFERENCES users (user_id) ON DELETE RESTRICT\n'
                       ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'customer_growth_rewards': 'CREATE TABLE customer_growth_rewards (\n'
                            '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                            '\tevent_key VARCHAR(191) NOT NULL, \n'
                            '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                            '\tsnapshot JSON NOT NULL, \n'
                            "\tstatus VARCHAR(16) NOT NULL DEFAULT 'pending', \n"
                            '\tgranted_at DATETIME(6), \n'
                            '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                            '\tCONSTRAINT pk_customer_growth_rewards PRIMARY KEY (id), \n'
                            '\tCONSTRAINT uq_customer_growth_rewards_event_key UNIQUE (event_key), \n'
                            '\tCONSTRAINT fk_customer_growth_rewards_user_id_users_user_id FOREIGN KEY(user_id) '
                            'REFERENCES users (user_id) ON DELETE RESTRICT\n'
                            ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'customer_voucher_grants': 'CREATE TABLE customer_voucher_grants (\n'
                            '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                            '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                            '\tvoucher_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                            '\tsource VARCHAR(32) NOT NULL, \n'
                            '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                            '\tCONSTRAINT pk_customer_voucher_grants PRIMARY KEY (id), \n'
                            '\tCONSTRAINT uq_customer_voucher_grants_user_id_voucher_id UNIQUE (user_id, '
                            'voucher_id), \n'
                            '\tCONSTRAINT fk_customer_voucher_grants_user_id_users_user_id FOREIGN KEY(user_id) '
                            'REFERENCES users (user_id) ON DELETE RESTRICT, \n'
                            '\tCONSTRAINT fk_customer_voucher_grants_voucher_id_vouchers_id FOREIGN '
                            'KEY(voucher_id) REFERENCES vouchers (id) ON DELETE RESTRICT\n'
                            ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'daily_checkins': 'CREATE TABLE daily_checkins (\n'
                   '\tuser_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                   '\tday VARCHAR(10) NOT NULL, \n'
                   '\tstreak INTEGER NOT NULL, \n'
                   '\tpoints INTEGER NOT NULL, \n'
                   '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                   '\tCONSTRAINT pk_daily_checkins PRIMARY KEY (user_id, day), \n'
                   '\tCONSTRAINT fk_daily_checkins_user_id_users_user_id FOREIGN KEY(user_id) REFERENCES users '
                   '(user_id) ON DELETE RESTRICT\n'
                   ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'cart_item_addons': 'CREATE TABLE cart_item_addons (\n'
                     '\tcart_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                     '\tproduct_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                     '\tvariant_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                     '\tCONSTRAINT pk_cart_item_addons PRIMARY KEY (cart_item_id, product_id), \n'
                     '\tCONSTRAINT fk_cart_item_addons_product_id_variant_id_prod_79b4ad7e2738 FOREIGN '
                     'KEY(product_id, variant_id) REFERENCES product_variants (product_id, id) ON DELETE '
                     'RESTRICT, \n'
                     '\tCONSTRAINT fk_cart_item_addons_cart_item_id_cart_items_id FOREIGN KEY(cart_item_id) '
                     'REFERENCES cart_items (id) ON DELETE CASCADE, \n'
                     '\tCONSTRAINT fk_cart_item_addons_product_id_products_id FOREIGN KEY(product_id) REFERENCES '
                     'products (id) ON DELETE RESTRICT\n'
                     ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci',
 'addon_flash_reservations': 'CREATE TABLE addon_flash_reservations (\n'
                             '\tid VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                             '\tcomponent_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                             '\torder_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                             '\tproduct_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                             '\tflash_sale_item_id VARCHAR(64) COLLATE utf8mb4_bin NOT NULL, \n'
                             '\tquantity INTEGER NOT NULL, \n'
                             "\tstatus VARCHAR(16) NOT NULL DEFAULT 'active', \n"
                             '\texpires_at DATETIME(6) NOT NULL, \n'
                             '\tresolved_at DATETIME(6), \n'
                             '\tcreated_at DATETIME(6) NOT NULL DEFAULT now(6), \n'
                             '\tCONSTRAINT pk_addon_flash_reservations PRIMARY KEY (id), \n'
                             '\tCONSTRAINT uq_addon_flash_reservations_component_id_flash_sale_item_id UNIQUE '
                             '(component_id, flash_sale_item_id), \n'
                             '\tCONSTRAINT fk_addon_flash_reservations_component_id_order_54baf21467dd FOREIGN '
                             'KEY(component_id, order_id, product_id) REFERENCES order_item_components (id, '
                             'order_id, product_id) ON DELETE RESTRICT, \n'
                             '\tCONSTRAINT fk_addon_flash_reservations_flash_sale_item_id_f9dbd13f63bb FOREIGN '
                             'KEY(flash_sale_item_id, product_id) REFERENCES flash_sale_items (id, product_id) ON '
                             'DELETE RESTRICT\n'
                             ')ENGINE=InnoDB CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COLLATE utf8mb4_unicode_ci'}
INDEX_DDL = ['CREATE INDEX ix_email_verifications_user_date ON email_verifications (user_id, created_at)',
 'CREATE INDEX ix_referrals_referrer ON customer_referrals (referrer_id, created_at)',
 'CREATE INDEX ix_growth_rewards_pending ON customer_growth_rewards (status, user_id)']
ALTER_COLUMNS = ['ALTER TABLE `users` ADD COLUMN email_verified_at DATETIME(6)',
 'ALTER TABLE `users` ADD COLUMN referral_code VARCHAR(32)',
 "ALTER TABLE `products` ADD COLUMN sale_role VARCHAR(16) NOT NULL DEFAULT 'main'",
 'ALTER TABLE `addresses` ADD COLUMN latitude NUMERIC(10, 7)',
 'ALTER TABLE `addresses` ADD COLUMN longitude NUMERIC(10, 7)',
 'ALTER TABLE `order_addresses` ADD COLUMN latitude NUMERIC(10, 7)',
 'ALTER TABLE `order_addresses` ADD COLUMN longitude NUMERIC(10, 7)',
 "ALTER TABLE `orders` ADD COLUMN payment_mode VARCHAR(16) NOT NULL DEFAULT 'online'",
 "ALTER TABLE `vouchers` ADD COLUMN audience VARCHAR(16) NOT NULL DEFAULT 'general'",
 'ALTER TABLE users ADD CONSTRAINT uq_users_referral_code UNIQUE (referral_code)']
COLUMNS = {'users': ('email_verified_at', 'referral_code'),
 'products': ('sale_role',),
 'addresses': ('latitude', 'longitude'),
 'order_addresses': ('latitude', 'longitude'),
 'orders': ('payment_mode',),
 'vouchers': ('audience',),
 'email_verifications': ('id', 'user_id', 'token_hash', 'email', 'expires_at', 'used_at', 'created_at'),
 'customer_referrals': ('referee_id', 'referrer_id', 'rule_snapshot', 'rewarded_at', 'created_at'),
 'customer_growth_rewards': ('id', 'event_key', 'user_id', 'snapshot', 'status', 'granted_at', 'created_at'),
 'customer_voucher_grants': ('id', 'user_id', 'voucher_id', 'source', 'created_at'),
 'daily_checkins': ('user_id', 'day', 'streak', 'points', 'created_at'),
 'cart_item_addons': ('cart_item_id', 'product_id', 'variant_id'),
 'addon_flash_reservations': ('id',
                              'component_id',
                              'order_id',
                              'product_id',
                              'flash_sale_item_id',
                              'quantity',
                              'status',
                              'expires_at',
                              'resolved_at',
                              'created_at')}
UNIQUES = {'email_verifications': [('token_hash',)],
 'customer_referrals': [],
 'customer_growth_rewards': [('event_key',)],
 'customer_voucher_grants': [('user_id', 'voucher_id')],
 'daily_checkins': [],
 'cart_item_addons': [],
 'addon_flash_reservations': [('component_id', 'flash_sale_item_id')]}
FKS = {'email_verifications': [(('user_id',), ('users.user_id',), 'CASCADE')],
 'customer_referrals': [(('referee_id',), ('users.user_id',), 'RESTRICT'),
                        (('referrer_id',), ('users.user_id',), 'RESTRICT')],
 'customer_growth_rewards': [(('user_id',), ('users.user_id',), 'RESTRICT')],
 'customer_voucher_grants': [(('user_id',), ('users.user_id',), 'RESTRICT'),
                             (('voucher_id',), ('vouchers.id',), 'RESTRICT')],
 'daily_checkins': [(('user_id',), ('users.user_id',), 'RESTRICT')],
 'cart_item_addons': [(('cart_item_id',), ('cart_items.id',), 'CASCADE'),
                      (('product_id',), ('products.id',), 'RESTRICT'),
                      (('product_id', 'variant_id'),
                       ('product_variants.product_id', 'product_variants.id'),
                       'RESTRICT')],
 'addon_flash_reservations': [(('component_id', 'order_id', 'product_id'),
                               ('order_item_components.id',
                                'order_item_components.order_id',
                                'order_item_components.product_id'),
                               'RESTRICT'),
                              (('flash_sale_item_id', 'product_id'),
                               ('flash_sale_items.id', 'flash_sale_items.product_id'),
                               'RESTRICT')]}
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
              ('ck_products_sale_role',
               "`sale_role` IN ('main','add_on')",
               "NEW.`sale_role` IN ('main','add_on')"),
              ('ck_products_type',
               "`product_type` IN ('frame','lens','package','accessories')",
               "NEW.`product_type` IN ('frame','lens','package','accessories')")),
 'addresses': (('ck_addresses_coordinates',
                '(`latitude` IS NULL AND `longitude` IS NULL) OR (`latitude` IS NOT NULL AND `longitude` IS NOT '
                'NULL AND `latitude` BETWEEN -90 AND 90 AND `longitude` BETWEEN -180 AND 180)',
                '(NEW.`latitude` IS NULL AND NEW.`longitude` IS NULL) OR (NEW.`latitude` IS NOT NULL AND '
                'NEW.`longitude` IS NOT NULL AND NEW.`latitude` BETWEEN -90 AND 90 AND NEW.`longitude` BETWEEN '
                '-180 AND 180)'),),
 'order_addresses': (('ck_order_addresses_coordinates',
                      '(`latitude` IS NULL AND `longitude` IS NULL) OR (`latitude` IS NOT NULL AND `longitude` IS '
                      'NOT NULL AND `latitude` BETWEEN -90 AND 90 AND `longitude` BETWEEN -180 AND 180)',
                      '(NEW.`latitude` IS NULL AND NEW.`longitude` IS NULL) OR (NEW.`latitude` IS NOT NULL AND '
                      'NEW.`longitude` IS NOT NULL AND NEW.`latitude` BETWEEN -90 AND 90 AND NEW.`longitude` '
                      'BETWEEN -180 AND 180)'),),
 'orders': (('ck_orders_amounts',
             '`points_used` >= 0 AND `points_discount` >= 0 AND `roulette_discount` >= 0 AND `shipping_cost` >= 0 '
             'AND `total` >= 0',
             'NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND '
             'NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0'),
            ('ck_orders_discount_amounts',
             '`subtotal` >= 0 AND `discount` >= 0 AND `flash_sale_discount` >= 0 AND `voucher_discount` >= 0',
             'NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND '
             'NEW.`voucher_discount` >= 0'),
            ('ck_orders_payment_mode',
             "`payment_mode` IN ('online','cod')",
             "NEW.`payment_mode` IN ('online','cod')"),
            ('ck_orders_payment_status',
             "`payment_status` IN ('pending','cod_pending','paid','failed','expired','cancelled','refunded')",
             "NEW.`payment_status` IN ('pending','cod_pending','paid','failed','expired','cancelled','refunded')"),
            ('ck_orders_shipment_status',
             '`shipment_status` IN '
             "('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')",
             'NEW.`shipment_status` IN '
             "('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')"),
            ('ck_orders_status',
             '`status` IN '
             "('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')",
             'NEW.`status` IN '
             "('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')")),
 'vouchers': (('ck_vouchers_amounts',
               '`discount_value` >= 0 AND `min_purchase` >= 0 AND (`max_discount` IS NULL OR `max_discount` >= 0)',
               'NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR '
               'NEW.`max_discount` >= 0)'),
              ('ck_vouchers_audience',
               "`audience` IN ('general','new_member','referral')",
               "NEW.`audience` IN ('general','new_member','referral')"),
              ('ck_vouchers_percentage',
               "`discount_type` <> 'percent' OR `discount_value` <= 100",
               "NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100"),
              ('ck_vouchers_quotas',
               '`quota` >= 0 AND `used_count` >= 0 AND `used_count` <= `quota` AND `quota_per_user` >= 0',
               'NEW.`quota` >= 0 AND NEW.`used_count` >= 0 AND NEW.`used_count` <= NEW.`quota` AND '
               'NEW.`quota_per_user` >= 0'),
              ('ck_vouchers_type',
               "`discount_type` IN ('percent','nominal','free_shipping')",
               "NEW.`discount_type` IN ('percent','nominal','free_shipping')"),
              ('ck_vouchers_window', '`end_at` > `start_at`', 'NEW.`end_at` > NEW.`start_at`')),
 'order_item_components': (('ck_order_item_components_amounts',
                            '`quantity` > 0 AND `unit_price` >= 0 AND `subtotal` >= 0 AND `index_surcharge` >= 0',
                            'NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND '
                            'NEW.`index_surcharge` >= 0'),
                           ('ck_order_item_components_type',
                            "`component_type` IN ('primary','lens','add_on')",
                            "NEW.`component_type` IN ('primary','lens','add_on')")),
 'customer_referrals': (('ck_customer_referrals_not_self',
                         '`referee_id` <> `referrer_id`',
                         'NEW.`referee_id` <> NEW.`referrer_id`'),),
 'customer_growth_rewards': (('ck_customer_growth_rewards_status',
                              "`status` IN ('pending','granted')",
                              "NEW.`status` IN ('pending','granted')"),),
 'daily_checkins': (('ck_daily_checkins_amounts',
                     '`streak` > 0 AND `points` >= 0',
                     'NEW.`streak` > 0 AND NEW.`points` >= 0'),),
 'addon_flash_reservations': (('ck_addon_flash_reservations_quantity', '`quantity` > 0', 'NEW.`quantity` > 0'),
                              ('ck_addon_flash_reservations_status',
                               "`status` IN ('active','confirmed','expired','cancelled')",
                               "NEW.`status` IN ('active','confirmed','expired','cancelled')"))}

def trigger_definitions():
    result = {}
    for table, rules in RULES.items():
        for event, prefix in (('INSERT', 'bi'), ('UPDATE', 'bu')):
            name = prefix + '_' + table + '_mysql57_guard'
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


def table_issues(connection):
    inspector = sa.inspect(connection)
    issues = []
    for table, required in COLUMNS.items():
        if not inspector.has_table(table):
            issues.append('missing_table:' + table)
            continue
        actual = {c['name'] for c in inspector.get_columns(table)}
        if not set(required) <= actual: issues.append('growth_columns_missing:' + table)
    for table, expected in UNIQUES.items():
        if not inspector.has_table(table): continue
        actual = {tuple(c['column_names']) for c in inspector.get_unique_constraints(table)}
        if not set(expected) <= actual: issues.append('growth_unique_missing:' + table)
    if inspector.has_table('users'):
        actual = {tuple(c['column_names']) for c in inspector.get_unique_constraints('users')}
        if ('referral_code',) not in actual: issues.append('referral_code_unique_missing')
    for table, expected in FKS.items():
        if not inspector.has_table(table): continue
        actual = {(tuple(c['constrained_columns']), tuple(c['referred_table'] + '.' + col for col in c['referred_columns']), c.get('options', {}).get('ondelete')) for c in inspector.get_foreign_keys(table)}
        if not set(expected) <= actual: issues.append('growth_fk_missing:' + table)
    return issues


def row_issues(connection):
    issues = []
    for table, rules in RULES.items():
        where = ' OR '.join('(' + predicate + ') IS FALSE' for _, predicate, _ in rules)
        if connection.exec_driver_sql('SELECT 1 FROM `' + table + '` WHERE ' + where + ' LIMIT 1').first():
            issues.append('row_rule_violation:' + table)
    if connection.exec_driver_sql("SELECT 1 FROM users WHERE role='customer' AND (referral_code IS NULL OR referral_code='') LIMIT 1").first():
        issues.append('missing_customer_referral_code')
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
    for sql in ALTER_COLUMNS: op.execute(sa.text(sql))
    for sql in TABLE_DDL.values(): op.execute(sa.text(sql))
    for sql in INDEX_DDL: op.execute(sa.text(sql))
    # Deterministic 96-bit public referral codes; email verification remains
    # unknown for legacy accounts until a real verification succeeds.
    op.execute(sa.text("UPDATE users SET referral_code=CONCAT('ME', UPPER(LEFT(SHA2(user_id,256),24))) WHERE referral_code IS NULL"))
    if context.is_offline_mode():
        output = op.get_context().impl.static_output
        output('DELIMITER $$')
        for name, definition in trigger_definitions().items():
            output('DROP TRIGGER IF EXISTS `' + name + '`$$')
            output(definition['sql'] + '$$')
        output('DELIMITER ;')
        return
    conn = op.get_bind()
    issues = table_issues(conn) + row_issues(conn)
    if issues: raise RuntimeError('Customer growth migration preflight failed: ' + ', '.join(issues))
    for name, definition in trigger_definitions().items():
        op.execute(sa.text('DROP TRIGGER IF EXISTS `' + name + '`'))
        op.execute(sa.text(definition['sql']))
    issues = table_issues(conn) + row_issues(conn) + trigger_issues(conn)
    if issues: raise RuntimeError('Customer growth migration audit failed: ' + ', '.join(issues))


def downgrade():
    raise RuntimeError('Customer rewards and COD history require a reviewed backup and reconciliation before downgrade.')
