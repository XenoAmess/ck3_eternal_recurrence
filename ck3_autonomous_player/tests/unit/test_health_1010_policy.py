from __future__ import annotations

from pathlib import Path
import sys
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)


PLAYER_ID = 29_829


def _scope(type_key: str, character_id: int | None = None) -> dict[str, object]:
    identity = (
        {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
        if character_id is not None
        else {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    )
    return {
        "status": "available",
        "raw_type_index": 4 if character_id is not None else 1,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": identity,
    }


def _saved(name: str, type_key: str, character_id: int | None = None) -> dict[str, object]:
    return {
        "name": name,
        "name_identifier": len(name) + 100,
        "scope": _scope(type_key, character_id),
    }


def _option(rendered: int, native: int) -> dict[str, object]:
    return {
        "rendered_index": rendered,
        "native_option_index": native,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
        "resolved_name": f"health.1010 option {native}",
        "unavailable_reason": "",
        "effect_indicators": {
            "status": "available",
            "coverage": "played-character-event-icon-indicators-1.19.0.6-v1",
            "complete_effect_set": False,
            "rows": [],
        },
        "effect_preview": {
            "status": "unavailable",
            "reason": "indicator_subset_has_no_completeness_signal",
        },
        "resource_deltas": {"status": "unavailable"},
        "relationship_deltas": {"status": "unavailable"},
    }


def _context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 1,
        "date_raw": 53_200_000,
        "current_event_instance_id": 4,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "health.1010",
        "calculated_event_id": 5_051_010,
        "runtime_stats_ordinal": 40,
        "root_scope": _scope("character", PLAYER_ID),
        "saved_scopes": [
            _saved("epidemic", "epidemic"),
            _saved("disease_type", "flag"),
            _saved("sick_character", "character", PLAYER_ID),
            _saved("new_memory", "character_memory"),
        ],
        "options": [_option(0, 0), _option(1, 6)],
        "readiness": {
            "event_definition_identity_ready": True,
            "root_scope_ready": True,
            "saved_scopes_ready": True,
            "option_presentation_ready": True,
            "effect_indicators_ready": True,
            "effect_preview_ready": False,
            "semantic_decision_ready": False,
        },
        "provenance": {},
    }


class Health1010PolicyTests(unittest.TestCase):
    def test_r14_no_physician_projection_calls_for_physician(self) -> None:
        result = recommend_registered_vanilla_event_option_v1(
            _context(),
            played_character_id=PLAYER_ID,
            snapshot_option_count=7,
        )

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 1)
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertEqual(result["matched_option_variant_index"], 0)
        self.assertEqual(result["failed_checks"], [])

    def test_patient_identity_drift_stays_blocked(self) -> None:
        context = _context()
        context["saved_scopes"][2] = _saved(
            "sick_character", "character", PLAYER_ID + 1
        )

        result = recommend_registered_vanilla_event_option_v1(
            context,
            played_character_id=PLAYER_ID,
            snapshot_option_count=7,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "scope:sick_character:character_id", result["failed_checks"]
        )


if __name__ == "__main__":
    unittest.main()
