from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "native_bridge/research/analyze_phase2_post_call_list_identity_live.py"
SPEC = importlib.util.spec_from_file_location("phase2_list_identity_postprocess", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sample(index: int, *, rva: int = 0x817C20, state: int = 1) -> dict[str, object]:
    task = 0x100000 + index * 0xC0
    return {
        "descriptor_index": index, "read_complete": True,
        "descriptor": task + 0x88, "task": task, "owner": 0x500000,
        "callback": task, "callback_slot2_target": 0x140000000 + rva,
        "callback_slot2_rva": rva, "state": state,
    }


def report(*, target_rva: int = 0x817C20, selected: int = 0) -> dict[str, object]:
    samples = [sample(i, rva=target_rva, state=1 if i < 2 else 0) for i in range(3)]
    observer = {
        "private_build": True, "installed": True, "failure": 0,
        "snapshot_consistent": True, "hit_count": 1, "capture_count": 1,
        "capture_contention_count": 0, "snapshot_sequence": 2,
        "last_producer_list": 0x800000, "last_list_begin": 0x800020,
        "last_list_count": 3, "last_scan_count": 3,
        "last_read_failure_count": 0, "last_scan_truncated_count": 0,
        "last_sample_count": 3, "last_sample_overflow_count": 0,
        "last_histogram_bin_count": 1, "last_histogram_overflow_count": 0,
        "last_selected_target_count": selected, "last_thread_id": 7,
        "last_timestamp_qpc": 99, "samples": samples,
        "histogram": [{
            "callback_slot2_target": 0x140000000 + target_rva,
            "callback_slot2_rva": target_rva, "count": 3,
            "first_task": samples[0]["task"], "first_owner": 0x500000,
            "last_task": samples[-1]["task"], "last_owner": 0x500000,
        }],
    }
    return {"terminal": {MODULE.OBSERVER_KEY: observer}}


class Phase2ListIdentityLivePostprocessTests(unittest.TestCase):
    def test_complete_list_excludes_loader_callback(self) -> None:
        result = MODULE.analyze(report())
        self.assertEqual(
            (result["status"], result["decision"]),
            ("GREEN", "complete-list-excludes-loader-callback"),
        )
        self.assertEqual(result["identity"]["slot2_rva_distribution"], [
            {"rva": "0x817C20", "count": 3}
        ])
        self.assertEqual(result["identity"]["task_stride_distribution"], [(192, 2)])
        self.assertFalse(result["identity"]["contains_loader_callback_rva"])

    def test_loader_callback_presence_is_typed(self) -> None:
        result = MODULE.analyze(report(target_rva=0x88B480, selected=3))
        self.assertEqual(result["decision"], "loader-callback-present")
        self.assertTrue(result["conclusion"]["current_list_is_loader_completion_list"])

    def test_overflow_and_schema_mismatch_are_red(self) -> None:
        value = report()
        observer = value["terminal"][MODULE.OBSERVER_KEY]
        observer["last_histogram_overflow_count"] = 1
        self.assertEqual(MODULE.analyze(value)["status"], "RED")
        value = report()
        del value["terminal"][MODULE.OBSERVER_KEY]["last_scan_count"]
        self.assertEqual(MODULE.analyze(value)["status"], "RED")

    def test_result_is_json_serializable(self) -> None:
        self.assertIsInstance(json.dumps(MODULE.analyze(report())), str)


if __name__ == "__main__":
    unittest.main()
