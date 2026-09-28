"""No-game checks for the remaining E2 one-day replay guard."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import remaining_live_step as live


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


class RemainingLiveStepTest(unittest.TestCase):
    def test_snapshot_requires_exact_paused_actor_war_and_army(self) -> None:
        body = {"date_raw": 53146344, "paused": True, "revision": 4,
                "played_character": {"character_id": 29829},
                "active_wars": [{"war_id": 4,
                                 "allied_armies": [{"army_id": 18, "army_state": "combat"}]}]}
        self.assertTrue(live.snapshot_case(body, 53146344, require_combat=True)[0])
        for key, value in (("date_raw", 53146368), ("paused", False),
                           ("revision", None)):
            changed = dict(body, **{key: value})
            self.assertFalse(live.snapshot_case(changed, 53146344, require_combat=True)[0])
        changed = dict(body, active_wars=[])
        self.assertFalse(live.snapshot_case(changed, 53146344, require_combat=True)[0])

    def test_source_pair_and_binary_are_not_interchangeable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "interactive-requests").mkdir()
            (output / "interactive-requests-responses").mkdir()
            spec = live.TRACKS["e2-04-d05"]
            source = {"save": {"sha256": spec["save"]},
                      "receipt": {"sha256": spec["receipt"]},
                      "actor": live.ACTOR, "date_raw": spec["date"]}
            preflight = {"result": "READY_FOR_BOUNDED_LIVE_ATTEMPT",
                         "checkpoint_source": source,
                         "game": {"sha256": live.EXE_SHA},
                         "bridge_dll": {"sha256": spec["dll"]},
                         "bridge_injector": {"sha256": spec["injector"]}}
            write(output / "preflight.json", preflight)
            write(output / "native-start-readback.json",
                  {"postcondition_verified": True, "source_checkpoint": source})
            write(output / "command.json",
                  {"argv": ["capture_session.py", "--capture",
                            "--enable-private-phase-trace"]})
            self.assertEqual(live.bind_session(output, "e2-04-d05")["track"],
                             "e2-04-d05")
            with self.assertRaisesRegex(ValueError, "different source pair"):
                live.bind_session(output, "e2-05-d26")
            preflight["bridge_dll"]["sha256"] = live.JOIN_DLL
            write(output / "preflight.json", preflight)
            with self.assertRaisesRegex(ValueError, "bridge pair differs"):
                live.bind_session(output, "e2-04-d05")

    def test_private_request_uses_owner_action_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            requests = output / "interactive-requests"
            responses = output / "interactive-requests-responses"
            requests.mkdir()
            responses.mkdir()
            envelope = {"action": "private_phase_trace", "step": "begin",
                        "combat_id": live.COMBAT}

            def responder() -> None:
                target = requests / "sample.json"
                for _ in range(100):
                    if target.is_file():
                        request = json.loads(target.read_text(encoding="utf-8"))
                        self.assertEqual(request, envelope)
                        write(responses / "sample.json",
                              {"result": "CALL_COMPLETED", "body": {"accepted": True}})
                        return
                    time.sleep(0.01)
                raise AssertionError("private request was not submitted")

            thread = threading.Thread(target=responder)
            thread.start()
            try:
                body, receipt = live.private_call(output, "sample", envelope, 10)
                self.assertTrue(body["accepted"])
                self.assertEqual(receipt["result"], "CALL_COMPLETED")
                with self.assertRaisesRegex(ValueError, "already used"):
                    live.private_call(output, "sample", envelope, 10)
            finally:
                thread.join(timeout=2)

    def test_stale_revision_stops_before_first_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            steps = output / "operator-steps"
            steps.mkdir()
            binding = {"track": "e2-04-d05"}
            write(steps / "e2-04-d05-observe.json",
                  {"same_source_war_army_frame": True, "source_binding": binding,
                   "snapshot_values": {"revision": 4}})
            stale = {"date_raw": 53146344, "paused": True, "revision": 5,
                     "played_character": {"character_id": 29829},
                     "active_wars": [{"war_id": 4,
                                      "allied_armies": [{"army_id": 18,
                                                         "army_state": "combat"}]}]}
            calls = []

            def fake_call(_output, name, tool, _arguments, _timeout):
                calls.append((name, tool))
                return stale, {"response": {"sha256": "synthetic"}}

            with patch.object(live, "marked_running_recorder", return_value={}), \
                    patch.object(live, "call", side_effect=fake_call):
                with self.assertRaisesRegex(ValueError, "revision changed"):
                    live.advance(output, "e2-04-d05", binding, output / "recorder", 26018, 10)
            self.assertEqual(calls, [("e2-04-d05-pre-advance-snapshot", "ck3_take_snapshot")])
            self.assertFalse((steps / "e2-04-d05-advance-intent.json").exists())

    def test_finish_refuses_active_or_unprobed_recorder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            output = attempt / "ck3-output"
            output.mkdir()
            recorder = attempt / "recording-a01"
            recorder.mkdir()
            write(recorder / "recorder-start.json", {"pid": 123})
            with self.assertRaisesRegex(ValueError, "active recorder"):
                live.finish(output, "e2-06-d11", {}, recorder)
            write(recorder / "recorder-end.json", {"ffmpeg_exit_code": 0})
            with self.assertRaisesRegex(ValueError, "probe/final receipt"):
                live.finish(output, "e2-06-d11", {}, recorder)
            self.assertFalse((output / "interactive-requests").exists())


if __name__ == "__main__":
    unittest.main()
