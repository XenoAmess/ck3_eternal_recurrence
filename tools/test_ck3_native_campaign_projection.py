"""Exercise the real provider's native transport with ordinary succession."""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / "ck3_autonomous_player"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests/unit"))
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeCampaignProjectionTests(unittest.TestCase):
    def test_actual_native_frames_follow_successor_without_one_life_projection(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                               episode_projection="native_campaign")
        try:
            endpoint.publish(_hello("game.state.snapshot", "game.state.played-character",
                                    "game.command.pause-map", "game.command.resume-map"))
            for revision, character, alive in [(1, 707, True), (2, 707, False), (3, 808, True)]:
                endpoint.publish(_snapshot(revision, date_raw=77535240+24*revision,
                                           played_character={"character_id": character, "alive": alive}))
                observed = driver.take_snapshot()
                self.assertEqual(observed["played_character"]["character_id"], character)
                self.assertEqual(observed["date_raw"], 77535240+24*revision)
                self.assertEqual(observed["episode_projection"], "native_campaign")
                self.assertNotIn("one_life_terminal_reason", observed)
                self.assertNotIn("succession_lifecycle", observed)
                self.assertIsNone(driver._episode_character_id)
                self.assertIsNone(driver._episode_run_id)
                self.assertIsNone(driver._campaign_goal)
                self.assertIn("resume-map", driver.capabilities()["action_steps"])
        finally:
            driver.close()

    def test_default_projection_preserves_existing_one_life_contract(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
        try:
            endpoint.publish(_hello("game.state.snapshot", "game.state.played-character"))
            endpoint.publish(_snapshot(1, played_character={"character_id": 707, "alive": True}))
            self.assertEqual(driver.take_snapshot()["episode_character_id"], 707)
            endpoint.publish(_snapshot(2, played_character={"character_id": 808, "alive": True}))
            self.assertEqual(driver.take_snapshot()["one_life_terminal_reason"], "played_character_changed")
        finally:
            driver.close()

    def test_ordinary_event_selection_still_uses_existing_native_transport_after_successor(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                    episode_projection="native_campaign", command_timeout_seconds=0.2)
        try:
            endpoint.publish(_hello("game.state.snapshot", "game.state.played-character",
                                    "game.state.active-event", "game.command.select-event-option-N"))
            endpoint.publish(_snapshot(1, played_character={"character_id": 707, "alive": True}))
            driver.take_snapshot()
            endpoint.publish(_snapshot(2, active_event={"instance_id": 500, "option_count": 2},
                                       played_character={"character_id": 808, "alive": True}))
            before = driver.take_snapshot()
            def answer(frame):
                if frame.get("type") != "execute_step": return
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": frame["request_id"], "ok": True, "result": {"accepted": True}})
                endpoint.publish(_snapshot(3, active_event=None,
                                           played_character={"character_id": 808, "alive": True}))
            endpoint.send_hook = answer
            result = driver.execute_step("select-event-option-2", expected_revision=before["revision"])
            self.assertEqual(result["event_selection"]["old_event_instance_id"], 500)
            self.assertIsNone(driver.take_snapshot()["active_event"])
            self.assertIsNone(driver._episode_character_id)
        finally:
            driver.close()

    def test_native_campaign_rejects_invented_lifecycle_or_unknown_mode(self):
        for arguments in ({"episode_projection": "observer"},
                          {"episode_projection": "native_campaign", "succession_lifecycle_binding": {"xar_enabled": False}}):
            endpoint = FakeEndpoint()
            with self.assertRaises(ValueError):
                NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, **arguments)
            self.assertIsNone(endpoint.on_frame)

    def test_server_current_pause_uses_real_provider_submission_revision_once(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                    episode_projection="native_campaign", command_timeout_seconds=0.2)
        try:
            endpoint.publish(_hello("game.state.snapshot", "game.command.pause-map"))
            endpoint.publish(_snapshot(1, speed=5, paused=False))
            observed = driver.take_snapshot()
            endpoint.publish(_snapshot(2, speed=5, paused=False))
            def answer(frame):
                if frame.get("type") != "execute_step": return
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": frame["request_id"], "ok": True,
                                  "result": {"accepted": True, "status": "submitted"}})
                endpoint.publish(_snapshot(3, speed=5, paused=True))
            endpoint.send_hook = answer
            driver.execute_step("pause-map", expected_revision=None)
            submitted = [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]
            self.assertEqual(len(submitted), 1)
            self.assertEqual(submitted[0]["expected_revision"], 2)
            self.assertTrue(driver.take_snapshot()["paused"])
            self.assertLess(observed["revision"], driver.take_snapshot()["revision"])
        finally:
            driver.close()

    def test_campaign_checkpoint_metadata_does_not_change_native_save_request_or_bytes(self):
        for mode in ("native_campaign", "one_life"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                save_dir = Path(temporary) / "save games"
                save_dir.mkdir()
                checkpoint_path = save_dir / "xar_checkpoint.ck3"
                payload = b"native engine fixture bytes; rules remain engine-owned"
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                            episode_projection=mode, save_dir=save_dir, command_timeout_seconds=0.2,
                            checkpoint_timeout_seconds=0.2)
                try:
                    endpoint.publish(_hello("game.state.snapshot", "game.command.save-checkpoint"))
                    endpoint.publish(_snapshot(8, date_raw=77535240, paused=True))
                    before = driver.take_snapshot()
                    def answer(frame):
                        if frame.get("type") != "execute_step": return
                        checkpoint_path.write_bytes(payload)
                        endpoint.publish({"type": "command_result", "protocol_version": 1,
                                          "request_id": frame["request_id"], "ok": True,
                                          "result": {"step": "save-checkpoint", "accepted": True,
                                                     "status": "submitted", "submission": {
                                                         "date_raw": 77535240, "sequence": 1,
                                                         "requested_save_name": "xar_checkpoint"}}})
                    endpoint.send_hook = answer
                    result = driver.execute_step("save-checkpoint", expected_revision=before["revision"])
                    checkpoint = result["checkpoint"]
                    self.assertEqual(checkpoint_path.read_bytes(), payload)
                    self.assertEqual(checkpoint["sha256"], hashlib.sha256(payload).hexdigest())
                    requests = [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]
                    self.assertEqual(len(requests), 1)
                    self.assertEqual(requests[0]["step"], "save-checkpoint")
                    self.assertEqual(requests[0]["expected_revision"], 8)
                    self.assertNotIn("succession_lifecycle", requests[0])
                    self.assertNotIn("episode_projection", requests[0])
                    if mode == "native_campaign":
                        self.assertIsNone(checkpoint["succession_lifecycle"])
                        self.assertEqual(checkpoint["episode_projection"], "native_campaign")
                        self.assertIsNone(checkpoint["episode_character_id"])
                        self.assertIsNone(checkpoint["episode_run_id"])
                        self.assertIsNone(result["episode_seed"])
                    else:
                        self.assertEqual(checkpoint["succession_lifecycle"]["source"], "legacy-driver-default")
                        self.assertEqual(checkpoint["succession_lifecycle"]["xar_enabled"], "xar_on")
                        self.assertNotIn("episode_projection", checkpoint)
                finally:
                    driver.close()

    def test_campaign_checkpoint_without_directory_reports_unbound_lifecycle(self):
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                    episode_projection="native_campaign", command_timeout_seconds=0.2)
        try:
            endpoint.publish(_hello("game.state.snapshot", "game.command.save-checkpoint"))
            endpoint.publish(_snapshot(8, date_raw=77535240))
            def answer(frame):
                if frame.get("type") != "execute_step": return
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": frame["request_id"], "ok": True,
                                  "result": {"accepted": True, "status": "submitted",
                                             "submission": {"date_raw": 77535240}}})
            endpoint.send_hook = answer
            result = driver.execute_step("save-checkpoint")
            self.assertEqual(result["checkpoint"]["status"], "materialization_unavailable")
            self.assertIsNone(result["checkpoint"]["succession_lifecycle"])
            self.assertEqual(result["checkpoint"]["episode_projection"], "native_campaign")
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
