#!/usr/bin/env python3
"""Namirims Ultimate Research Benchmark Harness.
==============================================
Asah 2026 Capstone Project - Application Engineering & Gen AI Track.

Runs comparative evaluation on Blind Sealed Testset with live developer-friendly
telemetry: dynamic progress bar, running accuracy, rolling latency, category breakdown,
and final ANSI-styled markdown & terminal receipts.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent dir to path so it can import Final_Pipeline_Architecture
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from Final_Pipeline_Architecture import (
    PassiveListeningPipeline,
    DEFAULT_LORA_PATH,
    DECISION_MODEL_PATH,
    INTENT_CLASSES,
)

# ---------------------------------------------------------------------------
# ANSI Terminal Formatting Helpers
# ---------------------------------------------------------------------------
class TermColor:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    WHITE_BOLD = "\033[1;37m"

def render_progress_bar(current: int, total: int, width: int = 24) -> str:
    fraction = current / total
    filled = int(fraction * width)
    bar = "█" * filled + "░" * (width - filled)
    percent = fraction * 100
    return f"[{bar}] {percent:5.1f}% ({current}/{total})"


class HeuristicRegexBaseline:
    """Config C: Naive Regex/Keyword Baseline for comparison."""
    def __init__(self):
        self.lora_attached = False

    def process_message_thread(self, customer_id: str, conversation_turns: List[Dict[str, Any]], current_clock: Optional[str] = None):
        t0 = time.perf_counter()
        import re
        text = " ".join(t.get("content", "") for t in conversation_turns if isinstance(t, dict)).lower()

        action = "QUERY_ONLY"
        session = None
        dates = []

        if re.search(r"ulat|kaca|staples|basi|bangkai|keracunan", text):
            action = "ESCALATE_OWNER"
        elif re.search(r"alergi|pantang|pedas|seafood|udang|ayam", text):
            action = "UPDATE_DIETARY"
        elif re.search(r"perpanjang|paket|transfer|lunas|hemat|nikmat", text):
            action = "RENEW_PACKAGE"
        elif re.search(r"batal libur|gak jadi libur|tetap kirim|resume|unskip", text):
            action = "CANCEL_SKIP"
        elif re.search(r"libur|skip|off|nggak kirim|jangan kirim", text):
            action = "APPLY_SKIP"
        elif re.search(r"ragu|bingung|gimana ya|tanya dulu|belum pasti", text):
            action = "NEEDS_REVIEW_CLARIFY"

        if "siang" in text and "malam" in text:
            session = "both"
        elif "siang" in text:
            session = "lunch"
        elif "malam" in text:
            session = "dinner"

        found = re.findall(r"\b2026-\d{2}-\d{2}\b", text)
        if found:
            dates = sorted(list(set(found)))

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "APPROVED",
            "action": action,
            "dates": dates,
            "session": session,
            "latency_ms": latency_ms,
        }


def run_benchmark():
    parser = argparse.ArgumentParser(description="Ultimate Passive Listening Benchmark Harness")
    parser.add_argument(
        "--testset",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "sealed", "sealed_eval_400.jsonl"),
        help="Path to 400 sealed test cases",
    )
    parser.add_argument(
        "--configs",
        type=str,
        default="A,B,C",
        help="Comma-separated configs: A (Base), B (LoRA), C (Regex Baseline)",
    )
    parser.add_argument(
        "--lora-path",
        type=str,
        default=DEFAULT_LORA_PATH,
        help="Path to fine-tuned LoRA checkpoint",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "reports", "comparison_report.json"),
        help="Path to save output JSON",
    )
    args = parser.parse_args()

    # Terminal Header
    print(f"\n{TermColor.BOLD}{TermColor.CYAN}╔═════════════════════════════════════════════════════════════════════════════╗{TermColor.RESET}")
    print(f"{TermColor.BOLD}{TermColor.CYAN}║     NAMIRIMS AI: ULTIMATE PASSIVE LISTENING BENCHMARK RUNNER (2026)         ║{TermColor.RESET}")
    print(f"{TermColor.BOLD}{TermColor.CYAN}╚═════════════════════════════════════════════════════════════════════════════╝{TermColor.RESET}")
    print(f" {TermColor.DIM}Engine Architecture : Final_Pipeline_Architecture.py{TermColor.RESET}")
    print(f" {TermColor.DIM}Target Dataset      : {args.testset}{TermColor.RESET}")
    print(f" {TermColor.DIM}Active Timestamp    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{TermColor.RESET}\n")

    if not os.path.exists(args.testset):
        print(f"{TermColor.RED}[!] ERROR: Testset not found at: {args.testset}{TermColor.RESET}")
        sys.exit(1)

    scenarios = []
    with open(args.testset, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))
    total_samples = len(scenarios)
    print(f"{TermColor.GREEN}✔ Successfully loaded {TermColor.BOLD}{total_samples}{TermColor.RESET}{TermColor.GREEN} blind adversarial test cases.{TermColor.RESET}\n")

    configs = [c.strip().upper() for c in args.configs.split(",") if c.strip()]
    results = {}

    for cfg in configs:
        print(f"{TermColor.BOLD}{TermColor.WHITE_BOLD}─────────────────────────────────────────────────────────────────────────────{TermColor.RESET}")
        if cfg == "A":
            name = "Intern-Decision-4B Base (Zero-Shot)"
            print(f" {TermColor.YELLOW}▶ CONFIG A:{TermColor.RESET} {TermColor.BOLD}{name}{TermColor.RESET}")
            print(f"   {TermColor.DIM}Loading base model without adapter...{TermColor.RESET}")
            pipeline = PassiveListeningPipeline(use_lora=False)
        elif cfg == "B":
            name = "Intern-Decision-4B + QLoRA (Fine-Tuned / Hardened)"
            print(f" {TermColor.GREEN}▶ CONFIG B:{TermColor.RESET} {TermColor.BOLD}{name}{TermColor.RESET}")
            print(f"   {TermColor.DIM}Loading model with remapped LoRA adapter from: {args.lora_path}...{TermColor.RESET}")
            pipeline = PassiveListeningPipeline(lora_checkpoint=args.lora_path, use_lora=True)
        elif cfg == "C":
            name = "Heuristic Fallback (Regex Rule Baseline)"
            print(f" {TermColor.MAGENTA}▶ CONFIG C:{TermColor.RESET} {TermColor.BOLD}{name}{TermColor.RESET}")
            print(f"   {TermColor.DIM}Initializing keyword state-machine baseline...{TermColor.RESET}")
            pipeline = HeuristicRegexBaseline()
        else:
            print(f" [!] Unknown config: {cfg}, skipping...")
            continue

        print(f"   {TermColor.CYAN}Running inference across {total_samples} multi-turn threads...{TermColor.RESET}\n")

        correct_exact = 0
        correct_action = 0
        correct_session = 0
        latencies: List[float] = []
        cat_stats = defaultdict(lambda: {"total": 0, "correct": 0})

        t_start = time.time()
        for idx, sc in enumerate(scenarios, 1):
            gold = sc.get("gold_call") or {}
            g_action = str(gold.get("action"))
            g_dates = sorted(gold.get("dates") or [])
            g_session = gold.get("session")
            cat = sc.get("category", "general")

            pred = pipeline.process_message_thread(
                customer_id=sc.get("student_id", f"student_{idx}"),
                conversation_turns=sc.get("turns", []),
                current_clock=sc.get("clock", "2026-11-16 08:00:00"),
            )

            p_action = str(pred.get("action"))
            p_dates = sorted(pred.get("dates") or [])
            p_session = pred.get("session")
            lat = pred.get("latency_ms", 0.0)
            latencies.append(lat)

            action_ok = (p_action == g_action)
            dates_ok = (p_dates == g_dates)
            sess_ok = (p_session == g_session)
            exact_ok = action_ok and dates_ok and sess_ok

            if exact_ok:
                correct_exact += 1
            if action_ok:
                correct_action += 1
            if sess_ok:
                correct_session += 1

            cat_stats[cat]["total"] += 1
            if exact_ok:
                cat_stats[cat]["correct"] += 1

            # Intuitive Real-Time Developer Telemetry every 25 samples & on final sample
            if idx % 25 == 0 or idx == total_samples:
                curr_acc = (correct_exact / idx) * 100
                avg_lat = sum(latencies) / idx
                bar_str = render_progress_bar(idx, total_samples)
                line = (
                    f"   {bar_str} | "
                    f"Acc: {TermColor.BOLD}{TermColor.GREEN if curr_acc >= 85 else TermColor.YELLOW}{curr_acc:5.2f}%{TermColor.RESET} | "
                    f"Lat: {avg_lat:5.1f}ms | "
                    f"Action: {(correct_action/idx)*100:4.1f}%"
                )
                print(line)

        elapsed = time.time() - t_start
        sorted_lat = sorted(latencies)
        p50 = sorted_lat[int(len(sorted_lat) * 0.50)] if sorted_lat else 0.0
        p95 = sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)] if sorted_lat else 0.0
        exec_acc = (correct_exact / total_samples) * 100

        print(f"\n   {TermColor.BOLD}✔ Completed Config {cfg}:{TermColor.RESET}")
        print(f"     • Overall Accuracy : {TermColor.BOLD}{TermColor.GREEN if exec_acc > 85 else TermColor.YELLOW}{exec_acc:.2f}%{TermColor.RESET} ({correct_exact}/{total_samples})")
        print(f"     • Intent Accuracy  : {(correct_action / total_samples) * 100:.2f}%")
        print(f"     • Latency Telemetry: Mean={sum(latencies)/total_samples:.1f}ms | p50={p50:.1f}ms | p95={p95:.1f}ms")
        print(f"     • Total Duration   : {elapsed:.1f}s\n")

        results[cfg] = {
            "config_name": name,
            "accuracy": round(exec_acc, 2),
            "intent_accuracy": round((correct_action / total_samples) * 100, 2),
            "mean_latency_ms": round(sum(latencies) / total_samples, 2),
            "p50_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2),
            "category_breakdown": {
                c: {
                    "total": s["total"],
                    "accuracy": round((s["correct"] / s["total"]) * 100, 2) if s["total"] > 0 else 0.0,
                }
                for c, s in cat_stats.items()
            },
        }

        del pipeline
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    # Save Output
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2)

    # Final Comparative Summary Table
    print(f"{TermColor.BOLD}{TermColor.CYAN}╔═════════════════════════════════════════════════════════════════════════════╗{TermColor.RESET}")
    print(f"{TermColor.BOLD}{TermColor.CYAN}║                     FINAL COMPARATIVE BENCHMARK SUMMARY                     ║{TermColor.RESET}")
    print(f"{TermColor.BOLD}{TermColor.CYAN}╚═════════════════════════════════════════════════════════════════════════════╝{TermColor.RESET}")
    print(f"| {'Config':<8} | {'Architecture / Model':<38} | {'Acc (%)':<8} | {'Intent (%)':<10} | {'Mean Lat':<10} |")
    print(f"|{'-'*10}|{'-'*40}|{'-'*10}|{'-'*12}|{'-'*12}|")
    for cfg, r in results.items():
        print(f"| {cfg:<8} | {r['config_name']:<38} | {r['accuracy']:6.2f}%  | {r['intent_accuracy']:8.2f}%  | {r['mean_latency_ms']:6.1f} ms |")
    print(f"{TermColor.DIM}─────────────────────────────────────────────────────────────────────────────{TermColor.RESET}")
    print(f"✔ Full JSON receipt saved to: {TermColor.BOLD}{args.output}{TermColor.RESET}\n")


if __name__ == "__main__":
    run_benchmark()
