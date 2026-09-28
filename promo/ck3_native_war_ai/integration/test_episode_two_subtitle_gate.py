"""Subtitle source words and timing must survive the Episode 2 layout."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import war_ai_promo  # noqa: E402

war_ai_promo.__path__.insert(0, str(Path(__file__).resolve().parent / "src" / "war_ai_promo"))
from war_ai_promo.episode_two_second_half import _rendered_subtitle_gate  # noqa: E402


class EpisodeTwoSubtitleGateTest(unittest.TestCase):
    def setUp(self):
        self.row = {
            "id": "opening", "zh": "甲乙。", "en": "A B.",
            "speech_duration_seconds": 2.0, "duration_seconds": 3.0,
            "sentence_boundaries": [{"type": "SentenceBoundary", "offset": 0,
                                     "duration": 20_000_000, "text": "甲乙。"}],
        }

    def test_source_text_survives_bilingual_caption_grouping(self):
        zh_count, en_count = _rendered_subtitle_gate(self.row, 2.0)
        self.assertGreater(zh_count, 0)
        self.assertGreater(en_count, 0)

    def test_event_text_tamper_and_short_mp3_are_rejected(self):
        changed = {**self.row, "sentence_boundaries": [
            {**self.row["sentence_boundaries"][0], "text": "丙乙。"}]}
        with self.assertRaisesRegex(ValueError, "lost spoken"):
            _rendered_subtitle_gate(changed, 2.0)
        with self.assertRaisesRegex(ValueError, "exceeds measured MP3"):
            _rendered_subtitle_gate(self.row, 1.95)

    def test_legacy_gameplay_layout_cannot_drop_english(self):
        with self.assertRaisesRegex(ValueError, "bilingual subtitle layout"):
            _rendered_subtitle_gate({**self.row, "visual_kind": "gameplay"}, 2.0)


if __name__ == "__main__":
    unittest.main()
