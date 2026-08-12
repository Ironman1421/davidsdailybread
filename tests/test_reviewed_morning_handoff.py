import json
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest

from ddb_morning_handoff import (
    MorningHandoffValidationError,
    fetch_packet,
    upload_packet,
    validate_candidate_ledger,
    validate_packet,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/ddb-reviewed-morning-handoff.valid.json"


def load_packet():
    return json.loads(FIXTURE.read_text())


def test_valid_reviewed_packet_is_date_bound_early_and_nonpublishing():
    packet = load_packet()
    validate_packet(
        packet,
        expected_date="2026-08-05",
        now=datetime(2026, 8, 5, 11, 30, tzinfo=timezone.utc),
    )
    assert packet["authority"]["publicationApproved"] is False


def test_every_ledger_candidate_and_must_review_signal_needs_a_disposition():
    packet = load_packet()
    packet["decisions"]["hold"] = []
    with pytest.raises(MorningHandoffValidationError) as exc:
        validate_packet(packet, now=datetime(2026, 8, 5, 11, 30, tzinfo=timezone.utc))
    assert "every ledger and gap candidate" in str(exc.value)
    assert "every must-review candidate" in str(exc.value)


def test_august_5_muse_code_has_explicit_morning_disposition():
    packet = load_packet()
    all_decisions = sum(packet["decisions"].values(), [])
    muse = next(item for item in all_decisions if item["id"] == "xmc-e148edfe52ba969259f2")
    assert muse["mustReview"] is True
    assert muse["decision"] in {"selected", "hold", "reject"}
    assert muse["scores"]["ruleVersion"] == "morning-editorial-v1"


def test_selected_story_must_clear_distinct_morning_score():
    packet = load_packet()
    packet["decisions"]["selected"][0]["scores"]["freshness"] = 20
    packet["decisions"]["selected"][0]["scores"]["total"] = 72
    packet["decisions"]["selected"][0]["scores"]["eligible"] = False
    with pytest.raises(MorningHandoffValidationError, match="eligible for a selected story"):
        validate_packet(packet, now=datetime(2026, 8, 5, 11, 30, tzinfo=timezone.utc))


def test_late_packet_is_rejected_before_bake():
    packet = load_packet()
    packet["reviewedAt"] = "2026-08-05T11:40:00Z"
    with pytest.raises(MorningHandoffValidationError, match="before the 4:40 AM"):
        validate_packet(packet, now=datetime(2026, 8, 5, 11, 41, tzinfo=timezone.utc))


def test_gap_sweep_must_cover_all_three_beats():
    packet = load_packet()
    packet["verification"]["gapSweep"]["science"]["completed"] = False
    with pytest.raises(MorningHandoffValidationError, match="science.completed"):
        validate_packet(packet, now=datetime(2026, 8, 5, 11, 30, tzinfo=timezone.utc))


def test_fetch_fails_closed_to_unavailable_record(tmp_path):
    output = tmp_path / "morning.json"
    with mock.patch.dict("os.environ", {"TOKEN": "test"}), mock.patch(
        "ddb_morning_handoff.request.urlopen", side_effect=OSError("offline")
    ):
        assert fetch_packet(
            "https://example.com",
            "2026-08-05",
            output,
            "TOKEN",
            now=datetime(2026, 8, 5, 11, 30, tzinfo=timezone.utc),
        ) is False
    fallback = json.loads(output.read_text())
    assert fallback["available"] is False
    assert fallback["targetEdition"]["slot"] == "morning"


def test_upload_validates_and_uses_existing_private_store(tmp_path):
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(load_packet()))

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return b'{"packetId":"2026-08-05-morning","stored":true}'

    with mock.patch.dict(
        "os.environ", {"WRITE": "private-write", "SITES": "private-sites"}
    ), mock.patch("ddb_morning_handoff.request.urlopen", return_value=Response()) as urlopen:
        receipt = upload_packet(
            "https://example.com",
            packet_path,
            "WRITE",
            "SITES",
            now=datetime(2026, 8, 5, 11, 30, tzinfo=timezone.utc),
        )
    assert receipt["stored"] is True
    sent = urlopen.call_args.args[0]
    assert sent.method == "POST"
    assert sent.full_url == "https://example.com/api/ddb-handoff"


def test_candidate_ledger_requires_no_paid_read_and_deterministic_order():
    ledger = json.loads(
        (ROOT / "tests/fixtures/x-manager-morning-candidate-ledger.muse-code-2026-08-05.json").read_text()
    )
    validate_candidate_ledger(ledger, expected_date="2026-08-05")
    muse = next(item for item in ledger["candidates"] if "Muse Code" in item["title"])
    assert muse["candidateId"] == "xmc-e148edfe52ba969259f2"
    assert muse["rank"] == 1
    assert muse["scores"]["total"] == 79
    assert muse["mustReview"] is True
    ledger["boundedInputs"]["newPaidRunTriggered"] = True
    with pytest.raises(MorningHandoffValidationError, match="must be false"):
        validate_candidate_ledger(ledger)


def test_evening_editorial_fit_contract_remains_unchanged():
    contract = json.loads((ROOT / "operations/tools-workflows-research-handoff.contract.json").read_text())
    assert contract["ddbCombinedReview"]["editorialFit"]["version"] == "editorial-fit-v1"


def test_daily_workflow_fetches_morning_packet_and_prompt_forbids_discovery():
    workflow = (ROOT / ".github/workflows/ddb-bake.yml").read_text()
    step = workflow.split("- name: Prepare DDB-reviewed morning handoff", 1)[1].split(
        "- name: Install Claude Code", 1
    )[0]
    assert "slot == 'morning'" in step
    assert "mode == 'daily'" in step
    assert "ddb_morning_handoff.py fetch" in step
    assert "ddb-reviewed-morning-handoff.json" in step
    assert "A missing, unavailable, invalid, stale, late, or incomplete daily morning packet fails closed" in workflow
    assert "Do not discover, add, substitute, rerank" in workflow


def test_bake_contract_has_no_open_ended_daily_morning_discovery():
    bake = (ROOT / "BAKE.md").read_text()
    morning = bake.split("**2. Consume reviewed research (daily morning).**", 1)[1].split(
        "**3. Select Scripture pairings", 1
    )[0]
    normalized = " ".join(morning.split())
    assert "Do not search for more candidates, refresh X Manager" in normalized
    assert "Daily morning has no open-ended research fallback" in normalized
    assert "authority.publicationApproved: false" in normalized


def test_morning_contract_and_schema_are_json_and_distinct_from_evening():
    contract = json.loads((ROOT / "operations/morning-research-handoff.contract.json").read_text())
    schema = json.loads((ROOT / "operations/schemas/ddb-reviewed-morning-handoff-v1.schema.json").read_text())
    assert contract["ddbReview"]["scoringRule"] == "morning-editorial-v1"
    assert contract["bake"]["openEndedDiscoveryAllowed"] is False
    assert schema["properties"]["schemaVersion"]["const"] == "ddb-reviewed-morning-handoff-v1"
