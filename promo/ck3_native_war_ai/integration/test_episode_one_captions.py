"""Regression for subtitles crossing a gameplay-to-explainer-card cut."""

import unittest

from war_ai_promo.captions import subtitle_document


class EpisodeOneCaptionTest(unittest.TestCase):
    def test_gameplay_to_card_cut_moves_subtitles_below_title(self):
        row = {
            "shot_title": "画面始终跟着战场",
            "visual_kind": "gameplay",
            "gameplay_seconds": 13,
            "speech_duration_seconds": 50,
            "duration_seconds": 52,
            "zh": "先看原版战场。接着解释镜头怎样保持战斗标记可见。" * 4,
            "en": "The camera follows the battle. The evidence is retained.",
        }
        document = subtitle_document(row)
        styles = {line.split(",")[0].removeprefix("Style: "): line.split(",")
                  for line in document.splitlines() if line.startswith("Style: ")}
        self.assertEqual(styles["ChineseGameplay"][-5], "8")
        self.assertEqual(styles["ChineseCard"][-5], "2")
        dialogues = [line for line in document.splitlines() if line.startswith("Dialogue: ")]
        self.assertTrue(any(",ChineseGameplay," in line for line in dialogues))
        self.assertTrue(any(",ChineseCard," in line for line in dialogues))
        self.assertFalse(any(",English," in line for line in dialogues))


if __name__ == "__main__":
    unittest.main()
