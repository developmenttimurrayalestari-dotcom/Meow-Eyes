"""Explicit development-only SQL seed preserving the original demo fixtures.

No import-time writes. A seed marker prevents repeating the demo fixtures. Core seed
requires an empty business database; content-only seed requires empty content
tables. Demo credentials are supplied explicitly through environment variables.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re

from sqlalchemy import select

from .base import utcnow
from .config import MySQLSettings
from .database import Database
from .importer import COLLECTIONS, TABLES, ImportRejected, build_plan
from .feature_content import ensure_feature_content

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures/demo_data.json"
CORE_MARKER = "demo_seed_all_v1"
CONTENT_MARKER = "demo_seed_content_v1"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def demo_id(kind: str, key: str) -> str:
    return "demo_" + kind + "_" + hashlib.sha256(key.encode()).hexdigest()[:24]


def build_demo_documents(*, include_core: bool = True, include_content: bool = True,
                         when: datetime | None = None, password_hashes: dict[str, str] | None = None,
                         pin_hash: str | None = None) -> dict[str, list[dict]]:
    """Pure fixture construction. No database connection or credential defaults."""
    import models as DTO
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    core, content = fixture["seed.py"], fixture["seed_content.py"]
    docs = {c: [] for c in COLLECTIONS}
    now = when or utcnow()
    stamp = now.isoformat()

    def dump(collection, model, **values):
        if "created_at" in model.model_fields:
            values.setdefault("created_at", stamp)
        if "updated_at" in model.model_fields:
            values.setdefault("updated_at", stamp)
        obj = model(**values).model_dump()
        docs[collection].append(obj)
        return obj

    if include_core:
        if not password_hashes or not pin_hash:
            raise ImportRejected("Demo accounts require explicitly supplied password and PIN hashes")
        for role, email, name in (("super_admin", "admin@meoweyes.id", "Mira Admin"),
                                  ("customer", "customer@meoweyes.id", "Lulu Customer"),
                                  ("staff", "staff@meoweyes.id", "Staff Content")):
            dump("users", DTO.User, user_id=demo_id("user", role), email=email, name=name,
                 password_hash=password_hashes[role], pin_hash=pin_hash, role=role, provider="password",
                 points_balance=500 if role == "customer" else 0,
                 permissions=["article.view", "article.create", "article.update", "article.delete", "review.view", "review.moderate"] if role == "staff" else [])

        def category(name, parent=None, kind="product", slug=None, order=0, featured=False):
            slug = slug or slugify(name)
            identity = demo_id("cat", slug)
            parents = {v["id"]: v for v in docs["categories"]}
            dump("categories", DTO.Category, id=identity, parent_id=parent, name=name, slug=slug,
                 category_type=kind, level=parents[parent]["level"] + 1 if parent else 0,
                 sort_order=order, is_featured=featured)
            return identity

        frame = category("Frame", kind="frame", order=1, featured=True)
        lens = category("Lensa", kind="lens", order=2, featured=True)
        package = category("Paket Frame + Lensa", kind="package", order=3, featured=True)
        sub_ids, segment_ids = {}, {}
        for i, name in enumerate(core["frame_subs_data"]):
            sub_ids[name] = category(name, frame, "frame", order=i, featured=i < 4)
            for j, segment in enumerate(core["segments"]):
                segment_ids[(name, segment)] = category(segment, sub_ids[name], slug=f"{slugify(name)}-{slugify(segment)}", order=j)
        lens_ids = {name: category(name, lens, "lens", order=i) for i, (name, _) in enumerate(core["lens_subs"])}
        package_ids = {name: category(name, package, "package", order=i) for i, name in enumerate(["Paket Hemat", "Paket Premium", "Paket Anak"])}
        brand_ids = {}
        for name in ["Leinz", "MeowOptik", "PurrLens", "Catlux", "Kittycraft", "EssenseEye"]:
            slug = slugify(name)
            brand_ids[name] = demo_id("brand", slug)
            dump("brands", DTO.Brand, id=brand_ids[name], name=name, slug=slug, description=f"Premium brand {name}")
        flash_items, images = [], core["PRODUCT_IMAGES"]
        for i, (name, kind, sub, brand, segment, price, discount, badges, variants) in enumerate(core["products_data"]):
            slug, pid = slugify(name), demo_id("product", slugify(name))
            categories = [frame, sub_ids[sub], segment_ids[(sub, segment)]] if kind == "frame" else [lens, lens_ids[sub]] if kind == "lens" else [package, package_ids[sub]]
            variant_models = [DTO.ProductVariant(id=demo_id("variant", v["sku"]), **{**v, "stock": v.get("stock", 25)}) for v in variants]
            product = dump("products", DTO.Product, id=pid, name=name, slug=slug,
                 # Fix duplicate truncated SKUs only in the demo fixture. Real
                 # import never renames a source SKU to avoid a collision.
                 sku="DEMO-" + hashlib.sha256(slug.encode()).hexdigest()[:20].upper(),
                 description=f"{name} — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.",
                 spec={"Material": "Acetate", "Origin": "Italy" if kind == "frame" else "Japan", "Garansi": "12 bulan", "Wajah": "Oval, Bulat, Persegi"},
                 product_type=kind, category_ids=categories, primary_category_id=categories[-1], brand_id=brand_ids[brand],
                 segments=[segment], price=price, discount_price=discount, flash_sale_price=int(price * .65) if "flashsale" in badges else None,
                 weight_gram=120, dimension="140 x 50 x 145 mm", main_image=images[i % len(images)],
                 gallery=[images[(i + j) % len(images)] for j in range(3)], variants=variant_models, badges=badges,
                 sold_count=(i * 17) % 200, rating_avg=round(4.5 + (i % 5) * .1, 2), rating_count=i * 7 + 5)
            if "flashsale" in badges:
                flash_items.append({"product_id": pid, "flash_price": product["flash_sale_price"], "quota": 20, "sold": 0})
        vouchers = [
            {"code": "MEOWWELCOME", "name": "Diskon Selamat Datang 15%", "discount_type": "percent", "discount_value": 15, "min_purchase": 250000, "max_discount": 100000, "quota": 500},
            {"code": "GRATISONGKIR", "name": "Gratis Ongkir", "discount_type": "free_shipping", "discount_value": 0, "min_purchase": 200000, "quota": 300},
            {"code": "MEOW50K", "name": "Potongan Rp 50.000", "discount_type": "nominal", "discount_value": 50000, "min_purchase": 500000, "quota": 200},
        ]
        for value in vouchers:
            dump("vouchers", DTO.Voucher, id=demo_id("voucher", value["code"]), **value, start_at=stamp, end_at=(now + timedelta(days=365)).isoformat())
        if flash_items:
            dump("flash_sales", DTO.FlashSale, id=demo_id("flash", "catlux"), name="Catlux Flash Sale", start_at=(now - timedelta(hours=1)).isoformat(), end_at=(now + timedelta(hours=23)).isoformat(), items=flash_items)
        rewards = [("50 Poin", "points", 50, "#FCA311", .25), ("100 Poin", "points", 100, "#FFD166", .15),
                   ("Gratis Ongkir", "free_shipping", 0, "#06D6A0", .15), ("Diskon Rp 25.000", "discount", 25000, "#FF8FA3", .15),
                   ("Diskon Rp 50.000", "discount", 50000, "#FF6B6B", .10), ("Diskon Rp 100.000", "discount", 100000, "#2A9D8F", .05),
                   ("200 Poin", "points", 200, "#0B192C", .05), ("Coba Lagi", "nothing", 0, "#94A3B8", .10)]
        for label, kind, value, color, probability in rewards:
            dump("roulette_rewards", DTO.RouletteReward, id=demo_id("reward", label), label=label, type=kind, value=value, color=color, probability=probability)
        for key, name, description, photo in [
            ("matching", "Match Meow Pairs", "Cocokkan pasangan kartu kacamata kucing!", "1565127803051-49aaf3d36e29"),
            ("puzzle", "Meow Puzzle", "Susun puzzle kacamata cute Meow Eyes", "1533738363-b7f9aef128ce"),
            ("tetris", "Glasses Tetris", "Susun bingkai kacamata jatuh ala Tetris", "1574258495973-f010dfbb5371")]:
            docs["games"].append({"id": demo_id("game", key), "key": key, "name": name, "description": description,
                "image": f"https://images.unsplash.com/photo-{photo}?crop=entropy&cs=srgb&fm=jpg&w=800", "max_points": 50, "is_active": True, "created_at": stamp})
        docs["cms_banners"].extend([
            {"id": demo_id("legacy_banner", "cat-eye"), "title": "Diskon Hingga 50% — Cat Eye Edition", "image": "https://images.unsplash.com/photo-1670739368045-7f09844fc862?crop=entropy&cs=srgb&fm=jpg&w=1600", "link": "/products?badge=flashsale", "position": "hero", "is_active": True, "created_at": stamp},
            {"id": demo_id("legacy_banner", "leinz"), "title": "Koleksi Leinz Pria Terbaru", "image": "https://images.unsplash.com/photo-1525786210598-d527194d3e9a?crop=entropy&cs=srgb&fm=jpg&w=1600", "link": "/category/leinz-pria", "position": "promo", "is_active": True, "created_at": stamp},
        ])
    if include_content:
        for i, (name, index, description, thickness, power_range, price) in enumerate(content["base"]):
            dump("lens_indexes", DTO.LensIndex, id=demo_id("index", index), name=name, index_value=index, description=description,
                 thickness_level=thickness, recommended_power_range=power_range, additional_price=price, sort_order=i)
        for i, (name, slug) in enumerate([("Tips Kacamata", "tips-kacamata"), ("Fashion Eyewear", "fashion-eyewear"), ("Kesehatan Mata", "kesehatan-mata"), ("Promo & Event", "promo-event"), ("Panduan Belanja", "panduan-belanja")]):
            dump("article_categories", DTO.ArticleCategory, id=demo_id("article_cat", slug), name=name, slug=slug, sort_order=i)
        for i, (title, slug, excerpt, body, category, thumbnail) in enumerate(content["articles"]):
            dump("articles", DTO.Article, id=demo_id("article", slug), category_id=demo_id("article_cat", category), author_name="Tim Meow Eyes", title=title,
                 slug=slug, excerpt=excerpt, content=body, thumbnail=thumbnail, status="published", published_at=(now - timedelta(days=i)).isoformat())

        def knowledge(kind, title, slug, description, photo, order, **extra):
            dump("product_knowledges", DTO.ProductKnowledge, id=demo_id("knowledge", slug), knowledge_type=kind,
                 title=title, slug=slug, description=description, content=f"<p>{description}</p>",
                 image=f"https://images.unsplash.com/photo-{photo}?crop=entropy&cs=srgb&fm=jpg&w=800", sort_order=order, **extra)
        for i, (name, description, face, style, pros, cons) in enumerate(content["frame_shapes"]):
            knowledge("frame_shape", f"Frame {name}", "frame-" + slugify(name), description, "1591076482161-42ce6da69f67" if i % 2 == 0 else "1508296695146-257a814070b4", i,
                      face_shape_recommendation=face, style_recommendation=style, pros=pros, cons=cons, filter_param={"badge": None})
        for i, (name, description, pros, cons) in enumerate(content["materials"]):
            knowledge("material", name, "material-" + slugify(name), description, "1574258495973-f010dfbb5371", i, pros=pros, cons=cons)
        for i, (name, description, pros, cons) in enumerate(content["lens_types"]):
            knowledge("lens_type", name, "lensa-" + name.lower().split(" ")[-1], description, "1601924994987-69e26d50dc26", i, pros=pros, cons=cons)
        for i, (name, index, description) in enumerate(content["indexes_kn"]):
            knowledge("lens_index", name, "index-" + index.replace(".", "-"), description, "1581290447921-b54aaca33ac2", i)
        for i, (name, slug) in enumerate([("Pemesanan", "pemesanan"), ("Pembayaran", "pembayaran"), ("Pengiriman", "pengiriman"), ("Garansi & Retur", "garansi-retur")]):
            dump("faq_categories", DTO.FAQCategory, id=demo_id("faq_cat", slug), name=name, slug=slug, sort_order=i)
        for i, (question, answer, category) in enumerate(content["faqs"]):
            dump("faqs", DTO.FAQItem, id=demo_id("faq", question), question=question, answer=answer, category_id=demo_id("faq_cat", category), sort_order=i)
        for kind, title, slug, body in content["pages"]:
            dump("cms_pages", DTO.CMSPage, id=demo_id("page", slug), page_type=kind, title=title, slug=slug, content=body, status="published", published_at=stamp)
        dump("contact_settings", DTO.ContactSetting, id=demo_id("contact", "store"), store_name="Meow Eyes",
             address="Jl. Cat Eye Square No. 9, Kebayoran Baru, Jakarta Selatan 12130", email="hello@meoweyes.id", phone="021-1234-5678",
             whatsapp="6281234567890", operational_hours="Senin - Sabtu, 09:00 - 20:00 WIB", instagram="https://instagram.com/meoweyes.id",
             facebook="https://facebook.com/meoweyes.id", tiktok="https://tiktok.com/@meoweyes.id", tokopedia="https://tokopedia.com/meoweyes", shopee="https://shopee.co.id/meoweyes")
        for title, image, kind, url, position, order in content["banners"]:
            dump("banners_v2", DTO.BannerV2, id=demo_id("banner", title), title=title, image_desktop=image,
                 image_mobile=image, link_type=kind, link_url=url, position=position, sort_order=order)
    return docs


def require_demo_mode(*, confirmed: bool, environment: str) -> None:
    if not confirmed:
        raise ImportRejected("Demo seed requires explicit --demo")
    if environment not in {"development", "test"}:
        raise ImportRejected("Demo seed is disabled outside development/test")


async def seed_with_factory(factory, *, confirmed: bool, environment: str, content_only: bool = False,
                            password_hashes=None, pin_hash=None, when: datetime | None = None) -> dict:
    require_demo_mode(confirmed=confirmed, environment=environment)
    marker = CONTENT_MARKER if content_only else CORE_MARKER
    settings = TABLES["settings"]
    async with factory() as session, session.begin():
        markers = (await session.execute(select(settings.c.key).where(settings.c.key.in_([marker, CORE_MARKER])))).scalars().all()
        if marker in markers or CORE_MARKER in markers:
            features = await ensure_feature_content(session)
            count = features["knowledge_created"] + int(features["new_arrival_category_created"]) + int(not features["backfill_already_applied"])
            return {"ok": True, "status": "already_seeded", "inserted_rows": count, "feature_content": features}
        documents = build_demo_documents(include_core=not content_only, include_content=True,
                                         when=when, password_hashes=password_hashes, pin_hash=pin_hash)
        plan = build_plan(documents)
        if plan.errors:
            raise ImportRejected("Bundled demo fixture failed source preflight; seed aborted")
        target_tables = {row.table for row in plan.rows}
        inspect_tables = target_tables if content_only else set(TABLES) - {"migration_runs", "migration_records", "migration_issues", "settings"}
        for name in sorted(inspect_tables):
            if (await session.execute(select(TABLES[name]).limit(1))).first() is not None:
                raise ImportRejected("Demo seed target is not empty; existing customer/catalog/content data will not be overwritten")
        for row in plan.rows:
            await session.execute(TABLES[row.table].insert().values(**row.values))
        await session.execute(settings.insert().values(key=marker, value={"version": 1,
            "fixture_checksum": hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(), "source_records": len(plan.sources)}, is_public=False))
        features = await ensure_feature_content(session)
        extra_rows = features["knowledge_created"] + int(features["new_arrival_category_created"]) + int(not features["backfill_already_applied"])
        return {"ok": True, "status": "seeded", "inserted_rows": len(plan.rows) + extra_rows,
                "source_records": len(plan.sources), "feature_content": features,
                "fixture_warnings": sorted({i.code for i in plan.warnings}), "synthetic_counters": True, "production_data": False}


async def _run(*, confirmed: bool, content_only: bool) -> dict:
    settings = MySQLSettings.from_env()
    require_demo_mode(confirmed=confirmed, environment=settings.app_env)
    database = Database(settings)
    try:
        ready = await database.check_readiness()
        if not ready.ready:
            raise ImportRejected(f"Target readiness failed: {ready.reason}; run Alembic first")
        password_hashes, pin_hash = None, None
        if not content_only:
            from auth import hash_secret
            variables = {"super_admin": "DEMO_ADMIN_PASSWORD", "customer": "DEMO_CUSTOMER_PASSWORD", "staff": "DEMO_STAFF_PASSWORD"}
            password_hashes = {}
            for role, variable in variables.items():
                value = os.environ.get(variable, "")
                if len(value) < 8 or len(value.encode()) > 72:
                    raise ImportRejected(f"{variable} must be supplied (8-72 UTF-8 bytes)")
                password_hashes[role] = hash_secret(value)
            pin = os.environ.get("DEMO_CHECKOUT_PIN", "")
            if not re.fullmatch(r"[0-9]{6}", pin):
                raise ImportRejected("DEMO_CHECKOUT_PIN must be supplied as six digits")
            pin_hash = hash_secret(pin)
        return await seed_with_factory(database.session_factory, confirmed=confirmed, environment=settings.app_env,
                                       content_only=content_only, password_hashes=password_hashes, pin_hash=pin_hash)
    finally:
        await database.dispose()


def main(argv: list[str] | None = None, *, content_only: bool = False) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Explicitly seed sample data in development/test only")
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(_run(confirmed=args.demo, content_only=content_only))
    except ImportRejected as exc:
        result = {"ok": False, "error": str(exc)}
    except Exception:
        result = {"ok": False, "error": "demo_seed_failed_check_environment_database_and_schema"}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2
