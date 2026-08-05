#!/usr/bin/env python3
"""Build and verify one sealed Daily bake publisher bundle.

The author runner is untrusted and never receives a repository-write
credential.  This helper packages only the files accepted by
``ddb_workflow_guard.py``.  A fresh publisher runner decrypts the envelope,
revalidates every byte, and applies it to a clean checkout of the captured
base commit before any GitHub App token is minted.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile

from ddb_workflow_guard import Change, GuardError, parse_porcelain_z, validate_changes


SCHEMA_VERSION = "ddb-publisher-bundle-v1"
SHA_RE = re.compile(r"[0-9a-f]{40}")
MODES = ("daily", "backfill")
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 128 * 1024


class BundleError(ValueError):
    """The bundle violates the publisher trust contract."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_head(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _current_changes(root: Path) -> list[Change]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    return parse_porcelain_z(completed.stdout)


def _validate_identity(date: str, slot: str, mode: str, base_sha: str) -> None:
    if mode not in MODES:
        raise BundleError("invalid bake mode")
    if SHA_RE.fullmatch(base_sha) is None:
        raise BundleError("invalid base commit")
    try:
        validate_changes(
            [Change("??", f"editions/{date}-{slot}.html")], date, slot
        )
    except GuardError as exc:
        if "expected new edition is missing" not in str(exc):
            raise BundleError("invalid edition identity") from exc


def _safe_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or value != path.as_posix()
        or value.startswith("./")
    ):
        raise BundleError("unsafe bundle path")
    return path


def _manifest_files(
    root: Path, paths: list[str]
) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    records: list[dict[str, object]] = []
    payloads: dict[str, bytes] = {}
    total = 0
    for value in sorted(paths):
        _safe_path(value)
        source = root / value
        if source.is_symlink() or not source.is_file():
            raise BundleError("bundle source must be one regular file")
        payload = source.read_bytes()
        size = len(payload)
        if size > MAX_FILE_BYTES:
            raise BundleError("bundle file exceeds size limit")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise BundleError("bundle exceeds total size limit")
        records.append({"path": value, "sha256": _sha256(payload), "size": size})
        payloads[value] = payload
    return records, payloads


def create_bundle(
    *, root: Path, output: Path, date: str, slot: str, mode: str, base_sha: str
) -> dict[str, object]:
    _validate_identity(date, slot, mode, base_sha)
    if _git_head(root) != base_sha:
        raise BundleError("author checkout does not match captured base commit")
    try:
        paths = validate_changes(_current_changes(root), date, slot)
    except GuardError as exc:
        raise BundleError("author change set failed the bake guard") from exc
    records, payloads = _manifest_files(root, paths)
    manifest: dict[str, object] = {
        "schemaVersion": SCHEMA_VERSION,
        "baseSha": base_sha,
        "date": date,
        "slot": slot,
        "mode": mode,
        "files": records,
    }
    manifest_bytes = (
        json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )
    if len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise BundleError("manifest exceeds size limit")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        manifest_info = tarfile.TarInfo("manifest.json")
        manifest_info.size = len(manifest_bytes)
        manifest_info.mode = 0o600
        manifest_info.mtime = 0
        archive.addfile(manifest_info, io.BytesIO(manifest_bytes))
        for value in sorted(payloads):
            payload = payloads[value]
            info = tarfile.TarInfo(f"files/{value}")
            info.size = len(payload)
            info.mode = 0o600
            info.mtime = 0
            archive.addfile(info, io.BytesIO(payload))
    return manifest


def _read_bundle(bundle: Path) -> tuple[dict[str, object], dict[str, bytes]]:
    if bundle.is_symlink() or not bundle.is_file():
        raise BundleError("bundle must be one regular file")
    members: dict[str, bytes] = {}
    total = 0
    try:
        with tarfile.open(bundle, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile() or member.name in members:
                    raise BundleError("bundle contains a non-file or duplicate member")
                if member.size < 0 or member.size > MAX_FILE_BYTES:
                    raise BundleError("bundle member exceeds size limit")
                total += member.size
                if total > MAX_TOTAL_BYTES + MAX_MANIFEST_BYTES:
                    raise BundleError("bundle exceeds total size limit")
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise BundleError("bundle member could not be read")
                members[member.name] = extracted.read()
    except (tarfile.TarError, OSError) as exc:
        raise BundleError("bundle is not a valid gzip tar archive") from exc
    manifest_bytes = members.pop("manifest.json", None)
    if manifest_bytes is None or len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise BundleError("bundle manifest is missing or oversized")
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError("bundle manifest is invalid") from exc
    if not isinstance(manifest, dict):
        raise BundleError("bundle manifest must be an object")
    return manifest, members


def apply_bundle(
    *, root: Path, bundle: Path, date: str, slot: str, mode: str, base_sha: str
) -> dict[str, object]:
    _validate_identity(date, slot, mode, base_sha)
    if _git_head(root) != base_sha:
        raise BundleError("publisher checkout does not match captured base commit")
    dirty = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    if dirty:
        raise BundleError("publisher checkout is not clean")

    manifest, members = _read_bundle(bundle)
    expected_header = {
        "schemaVersion": SCHEMA_VERSION,
        "baseSha": base_sha,
        "date": date,
        "slot": slot,
        "mode": mode,
    }
    for key, expected in expected_header.items():
        if manifest.get(key) != expected:
            raise BundleError("bundle identity does not match this run")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise BundleError("bundle file manifest is empty or invalid")

    changes: list[Change] = []
    verified: dict[str, bytes] = {}
    seen: set[str] = set()
    expected_edition = f"editions/{date}-{slot}.html"
    for record in records:
        if not isinstance(record, dict):
            raise BundleError("bundle file record is invalid")
        value = record.get("path")
        digest = record.get("sha256")
        size = record.get("size")
        if not isinstance(value, str) or value in seen:
            raise BundleError("bundle path is invalid or duplicated")
        _safe_path(value)
        seen.add(value)
        member_name = f"files/{value}"
        payload = members.get(member_name)
        if (
            payload is None
            or not isinstance(digest, str)
            or not isinstance(size, int)
            or size != len(payload)
            or digest != _sha256(payload)
        ):
            raise BundleError("bundle file digest or size does not match")
        verified[value] = payload
        changes.append(Change("??" if value == expected_edition else " M", value))
    if set(members) != {f"files/{value}" for value in seen}:
        raise BundleError("bundle contains an unmanifested member")
    try:
        accepted = validate_changes(changes, date, slot)
    except GuardError as exc:
        raise BundleError("bundle paths failed the bake guard") from exc
    if accepted != sorted(seen):
        raise BundleError("bundle path set is not canonical")

    for value in accepted:
        destination = root / value
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(verified[value])
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("create", "apply"):
        child = subparsers.add_parser(command)
        child.add_argument("--date", required=True)
        child.add_argument("--slot", choices=("morning", "evening"), required=True)
        child.add_argument("--mode", choices=MODES, required=True)
        child.add_argument("--base-sha", required=True)
    create = subparsers.choices["create"]
    create.add_argument("--output", type=Path, required=True)
    apply = subparsers.choices["apply"]
    apply.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    try:
        if args.command == "create":
            manifest = create_bundle(
                root=root,
                output=args.output,
                date=args.date,
                slot=args.slot,
                mode=args.mode,
                base_sha=args.base_sha,
            )
        else:
            manifest = apply_bundle(
                root=root,
                bundle=args.bundle,
                date=args.date,
                slot=args.slot,
                mode=args.mode,
                base_sha=args.base_sha,
            )
    except (BundleError, OSError, subprocess.CalledProcessError) as exc:
        print(f"PUBLISHER BUNDLE FAIL: {exc}", file=__import__("sys").stderr)
        return 1
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
