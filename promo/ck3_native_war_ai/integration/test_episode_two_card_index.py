"""Keep A05 as the formal terminal card and 024 as an exact historical sidecar."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.episode_two_second_half import (  # noqa: E402
    HISTORICAL_024_CARD_SHA, HISTORICAL_085_CARD_SHA,
    _card_replays, _sha, editorial_check,
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
        self.assertEqual(result["replay_by_card"]["E2-06"], "A01")
        self.assertEqual(result["replay_by_card"]["E2-07"], "A01")
        self.assertEqual(result["card_sha256"]["E2-09"],
                         fact["artifacts"]["current_a05_card"]["sha256"])
        self.assertEqual(_sha(CARDS / "e2-09-calculation.svg"), HISTORICAL_024_CARD_SHA)
        self.assertNotEqual(result["card_sha256"]["E2-09"], HISTORICAL_024_CARD_SHA)
        for card_id, digest in HISTORICAL_085_CARD_SHA.items():
            self.assertEqual(_sha(CARDS / f"{card_id.lower()}-calculation.svg"), digest)
            self.assertNotEqual(result["card_sha256"][card_id], digest)

    def test_024_replay_cannot_become_formal_terminal(self):
        index = json.loads((CARDS / "calculation-cards.json").read_text(encoding="utf-8"))
        terminal = next(row for row in index["cards"] if row["id"] == "E2-09")
        terminal["replay"] = "024"
        with self.assertRaisesRegex(ValueError, "current A01/A05"):
            _card_replays(index)

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
