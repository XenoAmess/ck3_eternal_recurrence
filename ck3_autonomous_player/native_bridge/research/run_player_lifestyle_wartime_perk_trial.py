"""One private wartime stewardship perk on a fresh ordinary paired checkpoint.

This is a separate bounded action candidate.  It never resumes the war
planner, changes a war order, advances the date, or advertises public LIFE.
The resulting save and driver state are paired by the official save step.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import traceback
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Callable

from run_player_lifestyle_three_query_readback import (
    _frame, _need, _non_c_task_path, _now, _sha, _valid_start, _write,
    parser, preflight, prepare_candidate,
)


SCHEMA = "xar.ck3.g2_m4_wartime_perk_action_candidate_v1"
REPORT_SCHEMA = "xar.ck3.g2_m4_wartime_perk_action_live_v1"
ROOT_STEP = "query-campaign-root-context-v1"
TARGET = "cutting_corners_perk"


def choose_one_wartime_perk(
    driver: Any,
    manifest: dict[str, object],
    *,
    wait_for_post: Callable[[dict[str, object]], object],
    save_paired_checkpoint: Callable[[], dict[str, object]],
    plan_current_turn: Callable[[], dict[str, object]],
    plan_following_turn: Callable[[], dict[str, object]],
) -> dict[str, object]:
    """Reuse the private formal action/receipt, then consume and checkpoint it."""

    from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
        STATE_QUERY_STEP, query_player_lifestyle_private_v1,
    )
    from xar_autoplayer.lifestyle_formal_consumer import (
        same_frame_feudal_lifestyle_scope,
    )
    from xar_autoplayer.lifestyle_min_policy import (
        WAR_PERK_POLICY_ID, choose_min_feudal_lifestyle_action,
    )

    starting_snapshot = driver.take_snapshot()
    starting = _frame(starting_snapshot)
    record: dict[str, object] = {
        "status": "ineligible_scene", "starting_frame": starting,
        "gameplay_actions": 0, "date_advanced": False,
    }
    if not _valid_start(starting, manifest):
        return record
    if (
        not isinstance(starting_snapshot.get("active_wars"), list)
        or not starting_snapshot["active_wars"]
        or starting_snapshot.get("active_event") is not None
        or starting_snapshot.get("pending_character_interaction") is not None
    ):
        record["reason"] = "wartime_paused_scene_or_decision_not_available"
        return record
    record["source_pair"] = {
        "save_sha256": manifest["source_save_sha256"],
        "driver_sha256": manifest["source_driver_sha256"],
        "history_index": manifest["expected_history_index"],
        "date_raw": manifest["expected_date_raw"],
    }
    record["war_ids_before"] = [
        war.get("war_id") for war in starting_snapshot["active_wars"]
        if isinstance(war, dict)
    ]
    start_revision = starting_snapshot.get("revision")
    _need(isinstance(start_revision, int) and start_revision > 0,
          "public paused revision is unavailable")
    driver.execute_step(ROOT_STEP, expected_revision=start_revision)
    scoped_snapshot = driver.take_snapshot()
    _need(_frame(scoped_snapshot) == starting,
          "campaign root query changed the native paused frame")
    scope = same_frame_feudal_lifestyle_scope(
        scoped_snapshot, scoped_snapshot.get("native_command_history", [])
    )
    record["scope"] = scope
    if scope.get("status") != "admitted" or scope.get("at_peace") is not False:
        record.update(status="scope_unavailable", reason="feudal war scope unproved")
        return record
    query = driver.query_player_lifestyle_formal_private_v1(
        expected_revision=int(scoped_snapshot["revision"])
    )
    record["query_status"] = query.get("status")
    if query.get("status") != "available" or query.get(
        "formal_precondition_status"
    ) != "ready":
        record.update(status="query_unavailable", reason="formal perk query not ready")
        return record
    observed = query.get("snapshot")
    decision = choose_min_feudal_lifestyle_action(
        observed, feudal_scope_admitted=True, at_peace=False,
        allow_wartime_perk=True,
    )
    record["decision"] = decision
    action = decision.get("selected_action")
    if (
        decision.get("policy_id") != WAR_PERK_POLICY_ID
        or decision.get("status") != "recommend_action"
        or not isinstance(action, dict)
        or action.get("kind") != "perk"
        or action.get("target_key") != TARGET
        or not isinstance(observed, dict)
    ):
        record.update(status="no_legal_wartime_perk", reason=decision.get("status"))
        return record
    before_progress = observed.get("current_lifestyle_progress")
    _need(isinstance(before_progress, dict), "pre-action point row is absent")
    pre_unspent = before_progress.get("unspent_perk_points")
    pre_used = before_progress.get("used_perk_points")
    _need(
        isinstance(pre_unspent, int) and pre_unspent > 0
        and isinstance(pre_used, int) and pre_used >= 0,
        "pre-action stewardship point counts are unavailable",
    )
    record["pre_points"] = {"unspent": pre_unspent, "used": pre_used}
    current = plan_current_turn()
    current_plan = current.get("plan") if isinstance(current, dict) else None
    record["current_war_plan"] = current_plan
    prior_life = (
        current.get("_private_lifestyle_pending_v1")
        if isinstance(current, dict) else None
    )
    record["prior_lifestyle_pending"] = prior_life
    if prior_life is not None:
        record.update(status="prior_lifestyle_pending", reason="verify existing action")
        return record
    selected = (
        current_plan.get("selected_step")
        if isinstance(current_plan, dict) else None
    )
    if not (
        isinstance(current_plan, dict)
        and (selected is None or (
            isinstance(selected, str) and selected.startswith("query-")
        ))
    ):
        record.update(status="war_action_pending", reason="formal war step has priority")
        return record
    pending = driver.submit_player_lifestyle_perk_private_v1(
        query=query, action=action,
        expected_revision=int(driver.take_snapshot()["revision"]),
    )
    record["pending"] = pending
    _need(pending.get("status") == "submitted_verification_pending",
          "typed perk submission did not enter pending verification")
    record["gameplay_actions"] = 1
    wait_for_post(pending)
    later_snapshot = driver.take_snapshot()
    record["post_frame"] = _frame(later_snapshot)
    receipt = driver.query_player_lifestyle_receipt_private_v1(
        pending=pending, expected_revision=int(later_snapshot["revision"])
    )
    record["receipt"] = receipt
    _need(
        receipt.get("status") == "applied"
        and receipt.get("post_target_perk_owned") is True
        and receipt.get("postcondition_verified") is True,
        "independent native HasPerk receipt is not applied",
    )
    # Save the applied action before further read-only checks.  A later RED
    # still leaves the mainline with an official, restorable action pair.
    record["checkpoint"] = save_paired_checkpoint()
    _need(
        record["checkpoint"].get("status") == "saved"
        and record["checkpoint"].get("date_raw") == starting["date_raw"]
        and record["checkpoint"].get("history_index", 0)
        > manifest["expected_history_index"],
        "official post-action checkpoint did not extend the source pair",
    )
    post_read = query_player_lifestyle_private_v1(
        driver, expected_revision=int(driver.take_snapshot()["revision"]),
        query_step=STATE_QUERY_STEP,
    )
    record["post_read_status"] = post_read.get("status")
    post_state = post_read.get("snapshot")
    post_frame = driver.take_snapshot()
    progress = (
        post_state.get("current_lifestyle_progress")
        if isinstance(post_state, dict) else None
    )
    if not (
        post_read.get("status") == "available"
        and isinstance(post_state, dict)
        and post_state.get("snapshot_id") == post_frame.get("snapshot_id")
        and post_state.get("native_revision") == post_frame.get("native_revision")
        and post_state.get("date_raw") == starting["date_raw"]
        and post_state.get("player_character_id") == starting["played_character_id"]
        and post_state.get("episode_run_id") == starting["episode_run_id"]
        and post_state.get("current_focus") == observed.get("current_focus")
        and TARGET in post_state.get("owned_perk_keys", [])
        and isinstance(progress, dict)
        and progress.get("lifestyle_key") == "stewardship_lifestyle"
        and progress.get("unspent_perk_points") == pre_unspent - 1
        and progress.get("used_perk_points") == pre_used + 1
    ):
        record.update(status="post_points_red", reason="LIFE2 point delta unproved")
        return record
    record["post_points"] = {
        "unspent": progress["unspent_perk_points"],
        "used": progress["used_perk_points"],
    }
    following = plan_following_turn()
    following_plan = following.get("plan") if isinstance(following, dict) else None
    consumed = (
        following_plan.get("lifestyle_receipt_consumed")
        if isinstance(following_plan, dict) else None
    )
    record["following_plan"] = following_plan
    if isinstance(following_plan, dict) and str(
        following_plan.get("phase", "")
    ).startswith("native_war_"):
        record["war_red_preserved"] = {
            "phase": following_plan.get("phase"),
            "required_observation": following_plan.get("required_observation"),
            "selected_step": following_plan.get("selected_step"),
        }
    if not (
        isinstance(consumed, dict)
        and consumed.get("action_request_id") == pending.get("action_request_id")
        and consumed.get("postcondition_verified") is True
    ):
        record.update(status="next_turn_red", reason="formal receipt not consumed")
        return record
    ending_snapshot = driver.take_snapshot()
    ending = _frame(ending_snapshot)
    record["ending_frame"] = ending
    record["date_advanced"] = ending["date_raw"] != starting["date_raw"]
    _need(not record["date_advanced"], "wartime perk trial advanced the date")
    wars_after = ending_snapshot.get("active_wars")
    record["war_ids_after"] = (
        [war.get("war_id") for war in wars_after if isinstance(war, dict)]
        if isinstance(wars_after, list) else None
    )
    _need(record["war_ids_after"] == record["war_ids_before"],
          "wartime perk trial changed the active WarID set")
    record["status"] = "perk_checkpointed"
    return record


def run(candidate_root: Path, round_id: str, evidence: Path) -> int:
    spec, manifest, ready = preflight(
        candidate_root, expected_schema=SCHEMA, expected_read_only=False
    )
    _need(round_id.startswith("R") and round_id[1:].isdigit(),
          "sole operator must allocate a new R{n}")
    evidence = _non_c_task_path(evidence, "round evidence directory")
    _need(not evidence.exists(), "round evidence directory already exists")
    evidence.mkdir(parents=True)
    started = time.monotonic()
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA, "round_id": round_id,
        "candidate": str(candidate_root.resolve()),
        "python_source_commit": manifest["python_source_commit"],
        "native_source_commit": manifest["native_source_commit"],
        "game_exe_sha256": manifest["game_exe_sha256"],
        "native_dll_sha256": manifest["dll_sha256"],
        "source_save_sha256": manifest["source_save_sha256"],
        "source_driver_sha256": manifest["source_driver_sha256"],
        "preflight": ready, "status": "unexecuted", "started_at": _now(),
        "public_registered_or_advertised": False,
    }
    locks = ExitStack()
    driver = None
    handle = None
    try:
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.environment import ck3_process_inventory
        from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
        from xar_autoplayer.native_auto_run import (
            _verify_checkpoint_result, _wait_for_readiness,
        )
        from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch

        _need(not ck3_process_inventory().get("processes"), "old CK3 still alive")
        locks.enter_context(exclusive_launch_lock(spec.game_exe))
        locks.enter_context(exclusive_state_lock(spec.state_dir, "g2m4-wartime-perk"))
        driver = NativeHeadlessGameplayDriver(
            str(manifest["pipe"]), state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            succession_lifecycle_binding=ready["succession_lifecycle_binding"],
            allow_private_lifestyle_formal_trial=True,
        )
        service = GameplayBridgeService(driver)
        handle = launch(
            spec,
            native_bridge=NativeBridgeLaunchConfig(
                mode="native-headless", pipe_name=str(manifest["pipe"]),
                dll_path=Path(str(manifest["dll"])),
                injector_path=Path(str(manifest["injector"])),
            ),
            continue_last_save=False, load_save_name="xar_checkpoint",
            verify_prepared_profile=False,
        )
        report["process"] = {
            "pid": handle.process.pid,
            "creation_date": handle.ck3_creation_date,
            "watchdog_pid": handle.watchdog_pid,
            "watchdog_creation_date": handle.watchdog_creation_date,
            "command": handle.command,
        }
        _write(evidence / "round-ownership.json", report["process"])
        session_done = threading.Event()
        session_state: dict[str, object] = {}
        deadline = started + float(manifest["bounds"]["overall_seconds"])

        def ready_frame() -> dict[str, object]:
            _need(time.monotonic() < deadline, "wartime perk wall bound exhausted")
            return _wait_for_readiness(
                driver, session_done=session_done, session_state=session_state,
                timeout_seconds=min(
                    float(manifest["bounds"]["readiness_seconds"]),
                    deadline - time.monotonic(),
                ),
                stable_seconds=0.0, poll_interval_seconds=0.1,
                cold_start_checkpoint=False, allow_terminal=False,
            )

        def later_paused_frame(pending: dict[str, object]) -> dict[str, object]:
            source = pending.get("source_frame")
            _need(isinstance(source, dict), "typed perk source frame is absent")
            while time.monotonic() < deadline:
                frame = driver.take_snapshot()
                if (
                    frame.get("paused") is True
                    and frame.get("map_ready") is True
                    and frame.get("episode_run_id") == pending.get("episode_run_id")
                    and isinstance(frame.get("revision"), int)
                    and frame["revision"] > pending.get("pre_public_revision", 0)
                    and isinstance(frame.get("native_revision"), int)
                    and frame["native_revision"] > source.get("native_revision", 0)
                ):
                    return frame
                time.sleep(0.1)
            raise TimeoutError("typed perk lacks a later paused native frame")

        report["readiness"] = _wait_for_readiness(
            driver, session_done=session_done, session_state=session_state,
            timeout_seconds=int(manifest["bounds"]["readiness_seconds"]),
            stable_seconds=1.0, poll_interval_seconds=0.1,
            cold_start_checkpoint=True, allow_terminal=False,
        )

        def checkpoint() -> dict[str, object]:
            ready_frame()
            result = service.save_checkpoint(
                expected_revision=int(driver.take_snapshot()["revision"])
            )
            return _verify_checkpoint_result(
                result, snapshot=service.snapshot(),
                expected_save_dir=spec.profile_dir / "save games",
            )

        report["trial"] = choose_one_wartime_perk(
            driver, manifest, wait_for_post=later_paused_frame,
            save_paired_checkpoint=checkpoint,
            plan_current_turn=service.plan_turn,
            plan_following_turn=service.plan_turn,
        )
        report["status"] = report["trial"]["status"]
    except BaseException as error:
        report.update(
            status="red", red={"reason": f"{type(error).__name__}: {error}",
                               "traceback": traceback.format_exc()},
        )
    finally:
        if handle is not None:
            try:
                from xar_autoplayer.runtime import stop_tracked
                report["cleanup"] = stop_tracked(handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {
                    "ok": False, "issue": f"{type(error).__name__}: {error}"
                }
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
            from xar_autoplayer.native_session import validate_cold_start_checkpoint_for_pipe
            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_save_sha256": _sha(Path(str(manifest["source_save"]))),
                "prepared_save_sha256": _sha(Path(str(manifest["prepared_save"]))),
                "prepared_driver_sha256": _sha(Path(str(manifest["prepared_driver"]))),
                "wall_seconds": time.monotonic() - started,
            }
            if isinstance(report.get("trial"), dict) and isinstance(
                report["trial"].get("checkpoint"), dict
            ):
                report["postflight"]["paired_checkpoint"] = (
                    validate_cold_start_checkpoint_for_pipe(
                        spec, str(manifest["pipe"])
                    )
                )
        except BaseException as error:
            report["postflight_red"] = f"{type(error).__name__}: {error}"
        post = report.get("postflight")
        reclaimed = bool(
            isinstance(report.get("cleanup"), dict)
            and report["cleanup"].get("ok") is True
            and isinstance(post, dict)
            and not post["ck3_inventory"].get("processes")
            and post["source_save_sha256"] == manifest["source_save_sha256"]
            and post["wall_seconds"] <= manifest["bounds"]["overall_seconds"]
            and not report.get("driver_close_red")
            and not report.get("lock_close_red")
        )
        report["ck3_reclaimed"] = reclaimed
        paired = post.get("paired_checkpoint") if isinstance(post, dict) else None
        trial_checkpoint = (
            report["trial"].get("checkpoint")
            if isinstance(report.get("trial"), dict) else None
        )
        if report["status"] == "perk_checkpointed" and not (
            isinstance(paired, dict)
            and isinstance(trial_checkpoint, dict)
            and paired.get("sha256") == trial_checkpoint.get("sha256")
            and post["prepared_save_sha256"] == trial_checkpoint.get("sha256")
        ):
            report["status"] = "red_pair"
        if not reclaimed:
            report["status"] = "red_cleanup"
        report["finished_at"] = _now()
        _write(evidence / "report.json", report)
    print(json.dumps({"status": report["status"],
                      "ck3_reclaimed": report["ck3_reclaimed"],
                      "evidence": str(evidence)}, sort_keys=True))
    return 0 if report["ck3_reclaimed"] and report["status"] == "perk_checkpointed" else 2


def main() -> int:
    args = parser(description=__doc__).parse_args()
    if args.prepare_only:
        required = (
            "python_source_repo", "native_source_repo",
            "expected_python_source_commit", "expected_native_source_commit",
            "source_save", "source_driver", "expected_source_save_sha256",
            "expected_source_driver_sha256", "game_dir", "bridge_dll",
            "bridge_injector", "cmake_cache", "pipe", "expected_actor_id",
            "expected_date_raw", "expected_history_index",
        )
        _need(all(getattr(args, name) is not None for name in required),
              "--prepare-only requires complete source/build/pair identity")
        print(json.dumps(prepare_candidate(
            args, schema=SCHEMA, read_only=False
        ), sort_keys=True))
        return 0
    if args.preflight_only:
        _, _, ready = preflight(
            args.candidate_root, expected_schema=SCHEMA,
            expected_read_only=False,
        )
        print(json.dumps(ready, sort_keys=True))
        return 0
    _need(args.round is not None and args.evidence is not None,
          "live mode requires allocated --round and fresh --evidence")
    return run(args.candidate_root, args.round, args.evidence)


if __name__ == "__main__":
    raise SystemExit(main())
