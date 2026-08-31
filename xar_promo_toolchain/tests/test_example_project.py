from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from xar_promo.errors import ManifestError
from xar_promo.project import load_document, validate_profile
from xar_promo.tts import TtsRequest


TOOLCHAIN_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = TOOLCHAIN_ROOT / "examples" / "minimal"
PROJECT_CONFIG = EXAMPLE_ROOT / "promo-project.json"
AUTHORING_SETTINGS = EXAMPLE_ROOT / "authoring-settings.json"


class MinimalExampleProjectTests(unittest.TestCase):
    def test_native_authoring_config_and_real_inputs_are_consistent(self) -> None:
        loaded = load_document(PROJECT_CONFIG)
        validate_profile(loaded, "authoring")
        self.assertEqual("project-config-v1", loaded.source_format)
        self.assertIsNotNone(loaded.config)
        project = loaded.config
        if project is None:
            self.fail("native example did not load as a ProjectConfig")

        settings = json.loads(AUTHORING_SETTINGS.read_text(encoding="utf-8"))
        self.assertEqual(project.adapter, settings["adapter"])
        self.assertEqual(project.preset, settings["preset"])
        self.assertEqual(project.narration_locale, settings["locales"]["narration"])
        self.assertEqual(
            list(project.subtitle_locales), settings["locales"]["subtitles"]
        )

        voice = settings["voice"]
        first_cue = project.chapters[0].cues[0]
        request = TtsRequest(
            text=first_cue.narration[project.narration_locale],
            voice=voice["name"],
            rate=voice["rate"],
            pitch=voice["pitch"],
            volume=voice["volume"],
            audio_format=voice["audio_format"],
        )
        self.assertEqual("zh-CN-XiaoxiaoNeural", request.voice)
        self.assertEqual("edge-tts", voice["provider"])

        input_paths: dict[str, Path] = {}
        for role, relative in settings["inputs"].items():
            candidate = (EXAMPLE_ROOT / relative).resolve()
            self.assertTrue(candidate.is_relative_to(EXAMPLE_ROOT.resolve()))
            self.assertTrue(candidate.is_file(), f"missing {role} input: {candidate}")
            self.assertGreater(candidate.stat().st_size, 0)
            input_paths[role] = candidate

        script = input_paths["script"].read_text(encoding="utf-8")
        for chapter in project.chapters:
            for cue in chapter.cues:
                for text in (*cue.narration.values(), *cue.subtitles.values()):
                    self.assertIn(text, script)
        visual_root = ET.parse(input_paths["visual"]).getroot()
        self.assertEqual("{http://www.w3.org/2000/svg}svg", visual_root.tag)

    def test_example_claims_authoring_only_and_contains_no_run_evidence(self) -> None:
        loaded = load_document(PROJECT_CONFIG)
        self.assertIsNotNone(loaded.config)
        project = loaded.config
        if project is None:
            self.fail("native example did not load as a ProjectConfig")
        self.assertTrue(all(chapter.state == "planned" for chapter in project.chapters))
        self.assertFalse(list(EXAMPLE_ROOT.rglob("run-manifest.json")))
        self.assertFalse(list(EXAMPLE_ROOT.rglob("*signoff*")))
        self.assertFalse(list(EXAMPLE_ROOT.rglob("*audit*")))
        with self.assertRaisesRegex(
            ManifestError, "release profile requires a native run manifest"
        ):
            validate_profile(loaded, "release")


if __name__ == "__main__":
    unittest.main()
