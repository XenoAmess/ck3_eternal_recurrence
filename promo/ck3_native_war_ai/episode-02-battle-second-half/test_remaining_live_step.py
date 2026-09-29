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
    @staticmethod
    def d11_snapshot(date: int, revision: int) -> dict:
        return {"date_raw": date, "paused": True, "revision": revision,
                "played_character": {"character_id": live.ACTOR},
                "active_wars": [{"war_id": live.WAR,
                                 "allied_armies": [{"army_id": live.PLAYER_ARMY,
                                                    "army_state": "combat"}]}]}

    @staticmethod
    def d11_control(date: int, revision: int, combat: int = live.COMBAT) -> dict:
        return {"accepted": True, "status": "available", "snapshot_revision": revision,
                "battle_control_snapshot": {
                    "status": "available", "battle_control_ready": True,
                    "snapshot_revision": revision, "observed_date_raw": date,
                    "subject_public_cunit_id": live.PLAYER_ARMY,
                    "subject_native_carmy_id": live.PLAYER_ARMY,
                    "selected_owner_character_id": live.ACTOR,
                    "combat_id": combat, "combat_province_id": live.PROVINCE}}

    def test_d11_requires_control_before_first_day_action(self) -> None:
        self.assertTrue(live.TRACKS["e2-06-d11"]["control"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            steps = output / "operator-steps"
            steps.mkdir()
            binding = {"track": "e2-06-d11"}
            write(steps / "e2-06-d11-observe.json",
                  {"same_source_war_army_frame": True, "source_binding": binding,
                   "subject_combat_membership_verified": False,
                   "snapshot_values": {"revision": 4}})
            with patch.object(live, "call") as native_call:
                with self.assertRaisesRegex(ValueError, "battle-control membership"):
                    live.advance(output, "e2-06-d11", binding, output / "recorder", 7, 10)
            native_call.assert_not_called()
            self.assertFalse((steps / "e2-06-d11-advance-intent.json").exists())

    def test_d11_duplicate_advance_rejects_before_any_new_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            steps = output / "operator-steps"
            steps.mkdir()
            binding = {"track": "e2-06-d11"}
            write(steps / "e2-06-d11-observe.json",
                  {"same_source_war_army_frame": True, "source_binding": binding,
                   "subject_combat_membership_verified": True,
                   "snapshot_values": {"revision": 4}})
            write(steps / "e2-06-d11-advance-intent.json", {"already": "committed"})
            with patch.object(live, "marked_running_recorder") as marker, \
                    patch.object(live, "call") as native_call:
                with self.assertRaisesRegex(ValueError, "already attempted"):
                    live.advance(output, "e2-06-d11", binding, output / "recorder", 7, 10)
            marker.assert_not_called()
            native_call.assert_not_called()

    def test_d11_observe_rejects_missing_native_control(self) -> None:
        date = live.TRACKS["e2-06-d11"]["date"]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "operator-steps").mkdir()
            calls = []

            def fake_call(_output, name, tool, _arguments, _timeout):
                calls.append(tool)
                body = (self.d11_snapshot(date, 4) if tool == "ck3_take_snapshot" else
                        {"accepted": True, "status": "available", "snapshot_revision": 4,
                         "battle_control_snapshot": None})
                return body, {"response": {"sha256": name}}

            with patch.object(live, "call", side_effect=fake_call):
                result = live.observe(output, "e2-06-d11", {}, 10)
            row = json.loads((output / "operator-steps" /
                              "e2-06-d11-observe.json").read_text(encoding="utf-8"))
            self.assertEqual(result, 2)
            self.assertEqual(calls, ["ck3_take_snapshot",
                                     "ck3_query_battle_control_snapshot_v1"])
            self.assertFalse(row["subject_combat_membership_verified"])
            self.assertIsNotNone(row["control"])

    def test_d11_post_control_is_bound_or_advanced_run_is_red(self) -> None:
        date = live.TRACKS["e2-06-d11"]["date"]
        for post_combat in (live.COMBAT, live.COMBAT + 1):
            with self.subTest(post_combat=post_combat), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                steps = output / "operator-steps"
                steps.mkdir()
                binding = {"track": "e2-06-d11"}
                write(steps / "e2-06-d11-observe.json",
                      {"same_source_war_army_frame": True, "source_binding": binding,
                       "subject_combat_membership_verified": True,
                       "snapshot_values": {"revision": 4}})
                replies = {
                    "e2-06-d11-pre-advance-snapshot": self.d11_snapshot(date, 4),
                    "e2-06-d11-before-save": {"accepted": True, "checkpoint":
                                                  {"status": "saved", "date_raw": date}},
                    "e2-06-d11-after-save-snapshot": self.d11_snapshot(date, 5),
                    "e2-06-d11-after-save-control": self.d11_control(date, 5),
                    "e2-06-d11-one-day": {"revision": 6, "ending_date_raw": date + 24},
                    "e2-06-d11-post-snapshot": self.d11_snapshot(date + 24, 6),
                    "e2-06-d11-post-control": self.d11_control(date + 24, 6, post_combat),
                }
                calls = []

                def fake_call(_output, name, tool, arguments, _timeout):
                    calls.append((name, tool, arguments))
                    return replies[name], {"response": {"sha256": name}}

                def fake_private(_output, name, _arguments, _timeout):
                    return {"accepted": True, "combat_id": live.COMBAT,
                            "managed_daily_sequence_token": 7}, {"response": {"sha256": name}}

                with patch.object(live, "marked_running_recorder", return_value={}), \
                        patch.object(live, "call", side_effect=fake_call), \
                        patch.object(live, "private_call", side_effect=fake_private):
                    result = live.advance(output, "e2-06-d11", binding,
                                          output / "recorder", 7, 10)
                row = json.loads((steps / "e2-06-d11-advance.json").read_text(encoding="utf-8"))
                self.assertEqual(result, 0 if post_combat == live.COMBAT else 2)
                self.assertEqual(row["result"], "ONE_DAY_ADVANCED_UNREVIEWED"
                                 if post_combat == live.COMBAT else "RED_PRESERVED")
                self.assertEqual(sum(tool == "ck3_execute_step" for _, tool, _ in calls), 1)
                self.assertEqual(row["post_control"]["response"]["sha256"],
                                 "e2-06-d11-post-control")
                self.assertEqual(calls[-1][2]["expected_revision"], 6)
                self.assertEqual(row["subject_combat_membership_verified"],
                                 post_combat == live.COMBAT)

    def test_d12_mark_binds_post_control_snapshot_and_sealed_journal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recorder = Path(directory)
            control_path = recorder / "control.json"
            report_path = recorder / "snapshot.json"
            screenshot_path = recorder / "frame.png"
            write(control_path, {"native": "control"})
            write(report_path, {"native": "snapshot"})
            screenshot_path.write_bytes(b"fixture-frame")
            control = live.identity(control_path)
            report = live.identity(report_path)
            screenshot = live.identity(screenshot_path)
            mark = {"kind": "d12-after", "date_raw": 53146512,
                    "war_id": live.WAR, "combat_id": live.COMBAT,
                    "monotonic_ns": 15, "control": control,
                    "report": report, "screenshot": screenshot}
            marks = recorder / "marks.jsonl"
            marks.write_text(json.dumps(mark) + "\n", encoding="utf-8")
            write(recorder / "recorder-start.json", {"monotonic_ns": 10})
            write(recorder / "recorder-end.json", {"monotonic_ns": 20})
            write(recorder / "recorder-final.json",
                  {"result": "ENCODED_UNREVIEWED", "marks": live.identity(marks)})
            advance = {"result": "ONE_DAY_ADVANCED_UNREVIEWED",
                       "post_control": {"response": control},
                       "post_snapshot": {"response": report}}
            self.assertEqual(live.post_mark_case(recorder, advance)["post_control"], control)
            with self.assertRaisesRegex(ValueError, "does not bind"):
                live.post_mark_case(recorder, {**advance, "post_control":
                                               {"response": {**control, "sha256": "0" * 64}}})
            with self.assertRaisesRegex(ValueError, "eligible"):
                live.post_mark_case(recorder, {**advance, "result": "RED_PRESERVED"})
            marks.write_text(json.dumps(mark) + "\n" + json.dumps(mark) + "\n",
                             encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "sealed marks bytes changed"):
                live.post_mark_case(recorder, advance)

    def test_d11_finish_preserves_missing_post_mark_red_and_requests_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            output = attempt / "ck3-output"
            output.mkdir()
            (output / "interactive-requests").mkdir()
            (output / "operator-steps").mkdir()
            recorder = attempt / "recording-d11"
            recorder.mkdir()
            write(recorder / "recorder-start.json", {"pid": 12})
            write(recorder / "recorder-end.json", {"monotonic_ns": 20})
            write(recorder / "recorder-final.json", {"result": "ENCODED_UNREVIEWED"})
            self.assertEqual(live.finish(output, "e2-06-d11", {}, recorder), 2)
            self.assertTrue((output / "interactive-requests" /
                             "999-e2-06-d11-finish.json").is_file())
            finish = json.loads((output / "operator-steps" /
                                 "e2-06-d11-finish.json").read_text(encoding="utf-8"))
            self.assertEqual(finish["result"], "RED_PRESERVED")
            self.assertIn("advance.json", finish["post_mark_error"])

    def test_battle_control_uses_nested_subject_and_exact_frame(self) -> None:
        snapshot = {"revision": 4, "native_revision": 3, "snapshot_id": "native:3"}
        body = {"accepted": True, "status": "available", "snapshot_revision": 3,
                "queried_revision": 4, "queried_native_revision": 3,
                "queried_snapshot_id": "native:3",
                "source": {"revision": 4, "native_revision": 3,
                           "snapshot_id": "native:3", "date_raw": 53146344,
                           "paused": True},
                "battle_control_snapshot": {
                    "status": "available", "battle_control_ready": True,
                    "snapshot_revision": 3, "observed_date_raw": 53146344,
                    "subject_public_cunit_id": 18, "subject_native_carmy_id": 18,
                    "selected_owner_character_id": 29829,
                    "combat_id": 16777218, "combat_province_id": 2633}}
        self.assertTrue(live.battle_control_case(body, snapshot, 53146344)[0])
        for key, value in (("snapshot_revision", 4),
                           ("observed_date_raw", 53146368),
                           ("subject_public_cunit_id", 22),
                           ("combat_id", 16777219)):
            changed = dict(body, battle_control_snapshot={
                **body["battle_control_snapshot"], key: value})
            self.assertFalse(live.battle_control_case(changed, snapshot, 53146344)[0])
        for key, value in (("snapshot_revision", 4), ("queried_revision", 5),
                           ("queried_native_revision", 4),
                           ("queried_snapshot_id", "native:4")):
            self.assertFalse(live.battle_control_case(
                dict(body, **{key: value}), snapshot, 53146344)[0])
        for key, value in (("revision", 5), ("native_revision", 4),
                           ("snapshot_id", "native:4"), ("date_raw", 53146368),
                           ("paused", False)):
            changed = dict(body, source={**body["source"], key: value})
            self.assertFalse(live.battle_control_case(changed, snapshot, 53146344)[0])
        self.assertFalse(live.battle_control_case(body, {**snapshot, "revision": 5}, 53146344)[0])

    def test_snapshot_requires_exact_paused_actor_war_and_army(self) -> None:
        body = {"date_raw": 53146344, "paused": True, "revision": 4,
                "native_revision": 3, "snapshot_id": "native:3",
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
                   "subject_combat_membership_verified": True,
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
