from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_trait_specific import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_TRAIT_SPECIFIC_ANALYSIS,
    VANILLA_TRAIT_SPECIFIC_OBSERVATIONS,
    VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


EVENT_KEY = "trait_specific.4001"
HERBALIST_EVENT_KEY = "trait_specific.8001"
POET_EVENT_KEY = "trait_specific.9001"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _character_scope(name: str, character_id: int) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "character",
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": character_id,
            },
        },
    }


def _secret_scope(name: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "secret",
            "typed_identity": {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            },
        },
    }


def _boolean_scope(name: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "boolean",
            "typed_identity": {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            },
        },
    }


class TraitSpecificEventRecordTests(unittest.TestCase):
    def test_poet_event_selects_exact_source_reviewed_trait_route(self) -> None:
        contract = VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS[POET_EVENT_KEY]
        analysis = VANILLA_TRAIT_SPECIFIC_ANALYSIS[POET_EVENT_KEY]
        exemplar = VANILLA_TRAIT_SPECIFIC_OBSERVATIONS[POET_EVENT_KEY][
            "exemplars"
        ][0]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["scope_types"], {"subject": "character"})
        self.assertEqual(contract["saved_scope_name_sets"], (("subject",),))
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertIn(
            "poetry_romance_target",
            analysis["source_possible_scope_variants"],
        )
        self.assertEqual(
            analysis["source_sha256"][
                "common/on_action/yearly_groups_on_actions.txt"
            ],
            "D916E482A780F26CC1B1B27B582B675F90945AB808EB461A54A906EAAD0147C5",
        )
        utility = analysis["selected_choice_campaign_utility_profile"]
        self.assertEqual(
            utility["objective_id"],
            "acquire_long_term_poet_trait_from_one_time_event",
        )
        self.assertEqual(exemplar["run"], "R856")
        self.assertEqual(exemplar["event_instance_id"], 4)
        self.assertFalse(exemplar["selection_attempted"])
        self.assertTrue(exemplar["retained_red"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        self.assertRegex(exemplar["driver_state_artifact_sha256"], SHA256_PATTERN)

    def test_poet_event_r856_shape_is_recommended_and_scope_drift_blocks(self) -> None:
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": POET_EVENT_KEY,
            "current_event_instance_id": 4,
            "date_raw": 53208912,
            "root_scope": _character_scope("root", 31853)["scope"],
            "saved_scopes": [_character_scope("subject", 1)],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }

        recommendation = recommend_registered_vanilla_event_option_v1(
            context,
            played_character_id=31853,
            snapshot_option_count=3,
        )
        self.assertEqual(recommendation["status"], "recommended")
        self.assertEqual(recommendation["selected_option_number"], 1)
        self.assertEqual(recommendation["selected_native_option_index"], 0)
        self.assertEqual(recommendation["selected_rendered_index"], 0)
        self.assertTrue(recommendation["campaign_utility_ready"])
        self.assertEqual(
            recommendation["choice_effect_profile"]["selected_option_effects"]
            [0]["trait"],
            "lifestyle_poet",
        )

        drifted = json.loads(json.dumps(context))
        drifted["saved_scopes"].append(_boolean_scope("poetry_romance_target"))
        blocked = recommend_registered_vanilla_event_option_v1(
            drifted,
            played_character_id=31853,
            snapshot_option_count=3,
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(
            blocked["unavailable_reason"],
            "registered_contract_projection_drift",
        )

    def test_poet_event_r856_shape_passes_production_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[POET_EVENT_KEY],
            player=31853,
            event_key=POET_EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53200000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": POET_EVENT_KEY,
            "current_event_instance_id": 4,
            "date_raw": 53208912,
            "root_scope": _character_scope("root", 31853)["scope"],
            "saved_scopes": [_character_scope("subject", 1)],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53208912,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 4},
            context=context,
            event_key=POET_EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)

    def test_herbalist_refusal_gold_effect_profile_is_queryable(self) -> None:
        response = query_vanilla_event_knowledge_v1(HERBALIST_EVENT_KEY)
        profile = response["analysis"]["selected_choice_effect_profile"]

        json.dumps(profile, allow_nan=False)
        self.assertEqual(profile["selected_native_option_index"], 1)
        effect = profile["selected_option_effects"][0]
        self.assertEqual(effect["authored_value_key"], "minor_gold_value")
        self.assertEqual(effect["authored_minimum_whole"], 15)
        self.assertFalse(effect["runtime_delta_exact"])
        self.assertEqual(
            profile["observable_postcondition"]["metric"],
            "played_character_gold.raw",
        )
        utility = response["analysis"][
            "selected_choice_campaign_utility_profile"
        ]
        self.assertEqual(
            utility["objective_id"],
            "increase_liquid_reserve_without_random_persistence",
        )
        self.assertEqual(utility["selected_rank"], 1)
        self.assertEqual(utility["rank_count"], 2)
        self.assertIsNone(utility["cross_event_numeric_score"])

    def test_herbalist_seed_event_uses_deterministic_gold_route(self) -> None:
        contract = VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS[
            HERBALIST_EVENT_KEY
        ]
        analysis = VANILLA_TRAIT_SPECIFIC_ANALYSIS[HERBALIST_EVENT_KEY]
        exemplar = VANILLA_TRAIT_SPECIFIC_OBSERVATIONS[
            HERBALIST_EVENT_KEY
        ]["exemplars"][0]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["saved_scope_name_sets"], ((),))
        self.assertEqual(contract["saved_scope_count"], 0)
        self.assertEqual(contract["native_option_indices"], (0, 1))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )
        self.assertIn("ten years", analysis["option_semantics"][0])
        self.assertIn("deterministic positive gold", analysis["safe_option_rationale"])
        self.assertEqual(exemplar["run"], "R414-attempt-06")
        self.assertEqual(exemplar["event_instance_id"], 1075)
        self.assertEqual(exemplar["snapshot_id"], "native:1913")
        self.assertFalse(exemplar["selection_attempted"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_herbalist_seed_live_shape_passes_production_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[HERBALIST_EVENT_KEY],
            player=32904,
            event_key=HERBALIST_EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53780000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": HERBALIST_EVENT_KEY,
            "current_event_instance_id": 1075,
            "date_raw": 53783472,
            "root_scope": _character_scope("root", 32904)["scope"],
            "saved_scopes": [],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53783472,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 1075},
            context=context,
            event_key=HERBALIST_EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

    def test_contract_is_portable_and_selects_non_conversion_route(self) -> None:
        contract = VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "witch": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["optional_unique_character_scope_excludes"], {
            "created_witch": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["optional_character_scope_matches_any"], {
            "created_witch": ("witch",),
        })
        self.assertEqual(contract["scope_types"], {
            "witch": "character",
        })
        self.assertEqual(contract["optional_scope_types"], {
            "created_witch": "character",
            "witch_secret": "secret",
            "old_courtier": "boolean",
        })
        self.assertEqual(contract["boolean_scope_name_sets"], (
            (),
            ("old_courtier",),
        ))
        self.assertEqual(contract["saved_scope_counts"], (1, 2, 3))
        self.assertEqual(contract["native_option_indices"], (0, 1))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"witch": (32904,)},
        )
        self.assertEqual(
            materialized["optional_unique_character_scope_excludes"],
            {"created_witch": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_sources_and_complete_side_effect_boundary(self) -> None:
        analysis = VANILLA_TRAIT_SPECIFIC_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "584-717")
        self.assertEqual(analysis["random_yearly_playable_pulse_lines"], "2522-2563")
        self.assertEqual(analysis["on_yearly_pool_entry_line"], "3019")
        self.assertIn("not a daily event", analysis["frequency_boundary"])
        self.assertIn("same-culture, same-faith witch", analysis["immediate_effect"])
        self.assertIn("existing-courtier branch", analysis["source_scope_variants"])
        self.assertIn("learning plus one", analysis["option_semantics"][0])
        self.assertIn("one hundred", analysis["option_semantics"][1])
        self.assertIn(
            "downstream player choices",
            analysis["conversion_outcome_boundary"],
        )
        self.assertIn("owner-deferred", analysis["religion_scope_boundary"])
        self.assertIsNone(analysis["after_effect"])
        self.assertEqual(len(analysis["source_sha256"]), 11)
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r374_values_remain_observation_only(self) -> None:
        r374, r414 = VANILLA_TRAIT_SPECIFIC_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(r374["event_instance_id"], 1040)
        self.assertEqual(r374["date_raw"], 53583192)
        self.assertEqual(r374["saved_character_ids"], {
            "created_witch": 94245,
            "witch": 94245,
        })
        self.assertEqual(r374["saved_scope_raw_types"], {
            "created_witch": 4,
            "witch_secret": 7,
            "witch": 4,
        })
        self.assertEqual(r374["rendered_native_option_indices"], [0, 1])
        self.assertFalse(r374["selection_attempted"])
        self.assertFalse(r374["process_restart_required"])
        self.assertEqual(r374["snapshot_id"], "native:1669")
        self.assertEqual(r374["revision"], 1670)
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(r374[field], SHA256_PATTERN)

        self.assertEqual(r414["run"], "R414")
        self.assertEqual(r414["saved_scope_raw_types"], {
            "old_courtier": 2,
            "witch": 4,
        })
        self.assertEqual(r414["saved_character_ids"], {"witch": 94245})
        self.assertEqual(r414["snapshot_id"], "native:660")
        self.assertFalse(r414["selection_attempted"])
        self.assertFalse(r414["product_failure_proven"])
        self.assertTrue(r414["retained_red"])
        self.assertRegex(r414["artifact_sha256"], SHA256_PATTERN)

        for observation_only in (
            1040, 1067, 53583192, 53681976, 94245, 32904, 51852, 202268, 1669,
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_runtime_include_record(self) -> None:
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 195)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_ANALYSIS), 195)
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_TRAIT_SPECIFIC_OBSERVATIONS[EVENT_KEY],
        )
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 341)
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0, 1])
        self.assertEqual(response["analysis"]["definition_lines"], "584-717")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            1040,
        )
        json.dumps(response, allow_nan=False)

    def test_current_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53580000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1040,
            "date_raw": 53583192,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 32904,
                },
            },
            "saved_scopes": [
                _character_scope("created_witch", 94245),
                _secret_scope("witch_secret"),
                _character_scope("witch", 94245),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53583192,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 1040},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

    def test_registry_consumes_only_four_exact_witch_scope_shapes(self) -> None:
        root = 101
        witch = 202
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 7,
            "date_raw": 53200000,
            "root_scope": _character_scope("root", root)["scope"],
            "saved_scopes": [],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        witch_scope = _character_scope("witch", witch)
        created_scope = _character_scope("created_witch", witch)
        shapes = (
            [witch_scope],
            [_boolean_scope("old_courtier"), witch_scope],
            [created_scope, witch_scope],
            [created_scope, _secret_scope("witch_secret"), witch_scope],
        )
        for scopes in shapes:
            with self.subTest(scopes=[row["name"] for row in scopes]):
                frame = {**context, "saved_scopes": scopes}
                result = recommend_registered_vanilla_event_option_v1(
                    frame, played_character_id=root, snapshot_option_count=2
                )
                self.assertEqual(result["status"], "recommended", result)
                self.assertEqual(result["selected_option_number"], 2)
                self.assertEqual(result["selected_native_option_index"], 1)
                self.assertEqual(result["failed_checks"], [])

        drifted_shapes = (
            [_character_scope("witch", root)],
            [_character_scope("created_witch", root), witch_scope],
            [_character_scope("created_witch", witch + 1), witch_scope],
            [_secret_scope("created_witch"), witch_scope],
            [_boolean_scope("old_courtier"), created_scope, witch_scope],
            [created_scope, _boolean_scope("witch_secret"), witch_scope],
            [witch_scope, _character_scope("witch", witch)],
            [witch_scope, _secret_scope("unexpected_scope")],
        )
        for scopes in drifted_shapes:
            with self.subTest(drift=[row["name"] for row in scopes]):
                frame = {**context, "saved_scopes": scopes}
                result = recommend_registered_vanilla_event_option_v1(
                    frame, played_character_id=root, snapshot_option_count=2
                )
                self.assertEqual(result["status"], "blocked", result)

        disabled = json.loads(json.dumps(context))
        disabled["saved_scopes"] = [witch_scope]
        disabled["options"][1]["enabled"] = False
        result = recommend_registered_vanilla_event_option_v1(
            disabled, played_character_id=root, snapshot_option_count=2
        )
        self.assertEqual(result["status"], "blocked", result)

    def test_existing_courtier_live_shape_passes_production_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53680000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1067,
            "date_raw": 53681976,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 32904,
                },
            },
            "saved_scopes": [
                _boolean_scope("old_courtier"),
                _character_scope("witch", 94245),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(2)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53681976,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 1067},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)


if __name__ == "__main__":
    unittest.main()
