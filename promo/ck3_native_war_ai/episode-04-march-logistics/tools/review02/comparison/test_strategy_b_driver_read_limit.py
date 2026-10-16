"""Rehydration checks actual size before hashing an admitted Driver reference."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import strategy_b_stages as B


class Tests(unittest.TestCase):
    def test_small_reference_cannot_trigger_read_of_actual_oversize_driver(self):
        stages = B.BStages.__new__(B.BStages)
        stages.evidence = SimpleNamespace(file_limit=lambda path: 16 * 1024 * 1024)
        stages.r = SimpleNamespace(verify_pin=Mock(side_effect=AssertionError('must not hash/read oversized Driver')))
        packet = {'refs': {'strength_raw': {'path': 'unit-only-never-opened-driver.json', 'bytes': 1}}}
        with patch.object(B, 'Path') as path:
            path.return_value.stat.return_value.st_size = 16 * 1024 * 1024 + 1
            with self.assertRaisesRegex(RuntimeError, 'exceeds admitted input limit'):
                stages.full_packet(packet)
        stages.r.verify_pin.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
