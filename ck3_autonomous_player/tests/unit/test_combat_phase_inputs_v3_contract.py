from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.combat_contract import (
    PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
    PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
    PHASE_EVENT_STOCK_MANIFEST_SHA256,
    _V3_ADVANTAGE_SOURCE_ORDER,
    _V3_ADVANTAGE_STAGE_SIDES,
    _V3_CONSTRUCTOR_CALL_ORDER,
    _V3_NATIVE_LEAF_EXACT_REF_PATHS,
    _V3_REQUIRED_ARMY_REF_PATHS,
    _V3_TEST_ONLY_BLOCKERS,
    _canonical_character_ref_paths,
    _canonical_side_ref_paths,
    _expected_phase_characters,
    _phase_event_ref_coverage_v3_test_only,
    normalize_combat_simulation_inputs_v3_test_only,
    parse_query_combat_simulation_inputs_step,
    parse_query_combat_simulation_inputs_v3_test_step,
    query_combat_simulation_inputs_v3_test_step,
)


RECIPE_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "combat_phase_events"
    / "v3_test_only_contract_recipe.json"
)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _base_fixture() -> dict[str, object]:
    recipe = _load(RECIPE_PATH)
    return _load(PROJECT_ROOT / str(recipe["base_fixture"]))


def _expected_scope(base: dict[str, object]) -> dict[str, object]:
    scenario = base["scenario"]
    armies = base["armies"]
    assert isinstance(scenario, dict)
    assert isinstance(armies, list)
    selected_scope = [
        {
            "army_id": army["army_id"],
            "scope_role": army["scope_role"],
            "war_ids": list(army["war_ids"]),
        }
        for army in armies
    ]
    attacker_count = len(scenario["attacker_army_ids"])
    common_war_ids = list(selected_scope[0]["war_ids"])
    for army in selected_scope[1:]:
        common_war_ids = [
            war_id for war_id in common_war_ids if war_id in army["war_ids"]
        ]
    return {
        "army_ids": [army["army_id"] for army in selected_scope],
        "attacker_army_ids": list(scenario["attacker_army_ids"]),
        "defender_army_ids": list(scenario["defender_army_ids"]),
        "selected_scope": selected_scope,
        "attacker_scope": selected_scope[:attacker_count],
        "defender_scope": selected_scope[attacker_count:],
        "attacker_side": scenario["attacker_side"],
        "defender_side": scenario["defender_side"],
        "common_war_ids": common_war_ids,
    }


def _synthetic_ref(path: str) -> dict[str, object]:
    if path == "army.current_eligible_soldiers":
        return {"path": path, "value_type": "signed_int64", "value": 0}
    if path in {
        "root.skills.martial_raw",
        "root.skills.learning_raw",
        "root.skills.prowess_raw",
    }:
        return {"path": path, "value_type": "signed_int32", "value": 0}
    if path.endswith("_raw"):
        return {"path": path, "value_type": "signed_q100000", "value": 0}
    if path.endswith("_ids") or any(
        token in path
        for token in ("membership", "ordered_enemy_knights", "enemy_faiths")
    ):
        return {"path": path, "value_type": "full_id_array", "value": []}
    bool_markers = (
        ".alive",
        ".exists",
        ".is_",
        ".traits.",
        ".perks.",
        ".parameters.",
        ".tenets.",
        ".valid",
        ".germanic",
        ".garuda",
        ".heritage_",
        ".can_be_",
        ".recently_disembarked",
        ".unreformed_faith",
    )
    if any(marker in path for marker in bool_markers):
        return {
            "path": path,
            "value_type": "bool",
            "value": path.endswith(".alive") or path.endswith(".exists"),
        }
    if path.endswith("_id") or path in {
        "root.liege",
        "combat_side.commander",
        "side.commander",
    }:
        return {"path": path, "value_type": "full_id", "value": 1}
    return {
        "path": path,
        "value_type": "not_applicable",
        "value": "synthetic_contract_sentinel",
    }


def _refs(paths: set[str]) -> list[dict[str, object]]:
    return [_synthetic_ref(path) for path in sorted(paths)]


def _v3_payload() -> tuple[dict[str, object], dict[str, object]]:
    fixture = _base_fixture()
    base = copy.deepcopy(fixture["combat_simulation_inputs"])
    assert isinstance(base, dict)
    manifest_refs = _V3_NATIVE_LEAF_EXACT_REF_PATHS
    character_paths = _canonical_character_ref_paths(manifest_refs)
    side_paths = _canonical_side_ref_paths(manifest_refs)
    global_paths = {
        path for path in manifest_refs if path.startswith("game_rules")
    }
    expected_characters = _expected_phase_characters(base)
    characters = [
        {
            **expected,
            "state_refs": _refs(character_paths),
        }
        for expected in expected_characters
    ]
    armies = [
        {
            "army_id": army["army_id"],
            "encounter_role": army["encounter_role"],
            "state_refs": _refs(_V3_REQUIRED_ARMY_REF_PATHS),
        }
        for army in base["armies"]
    ]
    scenario = base["scenario"]
    assert isinstance(scenario, dict)
    sides = []
    for side_index, encounter_role in enumerate(("attacker", "defender")):
        side_army_ids = list(
            scenario[
                "attacker_army_ids"
                if side_index == 0
                else "defender_army_ids"
            ]
        )
        sides.append(
            {
                "side_index": side_index,
                "encounter_role": encounter_role,
                "ordered_army_ids": side_army_ids,
                "ordered_character_ids": [
                    character["character_id"]
                    for character in characters
                    if character["encounter_role"] == encounter_role
                ],
                "primary_participant_character_id": 1,
                "primary_source_army_id": side_army_ids[0],
                "primary_selection_policy": (
                    "first_inserted_army_owner_with_native_preservation"
                ),
                "side_strength_raw": 0,
                "side_strength_scale": 100_000,
                "side_army_size_raw": 0,
                "side_army_size_scale": 100_000,
                "state_refs": _refs(side_paths),
            }
        )
    source_rows = [
        {
            "stage_order": index,
            "append_order": None,
            "stage": kind,
            "side": _V3_ADVANTAGE_STAGE_SIDES[kind],
            "source_key": None,
            "effect_advantage_points": None,
            "scale_raw": 100_000,
            "signed_contribution_raw": 0,
            "accumulator_before_raw": 0,
            "accumulator_after_raw": 0,
            "selected": False,
            "applied": False,
            "skip_reason": "not_selected_in_synthetic_fixture",
        }
        for index, kind in enumerate(_V3_ADVANTAGE_SOURCE_ORDER)
    ]
    side_inputs = []
    for side_index, side in enumerate(("attacker", "defender")):
        ordered_army_ids = list(
            scenario[
                "attacker_army_ids"
                if side_index == 0
                else "defender_army_ids"
            ]
        )
        side_inputs.append(
            {
                "side": side,
                "primary_army_id": ordered_army_ids[0],
                "ordered_army_ids": ordered_army_ids,
                "supply": {
                    "selected_key": "supply_state_supplied_advantage",
                    "selected_effect_identity": "synthetic:db+F38",
                    "selected_effect_points": 0,
                    "eligible_soldiers_total": 0,
                    "eligible_soldiers_supplied": 0,
                    "eligible_soldiers_running_low": 0,
                    "eligible_soldiers_starving": 0,
                },
                "primary_army_gathering_raw": 0,
                "owner_character_id": 1,
                "owner_debt_selector_raw": 0,
                "treasury_debt_selector_raw": None,
            }
        )
    dynamic_sides = []
    for side_index, side in enumerate(("attacker", "defender")):
        commander = next(
            character
            for character in characters
            if character["encounter_role"] == side
            and "commander" in character["phase_roles"]
        )
        dynamic_sides.append(
            {
                "side": side,
                "battle_commander_character_id": commander["character_id"],
                "battle_commander_selected": True,
                "battle_commander_selection": "native_0x23C8A60",
                "primary_army_gathering_raw": 0,
                "gathering": False,
                "relation_kind_raw": 0,
                "roll_points": 0,
                "roll_raw": 0,
                "target_conditionals_residual_raw": 0,
                "commander_dynamic_raw": 0,
                "side_dynamic_raw": 0,
                "side_total_raw": 0,
                "contribution_to_resolved_raw": 0,
            }
        )
    phase = {
        "status": "partial",
        "rules_source": "stock-installation-static-manifest",
        "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
        "required_state_refs": {
            "count": PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
            "sha256": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
        },
        "state_ref_coverage": _phase_event_ref_coverage_v3_test_only(),
        "scope_mode": "hypothetical_precontact_offline_ast",
        "characters": characters,
        "armies": armies,
        "sides": sides,
        "global_state_refs": _refs(global_paths),
        "advantage_model": {
            "status": "available",
            "scale": 100_000,
            "scenario_policy": (
                "explicit_hypothetical_fixed_at_contact_no_reinforcements"
            ),
            "observation_origin": "independent_synthetic_contract_fixture",
            "side_inputs": side_inputs,
            "constructor_call_order": list(_V3_CONSTRUCTOR_CALL_ORDER),
            "constructor_sources": source_rows,
            "base_static_accumulator_raw": 0,
            "resolved_dynamic": {
                "status": "available",
                "helper_status": "original_helpers_matched",
                "context_mode": "temporary_unregistered_local_context",
                "roll_policy": "zero_in_query_sampled_offline",
                "sides": dynamic_sides,
                "side_0_dynamic_raw": 0,
                "side_1_dynamic_raw": 0,
                "resolved_advantage_at_zero_roll_raw": 0,
                "original_total_helper_raw": 0,
                "original_total_helper_match": True,
            },
            "unavailable_reason": None,
        },
        "row_evaluations": {
            "status": "unsupported",
            "scope": "hypothetical_precontact",
            "reason": "hypothetical_precontact_has_no_real_combat_side",
        },
        "offline_admission": {
            "raw_state_ref_contract_complete": True,
            "advantage_model_contract_complete": True,
            "native_raw_state_refs_ready": False,
            "native_advantage_model_ready": False,
            "loaded_playset_verified": False,
            "ast_evaluator_ready": False,
            "ready": False,
            "missing_required_domains": list(_V3_TEST_ONLY_BLOCKERS),
        },
        "unavailable_reason": "v3_test_only_contract_not_production_ready",
    }
    payload = {
        "schema_version": 3,
        "contract_stage": "test_only_unadvertised",
        "rules_manifest_sha256": PHASE_EVENT_STOCK_MANIFEST_SHA256,
        "base_inputs": base,
        "phase_event_inputs": phase,
        "completeness": {
            "observation_slice": (
                "precontact-phase-event-inputs-v3-test-only"
            ),
            "base_input_observation_ready": True,
            "phase_raw_observation_ready": False,
            "offline_ast_admission_ready": False,
            "input_observation_ready": False,
            "monte_carlo_ready": False,
            "missing_required_domains": list(_V3_TEST_ONLY_BLOCKERS),
        },
    }
    return payload, _expected_scope(base)


def _normalize(payload: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
    base = payload["base_inputs"]
    assert isinstance(base, dict)
    scenario = base["scenario"]
    assert isinstance(scenario, dict)
    return normalize_combat_simulation_inputs_v3_test_only(
        payload,
        expected_target_province_id=int(base["target_province_id"]),
        expected_attacker_entry_province_id=int(
            scenario["attacker_entry_province_id"]
        ),
        expected_encounter_scope=scope,
    )


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


class CombatPhaseInputsV3ContractTests(unittest.TestCase):
    def test_reserved_literal_is_canonical_but_not_a_v2_step(self) -> None:
        step = query_combat_simulation_inputs_v3_test_step(
            2596, 2597, [357, 33554657], [83886341]
        )
        self.assertEqual(
            step,
            "query-combat-simulation-inputs-v3-2596-2597-a-2-357-33554657-d-1-83886341",
        )
        self.assertEqual(
            parse_query_combat_simulation_inputs_v3_test_step(step),
            (2596, 2597, [357, 33554657], [83886341]),
        )
        self.assertIsNone(parse_query_combat_simulation_inputs_step(step))

    def test_recipe_and_manifest_binding_are_frozen(self) -> None:
        recipe = _load(RECIPE_PATH)
        self.assertEqual(
            recipe["rules_manifest_sha256"],
            PHASE_EVENT_STOCK_MANIFEST_SHA256,
        )
        self.assertEqual(
            recipe["required_state_refs"],
            {
                "count": PHASE_EVENT_REQUIRED_STATE_REF_COUNT,
                "sha256": PHASE_EVENT_REQUIRED_STATE_REFS_SHA256,
            },
        )
        self.assertEqual(
            recipe["constructor_source_order"],
            _V3_ADVANTAGE_SOURCE_ORDER,
        )
        coverage = _phase_event_ref_coverage_v3_test_only()
        self.assertEqual(recipe["state_ref_coverage"], coverage)
        self.assertEqual(coverage["abi_level_counts"]["native_leaf_exact"], 47)
        self.assertEqual(coverage["abi_level_counts"]["offline_derived_exact"], 15)
        self.assertEqual(coverage["abi_level_counts"]["remaining_unclosed"], 70)
        self.assertEqual(coverage["abi_level_counts"]["production_live_observed"], 0)

    def test_complete_synthetic_raw_slice_remains_unavailable_for_production(self) -> None:
        payload, scope = _v3_payload()
        normalized = _normalize(payload, scope)
        phase = normalized["phase_event_inputs"]
        self.assertEqual(len(phase["characters"]), 28)
        self.assertEqual(
            len({
                (
                    row["character_id"],
                    row["source_army_id"],
                    tuple(row["phase_roles"]),
                )
                for row in phase["characters"]
            }),
            28,
        )
        self.assertFalse(phase["offline_admission"]["ready"])
        self.assertFalse(normalized["completeness"]["input_observation_ready"])
        self.assertFalse(normalized["completeness"]["monte_carlo_ready"])
        self.assertFalse(_contains_key(phase, "combat_id"))
        first_refs = {
            ref["path"]: ref
            for ref in phase["characters"][0]["state_refs"]
        }
        for skill_path in (
            "root.skills.martial_raw",
            "root.skills.learning_raw",
            "root.skills.prowess_raw",
        ):
            self.assertEqual(first_refs[skill_path]["value_type"], "signed_int32")
        all_paths = {
            ref["path"]
            for character in phase["characters"]
            for ref in character["state_refs"]
        }
        self.assertNotIn("root.house_id", all_paths)
        self.assertFalse(any(path.startswith("derived.") for path in all_paths))

    def test_missing_or_null_character_ref_fails_closed(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        characters = phase["characters"]
        assert isinstance(characters, list)
        refs = characters[0]["state_refs"]
        assert isinstance(refs, list)
        refs.pop()
        with self.assertRaisesRegex(ValueError, "state ref coverage mismatch"):
            _normalize(payload, scope)

        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        characters = phase["characters"]
        assert isinstance(characters, list)
        refs = characters[0]["state_refs"]
        assert isinstance(refs, list)
        refs[0]["value"] = None
        with self.assertRaises(ValueError):
            _normalize(payload, scope)

    def test_advantage_sources_apply_sign_and_clamp_after_each_row(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        advantage = phase["advantage_model"]
        assert isinstance(advantage, dict)
        rows = advantage["constructor_sources"]
        assert isinstance(rows, list)
        attacker_supply = next(row for row in rows if row["stage"] == "supply_0")
        defender_supply = next(row for row in rows if row["stage"] == "supply_1")
        attacker_supply.update(
            append_order=0,
            selected=True,
            applied=True,
            source_key="db+F38:synthetic_supplied",
            effect_advantage_points=200,
            signed_contribution_raw=20_000_000,
            skip_reason=None,
        )
        defender_supply.update(
            append_order=1,
            selected=True,
            applied=True,
            source_key="db+F48:synthetic_running_low",
            effect_advantage_points=50,
            signed_contribution_raw=-5_000_000,
            skip_reason=None,
        )
        accumulator = 0
        for row in rows:
            row["accumulator_before_raw"] = accumulator
            accumulator = max(
                -10_000_000,
                min(10_000_000, accumulator + row["signed_contribution_raw"]),
            )
            row["accumulator_after_raw"] = accumulator
        advantage["base_static_accumulator_raw"] = 5_000_000
        resolved = advantage["resolved_dynamic"]
        assert isinstance(resolved, dict)
        resolved["resolved_advantage_at_zero_roll_raw"] = 5_000_000
        resolved["original_total_helper_raw"] = 5_000_000
        normalized = _normalize(payload, scope)
        self.assertEqual(
            normalized["phase_event_inputs"]["advantage_model"][
                "base_static_accumulator_raw"
            ],
            5_000_000,
        )

    def test_gathering_army_side_input_and_stages_are_exact(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        advantage = phase["advantage_model"]
        assert isinstance(advantage, dict)
        rows = advantage["constructor_sources"]
        assert isinstance(rows, list)
        for row in rows:
            if row["stage"] in {"gathering_army_0", "gathering_army_1"}:
                row["skip_reason"] = "primary_army_not_gathering"

        normalized = _normalize(payload, scope)
        normalized_advantage = normalized["phase_event_inputs"][
            "advantage_model"
        ]
        self.assertEqual(
            [
                row["stage"]
                for row in normalized_advantage["constructor_sources"]
                if row["stage"].startswith("gathering_army_")
            ],
            ["gathering_army_0", "gathering_army_1"],
        )
        self.assertTrue(
            all(
                row["skip_reason"] == "primary_army_not_gathering"
                for row in normalized_advantage["constructor_sources"]
                if row["stage"].startswith("gathering_army_")
            )
        )
        self.assertTrue(
            all(
                "primary_army_gathering_raw" in side
                for side in normalized_advantage["side_inputs"]
            )
        )

        legacy_payload, legacy_scope = _v3_payload()
        legacy_phase = legacy_payload["phase_event_inputs"]
        assert isinstance(legacy_phase, dict)
        legacy_advantage = legacy_phase["advantage_model"]
        assert isinstance(legacy_advantage, dict)
        legacy_side = legacy_advantage["side_inputs"][0]
        legacy_side["primary_army_recently_disembarked_raw"] = legacy_side.pop(
            "primary_army_gathering_raw"
        )
        with self.assertRaisesRegex(ValueError, "schema is malformed"):
            _normalize(legacy_payload, legacy_scope)

    def test_fake_precontact_combat_id_is_rejected_by_exact_schema(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        evaluations = phase["row_evaluations"]
        assert isinstance(evaluations, dict)
        evaluations["combat_id"] = 123
        with self.assertRaisesRegex(ValueError, "schema is malformed"):
            _normalize(payload, scope)

    def test_dynamic_helper_total_mismatch_is_rejected(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        advantage = phase["advantage_model"]
        assert isinstance(advantage, dict)
        resolved = advantage["resolved_dynamic"]
        assert isinstance(resolved, dict)
        resolved["original_total_helper_raw"] = 1
        with self.assertRaisesRegex(ValueError, "original total helper"):
            _normalize(payload, scope)

    def test_helper_failure_publishes_no_partial_advantage_numbers(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        advantage = phase["advantage_model"]
        assert isinstance(advantage, dict)
        advantage.update(
            status="unavailable",
            side_inputs=None,
            constructor_sources=None,
            base_static_accumulator_raw=None,
            resolved_dynamic=None,
            unavailable_reason="native_helper_validation_failed",
        )
        normalized = _normalize(payload, scope)
        normalized_advantage = normalized["phase_event_inputs"]["advantage_model"]
        self.assertEqual(normalized_advantage["status"], "unavailable")
        self.assertIsNone(normalized_advantage["constructor_sources"])
        self.assertFalse(normalized["completeness"]["input_observation_ready"])

    def test_side_helpers_bind_primary_and_exact_state_refs(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        sides = phase["sides"]
        assert isinstance(sides, list)
        attacker = sides[0]
        assert isinstance(attacker, dict)
        attacker["primary_source_army_id"] = 99
        with self.assertRaisesRegex(ValueError, "primary source"):
            _normalize(payload, scope)

        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        sides = phase["sides"]
        assert isinstance(sides, list)
        attacker = sides[0]
        assert isinstance(attacker, dict)
        attacker["side_strength_raw"] = 1
        with self.assertRaisesRegex(ValueError, "disagree with state refs"):
            _normalize(payload, scope)

    def test_side_helper_failure_makes_whole_phase_slice_unavailable(self) -> None:
        payload, scope = _v3_payload()
        phase = payload["phase_event_inputs"]
        assert isinstance(phase, dict)
        phase.update(
            status="unavailable",
            characters=None,
            armies=None,
            sides=None,
            global_state_refs=None,
            advantage_model=None,
            row_evaluations=None,
            unavailable_reason="side_strength_helper_mismatch",
        )
        normalized = _normalize(payload, scope)
        normalized_phase = normalized["phase_event_inputs"]
        self.assertEqual(normalized_phase["status"], "unavailable")
        self.assertIsNone(normalized_phase["sides"])

        phase["sides"] = []
        with self.assertRaisesRegex(ValueError, "must not publish partial"):
            _normalize(payload, scope)


if __name__ == "__main__":
    unittest.main()
