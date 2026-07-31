#!/usr/bin/env python3
"""Executable schema and cross-record checks for manual X reply operations."""

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
PACIFIC = ZoneInfo("America/Los_Angeles")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def assert_score_totals(item):
    bread = item["qualityRubric"]
    assert bread["total"] == sum(
        bread[key]
        for key in (
            "buildsConversation",
            "relevant",
            "evidenceGrounded",
            "appropriateVoice",
            "distinct",
        )
    )

    opportunity = item["opportunityScore"]
    assert opportunity["total"] == sum(
        opportunity[key]
        for key in (
            "relevance",
            "incrementalValue",
            "sourceConfidence",
            "conversationTiming",
            "targetCredibility",
            "operationalSafety",
        )
    )


def assert_approval_card_semantics(card):
    assert_score_totals(card)
    assert card["lengthCharacters"] == len(card["draft"])
    observed = parse_time(card["parentObservedAt"])
    expires = parse_time(card["approvalExpiresAt"])
    assert observed < expires <= observed + timedelta(minutes=60)


def assert_ledger_semantics(ledger):
    baseline = ledger["strategyBaseline"]
    assert baseline["aiExternalInteractionAuthorized"] is False
    if baseline["dailyPublishedReplyCap"] == 6:
        assert baseline["staffedApprovalWindows"] >= 3

    daily_counts = Counter()
    by_target = defaultdict(list)
    for reply in ledger["publishedReplies"]:
        assert_score_totals(reply)
        discovered = parse_time(reply["discoveredAt"])
        approved = parse_time(reply["approvedAt"])
        expires = parse_time(reply["approvalExpiresAt"])
        published = parse_time(reply["publishedAt"])
        assert discovered <= approved <= published <= expires
        assert expires <= discovered + timedelta(minutes=60)

        pacific_day = published.astimezone(PACIFIC).date()
        daily_counts[pacific_day] += 1
        by_target[reply["targetAccount"].lower()].append(published)

    assert all(
        count <= baseline["dailyPublishedReplyCap"]
        for count in daily_counts.values()
    )

    minimum_gap = timedelta(
        hours=baseline["targetMinimumHoursBetweenProactiveReplies"]
    )
    rolling_window = timedelta(days=14)
    maximum_in_window = baseline["targetMaximumProactiveRepliesPer14Days"]
    for timestamps in by_target.values():
        timestamps.sort()
        for previous, current in zip(timestamps, timestamps[1:]):
            assert current - previous >= minimum_gap
        for start_index, start in enumerate(timestamps):
            count = sum(
                start <= timestamp < start + rolling_window
                for timestamp in timestamps[start_index:]
            )
            assert count <= maximum_in_window


class XReplyContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger_schema = load_json(
            ROOT / "distribution" / "x-replies.schema.json"
        )
        cls.card_schema = load_json(
            ROOT / "distribution" / "x-reply-approval-card.schema.json"
        )
        cls.ledger_validator = Draft202012Validator(
            cls.ledger_schema, format_checker=FormatChecker()
        )
        cls.card_validator = Draft202012Validator(
            cls.card_schema, format_checker=FormatChecker()
        )
        cls.valid_ledger = load_json(
            FIXTURES / "x-reply-ledger.valid.json"
        )
        cls.valid_card = load_json(
            FIXTURES / "x-reply-approval-card.valid.json"
        )

    def test_schemas_and_current_empty_ledger_validate(self):
        Draft202012Validator.check_schema(self.ledger_schema)
        Draft202012Validator.check_schema(self.card_schema)
        self.ledger_validator.validate(
            load_json(ROOT / "distribution" / "x-replies.json")
        )

    def test_synthetic_valid_fixtures_validate_semantically(self):
        self.card_validator.validate(self.valid_card)
        self.ledger_validator.validate(self.valid_ledger)
        assert_approval_card_semantics(self.valid_card)
        assert_ledger_semantics(self.valid_ledger)

    def test_schema_rejects_automation_and_failed_safety_checks(self):
        for path, value in (
            (("publishedReplies", 0, "automated"), True),
            (("publishedReplies", 0, "operatorChecks", "browserScriptingAbsent"), False),
            (("publishedReplies", 0, "operatorChecks", "scrapingAbsent"), False),
            (("publishedReplies", 0, "profileConversionReadiness", "canonicalSiteLink"), False),
        ):
            candidate = deepcopy(self.valid_ledger)
            cursor = candidate
            for key in path[:-1]:
                cursor = cursor[key]
            cursor[path[-1]] = value
            with self.subTest(path=path):
                with self.assertRaises(ValidationError):
                    self.ledger_validator.validate(candidate)

    def test_schema_rejects_weak_scores_missing_conversion_metrics_and_bad_staffing(self):
        weak_bread = deepcopy(self.valid_ledger)
        weak_bread["publishedReplies"][0]["qualityRubric"]["total"] = 8
        with self.assertRaises(ValidationError):
            self.ledger_validator.validate(weak_bread)

        weak_opportunity = deepcopy(self.valid_ledger)
        weak_opportunity["publishedReplies"][0]["opportunityScore"]["total"] = 74
        with self.assertRaises(ValidationError):
            self.ledger_validator.validate(weak_opportunity)

        no_direct_follows = deepcopy(self.valid_ledger)
        del no_direct_follows["publishedReplies"][0]["metrics24h"]["directFollows"]
        with self.assertRaises(ValidationError):
            self.ledger_validator.validate(no_direct_follows)

        no_profile_clicks = deepcopy(self.valid_ledger)
        del no_profile_clicks["publishedReplies"][0]["metrics24h"]["userProfileClicks"]
        with self.assertRaises(ValidationError):
            self.ledger_validator.validate(no_profile_clicks)

        unstaffed_six = deepcopy(self.valid_ledger)
        unstaffed_six["strategyBaseline"]["dailyPublishedReplyCap"] = 6
        with self.assertRaises(ValidationError):
            self.ledger_validator.validate(unstaffed_six)

    def test_card_rejects_automated_scouting_and_unsubstantiated_verification(self):
        automated = deepcopy(self.valid_card)
        automated["scoutingMethod"] = "automated-browser"
        with self.assertRaises(ValidationError):
            self.card_validator.validate(automated)

        unsubstantiated = deepcopy(self.valid_card)
        unsubstantiated["targetVerification"]["claimBasis"] = "employer_source"
        with self.assertRaises(ValidationError):
            self.card_validator.validate(unsubstantiated)

    def test_semantic_checks_reject_score_math_and_expired_approval(self):
        bad_math = deepcopy(self.valid_card)
        bad_math["opportunityScore"]["incrementalValue"] -= 1
        with self.assertRaises(AssertionError):
            assert_approval_card_semantics(bad_math)

        expired = deepcopy(self.valid_card)
        expired["approvalExpiresAt"] = "2026-07-31T16:01:00Z"
        with self.assertRaises(AssertionError):
            assert_approval_card_semantics(expired)

    def test_semantic_checks_enforce_four_per_day_and_target_frequency(self):
        too_many = deepcopy(self.valid_ledger)
        original = too_many["publishedReplies"][0]
        for index in range(2, 6):
            reply = deepcopy(original)
            reply["replyId"] = f"XR-20260731-{index:03d}"
            reply["targetAccount"] = f"@Fixture{index}"
            reply["replyPostId"] = f"100000000000000000{index}"
            reply["replyUrl"] = (
                f"https://x.com/Fixture{index}/status/100000000000000000{index}"
            )
            too_many["publishedReplies"].append(reply)
        self.ledger_validator.validate(too_many)
        with self.assertRaises(AssertionError):
            assert_ledger_semantics(too_many)

        repeated_target = deepcopy(self.valid_ledger)
        repeat = deepcopy(original)
        repeat["replyId"] = "XR-20260802-001"
        repeat["replyPostId"] = "1000000000000000009"
        repeat["replyUrl"] = "https://x.com/DDBFixture/status/1000000000000000009"
        for field in ("discoveredAt", "approvedAt", "approvalExpiresAt", "publishedAt"):
            repeat[field] = (
                parse_time(repeat[field]) + timedelta(hours=48)
            ).isoformat().replace("+00:00", "Z")
        repeated_target["publishedReplies"].append(repeat)
        self.ledger_validator.validate(repeated_target)
        with self.assertRaises(AssertionError):
            assert_ledger_semantics(repeated_target)


if __name__ == "__main__":
    unittest.main()
