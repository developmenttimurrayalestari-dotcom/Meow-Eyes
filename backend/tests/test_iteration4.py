"""Iteration 4 tests: RBAC full coverage, bundle recommendation, cron scheduler."""
import os
import time
import uuid
from datetime import datetime, timezone, timedelta

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

STAFF_EMAIL = "staff@meoweyes.id"
STAFF_PW = "Staff@123"
STAFF_PIN = "111222"
BASE_STAFF_PERMS = ["article.view", "article.create", "article.update", "article.delete",
                    "review.view", "review.moderate"]


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def mongo():
    c = MongoClient(MONGO_URL)
    yield c[DB_NAME]
    c.close()


def _login(email, pw):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, f"Login failed for {email}: {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login("admin@meoweyes.id", "Admin@123")


@pytest.fixture(scope="module")
def customer_token():
    return _login("customer@meoweyes.id", "Customer@123")


@pytest.fixture(scope="module")
def staff_token():
    return _login(STAFF_EMAIL, STAFF_PW)


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def staff_user_id(mongo):
    u = mongo.users.find_one({"email": STAFF_EMAIL}, {"_id": 0, "user_id": 1})
    assert u, "staff user not seeded"
    return u["user_id"]


def _set_staff_perms(mongo, perms):
    mongo.users.update_one({"email": STAFF_EMAIL}, {"$set": {"permissions": perms}})


# ---------- P0: RBAC — staff DENIED with only base perms ----------
class TestRBACDeny:
    """Staff with only article.* + review.* perms → 403 on setting.* / product.* routes."""

    @pytest.fixture(autouse=True)
    def reset_perms(self, mongo):
        _set_staff_perms(mongo, BASE_STAFF_PERMS)
        yield
        _set_staff_perms(mongo, BASE_STAFF_PERMS)

    def test_knowledge_allowed_via_article_view(self, staff_token):
        # Knowledge uses article.view — should be 200 (per spec note)
        r = requests.get(f"{BASE_URL}/api/admin/knowledge", headers=_hdr(staff_token))
        assert r.status_code == 200, r.text

    def test_faqs_denied(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/faqs", headers=_hdr(staff_token))
        assert r.status_code == 403, r.text

    def test_pages_denied(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/pages", headers=_hdr(staff_token))
        assert r.status_code == 403, r.text

    def test_contact_setting_denied(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/contact-setting", headers=_hdr(staff_token))
        assert r.status_code == 403, r.text

    def test_lens_indexes_denied(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/lens/indexes", headers=_hdr(staff_token))
        assert r.status_code == 403, r.text


# ---------- P0: RBAC — staff ALLOWED when granted setting.*+product.view ----------
class TestRBACGrant:
    @pytest.fixture(autouse=True)
    def grant(self, mongo):
        _set_staff_perms(mongo, BASE_STAFF_PERMS + ["setting.view", "setting.update", "product.view"])
        yield
        _set_staff_perms(mongo, BASE_STAFF_PERMS)

    def test_faqs_get(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/faqs", headers=_hdr(staff_token))
        assert r.status_code == 200, r.text
        assert "items" in r.json()

    def test_pages_get(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/pages", headers=_hdr(staff_token))
        assert r.status_code == 200, r.text

    def test_contact_setting_get(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/contact-setting", headers=_hdr(staff_token))
        assert r.status_code == 200, r.text

    def test_lens_indexes_get(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/lens/indexes", headers=_hdr(staff_token))
        assert r.status_code == 200, r.text

    def test_knowledge_post_ok(self, staff_token, mongo):
        payload = {"title": f"TEST_KN_{uuid.uuid4().hex[:6]}", "knowledge_type": "frame_shape",
                   "content": "test", "sort_order": 999}
        r = requests.post(f"{BASE_URL}/api/admin/knowledge", headers=_hdr(staff_token), json=payload)
        assert r.status_code == 200, r.text
        kid = r.json()["knowledge"]["id"]
        # cleanup
        mongo.product_knowledges.delete_one({"id": kid})

    def test_faq_put_needs_setting_update(self, staff_token, mongo):
        # Create a faq via admin path (staff has setting.update now)
        r = requests.post(f"{BASE_URL}/api/admin/faqs", headers=_hdr(staff_token),
                          json={"question": "TEST_Q", "answer": "TEST_A"})
        assert r.status_code == 200, r.text
        fid = r.json()["item"]["id"]
        r2 = requests.put(f"{BASE_URL}/api/admin/faqs/{fid}", headers=_hdr(staff_token),
                          json={"answer": "TEST_A2"})
        assert r2.status_code == 200, r2.text
        # cleanup
        mongo.faqs.delete_one({"id": fid})

    def test_page_delete_needs_setting_update(self, staff_token, mongo):
        r = requests.post(f"{BASE_URL}/api/admin/pages", headers=_hdr(staff_token),
                          json={"title": f"TEST_P_{uuid.uuid4().hex[:6]}", "content": "x"})
        assert r.status_code == 200, r.text
        pid = r.json()["page"]["id"]
        r2 = requests.delete(f"{BASE_URL}/api/admin/pages/{pid}", headers=_hdr(staff_token))
        assert r2.status_code == 200, r2.text


# ---------- P0: Bundle Recommendation ----------
class TestBundleRecommendation:
    @pytest.fixture(scope="class")
    def frame_id(self, mongo):
        f = mongo.products.find_one({"product_type": "frame", "is_active": True}, {"_id": 0, "id": 1})
        assert f, "No active frame in DB"
        return f["id"]

    def test_bundle_public_endpoint(self, frame_id):
        r = requests.get(f"{BASE_URL}/api/lens/recommended-bundle/{frame_id}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "frame" in data and "picks" in data
        assert len(data["picks"]) == 3
        tiers = [p["tier"] for p in data["picks"]]
        assert tiers == ["basic", "popular", "premium"]

    def test_bundle_math(self, frame_id):
        r = requests.get(f"{BASE_URL}/api/lens/recommended-bundle/{frame_id}")
        for pick in r.json()["picks"]:
            expected = pick["frame_price"] + pick["lens_price"] + pick["lens_index_price"]
            assert abs(pick["bundle_total"] - expected) < 0.01, f"Bundle math wrong: {pick}"
            for k in ["lens_product_id", "lens_index_id", "bundle_total", "original_total", "savings"]:
                assert k in pick

    def test_bundle_invalid_frame(self):
        r = requests.get(f"{BASE_URL}/api/lens/recommended-bundle/nonexistent-id")
        assert r.status_code == 404


# ---------- P0: Bundle Checkout — cart subtotal equals bundle_total ----------
class TestBundleCheckout:
    def test_add_bundle_to_cart_subtotal_matches(self, customer_token, mongo):
        # Pick a frame
        f = mongo.products.find_one({"product_type": "frame", "is_active": True}, {"_id": 0})
        assert f
        r = requests.get(f"{BASE_URL}/api/lens/recommended-bundle/{f['id']}")
        assert r.status_code == 200
        pick = r.json()["picks"][1]  # popular
        variant_id = (f.get("variants") or [{}])[0].get("id")

        # Clear cart first
        rc = requests.get(f"{BASE_URL}/api/cart", headers=_hdr(customer_token))
        for it in rc.json().get("items", []):
            requests.delete(f"{BASE_URL}/api/cart/{it['cart_id']}", headers=_hdr(customer_token))

        # Add bundle
        payload = {
            "product_id": f["id"],
            "variant_id": variant_id,
            "quantity": 1,
            "lens_product_id": pick["lens_product_id"],
            "lens_index_id": pick["lens_index_id"],
        }
        r2 = requests.post(f"{BASE_URL}/api/cart", headers=_hdr(customer_token), json=payload)
        assert r2.status_code == 200, r2.text

        # Fetch cart and verify subtotal
        r3 = requests.get(f"{BASE_URL}/api/cart", headers=_hdr(customer_token))
        assert r3.status_code == 200
        data = r3.json()
        # Sum of item subtotals
        item_subtotal = sum(i["subtotal"] for i in data["items"])
        assert abs(item_subtotal - pick["bundle_total"]) < 0.01, \
            f"cart subtotal {item_subtotal} != bundle {pick['bundle_total']}"


# ---------- P0: Cron / Scheduler ----------
class TestScheduler:
    def test_health_scheduler_running(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert data.get("scheduler_running") is True, data

    def test_status_admin_only(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/admin/scheduler/status", headers=_hdr(admin_token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["running"] is True
        ids = {j["id"] for j in data["jobs"]}
        expected = {"expire-pending-orders", "activate-flash-sales", "poll-shipments", "auto-complete-orders"}
        assert expected.issubset(ids), f"Missing jobs: {expected - ids}"

    def test_status_denied_customer(self, customer_token):
        r = requests.get(f"{BASE_URL}/api/admin/scheduler/status", headers=_hdr(customer_token))
        assert r.status_code == 403

    def test_status_denied_staff(self, staff_token):
        r = requests.get(f"{BASE_URL}/api/admin/scheduler/status", headers=_hdr(staff_token))
        assert r.status_code == 403

    @pytest.mark.parametrize("job_id", [
        "expire-pending-orders", "activate-flash-sales",
        "poll-shipments", "auto-complete-orders",
    ])
    def test_run_job(self, admin_token, job_id):
        r = requests.post(f"{BASE_URL}/api/admin/scheduler/run/{job_id}", headers=_hdr(admin_token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert data.get("job") == job_id

    def test_run_invalid_job(self, admin_token):
        r = requests.post(f"{BASE_URL}/api/admin/scheduler/run/bogus-job", headers=_hdr(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is False
        assert "error" in data


# ---------- P1: Cron effect ----------
class TestCronEffect:
    def test_expire_pending_order(self, admin_token, mongo):
        # Insert a fake pending_payment order with reservation_expires_at in the past
        oid = f"TEST_ORDER_{uuid.uuid4().hex[:8]}"
        past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        now_str = datetime.now(timezone.utc).isoformat()
        mongo.orders.insert_one({
            "id": oid, "order_number": f"TEST-{oid[:8]}",
            "user_id": "TEST_USER", "items": [], "address": {},
            "subtotal": 100000, "total": 100000, "shipping_cost": 0,
            "voucher_discount": 0, "points_used": 0, "points_discount": 0,
            "roulette_discount": 0, "status": "pending_payment",
            "payment_status": "unpaid", "reservation_expires_at": past,
            "created_at": now_str, "updated_at": now_str,
        })
        try:
            r = requests.post(f"{BASE_URL}/api/admin/scheduler/run/expire-pending-orders",
                              headers=_hdr(admin_token))
            assert r.status_code == 200, r.text
            # Verify order flipped
            o = mongo.orders.find_one({"id": oid}, {"_id": 0})
            assert o["status"] == "expired", f"status={o['status']}"
        finally:
            mongo.orders.delete_one({"id": oid})
            mongo.order_status_logs.delete_many({"order_id": oid})
            mongo.stock_reservations.delete_many({"order_id": oid})

    def test_activate_flash_sale(self, admin_token, mongo):
        fs_id = f"TEST_FS_{uuid.uuid4().hex[:8]}"
        start = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        mongo.flash_sales.insert_one({
            "id": fs_id, "name": "TEST FS", "start_at": start, "end_at": end,
            "is_active": False, "items": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            r = requests.post(f"{BASE_URL}/api/admin/scheduler/run/activate-flash-sales",
                              headers=_hdr(admin_token))
            assert r.status_code == 200, r.text
            fs = mongo.flash_sales.find_one({"id": fs_id}, {"_id": 0})
            assert fs["is_active"] is True
        finally:
            mongo.flash_sales.delete_one({"id": fs_id})


# ---------- P1: Regression ----------
class TestRegression:
    def test_admin_login(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=_hdr(admin_token))
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "super_admin"

    def test_customer_login(self, customer_token):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=_hdr(customer_token))
        assert r.status_code == 200

    def test_vouchers_active(self):
        r = requests.get(f"{BASE_URL}/api/vouchers/active")
        assert r.status_code == 200
        codes = {v["code"] for v in r.json().get("vouchers", [])}
        assert "MEOWWELCOME" in codes or len(codes) >= 1, codes
