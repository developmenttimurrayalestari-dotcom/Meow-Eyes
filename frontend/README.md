# Meow Eyes — frontend

React 19, React Router, Tailwind, dan CRA/CRACO. Backend aplikasi berada pada
`../backend/server.py` dan menyediakan API dengan prefix `/api`.

## Menjalankan development

Gunakan Node 20–24 dan npm 10 atau lebih baru. Paket ini divalidasi dengan
Node 24. `package-lock.json` adalah lockfile yang dipakai; `.npmrc` menyimpan
pengaturan peer dependency yang diperlukan stack CRA/React saat ini.

```bash
npm ci
cp .env.example .env
npm start
```

Development memakai `REACT_APP_BACKEND_URL=http://localhost:8001`. Jalankan
FastAPI dan MySQL sesuai [panduan rilis](../docs/FEATURES_AND_RELEASE.md).
Frontend tidak menyimpan kredensial database, DOKU, atau Everpro.

## Build dan pengujian

```bash
CI=true npm test -- --watchAll=false --runInBand
CI=true GENERATE_SOURCEMAP=false npm run build
```

Build menghasilkan direktori `build/`. Untuk deployment dengan origin yang
sama, kosongkan `REACT_APP_BACKEND_URL` saat build dan proxy `/api` ke FastAPI.
Untuk origin terpisah, isi origin HTTPS backend dan atur `CORS_ORIGINS` backend.
Konfigurasi nilai React dimasukkan saat build, bukan dibaca ulang saat runtime.

Web server harus mengarahkan route SPA, termasuk `/payment/:orderNumber`, ke
`index.html`. Terapkan aturan proxy `/api` sebelum fallback tersebut. Jangan
menyajikan direktori foto resep sebagai direktori static.

## Fitur utama

- Katalog 15 produk per halaman, Flash Sale, New Arrival dan breadcrumb.
- Checkout resep per frame+lensa dan foto privat; status pembayaran DOKU;
  rating produk dan transaksi sesudah pembayaran terverifikasi.
- Ongkir Everpro berbasis quote dari backend; pilihan alamat dan layanan.
- WhatsApp global, sharing dan Copy Link, publikasi artikel/knowledge,
  urutan/link banner, dan halaman pengaturan admin.
- Virtual Try-On dengan kamera atau foto lokal, aset gambar transparan atau
  GLB/GLTF dan penyesuaian manual. Renderer 3D dimuat saat diperlukan.

Kamera memerlukan izin pengguna serta HTTPS atau localhost. Foto try-on lokal
tidak diunggah oleh UI. Sumber model eksternal harus dapat diakses melalui CORS.
Pratinjau ini tidak melakukan pelacakan landmark atau pengukuran ukuran wajah
otomatis. Detail konfigurasi dan batas pengujian terdapat pada
[panduan rilis](../docs/FEATURES_AND_RELEASE.md),
[integrasi](../docs/INTEGRATIONS.md), dan
[laporan validasi](../docs/mysql-migration/VALIDATION.md).
