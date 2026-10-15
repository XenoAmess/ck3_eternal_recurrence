"""Pure priority plan for an observed, Native-proved exclusive choice window."""

from __future__ import annotations

import copy

from .mandatory_choice_evidence_v1 import SCHEMA as EVIDENCE_SCHEMA
from .mandatory_choice_policy_v1 import select_unknown_mandatory_choice_v1


QUERY_STEP = "query-mandatory-choice-v1"
SELECT_STEP = "select-mandatory-choice-v1"
QUERY_CAPABILITY = "game.state.native-mandatory-choice-window-v1"
HINT_SOURCES = {
    "application_main_pump_observed_modal_receiver",
}
EVENT_ROOT_RELATION_SOURCE = "exact_12004_event_controller_gui_root_and_owner_tree"


def _independent_top_modal_over_event(dto: dict, hint: dict, event: dict) -> bool:
    """Require Native's exact GUI-root relation before overriding typed events."""
    relation = dto.get("typed_window_relation")
    instance_id = event.get("instance_id")
    return (
        type(instance_id) is int and instance_id > 0
        and isinstance(relation, dict)
        and relation.get("status") == "independent_top_modal"
        and relation.get("owner_verified") is True
        and relation.get("source") == EVENT_ROOT_RELATION_SOURCE
        and relation.get("typed_domain") == "event"
        and relation.get("typed_window_instance_id") == instance_id
        and relation.get("top_opaque_root_id") == hint.get("opaque_root_id")
        and relation.get("top_opaque_root_id") == dto.get("window_instance_id")
        and relation.get("typed_opaque_root_id") != relation.get("top_opaque_root_id")
        and isinstance(relation.get("typed_opaque_root_id"), str)
        and bool(relation["typed_opaque_root_id"])
    )


def _same_typed_event_root_after_unavailable(
    dto: dict, hint: dict, event: dict, context: dict | None,
) -> bool:
    """Use Native buttons only after this very event's typed read failed.

    A saved-scope failure gives no enabled option catalogue, but the separate
    exact Native top-root query can. A materialized typed event retains its
    existing selector.
    """
    relation = dto.get("typed_window_relation")
    instance_id = event.get("instance_id")
    return (
        isinstance(context, dict) and context.get("status") == "unavailable"
        and context.get("current_event_instance_id") == instance_id
        and type(instance_id) is int and instance_id > 0
        and isinstance(relation, dict)
        and relation.get("status") == "same_typed_root"
        and relation.get("owner_verified") is True
        and relation.get("source") == EVENT_ROOT_RELATION_SOURCE
        and relation.get("typed_domain") == "event"
        and relation.get("typed_window_instance_id") == instance_id
        and relation.get("top_opaque_root_id") == hint.get("opaque_root_id")
        and relation.get("top_opaque_root_id") == dto.get("window_instance_id")
        and relation.get("typed_opaque_root_id") == relation.get("top_opaque_root_id")
    )


def _frame(snapshot: dict) -> dict | None:
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(played, dict) or not isinstance(diagnostics, dict):
        return None
    frame = {"game_pid": diagnostics.get("bridge_pid"),
             "connection_generation": diagnostics.get("connection_generation"),
             "revision": snapshot.get("revision"),
             "native_revision": snapshot.get("native_revision"),
             "date_raw": snapshot.get("date_raw"),
             "actor_character_id": played.get("character_id"),
             "episode_run_id": snapshot.get("episode_run_id"),
             "snapshot_id": snapshot.get("snapshot_id")}
    if (any(type(frame[key]) is not int or frame[key] < 1 for key in (
            "game_pid", "connection_generation", "native_revision", "actor_character_id"))
            or type(frame["revision"]) is not int or frame["revision"] < 0
            or type(frame["date_raw"]) is not int
            or not isinstance(frame["episode_run_id"], str) or not frame["episode_run_id"]
            or not isinstance(frame["snapshot_id"], str) or not frame["snapshot_id"]):
        return None
    return frame


def _query_result(commands: list[dict], frame: dict) -> dict | None:
    """Only a successful read from this exact public and Native frame counts."""
    for row in reversed(commands):
        if not isinstance(row, dict):
            continue
        command = row.get("command")
        result = row.get("result")
        if command == "auto-turn" and isinstance(result, dict):
            auto = result.get("auto_turn")
            command = auto.get("selected_step") if isinstance(auto, dict) else None
            nested = auto.get("result") if isinstance(auto, dict) else None
            if isinstance(nested, dict):
                result = nested
        if command != QUERY_STEP:
            continue
        if row.get("ok") is not True or not isinstance(result, dict):
            return {"status": "failed_read", "row": row}
        if (result.get("queried_snapshot_id") == frame["snapshot_id"]
                and result.get("queried_revision") == frame["revision"]
                and result.get("queried_native_revision") == frame["native_revision"]):
            return {"status": "same_frame", "result": result}
        return None
    return None


def _latest_select(commands: list[dict], frame: dict) -> dict | None:
    """Find the latest submitted generic token in this actual game episode."""
    for row in reversed(commands):
        if not isinstance(row, dict) or row.get("ok") is not True:
            continue
        result = row.get("result")
        if row.get("command") == "auto-turn" and isinstance(result, dict):
            result = result.get("auto_turn")
        if not isinstance(result, dict) or result.get("selected_step") != SELECT_STEP:
            continue
        plan = result.get("plan")
        capture = plan.get("unknown_mandatory_choice_v1") if isinstance(plan, dict) else None
        source = capture.get("frame_binding") if isinstance(capture, dict) else None
        if not isinstance(source, dict) or any(
            source.get(key) != frame[key] for key in (
                "game_pid", "actor_character_id", "episode_run_id")
        ):
            continue
        return result
    return None


def plan_native_mandatory_choice_v1(
    commands: list[dict], *, snapshot: dict | None,
    action_steps=(), bridge_capabilities=(),
    known_review_root=None, backend_sha256=None,
) -> dict | None:
    """Return None unless Native says the current top window captures input.

    Existing terminal/war-window routing calls this only after its priority
    checks. Existing event and interaction typed routes keep their priority.
    """
    if not isinstance(snapshot, dict):
        return None
    event = snapshot.get("active_event")
    if isinstance(snapshot.get("pending_character_interaction"), dict):
        return None
    hint = snapshot.get("top_exclusive_modal_choice_hint")
    if (not isinstance(hint, dict) or hint.get("status") != "present"
            or hint.get("source") not in HINT_SOURCES
            or hint.get("owner_verified") is not True
            or hint.get("max_observation_age_ms") != 2000
            or not isinstance(hint.get("opaque_root_id"), str)
            or not hint["opaque_root_id"]):
        return None
    frame = _frame(snapshot)
    if frame is None:
        if isinstance(event, dict):
            return None
        return {"policy": "native-mandatory-choice-v1",
                "phase": "unknown_mandatory_choice_frame_unavailable",
                "selected_step": None, "reason": "Native top modal hint lacks a complete current owner frame",
                "top_exclusive_modal_choice_hint": copy.deepcopy(hint)}
    steps, capabilities = set(action_steps), set(bridge_capabilities)
    if not (QUERY_STEP in steps and QUERY_CAPABILITY in capabilities):
        if isinstance(event, dict):
            return None
        return {"policy": "native-mandatory-choice-v1",
                "phase": "unknown_mandatory_choice_mechanism_unavailable",
                "selected_step": None, "reason": "Native did not advertise both typed query and token action",
                 "required_public_step": QUERY_STEP,
                 "required_typed_method": "select_mandatory_choice_v1",
                "required_capability": QUERY_CAPABILITY,
                "top_exclusive_modal_choice_hint": copy.deepcopy(hint)}
    observed = _query_result(commands, frame)
    if observed is None:
        return {"policy": "native-mandatory-choice-v1",
                "phase": "unknown_mandatory_choice_query",
                "selected_step": QUERY_STEP,
                "reason": "Read the complete current top exclusive modal choice catalogue before selecting",
                "top_exclusive_modal_choice_hint": copy.deepcopy(hint)}
    if observed["status"] != "same_frame":
        if isinstance(event, dict):
            return None
        return {"policy": "native-mandatory-choice-v1",
                "phase": "unknown_mandatory_choice_query_failed",
                "selected_step": None,
                "reason": "The current typed query failed; do not repeat it or guess a button",
                "query_observation": copy.deepcopy(observed)}
    result = observed["result"]
    dto = result.get("mandatory_choice")
    if (result.get("step") != QUERY_STEP or result.get("accepted") is not True
            or not isinstance(dto, dict) or dto.get("schema") != "xar.native-mandatory-choice-window/v1"
            or dto.get("frame_binding") != frame
            or not isinstance(dto.get("query_id"), str) or not dto["query_id"]
            or not isinstance(dto.get("window_instance_id"), (str, int))):
        if isinstance(event, dict):
            return None
        return {"policy": "native-mandatory-choice-v1",
                "phase": "unknown_mandatory_choice_query_malformed",
                "selected_step": None,
                "reason": "Typed query lacks exact source frame, window instance or query ID",
                "query_observation": copy.deepcopy(result)}
    typed_event_fallback = False
    typed_event_context = None
    if isinstance(event, dict):
        independent = _independent_top_modal_over_event(dto, hint, event)
        from .strategy import _same_frame_event_window_context

        typed_event_context = _same_frame_event_window_context(commands, snapshot)
        typed_event_fallback = _same_typed_event_root_after_unavailable(
            dto, hint, event, typed_event_context)
        if not independent and not typed_event_fallback:
            return None
    previous = _latest_select(commands, frame)
    if isinstance(previous, dict) and previous.get("status") == "pending":
        previous_plan = previous.get("plan")
        previous_capture = (previous_plan.get("unknown_mandatory_choice_v1")
                            if isinstance(previous_plan, dict) else None)
        old_window = (previous_capture.get("native_window")
                      if isinstance(previous_capture, dict) else None)
        if (isinstance(old_window, dict)
                and old_window.get("window_id") == dto.get("window_id")
                and old_window.get("window_instance_id") == dto.get("window_instance_id")):
            return {"policy": "native-mandatory-choice-v1",
                    "phase": "unknown_mandatory_choice_pending_verification",
                    "selected_step": None,
                    "reason": "The same blocking Native instance remains after a submitted token; do not dispatch another",
                    "pending_token_result": copy.deepcopy(previous.get("result")),
                    "current_query_observation": copy.deepcopy(result)}
    decision = select_unknown_mandatory_choice_v1(dto, expected_frame=frame)
    if decision.get("status") != "recommended":
        return {"policy": "native-mandatory-choice-v1",
                "phase": "unknown_mandatory_choice_unavailable",
                "selected_step": None,
                "reason": decision.get("reason"),
                "mandatory_choice_decision": decision}
    choice = decision["selected_choice"]
    known_ui = None
    if known_review_root is not None and backend_sha256 is not None:
        from .mandatory_choice_offline_analysis_v1 import lookup_observed_ui_recovery
        known_ui = lookup_observed_ui_recovery(
            dto, backend_sha256=backend_sha256,
            review_root=known_review_root)
    capture = {"schema": EVIDENCE_SCHEMA, "native_window": copy.deepcopy(dto),
               "frame_binding": copy.deepcopy(frame),
               "blocking_proof_verified": True, "catalogue_complete": True,
               "native_query_receipt": copy.deepcopy(result),
               "selector_decision": copy.deepcopy(decision),
               "selection": {"selected_step": SELECT_STEP,
                             "choice_id": decision["selected_choice_id"],
                             "action_token": decision["action_token"],
                             "query_id": dto["query_id"],
                             "window_instance_id": dto["window_instance_id"],
                             "native_index": decision.get("native_index"),
                             "bounds": copy.deepcopy(choice.get("bounds"))},
               "known_ui_recovery_source": copy.deepcopy(known_ui),
               "semantic_optimal": False, "material_effects_verified": False,
               "typed_event_unavailable_same_root_fallback": typed_event_fallback,
               "typed_event_unavailable_context": (
                   copy.deepcopy(typed_event_context) if typed_event_fallback else None)}
    return {"policy": "native-mandatory-choice-v1",
            "phase": ("known_observed_ui_recovery_first_enabled" if known_ui
                      else "unknown_mandatory_choice_first_enabled"),
            "selected_step": SELECT_STEP,
            "reason": decision["reason"],
            "unknown_mandatory_choice_v1": capture,
            "known_ui_recovery_source": copy.deepcopy(known_ui),
            "mandatory_choice_decision": decision}
