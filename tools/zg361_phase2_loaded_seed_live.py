#!/usr/bin/env python3
"""No-launch paused live wrapper for the phase-two loaded-seed v2 proof.

The live callable consumes an already-connected gameplay service.  This file
does not know how to launch, stop, resume, pause, or mutate CK3, and its CLI is
plan-only.  The owning managed session can therefore call the wrapper after a
canonical seed becomes GREEN and immediately continue with the same service.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import importlib
import json
from pathlib import Path
from typing import Protocol

REPORT_NAME = "phase2_loaded_seed_v2_paused_live.json"
PLAN_SCHEMA_VERSION = 1
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEED_CONTRACT_PATH = ROOT / "tools" / "zg361_phase2_seed_contract.json"


class ExistingPausedSession(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_loaded_feature_manifest_v1(
        self, *, expected_revision: int
    ) -> dict[str, object]: ...


class LoadedSeedLiveError(RuntimeError):
    result = "RED"

    def __init__(
        self, reason_code: str, evidence: Mapping[str, object] | None = None
    ) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **dict(evidence or {}),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"phase-two loaded-seed live RED [{reason_code}]")


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_no_launch_plan(seed_contract_path: Path) -> dict[str, object]:
    """Describe the reusable existing-session sequence without touching CK3."""

    contract_path = Path(seed_contract_path).resolve()
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LoadedSeedLiveError(
            "seed_contract_unreadable", {"cause": str(error)}
        ) from error
    if not (
        isinstance(contract, dict)
        and contract.get("schema_version") == 1
        and contract.get("kind") == "zg361_phase2_paused_seed"
        and isinstance(contract.get("ready"), bool)
        and isinstance(contract.get("status"), str)
        and isinstance(contract.get("blocker"), str)
    ):
        raise LoadedSeedLiveError("seed_contract_header_invalid")
    current_seed_ready = (
        contract.get("ready") is True and contract.get("status") == "ready"
    )
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "kind": "zg361_phase2_loaded_seed_v2_no_launch_plan",
        "result": "GREEN",
        "ready_to_run": True,
        "current_seed_ready": current_seed_ready,
        "execution_state": (
            "READY_FOR_EXISTING_SESSION"
            if current_seed_ready
            else "WAITING_CANONICAL_SEED"
        ),
        "current_seed_blocker": (
            None if current_seed_ready else contract.get("blocker")
        ),
        "seed_contract_path": str(contract_path),
        "seed_contract_kind": contract.get("kind"),
        "proof_schema_version": 2,
        "required_existing_session": {
            "paused": True,
            "map_ready": True,
            "tracked_ck3_pid": "positive exact PID",
            "expected_connection_generation": (
                "positive exact generation from the owning managed-session binding"
            ),
            "service_methods": [
                "snapshot",
                "query_loaded_feature_manifest_v1",
            ],
        },
        "ordered_steps": [
            "load canonical ready seed contract",
            "read first paused snapshot from the existing session",
            "bind snapshot/player/PID/generation/date",
            "query loaded-feature manifest at the same public revision",
            "read a second snapshot and reject any binding change",
            "run prove_phase2_loaded_seed schema v2 for all eight rows",
            "return service ownership to the same managed session",
        ],
        "forbidden_operations": [
            "launch CK3",
            "stop CK3",
            "pause or resume the map",
            "change game speed",
            "select an event option",
            "run any phase-two span handler",
            "start a recorder",
        ],
        "same_session_continuation": True,
        "integrated_consumer": (
            "run_zhongguo_acceptance._phase2_promo_seed_proof_probe"
        ),
        "lifecycle_order": [
            "install canonical seed before launch",
            "start managed native session and bind PID/generation",
            "complete the managed loader gate",
            "obtain owner paused snapshot",
            "run loaded-seed v2 manifest/same-frame proof inline",
            "enter eight-span capture executor and start recorder",
            "stop recorder",
            "cleanup supervisor and driver in the owning runner finally block",
        ],
        "typed_pre_record_stops": [
            "canonical_seed_not_ready",
            "loaded_feature_manifest_unavailable",
            "managed_session_generation_mismatch",
            "state_changed_after_manifest",
            "eight_row_loaded_proof_not_green",
        ],
        "upstream_observer_gate_boundary": {
            "owner": "run_zg361_phase2_seed_capture",
            "when_requested": (
                "must be GREEN before the seed-generation launch boundary"
            ),
            "missing_manifest_reason": "native_observer_manifest_pending",
            "session_reuse_claimed": False,
        },
        "live_executed": False,
        "provider_live_proof_claimed": False,
    }


def run_existing_session_loaded_seed_v2(
    service: ExistingPausedSession,
    *,
    seed_contract_path: Path | None = None,
    seed_contract: Mapping[str, object] | None = None,
    artifacts: Path,
    tracked_ck3_pid: int,
    expected_connection_generation: int,
    first_snapshot: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Prove one canonical seed/manifest frame without any gameplay action."""

    artifacts = Path(artifacts).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    report_path = artifacts / REPORT_NAME
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_loaded_seed_v2_paused_live_acceptance",
        "result": "RED",
        "reason_code": None,
        "scope": "existing_session_same_frame_loaded_seed_v2_only",
        "no_launch": True,
        "service_session_reused": True,
        "tracked_ck3_pid": tracked_ck3_pid,
        "expected_connection_generation": expected_connection_generation,
        "seed_contract_path": (
            str(Path(seed_contract_path).resolve())
            if seed_contract_path is not None
            else None
        ),
        "seed_contract_inline": seed_contract is not None,
        "first_snapshot_supplied_by_owner": first_snapshot is not None,
        "first_binding": None,
        "second_binding": None,
        "loaded_feature_manifest": None,
        "loaded_seed_proof": None,
        "eight_row_loaded_proof_green": False,
        "span_actions_executed": [],
        "recorder_started": False,
        "provider_live_proof_claimed": False,
        "same_session_continuation_authorized": False,
        "failure_reason": None,
    }
    _write_json(report_path, report)
    try:
        phase2 = importlib.import_module("run_zhongguo_acceptance")
        if (
            isinstance(tracked_ck3_pid, bool)
            or not isinstance(tracked_ck3_pid, int)
            or tracked_ck3_pid <= 0
        ):
            raise LoadedSeedLiveError("tracked_pid_invalid")
        if (
            isinstance(expected_connection_generation, bool)
            or not isinstance(expected_connection_generation, int)
            or expected_connection_generation <= 0
        ):
            raise LoadedSeedLiveError("expected_connection_generation_invalid")
        if (seed_contract_path is None) == (seed_contract is None):
            raise LoadedSeedLiveError("seed_contract_input_ambiguous")
        contract = (
            phase2.load_phase2_seed_contract(seed_contract_path)
            if seed_contract_path is not None
            else dict(seed_contract or {})
        )
        if not (
            contract.get("ready") is True
            and contract.get("status") == "ready"
        ):
            raise LoadedSeedLiveError(
                "canonical_seed_not_ready",
                {"seed_blocker": contract.get("blocker")},
            )
        first_value = (
            service.snapshot() if first_snapshot is None else first_snapshot
        )
        if not isinstance(first_value, Mapping):
            raise LoadedSeedLiveError("first_snapshot_invalid")
        first = dict(first_value)
        first_binding = phase2._phase2_paused_binding(
            first, label="phase-two loaded-seed v2 first snapshot"
        )
        report["first_binding"] = first_binding
        if first_binding["bridge_pid"] != tracked_ck3_pid:
            raise LoadedSeedLiveError(
                "tracked_pid_mismatch", {"first_binding": first_binding}
            )
        if (
            first_binding["connection_generation"]
            != expected_connection_generation
        ):
            raise LoadedSeedLiveError(
                "managed_session_generation_mismatch",
                {
                    "expected_connection_generation": (
                        expected_connection_generation
                    ),
                    "first_binding": first_binding,
                },
            )
        query_manifest = getattr(
            service, "query_loaded_feature_manifest_v1", None
        )
        if not callable(query_manifest):
            raise LoadedSeedLiveError("loaded_feature_manifest_unavailable")
        try:
            manifest = query_manifest(
                expected_revision=int(first_binding["revision"])
            )
        except BaseException as error:
            raise LoadedSeedLiveError(
                "loaded_feature_manifest_unavailable",
                {"cause": f"{type(error).__name__}: {error}"},
            ) from error
        if not (
            isinstance(manifest, Mapping)
            and manifest.get("status") == "available"
            and manifest.get("loaded_feature_manifest_ready") is True
        ):
            raise LoadedSeedLiveError(
                "loaded_feature_manifest_unavailable",
                {
                    "manifest": (
                        dict(manifest)
                        if isinstance(manifest, Mapping)
                        else {"actual_type": type(manifest).__name__}
                    )
                },
            )
        manifest = dict(manifest)
        report["loaded_feature_manifest"] = manifest
        second = service.snapshot()
        if not isinstance(second, dict):
            raise LoadedSeedLiveError("second_snapshot_invalid")
        second_binding = phase2._phase2_paused_binding(
            second, label="phase-two loaded-seed v2 second snapshot"
        )
        report["second_binding"] = second_binding
        binding_fields = (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "player_character_id",
            "bridge_pid",
            "connection_generation",
        )
        if any(
            first_binding[field] != second_binding[field]
            for field in binding_fields
        ):
            raise LoadedSeedLiveError(
                "state_changed_after_manifest",
                {
                    "first_binding": first_binding,
                    "second_binding": second_binding,
                },
            )
        proof = phase2.prove_phase2_loaded_seed(
            first,
            contract,
            artifacts,
            loaded_feature_manifest=manifest,
        )
        report["loaded_seed_proof"] = proof
        rows = proof.get("span_requirements")
        eight_rows_green = (
            proof.get("result") == "GREEN"
            and isinstance(rows, list)
            and len(rows) == 8
            and len(
                {
                    row.get("span_id")
                    for row in rows
                    if isinstance(row, Mapping)
                }
            )
            == 8
            and all(
                isinstance(row, Mapping)
                and row.get("loaded_feature_seed_ready") is True
                and row.get("provider_ready_claimed") is False
                for row in rows
            )
        )
        if not eight_rows_green:
            raise LoadedSeedLiveError(
                "eight_row_loaded_proof_not_green", {"proof": proof}
            )
        report.update(
            {
                "result": "GREEN",
                "eight_row_loaded_proof_green": True,
                "same_session_continuation_authorized": True,
                "failure_reason": None,
            }
        )
        _write_json(report_path, report)
        return report
    except BaseException as error:
        reason_code = (
            error.reason_code
            if isinstance(error, LoadedSeedLiveError)
            else "loaded_seed_v2_proof_failed"
        )
        report["result"] = "RED"
        report["reason_code"] = reason_code
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        report["same_session_continuation_authorized"] = False
        if isinstance(error, LoadedSeedLiveError):
            report["typed_error"] = error.evidence
        _write_json(report_path, report)
        if isinstance(error, LoadedSeedLiveError):
            raise
        raise LoadedSeedLiveError(reason_code, {"cause": str(error)}) from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-only", action="store_true", required=True)
    parser.add_argument(
        "--seed-contract", type=Path, default=DEFAULT_SEED_CONTRACT_PATH
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    plan = build_no_launch_plan(args.seed_contract)
    _write_json(args.output, plan)
    print(f"GREEN: no-launch loaded-seed v2 plan written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
