"""Read one ordinary-feudal Council final-gate scene through the private native route.

The sole CK3 operator allocates --new-round. --preflight-only never starts CK3.
This captures native provider rows; it neither submits an assignment nor advertises
the Council query/action capability.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

from inspect_council_final_gate_scene import inspect, sha256

SCHEMA = "xar.ck3.private.council-native-gate-scene-candidate/1.19.0.6-v1"
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
QUERY = "private-query-council-final-gates-v1"
STATUS = "private-council-application-main-status-v1"
ENVELOPE = "xar.ck3.council-application-main/v1"
PRIVATE_FLAGS = {
    "XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1": "ON",
    "XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1": "ON",
    "XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1": "OFF",
}
PUBLIC_CAPABILITIES = {
    "game.query.council-composition-candidates-v1",
    "game.action.assign-councillor-v1",
}


class HeldLaunchLocks(ExitStack):
    def __exit__(self, *arguments: object) -> bool:
        return False

    def close(self) -> None:
        ExitStack.__exit__(self, None, None, None)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def verify_candidate(root: Path) -> dict[str, object]:
    root = root.resolve()
    manifest = json.loads((root / "candidate-manifest.json").read_text(encoding="utf-8"))
    require(isinstance(manifest, dict) and manifest.get("schema") == SCHEMA
            and manifest.get("status") == "sealed-no-launch"
            and manifest.get("source_round") == "R739"
            and manifest.get("public_registered_or_advertised") is False
            and manifest.get("gameplay_actions") == 0,
            "Council scene candidate is not a sealed private read-only R739 copy")
    frame = manifest.get("expected_frame")
    require(isinstance(frame, dict) and frame.get("government_key") == "feudal_government"
            and type(frame.get("played_character_id")) is int
            and type(frame.get("date_raw")) is int
            and type(frame.get("steward_incumbent_character_id")) is int
            and frame["played_character_id"] > 0
            and frame["steward_incumbent_character_id"] > 0,
            "ordinary-feudal paused anchor fields are absent")
    rows = manifest.get("frozen_files")
    require(isinstance(rows, list) and rows, "frozen file list is absent")
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("path"), str)
                and isinstance(row.get("sha256"), str),
                "frozen file row is untyped")
        path = (root / row["path"]).resolve()
        require(path.is_relative_to(root) and path.is_file()
                and sha256(path) == row["sha256"].upper(),
                f"frozen candidate file differs: {row['path']}")
    source = root / "source-save" / "xar_checkpoint.ck3"
    target = root / "state" / "profile" / "save games" / "xar_checkpoint.ck3"
    driver_path = root / "state" / "native-session" / "driver-state.json"
    save_sha = manifest.get("source_save_sha256")
    require(source.open("rb").read(7) == b"SAV0101"
            and sha256(source) == sha256(target) == save_sha
            and sha256(driver_path) == manifest.get("source_driver_sha256"),
            "R739 source/target SAV0101 and driver are not a frozen pair")
    driver = json.loads(driver_path.read_text(encoding="utf-8"))
    checkpoint = driver.get("last_checkpoint")
    require(driver.get("format_version") == 2 and isinstance(checkpoint, dict)
            and checkpoint.get("sha256", "").upper() == save_sha
            and checkpoint.get("date_raw") == frame["date_raw"]
            and checkpoint.get("episode_character_id") == frame["played_character_id"],
            "driver checkpoint does not belong to the R739 paused frame")
    cache = (root / "candidate-bin" / "CMakeCache.txt").read_text(
        encoding="utf-8", errors="replace")
    require(manifest.get("private_build_flags") == PRIVATE_FLAGS
            and all(f"{flag}:BOOL={value}" in cache
                    for flag, value in PRIVATE_FLAGS.items()),
            "native private query/action build options differ")
    dlc = json.loads((root / "state" / "profile" / "dlc_load.json").read_text(
        encoding="utf-8-sig"))
    require(dlc == {"enabled_mods": ["mod/xar_autoplayer.mod"],
                    "disabled_dlcs": []}, "frozen ordinary-feudal mod/DLC list differs")
    descriptor = (root / "state" / "profile" / "mod" / "xar_autoplayer.mod").read_text(
        encoding="utf-8-sig")
    mod_root = (root / "state" / "profile" / "mod-content" / "xar-production").as_posix()
    require(f'path="{mod_root}"' in descriptor and
            (root / "state" / "profile" / "mod-content" / "xar-production").is_dir(),
            "candidate mod descriptor does not resolve to its own production tree")
    environment = json.loads((root / "state" / "profile" /
                              "xar-autoplayer-environment.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(root / "source-repo" / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.environment import _contract_digest

    require(environment.get("state_dir") == str((root / "state").resolve())
            and environment.get("profile_dir") ==
            str((root / "state" / "profile").resolve())
            and environment.get("environment_sha256") ==
            manifest.get("profile_environment_sha256") == _contract_digest(environment),
            "relocated profile environment still refers to the old R739 workspace")
    game = Path(str(manifest.get("game_dir", ""))).resolve()
    python = Path(str(manifest.get("operator_python", ""))).resolve()
    require(manifest.get("game_exe_sha256") == EXE_SHA
            and sha256(game / "binaries" / "ck3.exe") == EXE_SHA
            and sha256(python) == manifest.get("operator_python_sha256"),
            "operator CK3/Python exact binary differs")
    require((root / "source-repo" / "ck3_autonomous_player" / "src"
             / "xar_autoplayer" / "bridge" / "native_driver.py").is_file(),
            "frozen Python production driver is absent")
    pipe = manifest.get("pipe")
    require(isinstance(pipe, str) and pipe.startswith(r"\\.\pipe\xar_ck3_"),
            "candidate has no unique native pipe")
    return {"status": "ready-no-launch", "ck3_launched": False,
            "source_round": "R739", "source_save_sha256": save_sha,
            "source_driver_sha256": manifest["source_driver_sha256"],
            "native_source_commit": manifest["native_source_commit"],
            "dll_sha256": manifest["dll_sha256"],
            "game_exe_sha256": EXE_SHA, "public_advertised": False,
            "bounded_seconds": manifest["bounded_seconds"]}


def send(driver: object, step: str, request_id: str, revision: int,
         wait_seconds: float) -> dict[str, object]:
    driver.endpoint.send({"type": "execute_step", "protocol_version": 1,
                          "request_id": request_id, "step": step,
                          "expected_revision": revision})
    result = driver.state.wait_for_command_result(request_id, wait_seconds)
    require(isinstance(result, dict), f"private Council {step} timed out")
    return result


def validate_terminal(path: Path, manifest: dict[str, object],
                      initial: dict[str, object]) -> dict[str, object]:
    scene = inspect(path, sha256(path))
    frame = manifest["expected_frame"]
    require(scene["owner_character_id"] == frame["played_character_id"]
            and scene["incumbent_character_id"] ==
            frame["steward_incumbent_character_id"]
            and scene["snapshot"]["date_raw"] == frame["date_raw"]
            and initial.get("date_raw") == frame["date_raw"]
            and initial.get("episode_character_id") == frame["played_character_id"]
            and scene["snapshot"]["native_revision"] ==
            initial.get("native_revision")
            and scene["native_helper_invocations_delta"] == 0
            and scene["public_registered_or_advertised"] is False,
            "real native Council row differs from frozen ordinary-feudal paused frame")
    return scene


def run(root: Path, round_id: str, evidence: Path,
        preflight: dict[str, object], manifest: dict[str, object]) -> int:
    evidence = evidence.resolve()
    require(evidence.is_relative_to(root.resolve()) and not evidence.exists(),
            "new round evidence must be a fresh candidate-owned directory")
    evidence.mkdir(parents=True)
    source_repo = root / "source-repo"
    sys.path[:0] = [str(source_repo / "ck3_autonomous_player" / "src"),
                    str(source_repo / "tools")]
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
    from xar_autoplayer.native_auto_run import _wait_for_readiness
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked

    report: dict[str, object] = {
        "schema": "xar.ck3.private.council-native-gate-scene-live/1.19.0.6-v1",
        "status": "preflight", "round": round_id, "started_at": now(),
        "source_round": "R739", "private_query_only": True,
        "gameplay_actions": 0, "public_registered_or_advertised": False,
        "controlled_rejection_gate_acceptance": "unverified_query_only",
        "bounded_seconds": manifest["bounded_seconds"],
        "preflight": preflight, "red": None,
    }
    source = root / "source-save" / "xar_checkpoint.ck3"
    target = root / "state" / "profile" / "save games" / "xar_checkpoint.ck3"
    locks = HeldLaunchLocks()
    driver = None
    handle = None
    started = time.monotonic()
    deadline = started + 480
    try:
        game = Path(str(manifest["game_dir"]))
        spec = make_spec(root / "state", game)
        inventory = ck3_process_inventory()
        require(not inventory.get("processes"), "CK3 inventory nonzero before sole-owner launch")
        write_json(evidence / "preflight.json", {**preflight,
                                                 "ck3_inventory": inventory})
        with locks:
            locks.enter_context(exclusive_launch_lock(spec.game_exe))
            locks.enter_context(exclusive_state_lock(root / "state",
                                                     f"council-{round_id.lower()}-scene"))
            driver = NativeHeadlessGameplayDriver(
                str(manifest["pipe"]), state_dir=root / "state",
                save_dir=root / "state" / "profile" / "save games")
            handle = launch(spec, native_bridge=NativeBridgeLaunchConfig(
                mode="native-headless", pipe_name=str(manifest["pipe"]),
                dll_path=root / "candidate-bin" / "xar_ck3_bridge.dll",
                injector_path=root / "candidate-bin" / "xar_ck3_bridge_injector.exe"),
                continue_last_save=False, load_save_name="xar_checkpoint",
                verify_prepared_profile=False)
            report["process"] = {"pid": handle.process.pid,
                                 "creation_date": handle.ck3_creation_date,
                                 "watchdog_pid": handle.watchdog_pid,
                                 "watchdog_creation_date": handle.watchdog_creation_date,
                                 "command": handle.command, "launched_at": now()}
            write_json(evidence / "round-ownership.json", report["process"])
            _wait_for_readiness(driver, session_done=threading.Event(),
                                session_state={},
                                timeout_seconds=min(300, deadline-time.monotonic()-20),
                                stable_seconds=1.0, poll_interval_seconds=0.1,
                                cold_start_checkpoint=False, allow_terminal=False)
            initial = driver.take_internal_semantic_snapshot()
            frame = manifest["expected_frame"]
            require(initial.get("paused") is True
                    and initial.get("episode_character_id") == frame["played_character_id"]
                    and initial.get("date_raw") == frame["date_raw"]
                    and type(initial.get("native_revision")) is int,
                    "new process did not cold-load the frozen paused R739 scene")
            advertised = driver.capabilities().get("capabilities")
            require(not isinstance(advertised, list)
                    or not PUBLIC_CAPABILITIES.intersection(advertised),
                    "private Council query/action leaked into public hello")
            revision = initial["native_revision"]
            query_deadline = min(time.monotonic()+60, deadline-20)
            first = send(driver, QUERY, f"{round_id.lower()}-gate-query", revision,
                         min(5, query_deadline-time.monotonic()))
            write_json(evidence / "raw-query-queue-result.json", first)
            require(first.get("ok") is True and
                    isinstance(first.get("result"), dict) and
                    first["result"].get("status") == "pending",
                    "native Council private query was not queued")
            attempts: list[dict[str, object]] = []
            terminal = None
            while time.monotonic() < query_deadline:
                require(handle.process.poll() is None, "CK3 exited before Council query publication")
                current = driver.take_internal_semantic_snapshot()
                require(current.get("paused") is True and
                        current.get("date_raw") == frame["date_raw"],
                        "paused/date changed during read-only Council query")
                status = send(driver, STATUS,
                              f"{round_id.lower()}-gate-status-{len(attempts)+1}",
                              revision, min(2, max(0.1, query_deadline-time.monotonic())))
                attempts.append(status)
                write_json(evidence / "raw-status-results.json", attempts)
                require(status.get("ok") is True,
                        f"native Council private status RED: {status!r}")
                if (isinstance(status.get("result"), dict) and
                        status["result"].get("schema") == ENVELOPE):
                    terminal = status
                    break
                time.sleep(0.1)
            require(terminal is not None, "Council native gate query did not publish in 60s")
            terminal_path = evidence / "raw-terminal-result.json"
            write_json(terminal_path, terminal)
            scene = validate_terminal(terminal_path, manifest, initial)
            final = driver.take_internal_semantic_snapshot()
            require(final.get("paused") is True and
                    final.get("date_raw") == frame["date_raw"] and
                    final.get("native_revision") == initial.get("native_revision"),
                    "paused/date/revision changed after private native Council query")
            report["capture"] = {"initial": initial, "final": final,
                                 "native_scene": scene,
                                 "raw_terminal_sha256": sha256(terminal_path)}
            report["isolated_positive_counts"] = {
                gate: len(scene[field]) for gate, field in {
                    "guest": "isolated_guest_rejection_ids",
                    "candidate_pending": "isolated_candidate_pending_rejection_ids",
                    "replacement_fireability_denial":
                        "isolated_replacement_fireability_denial_ids",
                }.items()
            }
            report["status"] = "green_pending_cleanup"
    except BaseException as error:
        report["status"] = "red_pending_cleanup"
        report["red"] = {"reason": f"{type(error).__name__}: {error}",
                         "traceback": traceback.format_exc(),
                         "blind_retry_allowed": False}
    finally:
        if handle is not None:
            try:
                report["cleanup"] = stop_tracked(handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {"ok": False, "reason": str(error)}
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_red"] = str(error)
        try:
            locks.close()
        except BaseException as error:
            report["lock_close_red"] = str(error)
        try:
            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_save_sha256": sha256(source),
                "target_save_sha256": sha256(target),
                "wall_seconds": time.monotonic()-started,
            }
        except BaseException as error:
            report["postflight_red"] = str(error)
        post = report.get("postflight")
        cleanup = report.get("cleanup")
        report["ok"] = (report["status"] == "green_pending_cleanup"
                        and isinstance(cleanup, dict) and cleanup.get("ok") is True
                        and isinstance(post, dict)
                        and not post["ck3_inventory"].get("processes")
                        and post["source_save_sha256"] ==
                        post["target_save_sha256"] == manifest["source_save_sha256"]
                        and post["wall_seconds"] <= 480
                        and not report.get("driver_close_red")
                        and not report.get("lock_close_red")
                        and not report.get("postflight_red"))
        report["status"] = "green" if report["ok"] else "red"
        report["finished_at"] = now()
        write_json(evidence / "report.json", report)
    print(json.dumps({"status": report["status"], "ok": report["ok"],
                      "red": report["red"]}, ensure_ascii=False))
    return 0 if report["ok"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--new-round", help="monotonic round allocated by sole CK3 owner")
    parser.add_argument("--evidence", type=Path, help="new per-round candidate-owned directory")
    args = parser.parse_args()
    root = args.candidate_root.resolve()
    try:
        preflight = verify_candidate(root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "red-no-launch", "ck3_launched": False,
                          "reason": str(error)}, ensure_ascii=False))
        return 2
    if args.preflight_only:
        print(json.dumps(preflight, sort_keys=True))
        return 0
    require(isinstance(args.new_round, str) and args.new_round.startswith("R")
            and args.new_round[1:].isdigit() and args.evidence is not None,
            "sole CK3 owner must allocate a new monotonic round and evidence path")
    manifest = json.loads((root / "candidate-manifest.json").read_text(encoding="utf-8"))
    return run(root, args.new_round, args.evidence, preflight, manifest)


if __name__ == "__main__":
    raise SystemExit(main())
