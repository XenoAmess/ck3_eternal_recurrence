"""Keep each current child's education facts useful to the existing planner.

Inputs have passed the existing family or ordinary-interaction validators.
Focus absence describes focus management. Native final secondary roles name
a request candidate; generic relation materials retain their narrower meaning.
"""
from __future__ import annotations

from copy import deepcopy


SCHEMA = "family_education_needs_12004"


def _focus_management(focus: dict[str, object]) -> dict[str, object]:
    if focus.get("available") is not True:
        return {
            "available": False, "state": "unknown", "current_key": None,
            "focus_absent": None, "education_focus_present": None,
            "unavailable_reason": focus.get("unavailable_reason"),
        }
    absent = focus["presence"] == "absent"
    education = focus["has_education_focus"]
    return {
        "available": True,
        "state": ("known_absent" if absent else "education_focus_present"
                  if education else "other_focus_present"),
        "current_key": focus["key"], "focus_absent": absent,
        "education_focus_present": education, "unavailable_reason": None,
    }


def _child_materials(child_id: int, source: dict[str, object] | None) -> dict[str, object]:
    # The optional source belongs to the same validated family command. It has
    # no standalone frame: a caller must not rebind another command's sidecar.
    if source is None:
        return {"observed": False, "collection_available": False,
                "observation": None, "unavailable_reason": "child_relation_materials_not_observed"}
    collected = source["collection_available"]
    observation = next((row for row in source["rows"]
                        if row["child_character_id"] == child_id), None) if collected else None
    return {
        "observed": True, "collection_available": collected,
        "observation": deepcopy(observation),
        "unavailable_reason": (None if observation is not None else
                               source["unavailable_reason"] or "child_material_row_not_observed"),
    }


def derive_family_education_needs_12004(
    inputs: dict[str, object] | None, *,
    child_relation_materials: dict[str, object] | None = None,
) -> dict[str, object]:
    """Project observed focus states and missing reads without suppressing rows.

    ``inputs`` is family_generation_education_decision_inputs_v1. Optional
    materials are the strict same-family-command current_child_relation_materials_v1.
    The existing living-child order and full occurrence groups remain unchanged.
    A partial child, known focus absence, noneducation focus or unknown focus
    all remain candidates for the planner's existing native request query.
    """
    result: dict[str, object] = {
        "schema": SCHEMA, "source": "current_family_education_observed_inputs",
        "frame": None, "roster_complete": False,
        "living_child_classification_complete": False,
        "known_empty": None, "rows": [], "source_projection_only": True,
    }
    if inputs is None:
        return result
    result.update({key: deepcopy(inputs[key]) for key in (
        "frame", "roster_complete", "living_child_classification_complete", "known_empty",
    )})
    decisions = {row["raw_character_id"]: row for row in inputs["education_rows"]}
    for child in inputs["children"]["rows"]:
        decision = decisions[child["raw_character_id"]]
        availability = child["leaf_availability"]
        result["rows"].append({
            "character_id": child["character_id"],
            "raw_character_id": child["raw_character_id"],
            "occurrence_indices": list(child["occurrence_indices"]),
            "frame": deepcopy(inputs["frame"]),
            "focus_management": _focus_management(decision["current_focus"]),
            "leaf_availability": deepcopy(availability),
            "missing_observations": [key for key, value in availability.items()
                                     if value["status"] != "available"],
            "values": deepcopy(child["values"]),
            "childhood_traits": deepcopy(child["childhood_traits"]),
            "education_point_traits": deepcopy(child["education_point_traits"]),
            "stock_skill_options": deepcopy(decision["stock_skill_options"]),
            "current_education_skill_inputs": deepcopy(decision["current_education_skill_inputs"]),
            "current_court_owner": deepcopy(decision["current_court_owner"]),
            "relation_materials": _child_materials(child["raw_character_id"], child_relation_materials),
        })
    return result


def project_family_education_request_candidate_12004(
    needs_row: dict[str, object], normalized_ordinary_context: dict[str, object],
) -> dict[str, object]:
    """Retain the native evaluated pair independently of CanSend and send readiness.

    The caller passes the existing strict ordinary context from its default or
    explicit-request query. The original recipient may redirect; only the final
    secondary_recipient binds the ward. This candidate does not claim an assigned
    guardian, HasGuardian value or the stock effect's saved educator scope.
    """
    context = normalized_ordinary_context
    child_id = needs_row["raw_character_id"]
    observed = (context["status"] == "available"
                and context["interaction_key"] == "educate_child_interaction")
    roles = context["effective_roles"]
    matches = roles["secondary_recipient_id"] == child_id if observed else None
    guardian = roles["secondary_actor_id"] if observed else None
    available = matches is True and guardian is not None
    return {
        "available": available, "role_observation_available": observed,
        "pair_matches_child": matches, "child_full_id": child_id,
        "guardian_full_id": guardian if available else None,
        "guardian_role_known_null": guardian is None if observed else None,
        "roles": deepcopy(roles),
        "frame": {key: deepcopy(context[key]) for key in (
            "snapshot_revision", "date_raw", "player_character_id",
            "game_pid", "connection_generation",
        )},
        "can_send": context["can_send"],
        "ready_to_initiate": context["ready_to_initiate"],
        "basis": "native_final_secondary_actor_and_secondary_recipient" if available else "",
        "unavailable_reason": (None if available else
                               "ordinary_context_not_education" if context["interaction_key"] != "educate_child_interaction"
                               else context["unavailable_reason"]
                               if not observed else "native_secondary_recipient_differs_from_child"
                               if matches is False else "native_secondary_actor_known_null"),
    }
