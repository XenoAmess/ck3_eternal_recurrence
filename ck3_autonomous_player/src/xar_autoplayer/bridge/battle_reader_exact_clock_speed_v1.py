"""Speed admission for an already selected hands-off exact battle watch day.

Date accuracy is supplied by the existing Native daily sentinel. This module
does not certify a battle prediction, change orders, or authorize retreat.
"""
from .battle_reader_watch_v1 import CLOCK_CAPABILITIES, select_watch


def reader_watch_exact_speed_five_ready_v1(
    snapshot, history, *, exact_one_day, result_step, proof_kind,
    bridge_capabilities, available_action_steps, assault_in_progress,
):
    if (exact_one_day is not True or result_step != "life-advance-one-day"
            or proof_kind is not None or assault_in_progress is not False
            or not isinstance(snapshot, dict)
            or not isinstance(history, list)
            or not isinstance(bridge_capabilities, set)
            or not CLOCK_CAPABILITIES <= bridge_capabilities
            or not isinstance(available_action_steps, set)
            or not {"life-advance-one-day", "set-speed-5", "resume-map", "pause-map"} <= available_action_steps
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("one_life_terminal") is not False
            or snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None
            or snapshot.get("war_objective_assault_supported") is not True):
        return False
    hint = snapshot.get("top_exclusive_modal_choice_hint")
    if (not isinstance(hint, dict) or hint.get("status") != "absent"
            or hint.get("owner_verified") is not True):
        return False
    played = snapshot.get("played_character")
    armies = snapshot.get("player_armies")
    if (not isinstance(played, dict) or played.get("alive") is not True
            or type(played.get("character_id")) is not int
            or not isinstance(armies, list) or not armies):
        return False
    # Restrict this candidate to an isolated ongoing combat. Do not turn a
    # concurrent moving/embarked/retreating/unknown army into a fast watch.
    for army in armies:
        if (not isinstance(army, dict) or army.get("controllable") is not True
                or army.get("owner_character_id") != played["character_id"]
                or army.get("in_combat") is not True or army.get("retreating") is not False
                or type(army.get("current_province_id")) is not int or army["current_province_id"] <= 0
                or army.get("move_target_province_id") is not None
                or army.get("route_province_ids") != []
                or army.get("army_state") != "combat"):
            return False
    if len({army["current_province_id"] for army in armies}) != 1:
        return False
    from ..strategy import _effective_command, _effective_command_result
    try:
        # Bounded scan, no transcript deep copy. select_watch validates the
        # exact original failed read and current scope/continuous-day lineage.
        watch = select_watch(snapshot, history[-256:], command=_effective_command,
                             result=_effective_command_result)
    except (TypeError, ValueError, KeyError):
        return False
    return (isinstance(watch, dict)
            and watch.get("status") == "reader_unavailable_hands_off"
            and watch.get("observed_date_raw") == snapshot.get("date_raw")
            and watch.get("prediction_ready") is False
            and watch.get("retreat_authorized") is False)
