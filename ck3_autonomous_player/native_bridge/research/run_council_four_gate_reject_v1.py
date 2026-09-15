"""One bounded private typed Council gate rejection from a frozen real scene.

Only the sole CK3 owner may use the live route after exclusive machine release.
The preflight route does not launch CK3 or touch the screen.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

from council_four_gate_reject_v1 import (
    PositiveSceneMissing, read_plan, select, sha256, validate_rejection_ack,
    verify_candidate,
)
from run_council_r696_controlled_replace import (
    ASSIGN, QUERY, HeldLaunchLocks, bounded_operation, envelope,
    public_from_gate, require, write_json,
)


def verify_live_gate(result: dict[str, object], terminal: Path,
                     plan: dict[str, object], initial: dict[str, object]) -> tuple[
                         dict[str, object], dict[str, object]]:
    fresh = select(terminal, sha256(terminal), str(plan["gate"]))
    for key in ("candidate_character_id", "owner_character_id",
                "incumbent_character_id", "vacant", "candidate_count"):
        require(fresh[key] == plan[key],
                f"real paused {key} differs from checkpoint-bound positive scene")
    require(fresh["snapshot"]["date_raw"] == plan["snapshot"]["date_raw"] ==
            initial.get("date_raw") and initial.get("paused") is True and
            initial.get("episode_character_id") == plan["owner_character_id"],
            "live native scene is not the frozen paused campaign/checkpoint")
    public = public_from_gate(result)
    require(public.get("owner_character_id") == plan["owner_character_id"] and
            public.get("snapshot") == fresh["snapshot"] and
            isinstance(public.get("position"), dict) and
            public["position"].get("position_key") == "councillor_steward",
            "public projection does not match exact native gate transaction")
    return fresh, public


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--new-round", help="monotonic round allocated by sole CK3 owner")
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    try:
        candidate, plan = verify_candidate(root)
    except (OSError, ValueError, PositiveSceneMissing, json.JSONDecodeError) as error:
        print(json.dumps({"status": "evidence_insufficient", "ck3_launched": False,
                          "reason": str(error)}, sort_keys=True))
        return 2
    if args.preflight_only:
        print(json.dumps({"status": "green_no_launch", "ck3_launched": False,
                          "gate": plan["gate"],
                          "source_save_sha256": candidate["source_save_sha256"],
                          "driver_state_sha256": candidate["driver_state_sha256"],
                          "bridge_dll_sha256": candidate["bridge_dll_sha256"],
                          "planned_full_character_id": plan["candidate_character_id"],
                          "public_registered_or_advertised": False}, sort_keys=True))
        return 0
    round_id = args.new_round
    require(isinstance(round_id, str) and round_id.startswith("R") and
            round_id[1:].isdigit(), "sole owner must allocate a new CK3 round")
    evidence = root / f"live-{round_id.lower()}"
    require(not evidence.exists(), "round already has evidence; do not retry")
    evidence.mkdir(parents=True)
    source = root / "source-repo"
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"),
                    str(source / "tools")]
    from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
        build_assign_councillor_request_v1, normalize_assign_councillor_ack_v1,
    )
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
    from xar_autoplayer.native_auto_run import _wait_for_readiness
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked

    state = root / "fresh-profile-state"
    save_name = str(candidate["save_name"])
    source_save = root / "source-save" / (save_name + ".ck3")
    target_save = state / "profile" / "save games" / (save_name + ".ck3")
    deadline = time.monotonic() + 480
    report: dict[str, object] = {
        "schema": "xar.ck3.private.council-four-gate-reject-live/1.19.0.6-v1",
        "status": "preflight", "round": round_id, "gate": plan["gate"],
        "positive_scene": plan, "native_helper_invocations_expected": 0,
        "public_registered_or_advertised": False,
        "formal_next_turn_consumption": "unverified_private_gate_only",
        "red": None,
    }
    locks = HeldLaunchLocks()
    driver = None
    handle = None
    started = time.monotonic()
    try:
        inventory = ck3_process_inventory()
        require(not inventory.get("processes"),
                "CK3 inventory nonzero; do not claim sole ownership")
        spec = make_spec(state, Path(str(candidate["game_dir"])))
        with locks:
            locks.enter_context(exclusive_launch_lock(spec.game_exe))
            locks.enter_context(exclusive_state_lock(
                state, f"council-four-{round_id.lower()}-reject"))
            driver = NativeHeadlessGameplayDriver(
                str(candidate["pipe"]), state_dir=state,
                save_dir=state / "profile" / "save games")
            handle = launch(
                spec, native_bridge=NativeBridgeLaunchConfig(
                    mode="native-headless", pipe_name=str(candidate["pipe"]),
                    dll_path=root / "candidate-bin" / "xar_ck3_bridge.dll",
                    injector_path=root / "candidate-bin" / "xar_ck3_bridge_injector.exe"),
                continue_last_save=False, load_save_name=save_name,
                verify_prepared_profile=False)
            report["process"] = {
                "pid": handle.process.pid, "creation_date": handle.ck3_creation_date,
                "watchdog_pid": handle.watchdog_pid,
                "watchdog_creation_date": handle.watchdog_creation_date,
                "command": handle.command,
            }
            write_json(evidence / "round-ownership.json", report["process"])
            _wait_for_readiness(
                driver, session_done=threading.Event(), session_state={},
                timeout_seconds=min(300, deadline - time.monotonic() - 20),
                stable_seconds=1.0, poll_interval_seconds=0.1,
                cold_start_checkpoint=False, allow_terminal=False)
            initial = driver.take_internal_semantic_snapshot()
            advertised = driver.capabilities().get("capabilities")
            require(not isinstance(advertised, list) or all(value not in {
                "game.query.council-composition-candidates-v1",
                "game.action.assign-councillor-v1",
            } for value in advertised), "Council public capability leaked")
            revision = initial.get("native_revision")
            require(type(revision) is int and initial.get("paused") is True,
                    "new process did not load an exact paused native frame")
            first = bounded_operation(
                driver, handle, evidence, "first-gate", QUERY,
                f"{round_id.lower()}-first-gate", revision, deadline,
                initial["date_raw"])
            terminal = evidence / "first-gate-raw-terminal-result.json"
            live_plan, public = verify_live_gate(first, terminal, plan, initial)
            candidate_id = int(live_plan["candidate_character_id"])
            request_id = f"{round_id.lower()}-{plan['gate']}-reject-{candidate_id}"
            request = build_assign_councillor_request_v1(
                public, candidate_character_id=candidate_id,
                request_id=request_id)
            write_json(evidence / "typed-rejection-request.json", request.as_wire_fields())
            result = bounded_operation(
                driver, handle, evidence, "typed-rejection", ASSIGN,
                request_id, revision, deadline, initial["date_raw"],
                candidate_character_id=candidate_id)
            payload = envelope(result, "assign-councillor-v1")
            raw_ack = payload.get("council_assign_councillor_ack")
            write_json(evidence / "raw-rejection-ack.json", raw_ack)
            ack = normalize_assign_councillor_ack_v1(
                raw_ack, expected_request=request)
            validate_rejection_ack(ack, plan)
            # Submit preparation clears the query; independent later paused query.
            later = driver.take_internal_semantic_snapshot()
            require(later.get("paused") is True and
                    later.get("date_raw") == initial["date_raw"] and
                    type(later.get("native_revision")) is int,
                    "paused native state changed after rejected request")
            second = bounded_operation(
                driver, handle, evidence, "later-gate", QUERY,
                f"{round_id.lower()}-later-gate", later["native_revision"],
                deadline, initial["date_raw"])
            later_terminal = evidence / "later-gate-raw-terminal-result.json"
            later_plan, later_public = verify_live_gate(
                second, later_terminal, plan, later)
            require(later_public["position"]["incumbent_character_id"] ==
                    plan["incumbent_character_id"] and
                    later_plan["candidate_character_id"] == candidate_id,
                    "independent later paused query changed incumbent or rejected ID")
            report["capture"] = {
                "initial": initial, "typed_rejection": ack,
                "later_paused": later,
                "later_incumbent": later_public["position"]["incumbent_character_id"],
                "native_helper_invocations_delta": 0,
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
            report["lock_cleanup_red"] = str(error)
        try:
            post = ck3_process_inventory()
            report["postflight"] = {
                "ck3_inventory": post,
                "source_save_sha256": sha256(source_save),
                "target_save_sha256": sha256(target_save),
                "wall_seconds": time.monotonic() - started,
            }
        except BaseException as error:
            report["postflight_red"] = str(error)
        postflight = report.get("postflight")
        cleanup = report.get("cleanup")
        report["ok"] = (
            report["status"] == "green_pending_cleanup" and
            isinstance(cleanup, dict) and cleanup.get("ok") is True and
            isinstance(postflight, dict) and
            not postflight["ck3_inventory"].get("processes") and
            postflight["source_save_sha256"] ==
            postflight["target_save_sha256"] ==
            candidate["source_save_sha256"] and
            postflight["wall_seconds"] <= 480 and
            not report.get("driver_close_red") and
            not report.get("lock_cleanup_red"))
        report["status"] = "green" if report["ok"] else "red"
        write_json(evidence / "report.json", report)
    print(json.dumps({"status": report["status"], "ok": report["ok"],
                      "red": report["red"]}, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
