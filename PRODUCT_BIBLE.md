# PRODUCT BIBLE: NAMIRIMS CATERING SYSTEM

Single Source of Truth (SSOT) untuk proyek Capstone Asah 2026.  
Berisi formulir pengajuan resmi Use Case UMKM (Bagian A – O), arsitektur teknis *Dual-Intake*, spesifikasi *Admin Dashboard*, dan pembagian peran tiga divisi (Full-Stack, Gen AI, Data Science).

---

# BAGIAN 1: FORMULIR TEMPLATE USE CASE UMKM (ASAH 2026)

*Catatan: Bagian ini merupakan draft final siap salin ke Google Docs pengajuan Capstone.*

## A. Informasi Umum

- **Nama UMKM:** Namirims Catering
- **Bidang usaha:** Jasa Boga / F&B (Katering Harian Asrama & Paket Acara)
- **Nama narasumber:** Owner Namirims
- **Peran narasumber:** Pemilik / Pengelola Utama (*Owner*)
- **PIC UMKM:** Owner Namirims
- **Kontak PIC:** WhatsApp Owner Namirims
- **Tanggal interview:** 27 Oktober 2026
- **Nama tim:** Tim Capstone Namirims
- **Anggota tim:**
  1. Rafid (Ilmu Komputer IPB 61) - Full-Stack / Project Lead
  2. Anggota Full-Stack - Full-Stack Engineer
  3. Anggota Gen AI - Gen AI / AI Engineer
  4. Anggota Gen AI - Gen AI / AI Engineer
  5. Anggota Data Science - Data Scientist
  6. Anggota Data Science - Data Scientist
- **Status validasi use case:** Sudah dikonfirmasi oleh UMKM

---

## B. Penentuan Use Case

### Masalah yang ditemukan dari hasil interview:
1. **Perluasan Pasar Rendah:** Kanal pemasaran daring (Instagram) belum efektif mendatangkan pelanggan baru secara rutin; promosi WhatsApp masih terbatas dari mulut ke mulut.
2. **Pencatatan Pesanan Rutin Manual:** Proses pendataan langganan makan harian mahasiswa masih dilakukan secara manual dan berulang dari obrolan WhatsApp ke Google Spreadsheet.
3. **Salah Catat & Pesanan Terlewat pada Skip Jadwal:** Penanganan permintaan penyesuaian (*skip* jadwal makan) dari pelanggan asrama/kost masih manual, memicu risiko salah rekap, kelebihan porsi masak, atau pesanan terlewat.

### Masalah yang dipilih sebagai use case:
Inakurasi dan inefisiensi rekapitulasi katering harian akibat pencatatan pesanan rutin dan penanganan pengajuan skip jadwal pelanggan yang masih manual (menyelesaikan masalah nomor 2 dan 3 sekaligus sebagai satu kesatuan rantai sebab-akibat operasional).

### Alasan menjadi prioritas bagi UMKM:
Masalah nomor 2 (proses pencatatan manual) dan nomor 3 (salah catat & pesanan terlewat pada skip jadwal) adalah satu kesatuan masalah operasional yang ditegaskan langsung oleh Owner katering sebagai kendala paling mendesak yang memengaruhi kinerja usaha sejak awal berdiri. Otomasi pencatatan pesanan baru tidak akan efektif jika pengajuan skip jadwal harian tetap bocor secara manual, sehingga kedua masalah ini wajib diselesaikan bersamaan dalam satu alur terpadu.

### Skill yang dibutuhkan:
- Full-Stack Web Development (Frontend responsive, Backend RESTful API, Database Management).
- Gen AI & NLP (Small Language Model fine-tuning, Logit Candidate Scoring, Causal Decision Modeling).
- Data Science (Data Wrangling, Exploratory Data Analysis, Demand Forecasting).
- UI/UX & Cloud Deployment.

### Skill yang dimiliki anggota tim:
- Full-Stack: React, Vite, Node.js/Express, PostgreSQL, Tailwind CSS.
- Gen AI: PyTorch, HuggingFace Transformers, LoRA/PEFT, BitsAndBytes 4-bit, FastAPI model serving.
- Data Science: Python, Pandas, Scikit-learn, EDA, Time-Series Forecasting (Prophet/LightGBM).

### Skill yang belum dimiliki tim:
Tidak ada.

### Cara mengatasi kekurangan skill:
Melakukan pembagian tugas yang ketat sesuai *learning path* masing-masing, mengunci skema data berdasarkan file `2026-2027 Catering Namirims.xlsx` sejak minggu pertama, dan membatasi scope teknis pada arsitektur MVP modular.

### Pemeriksaan kelayakan timeline capstone (4 minggu):
- [x] Alur utama dapat dikembangkan dalam empat minggu.
- [x] Data atau data dummy dapat disiapkan.
- [x] Solusi dapat diuji tanpa integrasi ke sistem produksi UMKM.
- [x] Tim memiliki skill utama yang diperlukan.
- [x] Ketergantungan kepada pihak lain dapat dihindari atau dikelola.
- [x] UMKM bersedia menerima demonstrasi dan memberikan feedback.
- [x] Tim memiliki waktu untuk pengujian dan perbaikan.

### Kesimpulan pemilihan use case:
Use case ini dipilih karena **merupakan kendala operasional paling mendesak yang langsung diminta oleh Owner UMKM untuk mengeliminasi salah catat dan pesanan terlewat**, sesuai dengan kemampuan tim dalam **Full-Stack Web Development, Gen AI Decision Modeling, dan Data Analytics**, serta dapat dikembangkan dalam waktu empat minggu dengan membatasi scope pada **otomasi intake pemesanan/skip jadwal via Web Portal Mandiri & WhatsApp Passive Listening Pipeline, serta penyediaan Live Dashboard Kitchen Manifest bagi Owner**.

---

## C. Judul Use Case
**Sistem Terpadu Manajemen Katering Harian: Dashboard Operasional Owner dan Intake Pemesanan Mandiri Berbasis Web & WhatsApp Passive Listening AI**

---

## D. Ringkasan Use Case
**Owner dan pengelola operasional Namirims Catering** mengalami **kesalahan pencatatan data dan adanya pesanan harian yang terlewat** ketika menjalankan **proses rekapitulasi pesanan rutin dan permintaan skip jadwal pelanggan secara manual dari chat WhatsApp ke spreadsheet umum**. Masalah utama berakar pada *context-switching fatigue*: admin harus membaca chat, berpindah jendela aplikasi ke spreadsheet, mencari baris nama pelanggan, lalu mengetik ulang tanggal dan sesi. Di saat jam sibuk (*rush hour* sebelum cutoff), admin kerap membaca chat namun **lupa atau terlewat menginputnya ke spreadsheet**, menyebabkan **waktu kerja tersita berjam-jam, salah saji porsi makanan, dan kerugian finansial**.

Sebagai solusinya, tim mengembangkan **Sistem Informasi (SI) Terpadu Operasional Katering Khusus** (menggantikan lembar spreadsheet umum) yang dilengkapi **fitur pengisian formulir otomatis (*Automatic Pre-Filled Fields*)** bertenaga **WhatsApp Passive Listening AI (PaLiPi)**. Saat chat masuk, model AI membedah isi pesan dan langsung mengisikan seluruh kolom aksi operasional secara otomatis ke antrean draf tinjauan admin. Admin **tidak perlu berpindah-pindah aplikasi (tanpa bolak-balik WhatsApp-Spreadsheet)** karena antarmuka web langsung menyajikan **cuplikan chat asli (*chat snippet*) berdampingan langsung (*side-by-side*) dengan formulir yang telah terisi otomatis**. Admin cukup membuka aplikasi, memverifikasi hasil pembacaan AI dengan melihat cuplikan chat di sampingnya, melakukan penyesuaian cepat bila diperlukan, dan mengeklik satu tombol persetujuan (*1-Click Approve*) untuk menyinkronkan data langsung ke manifes dapur.

---

## E. Latar Belakang

- **Produk atau layanan utama:**
  1. *Paket Acara:* Paket Hemat (Rp10.500), Paket Nikmat (Rp12.000), Paket Kenyang (Rp15.000).
  2. *Paket Harian:* Katering harian asrama dan kost mahasiswa (Rp12.000 – Rp16.000/porsi).
- **Target customer:**
  Penghuni Asrama IPB (mitra utama kerja sama jangka panjang stabil), Asrama Cifor, dan mahasiswa kost sekitar.
- **Kanal penjualan atau pelayanan:**
  WhatsApp, Instagram, dan Penjualan Offline.
- **Tools yang digunakan saat ini:**
  WhatsApp untuk komunikasi pesanan dan Google Spreadsheet untuk pencatatan manual.
- **Gambaran bisnis:**
  Namirims Catering berdiri sejak tahun 2017 berawal dari pesanan tetangga sekitar hingga berkembang menjadi mitra konsumsi rutin institusi asrama mahasiswa di Bogor. Model operasional mengandalkan langganan harian terjadwal (makan siang dan malam) dengan volume puluhan porsi per hari yang memerlukan rekapitulasi ketat setiap pagi dan sore hari.

---

## F. Masalah Prioritas

- **Proses bisnis saat ini:**
  Pelanggan bertanya ➔ Pemberian Menu dan Biaya ➔ Pelanggan memesan ➔ Dicatat manual & diproses ➔ Pembayaran ➔ Pengiriman/diterima pelanggan ➔ Penanganan keluhan.
- **Masalah utama:**
  Pencatatan pesanan rutin dan pengajuan *skip* jadwal makan pelanggan masih dilakukan secara manual satu per satu dari chat ke lembar spreadsheet umum. Tingginya friksi mental (*context-switching*) akibat bolak-balik antara layar WhatsApp dan spreadsheet menyebabkan admin kerap membaca chat tetapi **lupa memasukkan datanya ke spreadsheet**.
- **Contoh kejadian:**
  Pelanggan asrama mengirim pesan izin tidak makan (*skip*) di WhatsApp pukul 08:15 WIB sebelum batas cutoff. Admin sempat membaca pesan di ponsel, namun karena terdistraksi pesanan lain dan harus membuka laptop untuk mengedit spreadsheet, admin **lupa mencatatnya ke baris Excel pelanggan**. Akibatnya, porsi makan siang tetap dimasak dapur dan dikirim ke asrama. Hal ini memicu kerugian porsi makanan bagi katering dan sengketa sisa kuota langganan pelanggan.
- **Frekuensi masalah:**
  Terjadi setiap hari kerja pada siklus persiapan makan siang (pagi hari) dan makan malam (sore hari).
- **Pihak yang terdampak:**
  Owner/Admin katering (beban waktu rekapitulasi dan stres operasional) dan mahasiswa pelanggan asrama/kost (pesanan terlewat atau kuota makan tidak sinkron).
- **Dampak terhadap bisnis atau customer:**
  Waktu kerja terbuang hingga 1–2 jam per hari hanya untuk sinkronisasi data manual, risiko pemborosan bahan baku makanan, dan komplain pelanggan akibat ketidaksesuaian pesanan.
- **Penanganan saat ini:**
  Owner membaca pesan riwayat percakapan secara manual di WhatsApp lalu berpindah aplikasi (*alt-tab*) dan mengetik ulang perubahan tanggal satu per satu ke lembar Google Spreadsheet.

---

## G. Target Pengguna

- **Pengguna utama:** Owner / Admin Operasional Namirims Catering.
- **Pengguna lain yang terlibat:** Mahasiswa pelanggan katering harian (Asrama IPB, Asrama Cifor, Kost Babakan).
- **Penerima manfaat:** Tim operasional dapur UMKM dan seluruh pelanggan katering aktif.

---

## H. Tujuan dan Outcome Bisnis

- **Tujuan utama:**
  Use case ini bertujuan membantu **Owner Namirims Catering dan pelanggan katering** untuk **mengotomasi pencatatan pesanan rutin dan pengajuan skip jadwal melalui Web Portal Mandiri serta WhatsApp Passive Listening Pipeline**, sehingga **rekapan produksi harian terintegrasi tanpa risiko salah catat atau pesanan terlewat**.
- **Outcome yang diharapkan:**
  1. Tereliminasinya kesalahan pencatatan data pesanan rutin dan permintaan *skip* jadwal menjadi 0%.
  2. Tersedianya ringkasan manifest dapur harian (*Kitchen Manifest*) otomatis yang memuat jumlah porsi masak dan catatan khusus (*dietary notes*) per lokasi asrama.
  3. Pemangkasan waktu administrasi harian Owner hingga >60%.

---

## I. Arah Solusi dan Scope MVP

- **Arah solusi:**
  Membangun sistem katering terpadu berbasis aplikasi web yang menggantikan spreadsheet manual, dilengkapi sistem dua pintu masuk (*Dual-Intake*):
  1. *Web Portal Mandiri:* Antarmuka web responsif bagi mahasiswa untuk registrasi paket dan memilih tanggal *skip* secara mandiri tanpa interaksi chat.
  2. *WhatsApp Passive Listening Pipeline:* Pengamat senyap di latar belakang chat WhatsApp asli antara pelanggan dan admin. Model AI mengekstrak keputusan bisnis secara deterministik tanpa ikut membalas chat pelanggan.  
  Seluruh data dari kedua pintu masuk mengalir otomatis ke satu **Admin Kitchen Manifest Dashboard**.

- **Pengguna utama MVP:** Owner / Admin Namirims Catering.
- **Masalah utama yang diselesaikan:** Pencatatan manual pesanan rutin harian dan pengajuan *skip* jadwal pelanggan yang memicu salah catat dan pesanan terlewat.

- **Alur utama MVP:**
  1. Pelanggan melakukan interaksi melalui salah satu kanal:
     - *Jalur Web:* Memilih tanggal *skip* pada kalender interaktif portal web (langsung terverifikasi).
     - *Jalur WhatsApp:* Mengirim chat izin tidak makan/ganti menu ke WhatsApp.
  2. **Mutable Living Buffer & Interruptible Ingestion (PaLiPi Model):**
     - Webhook WhatsApp menghimpun balon pesan pelanggan ke dalam buffer aktif per sesi percakapan.
     - Debounce *trailing-edge* 2.5s menunggu balon pesan susulan; jika pesan baru masuk saat komputasi berlangsung, inferensi lama seketika dibatalkan (*AbortController*) dan buffer diperbarui.
  3. **PVE Pattern & Automatic Pre-Filled Field Ingestion:**
     - PaLiPi memprediksi intent, sesi makan, tanggal kalender, dan catatan diet dari percakapan WhatsApp.
     - Gerbang deterministik memvalidasi batas waktu (*Cutoff*: siang $\le$ 08:30 WIB, malam $\le$ 15:00 WIB) berdasarkan timestamp *Terminal Discourse Marker*.
     - Seluruh hasil inferensi AI secara otomatis **mengisi formulir aksi operasional (*Automatic Pre-Filled Fields*)** dan masuk ke antrean **HITL Queue (`hitl_queue`)** dengan status `DRAFT_PENDING`. Admin tidak lagi berhadapan dengan formulir kosong.
  4. **Admin HITL Review & Split-Screen Ingestion (Zero Alt-Tab):**
     - Dashboard SI Admin menampilkan antrean draf tinjauan dengan tata letak berdampingan (*side-by-side*):
       * Sisi Kiri / Atas: **Cuplikan Percakapan Utuh (*Chat Snippet / Digital Double*)** yang mendasari keputusan pelanggan, lengkap dengan profil pelanggan (*Customer Dossier*: riwayat alergi, sisa kuota, asrama).
       * Sisi Kanan / Bawah: **Formulir yang Telah Terisi Otomatis (*Pre-Filled Form*)** memuat aksi, tanggal terpilih, dan sesi makan.
     - **Verifikasi & Edit Fleksibel:** Admin cukup membaca cuplikan chat di layar yang sama tanpa perlu bolak-balik membuka WhatsApp. Jika AI membaca 100% akurat, admin cukup mengeklik tombol **1-Click Approve**. Jika ada nuansa khusus, admin dapat langsung mengubah dropdown/tanggal secara *inline* dalam hitungan detik sebelum konfirmasi.
     - Persetujuan admin seketika memutasi database manifes dapur produksi dan memicu tanda terima balasan WhatsApp.
  5. **Live Kitchen Manifest:** Rekap porsi masak hari ini per lokasi asrama otomatis diperbarui seketika setelah persetujuan admin tanpa perlu rumus spreadsheet manual.

- **Cakupan MVP:**
  - **Fitur 1 (Web Portal Mandiri):** Formulir pendaftaran paket langganan dan kalender interaktif pengajuan *skip* jadwal makan pelanggan.
  - **Fitur 2 (Admin Kitchen Manifest Dashboard):** Tampilan ringkasan jumlah porsi masak per sesi (siang/malam), breakdown per asrama, catatan diet khusus, dan riwayat log transaksi sebagai pengganti spreadsheet umum.
  - **Fitur 3 (PaLiPi Model & Pre-Filled Living Draft Queue):** Integrasi webhook chat WhatsApp dengan model keputusan Intern-Decision-4B + QLoRA, didukung *Mutable Living Buffer* untuk menangani chat terpotong-potong, sistem *pre-fill form* otomatis, dan antarmuka tinjauan terpadu yang menampilkan cuplikan chat asli berdampingan dengan formulir draf.
  - **Fitur 4 (Embedded Data Science Analytics):** Widget visualisasi tren jumlah skip harian dan estimasi kebutuhan porsi mingguan pada dashboard admin.

- **Bentuk demonstrasi kepada UMKM:**
  Simulasi mahasiswa mengajukan skip jadwal lewat WhatsApp ➔ PaLiPi otomatis mengisi kolom formulir (*pre-filled fields*) ke antrean SI katering ➔ Admin membuka aplikasi, memverifikasi hasil pembacaan AI dengan cuplikan chat di sampingnya tanpa buka WhatsApp (*zero alt-tab*), melakukan penyesuaian jika perlu, dan melakukan persetujuan 1-klik (*1-Click Approve*) ➔ manifes porsi dapur ter-update seketika secara akurat.

- **Di luar scope:**
  - Integrasi pembayaran otomatis (*payment gateway* / auto-debit).
  - Pelacakan pengantaran kurir berbasis GPS *live tracking*.
  - Otomasi kampanye pemasaran media sosial (Instagram Ads/Bot).
  - Modul pembukuan keuangan laba-rugi katering menyeluruh.

---

## J. Hasil yang Diharapkan

Pada akhir capstone, tim menghasilkan:
- **Aplikasi Web MVP Terintegrasi:** Web Portal Pelanggan dan Admin Dashboard yang dapat diakses melalui browser ponsel dan laptop.
- **Layanan API Model AI:** REST API model keputusan terarah (*Passive Listening Pipeline*) berbasis FastAPI.
- **Dokumentasi & Panduan Operasional:** Buku panduan ringkas penggunaan Dashboard Admin untuk Owner katering.
- **Evaluasi Uji Coba Bersama UMKM:** Laporan hasil demonstrasi, feedback, dan pengisian survei evaluasi akhir oleh PIC UMKM.

---

## K. Indikator Keberhasilan

### Indikator validasi selama capstone:
- Transaksi pemesanan dan pengajuan *skip* dari Web Portal maupun WhatsApp berhasil tersimpan ke database relasional dengan konsistensi data 100%.
- Dashboard Admin mampu memperbarui kuota porsi masak secara *real-time* dalam waktu $<3$ detik.
- Sistem berhasil menolak pengajuan *skip* yang melewati batas waktu cutoff (Lunch >08:30 WIB, Dinner >15:00 WIB) dengan presisi 100%.
- PIC UMKM dapat menjalankan alur verifikasi rekap porsi saat sesi demonstrasi dan memberikan penilaian kepuasan melalui survei akhir.

### Potensi indikator bisnis jika solusi diimplementasikan:
- Efisiensi waktu administrasi rekapitulasi harian katering hingga >60%.
- Pengurangan angka pesanan salah saji atau terlewat hingga 0%.
- Pengurangan potensi pemborosan bahan baku makanan (*food waste*) akibat pembatalan mendadak hingga 15–20%.

---

## L. Data dan Referensi

- **Website UMKM:** Tidak ada.
- **Media sosial UMKM:** Instagram (@namirims / akun resmi Namirims Catering).
- **Dokumen atau contoh proses:** File riil spreadsheet operasional: `2026-2027 Catering Namirims.xlsx` (139 kB, 3 lembar).
- **Data yang dapat digunakan:** Struktur katalog menu paket acara dan harian, skema harga per porsi, variabel data jadwal langganan harian, dan kluster lokasi pengantaran (Asrama IPB, Asrama Cifor, Kost).
- **Data yang tidak tersedia atau tidak dapat digunakan:** Informasi rekening pribadi UMKM dan data kontak pribadi sensitif mahasiswa.
- **Sumber data alternatif:** Dataset sintetis obrolan WhatsApp terverifikasi (`training_set_1740.jsonl` dan 600 skenario di `datasets/sealed/`) yang dibangun tim berdasarkan struktur data asli UMKM.
- **Ketentuan penggunaan data:** Data hanya digunakan untuk perancangan dan validasi prototipe Capstone Asah 2026; seluruh identitas asli pelanggan disamarkan (*anonymized*).

---

## M. Asumsi dan Batasan

- **Asumsi:** Mahasiswa wajib mengajukan *skip* jadwal makan sebelum jam *cutoff* yang ditetapkan katering (siang maks 08:30 WIB, malam maks 15:00 WIB); pengajuan melewati batas waktu tidak mendapatkan pengembalian kuota makan.
- **Keterbatasan data:** Dataset acuan berasal dari snapshot file Excel historis, bukan database cloud dinamis.
- **Keterbatasan akses:** Integrasi WhatsApp pada prototipe menggunakan environment webhook pengembang (WhatsApp Cloud API Test/Webhook Payload) untuk mensimulasikan aliran obrolan.
- **Keterbatasan waktu:** Waktu pengerjaan 4 minggu difokuskan secara disiplin pada MVP alur pemesanan, skip jadwal, dan rekap dapur harian.
- **Batasan prototype:** Solusi berupa prototipe fungsional untuk validasi dan demonstrasi kelayakan; implementasi komersial penuh memerlukan audit infrastruktur mandiri.

---

## N. Keterlibatan dan Tindak Lanjut UMKM

- **PIC untuk tindak lanjut:** Owner Namirims
- **Kontak PIC:** WhatsApp Owner Namirims
- **UMKM bersedia memberikan klarifikasi tambahan:** Ya
- **UMKM bersedia menerima demonstrasi:** Ya (Telah disetujui pada wawancara: *"Tentu, silahkan"*)
- **UMKM bersedia mencoba prototype jika memungkinkan:** Ya
- **UMKM bersedia memberikan feedback atau penilaian:** Ya
- **Catatan tindak lanjut:** Menjadwalkan sesi pertemuan daring/luring pada fase demonstrasi akhir masa Capstone untuk evaluasi langsung dan pengisian kuesioner *Final Survey*.

---

## O. Konfirmasi Akhir

- [x] Dokumen hanya berisi satu use case utama.
- [x] Masalah berasal dari hasil wawancara.
- [x] Masalah menjadi prioritas bagi UMKM.
- [x] Masalah memiliki dampak yang jelas.
- [x] Pengguna yang terdampak sudah diketahui.
- [x] Use case sesuai dengan skillset anggota tim.
- [x] Use case feasible dikerjakan dalam empat minggu.
- [x] Scope telah dipersempit menjadi satu MVP.
- [x] Tim memiliki waktu untuk melakukan demonstrasi dan perbaikan.
- [x] Bagian di luar scope sudah ditentukan.
- [x] Data atau referensi yang diperlukan sudah diketahui.
- [x] Indikator keberhasilan dapat dinilai.
- [x] PIC UMKM sudah ditentukan.
- [x] UMKM bersedia menerima demonstrasi dan memberikan penilaian.
- [x] Dokumen tidak menjanjikan implementasi produksi atau adopsi wajib.

---

# BAGIAN 2: SPESIFIKASI TEKNIS & ARSITEKTUR PRODUK

## 1. Topologi Sistem Dual-Intake

```
┌──────────────────────────────────────┐     ┌────────────────────────────────────────────────────────┐
│ PINTU 1: WEB SELF-SERVICE (CLIENT)   │     │ PINTU 2: WHATSAPP PASSIVE LISTENING (PaLiPi MODEL)     │
│ - Mahasiswa pesan/skip mandiri       │     │ - Obrolan asli pelanggan & admin                       │
│ - Form registrasi paket katering     │     │ - Mutable Living Buffer: Debounce 2.5s + Abort signal  │
│ - Kalender toggle skip tanggal makan │     │ - Intern-Decision-4B + QLoRA Logit Scoring Engine      │
│ - Mobile-first PWA (React + Vite)    │     │ - Grounding TDM & Deterministic Cutoff (08:30 / 15:00) │
└──────────────────┬───────────────────┘     └───────────────────────────┬────────────────────────────┘
                   │ Direct Verified JSON                                │ Staged Draft Proposal
                   ▼                                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ BACKEND REST API ORCHESTRATOR (Node.js / Express) & FASTAPI GEN AI SERVING                          │
│ - Routing: /api/v1/subscriptions, /api/v1/skips, /webhook/whatsapp, /v1/decision                    │
│ - Ingress Deduplication: wamid idempotency check & sliding buffer trailing-edge                     │
│ - PVE Pattern: Dilarang mutasi langsung ke manifes dapur; seluruh aksi masuk ke antrean HITL        │
└──────────────────┬─────────────────────────────────────────────────────┬────────────────────────────┘
                   │ Direct Web Mutate                                   │ Dynamic UPSERT
                   ▼                                                     ▼
┌──────────────────────────────────────────────┐     ┌────────────────────────────────────────────────┐
│ PRODUCTION MANIFEST (PostgreSQL)             │     │ HUMAN-IN-THE-LOOP (HITL) QUEUE (hitl_queue)    │
│ - catering_deliveries: Tanggal, Porsi, Sesi  │     │ - Status: DRAFT_PENDING (Auto-updated turns)   │
│ - Matriks Kluster Kos / Asrama (Bara, Cifor) │     │ - Digital Double: Kronologi chat lengkap       │
│ - Profil Alergi & Dietary Notes Pelanggan    │     │ - Customer Dossier: Alergi, sisa kuota, asrama │
└──────────────────▲───────────────────────────┘     └───────────────────────────┬────────────────────┘
                   │                                                             │
                   │ Persetujuan 1-Klik (Approve & Mutate)                       │ Tinjau Tiket
                   └─────────────────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ADMIN KITCHEN MANIFEST & HITL REVIEW DASHBOARD (React + Tailwind + Recharts)                        │
│ - Panel Kiri: Digital Double (Rekaman chat WhatsApp asli) + Customer Dossier (Alergi & Kuota)       │
│ - Panel Kanan: Staged Decision AI (Action, Tanggal, Sesi, Status Cutoff, Tombol 1-Click Approve)    │
│ - Header: Live counter porsi masak dapur hari ini per asrama (Pengganti Spreadsheet Excel)          │
│ - Visualisasi analitik Data Science: Tren skip & 7-day demand forecasting bahan baku dapur           │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Matriks Pemenuhan Rubrik Penilaian (Tri-Track Alignment)

| Jalur Belajar | Checklist Main Quest (Wajib) | Checklist Side Quest (Nilai Tambah) |
| :--- | :--- | :--- |
| **Full-Stack (FS)** | 1. Selesaikan problem nyata UMKM (rekap pesanan rutin & skip jadwal).<br>2. Dua fitur utama fungsional: Web Intake Pelanggan & Admin Manifest Dashboard.<br>3. Responsive di browser ponsel & laptop.<br>4. Umpan balik aksi jelas (loading, toast sukses/gagal).<br>5. Disertai petunjuk panduan penggunaan. | 1. Arsitektur Decoupled (Vite React + Express API).<br>2. Persistensi PostgreSQL & RESTful API `/api/v1/*`.<br>3. Backend reverse-proxy ke API model Gen AI.<br>4. Menyimpan log keputusan AI ke database.<br>5. Menampilkan dashboard visual Data Science.<br>6. Schema validation Joi & error fallback boundary. |
| **Gen AI (AE)** | 1. Dokumentasi problem di README & `AE_BIBLE.md`.<br>2. Model custom: Fine-tuned *Intern-Decision-4B* via QLoRA untuk keputusan operasional katering.<br>3. Preprocessing data percakapan & penanggalan grounded [0..8 hari].<br>4. Serving online via FastAPI (`Final_Pipeline_Architecture.py`).<br>5. Komparasi model Base vs LoRA pada 600 skenario Blind Sealed Benchmark (`datasets/run_all_sealed_benchmark.py`). | 1. Multi-head causal decision grid mendukung compound intent & multi-aksi (`secondary_actions`).<br>2. Pure logit candidate scoring (Zero token generation, hemat komputasi, kebal prompt injection).<br>3. Guardrail cutoff waktu deterministik (08:30 lunch / 15:00 dinner).<br>4. Integrasi Webhook WhatsApp / Backend Payload.<br>5. Swagger / OpenAPI live documentation. |
| **Data Science (DS)** | 1. Data wrangling lengkap file asli `2026-2027 Catering Namirims.xlsx` (Gathering, Assessing, Cleaning).<br>2. Menjawab pertanyaan bisnis: fluktuasi porsi & risiko pemborosan bahan dapur.<br>3. Menyajikan rekomendasi berbasis data.<br>4. Menyediakan data bersih/kamus data untuk tim FS & AE.<br>5. Verifikasi akurasi data sebelum integrasi. | 1. Dashboard analitik interaktif tren skip harian.<br>2. Predictive model: 7-day demand forecasting kebutuhan porsi (Prophet/LightGBM).<br>3. Sintesis dataset multi-turn percakapan mahasiswa.<br>4. Integrasi widget visualisasi langsung ke Dashboard Admin FS.<br>*Catatan*: Metodologi pembangkitan dataset, verifikasi 5 rubrik, dan riset SFT QLoRA Intern-Decision-4B yang divalidasi AE telah didokumentasikan di `AE_BIBLE.md`. |

---

## 3. Data Schema & Aturan Bisnis

### A. Skema Data Langganan Pelanggan
```json
{
  "student_id": "STD_001",
  "name": "Ahmad Fauzi",
  "phone": "081234567890",
  "dorm": "Asrama Sylvaplat A-12 IPB",
  "package": "nikmat",
  "daily_rate": 12000,
  "active": true,
  "quota_lunch": 15,
  "quota_dinner": 15,
  "schedule": {
    "2026-10-29": {
      "lunch": "SKIPPED",
      "dinner": "SCHEDULED",
      "notes": "Jangan pedas"
    }
  }
}
```

### B. Aturan Bisnis Cutoff Dapur
1. **Sesi Makan Siang (*Lunch*):** Batas waktu pengajuan maksimal pukul **08:30 WIB**. Pengajuan sesudah jam tersebut otomatis ditolak (`LUNCH_CUTOFF_EXCEEDED`); kuota tidak dikembalikan.
2. **Sesi Makan Malam (*Dinner*):** Batas waktu pengajuan maksimal pukul **15:00 WIB**. Pengajuan sesudah jam tersebut otomatis ditolak (`DINNER_CUTOFF_EXCEEDED`); kuota tidak dikembalikan.
3. **Akumulasi Kuota:** Pengajuan *skip* yang sah sebelum batas waktu akan menambah kredit kuota makan yang dapat digunakan untuk perpanjangan masa langganan.
4. **Eskalasi Komplain:** Laporan bahaya fisik makanan (*pecahan kaca, benda asing, basi*) otomatis dialihkan ke tiket penanganan manual Owner (`ESCALATE_OWNER`) dengan status `ESCALATED_TO_MANAGEMENT`.

---

## 4. Roadmap Pengerjaan Berbasis Fase (Milestone-Driven)

```
Fase 1: Fondasi, Wrangling Data, & Kontrak API
├─ DS: Data wrangling file Excel UMKM, susun Data Dictionary, sintesis data latih.
├─ FS: Setup boilerplate Vite React & Express API, rancang skema database 3NF.
└─ AE: Preprocessing data, benchmark baseline classifier & fine-tuning Intern-Decision-4B.

Fase 2: Pengembangan Modul Inti & Model Serving
├─ FS: Bangun UI Web Portal Pelanggan, Kitchen Manifest Admin, endpoint Webhook.
├─ AE: Serving FastAPI modul Final_Pipeline_Architecture.py (Passive Listening Engine).
└─ DS: Analisis pola tren skip data katering & bangun model demand forecasting porsi.

Fase 3: Integrasi Lintas Divisi & Hardening Sistem
├─ FS + AE: Integrasi Webhook WhatsApp ➔ Passive Listening Pipeline ➔ DB ➔ Dashboard Manifest.
├─ FS + DS: Sematkan visualisasi analitik & hasil forecast DS ke Dashboard Admin FS.
├─ ALL: Pemasangan guardrail cutoff waktu, error boundary, & deploy cloud (Vercel + Render).
└─ AE: Pengujian skenario multi-turn benchmark & evaluasi metrik GCR/latensi (datasets/run_benchmark.py).

Fase 4: Demonstrasi UMKM & Final Deliverables
├─ ALL: Sesi demonstrasi langsung dan uji coba alur bersama Owner Namirims.
├─ ALL: Pengambilan umpan balik dan pengisian kuesioner Final Survey oleh Owner.
├─ FS + AE + DS: Pembuatan video presentasi 10 menit, panduan SOP sistem, & README GitHub.
└─ ALL: Pengumpulan Project Brief dan final submission Capstone Asah 2026.
```
