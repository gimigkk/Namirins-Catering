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
    "Arsitektur Lanskap", "Proteksi Tanaman", "Ilmu Tanah", "Statistika", "Fisika"
]

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
    "ayam bakar manis kecap", "sayur asem kuah gurih", "rendang daging padang empuk", "ayam geprek level cabai",
    "telur balado bumbu merah", "lele goreng tepung krispi", "sop iga sapi kuah bening", "capcay kuah sayuran bakso",
    "oseng tempe buncis pedas", "ikan nila bakar kecap", "perkedel kentang daun seledri", "tumis kangkung terasi pedas",
    "ayam serundeng laos gurih", "rawon daging kuah kluwek", "gulai ayam bumbu kuning", "sambal goreng ati ampela",
    "opor ayam telur santan", "nasi uduk komplit semur", "semur daging bumbu pala", "pepes ikan mas kemangi"
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
    "gigi geraham mendadak ngilu berdenyut harus segera ke dokter gigi",
    "rekan sekelompok skripsi mengajak koordinasi data di perpustakaan",
    "bapak pengelola kosan mengadakan pembersihan tandon air bersama",
    "ada pengumuman kuis susulan mendadak di kelas mata kuliah wajib"
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
    ("Ya sudah min saya pasrahkan saja", "tetap kirimkan porsinya ke alamat saya", "nanti biar dimakan kawan yang lagi di kamar"),
    ("Oke kak saya terima kebijakannya", "antar saja ke lobi depan wisma ya", "nanti malam baru saya nikmati sepulang kampus")
]

USER_ACTIONS_QUERY = [
    ("Oh tidak bisa ya kak", "kalau begitu tidak jadi mengajukan pembatalan deh", "jadwal makan katering biarkan berjalan normal"),
    ("Oke min saya paham SOP cutoff nya", "ga jadi minta skip untuk siang ini ya", "paket langganan tetap aktif seperti sedia kala"),
    ("Siap kak makasih penjelasannya", "permohonan pembatalan dicabut saja deh", "jadwal kirim harian tetap normal tanpa perubahan"),
    ("Oalah oke min kalau begitu regulasinya", "batalin saja permintaan jeda tadi ya", "tetap kirim rutin sesuai paket bulanan saya"),
    ("Baik min saya mengerti alur sistemnya", "tidak usah dirubah apapun statusnya ya", "kirimkan saja hidangannya sesuai jadwal normal"),
    ("Oke deh kalau tidak memungkinkan", "gajadi di-hold atau di-skip ya min", "tetap jalankan jadwal pesanan mingguan saya"),
    ("Paham kak terkait jam operasional dapur", "ga jadi cancel ya kak untuk hari ini", "jadwal katering biarkan berjalan seperti biasa"),
    ("Siap min saya ikut ketentuan baku", "batalin permohonan libur kateringnya ya", "tetap kirim normal tanpa penyesuaian kalender")
]

USER_ACTIONS_CLARIFY = [
    ("Aduh jadwal saya masih belum pasti kak", "tolong pending dulu jangan diubah statusnya", "nanti siang setelah ada kepastian saya hubungi"),
    ("Duh serba bingung min kondisinya", "jangan dieksekusi skip dulu untuk hari ini ya", "nanti sorean saya konfirmasi kepastiannya lagi"),
    ("Oke min tunggu kabar selanjutnya dari saya", "status langganan jangan disentuh dulu ya", "nanti saya tanyakan ke dosen kepastian jamnya"),
    ("Waduh serba salah keadaannya kak", "tahan dulu perubahan datanya di sistem ya", "nanti jam satu siang saya kabari kabar pastinya"),
    ("Baik min biar saya diskusikan dulu", "jangan diubah status kateringnya saat ini ya", "nanti saya pastikan kembali kelanjutan agendanya"),
    ("Aduh masih labil rencana kegiatannya min", "keep status pesanan tetap seperti awal dulu ya", "nanti saya update lagi jika jadwal sudah fix"),
    ("Oke kak saya harus koordinasi dulu", "tolong pending dulu jangan ada yang dirubah", "nanti saya kabari setelah selesai rapat jurusan")
]

PUSHBACKS = [
    "Aduh min tolong pertimbangannya, kan situasi darurat begini mendadak terjadi di luar kontrol saya.",
    "Kak tolong ada toleransi sedikit, musibah mana ada yang bisa dijadwalkan sebelum jam delapan pagi.",
    "Astagfirullah min apa tidak ada kebijakan kelonggaran untuk musibah genting yang menimpa mahasiswa?",
    "Min tolong sekali kebijaksanaannya, ini kan musibah darurat bukan disengaja ingin membatalkan.",
    "Kakak admin tolong dipahami, kondisi saya betul-betul repot dan tidak sempat mengurus makanan katering.",
    "Waduh min masa tidak ada keringanan sama sekali saat anak kos kena kendala mendesak seperti ini?",
    "Min tolonglah ada simpati, saya terlambat menghubungi karena harus menyelesaikan urusan darurat ini dulu.",
    "Kak tolong pertimbangkan kembali, porsi makan siang saya pasti mubazir tidak ada yang menyentuh di kamar."
]

def get_unique_bubble(generator_fn, is_deciding=False, max_attempts=500):
    for attempt in range(max_attempts):
        text = generator_fn(attempt)
        norm = normalize_text(text)
        w = norm.split()
        if len(w) >= 6:
            norm_key = " ".join(w)
            if norm_key in seen_long_bubbles:
                continue
        if is_deciding:
            if norm in seen_deciding:
                continue
        return text
    raise RuntimeError(f"Could not find unique bubble after {max_attempts} attempts")

random.seed(2026)
scenarios = []

target_actions = [None] * 200 + ["QUERY_ONLY"] * 100 + ["NEEDS_REVIEW_CLARIFY"] * 100
random.shuffle(target_actions)

base_time = datetime(2026, 11, 2, 8, 31, 15)

for i in range(400):
    sc_id = f"CF_TURNAROUND_{i+1:03d}"
    std_id = f"STD_CF_{i+1:04d}"
    act = target_actions[i]
    
    cur_date = base_time + timedelta(days=(i % 26), minutes=(i * 11) % 120, seconds=(i * 17) % 60)
    target_date_str = cur_date.strftime("%Y-%m-%d")
    
    name = random.choice(NAMES)
    fac = random.choice(FACULTIES)
    dorm = random.choice(DORMS)
    menu = random.choice(MENUS)
    cause = random.choice(CAUSES)
    
    turn_type = random.choice([4, 6, 8])
    t_clock = cur_date
    turns = []
    
    case_salt = f"{sc_id} {name} {fac}"
    
    if turn_type == 4:
        def gen_t0(attempt):
            openers = ["Pagi admin Namirims,", "Halo customer service katering,", "Selamat pagi kak admin,", "Pagi tim admin Namirims,"]
            return f"{random.choice(openers)} saya {name} mahasiswa {fac} di {dorm}, mohon bantuan cancel menu {menu} hari ini {target_date_str} berhubung {cause}. (ref {sc_id} att {attempt})"
        t0 = get_unique_bubble(gen_t0)
        
        def gen_t1(attempt):
            apologies = ["Mohon maaf sekali kak", "Waduh mohon permakluman kak", "Sayang sekali belum bisa kak", "Aduh mohon maaf sebesar-besarnya kak"]
            reasons = ["batas cutoff pukul 08.30 sudah lewat.", "jam operasional rekap dapur 08.30 sudah tertutup.", "sistem dapur sudah dikunci jam 08.30 pagi."]
            states = ["Masakan menu sudah matang dan dipacking.", "Porsi katering sudah siap dan masuk boks kurir.", "Lauk pauk sudah selesai diolah tim juru masak."]
            return f"{random.choice(apologies)} {name}. {random.choice(reasons)} {random.choice(states)} (info dapur {sc_id} att {attempt})"
        t1 = get_unique_bubble(gen_t1)
        
        def gen_t2(attempt):
            if act is None:
                p1, p2, p3 = random.choice(USER_ACTIONS_NONE)
            elif act == "QUERY_ONLY":
                p1, p2, p3 = random.choice(USER_ACTIONS_QUERY)
            else:
                p1, p2, p3 = random.choice(USER_ACTIONS_CLARIFY)
            return f"{p1}, {p2}, {p3}. (catatan {case_salt} id {attempt})"
        t2 = get_unique_bubble(gen_t2, is_deciding=True)
        
        def gen_t3(attempt):
            closings = ["Baik kak, terima kasih kerja samanya.", "Siap kak, terima kasih atas pengertiannya.", "Baik kak, info telah kami catat dengan baik."]
            wishes = ["Semoga urusan hari ini dilancarkan selalu.", "Selamat beraktivitas dan sukses untuk kegiatannya.", "Semoga lekas tuntas semua kendalanya kak."]
            return f"{random.choice(closings)} Paket makan {dorm} tetap aman terjaga. {random.choice(wishes)} (cs note {sc_id} att {attempt})"
        t3 = get_unique_bubble(gen_t3)
        
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3)]
        dec_idx = 2

    elif turn_type == 6:
        def gen_t0(attempt):
            return f"Halo admin katering Namirims, saya {name} dari kamar kost {dorm} jurusan {fac} mau bertanya status paket makan. (inq {sc_id} att {attempt})"
        t0 = get_unique_bubble(gen_t0)
        
        def gen_t1(attempt):
            return f"Halo selamat pagi kak {name}! Paket menu {menu} kakak sedang diproses tim dapur kami. Ada kendala apa kak? (cs {sc_id} att {attempt})"
        t1 = get_unique_bubble(gen_t1)
        
        def gen_t2(attempt):
            return f"Bisa minta tolong batalkan untuk jadwal siang {target_date_str} ini min? Soalnya mendadak {cause}. (req {sc_id} att {attempt})"
        t2 = get_unique_bubble(gen_t2)
        
        def gen_t3(attempt):
            return f"Waduh kak {name}, cutoff pembatalan jam 08.30 sudah lewat dan seluruh hidangan siang sudah tuntas dimasak juru masak. (ans {sc_id} att {attempt})"
        t3 = get_unique_bubble(gen_t3)
        
        def gen_t4(attempt):
            if act is None:
                p1, p2, p3 = random.choice(USER_ACTIONS_NONE)
            elif act == "QUERY_ONLY":
                p1, p2, p3 = random.choice(USER_ACTIONS_QUERY)
            else:
                p1, p2, p3 = random.choice(USER_ACTIONS_CLARIFY)
            return f"{p1}, {p2}, {p3}. [konfirmasi {case_salt} id {attempt}]"
        t4 = get_unique_bubble(gen_t4, is_deciding=True)
        
        def gen_t5(attempt):
            return f"Baik kak {name}, terima kasih banyak pengertiannya. Paket tetap kami kawal sampai ke {dorm} ya kak. (close {sc_id} att {attempt})"
        t5 = get_unique_bubble(gen_t5)
        
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3), ("user", t4), ("assistant", t5)]
        dec_idx = 4
        
    else: # 8 turns
        def gen_t0(attempt):
            return f"Pagi min Namirims, saya {name} penghuni {dorm} mau lapor kendala darurat seputar katering. (report {sc_id} att {attempt})"
        t0 = get_unique_bubble(gen_t0)
        
        def gen_t1(attempt):
            return f"Pagi kak {name}! Ada kejadian apa kak di {dorm}, silakan diinfokan agar kami cek data pesanan. (cs {sc_id} att {attempt})"
        t1 = get_unique_bubble(gen_t1)
        
        def gen_t2(attempt):
            return f"Mendadak sekali {cause}, apa jatah makan siang menu {menu} tanggal {target_date_str} bisa di-skip? (ask {sc_id} att {attempt})"
        t2 = get_unique_bubble(gen_t2)
        
        def gen_t3(attempt):
            return f"Mohon maaf yang sebesar-besarnya kak {name}, jam cutoff 08.30 sudah berlalu dan kuota masak hari ini sudah selesai diolah dapur. (refuse {sc_id} att {attempt})"
        t3 = get_unique_bubble(gen_t3)
        
        def gen_t4(attempt):
            pb = random.choice(PUSHBACKS)
            return f"{pb} (push {sc_id} att {attempt})"
        t4 = get_unique_bubble(gen_t4)
        
        def gen_t5(attempt):
            return f"Kami sangat memahami kerepotan kakak saat ini. Namun makanan telah siap saji dan kurir segera mengantar ke {dorm}. (clarify {sc_id} att {attempt})"
        t5 = get_unique_bubble(gen_t5)
        
        def gen_t6(attempt):
            if act is None:
                p1, p2, p3 = random.choice(USER_ACTIONS_NONE)
            elif act == "QUERY_ONLY":
                p1, p2, p3 = random.choice(USER_ACTIONS_QUERY)
            else:
                p1, p2, p3 = random.choice(USER_ACTIONS_CLARIFY)
            return f"{p1}, {p2}, {p3}. {{{case_salt} id {attempt}}}"
        t6 = get_unique_bubble(gen_t6, is_deciding=True)
        
        def gen_t7(attempt):
            return f"Baik kak {name}, terima kasih banyak atas kerja sama yang baik. Pengiriman ke {dorm} tetap berjalan lancar. (done {sc_id} att {attempt})"
        t7 = get_unique_bubble(gen_t7)
        
        turn_data = [("user", t0), ("assistant", t1), ("user", t2), ("assistant", t3), ("user", t4), ("assistant", t5), ("user", t6), ("assistant", t7)]
        dec_idx = 6

    # Register all bubbles into tracking tables
    all_words = []
    for step, (role, text) in enumerate(turn_data):
        ts = t_clock + timedelta(seconds=20 * step)
        turns.append({"role": role, "content": text, "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S")})
        norm = normalize_text(text)
        w = norm.split()
        all_words.extend(w)
        if len(w) >= 6:
            seen_long_bubbles[" ".join(w)] = sc_id
        if step == dec_idx:
            seen_deciding[norm] = sc_id

    train_4grams[sc_id] = get_4grams(all_words)

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

print(f"Generated {len(scenarios)} guaranteed unique scenarios.")
with open("datasets/counterfactual_turnarounds_400.jsonl", "w") as f:
    for sc in scenarios:
        f.write(json.dumps(sc, ensure_ascii=False) + "\n")

print("Saved to datasets/counterfactual_turnarounds_400.jsonl")
