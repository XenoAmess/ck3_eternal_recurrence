"""No-launch replay of the exact-build War 31 scripted truce receipt."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/extract_dejure_war31_truce_script.py"
RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_war31_truce_script_1_19_0_6.json"
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json"
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def _extractor():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeJureWar31TruceScriptTests(unittest.TestCase):
    def test_wrong_source_fails_closed_before_parsing(self) -> None:
        extractor = _extractor()
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            source = game / "game/common/casus_belli_types/00_dejure_war.txt"
            source.parent.mkdir(parents=True)
            source.write_text("individual_county_de_jure_cb = {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "wrong stock build or changed game script"):
                extractor.extract(game, REQUEST)

    @unittest.skipUnless(
        (GAME / "game/common/casus_belli_types/00_dejure_war.txt").is_file(),
        "exact stock game scripts are unavailable",
    )
    def test_exact_scripts_and_R0221_match_static_receipt(self) -> None:
        extractor = _extractor()
        observed = extractor.extract(GAME, REQUEST)
        expected = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(observed, expected)
        truce = observed["scripted_on_victory"]
        self.assertEqual((truce["truce_owner_character_id"], truce["toward_character_id"]), (30097, 29829))
        self.assertIsNone(observed["actual_evaluated_days"])
        self.assertIsNone(observed["actual_expiry_date_raw"])

    @unittest.skipUnless(
        (GAME / "game/common/casus_belli_types/00_dejure_war.txt").is_file(),
        "exact stock game scripts are unavailable",
    )
    def test_changed_request_identity_fails_closed(self) -> None:
        extractor = _extractor()
        with tempfile.TemporaryDirectory() as temporary:
            wrong_request = Path(temporary) / "request.json"
            request = json.loads(REQUEST.read_text(encoding="utf-8"))
            request["reproduction"]["player_side"] = "attacker"
            wrong_request.write_text(json.dumps(request), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not the frozen primary-defender War 31 frame"):
                extractor.extract(GAME, wrong_request)


if __name__ == "__main__":
    unittest.main()
