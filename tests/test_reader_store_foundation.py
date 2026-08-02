#!/usr/bin/env python3
"""Static gates for the private reader-store foundation when Docker is unavailable."""

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUPABASE = ROOT / "supabase"
MIGRATION = next((SUPABASE / "migrations").glob("*_reader_private_foundation.sql"))


class ReaderStoreFoundationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8")
        cls.config = (SUPABASE / "config.toml").read_text(encoding="utf-8")
        cls.functions = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((SUPABASE / "functions").rglob("*.ts"))
            if "tests" not in path.parts
        )

    def test_private_schema_is_not_exposed_and_bucket_is_private(self):
        self.assertIn('schemas = ["public", "graphql_public"]', self.config)
        self.assertNotRegex(self.config, r'(?m)^schemas\s*=.*reader_private')
        self.assertIn("auto_expose_new_tables = false", self.config)
        bucket = self.config.split("[storage.buckets.bake-handoffs]", 1)[1]
        self.assertRegex(bucket, r"(?m)^public = false$")
        self.assertIn('file_size_limit = "10MiB"', bucket)

    def test_all_private_tables_have_forced_rls_and_no_browser_grants(self):
        tables = ("submissions", "plan_batches", "plan_items", "audit_events")
        for table in tables:
            self.assertIn(
                f"alter table reader_private.{table} enable row level security;",
                self.sql,
            )
            self.assertIn(
                f"alter table reader_private.{table} force row level security;",
                self.sql,
            )
        self.assertIn(
            "revoke all on all tables in schema reader_private from public, anon, authenticated, service_role, reader_edge;",
            self.sql,
        )
        self.assertNotRegex(
            self.sql,
            r"grant\s+(?:select|insert|update|delete|all).*\s+to\s+(?:anon|authenticated)",
        )

    def test_edge_role_is_execute_only_and_functions_are_hardened(self):
        self.assertIn("create role reader_edge", self.sql)
        self.assertIn("nobypassrls", self.sql)
        self.assertNotRegex(self.sql, r"grant .* on .*table.* to reader_edge")
        for routine in (
            "submit_submission",
            "delete_submission",
            "reserve_plan",
            "authorize_publish",
            "finalize_plan",
            "release_plan",
            "authorize_handoff",
        ):
            self.assertRegex(
                self.sql,
                rf"create function reader_private\.{routine}\([\s\S]*?security definer[\s\S]*?set search_path = ''",
            )
            self.assertRegex(
                self.sql,
                rf"grant execute on function reader_private\.{routine}\(",
            )

    def test_queue_and_idempotency_primitives_are_present(self):
        for invariant in (
            "for update skip locked",
            "order by submission.submitted_at, submission.id",
            "pg_advisory_xact_lock",
            "plan_batches_one_live_or_finalized_edition_idx",
            "plan_items_one_active_batch_per_submission_idx",
            "manifest_digest_mismatch",
            "publishing_reconciliation_required",
            "constant_time_equal",
        ):
            self.assertIn(invariant, self.sql.lower())

    def test_retention_and_private_receipt_primitives_are_bounded(self):
        for invariant in (
            "interval '90 days'",
            "interval '30 days'",
            "interval '365 days'",
            "ddb-reader-retention-daily",
            "reader_private.run_retention",
            "where submission.reserved_batch_id = batch.id",
        ):
            self.assertIn(invariant, self.sql)
        self.assertNotIn("body jsonb", self.sql.lower())
        self.assertNotIn("byline jsonb", self.sql.lower())

    def test_edge_source_has_no_privileged_supabase_key_or_sensitive_logging(self):
        for forbidden in (
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_SECRET_KEYS",
            "ctx.supabaseAdmin",
            "console.log(error",
            "console.error(error",
        ):
            self.assertNotIn(forbidden, self.functions)
        self.assertIn("DDB_READER_DATABASE_URL", self.functions)
        self.assertIn("DDB_READER_DATABASE_SSL_CA", self.functions)
        self.assertIn("DDB_READER_BROKER_TOKEN", self.functions)
        self.assertIn("DDB_TURNSTILE_SECRET_KEY", self.functions)

    def test_remote_database_connections_fail_closed_on_tls(self):
        database = (
            SUPABASE / "functions" / "_shared" / "database.ts"
        ).read_text(encoding="utf-8")
        self.assertIn('sslMode !== "verify-full"', database)
        self.assertIn("rejectUnauthorized: true", database)
        self.assertIn('sslMode === "disable"', database)
        self.assertIn('hostname === "localhost"', database)
        self.assertNotIn('ssl: "require"', database)

        contract = json.loads(
            (ROOT / "operations" / "reader-store.contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("verify-full", contract["database"]["remoteTlsMode"])
        self.assertEqual(
            "DDB_READER_DATABASE_SSL_CA",
            contract["database"]["remoteTlsCaSecret"],
        )
        self.assertEqual("loopback-only", contract["database"]["tlsDisableScope"])

    def test_reserve_response_is_selected_items_only(self):
        response_match = re.search(
            r"create function reader_private\.plan_response[\s\S]*?create function",
            self.sql,
        )
        self.assertIsNotNone(response_match)
        response_sql = response_match.group(0)
        for allowed in ("selectionReference", "kind", "body", "byline"):
            self.assertIn(f"'{allowed}'", response_sql)
        for forbidden in (
            "deletion_token_hash",
            "count(*)",
            "submitted_at",
            "publication_consent",
        ):
            self.assertNotIn(forbidden, response_sql)

    def test_handoff_capabilities_are_private_immutable_and_retained_six_hours(self):
        storage = (
            SUPABASE / "functions" / "_shared" / "storage.ts"
        ).read_text(encoding="utf-8")
        for invariant in (
            'const BUCKET = "bake-handoffs"',
            "createSignedUploadUrl(objectPath, { upsert: false })",
            "const DOWNLOAD_SECONDS = 60",
            "6 * 60 * 60 * 1_000",
            "requiredCacheControl: \"0\"",
        ):
            self.assertIn(invariant, storage)
        self.assertRegex(storage, r"\.remove\(\[\s*objectPath,\s*\]\)")
        self.assertNotIn(".getPublicUrl(", storage)

    def test_external_launch_gates_remain_explicit_and_unfilled(self):
        contract = json.loads(
            (ROOT / "operations" / "reader-store.contract.json").read_text(
                encoding="utf-8"
            )
        )
        decision = contract["founderDecision"]
        self.assertFalse(decision["newReaderIntakeAuthorized"])
        self.assertFalse(decision["provisioningAuthorized"])
        self.assertFalse(decision["deploymentAuthorized"])
        self.assertFalse(decision["canaryAuthorized"])
        self.assertFalse(decision["activationAuthorized"])
        self.assertTrue(decision["explicitReversalRequired"])
        self.assertEqual(
            [
                "verified-privacy-contact-address",
                "provisioned-dedicated-supabase-project",
            ],
            contract["launchBlockers"],
        )
        self.assertEqual(
            [], contract["database"]["edgeRoleTablePrivileges"]
        )
        self.assertEqual(
            "cleanup-handoffs",
            contract["retentionAutomation"]["handoffCleanupOperation"],
        )
        runbook = (ROOT / "docs" / "READER_STORE_RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not link, migrate, deploy, canary", runbook)
        self.assertIn("no Supabase", runbook)
        self.assertIn("David first records an explicit reversal", runbook)
        self.assertNotRegex(runbook, r"[A-Za-z0-9._%+-]+@davidsdailybread\.com")

    def test_merge_gate_runs_reader_source_database_and_concurrency_checks(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        for command in (
            "npm ci",
            "npm run test:reader-edge",
            "npm run test:reader-types",
            "npm exec -- supabase db start",
            "npm run supabase:reset",
            "npm run test:reader-db",
            "npm run test:reader-concurrency",
            "npm exec -- supabase stop --no-backup",
        ):
            self.assertIn(command, workflow)


if __name__ == "__main__":
    unittest.main()
