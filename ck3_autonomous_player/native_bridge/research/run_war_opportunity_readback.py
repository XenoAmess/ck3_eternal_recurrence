#!/usr/bin/env python3
"""Bounded, read-only war opportunity query from one ordinary cold checkpoint.

The owner prepares an independent xar_off profile, then uses a separately
allocated single-instance round for live MCP reads.  This runner never submits
a declaration or advances the date.  An empty pre-query snapshot is not a
negative opportunity result: the native declaration query must actually run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import threading
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from xar_autoplayer.bridge.mcp_server import create_server  # noqa: E402
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver  # noqa: E402
from xar_autoplayer.environment import make_spec, prepare_profile, verify_profile  # noqa: E402
from xar_autoplayer.environment import ck3_process_inventory  # noqa: E402
from xar_autoplayer.native_auto_run import _cleanup_report, _wait_for_readiness  # noqa: E402
from xar_autoplayer.native_session import (  # noqa: E402
    native_session, validate_cold_start_checkpoint_for_pipe,
)
from xar_autoplayer.ordinary_seed_rebinder import rebind_ordinary_seed_v1  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402

import run_war_termination_terms_live_acceptance as common  # noqa: E402

SCHEMA = "xar.ck3.war_opportunity_readback_candidate.v1"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ALLOWED = {
    "query-campaign-root-context-v1",
    "query-declarable-wars",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def copy_frozen_bytes_to_candidate(source: Path, target: Path) -> None:
    """Copy immutable evidence bytes into one writable derived candidate."""

    shutil.copyfile(source, target)
    target.chmod(target.stat().st_mode | stat.S_IWRITE)


def same_frame(before: dict[str, object], after: dict[str, object]) -> bool:
    return (
        before.get("paused") is True and after.get("paused") is True
        and before.get("map_ready") is True and after.get("map_ready") is True
        and all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id"))
        and before.get("played_character") == after.get("played_character")
    )


def targets_from_declarations(rows: object, limit: int) -> tuple[list[int], bool]:
    require(isinstance(rows, list), "native declaration query has no rows array")
    targets: list[int] = []
    for row in rows:
        require(isinstance(row, dict), "native declaration row is malformed")
        target = row.get("target_character_id")
        require(type(target) is int and 0 < target < 2**31,
                "native declaration target identity is malformed")
        if target not in targets:
            targets.append(target)
    return targets[:limit], len(targets) <= limit


async def query_frame(driver: Any, actor_id: int, date_raw: int,
                      limit: int) -> dict[str, object]:
    from mcp import Client

    calls: list[str] = []
    async with Client(create_server(driver)) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}
        required = {"ck3_take_snapshot", "ck3_query_campaign_root_context_v1",
                    "ck3_query_declarable_wars", "ck3_query_war_entry_assessments"}
        require(required <= names, "required official MCP tools are absent")

        async def call(name: str, args: dict[str, object]) -> dict[str, object]:
            result = await client.call_tool(name, args)
            require(not getattr(result, "is_error", False), f"{name} returned MCP error")
            calls.append(name)
            return common._structured(result, tool_name=name)

        capabilities = await call("ck3_get_capabilities", {})
        diagnostics = capabilities.get("diagnostics")
        hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        require(isinstance(hello, dict)
                and hello.get("game_adapter_id") == "ck3-1.19.0.6-msvc-x64"
                and hello.get("game_adapter_status") == "ready"
                and hello.get("ck3_build_match") is True
                and str(hello.get("expected_ck3_sha256", "")).upper() == EXE_SHA256,
                "exact-build native adapter proof failed")
        first = await call("ck3_take_snapshot", {})
        player = first.get("played_character")
        require(first.get("paused") is True and first.get("map_ready") is True
                and isinstance(player, dict)
                and player.get("character_id") == actor_id
                and first.get("date_raw") == date_raw,
                "restored frame differs from the requested actor/date")
        revision = first.get("revision")
        require(type(revision) is int and revision >= 0,
                "restored frame has no public revision")
        root = await call("ck3_query_campaign_root_context_v1",
                          {"expected_revision": revision})
        require(root.get("status") == "available"
                and root.get("player_character_id") == actor_id
                and root.get("queried_snapshot_id") == first.get("snapshot_id")
                and root.get("queried_revision") == revision,
                "campaign root is unavailable or stale")
        declarations = await call("ck3_query_declarable_wars",
                                  {"expected_revision": revision})
        require(type(declarations.get("query_sequence")) is int
                and isinstance(declarations.get("declarable_wars"), list),
                "native declaration query did not complete")
        targets, complete = targets_from_declarations(
            declarations.get("declarable_wars"), limit)
        assessments = []
        for target in targets:
            assessment = await call("ck3_query_war_entry_assessments", {
                "target_character_ids": [target], "expected_revision": revision,
            })
            require(assessment.get("status") == "available"
                    and assessment.get("target_character_ids") == [target]
                    and assessment.get("queried_snapshot_id") == first.get("snapshot_id")
                    and assessment.get("queried_revision") == revision,
                    "war entry assessment is unavailable or stale")
            assessments.append(assessment)
        last = await call("ck3_take_snapshot", {})
        require(same_frame(first, last), "query crossed the paused decision frame")

    history_before = first.get("native_command_history")
    history_after = last.get("native_command_history")
    require(isinstance(history_before, list) and isinstance(history_after, list)
            and history_after[:len(history_before)] == history_before,
            "native command history was not append-only")
    new_commands = [row.get("command") for row in history_after[len(history_before):]
                    if isinstance(row, dict)]
    require(len(new_commands) == len(history_after) - len(history_before)
            and all(step in ALLOWED or (
                isinstance(step, str)
                and step.startswith("query-war-entry-assessments-v1-"))
                for step in new_commands),
            "unexpected native command in read-only window")
    return {
        "ok": True, "status": "green" if complete else "green_partial",
        "scope_complete": complete, "target_limit": limit,
        "mcp_calls": calls, "native_commands": new_commands,
        "first_snapshot": first, "campaign_root": root,
        "declarable_wars_query": declarations,
        "war_entry_assessments": assessments, "last_snapshot": last,
        "gameplay_actions": 0, "date_advanced": False,
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-dir", type=Path, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--live", action="store_true")
    for name in ("source-checkpoint", "source-driver-state", "game-dir",
                 "bridge-dll", "bridge-injector"):
        p.add_argument("--" + name, type=Path)
    for name in ("expected-checkpoint-sha256", "expected-driver-state-sha256"):
        p.add_argument("--" + name)
    p.add_argument("--expected-actor-id", type=int)
    p.add_argument("--expected-date-raw", type=int)
    p.add_argument("--round-ledger", type=Path)
    p.add_argument("--evidence", type=Path)
    p.add_argument("--max-targets", type=int, default=8)
    return p


def prepare(args: argparse.Namespace) -> dict[str, object]:
    candidate = args.candidate_dir.resolve()
    require(not candidate.exists(), "candidate directory already exists")
    required = ("source_checkpoint", "source_driver_state", "game_dir",
                "bridge_dll", "bridge_injector", "expected_checkpoint_sha256",
                "expected_driver_state_sha256", "expected_actor_id",
                "expected_date_raw")
    require(all(getattr(args, key) is not None for key in required),
            "prepare requires frozen source, hashes, actor/date and build paths")
    source_save = args.source_checkpoint.resolve()
    source_driver = args.source_driver_state.resolve()
    save_sha = common._expected_sha256(args.expected_checkpoint_sha256, "source save")
    driver_sha = common._expected_sha256(args.expected_driver_state_sha256, "source driver")
    require(common._sha256_file(source_save) == save_sha
            and common._sha256_file(source_driver) == driver_sha,
            "frozen source pair hash differs")
    anchor = common._driver_anchor(source_driver)
    require(anchor["episode_character_id"] == args.expected_actor_id
            and anchor["last_checkpoint"].get("date_raw") == args.expected_date_raw
            and str(anchor["last_checkpoint"].get("sha256", "")).upper() == save_sha,
            "source driver checkpoint identity differs")
    game = args.game_dir.resolve()
    dll = args.bridge_dll.resolve()
    injector = args.bridge_injector.resolve()
    require(common._sha256_file(game / "binaries" / "ck3.exe") == EXE_SHA256,
            "game binary differs from exact build")
    candidate.mkdir(parents=True)
    spec = make_spec(candidate / "state", game)
    prepared = prepare_profile(spec, xar_enabled="xar_off")
    target_save = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    target_driver = spec.state_dir / "native-session" / "driver-state.json"
    target_save.parent.mkdir(parents=True, exist_ok=True)
    target_driver.parent.mkdir(parents=True, exist_ok=True)
    copy_frozen_bytes_to_candidate(source_save, target_save)
    copy_frozen_bytes_to_candidate(source_driver, target_driver)
    receipt = rebind_ordinary_seed_v1(spec, expected_pipe_name=anchor["pipe_name"])
    verified = verify_profile(spec, xar_enabled="xar_off")
    cold = validate_cold_start_checkpoint_for_pipe(spec, anchor["pipe_name"])
    require(receipt.get("ok") is True and cold is not None
            and common._sha256_file(target_save) == save_sha
            and common._sha256_file(source_save) == save_sha
            and common._sha256_file(source_driver) == driver_sha,
            "official rebind or frozen source invariant failed")
    manifest: dict[str, object] = {
        "schema": SCHEMA, "source_save": str(source_save),
        "source_save_sha256": save_sha, "source_driver": str(source_driver),
        "source_driver_sha256": driver_sha, "state_dir": str(spec.state_dir),
        "game_dir": str(game), "game_exe_sha256": EXE_SHA256,
        "bridge_dll": str(dll), "bridge_dll_sha256": common._sha256_file(dll),
        "bridge_injector": str(injector),
        "bridge_injector_sha256": common._sha256_file(injector),
        "operator_sha256": common._sha256_file(Path(__file__)),
        "prepared_environment_sha256": verified["environment_sha256"],
        "production_tree_sha256": prepared["mod"]["production_tree_sha256"],
        "prepared_save_sha256": common._sha256_file(target_save),
        "prepared_driver_sha256": common._sha256_file(target_driver),
        "pipe_name": anchor["pipe_name"],
        "expected_actor_id": args.expected_actor_id,
        "expected_date_raw": args.expected_date_raw,
        "profile": "ordinary_campaign_succession/xar_off",
        "rebind_receipt": receipt,
    }
    common._write_json_atomic(candidate / "candidate.json", manifest)
    return manifest


def preflight(candidate: Path) -> tuple[dict[str, object], Any, dict[str, object]]:
    manifest = json.loads((candidate / "candidate.json").read_text(encoding="utf-8"))
    require(manifest.get("schema") == SCHEMA
            and manifest.get("profile") == "ordinary_campaign_succession/xar_off"
            and manifest.get("operator_sha256") == common._sha256_file(Path(__file__)),
            "candidate operator/profile differs")
    spec = make_spec(Path(manifest["state_dir"]), Path(manifest["game_dir"]))
    profile = verify_profile(spec, xar_enabled="xar_off")
    require(profile["environment_sha256"] == manifest["prepared_environment_sha256"]
            and profile["mod"]["production_tree_sha256"]
            == manifest["production_tree_sha256"]
            and spec.state_dir.resolve() == (candidate / "state").resolve()
            and common._sha256_file(spec.game_exe) == manifest["game_exe_sha256"]
            and common._sha256_file(Path(manifest["bridge_dll"])) == manifest["bridge_dll_sha256"]
            and common._sha256_file(Path(manifest["bridge_injector"])) == manifest["bridge_injector_sha256"],
            "candidate build/profile hash differs")
    pins = (
        (Path(manifest["source_save"]), manifest["source_save_sha256"]),
        (Path(manifest["source_driver"]), manifest["source_driver_sha256"]),
        (spec.profile_dir / "save games" / "xar_checkpoint.ck3",
         manifest["prepared_save_sha256"]),
        (spec.state_dir / "native-session" / "driver-state.json",
         manifest["prepared_driver_sha256"]),
    )
    require(all(common._sha256_file(path) == sha for path, sha in pins),
            "candidate source/prepared pair differs")
    cold = validate_cold_start_checkpoint_for_pipe(spec, manifest["pipe_name"])
    require(cold is not None, "cold checkpoint validation failed")
    inventory = ck3_process_inventory()
    readiness = {
        "status": "ready_no_launch" if not inventory["processes"] else "wait_single_instance",
        "ck3_process_inventory": inventory, "cold_checkpoint": cold,
        "candidate_manifest_sha256": common._sha256_file(candidate / "candidate.json"),
    }
    return manifest, spec, readiness


def live(args: argparse.Namespace, manifest: dict[str, object], spec: Any) -> dict[str, object]:
    require(args.round_ledger is not None and args.evidence is not None,
            "live requires allocated owner/round ledger and fresh evidence path")
    ledger = json.loads(args.round_ledger.read_text(encoding="utf-8-sig"))
    require(ledger.get("schema") == "xar.ck3.single-instance-round-allocation/v1"
            and isinstance(ledger.get("owner"), str) and ledger["owner"]
            and isinstance(ledger.get("round"), str)
            and ledger["round"].startswith("R"),
            "persistent single-instance allocation is absent")
    evidence = args.evidence.resolve()
    require(not evidence.exists(), "live evidence directory already exists")
    evidence.mkdir(parents=True)
    stop = threading.Event()
    done = threading.Event()
    session: dict[str, object] = {"report": None, "error": None}
    driver = None
    thread = None
    report: dict[str, object] = {
        "schema": "xar.ck3.war_opportunity_readback_live.v1",
        "round": ledger["round"], "status": "red", "ok": False,
        "candidate_manifest_sha256": common._sha256_file(args.candidate_dir / "candidate.json"),
        "gameplay_actions": 0, "date_advanced": False,
    }
    try:
        pipe = manifest["pipe_name"]
        persisted = common._persisted_succession_lifecycle(
            spec.state_dir / "native-session" / "driver-state.json")
        driver = NativeHeadlessGameplayDriver(
            pipe, state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            succession_lifecycle_binding=persisted)
        config = NativeBridgeLaunchConfig(
            mode="native-headless", pipe_name=pipe,
            dll_path=Path(manifest["bridge_dll"]),
            injector_path=Path(manifest["bridge_injector"]))

        def supervise() -> None:
            try:
                session["report"] = native_session(
                    spec, timeout_seconds=900, native_bridge=config,
                    cold_start_checkpoint=True, stop_event=stop,
                    prepared_xar_enabled="xar_off")
            except BaseException as error:
                session["error"] = f"{type(error).__name__}: {error}"
            finally:
                done.set()

        thread = threading.Thread(target=supervise, name="war-opportunity-readback")
        thread.start()
        _wait_for_readiness(driver, session_done=done, session_state=session,
                            timeout_seconds=300, stable_seconds=0.5,
                            poll_interval_seconds=0.05,
                            cold_start_checkpoint=True, allow_terminal=False)
        report["query"] = asyncio.run(query_frame(
            driver, manifest["expected_actor_id"], manifest["expected_date_raw"],
            args.max_targets))
        report["status"] = report["query"]["status"]
        report["ok"] = True
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        stop.set()
        if thread is not None:
            thread.join()
        closed = False
        if driver is not None:
            try:
                driver.close()
                closed = True
            except BaseException as error:
                report["close_error"] = f"{type(error).__name__}: {error}"
        cleanup = _cleanup_report(session["report"], session_error=session["error"],
                                  driver_closed=closed,
                                  elapsed_seconds=0.0)
        report["cleanup"] = cleanup
        if not cleanup.get("ok"):
            report["ok"] = False
            report["status"] = "red"
        common._write_json_atomic(evidence / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    require(1 <= args.max_targets <= 32, "target bound must be 1..32")
    candidate = args.candidate_dir.resolve()
    require(candidate.drive.upper() != "C:", "candidate must be on non-C storage")
    temp = (candidate.parent / (candidate.name + "-tmp")
            if args.prepare_only else candidate / "tmp")
    temp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = str(temp)
    os.environ["TMP"] = str(temp)
    if args.prepare_only:
        result = prepare(args)
    else:
        manifest, spec, readiness = preflight(candidate)
        result = {"status": readiness["status"], "preflight": readiness,
                  "manifest": manifest}
        if args.live:
            require(readiness["status"] == "ready_no_launch",
                    "CK3 instance exists; live readback must wait")
            result = live(args, manifest, spec)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
