#!/usr/bin/env python3
"""No-launch preflight for the strict Incident source-capture entry."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Mapping

import run_zhongguo_acceptance as runner
from zg361_phase2_incident_checkpoint_seam import (
    IncidentCheckpointSeamError,
    validate_received_self_incident_checkpoint_receipt,
)
from zg361_phase2_incident_source_capture_entry import (
    LIVE_CAPTURE_KIND,
    REGISTRY_CAPTURE_ENTRY_KIND,
    IncidentSourceCaptureEntryError,
    build_schema2_incident_registry_capture_entry,
    wait_for_and_capture_incident_source_checkpoint,
)
from zhongguo_phase2_source_checkpoint_provider import (
    INCIDENT_STRICT_RECEIPT_FIELD,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "run_zhongguo_acceptance.py"


def _load(path: Path) -> dict[str, object]:
    target = path.expanduser().resolve()
    try:
        value = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IncidentSourceCaptureEntryError(
            "incident_source_capture_artifact_unreadable",
            {
                "path": str(target),
                "message": f"{type(error).__name__}: {error}",
            },
        ) from error
    if not isinstance(value, dict):
        raise IncidentSourceCaptureEntryError(
            "incident_source_capture_artifact_not_object",
            {"path": str(target), "root_type": type(value).__name__},
        )
    return value


def _file_record_matches(
    value: object,
    *,
    expected_path: Path | None = None,
    expected_payload: Mapping[str, object] | None = None,
) -> bool:
    record = dict(value) if isinstance(value, Mapping) else {}
    raw_path = record.get("path")
    path = (
        Path(raw_path).expanduser().resolve()
        if isinstance(raw_path, str) and Path(raw_path).is_absolute()
        else None
    )
    if path is None or not path.is_file():
        return False
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest().upper()
    if not (
        record.get("bytes") == len(payload)
        and str(record.get("sha256", "")).upper() == digest
        and (expected_path is None or path == expected_path.resolve())
    ):
        return False
    if expected_payload is None:
        return True
    try:
        observed = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError):
        return False
    return observed == dict(expected_payload)


def _validate_live_artifacts(
    capture_report_path: Path,
    registry_entry_path: Path,
) -> dict[str, object]:
    report = _load(capture_report_path)
    entry = _load(registry_entry_path)
    strict = entry.get(INCIDENT_STRICT_RECEIPT_FIELD)
    strict = dict(strict) if isinstance(strict, Mapping) else {}
    seed_lineage_id = strict.get("seed_lineage_id")
    try:
        summary = validate_received_self_incident_checkpoint_receipt(
            strict,
            expected_seed_lineage_id=(
                str(seed_lineage_id)
                if isinstance(seed_lineage_id, str)
                else None
            ),
        )
        projected = build_schema2_incident_registry_capture_entry(
            strict,
            expected_seed_lineage_id=str(seed_lineage_id),
        )
    except (IncidentCheckpointSeamError, IncidentSourceCaptureEntryError) as error:
        reason_code = getattr(error, "reason_code", type(error).__name__)
        raise IncidentSourceCaptureEntryError(
            "incident_source_capture_live_artifact_invalid",
            {"upstream_reason_code": reason_code},
        ) from error
    checks = {
        "capture_report_green": report.get("result") == "GREEN",
        "capture_report_kind": report.get("kind") == LIVE_CAPTURE_KIND,
        "capture_report_readiness": report.get("readiness")
        == "captured-real-checkpoint",
        "provider_ui_observed": report.get("provider_observed") is True
        and report.get("ui_state_verified") is True,
        "no_fixture_console_or_action": report.get("fixture_used") is False
        and report.get("console_used") is False
        and report.get("gameplay_action_executed") is False,
        "ack_not_state_evidence": report.get(
            "action_ack_used_as_state_evidence"
        )
        is False,
        "registry_entry_schema2": entry.get("schema_version")
        == SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "registry_entry_kind": entry.get("kind")
        == REGISTRY_CAPTURE_ENTRY_KIND,
        "registry_entry_exact_projection": entry == projected,
        "capture_report_strict_receipt_record": _file_record_matches(
            report.get("strict_receipt"), expected_payload=strict
        ),
        "capture_report_registry_entry_record": _file_record_matches(
            report.get("schema2_registry_capture_entry"),
            expected_path=registry_entry_path.expanduser().resolve(),
            expected_payload=entry,
        ),
        "capture_report_checkpoint_binding": report.get("checkpoint")
        == entry.get("checkpoint"),
        "capture_report_identity_binding": report.get(
            "player_character_id"
        )
        == report.get("subject_character_id")
        == report.get("event_root_character_id")
        == summary.get("player_character_id")
        and report.get("owner_character_id")
        == report.get("notice_owner_character_id")
        == summary.get("owner_character_id"),
        "capture_report_option_and_frame": report.get("option_number") == 1
        and report.get("option_shown") is True
        and report.get("option_enabled") is True
        and report.get("provider_ui_same_frame") is True,
        "capture_report_lineage_binding": report.get("seed_lineage_id")
        == summary.get("seed_lineage_id")
        and report.get("capture_lineage") == summary.get("capture_lineage")
        and entry.get("seed_lineage_id") == summary.get("seed_lineage_id")
        and entry.get("capture_lineage") == summary.get("capture_lineage"),
        "strict_player_root_subject": summary.get("player_character_id")
        == summary.get("subject_character_id"),
        "strict_notice_owner_distinct": summary.get("owner_character_id")
        != summary.get("player_character_id"),
    }
    if not all(checks.values()):
        raise IncidentSourceCaptureEntryError(
            "incident_source_capture_live_artifact_invalid",
            {"checks": checks},
        )
    return {
        "result": "GREEN",
        "qualified_checkpoint_found": True,
        "checks": checks,
        "checkpoint": summary["checkpoint"],
        "owner_character_id": summary["owner_character_id"],
        "player_character_id": summary["player_character_id"],
        "date_raw": summary["date_raw"],
    }


def run_preflight(
    capture_report_path: Path | None = None,
    registry_entry_path: Path | None = None,
) -> dict[str, object]:
    runner_source = RUNNER_PATH.read_text(encoding="utf-8-sig")
    capture_source = inspect.getsource(
        wait_for_and_capture_incident_source_checkpoint
    )
    main_parameters = inspect.signature(runner.main).parameters
    cell_parameters = inspect.signature(runner.run_cell).parameters
    checks = {
        "formal_runtime_mode_registered": (
            "phase2_incident_source_checkpoint_capture" in main_parameters
            and "phase2_incident_source_checkpoint_capture" in cell_parameters
            and '"--phase2-incident-source-checkpoint-capture"'
            in runner_source
        ),
        "formal_runner_calls_capture": (
            "wait_for_and_capture_incident_source_checkpoint("
            in runner_source
            and "focused_incident_source_capture=(" in runner_source
        ),
        "managed_wait_capture_callable": callable(
            wait_for_and_capture_incident_source_checkpoint
        ),
        "schema2_registry_contract": (
            SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION == 2
        ),
        "product_only_runtime": (
            "or phase2_incident_source_checkpoint_capture" in runner_source
        ),
        "no_console_fixture_or_action_path": (
            '"gameplay_action_executed": False' in capture_source
            and '"action_ack_used_as_state_evidence": False'
            in capture_source
            and "select_event_option" not in capture_source
            and "execute_step" not in capture_source
        ),
    }
    failed = [name for name, value in checks.items() if value is not True]
    paths_paired = (capture_report_path is None) == (
        registry_entry_path is None
    )
    if not paths_paired:
        failed.append("live_artifact_paths_paired")
    if capture_report_path is None or registry_entry_path is None:
        live = {
            "result": "RED",
            "reason_code": "strict_incident_source_checkpoint_pending",
            "qualified_checkpoint_found": False,
        }
    else:
        try:
            live = _validate_live_artifacts(
                capture_report_path, registry_entry_path
            )
        except IncidentSourceCaptureEntryError as error:
            live = dict(error.evidence)
            live["qualified_checkpoint_found"] = False
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_incident_source_capture_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": "static-ready-live-pending",
        "ck3_started": False,
        "service_instantiated": False,
        "gameplay_action_executed": False,
        "gameplay_result_claimed": False,
        "checks": checks,
        "failed_checks": failed,
        "live_checkpoint": live,
        "live_gate_ready": live.get("result") == "GREEN",
        "formal_execute_requires": [
            "--phase2-incident-source-checkpoint-capture",
            "--phase2-frontend-first-load-save-name <REAL_PRODUCT_SAVE>",
        ],
        "capture_outputs": [
            "cell/05_phase2_incident_source_checkpoint_capture.json",
            "cell/incident-source-checkpoint/strict-receipt.json",
            "cell/incident-source-checkpoint/schema2-registry-entry.json",
            "cell/incident-source-checkpoint/checkpoints/*.ck3",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-report", type=Path)
    parser.add_argument("--registry-entry", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = run_preflight(
        arguments.capture_report,
        arguments.registry_entry,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.output is not None:
        output = arguments.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
