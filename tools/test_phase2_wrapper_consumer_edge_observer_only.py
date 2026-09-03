#!/usr/bin/env python3
"""Focused static contracts for Phase-2 native-observer-only mode."""

from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parent
MODULE_PATH = SOURCE / "run_zg361_phase2_seed_capture.py"
SPEC = importlib.util.spec_from_file_location("phase2_seed_observer_only", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def edge(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "private_build": True,
        "installed": True,
        "failure_flags": 0,
        "wrapper_post_publish_entry_count": 1,
        "selected_after_publish_edge_0x3B9E10B_count": 1,
        "selected_after_publish_edge_0x3B9E175_count": 0,
        "selected_after_publish_other_caller_count": 0,
        "consumer_identity_match_count": 1,
    }
    value.update(overrides)
    return value


class FakeService:
    def __init__(self, samples: list[tuple[dict[str, object], dict[str, object]]]):
        self.samples = samples
        self.index = 0

    def capabilities(self) -> dict[str, object]:
        sample = self.samples[min(self.index, len(self.samples) - 1)]
        self.index += 1
        return {
            "diagnostics": {
                "last_heartbeat": {
                    "type": "heartbeat",
                    "pid": 42,
                    "sequence": self.index,
                    runner.PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_KEY: sample[0],
                    runner.PHASE2_PRODUCER_CORRELATION_OBSERVER_KEY: sample[1],
                }
            }
        }


class FakeTime:
    def __init__(self) -> None:
        self.value = 0.0

    def clock(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class ObserverOnlyTest(unittest.TestCase):
    def test_typed_decision_matrix(self) -> None:
        cases = (
            (edge(), {"producer_selected_count": 0}, "producer_selected_task_not_observed"),
            (
                edge(wrapper_post_publish_entry_count=0),
                {"producer_selected_count": 1},
                "selected_task_wrapper_never_rescheduled",
            ),
            (
                edge(
                    selected_after_publish_edge_0x3B9E10B_count=0,
                    selected_after_publish_edge_0x3B9E175_count=0,
                ),
                {"producer_selected_count": 1},
                "wrapper_entered_other_branch",
            ),
            (
                edge(consumer_identity_match_count=0),
                {"producer_selected_count": 1},
                "consumer_edge_without_retained_task_identity",
            ),
            (
                edge(),
                {"producer_selected_count": 1},
                "selected_task_reached_completion_consumer",
            ),
        )
        for observer, correlation, expected in cases:
            with self.subTest(expected=expected):
                _status, decision = runner._phase2_wrapper_edge_decision(
                    observer, correlation
                )
                self.assertEqual(decision, expected)

    def test_heartbeat_only_green_has_no_desktop_or_input(self) -> None:
        service = FakeService([(edge(), {"producer_selected_count": 1})])
        timer = FakeTime()
        with tempfile.TemporaryDirectory() as raw:
            report = runner.observe_phase2_wrapper_consumer_edge(
                service,
                Path(raw),
                timeout_seconds=1.0,
                clock=timer.clock,
                sleeper=timer.sleep,
            )
            persisted = [
                json.loads(line)
                for line in (
                    Path(raw) / "phase2-wrapper-consumer-edge-heartbeats.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["sample_count"], 1)
        self.assertEqual(len(persisted), 1)
        self.assertFalse(report["image_used"])
        self.assertFalse(report["ocr_used"])
        self.assertFalse(report["ui_input_sent"])
        self.assertEqual(report["gameplay_commands"], [])

    def test_observer_only_branch_returns_before_legal_handler(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        branch = source[
            source.index("        if config.native_observer_only:") : source.index(
                "        try:\n            legal_evidence", source.index(
                    "        if config.native_observer_only:"
                )
            )
        ]
        self.assertIn("observe_phase2_wrapper_consumer_edge", branch)
        self.assertIn("return report", branch)
        self.assertNotIn("ImageGrab", branch)
        self.assertNotIn("handle_phase2_optional_legal_consent", branch)
        helper = inspect.getsource(runner.observe_phase2_wrapper_consumer_edge)
        self.assertNotIn("ImageGrab", helper)
        self.assertNotIn("deliberate_click", helper)
        self.assertNotIn("keyboard_layout_attestor", helper)


if __name__ == "__main__":
    unittest.main()
