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
from xar_autoplayer.vanilla_events.records_death_management import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_DEATH_MANAGEMENT_ANALYSIS,
    VANILLA_DEATH_MANAGEMENT_OBSERVATIONS,
    VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
import zg361_phase2_promotion_source_production_entry as production  # noqa: E402


EVENT_KEY = "death_management.1007"
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


class DeathManagementEventRecordTests(unittest.TestCase):
    def test_contract_is_portable_and_keeps_no_killer_shape_exact(self) -> None:
        contract = VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["unique_character_scope_excludes"], {
            "dead_character": (PLAYER_SENTINEL,),
        })
        self.assertEqual(contract["scope_types"], {
            "new_memory": "character_memory",
            "dead_character": "character",
            "deceased_character_stress": "value",
        })
        self.assertEqual(contract["saved_scope_count"], 3)
        self.assertEqual(contract["native_option_indices"], (0,))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        self.assertNotIn("optional_scope_types", contract)
        self.assertEqual(
            contract["occurrence_policy"],
            "repeatable-within-product-observation-window",
        )

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"dead_character": (32904,)},
        )
        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)

    def test_analysis_freezes_sources_and_complete_effect_boundary(self) -> None:
        analysis = VANILLA_DEATH_MANAGEMENT_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "1948-2057")
        self.assertEqual(analysis["heir_family_dispatch_lines"], "690-696")
        self.assertEqual(analysis["close_family_memory_lines"], "966-984")
        self.assertEqual(analysis["character_memory_abi_lines"], "58-70")
        self.assertIn("saves it as new_memory", analysis["caller_semantics"])
        self.assertIn("exactly twenty", analysis["option_semantics"][0])
        self.assertIn("trait-dependent", analysis["option_semantics"][0])
        self.assertIn("display-only", analysis["after_effect"])
        self.assertIn("must remain RED", analysis["strict_shape_boundary"])
        self.assertIn("independently", analysis["repeatability"])
        self.assertIn("not a campaign", analysis["duplicate_blocker_boundary"])
        self.assertIn("does not save", analysis["option_semantics"][0])
        self.assertEqual(len(analysis["source_sha256"]), 6)
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r374_values_remain_observation_only(self) -> None:
        exemplar, = VANILLA_DEATH_MANAGEMENT_OBSERVATIONS[EVENT_KEY][
            "exemplars"
        ]
        contract_repr = repr(
            VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS[EVENT_KEY]
        )

        self.assertEqual(exemplar["event_instance_id"], 1046)
        self.assertEqual(exemplar["date_raw"], 53590464)
        self.assertEqual(exemplar["saved_character_ids"], {
            "dead_character": 39246,
        })
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "new_memory": 34,
            "dead_character": 4,
            "deceased_character_stress": 1,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertFalse(exemplar["process_restart_required"])
        self.assertEqual(exemplar["snapshot_id"], "native:1779")
        self.assertEqual(exemplar["revision"], 1780)
        for field in (
            "artifact_sha256",
            "park_artifact_sha256",
            "driver_state_artifact_sha256",
        ):
            self.assertRegex(exemplar[field], SHA256_PATTERN)
        for observation_only in (1046, 53590464, 39246, 32904, 51852, 1779):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_mcp_and_runtime_include_record(self) -> None:
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS), 185)
        self.assertEqual(len(DEFAULT_VANILLA_EVENT_ANALYSIS), 185)
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_DEATH_MANAGEMENT_OBSERVATIONS[EVENT_KEY],
        )
        self.assertEqual(len(production.KNOWN_TIMELINE_INTERRUPTS), 328)
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        self.assertEqual(response["contract"]["native_option_indices"], [0])
        self.assertEqual(response["analysis"]["definition_lines"], "1948-2057")
        self.assertEqual(
            response["observations"]["exemplars"][0]["event_instance_id"],
            1046,
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
            starting_date=53590000,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1046,
            "date_raw": 53590464,
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
                _generic_scope("new_memory", "character_memory"),
                _character_scope("dead_character", 39246),
                _generic_scope("deceased_character_stress", "value"),
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
                "date_raw": 53590464,
                "active_event": {"option_count": 1},
            },
            event={"event_instance_id": 1046},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)


if __name__ == "__main__":
    unittest.main()
