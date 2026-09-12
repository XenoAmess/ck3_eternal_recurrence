#!/usr/bin/env python3
"""Focused unit checks for the retained endgame-source recovery boundary."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zg361_phase2_endgame_source_retained_recovery import (
    _archive_failed_attempt,
    _retained_binding,
)


class RetainedEndgameSourceRecoveryTests(unittest.TestCase):
    def test_archives_failed_action_without_removing_original(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            action = root / "endgame-source-action.json"
            action.write_text('{"result":"RED"}\n', encoding="utf-8")
            records = _archive_failed_attempt(root, 1)
            archived = root / "endgame-source-action-red-attempt-01.json"
            self.assertEqual(len(records), 1)
            self.assertTrue(action.is_file())
            self.assertEqual(archived.read_bytes(), action.read_bytes())

    def test_accepts_exact_retained_owner_frame(self) -> None:
        binding = _retained_binding(
            {
                "paused": True,
                "map_ready": True,
                "date_raw": 53366568,
                "revision": 7,
                "snapshot_id": "snap",
                "played_character": {"character_id": 32904},
                "active_event": {"instance_id": 620},
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": 180184,
                    "connection_generation": 1,
                },
            },
            expected_pid=180184,
            expected_owner_character_id=32904,
            expected_date_raw=53366568,
        )
        self.assertEqual(binding["bridge_pid"], 180184)
        self.assertEqual(binding["event_instance_id"], 620)

    def test_rejects_a_different_pid(self) -> None:
        with self.assertRaises(RuntimeError):
            _retained_binding(
                {
                    "paused": True,
                    "map_ready": True,
                    "date_raw": 53366568,
                    "played_character": {"character_id": 32904},
                    "active_event": {"instance_id": 620},
                    "diagnostics": {
                        "connected": True,
                        "bridge_pid": 99,
                        "connection_generation": 1,
                    },
                },
                expected_pid=180184,
                expected_owner_character_id=32904,
                expected_date_raw=53366568,
            )


if __name__ == "__main__":
    unittest.main()
