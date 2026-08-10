#!/usr/bin/env python3
"""Classify a Claude CLI failure without emitting its raw output."""

from __future__ import annotations

from pathlib import Path
import re
import sys


MAX_INPUT_BYTES = 256 * 1024

SIGNATURES = (
    (
        "authentication",
        (
            r"\bauthentication_error\b",
            r"\binvalid (?:api key|x-api-key|oauth token)\b",
            r"\boauth token (?:has )?expired\b",
            r"\bnot logged in\b",
            r"\bunauthorized\b",
            r"\b(?:http(?: status)?|status code)\s*[:=]?\s*401\b",
        ),
    ),
    (
        "billing_or_quota",
        (
            r"\bbilling_error\b",
            r"\binsufficient (?:credits?|balance)\b",
            r"\bcredit balance\b",
            r"\b(?:spending|usage) limit\b",
            r"\bquota (?:has been )?(?:exceeded|exhausted)\b",
            r"\b(?:http(?: status)?|status code)\s*[:=]?\s*402\b",
        ),
    ),
    (
        "rate_limit",
        (
            r"\brate_limit_error\b",
            r"\brate limit(?:ed| exceeded)?\b",
            r"\btoo many requests\b",
            r"\b(?:http(?: status)?|status code)\s*[:=]?\s*429\b",
        ),
    ),
    (
        "authorization_or_model_access",
        (
            r"\bpermission_error\b",
            r"\bmodel_not_found\b",
            r"\bmodel\b.{0,80}\b(?:not found|not available|no access)\b",
            r"\b(?:do not|don't) have access\b.{0,80}\bmodel\b",
            r"\bforbidden\b",
            r"\b(?:http(?: status)?|status code)\s*[:=]?\s*403\b",
        ),
    ),
    (
        "request_rejected",
        (
            r"\binvalid_request_error\b",
            r"\bprompt (?:is )?too long\b",
            r"\bcontext (?:window|length)\b.{0,80}\b(?:exceed|maximum|too long)\b",
            r"\brequest (?:is )?too large\b",
            r"\busage policy\b",
        ),
    ),
    (
        "provider_unavailable",
        (
            r"\boverloaded_error\b",
            r"\bapi_error\b",
            r"\binternal server error\b",
            r"\bservice (?:is )?(?:temporarily )?unavailable\b",
            r"\boverloaded\b",
            r"\b(?:http(?: status)?|status code)\s*[:=]?\s*50[0234]\b",
        ),
    ),
    (
        "network",
        (
            r"\b(?:eai_again|enotfound|econnrefused|econnreset|etimedout)\b",
            r"\bsocket hang up\b",
            r"\bnetwork error\b",
            r"\bunable to (?:connect|resolve host)\b",
            r"\btls handshake\b",
        ),
    ),
    (
        "cli_configuration",
        (
            r"\bunknown (?:argument|option)\b",
            r"\binvalid (?:argument|option)\b",
            r"\bcommand not found\b",
            r"\bno such file or directory\b",
        ),
    ),
)


def classify_text(raw: str) -> str:
    """Return one controlled category and never include input text."""
    normalized = raw.casefold()
    for category, patterns in SIGNATURES:
        if any(re.search(pattern, normalized, flags=re.DOTALL) for pattern in patterns):
            return category
    return "unknown"


def classify_file(path: Path) -> str:
    """Read only the bounded tail where CLI errors are normally reported."""
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - MAX_INPUT_BYTES))
            raw = handle.read(MAX_INPUT_BYTES)
    except OSError:
        return "classifier_error"
    return classify_text(raw.decode("utf-8", errors="replace"))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stdout.write("classifier_error\n")
        return 0
    sys.stdout.write(classify_file(Path(argv[1])) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
