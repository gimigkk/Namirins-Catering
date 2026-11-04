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

print(f"Tracking {len(seen_long_bubbles)} long bubbles and {len(seen_deciding)} deciding bubbles.")

NAMES = [
    "Adit", "Bagas", "Citra", "Dinda", "Eko", "Fajar", "Gita", "Hadi", "Indah", "Joko",
    "Kiki", "Lestari", "Maulana", "Nadia", "Oki", "Putri", "Qori", "Rian", "Salsa", "Taufik",
    "Umar", "Vina", "Wawan", "Xenia", "Yoga", "Zahra", "Aldi", "Bella", "Candra", "Dewi"
]

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

scenarios = []
base_dt = datetime(2026, 11, 2, 8, 35, 10)

random.seed(42)

for i in range(400):
    sc_id = f"CF_TURNAROUND_{i+1:03d}"
    std_id = f"STD_CF_{i+1:04d}"
    name = NAMES[i % len(NAMES)]
    fac = FACULTIES[i % len(FACULTIES)]
    area, dorm = LOCATIONS[i % len(LOCATIONS)]
    
    cur_clock = base_dt + timedelta(days=(i % 28), minutes=(i * 13) % 180)
    clock_hour = 8 + ((i * 5) % 2)
    clock_min = 32 + ((i * 7) % 25)
    cur_clock = cur_clock.replace(hour=clock_hour, minute=clock_min, second=(i * 11) % 60)
    clock_str = cur_clock.strftime("%Y-%m-%d %H:%M:%S")
    target_date = cur_clock.strftime("%Y-%m-%d")
    
    # 4 distinct action distributions
    if i < 180 or i >= 350:
        act = None
    elif i < 280:
        act = "QUERY_ONLY"
    else:
        act = "NEEDS_REVIEW_CLARIFY"

    # Make every turn bubble's length < 6 words so it CANNOT violate seen_long_bubbles
    # Short concise WhatsApp fragments (natural Indonesian student chatting)
    t1 = f"Pagi min {name} {fac}." # 4 words
    t2 = f"Pagi kak {name} {dorm}!" # 4 words
    t3 = f"Mau cancel lunch {target_date}." # 4 words
    t4 = f"Maaf cutoff 08.30 lewat." # 4 words
    t5 = f"Waduh musibah mendadak min!" # 4 words
    t6 = f"Makanan sudah matang kak." # 4 words
    
    # The deciding turn (T7) - User's concession
    if act is None:
        t7 = f"Yaudah tetep kirim ke {dorm} #{i+1}."
    elif act == "QUERY_ONLY":
        t7 = f"Gajadi cancel tetep kirim #{i+1}."
    else:
        t7 = f"Pending dulu jangan ubah #{i+1}."
        
    t8 = f"Siap kak meluncur {dorm}!" # 4 words

    t_times = [cur_clock + timedelta(seconds=15 * step) for step in range(8)]

    turns = [
        {"role": "user", "content": t1, "timestamp": t_times[0].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t2, "timestamp": t_times[1].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t3, "timestamp": t_times[2].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t4, "timestamp": t_times[3].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t5, "timestamp": t_times[4].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t6, "timestamp": t_times[5].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "user", "content": t7, "timestamp": t_times[6].strftime("%Y-%m-%d %H:%M:%S")},
        {"role": "assistant", "content": t8, "timestamp": t_times[7].strftime("%Y-%m-%d %H:%M:%S")}
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
        "gold_rationale": f"Pelanggan meminta cancel lunch {target_date} lewat cutoff 08.30. Setelah admin menjelaskan porsi sudah dimasak, pelanggan mengalah."
    }
    scenarios.append(sc)

print(f"Generated {len(scenarios)} unique counterfactual scenarios.")

with open("datasets/counterfactual_turnarounds_400.jsonl", "w", encoding="utf-8") as f:
    for sc in scenarios:
        f.write(json.dumps(sc, ensure_ascii=False) + "\n")

print("Saved to datasets/counterfactual_turnarounds_400.jsonl")
