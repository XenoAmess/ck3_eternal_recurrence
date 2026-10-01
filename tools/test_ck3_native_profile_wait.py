"""Use the real provider to reproduce ACK-before-semantic-frame materialization."""
from pathlib import Path
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1] / "ck3_autonomous_player"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests/unit"))
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from test_ck3_native_profile_mcp import service_fixture
import ck3_native_profile_mcp as native
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class NativeProfileWaitTests(unittest.TestCase):
    def real_service(self, root, capabilities, *, paused=True, event=None, save=False):
        service, backend, _, _, _ = service_fixture(root)
        service.attach()
        endpoint = FakeEndpoint()
        save_dir = Path(service.profile["userdir"]) / "save games"
        if save: save_dir.mkdir()
        driver = NativeHeadlessGameplayDriver(service.pipe_name, endpoint=endpoint,
                    episode_projection="native_campaign", command_timeout_seconds=0.5,
                    save_dir=save_dir if save else None, checkpoint_timeout_seconds=0.5,
                    checkpoint_poll_interval_seconds=0.002)
        target = service.profile["guard"]["target"]
        hello = _hello("game.state.snapshot", *capabilities)
        hello.update(pid=target["pid"], game_adapter_status="ready",
                     expected_ck3_version=service.profile["game_version"],
                     expected_ck3_sha256=target["executable_sha256"])
        endpoint.publish(hello)
        endpoint.publish(_snapshot(8, date_raw=123456, speed=3, paused=paused, active_event=event))
        service.driver = driver
        service._gameplay = None
        service._postcondition_timeout_seconds = 0.5
        service._postcondition_poll_seconds = 0.002
        return service, backend, endpoint, driver, save_dir

    def test_resume_speed_and_current_pause_wait_for_delayed_real_provider_frame_once(self):
        for action, capability, initial_paused, final_paused, final_speed in (
                ("resume", "game.command.resume-map", True, False, 3),
                ("speed_5", "game.command.set-speed-5", True, True, 5),
                ("current_pause", "game.command.pause-map", False, True, 3)):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temporary:
                service, _, endpoint, driver, _ = self.real_service(
                    Path(temporary), [capability], paused=initial_paused)
                timer = None
                seen = []
                original_snapshot = service._snapshot
                def read():
                    value = original_snapshot()
                    seen.append((value["paused"], value["speed"]))
                    return value
                service._snapshot = read
                original_wait = service._wait_postcondition
                def delay_after_ack(result, before, verify):
                    nonlocal timer
                    # The command ACK has already returned from the real
                    # provider. Release the frame producer only after the
                    # production verifier actually observes its pending frame.
                    release, published = threading.Event(), threading.Event()
                    def publish():
                        if release.wait(0.5):
                            endpoint.publish(_snapshot(9, date_raw=123456,
                                paused=final_paused, speed=final_speed))
                            published.set()
                    timer = threading.Thread(target=publish)
                    timer.start()
                    def verify_pending(result, before, after):
                        try:
                            return verify(result, before, after)
                        except native._PostconditionPending:
                            release.set()
                            self.assertTrue(published.wait(0.5))
                            raise
                    return original_wait(result, before, verify_pending)
                service._wait_postcondition = delay_after_ack
                def answer(frame):
                    if frame.get("type") != "execute_step": return
                    endpoint.publish({"type": "command_result", "protocol_version": 1,
                                      "request_id": frame["request_id"], "ok": True,
                                      "result": {"step": frame["step"], "accepted": True,
                                                 "status": "submitted"}})
                endpoint.send_hook = answer
                try:
                    before = service._snapshot()
                    result = (service.pause_current() if action == "current_pause"
                              else service.simulation(action, before["revision"]))
                    self.assertEqual(result["status"], "native_gameplay_postcondition_verified")
                    self.assertEqual(result["snapshot_after"]["paused"], final_paused)
                    self.assertEqual(result["snapshot_after"]["speed"], final_speed)
                    requests = [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]
                    self.assertEqual(len(requests), 1)
                    self.assertGreaterEqual(len(seen), 4)
                    self.assertEqual(seen[-1], (final_paused, final_speed))
                finally:
                    if timer: timer.join()
                    driver.close()

    def test_event_selection_waits_for_real_delayed_event_instance_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, _, endpoint, driver, _ = self.real_service(Path(temporary),
                ["game.state.active-event", "game.command.select-event-option-N"],
                event={"instance_id": 500, "option_count": 2})
            timer = None
            def answer(frame):
                nonlocal timer
                if frame.get("type") != "execute_step": return
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": frame["request_id"], "ok": True,
                                  "result": {"accepted": True, "status": "submitted"}})
                timer = threading.Timer(0.03, lambda: endpoint.publish(_snapshot(
                    9, date_raw=123456, paused=True, active_event=None)))
                timer.start()
            endpoint.send_hook = answer
            try:
                before = service._snapshot()
                result = service.select_event(1, 500, before["revision"])
                self.assertEqual(result["status"], "native_gameplay_postcondition_verified")
                self.assertIsNone(result["snapshot_after"]["active_event"])
                self.assertEqual(len([f for f in endpoint.frames if f.get("type") == "execute_step"]), 1)
            finally:
                if timer: timer.join()
                driver.close()

    def test_checkpoint_uses_real_materialized_file_after_delayed_save_ack(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, _, endpoint, driver, save_dir = self.real_service(
                Path(temporary), ["game.command.save-checkpoint"], save=True)
            timer = None
            payload = b"delayed native engine save"
            def answer(frame):
                nonlocal timer
                if frame.get("type") != "execute_step": return
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": frame["request_id"], "ok": True,
                                  "result": {"accepted": True, "status": "submitted",
                                             "submission": {"date_raw": 123456}}})
                timer = threading.Timer(0.03, lambda: (save_dir / "xar_checkpoint.ck3").write_bytes(payload))
                timer.start()
            endpoint.send_hook = answer
            try:
                before = service._snapshot()
                result = service.checkpoint(before["revision"])
                self.assertEqual(result["status"], "native_gameplay_postcondition_verified")
                self.assertEqual(result["result"]["checkpoint"]["size"], len(payload))
                self.assertEqual((save_dir / "xar_checkpoint.ck3").read_bytes(), payload)
                self.assertEqual(len([f for f in endpoint.frames if f.get("type") == "execute_step"]), 1)
            finally:
                if timer: timer.join()
                driver.close()

    def test_new_crash_during_real_resume_postcondition_returns_red_without_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            service, _, endpoint, driver, _ = self.real_service(
                Path(temporary), ["game.command.resume-map"])
            def answer(frame):
                if frame.get("type") != "execute_step": return
                endpoint.publish({"type": "command_result", "protocol_version": 1,
                                  "request_id": frame["request_id"], "ok": True,
                                  "result": {"accepted": True, "status": "submitted"}})
                directory = Path(service.profile["userdir"]) / "crashes"
                directory.mkdir()
                (directory / "incomplete").mkdir()
            endpoint.send_hook = answer
            try:
                before = service._snapshot()
                result = service.simulation("resume", before["revision"])
                self.assertEqual(result["status"], "RED")
                self.assertIn("crash artifact", result["reason"])
                self.assertEqual(len([f for f in endpoint.frames if f.get("type") == "execute_step"]), 1)
            finally:
                driver.close()


if __name__ == "__main__":
    unittest.main()
