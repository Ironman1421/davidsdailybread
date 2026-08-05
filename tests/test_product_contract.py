#!/usr/bin/env python3
"""Executable checks for current product truth and governance wiring."""

from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProductContractTest(unittest.TestCase):
    def test_current_specs_exist_and_name_both_distinct_editions(self):
        doctrine = (ROOT / "FOUNDER_DOCTRINE.md").read_text(encoding="utf-8")
        product = (ROOT / "docs" / "PRODUCT_SPEC.md").read_text(encoding="utf-8")
        security = (ROOT / "docs" / "SECURITY_SPEC.md").read_text(encoding="utf-8")
        growth = (ROOT / "docs" / "GROWTH_ROADMAP.md").read_text(encoding="utf-8")
        distribution = (ROOT / "docs" / "DISTRIBUTION_SPEC.md").read_text(
            encoding="utf-8"
        )
        repo_map = (ROOT / "docs" / "REPOSITORY_MAP.md").read_text(encoding="utf-8")
        normalized_growth = " ".join(growth.split())

        for required in (
            "### Morning edition",
            "### Evening edition",
            "at most 130 characters",
            "absolute, credential-free HTTPS",
        ):
            self.assertIn(required, product)
        for governing_truth in (
            "founder-led Christian media and learning project",
            "website, archive, and RSS are the permanent canonical home",
            "Durable-moat direction",
            "research, product strategy, architecture, design, local",
            "Newsletter strategy and local integration prototypes may proceed",
            "Do not form a nonprofit",
            "Do not deploy or activate custom community software",
            "Public is never the default",
            "David retains final control",
        ):
            self.assertIn(governing_truth, doctrine)
        self.assertIn("Reader privacy", security)
        self.assertIn("1,000 genuinely engaged people", normalized_growth)
        self.assertIn("no longer the active", normalized_growth)
        self.assertIn("operating goal", normalized_growth)
        self.assertIn("Adapter acceptance contract", distribution)
        self.assertIn("Production source of truth", repo_map)

    def test_growth_decisions_are_resolved_in_active_docs(self):
        growth = (ROOT / "docs" / "GROWTH_ROADMAP.md").read_text(encoding="utf-8")
        distribution = (ROOT / "docs" / "DISTRIBUTION_SPEC.md").read_text(
            encoding="utf-8"
        )
        active = " ".join((growth + "\n" + distribution).split())

        for decision in (
            "first 1,000 genuinely engaged people remain the first proof gate",
            "five X followers",
            "David may remain off camera",
            "The website, archive, and RSS are the permanent home",
            "public, carefully moderated prayer-thread playbook",
            "No spend is authorized by this roadmap",
            "Claude Cowork",
            "Credible-account replies",
            "David approves every reply individually",
        ):
            self.assertIn(decision, active)
        for stale_question in (
            "Is the million-follower target aggregate or platform-specific?",
            "Is the brand faceless, voice-led, or David on camera?",
        ):
            self.assertNotIn(stale_question, active)

    def test_canonical_surfaces_state_the_product_distinction(self):
        distinction = (
            "News and Scripture each morning. An evening Field Guide with useful "
            "tools and workflows. "
            "Loved by God."
        )
        masthead_subtitle = (
            "News and Scripture each morning. Practical tools each evening. "
            "Loved by God."
        )
        brand = (ROOT / "BRAND.md").read_text(encoding="utf-8")
        home = (ROOT / "templates" / "home.html").read_text(encoding="utf-8")
        evening = (ROOT / "templates" / "evening.html").read_text(encoding="utf-8")
        category = (ROOT / "templates" / "category.html").read_text(encoding="utf-8")
        renderer = (ROOT / "ddb_session_bake.py").read_text(encoding="utf-8")
        self.assertIn("news and Scripture each morning", brand)
        self.assertIn("Field Guide with useful tools and workflows", brand)
        self.assertIn(masthead_subtitle, home)
        self.assertIn(masthead_subtitle, category)
        self.assertIn("MASTHEAD_SUBTITLE", evening)
        for template in (home, evening, category):
            self.assertNotIn('class="product-rhythm"', template)
        self.assertIn("News and Scripture each morning", renderer)
        self.assertIn("Practical tools each evening", renderer)
        self.assertNotIn("—", distinction)

    def test_distribution_metrics_schema_has_provenance_and_outcome_fields(self):
        schema = json.loads(
            (ROOT / "distribution" / "metrics.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(1, schema["properties"]["version"]["const"])
        self.assertEqual(
            ["version", "updatedAt", "baseline", "posts"], schema["required"]
        )
        required_post_fields = set(schema["$defs"]["post"]["required"])
        self.assertTrue(
            {
                "editionId",
                "lead",
                "platformPostId",
                "formatId",
                "idempotencyKey",
                "voiceMode",
                "spendUsd",
                "metrics24h",
                "metrics7d",
            }.issubset(required_post_fields)
        )
        ledger = json.loads(
            (ROOT / "distribution" / "ledger.json").read_text(encoding="utf-8")
        )
        x_baseline = next(
            item for item in ledger["baseline"] if item["platform"] == "x"
        )
        self.assertEqual(5, x_baseline["followers"])
        self.assertEqual([], ledger["posts"])

    def test_x_reply_growth_is_manual_approved_sourced_and_measured(self):
        schema = json.loads(
            (ROOT / "distribution" / "x-replies.schema.json").read_text(
                encoding="utf-8"
            )
        )
        approval_schema = json.loads(
            (ROOT / "distribution" / "x-reply-approval-card.schema.json").read_text(
                encoding="utf-8"
            )
        )
        ledger = json.loads(
            (ROOT / "distribution" / "x-replies.json").read_text(
                encoding="utf-8"
            )
        )
        playbook = (ROOT / "docs" / "X_REPLY_PLAYBOOK.md").read_text(
            encoding="utf-8"
        )
        distribution = (ROOT / "docs" / "DISTRIBUTION_SPEC.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(1, schema["properties"]["version"]["const"])
        self.assertEqual(
            ["version", "updatedAt", "strategyBaseline", "publishedReplies"],
            schema["required"],
        )
        baseline = ledger["strategyBaseline"]
        self.assertEqual(5, baseline["xFollowers"])
        self.assertEqual("credible-account-replies", baseline["primaryAcquisitionChannel"])
        self.assertEqual("manual-ui-per-reply-approval", baseline["mode"])
        self.assertEqual("2026-07-31T21:05:50Z", baseline["cadenceApprovedAt"])
        self.assertFalse(baseline["aiExternalInteractionAuthorized"])
        self.assertEqual("manual-x-search-or-lists", baseline["scoutingMode"])
        self.assertEqual(2, baseline["staffedApprovalWindows"])
        self.assertEqual(4, baseline["dailyPublishedReplyCap"])
        self.assertEqual(3, baseline["sixReplyDayMinimumApprovalWindows"])
        self.assertEqual(9, baseline["breadMinimumScore"])
        self.assertEqual(75, baseline["opportunityPublishThreshold"])
        self.assertEqual(8, baseline["minimumComparedShapeObservations"])
        self.assertEqual(50, baseline["minimumMeasuredRepliesBeforeVolumeScaling"])
        self.assertEqual(
            "blocked_pending_readiness",
            baseline["operationalReadiness"]["status"],
        )
        self.assertEqual([], ledger["publishedReplies"])

        reply = schema["$defs"]["reply"]
        required = set(reply["required"])
        self.assertTrue(
            {
                "parentPostUrl",
                "targetTier",
                "replyShape",
                "qualityRubric",
                "opportunityScore",
                "operationalPriority",
                "approvedBy",
                "approvedAt",
                "approvalExpiresAt",
                "followerCountAtApproval",
                "replyText",
                "supportUrls",
                "automated",
                "postedThrough",
                "policyChecks",
                "operatorChecks",
                "visibilityInspectionAtPublish",
                "targetAuthorInteractions",
                "metricsAtPublish",
                "metrics24h",
                "metrics7d",
            }.issubset(required)
        )
        self.assertEqual("David", reply["properties"]["approvedBy"]["const"])
        self.assertFalse(reply["properties"]["automated"]["const"])
        self.assertEqual(
            "official-x-ui", reply["properties"]["postedThrough"]["const"]
        )
        self.assertEqual(280, reply["properties"]["replyText"]["maxLength"])
        self.assertEqual(1, reply["properties"]["supportUrls"]["minItems"])
        snapshot_required = set(schema["$defs"]["snapshot"]["required"])
        self.assertTrue(
            {
                "userProfileClicks",
                "directFollows",
                "accountProfileVisitsWindow",
                "followerDeltaWindow",
                "visibilityStatus",
                "visibilityInspectionMethod",
            }.issubset(snapshot_required)
        )
        self.assertEqual(1, approval_schema["properties"]["version"]["const"])
        self.assertEqual(
            ["manual-x-search", "manual-x-list"],
            approval_schema["properties"]["scoutingMethod"]["enum"],
        )

        active = " ".join((playbook + "\n" + distribution).lower().split())
        for invariant in (
            "primary near-term acquisition channel",
            "every reply requires david's explicit approval",
            "no api credential is installed for replies",
            "silence is rejection",
            "no more than 60 minutes",
            "no reply asks for engagement",
            "browser scripting, scraping",
            "no more than four published replies per day",
            "at least eight measured observations",
            "at least 50",
        ):
            self.assertIn(invariant, active)

    def test_chronicles_closes_new_intake_and_preserves_notes(self):
        page = (ROOT / "chronicles.html").read_text(encoding="utf-8")

        for current_truth in (
            "The Counter is temporarily closed",
            "Reader slips are resting",
            "New Ask the Baker questions, Letters to the King, and Crumb Board pins are paused",
            "all four export options still work",
            "Existing reviewed reader material remains preserved in past editions",
            "Please do not send reader slips through an old form link",
        ):
            self.assertIn(current_truth, page)
        for forbidden_intake in (
            "formResponse",
            'id="askBtn"',
            'id="kingBtn"',
            'id="pinBtn"',
        ):
            self.assertNotIn(forbidden_intake, page)

    def test_bake_plan_has_no_counter_or_network_input(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        guard = (ROOT / "ddb_workflow_guard.py").read_text(encoding="utf-8")
        self.assertNotIn('"counter.csv"', guard)
        self.assertIn("python3 ddb_workflow_guard.py", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertRegex(workflow, r"(?m)^permissions:\n  contents: read$")
        self.assertIn("  prepare-reader-plan:", workflow)
        self.assertIn("  author-edition:", workflow)
        self.assertIn("  validate-and-publish:", workflow)

        bake_spec = (ROOT / "BAKE.md").read_text(encoding="utf-8")
        normalized = " ".join(bake_spec.split())
        self.assertIn(
            "it has no Counter, network, or public-submission input and never mutates state",
            normalized,
        )

    def test_bake_is_serialized_and_paused_counter_is_not_a_writer(self):
        bake = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        counter = (ROOT / ".github" / "workflows" / "counter-sync.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("group: ddb-main-publisher", bake)
        self.assertIn("queue: max", bake)
        self.assertIn("contents: read", counter)
        for forbidden in (
            "group: ddb-main-publisher",
            "contents: write",
            "git pull --rebase origin main",
            "git push",
        ):
            self.assertNotIn(forbidden, counter)

    def test_private_reader_store_desired_state_is_machine_readable(self):
        contract = json.loads(
            (ROOT / "operations" / "reader-store.contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(2, contract["version"])
        self.assertEqual(
            "local-implementation-authorized-not-provisioned",
            contract["deploymentStatus"],
        )
        self.assertEqual(2, contract["roadmapPhase"])
        self.assertTrue(contract["localImplementationAuthorized"])
        for field in (
            "externalProvisioningAuthorized",
            "deploymentAuthorized",
            "liveDataMigrationAuthorized",
            "publicIntakeActivationAuthorized",
        ):
            self.assertFalse(contract[field])
        self.assertEqual("dedicated-reader-project", contract["projectIsolation"])
        self.assertEqual("reader_private", contract["database"]["storageSchema"])
        self.assertEqual([], contract["database"]["exposedSchemas"])
        self.assertTrue(contract["database"]["rlsEnabled"])
        self.assertEqual([], contract["database"]["browserRolesWithTableAccess"])
        self.assertEqual([], contract["browserSubmission"]["browserSecrets"])
        self.assertEqual([], contract["browserSubmission"]["storedNetworkIdentifiers"])
        self.assertTrue(contract["browserSubmission"]["publicationConsentRequired"])
        self.assertEqual(
            ["pending", "reserved"], contract["browserDeletion"]["erasableStates"]
        )
        self.assertTrue(
            contract["browserDeletion"]["publishingStateUsesPublicRemovalProcess"]
        )
        self.assertFalse(contract["readerBroker"]["mayReturnFullQueue"])
        self.assertEqual("selected-items-only", contract["selection"]["agentVisibility"])
        self.assertEqual(1, contract["selection"]["maximumPerKind"])
        self.assertEqual(120, contract["selection"]["leaseMinutes"])
        self.assertTrue(contract["selection"]["sameLiveEditionRetryIsIdempotent"])
        self.assertIn(
            "deletion-state", contract["selection"]["authorizePublishRevalidates"]
        )
        self.assertFalse(contract["privateHandoff"]["public"])
        self.assertFalse(contract["privateHandoff"]["publicActionsArtifactsAllowed"])
        self.assertLessEqual(contract["privateHandoff"]["maximumRetentionHours"], 6)
        self.assertIn("counter.csv", contract["retiredPublicArtifacts"])
        self.assertIn("published Google Sheet export", contract["retiredPublicArtifacts"])
        self.assertFalse(contract["logging"]["readerBodyAllowed"])
        self.assertFalse(contract["logging"]["readerBylineAllowed"])

        spec = (ROOT / "docs" / "READER_STORE_SPEC.md").read_text(encoding="utf-8")
        for invariant in (
            "FOR UPDATE SKIP LOCKED",
            "returns the waiting queue",
            "public Actions artifacts",
            "History rewriting is a separate destructive privacy operation",
        ):
            self.assertIn(invariant, spec)

    def test_durable_moat_roadmap_authorizes_local_work_only(self):
        contract = json.loads(
            (ROOT / "operations" / "durable-moat-roadmap.contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(1, contract["version"])
        self.assertEqual(
            "active-local-work-external-activation-gated", contract["status"]
        )
        self.assertEqual(1000, contract["firstProofGate"]["qualifiedEngagedReturningPeople"])
        self.assertFalse(contract["firstProofGate"]["isCeiling"])
        self.assertEqual(6, len(contract["moatAssets"]))
        authorization = contract["authorization"]
        for field in (
            "research",
            "strategy",
            "architecture",
            "design",
            "localPrototyping",
            "localImplementation",
            "localTesting",
        ):
            self.assertTrue(authorization[field])
        for field in (
            "publishing",
            "externalDeployment",
            "providerMutation",
            "accountOrResourceCreation",
            "providerTermsAcceptance",
            "credentialInstallation",
            "livePersonalDataCollection",
            "communitySurfaceActivation",
            "newsletterSending",
        ):
            self.assertFalse(authorization[field])
        self.assertEqual(0, authorization["spendAuthorizedUsd"])
        self.assertEqual(list(range(6)), [phase["id"] for phase in contract["phases"]])
        for phase in contract["phases"]:
            self.assertTrue(phase["localWorkAuthorized"])
            self.assertFalse(phase["externalActivationAuthorized"])
        self.assertTrue(contract["privacy"]["personalAndSpiritualDataPrivateByDefault"])
        self.assertFalse(contract["privacy"]["publicSharingDefault"])
        self.assertFalse(contract["moderation"]["privateMessagingIsLaunchRequirement"])

    def test_only_custom_publisher_is_designed_to_bypass_main(self):
        contract = json.loads(
            (ROOT / "operations" / "publishing.contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(1, contract["version"])
        self.assertEqual("provisioning-in-progress", contract["deploymentStatus"])
        self.assertEqual({"contents": "read"}, contract["workflow"]["topLevelPermissions"])
        self.assertEqual("max", contract["workflow"]["concurrencyQueue"])
        self.assertTrue(contract["workflow"]["freshRunnerBoundaryBeforePublisherCredential"])
        self.assertTrue(contract["workflow"]["publisherRequiresUnchangedBaseSha"])
        self.assertFalse(
            contract["workflow"]["publicActionsArtifactsMayContainUnpublishedContent"]
        )

        bypass = [
            identity["name"]
            for identity in contract["identities"]
            if identity["mainRulesetBypass"]
        ]
        self.assertEqual(["ddb-publisher[bot]"], bypass)
        publisher = next(
            identity
            for identity in contract["identities"]
            if identity["name"] == "ddb-publisher[bot]"
        )
        self.assertEqual(
            ["Ironman1421/davidsdailybread"], publisher["repositorySelection"]
        )
        self.assertEqual(
            {"contents": "write", "metadata": "read"},
            publisher["repositoryPermissions"],
        )
        self.assertIn("administration", publisher["forbiddenPermissions"])
        self.assertIn("workflows", publisher["forbiddenPermissions"])

        token = contract["publisherToken"]
        self.assertRegex(token["pinnedCommit"], r"^[0-9a-f]{40}$")
        self.assertTrue(token["mintAfterValidation"])
        self.assertFalse(token["persistCheckoutCredentials"])
        self.assertFalse(token["placeTokenInRemoteUrl"])
        self.assertEqual("production-publish", token["privateKeyEnvironment"])
        self.assertEqual(["main"], token["environmentDeploymentBranches"])
        ruleset = contract["mainRuleset"]
        self.assertTrue(ruleset["requirePullRequest"])
        self.assertEqual(0, ruleset["requiredApprovals"])
        self.assertTrue(ruleset["blockForcePushes"])
        self.assertTrue(ruleset["blockDeletions"])
        self.assertEqual(
            [{
                "name": "ddb-publisher[bot]",
                "actorType": "Integration",
                "mode": "always",
            }],
            ruleset["bypassActors"],
        )

        spec = (ROOT / "docs" / "PUBLISHER_IDENTITY_SPEC.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Required approvals begin at zero", spec)
        self.assertIn("trusted maintainer", spec)
        self.assertIn("fail closed", spec)

    def test_workflow_dependencies_are_immutable(self):
        workflows = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        )
        self.assertNotRegex(workflows, r"uses:\s+[^\s]+@v\d+(?:\s|$)")
        self.assertIn("@anthropic-ai/claude-code@2.1.220", workflows)
        self.assertIn("sha512sum --check", workflows)
        self.assertIn("pytest==8.4.2", workflows)
        self.assertIn("DDB_SITE_DIR: ${{ github.workspace }}", workflows)

    def test_security_scanning_is_wired(self):
        codeql = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(
            encoding="utf-8"
        )
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("language: [python, javascript-typescript]", codeql)
        self.assertIn("security-extended", codeql)
        self.assertIn("package-ecosystem: github-actions", dependabot)

    def test_archive_contract_is_named_consistently_across_active_docs(self):
        for relative in ("README.md", "BAKE.md", "docs/PRODUCT_SPEC.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                self.assertIn("archive.json", text)
                self.assertIn("morning", text.lower())
                self.assertIn("evening", text.lower())


if __name__ == "__main__":
    unittest.main()
