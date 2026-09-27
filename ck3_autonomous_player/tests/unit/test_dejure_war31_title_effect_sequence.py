"""No-launch contract for the R0221 de-jure title-effect script sequence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/extract_dejure_war31_title_effect_sequence.py"
RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_war31_title_effect_sequence_1_19_0_6.json"
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0221-WAR31-20260927.json"
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def _extractor():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeJureWar31TitleEffectSequenceTests(unittest.TestCase):
    def test_changed_stock_script_fails_closed(self) -> None:
        extractor = _extractor()
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            source = game / extractor.SCRIPT_PATH
            source.parent.mkdir(parents=True)
            source.write_text("individual_county_de_jure_cb = {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "wrong stock build"):
                extractor.extract(game, REQUEST)

    def test_direct_child_parser_does_not_promote_nested_setup(self) -> None:
        extractor = _extractor()
        nested = (
            "\n every_in_list = {\n  list = target_titles\n"
            "  setup_de_jure_cb = { title = scope:target }\n }\n"
            " resolve_title_and_vassal_change = scope:change\n"
        )
        direct_keys = [row[0] for row in extractor._direct_statements(nested)]
        self.assertEqual(direct_keys, ["every_in_list", "resolve_title_and_vassal_change"])

    @unittest.skipUnless(
        (GAME / "game/common/casus_belli_types/00_dejure_war.txt").is_file(),
        "exact stock game script is unavailable",
    )
    def test_exact_stock_script_matches_static_receipt(self) -> None:
        extractor = _extractor()
        observed = extractor.extract(GAME, REQUEST)
        self.assertEqual(observed, json.loads(RECEIPT.read_text(encoding="utf-8")))
        self.assertTrue(observed["setup_is_outside_target_loop"])
        self.assertFalse(observed["explicit_change_title_holder_in_on_victory"])
        self.assertFalse(observed["effect_invoked"])
        self.assertEqual(observed["declared_target_title_ids_in_request"], [2128])


if __name__ == "__main__":
    unittest.main()
