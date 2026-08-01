#!/usr/bin/env python3
"""Fail-closed validation for files produced by one Daily bake run.

The active author process is untrusted.  This guard therefore permits only
worktree modifications to the standing files owned by the selected slot and
one new, untracked edition whose path exactly matches the requested date and
slot.  Staged changes, deletions, renames, and historical-edition edits fail.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass


DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
SLOTS = ("morning", "evening")

SLOT_STANDING_FILES = {
    "morning": {
        "index.html",
        "tech.html",
        "markets.html",
        "science.html",
        "archive.html",
        "archive.json",
        "feed.xml",
        "bakery-state.json",
        "kings-satchel.json",
    },
    "evening": {
        "index.html",
        "evening-catalog.json",
        "archive.html",
        "archive.json",
        "feed.xml",
    },
}


class GuardError(ValueError):
    """The bake changed a path or status outside its publish contract."""


@dataclass(frozen=True)
class Change:
    status: str
    path: str


def parse_porcelain_z(payload: bytes) -> list[Change]:
    """Parse the non-rename subset of ``git status --porcelain=v1 -z``.

    Rename and copy records are rejected before their extra path field could
    be interpreted.  Surrogate-escaped names cannot match the ASCII allowlist.
    """
    changes: list[Change] = []
    fields = payload.split(b"\0")
    for field in fields:
        if not field:
            continue
        text = field.decode("utf-8", errors="surrogateescape")
        if len(text) < 4 or text[2] != " ":
            raise GuardError("malformed or multi-path git status record")
        status, path = text[:2], text[3:]
        if "R" in status or "C" in status:
            raise GuardError(f"rename/copy status is forbidden: {status!r} {path}")
        changes.append(Change(status=status, path=path))
    return changes


def validate_changes(changes: list[Change], date: str, slot: str) -> list[str]:
    if DATE_RE.fullmatch(date) is None:
        raise GuardError(f"invalid edition date: {date!r}")
    if slot not in SLOTS:
        raise GuardError(f"invalid edition slot: {slot!r}")

    expected_edition = f"editions/{date}-{slot}.html"
    standing = SLOT_STANDING_FILES[slot]
    seen: set[str] = set()

    for change in changes:
        if change.path in seen:
            raise GuardError(f"duplicate changed path: {change.path}")
        seen.add(change.path)

        if change.path == expected_edition:
            if change.status != "??":
                raise GuardError(
                    f"edition must be one new untracked file, got "
                    f"{change.status!r}: {change.path}"
                )
            continue

        if change.path not in standing:
            raise GuardError(f"changed path not on {slot} allowlist: {change.path}")
        if change.status != " M":
            raise GuardError(
                f"standing file must be an unstaged modification, got "
                f"{change.status!r}: {change.path}"
            )

    if expected_edition not in seen:
        raise GuardError(f"expected new edition is missing: {expected_edition}")
    return sorted(seen)


def current_changes() -> list[Change]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return parse_porcelain_z(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", required=True)
    parser.add_argument("--slot", choices=SLOTS, required=True)
    args = parser.parse_args()
    try:
        paths = validate_changes(current_changes(), args.date, args.slot)
    except (GuardError, subprocess.CalledProcessError) as exc:
        print(f"BAKE GUARD FAIL: {exc}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
