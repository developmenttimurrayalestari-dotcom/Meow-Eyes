from pathlib import Path
root = Path(__file__).resolve().parents[2]
p = root / 'backend/mysql/commerce.py'
s = p.read_text(encoding='utf-8')
old = '''    max_points = int(max(ZERO, subtotal - voucher_discount - roulette_discount) // POINT_VALUE)
    requested_points = integer(req.use_points or 0, "Poin", 0, 9223372036854775807)
    points_used = 0 if flash_sale_exclusive else min(requested_points, user.points_balance, max_points)
    points_discount = POINT_VALUE * points_used'''
new = '''    from mysql.points import quote as point_quote
    requested_points = integer(req.use_points or 0, "Poin", 0, 9223372036854775807)
    points_used, points_discount, point_plan = await point_quote(s, user, 0 if flash_sale_exclusive else requested_points,
        max(ZERO, subtotal - voucher_discount - roulette_discount))'''
assert old in s; s = s.replace(old, new)
s = s.replace('    total: Decimal\n\n    def payload', '    total: Decimal\n    point_plan: list | None = None\n\n    def payload')
s = s.replace('roulette, money(roulette_discount), free_shipping, total)', 'roulette, money(roulette_discount), free_shipping, total, point_plan)')
old = '''    if quote.points_used:
        quote.user.points_balance -= quote.points_used
        s.add(m.PointLog(
            id=gen_id("pts"), user_id=order.user_id, delta=-quote.points_used,
            balance_after=quote.user.points_balance, type="redeem_checkout",
            note=order.order_number, order_id=order.id,
        ))'''
new = '''    from mysql.points import reserve as reserve_points, snapshot_cashback
    await reserve_points(s, quote.user, order, quote.point_plan or [])
    await snapshot_cashback(s, order)'''
assert old in s; s = s.replace(old, new)
old = '''    if order.points_used:
        user.points_balance += order.points_used
        s.add(m.PointLog(
            id=gen_id("pts"), user_id=user.user_id, delta=order.points_used,
            balance_after=user.points_balance, type="refund_point", order_id=order.id,
            note=order.order_number + " (" + status + ")",
        ))'''
new = '''    from mysql.points import release as release_points
    await release_points(s, user, order, status)'''
assert old in s; s = s.replace(old, new)
s = s.replace('                order.completed_at = utcnow()', '                order.completed_at = utcnow()\n                from mysql.points import complete_order as complete_point_order\n                await complete_point_order(s, user, order)')
p.write_text(s, encoding='utf-8')
p = root / 'backend/routes_orders.py';s = p.read_text(encoding='utf-8')
s = s.replace('''    async with read_session() as s:
        fresh = await s.get(m.User, user.user_id)
        if fresh is None or not fresh.is_active:
            raise HTTPException(403, "Akun tidak tersedia")
        return (await checkout_quote(s, fresh, req)).payload()''', '''    from mysql.commerce import lock_user
    async with session_scope() as s:
        fresh = await lock_user(s, user.user_id)
        return (await checkout_quote(s, fresh, req)).payload()''')
p.write_text(s, encoding='utf-8')
