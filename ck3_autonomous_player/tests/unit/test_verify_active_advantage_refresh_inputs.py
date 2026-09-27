from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "native_bridge" / "research"))

import verify_active_advantage_refresh_inputs as refresh


class _Image:
    def __init__(self):
        self.data = {rva: bytes.fromhex(expected)
                     for rva, expected in refresh.SITES.values()}
        self.DIRECTORY_ENTRY_EXCEPTION = [
            SimpleNamespace(struct=SimpleNamespace(BeginAddress=begin,
                                                 EndAddress=end))
            for begin, end in refresh.FUNCTION_SPANS.values()
        ]

    def get_data(self, rva, size):
        return self.data[rva][:size]


class ActiveAdvantageRefreshInputsTest(unittest.TestCase):
    def test_knight_accolade_append_and_entry_writes_are_pinned(self):
        image = _Image()
        with patch.object(refresh, "verify_pause_leaves"):
            result = refresh.verify_image(image)
            self.assertEqual(result["anchors"]["side_modifier_destination"]["rva"],
                             "0x23CBE99")
            for name in ("apply_accolade_to_side", "entry_damage_write",
                         "entry_toughness_write"):
                rva, expected = refresh.SITES[name]
                image.data[rva] = b"\x90" * (len(expected) // 2)
                with self.assertRaisesRegex(ValueError, name):
                    refresh.verify_image(image)
                image.data[rva] = bytes.fromhex(expected)

    def test_pdata_owner_mismatch_is_rejected(self):
        image = _Image()
        image.DIRECTORY_ENTRY_EXCEPTION[1].struct.EndAddress -= 1
        with patch.object(refresh, "verify_pause_leaves"):
            with self.assertRaisesRegex(ValueError, "accolade_refresh_body"):
                refresh.verify_image(image)


if __name__ == "__main__":
    unittest.main()
