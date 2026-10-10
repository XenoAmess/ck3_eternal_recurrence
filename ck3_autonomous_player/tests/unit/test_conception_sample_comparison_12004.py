"""One bounded machine-body qualification of the new comparison consumer.

The external 241-byte exact body is supplied by Root, never searched for or
read from an EXE. Replay uses only owned synthetic two-DWORD state and adds no
game-state, probability, distribution or future-result evidence.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import time
import unittest

from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.simulation.conception_sample_comparison_12004 import (
    consume_conception_sample_comparison_12004,
)

EXPECTED_BODY_SHA256 = "73f7d36add188727a897301db67dbabc36637e44b9c8668c2b38762a1b6bb5ef"


class ConceptionSampleComparison12004MachineBodyTest(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt" and os.environ.get("XAR_CONCEPTION_SAMPLE_BODY"),
                         "requires Root-supplied exact241B body on Windows x64")
    def test_reached_body_and_comparison_consumer_once(self) -> None:
        start = time.perf_counter()
        source = Path(os.environ["XAR_CONCEPTION_SAMPLE_BODY"])
        code = source.read_bytes()
        self.assertEqual(len(code), 241)
        self.assertEqual(hashlib.sha256(code).hexdigest(), EXPECTED_BODY_SHA256)
        self.assertEqual(ctypes.sizeof(ctypes.c_void_p), 8)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
        kernel.VirtualAlloc.restype = ctypes.c_void_p
        kernel.VirtualProtect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        kernel.VirtualProtect.restype = ctypes.c_int
        kernel.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
        kernel.VirtualFree.restype = ctypes.c_int
        address = kernel.VirtualAlloc(None, len(code), 0x3000, 0x04)
        if not address:
            raise OSError(ctypes.get_last_error(), "VirtualAlloc failed")
        rows = []
        try:
            ctypes.memmove(address, code, len(code))
            old_protection = ctypes.c_uint32()
            if not kernel.VirtualProtect(address, len(code), 0x20, ctypes.byref(old_protection)):
                raise OSError(ctypes.get_last_error(), "VirtualProtect failed")
            state_type = ctypes.c_uint32 * 2
            native = ctypes.WINFUNCTYPE(ctypes.c_int64, ctypes.POINTER(ctypes.c_uint32),
                                       ctypes.c_int64, ctypes.c_int64)(address)
            identity = {"build_version": CK3_12004.game_version,
                        "executable_sha256": CK3_12004.executable_sha256}
            for counter, mixer in [(0, 0), (1, 1), (0xFFFFFFFE, 0),
                                   (0xFFFFFFFF, 0xFFFFFFFF), (0x80000000, 0x12345678),
                                   (0x12345678, 0x80000000)]:
                state = state_type(counter, mixer)
                sample = native(state, 0, 10_000_000)
                self.assertGreaterEqual(sample, 0)
                self.assertLessEqual(sample, 10_000_000)
                self.assertEqual(state[0], (counter + 2) & 0xFFFFFFFF)
                self.assertEqual(state[1], mixer)
                # Actual machine result, then the new production leaf. The
                # expected branch follows the native CMP/JGE, not a draw model.
                for threshold in (0, max(1, sample), sample + 1, 2**63 - 1):
                    consumed = consume_conception_sample_comparison_12004(
                        **identity, clamped_threshold=threshold, returned_sample=sample)
                    self.assertEqual(consumed.helper_reached, threshold > 0)
                    self.assertEqual(consumed.candidate_comparison_passed,
                                     threshold > 0 and sample < threshold)
                rows.append({"counter_before": counter, "mixer": mixer, "sample": sample,
                             "counter_after": state[0]})
            for sample, threshold, expected in [(0, 1, True), (10_000_000, 10_000_000, False),
                                                (10_000_000, 10_000_001, True)]:
                result = consume_conception_sample_comparison_12004(
                    **identity, clamped_threshold=threshold, returned_sample=sample)
                self.assertEqual(result.candidate_comparison_passed, expected)
            missing = consume_conception_sample_comparison_12004(
                **identity, clamped_threshold=1, returned_sample=None)
            self.assertIsNone(missing.candidate_comparison_passed)
            self.assertEqual(missing.status, "sample_unavailable")
            evidence = {"schema": "xar.conception-sample-comparison12004-machine-body-qualification.v1",
                        "body_sha256": EXPECTED_BODY_SHA256, "body_bytes": len(code),
                        "proof_layer": "offline-machine-body-and-production-consumer",
                        "state_source": "owned synthetic two-DWORD buffers", "native_calls": len(rows),
                        "rows": rows, "new_game_calls": 0, "new_exe_reads": 0,
                        "probability_or_forecast_claim": False, "elapsed_seconds": time.perf_counter() - start}
            receipt = os.environ.get("XAR_CONCEPTION_SAMPLE_RECEIPT")
            if receipt:
                with Path(receipt).open("x", encoding="utf-8") as output:
                    json.dump(evidence, output, indent=2)
                    output.write("\n")
        finally:
            if not kernel.VirtualFree(address, 0, 0x8000):
                raise OSError(ctypes.get_last_error(), "VirtualFree failed")


if __name__ == "__main__":
    unittest.main()
