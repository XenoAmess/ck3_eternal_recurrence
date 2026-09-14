"""Run one exact-build paused faction-targeting row private probe.

The runner owns one R692 launch, preserves the complete private heartbeat
before interpreting it, and stops immediately after one terminal publication.
It never promotes the private payload to a public capability or schema.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import threading
import time
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


PROBE_KEY = "g2_faction_targeting_row_probe_v1_async"
RESULT_SCHEMA = "g2_faction_targeting_row_probe_v1"
EXPECTED_OLD_ROUND = "R691"
EXPECTED_NEW_ROUND = "R692"
EXPECTED_GAME_VERSION = "1.19.0.6"
REVISION_PATTERN = re.compile(r"[0-9a-fA-F]{40}\Z")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expected_sha256(value: str, name: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 64 or any(
        character not in "0123456789ABCDEF" for character in normalized
    ):
        raise ValueError(f"{name} must be 64 hexadecimal digits")
    return normalized


def _positive_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RuntimeError(f"{name} must be a positive integer: {value!r}")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RuntimeError(f"{name} must be a nonnegative integer: {value!r}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--source-save", type=Path, required=True)
    parser.add_argument("--save-name", default="faction-targeting-row-source.ck3")
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
    parser.add_argument("--publish-timeout", type=float, default=90.0)
    return parser


def validate_parameter_contract(args: argparse.Namespace) -> None:
    if args.old_round != EXPECTED_OLD_ROUND or args.new_round != EXPECTED_NEW_ROUND:
        raise ValueError("this one-shot runner is frozen to R691 -> R692")
    if not REVISION_PATTERN.fullmatch(args.candidate_revision):
        raise ValueError("candidate revision must be one full Git commit")
    if args.expected_character_id <= 0:
        raise ValueError("expected character id must be positive")
    if args.readiness_timeout <= 0 or args.publish_timeout <= 0:
        raise ValueError("timeouts must be positive")


def validate_candidate_manifest(
    manifest: dict[str, object], args: argparse.Namespace, expected_exe_sha256: str
) -> None:
    source = manifest.get("source")
    exact_build = manifest.get("exact_build")
    next_live = manifest.get("next_live")
    if not isinstance(source, dict) or source.get("commit") != args.candidate_revision:
        raise RuntimeError("candidate manifest is not bound to candidate revision")
    if not isinstance(exact_build, dict) or exact_build != {
        "game_version": EXPECTED_GAME_VERSION,
        "executable_sha256": expected_exe_sha256,
    }:
        raise RuntimeError("candidate manifest exact-build identity drifted")
    if not isinstance(next_live, dict):
        raise RuntimeError("candidate manifest lacks next_live")
    expected_live = {
        "old_round": args.old_round,
        "new_round": args.new_round,
        "unique_pipe": args.pipe,
    }
    for key, value in expected_live.items():
        if next_live.get(key) != value:
            raise RuntimeError(f"candidate manifest next_live.{key} drifted")


def persist_raw_probe(
    output: Path,
    *,
    diagnostics: dict[str, object],
    probe: dict[str, object],
    readiness: dict[str, object],
) -> None:
    write_json_atomic(
        output,
        {
            "schema": "xar.ck3.private.faction_targeting_row_raw_probe_v1",
            "captured_at": _now(),
            "readiness": readiness,
            "diagnostics": diagnostics,
            "probe": probe,
            "terminal_result": probe.get("terminal_result"),
            "semantic_validation_started": False,
        },
    )


def _heartbeat_probe(
    driver: NativeHeadlessGameplayDriver,
) -> tuple[dict[str, object], dict[str, object]]:
    diagnostics = driver.diagnostics()
    heartbeat = (
        diagnostics.get("last_heartbeat") if isinstance(diagnostics, dict) else None
    )
    probe = heartbeat.get(PROBE_KEY) if isinstance(heartbeat, dict) else None
    if not isinstance(diagnostics, dict) or not isinstance(probe, dict):
        raise RuntimeError("private faction-targeting probe missing from heartbeat")
    return diagnostics, probe


def validate_probe_envelope(probe: dict[str, object]) -> None:
    expected = {"private_build": True, "read_only": True, "advertised": False}
    for key, value in expected.items():
        if probe.get(key) != value:
            raise RuntimeError(f"private heartbeat field {key} mismatch")
    if probe.get("async_state") not in {
        "waiting-snapshot",
        "query-queued",
        "query-executing",
        "awaiting-observer",
        "terminal",
        "blocked",
    }:
        raise RuntimeError("private heartbeat has invalid async_state")
    if not isinstance(probe.get("query_in_flight"), bool) or not isinstance(
        probe.get("terminal_published"), bool
    ):
        raise RuntimeError("private heartbeat booleans are malformed")
    for field in (
        "last_submit_result",
        "last_wait_result",
        "last_reclaim_result",
        "async_failure_flags",
        "admission_generation",
    ):
        _nonnegative_int(probe.get(field), field)
    if not isinstance(probe.get("observer"), dict):
        raise RuntimeError("private heartbeat observer diagnostics are missing")
    if probe["terminal_published"] is False and probe.get("terminal_result") is not None:
        raise RuntimeError("nonterminal heartbeat leaked a terminal result")


def _validate_binding(
    value: object, *, expected_character_id: int, expected_date_raw: int, name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "paused",
        "proof_epoch",
        "snapshot_revision",
        "date_raw",
        "player_character_id",
    }:
        raise RuntimeError(f"{name} binding shape drifted")
    if value.get("paused") is not True:
        raise RuntimeError(f"{name} is not paused")
    _positive_int(value.get("proof_epoch"), f"{name}.proof_epoch")
    _positive_int(value.get("snapshot_revision"), f"{name}.snapshot_revision")
    if value.get("date_raw") != expected_date_raw:
        raise RuntimeError(f"{name}.date_raw crossed the paused frame")
    if value.get("player_character_id") != expected_character_id:
        raise RuntimeError(f"{name}.player_character_id drifted")
    return value


def validate_terminal_result(
    probe: dict[str, object], *, expected_character_id: int, expected_date_raw: int
) -> dict[str, object]:
    if probe.get("terminal_published") is not True or probe.get("async_state") != "terminal":
        raise RuntimeError("probe did not reach its terminal heartbeat")
    if probe.get("query_in_flight") is not False:
        raise RuntimeError("terminal heartbeat retained an in-flight query")
    if probe.get("async_failure_flags") != 0:
        raise RuntimeError("async glue published failure flags")
    result = probe.get("terminal_result")
    if not isinstance(result, dict):
        raise RuntimeError("terminal heartbeat lacks a result object")
    if result.get("schema") != RESULT_SCHEMA or result.get("private") is not True:
        raise RuntimeError("terminal private schema drifted")
    if result.get("raw_pointers_persisted") is not False:
        raise RuntimeError("terminal result persisted process-local pointers")
    required = _validate_binding(
        result.get("required_binding"),
        expected_character_id=expected_character_id,
        expected_date_raw=expected_date_raw,
        name="required",
    )
    observed = _validate_binding(
        result.get("observed_binding"),
        expected_character_id=expected_character_id,
        expected_date_raw=expected_date_raw,
        name="observed",
    )
    if observed != required:
        raise RuntimeError("terminal observer binding differs from required binding")
    generation = _positive_int(result.get("published_generation"), "published_generation")
    if generation & 1:
        raise RuntimeError("terminal observer generation is unstable/odd")
    terminal = result.get("terminal")
    unavailable_reasons = _nonnegative_int(
        result.get("unavailable_reasons"), "unavailable_reasons"
    )
    observer_failures = _nonnegative_int(
        result.get("observer_failure_flags"), "observer_failure_flags"
    )
    if terminal == "unavailable":
        raise RuntimeError(
            "private faction-targeting probe is unavailable: "
            f"reasons={unavailable_reasons}, observer_failures={observer_failures}"
        )
    if terminal not in {"ready", "known-empty"}:
        raise RuntimeError(f"unknown faction probe terminal: {terminal!r}")
    if unavailable_reasons != 0 or observer_failures != 0:
        raise RuntimeError("available terminal retained failure flags")
    count = _nonnegative_int(result.get("faction_count"), "faction_count")
    rows = result.get("factions")
    if not isinstance(rows, list) or len(rows) != count:
        raise RuntimeError("faction rows do not match faction_count")
    if (terminal == "known-empty") != (count == 0):
        raise RuntimeError("known-empty terminal disagrees with faction_count")
    identities: list[int] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"factions[{index}] is not an object")
        faction_id = _positive_int(row.get("faction_id"), f"factions[{index}].faction_id")
        if row.get("target_character_id") != expected_character_id:
            raise RuntimeError(f"factions[{index}] targets another character")
        leader = row.get("leader_character_id")
        if leader is not None:
            _positive_int(leader, f"factions[{index}].leader_character_id")
        members = row.get("character_member_ids")
        if not isinstance(members, list):
            raise RuntimeError(f"factions[{index}].character_member_ids is malformed")
        member_ids = [
            _positive_int(value, f"factions[{index}].character_member_ids")
            for value in members
        ]
        if member_ids != sorted(set(member_ids)):
            raise RuntimeError(f"factions[{index}] member identities are not sorted unique")
        if row.get("leader_present_in_character_members") is not (
            leader is not None and leader in member_ids
        ):
            raise RuntimeError(f"factions[{index}] leader membership flag drifted")
        identities.append(faction_id)
    if identities != sorted(set(identities)):
        raise RuntimeError("faction identities are not sorted unique")
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validate_parameter_contract(args)
    artifacts = args.artifact_dir.expanduser().resolve()
    state_dir = args.state_dir.expanduser().resolve()
    if state_dir.exists():
        raise ValueError(f"R692 requires a fresh state directory: {state_dir}")
    for evidence_name in ("raw-probe.json", "report.json", "round-ownership.json"):
        if (artifacts / evidence_name).exists():
            raise ValueError(f"R692 refuses pre-existing evidence: {evidence_name}")
    artifacts.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema": "xar.ck3.private.faction_targeting_row_live_v1",
        "status": "preflight",
        "policy": {
            "paused_only": True,
            "gameplay_actions": 0,
            "date_advance": False,
            "save_mutation": False,
            "same_round_retry": False,
            "terminal_publish_then_immediate_stop": True,
        },
        "round": {
            "old": args.old_round,
            "new": args.new_round,
            "current": f"{args.new_round} pending launch",
            "reason": "one paused faction-targeting row private heartbeat",
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
        manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8-sig"))
        if not isinstance(manifest, dict):
            raise RuntimeError("candidate manifest root is not an object")
        validate_candidate_manifest(manifest, args, expected["exe"])

        prepare_profile(spec)
        stage_mod_bridge_companion(spec)
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
            "ck3_inventory": ck3_process_inventory(),
        }
        write_json_atomic(artifacts / "preflight.json", report["preflight"])
        write_json_atomic(artifacts / "round-ownership.json", report["round"])

        stack.enter_context(exclusive_launch_lock(spec.game_exe))
        stack.enter_context(exclusive_state_lock(spec.state_dir, "faction-targeting-row-private-probe"))
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

        readiness = _wait_for_readiness(
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
                raise RuntimeError("CK3 exited before terminal publication")
            current = driver.take_internal_semantic_snapshot()
            if current.get("paused") is not True or current.get("date_raw") != initial_date:
                raise RuntimeError("paused/date invariant changed before publication")
            diagnostics, probe = _heartbeat_probe(driver)
            validate_probe_envelope(probe)
            last_probe = probe
            if probe.get("terminal_published") is True:
                persist_raw_probe(
                    artifacts / "raw-probe.json",
                    diagnostics=diagnostics,
                    probe=probe,
                    readiness=readiness,
                )
                result = validate_terminal_result(
                    probe,
                    expected_character_id=args.expected_character_id,
                    expected_date_raw=initial_date,
                )
                report["capture"] = {
                    "readiness": readiness,
                    "result": result,
                    "raw_probe": str(artifacts / "raw-probe.json"),
                }
                report["status"] = "green_pending_cleanup"
                break
            if probe.get("async_state") == "blocked":
                raise RuntimeError(f"private async probe blocked: {probe!r}")
            time.sleep(0.05)
        else:
            raise RuntimeError(
                "private heartbeat did not publish within timeout; "
                "refresh the Factions view after paused admission: "
                f"{last_probe!r}"
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
    print(
        json.dumps(
            {"status": report["status"], "ok": report["ok"], "red": report.get("red")},
            ensure_ascii=False,
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
