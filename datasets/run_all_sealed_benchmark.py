#!/usr/bin/env python3
"""Unified Comprehensive Benchmark: Base Model vs. LoRA 1,700 across Sealed Testsets.
=====================================================================================
Supports --split:
  - multipolicy_100 (100 scenarios)
  - adversarial_100 (100 scenarios)
  - baseline_400    (400 scenarios)
  - all             (600 scenarios)

Saves incremental checkpoint to datasets/reports/all_sealed_comparison_report.json.
Zero regex. Pure neural decision grid.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from Final_Pipeline_Architecture import PassiveListeningPipeline


SEALED_FILES = {
    "multipolicy_100": os.path.join(ROOT_DIR, "datasets/sealed/multipolicy_sealed_100.jsonl"),
    "adversarial_100": os.path.join(ROOT_DIR, "datasets/sealed/adversarial_sealed_100.jsonl"),
    "baseline_400":    os.path.join(ROOT_DIR, "datasets/sealed/sealed_eval_400.jsonl"),
}

REPORT_PATH = os.path.join(ROOT_DIR, "datasets/reports/all_sealed_comparison_report.json")


def eval_prediction(pred: Dict[str, Any], gold: Dict[str, Any]) -> Dict[str, bool]:
    pred_action = pred.get("action")
    gold_action = gold.get("action")
    act_ok = (pred_action == gold_action)

    pred_dates = sorted(pred.get("dates") or [])
    gold_dates = sorted(gold.get("dates") or [])
    dates_ok = (pred_dates == gold_dates)

    pred_sess = pred.get("session")
    gold_sess = gold.get("session")
    sess_ok = (pred_sess == gold_sess)

    exact_ok = act_ok and dates_ok and sess_ok

    return {
        "action": act_ok,
        "dates": dates_ok,
        "session": sess_ok,
        "exact": exact_ok,
    }


def load_existing_report() -> Dict[str, Any]:
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "timestamp": datetime.now().isoformat(),
        "splits": {},
        "failures_sample": [],
    }


def save_report(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_split(pipe: PassiveListeningPipeline, split_name: str, file_path: str, master_report: Dict[str, Any]):
    print(f"\n\033[1;36m>>> RUNNING BENCHMARK SPLIT: {split_name} ({file_path})\033[0m")
    scenarios: List[Dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))

    total = len(scenarios)
    print(f"Total scenarios in split: {total}")

    lora_stats = {"action": 0, "dates": 0, "session": 0, "exact": 0}
    base_stats = {"action": 0, "dates": 0, "session": 0, "exact": 0}
    split_failures = []

    t0 = time.perf_counter()

    for idx, sc in enumerate(scenarios, 1):
        sid = sc.get("id", f"case_{idx}")
        gold = sc.get("gold_call", {})
        customer_id = sc.get("student_id", "STD_UNKNOWN")
        turns = sc.get("turns", [])
        clock = sc.get("clock")

        # 1. LoRA pass
        pred_lora = pipe.process_message_thread(customer_id, turns, clock)
        l_eval = eval_prediction(pred_lora, gold)

        # 2. Base pass
        with pipe.backend.model.disable_adapter():
            pred_base = pipe.process_message_thread(customer_id, turns, clock)
        b_eval = eval_prediction(pred_base, gold)

        for k in ("action", "dates", "session", "exact"):
            if l_eval[k]:
                lora_stats[k] += 1
            if b_eval[k]:
                base_stats[k] += 1

        if not l_eval["exact"] and len(split_failures) < 25:
            split_failures.append({
                "id": sid,
                "split": split_name,
                "category": sc.get("category", "unspecified"),
                "gold": gold,
                "lora": {"action": pred_lora.get("action"), "dates": pred_lora.get("dates"), "session": pred_lora.get("session")},
                "base": {"action": pred_base.get("action"), "dates": pred_base.get("dates"), "session": pred_base.get("session")},
            })

        if idx % 10 == 0 or idx == total:
            elapsed = time.perf_counter() - t0
            pace = elapsed / idx
            rem = pace * (total - idx)
            l_pct = lora_stats["exact"] / idx * 100.0
            b_pct = base_stats["exact"] / idx * 100.0
            print(
                f"[{split_name}] [{idx:3d}/{total}] ({idx/total*100:5.1f}%) | "
                f"LoRA: \033[1;32m{l_pct:5.1f}%\033[0m | "
                f"Base: \033[1;33m{b_pct:5.1f}%\033[0m | "
                f"Pace: {pace:.2f}s/pair | ETA: {rem/60:.1f}m"
            )

    t_split = time.perf_counter() - t0

    master_report["splits"][split_name] = {
        "total": total,
        "runtime_seconds": round(t_split, 2),
        "base_exact_acc": round(base_stats["exact"] / total * 100.0, 2),
        "lora_exact_acc": round(lora_stats["exact"] / total * 100.0, 2),
        "base_action_acc": round(base_stats["action"] / total * 100.0, 2),
        "lora_action_acc": round(lora_stats["action"] / total * 100.0, 2),
        "base_dates_acc": round(base_stats["dates"] / total * 100.0, 2),
        "lora_dates_acc": round(lora_stats["dates"] / total * 100.0, 2),
        "delta_exact": round((lora_stats["exact"] - base_stats["exact"]) / total * 100.0, 2),
    }
    master_report["failures_sample"].extend(split_failures)
    master_report["timestamp"] = datetime.now().isoformat()
    save_report(master_report)
    print(f"Checkpointed split '{split_name}' to {REPORT_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["multipolicy_100", "adversarial_100", "baseline_400", "all"], default="all")
    args = parser.parse_args()

    master_report = load_existing_report()

    print("\nInitializing Final_Pipeline_Architecture with LoRA adapter...")
    pipe = PassiveListeningPipeline()

    splits_to_run = (
        ["multipolicy_100", "adversarial_100", "baseline_400"]
        if args.split == "all"
        else [args.split]
    )

    for sp in splits_to_run:
        path = SEALED_FILES[sp]
        run_split(pipe, sp, path, master_report)

    # Print summary
    print("\n" + "=" * 80)
    print("                 FINAL SEALED BENCHMARK AUDIT REPORT")
    print("=" * 80)
    for sp_name, data in master_report["splits"].items():
        diff = data["delta_exact"]
        diff_str = f"+{diff:.2f}%" if diff >= 0 else f"{diff:.2f}%"
        print(f"Split: {sp_name:<18} | Base Exact: {data['base_exact_acc']:5.2f}% | LoRA Exact: \033[1;32m{data['lora_exact_acc']:5.2f}%\033[0m | Delta: {diff_str}")
    print("=" * 80)


if __name__ == "__main__":
    main()
