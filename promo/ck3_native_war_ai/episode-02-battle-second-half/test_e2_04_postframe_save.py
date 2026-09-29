"""No-game mismatch tests for one-shot E2-04 d06 checkpoint preservation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import e2_04_postframe_save as post
from pursuit_live_step import identity, write_new
from remaining_live_step import bind_session, snapshot_case


def snapshot(date: int, revision: int) -> dict:
    return {"date_raw": date, "paused": True, "revision": revision,
            "native_revision": revision - 1, "snapshot_id": f"native:{revision - 1}",
            "played_character": {"character_id": post.ACTOR},
            "active_wars": [{"war_id": post.WAR, "allied_armies": [
                {"army_id": post.PLAYER_ARMY, "army_state": "combat"}]}]}


def control(snap: dict) -> dict:
    return {"accepted": True, "status": "available",
            "snapshot_revision": snap["native_revision"],
            "queried_revision": snap["revision"],
            "queried_native_revision": snap["native_revision"],
            "queried_snapshot_id": snap["snapshot_id"],
            "source": {"revision": snap["revision"],
                       "native_revision": snap["native_revision"],
                       "snapshot_id": snap["snapshot_id"],
                       "date_raw": snap["date_raw"], "paused": True},
            "battle_control_snapshot": {
                "status": "available", "battle_control_ready": True,
                "snapshot_revision": snap["native_revision"],
                "observed_date_raw": snap["date_raw"],
                "subject_public_cunit_id": post.PLAYER_ARMY,
                "subject_native_carmy_id": post.PLAYER_ARMY,
                "selected_owner_character_id": post.ACTOR,
                "combat_id": post.COMBAT,
                "combat_province_id": post.PROVINCE}}


def save_response(path: Path, date: int, content: bytes) -> dict:
    return {"result": "CALL_COMPLETED", "body": {
        "step": "save-checkpoint", "accepted": True,
        "checkpoint": {"status": "saved", "path": str(path),
                       "name": "xar_checkpoint.ck3", "size": len(content),
                       "sha256": __import__("hashlib").sha256(content).hexdigest(),
                       "date_raw": date, "episode_character_id": post.ACTOR,
                       "succession_lifecycle": {
                           "lifecycle": "ordinary_campaign_succession",
                           "xar_enabled": "xar_off",
                           "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                           "source": "pure-vanilla-enabled-mods-empty"}}},
            "driver_state": {"hello": {"ck3_build_match": True,
                                       "expected_ck3_sha256": post.EXE_SHA}}}


class Fixture:
    def __init__(self, root: Path):
        self.root = root
        self.output = root / "ck3-output"
        self.output.mkdir()
        self.requests = self.output / "interactive-requests"
        self.responses = self.output / "interactive-requests-responses"
        self.steps = self.output / "operator-steps"
        for path in self.requests, self.responses, self.steps:
            path.mkdir()
        self.save_dir = root / "ck3-state" / "profile" / "save games"
        self.save_dir.mkdir(parents=True)
        self.save_path = self.save_dir / "xar_checkpoint.ck3"
        self.save_path.write_bytes(b"synthetic-d05-checkpoint")
        spec = post.TRACKS[post.TRACK]
        source = {"save": {"sha256": spec["save"]},
                  "receipt": {"sha256": spec["receipt"]},
                  "actor": post.ACTOR, "date_raw": spec["date"]}
        write_new(self.output / "preflight.json", {
            "result": "READY_FOR_BOUNDED_LIVE_ATTEMPT", "checkpoint_source": source,
            "game": {"sha256": post.EXE_SHA},
            "bridge_dll": {"sha256": spec["dll"]},
            "bridge_injector": {"sha256": spec["injector"]}})
        write_new(self.output / "native-start-readback.json",
                  {"postcondition_verified": True, "source_checkpoint": source})
        write_new(self.output / "command.json",
                  {"argv": ["capture_session.py", "--capture",
                            "--enable-private-phase-trace"]})
        self.binding = bind_session(self.output, post.TRACK)
        self.post = snapshot(post.POST_DATE, 8)
        self.saved_bytes = b"synthetic-d06-checkpoint"
        pre = self._response(post.PRE_SAVE_NAME, save_response(
            self.save_path, spec["date"], self.save_path.read_bytes()))
        after_save = self._response(f"{post.TRACK}-after-save-snapshot",
                                    {"result": "CALL_COMPLETED",
                                     "body": snapshot(spec["date"], 5)})
        begin = self._response(f"{post.TRACK}-trace-begin",
                               {"result": "CALL_COMPLETED",
                                "body": {"accepted": True, "combat_id": post.COMBAT,
                                         "managed_daily_sequence_token": 72907}},
                               {"action": "private_phase_trace", "combat_id": post.COMBAT,
                                "managed_daily_sequence_token": 72907,
                                "expected_revision": 5})
        day = self._response(f"{post.TRACK}-one-day",
                             {"result": "CALL_COMPLETED",
                              "body": {"ending_date_raw": post.POST_DATE,
                                       "revision": 8}},
                             {"action": "mcp", "tool": "ck3_execute_step",
                              "arguments": {"step": "life-advance",
                                            "expected_revision": 5}})
        trace = self._response(f"{post.TRACK}-trace-finish",
                               {"result": "CALL_COMPLETED",
                                "body": {"accepted": True, "combat_id": post.COMBAT,
                                         "managed_daily_sequence_token": 72907}},
                               {"action": "private_phase_trace", "combat_id": post.COMBAT,
                                "managed_daily_sequence_token": 72907,
                                "expected_revision": 8})
        snap = self._response(f"{post.TRACK}-post-snapshot",
                              {"result": "CALL_COMPLETED", "body": self.post})
        self.intent_path = self.steps / f"{post.TRACK}-advance-intent.json"
        write_new(self.intent_path, {"track": post.TRACK,
                                     "source_binding": self.binding,
                                     "at_most_one_day": True,
                                     "sequence_token": 72907})
        self.advance_path = self.steps / f"{post.TRACK}-advance.json"
        write_new(self.advance_path, {
            "mode": "advance", "track": post.TRACK,
            "result": "ONE_DAY_ADVANCED_UNREVIEWED",
            "source_binding": self.binding, "intent": identity(self.intent_path),
            "pre_save": pre, "after_save_snapshot": after_save,
            "trace_begin": begin, "one_day": day, "trace_finish": trace,
            "post_snapshot": snap,
            "post_values": snapshot_case(self.post, post.POST_DATE,
                                         require_combat=True)[1]})
        self.calls = []
        self.save_date = post.POST_DATE
        self.save_materializes = True
        self.pending_timeout = False
        self.current_control_combat = post.COMBAT
        self.after_control_combat = post.COMBAT

    def _response(self, name: str, payload: dict,
                  request_payload: dict | None = None) -> dict:
        request = self.requests / f"{name}.json"
        response = self.responses / f"{name}.json"
        write_new(request, request_payload or {"tool": name})
        write_new(response, payload)
        return {"request": identity(request), "response": identity(response),
                "result": "CALL_COMPLETED"}

    def call(self, output: Path, name: str, tool: str, arguments: dict,
             _timeout: float) -> tuple[dict, dict]:
        assert output == self.output
        self.calls.append((name, tool, arguments))
        if tool == "ck3_take_snapshot":
            body = snapshot(post.POST_DATE, 9) if name.endswith("after-save-snapshot") else self.post
            row = self._response(name, {"result": "CALL_COMPLETED", "body": body})
            return body, row
        if tool == "ck3_query_battle_control_snapshot_v1":
            snap = snapshot(post.POST_DATE, 9) if name.endswith("after-save-control") else self.post
            body = control(snap)
            if name.endswith("after-save-control"):
                body["battle_control_snapshot"]["combat_id"] = self.after_control_combat
            else:
                body["battle_control_snapshot"]["combat_id"] = self.current_control_combat
            row = self._response(name, {"result": "CALL_COMPLETED", "body": body})
            return body, row
        assert tool == "ck3_save_checkpoint"
        assert arguments == {"expected_revision": 8}
        if self.pending_timeout:
            write_new(self.requests / f"{name}.json",
                      {"tool": tool, "arguments": arguments})
            raise TimeoutError("synthetic pending request")
        if self.save_materializes:
            self.save_path.write_bytes(self.saved_bytes)
        payload = save_response(self.save_path, self.save_date, self.saved_bytes)
        row = self._response(name, payload)
        return payload["body"], row


class PostframeSaveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = Fixture(Path(self.temp.name))

    def execute(self) -> dict:
        with patch.object(post, "call", side_effect=self.fixture.call):
            return post.run(self.fixture.output, 10)

    def assert_no_save(self) -> None:
        self.assertFalse(any(tool == "ck3_save_checkpoint"
                             for _, tool, _ in self.fixture.calls))

    def test_success_preserves_both_exact_saves_and_real_response(self) -> None:
        fixture = self.fixture
        prior = fixture.save_path.read_bytes()
        result = self.execute()
        self.assertEqual(result["result"], "D06_PAIR_READY_FOR_SEPARATE_COLDLOAD_UNREVIEWED")
        self.assertEqual(sum(tool == "ck3_save_checkpoint"
                             for _, tool, _ in fixture.calls), 1)
        base = fixture.root / post.PRESERVATION_NAME
        self.assertEqual((base / "d05-preserved-before-post-save.ck3").read_bytes(), prior)
        self.assertEqual((base / "d06-immutable.ck3").read_bytes(), fixture.saved_bytes)
        self.assertEqual(result["d06_receipt"]["sha256"],
                         identity(fixture.responses / f"{post.SAVE_NAME}.json")["sha256"])
        self.assertFalse(result["trait_and_v3_result_known"])
        with self.assertRaisesRegex(ValueError, "already used"):
            self.execute()

    def test_source_or_token_mismatch_refuses_any_new_call(self) -> None:
        fixture = self.fixture
        original = json.loads(fixture.advance_path.read_text(encoding="utf-8"))
        for key, value in (("source_binding", {"wrong": True}),
                           ("result", "RED_PRESERVED")):
            changed = copy.deepcopy(original)
            changed[key] = value
            fixture.advance_path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "accepted one-day"):
                self.execute()
            self.assertEqual(fixture.calls, [])
        fixture.advance_path.write_text(json.dumps(original), encoding="utf-8")
        intent = json.loads(fixture.intent_path.read_text(encoding="utf-8"))
        intent["sequence_token"] = 0
        fixture.intent_path.write_text(json.dumps(intent), encoding="utf-8")
        updated = json.loads(fixture.advance_path.read_text(encoding="utf-8"))
        updated["intent"] = identity(fixture.intent_path)
        fixture.advance_path.write_text(json.dumps(updated), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sequence token"):
            self.execute()
        self.assertEqual(fixture.calls, [])

    def test_stale_current_frame_stops_before_copy_or_save(self) -> None:
        fixture = self.fixture
        stale = snapshot(post.POST_DATE, 10)
        def stale_call(output, name, tool, arguments, timeout):
            if tool == "ck3_take_snapshot":
                fixture.calls.append((name, tool, arguments))
                return stale, {"response": {"sha256": "synthetic"}}
            raise AssertionError("a stale frame must stop here")
        with patch.object(post, "call", side_effect=stale_call):
            with self.assertRaisesRegex(ValueError, "snapshot changed"):
                post.run(fixture.output, 10)
        self.assert_no_save()
        self.assertFalse((fixture.root / post.PRESERVATION_NAME).exists())

    def test_current_combat_mismatch_stops_before_save(self) -> None:
        fixture = self.fixture
        fixture.current_control_combat += 1
        with self.assertRaisesRegex(ValueError, "battle identity"):
            self.execute()
        self.assert_no_save()
        self.assertFalse((fixture.root / post.PRESERVATION_NAME).exists())

    def test_existing_intent_or_changed_d05_bytes_refuses_save(self) -> None:
        fixture = self.fixture
        post_intent = fixture.steps / f"{post.TRACK}-post-save-intent.json"
        write_new(post_intent, {"already": "attempted"})
        with self.assertRaisesRegex(ValueError, "already used"):
            self.execute()
        self.assertEqual(fixture.calls, [])
        post_intent.unlink()
        fixture.save_path.write_bytes(b"changed-d05")
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            self.execute()
        self.assert_no_save()

    def test_bad_native_date_or_missing_materialization_is_red_after_one_save(self) -> None:
        for date, materializes, expected in (
            (post.POST_DATE + 24, True, "actor/date/path"),
            (post.POST_DATE, False, "bytes differ"),
        ):
            with self.subTest(date=date, materializes=materializes):
                with tempfile.TemporaryDirectory() as root:
                    fixture = Fixture(Path(root))
                    fixture.save_date = date
                    fixture.save_materializes = materializes
                    with patch.object(post, "call", side_effect=fixture.call):
                        with self.assertRaisesRegex(ValueError, expected):
                            post.run(fixture.output, 10)
                    self.assertEqual(sum(tool == "ck3_save_checkpoint"
                                         for _, tool, _ in fixture.calls), 1)
                    self.assertTrue((fixture.steps /
                                     f"{post.TRACK}-post-save-intent.json").exists())
                    self.assertFalse((fixture.root / post.PRESERVATION_NAME /
                                      "postframe-save-result.json").exists())

    def test_pending_timeout_is_not_retryable(self) -> None:
        fixture = self.fixture
        fixture.pending_timeout = True
        with self.assertRaisesRegex(TimeoutError, "pending request"):
            self.execute()
        self.assertEqual(sum(tool == "ck3_save_checkpoint"
                             for _, tool, _ in fixture.calls), 1)
        with self.assertRaisesRegex(ValueError, "already used"):
            self.execute()
        self.assertEqual(sum(tool == "ck3_save_checkpoint"
                             for _, tool, _ in fixture.calls), 1)

    def test_post_save_combat_divergence_preserves_pair_but_withholds_ready(self) -> None:
        fixture = self.fixture
        fixture.after_control_combat += 1
        with self.assertRaisesRegex(ValueError, "post-save battle identity changed"):
            self.execute()
        base = fixture.root / post.PRESERVATION_NAME
        self.assertTrue((base / "d06-immutable.ck3").is_file())
        self.assertFalse((base / "postframe-save-result.json").exists())


if __name__ == "__main__":
    unittest.main()
