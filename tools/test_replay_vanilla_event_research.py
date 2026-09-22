"""Offline adapter tests using the existing tgp-travel fixture shape."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import replay_vanilla_event_research as replay


def _scope(type_key: str, character_id: int | None = None) -> dict:
    return {
        "status": "available",
        "raw_type_index": 4 if character_id else 3,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": (
            {"status": "available", "kind": "character", "character_id": character_id}
            if character_id else
            {"status": "unavailable", "reason": "generic_scope_payload_identity_not_closed"}
        ),
    }


def _bundle() -> dict:
    # Synthetic data matching test_vanilla_event_registry_policy._context;
    # this test is never a historical or live-game evidence claim.
    return {
        "ck3_build": replay.registry.EXACT_CK3_BUILD,
        "ck3_exe_sha256": replay.registry.EXACT_CK3_EXE_SHA256,
        "played_character_id": 27181,
        "snapshot_option_count": 2,
        "context": {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "tgp_travel_events.0030",
            "root_scope": _scope("character", 27181),
            "saved_scopes": [
                {"name": "travel_plan", "name_identifier": 1, "scope": _scope("travel_plan")},
                {"name": "poem_province", "name_identifier": 2, "scope": _scope("province")},
            ],
            "options": [
                {"rendered_index": index, "native_option_index": index,
                 "shown": True, "enabled": True, "fallback": False, "cancel": False}
                for index in (0, 1)
            ],
        },
    }


def _with_receipt() -> dict:
    value = _bundle()
    value["snapshot"] = {
        "snapshot_id": "native:19", "revision": 33,
        "played_character": {"character_id": 27181, "stress_points": 42},
    }
    value["event_selection"] = {
        "postcondition_verified": True,
        "starting_snapshot_id": "native:19", "starting_revision": 33,
        "starting_played_character_stress": {"status": "available", "character_id": 27181, "stress_points": 42},
        "ending_played_character_stress": {"status": "available", "character_id": 27181, "stress_points": 27},
    }
    return value


def _bytes(value: dict) -> bytes:
    return json.dumps(value).encode("utf-8")


class EventResearchReplayTests(unittest.TestCase):
    def test_policy_without_snapshot_and_exact_input_hash(self) -> None:
        value = _bundle()
        original = copy.deepcopy(value)
        data = b"\xef\xbb\xbf" + _bytes(value) + b"\n"
        report = replay.replay_bytes(data)
        self.assertEqual(value, original)
        self.assertEqual(report["policy"]["status"], "recommended")
        self.assertEqual(report["policy"]["selected_native_option_index"], 1)
        self.assertEqual(report["material_plan"]["reason"], "snapshot_not_supplied")
        self.assertEqual(report["input"]["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(report["execution_mode"], "offline-replay")
        self.assertFalse(report["new_live_evidence"])

    def test_production_three_stage_replay_has_no_process_side_effects(self) -> None:
        with mock.patch.object(replay.policy, "recommend_registered_vanilla_event_option_v1", wraps=replay.policy.recommend_registered_vanilla_event_option_v1) as policy_call, mock.patch.object(replay.outcome, "plan_registered_event_material_postcondition_v1", wraps=replay.outcome.plan_registered_event_material_postcondition_v1) as plan_call, mock.patch.object(replay.outcome, "evaluate_registered_event_material_postcondition_v1", wraps=replay.outcome.evaluate_registered_event_material_postcondition_v1) as evaluate_call, mock.patch("subprocess.Popen", side_effect=AssertionError("process launch forbidden")), mock.patch("socket.socket", side_effect=AssertionError("network forbidden")):
            report = replay.replay_bytes(_bytes(_with_receipt()))
        policy_call.assert_called_once()
        plan_call.assert_called_once()
        evaluate_call.assert_called_once()
        self.assertEqual(report["material_evaluation"]["status"], "verified_change")
        self.assertEqual(report["material_evaluation"]["delta"], -15)
        self.assertFalse(report["game_started"])
        self.assertEqual(report["gameplay_commands_submitted"], 0)

    def test_missing_material_value_is_not_assumed_zero(self) -> None:
        value = _with_receipt()
        del value["snapshot"]["played_character"]["stress_points"]
        report = replay.replay_bytes(_bytes(value))
        self.assertEqual(report["material_plan"]["status"], "not_evaluated")
        self.assertEqual(report["material_plan"]["production_result"]["status"], "unavailable")
        self.assertIsNone(report["material_plan"]["production_result"]["starting_value"])
        self.assertEqual(report["material_evaluation"]["status"], "not_evaluated")

    def test_registered_policy_without_supported_material_outcome(self) -> None:
        value = _with_receipt()
        value["snapshot_option_count"] = 3
        value["context"].update(
            event_definition_key="epidemic_events.0110",
            saved_scopes=[{"name": "epidemic", "name_identifier": 264, "scope": _scope("epidemic")}],
            options=[
                {"rendered_index": rendered, "native_option_index": native,
                 "shown": True, "enabled": True, "fallback": False, "cancel": False}
                for rendered, native in enumerate((1, 2))
            ],
        )
        report = replay.replay_bytes(_bytes(value))
        self.assertEqual(report["policy"]["status"], "recommended")
        self.assertEqual(report["material_plan"]["reason"], "material_postcondition_not_supported")

    def test_missing_revision_is_not_invented(self) -> None:
        value = _with_receipt()
        del value["snapshot"]["revision"]
        report = replay.replay_bytes(_bytes(value))
        self.assertEqual(report["material_plan"]["missing_fields"], ["revision"])
        self.assertEqual(report["material_evaluation"]["status"], "not_evaluated")

    def test_no_receipt_and_failed_receipt_remain_distinct(self) -> None:
        value = _with_receipt()
        del value["event_selection"]
        report = replay.replay_bytes(_bytes(value))
        self.assertEqual(report["material_plan"]["status"], "ready")
        self.assertEqual(report["material_evaluation"]["reason"], "event_selection_not_supplied")
        value = _with_receipt()
        value["event_selection"]["starting_revision"] = 999
        report = replay.replay_bytes(_bytes(value))
        self.assertEqual(report["material_evaluation"]["status"], "failed")

    def test_unregistered_and_blocked_policy_do_not_evaluate_outcome(self) -> None:
        for event_key, enabled, expected in (("not_registered.9999", True, "not_registered"), ("tgp_travel_events.0030", False, "blocked")):
            with self.subTest(expected=expected):
                value = _with_receipt()
                value["context"]["event_definition_key"] = event_key
                value["context"]["options"][1]["enabled"] = enabled
                report = replay.replay_bytes(_bytes(value))
                self.assertEqual(report["policy"]["status"], expected)
                self.assertEqual(report["material_plan"]["status"], "not_evaluated")

    def test_versions_must_be_declared_and_consistent(self) -> None:
        for field in ("ck3_build", "ck3_exe_sha256"):
            with self.subTest(field=field):
                value = _bundle()
                del value[field]
                with self.assertRaises(replay.ReplayInputError):
                    replay.replay_bytes(_bytes(value))
                value = _bundle()
                value["context"][field] = "wrong-version"
                with self.assertRaises(replay.ReplayInputError):
                    replay.replay_bytes(_bytes(value))
        value = _bundle()
        value["context"]["ck3_build"] = value.pop("ck3_build")
        value["context"]["ck3_exe_sha256"] = value.pop("ck3_exe_sha256").lower()
        self.assertEqual(replay.replay_bytes(_bytes(value))["policy"]["status"], "recommended")

    def test_cross_frame_or_player_input_is_rejected(self) -> None:
        for mutate in (
            lambda value: value["snapshot"]["played_character"].update(character_id=27182),
            lambda value: (value["context"].update(snapshot_revision=19), value["snapshot"].update(native_revision=20)),
            lambda value: value["event_selection"].update(event_definition_key="other.1"),
        ):
            value = _with_receipt()
            mutate(value)
            with self.assertRaises(replay.ReplayInputError):
                replay.replay_bytes(_bytes(value))

    def test_invalid_or_ambiguous_json_is_rejected(self) -> None:
        for data in (b"[]", b'{"context":{},"context":{}}', b'{"context":NaN}'):
            with self.assertRaises(replay.ReplayInputError):
                replay.replay_bytes(data)
        value = _bundle()
        value["played_character_id"] = True
        with self.assertRaises(replay.ReplayInputError):
            replay.replay_bytes(_bytes(value))

    def test_cli_stdout_new_file_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, target = root / "input.json", root / "report.json"
            data = _bytes(_bundle())
            source.write_bytes(data)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(replay.main(["--input", str(source)]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["execution_mode"], "offline-replay")
            self.assertEqual(replay.main(["--input", str(source), "--output", str(target)]), 0)
            prior = target.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(replay.main(["--input", str(source), "--output", str(target)]), 2)
                self.assertEqual(replay.main(["--input", str(source), "--output", str(source)]), 2)
            self.assertEqual(target.read_bytes(), prior)
            self.assertEqual(source.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
