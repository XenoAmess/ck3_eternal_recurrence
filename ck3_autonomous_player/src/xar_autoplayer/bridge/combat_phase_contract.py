"""Strict production contract for CK3 1.19.0.6 combat phase inputs.

The native bridge publishes only exact-build leaves.  This module validates
that atomic payload, derives the stock manifest's process-external values,
and proves the immutable 81-native + 51-offline = 132 state-ref partition.
It does not execute a phase event or advance CK3.
"""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .combat_contract import (
    CK3_COMBAT_FIXED_POINT_SCALE,
    PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
    PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
    PHASE_EVENT_STOCK_MANIFEST_SHA256,
    _normalize_advantage_model_v3_test_only,
    normalize_combat_simulation_inputs,
    normalize_combat_simulation_request,
)
from ..simulation.phase_event_evaluator import (
    PhaseEventEvaluationError,
    evaluate_phase_event_contexts,
)
from ..simulation.candidate_source_proof import (
    normalize_candidate_source_proof,
)


QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY = (
    "game.command.query-combat-simulation-inputs-v3-N"
)
QUERY_COMBAT_SIMULATION_INPUTS_V3_STEP_PREFIX = (
    "query-combat-simulation-inputs-v3-"
)
PHASE_EVENT_NATIVE_LEAF_EXACT_REF_COUNT = 81
PHASE_EVENT_OFFLINE_EXACT_REF_COUNT = 51
PHASE_EVENT_NATIVE_LEAF_EXACT_REFS_SHA256 = (
    "E18C26667EF5F896564B21766E145A5B63C73ACDB5DD8B21ED25853CA793119E"
)
PHASE_EVENT_OFFLINE_EXACT_REFS_SHA256 = (
    "368924B26875C74EEA9A631CAA528086829851233A48860671140E7842FF5CA6"
)

_DOMAIN_COUNTS = {
    "character_relation": 79,
    "army": 13,
    "side": 10,
    "global": 3,
    "derived": 27,
}
_ABI_COUNTS = {
    "native_leaf_exact": 81,
    "offline_exact": 51,
    "determinable": 132,
    "missing": 0,
}
_PATH_HASHES = {
    "native_leaf_exact": PHASE_EVENT_NATIVE_LEAF_EXACT_REFS_SHA256,
    "offline_exact": PHASE_EVENT_OFFLINE_EXACT_REFS_SHA256,
    "required": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
}
_PAYLOAD_POLICY = "81_exact_native_leaves_plus_51_offline_exact"
_PHASE_EVENT_MANIFEST_FIDELITY = {
    "loaded_playset_verified": False,
    "ast_evaluator_ready": False,
    "original_trace_ready": False,
    "fidelity_gate": False,
}
_MISSING_PHASE_EVENT_FIDELITY_GATES = [
    "loaded_playset_verified",
    "ast_evaluator_ready",
    "original_trace_ready",
]

_EXPLICIT_DERIVED_PATHS = frozenset(
    """derived.accolade_qualification_wound_factor_raw
derived.become_berserker_wound_factor_raw
derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter
derived.candidate_prowess_at_or_below_root_opponent_threshold
derived.candidate_prowess_at_or_below_root_opponent_threshold_without_alive_filter
derived.enemy_alive_knight_at_or_below_root_opponent_threshold_exists
derived.enemy_hostile_knight_death_accolade_any_tier
derived.enemy_hostile_knight_death_accolade_factor_raw
derived.outnumbering_injury_factor_raw
derived.own_side_more_than_five_times_enemy
derived.own_side_stronger
derived.qualifying_enemy_knight_exists
derived.root_ai_stalwart
derived.root_has_any_maim_injury
derived.root_has_any_wounded_rank_1_2_3
derived.root_injury_factor_30_raw
derived.root_injury_factor_30_with_garuda_raw
derived.root_injury_factor_40_with_garuda_raw
derived.root_is_wounded
derived.root_player_stalwart
derived.root_wounded_rank_3
derived.same_house_defends_family_any_tier
derived.same_house_defends_family_factor_raw
derived.same_house_defends_family_tier_high
derived.same_house_defends_family_tier_low_only
derived.same_house_defends_family_tier_medium_only
derived.stock_enemy_knight_selection_weight_raw""".splitlines()
)
_OFFLINE_CONTAINER_PATHS = frozenset(
    {
        "root.house_and_liege_relations",
        "root.knight_army.maa_counts",
        "game_rules",
        "root.traits_and_culture_for_blademaster",
        "selected_enemy_knight.traits_and_culture_for_blademaster",
        "root.variables",
        "root.employer.variables",
        "root.ai_should_get_extreme_conqueror_bonuses",
        "combat_side.enemy_faiths",
        "combat_side.ordered_commanders_and_knights_with_accolade_parameters",
        "root.accolade_unlocks",
        *(
            f"root.accolade_unlocks.{key}.valid"
            for key in (
                "skirmisher",
                "archer",
                "crossbowmen",
                "pike",
                "vanguard",
                "outrider",
                "lancer",
                "camelry",
                "elephantry",
                "horse_archer",
                "gunpowder",
                "fanatic",
                "valiant",
            )
        ),
    }
)
OFFLINE_EXACT_REF_PATHS = frozenset(
    _EXPLICIT_DERIVED_PATHS | _OFFLINE_CONTAINER_PATHS
)

_TRAIT_OR_GROUP_KEYS = (
    "ambitious",
    "athletic",
    "berserker",
    "brave",
    "calm",
    "cautious_leader",
    "compassionate",
    "content",
    "craven",
    "desert_warrior",
    "disfigured",
    "education_martial_1",
    "education_martial_2",
    "education_martial_3",
    "education_martial_4",
    "education_martial_5",
    "education_martial_prowess_1",
    "education_martial_prowess_2",
    "education_martial_prowess_3",
    "education_martial_prowess_4",
    "flexible_leader",
    "forest_fighter",
    "giant",
    "holy_warrior",
    "impatient",
    "incapable",
    "intellect_good_1",
    "intellect_good_2",
    "intellect_good_3",
    "jungle_stalker",
    "lazy",
    "lifestyle_blademaster",
    "maimed",
    "nomadic_philosophy",
    "one_eyed",
    "one_legged",
    "open_terrain_expert",
    "patient",
    "physique_good",
    "reckless",
    "rough_terrain_expert",
    "sadistic",
    "scholar",
    "shieldmaiden",
    "shrewd",
    "strong",
    "temperate",
    "winter_soldier",
    "wrathful",
    "zealous",
    "aggressive_attacker",
    "wounded_1",
    "wounded_2",
    "wounded_3",
    "fragile_bones",
    "tourney_participant",
)
_INNOVATION_KEYS = (
    "innovation_quilted_armor",
    "innovation_sarawit",
    "innovation_legionnaires",
    "innovation_arched_saddle",
    "innovation_valets",
    "innovation_tiefutu",
    "innovation_advanced_bowmaking",
    "innovation_repeating_crossbow",
    "innovation_war_camels",
    "innovation_elephantry",
    "innovation_gunpowder",
    "innovation_fire_medicine",
)
_TRADITION_KEYS = (
    "tradition_fp1_coastal_warriors",
    "tradition_hird",
    "tradition_futuwaa",
    "tradition_druzhina",
    "tradition_khadga_puja",
    "tradition_garuda_warriors",
    "tradition_himalayan_settlers",
    "tradition_mubarizuns",
    "tradition_burman_royal_army",
    "tradition_mountaineer_ruralism",
    "tradition_caucasian_wolves",
    "tradition_roman_legacy",
    "tradition_ep3_audacious_cadets",
    "tradition_ep3_imperial_tagmata",
)
_CULTURE_PARAMETER_KEYS = (
    "knights_slightly_more_prone_to_injury",
    "blademaster_traits_more_common",
    "unlock_zhanmadao",
    "unlock_burenjia",
    "unlock_maa_cataphract_archers",
    "unlock_maa_black_armor_cavalry",
    "unlock_maa_horse_archers",
    "unlock_maa_mangudai",
    "unlock_emishi_horse_archers_units",
    "unlock_mounted_samurai_units",
)
_ATTRIBUTE_UNLOCK_KEYS = (
    "skirmisher",
    "archer",
    "crossbowmen",
    "pike",
    "vanguard",
    "outrider",
    "lancer",
    "camelry",
    "elephantry",
    "horse_archer",
    "gunpowder",
    "fanatic",
    "valiant",
)
_ACCOLADE_PARAMETER_KEYS = (
    "accolade_defends_family_low",
    "accolade_defends_family_medium",
    "accolade_defends_family_high",
    "accolade_increase_hostile_knight_death_low",
    "accolade_increase_hostile_knight_death_medium",
    "accolade_increase_hostile_knight_death_high",
)
_MAA_COUNT_KEYS = (
    "skirmishers_raw",
    "pikemen_raw",
    "heavy_infantry_raw",
    "light_cavalry_raw",
    "heavy_cavalry_raw",
    "camel_cavalry_raw",
    "elephant_cavalry_raw",
    "archer_cavalry_raw",
    "gunpowder_raw",
    "crossbow_family_raw",
    "non_crossbow_archers_raw",
)

_CHARACTER_KEYS = {
    "character_id",
    "source_army_id",
    "source_regiment_id",
    "encounter_role",
    "phase_roles",
    "alive",
    "is_ai",
    "martial",
    "learning",
    "prowess",
    "traits_or_groups",
    "wounded_rank_raw",
    "fragile_bones_rank_raw",
    "fragile_bones_xp_raw",
    "lifestyle_blademaster_xp_raw",
    "tourney_bow_xp_raw",
    "tourney_foot_xp_raw",
    "tourney_horse_xp_raw",
    "house",
    "liege",
    "liege_house",
    "employer",
    "dynasty",
    "warfare_legacy_3",
    "stalwart_leader",
    "culture",
    "faith",
    "religion",
    "heritage_north_germanic",
    "knights_slightly_more_prone_to_injury",
    "death_is_glory",
    "tenet_warmonger",
    "germanic_religion",
    "blademaster_traits_more_common",
    "innovations",
    "traditions",
    "culture_parameters",
    "is_acclaimed",
    "can_be_acclaimed",
    "accolade",
    "accolade_has_men_at_arms_category",
    "accolade_parameters",
    "conqueror_variable_present",
    "attribute_unlock_variables",
    "hold_court_8050_knight",
    "employer_hold_court_8050_promise",
    "liege_accolade_progress_raw",
    "ai_extreme_conqueror_modifier",
    "garuda_court_position",
    "government_is_nomadic",
}


def query_combat_simulation_inputs_v3_step(
    target_province_id: object,
    attacker_entry_province_id: object,
    attacker_army_ids: object,
    defender_army_ids: object,
) -> str:
    """Encode the canonical production-v3 request literal."""
    target, entry, attackers, defenders = normalize_combat_simulation_request(
        target_province_id,
        attacker_entry_province_id,
        attacker_army_ids,
        defender_army_ids,
    )
    tokens = [
        str(target),
        str(entry),
        "a",
        str(len(attackers)),
        *(str(value) for value in attackers),
        "d",
        str(len(defenders)),
        *(str(value) for value in defenders),
    ]
    return QUERY_COMBAT_SIMULATION_INPUTS_V3_STEP_PREFIX + "-".join(tokens)


def parse_query_combat_simulation_inputs_v3_step(
    step: object,
) -> tuple[int, int, list[int], list[int]] | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_COMBAT_SIMULATION_INPUTS_V3_STEP_PREFIX
    ):
        return None
    tokens = step.removeprefix(QUERY_COMBAT_SIMULATION_INPUTS_V3_STEP_PREFIX).split(
        "-"
    )
    if len(tokens) < 8 or tokens[2] != "a":
        return None
    numeric = [_canonical_positive_token(token) for token in tokens[:2]]
    attacker_count = _canonical_positive_token(tokens[3])
    if any(value is None for value in numeric) or attacker_count is None:
        return None
    defender_marker = 4 + attacker_count
    if defender_marker + 2 >= len(tokens) or tokens[defender_marker] != "d":
        return None
    defender_count = _canonical_positive_token(tokens[defender_marker + 1])
    if defender_count is None or len(tokens) != defender_marker + 2 + defender_count:
        return None
    attacker_tokens = tokens[4:defender_marker]
    defender_tokens = tokens[defender_marker + 2 :]
    attackers = [_canonical_positive_token(token) for token in attacker_tokens]
    defenders = [_canonical_positive_token(token) for token in defender_tokens]
    if any(value is None for value in (*attackers, *defenders)):
        return None
    try:
        return normalize_combat_simulation_request(
            numeric[0], numeric[1], attackers, defenders
        )
    except ValueError:
        return None


def phase_event_ref_partition() -> dict[str, object]:
    """Return and re-prove the exact manifest partition."""
    manifest_refs = _manifest_required_refs()
    offline_refs = OFFLINE_EXACT_REF_PATHS
    native_refs = manifest_refs - offline_refs
    if (
        len(manifest_refs) != PHASE_EVENT_REQUIRED_STATE_REF_COUNT
        or len(native_refs) != PHASE_EVENT_NATIVE_LEAF_EXACT_REF_COUNT
        or len(offline_refs) != PHASE_EVENT_OFFLINE_EXACT_REF_COUNT
        or native_refs & offline_refs
        or native_refs | offline_refs != manifest_refs
    ):
        raise ValueError("production v3 132-ref partition is malformed")
    actual_hashes = {
        "native_leaf_exact": _path_digest(native_refs),
        "offline_exact": _path_digest(offline_refs),
        "required": _path_digest(manifest_refs),
    }
    if actual_hashes != _PATH_HASHES:
        raise ValueError("production v3 state-ref partition hash drifted")
    return {
        "manifest_domain_counts": dict(_DOMAIN_COUNTS),
        "abi_level_counts": dict(_ABI_COUNTS),
        "path_set_sha256": dict(_PATH_HASHES),
        "native_payload_policy": _PAYLOAD_POLICY,
        "native_leaf_paths": sorted(native_refs),
        "offline_exact_paths": sorted(offline_refs),
    }


def normalize_combat_simulation_inputs_v3(
    value: object,
    *,
    expected_target_province_id: int,
    expected_attacker_entry_province_id: int,
    expected_encounter_scope: dict[str, object],
) -> dict[str, object]:
    """Validate one atomic production v3 response and derive stock state."""
    name = "combat_simulation_inputs_v3"
    wire_root_keys = {
        "schema_version",
        "contract_stage",
        "rules_manifest_sha256",
        "base_inputs",
        "phase_event_inputs",
    }
    wire_phase_keys = {
        "status",
        "rules_source",
        "rules_manifest_sha256",
        "required_state_refs",
        "state_ref_coverage",
        "scope_mode",
        "raw",
        "advantage_model",
        "unavailable_reason",
    }
    # Driver caches and service boundaries deliberately validate the same
    # value again.  Accept the sole canonical enriched form, strip only the
    # deterministic offline projection, then recompute and byte-for-value
    # compare it.  This keeps normalization idempotent without letting a
    # producer smuggle pre-derived production claims into the native wire.
    if isinstance(value, dict) and set(value) == wire_root_keys | {"completeness"}:
        candidate = copy.deepcopy(value)
        candidate.pop("completeness")
        candidate_phase = candidate.get("phase_event_inputs")
        enriched_phase_keys = {
            "state_ref_partition",
            "evaluation_contexts",
            "row_evaluations",
            "offline_admission",
        }
        if not isinstance(candidate_phase, dict) or set(candidate_phase) != (
            wire_phase_keys | enriched_phase_keys
        ):
            raise ValueError("normalized production combat v3 phase schema is malformed")
        for key in enriched_phase_keys:
            candidate_phase.pop(key)
        recomputed = normalize_combat_simulation_inputs_v3(
            candidate,
            expected_target_province_id=expected_target_province_id,
            expected_attacker_entry_province_id=(
                expected_attacker_entry_province_id
            ),
            expected_encounter_scope=expected_encounter_scope,
        )
        if recomputed != value:
            raise ValueError("normalized production combat v3 derivation drifted")
        return recomputed
    root = _exact_object(
        value,
        wire_root_keys,
        name,
    )
    if root.get("schema_version") != 3:
        raise ValueError("production combat v3 schema_version is malformed")
    if root.get("contract_stage") != "production_exact_132_refs":
        raise ValueError("production combat v3 contract_stage is malformed")
    if root.get("rules_manifest_sha256") != PHASE_EVENT_STOCK_MANIFEST_SHA256:
        raise ValueError("production combat v3 manifest hash is malformed")
    base = normalize_combat_simulation_inputs(
        root.get("base_inputs"),
        expected_target_province_id=expected_target_province_id,
        expected_attacker_entry_province_id=expected_attacker_entry_province_id,
        expected_encounter_scope=expected_encounter_scope,
    )
    if base["completeness"]["input_observation_ready"] is not True:
        raise ValueError("production combat v3 requires a complete v2 base slice")
    phase = _normalize_phase_event_inputs(root.get("phase_event_inputs"), base=base)
    ready = phase["offline_admission"]["ready"] is True
    row_evaluations = phase.get("row_evaluations")
    evaluator_coverage = (
        row_evaluations.get("event_row_coverage")
        if isinstance(row_evaluations, dict)
        else None
    )
    ast_evaluator_ready = bool(
        ready
        and isinstance(row_evaluations, dict)
        and row_evaluations.get("status") == "ready"
        and isinstance(evaluator_coverage, dict)
        and evaluator_coverage.get("event_row_count") == 13
        and evaluator_coverage.get("trigger_ast_rows_covered") == 13
        and evaluator_coverage.get("chance_ast_rows_covered") == 13
        and evaluator_coverage.get("effect_ast_rows_covered") == 13
        and evaluator_coverage.get("unsupported_nodes") == []
        and evaluator_coverage.get("unsupported_effects") == []
        and evaluator_coverage.get("ready") is True
        and row_evaluations.get("ast_evaluator_ready") is True
        and isinstance(
            row_evaluations.get("candidate_materialization_and_order"), dict
        )
        and row_evaluations["candidate_materialization_and_order"].get("ready")
        is True
        and isinstance(row_evaluations.get("battle_horizon_feedback"), dict)
        and row_evaluations["battle_horizon_feedback"].get("ready") is True
    )
    manifest_fidelity = dict(_PHASE_EVENT_MANIFEST_FIDELITY)
    manifest_fidelity["ast_evaluator_ready"] = ast_evaluator_ready
    base_missing = copy.deepcopy(
        base["completeness"]["missing_required_domains"]
    )
    return copy.deepcopy(
        {
            "schema_version": 3,
            "contract_stage": "production_exact_132_refs",
            "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
            "base_inputs": base,
            "phase_event_inputs": phase,
            "completeness": {
                "observation_slice": "precontact-phase-event-inputs-v3",
                "base_input_observation_ready": True,
                "phase_raw_observation_ready": ready,
                "offline_exact_state_refs_ready": ready,
                "phase_event_inputs_ready": ready,
                "input_observation_ready": ready,
                # Full battle transition simulation has a separate gate.
                "monte_carlo_ready": False,
                "transition_fidelity_gate": False,
                "planner_usable": False,
                "active_attack_allowed": False,
                "phase_event_manifest_fidelity": manifest_fidelity,
                "missing_observation_domains": (
                    [] if ready else ["phase_event_inputs"]
                ),
                "missing_fidelity_gates": [
                    key
                    for key in _MISSING_PHASE_EVENT_FIDELITY_GATES
                    if key != "ast_evaluator_ready" or not ast_evaluator_ready
                ],
                "missing_required_domains": base_missing,
            },
        }
    )


def combat_simulation_inputs_v3_status(value: dict[str, object]) -> str:
    completeness = value.get("completeness")
    if not isinstance(completeness, dict):
        raise ValueError("production combat v3 completeness is missing")
    return (
        "available"
        if completeness.get("input_observation_ready") is True
        else "unavailable"
    )


def _normalize_phase_event_inputs(
    value: object, *, base: dict[str, object]
) -> dict[str, object]:
    name = "combat_simulation_inputs_v3.phase_event_inputs"
    row = _exact_object(
        value,
        {
            "status",
            "rules_source",
            "rules_manifest_sha256",
            "required_state_refs",
            "state_ref_coverage",
            "scope_mode",
            "raw",
            "advantage_model",
            "unavailable_reason",
        },
        name,
    )
    if row.get("rules_source") != "stock-installation-static-manifest":
        raise ValueError("production phase rules_source is malformed")
    if row.get("rules_manifest_sha256") != PHASE_EVENT_STOCK_MANIFEST_SHA256:
        raise ValueError("production phase manifest hash is malformed")
    if row.get("scope_mode") != "hypothetical_precontact_offline_ast":
        raise ValueError("production phase scope_mode is malformed")
    required = _exact_object(
        row.get("required_state_refs"), {"count", "sha256"}, f"{name}.required_state_refs"
    )
    if required != {
        "count": PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
        "sha256": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
    }:
        raise ValueError("production phase required-state binding is malformed")
    coverage = _normalize_coverage(row.get("state_ref_coverage"), f"{name}.state_ref_coverage")
    if row.get("status") == "unavailable":
        if row.get("raw") is not None or row.get("advantage_model") is not None:
            raise ValueError("unavailable production phase must not publish partial data")
        reason = _nonempty_string(row.get("unavailable_reason"), f"{name}.unavailable_reason")
        return {
            "status": "unavailable",
            "rules_source": "stock-installation-static-manifest",
            "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
            "required_state_refs": dict(required),
            "state_ref_coverage": coverage,
            "scope_mode": "hypothetical_precontact_offline_ast",
            "raw": None,
            "advantage_model": None,
            "state_ref_partition": phase_event_ref_partition(),
            "evaluation_contexts": None,
            "row_evaluations": None,
            "offline_admission": {
                "native_leaf_exact_count": 0,
                "offline_exact_count": 0,
                "determinable_count": 0,
                "partition_complete": True,
                "ready": False,
                "missing_required_domains": ["phase_event_inputs"],
            },
            "unavailable_reason": reason,
        }
    if row.get("status") != "available" or row.get("unavailable_reason") is not None:
        raise ValueError("production phase status is malformed")
    raw = _normalize_raw(row.get("raw"), base=base, name=f"{name}.raw")
    advantage_input = copy.deepcopy(row.get("advantage_model"))
    if (
        not isinstance(advantage_input, dict)
        or advantage_input.get("observation_origin")
        != "native_exact_build_production"
    ):
        raise ValueError("production advantage observation origin is malformed")
    if isinstance(advantage_input, dict):
        # The existing exact helper validator is shared with the frozen
        # test-only ABI; production has a distinct provenance string.
        advantage_input["observation_origin"] = "native_exact_build_test_only"
    advantage = _normalize_advantage_model_v3_test_only(
        advantage_input, name=f"{name}.advantage_model"
    )
    if advantage["status"] != "available":
        raise ValueError("available production phase requires the full advantage model")
    advantage["observation_origin"] = "native_exact_build_production"
    contexts = _derive_evaluation_contexts(raw)
    try:
        row_evaluations = evaluate_phase_event_contexts(contexts)
    except PhaseEventEvaluationError as error:
        raise ValueError(
            f"production phase AST evaluator rejected the 132-ref context: {error}"
        ) from error
    partition = phase_event_ref_partition()
    return {
        "status": "available",
        "rules_source": "stock-installation-static-manifest",
        "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
        "required_state_refs": dict(required),
        "state_ref_coverage": coverage,
        "scope_mode": "hypothetical_precontact_offline_ast",
        "raw": raw,
        "advantage_model": advantage,
        "state_ref_partition": partition,
        "evaluation_contexts": contexts,
        "row_evaluations": row_evaluations,
        "offline_admission": {
            "native_leaf_exact_count": 81,
            "offline_exact_count": 51,
            "determinable_count": 132,
            "partition_complete": True,
            "ready": True,
            "missing_required_domains": [],
        },
        "unavailable_reason": None,
    }


def _normalize_coverage(value: object, name: str) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "manifest_domain_counts",
            "abi_level_counts",
            "path_set_sha256",
            "native_payload_policy",
        },
        name,
    )
    if (
        row.get("manifest_domain_counts") != _DOMAIN_COUNTS
        or row.get("abi_level_counts") != _ABI_COUNTS
        or row.get("path_set_sha256") != _PATH_HASHES
        or row.get("native_payload_policy") != _PAYLOAD_POLICY
    ):
        raise ValueError("production phase state-ref coverage is malformed")
    return {
        "manifest_domain_counts": dict(_DOMAIN_COUNTS),
        "abi_level_counts": dict(_ABI_COUNTS),
        "path_set_sha256": dict(_PATH_HASHES),
        "native_payload_policy": _PAYLOAD_POLICY,
    }


def _normalize_raw(
    value: object, *, base: dict[str, object], name: str
) -> dict[str, object]:
    row = _exact_object(
        value,
        {"characters", "armies", "sides", "faith_hostility", "game_rules"},
        name,
    )
    expected_characters = _expected_phase_characters(base)
    character_rows = _array(row.get("characters"), f"{name}.characters")
    if len(character_rows) != len(expected_characters):
        raise ValueError("production phase character roster differs from v2")
    characters = [
        _normalize_character(raw, expected=expected, name=f"{name}.characters[{index}]")
        for index, (raw, expected) in enumerate(
            zip(character_rows, expected_characters, strict=True)
        )
    ]
    base_armies = _array(base.get("armies"), "base_inputs.armies")
    army_rows = _array(row.get("armies"), f"{name}.armies")
    if len(army_rows) != len(base_armies):
        raise ValueError("production phase army roster differs from v2")
    armies = [
        _normalize_army(raw, expected=expected, name=f"{name}.armies[{index}]")
        for index, (raw, expected) in enumerate(zip(army_rows, base_armies, strict=True))
    ]
    sides = _normalize_sides(
        row.get("sides"), base=base, characters=characters, name=f"{name}.sides"
    )
    hostility = _normalize_faith_hostility(
        row.get("faith_hostility"), characters=characters, sides=sides,
        name=f"{name}.faith_hostility",
    )
    rules = _exact_object(
        row.get("game_rules"), {"easy_difficulty", "very_easy_difficulty"},
        f"{name}.game_rules",
    )
    easy = _strict_bool(rules.get("easy_difficulty"), f"{name}.game_rules.easy_difficulty")
    very_easy = _strict_bool(
        rules.get("very_easy_difficulty"), f"{name}.game_rules.very_easy_difficulty"
    )
    if easy and very_easy:
        raise ValueError("easy and very-easy game-rule tokens cannot coexist")
    return {
        "characters": characters,
        "armies": armies,
        "sides": sides,
        "faith_hostility": hostility,
        "game_rules": {"easy_difficulty": easy, "very_easy_difficulty": very_easy},
    }


def _normalize_character(
    value: object, *, expected: dict[str, object], name: str
) -> dict[str, object]:
    row = _exact_object(value, _CHARACTER_KEYS, name)
    character_id = _positive_int32(row.get("character_id"), f"{name}.character_id")
    source_army_id = _positive_int32(row.get("source_army_id"), f"{name}.source_army_id")
    if (
        character_id != expected["character_id"]
        or source_army_id != expected["source_army_id"]
        or row.get("encounter_role") != expected["encounter_role"]
        or row.get("phase_roles") != expected["phase_roles"]
    ):
        raise ValueError("production phase character identity or role mismatch")
    expected_regiment = expected["source_regiment_id"]
    if expected_regiment is None:
        if row.get("source_regiment_id") is not None:
            raise ValueError("commander-only phase row invented a RegimentID")
    elif _positive_int32(row.get("source_regiment_id"), f"{name}.source_regiment_id") != expected_regiment:
        raise ValueError("production phase knight RegimentID mismatch")

    traits = _named_bools(row.get("traits_or_groups"), _TRAIT_OR_GROUP_KEYS, f"{name}.traits_or_groups")
    innovations = _named_bools(row.get("innovations"), _INNOVATION_KEYS, f"{name}.innovations")
    traditions = _named_bools(row.get("traditions"), _TRADITION_KEYS, f"{name}.traditions")
    culture_parameters = _named_bools(
        row.get("culture_parameters"), _CULTURE_PARAMETER_KEYS, f"{name}.culture_parameters"
    )
    accolade_parameters = _named_bools(
        row.get("accolade_parameters"), _ACCOLADE_PARAMETER_KEYS, f"{name}.accolade_parameters"
    )
    unlocks = _named_bools(
        row.get("attribute_unlock_variables"), _ATTRIBUTE_UNLOCK_KEYS,
        f"{name}.attribute_unlock_variables",
    )
    optionals = {
        key: _optional_full_id(row.get(key), f"{name}.{key}")
        for key in (
            "house", "liege", "liege_house", "employer", "dynasty", "culture",
            "faith", "religion", "accolade", "hold_court_8050_knight",
            "employer_hold_court_8050_promise",
        )
    }
    wounded_rank = _signed_int64(row.get("wounded_rank_raw"), f"{name}.wounded_rank_raw")
    if wounded_rank not in {0, 100_000, 200_000, 300_000}:
        raise ValueError("wounded rank must be exactly 0, 1, 2, or 3")
    observed_wounded = [traits[f"wounded_{rank}"] for rank in (1, 2, 3)]
    if sum(observed_wounded) > 1 or (
        wounded_rank != (observed_wounded.index(True) + 1) * 100_000
        if any(observed_wounded) else wounded_rank != 0
    ):
        raise ValueError("wounded rank disagrees with concrete trait membership")
    fragile_rank = _signed_int64(
        row.get("fragile_bones_rank_raw"), f"{name}.fragile_bones_rank_raw"
    )
    if fragile_rank not in {0, 100_000} or (fragile_rank > 0) is not traits["fragile_bones"]:
        raise ValueError("fragile-bones rank disagrees with trait membership")
    if optionals["liege"]["status"] == "absent":
        if optionals["liege_house"]["status"] != "absent":
            raise ValueError("absent liege cannot have a house")
        if row.get("liege_accolade_progress_raw") != 0:
            raise ValueError("absent liege cannot publish accolade progress")
    accolade_present = optionals["accolade"]["status"] == "available"
    is_acclaimed = _strict_bool(row.get("is_acclaimed"), f"{name}.is_acclaimed")
    if is_acclaimed is not accolade_present:
        raise ValueError("is_acclaimed disagrees with current accolade identity")
    accolade_maa = _strict_bool(
        row.get("accolade_has_men_at_arms_category"),
        f"{name}.accolade_has_men_at_arms_category",
    )
    if not accolade_present and (accolade_maa or any(accolade_parameters.values())):
        raise ValueError("absent accolade published category or parameters")
    if optionals["employer"]["status"] == "absent" and optionals[
        "employer_hold_court_8050_promise"
    ]["status"] != "absent":
        raise ValueError("absent employer published an employer variable")
    culture_present = optionals["culture"]["status"] == "available"
    if not culture_present and (
        any(innovations.values())
        or any(traditions.values())
        or any(culture_parameters.values())
        or row.get("heritage_north_germanic") is not False
        or row.get("knights_slightly_more_prone_to_injury") is not False
        or row.get("blademaster_traits_more_common") is not False
    ):
        raise ValueError("absent culture published owned definitions")
    if optionals["faith"]["status"] == "absent" and (
        row.get("death_is_glory") is not False
        or row.get("tenet_warmonger") is not False
    ):
        raise ValueError("absent faith published doctrine or parameter state")
    if optionals["religion"]["status"] == "absent" and row.get(
        "germanic_religion"
    ) is not False:
        raise ValueError("absent religion published religion membership")
    result = {
        "character_id": character_id,
        "source_army_id": source_army_id,
        "source_regiment_id": expected_regiment,
        "encounter_role": expected["encounter_role"],
        "phase_roles": list(expected["phase_roles"]),
        "alive": _strict_bool(row.get("alive"), f"{name}.alive"),
        "is_ai": _strict_bool(row.get("is_ai"), f"{name}.is_ai"),
        "martial": _signed_int32(row.get("martial"), f"{name}.martial"),
        "learning": _signed_int32(row.get("learning"), f"{name}.learning"),
        "prowess": _signed_int32(row.get("prowess"), f"{name}.prowess"),
        "traits_or_groups": traits,
        "wounded_rank_raw": wounded_rank,
        "fragile_bones_rank_raw": fragile_rank,
        "fragile_bones_xp_raw": _signed_int64(row.get("fragile_bones_xp_raw"), f"{name}.fragile_bones_xp_raw"),
        "lifestyle_blademaster_xp_raw": _signed_int64(row.get("lifestyle_blademaster_xp_raw"), f"{name}.lifestyle_blademaster_xp_raw"),
        "tourney_bow_xp_raw": _signed_int64(row.get("tourney_bow_xp_raw"), f"{name}.tourney_bow_xp_raw"),
        "tourney_foot_xp_raw": _signed_int64(row.get("tourney_foot_xp_raw"), f"{name}.tourney_foot_xp_raw"),
        "tourney_horse_xp_raw": _signed_int64(row.get("tourney_horse_xp_raw"), f"{name}.tourney_horse_xp_raw"),
        **optionals,
        "warfare_legacy_3": _strict_bool(row.get("warfare_legacy_3"), f"{name}.warfare_legacy_3"),
        "stalwart_leader": _strict_bool(row.get("stalwart_leader"), f"{name}.stalwart_leader"),
        "heritage_north_germanic": _strict_bool(row.get("heritage_north_germanic"), f"{name}.heritage_north_germanic"),
        "knights_slightly_more_prone_to_injury": _strict_bool(row.get("knights_slightly_more_prone_to_injury"), f"{name}.knights_slightly_more_prone_to_injury"),
        "death_is_glory": _strict_bool(row.get("death_is_glory"), f"{name}.death_is_glory"),
        "tenet_warmonger": _strict_bool(row.get("tenet_warmonger"), f"{name}.tenet_warmonger"),
        "germanic_religion": _strict_bool(row.get("germanic_religion"), f"{name}.germanic_religion"),
        "blademaster_traits_more_common": _strict_bool(row.get("blademaster_traits_more_common"), f"{name}.blademaster_traits_more_common"),
        "innovations": innovations,
        "traditions": traditions,
        "culture_parameters": culture_parameters,
        "is_acclaimed": is_acclaimed,
        "can_be_acclaimed": _strict_bool(row.get("can_be_acclaimed"), f"{name}.can_be_acclaimed"),
        "accolade_has_men_at_arms_category": accolade_maa,
        "accolade_parameters": accolade_parameters,
        "conqueror_variable_present": _strict_bool(row.get("conqueror_variable_present"), f"{name}.conqueror_variable_present"),
        "attribute_unlock_variables": unlocks,
        "liege_accolade_progress_raw": _signed_int64(row.get("liege_accolade_progress_raw"), f"{name}.liege_accolade_progress_raw"),
        "ai_extreme_conqueror_modifier": _strict_bool(row.get("ai_extreme_conqueror_modifier"), f"{name}.ai_extreme_conqueror_modifier"),
        "garuda_court_position": _strict_bool(row.get("garuda_court_position"), f"{name}.garuda_court_position"),
        "government_is_nomadic": _strict_bool(row.get("government_is_nomadic"), f"{name}.government_is_nomadic"),
    }
    if result["knights_slightly_more_prone_to_injury"] is not culture_parameters[
        "knights_slightly_more_prone_to_injury"
    ] or result["blademaster_traits_more_common"] is not culture_parameters[
        "blademaster_traits_more_common"
    ]:
        raise ValueError("named culture-parameter mirrors disagree")
    return result


def _normalize_army(value: object, *, expected: dict[str, object], name: str) -> dict[str, object]:
    row = _exact_object(
        value,
        {"army_id", "native_carmy_id", "encounter_role", "maa_regiment_count_raw", "maa_counts_raw"},
        name,
    )
    army_id = _positive_int32(row.get("army_id"), f"{name}.army_id")
    native_id = _positive_int32(row.get("native_carmy_id"), f"{name}.native_carmy_id")
    if (
        army_id != expected.get("army_id")
        or native_id != expected.get("native_carmy_id")
        or row.get("encounter_role") != expected.get("encounter_role")
    ):
        raise ValueError("production phase army identity or role mismatch")
    counts = _named_int64(row.get("maa_counts_raw"), _MAA_COUNT_KEYS, f"{name}.maa_counts_raw")
    if any(value < 0 or value % CK3_COMBAT_FIXED_POINT_SCALE for value in counts.values()):
        raise ValueError("MAA family counts must be non-negative whole Q100000 counts")
    total = _signed_int64(row.get("maa_regiment_count_raw"), f"{name}.maa_regiment_count_raw")
    if (
        total < 0
        or total % CK3_COMBAT_FIXED_POINT_SCALE
        or total // CK3_COMBAT_FIXED_POINT_SCALE > 2**31 - 1
    ):
        raise ValueError(
            "MAA regiment count must be a non-negative signed-int32 "
            "whole Q100000 count"
        )
    if sum(counts.values()) > total:
        raise ValueError("MAA family counts exceed the total regiment count")
    return {
        "army_id": army_id,
        "native_carmy_id": native_id,
        "encounter_role": expected["encounter_role"],
        "maa_regiment_count_raw": total,
        "maa_counts_raw": counts,
    }


def _normalize_sides(
    value: object,
    *,
    base: dict[str, object],
    characters: list[dict[str, object]],
    name: str,
) -> list[dict[str, object]]:
    rows = _array(value, name)
    if len(rows) != 2:
        raise ValueError("production phase requires exactly two sides")
    scenario = base["scenario"]
    assert isinstance(scenario, dict)
    base_armies = base["armies"]
    assert isinstance(base_armies, list)
    result: list[dict[str, object]] = []
    for index, role in enumerate(("attacker", "defender")):
        row_name = f"{name}[{index}]"
        row = _exact_object(
            rows[index],
            {
                "side_index", "encounter_role", "ordered_army_ids",
                "ordered_character_ids", "ordered_commander_ids",
                "ordered_knight_ids", "primary_participant_character_id",
                "primary_source_army_id", "commander_character_id",
                "side_strength_raw", "side_army_size_raw", "participants",
                "candidate_source_proof",
            },
            row_name,
        )
        expected_armies = list(
            scenario["attacker_army_ids" if index == 0 else "defender_army_ids"]
        )
        expected_rows = [character for character in characters if character["encounter_role"] == role]
        expected_characters = [int(character["character_id"]) for character in expected_rows]
        expected_commanders = [
            int(army["commander"]["character_id"])
            for army in base_armies
            if army["encounter_role"] == role and army["commander"]["status"] == "available"
        ]
        expected_knights = [
            int(member["character_id"])
            for army in base_armies
            if army["encounter_role"] == role
            for member in army["knights"]["members"]
        ]
        if (
            row.get("side_index") != index
            or row.get("encounter_role") != role
            or row.get("ordered_army_ids") != expected_armies
            or row.get("ordered_character_ids") != expected_characters
            or row.get("ordered_commander_ids") != expected_commanders
            or row.get("ordered_knight_ids") != expected_knights
        ):
            raise ValueError("production phase side roster/order mismatch")
        participants = _normalize_participants(
            row.get("participants"), expected_army_ids=expected_armies,
            base_armies=base_armies, name=f"{row_name}.participants",
        )
        if not participants:
            raise ValueError("production phase side has no participants")
        primary_id = _positive_int32(
            row.get("primary_participant_character_id"),
            f"{row_name}.primary_participant_character_id",
        )
        primary_army = _positive_int32(
            row.get("primary_source_army_id"), f"{row_name}.primary_source_army_id"
        )
        if primary_id != participants[0]["owner_character_id"] or primary_army != expected_armies[0]:
            raise ValueError("production phase side primary participant mismatch")
        commander = row.get("commander_character_id")
        if commander is not None:
            commander = _positive_int32(commander, f"{row_name}.commander_character_id")
            if commander not in expected_commanders:
                raise ValueError("canonical battle commander is outside side commanders")
        side_strength_raw = _signed_int32(
            row.get("side_strength_raw"), f"{row_name}.side_strength_raw"
        )
        side_army_size_raw = _signed_int64(
            row.get("side_army_size_raw"), f"{row_name}.side_army_size_raw"
        )
        if (
            side_army_size_raw < 0
            or side_army_size_raw % CK3_COMBAT_FIXED_POINT_SCALE
            or side_army_size_raw // CK3_COMBAT_FIXED_POINT_SCALE > 2**31 - 1
        ):
            raise ValueError(
                "production phase side army size must be a non-negative "
                "signed-int32 whole Q100000 count"
            )
        candidate_source_proof = normalize_candidate_source_proof(
            row.get("candidate_source_proof"), side_index=index
        )
        _validate_candidate_source_roster(
            candidate_source_proof,
            expected_army_ids=expected_armies,
            expected_commander_ids=expected_commanders,
            expected_knight_ids=expected_knights,
            characters=expected_rows,
            name=f"{row_name}.candidate_source_proof",
        )
        result.append(
            {
                "side_index": index,
                "encounter_role": role,
                "ordered_army_ids": expected_armies,
                "ordered_character_ids": expected_characters,
                "ordered_commander_ids": expected_commanders,
                "ordered_knight_ids": expected_knights,
                "primary_participant_character_id": primary_id,
                "primary_source_army_id": primary_army,
                "commander_character_id": commander,
                "side_strength_raw": side_strength_raw,
                "side_army_size_raw": side_army_size_raw,
                "participants": participants,
                "candidate_source_proof": candidate_source_proof,
            }
        )
    return result


def _validate_candidate_source_roster(
    proof: dict[str, object],
    *,
    expected_army_ids: list[int],
    expected_commander_ids: list[int],
    expected_knight_ids: list[int],
    characters: list[dict[str, object]],
    name: str,
) -> None:
    sources = proof["ordered_sources"]
    assert isinstance(sources, list)
    commander_ids: list[int] = []
    knight_ids: list[int] = []
    reached_knights = False
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"{name}.ordered_sources[{index}] is malformed")
        role = str(source["role"])
        army_id = int(source["source_army_id"])
        character_id = int(source["character_id"])
        regiment_id = source["source_regiment_id"]
        if army_id not in expected_army_ids:
            raise ValueError("candidate source refers to an army outside its side")
        if role == "commander":
            if reached_knights or regiment_id is not None:
                raise ValueError("candidate commander source order is malformed")
            commander_ids.append(character_id)
        else:
            reached_knights = True
            knight_ids.append(character_id)
        matches = [
            character
            for character in characters
            if character["character_id"] == character_id
            and character["source_army_id"] == army_id
            and role in character["phase_roles"]
            and (
                role == "commander"
                or character["source_regiment_id"] == regiment_id
            )
        ]
        if len(matches) != 1:
            raise ValueError(
                "candidate source does not uniquely match the normalized "
                "army/character/regiment roster"
            )
    if commander_ids != expected_commander_ids or knight_ids != expected_knight_ids:
        raise ValueError(
            "candidate source commander/knight subsequences differ from side rosters"
        )


def _normalize_participants(
    value: object,
    *,
    expected_army_ids: list[int],
    base_armies: list[object],
    name: str,
) -> list[dict[str, int]]:
    rows = _array(value, name)
    base_by_id = {
        int(army["army_id"]): army for army in base_armies if isinstance(army, dict)
    }
    expected_sources: list[tuple[int, int]] = []
    seen_owners: set[int] = set()
    for army_id in expected_army_ids:
        army = base_by_id[army_id]
        owner = army.get("owner")
        if not isinstance(owner, dict) or owner.get("status") != "available":
            raise ValueError("v2 army owner is unavailable for phase participants")
        owner_id = int(owner["character_id"])
        if owner_id not in seen_owners:
            seen_owners.add(owner_id)
            expected_sources.append((army_id, owner_id))
    if len(rows) != len(expected_sources):
        raise ValueError("phase participant first-seen owner roster mismatch")
    result: list[dict[str, int]] = []
    for index, ((expected_army, expected_owner), raw) in enumerate(
        zip(expected_sources, rows, strict=True)
    ):
        row_name = f"{name}[{index}]"
        row = _exact_object(raw, {"source_army_id", "owner_character_id", "faith_id"}, row_name)
        normalized = {
            "source_army_id": _positive_int32(row.get("source_army_id"), f"{row_name}.source_army_id"),
            "owner_character_id": _positive_int32(row.get("owner_character_id"), f"{row_name}.owner_character_id"),
            "faith_id": _positive_int32(row.get("faith_id"), f"{row_name}.faith_id"),
        }
        if (normalized["source_army_id"], normalized["owner_character_id"]) != (
            expected_army, expected_owner
        ):
            raise ValueError("phase participant source order/identity mismatch")
        result.append(normalized)
    return result


def _normalize_faith_hostility(
    value: object,
    *,
    characters: list[dict[str, object]],
    sides: list[dict[str, object]],
    name: str,
) -> list[dict[str, int]]:
    rows = _array(value, name)
    expected: list[tuple[int, int, int, int, int]] = []
    for character in characters:
        side_index = 0 if character["encounter_role"] == "attacker" else 1
        enemy_index = 1 - side_index
        root_faith = character["faith"]
        if not isinstance(root_faith, dict) or root_faith["status"] != "available":
            raise ValueError("phase root requires an available current faith")
        for participant in sides[enemy_index]["participants"]:
            expected.append(
                (
                    int(character["character_id"]), enemy_index,
                    int(participant["owner_character_id"]),
                    int(participant["faith_id"]), int(root_faith["value"]),
                )
            )
    if len(rows) != len(expected):
        raise ValueError("faith-hostility full matrix row count mismatch")
    result: list[dict[str, int]] = []
    keys = {
        "root_character_id", "enemy_side_index", "enemy_owner_character_id",
        "enemy_faith_id", "root_faith_id", "hostility_level_raw",
    }
    for index, (raw, expected_identity) in enumerate(zip(rows, expected, strict=True)):
        row_name = f"{name}[{index}]"
        row = _exact_object(raw, keys, row_name)
        identity = tuple(
            _positive_int32(row.get(key), f"{row_name}.{key}")
            if key != "enemy_side_index"
            else _side_index(row.get(key), f"{row_name}.{key}")
            for key in (
                "root_character_id", "enemy_side_index", "enemy_owner_character_id",
                "enemy_faith_id", "root_faith_id",
            )
        )
        if identity != expected_identity:
            raise ValueError("faith-hostility matrix order or identity mismatch")
        level = _signed_int32(row.get("hostility_level_raw"), f"{row_name}.hostility_level_raw")
        if not 0 <= level <= 3:
            raise ValueError("faith hostility must be an exact enum in [0,3]")
        result.append(
            {
                "root_character_id": identity[0],
                "enemy_side_index": identity[1],
                "enemy_owner_character_id": identity[2],
                "enemy_faith_id": identity[3],
                "root_faith_id": identity[4],
                "hostility_level_raw": level,
            }
        )
    return result


def _derive_evaluation_contexts(raw: dict[str, object]) -> list[dict[str, object]]:
    characters = raw["characters"]
    armies = raw["armies"]
    sides = raw["sides"]
    assert isinstance(characters, list) and isinstance(armies, list) and isinstance(sides, list)
    army_by_id = {int(army["army_id"]): army for army in armies}
    character_by_side_and_id = {
        (0 if row["encounter_role"] == "attacker" else 1, int(row["character_id"])): row
        for row in characters
    }
    contexts: list[dict[str, object]] = []
    for root in characters:
        side_index = 0 if root["encounter_role"] == "attacker" else 1
        enemy_index = 1 - side_index
        own_side = sides[side_index]
        enemy_side = sides[enemy_index]
        root_army = army_by_id[int(root["source_army_id"])]
        enemy_knights = [
            character_by_side_and_id[(enemy_index, int(character_id))]
            for character_id in enemy_side["ordered_knight_ids"]
        ]
        own_accolades = _ordered_accolade_parameter_rows(
            own_side, character_by_side_and_id
        )
        enemy_accolades = _ordered_accolade_parameter_rows(
            enemy_side, character_by_side_and_id
        )
        hostility = [
            row for row in raw["faith_hostility"]
            if row["root_character_id"] == root["character_id"]
        ]
        root_refs = _root_native_refs(root, root_army)
        combat_refs = {
            "combat_side.character_membership": list(own_side["ordered_character_ids"]),
            "combat_side.commander": own_side["commander_character_id"],
            "combat_side.ordered_enemy_knights": list(enemy_side["ordered_knight_ids"]),
            "combat_side.side_army_size_raw": own_side["side_army_size_raw"],
            "combat_side.side_strength_raw": own_side["side_strength_raw"],
        }
        enemy_refs = {
            "enemy_side.character_membership": list(enemy_side["ordered_character_ids"]),
            "enemy_side.side_army_size_raw": enemy_side["side_army_size_raw"],
            "enemy_side.side_strength_raw": enemy_side["side_strength_raw"],
        }
        global_refs = {
            "game_rules.easy_difficulty": raw["game_rules"]["easy_difficulty"],
            "game_rules.very_easy_difficulty": raw["game_rules"]["very_easy_difficulty"],
        }
        offline = _derive_root_offline_refs(
            root=root,
            root_army=root_army,
            own_side=own_side,
            enemy_side=enemy_side,
            enemy_knights=enemy_knights,
            own_accolades=own_accolades,
            enemy_accolades=enemy_accolades,
            hostility=hostility,
            game_rules=raw["game_rules"],
        )
        candidate_rows = []
        for candidate in enemy_knights:
            candidate_refs = _candidate_native_refs(candidate)
            candidate_refs.update(
                _candidate_derived_refs(root=root, candidate=candidate)
            )
            selected_refs = _selected_enemy_native_refs(candidate)
            selected_refs[
                "selected_enemy_knight.traits_and_culture_for_blademaster"
            ] = _blademaster_container(candidate)
            candidate_rows.append(
                {
                    "character_id": candidate["character_id"],
                    "candidate_refs": candidate_refs,
                    "selected_enemy_knight_refs": selected_refs,
                }
            )
        _validate_context_path_coverage(
            native_refs={**root_refs, **combat_refs, **enemy_refs, **global_refs},
            offline_refs=offline,
            candidate_rows=candidate_rows,
        )
        contexts.append(
            {
                "root_character_id": root["character_id"],
                "root_source_army_id": root["source_army_id"],
                "root_source_regiment_id": root["source_regiment_id"],
                "phase_roles": list(root["phase_roles"]),
                "combat_side_index": side_index,
                "enemy_side_index": enemy_index,
                "native_state_refs": {
                    **root_refs, **combat_refs, **enemy_refs, **global_refs,
                },
                "offline_state_refs": offline,
                "candidate_source_proof": copy.deepcopy(
                    enemy_side["candidate_source_proof"]
                ),
                "candidate_rows": candidate_rows,
            }
        )
    return contexts


def _root_native_refs(root: dict[str, object], army: dict[str, object]) -> dict[str, object]:
    traits = root["traits_or_groups"]
    assert isinstance(traits, dict)
    maa = army["maa_counts_raw"]
    assert isinstance(maa, dict)
    refs: dict[str, object] = {
        "root.exists": True,
        "root.alive": root["alive"],
        "root.is_ai": root["is_ai"],
        "root.is_incapable": traits["incapable"],
        "root.skills.martial_raw": int(root["martial"]) * CK3_COMBAT_FIXED_POINT_SCALE,
        "root.skills.learning_raw": int(root["learning"]) * CK3_COMBAT_FIXED_POINT_SCALE,
        "root.skills.prowess_raw": int(root["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE,
        "root.house_id": root["house"]["value"],
        "root.liege": root["liege"]["value"],
        "root.liege.house_id": root["liege_house"]["value"],
        "root.liege.accolade_progress_raw": root["liege_accolade_progress_raw"],
        "root.dynasty.perks.warfare_legacy_3": root["warfare_legacy_3"],
        "root.perks.stalwart_leader": root["stalwart_leader"],
        "root.culture.heritage_north_germanic": root["heritage_north_germanic"],
        "root.culture.parameters.knights_slightly_more_prone_to_injury": root["knights_slightly_more_prone_to_injury"],
        "root.faith.parameters.death_is_glory": root["death_is_glory"],
        "root.faith.tenets.warmonger": root["tenet_warmonger"],
        "root.religion.germanic": root["germanic_religion"],
        "root.is_acclaimed": root["is_acclaimed"],
        "root.can_be_acclaimed": root["can_be_acclaimed"],
        "root.court_positions.garuda": root["garuda_court_position"],
        "root.knight_army.maa_regiment_count_raw": army["maa_regiment_count_raw"],
        "root.traits.wounded.rank_raw": root["wounded_rank_raw"],
        "root.traits.fragile_bones.rank_raw": root["fragile_bones_rank_raw"],
        "root.traits.fragile_bones.xp_raw": root["fragile_bones_xp_raw"],
        "root.traits.maim_injuries": any(
            bool(traits[key]) for key in ("one_legged", "disfigured", "one_eyed", "maimed")
        ),
    }
    for key in (
        "ambitious", "berserker", "brave", "calm", "compassionate", "content",
        "craven", "disfigured", "giant", "impatient", "incapable", "lazy",
        "maimed", "one_eyed", "one_legged", "patient", "sadistic",
        "shieldmaiden", "temperate", "wrathful",
    ):
        path = "root.traits.incapable" if key == "incapable" else f"root.traits.{key}"
        refs[path] = traits[key]
    for key, value in maa.items():
        refs[f"root.knight_army.maa_counts.{key}"] = value
    return refs


def _candidate_native_refs(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate.alive": candidate["alive"],
        "candidate.dynasty.perks.warfare_legacy_3": candidate["warfare_legacy_3"],
        "candidate.is_acclaimed": candidate["is_acclaimed"],
        "candidate.perks.stalwart_leader": candidate["stalwart_leader"],
        "candidate.skills.prowess_raw": int(candidate["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE,
    }


def _selected_enemy_native_refs(candidate: dict[str, object]) -> dict[str, object]:
    traits = candidate["traits_or_groups"]
    return {
        "selected_enemy_knight.alive": candidate["alive"],
        "selected_enemy_knight.dynasty.perks.warfare_legacy_3": candidate["warfare_legacy_3"],
        "selected_enemy_knight.faith": candidate["faith"]["value"],
        "selected_enemy_knight.is_acclaimed": candidate["is_acclaimed"],
        "selected_enemy_knight.perks.stalwart_leader": candidate["stalwart_leader"],
        "selected_enemy_knight.skills.learning_raw": int(candidate["learning"]) * CK3_COMBAT_FIXED_POINT_SCALE,
        "selected_enemy_knight.skills.prowess_raw": int(candidate["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE,
        "selected_enemy_knight.traits.brave": traits["brave"],
        "selected_enemy_knight.traits.craven": traits["craven"],
    }


def _candidate_derived_refs(
    *, root: dict[str, object], candidate: dict[str, object]
) -> dict[str, object]:
    threshold = _qmul(
        int(root["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE, 80_000
    )
    candidate_prowess = int(candidate["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE
    return {
        "derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter": candidate_prowess >= threshold,
        "derived.candidate_prowess_at_or_below_root_opponent_threshold": bool(candidate["alive"]) and candidate_prowess <= threshold,
        "derived.candidate_prowess_at_or_below_root_opponent_threshold_without_alive_filter": candidate_prowess <= threshold,
        "derived.stock_enemy_knight_selection_weight_raw": _selection_weight(candidate),
    }


def _derive_root_offline_refs(
    *,
    root: dict[str, object],
    root_army: dict[str, object],
    own_side: dict[str, object],
    enemy_side: dict[str, object],
    enemy_knights: list[dict[str, object]],
    own_accolades: list[dict[str, object]],
    enemy_accolades: list[dict[str, object]],
    hostility: list[dict[str, object]],
    game_rules: dict[str, object],
) -> dict[str, object]:
    traits = root["traits_or_groups"]
    wounded_rank = int(root["wounded_rank_raw"])
    maim = any(bool(traits[key]) for key in ("one_legged", "disfigured", "one_eyed", "maimed"))
    threshold = _qmul(int(root["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE, 80_000)
    any_alive_below = any(
        bool(candidate["alive"])
        and int(candidate["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE <= threshold
        for candidate in enemy_knights
    )
    any_below = any(
        int(candidate["prowess"]) * CK3_COMBAT_FIXED_POINT_SCALE <= threshold
        for candidate in enemy_knights
    )
    own_strength = int(own_side["side_strength_raw"])
    enemy_strength = int(enemy_side["side_strength_raw"])
    own_stronger = own_strength > enemy_strength
    outnumber_factor = 100_000
    if own_stronger and own_strength != 0:
        outnumber_factor = min(
            _qmul(_qdiv(enemy_strength, own_strength), 140_000), 100_000
        )
    prowess = int(root["prowess"])
    garuda = 8 if root["garuda_court_position"] else 0
    house_equal = (
        root["house"]["status"] == "available"
        and root["liege_house"]["status"] == "available"
        and root["house"]["value"] == root["liege_house"]["value"]
    )
    own_tier = _highest_accolade_tier(own_accolades, "accolade_defends_family") if house_equal else None
    enemy_tier = _highest_accolade_tier(
        enemy_accolades, "accolade_increase_hostile_knight_death"
    )
    family_factor = {None: 100_000, "low": 75_000, "medium": 50_000, "high": 25_000}[own_tier]
    hostile_factor = {None: 100_000, "low": 125_000, "medium": 150_000, "high": 175_000}[enemy_tier]
    maa = dict(root_army["maa_counts_raw"])
    accolades = _accolade_unlocks(
        root=root, maa=maa, own_side=own_side, enemy_side=enemy_side,
        hostility=hostility,
    )
    wound_factor = (
        25_000 if wounded_rank == 300_000 else 50_000
        if wounded_rank in {100_000, 200_000} else 100_000
    )
    refs: dict[str, object] = {
        "root.house_and_liege_relations": {
            "house": copy.deepcopy(root["house"]),
            "liege": copy.deepcopy(root["liege"]),
            "liege_house": copy.deepcopy(root["liege_house"]),
            "same_house": house_equal,
        },
        "root.knight_army.maa_counts": maa,
        "game_rules": copy.deepcopy(game_rules),
        "root.traits_and_culture_for_blademaster": _blademaster_container(root),
        "root.variables": {
            "hold_court_8050_knight": copy.deepcopy(root["hold_court_8050_knight"]),
        },
        "root.employer.variables": {
            "employer": copy.deepcopy(root["employer"]),
            "hold_court_8050_promise": copy.deepcopy(root["employer_hold_court_8050_promise"]),
        },
        "root.ai_should_get_extreme_conqueror_bonuses": bool(root["conqueror_variable_present"] and root["ai_extreme_conqueror_modifier"]),
        "combat_side.enemy_faiths": _first_seen([int(row["enemy_faith_id"]) for row in hostility]),
        "combat_side.ordered_commanders_and_knights_with_accolade_parameters": own_accolades,
        "root.accolade_unlocks": accolades,
        "derived.accolade_qualification_wound_factor_raw": wound_factor,
        "derived.become_berserker_wound_factor_raw": wound_factor,
        "derived.enemy_alive_knight_at_or_below_root_opponent_threshold_exists": any_alive_below,
        "derived.qualifying_enemy_knight_exists": any_below,
        "derived.outnumbering_injury_factor_raw": outnumber_factor,
        "derived.own_side_more_than_five_times_enemy": own_strength > _qmul(enemy_strength, 500_000),
        "derived.own_side_stronger": own_stronger,
        "derived.root_has_any_maim_injury": maim,
        "derived.root_has_any_wounded_rank_1_2_3": wounded_rank in {100_000, 200_000, 300_000},
        "derived.root_injury_factor_30_raw": _injury_factor(prowess, 30, 0),
        "derived.root_injury_factor_30_with_garuda_raw": _injury_factor(prowess, 30, garuda),
        "derived.root_injury_factor_40_with_garuda_raw": _injury_factor(prowess, 40, garuda),
        "derived.root_is_wounded": wounded_rank in {100_000, 200_000, 300_000},
        "derived.root_player_stalwart": bool(root["stalwart_leader"] and not root["is_ai"]),
        "derived.root_ai_stalwart": bool(root["stalwart_leader"] and root["is_ai"]),
        "derived.root_wounded_rank_3": wounded_rank == 300_000,
        "derived.same_house_defends_family_any_tier": own_tier is not None,
        "derived.same_house_defends_family_factor_raw": family_factor,
        "derived.same_house_defends_family_tier_high": own_tier == "high",
        "derived.same_house_defends_family_tier_low_only": own_tier == "low",
        "derived.same_house_defends_family_tier_medium_only": own_tier == "medium",
        "derived.enemy_hostile_knight_death_accolade_any_tier": enemy_tier is not None,
        "derived.enemy_hostile_knight_death_accolade_factor_raw": hostile_factor,
    }
    for key, value in accolades.items():
        refs[f"root.accolade_unlocks.{key}.valid"] = value["valid"]
    return refs


def _accolade_unlocks(
    *,
    root: dict[str, object],
    maa: dict[str, int],
    own_side: dict[str, object],
    enemy_side: dict[str, object],
    hostility: list[dict[str, object]],
) -> dict[str, dict[str, bool]]:
    traits = root["traits_or_groups"]
    innovations = root["innovations"]
    traditions = root["traditions"]
    parameters = root["culture_parameters"]
    unlock = root["attribute_unlock_variables"]
    xp_bow = int(root["tourney_bow_xp_raw"])
    xp_foot = int(root["tourney_foot_xp_raw"])
    xp_horse = int(root["tourney_horse_xp_raw"])
    accolade_exists = root["accolade"]["status"] == "available"
    allowance = not accolade_exists or not root["accolade_has_men_at_arms_category"]
    vanguard_culture = any(
        innovations[key]
        for key in ("innovation_quilted_armor", "innovation_sarawit", "innovation_legionnaires")
    ) or any(
        traditions[key]
        for key in (
            "tradition_fp1_coastal_warriors", "tradition_hird", "tradition_futuwaa",
            "tradition_druzhina", "tradition_khadga_puja", "tradition_garuda_warriors",
            "tradition_himalayan_settlers", "tradition_mubarizuns",
            "tradition_burman_royal_army", "tradition_mountaineer_ruralism",
        )
    ) or parameters["unlock_zhanmadao"] or parameters["unlock_burenjia"]
    lancer_culture = any(
        innovations[key]
        for key in ("innovation_arched_saddle", "innovation_valets", "innovation_tiefutu")
    ) or any(
        traditions[key]
        for key in (
            "tradition_caucasian_wolves", "tradition_roman_legacy",
            "tradition_ep3_audacious_cadets", "tradition_ep3_imperial_tagmata",
        )
    ) or parameters["unlock_maa_cataphract_archers"] or parameters["unlock_maa_black_armor_cavalry"]
    horse_culture = any(
        parameters[key]
        for key in (
            "unlock_maa_horse_archers", "unlock_maa_mangudai",
            "unlock_emishi_horse_archers_units", "unlock_mounted_samurai_units",
            "unlock_maa_cataphract_archers",
        )
    )
    attrs = {
        "skirmisher": (
            unlock["skirmisher"] or xp_bow >= 3_000_000 or xp_foot >= 3_000_000
            or traits["winter_soldier"] or traits["jungle_stalker"]
        ) and allowance,
        "archer": (unlock["archer"] or xp_bow >= 3_000_000 or traits["forest_fighter"]) and allowance,
        "crossbowmen": (
            unlock["crossbowmen"] or xp_bow >= 3_000_000 or traits["cautious_leader"]
        ) and (innovations["innovation_advanced_bowmaking"] or innovations["innovation_repeating_crossbow"]) and allowance,
        "pike": (unlock["pike"] or xp_foot >= 3_000_000 or traits["rough_terrain_expert"]) and allowance,
        "vanguard": (
            unlock["vanguard"] or traits["strong"] or traits["athletic"]
            or traits["physique_good"] or xp_foot >= 3_000_000
        ) and vanguard_culture and allowance,
        "outrider": (unlock["outrider"] or xp_horse >= 3_000_000 or traits["open_terrain_expert"]) and allowance,
        "lancer": (unlock["lancer"] or xp_horse >= 3_000_000 or traits["aggressive_attacker"]) and lancer_culture and allowance,
        "camelry": (unlock["camelry"] or xp_horse >= 3_000_000 or traits["desert_warrior"]) and innovations["innovation_war_camels"] and allowance,
        "elephantry": (unlock["elephantry"] or xp_horse >= 3_000_000 or traits["jungle_stalker"]) and innovations["innovation_elephantry"] and allowance,
        "horse_archer": (
            unlock["horse_archer"] or xp_horse >= 3_000_000 or xp_bow >= 3_000_000
            or traits["flexible_leader"]
        ) and (horse_culture or root["government_is_nomadic"] or traits["nomadic_philosophy"]) and allowance,
        "gunpowder": (
            unlock["gunpowder"] or traits["scholar"] or int(root["learning"]) >= 12
        ) and (innovations["innovation_gunpowder"] or innovations["innovation_fire_medicine"]) and allowance,
        "valiant": unlock["valiant"] or traits["brave"] or traits["berserker"] or traits["reckless"],
    }
    valid = {
        "skirmisher": maa["skirmishers_raw"] > 0 and not attrs["skirmisher"],
        "archer": maa["non_crossbow_archers_raw"] > 0 and not attrs["archer"],
        "crossbowmen": maa["crossbow_family_raw"] > 0 and not attrs["crossbowmen"],
        "pike": maa["pikemen_raw"] > 0 and not attrs["pike"],
        "vanguard": maa["heavy_infantry_raw"] > 0 and not attrs["vanguard"],
        "outrider": maa["light_cavalry_raw"] > 0 and not attrs["outrider"],
        "lancer": maa["heavy_cavalry_raw"] > 0 and not attrs["lancer"],
        "camelry": maa["camel_cavalry_raw"] > 0 and not attrs["camelry"],
        "elephantry": maa["elephant_cavalry_raw"] > 0 and not attrs["elephantry"],
        "horse_archer": maa["archer_cavalry_raw"] > 0 and not attrs["horse_archer"],
        "gunpowder": maa["gunpowder_raw"] > 0 and not attrs["gunpowder"],
        "fanatic": any(int(row["hostility_level_raw"]) >= 3 for row in hostility),
        "valiant": int(own_side["side_army_size_raw"]) >= _qmul(
            int(enemy_side["side_army_size_raw"]), 66_000
        ) and not attrs["valiant"],
    }
    return {key: {"valid": bool(valid[key])} for key in _ATTRIBUTE_UNLOCK_KEYS}


def _validate_context_path_coverage(
    *,
    native_refs: dict[str, object],
    offline_refs: dict[str, object],
    candidate_rows: list[dict[str, object]],
) -> None:
    partition = phase_event_ref_partition()
    expected_native = set(partition["native_leaf_paths"])
    expected_offline = set(partition["offline_exact_paths"])
    actual_native = set(native_refs)
    actual_offline = set(offline_refs)
    # Candidate-local paths are a typed iterator schema.  An empty enemy
    # knight roster is a legitimate empty iterator, not missing observation.
    actual_native.update(
        path
        for path in expected_native
        if path.startswith("candidate.")
        or path.startswith("selected_enemy_knight.")
    )
    actual_offline.update(
        path
        for path in expected_offline
        if path.startswith("derived.candidate_")
        or path == "derived.stock_enemy_knight_selection_weight_raw"
        or path.startswith("selected_enemy_knight.")
    )
    for row in candidate_rows:
        actual_native.update(row["candidate_refs"])
        actual_native.update(row["selected_enemy_knight_refs"])
        actual_offline.update(
            path
            for path in row["candidate_refs"]
            if path in expected_offline
        )
        actual_offline.update(
            path
            for path in row["selected_enemy_knight_refs"]
            if path in expected_offline
        )
        actual_native.difference_update(expected_offline)
    if actual_native != expected_native or actual_offline != expected_offline:
        raise ValueError(
            "production phase evaluation context does not cover the exact "
            f"132-ref partition: native_missing={sorted(expected_native - actual_native)}, "
            f"native_extra={sorted(actual_native - expected_native)}, "
            f"offline_missing={sorted(expected_offline - actual_offline)}, "
            f"offline_extra={sorted(actual_offline - expected_offline)}"
        )


def _ordered_accolade_parameter_rows(
    side: dict[str, object],
    character_by_side_and_id: dict[tuple[int, int], dict[str, object]],
) -> list[dict[str, object]]:
    side_index = int(side["side_index"])
    rows: list[dict[str, object]] = []
    for role, ids in (
        ("commander", side["ordered_commander_ids"]),
        ("knight", side["ordered_knight_ids"]),
    ):
        for character_id in ids:
            character = character_by_side_and_id[(side_index, int(character_id))]
            rows.append(
                {
                    "role": role,
                    "character_id": int(character_id),
                    "source_army_id": character["source_army_id"],
                    "source_regiment_id": (
                        character["source_regiment_id"] if role == "knight" else None
                    ),
                    "accolade": copy.deepcopy(character["accolade"]),
                    "parameters": copy.deepcopy(character["accolade_parameters"]),
                }
            )
    return rows


def _highest_accolade_tier(
    rows: list[dict[str, object]], prefix: str
) -> str | None:
    for tier in ("high", "medium", "low"):
        key = f"{prefix}_{tier}"
        if any(bool(row["parameters"][key]) for row in rows):
            return tier
    return None


def _blademaster_container(character: dict[str, object]) -> dict[str, object]:
    traits = character["traits_or_groups"]
    return {
        "education_martial": [traits[f"education_martial_{index}"] for index in range(1, 6)],
        "education_martial_prowess": [traits[f"education_martial_prowess_{index}"] for index in range(1, 5)],
        "lifestyle_blademaster": traits["lifestyle_blademaster"],
        "lifestyle_blademaster_xp_raw": character["lifestyle_blademaster_xp_raw"],
        "shrewd": traits["shrewd"],
        "physique_good": traits["physique_good"],
        "intellect_good": [traits[f"intellect_good_{index}"] for index in range(1, 4)],
        "culture_blademaster_traits_more_common": character["blademaster_traits_more_common"],
    }


def _selection_weight(character: dict[str, object]) -> int:
    result = 10_000_000
    for present in (
        character["is_acclaimed"],
        character["stalwart_leader"],
        character["warfare_legacy_3"],
    ):
        if present:
            result = _qmul(result, 75_000)
    return result


def _injury_factor(prowess: int, denominator: int, bonus: int) -> int:
    return max(_trunc_div((denominator - prowess + bonus) * 100_000, denominator), 10_000)


def _qmul(left: int, right: int) -> int:
    return _trunc_div(left * right, CK3_COMBAT_FIXED_POINT_SCALE)


def _qdiv(left: int, right: int) -> int:
    if right == 0:
        raise ValueError("production phase fixed-point division by zero")
    return _trunc_div(left * CK3_COMBAT_FIXED_POINT_SCALE, right)


def _trunc_div(numerator: int, denominator: int) -> int:
    if denominator == 0:
        raise ValueError("production phase integer division by zero")
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    return sign * (abs(numerator) // abs(denominator))


def _first_seen(values: list[int]) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _expected_phase_characters(base: dict[str, object]) -> list[dict[str, object]]:
    armies = base.get("armies")
    if not isinstance(armies, list):
        raise ValueError("v2 combat armies are malformed")
    expected: list[dict[str, object]] = []
    seen: dict[tuple[int, int], int] = {}
    for army in armies:
        if not isinstance(army, dict):
            raise ValueError("v2 combat army row is malformed")
        army_id = int(army["army_id"])
        role = str(army["encounter_role"])
        commander = army.get("commander")
        if isinstance(commander, dict) and commander.get("status") == "available":
            character_id = int(commander["character_id"])
            seen[(character_id, army_id)] = len(expected)
            expected.append(
                {
                    "character_id": character_id,
                    "source_army_id": army_id,
                    "source_regiment_id": None,
                    "encounter_role": role,
                    "phase_roles": ["commander"],
                }
            )
        knights = army.get("knights")
        members = knights.get("members") if isinstance(knights, dict) else None
        if not isinstance(members, list):
            raise ValueError("v2 combat knight roster is malformed")
        for member in members:
            character_id = int(member["character_id"])
            key = (character_id, army_id)
            if key in seen:
                current = expected[seen[key]]
                if current["source_regiment_id"] is not None:
                    raise ValueError("v2 roster repeats a commander/knight")
                current["phase_roles"] = ["commander", "knight"]
                current["source_regiment_id"] = int(member["source_regiment_id"])
            else:
                seen[key] = len(expected)
                expected.append(
                    {
                        "character_id": character_id,
                        "source_army_id": army_id,
                        "source_regiment_id": int(member["source_regiment_id"]),
                        "encounter_role": role,
                        "phase_roles": ["knight"],
                    }
                )
    return expected


@lru_cache(maxsize=1)
def _manifest_required_refs() -> frozenset[str]:
    path = (
        Path(__file__).resolve().parents[1]
        / "simulation"
        / "data"
        / "ck3_1_19_0_6_stock_combat_phase_events.json"
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    canonical = dict(manifest)
    claimed = canonical.pop("canonical_manifest_sha256", None)
    digest = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()
    if claimed != PHASE_EVENT_STOCK_MANIFEST_SHA256 or digest != claimed:
        raise ValueError("production phase manifest hash mismatch")
    refs = frozenset(
        ref for event in manifest["event_rows"] for ref in event["state_dependencies"]
    )
    if len(refs) != PHASE_EVENT_REQUIRED_STATE_REF_COUNT or _path_digest(refs) != PHASE_EVENT_REQUIRED_STATE_REFS_SHA256:
        raise ValueError("production phase required-state digest mismatch")
    return refs


def _path_digest(paths: frozenset[str] | set[str]) -> str:
    return hashlib.sha256(
        json.dumps(sorted(paths), separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def _canonical_positive_token(token: str) -> int | None:
    if not token or not token.isascii() or not token.isdecimal() or token.startswith("0"):
        return None
    value = int(token)
    return value if 0 < value <= 2**31 - 1 else None


def _exact_object(value: object, keys: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} schema is malformed")
    return value


def _array(value: object, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")
    return value


def _signed_int32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not -(2**31) <= value <= 2**31 - 1:
        raise ValueError(f"{name} must be a signed int32")
    return value


def _signed_int64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not -(2**63) <= value <= 2**63 - 1:
        raise ValueError(f"{name} must be a signed int64")
    return value


def _positive_int32(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be a positive full ID")
    return result


def _side_index(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result not in {0, 1}:
        raise ValueError(f"{name} must be side index 0 or 1")
    return result


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _optional_full_id(value: object, name: str) -> dict[str, object]:
    row = _exact_object(value, {"status", "value"}, name)
    if row.get("status") == "absent":
        if row.get("value") is not None:
            raise ValueError(f"{name} absent ID must be null")
        return {"status": "absent", "value": None}
    if row.get("status") != "available":
        raise ValueError(f"{name} optional-ID status is malformed")
    return {"status": "available", "value": _positive_int32(row.get("value"), f"{name}.value")}


def _named_bools(value: object, keys: tuple[str, ...], name: str) -> dict[str, bool]:
    row = _exact_object(value, set(keys), name)
    return {key: _strict_bool(row.get(key), f"{name}.{key}") for key in keys}


def _named_int64(value: object, keys: tuple[str, ...], name: str) -> dict[str, int]:
    row = _exact_object(value, set(keys), name)
    return {key: _signed_int64(row.get(key), f"{name}.{key}") for key in keys}
