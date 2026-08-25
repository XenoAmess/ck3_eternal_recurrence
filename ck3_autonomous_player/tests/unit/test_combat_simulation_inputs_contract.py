from __future__ import annotations

from pathlib import Path
import copy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.combat_contract import (
    MAX_COMBAT_SIMULATION_REQUEST_ARMY_IDS,
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    combat_simulation_inputs_status,
    combat_simulation_encounter_scope,
    is_native_combat_query_step,
    normalize_combat_simulation_request,
    normalize_combat_simulation_inputs,
    parse_query_combat_simulation_inputs_step,
    query_combat_simulation_inputs_step,
)
from xar_autoplayer.bridge.native_driver import _action_steps


def _army(army_id: int) -> dict[str, object]:
    return {"army_id": army_id}


def _snapshot() -> dict[str, object]:
    return {
        "player_armies": [_army(11)],
        "active_wars": [
            {
                "war_id": 101,
                "allied_armies": [_army(11), _army(12)],
                "enemy_armies": [_army(21), _army(22)],
            },
            {
                "war_id": 102,
                "allied_armies": [_army(12)],
                "enemy_armies": [_army(22), _army(23)],
            },
        ],
    }


def _combat_regiment(regiment_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "regiment_id": regiment_id,
        "identity_valid": True,
        "current_soldiers": 400,
        "maximum_soldiers": 500,
        "maa_type": {
            "status": "available",
            "key": "bowmen",
            "unavailable_reason": None,
        },
        "kind": {
            "status": "available",
            "value": "men_at_arms",
            "unavailable_reason": None,
        },
        "fights_in_main_phase": True,
        "effective_stats": {
            "status": "available",
            "source_target_province_id": 900,
            "max_size": 500,
            "siege_value_raw": 0,
            "damage_raw": 2_500_000,
            "toughness_raw": 1_000_000,
            "pursuit_raw": 500_000,
            "screen_raw": 300_000,
            "scale": 100_000,
            "unavailable_reason": None,
        },
        "counter": {
            "status": "absent",
            "class_index": None,
            "current_chunk_raw": None,
            "targets": [],
            "scale": 100_000,
            "unavailable_reason": None,
        },
        "unavailable_reason": None,
    }


def _combat_army(
    army_id: int,
    native_carmy_id: int,
    encounter_role: str,
    scope_role: str,
    war_ids: list[int],
    current_province_id: int,
    owner_id: int,
    regiment_id: int,
) -> dict[str, object]:
    return {
        "status": "available",
        "army_id": army_id,
        "encounter_role": encounter_role,
        "native_carmy_id": native_carmy_id,
        "scope_role": scope_role,
        "war_ids": war_ids,
        "current_province_id": current_province_id,
        "owner": {
            "status": "available",
            "character_id": owner_id,
            "counter_efficiency_raw": 0,
            "counter_resistance_raw": 0,
            "scale": 100_000,
            "unavailable_reason": None,
        },
        "commander": {
            "status": "absent",
            "character_id": None,
            "generic_advantage_points": None,
            "battle_context": {
                "status": "available",
                "source_target_province_id": 900,
                "effective_min_roll": 0,
                "effective_max_roll": 0,
                "unavailable_reason": None,
            },
            "unavailable_reason": None,
        },
        "regiments": [_combat_regiment(regiment_id)],
        "knights": {
            "status": "available",
            "members": [],
            "unavailable_reason": None,
        },
        "unavailable_reason": None,
    }


def _combat_inputs() -> dict[str, object]:
    return {
        "target_province_id": 900,
        "participant_policy": (
            "explicit_hypothetical_fixed_at_contact_no_reinforcements"
        ),
        "scenario": {
            "kind": "explicit_hypothetical_contact",
            "attacker_entry_province_id": 800,
            "attacker_army_ids": [12],
            "defender_army_ids": [22],
            "attacker_side": "player_or_allied",
            "defender_side": "enemy",
            "attacker_position_policy": "fixed_at_entry_hypothetical",
            "defender_position_policy": "fixed_at_target_hypothetical",
            "defender_insertion_order_policy": (
                "explicit_request_order_hypothetical"
            ),
            "actual_route_dependency": False,
        },
        "armies": [
            _combat_army(
                12, 1_012, "attacker", "active_war_ally",
                [101, 102], 800, 7, 31,
            ),
            _combat_army(
                22, 1_022, "defender", "active_war_enemy",
                [101, 102], 900, 8, 32,
            ),
        ],
        "target_province": {
            "status": "available",
            "province_id": 900,
            "terrain": {
                "status": "available",
                "key": "hills",
                "combat_width_multiplier_raw": 80_000,
                "scale": 100_000,
                "unavailable_reason": None,
            },
            "crossing": {
                "status": "available",
                "kind": "river",
                "unavailable_reason": None,
            },
            "defender_context": {
                "status": "available",
                "defender_side": "enemy",
                "holding_defender_status": "available",
                "holding_defender": True,
                "holding_unavailable_reason": None,
                "unavailable_reason": None,
            },
            "precontact_width": {
                "status": "available",
                "base": 400,
                "final": 320,
                "unavailable_reason": None,
            },
            "unavailable_reason": None,
        },
        "ongoing_combats": [],
        "counter_resolutions": [
            {
                "status": "available",
                "countered_side": "player_or_allied",
                "countering_side": "enemy",
                "countered_modifier_owner_character_id": 7,
                "countering_modifier_owner_character_id": 8,
                "context_scale_raw": 100_000,
                "class_count": 2,
                "damage_retention_by_class_raw": [100_000, 100_000],
                "scale": 100_000,
                "unavailable_reason": None,
            },
            {
                "status": "available",
                "countered_side": "enemy",
                "countering_side": "player_or_allied",
                "countered_modifier_owner_character_id": 8,
                "countering_modifier_owner_character_id": 7,
                "context_scale_raw": 100_000,
                "class_count": 2,
                "damage_retention_by_class_raw": [100_000, 100_000],
                "scale": 100_000,
                "unavailable_reason": None,
            },
        ],
        "completeness": {
            "observation_slice": "precontact-composition-context-v2",
            "input_observation_ready": True,
            "monte_carlo_ready": False,
            "missing_required_domains": [
                "damage_to_casualty_allocation",
                "pursuit_transition",
                "battle_end_and_retreat_transition",
                "phase_event_rng_and_effects",
            ],
        },
    }


class CombatSimulationInputsContractTests(unittest.TestCase):
    def test_frozen_capability_and_hypothetical_contact_step(self) -> None:
        self.assertEqual(
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
            "game.command.query-combat-simulation-inputs-v2-N",
        )
        step = query_combat_simulation_inputs_step(900, 800, [12], [22])
        self.assertEqual(
            step,
            "query-combat-simulation-inputs-v2-900-800-a-1-12-d-1-22",
        )
        self.assertEqual(
            parse_query_combat_simulation_inputs_step(step),
            (900, 800, [12], [22]),
        )
        self.assertTrue(is_native_combat_query_step(step))

    def test_parser_rejects_old_noncanonical_or_ambiguous_tokens(self) -> None:
        invalid = (
            None,
            "query-combat-simulation-inputs-v1-900-12-22",
            "query-combat-simulation-inputs-v2-900-800-a-1-12-d-0",
            "query-combat-simulation-inputs-v2-900-800-a-2-12-d-1-22",
            "query-combat-simulation-inputs-v2-900-800-a-1-12-x-1-22",
            "query-combat-simulation-inputs-v2-0900-800-a-1-12-d-1-22",
            "query-combat-simulation-inputs-v2-900-800-a-1-012-d-1-22",
            "query-combat-simulation-inputs-v2-900-800-a-1-12-d-1-12",
            "query-combat-simulation-inputs-v2-900-900-a-1-12-d-1-22",
            "query-combat-simulation-inputs-v2-９００-800-a-1-12-d-1-22",
            "game.command.query-combat-simulation-inputs-v2-N",
        )
        for step in invalid:
            with self.subTest(step=step):
                self.assertIsNone(
                    parse_query_combat_simulation_inputs_step(step)
                )
                self.assertFalse(is_native_combat_query_step(step))

    def test_request_is_bounded_partitioned_and_never_deduplicated(self) -> None:
        self.assertEqual(
            normalize_combat_simulation_request(900, 800, [22], [12]),
            (900, 800, [22], [12]),
        )
        invalid = (
            (0, 800, [12], [22]),
            (900, 900, [12], [22]),
            (900, True, [12], [22]),
            (900, 800, None, [22]),
            (900, 800, [], [22]),
            (900, 800, [12], []),
            (900, 800, [12], [12]),
            (900, 800, [True], [22]),
            (900, 800, [2**31], [22]),
            (
                900,
                800,
                list(range(1, MAX_COMBAT_SIMULATION_REQUEST_ARMY_IDS + 1)),
                [100],
            ),
        )
        for target, entry, attackers, defenders in invalid:
            with self.subTest(target=target, attackers=attackers):
                with self.assertRaises(ValueError):
                    normalize_combat_simulation_request(
                        target, entry, attackers, defenders
                    )

    def test_scope_requires_opposite_partitions_in_one_shared_war(self) -> None:
        scope = combat_simulation_encounter_scope(_snapshot(), [12], [22])
        self.assertEqual(scope["army_ids"], [12, 22])
        self.assertEqual(scope["common_war_ids"], [101, 102])
        self.assertEqual(scope["attacker_side"], "player_or_allied")
        self.assertEqual(scope["defender_side"], "enemy")

        invalid = (
            ([11], [12]),
            ([21], [22]),
            ([11], [23]),
            ([11], [99]),
        )
        for attackers, defenders in invalid:
            with self.subTest(attackers=attackers, defenders=defenders):
                with self.assertRaises(ValueError):
                    combat_simulation_encounter_scope(
                        _snapshot(), attackers, defenders
                    )

    def test_live_shaped_three_army_scenario_needs_no_move_order(self) -> None:
        player_id = 83_886_341
        enemy_ids = [357, 33_554_657]
        snapshot = {
            "player_armies": [_army(player_id)],
            "active_wars": [
                {
                    "war_id": 16_777_290,
                    "allied_armies": [_army(player_id)],
                    "enemy_armies": [_army(value) for value in enemy_ids],
                }
            ],
        }
        scope = combat_simulation_encounter_scope(
            snapshot, enemy_ids, [player_id]
        )
        self.assertEqual(scope["attacker_side"], "enemy")
        self.assertEqual(scope["defender_side"], "player_or_allied")
        self.assertEqual(
            query_combat_simulation_inputs_step(
                2596, 2597, enemy_ids, [player_id]
            ),
            "query-combat-simulation-inputs-v2-2596-2597-a-2-357-"
            "33554657-d-1-83886341",
        )

    def test_mixed_owner_coalition_uses_first_request_order_owner(self) -> None:
        value = _combat_inputs()
        value["scenario"].update(
            {
                "attacker_army_ids": [21, 22],
                "defender_army_ids": [12],
                "attacker_side": "enemy",
                "defender_side": "player_or_allied",
            }
        )
        value["armies"] = [
            _combat_army(
                21, 1_021, "attacker", "active_war_enemy",
                [101], 700, 8, 32,
            ),
            _combat_army(
                22, 1_022, "attacker", "active_war_enemy",
                [101, 102], 701, 9, 33,
            ),
            _combat_army(
                12, 1_012, "defender", "active_war_ally",
                [101, 102], 900, 7, 31,
            ),
        ]
        defender = value["target_province"]["defender_context"]
        defender["defender_side"] = "player_or_allied"
        first, second = value["counter_resolutions"]
        first.update(
            {
                "countered_modifier_owner_character_id": 7,
                "countering_modifier_owner_character_id": 8,
            }
        )
        second.update(
            {
                "countered_modifier_owner_character_id": 8,
                "countering_modifier_owner_character_id": 7,
            }
        )
        scope = combat_simulation_encounter_scope(
            _snapshot(), [21, 22], [12]
        )
        normalized = normalize_combat_simulation_inputs(
            value,
            expected_target_province_id=900,
            expected_attacker_entry_province_id=800,
            expected_encounter_scope=scope,
        )
        self.assertEqual(combat_simulation_inputs_status(normalized), "available")

        wrong_owner = copy.deepcopy(value)
        wrong_owner["counter_resolutions"][0][
            "countering_modifier_owner_character_id"
        ] = 9
        with self.assertRaisesRegex(ValueError, "first request-order owner"):
            normalize_combat_simulation_inputs(
                wrong_owner,
                expected_target_province_id=900,
                expected_attacker_entry_province_id=800,
                expected_encounter_scope=scope,
            )

    def test_parameterized_or_literal_capability_never_leaks_action(self) -> None:
        self.assertEqual(
            _action_steps(
                [QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY], paused=True
            ),
            [],
        )

    def _normalize(self, value: dict[str, object]) -> dict[str, object]:
        scope = combat_simulation_encounter_scope(_snapshot(), [12], [22])
        return normalize_combat_simulation_inputs(
            value,
            expected_target_province_id=900,
            expected_attacker_entry_province_id=800,
            expected_encounter_scope=scope,
        )

    def test_exact_serializer_schema_normalizes_available_observation(self) -> None:
        normalized = self._normalize(_combat_inputs())
        self.assertEqual(
            combat_simulation_inputs_status(normalized), "available"
        )
        self.assertTrue(
            normalized["completeness"]["input_observation_ready"]
        )
        self.assertFalse(normalized["completeness"]["monte_carlo_ready"])

    def test_unavailable_holding_does_not_erase_observed_armies(self) -> None:
        value = _combat_inputs()
        defender = value["target_province"]["defender_context"]
        defender.update(
            {
                "holding_defender_status": "unavailable",
                "holding_defender": None,
                "holding_unavailable_reason": "holding_owner_unavailable",
            }
        )
        resolution = value["counter_resolutions"][0]
        resolution.update(
            {
                "status": "unavailable",
                "countered_modifier_owner_character_id": None,
                "countering_modifier_owner_character_id": None,
                "context_scale_raw": None,
                "damage_retention_by_class_raw": None,
                "unavailable_reason": "counter_context_scale_unavailable",
            }
        )
        value["completeness"].update(
            {
                "input_observation_ready": False,
                "missing_required_domains": [
                    "attacker_defender_holding",
                    "counter_resolutions",
                    "damage_to_casualty_allocation",
                    "pursuit_transition",
                    "battle_end_and_retreat_transition",
                    "phase_event_rng_and_effects",
                ],
            }
        )
        normalized = self._normalize(value)
        self.assertEqual(combat_simulation_inputs_status(normalized), "partial")
        self.assertEqual(
            normalized["target_province"]["defender_context"][
                "defender_side"
            ],
            "enemy",
        )
        self.assertIsNotNone(normalized["armies"][1]["regiments"])

    def test_schema_scale_status_and_scenario_binding_are_strict(self) -> None:
        mutations = []
        fake_key = _combat_inputs()
        fake_key["win_probability"] = 0.75
        mutations.append(fake_key)
        wrong_scale = _combat_inputs()
        wrong_scale["armies"][0]["owner"]["scale"] = 1
        mutations.append(wrong_scale)
        wrong_partition = _combat_inputs()
        wrong_partition["scenario"]["attacker_army_ids"] = [22]
        mutations.append(wrong_partition)
        route_dependent = _combat_inputs()
        route_dependent["scenario"]["actual_route_dependency"] = True
        mutations.append(route_dependent)
        fake_ready = _combat_inputs()
        fake_ready["completeness"]["monte_carlo_ready"] = True
        mutations.append(fake_ready)
        for value in mutations:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self._normalize(value)
        self.assertEqual(
            _action_steps(
                [
                    "game.command.query-combat-simulation-inputs-v2-"
                    "900-800-a-1-12-d-1-22"
                ],
                paused=True,
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
