from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from xar_promo.model import (
    ArtifactPolicy,
    ConfigBinding,
    RunManifest,
    SourceRecord,
)
from xar_promo.project import load_document

from rmtm_promo.composer import TOTAL_SECONDS, _music_ducks, _subtitle_document, compose
from rmtm_promo.components import adapter_factory, preset_factory


PROMO = Path(__file__).resolve().parents[2]
CONFIG = PROMO / "promo-project.json"
POLICY = PROMO / "promo-policy.json"


def _source(path: Path, artifact_id: str, media_type: str) -> SourceRecord:
    payload = path.read_bytes()
    return SourceRecord(
        artifact_id=artifact_id,
        collection="raw",
        role="test-input",
        path=path.name,
        label=artifact_id,
        bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest().upper(),
        media_type=media_type,
    )


class ReclaimPromoTests(unittest.TestCase):
    def test_policy_timeline_and_terms_are_frozen(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        sections = policy["timeline"]["sections"]
        self.assertEqual([(row["start"], row["end"]) for row in sections], [(0,6),(6,15),(15,27),(27,39),(39,51),(51,63),(63,75),(75,83),(83,88),(88,96)])
        joined = json.dumps(policy, ensure_ascii=False)
        self.assertIn("溥天之下", joined)
        self.assertNotIn("天下归心", " ".join(policy["terminology"]["required"]))
        self.assertEqual(policy["narration"]["voice"], "zh-CN-XiaoxiaoNeural")

    def test_duck_windows_do_not_overlap_and_tail_fade_is_explicit(self) -> None:
        windows = _music_ducks()
        self.assertTrue(all(left.end_seconds <= right.start_seconds for left, right in zip(windows, windows[1:])))
        self.assertEqual(windows[6].gain_db, -9.5)

    def test_subtitles_use_approved_copy(self) -> None:
        document = _subtitle_document(None, None, workdir=Path("."))
        self.assertIn("重整河山", document)
        self.assertIn("溥天之下 / All Under Heaven", document)
        self.assertIn("一朝失鹿，尚可再兴", document)
        self.assertNotIn("天下归心", document)

    def test_composer_builds_one_gapless_master(self) -> None:
        config = load_document(CONFIG).config
        self.assertIsNotNone(config)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            visual = root / "visual.mp4"
            narration = root / "narration.wav"
            music = root / "music.wav"
            visual.write_bytes(b"video")
            narration.write_bytes(b"narration")
            music.write_bytes(b"music")
            config_bytes = CONFIG.read_bytes()
            run = RunManifest(
                run_id="test-run",
                project_config=ConfigBinding(
                    path="promo-project.json",
                    bytes=len(config_bytes),
                    sha256=hashlib.sha256(config_bytes).hexdigest().upper(),
                ),
                artifact_policy=ArtifactPolicy(
                    strategy="content-addressed-sha256",
                    raw_directory="artifacts/raw/sha256",
                    derived_directory="artifacts/derived/sha256",
                    manifest_history_directory="manifest-history",
                    preserve_process_material=True,
                ),
                phase_history=(),
                artifacts=(
                    _source(visual, "visual-master-a01", "video/mp4"),
                    _source(narration, "narration-master-a01", "audio/wav"),
                    _source(music, "bgm-a03-source", "audio/wav"),
                ),
                audits=(),
                signoffs=(),
            )
            invocation = compose(
                config,
                run,
                config_path=CONFIG,
                run_path=root / "run-manifest.json",
                workdir=root / "attempt",
                adapter_factory=adapter_factory,
                preset_factory=preset_factory,
                validate_only=True,
            )
            segment = invocation.draft.segments[0]
            self.assertEqual(segment.render_options.duration_seconds, TOTAL_SECONDS)
            self.assertEqual([stem.stem_id for stem in segment.audio_mix.stems], ["narration", "a03"])
            self.assertFalse(segment.audio_mix.normalize)
            self.assertEqual(segment.audio_mix.stems[1].fade_out_seconds, 8.0)


if __name__ == "__main__":
    unittest.main()
