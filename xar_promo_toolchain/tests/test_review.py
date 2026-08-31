from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from xar_promo.media import parse_ffprobe_json  # noqa: E402
from xar_promo.process import (  # noqa: E402
    CommandFailedError,
    CommandResult,
    CommandSpec,
    run_command,
)
from xar_promo.review import (  # noqa: E402
    PENDING_REVIEW_STATE,
    REVIEW_TEMPLATE_KIND,
    ReviewPackagePlan,
    ReviewPlanError,
    execute_review_frame_plan,
    normalize_storyboard_timeline,
    plan_review_package,
    write_review_template,
)


def _probe() -> object:
    return parse_ffprobe_json(
        json.dumps(
            {
                "streams": [
                    {
                        "index": 0,
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1920,
                        "height": 1080,
                        "avg_frame_rate": "2/1",
                    },
                    {
                        "index": 1,
                        "codec_type": "audio",
                        "codec_name": "aac",
                        "sample_rate": "48000",
                        "channels": 2,
                    },
                    {
                        "index": 2,
                        "codec_type": "subtitle",
                        "codec_name": "ass",
                        "tags": {"language": "locale-a", "title": "Primary"},
                    },
                    {
                        "index": 3,
                        "codec_type": "subtitle",
                        "codec_name": "subrip",
                        "tags": {"language": "locale-b"},
                    },
                ],
                "format": {"duration": "10", "format_name": "mov,mp4"},
            }
        )
    )


def _timeline() -> dict[str, object]:
    return {
        "boundary_seconds": [5],
        "chapters": [
            {
                "id": "opening",
                "start_seconds": 0,
                "end_seconds": 4,
                "boundary_seconds": [2],
            },
            {
                "id": "feature",
                "start_seconds": 4,
                "end_seconds": 10,
                "boundary_seconds": [7],
            },
        ],
    }


class ReviewPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.artifact = self.root / "final movie.mp4"
        self.artifact.write_bytes(b"deterministic finished movie")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _plan(self) -> ReviewPackagePlan:
        return plan_review_package(
            ffmpeg="vendor/custom-ffmpeg",
            artifact_path=self.artifact,
            probe=_probe(),
            storyboard_timeline=_timeline(),
            output_directory=self.root / "review",
            audit_directory=self.root / "audit",
        )

    def test_plan_is_deterministic_and_preserves_injected_command_token(self) -> None:
        first = self._plan()
        second = self._plan()
        self.assertEqual(first, second)
        self.assertEqual(len(first.frames), 10)
        self.assertEqual(
            [f"{frame.timestamp_seconds:.6f}" for frame in first.frames],
            [
                "0.000000",
                "1.500000",
                "2.000000",
                "3.500000",
                "4.000000",
                "4.500000",
                "5.000000",
                "6.500000",
                "7.000000",
                "9.500000",
            ],
        )
        first_frame = first.frames[0]
        self.assertEqual(first_frame.command.spec.argv[0], "vendor/custom-ffmpeg")
        self.assertEqual(first_frame.command.spec.cwd, None)
        self.assertIn("-frames:v", first_frame.command.spec.argv)
        self.assertEqual(
            first_frame.command.spec.partial_artifacts,
            (first_frame.partial_output,),
        )
        self.assertIn("artifact-first", first_frame.roles)
        self.assertIn("chapter-start", first_frame.roles)
        self.assertEqual(first_frame.chapter_ids, ("opening",))

    def test_summary_binds_hash_media_shape_codecs_and_subtitle_tracks(self) -> None:
        summary = self._plan().artifact_summary
        self.assertEqual(
            summary["sha256"],
            hashlib.sha256(self.artifact.read_bytes()).hexdigest().upper(),
        )
        self.assertEqual(summary["bytes"], self.artifact.stat().st_size)
        self.assertEqual(summary["duration_seconds"], "10.000000")
        self.assertEqual(summary["resolution"], {"width": 1920, "height": 1080})
        self.assertEqual(summary["video_tracks"][0]["codec"], "h264")
        self.assertEqual(summary["audio_tracks"][0]["codec"], "aac")
        self.assertEqual(
            summary["subtitle_tracks"],
            [
                {
                    "index": 2,
                    "codec": "ass",
                    "language": "locale-a",
                    "title": "Primary",
                },
                {
                    "index": 3,
                    "codec": "subrip",
                    "language": "locale-b",
                    "title": None,
                },
            ],
        )

    def test_aac_padding_does_not_seek_past_primary_video_stream(self) -> None:
        probe = parse_ffprobe_json(
            json.dumps(
                {
                    "streams": [
                        {
                            "index": 0,
                            "codec_type": "video",
                            "codec_name": "h264",
                            "width": 640,
                            "height": 360,
                            "avg_frame_rate": "24/1",
                            "duration": "3.000000",
                        },
                        {
                            "index": 1,
                            "codec_type": "audio",
                            "codec_name": "aac",
                            "duration": "3.021333",
                        },
                    ],
                    "format": {"duration": "3.021333", "format_name": "mov,mp4"},
                }
            )
        )
        plan = plan_review_package(
            ffmpeg="injected-ffmpeg",
            artifact_path=self.artifact,
            probe=probe,
            storyboard_timeline={
                "boundary_seconds": [1.5],
                "chapters": [
                    {"id": "first", "start_seconds": 0, "end_seconds": 1.5},
                    {
                        "id": "second",
                        "start_seconds": 1.5,
                        "end_seconds": 3.021333,
                    },
                ],
            },
            output_directory=self.root / "aac-padding-review",
            audit_directory=self.root / "aac-padding-audit",
        )

        self.assertEqual(
            plan.artifact_summary["duration_seconds"], "3.021333"
        )
        self.assertEqual(f"{plan.frames[-1].timestamp_seconds:.6f}", "2.958333")
        self.assertEqual(
            plan.frames[-1].command.spec.argv[
                plan.frames[-1].command.spec.argv.index("-ss") + 1
            ],
            "2.958333",
        )
        self.assertIn("artifact-final", plan.frames[-1].roles)
        self.assertIn("chapter-end", plan.frames[-1].roles)

    def test_checklist_requires_full_one_x_viewing_and_every_chapter(self) -> None:
        plan = self._plan()
        watch = plan.checklist[0]
        self.assertEqual(watch["id"], "watch-complete-at-1x")
        self.assertEqual(watch["state"], "pending")
        self.assertIn("exactly 1.0x", watch["instruction"])
        self.assertIn("without skipping", watch["instruction"])
        chapter_items = [row for row in plan.checklist if "chapter_id" in row]
        self.assertEqual(
            [row["chapter_id"] for row in chapter_items],
            ["opening", "feature"],
        )
        self.assertTrue(all(row["state"] == "pending" for row in plan.checklist))

    def test_template_is_explicitly_pending_and_never_a_signoff(self) -> None:
        template = self._plan().review_template
        self.assertEqual(template["kind"], REVIEW_TEMPLATE_KIND)
        self.assertEqual(template["state"], PENDING_REVIEW_STATE)
        self.assertIs(template["template_only"], True)
        self.assertIs(template["is_signoff"], False)
        self.assertIs(template["approval_granted"], False)
        self.assertEqual(
            template["human_response"],
            {
                "reviewer": None,
                "reviewed_at": None,
                "decision": None,
                "notes": None,
                "checklist_results": {},
            },
        )
        self.assertTrue(
            all(
                row["state"] == "pending"
                for row in template["full_watch"]["checklist"]
            )
        )

    def test_template_writer_is_deterministic_and_exclusive(self) -> None:
        path = self.root / "review" / "review-template.json"
        plan = self._plan()
        self.assertEqual(write_review_template(path, plan), path)
        payload = path.read_bytes()
        self.assertTrue(payload.endswith(b"\n"))
        loaded = json.loads(payload)
        self.assertEqual(loaded, plan.review_template)
        with self.assertRaisesRegex(ReviewPlanError, "overwrite"):
            write_review_template(path, plan)

    def test_invalid_or_unordered_timeline_is_rejected(self) -> None:
        invalid = (
            [],
            [{"id": "a", "start_seconds": 0, "end_seconds": 11}],
            [
                {"id": "a", "start_seconds": 0, "end_seconds": 6},
                {"id": "b", "start_seconds": 5, "end_seconds": 9},
            ],
            [
                {
                    "id": "a",
                    "start_seconds": 0,
                    "end_seconds": 5,
                    "boundary_seconds": [4, 2],
                }
            ],
            [
                {"id": "a", "start_seconds": 0, "end_seconds": 3},
                {"id": "a", "start_seconds": 3, "end_seconds": 4},
            ],
        )
        for timeline in invalid:
            with self.subTest(timeline=timeline):
                with self.assertRaises(ReviewPlanError):
                    normalize_storyboard_timeline(timeline, duration_seconds=10)


class ReviewExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.artifact = self.root / "final.mp4"
        self.artifact.write_bytes(b"finished")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _plan(self) -> ReviewPackagePlan:
        return plan_review_package(
            ffmpeg="injected-ffmpeg",
            artifact_path=self.artifact,
            probe=_probe(),
            storyboard_timeline=[
                {"id": "only", "start_seconds": 0, "end_seconds": 10}
            ],
            output_directory=self.root / "review",
            audit_directory=self.root / "audit",
        )

    def test_success_promotes_each_partial_only_after_command_success(self) -> None:
        plan = self._plan()
        calls: list[CommandSpec] = []

        def fake_runner(spec: CommandSpec, *, audit_directory: Path) -> CommandResult:
            calls.append(spec)
            partial = spec.partial_artifacts[0]
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(spec.label.encode("utf-8"))
            return CommandResult(
                spec,
                0,
                "frame stdout",
                "",
                "succeeded",
                audit_directory,
                (),
            )

        results = execute_review_frame_plan(plan, command_runner=fake_runner)
        self.assertEqual(len(results), len(plan.frames))
        self.assertEqual(len(calls), len(plan.frames))
        for frame in plan.frames:
            self.assertTrue(frame.final_output.is_file())
            self.assertFalse(frame.partial_output.exists())

    def test_nonzero_ffmpeg_retains_partial_command_and_stdio(self) -> None:
        plan = self._plan()
        first = plan.frames[0]

        def failed_process(
            argv: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            first.partial_output.parent.mkdir(parents=True, exist_ok=True)
            first.partial_output.write_bytes(b"failed-frame-bytes")
            return subprocess.CompletedProcess(
                argv, 7, stdout="extract stdout", stderr="extract failed"
            )

        def audited_runner(
            spec: CommandSpec, *, audit_directory: Path
        ) -> CommandResult:
            return run_command(
                spec,
                audit_directory=audit_directory,
                run=failed_process,
            )

        with self.assertRaises(CommandFailedError):
            execute_review_frame_plan(plan, command_runner=audited_runner)
        self.assertEqual(first.partial_output.read_bytes(), b"failed-frame-bytes")
        self.assertFalse(first.final_output.exists())
        self.assertEqual(
            (first.command.audit_directory / "stdout.txt").read_text(encoding="utf-8"),
            "extract stdout",
        )
        self.assertEqual(
            (first.command.audit_directory / "stderr.txt").read_text(encoding="utf-8"),
            "extract failed",
        )
        command = json.loads(
            (first.command.audit_directory / "command.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIs(command["shell"], False)
        self.assertEqual(command["argv"], list(first.command.spec.argv))


if __name__ == "__main__":
    unittest.main()
