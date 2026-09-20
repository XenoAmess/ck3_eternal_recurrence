from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.records_chancellor_foreign_affairs import (  # noqa: E402
    VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_ANALYSIS,
    VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_OBSERVATIONS,
    VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "chancellor_task.1004"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


class ChancellorForeignAffairsRecordTests(unittest.TestCase):
    def test_contract_is_campaign_neutral_and_forced_single_option(self) -> None:
        contract = VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_TIMELINE_CONTRACTS[
            EVENT_KEY
        ]

        self.assertEqual(contract["root_character_id"], "$player")
        self.assertNotIn("date_raw", contract)
        self.assertEqual(
            contract["character_scopes"], {"councillor_liege": "$player"}
        )
        self.assertEqual(contract["saved_scope_count"], 4)
        self.assertEqual(contract["option_count"], 1)
        self.assertEqual(contract["snapshot_option_count"], 1)
        self.assertEqual(contract["native_option_indices"], (0,))
        self.assertEqual(contract["selected_option_number"], 1)
        self.assertEqual(contract["selected_native_option_index"], 0)
        rebound = materialize_vanilla_timeline_contract(contract, 29829)
        self.assertEqual(rebound["root_character_id"], 29829)
        self.assertEqual(contract["root_character_id"], "$player")

    def test_r16_native_scope_projection_selects_only_option(self) -> None:
        player = 29_829

        def scope(character_id: int) -> dict[str, object]:
            return {
                "status": "available",
                "raw_type_index": 4,
                "type_key": "character",
                "subtype": 0,
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                },
            }

        saved = (
            ("councillor", 32_716),
            ("councillor_liege", player),
            ("active_councillor", 32_716),
            ("neighbor", 37_011),
        )
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "snapshot_revision": 1,
            "date_raw": 53_151_144,
            "current_event_instance_id": 1,
            "window_match_count": 1,
            "unavailable_reason": None,
            "event_definition_key": EVENT_KEY,
            "calculated_event_id": 1_001_004,
            "runtime_stats_ordinal": 1,
            "root_scope": scope(player),
            "saved_scopes": [
                {
                    "name": name,
                    "name_identifier": index + 50,
                    "scope": scope(character_id),
                }
                for index, (name, character_id) in enumerate(saved)
            ],
            "options": [{
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
                "resolved_name": "acknowledge",
                "unavailable_reason": "",
                "effect_indicators": {
                    "status": "available",
                    "coverage": (
                        "played-character-event-icon-indicators-1.19.0.6-v1"
                    ),
                    "complete_effect_set": False,
                    "rows": [],
                },
                "effect_preview": {"status": "unavailable"},
                "resource_deltas": {"status": "unavailable"},
                "relationship_deltas": {"status": "unavailable"},
            }],
            "readiness": {},
            "provenance": {},
        }

        result = recommend_registered_vanilla_event_option_v1(
            context,
            played_character_id=player,
            snapshot_option_count=1,
        )

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["failed_checks"], [])

    def test_analysis_freezes_call_chain_and_unavoidable_effect(self) -> None:
        analysis = VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "508-525")
        self.assertIn("directly triggers .1004", analysis["caller_semantics"])
        self.assertIn("negative opinion effect is unavoidable", analysis[
            "safe_option_rationale"
        ])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r445_visual_evidence_does_not_invent_native_scopes(self) -> None:
        exemplar, = VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_OBSERVATIONS[EVENT_KEY][
            "exemplars"
        ]

        self.assertEqual(exemplar["run"], "R445")
        self.assertEqual(exemplar["option_ocr_center"], [1266, 984])
        self.assertFalse(exemplar["native_event_context_available"])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertTrue(exemplar["retained_red"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)

    def test_default_registry_and_read_only_queries_expose_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_OBSERVATIONS[EVENT_KEY],
        )

        knowledge = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(knowledge["status"], "available")
        self.assertEqual(knowledge["contract"]["native_option_indices"], [0])
        self.assertFalse(
            knowledge["observations"]["exemplars"][0][
                "native_event_context_available"
            ]
        )
        provenance = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(provenance["status"], "available")
        self.assertEqual(provenance["definition"]["line"], 508)
        json.dumps(knowledge, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
