from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "native_bridge/research/analyze_phase2_post_call_live.py"
SPEC = importlib.util.spec_from_file_location("phase2_post_call_postprocess", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def observer(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "private_build": True,
        "installed": True,
        "failure": 0,
        **{field: 0 for field in MODULE.TELEMETRY_FIELDS},
    }
    values.update(changes)
    return values


def heartbeat(sequence: int, **changes: object) -> dict[str, object]:
    return {
        "type": "heartbeat",
        "pid": 42,
        "sequence": sequence,
        MODULE.OBSERVER_KEY: observer(**changes),
    }


def complete_scan(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "hit_count": 1,
        "nonempty_list_count": 1,
        "descriptor_seen_count": 27,
        "last_producer_list": 0x1000,
        "last_list_begin": 0x2000,
        "last_list_count": 27,
        "raw_last_descriptor": 0x3000,
        "raw_last_task": 0x4000,
        "raw_last_owner": 0x5000,
        "raw_last_callback": 0x6000,
        "raw_last_callback_slot2_target": 0x7000,
        "last_thread_id": 7,
        "last_timestamp_qpc": 100,
    }
    values.update(changes)
    return values


class Phase2PostCallLivePostprocessTests(unittest.TestCase):
    def test_no_hook_hit(self) -> None:
        result = MODULE.analyze({"last": heartbeat(1)})
        self.assertEqual((result["status"], result["decision"]), ("NO-GO", "no-hook-hit"))

    def test_empty_list(self) -> None:
        result = MODULE.analyze(
            {"last": heartbeat(1, hit_count=1, last_producer_list=0x1000,
                               last_thread_id=7, last_timestamp_qpc=100)}
        )
        self.assertEqual(result["decision"], "empty-list")

    def test_scan_no_selected_and_next_seam(self) -> None:
        result = MODULE.analyze({"last": heartbeat(1, **complete_scan())})
        self.assertEqual((result["status"], result["decision"]), ("NO-GO", "scan-no-selected"))
        self.assertEqual(result["scan"]["last_list_count"], 27)
        self.assertEqual(
            result["next_observation"]["kind"],
            "private-slot2-rva-histogram-with-task-identity",
        )

    def test_selected_states_are_typed_from_last_selection(self) -> None:
        for state in (0, 2, 3):
            with self.subTest(state=state):
                counts = {f"selected_state{state}_count": 1}
                result = MODULE.analyze(
                    {
                        "last": heartbeat(
                            1,
                            **complete_scan(
                                selected_event_count=1,
                                last_descriptor=0x3000,
                                last_task=0x4000,
                                last_owner=0x5000,
                                last_callback=0x6000,
                                last_callback_slot2_target=0x14088B480,
                                last_state=state,
                                **counts,
                            ),
                        )
                    }
                )
                self.assertEqual((result["status"], result["decision"]), ("GREEN", f"selected-state{state}"))

    def test_read_failure_or_oversize_list_is_context_incomplete(self) -> None:
        result = MODULE.analyze(
            {"last": heartbeat(1, **complete_scan(read_failure_count=1))}
        )
        self.assertEqual(result["decision"], "context-incomplete")
        result = MODULE.analyze(
            {"last": heartbeat(1, **complete_scan(last_list_count=4097, scan_truncated_count=1))}
        )
        self.assertEqual(result["decision"], "context-incomplete")

    def test_strict_27_field_schema_rejects_missing_and_extra(self) -> None:
        missing = heartbeat(1)
        del missing[MODULE.OBSERVER_KEY]["raw_last_task"]
        result = MODULE.analyze({"last": missing})
        self.assertEqual((result["status"], result["decision"]), ("RED", "observer-schema-invalid"))
        extra = heartbeat(1)
        extra[MODULE.OBSERVER_KEY]["future_field"] = 1
        result = MODULE.analyze({"last": extra})
        self.assertEqual((result["status"], result["decision"]), ("RED", "observer-schema-invalid"))
        self.assertEqual(result["schema"]["telemetry_field_count"], 27)

    def test_install_and_counter_contract_failures_are_red(self) -> None:
        failed = MODULE.analyze({"last": heartbeat(1, installed=False, failure=4)})
        self.assertEqual(failed["decision"], "observer-install-or-runtime-failure")
        regressed = MODULE.analyze(
            {
                "heartbeats": [
                    heartbeat(1, hit_count=2),
                    heartbeat(2, hit_count=1),
                ]
            }
        )
        self.assertEqual(regressed["decision"], "observer-counter-contract-invalid")

    def test_result_is_json_serializable(self) -> None:
        result = MODULE.analyze({"last": heartbeat(1, **complete_scan())})
        self.assertIsInstance(json.dumps(result), str)


if __name__ == "__main__":
    unittest.main()
