#!/usr/bin/env python3
"""Observe the two native CAddTruce evaluator callsites without querying them.

The runner starts one managed CK3 process from an immutable cold checkpoint,
waits for paused native readiness, and then samples only cached heartbeat
diagnostics.  It sends no MCP query, Context effect, war action, or evaluator
request.  A live invocation requires a fresh absent attempt directory.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import time
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))
RESEARCH_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(RESEARCH_ROOT))

import analyze_g2_truce_native_callsite_observer_live as postprocessor  # noqa: E402

from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.environment import (  # noqa: E402
    make_spec,
    prepare_profile,
    verify_profile,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import (  # noqa: E402
    NATIVE_DRIVER_STATE_FILENAME,
    NATIVE_SESSION_CHECKPOINT_FILENAME,
    NATIVE_SESSION_QUEUE_DIRNAME,
    native_session,
    validate_cold_start_checkpoint_for_pipe,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


REPORT_KIND = "ck3_g2_truce_native_callsite_observer_live_acceptance"
OBSERVER_KEY = "g2_truce_native_callsite_observer_v1"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
EXPECTED_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_CALL_RVAS = (0x2EDAF0F, 0x2EDB59E)
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
REQUIRED_CALLSITE_FIELDS = (
    "call_instruction_rva",
    "pre_call_count",
    "post_call_count",
    "last_script_value",
    "last_effect_context",
    "last_evaluation_context",
    "last_pre_thread_id",
    "last_pre_timestamp_qpc",
    "last_return_eax",
    "last_post_thread_id",
    "last_post_timestamp_qpc",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--source-driver-state", type=Path, required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--expected-driver-state-sha256", required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--expected-bridge-dll-sha256", required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--expected-bridge-injector-sha256", required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--expected-date-raw", type=int, required=True)
    parser.add_argument("--ready-manifest", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=420.0)
    parser.add_argument("--readiness-timeout", type=float, default=300.0)
    parser.add_argument("--observation-timeout", type=float, default=60.0)
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: object, name: str) -> str:
    result = str(value).strip().upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise AgentError(f"{name} must be 64 hexadecimal digits")
    return result


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _materialize_acceptance_evidence(
    *,
    report_path: Path,
    manifest_path: Path,
    expected_manifest_sha256: str | None = None,
) -> dict[str, object]:
    """Bind one raw runner report to its typed offline acceptance result."""

    report_path = report_path.expanduser().resolve()
    manifest_path = manifest_path.expanduser().resolve()
    report_bytes = report_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    if len(report_bytes) > postprocessor.MAX_REPORT_BYTES:
        raise AgentError("runner report exceeds bounded postprocessor limit")
    if len(manifest_bytes) > MAX_MANIFEST_BYTES:
        raise AgentError("ready manifest exceeds bounded postprocessor limit")
    report_sha256 = hashlib.sha256(report_bytes).hexdigest().upper()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest().upper()
    expected_manifest_sha256 = (
        _expected_sha256(
            expected_manifest_sha256, "ready-manifest SHA-256"
        )
        if expected_manifest_sha256 is not None
        else manifest_sha256
    )
    typed = postprocessor.analyze(
        json.loads(report_bytes.decode("utf-8")),
        json.loads(manifest_bytes.decode("utf-8")),
        report_sha256=report_sha256,
        manifest_sha256=manifest_sha256,
        expected_manifest_sha256=expected_manifest_sha256,
    )
    typed_path = report_path.with_name("typed-postprocess.json")
    _write_json_atomic(typed_path, typed)
    typed_sha256 = _sha256_file(typed_path)
    evaluated = typed.get("evaluated_days")
    evaluated = evaluated if isinstance(evaluated, dict) else {}
    projection_eligible = bool(
        typed.get("status") == "GREEN"
        and typed.get("classification") == "two_site_return_observed"
        and evaluated.get("observable") is True
    )
    runner_path = Path(__file__).resolve()
    postprocessor_path = Path(postprocessor.__file__).resolve()
    acceptance_path = report_path.with_name("acceptance-report.json")
    acceptance = {
        "format_version": 1,
        "kind": "ck3_g2_truce_native_callsite_observer_typed_acceptance",
        "status": typed.get("status"),
        "classification": typed.get("classification"),
        "ok": projection_eligible,
        "input_evidence": {
            "runner_report_path": str(report_path),
            "runner_report_sha256": report_sha256,
            "ready_manifest_path": str(manifest_path),
            "ready_manifest_sha256": manifest_sha256,
            "expected_ready_manifest_sha256": expected_manifest_sha256,
            "runner_source_path": str(runner_path),
            "runner_source_sha256": _sha256_file(runner_path),
            "postprocessor_source_path": str(postprocessor_path),
            "postprocessor_source_sha256": _sha256_file(postprocessor_path),
        },
        "typed_postprocess": {
            "path": str(typed_path),
            "sha256": typed_sha256,
            "contract": typed.get("contract"),
            "status": typed.get("status"),
            "classification": typed.get("classification"),
        },
        "projection": {
            "identity_bound_truce_input_eligible": projection_eligible,
            "evaluated_days": {
                "observable": projection_eligible,
                "site_0": (
                    evaluated.get("site_0") if projection_eligible else None
                ),
                "site_1": (
                    evaluated.get("site_1") if projection_eligible else None
                ),
            },
            "expiry_observable": False,
            "war_bound_observable": False,
        },
        "readiness": {
            "action_terms_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
        },
        "boundaries": {
            "heartbeat_or_install_is_evaluated_days": False,
            "no_hit_is_evaluated_days": False,
            "direct_evaluator_invoked": False,
            "context_effect_executed": False,
            "mutation_executed": False,
            "ck3_started_by_postprocessing": False,
        },
    }
    _write_json_atomic(acceptance_path, acceptance)
    return {
        "acceptance": acceptance,
        "acceptance_path": str(acceptance_path),
        "acceptance_sha256": _sha256_file(acceptance_path),
        "typed": typed,
        "typed_path": str(typed_path),
        "typed_sha256": typed_sha256,
    }


def _copy_exact(source: Path, target: Path, expected_sha256: str) -> dict[str, object]:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise AgentError(f"immutable input is missing: {source}")
    before = _sha256_file(source)
    if before != expected_sha256:
        raise AgentError(f"immutable input SHA-256 differs: {before}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied = _sha256_file(target)
    after = _sha256_file(source)
    if copied != expected_sha256 or after != before:
        raise AgentError("immutable input changed while it was copied")
    return {
        "source": str(source),
        "copy": str(target.resolve()),
        "size": target.stat().st_size,
        "sha256": copied,
        "source_unchanged": after == before,
    }


def _driver_anchor(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    checkpoint = value.get("last_checkpoint") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or value.get("format_version") != 2
        or not isinstance(value.get("pipe_name"), str)
        or not value.get("pipe_name")
        or not isinstance(checkpoint, dict)
    ):
        raise AgentError("driver-state lacks a v2 cold checkpoint anchor")
    return {
        "pipe_name": value["pipe_name"],
        "episode_character_id": value.get("episode_character_id"),
        "last_checkpoint": copy.deepcopy(checkpoint),
    }


def _heartbeat(capabilities: object) -> dict[str, object] | None:
    if not isinstance(capabilities, dict):
        return None
    diagnostics = capabilities.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return None
    value = diagnostics.get("last_heartbeat")
    return copy.deepcopy(value) if isinstance(value, dict) else None


def _observer_sample(capabilities: object) -> dict[str, object] | None:
    heartbeat = _heartbeat(capabilities)
    if heartbeat is None:
        return None
    observer = heartbeat.get(OBSERVER_KEY)
    if not isinstance(observer, dict):
        return {
            "sequence": heartbeat.get("sequence"),
            "schema_ok": False,
            "error": "observer_object_missing",
        }
    callsites = observer.get("callsites")
    schema_ok = (
        observer.get("installed_mask") == 3
        and observer.get("failure") == 0
        and isinstance(callsites, list)
        and len(callsites) == 2
    )
    if schema_ok:
        for index, row in enumerate(callsites):
            schema_ok = bool(
                schema_ok
                and isinstance(row, dict)
                and all(field in row for field in REQUIRED_CALLSITE_FIELDS)
                and row.get("call_instruction_rva") == EXPECTED_CALL_RVAS[index]
            )
    return {
        "sequence": heartbeat.get("sequence"),
        "pid": heartbeat.get("pid"),
        "schema_ok": schema_ok,
        "installed_mask": observer.get("installed_mask"),
        "failure": observer.get("failure"),
        "callsites": copy.deepcopy(callsites),
    }


def _completed_signature(sample: dict[str, object]) -> tuple[object, ...] | None:
    if sample.get("schema_ok") is not True:
        return None
    rows = sample.get("callsites")
    if not isinstance(rows, list):
        return None
    completed = False
    values: list[object] = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        pre_count = row.get("pre_call_count")
        post_count = row.get("post_call_count")
        if not isinstance(pre_count, int) or not isinstance(post_count, int):
            return None
        if pre_count < post_count:
            return None
        completed = completed or post_count > 0
        values.extend(row.get(field) for field in REQUIRED_CALLSITE_FIELDS)
    return tuple(values) if completed else None


def _exact_build_proof(
    capabilities: object,
    *,
    game_executable_sha256: str,
    bridge_dll_sha256: str,
    expected_bridge_dll_sha256: str,
    bridge_injector_sha256: str,
    expected_bridge_injector_sha256: str,
) -> dict[str, object]:
    diagnostics = (
        capabilities.get("diagnostics")
        if isinstance(capabilities, dict)
        else None
    )
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    hello = hello if isinstance(hello, dict) else {}
    heartbeat = _heartbeat(capabilities)
    checks = {
        "game_version": hello.get("expected_ck3_version") == EXPECTED_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": str(
            hello.get("expected_ck3_sha256", "")
        ).upper()
        == EXPECTED_EXECUTABLE_SHA256,
        "managed_executable_sha256": game_executable_sha256
        == EXPECTED_EXECUTABLE_SHA256,
        "private_bridge_dll_sha256": bridge_dll_sha256
        == expected_bridge_dll_sha256,
        "injector_sha256": bridge_injector_sha256
        == expected_bridge_injector_sha256,
        "private_observer_heartbeat_present": isinstance(heartbeat, dict)
        and isinstance(heartbeat.get(OBSERVER_KEY), dict),
    }
    return {"checks": checks, "ok": all(checks.values())}


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    started_wall = utc_now()
    attempt = args.attempt_dir.expanduser().resolve()
    if attempt.exists():
        raise AgentError("fresh attempt directory already exists")
    attempt.mkdir(parents=True, exist_ok=False)
    report_path = attempt / "report.json"

    expected_checkpoint_sha = _expected_sha256(
        args.expected_checkpoint_sha256, "checkpoint SHA-256"
    )
    expected_driver_sha = _expected_sha256(
        args.expected_driver_state_sha256, "driver-state SHA-256"
    )
    expected_dll_sha = _expected_sha256(
        args.expected_bridge_dll_sha256, "bridge DLL SHA-256"
    )
    expected_injector_sha = _expected_sha256(
        args.expected_bridge_injector_sha256, "injector SHA-256"
    )
    source_checkpoint = args.source_checkpoint.expanduser().resolve()
    source_driver = args.source_driver_state.expanduser().resolve()
    source_before = {
        "checkpoint": _sha256_file(source_checkpoint),
        "driver_state": _sha256_file(source_driver),
    }
    session_state: dict[str, object] = {"report": None, "error": None}
    stop_event = threading.Event()
    session_done = threading.Event()
    session_thread: threading.Thread | None = None
    driver: NativeHeadlessGameplayDriver | None = None
    driver_closed = False
    session_started = False
    preparation: dict[str, object] | None = None
    inputs: dict[str, object] | None = None
    anchor: dict[str, object] | None = None
    readiness: dict[str, object] | None = None
    exact_build: dict[str, object] | None = None
    samples: list[dict[str, object]] = []
    observation_result = "not_started"
    primary_error: str | None = None
    cleanup: dict[str, object] = {"ok": True, "reason": "not started"}

    try:
        immutable = attempt / "inputs"
        checkpoint_copy = _copy_exact(
            source_checkpoint,
            immutable / NATIVE_SESSION_CHECKPOINT_FILENAME,
            expected_checkpoint_sha,
        )
        driver_copy = _copy_exact(
            source_driver,
            immutable / NATIVE_DRIVER_STATE_FILENAME,
            expected_driver_sha,
        )
        inputs = {"checkpoint": checkpoint_copy, "driver_state": driver_copy}
        anchor = _driver_anchor(immutable / NATIVE_DRIVER_STATE_FILENAME)
        if anchor.get("episode_character_id") != args.expected_character_id:
            raise AgentError("driver-state CharacterID differs")
        checkpoint_anchor = anchor.get("last_checkpoint")
        if (
            not isinstance(checkpoint_anchor, dict)
            or str(checkpoint_anchor.get("sha256", "")).upper()
            != expected_checkpoint_sha
            or checkpoint_anchor.get("date_raw") != args.expected_date_raw
        ):
            raise AgentError("driver-state checkpoint identity differs")

        state_dir = attempt / "state"
        spec = make_spec(state_dir, args.game_dir.expanduser().resolve())
        prepared = prepare_profile(spec)
        verified = verify_profile(spec)
        state_checkpoint = (
            spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
        )
        state_driver = (
            spec.state_dir / NATIVE_SESSION_QUEUE_DIRNAME / NATIVE_DRIVER_STATE_FILENAME
        )
        state_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        state_driver.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(checkpoint_copy["copy"], state_checkpoint)
        shutil.copy2(driver_copy["copy"], state_driver)
        preparation = {
            "state_dir": str(spec.state_dir),
            "profile_dir": str(spec.profile_dir),
            "environment_sha256": verified.get("environment_sha256"),
            "production_tree_sha256": prepared.get("mod", {}).get(
                "production_tree_sha256"
            ),
            "cold_validation": validate_cold_start_checkpoint_for_pipe(
                spec, str(anchor["pipe_name"])
            ),
        }
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=str(anchor["pipe_name"]),
            dll_path=args.bridge_dll.expanduser().resolve(),
            injector_path=args.bridge_injector.expanduser().resolve(),
        )

        def supervise() -> None:
            try:
                session_state["report"] = native_session(
                    spec,
                    timeout_seconds=float(args.timeout) + 90.0,
                    native_bridge=config,
                    input_stream=None,
                    output_stream=None,
                    poll_interval_seconds=0.05,
                    cold_start_checkpoint=True,
                    stop_event=stop_event,
                )
            except BaseException as error:
                session_state["error"] = f"{type(error).__name__}: {error}"
            finally:
                session_done.set()

        driver = NativeHeadlessGameplayDriver(
            str(anchor["pipe_name"]),
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        session_thread = threading.Thread(
            target=supervise,
            name="xar-g2-truce-native-callsite-observer-live",
            daemon=False,
        )
        session_thread.start()
        session_started = True
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=float(args.readiness_timeout),
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=True,
            allow_terminal=False,
        )
        capabilities = driver.capabilities()
        exact_build = _exact_build_proof(
            capabilities,
            game_executable_sha256=_sha256_file(spec.game_exe),
            bridge_dll_sha256=_sha256_file(config.dll_path),
            expected_bridge_dll_sha256=expected_dll_sha,
            bridge_injector_sha256=_sha256_file(config.injector_path),
            expected_bridge_injector_sha256=expected_injector_sha,
        )
        if exact_build.get("ok") is not True:
            raise RuntimeError("exact-build/private-observer proof failed")

        deadline = time.monotonic() + float(args.observation_timeout)
        last_sequence: object = None
        previous_signature: tuple[object, ...] | None = None
        stable_count = 0
        while time.monotonic() < deadline:
            if session_done.is_set():
                observation_result = "process_exit_before_stable_native_return"
                break
            sample = _observer_sample(driver.capabilities())
            if sample is not None and sample.get("sequence") != last_sequence:
                last_sequence = sample.get("sequence")
                samples.append(sample)
                if sample.get("schema_ok") is not True:
                    observation_result = "observer_schema_or_install_red"
                    break
                signature = _completed_signature(sample)
                if signature is not None and signature == previous_signature:
                    stable_count += 1
                elif signature is not None:
                    stable_count = 1
                else:
                    stable_count = 0
                previous_signature = signature
                if stable_count >= 2:
                    observation_result = "two_stable_native_pre_post_samples"
                    break
            time.sleep(0.05)
        else:
            observation_result = "observation_timeout_without_stable_native_return"
        if observation_result != "two_stable_native_pre_post_samples":
            raise RuntimeError(observation_result)
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None and session_started:
            session_thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = detail if primary_error is None else f"{primary_error}; {detail}"
        cleanup = _cleanup_report(
            session_state.get("report"),
            session_error=session_state.get("error"),
            driver_closed=driver_closed,
            elapsed_seconds=stop_elapsed,
        )
        if cleanup.get("ok") is not True and primary_error is None:
            primary_error = str(cleanup.get("reason") or "cleanup not proven")

    source_after = {
        "checkpoint": _sha256_file(source_checkpoint),
        "driver_state": _sha256_file(source_driver),
    }
    source_unchanged = source_before == source_after
    if not source_unchanged and primary_error is None:
        primary_error = "immutable checkpoint inputs changed"
    ok = bool(
        primary_error is None
        and exact_build
        and exact_build.get("ok") is True
        and observation_result == "two_stable_native_pre_post_samples"
        and cleanup.get("ok") is True
        and source_unchanged
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": REPORT_KIND,
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "status": "green" if ok else "red",
        "ok": ok,
        "attempt_dir": str(attempt),
        "report_path": str(report_path),
        "policy": {
            "heartbeat_only": True,
            "mcp_queries": [],
            "evaluator_requests": [],
            "context_effects": [],
            "mutation_commands": [],
            "time_advanced": False,
        },
        "inputs": inputs,
        "driver_anchor": anchor,
        "preparation": preparation,
        "readiness": readiness,
        "exact_build_proof": exact_build,
        "observation": {
            "observer_key": OBSERVER_KEY,
            "expected_call_instruction_rvas": list(EXPECTED_CALL_RVAS),
            "result": observation_result,
            "samples": samples,
        },
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "source_invariant": {
            "before": source_before,
            "after": source_after,
            "unchanged": source_unchanged,
        },
        "error": primary_error,
    }
    _write_json_atomic(report_path, payload)
    return payload, 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload, exit_code = _run(args)
        evidence = _materialize_acceptance_evidence(
            report_path=Path(str(payload["report_path"])),
            manifest_path=args.ready_manifest,
        )
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    acceptance = evidence["acceptance"]
    if acceptance.get("ok") is not True:
        exit_code = 1
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "status": payload.get("status"),
                "report_path": payload.get("report_path"),
                "observation_result": payload.get("observation", {}).get("result"),
                "typed_postprocess_path": evidence["typed_path"],
                "typed_postprocess_sha256": evidence["typed_sha256"],
                "acceptance_report_path": evidence["acceptance_path"],
                "acceptance_report_sha256": evidence["acceptance_sha256"],
                "typed_status": acceptance.get("status"),
                "typed_classification": acceptance.get("classification"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
