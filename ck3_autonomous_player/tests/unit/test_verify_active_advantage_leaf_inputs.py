from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "native_bridge" / "research"))

import verify_active_advantage_leaf_inputs as leaves


class _Image:
    def __init__(self):
        self.data = {rva: bytes.fromhex(expected)
                     for _, rva, _, expected in leaves.SITES}

    def get_data(self, rva, size):
        return self.data[rva][:size]


class ActiveAdvantageLeafVerifierTest(unittest.TestCase):
    def test_exact_leaf_pair_and_zero_flag_branch(self):
        image = _Image()
        with patch.object(leaves, "verify_component_sources",
                          return_value={"cache_chain_verified_on_same_image": True}):
            result = leaves.verify_image(image)
            self.assertEqual(result["aggregator_zero_flag_branch_target_rva"],
                             "0x23075E9")
            image.data[0x23076B8] = b"\x90" * 7
            with self.assertRaises(ValueError):
                leaves.verify_image(image)
            image.data[0x23076B8] = bytes.fromhex("496390D8000000")
            image.data[0x23074D1] = bytes.fromhex("0F8413010000")
            with self.assertRaises(ValueError):
                leaves.verify_image(image)


if __name__ == "__main__":
    unittest.main()
