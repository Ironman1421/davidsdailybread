"""Executable privacy and authority gates for the observable-return receipt."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "operations/validate_outreach_observable_return.py"
SPEC = importlib.util.spec_from_file_location("observable_return", VALIDATOR_PATH)
observable_return = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observable_return)


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ObservableReturnImplementationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json(
            "operations/schemas/outreach-observable-return-receipt-v1.schema.json"
        )
        cls.receipt = load_json(
            "operations/outreach-observable-return-validation-receipt.json"
        )
        cls.ledger = load_json("operations/outreach-observable-return-ledger.json")
        cls.campaign = load_json("operations/outreach-campaign.contract.json")
        cls.authority = load_json("measurement/authority.json")
        cls.validator = Draft202012Validator(
            cls.schema, format_checker=FormatChecker()
        )

    def test_closed_receipt_and_current_record_validate(self):
        Draft202012Validator.check_schema(self.schema)
        self.validator.validate(self.receipt)
        self.assertEqual([], observable_return.validate_current())

    def test_receipt_binds_public_post_id_and_exact_edition(self):
        self.assertEqual(
            self.receipt["publicXPostId"],
            self.receipt["publicXPostUrl"].rsplit("/", 1)[-1],
        )
        self.assertEqual(
            self.receipt["editionId"],
            self.receipt["exactEditionUrl"].rsplit("/", 1)[-1][:-5],
        )
        self.assertNotIn("?", self.receipt["exactEditionUrl"])
        self.assertNotIn("#", self.receipt["exactEditionUrl"])

    def test_closed_schema_rejects_personal_or_tracking_fields(self):
        for field, value in (
            ("viewerIdentity", "reader@example.com"),
            ("ipAddress", "192.0.2.1"),
            ("userAgent", "browser"),
            ("referrer", "https://example.com"),
            ("cookie", "identifier"),
            ("trackingToken", "utm_source=x"),
            ("screenshotBytes", "not-allowed"),
        ):
            mutated = deepcopy(self.receipt)
            mutated[field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.validator.validate(mutated)

    def test_schema_rejects_query_fragment_negative_or_fractional_counts(self):
        for url in (
            self.receipt["exactEditionUrl"] + "?utm_source=x",
            self.receipt["exactEditionUrl"] + "#return",
        ):
            mutated = deepcopy(self.receipt)
            mutated["exactEditionUrl"] = url
            with self.subTest(url=url), self.assertRaises(ValidationError):
                self.validator.validate(mutated)
        for value in (-1, 0.5):
            mutated = deepcopy(self.receipt)
            mutated["aggregateValue"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.validator.validate(mutated)

    def test_explicit_zero_is_valid_but_not_a_reader_claim(self):
        mutated = deepcopy(self.receipt)
        mutated["aggregateValue"] = 0
        self.validator.validate(mutated)
        joined = " ".join(mutated["limitations"])
        self.assertIn("not a unique visitor", joined)
        self.assertIn("not a verified page load", joined)
        self.assertIn("not a returning reader", joined)

    def test_campaign_ledger_is_inactive_and_empty(self):
        self.assertEqual("inactive-campaign-not-started", self.ledger["status"])
        self.assertIsNone(self.ledger["campaignActivationReceipt"])
        self.assertEqual([], self.ledger["entries"])

    def test_semantics_fail_closed_on_authority_or_state_drift(self):
        authority = deepcopy(self.authority)
        authority["firstPartyReturnMeasurementAuthorized"] = True
        errors = observable_return.semantic_errors(
            self.receipt, self.ledger, self.campaign, authority
        )
        self.assertIn("official first-party return measurement is activated", errors)

        campaign = deepcopy(self.campaign)
        campaign["campaignWindow"]["status"] = "active"
        errors = observable_return.semantic_errors(
            self.receipt, self.ledger, campaign, self.authority
        )
        self.assertIn("campaign clock has started", errors)

        campaign = deepcopy(self.campaign)
        campaign["externalActions"]["xSourceCardAuthorized"] = True
        errors = observable_return.semantic_errors(
            self.receipt, self.ledger, campaign, self.authority
        )
        self.assertIn("campaign authorizes an external action", errors)

    def test_receipt_stores_hash_not_evidence_bytes(self):
        self.assertTrue(
            self.receipt["restrictedEvidenceRef"].startswith(
                "restricted://ddb-pc-028/x-link-click/"
            )
        )
        self.assertRegex(self.receipt["restrictedEvidenceSha256"], r"^[a-f0-9]{64}$")
        self.assertNotIn("screenshotBytes", self.receipt)


if __name__ == "__main__":
    unittest.main()
