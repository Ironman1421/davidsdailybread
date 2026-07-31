#!/usr/bin/env python3
"""Fail-closed canonical-edition broadcaster for X.

The module is deliberately standard-library only.  It consumes one exact
archive.json edition, applies the repository distribution contract, and talks
only to X API v2 with OAuth 1.0a user context.  It never handles replies.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import random
import re
import secrets
import sys
import time
from typing import Any, Callable, Mapping, Protocol
import unicodedata
from urllib import error, parse, request


API_BASE = "https://api.x.com"
SITE_BASE = "https://davidsdailybread.com"
FORMAT_ID = "x-canonical-v1"
MAX_WEIGHTED_LENGTH = 280
URL_WEIGHT = 23
EDITION_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(morning|evening)$")
HTTPS_URL_RE = re.compile(r"https://[^\s]+", re.IGNORECASE)
URL_LIKE_RE = re.compile(
    r"(?i)(?:\b[a-z][a-z0-9+.-]*://|\bwww\.|"
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\.)+"
    r"[a-z]{2,63}\b)"
)
SECRET_FIELD_RE = re.compile(
    r"(?i)(authorization|oauth_(?:consumer_key|token|signature))"
    r"\s*[:=]\s*([^\s,]+)"
)
X_ID_RE = re.compile(r"^[0-9]{1,19}$")
TRUE_VALUES = {"1", "true", "yes", "on"}
WEIGHT_ONE_RANGES = (
    (0, 4351),
    (8192, 8205),
    (8208, 8223),
    (8242, 8247),
)


class BroadcastError(RuntimeError):
    """Base class for expected adapter failures."""


class ValidationError(BroadcastError):
    pass


class DuplicateError(BroadcastError):
    pass


class ProviderError(BroadcastError):
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


class PermanentProviderError(ProviderError):
    pass


class RetryableProviderError(ProviderError):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message, status=status)
        self.retry_after = retry_after


class AmbiguousMutationError(ProviderError):
    """The create request may have reached X, so automatic retry is unsafe."""


class ReadbackError(BroadcastError):
    def __init__(self, message: str, *, provider_post_id: str | None = None):
        super().__init__(message)
        self.provider_post_id = provider_post_id


@dataclass(frozen=True)
class EditionPackage:
    edition_id: str
    date: str
    slot: str
    lead: str
    canonical_url: str
    text: str
    weighted_length: int
    format_id: str
    idempotency_key: str


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


class Provider(Protocol):
    mutation_attempts: int

    def verify_identity(self) -> Mapping[str, Any]: ...

    def find_existing_post(self, package: EditionPackage) -> Mapping[str, Any] | None: ...

    def create_post(self, text: str) -> Mapping[str, Any]: ...

    def read_post(self, post_id: str) -> Mapping[str, Any]: ...


class Redactor:
    def __init__(self, values: list[str] | tuple[str, ...] = ()) -> None:
        self.values = tuple(sorted({v for v in values if v}, key=len, reverse=True))

    def clean(self, value: object) -> str:
        text = str(value)
        for secret_value in self.values:
            text = text.replace(secret_value, "[REDACTED]")
        return SECRET_FIELD_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)


class UrlLibTransport:
    """Small injectable transport that caps response bodies."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HttpResponse:
        req = request.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return HttpResponse(
                    response.status,
                    dict(response.headers.items()),
                    response.read(65_537),
                )
        except error.HTTPError as exc:
            return HttpResponse(exc.code, dict(exc.headers.items()), exc.read(65_537))


def _is_true(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return (value or "").strip().lower() in TRUE_VALUES


def _weight_for_codepoint(codepoint: int) -> int:
    return 1 if any(start <= codepoint <= end for start, end in WEIGHT_ONE_RANGES) else 2


def x_weighted_length(text: str) -> int:
    """Return X's NFC/code-point weight with every HTTPS URL transformed to 23.

    Canonical broadcasts prohibit format controls and emoji-joiner characters,
    so the allowed input does not require twitter-text's emoji cluster parser.
    """

    normalized = unicodedata.normalize("NFC", text)
    total = 0
    cursor = 0
    for match in HTTPS_URL_RE.finditer(normalized):
        total += sum(_weight_for_codepoint(ord(ch)) for ch in normalized[cursor : match.start()])
        total += URL_WEIGHT
        cursor = match.end()
    total += sum(_weight_for_codepoint(ord(ch)) for ch in normalized[cursor:])
    return total


def _validate_lead(lead: object) -> str:
    if not isinstance(lead, str):
        raise ValidationError("archive lead must be a string")
    if not lead or lead != lead.strip():
        raise ValidationError("archive lead must be non-empty with no edge whitespace")
    if unicodedata.normalize("NFC", lead) != lead:
        raise ValidationError("archive lead must already be Unicode NFC")
    if len(lead) > 130:
        raise ValidationError("archive lead exceeds the 130-character product contract")
    if "\u2014" in lead:
        raise ValidationError("archive lead contains a prohibited em dash")
    if "@" in lead or "#" in lead:
        raise ValidationError("archive lead may not inject mentions or hashtags")
    if URL_LIKE_RE.search(lead):
        raise ValidationError("archive lead may not contain URL-like text")
    for char in lead:
        codepoint = ord(char)
        if (
            codepoint in {0x20E3, 0xFE0E, 0xFE0F}
            or 0x1F1E6 <= codepoint <= 0x1F1FF
            or 0x1F3FB <= codepoint <= 0x1F3FF
        ):
            raise ValidationError("archive lead contains a prohibited emoji joiner or modifier")
        category = unicodedata.category(char)
        if category in {"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"}:
            raise ValidationError("archive lead contains a prohibited Unicode character")
    return lead


def _edition_order_key(edition_id: str) -> tuple[str, int]:
    match = EDITION_RE.fullmatch(edition_id)
    if not match:
        raise ValidationError(f"invalid edition id: {edition_id}")
    return match.group(1), 0 if match.group(2) == "morning" else 1


def build_package(archive_path: Path, date: str, slot: str) -> EditionPackage:
    edition_id = f"{date}-{slot}"
    if not EDITION_RE.fullmatch(edition_id):
        raise ValidationError("date and slot do not form a valid edition id")
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
    label = "Morning edition" if slot == "morning" else "Evening edition"
    text = f"{label}: {lead}\n\nRead the full briefing: {canonical_url}"
    weighted_length = x_weighted_length(text)
    if weighted_length > MAX_WEIGHTED_LENGTH:
        raise ValidationError(
            f"canonical post weighs {weighted_length}, exceeding {MAX_WEIGHTED_LENGTH}"
        )
    return EditionPackage(
        edition_id=edition_id,
        date=date,
        slot=slot,
        lead=lead,
        canonical_url=canonical_url,
        text=text,
        weighted_length=weighted_length,
        format_id=FORMAT_ID,
        idempotency_key=f"ddb:x:canonical:{edition_id}:v1",
    )


def load_state(path: Path) -> Mapping[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read X broadcast state: {exc}") from exc
    if state.get("version") != 1:
        raise ValidationError("unsupported X broadcast state version")
    if not isinstance(state.get("receipts"), list) or not isinstance(
        state.get("clearedRemoteArtifactIds"), list
    ):
        raise ValidationError("malformed X broadcast state")
    return state


def _iter_receipt_objects(receipt_dir: Path) -> list[Mapping[str, Any]]:
    receipts: list[Mapping[str, Any]] = []
    if not receipt_dir.exists():
        return receipts
    for path in sorted(receipt_dir.rglob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"invalid receipt file {path.name}: {exc}") from exc
        if isinstance(value, dict):
            receipts.append(value)
    return receipts


def assert_not_duplicate(
    package: EditionPackage,
    state: Mapping[str, Any],
    receipt_dir: Path,
) -> None:
    cutover = state.get("cutoverAfterEditionId")
    if not isinstance(cutover, str):
        raise ValidationError("state must name cutoverAfterEditionId")
    if _edition_order_key(package.edition_id) <= _edition_order_key(cutover):
        raise DuplicateError(
            f"edition {package.edition_id} is at or before the automatic cutover watermark"
        )
    candidates = list(state["receipts"]) + _iter_receipt_objects(receipt_dir)
    for receipt in candidates:
        if receipt.get("editionId") == package.edition_id:
            raise DuplicateError(f"edition {package.edition_id} already has a blocking receipt")


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_json(response: HttpResponse, redactor: Redactor) -> Mapping[str, Any]:
    if len(response.body) > 65_536:
        raise ProviderError("provider response exceeded 64 KiB", status=response.status)
    try:
        value = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderError(
            redactor.clean(f"provider returned malformed JSON ({exc})"),
            status=response.status,
        ) from exc
    if not isinstance(value, dict):
        raise ProviderError("provider returned a non-object JSON response", status=response.status)
    return value


class OAuth1Signer:
    def __init__(self, api_key: str, api_secret: str, access_token: str, token_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.token_secret = token_secret

    @staticmethod
    def _quote(value: object) -> str:
        return parse.quote(str(value), safe="~-._")

    def authorization(self, method: str, url: str) -> str:
        oauth = {
            "oauth_consumer_key": self.api_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.access_token,
            "oauth_version": "1.0",
        }
        split = parse.urlsplit(url)
        query = parse.parse_qsl(split.query, keep_blank_values=True)
        parameters = query + list(oauth.items())
        normalized = "&".join(
            f"{self._quote(key)}={self._quote(value)}"
            for key, value in sorted(parameters, key=lambda item: (self._quote(item[0]), self._quote(item[1])))
        )
        base_url = parse.urlunsplit((split.scheme, split.netloc, split.path, "", ""))
        signature_base = "&".join(
            (method.upper(), self._quote(base_url), self._quote(normalized))
        )
        signing_key = f"{self._quote(self.api_secret)}&{self._quote(self.token_secret)}"
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), signature_base.encode(), hashlib.sha1).digest()
        ).decode()
        oauth["oauth_signature"] = signature
        fields = ", ".join(
            f'{self._quote(key)}="{self._quote(value)}"' for key, value in sorted(oauth.items())
        )
        return f"OAuth {fields}"


def _header(headers: Mapping[str, str], name: str) -> str | None:
    wanted = name.lower()
    return next((str(value) for key, value in headers.items() if key.lower() == wanted), None)


class XApiProvider:
    def __init__(
        self,
        *,
        signer: OAuth1Signer,
        expected_user_id: str,
        expected_username: str,
        transport: Any | None = None,
        timeout: float = 10.0,
        max_attempts: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
        redactor: Redactor | None = None,
    ) -> None:
        if not X_ID_RE.fullmatch(expected_user_id):
            raise ValidationError("X_EXPECTED_USER_ID must be a numeric X user id")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,15}", expected_username):
            raise ValidationError("X_EXPECTED_USERNAME is invalid")
        self.signer = signer
        self.expected_user_id = expected_user_id
        self.expected_username = expected_username
        self.transport = transport or UrlLibTransport()
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.sleeper = sleeper
        self.jitter = jitter
        self.redactor = redactor or Redactor()
        self.mutation_attempts = 0

    def _once(self, method: str, url: str, payload: Mapping[str, Any] | None) -> HttpResponse:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        headers = {
            "Accept": "application/json",
            "Authorization": self.signer.authorization(method, url),
            "User-Agent": "ddb-x-canonical-broadcast/1",
        }
        if body is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        try:
            return self.transport.request(
                method, url, headers=headers, body=body, timeout=self.timeout
            )
        except (TimeoutError, error.URLError, OSError) as exc:
            if method == "POST":
                raise AmbiguousMutationError(
                    self.redactor.clean(f"create request ended ambiguously: {exc}")
                ) from exc
            raise RetryableProviderError(
                self.redactor.clean(f"provider request failed transiently: {exc}")
            ) from exc

    def _request_json(
        self,
        method: str,
        url: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        for attempt in range(1, self.max_attempts + 1):
            if method == "POST":
                self.mutation_attempts += 1
            try:
                response = self._once(method, url, payload)
            except RetryableProviderError:
                if method != "GET" or attempt >= self.max_attempts:
                    raise
                self.sleeper(
                    min(8.0, 0.75 * (2 ** (attempt - 1)))
                    + self.jitter() * 0.25
                )
                continue
            if 200 <= response.status < 300:
                try:
                    return _safe_json(response, self.redactor)
                except ProviderError as exc:
                    if method == "POST":
                        raise AmbiguousMutationError(
                            self.redactor.clean(
                                f"create response was successful but unusable: {exc}"
                            ),
                            status=response.status,
                        ) from exc
                    raise
            summary = self.redactor.clean(
                f"X API HTTP {response.status}: {response.body[:512].decode('utf-8', 'replace')}"
            )
            if response.status in (401, 403):
                raise PermanentProviderError(summary, status=response.status)
            if response.status == 429:
                if attempt >= self.max_attempts:
                    raise RetryableProviderError(summary, status=429)
                reset = _header(response.headers, "x-rate-limit-reset")
                reset_wait = 0.0
                if reset and reset.isdigit():
                    reset_wait = max(0.0, float(reset) - time.time())
                delay = max(reset_wait, min(8.0, 0.75 * (2 ** (attempt - 1))))
                if delay > 30.0:
                    raise RetryableProviderError(
                        "X API rate-limit reset exceeds the 30-second retry budget",
                        status=429,
                        retry_after=delay,
                    )
                self.sleeper(delay + self.jitter() * 0.25)
                continue
            if 500 <= response.status <= 599:
                if method == "POST":
                    raise AmbiguousMutationError(summary, status=response.status)
                if attempt < self.max_attempts:
                    self.sleeper(min(8.0, 0.75 * (2 ** (attempt - 1))) + self.jitter() * 0.25)
                    continue
                raise RetryableProviderError(summary, status=response.status)
            raise PermanentProviderError(summary, status=response.status)
        raise AssertionError("retry loop exhausted unexpectedly")

    def verify_identity(self) -> Mapping[str, Any]:
        value = self._request_json("GET", f"{API_BASE}/2/users/me")
        data = value.get("data")
        if not isinstance(data, dict):
            raise PermanentProviderError("X identity response has no data object")
        if data.get("id") != self.expected_user_id or str(data.get("username", "")).lower() != self.expected_username.lower():
            raise PermanentProviderError("X credential identity does not match the configured account")
        return data

    def create_post(self, text: str) -> Mapping[str, Any]:
        value = self._request_json("POST", f"{API_BASE}/2/tweets", {"text": text})
        data = value.get("data")
        if not isinstance(data, dict) or not X_ID_RE.fullmatch(str(data.get("id", ""))):
            raise ReadbackError("X create response has no valid post id")
        return data

    def find_existing_post(self, package: EditionPackage) -> Mapping[str, Any] | None:
        query = parse.urlencode(
            {
                "max_results": 100,
                "exclude": "replies,retweets",
                "tweet.fields": "author_id,created_at,entities",
            }
        )
        value = self._request_json(
            "GET", f"{API_BASE}/2/users/{self.expected_user_id}/tweets?{query}"
        )
        data = value.get("data", [])
        if data is None:
            return None
        if not isinstance(data, list):
            raise ProviderError("X user-posts response has a non-array data field")
        for item in data:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if (
                item.get("author_id") == self.expected_user_id
                and isinstance(text, str)
                and _url_shape(text) == _url_shape(package.text)
                and _expanded_urls(item) == [package.canonical_url]
            ):
                return item
        return None

    def read_post(self, post_id: str) -> Mapping[str, Any]:
        query = parse.urlencode({"tweet.fields": "author_id,created_at,entities"})
        value = self._request_json("GET", f"{API_BASE}/2/tweets/{post_id}?{query}")
        data = value.get("data")
        if not isinstance(data, dict):
            raise ReadbackError("X read-back response has no data object", provider_post_id=post_id)
        return data


def _urls_in(text: str) -> list[str]:
    return [match.group(0) for match in HTTPS_URL_RE.finditer(text)]


def _url_shape(text: str) -> str:
    return HTTPS_URL_RE.sub("<URL>", unicodedata.normalize("NFC", text))


def _expanded_urls(post: Mapping[str, Any]) -> list[str]:
    entities = post.get("entities")
    urls = entities.get("urls") if isinstance(entities, dict) else None
    expanded = []
    if isinstance(urls, list):
        for item in urls:
            if isinstance(item, dict):
                value = item.get("unwound_url") or item.get("expanded_url")
                if isinstance(value, str):
                    expanded.append(value)
    return expanded


def verify_readback(
    package: EditionPackage,
    created: Mapping[str, Any],
    readback: Mapping[str, Any],
    expected_user_id: str,
) -> str:
    post_id = str(created.get("id", ""))
    if not X_ID_RE.fullmatch(post_id) or str(readback.get("id", "")) != post_id:
        raise ReadbackError("provider post id changed during read-back", provider_post_id=post_id or None)
    if readback.get("author_id") != expected_user_id:
        raise ReadbackError("read-back author does not match configured account", provider_post_id=post_id)
    created_text = created.get("text")
    actual_text = readback.get("text")
    if not isinstance(created_text, str) or _url_shape(created_text) != _url_shape(package.text):
        raise ReadbackError("create response text does not match canonical package", provider_post_id=post_id)
    if not isinstance(actual_text, str) or _url_shape(actual_text) != _url_shape(package.text):
        raise ReadbackError("read-back text does not match canonical package", provider_post_id=post_id)
    if len(_urls_in(actual_text)) != 1:
        raise ReadbackError("read-back must contain exactly one provider URL", provider_post_id=post_id)
    expanded = _expanded_urls(readback)
    if expanded != [package.canonical_url]:
        raise ReadbackError("read-back URL does not expand to the canonical edition", provider_post_id=post_id)
    published_at = readback.get("created_at")
    if not isinstance(published_at, str) or not published_at:
        raise ReadbackError("read-back has no provider publication time", provider_post_id=post_id)
    return published_at


def _base_attempt(package: EditionPackage) -> dict[str, Any]:
    return {
        "version": 1,
        "editionId": package.edition_id,
        "idempotencyKey": package.idempotency_key,
        "canonicalUrl": package.canonical_url,
        "formatId": package.format_id,
        "startedAt": _utc_now(),
        "finishedAt": None,
        "status": "started",
        "mutationAttempts": 0,
        "errorClass": None,
        "error": None,
    }


def _blocking_receipt(
    package: EditionPackage,
    *,
    status: str,
    provider_post_id: str | None,
    reason: str | None,
    published_at: str | None = None,
    expected_username: str,
    automated: bool | None = True,
) -> dict[str, Any]:
    return {
        "version": 1,
        "status": status,
        "editionId": package.edition_id,
        "canonicalUrl": package.canonical_url,
        "lead": package.lead,
        "postText": package.text,
        "platform": "x",
        "platformPostId": provider_post_id,
        "platformPostUrl": (
            f"https://x.com/{expected_username}/status/{provider_post_id}"
            if provider_post_id
            else None
        ),
        "formatId": package.format_id,
        "idempotencyKey": package.idempotency_key,
        "hookVariant": None,
        "voiceMode": "caption_only",
        "automated": automated,
        "publishedAt": published_at,
        "recordedAt": _utc_now(),
        "operator": "github-actions:x-canonical-broadcast",
        "rightsManifest": None,
        "spendUsd": 0,
        "metrics24h": None,
        "metrics7d": None,
        "readBackVerified": status in {"published", "existing_provider_post"},
        "reconciliationReason": reason,
    }


def write_durable_reservation(
    package: EditionPackage,
    *,
    state_path: Path,
    receipt_dir: Path,
    output_path: Path,
) -> None:
    state = load_state(state_path)
    assert_not_duplicate(package, state, receipt_dir)
    _atomic_write_json(
        output_path,
        {
            "version": 1,
            "status": "reserved_before_mutation",
            "editionId": package.edition_id,
            "canonicalUrl": package.canonical_url,
            "lead": package.lead,
            "postText": package.text,
            "formatId": package.format_id,
            "idempotencyKey": package.idempotency_key,
            "reservedAt": _utc_now(),
            "purpose": (
                "duplicate-blocking reservation; clear only after provider "
                "reconciliation proves no post exists"
            ),
        },
    )


def execute_broadcast(
    package: EditionPackage,
    *,
    state_path: Path,
    receipt_dir: Path,
    attempt_dir: Path,
    enabled: bool,
    kill_switch: bool,
    dry_run: bool,
    provider_factory: Callable[[], Provider],
    expected_user_id: str,
    expected_username: str,
    redactor: Redactor,
    logger: logging.Logger,
) -> str:
    attempt = _base_attempt(package)
    attempt_path = attempt_dir / f"{package.edition_id}-attempt.json"
    receipt_path = receipt_dir / f"{package.edition_id}.json"

    def finish(status: str, *, exc: BaseException | None = None, mutations: int = 0) -> None:
        attempt["finishedAt"] = _utc_now()
        attempt["status"] = status
        attempt["mutationAttempts"] = mutations
        if exc is not None:
            attempt["errorClass"] = type(exc).__name__
            attempt["error"] = redactor.clean(exc)
        _atomic_write_json(attempt_path, attempt)

    if kill_switch:
        finish("skipped_kill_switch")
        logger.info("canonical broadcast skipped: kill switch is active")
        return "skipped_kill_switch"

    state = load_state(state_path)
    try:
        assert_not_duplicate(package, state, receipt_dir)
    except DuplicateError as exc:
        finish("refused_duplicate", exc=exc)
        logger.warning(redactor.clean(exc))
        return "refused_duplicate"

    if dry_run:
        finish("dry_run")
        logger.info("canonical broadcast dry-run passed without provider mutation")
        return "dry_run"
    if not enabled:
        finish("skipped_disabled")
        logger.info("canonical broadcast skipped: adapter is disabled")
        return "skipped_disabled"

    provider: Provider | None = None
    post_id: str | None = None
    # Reserve the edition before loading credentials. If the runner is
    # interrupted after mutation, the always-run artifact step has a blocking
    # receipt to preserve rather than silently permitting a duplicate rerun.
    _atomic_write_json(
        receipt_path,
        _blocking_receipt(
            package,
            status="needs_reconciliation",
            provider_post_id=None,
            reason="pre-mutation reservation; reconcile if this run did not finish",
            expected_username=expected_username,
        ),
    )
    try:
        provider = provider_factory()
        provider.verify_identity()
        existing = provider.find_existing_post(package)
        if existing is not None:
            post_id = str(existing.get("id", "")) or None
            published_at = verify_readback(
                package, existing, existing, expected_user_id
            )
            _atomic_write_json(
                receipt_path,
                _blocking_receipt(
                    package,
                    status="existing_provider_post",
                    provider_post_id=post_id,
                    reason="exact canonical post recovered from provider timeline before mutation",
                    published_at=published_at,
                    expected_username=expected_username,
                    automated=None,
                ),
            )
            finish("refused_provider_duplicate", mutations=0)
            logger.warning("exact canonical X post already exists; mutation refused")
            return "refused_provider_duplicate"
        created = provider.create_post(package.text)
        post_id = str(created.get("id", "")) or None
        try:
            readback = provider.read_post(post_id or "")
        except Exception as exc:
            raise ReadbackError(
                redactor.clean(f"provider read-back failed: {exc}"),
                provider_post_id=post_id,
            ) from exc
        published_at = verify_readback(
            package, created, readback, expected_user_id
        )
        receipt = _blocking_receipt(
            package,
            status="published",
            provider_post_id=post_id,
            reason=None,
            published_at=published_at,
            expected_username=expected_username,
        )
        _atomic_write_json(receipt_path, receipt)
        finish("published", mutations=provider.mutation_attempts)
        logger.info("canonical X broadcast published and read-back verified")
        return "published"
    except (AmbiguousMutationError, ReadbackError) as exc:
        if isinstance(exc, ReadbackError) and exc.provider_post_id:
            post_id = exc.provider_post_id
        receipt = _blocking_receipt(
            package,
            status="needs_reconciliation",
            provider_post_id=post_id,
            reason=redactor.clean(exc),
            expected_username=expected_username,
        )
        _atomic_write_json(receipt_path, receipt)
        mutations = provider.mutation_attempts if provider else 0
        finish("needs_reconciliation", exc=exc, mutations=mutations)
        logger.error(redactor.clean(exc))
        raise
    except Exception as exc:
        mutations = provider.mutation_attempts if provider else 0
        known_no_mutation = (
            mutations == 0
            or isinstance(exc, PermanentProviderError)
            or isinstance(exc, RetryableProviderError) and exc.status == 429
        )
        if known_no_mutation:
            receipt_path.unlink(missing_ok=True)
        finish("failed", exc=exc, mutations=mutations)
        logger.error(redactor.clean(exc))
        raise


def _github_api_json(
    url: str,
    token: str,
    *,
    transport: Any | None = None,
) -> Mapping[str, Any]:
    client = transport or UrlLibTransport()
    try:
        response = client.request(
            "GET",
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ddb-x-receipt-hydrator/1",
            },
            body=None,
            timeout=10.0,
        )
    except (TimeoutError, error.URLError, OSError) as exc:
        raise BroadcastError("GitHub receipt lookup failed before duplicate safety could be proven") from exc
    if response.status != 200:
        raise BroadcastError(f"GitHub receipt lookup failed with HTTP {response.status}")
    return _safe_json(response, Redactor([token]))


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
    _edition_order_key(edition_id)
    state = load_state(state_path)
    cleared = {str(value) for value in state["clearedRemoteArtifactIds"]}
    names = (
        f"x-broadcast-receipt-{edition_id}",
        f"x-broadcast-reservation-{edition_id}",
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
            raise BroadcastError("GitHub artifact lookup returned no artifact array")
        active = []
        for item in artifacts:
            if (
                not isinstance(item, dict)
                or item.get("name") != name
                or item.get("expired") is True
            ):
                continue
            artifact_id = str(item.get("id", ""))
            if artifact_id and artifact_id not in cleared:
                active.append(item)
        if not active:
            continue
        active.sort(key=lambda item: int(item.get("id", 0)), reverse=True)
        selected = active[0]
        stub = {
            "version": 1,
            "status": "remote_artifact",
            "editionId": edition_id,
            "artifactId": str(selected["id"]),
            "artifactName": name,
            "workflowRunId": str((selected.get("workflow_run") or {}).get("id", "")),
            "source": "GitHub Actions receipt or reservation artifact metadata",
        }
        _atomic_write_json(output_dir / f"remote-{edition_id}.json", stub)
        return True
    return False


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ValidationError(f"required environment value {name} is missing")
    return value


def _provider_from_environment(redactor: Redactor) -> XApiProvider:
    return XApiProvider(
        signer=OAuth1Signer(
            _required_env("X_API_KEY"),
            _required_env("X_API_SECRET"),
            _required_env("X_ACCESS_TOKEN"),
            _required_env("X_ACCESS_TOKEN_SECRET"),
        ),
        expected_user_id=_required_env("X_EXPECTED_USER_ID"),
        expected_username=_required_env("X_EXPECTED_USERNAME"),
        redactor=redactor,
    )


def _preview_value(package: EditionPackage) -> dict[str, Any]:
    value = asdict(package)
    return {
        "editionId": value["edition_id"],
        "date": value["date"],
        "slot": value["slot"],
        "lead": value["lead"],
        "canonicalUrl": value["canonical_url"],
        "text": value["text"],
        "weightedLength": value["weighted_length"],
        "formatId": value["format_id"],
        "idempotencyKey": value["idempotency_key"],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("preview", "run", "reserve"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--archive", type=Path, default=Path("archive.json"))
        sub.add_argument("--date", required=True)
        sub.add_argument("--slot", choices=("morning", "evening"), required=True)
        if name in {"run", "reserve"}:
            sub.add_argument(
                "--state", type=Path, default=Path("distribution/x-broadcast-state.json")
            )
            sub.add_argument("--receipt-dir", type=Path, required=True)
        if name == "run":
            sub.add_argument("--attempt-dir", type=Path, required=True)
            sub.add_argument("--dry-run", action="store_true")
        if name == "reserve":
            sub.add_argument("--output", type=Path, required=True)
    hydrate = subparsers.add_parser("hydrate-github-receipt")
    hydrate.add_argument("--repository", required=True)
    hydrate.add_argument("--edition-id", required=True)
    hydrate.add_argument(
        "--state", type=Path, default=Path("distribution/x-broadcast-state.json")
    )
    hydrate.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger("ddb.x_broadcast")
    runtime_redactor = Redactor(
        [
            os.environ.get(name, "")
            for name in (
                "GITHUB_TOKEN",
                "X_API_KEY",
                "X_API_SECRET",
                "X_ACCESS_TOKEN",
                "X_ACCESS_TOKEN_SECRET",
            )
        ]
    )
    try:
        if args.command == "hydrate-github-receipt":
            found = hydrate_github_receipt(
                repository=args.repository,
                edition_id=args.edition_id,
                token=_required_env("GITHUB_TOKEN"),
                state_path=args.state,
                output_dir=args.output_dir,
            )
            logger.info("prior blocking receipt artifact %s", "found" if found else "not found")
            return 0

        package = build_package(args.archive, args.date, args.slot)
        if args.command == "preview":
            print(json.dumps(_preview_value(package), indent=2, sort_keys=True))
            return 0
        if args.command == "reserve":
            write_durable_reservation(
                package,
                state_path=args.state,
                receipt_dir=args.receipt_dir,
                output_path=args.output,
            )
            logger.info("durable pre-mutation reservation prepared")
            return 0

        redactor = runtime_redactor
        expected_user_id = os.environ.get("X_EXPECTED_USER_ID", "")
        expected_username = os.environ.get("X_EXPECTED_USERNAME", "")
        enabled = _is_true(os.environ.get("DDB_X_BROADCAST_ENABLED"))
        kill_switch = (
            os.environ.get("DDB_X_BROADCAST_KILL_SWITCH", "").strip().lower()
            != "false"
        )
        # Dry runs use inert, syntactically valid identity placeholders and do
        # not instantiate the credentialed provider.
        if args.dry_run:
            expected_user_id = expected_user_id or "1"
            expected_username = expected_username or "DavidDailyBread"
        execute_broadcast(
            package,
            state_path=args.state,
            receipt_dir=args.receipt_dir,
            attempt_dir=args.attempt_dir,
            enabled=enabled,
            kill_switch=kill_switch,
            dry_run=args.dry_run,
            provider_factory=lambda: _provider_from_environment(redactor),
            expected_user_id=expected_user_id,
            expected_username=expected_username,
            redactor=redactor,
            logger=logger,
        )
        return 0
    except BroadcastError as exc:
        logger.error("broadcast failed: %s", runtime_redactor.clean(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
