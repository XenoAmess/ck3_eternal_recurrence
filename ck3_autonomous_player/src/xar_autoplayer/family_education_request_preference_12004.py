"""Order finite observed education requests using an explicit source preference.

This explicit request preference retains its 2/5 focus and 1/5 learning
weights. Martial focus consumes the separately validated native total callback;
other skills retain their raw observations. This does not replay the education
expression, select an effect educator or predict native AI willingness/outcome.
"""
from __future__ import annotations

from copy import deepcopy


POLICY = "source_informed_request_guardian_skill_preference_12004.v2"
_FOCUS_SKILLS = {
    "education_diplomacy": "diplomacy", "education_martial": "martial",
    "education_stewardship": "stewardship", "education_intrigue": "intrigue",
    "education_learning": "learning",
}


_RAW_SKILL_BASIS = "raw_skill_observation"
_TOTAL_MARTIAL_BASIS = "native_character_total_skill_callback"


def _component(
    field: dict[str, object] | None, weight: int, reason: str, *,
    source_basis: str = _RAW_SKILL_BASIS,
) -> dict[str, object]:
    available = isinstance(field, dict) and field["available"] is True
    raw = field["value"] if available else None
    return {
        "available": available, "raw_value": raw, "source_basis": source_basis,
        "weight": {"numerator": weight, "denominator": 5},
        "weighted_numerator": weight * raw if available else None,
        "unavailable_reason": None if available else field["unavailable_reason"]
                              if isinstance(field, dict) else reason,
    }


def _focus_component(
    profile: dict[str, object] | None, skills: dict[str, object] | None,
    skill_key: str | None, bound: bool, guardian_full_id: int,
) -> dict[str, object]:
    # The original ordinary-context validator owns the exact build, role and
    # revision proof. The caller additionally bound profile to this intent.
    if skill_key == "martial":
        total = profile.get("total_martial_callback_v1") if bound else None
        same_target = (isinstance(total, dict)
                       and total.get("source") == _TOTAL_MARTIAL_BASIS
                       and type(total.get("target_character_id")) is int
                       and total["target_character_id"] == guardian_full_id)
        reason = ("request_guardian_profile_identity_unavailable" if not bound
                  else "request_guardian_total_martial_callback_not_observed")
        # No raw-prefix fallback: an absent total observation remains unknown.
        return _component(total if same_target else None, 2, reason,
                          source_basis=_TOTAL_MARTIAL_BASIS)
    return _component(
        skills[skill_key] if skills is not None and skill_key is not None else None,
        2, "request_guardian_profile_identity_unavailable" if not bound
        else "current_child_education_focus_not_observed",
    )


def order_family_education_request_candidates_12004(
    observations: list[dict[str, object]],
) -> dict[str, object]:
    """Compare equal observed component sets and preserve other original slots.

    The caller has already preserved every default query and its native false
    result. Only its existing complete pair/key intents are ordered here. An
    unknown operand stays unknown and never removes an intent from attempts.
    The focus source and guardian query keep their separate source frames.
    """
    candidates = []
    groups: dict[tuple[bool, bool, str, str], list[dict[str, object]]] = {}
    for index, observation in enumerate(observations):
        intent = observation.get("default_request_intent")
        if intent is None:
            continue
        needs = observation["needs"]
        candidate = observation["candidate"]
        context = observation["default_query"]["character_interaction_ordinary_context"]
        profile = context.get("request_guardian_skill_inputs_v1")
        bound = isinstance(profile, dict) and profile["binding_status"] == "resolved" and all(
            type(profile[key]) is type(expected) and profile[key] == expected
            for key, expected in (
                ("child_character_id", intent["child_full_id"]),
                ("character_id", intent["guardian_full_id"]),
                ("owning_native_revision", context["snapshot_revision"]),
            )
        )
        skills = profile["skills"] if bound else None
        focus = needs["focus_management"]
        skill_key = (_FOCUS_SKILLS.get(focus["current_key"])
                     if focus["state"] == "education_focus_present" else None)
        focused = _focus_component(profile, skills, skill_key, bound, intent["guardian_full_id"])
        learning = _component(skills["learning"] if skills is not None else None,
                              1, "request_guardian_profile_identity_unavailable")
        components = {"focus": focused, "learning": learning}
        numerators = [field["weighted_numerator"] for field in components.values()
                      if field["available"]]
        known_score = {"numerator": sum(numerators), "denominator": 5} if numerators else None
        signature = (focused["available"], learning["available"],
                     focused["source_basis"], learning["source_basis"])
        occurrences = needs["occurrence_indices"]
        record = {
            "observation_index": index, "child_full_id": intent["child_full_id"],
            "guardian_full_id": intent["guardian_full_id"],
            "first_occurrence_index": occurrences[0],
            "request_profile_identity_bound": bound,
            "focus_key": focus["current_key"], "focus_management": deepcopy(focus),
            "focus_source_frame": deepcopy(needs["frame"]),
            "guardian_query_frame": deepcopy(candidate["frame"]),
            "raw_request_guardian_profile": deepcopy(profile),
            "components": components, "known_weighted_score": known_score,
            "complete_weighted_score": deepcopy(known_score) if all(signature[:2]) else None,
            "availability": {"focus": signature[0], "learning": signature[1]},
        }
        candidates.append(record)
        groups.setdefault(signature, []).append(record)

    ordered_groups = {}
    for signature, records in groups.items():
        def tie(record):
            return (record["first_occurrence_index"], record["child_full_id"],
                    record["guardian_full_id"], record["observation_index"])
        if any(signature[:2]):
            records = sorted(records, key=lambda record: (
                -record["known_weighted_score"]["numerator"], *tie(record)))
        else:
            records = sorted(records, key=tie)
        ordered_groups[signature] = iter(records)
    ordered = [next(ordered_groups[(record["availability"]["focus"],
                                    record["availability"]["learning"],
                                    record["components"]["focus"]["source_basis"],
                                    record["components"]["learning"]["source_basis"])])
               for record in candidates]
    return {
        "schema": "family_education_request_preference_12004", "policy": POLICY,
        "qualification": "explicit_source_informed_request_preference",
        "comparison": "descending known weighted numerator within identical availability and operand sources; other source/availability slots keep original occurrence order",
        "tie": "original occurrence, full child ID, full guardian ID, original observation index",
        "candidates": candidates,
        "ordered_observation_indices": [record["observation_index"] for record in ordered],
        "unknown_operands_substituted": False, "native_ai_replay": False,
        "effect_educator_selection_observed": False, "education_outcome_predicted": False,
    }
