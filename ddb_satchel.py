#!/usr/bin/env python3
"""DDB satchel — fills the three reader-content sections of a bake:
Ask the Baker (RQ*), Letters to the King (KQ*), The Crumb Board (PIN*).

Subsumes satchel-steward's draw/bookkeeping logic for bake time (selecting
and marking used). Weekly restock of kings-satchel.json back up to 16 unused
letters is a separate, larger job (satchel-steward proper, APR-005 sec 4) and
is NOT done here.

Reads:
  - bakery-state.json   (used-item dedup keys, from the git working tree)
  - kings-satchel.json  (house letters, fallback when no reader letter waits)
  - the Google Form response export (CSV) — see CSV_PATH / NOTE below

Writes:
  - bakery-state.json   (appends the newly-used dedup key)

Column assumption (UNVERIFIED — no real export seen yet): Timestamp, Type,
Text, Name in that order, matching the three form fields wired in
chronicles.html (entry.386221157=Type, entry.957805310=Text,
entry.891809667=Name). Verify against the real export before the first live
bake with real reader content; adjust the *_COL constants below if the
header order differs.

House style (BRAND.md, imperative): no em dashes anywhere in output. Ask the
Baker answers: factual, one bread/baking analogy. Letters to the King: King
David persona, poetic/warm/biblical register, factually sound. Crumb Board:
light copyedit only, never change meaning or voice.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

TIMESTAMP_COL, TYPE_COL, TEXT_COL, NAME_COL = 0, 1, 2, 3

TYPE_QUESTION = "Question for the Baker"   # covers BOTH Ask the Baker and Letters to the King
TYPE_PIN = "Pin for the Crumb Board"
KING_PREFIX = "[For King David] "

CLAUDE_BIN = os.environ.get("DDB_CLAUDE_BIN", "claude")
MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_OPUS = "claude-opus-4-8"

EM_DASH_CHARS = ("—", "&mdash;", "---", "--")


def strip_em_dashes(text: str) -> str:
    """Mechanical safety net; copyedit/generation prompts are also told not to use them."""
    out = text
    for ch in EM_DASH_CHARS:
        out = out.replace(ch, ", " if ch != "&mdash;" else ", ")
    return out


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

    def _sort_key(r):
        return r["timestamp"]  # ISO-ish / Google Forms default sorts correctly enough lexically for same-day; ties broken by CSV order otherwise
    return sorted(candidates, key=_sort_key)[0]


# ---------------------------------------------------------------------------
# Satchel (house letters) draw
# ---------------------------------------------------------------------------

def load_satchel(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("letters", [])


def pick_satchel_letter(letters: list[dict], used_ids: set[str]) -> dict | None:
    unused = [l for l in letters if l["id"] not in used_ids]
    if not unused:
        return None
    return sorted(unused, key=lambda l: l["id"])[0]


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
    """Returns the token->value dict for RQ1_*, KQ1_*, PIN1_* and updates
    bakery-state.json in place (site_dir) with newly-used dedup keys, unless
    write_state is False (dry runs must not mutate shared state)."""
    state_path = site_dir / "bakery-state.json"
    satchel_path = site_dir / "kings-satchel.json"

    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {
        "note": "", "answeredQuestions": [], "postedPins": [], "kingLetters": [], "usedSatchelLetters": []
    }

    rows = classify(load_csv_rows(csv_path))
    tokens: dict[str, str] = {}

    # --- Ask the Baker ---
    ask_used = set(state.get("answeredQuestions", []))
    ask_row = pick_oldest_unused(rows["asks"], ask_used)
    if ask_row:
        answer = generate_baker_reply(ask_row["text"])
        tokens["RQ1_Q"] = strip_em_dashes(ask_row["text"])
        tokens["RQ1_A"] = answer
        state.setdefault("answeredQuestions", []).append(dedup_key(ask_row))
    else:
        tokens["RQ1_Q"] = ""
        tokens["RQ1_A"] = ""

    # --- Letters to the King ---
    king_used = set(state.get("kingLetters", []))
    king_row = pick_oldest_unused(rows["king_letters"], king_used)
    if king_row:
        letter_text = king_row["text"][len(KING_PREFIX):].strip()
        reply = generate_king_reply(letter_text)
        tokens["KQ1_Q"] = strip_em_dashes(letter_text)
        tokens["KQ1_FROM"] = f"From {strip_em_dashes(king_row['name'])}"
        tokens["KQ1_A"] = reply
        state.setdefault("kingLetters", []).append(dedup_key(king_row))
    else:
        satchel_used = set(state.get("usedSatchelLetters", []))
        satchel_letters = load_satchel(satchel_path)
        drawn = pick_satchel_letter(satchel_letters, satchel_used)
        if drawn:
            reply = generate_king_reply(drawn["letter"])
            tokens["KQ1_Q"] = strip_em_dashes(drawn["letter"])
            tokens["KQ1_FROM"] = "From the Baker's own shelf"
            tokens["KQ1_A"] = reply
            state.setdefault("usedSatchelLetters", []).append(drawn["id"])
        else:
            # Satchel exhausted too — leave empty rather than publish placeholders.
            tokens["KQ1_Q"] = tokens["KQ1_FROM"] = tokens["KQ1_A"] = ""

    # --- The Crumb Board ---
    pin_used = set(state.get("postedPins", []))
    pin_row = pick_oldest_unused(rows["pins"], pin_used)
    if pin_row:
        text, name = copyedit_pin(pin_row["text"], pin_row["name"])
        tokens["PIN1_TEXT"] = text
        tokens["PIN1_SIG"] = f"– {name}"
        state.setdefault("postedPins", []).append(dedup_key(pin_row))
    else:
        tokens["PIN1_TEXT"] = ""
        tokens["PIN1_SIG"] = ""

    if write_state:
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return tokens
