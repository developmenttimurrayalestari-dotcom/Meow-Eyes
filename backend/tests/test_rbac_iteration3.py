"""RBAC iteration 3 tests: staff permission enforcement + admin regression + voucher + checkout."""
import os
import time
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login {email} failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def staff():
    tok = _login("staff@meoweyes.id", "Staff@123")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {tok}"})
    return s


@pytest.fixture(scope="module")
def admin():
    tok = _login("admin@meoweyes.id", "Admin@123")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {tok}"})
    return s


@pytest.fixture(scope="module")
def customer():
    tok = _login("customer@meoweyes.id", "Customer@123")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {tok}"})
    return s


# ---------- P0: Staff permitted routes ----------
class TestStaffAllowed:
    def test_staff_get_articles(self, staff):
        r = staff.get(f"{BASE_URL}/api/admin/articles")
        assert r.status_code == 200, r.text
        assert "articles" in r.json()

    def test_staff_full_article_crud(self, staff):
        # CREATE
        r = staff.post(f"{BASE_URL}/api/admin/articles", json={
            "title": "TEST_Staff RBAC Article",
            "content": "<p>body</p>",
            "excerpt": "excerpt",
            "status": "published",
        })
        assert r.status_code == 200, r.text
        art = r.json()["article"]
        aid = art["id"]
        # UPDATE
        r2 = staff.put(f"{BASE_URL}/api/admin/articles/{aid}", json={"title": "TEST_Staff RBAC Article Updated"})
        assert r2.status_code == 200, r2.text
        # GET verify update
        r3 = staff.get(f"{BASE_URL}/api/admin/articles/{aid}")
        assert r3.status_code == 200
        assert r3.json()["article"]["title"] == "TEST_Staff RBAC Article Updated"
        # DELETE
        r4 = staff.delete(f"{BASE_URL}/api/admin/articles/{aid}")
        assert r4.status_code == 200
        # Verify gone
        r5 = staff.get(f"{BASE_URL}/api/admin/articles/{aid}")
        assert r5.status_code == 404

    def test_staff_get_reviews(self, staff):
        r = staff.get(f"{BASE_URL}/api/admin/reviews")
        assert r.status_code == 200, r.text
        assert "reviews" in r.json()

    def test_staff_moderate_review(self, staff, admin):
        # Find any review; create one via DB if not exist
        r = staff.get(f"{BASE_URL}/api/admin/reviews")
        reviews = r.json().get("reviews", [])
        if not reviews:
            pytest.skip("No reviews present to moderate")
        rid = reviews[0]["id"]
        r2 = staff.post(f"{BASE_URL}/api/admin/reviews/{rid}/moderate", json={"action": "approve"})
        assert r2.status_code == 200, r2.text

    def test_staff_reviews_analytics(self, staff):
        r = staff.get(f"{BASE_URL}/api/admin/reviews/analytics")
        assert r.status_code == 200, r.text


# ---------- P0: Staff denied routes (403) ----------
class TestStaffDenied:
    def test_staff_banners_403(self, staff):
        r = staff.get(f"{BASE_URL}/api/admin/banners-v2")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

    def test_staff_products_403(self, staff):
        r = staff.get(f"{BASE_URL}/api/admin/products")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

    def test_staff_staff_list_403(self, staff):
        r = staff.get(f"{BASE_URL}/api/admin/staff")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

    def test_staff_import_template_403(self, staff):
        r = staff.get(f"{BASE_URL}/api/admin/products/import/template")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"


# ---------- P0: Admin regression ----------
class TestAdminRegression:
    def test_admin_articles(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/articles")
        assert r.status_code == 200

    def test_admin_banners(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/banners-v2")
        assert r.status_code == 200

    def test_admin_products(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/products")
        assert r.status_code == 200

    def test_admin_staff_list(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/staff")
        assert r.status_code == 200

    def test_admin_reviews(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/reviews")
        assert r.status_code == 200

    def test_admin_import_template(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/products/import/template")
        assert r.status_code == 200
        assert "spreadsheet" in r.headers.get("content-type", "").lower()

    def test_admin_reviews_analytics(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/reviews/analytics")
        assert r.status_code == 200


# ---------- P0: Voucher active list ----------
class TestVouchers:
    def test_active_vouchers_returns_three(self):
        r = requests.get(f"{BASE_URL}/api/vouchers/active", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        vouchers = data.get("vouchers", data) if isinstance(data, dict) else data
        codes = {v.get("code") for v in vouchers}
        assert {"MEOWWELCOME", "GRATISONGKIR", "MEOW50K"}.issubset(codes), \
            f"Missing expected vouchers, got: {codes}"


# ---------- P0: Review gate — only status='completed' ----------
class TestReviewGate:
    """Confirm review requires order status='completed', 'shipped' no longer qualifies."""

    def _pin_setup(self, sess, pin="123456"):
        # try to set PIN; ignore if already set
        sess.post(f"{BASE_URL}/api/auth/pin/setup", json={"pin": pin})

    def test_shipped_order_review_rejected(self, customer):
        # Get MONGO_URL from backend env
        mongo_url = None
        db_name = None
        with open("/app/backend/.env") as f:
            for line in f:
                if line.startswith("MONGO_URL="):
                    mongo_url = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("DB_NAME="):
                    db_name = line.split("=", 1)[1].strip().strip('"')
        if not mongo_url or not db_name:
            pytest.skip("No mongo access")
        client = MongoClient(mongo_url)
        db = client[db_name]
        # Find a product
        prod = db.products.find_one({"is_active": True}, {"_id": 0, "id": 1})
        assert prod, "No product for test"
        pid = prod["id"]
        # Find customer user_id
        me = customer.get(f"{BASE_URL}/api/auth/me").json()
        uid = me.get("user", me).get("user_id")
        # Insert a shipped-only order containing this product
        from datetime import datetime, timezone
        order_id = f"ord_test_shipped_{int(time.time())}"
        db.orders.insert_one({
            "id": order_id,
            "user_id": uid,
            "status": "shipped",
            "items": [{"product_id": pid, "sku": "TEST", "name": "TEST", "quantity": 1, "unit_price": 100000}],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            r = customer.post(f"{BASE_URL}/api/products/{pid}/reviews", json={
                "order_id": order_id, "rating": 5, "body": "TEST shipped review body",
            })
            assert r.status_code == 400, f"Expected 400 (shipped != completed), got {r.status_code}: {r.text}"
        finally:
            db.orders.delete_one({"id": order_id})
            client.close()

    def test_completed_order_review_allowed(self, customer):
        mongo_url = None
        db_name = None
        with open("/app/backend/.env") as f:
            for line in f:
                if line.startswith("MONGO_URL="):
                    mongo_url = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("DB_NAME="):
                    db_name = line.split("=", 1)[1].strip().strip('"')
        client = MongoClient(mongo_url)
        db = client[db_name]
        # Fresh product to avoid duplicate-review conflicts
        products = list(db.products.find({"is_active": True}, {"_id": 0, "id": 1}).limit(50))
        me = customer.get(f"{BASE_URL}/api/auth/me").json()
        uid = me.get("user", me).get("user_id")
        # Choose product without existing review by this user
        chosen = None
        for p in products:
            existing = db.product_reviews.find_one({"user_id": uid, "product_id": p["id"]})
            if not existing:
                chosen = p["id"]
                break
        if not chosen:
            pytest.skip("No un-reviewed product available")
        from datetime import datetime, timezone
        order_id = f"ord_test_completed_{int(time.time())}"
        db.orders.insert_one({
            "id": order_id,
            "user_id": uid,
            "status": "completed",
            "items": [{"product_id": chosen, "sku": "TEST", "name": "TEST", "quantity": 1, "unit_price": 100000}],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            r = customer.post(f"{BASE_URL}/api/products/{chosen}/reviews", json={
                "order_id": order_id, "rating": 5, "body": "TEST_iter3 completed order review body",
            })
            assert r.status_code == 200, f"Expected 200 (completed), got {r.status_code}: {r.text}"
            # Cleanup created review
            rev = r.json().get("review", {})
            if rev.get("id"):
                db.product_reviews.delete_one({"id": rev["id"]})
        finally:
            db.orders.delete_one({"id": order_id})
            client.close()


# ---------- P0: Checkout regression ----------
class TestCheckoutRegression:
    def test_full_checkout_flow(self, customer):
        # 1. Get products (frame + lens)
        r = requests.get(f"{BASE_URL}/api/products?product_type=frame&limit=5", timeout=30)
        assert r.status_code == 200
        frames = r.json().get("products", [])
        assert frames, "no frames"
        frame = next((p for p in frames if p.get("variants")), frames[0])

        # 2. Add frame to cart with lens bundle
        # Get a lens
        r2 = requests.get(f"{BASE_URL}/api/products?product_type=lens&limit=5", timeout=30)
        lenses = r2.json().get("products", [])
        lens = lenses[0] if lenses else None

        variant_sku = frame["variants"][0]["sku"] if frame.get("variants") else None
        cart_payload = {
            "product_id": frame["id"],
            "variant_sku": variant_sku,
            "quantity": 1,
        }
        if lens:
            cart_payload["lens_bundle"] = {
                "lens_product_id": lens["id"],
                "lens_index": "1.56",
                "lens_addon": "blue_cut",
            }
        r3 = customer.post(f"{BASE_URL}/api/cart", json=cart_payload)
        assert r3.status_code in (200, 201), f"Cart add failed: {r3.status_code} {r3.text}"

        # 3. Get user address
        r4 = customer.get(f"{BASE_URL}/api/addresses")
        addrs = r4.json().get("addresses", [])
        if not addrs:
            # create one
            r_addr = customer.post(f"{BASE_URL}/api/addresses", json={
                "label": "TEST_iter3",
                "recipient": "Test User",
                "phone": "081234567890",
                "province": "DKI Jakarta",
                "city": "Jakarta Selatan",
                "district": "Kebayoran Baru",
                "postal_code": "12110",
                "detail": "Jl. Test 1",
                "is_default": True,
            })
            assert r_addr.status_code in (200, 201), r_addr.text
            addrs = customer.get(f"{BASE_URL}/api/addresses").json().get("addresses", [])
        assert addrs, "No address available"
        address_id = addrs[0]["id"]

        # 4. Checkout preview
        r5 = customer.post(f"{BASE_URL}/api/checkout/preview", json={
            "address_id": address_id,
            "courier_code": "jne",
            "service_code": "REG",
        })
        assert r5.status_code == 200, f"Preview failed: {r5.status_code} {r5.text}"
        preview = r5.json()
        assert "total" in preview or "grand_total" in preview or "subtotal" in preview

        # 5. Confirm order with PIN
        r6 = customer.post(f"{BASE_URL}/api/checkout/confirm", json={
            "address_id": address_id,
            "courier_code": "jne",
            "service_code": "REG",
            "pin": "654321",
            "payment_method": "va_bca",
        })
        assert r6.status_code == 200, f"Confirm failed: {r6.status_code} {r6.text}"
        data = r6.json()
        order_id = data.get("order_id") or data.get("order", {}).get("id")
        order_number = data.get("order_number") or data.get("order", {}).get("order_number")
        assert order_id or order_number, f"No order id/number returned: {data}"

        # 6. Payment confirm (mock DOKU) — endpoint uses order_number
        if order_number:
            r7 = customer.post(f"{BASE_URL}/api/payment/confirm/{order_number}", json={})
            assert r7.status_code in (200, 201, 202), f"Payment confirm: {r7.status_code} {r7.text}"


# ---------- P1: Excel import ----------
class TestExcelImport:
    def test_admin_import_template_still_200(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/products/import/template")
        assert r.status_code == 200
