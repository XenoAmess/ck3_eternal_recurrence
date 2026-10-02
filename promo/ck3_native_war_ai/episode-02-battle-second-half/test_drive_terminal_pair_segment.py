"""Focused no-screen tests for early terminal capture in the segmented driver."""

from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("drive_terminal_pair_segment.py")
SPEC = importlib.util.spec_from_file_location("e2_terminal_segment", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SEGMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEGMENT)


class EarlyTerminalTest(unittest.TestCase):
    def run_observe(self, terminal_kind: str, include_writer: bool) -> tuple[dict, list[str]]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            live = root / "live"
            output = live / "ck3-output"
            output.mkdir(parents=True)
            recorder = live / "recording-e2-09-terminal-a01"
            frozen = {
                "status": "STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY",
                "checkpoint_date_raw": 53146872,
                "expected_combat_id": 16777218,
                "expected_war_id": 4,
                "bridge": {"sha256": "B" * 64},
                "injector": {"sha256": "I" * 64},
                "checkpoint_save": {"sha256": "S" * 64},
                "live_argv_without_fresh_steam_offline_receipt": ["--output-dir", str(output), "--capture"],
            }
            static = root / "a05.json"
            static.write_text(json.dumps(frozen), encoding="utf-8")
            (output / "preflight.json").write_text(json.dumps({
                "result": "READY_FOR_BOUNDED_LIVE_ATTEMPT",
                "bridge_dll": frozen["bridge"],
                "bridge_injector": frozen["injector"],
                "checkpoint_source": {"save": frozen["checkpoint_save"]},
            }), encoding="utf-8")
            writer = {
                "status": "recorded", "war_id": 4,
                "value_raw_q100000": 100000,
                "attacker_relative_delta_raw_q100000": -100000,
                "selected_cb_battle_scale_raw_q100000": 100000,
                "denominator_inputs": {
                    "after_minimum_int32": 1,
                    "participants": [{"buckets_native_add_order_int32": [1] * 8}],
                },
            } if include_writer else {}
            responses = [
                ({"paused": True, "map_ready": True, "date_raw": 53146872,
                  "revision": 7}, {"sha256": "1" * 64}, {}),
                ({"battle_control_snapshot": {"status": "unavailable"},
                  "queried_revision": 7}, {"sha256": "2" * 64}, {}),
                ({"battle_terminal_transition": {"prior": {
                    "terminal_kind": terminal_kind,
                    "hard_loss_inputs": {"hard_loss_raw": 1},
                    "battle_warscore": writer}},
                  "queried_revision": 7}, {"sha256": "3" * 64}, {}),
            ]
            names: list[str] = []

            def fake_call(_output, label, _tool, _arguments, _workdir, _frozen, _timeout):
                names.append(label)
                return responses.pop(0)

            argv = [str(SCRIPT), "observe", "--static-receipt", str(static),
                    "--session-output", str(output), "--recorder-workdir", str(recorder),
                    "--segment", "1", "--day", "27", "--execute"]
            with (patch.object(sys, "argv", argv),
                  patch.object(SEGMENT, "call", fake_call),
                  redirect_stdout(io.StringIO())):
                if terminal_kind == "normal_result" and include_writer:
                    SEGMENT.main()
                else:
                    with self.assertRaises(ValueError):
                        SEGMENT.main()
            result = json.loads((live / "terminal-pair-steps" /
                                 "e2t-s01-d27-observe.json").read_text(encoding="utf-8"))
            return result, names

    def test_early_normal_result_preserves_control_and_writer(self) -> None:
        result, names = self.run_observe("normal_result", True)
        self.assertEqual(result["status"], "new-run-writer-captured-await-after-panel")
        self.assertEqual(result["control_probe"]["sha256"], "2" * 64)
        self.assertEqual(result["native_response"]["sha256"], "3" * 64)
        self.assertEqual(names, ["e2t-s01-d27-snapshot", "e2t-s01-d27-control",
                                 "e2t-s01-d27-early-terminal"])

    def test_early_normal_result_missing_writer_is_red(self) -> None:
        result, names = self.run_observe("normal_result", False)
        self.assertEqual(result["status"], "red-preserved")
        self.assertEqual(len(names), 3)


if __name__ == "__main__":
    unittest.main()
