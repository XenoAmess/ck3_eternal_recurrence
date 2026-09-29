from __future__ import annotations

import struct
import hashlib
import tempfile
import unittest
from pathlib import Path

from e2_05_a03_no_screen_gate import GateRed
from e2_05_a03_selector_binary_gate import (
    REQUIRED_TESTS,
    checked_cache,
    checked_junit,
    pe_machine_and_rva,
)


def fixture_pe() -> bytearray:
    image = bytearray(0x400)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 0x80)
    image[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HH", image, 0x84, 0x8664, 1)
    struct.pack_into("<H", image, 0x80 + 20, 0xF0)
    struct.pack_into("<H", image, 0x80 + 24, 0x20B)
    section = 0x80 + 24 + 0xF0
    struct.pack_into("<IIII", image, section + 8,
                     0x100, 0x1000, 0x100, 0x200)
    image[0x220:0x223] = b"ABC"
    return image


class SelectorBinaryGateTests(unittest.TestCase):
    def test_exact_amd64_pe_rva_bytes(self) -> None:
        self.assertEqual(pe_machine_and_rva(bytes(fixture_pe()), 0x1020, 3),
                         (0x8664, b"ABC"))

    def test_wrong_machine_or_unbacked_rva_is_red(self) -> None:
        image = fixture_pe()
        struct.pack_into("<H", image, 0x84, 0x14C)
        with self.assertRaises(GateRed):
            pe_machine_and_rva(bytes(image), 0x1020, 3)
        image = fixture_pe()
        with self.assertRaises(GateRed):
            pe_machine_and_rva(bytes(image), 0x1200, 3)

    def test_cache_rejects_disabled_managed_trace(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            exe = root / "ck3.exe"
            exe.write_bytes(b"fixture")
            cache = root / "CMakeCache.txt"
            cache.write_text(
                f"CMAKE_BUILD_TYPE:STRING=Release\n"
                f"BUILD_TESTING:BOOL=ON\n"
                f"XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1:BOOL=OFF\n"
                f"XAR_CK3_EXECUTABLE_PATH:FILEPATH={exe}\n",
                encoding="utf-8")
            with self.assertRaises(GateRed):
                checked_cache(cache, exe,
                              root, hashlib.sha256(cache.read_bytes()).hexdigest().upper())

    def test_junit_requires_exact_green_scope(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tests.xml"
            cases = "".join(f'<testcase name="{name}" status="run"><properties /></testcase>'
                            for name in sorted(REQUIRED_TESTS))
            path.write_text(f'<testsuite tests="6" failures="0">{cases}</testsuite>',
                            encoding="utf-8")
            correct_sha = hashlib.sha256(path.read_bytes()).hexdigest().upper()
            self.assertEqual(len(checked_junit(path, correct_sha, Path(folder))["tests"]), 6)
            with self.assertRaises(GateRed):
                checked_junit(path, "0" * 64, Path(folder))
            with self.assertRaises(GateRed):
                checked_junit(path, correct_sha, Path(folder) / "different-build")
            path.write_text('<testsuite tests="1" failures="0"><testcase name="one" /></testsuite>',
                            encoding="utf-8")
            with self.assertRaises(GateRed):
                checked_junit(path, hashlib.sha256(path.read_bytes()).hexdigest().upper(),
                              Path(folder))


if __name__ == "__main__":
    unittest.main()
