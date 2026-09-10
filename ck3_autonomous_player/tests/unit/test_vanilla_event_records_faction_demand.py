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
from xar_autoplayer.vanilla_events.records_faction_demand import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_FACTION_DEMAND_ANALYSIS,
    VANILLA_FACTION_DEMAND_OBSERVATIONS,
    VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


CLAIMANT_EVENT_KEY = "faction_demand.2001"
PEASANT_EVENT_KEY = "faction_demand.1101"
POPULIST_VASSAL_EVENT_KEY = "faction_demand.0099"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _generic_scope(name: str, type_key: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            },
        },
    }


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


class FactionDemandEventRecordTests(unittest.TestCase):
    def test_populist_vassal_no_side_route_matches_r406(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[POPULIST_VASSAL_EVENT_KEY],
            player=33596113,
            event_key=POPULIST_VASSAL_EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53998728,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": POPULIST_VASSAL_EVENT_KEY,
            "current_event_instance_id": 2152,
            "date_raw": 54001392,
            "root_scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": 33596113,
                },
            },
            "saved_scopes": [
                _generic_scope("faction", "faction"),
                _generic_scope("peasant_county", "landed_title"),
                _character_scope("faction_target", 16863885),
                _generic_scope("target_title", "landed_title"),
                _character_scope("peasant_leader", 117494968),
                _generic_scope("populist_war", "war"),
            ],
            "options": [
                {
                    "rendered_index": rendered,
                    "native_option_index": native,
                    "shown": True,
                    "enabled": True,
                    "fallback": False,
                    "cancel": False,
                }
                for rendered, native in enumerate((1, 2))
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 54001392,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 2152},
            context=context,
            event_key=POPULIST_VASSAL_EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertIn(
            "no-op route",
            VANILLA_FACTION_DEMAND_ANALYSIS[POPULIST_VASSAL_EVENT_KEY][
                "safe_option_rationale"
            ],
        )
        exemplar, = VANILLA_FACTION_DEMAND_OBSERVATIONS[
            POPULIST_VASSAL_EVENT_KEY
        ]["exemplars"]
        self.assertEqual(exemplar["event_instance_id"], 2152)
        self.assertFalse(exemplar["selection_attempted"])

    def test_contract_is_portable_and_selects_war_ooda_route(self) -> None:
        contract = VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS[
            CLAIMANT_EVENT_KEY
        ]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["character_scopes"], {
            "faction_target": PLAYER_SENTINEL,
        })
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "faction_leader": (PLAYER_SENTINEL,),
            "faction_claimant": (PLAYER_SENTINEL,),
        })
        self.assertNotIn("character_scope_differs_from", contract)
        self.assertEqual(contract["saved_scope_count"], 5)
        self.assertEqual(contract["native_option_indices"], (0, 1, 2))
        self.assertEqual(contract["disabled_native_option_indices"], (1,))
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(materialized["character_scopes"], {
            "faction_target": 32904,
        })
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"faction_leader": (32904,), "faction_claimant": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_sources_and_complete_decision_boundary(self) -> None:
        analysis = VANILLA_FACTION_DEMAND_ANALYSIS[CLAIMANT_EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "2039-2277")
        self.assertEqual(analysis["demand_dispatch_lines"], "992-1026")
        self.assertEqual(analysis["monthly_faction_abi_lines"], "136-143")
        self.assertIn("five days", analysis["caller_semantics"])
        self.assertIn("once per month", analysis["frequency_boundary"])
        self.assertIn("ninety", analysis["frequency_boundary"])
        self.assertIn("claimant title/vassal transfer", analysis["option_semantics"][0])
        self.assertIn("shown but disabled", analysis["option_semantics"][1])
        self.assertIn("starts", analysis["option_semantics"][2])
        self.assertIn("war OODA", analysis["safe_option_rationale"])
        self.assertIn("does not infer", analysis["religion_scope_boundary"])
        self.assertIn("removes", analysis["after_effect"])
        self.assertEqual(len(analysis["source_sha256"]), 11)
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r374_values_remain_observation_only(self) -> None:
        exemplar, = VANILLA_FACTION_DEMAND_OBSERVATIONS[
            CLAIMANT_EVENT_KEY
        ]["exemplars"]
        contract_repr = repr(
            VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS[CLAIMANT_EVENT_KEY]
        )

        self.assertEqual(exemplar["event_instance_id"], 1050)
        self.assertEqual(exemplar["date_raw"], 53595360)
        self.assertEqual(exemplar["saved_character_ids"], {
            "faction_leader": 50355542,
            "faction_target": 32904,
            "faction_claimant": 39232,
        })
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "faction": 25,
            "faction_leader": 4,
            "faction_target": 4,
            "faction_claimant": 4,
            "faction_targeted_title": 5,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1, 2])
        self.assertEqual(exemplar["disabled_native_option_indices"], [1])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["process_restart_required"])
        self.assertEqual(exemplar["snapshot_id"], "native:1847")
        self.assertEqual(exemplar["revision"], 1848)
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (
            1050, 53595360, 50355542, 39232, 32904, 51852, 1847,
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_runtime_include_record(self) -> None:
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 170)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_ANALYSIS), 170)
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[CLAIMANT_EVENT_KEY],
            VANILLA_FACTION_DEMAND_OBSERVATIONS[CLAIMANT_EVENT_KEY],
        )
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 309)
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[CLAIMANT_EVENT_KEY],
            VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS[CLAIMANT_EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(CLAIMANT_EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0, 1, 2])
        self.assertEqual(
            response["contract"]["disabled_native_option_indices"],
            [1],
        )
        self.assertEqual(response["analysis"]["definition_lines"], "2039-2277")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            1050,
        )
        json.dumps(response, allow_nan=False)

    def test_current_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[CLAIMANT_EVENT_KEY],
            player=32904,
            event_key=CLAIMANT_EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53590000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": CLAIMANT_EVENT_KEY,
            "current_event_instance_id": 1050,
            "date_raw": 53595360,
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
                _generic_scope("faction", "faction"),
                _character_scope("faction_leader", 50355542),
                _character_scope("faction_target", 32904),
                _character_scope("faction_claimant", 39232),
                _generic_scope("faction_targeted_title", "landed_title"),
            ],
            "options": [
                {
                    "rendered_index": index,
                    "native_option_index": index,
                    "shown": True,
                    "enabled": index != 1,
                    "fallback": False,
                    "cancel": False,
                }
                for index in range(3)
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53595360,
                "active_event": {"option_count": 3},
            },
            event={"event_instance_id": 1050},
            context=context,
            event_key=CLAIMANT_EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 3)
        self.assertEqual(contract["selected_native_option_index"], 2)

    def test_peasant_contract_is_portable_and_selects_acceptance(self) -> None:
        contract = VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS[
            PEASANT_EVENT_KEY
        ]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["character_scopes"], {})
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "peasant_leader": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["saved_scope_count"], 4)
        self.assertEqual(contract["native_option_indices"], (0, 1))
        self.assertNotIn("disabled_native_option_indices", contract)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"peasant_leader": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_peasant_analysis_freezes_full_choice_boundary(self) -> None:
        analysis = VANILLA_FACTION_DEMAND_ANALYSIS[PEASANT_EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "1816-1925")
        self.assertEqual(analysis["demand_dispatch_lines"], "69-105")
        self.assertEqual(analysis["monthly_faction_abi_lines"], "136-143")
        self.assertIn("synchronously", analysis["caller_semantics"])
        self.assertIn("once per month", analysis["frequency_boundary"])
        self.assertIn("ninety", analysis["frequency_boundary"])
        self.assertIn("seventy-five", analysis["option_semantics"][0])
        self.assertIn("twenty-five", analysis["option_semantics"][1])
        self.assertIn("one hundred", analysis["option_semantics"][1])
        self.assertIn("avoids", analysis["safe_option_rationale"])
        self.assertIn("not a general", analysis["religion_scope_boundary"])
        self.assertEqual(len(analysis["source_sha256"]), 9)
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_park9_values_remain_observation_only(self) -> None:
        exemplar, = VANILLA_FACTION_DEMAND_OBSERVATIONS[
            PEASANT_EVENT_KEY
        ]["exemplars"]
        contract_repr = repr(
            VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS[PEASANT_EVENT_KEY]
        )

        self.assertEqual(exemplar["event_instance_id"], 1055)
        self.assertEqual(exemplar["date_raw"], 53607792)
        self.assertEqual(exemplar["saved_character_ids"], {
            "peasant_leader": 33633057,
        })
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "faction": 25,
            "peasant_county": 5,
            "peasant_leader": 4,
            "new_title": 5,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1])
        self.assertEqual(exemplar["enabled_native_option_indices"], [0, 1])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["process_restart_required"])
        self.assertEqual(exemplar["snapshot_id"], "native:2057")
        self.assertEqual(exemplar["revision"], 2058)
        self.assertEqual(exemplar["remaining_game_days"], 1171)
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (
            1055, 53607792, 33633057, 32904, 51852, 2057,
        ):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_peasant_default_registry_mcp_and_runtime_include_record(self) -> None:
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[PEASANT_EVENT_KEY],
            VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS[PEASANT_EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(PEASANT_EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0, 1])
        self.assertEqual(response["contract"]["selected_option_number"], 1)
        self.assertEqual(response["analysis"]["definition_lines"], "1816-1925")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            1055,
        )
        json.dumps(response, allow_nan=False)

    def test_peasant_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[PEASANT_EVENT_KEY],
            player=32904,
            event_key=PEASANT_EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53600000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": PEASANT_EVENT_KEY,
            "current_event_instance_id": 1055,
            "date_raw": 53607792,
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
                _generic_scope("faction", "faction"),
                _generic_scope("peasant_county", "landed_title"),
                _character_scope("peasant_leader", 33633057),
                _generic_scope("new_title", "landed_title"),
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
                "date_raw": 53607792,
                "active_event": {"option_count": 2},
            },
            event={"event_instance_id": 1055},
            context=context,
            event_key=PEASANT_EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)


if __name__ == "__main__":
    unittest.main()
