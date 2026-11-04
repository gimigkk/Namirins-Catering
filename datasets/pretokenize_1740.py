#!/usr/bin/env python3
"""Pre-tokenizes 1,740-scenario training corpus for Intern-Decision-4B QLoRA.
=============================================================================
Combines:
  1) 1,200 baseline single-intent non-templated scenarios (leakage-repaired)
  2) 540 multi-policy compound scenarios (including commuter non-consecutive)

Applies exact decision-token loss masking:
  - Prompt tokens, system prompt, JSON formatting tokens -> label: -100
  - Decision value spans (policy, session, risk, tier, 9 calendar dates) -> label: token_ids
Produces:
  - datasets/tokenized_train_1740.json.gz
  - Embedded DATA_B64 update for train_colab.ipynb
  - Embedded BUNDLE_B64 update for train_colab.ipynb
"""

import base64
from datetime import datetime, timedelta
import gzip
import json
import os
import sys

from transformers import AutoTokenizer

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOKENIZER_DIR = os.path.join(ROOT_DIR, "models/checkpoints/intern_decision_lora_fixed")
NOTEBOOK_PATH = os.path.join(ROOT_DIR, "train_colab.ipynb")
GZ_OUT_PATH = os.path.join(ROOT_DIR, "datasets/tokenized_train_1740.json.gz")
TRAIN_1740_PATH = os.path.join(ROOT_DIR, "datasets/training_set_1740.jsonl")

TIER_MAP = {
    "PAKET_HEMAT_LUNCH": "hemat",
    "PAKET_REGULER_BOTH": "reguler",
    "PAKET_AYAM_DINNER": "ayam",
    "PAKET_BULANAN_LUNCH": "bulanan",
    "PAKET_BULANAN_BOTH": "bulanan",
    "PAKET_VEGETARIAN_LUNCH": "vegetarian",
    "PAKET_PROTEIN_BOTH": "protein",
}

ANSWER_SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

SYSTEM_PROMPT = (
    "You are a careful decision assistant. Use the state and decision schema in the user message "
    "to make the requested decisions. For every field, choose exactly one answer symbol (e.g. A, B, C, ...) "
    "from its listed options and return one valid JSON object mapping each field name to its chosen symbol. "
    "Use the field names and symbols exactly as given. Do not include explanations, Markdown, or extra text."
)

INDO_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
INDO_MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

INTENT_OPTIONS = [
    ("APPLY_SKIP", "Pelanggan meminta libur makan, jeda kirim, atau membatalkan pengiriman katering."),
    ("CANCEL_SKIP", "Pelanggan meminta pembatalan libur makan dan ingin katering kembali dikirim normal."),
    ("UPDATE_DIETARY", "Pelanggan menyampaikan catatan alergi, pantangan bahan, atau preferensi menu."),
    ("RENEW_PACKAGE", "Pelanggan meminta perpanjangan paket atau memesan paket langganan baru."),
    ("ESCALATE_OWNER", "Pelanggan melaporkan bahaya fisik makanan, keracunan, atau komplain darurat."),
    ("NEEDS_REVIEW_CLARIFY", "Pelanggan berniat mengubah jadwal namun tanggal atau sesi tidak jelas/rancu."),
    ("QUERY_ONLY", "Pertanyaan informasi umum, jadwal menu harian, atau sekadar obrolan biasa."),
]
SESSION_OPTIONS = [
    ("lunch", "Sesi makan siang."),
    ("dinner", "Sesi makan malam."),
    ("both", "Kedua sesi makan (siang dan malam)."),
    ("unspecified", "Sesi makan tidak dispesifikasikan."),
]
RISK_OPTIONS = [
    ("SAFE_AUTOMATED", "Permintaan operasional standar yang aman diproses sistem secara otomatis."),
    ("ESCALATE_TO_HUMAN", "Bahaya fisik makanan (pecahan kaca, benda asing), alergi akut, atau komplain darurat."),
]
TIER_OPTIONS = [
    ("hemat", "Paket Hemat."),
    ("nikmat", "Paket Nikmat."),
    ("kenyang", "Paket Kenyang."),
    ("bulanan", "Paket Bulanan."),
    ("mingguan", "Paket Mingguan."),
    ("ayam", "Paket Ayam."),
    ("protein", "Paket Protein."),
    ("reguler", "Paket Reguler."),
    ("vegetarian", "Paket Vegetarian."),
    ("unspecified", "Tidak ada tier paket yang disebutkan."),
]


def _get_relative_date_label(offset_days: int, d_obj) -> str:
    day_id = INDO_DAYS[d_obj.weekday()]
    day_en = d_obj.strftime("%A")
    m_id = INDO_MONTHS[d_obj.month]
    d_str = d_obj.strftime("%Y-%m-%d")
    if offset_days == 0:
        rel = "Hari ini / Today"
    elif offset_days == 1:
        rel = "Besok / Tomorrow"
    elif offset_days == 2:
        rel = "Lusa / Day after tomorrow"
    else:
        rel = f"{offset_days} hari lagi / in {offset_days} days"
    return f"{d_str} ({rel}, {day_id}/{day_en}, {d_obj.day} {m_id})"


def _val_to_symbol(value: str, options: list[tuple[str, str]]) -> str:
    for idx, (val, _desc) in enumerate(options):
        if val == value:
            return ANSWER_SYMBOLS[idx]
    raise ValueError(f"Value {value!r} not found in options {[v for v,_ in options]}")


def derive_gold_symbols(row: dict) -> tuple[dict, dict, list[str]]:
    """Returns (answer_symbols_dict, questions_ordered_dict, date_strings_9, all_yes).

    answer_symbols_dict maps field_name -> letter symbol (e.g. "A").
    questions_ordered_dict maps field_name -> list of (value, description) options.
    """
    gold = row.get("gold_call", {})
    secs = row.get("secondary_calls") or []

    action = gold.get("action")
    raw_dates = list(gold.get("dates") or [])
    session = gold.get("session")

    # In operational cutoff rejection scenarios (temporal cutoff crossing or emergency social engineering),
    # gold_call['action'] is None in sealed evaluations because the kitchen cutoff rejected the request.
    # The model must predict the underlying semantic intent (APPLY_SKIP / CANCEL_SKIP) and the target date
    # so verify_operational_cutoff() deterministically rejects it and sets status='REJECTED_CUTOFF', action=None.
    if action is None or action == "None":
        cat = row.get("category", "")
        if cat in ("temporal_cutoff_crossing", "social_engineering"):
            dti = row.get("deciding_turn_index")
            safe_turns = row.get("turns") or []
            t_content = safe_turns[dti].get("content", "").lower() if (dti is not None and dti < len(safe_turns)) else ""
            c_all = " ".join([t.get("content", "").lower() for t in safe_turns])

            if "batal libur" in c_all or "aktif kembali" in c_all or "cancel skip" in c_all:
                action = "CANCEL_SKIP"
            else:
                action = "APPLY_SKIP"

            # Derive requested target date (the day on which cutoff was attempted)
            clock_date = row["clock"].split()[0]
            raw_dates = [clock_date]

            # Derive requested session
            if "malam" in t_content or "dinner" in t_content:
                session = "dinner"
            elif "siang" in t_content or "lunch" in t_content:
                session = "lunch"
            elif "malam" in c_all or "dinner" in c_all:
                session = "dinner"
            elif "siang" in c_all or "lunch" in c_all:
                session = "lunch"
            else:
                session = "lunch"
        else:
            action = "QUERY_ONLY"

    if session not in ("lunch", "dinner", "both"):
        session = None
        for sc in secs:
            if sc.get("session") in ("lunch", "dinner", "both"):
                session = sc["session"]
                break
    if not session:
        rpkg = gold.get("renewal_package")
        if not rpkg and secs:
            for sc in secs:
                if sc.get("renewal_package"):
                    rpkg = sc["renewal_package"]
                    break
        if rpkg:
            if "BOTH" in rpkg:
                session = "both"
            elif "LUNCH" in rpkg:
                session = "lunch"
            elif "DINNER" in rpkg:
                session = "dinner"
            else:
                session = "unspecified"
        else:
            session = "unspecified"

    risk = "ESCALATE_TO_HUMAN" if action == "ESCALATE_OWNER" else "SAFE_AUTOMATED"

    rpkg = gold.get("renewal_package")
    if not rpkg and secs:
        for sc in secs:
            if sc.get("renewal_package"):
                rpkg = sc["renewal_package"]
                break
    tier = TIER_MAP.get(rpkg, "unspecified")

    clock_dt = datetime.strptime(row["clock"].split()[0], "%Y-%m-%d")
    dates_9 = [(clock_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(9)]

    # Strictly isolate target dates to primary operational delivery changes (no secondary package start dates)
    all_yes = set(raw_dates)

    answers = {}
    questions = {}

    answers["policy_intent"] = _val_to_symbol(action, INTENT_OPTIONS)
    questions["policy_intent"] = INTENT_OPTIONS

    answers["meal_session"] = _val_to_symbol(session, SESSION_OPTIONS)
    questions["meal_session"] = SESSION_OPTIONS

    answers["risk_escalation"] = _val_to_symbol(risk, RISK_OPTIONS)
    questions["risk_escalation"] = RISK_OPTIONS

    answers["package_tier"] = _val_to_symbol(tier, TIER_OPTIONS)
    questions["package_tier"] = TIER_OPTIONS

    return answers, questions, dates_9, all_yes


def format_row(row: dict, tokenizer: AutoTokenizer) -> dict:
    answers, questions, dates_9, all_yes = derive_gold_symbols(row)

    # Build conversation lines exactly as Pipeline_MultiPolicy.process_message_thread
    safe_turns = row["turns"] if isinstance(row["turns"], list) else []
    lines = []
    user_turns = []
    now_dt = datetime.strptime(row["clock"], "%Y-%m-%d %H:%M:%S")
    for i, turn in enumerate(safe_turns):
        if not isinstance(turn, dict):
            continue
        is_user = turn.get("role") in ("user", "CUSTOMER")
        sender = "Pelanggan" if is_user else "Admin"
        raw_c = turn.get("content") or turn.get("caption") or turn.get("body") or ""
        clean_c = (
            str(raw_c)
            .replace("<decision>", "[decision]")
            .replace("</decision>", "[/decision]")
            .replace("\r", " ")
            .replace("\n", " ")
            .strip()
        )
        raw_ts = turn.get("timestamp")
        ts = (now_dt + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S") if raw_ts is None else str(raw_ts).strip()
        time_part = ts.split(" ")[-1][:5] if " " in ts else ts[:5]
        lines.append(f"Turn {i+1} [{time_part}] {sender}: {clean_c}")
        if is_user:
            user_turns.append(turn)
    dialogue_text = "\n".join(lines)
    raw_latest = str(user_turns[-1].get("content") or user_turns[-1].get("body") or "") if user_turns else ""
    latest_user_text = raw_latest.replace("<decision>", "[decision]").replace("</decision>", "[/decision]").strip()

    state_dict = {
        "student_id": str(row.get("student_id", f"STD_{row.get('id', 'UNK')}")).replace("<decision>", "[decision]"),
        "current_clock": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "conversation_history": dialogue_text,
        "latest_customer_message": latest_user_text,
    }

    # Build schema lines exactly matching compile_row / _options format
    schema_lines = []
    base_date = now_dt.date()

    def _add_field(field_name, options, instr=""):
        syms = tuple(ANSWER_SYMBOLS[: len(options)])
        schema_lines.append(f"{field_name}: {instr}")
        for sym, (val, desc) in zip(syms, options):
            schema_lines.append(f"    {sym} = {val}: {desc}")

    _add_field("policy_intent", INTENT_OPTIONS)
    _add_field("meal_session", SESSION_OPTIONS)
    _add_field("risk_escalation", RISK_OPTIONS)
    _add_field("package_tier", TIER_OPTIONS)

    # decisive_turn field (mirrors Pipeline lines 461-469)
    active_customer_turns = list(reversed(user_turns[-5:]))
    if active_customer_turns:
        dt_options = []
        for idx_t, t in enumerate(active_customer_turns):
            snippet = str(t.get("content") or t.get("body") or "").replace("<decision>", "[decision]")[:40]
            dt_options.append((f"turn_{idx_t}", f"Balon chat (usia {idx_t}) yang memuat keputusan akhir: {snippet}"))
        _add_field("decisive_turn", dt_options)
        questions["decisive_turn"] = dt_options

        # Find gold decisive_turn symbol
        dti = row.get("deciding_turn_index")
        if dti is not None:
            user_turn_indices = [k for k, x in enumerate(safe_turns) if x.get("role") in ("user", "CUSTOMER")]
            reversed_last5 = list(reversed(user_turn_indices[-5:]))
            if dti in reversed_last5:
                gold_dt_idx = reversed_last5.index(dti)
                answers["decisive_turn"] = ANSWER_SYMBOLS[gold_dt_idx]
            else:
                answers["decisive_turn"] = "A"
        else:
            answers["decisive_turn"] = "A"

    # Date fields with relative labels (mirrors Pipeline lines 471-481)
    date_options_cache = {}
    for i, d_str in enumerate(dates_9):
        d_obj = base_date + timedelta(days=i)
        rel_label = _get_relative_date_label(i, d_obj)
        q_key = f"target_{d_str.replace('-', '_')}"
        d_options = [
            ("YES", f"Pelanggan meminta tindakan operasional pengiriman untuk tanggal {rel_label}."),
            ("NO", f"Tanggal {rel_label} tidak menjadi target aksi operasional pengiriman."),
        ]
        _add_field(q_key, d_options)
        questions[q_key] = d_options
        date_options_cache[q_key] = d_options
        answers[q_key] = _val_to_symbol("YES" if d_str in all_yes else "NO", d_options)

    state_str = json.dumps(state_dict, ensure_ascii=False, indent=2, sort_keys=False)
    user_prompt = f"State:\n{state_str}\n\nDecision schema:\n" + "\n".join(schema_lines)

    # Build assistant response: JSON mapping field -> chosen symbol
    all_fields = list(answers.keys())
    asst_dict = {f: answers[f] for f in all_fields}
    asst_str = json.dumps(asst_dict, ensure_ascii=False, indent=2, sort_keys=False)

    # Assemble using chat template tokens directly
    full_text = (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n\n{asst_str}<|im_end|>\n"
    )

    encoding = tokenizer(full_text, return_offsets_mapping=True, add_special_tokens=False)
    input_ids = encoding["input_ids"]
    labels = [-100] * len(input_ids)
    offsets = encoding["offset_mapping"]

    # Mask loss to only the letter-symbol tokens in the assistant JSON
    asst_start_char = full_text.find("<|im_start|>assistant")
    curr_search_pos = asst_start_char
    for field_name in all_fields:
        sym = answers[field_name]
        key_str = f'"{field_name}": "'
        key_pos = full_text.find(key_str, curr_search_pos)
        assert key_pos != -1, f"Could not find key {field_name}"
        val_start = key_pos + len(key_str)
        val_end = val_start + len(sym)
        assert full_text[val_start:val_end] == sym, f"Value mismatch for {field_name}: expected {sym!r}, got {full_text[val_start:val_end]!r}"

        for tok_idx, (tok_start, tok_end) in enumerate(offsets):
            if tok_start >= val_start and tok_end <= val_end:
                labels[tok_idx] = input_ids[tok_idx]
        curr_search_pos = val_end

    return {
        "input_ids": input_ids,
        "labels": labels,
        "attention_mask": [1] * len(input_ids),
    }


def main():
    print(f"Loading tokenizer from {TOKENIZER_DIR}...")
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_DIR, trust_remote_code=True)

    print(f"Loading cleaned 1,740 records directly from {TRAIN_1740_PATH}...")
    with open(TRAIN_1740_PATH, "r", encoding="utf-8") as f:
        records_raw = [json.loads(line) for line in f if line.strip()]
    assert len(records_raw) == 1740, f"Expected 1740 records, got {len(records_raw)}"

    print(f"Tokenizing and applying exact decision loss masking to all 1,740 records...")
    tokenized_1740 = []
    for idx, r in enumerate(records_raw):
        t_row = format_row(r, tokenizer)
        assert len(t_row["input_ids"]) == len(t_row["labels"]) == len(t_row["attention_mask"])
        unmasked = sum(1 for l in t_row["labels"] if l != -100)
        assert 14 <= unmasked <= 16, f"Scenario {idx} ({r['id']}): unmasked count {unmasked} anomalous (expected 14-15 single-char symbols)"
        tokenized_1740.append(t_row)

    print(f"Total tokenized records: {len(tokenized_1740)}")

    print(f"Serializing 1,740 tokenized records to {GZ_OUT_PATH}...")
    raw_bytes = json.dumps(tokenized_1740, ensure_ascii=False).encode("utf-8")
    gz_bytes = gzip.compress(raw_bytes, compresslevel=9)
    with open(GZ_OUT_PATH, "wb") as f:
        f.write(gz_bytes)
    print(f"Saved {GZ_OUT_PATH} ({len(gz_bytes)/1024:.1f} KB).")

    print("Encoding base64 string for Colab notebook embedding...")
    b64_str = base64.b64encode(gz_bytes).decode("ascii")
    print(f"Base64 length: {len(b64_str)} chars.")

    # Update train_colab.ipynb
    print(f"Updating {NOTEBOOK_PATH}...")
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # 1. Update Cell 0 header
    nb["cells"][0]["source"] = [
        "# QLoRA Fine-Tuning: Intern-Decision-4B (LoRA v6) on Google Colab (T4 / A100 GPU)\n",
        "\n",
        "Pre-tokenized, decision-masked training dataset embedded (1,740 clean scenarios).\n",
        "Inference-aligned prompt format: letter-symbol supervision matching Pipeline compile_row.\n",
        "LoRA r=16, alpha=32, all 7 projections, lr=1.5e-4, 4 epochs.\n",
    ]

    # 2. Update Cell 4 DATA_B64
    cell_ingest = nb["cells"][4]
    new_source_cell4 = []
    for line in cell_ingest["source"]:
        if line.startswith("DATA_B64 = "):
            new_source_cell4.append(f'DATA_B64 = "{b64_str}"\n')
        else:
            new_source_cell4.append(line)
    cell_ingest["source"] = new_source_cell4

    # 3. Cell 6 and Cell 8 are NOT patched here — manage them directly in the notebook.

    # 4. Update Cell 12 Benchmark Bundle with latest Pipeline_MultiPolicy.py and all 600 sealed holdouts
    cell_eval = nb["cells"][12]
    bundle_files = {
        "multipolicy_sealed_100.jsonl": open(os.path.join(ROOT_DIR, "datasets/sealed/multipolicy_sealed_100.jsonl"), "r", encoding="utf-8").read(),
        "adversarial_sealed_100.jsonl": open(os.path.join(ROOT_DIR, "datasets/sealed/adversarial_sealed_100.jsonl"), "r", encoding="utf-8").read(),
        "sealed_eval_400.jsonl": open(os.path.join(ROOT_DIR, "datasets/sealed/sealed_eval_400.jsonl"), "r", encoding="utf-8").read(),
        "Pipeline_MultiPolicy.py": open(os.path.join(ROOT_DIR, "Pipeline_MultiPolicy.py"), "r", encoding="utf-8").read(),
    }
    raw_bundle_bytes = json.dumps(bundle_files, ensure_ascii=False).encode("utf-8")
    new_bundle_b64 = base64.b64encode(gzip.compress(raw_bundle_bytes, compresslevel=9)).decode("ascii")

    eval_code = "".join(cell_eval["source"])
    old_bundle_line = [l for l in cell_eval["source"] if l.startswith("BUNDLE_B64 = ")][0]
    eval_code = eval_code.replace(old_bundle_line, f'BUNDLE_B64 = "{new_bundle_b64}"\n')
    # Version label replacements are no longer needed; Cell 12 uses v5/v6 labels managed directly.
    cell_eval["source"] = [line + "\n" for line in eval_code.splitlines()]

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Successfully updated and validated {NOTEBOOK_PATH}.")


if __name__ == "__main__":
    main()
