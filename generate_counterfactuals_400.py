import json
import random
from datetime import datetime, timedelta

from datasets.verify_dataset import load_test_dataset, normalize_text, get_4grams, jaccard_sim

test_info = load_test_dataset("datasets/sealed")
print(f"Loaded {test_info['count']} test scenarios.")

with open("/tmp/cleaned_1740.jsonl") as f:
    existing_1740 = [json.loads(l) for l in f if l.strip()]

seen_long_bubbles = set()
seen_deciding = set()
for sc in existing_1740:
    for t in sc.get("turns", []):
        w = normalize_text(t.get("content", "")).split()
        if len(w) >= 6:
            seen_long_bubbles.add(" ".join(w))
    dec_idx = sc.get("deciding_turn_index")
    if dec_idx is not None and 0 <= dec_idx < len(sc.get("turns", [])):
        seen_deciding.add(normalize_text(sc["turns"][dec_idx].get("content", "")))

for b in test_info["long_bubbles"]:
    seen_long_bubbles.add(b)
for d in test_info["deciding"]:
    seen_deciding.add(d)

print(f"Tracking {len(seen_long_bubbles)} long bubbles and {len(seen_deciding)} deciding bubbles.")

FACULTIES = ["Faperta", "Fapet", "Fahutan", "Fateta", "Fem", "Fema", "Fmipa", "FPIK", "FKH", "Vokasi", "Ilkom", "Biologi", "Kimia", "Agronomi", "Silvikultur"]
AREAS = ["Bara", "Bateng", "Balio", "Leuwikopo", "Cifor", "Babakan Raya", "Babakan Lebak", "Dramaga Cantik", "Perwira", "Cangkrang"]
DORMS = ["Wisma Amarilis", "Griya Dahlia", "Pondok Damai", "Kost Asri", "Wisma Mawar", "Kost Kenanga", "Griya Melati", "Pondok Bougenville", "Kost Flamboyan", "Wisma Cempaka", "Kost Anggrek", "Griya Kencana", "Pondok Pelangi", "Kost Barokah", "Wisma Sakura"]

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
    ("diajak makan siang bareng dosen penguji di resto luar kampus", "ga enak nolak ajakan makan siang tim riset laboratorium")
]

CONCESSION_TEMPLATES = [
    # 0: None action, yield to delivery
    ("Hhh ya ampun yaudah deh kak gapapa, {post}. Tetep kirim normal aja makanannya ya.", None),
    ("Oalah gitu ya aturannya, yaudah kak gapapa biar kurir tetep kirim seperti biasa, {post}.", None),
    ("Yaudah deh kak saya paham konsekuensi operasionalnya, {post}. Makasih infonya ya min.", None),
    ("Oke min gapapa saya maklumi, kirim aja porsinya ke kosan seperti biasa ya nanti {post}.", None),
    ("Waduh sayang juga ya, tapi gapapa deh tetep kirim aja porsi saya hari ini min, {post}.", None),
    ("Iya deh kak betul juga daripada pusing, tetep drop makanannya di meja depan ya, {post}.", None),
    ("Yaudah min gapapa kirim aja sesuai jadwal normal, {post}. Nuhun infonya.", None),
    ("Oke kak kalo emang udah mateng yaudah kirim aja, {post}. Makasih banyak infonya.", None),
    ("Baiklah kak gapapa tetep antar aja ke alamat biasa, {post}. Terima kasih pengertiannya.", None),
    ("Sip min ga masalah tetep kirim aja porsi hari ini, {post}. Makasih ya min.", None),
    
    # 1: QUERY_ONLY action, cancel request
    ("Oalah gabisa ya kak, yaudah kalau gitu ga usah di-skip, biarin jadwal katering berjalan normal ya makasih.", "QUERY_ONLY"),
    ("Oh oke min paham regulasinya, gajadi batalin deh kalau gitu, jadwal minggu ini tetep kirim seperti semula ya.", "QUERY_ONLY"),
    ("Oke kak makasih banyak penjelasannya seputar aturan cutoff, untuk sekarang jadwal makan saya biarin aktif normal aja.", "QUERY_ONLY"),
    ("Siap min saya mengerti SOP kateringnya, untuk pesanan saya tetep lanjut kirim biasa aja ya makasih.", "QUERY_ONLY"),
    ("Paham kak penjelasannya, gausah diubah apa-apa deh kalo gitu, biarin paket berjalan normal seperti biasa ya.", "QUERY_ONLY"),
    ("Oke min kalo sistemnya begitu saya ikut aja, ga jadi minta skip ya tetep kirim normal aja.", "QUERY_ONLY"),
    ("Siap min jelas banget infonya, batalin aja permohonan jeda tadi ya tetep kirim rutin.", "QUERY_ONLY"),
    
    # 2: NEEDS_REVIEW_CLARIFY action, ambiguous hold
    ("Aduh bingung juga ya kak, yaudah liat ntar siangan aja deh kepastiannya, jangan diubah dulu status katering saya.", "NEEDS_REVIEW_CLARIFY"),
    ("Duh serba salah, nanti saya rundingin dulu sama temen sekamar kak, sementara jangan diapa-apain dulu jadwalnya.", "NEEDS_REVIEW_CLARIFY"),
    ("Oke kak nanti saya kabari lagi kepastian jadwal kuliahnya, untuk sekarang status langganan biarkan normal dulu ya.", "NEEDS_REVIEW_CLARIFY"),
    ("Aduh masih belum pasti juga nih acaranya, liat kondisi nanti aja deh min jangan di-skip dulu.", "NEEDS_REVIEW_CLARIFY")
]

POST_OPTIONS = [
    "nanti saya minta tolong anak kosan sebelah buat ambilin di rak depan",
    "nanti biar dimakan sama temen satu paviliun yang standby di kosan",
    "nanti pas pulang sorean baru saya panasin di microwave dapur bersama",
    "nanti saya titip pesan ke bapak penjaga kosan buat simpen di kulkas",
    "nanti biar adek tingkat satu jurusan yang ambil di meja lobi utama",
    "nanti saya kabarin anak-anak kosan lain buat makan siang bareng",
    "nanti biar kurir taruh di atas meja paket teras depan aja",
    "nanti saya ambil pas jam istirahat sebentar ke kosan",
    "nanti biar temen yang nemenin di kampus yang habisin makanannya",
    "nanti saya simpen buat lauk makan malam sekalian aja di kosan",
    "nanti biar dihabisin temen sekamar yang lagi ga kemana-mana",
    "nanti saya minta tolong ibu kosan buat naruh di meja makan",
    "nanti pas kelar urusan di kampus langsung saya ambil di lobi",
    "nanti saya oper ke tetangga kamar sebelah yang belum makan",
    "nanti biar dimakan temen sekelompok praktikum yang mampir kosan"
]

scenarios = []
base_dt = datetime(2026, 11, 2, 8, 35, 10)

random.seed(42)

for i in range(400):
    sc_id = f"CF_TURNAROUND_{i+1:03d}"
    std_id = f"STD_CF_{i+1:04d}"
    
    cur_clock = base_dt + timedelta(days=(i % 28), minutes=(i * 7) % 180)
    # Ensure current clock is AFTER morning cutoff 08:30 (e.g. 08:35 to 09:45)
    clock_hour = 8 + ((i * 3) % 2)
    clock_min = 32 + (i % 25)
    cur_clock = cur_clock.replace(hour=clock_hour, minute=clock_min)
    clock_str = cur_clock.strftime("%Y-%m-%d %H:%M:%S")
    target_date = cur_clock.strftime("%Y-%m-%d")
    
    fac = random.choice(FACULTIES)
    area = random.choice(AREAS)
    dorm = random.choice(DORMS)
    reason_1, reason_2 = random.choice(REASONS)
    post = random.choice(POST_OPTIONS)
    
    tmpl, act = CONCESSION_TEMPLATES[i % len(CONCESSION_TEMPLATES)]
    concession_text = tmpl.format(post=post)
    
    # Build dialogue turns
    # T1: User greeting & urgent context
    t1_time = cur_clock
    t1_text = f"Pagi min katering Namirims, mau minta tolong darurat nih dari anak {fac} di {dorm} daerah {area}..."
    
    # T2: Assistant greeting
    t2_time = t1_time + timedelta(seconds=random.randint(20, 45))
    t2_text = f"Pagi kak! Ada hal mendesak apa yang bisa kami bantu terkait katering di {dorm} kak?"
    
    # T3: User requests skip for today (mentioning explicit date)
    t3_time = t2_time + timedelta(seconds=random.randint(40, 80))
    t3_text = f"Mendadak banget {reason_1}, jadi {reason_2}. Tolong skip makan siang saya hari ini tgl {target_date} ya min, kamar kosan kosong ga ada orang."
    
    # T4: Assistant explains cutoff refusal
    t4_time = t3_time + timedelta(seconds=random.randint(40, 70))
    t4_text = f"Waduh mohon maaf sekali kak, batas cutoff dapur untuk makan siang (pukul 08.30) sudah lewat. Menu siang tanggal {target_date} sudah selesai dimasak dan dipacking tim dapur {area}."
    
    # T5: User initial pushback
    t5_time = t4_time + timedelta(seconds=random.randint(30, 60))
    t5_text = f"Aduh min tolong dong kebijaksanaannya, ini kan musibah mendadak bukan disengaja! Masa ga ada kelonggaran darurat sedikitpun buat pembatalan katering?"
    
    # T6: Assistant empathetic policy explanation
    t6_time = t5_time + timedelta(seconds=random.randint(35, 65))
    t6_text = f"Kami sangat memahami kerepotan kakak saat ini. Namun bumbu dan bahan baku sudah diolah penuh oleh dapur dan kurir segera meluncur ke {dorm}. Paket tetap kami antarkan ke titik drop lobi kak."
    
    # T7: User final concession (The turnaround)
    t7_time = t6_time + timedelta(seconds=random.randint(25, 55))
    t7_text = concession_text
    
    # T8: Assistant closing
    t8_time = t7_time + timedelta(seconds=random.randint(15, 30))
    t8_text = f"Baik kak, terima kasih banyak atas pengertian dan kerja samanya. Paket makan siang tanggal {target_date} tetap aman diantar ke {dorm} ya kak. Semangat lancar urusannya!"

    turns = [
        {"role": "user", "content": t1_text, "timestamp": t1_time.strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t2_text, "timestamp": t2_time.strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t3_text, "timestamp": t3_time.strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t4_text, "timestamp": t4_time.strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t5_text, "timestamp": t5_time.strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t6_text, "timestamp": t6_time.strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t7_text, "timestamp": t7_time.strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t8_text, "timestamp": t8_time.strftime("%Y-%m-%d %H:%M:%S")}
    ]
    
    deciding_idx = 6 # T7 (user concession) is index 6
    
    gold_call = {
        "action": act,
        "dates": [],
        "session": None,
        "notes": None,
        "renewal_package": None
    }
    
    sc = {
        "id": sc_id,
        "category": "counterfactual_turnaround_concession",
        "student_id": std_id,
        "clock": clock_str,
        "turns": turns,
        "deciding_turn_index": deciding_idx,
        "gold_call": gold_call,
        "secondary_calls": [],
        "gold_rationale": f"Pelanggan meminta pembatalan makan siang tanggal {target_date} setelah batas cutoff 08.30 terlewati karena {reason_1}. Setelah admin menjelaskan porsi sudah dimasak dapur, pelanggan mengalah dan meminta makanan tetap diantar normal."
    }
    scenarios.append(sc)

print(f"Generated {len(scenarios)} scenarios.")

with open("datasets/counterfactual_turnarounds_400.jsonl", "w", encoding="utf-8") as f:
    for sc in scenarios:
        f.write(json.dumps(sc, ensure_ascii=False) + "\n")

print("Saved to datasets/counterfactual_turnarounds_400.jsonl")
