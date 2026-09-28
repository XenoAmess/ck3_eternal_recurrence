"""Bind current A05/A01 cards and retain exact historical sidecars."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.episode_two_second_half import (  # noqa: E402
    FORMAL_CARD_INDEX_SHA, FORMAL_CARD_SHA,
    HISTORICAL_004_CARD_SHA, HISTORICAL_024_CARD_SHA, HISTORICAL_085_CARD_SHA,
    _card_replays, _formal_card_bytes_gate, _sha, _synthetic_flag, editorial_check,
)


PROJECT = Path(__file__).resolve().parents[1] / "episode-02-battle-second-half"
CARDS = PROJECT / "cards"


class EpisodeTwoCardIndexTest(unittest.TestCase):
    def test_a05_formal_card_and_024_sidecar_are_distinct(self):
        result = editorial_check(PROJECT / "project" / "promo-project.json",
                                 PROJECT / "narration-script-draft.md", CARDS)
        fact = json.loads((CARDS / "e2-09-a05-writer-facts-20260928.json").read_text(
            encoding="utf-8"))
        self.assertEqual(result["replay_by_card"]["E2-09"], "A05")
        self.assertEqual(result["replay_by_card"]["E2-02"], "A05")
        self.assertEqual(result["replay_by_card"]["E2-03"], "A05")
        self.assertEqual(result["replay_by_card"]["E2-06"], "A01")
        self.assertEqual(result["replay_by_card"]["E2-07"], "A01")
        self.assertEqual(result["card_sha256"]["E2-09"],
                         fact["artifacts"]["current_a05_card"]["sha256"])
        self.assertEqual(_sha(CARDS / "e2-09-calculation.svg"), HISTORICAL_024_CARD_SHA)
        self.assertNotEqual(result["card_sha256"]["E2-09"], HISTORICAL_024_CARD_SHA)
        for card_id, digest in HISTORICAL_004_CARD_SHA.items():
            self.assertEqual(_sha(CARDS / f"{card_id.lower()}-calculation.svg"), digest)
            self.assertNotEqual(result["card_sha256"][card_id], digest)
        for card_id, digest in HISTORICAL_085_CARD_SHA.items():
            self.assertEqual(_sha(CARDS / f"{card_id.lower()}-calculation.svg"), digest)
            self.assertNotEqual(result["card_sha256"][card_id], digest)

    def test_024_replay_cannot_become_formal_terminal(self):
        index = json.loads((CARDS / "calculation-cards.json").read_text(encoding="utf-8"))
        terminal = next(row for row in index["cards"] if row["id"] == "E2-09")
        terminal["replay"] = "024"
        with self.assertRaisesRegex(ValueError, "current A05/A01"):
            _card_replays(index)

    def test_a05_pursuit_requires_all_native_days_and_parity(self):
        original = json.loads((CARDS / "calculation-cards.json").read_text(encoding="utf-8"))
        for field in ("source_day28_control_sha256", "source_day29_control_sha256",
                      "source_day30_control_sha256", "source_day31_control_sha256",
                      "source_pursuit_parity_sha256"):
            index = json.loads(json.dumps(original))
            index["replays"]["A05"][field] = "0" * 64
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "pursuit"):
                _card_replays(index)
        index = json.loads(json.dumps(original))
        next(row for row in index["cards"] if row["id"] == "E2-03")["source_receipt_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "E2-03 pursuit"):
            _card_replays(index)

    def test_formal_production_rejects_card_or_index_drift(self):
        _formal_card_bytes_gate(FORMAL_CARD_INDEX_SHA, FORMAL_CARD_SHA)
        with self.assertRaisesRegex(ValueError, "card index changed"):
            _formal_card_bytes_gate("0" * 64, FORMAL_CARD_SHA)
        cards = dict(FORMAL_CARD_SHA)
        cards["E2-03"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SVG bytes changed"):
            _formal_card_bytes_gate(FORMAL_CARD_INDEX_SHA, cards)

    def test_synthetic_flag_cannot_skip_formal_gate_with_truthy_nonboolean(self):
        self.assertFalse(_synthetic_flag({}))
        self.assertTrue(_synthetic_flag({"synthetic": True}))
        for value in ("false", 1, [], None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "boolean"):
                _synthetic_flag({"synthetic": value})

    def test_a05_name_cannot_hide_an_old_writer_or_other_run(self):
        original = json.loads((CARDS / "calculation-cards.json").read_text(encoding="utf-8"))
        bad_values = {
            "source_terminal_sha256": original["replays"]["024"]["source_terminal_sha256"],
            "source_save_sha256": "0" * 64,
            "source_post_snapshot_sha256": "0" * 64,
        }
        for field, value in bad_values.items():
            index = json.loads(json.dumps(original))
            index["replays"]["A05"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "exact writer"):
                _card_replays(index)


if __name__ == "__main__":
    unittest.main()
