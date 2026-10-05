"""Consume current Combat geometry without constructing a contact preview.

Inputs are an existing normalized actual battle frame and its observed build.
The retained holding byte is used directly; no current holder predicate runs.
"""

from __future__ import annotations

import copy
from typing import Mapping


EXACT_GAME_VERSION = "1.20.0.3"
EXACT_EXECUTABLE_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
_CROSSING_BY_RETAINED_KIND = {0: "none", 1: "strait", 2: "river", 3: "large_river"}


def retained_constructor_geometry_fields(
    snapshot: Mapping[str, object], build_source: object,
) -> dict[str, object]:
    """Add the diagnostic only when the original optional leaf is present.

    This independent ready flag covers geometry operands, not constructor
    effects, historical participants, initial advantage or a future battle.
    """
    if "actual_geography_v1" not in snapshot:
        return {}
    build = build_source if isinstance(build_source, Mapping) else {}
    sha = build.get("executable_sha256")
    exact_build = (
        build.get("game_version") == EXACT_GAME_VERSION
        and isinstance(sha, str) and sha.lower() == EXACT_EXECUTABLE_SHA256
    )
    is_control = snapshot.get("contract_stage") == "production_exact_ongoing_combat"
    is_transition = snapshot.get("contract_stage") == "production_exact_combat_lifecycle"
    actual = snapshot.get("status") == "available" and (is_control or is_transition)
    missing: list[str] = []
    if not exact_build:
        missing.append("exact_1_20_0_3_build_binding")
    if not actual:
        missing.append("available_actual_combat_frame")
    sides: list[dict[str, object]] = []
    if actual:
        for side_index, role in enumerate(("attacker", "defender")):
            side = {
                "side_index": side_index,
                "role": role,
                "public_cunit_ids_in_stored_order": (
                    [row["public_cunit_id"] for row in snapshot[role]["ordered_armies"]]
                    if is_control else list(snapshot[f"{role}_public_cunit_ids_in_stored_order"])
                ),
                "source": "actual_combat_side_stored_order",
            }
            if is_control:
                side["primary_participant_character_id"] = snapshot[role]["primary_participant_character_id"]
                side["primary_source"] = "actual_combat_side_70"
            sides.append(side)
    geometry = snapshot.get("actual_geography_v1")
    terrain = None
    raw_kind = None
    holding = None
    if geometry is None:
        missing.append("actual_geography_v1")
    else:
        terrain = copy.deepcopy(geometry["terrain"])
        raw_kind = geometry["constructor_adjacency_kind_raw"]
        holding = geometry["holding_defender"]
        if terrain["status"] != "available":
            missing.append("actual_terrain")
        if raw_kind is None:
            missing.append("retained_constructor_adjacency_kind")
        elif raw_kind not in _CROSSING_BY_RETAINED_KIND:
            missing.append("supported_retained_constructor_kind_0_to_3")
        if holding is None:
            missing.append("retained_holding_defender")
    crossing = _CROSSING_BY_RETAINED_KIND.get(raw_kind)
    effects = copy.deepcopy(geometry.get("constructor_rule_effects_v1")) if geometry is not None else None
    effects_ready = bool(exact_build and actual and crossing is not None
                         and holding is not None and effects is not None
                         and effects["status"] == "available")
    current_context = copy.deepcopy(geometry.get("current_rule_context_v1")) if geometry is not None else None
    # These are the closed constructor's rule slots, not captured effect values.
    # Commander exclusions, scale modifiers and initial contexts stay separate.
    rule_plan = None
    if exact_build and actual and crossing is not None and holding is not None:
        rule_plan = {
            "attacker_adjacency": {"side_index": 0, "rules_pointer_offset": 0xF70 + 8 * raw_kind},
            "defender_adjacency": {"side_index": 1, "rules_pointer_offset": 0xFA0 + 8 * raw_kind},
            "holding_defender": {
                "side_index": 1, "rules_pointer_offset": 0xF10,
                "enabled": holding, "predicate_source": "retained_combat_6FE",
            },
            "effect_values_observed": effects_ready,
            "commander_exclusion_and_scale_inputs_observed": False,
        }
    diagnostic = {
        "schema_version": 1,
        "status": "available" if not missing else "unavailable",
        "retained_geometry_ready": not missing,
        "geometry_mode": "actual_current_combat_retained_constructor_inputs",
        "source": {
            "game_version": build.get("game_version"),
            "executable_sha256": sha,
            "snapshot_revision": snapshot["snapshot_revision"],
            "observed_date_raw": snapshot["observed_date_raw"],
            "combat_id": snapshot["combat_id"], "province_id": snapshot["province_id"],
            "query": "battle_control_snapshot_v1" if is_control else "battle_transition_v1",
        },
        "actual_sides_in_stored_order": sides,
        "terrain": terrain,
        "constructor_adjacency_kind_raw": raw_kind,
        "crossing_kind": crossing,
        "adjacency_source": "retained_combat_6F8",
        "holding_defender": holding,
        "holding_source": "retained_combat_6FE",
        "constructor_rule_plan": rule_plan,
        "current_loaded_rule_effects": effects,
        "loaded_selected_rule_effects_ready": effects_ready,
        "loaded_effect_source": "current_frame_phase_effect_database_8FC3E0",
        "loaded_effect_selection_scope": "retained_rule_slots_before_commander_exclusion_and_holding_scale",
        "current_rule_context": current_context,
        "current_rule_context_frame_qualified": bool(exact_build and actual and crossing is not None and holding is not None),
        "missing_inputs": missing,
        "complete_constructor_ready": False,
        "future_contact_preview": False,
        "unobserved_historical_inputs": [
            "original_initiator_identity_and_role", "original_attacker_entry_province",
            "initial_participant_contexts_and_roster", "initial_loaded_effect_and_scale_operands",
        ],
    }
    if current_context is not None:
        from ..simulation.battle_retained_current_rule_contributions import (
            adapt_current_retained_rule_contributions, evaluate_current_retained_rule_contributions,
        )
        inputs = adapt_current_retained_rule_contributions(diagnostic)
        diagnostic["current_rule_contributions_v1"] = (
            evaluate_current_retained_rule_contributions(inputs) if inputs is not None else None
        )
    fields = {"retained_constructor_geometry_v1": diagnostic}
    stored = geometry.get("stored_advantage_sources_v1") if geometry is not None else None
    if stored is not None:
        from ..simulation.battle_actual_stored_advantage_sources import (
            adapt_actual_stored_advantage_sources, evaluate_actual_stored_advantage_sources,
        )
        stored_diagnostic = {
            "schema_version": 1,
            "current_frame_qualified": bool(exact_build and actual),
            "source": copy.deepcopy(diagnostic["source"]),
            "stored_inputs": copy.deepcopy(stored),
        }
        inputs = adapt_actual_stored_advantage_sources(stored_diagnostic)
        stored_diagnostic["current_sources"] = (
            evaluate_actual_stored_advantage_sources(inputs) if inputs is not None else None
        )
        fields["stored_advantage_sources_v1"] = stored_diagnostic
    current = geometry.get("current_dynamic_advantage_v1") if geometry is not None else None
    if current is not None:
        from ..simulation.battle_actual_current_dynamic_advantage import (
            adapt_actual_current_dynamic_advantage, evaluate_actual_current_dynamic_advantage,
        )
        current_diagnostic = {
            "schema_version": 1, "current_frame_qualified": bool(exact_build and actual),
            "source": copy.deepcopy(diagnostic["source"]), "current_inputs": copy.deepcopy(current),
        }
        inputs = adapt_actual_current_dynamic_advantage(current_diagnostic)
        current_diagnostic["current_advantage"] = (
            evaluate_actual_current_dynamic_advantage(inputs) if inputs is not None else None
        )
        fields["current_dynamic_advantage_v1"] = current_diagnostic
    from .battle_current_dynamic_components_fields import current_dynamic_component_fields
    fields.update(current_dynamic_component_fields(snapshot, diagnostic["source"], bool(exact_build and actual)))
    from .battle_opposite_effect_eligibility_fields import opposite_effect_eligibility_fields
    fields.update(opposite_effect_eligibility_fields(snapshot, diagnostic["source"], bool(exact_build and actual)))
    from .battle_current_own_nested_modifier_fields import current_own_nested_modifier_fields
    fields.update(current_own_nested_modifier_fields(snapshot, diagnostic["source"], bool(exact_build and actual)))
    return fields
