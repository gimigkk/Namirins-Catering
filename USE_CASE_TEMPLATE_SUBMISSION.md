# Asah 2026 - Template Use Case UMKM

## Petunjuk Pengisian
- Dokumen dibuat untuk satu UMKM dan satu use case.
- Bagian yang sebelumnya di-bold dan di-highlight kuning telah diisi secara lengkap tanpa highlight kuning.
- Informasi berasal langsung dari hasil wawancara dengan UMKM Namirims Catering.
- Menggunakan bahasa bisnis yang mudah dipahami, realistis, dan berfokus pada alur utama MVP.

---

## A. Informasi Umum

**Nama UMKM:**  
Namirims Catering

**Bidang usaha:**  
Jasa Boga / F&B (Katering Harian Asrama & Paket Acara)

**Nama narasumber:**  
Owner Namirims

**Peran narasumber:**  
Pemilik / Pengelola Utama (Owner)

**PIC UMKM:**  
Owner Namirims

**Kontak PIC:**  
WhatsApp Owner Namirims

**Tanggal interview:**  
27 Oktober 2026

**Nama tim:**  
[Isi nama tim Capstone]

**Anggota tim:**  
1. Rafid (Ilmu Komputer IPB 61) - Full-Stack / Project Lead  
2. [Nama Anggota 2] - Full-Stack  
3. [Nama Anggota 3] - Gen AI  
4. [Nama Anggota 4] - Gen AI  
5. [Nama Anggota 5] - Data Science  
6. [Nama Anggota 6] - Data Science  

**Status validasi use case:**  
Sudah dikonfirmasi oleh UMKM

---

## B. Penentuan Use Case

Dari seluruh masalah yang ditemukan selama interview, tim memilih satu masalah sebagai fokus capstone.

### Masalah yang ditemukan dari hasil interview:
1. Perluasan pasar daring masih rendah; promosi Instagram belum menghasilkan pemesan rutin dan WhatsApp hanya mengandalkan kabar dari mulut ke mulut.
2. Pencatatan pesanan rutin harian masih dilakukan secara manual dan berulang, menyita banyak waktu operasional.
3. Terjadi kesalahan pencatatan data dan adanya pesanan yang terlewat, terutama saat menangani permintaan penyesuaian atau pengajuan skip jadwal makan dari pelanggan.

### Masalah yang dipilih sebagai use case:
Inakurasi dan inefisiensi rekapitulasi katering harian akibat pencatatan pesanan rutin dan penanganan pengajuan skip jadwal pelanggan yang masih manual (menyelesaikan masalah nomor 2 dan 3 sekaligus sebagai satu kesatuan rantai sebab-akibat operasional).

### Alasan menjadi prioritas bagi UMKM:
Masalah nomor 2 (proses pencatatan manual) dan nomor 3 (salah catat & pesanan terlewat pada skip jadwal) adalah satu kesatuan masalah operasional yang ditegaskan langsung oleh Owner katering sebagai kendala paling mendesak yang memengaruhi kinerja usaha sejak awal berdiri (chat 15.21, 15.28, 15.34). Otomasi pencatatan pesanan baru tidak akan efektif jika pengajuan skip jadwal harian tetap bocor secara manual, sehingga kedua masalah ini wajib diselesaikan bersamaan dalam satu alur terpadu.

### Skill yang dibutuhkan:
- Full-Stack Web Development (Frontend antarmuka pengguna, Backend REST API, Database Management).
- Gen AI & NLP (Decision Model, Intent Classification, Prompt Engineering).
- Data Science (Data Wrangling, Exploratory Data Analysis, Demand Forecasting).

### Skill yang dimiliki anggota tim:
- Full-Stack: React, Vite, Node.js/Express, PostgreSQL, Tailwind CSS.
- Gen AI: Model Fine-Tuning, PyTorch, HuggingFace, FastAPI Model Serving, LangChain.
- Data Science: Python Data Wrangling, Pandas, Scikit-learn, Time-Series Forecasting.

### Skill yang belum dimiliki tim:
Tidak ada.

### Cara mengatasi kekurangan skill:
Melakukan pembagian tugas yang jelas sesuai learning path, menyepakati kontrak data dan API sejak fase awal, serta membatasi cakupan sistem pada alur MVP yang terdefinisi dengan ketat.

### Pemeriksaan kelayakan timeline capstone (4 minggu):
- [x] Alur utama dapat dikembangkan dalam empat minggu.
- [x] Data atau data dummy dapat disiapkan.
- [x] Solusi dapat diuji tanpa integrasi ke sistem produksi UMKM.
- [x] Tim memiliki skill utama yang diperlukan.
- [x] Ketergantungan kepada pihak lain dapat dihindari atau dikelola.
- [x] UMKM bersedia menerima demonstrasi dan memberikan feedback.
- [x] Tim memiliki waktu untuk pengujian dan perbaikan.

### Kesimpulan pemilihan use case:
Use case ini dipilih karena merupakan masalah operasional paling mendesak yang langsung diminta oleh Owner UMKM untuk mencegah salah catat data dan pesanan terlewat, sesuai dengan kemampuan tim dalam Full-Stack Development, Decision Model AI, dan Data Analytics, serta dapat dikembangkan dalam waktu empat minggu dengan membatasi scope pada otomasi intake pesanan/skip jadwal mandiri via Web Portal dan WhatsApp Bot, serta penyediaan Dashboard Kitchen Manifest untuk rekap harian Owner.

---

## C. Judul Use Case

**Sistem Terpadu Manajemen Katering Harian: Dashboard Operasional Owner dan Intake Pemesanan Mandiri Berbasis Web & WhatsApp Agentic AI**

---

## D. Ringkasan Use Case

**Ringkasan Use Case:**  
**Owner dan pengelola operasional Namirims Catering** mengalami **kesalahan pencatatan data dan adanya pesanan yang terlewat** ketika menjalankan **proses rekapitulasi pesanan rutin dan penanganan pengajuan skip jadwal makan pelanggan secara manual dari chat ke spreadsheet umum**. Masalah utama berakar pada *context-switching fatigue*: admin membaca chat WhatsApp di ponsel, berpindah aplikasi ke spreadsheet di laptop, mencari baris nama pelanggan, lalu mengetik ulang tanggal dan sesi. Di saat jam sibuk (*rush hour* sebelum cutoff), admin kerap membaca chat namun **lupa atau terlewat menginputnya ke spreadsheet**.

Sebagai solusinya, tim mengembangkan **Sistem Informasi (SI) Terpadu Operasional Katering Khusus** (menggantikan lembar spreadsheet umum) yang dilengkapi **fitur pengisian formulir otomatis (*Automatic Pre-Filled Fields*)** bertenaga **WhatsApp Passive Listening AI (PaLiPi)**. Saat chat masuk, model AI membedah isi pesan dan langsung mengisikan seluruh kolom aksi operasional secara otomatis ke antrean draf tinjauan admin. Admin **tidak perlu berpindah-pindah aplikasi (tanpa bolak-balik WhatsApp-Spreadsheet)** karena antarmuka web langsung menyajikan **cuplikan chat asli (*chat snippet*) berdampingan langsung (*side-by-side*) dengan formulir yang telah terisi otomatis**. Admin cukup membuka aplikasi, memverifikasi hasil pembacaan AI dengan melihat cuplikan chat di sampingnya, melakukan penyesuaian cepat bila diperlukan, dan mengeklik satu tombol persetujuan (*1-Click Approve*) untuk menyinkronkan data langsung ke manifes dapur.

---

## E. Latar Belakang

**Produk atau layanan utama:**  
1. Paket Acara: Paket Hemat (Rp10.500), Paket Nikmat (Rp12.000), Paket Kenyang (Rp15.000).  
2. Paket Harian: Katering makan harian rutin untuk asrama dan kost mahasiswa (Rp12.000 – Rp16.000/porsi).

**Target customer:**  
Pelanggan utama saat ini adalah penghuni Asrama IPB (kerja sama jangka panjang stabil), Asrama Cifor, dan mahasiswa kost sekitar. Rencana ke depan menargetkan asrama sekolah lain dan pesanan acara harian.

**Kanal penjualan atau pelayanan:**  
WhatsApp, Instagram, dan Penjualan Offline.

**Tools yang digunakan saat ini:**  
WhatsApp untuk percakapan pesanan dan Google Spreadsheet untuk pencatatan rekapitulasi.

**Gambaran bisnis:**  
Namirims Catering berdiri sejak tahun 2017, berawal dari penawaran ke tetangga sekitar hingga kini dipercaya menyuplai kebutuhan makan harian institusi asrama seperti Asrama IPB dan Asrama Cifor. Bisnis beroperasi secara rutin setiap hari untuk melayani makan siang dan makan malam penghuni asrama dengan jadwal dan preferensi makan yang dinamis.

---

## F. Masalah Prioritas

**Proses bisnis saat ini:**  
Pelanggan bertanya ➔ Pemberian Menu dan Biaya ➔ Pelanggan memesan ➔ Dicatat manual & diproses ➔ Pembayaran ➔ Pengiriman/diterima pelanggan ➔ Penanganan keluhan.

**Masalah utama:**  
Pencatatan manual pesanan rutin harian dan pengajuan skip jadwal makan dari pelanggan yang masih dikerjakan satu per satu dari chat WhatsApp ke spreadsheet umum. Friksi mental akibat bolak-balik aplikasi antara WhatsApp dan spreadsheet menyebabkan admin kerap membaca chat tetapi **lupa memasukkan datanya ke spreadsheet**.

**Contoh kejadian:**  
Pelanggan asrama mengirim pesan izin tidak makan (skip) via chat WhatsApp pukul 08:15 WIB sebelum batas cutoff. Admin sempat membaca pesan di ponsel, namun karena terdistraksi dan harus membuka laptop untuk mengedit spreadsheet, admin **lupa mencatatnya ke baris Excel pelanggan**. Akibatnya, porsi makan tetap dibuat dan dikirim ke asrama, memicu pemborosan makanan bagi katering dan sengketa sisa kuota langganan pelanggan.

**Frekuensi masalah:**  
Terjadi setiap hari pada siklus produksi makan siang dan makan malam.

**Pihak yang terdampak:**  
Owner/Admin katering (beban waktu rekapitulasi manual) dan pelanggan katering (makanan salah kirim atau pesanan terlewat).

**Dampak terhadap bisnis atau customer:**  
Waktu kerja operasional terbuang hingga 1–2 jam per hari untuk sinkronisasi manual, timbulnya potensi pemborosan bahan makanan akibat porsi batal yang terlanjur dimasak, serta penurunan kepuasan pelanggan.

**Penanganan saat ini:**  
Admin memeriksa pesan WhatsApp secara berkala dan mengetikkan perubahan data secara manual ke Google Spreadsheet.

---

## G. Target Pengguna

**Pengguna utama:**  
Owner / Admin Operasional Namirims Catering.

**Pengguna lain yang terlibat:**  
Mahasiswa pelanggan katering harian (penghuni Asrama IPB, Asrama Cifor, dan Kost Babakan).

**Penerima manfaat:**  
Pengelola katering dan seluruh pelanggan langganan aktif.

---

## H. Tujuan dan Outcome Bisnis

**Tujuan utama:**  
Use case ini bertujuan membantu **Owner Namirims Catering dan pelanggan katering** untuk **mencatat pesanan rutin dan memproses pengajuan skip jadwal makan secara otomatis melalui Web Portal Mandiri serta WhatsApp Bot cerdas**, sehingga **operasional rekapitulasi harian berjalan lebih efisien, teratur, dan bebas dari pesanan terlewat**.

**Outcome yang diharapkan:**  
- Tersedianya ringkasan porsi masak harian (Kitchen Manifest) otomatis tanpa input ganda manual.
- Pengajuan skip jadwal pelanggan langsung terekam dan memotong kuota produksi sebelum batas waktu dapur masak.
- Catatan permintaan diet khusus pelanggan terdokumentasi rapi dan lengkap.

---

## I. Arah Solusi dan Scope MVP

**Arah solusi:**  
Membangun sistem katering terpadu berbasis aplikasi web yang menggantikan pencatatan spreadsheet manual dengan menyediakan dua pintu masuk transaksi (Dual-Intake):
1. **Web Portal Mandiri:** Formulir web responsif bagi pelanggan untuk mendaftar paket katering atau memilih tanggal izin tidak makan (*skip*) secara mandiri tanpa harus menunggu balasan chat admin.
2. **Asisten WhatsApp Cerdas (Dual-Mode):** Kanal percakapan interaktif bagi pelanggan yang terbiasa menggunakan WhatsApp. Dilengkapi kecerdasan buatan (AI) yang mampu memahami bahasa santai/singkatan mahasiswa, mengekstrak tanggal izin makan dan catatan khusus secara otomatis, serta memeriksa kepatuhan batas waktu masak (*cutoff* dapur). Sistem ini menyediakan dua mode operasional: mode asisten aktif untuk menjawab cepat saat jam sibuk, serta mode menyimak pasif untuk mendata otomatis dari percakapan saat pengelola membalas manual.  
Seluruh data dari kedua pintu masuk mengalir terpusat ke satu Dashboard Operasional Admin katering secara real-time.

**Pengguna utama MVP:**  
Owner / Admin Pengelola Namirims Catering.

**Masalah utama yang diselesaikan:**  
Pencatatan manual pesanan rutin harian dan penanganan pengajuan skip jadwal pelanggan yang memicu salah catat data dan pesanan terlewat.

**Alur utama MVP:**  
1. Pelanggan memilih paket langganan atau mengajukan izin tidak makan (*skip*) melalui Web Portal Mandiri atau chat WhatsApp.
2. Pada kanal WhatsApp, kecerdasan buatan (PaLiPi) memahami maksud pesan, mengekstrak rincian tanggal serta sesi makan yang diajukan, memeriksa aturan batas waktu dapur (Cutoff: siang maks 08:30 WIB, malam maks 15:00 WIB), dan **mengisi seluruh kolom formulir aksi operasional secara otomatis (*Automatic Pre-Filled Fields*)**.
3. Hasil pembacaan sistem dimasukkan ke dalam **Antrean Verifikasi Transaksi (Verification Queue)** pada dashboard pengelola dengan tata letak berdampingan (*side-by-side*): cuplikan chat WhatsApp asli ditampilkan di sebelah formulir yang telah terisi otomatis (*zero alt-tab*).
4. Pengelola memverifikasi data tanpa perlu membuka WhatsApp lagi, dapat melakukan penyesuaian cepat langsung pada formulir bila diperlukan, dan menyetujui transaksi dengan satu klik (*1-Click Approve*). Jadwal langganan dan ringkasan porsi masak harian dapur (*Kitchen Manifest*) otomatis terpotong rapi tanpa risiko salah hitung manual.

**Cakupan MVP:**  
- **Web Portal Mandiri:** Halaman pendaftaran paket katering dan kalender interaktif pengajuan izin tidak makan pelanggan.
- **Asisten WhatsApp AI Dual-Mode (PaLiPi):** Modul kecerdasan buatan pemroses percakapan WhatsApp untuk mengenali maksud pesan, mengekstrak rincian tanggal/sesi makan, memvalidasi batas waktu operasional dapur, mengisi formulir aksi operasional secara otomatis (*pre-fill form*), serta mengalihkan pesan darurat langsung ke pengelola.
- **Dashboard Operasional Kitchen Manifest:** Dasbor pengelola katering khusus pengganti spreadsheet umum untuk memantau ringkasan total porsi siap masak harian per lokasi asrama, catatan diet khusus pelanggan, serta panel antrean verifikasi terpadu (cuplikan chat berdampingan dengan formulir pre-filled) untuk menyetujui mutasi jadwal sebelum dicatat permanen.
- **Visualisasi Analitik Tren Langganan:** Panel grafik sederhana pada dasbor pengelola untuk melihat tren jumlah pembatalan porsi harian dan membantu perencanaan bahan baku dapur.

**Bentuk demonstrasi kepada UMKM:**  
Memperagakan pengajuan izin tidak makan melalui Web Portal dan WhatsApp, menunjukkan ekstraksi AI yang langsung mengisi formulir di dashboard admin secara otomatis (*pre-filled*), menampilkan cuplikan chat asli berdampingan dengan formulir verifikasi (*tanpa bolak-balik WhatsApp*), mendemonstrasikan penyesuaian cepat dan persetujuan 1-klik oleh admin, serta membuktikan ringkasan porsi masak dapur yang seketika berkurang akurat.

**Di luar scope:**  
- Integrasi pembayaran otomatis (payment gateway / QRIS otomatis).
- Fitur pelacakan lokasi kurir pengantaran secara GPS real-time.
- Otomasi promosi pemasaran media sosial Instagram.
- Sistem pencatatan akuntansi keuangan dan penggajian karyawan katering.

---

## J. Hasil yang Diharapkan

Pada akhir capstone, tim diharapkan menghasilkan:
- Aplikasi Web MVP fungsional yang mencakup Web Portal Pelanggan dan Dashboard Operasional Pengelola.
- Layanan integrasi kecerdasan buatan (AI) percakapan WhatsApp untuk pengenalan maksud pesan dan ekstraksi data jadwal makan.
- Buku panduan ringkas penggunaan Dashboard Operasional bagi pengelola katering.
- Laporan hasil demonstrasi, pengujian bersama UMKM, dan kuesioner umpan balik akhir.

---

## K. Indikator Keberhasilan

**Indikator validasi selama capstone:**  
- Transaksi pemesanan dan pengajuan skip jadwal dari Web Portal maupun WhatsApp berhasil tersimpan ke sistem dengan konsistensi data 100%.
- Dashboard Operasional mampu memperbarui rekap porsi masak secara real-time dalam waktu kurang dari 3 detik setelah disetujui.
- Sistem memvalidasi kepatuhan batas waktu operasional (*cutoff*) makan siang dan makan malam dengan presisi 100%.
- Pengelola UMKM dapat mengoperasikan alur verifikasi dasbor dengan lancar saat sesi demonstrasi dan memberikan penilaian kepuasan melalui survei akhir.

**Potensi indikator bisnis jika solusi diimplementasikan:**  
- Peningkatan efisiensi waktu kerja admin pada proses rekapitulasi harian porsi makan siang dan malam.
- Pencegahan kesalahan saji atau pesanan terlewat melalui sinkronisasi data jadwal otomatis.
- Pengurangan potensi pemborosan bahan baku makanan berlebih akibat pembatalan jadwal makan yang terlambat dicatat.

---

## L. Data dan Referensi

**Website UMKM:**  
Tidak ada

**Media sosial UMKM:**  
Instagram: @namirims (akun resmi Namirims Catering)

**Dokumen atau contoh proses:**  
File riil spreadsheet operasional: `2026-2027 Catering Namirims.xlsx` (3 lembar, 139 kB) serta arsip riil ekspor riwayat percakapan WhatsApp pemesanan dan pengajuan skip jadwal katering.

**Data yang dapat digunakan:**  
Daftar paket menu katering, harga per porsi, variabel format rekapitulasi jadwal harian, nama-nama kluster asrama/kost pengantaran, serta transkrip riwayat percakapan chat WhatsApp asli (setelah proses anonimisasi PII nama dan kontak pelanggan) sebagai data latih dan uji coba model NLP.

**Data yang tidak tersedia atau tidak dapat digunakan:**  
Data informasi rekening perbankan dan data identitas pribadi sensitif pelanggan.

**Sumber data alternatif:**  
Augmentasi data sintetis terarah untuk memperkuat kelas minoritas (skenario komplain makanan basi, sengketa pembayaran, dan batas cutoff kritis) berbasis pola bahasa dari data riil.

**Ketentuan penggunaan data:**  
Data hanya digunakan untuk perancangan, pelatihan model, dan pengujian MVP Capstone Asah 2026; seluruh nama dan nomor kontak pribadi pelanggan asli disamarkan (anonymized).

---

## M. Asumsi dan Batasan

- **Asumsi:** Pelanggan wajib mengajukan skip jadwal sebelum jam batas waktu (cutoff) yang ditentukan katering (makan siang maks 08:30 WIB, makan malam maks 15:00 WIB) agar kuota makan dapat dialihkan.
- **Keterbatasan data & Integrasi:** Sistem menerapkan skema migrasi data satu arah; data historis spreadsheet diimpor ke basis data aplikasi untuk operasional, dan laporan rekapitulasi baru dapat diekspor kembali dalam format lembar sebar tanpa sinkronisasi langsung dua arah ke file Excel lokal UMKM.
- **Batasan Saluran Intake:** Web Portal bertindak sebagai antarmuka pemesanan primer yang deterministik; bot WhatsApp sandbox bertindak sebagai antarmuka alternatif untuk demonstrasi integrasi AI percakapan.
- **Keterbatasan akses:** Integrasi WhatsApp pada prototipe menggunakan nomor uji coba pengembang (WhatsApp Cloud API sandbox) untuk menjaga keamanan nomor bisnis UMKM.
- **Keterbatasan waktu:** Waktu pengerjaan difokuskan secara ketat pada alur utama pemesanan, skip jadwal, dan rekapitulasi porsi dapur.
- **Batasan prototipe:** Solusi berupa prototipe fungsional untuk demonstrasi dan validasi, belum mencakup infrastruktur skala produksi komersial penuh.

---

## N. Keterlibatan dan Tindak Lanjut UMKM

**PIC untuk tindak lanjut:**  
Owner Namirims

**Kontak PIC:**  
WhatsApp Owner Namirims

**UMKM bersedia memberikan klarifikasi tambahan:**  
Ya

**UMKM bersedia menerima demonstrasi:**  
Ya (Telah disetujui pada sesi wawancara: "Tentu, silahkan")

**UMKM bersedia mencoba prototype jika memungkinkan:**  
Ya

**UMKM bersedia memberikan feedback atau penilaian:**  
Ya

**Catatan tindak lanjut:**  
Menjadwalkan pertemuan langsung atau daring pada fase pengujian akhir Capstone untuk demonstrasi aplikasi, uji coba alur menggunakan perangkat pengujian yang disediakan tim, dan pengisian survei evaluasi akhir oleh PIC UMKM.

---

## O. Konfirmasi Akhir

Sebelum dokumen digunakan sebagai acuan capstone, pastikan:
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
