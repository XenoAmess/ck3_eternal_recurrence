from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer import strategy


def fixture_inputs():
    fixture = json.loads((PROJECT_ROOT / "tests/fixtures/faction_watch_current_673_674.json").read_text())
    snapshot = {**fixture["source"], "played_character": {"character_id": 29829}}
    return snapshot, fixture["faction_query_result"]


def query_row(result, *, auto=False):
    if auto:
        return {"command": "auto-turn", "ok": True, "result": {"auto_turn": {
            "selected_step": strategy.QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
            "result": result,
        }}}
    return {"command": strategy.QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
            "ok": True, "result": result}


class FactionAlertHistoryLookupV1Test(unittest.TestCase):
    def test_latest_history_precedes_snapshot_without_scanning_old_rows(self):
        snapshot, result = fixture_inputs()
        snapshot["player_faction_alerts"] = copy.deepcopy(result["player_faction_alerts"])
        snapshot["player_faction_alerts"]["targeting_factions"][0]["power"]["raw"] -= 1
        rows = [{"command": "life-advance", "ok": True}] * 8849 + [query_row(result, auto=True)]
        original = copy.deepcopy((rows, snapshot))
        with mock.patch.object(strategy, "_effective_command", wraps=strategy._effective_command) as unpack:
            alert = strategy._same_frame_player_faction_alerts(rows, snapshot)
        self.assertEqual(unpack.call_count, 1)
        self.assertEqual(alert["targeting_factions"][0]["power"]["raw"], 3304900)
        self.assertEqual((rows, snapshot), original)

    def test_stale_latest_envelope_does_not_hide_older_current_alert(self):
        snapshot, result = fixture_inputs()
        for key in ("queried_snapshot_id", "queried_revision", "queried_native_revision"):
            with self.subTest(key=key):
                stale = copy.deepcopy(result)
                stale[key] = "wrong" if key == "queried_snapshot_id" else 7
                alert = strategy._same_frame_player_faction_alerts(
                    [query_row(result), query_row(stale, auto=True)], snapshot)
                self.assertEqual(alert["snapshot_revision"], snapshot["native_revision"])

    def test_snapshot_fallback_remains_normalized_and_independent(self):
        snapshot, result = fixture_inputs()
        snapshot["player_faction_alerts"] = result["player_faction_alerts"]
        alert = strategy._same_frame_player_faction_alerts(
            [query_row({"player_faction_alerts": {}})], snapshot)
        self.assertIsNot(alert, snapshot["player_faction_alerts"])
        alert["targeting_factions"][0]["power"]["raw"] = 0
        self.assertEqual(snapshot["player_faction_alerts"]["targeting_factions"][0]["power"]["raw"], 3304900)


if __name__ == "__main__":
    unittest.main()
