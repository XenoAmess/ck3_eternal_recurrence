"""Run one paused Council23 private query/status cycle; emit no gameplay action."""

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

from verify_council_r694_query_prep import sha256, verify

QUERY = "private-query-council-composition-candidates-v1"
STATUS = "private-council-application-main-status-v1"
PUBLIC_SCHEMA = "xar.ck3.council-composition-candidates/v1"
ENVELOPE_SCHEMA = "xar.ck3.council-application-main/v1"
EXPECTED_OWNER = 29829
EXPECTED_INCUMBENT = 32716
SCENE_CANDIDATE = 33433
SAVE_SHA = "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def command(driver: object, step: str, request_id: str, revision: int,
            wait_seconds: float) -> dict[str, object]:
    frame = {
        "type": "execute_step", "protocol_version": 1, "request_id": request_id,
        "step": step, "expected_revision": revision,
    }
    driver.endpoint.send(frame)
    result = driver.state.wait_for_command_result(request_id, wait_seconds)
    require(isinstance(result, dict), f"private command timed out: {step}")
    return result


def validate_query(result: dict[str, object], initial: dict[str, object]) -> dict[str, object]:
    require(result.get("type") == "command_result" and result.get("ok") is True,
            f"private status returned RED: {result!r}")
    payload = result.get("result")
    require(isinstance(payload, dict), "private query has no result object")
    require(payload.get("schema") == ENVELOPE_SCHEMA and
            payload.get("step") == "query-council-composition-candidates-v1" and
            payload.get("status") == "available", f"query envelope unavailable: {payload!r}")
    public = payload.get("council_composition_candidates")
    require(isinstance(public, dict) and public.get("schema") == PUBLIC_SCHEMA and
            public.get("status") == "available", "public council query unavailable")
    exact = public.get("exact_build")
    require(isinstance(exact, dict) and exact.get("game_version") == "1.19.0.6" and
            exact.get("executable_sha256") ==
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "private result exact-build identity differs")
    binding = public.get("snapshot")
    require(isinstance(binding, dict) and binding.get("paused") is True and
            binding.get("date_raw") == initial["date_raw"] and
            binding.get("snapshot_id") == f"native:{binding.get('native_revision')}" and
            binding.get("native_revision") == binding.get("public_revision") and
            isinstance(binding.get("native_revision"), int) and
            not isinstance(binding.get("native_revision"), bool),
            f"same-frame binding differs: {binding!r}")
    require(public.get("owner_character_id") == EXPECTED_OWNER,
            "Council owner differs from frozen scene")
    position = public.get("position")
    require(isinstance(position, dict) and position.get("position_key") ==
            "councillor_steward" and position.get("incumbent_character_id") ==
            EXPECTED_INCUMBENT and position.get("vacant") is False and
            position.get("action_route") == "replace", f"incumbent differs: {position!r}")
    readiness = public.get("readiness")
    require(isinstance(readiness, dict) and readiness.get("ready") is True and
            all(value is True for value in readiness.values()),
            f"public query readiness differs: {readiness!r}")
    candidates = public.get("candidates")
    require(public.get("candidate_collection_complete") is True and
            isinstance(candidates, list) and len(candidates) > 0,
            "candidate collection is incomplete or empty")
    ids = [candidate.get("character_id") for candidate in candidates
           if isinstance(candidate, dict)]
    require(len(ids) == len(candidates) and len(ids) == len(set(ids)),
            "candidate IDs are absent or duplicated")
    scene = next((candidate for candidate in candidates
                  if candidate.get("character_id") == SCENE_CANDIDATE), None)
    incumbent_skill = position.get("incumbent_main_skill")
    if scene is not None:
        skill = scene.get("main_skill")
        delta = (skill.get("value") - incumbent_skill.get("value")) if (
            isinstance(skill, dict) and isinstance(incumbent_skill, dict) and
            isinstance(skill.get("value"), int) and
            isinstance(incumbent_skill.get("value"), int)) else None
    else:
        delta = None
    return {
        "owner": EXPECTED_OWNER,
        "incumbent": position,
        "candidate_count": len(candidates),
        "scene_candidate_33433": scene,
        "scene_candidate_skill_delta": delta,
        "snapshot": binding,
        "gate_fields_present": {
            "candidate_eligibility": bool(scene is not None and "eligible" in scene),
            "guest": bool(scene is not None and "guest" in scene),
            "pending_interaction": bool(scene is not None and "pending_interaction" in scene),
            "replacement_fireability": "replacement_fireability" in position,
        },
        "action_gate_live_verified": False,
        "gameplay_actions": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    preflight = verify(root)
    if args.preflight_only:
        print(json.dumps(preflight, sort_keys=True))
        return 0
    operator = json.loads((root / "operator-runtime.json").read_text(encoding="utf-8"))
    source = root / "source-repo"
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"), str(source / "tools")]
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
    from xar_autoplayer.native_auto_run import _wait_for_readiness
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked

    evidence = root / "live-r694"
    require(not evidence.exists(), "R694 already has a live attempt; do not retry same round")
    evidence.mkdir(parents=True)
    report: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_council_r694_query_live_v1",
        "status": "preflight", "started_at": now(), "round": "R694",
        "old_round": "R693", "policy": {
            "private_query_only": True, "gameplay_actions": 0, "ui_inputs": 0,
            "date_advance": False, "manual_save_mutation": False,
            "readiness_timeout_seconds": 300, "query_timeout_seconds": 60,
            "overall_window_seconds": 480,
        }, "preflight": preflight, "red": None,
    }
    handle = None
    driver = None
    started = time.monotonic()
    deadline = started + 480
    state_dir = root / "fresh-profile-state"
    source_save = root / "source-save" / "dev3b_r639.ck3"
    target_save = state_dir / "profile" / "save games" / "dev3b_r639.ck3"
    try:
        spec = make_spec(state_dir, Path(str(operator["game_dir"])))
        inventory = ck3_process_inventory()
        require(not inventory.get("processes"), "CK3 inventory nonzero before R694 launch")
        write_json(evidence / "preflight.json", {**preflight, "ck3_inventory": inventory})
        with ExitStack() as locks:
            locks.enter_context(exclusive_launch_lock(spec.game_exe))
            locks.enter_context(exclusive_state_lock(state_dir, "council-r694-private-query"))
            driver = NativeHeadlessGameplayDriver(
                str(operator["pipe"]), state_dir=state_dir,
                save_dir=state_dir / "profile" / "save games",
            )
            handle = launch(
                spec, native_bridge=NativeBridgeLaunchConfig(
                    mode="native-headless", pipe_name=str(operator["pipe"]),
                    dll_path=root / "candidate-bin" / "xar_ck3_bridge.dll",
                    injector_path=root / "candidate-bin" / "xar_ck3_bridge_injector.exe",
                ), continue_last_save=False, load_save_name="dev3b_r639",
                verify_prepared_profile=False,
            )
            report["process"] = {
                "pid": handle.process.pid,
                "creation_date": handle.ck3_creation_date,
                "watchdog_pid": handle.watchdog_pid,
                "watchdog_creation_date": handle.watchdog_creation_date,
                "command": handle.command, "launched_at": now(),
            }
            write_json(evidence / "round-ownership.json", report["process"])
            remaining = deadline - time.monotonic()
            require(remaining > 30, "overall window consumed before CK3 readiness")
            binding = _wait_for_readiness(
                driver, session_done=threading.Event(), session_state={},
                timeout_seconds=min(300, remaining - 20), stable_seconds=1.0,
                poll_interval_seconds=0.1, cold_start_checkpoint=False,
                allow_terminal=False,
            )
            initial = driver.take_internal_semantic_snapshot()
            require(initial.get("paused") is True and
                    initial.get("episode_character_id") == EXPECTED_OWNER and
                    isinstance(initial.get("date_raw"), int) and
                    isinstance(initial.get("native_revision"), int),
                    f"frozen paused scene differs: {initial!r}")
            advertised = driver.capabilities().get("capabilities")
            require(not isinstance(advertised, list) or
                    all(value not in {
                        "game.query.council-composition-candidates-v1",
                        "game.action.assign-councillor-v1",
                    } for value in advertised),
                    "private Council capability leaked into public hello")
            initial_date = initial["date_raw"]
            revision = initial["native_revision"]
            query_start = time.monotonic()
            query_deadline = min(query_start + 60, deadline - 20)
            require(query_deadline > query_start, "no query window remains")
            first = command(driver, QUERY, "r694-council-query", revision,
                            min(5, query_deadline - time.monotonic()))
            write_json(evidence / "raw-query-request-result.json", first)
            require(first.get("ok") is True and
                    isinstance(first.get("result"), dict) and
                    first["result"].get("status") == "pending",
                    f"private query queue RED: {first!r}")
            terminal = None
            attempts = []
            while time.monotonic() < query_deadline:
                require(handle.process.poll() is None, "CK3 exited before query publication")
                current = driver.take_internal_semantic_snapshot()
                require(current.get("paused") is True and
                        current.get("date_raw") == initial_date,
                        "date/paused invariant changed during read-only query")
                request_id = f"r694-council-status-{len(attempts) + 1}"
                status = command(driver, STATUS, request_id, revision,
                                 min(2, query_deadline - time.monotonic()))
                attempts.append(status)
                write_json(evidence / "raw-status-results.json", attempts)
                payload = status.get("result")
                if status.get("ok") is not True:
                    raise RuntimeError(f"private status RED: {status!r}")
                if isinstance(payload, dict) and payload.get("schema") == ENVELOPE_SCHEMA:
                    terminal = status
                    break
                time.sleep(0.1)
            require(terminal is not None, "Council23 private query did not publish in 60 seconds")
            write_json(evidence / "raw-terminal-result.json", terminal)
            semantic = validate_query(terminal, initial)
            final = driver.take_internal_semantic_snapshot()
            require(final.get("paused") is True and final.get("date_raw") == initial_date,
                    "paused/date invariant changed after query")
            report["capture"] = {
                "binding": binding, "initial_snapshot": initial,
                "result": semantic, "final_snapshot": final,
                "raw_terminal": str(evidence / "raw-terminal-result.json"),
                "query_wall_seconds": time.monotonic() - query_start,
            }
            report["status"] = "green_pending_cleanup"
    except BaseException as error:
        report["status"] = "red_pending_cleanup"
        report["red"] = {
            "at": now(), "reason": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
        }
    finally:
        if handle is not None:
            try:
                report["cleanup"] = stop_tracked(handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {"ok": False, "reason": f"{type(error).__name__}: {error}"}
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_red"] = f"{type(error).__name__}: {error}"
        try:
            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_save_sha256": sha256(source_save),
                "target_save_sha256": sha256(target_save),
                "wall_seconds": time.monotonic() - started,
            }
        except BaseException as error:
            report["postflight_red"] = f"{type(error).__name__}: {error}"
        cleanup = report.get("cleanup")
        post = report.get("postflight")
        ok = (report["status"] == "green_pending_cleanup" and
              isinstance(cleanup, dict) and cleanup.get("ok") is True and
              isinstance(post, dict) and not post["ck3_inventory"].get("processes") and
              post["source_save_sha256"] == SAVE_SHA and
              post["target_save_sha256"] == SAVE_SHA and
              not report.get("driver_close_red") and
              post["wall_seconds"] <= 480)
        report["ok"] = ok
        report["status"] = "green" if ok else "red"
        report["finished_at"] = now()
        write_json(evidence / "report.json", report)
    print(json.dumps({"status": report["status"], "ok": report["ok"],
                      "red": report["red"]}, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
