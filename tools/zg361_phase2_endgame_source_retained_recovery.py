#!/usr/bin/env python3
"""Adopt one paused endgame-source CK3 process after a Python-only RED.

The failed operator must first release its named-pipe server without killing
its CK3 child.  This command recreates the same pipe server, proves the exact
retained PID and paused owner frame, reloads the current Python policy, and
performs only the pending source save and registry assembly.  Recovery failure
leaves CK3 paused.  Optional success cleanup terminates only the bound CK3 PID.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Mapping, Sequence

import zg361_phase2_af5_operator_job as base
from zg361_phase2_endgame_source_operator_job import (
    EndgameSourceOperatorJob,
    validate_activation,
)


RECOVERY_KIND = "zg361_phase2_endgame_source_retained_recovery_v1"
FAILED_ATTEMPT_FILES = (
    "endgame-source-action.json",
    "endgame-source-production-entry.json",
)


def _archive_failed_attempt(source_dir: Path, attempt: int) -> list[dict[str, object]]:
    if attempt <= 0:
        raise ValueError("attempt must be positive")
    archived: list[dict[str, object]] = []
    for name in FAILED_ATTEMPT_FILES:
        source = source_dir / name
        if not source.is_file():
            continue
        destination = source.with_name(
            f"{source.stem}-red-attempt-{attempt:02d}{source.suffix}"
        )
        if destination.exists():
            raise base.Af5JobError(
                f"retained recovery archive already exists: {destination}"
            )
        shutil.copy2(source, destination)
        archived.append(base.file_record(destination))
    return archived


def _retained_binding(
    snapshot: object,
    *,
    expected_pid: int,
    expected_owner_character_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    frame = base.mapping(snapshot, "retained snapshot")
    diagnostics = base.mapping(frame.get("diagnostics"), "retained diagnostics")
    played = base.mapping(frame.get("played_character"), "retained played character")
    event = base.mapping(frame.get("active_event"), "retained active event")
    generation = base.positive_int(
        diagnostics.get("connection_generation"), "retained connection generation"
    )
    checks = {
        "paused": frame.get("paused") is True,
        "map_ready": frame.get("map_ready") is True,
        "bridge_connected": diagnostics.get("connected") is True,
        "bridge_pid": diagnostics.get("bridge_pid") == expected_pid,
        "owner_character": (
            played.get("character_id") == expected_owner_character_id
        ),
        "date_raw": frame.get("date_raw") == expected_date_raw,
        "active_event_instance": (
            isinstance(event.get("instance_id"), int)
            and not isinstance(event.get("instance_id"), bool)
            and int(event["instance_id"]) > 0
        ),
    }
    if not all(checks.values()):
        raise base.Af5JobError(
            "retained endgame-source frame does not match the frozen retry",
            {"checks": checks, "snapshot": deepcopy(dict(frame))},
        )
    return {
        "bridge_pid": expected_pid,
        "connection_generation": generation,
        "player_character_id": expected_owner_character_id,
        "date_raw": expected_date_raw,
        "event_instance_id": event["instance_id"],
        "snapshot_id": frame.get("snapshot_id"),
        "revision": frame.get("revision"),
    }


def _wait_for_retained_snapshot(
    service: object, *, expected_pid: int, timeout_seconds: float
) -> Mapping[str, object]:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    deadline = time.monotonic() + timeout_seconds
    last_error = "native bridge has not reconnected"
    while time.monotonic() < deadline:
        try:
            snapshot = service.snapshot()
            diagnostics = (
                snapshot.get("diagnostics")
                if isinstance(snapshot, Mapping)
                else None
            )
            if (
                isinstance(diagnostics, Mapping)
                and diagnostics.get("connected") is True
                and diagnostics.get("bridge_pid") == expected_pid
            ):
                return snapshot
            last_error = f"unexpected diagnostics: {diagnostics!r}"
        except BaseException as error:
            last_error = f"{type(error).__name__}: {error}"
        time.sleep(0.05)
    raise base.Af5JobError(
        f"retained native bridge reconnection timed out: {last_error}"
    )


def _terminate_exact_ck3(pid: int, *, timeout_seconds: float = 15.0) -> dict[str, object]:
    before = base.ck3_pids()
    if before != [pid]:
        raise base.Af5JobError(
            f"exact retained cleanup expected sole CK3 PID {pid}, found {before}"
        )
    result = subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    deadline = time.monotonic() + timeout_seconds
    after = base.ck3_pids()
    while after and time.monotonic() < deadline:
        time.sleep(0.10)
        after = base.ck3_pids()
    proven = result.returncode == 0 and after == []
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_endgame_source_retained_cleanup_v1",
        "result": "GREEN" if proven else "RED",
        "cleanup_proven": proven,
        "exact_pid": pid,
        "ck3_pids_before": before,
        "ck3_pids_after": after,
        "taskkill_returncode": result.returncode,
        "taskkill_stdout": result.stdout.strip(),
        "taskkill_stderr": result.stderr.strip(),
    }


def recover_retained_source(
    activation_path: Path,
    *,
    expected_pid: int,
    attempt: int,
    reconnect_timeout_seconds: float,
    cleanup_after_success: bool,
) -> dict[str, object]:
    activation_path = activation_path.expanduser().resolve()
    bound = validate_activation(activation_path, require_empty_slot=False)
    if base.ck3_pids() != [expected_pid]:
        raise base.Af5JobError(
            f"retained recovery requires sole CK3 PID {expected_pid}"
        )
    root = Path(str(bound["repository_root"]))
    sys.path.insert(0, str(root / "ck3_autonomous_player" / "src"))
    sys.path.insert(0, str(root / "tools"))
    runner = importlib.import_module("run_zhongguo_acceptance")
    native_driver = importlib.import_module("xar_autoplayer.bridge.native_driver")
    service_module = importlib.import_module("xar_autoplayer.bridge.service")
    artifacts = Path(str(bound["artifact_directory"]))
    source_dir = artifacts / "source"
    recovery_path = artifacts / "endgame-source-hot-recovery.json"
    cleanup_path = artifacts / "endgame-source-retained-cleanup.json"
    if recovery_path.exists():
        raise base.Af5JobError(
            f"retained recovery output already exists: {recovery_path}"
        )
    archived = _archive_failed_attempt(source_dir, attempt)
    driver = native_driver.NativeHeadlessGameplayDriver(
        str(bound["bridge_pipe"]),
        state_dir=Path(str(bound["state_directory"])),
        save_dir=Path(str(bound["state_directory"])) / "profile" / "save games",
        command_timeout_seconds=runner.NATIVE_TITLE_COMMAND_TIMEOUT_S,
    )
    service = service_module.GameplayBridgeService(driver)
    result: dict[str, object] = {
        "schema_version": 1,
        "kind": RECOVERY_KIND,
        "result": "RED",
        "same_ck3_process_retained": False,
        "expected_pid": expected_pid,
        "attempt": attempt + 1,
        "archived_failed_attempt": archived,
        "activation": bound["activation_record"],
        "failure_reason": None,
    }
    try:
        snapshot = _wait_for_retained_snapshot(
            service,
            expected_pid=expected_pid,
            timeout_seconds=reconnect_timeout_seconds,
        )
        binding = _retained_binding(
            snapshot,
            expected_pid=expected_pid,
            expected_owner_character_id=int(
                bound["endgame_source_expected_owner_character_id"]
            ),
            expected_date_raw=int(bound["endgame_source_expected_date_raw"]),
        )
        result["same_ck3_process_retained"] = True
        result["retained_binding"] = binding
        job = EndgameSourceOperatorJob(activation_path)
        job.bound = bound
        job.runner = runner
        job.driver = driver
        job.service = service
        job.binding = binding
        job._execute_action(bound)
        if job.product_result != "GREEN":
            raise base.Af5JobError("retained source action did not become GREEN")
        result.update(
            result="GREEN",
            source_result="GREEN",
            source_evidence=base.file_record(
                artifacts / "endgame-source-green.json"
            ),
        )
        base.write_object(recovery_path, result)
    except BaseException as error:
        result["failure_reason"] = f"{type(error).__name__}: {error}"
        result["failure_evidence"] = base.bootstrap_evidence_json_value(
            getattr(error, "evidence", None)
        )
        base.write_object(recovery_path, result)
        raise
    finally:
        driver.close()
    if cleanup_after_success:
        cleanup = _terminate_exact_ck3(expected_pid)
        base.write_object(cleanup_path, cleanup)
        result["cleanup"] = cleanup
        base.write_object(recovery_path, result)
        if cleanup.get("result") != "GREEN":
            raise base.Af5JobError("retained CK3 cleanup was not proven", cleanup)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activation", required=True, type=Path)
    parser.add_argument("--expected-pid", required=True, type=int)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--reconnect-timeout-seconds", type=float, default=30.0)
    parser.add_argument("--cleanup-after-success", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = recover_retained_source(
            args.activation,
            expected_pid=base.positive_int(args.expected_pid, "expected PID"),
            attempt=base.positive_int(args.attempt, "attempt"),
            reconnect_timeout_seconds=args.reconnect_timeout_seconds,
            cleanup_after_success=args.cleanup_after_success,
        )
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except BaseException as error:
        print(f"RETAINED ENDGAME SOURCE RECOVERY FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
