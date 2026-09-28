"""English subtitle source must bind each chapter's exact Chinese spoken text."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from prepare_production_inputs import _english_source
from war_ai_promo.episode_two_second_half import CHAPTER_IDS, script_chapters
from war_ai_promo.episode_two_subtitle_contract import identity


ROOT = Path(__file__).resolve().parent


class EnglishSubtitleGateTest(unittest.TestCase):
    def test_each_translation_is_bound_to_its_original_chapter(self):
        narration = script_chapters(ROOT / "narration-script-draft.md")
        rows = [{"id": chapter,
                 "source_zh_sha256": hashlib.sha256(narration[chapter].encode("utf-8")).hexdigest().upper(),
                 "en": f"English translation for {chapter}."}
                for chapter in CHAPTER_IDS]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "english.json"

            def check():
                source.write_text(json.dumps({
                    "schema": "ck3-war-ai.episode02.english-subtitles.v1",
                    "status": "translation-source-reviewed-not-video-reviewed",
                    "chapters": rows,
                }), encoding="utf-8")
                return _english_source({"english_subtitles": {
                    "source": str(source), **identity(source)}}, narration)

            _, translated = check()
            self.assertEqual(translated["terminal"], "English translation for terminal.")
            rows[4]["source_zh_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "terminal English subtitle"):
                check()
            rows[4]["source_zh_sha256"] = hashlib.sha256(
                narration["terminal"].encode("utf-8")).hexdigest().upper()
            rows.pop()
            with self.assertRaisesRegex(ValueError, "six source-reviewed chapters"):
                check()


if __name__ == "__main__":
    unittest.main()
