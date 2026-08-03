#!/usr/bin/env python3
"""Verified morning Scripture catalog and deterministic HTML rendering."""

from __future__ import annotations

from functools import lru_cache
from html import escape
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "scripture" / "bsb-verses.json"
ALLOWED_SELECTION_KEYS = {"id", "connection"}
MAX_CONNECTION_CHARS = 240


class ScriptureError(ValueError):
    """Raised when the catalog or an editorial selection violates the contract."""


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScriptureError(f"cannot load verified BSB catalog: {exc}") from exc

    translation = catalog.get("translation") or {}
    if catalog.get("version") != 1:
        raise ScriptureError("verified BSB catalog version must be 1")
    if translation.get("name") != "Berean Standard Bible":
        raise ScriptureError("verified Scripture translation name must be Berean Standard Bible")
    if translation.get("label") != "BSB":
        raise ScriptureError("verified Scripture translation label must be BSB")
    if translation.get("license") != "Public domain":
        raise ScriptureError("verified BSB catalog must record its public-domain status")

    verses = catalog.get("verses")
    if not isinstance(verses, list) or not verses:
        raise ScriptureError("verified BSB catalog must contain verses")

    by_id: dict[str, dict] = {}
    for index, verse in enumerate(verses):
        if not isinstance(verse, dict):
            raise ScriptureError(f"verified BSB verse {index} must be an object")
        for key in ("id", "reference", "text", "url", "themes"):
            if key not in verse:
                raise ScriptureError(f"verified BSB verse {index} is missing {key}")
        verse_id = verse["id"]
        if not isinstance(verse_id, str) or not verse_id:
            raise ScriptureError(f"verified BSB verse {index} has an invalid identifier")
        if verse_id in by_id:
            raise ScriptureError(f"duplicate verified BSB identifier: {verse_id}")
        if not isinstance(verse["reference"], str) or not verse["reference"].strip():
            raise ScriptureError(f"verified BSB verse {verse_id} has an invalid reference")
        if not isinstance(verse["text"], str) or not verse["text"].strip():
            raise ScriptureError(f"verified BSB verse {verse_id} has invalid text")
        if "—" in verse["text"]:
            raise ScriptureError(f"verified BSB verse {verse_id} contains a prohibited em dash")
        if not isinstance(verse["url"], str) or not verse["url"].startswith(
            "https://www.bible.com/bible/3034/"
        ):
            raise ScriptureError(f"verified BSB verse {verse_id} has an invalid Bible link")
        if not isinstance(verse["themes"], list) or not all(
            isinstance(theme, str) and theme.strip() for theme in verse["themes"]
        ):
            raise ScriptureError(f"verified BSB verse {verse_id} has invalid themes")
        by_id[verse_id] = verse

    return {**catalog, "byId": by_id}


def validate_selection(value: object) -> tuple[dict, str]:
    if not isinstance(value, dict):
        raise ScriptureError("lead.scripture must be an object")
    unexpected = set(value) - ALLOWED_SELECTION_KEYS
    if unexpected:
        raise ScriptureError(
            "lead.scripture may contain only id and connection; "
            f"unexpected keys: {sorted(unexpected)}"
        )

    verse_id = value.get("id")
    if not isinstance(verse_id, str) or not verse_id.strip():
        raise ScriptureError("lead.scripture.id must be a non-empty catalog identifier")
    verse = load_catalog()["byId"].get(verse_id)
    if verse is None:
        raise ScriptureError(f"lead.scripture.id is not in the verified BSB catalog: {verse_id}")

    connection = value.get("connection", "")
    if not isinstance(connection, str):
        raise ScriptureError("lead.scripture.connection must be a string when present")
    connection = connection.strip()
    if len(connection) > MAX_CONNECTION_CHARS:
        raise ScriptureError(
            f"lead.scripture.connection must be <= {MAX_CONNECTION_CHARS} characters"
        )
    if "\n" in connection or "\r" in connection:
        raise ScriptureError("lead.scripture.connection must be one brief paragraph")
    if "<" in connection or ">" in connection:
        raise ScriptureError("lead.scripture.connection must be plain text")
    return verse, connection


def search_catalog(query: str | None, limit: int = 12) -> dict:
    catalog = load_catalog()
    terms = [term.casefold() for term in (query or "").split() if term.strip()]
    ranked: list[tuple[int, int, dict]] = []
    for index, verse in enumerate(catalog["verses"]):
        haystack = " ".join(
            [verse["reference"], verse["text"], *verse["themes"]]
        ).casefold()
        score = sum(1 for term in terms if term in haystack)
        if not terms or score:
            ranked.append((-score, index, verse))
    ranked.sort(key=lambda item: (item[0], item[1]))
    matches = [
        {
            "id": verse["id"],
            "reference": verse["reference"],
            "text": verse["text"],
            "themes": verse["themes"],
        }
        for _, _, verse in ranked[:limit]
    ]
    return {
        "translation": "Berean Standard Bible",
        "label": "BSB",
        "query": query or None,
        "matches": matches,
    }


def render_pairing(selection: object, heading_id: str = "lead-scripture-label") -> str:
    verse, connection = validate_selection(selection)
    reference = verse["reference"]
    url = verse["url"]
    connection_html = (
        f'      <p class="scripture-connection">{escape(connection)}</p>\n'
        if connection
        else ""
    )
    return (
        f'    <section class="scripture-inline" aria-labelledby="{escape(heading_id)}">\n'
        f'      <h2 class="scripture-label" id="{escape(heading_id)}">Scripture for Reflection</h2>\n'
        f'      <blockquote cite="{escape(url, quote=True)}">\n'
        f'        <p class="verse-text">&ldquo;{escape(verse["text"])}&rdquo;</p>\n'
        f'        <footer><cite class="verse-reference"><a href="{escape(url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer" aria-label="Read {escape(reference, quote=True)} '
        f'in the Berean Standard Bible, opens in a new tab">{escape(reference)} &middot; BSB '
        f'<span class="external-mark" aria-hidden="true">&#8599;</span></a></cite></footer>\n'
        f'      </blockquote>\n'
        f'{connection_html}'
        f'    </section>'
    )
