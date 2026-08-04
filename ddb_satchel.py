#!/usr/bin/env python3
"""DDB satchel helpers for reviewed house material and frozen legacy records.

Subsumes satchel-steward's draw/bookkeeping logic for bake time (selecting
and marking used). Weekly restock of kings-satchel.json back up to 16 unused
letters is a separate, larger job (satchel-steward proper, APR-005 sec 4) and
is NOT done here.

Network reader intake and the legacy all-in-one reader renderer are disabled
while the founder pause is active. The current session renderer may select only
reviewed house letters from `kings-satchel.json`. CSV parsing functions remain
solely for deterministic migration and historical tests; no production path
fetches or publishes those rows.

Columns (confirmed against the real export 2026-07-10): Timestamp, Slip type
("Question for the Baker" | "Pin for the Crumb Board"), The slip, Signed.

House style (BRAND.md, imperative): no em dashes anywhere in output. Ask the
Baker answers: factual, one bread/baking analogy. Letters to the King: King
David persona, poetic/warm/biblical register, factually sound. Crumb Board:
light copyedit only, never change meaning or voice.
"""
from __future__ import annotations

import csv
import json
import os
import random
import re
import subprocess
from datetime import datetime
from pathlib import Path

TIMESTAMP_COL, TYPE_COL, TEXT_COL, NAME_COL = 0, 1, 2, 3

TYPE_QUESTION = "Question for the Baker"   # covers BOTH Ask the Baker and Letters to the King
TYPE_PIN = "Pin for the Crumb Board"
KING_PREFIX = "[For King David] "

CLAUDE_BIN = os.environ.get("DDB_CLAUDE_BIN", "claude")
MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_OPUS = "claude-opus-4-8"

EM_DASH_RE = re.compile(r"\s*(?:—|&mdash;|&#0*8212;|&#x0*2014;)\s*", re.IGNORECASE)


def strip_em_dashes(text: str) -> str:
    """Mechanical safety net; copyedit/generation prompts are also told not to use them."""
    return EM_DASH_RE.sub(", ", text)


def fetch_csv(*_args, **_kwargs) -> bool:
    """Fail closed if retired code attempts network reader ingestion."""
    raise RuntimeError("reader intake is paused; Counter network ingestion is disabled")


# ---------------------------------------------------------------------------
# CSV loading and classification
# ---------------------------------------------------------------------------

def load_csv_rows(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for r in reader:
            if len(r) <= max(TIMESTAMP_COL, TYPE_COL, TEXT_COL, NAME_COL):
                continue
            rows.append({
                "timestamp": r[TIMESTAMP_COL].strip(),
                "type": r[TYPE_COL].strip(),
                "text": r[TEXT_COL].strip(),
                "name": (r[NAME_COL].strip() or "Anonymous"),
            })
    return rows


def dedup_key(row: dict) -> str:
    return f"{row['timestamp']}|{row['text'][:40]}"


def classify(rows: list[dict]) -> dict[str, list[dict]]:
    asks, king_letters, pins = [], [], []
    for row in rows:
        if row["type"] == TYPE_QUESTION:
            if row["text"].startswith(KING_PREFIX):
                king_letters.append(row)
            else:
                asks.append(row)
        elif row["type"] == TYPE_PIN:
            pins.append(row)
    return {"asks": asks, "king_letters": king_letters, "pins": pins}


def pick_oldest_unused(rows: list[dict], used_keys: set[str]) -> dict | None:
    candidates = [r for r in rows if dedup_key(r) not in used_keys]
    if not candidates:
        return None

    def parse_timestamp(value: str) -> datetime:
        formats = (
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y %I:%M:%S %p",
            "%m/%d/%Y %I:%M %p",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        )
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"unsupported Counter timestamp: {value!r}")

    # ``min`` is stable through the CSV index when timestamps tie.
    return min(
        enumerate(candidates),
        key=lambda indexed: (parse_timestamp(indexed[1]["timestamp"]), indexed[0]),
    )[1]


# ---------------------------------------------------------------------------
# Satchel (house letters) draw
# ---------------------------------------------------------------------------

def load_satchel(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("letters", [])


def pick_satchel_letter(letters: list[dict], used_ids: set[str]) -> dict | None:
    """Random draw among unused entries — matches the observed Mac behavior
    (used ids KS-006 then KS-015: non-sequential, not lowest-id-first)."""
    unused = [l for l in letters if l["id"] not in used_ids]
    if not unused:
        return None
    return random.choice(unused)


# ---------------------------------------------------------------------------
# Model calls (Haiku copyedit, Opus persona replies) — matches APR-005 sec 3
# ---------------------------------------------------------------------------

def call_claude(prompt: str, model: str, timeout: int = 120) -> str:
    out = subprocess.run(
        [CLAUDE_BIN, "-p", prompt, "--model", model],
        capture_output=True, text=True, timeout=timeout, check=True,
    )
    return out.stdout.strip()


def copyedit_pin(text: str, name: str) -> tuple[str, str]:
    prompt = (
        "House style for davidsdailybread.com's Crumb Board (a corkboard of reader "
        "notes). Lightly copyedit ONLY obvious spelling/typo errors in the note below. "
        "Never change meaning, voice, or wording beyond the correction; when in doubt, "
        "print as written. Never use an em dash character anywhere in the output. "
        "Return ONLY the corrected note text, nothing else.\n\n"
        f"Note: {text}"
    )
    edited = call_claude(prompt, MODEL_HAIKU)
    return strip_em_dashes(edited), strip_em_dashes(name)


def generate_baker_reply(question: str) -> str:
    prompt = (
        "You are 'the Baker' persona for davidsdailybread.com, answering a reader "
        "question in the 'Ask the Baker' section. Voice: factual, warm, exactly one "
        "bread/baking analogy in the answer. Never use an em dash character anywhere "
        "in the output; use a comma, colon, semicolon, period, parentheses, or an en "
        "dash instead. Keep it to 2-4 sentences. Return ONLY the answer text.\n\n"
        f"Reader question: {question}"
    )
    return strip_em_dashes(call_claude(prompt, MODEL_OPUS))


def generate_king_reply(letter: str) -> str:
    prompt = (
        "You are writing as the historical King David for davidsdailybread.com's "
        "'Letters to the King' section, replying to a letter addressed to him. Voice: "
        "poetic, warm, biblical register with a wink; factually sound beneath the "
        "poetry. Never use an em dash character anywhere in the output; use a comma, "
        "colon, semicolon, period, parentheses, or an en dash instead. Keep it to "
        "3-6 sentences. Return ONLY the reply text, no signature line (the signature "
        "is appended separately).\n\n"
        f"Letter: {letter}"
    )
    return strip_em_dashes(call_claude(prompt, MODEL_OPUS))


# ---------------------------------------------------------------------------
# Orchestration: fill all three sections for one bake
# ---------------------------------------------------------------------------

def fill_reader_sections(site_dir: Path, csv_path: Path, write_state: bool = True) -> dict[str, str]:
    """Retired all-in-one reader renderer, retained only to fail closed."""
    raise RuntimeError(
        "reader intake is paused; legacy Counter rendering is disabled"
    )
