"""Default-off Journaller adapter; original guarded routes own all submissions.

One positive attempt per full actor ID/original state root, including cold
re-entry. Adds no capability, public route, event execution or scheduling.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from .bridge.event_contract import action_step_set
from .bridge.ingame_decision_item_contract import normalize_decision_item
from .bridge.ingame_decision_item_action_contract import actual_selected_detail
from .bridge.ingame_decision_outcome_contract import actual_expected_event
from .bridge.ingame_decisions_open_contract import (
    actual_visible_decisions_tree, normalize_open_result, opening_binding,
)
from .ck3_live_run_identity_v1 import current_machine_id
from .ordinary_player_risk_context_v1 import build_ordinary_player_risk_context_v1


SCHEMA = "xar.ck3.journaller-stress-relief.v1"
DECISION = "stress_loss_journaller_decision"
EVENT = "stress_trait_coping_decisions.6501"
FLAG = "allow_private_journaller_stress_relief_v1"
SOURCE_PINS = {
    "common/decisions/90_minor_decisions.txt":
        "47da3707b26515a9d7d063395f834e4447d0ff9170d7c5c58d2da35e5dd4ecac",
    "common/on_action/stress_coping_decisions_on_actions.txt":
        "41f57ac3f06c843945ff36ccdaf9c719ac6bf5308301bb0d35f93612a17393b8",
    "events/stress_events/stress_trait_coping_decisions_events.txt":
        "d18a975ad72325e67d7dd5eb13d25d951608dc4153a0d60fd1e9fbf253f37327",
}
REQUIRED_CAPS = frozenset({
    "game.command.activate-ingame-decisions-v1",
    "game.command.query-ingame-decision-item-v1",
    "game.command.select-ingame-decision-item-v1",
    "game.command.confirm-ingame-decision-outcome-v1",
    "game.command.query-current-event-window-context-v1",
    "game.command.inspect-gui-window-tree-v1",
    "game.command.select-event-option-N",
})
_CONTROL = ("game_pid", "played_character_id", "connection_generation",
            "date_raw", "episode_run_id")


def verify_journaller_sources_v1(game_source_root: Path) -> dict:
    """Verify only three bounded authored inputs."""
    root = Path(game_source_root).resolve(strict=True)
    for relative, expected in SOURCE_PINS.items():
        target = (root / relative).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError("journaller source escaped its admitted root")
        if target.stat().st_size > 512 * 1024:
            raise ValueError("journaller authored source exceeded its read bound")
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError("journaller authored source changed: " + relative)
    return dict(SOURCE_PINS)


def _read(driver):
    return driver.take_snapshot_without_native_command_history()


def _same_frame(driver, original, *, allow_event=False):
    current = _read(driver)
    if (opening_binding(current) != opening_binding(original)
            or current.get("revision") != original.get("revision")
            or current.get("snapshot_id") != original.get("snapshot_id")
            or current.get("pending_character_interaction") is not None
            or not allow_event and current.get("active_event") is not None):
        raise ValueError("journaller current paused frame changed")
    return current


def _write_once(path, value):
    encoded = (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    if len(encoded) > 12 * 1024:
        raise ValueError("journaller receipt exceeded its small metadata bound")
    with path.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def _receipt_ref(result):
    return {key: result.get(key) for key in (
        "status", "action_request_id", "action_claim_path", "queried_revision",
        "postcondition_verified", "verification_pending",
    )}


def _exact_build(result, snapshot):
    hello = snapshot["diagnostics"]["hello"]
    if (not isinstance(result, dict)
            or result.get("game_version") != "1.20.0.4"
            or result.get("executable_sha256") != hello["expected_ck3_sha256"]):
        raise ValueError("journaller result belongs to another exact native build")


def _event_plan(snapshot, query):
    binding = opening_binding(snapshot)
    if not actual_expected_event(query, snapshot, binding, EVENT):
        raise ValueError("journaller exact later event/root/frame is unavailable")
    context = query["current_event_window_context"]
    if context["provenance"]["backend_id"] != "ck3-1.20.0.4-native-event-window-v1":
        raise ValueError("journaller event provenance belongs to another build")
    options = context["options"]
    if (len(options) != 1 or options[0].get("rendered_index") != 0
            or options[0].get("native_option_index") != 0
            or options[0].get("shown") is not True
            or options[0].get("enabled") is not True
            or type(snapshot["active_event"].get("option_count")) is not int
            or snapshot["active_event"].get("option_count") != 1):
        raise ValueError("journaller sole authored option is not the actual projection")
    diagnostics = snapshot.get("diagnostics", {})
    return {
        "policy": SCHEMA, "event_definition_key": EVENT,
        "event_instance_id": snapshot["active_event"]["instance_id"],
        "selected_step": "select-event-option-1", "selected_option_number": 1,
        "selected_native_option_index": 0,
        "reason": "选择实际显示的记日记选项；随后核对窗口和压力变化",
        "binding": {**binding, "revision": snapshot["revision"],
                    "snapshot_id": snapshot["snapshot_id"],
                    "bridge_pid": diagnostics.get("bridge_pid")},
        "source_sha256": dict(SOURCE_PINS),
        "health_treatment_credit": False,
        "option_submitted": False,
    }


def start_journaller_stress_relief_v1(
    driver, *, expected_revision: int, campaign_root_result: object,
    game_source_root: Path, before_action,
) -> dict:
    """Open one opportunity; return its event plan without choosing an option.

    before_action is the original owner record/display hook, called before each
    UI action. Callback return does not prove actual screen display.
    """
    if getattr(driver, FLAG, False) is not True:
        return {"schema": SCHEMA, "status": "disabled", "queries_performed": 0}
    if not callable(before_action):
        return {"schema": SCHEMA, "status": "decision_display_hook_unavailable"}
    snapshot = _read(driver)
    binding = opening_binding(snapshot)
    hello = snapshot["diagnostics"]["hello"]
    if hello["expected_ck3_version"] != "1.20.0.4":
        raise ValueError("journaller authored knowledge requires exact 1.20.0.4")
    if type(expected_revision) is not int or expected_revision != snapshot.get("revision"):
        raise ValueError("journaller public revision changed")
    if (snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None):
        return {"schema": SCHEMA, "status": "original_player_decision_has_priority"}
    risk = build_ordinary_player_risk_context_v1(snapshot, campaign_root_result)
    stress = risk["stress"]
    if stress["status"] != "available":
        return {"schema": SCHEMA, "status": "same_frame_stress_unavailable"}
    if stress["value"]["points"] < 100:
        return {"schema": SCHEMA, "status": "below_urgent_stress_threshold"}
    parent = driver._native_driver_state_path().parent / "journaller-stress-relief-v1"
    claim = parent / f"{binding['played_character_id']}.claim.json"
    if claim.exists():
        return {"schema": SCHEMA, "status": "actor_attempt_already_claimed_no_replay",
                "claim_path": str(claim)}
    caps = driver.capabilities()
    advertised = caps.get("bridge_capabilities") if isinstance(caps, dict) else None
    if (not isinstance(advertised, list) or not all(isinstance(x, str) for x in advertised)
            or not REQUIRED_CAPS <= set(advertised)):
        return {"schema": SCHEMA, "status": "required_native_capability_unavailable"}
    pins = verify_journaller_sources_v1(game_source_root)

    def display(operation):
        before_action({"policy": SCHEMA, "operation": operation,
                       "reason": "压力已达危机阈值；检查原生记日记资格并保留实际回执",
                       "source_binding": dict(binding), "decision_key": DECISION})
        _same_frame(driver, snapshot)

    display("open_decisions")
    opened = driver.open_ingame_decisions_v1(expected_revision=expected_revision)
    _exact_build(opened.get("native_ack"), snapshot)
    normalize_open_result(opened.get("native_ack"), binding)
    if (opened.get("postcondition_verified") is not True
            or opened.get("verification_pending") is not False
            or not actual_visible_decisions_tree(opened.get("later_decisions_tree"))):
        raise ValueError("journaller Decisions visibility is unproved")
    _same_frame(driver, snapshot)
    model = driver.query_ingame_decision_item_v1(DECISION, expected_revision=expected_revision)
    _exact_build(model, snapshot)
    normalize_decision_item(model, binding, DECISION)
    if model.get("available") is not True:
        return {"schema": SCHEMA, "status": "no_qualified_native_journaller_model",
                "native_open": _receipt_ref(opened), "business_submission": False}
    if model.get("row_scope_reference_available") is not True:
        raise ValueError("journaller original row scope is unavailable")
    _same_frame(driver, snapshot)
    parent.mkdir(parents=True, exist_ok=True)
    claimed = {"schema": SCHEMA, "status": "claimed_result_unknown_no_retry",
               "machine_id": current_machine_id(),
               "observed_at_utc": datetime.now(timezone.utc).isoformat(),
               "binding": binding, "revision": expected_revision,
               "decision_key": DECISION, "starting_stress_points": stress["value"]["points"],
               "source_sha256": pins, "native_open": _receipt_ref(opened),
               "once_scope": "original_driver_state_root_and_full_actor_id"}
    _write_once(claim, claimed)
    # Failure preserves this claim and all original Driver claims; no replay.
    display("select_journaller_decision")
    selected = driver.select_ingame_decision_item_v1(DECISION, expected_revision=expected_revision)
    _same_frame(driver, snapshot)
    selected_model = driver.query_ingame_decision_item_v1(DECISION, expected_revision=expected_revision)
    _exact_build(selected_model, snapshot)
    if (selected.get("postcondition_verified") is not True
            or selected.get("verification_pending") is not False
            or not actual_selected_detail(selected_model, binding, DECISION)):
        raise ValueError("journaller current selected detail/actor is unproved")
    display("confirm_journaller_decision")
    confirmed = driver.confirm_ingame_decision_outcome_v1(
        DECISION, "event_window", expected_event_definition_key=EVENT,
        expected_revision=expected_revision)
    _exact_build(confirmed.get("native_ack"), snapshot)
    ending = _read(driver)
    later = opening_binding(ending)
    if (any(later[key] != binding[key] for key in _CONTROL)
            or ending.get("pending_character_interaction") is not None
            or later["native_revision"] < binding["native_revision"]
            or confirmed.get("postcondition_verified") is not True
            or confirmed.get("verification_pending") is not False
            or confirmed.get("business_effects_verified") is not False):
        raise ValueError("journaller Confirm changed control or overcredited business effects")
    plan = _event_plan(ending, confirmed.get("later_actual_observation"))
    if "select-event-option-1" not in action_step_set(driver.capabilities()):
        raise ValueError("journaller event option is not currently advertised")
    result = {"schema": SCHEMA, "status": "exact_event_observed_choice_pending",
              "machine_id": claimed["machine_id"],
              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "claim_path": str(claim), "event_plan": plan,
              "native_select": _receipt_ref(selected), "native_confirm": _receipt_ref(confirmed),
              "event_choice_verified": False, "stress_reduction_observed": None,
              "health_treatment_credit": False}
    _write_once(claim.with_suffix(".event.json"), result)
    return result


def observe_journaller_choice_v1(handoff: object, choice_receipt: object,
                                current_snapshot: object) -> dict:
    """Separate old-window and measured-stress credit; no query or submission."""
    result = {"schema": SCHEMA, "status": "choice_observation_unavailable",
              "selection_acknowledged": None, "old_event_window_absent": False,
              "active_event_absent": False, "stress_change_observed": False,
              "starting_stress_points": None, "ending_stress_points": None,
              "stress_delta_points": None, "stress_reduction_observed": None,
              "health_treatment_credit": False}
    if (not isinstance(handoff, dict) or handoff.get("schema") != SCHEMA
            or handoff.get("status") != "exact_event_observed_choice_pending"
            or not isinstance(choice_receipt, dict) or not isinstance(current_snapshot, dict)):
        return result
    accepted = choice_receipt.get("accepted")
    result["selection_acknowledged"] = accepted if type(accepted) is bool else None
    plan = handoff.get("event_plan")
    selection = choice_receipt.get("event_selection")
    if (not isinstance(plan, dict) or plan.get("event_definition_key") != EVENT
            or plan.get("source_sha256") != SOURCE_PINS or not isinstance(selection, dict)):
        return result
    before = plan.get("binding")
    if (not isinstance(before, dict) or type(before.get("revision")) is not int
            or not isinstance(before.get("snapshot_id"), str)):
        return result
    try:
        after = opening_binding(current_snapshot)
    except (ValueError, KeyError, TypeError):
        return result
    if current_snapshot["diagnostics"]["hello"]["expected_ck3_version"] != "1.20.0.4":
        return result
    current_event = current_snapshot.get("active_event")
    current_id = current_event.get("instance_id") if isinstance(current_event, dict) else None
    if current_event is not None and (type(current_id) is not int or current_id <= 0):
        return result
    if (any(after[key] != before.get(key) for key in _CONTROL)
            or selection.get("status") != "event_instance_advanced"
            or selection.get("postcondition_verified") is not True
            or selection.get("old_event_instance_id") != plan.get("event_instance_id")
            or selection.get("new_event_instance_id") != current_id
            or current_id == plan.get("event_instance_id")
            or selection.get("selected_option_number") != 1
            or selection.get("selected_native_option_index") != 0
            or type(selection.get("selected_option_number")) is not int
            or type(selection.get("selected_native_option_index")) is not int
            or selection.get("starting_snapshot_id") != before.get("snapshot_id")
            or selection.get("starting_revision") != before.get("revision")
            or selection.get("ending_snapshot_id") != current_snapshot.get("snapshot_id")
            or selection.get("ending_revision") != current_snapshot.get("revision")
            or type(selection.get("ending_revision")) is not int
            or selection["ending_revision"] <= before["revision"]
            or selection.get("episode_run_id") != before.get("episode_run_id")
            or selection.get("connection_generation") != before.get("connection_generation")
            or selection.get("bridge_pid") != before.get("bridge_pid")
            or after["native_revision"] < before.get("native_revision", 0)):
        return result
    result.update(status="old_event_window_advanced", old_event_window_absent=True,
                  active_event_absent=current_event is None)
    first = selection.get("starting_played_character_stress")
    last = selection.get("ending_played_character_stress")
    for value in (first, last):
        if (not isinstance(value, dict) or value.get("status") != "available"
                or value.get("character_id") != before["played_character_id"]
                or type(value.get("stress_points")) is not int
                or not 0 <= value["stress_points"] <= 2**31 - 1):
            return result
    if current_snapshot["played_character"].get("stress_points") != last["stress_points"]:
        return result
    delta = last["stress_points"] - first["stress_points"]
    result.update(status="choice_and_stress_interval_observed", stress_change_observed=True,
                  starting_stress_points=first["stress_points"], ending_stress_points=last["stress_points"],
                  stress_delta_points=delta, stress_reduction_observed=delta < 0)
    return result
