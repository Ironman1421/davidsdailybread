#!/usr/bin/env python3
"""SQLite execution contract for the local Cloudflare D1 implementation."""

from pathlib import Path
import re
import sqlite3
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "audience" / "cloudflare" / "schema.sql"
WORKER_PATH = ROOT / "audience" / "cloudflare" / "worker.mjs"
DEFINITION_VERSION = 1
MONTH = "2026-07"
DIGEST = "a" * 64


def worker_sql(name: str) -> str:
    """Read the exact prepared statement used by worker.mjs."""

    source = WORKER_PATH.read_text(encoding="utf-8")
    match = re.search(rf"  {re.escape(name)}: `\n(.*?)\n  `,", source, re.DOTALL)
    if match is None:
        raise AssertionError(f"Worker SQL statement {name!r} was not found")
    return textwrap.dedent(match.group(1)).strip()


class CloudflareD1SchemaTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def tearDown(self):
        self.db.close()

    def transition(self, name: str, received_date: str) -> int:
        cursor = self.db.execute(
            worker_sql(name),
            (DEFINITION_VERSION, MONTH, DIGEST, received_date),
        )
        self.db.commit()
        return cursor.rowcount

    def aggregate(self) -> tuple[int, int, int]:
        row = self.db.execute(
            worker_sql("readAggregate"),
            (DEFINITION_VERSION, MONTH),
        ).fetchone()
        assert row is not None
        return (
            row["first_seen_visitors"],
            row["returning_visitors"],
            row["qualified_engaged_returning_readers"],
        )

    def test_exact_worker_statements_are_idempotent_ordered_and_aggregated(self):
        self.assertEqual(1, self.transition("insertFirstSeen", "2026-07-01"))
        self.assertEqual(0, self.transition("insertFirstSeen", "2026-07-01"))
        self.assertEqual((1, 0, 0), self.aggregate())

        self.assertEqual(0, self.transition("recordReturned", "2026-07-01"))
        self.assertEqual(1, self.transition("recordReturned", "2026-07-02"))
        self.assertEqual(0, self.transition("recordReturned", "2026-07-03"))
        self.assertEqual((1, 1, 0), self.aggregate())

        self.assertEqual(0, self.transition("recordQualified", "2026-07-02"))
        self.assertEqual(1, self.transition("recordQualified", "2026-07-03"))
        self.assertEqual(0, self.transition("recordQualified", "2026-07-04"))
        self.assertEqual((1, 1, 1), self.aggregate())

        row = self.db.execute(
            "SELECT * FROM audience_visitors"
        ).fetchone()
        assert row is not None
        self.assertEqual(DIGEST, row["token_digest"])
        self.assertEqual("2026-08-05", row["expires_on"])
        self.assertNotIn("token", row.keys())
        self.assertNotIn("ip", row.keys())

    def test_purge_erases_participant_row_and_preserves_monthly_aggregate(self):
        self.transition("insertFirstSeen", "2026-07-01")
        self.transition("recordReturned", "2026-07-02")
        self.transition("recordQualified", "2026-07-03")

        before_expiry = self.db.execute(
            worker_sql("purgeExpired"), ("2026-08-04",)
        )
        self.assertEqual(0, before_expiry.rowcount)
        at_expiry = self.db.execute(
            worker_sql("purgeExpired"), ("2026-08-05",)
        )
        self.assertEqual(1, at_expiry.rowcount)
        self.db.commit()

        self.assertEqual(
            0,
            self.db.execute(worker_sql("countExpired"), ("2026-08-05",)).fetchone()[
                "expired_count"
            ],
        )
        self.assertEqual(0, self.db.execute("SELECT COUNT(*) FROM audience_visitors").fetchone()[0])
        self.assertEqual((1, 1, 1), self.aggregate())

    def test_schema_rejects_invalid_digest_expiry_and_identity_mutation(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                """
                INSERT INTO audience_visitors (
                    definition_version, month, token_digest,
                    first_seen_date, expires_on
                ) VALUES (?1, ?2, ?3, ?4, date(?4, '+35 days'))
                """,
                (
                    DEFINITION_VERSION,
                    MONTH,
                    "raw-browser-token",
                    "2026-07-01",
                ),
            )

        self.transition("insertFirstSeen", "2026-07-01")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE audience_visitors SET token_digest = ?",
                ("b" * 64,),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE audience_visitors SET expires_on = ?",
                ("2099-01-01",),
            )


if __name__ == "__main__":
    unittest.main()
