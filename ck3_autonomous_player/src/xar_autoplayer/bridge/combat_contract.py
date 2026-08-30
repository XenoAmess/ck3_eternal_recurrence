"""Strict hypothetical-contact contract for native CK3 combat input queries.

This module deliberately contains no simulator.  It validates the explicit
encounter identity that the read-only native bridge is allowed to inspect and
normalizes only exact-build observations; aggregates or command ACKs are never
promoted to combat readiness.
"""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from .war_contract import army_strength_scope


QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY = (
    "game.command.query-combat-simulation-inputs-v2-N"
)
QUERY_COMBAT_SIMULATION_INPUTS_STEP_PREFIX = (
    "query-combat-simulation-inputs-v2-"
)
QUERY_COMBAT_SIMULATION_INPUTS_V3_TEST_STEP_PREFIX = (
    "query-combat-simulation-inputs-v3-"
)
MAX_COMBAT_SIMULATION_REQUEST_ARMY_IDS = 64
CK3_COMBAT_FIXED_POINT_SCALE = 100_000
PHASE_EVENT_STOCK_MANIFEST_SHA256 = (
    "91EDCEEDC634C5ACDCFAC8B02F53FE74C4E7A2E1768AAFC12CD0D976E874F2AC"
)
PHASE_EVENT_REQUIRED_STATE_REFS_SHA256 = (
    "2B5E8445EFD14DC65D8BA4046242BBC37A0226C2BCD971D805D9A6F0064A1DD0"
)
PHASE_EVENT_REQUIRED_STATE_REF_COUNT = 132
PHASE_EVENT_NATIVE_LEAF_EXACT_REFS_SHA256 = (
    "1BB1CA55C1C7E2388B5FE2A71CB4AFBD76DAD784A9CDB825615E2AACB94D8D5E"
)
PHASE_EVENT_OFFLINE_DERIVED_EXACT_REFS_SHA256 = (
    "7F93575CEDFE3CF1DCEBC6265A2BE867FA1BC341CDFE334DE3791B6A9AB48064"
)
PHASE_EVENT_REMAINING_UNCLOSED_REFS_SHA256 = (
    "180FD456E591FF72CF513D5197EB927782EB813001DDAE533482B3985038A60F"
)

_V3_NATIVE_LEAF_EXACT_REF_PATHS = frozenset(
    """candidate.alive
candidate.skills.prowess_raw
combat_side.character_membership
combat_side.commander
combat_side.ordered_enemy_knights
combat_side.side_army_size_raw
combat_side.side_strength_raw
enemy_side.character_membership
enemy_side.side_army_size_raw
enemy_side.side_strength_raw
root.alive
root.exists
root.is_ai
root.is_incapable
root.knight_army.maa_regiment_count_raw
root.skills.learning_raw
root.skills.martial_raw
root.skills.prowess_raw
root.traits.ambitious
root.traits.berserker
root.traits.brave
root.traits.calm
root.traits.compassionate
root.traits.content
root.traits.craven
root.traits.disfigured
root.traits.fragile_bones.rank_raw
root.traits.fragile_bones.xp_raw
root.traits.giant
root.traits.impatient
root.traits.incapable
root.traits.lazy
root.traits.maim_injuries
root.traits.maimed
root.traits.one_eyed
root.traits.one_legged
root.traits.patient
root.traits.sadistic
root.traits.shieldmaiden
root.traits.temperate
root.traits.wounded.rank_raw
root.traits.wrathful
selected_enemy_knight.alive
selected_enemy_knight.skills.learning_raw
selected_enemy_knight.skills.prowess_raw
selected_enemy_knight.traits.brave
selected_enemy_knight.traits.craven""".splitlines()
)
_V3_OFFLINE_DERIVED_EXACT_REF_PATHS = frozenset(
    """derived.accolade_qualification_wound_factor_raw
derived.become_berserker_wound_factor_raw
derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter
derived.candidate_prowess_at_or_below_root_opponent_threshold
derived.candidate_prowess_at_or_below_root_opponent_threshold_without_alive_filter
derived.enemy_alive_knight_at_or_below_root_opponent_threshold_exists
derived.outnumbering_injury_factor_raw
derived.own_side_more_than_five_times_enemy
derived.own_side_stronger
derived.qualifying_enemy_knight_exists
derived.root_has_any_maim_injury
derived.root_has_any_wounded_rank_1_2_3
derived.root_injury_factor_30_raw
derived.root_is_wounded
derived.root_wounded_rank_3""".splitlines()
)

_V3_CONSTRUCTOR_CALL_ORDER = [
    "width",
    "attacker_adjacency",
    "defender_adjacency",
    "attacker_terrain",
    "defender_terrain",
    "side_context_0",
    "side_context_1",
    "supply_0",
    "supply_1",
    "holding_defender_1",
    "gathering_army_0",
    "gathering_army_1",
    "debt_0_owner_then_treasury",
    "debt_1_owner_then_treasury",
    "unreformed_faith_0",
    "unreformed_faith_1",
    "side_finalize_0",
    "side_finalize_1",
]
_V3_ADVANTAGE_SOURCE_ORDER = [
    "attacker_adjacency",
    "defender_adjacency",
    "attacker_terrain",
    "defender_terrain",
    "supply_0",
    "supply_1",
    "holding_defender_1",
    "gathering_army_0",
    "gathering_army_1",
    "debt_0_owner",
    "debt_0_treasury",
    "debt_1_owner",
    "debt_1_treasury",
    "unreformed_faith_0",
    "unreformed_faith_1",
]
_V3_TEST_ONLY_BLOCKERS = [
    "native_exact_phase_state_readers",
    "native_advantage_model_fixture_and_paused_live_acceptance",
    "loaded_playset_phase_effects_exact",
    "phase_effect_ast_evaluator_exact",
    "effect_local_candidate_order_exact",
    "dynamic_participant_route_exact",
    "original_participant_recompute_trace_exact",
]

_SIMULATOR_GAPS = [
    "damage_to_casualty_allocation",
    "pursuit_transition",
    "battle_end_and_retreat_transition",
    "phase_event_rng_and_effects",
]
_INPUT_GAPS = {
    "target_terrain",
    "crossing",
    "attacker_defender_holding",
    "contact_combat_width",
    "army_identity_and_owner",
    "commander_and_roll_bounds",
    "regiment_composition",
    "regiment_identity",
    "regiment_maa_type",
    "regiment_kind_and_main_phase_eligibility",
    "effective_regiment_stats",
    "counter_operands",
    "knights",
    "ongoing_combat_context",
    "counter_resolutions",
}


def normalize_combat_simulation_request(
    target_province_id: object,
    attacker_entry_province_id: object,
    attacker_army_ids: object,
    defender_army_ids: object,
) -> tuple[int, int, list[int], list[int]]:
    """Validate one explicit hypothetical contact scenario.

    The two physical sides are caller-selected, but every ID is revalidated
    against one paused active-war scope before the native query may run.
    """
    target = _positive_int32_id(target_province_id, "target_province_id")
    entry = _positive_int32_id(
        attacker_entry_province_id,
        "attacker_entry_province_id",
    )
    if target == entry:
        raise ValueError(
            "attacker_entry_province_id must differ from target_province_id"
        )
    normalized_sides: list[list[int]] = []
    seen: set[int] = set()
    for side_name, raw_ids in (
        ("attacker_army_ids", attacker_army_ids),
        ("defender_army_ids", defender_army_ids),
    ):
        if not isinstance(raw_ids, list) or not raw_ids:
            raise ValueError(f"{side_name} must be a non-empty array")
        normalized: list[int] = []
        for index, value in enumerate(raw_ids):
            army_id = _positive_int32_id(value, f"{side_name}[{index}]")
            if army_id in seen:
                raise ValueError(
                    "combat participant ArmyIDs must not contain duplicates"
                )
            seen.add(army_id)
            normalized.append(army_id)
        normalized_sides.append(normalized)
    if len(seen) > MAX_COMBAT_SIMULATION_REQUEST_ARMY_IDS:
        raise ValueError(
            "combat participants must contain at most "
            f"{MAX_COMBAT_SIMULATION_REQUEST_ARMY_IDS} ArmyIDs"
        )
    return target, entry, normalized_sides[0], normalized_sides[1]


def query_combat_simulation_inputs_step(
    target_province_id: object,
    attacker_entry_province_id: object,
    attacker_army_ids: object,
    defender_army_ids: object,
) -> str:
    """Encode the canonical, count-delimited strict-ASCII v2 step."""
    target, entry, attackers, defenders = normalize_combat_simulation_request(
        target_province_id,
        attacker_entry_province_id,
        attacker_army_ids,
        defender_army_ids,
    )
    tokens: list[str] = [
        str(target),
        str(entry),
        "a",
        str(len(attackers)),
        *(str(value) for value in attackers),
        "d",
        str(len(defenders)),
        *(str(value) for value in defenders),
    ]
    return QUERY_COMBAT_SIMULATION_INPUTS_STEP_PREFIX + "-".join(tokens)


def query_combat_simulation_inputs_v3_test_step(
    target_province_id: object,
    attacker_entry_province_id: object,
    attacker_army_ids: object,
    defender_army_ids: object,
) -> str:
    """Encode the reserved v3 literal without advertising or dispatching it."""
    target, entry, attackers, defenders = normalize_combat_simulation_request(
        target_province_id,
        attacker_entry_province_id,
        attacker_army_ids,
        defender_army_ids,
    )
    tokens: list[str] = [
        str(target),
        str(entry),
        "a",
        str(len(attackers)),
        *(str(value) for value in attackers),
        "d",
        str(len(defenders)),
        *(str(value) for value in defenders),
    ]
    return QUERY_COMBAT_SIMULATION_INPUTS_V3_TEST_STEP_PREFIX + "-".join(
        tokens
    )


def _canonical_positive_token(token: str) -> int | None:
    if (
        not token
        or not token.isascii()
        or not token.isdecimal()
        or token.startswith("0")
    ):
        return None
    value = int(token)
    return value if 0 < value <= 2**31 - 1 else None


def parse_query_combat_simulation_inputs_step(
    step: object,
) -> tuple[int, int, list[int], list[int]] | None:
    """Parse only the canonical count-delimited ASCII v2 spelling."""
    return _parse_query_combat_simulation_inputs_step_with_prefix(
        step, QUERY_COMBAT_SIMULATION_INPUTS_STEP_PREFIX
    )


def parse_query_combat_simulation_inputs_v3_test_step(
    step: object,
) -> tuple[int, int, list[int], list[int]] | None:
    """Parse the reserved v3 spelling; no production dispatcher calls this."""
    return _parse_query_combat_simulation_inputs_step_with_prefix(
        step, QUERY_COMBAT_SIMULATION_INPUTS_V3_TEST_STEP_PREFIX
    )


def _parse_query_combat_simulation_inputs_step_with_prefix(
    step: object, prefix: str
) -> tuple[int, int, list[int], list[int]] | None:
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    suffix = step.removeprefix(prefix)
    tokens = suffix.split("-")
    if len(tokens) < 8 or tokens[2] != "a":
        return None
    target = _canonical_positive_token(tokens[0])
    entry = _canonical_positive_token(tokens[1])
    attacker_count = _canonical_positive_token(tokens[3])
    if target is None or entry is None or attacker_count is None:
        return None
    defender_marker_index = 4 + attacker_count
    if (
        defender_marker_index + 2 >= len(tokens)
        or tokens[defender_marker_index] != "d"
    ):
        return None
    defender_count = _canonical_positive_token(
        tokens[defender_marker_index + 1]
    )
    if defender_count is None or len(tokens) != defender_marker_index + 2 + defender_count:
        return None
    attacker_tokens = tokens[4:defender_marker_index]
    defender_tokens = tokens[defender_marker_index + 2 :]
    attackers = [_canonical_positive_token(token) for token in attacker_tokens]
    defenders = [_canonical_positive_token(token) for token in defender_tokens]
    if any(value is None for value in (*attackers, *defenders)):
        return None
    try:
        return normalize_combat_simulation_request(
            target,
            entry,
            attackers,
            defenders,
        )
    except ValueError:
        return None


def combat_simulation_encounter_scope(
    snapshot: dict[str, object],
    attacker_army_ids: object,
    defender_army_ids: object,
) -> dict[str, object]:
    """Prove the selected armies form two sides of one current active war.

    The relation lane comes exclusively from the paused native snapshot.  It
    is not reconstructed from owners or inferred from positions.  Every
    selected army must share at least one full-generation WarID, and the set
    must contain at least one friendly and one hostile row.
    """
    _, _, attackers, defenders = normalize_combat_simulation_request(
        1,
        2,
        attacker_army_ids,
        defender_army_ids,
    )
    requested_ids = [*attackers, *defenders]
    scope = army_strength_scope(snapshot)
    by_id = {int(row["army_id"]): row for row in scope}
    outside_scope = [
        army_id for army_id in requested_ids if army_id not in by_id
    ]
    if outside_scope:
        raise ValueError(
            "army_ids are outside the current published player/war scope: "
            f"{outside_scope}"
        )
    selected_attackers = [by_id[army_id] for army_id in attackers]
    selected_defenders = [by_id[army_id] for army_id in defenders]
    selected = [*selected_attackers, *selected_defenders]
    relation_side = lambda row: (
        "enemy"
        if row.get("scope_role") == "active_war_enemy"
        else "player_or_allied"
    )
    attacker_sides = {relation_side(row) for row in selected_attackers}
    defender_sides = {relation_side(row) for row in selected_defenders}
    common_war_ids = list(selected[0].get("war_ids", []))
    for row in selected:
        row_war_ids = row.get("war_ids")
        if not isinstance(row_war_ids, list):
            raise ValueError("combat encounter scope contains malformed war_ids")
        common_war_ids = [
            war_id for war_id in common_war_ids if war_id in row_war_ids
        ]
    if (
        len(attacker_sides) != 1
        or len(defender_sides) != 1
        or attacker_sides == defender_sides
        or not common_war_ids
    ):
        raise ValueError(
            "attacker and defender ArmyIDs must be opposite coalitions "
            "sharing one active war"
        )
    attacker_side = next(iter(attacker_sides))
    defender_side = next(iter(defender_sides))
    return {
        "army_ids": requested_ids,
        "attacker_army_ids": attackers,
        "defender_army_ids": defenders,
        "selected_scope": [dict(row) for row in selected],
        "attacker_scope": [dict(row) for row in selected_attackers],
        "defender_scope": [dict(row) for row in selected_defenders],
        "attacker_side": attacker_side,
        "defender_side": defender_side,
        "common_war_ids": common_war_ids,
    }


def is_native_combat_query_step(step: object) -> bool:
    return parse_query_combat_simulation_inputs_step(step) is not None


def normalize_combat_simulation_inputs(
    value: object,
    *,
    expected_target_province_id: int,
    expected_attacker_entry_province_id: int,
    expected_encounter_scope: dict[str, object],
) -> dict[str, object]:
    """Validate the exact JSON emitted by ``AppendCombatSimulationInputs``.

    Every available branch is value-complete.  ``absent`` and ``unavailable``
    retain their distinct null contracts, and any unavailable required input
    must keep ``input_observation_ready`` false.  This function never changes
    the separate Monte Carlo gate.
    """
    root = _exact_object(
        value,
        {
            "target_province_id",
            "participant_policy",
            "scenario",
            "armies",
            "target_province",
            "ongoing_combats",
            "counter_resolutions",
            "completeness",
        },
        "combat_simulation_inputs",
    )
    target_id = _positive_int32_id(
        root.get("target_province_id"),
        "combat_simulation_inputs.target_province_id",
    )
    if target_id != _positive_int32_id(
        expected_target_province_id,
        "expected_target_province_id",
    ):
        raise ValueError("native combat target ProvinceID mismatch")
    if (
        root.get("participant_policy")
        != "explicit_hypothetical_fixed_at_contact_no_reinforcements"
    ):
        raise ValueError("native combat participant_policy is malformed")

    scenario = _normalize_scenario(
        root.get("scenario"),
        target_province_id=target_id,
        expected_attacker_entry_province_id=(
            expected_attacker_entry_province_id
        ),
        expected_encounter_scope=expected_encounter_scope,
    )

    raw_armies = _array(root.get("armies"), "combat_simulation_inputs.armies")
    expected_army_scope = expected_encounter_scope.get("selected_scope")
    if not isinstance(expected_army_scope, list):
        raise ValueError("expected combat encounter scope is malformed")
    if len(raw_armies) != len(expected_army_scope):
        raise ValueError("native combat armies do not match the request")
    input_gaps: set[str] = set()
    normalized_armies: list[dict[str, object]] = []
    seen_native_army_ids: set[int] = set()
    seen_regiment_ids: set[int] = set()
    seen_knight_ids: set[int] = set()
    seen_knight_regiment_ids: set[int] = set()
    attacker_count = len(scenario["attacker_army_ids"])
    for index, (raw_army, scope_row) in enumerate(
        zip(raw_armies, expected_army_scope, strict=True)
    ):
        army = _normalize_combat_army(
            raw_army,
            name=f"combat_simulation_inputs.armies[{index}]",
            target_province_id=target_id,
            expected_scope=scope_row,
            expected_encounter_role=(
                "attacker" if index < attacker_count else "defender"
            ),
            input_gaps=input_gaps,
            seen_regiment_ids=seen_regiment_ids,
            seen_knight_ids=seen_knight_ids,
            seen_knight_regiment_ids=seen_knight_regiment_ids,
        )
        native_army_id = army.get("native_carmy_id")
        if native_army_id is not None:
            if int(native_army_id) in seen_native_army_ids:
                raise ValueError("native combat armies repeat a CArmyID")
            seen_native_army_ids.add(int(native_army_id))
        normalized_armies.append(army)

    target = _normalize_target_province(
        root.get("target_province"),
        target_province_id=target_id,
        input_gaps=input_gaps,
    )
    ongoing = _normalize_ongoing_combats(
        root.get("ongoing_combats"), input_gaps=input_gaps
    )
    first_owner_by_side: dict[str, int] = {}
    for army in normalized_armies:
        relation_side = (
            "enemy"
            if army["scope_role"] == "active_war_enemy"
            else "player_or_allied"
        )
        owner = army["owner"]
        if relation_side not in first_owner_by_side and (
            owner["status"] == "available"
        ):
            first_owner_by_side[relation_side] = int(owner["character_id"])
    counter_resolutions = _normalize_counter_resolutions(
        root.get("counter_resolutions"),
        input_gaps=input_gaps,
        expected_owner_by_side=first_owner_by_side,
    )
    class_count = int(counter_resolutions[0]["class_count"])
    for army in normalized_armies:
        regiments = army.get("regiments")
        for regiment in regiments if isinstance(regiments, list) else []:
            counter = regiment["counter"]
            if counter["status"] == "available":
                if int(counter["class_index"]) >= class_count:
                    raise ValueError(
                        "native combat counter class_index is out of range"
                    )
                for counter_target in counter["targets"]:
                    if int(counter_target["class_index"]) >= class_count:
                        raise ValueError(
                            "native combat counter target is out of range"
                        )

    completeness = _normalize_completeness(
        root.get("completeness"), input_gaps=input_gaps
    )
    normalized = {
        "target_province_id": target_id,
        "participant_policy": (
            "explicit_hypothetical_fixed_at_contact_no_reinforcements"
        ),
        "scenario": scenario,
        "armies": normalized_armies,
        "target_province": target,
        "ongoing_combats": ongoing,
        "counter_resolutions": counter_resolutions,
        "completeness": completeness,
    }
    # Return detached canonical values so a transport fixture cannot mutate a
    # query cache after validation.
    return copy.deepcopy(normalized)


def normalize_combat_simulation_inputs_v3_test_only(
    value: object,
    *,
    expected_target_province_id: int,
    expected_attacker_entry_province_id: int,
    expected_encounter_scope: dict[str, object],
) -> dict[str, object]:
    """Validate the unadvertised v3 fixture shape.

    This path exists only to freeze the DTO and admission gates while native
    readers are still being reversed.  It cannot return a production-ready
    observation, has no capability, and contains no hypothetical CombatID.
    """
    name = "combat_simulation_inputs_v3_test_only"
    root = _exact_object(
        value,
        {
            "schema_version",
            "contract_stage",
            "rules_manifest_sha256",
            "base_inputs",
            "phase_event_inputs",
            "completeness",
        },
        name,
    )
    if root.get("schema_version") != 3:
        raise ValueError("native v3 test schema_version is malformed")
    if root.get("contract_stage") != "test_only_unadvertised":
        raise ValueError("native v3 contract_stage is malformed")
    if root.get("rules_manifest_sha256") != PHASE_EVENT_STOCK_MANIFEST_SHA256:
        raise ValueError("native v3 phase manifest hash is malformed")
    base_inputs = normalize_combat_simulation_inputs(
        root.get("base_inputs"),
        expected_target_province_id=expected_target_province_id,
        expected_attacker_entry_province_id=(
            expected_attacker_entry_province_id
        ),
        expected_encounter_scope=expected_encounter_scope,
    )
    if base_inputs["completeness"]["input_observation_ready"] is not True:
        raise ValueError("v3 test contract requires a complete v2 base slice")
    phase = _normalize_phase_event_inputs_v3_test_only(
        root.get("phase_event_inputs"), base_inputs=base_inputs
    )
    completeness = _normalize_v3_test_completeness(
        root.get("completeness"), base_inputs=base_inputs, phase=phase
    )
    return copy.deepcopy(
        {
            "schema_version": 3,
            "contract_stage": "test_only_unadvertised",
            "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
            "base_inputs": base_inputs,
            "phase_event_inputs": phase,
            "completeness": completeness,
        }
    )


def _normalize_phase_event_inputs_v3_test_only(
    value: object, *, base_inputs: dict[str, object]
) -> dict[str, object]:
    name = "combat_simulation_inputs_v3_test_only.phase_event_inputs"
    row = _exact_object(
        value,
        {
            "status",
            "rules_source",
            "rules_manifest_sha256",
            "required_state_refs",
            "state_ref_coverage",
            "scope_mode",
            "characters",
            "armies",
            "sides",
            "global_state_refs",
            "advantage_model",
            "row_evaluations",
            "offline_admission",
            "unavailable_reason",
        },
        name,
    )
    if row.get("rules_source") != "stock-installation-static-manifest":
        raise ValueError("v3 test rules_source is malformed")
    if row.get("rules_manifest_sha256") != PHASE_EVENT_STOCK_MANIFEST_SHA256:
        raise ValueError("v3 test rules manifest hash is malformed")
    if row.get("scope_mode") != "hypothetical_precontact_offline_ast":
        raise ValueError("v3 test scope_mode is malformed")
    required_ref_summary = _exact_object(
        row.get("required_state_refs"),
        {"count", "sha256"},
        f"{name}.required_state_refs",
    )
    if (
        required_ref_summary.get("count")
        != PHASE_EVENT_REQUIRED_STATE_REF_COUNT
        or required_ref_summary.get("sha256")
        != PHASE_EVENT_REQUIRED_STATE_REFS_SHA256
    ):
        raise ValueError("v3 required-state-ref binding is malformed")
    coverage = _normalize_phase_ref_coverage_v3_test_only(
        row.get("state_ref_coverage"), name=f"{name}.state_ref_coverage"
    )

    if row.get("status") == "unavailable":
        for key in (
            "characters",
            "armies",
            "sides",
            "global_state_refs",
            "advantage_model",
            "row_evaluations",
        ):
            if row.get(key) is not None:
                raise ValueError(
                    "unavailable v3 phase slice must not publish partial values"
                )
        admission = _normalize_phase_offline_admission_v3_test_only(
            row.get("offline_admission"),
            name=f"{name}.offline_admission",
        )
        unavailable_reason = _nonempty_string(
            row.get("unavailable_reason"), f"{name}.unavailable_reason"
        )
        return {
            "status": "unavailable",
            "rules_source": "stock-installation-static-manifest",
            "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
            "required_state_refs": {
                "count": PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
                "sha256": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
            },
            "state_ref_coverage": coverage,
            "scope_mode": "hypothetical_precontact_offline_ast",
            "characters": None,
            "armies": None,
            "sides": None,
            "global_state_refs": None,
            "advantage_model": None,
            "row_evaluations": None,
            "offline_admission": admission,
            "unavailable_reason": unavailable_reason,
        }
    if row.get("status") != "partial":
        raise ValueError("v3 test phase status is malformed")

    manifest_refs = _V3_NATIVE_LEAF_EXACT_REF_PATHS
    character_ref_paths = _canonical_character_ref_paths(manifest_refs)
    side_ref_paths = _canonical_side_ref_paths(manifest_refs)
    global_ref_paths = {
        path for path in manifest_refs if path.startswith("game_rules")
    }
    expected_characters = _expected_phase_characters(base_inputs)
    raw_characters = _array(row.get("characters"), f"{name}.characters")
    if len(raw_characters) != len(expected_characters):
        raise ValueError("v3 character roster does not match v2 participants")
    characters = [
        _normalize_phase_character_v3_test_only(
            raw_character,
            name=f"{name}.characters[{index}]",
            expected=expected,
            required_ref_paths=character_ref_paths,
        )
        for index, (raw_character, expected) in enumerate(
            zip(raw_characters, expected_characters, strict=True)
        )
    ]

    base_armies = base_inputs.get("armies")
    assert isinstance(base_armies, list)
    raw_armies = _array(row.get("armies"), f"{name}.armies")
    if len(raw_armies) != len(base_armies):
        raise ValueError("v3 phase armies do not match v2 participants")
    armies = [
        _normalize_phase_army_v3_test_only(
            raw_army,
            name=f"{name}.armies[{index}]",
            expected=base_army,
        )
        for index, (raw_army, base_army) in enumerate(
            zip(raw_armies, base_armies, strict=True)
        )
    ]
    sides = _normalize_phase_sides_v3_test_only(
        row.get("sides"),
        name=f"{name}.sides",
        base_inputs=base_inputs,
        characters=characters,
        required_ref_paths=side_ref_paths,
    )
    global_refs = _normalize_state_refs_v3_test_only(
        row.get("global_state_refs"),
        name=f"{name}.global_state_refs",
        required_paths=global_ref_paths,
    )
    advantage = _normalize_advantage_model_v3_test_only(
        row.get("advantage_model"), name=f"{name}.advantage_model"
    )
    evaluations = _exact_object(
        row.get("row_evaluations"),
        {"status", "scope", "reason"},
        f"{name}.row_evaluations",
    )
    if evaluations != {
        "status": "unsupported",
        "scope": "hypothetical_precontact",
        "reason": "hypothetical_precontact_has_no_real_combat_side",
    }:
        raise ValueError("precontact row evaluations must remain unsupported")
    admission = _normalize_phase_offline_admission_v3_test_only(
        row.get("offline_admission"),
        name=f"{name}.offline_admission",
    )
    unavailable_reason = _nonempty_string(
        row.get("unavailable_reason"), f"{name}.unavailable_reason"
    )
    if unavailable_reason != "v3_test_only_contract_not_production_ready":
        raise ValueError("v3 test unavailable_reason is malformed")
    return {
        "status": "partial",
        "rules_source": "stock-installation-static-manifest",
        "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
        "required_state_refs": {
            "count": PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
            "sha256": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
        },
        "state_ref_coverage": coverage,
        "scope_mode": "hypothetical_precontact_offline_ast",
        "characters": characters,
        "armies": armies,
        "sides": sides,
        "global_state_refs": global_refs,
        "advantage_model": advantage,
        "row_evaluations": dict(evaluations),
        "offline_admission": admission,
        "unavailable_reason": unavailable_reason,
    }


def _normalize_phase_character_v3_test_only(
    value: object,
    *,
    name: str,
    expected: dict[str, object],
    required_ref_paths: set[str],
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "character_id",
            "source_army_id",
            "source_regiment_id",
            "encounter_role",
            "phase_roles",
            "state_refs",
        },
        name,
    )
    character_id = _positive_int32_id(row.get("character_id"), f"{name}.character_id")
    source_army_id = _positive_int32_id(row.get("source_army_id"), f"{name}.source_army_id")
    if (
        character_id != expected["character_id"]
        or source_army_id != expected["source_army_id"]
        or row.get("encounter_role") != expected["encounter_role"]
    ):
        raise ValueError("v3 phase character identity/role mismatch")
    roles = _array(row.get("phase_roles"), f"{name}.phase_roles")
    if roles != expected["phase_roles"]:
        raise ValueError("v3 phase character roles are malformed")
    regiment_id = row.get("source_regiment_id")
    expected_regiment_id = expected["source_regiment_id"]
    if expected_regiment_id is None:
        if regiment_id is not None:
            raise ValueError("commander-only v3 row must not invent a RegimentID")
    elif _positive_int32_id(regiment_id, f"{name}.source_regiment_id") != expected_regiment_id:
        raise ValueError("v3 knight RegimentID mismatch")
    refs = _normalize_state_refs_v3_test_only(
        row.get("state_refs"),
        name=f"{name}.state_refs",
        required_paths=required_ref_paths,
    )
    return {
        "character_id": character_id,
        "source_army_id": source_army_id,
        "source_regiment_id": expected_regiment_id,
        "encounter_role": expected["encounter_role"],
        "phase_roles": list(expected["phase_roles"]),
        "state_refs": refs,
    }


_V3_REQUIRED_ARMY_REF_PATHS = {
    "army.maa_regiment_count_raw",
}


def _normalize_phase_army_v3_test_only(
    value: object, *, name: str, expected: dict[str, object]
) -> dict[str, object]:
    row = _exact_object(
        value,
        {"army_id", "encounter_role", "state_refs"},
        name,
    )
    army_id = _positive_int32_id(row.get("army_id"), f"{name}.army_id")
    if (
        army_id != expected.get("army_id")
        or row.get("encounter_role") != expected.get("encounter_role")
    ):
        raise ValueError("v3 phase army identity/role mismatch")
    return {
        "army_id": army_id,
        "encounter_role": expected["encounter_role"],
        "state_refs": _normalize_state_refs_v3_test_only(
            row.get("state_refs"),
            name=f"{name}.state_refs",
            required_paths=_V3_REQUIRED_ARMY_REF_PATHS,
        ),
    }


def _normalize_phase_sides_v3_test_only(
    value: object,
    *,
    name: str,
    base_inputs: dict[str, object],
    characters: list[dict[str, object]],
    required_ref_paths: set[str],
) -> list[dict[str, object]]:
    raw_sides = _array(value, name)
    if len(raw_sides) != 2:
        raise ValueError("v3 phase inputs require exactly two sides")
    scenario = base_inputs["scenario"]
    assert isinstance(scenario, dict)
    expected_armies = [
        scenario["attacker_army_ids"],
        scenario["defender_army_ids"],
    ]
    expected_roles = ["attacker", "defender"]
    normalized: list[dict[str, object]] = []
    for side_index, raw_side in enumerate(raw_sides):
        side_name = f"{name}[{side_index}]"
        row = _exact_object(
            raw_side,
            {
                "side_index",
                "encounter_role",
                "ordered_army_ids",
                "ordered_character_ids",
                "primary_participant_character_id",
                "primary_source_army_id",
                "primary_selection_policy",
                "side_strength_raw",
                "side_strength_scale",
                "side_army_size_raw",
                "side_army_size_scale",
                "state_refs",
            },
            side_name,
        )
        if row.get("side_index") != side_index or row.get("encounter_role") != expected_roles[side_index]:
            raise ValueError("v3 side index/role is malformed")
        army_ids = _positive_id_array(
            row.get("ordered_army_ids"), f"{side_name}.ordered_army_ids"
        )
        if army_ids != expected_armies[side_index]:
            raise ValueError("v3 side army order changed request order")
        expected_character_ids = [
            int(character["character_id"])
            for character in characters
            if character["encounter_role"] == expected_roles[side_index]
        ]
        character_ids = _positive_id_array(
            row.get("ordered_character_ids"),
            f"{side_name}.ordered_character_ids",
        )
        if character_ids != expected_character_ids:
            raise ValueError("v3 side character order is malformed")
        primary_participant_id = _positive_int32_id(
            row.get("primary_participant_character_id"),
            f"{side_name}.primary_participant_character_id",
        )
        primary_source_army_id = _positive_int32_id(
            row.get("primary_source_army_id"),
            f"{side_name}.primary_source_army_id",
        )
        if primary_source_army_id != army_ids[0]:
            raise ValueError("v3 side primary source changed request order")
        if row.get("primary_selection_policy") != (
            "first_inserted_army_owner_with_native_preservation"
        ):
            raise ValueError("v3 side primary selection policy is malformed")
        side_strength_raw = _signed_int32(
            row.get("side_strength_raw"), f"{side_name}.side_strength_raw"
        )
        _fixed_scale(
            row.get("side_strength_scale"), f"{side_name}.side_strength_scale"
        )
        side_army_size_raw = _non_negative_int64(
            row.get("side_army_size_raw"),
            f"{side_name}.side_army_size_raw",
        )
        _fixed_scale(
            row.get("side_army_size_scale"),
            f"{side_name}.side_army_size_scale",
        )
        state_refs = _normalize_state_refs_v3_test_only(
            row.get("state_refs"),
            name=f"{side_name}.state_refs",
            required_paths=required_ref_paths,
        )
        refs_by_path = {ref["path"]: ref for ref in state_refs}
        if (
            refs_by_path["side.side_strength_raw"]["value"]
            != side_strength_raw
            or refs_by_path["side.side_army_size_raw"]["value"]
            != side_army_size_raw
        ):
            raise ValueError("v3 side exact helper fields disagree with state refs")
        normalized.append(
            {
                "side_index": side_index,
                "encounter_role": expected_roles[side_index],
                "ordered_army_ids": army_ids,
                "ordered_character_ids": character_ids,
                "primary_participant_character_id": primary_participant_id,
                "primary_source_army_id": primary_source_army_id,
                "primary_selection_policy": (
                    "first_inserted_army_owner_with_native_preservation"
                ),
                "side_strength_raw": side_strength_raw,
                "side_strength_scale": CK3_COMBAT_FIXED_POINT_SCALE,
                "side_army_size_raw": side_army_size_raw,
                "side_army_size_scale": CK3_COMBAT_FIXED_POINT_SCALE,
                "state_refs": state_refs,
            }
        )
    return normalized


def _normalize_state_refs_v3_test_only(
    value: object, *, name: str, required_paths: set[str]
) -> list[dict[str, object]]:
    raw_refs = _array(value, name)
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw_ref in enumerate(raw_refs):
        ref_name = f"{name}[{index}]"
        ref = _exact_object(
            raw_ref, {"path", "value_type", "value"}, ref_name
        )
        path = _nonempty_string(ref.get("path"), f"{ref_name}.path")
        if path in seen:
            raise ValueError("v3 state refs contain duplicate paths")
        seen.add(path)
        value_type = ref.get("value_type")
        expected_value_type = _v3_closed_state_ref_value_type(path)
        if value_type != expected_value_type:
            raise ValueError(
                f"v3 closed state ref {path} requires {expected_value_type}"
            )
        raw_value = ref.get("value")
        if value_type == "bool":
            normalized_value: object = _strict_bool(raw_value, f"{ref_name}.value")
        elif value_type == "signed_int32":
            normalized_value = _signed_int32(raw_value, f"{ref_name}.value")
        elif value_type == "signed_int64":
            normalized_value = _signed_int64(raw_value, f"{ref_name}.value")
        elif value_type == "signed_q100000":
            normalized_value = _signed_int64(raw_value, f"{ref_name}.value")
        elif value_type == "full_id":
            normalized_value = _positive_int32_id(raw_value, f"{ref_name}.value")
        elif value_type == "full_id_array":
            normalized_value = _positive_id_array(raw_value, f"{ref_name}.value")
        elif value_type == "string":
            normalized_value = _nonempty_string(raw_value, f"{ref_name}.value")
        elif value_type == "not_applicable":
            normalized_value = _nonempty_string(raw_value, f"{ref_name}.value")
        else:
            raise ValueError("v3 state ref value_type is malformed")
        normalized.append(
            {"path": path, "value_type": value_type, "value": normalized_value}
        )
    if seen != required_paths:
        missing = sorted(required_paths - seen)
        extra = sorted(seen - required_paths)
        raise ValueError(
            f"v3 state ref coverage mismatch: missing={missing}, extra={extra}"
        )
    return normalized


def _v3_closed_state_ref_value_type(path: str) -> str:
    if path in {
        "root.skills.martial_raw",
        "root.skills.learning_raw",
        "root.skills.prowess_raw",
    }:
        return "signed_int32"
    if path in {
        "side.character_membership",
        "side.ordered_enemy_knights",
    }:
        return "full_id_array"
    if path == "side.commander":
        return "full_id"
    if path.endswith("_raw"):
        return "signed_q100000"
    return "bool"


def _normalize_advantage_model_v3_test_only(
    value: object, *, name: str
) -> dict[str, object]:
    """Validate the no-CombatID temporary-shell advantage wire.

    An available row is all-or-nothing: the native helper totals, independent
    component calls, checked arithmetic and ``shell+0x710`` must agree.  The
    unavailable branch intentionally carries no partial numeric model that a
    planner could accidentally mix with a later observation.
    """
    row = _exact_object(
        value,
        {
            "status",
            "scale",
            "scenario_policy",
            "observation_origin",
            "side_inputs",
            "constructor_call_order",
            "constructor_sources",
            "base_static_accumulator_raw",
            "resolved_dynamic",
            "unavailable_reason",
        },
        name,
    )
    if _fixed_scale(row.get("scale"), f"{name}.scale") != CK3_COMBAT_FIXED_POINT_SCALE:
        raise AssertionError("unreachable fixed scale mismatch")
    if row.get("scenario_policy") != (
        "explicit_hypothetical_fixed_at_contact_no_reinforcements"
    ):
        raise ValueError("v3 advantage scenario policy is malformed")
    origin = row.get("observation_origin")
    if origin not in {
        "independent_synthetic_contract_fixture",
        "native_exact_build_test_only",
    }:
        raise ValueError("v3 advantage observation origin is malformed")
    if row.get("constructor_call_order") != _V3_CONSTRUCTOR_CALL_ORDER:
        raise ValueError("v3 advantage constructor call order is malformed")
    status = row.get("status")
    if status == "unavailable":
        if any(
            row.get(key) is not None
            for key in (
                "side_inputs",
                "constructor_sources",
                "base_static_accumulator_raw",
                "resolved_dynamic",
            )
        ):
            raise ValueError(
                "unavailable v3 advantage model must not publish partial values"
            )
        reason = _nonempty_string(
            row.get("unavailable_reason"), f"{name}.unavailable_reason"
        )
        return {
            "status": "unavailable",
            "scale": CK3_COMBAT_FIXED_POINT_SCALE,
            "scenario_policy": row["scenario_policy"],
            "observation_origin": origin,
            "side_inputs": None,
            "constructor_call_order": list(_V3_CONSTRUCTOR_CALL_ORDER),
            "constructor_sources": None,
            "base_static_accumulator_raw": None,
            "resolved_dynamic": None,
            "unavailable_reason": reason,
        }
    if status != "available" or row.get("unavailable_reason") is not None:
        raise ValueError("v3 advantage model status is malformed")

    side_inputs = _normalize_advantage_side_inputs_v3_test_only(
        row.get("side_inputs"), name=f"{name}.side_inputs"
    )
    constructor_sources, accumulator = (
        _normalize_advantage_constructor_sources_v3_test_only(
            row.get("constructor_sources"),
            name=f"{name}.constructor_sources",
        )
    )
    base_static = _signed_int64(
        row.get("base_static_accumulator_raw"),
        f"{name}.base_static_accumulator_raw",
    )
    if base_static != accumulator:
        raise ValueError("v3 base static advantage disagrees with source ledger")
    resolved_dynamic = _normalize_resolved_dynamic_v3_test_only(
        row.get("resolved_dynamic"),
        name=f"{name}.resolved_dynamic",
        base_static_accumulator_raw=base_static,
    )
    return {
        "status": "available",
        "scale": CK3_COMBAT_FIXED_POINT_SCALE,
        "scenario_policy": row["scenario_policy"],
        "observation_origin": origin,
        "side_inputs": side_inputs,
        "constructor_call_order": list(_V3_CONSTRUCTOR_CALL_ORDER),
        "constructor_sources": constructor_sources,
        "base_static_accumulator_raw": base_static,
        "resolved_dynamic": resolved_dynamic,
        "unavailable_reason": None,
    }


def _normalize_advantage_side_inputs_v3_test_only(
    value: object, *, name: str
) -> list[dict[str, object]]:
    rows = _array(value, name)
    if len(rows) != 2:
        raise ValueError("v3 advantage model requires exactly two side inputs")
    normalized: list[dict[str, object]] = []
    for side_index, expected_side in enumerate(("attacker", "defender")):
        side_name = f"{name}[{side_index}]"
        row = _exact_object(
            rows[side_index],
            {
                "side",
                "primary_army_id",
                "ordered_army_ids",
                "supply",
                "primary_army_gathering_raw",
                "owner_character_id",
                "owner_debt_selector_raw",
                "treasury_debt_selector_raw",
            },
            side_name,
        )
        if row.get("side") != expected_side:
            raise ValueError("v3 advantage side input order is malformed")
        ordered_armies = _positive_id_array(
            row.get("ordered_army_ids"), f"{side_name}.ordered_army_ids"
        )
        primary_army = _positive_int32_id(
            row.get("primary_army_id"), f"{side_name}.primary_army_id"
        )
        if primary_army != ordered_armies[0]:
            raise ValueError("v3 advantage primary army changed request order")
        supply = _exact_object(
            row.get("supply"),
            {
                "selected_key",
                "selected_effect_identity",
                "selected_effect_points",
                "eligible_soldiers_total",
                "eligible_soldiers_supplied",
                "eligible_soldiers_running_low",
                "eligible_soldiers_starving",
            },
            f"{side_name}.supply",
        )
        selected_key = _nonempty_string(
            supply.get("selected_key"), f"{side_name}.supply.selected_key"
        )
        if selected_key not in {
            "supply_state_supplied_advantage",
            "supply_state_running_low_advantage",
            "supply_state_starving_advantage",
        }:
            raise ValueError("v3 supply selected key is malformed")
        supply_counts = {
            key: _non_negative_int64(
                supply.get(key), f"{side_name}.supply.{key}"
            )
            for key in (
                "eligible_soldiers_total",
                "eligible_soldiers_supplied",
                "eligible_soldiers_running_low",
                "eligible_soldiers_starving",
            )
        }
        if supply_counts["eligible_soldiers_total"] != sum(
            supply_counts[key]
            for key in (
                "eligible_soldiers_supplied",
                "eligible_soldiers_running_low",
                "eligible_soldiers_starving",
            )
        ):
            raise ValueError("v3 supply eligible-soldier totals disagree")
        total = supply_counts["eligible_soldiers_total"]
        supplied = supply_counts["eligible_soldiers_supplied"]
        running_low = supply_counts["eligible_soldiers_running_low"]
        if total <= 0 or supplied * 2 > total:
            expected_supply_key = "supply_state_supplied_advantage"
        elif (supplied + running_low) * 2 > total:
            expected_supply_key = "supply_state_running_low_advantage"
        else:
            expected_supply_key = "supply_state_starving_advantage"
        if selected_key != expected_supply_key:
            raise ValueError("v3 supply strict-majority selection is malformed")
        treasury_selector = row.get("treasury_debt_selector_raw")
        if treasury_selector is not None:
            treasury_selector = _signed_int32(
                treasury_selector, f"{side_name}.treasury_debt_selector_raw"
            )
        normalized.append(
            {
                "side": expected_side,
                "primary_army_id": primary_army,
                "ordered_army_ids": ordered_armies,
                "supply": {
                    "selected_key": selected_key,
                    "selected_effect_identity": _nonempty_string(
                        supply.get("selected_effect_identity"),
                        f"{side_name}.supply.selected_effect_identity",
                    ),
                    "selected_effect_points": _signed_int32(
                        supply.get("selected_effect_points"),
                        f"{side_name}.supply.selected_effect_points",
                    ),
                    **supply_counts,
                },
                "primary_army_gathering_raw": _signed_int32(
                    row.get("primary_army_gathering_raw"),
                    f"{side_name}.primary_army_gathering_raw",
                ),
                "owner_character_id": _positive_int32_id(
                    row.get("owner_character_id"),
                    f"{side_name}.owner_character_id",
                ),
                "owner_debt_selector_raw": _signed_int32(
                    row.get("owner_debt_selector_raw"),
                    f"{side_name}.owner_debt_selector_raw",
                ),
                "treasury_debt_selector_raw": treasury_selector,
            }
        )
    return normalized


_V3_ADVANTAGE_STAGE_SIDES = {
    stage: ("defender" if stage in {
        "defender_adjacency",
        "defender_terrain",
        "supply_1",
        "holding_defender_1",
        "gathering_army_1",
        "debt_1_owner",
        "debt_1_treasury",
        "unreformed_faith_1",
    } else "attacker")
    for stage in _V3_ADVANTAGE_SOURCE_ORDER
}


def _normalize_advantage_constructor_sources_v3_test_only(
    value: object, *, name: str
) -> tuple[list[dict[str, object]], int]:
    rows = _array(value, name)
    if len(rows) < len(_V3_ADVANTAGE_SOURCE_ORDER):
        raise ValueError("v3 advantage source ledger omits a constructor stage")
    stage_indexes = {stage: index for index, stage in enumerate(_V3_ADVANTAGE_SOURCE_ORDER)}
    seen_stages: set[str] = set()
    prior_stage_index = -1
    next_append_order = 0
    accumulator = 0
    normalized: list[dict[str, object]] = []
    for index, raw_source in enumerate(rows):
        source_name = f"{name}[{index}]"
        source = _exact_object(
            raw_source,
            {
                "stage_order",
                "append_order",
                "stage",
                "side",
                "source_key",
                "effect_advantage_points",
                "scale_raw",
                "signed_contribution_raw",
                "accumulator_before_raw",
                "accumulator_after_raw",
                "selected",
                "applied",
                "skip_reason",
            },
            source_name,
        )
        if source.get("stage_order") != index:
            raise ValueError("v3 advantage stage_order is malformed")
        stage = source.get("stage")
        if not isinstance(stage, str) or stage not in stage_indexes:
            raise ValueError("v3 advantage source stage is malformed")
        stage_index = stage_indexes[stage]
        if stage_index < prior_stage_index:
            raise ValueError("v3 advantage source stages changed native order")
        prior_stage_index = stage_index
        seen_stages.add(stage)
        expected_side = _V3_ADVANTAGE_STAGE_SIDES[stage]
        if source.get("side") != expected_side:
            raise ValueError("v3 advantage source side is malformed")
        selected = _strict_bool(source.get("selected"), f"{source_name}.selected")
        applied = _strict_bool(source.get("applied"), f"{source_name}.applied")
        if applied and not selected:
            raise ValueError("v3 advantage source cannot apply when unselected")
        source_key = source.get("source_key")
        effect_points = source.get("effect_advantage_points")
        if selected:
            source_key = _nonempty_string(source_key, f"{source_name}.source_key")
            effect_points = _signed_int32(
                effect_points, f"{source_name}.effect_advantage_points"
            )
        elif source_key is not None or effect_points is not None:
            raise ValueError("unselected v3 advantage source must not invent an effect")
        scale_raw = _signed_int64(
            source.get("scale_raw"), f"{source_name}.scale_raw"
        )
        expected_contribution = (
            int(effect_points) * scale_raw if applied else 0
        )
        if expected_side == "defender":
            expected_contribution = -expected_contribution
        contribution = _signed_int64(
            source.get("signed_contribution_raw"),
            f"{source_name}.signed_contribution_raw",
        )
        if contribution != expected_contribution:
            raise ValueError("v3 advantage signed contribution is malformed")
        if _signed_int64(
            source.get("accumulator_before_raw"),
            f"{source_name}.accumulator_before_raw",
        ) != accumulator:
            raise ValueError("v3 advantage accumulator_before is malformed")
        accumulator = max(-10_000_000, min(10_000_000, accumulator + contribution))
        if _signed_int64(
            source.get("accumulator_after_raw"),
            f"{source_name}.accumulator_after_raw",
        ) != accumulator:
            raise ValueError("v3 advantage per-source clamp is malformed")
        append_order = source.get("append_order")
        if applied:
            if append_order != next_append_order:
                raise ValueError("v3 advantage append_order is malformed")
            next_append_order += 1
        elif append_order is not None:
            raise ValueError("non-applied v3 source must have null append_order")
        skip_reason = source.get("skip_reason")
        if applied:
            if skip_reason is not None:
                raise ValueError("applied v3 source must not have a skip_reason")
        else:
            skip_reason = _nonempty_string(
                skip_reason, f"{source_name}.skip_reason"
            )
        normalized.append(
            {
                "stage_order": index,
                "append_order": append_order,
                "stage": stage,
                "side": expected_side,
                "source_key": source_key,
                "effect_advantage_points": effect_points,
                "scale_raw": scale_raw,
                "signed_contribution_raw": contribution,
                "accumulator_before_raw": _signed_int64(
                    source.get("accumulator_before_raw"),
                    f"{source_name}.accumulator_before_raw",
                ),
                "accumulator_after_raw": accumulator,
                "selected": selected,
                "applied": applied,
                "skip_reason": skip_reason,
            }
        )
    if seen_stages != set(_V3_ADVANTAGE_SOURCE_ORDER):
        raise ValueError("v3 advantage source ledger stage coverage is malformed")
    return normalized, accumulator


def _normalize_resolved_dynamic_v3_test_only(
    value: object, *, name: str, base_static_accumulator_raw: int
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "helper_status",
            "context_mode",
            "roll_policy",
            "sides",
            "side_0_dynamic_raw",
            "side_1_dynamic_raw",
            "resolved_advantage_at_zero_roll_raw",
            "original_total_helper_raw",
            "original_total_helper_match",
        },
        name,
    )
    if row.get("status") != "available" or row.get("helper_status") != (
        "original_helpers_matched"
    ):
        raise ValueError("v3 resolved dynamic helper status is malformed")
    if row.get("context_mode") != "temporary_unregistered_local_context":
        raise ValueError("v3 resolved dynamic context mode is malformed")
    if row.get("roll_policy") != "zero_in_query_sampled_offline":
        raise ValueError("v3 resolved dynamic roll policy is malformed")
    raw_sides = _array(row.get("sides"), f"{name}.sides")
    if len(raw_sides) != 2:
        raise ValueError("v3 resolved dynamic requires exactly two sides")
    sides: list[dict[str, object]] = []
    side_totals: list[int] = []
    for side_index, expected_side in enumerate(("attacker", "defender")):
        side_name = f"{name}.sides[{side_index}]"
        side = _exact_object(
            raw_sides[side_index],
            {
                "side",
                "battle_commander_character_id",
                "battle_commander_selected",
                "battle_commander_selection",
                "primary_army_gathering_raw",
                "gathering",
                "relation_kind_raw",
                "roll_points",
                "roll_raw",
                "target_conditionals_residual_raw",
                "commander_dynamic_raw",
                "side_dynamic_raw",
                "side_total_raw",
                "contribution_to_resolved_raw",
            },
            side_name,
        )
        if side.get("side") != expected_side:
            raise ValueError("v3 resolved dynamic side order is malformed")
        selected = _strict_bool(
            side.get("battle_commander_selected"),
            f"{side_name}.battle_commander_selected",
        )
        commander_id = side.get("battle_commander_character_id")
        if selected:
            commander_id = _positive_int32_id(
                commander_id, f"{side_name}.battle_commander_character_id"
            )
        elif commander_id is not None:
            raise ValueError("absent v3 battle commander must have a null ID")
        if side.get("battle_commander_selection") != "native_0x23C8A60":
            raise ValueError("v3 battle commander selection provenance is malformed")
        gathering_raw = _signed_int32(
            side.get("primary_army_gathering_raw"),
            f"{side_name}.primary_army_gathering_raw",
        )
        gathering = _strict_bool(side.get("gathering"), f"{side_name}.gathering")
        if gathering is not (gathering_raw > 0):
            raise ValueError("v3 gathering bool disagrees with CArmy+0x1D0")
        roll_points = _signed_int32(
            side.get("roll_points"), f"{side_name}.roll_points"
        )
        roll_raw = _signed_int64(side.get("roll_raw"), f"{side_name}.roll_raw")
        if roll_points != 0 or roll_raw != 0:
            raise ValueError("v3 precontact dynamic query must use zero rolls")
        residual = _signed_int64(
            side.get("target_conditionals_residual_raw"),
            f"{side_name}.target_conditionals_residual_raw",
        )
        commander_dynamic = _signed_int64(
            side.get("commander_dynamic_raw"),
            f"{side_name}.commander_dynamic_raw",
        )
        if not selected and commander_dynamic != 0:
            raise ValueError("absent v3 battle commander has nonzero contribution")
        side_dynamic = _signed_int64(
            side.get("side_dynamic_raw"), f"{side_name}.side_dynamic_raw"
        )
        side_total = _signed_int64(
            side.get("side_total_raw"), f"{side_name}.side_total_raw"
        )
        expected_total = roll_raw + residual + commander_dynamic + side_dynamic
        if side_total != expected_total:
            raise ValueError("v3 resolved dynamic component sum is malformed")
        expected_contribution = side_total if side_index == 0 else -side_total
        contribution = _signed_int64(
            side.get("contribution_to_resolved_raw"),
            f"{side_name}.contribution_to_resolved_raw",
        )
        if contribution != expected_contribution:
            raise ValueError("v3 resolved dynamic side sign is malformed")
        side_totals.append(side_total)
        sides.append(
            {
                "side": expected_side,
                "battle_commander_character_id": commander_id,
                "battle_commander_selected": selected,
                "battle_commander_selection": "native_0x23C8A60",
                "primary_army_gathering_raw": gathering_raw,
                "gathering": gathering,
                "relation_kind_raw": _signed_int32(
                    side.get("relation_kind_raw"),
                    f"{side_name}.relation_kind_raw",
                ),
                "roll_points": 0,
                "roll_raw": 0,
                "target_conditionals_residual_raw": residual,
                "commander_dynamic_raw": commander_dynamic,
                "side_dynamic_raw": side_dynamic,
                "side_total_raw": side_total,
                "contribution_to_resolved_raw": contribution,
            }
        )
    side_0 = _signed_int64(
        row.get("side_0_dynamic_raw"), f"{name}.side_0_dynamic_raw"
    )
    side_1 = _signed_int64(
        row.get("side_1_dynamic_raw"), f"{name}.side_1_dynamic_raw"
    )
    if [side_0, side_1] != side_totals:
        raise ValueError("v3 resolved dynamic side totals disagree")
    resolved = _signed_int64(
        row.get("resolved_advantage_at_zero_roll_raw"),
        f"{name}.resolved_advantage_at_zero_roll_raw",
    )
    expected_resolved = base_static_accumulator_raw + side_0 - side_1
    if resolved != expected_resolved:
        raise ValueError("v3 zero-roll resolved advantage is malformed")
    original = _signed_int64(
        row.get("original_total_helper_raw"),
        f"{name}.original_total_helper_raw",
    )
    if (
        _strict_bool(
            row.get("original_total_helper_match"),
            f"{name}.original_total_helper_match",
        )
        is not True
        or original != resolved
    ):
        raise ValueError("v3 original total helper equality is malformed")
    return {
        "status": "available",
        "helper_status": "original_helpers_matched",
        "context_mode": "temporary_unregistered_local_context",
        "roll_policy": "zero_in_query_sampled_offline",
        "sides": sides,
        "side_0_dynamic_raw": side_0,
        "side_1_dynamic_raw": side_1,
        "resolved_advantage_at_zero_roll_raw": resolved,
        "original_total_helper_raw": original,
        "original_total_helper_match": True,
    }


def _normalize_phase_offline_admission_v3_test_only(
    value: object, *, name: str
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "raw_state_ref_contract_complete",
            "advantage_model_contract_complete",
            "native_raw_state_refs_ready",
            "native_advantage_model_ready",
            "loaded_playset_verified",
            "ast_evaluator_ready",
            "ready",
            "missing_required_domains",
        },
        name,
    )
    if (
        _strict_bool(
            row.get("raw_state_ref_contract_complete"),
            f"{name}.raw_state_ref_contract_complete",
        )
        is not True
        or _strict_bool(
            row.get("advantage_model_contract_complete"),
            f"{name}.advantage_model_contract_complete",
        )
        is not True
        or _strict_bool(
            row.get("native_raw_state_refs_ready"),
            f"{name}.native_raw_state_refs_ready",
        )
        is not False
        or _strict_bool(
            row.get("native_advantage_model_ready"),
            f"{name}.native_advantage_model_ready",
        )
        is not False
        or _strict_bool(row.get("loaded_playset_verified"), f"{name}.loaded_playset_verified")
        is not False
        or _strict_bool(row.get("ast_evaluator_ready"), f"{name}.ast_evaluator_ready")
        is not False
        or _strict_bool(row.get("ready"), f"{name}.ready") is not False
    ):
        raise ValueError("v3 test offline admission falsely claims readiness")
    domains = [
        _nonempty_string(item, f"{name}.missing_required_domains[{index}]")
        for index, item in enumerate(
            _array(
                row.get("missing_required_domains"),
                f"{name}.missing_required_domains",
            )
        )
    ]
    if domains != _V3_TEST_ONLY_BLOCKERS:
        raise ValueError("v3 test offline admission blockers are malformed")
    return {
        "raw_state_ref_contract_complete": True,
        "advantage_model_contract_complete": True,
        "native_raw_state_refs_ready": False,
        "native_advantage_model_ready": False,
        "loaded_playset_verified": False,
        "ast_evaluator_ready": False,
        "ready": False,
        "missing_required_domains": list(_V3_TEST_ONLY_BLOCKERS),
    }


def _normalize_v3_test_completeness(
    value: object,
    *,
    base_inputs: dict[str, object],
    phase: dict[str, object],
) -> dict[str, object]:
    name = "combat_simulation_inputs_v3_test_only.completeness"
    row = _exact_object(
        value,
        {
            "observation_slice",
            "base_input_observation_ready",
            "phase_raw_observation_ready",
            "offline_ast_admission_ready",
            "input_observation_ready",
            "monte_carlo_ready",
            "missing_required_domains",
        },
        name,
    )
    if row.get("observation_slice") != "precontact-phase-event-inputs-v3-test-only":
        raise ValueError("v3 test observation_slice is malformed")
    expected_bools = {
        "base_input_observation_ready": True,
        "phase_raw_observation_ready": False,
        "offline_ast_admission_ready": False,
        "input_observation_ready": False,
        "monte_carlo_ready": False,
    }
    for key, expected in expected_bools.items():
        if _strict_bool(row.get(key), f"{name}.{key}") is not expected:
            raise ValueError("v3 test completeness falsely claims readiness")
    assert base_inputs["completeness"]["input_observation_ready"] is True
    assert phase["offline_admission"]["ready"] is False
    # Damage/casualty, pursuit and battle-end kernels are already frozen in
    # the simulator.  A native observation payload does not need to serialize
    # those algorithms, so only genuinely open v3 observation/effect gates
    # belong in this readiness list.
    expected_domains = list(_V3_TEST_ONLY_BLOCKERS)
    domains = [
        _nonempty_string(item, f"{name}.missing_required_domains[{index}]")
        for index, item in enumerate(
            _array(
                row.get("missing_required_domains"),
                f"{name}.missing_required_domains",
            )
        )
    ]
    if domains != expected_domains:
        raise ValueError("v3 test completeness blockers are malformed")
    return {
        "observation_slice": "precontact-phase-event-inputs-v3-test-only",
        **expected_bools,
        "missing_required_domains": expected_domains,
    }


def _expected_phase_characters(
    base_inputs: dict[str, object]
) -> list[dict[str, object]]:
    armies = base_inputs.get("armies")
    assert isinstance(armies, list)
    expected: list[dict[str, object]] = []
    seen: dict[tuple[int, int], int] = {}
    for army in armies:
        assert isinstance(army, dict)
        army_id = int(army["army_id"])
        encounter_role = str(army["encounter_role"])
        commander = army.get("commander")
        if isinstance(commander, dict) and commander.get("status") == "available":
            character_id = int(commander["character_id"])
            seen[(character_id, army_id)] = len(expected)
            expected.append(
                {
                    "character_id": character_id,
                    "source_army_id": army_id,
                    "source_regiment_id": None,
                    "encounter_role": encounter_role,
                    "phase_roles": ["commander"],
                }
            )
        knights = army.get("knights")
        members = knights.get("members") if isinstance(knights, dict) else None
        if isinstance(members, list):
            for member in members:
                assert isinstance(member, dict)
                character_id = int(member["character_id"])
                key = (character_id, army_id)
                if key in seen:
                    row = expected[seen[key]]
                    row["phase_roles"] = ["commander", "knight"]
                    row["source_regiment_id"] = int(
                        member["source_regiment_id"]
                    )
                else:
                    seen[key] = len(expected)
                    expected.append(
                        {
                            "character_id": character_id,
                            "source_army_id": army_id,
                            "source_regiment_id": int(
                                member["source_regiment_id"]
                            ),
                            "encounter_role": encounter_role,
                            "phase_roles": ["knight"],
                        }
                    )
    if len(seen) != len(expected):
        raise ValueError("v2 participant roster repeats a character/army pair")
    return expected


@lru_cache(maxsize=1)
def _phase_event_manifest_required_refs() -> frozenset[str]:
    path = (
        Path(__file__).resolve().parents[1]
        / "simulation"
        / "data"
        / "ck3_1_19_0_6_stock_combat_phase_events.json"
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    claimed_hash = manifest.get("canonical_manifest_sha256")
    canonical = dict(manifest)
    canonical.pop("canonical_manifest_sha256", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if (
        claimed_hash != PHASE_EVENT_STOCK_MANIFEST_SHA256
        or hashlib.sha256(encoded).hexdigest().upper()
        != PHASE_EVENT_STOCK_MANIFEST_SHA256
    ):
        raise ValueError("phase-event stock manifest hash mismatch")
    refs = frozenset(
        ref
        for event in manifest["event_rows"]
        for ref in event["state_dependencies"]
    )
    digest = hashlib.sha256(
        json.dumps(sorted(refs), separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()
    if (
        len(refs) != PHASE_EVENT_REQUIRED_STATE_REF_COUNT
        or digest != PHASE_EVENT_REQUIRED_STATE_REFS_SHA256
    ):
        raise ValueError("phase-event required-state-ref digest mismatch")
    return refs


@lru_cache(maxsize=1)
def _phase_event_ref_coverage_v3_test_only() -> dict[str, object]:
    manifest_refs = _phase_event_manifest_required_refs()
    native_refs = _V3_NATIVE_LEAF_EXACT_REF_PATHS
    derived_refs = _V3_OFFLINE_DERIVED_EXACT_REF_PATHS
    remaining_refs = manifest_refs - native_refs - derived_refs
    if (
        len(native_refs) != 47
        or len(derived_refs) != 15
        or len(remaining_refs) != 70
        or native_refs & derived_refs
        or (native_refs | derived_refs | remaining_refs) != manifest_refs
    ):
        raise ValueError("v3 phase ref closure partition is malformed")

    def digest(paths: frozenset[str]) -> str:
        return hashlib.sha256(
            json.dumps(sorted(paths), separators=(",", ":")).encode("utf-8")
        ).hexdigest().upper()

    path_hashes = {
        "native_leaf_exact": digest(native_refs),
        "offline_derived_exact": digest(derived_refs),
        "remaining_unclosed": digest(remaining_refs),
    }
    if path_hashes != {
        "native_leaf_exact": PHASE_EVENT_NATIVE_LEAF_EXACT_REFS_SHA256,
        "offline_derived_exact": PHASE_EVENT_OFFLINE_DERIVED_EXACT_REFS_SHA256,
        "remaining_unclosed": PHASE_EVENT_REMAINING_UNCLOSED_REFS_SHA256,
    }:
        raise ValueError("v3 phase ref closure hashes are malformed")
    return {
        "manifest_domain_counts": {
            "character_relation": 79,
            "army": 13,
            "side": 10,
            "global": 3,
            "derived": 27,
        },
        "abi_level_counts": {
            "native_leaf_exact": 47,
            "offline_derived_exact": 15,
            "determinable": 62,
            "remaining_unclosed": 70,
            "production_live_observed": 0,
        },
        "path_set_sha256": path_hashes,
        "native_payload_policy": (
            "closed_native_leaves_only_offline_derived_not_serialized"
        ),
    }


def _normalize_phase_ref_coverage_v3_test_only(
    value: object, *, name: str
) -> dict[str, object]:
    expected = _phase_event_ref_coverage_v3_test_only()
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
    for section_name in (
        "manifest_domain_counts",
        "abi_level_counts",
    ):
        expected_section = expected[section_name]
        assert isinstance(expected_section, dict)
        actual_section = _exact_object(
            row.get(section_name), set(expected_section), f"{name}.{section_name}"
        )
        for key, expected_value in expected_section.items():
            if (
                type(actual_section.get(key)) is not int
                or actual_section.get(key) != expected_value
            ):
                raise ValueError("v3 phase ref coverage counts are malformed")
    expected_hashes = expected["path_set_sha256"]
    assert isinstance(expected_hashes, dict)
    hashes = _exact_object(
        row.get("path_set_sha256"),
        set(expected_hashes),
        f"{name}.path_set_sha256",
    )
    if hashes != expected_hashes or row.get("native_payload_policy") != expected.get(
        "native_payload_policy"
    ):
        raise ValueError("v3 phase ref coverage provenance is malformed")
    return copy.deepcopy(expected)


def _canonical_character_ref_paths(refs: frozenset[str]) -> set[str]:
    result: set[str] = set()
    for path in refs:
        if path.startswith("root.knight_army."):
            continue
        if path.startswith("root."):
            result.add(path)
        elif path.startswith("candidate."):
            result.add("root." + path.removeprefix("candidate."))
        elif path.startswith("selected_enemy_knight."):
            result.add(
                "root." + path.removeprefix("selected_enemy_knight.")
            )
    return result


def _canonical_side_ref_paths(refs: frozenset[str]) -> set[str]:
    result: set[str] = set()
    for path in refs:
        if path.startswith("combat_side."):
            result.add("side." + path.removeprefix("combat_side."))
        elif path.startswith("enemy_side."):
            result.add("side." + path.removeprefix("enemy_side."))
    return result


def _normalize_scenario(
    value: object,
    *,
    target_province_id: int,
    expected_attacker_entry_province_id: int,
    expected_encounter_scope: dict[str, object],
) -> dict[str, object]:
    name = "combat_simulation_inputs.scenario"
    row = _exact_object(
        value,
        {
            "kind",
            "attacker_entry_province_id",
            "attacker_army_ids",
            "defender_army_ids",
            "attacker_side",
            "defender_side",
            "attacker_position_policy",
            "defender_position_policy",
            "defender_insertion_order_policy",
            "actual_route_dependency",
        },
        name,
    )
    if row.get("kind") != "explicit_hypothetical_contact":
        raise ValueError("native combat scenario kind is malformed")
    entry = _positive_int32_id(
        row.get("attacker_entry_province_id"),
        f"{name}.attacker_entry_province_id",
    )
    expected_entry = _positive_int32_id(
        expected_attacker_entry_province_id,
        "expected_attacker_entry_province_id",
    )
    if entry != expected_entry or entry == target_province_id:
        raise ValueError("native combat attacker entry ProvinceID mismatch")
    attackers = _positive_id_array(
        row.get("attacker_army_ids"), f"{name}.attacker_army_ids"
    )
    defenders = _positive_id_array(
        row.get("defender_army_ids"), f"{name}.defender_army_ids"
    )
    if set(attackers) & set(defenders):
        raise ValueError("native combat scenario repeats an ArmyID")
    if attackers != expected_encounter_scope.get("attacker_army_ids") or (
        defenders != expected_encounter_scope.get("defender_army_ids")
    ):
        raise ValueError("native combat scenario participant partition drifted")
    attacker_side = row.get("attacker_side")
    defender_side = row.get("defender_side")
    if (
        attacker_side != expected_encounter_scope.get("attacker_side")
        or defender_side != expected_encounter_scope.get("defender_side")
        or {attacker_side, defender_side} != {"player_or_allied", "enemy"}
    ):
        raise ValueError("native combat scenario coalition orientation drifted")
    if (
        row.get("attacker_position_policy")
        != "fixed_at_entry_hypothetical"
        or row.get("defender_position_policy")
        != "fixed_at_target_hypothetical"
        or row.get("defender_insertion_order_policy")
        != "explicit_request_order_hypothetical"
        or row.get("actual_route_dependency") is not False
    ):
        raise ValueError("native combat scenario position policy is malformed")
    return {
        "kind": "explicit_hypothetical_contact",
        "attacker_entry_province_id": entry,
        "attacker_army_ids": attackers,
        "defender_army_ids": defenders,
        "attacker_side": attacker_side,
        "defender_side": defender_side,
        "attacker_position_policy": "fixed_at_entry_hypothetical",
        "defender_position_policy": "fixed_at_target_hypothetical",
        "defender_insertion_order_policy": (
            "explicit_request_order_hypothetical"
        ),
        "actual_route_dependency": False,
    }


def combat_simulation_inputs_status(value: dict[str, object]) -> str:
    completeness = value.get("completeness")
    if not isinstance(completeness, dict) or not isinstance(
        completeness.get("input_observation_ready"), bool
    ):
        raise ValueError("normalized combat completeness is missing")
    return (
        "available"
        if completeness["input_observation_ready"] is True
        else "partial"
    )


def _normalize_combat_army(
    value: object,
    *,
    name: str,
    target_province_id: int,
    expected_scope: dict[str, object],
    expected_encounter_role: str,
    input_gaps: set[str],
    seen_regiment_ids: set[int],
    seen_knight_ids: set[int],
    seen_knight_regiment_ids: set[int],
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "army_id",
            "encounter_role",
            "native_carmy_id",
            "scope_role",
            "war_ids",
            "current_province_id",
            "owner",
            "commander",
            "regiments",
            "knights",
            "unavailable_reason",
        },
        name,
    )
    status = _available_status(row.get("status"), f"{name}.status")
    army_id = _positive_int32_id(row.get("army_id"), f"{name}.army_id")
    expected_army_id = _positive_int32_id(
        expected_scope.get("army_id"), f"{name}.expected_army_id"
    )
    if army_id != expected_army_id:
        raise ValueError(f"native {name}.army_id changed request order")
    encounter_role = row.get("encounter_role")
    if encounter_role != expected_encounter_role:
        raise ValueError(f"native {name}.encounter_role is malformed")
    scope_role = row.get("scope_role")
    if scope_role not in {
        "player",
        "active_war_ally",
        "active_war_enemy",
    } or scope_role != expected_scope.get("scope_role"):
        raise ValueError(f"native {name}.scope_role is malformed")
    war_ids = _positive_id_array(row.get("war_ids"), f"{name}.war_ids")
    if war_ids != expected_scope.get("war_ids"):
        raise ValueError(f"native {name}.war_ids drifted from paused scope")
    native_carmy_id = _optional_positive_int32_id(
        row.get("native_carmy_id"), f"{name}.native_carmy_id"
    )
    current_province_id = _optional_positive_int32_id(
        row.get("current_province_id"), f"{name}.current_province_id"
    )
    reason = _status_reason(status, row.get("unavailable_reason"), name)
    owner = _normalize_owner(row.get("owner"), name=f"{name}.owner")
    commander = _normalize_commander(
        row.get("commander"),
        name=f"{name}.commander",
        target_province_id=target_province_id,
    )
    raw_regiments = row.get("regiments")
    if raw_regiments is None:
        regiments = None
        input_gaps.add("regiment_composition")
    else:
        regiments = []
        for index, raw_regiment in enumerate(
            _array(raw_regiments, f"{name}.regiments")
        ):
            regiment = _normalize_regiment(
                raw_regiment,
                name=f"{name}.regiments[{index}]",
                target_province_id=target_province_id,
                input_gaps=input_gaps,
            )
            regiment_id = int(regiment["regiment_id"])
            if regiment_id in seen_regiment_ids:
                raise ValueError("native combat repeats a RegimentID")
            seen_regiment_ids.add(regiment_id)
            regiments.append(regiment)
    knights = _normalize_knights(
        row.get("knights"),
        name=f"{name}.knights",
        native_carmy_id=native_carmy_id,
        regiment_ids={
            int(regiment["regiment_id"])
            for regiment in regiments or []
        },
        input_gaps=input_gaps,
        seen_knight_ids=seen_knight_ids,
        seen_knight_regiment_ids=seen_knight_regiment_ids,
    )
    if (
        status != "available"
        or native_carmy_id is None
        or owner["status"] != "available"
    ):
        input_gaps.add("army_identity_and_owner")
    if (
        commander["status"] == "unavailable"
        or commander["battle_context"]["status"] != "available"
    ):
        input_gaps.add("commander_and_roll_bounds")
    if status == "available" and (
        native_carmy_id is None
        or regiments is None
    ):
        raise ValueError(f"native available {name} is incomplete")
    return {
        "status": status,
        "army_id": army_id,
        "encounter_role": encounter_role,
        "native_carmy_id": native_carmy_id,
        "scope_role": scope_role,
        "war_ids": war_ids,
        "current_province_id": current_province_id,
        "owner": owner,
        "commander": commander,
        "regiments": regiments,
        "knights": knights,
        "unavailable_reason": reason,
    }


def _normalize_owner(value: object, *, name: str) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "character_id",
            "counter_efficiency_raw",
            "counter_resistance_raw",
            "scale",
            "unavailable_reason",
        },
        name,
    )
    status = _tri_status(row.get("status"), f"{name}.status")
    if status == "absent":
        raise ValueError(f"native {name}.status cannot be absent")
    available = status == "available"
    character_id = _conditional_non_negative_int32_id(
        row.get("character_id"), available, f"{name}.character_id"
    )
    efficiency = _conditional_signed_int64(
        row.get("counter_efficiency_raw"),
        available,
        f"{name}.counter_efficiency_raw",
    )
    resistance = _conditional_signed_int64(
        row.get("counter_resistance_raw"),
        available,
        f"{name}.counter_resistance_raw",
    )
    _fixed_scale(row.get("scale"), f"{name}.scale")
    return {
        "status": status,
        "character_id": character_id,
        "counter_efficiency_raw": efficiency,
        "counter_resistance_raw": resistance,
        "scale": CK3_COMBAT_FIXED_POINT_SCALE,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_commander(
    value: object,
    *,
    name: str,
    target_province_id: int,
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "character_id",
            "generic_advantage_points",
            "battle_context",
            "unavailable_reason",
        },
        name,
    )
    status = _tri_status(row.get("status"), f"{name}.status")
    available = status == "available"
    character_id = _conditional_non_negative_int32_id(
        row.get("character_id"), available, f"{name}.character_id"
    )
    generic_advantage = _conditional_signed_int32(
        row.get("generic_advantage_points"),
        available,
        f"{name}.generic_advantage_points",
    )
    context = _exact_object(
        row.get("battle_context"),
        {
            "status",
            "source_target_province_id",
            "effective_min_roll",
            "effective_max_roll",
            "unavailable_reason",
        },
        f"{name}.battle_context",
    )
    context_status = _available_status(
        context.get("status"), f"{name}.battle_context.status"
    )
    context_available = context_status == "available"
    context_target = _conditional_positive_int32_id(
        context.get("source_target_province_id"),
        context_available,
        f"{name}.battle_context.source_target_province_id",
    )
    if context_target is not None and context_target != target_province_id:
        raise ValueError(f"native {name}.battle_context target mismatch")
    minimum = _conditional_signed_int32(
        context.get("effective_min_roll"),
        context_available,
        f"{name}.battle_context.effective_min_roll",
    )
    maximum = _conditional_signed_int32(
        context.get("effective_max_roll"),
        context_available,
        f"{name}.battle_context.effective_max_roll",
    )
    if status == "absent" and context_available and (minimum, maximum) != (0, 0):
        raise ValueError("native absent commander must have 0..0 roll bounds")
    return {
        "status": status,
        "character_id": character_id,
        "generic_advantage_points": generic_advantage,
        "battle_context": {
            "status": context_status,
            "source_target_province_id": context_target,
            "effective_min_roll": minimum,
            "effective_max_roll": maximum,
            "unavailable_reason": _status_reason(
                context_status,
                context.get("unavailable_reason"),
                f"{name}.battle_context",
            ),
        },
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_regiment(
    value: object,
    *,
    name: str,
    target_province_id: int,
    input_gaps: set[str],
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "regiment_id",
            "identity_valid",
            "current_soldiers",
            "maximum_soldiers",
            "maa_type",
            "kind",
            "fights_in_main_phase",
            "effective_stats",
            "counter",
            "unavailable_reason",
        },
        name,
    )
    status = _available_status(row.get("status"), f"{name}.status")
    regiment_id = _positive_int32_id(
        row.get("regiment_id"), f"{name}.regiment_id"
    )
    identity_valid = _strict_bool(
        row.get("identity_valid"), f"{name}.identity_valid"
    )
    current = _non_negative_int32(
        row.get("current_soldiers"), f"{name}.current_soldiers"
    )
    maximum = _non_negative_int32(
        row.get("maximum_soldiers"), f"{name}.maximum_soldiers"
    )
    maa_type = _normalize_maa_type(row.get("maa_type"), name=f"{name}.maa_type")
    kind = _normalize_regiment_kind(row.get("kind"), name=f"{name}.kind")
    fights = row.get("fights_in_main_phase")
    if kind["status"] == "available":
        fights = _strict_bool(fights, f"{name}.fights_in_main_phase")
    elif fights is not None:
        raise ValueError(
            f"native {name}.fights_in_main_phase must be null when kind is not available"
        )
    stats = _normalize_effective_stats(
        row.get("effective_stats"),
        name=f"{name}.effective_stats",
        target_province_id=target_province_id,
    )
    counter = _normalize_counter(row.get("counter"), name=f"{name}.counter")
    reason = _status_reason(status, row.get("unavailable_reason"), name)
    if not identity_valid:
        input_gaps.add("regiment_identity")
    if maa_type["status"] == "unavailable":
        input_gaps.add("regiment_maa_type")
    if kind["status"] != "available":
        input_gaps.add("regiment_kind_and_main_phase_eligibility")
    if stats["status"] != "available":
        input_gaps.add("effective_regiment_stats")
    if counter["status"] == "unavailable":
        input_gaps.add("counter_operands")
    if status == "available" and (
        not identity_valid
        or maa_type["status"] == "unavailable"
        or kind["status"] != "available"
        or stats["status"] != "available"
    ):
        raise ValueError(f"native available {name} has unavailable required fields")
    if status == "unavailable" and (
        identity_valid
        and maa_type["status"] != "unavailable"
        and kind["status"] == "available"
        and stats["status"] == "available"
        and counter["status"] != "unavailable"
    ):
        raise ValueError(
            f"native unavailable {name} lacks a matching required-input gap"
        )
    return {
        "status": status,
        "regiment_id": regiment_id,
        "identity_valid": identity_valid,
        "current_soldiers": current,
        "maximum_soldiers": maximum,
        "maa_type": maa_type,
        "kind": kind,
        "fights_in_main_phase": fights,
        "effective_stats": stats,
        "counter": counter,
        "unavailable_reason": reason,
    }


def _normalize_maa_type(value: object, *, name: str) -> dict[str, object]:
    row = _exact_object(
        value, {"status", "key", "unavailable_reason"}, name
    )
    status = _tri_status(row.get("status"), f"{name}.status")
    key = row.get("key")
    if status == "available":
        key = _nonempty_string(key, f"{name}.key")
    elif key is not None:
        raise ValueError(f"native {name}.key must be null")
    return {
        "status": status,
        "key": key,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_regiment_kind(value: object, *, name: str) -> dict[str, object]:
    row = _exact_object(
        value, {"status", "value", "unavailable_reason"}, name
    )
    status = _tri_status(row.get("status"), f"{name}.status")
    if status == "absent":
        raise ValueError(f"native {name}.status cannot be absent")
    kind = row.get("value")
    if status == "available":
        if kind not in {"levy", "men_at_arms"}:
            raise ValueError(f"native {name}.value is malformed")
    elif kind is not None:
        raise ValueError(f"native {name}.value must be null")
    return {
        "status": status,
        "value": kind,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_effective_stats(
    value: object,
    *,
    name: str,
    target_province_id: int,
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "source_target_province_id",
            "max_size",
            "siege_value_raw",
            "damage_raw",
            "toughness_raw",
            "pursuit_raw",
            "screen_raw",
            "scale",
            "unavailable_reason",
        },
        name,
    )
    status = _available_status(row.get("status"), f"{name}.status")
    available = status == "available"
    source_target = _conditional_positive_int32_id(
        row.get("source_target_province_id"),
        available,
        f"{name}.source_target_province_id",
    )
    if source_target is not None and source_target != target_province_id:
        raise ValueError(f"native {name} target ProvinceID mismatch")
    max_size = _conditional_non_negative_int32(
        row.get("max_size"), available, f"{name}.max_size"
    )
    raw_fields = {
        field: _conditional_signed_int64(
            row.get(field), available, f"{name}.{field}"
        )
        for field in (
            "siege_value_raw",
            "damage_raw",
            "toughness_raw",
            "pursuit_raw",
            "screen_raw",
        )
    }
    _fixed_scale(row.get("scale"), f"{name}.scale")
    return {
        "status": status,
        "source_target_province_id": source_target,
        "max_size": max_size,
        **raw_fields,
        "scale": CK3_COMBAT_FIXED_POINT_SCALE,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_counter(value: object, *, name: str) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "class_index",
            "current_chunk_raw",
            "targets",
            "scale",
            "unavailable_reason",
        },
        name,
    )
    status = _tri_status(row.get("status"), f"{name}.status")
    available = status == "available"
    class_index = _conditional_non_negative_int32(
        row.get("class_index"), available, f"{name}.class_index"
    )
    chunk = _conditional_non_negative_int64(
        row.get("current_chunk_raw"),
        available,
        f"{name}.current_chunk_raw",
    )
    raw_targets = row.get("targets")
    if status == "unavailable":
        if raw_targets is not None:
            raise ValueError(f"native {name}.targets must be null")
        targets = None
    else:
        targets = []
        for index, raw_target in enumerate(
            _array(raw_targets, f"{name}.targets")
        ):
            target_name = f"{name}.targets[{index}]"
            target = _exact_object(
                raw_target,
                {"class_index", "effectiveness_raw", "scale"},
                target_name,
            )
            targets.append(
                {
                    "class_index": _non_negative_int32(
                        target.get("class_index"),
                        f"{target_name}.class_index",
                    ),
                    "effectiveness_raw": _signed_int64(
                        target.get("effectiveness_raw"),
                        f"{target_name}.effectiveness_raw",
                    ),
                    "scale": _fixed_scale(
                        target.get("scale"), f"{target_name}.scale"
                    ),
                }
            )
        if status == "absent" and targets:
            raise ValueError(f"native absent {name} must have no targets")
    _fixed_scale(row.get("scale"), f"{name}.scale")
    return {
        "status": status,
        "class_index": class_index,
        "current_chunk_raw": chunk,
        "targets": targets,
        "scale": CK3_COMBAT_FIXED_POINT_SCALE,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_knights(
    value: object,
    *,
    name: str,
    native_carmy_id: int | None,
    regiment_ids: set[int],
    input_gaps: set[str],
    seen_knight_ids: set[int],
    seen_knight_regiment_ids: set[int],
) -> dict[str, object]:
    row = _exact_object(
        value, {"status", "members", "unavailable_reason"}, name
    )
    status = _available_status(row.get("status"), f"{name}.status")
    if status == "unavailable":
        if row.get("members") is not None:
            raise ValueError(f"native {name}.members must be null")
        input_gaps.add("knights")
        members = None
    else:
        members = []
        ordering: list[tuple[int, int, int]] = []
        for index, raw_member in enumerate(
            _array(row.get("members"), f"{name}.members")
        ):
            member_name = f"{name}.members[{index}]"
            member = _exact_object(
                raw_member,
                {
                    "eligible",
                    "character_id",
                    "source_regiment_id",
                    "army_id",
                    "participant_army_membership_verified",
                    "prowess",
                    "knight_effectiveness_raw",
                    "effective_damage_raw",
                    "effective_toughness_raw",
                    "scale",
                },
                member_name,
            )
            eligible = _strict_bool(
                member.get("eligible"), f"{member_name}.eligible"
            )
            membership = _strict_bool(
                member.get("participant_army_membership_verified"),
                f"{member_name}.participant_army_membership_verified",
            )
            if not eligible or not membership:
                raise ValueError(f"native {member_name} is not an eligible member")
            character_id = _non_negative_int32_id(
                member.get("character_id"), f"{member_name}.character_id"
            )
            regiment_id = _positive_int32_id(
                member.get("source_regiment_id"),
                f"{member_name}.source_regiment_id",
            )
            army_id = _positive_int32_id(
                member.get("army_id"), f"{member_name}.army_id"
            )
            if native_carmy_id is None or army_id != native_carmy_id:
                raise ValueError(f"native {member_name}.army_id is not its CArmyID")
            if regiment_id not in regiment_ids:
                raise ValueError(
                    f"native {member_name} is outside its army regiments"
                )
            if character_id in seen_knight_ids:
                raise ValueError("native combat repeats a knight CharacterID")
            if regiment_id in seen_knight_regiment_ids:
                raise ValueError("native combat repeats a knight RegimentID")
            seen_knight_ids.add(character_id)
            seen_knight_regiment_ids.add(regiment_id)
            prowess = _signed_int32(
                member.get("prowess"), f"{member_name}.prowess"
            )
            effectiveness = _non_negative_int64(
                member.get("knight_effectiveness_raw"),
                f"{member_name}.knight_effectiveness_raw",
            )
            damage = _non_negative_int64(
                member.get("effective_damage_raw"),
                f"{member_name}.effective_damage_raw",
            )
            toughness = _non_negative_int64(
                member.get("effective_toughness_raw"),
                f"{member_name}.effective_toughness_raw",
            )
            effective_prowess = max(1, prowess)
            if (
                damage != effective_prowess * effectiveness * 50
                or toughness != effective_prowess * effectiveness * 10
            ):
                raise ValueError(f"native {member_name} knight stats disagree")
            _fixed_scale(member.get("scale"), f"{member_name}.scale")
            members.append(
                {
                    "eligible": True,
                    "character_id": character_id,
                    "source_regiment_id": regiment_id,
                    "army_id": army_id,
                    "participant_army_membership_verified": True,
                    "prowess": prowess,
                    "knight_effectiveness_raw": effectiveness,
                    "effective_damage_raw": damage,
                    "effective_toughness_raw": toughness,
                    "scale": CK3_COMBAT_FIXED_POINT_SCALE,
                }
            )
            ordering.append((army_id, regiment_id, character_id))
        if ordering != sorted(ordering):
            raise ValueError(f"native {name}.members ordering is unstable")
    return {
        "status": status,
        "members": members,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_target_province(
    value: object,
    *,
    target_province_id: int,
    input_gaps: set[str],
) -> dict[str, object]:
    name = "combat_simulation_inputs.target_province"
    row = _exact_object(
        value,
        {
            "status",
            "province_id",
            "terrain",
            "crossing",
            "defender_context",
            "precontact_width",
            "unavailable_reason",
        },
        name,
    )
    status = _available_status(row.get("status"), f"{name}.status")
    province_id = _positive_int32_id(
        row.get("province_id"), f"{name}.province_id"
    )
    if province_id != target_province_id:
        raise ValueError("native target_province identity mismatch")
    terrain_name = f"{name}.terrain"
    terrain_row = _exact_object(
        row.get("terrain"),
        {
            "status",
            "key",
            "combat_width_multiplier_raw",
            "scale",
            "unavailable_reason",
        },
        terrain_name,
    )
    terrain_status = _available_status(
        terrain_row.get("status"), f"{terrain_name}.status"
    )
    terrain_available = terrain_status == "available"
    terrain_key = terrain_row.get("key")
    if terrain_available:
        terrain_key = _nonempty_string(terrain_key, f"{terrain_name}.key")
    elif terrain_key is not None:
        raise ValueError(f"native {terrain_name}.key must be null")
    width_multiplier = _conditional_signed_int64(
        terrain_row.get("combat_width_multiplier_raw"),
        terrain_available,
        f"{terrain_name}.combat_width_multiplier_raw",
    )
    _fixed_scale(terrain_row.get("scale"), f"{terrain_name}.scale")
    terrain = {
        "status": terrain_status,
        "key": terrain_key,
        "combat_width_multiplier_raw": width_multiplier,
        "scale": CK3_COMBAT_FIXED_POINT_SCALE,
        "unavailable_reason": _status_reason(
            terrain_status,
            terrain_row.get("unavailable_reason"),
            terrain_name,
        ),
    }
    crossing = _normalize_crossing(row.get("crossing"), name=f"{name}.crossing")
    defender = _normalize_defender_context(
        row.get("defender_context"), name=f"{name}.defender_context"
    )
    width = _normalize_precontact_width(
        row.get("precontact_width"), name=f"{name}.precontact_width"
    )
    if status != "available" or terrain_status != "available":
        input_gaps.add("target_terrain")
    if crossing["status"] != "available":
        input_gaps.add("crossing")
    if (
        defender["status"] != "available"
        or defender["holding_defender_status"] != "available"
    ):
        input_gaps.add("attacker_defender_holding")
    if width["status"] != "available":
        input_gaps.add("contact_combat_width")
    if status == "available" and terrain_status != "available":
        raise ValueError("native available target_province lacks terrain")
    return {
        "status": status,
        "province_id": province_id,
        "terrain": terrain,
        "crossing": crossing,
        "defender_context": defender,
        "precontact_width": width,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_crossing(value: object, *, name: str) -> dict[str, object]:
    row = _exact_object(
        value, {"status", "kind", "unavailable_reason"}, name
    )
    status = _available_status(row.get("status"), f"{name}.status")
    kind = row.get("kind")
    if status == "available":
        if kind not in {"none", "strait", "river", "large_river"}:
            raise ValueError(f"native {name}.kind is malformed")
    elif kind is not None:
        raise ValueError(f"native {name}.kind must be null")
    return {
        "status": status,
        "kind": kind,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_defender_context(
    value: object, *, name: str
) -> dict[str, object]:
    row = _exact_object(
        value,
        {
            "status",
            "defender_side",
            "holding_defender_status",
            "holding_defender",
            "holding_unavailable_reason",
            "unavailable_reason",
        },
        name,
    )
    status = _available_status(row.get("status"), f"{name}.status")
    side = row.get("defender_side")
    holding_status = _available_status(
        row.get("holding_defender_status"),
        f"{name}.holding_defender_status",
    )
    holding = row.get("holding_defender")
    if status == "available":
        if side not in {"player_or_allied", "enemy"}:
            raise ValueError(f"native {name}.defender_side is malformed")
    elif side is not None:
        raise ValueError(f"native unavailable {name} must null defender_side")
    if holding_status == "available":
        if status != "available":
            raise ValueError(
                f"native unavailable {name} cannot publish holding context"
            )
        holding = _strict_bool(holding, f"{name}.holding_defender")
        holding_reason = _status_reason(
            holding_status,
            row.get("holding_unavailable_reason"),
            f"{name}.holding",
        )
    else:
        if holding is not None:
            raise ValueError(
                f"native unavailable {name}.holding_defender must be null"
            )
        holding_reason = _status_reason(
            holding_status,
            row.get("holding_unavailable_reason"),
            f"{name}.holding",
        )
    return {
        "status": status,
        "defender_side": side,
        "holding_defender_status": holding_status,
        "holding_defender": holding,
        "holding_unavailable_reason": holding_reason,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_precontact_width(
    value: object, *, name: str
) -> dict[str, object]:
    row = _exact_object(
        value, {"status", "base", "final", "unavailable_reason"}, name
    )
    status = _available_status(row.get("status"), f"{name}.status")
    available = status == "available"
    base = _conditional_non_negative_int32(
        row.get("base"), available, f"{name}.base"
    )
    final = _conditional_non_negative_int32(
        row.get("final"), available, f"{name}.final"
    )
    return {
        "status": status,
        "base": base,
        "final": final,
        "unavailable_reason": _status_reason(
            status, row.get("unavailable_reason"), name
        ),
    }


def _normalize_ongoing_combats(
    value: object, *, input_gaps: set[str]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen_ids: set[int] = set()
    for index, raw_row in enumerate(
        _array(value, "combat_simulation_inputs.ongoing_combats")
    ):
        name = f"combat_simulation_inputs.ongoing_combats[{index}]"
        row = _exact_object(
            raw_row,
            {
                "status",
                "combat_id",
                "province_id",
                "phase",
                "phase_day",
                "base_combat_width",
                "final_combat_width",
                "side_0_roll",
                "side_1_roll",
                "base_advantage",
                "resolved_advantage",
                "orientation",
                "unavailable_reason",
            },
            name,
        )
        status = _available_status(row.get("status"), f"{name}.status")
        available = status == "available"
        raw_combat_id = row.get("combat_id")
        combat_id = (
            None
            if raw_combat_id is None
            else _signed_int32(raw_combat_id, f"{name}.combat_id")
        )
        if available and (combat_id is None or combat_id == -1):
            raise ValueError(f"native available {name}.combat_id is invalid")
        if combat_id is not None:
            if combat_id in seen_ids:
                raise ValueError("native ongoing_combats repeats a CombatID")
            seen_ids.add(combat_id)
        province_id = _conditional_positive_int32_id(
            row.get("province_id"), available, f"{name}.province_id"
        )
        phase = _conditional_non_negative_int32(
            row.get("phase"), available, f"{name}.phase"
        )
        if phase is not None and phase > 3:
            raise ValueError(f"native {name}.phase is out of range")
        phase_day = _conditional_non_negative_int32(
            row.get("phase_day"), available, f"{name}.phase_day"
        )
        base_width = _conditional_non_negative_int32(
            row.get("base_combat_width"),
            available,
            f"{name}.base_combat_width",
        )
        final_width = _conditional_non_negative_int32(
            row.get("final_combat_width"),
            available,
            f"{name}.final_combat_width",
        )
        signed_fields = {
            field: _conditional_signed_int32(
                row.get(field), available, f"{name}.{field}"
            )
            for field in (
                "side_0_roll",
                "side_1_roll",
            )
        }
        signed_fields.update(
            {
                field: _conditional_signed_int64(
                    row.get(field), available, f"{name}.{field}"
                )
                for field in (
                    "base_advantage",
                    "resolved_advantage",
                )
            }
        )
        orientation = row.get("orientation")
        if available:
            if orientation != "native_side_0_attacker_side_1_defender":
                raise ValueError(f"native {name}.orientation is malformed")
        elif orientation is not None:
            raise ValueError(f"native unavailable {name} must null orientation")
        if not available:
            input_gaps.add("ongoing_combat_context")
        rows.append(
            {
                "status": status,
                "combat_id": combat_id,
                "province_id": province_id,
                "phase": phase,
                "phase_day": phase_day,
                "base_combat_width": base_width,
                "final_combat_width": final_width,
                **signed_fields,
                "orientation": orientation,
                "unavailable_reason": _status_reason(
                    status, row.get("unavailable_reason"), name
                ),
            }
        )
    return rows


def _normalize_counter_resolutions(
    value: object,
    *,
    input_gaps: set[str],
    expected_owner_by_side: dict[str, int],
) -> list[dict[str, object]]:
    raw_rows = _array(
        value, "combat_simulation_inputs.counter_resolutions"
    )
    if len(raw_rows) != 2:
        raise ValueError("native combat must publish two counter resolutions")
    expected_pairs = [
        ("player_or_allied", "enemy"),
        ("enemy", "player_or_allied"),
    ]
    rows: list[dict[str, object]] = []
    common_class_count: int | None = None
    for index, (raw_row, expected_pair) in enumerate(
        zip(raw_rows, expected_pairs, strict=True)
    ):
        name = f"combat_simulation_inputs.counter_resolutions[{index}]"
        row = _exact_object(
            raw_row,
            {
                "status",
                "countered_side",
                "countering_side",
                "countered_modifier_owner_character_id",
                "countering_modifier_owner_character_id",
                "context_scale_raw",
                "class_count",
                "damage_retention_by_class_raw",
                "scale",
                "unavailable_reason",
            },
            name,
        )
        status = _available_status(row.get("status"), f"{name}.status")
        pair = (row.get("countered_side"), row.get("countering_side"))
        if pair != expected_pair:
            raise ValueError(f"native {name} side orientation is malformed")
        available = status == "available"
        countered_owner = _conditional_non_negative_int32_id(
            row.get("countered_modifier_owner_character_id"),
            available,
            f"{name}.countered_modifier_owner_character_id",
        )
        countering_owner = _conditional_non_negative_int32_id(
            row.get("countering_modifier_owner_character_id"),
            available,
            f"{name}.countering_modifier_owner_character_id",
        )
        context_scale = _conditional_non_negative_int64(
            row.get("context_scale_raw"),
            available,
            f"{name}.context_scale_raw",
        )
        if available and (
            countered_owner != expected_owner_by_side.get(expected_pair[0])
            or countering_owner
            != expected_owner_by_side.get(expected_pair[1])
        ):
            raise ValueError(
                f"native {name} did not use the first request-order owner"
            )
        class_count = _positive_int32_id(
            row.get("class_count"), f"{name}.class_count"
        )
        if common_class_count is None:
            common_class_count = class_count
        elif class_count != common_class_count:
            raise ValueError("native counter resolutions disagree on class_count")
        raw_retention = row.get("damage_retention_by_class_raw")
        if available:
            retention = []
            for class_index, raw_value in enumerate(
                _array(raw_retention, f"{name}.damage_retention_by_class_raw")
            ):
                fixed = _non_negative_int64(
                    raw_value,
                    f"{name}.damage_retention_by_class_raw[{class_index}]",
                )
                if fixed > CK3_COMBAT_FIXED_POINT_SCALE:
                    raise ValueError(f"native {name} retention is out of range")
                retention.append(fixed)
            if len(retention) != class_count:
                raise ValueError(f"native {name} retention vector is incomplete")
        else:
            if raw_retention is not None:
                raise ValueError(f"native unavailable {name} must null retention")
            retention = None
            input_gaps.add("counter_resolutions")
        _fixed_scale(row.get("scale"), f"{name}.scale")
        rows.append(
            {
                "status": status,
                "countered_side": expected_pair[0],
                "countering_side": expected_pair[1],
                "countered_modifier_owner_character_id": countered_owner,
                "countering_modifier_owner_character_id": countering_owner,
                "context_scale_raw": context_scale,
                "class_count": class_count,
                "damage_retention_by_class_raw": retention,
                "scale": CK3_COMBAT_FIXED_POINT_SCALE,
                "unavailable_reason": _status_reason(
                    status, row.get("unavailable_reason"), name
                ),
            }
        )
    return rows


def _normalize_completeness(
    value: object, *, input_gaps: set[str]
) -> dict[str, object]:
    name = "combat_simulation_inputs.completeness"
    row = _exact_object(
        value,
        {
            "observation_slice",
            "input_observation_ready",
            "monte_carlo_ready",
            "missing_required_domains",
        },
        name,
    )
    if row.get("observation_slice") != "precontact-composition-context-v2":
        raise ValueError("native combat observation_slice is malformed")
    input_ready = _strict_bool(
        row.get("input_observation_ready"), f"{name}.input_observation_ready"
    )
    monte_carlo_ready = _strict_bool(
        row.get("monte_carlo_ready"), f"{name}.monte_carlo_ready"
    )
    if monte_carlo_ready:
        raise ValueError("combat-simulation-inputs-v2 cannot be Monte Carlo ready")
    raw_domains = _array(
        row.get("missing_required_domains"),
        f"{name}.missing_required_domains",
    )
    domains = [
        _nonempty_string(domain, f"{name}.missing_required_domains[{index}]")
        for index, domain in enumerate(raw_domains)
    ]
    if len(domains) != len(set(domains)):
        raise ValueError("native combat missing_required_domains has duplicates")
    if len(domains) < len(_SIMULATOR_GAPS) or domains[-4:] != _SIMULATOR_GAPS:
        raise ValueError("native combat simulator gaps are malformed")
    observed_input_gaps = domains[: -len(_SIMULATOR_GAPS)]
    if any(domain not in _INPUT_GAPS for domain in observed_input_gaps):
        raise ValueError("native combat input gap is not part of v1")
    if set(observed_input_gaps) != input_gaps:
        raise ValueError("native combat completeness disagrees with subdomains")
    if input_ready is not (not input_gaps):
        raise ValueError("native combat input_observation_ready is inconsistent")
    if input_ready and domains != _SIMULATOR_GAPS:
        raise ValueError("available combat input has non-simulator gaps")
    return {
        "observation_slice": "precontact-composition-context-v2",
        "input_observation_ready": input_ready,
        "monte_carlo_ready": False,
        "missing_required_domains": domains,
    }


def _exact_object(
    value: object, keys: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native {name} schema is malformed")
    return value


def _array(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    return value


def _tri_status(value: object, name: str) -> str:
    if value not in {"available", "absent", "unavailable"}:
        raise ValueError(f"native {name} is malformed")
    assert isinstance(value, str)
    return value


def _available_status(value: object, name: str) -> str:
    if value not in {"available", "unavailable"}:
        raise ValueError(f"native {name} is malformed")
    assert isinstance(value, str)
    return value


def _status_reason(status: str, value: object, name: str) -> str | None:
    if status == "unavailable":
        return _nonempty_string(value, f"{name}.unavailable_reason")
    if value is not None:
        raise ValueError(f"native {name}.unavailable_reason must be null")
    return None


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"native {name} must be a non-empty string")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"native {name} must be boolean")
    return value


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < -(2**31)
        or value > 2**31 - 1
    ):
        raise ValueError(f"native {name} must be signed int32")
    return value


def _non_negative_int32(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result < 0:
        raise ValueError(f"native {name} must be non-negative")
    return result


def _non_negative_int32_id(value: object, name: str) -> int:
    return _non_negative_int32(value, name)


def _optional_non_negative_int32_id(value: object, name: str) -> int | None:
    return None if value is None else _non_negative_int32_id(value, name)


def _optional_positive_int32_id(value: object, name: str) -> int | None:
    return None if value is None else _positive_int32_id(value, name)


def _signed_int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < -(2**63)
        or value > 2**63 - 1
    ):
        raise ValueError(f"native {name} must be signed int64")
    return value


def _non_negative_int64(value: object, name: str) -> int:
    result = _signed_int64(value, name)
    if result < 0:
        raise ValueError(f"native {name} must be non-negative")
    return result


def _conditional_signed_int32(
    value: object, available: bool, name: str
) -> int | None:
    if available:
        return _signed_int32(value, name)
    if value is not None:
        raise ValueError(f"native {name} must be null when unavailable")
    return None


def _conditional_non_negative_int32(
    value: object, available: bool, name: str
) -> int | None:
    if available:
        return _non_negative_int32(value, name)
    if value is not None:
        raise ValueError(f"native {name} must be null when unavailable")
    return None


def _conditional_positive_int32_id(
    value: object, available: bool, name: str
) -> int | None:
    if available:
        return _positive_int32_id(value, name)
    if value is not None:
        raise ValueError(f"native {name} must be null when unavailable")
    return None


def _conditional_non_negative_int32_id(
    value: object, available: bool, name: str
) -> int | None:
    if available:
        return _non_negative_int32_id(value, name)
    if value is not None:
        raise ValueError(f"native {name} must be null when unavailable")
    return None


def _conditional_signed_int64(
    value: object, available: bool, name: str
) -> int | None:
    if available:
        return _signed_int64(value, name)
    if value is not None:
        raise ValueError(f"native {name} must be null when unavailable")
    return None


def _conditional_non_negative_int64(
    value: object, available: bool, name: str
) -> int | None:
    if available:
        return _non_negative_int64(value, name)
    if value is not None:
        raise ValueError(f"native {name} must be null when unavailable")
    return None


def _fixed_scale(value: object, name: str) -> int:
    if value != CK3_COMBAT_FIXED_POINT_SCALE:
        raise ValueError(
            f"native {name} must be {CK3_COMBAT_FIXED_POINT_SCALE}"
        )
    return CK3_COMBAT_FIXED_POINT_SCALE


def _positive_id_array(value: object, name: str) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for index, item in enumerate(_array(value, name)):
        normalized = _positive_int32_id(item, f"{name}[{index}]")
        if normalized in seen:
            raise ValueError(f"native {name} contains duplicate IDs")
        seen.add(normalized)
        result.append(normalized)
    return result


def _positive_int32_id(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive signed int32")
    return value
