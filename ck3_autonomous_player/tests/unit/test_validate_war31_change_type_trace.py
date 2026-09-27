"""Fail-closed offline pairing checks for a future War31 type trace."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/validate_war31_change_type_trace.py"
STATIC_RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_setup_change_type_write_boundary_1_19_0_6.json"
STATIC_RECEIPT_SHA256 = "52C90BAC612E76DCD28DBE380A80160C25DE2CE1AD3AE3736A128526141AF6FC"


def load_validator():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("War31 trace validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_trace(module, setup_type=0, resolve_type=0):
    shared = {
        "process_instance_id": "synthetic-process-1",
        "thread_id": 7,
        "action_attempt_id": "synthetic-authorized-action-1",
        "effect_invocation_id": "synthetic-invocation-1",
        "frame_token": "synthetic-frame-1",
        "war_id": module.WAR_ID,
        "episode_run_id": module.EPISODE_RUN_ID,
        "date_raw": 53215920,
        "checkpoint_sha256": "A" * 64,
        "bridge_dll_sha256": "B" * 64,
        "raw_capture_sha256": "C" * 64,
        "rax_change_pointer": "0x100000008",
        "memory_read_status": "ok",
        "capture_timing": "before_instruction",
    }
    samples = []
    for ordinal, ((site, opcode, phase), value) in enumerate(
        zip(module.SITES, (setup_type, resolve_type)), start=1
    ):
        samples.append({**shared, "site_rva": site, "instruction_bytes": opcode,
                        "site_phase": phase, "event_ordinal": ordinal,
                        "change_type_dword": value})
    return {"schema": module.SCHEMA, "request_id": module.REQUEST_ID,
            "ck3_exe_sha256": module.EXE_SHA256, "samples": samples}


class War31ChangeTypeTraceValidationTests(unittest.TestCase):
    def test_exact_sites_match_existing_static_receipt(self) -> None:
        module = load_validator()
        raw = STATIC_RECEIPT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest().upper(), STATIC_RECEIPT_SHA256)
        receipt = json.loads(raw)
        self.assertEqual(module.SITES[0][:2],
                         (receipt["setup_execute"]["resolved_change_pointer"]["rva"],
                          receipt["setup_execute"]["resolved_change_pointer"]["bytes"]))
        self.assertEqual(module.SITES[1][:2],
                         (receipt["resolve"]["type_read"]["rva"],
                          receipt["resolve"]["type_read"]["bytes"]))

    def test_pair_reports_only_raw_resolve_comparison(self) -> None:
        module = load_validator()
        result = module.validate(synthetic_trace(module, 0, 0x17))
        self.assertEqual(result["status"], "STRUCTURAL_PAIR_ONLY")
        self.assertEqual(result["setup_type_dword"], 0)
        self.assertEqual(result["resolve_type_dword"], 0x17)
        self.assertTrue(result["resolve_cmp_equals_0x17"])
        self.assertIsNone(result["actual_taken_branch"])
        self.assertIsNone(result["persisted_surrender_terms"])

    def test_one_point_and_cross_action_pairs_fail_closed(self) -> None:
        module = load_validator()
        one = synthetic_trace(module)
        one["samples"].pop()
        with self.assertRaisesRegex(ValueError, "exactly two"):
            module.validate(one)
        different = synthetic_trace(module)
        different["samples"][1]["action_attempt_id"] = "different-action"
        with self.assertRaisesRegex(ValueError, "cross-action"):
            module.validate(different)
        cross_frame = synthetic_trace(module)
        cross_frame["samples"][1]["date_raw"] += 24
        with self.assertRaisesRegex(ValueError, "cross-action or cross-frame"):
            module.validate(cross_frame)
        cross_capture = synthetic_trace(module)
        cross_capture["samples"][1]["raw_capture_sha256"] = "D" * 64
        with self.assertRaisesRegex(ValueError, "cross-action or cross-frame"):
            module.validate(cross_capture)

    def test_pointer_timing_and_memory_read_mismatches_fail_closed(self) -> None:
        module = load_validator()
        different_pointer = synthetic_trace(module)
        different_pointer["samples"][1]["rax_change_pointer"] = "0x100000010"
        with self.assertRaisesRegex(ValueError, "different change objects"):
            module.validate(different_pointer)
        wrong_timing = synthetic_trace(module)
        wrong_timing["samples"][0]["capture_timing"] = "after_instruction"
        with self.assertRaisesRegex(ValueError, "must precede"):
            module.validate(wrong_timing)
        failed_read = synthetic_trace(module)
        failed_read["samples"][1]["memory_read_status"] = "failed"
        with self.assertRaisesRegex(ValueError, "successful memory read"):
            module.validate(failed_read)
        wrong_opcode = synthetic_trace(module)
        wrong_opcode["samples"][1]["instruction_bytes"] = "90"
        with self.assertRaisesRegex(ValueError, "wrong exact pre-instruction site"):
            module.validate(wrong_opcode)


if __name__ == "__main__":
    unittest.main()
