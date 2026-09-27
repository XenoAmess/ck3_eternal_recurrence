"""Replay bounded shared-helper effect-base provenance without launching CK3."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/extract_dejure_shared_prelookup_effect_base.py"
RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_shared_prelookup_effect_base_1_19_0_6.json"
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json"
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def load_extractor():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("WAR31 shared-helper extractor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    importlib.util.find_spec("capstone") and importlib.util.find_spec("pefile"),
    "static reverse-engineering dependencies are unavailable",
)
class DeJureSharedPrelookupEffectBaseTests(unittest.TestCase):
    def test_wrong_script_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp)
            script = game / "game/common/casus_belli_types/00_dejure_war.txt"
            script.parent.mkdir(parents=True)
            script.write_text("individual_county_de_jure_cb = {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "wrong stock build"):
                load_extractor().extract(game, REQUEST)

    @unittest.skipUnless(GAME.is_dir(), "exact CK3 install unavailable")
    def test_exact_build_replays_effect_base_boundary(self) -> None:
        observed = load_extractor().extract(GAME, REQUEST)
        expected = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(observed, expected)
        self.assertEqual(len(observed["helper"]["effect_base_direct_accesses"]), 2)
        self.assertFalse(observed["helper"]["direct_effect_base_change_scope_access"])
        self.assertFalse(observed["helper"]["direct_effect_base_change_type_write"])
        self.assertIn("actual War31 change+0x268", " ".join(observed["boundary"]["not_proven"]))
        self.assertFalse(observed["boundary"]["ck3_launched"])


if __name__ == "__main__":
    unittest.main()
