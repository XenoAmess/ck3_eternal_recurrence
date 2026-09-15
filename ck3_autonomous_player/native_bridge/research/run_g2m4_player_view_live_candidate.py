"""One owned CK3 round: bounded paused G2-M4 private player-view read.

Only the current single-instance operator runs this script with a new
monotonic ``--round``. It loads the sealed ordinary production feudal pair,
reads campaign-root then private cache on one paused frame, captures a
read-only desktop image for county-window review, and reclaims CK3. A cache
branch alone does not advertise or complete construction.
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


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def private_read_exit_code(status: str, reclaimed: bool, read_kind: str) -> int:
    required = ("model_sources_observed" if read_kind == "player-model-sources"
                else "cache_branch_observed")
    if reclaimed and status == required:
        return 0
    if reclaimed and status in {"closed_view_evidence_insufficient", "open_view_scene",
                               "model_sources_evidence_insufficient"}:
        return 2
    return 1


def preflight(root: Path) -> tuple[object, dict[str, object], dict[str, object]]:
    manifest_path = root / "candidate-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("schema") == "xar.ck3.g2_m4_player_view_private_live_candidate_v1"
            and manifest.get("status") == "READY_NO_LAUNCH" and manifest.get("advertised") is False,
            "private candidate manifest is absent or not sealed")
    require(manifest.get("read_kind", "cache-view") in {"cache-view", "player-model-sources"},
            "private candidate read kind is unsupported")
    require(Path(str(manifest.get("candidate_root"))).resolve() == root,
            "candidate belongs to a different artifact root")
    source = Path(str(manifest["source_repo"]))
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"), str(source / "tools"),
                    str(source / "ck3_autonomous_player" / "native_bridge" / "research")]
    from xar_autoplayer.environment import ck3_process_inventory, make_spec, verify_profile
    from xar_autoplayer.native_session import validate_cold_start_checkpoint_for_pipe
    from xar_autoplayer.bridge.native_driver import load_native_driver_state_for_resume
    game = Path(str(manifest["game_dir"]))
    state = Path(str(manifest["state_dir"]))
    spec = make_spec(state, game)
    require(sha(spec.game_exe) == manifest["game_exe_sha256"], "CK3 exact EXE SHA differs")
    for key, hash_key in (("dll", "dll_sha256"), ("injector", "injector_sha256"),
                          ("source_save", "source_save_sha256"),
                          ("paired_driver_state", "paired_driver_state_sha256")):
        require(sha(Path(str(manifest[key]))) == manifest[hash_key], f"sealed {key} SHA differs")
    require(sha(root / "build-release-cache.txt") == manifest["cmake_cache_sha256"],
            "private feature build cache SHA differs")
    cache = (root / "build-release-cache.txt").read_text(encoding="utf-8", errors="replace")
    require("XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1:BOOL=ON" in cache,
            "private player-view feature is not ON in sealed DLL")
    profile = verify_profile(spec)
    require(profile.get("environment_sha256") == manifest["profile_environment_sha256"],
            "prepared production profile changed")
    require(sha(Path(str(manifest["prepared_save"]))) == manifest["source_save_sha256"]
            and sha(Path(str(manifest["prepared_driver_state"]))) == manifest["paired_driver_state_sha256"],
            "prepared R697 source pair changed")
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, str(manifest["pipe"]))
    driver_state = load_native_driver_state_for_resume(
        Path(str(manifest["prepared_driver_state"])), str(manifest["pipe"]))
    require(checkpoint.get("saved_date_raw") == manifest["date_raw"]
            and isinstance(driver_state, dict)
            and driver_state.get("episode_character_id") == manifest["episode_character_id"]
            and driver_state.get("episode_run_id") == manifest["episode_run_id"],
            "paired checkpoint/driver restore identity differs")
    inventory = ck3_process_inventory()
    require(not inventory.get("processes"), "CK3 inventory nonzero before new round")
    return spec, manifest, {
        "status": "READY_NO_LAUNCH", "ck3_inventory": inventory,
        "profile_environment_sha256": profile.get("environment_sha256"),
        "checkpoint": checkpoint,
    }


def screenshot(root: Path, frame: dict[str, object], bridge_pid: object) -> dict[str, object]:
    result: dict[str, object] = {
        "snapshot_id": frame.get("snapshot_id"),
        "native_revision": frame.get("native_revision"),
        "date_raw": frame.get("date_raw"),
        "bridge_pid": bridge_pid,
        "window_county_view_visible": "unreviewed",
    }
    try:
        from PIL import ImageGrab
        path = root / "paused-desktop-before-private-read.png"
        ImageGrab.grab(all_screens=True).save(path)
        result.update(path=str(path), sha256=sha(path), capture_status="captured")
    except Exception as error:
        result.update(capture_status="unavailable", capture_issue=f"{type(error).__name__}: {error}")
    return result


def run(root: Path, round_id: str, evidence: Path) -> int:
    spec, manifest, pre = preflight(root)
    require(round_id.startswith("R") and round_id[1:].isdigit() and int(round_id[1:]) > 0,
            "operator must supply a real monotonic CK3 round R{n}")
    require(not evidence.exists(), "one owned round has one evidence directory")
    evidence.mkdir(parents=True)
    report: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_player_view_private_live_v1",
        "status": "unexecuted", "round_id": round_id,
        "candidate_root": str(root), "source_commit": manifest["source_commit"],
        "ck3_exact_exe_sha256": manifest["game_exe_sha256"],
        "dll_sha256": manifest["dll_sha256"],
        "source_save_sha256": manifest["source_save_sha256"],
        "paired_driver_state_sha256": manifest["paired_driver_state_sha256"],
        "entry": "owned NativeHeadlessGameplayDriver+read-only execute_step",
        "manual_ui_inputs": 0, "gameplay_actions": 0,
        "manual_date_advance": False, "public_construction_advertised": False,
        "bounds": manifest["bounds"], "preflight": pre,
        "started_at": now(), "red": None,
    }
    handle = None
    driver = None
    locks = ExitStack()
    started = time.monotonic()
    try:
        source = Path(str(manifest["source_repo"]))
        sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"),
                        str(source / "ck3_autonomous_player" / "native_bridge" / "research")]
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.environment import ck3_process_inventory
        from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
        from xar_autoplayer.native_auto_run import _wait_for_readiness
        from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked
        from run_g2m4_paused_player_view_read import run_owned_paused_player_view_read
        from run_g2m4_paused_player_model_source_read import run_owned_paused_player_model_source_read
        from PIL import ImageGrab  # noqa: F401; needed only for an optional same-frame receipt
        require(not ck3_process_inventory().get("processes"), "old CK3 instance still alive")
        locks.enter_context(exclusive_launch_lock(spec.game_exe))
        locks.enter_context(exclusive_state_lock(spec.state_dir, "g2m4-player-view-private-read"))
        driver = NativeHeadlessGameplayDriver(
            str(manifest["pipe"]), state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        handle = launch(
            spec, native_bridge=NativeBridgeLaunchConfig(
                mode="native-headless", pipe_name=str(manifest["pipe"]),
                dll_path=Path(str(manifest["dll"])),
                injector_path=Path(str(manifest["injector"])),
            ), continue_last_save=False, load_save_name="xar_checkpoint",
            verify_prepared_profile=False,
        )
        report["process"] = {
            "pid": handle.process.pid,
            "creation_date": handle.ck3_creation_date,
            "watchdog_pid": handle.watchdog_pid,
            "watchdog_creation_date": handle.watchdog_creation_date,
            "command": handle.command, "launched_at": now(),
        }
        write(evidence / "round-ownership.json", report["process"])
        binding = _wait_for_readiness(
            driver, session_done=threading.Event(), session_state={},
            timeout_seconds=300, stable_seconds=1.0,
            poll_interval_seconds=0.1, cold_start_checkpoint=True,
            allow_terminal=False,
        )
        initial = driver.state.semantic_snapshot()
        played = initial.get("played_character")
        require(initial.get("paused") is True and initial.get("map_ready") is True
                and initial.get("date_raw") == manifest["date_raw"]
                and isinstance(played, dict)
                and played.get("character_id") == manifest["episode_character_id"],
                "frozen paused source identity differs before private read")
        report["readiness"] = binding
        report["starting_frame"] = {
            "snapshot_id": initial.get("snapshot_id"),
            "native_revision": initial.get("native_revision"),
            "date_raw": initial.get("date_raw"),
            "played_character_id": played.get("character_id"),
        }
        bridge_pid = initial.get("diagnostics", {}).get("bridge_pid") if isinstance(initial.get("diagnostics"), dict) else None
        report["desktop_diagnostic"] = screenshot(evidence, initial, bridge_pid)
        frozen = {
            "candidate_id": root.name, "round_id": round_id,
            "seed": "r697-standard-feudal-peace-paired",
            "source_save_path": str(manifest["source_save"]),
            "source_save_sha256": manifest["source_save_sha256"],
            "ck3_exe_path": str(spec.game_exe),
            "ck3_exe_sha256": manifest["game_exe_sha256"],
            "native_dll_path": manifest["dll"],
            "native_dll_sha256": manifest["dll_sha256"],
            "agent_commit": manifest["source_commit"],
            "dlc_mod_load_order": [manifest["dlc_mod_load_order"]],
            "configuration": manifest["configuration"] if isinstance(manifest["configuration"], dict) else {},
        }
        if manifest.get("read_kind", "cache-view") == "player-model-sources":
            read = run_owned_paused_player_model_source_read(
                driver, frozen, evidence / "paused-player-model-source-read.json",
                timeout_seconds=12.0,
            )
        else:
            read = run_owned_paused_player_view_read(
                driver, frozen, evidence / "paused-player-view-read.json",
                timeout_seconds=12.0,
            )
        report["read"] = read
        report["cache_branch"] = read.get("cache_branch")
        report["player_model_sources"] = read.get("player_model_sources")
        report["next_read"] = read.get("next_read")
        report["status"] = read.get("status", "red")
    except BaseException as error:
        report.update(status="red", red={
            "at": now(), "reason": f"{type(error).__name__}: {error}",
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
            report["lock_cleanup_red"] = f"{type(error).__name__}: {error}"
        try:
            from xar_autoplayer.environment import ck3_process_inventory
            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_seed_sha256": sha(Path(str(manifest["source_save"]))),
                "wall_seconds": time.monotonic() - started,
            }
        except BaseException as error:
            report["postflight_red"] = f"{type(error).__name__}: {error}"
        cleanup = report.get("cleanup")
        post = report.get("postflight")
        reclaimed = (isinstance(cleanup, dict) and cleanup.get("ok") is True
                     and isinstance(post, dict) and not post["ck3_inventory"].get("processes")
                     and post["source_seed_sha256"] == manifest["source_save_sha256"]
                     and post["wall_seconds"] <= 480 and not report.get("driver_close_red")
                     and not report.get("lock_cleanup_red"))
        report["ck3_reclaimed"] = reclaimed
        if not reclaimed:
            report["status"] = "red_cleanup" if report["status"] != "red" else "red"
        report["finished_at"] = now()
        write(evidence / "report.json", report)
    print(json.dumps({"status": report["status"], "cache_branch": report.get("cache_branch"),
                      "ck3_reclaimed": report["ck3_reclaimed"], "evidence": str(evidence)}, ensure_ascii=False))
    return private_read_exit_code(
        report["status"], report["ck3_reclaimed"],
        manifest.get("read_kind", "cache-view"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--round", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    root = args.candidate_root.resolve()
    if args.preflight_only:
        _, _, result = preflight(root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    return run(root, args.round, args.evidence.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
