#!/usr/bin/env python3
"""Prepare or run one bounded slot49 minor-religious-war defender readback.

The default-OFF native route is read-only.  Prepare and preflight never launch
CK3.  Live mode requires an explicit persistent single-instance round ledger,
performs one private query, advances no date and submits no gameplay action.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_query_minor_religious_war_defenders_private_v1,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    ck3_process_inventory,
    make_spec,
    prepare_profile,
    verify_profile,
)
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import (  # noqa: E402
    native_session,
    validate_cold_start_checkpoint_for_pipe,
)
from xar_autoplayer.ordinary_seed_rebinder import (  # noqa: E402
    rebind_ordinary_seed_v1,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402

import run_war_termination_terms_live_acceptance as common  # noqa: E402


SCHEMA = "xar.ck3.minor_religious_war_defenders_candidate.v1"
LIVE_SCHEMA = "xar.ck3.minor_religious_war_defenders_live.v1"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
TARGET_KEY = "minor_religious_war"
SLOT49_OPTION = "XAR_CK3_ENABLE_G2_MINOR_RELIGIOUS_WAR_DEFENDERS_PRIVATE_V1=ON"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def same_frame(before: dict[str, object], after: dict[str, object]) -> bool:
    keys = (
        "snapshot_id", "revision", "native_revision", "date_raw",
        "episode_run_id", "episode_character_id", "paused", "map_ready",
    )
    return (
        before.get("paused") is True
        and after.get("paused") is True
        and before.get("map_ready") is True
        and after.get("map_ready") is True
        and all(before.get(key) == after.get(key) for key in keys)
        and before.get("played_character") == after.get("played_character")
        and before.get("active_wars") == after.get("active_wars")
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--candidate-dir", type=Path, required=True)
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--live", action="store_true")
    for name in (
        "source-checkpoint", "source-driver-state", "game-dir",
        "bridge-dll", "bridge-injector",
    ):
        result.add_argument("--" + name, type=Path)
    for name in (
        "expected-checkpoint-sha256", "expected-driver-state-sha256",
    ):
        result.add_argument("--" + name)
    result.add_argument("--expected-actor-id", type=int)
    result.add_argument("--expected-date-raw", type=int)
    result.add_argument("--target-character-id", type=int, default=31_549)
    result.add_argument("--round-ledger", type=Path)
    result.add_argument("--evidence", type=Path)
    return result


def prepare(args: argparse.Namespace) -> dict[str, object]:
    candidate = args.candidate_dir.resolve()
    require(not candidate.exists(), "candidate directory already exists")
    required = (
        "source_checkpoint", "source_driver_state", "game_dir",
        "bridge_dll", "bridge_injector", "expected_checkpoint_sha256",
        "expected_driver_state_sha256", "expected_actor_id",
        "expected_date_raw",
    )
    require(
        all(getattr(args, name) is not None for name in required),
        "prepare requires frozen pair, hashes, actor/date and exact build paths",
    )
    require(args.target_character_id == 31_549,
            "this bounded candidate is frozen to target 31549")
    source_save = args.source_checkpoint.resolve()
    source_driver = args.source_driver_state.resolve()
    save_sha = common._expected_sha256(
        args.expected_checkpoint_sha256, "source save"
    )
    driver_sha = common._expected_sha256(
        args.expected_driver_state_sha256, "source driver"
    )
    require(
        common._sha256_file(source_save) == save_sha
        and common._sha256_file(source_driver) == driver_sha,
        "frozen R0142 source pair hash differs",
    )
    anchor = common._driver_anchor(source_driver)
    require(
        anchor["episode_character_id"] == args.expected_actor_id
        and anchor["last_checkpoint"].get("date_raw") == args.expected_date_raw
        and str(anchor["last_checkpoint"].get("sha256", "")).upper()
        == save_sha,
        "source driver checkpoint identity differs",
    )
    game = args.game_dir.resolve()
    dll = args.bridge_dll.resolve()
    injector = args.bridge_injector.resolve()
    require(
        common._sha256_file(game / "binaries" / "ck3.exe") == EXE_SHA256,
        "game binary differs from exact build",
    )
    candidate.mkdir(parents=True)
    spec = make_spec(candidate / "state", game)
    prepared = prepare_profile(spec, xar_enabled="xar_off")
    target_save = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    target_driver = spec.state_dir / "native-session" / "driver-state.json"
    target_save.parent.mkdir(parents=True, exist_ok=True)
    target_driver.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_save, target_save)
    shutil.copy2(source_driver, target_driver)
    receipt = rebind_ordinary_seed_v1(
        spec, expected_pipe_name=anchor["pipe_name"]
    )
    verified = verify_profile(spec, xar_enabled="xar_off")
    cold = validate_cold_start_checkpoint_for_pipe(spec, anchor["pipe_name"])
    require(
        receipt.get("ok") is True
        and cold is not None
        and common._sha256_file(target_save) == save_sha
        and common._sha256_file(source_save) == save_sha
        and common._sha256_file(source_driver) == driver_sha,
        "official rebind or frozen-source invariant failed",
    )
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "source_round": "R0142",
        "source_save": str(source_save),
        "source_save_sha256": save_sha,
        "source_driver": str(source_driver),
        "source_driver_sha256": driver_sha,
        "state_dir": str(spec.state_dir),
        "game_dir": str(game),
        "game_exe_sha256": EXE_SHA256,
        "bridge_dll": str(dll),
        "bridge_dll_sha256": common._sha256_file(dll),
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
        "target_character_id": args.target_character_id,
        "target_casus_belli_key": TARGET_KEY,
        "profile": "ordinary_campaign_succession/xar_off",
        "required_native_build_option": SLOT49_OPTION,
        "rebind_receipt": receipt,
    }
    common._write_json_atomic(candidate / "candidate.json", manifest)
    return manifest


def preflight(candidate: Path) -> tuple[dict[str, object], Any, dict[str, object]]:
    manifest_path = candidate / "candidate.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(
        manifest.get("schema") == SCHEMA
        and manifest.get("source_round") == "R0142"
        and manifest.get("profile") == "ordinary_campaign_succession/xar_off"
        and manifest.get("target_character_id") == 31_549
        and manifest.get("target_casus_belli_key") == TARGET_KEY
        and manifest.get("required_native_build_option") == SLOT49_OPTION
        and manifest.get("operator_sha256")
        == common._sha256_file(Path(__file__)),
        "candidate identity/operator/profile differs",
    )
    spec = make_spec(Path(manifest["state_dir"]), Path(manifest["game_dir"]))
    profile = verify_profile(spec, xar_enabled="xar_off")
    require(
        profile["environment_sha256"]
        == manifest["prepared_environment_sha256"]
        and profile["mod"]["production_tree_sha256"]
        == manifest["production_tree_sha256"]
        and spec.state_dir.resolve() == (candidate / "state").resolve()
        and common._sha256_file(spec.game_exe) == EXE_SHA256
        and common._sha256_file(Path(manifest["bridge_dll"]))
        == manifest["bridge_dll_sha256"]
        and common._sha256_file(Path(manifest["bridge_injector"]))
        == manifest["bridge_injector_sha256"],
        "candidate build/profile hash differs",
    )
    pins = (
        (Path(manifest["source_save"]), manifest["source_save_sha256"]),
        (Path(manifest["source_driver"]), manifest["source_driver_sha256"]),
        (spec.profile_dir / "save games" / "xar_checkpoint.ck3",
         manifest["prepared_save_sha256"]),
        (spec.state_dir / "native-session" / "driver-state.json",
         manifest["prepared_driver_sha256"]),
    )
    require(
        all(common._sha256_file(path) == sha for path, sha in pins),
        "candidate source/prepared pair differs",
    )
    cold = validate_cold_start_checkpoint_for_pipe(
        spec, manifest["pipe_name"]
    )
    require(cold is not None, "cold checkpoint validation failed")
    inventory = ck3_process_inventory()
    readiness = {
        "status": (
            "ready_no_launch" if not inventory["processes"]
            else "wait_single_instance"
        ),
        "ck3_process_inventory": inventory,
        "cold_checkpoint": cold,
        "candidate_manifest_sha256": common._sha256_file(manifest_path),
    }
    return manifest, spec, readiness


def query_one(service: GameplayBridgeService, manifest: dict[str, object]) -> dict[str, object]:
    before = service.snapshot()
    player = before.get("played_character")
    require(
        before.get("paused") is True
        and before.get("map_ready") is True
        and isinstance(player, dict)
        and player.get("character_id") == manifest["expected_actor_id"]
        and before.get("date_raw") == manifest["expected_date_raw"],
        "restored frame differs from frozen R0142 actor/date",
    )
    revision = before.get("revision")
    require(type(revision) is int and revision >= 0,
            "restored frame has no public revision")
    history_before = before.get("native_command_history")
    require(isinstance(history_before, list), "native history is unavailable")
    readback = _ck3_query_minor_religious_war_defenders_private_v1(
        service, int(manifest["target_character_id"]), revision
    )
    payload = readback.get("minor_religious_war_defenders")
    require(
        readback.get("advertised") is False
        and readback.get("read_only") is True
        and isinstance(payload, dict)
        and payload.get("status") == "available"
        and payload.get("actor_character_id") == manifest["expected_actor_id"]
        and isinstance(payload.get("declaration"), dict)
        and payload["declaration"].get("target_character_id")
        == manifest["target_character_id"]
        and payload["declaration"].get("casus_belli_key") == TARGET_KEY,
        "slot49 result does not bind the frozen declaration",
    )
    after = service.snapshot()
    require(same_frame(before, after), "slot49 query crossed its paused frame")
    require(
        after.get("native_command_history") == history_before,
        "slot49 query changed native gameplay history",
    )
    return {
        "ok": True,
        "status": "green_read_only",
        "before": before,
        "readback": readback,
        "after": after,
        "gameplay_actions": 0,
        "date_advanced": False,
    }


def live(
    args: argparse.Namespace, manifest: dict[str, object], spec: Any
) -> dict[str, object]:
    require(
        args.round_ledger is not None and args.evidence is not None,
        "live requires allocated round ledger and fresh evidence path",
    )
    ledger = json.loads(args.round_ledger.read_text(encoding="utf-8-sig"))
    require(
        ledger.get("schema") == "xar.ck3.single-instance-round-allocation/v1"
        and isinstance(ledger.get("owner"), str) and ledger["owner"]
        and isinstance(ledger.get("round"), str)
        and ledger["round"].startswith("R")
        and ledger["round"][1:].isdigit(),
        "persistent single-instance allocation is absent",
    )
    evidence = args.evidence.resolve()
    require(evidence.drive.upper() != "C:",
            "live evidence must use real non-C storage")
    require(not evidence.exists(), "live evidence directory already exists")
    evidence.mkdir(parents=True)
    stop = threading.Event()
    done = threading.Event()
    session: dict[str, object] = {"report": None, "error": None}
    driver = None
    thread = None
    report: dict[str, object] = {
        "schema": LIVE_SCHEMA,
        "round": ledger["round"],
        "status": "red",
        "ok": False,
        "candidate_manifest_sha256": common._sha256_file(
            args.candidate_dir / "candidate.json"
        ),
        "gameplay_actions": 0,
        "date_advanced": False,
    }
    started = time.monotonic()
    try:
        pipe = manifest["pipe_name"]
        persisted = common._persisted_succession_lifecycle(
            spec.state_dir / "native-session" / "driver-state.json"
        )
        driver = NativeHeadlessGameplayDriver(
            pipe,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            succession_lifecycle_binding=persisted,
            allow_private_minor_religious_war_defenders_query=True,
        )
        service = GameplayBridgeService(driver)
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=pipe,
            dll_path=Path(manifest["bridge_dll"]),
            injector_path=Path(manifest["bridge_injector"]),
        )

        def supervise() -> None:
            try:
                session["report"] = native_session(
                    spec,
                    timeout_seconds=900,
                    native_bridge=config,
                    cold_start_checkpoint=True,
                    stop_event=stop,
                    prepared_xar_enabled="xar_off",
                )
            except BaseException as error:
                session["error"] = f"{type(error).__name__}: {error}"
            finally:
                done.set()

        thread = threading.Thread(
            target=supervise, name="minor-religious-war-defenders-readback"
        )
        thread.start()
        _wait_for_readiness(
            driver,
            session_done=done,
            session_state=session,
            timeout_seconds=300,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=True,
            allow_terminal=False,
        )
        report["query"] = query_one(service, manifest)
        report["status"] = "green_read_only"
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
        cleanup = _cleanup_report(
            session["report"],
            session_error=session["error"],
            driver_closed=closed,
            elapsed_seconds=time.monotonic() - started,
        )
        report["cleanup"] = cleanup
        if not cleanup.get("ok"):
            report["ok"] = False
            report["status"] = "red"
        common._write_json_atomic(evidence / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    candidate = args.candidate_dir.resolve()
    require(candidate.drive.upper() != "C:",
            "candidate must use real non-C storage")
    temp = (
        candidate.parent / (candidate.name + "-tmp")
        if args.prepare_only
        else candidate / "tmp"
    )
    temp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = str(temp)
    os.environ["TMP"] = str(temp)
    if args.prepare_only:
        result = prepare(args)
    else:
        manifest, spec, readiness = preflight(candidate)
        result = {
            "status": readiness["status"],
            "preflight": readiness,
            "manifest": manifest,
        }
        if args.live:
            require(
                readiness["status"] == "ready_no_launch",
                "CK3 instance exists; live readback must wait",
            )
            result = live(args, manifest, spec)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
