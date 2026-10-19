"""Finite ABI/closed-fact tests only. No C++ fixture execution or output files."""
import copy
import io
import struct
import unittest

import native30_artifact_postcheck10_20261020 as p


def image():
    data = bytearray(0x4400)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 3, 0, 0, 0, 240, 0x2022)
    opt = 0x98
    struct.pack_into("<H", data, opt, 0x20B)
    struct.pack_into("<Q", data, opt + 24, 0x180000000)
    struct.pack_into("<I", data, opt + 56, 0x113B000)
    struct.pack_into("<II", data, opt + 112, 0x3000, 0x100)
    for i, (name, virtual, rva, size, offset, flags) in enumerate((
        (b".text", 0x1000, 0x1000, 0x1000, 0x400, 0x60000020),
        (b".rdata", 0x1000, 0x3000, 0x1000, 0x1400, 0x40000040),
        (b".data", 0x2000, 0x1139000, 0x2000, 0x2400, 0xC0000040))):
        at = opt + 240 + i * 40
        data[at:at + len(name)] = name
        struct.pack_into("<IIII", data, at + 8, virtual, rva, size, offset)
        struct.pack_into("<I", data, at + 36, flags)
    struct.pack_into("<IIHHIIIIIII", data, 0x1400, 0, 0, 0, 0, 0, 1, 6, 6, 0x3100, 0x3140, 0x3120)
    struct.pack_into("<6I", data, 0x1500, *range(0x1100, 0x1105), p.DATA_RVA)
    struct.pack_into("<6H", data, 0x1520, *range(6))
    offset = 0x1600
    for i, name in enumerate((*p.FUNCTIONS, p.DATA)):
        struct.pack_into("<I", data, 0x1540 + i * 4, offset - 0x1400 + 0x3000)
        raw = name.encode() + b"\0"
        data[offset:offset + len(raw)] = raw
        offset += len(raw)
    struct.pack_into("<8Q", data, 0x2F50, *p.HEADER)
    return data


class PeTests(unittest.TestCase):
    def test_five_code_plus_source_data_write_is_allowed(self):
        result = p.inspect_pe_exports(io.BytesIO(image()))
        self.assertEqual(len(result["exports"]), 6)
        self.assertEqual(result["directory_bytes"], 2752)
        self.assertEqual(result["raw_header"], list(p.HEADER))
        self.assertTrue(result["data_section"]["flags"] & 0x80000000)

    def test_wrong_header_or_code_data_rejected(self):
        for offset, value in ((0x2F58, 2), (0x98 + 240 + 2 * 40 + 36, 0xE0000040)):
            data = image()
            struct.pack_into("<I", data, offset, value)
            with self.assertRaises(RuntimeError):
                p.inspect_pe_exports(io.BytesIO(data))

    def test_ordinal_only_duplicate_forwarder_and_wrong_name_rejected(self):
        changes = ((0x1400 + 24, 5), (0x1520, 1), (0x1500, 0x3050), (0x1600, 0x58585858))
        for offset, value in changes:
            data = image()
            struct.pack_into("<I" if offset != 0x1520 else "<H", data, offset, value)
            with self.assertRaises(RuntimeError):
                p.inspect_pe_exports(io.BytesIO(data))

    def test_virtual_zero_fill_and_cross_section_rejected(self):
        for raw_size, virtual_size in ((0xB50, 0x2000), (0x2000, 0xB50)):
            data = image()
            struct.pack_into("<I", data, 0x98 + 240 + 2 * 40 + 8, virtual_size)
            struct.pack_into("<I", data, 0x98 + 240 + 2 * 40 + 16, raw_size)
            with self.assertRaises(RuntimeError):
                p.inspect_pe_exports(io.BytesIO(data))


def records():
    args = [["fixture%d.exe" % i] for i in range(9)]
    return {"result": {"machine_id": "m", "status": "FAILED", "error": {"type": "RuntimeError", "text": "five exports"},
        "owned_active_after": 0, "future_writes": 0, "fixture_executions": 9, "fixture_builds": [],
        "fixture_runs": [{"argv": a, "returncode": 0, "owned_active_after": 0} for a in args],
        "phases": [{"argv": ["python", "-B", "check_native_layout_report_v1.py"], "returncode": 0, "owned_active_after": 0}]},
        "spec": {"machine_id": "m", "nonce": "task9", "task_name": "owned"},
        "closed": {"machine_id": "m", "nonce": "task9", "spec_sha256": p.RECORD09["spec"][2],
                   "child_exit_code": 1, "bootstrap_exit_code": 1, "job_active_after_stage": 0, "forced_remaining_cleanup": False},
        "unregister": {"machine_id": "m", "task_name": "owned", "actual": {"last_result": 1, "instances": 0, "absent_after": True}}}, args


class FactTests(unittest.TestCase):
    def test_exact_failure_reuses_only_closed_nine(self):
        value, args = records()
        before = copy.deepcopy(value)
        p.verify_closed09(value, args, "m")
        self.assertEqual(value, before)

    def test_missing_run_wrong_argv_and_nonzero_fail(self):
        for mode in ("missing", "argv", "exit", "Job", "machine", "other_failure", "Task"):
            value, args = records()
            if mode == "missing": value["result"]["fixture_runs"].pop()
            if mode == "argv": value["result"]["fixture_runs"][0]["argv"] = ["other.exe"]
            if mode == "exit": value["result"]["fixture_runs"][0]["returncode"] = 1
            if mode == "Job": value["closed"]["job_active_after_stage"] = 1
            if mode == "machine": value["spec"]["machine_id"] = "other"
            if mode == "other_failure": value["result"]["error"]["text"] = "other"
            if mode == "Task": value["unregister"]["actual"]["absent_after"] = False
            with self.assertRaises(RuntimeError):
                p.verify_closed09(value, args, "m")


if __name__ == "__main__":
    unittest.main(verbosity=2)
