"""Same Root Queue, ordinary successor, no SDK/Game owner.

The pure validators below are copied from SDK86 7a6 native_auto_run.py.
Raw Queue responses remain the authority.
"""
from __future__ import annotations

import copy
import re

CONTINUE_AS_RECONCILED_SUCCESSOR_STEP = "continue-as-reconciled-successor"
SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA = "xar.ck3.succession-lifecycle-binding/v1"
ROGUE_ONE_LIFE = "rogue_one_life"
AgentError = ValueError


def ordinary_no_pact_lifecycle(value):
    """Consume a frozen lifecycle; do not infer mod absence from None.

    The legacy xar_off branch keeps its original admission. A new vanilla
    binding is produced only after the SDK verifies profile/startup evidence.
    This queue consumer stays independent of SDK imports.
    """
    if not isinstance(value, dict) or value.get("lifecycle") != "ordinary_campaign_succession":
        return False
    if value.get("xar_enabled") == "xar_off":
        return True
    absence = "absent_by_verified_xar_mod_not_loaded"
    return (set(value) == {"schema", "lifecycle", "xar_enabled", "pact_contract",
                           "source", "environment_sha256"}
            and value.get("schema") == SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA
            and value.get("xar_enabled") is None
            and value.get("pact_contract") == absence
            and value.get("source") == absence
            and isinstance(value.get("environment_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", value["environment_sha256"]) is not None)


def frame(snapshot):
    played = snapshot.get("played_character", {})
    return {
        "ending_date_raw": snapshot.get("date_raw"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "paused": snapshot.get("paused"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "episode_character_id": snapshot.get("episode_character_id"),
        "played_character_id": played.get("character_id"),
        "played_character_alive": played.get("alive"),
        "one_life_terminal": snapshot.get("one_life_terminal"),
        "one_life_terminal_reason": snapshot.get("one_life_terminal_reason"),
        "frame_source": "actual_successor_snapshot",
    }


def binding(snapshot, capabilities):
    """Only the source runner binding fields used by its transition validator."""
    diagnostics = capabilities.get("diagnostics", {})
    control = capabilities.get("native_session_control", {})
    observed = frame(snapshot)
    observed["date_raw"] = observed.pop("ending_date_raw")
    observed.update({
        "snapshot_id": snapshot.get("snapshot_id"),
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
        "episode_binding_state": control.get("episode_binding_state"),
        "driver_state_restore_kind": control.get("driver_state_restore_kind"),
    })
    if (type(observed["bridge_pid"]) is not int
            or observed["bridge_pid"] <= 0
            or type(observed["connection_generation"]) is not int
            or observed["connection_generation"] <= 0
            or any(snapshot.get("diagnostics", {}).get(key) != observed[key]
                   for key in ("bridge_pid", "connection_generation"))):
        raise ValueError("transition lacks an actual process/generation binding")
    return observed


def goal_matches(before, after, successor_id, *, increment):
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("ordinary successor requires the actual retained campaign goal")
    keys = ("goal_key", "campaign_id", "origin_character_id")
    if (before.get("format_version") != 1 or after.get("format_version") != 1
            or before.get("goal_key") != "dynasty_continuity"
            or not isinstance(before.get("campaign_id"), str) or not before["campaign_id"]
            or type(before.get("origin_character_id")) is not int
            or before["origin_character_id"] <= 0
            or type(before.get("current_character_id")) is not int
            or before["current_character_id"] <= 0
            or any(before.get(key) != after.get(key) for key in keys)
            or after.get("current_character_id") != successor_id):
        raise ValueError("ordinary successor changed campaign/origin/current goal binding")
    old_count = before.get("progress", {}).get("reconciled_successions")
    new_count = after.get("progress", {}).get("reconciled_successions")
    if (type(old_count) is not int or type(new_count) is not int
            or old_count < 0
            or new_count != old_count + increment):
        raise ValueError("ordinary goal succession increment is not the actual one transition")


def snapshot_once(queue, kind):
    return queue.call("ck3_take_snapshot",
                      {"include_native_command_history": False}, kind)


def require_current_successor(snapshot, transition):
    played = snapshot.get("played_character", {})
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or played.get("alive") is not True
            or played.get("character_id") != transition["successor_character_id"]
            or snapshot.get("episode_character_id") != transition["successor_character_id"]
            or snapshot.get("episode_run_id") != transition["episode_run_id"]
            or snapshot.get("succession_lifecycle") != transition["succession_lifecycle"]
            or snapshot.get("one_life_terminal") is True
            or snapshot.get("one_life_terminal_reason") is not None):
        raise ValueError("successor checkpoint input is not its actual living paused episode")
    goal_matches(transition["campaign_goal_after"], snapshot.get("campaign_goal"),
                 transition["successor_character_id"], increment=0)
    # Compare only this live transition; cold initial inputs use their new process.
    predecessor = transition.get("predecessor_binding", {})
    successor = transition.get("successor_episode_binding", {})
    observed = snapshot.get("diagnostics", {})
    if any(type(successor.get(key)) is not int or successor[key] <= 0
           or predecessor.get(key) != successor[key]
           or observed.get(key) != successor[key]
           for key in ("bridge_pid", "connection_generation")):
        raise ValueError("live successor changed its verified native process/connection")


def continue_successor(queue, expected_episode, transitions):
    before, before_path = snapshot_once(queue, "m7-predecessor-snapshot")
    if (before.get("episode_character_id") != expected_episode["episode_character_id"]
            or before.get("episode_run_id") != expected_episode["episode_run_id"]
            or before.get("campaign_goal", {}).get("current_character_id") != before.get("episode_character_id")
            or before.get("one_life_terminal") is not True
            or before.get("one_life_terminal_reason") != "played_character_changed"):
        raise ValueError("the observed terminal is not this retained predecessor transition")
    lifecycle = before.get("succession_lifecycle", {})
    if not ordinary_no_pact_lifecycle(lifecycle):
        raise ValueError("natural Queue continuation requires a qualified ordinary no-pact lifecycle")
    caps_before, _ = queue.call("ck3_get_capabilities", {}, "m7-before-capabilities")
    before_binding = binding(before, caps_before)
    planned, plan_path = queue.call("ck3_plan_turn", {}, "m7-successor-plan")
    plan = planned.get("plan", {})
    if (plan.get("selected_step") != CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
            or planned.get("revision") != before.get("revision")
            or planned.get("snapshot_id") != before.get("snapshot_id")):
        raise ValueError("retain actual pending/red reconciliation; do not force a successor")
    turn, turn_path = queue.call("ck3_auto_turn", {}, "m7-successor-continue")
    after, after_path = snapshot_once(queue, "m7-successor-snapshot")
    caps_after, _ = queue.call("ck3_get_capabilities", {}, "m7-after-capabilities")
    transition = _verify_natural_succession_transition(
        turn.get("result"), snapshot=after, binding=binding(after, caps_after),
        before=before_binding, succession_lifecycle=lifecycle)
    goal_matches(before.get("campaign_goal"), after.get("campaign_goal"),
                 transition["successor_character_id"], increment=1)
    transition.update({
        "predecessor_snapshot_response": str(before_path),
        "transition_plan_response": str(plan_path),
        "continuation_response": str(turn_path),
        "successor_snapshot_response": str(after_path),
        "campaign_goal_before": copy.deepcopy(before["campaign_goal"]),
        "campaign_goal_after": copy.deepcopy(after["campaign_goal"]),
        "successor_checkpoint": {"status": "pending_actual_clear_successor_save"},
    })
    return finish_transition(queue, after, after_path, transition, transitions)


def completed_continuation(turn):
    result = turn.get("result") if isinstance(turn, dict) else None
    # Include unknown/failed attempts so the caller stops instead of submitting
    # another ordinary turn that could repeat an unconfirmed continuation.
    return bool(isinstance(turn, dict) and (
        turn.get("selected_step") == CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
        or (isinstance(result, dict)
            and result.get("step") == CONTINUE_AS_RECONCILED_SUCCESSOR_STEP)))


def consume_completed(queue, turn, response_path, source_snapshot, source_path,
                      transitions, checkpoint_pair=None):
    """Consume the original completed response, never submit continuation again.

    An earlier living snapshot can validate an already saved reference, but it
    cannot stand in for a fresh terminal before-anchor. A new transition needs
    an independently retained terminal snapshot on the original result frame;
    otherwise stop for Root review after reads, before any Close or SAVE.
    """
    result = turn.get("result", {})
    reconciliation = result.get("reconciliation", {})
    pre = reconciliation.get("predecessor_binding", {})
    post = reconciliation.get("successor_binding", {})
    predecessor_id = result.get("predecessor_character_id")
    successor_id = result.get("successor_character_id")
    old_run, new_run = result.get("source_episode_run_id"), result.get("episode_run_id")
    lifecycle = source_snapshot.get("succession_lifecycle", {})
    if (turn.get("status") != "executed"
            or turn.get("selected_step") != CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
            or result.get("step") != CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
            or result.get("accepted") is not True or result.get("status") != "continued"
            or result.get("source") != "native-played-character-transition"
            or result.get("lifecycle_intent") != "natural_succession"
            or result.get("continue_as_heir_after_death") is not True
            or result.get("heir_gameplay_actions") != 0
            or result.get("ck3_command_submitted") is not False
            or result.get("process_restarted") is not False
            or type(predecessor_id) is not int or predecessor_id <= 0
            or type(successor_id) is not int or successor_id <= 0 or successor_id == predecessor_id
            or not isinstance(old_run, str) or not old_run
            or not isinstance(new_run, str) or not new_run or old_run == new_run
            or not ordinary_no_pact_lifecycle(lifecycle)
            or result.get("succession_lifecycle") != lifecycle
            or reconciliation.get("status") != "available"
            or reconciliation.get("verdict") != "matched"
            or reconciliation.get("successor_match") is not True
            or reconciliation.get("title_distribution_match") is not True
            or reconciliation.get("predecessor_character_id") != predecessor_id
            or reconciliation.get("actual_successor_character_id") != successor_id
            or pre.get("episode_character_id") != predecessor_id
            or pre.get("episode_run_id") != old_run
            or not isinstance(post.get("snapshot_id"), str) or not post["snapshot_id"]
            or any(type(post.get(key)) is not int for key in ("revision", "native_revision", "date_raw"))
            or post["revision"] < 0 or post["native_revision"] <= 0
            or any(result.get(key) != post.get(key) for key in ("snapshot_id", "revision", "date_raw"))):
        raise ValueError("retain original unavailable/unknown/mismatched continuation; never resubmit")
    after, after_path = snapshot_once(queue, "m7-completed-successor-snapshot")
    caps, _ = queue.call("ck3_get_capabilities", {}, "m7-completed-successor-capabilities")
    actual = binding(after, caps)
    source_diagnostics = source_snapshot.get("diagnostics", {})
    if (type(source_diagnostics.get("bridge_pid")) is not int
            or source_diagnostics["bridge_pid"] <= 0
            or type(source_diagnostics.get("connection_generation")) is not int
            or source_diagnostics["connection_generation"] <= 0
            or any(source_diagnostics.get(key) != actual.get(key)
                   for key in ("bridge_pid", "connection_generation"))):
        raise ValueError("completed continuation lacks its actual retained physical predecessor context")
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or actual.get("played_character_alive") is not True
            or actual.get("played_character_id") != successor_id
            or after.get("episode_character_id") != successor_id
            or after.get("episode_run_id") != new_run
            or after.get("succession_lifecycle") != lifecycle
            or after.get("one_life_terminal") is True
            or after.get("one_life_terminal_reason") is not None):
        raise ValueError("original continuation does not bind the fresh living successor")
    if source_snapshot.get("episode_run_id") == new_run:
        # A bounded-loop resume reference after an already paired successor SAVE.
        # It creates no new natural/goal credit and never repeats Close or SAVE.
        if (not isinstance(checkpoint_pair, dict)
                or checkpoint_pair.get("episode_run_id") != new_run
                or checkpoint_pair.get("episode_character_id") != successor_id
                or checkpoint_pair.get("succession_lifecycle") != lifecycle
                or source_snapshot.get("episode_character_id") != successor_id
                or source_snapshot.get("campaign_goal", {}).get("current_character_id") != successor_id):
            raise ValueError("already-bound continuation reference requires the actual matched SAVE pair")
        goal_matches(source_snapshot.get("campaign_goal"), after.get("campaign_goal"),
                     successor_id, increment=0)
        queue.thin("m7-retained-continuation-reference", {
            "status": "already_checkpointed_reference_consumed", "continuation_response": str(response_path),
            "source_snapshot_response": str(source_path), "fresh_snapshot_response": str(after_path),
            "checkpoint_episode": checkpoint_pair, "new_natural_succession_credit": 0,
        })
        return after, after_path, None
    if (source_snapshot.get("one_life_terminal") is not True
            or source_snapshot.get("one_life_terminal_reason") != "played_character_changed"
            or any(source_snapshot.get(key) != post.get(key)
                   for key in ("snapshot_id", "revision", "native_revision", "date_raw"))):
        raise ValueError("new completed continuation lacks an independently retained terminal before-anchor; Root review")
    if (source_snapshot.get("episode_character_id") != predecessor_id
            or source_snapshot.get("episode_run_id") != old_run
            or source_snapshot.get("campaign_goal", {}).get("current_character_id") != predecessor_id
            or actual.get("episode_binding_state") != "active_natural_successor"
            or actual.get("driver_state_restore_kind") != "natural_succession"
            or any(after.get(key) != post.get(key)
                   for key in ("snapshot_id", "revision", "native_revision", "date_raw"))):
        raise ValueError("original continuation differs from the retained predecessor and fresh result frame")
    goal_matches(source_snapshot.get("campaign_goal"), after.get("campaign_goal"), successor_id, increment=1)
    transition = _verify_natural_succession_transition(
        result, snapshot=after, binding=actual,
        before=binding(source_snapshot, caps), succession_lifecycle=lifecycle)
    transition.update({
        "continuation_response": str(response_path), "successor_snapshot_response": str(after_path),
        "predecessor_context_response": str(source_path),
        "before_terminal_snapshot_independently_retained": True,
        "campaign_goal_before": copy.deepcopy(source_snapshot["campaign_goal"]),
        "campaign_goal_after": copy.deepcopy(after["campaign_goal"]),
        "successor_checkpoint": {"status": "pending_actual_clear_successor_save"},
    })
    return finish_transition(queue, after, after_path, transition, transitions)


def finish_transition(queue, after, after_path, transition, transitions):
    # Retain the actual new episode even if a later timeline call fails.
    transitions.append(transition)
    query, query_path = queue.call("ck3_query_current_timeline_blocker_context_v1",
                                  {"expected_revision": after["revision"]}, "m7-timeline")
    state = _ordinary_succession_timeline_state(query)
    continuation = {"status": state, "initial_query_response": str(query_path),
                    "close_result_response": None}
    transition["timeline_blocker_continuation"] = continuation
    if state == "close_required":
        close, close_path = queue.call("ck3_continue_death_succession_modal_v1", {
            "expected_revision": after["revision"],
            "expected_played_character_id": transition["successor_character_id"],
            "expected_episode_run_id": transition["episode_run_id"],
        }, "m7-modal-close")
        continuation["close_result_response"] = str(close_path)
        issue = _ordinary_succession_close_issue(
            close, starting_date_raw=after["date_raw"],
            successor_character_id=transition["successor_character_id"])
        if issue is not None:
            raise ValueError("retain original single Close result: " + issue)
        after, after_path = snapshot_once(queue, "m7-cleared-successor-snapshot")
        if any(after.get(left) != close.get(right) for left, right in (
                ("date_raw", "ending_date_raw"), ("revision", "ending_revision"),
                ("native_revision", "ending_native_revision"))):
            raise ValueError("independent successor snapshot disagrees with typed Close")
        continuation["status"] = "materially_cleared"
    elif state != "already_clear":
        raise ValueError("retain ambiguous/unavailable actual timeline; no invented modal action")
    require_current_successor(after, transition)
    transition["current_date_raw"] = after["date_raw"]
    transition["current_snapshot_response"] = str(after_path)
    queue.thin("m7-natural-transition", transition)
    return after, after_path, transition


def checkpoint_if_clear(queue, transition):
    current, current_path = snapshot_once(queue, "m7-save-readback")
    require_current_successor(current, transition)
    if _player_decision_pending(current):
        transition["successor_checkpoint"] = {"status": "deferred_player_decision"}
        return current, current_path, None
    saved, save_path = queue.call("ck3_save_checkpoint",
                                  {"expected_revision": current["revision"]}, "m7-successor-save")
    checkpoint = saved.get("checkpoint", {})
    if (checkpoint.get("status") != "saved"
            or checkpoint.get("date_raw") != current.get("date_raw")
            or checkpoint.get("episode_character_id") != transition["successor_character_id"]
            or checkpoint.get("episode_run_id") != transition["episode_run_id"]
            or checkpoint.get("succession_lifecycle") != current.get("succession_lifecycle")):
        raise ValueError("actual successor SAVE is not its exact episode/date/lifecycle pair")
    transition["successor_checkpoint"] = {
        "status": "saved", "snapshot_response": str(current_path),
        "save_response": str(save_path), "checkpoint": checkpoint,
        "campaign_goal": copy.deepcopy(current["campaign_goal"]),
    }
    queue.thin("m7-successor-save", transition["successor_checkpoint"])
    return current, current_path, save_path


# The author helper appends the existing SDK86 pure validation functions here.

def _timeline_typed_boolean(
    context: object, field: str, expected: bool
) -> bool:
    value = context.get(field) if isinstance(context, dict) else None
    return bool(
        isinstance(value, dict)
        and value.get("status") == "available"
        and value.get("value") is expected
        and value.get("unavailable_reason") is None
    )

def _ordinary_succession_timeline_state(query: object) -> str | None:
    """Classify one normalized private timeline query without guessing."""

    context = (
        query.get("current_timeline_blocker_context")
        if isinstance(query, dict)
        else None
    )
    if not isinstance(context, dict) or context.get("status") != "available":
        return None
    identity = context.get("identity")
    if (
        identity == "death_succession_modal"
        and _timeline_typed_boolean(context, "can_continue", True)
        and _timeline_typed_boolean(context, "blocks_simulation", True)
        and _timeline_typed_boolean(context, "has_open_succession", True)
    ):
        return "close_required"
    if (
        identity == "none"
        and _timeline_typed_boolean(context, "blocks_simulation", False)
        and _timeline_typed_boolean(context, "has_open_succession", False)
    ):
        return "already_clear"
    return None

def _ordinary_succession_close_issue(
    result: object,
    *,
    starting_date_raw: int,
    successor_character_id: int,
) -> str | None:
    """Require the existing private Close route's independent material proof."""

    if not isinstance(result, dict):
        return "result_unavailable"
    if result.get("status") != "materially_verified":
        return str(result.get("status") or "unknown_status")
    if result.get("material_result_verified") is not True:
        return "material_result_unverified"
    if result.get("starting_date_raw") != starting_date_raw:
        return "starting_date_mismatch"
    ending_date_raw = result.get("ending_date_raw")
    if (
        isinstance(ending_date_raw, bool)
        or not isinstance(ending_date_raw, int)
        or ending_date_raw <= starting_date_raw
    ):
        return "date_not_advanced"
    ack = result.get("submission_ack")
    if not (
        isinstance(ack, dict)
        and ack.get("accepted") is True
        and ack.get("status") == "submitted"
        and ack.get("played_character_id") == successor_character_id
        and ack.get("close_invocations") == 1
        and ack.get("material_result_verified") is False
    ):
        return "close_ack_invalid"
    if (
        _ordinary_succession_timeline_state(result.get("initial_query"))
        != "close_required"
    ):
        return "initial_modal_not_bound"
    if _ordinary_succession_timeline_state(
        result.get("postcondition_query")
    ) != "already_clear":
        return "independent_clear_not_observed"
    ending_revision = result.get("ending_revision")
    ending_native_revision = result.get("ending_native_revision")
    if (
        isinstance(ending_revision, bool)
        or not isinstance(ending_revision, int)
        or ending_revision < 0
        or isinstance(ending_native_revision, bool)
        or not isinstance(ending_native_revision, int)
        or ending_native_revision <= 0
    ):
        return "ending_revision_invalid"
    return None

def _verify_natural_succession_transition(
    result: object,
    *,
    snapshot: dict[str, object],
    binding: dict[str, object],
    before: dict[str, object],
    succession_lifecycle: dict[str, object],
) -> dict[str, object]:
    """Prove a same-process new episode on CK3's played successor."""

    if not isinstance(result, dict):
        raise AgentError("natural successor continuation returned no result")
    predecessor_id = before.get("episode_character_id")
    predecessor_run_id = before.get("episode_run_id")
    successor_id = before.get("played_character_id")
    successor_run_id = result.get("episode_run_id")
    reconciliation = result.get("reconciliation")
    successor_binding = (
        reconciliation.get("successor_binding")
        if isinstance(reconciliation, dict)
        else None
    )
    played = snapshot.get("played_character")
    same_frame_keys = (
        "bridge_pid",
        "connection_generation",
        "snapshot_id",
        "revision",
        "native_revision",
        "date_raw",
    )
    lifecycle_result_matches = (
        result.get("succession_lifecycle") == succession_lifecycle
        or (
            succession_lifecycle == legacy_rogue_one_life_binding_v1()
            and result.get("succession_lifecycle") is None
        )
    )
    if (
        isinstance(predecessor_id, bool)
        or not isinstance(predecessor_id, int)
        or not isinstance(predecessor_run_id, str)
        or not predecessor_run_id
        or isinstance(successor_id, bool)
        or not isinstance(successor_id, int)
        or successor_id == predecessor_id
        or before.get("played_character_alive") is not True
        or before.get("one_life_terminal") is not True
        or before.get("one_life_terminal_reason")
        != "played_character_changed"
        or result.get("step") != CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
        or result.get("accepted") is not True
        or result.get("status") != "continued"
        or result.get("source") != "native-played-character-transition"
        or result.get("lifecycle_intent") != "natural_succession"
        or not lifecycle_result_matches
        or result.get("predecessor_character_id") != predecessor_id
        or result.get("successor_character_id") != successor_id
        or result.get("source_episode_run_id") != predecessor_run_id
        or not isinstance(successor_run_id, str)
        or not successor_run_id
        or successor_run_id == predecessor_run_id
        or result.get("continue_as_heir_after_death") is not True
        or result.get("heir_gameplay_actions") != 0
        or result.get("ck3_command_submitted") is not False
        or result.get("process_restarted") is not False
        or any(binding.get(key) != before.get(key) for key in same_frame_keys)
        or snapshot.get("episode_character_id") != successor_id
        or snapshot.get("episode_run_id") != successor_run_id
        or not isinstance(played, dict)
        or played.get("character_id") != successor_id
        or played.get("alive") is not True
        or snapshot.get("one_life_terminal") is True
        or snapshot.get("one_life_terminal_reason") is not None
        or binding.get("episode_binding_state")
        != "active_natural_successor"
        or binding.get("driver_state_restore_kind") != "natural_succession"
        or not isinstance(reconciliation, dict)
        or reconciliation.get("status") != "available"
        or reconciliation.get("verdict") != "matched"
        or reconciliation.get("successor_match") is not True
        or reconciliation.get("title_distribution_match") is not True
        or reconciliation.get("predecessor_character_id") != predecessor_id
        or reconciliation.get("actual_successor_character_id") != successor_id
        or not isinstance(successor_binding, dict)
        or any(
            successor_binding.get(key) != before.get(key)
            for key in ("snapshot_id", "revision", "native_revision", "date_raw")
        )
    ):
        raise AgentError(
            "natural successor continuation lacks a matched same-process "
            "episode transition"
        )
    return {
        "status": "verified",
        "predecessor_character_id": predecessor_id,
        "successor_character_id": successor_id,
        "source_episode_run_id": predecessor_run_id,
        "episode_run_id": successor_run_id,
        "date_raw": binding.get("date_raw"),
        "same_campaign_frame": True,
        "ck3_command_submitted": False,
        "process_restarted": False,
        "succession_lifecycle": copy.deepcopy(succession_lifecycle),
        "reconciliation": copy.deepcopy(reconciliation),
        "predecessor_binding": _public_binding(before),
        "successor_episode_binding": _public_binding(binding),
    }

def _player_decision_pending(snapshot: object) -> bool:
    return bool(
        isinstance(snapshot, dict)
        and (
            isinstance(snapshot.get("active_event"), dict)
            or isinstance(
                snapshot.get("pending_character_interaction"), dict
            )
        )
    )

def _public_binding(binding: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in binding.items() if key != "_semantic"}

def legacy_rogue_one_life_binding_v1() -> dict[str, object]:
    """Return the pre-profile-binding behavior for old driver call sites."""

    return {
        "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        "lifecycle": ROGUE_ONE_LIFE,
        "xar_enabled": "xar_on",
        "pact_contract": "terminal_settlement_required",
        "source": "legacy-driver-default",
        "environment_sha256": None,
    }
