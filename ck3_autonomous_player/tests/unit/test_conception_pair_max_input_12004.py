"""One focused captured-instruction qualification of the new pair-max leaf.

Only the already captured CMP/CMOVL bytes are executed on synthetic signed32
register arguments. The full helper and Game state are never executed/read.
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
from xar_autoplayer.simulation.conception_pair_max_input_12004 import (
    consume_conception_pair_max_input_12004,
)


class ConceptionPairMaxInput12004Test(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt" and os.environ.get("XAR_PAIR_MAX_SOURCE"),
                         "requires supplied actual4 provider source on Windows x64")
    def test_captured_compare_numeric_edges_and_actual_absence_once(self) -> None:
        start = time.perf_counter()
        source = Path(os.environ["XAR_PAIR_MAX_SOURCE"])
        source_bytes = source.read_bytes()
        provider = json.loads(source_bytes)
        self.assertEqual(provider["build"], CK3_12004.game_version)
        self.assertEqual(provider["held_image_sha256"], CK3_12004.executable_sha256)
        rows = {int(row["rva"], 0): row for row in provider["instructions"]}
        cmp_row, cmov_row = rows[0x2B95B98], rows[0x2B95B9A]
        self.assertEqual((cmp_row["mnemonic"], cmp_row["op_str"], cmp_row["bytes"]),
                         ("cmp", "ebx, eax", "3bd8"))
        self.assertEqual((cmov_row["mnemonic"], cmov_row["op_str"], cmov_row["bytes"]),
                         ("cmovl", "ebx, eax", "0f4cd8"))
        compare_bytes = bytes.fromhex(cmp_row["bytes"] + cmov_row["bytes"])
        # Windows x64 wrapper saves RBX, moves RCX/RDX arguments into EBX/EAX,
        # executes the five literal captured bytes, returns EBX in EAX.
        code = bytes.fromhex("538bd98bc2") + compare_bytes + bytes.fromhex("8bc35bc3")
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
        comparisons = []
        identity = {"build_version": CK3_12004.game_version,
                    "executable_sha256": CK3_12004.executable_sha256}
        try:
            ctypes.memmove(address, code, len(code))
            old_protection = ctypes.c_uint32()
            if not kernel.VirtualProtect(address, len(code), 0x20, ctypes.byref(old_protection)):
                raise OSError(ctypes.get_last_error(), "VirtualProtect failed")
            native = ctypes.WINFUNCTYPE(ctypes.c_int32, ctypes.c_int32, ctypes.c_int32)(address)
            for first, second in [
                (0, 0), (0, 1), (1, 0), (4, 7), (7, 4), (7, 7),
                (-1, 0), (0, -1), (-7, -4), (-4, -7),
                (-(2**31), 2**31 - 1), (2**31 - 1, -(2**31)),
                (-(2**31), -(2**31)), (2**31 - 1, 2**31 - 1),
            ]:
                result = consume_conception_pair_max_input_12004(
                    **identity, first_character_id=38822, second_character_id=38718,
                    first_lineage_tier_max_raw=first, second_lineage_tier_max_raw=second,
                )
                actual = native(first, second)
                self.assertEqual(result.pair_lineage_tier_max_raw, actual)
                self.assertEqual(result.status, "pair_max_available")
                self.assertEqual(result.selected_return, "second" if second > first else "first")
                comparisons.append({"first_raw": first, "second_raw": second,
                                    "captured_instruction_result_raw": actual,
                                    "selected_return": result.selected_return})
        finally:
            if not kernel.VirtualFree(address, 0, 0x8000):
                raise OSError(ctypes.get_last_error(), "VirtualFree failed")
        for first, second in [(None, None), (0, None), (None, 0)]:
            result = consume_conception_pair_max_input_12004(
                **identity, first_character_id=38822, second_character_id=38718,
                first_lineage_tier_max_raw=first, second_lineage_tier_max_raw=second,
            )
            self.assertEqual(result.status, "helper_values_unavailable")
            self.assertIsNone(result.pair_lineage_tier_max_raw)
            self.assertEqual(result.first_lineage_tier_max_raw, first)
            self.assertEqual(result.second_lineage_tier_max_raw, second)
        with self.assertRaisesRegex(ValueError, "signed32"):
            consume_conception_pair_max_input_12004(
                **identity, first_character_id=38822, second_character_id=38718,
                first_lineage_tier_max_raw=2**31, second_lineage_tier_max_raw=0,
            )
        household_source = Path(os.environ["XAR_PAIR_MAX_HOUSEHOLD"])
        household_bytes = household_source.read_bytes()
        household = json.loads(household_bytes)
        inputs = household["relation"]["current_first_heir_reproductive_inputs_v1"]
        actual_rows = inputs["rows"]
        self.assertEqual([row["character_id"] for row in actual_rows], [38822, 38718])
        self.assertTrue(all("lineage_tier_max_raw" not in row for row in actual_rows))
        self.assertEqual([row["native_fertility"]["effective_raw"] for row in actual_rows], [40000, 25000])
        missing = consume_conception_pair_max_input_12004(
            **identity, first_character_id=38822, second_character_id=38718,
            first_lineage_tier_max_raw=None, second_lineage_tier_max_raw=None,
        )
        self.assertIsNone(missing.pair_lineage_tier_max_raw)
        receipt = {
            "schema": "xar.conception-pair-max-input12004-focused-qualification.v1",
            "status": "GREEN", "proof_layer": "offline-captured-instruction-and-production-consumer",
            "provider_source": str(source), "provider_source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "literal_compare_bytes": compare_bytes.hex(), "literal_compare_rvas": ["0x2B95B98", "0x2B95B9A"],
            "synthetic_signed32_comparison_cases": comparisons,
            "negative_and_extreme_cases_scope": "Register-level arithmetic contract only; not actual household tier observations",
            "actual_household_source": str(household_source),
            "actual_household_sha256": hashlib.sha256(household_bytes).hexdigest(),
            "actual_household_native_revision": inputs["native_revision"],
            "actual_household_date_raw": inputs["date_raw"],
            "actual_helper_values": [None, None], "actual_pair_max_raw": None,
            "new_game_calls": 0, "new_exe_reads": 0, "new_m7_credit": 0,
            "elapsed_seconds": time.perf_counter() - start,
        }
        with Path(os.environ["XAR_PAIR_MAX_RECEIPT"]).open("x", encoding="utf-8") as output:
            json.dump(receipt, output, indent=2)
            output.write("\n")


if __name__ == "__main__":
    unittest.main()
