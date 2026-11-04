#!/usr/bin/env python3
"""Pre-tokenizes 2,140-scenario training corpus for Intern-Decision-4B QLoRA.
=============================================================================
Combines:
  1) 1,200 baseline single-intent non-templated scenarios
  2) 540 multi-policy compound scenarios (independent policy grid)
  3) 400 counterfactual turnaround/concession scenarios

Applies exact decision-token loss masking:
  - Prompt tokens, system prompt, JSON formatting tokens -> label: -100
  - Decision value spans (policy, session, risk, tier, 9 calendar dates) -> label: token_ids
Produces:
  - datasets/tokenized_train_2140.json.gz
  - Embedded DATA_B64 update for train_colab.ipynb
"""

import base64
from datetime import datetime, timedelta
import glob
import gzip
import json
import os
import sys

from transformers import AutoTokenizer

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOKENIZER_DIR = os.path.join(ROOT_DIR, "models/checkpoints/intern_decision_lora_fixed")
NOTEBOOK_PATH = os.path.join(ROOT_DIR, "train_colab.ipynb")
GZ_OUT_PATH = os.path.join(ROOT_DIR, "datasets/tokenized_train_2140.json.gz")
TRAIN_2140_PATH = os.path.join(ROOT_DIR, "datasets/training_set_2140.jsonl")

TIER_MAP = {
    "PAKET_HEMAT_LUNCH": "hemat",
    "PAKET_REGULER_BOTH": "reguler",
    "PAKET_AYAM_DINNER": "ayam",
    "PAKET_BULANAN_LUNCH": "bulanan",
    "PAKET_BULANAN_BOTH": "bulanan",
    "PAKET_VEGETARIAN_LUNCH": "vegetarian",
    "PAKET_PROTEIN_BOTH": "protein",
}


def derive_compound_asst(row: dict) -> tuple[dict, list[str]]:
    gold = row.get("gold_call", {})
    secs = row.get("secondary_calls") or []

    action = gold.get("action")
    if action is None or action == "None":
        action = "QUERY_ONLY"
    policy_intent = action

    session = gold.get("session")
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
    if not risk and secs:
        for sc in secs:
            if sc.get("action") == "ESCALATE_OWNER":
                risk = "ESCALATE_TO_HUMAN"
                break

    rpkg = gold.get("renewal_package")
    if not rpkg and secs:
        for sc in secs:
            if sc.get("renewal_package"):
                rpkg = sc["renewal_package"]
                break
    tier = TIER_MAP.get(rpkg, "unspecified")

    clock_str = row["clock"]
    t0 = datetime.strptime(clock_str, "%Y-%m-%d %H:%M:%S")
    dates_9 = [(t0 + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(9)]

    all_yes = set()
    for d in gold.get("dates") or []:
        all_yes.add(d)
    for sc in secs:
        for d in sc.get("dates") or []:
            all_yes.add(d)

    res = {
        "policy_intent": policy_intent,
        "meal_session": session,
        "risk_escalation": risk,
        "package_tier": tier,
    }
    for d in dates_9:
        d_clean = d.replace("-", "_")
        res[f"target_{d_clean}"] = "YES" if d in all_yes else "NO"

    return res, dates_9


def format_row(row: dict, tokenizer: AutoTokenizer) -> dict:
    asst_dict, dates_9 = derive_compound_asst(row)

    lines = []
    for i, t in enumerate(row["turns"]):
        sender = "Pelanggan" if t.get("role") in ("user", "CUSTOMER") else "Admin"
        c = (
            t.get("content", "")
            .replace("<decision>", "[decision]")
            .replace("</decision>", "[/decision]")
            .replace("\r", " ")
            .replace("\n", " ")
            .strip()
        )
        ts = t.get("timestamp", "").strip()
        time_part = ts.split(" ")[-1][:5] if " " in ts else ts[:5]
        lines.append(f"Turn {i+1} [{time_part}] {sender}: {c}")
    conversation_history = "\n".join(lines)

    user_turns = [t for t in row["turns"] if t.get("role") in ("user", "CUSTOMER")]
    latest_customer_message = (
        user_turns[-1]["content"]
        .replace("<decision>", "[decision]")
        .replace("</decision>", "[/decision]")
        .strip()
        if user_turns
        else ""
    )

    state_dict = {
        "student_id": row.get("student_id", f"STD_{row.get('id', 'UNK')}"),
        "current_clock": row["clock"],
        "conversation_history": conversation_history,
        "latest_customer_message": latest_customer_message,
    }
    state_str = json.dumps(state_dict, ensure_ascii=False, indent=2)

    q_lines = [
        "- policy_intent: (APPLY_SKIP, CANCEL_SKIP, UPDATE_DIETARY, RENEW_PACKAGE, ESCALATE_OWNER, NEEDS_REVIEW_CLARIFY, QUERY_ONLY)",
        "- meal_session: (lunch, dinner, both, unspecified)",
        "- risk_escalation: (SAFE_AUTOMATED, ESCALATE_TO_HUMAN)",
        "- package_tier: (hemat, nikmat, kenyang, bulanan, mingguan, ayam, protein, reguler, vegetarian, unspecified)",
    ]
    for d in dates_9:
        d_clean = d.replace("-", "_")
        q_lines.append(f"- target_{d_clean}: (YES, NO)")
    questions_str = "\n".join(q_lines)

    user_msg = (
        f"Return one answer for every field using the supplied allowed choices.\n\n"
        f"## State\n{state_str}\n\n## Questions\n{questions_str}"
    )

    asst_str = json.dumps(asst_dict, ensure_ascii=False, indent=2)
    full_text = (
        f"<|im_start|>system\nYou are a typed decision model. Read the state and answer the typed questions about it with one of the allowed choices.<|im_end|>\n"
        f"<|im_start|>user\n{user_msg}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n\n{asst_str}<|im_end|>\n"
    )

    encoding = tokenizer(full_text, return_offsets_mapping=True, add_special_tokens=False)
    input_ids = encoding["input_ids"]
    labels = [-100] * len(input_ids)
    offsets = encoding["offset_mapping"]

    asst_start_char = full_text.find("<|im_start|>assistant")
    curr_search_pos = asst_start_char
    for k, v in asst_dict.items():
        key_str = f'"{k}": "'
        key_pos = full_text.find(key_str, curr_search_pos)
        assert key_pos != -1, f"Could not find key {k}"
        val_start = key_pos + len(key_str)
        val_end = val_start + len(v)
        assert full_text[val_start:val_end] == v, f"Value mismatch for {k}"

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

    print(f"Loading 2,140 verified training scenarios from {TRAIN_2140_PATH}...")
    with open(TRAIN_2140_PATH, "r", encoding="utf-8") as f:
        train_rows = [json.loads(line) for line in f if line.strip()]
    assert len(train_rows) == 2140, f"Expected 2140 records, got {len(train_rows)}"
    print(f"Successfully loaded {len(train_rows)} scenarios.")

    print("Pre-tokenizing and decision-masking all 2,140 scenarios...")
    combined_2140 = []
    for idx, row in enumerate(train_rows):
        rec = format_row(row, tokenizer)
        unmasked = sum(1 for l in rec["labels"] if l != -100)
        assert 14 <= unmasked <= 40, f"Record {idx} ({row.get('id')}): unmasked count {unmasked} anomalous"
        combined_2140.append(rec)
    assert len(combined_2140) == 2140

    print(f"Serializing 2,140 tokenized records to {GZ_OUT_PATH}...")
    raw_bytes = json.dumps(combined_2140, ensure_ascii=False).encode("utf-8")
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

    # 1. Update Cell 0 Title & Description
    nb["cells"][0]["source"] = [
        "# QLoRA Fine-Tuning: Intern-Decision-4B on Google Colab (A100 / T4 GPU)\n",
        "\n",
        "Pre-tokenized, decision-masked training dataset embedded (2,140 non-templated scenarios: 1,200 baseline + 540 compound multi-policy + 400 counterfactual).\n",
        "LoRA v4 Regularized Setup: Attention-only projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`), RSLoRA (r=16, alpha=16), lr=8e-5, weight_decay=0.1, NEFTune alpha=5.\n",
        "Zero tokenization discrepancies; exact loss masking applied directly to decision spans.",
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

    # 3. Update Cell 6 LoraConfig (Attention-only target_modules, RSLoRA)
    cell_model = nb["cells"][6]
    model_code = "".join(cell_model["source"])
    # Replace LoraConfig
    old_lora = """peft_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)"""
    new_lora = """peft_config = LoraConfig(
    r=16,
    lora_alpha=16,
    use_rslora=True,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)"""
    assert old_lora in model_code, "Could not find expected LoraConfig block in Cell 6"
    model_code = model_code.replace(old_lora, new_lora)
    cell_model["source"] = [line + "\n" for line in model_code.splitlines()]

    # 4. Update Cell 8 TrainingArguments (lr=8e-5, weight_decay=0.1, neftune_noise_alpha=5)
    cell_train = nb["cells"][8]
    train_code = "".join(cell_train["source"])
    old_args = """training_args = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=4,        # safe peak VRAM on T4/L4/A100 (seq len ~1150)
    gradient_accumulation_steps=4,        # effective batch size = 16
    learning_rate=1.5e-4,
    logging_steps=10,
    num_train_epochs=4,
    warmup_steps=15,
    lr_scheduler_type="cosine",
    fp16=True,
    bf16=False,
    save_strategy="steps",
    save_steps=25,
    save_total_limit=2,
    report_to="none"
)"""
    new_args = """training_args = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=4,        # safe peak VRAM on T4/L4/A100 (seq len ~1150)
    gradient_accumulation_steps=4,        # effective batch size = 16 (2,140 / 16 = ~134 steps/epoch)
    learning_rate=8e-5,                   # calibrated for RSLoRA & attention-only tuning
    weight_decay=0.1,                     # AdamW regularization against representation collapse
    neftune_noise_alpha=5,                # embedding noise regularization
    logging_steps=10,
    num_train_epochs=4,
    warmup_steps=25,
    lr_scheduler_type="cosine",
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    save_strategy="steps",
    save_steps=25,
    save_total_limit=2,
    report_to="none"
)"""
    assert old_args in train_code, "Could not find expected TrainingArguments block in Cell 8"
    train_code = train_code.replace(old_args, new_args)
    train_code = train_code.replace(
        'print("Starting training on 1,740 masked samples across 4 epochs (435 steps total)...")',
        'print("Starting training on 2,140 masked samples across 4 epochs (535 steps total)...")'
    )
    cell_train["source"] = [line + "\n" for line in train_code.splitlines()]

    # 5. Update Cell 12 Benchmark Bundle with latest Pipeline_MultiPolicy.py and LoRA v4 labels
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
    eval_code = eval_code.replace("=== EVALUATING LoRA v3:", "=== EVALUATING LoRA v4:")
    eval_code = eval_code.replace("LoRA v3 (1 fast forward pass per scenario)", "LoRA v4 (1 fast forward pass per scenario)")
    eval_code = eval_code.replace("v3_exact", "v4_exact")
    eval_code = eval_code.replace("v3_action", "v4_action")
    eval_code = eval_code.replace("v3_dates", "v4_dates")
    cell_eval["source"] = [line + "\n" for line in eval_code.splitlines()]

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"Successfully updated and validated {NOTEBOOK_PATH}.")


if __name__ == "__main__":
    main()
