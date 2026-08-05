#!/usr/bin/env python3
"""Regression tests for the fresh-runner publisher bundle boundary."""
from __future__ import annotations

from pathlib import Path
import io
import json
import subprocess
import tarfile
import tempfile
import unittest

from ddb_publish_bundle import BundleError, apply_bundle, create_bundle


DATE = "2099-01-01"
SLOT = "morning"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


class PublisherBundleTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        git(self.source, "init", "-b", "main")
        git(self.source, "config", "user.name", "Test")
        git(self.source, "config", "user.email", "test@example.com")
        (self.source / "index.html").write_text("before\n", encoding="utf-8")
        git(self.source, "add", "index.html")
        git(self.source, "commit", "-m", "base")
        self.base_sha = git(self.source, "rev-parse", "HEAD")
        self.publisher = self.root / "publisher"
        git(self.root, "clone", str(self.source), str(self.publisher))

    def tearDown(self):
        self.temporary.cleanup()

    def author_changes(self):
        (self.source / "index.html").write_text("after\n", encoding="utf-8")
        edition = self.source / "editions" / f"{DATE}-{SLOT}.html"
        edition.parent.mkdir()
        edition.write_text("edition\n", encoding="utf-8")

    def test_round_trip_applies_only_guarded_bytes_to_clean_base(self):
        self.author_changes()
        bundle = self.root / "bundle.tar.gz"
        manifest = create_bundle(
            root=self.source,
            output=bundle,
            date=DATE,
            slot=SLOT,
            mode="daily",
            base_sha=self.base_sha,
        )
        applied = apply_bundle(
            root=self.publisher,
            bundle=bundle,
            date=DATE,
            slot=SLOT,
            mode="daily",
            base_sha=self.base_sha,
        )

        self.assertEqual(manifest, applied)
        self.assertEqual("after\n", (self.publisher / "index.html").read_text())
        self.assertEqual(
            "edition\n",
            (self.publisher / "editions" / f"{DATE}-{SLOT}.html").read_text(),
        )

    def test_rejects_identity_mismatch_and_dirty_publisher(self):
        self.author_changes()
        bundle = self.root / "bundle.tar.gz"
        create_bundle(
            root=self.source,
            output=bundle,
            date=DATE,
            slot=SLOT,
            mode="daily",
            base_sha=self.base_sha,
        )
        with self.assertRaises(BundleError):
            apply_bundle(
                root=self.publisher,
                bundle=bundle,
                date=DATE,
                slot=SLOT,
                mode="backfill",
                base_sha=self.base_sha,
            )
        (self.publisher / "unexpected.txt").write_text("dirty\n")
        with self.assertRaises(BundleError):
            apply_bundle(
                root=self.publisher,
                bundle=bundle,
                date=DATE,
                slot=SLOT,
                mode="daily",
                base_sha=self.base_sha,
            )

    def test_rejects_an_unmanifested_or_unsafe_member(self):
        self.author_changes()
        original = self.root / "bundle.tar.gz"
        create_bundle(
            root=self.source,
            output=original,
            date=DATE,
            slot=SLOT,
            mode="daily",
            base_sha=self.base_sha,
        )
        tampered = self.root / "tampered.tar.gz"
        with tarfile.open(original, "r:gz") as source, tarfile.open(
            tampered, "w:gz"
        ) as destination:
            for member in source.getmembers():
                payload = source.extractfile(member).read()
                destination.addfile(member, io.BytesIO(payload))
            payload = b"unexpected\n"
            member = tarfile.TarInfo("files/../unexpected.txt")
            member.size = len(payload)
            destination.addfile(member, io.BytesIO(payload))

        with self.assertRaises(BundleError):
            apply_bundle(
                root=self.publisher,
                bundle=tampered,
                date=DATE,
                slot=SLOT,
                mode="daily",
                base_sha=self.base_sha,
            )


if __name__ == "__main__":
    unittest.main()
