#!/usr/bin/env python3
"""Reconnect to a retained Phase2 CK3 session and continue source capture.

This client never launches or terminates CK3 by default.  It is the recovery
half of ``--retain-healthy-phase2-session-on-red``: Python/harness changes can
be tested in a fresh client process while the exact mounted product, save and
native bridge remain alive in the owning runner process.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
import time
import uuid
from collections.abc import Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver  # noqa: E402
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import write_json_atomic  # noqa: E402
from zg361_phase2_promotion_source_checkpoint_capture import (  # noqa: E402
    capture_promotion_source_checkpoint_v2,
)
from zg361_phase2_promotion_source_production_entry import (  # noqa: E402
    enter_promotion_source_checkpoint_v1,
)


class RetainedSessionError(RuntimeError):
    pass


def _read_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RetainedSessionError(f"{label} is unreadable: {path}: {error}") from error
    if not isinstance(value, dict):
        raise RetainedSessionError(f"{label} must be a JSON object: {path}")
    return value


def _write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, dict(value))


def _seed_lineage_id(contract: Mapping[str, object]) -> str:
    source = contract.get("source")
    digest = source.get("sha256") if isinstance(source, Mapping) else None
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in digest)
    ):
        raise RetainedSessionError("source run seed contract lacks a SHA-256")
    return f"zg361-phase2-seed-{digest.lower()}"


def validate_retained_session_inputs(
    *,
    state_dir: Path,
    pipe_name: str,
    source_run_cell: Path,
) -> dict[str, object]:
    retention_path = source_run_cell / "09_phase2_native_session_retained.json"
    retention = _read_object(retention_path, "retention evidence")
    seed_install = _read_object(
        source_run_cell / "00_phase2_seed_install.json", "seed install evidence"
    )
    loader_gate = _read_object(
        source_run_cell / "03_loader_gate.json", "loader gate evidence"
    )
    contract = seed_install.get("contract")
    checks = {
        "retention_authorized": (
            retention.get("result") == "RETAINED"
            and retention.get("reconnect_authorized") is True
            and retention.get("process_restart_required") is False
        ),
        "state_dir_exact": Path(str(retention.get("state_dir", ""))).resolve()
        == state_dir.resolve(),
        "profile_dir_exact": Path(str(retention.get("profile_dir", ""))).resolve()
        == (state_dir / "profile").resolve(),
        "pipe_exact": retention.get("pipe") == pipe_name,
        "seed_ready": (
            seed_install.get("result") == "GREEN"
            and isinstance(contract, Mapping)
            and contract.get("ready") is True
            and contract.get("status") == "ready"
        ),
        "loader_green": loader_gate.get("result") == "GREEN",
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        raise RetainedSessionError(
            "retained session inputs failed: " + ", ".join(failed)
        )
    return {
        "retention_path": str(retention_path.resolve()),
        "retention": retention,
        "seed_install": seed_install,
        "seed_contract": copy.deepcopy(dict(contract)),
        "loader_gate": loader_gate,
        "checks": checks,
    }


def request_session_stop(state_dir: Path, *, timeout_seconds: float = 30.0) -> dict[str, object]:
    """Ask the owning native-session process to stop through its file queue."""

    request_id = f"phase2-client-stop-{uuid.uuid4().hex}"
    bridge_dir = state_dir / "native-session" / "bridge"
    inbox = bridge_dir / "inbox" / f"{request_id}.json"
    outbox = bridge_dir / "outbox" / f"{request_id}.json"
    write_json_atomic(
        inbox,
        {"protocol_version": 1, "request_id": request_id, "command": "stop"},
    )
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if outbox.is_file():
            response = _read_object(outbox, "native-session stop response")
            if response.get("ok") is not True:
                raise RetainedSessionError(
                    f"native-session rejected stop request: {response!r}"
                )
            return response
        time.sleep(0.05)
    raise RetainedSessionError("native-session stop response timed out")


def run(
    *,
    state_dir: Path,
    pipe_name: str,
    source_run_cell: Path,
    artifacts: Path,
    timeout_seconds: float,
    stop_session_after: bool = False,
) -> dict[str, object]:
    if timeout_seconds <= 0:
        raise RetainedSessionError("timeout must be positive")
    state_dir = state_dir.resolve()
    source_run_cell = source_run_cell.resolve()
    artifacts = artifacts.resolve()
    if artifacts.exists():
        raise RetainedSessionError(f"artifact directory already exists: {artifacts}")
    artifacts.mkdir(parents=True)
    inputs = validate_retained_session_inputs(
        state_dir=state_dir,
        pipe_name=pipe_name,
        source_run_cell=source_run_cell,
    )
    retention = inputs["retention"]
    seed_contract = inputs["seed_contract"]
    assert isinstance(retention, dict)
    assert isinstance(seed_contract, dict)
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_retained_session_promotion_source_client",
        "result": "RED",
        "launch_performed": False,
        "restart_performed": False,
        "session_stop_requested": stop_session_after,
        "source_run_cell": str(source_run_cell),
        "retention": copy.deepcopy(retention),
        "input_checks": inputs["checks"],
        "entry": None,
        "capture": None,
        "error_reason": None,
    }
    driver: NativeHeadlessGameplayDriver | None = None
    try:
        driver = NativeHeadlessGameplayDriver(
            pipe_name,
            state_dir=state_dir,
            save_dir=state_dir / "profile" / "save games",
        )
        service = GameplayBridgeService(driver)
        capabilities = service.capabilities()
        snapshot = service.snapshot()
        diagnostics = capabilities.get("diagnostics")
        played = snapshot.get("played_character")
        live_checks = {
            "bridge_connected": (
                isinstance(diagnostics, Mapping)
                and diagnostics.get("connected") is True
            ),
            "same_pid": (
                isinstance(diagnostics, Mapping)
                and diagnostics.get("bridge_pid") == retention.get("bridge_pid")
            ),
            "same_generation": (
                isinstance(diagnostics, Mapping)
                and diagnostics.get("connection_generation")
                == retention.get("connection_generation")
            ),
            "map_ready": snapshot.get("map_ready") is True,
            "player_bound": (
                isinstance(played, Mapping)
                and isinstance(played.get("character_id"), int)
                and not isinstance(played.get("character_id"), bool)
            ),
        }
        failed = [name for name, passed in live_checks.items() if passed is not True]
        if failed:
            raise RetainedSessionError(
                "live retained-session binding failed: " + ", ".join(failed)
            )
        report["live_checks"] = live_checks
        report["attached_snapshot"] = {
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "date_raw": snapshot.get("date_raw"),
            "paused": snapshot.get("paused"),
            "played_character_id": played.get("character_id"),
        }
        entry: dict[str, object] = {}
        try:
            enter_promotion_source_checkpoint_v1(
                service,
                timeout_seconds=timeout_seconds,
                evidence_out=entry,
            )
        finally:
            _write(artifacts / "03_promotion_source_production_entry.json", entry)
            report["entry"] = entry
        current_capabilities = service.capabilities()
        current_diagnostics = current_capabilities.get("diagnostics")
        if not isinstance(current_diagnostics, Mapping):
            raise RetainedSessionError("retained session lost native diagnostics")
        seed_lineage_id = _seed_lineage_id(seed_contract)
        managed_session = {
            "schema_version": 1,
            "kind": "zg361_phase2_managed_product_session",
            "result": "GREEN",
            "managed_native_session": True,
            "retained_session_reconnect": True,
            "product_only_runtime": True,
            "acceptance_fixture_loaded": False,
            "same_pid_gameplay_continuation_authorized": True,
            "tracked_ck3_pid": current_diagnostics.get("bridge_pid"),
            "connection_generation": current_diagnostics.get(
                "connection_generation"
            ),
            "seed_lineage_id": seed_lineage_id,
            "game_version": "1.19.0.6",
            "executable_sha256": (
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
            ),
        }
        capture_lineage = {
            "seed_lineage_id": seed_lineage_id,
            "evidence_class": "real_ck3",
            "session_kind": "managed_product_session_retained_reconnect",
            "product_only_runtime": True,
            "tracked_ck3_pid": current_diagnostics.get("bridge_pid"),
            "connection_generation": current_diagnostics.get(
                "connection_generation"
            ),
            "game_version": "1.19.0.6",
            "executable_sha256": managed_session["executable_sha256"],
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
            "source_retention_evidence": inputs["retention_path"],
        }
        capture = capture_promotion_source_checkpoint_v2(
            service,
            checkpoint_root=artifacts / "promotion-source-checkpoints",
            capture_artifact_path=(
                artifacts / "04_promotion_source_checkpoint_capture_v2.json"
            ),
            seed_lineage_id=seed_lineage_id,
            capture_lineage=capture_lineage,
            managed_product_session=managed_session,
            timeout_seconds=timeout_seconds,
        )
        report["capture"] = capture
        if capture.get("result") != "GREEN":
            raise RetainedSessionError("promotion source checkpoint capture returned RED")
        report["result"] = "GREEN"
    except BaseException as error:
        report["error_reason"] = f"{type(error).__name__}: {error}"
    finally:
        if driver is not None:
            try:
                driver.close()
                report["client_driver_closed"] = True
            except BaseException as close_error:
                report["client_driver_closed"] = False
                report["client_close_error"] = (
                    f"{type(close_error).__name__}: {close_error}"
                )
                report["result"] = "RED"
        if stop_session_after:
            try:
                report["session_stop_response"] = request_session_stop(state_dir)
            except BaseException as stop_error:
                report["session_stop_error"] = (
                    f"{type(stop_error).__name__}: {stop_error}"
                )
                report["result"] = "RED"
        else:
            report["session_retained_for_next_client"] = True
        _write(artifacts / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--source-run-cell", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--stop-session-after", action="store_true")
    args = parser.parse_args()
    report = run(
        state_dir=args.state_dir,
        pipe_name=args.bridge_pipe,
        source_run_cell=args.source_run_cell,
        artifacts=args.artifacts_dir,
        timeout_seconds=args.timeout_seconds,
        stop_session_after=args.stop_session_after,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("result") == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
