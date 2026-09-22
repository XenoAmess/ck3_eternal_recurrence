from __future__ import annotations

import copy
import unittest

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn
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


def _epidemic_1100_context(native_indices: tuple[int, ...]) -> dict[str, object]:
    scope_types = {
        "epidemic": ("epidemic", 50),
        "province": ("province", 8),
        "infected_county": ("landed_title", 5),
    }
    saved_scopes = []
    for index, (name, (type_key, raw_type_index)) in enumerate(
        scope_types.items()
    ):
        scope = _scope(type_key)
        scope["raw_type_index"] = raw_type_index
        saved_scopes.append(
            {"name": name, "name_identifier": index + 10, "scope": scope}
        )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "epidemic_events.1100",
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": saved_scopes,
        "options": [
            _option(rendered, native)
            for rendered, native in enumerate(native_indices)
        ],
    }


def _epidemic_5007_context(
    native_indices: tuple[int, ...],
    *,
    played_character_id: int = 36_403,
    herbalist_character_id: int = 50_001,
    accuser_character_id: int = 50_002,
) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "epidemic_events.5007",
        "root_scope": _scope("character", character_id=played_character_id),
        "saved_scopes": [
            {
                "name": name,
                "name_identifier": index + 10,
                "scope": _scope(
                    "character", character_id=character_id
                ) if character_id is not None else _scope("epidemic"),
            }
            for index, (name, character_id) in enumerate(
                (
                    ("epidemic", None),
                    ("epidemic_scope", None),
                    ("herbalist", herbalist_character_id),
                    ("accuser", accuser_character_id),
                )
            )
        ],
        "options": [
            _option(rendered, native)
            for rendered, native in enumerate(native_indices)
        ],
    }


def _epidemic_1020_context(
    *,
    played_character_id: int = 36_403,
    courtier_character_id: int = 50_001,
) -> dict[str, object]:
    scope_types = (
        ("epidemic", "epidemic"),
        ("epidemic_province", "province"),
        ("epidemic_scope", "epidemic"),
        ("epidemic_county", "landed_title"),
        ("miasma_courtier", "character"),
    )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "epidemic_events.1020",
        "root_scope": _scope("character", character_id=played_character_id),
        "saved_scopes": [
            {
                "name": name,
                "name_identifier": index + 10,
                "scope": _scope(
                    type_key,
                    character_id=(
                        courtier_character_id
                        if name == "miasma_courtier" else None
                    ),
                ),
            }
            for index, (name, type_key) in enumerate(scope_types)
        ],
        "options": [_option(0, 0), _option(1, 1)],
    }


def _r0065_grief_context(
    native_indices: tuple[int, ...] = (0, 4, 7),
    *,
    deceased_character_id: int = 36_403,
) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "stress_threshold_special.1001",
        "calculated_event_id": 3_121_001,
        "runtime_stats_ordinal": 4_333,
        "current_event_instance_id": 9,
        "snapshot_revision": 19,
        "date_raw": 53_284_680,
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": [
            {
                "name": "stress_character",
                "name_identifier": 20_928,
                "scope": _scope("character", character_id=PLAYER),
            },
            {
                "name": "deceased_character",
                "name_identifier": 19_883,
                "scope": _scope(
                    "character", character_id=deceased_character_id
                ),
            },
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


def _hostile_scheme_context() -> dict[str, object]:
    scope_rows = (
        ("scheme", "scheme", None),
        ("owner", "character", 31_549),
        ("artifact", "artifact", None),
        ("target", "character", PLAYER),
        ("spymaster", "character", 34_867),
        ("discovery_chance", "value", None),
    )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "hostile_scheme_discovery.2001",
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": [
            {
                "name": name,
                "name_identifier": index + 1,
                "scope": _scope(type_key, character_id=character_id),
            }
            for index, (name, type_key, character_id) in enumerate(scope_rows)
        ],
        "options": [_option(0, 0)],
    }


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


def _chancellor_success_context(
    *,
    liege_id: int = PLAYER,
    chancellor_id: int = 32_716,
    chancellor_alias_id: int = 32_716,
    active_chancellor_id: int = 32_716,
    neighbor_id: int = 33_422,
) -> dict[str, object]:
    character_scopes = (
        ("councillor", chancellor_id),
        ("councillor_liege", liege_id),
        ("chancellor", chancellor_alias_id),
        ("active_councillor", active_chancellor_id),
        ("neighbor", neighbor_id),
    )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "chancellor_task.1104",
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": [
            {
                "name": name,
                "name_identifier": index + 30,
                "scope": _scope("character", character_id=character_id),
            }
            for index, (name, character_id) in enumerate(character_scopes)
        ],
        "options": [_option(0, 0)],
    }


def _prison_release_context(
    *,
    player_id: int = 29_829,
    imprisoner_id: int = 32_309,
    prisoner_id: int = 34_730,
    background_id: int = 32_309,
) -> dict[str, object]:
    character_scopes = (
        ("imprisoner", imprisoner_id),
        ("prisoner", prisoner_id),
        ("bg_override_char", background_id),
        ("this_player", player_id),
    )
    saved_scopes = [
        {
            "name": "new_memory",
            "name_identifier": 205,
            "scope": _scope("character_memory"),
        }
    ]
    saved_scopes.extend(
        {
            "name": name,
            "name_identifier": index,
            "scope": _scope("character", character_id=character_id),
        }
        for index, (name, character_id) in enumerate(character_scopes, start=206)
    )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "prison_notification.2002",
        "root_scope": _scope("character", character_id=player_id),
        "saved_scopes": saved_scopes,
        "options": [_option(0, 0)],
    }


def _r0072_infirm_context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "health.7000",
        "root_scope": _scope("character", character_id=31_853),
        "saved_scopes": [],
        "options": [_option(0, 0)],
    }


def _withering_mind_context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "health.7200",
        "root_scope": _scope("character", character_id=29_829),
        "saved_scopes": [],
        "options": [_option(0, 0)],
    }


def _fragile_bones_context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "health.7500",
        "root_scope": _scope("character", character_id=29_829),
        "saved_scopes": [],
        "options": [_option(0, 0)],
    }


def _health_3104_punishment_context() -> dict[str, object]:
    scope_rows = (
        ("epidemic", "epidemic", None),
        ("disease_type", "flag", None),
        ("sick_character", "character", 29_829),
        ("new_memory", "character_memory", None),
        ("high_skill_option", "character", 41_567),
        ("low_skill_option", "character", 65_487),
        ("physician", "character", 41_567),
        ("background_terrain_scope", "province", None),
        ("treatment_picker", "character", 29_829),
        ("treatment", "flag", None),
        ("outcome", "flag", None),
        ("portrait", "character", 41_567),
    )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "health.3104",
        "root_scope": _scope("character", character_id=29_829),
        "saved_scopes": [
            {
                "name": name,
                "name_identifier": index + 260,
                "scope": _scope(type_key, character_id=character_id),
            }
            for index, (name, type_key, character_id) in enumerate(scope_rows)
        ],
        "options": [_option(0, 0), _option(1, 1), _option(2, 2)],
    }


class VanillaEventRegistryPolicyTests(unittest.TestCase):
    def test_health_3104_r19_three_option_variant_spares_physician(
        self,
    ) -> None:
        result = recommend_registered_vanilla_event_option_v1(
            _health_3104_punishment_context(),
            played_character_id=29_829,
            snapshot_option_count=3,
        )

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 1)
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertEqual(result["matched_option_variant_index"], 0)
        self.assertEqual(result["failed_checks"], [])

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

    def test_chancellor_success_requires_exact_role_relationships(self) -> None:
        recommended = recommend_registered_vanilla_event_option_v1(
            _chancellor_success_context(),
            played_character_id=PLAYER,
            snapshot_option_count=1,
        )

        self.assertEqual(recommended["status"], "recommended")
        self.assertEqual(recommended["selected_option_number"], 1)
        self.assertEqual(recommended["selected_native_option_index"], 0)
        self.assertEqual(recommended["failed_checks"], [])

        drift_cases = (
            (
                {"liege_id": 40_001},
                "scope:councillor_liege:character_id",
            ),
            (
                {"chancellor_alias_id": 40_002},
                "scope:chancellor:matches_any",
            ),
            (
                {"active_chancellor_id": 40_003},
                "scope:active_councillor:matches_any",
            ),
            (
                {"neighbor_id": 32_716},
                "scope:neighbor:differs_from",
            ),
        )
        for changes, failed_check in drift_cases:
            with self.subTest(failed_check=failed_check):
                result = recommend_registered_vanilla_event_option_v1(
                    _chancellor_success_context(**changes),
                    played_character_id=PLAYER,
                    snapshot_option_count=1,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

    def test_prison_release_acknowledgement_requires_r840_role_shape(self) -> None:
        recommended = recommend_registered_vanilla_event_option_v1(
            _prison_release_context(),
            played_character_id=29_829,
            snapshot_option_count=1,
        )

        self.assertEqual(recommended["status"], "recommended")
        self.assertEqual(recommended["selected_option_number"], 1)
        self.assertEqual(recommended["selected_native_option_index"], 0)
        self.assertEqual(recommended["selected_rendered_index"], 0)
        self.assertEqual(recommended["failed_checks"], [])
        for restored_check in (
            "disabled_option_contract",
            "native_option_indices_exact",
            "saved_scope_names_exact",
            "scope_types_cover_projection",
        ):
            with self.subTest(restored_check=restored_check):
                self.assertTrue(recommended["checks"][restored_check])
        self.assertFalse(recommended["semantic_optimal"])
        self.assertFalse(recommended["campaign_utility_ready"])
        self.assertIsNone(recommended["choice_effect_profile"])

        drift_cases = (
            (
                {"player_id": 40_001},
                29_829,
                "root_character_id",
            ),
            (
                {"imprisoner_id": 29_829},
                29_829,
                "scope:imprisoner:unique_character_excludes",
            ),
            (
                {"prisoner_id": 32_309},
                29_829,
                "scope:prisoner:differs_from",
            ),
            (
                {"background_id": 40_002},
                29_829,
                "scope:bg_override_char:matches_any",
            ),
        )
        for changes, played_character_id, failed_check in drift_cases:
            with self.subTest(failed_check=failed_check):
                result = recommend_registered_vanilla_event_option_v1(
                    _prison_release_context(**changes),
                    played_character_id=played_character_id,
                    snapshot_option_count=1,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

        missing_memory = _prison_release_context()
        missing_memory["saved_scopes"] = [
            row
            for row in missing_memory["saved_scopes"]
            if row["name"] != "new_memory"
        ]
        result = recommend_registered_vanilla_event_option_v1(
            missing_memory,
            played_character_id=29_829,
            snapshot_option_count=1,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("saved_scope_names_exact", result["failed_checks"])

    def test_r0072_infirm_onset_exact_projection_only(self) -> None:
        context = _r0072_infirm_context()
        recommended = recommend_registered_vanilla_event_option_v1(
            context,
            played_character_id=31_853,
            snapshot_option_count=1,
        )
        self.assertEqual(recommended["status"], "recommended")
        self.assertEqual(recommended["selected_option_number"], 1)
        self.assertEqual(recommended["selected_native_option_index"], 0)
        self.assertEqual(recommended["selected_rendered_index"], 0)
        self.assertEqual(recommended["failed_checks"], [])
        for restored_check in (
            "saved_scope_names_exact",
            "scope_types_cover_projection",
            "native_option_indices_exact",
            "disabled_option_contract",
        ):
            self.assertTrue(recommended["checks"][restored_check])

        for label, changes, failed_check in (
            (
                "unexpected saved scope",
                {
                    "saved_scopes": [
                        {
                            "name": "unexpected",
                            "name_identifier": 1,
                            "scope": _scope("character", character_id=30_001),
                        }
                    ]
                },
                "saved_scope_names_exact",
            ),
            ("native remap", {"options": [_option(0, 1)]}, "native_option_indices_exact"),
            (
                "disabled sole option",
                {"options": [{**_option(0, 0), "enabled": False}]},
                "selected_native_option_enabled",
            ),
        ):
            with self.subTest(label=label):
                drifted = _r0072_infirm_context()
                drifted.update(changes)
                result = recommend_registered_vanilla_event_option_v1(
                    drifted,
                    played_character_id=31_853,
                    snapshot_option_count=1,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

    def test_withering_mind_acknowledgement_requires_r842_exact_projection(
        self,
    ) -> None:
        recommended = recommend_registered_vanilla_event_option_v1(
            _withering_mind_context(),
            played_character_id=29_829,
            snapshot_option_count=1,
        )

        self.assertEqual(recommended["status"], "recommended")
        self.assertEqual(recommended["selected_option_number"], 1)
        self.assertEqual(recommended["selected_native_option_index"], 0)
        self.assertEqual(recommended["selected_rendered_index"], 0)
        self.assertEqual(recommended["failed_checks"], [])
        self.assertFalse(recommended["semantic_optimal"])
        self.assertFalse(recommended["campaign_utility_ready"])
        self.assertIsNone(recommended["choice_effect_profile"])

        drift_cases: tuple[tuple[str, dict[str, object], str], ...] = (
            (
                "unexpected saved scope",
                {
                    "saved_scopes": [
                        {
                            "name": "unexpected",
                            "name_identifier": 1,
                            "scope": _scope("character", character_id=30_001),
                        }
                    ]
                },
                "saved_scope_names_exact",
            ),
            (
                "native option remap",
                {"options": [_option(0, 1)]},
                "native_option_indices_exact",
            ),
            (
                "disabled sole option",
                {
                    "options": [
                        {
                            **_option(0, 0),
                            "enabled": False,
                        }
                    ]
                },
                "selected_native_option_enabled",
            ),
        )
        for label, changes, failed_check in drift_cases:
            with self.subTest(label=label):
                context = _withering_mind_context()
                context.update(changes)
                result = recommend_registered_vanilla_event_option_v1(
                    context,
                    played_character_id=29_829,
                    snapshot_option_count=1,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

    def test_fragile_bones_acknowledgement_requires_r844_exact_projection(
        self,
    ) -> None:
        recommended = recommend_registered_vanilla_event_option_v1(
            _fragile_bones_context(),
            played_character_id=29_829,
            snapshot_option_count=1,
        )

        self.assertEqual(recommended["status"], "recommended")
        self.assertEqual(recommended["selected_option_number"], 1)
        self.assertEqual(recommended["selected_native_option_index"], 0)
        self.assertEqual(recommended["selected_rendered_index"], 0)
        self.assertEqual(recommended["failed_checks"], [])
        for restored_check in (
            "disabled_option_contract",
            "native_option_indices_exact",
            "saved_scope_names_exact",
            "scope_types_cover_projection",
        ):
            with self.subTest(restored_check=restored_check):
                self.assertTrue(recommended["checks"][restored_check])
        self.assertFalse(recommended["semantic_optimal"])
        self.assertFalse(recommended["campaign_utility_ready"])
        self.assertIsNone(recommended["choice_effect_profile"])

        drift_cases: tuple[tuple[str, dict[str, object], str], ...] = (
            (
                "unexpected saved scope",
                {
                    "saved_scopes": [
                        {
                            "name": "unexpected",
                            "name_identifier": 1,
                            "scope": _scope("character", character_id=30_001),
                        }
                    ]
                },
                "saved_scope_names_exact",
            ),
            (
                "native option remap",
                {"options": [_option(0, 1)]},
                "native_option_indices_exact",
            ),
            (
                "disabled sole option",
                {
                    "options": [
                        {
                            **_option(0, 0),
                            "enabled": False,
                        }
                    ]
                },
                "selected_native_option_enabled",
            ),
        )
        for label, changes, failed_check in drift_cases:
            with self.subTest(label=label):
                context = _fragile_bones_context()
                context.update(changes)
                result = recommend_registered_vanilla_event_option_v1(
                    context,
                    played_character_id=29_829,
                    snapshot_option_count=1,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

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

    def test_r0065_grief_exact_variant_selects_native_seven_only(self) -> None:
        result = recommend_registered_vanilla_event_option_v1(
            _r0065_grief_context(),
            played_character_id=PLAYER,
            snapshot_option_count=9,
        )

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_native_option_index"], 7)
        self.assertEqual(result["selected_option_number"], 8)
        self.assertEqual(result["selected_rendered_index"], 2)
        self.assertEqual(result["matched_option_variant_index"], 3)
        self.assertEqual(result["failed_checks"], [])
        self.assertFalse(result["semantic_optimal"])
        profile = result["choice_effect_profile"]
        self.assertEqual(profile["selected_native_option_index"], 7)
        self.assertEqual(
            profile["selected_option_effects"][0]["modifier"],
            "stress_frozen_grief",
        )

    def test_r0065_grief_drift_and_older_variants_remain_blocked(self) -> None:
        cases = (
            ("older_shape", _r0065_grief_context((1, 4, 7))),
            ("old_confider_shape", _r0065_grief_context((1, 6, 7))),
            ("old_depression_shape", _r0065_grief_context((0, 1, 7))),
            ("unknown_shape", _r0065_grief_context((0, 4, 8))),
            ("same_deceased", _r0065_grief_context(deceased_character_id=PLAYER)),
            ("missing_frame", {**_r0065_grief_context(), "date_raw": None}),
            ("wrong_identity", {**_r0065_grief_context(), "runtime_stats_ordinal": 1}),
        )
        for label, context in cases:
            with self.subTest(label=label):
                result = recommend_registered_vanilla_event_option_v1(
                    context,
                    played_character_id=PLAYER,
                    snapshot_option_count=9,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_native_option_index"])

        for mutation in ("hidden", "disabled", "extra_scope", "stress_role"):
            with self.subTest(mutation=mutation):
                context = _r0065_grief_context()
                if mutation == "hidden":
                    context["options"][2]["shown"] = False
                elif mutation == "disabled":
                    context["options"][2]["enabled"] = False
                else:
                    if mutation == "extra_scope":
                        context["saved_scopes"].append({
                            "name": "confidant",
                            "name_identifier": 3,
                            "scope": _scope("character", character_id=91_001),
                        })
                    else:
                        context["saved_scopes"][0]["scope"] = _scope(
                            "character", character_id=91_001
                        )
                result = recommend_registered_vanilla_event_option_v1(
                    context,
                    played_character_id=PLAYER,
                    snapshot_option_count=9,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_native_option_index"])

    def test_epidemic_1100_exact_physician_variants_choose_bounded_option(
        self,
    ) -> None:
        for native_indices, variant_index in (((0, 1), 0), ((0, 2), 1)):
            with self.subTest(native_indices=native_indices):
                result = recommend_registered_vanilla_event_option_v1(
                    _epidemic_1100_context(native_indices),
                    played_character_id=PLAYER,
                    snapshot_option_count=3,
                )
                self.assertEqual(result["status"], "recommended")
                self.assertEqual(result["selected_option_number"], 1)
                self.assertEqual(result["selected_native_option_index"], 0)
                self.assertEqual(result["matched_option_variant_index"], variant_index)
                self.assertEqual(result["failed_checks"], [])

    def test_epidemic_1100_other_or_malformed_variants_stay_blocked(self) -> None:
        variants = (
            (0, 1, 2),
            (0,),
            (1, 2),
        )
        for native_indices in variants:
            with self.subTest(native_indices=native_indices):
                result = recommend_registered_vanilla_event_option_v1(
                    _epidemic_1100_context(native_indices),
                    played_character_id=PLAYER,
                    snapshot_option_count=3,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_option_number"])

        wrong_scope = _epidemic_1100_context((0, 1))
        wrong_scope["saved_scopes"][2]["scope"]["type_key"] = "province"
        result = recommend_registered_vanilla_event_option_v1(
            wrong_scope, played_character_id=PLAYER, snapshot_option_count=3
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("scope:infected_county:type", result["failed_checks"])

    def test_r0092_epidemic_5007_natural_two_button_projection_selects_native_two(
        self,
    ) -> None:
        for native_indices, variant_index in (((1, 2), 0), ((0, 1, 2), 1)):
            with self.subTest(native_indices=native_indices):
                result = recommend_registered_vanilla_event_option_v1(
                    _epidemic_5007_context(native_indices),
                    played_character_id=36_403,
                    snapshot_option_count=3,
                )
                self.assertEqual(result["status"], "recommended")
                self.assertEqual(result["selected_option_number"], 3)
                self.assertEqual(result["selected_native_option_index"], 2)
                self.assertEqual(
                    result["matched_option_variant_index"], variant_index
                )
                self.assertEqual(result["failed_checks"], [])

    def test_r0092_epidemic_5007_relational_or_option_drift_blocks(
        self,
    ) -> None:
        cases = (
            (_epidemic_5007_context((1, 2), herbalist_character_id=36_403),
             "scope:herbalist:unique_character_excludes"),
            (_epidemic_5007_context((1, 2), accuser_character_id=50_001),
             "scope:accuser:differs_from"),
            (_epidemic_5007_context((0, 2)),
             "option_variant_projection"),
        )
        for context, failed_check in cases:
            with self.subTest(failed_check=failed_check):
                result = recommend_registered_vanilla_event_option_v1(
                    context,
                    played_character_id=36_403,
                    snapshot_option_count=3,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_native_option_index"])
                self.assertIn(failed_check, result["failed_checks"])

    def test_r0092_epidemic_5007_formal_planner_selects_typed_option_three(
        self,
    ) -> None:
        context = _epidemic_5007_context((1, 2))
        context.update({
            "current_event_instance_id": 21,
            "snapshot_revision": 73,
            "date_raw": 53_359_920,
            "unavailable_reason": None,
            "calculated_event_id": 1,
            "runtime_stats_ordinal": 1,
            "readiness": {
                "event_definition_identity_ready": True,
                "root_scope_ready": True,
                "saved_scopes_ready": True,
                "option_presentation_ready": True,
                "effect_indicators_ready": True,
                "effect_preview_ready": False,
                "semantic_decision_ready": False,
            },
            "provenance": {
                "root": "module+0x570F7B8->+0x10",
                "idler_vtable_rva": "0x40B1D30",
                "manager_offset": "+0x28",
                "backend_id": "ck3-1.19.0.6-native-event-window-v1",
            },
        })
        for option in context["options"]:
            option.update({
                "resolved_name": "test option",
                "unavailable_reason": "",
                "effect_indicators": {
                    "status": "available",
                    "coverage": (
                        "played-character-event-icon-indicators-1.19.0.6-v1"
                    ),
                    "complete_effect_set": False,
                    "rows": [],
                },
                "effect_preview": {
                    "status": "unavailable",
                    "reason": "indicator_subset_has_no_completeness_signal",
                },
                "resource_deltas": {"status": "unavailable"},
                "relationship_deltas": {"status": "unavailable"},
            })
        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "accepted": True,
                "status": "available",
                "snapshot_revision": 73,
                "current_event_instance_id": 21,
                "date_raw": 53_359_920,
                "current_event_window_context": copy.deepcopy(context),
                "queried_snapshot_id": "native:73",
                "queried_revision": 74,
                "queried_native_revision": 73,
            },
        }]
        snapshot = {
            "snapshot_id": "native:73",
            "revision": 74,
            "native_revision": 73,
            "date_raw": 53_359_920,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {"character_id": 36_403, "alive": True},
            "active_event": {"instance_id": 21, "option_count": 3},
        }
        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-3",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-3")
        self.assertEqual(plan["event_decision"]["selected_native_option_index"], 2)
        self.assertEqual(plan["event_decision"]["failed_checks"], [])

    def test_r0094_epidemic_1020_selects_authored_flower_response(self) -> None:
        result = recommend_registered_vanilla_event_option_v1(
            _epidemic_1020_context(),
            played_character_id=36_403,
            snapshot_option_count=2,
        )

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 1)
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(
            result["choice_effect_profile"]["observable_postcondition"][
                "expected_relation"
            ],
            "strictly_decreasing",
        )

    def test_r0094_epidemic_1020_scope_or_option_drift_blocks(self) -> None:
        same_player = _epidemic_1020_context(courtier_character_id=36_403)
        missing_county = _epidemic_1020_context()
        missing_county["saved_scopes"] = [
            row for row in missing_county["saved_scopes"]
            if row["name"] != "epidemic_county"
        ]
        wrong_option = _epidemic_1020_context()
        wrong_option["options"][0]["enabled"] = False
        cases = (
            (same_player, "scope:miasma_courtier:unique_character_excludes"),
            (missing_county, "saved_scope_names_exact"),
            (wrong_option, "selected_native_option_enabled"),
        )
        for context, failed_check in cases:
            with self.subTest(failed_check=failed_check):
                result = recommend_registered_vanilla_event_option_v1(
                    context,
                    played_character_id=36_403,
                    snapshot_option_count=2,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_native_option_index"])
                self.assertIn(failed_check, result["failed_checks"])

    def test_r0094_epidemic_1020_formal_planner_selects_typed_option_one(
        self,
    ) -> None:
        context = _epidemic_1020_context()
        context.update({
            "current_event_instance_id": 21,
            "snapshot_revision": 11,
            "date_raw": 53_361_360,
            "unavailable_reason": None,
            "calculated_event_id": 1,
            "runtime_stats_ordinal": 1,
            "readiness": {
                "event_definition_identity_ready": True,
                "root_scope_ready": True,
                "saved_scopes_ready": True,
                "option_presentation_ready": True,
                "effect_indicators_ready": True,
                "effect_preview_ready": False,
                "semantic_decision_ready": False,
            },
            "provenance": {
                "root": "module+0x570F7B8->+0x10",
                "idler_vtable_rva": "0x40B1D30",
                "manager_offset": "+0x28",
                "backend_id": "ck3-1.19.0.6-native-event-window-v1",
            },
        })
        for option in context["options"]:
            option.update({
                "resolved_name": "test option",
                "unavailable_reason": "",
                "effect_indicators": {
                    "status": "available",
                    "coverage": (
                        "played-character-event-icon-indicators-1.19.0.6-v1"
                    ),
                    "complete_effect_set": False,
                    "rows": [],
                },
                "effect_preview": {
                    "status": "unavailable",
                    "reason": "indicator_subset_has_no_completeness_signal",
                },
                "resource_deltas": {"status": "unavailable"},
                "relationship_deltas": {"status": "unavailable"},
            })
        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "accepted": True,
                "status": "available",
                "snapshot_revision": 11,
                "current_event_instance_id": 21,
                "date_raw": 53_361_360,
                "current_event_window_context": copy.deepcopy(context),
                "queried_snapshot_id": "native:11",
                "queried_revision": 12,
                "queried_native_revision": 11,
            },
        }]
        snapshot = {
            "snapshot_id": "native:11",
            "revision": 12,
            "native_revision": 11,
            "date_raw": 53_361_360,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {"character_id": 36_403, "alive": True},
            "played_character_gold": {"raw": 66_365_619, "scale": 100_000},
            "active_event": {"instance_id": 21, "option_count": 2},
        }
        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        self.assertEqual(plan["event_decision"]["selected_native_option_index"], 0)
        self.assertEqual(plan["event_decision"]["failed_checks"], [])
        self.assertEqual(plan["event_material_postcondition"]["status"], "ready")
        self.assertEqual(
            plan["event_material_postcondition"]["starting_value"], 66_365_619
        )

        missing_gold = {**snapshot, "played_character_gold": None}
        blocked = choose_one_life_turn(
            history,
            snapshot=missing_gold,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )
        self.assertEqual(
            blocked["phase"], "active_event_registry_material_observation_blocked"
        )
        self.assertIsNone(blocked["selected_step"])

    def test_other_variant_contracts_still_require_explicit_consumer_review(
        self,
    ) -> None:
        context = _context()
        context["event_definition_key"] = "adultery.0002"

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
        self.assertIn(
            "direct_projection_support:option_variants", result["failed_checks"]
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

    def test_hostile_scheme_notification_uses_exact_relational_projection(
        self,
    ) -> None:
        result = recommend_registered_vanilla_event_option_v1(
            _hostile_scheme_context(),
            played_character_id=PLAYER,
            snapshot_option_count=1,
        )

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["failed_checks"], [])

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
