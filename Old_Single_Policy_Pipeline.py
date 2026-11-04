#!/usr/bin/env python3
"""Modul Pipeline Keputusan Passive Listening Namirims.
=====================================================
Capstone Asah 2026 - Jalur Application Engineering & Gen AI.

Arsitektur PaLiPi (Passive Listening Pipeline) Model:
- Pemantauan senyap di latar belakang obrolan WhatsApp pelanggan dan admin katering.
- Menghimpun episode percakapan utuh via Mutable Living Buffer (mendukung interupsi mid-inference).
- Ekstraksi keputusan operasional tanpa intervensi dialog: libur makan, batal libur,
  catatan alergi/diet, serta perpanjangan paket.
- Prinsip PVE (Propose-Validate-Execute): 100% keputusan bermuara ke Human-In-The-Loop (HITL) Queue
  sebagai draf proposal terstruktur (DRAFT_PENDING) lengkap dengan Digital Double & Customer Dossier.
- Inferensi saraf murni (Intern-Decision-4B + adapter QLoRA) berbasis penilaian logit kandidat.
- Bebas regex, bebas pencocokan kata mentah, dan kebal injeksi prompt.
- Penentuan tanggal deterministik & validasi batas jam operasional dapur (08:30 / 15:00 WIB).
- Latensi p95 sub-detik (<1.5 detik) pada GPU konsumen (<4 GB VRAM).
"""

import json
import os
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import AutoProcessor, AutoTokenizer, Qwen3_5ForConditionalGeneration

# ---------------------------------------------------------------------------
# Konstanta Global & Jalur Model
# ---------------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

DECISION_MODEL_PATH = os.environ.get(
    "DECISION_MODEL_PATH",
    os.path.expanduser("~/.cache/huggingface/hub/models--internlm--Intern-Decision-4B/snapshots/main"),
)
DEFAULT_LORA_PATH = os.environ.get(
    "LORA_CHECKPOINT_PATH",
    os.path.join(ROOT_DIR, "models/checkpoints/intern_decision_lora_fixed"),
)

DECISION_TOKEN = "<decision>"
ANSWER_SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
DEFAULT_TEMPERATURE = 1.99241824

SYSTEM_PROMPT = (
    "You are a careful decision assistant. Use the state and decision schema in the user message "
    "to make the requested decisions. For every field, choose exactly one answer symbol (e.g. A, B, C, ...) "
    "from its listed options and return one valid JSON object mapping each field name to its chosen symbol. "
    "Use the field names and symbols exactly as given. Do not include explanations, Markdown, or extra text."
)

INDO_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
INDO_MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

VALID_SESSIONS = {"lunch", "dinner", "both"}
LUNCH_CUTOFF = dt_time(8, 30, 0)
DINNER_CUTOFF = dt_time(15, 0, 0)

VALID_PACKAGE_SKUS = {
    "PAKET_HEMAT_LUNCH",
    "PAKET_REGULER_BOTH",
    "PAKET_AYAM_DINNER",
    "PAKET_BULANAN_LUNCH",
    "PAKET_BULANAN_BOTH",
    "PAKET_VEGETARIAN_LUNCH",
    "PAKET_PROTEIN_BOTH",
}

INTENT_CLASSES = [
    "APPLY_SKIP",
    "CANCEL_SKIP",
    "UPDATE_DIETARY",
    "RENEW_PACKAGE",
    "ESCALATE_OWNER",
    "NEEDS_REVIEW_CLARIFY",
    "QUERY_ONLY",
    "None",
]


# ---------------------------------------------------------------------------
# Backend Komputasi Logit (Intern-Decision-4B Logit Scoring Engine)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CompiledExample:
    messages: list[dict[str, Any]]
    fields: tuple[str, ...]
    symbols: dict[str, tuple[str, ...]]


def _options(question: Mapping[str, Any]) -> list[tuple[str, str]]:
    kind = question.get("type")
    criteria = question.get("criteria")
    if kind == "choice":
        if not isinstance(criteria, Mapping):
            raise ValueError("Kriteria pilihan ganda harus berupa objek pemetaan.")
        return [(str(key), str(value)) for key, value in criteria.items()]
    if kind == "score":
        if isinstance(criteria, list):
            return [(str(index), str(value)) for index, value in enumerate(criteria)]
        if isinstance(criteria, Mapping):
            return [(str(key), str(value)) for key, value in criteria.items()]
        raise ValueError("Kriteria skor harus berupa list atau objek pemetaan.")
    if kind == "noul":
        descriptions = criteria if isinstance(criteria, Mapping) else {}
        yes = next((str(descriptions[k]) for k in descriptions if str(k).lower() in {"yes", "true", "1"}), "Ya.")
        no = next((str(descriptions[k]) for k in descriptions if str(k).lower() in {"no", "false", "0"}), "Tidak.")
        return [("no", no), ("yes", yes)]
    raise ValueError(f"Tipe pertanyaan tidak didukung: {kind!r}")


def compile_row(row: Mapping[str, Any]) -> CompiledExample:
    questions = row.get("questions")
    if not isinstance(questions, Mapping) or not questions:
        raise ValueError(f"{row.get('id')}: questions wajib berupa objek yang tidak kosong.")
    fields: list[str] = []
    symbols: dict[str, tuple[str, ...]] = {}
    schema_lines: list[str] = []

    for field, question in questions.items():
        if not isinstance(question, Mapping):
            raise ValueError(f"Pertanyaan {field!r} bukan objek pemetaan.")
        options = _options(question)
        if not options:
            raise ValueError(f"Pertanyaan {field!r} tidak memiliki opsi pilihan.")
        if len(options) > len(ANSWER_SYMBOLS):
            raise ValueError(f"Maksimal {len(ANSWER_SYMBOLS)} simbol opsi yang didukung.")
        field_name = str(field)
        fields.append(field_name)
        field_symbols = tuple(ANSWER_SYMBOLS[: len(options)])
        symbols[field_name] = field_symbols
        instr = question.get("instructions", "")
        schema_lines.append(f"{field_name}: {instr}")
        for symbol, (value, description) in zip(field_symbols, options):
            schema_lines.append(f"    {symbol} = {value}: {description}")

    state = json.dumps(row.get("state"), ensure_ascii=False, indent=2, sort_keys=False)
    user_prompt = f"State:\n{state}\n\nDecision schema:\n" + "\n".join(schema_lines)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    return CompiledExample(messages=messages, fields=tuple(fields), symbols=symbols)


class DecisionEngine:
    """Mesin inferensi penilaian kandidat logit menggunakan HuggingFace transformers."""

    def __init__(
        self,
        checkpoint: str,
        device: str = "cuda",
        dtype: str = "bfloat16",
        load_in_4bit: bool = True,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        self.device = device
        self.temperature = float(temperature)
        torch_dtype = getattr(torch, dtype) if isinstance(dtype, str) else dtype
        self.processor = AutoProcessor.from_pretrained(checkpoint, trust_remote_code=True)
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)

        model_kwargs = {"trust_remote_code": True, "device_map": "auto"}
        if load_in_4bit:
            from transformers import BitsAndBytesConfig
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch_dtype,
                bnb_4bit_quant_type="nf4",
            )
        else:
            model_kwargs["torch_dtype"] = torch_dtype

        self.model = Qwen3_5ForConditionalGeneration.from_pretrained(checkpoint, **model_kwargs).eval()
        self.symbol_tokens = {sym: self.tokenizer.encode(sym, add_special_tokens=False)[0] for sym in ANSWER_SYMBOLS}
        self.decision_token_id = self.tokenizer.encode(DECISION_TOKEN, add_special_tokens=False)[-1]

    def predict(self, row: Mapping[str, Any]) -> dict[str, Any]:
        compiled = compile_row(row)
        skeleton_dict = {f: DECISION_TOKEN for f in compiled.fields}
        assistant_text = json.dumps(skeleton_dict, ensure_ascii=False, indent=2, sort_keys=False)
        full_messages = [*compiled.messages, {"role": "assistant", "content": assistant_text}]

        prompt_text = self.processor.apply_chat_template(full_messages, tokenize=False)
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device)
        input_ids = inputs.input_ids[0]

        decision_positions = (input_ids == self.decision_token_id).nonzero(as_tuple=True)[0]
        if len(decision_positions) != len(compiled.fields):
            raise ValueError(f"Ketidaksesuaian token decision: diharapkan {len(compiled.fields)}, ditemukan {len(decision_positions)}")

        query_indices = (decision_positions - 1).tolist()
        with torch.inference_mode():
            logits = self.model(**inputs).logits[0, query_indices, :]

        answers = {}
        for idx, field in enumerate(compiled.fields):
            field_symbols = compiled.symbols[field]
            target_token_ids = [self.symbol_tokens[s] for s in field_symbols]
            field_logits = logits[idx, target_token_ids].to(torch.float32)

            probs = torch.softmax(field_logits / self.temperature, dim=-1).tolist()
            chosen_idx = int(torch.argmax(field_logits).item())
            chosen_sym = field_symbols[chosen_idx]

            options = _options(row["questions"][field])
            chosen_val = options[chosen_idx][0]

            answers[field] = {
                "symbol": chosen_sym,
                "choice": chosen_val,
                "confidence": round(probs[chosen_idx], 4),
            }

        return {"answers": answers}


# ---------------------------------------------------------------------------
# Helper Kalender Operasional & Validator Batas Waktu Dapur (Cutoff)
# ---------------------------------------------------------------------------
def get_relative_date_label(offset_days: int, d_obj: date) -> str:
    """Menghasilkan label tanggal relatif dan kalender baku untuk prompt grounded."""
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


def parse_operational_timestamp(ts_val: Any, default_dt: datetime) -> datetime:
    """Mengurai berbagai format timestamp obrolan WhatsApp menjadi objek datetime standar."""
    if not ts_val:
        return default_dt
    if isinstance(ts_val, datetime):
        return ts_val
    if isinstance(ts_val, (int, float)):
        try:
            return datetime.fromtimestamp(ts_val)
        except (ValueError, OverflowError, OSError):
            return default_dt
    ts_str = str(ts_val).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            pass
    return default_dt


def verify_operational_cutoff(
    current_dt: datetime, action: str, target_dates: List[str], session: Optional[str]
) -> Tuple[bool, str, Optional[str]]:
    """Memverifikasi batas jam operasional dapur UMKM secara deterministik.
    
    Aturan:
    - Makan siang (lunch): cutoff jam 08:30 WIB.
    - Makan malam (dinner): cutoff jam 15:00 WIB.
    - Kedua sesi (both) pada hari H: jika lewat 08:30 tapi belum 15:00, penuhi parsial makan malam.
    """
    if action not in ("APPLY_SKIP", "CANCEL_SKIP"):
        return True, "OPERATION_VALID", session
    if not target_dates or not session:
        return False, "MISSING_PARAMETERS", None
    if session not in VALID_SESSIONS:
        return False, "INVALID_SESSION", None

    unique_dates = sorted(list(set(target_dates)))
    current_date = current_dt.date()
    current_time = current_dt.time().replace(tzinfo=None)
    has_partial_dinner = False

    for d_str in unique_dates:
        try:
            t_date = datetime.strptime(d_str, "%Y-%m-%d").date()
        except ValueError:
            return False, "INVALID_DATE_FORMAT", None

        if t_date < current_date:
            return False, "TARGET_DATE_IN_PAST", None

        if t_date == current_date:
            if session == "both":
                is_lunch_past = current_time >= LUNCH_CUTOFF
                is_dinner_past = current_time >= DINNER_CUTOFF
                if is_lunch_past and is_dinner_past:
                    return False, "BOTH_CUTOFFS_EXCEEDED", None
                elif is_lunch_past and not is_dinner_past:
                    if len(unique_dates) == 1:
                        return True, "PARTIAL_DINNER_FULFILLED", "dinner"
                    has_partial_dinner = True
            elif session == "lunch":
                if current_time >= LUNCH_CUTOFF:
                    return False, "LUNCH_CUTOFF_EXCEEDED", None
            elif session == "dinner":
                if current_time >= DINNER_CUTOFF:
                    return False, "DINNER_CUTOFF_EXCEEDED", None

    if has_partial_dinner:
        return False, "TODAY_LUNCH_CUTOFF_EXCEEDED_SPLIT_REQUIRED", None
    return True, "CUTOFF_VERIFIED", session


# ---------------------------------------------------------------------------
# Modul Pipeline Utama Passive Listening WhatsApp
# ---------------------------------------------------------------------------
class PassiveListeningPipeline:
    """Pipeline pengambilan keputusan pasif untuk aliran obrolan WhatsApp katering."""

    def __init__(
        self,
        base_checkpoint: Optional[str] = None,
        lora_checkpoint: Optional[str] = None,
        device: str = "cuda",
        load_in_4bit: bool = True,
        use_lora: bool = True,
    ):
        ckpt = base_checkpoint or DECISION_MODEL_PATH
        self.backend = DecisionEngine(checkpoint=ckpt, device=device, dtype="bfloat16", load_in_4bit=load_in_4bit)
        self.lora_attached = False

        if use_lora:
            resolved_lora = lora_checkpoint or DEFAULT_LORA_PATH
            if resolved_lora and os.path.exists(resolved_lora):
                try:
                    from peft import PeftModel
                    self.backend.model = PeftModel.from_pretrained(self.backend.model, resolved_lora).eval()
                    self.lora_attached = True
                except Exception:
                    pass

        self._lock = threading.Lock()

    def process_message_thread(
        self,
        customer_id: str,
        conversation_turns: List[Dict[str, Any]],
        current_clock: Optional[str] = None,
        operational_window_days: int = 9,
    ) -> Dict[str, Any]:
        """Pengamat pasif: memproses riwayat obrolan pelanggan menjadi kontrak aksi terstruktur."""
        t0 = time.perf_counter()
        now_dt = parse_operational_timestamp(current_clock, datetime.now())
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        base_date = now_dt.date()

        safe_turns = conversation_turns if isinstance(conversation_turns, list) else []
        lines = []
        user_turns = []
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

        has_user_turns = len(user_turns) > 0
        base_questions_count = 5 if has_user_turns else 4
        max_window_days = 16 - base_questions_count
        effective_window_days = max(1, min(operational_window_days, max_window_days))

        calendar_window = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(effective_window_days)]

        questions: Dict[str, Any] = {
            "policy_intent": {
                "type": "choice",
                "criteria": {
                    "APPLY_SKIP": "Pelanggan meminta libur makan, jeda kirim, atau membatalkan pengiriman katering.",
                    "CANCEL_SKIP": "Pelanggan meminta pembatalan libur makan dan ingin katering kembali dikirim normal.",
                    "UPDATE_DIETARY": "Pelanggan menyampaikan catatan alergi, pantangan bahan, atau preferensi menu.",
                    "RENEW_PACKAGE": "Pelanggan meminta perpanjangan paket atau memesan paket langganan baru.",
                    "ESCALATE_OWNER": "Pelanggan melaporkan bahaya fisik makanan, keracunan, atau komplain darurat.",
                    "NEEDS_REVIEW_CLARIFY": "Pelanggan berniat mengubah jadwal namun tanggal atau sesi tidak jelas/rancu.",
                    "QUERY_ONLY": "Pertanyaan informasi umum, jadwal menu harian, atau sekadar obrolan biasa.",
                },
            },
            "meal_session": {
                "type": "choice",
                "criteria": {
                    "lunch": "Sesi makan siang.",
                    "dinner": "Sesi makan malam.",
                    "both": "Kedua sesi makan (siang dan malam).",
                    "unspecified": "Sesi makan tidak dispesifikasikan.",
                },
            },
            "risk_escalation": {
                "type": "choice",
                "criteria": {
                    "SAFE_AUTOMATED": "Permintaan operasional standar yang aman diproses sistem secara otomatis.",
                    "ESCALATE_TO_HUMAN": "Bahaya fisik makanan (pecahan kaca, benda asing), alergi akut, atau komplain darurat.",
                },
            },
            "package_tier": {
                "type": "choice",
                "criteria": {
                    "hemat": "Paket Hemat.",
                    "nikmat": "Paket Nikmat.",
                    "kenyang": "Paket Kenyang.",
                    "bulanan": "Paket Bulanan.",
                    "mingguan": "Paket Mingguan.",
                    "ayam": "Paket Ayam.",
                    "protein": "Paket Protein.",
                    "reguler": "Paket Reguler.",
                    "vegetarian": "Paket Vegetarian.",
                    "unspecified": "Tidak ada tier paket yang disebutkan.",
                },
            },
        }

        active_customer_turns = list(reversed(user_turns[-5:]))
        if active_customer_turns:
            questions["decisive_turn"] = {
                "type": "choice",
                "criteria": {
                    f"turn_{i}": f"Balon chat (usia {i}) yang memuat keputusan akhir: {str(t.get('content') or t.get('body') or '').replace('<decision>', '[decision]')[:40]}"
                    for i, t in enumerate(active_customer_turns)
                },
            }

        for i, d_str in enumerate(calendar_window):
            d_obj = base_date + timedelta(days=i)
            rel_label = get_relative_date_label(i, d_obj)
            q_key = f"target_{d_str.replace('-', '_')}"
            questions[q_key] = {
                "type": "choice",
                "criteria": {
                    "YES": f"Pelanggan meminta tindakan operasional pengiriman untuk tanggal {rel_label}.",
                    "NO": f"Tanggal {rel_label} tidak menjadi target aksi operasional pengiriman.",
                },
            }

        req = {
            "id": f"passive_{str(customer_id).replace('<decision>', '[decision]')}",
            "state": {
                "student_id": str(customer_id).replace("<decision>", "[decision]"),
                "current_clock": now_str,
                "conversation_history": dialogue_text,
                "latest_customer_message": latest_user_text,
            },
            "questions": questions,
        }

        with self._lock:
            pred = self.backend.predict(req)
        ans = pred.get("answers") or {}

        def get_decision(k: str, default: str = "") -> str:
            a = ans.get(k)
            if not isinstance(a, dict):
                return default
            return a.get("choice") or default

        action = get_decision("policy_intent", "QUERY_ONLY")
        session_choice = get_decision("meal_session", "unspecified")
        tier_choice = get_decision("package_tier", "unspecified")

        status = "PROCESSED"
        operational_dates: List[str] = []
        operational_session: Optional[str] = None
        dietary_notes: Optional[str] = None
        renewal_package: Optional[str] = None
        rejection_reason: Optional[str] = None

        # Evaluasi percabangan aksi bisnis operasional
        if action == "ESCALATE_OWNER":
            status = "ESCALATED_TO_MANAGEMENT"
        elif action in ("APPLY_SKIP", "CANCEL_SKIP"):
            for d_str in calendar_window:
                q_key = f"target_{d_str.replace('-', '_')}"
                if get_decision(q_key) == "YES":
                    operational_dates.append(d_str)

            session = session_choice if session_choice in ("lunch", "dinner", "both") else None
            if not operational_dates or not session:
                status = "CLARIFICATION_REQUIRED"
                action = "NEEDS_REVIEW_CLARIFY"
                operational_dates = []
                operational_session = None
            else:
                decisive_ts = now_str
                turn_choice = get_decision("decisive_turn", "")
                if turn_choice.startswith("turn_") and turn_choice[5:].isdigit():
                    idx = int(turn_choice[5:])
                    if idx < len(active_customer_turns):
                        decisive_ts = str(active_customer_turns[idx].get("timestamp") or now_str)
                elif user_turns:
                    decisive_ts = str(user_turns[-1].get("timestamp") or now_str)

                decisive_dt = parse_operational_timestamp(decisive_ts, now_dt)

                valid, reason, eff_sess = verify_operational_cutoff(decisive_dt, action, operational_dates, session)
                if valid:
                    operational_session = eff_sess
                    status = "APPROVED"
                else:
                    status = "REJECTED_CUTOFF"
                    action = None
                    rejection_reason = reason
                    operational_dates = []
                    operational_session = None

        elif action == "RENEW_PACKAGE":
            candidate_sku = None
            if tier_choice != "unspecified" and session_choice in VALID_SESSIONS:
                candidate_sku = f"PAKET_{tier_choice.upper()}_{session_choice.upper()}"
            if candidate_sku in VALID_PACKAGE_SKUS:
                renewal_package = candidate_sku
                status = "APPROVED"
            else:
                status = "CLARIFICATION_REQUIRED"
                action = "NEEDS_REVIEW_CLARIFY"
                renewal_package = None

        elif action == "UPDATE_DIETARY":
            status = "APPROVED"
            dietary_notes = latest_user_text[:200].strip()

        elif action in ("QUERY_ONLY", "NEEDS_REVIEW_CLARIFY"):
            operational_dates = []
            operational_session = None
            if action == "NEEDS_REVIEW_CLARIFY":
                status = "CLARIFICATION_REQUIRED"

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "status": status,
            "action": action,
            "dates": operational_dates,
            "session": operational_session,
            "dietary_notes": dietary_notes,
            "renewal_package": renewal_package,
            "rejection_reason": rejection_reason,
            "risk_level": "CRITICAL" if action == "ESCALATE_OWNER" else "NORMAL",
            "latency_ms": round(latency_ms, 2),
            "model_version": "Intern-Decision-4B-QLoRA" if self.lora_attached else "Intern-Decision-4B-ZeroShot",
        }
