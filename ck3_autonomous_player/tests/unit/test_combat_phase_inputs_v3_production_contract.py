from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.combat_phase_contract import (
    OFFLINE_EXACT_REF_PATHS,
    PHASE_EVENT_NATIVE_LEAF_EXACT_REF_COUNT,
    PHASE_EVENT_NATIVE_LEAF_EXACT_REFS_SHA256,
    PHASE_EVENT_OFFLINE_EXACT_REF_COUNT,
    PHASE_EVENT_OFFLINE_EXACT_REFS_SHA256,
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    _ABI_COUNTS,
    _ACCOLADE_PARAMETER_KEYS,
    _ATTRIBUTE_UNLOCK_KEYS,
    _CULTURE_PARAMETER_KEYS,
    _DOMAIN_COUNTS,
    _INNOVATION_KEYS,
    _MAA_COUNT_KEYS,
    _PATH_HASHES,
    _PAYLOAD_POLICY,
    _TRADITION_KEYS,
    _TRAIT_OR_GROUP_KEYS,
    _accolade_unlocks,
    _expected_phase_characters,
    combat_simulation_inputs_v3_status,
    normalize_combat_simulation_inputs_v3,
    parse_query_combat_simulation_inputs_v3_step,
    phase_event_ref_partition,
    query_combat_simulation_inputs_v3_step,
)
from xar_autoplayer.bridge.combat_contract import (
    PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
    PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
    PHASE_EVENT_STOCK_MANIFEST_SHA256,
)
from xar_autoplayer.simulation.phase_event_evaluator import (
    PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
    PHASE_EVENT_AST_EVALUATOR_SHA256,
    PHASE_EVENT_AST_EVALUATOR_VERSION,
)
from xar_autoplayer.simulation.candidate_source_proof import (
    CANDIDATE_SOURCE_PROOF_POLICY,
    candidate_source_sequence_sha256,
)


RECIPE_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "combat_phase_events"
    / "v3_production_contract_recipe.json"
)
NATIVE_GOLDEN_DIR = (
    PROJECT_ROOT / "native_bridge" / "research" / "fixtures"
)
NATIVE_AVAILABLE_GOLDEN_PATH = (
    NATIVE_GOLDEN_DIR
    / "combat_simulation_inputs_v3_production_available.json"
)
NATIVE_UNAVAILABLE_GOLDEN_PATH = (
    NATIVE_GOLDEN_DIR
    / "combat_simulation_inputs_v3_production_unavailable.json"
)


def _legacy_v3_fixture_builder():
    path = Path(__file__).with_name("test_combat_phase_inputs_v3_contract.py")
    spec = importlib.util.spec_from_file_location("_xar_v3_fixture_builder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _optional(value: int | None) -> dict[str, object]:
    return {
        "status": "available" if value is not None else "absent",
        "value": value,
    }


def _production_payload() -> tuple[dict[str, object], dict[str, object]]:
    legacy, scope = _legacy_v3_fixture_builder()._v3_payload()
    base = copy.deepcopy(legacy["base_inputs"])
    advantage = copy.deepcopy(legacy["phase_event_inputs"]["advantage_model"])
    advantage["observation_origin"] = "native_exact_build_production"
    expected_characters = _expected_phase_characters(base)
    characters: list[dict[str, object]] = []
    for index, expected in enumerate(expected_characters):
        character_id = int(expected["character_id"])
        faith_id = 10_000 + character_id
        traits = {key: False for key in _TRAIT_OR_GROUP_KEYS}
        characters.append(
            {
                **copy.deepcopy(expected),
                "alive": True,
                "is_ai": True,
                "martial": 10 + index,
                "learning": 11 + index,
                "prowess": 12 + index,
                "traits_or_groups": traits,
                "wounded_rank_raw": 0,
                "fragile_bones_rank_raw": 0,
                "fragile_bones_xp_raw": 0,
                "lifestyle_blademaster_xp_raw": 0,
                "tourney_bow_xp_raw": 0,
                "tourney_foot_xp_raw": 0,
                "tourney_horse_xp_raw": 0,
                "house": _optional(100 + index % 2),
                "liege": _optional(20_000 + index),
                "liege_house": _optional(100 + index % 2),
                "employer": _optional(30_000 + index),
                "dynasty": _optional(40_000 + index),
                "warfare_legacy_3": False,
                "stalwart_leader": False,
                "culture": _optional(50_000 + index),
                "faith": _optional(faith_id),
                "religion": _optional(60_000 + index),
                "heritage_north_germanic": False,
                "knights_slightly_more_prone_to_injury": False,
                "death_is_glory": False,
                "tenet_warmonger": False,
                "germanic_religion": False,
                "blademaster_traits_more_common": False,
                "innovations": {key: False for key in _INNOVATION_KEYS},
                "traditions": {key: False for key in _TRADITION_KEYS},
                "culture_parameters": {
                    key: False for key in _CULTURE_PARAMETER_KEYS
                },
                "is_acclaimed": False,
                "can_be_acclaimed": True,
                "accolade": _optional(None),
                "accolade_has_men_at_arms_category": False,
                "accolade_parameters": {
                    key: False for key in _ACCOLADE_PARAMETER_KEYS
                },
                "conqueror_variable_present": False,
                "attribute_unlock_variables": {
                    key: False for key in _ATTRIBUTE_UNLOCK_KEYS
                },
                "hold_court_8050_knight": _optional(None),
                "employer_hold_court_8050_promise": _optional(None),
                "liege_accolade_progress_raw": 0,
                "ai_extreme_conqueror_modifier": False,
                "garuda_court_position": False,
                "government_is_nomadic": False,
            }
        )
    character_by_id = {int(row["character_id"]): row for row in characters}
    armies = [
        {
            "army_id": army["army_id"],
            "native_carmy_id": army["native_carmy_id"],
            "encounter_role": army["encounter_role"],
            "maa_regiment_count_raw": 100_000,
            "maa_counts_raw": {
                key: (100_000 if key == "skirmishers_raw" else 0)
                for key in _MAA_COUNT_KEYS
            },
        }
        for army in base["armies"]
    ]
    scenario = base["scenario"]
    sides: list[dict[str, object]] = []
    for side_index, role in enumerate(("attacker", "defender")):
        side_army_ids = list(
            scenario[
                "attacker_army_ids"
                if side_index == 0
                else "defender_army_ids"
            ]
        )
        side_armies = [
            army for army in base["armies"] if army["army_id"] in side_army_ids
        ]
        ordered_characters = [
            row["character_id"]
            for row in characters
            if row["encounter_role"] == role
        ]
        commanders = [
            army["commander"]["character_id"]
            for army in side_armies
            if army["commander"]["status"] == "available"
        ]
        knights = [
            member["character_id"]
            for army in side_armies
            for member in army["knights"]["members"]
        ]
        ordered_sources = [
            {
                "role": "commander",
                "source_army_id": int(army["army_id"]),
                "source_regiment_id": None,
                "character_id": int(army["commander"]["character_id"]),
            }
            for army in side_armies
            if army["commander"]["status"] == "available"
        ]
        ordered_sources.extend(
            {
                "role": "knight",
                "source_army_id": int(army["army_id"]),
                "source_regiment_id": int(member["source_regiment_id"]),
                "character_id": int(member["character_id"]),
            }
            for army in side_armies
            for member in army["knights"]["members"]
        )
        candidate_source_proof = {
            "policy": CANDIDATE_SOURCE_PROOF_POLICY,
            "source_vector_equivalence": True,
            "sequence_sha256": candidate_source_sequence_sha256(
                side_index, ordered_sources
            ),
            "ordered_sources": ordered_sources,
        }
        participants: list[dict[str, int]] = []
        seen_owners: set[int] = set()
        for army in side_armies:
            owner_id = int(army["owner"]["character_id"])
            if owner_id in seen_owners:
                continue
            seen_owners.add(owner_id)
            participants.append(
                {
                    "source_army_id": int(army["army_id"]),
                    "owner_character_id": owner_id,
                    "faith_id": int(character_by_id[owner_id]["faith"]["value"]),
                }
            )
        sides.append(
            {
                "side_index": side_index,
                "encounter_role": role,
                "ordered_army_ids": side_army_ids,
                "ordered_character_ids": ordered_characters,
                "ordered_commander_ids": commanders,
                "ordered_knight_ids": knights,
                "primary_participant_character_id": participants[0][
                    "owner_character_id"
                ],
                "primary_source_army_id": side_army_ids[0],
                "commander_character_id": commanders[0] if commanders else None,
                "side_strength_raw": (200_000 if side_index == 0 else 100_000),
                "side_army_size_raw": (
                    200_000_000 if side_index == 0 else 100_000_000
                ),
                "participants": participants,
                "candidate_source_proof": candidate_source_proof,
            }
        )
    hostility: list[dict[str, int]] = []
    for character in characters:
        side_index = 0 if character["encounter_role"] == "attacker" else 1
        enemy_index = 1 - side_index
        for participant in sides[enemy_index]["participants"]:
            hostility.append(
                {
                    "root_character_id": int(character["character_id"]),
                    "enemy_side_index": enemy_index,
                    "enemy_owner_character_id": int(
                        participant["owner_character_id"]
                    ),
                    "enemy_faith_id": int(participant["faith_id"]),
                    "root_faith_id": int(character["faith"]["value"]),
                    "hostility_level_raw": 2,
                }
            )
    coverage = {
        "manifest_domain_counts": dict(_DOMAIN_COUNTS),
        "abi_level_counts": dict(_ABI_COUNTS),
        "path_set_sha256": dict(_PATH_HASHES),
        "native_payload_policy": _PAYLOAD_POLICY,
    }
    phase = {
        "status": "available",
        "rules_source": "stock-installation-static-manifest",
        "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
        "required_state_refs": {
            "count": PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
            "sha256": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
        },
        "state_ref_coverage": coverage,
        "scope_mode": "hypothetical_precontact_offline_ast",
        "raw": {
            "characters": characters,
            "armies": armies,
            "sides": sides,
            "faith_hostility": hostility,
            "game_rules": {
                "easy_difficulty": False,
                "very_easy_difficulty": False,
            },
        },
        "advantage_model": advantage,
        "unavailable_reason": None,
    }
    return (
        {
            "schema_version": 3,
            "contract_stage": "production_exact_132_refs",
            "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
            "base_inputs": base,
            "phase_event_inputs": phase,
        },
        scope,
    )


def _normalize(payload: dict[str, object], scope: dict[str, object]):
    base = payload["base_inputs"]
    return normalize_combat_simulation_inputs_v3(
        payload,
        expected_target_province_id=int(base["target_province_id"]),
        expected_attacker_entry_province_id=int(
            base["scenario"]["attacker_entry_province_id"]
        ),
        expected_encounter_scope=scope,
    )


def _normalize_native_golden_envelope(
    fixture: object,
) -> dict[str, object]:
    if not isinstance(fixture, dict) or set(fixture) != {
        "type", "protocol_version", "request_id", "ok", "result"
    }:
        raise ValueError("production v3 golden envelope is malformed")
    if (
        fixture.get("type") != "command_result"
        or fixture.get("protocol_version") != 1
        or not isinstance(fixture.get("request_id"), str)
        or not fixture.get("request_id")
        or fixture.get("ok") is not True
    ):
        raise ValueError("production v3 golden envelope identity is malformed")
    result = fixture.get("result")
    if not isinstance(result, dict) or set(result) != {
        "step", "accepted", "status", "query_sequence",
        "combat_simulation_inputs",
    }:
        raise ValueError("production v3 golden result schema is malformed")
    parsed = parse_query_combat_simulation_inputs_v3_step(result.get("step"))
    query_sequence = result.get("query_sequence")
    if (
        parsed is None
        or result.get("accepted") is not True
        or result.get("status") not in {"available", "unavailable"}
        or isinstance(query_sequence, bool)
        or not isinstance(query_sequence, int)
        or not 1 <= query_sequence <= 2**64 - 1
    ):
        raise ValueError("production v3 golden command result is malformed")
    target, entry, attackers, defenders = parsed
    payload = result.get("combat_simulation_inputs")
    if not isinstance(payload, dict):
        raise ValueError("production v3 golden payload is malformed")
    base = payload.get("base_inputs")
    if not isinstance(base, dict) or not isinstance(base.get("armies"), list):
        raise ValueError("production v3 golden base slice is malformed")
    by_id = {
        row.get("army_id"): row
        for row in base["armies"]
        if isinstance(row, dict)
    }

    def scope_rows(ids: list[int]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for army_id in ids:
            row = by_id.get(army_id)
            if not isinstance(row, dict):
                raise ValueError("production v3 golden request army is absent")
            scope_role = row.get("scope_role")
            war_ids = row.get("war_ids")
            if not isinstance(scope_role, str) or not isinstance(war_ids, list):
                raise ValueError("production v3 golden army relation is malformed")
            rows.append(
                {
                    "army_id": army_id,
                    "scope_role": scope_role,
                    "war_ids": list(war_ids),
                }
            )
        return rows

    attacker_scope = scope_rows(attackers)
    defender_scope = scope_rows(defenders)
    selected_scope = [*attacker_scope, *defender_scope]
    relation = lambda row: (
        "enemy"
        if row["scope_role"] == "active_war_enemy"
        else "player_or_allied"
    )
    attacker_sides = {relation(row) for row in attacker_scope}
    defender_sides = {relation(row) for row in defender_scope}
    common_war_ids = list(selected_scope[0]["war_ids"])
    for row in selected_scope:
        common_war_ids = [
            war_id for war_id in common_war_ids
            if war_id in row["war_ids"]
        ]
    if (
        len(attacker_sides) != 1
        or len(defender_sides) != 1
        or attacker_sides == defender_sides
        or not common_war_ids
    ):
        raise ValueError("production v3 golden coalition binding is malformed")
    scope = {
        "army_ids": [*attackers, *defenders],
        "attacker_army_ids": attackers,
        "defender_army_ids": defenders,
        "selected_scope": selected_scope,
        "attacker_scope": attacker_scope,
        "defender_scope": defender_scope,
        "attacker_side": next(iter(attacker_sides)),
        "defender_side": next(iter(defender_sides)),
        "common_war_ids": common_war_ids,
    }
    normalized = normalize_combat_simulation_inputs_v3(
        payload,
        expected_target_province_id=target,
        expected_attacker_entry_province_id=entry,
        expected_encounter_scope=scope,
    )
    if combat_simulation_inputs_v3_status(normalized) != result["status"]:
        raise ValueError("production v3 golden status disagrees with payload")
    return normalized


class CombatPhaseInputsV3ProductionContractTests(unittest.TestCase):
    def test_capability_literal_and_132_partition_are_frozen(self) -> None:
        self.assertEqual(
            QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
            "game.command.query-combat-simulation-inputs-v3-N",
        )
        step = query_combat_simulation_inputs_v3_step(
            2596, 2597, [357, 33554657], [83886341]
        )
        self.assertEqual(
            step,
            "query-combat-simulation-inputs-v3-2596-2597-a-2-357-33554657-d-1-83886341",
        )
        self.assertEqual(
            parse_query_combat_simulation_inputs_v3_step(step),
            (2596, 2597, [357, 33554657], [83886341]),
        )
        partition = phase_event_ref_partition()
        self.assertEqual(len(partition["native_leaf_paths"]), 81)
        self.assertEqual(len(partition["offline_exact_paths"]), 51)
        self.assertEqual(
            partition["path_set_sha256"],
            {
                "native_leaf_exact": PHASE_EVENT_NATIVE_LEAF_EXACT_REFS_SHA256,
                "offline_exact": PHASE_EVENT_OFFLINE_EXACT_REFS_SHA256,
                "required": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
            },
        )
        self.assertEqual(len(OFFLINE_EXACT_REF_PATHS), 51)

    def test_complete_atomic_raw_slice_derives_all_132_refs(self) -> None:
        payload, scope = _production_payload()
        normalized = _normalize(payload, scope)
        self.assertEqual(combat_simulation_inputs_v3_status(normalized), "available")
        phase = normalized["phase_event_inputs"]
        self.assertTrue(phase["offline_admission"]["ready"])
        self.assertEqual(phase["offline_admission"]["native_leaf_exact_count"], 81)
        self.assertEqual(phase["offline_admission"]["offline_exact_count"], 51)
        self.assertEqual(len(phase["evaluation_contexts"]), 28)
        self.assertTrue(normalized["completeness"]["phase_event_inputs_ready"])
        self.assertFalse(normalized["completeness"]["monte_carlo_ready"])
        self.assertFalse(normalized["completeness"]["transition_fidelity_gate"])
        self.assertFalse(normalized["completeness"]["planner_usable"])
        self.assertFalse(normalized["completeness"]["active_attack_allowed"])
        self.assertFalse(
            normalized["completeness"]["phase_event_manifest_fidelity"]
            ["ast_evaluator_ready"]
        )
        evaluations = phase["row_evaluations"]
        self.assertEqual(
            evaluations["status"], "structurally_covered_fidelity_blocked"
        )
        self.assertEqual(evaluations["event_row_coverage"]["event_row_count"], 13)
        self.assertEqual(
            evaluations["event_row_coverage"]["trigger_ast_rows_covered"], 13
        )
        self.assertEqual(
            evaluations["event_row_coverage"]["chance_ast_rows_covered"], 13
        )
        self.assertEqual(
            evaluations["event_row_coverage"]["effect_ast_rows_covered"], 13
        )
        self.assertTrue(
            evaluations["event_row_coverage"]["structural_ready"]
        )
        self.assertFalse(evaluations["event_row_coverage"]["ready"])
        self.assertFalse(evaluations["ast_evaluator_ready"])
        candidate = evaluations["candidate_materialization_and_order"]
        self.assertTrue(candidate["materialization_input_ready"])
        self.assertTrue(candidate["ready"])
        self.assertIsNone(candidate["materialization_input_blocker"])
        self.assertEqual(
            candidate["candidate_source_proof_policy"],
            CANDIDATE_SOURCE_PROOF_POLICY,
        )
        self.assertEqual(len(candidate["production_proofs"]), 28)
        self.assertFalse(evaluations["battle_horizon_feedback"]["ready"])
        self.assertEqual(normalized["completeness"]["missing_observation_domains"], [])
        self.assertEqual(
            normalized["completeness"]["missing_fidelity_gates"],
            [
                "loaded_playset_verified",
                "ast_evaluator_ready",
                "original_trace_ready",
            ],
        )

        self.assertEqual(_normalize(normalized, scope), normalized)
        tampered = copy.deepcopy(normalized)
        tampered["phase_event_inputs"]["offline_admission"]["ready"] = False
        with self.assertRaisesRegex(ValueError, "derivation drifted"):
            _normalize(tampered, scope)

    def test_candidate_source_proof_is_digest_and_roster_bound(self) -> None:
        payload, scope = _production_payload()
        side = payload["phase_event_inputs"]["raw"]["sides"][0]
        proof = side["candidate_source_proof"]
        self.assertEqual(
            proof["sequence_sha256"],
            candidate_source_sequence_sha256(0, proof["ordered_sources"]),
        )

        digest_tamper = copy.deepcopy(payload)
        digest_tamper["phase_event_inputs"]["raw"]["sides"][0][
            "candidate_source_proof"
        ]["sequence_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            _normalize(digest_tamper, scope)

        def roster_tamper(field: str, replacement: int) -> dict[str, object]:
            mutated = copy.deepcopy(payload)
            mutated_proof = mutated["phase_event_inputs"]["raw"]["sides"][0][
                "candidate_source_proof"
            ]
            knight = next(
                row
                for row in mutated_proof["ordered_sources"]
                if row["role"] == "knight"
            )
            knight[field] = replacement
            mutated_proof["sequence_sha256"] = candidate_source_sequence_sha256(
                0, mutated_proof["ordered_sources"]
            )
            return mutated

        knight = next(
            row for row in proof["ordered_sources"] if row["role"] == "knight"
        )
        for field, replacement in (
            ("source_army_id", 2_000_000_000),
            ("source_regiment_id", int(knight["source_regiment_id"]) + 1),
            ("character_id", int(knight["character_id"]) + 1),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                _normalize(roster_tamper(field, replacement), scope)

        reordered = copy.deepcopy(payload)
        reordered_proof = reordered["phase_event_inputs"]["raw"]["sides"][0][
            "candidate_source_proof"
        ]
        knight_indices = [
            index
            for index, row in enumerate(reordered_proof["ordered_sources"])
            if row["role"] == "knight"
        ]
        self.assertGreaterEqual(len(knight_indices), 2)
        first, second = knight_indices[:2]
        reordered_proof["ordered_sources"][first], reordered_proof[
            "ordered_sources"
        ][second] = (
            reordered_proof["ordered_sources"][second],
            reordered_proof["ordered_sources"][first],
        )
        reordered_proof["sequence_sha256"] = candidate_source_sequence_sha256(
            0, reordered_proof["ordered_sources"]
        )
        with self.assertRaisesRegex(ValueError, "subsequences differ"):
            _normalize(reordered, scope)

    def test_offline_formulas_preserve_thresholds_tiers_and_source_order(self) -> None:
        payload, scope = _production_payload()
        raw = payload["phase_event_inputs"]["raw"]
        root = raw["characters"][0]
        root["is_ai"] = False
        root["stalwart_leader"] = True
        root["prowess"] = 20
        root["wounded_rank_raw"] = 300_000
        root["traits_or_groups"]["wounded_3"] = True
        root["garuda_court_position"] = True
        own_side = raw["sides"][0]
        enemy_side = raw["sides"][1]
        own_side["side_strength_raw"] = 600_000
        enemy_side["side_strength_raw"] = 100_000
        own_side["side_army_size_raw"] = 66_000_000
        enemy_side["side_army_size_raw"] = 100_000_000
        ally = next(
            row
            for row in raw["characters"]
            if row["encounter_role"] == "attacker" and row is not root
        )
        ally["accolade"] = _optional(70001)
        ally["is_acclaimed"] = True
        ally["accolade_parameters"]["accolade_defends_family_high"] = True
        enemy = next(
            row for row in raw["characters"] if row["encounter_role"] == "defender"
        )
        enemy["accolade"] = _optional(70002)
        enemy["is_acclaimed"] = True
        enemy["accolade_parameters"][
            "accolade_increase_hostile_knight_death_medium"
        ] = True
        for row in raw["faith_hostility"]:
            if row["root_character_id"] == root["character_id"]:
                row["hostility_level_raw"] = 3
        normalized = _normalize(payload, scope)
        context = normalized["phase_event_inputs"]["evaluation_contexts"][0]
        refs = context["offline_state_refs"]
        self.assertEqual(refs["derived.accolade_qualification_wound_factor_raw"], 25_000)
        self.assertTrue(refs["derived.root_player_stalwart"])
        self.assertFalse(refs["derived.root_ai_stalwart"])
        self.assertEqual(refs["derived.root_injury_factor_30_with_garuda_raw"], 60_000)
        self.assertTrue(refs["derived.own_side_more_than_five_times_enemy"])
        self.assertEqual(refs["derived.same_house_defends_family_factor_raw"], 25_000)
        self.assertEqual(refs["derived.enemy_hostile_knight_death_accolade_factor_raw"], 150_000)
        self.assertTrue(refs["root.accolade_unlocks.fanatic.valid"])
        self.assertTrue(refs["root.accolade_unlocks.valiant.valid"])
        first_candidate = context["candidate_rows"][0]
        expected_weight = 10_000_000
        candidate_raw = next(
            row for row in raw["characters"]
            if row["character_id"] == first_candidate["character_id"]
        )
        if candidate_raw["is_acclaimed"]:
            expected_weight = expected_weight * 75_000 // 100_000
        self.assertEqual(
            first_candidate["candidate_refs"][
                "derived.stock_enemy_knight_selection_weight_raw"
            ],
            expected_weight,
        )

    def test_all_13_accolade_branch_asts_and_boundaries_are_explicit(self) -> None:
        maa_by_branch = {
            "skirmisher": "skirmishers_raw",
            "archer": "non_crossbow_archers_raw",
            "crossbowmen": "crossbow_family_raw",
            "pike": "pikemen_raw",
            "vanguard": "heavy_infantry_raw",
            "outrider": "light_cavalry_raw",
            "lancer": "heavy_cavalry_raw",
            "camelry": "camel_cavalry_raw",
            "elephantry": "elephant_cavalry_raw",
            "horse_archer": "archer_cavalry_raw",
            "gunpowder": "gunpowder_raw",
        }
        culture_gate = {
            "crossbowmen": ("innovations", "innovation_advanced_bowmaking"),
            "vanguard": ("innovations", "innovation_quilted_armor"),
            "lancer": ("innovations", "innovation_arched_saddle"),
            "camelry": ("innovations", "innovation_war_camels"),
            "elephantry": ("innovations", "innovation_elephantry"),
            "horse_archer": (
                "culture_parameters",
                "unlock_maa_horse_archers",
            ),
            "gunpowder": ("innovations", "innovation_gunpowder"),
        }

        def inputs():
            payload, _scope = _production_payload()
            raw = payload["phase_event_inputs"]["raw"]
            root = raw["characters"][0]
            army = next(
                row for row in raw["armies"]
                if row["army_id"] == root["source_army_id"]
            )
            army["maa_regiment_count_raw"] = 0
            army["maa_counts_raw"] = {key: 0 for key in _MAA_COUNT_KEYS}
            raw["sides"][0]["side_army_size_raw"] = 0
            raw["sides"][1]["side_army_size_raw"] = 100_000_000
            hostility = [
                row for row in raw["faith_hostility"]
                if row["root_character_id"] == root["character_id"]
            ]
            return root, army["maa_counts_raw"], raw["sides"], hostility

        def evaluate(root, maa, sides, hostility):
            return {
                key
                for key, row in _accolade_unlocks(
                    root=root,
                    maa=maa,
                    own_side=sides[0],
                    enemy_side=sides[1],
                    hostility=hostility,
                ).items()
                if row["valid"]
            }

        for branch, maa_key in maa_by_branch.items():
            with self.subTest(branch=branch, case="outer_maa_positive"):
                root, maa, sides, hostility = inputs()
                maa[maa_key] = 100_000
                self.assertEqual(evaluate(root, maa, sides, hostility), {branch})

            with self.subTest(branch=branch, case="attribute_suppresses"):
                root, maa, sides, hostility = inputs()
                maa[maa_key] = 100_000
                root["attribute_unlock_variables"][branch] = True
                if branch in culture_gate:
                    container, key = culture_gate[branch]
                    # A gated attribute remains false until its culture arm
                    # also succeeds.
                    self.assertEqual(
                        evaluate(root, maa, sides, hostility), {branch}
                    )
                    root[container][key] = True
                self.assertEqual(evaluate(root, maa, sides, hostility), set())

        root, maa, sides, hostility = inputs()
        hostility[0]["hostility_level_raw"] = 3
        self.assertEqual(evaluate(root, maa, sides, hostility), {"fanatic"})

        root, maa, sides, hostility = inputs()
        sides[0]["side_army_size_raw"] = 66_000_000
        self.assertEqual(evaluate(root, maa, sides, hostility), {"valiant"})
        sides[0]["side_army_size_raw"] = 65_900_000
        self.assertEqual(evaluate(root, maa, sides, hostility), set())
        root["attribute_unlock_variables"]["valiant"] = True
        sides[0]["side_army_size_raw"] = 66_000_000
        self.assertEqual(evaluate(root, maa, sides, hostility), set())

        root, maa, sides, hostility = inputs()
        maa["skirmishers_raw"] = 100_000
        root["attribute_unlock_variables"]["skirmisher"] = True
        self.assertEqual(evaluate(root, maa, sides, hostility), set())
        root["accolade"] = _optional(70_003)
        root["is_acclaimed"] = True
        root["accolade_has_men_at_arms_category"] = True
        self.assertEqual(evaluate(root, maa, sides, hostility), {"skirmisher"})

        root, maa, sides, hostility = inputs()
        maa["skirmishers_raw"] = 100_000
        root["tourney_bow_xp_raw"] = 2_999_999
        self.assertEqual(evaluate(root, maa, sides, hostility), {"skirmisher"})
        root["tourney_bow_xp_raw"] = 3_000_000
        self.assertEqual(evaluate(root, maa, sides, hostility), set())

    def test_missing_named_leaf_or_partial_unavailable_slice_fails_closed(self) -> None:
        payload, scope = _production_payload()
        del payload["phase_event_inputs"]["raw"]["characters"][0][
            "innovations"
        ]["innovation_quilted_armor"]
        with self.assertRaisesRegex(ValueError, "schema is malformed"):
            _normalize(payload, scope)

        payload, scope = _production_payload()
        phase = payload["phase_event_inputs"]
        phase.update(
            status="unavailable",
            raw=None,
            advantage_model=None,
            unavailable_reason="native_phase_identity_revalidation_failed",
        )
        normalized = _normalize(payload, scope)
        self.assertEqual(combat_simulation_inputs_v3_status(normalized), "unavailable")
        self.assertIsNone(normalized["phase_event_inputs"]["raw"])
        phase["raw"] = {}
        with self.assertRaisesRegex(ValueError, "must not publish partial"):
            _normalize(payload, scope)

    def test_raw_numeric_invariants_match_native_fixed_point_domains(self) -> None:
        payload, scope = _production_payload()
        payload["phase_event_inputs"]["raw"]["armies"][0][
            "maa_regiment_count_raw"
        ] = 0
        with self.assertRaisesRegex(ValueError, "exceed the total"):
            _normalize(payload, scope)

        payload, scope = _production_payload()
        payload["phase_event_inputs"]["raw"]["sides"][0][
            "side_army_size_raw"
        ] = 1
        with self.assertRaisesRegex(ValueError, "whole Q100000"):
            _normalize(payload, scope)

        payload, scope = _production_payload()
        payload["phase_event_inputs"]["raw"]["sides"][0][
            "side_strength_raw"
        ] = -1
        normalized = _normalize(payload, scope)
        self.assertEqual(
            normalized["phase_event_inputs"]["raw"]["sides"][0][
                "side_strength_raw"
            ],
            -1,
        )

    def test_contract_recipe_matches_code_partition(self) -> None:
        recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
        partition = phase_event_ref_partition()
        self.assertEqual(recipe["required_state_refs"]["count"], 132)
        self.assertEqual(
            recipe["required_state_refs"]["sha256"],
            PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
        )
        self.assertEqual(recipe["state_ref_coverage"], {
            key: partition[key]
            for key in (
                "manifest_domain_counts", "abi_level_counts",
                "path_set_sha256", "native_payload_policy",
            )
        })
        self.assertEqual(
            recipe["simulation_fidelity_boundary"],
            {
                "loaded_playset_verified": False,
                "ast_evaluator_ready": False,
                "original_trace_ready": False,
                "fidelity_gate": False,
                "planner_usable": False,
                "active_attack_allowed": False,
            },
        )
        self.assertEqual(
            recipe["ast_evaluator"],
            {
                "schema_version": PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
                "version": PHASE_EVENT_AST_EVALUATOR_VERSION,
                "sha256": PHASE_EVENT_AST_EVALUATOR_SHA256,
                "event_family_golden": (
                    "tests/fixtures/combat_phase_events/"
                    "v3_ast_evaluator_family_golden.json"
                ),
                "row_counts": {"total": 13, "commander": 4, "knight": 9},
                "owner_scope": "absent",
                "structural_ast_coverage_ready": True,
                "native_candidate_order_ready": True,
                "battle_horizon_effect_feedback_ready": False,
                "original_trace_ready": False,
            },
        )
        self.assertEqual(
            recipe["production_golden_interface"],
            {
                "available_path": (
                    "native_bridge/research/fixtures/"
                    "combat_simulation_inputs_v3_production_available.json"
                ),
                "unavailable_path": (
                    "native_bridge/research/fixtures/"
                    "combat_simulation_inputs_v3_production_unavailable.json"
                ),
                "envelope_exact_keys": [
                    "type", "protocol_version", "request_id", "ok", "result"
                ],
                "result_exact_keys": [
                    "step", "accepted", "status", "query_sequence",
                    "combat_simulation_inputs",
                ],
                "result_statuses": ["available", "unavailable"],
                "named_objects_policy": (
                    "all_frozen_keys_present_even_when_false_or_zero"
                ),
                "scope_binding_policy": (
                    "canonical_step_plus_base_v2_scenario_and_army_relations"
                ),
            },
        )

    def test_native_golden_envelope_validator_is_ready_for_both_statuses(self) -> None:
        payload, _scope = _production_payload()
        for status in ("available", "unavailable"):
            with self.subTest(status=status):
                candidate = copy.deepcopy(payload)
                if status == "unavailable":
                    candidate["phase_event_inputs"].update(
                        status="unavailable",
                        raw=None,
                        advantage_model=None,
                        unavailable_reason=(
                            "native_phase_identity_revalidation_failed"
                        ),
                    )
                fixture = {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": f"fixture-production-v3-{status}",
                    "ok": True,
                    "result": {
                        "step": (
                            "query-combat-simulation-inputs-v3-2596-2597-"
                            "a-2-357-33554657-d-1-83886341"
                        ),
                        "accepted": True,
                        "status": status,
                        "query_sequence": 1,
                        "combat_simulation_inputs": candidate,
                    },
                }
                normalized = _normalize_native_golden_envelope(fixture)
                self.assertEqual(
                    combat_simulation_inputs_v3_status(normalized), status
                )

    def test_full_native_production_goldens_normalize_exactly(self) -> None:
        expected = (
            (NATIVE_AVAILABLE_GOLDEN_PATH, "available"),
            (NATIVE_UNAVAILABLE_GOLDEN_PATH, "unavailable"),
        )
        for path, status in expected:
            with self.subTest(status=status):
                self.assertTrue(path.is_file(), path)
                envelope = json.loads(path.read_text(encoding="utf-8"))
                normalized = _normalize_native_golden_envelope(envelope)
                self.assertEqual(
                    combat_simulation_inputs_v3_status(normalized), status
                )
                phase = normalized["phase_event_inputs"]
                if status == "available":
                    self.assertEqual(len(phase["raw"]["characters"]), 2)
                    self.assertEqual(len(phase["raw"]["armies"]), 2)
                    self.assertEqual(len(phase["raw"]["sides"]), 2)
                    self.assertEqual(
                        len(
                            phase["advantage_model"][
                                "constructor_sources"
                            ]
                        ),
                        15,
                    )
                    self.assertTrue(phase["offline_admission"]["ready"])
                else:
                    self.assertIsNone(phase["raw"])
                    self.assertIsNone(phase["advantage_model"])
                    self.assertFalse(phase["offline_admission"]["ready"])


if __name__ == "__main__":
    unittest.main()
