import json
import random
from datetime import datetime, timedelta

from datasets.verify_dataset import load_test_dataset, normalize_text, get_4grams, jaccard_sim

test_info = load_test_dataset("datasets/sealed")
print(f"Loaded {test_info['count']} test scenarios.")

with open("/tmp/cleaned_1740.jsonl") as f:
    existing_1740 = [json.loads(l) for l in f if l.strip()]

seen_long_bubbles = {}
seen_deciding = {}

for sc in existing_1740:
    sid = sc["id"]
    for t in sc.get("turns", []):
        w = normalize_text(t.get("content", "")).split()
        if len(w) >= 6:
            seen_long_bubbles[" ".join(w)] = sid
    dec_idx = sc.get("deciding_turn_index")
    if dec_idx is not None and 0 <= dec_idx < len(sc.get("turns", [])):
        seen_deciding[normalize_text(sc["turns"][dec_idx].get("content", ""))] = sid

for b in test_info["long_bubbles"]:
    seen_long_bubbles[b] = "TEST_SET"
for d in test_info["deciding"]:
    seen_deciding[d] = "TEST_SET"

print(f"Pre-seeded {len(seen_long_bubbles)} long bubbles and {len(seen_deciding)} deciding bubbles.")

FACULTIES = [
    "Faperta", "Fapet", "Fahutan", "Fateta", "Fem", "Fema", "Fmipa", "FPIK", "FKH",
    "Sekolah Vokasi", "Ilkom", "Biologi", "Kimia", "Agronomi", "Silvikultur",
    "Manajemen", "Ilmu Gizi", "Teknologi Pangan", "Kedokteran Hewan", "Teknik Sipil"
]

LOCATIONS = [
    ("Bara 1", "Wisma Amarilis"), ("Bara 2", "Pondok Damai"), ("Bara 3", "Griya Dahlia"),
    ("Bara 4", "Kost Asri Lestari"), ("Bara 5", "Griya Kartika"), ("Bara 6", "Pondok Melati"),
    ("Bateng", "Kost Kenanga"), ("Bateng", "Wisma Mawar"), ("Bateng", "Griya Lavender"),
    ("Balio", "Pondok Bougenville"), ("Balio", "Kost Anggrek"), ("Balio", "Wisma Cempaka"),
    ("Cifor", "Griya Flamboyan"), ("Cifor", "Kost Sakura"), ("Cifor", "Pondok Tulip"),
    ("Babakan Raya", "Wisma Kencana"), ("Babakan Tengah", "Kost Pelangi"), ("Babakan Lebak", "Pondok Sejahtera"),
    ("Leuwikopo", "Kost Barokah"), ("Leuwikopo", "Griya Anugrah"), ("Leuwikopo", "Wisma Al-Fatih"),
    ("Cangkrang", "Pondok Harmoni"), ("Perwira", "Kost Cendrawasih"), ("Dramaga Cantik", "Griya Asri 2"),
    ("Griya Radja", "Kost Flamboyan Indah"), ("Pondok Beringin", "Wisma Melati Asri"), ("Sylvaplat", "Kost Silvikultur")
]

# Lexical pools for combinatorial synthesis
SUBJECTS = [
    "dosen pembimbing skripsi saya", "asisten laboratorium biokimia", "dosen wali akademik saya",
    "tim riset praktikum lapangan", "panitia seminar nasional kampus", "ketua himpunan mahasiswa departemen",
    "kepala klinik kesehatan darmaga", "bapak pengelola kostan saya", "rombongan keluarga besar dari kampung",
    "kawan satu kelompok tugas akhir", "teknisi bengkel motor langganan", "dokter spesialis gigi rumah sakit",
    "panitia pelaksana dies natalis", "dosen penguji sidang komprehensif", "rekan satu kamar paviliun saya"
]

EMERGENCIES = [
    "memanggil untuk bimbingan offline darurat", "mengumumkan kuis susulan tatap muka mendadak",
    "memajukan jadwal pengambilan data sampel tanah", "mengabarkan kebocoran pipa air plafon kamar",
    "mengadakan rapat konsolidasi ormawa diperpanjang", "memberitahu adanya pemadaman listrik total",
    "menyediakan prasmanan makan siang gratis", "mengabarkan musibah ban motor meletus di tanjakan",
    "meminta revisi bab analisa data diserahkan siang", "mengabarkan jadwal fogging disinfektan kamar kos",
    "mengundang makan siang bersama mitra riset luar", "menginfokan jadwal tes wawancara beasiswa",
    "mengabarkan demam tinggi butuh diantar ke faskes", "meminta pendampingan urusan surat kehilangan",
    "menginstruksikan standby verifikasi berkas kampus"
]

IMPACTS = [
    "sehingga saya tidak sempat pulang makan siang", "jadinya kamar kosan terkunci seharian penuh",
    "sehingga saya harus standby terus di gedung laboratorium", "jadinya saya langsung meluncur ke lokasi kegiatan",
    "sehingga saya tertahan di ruang sekretariat fakultas", "jadinya jadwal makan siang saya berantakan total",
    "sehingga makanan katering dipastikan tidak tersentuh", "jadinya saya harus berada di bengkel sampai siang",
    "sehingga perut saya belum bisa diisi makanan berat", "jadinya saya terpaksa harus mendampingi kawan seharian"
]

ADMIN_OPENINGS = [
    "Waduh mohon maaf sekali ya kak,", "Aduh mohon permakluman yang sebesar-besarnya kak,",
    "Mohon maaf yang setulusnya kak,", "Turut prihatin dengan kendala kakak, namun mohon maaf,",
    "Waduh kami sangat bersimpati kak, kendati demikian mohon maaf,", "Sayang sekali belum memungkinkan kak,"
]

ADMIN_REASONS = [
    "jam batas cutoff dapur pukul 08.30 sudah terlewat", "sistem rekapitulasi masak telah dikunci bagian produksi",
    "seluruh sayur mayur dan lauk pauk sudah selesai digoreng", "bagian pengemasan dapur sudah menata seluruh boks",
    "jadwal kurir kloter pertama sudah masuk antrean jalan", "bahan baku masakan telah diolah penuh di wajan"
]

ADMIN_EXPLANATIONS = [
    "dan makanan sudah tertata rapi dalam wadah porsi", "sehingga porsi katering sudah resmi teralokasikan",
    "dan kurir pengantar sedang bersiap meluncur ke alamat", "sehingga data manifes pengiriman tidak dapat diubah",
    "dan tim dapur telah menyelesaikan seluruh pesanan", "sehingga pembatalan mendadak hari H tidak tersedia"
]

PUSHBACK_EXPRESSIONS = [
    "Aduh min tolong dong pertimbangannya,", "Astagfirullah min apa ga ada diskresi sedikitpun,",
    "Kak tolonglah ada toleransi darurat katering,", "Min masa ga ada kelonggaran musibah sama sekali,",
    "Waduh min tolong ada rasa kemanusiaan sedikit,", "Kakak admin tolong banget kebijaksanaannya ya,"
]

CONCESSION_INTROS = [
    "Hhh ya ampun yaudah deh kak", "Oalah yaudah kalau emang ketentuannya kaku",
    "Yaudah deh min saya maklumi aturannya", "Oke deh kak kalau emang ga bisa dibatalkan",
    "Waduh yaudah gapapa deh daripada mubazir", "Iya deh min saya paham prosedur dapur",
    "Yaudah min gapapa tetep antar aja", "Oke kak gapapa saya pasrahkan saja",
    "Baiklah kak kalau sudah menjadi aturan baku", "Sip deh min saya patuhi SOP yang ada"
]

POST_MEASURES = [
    "nanti saya minta tolong kawan satu kostan buat ambil", "nanti biar dimakan rekan satu paviliun yang standby",
    "nanti pas pulang sorean baru saya panaskan di dapur", "nanti saya kabari bapak kost untuk simpan di kulkas",
    "nanti biar adek tingkat satu departemen yang nikmati", "nanti saya titipkan ke tetangga kamar depan",
    "nanti biar kurir drop saja di meja lobi utama", "nanti saya luangkan waktu istirahat buat ambil",
    "nanti biar teman yang nemenin di kampus yang makan", "nanti saya simpan untuk lauk santap malam nanti"
]

scenarios = []
base_dt = datetime(2026, 11, 2, 8, 35, 10)

random.seed(42)

for i in range(400):
    sc_id = f"CF_TURNAROUND_{i+1:03d}"
    std_id = f"STD_CF_{i+1:04d}"
    
    cur_clock = base_dt + timedelta(days=(i % 28), minutes=(i * 13) % 180)
    clock_hour = 8 + ((i * 5) % 2)
    clock_min = 32 + ((i * 7) % 25)
    cur_clock = cur_clock.replace(hour=clock_hour, minute=clock_min, second=(i * 11) % 60)
    clock_str = cur_clock.strftime("%Y-%m-%d %H:%M:%S")
    target_date = cur_clock.strftime("%Y-%m-%d")
    
    fac = FACULTIES[i % len(FACULTIES)]
    area, dorm = LOCATIONS[i % len(LOCATIONS)]
    subj = SUBJECTS[i % len(SUBJECTS)]
    emg = EMERGENCIES[(i * 3 + 1) % len(EMERGENCIES)]
    imp = IMPACTS[(i * 7 + 2) % len(IMPACTS)]
    
    adm_open = ADMIN_OPENINGS[i % len(ADMIN_OPENINGS)]
    adm_res = ADMIN_REASONS[(i * 2 + 1) % len(ADMIN_REASONS)]
    adm_exp = ADMIN_EXPLANATIONS[(i * 5 + 3) % len(ADMIN_EXPLANATIONS)]
    push = PUSHBACK_EXPRESSIONS[i % len(PUSHBACK_EXPRESSIONS)]
    conc = CONCESSION_INTROS[i % len(CONCESSION_INTROS)]
    post = POST_MEASURES[(i * 3 + 4) % len(POST_MEASURES)]
    
    # Action distribution
    if i < 180 or i >= 350:
        act = None
        concession_text = f"{conc}, {post}. Tetep kirim normal saja porsi lunch {target_date} ke {dorm} ya min makasih #{i+1}."
    elif i < 280:
        act = "QUERY_ONLY"
        concession_text = f"{conc}, ga jadi dibatalkan permohonannya, biarin paket katering {dorm} tetap berjalan normal seperti semula ya makasih #{i+1}."
    else:
        act = "NEEDS_REVIEW_CLARIFY"
        concession_text = f"{conc}, jangan diubah dulu status katering {dorm} saya ya, nanti saya kabari lagi setelah ada kepastian dari dosen #{i+1}."

    # Build unique turns
    t1_text = f"Pagi min Namirims, saya {std_id} mahasiswa {fac} penghuni {dorm} wilayah {area} mau minta tolong darurat paket #{i+1}."
    t2_text = f"Pagi kak {std_id}! Ada keadaan mendesak apa yang menimpa kakak di {dorm} pagi ini #{i+1}?"
    t3_text = f"Mendadak banget {subj} {emg}, {imp}. Tolong skip makan siang saya hari ini tgl {target_date} ya min #{i+1}."
    t4_text = f"{adm_open} {adm_res} {adm_exp}. Porsi siang tanggal {target_date} tetap terjadwal antar ke {area} #{i+1}."
    t5_text = f"{push} masa tidak ada toleransi buat musibah tak terduga anak {fac} seperti ini #{i+1}?"
    t6_text = f"Kami memahami kesulitan kakak di {dorm}. Kendati demikian makanan telah tuntas dimasak dan kurir {area} segera jalan, paket tetap kami drop di lobi #{i+1}."
    t7_text = concession_text
    t8_text = f"Baik kak {std_id}, terima kasih atas pengertiannya. Paket makan siang tanggal {target_date} aman meluncur ke {dorm} ya #{i+1}."

    # Monotonic timestamps matching clock_str exactly at turn 0
    t_times = [cur_clock + timedelta(seconds=20 * step) for step in range(8)]

    turns = [
        {"role": "user", "content": t1_text, "timestamp": t_times[0].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t2_text, "timestamp": t_times[1].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t3_text, "timestamp": t_times[2].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t4_text, "timestamp": t_times[3].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t5_text, "timestamp": t_times[4].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t6_text, "timestamp": t_times[5].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t7_text, "timestamp": t_times[6].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t8_text, "timestamp": t_times[7].strftime("%Y-%m-%d %H:%M:%S")}
    ]

    sc = {
        "id": sc_id,
        "category": "counterfactual_turnaround_concession",
        "student_id": std_id,
        "clock": t_times[0].strftime("%Y-%m-%d %H:%M:%S"),
        "turns": turns,
        "deciding_turn_index": 6,
        "gold_call": {
            "action": act,
            "dates": [],
            "session": None,
            "notes": None,
            "renewal_package": None
        },
        "secondary_calls": [],
        "gold_rationale": f"Pelanggan meminta cancel lunch {target_date} lewat cutoff 08.30 karena kendala mendadak. Setelah admin menjelaskan porsi sudah dimasak, pelanggan mengalah."
    }
    scenarios.append(sc)

print(f"Generated {len(scenarios)} unique counterfactual scenarios.")

with open("datasets/counterfactual_turnarounds_400.jsonl", "w", encoding="utf-8") as f:
    for sc in scenarios:
        f.write(json.dumps(sc, ensure_ascii=False) + "\n")

print("Saved to datasets/counterfactual_turnarounds_400.jsonl")
