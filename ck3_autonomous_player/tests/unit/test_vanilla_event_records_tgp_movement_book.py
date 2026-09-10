from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
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
from xar_autoplayer.vanilla_events.records_tgp_movement import (  # noqa: E402
    PLAYER_SENTINEL,
    VANILLA_TGP_MOVEMENT_ANALYSIS,
    VANILLA_TGP_MOVEMENT_OBSERVATIONS,
    VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_provenance_v1,
)


EVENT_KEY = "tgp_movement_events.0110"
SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
SCOPE_TYPES = {
    "root_scope": "character",
    "my_movement": "situation_participant_group",
    "other_ruler": "character",
    "owner": "character",
    "author": "character",
    "random_quality_bonus": "value",
    "quality": "value",
    "wealth": "value",
    "newly_created_artifact": "artifact",
    "skill_base": "character",
    "book_content_quality": "value",
}


def _scope(name: str, character_id: int | None = None) -> dict[str, object]:
    identity = (
        {"status": "available", "kind": "character", "character_id": character_id}
        if character_id is not None
        else {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    )
    return {
        "name": name,
        "scope": {
            "status": "available",
            "type_key": SCOPE_TYPES[name],
            "typed_identity": identity,
        },
    }


class TgpMovementBookEventRecordTests(unittest.TestCase):
    def test_contract_is_campaign_neutral_and_selects_prestige(self) -> None:
        contract = VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertEqual(contract["character_scopes"], {
            "root_scope": PLAYER_SENTINEL,
        })
        self.assertEqual(contract["scope_types"], SCOPE_TYPES)
        self.assertEqual(contract["saved_scope_count"], 11)
        self.assertEqual(contract["option_count"], 2)
        self.assertEqual(contract["native_option_indices"], (0, 1))
        self.assertEqual(contract["selected_option_number"], 2)
        self.assertEqual(contract["selected_native_option_index"], 1)

        materialized = materialize_vanilla_timeline_contract(contract, 32904)
        self.assertEqual(materialized["root_character_id"], 32904)
        self.assertEqual(materialized["character_scopes"], {"root_scope": 32904})
        self.assertEqual(
            materialized["unique_character_scope_excludes"],
            {"other_ruler": (32904,)},
        )

    def test_analysis_freezes_unavoidable_artifact_and_narrower_route(self) -> None:
        analysis = VANILLA_TGP_MOVEMENT_ANALYSIS[EVENT_KEY]

        self.assertEqual(analysis["definition_lines"], "2407-2530")
        self.assertIn("five-year cooldown", analysis["frequency_boundary"])
        self.assertIn("all eleven", analysis["source_scope_boundary"])
        self.assertIn("potential_friend", analysis["option_semantics"][0])
        self.assertIn("medium_prestige_gain", analysis["option_semantics"][1])
        self.assertIn("unavoidable", analysis["after_effect"])
        self.assertIsNone(analysis["follow_up_event"])
        for digest in analysis["source_sha256"].values():
            self.assertRegex(digest, SHA256_PATTERN)

    def test_r416_values_remain_observation_only(self) -> None:
        exemplar = VANILLA_TGP_MOVEMENT_OBSERVATIONS[EVENT_KEY]["exemplars"][0]
        contract_repr = repr(VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[EVENT_KEY])

        self.assertEqual(exemplar["run"], "R416")
        self.assertEqual(exemplar["red_classification"], "harness-route-red")
        self.assertEqual(exemplar["saved_scope_raw_types"], {
            name: {
                "character": 4,
                "situation_participant_group": 61,
                "value": 1,
                "artifact": 31,
            }[type_key]
            for name, type_key in SCOPE_TYPES.items()
        })
        self.assertEqual(exemplar["rendered_native_option_indices"], [0, 1])
        self.assertFalse(exemplar["selection_attempted"])
        self.assertRegex(exemplar["artifact_sha256"], SHA256_PATTERN)
        for observed in (53814264, 1079, 32904, 16837319, 174656):
            self.assertNotIn(str(observed), contract_repr)

    def test_default_registry_runtime_and_evidence_share_record(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY],
            VANILLA_TGP_MOVEMENT_ANALYSIS[EVENT_KEY],
        )
        self.assertIs(
            DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY],
            VANILLA_TGP_MOVEMENT_OBSERVATIONS[EVENT_KEY],
        )
        self.assertIs(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS[EVENT_KEY],
        )

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["selected_native_option_index"], 1)
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY)
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 2428)
        portable = query_vanilla_event_evidence_index_v1(EVENT_KEY)
        self.assertEqual(portable["status"], "available")
        self.assertEqual(
            {row["kind"] for row in portable["evidence"]},
            {"source_definition", "observation_artifact"},
        )
        json.dumps(response, allow_nan=False)

    def test_canonical_runtime_reload_rebinds_shared_record(self) -> None:
        script = (
            "import importlib,sys;"
            f"sys.path[:0]=[{str(ROOT / 'ck3_autonomous_player' / 'src')!r},"
            f"{str(ROOT / 'tools')!r}];"
            "import zg361_phase2_promotion_source_production_entry as entry;"
            "entry=importlib.reload(entry);"
            f"contract=entry.KNOWN_TIMELINE_INTERRUPTS[{EVENT_KEY!r}];"
            "assert contract['saved_scope_count']==11;"
            "assert contract['selected_option_number']==2;"
            "assert contract['selected_native_option_index']==1"
        )
        completed = subprocess.run(
            [sys.executable, "-c", script], cwd=ROOT, check=False,
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_r416_live_shape_passes_production_recovery_checks(self) -> None:
        contract = production._manager_recovery_contract(
            production.KNOWN_TIMELINE_INTERRUPTS[EVENT_KEY],
            player=32904,
            event_key=EVENT_KEY,
        )
        contract = production._timeline_contract_for_window(
            contract,
            starting_date=53804184,
            absolute_end_date=53958720,
        )
        character_ids = {
            "root_scope": 32904,
            "other_ruler": 16837319,
            "owner": 16837319,
            "author": 16837319,
            "skill_base": 16837319,
        }
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": EVENT_KEY,
            "current_event_instance_id": 1079,
            "date_raw": 53814264,
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
                _scope(name, character_ids.get(name)) for name in SCOPE_TYPES
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
            snapshot={"date_raw": 53814264, "active_event": {"option_count": 2}},
            event={"event_instance_id": 1079},
            context=context,
            event_key=EVENT_KEY,
            contract=contract,
        )

        self.assertTrue(all(checks.values()), checks)


if __name__ == "__main__":
    unittest.main()
