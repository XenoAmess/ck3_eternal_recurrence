from __future__ import annotations

import json
from pathlib import Path
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
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.records_embedded_b import (  # noqa: E402
    EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import PLAYER_SENTINEL  # noqa: E402


EVENT_KEY = "ep3_story_cycle_admin_eunuch.8030"
PLAYER = 32_904
DATE_RAW = 53_366_664
EVENT_INSTANCE_ID = 621


def _scope(type_key: str, character_id: int | None = None) -> dict[str, object]:
    identity: dict[str, object]
    if character_id is None:
        identity = {"status": "unavailable", "reason": "not_identity_bearing"}
    else:
        identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "status": "available",
        "type_key": type_key,
        "typed_identity": identity,
    }


def _context(native_indices: tuple[int, ...] = (0, 1, 3)) -> dict[str, object]:
    scope_types = {
        "story": "story",
        "eunuch": "character",
        "emperor": "character",
        "admin_title": "landed_title",
        "student": "character",
        "rival": "character",
        "background_throne_room_scope": "character",
    }
    character_ids = {
        "eunuch": 31_801,
        "emperor": PLAYER,
        "student": 33_596_937,
        "rival": 16_834_604,
        "background_throne_room_scope": 31_440,
    }
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "current_event_instance_id": EVENT_INSTANCE_ID,
        "date_raw": DATE_RAW,
        "root_scope": _scope("character", PLAYER),
        "saved_scopes": [
            {
                "name": name,
                "scope": _scope(type_key, character_ids.get(name)),
            }
            for name, type_key in scope_types.items()
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
            for rendered, native in enumerate(native_indices)
        ],
    }


class Ep3AdminEunuchEventRecordTests(unittest.TestCase):
    def test_existing_contract_is_portable_and_admits_r588_variant(self) -> None:
        contract = EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS[EVENT_KEY]

        self.assertEqual(contract["root_character_id"], PLAYER_SENTINEL)
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["selected_option_number"], 4)
        self.assertEqual(contract["selected_native_option_index"], 3)
        self.assertIn(
            (0, 1, 3),
            tuple(
                variant["native_option_indices"]
                for variant in contract["option_variants"]
            ),
        )

    def test_r588_projection_passes_extended_consumer_and_drift_fails(self) -> None:
        contract = production._resolve_timeline_interrupt_contract(
            EVENT_KEY,
            player=PLAYER,
            starting_date=DATE_RAW,
            stop_at_clean_review_boundary=True,
        )
        self.assertIsNotNone(contract)

        def checks(context: dict[str, object]) -> dict[str, bool]:
            return production._known_interrupt_checks(
                snapshot={
                    "date_raw": DATE_RAW,
                    "active_event": {"option_count": 4},
                },
                event={"event_instance_id": EVENT_INSTANCE_ID},
                context=context,
                event_key=EVENT_KEY,
                contract=contract,
            )

        accepted = checks(_context())
        drifted = checks(_context((0, 1, 2)))
        self.assertTrue(all(accepted.values()), accepted)
        self.assertFalse(drifted["authored_options_exact"])

    def test_registry_analysis_and_r588_observation_are_queryable(self) -> None:
        self.assertIs(
            DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[EVENT_KEY],
            EMBEDDED_B_VANILLA_TIMELINE_CONTRACTS[EVENT_KEY],
        )
        analysis = DEFAULT_VANILLA_EVENT_ANALYSIS[EVENT_KEY]
        self.assertEqual(analysis["definition_lines"], "6282-6430")
        self.assertEqual(
            analysis["caller_lines"][
                "common/story_cycles/ep3_story_cycle_admin_eunuch.txt"
            ],
            "195-202",
        )
        self.assertIn("no payment", analysis["safe_option_rationale"])
        self.assertEqual(len(analysis["source_sha256"]), 3)

        observations = DEFAULT_VANILLA_EVENT_OBSERVATIONS[EVENT_KEY]["exemplars"]
        r588 = next(row for row in observations if row.get("run") == "R588")
        self.assertEqual(r588["rendered_native_option_indices"], [0, 1, 3])
        self.assertFalse(r588["selection_attempted"])

        response = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["contract"]["root_character_id"], "$player")
        json.dumps(response, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
