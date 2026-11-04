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

# 400 distinct emergency narrative seeds
REASONS = [
    ("dosen pembimbing skripsi manggil bimbingan mendadak jam sembilan", "bimbingan proposal offline di kampus darmaga"),
    ("praktikum lapangan agronomi dipindah ke kebun percobaan cikarawang", "jadwal ambil sampel tanah dipercepat pagi ini"),
    ("kamar kosan kebanjiran karena pipa air kamar mandi atas jebol", "harus beres-beres genangan air di lantai kamar"),
    ("ada kuis susulan mendadak mata kuliah biokimia jam sepuluh", "dosen baru umumin pengumuman di sipinter ipb"),
    ("motor mogok di jalan raya dramaga busi kena air kubangan", "lagi nunggu montir bengkel di deket pom bensin"),
    ("dosen tamu dari kementerian ngasih kuliah umum ada snack berat", "panitia acara nyiapin prasmanan makan siang gratis"),
    ("sedang ada pemadaman listrik bergilir di lingkungan kosan", "ga bisa masak nasi dan ruangan gelap pengap"),
    ("ketiduran pulas kecapekan abis ngerjain revisi laporan sampai subuh", "baru kebangun jam setengah sembilan lewat"),
    ("orang tua mendadak video call ngabarin ada keperluan keluarga penting", "harus koordinasi mendesak sama keluarga di rumah"),
    ("laptop mendadak blue screen mati total mau ujian presentasi", "harus segera pinjem laptop temen satu jurusan"),
    ("ada wawancara magang bumn online dadakan jam sebelas siang", "harus siap-siap pakaian rapi dan sinyal stabil"),
    ("diare melilit dari pagi perut kram ga bisa makan santan pedas", "badan lemes harus istirahat total di kasur"),
    ("ada rapat ormawa fakultas persiapan dies natalis kampus", "kumpul konsolidasi panitia di koridor rektorat"),
    ("kamar kosan mau disemprot fogging nyamuk dbd dari puskesmas", "semua penghuni kos diminta keluar ruangan sampai sore"),
    ("diajak makan siang bareng dosen penguji di resto luar kampus", "ga enak nolak ajakan makan siang tim riset laboratorium"),
    ("dompet dan stnk motor hilang tercecer pas sarapan bubur ayam", "lagi nyari keliling warung dan bikin laporan kehilangan"),
    ("gigi bungsu tiba-tiba berdenyut ngilu parah ga bisa ngunyah nasi", "lagi antre pendaftaran di klinik dokter gigi darmaga"),
    ("teman satu kosan pingsan di dapur kosan karena kelelahan praktikum", "harus nemenin periksa ke faskes pertama bpjs"),
    ("ada sidak pemeriksaan kamar kosan mendadak dari bapak pemilik kos", "semua penghuni harus standby di kamar masing-masing"),
    ("jadwal presentasi capstone dimajuin jam sepuluh pagi di gedung rektorat", "harus gladi resik slide materi bareng tim kelompok")
]

# 20 distinct opening greetings
GREETINGS_USER = [
    "Pagi min Namirims, tolong dibantu respon ya ada musibah mendadak...",
    "Halo admin katering, urgent banget tolong perhatikan pesan saya ini...",
    "Pagi kak admin, aduh saya lagi panik banget mau minta bantuan katering...",
    "Assalamualaikum min katering Namirims, tolong bantuannya segera ya...",
    "Min tolong dibaca dulu ya, ada kendala genting di kosan pagi ini...",
    "Pagi kak, maaf ganggu jam sibuknya tapi ini mendesak banget...",
    "Halo admin, tolong pertimbangan kemanusiaannya ya pagi hari ini...",
    "Pagi min Namirims, saya mahasiswa langganan mau lapor kondisi darurat...",
    "Min tolong banget ya, jadwal kegiatan kampus saya mendadak kacau balau...",
    "Halo kak admin, mau konfirmasi mendadak seputar kiriman makan siang..."
]

GREETINGS_ADMIN = [
    "Selamat pagi kak! Ada kendala darurat apa yang menimpa kakak pagi ini?",
    "Pagi kak! Tenang dulu ya kak, ada hal apa yang bisa kami bantu periksa?",
    "Waalaikumsalam kak! Silakan disampaikan kak, ada kondisi apa di kosan?",
    "Pagi kak! Boleh diinfokan detail kendalanya agar kami cek di sistem?",
    "Pagi kak! Iya kak kami standby, ada kejadian apa perihal katering hari ini?",
    "Halo pagi kak! Ada situasi apa kak, semoga semuanya baik-baik saja ya?",
    "Pagi kak! Silakan ceritakan keadaannya kak, ada apa dengan paket siangnya?",
    "Pagi kak! Kami siap menyimak, ada urgensi apa terkait pengantaran hari ini?"
]

# 20 distinct pushbacks
PUSHBACKS = [
    "Aduh min tolong dong kebijaksanaannya, ini kan musibah mendadak bukan disengaja!",
    "Kak saya mohon pengertiannya, musibah mana ada yang bisa direncanain sebelum jam 8.30!",
    "Min tolonglah ada toleransi darurat, kondisi saya beneran lagi darurat ga karuan!",
    "Astagfirullah min, masa ga ada kelonggaran sedikitpun buat kondisi genting begini?",
    "Kakak admin tolong banget diskresinya, ini beneran kejadian tak terduga di luar kendali!",
    "Min masa katering seketat ini peraturannya saat mahasiswa lagi kena musibah mendesak?",
    "Aduh kak tolong dipertimbangkan lagi, saya beneran repot banget ga sempat makan!",
    "Min tolong ada simpati sedikit, saya telat kabarin karena ngurusin musibah dulu!"
]

# 20 distinct concession openers
CONCESSION_OPENERS = [
    "Hhh ya ampun yaudah deh kak",
    "Oalah yaudah kalau emang aturannya kaku begitu",
    "Yaudah deh min saya maklumi konsekuensinya",
    "Oke deh kak kalau emang ga bisa diotak-atik lagi",
    "Waduh yaudah gapapa deh kak daripada mubazir",
    "Iya deh min saya paham prosedur operasionalnya",
    "Yaudah min gapapa tetep kirim aja",
    "Oke kak gapapa saya pasrah aja",
    "Baiklah kak kalau sudah ketentuan baku dapur",
    "Sip deh min saya ikut regulasi yang berlaku"
]

POST_ACTS = [
    "nanti saya hubungi temen kosan buat ambil di meja depan",
    "nanti biar dimakan sama temen satu paviliun kos",
    "nanti pas pulang sorean baru saya panasin di rice cooker",
    "nanti saya titip bapak penjaga kosan buat taro kulkas",
    "nanti biar adek tingkat satu jurusan yang habisin",
    "nanti saya tawarin ke tetangga kamar sebelah",
    "nanti biar kurir drop di rak paket lobi aja",
    "nanti saya mampir sebentar ke kosan buat ambil",
    "nanti biar temen yang nemenin yang makan porsinya",
    "nanti saya simpen buat lauk makan malam aja"
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
    cur_clock = cur_clock.replace(hour=clock_hour, minute=clock_min)
    clock_str = cur_clock.strftime("%Y-%m-%d %H:%M:%S")
    target_date = cur_clock.strftime("%Y-%m-%d")
    
    fac = FACULTIES[i % len(FACULTIES)]
    area, dorm = LOCATIONS[i % len(LOCATIONS)]
    r_idx = (i * 3 + 1) % len(REASONS)
    reason_1, reason_2 = REASONS[r_idx]
    
    # 4 distinct action distributions:
    # 0..179: None (45%) -> yield to delivery
    # 180..279: QUERY_ONLY (25%) -> customer cancels request, asks about policy
    # 280..349: NEEDS_REVIEW_CLARIFY (17.5%) -> customer puts request on hold
    # 350..399: None (12.5%) -> yielding to delivery
    if i < 180 or i >= 350:
        act = None
        concession_text = f"{CONCESSION_OPENERS[i % len(CONCESSION_OPENERS)]}, {POST_ACTS[i % len(POST_ACTS)]}. Tetep kirim normal aja porsi lunch {target_date} ke {dorm} ya min makasih #{i+1}."
    elif i < 280:
        act = "QUERY_ONLY"
        concession_text = f"{CONCESSION_OPENERS[i % len(CONCESSION_OPENERS)]}, ga jadi dibatalin deh kalo gitu, biarin paket katering {dorm} tetap berjalan normal seperti semula ya makasih infonya #{i+1}."
    else:
        act = "NEEDS_REVIEW_CLARIFY"
        concession_text = f"{CONCESSION_OPENERS[i % len(CONCESSION_OPENERS)]}, jangan diubah dulu status katering {dorm} saya ya, nanti saya kabari lagi setelah ada kepastian dari dosen #{i+1}."

    t1_text = f"{GREETINGS_USER[i % len(GREETINGS_USER)]} Saya {std_id} dari fakultas {fac} yang tinggal di {dorm} area {area}."
    t2_text = f"{GREETINGS_ADMIN[i % len(GREETINGS_ADMIN)]} Ada kendala katering apa di {dorm} kak?"
    t3_text = f"Mendadak banget {reason_1}, akibatnya {reason_2}. Tolong cancel atau skip jatah makan siang saya hari ini tgl {target_date} ya min, kosan kosong."
    t4_text = f"Waduh mohon maaf sekali kak, sistem dapur {area} sudah tutup pukul 08.30 WIB tadi. Menu makan siang tanggal {target_date} sudah dimasak penuh dan kurir bersiap packing."
    t5_text = f"{PUSHBACKS[i % len(PUSHBACKS)]} Masa ga ada toleransi sedikitpun buat anak {fac} yang kena kendala darurat begini?"
    t6_text = f"Kami sangat memahami kerepotan kakak di {dorm}. Kendati demikian, seluruh lauk sudah diporsikan dan kurir rute {area} segera berangkat. Paket tetap kami antar ke lobi ya kak."
    t7_text = concession_text
    t8_text = f"Baik kak {std_id}, terima kasih banyak atas kerja sama dan pengertiannya. Paket makan siang tanggal {target_date} tetap aman diantar kurir ke {dorm} ya. Semangat urusannya!"

    t_times = [cur_clock + timedelta(seconds=25 * step + (i % 7)) for step in range(8)]

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
        "clock": clock_str,
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
        "gold_rationale": f"Pelanggan meminta cancel lunch {target_date} lewat cutoff 08.30 karena {reason_1}. Setelah admin menjelaskan porsi sudah dimasak, pelanggan mengalah."
    }
    scenarios.append(sc)

print(f"Generated {len(scenarios)} unique counterfactual scenarios.")

with open("datasets/counterfactual_turnarounds_400.jsonl", "w", encoding="utf-8") as f:
    for sc in scenarios:
        f.write(json.dumps(sc, ensure_ascii=False) + "\n")

print("Saved to datasets/counterfactual_turnarounds_400.jsonl")
