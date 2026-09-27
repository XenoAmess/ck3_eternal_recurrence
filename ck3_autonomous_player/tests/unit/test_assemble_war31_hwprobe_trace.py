"""Offline source-binding checks for a future War31 hardware-probe stream."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/assemble_war31_hwprobe_trace.py"


def load_assembler():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("War31 probe assembler unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_input():
    start = {"kind": "start", "schema": "xar.ck3.war31.hwprobe_raw.v1",
             "pid": 1234, "process_created_filetime": 100000,
             "module_base": "0x140000000", "fixture": False}
    common = {"kind": "sample", "pid": 1234, "thread_id": 7,
              "rax_change_pointer": "0x100000008", "change_type_dword": 0,
              "memory_read_status": "ok"}
    first = {**common, "site_rva": "0x2E9F746", "event_ordinal": 1, "qpc": 100}
    second = {**common, "site_rva": "0x2EC4410", "event_ordinal": 2,
              "qpc": 101, "change_type_dword": 23}
    end = {"kind": "terminal", "status": "paired", "reason": "paired",
           "debug_registers_cleared": True, "detached": True, "hit_count": 2}
    manifest = {"schema": "xar.ck3.war31.hwprobe_manifest.v1",
                "request_id": "WAR-INPUT-R0221-WAR31-20260927", "war_id": 16777231,
                "episode_run_id": "native-29829-2bc2d599f7f9",
                "date_raw": 53215920, "ck3_exe_sha256":
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
                "bridge_dll_sha256": "C36ECCEB67A0DCA7C8C1C6C855A5036771B46617E9F1BF5F4185D965C1951BCE",
                "checkpoint_sha256": "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A",
                "source_driver_state_sha256": "1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336",
                "driver_state_sha256": "D" * 64,
                "rebind_receipt_sha256": "E" * 64,
                "authorization_receipt_sha256": "C" * 64,
                "action_attempt_id": "synthetic-action-1",
                "effect_invocation_id": "synthetic-invocation-1",
                "frame_token": "synthetic-frame-1", "expected_pid": 1234,
                "expected_process_created_filetime": 100000,
                "approved_action_step": "surrender-war-16777231",
                "source_evidence_status": "separately_authorized_unverified_by_probe"}
    return [start, first, second, end], manifest


def encode(events):
    return ("\n".join(json.dumps(value) for value in events) + "\n").encode()


class AssembleWar31HardwareProbeTests(unittest.TestCase):
    def test_synthetic_pair_remains_structural_only(self):
        module = load_assembler()
        events, manifest = synthetic_input()
        assembled = module.assemble(encode(events), manifest)
        self.assertEqual(assembled["status"], "STRUCTURAL_PAIR_ONLY")
        self.assertEqual(assembled["structural_validation"]["resolve_type_dword"], 23)
        self.assertIsNone(assembled["structural_validation"]["actual_taken_branch"])
        self.assertEqual(assembled["trace"]["samples"][0]["process_instance_id"], "1234:100000")

    def test_fixture_red_and_single_point_fail_closed(self):
        module = load_assembler()
        events, manifest = synthetic_input()
        fixture = copy.deepcopy(events)
        fixture[0]["fixture"] = True
        with self.assertRaisesRegex(ValueError, "fixture"):
            module.assemble(encode(fixture), manifest)
        red = copy.deepcopy(events)
        red[-1]["debug_registers_cleared"] = False
        with self.assertRaisesRegex(ValueError, "clean two-point detach"):
            module.assemble(encode(red), manifest)
        single = [events[0], events[1], events[-1]]
        with self.assertRaisesRegex(ValueError, "one start, two samples"):
            module.assemble(encode(single), manifest)

    def test_cross_process_pointer_and_authorization_fail_closed(self):
        module = load_assembler()
        events, manifest = synthetic_input()
        mismatch = copy.deepcopy(events)
        mismatch[2]["rax_change_pointer"] = "0x100000010"
        with self.assertRaisesRegex(ValueError, "different change pointers"):
            module.assemble(encode(mismatch), manifest)
        mismatch = copy.deepcopy(events)
        mismatch[2]["pid"] = 4321
        with self.assertRaisesRegex(ValueError, "another process"):
            module.assemble(encode(mismatch), manifest)
        wrong_action = dict(manifest)
        wrong_action["approved_action_step"] = "white-peace-war-16777231"
        with self.assertRaisesRegex(ValueError, "authorized War31 action"):
            module.assemble(encode(events), wrong_action)
        wrong_source = dict(manifest)
        wrong_source["source_driver_state_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source_driver_state_sha256"):
            module.assemble(encode(events), wrong_source)


if __name__ == "__main__":
    unittest.main()
