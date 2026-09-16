"""Owned bounded LIFE2 current-state read from an ordinary feudal save.

``--preflight-only`` verifies the frozen production profile, paired R739
checkpoint, exact game/native hashes, and zero local CK3 processes without
launching. Only the sole CK3 operator supplies a new R{n} for the live mode.
The live mode performs one private read, then reclaims the CK3 process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

from run_player_lifestyle_current_state_read import (
    run_owned_paused_life2_current_state_read,
)


SCHEMA = "xar.ck3.g2_m4_life2_paused_candidate_v1"
EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
SAVE_SHA256 = "d8bdc3c44d21a6f94dc7e4c050db464f6c5036d5ba7e66233354b171f3401474"
DRIVER_SHA256 = "163850711947eacb8dfb3dec82e39bad332bd00bc119dbb36642ed701de4fb1a"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def preflight(candidate_root: Path) -> tuple[object, dict[str, object], dict[str, object]]:
    root = candidate_root.resolve()
    manifest_path = root / "candidate-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    _need(manifest.get("schema") == SCHEMA and manifest.get("status") == "ready-no-launch"
          and manifest.get("public_registered_or_advertised") is False,
          "LIFE2 candidate manifest is missing or advertised")
    _need(Path(str(manifest.get("candidate_root"))).resolve() == root,
          "LIFE2 candidate belongs to another artifact root")
    source = Path(str(manifest["source_repo"]))
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"), str(source / "tools")]
    from xar_autoplayer.environment import ck3_process_inventory, make_spec, verify_profile
    from xar_autoplayer.native_session import validate_cold_start_checkpoint_for_pipe
    from xar_autoplayer.bridge.native_driver import load_native_driver_state_for_resume

    spec = make_spec(Path(str(manifest["state_dir"])), Path(str(manifest["game_dir"])))
    _need(_sha(spec.game_exe) == manifest["game_exe_sha256"] == EXE_SHA256,
          "CK3 executable differs from exact 1.19.0.6 build")
    for key, hash_key in (("dll", "dll_sha256"), ("injector", "injector_sha256"),
                          ("source_save", "source_save_sha256"),
                          ("source_driver", "source_driver_sha256"),
                          ("prepared_save", "prepared_save_sha256"),
                          ("prepared_driver", "prepared_driver_sha256")):
        _need(_sha(Path(str(manifest[key]))) == manifest[hash_key],
              f"frozen LIFE2 {key} SHA differs")
    _need(manifest["source_save_sha256"] == manifest["prepared_save_sha256"] == SAVE_SHA256
          and manifest["source_driver_sha256"] == manifest["prepared_driver_sha256"] == DRIVER_SHA256,
          "R739 ordinary feudal save/driver pairing changed")
    cache_path = Path(str(manifest["cmake_cache_path"]))
    _need(_sha(cache_path) == manifest["cmake_cache_sha256"], "LIFE2 build cache changed")
    cache = cache_path.read_text(encoding="utf-8", errors="replace")
    _need("XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1:BOOL=ON" in cache,
          "private LIFE2 slot43 feature is not ON in candidate build")
    profile = verify_profile(spec)
    _need(profile.get("environment_sha256") == manifest["profile_environment_sha256"],
          "prepared production profile differs")
    pipe = str(manifest["pipe"])
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, pipe)
    driver_state = load_native_driver_state_for_resume(
        Path(str(manifest["prepared_driver"])), pipe)
    _need(isinstance(driver_state, dict)
          and checkpoint.get("saved_date_raw") == manifest["expected_date_raw"]
          and driver_state.get("episode_character_id") == manifest["expected_actor_id"]
          and driver_state.get("episode_run_id") == manifest["episode_run_id"],
          "R739 cold restore actor/date/episode differs")
    inventory = ck3_process_inventory()
    _need(not inventory.get("processes"), "local CK3 instance occupies the read candidate slot")
    return spec, manifest, {
        "status": "ready-no-launch", "ck3_launched": False,
        "ck3_inventory": inventory,
        "profile_environment_sha256": profile.get("environment_sha256"),
        "checkpoint": checkpoint,
        "episode_run_id": driver_state.get("episode_run_id"),
    }


def run(candidate_root: Path, round_id: str, evidence: Path) -> int:
    spec, manifest, ready = preflight(candidate_root)
    _need(round_id.startswith("R") and round_id[1:].isdigit()
          and int(round_id[1:]) > 0, "sole operator must allocate a new R{n}")
    _need(not evidence.exists(), "evidence directory already exists for this round")
    evidence.mkdir(parents=True)
    report: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_life2_paused_live_v1",
        "candidate": str(candidate_root.resolve()), "round_id": round_id,
        "status": "unexecuted", "preflight": ready,
        "exact_ck3_exe_sha256": manifest["game_exe_sha256"],
        "native_source_commit": manifest["native_source_commit"],
        "native_dll_sha256": manifest["dll_sha256"],
        "source_save_sha256": manifest["source_save_sha256"],
        "source_driver_sha256": manifest["source_driver_sha256"],
        "public_registered_or_advertised": False,
        "gameplay_actions": 0, "manual_ui_inputs": 0,
        "manual_date_advance": False, "bounds": manifest["bounds"],
        "started_at": _now(),
    }
    started = time.monotonic()
    locks = ExitStack()
    driver = None
    handle = None
    try:
        from xar_autoplayer.environment import ck3_process_inventory
        from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
        from xar_autoplayer.native_auto_run import _wait_for_readiness
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch

        _need(not ck3_process_inventory().get("processes"), "old CK3 still alive before launch")
        locks.enter_context(exclusive_launch_lock(spec.game_exe))
        locks.enter_context(exclusive_state_lock(spec.state_dir, "g2m4-life2-paused-read"))
        driver = NativeHeadlessGameplayDriver(
            str(manifest["pipe"]), state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games")
        handle = launch(
            spec,
            native_bridge=NativeBridgeLaunchConfig(
                mode="native-headless", pipe_name=str(manifest["pipe"]),
                dll_path=Path(str(manifest["dll"])),
                injector_path=Path(str(manifest["injector"]))),
            continue_last_save=False, load_save_name="xar_checkpoint",
            verify_prepared_profile=False)
        report["process"] = {
            "pid": handle.process.pid,
            "creation_date": handle.ck3_creation_date,
            "watchdog_pid": handle.watchdog_pid,
            "watchdog_creation_date": handle.watchdog_creation_date,
            "command": handle.command,
            "launched_at": _now(),
        }
        _write(evidence / "round-ownership.json", report["process"])
        binding = _wait_for_readiness(
            driver, session_done=threading.Event(), session_state={},
            timeout_seconds=int(manifest["bounds"]["readiness_seconds"]),
            stable_seconds=1.0, poll_interval_seconds=0.1,
            cold_start_checkpoint=True, allow_terminal=False)
        report["readiness"] = binding
        initial = driver.state.semantic_snapshot()
        played = initial.get("played_character")
        _need(initial.get("paused") is True and initial.get("map_ready") is True
              and isinstance(played, dict) and played.get("alive") is True
              and played.get("character_id") == manifest["expected_actor_id"]
              and initial.get("date_raw") == manifest["expected_date_raw"],
              "frozen R739 paused actor/date differs")
        report["starting_frame"] = {
            "snapshot_id": initial.get("snapshot_id"),
            "native_revision": initial.get("native_revision"),
            "date_raw": initial.get("date_raw"),
            "played_character_id": played.get("character_id"),
            "episode_run_id": manifest["episode_run_id"],
        }
        frozen = {
            "candidate": candidate_root.resolve().name,
            "round_id": round_id,
            "native_source_commit": manifest["native_source_commit"],
            "native_dll_sha256": manifest["dll_sha256"],
            "game_exe_sha256": manifest["game_exe_sha256"],
            "save_sha256": manifest["source_save_sha256"],
            "dlc_mod_load_order": manifest["dlc_mod_load_order"],
            "episode_run_id": manifest["episode_run_id"],
        }
        remaining = float(manifest["bounds"]["overall_seconds"]) - (time.monotonic() - started)
        _need(remaining > 20, "LIFE2 overall window exhausted before native query")
        query_timeout = min(float(manifest["bounds"]["native_query_seconds"]), remaining - 20)
        result = run_owned_paused_life2_current_state_read(
            driver, str(manifest["episode_run_id"]), frozen,
            evidence / "paused-life2-current-state.json",
            timeout_seconds=query_timeout)
        report["read"] = result
        report["status"] = str(result["status"])
    except BaseException as error:
        report.update(status="red", red={
            "at": _now(), "reason": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
        })
    finally:
        if handle is not None:
            try:
                from xar_autoplayer.runtime import stop_tracked
                report["cleanup"] = stop_tracked(handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {"ok": False, "issue": f"{type(error).__name__}: {error}"}
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_red"] = f"{type(error).__name__}: {error}"
        try:
            locks.close()
        except BaseException as error:
            report["lock_close_red"] = f"{type(error).__name__}: {error}"
        try:
            from xar_autoplayer.environment import ck3_process_inventory
            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_save_sha256": _sha(Path(str(manifest["source_save"]))),
                "wall_seconds": time.monotonic() - started,
            }
        except BaseException as error:
            report["postflight_red"] = f"{type(error).__name__}: {error}"
        cleanup = report.get("cleanup")
        post = report.get("postflight")
        reclaimed = (isinstance(cleanup, dict) and cleanup.get("ok") is True
                     and isinstance(post, dict) and not post["ck3_inventory"].get("processes")
                     and post["source_save_sha256"] == manifest["source_save_sha256"]
                     and post["wall_seconds"] <= manifest["bounds"]["overall_seconds"]
                     and not report.get("driver_close_red")
                     and not report.get("lock_close_red"))
        report["ck3_reclaimed"] = reclaimed
        if not reclaimed:
            report["status"] = "red_cleanup" if report["status"] != "red" else "red"
        report["finished_at"] = _now()
        _write(evidence / "report.json", report)
    print(json.dumps({
        "status": report["status"],
        "ck3_reclaimed": report["ck3_reclaimed"],
        "evidence": str(evidence),
    }, ensure_ascii=False, sort_keys=True))
    if report["ck3_reclaimed"] and report["status"] == "state_observed_final_candidates_unavailable":
        return 0
    if report["ck3_reclaimed"] and report["status"] in {
            "typed_absent_progress_evidence_insufficient", "timeout", "ineligible_scene"}:
        return 2
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--round")
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    if args.preflight_only:
        _, _, ready = preflight(args.candidate_root)
        print(json.dumps(ready, ensure_ascii=False, sort_keys=True))
        return 0
    _need(args.round is not None and args.evidence is not None,
          "live mode requires --round and --evidence")
    return run(args.candidate_root, args.round, args.evidence.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
