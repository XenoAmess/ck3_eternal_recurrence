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
from xar_autoplayer.vanilla_events.records_vassal_interaction import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_VASSAL_INTERACTION_ANALYSIS,
    VANILLA_VASSAL_INTERACTION_OBSERVATIONS,
    VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


EVENT_KEY = "vassal_interaction.0040"
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


def _unavailable_character_scope(name: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": "character",
            "typed_identity": {
                "status": "unavailable",
                "reason": "character_scope_identity_unavailable",
            },
        },
    }


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


class VassalInteractionEventRecordTests(unittest.TestCase):
    def test_contract_is_portable_and_exact(self) -> None:
        contract = VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["character_scopes"], {
            "recipient": PLAYER_SENTINEL,
        })
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "actor": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["scope_types"], {
            "target": "landed_title",
            "county_in_title": "province",
        })
        self.assertEqual(contract["saved_scope_count"], 7)
        self.assertEqual(contract["native_option_indices"], (0,))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(materialized["character_scopes"], {"recipient": 32904})
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"actor": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_exact_sources_and_acknowledgement_semantics(self) -> None:
        analysis = VANILLA_VASSAL_INTERACTION_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "1416-1433")
        self.assertEqual(analysis["interaction_definition_lines"], "2903-3418")
        self.assertEqual(analysis["interaction_effect_lines"], "4233-4244")
        self.assertIn("auto-accepted", analysis["caller_semantics"])
        self.assertIn("does not execute", analysis["option_semantics"][0])
        self.assertIn("other qualifying actors", analysis["repeatability"])
        self.assertIsNone(analysis["event_immediate_effect"])
        self.assertIsNone(analysis["after_effect"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r374_campaign_values_remain_observation_only(self) -> None:
        exemplar, = VANILLA_VASSAL_INTERACTION_OBSERVATIONS[EVENT_KEY][
            "exemplars"
        ]
        contract_repr = repr(
            VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS[EVENT_KEY]
        )

        self.assertEqual(exemplar["event_instance_id"], 1038)
        self.assertEqual(exemplar["date_raw"], 53582544)
        self.assertEqual(exemplar["saved_character_ids"], {
            "actor": 39232,
            "recipient": 32904,
        })
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "actor": 4,
            "recipient": 4,
            "secondary_actor": 4,
            "secondary_recipient": 4,
            "intermediary": 4,
            "target": 5,
            "county_in_title": 8,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["process_restart_required"])
        self.assertEqual(exemplar["snapshot_id"], "native:1655")
        self.assertEqual(exemplar["revision"], 1656)
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (1038, 53582544, 39232, 32904, 51852, 1655):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_runtime_include_record(self) -> None:
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 165)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_ANALYSIS), 165)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_OBSERVATIONS), 16)
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 304)
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0])
        self.assertEqual(response["analysis"]["definition_lines"], "1416-1433")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            1038,
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
            "current_event_instance_id": 1038,
            "date_raw": 53582544,
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
                _character_scope("actor", 39232),
                _character_scope("recipient", 32904),
                _unavailable_character_scope("secondary_actor"),
                _unavailable_character_scope("secondary_recipient"),
                _unavailable_character_scope("intermediary"),
                _generic_scope("target", "landed_title"),
                _generic_scope("county_in_title", "province"),
            ],
            "options": [{
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53582544,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 1038},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)


if __name__ == "__main__":
    unittest.main()
