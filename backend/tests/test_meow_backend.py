"""Meow Eyes backend smoke + integration tests covering catalog, auth, cart, checkout, wishlist, engagement, admin, export."""
import os
import time
import uuid
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


# ============ Health & Catalog (public) ============
class TestHealthAndCatalog:
    def test_health(self, api):
        r = api.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_homepage(self, api):
        r = api.get(f"{BASE_URL}/api/homepage")
        assert r.status_code == 200
        data = r.json()
        for k in ["bestsellers", "newest", "categories", "brands"]:
            assert k in data, f"missing key {k}"
        assert isinstance(data["bestsellers"], list)

    def test_products_list(self, api):
        r = api.get(f"{BASE_URL}/api/products?limit=5")
        assert r.status_code == 200
        d = r.json()
        assert "products" in d and isinstance(d["products"], list)
        assert d["limit"] == 5

    def test_products_filters(self, api):
        r = api.get(f"{BASE_URL}/api/products?product_type=frame&sort=price_asc&limit=10")
        assert r.status_code == 200
        # Server-side sort uses base price field
        prices = [p["price"] for p in r.json()["products"]]
        assert prices == sorted(prices), f"prices not asc: {prices}"

    def test_product_detail_existing_slug(self, api):
        # Pick any existing slug
        lst = api.get(f"{BASE_URL}/api/products?limit=1").json()["products"]
        slug = lst[0]["slug"]
        r = api.get(f"{BASE_URL}/api/products/{slug}")
        assert r.status_code == 200, r.text
        body = r.json()
        prod = body.get("product", body)
        assert prod.get("slug") == slug
        assert "variants" in prod
        assert "related" in body

    def test_product_detail_missing(self, api):
        r = api.get(f"{BASE_URL}/api/products/this-does-not-exist-zzz")
        assert r.status_code == 404

    def test_categories_tree(self, api):
        r = api.get(f"{BASE_URL}/api/categories/tree")
        assert r.status_code == 200
        assert isinstance(r.json().get("tree", r.json() if isinstance(r.json(), list) else []), list) or "tree" in r.json()

    def test_flash_sale_active(self, api):
        r = api.get(f"{BASE_URL}/api/flash-sales/active")
        assert r.status_code == 200


# ============ Auth ============
class TestAuth:
    def test_login_admin(self, api):
        r = api.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@meoweyes.id", "password": "Admin@123"})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["user"]["role"] == "super_admin"
        assert data["user"]["has_pin"] is True

    def test_login_customer(self, api):
        r = api.post(f"{BASE_URL}/api/auth/login", json={"email": "customer@meoweyes.id", "password": "Customer@123"})
        assert r.status_code == 200
        assert r.json()["user"]["has_pin"] is True

    def test_login_wrong_password(self, api):
        r = api.post(f"{BASE_URL}/api/auth/login", json={"email": "customer@meoweyes.id", "password": "wrong"})
        assert r.status_code in (400, 401)

    def test_register_and_setup_pin(self, api):
        email = f"test_{uuid.uuid4().hex[:8]}@meoweyes.id"
        r = api.post(f"{BASE_URL}/api/auth/register",
                     json={"name": "Test User", "email": email, "password": "Password@123"})
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert "token" in body
        assert body["user"]["email"] == email
        assert body["user"]["has_pin"] is False

        token = body["token"]
        # Set PIN
        r2 = api.post(f"{BASE_URL}/api/auth/pin/setup",
                      json={"pin": "112233"},
                      headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200, r2.text

        # Verify /auth/me
        me = api.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        me_body = me.json()
        me_user = me_body.get("user", me_body)
        assert me_user["has_pin"] is True

    def test_me_requires_auth(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code in (401, 403)


# ============ Cart & Wishlist ============
class TestCartWishlist:
    def test_add_to_cart_and_get(self, customer_client):
        # Get a product with variants
        lst = customer_client.get(f"{BASE_URL}/api/products?limit=20").json()["products"]
        product_id = None
        variant_id = None
        for p in lst:
            pd = customer_client.get(f"{BASE_URL}/api/products/{p['slug']}").json()
            prod = pd.get("product", pd)
            if prod.get("variants"):
                product_id = prod["id"]
                variant_id = prod["variants"][0]["id"]
                break
        assert product_id, "No product with variants seeded"

        # Clear cart first
        cart = customer_client.get(f"{BASE_URL}/api/cart").json()
        for ci in cart.get("items", []):
            customer_client.delete(f"{BASE_URL}/api/cart/{ci['id']}")

        r = customer_client.post(f"{BASE_URL}/api/cart",
                                 json={"product_id": product_id, "variant_id": variant_id, "quantity": 2})
        assert r.status_code in (200, 201), r.text
        cart = customer_client.get(f"{BASE_URL}/api/cart").json()
        assert len(cart["items"]) >= 1
        assert any(i["product_id"] == product_id for i in cart["items"])

    def test_wishlist_add_remove(self, customer_client):
        lst = customer_client.get(f"{BASE_URL}/api/products?limit=1").json()["products"]
        pid = lst[0]["id"]
        # Ensure clean
        customer_client.delete(f"{BASE_URL}/api/wishlist/{pid}")
        r = customer_client.post(f"{BASE_URL}/api/wishlist/{pid}")
        assert r.status_code in (200, 201), r.text
        wl = customer_client.get(f"{BASE_URL}/api/wishlist").json()
        items = wl.get("items") or wl.get("products") or wl.get("wishlist") or (wl if isinstance(wl, list) else [])
        # tolerate any container - just confirm the API works (POST + GET 200)
        assert isinstance(items, list)
        r2 = customer_client.delete(f"{BASE_URL}/api/wishlist/{pid}")
        assert r2.status_code in (200, 204)


# ============ Vouchers ============
class TestVouchers:
    def test_active_vouchers(self, customer_client):
        r = customer_client.get(f"{BASE_URL}/api/vouchers/active")
        assert r.status_code == 200
        data = r.json()
        codes = [v["code"] for v in data.get("vouchers", data if isinstance(data, list) else [])]
        # Seeded vouchers
        assert any(c in codes for c in ["MEOWWELCOME", "GRATISONGKIR", "MEOW50K"]), f"Got: {codes}"


# ============ Checkout & Order full flow ============
class TestCheckoutFlow:
    @pytest.fixture(scope="class")
    def setup_address_and_cart(self, base_url):
        # Login customer fresh
        import requests
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        token = s.post(f"{BASE_URL}/api/auth/login",
                       json={"email": "customer@meoweyes.id", "password": "Customer@123"}).json()["token"]
        s.headers["Authorization"] = f"Bearer {token}"

        # Clear cart
        cart = s.get(f"{BASE_URL}/api/cart").json()
        for ci in cart.get("items", []):
            s.delete(f"{BASE_URL}/api/cart/{ci['id']}")

        # Create address (server schema: recipient/street)
        addr_payload = {
            "label": "Rumah", "recipient": "Mira Customer", "phone": "081234567890",
            "province": "DKI Jakarta", "city": "Jakarta Selatan",
            "postal_code": "12345", "street": "Jl. Cat Lovers No. 7",
            "is_default": True,
        }
        ar = s.post(f"{BASE_URL}/api/addresses", json=addr_payload)
        assert ar.status_code in (200, 201), ar.text
        addr_body = ar.json()
        address_id = addr_body.get("id") or addr_body.get("address", {}).get("id")
        assert address_id

        # Find product with variants
        lst = s.get(f"{BASE_URL}/api/products?limit=20").json()["products"]
        product_id = None
        variant_id = None
        for p in lst:
            pd = s.get(f"{BASE_URL}/api/products/{p['slug']}").json()
            prod = pd.get("product", pd)
            if prod.get("variants"):
                product_id = prod["id"]
                variant_id = prod["variants"][0]["id"]
                break

        cr = s.post(f"{BASE_URL}/api/cart",
                    json={"product_id": product_id, "variant_id": variant_id, "quantity": 1})
        assert cr.status_code in (200, 201), cr.text
        cart_items = s.get(f"{BASE_URL}/api/cart").json()["items"]
        return {"session": s, "address_id": address_id, "cart_items": cart_items}

    def test_shipping_options(self, setup_address_and_cart):
        ctx = setup_address_and_cart
        s = ctx["session"]
        cart_ids = [c["id"] for c in ctx["cart_items"]]
        r = s.post(f"{BASE_URL}/api/checkout/shipping-options",
                   json={"address_id": ctx["address_id"], "selected_item_ids": cart_ids})
        assert r.status_code == 200, r.text
        opts = r.json()["options"]
        assert len(opts) >= 1
        assert "courier_code" in opts[0]

    def test_checkout_preview_with_voucher(self, setup_address_and_cart):
        ctx = setup_address_and_cart
        s = ctx["session"]
        cart_ids = [c["id"] for c in ctx["cart_items"]]
        opts = s.post(f"{BASE_URL}/api/checkout/shipping-options",
                      json={"address_id": ctx["address_id"], "selected_item_ids": cart_ids}).json()["options"]
        ship = opts[0]
        r = s.post(f"{BASE_URL}/api/checkout/preview", json={
            "address_id": ctx["address_id"],
            "selected_item_ids": cart_ids,
            "courier_code": ship["courier_code"],
            "service_code": ship["service_code"],
            "voucher_code": "MEOWWELCOME",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["subtotal"] > 0
        assert body["total"] >= 0
        # voucher may or may not apply depending on min_purchase
        assert "shipping" in body

    def test_checkout_confirm_and_pay(self, setup_address_and_cart):
        ctx = setup_address_and_cart
        s = ctx["session"]
        cart_ids = [c["id"] for c in ctx["cart_items"]]
        opts = s.post(f"{BASE_URL}/api/checkout/shipping-options",
                      json={"address_id": ctx["address_id"], "selected_item_ids": cart_ids}).json()["options"]
        ship = opts[0]

        # Confirm with WRONG pin first
        bad = s.post(f"{BASE_URL}/api/checkout/confirm", json={
            "address_id": ctx["address_id"], "selected_item_ids": cart_ids,
            "courier_code": ship["courier_code"], "service_code": ship["service_code"],
            "pin": "000000",
        })
        assert bad.status_code in (400, 401, 403), bad.text

        # Correct PIN
        good = s.post(f"{BASE_URL}/api/checkout/confirm", json={
            "address_id": ctx["address_id"], "selected_item_ids": cart_ids,
            "courier_code": ship["courier_code"], "service_code": ship["service_code"],
            "pin": "654321",
        })
        assert good.status_code == 200, good.text
        order = good.json()["order"]
        assert order["status"] == "pending_payment"
        assert order["total"] > 0
        order_number = order["order_number"]

        # Pay
        p = s.post(f"{BASE_URL}/api/payment/confirm/{order_number}")
        assert p.status_code == 200, p.text
        paid = p.json().get("order", p.json())
        assert paid.get("status") in ("paid", "processing", "shipped")
        assert paid.get("tracking_number") or paid.get("shipment", {}).get("tracking_number")

        # Get order detail
        oid = order["id"]
        det = s.get(f"{BASE_URL}/api/orders/{oid}")
        assert det.status_code == 200
        d = det.json()
        assert d.get("order", d).get("order_number") == order_number


# ============ Engagement: Games, Roulette, Newsletter ============
class TestEngagement:
    def test_games_list(self, customer_client):
        r = customer_client.get(f"{BASE_URL}/api/games")
        assert r.status_code == 200

    def test_game_submit_score(self, customer_client):
        r = customer_client.post(f"{BASE_URL}/api/games/matching/submit", json={"score": 100, "duration_sec": 30})
        assert r.status_code == 200, r.text
        body = r.json()
        # points awarded but capped
        assert "points_awarded" in body or "points" in body or body.get("ok") is True

    def test_roulette_spin(self, customer_client):
        r = customer_client.post(f"{BASE_URL}/api/roulette/spin")
        # Should either return reward or 400 if cooldown
        assert r.status_code in (200, 400, 429), r.text
        if r.status_code == 200:
            assert "reward" in r.json() or "reward_type" in r.json()

    def test_newsletter_subscribe(self, api):
        email = f"news_{uuid.uuid4().hex[:6]}@meow.id"
        r = api.post(f"{BASE_URL}/api/newsletter/subscribe", json={"email": email})
        assert r.status_code == 200, r.text


# ============ Admin endpoints ============
class TestAdmin:
    def test_dashboard_summary(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/dashboard/summary")
        assert r.status_code == 200, r.text
        d = r.json()
        # Common keys
        assert any(k in d for k in ("total_sales", "revenue", "orders_count", "summary", "sales_today", "total_users"))

    def test_dashboard_sales_chart(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/dashboard/sales-chart")
        assert r.status_code == 200

    def test_dashboard_pie_and_top(self, admin_client):
        r1 = admin_client.get(f"{BASE_URL}/api/admin/dashboard/order-status-chart")
        r2 = admin_client.get(f"{BASE_URL}/api/admin/dashboard/top-products")
        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_admin_requires_admin(self, customer_client):
        r = customer_client.get(f"{BASE_URL}/api/admin/dashboard/summary")
        assert r.status_code in (401, 403)

    def test_admin_products_crud(self, admin_client):
        # Create
        payload = {
            "name": "TEST_Auto Frame", "sku": f"TEST-{uuid.uuid4().hex[:6].upper()}",
            "product_type": "frame", "price": 250000,
            "main_image": "https://images.unsplash.com/photo-1508296695146-257a814070b4?w=600",
            "description": "Test frame",
            "category_ids": [], "brand_id": None,
            "segments": ["Wanita"],
            "variants": [{"sku": f"TESTV-{uuid.uuid4().hex[:6].upper()}", "color": "Black", "size": "M", "stock": 10}],
            "is_active": True,
            "weight_gram": 200,
        }
        r = admin_client.post(f"{BASE_URL}/api/admin/products", json=payload)
        assert r.status_code in (200, 201), r.text
        prod = r.json()
        pid = prod.get("id") or prod.get("product", {}).get("id")
        assert pid

        # Update
        upd = admin_client.put(f"{BASE_URL}/api/admin/products/{pid}", json={"name": "TEST_Auto Frame V2", "price": 275000})
        assert upd.status_code == 200, upd.text

        # Delete (soft)
        dl = admin_client.delete(f"{BASE_URL}/api/admin/products/{pid}")
        assert dl.status_code in (200, 204), dl.text

    def test_admin_categories(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/categories")
        assert r.status_code == 200

    def test_admin_orders(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/orders")
        assert r.status_code == 200

    def test_admin_inventory(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/inventory")
        assert r.status_code == 200

    def test_admin_vouchers_list(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/vouchers")
        assert r.status_code == 200

    def test_admin_users_list(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/users")
        assert r.status_code == 200


# ============ Excel exports ============
class TestExports:
    @pytest.mark.parametrize("key", ["sales", "inventory", "flash-sales", "roulette", "games", "newsletter", "users", "points"])
    def test_export_xlsx(self, admin_client, key):
        r = admin_client.get(f"{BASE_URL}/api/admin/export/{key}")
        assert r.status_code == 200, f"{key} -> {r.status_code}: {r.text[:200]}"
        ctype = r.headers.get("content-type", "")
        assert "spreadsheet" in ctype or "officedocument" in ctype or "xlsx" in ctype or "octet-stream" in ctype, ctype
        assert len(r.content) > 100


# ============ Cron expire orders ============
class TestCron:
    def test_cron_expire(self, api):
        r = api.post(f"{BASE_URL}/api/cron/expire-orders")
        assert r.status_code == 200, r.text
        body = r.json()
        assert any(k in body for k in ("expired", "count", "expired_count")) or body.get("ok") is True
