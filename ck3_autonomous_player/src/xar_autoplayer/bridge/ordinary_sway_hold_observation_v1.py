"""Monthly retained-Sway reads after a fully verified stationary hold.

The original planning frame remains untouched. A stop summary can prefilter a
due observation; only an actual, fully matched paused post snapshot can feed it.
"""
from collections.abc import Mapping

from ..ordinary_sway_lifecycle_observation_v1 import READERS
from ..ordinary_sway_schedule_v1 import _due, _state
from ..strategy import _battle_sentinel_advance_validation
from .ordinary_sway_quiet_observation_v1 import _observe_applied_after_turn, _start_identity
from .ordinary_sway_service_v1 import _inputs
from .war_contract import parse_war_objective_hold_sentinel_advance_step

KEY = "ordinary_sway_post_hold_observation"
FOUR = ("snapshot_id", "revision", "native_revision", "date_raw")


def _stop(planned, outcome):
    plan, source, result = planned.get("plan"), planned.get("planning_source_frame"), outcome.get("result")
    if (not isinstance(plan, Mapping) or not isinstance(source, Mapping)
            or source.get("status") != "complete" or not isinstance(result, dict)
            or plan.get("phase") != "native_war_stationary_objective_hold_sentinel"
            or planned.get("_private_window_priority_v1") is True
            or planned.get("_private_lifestyle_pending_v1") is not None
            or outcome.get("status") != "executed" or KEY in outcome
            or plan.get("selected_step") != outcome.get("selected_step")
            or result.get("step") != outcome.get("selected_step")
            or result.get("player_decision_boundary") is not None
            or result.get("one_life_terminal") is not False
            or result.get("one_life_terminal_reason") is not None
            or result.get("active_event") is not None
            or result.get("pending_character_interaction") is not None):
        return None
    request = parse_war_objective_hold_sentinel_advance_step(result["step"])
    if request is None or any(plan.get(key) != item for key, item in zip(
            ("war_id", "subject_army_id", "objective_province_id", "absolute_target_date_raw"), request)):
        return None
    valid = _battle_sentinel_advance_validation(result)
    if not isinstance(valid, dict) or valid.get("valid") is not True:
        return None
    post, admission = result.get("war_objective_hold_post_stop"), result.get("war_objective_hold_admission")
    if (not isinstance(post, dict) or post.get("status") != "matched"
            or not isinstance(admission, dict) or admission.get("status") != "matched"
            or plan.get("watch_army_ids") != result.get("watch_army_ids")
            or result.get("starting_date_raw") != source.get("date_raw")
            or result.get("date_raw", result.get("ending_date_raw")) != result.get("ending_date_raw")
            or result.get("bridge_pid") != source.get("bridge_pid")
            or result.get("connection_generation") != source.get("connection_generation")
            or result.get("episode_run_id") != source.get("episode_run_id")
            or result.get("episode_character_id") != source.get("actor_character_id")
            or result.get("played_character_id") != source.get("actor_character_id")
            or result.get("played_character_alive") is not True
            or type(source.get("bridge_pid")) is not int or source["bridge_pid"] <= 0
            or type(source.get("connection_generation")) is not int
            or not isinstance(result.get("snapshot_id"), str) or not result["snapshot_id"]
            or any(type(result.get(key)) is not int or type(source.get(key)) is not int
                   or result[key] <= source[key] for key in ("revision", "native_revision"))):
        return None
    return request


def _post_matches(snapshot, source, result, request):
    # Reuse the actual Native post-stop scope checker, including the complete
    # controllable roster, regular idle armies, siege and war/objective checks.
    from .native_driver import _battle_sentinel_stationary_objective_hold_state

    played, diagnostics = snapshot.get("played_character"), snapshot.get("diagnostics")
    context, hint = snapshot.get("active_context"), snapshot.get("top_exclusive_modal_choice_hint")
    armies = snapshot.get("player_armies")
    if context is None:
        context = snapshot
    if (not isinstance(played, Mapping) or played.get("alive") is not True
            or played.get("character_id") != source["actor_character_id"]
            or snapshot.get("episode_character_id") != source["actor_character_id"]
            or snapshot.get("episode_run_id") != source["episode_run_id"]
            or not isinstance(diagnostics, Mapping)
            or any(diagnostics.get(key) != source[key] for key in ("bridge_pid", "connection_generation"))
            or any(snapshot.get(key) != (result.get("ending_date_raw") if key == "date_raw" else result.get(key))
                   for key in FOUR)
            or snapshot.get("episode_identity_pending") is not False
            or snapshot.get("one_life_terminal") is not False
            or snapshot.get("one_life_terminal_reason") is not None
            or not isinstance(armies, list)
            or not all(isinstance(army, Mapping) and army.get("in_combat") is False
                       and army.get("retreating") is False and army.get("gathering") is not True for army in armies)
            or any(key not in context or context[key] is not None
                   for key in ("active_event", "pending_character_interaction"))
            or (isinstance(hint, Mapping) and hint.get("status") == "present")):
        return False
    post = _battle_sentinel_stationary_objective_hold_state(snapshot, tuple(result["watch_army_ids"]),
        war_id=request[0], subject_army_id=request[1], objective_province_id=request[2])
    return post.get("status") == "matched" and post == result["war_objective_hold_post_stop"]


def observe_sway_after_stationary_hold_v1(service, planned, outcome):
    """Never replace/retry the completed hold, including on optional I/O failure."""
    try:
        request = _stop(planned, outcome)
        if request is None or not any(getattr(service.driver, flag, False) is True for _, flag, _ in READERS):
            return outcome
        inputs = _inputs(service)
        if inputs is None:
            return outcome
        _, state, ledger = inputs
        resolved = ledger.get("resolved")
        source, result = planned["planning_source_frame"], outcome["result"]
        identity = _start_identity(resolved)
        terminal = resolved.get("terminal_intervention") if isinstance(resolved, Mapping) else None
        if (ledger.get("pending") is not None or identity is None or identity[1] != source.get("actor_character_id")
                or (isinstance(terminal, Mapping) and terminal.get("instance_terminal_outcome_observed") is True)):
            return outcome
        cadence = _state(state, identity[1])
        if (cadence.get("last_observation_attempt_action_id") == identity[0]
                and not _due(cadence, result["ending_date_raw"])):
            return outcome
        # The ledger/month gate above adds zero snapshots on inactive/not-due
        # holds. This is a real post read, never a summary with filled fields.
        snapshot = service.snapshot(include_native_command_history=False)
        if not _post_matches(snapshot, source, result, request):
            return outcome
        return _observe_applied_after_turn(service, planned, outcome,
            window="after_verified_stationary_objective_hold", receipt_key=KEY,
            verified_hold_snapshot=snapshot)
    except Exception as error:
        return {**outcome, KEY: {"status": "unavailable", "reason": f"{type(error).__name__}: {error}",
                "submit_attempted": False, "request_retried": False, "new_game_days": 0}}
