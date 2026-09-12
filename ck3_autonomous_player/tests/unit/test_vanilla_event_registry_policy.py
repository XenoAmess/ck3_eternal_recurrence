from __future__ import annotations

import copy
import unittest

from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)


PLAYER = 27_181
EVENT_KEY = "tgp_travel_events.0030"


def _scope(type_key: str, *, character_id: int | None = None) -> dict[str, object]:
    if character_id is not None:
        identity: dict[str, object] = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
        raw_type_index = 4
    else:
        identity = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
        raw_type_index = 3
    return {
        "status": "available",
        "raw_type_index": raw_type_index,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": identity,
    }


def _option(rendered: int, native: int) -> dict[str, object]:
    return {
        "rendered_index": rendered,
        "native_option_index": native,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
    }


def _context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": [
            {
                "name": "travel_plan",
                "name_identifier": 1,
                "scope": _scope("travel_plan"),
            },
            {
                "name": "poem_province",
                "name_identifier": 2,
                "scope": _scope("province"),
            },
        ],
        "options": [_option(0, 0), _option(1, 1)],
    }


def _recommend(context: dict[str, object]) -> dict[str, object]:
    return recommend_registered_vanilla_event_option_v1(
        context,
        played_character_id=PLAYER,
        snapshot_option_count=2,
    )


class VanillaEventRegistryPolicyTests(unittest.TestCase):
    def test_exact_tgp_travel_projection_selects_authored_option_two(
        self,
    ) -> None:
        result = _recommend(_context())

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 2)
        self.assertEqual(result["selected_native_option_index"], 1)
        self.assertEqual(result["selected_rendered_index"], 1)
        self.assertEqual(result["failed_checks"], [])
        self.assertFalse(result["semantic_optimal"])

    def test_unknown_event_leaves_existing_planner_fallback_available(
        self,
    ) -> None:
        context = _context()
        context["event_definition_key"] = "unregistered_event.1"

        result = _recommend(context)

        self.assertEqual(result["status"], "not_registered")
        self.assertEqual(
            result["unavailable_reason"],
            "event_definition_key_not_registered",
        )

    def test_registered_scope_drift_blocks_without_selecting(self) -> None:
        context = _context()
        saved_scopes = context["saved_scopes"]
        assert isinstance(saved_scopes, list)
        saved_scopes[1]["name"] = "wrong_province"

        result = _recommend(context)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("saved_scope_names_exact", result["failed_checks"])
        self.assertIsNone(result["selected_native_option_index"])

    def test_registered_selected_option_must_be_enabled(self) -> None:
        context = _context()
        options = context["options"]
        assert isinstance(options, list)
        options[1]["enabled"] = False

        result = _recommend(context)

        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "selected_native_option_enabled", result["failed_checks"]
        )
        self.assertIsNone(result["selected_option_number"])

    def test_registered_native_projection_drift_blocks(self) -> None:
        context = _context()
        options = context["options"]
        assert isinstance(options, list)
        drifted = copy.deepcopy(options)
        drifted[0]["native_option_index"] = 1
        drifted[1]["native_option_index"] = 0
        context["options"] = drifted

        result = _recommend(context)

        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "native_option_indices_exact", result["failed_checks"]
        )


if __name__ == "__main__":
    unittest.main()
