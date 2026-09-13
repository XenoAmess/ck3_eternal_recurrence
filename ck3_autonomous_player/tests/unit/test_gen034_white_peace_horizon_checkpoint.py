"""Focused checks for the bounded GEN-034 horizon checkpoint runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "unit"))
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_gen034_white_peace_horizon_checkpoint.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_gen034_white_peace_horizon_checkpoint", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

from ck3_autonomous_player.tests.unit.test_native_bridge_driver import (  # noqa: E402
    _termination_options,
)


WAR_ID = 33_554_473


class Gen034WhitePeaceHorizonCheckpointTests(unittest.TestCase):
    def test_admission_requires_duration_option_and_final_response(self) -> None:
        query = {
            "war_termination_options": _termination_options(
                WAR_ID,
                war_duration_days=365,
                white_peace_available=True,
            )
        }
        _, checks = HARNESS._white_peace_admission(query, war_id=WAR_ID)
        self.assertTrue(all(checks.values()))

        query["war_termination_options"]["war_duration_days"] = 364
        _, rejected = HARNESS._white_peace_admission(query, war_id=WAR_ID)
        self.assertFalse(rejected["war_duration_reached"])

    def test_history_accepts_only_the_declared_fixed_commands(self) -> None:
        prefix = [{"command": "old-read", "ok": True}]
        commands = [
            "resume-map",
            "pause-map",
            f"query-war-termination-options-{WAR_ID}",
            "save-checkpoint",
        ]
        after = [
            *prefix,
            *({"command": command, "ok": True} for command in commands),
        ]
        self.assertTrue(
            HARNESS._history_checks(
                {"native_command_history": prefix},
                {"native_command_history": after},
                expected_commands=commands,
            )["exact_command_delta"]
        )
        after.append({"command": "select-event-option-1", "ok": True})
        self.assertFalse(
            HARNESS._history_checks(
                {"native_command_history": prefix},
                {"native_command_history": after},
                expected_commands=commands,
            )["exact_command_delta"]
        )

    def test_compact_snapshot_preserves_event_and_war_identity(self) -> None:
        result = HARNESS._compact_snapshot(
            {
                "snapshot_id": "native:5",
                "revision": 6,
                "native_revision": 5,
                "date_raw": 53_192_616,
                "speed": 5,
                "paused": True,
                "episode_run_id": "episode",
                "played_character": {"character_id": 29_829},
                "active_event": None,
                "active_wars": [
                    {
                        "war_id": WAR_ID,
                        "player_side": "attacker",
                        "player_is_primary_war_leader": True,
                        "primary_opponent_character_id": 28_551,
                        "player_relative_war_score": 0,
                    }
                ],
            },
            war_id=WAR_ID,
        )
        self.assertEqual(result["character_id"], 29_829)
        self.assertEqual(result["war"]["war_id"], WAR_ID)
        self.assertIsNone(result["active_event"])

    def test_source_forbids_event_selection_and_termination_calls(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            '"ck3_query_current_event_window_context_v1"', source
        )
        self.assertIn('"event_encountered_before_horizon"', source)
        self.assertNotIn('"step": "select-event-option-', source)
        self.assertNotIn('"step": "surrender-war-', source)
        self.assertNotIn('"step": "offer-white-peace-', source)
        self.assertNotIn(
            'call_tool("ck3_query_war_termination_exit_terms_v2"', source
        )


if __name__ == "__main__":
    unittest.main()
