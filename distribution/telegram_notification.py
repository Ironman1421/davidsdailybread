#!/usr/bin/env python3
"""Fail-closed Telegram receipt for one exact morning edition.

The notification is deliberately deterministic. It consumes the canonical
archive entry produced by the bake, sends one plain-text Telegram message, and
writes redacted attempt/receipt evidence. It never asks a model to select or
summarize an edition.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date as calendar_date, datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import secrets
import sys
from typing import Any, Callable, Mapping, Protocol
from urllib import error, parse, request


SITE_BASE = "https://davidsdailybread.com"
FORMAT_ID = "telegram-morning-receipt-v1"
EDITION_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-morning$")
CHAT_ID_RE = re.compile(r"^-?[1-9][0-9]{5,19}$")
BOT_TOKEN_RE = re.compile(r"^[0-9]{6,12}:[A-Za-z0-9_-]{30,}$")
TRUE_VALUES = {"1", "true", "yes", "on"}
class NotificationError(RuntimeError):
    """Base class for expected notification failures."""


class ValidationError(NotificationError):
    pass


class DuplicateError(NotificationError):
    pass


class PermanentProviderError(NotificationError):
    pass


class AmbiguousMutationError(NotificationError):
    """Telegram may have accepted the message, so retrying could duplicate it."""


class ReadbackError(NotificationError):
    pass


@dataclass(frozen=True)
class NotificationPackage:
    edition_id: str
    date: str
    slot: str
    lead: str
    canonical_url: str
    text: str
    format_id: str
    idempotency_key: str


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes


class Provider(Protocol):
    mutation_attempts: int

    def send_message(self, text: str) -> Mapping[str, Any]: ...


class UrlLibTransport:
    def request(
        self,
        url: str,
        *,
        body: bytes | None,
        headers: Mapping[str, str],
        timeout: float,
        method: str = "POST",
    ) -> HttpResponse:
        req = request.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return HttpResponse(response.status, response.read(65_537))
        except error.HTTPError as exc:
            return HttpResponse(exc.code, exc.read(65_537))
        except (TimeoutError, error.URLError, OSError) as exc:
            raise AmbiguousMutationError(
                "Telegram request ended without a definitive response"
            ) from exc


class TelegramProvider:
    def __init__(
        self,
        token: str,
        chat_id: str,
        *,
        transport: UrlLibTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not BOT_TOKEN_RE.fullmatch(token):
            raise ValidationError("Telegram bot token is missing or malformed")
        if not CHAT_ID_RE.fullmatch(chat_id):
            raise ValidationError("Telegram chat id is missing or malformed")
        self.token = token
        self.chat_id = chat_id
        self.transport = transport or UrlLibTransport()
        self.timeout = timeout
        self.mutation_attempts = 0

    def send_message(self, text: str) -> Mapping[str, Any]:
        self.mutation_attempts += 1
        body = parse.urlencode(
            {
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": "false",
            }
        ).encode("utf-8")
        try:
            response = self.transport.request(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                body=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )
        except (TimeoutError, error.URLError, OSError) as exc:
            raise AmbiguousMutationError(
                "Telegram request ended without a definitive response"
            ) from exc
        if response.status >= 500:
            raise AmbiguousMutationError(
                f"Telegram returned ambiguous HTTP status {response.status}"
            )
        if response.status != 200:
            raise PermanentProviderError(
                f"Telegram rejected the message with HTTP status {response.status}"
            )
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AmbiguousMutationError(
                "Telegram returned an unreadable success response"
            ) from exc
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            raise AmbiguousMutationError(
                "Telegram success response did not confirm the message"
            )
        result = payload.get("result")
        if not isinstance(result, dict):
            raise AmbiguousMutationError("Telegram response has no message result")
        return result


def _is_true(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return (value or "").strip().lower() in TRUE_VALUES


def _human_date(value: str) -> str:
    try:
        parsed = calendar_date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("notification date must be valid YYYY-MM-DD") from exc
    return f"{parsed.strftime('%A, %B')} {parsed.day}, {parsed.year}"


def _validate_lead(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValidationError("archive lead must be a non-empty trimmed string")
    if "\n" in value or "\r" in value:
        raise ValidationError("archive lead must be one line")
    if "\u2014" in value:
        raise ValidationError("archive lead contains a prohibited em dash")
    return value


def build_package(archive_path: Path, date: str, slot: str) -> NotificationPackage:
    edition_id = f"{date}-{slot}"
    if slot != "morning" or not EDITION_RE.fullmatch(edition_id):
        raise ValidationError("Telegram receipts are limited to an exact morning edition")
    try:
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read archive contract: {exc}") from exc
    editions = archive.get("editions")
    if not isinstance(editions, list):
        raise ValidationError("archive.json editions must be an array")
    expected_file = f"editions/{edition_id}.html"
    matches = [
        item
        for item in editions
        if isinstance(item, dict)
        and item.get("date") == date
        and item.get("edition") == slot
        and item.get("file") == expected_file
    ]
    if len(matches) != 1:
        raise ValidationError("archive must contain exactly one exact date/slot/file match")
    lead = _validate_lead(matches[0].get("lead"))
    canonical_url = f"{SITE_BASE}/{expected_file}"
    text = (
        f"\U0001f35e {_human_date(date)} morning edition is live\n\n"
        f"{lead}\n\nRead the full briefing: {canonical_url}"
    )
    if len(text) > 4096:
        raise ValidationError("Telegram notification exceeds the 4096-character limit")
    return NotificationPackage(
        edition_id=edition_id,
        date=date,
        slot=slot,
        lead=lead,
        canonical_url=canonical_url,
        text=text,
        format_id=FORMAT_ID,
        idempotency_key=f"ddb:telegram:morning-receipt:{edition_id}:v1",
    )


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _edition_order_key(edition_id: str) -> str:
    if not EDITION_RE.fullmatch(edition_id):
        raise ValidationError(f"invalid morning edition id: {edition_id}")
    return edition_id


def _iter_receipts(receipt_dir: Path) -> list[Mapping[str, Any]]:
    values: list[Mapping[str, Any]] = []
    if not receipt_dir.exists():
        return values
    for path in sorted(receipt_dir.rglob("*.json")):
        value = _read_json(path)
        if isinstance(value, dict):
            values.append(value)
    return values


def _receipt_path(receipt_dir: Path, package: NotificationPackage) -> Path:
    return receipt_dir / f"{package.edition_id}.json"


def _attempt_path(attempt_dir: Path, package: NotificationPackage) -> Path:
    return attempt_dir / f"{package.edition_id}-attempt.json"


def assert_not_duplicate(
    package: NotificationPackage,
    state_path: Path,
    receipt_dir: Path,
) -> None:
    state = _read_json(state_path)
    if not isinstance(state, dict) or state.get("version") != 1:
        raise ValidationError("notification state must be a version 1 object")
    cutover = state.get("cutoverAfterEditionId")
    if not isinstance(cutover, str):
        raise ValidationError("notification state must name cutoverAfterEditionId")
    if _edition_order_key(package.edition_id) <= _edition_order_key(cutover):
        raise DuplicateError(
            f"notification is blocked at or before cutover for {package.edition_id}"
        )
    receipts = state.get("receipts")
    if not isinstance(receipts, list):
        raise ValidationError("notification state receipts must be an array")
    cleared = state.get("clearedRemoteArtifactIds")
    if not isinstance(cleared, list):
        raise ValidationError("notification state clearedRemoteArtifactIds must be an array")
    candidates = list(receipts) + _iter_receipts(receipt_dir)
    if any(
        isinstance(item, dict) and item.get("editionId") == package.edition_id
        for item in candidates
    ):
        raise DuplicateError(f"notification already blocked for {package.edition_id}")


def write_reservation(
    package: NotificationPackage,
    *,
    state_path: Path,
    receipt_dir: Path,
    output_path: Path,
) -> None:
    assert_not_duplicate(package, state_path, receipt_dir)
    _write_json(
        output_path,
        {
            "editionId": package.edition_id,
            "formatId": package.format_id,
            "idempotencyKey": package.idempotency_key,
            "status": "reserved",
        },
    )


def _validate_reservation(path: Path, package: NotificationPackage) -> None:
    reservation = _read_json(path)
    expected = {
        "editionId": package.edition_id,
        "formatId": package.format_id,
        "idempotencyKey": package.idempotency_key,
        "status": "reserved",
    }
    if reservation != expected:
        raise ValidationError("durable reservation does not match the notification package")


def _github_api_json(
    url: str,
    token: str,
    *,
    transport: Any | None = None,
) -> Mapping[str, Any]:
    client = transport or UrlLibTransport()
    try:
        response = client.request(
            url,
            body=None,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ddb-telegram-receipt-hydrator/1",
            },
            timeout=10.0,
            method="GET",
        )
    except (TimeoutError, error.URLError, OSError) as exc:
        raise NotificationError(
            "GitHub receipt lookup failed before duplicate safety could be proven"
        ) from exc
    if response.status != 200:
        raise NotificationError(
            f"GitHub receipt lookup failed with HTTP {response.status}"
        )
    try:
        value = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NotificationError("GitHub receipt lookup returned malformed JSON") from exc
    if not isinstance(value, dict):
        raise NotificationError("GitHub receipt lookup returned a non-object")
    return value


def hydrate_github_receipt(
    *,
    repository: str,
    edition_id: str,
    token: str,
    state_path: Path,
    output_dir: Path,
    transport: Any | None = None,
) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValidationError("invalid GitHub repository name")
    if not token:
        raise ValidationError("GitHub token is missing")
    _edition_order_key(edition_id)
    state = _read_json(state_path)
    if not isinstance(state, dict) or not isinstance(
        state.get("clearedRemoteArtifactIds"), list
    ):
        raise ValidationError("notification state has no cleared artifact list")
    cleared = {str(value) for value in state["clearedRemoteArtifactIds"]}
    names = (
        f"telegram-notification-receipt-{edition_id}",
        f"telegram-notification-reservation-{edition_id}",
    )
    for name in names:
        query = parse.urlencode({"name": name, "per_page": 100})
        value = _github_api_json(
            f"https://api.github.com/repos/{repository}/actions/artifacts?{query}",
            token,
            transport=transport,
        )
        artifacts = value.get("artifacts")
        if not isinstance(artifacts, list):
            raise NotificationError("GitHub artifact lookup returned no artifact array")
        active = [
            item
            for item in artifacts
            if isinstance(item, dict)
            and item.get("name") == name
            and item.get("expired") is not True
            and str(item.get("id", ""))
            and str(item.get("id")) not in cleared
        ]
        if not active:
            continue
        active.sort(key=lambda item: int(item.get("id", 0)), reverse=True)
        selected = active[0]
        _write_json(
            output_dir / f"remote-{edition_id}.json",
            {
                "artifactId": str(selected["id"]),
                "artifactName": name,
                "editionId": edition_id,
                "source": "GitHub Actions receipt or reservation artifact metadata",
                "status": "remote_artifact",
                "version": 1,
                "workflowRunId": str(
                    (selected.get("workflow_run") or {}).get("id", "")
                ),
            },
        )
        return True
    return False


def _verify_result(
    result: Mapping[str, Any], package: NotificationPackage, expected_chat_id: str
) -> int:
    message_id = result.get("message_id")
    chat = result.get("chat")
    if not isinstance(message_id, int) or message_id <= 0:
        raise ReadbackError("Telegram response has no valid message id")
    if not isinstance(chat, dict) or str(chat.get("id")) != expected_chat_id:
        raise ReadbackError("Telegram response chat does not match the configured recipient")
    if result.get("text") != package.text:
        raise ReadbackError("Telegram response text does not match the exact package")
    return message_id


def execute_notification(
    package: NotificationPackage,
    *,
    state_path: Path,
    receipt_dir: Path,
    attempt_dir: Path,
    reservation_path: Path,
    enabled: bool,
    kill_switch: bool,
    dry_run: bool,
    expected_chat_id: str,
    provider_factory: Callable[[], Provider],
) -> str:
    attempt = {
        "editionId": package.edition_id,
        "formatId": package.format_id,
        "idempotencyKey": package.idempotency_key,
        "mutationAttempts": 0,
        "providerMessageId": None,
        "status": "starting",
    }
    attempt_path = _attempt_path(attempt_dir, package)

    if kill_switch:
        attempt["status"] = "skipped_kill_switch"
        _write_json(attempt_path, attempt)
        return str(attempt["status"])
    if dry_run:
        attempt["status"] = "dry_run"
        _write_json(attempt_path, attempt)
        return str(attempt["status"])
    if not enabled:
        attempt["status"] = "skipped_disabled"
        _write_json(attempt_path, attempt)
        return str(attempt["status"])

    assert_not_duplicate(package, state_path, receipt_dir)
    _validate_reservation(reservation_path, package)
    provider = provider_factory()
    try:
        result = provider.send_message(package.text)
        attempt["mutationAttempts"] = provider.mutation_attempts
        message_id = _verify_result(result, package, expected_chat_id)
    except (AmbiguousMutationError, ReadbackError) as exc:
        attempt["mutationAttempts"] = provider.mutation_attempts
        attempt["status"] = "needs_reconciliation"
        attempt["errorType"] = type(exc).__name__
        receipt = {
            "editionId": package.edition_id,
            "formatId": package.format_id,
            "idempotencyKey": package.idempotency_key,
            "providerMessageId": None,
            "sentAt": None,
            "status": "needs_reconciliation",
        }
        _write_json(_receipt_path(receipt_dir, package), receipt)
        _write_json(attempt_path, attempt)
        raise
    except NotificationError as exc:
        attempt["mutationAttempts"] = provider.mutation_attempts
        attempt["status"] = "failed"
        attempt["errorType"] = type(exc).__name__
        _write_json(attempt_path, attempt)
        raise

    sent_at = datetime.now(timezone.utc).isoformat()
    attempt["providerMessageId"] = message_id
    attempt["status"] = "sent"
    receipt = {
        "editionId": package.edition_id,
        "formatId": package.format_id,
        "idempotencyKey": package.idempotency_key,
        "providerMessageId": message_id,
        "sentAt": sent_at,
        "status": "sent",
    }
    _write_json(_receipt_path(receipt_dir, package), receipt)
    _write_json(attempt_path, attempt)
    return "sent"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    def package_args(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--archive", type=Path, required=True)
        subparser.add_argument("--date", required=True)
        subparser.add_argument("--slot", choices=["morning"], required=True)

    preview = subparsers.add_parser("preview")
    package_args(preview)

    reserve = subparsers.add_parser("reserve")
    package_args(reserve)
    reserve.add_argument(
        "--state", type=Path, default=Path("distribution/telegram-notification-state.json")
    )
    reserve.add_argument("--receipt-dir", type=Path, required=True)
    reserve.add_argument("--output", type=Path, required=True)

    hydrate = subparsers.add_parser("hydrate-github-receipt")
    hydrate.add_argument("--repository", required=True)
    hydrate.add_argument("--edition-id", required=True)
    hydrate.add_argument(
        "--state", type=Path, default=Path("distribution/telegram-notification-state.json")
    )
    hydrate.add_argument("--output-dir", type=Path, required=True)

    run = subparsers.add_parser("run")
    package_args(run)
    run.add_argument(
        "--state", type=Path, default=Path("distribution/telegram-notification-state.json")
    )
    run.add_argument("--receipt-dir", type=Path, required=True)
    run.add_argument("--attempt-dir", type=Path, required=True)
    run.add_argument("--reservation", type=Path, required=True)
    run.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "hydrate-github-receipt":
            found = hydrate_github_receipt(
                repository=args.repository,
                edition_id=args.edition_id,
                token=os.environ.get("GITHUB_TOKEN", ""),
                state_path=args.state,
                output_dir=args.output_dir,
            )
            print("found" if found else "not-found")
            return 0
        package = build_package(args.archive, args.date, args.slot)
        if args.command == "preview":
            print(json.dumps(asdict(package), indent=2, sort_keys=True))
            return 0
        if args.command == "reserve":
            write_reservation(
                package,
                state_path=args.state,
                receipt_dir=args.receipt_dir,
                output_path=args.output,
            )
            return 0
        enabled = _is_true(os.environ.get("DDB_TELEGRAM_NOTIFY_ENABLED"))
        kill_switch = not (
            os.environ.get("DDB_TELEGRAM_NOTIFY_KILL_SWITCH", "true").strip().lower()
            == "false"
        )
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        status = execute_notification(
            package,
            state_path=args.state,
            receipt_dir=args.receipt_dir,
            attempt_dir=args.attempt_dir,
            reservation_path=args.reservation,
            enabled=enabled,
            kill_switch=kill_switch,
            dry_run=args.dry_run,
            expected_chat_id=chat_id,
            provider_factory=lambda: TelegramProvider(token, chat_id),
        )
        logging.info("Telegram notification status=%s edition=%s", status, package.edition_id)
        return 0
    except NotificationError as exc:
        print(f"telegram notification failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
