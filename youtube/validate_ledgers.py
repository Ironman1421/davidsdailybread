#!/usr/bin/env python3
"""Validate the checked-in YouTube pilot ledgers and their shared semantics."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


YOUTUBE = Path(__file__).resolve().parent
SCHEMAS = YOUTUBE / "schemas"
LEDGERS = YOUTUBE / "ledgers"
SCHEMA_LEDGER_PAIRS = {
    "claim-evidence": (
        SCHEMAS / "claim-evidence.schema.json",
        LEDGERS / "claim-evidence.json",
    ),
    "asset-provenance": (
        SCHEMAS / "asset-provenance.schema.json",
        LEDGERS / "asset-provenance.json",
    ),
    "corrections": (
        SCHEMAS / "corrections.schema.json",
        LEDGERS / "corrections.json",
    ),
    "video-receipts": (
        SCHEMAS / "video-receipts.schema.json",
        LEDGERS / "video-receipts.json",
    ),
    "experiment": (
        SCHEMAS / "experiment.schema.json",
        LEDGERS / "experiment.json",
    ),
}


class YoutubeLedgerValidationError(ValueError):
    """Raised when a YouTube ledger contract is internally inconsistent."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _duplicates(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def _format_path(parts: Any) -> str:
    return ".".join(str(part) for part in parts) or "<root>"


def validate_schema_and_ledger(
    name: str, schema: dict[str, Any], ledger: dict[str, Any]
) -> None:
    """Check a Draft 2020-12 schema itself, then validate its real ledger."""
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(ledger),
        key=lambda error: tuple(str(part) for part in error.path),
    )
    if errors:
        details = "; ".join(
            f"{_format_path(error.path)}: {error.message}" for error in errors
        )
        raise YoutubeLedgerValidationError(f"{name} ledger is invalid: {details}")


def semantic_errors(ledgers: dict[str, dict[str, Any]]) -> list[str]:
    """Return cross-record errors JSON Schema cannot express safely."""
    errors: list[str] = []
    experiment_ledger = ledgers["experiment"]
    constraints = experiment_ledger["constraints"]
    platform_baseline = experiment_ledger["platformBaseline"]
    experiments = experiment_ledger["experiments"]
    gates = experiment_ledger["gateEvaluations"]

    if (
        experiment_ledger["operatingState"] == "disabled"
        or platform_baseline["metricsStatus"] != "captured"
    ):
        for field in ("publishingEnabled", "externalAccountMutationAuthorized"):
            if constraints[field]:
                errors.append(
                    f"constraints.{field} must remain false while the pilot is "
                    "disabled or its metrics baseline is not captured"
                )

    experiment_ids = [experiment["experimentId"] for experiment in experiments]
    for duplicate in _duplicates(experiment_ids):
        errors.append(f"duplicate experimentId: {duplicate}")

    experiments_by_id: dict[str, dict[str, Any]] = {}
    cells_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    all_cell_ids: list[str] = []
    all_assignment_ids: list[str] = []
    total_exposure = 0.0

    for experiment in experiments:
        experiment_id = experiment["experimentId"]
        experiments_by_id.setdefault(experiment_id, experiment)
        cells = experiment["cells"]
        cell_ids = [cell["cellId"] for cell in cells]
        combinations = [f'{cell["franchise"]}:{cell["voiceMode"]}' for cell in cells]

        for duplicate in _duplicates(cell_ids):
            errors.append(f"{experiment_id} has duplicate cellId: {duplicate}")
        for duplicate in _duplicates(combinations):
            errors.append(f"{experiment_id} has duplicate cell combination: {duplicate}")
        if set(combinations) != set(constraints["plannedCellDefinitions"]):
            errors.append(
                f"{experiment_id} cells do not exactly match plannedCellDefinitions"
            )

        for cell in cells:
            cell_id = cell["cellId"]
            all_cell_ids.append(cell_id)
            cells_by_id.setdefault(cell_id, (experiment_id, cell))

        assignment_ids = [
            assignment["assignmentId"] for assignment in experiment["assignments"]
        ]
        all_assignment_ids.extend(assignment_ids)
        for duplicate in _duplicates(assignment_ids):
            errors.append(f"{experiment_id} has duplicate assignmentId: {duplicate}")
        for assignment in experiment["assignments"]:
            if assignment["assignedCellId"] not in set(cell_ids):
                errors.append(
                    f'{assignment["assignmentId"]} references a cell outside '
                    f"{experiment_id}: {assignment['assignedCellId']}"
                )

        expected_exposure = (
            experiment["externalCommittedCostUsd"]
            + experiment["externalPaidCostUsd"]
        )
        exposure = experiment["externalTotalExposureUsd"]
        total_exposure += exposure
        if not math.isclose(exposure, expected_exposure, rel_tol=0, abs_tol=1e-9):
            errors.append(
                f"{experiment_id} externalTotalExposureUsd must equal committed plus paid cost"
            )
        if exposure > 0:
            if not constraints["spendAuthorized"]:
                errors.append(f"{experiment_id} records cost without spend authorization")
            if not experiment["spendAuthorizationReferences"]:
                errors.append(
                    f"{experiment_id} records cost without a spend authorization reference"
                )
            if exposure > constraints["authorizedSpendUsd"]:
                errors.append(
                    f"{experiment_id} exposure exceeds the authorized pilot spend"
                )

    for duplicate in _duplicates(all_cell_ids):
        errors.append(f"cellId is reused across experiments: {duplicate}")
    for duplicate in _duplicates(all_assignment_ids):
        errors.append(f"assignmentId is reused across experiments: {duplicate}")

    if total_exposure > constraints["authorizedSpendUsd"]:
        errors.append("combined experiment exposure exceeds authorizedSpendUsd")
    if total_exposure > constraints["externalPlanningCeilingUsd"]:
        errors.append("combined experiment exposure exceeds externalPlanningCeilingUsd")

    gate_ids = [gate["gateId"] for gate in gates]
    for duplicate in _duplicates(gate_ids):
        errors.append(f"duplicate gateId: {duplicate}")

    for gate in gates:
        gate_id = gate["gateId"]
        experiment_id = gate["experimentId"]
        experiment = experiments_by_id.get(experiment_id)
        if experiment is None:
            errors.append(f"{gate_id} references nonexistent experiment: {experiment_id}")
            continue

        metric_cell_ids = [metric["cellId"] for metric in gate["cellMetrics"]]
        for duplicate in _duplicates(metric_cell_ids):
            errors.append(f"{gate_id} compares duplicate cell: {duplicate}")

        comparison_modes: set[str] = set()
        for cell_id in metric_cell_ids:
            cell_record = cells_by_id.get(cell_id)
            if cell_record is None or cell_record[0] != experiment_id:
                errors.append(
                    f"{gate_id} references nonexistent cell in {experiment_id}: {cell_id}"
                )
                continue
            cell = cell_record[1]
            if cell["franchise"] != gate["franchise"]:
                errors.append(
                    f"{gate_id} references cell {cell_id} from the wrong franchise"
                )
            comparison_modes.add(cell["voiceMode"])

        if comparison_modes != {"recurring_human_narrator", "caption_only"}:
            errors.append(f"{gate_id} does not compare both voice-mode cells")

    videos = ledgers["video-receipts"]["videos"]
    for duplicate in _duplicates([video["videoRecordId"] for video in videos]):
        errors.append(f"duplicate videoRecordId: {duplicate}")
    passing_gate_ids = {gate["gateId"] for gate in gates if gate["result"] == "pass"}
    for video in videos:
        disclosure = video["alteredSyntheticDisclosure"]
        if (
            disclosure["realisticAlteredOrSyntheticContentPresent"]
            and disclosure["studioSelection"] != "Yes"
        ):
            errors.append(
                f'{video["videoRecordId"]} has altered or synthetic content but '
                "records Studio selection No"
            )
        if video["durationClass"] == "long_form":
            gate_id = video["shortWinnerGateReceiptId"]
            if gate_id not in passing_gate_ids:
                errors.append(
                    f'{video["videoRecordId"]} references a nonexistent or nonpassing '
                    f"Short gate: {gate_id}"
                )

    return errors


def validate_youtube_ledgers() -> dict[str, dict[str, Any]]:
    """Validate all five checked-in schema/ledger pairs and shared semantics."""
    ledgers: dict[str, dict[str, Any]] = {}
    for name, (schema_path, ledger_path) in SCHEMA_LEDGER_PAIRS.items():
        schema = load_json(schema_path)
        ledger = load_json(ledger_path)
        validate_schema_and_ledger(name, schema, ledger)
        ledgers[name] = ledger

    errors = semantic_errors(ledgers)
    if errors:
        raise YoutubeLedgerValidationError(
            "YouTube ledger semantics are invalid:\n- " + "\n- ".join(errors)
        )
    return ledgers


if __name__ == "__main__":
    validate_youtube_ledgers()
    print("Validated five YouTube Draft 2020-12 schema/ledger pairs and semantics.")
