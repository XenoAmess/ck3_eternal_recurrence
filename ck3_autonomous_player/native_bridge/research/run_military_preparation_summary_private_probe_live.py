"""Run one exact-build paused military-preparation private-probe heartbeat.

This is the canonical successor to the artifact-local R685 runner.  It stages
the repository data bridge as an isolated companion mod, proves all five
script-value wrappers before launch ownership, and persists the unclassified
raw probe before applying the semantic GREEN assertions.
"""

from __future__ import annotations

import argparse
import json
import shutil
import threading
import time
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.companion_profile import (
    stage_mod_bridge_companion,
    verify_mod_bridge_companion,
)
from xar_autoplayer.environment import (
    ck3_process_inventory,
    make_spec,
    prepare_profile,
    sha256_file,
    write_json_atomic,
)
from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
from xar_autoplayer.native_auto_run import _wait_for_readiness
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked


PROBE_KEY = "g2_military_preparation_summary_v1_private_probe"
RESULT_KEY = "g2_military_preparation_summary_v1"
EXPECTED_OLD_ROUND = "R685"
EXPECTED_NEW_ROUND = "R686"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expected_sha256(value: str, name: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 64 or any(
        character not in "0123456789ABCDEF" for character in normalized
    ):
        raise ValueError(f"{name} must be 64 hexadecimal digits")
    return normalized


def persist_raw_probe_before_validation(
    output: Path,
    *,
    diagnostics: dict[str, object],
    probe: dict[str, object],
    binding: dict[str, object],
) -> dict[str, object]:
    """Persist the full published object before any semantic assertion."""

    raw = {
        "schema": "xar.ck3.private.military_preparation_raw_probe_v1",
        "captured_at": _now(),
        "binding": binding,
        "diagnostics": diagnostics,
        "probe": probe,
        "result": probe.get("result"),
        "semantic_validation_started": False,
    }
    write_json_atomic(output, raw)
    return raw


def persist_then_validate(
    output: Path,
    *,
    diagnostics: dict[str, object],
    probe: dict[str, object],
    binding: dict[str, object],
    validator: Callable[[dict[str, object]], dict[str, object]],
) -> dict[str, object]:
    """Enforce the evidence order even when validation raises."""

    persist_raw_probe_before_validation(
        output, diagnostics=diagnostics, probe=probe, binding=binding
    )
    return validator(probe)


def _heartbeat_probe(
    driver: NativeHeadlessGameplayDriver,
) -> tuple[dict[str, object], dict[str, object]]:
    diagnostics = driver.diagnostics()
    heartbeat = (
        diagnostics.get("last_heartbeat") if isinstance(diagnostics, dict) else None
    )
    probe = heartbeat.get(PROBE_KEY) if isinstance(heartbeat, dict) else None
    if not isinstance(diagnostics, dict) or not isinstance(probe, dict):
        raise RuntimeError("private military-preparation probe missing from heartbeat")
    return diagnostics, probe


def _validate_envelope(probe: dict[str, object]) -> None:
    expected = {
        "private_build": True,
        "read_only": True,
        "advertised": False,
        "private_key": PROBE_KEY,
        "installed": True,
    }
    for key, value in expected.items():
        if probe.get(key) != value:
            raise RuntimeError(f"private heartbeat field {key} mismatch: {probe.get(key)!r}")
    count = probe.get("published_execution_count")
    if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= 1:
        raise RuntimeError(f"invalid one-shot execution count: {count!r}")
    if not isinstance(probe.get("query_in_flight"), bool):
        raise RuntimeError("query_in_flight is not boolean")


def _validate_published(
    probe: dict[str, object],
    *,
    initial_date: int,
    expected_character_id: int,
    expected_exe_sha256: str,
) -> dict[str, object]:
    _validate_envelope(probe)
    if probe.get("request_prepared") is not True or probe.get("result_published") is not True:
        raise RuntimeError("probe did not publish its prepared one-shot result")
    if probe.get("published_execution_count") != 1 or probe.get("query_in_flight") is not False:
        raise RuntimeError("probe did not finish exactly one execution")
    result = probe.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("published heartbeat has no result object")
    required = {
        "schema": "xar.ck3.private.military_preparation_summary_v1",
        "schema_version": 1,
        "private_key": RESULT_KEY,
        "status": "available",
        "failure_flags": 0,
        "observation_ready": True,
        "offline_fixture": False,
        "raw_pointer_fields_persisted": False,
    }
    for key, value in required.items():
        if result.get(key) != value:
            raise RuntimeError(f"published result field {key} mismatch: {result.get(key)!r}")
    exact = result.get("exact_build")
    if (
        not isinstance(exact, dict)
        or exact.get("game_version") != "1.19.0.6"
        or str(exact.get("executable_sha256", "")).upper()
        != expected_exe_sha256
    ):
        raise RuntimeError(f"published exact-build identity mismatch: {exact!r}")
    source = result.get("source")
    if (
        not isinstance(source, dict)
        or source.get("paused") is not True
        or source.get("played_character_id") != expected_character_id
        or source.get("date_raw") != initial_date
    ):
        raise RuntimeError(f"published source identity mismatch: {source!r}")
    revision = source.get("snapshot_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision <= 0:
        raise RuntimeError(f"invalid source snapshot revision: {revision!r}")
    stock = result.get("stock_final_values")
    maa = result.get("maa_gold_band")
    if not isinstance(stock, dict) or not isinstance(maa, dict):
        raise RuntimeError("published result lacks value groups")
    groups = (
        (
            stock,
            (
                "current_military_strength_raw",
                "max_military_strength_raw",
                "number_of_knights_raw",
                "max_number_of_knights_raw",
            ),
        ),
        (
            maa,
            (
                "expense_relative_raw",
                "min_raw",
                "ideal_raw",
                "max_raw",
                "chance_below_min_raw",
                "chance_below_ideal_raw",
            ),
        ),
    )
    for group, fields in groups:
        for field in fields:
            value = group.get(field)
            if not isinstance(value, int) or isinstance(value, bool):
                raise RuntimeError(
                    f"published value {field} is not an integer: {value!r}"
                )
        if group.get("scale") != 100000:
            raise RuntimeError(
                f"published fixed-point scale mismatch: {group.get('scale')!r}"
            )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--source-save", type=Path, required=True)
    parser.add_argument("--save-name", default="military-preparation-source.ck3")
    parser.add_argument("--expected-save-sha256", required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--expected-candidate-manifest-sha256", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--expected-bridge-dll-sha256", required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--expected-bridge-injector-sha256", required=True)
    parser.add_argument("--expected-game-exe-sha256", required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--pipe", required=True)
    parser.add_argument("--old-round", required=True)
    parser.add_argument("--new-round", required=True)
    parser.add_argument("--candidate-revision", required=True)
    parser.add_argument("--readiness-timeout", type=float, default=300.0)
    parser.add_argument("--publish-timeout", type=float, default=20.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    artifacts = args.artifact_dir.expanduser().resolve()
    state_dir = args.state_dir.expanduser().resolve()
    if args.old_round != EXPECTED_OLD_ROUND or args.new_round != EXPECTED_NEW_ROUND:
        raise ValueError(
            "this one-shot successor is frozen to old round R685 and new round R686"
        )
    if state_dir.exists():
        raise ValueError(f"R686 requires a fresh state directory: {state_dir}")
    for evidence_name in ("raw-probe.json", "report.json", "round-ownership.json"):
        if (artifacts / evidence_name).exists():
            raise ValueError(
                f"R686 refuses pre-existing run evidence: {artifacts / evidence_name}"
            )
    artifacts.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema": "xar.ck3.private.military_preparation_live_v2",
        "status": "preflight",
        "policy": {
            "paused_only": True,
            "ui_inputs": 0,
            "gameplay_actions": 0,
            "date_advance": False,
            "save_mutation": False,
            "same_round_retry": False,
        },
        "round": {
            "old": args.old_round,
            "new": args.new_round,
            "current": f"{args.new_round} pending launch",
            "reason": "one paused-only raw-persisted military-preparation heartbeat",
            "before_version": args.candidate_revision,
            "after_version": args.candidate_revision,
            "dll_or_game_file_change": True,
        },
        "red": None,
        "started_at": _now(),
    }
    expected = {
        "save": _expected_sha256(args.expected_save_sha256, "save SHA-256"),
        "manifest": _expected_sha256(
            args.expected_candidate_manifest_sha256, "manifest SHA-256"
        ),
        "dll": _expected_sha256(args.expected_bridge_dll_sha256, "DLL SHA-256"),
        "injector": _expected_sha256(
            args.expected_bridge_injector_sha256, "injector SHA-256"
        ),
        "exe": _expected_sha256(args.expected_game_exe_sha256, "EXE SHA-256"),
    }
    spec = make_spec(state_dir, args.game_dir)
    handle = None
    driver = None
    cleanup = None
    target_save: Path | None = None
    stack = ExitStack()
    try:
        if ck3_process_inventory().get("processes"):
            raise RuntimeError("prelaunch CK3 inventory is nonzero")
        hashes = {
            "save": sha256_file(args.source_save),
            "manifest": sha256_file(args.candidate_manifest),
            "dll": sha256_file(args.bridge_dll),
            "injector": sha256_file(args.bridge_injector),
            "exe": sha256_file(spec.game_exe),
        }
        if {key: value.upper() for key, value in hashes.items()} != expected:
            raise RuntimeError(f"frozen input hash mismatch: {hashes!r}")

        prepare_profile(spec)
        companion = stage_mod_bridge_companion(spec)
        target_save = spec.profile_dir / "save games" / args.save_name
        target_save.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.source_save, target_save)
        if sha256_file(target_save).upper() != expected["save"]:
            raise RuntimeError("profile save copy differs from source")
        companion = verify_mod_bridge_companion(spec)
        if companion.get("status") != "green":
            raise RuntimeError("companion preflight is not GREEN")
        report["preflight"] = {
            "hashes": hashes,
            "companion": companion,
            "target_save": str(target_save),
            "target_save_sha256": sha256_file(target_save),
            "ck3_inventory": ck3_process_inventory(),
        }
        write_json_atomic(artifacts / "preflight.json", report["preflight"])
        write_json_atomic(artifacts / "round-ownership.json", report["round"])

        stack.enter_context(exclusive_launch_lock(spec.game_exe))
        stack.enter_context(
            exclusive_state_lock(spec.state_dir, "military-preparation-private-probe")
        )
        driver = NativeHeadlessGameplayDriver(
            args.pipe,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        handle = launch(
            spec,
            native_bridge=NativeBridgeLaunchConfig(
                mode="native-headless",
                pipe_name=args.pipe,
                dll_path=args.bridge_dll,
                injector_path=args.bridge_injector,
            ),
            continue_last_save=False,
            load_save_name=Path(args.save_name).stem,
            # The explicit companion verifier above replaces the normal
            # production-singleton verifier for this disposable playset.
            verify_prepared_profile=False,
        )
        report["round"].update(
            {
                "current": args.new_round,
                "pid": int(handle.process.pid),
                "creation_date": handle.ck3_creation_date,
                "watchdog_pid": handle.watchdog_pid,
                "watchdog_creation_date": handle.watchdog_creation_date,
                "launch_command": handle.command,
                "launched_at": _now(),
            }
        )
        write_json_atomic(artifacts / "round-ownership.json", report["round"])

        binding = _wait_for_readiness(
            driver,
            session_done=threading.Event(),
            session_state={},
            timeout_seconds=args.readiness_timeout,
            stable_seconds=1.0,
            poll_interval_seconds=0.1,
            cold_start_checkpoint=False,
            allow_terminal=False,
            expected_character_id=args.expected_character_id,
        )
        snapshot = driver.take_internal_semantic_snapshot()
        initial_date = snapshot.get("date_raw")
        if (
            snapshot.get("paused") is not True
            or snapshot.get("episode_character_id") != args.expected_character_id
            or not isinstance(initial_date, int)
            or isinstance(initial_date, bool)
        ):
            raise RuntimeError("stable paused snapshot identity differs")
        deadline = time.monotonic() + args.publish_timeout
        last_probe = None
        while time.monotonic() < deadline:
            if handle.process.poll() is not None:
                raise RuntimeError("CK3 exited before heartbeat publication")
            current = driver.take_internal_semantic_snapshot()
            if current.get("paused") is not True or current.get("date_raw") != initial_date:
                raise RuntimeError("paused/date invariant changed before publication")
            diagnostics, probe = _heartbeat_probe(driver)
            _validate_envelope(probe)
            last_probe = probe
            if probe.get("result_published") is True:
                result = persist_then_validate(
                    artifacts / "raw-probe.json",
                    diagnostics=diagnostics,
                    probe=probe,
                    binding=binding,
                    validator=lambda value: _validate_published(
                        value,
                        initial_date=initial_date,
                        expected_character_id=args.expected_character_id,
                        expected_exe_sha256=expected["exe"],
                    ),
                )
                report["capture"] = {
                    "binding": binding,
                    "result": result,
                    "raw_probe": str(artifacts / "raw-probe.json"),
                }
                report["status"] = "green_pending_cleanup"
                break
            time.sleep(0.05)
        else:
            raise RuntimeError(
                f"private heartbeat did not publish within timeout: {last_probe!r}"
            )
    except BaseException as error:
        report["red"] = {
            "reason": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
            "at": _now(),
        }
        report["status"] = "red_pending_cleanup"
        if (artifacts / "raw-probe.json").is_file():
            report["raw_probe"] = str(artifacts / "raw-probe.json")
    finally:
        if handle is not None:
            try:
                cleanup = stop_tracked(handle, require_running=True)
            except BaseException as error:
                cleanup = {
                    "ok": False,
                    "error": f"{type(error).__name__}: {error}",
                    "traceback": traceback.format_exc(),
                }
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_error"] = f"{type(error).__name__}: {error}"
        try:
            stack.close()
        except BaseException as error:
            report["lock_release_error"] = f"{type(error).__name__}: {error}"
        post = ck3_process_inventory()
        report["cleanup"] = cleanup
        report["postflight_ck3_inventory"] = post
        report["source_save_after_sha256"] = (
            sha256_file(args.source_save) if args.source_save.is_file() else None
        )
        report["target_save_after_sha256"] = (
            sha256_file(target_save)
            if target_save is not None and target_save.is_file()
            else None
        )
        report["source_save_unchanged"] = (
            str(report["source_save_after_sha256"]).upper() == expected["save"]
        )
        report["target_save_unchanged"] = (
            str(report["target_save_after_sha256"]).upper() == expected["save"]
        )
        report["round"]["current"] = (
            f"{args.new_round} terminated" if handle is not None else f"{args.new_round} not launched"
        )
        clean = (
            not post.get("processes")
            and isinstance(cleanup, dict)
            and cleanup.get("cleanup_proven") is True
            and cleanup.get("tree_gone") is True
        )
        report["ok"] = bool(
            report.get("red") is None
            and isinstance(report.get("capture"), dict)
            and clean
            and report["source_save_unchanged"] is True
            and report["target_save_unchanged"] is True
        )
        report["status"] = "green" if report["ok"] else "red"
        report["finished_at"] = _now()
        write_json_atomic(artifacts / "report.json", report)
        write_json_atomic(artifacts / "round-ownership.json", report["round"])
    print(json.dumps({"status": report["status"], "ok": report["ok"], "red": report.get("red")}, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
