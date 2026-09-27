"""Replay the exact-build de-jure eight-byte pair append without launching CK3."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/extract_dejure_pair_append_boundary.py"
RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_pair_append_boundary_1_19_0_6.json"
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json"
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def load_extractor():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("WAR31 pair append extractor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    importlib.util.find_spec("capstone") and importlib.util.find_spec("pefile"),
    "static reverse-engineering dependencies are unavailable",
)
class DeJurePairAppendBoundaryTests(unittest.TestCase):
    def test_wrong_script_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp)
            script = game / "game/common/casus_belli_types/00_dejure_war.txt"
            script.parent.mkdir(parents=True)
            script.write_text("individual_county_de_jure_cb = {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "wrong stock build"):
                load_extractor().extract(game, REQUEST)

    @unittest.skipUnless(GAME.is_dir(), "exact CK3 install unavailable")
    def test_exact_build_replays_bounded_pair_write_set(self) -> None:
        observed = load_extractor().extract(GAME, REQUEST)
        expected = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(observed, expected)
        self.assertEqual(observed["append_helper"]["base_write_offsets"],
                         ["0x8", "0x0", "0xC", "0xC"])
        self.assertFalse(observed["parent_offsets_if_no_alias"]["direct_descriptor_write_overlaps_type"])
        self.assertIn("actual War31 change+0x268", " ".join(observed["boundary"]["not_proven"]))
        self.assertFalse(observed["boundary"]["ck3_launched"])


if __name__ == "__main__":
    unittest.main()
