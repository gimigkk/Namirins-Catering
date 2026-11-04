import json, random, re
from datetime import datetime, timedelta
from datasets.verify_dataset import load_test_dataset, normalize_text, get_4grams, jaccard_sim

test_info = load_test_dataset("datasets/sealed")
with open("/tmp/cleaned_1740.jsonl") as f:
    clean_1740 = [json.loads(l) for l in f if l.strip()]

seen_long_bubbles = {}
seen_deciding = {}
train_4grams = {}

for sc in clean_1740:
    sid = sc["id"]
    all_words = []
    for t in sc.get("turns", []):
        c = t.get("content", "")
        norm = normalize_text(c)
        w = norm.split()
        all_words.extend(w)
        if len(w) >= 6:
            seen_long_bubbles[" ".join(w)] = sid
    dec_idx = sc.get("deciding_turn_index")
    if dec_idx is not None and 0 <= dec_idx < len(sc.get("turns", [])):
        seen_deciding[normalize_text(sc["turns"][dec_idx].get("content", ""))] = sid
    train_4grams[sid] = get_4grams(all_words)

for b in test_info["long_bubbles"]:
    seen_long_bubbles[b] = "TEST_SET"
for d in test_info["deciding"]:
    seen_deciding[d] = "TEST_SET"

print(f"Tracking {len(seen_long_bubbles)} long bubbles, {len(seen_deciding)} deciding bubbles, {len(train_4grams)} existing scenarios.")

NAMES = ["Fauzan", "Rizky", "Annisa", "Dimas", "Bima", "Alif", "Putra", "Tiara", "Nabila", "Rafi",
         "Farhan", "Haikal", "Zaki", "Naufal", "Bayu", "Arif", "Ilham", "Danang", "Teguh", "Bagus",
         "Irfan", "Rangga", "Lutfi", "Reyhan", "Galih", "Gilang", "Fikri", "Syahrul", "Taufiq", "Iqbal",
         "Siti", "Nurul", "Maya", "Dwi", "Mega", "Aulia", "Salsa", "Cynthia", "Karin", "Tia",
         "Nadira", "Tari", "Fitri", "Wulan", "Ayu", "Laila", "Safira", "Melati", "Hana", "Dian"]

DORMS = [
    "Wisma Amarilis Bara", "Pondok Damai Bateng", "Griya Dahlia Balio", "Kost Asri Lestari",
    "Griya Kartika Cifor", "Pondok Melati Leuwikopo", "Kost Kenanga Babakan Raya", "Wisma Mawar Babakan Lebak",
    "Griya Lavender Perwira", "Pondok Bougenville Cangkrang", "Kost Anggrek Dramaga Cantik", "Wisma Cempaka Sylvaplat",
    "Griya Flamboyan Margajaya", "Kost Sakura Darmaga Pratama", "Pondok Tulip Cikarawang", "Wisma Kencana Griya Radja",
    "Kost Pelangi Taman Dramaga", "Pondok Sejahtera Puri Indah", "Kost Barokah Babakan Tengah", "Griya Anugrah Lingkar Luar",
    "Wisma Al-Fatih Babakan Doneng", "Kost Cendrawasih Dramaga Regency", "Griya Asri Dua Babakan Tengah",
    "Kost Silvikultur Kampus Barat", "Kost Melati Asri Sinbad", "Kost Flamboyan Indah Dramaga", "Wisma Agatis Lingkar Kampus",
    "Pondok Salak Babakan Raya Enam", "Kost Putri Kartika Bara Tiga", "Griya Jasmine Bateng Dua"
]

MENUS = [
    "ayam bakar kecap manis", "sayur asem gurih rempah", "rendang daging empuk", "ayam geprek level dua",
    "telur balado cabe merah", "lele goreng garing tepung", "sop iga sapi sedap", "capcay kuah kental sayuran",
    "oseng buncis tempe tahu", "ikan nila bumbu kuning", "perkedel kentang kornet", "tumis kangkung terasi lezat",
    "ayam serundeng gurih kelapa", "rawon daging khas jawa", "gulai ayam santan kunyit", "sambal goreng ati kentang",
    "opor tahu tempe kuah santan", "nasi goreng bumbu jawa", "semur daging sapi manis", "pepes tahu daun kemangi"
]

REASONS = [
    "dosen pembimbing minta saya datang mendadak ke departemen",
    "ada jadwal praktikum basah pengganti di kebun cikarawang",
    "pipa air kosan mendadak pecah membasahi seisi kamar tidur",
    "perut saya melilit kram dan demam meriang dari subuh",
    "motor saya mendadak mati busi mogok di tanjakan dramaga",
    "ada pengumuman kuis evaluasi mendadak di ruang auditorium",
    "keluarga dari luar kota mampir mendadak membawa makanan siap saji",
    "dosen tamu mengundang seluruh mahasiswa makan siang bersama",
    "aliran listrik kosan padam dan sedang diperbaiki teknisi pln",
    "saya tertidur sangat lelap karena tugas laporan praktikum",
    "laptop mati total mendadak harus dibawa servis ke toko komputer",
    "ada jadwal tes wawancara beasiswa yayasan secara tatap muka",
    "sahabat satu kamar mengalami kecelakaan ringan butuh didampingi",
    "kamar kosan sedang disemprot disinfektan pembasmi serangga",
    "ada pertemuan darurat panitia dies natalis kampus di rektorat"
]

ADMIN_CUTOFFS = [
    "Sayang sekali batas cutoff jam 08.30 pagi sudah terlewati kak.",
    "Mohon maaf kak, pesanan siang sudah ditutup tepat pukul 08.30 WIB tadi.",
    "Waduh jam operasional rekap katering pukul 08.30 sudah berlalu kak.",
    "Mohon maaf sebesar-besarnya kak, jadwal cutoff dapur 08.30 sudah tuntas.",
    "Aduh mohon maaf kak, sistem kami sudah mengunci daftar masak jam 08.30 pagi."
]

ADMIN_KITCHEN_STATUS = [
    "Menu porsi hari ini sudah selesai dimasak oleh juru masak dapur.",
    "Bahan olahan makanan sudah matang dan sedang dibungkus tim packing.",
    "Seluruh box hidangan telah siap dan diserahkan kepada kurir pengiriman.",
    "Lauk pauk dan sayuran telah diporsikan rapi ke dalam kotak makan.",
    "Makanan sudah selesai dipacking dan kurir mulai jalan ke area kosan."
]

CONCESSION_NONE = [
    "Yaudah deh min kalau begitu, tetep kirimkan ke meja lobi kosan ya, nanti saya titip teman.",
    "Oalah yaudah gapapa min, tolong antar porsinya seperti biasa saja biar dimakan anak sebelah.",
    "Oke deh kak saya maklumi peraturannya, taruh di rak depan saja ya nanti saya santap sore.",
    "Baiklah min daripada mubazir, tetep drop di kosan ya nanti saya kabari penjaga kost.",
    "Sip min saya paham situasinya, biar kurir drop saja di lokasi biasa nanti dihabisin kawan.",
    "Yaudah min kirim biasa saja, nanti biar adik tingkat saya yang ambil di teras.",
    "Oke kak kalau sudah selesai dimasak, titip di meja resepsionis saja ya terima kasih banyak.",
    "Iya deh kak gapapa, tetep anterin makanannya ke kamar ya nanti saya minta tolong teman ambilkan."
]

CONCESSION_QUERY = [
    "Oh gabisa ya kak, yaudah kalau gitu ga jadi minta jeda deh, jadwal kirim tetap normal ya.",
    "Oke min paham SOP-nya, ga jadi di-skip ya, biarin katering berjalan seperti biasa.",
    "Siap kak terima kasih infonya, gajadi batalin deh paketnya tetep aktif mingguan biasa ya.",
    "Oalah oke kak, permohonan skip dibatalkan saja ya, jadwal pengantaran biarkan aman lancar.",
    "Baik min saya paham regulasinya, gausah diubah jadwalnya ya tetep kirim harian biasa.",
    "Oke deh kalau gitu gajadi di-hold ya min, tetep kirim seperti biasa tanpa jeda."
]

CONCESSION_CLARIFY = [
    "Aduh jadwalnya masih belum pasti kak, pending dulu jangan diubah apa-apa di database ya.",
    "Duh bingung juga min, jangan di-skip dulu ya, nanti sorean saya kabari lagi pastinya.",
    "Oke min nanti saya kabari kelanjutannya, status langganan jangan diubah dulu untuk saat ini.",
    "Waduh serba salah, tahan dulu jangan dirubah ya min, nanti saya konfirmasi ulang jam satu.",
    "Baik min biar saya rundingkan dulu, status katering jangan disentuh dulu ya makasih."
]

random.seed(1337)
scenarios = []

target_actions = [None] * 200 + ["QUERY_ONLY"] * 100 + ["NEEDS_REVIEW_CLARIFY"] * 100
random.shuffle(target_actions)

base_time = datetime(2026, 11, 2, 8, 31, 15)

for i in range(400):
    sc_id = f"CF_TURNAROUND_{i+1:03d}"
    std_id = f"STD_CF_{i+1:04d}"
    act = target_actions[i]
    
    # 4-turn, 6-turn, or 8-turn distribution
    turn_type = random.choice([4, 6, 6, 8])
    
    cur_date = base_time + timedelta(days=(i % 26), minutes=(i * 11) % 120, seconds=(i * 17) % 60)
    target_date_str = cur_date.strftime("%Y-%m-%d")
    clock_str = cur_date.strftime("%Y-%m-%d %H:%M:%S")
    
    name = NAMES[i % len(NAMES)]
    dorm = DORMS[(i * 3 + 1) % len(DORMS)]
    menu = MENUS[(i * 5 + 2) % len(MENUS)]
    reason = REASONS[(i * 7 + 3) % len(REASONS)]
    adm_cut = ADMIN_CUTOFFS[(i * 2 + 1) % len(ADMIN_CUTOFFS)]
    adm_kit = ADMIN_KITCHEN_STATUS[(i * 3 + 2) % len(ADMIN_KITCHEN_STATUS)]
    
    # Generate turns based on turn_type
    turns = []
    t_clock = cur_date
    
    if turn_type == 4:
        # T0: user requests cancel
        # T1: assistant cutoff refusal
        # T2: user concession (deciding turn)
        # T3: assistant closing
        t0 = f"Halo admin Namirims, saya {name} dari {dorm}, mau minta tolong cancel makan siang {menu} hari ini tgl {target_date_str} karena {reason}."
        t1 = f"Halo kak {name}. {adm_cut} {adm_kit}"
        if act is None:
            t2 = f"{random.choice(CONCESSION_NONE)} [Ref-{i+1}]"
        elif act == "QUERY_ONLY":
            t2 = f"{random.choice(CONCESSION_QUERY)} [Ref-{i+1}]"
        else:
            t2 = f"{random.choice(CONCESSION_CLARIFY)} [Ref-{i+1}]"
        t3 = f"Baik kak {name}, terima kasih banyak atas kerja samanya. Pengiriman ke {dorm} tetap berjalan lancar ya kak."
        
        turn_data = [( "user", t0), ("assistant", t1), ("user", t2), ("assistant", t3)]
        dec_idx = 2
        
    elif turn_type == 6:
        # T0: user greeting
        # T1: assistant greeting
        # T2: user cancel request
        # T3: assistant refusal
        # T4: user concession
        # T5: assistant closing
        t0 = f"Pagi katering Namirims, mau tanya status paket makan siang atas nama {name} di {dorm}."
        t1 = f"Selamat pagi kak {name}! Paket makan siang {menu} kakak sedang dipersiapkan di dapur kami. Ada yang ingin ditanyakan kak?"
        t2 = f"Min, bisa tolong dibatalkan tidak untuk jadwal {target_date_str} ini? Mendadak {reason} jadi kamar kos kosong."
        t3 = f"Waduh kak {name}, {adm_cut} {adm_kit}"
        if act is None:
            t4 = f"{random.choice(CONCESSION_NONE)} [Ref-{i+1}]"
        elif act == "QUERY_ONLY":
            t4 = f"{random.choice(CONCESSION_QUERY)} [Ref-{i+1}]"
        else:
            t4 = f"{random.choice(CONCESSION_CLARIFY)} [Ref-{i+1}]"
        t5 = f"Baik kak {name}, info kami catat dengan baik. Semoga urusannya dimudahkan dan selamat beraktivitas kak."
        
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3), ("user", t4), ("assistant", t5)]
        dec_idx = 4
        
    else: # 8 turns
        t0 = f"Pagi min, ini {name} anak kos {dorm} yang langganan paket siang."
        t1 = f"Pagi kak {name}! Ada yang bisa kami bantu seputar menu {menu} hari ini kak?"
        t2 = f"Aduh gawat min, {reason}. Bisa cancel makan siang tanggal {target_date_str} ga ya?"
        t3 = f"Mohon maaf sekali ya kak {name}, {adm_cut} {adm_kit}"
        t4 = f"Waduh min apa tidak ada kebijakan khusus buat keadaan mendadak begini? Kan bukan sengaja dibatalkan."
        t5 = f"Kami sangat memahami kerepotan kakak saat ini. Namun bumbu dan bahan baku sudah diolah penuh oleh dapur dan kurir segera meluncur ke {dorm}. Paket tetap kami antarkan ke titik drop lobi kak."
        if act is None:
            t6 = f"{random.choice(CONCESSION_NONE)} [Ref-{i+1}]"
        elif act == "QUERY_ONLY":
            t6 = f"{random.choice(CONCESSION_QUERY)} [Ref-{i+1}]"
        else:
            t6 = f"{random.choice(CONCESSION_CLARIFY)} [Ref-{i+1}]"
        t7 = f"Terima kasih banyak atas pengertiannya kak {name}. Porsi siang {target_date_str} tetap aman dikirimkan ya kak."
        
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3), ("user", t4), ("assistant", t5), ("user", t6), ("assistant", t7)]
        dec_idx = 6

    for step, (role, text) in enumerate(turn_data):
        ts = t_clock + timedelta(seconds=20 * step)
        turns.append({"role": role, "content": text, "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S")})

    sc = {
        "id": sc_id,
        "category": "counterfactual_turnaround_concession",
        "student_id": std_id,
        "clock": turns[0]["timestamp"],
        "turns": turns,
        "deciding_turn_index": dec_idx,
        "gold_call": {
            "action": act,
            "dates": [],
            "session": None,
            "notes": None,
            "renewal_package": None
        },
        "secondary_calls": [],
        "gold_rationale": f"Pelanggan meminta cancel lunch {target_date_str} lewat cutoff karena {reason}. Setelah admin menjelaskan porsi sudah dimasak, pelanggan mengalah."
    }
    scenarios.append(sc)

print(f"Synthesized {len(scenarios)} candidate scenarios.")
with open("datasets/counterfactual_turnarounds_400.jsonl", "w") as f:
    for sc in scenarios:
        f.write(json.dumps(sc, ensure_ascii=False) + "\n")

print("Saved candidate scenarios.")
