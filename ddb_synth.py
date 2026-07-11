#!/usr/bin/env python3
"""DDB synth — the actual editorial content for a bake: front-page/lead
selection + body, per-story deks (bolded lead-in), per-section "at a
glance" roundups. This is the part of the pipeline that was never in the
repo before 2026-07-10 — it lived only as a Cowork task prompt on the Mac.
This is an independent reconstruction from BRAND.md's house style and
observed real output, NOT a copy of the Mac's exact prompt (not available
at build time). Revisit if the original prompt turns up later.

Contract (ddb_bake.py's docstring, unchanged): every fact traces back to
its source link, no hallucination. So every synthesis call here is
grounded in the actual fetched article text where available; when a fetch
fails, the prompt is told to stay conservative (headline-only, no invented
specifics) rather than make something up.

Model routing (APR-005 sec 3):
  - Crumb Board slips (draw + copyedit)         -> Haiku  (ddb_satchel.py)
  - Per-story deks, "at a glance" roundups       -> Sonnet
  - Front-page/lead selection + lead body        -> Opus
  - Ask the Baker / Letters to the King replies  -> Opus  (ddb_satchel.py)
"""
from __future__ import annotations

import os
import re
import subprocess
import urllib.request

CLAUDE_BIN = os.environ.get("DDB_CLAUDE_BIN", "claude")
MODEL_SONNET = "claude-sonnet-5"
MODEL_OPUS = "claude-opus-4-8"

EM_DASH_CHARS = ("—", "&mdash;")


def strip_em_dashes(text: str) -> str:
    out = text
    for ch in EM_DASH_CHARS:
        out = out.replace(ch, ", ")
    return out


def fetch_article_text(url: str, timeout: int = 12, max_chars: int = 6000) -> str | None:
    """Best-effort plain-text extraction of a source article. Returns None
    on any failure (paywall, block, timeout, non-HTML) — callers must
    treat None as 'write conservatively from the headline alone', never as
    license to invent details."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; ddb-bake/1.0; +https://davidsdailybread.com)"
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "text" not in ctype:
                return None
            raw = resp.read(2_000_000).decode("utf-8", errors="replace")
    except Exception:
        return None
    text = re.sub(r"(?is)<(script|style|nav|header|footer|noscript).*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 200:
        return None
    return text[:max_chars]


def call_claude(prompt: str, model: str, timeout: int = 120) -> str:
    out = subprocess.run(
        [CLAUDE_BIN, "-p", prompt, "--model", model],
        capture_output=True, text=True, timeout=timeout, check=True,
    )
    return out.stdout.strip()


def _grounding_block(article_text: str | None) -> str:
    if article_text:
        return (
            "Source article text (grounds your writing — every specific fact, "
            f"number, or quote must come from here):\n{article_text}\n"
        )
    return (
        "No source article text was available to fetch (paywall/block/timeout). "
        "Write conservatively from the headline alone. Do NOT invent specific "
        "numbers, quotes, or details you don't actually have.\n"
    )


def synthesize_dek(title: str, url: str, source: str, article_text: str | None) -> str:
    """One card dek: '<b>Lead-in</b> rest of the sentence.' Matches the
    real site's format exactly (2 examples read directly from the live
    site)."""
    prompt = (
        "House style for davidsdailybread.com, a twice-daily news briefing. Write ONE "
        "sentence (occasionally two short ones) summarizing this story for a card dek. "
        "Format EXACTLY: start with 2-4 words in <b>bold</b> as a lead-in, then the rest "
        "of the sentence, ending in a period. Example format: "
        "'<b>OpenAI turned</b> its chatbot into a multi-step agent on Thursday, powered "
        "by the new model.' Straight factual news register, no bread metaphors (this is "
        "the journalism itself, not site chrome). Never use an em dash character; use a "
        "comma, colon, semicolon, period, or parentheses instead. Return ONLY the HTML "
        "sentence, nothing else — no preamble, no quotes around it.\n\n"
        f"Headline: {title}\nSource: {source}\n\n{_grounding_block(article_text)}"
    )
    return strip_em_dashes(call_claude(prompt, MODEL_SONNET))


def synthesize_glance(section_label: str, top_titles: list[str]) -> str:
    """One roundup sentence combining a section's top headlines, e.g.
    'OpenAI and Anthropic push agents into the office as Meta trims 8,000 jobs.'"""
    prompt = (
        "House style for davidsdailybread.com. Write ONE sentence (max ~20 words) that "
        f"rounds up today's top {section_label} headlines into a single 'at a glance' "
        "line, in the spirit of a newspaper deck. Straight factual news register, no "
        "bread metaphors. Never use an em dash; use a comma or semicolon instead. Return "
        "ONLY the sentence, no quotes, ending in a period.\n\n"
        + "\n".join(f"- {t}" for t in top_titles)
    )
    return strip_em_dashes(call_claude(prompt, MODEL_SONNET))


LEAD_BADGES = {"tech": "Technology", "markets": "Business & markets", "science": "Science"}
# Plain text — render_home HTML-escapes it once at render time. Storing the
# already-escaped "&amp;" here double-escapes to "&amp;amp;" (caught in testing).


def synthesize_lead(candidates: list[dict]) -> dict:
    """Front-page judgment across all sections: pick ONE lead story, write
    its badge/standfirst/body. candidates: [{section, title, url, source}]
    — a WIDE pool, titles only (no fetch yet — fetching every candidate's
    article just to throw most away is wasteful; a narrow pool also biases
    the pick toward whatever's simply first/most-recent per section rather
    than genuinely most newsworthy, which is what happened with a top-2
    pool on 2026-07-10 — it kept landing on routine NASA photo-of-the-day
    posts instead of the more substantive items further down the list).
    Only the winning candidate's article gets fetched, for the write step.
    Returns {section, title, url, badge, standfirst, body}."""
    listing = "\n".join(
        f"{i}. [{c['section']}] {c['title']} ({c['source']})" for i, c in enumerate(candidates)
    )
    pick_prompt = (
        "You are the final editor for davidsdailybread.com's twice-daily briefing, "
        "picking the single front-page lead story from today's candidates across "
        "technology, markets, and science. Judge genuine newsworthiness and impact, not "
        "just section order or recency — a routine status update or photo-of-the-day post "
        "should lose to a substantive story even if it's chronologically newer. Reply with "
        "ONLY the number of your pick, nothing else.\n\n"
        + listing
    )
    idx_raw = call_claude(pick_prompt, MODEL_OPUS)
    m = re.search(r"\d+", idx_raw)
    idx = int(m.group()) if m and int(m.group()) < len(candidates) else 0
    lead = dict(candidates[idx])
    lead["article_text"] = fetch_article_text(lead["url"])

    write_prompt = (
        "You are the final editor for davidsdailybread.com. Write the front-page lead "
        "for this story: (1) a one-sentence punchy editorial standfirst/subhead — sharp, "
        "not generic; (2) a 2-4 sentence body paragraph, real synthesized news writing "
        "with specific grounded facts. Straight factual news register, no bread "
        "metaphors. Never use an em dash. Return EXACTLY two lines: line 1 = "
        "'STANDFIRST: ...', line 2 = 'BODY: ...'. Nothing else.\n\n"
        f"Headline: {lead['title']}\nSource: {lead['source']}\n\n"
        + _grounding_block(lead.get("article_text"))
    )
    out = strip_em_dashes(call_claude(write_prompt, MODEL_OPUS))
    standfirst, body = "", ""
    for line in out.splitlines():
        if line.startswith("STANDFIRST:"):
            standfirst = line[len("STANDFIRST:"):].strip()
        elif line.startswith("BODY:"):
            body = line[len("BODY:"):].strip()
    return {
        "section": lead["section"], "title": lead["title"], "url": lead["url"],
        "badge": LEAD_BADGES.get(lead["section"], lead["section"].capitalize()),
        "standfirst": standfirst or lead["title"],
        "body": body or lead["title"],
    }
