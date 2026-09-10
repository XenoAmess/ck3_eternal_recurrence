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
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


EVENT_KEY = "trait_specific.4001"
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


class TraitSpecificEventRecordTests(unittest.TestCase):
    def test_contract_is_portable_and_selects_non_conversion_route(self) -> None:
        contract = VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "created_witch": (PLAYER_SENTINEL,),
            "witch": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["character_scope_matches_any"], {
            "created_witch": ("witch",),
            "witch": ("created_witch",),
        })
        self.assertEqual(contract["scope_types"], {
            "created_witch": "character",
            "witch_secret": "secret",
            "witch": "character",
        })
        self.assertEqual(contract["saved_scope_count"], 3)
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
            {"created_witch": (32904,), "witch": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_sources_and_complete_side_effect_boundary(self) -> None:
        analysis = VANILLA_TRAIT_SPECIFIC_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "584-717")
        self.assertEqual(analysis["random_yearly_playable_pulse_lines"], "2522-2563")
        self.assertEqual(analysis["on_yearly_pool_entry_line"], "3019")
        self.assertIn("not a daily event", analysis["frequency_boundary"])
        self.assertIn("same-culture, same-faith witch", analysis["immediate_effect"])
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
        exemplar, = VANILLA_TRAIT_SPECIFIC_OBSERVATIONS[EVENT_KEY]["exemplars"]
        contract_repr = repr(VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["event_instance_id"], 1040)
        self.assertEqual(exemplar["date_raw"], 53583192)
        self.assertEqual(exemplar["saved_character_ids"], {
            "created_witch": 94245,
            "witch": 94245,
        })
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "created_witch": 4,
            "witch_secret": 7,
            "witch": 4,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["process_restart_required"])
        self.assertEqual(exemplar["snapshot_id"], "native:1669")
        self.assertEqual(exemplar["revision"], 1670)
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (1040, 53583192, 94245, 32904, 51852, 1669):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_runtime_include_record(self) -> None:
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 172)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_ANALYSIS), 172)
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_TRAIT_SPECIFIC_OBSERVATIONS[EVENT_KEY],
        )
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 316)
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


if __name__ == "__main__":
    unittest.main()
