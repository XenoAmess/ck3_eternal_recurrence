"""Exact patch clock selection with in-memory native layout replay."""

import unittest
from unittest.mock import patch
import ck3_native_clock_reader as clock
from test_ck3_native_clock_reader import MemoryFixture

SHA = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"


class PatchClockTests(unittest.TestCase):
    def test_patch_identity_header_and_reviewed_layout_replay(self):
        old, new = clock.source_contract(), clock.source_contract("1.20.0.3")
        self.assertEqual(new["executable_sha256"], SHA)
        self.assertEqual(new["identity_header_path"], "include/xar_bridge/ck3_12003.hpp")
        self.assertEqual(new["layout_source_path"], "src/ck3_12002.cpp")
        for key in ("jomini_slot", "game_slot", "player_manager", "date_offset", "speed_offset", "paused_offset"):
            self.assertEqual(new[key], old[key])
        fixture = MemoryFixture()
        fixture.close = lambda: None
        with patch.object(clock, "WindowsReadOnlyMemory", return_value=fixture):
            result = clock.read_live_clock(11, "fixture.exe", SHA, "1.20.0.3")
        self.assertEqual(result["source_contract"], new)
        self.assertEqual((result["date_raw"], result["played_character_id"]), (53169336, 29829))

    def test_mixed_patch_identity_rejected_before_memory_open(self):
        with patch.object(clock, "WindowsReadOnlyMemory") as reader:
            with self.assertRaisesRegex(RuntimeError, "exact"):
                clock.read_live_clock(11, "fixture.exe", "0" * 64, "1.20.0.3")
            reader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
