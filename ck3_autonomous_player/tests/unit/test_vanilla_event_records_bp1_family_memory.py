from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import zg361_phase2_promotion_source_production_entry as production  # noqa: E402
from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.portable_evidence import (  # noqa: E402
    query_vanilla_event_evidence_index_v1,
)
from xar_autoplayer.vanilla_events.records_bp1_yearly import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_BP1_YEARLY_ANALYSIS,
    VANILLA_BP1_YEARLY_OBSERVATIONS,
    VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "bp1_yearly.4000"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


def _scope(
    name: str,
    type_key: str,
    *,
    character_id: int | None = None,
) -> dict[str, object]:
    typed_identity: dict[str, object]
    if character_id is None:
        typed_identity = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    else:
        typed_identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": type_key,
            "typed_identity": typed_identity,
        },
    }


class Bp1FamilyMemoryEventRecordTests(unittest.TestCase):
    def test_contract_binds_dead_participant_projection(self) -> None:
        contract = VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["scope_types"], {
            "family_memory": "character_memory",
            "family_memory_participant": "character",
        })
        self.assertEqual(
            contract["saved_scope_name_sets"],
            (("family_memory", "family_memory_participant"),),
        )
        self.assertEqual(contract["saved_scope_count"], 2)
        self.assertEqual(contract["option_count"], 2)
        self.assertEqual(contract["snapshot_option_count"], 5)
        self.assertEqual(contract["native_option_indices"], (1, 3))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"family_memory_participant": (32904,)},
        )

    def test_analysis_freezes_source_and_deterministic_choice(self) -> None:
        analysis = VANILLA_BP1_YEARLY_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "22-292")
        self.assertEqual(analysis["on_yearly_pool_entry_line"], "3377")
        self.assertEqual(analysis["yearly_group_pool_entry_line"], "227")
        self.assertIn("five-year cooldown", analysis["frequency_boundary"])
        self.assertIn("deterministic", analysis["option_semantics"][1])
        self.assertIn("diplomacy-10 duel", analysis["option_semantics"][3])
        self.assertIn("minor stress gain", analysis["safe_option_rationale"])
        self.assertIsNone(analysis["after_effect"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r416_values_remain_observation_only(self) -> None:
        exemplar = VANILLA_BP1_YEARLY_OBSERVATIONS[EVENT_KEY]["exemplars"][0]
        contract_repr = repr(VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["run"], "R416-retry-10")
        self.assertEqual(exemplar["red_classification"], "harness-route-red")
        self.assertFalse(exemplar["product_failure_proven"])
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            "family_memory": 34,
            "family_memory_participant": 4,
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [1, 3])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        for observation_only in (53902032, 1090, 32904, 67046, 174656):
            self.assertNotIn(str(observation_only), contract_repr)

    def test_default_registry_runtime_and_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_BP1_YEARLY_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_BP1_YEARLY_OBSERVATIONS[EVENT_KEY],
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["native_option_indices"], [1, 3])
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 22)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)

    def test_r416_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53783472,
            absolute_end_date=53958720,
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1090,
            "date_raw": 53902032,
            "root_scope": _scope("root", "character", character_id=32904)["scope"],
            "saved_scopes": [
                _scope("family_memory", "character_memory"),
                _scope(
                    "family_memory_participant",
                    "character",
                    character_id=67046,
                ),
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
                for rendered, native in ((0, 1), (1, 3))
            ],
        }
        checks = production._known_interrupt_checks(
            snapshot={
                "date_raw": 53902032,
                "active_event": {"option_count": 5},
            },
            event={"event_instance_id": 1090},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
