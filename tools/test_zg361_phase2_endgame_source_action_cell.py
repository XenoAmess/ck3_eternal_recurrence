from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import zg361_phase2_endgame_source_action_cell as action


class EndgameSourceActionTests(unittest.TestCase):
    def test_post_save_retry_restores_owner_before_source_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefix = root / "prefix.json"
            prefix.write_text("{}", encoding="utf-8")
            subject = {
                "paused": True,
                "map_ready": True,
                "date_raw": 1648,
                "revision": 18,
                "played_character": {"character_id": 31450},
                "active_event": None,
            }
            owner = {
                "paused": True,
                "map_ready": True,
                "date_raw": 1648,
                "revision": 19,
                "played_character": {"character_id": 32904},
                "active_event": {"instance_id": 620},
            }
            service = mock.Mock()
            service.snapshot.side_effect = [subject, owner]
            available = lambda value: {
                "status": "available",
                "value": value,
                "unavailable_reason": None,
            }
            service.query_zhongguo_workforce_collective_snapshot_v1.return_value = {
                "status": "available",
                "player_character_id": 31450,
                "subject_character_id": 31450,
                "requested_owner_character_id": 32904,
                "al_case": {
                    "owner_character_id": available(32904),
                    "subject_character_id": available(31450),
                    "cycle_serial": available(5),
                    "case_serial": available(1),
                    "state": available(1),
                    "active": available(True),
                },
            }
            service.set_player_character_v1.return_value = {
                "accepted": True,
                "status": "switched",
                "from_character_id": 31450,
                "to_character_id": 32904,
            }
            enter = mock.Mock(
                return_value={
                    "result": "GREEN",
                    "readiness": "paused-real-zg361we.356",
                    "pause_on_event_definition_key": "zg361we.356",
                    "pause_on_event_occurrence": 1,
                    "fixture_used": False,
                    "console_used": False,
                }
            )
            capture = mock.Mock(
                return_value={
                    "result": "GREEN",
                    "source_checkpoint_captured": True,
                    "registry": {"result": "GREEN"},
                }
            )
            result = action.run_endgame_source_capture(
                service,
                evidence_directory=root / "artifacts",
                prefix_manifest=prefix,
                expected_owner_character_id=32904,
                expected_date_raw=1648,
                runtime_capture_lineage={"seed_lineage_id": "seed"},
                request_nonce="R508.phase2-endgame-source",
                entry_runner=enter,
                capture_runner=capture,
            )
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(
                result["owner_restore"]["from_character_id"], 31450
            )
            service.set_player_character_v1.assert_called_once_with(
                32904, expected_revision=18
            )

    def test_bounded_entry_stops_on_first_source_then_assembles_registry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefix = root / "prefix.json"
            prefix.write_text("{}", encoding="utf-8")
            service = mock.Mock()
            service.snapshot.return_value = {
                "paused": True,
                "map_ready": True,
                "date_raw": 1000,
                "played_character": {"character_id": 32904},
            }

            def enter(_service, **kwargs):
                kwargs["evidence_out"].update(
                    result="GREEN",
                    readiness="paused-real-zg361we.356",
                    pause_on_event_definition_key="zg361we.356",
                    pause_on_event_occurrence=1,
                    fixture_used=False,
                    console_used=False,
                )
                return kwargs["evidence_out"]

            capture = mock.Mock(
                return_value={
                    "result": "GREEN",
                    "source_checkpoint_captured": True,
                    "registry": {"result": "GREEN"},
                }
            )
            result = action.run_endgame_source_capture(
                service,
                evidence_directory=root / "artifacts",
                prefix_manifest=prefix,
                expected_owner_character_id=32904,
                expected_date_raw=1648,
                runtime_capture_lineage={"seed_lineage_id": "seed"},
                request_nonce="R506.phase2-endgame-source",
                entry_runner=enter,
                capture_runner=capture,
            )
            self.assertEqual(result["result"], "GREEN")
            self.assertEqual(result["absolute_end_date_raw"], 1720)
            self.assertTrue(result["source_checkpoint_captured"])
            capture.assert_called_once()
            self.assertEqual(
                capture.call_args.kwargs["expected_date_raw"], 1648
            )

    def test_route_rejects_more_than_thirty_days(self):
        service = mock.Mock()
        with self.assertRaisesRegex(ValueError, "focused source bound"):
            action.run_endgame_source_capture(
                service,
                evidence_directory=Path("unused"),
                prefix_manifest=Path("unused.json"),
                expected_owner_character_id=32904,
                expected_date_raw=1,
                runtime_capture_lineage={},
                request_nonce="bounded",
                max_advance_days=31,
            )


if __name__ == "__main__":
    unittest.main()
