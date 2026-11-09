"""MySQL 5.7.24 compatibility: enforce row rules with validation triggers.

Revision ID: 20261106_0002
Revises: 20261106_0001

Frozen snapshot: no imports of current application models or dynamic metadata.
No tables or business data are dropped or rewritten during upgrade. CHECK is
not enforced by MySQL 5.7; both INSERT and UPDATE need explicit validation.
"""
from __future__ import annotations

import re

from alembic import context, op
import sqlalchemy as sa

revision = "20261106_0002"
down_revision = "20261106_0001"
branch_labels = None
depends_on = None

EXPECTED_SQL_MODES = frozenset({
    "STRICT_TRANS_TABLES", "ERROR_FOR_DIVISION_BY_ZERO", "NO_ENGINE_SUBSTITUTION",
    "ONLY_FULL_GROUP_BY", "NO_ZERO_DATE", "NO_ZERO_IN_DATE",
})

# Frozen tuples: (rule name, quoted row predicate, NEW-qualified predicate).
RULES = {'articles': (('ck_articles_status',
               "`status` IN ('draft','published','unpublished','archived')",
               "NEW.`status` IN ('draft','published','unpublished','archived')"),
              ('ck_articles_views', '`view_count` >= 0', 'NEW.`view_count` >= 0')),
 'banners': (('ck_banners_link_type',
              '`link_type` IN '
              "('internal','product','category','shop_now','flash_sale','article','external','none')",
              'NEW.`link_type` IN '
              "('internal','product','category','shop_now','flash_sale','article','external','none')"),
             ('ck_banners_target_device',
              "`target_device` IN ('desktop','mobile','all')",
              "NEW.`target_device` IN ('desktop','mobile','all')"),
             ('ck_banners_window',
              '`start_at` IS NULL OR `end_at` IS NULL OR `end_at` > `start_at`',
              'NEW.`start_at` IS NULL OR NEW.`end_at` IS NULL OR NEW.`end_at` > NEW.`start_at`')),
 'cart_items': (('ck_cart_items_lens_variant_owner',
                 '`lens_variant_id` IS NULL OR `lens_product_id` IS NOT NULL',
                 'NEW.`lens_variant_id` IS NULL OR NEW.`lens_product_id` IS NOT NULL'),
                ('ck_cart_items_quantity', '`quantity` > 0', 'NEW.`quantity` > 0')),
 'categories': (('ck_categories_level_nonnegative', '`level` >= 0', 'NEW.`level` >= 0'),
                ('ck_categories_not_own_parent',
                 '`parent_id` IS NULL OR `parent_id` <> `id`',
                 'NEW.`parent_id` IS NULL OR NEW.`parent_id` <> NEW.`id`')),
 'cms_pages': (('ck_cms_pages_page_type',
                '`page_type` IN '
                "('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')",
                'NEW.`page_type` IN '
                "('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')"),
               ('ck_cms_pages_status',
                "`status` IN ('draft','published','unpublished','archived')",
                "NEW.`status` IN ('draft','published','unpublished','archived')"),
               ('ck_cms_pages_version', '`version` > 0', 'NEW.`version` > 0')),
 'contact_messages': (('ck_contact_messages_status',
                       "`status` IN ('new','read','replied')",
                       "NEW.`status` IN ('new','read','replied')"),),
 'contact_settings': (('ck_contact_settings_singleton', '`singleton_key` = 1', 'NEW.`singleton_key` = 1'),),
 'flash_sale_categories': (('ck_flash_sale_categories_amounts',
                            '`discount_value` >= 0 AND `quota_per_product` >= 0',
                            'NEW.`discount_value` >= 0 AND NEW.`quota_per_product` >= 0'),
                           ('ck_flash_sale_categories_percentage',
                            "`discount_type` <> 'percent' OR `discount_value` <= 100",
                            "NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100"),
                           ('ck_flash_sale_categories_type',
                            "`discount_type` IN ('percent','nominal','fixed_price')",
                            "NEW.`discount_type` IN ('percent','nominal','fixed_price')")),
 'flash_sale_items': (('ck_flash_sale_items_price', '`flash_price` >= 0', 'NEW.`flash_price` >= 0'),
                      ('ck_flash_sale_items_quota',
                       '`quota` >= 0 AND `sold` >= 0 AND `reserved` >= 0 AND `sold` + `reserved` <= `quota`',
                       'NEW.`quota` >= 0 AND NEW.`sold` >= 0 AND NEW.`reserved` >= 0 AND NEW.`sold` + '
                       'NEW.`reserved` <= NEW.`quota`')),
 'flash_sale_reservations': (('ck_flash_sale_reservations_quantity', '`quantity` > 0', 'NEW.`quantity` > 0'),
                             ('ck_flash_sale_reservations_status',
                              "`status` IN ('active','confirmed','expired','cancelled')",
                              "NEW.`status` IN ('active','confirmed','expired','cancelled')")),
 'flash_sales': (('ck_flash_sales_window', '`end_at` > `start_at`', 'NEW.`end_at` > NEW.`start_at`'),),
 'game_scores': (('ck_game_scores_scores',
                  '`score` >= 0 AND `points_awarded` >= 0',
                  'NEW.`score` >= 0 AND NEW.`points_awarded` >= 0'),),
 'games': (('ck_games_max_points', '`max_points` >= 0', 'NEW.`max_points` >= 0'),),
 'integration_webhook_events': (('ck_integration_webhook_events_attempts',
                                 '`attempts` >= 0',
                                 'NEW.`attempts` >= 0'),
                                ('ck_integration_webhook_events_status',
                                 "`status` IN ('received','processed','failed','ignored')",
                                 "NEW.`status` IN ('received','processed','failed','ignored')")),
 'lens_indexes': (('ck_lens_indexes_price', '`additional_price` >= 0', 'NEW.`additional_price` >= 0'),),
 'migration_issues': (('ck_migration_issues_severity',
                       "`severity` IN ('info','warning','error')",
                       "NEW.`severity` IN ('info','warning','error')"),),
 'migration_records': (('ck_migration_records_status',
                        "`status` IN ('planned','imported','verified','rejected')",
                        "NEW.`status` IN ('planned','imported','verified','rejected')"),),
 'migration_runs': (('ck_migration_runs_counts',
                     '`source_count` >= 0 AND `migrated_count` >= 0 AND `rejected_count` >= 0',
                     'NEW.`source_count` >= 0 AND NEW.`migrated_count` >= 0 AND NEW.`rejected_count` >= 0'),
                    ('ck_migration_runs_status',
                     "`status` IN ('planned','running','validated','failed','completed')",
                     "NEW.`status` IN ('planned','running','validated','failed','completed')")),
 'newsletter_campaigns': (('ck_newsletter_campaigns_counts',
                           '`sent_count` >= 0 AND `failed_count` >= 0',
                           'NEW.`sent_count` >= 0 AND NEW.`failed_count` >= 0'),),
 'order_item_components': (('ck_order_item_components_amounts',
                            '`quantity` > 0 AND `unit_price` >= 0 AND `subtotal` >= 0 AND `index_surcharge` '
                            '>= 0',
                            'NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND '
                            'NEW.`index_surcharge` >= 0'),
                           ('ck_order_item_components_type',
                            "`component_type` IN ('primary','lens')",
                            "NEW.`component_type` IN ('primary','lens')")),
 'order_items': (('ck_order_items_amounts',
                  '`quantity` > 0 AND `unit_price` >= 0 AND `subtotal` >= 0',
                  'NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0'),),
 'order_reviews': (('ck_order_reviews_rating', '`rating` BETWEEN 1 AND 5', 'NEW.`rating` BETWEEN 1 AND 5'),
                   ('ck_order_reviews_status',
                    "`status` IN ('pending','approved','rejected','hidden')",
                    "NEW.`status` IN ('pending','approved','rejected','hidden')")),
 'orders': (('ck_orders_amounts',
             '`points_used` >= 0 AND `points_discount` >= 0 AND `roulette_discount` >= 0 AND `shipping_cost` '
             '>= 0 AND `total` >= 0',
             'NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND '
             'NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0'),
            ('ck_orders_discount_amounts',
             '`subtotal` >= 0 AND `discount` >= 0 AND `flash_sale_discount` >= 0 AND `voucher_discount` >= 0',
             'NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND '
             'NEW.`voucher_discount` >= 0'),
            ('ck_orders_payment_status',
             "`payment_status` IN ('pending','paid','failed','expired','cancelled','refunded')",
             "NEW.`payment_status` IN ('pending','paid','failed','expired','cancelled','refunded')"),
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
 'payments': (('ck_payments_amount', '`amount` >= 0', 'NEW.`amount` >= 0'),
              ('ck_payments_status',
               "`status` IN ('pending','paid','failed','expired','cancelled','refunded')",
               "NEW.`status` IN ('pending','paid','failed','expired','cancelled','refunded')")),
 'point_logs': (('ck_point_logs_balance', '`balance_after` >= 0', 'NEW.`balance_after` >= 0'),),
 'prescription_eyes': (('ck_prescription_eyes_axis',
                        '`axis` IS NULL OR `axis` BETWEEN 0 AND 180',
                        'NEW.`axis` IS NULL OR NEW.`axis` BETWEEN 0 AND 180'),
                       ('ck_prescription_eyes_eye',
                        "`eye` IN ('right','left')",
                        "NEW.`eye` IN ('right','left')")),
 'prescriptions': (('ck_prescriptions_pd_left',
                    '`pd_left` IS NULL OR `pd_left` > 0',
                    'NEW.`pd_left` IS NULL OR NEW.`pd_left` > 0'),
                   ('ck_prescriptions_pd_mode',
                    '`pd_total` IS NULL OR (`pd_right` IS NULL AND `pd_left` IS NULL)',
                    'NEW.`pd_total` IS NULL OR (NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL)'),
                   ('ck_prescriptions_pd_pair',
                    '(`pd_right` IS NULL AND `pd_left` IS NULL) OR (`pd_right` IS NOT NULL AND `pd_left` IS '
                    'NOT NULL)',
                    '(NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL) OR (NEW.`pd_right` IS NOT NULL AND '
                    'NEW.`pd_left` IS NOT NULL)'),
                   ('ck_prescriptions_pd_right',
                    '`pd_right` IS NULL OR `pd_right` > 0',
                    'NEW.`pd_right` IS NULL OR NEW.`pd_right` > 0'),
                   ('ck_prescriptions_pd_total',
                    '`pd_total` IS NULL OR `pd_total` > 0',
                    'NEW.`pd_total` IS NULL OR NEW.`pd_total` > 0')),
 'product_knowledge_bullets': (('ck_product_knowledge_bullets_kind',
                                "`kind` IN ('pro','con')",
                                "NEW.`kind` IN ('pro','con')"),),
 'product_knowledges': (('ck_product_knowledges_status',
                         "`status` IN ('draft','published','unpublished','archived')",
                         "NEW.`status` IN ('draft','published','unpublished','archived')"),
                        ('ck_product_knowledges_type',
                         '`knowledge_type` IN '
                         "('frame_shape','material','lens_type','lens_index','buying_guide')",
                         'NEW.`knowledge_type` IN '
                         "('frame_shape','material','lens_type','lens_index','buying_guide')")),
 'product_reviews': (('ck_product_reviews_line_requires_order',
                      '(`order_item_id` IS NULL AND `order_component_id` IS NULL) OR `order_id` IS NOT NULL',
                      '(NEW.`order_item_id` IS NULL AND NEW.`order_component_id` IS NULL) OR NEW.`order_id` '
                      'IS NOT NULL'),
                     ('ck_product_reviews_one_purchase_line',
                      '`order_item_id` IS NULL OR `order_component_id` IS NULL',
                      'NEW.`order_item_id` IS NULL OR NEW.`order_component_id` IS NULL'),
                     ('ck_product_reviews_rating',
                      '`rating` BETWEEN 1 AND 5',
                      'NEW.`rating` BETWEEN 1 AND 5'),
                     ('ck_product_reviews_status',
                      "`status` IN ('pending','approved','rejected','hidden')",
                      "NEW.`status` IN ('pending','approved','rejected','hidden')"),
                     ('ck_product_reviews_verified_purchase',
                      '`verified_purchase` = 0 OR (`order_id` IS NOT NULL AND (`order_item_id` IS NOT NULL '
                      'OR `order_component_id` IS NOT NULL))',
                      'NEW.`verified_purchase` = 0 OR (NEW.`order_id` IS NOT NULL AND (NEW.`order_item_id` '
                      'IS NOT NULL OR NEW.`order_component_id` IS NOT NULL))')),
 'product_variants': (('ck_product_variants_inventory',
                       '`stock` >= 0 AND `reserved` >= 0 AND `reserved` <= `stock`',
                       'NEW.`stock` >= 0 AND NEW.`reserved` >= 0 AND NEW.`reserved` <= NEW.`stock`'),
                      ('ck_product_variants_price',
                       '`price_override` IS NULL OR `price_override` >= 0',
                       'NEW.`price_override` IS NULL OR NEW.`price_override` >= 0')),
 'products': (('ck_products_counters',
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
               "`product_type` IN ('frame','lens','package')",
               "NEW.`product_type` IN ('frame','lens','package')")),
 'roulette_redemptions': (('ck_roulette_redemptions_discount',
                           '`discount_amount` >= 0',
                           'NEW.`discount_amount` >= 0'),
                          ('ck_roulette_redemptions_status',
                           "`status` IN ('reserved','redeemed','released')",
                           "NEW.`status` IN ('reserved','redeemed','released')")),
 'roulette_rewards': (('ck_roulette_rewards_amounts',
                       '`value` >= 0 AND `probability` >= 0',
                       'NEW.`value` >= 0 AND NEW.`probability` >= 0'),
                      ('ck_roulette_rewards_type',
                       "`type` IN ('points','voucher','free_shipping','discount','nothing')",
                       "NEW.`type` IN ('points','voucher','free_shipping','discount','nothing')")),
 'roulette_spins': (('ck_roulette_spins_value', '`reward_value` >= 0', 'NEW.`reward_value` >= 0'),),
 'shipments': (('ck_shipments_cost', '`cost` >= 0', 'NEW.`cost` >= 0'),
               ('ck_shipments_status',
                '`status` IN '
                "('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')",
                'NEW.`status` IN '
                "('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')")),
 'shipping_quotes': (('ck_shipping_quotes_amounts',
                      '`weight_gram` > 0 AND `cost` >= 0 AND `insurance_cost` >= 0',
                      'NEW.`weight_gram` > 0 AND NEW.`cost` >= 0 AND NEW.`insurance_cost` >= 0'),),
 'stock_movements': (('ck_stock_movements_quantity', '`quantity` >= 0', 'NEW.`quantity` >= 0'),
                     ('ck_stock_movements_reserved_after',
                      '`reserved_after` IS NULL OR `reserved_after` >= 0',
                      'NEW.`reserved_after` IS NULL OR NEW.`reserved_after` >= 0'),
                     ('ck_stock_movements_stock_after',
                      '`stock_after` IS NULL OR `stock_after` >= 0',
                      'NEW.`stock_after` IS NULL OR NEW.`stock_after` >= 0')),
 'stock_reservations': (('ck_stock_reservations_quantity', '`quantity` > 0', 'NEW.`quantity` > 0'),
                        ('ck_stock_reservations_status',
                         "`status` IN ('active','confirmed','expired','cancelled')",
                         "NEW.`status` IN ('active','confirmed','expired','cancelled')")),
 'uploads': (('ck_uploads_size', '`size` >= 0', 'NEW.`size` >= 0'),
             ('ck_uploads_visibility',
              "`visibility` IN ('public','private')",
              "NEW.`visibility` IN ('public','private')")),
 'users': (('ck_users_pin_attempts_nonnegative',
            '`pin_failed_attempts` >= 0',
            'NEW.`pin_failed_attempts` >= 0'),
           ('ck_users_points_nonnegative', '`points_balance` >= 0', 'NEW.`points_balance` >= 0'),
           ('ck_users_role',
            "`role` IN ('customer','staff','admin','super_admin')",
            "NEW.`role` IN ('customer','staff','admin','super_admin')")),
 'virtual_try_on_assets': (('ck_virtual_try_on_assets_asset_type',
                            "`asset_type` IN ('image','glb','gltf')",
                            "NEW.`asset_type` IN ('image','glb','gltf')"),
                           ('ck_virtual_try_on_assets_scale', '`scale` > 0', 'NEW.`scale` > 0'),
                           ('ck_virtual_try_on_assets_source',
                            '`upload_id` IS NOT NULL OR `source_url` IS NOT NULL',
                            'NEW.`upload_id` IS NOT NULL OR NEW.`source_url` IS NOT NULL'),
                           ('ck_virtual_try_on_assets_status',
                            "`status` IN ('draft','published','archived')",
                            "NEW.`status` IN ('draft','published','archived')")),
 'voucher_redemptions': (('ck_voucher_redemptions_amount',
                          '`discount_amount` >= 0',
                          'NEW.`discount_amount` >= 0'),
                         ('ck_voucher_redemptions_status',
                          "`status` IN ('reserved','redeemed','released')",
                          "NEW.`status` IN ('reserved','redeemed','released')")),
 'vouchers': (('ck_vouchers_amounts',
               '`discount_value` >= 0 AND `min_purchase` >= 0 AND (`max_discount` IS NULL OR `max_discount` '
               '>= 0)',
               'NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR '
               'NEW.`max_discount` >= 0)'),
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
 'whatsapp_settings': (('ck_whatsapp_settings_singleton', '`id` = 1', 'NEW.`id` = 1'),)}
ALL_TABLES = ('addresses',
 'article_categories',
 'article_tags',
 'articles',
 'banners',
 'brands',
 'cart_items',
 'categories',
 'cms_pages',
 'contact_messages',
 'contact_settings',
 'faq_categories',
 'faqs',
 'flash_sale_categories',
 'flash_sale_items',
 'flash_sale_reservations',
 'flash_sales',
 'game_scores',
 'games',
 'integration_webhook_events',
 'lens_indexes',
 'migration_issues',
 'migration_records',
 'migration_runs',
 'newsletter_campaigns',
 'newsletter_subscribers',
 'order_addresses',
 'order_item_components',
 'order_item_prescriptions',
 'order_items',
 'order_reviews',
 'order_status_logs',
 'orders',
 'payment_logs',
 'payments',
 'point_logs',
 'prescription_eyes',
 'prescriptions',
 'product_badges',
 'product_categories',
 'product_images',
 'product_knowledge_bullets',
 'product_knowledge_products',
 'product_knowledges',
 'product_review_images',
 'product_reviews',
 'product_segments',
 'product_subscriptions',
 'product_variants',
 'products',
 'roulette_redemptions',
 'roulette_rewards',
 'roulette_spins',
 'settings',
 'shipment_logs',
 'shipments',
 'shipping_quotes',
 'stock_movements',
 'stock_reservations',
 'uploads',
 'user_permissions',
 'user_sessions',
 'users',
 'virtual_try_on_assets',
 'voucher_redemptions',
 'vouchers',
 'whatsapp_settings',
 'wishlists')


def trigger_definitions() -> dict[str, dict[str, str]]:
    definitions = {}
    for table, rules in RULES.items():
        for event, prefix in (("INSERT", "bi"), ("UPDATE", "bu")):
            name = f"{prefix}_{table}_mysql57_guard"
            lines = ["BEGIN"]
            for rule_name, _, predicate in rules:
                lines.extend([
                    f"  IF ({predicate}) IS FALSE THEN",
                    "    SIGNAL SQLSTATE '45000'",
                    f"      SET MESSAGE_TEXT = 'Integrity rule {rule_name} failed';",
                    "  END IF;",
                ])
            lines.append("END")
            body = "\n".join(lines)
            definitions[name] = {
                "table": table, "event": event, "timing": "BEFORE", "body": body,
                "sql": f"CREATE TRIGGER `{name}` BEFORE {event} ON `{table}`\nFOR EACH ROW\n{body}",
            }
    return definitions


def canonical_body(body: str) -> tuple[str, ...]:
    """Ignore formatting/identifier case; preserve string-literal contents."""
    tokens = re.findall(r"'(?:''|[^'])*'|`(?:``|[^`])*`|[A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?|[^\s]", body)
    return tuple(token if token.startswith("'") else token.strip("`").lower() for token in tokens)


def table_issues(connection) -> list[str]:
    rows = connection.execute(sa.text(
        "SELECT TABLE_NAME AS table_name, ENGINE AS engine, ROW_FORMAT AS row_format "
        "FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()"
    )).mappings()
    actual = {row["table_name"]: row for row in rows}
    issues = []
    for table in ALL_TABLES:
        row = actual.get(table)
        if row is None:
            issues.append(f"missing_table:{table}")
        elif str(row["engine"]).lower() != "innodb" or str(row["row_format"]).lower() != "dynamic":
            issues.append(f"table_storage_mismatch:{table}")
    return issues


def row_issues(connection) -> list[str]:
    """Report table names only; never include customer/order/prescription data."""
    issues = []
    for table, rules in RULES.items():
        where = " OR ".join(f"({predicate}) IS FALSE" for _, predicate, _ in rules)
        # All identifiers and expressions are frozen migration constants.
        if connection.exec_driver_sql(f"SELECT 1 FROM `{table}` WHERE {where} LIMIT 1").first():
            issues.append(f"row_rule_violation:{table}")
    return issues


def installed_triggers(connection) -> dict[str, dict]:
    rows = connection.execute(sa.text(
        "SELECT TRIGGER_NAME AS name, EVENT_MANIPULATION AS event, "
        "EVENT_OBJECT_TABLE AS table_name, ACTION_TIMING AS timing, ACTION_STATEMENT AS body, "
        "SQL_MODE AS sql_mode, ACTION_ORDER AS action_order "
        "FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE()"
    )).mappings()
    return {row["name"]: dict(row) for row in rows}


def trigger_issues(connection, *, allow_missing: bool = False) -> list[str]:
    actual = installed_triggers(connection)
    issues = []
    for name, expected in trigger_definitions().items():
        row = actual.get(name)
        if row is None:
            if not allow_missing:
                issues.append(f"missing_trigger:{name}")
        elif (row["table_name"] != expected["table"] or row["event"] != expected["event"]
              or row["timing"] != "BEFORE" or canonical_body(row["body"]) != canonical_body(expected["body"])):
            issues.append(f"trigger_definition_mismatch:{name}")
        else:
            modes = {mode.strip().upper() for mode in row["sql_mode"].split(",") if mode.strip()}
            if modes != EXPECTED_SQL_MODES:
                issues.append(f"trigger_sql_mode_mismatch:{name}")
            # Another BEFORE trigger must not mutate NEW values after validation.
            last_order = max(int(candidate["action_order"]) for candidate in actual.values()
                             if candidate["table_name"] == row["table_name"]
                             and candidate["event"] == row["event"] and candidate["timing"] == "BEFORE")
            if int(row["action_order"]) != last_order:
                issues.append(f"trigger_not_last:{name}")
    return issues


def upgrade() -> None:
    definitions = trigger_definitions()
    if context.is_offline_mode():
        output = op.get_context().impl.static_output
        output("-- MySQL 5.7 validation guards. For populated targets, pause writers and run")
        output("-- python -m mysql.check_integrity --preflight-only BEFORE applying this SQL.")
        output("-- Stop on the first error. Do not use mysql --force. Requires TRIGGER privileges.")
        output("DELIMITER $$")
        for definition in definitions.values():
            output(definition["sql"] + "$$")
        output("DELIMITER ;")
        return

    connection = op.get_bind()
    issues = table_issues(connection)
    if issues:
        raise RuntimeError("MySQL 5.7 schema preflight failed: " + ", ".join(issues))
    issues = row_issues(connection)
    if issues:
        raise RuntimeError("Existing data violates integrity rules; no triggers were installed: " + ", ".join(issues))
    issues = trigger_issues(connection, allow_missing=True)
    if issues:
        raise RuntimeError("Existing trigger definitions differ; no triggers were replaced: " + ", ".join(issues))
    # DDL is not transactional in MySQL. A retry can resume a partial install
    # only if already-created guards exactly match this immutable revision.
    existing = installed_triggers(connection)
    for name, definition in definitions.items():
        if name not in existing:
            connection.exec_driver_sql(definition["sql"])
    remaining = trigger_issues(connection)
    # A final scan catches a concurrent invalid write that arrived after the
    # initial scan but before its table's guards were installed. Prefer paused
    # writers for deployments; do not stamp the revision with invalid rows.
    remaining.extend(row_issues(connection))
    if remaining:
        raise RuntimeError("MySQL 5.7 integrity verification failed: " + ", ".join(remaining))


def downgrade() -> None:
    if not context.is_offline_mode():
        if context.get_x_argument(as_dictionary=True).get("allow_schema_drop") != "true":
            raise RuntimeError("Removing validation guards requires -x allow_schema_drop=true on a disposable target only.")
    for name in reversed(trigger_definitions()):
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS `{name}`"))
