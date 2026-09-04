#!/usr/bin/env python3
"""No-launch preflight for the ``incidents-operations`` gameplay cell.

The reusable action cell already owns the live query -> action -> independent
Incident-provider postcondition sequence.  This preflight binds that cell to
the exact snapshot source contract and the existing Incident-X full-entry
artifact, then describes the one received-self source checkpoint still needed
for a real run.  It never launches CK3 and never promotes an ACK to evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Final, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_incident_action_cell import (  # noqa: E402
    INCIDENT_ACTION_CELL_ID,
    INCIDENT_PROFILES,
    INCIDENT_RESULT_EVENT_DEFINITION_KEY,
    INCIDENT_RESULT_OPTION_NUMBER,
    INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
    INCIDENT_TRIGGER_OPTION_NUMBER,
    SELECT_EVENT_OPTION_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_incident_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_INCIDENT_KIND_V1,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION,
)
from zg361_phase2_incident_checkpoint_seam import (  # noqa: E402
    SOURCE_CHECKPOINT_KIND,
    IncidentCheckpointSeamError,
    load_received_self_incident_checkpoint_receipt,
)


PREFLIGHT_KIND: Final = "zg361_phase2_incidents_operations_preflight"
CURRENT_READINESS: Final = "static-ready-live-pending"
SPAN_ID: Final = "phase2_incidents_operations"
PRODUCER_KEY: Final = "incidents-operations"
HANDLER: Final = "capture_incidents_operations"

SOURCE_CONTRACT_PATH: Final = (
    ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "fixtures"
    / "zhongguo_incident_snapshot_v1_source_contract.json"
)
SOURCE_CONTRACT_SHA256: Final = (
    "C32C8C7248DC76CA3CAF296EEA50A4ACFFBD77C4FBD3CB08F2503D755980F522"
)
INCIDENT_X_CLOSURE_CONTRACT_PATH: Final = (
    ROOT / "tools" / "zg361_phase2_incident_x_production_closure.json"
)
INCIDENT_X_CLOSURE_CONTRACT_SHA256: Final = (
    "ED4B5E82430187B1C79E2AEFE29748C5D51749782CC340644DB434C14A0B468A"
)
DEFAULT_INCIDENT_X_LIVE_REPORT: Final = (
    Path(r"Z:\ck3_mod_rewrite_process_assets\zg361")
    / "phase2-incident-x-full-entry-20260904-r2"
    / "report.json"
)
INCIDENT_X_LIVE_REPORT_SHA256: Final = (
    "1D41298B8987AA473304AE70FC53628639DE7700BBE5A9D7484A6BF76F566FE2"
)
INCIDENT_X_LIVE_TREE_SHA256: Final = (
    "AF8F0DECE9477FDD60B6C96D0E09A27BFC9E55CEED40A9804B70ACB986D57A2D"
)
INCIDENT_X_LIVE_FILE_COUNT: Final = 135


class IncidentsOperationsPreflightError(RuntimeError):
    """A static input or supplied live checkpoint is malformed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _record(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": _sha256(resolved),
    }


def _json(path: Path, label: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise IncidentsOperationsPreflightError(
            f"cannot read {label} JSON {path}: {error}"
        ) from error
    if not isinstance(value, Mapping):
        raise IncidentsOperationsPreflightError(f"{label} root must be an object")
    return value


def _static_cell_contract() -> dict[str, object]:
    return {
        "cell_id": INCIDENT_ACTION_CELL_ID,
        "span_id": SPAN_ID,
        "producer_key": PRODUCER_KEY,
        "handler": HANDLER,
        "profiles": list(INCIDENT_PROFILES),
        "entry_event_definition_key": INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
        "entry_option_number": INCIDENT_TRIGGER_OPTION_NUMBER,
        "result_event_definition_key": INCIDENT_RESULT_EVENT_DEFINITION_KEY,
        "result_option_number": INCIDENT_RESULT_OPTION_NUMBER,
        "required_capabilities": [
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
            SELECT_EVENT_OPTION_CAPABILITY,
            QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
        ],
        "sequence": [
            "provider-query-exact-entry-event-context",
            "select-fixed-authored-option-and-observe-old-instance-disappear",
            "provider-query-x-y-z-terminal-and-kpi-matrix",
            "provider-query-wrong-owner-acl-negative-control",
        ],
        "ack_only_is_green": False,
        "green_requires_provider_observed_postcondition": True,
        "fixture_evidence_is_live": False,
        "readiness": CURRENT_READINESS,
    }


def _validate_source_contract(path: Path) -> dict[str, object]:
    payload = _json(path, "Incident snapshot source contract")
    record = _record(path)
    properties = payload.get("required_source_properties")
    checks = {
        "canonical_sha256": record["sha256"] == SOURCE_CONTRACT_SHA256,
        "query_capability_exact": payload.get("capability")
        == QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
        "case_kind_exact": payload.get("case_kind") == ZHONGGUO_INCIDENT_KIND_V1,
        "profiles_exact": payload.get("profiles") == list(INCIDENT_PROFILES),
        "request_fields_exact": payload.get("request_fields")
        == [
            "request_nonce",
            "expected_revision",
            "owner_character_id",
            "profile",
        ],
        "mixed_terminal_contract": isinstance(properties, list)
        and "mixed_na_incident_profiles_are_queryable_in_one_paused_frame"
        in properties,
        "same_frame_contract": isinstance(properties, list)
        and "before_after_frame_equality" in properties,
        "frozen_profile_receipt_contract": isinstance(properties, list)
        and "profile_probe_receipt_is_frozen_before_terminal_publication"
        in properties,
        "explicitly_not_live": payload.get("readiness")
        == "static_and_fixture_ready_shared_protocol_not_live",
    }
    if not all(checks.values()):
        raise IncidentsOperationsPreflightError(
            "Incident snapshot source contract no longer matches the action cell"
        )
    return {"record": record, "checks": checks}


def _validate_incident_x_closure_contract(path: Path) -> dict[str, object]:
    payload = _json(path, "Incident-X closure contract")
    record = _record(path)
    candidate = payload.get("candidate")
    incident = payload.get("incident")
    checks = {
        "canonical_sha256": record["sha256"]
        == INCIDENT_X_CLOSURE_CONTRACT_SHA256,
        "kind_exact": payload.get("kind")
        == "zg361_phase2_incident_x_production_closure",
        "readiness_not_live": payload.get("readiness") == "static-ready-not-live",
        "live_pending": isinstance(candidate, Mapping)
        and candidate.get("live_status") == "pending",
        "x_effect_entry_present": isinstance(payload.get("fixture_root_effects"), list)
        and "zg361_ip_open_x_case_effect" in payload["fixture_root_effects"],
        "x_provider_closure_complete": isinstance(incident, Mapping)
        and len(incident.get("fixture_reachable_effects", [])) == 46
        and len(incident.get("reachable_events", [])) == 20,
    }
    if not all(checks.values()):
        raise IncidentsOperationsPreflightError(
            "Incident-X closure contract is stale or claims live readiness"
        )
    return {"record": record, "checks": checks}


def _validate_incident_x_live_report(path: Path) -> dict[str, object]:
    payload = _json(path, "Incident-X full-entry live report")
    record = _record(path)
    game = payload.get("game")
    candidate = payload.get("candidate")
    entry = payload.get("entry")
    logs = payload.get("logs")
    cleanup = payload.get("cleanup")
    checks = {
        "immutable_report_sha256": record["sha256"] == INCIDENT_X_LIVE_REPORT_SHA256,
        "real_probe_kind": payload.get("kind") == "zg361_minimal_full_entry_probe",
        "result_green": payload.get("result") == "GREEN",
        "exact_game_build": isinstance(game, Mapping)
        and game.get("installed_version")
        == ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION
        and str(game.get("exe_sha256", "")).upper()
        == ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256,
        "exact_incident_x_candidate": isinstance(candidate, Mapping)
        and candidate.get("file_count") == INCIDENT_X_LIVE_FILE_COUNT
        and str(candidate.get("tree_sha256", "")).upper()
        == INCIDENT_X_LIVE_TREE_SHA256,
        "candidate_loaded_to_paused_map": isinstance(entry, Mapping)
        and entry.get("candidate_mounted") is True
        and entry.get("game_state_ready") is True
        and entry.get("map_rendered") is True
        and entry.get("paused") is True,
        "no_material_project_errors": isinstance(logs, Mapping)
        and logs.get("material_error_lines") == [],
        "cleanup_green": isinstance(cleanup, Mapping)
        and cleanup.get("ck3_running_after") is False,
    }
    if not all(checks.values()):
        raise IncidentsOperationsPreflightError(
            "Incident-X full-entry report is absent, changed, or not GREEN"
        )
    return {
        "record": record,
        "evidence_scope": "product-full-entry-and-paused-map-only",
        "proves_gameplay_action": False,
        "proves_incident_provider_postcondition": False,
        "checks": checks,
    }


def _validate_source_checkpoint(
    path: Path, *, expected_seed_lineage_id: str
) -> dict[str, object]:
    try:
        return load_received_self_incident_checkpoint_receipt(
            path, expected_seed_lineage_id=expected_seed_lineage_id
        )
    except IncidentCheckpointSeamError as error:
        raise IncidentsOperationsPreflightError(
            "incidents-operations source checkpoint is not action-ready: "
            f"{error.reason_code}"
        ) from error


def build_preflight(
    *,
    source_contract_path: Path = SOURCE_CONTRACT_PATH,
    incident_x_closure_contract_path: Path = INCIDENT_X_CLOSURE_CONTRACT_PATH,
    incident_x_live_report_path: Path = DEFAULT_INCIDENT_X_LIVE_REPORT,
    source_checkpoint_receipt_path: Path | None = None,
    expected_seed_lineage_id: str | None = None,
) -> dict[str, object]:
    """Build one no-launch report without changing the readiness level."""

    static_cell = _static_cell_contract()
    source_contract = _validate_source_contract(source_contract_path)
    closure_contract = _validate_incident_x_closure_contract(
        incident_x_closure_contract_path
    )
    live_entry = _validate_incident_x_live_report(incident_x_live_report_path)
    source_checkpoint = None
    blockers: list[str] = []
    if source_checkpoint_receipt_path is None:
        blockers.append("received_self_incident_source_checkpoint_pending")
    else:
        if not (
            isinstance(expected_seed_lineage_id, str)
            and bool(expected_seed_lineage_id)
        ):
            raise IncidentsOperationsPreflightError(
                "expected seed lineage ID is required with a source checkpoint"
            )
        source_checkpoint = _validate_source_checkpoint(
            source_checkpoint_receipt_path,
            expected_seed_lineage_id=expected_seed_lineage_id,
        )

    return {
        "schema_version": 1,
        "kind": PREFLIGHT_KIND,
        "status": "GREEN_STATIC" if blockers else "READY_FOR_LIVE_RUN",
        "readiness": CURRENT_READINESS,
        "live_run_ready": not blockers,
        "live_gameplay_result": "pending",
        "feature_or_runtime_certification": False,
        "ck3_launch": "NOT_RUN_BY_PREFLIGHT",
        "cell": static_cell,
        "incident_snapshot_source_contract": source_contract,
        "incident_x_full_entry_live_evidence": live_entry,
        "incident_x_closure_contract": closure_contract,
        "source_checkpoint": source_checkpoint,
        "blockers": blockers,
        "required_live_checkpoint": {
            "kind": SOURCE_CHECKPOINT_KIND,
            "event_definition_key": INCIDENT_TRIGGER_EVENT_DEFINITION_KEY,
            "option_number": INCIDENT_TRIGGER_OPTION_NUMBER,
            "paused": True,
            "map_ready": True,
            "received_self": True,
            "player_must_equal_event_root": True,
            "owner_must_equal_notice_saved_scope": True,
            "owner_must_differ_from_player": True,
            "checkpoint_bytes_and_sha256_required": True,
            "event_context_provider_receipt_required": True,
            "same_frame_query_and_native_save_required": True,
            "seed_and_capture_lineage_required": True,
            "restore_then_reobserve_before_action_required": True,
        },
        "next_action": (
            "Capture the exact paused zg361.50 received-self checkpoint, then run "
            "the existing Incident gameplay cell and retain its provider-observed "
            "X/Y/Z terminal/KPI matrix."
        ),
    }


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--incident-x-live-report",
        type=Path,
        default=DEFAULT_INCIDENT_X_LIVE_REPORT,
    )
    parser.add_argument("--source-checkpoint-receipt", type=Path)
    parser.add_argument("--expected-seed-lineage-id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_preflight(
            incident_x_live_report_path=args.incident_x_live_report,
            source_checkpoint_receipt_path=args.source_checkpoint_receipt,
            expected_seed_lineage_id=args.expected_seed_lineage_id,
        )
    except IncidentsOperationsPreflightError as error:
        print(f"RED_STATIC: {error}")
        return 1
    if args.output is not None:
        _write_json(args.output, report)
    print(
        f"{report['status']}: {report['readiness']}; "
        f"blockers={','.join(report['blockers']) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CURRENT_READINESS",
    "DEFAULT_INCIDENT_X_LIVE_REPORT",
    "HANDLER",
    "IncidentsOperationsPreflightError",
    "PREFLIGHT_KIND",
    "PRODUCER_KEY",
    "SOURCE_CHECKPOINT_KIND",
    "SPAN_ID",
    "build_preflight",
]
