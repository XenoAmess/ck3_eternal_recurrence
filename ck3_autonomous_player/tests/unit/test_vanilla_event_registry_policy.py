from __future__ import annotations

import copy
import unittest

from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)


PLAYER = 27_181
EVENT_KEY = "tgp_travel_events.0030"


def _scope(type_key: str, *, character_id: int | None = None) -> dict[str, object]:
    if character_id is not None:
        identity: dict[str, object] = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
        raw_type_index = 4
    else:
        identity = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
        raw_type_index = 3
    return {
        "status": "available",
        "raw_type_index": raw_type_index,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": identity,
    }


def _option(rendered: int, native: int) -> dict[str, object]:
    return {
        "rendered_index": rendered,
        "native_option_index": native,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
    }


def _context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": [
            {
                "name": "travel_plan",
                "name_identifier": 1,
                "scope": _scope("travel_plan"),
            },
            {
                "name": "poem_province",
                "name_identifier": 2,
                "scope": _scope("province"),
            },
        ],
        "options": [_option(0, 0), _option(1, 1)],
    }


def _recommend(context: dict[str, object]) -> dict[str, object]:
    return recommend_registered_vanilla_event_option_v1(
        context,
        played_character_id=PLAYER,
        snapshot_option_count=2,
    )


def _natural_disaster_context(native_indices: tuple[int, ...]) -> dict[str, object]:
    scope_types = {
        "situation": "situation",
        "situation_sub_region": "situation_sub_region",
        "epicenter_county": "landed_title",
        "river_region": "geographical_region",
    }
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "natural_disaster.7031",
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": [
            {
                "name": name,
                "name_identifier": index + 10,
                "scope": _scope(type_key),
            }
            for index, (name, type_key) in enumerate(scope_types.items())
        ],
        "options": [
            _option(rendered, native)
            for rendered, native in enumerate(native_indices)
        ],
    }


def _trait_gold_context() -> dict[str, object]:
    context = _context()
    context["event_definition_key"] = "trait_specific.8001"
    context["saved_scopes"] = []
    return context


def _heir_death_context(*, dead_character_id: int = 39_246) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "death_management.1007",
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": [
            {
                "name": "new_memory",
                "name_identifier": 20,
                "scope": _scope("character_memory"),
            },
            {
                "name": "dead_character",
                "name_identifier": 21,
                "scope": _scope("character", character_id=dead_character_id),
            },
            {
                "name": "deceased_character_stress",
                "name_identifier": 22,
                "scope": _scope("value"),
            },
        ],
        "options": [_option(0, 0)],
    }


class VanillaEventRegistryPolicyTests(unittest.TestCase):
    def test_exact_tgp_travel_projection_selects_authored_option_two(
        self,
    ) -> None:
        result = _recommend(_context())

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 2)
        self.assertEqual(result["selected_native_option_index"], 1)
        self.assertEqual(result["selected_rendered_index"], 1)
        self.assertEqual(result["failed_checks"], [])
        self.assertFalse(result["semantic_optimal"])
        self.assertEqual(result["option_projection_source"], "base_contract")
        profile = result["choice_effect_profile"]
        self.assertEqual(profile["schema"], "xar.ck3.vanilla-event-choice-effect")
        stress_effect = profile["selected_option_effects"][0]
        self.assertEqual(stress_effect["authored_base_points"], -30)
        self.assertFalse(stress_effect["runtime_delta_exact"])
        self.assertEqual(
            profile["observable_postcondition"]["expected_relation"],
            "non_increasing",
        )
        utility = result["campaign_utility_profile"]
        self.assertTrue(result["campaign_utility_ready"])
        self.assertEqual(
            utility["objective_id"], "reduce_stress_without_delaying_travel"
        )
        self.assertEqual(utility["selected_rank"], 1)
        self.assertEqual(utility["alternatives"][0]["native_option_index"], 0)
        self.assertIsNone(utility["cross_event_numeric_score"])

    def test_exact_natural_disaster_option_variants_select_native_two(
        self,
    ) -> None:
        for native_indices, expected_variant in (
            ((2,), 0),
            ((0, 2), 1),
            ((0, 1, 2), 2),
        ):
            with self.subTest(native_indices=native_indices):
                result = recommend_registered_vanilla_event_option_v1(
                    _natural_disaster_context(native_indices),
                    played_character_id=PLAYER,
                    snapshot_option_count=3,
                )

                self.assertEqual(result["status"], "recommended")
                self.assertEqual(result["selected_option_number"], 3)
                self.assertEqual(result["selected_native_option_index"], 2)
                self.assertEqual(
                    result["matched_option_variant_index"], expected_variant
                )
                self.assertEqual(
                    result["option_projection_source"],
                    "registered_option_variant",
                )
                profile = result["choice_effect_profile"]
                self.assertFalse(
                    profile["selected_option_effects"][0][
                        "material_state_change"
                    ]
                )
                self.assertEqual(
                    profile["common_after_effects"][0]["variable_key"],
                    "natural_disaster_received_first_warning",
                )
                self.assertIsNone(profile["observable_postcondition"])

    def test_trait_gold_projection_selects_deterministic_gain(self) -> None:
        result = _recommend(_trait_gold_context())

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 2)
        self.assertEqual(result["selected_native_option_index"], 1)
        profile = result["choice_effect_profile"]
        effect = profile["selected_option_effects"][0]
        self.assertEqual(effect["authored_value_key"], "minor_gold_value")
        self.assertEqual(effect["authored_minimum_whole"], 15)
        self.assertFalse(effect["runtime_delta_exact"])
        self.assertEqual(
            profile["observable_postcondition"]["expected_relation"],
            "strictly_increasing",
        )
        utility = result["campaign_utility_profile"]
        self.assertEqual(
            utility["objective_id"],
            "increase_liquid_reserve_without_random_persistence",
        )
        self.assertEqual(utility["selected_rank"], 1)
        self.assertEqual(utility["alternatives"][0]["rank"], 2)
        self.assertIsNone(utility["cross_event_numeric_score"])

    def test_heir_death_projection_requires_a_distinct_dead_character(
        self,
    ) -> None:
        recommended = recommend_registered_vanilla_event_option_v1(
            _heir_death_context(),
            played_character_id=PLAYER,
            snapshot_option_count=1,
        )
        drifted = recommend_registered_vanilla_event_option_v1(
            _heir_death_context(dead_character_id=PLAYER),
            played_character_id=PLAYER,
            snapshot_option_count=1,
        )

        self.assertEqual(recommended["status"], "recommended")
        self.assertEqual(recommended["selected_option_number"], 1)
        self.assertEqual(recommended["selected_native_option_index"], 0)
        profile = recommended["choice_effect_profile"]
        self.assertEqual(
            profile["selected_option_effects"][0]["authored_base_points"], 20
        )
        self.assertEqual(
            profile["observable_postcondition"]["expected_relation"],
            "non_decreasing",
        )
        utility = recommended["campaign_utility_profile"]
        self.assertEqual(
            utility["objective_id"],
            "acknowledge_unavoidable_heir_death_event",
        )
        self.assertEqual(utility["comparison_kind"], "sole_legal_route")
        self.assertEqual(utility["alternatives"], [])
        self.assertIsNone(utility["cross_event_numeric_score"])
        self.assertEqual(drifted["status"], "blocked")
        self.assertIn(
            "scope:dead_character:unique_character_excludes",
            drifted["failed_checks"],
        )

    def test_natural_disaster_unregistered_projection_stays_blocked(self) -> None:
        result = recommend_registered_vanilla_event_option_v1(
            _natural_disaster_context((0, 1)),
            played_character_id=PLAYER,
            snapshot_option_count=3,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["unavailable_reason"],
            "registered_option_variant_projection_drift",
        )
        self.assertEqual(result["failed_checks"], ["option_variant_projection"])

    def test_other_variant_contracts_still_require_explicit_consumer_review(
        self,
    ) -> None:
        context = _context()
        context["event_definition_key"] = "epidemic_events.1100"

        result = recommend_registered_vanilla_event_option_v1(
            context,
            played_character_id=PLAYER,
            snapshot_option_count=2,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["unavailable_reason"],
            "registered_contract_requires_extended_consumer",
        )
        self.assertEqual(
            result["failed_checks"],
            ["direct_projection_support:option_variants"],
        )

    def test_unknown_event_leaves_existing_planner_fallback_available(
        self,
    ) -> None:
        context = _context()
        context["event_definition_key"] = "unregistered_event.1"

        result = _recommend(context)

        self.assertEqual(result["status"], "not_registered")
        self.assertEqual(
            result["unavailable_reason"],
            "event_definition_key_not_registered",
        )

    def test_registered_scope_drift_blocks_without_selecting(self) -> None:
        context = _context()
        saved_scopes = context["saved_scopes"]
        assert isinstance(saved_scopes, list)
        saved_scopes[1]["name"] = "wrong_province"

        result = _recommend(context)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("saved_scope_names_exact", result["failed_checks"])
        self.assertIsNone(result["selected_native_option_index"])

    def test_registered_selected_option_must_be_enabled(self) -> None:
        context = _context()
        options = context["options"]
        assert isinstance(options, list)
        options[1]["enabled"] = False

        result = _recommend(context)

        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "selected_native_option_enabled", result["failed_checks"]
        )
        self.assertIsNone(result["selected_option_number"])

    def test_registered_native_projection_drift_blocks(self) -> None:
        context = _context()
        options = context["options"]
        assert isinstance(options, list)
        drifted = copy.deepcopy(options)
        drifted[0]["native_option_index"] = 1
        drifted[1]["native_option_index"] = 0
        context["options"] = drifted

        result = _recommend(context)

        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "native_option_indices_exact", result["failed_checks"]
        )


if __name__ == "__main__":
    unittest.main()
