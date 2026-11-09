"""Phase 2 backend tests: content endpoints, lens bundle cart/checkout, review validation,
admin content CRUD, excel import, dashboard endpoints, exports.

Verifies:
- CheckoutPreview payload fix (address_id/courier_code/service_code) → no regression 500
- Cart lens bundle math (frame + lens + lens_index additional_price)
- Review only allowed after completed order (mutate order status via API? No — via MongoDB direct)
- Public content endpoints + slug fetch
- Admin content CRUD (articles, knowledge, faqs, pages, banners-v2, lens/indexes, contact-setting)
- Admin reviews moderation + analytics
- Excel import template/preview/commit
- Admin dashboard summary + chart endpoints
"""
import os
import io
import uuid
import time
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers():
    tok = _login("admin@meoweyes.id", "Admin@123")
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def customer_headers():
    tok = _login("customer@meoweyes.id", "Customer@123")
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ================= Public content =================
class TestPublicContent:
    def test_articles_list(self):
        r = requests.get(f"{BASE_URL}/api/articles")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "articles" in d and isinstance(d["articles"], list)
        assert d["total"] >= 1

    def test_articles_categories(self):
        r = requests.get(f"{BASE_URL}/api/articles/categories")
        assert r.status_code == 200
        assert "categories" in r.json()

    def test_articles_paws_vision_slug_or_first(self):
        # try paws-vision slug; if not, use first article
        r = requests.get(f"{BASE_URL}/api/articles/paws-vision")
        if r.status_code == 404:
            lst = requests.get(f"{BASE_URL}/api/articles").json()["articles"]
            assert lst, "No seeded articles"
            slug = lst[0]["slug"]
            r = requests.get(f"{BASE_URL}/api/articles/{slug}")
        assert r.status_code == 200, r.text
        b = r.json()
        assert "article" in b and "related" in b

    def test_knowledge_list(self):
        r = requests.get(f"{BASE_URL}/api/knowledge")
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and isinstance(d["items"], list) and len(d["items"]) >= 1

    def test_knowledge_paws_vision_slug_or_first(self):
        r = requests.get(f"{BASE_URL}/api/knowledge/paws-vision")
        if r.status_code == 404:
            lst = requests.get(f"{BASE_URL}/api/knowledge").json()["items"]
            assert lst
            slug = lst[0]["slug"]
            r = requests.get(f"{BASE_URL}/api/knowledge/{slug}")
        assert r.status_code == 200, r.text
        b = r.json()
        assert "knowledge" in b and "related_products" in b

    def test_faqs(self):
        r = requests.get(f"{BASE_URL}/api/faqs")
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and "categories" in d

    def test_page_privacy(self):
        r = requests.get(f"{BASE_URL}/api/pages/kebijakan-privasi")
        assert r.status_code == 200, r.text
        assert "page" in r.json()

    def test_contact_info(self):
        r = requests.get(f"{BASE_URL}/api/contact/info")
        assert r.status_code == 200
        assert "contact" in r.json()

    def test_banners_hero(self):
        r = requests.get(f"{BASE_URL}/api/banners?position=hero")
        assert r.status_code == 200
        assert "banners" in r.json()

    def test_lens_indexes(self):
        r = requests.get(f"{BASE_URL}/api/lens/indexes")
        assert r.status_code == 200
        d = r.json()
        assert "items" in d and len(d["items"]) >= 1

    def test_lens_options_for_frame(self):
        # pick a frame product
        lst = requests.get(f"{BASE_URL}/api/products?product_type=frame&limit=1").json()["products"]
        assert lst
        fid = lst[0]["id"]
        r = requests.get(f"{BASE_URL}/api/lens/options-for-frame/{fid}")
        assert r.status_code == 200, r.text
        b = r.json()
        assert "lens_products" in b and "lens_indexes" in b


# ================= Cart lens bundle + checkout preview no-regression =================
class TestCartLensBundleAndCheckout:
    @pytest.fixture(scope="class")
    def ctx(self):
        tok = _login("customer@meoweyes.id", "Customer@123")
        H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

        # Clear cart
        cart = requests.get(f"{BASE_URL}/api/cart", headers=H).json()
        for ci in cart.get("items", []):
            requests.delete(f"{BASE_URL}/api/cart/{ci['id']}", headers=H)

        # Find Kittycraft Cubby Anak
        frame_id = None
        frame_variant_id = None
        frame_price = None
        lst = requests.get(f"{BASE_URL}/api/products?limit=50").json()["products"]
        for p in lst:
            if "Kittycraft Cubby" in p["name"]:
                pd = requests.get(f"{BASE_URL}/api/products/{p['slug']}").json()
                prod = pd.get("product", pd)
                frame_id = prod["id"]
                frame_price = prod.get("discount_price") or prod["price"]
                if prod.get("variants"):
                    frame_variant_id = prod["variants"][0]["id"]
                break

        # Find Lensa Progresif Premium
        lens_id = None
        lens_price = None
        for p in lst:
            if "Progresif Premium" in p["name"]:
                pd = requests.get(f"{BASE_URL}/api/products/{p['slug']}").json()
                prod = pd.get("product", pd)
                lens_id = prod["id"]
                lens_price = prod.get("discount_price") or prod["price"]
                break

        # Find 1.56 Blue Cut lens index
        lens_idx_id = None
        lens_idx_add = None
        idxs = requests.get(f"{BASE_URL}/api/lens/indexes").json()["items"]
        for li in idxs:
            if "1.56" in li["name"] and "Blue" in li["name"]:
                lens_idx_id = li["id"]
                lens_idx_add = li["additional_price"]
                break

        return {
            "H": H, "frame_id": frame_id, "frame_variant_id": frame_variant_id,
            "frame_price": frame_price, "lens_id": lens_id, "lens_price": lens_price,
            "lens_idx_id": lens_idx_id, "lens_idx_add": lens_idx_add,
        }

    def test_seeded_products_exist(self, ctx):
        assert ctx["frame_id"], "Kittycraft Cubby Anak not seeded"
        assert ctx["lens_id"], "Lensa Progresif Premium not seeded"
        assert ctx["lens_idx_id"], "1.56 Blue Cut lens index not seeded"
        # Verify prices from spec
        assert ctx["frame_price"] == 350000, f"frame_price={ctx['frame_price']}"
        assert ctx["lens_price"] == 1300000, f"lens_price={ctx['lens_price']}"
        assert ctx["lens_idx_add"] == 75000, f"lens_idx_add={ctx['lens_idx_add']}"

    def test_cart_frame_only(self, ctx):
        H = ctx["H"]
        # Clear
        cart = requests.get(f"{BASE_URL}/api/cart", headers=H).json()
        for ci in cart.get("items", []):
            requests.delete(f"{BASE_URL}/api/cart/{ci['id']}", headers=H)

        r = requests.post(f"{BASE_URL}/api/cart", headers=H, json={
            "product_id": ctx["frame_id"], "variant_id": ctx["frame_variant_id"], "quantity": 2,
        })
        assert r.status_code in (200, 201), r.text
        cart = requests.get(f"{BASE_URL}/api/cart", headers=H).json()
        it = [c for c in cart["items"] if c["product_id"] == ctx["frame_id"] and not c.get("lens_product")][0]
        assert it["frame_price"] == 350000
        assert it["lens_price"] == 0
        assert it["subtotal"] == 350000 * 2

    def test_cart_frame_with_lens_bundle(self, ctx):
        H = ctx["H"]
        r = requests.post(f"{BASE_URL}/api/cart", headers=H, json={
            "product_id": ctx["frame_id"], "variant_id": ctx["frame_variant_id"], "quantity": 1,
            "lens_product_id": ctx["lens_id"], "lens_index_id": ctx["lens_idx_id"],
        })
        assert r.status_code in (200, 201), r.text
        cart = requests.get(f"{BASE_URL}/api/cart", headers=H).json()
        bundle_items = [c for c in cart["items"] if c.get("lens_product")]
        assert bundle_items, "bundle item not found"
        b = bundle_items[0]
        # Expected: 350k + 1.3M + 75k = 1,725,000
        assert b["frame_price"] == 350000
        assert b["lens_price"] == 1300000 + 75000, f"lens_price={b['lens_price']}"
        assert b["unit_price"] == 1725000
        assert b["subtotal"] == 1725000

    def test_checkout_preview_new_payload(self, ctx):
        """Regression: CheckoutPreview must accept address_id/courier_code/service_code."""
        H = ctx["H"]
        # Ensure address
        addrs = requests.get(f"{BASE_URL}/api/addresses", headers=H).json()
        addr_list = addrs.get("addresses", addrs if isinstance(addrs, list) else [])
        if not addr_list:
            ar = requests.post(f"{BASE_URL}/api/addresses", headers=H, json={
                "label": "Rumah", "recipient": "Mira", "phone": "081234567890",
                "province": "DKI Jakarta", "city": "Jakarta Selatan",
                "postal_code": "12345", "street": "Jl. Cat No. 7", "is_default": True,
            })
            assert ar.status_code in (200, 201), ar.text
            aid = ar.json().get("id") or ar.json().get("address", {}).get("id")
        else:
            aid = addr_list[0]["id"]

        cart = requests.get(f"{BASE_URL}/api/cart", headers=H).json()
        cart_ids = [c["id"] for c in cart["items"]]
        r = requests.post(f"{BASE_URL}/api/checkout/preview", headers=H, json={
            "address_id": aid, "courier_code": "jne", "service_code": "REG",
            "selected_item_ids": cart_ids,
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["subtotal"] > 0 and d["total"] > 0
        assert "shipping" in d


# ================= Review flow (only after completed order) =================
class TestReviewGate:
    @pytest.fixture(scope="class")
    def new_customer(self):
        email = f"test_reviewer_{uuid.uuid4().hex[:6]}@meoweyes.id"
        r = requests.post(f"{BASE_URL}/api/auth/register",
                          json={"name": "Reviewer", "email": email, "password": "Password@123"})
        assert r.status_code in (200, 201), r.text
        tok = r.json()["token"]
        H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
        # Setup PIN
        requests.post(f"{BASE_URL}/api/auth/pin/setup", headers=H, json={"pin": "112233"})
        u = r.json()["user"]
        return {"email": email, "H": H, "user_id": u.get("id") or u.get("user_id")}

    def test_review_rejected_without_order(self, new_customer):
        lst = requests.get(f"{BASE_URL}/api/products?limit=1").json()["products"]
        pid = lst[0]["id"]
        r = requests.post(f"{BASE_URL}/api/products/{pid}/reviews",
                          headers=new_customer["H"], json={"rating": 5, "body": "Bagus"})
        assert r.status_code == 400, f"Expected 400 got {r.status_code}: {r.text}"

    def test_review_allowed_after_completed_order(self, new_customer):
        """Uses MongoDB direct update to mark an order completed for this user."""
        try:
            from pymongo import MongoClient
        except ImportError:
            pytest.skip("pymongo not installed")

        H = new_customer["H"]
        uid = new_customer["user_id"]

        # Create an order end-to-end for this user
        # Add address
        ar = requests.post(f"{BASE_URL}/api/addresses", headers=H, json={
            "label": "Rumah", "recipient": "Reviewer", "phone": "081234567890",
            "province": "DKI Jakarta", "city": "Jakarta Selatan",
            "postal_code": "12345", "street": "Jl. Test", "is_default": True,
        })
        assert ar.status_code in (200, 201), ar.text
        aid = ar.json().get("id") or ar.json().get("address", {}).get("id")

        # Find product with variant + stock
        lst = requests.get(f"{BASE_URL}/api/products?limit=20").json()["products"]
        pid = None
        vid = None
        for p in lst:
            pd = requests.get(f"{BASE_URL}/api/products/{p['slug']}").json()
            prod = pd.get("product", pd)
            for v in prod.get("variants", []):
                if v.get("stock", 0) - v.get("reserved", 0) > 0:
                    pid = prod["id"]; vid = v["id"]; break
            if pid: break
        assert pid, "no in-stock product"

        # Add to cart
        rc = requests.post(f"{BASE_URL}/api/cart", headers=H, json={
            "product_id": pid, "variant_id": vid, "quantity": 1,
        })
        assert rc.status_code in (200, 201), rc.text
        cart = requests.get(f"{BASE_URL}/api/cart", headers=H).json()
        cart_ids = [c["id"] for c in cart["items"]]

        # Confirm order
        confirm = requests.post(f"{BASE_URL}/api/checkout/confirm", headers=H, json={
            "address_id": aid, "selected_item_ids": cart_ids,
            "courier_code": "jne", "service_code": "REG", "pin": "112233",
        })
        assert confirm.status_code == 200, confirm.text
        order = confirm.json()["order"]
        order_id = order["id"]

        # Pay
        p = requests.post(f"{BASE_URL}/api/payment/confirm/{order['order_number']}", headers=H)
        assert p.status_code == 200, p.text

        # Direct DB flip: status → completed
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        res = db.orders.update_one({"id": order_id}, {"$set": {"status": "completed"}})
        assert res.matched_count == 1, "order not found in DB to mark completed"

        # Now review should be allowed
        rv = requests.post(f"{BASE_URL}/api/products/{pid}/reviews", headers=H,
                           json={"rating": 5, "body": "Sangat bagus", "order_id": order_id})
        assert rv.status_code == 200, f"review must be allowed after completed: {rv.status_code} {rv.text}"
        assert rv.json()["review"]["status"] == "approved"

        # Duplicate should be rejected
        rv2 = requests.post(f"{BASE_URL}/api/products/{pid}/reviews", headers=H,
                            json={"rating": 4, "body": "Coba lagi", "order_id": order_id})
        assert rv2.status_code == 400, f"duplicate review must be rejected: {rv2.status_code}"

        # Save for admin moderation test
        pytest.review_product_id = pid


# ================= Admin content CRUD =================
class TestAdminContent:
    def test_admin_articles_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/articles", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_article_crud(self, admin_headers):
        payload = {
            "title": f"TEST_Article {uuid.uuid4().hex[:6]}",
            "slug": f"test-article-{uuid.uuid4().hex[:6]}",
            "excerpt": "Test excerpt",
            "content": "<p>Content</p>",
            "cover_image": "https://images.unsplash.com/photo-1508296695146-257a814070b4?w=600",
            "status": "published",
        }
        r = requests.post(f"{BASE_URL}/api/admin/articles", headers=admin_headers, json=payload)
        assert r.status_code in (200, 201), r.text
        aid = r.json().get("id") or r.json().get("article", {}).get("id")
        assert aid
        # Update
        u = requests.put(f"{BASE_URL}/api/admin/articles/{aid}", headers=admin_headers,
                        json={"title": "TEST_Article Updated"})
        assert u.status_code == 200, u.text
        # Delete
        d = requests.delete(f"{BASE_URL}/api/admin/articles/{aid}", headers=admin_headers)
        assert d.status_code in (200, 204)

    def test_admin_knowledge_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/knowledge", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_faqs_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/faqs", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_pages_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/pages", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_banners_v2_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/banners-v2", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_contact_setting_get(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/contact-setting", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_lens_indexes(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/lens/indexes", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json().get("items", [])) >= 1

    def test_admin_staff_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/staff", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_permissions(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/permissions", headers=admin_headers)
        assert r.status_code == 200


# ================= Admin reviews =================
class TestAdminReviews:
    def test_admin_reviews_list(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/reviews", headers=admin_headers)
        assert r.status_code == 200

    def test_admin_reviews_analytics(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/reviews/analytics", headers=admin_headers)
        assert r.status_code == 200


# ================= Excel import =================
class TestExcelImport:
    def test_import_template(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/products/import/template", headers=admin_headers)
        assert r.status_code == 200, r.text
        assert len(r.content) > 200
        ctype = r.headers.get("content-type", "")
        assert "spreadsheet" in ctype or "officedocument" in ctype or "octet-stream" in ctype

    def test_import_preview_and_commit(self, admin_headers):
        try:
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not installed")
        # Fetch template
        r = requests.get(f"{BASE_URL}/api/admin/products/import/template", headers=admin_headers)
        assert r.status_code == 200
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active
        # Read header to build a row with two color variants
        header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]

        def make_row(color, sku):
            row = {h: "" for h in header}
            row["name"] = f"TEST_ImportProd_{uuid.uuid4().hex[:6]}"
            row["sku"] = sku
            row["product_type"] = "frame"
            row["price"] = 250000
            row["main_image"] = "https://images.unsplash.com/photo-1508296695146-257a814070b4?w=600"
            row["description"] = "Import test"
            row["color"] = color
            row["stock"] = 10
            row["weight_gram"] = 100
            # optional fields left blank
            return [row.get(h, "") for h in header]

        # Two rows same name/sku → 2 color variants
        base_name = f"TEST_ImportProd_{uuid.uuid4().hex[:6]}"
        base_sku = f"TESTIMP-{uuid.uuid4().hex[:6].upper()}"
        wb2 = openpyxl.Workbook()
        ws2 = wb2.active
        ws2.append(header)
        for color in ["Black", "Brown"]:
            r_data = {h: "" for h in header}
            r_data.update({
                "name": base_name, "sku": base_sku, "product_type": "frame", "price": 250000,
                "main_image": "https://images.unsplash.com/photo-1508296695146-257a814070b4?w=600",
                "description": "Import test", "color": color, "stock": 10, "weight_gram": 100,
            })
            ws2.append([r_data.get(h, "") for h in header])
        buf = io.BytesIO()
        wb2.save(buf); buf.seek(0)

        # Preview (multipart)
        files = {"file": ("import.xlsx", buf.getvalue(),
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        h_noct = {k: v for k, v in admin_headers.items() if k.lower() != "content-type"}
        pv = requests.post(f"{BASE_URL}/api/admin/products/import/preview", headers=h_noct, files=files)
        assert pv.status_code == 200, pv.text
        preview = pv.json()
        assert "rows" in preview or "products" in preview or "count" in preview or "items" in preview

        # Commit
        buf.seek(0)
        files = {"file": ("import.xlsx", buf.getvalue(),
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        cm = requests.post(f"{BASE_URL}/api/admin/products/import/commit", headers=h_noct, files=files)
        assert cm.status_code == 200, cm.text
        body = cm.json()
        assert body.get("ok") is True or body.get("created", body.get("count", 0)) >= 1


# ================= Admin dashboard chart endpoints =================
class TestDashboardCharts:
    def test_summary(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard/summary", headers=admin_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ["sales_today", "total_users", "total_products", "low_stock"]:
            assert k in d

    def test_sales_chart(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard/sales-chart", headers=admin_headers)
        assert r.status_code == 200

    def test_order_status_chart(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard/order-status-chart", headers=admin_headers)
        assert r.status_code == 200

    def test_top_products(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard/top-products", headers=admin_headers)
        assert r.status_code == 200


# ================= Admin exports =================
class TestExports:
    @pytest.mark.parametrize("key", ["sales", "inventory", "flash-sales", "roulette", "games",
                                     "newsletter", "users", "points"])
    def test_export(self, admin_headers, key):
        r = requests.get(f"{BASE_URL}/api/admin/export/{key}", headers=admin_headers)
        assert r.status_code == 200, f"{key}: {r.status_code} {r.text[:150]}"
        assert len(r.content) > 100
