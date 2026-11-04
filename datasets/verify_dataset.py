#!/usr/bin/env python3
"""
Strict verification script for training dataset (benchmark/augmented_corpus/audited/training_set_1200.jsonl)
and test dataset (benchmark/adv_testset).

ponytail: stdlib only (re, json, glob, random); upgrade to faiss / minhash if dataset exceeds 100k items.
"""

import os
import sys
import json
import re
import glob
import random
import argparse
from datetime import datetime
from collections import Counter

VALID_ACTIONS = {
    "APPLY_SKIP", "CANCEL_SKIP", "UPDATE_DIETARY", "RENEW_PACKAGE",
    "ESCALATE_OWNER", "QUERY_ONLY", "NEEDS_REVIEW_CLARIFY", None
}
ALL_ACTION_KEYS = [
    "APPLY_SKIP", "CANCEL_SKIP", "UPDATE_DIETARY", "RENEW_PACKAGE",
    "ESCALATE_OWNER", "QUERY_ONLY", "NEEDS_REVIEW_CLARIFY", None
]
VALID_SESSIONS = {"lunch", "dinner", "both", None}
VALID_PACKAGES = {
    "PAKET_HEMAT_LUNCH", "PAKET_REGULER_BOTH", "PAKET_AYAM_DINNER",
    "PAKET_BULANAN_LUNCH", "PAKET_BULANAN_BOTH", "PAKET_VEGETARIAN_LUNCH",
    "PAKET_PROTEIN_BOTH"
}
EMOJI_REGEX = re.compile(
    r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]"
)

def normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"\d+", "#", t)
    t = re.sub(r"[^\w\s#]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def get_4grams(words: list[str]) -> set[str]:
    if len(words) < 4:
        return set([" ".join(words)])
    return set(" ".join(words[i:i+4]) for i in range(len(words) - 3))

def jaccard_sim(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0

def load_test_dataset(test_path: str):
    if os.path.isfile(test_path):
        files = [test_path]
    else:
        files = sorted(glob.glob(os.path.join(test_path, "dev", "batch_*.jsonl")) +
                       glob.glob(os.path.join(test_path, "sealed", "batch_*.jsonl")) +
                       glob.glob(os.path.join(test_path, "*.jsonl")))
    if not files:
        raise FileNotFoundError(f"No test batches found in {test_path}")
    
    test_cases = {}
    test_ids = set()
    test_dialogues = set()
    test_deciding = set()
    test_long_bubbles = set()
    test_4grams = {}
    test_inv_index = {}

    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            for line_no, line in enumerate(fp, 1):
                line = line.strip()
                if not line:
                    continue
                sc = json.loads(line)
                sid = sc["id"]
                test_ids.add(sid)
                test_cases[sid] = sc

                turns = sc.get("turns", [])
                full_diag = normalize_text(" ".join(t.get("content", "") for t in turns))
                test_dialogues.add(full_diag)

                d_idx = sc.get("deciding_turn_index", 0)
                if 0 <= d_idx < len(turns):
                    test_deciding.add(normalize_text(turns[d_idx].get("content", "")))

                all_words = []
                for t in turns:
                    norm_c = normalize_text(t.get("content", ""))
                    words = norm_c.split()
                    all_words.extend(words)
                    if len(words) >= 6:
                        test_long_bubbles.add(norm_c)
                grams = get_4grams(all_words)
                test_4grams[sid] = grams
                for g in grams:
                    test_inv_index.setdefault(g, []).append(sid)

    return {
        "count": len(test_cases),
        "ids": test_ids,
        "dialogues": test_dialogues,
        "deciding": test_deciding,
        "long_bubbles": test_long_bubbles,
        "4grams": test_4grams,
        "inv_index": test_inv_index,
    }

def verify_records(
    records: list[dict],
    test_info: dict = None,
    expected_total: int = 1200,
    expected_per_class: int = 150,
    class_tolerance: int = 5,
    enforce_class_balance: bool = True,
    jaccard_threshold: float = 0.35,
    max_pairwise_samples: int = 5000,
):
    errors = []
    seen_ids = set()
    seen_long_bubbles = {}
    seen_deciding_bubbles = {}
    train_4grams = {}
    action_counts = Counter()
    multi_day_count = 0
    both_session_count = 0
    emoji_count = 0

    if expected_total is not None and len(records) != expected_total:
        errors.append(f"Total count mismatch: got {len(records)}, expected {expected_total}")

    for idx, sc in enumerate(records, 1):
        if not isinstance(sc, dict):
            errors.append(f"Record {idx}: Not a valid JSON object")
            continue
        
        sid = sc.get("id")
        if not sid or not isinstance(sid, str):
            errors.append(f"Record {idx}: Missing or invalid 'id'")
        elif sid in seen_ids:
            errors.append(f"Record {idx}: Duplicate 'id' {sid}")
        else:
            seen_ids.add(sid)
        
        cat = sc.get("category")
        if not cat or not isinstance(cat, str):
            errors.append(f"Record {idx} ({sid}): Missing or invalid 'category'")

        turns = sc.get("turns")
        if not isinstance(turns, list) or not (3 <= len(turns) <= 15):
            errors.append(f"Record {idx} ({sid}): 'turns' must be list of 3..15 items")
            turns = []

        clock = sc.get("clock")
        if turns and clock and clock != turns[0].get("timestamp"):
            errors.append(f"Record {idx} ({sid}): 'clock' ({clock}) != turns[0].timestamp ({turns[0].get('timestamp')})")

        prev_dt = None
        has_emoji = False
        all_words = []

        for t_idx, turn in enumerate(turns):
            if not isinstance(turn, dict):
                errors.append(f"Record {idx} ({sid}): Turn {t_idx} is not a dict")
                continue
            role = turn.get("role")
            if role not in ("user", "assistant"):
                errors.append(f"Record {idx} ({sid}): Turn {t_idx} invalid role '{role}'")
            content = turn.get("content")
            if not content or not isinstance(content, str):
                errors.append(f"Record {idx} ({sid}): Turn {t_idx} missing or empty 'content'")
                content = ""
            if EMOJI_REGEX.search(content):
                has_emoji = True
            ts = turn.get("timestamp")
            if not ts:
                errors.append(f"Record {idx} ({sid}): Turn {t_idx} missing 'timestamp'")
            else:
                try:
                    cur_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    if prev_dt and cur_dt < prev_dt:
                        errors.append(f"Record {idx} ({sid}): Turn {t_idx} timestamp decreases ({ts} < {prev_dt})")
                    prev_dt = cur_dt
                except Exception as e:
                    errors.append(f"Record {idx} ({sid}): Turn {t_idx} invalid timestamp format '{ts}': {e}")
            norm_content = normalize_text(content)
            words = norm_content.split()
            all_words.extend(words)
            if len(words) >= 6:
                if norm_content in seen_long_bubbles and seen_long_bubbles[norm_content] != sid:
                    prev_sid = seen_long_bubbles[norm_content]
                    errors.append(f"Record {idx} ({sid}): Duplicate 6+ word bubble with {prev_sid}: '{content}'")
                seen_long_bubbles[norm_content] = sid
                if test_info and norm_content in test_info["long_bubbles"]:
                    errors.append(f"Record {idx} ({sid}): Test leakage - 6+ word bubble matches test set: '{content}'")

        if has_emoji:
            emoji_count += 1

        dec_idx = sc.get("deciding_turn_index")
        if dec_idx is None or not isinstance(dec_idx, int) or not (0 <= dec_idx < len(turns)):
            errors.append(f"Record {idx} ({sid}): Invalid deciding_turn_index {dec_idx}")
        else:
            dec_turn = turns[dec_idx]
            if dec_turn.get("role") != "user":
                errors.append(f"Record {idx} ({sid}): Deciding turn {dec_idx} role must be 'user', got '{dec_turn.get('role')}'")
            norm_dec = normalize_text(dec_turn.get("content", ""))
            if norm_dec in seen_deciding_bubbles and seen_deciding_bubbles[norm_dec] != sid:
                prev_sid = seen_deciding_bubbles[norm_dec]
                errors.append(f"Record {idx} ({sid}): Duplicate deciding bubble with {prev_sid}: '{dec_turn.get('content')}'")
            seen_deciding_bubbles[norm_dec] = sid
            if test_info and norm_dec in test_info["deciding"]:
                errors.append(f"Record {idx} ({sid}): Test leakage - Deciding bubble matches test set: '{dec_turn.get('content')}'")

        gold = sc.get("gold_call")
        if not isinstance(gold, dict):
            errors.append(f"Record {idx} ({sid}): Missing or invalid 'gold_call'")
        else:
            action = gold.get("action")
            if action not in VALID_ACTIONS:
                errors.append(f"Record {idx} ({sid}): Invalid gold action '{action}'")
            action_counts[action] += 1
            session = gold.get("session")
            if session not in VALID_SESSIONS:
                errors.append(f"Record {idx} ({sid}): Invalid gold session '{session}'")
            if session == "both":
                both_session_count += 1
            dates = gold.get("dates")
            if not isinstance(dates, list):
                errors.append(f"Record {idx} ({sid}): 'dates' must be a list")
            else:
                for d in dates:
                    try:
                        datetime.strptime(d, "%Y-%m-%d")
                    except Exception:
                        errors.append(f"Record {idx} ({sid}): Invalid date format '{d}' (expected YYYY-MM-DD)")
                if len(dates) >= 2:
                    multi_day_count += 1
            notes = gold.get("notes")
            if action == "UPDATE_DIETARY":
                if not notes or not isinstance(notes, str) or not notes.strip():
                    errors.append(f"Record {idx} ({sid}): Action UPDATE_DIETARY requires non-empty notes")
            pkg = gold.get("renewal_package")
            if action == "RENEW_PACKAGE":
                if pkg not in VALID_PACKAGES:
                    errors.append(f"Record {idx} ({sid}): Action RENEW_PACKAGE requires valid package, got '{pkg}'")
            else:
                if pkg is not None:
                    errors.append(f"Record {idx} ({sid}): renewal_package must be null for action '{action}'")
            if action in ("NEEDS_REVIEW_CLARIFY", None):
                if dates != [] or session is not None:
                    errors.append(f"Record {idx} ({sid}): Action '{action}' must have dates [] and session null, got {dates}, {session}")

        if test_info:
            if sid in test_info["ids"]:
                errors.append(f"Record {idx} ({sid}): Test leakage - Scenario ID matches test set: {sid}")
            full_diag = normalize_text(" ".join(t.get("content", "") for t in turns))
            if full_diag in test_info["dialogues"]:
                errors.append(f"Record {idx} ({sid}): Test leakage - Verbatim full dialogue identical to test set: {sid}")

        sc_4grams = get_4grams(all_words)
        train_4grams[sid] = sc_4grams
        if test_info:
            cand_test_ids = set()
            for g in sc_4grams:
                if g in test_info["inv_index"]:
                    cand_test_ids.update(test_info["inv_index"][g])
            for tid in cand_test_ids:
                sim = jaccard_sim(sc_4grams, test_info["4grams"][tid])
                if sim > jaccard_threshold:
                    errors.append(f"Record {idx} ({sid}): Test leakage - 4-gram Jaccard {sim:.3f} > {jaccard_threshold} with test {tid}")

    all_sids = list(train_4grams.keys())
    n = len(all_sids)
    max_pairwise_sim = 0.0
    if n > 1:
        total_possible_pairs = n * (n - 1) // 2
        sample_size = min(max_pairwise_samples, total_possible_pairs)
        checked_pairs = set()
        while len(checked_pairs) < sample_size:
            i = random.randint(0, n - 1)
            j = random.randint(0, n - 1)
            if i != j:
                checked_pairs.add((min(i, j), max(i, j)))
        for i, j in checked_pairs:
            s1, s2 = all_sids[i], all_sids[j]
            sim = jaccard_sim(train_4grams[s1], train_4grams[s2])
            if sim > max_pairwise_sim:
                max_pairwise_sim = sim
            if sim > jaccard_threshold:
                errors.append(f"Anti-template violation: Train pairwise Jaccard similarity {sim:.3f} > {jaccard_threshold} between {s1} and {s2}")

    if expected_per_class is not None and enforce_class_balance:
        for act in ALL_ACTION_KEYS:
            c = action_counts[act]
            min_allowed = expected_per_class - class_tolerance
            max_allowed = expected_per_class + class_tolerance
            if not (min_allowed <= c <= max_allowed):
                errors.append(f"Class imbalance: action '{act}' has {c} items (expected {expected_per_class} +/- {class_tolerance})")

    if multi_day_count < 1:
        errors.append("Cardinality violation: Multi-day skips (len(dates) >= 2) not present in dataset")
    if both_session_count < 1:
        errors.append("Cardinality violation: session == 'both' not present in dataset")
    if emoji_count < 1:
        errors.append("Cardinality violation: Emojis not present in dataset")

    stats = {
        "total_records": len(records),
        "action_counts": {str(k): v for k, v in action_counts.items()},
        "multi_day_count": multi_day_count,
        "both_session_count": both_session_count,
        "emoji_count": emoji_count,
        "max_pairwise_sim": max_pairwise_sim,
    }
    return (len(errors) == 0, errors, stats)

def run_self_tests():
    print("Running verify_augmented_dataset self-tests...")
    def make_unique_record(idx, action, has_multi_day=False, is_both=False, with_emoji=True):
        sid = f"SYN_{action}_{idx:04d}"
        clock_str = f"2026-11-02 08:{idx%60:02d}:00"
        dates = ["2026-11-05", "2026-11-06"] if (action in ("APPLY_SKIP", "CANCEL_SKIP") and has_multi_day) else (["2026-11-05"] if action in ("APPLY_SKIP", "CANCEL_SKIP") else [])
        session = "both" if (is_both and action not in ("NEEDS_REVIEW_CLARIFY", None)) else ("lunch" if action in ("APPLY_SKIP", "CANCEL_SKIP") else None)
        notes = f"Alergi udang varian kata{idx}" if action == "UPDATE_DIETARY" else None
        pkg = "PAKET_BULANAN_LUNCH" if action == "RENEW_PACKAGE" else None
        emoji_str = " 🙏" if with_emoji else ""
        alpha = "".join(chr(ord('a') + int(c)) for c in f"{idx:04d}")
        u1, u2, u3, u4, u5, u6 = f"a{alpha}a", f"b{alpha}b", f"c{alpha}c", f"d{alpha}d", f"e{alpha}e", f"f{alpha}f"
        turns = [
            {"role": "user", "content": f"pesan pembuka percakapan {u1} {u2} apel mangga jeruk", "timestamp": clock_str},
            {"role": "assistant", "content": f"jawaban admin catering {u3} {u4} nanas melon semangka", "timestamp": clock_str},
            {"role": "user", "content": f"konfirmasi keputusan {action} {u5} {u6} rambutan duku kelengkeng{emoji_str}", "timestamp": clock_str},
            {"role": "assistant", "content": f"notifikasi selesai proses {u1} {u4} manggis cempedak sirsak", "timestamp": clock_str},
            {"role": "user", "content": f"terima kasih penutup {u2} {u5} pepaya belimbing delima", "timestamp": clock_str}
        ]
        return {
            "id": sid, "category": "augmented_training", "clock": clock_str,
            "turns": turns, "deciding_turn_index": 2,
            "gold_call": {"action": action, "dates": dates, "session": session, "notes": notes, "renewal_package": pkg}
        }
    records = []
    rec_idx = 0
    for act in ALL_ACTION_KEYS:
        for i in range(10):
            rec_idx += 1
            records.append(make_unique_record(rec_idx, act, has_multi_day=(i == 0), is_both=(i == 1), with_emoji=(i % 2 == 0)))
    ok, errors, _ = verify_records(records, None, expected_total=80, expected_per_class=10)
    assert ok, f"Valid dataset failed: {errors}"
    print("  ✓ Test 1: Valid dataset passed all checks")

    bad = [json.loads(json.dumps(r)) for r in records]
    bad[0]["turns"][0]["role"] = "robot"
    ok, errors, _ = verify_records(bad, None, expected_total=80, expected_per_class=10)
    assert not ok and any("invalid role 'robot'" in e for e in errors)
    print("  ✓ Test 2: Schema violation caught")

    bad = [json.loads(json.dumps(r)) for r in records]
    bad[1]["turns"][0]["content"] = bad[0]["turns"][0]["content"]
    ok, errors, _ = verify_records(bad, None, expected_total=80, expected_per_class=10)
    assert not ok and any("Duplicate 6+ word bubble" in e for e in errors)
    print("  ✓ Test 3: Duplicate 6+ word bubble caught")

    bad = [json.loads(json.dumps(r)) for r in records]
    bad[1]["turns"][2]["content"] = bad[0]["turns"][2]["content"]
    ok, errors, _ = verify_records(bad, None, expected_total=80, expected_per_class=10)
    assert not ok and any("Duplicate deciding bubble" in e for e in errors)
    print("  ✓ Test 4: Duplicate deciding bubble caught")

    no_multi = [json.loads(json.dumps(r)) for r in records]
    for r in no_multi:
        r["gold_call"]["dates"] = ["2026-11-05"] if r["gold_call"]["dates"] else []
    ok, errors, _ = verify_records(no_multi, None, expected_total=80, expected_per_class=10)
    assert not ok and any("Multi-day skips" in e for e in errors)
    print("  ✓ Test 5: Missing multi-day skips caught")

    no_both = [json.loads(json.dumps(r)) for r in records]
    for r in no_both:
        if r["gold_call"]["session"] == "both":
            r["gold_call"]["session"] = "lunch"
    ok, errors, _ = verify_records(no_both, None, expected_total=80, expected_per_class=10)
    assert not ok and any("session == 'both'" in e for e in errors)
    print("  ✓ Test 6: Missing session == 'both' caught")

    no_emo = [json.loads(json.dumps(r)) for r in records]
    for r in no_emo:
        for t in r["turns"]:
            t["content"] = re.sub(EMOJI_REGEX, "", t["content"])
    ok, errors, _ = verify_records(no_emo, None, expected_total=80, expected_per_class=10)
    assert not ok and any("Emojis" in e for e in errors)
    print("  ✓ Test 7: Missing emojis caught")

    fake_test = {"ids": {records[0]["id"]}, "dialogues": set(), "deciding": set(), "long_bubbles": set(), "4grams": {}, "inv_index": {}}
    ok, errors, _ = verify_records(records, fake_test, expected_total=80, expected_per_class=10)
    assert not ok and any("Scenario ID matches test set" in e for e in errors)
    print("  ✓ Test 8: Test set ID leakage caught")

    print("All 8 self-test assertions passed successfully!")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Strict verification for training & test datasets.")
    parser.add_argument("--train-file", default="datasets/training_set_1740.jsonl")
    parser.add_argument("--test-dir", default="datasets/sealed/sealed_eval_400.jsonl")
    parser.add_argument("--expected-total", type=int, default=1740)
    parser.add_argument("--expected-per-class", type=int, default=150)
    parser.add_argument("--class-tolerance", type=int, default=5)
    parser.add_argument("--no-enforce-class-balance", action="store_true")
    parser.add_argument("--jaccard-threshold", type=float, default=0.35)
    parser.add_argument("--max-pairwise-samples", type=int, default=5000)
    parser.add_argument("--self-test", action="store_true", help="Run self-test suite")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(run_self_tests())

    if not os.path.exists(args.train_file):
        print(f"ERROR: Training file not found: {args.train_file}")
        sys.exit(1)

    try:
        test_info = load_test_dataset(args.test_dir)
        print(f"Loaded {test_info['count']} test scenarios from {args.test_dir}.")
    except Exception as e:
        print(f"ERROR: Failed loading test dataset: {e}")
        sys.exit(1)

    records = []
    with open(args.train_file, "r", encoding="utf-8") as fp:
        for line_no, line in enumerate(fp, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception as e:
                print(f"ERROR: {args.train_file}:{line_no} Invalid JSON: {e}")
                sys.exit(1)

    ok, errors, stats = verify_records(
        records=records,
        test_info=test_info,
        expected_total=args.expected_total,
        expected_per_class=args.expected_per_class,
        class_tolerance=args.class_tolerance,
        enforce_class_balance=not args.no_enforce_class_balance,
        jaccard_threshold=args.jaccard_threshold,
        max_pairwise_samples=args.max_pairwise_samples,
    )

    print(f"\nVerification Results ({args.train_file}):")
    print(f"- Total records: {stats['total_records']}")
    print(f"- Class distribution: {stats['action_counts']}")
    print(f"- Multi-day skip records: {stats['multi_day_count']}")
    print(f"- Both-session records: {stats['both_session_count']}")
    print(f"- Emoji records: {stats['emoji_count']}")
    print(f"- Max sampled train pairwise 4-gram Jaccard: {stats['max_pairwise_sim']:.4f}")

    if not ok:
        print(f"\nFAILED: {len(errors)} violations found:")
        for e in errors[:50]:
            print(f"  [x] {e}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more.")
        sys.exit(1)

    print("\nALL STRICT CHECKS PASSED (exit code 0).")
    sys.exit(0)

if __name__ == "__main__":
    main()
