#!/usr/bin/env python3
"""Bounded private M5 alliance readback; only the CK3 owner may run live."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path()
LEGALITY_STEP = "query-observed-first-heir-marriage-legality-v1"
LEGALITY_SCHEMA = "xar.ck3.observed-first-heir-marriage-legality.v1"
PROJECTION_STEP = "query-first-heir-candidate-alliance-projection-v1-private"
PROJECTION_SCHEMA = "xar.ck3.first-heir-candidate-alliance-projection.v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def same_frame(first: dict[str, object], last: dict[str, object]) -> None:
    a, b = first.get("played_character"), last.get("played_character")
    require(
        first.get("paused") is True and last.get("paused") is True
        and first.get("map_ready") is True and last.get("map_ready") is True
        and all(first.get(key) == last.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id"))
        and isinstance(a, dict) and isinstance(b, dict)
        and a.get("character_id") == b.get("character_id")
        and a.get("alive") is True and b.get("alive") is True,
        "new query crossed the initial paused player/date/revision frame",
    )


def project_api(manifest: dict[str, object]) -> dict[str, object]:
    source = Path(manifest["source_repo"])
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"),
                    str(source / "tools")]
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.environment import (
        ck3_process_inventory, make_spec, verify_profile)
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
    from xar_autoplayer.native_auto_run import _wait_for_readiness
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked
    return locals()


def preflight(manifest: dict[str, object], api: dict[str, object]) -> tuple[object, dict[str, object]]:
    source = Path(manifest["source_repo"])
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    require(commit == manifest["source_commit"],
            "frozen source commit changed")
    require(not subprocess.check_output(
        ["git", "-C", str(source), "status", "--porcelain"], text=True).strip(),
        "frozen integrated source is dirty")
    spec = api["make_spec"](Path(manifest["state_dir"]),
                            Path(manifest["game"]["exe"]).parent.parent)
    profile = api["verify_profile"](spec,
                                     xar_enabled=manifest["profile_xar_enabled"])
    expected_profile = manifest["prepared_profile"]
    require(profile["environment_sha256"].upper() ==
            expected_profile["environment_sha256"],
            "prepared environment fingerprint changed")
    require(profile["agent_runtime"]["sha256"].upper() ==
            expected_profile["agent_runtime_sha256"],
            "integrated Python runtime fingerprint changed")
    require(profile["mod"]["git_revision"] == commit and
            profile["mod"]["production_tree_sha256"].upper() ==
            expected_profile["production_tree_sha256"],
            "production mod revision/tree changed")
    require(profile["load_profile"]["enabled_mods"] ==
            manifest["game"]["enabled_mods_in_order"] and
            profile["load_profile"]["disabled_dlcs"] == [],
            "single-mod/no-DLC load order changed")
    pins = {
        "game_exe_sha256": spec.game_exe,
        "source_save_sha256": Path(manifest["ordinary_feudal_fixture"][
            "source_save"]),
        "prepared_save_sha256": spec.profile_dir / "save games" /
            (manifest["save_name"] + ".ck3"),
        "bridge_dll_sha256": Path(manifest["native_build"]["bridge_dll"]),
        "injector_sha256": Path(manifest["native_build"]["injector"]),
        "cmake_cache_sha256": Path(manifest["native_build"]["cmake_cache"]),
    }
    expected = {
        "game_exe_sha256": manifest["game"]["exe_sha256"],
        "source_save_sha256": manifest["ordinary_feudal_fixture"][
            "source_save_sha256"],
        "prepared_save_sha256": expected_profile["prepared_save_sha256"],
        "bridge_dll_sha256": manifest["native_build"]["bridge_dll_sha256"],
        "injector_sha256": manifest["native_build"]["injector_sha256"],
        "cmake_cache_sha256": manifest["native_build"]["cmake_cache_sha256"],
    }
    for key, path in pins.items():
        require(path.is_file() and sha256(path) == expected[key],
                key + " absent or changed")
    cache = pins["cmake_cache_sha256"].read_text(
        encoding="utf-8", errors="replace")
    require("XAR_CK3_ENABLE_G2_M5_RANKED_MARRIAGE_PRIVATE_QUERY_V1:BOOL=ON"
            in cache and
            "XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1:BOOL=ON"
            in cache, "candidate DLL build lacks both private read-only switches")
    require(not (Path(manifest["state_dir"]) / "native-session" /
                  "driver-state.json").exists(),
            "fresh read-only seed acquired a driver before launch")
    inventory = api["ck3_process_inventory"]()
    return spec, {
        "status": "READY_NO_LAUNCH" if not inventory.get("processes")
                  else "WAIT_SINGLE_INSTANCE",
        "source_commit": commit,
        "profile_environment_sha256": profile["environment_sha256"],
        "agent_runtime_sha256": profile["agent_runtime"]["sha256"],
        "ck3_inventory": inventory,
        "ck3_launched": False,
        "pins": {key: str(path) for key, path in pins.items()},
    }


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--round-ledger", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    ROOT = args.candidate_dir.resolve()
    require(ROOT.is_dir() and ROOT.drive.upper() != "C:",
            "candidate must be an existing non-C directory")
    task_temp = ROOT / "tmp"
    task_temp.mkdir(exist_ok=True)
    os.environ["TEMP"] = str(task_temp)
    os.environ["TMP"] = str(task_temp)
    manifest_path = ROOT / "no-launch-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(sha256(Path(__file__)) == manifest["operator_sha256"],
            "frozen alliance-readback operator changed")
    require(manifest["schema"] ==
            "xar.ck3.m5_alliance_readback_live_prep_v1",
            "candidate manifest schema changed")
    require(manifest["legality_step"] == LEGALITY_STEP and
            manifest["legality_schema"] == LEGALITY_SCHEMA and
            manifest["projection_step"] == PROJECTION_STEP and
            manifest["projection_schema"] == PROJECTION_SCHEMA and
            manifest["public_capability_advertised"] is False and
            manifest["mcp_tool_registered"] is False,
            "private query contract/advertising changed")
    api = project_api(manifest)
    spec, pre = preflight(manifest, api)
    if args.preflight_only:
        print(json.dumps(pre, ensure_ascii=False, sort_keys=True))
        return 0
    require(pre["status"] == "READY_NO_LAUNCH",
            "single CK3 instance is not free for the owner")
    require(args.round_ledger is not None and args.evidence is not None,
            "live requires a unique owner round ledger and evidence directory")
    ledger = json.loads(args.round_ledger.read_text(encoding="utf-8-sig"))
    require(ledger.get("schema") ==
            "xar.ck3.single-instance-round-allocation/v1" and
            isinstance(ledger.get("owner"), str) and ledger["owner"] and
            str(ledger.get("round", "")).startswith("R"),
            "single-instance owner/round allocation absent")
    evidence = args.evidence.resolve()
    require(not evidence.exists(), "attempt evidence path already exists")
    evidence.mkdir(parents=True)
    report: dict[str, object] = {
        "schema": "xar.ck3.m5_alliance_projection_readback_live_v1",
        "status": "RED", "round": ledger["round"],
        "source_commit": manifest["source_commit"],
        "candidate_manifest_sha256": sha256(manifest_path),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "bounds_seconds": {"overall": 900, "readiness": 300,
                           "query": 360},
        "gameplay_actions": 0, "ui_inputs": 0, "date_advance": False,
        "preflight": pre,
    }
    driver = handle = None
    locks = ExitStack()
    started = time.monotonic()
    try:
        locks.enter_context(api["exclusive_launch_lock"](spec.game_exe))
        locks.enter_context(api["exclusive_state_lock"](
            Path(manifest["state_dir"]), "m5-alliance-readback-read-only"))
        pipe = "\\\\.\\pipe\\xar_ck3_m5_alliance_" + str(ledger["round"])
        driver = api["NativeHeadlessGameplayDriver"](
            pipe, state_dir=Path(manifest["state_dir"]),
            save_dir=spec.profile_dir / "save games")
        handle = api["launch"](
            spec, native_bridge=api["NativeBridgeLaunchConfig"](
                mode="native-headless", pipe_name=pipe,
                dll_path=Path(manifest["native_build"]["bridge_dll"]),
                injector_path=Path(manifest["native_build"]["injector"])),
            continue_last_save=False, load_save_name=manifest["save_name"],
            verify_prepared_profile=False)
        report["process"] = {"pid": handle.process.pid,
                             "creation_date": handle.ck3_creation_date,
                             "command": handle.command}
        api["_wait_for_readiness"](
            driver, session_done=threading.Event(), session_state={},
            timeout_seconds=300, stable_seconds=1.0,
            poll_interval_seconds=0.1, cold_start_checkpoint=False,
            allow_terminal=False, require_post_ready_pump=True)
        first = driver.take_snapshot()
        played = first.get("played_character")
        require(first.get("paused") is True and first.get("map_ready") is True
                and first.get("date_raw") == manifest["fixture"]["date_raw"]
                and isinstance(played, dict)
                and played.get("character_id") ==
                    manifest["fixture"]["played_character_id"]
                and played.get("alive") is True,
                "ordinary feudal source did not restore to paused player/date")
        caps = driver.capabilities()
        steps = caps.get("action_steps")
        require(isinstance(steps, list) and
                "query-campaign-root-context-v1" in steps and
                LEGALITY_STEP not in steps and PROJECTION_STEP not in steps,
                "public root absent or private query was advertised")
        native_revision = first.get("native_revision")
        require(type(native_revision) is int and native_revision > 0,
                "paused native revision unavailable")
        legality = driver.query_observed_first_heir_marriage_legality_v1(
            expected_native_revision=native_revision,
            timeout_seconds=360)
        write_json(evidence / "observed-first-heir-legality.json", legality)
        same_frame(first, driver.take_snapshot())
        require(legality["schema"] == LEGALITY_SCHEMA and
                legality["exact_ck3_build"] == "1.19.0.6" and
                legality["read_only"] is True and
                legality["advertised"] is False and
                legality["status"] == "available" and
                legality["native_revision"] == native_revision and
                legality["observed_first_heir_character_id"] ==
                    manifest["fixture"]["first_heir_character_id"] and
                legality["root_query_sequence"] > 0 and
                legality["query_sequence"] > 0,
                "private final-legality query did not bind")
        rows = legality["candidates"]
        legal = legality["native_legal_candidates"]
        ids = [row["candidate_character_id"] for row in legal]
        require(len(legal) == manifest["fixture"]["expected_final_legal_count"]
                and len(ids) == len(set(ids)) and len(ids) >= 5 and
                all(row["complete_can_send"] is True and
                    row["native_rank"] is None and
                    row["recipient_answer_status_raw"] in (0, 1) and
                    row["recipient_answer_allows_send"] is True
                    for row in legal) and
                all(row["native_rank"] is None and
                    row["recipient_answer_allows_send"] is
                    (row["recipient_answer_status_raw"] in (0, 1))
                    for row in rows),
                "native family final legality/rank differs from frozen fixture")
        selected_ids = ids[:5]  # Deterministic read-only sample; not a ranking.
        projection = driver.query_first_heir_candidate_alliance_projection_private_v1(
            legality=legality, candidate_character_ids=selected_ids,
            timeout_seconds=360)
        write_json(evidence / "five-candidate-alliance-projection.json", projection)
        same_frame(first, driver.take_snapshot())
        require(projection["schema"] == PROJECTION_SCHEMA and
                projection["exact_ck3_build"] == "1.19.0.6" and
                projection["read_only"] is True and
                projection["advertised"] is False and
                projection["native_revision"] == native_revision and
                projection["legality_query_sequence"] ==
                    legality["query_sequence"] and
                projection["status"] == "available" and
                [row["candidate_character_id"] for row in projection["rows"]]
                    == selected_ids and
                all(row["status"] == "available" for row in projection["rows"]),
                "five-candidate alliance projection unavailable or disagrees")
        report["initial_frame"] = {
            "snapshot_id": first.get("snapshot_id"),
            "revision": first.get("revision"),
            "native_revision": native_revision,
            "date_raw": first["date_raw"],
            "player_character_id": played["character_id"],
            "episode_run_id": first.get("episode_run_id"),
        }
        report["observations"] = {
            "all_can_send_rows": len(rows),
            "distinct_final_legal_rows": len(legal),
            "projected_candidate_ids": selected_ids,
            "projection_status": projection["status"],
            "projected_row_count": len(projection["rows"]),
            "native_rank_available": False,
            "private_query_advertised": False,
        }
        report["status"] = "GREEN_READ_ONLY_PENDING_CLEANUP"
    except BaseException as error:
        report["error"] = {"reason": type(error).__name__ + ": " + str(error),
                           "traceback": traceback.format_exc()}
        report["status"] = "RED_PENDING_CLEANUP"
    finally:
        if handle is not None:
            try:
                report["cleanup"] = api["stop_tracked"](
                    handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {"ok": False,
                                     "reason": type(error).__name__ + ": " +
                                     str(error)}
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_error"] = str(error)
        locks.close()
        report["postflight"] = {
            "source_save_sha256": sha256(Path(manifest[
                "ordinary_feudal_fixture"]["source_save"])),
            "prepared_save_sha256": sha256(spec.profile_dir / "save games" /
                                            (manifest["save_name"] + ".ck3")),
            "ck3_inventory": api["ck3_process_inventory"](),
            "wall_seconds": round(time.monotonic() - started, 3),
        }
        cleanup = report.get("cleanup")
        post = report["postflight"]
        report["ok"] = bool(
            report["status"] == "GREEN_READ_ONLY_PENDING_CLEANUP"
            and isinstance(cleanup, dict) and cleanup.get("ok") is True
            and cleanup.get("cleanup_proven") is True
            and not post["ck3_inventory"].get("processes")
            and post["source_save_sha256"] ==
                manifest["ordinary_feudal_fixture"]["source_save_sha256"]
            and post["prepared_save_sha256"] ==
                manifest["prepared_profile"]["prepared_save_sha256"]
            and post["wall_seconds"] <= 900
            and not report.get("driver_close_error"))
        report["status"] = "GREEN_READ_ONLY" if report["ok"] else "RED"
        write_json(evidence / "report.json", report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
