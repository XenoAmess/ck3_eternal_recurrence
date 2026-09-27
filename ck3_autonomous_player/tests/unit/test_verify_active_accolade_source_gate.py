from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "native_bridge" / "research"))

import verify_active_accolade_source_gate as gate


class _Image:
    def __init__(self):
        self.data = {rva: bytes.fromhex(expected)
                     for rva, expected in gate.SITES.values()}
        self.DIRECTORY_ENTRY_EXCEPTION = [SimpleNamespace(
            struct=SimpleNamespace(BeginAddress=gate.GATE_SPAN[0],
                                   EndAddress=gate.GATE_SPAN[1]))]

    def get_data(self, rva, size):
        return self.data[rva][:size]


class ActiveAccoladeSourceGateTest(unittest.TestCase):
    def test_all_row_source_gate_exact_bytes(self):
        image = _Image()
        with patch.object(gate, "verify_refresh_inputs"):
            result = gate.verify_image(image)
            self.assertEqual(result["gate_span"], ["0x251C200", "0x251C271"])
            for name in ("row_count", "row_source_pointer",
                         "source_virtual_gate", "gate_result_boolean"):
                rva, expected = gate.SITES[name]
                image.data[rva] = b"\x90" * (len(expected) // 2)
                with self.assertRaisesRegex(ValueError, name):
                    gate.verify_image(image)
                image.data[rva] = bytes.fromhex(expected)

    def test_gate_owner_is_required(self):
        image = _Image()
        image.DIRECTORY_ENTRY_EXCEPTION[0].struct.EndAddress -= 1
        with patch.object(gate, "verify_refresh_inputs"):
            with self.assertRaisesRegex(ValueError, "owner differs"):
                gate.verify_image(image)


if __name__ == "__main__":
    unittest.main()
