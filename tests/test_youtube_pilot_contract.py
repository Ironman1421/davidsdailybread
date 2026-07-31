#!/usr/bin/env python3
"""Regression tests for the repository-owned YouTube pilot foundation."""

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
YOUTUBE = ROOT / "youtube"
SCHEMAS = YOUTUBE / "schemas"
LEDGERS = YOUTUBE / "ledgers"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class YoutubePilotContractTest(unittest.TestCase):
    def setUp(self):
        self.spec = (ROOT / "docs" / "YOUTUBE_PILOT_SPEC.md").read_text(
            encoding="utf-8"
        )
        self.runbook = (ROOT / "docs" / "YOUTUBE_PILOT_RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        self.experiment = load_json(LEDGERS / "experiment.json")
        self.experiment_schema = load_json(SCHEMAS / "experiment.schema.json")
        self.video_schema = load_json(SCHEMAS / "video-receipts.schema.json")
        self.asset_schema = load_json(SCHEMAS / "asset-provenance.schema.json")

    def test_all_owned_artifacts_exist_and_all_json_parses(self):
        expected = (
            ROOT / "docs" / "YOUTUBE_PILOT_SPEC.md",
            ROOT / "docs" / "YOUTUBE_PILOT_RUNBOOK.md",
            YOUTUBE / "templates" / "morning-receipts.md",
            YOUTUBE / "templates" / "tonights-field-guide.md",
            SCHEMAS / "claim-evidence.schema.json",
            SCHEMAS / "asset-provenance.schema.json",
            SCHEMAS / "corrections.schema.json",
            SCHEMAS / "video-receipts.schema.json",
            SCHEMAS / "experiment.schema.json",
            LEDGERS / "claim-evidence.json",
            LEDGERS / "asset-provenance.json",
            LEDGERS / "corrections.json",
            LEDGERS / "video-receipts.json",
            LEDGERS / "experiment.json",
        )
        for path in expected:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                if path.suffix == ".json":
                    self.assertIsInstance(load_json(path), dict)

        for path in SCHEMAS.glob("*.schema.json"):
            schema = load_json(path)
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(1, schema["properties"]["version"]["const"])

    def test_morning_and_evening_have_distinct_jobs(self):
        normalized = " ".join(self.spec.split())
        self.assertIn("### Morning Receipts", self.spec)
        self.assertIn("What changed, what proves it, and why does it matter?", normalized)
        self.assertIn("### Tonight's Field Guide", self.spec)
        self.assertIn(
            "What can an everyday reader use or try tonight, how, at what cost, and with what caveat?",
            normalized,
        )

        morning = (YOUTUBE / "templates" / "morning-receipts.md").read_text(
            encoding="utf-8"
        )
        evening = (YOUTUBE / "templates" / "tonights-field-guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("What changed:", morning)
        self.assertIn("why it matters", morning.lower())
        self.assertNotIn("two to four steps", morning.lower())
        self.assertIn("Outcome tonight:", evening)
        self.assertIn("two to four steps", evening.lower())
        self.assertIn("Clean-account recording checklist", evening)

        video = self.video_schema["$defs"]["video"]
        slot_rule = next(
            rule
            for rule in video["allOf"]
            if rule.get("if", {}).get("properties", {}).get("formatId", {}).get("const")
            == "morning_receipts"
        )
        self.assertTrue(
            slot_rule["then"]["properties"]["editionId"]["pattern"].endswith("-morning$")
        )
        self.assertTrue(
            slot_rule["else"]["properties"]["editionId"]["pattern"].endswith("-evening$")
        )

    def test_pilot_forbids_read_aloud_and_news_feed_automation(self):
        production = self.video_schema["$defs"]["production"]
        self.assertEqual(True, production["properties"]["originalAnalysisConfirmed"]["const"])
        self.assertEqual(False, production["properties"]["readAloudOrNewsFeedAutomation"]["const"])
        self.assertEqual(False, production["properties"]["nearDuplicatePublicVariant"]["const"])

        active = " ".join((self.spec + "\n" + self.runbook).lower().split())
        for rejected in (
            "article or news-feed read-aloud",
            "headline roll",
            "near-duplicate public alternate cut",
            "only one variant for public release",
        ):
            self.assertIn(rejected, active)

    def test_initial_modes_are_contracted_human_or_caption_only_never_synthetic(self):
        constraints = self.experiment["constraints"]
        self.assertEqual(
            ["recurring_human_narrator", "caption_only"],
            constraints["initialComparison"],
        )
        self.assertFalse(constraints["syntheticNarratorAllowed"])
        self.assertFalse(constraints["clonedVoiceAllowed"])

        video = self.video_schema["$defs"]["video"]
        self.assertEqual(
            ["recurring_human_narrator", "caption_only"],
            video["properties"]["voiceMode"]["enum"],
        )
        self.assertFalse(video["properties"]["syntheticNarration"]["const"])
        self.assertFalse(video["properties"]["clonedVoice"]["const"])
        narrator_rule = next(
            rule
            for rule in video["allOf"]
            if rule.get("if", {}).get("properties", {}).get("voiceMode", {}).get("const")
            == "recurring_human_narrator"
        )
        self.assertEqual(
            "recurring_human_narrator",
            narrator_rule["if"]["properties"]["voiceMode"]["const"],
        )
        self.assertEqual(
            1,
            narrator_rule["then"]["properties"]["narratorRightsReceiptReference"]["minLength"],
        )

    def test_unknown_rights_cannot_enter_an_asset_manifest(self):
        asset = self.asset_schema["$defs"]["asset"]
        rights_statuses = asset["properties"]["rightsStatus"]["enum"]
        source_classes = asset["properties"]["sourceClass"]["enum"]
        self.assertNotIn("unknown", rights_statuses)
        self.assertNotIn("unknown", source_classes)
        for prohibited in (
            "press_footage",
            "broadcast_footage",
            "article_screenshot",
            "social_video",
            "unlicensed_music",
        ):
            self.assertNotIn(prohibited, source_classes)

        manifest = self.asset_schema["$defs"]["manifest"]
        self.assertEqual(0, manifest["properties"]["unknownRightsAssetCount"]["const"])
        self.assertEqual(
            [
                "press_footage",
                "broadcast_footage",
                "article_screenshot",
                "social_video",
                "unlicensed_music",
            ],
            manifest["properties"]["excludedPilotSourceTypes"]["const"],
        )
        self.assertEqual(1, asset["properties"]["finalTimecodes"]["minItems"])
        self.assertTrue(asset["properties"]["commercialUseAllowed"]["const"])
        self.assertTrue(asset["properties"]["youtubeUseAllowed"]["const"])

    def test_long_form_is_structurally_blocked_before_the_five_post_short_gate(self):
        rule = self.experiment["constraints"]["decisionRule"]
        self.assertTrue(self.experiment["constraints"]["longFormRequiresShortWinner"])
        self.assertEqual(5, rule["minimumEligiblePostsPerCell"])

        gate = self.experiment_schema["$defs"]["gateEvaluation"]
        cell_metrics = self.experiment_schema["$defs"]["cellMetrics"]
        self.assertEqual(5, cell_metrics["properties"]["eligiblePostCount"]["minimum"])
        pass_rule = gate["allOf"][0]
        self.assertEqual("pass", pass_rule["if"]["properties"]["result"]["const"])
        self.assertTrue(pass_rule["then"]["properties"]["longFormReleased"]["const"])
        self.assertFalse(pass_rule["else"]["properties"]["longFormReleased"]["const"])

        video = self.video_schema["$defs"]["video"]
        duration_rule = next(
            rule
            for rule in video["allOf"]
            if rule.get("if", {}).get("properties", {}).get("durationClass", {}).get("const")
            == "short"
        )
        long_form_rule = duration_rule["else"]["properties"]
        self.assertTrue(long_form_rule["longFormGatePassed"]["const"])
        self.assertRegex(long_form_rule["shortWinnerGateReceiptId"]["pattern"], "YGATE")

    def test_every_release_and_gate_requires_human_final_approval(self):
        schema_names = (
            "claim-evidence.schema.json",
            "asset-provenance.schema.json",
            "corrections.schema.json",
            "video-receipts.schema.json",
            "experiment.schema.json",
        )
        for name in schema_names:
            with self.subTest(schema=name):
                approval = load_json(SCHEMAS / name)["$defs"]["humanApproval"]
                self.assertTrue(approval["properties"]["human"]["const"])
                self.assertTrue(approval["properties"]["approved"]["const"])
                self.assertIn("approvedBy", approval["required"])
                self.assertIn("approvedAt", approval["required"])

        production = self.video_schema["$defs"]["production"]
        self.assertIn("humanFinalApproval", production["required"])
        self.assertIn("Silence is rejection", self.runbook)

    def test_budget_is_exactly_2500_and_spend_defaults_to_disabled_zero(self):
        constraints = self.experiment["constraints"]
        self.assertEqual(2500, constraints["externalPlanningCeilingUsd"])
        self.assertFalse(constraints["spendAuthorized"])
        self.assertEqual(0, constraints["authorizedSpendUsd"])
        self.assertFalse(constraints["externalAccountMutationAuthorized"])
        self.assertFalse(constraints["publishingEnabled"])
        self.assertEqual("disabled", self.experiment["operatingState"])
        normalized = " ".join(self.spec.split())
        self.assertIn("exactly USD 2,500", normalized)
        self.assertIn("design constraint, not permission to spend", normalized)

    def test_channel_identity_is_known_but_measurements_remain_unknown_not_zero(self):
        baseline = self.experiment["platformBaseline"]
        self.assertEqual("known", baseline["channelIdentityStatus"])
        self.assertEqual("David's Daily Bread", baseline["channelName"])
        self.assertEqual("@DavidDailyBreadTV", baseline["channelHandle"])
        self.assertEqual("UCRZkkqvdcfaiV-mtka-kmjQ", baseline["channelId"])
        self.assertEqual(
            "https://www.youtube.com/@DavidDailyBreadTV", baseline["publicUrl"]
        )
        self.assertEqual(
            "https://www.youtube.com/channel/UCRZkkqvdcfaiV-mtka-kmjQ",
            baseline["channelIdUrl"],
        )
        self.assertEqual("2026-07-31T21:46:44Z", baseline["createdAt"])
        self.assertEqual("approximate", baseline["createdAtPrecision"])
        self.assertIn(
            "official YouTube UI creation readback",
            baseline["identitySourceReceiptReference"],
        )
        self.assertEqual(
            {"@DavidDailyBread", "@DavidsDailyBread"},
            set(baseline["unavailablePreferredHandles"]),
        )
        self.assertEqual("not_measured", baseline["metricsStatus"])
        for field in (
            "metricsCapturedAt",
            "subscribers",
            "historicalViews",
            "historicalEngagedViews",
            "metricsSourceReceiptReference",
        ):
            self.assertIsNone(baseline[field], field)
        self.assertFalse(baseline["unknownMetricsTreatedAsZero"])
        self.assertEqual(
            {
                "subscriber_count_not_measured",
                "historical_views_not_measured",
                "historical_engaged_views_not_measured",
            },
            set(baseline["unknownMeasurementBlockers"]),
        )
        self.assertIn("Channel identity is no longer a blocker", self.spec)
        self.assertIn("`metricsStatus` is not `captured`", self.runbook)

    def test_baseline_ledgers_have_no_episode_or_operational_receipts(self):
        expected_empty = {
            "claim-evidence.json": ("manifests",),
            "asset-provenance.json": ("manifests",),
            "corrections.json": ("corrections", "replacements"),
            "video-receipts.json": ("videos",),
            "experiment.json": ("experiments", "gateEvaluations"),
        }
        for name, fields in expected_empty.items():
            ledger = load_json(LEDGERS / name)
            with self.subTest(ledger=name):
                self.assertEqual(1, ledger["version"])
                for field in fields:
                    self.assertEqual([], ledger[field])

    def test_claim_receipts_are_per_claim_and_credential_free(self):
        schema = load_json(SCHEMAS / "claim-evidence.schema.json")
        receipt = schema["$defs"]["retrievalReceipt"]
        claim = schema["$defs"]["claim"]
        manifest = schema["$defs"]["manifest"]
        for field in (
            "requestedUrl",
            "resolvedUrl",
            "retrievedAt",
            "httpStatus",
            "contentSha256",
            "primarySource",
        ):
            self.assertIn(field, receipt["required"])
        self.assertIn("(?![^/\\s]*@)", schema["$defs"]["httpsUrl"]["pattern"])
        self.assertEqual(1, claim["properties"]["sourceReceiptIds"]["minItems"])
        self.assertEqual("verified", claim["properties"]["status"]["const"])
        self.assertEqual(0, manifest["properties"]["unsupportedClaimCount"]["const"])

    def test_correction_syntax_and_replacement_receipts_are_preserved(self):
        schema = load_json(SCHEMAS / "corrections.schema.json")
        platform = schema["$defs"]["platformCorrection"]
        replacement = schema["$defs"]["replacement"]
        self.assertEqual(
            ["Correction:", "Corrections:"],
            platform["properties"]["keyword"]["enum"],
        )
        self.assertTrue(platform["properties"]["appearsAfterChapters"]["const"])
        self.assertTrue(replacement["properties"]["originalReceiptPreserved"]["const"])
        self.assertIn("originalPublishReceiptReference", replacement["required"])
        self.assertIn("replacementPublishReceiptReference", replacement["required"])

    def test_30_day_cells_and_thresholds_are_internal_assumptions(self):
        constraints = self.experiment["constraints"]
        self.assertEqual(30, constraints["durationDays"])
        self.assertEqual("voice_mode", constraints["singleChangedVariable"])
        self.assertEqual(
            [
                "morning_receipts:recurring_human_narrator",
                "morning_receipts:caption_only",
                "tonights_field_guide:recurring_human_narrator",
                "tonights_field_guide:caption_only",
            ],
            constraints["plannedCellDefinitions"],
        )
        rule = constraints["decisionRule"]
        self.assertEqual("subscribers_per_1000_engaged_views", rule["primaryMetric"])
        self.assertEqual(0.15, rule["minimumMedianRelativeLift"])
        self.assertEqual(0, rule["unsupportedClaimsAllowed"])
        self.assertEqual(0, rule["unknownRightsAssetsAllowed"])
        self.assertEqual(
            "internal_planning_assumptions_not_platform_benchmarks",
            constraints["classification"],
        )

    def test_policy_references_are_primary_official_pages(self):
        urls = re.findall(r"https://[^)\s]+", self.spec)
        policy_urls = [
            url
            for url in urls
            if url.startswith("https://support.google.com/youtube/")
        ]
        self.assertGreaterEqual(len(policy_urls), 9)
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(
                    url.startswith("https://support.google.com/youtube/")
                    or url.startswith("https://www.youtube.com/"),
                    f"reference is not an official YouTube or YouTube Help page: {url}",
                )
        for answer_id in (
            "1311392",
            "14328491",
            "2797466",
            "6162278",
            "10059070",
            "12220281",
            "57404",
            "72851",
            "13429240",
        ):
            self.assertIn(f"answer/{answer_id}", self.spec)

    def test_templates_are_placeholders_not_real_episodes(self):
        for name in ("morning-receipts.md", "tonights-field-guide.md"):
            template = (YOUTUBE / "templates" / name).read_text(encoding="utf-8")
            with self.subTest(template=name):
                self.assertIn("TEMPLATE ONLY", template)
                self.assertIn("{{", template)
                self.assertIn("}}", template)
                self.assertNotIn("https://", template)
                self.assertIn("Accountable final human approval", template)
                self.assertIn("Synthetic narration and cloned voice are prohibited", template)


if __name__ == "__main__":
    unittest.main()
