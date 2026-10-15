"""Pure native-choice ordering; no UI input, dispatch or semantic preference."""
from __future__ import annotations

from copy import deepcopy
import json
import math


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _blocking(dto):
    proof = dto.get("blocking_proof")
    if isinstance(proof, dict) and proof.get("verified") is True:
        if proof.get("kind") in ("blocks_simulation", "exclusive_modal_blocks_input"):
            return deepcopy(proof)
    if dto.get("blocks_simulation") is True:
        return {"kind": "blocks_simulation", "verified": True}
    if dto.get("exclusive_modal") is True and dto.get("blocks_input") is True:
        return {"kind": "exclusive_modal_blocks_input", "verified": True}
    return None


def _position(choice):
    bounds = choice.get("bounds")
    if not isinstance(bounds, dict):
        return None
    values = [bounds.get(key) for key in ("top", "left", "width", "height")]
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
        return None
    if values[2] <= 0 or values[3] <= 0:
        return None
    return values[0], values[1]


def _select(dto, expected_frame, *, generic):
    if not isinstance(dto, dict):
        return {"status": "mechanism_unavailable", "reason": "native_choice_DTO_unavailable"}
    evidence = {"frame_binding": deepcopy(dto.get("frame_binding")),
                "window_id": deepcopy(dto.get("window_id")), "window_type": dto.get("window_type"),
                "blocking_proof": _blocking(dto), "choices": deepcopy(dto.get("choices")),
                "excluded": [], "duplicates_removed": [], "sort_order": None,
                "material_effects_verified": False}
    def unavailable(reason, status="mechanism_unavailable"):
        return {"status": status, "selected_choice_id": None, "action_token": None,
                "reason": reason, "evidence": evidence}
    frame = dto.get("frame_binding")
    if not isinstance(frame, dict) or not frame:
        return unavailable("native_frame_binding_unavailable")
    if expected_frame is not None and _canonical(frame) != _canonical(expected_frame):
        return unavailable("native_frame_binding_changed", "stale_frame")
    if generic and _blocking(dto) is None:
        return unavailable("native_simulation_or_exclusive_input_blocking_proof_unavailable", "not_mandatory")
    if generic and dto.get("choices_complete", dto.get("complete")) is not True:
        return unavailable("native_complete_choice_list_unavailable")
    choices = dto.get("choices")
    if not isinstance(choices, list):
        return unavailable("native_choice_list_unavailable")
    unique = {}
    eligible = []
    for index, choice in enumerate(choices):
        if not isinstance(choice, dict):
            evidence["excluded"].append({"index": index, "reason": "not_native_choice_mapping"})
            continue
        identity = choice.get("choice_id")
        if type(identity) not in (str, int) or isinstance(identity, str) and not identity:
            return unavailable("native_choice_identity_unavailable")
        key = _canonical(identity)
        if key in unique:
            if _canonical(unique[key]) != _canonical(choice):
                return unavailable("conflicting_duplicate_native_choice_identity")
            evidence["duplicates_removed"].append({"index": index, "choice_id": identity})
            continue
        unique[key] = choice
        reason = ("invisible" if choice.get("visible") is not True else
                  "disabled" if choice.get("enabled") is not True else
                  "nonchoice" if choice.get("is_choice") is not True else
                  "nonchoice_role" if choice.get("role") in ("close", "close_x", "window_close", "decoration", "hud", "navigation") else None)
        if reason:
            evidence["excluded"].append({"index": index, "choice_id": identity, "reason": reason})
        else:
            eligible.append(choice)
    if not eligible:
        return unavailable("no_visible_enabled_native_choice")
    if len(eligible) == 1:
        ordered = eligible
        evidence["sort_order"] = "single_visible_enabled_native_choice_no_geometry_needed"
    elif all(_position(choice) is not None for choice in eligible):
        ordered = sorted(eligible, key=lambda choice: (*_position(choice),
            choice.get("rendered_index") if type(choice.get("rendered_index")) is int else 2**63,
            _canonical(choice["choice_id"])))
        evidence["sort_order"] = "native_bounds_top_then_left"
    else:
        proof = dto.get("presentation_order_proof")
        allowed = not generic and isinstance(proof, dict) and proof.get("kind") in (
            "native_event_rendered_order", "source_bound_stock_interaction_GUI_order")
        indices = [choice.get("rendered_index") for choice in eligible]
        if not allowed or any(type(index) is not int or index < 0 for index in indices) or len(set(indices)) != len(indices):
            return unavailable("native_choice_geometry_or_authorized_presentation_order_unavailable")
        ordered = sorted(eligible, key=lambda choice: choice["rendered_index"])
        evidence["sort_order"] = proof["kind"]
    chosen = ordered[0]
    evidence["ordered_eligible_choice_ids"] = [choice["choice_id"] for choice in ordered]
    native = chosen.get("native_index")
    if native is not None and (type(native) is not int or native < 0):
        return unavailable("native_option_index_invalid")
    token = chosen.get("action_token")
    existing = chosen.get("existing_typed_action")
    if not (isinstance(token, str) and token) and not (not generic and isinstance(existing, dict) and existing.get("available") is True):
        return unavailable("selected_native_choice_action_unavailable")
    return {"status": "recommended", "selected_choice_id": chosen["choice_id"],
            "action_token": deepcopy(token), "selected_choice": deepcopy(chosen),
            "native_index": native, "public_option_number": native + 1 if native is not None else None,
            "reason": "Select the first visible enabled native choice by " + evidence["sort_order"] + "; label semantics do not block the user's continuation policy.",
            "frame_binding": deepcopy(frame), "window_id": deepcopy(dto.get("window_id")),
            "evidence": evidence, "semantic_optimal": False, "material_effects_verified": False}


def select_unknown_mandatory_choice_v1(dto, *, expected_frame=None):
    """Consume authoritative Native blocking/choice/action evidence only."""
    return _select(dto, expected_frame, generic=True)


def select_existing_native_choice_v1(dto, *, expected_frame=None):
    """Existing event/interaction authorization does not invent mandatory proof."""
    if not isinstance(dto, dict) or dto.get("window_type") not in ("event", "pending_character_interaction"):
        return {"status": "mechanism_unavailable", "reason": "existing_native_domain_not_authorized"}
    return _select(dto, expected_frame, generic=False)
