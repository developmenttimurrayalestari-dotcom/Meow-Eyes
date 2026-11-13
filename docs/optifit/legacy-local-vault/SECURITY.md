> Arsip implementasi vault lokal sebelumnya. Dokumen ini tidak menjadi petunjuk alur customer saat ini. Gunakan [dokumentasi aktif](../README.md).

# Keamanan dan privasi Meowsurement

Dokumen ini menjelaskan implementasi vault lokal MVP, bukan sertifikasi keamanan
atau klaim bahwa browser dapat memberikan seluruh kontrol aplikasi native.
Tidak ada data pasien nyata atau kredensial produksi pada source/test fixture.

## Data yang disimpan

Vault memakai IndexedDB origin aplikasi dengan tiga object store:

| Store | Isi persisten |
| --- | --- |
| `meta` | ID/version vault, alias login, parameter PBKDF2, kunci data yang telah dibungkus, serta counter jeda percobaan lokal |
| `state` | Satu envelope AES-GCM untuk organisasi, pengguna/peran, pasien, sesi mentah, revisi, review, metadata foto, pengaturan dan audit |
| `photos` | ID acak dan envelope AES-GCM untuk bytes gambar; identitas pasien tidak menjadi indeks plaintext |

Nama pasien, resep, hasil ukur, foto dan alamat tidak ditulis ke localStorage,
cache HTTP atau galeri perangkat. Kode vault tidak mempunyai pemanggilan jaringan.
Sinkronisasi server maupun pelatihan model bukan efek samping penyimpanan lokal.

State lokal mengikuti model relasional logis pada DESIGN.md, tetapi dibungkus
sebagai graph terenkripsi agar atribut klinis tidak bocor melalui indeks.
Model server MySQL 5.7.24 tetap terpisah; vault tidak membuka koneksi database server.

## Kunci dan enkripsi

- Satu DEK acak 256 bit dibuat untuk workspace melalui `crypto.getRandomValues`.
- Setiap akun mempunyai salt 32 byte dan KEK hasil PBKDF2-HMAC-SHA-256 dengan
  600.000 iterasi. KEK mengenkripsi DEK; password/PIN tidak disimpan.
- State, foto dan pembungkus kunci menggunakan AES-256-GCM, IV acak 96 bit baru
  untuk setiap enkripsi, dan authentication tag 128 bit.
- Additional authenticated data mengikat ciphertext ke versi format, ID vault,
  jenis object, ID object atau nomor revisi. Menukar ciphertext antar foto/state
  tidak menghasilkan data yang dapat dibaca.
- Kunci WebCrypto diimpor sebagai non-extractable. Bytes DEK berada di memori
  hanya selama vault terbuka untuk pengelolaan akun/backup; lock menghapus
  referensi dan menimpa array bytes yang dimiliki modul.

Frasa sandi minimal 12 karakter disarankan. PIN lokal 10–32 digit diterima,
selain pola berulang/berurutan sederhana. PIN mempunyai ruang tebakan lebih
kecil; PBKDF2 dan jeda percobaan tidak mengubah PIN lemah menjadi rahasia yang
kuat terhadap pencurian berkas dan penebakan offline. Operator harus memakai
perangkat terkunci dan akses OS yang sesuai.

Pemilihan AES-GCM, pemisahan KEK/DEK, sumber acak serta work factor mengacu pada
[OWASP Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html),
[OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html),
dan [W3C Web Cryptography](https://www.w3.org/TR/webcrypto-1/).

## Peran dan batas ancaman

Admin membuat/menonaktifkan akun, mengubah konfigurasi, mengelola pasien dan
backup. Operator/Customer Meow Eyes hanya membaca pasien miliknya melalui API
vault dan dapat membuat data/revisi miliknya. Reviewer membaca workspace dan
membuat keputusan review; ia tidak mengubah data asli. Review mengikuti policy
independen pada `domain/workflow.js`, termasuk pemisahan reviewer dari operator
serta pembuat revisi terakhir.

Peran dibaca dari state terenkripsi, bukan flag UI/header plaintext. Setiap
mutasi membaca akun aktif terbaru. Perubahan/penonaktifan credential dan pesan
lintas tab mengunci sesi lama. Revision compare-and-swap menolak penimpaan data
oleh tab yang memakai snapshot lama.

**Ini adalah otorisasi aplikasi lokal pada workspace perangkat yang dipercaya.**
Anggota workspace mempunyai akses ke DEK workspace selama login. Pengguna yang
mengendalikan DevTools, mengganti JavaScript, memiliki malware/ekstensi browser,
atau mencuri memori proses bukan pihak yang dapat dibatasi hanya oleh UI lokal.
Gunakan vault/browser profile terpisah untuk pelanggan yang saling tidak
percaya. Multi-tenant server memerlukan autentikasi, otorisasi, pembagian kunci,
dan audit server tersendiri sebelum diaktifkan.

Semua skrip pada origin yang sama merupakan bagian batas kepercayaan. Route
khusus tidak dengan sendirinya menciptakan origin keamanan terpisah. Deployment
subdomain/origin terisolasi, CSP yang sesuai dan pengendalian skrip pihak ketiga
perlu dipertimbangkan oleh operator hosting. Risiko XSS terhadap data client
storage dijelaskan pada [OWASP HTML5 Security](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html).

## Lock, privasi layar dan persaingan tab

Idle timeout default lima menit, dapat dikonfigurasi admin 1–30 menit. UI
memanggil `touch()` pada aktivitas nyata dan `lock('hidden')` ketika dokumen
tersembunyi. Lock langsung menghapus state/key yang dirujuk vault; UI menghapus
view pasien, menghentikan kamera dan mencabut object URL. Mutasi yang antre dari
sesi lama ditolak. Commit mempunyai guard generasi lock dan pemeriksaan versi.

Lima kegagalan membuka akun memulai jeda lokal 30 detik; kegagalan berikutnya
menambah jeda sampai 15 menit. Counter ini tidak menggantikan perlindungan
terhadap penebakan offline atau administrator perangkat yang mereset database/jam.

Browser tidak memberikan jaminan universal untuk memblokir screenshot, recent
apps snapshot, swap OS atau salinan memori internal. Mask/lock adalah upaya
pengurangan paparan. JavaScript juga tidak dapat menjamin penghapusan forensik
semua salinan string/kunci yang pernah berada di heap.

## Revisi, audit dan transaksi

`session.raw` dan setiap `revision.data` hanya ditambahkan sebagai snapshot.
Koreksi mempunyai reason, parentRevisionId, actorId, timestamp dan versi
algoritma. Append membuat revisi baru dan mengembalikan status menjadi draft;
persetujuan versi sebelumnya tetap ada pada riwayat review.

Audit menyimpan urutan, pelaku, action, ID opak, hash state sebelum/sesudah,
previousHash dan hash event. AES-GCM melindungi envelope; verifikasi chain dan
state hash dijalankan saat unlock/mutasi. Tidak ada endpoint edit/hapus event
untuk operator. Jangan memasukkan data pribadi yang tidak perlu pada alasan
koreksi/penghapusan yang ditulis bebas.

Rantai ini **tamper-evident dalam batas aplikasi**. Pemilik DEK yang mengganti
seluruh data/chain atau memulihkan backup lama tidak dapat dibuktikan oleh hash
lokal saja. Timestamp berasal dari perangkat. Bukti waktu/anchor independen
memerlukan layanan server terpercaya dan kebijakan retensi terpisah.

Enkripsi dilakukan sebelum transaksi IndexedDB dibuka. Header, state dan
penambahan/penghapusan foto di-commit atomik setelah membandingkan ID/revision
terbaru. Kegagalan quota, konflik, lock atau abort mempertahankan versi lama.
Perilaku transaksi mengacu pada [IndexedDB 2.0](https://www.w3.org/TR/IndexedDB-2/).

## Foto, persetujuan dan retensi

Foto disimpan hanya melalui tindakan dengan `consent:true`. UI men-decode dan
menormalisasi JPEG/PNG/WebP lokal; vault membatasi 8 MiB dan memeriksa MIME/magic
bytes. Metadata dimensi, bila tersedia, dibatasi 20 MP. File asli/EXIF bukan
metadata otomatis pada state. Foto profil mempunyai persetujuan terpisah;
pencabutan persetujuan menghapus ciphertext profil secara atomik.

Default retensi foto 30 hari, dapat diatur 1–3650 hari. `expiresAt` dicatat saat
foto disimpan; pengaturan baru berlaku untuk foto baru. Foto expired tidak dapat
dibaca. Saat vault dibuka, foto yang expired dihapus melalui mutasi yang diaudit.
Admin juga dapat menjalankan penerapan retensi secara eksplisit.

Penghapusan foto menyisakan tombstone metadata supaya revisi lama tidak kehilangan
jejak. Landmark, nilai mentah dan revisi tetap tersedia. Penghapusan pasien
memerlukan admin, alasan, dan nomor rekam yang diketik. Proses menghapus data
pasien, sesi, revisi, review serta ciphertext foto; audit menyisakan ID/hash
minimal. Browser tidak dapat menjamin penghapusan fisik blok SSD, salinan OS,
atau backup yang sebelumnya telah diekspor.

Logo organisasi merupakan pengecualian kecil: data URL PNG/JPEG lokal maksimal
1 MiB dapat disimpan dalam state terenkripsi untuk laporan. URL cloud dan SVG
ditolak. Data klinis tidak menerima embedded image/base64; gunakan photoId.

## Laporan dan backup

PDF/CSV/JSON/print membutuhkan konfirmasi eksplisit dan dicatat melalui
`recordExport`. Thumbnail default mati. Pengaktifannya memerlukan persetujuan
`consents.thumbnail===true` pada revisi immutable yang dipilih, ID revisi
spesifik, pilihan 1–3 ID foto yang benar-benar disertakan, akses pasien, dan foto
yang masih tersedia dalam masa retensi. Foto historis yang sudah dihapus tetapi
tidak dipilih tidak menghalangi ekspor foto aktif lainnya. Pilihan
pada draft berbeda tidak mengesahkan foto revisi lama secara diam-diam.

Backup hanya dibuat admin dengan frasa sandi terpisah minimal 12 karakter
non-numerik. Backup mengenkripsi seluruh header/state/foto serta recovery DEK
menggunakan envelope baru, salt baru, PBKDF2 dan AES-GCM. Pemilik frasa sandi
backup dapat membuka isi backup: simpan rahasia itu terpisah dari file.

Restore mendekripsi dan memeriksa format, parameter KDF, state/chain, daftar serta
seluruh ciphertext foto sebelum mengganti storage. Parameter KDF tidak boleh
dimodifikasi menjadi nilai sangat besar yang menyebabkan DoS. Restore pada
vault berisi data membutuhkan admin terbuka dan teks `GANTI VAULT`. Commit
atomik mempertahankan vault lama jika password/validasi/versi gagal. Setelah
restore, vault terkunci dan akun asli dipakai untuk login. Tidak ada recovery
password yang dikirim ke server. Batas file backup MVP adalah 192 MiB.

IndexedDB dapat hilang ketika data situs dibersihkan atau storage browser tidak
persisten. Aplikasi menyediakan `requestPersistence()`, namun browser dapat
menolak permintaan; lihat [StorageManager.persist](https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist).
Backup terenkripsi perlu diuji pemulihannya oleh organisasi.

## Pengujian yang disediakan

`storage/vault.test.js` menjalankan WebCrypto nyata dengan store transaction
terisolasi untuk mengecek secret salah, bit ciphertext berubah, nonce/AAD,
roles/ownership, audit, konflik, raw immutable, review, lock saat commit,
backup/restore, foto, retensi dan penghapusan. Double transaksi bukan pembuktian
engine IndexedDB browser. Validasi browser tersendiri menjalankan penyimpanan
native dan alur UI; hasil final dicatat pada VALIDATION modul.
