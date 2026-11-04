import json, random, re
from datetime import datetime, timedelta
from datasets.verify_dataset import load_test_dataset, normalize_text, get_4grams, jaccard_sim

test_info = load_test_dataset("datasets/sealed")
print(f"Loaded {test_info['count']} test scenarios.")

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

print(f"Tracking {len(seen_long_bubbles)} long bubbles, {len(seen_deciding)} deciding bubbles, and {len(train_4grams)} train 4gram sets.")
