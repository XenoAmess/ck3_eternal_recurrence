#!/usr/bin/env python3
"""Offline unit tests for the full-showcase Edge TTS narration pipeline."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_full_agent_showcase as showcase  # noqa: E402


class RecordingCommunicate:
    """A synchronous, network-free stand-in for edge_tts.Communicate."""

    calls: list[dict[str, object]] = []
    payload = b"ID3\x04\x00\x00mock-edge-tts-audio"
    failure: Exception | None = None

    def __init__(self, text: str, voice: str, **settings: str) -> None:
        self.record = {
            "text": text,
            "voice": voice,
            "settings": settings,
            "save_path": None,
        }
        self.calls.append(self.record)

    def save_sync(self, output_path: str) -> None:
        path = Path(output_path)
        self.record["save_path"] = path
        path.write_bytes(self.payload)
        if self.failure is not None:
            raise self.failure


class EdgeTtsNarrationTests(unittest.TestCase):
    def setUp(self) -> None:
        RecordingCommunicate.calls = []
        RecordingCommunicate.payload = b"ID3\x04\x00\x00mock-edge-tts-audio"
        RecordingCommunicate.failure = None
        self.probe_duration = 4.25
        self.probed_paths: list[Path] = []

    def chapter(self, narration: str = "A measured account of present capabilities.") -> showcase.Chapter:
        return showcase.Chapter(
            index=0,
            chapter_id="opening",
            kind="title_card",
            title_en="Capability showcase",
            title_zh="能力展示",
            narration_en=narration,
            subtitle_zh="这是当前能力的如实展示。",
            status_en="CAPABILITY SHOWCASE",
            status_zh="能力展示",
            classification="showcase",
            body_en=[],
            body_zh=[],
            sources=[],
            source_path=None,
            start_seconds=0.0,
            end_seconds=None,
            min_duration_seconds=3.0,
            tail_padding_seconds=0.75,
            fit="contain",
            raw={"id": "opening", "type": "title_card"},
        )

    def fake_probe(self, _ffprobe: Path, path: Path) -> dict[str, object]:
        media_path = Path(path)
        self.assertTrue(media_path.is_file(), f"probe target is missing: {media_path}")
        self.probed_paths.append(media_path)
        duration = str(self.probe_duration)
        return {
            "format": {"duration": duration},
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "duration": duration,
                }
            ],
        }

    @contextlib.contextmanager
    def mocked_tts(self):
        fake_module = types.SimpleNamespace(Communicate=RecordingCommunicate)
        with (
            mock.patch.object(showcase, "edge_tts", fake_module),
            mock.patch.object(showcase, "EDGE_TTS_IMPORT_ERROR", None),
            mock.patch.object(showcase, "EDGE_TTS_VERSION", "7.2.8"),
            mock.patch.object(showcase, "probe_media", side_effect=self.fake_probe),
        ):
            yield

    def synthesize(
        self,
        chapter: showcase.Chapter,
        directory: Path,
        *,
        voice: str = "en-GB-SoniaNeural",
        force: bool = False,
    ) -> None:
        showcase.synthesize_narration(
            chapter,
            directory,
            requested_voice=voice,
            ffprobe=Path("ffprobe"),
            force=force,
        )

    def test_sonia_default_and_cli_override_resolution(self) -> None:
        self.assertEqual(
            "en-GB-SoniaNeural", showcase.resolve_requested_voice(None, {})
        )
        self.assertEqual(
            "en-GB-SoniaNeural",
            showcase.resolve_requested_voice(None, {"voice": "  "}),
        )
        self.assertEqual(
            "en-US-JennyNeural",
            showcase.resolve_requested_voice(None, {"voice": "en-US-JennyNeural"}),
        )
        self.assertEqual(
            "en-GB-LibbyNeural",
            showcase.resolve_requested_voice(
                "  en-GB-LibbyNeural  ", {"voice": "en-US-JennyNeural"}
            ),
        )
        with self.assertRaisesRegex(showcase.ShowcaseError, "voice.*string"):
            showcase.resolve_requested_voice(None, {"voice": 42})

    def test_generation_writes_validated_mp3_metadata_and_duration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            chapter = self.chapter()
            with self.mocked_tts():
                self.synthesize(chapter, directory)

            media_path = directory / "narration.en.mp3"
            metadata_path = directory / "narration.edge-tts.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            call = RecordingCommunicate.calls[0]

            self.assertEqual(RecordingCommunicate.payload, media_path.read_bytes())
            self.assertEqual(
                chapter.narration_en + "\n",
                (directory / "narration.en.txt").read_text(encoding="utf-8"),
            )
            self.assertEqual("en-GB-SoniaNeural", call["voice"])
            self.assertEqual(
                {"rate": "+0%", "volume": "+0%", "pitch": "+0Hz"},
                call["settings"],
            )
            self.assertEqual("edge-tts", metadata["provider"])
            self.assertEqual("7.2.8", metadata["provider_version"])
            self.assertEqual("en-GB-SoniaNeural", metadata["voice"])
            self.assertEqual(call["settings"], metadata["settings"])
            self.assertEqual(showcase._sha256(media_path), metadata["media_sha256"])
            self.assertEqual(media_path, chapter.narration_path)
            self.assertEqual(4.25, chapter.narration_duration_seconds)
            self.assertEqual(5.0, chapter.shot_duration_seconds)
            self.assertEqual("edge-tts", chapter.tts_provider)
            self.assertEqual("7.2.8", chapter.tts_provider_version)
            self.assertFalse(Path(call["save_path"]).exists())

    def test_minimum_duration_still_applies_to_short_narration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            chapter = self.chapter()
            self.probe_duration = 0.5
            with self.mocked_tts():
                self.synthesize(chapter, directory)

            self.assertEqual(0.5, chapter.narration_duration_seconds)
            self.assertEqual(3.0, chapter.shot_duration_seconds)

    def test_matching_cache_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.mocked_tts():
                first = self.chapter()
                self.synthesize(first, directory)
                second = self.chapter()
                self.synthesize(second, directory)

            self.assertEqual(1, len(RecordingCommunicate.calls))
            self.assertEqual(directory / "narration.en.mp3", second.narration_path)
            self.assertEqual(4.25, second.narration_duration_seconds)
            self.assertEqual("en-GB-SoniaNeural", second.voice)

    def test_text_voice_and_force_invalidate_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with self.mocked_tts():
                self.synthesize(self.chapter("First narration."), directory)
                first_fingerprint = json.loads(
                    (directory / "narration.edge-tts.json").read_text(encoding="utf-8")
                )["fingerprint"]

                self.synthesize(self.chapter("Changed narration."), directory)
                second_fingerprint = json.loads(
                    (directory / "narration.edge-tts.json").read_text(encoding="utf-8")
                )["fingerprint"]

                self.synthesize(
                    self.chapter("Changed narration."),
                    directory,
                    voice="en-GB-LibbyNeural",
                )
                third_fingerprint = json.loads(
                    (directory / "narration.edge-tts.json").read_text(encoding="utf-8")
                )["fingerprint"]

                self.synthesize(
                    self.chapter("Changed narration."),
                    directory,
                    voice="en-GB-LibbyNeural",
                    force=True,
                )

            self.assertEqual(4, len(RecordingCommunicate.calls))
            self.assertNotEqual(first_fingerprint, second_fingerprint)
            self.assertNotEqual(second_fingerprint, third_fingerprint)

    def test_provider_version_and_settings_invalidate_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            metadata_path = directory / "narration.edge-tts.json"
            with self.mocked_tts():
                self.synthesize(self.chapter(), directory)
                first_fingerprint = json.loads(
                    metadata_path.read_text(encoding="utf-8")
                )["fingerprint"]

                with mock.patch.object(showcase, "EDGE_TTS_VERSION", "7.2.9"):
                    self.synthesize(self.chapter(), directory)
                version_fingerprint = json.loads(
                    metadata_path.read_text(encoding="utf-8")
                )["fingerprint"]

                with mock.patch.object(showcase, "EDGE_TTS_RATE", "+5%"):
                    self.synthesize(self.chapter(), directory)
                settings_fingerprint = json.loads(
                    metadata_path.read_text(encoding="utf-8")
                )["fingerprint"]

            self.assertEqual(3, len(RecordingCommunicate.calls))
            self.assertNotEqual(first_fingerprint, version_fingerprint)
            self.assertNotEqual(first_fingerprint, settings_fingerprint)

    def test_corrupt_metadata_and_media_hash_are_cache_misses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            metadata_path = directory / "narration.edge-tts.json"
            media_path = directory / "narration.en.mp3"
            with self.mocked_tts():
                self.synthesize(self.chapter(), directory)

                metadata_path.write_text("{not valid json", encoding="utf-8")
                self.synthesize(self.chapter(), directory)

                media_path.write_bytes(b"tampered cached media")
                self.synthesize(self.chapter(), directory)

            self.assertEqual(3, len(RecordingCommunicate.calls))
            self.assertEqual(RecordingCommunicate.payload, media_path.read_bytes())
            self.assertEqual(
                showcase._sha256(media_path),
                json.loads(metadata_path.read_text(encoding="utf-8"))["media_sha256"],
            )

    def test_synthesis_failure_preserves_committed_cache_and_cleans_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            media_path = directory / "narration.en.mp3"
            metadata_path = directory / "narration.edge-tts.json"
            with self.mocked_tts():
                self.synthesize(self.chapter(), directory)
                original_media = media_path.read_bytes()
                original_metadata = metadata_path.read_bytes()
                RecordingCommunicate.payload = (
                    b"ID3\x04\x00\x00complete-replacement-audio"
                )

                with mock.patch.object(
                    showcase,
                    "_atomic_json",
                    side_effect=OSError("metadata write failure"),
                ):
                    with self.assertRaisesRegex(
                        showcase.ShowcaseError, "metadata write failure"
                    ):
                        self.synthesize(self.chapter(), directory, force=True)
                self.assertEqual(original_media, media_path.read_bytes())
                self.assertEqual(original_metadata, metadata_path.read_bytes())
                self.assertFalse(
                    any(directory.glob(".narration.edge-tts.json.*.staged"))
                )
                self.assertFalse(
                    any(directory.glob(".narration.en.mp3.*.rollback"))
                )

                real_replace = showcase.os.replace

                def fail_metadata_commit(source, destination):
                    if (
                        Path(destination) == metadata_path
                        and Path(source).name.endswith(".staged")
                    ):
                        raise OSError("metadata commit failure")
                    return real_replace(source, destination)

                with mock.patch.object(
                    showcase.os,
                    "replace",
                    side_effect=fail_metadata_commit,
                ):
                    with self.assertRaisesRegex(
                        showcase.ShowcaseError, "metadata commit failure"
                    ):
                        self.synthesize(self.chapter(), directory, force=True)
                self.assertEqual(original_media, media_path.read_bytes())
                self.assertEqual(original_metadata, metadata_path.read_bytes())
                self.assertFalse(
                    any(directory.glob(".narration.edge-tts.json.*.staged"))
                )
                self.assertFalse(
                    any(directory.glob(".narration.en.mp3.*.rollback"))
                )

                def interrupt_metadata_commit(source, destination):
                    if (
                        Path(destination) == metadata_path
                        and Path(source).name.endswith(".staged")
                    ):
                        raise KeyboardInterrupt("cancelled during metadata commit")
                    return real_replace(source, destination)

                RecordingCommunicate.payload = (
                    b"ID3\x04\x00\x00interrupted-replacement-audio"
                )
                with mock.patch.object(
                    showcase.os,
                    "replace",
                    side_effect=interrupt_metadata_commit,
                ):
                    with self.assertRaisesRegex(
                        KeyboardInterrupt, "cancelled during metadata commit"
                    ):
                        self.synthesize(self.chapter(), directory, force=True)
                self.assertEqual(original_media, media_path.read_bytes())
                self.assertEqual(original_metadata, metadata_path.read_bytes())
                self.assertFalse(
                    any(directory.glob(".narration.edge-tts.json.*.staged"))
                )
                self.assertFalse(
                    any(directory.glob(".narration.en.mp3.*.rollback"))
                )

                RecordingCommunicate.payload = b"partial replacement"
                RecordingCommunicate.failure = RuntimeError("offline test failure")
                with self.assertRaisesRegex(showcase.ShowcaseError, "offline test failure"):
                    self.synthesize(self.chapter(), directory, force=True)

                failed_temporary = Path(RecordingCommunicate.calls[-1]["save_path"])
                self.assertEqual(original_media, media_path.read_bytes())
                self.assertEqual(original_metadata, metadata_path.read_bytes())
                self.assertFalse(failed_temporary.exists())

                fresh_directory = directory / "fresh"
                fresh_directory.mkdir()
                with self.assertRaisesRegex(showcase.ShowcaseError, "offline test failure"):
                    self.synthesize(self.chapter(), fresh_directory)
                self.assertFalse((fresh_directory / "narration.en.mp3").exists())
                self.assertFalse(
                    (fresh_directory / "narration.edge-tts.json").exists()
                )
                self.assertFalse(
                    Path(RecordingCommunicate.calls[-1]["save_path"]).exists()
                )


class ValidateOnlyTests(unittest.TestCase):
    @staticmethod
    def manifest() -> dict[str, object]:
        return {
            "format_version": 1,
            "chapters": [
                {
                    "id": "opening",
                    "type": "title_card",
                    "title_en": "Capability showcase",
                    "title_zh": "能力展示",
                    "narration_en": "This is a validation-only fixture.",
                    "subtitle_zh": "这是仅验证夹具。",
                    "status": {
                        "en": "CAPABILITY SHOWCASE",
                        "zh": "能力展示",
                        "classification": "showcase",
                    },
                }
            ],
        }

    def test_validate_only_never_constructs_network_tts_client(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "manifest.json"
            output_path = root / "showcase.mp4"
            work_directory = root / "work"
            manifest_path.write_text(
                json.dumps(self.manifest(), ensure_ascii=False), encoding="utf-8"
            )
            args = showcase.parser().parse_args(
                [
                    "--manifest",
                    str(manifest_path),
                    "--output",
                    str(output_path),
                    "--work-dir",
                    str(work_directory),
                    "--validate-only",
                ]
            )
            network_client = mock.Mock(
                side_effect=AssertionError("validate-only attempted Edge TTS network use")
            )
            fake_edge_tts = types.SimpleNamespace(Communicate=network_client)

            with (
                mock.patch.object(showcase, "PIL_IMPORT_ERROR", None),
                mock.patch.object(showcase, "EDGE_TTS_IMPORT_ERROR", None),
                mock.patch.object(showcase, "edge_tts", fake_edge_tts),
                mock.patch.object(showcase, "find_program", return_value=Path("mock.exe")),
                mock.patch.object(showcase, "find_fonts", return_value=mock.sentinel.fonts),
                mock.patch.object(showcase, "preflight_video_sources"),
                mock.patch.object(showcase, "prepare_subtitle_layouts"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = showcase.build(args)

            network_client.assert_not_called()
            self.assertEqual(output_path.resolve(), result[0])
            self.assertFalse(output_path.exists())
            self.assertFalse(work_directory.exists())


if __name__ == "__main__":
    unittest.main()
