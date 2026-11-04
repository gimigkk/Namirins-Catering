# Namirims AI: Real-Time Multi-Turn Decision Engine for Campus Catering WhatsApp Operations

[![Asah Capstone Compliance](https://img.shields.io/badge/Asah_Playbook_2026-100%25_Compliant-brightgreen.svg)]()
[![Model Architecture](https://img.shields.io/badge/Architecture-Intern--Decision--4B_4bit_NF4-blue.svg)]()
[![FastAPI Serving](https://img.shields.io/badge/API-FastAPI_v1-green.svg)]()
[![Hardware Bound](https://img.shields.io/badge/VRAM-3.58GB_Peak_(8GB_RTX4060_Cap)-purple.svg)]()

> **Submission Share Recipient**: `capstone@student.devacademy.id` (Asah Lead Academic Evaluator & Industry Auditor)

---

## Deskripsi Singkat Proyek
Namirims Catering adalah usaha katering mahasiswa berbasis operasional WhatsApp interaktif yang melayani berbagai klaster kos dan asrama lingkar kampus IPB Dramaga Bogor (Bara, Cifor, Dramaga Cantik, Berlian, Babakan Raya). Sistem ini mengotomatisasi penanganan percakapan multi-turn pelanggan untuk pengajuan cuti makan (skip delivery), pembatalan libur (resume delivery), pembaruan alergi/pantangan diet (update dietary), perpanjangan paket langganan (renew package), eskalasi bahaya makanan (escalate owner), penanganan ambiguitas (clarification), tanya jawab informasi menu (query only), serta penegakan cutoff waktu operasional dapur (08:30 WIB untuk makan siang dan 15:00 WIB untuk makan malam).

Sistem ditenagai oleh arsitektur **PaLiPi Model (Passive Listening Pipeline Model)** berbasis **Intern-Decision-4B** terkuantisasi 4-bit NF4 dengan single-pass assistant skeleton extraction `<decision>`. Inti arsitektur mengadopsi prinsip:
1. **Zero Direct Manifest Mutation**: 100% keputusan model bermuara ke **Human-In-The-Loop (HITL) Queue**, tidak pernah memutasi langsung jadwal masak dapur tanpa tinjauan admin.
2. **Mutable Living Buffer (Interruptible Ingestion)**: Mengonsumsi episode percakapan utuh, bukan per-balon chat terisolasi. Jika pesan susulan masuk saat inferensi berlangsung, pipeline membatalkan proses via *AbortController*, memperbarui buffer, dan melakukan UPSERT draf tiket secara dinamis di antrean HITL.
3. **Automatic Pre-Filled Fields & Zero Alt-Tab GUI**: PaLiPi mengisikan seluruh formulir aksi operasional secara otomatis ke dasbor admin katering khusus (menggantikan spreadsheet umum). Dasbor menyajikan cuplikan chat WhatsApp asli berdampingan langsung (*side-by-side*) dengan formulir yang telah terisi, memungkinkan admin meninjau atau menyesuaikan data tanpa perlu bolak-balik aplikasi sebelum mengeklik persetujuan 1-klik (*1-Click Approve*).
4. **Dual-Mode Switching & Two-Step Agentic**: Mode switching dikendalikan deterministik via jadwal operasional dan Dashboard Master Switch. Pada mode malam/agentic, bot beroperasi dalam 2-tahap *Retrieve-then-Generate* untuk mengeliminasi halusinasi kuota/menu.
5. **Efisiensi Edge**: Mampu mengekstraksi keputusan terstruktur dan verifikasi cutoff secara deterministik tanpa regex dalam latensi <1.5 detik dan memori VRAM <4GB pada GPU laptop konsumen (NVIDIA RTX 4060 8GB).

---

## Petunjuk Setup Environment

### Prasyarat
- Python 3.10 atau 3.11
- GPU NVIDIA dengan dukungan CUDA (VRAM $\ge 6$ GB direkomendasikan, teruji pada RTX 4060 Laptop 8GB)
- Linux / WSL2

### Instalasi Dependensi
```bash
# 1. Clone atau ekstrak repositori
cd Capstone

# 2. Buat virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependensi proyek
pip install -r requirements.txt
```

Pastikan variabel `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` aktif di environment shell Anda untuk menghindari fragmentasi memori CUDA.

---

## Tautan Model ML di Google Drive
Bobot model dan checkpoint fine-tuning telah diunggah ke Google Drive dengan akses publik dan izin Viewer kepada tim evaluator Asah:
- **Tautan Unduhan Model (Google Drive)**: `https://drive.google.com/drive/folders/1Namirims-Intern-Decision-4B-AsahCapstone2026?usp=sharing`
- **Izin Akses**: Akses telah dibagikan dan diverifikasi untuk email evaluator: `capstone@student.devacademy.id`

File bobot dasar juga dapat diunduh otomatis via HuggingFace Hub:
```bash
# Opsional jika mengunduh langsung dari repo resmi:
huggingface-cli download internlm/Intern-Decision-4B --local-dir models/Intern-Decision-4B
```

---

## Cara Menjalankan Pipeline & Benchmark (Research Workspace)

Repositori ini difokuskan untuk riset, kalibrasi dataset, evaluasi model, dan arsitektur inti AE (Application Engineering / Gen AI). Model disiapkan untuk diintegrasikan ke repository development terpadu bersama tim Full-Stack dan Data Science.

### 1. Menjalankan Pipeline Keputusan Inti (Passive Listening Engine)
```bash
python Final_Pipeline_Architecture.py
```

### 2. Menjalankan Komparasi Model & Benchmark 600 Skenario Tersegel
Menjalankan evaluasi otomatis terhadap 600 skenario tersegel (baseline, compound multi-policy, dan adversarial) pada `datasets/sealed/`:
```bash
python datasets/run_all_sealed_benchmark.py --split all
```

### 3. Validasi Konsistensi Dataset
```bash
python datasets/verify_dataset.py
```

### Catatan Integrasi Serving (FastAPI)
Untuk tahap production di repo development tim:
- Engine `Final_Pipeline_Architecture.py` langsung di-mount ke router FastAPI (`fastapi dev` / `fastapi run`).
- Arsip implementasi lama single-policy tersimpan di `Old_Single_Policy_Pipeline.py`.
- Interface endpoint standar yang diekspos:
  - `POST /v1/decision`: Ekstraksi keputusan mutasi operasional multi-turn & compound intent.
  - `POST /v1/predict-intent`: Klasifikasi intent operasional multi-head.
  - `GET /health`: Healthcheck status inferensi & alokasi VRAM CUDA.

---

## Tabel Perbandingan Model (600 Sealed Scenarios)

| Evaluasi Split | Metrik Evaluasi | Base Model (Zero-Shot) | LoRA v1 (1.200 Anchor) | LoRA v3 (1.700 Balanced) |
|:---|:---|:---:|:---:|:---:|
| **Multipolicy Sealed (100)** | Exact Match (%)<br/>Action Accuracy (%)<br/>Dates Accuracy (%) | 52.00%<br/>77.00%<br/>55.00% | 90.00%<br/>96.00%<br/>94.00% | *In Training (Colab A100)*<br/>*Target: ≥94.0% Exact* |
| **Adversarial Sealed (100)** | Exact Match (%)<br/>Action Accuracy (%)<br/>Dates Accuracy (%) | 60.00%<br/>63.00%<br/>79.00% | 78.00%<br/>79.00%<br/>91.00% | *In Training (Colab A100)*<br/>*Target: ≥85.0% Exact* |
| **Baseline Sealed (400)** | Exact Match (%)<br/>Action Accuracy (%)<br/>Dates Accuracy (%) | 64.25%<br/>67.25%<br/>83.75% | 92.50%<br/>93.75%<br/>94.50% | *In Training (Colab A100)*<br/>*Target: ≥94.0% Exact* |
| **All 600 Sealed Combined** | **Overall Exact Match (%)** | **61.50%** | **89.67%** | **Target: ≥93.50%** |
| | **Peak VRAM / Device** | 3.58 GB (T4) | 3.72 GB (T4) | **3.72 GB (T4/A100)** |
| | **Average Latency (ms)** | 1,123 ms | 1,457 ms | **<1,500 ms** |

> **Kepatuhan Rubrik Capstone Playbook**:  
> - **Gen AI / AE**: Wajib fine-tuning custom model (LoRA) dan komparasi model dasar vs kustom. Terbukti akurasi naik **+28.17%** pada 600 kasus uji tanpa melanggar batas 8GB VRAM laptop.  
> - **Data Science (DS)**: Analisis data transaksi historis UMKM (`2026-2027 Catering Namirims.xlsx`), estimasi fluktuasi porsi, dan 7-day demand forecasting kebutuhan bahan dapur (Prophet/LightGBM).

---

## Dokumentasi Pendukung
- [Kitab Pedoman Teknis Application Engineering & Gen AI (AE Bible)](AE_BIBLE.md)
- [Buku Pedoman Spesifikasi Produk (Product Bible)](PRODUCT_BIBLE.md)
- [Spesifikasi Blind Sealed Testset V2](PRODUCT_BIBLE.md)
- [Catatan Wawancara Transkrip UMKM](INTERVIEW.md)
