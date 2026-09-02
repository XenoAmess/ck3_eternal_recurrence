from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge/research/analyze_phase2_wrapper_entry_live.py"
)
SPEC = importlib.util.spec_from_file_location("phase2_wrapper_postprocess", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def caller_artifact() -> dict:
    rvas = list(range(0x1000, 0x1000 + 618))
    MODULE.EXPECTED_CALLSITE_LIST_SHA256 = MODULE.canonical_rva_digest(rvas)
    return {
        "source": {"sha256": MODULE.EXPECTED_EXE_SHA256},
        "direct_callers": {"call_rvas": [f"0x{value:X}" for value in rvas]},
    }


def heartbeat(sequence: int, entry_count: int, callsite: int = 0x1000,
              owner: int = 0x2000, carrier: int = 0x3000) -> dict:
    return {
        "type": "heartbeat",
        "pid": 42,
        "sequence": sequence,
        MODULE.OBSERVER_KEY: {
            "installed": True,
            "failure": 0,
            "entry_count": entry_count,
            "last_return_address": 0 if entry_count == 0 else 0x5000,
            "last_callsite_rva": 0 if entry_count == 0 else callsite,
            "last_scheduler_owner": 0 if entry_count == 0 else owner,
            "last_producer_list": 0 if entry_count == 0 else carrier,
            "last_thread_id": 0 if entry_count == 0 else 7,
            "last_timestamp_qpc": 0 if entry_count == 0 else 100 + sequence,
        },
    }


class Phase2WrapperEntryLivePostprocessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.callers = caller_artifact()

    def test_valid_samples_report_distributions_and_carrier_change(self) -> None:
        runner = {
            "heartbeats": [
                heartbeat(1, 1),
                heartbeat(2, 3, callsite=0x1001, carrier=0x4000),
            ],
            "duplicate": heartbeat(2, 3, callsite=0x1001, carrier=0x4000),
        }
        result = MODULE.analyze(runner, self.callers)
        self.assertEqual(result["status"], "GREEN")
        self.assertEqual(result["decision"], "entry-caller-owner-carrier-observed")
        self.assertEqual(result["heartbeat"]["valid_observer_sample_count"], 2)
        self.assertEqual(
            result["producer_list_carrier"]["change_classification"],
            "changed-across-sampled-last-values",
        )
        self.assertEqual(result["return_dimension"]["status"], "not_observed_by_v1")
        self.assertFalse(result["return_dimension"]["affects_decision"])

    def test_no_entry_is_typed_no_go_not_schema_red(self) -> None:
        result = MODULE.analyze({"last": heartbeat(1, 0)}, self.callers)
        self.assertEqual(result["status"], "NO-GO")
        self.assertEqual(result["decision"], "no-entry-observed")

    def test_invalid_caller_is_red(self) -> None:
        result = MODULE.analyze(
            {"last": heartbeat(1, 1, callsite=0x9999)}, self.callers
        )
        self.assertEqual(result["status"], "RED")
        self.assertEqual(result["decision"], "entry-caller-outside-frozen-set")
        self.assertEqual(result["caller"]["invalid_sampled_callsites"], [0x9999])

    def test_missing_observer_schema_is_red(self) -> None:
        result = MODULE.analyze(
            {"last": {"type": "heartbeat", "pid": 42, "sequence": 1}},
            self.callers,
        )
        self.assertEqual(result["status"], "RED")
        self.assertEqual(result["decision"], "observer-schema-missing")

    def test_counter_regression_is_red(self) -> None:
        result = MODULE.analyze(
            {"heartbeats": [heartbeat(1, 2), heartbeat(2, 1)]}, self.callers
        )
        self.assertEqual(result["status"], "RED")
        self.assertEqual(result["decision"], "entry-counter-regressed")

    def test_qpc_regression_is_red(self) -> None:
        first = heartbeat(1, 1)
        second = heartbeat(2, 2)
        first[MODULE.OBSERVER_KEY]["last_timestamp_qpc"] = 200
        second[MODULE.OBSERVER_KEY]["last_timestamp_qpc"] = 100
        result = MODULE.analyze({"heartbeats": [first, second]}, self.callers)
        self.assertEqual(result["status"], "RED")
        self.assertEqual(result["decision"], "entry-qpc-regressed")

    def test_tool_source_is_json_serializable(self) -> None:
        result = MODULE.analyze({"last": heartbeat(1, 1)}, self.callers)
        self.assertIsInstance(json.dumps(result), str)


if __name__ == "__main__":
    unittest.main()
