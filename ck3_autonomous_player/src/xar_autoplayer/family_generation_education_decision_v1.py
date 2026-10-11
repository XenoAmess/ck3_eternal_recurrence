"""Compose current child reads into independent stock education decision inputs.

The supplied descendants have already passed the registered family validator.
Five explicit SKILL projections reuse stock childhood triggers and point terms.
This module acquires nothing and does not select a guardian or an educator.
"""
from __future__ import annotations

from copy import deepcopy

from .family_generation_education_inputs_v1 import (
    derive_family_generation_education_inputs_v1,
)
from .bridge.education_point_source_modifiers_12004 import (
    compute_education_point_source_modifiers_12004,
    education_point_inputs_from_child_row_12004,
)


SCHEMA = "family_generation_education_decision_inputs_v1"
_CHILDHOOD_TRAITS = ("curious", "rowdy", "bossy", "pensive", "charming")
# Literal 00_education_triggers.txt:195-248. Each entry names an explicit
# education SKILL parameter; it does not assert a selected native effect scope.
_SKILLS = (
    ("diplomacy", ("charming", "curious"), "bossy"),
    ("martial", ("rowdy", "bossy"), "curious"),
    ("stewardship", ("bossy", "pensive"), "charming"),
    ("intrigue", ("charming", "rowdy"), "pensive"),
    ("learning", ("pensive", "curious"), "rowdy"),
)
_EDUCATION_KEYS = {"education_" + skill for skill, _, _ in _SKILLS}


def _childhood_predicates(row: dict[str, object]) -> dict[str, bool] | None:
    leaf = row.get("childhood_traits")
    if not isinstance(leaf, dict) or leaf.get("status") != "available":
        return None
    # The caller's strict validator has established the source, fixed queried
    # keys and canonical subset. An empty observed subset is five known false.
    return {key: key in leaf["present_trait_keys"] for key in _CHILDHOOD_TRAITS}


def _current_focus(row: dict[str, object]) -> dict[str, object]:
    leaf = row.get("native_focus")
    if not isinstance(leaf, dict) or leaf.get("status") != "available":
        return {
            "available": False,
            "unavailable_reason": (
                leaf.get("unavailable_reason") if isinstance(leaf, dict)
                else "native_focus_not_observed"),
            "presence": None, "key": None, "known_null": None,
            "has_education_focus": None,
        }
    presence, key = leaf["presence"], leaf["key"]
    return {
        "available": True, "unavailable_reason": None,
        "presence": presence, "key": key,
        "known_null": presence == "absent",
        "has_education_focus": presence == "present" and key in _EDUCATION_KEYS,
    }


def _current_court_owner(row: dict[str, object], native_revision: int) -> dict[str, object]:
    from .education_child_court_owner_readonly_12004 import (
        child_court_owner_from_current_child_source_12004,
    )
    source = row.get("court_owner_source")
    observed = child_court_owner_from_current_child_source_12004(
        row["raw_character_id"], source, native_revision=native_revision,
    )
    return {
        "available": observed.available,
        "source_qualified": observed.source_qualified,
        "present": observed.owner_id is not None if observed.available else None,
        "known_null": observed.owner_id is None if observed.available else None,
        "owner_character_id_raw": observed.owner_id,
        "basis": "current_child_native_court_owner_source_projection",
        "unavailable_reason": None if observed.available else (
            source.get("unavailable_reason") or "court_owner_source_unavailable"
            if isinstance(source, dict) else "court_owner_source_not_observed"),
    }


def derive_family_generation_education_decision_inputs_v1(
    descendants: dict[str, object] | None,
) -> dict[str, object]:
    """Keep known-null focus and child trait terms useful independently.

    A source-complete household with no living actual child stays known empty.
    A present noneducation focus remains present under its exact native key.
    Missing focus never suppresses an available per-SKILL childhood projection.
    Missing educator facts leave only their reached source terms unavailable.
    """
    generation = derive_family_generation_education_inputs_v1(descendants)
    rows: list[dict[str, object]] = []
    for child in generation["rows"]:
        traits = _childhood_predicates(child)
        focus = _current_focus(child)
        options: list[dict[str, object]] = []
        for skill, positive, negative in _SKILLS:
            affinity = (None if traits is None else any(traits[key] for key in positive))
            disaffinity = None if traits is None else traits[negative]
            inputs = education_point_inputs_from_child_row_12004(
                child, focus_affinity=affinity, focus_disaffinity=disaffinity,
            )
            options.append({
                "skill_parameter": skill, "focus_key": "education_" + skill,
                "childhood_affinity": {
                    "available": affinity is not None, "raw_value": affinity,
                    "basis": "stock_childhood_trait_trigger_source_projection",
                    "required_any_trait_keys": list(positive),
                },
                "childhood_disaffinity": {
                    "available": disaffinity is not None, "raw_value": disaffinity,
                    "basis": "stock_childhood_trait_trigger_source_projection",
                    "required_trait_key": negative,
                },
                "source_point_components": compute_education_point_source_modifiers_12004(inputs),
            })
        current_option = next((option for option in options
                               if focus["available"] and option["focus_key"] == focus["key"]), None)
        rows.append({
            "character_id": child["character_id"],
            "raw_character_id": child["raw_character_id"],
            "occurrence_indices": list(child["occurrence_indices"]),
            "current_focus": focus,
            "current_court_owner": _current_court_owner(
                child, generation["frame"]["native_revision"],
            ),
            "stock_skill_options": options,
            "current_education_skill_inputs": deepcopy(current_option),
        })
    return {
        "schema": SCHEMA,
        "qualification": "current_native_child_inputs_and_stock_source_projection",
        "frame": deepcopy(generation["frame"]),
        "roster_complete": generation["roster_complete"],
        "living_child_classification_complete": generation["living_child_classification_complete"],
        "living_actual_child_exists": generation["living_actual_child_exists"],
        "living_actual_child_count": generation["living_actual_child_count"],
        "known_empty": generation["known_empty"],
        "children": generation,
        "education_rows": rows,
        "source_projection_only": True,
        "native_effect_invoked": False,
        "guardian_role_equivalence_qualified": False,
        "educator_selection_observed": False,
        "education_outcome_observed": False,
    }
