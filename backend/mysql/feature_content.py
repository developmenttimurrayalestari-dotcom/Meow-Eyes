"""Idempotent optical content additions. Existing edited content is preserved."""
from __future__ import annotations

from sqlalchemy import func, select

from . import models as m
from .base import utcnow


FEATURE_SEED_KEY = "features.optical.content.v1"
KNOWLEDGE_ENTRIES = [
    ("frame_shape", "Hexagonal", "frame-hexagonal",
     "Frame enam sisi dengan tampilan geometris.",
     "Frame hexagonal memiliki bentuk lensa enam sisi. Sudutnya memberi karakter geometris, dengan proporsi yang berbeda pada setiap model. Periksa lebar lensa, bridge, dan panjang gagang pada detail produk untuk membandingkan ukurannya."),
    ("frame_shape", "Kotak (Square)", "frame-kotak",
     "Frame kotak dengan garis sudut yang tegas.",
     "Frame kotak atau square memiliki siluet bersudut. Modelnya dapat berupa persegi atau mendekati persegi, dengan ketebalan bingkai yang beragam. Ukuran dan kenyamanan tetap ditentukan oleh dimensi serta penyesuaian frame."),
    ("frame_shape", "Bulat (Round)", "frame-bulat",
     "Frame bulat dengan garis melingkar.",
     "Frame bulat atau round menggunakan siluet lensa melingkar. Pilihannya tersedia dalam beragam ukuran dan bahan. Bandingkan ukuran lensa serta jarak bridge, lalu gunakan fitur try-on pada frame yang didukung untuk melihat proporsi visual."),
    ("frame_shape", "Half Rim", "frame-half-rim",
     "Konstruksi bingkai yang mengelilingi sebagian tepi lensa.",
     "Half rim atau semi-rimless memiliki bingkai pada sebagian tepi lensa, sedangkan bagian lainnya menggunakan sistem penahan yang disesuaikan dengan desain frame. Pilihan jenis dan bahan lensa perlu sesuai dengan konstruksi frame."),
    ("frame_shape", "Full Rim", "frame-full-rim",
     "Konstruksi bingkai yang mengelilingi seluruh tepi lensa.",
     "Pada frame full rim, bingkai mengelilingi seluruh tepi lensa. Konstruksi ini tersedia dalam berbagai bentuk dan bahan. Full rim menjelaskan konstruksi bingkai, sehingga sebuah frame bulat, kotak, atau hexagonal juga dapat termasuk full rim."),
    ("material", "Plastic", "material-plastic",
     "Pilihan frame berbahan plastik dengan beragam bentuk dan warna.",
     "Plastic adalah kelompok bahan frame, dengan komposisi dan karakter yang berbeda menurut model. Acetate dan jenis polimer lain tidak selalu memiliki sifat yang sama. Gunakan spesifikasi bahan pada produk sebagai acuan dan hindari menyimpan frame di dekat sumber panas."),
    ("material", "Mixed Material (Acetate mix Titanium)", "material-mixed",
     "Kombinasi dua atau lebih bahan dalam satu frame.",
     "Frame mixed material menggabungkan beberapa bahan, misalnya bagian depan acetate dengan komponen titanium. Komposisi tersebut dapat berbeda antara bagian depan, bridge, engsel, dan gagang. Lihat deskripsi tiap produk untuk mengetahui bahan serta petunjuk perawatannya."),
    ("lens_type", "Lensa Normal", "lensa-normal",
     "Lensa plano tanpa daya sferis, dicatat sebagai SPH 0.00.",
     "Lensa normal atau plano memiliki daya sferis 0.00. Pilihan bahan dan lapisan lensa dicatat terpisah dari ukuran resep. Jika resep memuat silinder, ADD, atau ukuran lainnya, masukkan juga nilai tersebut sesuai dokumen resep."),
    ("lens_type", "Lensa Minus", "lensa-minus",
     "Lensa dengan nilai SPH bertanda negatif.",
     "Pesanan lensa minus menggunakan nilai SPH negatif sesuai resep. Masukkan ukuran mata kanan (OD) dan mata kiri (OS) secara terpisah. Isikan CYL, AXIS, ADD, dan PD apabila tercantum pada resep; foto resep dapat dilampirkan saat checkout."),
    ("lens_type", "Lensa Plus", "lensa-plus",
     "Lensa dengan nilai SPH bertanda positif.",
     "Pesanan lensa plus menggunakan nilai SPH positif sesuai resep. Kolom SPH dan ADD memiliki fungsi yang berbeda dalam pencatatan resep, sehingga nilainya tidak boleh saling menggantikan. Salin setiap nilai mata kanan dan kiri sesuai dokumen resep."),
    ("lens_type", "Lensa Silinder", "lensa-silinder",
     "Pencatatan lensa dengan pasangan nilai CYL dan AXIS.",
     "Resep lensa silinder memuat nilai CYL dan arah AXIS. Masukkan kedua nilai beserta SPH untuk mata kanan dan kiri sesuai resep. Jangan mengubah tanda plus atau minus maupun mengonversi nilai sendiri saat memesan; lampirkan foto resep bila diperlukan."),
]


async def ensure_feature_content(session, *, apply: bool = True) -> dict:
    """Create requested topics and backfill old new badges once.

    We never overwrite a matching slug or publish an existing draft.
    New Arrival uses product flags rather than a category. The private marker governs the legacy badge
    backfill, so an administrator's later unmark action survives future reruns.
    """
    existing_slugs = {slug.casefold() for slug in (await session.scalars(select(m.ProductKnowledge.slug))).all()}
    marker = await session.get(m.Setting, FEATURE_SEED_KEY)
    missing = [entry for entry in KNOWLEDGE_ENTRIES if entry[2].casefold() not in existing_slugs]
    new_products = []
    if marker is None:
        statement = select(m.Product).where(
            m.Product.is_new_arrival.is_(False), m.Product.new_arrival_until.is_(None),
            m.Product.id.in_(select(m.ProductBadge.product_id).where(func.lower(m.ProductBadge.badge).in_(
                ["new", "newarrival", "new-arrival", "new_arrival"])))
        ).order_by(m.Product.id)
        if apply:
            statement = statement.with_for_update()
        new_products = (await session.scalars(statement)).all()
    report = {"knowledge_created": len(missing), "knowledge_preserved": len(KNOWLEDGE_ENTRIES) - len(missing),
              "new_arrival_category_created": False,
              "legacy_new_badges_backfilled": len(new_products), "backfill_already_applied": marker is not None,
              "applied": apply, "knowledge_slugs": [entry[2] for entry in missing]}
    if not apply:
        return report
    now = utcnow()
    for index, (kind, title, slug, description, body) in enumerate(missing):
        session.add(m.ProductKnowledge(id=m.new_id(), knowledge_type=kind, title=title, slug=slug,
            description=description, content=f"<p>{body}</p>", status="published", published_at=now,
            sort_order=100 + index, seo_title=title + " | Meow Eyes", seo_description=description))
    for product in new_products:
        product.is_new_arrival = True
    if marker is None:
        session.add(m.Setting(key=FEATURE_SEED_KEY,
            value={"version": 1, "applied_at": now.isoformat(), "legacy_new_badges_backfilled": len(new_products)},
            is_public=False, description="Optical feature content and one-time legacy New Arrival badge backfill"))
    await session.flush()
    return report
