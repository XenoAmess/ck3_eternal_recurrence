"""Owner-only bounded paused M4 typed submit and independent material read.

This is a controlled private acceptance helper for an already running,
single-owner NativeHeadlessGameplayDriver. It does not launch CK3, manipulate
the screen, open a county view, or advertise a public action. A lost command
response is recorded as unknown; callers must query stock Province state
before considering any new submit.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from run_g2m4_paused_player_view_read import (
    PRIVATE_STEP, _frame_binding, _read_step, _scene_issue,
)
from run_g2m4_paused_player_world_building_source_read import (
    run_owned_paused_player_world_building_source_read,
)


ACTION_STEP = "g2_player_world_building_action_private_v1"
EXACT_EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
PENDING_INTERACTION_STEPS = frozenset({
    "query-pending-character-interaction-context-v1",
    "accept-pending-character-interaction",
    "reject-pending-character-interaction",
    "block-pending-character-interaction",
    "acknowledge-pending-character-interaction",
})


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _stock_material_match(
    active: object, pending: dict[str, object], actor: int,
) -> bool:
    return isinstance(active, list) and any(
        isinstance(row, dict) and row.get("active") is True
        and row.get("barony_title_id") == pending.get("barony_title_id")
        and row.get("province_id") == pending.get("province_id")
        and row.get("building_type_id") == pending.get("building_type_id")
        and row.get("slot_index") == pending.get("slot_index")
        and row.get("initiator_character_id") == actor
        for row in active
    )


def _wait_for_newer_paused_frame(
    driver: Any,
    previous: dict[str, object],
    timeout_seconds: float,
    *,
    poll_interval_seconds: float = 0.05,
) -> tuple[dict[str, object] | None, dict[str, object], str | None]:
    """Wait until the bridge publishes the post-submit paused native frame.

    The command ACK can arrive before ``semantic_snapshot`` advances beyond
    the frame that admitted the command.  A private read against that old
    revision is rejected by the bridge and must not be treated as material
    evidence.  This wait performs no gameplay command and never retries the
    submitted construction action.
    """

    previous_revision = previous.get("native_revision")
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    last = _frame_binding(driver.state.semantic_snapshot())
    while True:
        revision = last.get("native_revision")
        if _positive_int(revision) and _positive_int(previous_revision):
            if revision < previous_revision:
                return None, last, "post_action_native_revision_regressed_keep_pending"
            if revision > previous_revision and last.get("paused") is True:
                if (
                    last.get("map_ready") is not True
                    or last.get("played_character_id")
                    != previous.get("played_character_id")
                    or last.get("played_character_alive") is not True
                    or last.get("date_raw") != previous.get("date_raw")
                ):
                    return None, last, "post_action_frame_identity_changed_keep_pending"
                return last, last, None
        now = time.monotonic()
        if now >= deadline:
            return None, last, "newer_paused_frame_timeout_keep_pending"
        time.sleep(min(max(0.0, poll_interval_seconds), deadline - now))
        last = _frame_binding(driver.state.semantic_snapshot())


def drain_official_pending_interactions_for_construction_read(
    service: Any,
    *,
    max_turns: int = 4,
) -> dict[str, object]:
    """Use only formal ``auto_turn`` to clear a forced interaction scene.

    Construction material reads are rejected while CK3 exposes an active
    event or pending character interaction.  A formal turn may advance into
    such a scene, so the acceptance runner must give the production planner a
    bounded chance to query and answer it before issuing another private
    construction read.  This helper never invokes the construction action or
    a direct interaction reply.  A missing typed production handler remains a
    capability RED with the planner's exact requirement attached.
    """

    if (
        not isinstance(max_turns, int)
        or isinstance(max_turns, bool)
        or max_turns <= 0
    ):
        raise ValueError("max_turns must be a positive integer")

    turns: list[dict[str, object]] = []
    record: dict[str, object] = {
        "schema_version": 1,
        "status": "unexecuted",
        "max_turns": max_turns,
        "official_turns": turns,
        "construction_action_submits": 0,
        "construction_read_permitted": False,
    }

    for turn_number in range(1, max_turns + 1):
        snapshot = service.snapshot()
        binding = _frame_binding(snapshot)
        pending = binding.get("pending_character_interaction")
        record["last_frame"] = binding

        if pending is None:
            issue = _scene_issue(binding)
            if issue is None:
                record.update(
                    status="scene_eligible",
                    turns_used=turn_number - 1,
                    construction_read_permitted=True,
                )
            else:
                record.update(
                    status="capability_red",
                    issue=f"scene_not_eligible_after_pending_drain:{issue}",
                    turns_used=turn_number - 1,
                )
            return record

        before = {
            "turn_number": turn_number,
            "frame": binding,
            "pending_character_interaction": pending,
        }
        try:
            outcome = service.auto_turn()
        except Exception as error:
            before.update(
                status="red_action_state_unknown",
                error=f"{type(error).__name__}: {error}",
            )
            turns.append(before)
            record.update(
                status="red_action_state_unknown",
                issue="official_pending_auto_turn_failed_stop_without_retry",
                turns_used=turn_number,
            )
            return record

        plan = outcome.get("plan") if isinstance(outcome, dict) else None
        selected_step = (
            outcome.get("selected_step")
            if isinstance(outcome, dict)
            else None
        )
        if selected_step is None and isinstance(plan, dict):
            selected_step = plan.get("selected_step")
        before["outcome"] = outcome
        turns.append(before)

        if not isinstance(outcome, dict) or outcome.get("status") != "executed":
            record.update(
                status="capability_red",
                issue="official_pending_handler_unavailable",
                turns_used=turn_number,
                planner_phase=(
                    plan.get("phase") if isinstance(plan, dict) else None
                ),
                required_step=(
                    plan.get("required_step")
                    if isinstance(plan, dict)
                    else None
                ),
                required_capabilities=(
                    plan.get("required_capabilities")
                    if isinstance(plan, dict)
                    else None
                ),
            )
            return record
        if selected_step not in PENDING_INTERACTION_STEPS:
            record.update(
                status="capability_red",
                issue="unexpected_official_step_while_pending",
                turns_used=turn_number,
                selected_step=selected_step,
                planner_phase=(
                    plan.get("phase") if isinstance(plan, dict) else None
                ),
            )
            return record

    final_snapshot = service.snapshot()
    final_binding = _frame_binding(final_snapshot)
    record["last_frame"] = final_binding
    issue = _scene_issue(final_binding)
    if issue is None:
        record.update(
            status="scene_eligible",
            turns_used=max_turns,
            construction_read_permitted=True,
        )
        return record
    last_outcome = turns[-1].get("outcome") if turns else None
    last_plan = (
        last_outcome.get("plan")
        if isinstance(last_outcome, dict)
        else None
    )
    record.update(
        status="capability_red",
        issue=f"bounded_pending_drain_exhausted:{issue}",
        turns_used=max_turns,
        planner_phase=(
            last_plan.get("phase") if isinstance(last_plan, dict) else None
        ),
        required_step=(
            last_plan.get("required_step")
            if isinstance(last_plan, dict)
            else None
        ),
        required_capabilities=(
            last_plan.get("required_capabilities")
            if isinstance(last_plan, dict)
            else None
        ),
    )
    return record


def run_owned_paused_world_building_action(
    driver: Any, frozen: dict[str, object], artifact_path: str | Path,
    *, timeout_seconds: float = 12.0,
) -> dict[str, object]:
    artifact = Path(artifact_path)
    report: dict[str, object] = {
        "schema_version": 1,
        "package_id": "G2-M4-CONSTRUCTION-COST-TO-ACTION-B0",
        "controlled_private_action": True,
        "advertised": False,
        "status": "unexecuted",
        "frozen": frozen,
        "timeout_seconds_per_step": timeout_seconds,
    }
    try:
        if str(frozen.get("ck3_exe_sha256", "")).casefold() != EXACT_EXE_SHA256:
            report.update(status="red", issue="wrong_exact_build_manifest")
            return report
        before = _frame_binding(driver.state.semantic_snapshot())
        report["starting_frame"] = before
        if not _positive_int(before.get("native_revision")) or before.get("paused") is not True:
            report.update(status="ineligible_scene", issue="not_paused_revision")
            return report
        preflight_path = artifact.with_name(artifact.stem + ".preflight.json")
        preflight = run_owned_paused_player_world_building_source_read(
            driver, frozen, preflight_path, timeout_seconds=timeout_seconds
        )
        report["preflight_path"] = str(preflight_path)
        report["preflight_status"] = preflight.get("status")
        report["preflight_issue"] = preflight.get("issue")
        if preflight.get("status") not in {
            "world_player_legality_observed", "world_player_cost_observed"
        }:
            report.update(status="red", issue="preflight_world_tuple_unavailable")
            return report
        world = preflight.get("player_world_building_sources")
        if not isinstance(world, dict) or world.get("native_cost_evaluated") is not True:
            report.update(status="red", issue="preflight_stock_cost_unavailable")
            return report
        if not isinstance(world.get("active_constructions"), list):
            report.update(status="red", issue="preflight_active_state_unavailable")
            return report
        if _frame_binding(driver.state.semantic_snapshot()) != before:
            report.update(status="red", issue="frame_changed_after_preflight")
            return report
        action_request_id, action_frame = _read_step(
            driver, ACTION_STEP, before["native_revision"], timeout_seconds
        )
        report["action_request_id"] = action_request_id
        report["action_frame"] = action_frame
        if action_frame is None:
            report.update(status="red_action_state_unknown", issue="action_response_timeout_query_state_before_retry")
            return report
        result = action_frame.get("result")
        private_probe = result.get("private_probe") if isinstance(result, dict) else None
        pending = private_probe.get("private_action") if isinstance(private_probe, dict) else None
        if not isinstance(pending, dict):
            report.update(status="red_action_state_unknown", issue="typed_action_receipt_missing_query_state_before_retry")
            return report
        report["pending_action"] = pending
        if pending.get("status") != "pending_receipt" or pending.get("applied") is not False:
            report.update(status="red" if pending.get("status") == "red" else "action_unready",
                          issue=str(pending.get("native_failure") or pending.get("candidate_failure")))
            return report
        if (result.get("step") != ACTION_STEP or result.get("accepted") is not True
                or pending.get("advertised") is not False
                or pending.get("production_native_path") is not True
                or pending.get("validator_calls") != 1
                or pending.get("materialize_calls") != 1
                or pending.get("receiver_calls") != 1
                or not _positive_int(pending.get("receiver_command_sequence"))
                or not _positive_int(pending.get("proof_epoch"))
                or pending.get("actor_character_id") != before["played_character_id"]):
            report.update(status="red_action_state_unknown", issue="pending_ack_shape_invalid_query_state_before_retry")
            return report
        tuples = world.get("legal_samples")
        if not isinstance(tuples, list) or not any(
            isinstance(row, dict)
            and all(row.get(key) == pending.get(key) for key in (
                "barony_title_id", "province_id", "building_type_id", "slot_index"))
            and isinstance(row.get("cost_raw_native"), list)
            and len(row["cost_raw_native"]) == 10
            and row["cost_raw_native"][0] == pending.get("stock_gold_cost_raw")
            and all(raw == 0 for raw in row["cost_raw_native"][1:])
            for row in tuples
        ):
            report.update(status="red_action_state_unknown", issue="action_tuple_not_in_preflight_stock_cost_query_state_before_retry")
            return report
        report["status"] = "pending_ack_observed"
        material_frame, after, frame_issue = _wait_for_newer_paused_frame(
            driver, before, timeout_seconds
        )
        report["after_action_frame"] = after
        report["material_query_frame"] = material_frame
        if material_frame is None:
            report.update(status="pending_receipt", issue=frame_issue)
            return report
        read_request_id, read_frame = _read_step(
            driver, PRIVATE_STEP, material_frame["native_revision"], timeout_seconds
        )
        report["material_read_request_id"] = read_request_id
        report["material_read_frame"] = read_frame
        if read_frame is None:
            report.update(status="pending_receipt", issue="material_read_timeout_keep_pending")
            return report
        read_result = read_frame.get("result")
        read_probe = read_result.get("private_probe") if isinstance(read_result, dict) else None
        next_world = read_probe.get("player_world_building_sources") if isinstance(read_probe, dict) else None
        next_epoch = read_probe.get("proof_epoch") if isinstance(read_probe, dict) else None
        if (not isinstance(next_world, dict) or next_world.get("status") != "source_available"
                or not _positive_int(next_epoch) or next_epoch <= pending["proof_epoch"]):
            report.update(status="pending_receipt", issue="fresh_material_source_unavailable_keep_pending")
            return report
        report["material_world"] = next_world
        if (next_world.get("player_character_id") == pending["actor_character_id"]
                and next_world.get("date_raw") >= before["date_raw"]
                and _stock_material_match(next_world.get("active_constructions"), pending,
                                          pending["actor_character_id"])):
            report["status"] = "independent_paused_material_observed"
            report["material_proof_epoch"] = next_epoch
            report["next_gate"] = "native_auto_run_or_ck3_auto_turn_next_policy_turn_consumes_construction_then_checkpoint_cold_restore"
        else:
            report.update(status="pending_receipt", issue="stock_active_construction_not_yet_matched_keep_pending")
        return report
    except Exception as error:
        report.update(status="red_action_state_unknown",
                      issue=f"{type(error).__name__}: {error}; query stock state before retry")
        return report
    finally:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")


__all__ = [
    "drain_official_pending_interactions_for_construction_read",
    "_wait_for_newer_paused_frame",
    "run_owned_paused_world_building_action",
]
