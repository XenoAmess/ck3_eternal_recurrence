"""Replay the WAR31 conquest change-type construction receipt."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/extract_dejure_conquest_change_type.py"
RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_conquest_change_type_1_19_0_6.json"
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json"
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def load_extractor():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("WAR31 extractor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    importlib.util.find_spec("capstone") and importlib.util.find_spec("pefile"),
    "static reverse-engineering dependencies are unavailable",
)
class DeJureConquestChangeTypeTests(unittest.TestCase):
    def test_wrong_script_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = Path(temp)
            script = game / "game/common/casus_belli_types/00_dejure_war.txt"
            script.parent.mkdir(parents=True)
            script.write_text("individual_county_de_jure_cb = {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "wrong stock build"):
                load_extractor().extract(game, REQUEST)

    def test_wrong_request_fails_closed(self) -> None:
        if not GAME.is_dir():
            self.skipTest("exact CK3 install unavailable")
        with tempfile.TemporaryDirectory() as temp:
            wrong = Path(temp) / "request.json"
            changed = json.loads(REQUEST.read_text(encoding="utf-8"))
            changed["reproduction"]["war_id"] = 0
            wrong.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "R0221 does not match"):
                load_extractor().extract(GAME, wrong)

    @unittest.skipUnless(GAME.is_dir(), "exact CK3 install unavailable")
    def test_exact_build_replays_initial_type_and_unknown_resolve_value(self) -> None:
        observed = load_extractor().extract(GAME, REQUEST)
        expected = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(observed, expected)
        self.assertEqual(observed["create_effect"]["conquest_token_index"], 0)
        self.assertEqual(observed["native_change_constructor"]["constructed_type"], 0)
        self.assertIsNone(observed["boundary"]["runtime_change_type_at_resolve"])
        self.assertFalse(observed["boundary"]["ck3_launched"])


if __name__ == "__main__":
    unittest.main()
