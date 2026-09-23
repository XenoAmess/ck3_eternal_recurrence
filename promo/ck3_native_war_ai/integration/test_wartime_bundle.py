"""Offline synthetic contract checks; never create a GREEN capture or run CK3/media."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo import wartime_bundle as wb
from war_ai_promo import gameplay_bundle as gb
from war_ai_promo.common import binding, load, write_new

OUTPUT = None


def native_snapshot(date=24):
    return {"source": "injected-dll-named-pipe", "map_ready": True, "paused": True, "date_raw": date,
        "played_character": {"character_id": 42}, "episode_character_id": 42,
        "episode_run_id": "synthetic-offline-episode", "episode_identity_pending": False,
        "revision": 1, "native_revision": 1, "snapshot_id": "native:1",
        "succession_lifecycle": {"xar_enabled": "xar_off", "source": "pure-vanilla-enabled-mods-empty",
            "environment_sha256": "synthetic-environment"},
        "diagnostics": {"bridge_pid": 999, "connection_generation": 1, "pipe_name": "synthetic-unused-pipe",
            "hello": {"ck3_build_match": True, "expected_ck3_version": "1.19.0.6",
                "expected_ck3_sha256": wb.EXE_SHA256, "pid": 999, "connection_generation": 1, "session_generation": 0}},
        "active_wars": [], "player_armies": [], "native_command_history": []}


class WartimeBundleTests(unittest.TestCase):
    def setUp(self):
        self.root = OUTPUT / self._testMethodName
        self.root.mkdir()

    def fixture(self):
        session, case, recording = (self.root / name for name in ("session", "case", "recording"))
        for directory in (session, case, recording, session / "recovery-requests", session / "recovery-requests-responses"):
            directory.mkdir(exist_ok=True)
        write_new(session / "live-run-identity.json", {"schema": "xar.ck3-live-run-receipt.v1", "identities": [
            {"mod_key": "vanilla", "run_id": "synthetic-not-a-live-run"}]})
        write_new(session / "preflight.json", {"pipe_name": "synthetic-unused-pipe", "game": {"sha256": wb.EXE_SHA256}})
        write_new(session / "command.json", {"argv": ["--output-dir", str(session), "--pipe-name", "synthetic-unused-pipe"]})
        (session / "session.jsonl").write_bytes((json.dumps({"type": "native_session_ready", "pid": 999,
            "pipe": "synthetic-unused-pipe"}) + "\n").encode())
        write_new(recording / "recording-command.json", {"monotonic_origin": 100})
        raw = recording / "synthetic.bin"
        raw.write_bytes(b"synthetic test fixture; not media or a CK3 recording")
        initial = native_snapshot()
        state = {"root": recording, "state": initial, "actor": 42, "date_raw": 24, "raw": binding(raw),
            "recording_started_at": "2026-09-23T00:00:00+00:00",
            "recording_completed_at": "2026-09-23T00:01:00+00:00", "duration_seconds": 60}
        write_new(recording / "snapshot-before.json", {"at": "2026-09-23T00:00:00+00:00", "body": initial})

        def call(number, tool, arguments, body, second):
            name = f"w{number:03d}-call.json"
            req, resp = session / "recovery-requests" / name, session / "recovery-requests-responses" / name
            write_new(req, {"action": "mcp", "tool": tool, "arguments": arguments})
            at = f"2026-09-23T00:00:{second:02d}+00:00"
            write_new(resp, {"request": binding(req), "at": at, "result": "CALL_COMPLETED", "body": body,
                "driver_state": deepcopy(initial["diagnostics"])})
            write_new(case / (name + ".submitted.json"), {"at": at, "monotonic": 100 + second,
                "tool": tool, "arguments": arguments, "request": str(req)})
            write_new(case / (name + ".received.json"), {"at": at, "monotonic": 100 + second,
                "response": binding(resp)})
            return resp

        before = deepcopy(initial)
        war = {"war_id": 4, "primary_opponent_character_id": 55}
        after_declare = deepcopy(before)
        after_declare["active_wars"] = [war]
        declare_body = {"accepted": True, "status": "submitted", "war_action": {
            "status": "war_started", "declaration_id": "55-40--1", "target_character_id": 55}}
        owned = {"army_id": 18, "owner_character_id": 42, "move_target_province_id": None, "route_province_ids": []}
        after_raise = deepcopy(after_declare)
        after_raise["player_armies"] = [owned]
        raise_body = {"accepted": True, "status": "submitted", "war_action": {"status": "raised", "raised_army_ids": [18]}}
        after_move = deepcopy(after_raise)
        after_move["player_armies"][0].update(move_target_province_id=100, route_province_ids=[90, 100])
        move_body = {"accepted": True, "status": "submitted", "war_action": {"status": "moving", "army_id": 18}}
        entries = [("declaration", before, after_declare, declare_body, {"declaration_id": "55-40--1", "expected_revision": 1}),
            ("raise", after_declare, after_raise, raise_body, {"expected_revision": 1}),
            ("move", after_raise, after_move, move_body, {"expected_revision": 1, "army_id": 18, "target_province_id": 100})]
        for i, (kind, pre, post, body, arguments) in enumerate(entries, 1):
            write_new(case / f"{kind}-intent.json", {"at": f"2026-09-23T00:00:{i*5:02d}+00:00",
                "monotonic": 100 + i*5, "precondition": pre, "label": "synthetic operator action"})
            write_new(case / f"{kind}-result.json", {"response": body, "snapshot": post})
            call(i, wb.ACTION_TOOLS[kind], arguments, body, i*5)
        final = deepcopy(after_move)
        final["date_raw"] = 72
        final["native_command_history"] = [{"index": i, "command": command} for i, command in enumerate(
            ("declare-war-55-40--1", "raise-troops-default", "move-army-18-to-100"), 1)]
        write_new(case / "advance-01.json", {"at": "2026-09-23T00:00:40+00:00", "requested_days": 2,
            "start": after_move, "end": final, "observations": [{"date_raw": 24, "paused": False}, {"date_raw": 48, "paused": False}]})
        self.unavailable_response = call(4, "ck3_query_battle_reinforcement_assignment_v1", {},
            {"accepted": True, "status": "unavailable", "battle_reinforcement_assignment_ready": False,
                "unavailable_reason": "synthetic-narrow-field-conflict"}, 50)
        endpoint = self.root / "actual-shape-synthetic-endpoint.json"
        write_new(endpoint, {"result": "CALL_COMPLETED", "at": "2026-09-23T00:01:02+00:00", "body": final})
        return state, case, session, endpoint

    def validate(self, fixture):
        return wb.validate_wartime_case(*fixture)

    def test_dynamic_dates_three_explicit_actions_and_unavailable_query_are_preserved(self):
        fixture = self.fixture()
        result = self.validate(fixture)
        self.assertEqual(result["end_date_raw"] - result["start_date_raw"], 48)
        self.assertEqual([row["kind"] for row in result["actions"]], ["declaration", "raise", "move"])
        self.assertEqual(result["calls"][-1]["native_status"], "unavailable")
        self.assertTrue(all(row["exact_media_pts"] is None for row in result["actions"]))
        self.assertFalse(wb.BOUNDARIES["narrow_query_ready_conflicts_resolved"])
        self.assertEqual(len(result["advances"]), 1)
        self.assertFalse(any(self.root.rglob("report.json")))

    def test_initial_recorder_projection_does_not_change_old_paused_reader(self):
        fixture = self.fixture()
        path = fixture[0]["root"] / "snapshot-before.json"
        self.assertEqual(wb._initial_snapshot(path, 42, 24)["date_raw"], 24)
        with self.assertRaisesRegex(gb.GameplayBundleError, "incomplete"):
            gb._snapshot(path, 42, 24)
        with patch.object(gb, "extract_frames", return_value={"pending": True}) as extract:
            wb.extract_wartime_frames("recording", "new", 0, 1)
            self.assertIs(extract.call_args.kwargs["recording_validator"], wb.completed_wartime_recording)

    def test_wrong_episode_or_same_date_cannot_be_dynamic_observation(self):
        fixture = self.fixture()
        path = fixture[-1]
        original = load(path)
        for field, value, error in (("episode_run_id", "other-episode", "changed"), ("date_raw", 24, "increased")):
            changed = deepcopy(original)
            changed["body"][field] = value
            candidate = self.root / f"bad-{field}.json"
            write_new(candidate, changed)
            with self.assertRaisesRegex(gb.GameplayBundleError, error):
                self.validate((*fixture[:-1], candidate))

    def test_accepted_ack_without_matching_route_is_not_success(self):
        fixture = self.fixture()
        path = fixture[1] / "move-result.json"
        value = load(path)
        value["snapshot"]["player_armies"][0]["route_province_ids"] = []
        path.write_bytes((json.dumps(value) + "\n").encode())
        with self.assertRaisesRegex(gb.GameplayBundleError, "committed route"):
            self.validate(fixture)

    def test_request_mutation_and_hidden_extra_operator_order_are_rejected(self):
        fixture = self.fixture()
        path = fixture[-1]
        value = load(path)
        value["body"]["native_command_history"].append({"index": 9, "command": "move-army-18-to-101"})
        candidate = self.root / "extra-move.json"
        write_new(candidate, value)
        with self.assertRaisesRegex(gb.GameplayBundleError, "exactly one"):
            self.validate((*fixture[:-1], candidate))
        req = next((fixture[2] / "recovery-requests").glob("*.json"))
        req.write_bytes(b"synthetic mutated request")
        with self.assertRaisesRegex(gb.GameplayBundleError, "SHA mismatch"):
            self.validate(fixture)

    def test_review_cannot_claim_signoff_or_narrow_conflict_resolution(self):
        for field in ("signoff_granted", "narrow_query_ready_conflicts_resolved"):
            path = self.root / f"false-claim-{field}.json"
            write_new(path, {"schema": wb.REVIEW_SCHEMA, "reviewer": {"kind": "agent", "id": "synthetic"},
                "review_scope": "endpoint-images-and-sampled-foreground", **wb.BOUNDARIES, field: True})
            with self.assertRaisesRegex(gb.GameplayBundleError, "boundaries"):
                wb._review(path, {})

    def test_package_refuses_existing_destination_and_missing_implementation(self):
        target = self.root / "existing-attempt"
        target.mkdir()
        sentinel = target / "retained.bin"
        sentinel.write_bytes(b"old failed attempt must remain unchanged")
        with patch.object(wb, "completed_wartime_recording", return_value={}), \
                patch.object(wb, "validate_wartime_case", return_value={}), \
                patch.object(wb, "_review", return_value=({}, {})):
            args = (self.root / "recording", self.root / "case", self.root / "session",
                    self.root / "after.json", self.root / "review.json")
            with self.assertRaisesRegex(gb.GameplayBundleError, "destination exists"):
                wb.package_wartime_bundle(*args, target, __file__, __file__)
            with self.assertRaisesRegex(gb.GameplayBundleError, "implementation files"):
                wb.package_wartime_bundle(*args, self.root / "new-attempt", "missing-recorder.py", __file__)
        self.assertEqual(sentinel.read_bytes(), b"old failed attempt must remain unchanged")
        self.assertFalse((self.root / "new-attempt").exists())


def main():
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    OUTPUT = args.output.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    capture = io.StringIO()
    result = unittest.TextTestRunner(stream=capture, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(WartimeBundleTests))
    log = OUTPUT / "unittest.txt"
    log.write_bytes(capture.getvalue().encode("utf-8"))
    write_new(OUTPUT / "verification-index.json", {"status": "PASS" if result.wasSuccessful() else "FAIL",
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "tests": result.testsRun,
        "scope": "synthetic offline native evidence contract and explicit dynamic extraction dispatch",
        "ck3_launched": False, "media_process_executed": False, "green_capture_bundle_created": False,
        "human_review_or_approval_created": False, "implementation": binding(wb.__file__),
        "tests_source": binding(__file__), "test_log": binding(log)})
    print(capture.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
