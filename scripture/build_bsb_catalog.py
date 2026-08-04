#!/usr/bin/env python3
"""Build DDB's curated BSB verse catalog from the verified official text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SOURCE_URL = "https://bereanbible.com/bsb.txt"
SOURCE_SHA256 = "2ac3af1de52d4e68261cba91d85c320b7eadc6560e830d99e591767b8ff5ca96"
LICENSE_URL = "https://berean.bible/licensing.htm"
VERIFIED_AT = "2026-08-03"

BOOK_CODES = {
    "Genesis": "GEN",
    "Exodus": "EXO",
    "Job": "JOB",
    "Psalm": "PSA",
    "Proverbs": "PRO",
    "Ecclesiastes": "ECC",
    "Isaiah": "ISA",
    "Jeremiah": "JER",
    "Amos": "AMO",
    "Micah": "MIC",
    "Zechariah": "ZEC",
    "Matthew": "MAT",
    "Luke": "LUK",
    "John": "JHN",
    "Acts": "ACT",
    "Romans": "ROM",
    "1 Corinthians": "1CO",
    "Galatians": "GAL",
    "Ephesians": "EPH",
    "Philippians": "PHP",
    "Colossians": "COL",
    "1 Thessalonians": "1TH",
    "1 Timothy": "1TI",
    "2 Timothy": "2TI",
    "Hebrews": "HEB",
    "James": "JAS",
    "1 Peter": "1PE",
    "1 John": "1JN",
    "3 John": "3JN",
}

# The catalog is intentionally restrained and topical. The morning editor chooses
# one identifier from this list; the renderer, never the editor, supplies the text.
CURATED = [
    ("Genesis 2:15", ("creation", "stewardship", "work")),
    ("Job 12:7", ("creation", "learning", "nature")),
    ("Psalm 19:1", ("creation", "science", "wonder")),
    ("Psalm 24:1", ("creation", "earth", "stewardship")),
    ("Psalm 34:18", ("comfort", "grief", "presence")),
    ("Psalm 37:5", ("plans", "trust", "uncertainty")),
    ("Psalm 46:1", ("crisis", "refuge", "strength")),
    ("Psalm 46:10", ("peace", "sovereignty", "stillness")),
    ("Psalm 56:3", ("courage", "fear", "trust")),
    ("Psalm 90:12", ("priorities", "time", "wisdom")),
    ("Psalm 104:24", ("creation", "nature", "wisdom")),
    ("Psalm 111:2", ("discovery", "research", "wonder")),
    ("Psalm 119:105", ("guidance", "path", "wisdom")),
    ("Psalm 121:2", ("creation", "help", "hope")),
    ("Proverbs 2:6", ("knowledge", "learning", "wisdom")),
    ("Proverbs 4:7", ("knowledge", "learning", "wisdom")),
    ("Proverbs 8:12", ("discernment", "knowledge", "prudence")),
    ("Proverbs 11:1", ("fairness", "honesty", "markets")),
    ("Proverbs 11:2", ("humility", "pride", "wisdom")),
    ("Proverbs 11:14", ("counsel", "leadership", "planning")),
    ("Proverbs 12:10", ("animals", "care", "stewardship")),
    ("Proverbs 12:22", ("honesty", "integrity", "truth")),
    ("Proverbs 14:15", ("discernment", "misinformation", "prudence")),
    ("Proverbs 14:31", ("justice", "poverty", "vulnerable")),
    ("Proverbs 15:1", ("conflict", "peace", "speech")),
    ("Proverbs 15:22", ("counsel", "planning", "wisdom")),
    ("Proverbs 16:3", ("plans", "purpose", "work")),
    ("Proverbs 16:11", ("fairness", "integrity", "markets")),
    ("Proverbs 17:17", ("adversity", "community", "friendship")),
    ("Proverbs 17:22", ("encouragement", "health", "hope")),
    ("Proverbs 17:28", ("discernment", "listening", "speech")),
    ("Proverbs 18:15", ("discernment", "knowledge", "learning")),
    ("Proverbs 19:20", ("advice", "learning", "wisdom")),
    ("Proverbs 21:3", ("justice", "morality", "righteousness")),
    ("Proverbs 22:9", ("generosity", "poverty", "provision")),
    ("Proverbs 22:29", ("excellence", "skill", "work")),
    ("Proverbs 27:17", ("collaboration", "community", "growth")),
    ("Proverbs 28:27", ("generosity", "poverty", "provision")),
    ("Ecclesiastes 3:11", ("change", "purpose", "timing")),
    ("Ecclesiastes 7:8", ("humility", "outcomes", "patience")),
    ("Isaiah 1:17", ("justice", "service", "vulnerable")),
    ("Isaiah 40:26", ("astronomy", "creation", "science")),
    ("Isaiah 41:10", ("comfort", "courage", "strength")),
    ("Jeremiah 17:14", ("health", "healing", "hope")),
    ("Amos 5:24", ("justice", "righteousness", "society")),
    ("Micah 6:8", ("humility", "justice", "mercy")),
    ("Matthew 5:9", ("conflict", "peace", "reconciliation")),
    ("Matthew 6:21", ("markets", "priorities", "wealth")),
    ("Matthew 6:34", ("anxiety", "present", "uncertainty")),
    ("Luke 12:15", ("greed", "markets", "wealth")),
    ("Luke 16:10", ("integrity", "responsibility", "stewardship")),
    ("John 8:32", ("freedom", "knowledge", "truth")),
    ("John 14:27", ("anxiety", "comfort", "peace")),
    ("Acts 17:11", ("discernment", "research", "truth")),
    ("Romans 8:28", ("adversity", "hope", "purpose")),
    ("Romans 12:3", ("humility", "judgment", "wisdom")),
    ("Romans 12:10", ("community", "honor", "love")),
    ("Romans 12:12", ("hope", "patience", "prayer")),
    ("Romans 12:15", ("empathy", "grief", "joy")),
    ("Romans 12:18", ("conflict", "peace", "reconciliation")),
    ("Romans 12:21", ("courage", "good", "morality")),
    ("Romans 15:13", ("hope", "joy", "peace")),
    ("1 Corinthians 10:31", ("purpose", "service", "work")),
    ("Galatians 5:13", ("freedom", "love", "service")),
    ("Galatians 6:9", ("perseverance", "service", "work")),
    ("Ephesians 2:10", ("purpose", "service", "work")),
    ("Ephesians 4:25", ("community", "honesty", "truth")),
    ("Philippians 2:4", ("community", "service", "selflessness")),
    ("Philippians 4:6", ("anxiety", "prayer", "thanksgiving")),
    ("Philippians 4:7", ("comfort", "peace", "understanding")),
    ("Philippians 4:13", ("courage", "perseverance", "strength")),
    ("1 Thessalonians 5:21", ("discernment", "testing", "truth")),
    ("1 Timothy 6:17", ("humility", "uncertainty", "wealth")),
    ("2 Timothy 1:7", ("courage", "love", "self-control")),
    ("Hebrews 10:24", ("encouragement", "love", "service")),
    ("Hebrews 13:5", ("contentment", "provision", "wealth")),
    ("James 1:5", ("prayer", "understanding", "wisdom")),
    ("James 3:17", ("peace", "reason", "wisdom")),
    ("1 Peter 5:7", ("anxiety", "care", "comfort")),
    ("1 John 3:18", ("action", "love", "service")),
    ("3 John 1:2", ("health", "prayer", "wellbeing")),
]


def parse_source(path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(
            f"source SHA256 {digest} does not match verified {SOURCE_SHA256}"
        )

    rows: dict[str, str] = {}
    for line in raw.decode("utf-8-sig").splitlines():
        if "\t" not in line:
            continue
        reference, text = line.split("\t", 1)
        if re.fullmatch(r".+ \d+:\d+", reference):
            rows[reference] = text
    return rows


def build_catalog(source: Path) -> dict:
    official = parse_source(source)
    verses = []
    seen_ids: set[str] = set()
    for reference, themes in CURATED:
        match = re.fullmatch(r"(.+?) (\d+):(\d+)", reference)
        if match is None:
            raise SystemExit(f"invalid curated reference: {reference}")
        book, chapter, verse = match.groups()
        if book not in BOOK_CODES:
            raise SystemExit(f"missing Bible.com code for {book}")
        text = official.get(reference)
        if not text:
            raise SystemExit(f"reference missing from official source: {reference}")
        if "—" in text:
            raise SystemExit(
                f"{reference} contains an em dash and cannot satisfy DDB house style"
            )
        verse_id = f"{BOOK_CODES[book]}.{chapter}.{verse}"
        if verse_id in seen_ids:
            raise SystemExit(f"duplicate verse identifier: {verse_id}")
        seen_ids.add(verse_id)
        verses.append(
            {
                "id": verse_id,
                "reference": reference,
                "text": text,
                "url": f"https://www.bible.com/bible/3034/{verse_id}.BSB",
                "themes": list(themes),
            }
        )

    return {
        "version": 1,
        "translation": {
            "name": "Berean Standard Bible",
            "label": "BSB",
            "sourceUrl": SOURCE_URL,
            "sourceSha256": SOURCE_SHA256,
            "license": "Public domain",
            "licenseUrl": LICENSE_URL,
            "verifiedAt": VERIFIED_AT,
        },
        "verses": verses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    catalog = build_catalog(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(catalog['verses'])} verified BSB verses to {args.output}")


if __name__ == "__main__":
    main()
