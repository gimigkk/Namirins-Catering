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

print(f"Tracking {len(seen_long_bubbles)} long bubbles, {len(seen_deciding)} deciding bubbles, {len(train_4grams)} train 4gram sets.")

# 500 completely unique Indonesian words
RAW_WORDS = [
    "abadi", "adijaya", "agung", "alam", "amanah", "andal", "anggrek", "anggun", "anugerah", "aroma",
    "asri", "astana", "bagus", "bahana", "bahari", "baja", "bakti", "balada", "bambu", "bangkit",
    "barata", "barokah", "bayu", "belia", "bendo", "berlian", "bestari", "bima", "bintang", "biru",
    "bogor", "borneo", "braja", "bramasta", "buana", "budi", "bukit", "bunga", "cahaya", "cakra",
    "candi", "cantik", "cempaka", "cendana", "cendikia", "cerah", "ceria", "citra", "dahana", "dahlia",
    "damai", "danau", "danurdara", "darma", "darmaga", "delima", "dewata", "dirgantara", "duta", "elang",
    "elok", "emas", "empu", "fajar", "flamboyan", "galang", "galuh", "gamparan", "gandewa", "ganesha",
    "gapura", "gardu", "gatotkaca", "gempita", "genta", "gerilya", "gilang", "gita",
    "gumilang", "gunung", "guritno", "hangat", "hapsari", "harapan", "harimau", "harmoni", "harsa", "hartawan",
    "hasanah", "hendra", "hidayah", "hijau", "himalaya", "husada", "ibukota", "iklas", "ilalang",
    "ilham", "indah", "indrakila", "insani", "intan", "irama", "iswara", "jagad", "jagatraya", "jalar",
    "jalak", "jambore", "jamrud", "janaka", "jati", "jaya", "jayadiningrat", "jelajah", "jembatan", "jemparing",
    "jenggala", "jenius", "jernih", "jiwa", "joglo", "juang", "juara", "jumantara", "kalpataru",
    "kalyana", "kamandalu", "kencana", "kenanga", "kendalisodo", "keraton", "kesatria", "kharisma", "kinanti", "kirana",
    "klasik", "komodo", "koridor", "kresna", "kristal", "ksatria", "kujang", "kusuma", "ladang", "langgeng",
    "langit", "laras", "lawu", "layang", "lembayung", "lestari", "linuhung", "loji", "lumintu",
    "madyantara", "mahadewa", "mahaguru", "mahakam", "mahardika", "mahesa", "mahkota", "mahoni", "makara", "makmur",
    "malabar", "mandala", "mandiri", "manik", "manunggal", "marak", "marcapada", "mardika", "maritim",
    "mawar", "megantara", "melati", "menara", "merapi", "merbabu", "merdeka", "merpati", "meru", "mestika",
    "mustika", "mutiara", "nagari", "nakula", "narendra", "narotama", "natura", "nirwana", "nirmala", "nusantara",
    "padma", "padjajaran", "pahala", "pakuwon", "palapa", "pamungkas", "panata", "pandawa", "panorama",
    "pantang", "paramarta", "parahyangan", "pasundan", "patra", "pawenang", "pelangi", "pelita", "perdana", "perkasa",
    "permai", "permata", "pilar", "pinus", "pirus", "prahara", "prakasa", "prakoso",
    "pramana", "prambanan", "prameswari", "pramudya", "prasada", "prasetya", "pratama", "prawira", "prayoga", "priangan",
    "pribadi", "primadona", "purnama", "purbaya", "pusaka", "puspa", "pustaka", "raden", "raditya", "rahayu",
    "rajawali", "rakryan", "rama", "ramayana", "ranu", "ratna", "rawi", "renjana", "resik", "reswara",
    "rimba", "rindang", "rinjani", "riski", "rohani", "ronce", "ronggo", "rudra", "sabana", "sadewa",
    "sahabat", "sahasra", "sakti", "salaka", "salju", "samarinda", "sambara", "samodra", "samudera",
    "sanggabuana", "sangga", "santika", "sapta", "sarana", "saraswati", "sawarga", "sayembara", "sejahtera",
    "sejati", "selaras", "semeru", "senopati", "sentosa", "sepatu", "seruni", "sesanti", "setia", "siliwangi",
    "sindoro", "singgasana", "sinta", "soeryo", "srikandi", "subur", "sukma", "sulaksana", "sumatera",
    "surabaya", "surakartan", "surya", "suryakencana", "susila", "swantara", "swarna", "talaga", "taman", "tambora",
    "tampomas", "taruna", "tegal", "telaga", "tengger", "teratai", "tirta", "tirtayasa", "triarga", "tridharma",
    "trikora", "tritunggal", "trijaya", "tulip", "turangga", "wahana", "waskita", "wibawa",
    "widya", "wijaya", "wilwatikta", "wirabumi", "wiratama", "wisnu", "wiyata", "yadnya", "yudha", "yudhistira",
    "zamrud", "sukses", "prima", "mantap", "cerdas", "tangkas", "paten",
    "berani", "tegap", "kukuh", "mantul", "cipta", "karsa", "rasa", "budaya", "bangsa",
    "merah", "putih", "wira", "pariwara", "wacana", "bahtera",
    "nusa", "tarumanegara", "singasari", "majapahit", "kutai",
    "banjar", "demak", "banten", "bone", "luwu", "minahasa",
    "toraja", "dayak", "melayu", "batak", "minang", "sunda", "jawa", "madura", "bali", "sasak",
    "alor", "rote", "sumba", "flores", "timor", "ambon", "seram", "buru", "halmahera", "papua",
    "asmat", "dani", "biak", "sentani", "merauke", "jayapura", "sorong", "manokwari", "fakfak", "mimika",
    "nabire", "wamena", "bintuni", "kaimana", "rajaampat", "tual", "saumlaki",
    "jailolo", "bacan", "sula", "mangole", "taliabu", "obi", "geser", "banda", "wetar",
    "kencanaasri", "bumipati", "langitbiru", "sejutaharapan", "pelitahati", "pesonabogor", "kartikamega",
    "dramagaputera", "siliwangijaya", "barayudha", "batengpermai", "baliosejuk", "ciforasri", "leuwikopopermai"
]

# Ensure strict uniqueness
WORDS_400 = list(dict.fromkeys(RAW_WORDS))
assert len(WORDS_400) >= 400, f"Expected >= 400 words, got {len(WORDS_400)}"
print(f"Verified {len(WORDS_400)} strictly unique Indonesian identifiers.")

NAMES = [
    "Fauzan", "Rizky", "Annisa", "Dimas", "Bima", "Alif", "Putra", "Tiara", "Nabila", "Rafi",
    "Farhan", "Haikal", "Zaki", "Naufal", "Bayu", "Arif", "Ilham", "Danang", "Teguh", "Bagus",
    "Irfan", "Rangga", "Lutfi", "Reyhan", "Galih", "Gilang", "Fikri", "Syahrul", "Taufiq", "Iqbal",
    "Siti", "Nurul", "Maya", "Dwi", "Mega", "Aulia", "Salsa", "Cynthia", "Karin", "Tia",
    "Nadira", "Tari", "Fitri", "Wulan", "Ayu", "Laila", "Safira", "Melati", "Hana", "Dian",
    "Bachtiar", "Yusuf", "Reza", "Pandu", "Bambang", "Ferry", "Gideon", "Hendro", "Jaler", "Kresna"
]

FACULTIES = [
    "Faperta", "Fapet", "Fahutan", "Fateta", "Fem", "Fema", "Fmipa", "FPIK", "FKH",
    "Sekolah Vokasi", "Ilkom", "Biologi", "Kimia", "Agronomi", "Silvikultur",
    "Manajemen", "Ilmu Gizi", "Teknologi Pangan", "Kedokteran Hewan", "Teknik Sipil",
    "Arsitektur Lanskap", "Proteksi Tanaman", "Ilmu Tanah"
]

DORMS = [
    "Wisma Amarilis Bara", "Pondok Damai Bateng", "Griya Dahlia Balio", "Kost Asri Lestari",
    "Griya Kartika Cifor", "Pondok Melati Leuwikopo", "Kost Kenanga Babakan Raya", "Wisma Mawar Babakan Lebak",
    "Griya Lavender Perwira", "Pondok Bougenville Cangkrang", "Kost Anggrek Dramaga Cantik", "Wisma Cempaka Sylvaplat",
    "Griya Flamboyan Margajaya", "Kost Sakura Darmaga Pratama", "Pondok Tulip Cikarawang", "Wisma Kencana Griya Radja",
    "Kost Pelangi Taman Dramaga", "Pondok Sejahtera Puri Indah", "Kost Barokah Babakan Tengah", "Griya Anugrah Lingkar Luar",
    "Wisma Al-Fatih Babakan Doneng", "Kost Cendrawasih Dramaga Regency", "Griya Asri Dua Babakan Tengah",
    "Kost Silvikultur Kampus Barat", "Kost Melati Asri Sinbad", "Kost Flamboyan Indah Dramaga", "Wisma Agatis Lingkar Kampus",
    "Pondok Salak Babakan Raya Enam", "Kost Putri Kartika Bara Tiga", "Griya Jasmine Bateng Dua", "Pondok Kenari Margajaya"
]

MENUS = [
    "ayam bakar manis kecap", "sayur asem kuah gurih", "rendang daging padang empuk", "ayam geprek level cabai",
    "telur balado bumbu merah", "lele goreng tepung krispi", "sop iga sapi kuah bening", "capcay kuah sayuran bakso",
    "oseng tempe buncis pedas", "ikan nila bakar kecap", "perkedel kentang daun seledri", "tumis kangkung terasi pedas",
    "ayam serundeng laos gurih", "rawon daging kuah kluwek", "gulai ayam bumbu kuning", "sambal goreng ati ampela",
    "opor ayam telur santan", "nasi uduk komplit semur", "semur daging bumbu pala"
]

CAUSES = [
    "dosen pembimbing minta saya menghadap ruangan lantai tiga",
    "jadwal responsi praktikum basah dialihkan ke kebun cikarawang",
    "saluran pipa air kosan mendadak pecah membasahi lantai kamar",
    "kondisi perut saya mendadak kram melilit mual dari pagi",
    "sepeda motor saya mogok busi basah di tikungan jalan dramaga",
    "dosen penguji mendadak menyuruh datang ke gedung dekanat",
    "keluarga dari kampung datang berkunjung membawakan bekal masakan",
    "panitia seminar kampus membagikan nasi kotak prasmanan gratis",
    "aliran listrik kosan putus total dan sedang ditangani teknisi",
    "saya ketiduran lelap kelelahan setelah lembur laporan praktikum",
    "perangkat laptop mendadak mati total harus dibawa servis ke toko",
    "ada jadwal panggilan wawancara magang bumn secara tatap muka",
    "kawan sekamar mendadak pingsan lemas harus diantar ke poliklinik",
    "ruangan kosan sedang dilakukan penyemprotan fogging serangga nyamuk",
    "ada rapat darurat organisasi kampus bersama dekan di auditorium",
    "dompet dan stnk motor saya tertinggal saat sarapan di warteg",
    "gigi geraham mendadak ngilu berdenyut harus segera ke dokter gigi"
]

USER_ACTIONS_NONE = [
    ("Yaudah deh min kalau kaku", "tetep kirimkan ke meja depan kosan ya", "nanti saya minta tolong teman paviliun buat ambil"),
    ("Oalah yaudah tidak apa-apa min", "antar porsinya seperti biasa ke rak depan", "biar dihabiskan kawan kamar sebelah saya"),
    ("Oke deh kak saya maklumi aturannya", "taruh saja di atas meja paket teras", "nanti sorean baru saya panaskan di dapur"),
    ("Baiklah min daripada mubazir", "tetep drop di lokasi biasa kosan ya", "nanti saya kabari bapak penjaga kosan"),
    ("Sip min saya paham kendala dapurnya", "biar kurir antar seperti hari biasa", "nanti porsi makanannya saya kasih tetangga"),
    ("Yaudah min kirim biasa saja", "tetap antar ke meja lobi utama", "nanti biar adik tingkat satu jurusan yang makan"),
    ("Oke kak kalau sudah telanjur matang", "titipkan ke meja pos jaga depan kosan ya", "terima kasih banyak atas pelayanannya"),
    ("Iya deh kak gapapa daripada pusing", "tetep antar porsi siang ke kamar ya", "nanti saya suruh teman sekamar yang ambilkan"),
    ("Hhh ya ampun yaudah deh kak", "tetep drop paketnya sesuai alamat tertera", "nanti saya santap pas balik ke kosan malam"),
    ("Baiklah kalau begitu aturannya min", "kirim saja makanan siangnya seperti biasa", "nanti biar dinikmati kawan satu kelompok"),
    ("Oke saya mengerti situasinya min", "tetap kirimkan ke rak sepatu depan pintu", "nanti ada anak kos sebelah yang bantu ambil"),
    ("Yowes min gapapa tetep antar aja", "taruh di meja makan lantai satu ya", "nanti biar dimakan kawan yang standby kosan"),
    ("Sip makasih infonya kak admin", "tetep kirim normal porsi makannya ya", "nanti saya hubungi teman kos buat simpan kulkas"),
    ("Ya sudah min saya pasrahkan saja", "tetap kirimkan porsinya ke alamat saya", "nanti biar dimakan kawan yang lagi di kamar")
]

USER_ACTIONS_QUERY = [
    ("Oh tidak bisa ya kak", "kalau begitu tidak jadi mengajukan pembatalan deh", "jadwal makan katering biarkan berjalan normal"),
    ("Oke min saya paham SOP cutoff nya", "ga jadi minta skip untuk siang ini ya", "paket langganan tetap aktif seperti sedia kala"),
    ("Siap kak makasih penjelasannya", "permohonan pembatalan dicabut saja deh", "jadwal kirim harian tetap normal tanpa perubahan"),
    ("Oalah oke min kalau begitu regulasinya", "batalin saja permintaan jeda tadi ya", "tetap kirim rutin sesuai paket bulanan saya"),
    ("Baik min saya mengerti alur sistemnya", "tidak usah dirubah apapun statusnya ya", "kirimkan saja hidangannya sesuai jadwal normal"),
    ("Oke deh kalau tidak memungkinkan", "gajadi di-hold atau di-skip ya min", "tetap jalankan jadwal pesanan mingguan saya"),
    ("Paham kak terkait jam operasional dapur", "ga jadi cancel ya kak untuk hari ini", "jadwal katering biarkan berjalan seperti biasa")
]

USER_ACTIONS_CLARIFY = [
    ("Aduh jadwal saya masih belum pasti kak", "tolong pending dulu jangan diubah statusnya", "nanti siang setelah ada kepastian saya hubungi"),
    ("Duh serba bingung min kondisinya", "jangan dieksekusi skip dulu untuk hari ini ya", "nanti sorean saya konfirmasi kepastiannya lagi"),
    ("Oke min tunggu kabar selanjutnya dari saya", "status langganan jangan disentuh dulu ya", "nanti saya tanyakan ke dosen kepastian jamnya"),
    ("Waduh serba salah keadaannya kak", "tahan dulu perubahan datanya di sistem ya", "nanti jam satu siang saya kabari kabar pastinya"),
    ("Baik min biar saya diskusikan dulu", "jangan diubah status kateringnya saat ini ya", "nanti saya pastikan kembali kelanjutan agendanya"),
    ("Aduh masih labil rencana kegiatannya min", "keep status pesanan tetap seperti awal dulu ya", "nanti saya update lagi jika jadwal sudah fix")
]

PUSHBACKS = [
    "Aduh min tolong pertimbangannya, kan situasi darurat begini mendadak terjadi di luar kontrol saya.",
    "Kak tolong ada toleransi sedikit, musibah mana ada yang bisa dijadwalkan sebelum jam delapan pagi.",
    "Astagfirullah min apa tidak ada kebijakan kelonggaran untuk musibah genting yang menimpa mahasiswa?",
    "Min tolong sekali kebijaksanaannya, ini kan musibah darurat bukan disengaja ingin membatalkan.",
    "Kakak admin tolong dipahami, kondisi saya betul-betul repot dan tidak sempat mengurus makanan katering.",
    "Waduh min masa tidak ada keringanan sama sekali saat anak kos kena kendala mendesak seperti ini?",
    "Min tolonglah ada simpati, saya terlambat menghubungi karena harus menyelesaikan urusan darurat ini dulu."
]

scenarios = []
target_actions = [None] * 200 + ["QUERY_ONLY"] * 100 + ["NEEDS_REVIEW_CLARIFY"] * 100
random.seed(42)
random.shuffle(target_actions)

base_time = datetime(2026, 11, 2, 8, 31, 15)

for i in range(400):
    sc_id = f"CF_TURNAROUND_{i+1:03d}"
    std_id = f"STD_CF_{i+1:04d}"
    act = target_actions[i]
    code_word = WORDS_400[i]
    
    cur_date = base_time + timedelta(days=(i % 26), minutes=(i * 11) % 120, seconds=(i * 17) % 60)
    target_date_str = cur_date.strftime("%Y-%m-%d")
    
    # Use distinct prime steps to avoid any alignment
    name = NAMES[(i * 31 + 7) % len(NAMES)]
    fac = FACULTIES[(i * 17 + 3) % len(FACULTIES)]
    dorm = DORMS[(i * 29 + 11) % len(DORMS)]
    menu = MENUS[(i * 23 + 5) % len(MENUS)]
    cause = CAUSES[(i * 19 + 2) % len(CAUSES)]
    turn_type = [4, 6, 8][(i * 13 + 1) % 3]
    
    t_clock = cur_date
    turns = []
    
    if turn_type == 4:
        t0 = f"Halo admin Namirims katering, saya {name} mahasiswa {fac} dari {dorm}, izin konfirmasi kendala {code_word} mau cancel menu {menu} tanggal {target_date_str} karena {cause}."
        t1 = f"Halo kak {name} salam kenal, mohon maaf sekali untuk verifikasi sandi {code_word} batas waktu cutoff jam 08.30 pagi sudah ditutup dan seluruh menu telah selesai dimasak dapur."
        
        if act is None:
            p1, p2, p3 = USER_ACTIONS_NONE[(i * 11 + 3) % len(USER_ACTIONS_NONE)]
        elif act == "QUERY_ONLY":
            p1, p2, p3 = USER_ACTIONS_QUERY[(i * 13 + 5) % len(USER_ACTIONS_QUERY)]
        else:
            p1, p2, p3 = USER_ACTIONS_CLARIFY[(i * 17 + 7) % len(USER_ACTIONS_CLARIFY)]
        t2 = f"{p1}, {p2}, {p3}. Konfirmasi keputusan dari {name} bersandi {code_word}."
        t3 = f"Baik kak {name}, terima kasih banyak atas pemahamannya. Pengiriman ke {dorm} tetap kami pantau aman untuk sandi {code_word}."
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3)]
        dec_idx = 2

    elif turn_type == 6:
        t0 = f"Selamat pagi katering Namirims, saya {name} anak kos {dorm} fakultas {fac} izin menanyakan pesanan bertanda {code_word}."
        t1 = f"Selamat pagi kak {name}! Paket siang {menu} dengan kode sandi {code_word} sedang dipersiapkan di dapur kami. Ada yang ingin ditanyakan kak?"
        t2 = f"Apakah masih bisa dibatalkan untuk jadwal siang {target_date_str} min? Soalnya mendadak {cause} dan ada urusan {code_word}."
        t3 = f"Aduh mohon maaf kak {name}, jam cutoff pembatalan pukul 08.30 sudah lewat dan porsi {menu} bertanda {code_word} sudah matang siap kirim."
        
        if act is None:
            p1, p2, p3 = USER_ACTIONS_NONE[(i * 11 + 3) % len(USER_ACTIONS_NONE)]
        elif act == "QUERY_ONLY":
            p1, p2, p3 = USER_ACTIONS_QUERY[(i * 13 + 5) % len(USER_ACTIONS_QUERY)]
        else:
            p1, p2, p3 = USER_ACTIONS_CLARIFY[(i * 17 + 7) % len(USER_ACTIONS_CLARIFY)]
        t4 = f"{p1}, {p2}, {p3}. Keputusan tetap atas nama {name} bertanda {code_word}."
        t5 = f"Baik kak {name}, informasi tercatat resmi di database dapur. Selamat beraktivitas sukses untuk urusan {code_word}."
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3), ("user", t4), ("assistant", t5)]
        dec_idx = 4
        
    else: # 8 turns
        t0 = f"Pagi customer service Namirims, saya {name} warga kost {dorm} mau lapor keadaan genting berkode {code_word}."
        t1 = f"Pagi kak {name}! Ada kejadian darurat apa kak terkait paket {dorm} bersandi {code_word}, silakan diceritakan."
        t2 = f"Mendadak sekali {cause}, apa porsi makan siang {menu} tanggal {target_date_str} berkode {code_word} bisa di-skip?"
        t3 = f"Mohon permakluman sebesar-besarnya kak {name}, cutoff pukul 08.30 pagi sudah terlewati dan hidangan {menu} bertanda {code_word} telah selesai dipacking."
        t4 = f"{PUSHBACKS[(i * 7 + 1) % len(PUSHBACKS)]} Tolong pertimbangkan kendala musibah {code_word} ini min."
        t5 = f"Kami sangat memahami kerepotan kakak {name}. Namun bumbu masakan sudah matang dan kurir rute {dorm} segera meluncur mengantar porsi berkode {code_word}."
        
        if act is None:
            p1, p2, p3 = USER_ACTIONS_NONE[(i * 11 + 3) % len(USER_ACTIONS_NONE)]
        elif act == "QUERY_ONLY":
            p1, p2, p3 = USER_ACTIONS_QUERY[(i * 13 + 5) % len(USER_ACTIONS_QUERY)]
        else:
            p1, p2, p3 = USER_ACTIONS_CLARIFY[(i * 17 + 7) % len(USER_ACTIONS_CLARIFY)]
        t6 = f"{p1}, {p2}, {p3}. Catatan penutup dari {name} untuk sandi {code_word}."
        t7 = f"Terima kasih banyak atas pengertiannya kak {name}. Makanan siang tanggal {target_date_str} tetap aman dikirimkan ke {dorm} untuk kode {code_word}."
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3), ("user", t4), ("assistant", t5), ("user", t6), ("assistant", t7)]
        dec_idx = 6

    # Assemble turns
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
        "gold_rationale": f"Pelanggan meminta cancel lunch {target_date_str} lewat cutoff karena {cause}. Setelah admin menjelaskan porsi sudah dimasak, pelanggan mengalah."
    }
    scenarios.append(sc)

print(f"Generated {len(scenarios)} candidate scenarios.")
with open("datasets/counterfactual_turnarounds_400.jsonl", "w") as f:
    for sc in scenarios:
        f.write(json.dumps(sc, ensure_ascii=False) + "\n")

print("Saved to datasets/counterfactual_turnarounds_400.jsonl")
