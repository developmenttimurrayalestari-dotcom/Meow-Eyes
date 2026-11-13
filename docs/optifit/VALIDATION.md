# Validasi Meowsurement terintegrasi — 9 November 2026

## Hasil yang dijalankan

| Pemeriksaan | Hasil | Lingkungan dan batas |
| --- | --- | --- |
| Frontend seluruh suite | **124 lulus, 15 suite** | Jest/React, termasuk storefront/checkout, profil, katalog, akun, geometri, reports, dan kompatibilitas vault lama |
| Backend seluruh suite | **296 lulus, 1 dilewati** | pytest, HTTP FastAPI + SQLAlchemy/SQLite, pemeriksaan model/MySQL DDL dan ekspor migrasi |
| Backend Meowsurement final | **10 skenario lulus** | Meliputi correction ID UUID penuh dan propagasi kegagalan job retensi |
| Build production | **Berhasil dengan CI=true** | `npm run build`; main `/static/js/main.60b34070.js` |
| Browser integrasi customer | **9 dari 9 lulus**, `pageErrors=[]` | Chromium, build produksi, endpoint HTTP asli, akun sintetis, SQLite disposable dengan foreign keys |
| Native MySQL 5.7.24-log | **Belum dijalankan** | Satu test ditahan sampai DB `test_meow_*` kosong dikonfigurasi eksplisit |
| Deploy/data produksi | **Belum dilakukan** | Tidak ada server target/export MongoDB/akses produksi pada pengerjaan ini |
| Kamera perangkat fisik/akurasi klinis | **Belum divalidasi** | Geometri/software sintetik bukan studi fitting pasien |

Backend memperlihatkan satu deprecation warning Starlette/httpx yang sudah ada. Build memberi pemberitahuan umur data Browserslist; tidak ada warning lint aplikasi yang menggagalkan build. Tidak dilakukan pembaruan dependency di luar cakupan perubahan.

Hasil browser terstruktur ada pada [BROWSER_VALIDATION.json](BROWSER_VALIDATION.json). Screenshot internal hanya dipakai memeriksa tampilan; tidak disertakan sebagai deliverable. Source fixture dan runner ada pada `frontend/e2e/meowsurement-server.py` serta `meowsurement-customer-browser.cjs`.

## Sembilan skenario browser

1. Meowsurement tanpa login diarahkan ke login website, lalu profil wajib. Return URL produk/varian utuh; customer tanpa PIN checkout tetap dapat melanjutkan. Tidak muncul organisasi, admin/operator lokal atau pendaftaran pasien.
2. Draft resep tersimpan; nol tetap nol, nilai belum diketahui tetap NULL, CYL nonzero memerlukan AXIS sebelum ready.
3. Admin website menyimpan A/B/DBL/ED default dan override per varian. Dimensi efektif sesuai varian.
4. Detail produk membawa pilihan frame/varian ke Meowsurement. Profil/resep dan geometri terisi otomatis.
5. API membuat sesi dengan snapshot sumber server. Upload foto, capture dan thumbnail belum disetujui secara default.
6. Checklist persiapan dan persetujuan → tiga pembacaan manual OD/OS → revisi → submit → approval oleh admin website berbeda dengan evidence. Data sintetis menghasilkan OD 31 mm, OS 33 mm; ini fixture pengujian, bukan pengukuran pasien.
7. Profil versi lama ditolak 409. Mengubah resep aktif dan dimensi katalog tidak mengubah snapshot sesi lama, termasuk setelah reload.
8. Antrean admin membuka sesi tanpa meminta petugas mengisi resep pribadi. Approval tetap terkait revisi yang benar.
9. Profil dan dialog spesifikasi bekerja pada viewport 390 px. Customer ditolak saat mengakses endpoint admin.

Browser context customer/admin terpisah dan identitas diperiksa melalui `/auth/me`. Runner tidak memakai `--single-process`, karena pada percobaan harness sebelumnya flag tersebut menimbulkan pencampuran cookie antar-context. Pengujian final memakai isolasi renderer normal.

## Cakupan backend dan schema

- Kesiapan profil, date/AXIS/angka nol, ownership resep, dan versi yang tertinggal.
- Profil boleh draft; create-session tidak boleh melewati kelengkapan. Resep checkout yang sudah ada tidak berubah.
- Default frame/override, varian milik produk lain, version conflict dan izin dashboard.
- Server-owned profile/Rx/frame snapshot, immutable source, session ownership, expected revision, unknown fields, dan data inline yang ditolak.
- Append-only revisions/captures/measurements/reviews/audit; FK source mengikat hasil dan bukti pada revisi yang sama.
- Submission/review, finite values, kualitas rendah, pemalsuan median, duplikasi foto, calibration/provenance yang tidak sesuai, dan independent reviewer.
- Upload hanya setelah consent terpisah, metadata EXIF dibersihkan, source-vs-normalized hash, akses foto, ekspor, tombstone/delete/expiry, serta cleanup job idempotent.
- Kegagalan cleanup diteruskan sehingga manual admin job tidak melaporkan keberhasilan palsu.
- Migrasi 0003 dibekukan; kedua salinan SQL cocok dengan ekspor Alembic. Head, 79 tabel, aturan data dan guard 0002/0003 diverifikasi secara portable/DDL.

Test native yang masih dilewati sudah diperbarui untuk head 0003, audit trigger kedua revisi, snapshot/revision immutability, pointer consistency dan approval dengan reviewer. SQLite tidak membuktikan perilaku MySQL trigger, locking, collation, implicit DDL commit atau privileges pada target nyata; itu tetap gate staging.

## Cakupan frontend

- Autofill Rx nol dan pemisahan NULL; data resep/frame hanya dibaca pada sesi.
- Customer tidak mengirim pemilik, resep/frame sumber atau approval saat membuat sesi.
- Gate profil dan returnTo lokal aman untuk login/register/OAuth; perilaku checkout lama tetap diuji.
- Frame tidak lengkap tidak dapat memulai; versi konflik tidak ditimpa.
- Reviewer website tidak dapat mengedit pengukuran customer dan tidak melewati batas role/permission server.
- Snapshot profil per sesi dipertahankan meskipun customer yang sama mempunyai sesi baru.
- Photo RAM default tanpa request upload; upload privat memakai consent eksplisit; pergantian akun membuang state sebelumnya.
- Respons yang terlambat setelah lock/pergantian akun tidak mengembalikan data atau mengizinkan unduh laporan.
- Geometri, repeatability, panto/PD, kualitas, provenance, ekspor dan parameter tetap diuji dalam suite OptiFit yang sudah ada.

## Menjalankan ulang

Backend:

```bash
cd backend
python -m pytest -c pytest-mysql.ini -q
```

Frontend:

```bash
cd frontend
CI=true npm test -- --watchAll=false --runInBand
CI=true npm run build
```

Browser dari root proyek, dengan Playwright dan environment backend yang sudah tersedia:

```bash
MEOW_QA_PYTHON=/path/to/backend-venv/bin/python \
MEOW_QA_BROWSER=/path/to/chromium \
MEOW_QA_DIR=/path/to/disposable-qa-output \
node frontend/e2e/meowsurement-customer-browser.cjs
```

Runner menjalankan server fixture dan browser dalam satu process tree, menggunakan file SQLite/foto sintetis sementara dan port lokal. `MEOW_QA_BROWSER` dapat dihilangkan jika browser Playwright sudah terpasang. Tidak ada transaksi provider atau data customer asli yang dipakai.

Pengujian native MySQL hanya boleh diaktifkan pada target test kosong dengan APP_ENV=test dan MYSQL_INTEGRATION_TESTS=1, mengikuti guard serta konfigurasi di `backend/tests_mysql/test_mysql_integration.py`. Jangan menunjuk test ini ke database toko.

## Riwayat implementasi sebelumnya

Dokumentasi dan hasil browser vault lokal v5 dipindahkan ke `legacy-local-vault/`. Hasil tersebut merupakan riwayat versi terdahulu, bukan bukti flow customer saat ini. Script lama `frontend/e2e/optifit-browser.cjs` ditandai archived dan tidak menjadi runner acceptance aktif. Tidak ada klaim bahwa data lokal lama telah diimpor ke MySQL.
