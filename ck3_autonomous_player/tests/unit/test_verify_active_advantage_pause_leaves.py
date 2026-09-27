from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "native_bridge" / "research"))

import verify_active_advantage_pause_leaves as leaves


class _Image:
    def __init__(self):
        self.data = {rva: bytes.fromhex(expected)
                     for rva, expected in leaves.SITES.values()}
        self.DIRECTORY_ENTRY_EXCEPTION = [
            SimpleNamespace(struct=SimpleNamespace(
                BeginAddress=leaves.CONSTRUCTOR_SPAN[0],
                EndAddress=leaves.CONSTRUCTOR_SPAN[1]))
        ]

    def get_data(self, rva, size):
        return self.data[rva][:size]


class ActiveAdvantagePauseLeavesTest(unittest.TestCase):
    def test_constructor_and_refresh_are_hash_bound(self):
        image = _Image()
        with patch.object(leaves, "verify_component_sources",
                          return_value={"cache_chain_verified_on_same_image": True}):
            result = leaves.verify_image(image)
            self.assertEqual(result["constructor_span"],
                             ["0x2303CF0", "0x230402A"])
            image.data[0x2303E7C] = b"\x90" * 6
            with self.assertRaisesRegex(ValueError, "constructor_flag_write"):
                leaves.verify_image(image)
            image.data[0x2303E7C] = bytes.fromhex("8886FD060000")
            image.data[0x2308D66] = b"\x90" * 5
            with self.assertRaisesRegex(ValueError, "materialize_refresh_side0"):
                leaves.verify_image(image)

    def test_constructor_owner_and_source_chain_fail_closed(self):
        image = _Image()
        with patch.object(leaves, "verify_component_sources",
                          return_value={"cache_chain_verified_on_same_image": False}):
            with self.assertRaisesRegex(ValueError, "source chain"):
                leaves.verify_image(image)
        image.DIRECTORY_ENTRY_EXCEPTION[0].struct.EndAddress -= 1
        with patch.object(leaves, "verify_component_sources",
                          return_value={"cache_chain_verified_on_same_image": True}):
            with self.assertRaisesRegex(ValueError, "constructor owner"):
                leaves.verify_image(image)


if __name__ == "__main__":
    unittest.main()
