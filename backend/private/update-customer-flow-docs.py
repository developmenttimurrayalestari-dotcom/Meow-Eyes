from pathlib import Path
root = Path(__file__).resolve().parents[2]
def edit(name, replacements):
    p = root / name
    value = p.read_text(encoding='utf-8')
    for old, new in replacements:
        assert old in value, (name, old)
        value = value.replace(old, new)
    p.write_text(value, encoding='utf-8')

edit('README.md', [('Head Alembic saat ini **`20261109_0003`**.', 'Head Alembic saat ini **`20261110_0004`**. [Alur menu pengukuran dan frame manual](docs/optifit/CUSTOMER_FLOW.md).')])
edit('docs/optifit/README.md', [
    ('ukuran frame dibaca dari katalog yang dikelola admin.', 'ukuran frame dapat diisi manual atau dibaca dari katalog yang dikelola admin. Pembaruan 10 November memisahkan jenis pengukuran menjadi kartu; lihat [rancangan UI customer](CUSTOMER_FLOW.md).'),
    ('5. Frame dipilih dari katalog aktif. A/B/DBL/ED harus lengkap dan Meowsurement diaktifkan admin. Varian dapat mengikuti spesifikasi produk atau memakai override.', '5. Pilih kartu jenis pengukuran. Isi A/B/DBL manual, atau pilih frame/varian katalog aktif dengan spesifikasi A/B/DBL lengkap dan diaktifkan admin. ED opsional pada kedua sumber. Varian dapat mengikuti spesifikasi produk atau memakai override.'),
    ('Target tetap Oracle', 'Head terkini **`20261110_0004`** mengizinkan sesi tanpa ID produk/varian dengan sumber ukuran manual; tidak menambah tabel. Target tetap Oracle'),
    ('- [SQL migrasi 0002 ke 0003](SCHEMA_MYSQL57.sql)', '- [SQL migrasi 0002 ke 0003](SCHEMA_MYSQL57.sql)\n- [SQL migrasi 0003 ke 0004](../../backend/sql/004_optional_customer_frame.sql)'),
])
edit('docs/optifit/RUNBOOK.md', [
    ('Head lama `20261106_0002`; head baru **`20261109_0003`**.', 'Head sebelumnya `20261109_0003`; head baru **`20261110_0004`**. [Rancangan menu dan frame manual](CUSTOMER_FLOW.md).'),
    ('0001 → 0002 → 0003.', '0001 → 0002 → 0003 → 0004.'),
    ('head harus `20261109_0003`', 'head harus `20261110_0004`'),
    ('Startup readiness memakai head baru.', 'Startup readiness memakai head baru. Target yang sudah berada di 0003 menerima perubahan nullable product_id dan dua trigger sesi; tidak ada penambahan tabel atau penghapusan data.'),
    ('Untuk target yang sudah tepat berada pada 0002 dan belum mempunyai tabel baru, gunakan', 'Untuk target yang sudah tepat berada pada 0003, jalankan `backend/sql/004_optional_customer_frame.sql`. Untuk target pada 0002 yang belum mempunyai tabel baru, jalankan SQL 003 lalu 004 secara berurutan. SQL 003 adalah'),
    ('mysql --show-warnings -h DB_HOST -u MIGRATION_USER -p DB_NAME < sql/003_customer_meowsurement.sql\npython -m mysql.check_integrity', 'mysql --show-warnings -h DB_HOST -u MIGRATION_USER -p DB_NAME < sql/003_customer_meowsurement.sql\nmysql --show-warnings -h DB_HOST -u MIGRATION_USER -p DB_NAME < sql/004_optional_customer_frame.sql\npython -m mysql.check_integrity'),
    ('Downgrade bersifat destruktif dan bukan prosedur rollback produksi biasa.', 'Migrasi 0004 menolak downgrade otomatis karena sesi manual mungkin sudah tersimpan. Rollback menggunakan backup yang sudah diuji; jangan menghapus sesi manual agar downgrade bisa lolos.'),
])
for name in ['DESIGN.md', 'UI_WIREFRAMES.md', 'SCHEMA.md']:
    p = root / 'docs/optifit' / name
    value = p.read_text(encoding='utf-8')
    lines = value.splitlines(keepends=True)
    lines.insert(1, '\n> Pembaruan 10 November 2026: [menu kartu, form khusus, frame manual, ED opsional, dan kamera](CUSTOMER_FLOW.md). Head terbaru `20261110_0004`; SQL 004 melengkapi migrasi 0003 di bawah. Sesi manual memakai `product_id`/`variant_id` NULL dan `spec_scope=manual`.\n')
    p.write_text(''.join(lines), encoding='utf-8')
