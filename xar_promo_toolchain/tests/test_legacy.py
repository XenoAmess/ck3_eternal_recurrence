from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parent
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))

import build_full_agent_showcase as showcase  # noqa: E402
import xar_promo.legacy as legacy  # noqa: E402
from xar_promo.media import ffprobe_command  # noqa: E402


class LegacyMediaDelegationTests(unittest.TestCase):
    def test_probe_keeps_legacy_dict_while_using_package_command_and_parser(self) -> None:
        ffprobe = Path("D:/media tools/ffprobe.exe")
        media = Path("D:/captures/a clip.mkv")
        raw = '{"streams":[],"format":{"duration":"3.5"}}'
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=raw, stderr=""
        )
        with mock.patch.object(
            showcase, "run_checked", return_value=completed
        ) as run_checked:
            result = showcase.probe_media(ffprobe, media)

        self.assertEqual(
            {"streams": [], "format": {"duration": "3.5"}}, result
        )
        run_checked.assert_called_once_with(
            ffprobe_command(ffprobe, media),
            cwd=None,
            action=f"probing media {media}",
        )

    def test_package_parse_error_stays_inside_legacy_error_boundary(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not-json", stderr=""
        )
        with (
            mock.patch.object(showcase, "run_checked", return_value=completed),
            self.assertRaisesRegex(showcase.ShowcaseError, "ffprobe returned invalid JSON"),
        ):
            showcase.probe_media(Path("ffprobe"), Path("broken.mp4"))


class LegacyProjectionTests(unittest.TestCase):
    def test_subtitle_and_time_edge_cases_keep_legacy_bytes(self) -> None:
        self.assertEqual("0:00:00.00", legacy.compatible_ass_timestamp(0.005))
        self.assertEqual("0:00:00.00", legacy.compatible_ass_timestamp(-1.0))
        self.assertEqual(
            r"slash\\ brace\{x\}\Nnext" + "\t",
            legacy.compatible_ass_escape("slash\\ brace{x}\nnext\t"),
        )
        self.assertEqual("-1.000000", legacy.compatible_seconds(-1.0))

    def test_concat_projection_matches_legacy_relative_layout(self) -> None:
        build = Path("D:/work/showcase")
        self.assertEqual(
            "file '001-opening/segment.mp4'\nfile '002-proof/segment.mp4'\n",
            legacy.compatible_concat_manifest(
                (
                    build / "001-opening" / "segment.mp4",
                    build / "002-proof" / "segment.mp4",
                ),
                build_directory=build,
            ),
        )

    def test_standard_timestamp_reaches_the_generic_delegate(self) -> None:
        with mock.patch.object(
            legacy, "ass_timestamp", return_value="0:00:01.25"
        ) as delegated:
            self.assertEqual(
                "0:00:01.25", legacy.compatible_ass_timestamp(1.25)
            )
        delegated.assert_called_once_with(1.25)

    def test_pipeline_projection_is_real_and_strictly_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work_directory = Path(temporary) / "must-not-be-created"
            result = legacy.validate_legacy_pipeline_projection(
                (
                    legacy.LegacyPipelineSegment(
                        segment_id="旧入口 / opening",
                        visual_kind="generated-card",
                        source_path=None,
                        subtitle_tracks={"zh-CN": "正文", "en": "Body"},
                        duration_seconds=2.5,
                    ),
                    legacy.LegacyPipelineSegment(
                        segment_id="captured",
                        visual_kind="video",
                        # The legacy adapter owns source normalization.  The
                        # projection must not inspect or rewrite this path.
                        source_path=Path("not-a-generic-visual-name.json"),
                        subtitle_tracks={"zh-CN": "实机", "en": "Live"},
                        duration_seconds=3.0,
                        start_seconds=1.25,
                    ),
                ),
                work_directory=work_directory,
                ffmpeg=Path("D:/media tools/ffmpeg.exe"),
                width=2560,
                height=1440,
                fps=30,
                crf=18,
                render_preset="medium",
            )

            self.assertEqual("validated", result.status)
            self.assertTrue(result.validate_only)
            self.assertFalse(work_directory.exists())


if __name__ == "__main__":
    unittest.main()
