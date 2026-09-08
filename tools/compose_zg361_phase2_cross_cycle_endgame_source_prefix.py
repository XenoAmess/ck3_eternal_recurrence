#!/usr/bin/env python3
"""Compose the three-source LIVE_PENDING prefix for the endgame capture.

The inputs are already-captured evidence: the canonical real 2/4 artifact and
one strict schema-2 incidents/operations entry.  This module never launches or
drives CK3.  It preserves the three input rows byte-for-byte at the JSON value
level and records each capture session's original lineage independently.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Final, Mapping

from zg361_phase2_cross_cycle_endgame_source_capture import (
    CAPTURE_PREFIX_KIND,
    MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
    MULTI_BRANCH_CAPTURE_SCHEMA_VERSION,
    PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
    EndgameSourceCaptureError,
    phase2_source_lineage_set_id,
    preflight_endgame_source_capture_prefix,
)
from zg361_phase2_incident_source_capture_entry import (
    REGISTRY_CAPTURE_ENTRY_KIND,
)
from zhongguo_phase2_source_checkpoint_provider import (
    CHECKPOINT_REQUIRED_HANDLERS,
    LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)


TWO_OF_FOUR_KIND: Final = "zg361_phase2_source_checkpoint_capture_artifact"
TWO_OF_FOUR_READINESS: Final = "captured-real-two-of-four-sources"
DEFAULT_TWO_OF_FOUR_SHA256: Final = (
    "8128750541EE7683EAB5CAD83CFDAF11FCCE47F8017019E3B5541A76F1AD603A"
)
DEFAULT_INCIDENT_SOURCE_CHECKPOINT_SHA256: Final = (
    "76E4FC13825C5A5A654CCD6F321808F627F9A47054C76DDA172B2733CC04884B"
)
DEFAULT_INCIDENT_SEED_LINEAGE_ID: Final = (
    "zg361-phase2-seed-"
    "8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9"
)
_PREFIX_HANDLERS: Final = CHECKPOINT_REQUIRED_HANDLERS[:-1]
_TWO_OF_FOUR_HANDLERS: Final = CHECKPOINT_REQUIRED_HANDLERS[:2]
_SHA256: Final = re.compile(r"^[0-9A-F]{64}$")


class EndgameSourcePrefixComposeError(RuntimeError):
    """Typed RED for invalid immutable inputs or output collisions."""

    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"endgame source prefix RED [{reason_code}]")


def _fail(reason_code: str, **evidence: object) -> None:
    raise EndgameSourcePrefixComposeError(reason_code, evidence)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_json_object(
    value: Mapping[str, object] | Path, *, label: str
) -> tuple[dict[str, object], Path | None]:
    if isinstance(value, Mapping):
        return deepcopy(dict(value)), None
    path = value.expanduser().resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(
            "source_prefix_input_unreadable",
            label=label,
            path=str(path),
            error=f"{type(error).__name__}: {error}",
        )
    if not isinstance(payload, dict):
        _fail(
            "source_prefix_input_invalid",
            label=label,
            path=str(path),
            root_type=type(payload).__name__,
        )
    return payload, path


def _file_record(value: object, *, label: str) -> tuple[dict[str, object], Path]:
    record = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    raw_path = record.get("path")
    path = (
        Path(raw_path).expanduser().resolve()
        if isinstance(raw_path, str) and Path(raw_path).is_absolute()
        else Path()
    )
    sha256 = str(record.get("sha256", "")).upper()
    valid = (
        path.is_absolute()
        and path.is_file()
        and isinstance(record.get("bytes"), int)
        and not isinstance(record.get("bytes"), bool)
        and record.get("bytes") == path.stat().st_size
        and _SHA256.fullmatch(sha256) is not None
        and _sha256_file(path) == sha256
    )
    if not valid:
        _fail("source_prefix_artifact_record_invalid", label=label, record=record)
    return record, path


def _path_record(path: Path) -> dict[str, object]:
    target = path.expanduser().resolve()
    return {
        "path": str(target),
        "bytes": target.stat().st_size,
        "sha256": _sha256_file(target),
    }


def _incident_run_report_provenance(
    report_value: Mapping[str, object] | Path,
    *,
    incident_entry_path: Path | None,
    expected_incident_seed_lineage_id: str,
    expected_incident_source_checkpoint_sha256: str,
) -> dict[str, object]:
    report, report_path = _read_json_object(
        report_value, label="incident-run-report"
    )
    if report_path is None:
        _fail("source_prefix_incident_run_report_locator_required")
    state_preparation = report.get("state_preparation")
    state_preparation = (
        dict(state_preparation)
        if isinstance(state_preparation, Mapping)
        else {}
    )
    source_checkpoint, source_checkpoint_path = _file_record(
        state_preparation.get("source_checkpoint"),
        label="incident-run-source-checkpoint",
    )
    original_after, original_after_path = _file_record(
        report.get("original_source_checkpoint_after"),
        label="incident-run-original-source-checkpoint-after",
    )
    source_entry, source_entry_path = _file_record(
        report.get("source_entry"),
        label="incident-run-source-entry",
    )
    player_switch = report.get("player_switch")
    player_switch = dict(player_switch) if isinstance(player_switch, Mapping) else {}
    switch_lineage = player_switch.get("capture_lineage")
    switch_lineage = (
        dict(switch_lineage) if isinstance(switch_lineage, Mapping) else {}
    )
    switch_record, switch_path = _file_record(
        player_switch.get("player_switch_receipt"),
        label="incident-run-player-switch-receipt",
    )
    switch_payload = switch_record.get("payload")
    switch_payload = (
        dict(switch_payload) if isinstance(switch_payload, Mapping) else {}
    )
    try:
        persisted_switch_payload = json.loads(
            switch_path.read_text(encoding="utf-8-sig")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(
            "source_prefix_incident_run_report_invalid",
            message=f"{type(error).__name__}: {error}",
        )
    expected_source_sha256 = expected_incident_source_checkpoint_sha256.upper()
    report_valid = (
        report.get("result") == "GREEN"
        and report.get("fixture_used") is False
        and report.get("console_used") is False
        and report.get("mcp_only") is True
        and _SHA256.fullmatch(expected_source_sha256) is not None
        and source_checkpoint.get("sha256") == expected_source_sha256
        and original_after.get("sha256") == expected_source_sha256
        and source_checkpoint.get("bytes") == original_after.get("bytes")
        and source_checkpoint_path == original_after_path
        and report.get("original_source_checkpoint_unchanged") is True
        and incident_entry_path is not None
        and source_entry_path == incident_entry_path
        and source_entry == _path_record(incident_entry_path)
        and player_switch.get("result") == "GREEN"
        and switch_lineage.get("seed_lineage_id")
        == expected_incident_seed_lineage_id
        and switch_payload.get("result") == "GREEN"
        and switch_payload.get("seed_lineage_id")
        == expected_incident_seed_lineage_id
        and persisted_switch_payload == switch_payload
    )
    if not report_valid:
        _fail(
            "source_prefix_incident_run_report_invalid",
            report_path=str(report_path),
            expected_incident_seed_lineage_id=(
                expected_incident_seed_lineage_id
            ),
            expected_incident_source_checkpoint_sha256=expected_source_sha256,
            source_checkpoint=source_checkpoint,
            original_source_checkpoint_after=original_after,
            original_source_checkpoint_unchanged=report.get(
                "original_source_checkpoint_unchanged"
            ),
            source_entry=source_entry,
            player_switch=player_switch,
        )
    return {
        "incident_run_report": _path_record(report_path),
        "capture_run_input_checkpoint": source_checkpoint,
        "source_entry": source_entry,
        "player_switch_receipt": {
            key: value for key, value in switch_record.items() if key != "payload"
        },
    }


def _source_artifact_lineage(
    record_value: object,
    *,
    handler: str,
    seed_lineage_id: str,
    expected_entry: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    record, path = _file_record(record_value, label=handler)
    artifact, _ = _read_json_object(path, label=f"{handler}-source-artifact")
    entries = artifact.get("entries")
    lineage = artifact.get("capture_lineage")
    common_valid = (
        artifact.get("schema_version")
        == LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        and artifact.get("result") == "GREEN"
        and artifact.get("evidence_class") == "real_ck3"
        and artifact.get("fixture_used") is False
        and artifact.get("console_used") is False
        and artifact.get("seed_lineage_id") == seed_lineage_id
        and isinstance(lineage, Mapping)
        and lineage.get("seed_lineage_id") == seed_lineage_id
        and isinstance(entries, list)
        and len(entries) == 1
        and entries[0] == expected_entry
    )
    if handler == "capture_promotion_compensation":
        kind_valid = (
            artifact.get("kind") == TWO_OF_FOUR_KIND
            and artifact.get("readiness") == "captured-real-promotion-source"
        )
    else:
        kind_valid = (
            artifact.get("registry_kind")
            == "zg361_projects_metrics_source_checkpoint_registry"
            and artifact.get("readiness") == "captured-real-checkpoint"
        )
    if not (common_valid and kind_valid):
        _fail(
            "source_prefix_source_artifact_invalid",
            handler=handler,
            source_artifact=record,
        )
    return deepcopy(dict(lineage)), record


def compose_endgame_source_capture_prefix(
    two_of_four: Mapping[str, object] | Path,
    incident_entry: Mapping[str, object] | Path,
    incident_run_report: Mapping[str, object] | Path,
    *,
    expected_two_of_four_sha256: str | None = None,
    expected_incident_seed_lineage_id: str = (
        DEFAULT_INCIDENT_SEED_LINEAGE_ID
    ),
    expected_incident_source_checkpoint_sha256: str = (
        DEFAULT_INCIDENT_SOURCE_CHECKPOINT_SHA256
    ),
) -> dict[str, object]:
    """Validate immutable inputs and return the strict three-row prefix."""

    captured, captured_path = _read_json_object(two_of_four, label="two-of-four")
    if expected_two_of_four_sha256 is not None:
        expected = expected_two_of_four_sha256.upper()
        actual = _sha256_file(captured_path) if captured_path is not None else None
        if _SHA256.fullmatch(expected) is None or actual != expected:
            _fail(
                "source_prefix_two_of_four_hash_mismatch",
                path=str(captured_path) if captured_path is not None else None,
                expected_sha256=expected,
                actual_sha256=actual,
            )
    seed_lineage_id = captured.get("seed_lineage_id")
    entries = captured.get("entries")
    observed = (
        tuple(
            row.get("handler") if isinstance(row, Mapping) else None
            for row in entries
        )
        if isinstance(entries, list)
        else ()
    )
    header_valid = (
        captured.get("schema_version")
        == LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        and captured.get("kind") == TWO_OF_FOUR_KIND
        and captured.get("result") == "GREEN"
        and captured.get("readiness") == TWO_OF_FOUR_READINESS
        and captured.get("evidence_class") == "real_ck3"
        and captured.get("fixture_used") is False
        and captured.get("console_used") is False
        and captured.get("canonical_registry_ready") is False
        and captured.get("captured_handlers") == list(_TWO_OF_FOUR_HANDLERS)
        and captured.get("missing_handlers")
        == list(CHECKPOINT_REQUIRED_HANDLERS[2:])
        and isinstance(seed_lineage_id, str)
        and bool(seed_lineage_id)
        and observed == _TWO_OF_FOUR_HANDLERS
    )
    if not header_valid:
        _fail(
            "source_prefix_two_of_four_invalid",
            observed_handlers=list(observed),
            two_of_four=captured,
        )
    assert isinstance(seed_lineage_id, str)
    assert isinstance(entries, list)

    source_artifacts = captured.get("source_artifacts")
    if not isinstance(source_artifacts, Mapping):
        _fail("source_prefix_source_artifacts_missing")
    provenance: list[dict[str, object]] = []
    for raw, handler in zip(entries, _TWO_OF_FOUR_HANDLERS, strict=True):
        assert isinstance(raw, Mapping)
        lineage, record = _source_artifact_lineage(
            source_artifacts.get(handler),
            handler=handler,
            seed_lineage_id=seed_lineage_id,
            expected_entry=raw,
        )
        provenance.append(
            {
                "handler": handler,
                "seed_lineage_id": seed_lineage_id,
                "provenance_source": "source_artifact.capture_lineage",
                "source_artifact": record,
                "capture_lineage": lineage,
            }
        )

    incident, incident_path = _read_json_object(
        incident_entry, label="incident-entry"
    )
    incident_lineage = incident.get("capture_lineage")
    incident_seed_lineage_id = incident.get("seed_lineage_id")
    incident_valid = (
        incident.get("schema_version")
        in (
            LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
            SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        )
        and incident.get("kind") == REGISTRY_CAPTURE_ENTRY_KIND
        and incident.get("result") == "GREEN"
        and incident.get("evidence_class") == "real_ck3"
        and incident.get("handler") == _PREFIX_HANDLERS[-1]
        and isinstance(incident_seed_lineage_id, str)
        and bool(incident_seed_lineage_id)
        and incident_seed_lineage_id == expected_incident_seed_lineage_id
        and isinstance(incident_lineage, Mapping)
        and incident_lineage.get("seed_lineage_id")
        == incident_seed_lineage_id
    )
    if not incident_valid:
        _fail("source_prefix_incident_entry_invalid", incident_entry=incident)
    incident_run_provenance = _incident_run_report_provenance(
        incident_run_report,
        incident_entry_path=incident_path,
        expected_incident_seed_lineage_id=(
            expected_incident_seed_lineage_id
        ),
        expected_incident_source_checkpoint_sha256=(
            expected_incident_source_checkpoint_sha256
        ),
    )
    provenance.append(
        {
            "handler": _PREFIX_HANDLERS[-1],
            "seed_lineage_id": incident_seed_lineage_id,
            "capture_run_input_checkpoint": incident_run_provenance[
                "capture_run_input_checkpoint"
            ],
            "provenance_source": "registry_entry.capture_lineage",
            "run_report": incident_run_provenance["incident_run_report"],
            "source_entry": incident_run_provenance["source_entry"],
            "player_switch_receipt": incident_run_provenance[
                "player_switch_receipt"
            ],
            "capture_lineage": deepcopy(dict(incident_lineage)),
        }
    )
    lineage_set_id = phase2_source_lineage_set_id(provenance)
    prefix = {
        "schema_version": MULTI_BRANCH_CAPTURE_SCHEMA_VERSION,
        "kind": CAPTURE_PREFIX_KIND,
        "result": "LIVE_PENDING",
        "readiness": "live-pending-endgame-source",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "lineage_set_id": lineage_set_id,
        "capture_lineage": {
            "schema_version": 2,
            "kind": PRODUCT_ONLY_MULTI_BRANCH_LINEAGE_KIND,
            "capture_lineage_mode": MULTI_BRANCH_CAPTURE_LINEAGE_MODE,
            "lineage_set_id": lineage_set_id,
            "evidence_class": "real_ck3",
            "fixture_used": False,
            "console_used": False,
            "entry_capture_lineages": provenance,
        },
        "entries": [*deepcopy(entries), deepcopy(incident)],
    }
    try:
        preflight_endgame_source_capture_prefix(
            prefix, expected_lineage_set_id=lineage_set_id
        )
    except EndgameSourceCaptureError as error:
        _fail(
            "source_prefix_composed_manifest_invalid",
            upstream_reason_code=error.reason_code,
            upstream_evidence=error.evidence,
        )
    return prefix


def write_endgame_source_capture_prefix(
    output: Path, prefix: Mapping[str, object]
) -> None:
    target = output.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(prefix, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        _fail("source_prefix_output_already_exists", path=str(target))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--two-of-four", required=True, type=Path)
    parser.add_argument("--incident-entry", required=True, type=Path)
    parser.add_argument("--incident-run-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--expected-two-of-four-sha256",
        default=DEFAULT_TWO_OF_FOUR_SHA256,
    )
    args = parser.parse_args()
    prefix = compose_endgame_source_capture_prefix(
        args.two_of_four,
        args.incident_entry,
        args.incident_run_report,
        expected_two_of_four_sha256=args.expected_two_of_four_sha256,
    )
    write_endgame_source_capture_prefix(args.output, prefix)
    print(
        json.dumps(
            {
                "result": "GREEN",
                "readiness": "live-pending-endgame-source",
                "output": str(args.output.expanduser().resolve()),
                "lineage_set_id": prefix["lineage_set_id"],
                "handlers": [row["handler"] for row in prefix["entries"]],
                "entry_count": len(prefix["entries"]),
                "ck3_launched": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EndgameSourcePrefixComposeError as error:
        print(json.dumps(error.evidence, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1)


__all__ = [
    "DEFAULT_TWO_OF_FOUR_SHA256",
    "EndgameSourcePrefixComposeError",
    "compose_endgame_source_capture_prefix",
    "write_endgame_source_capture_prefix",
]
