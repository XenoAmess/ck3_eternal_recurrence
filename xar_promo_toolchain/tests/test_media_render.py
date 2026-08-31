from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from xar_promo.media import (  # noqa: E402
    MediaProbeError,
    bind_media_probe,
    ffprobe_command,
    load_bound_media_probe,
    parse_ffprobe_json,
    probe_and_write_bound_media,
    probe_media,
    require_streams,
    write_bound_media_probe,
)
from xar_promo.process import (  # noqa: E402
    CommandFailedError,
    CommandResult,
    CommandSpec,
    CommandStartError,
    PartialArtifactSnapshot,
    run_command,
)
from xar_promo.render import (  # noqa: E402
    RenderOptions,
    RenderPlanError,
    ass_burn_in_filter,
    build_filtergraph,
    concat_manifest,
    execute_render_plan,
    plan_concat,
    plan_render,
)


class MediaProbeTests(unittest.TestCase):
    def test_ffprobe_command_is_stable_and_executable_is_injected(self) -> None:
        command = ffprobe_command(Path("tools/custom-probe"), Path("input movie.mkv"))
        self.assertEqual(
            command,
            (
                "tools/custom-probe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                "input movie.mkv",
            ),
        )

    def test_parse_ffprobe_json_extracts_typed_streams_and_duration(self) -> None:
        payload = {
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "avg_frame_rate": "30000/1001",
                    "duration": "4.5",
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                },
            ],
            "format": {"duration": "5.25", "format_name": "matroska"},
        }
        probe = parse_ffprobe_json(json.dumps(payload))
        self.assertEqual(probe.require_duration(), 5.25)
        self.assertEqual(len(probe.video_streams), 1)
        self.assertEqual(len(probe.audio_streams), 1)
        self.assertEqual(probe.video_streams[0].average_frame_rate, Fraction(30000, 1001))
        self.assertEqual(probe.audio_streams[0].sample_rate, 48_000)
        self.assertIs(require_streams(probe, video=True, audio=True), probe)

    def test_parse_ffprobe_json_rejects_invalid_shapes(self) -> None:
        for payload in ("not-json", "[]", '{"streams":{}}', '{"format":[]}'):
            with self.subTest(payload=payload):
                with self.assertRaises(MediaProbeError):
                    parse_ffprobe_json(payload)
        empty = parse_ffprobe_json("{}")
        with self.assertRaisesRegex(MediaProbeError, "video, audio"):
            require_streams(empty, video=True, audio=True)
        with self.assertRaises(MediaProbeError):
            empty.require_duration()

    def test_probe_media_passes_the_injected_command_and_parses_stdout(self) -> None:
        captured: list[tuple[CommandSpec, Path]] = []

        def fake_runner(spec: CommandSpec, *, audit_directory: Path) -> CommandResult:
            captured.append((spec, audit_directory))
            return CommandResult(
                spec=spec,
                returncode=0,
                stdout='{"streams":[],"format":{"duration":"1.5"}}',
                stderr="",
                status="succeeded",
                audit_directory=audit_directory,
                partial_artifacts=(),
            )

        probe = probe_media(
            "D:/media/bin/ffprobe.exe",
            "clip.mkv",
            audit_directory=Path("audit/probe"),
            command_runner=fake_runner,
        )
        self.assertEqual(probe.duration_seconds, 1.5)
        self.assertEqual(captured[0][0].argv[0], "D:/media/bin/ffprobe.exe")
        self.assertEqual(captured[0][1], Path("audit/probe"))

    def test_bound_probe_verifies_exact_bytes_and_rejects_stale_raw_rebinding(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = root / "current.mp4"
            current.write_bytes(b"current media bytes")
            raw_probe = {
                "streams": [{"codec_type": "video", "duration": "3.0"}],
                "format": {
                    "filename": str(current.resolve()),
                    "size": str(current.stat().st_size),
                    "duration": "3.0",
                },
            }
            probe = parse_ffprobe_json(json.dumps(raw_probe))
            envelope = root / "current.bound-probe.json"
            written = write_bound_media_probe(
                envelope,
                media_path=current,
                probe=probe,
            )
            loaded = load_bound_media_probe(envelope, media_path=current)
            self.assertEqual(written.subject_sha256, loaded.subject_sha256)
            self.assertEqual(3.0, loaded.probe.require_duration())

            current.write_bytes(b"changed media bytes")
            with self.assertRaisesRegex(MediaProbeError, "mismatch"):
                load_bound_media_probe(envelope, media_path=current)

            old = root / "old.mp4"
            old.write_bytes(b"old")
            stale = parse_ffprobe_json(
                json.dumps(
                    {
                        "streams": [{"codec_type": "video", "duration": "1.0"}],
                        "format": {
                            "filename": str(old.resolve()),
                            "size": str(old.stat().st_size),
                            "duration": "1.0",
                        },
                    }
                )
            )
            with self.assertRaisesRegex(MediaProbeError, "describes"):
                bind_media_probe(current, stale)

    def test_high_level_bound_probe_producer_runs_audited_ffprobe(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            subject = root / "subject.mp4"
            subject.write_bytes(b"media subject")
            calls: list[tuple[CommandSpec, Path]] = []

            def fake_runner(
                spec: CommandSpec, *, audit_directory: Path
            ) -> CommandResult:
                calls.append((spec, audit_directory))
                payload = {
                    "streams": [{"codec_type": "video", "duration": "2.5"}],
                    "format": {
                        "filename": str(subject.resolve()),
                        "size": str(subject.stat().st_size),
                        "duration": "2.5",
                    },
                }
                return CommandResult(
                    spec,
                    0,
                    json.dumps(payload),
                    "",
                    "succeeded",
                    audit_directory,
                    (),
                )

            output = root / "probe" / "subject.bound.json"
            bound = probe_and_write_bound_media(
                "custom-ffprobe",
                subject,
                output_path=output,
                audit_directory=root / "audit",
                command_runner=fake_runner,
            )
            self.assertTrue(output.is_file())
            self.assertEqual(1, len(calls))
            self.assertEqual("custom-ffprobe", calls[0][0].argv[0])
            self.assertEqual(bound, load_bound_media_probe(output, media_path=subject))


class ProcessAuditTests(unittest.TestCase):
    def test_nonzero_exit_retains_command_stdio_and_partial_without_shell(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            partial = root / "render.partial.mp4"
            audit = root / "audit"
            calls: list[tuple[list[str], dict[str, object]]] = []

            def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append((argv, kwargs))
                partial.write_bytes(b"PARTIAL-BYTES")
                return subprocess.CompletedProcess(
                    argv, 9, stdout="captured output", stderr="encoder failed"
                )

            spec = CommandSpec.create(
                ("custom-ffmpeg", "-i", "input", partial),
                label="test render",
                partial_artifacts=(partial,),
            )
            with self.assertRaises(CommandFailedError) as raised:
                run_command(spec, audit_directory=audit, run=fake_run)

            self.assertEqual(partial.read_bytes(), b"PARTIAL-BYTES")
            self.assertEqual(raised.exception.result.returncode, 9)
            self.assertEqual((audit / "stdout.txt").read_text(encoding="utf-8"), "captured output")
            self.assertEqual((audit / "stderr.txt").read_text(encoding="utf-8"), "encoder failed")
            command_record = json.loads((audit / "command.json").read_text(encoding="utf-8"))
            result_record = json.loads((audit / "result.json").read_text(encoding="utf-8"))
            self.assertIs(command_record["shell"], False)
            self.assertEqual(command_record["argv"], list(spec.argv))
            self.assertEqual(result_record["status"], "failed")
            self.assertEqual(result_record["partial_artifacts"][0]["bytes"], 13)
            self.assertEqual(len(calls), 1)
            self.assertIs(calls[0][1]["shell"], False)
            self.assertIs(calls[0][1]["check"], False)

    def test_start_failure_also_retains_audit_and_preexisting_partial(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            partial = root / "startup.partial.mp4"
            partial.write_bytes(b"older diagnostic bytes")
            audit = root / "audit"

            def cannot_start(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                raise FileNotFoundError("injected executable is absent")

            spec = CommandSpec.create(
                ("missing-ffmpeg", "-version"),
                label="test startup",
                partial_artifacts=(partial,),
            )
            with self.assertRaises(CommandStartError) as raised:
                run_command(spec, audit_directory=audit, run=cannot_start)
            self.assertIsNone(raised.exception.result.returncode)
            self.assertEqual(partial.read_bytes(), b"older diagnostic bytes")
            result = json.loads((audit / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "start_failed")
            self.assertEqual(result["partial_artifacts"][0]["bytes"], 22)
            self.assertIn(
                "injected executable is absent",
                (audit / "stderr.txt").read_text(encoding="utf-8"),
            )


class RenderPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.options = RenderOptions(
            width=1280,
            height=720,
            fps=30,
            duration_seconds=12.5,
            preset="slow",
            crf=18,
        )

    def test_filtergraph_and_ass_escape_are_stable(self) -> None:
        subtitle = Path("D:/project/sub titles/cue,one.ass")
        ass = ass_burn_in_filter(subtitle)
        self.assertEqual(
            ass,
            "ass=filename='D\\:/project/sub titles/cue\\,one.ass'",
        )
        first = build_filtergraph(self.options, ass_path=subtitle)
        second = build_filtergraph(self.options, ass_path=subtitle)
        self.assertEqual(first, second)
        self.assertIn("scale=1280:720", first)
        self.assertIn("fps=30", first)
        self.assertIn(ass, first)
        self.assertIn("atrim=duration=12.500000", first)
        self.assertNotIn("zh-CN", first)
        self.assertNotIn("voice", first.lower())

    def test_concat_manifest_preserves_order_and_rejects_ambiguous_paths(self) -> None:
        base = Path("build")
        result = concat_manifest(
            (base / "01 intro.mp4", base / "02-main.mp4"),
            manifest_directory=base,
        )
        self.assertEqual(result, "file '01 intro.mp4'\nfile '02-main.mp4'\n")
        with self.assertRaises(RenderPlanError):
            concat_manifest((Path("bad'name.mp4"),))
        with self.assertRaises(RenderPlanError):
            concat_manifest(())

    def test_render_plan_has_deterministic_shell_free_argv(self) -> None:
        arguments = {
            "ffmpeg": Path("vendor/ffmpeg-custom"),
            "video_input": Path("raw/video.mkv"),
            "audio_input": Path("raw/narration.wav"),
            "partial_output": Path("out/render.partial.mp4"),
            "final_output": Path("out/render.mp4"),
            "audit_directory": Path("audit"),
            "options": self.options,
            "ass_path": Path("subs/main.ass"),
            "start_seconds": 1.25,
            "working_directory": Path("work"),
        }
        first = plan_render(**arguments)
        second = plan_render(**arguments)
        self.assertEqual(first, second)
        command = first.commands[0].spec
        self.assertEqual(command.argv[0], "vendor/ffmpeg-custom")
        self.assertEqual(command.argv[1:6], ("-nostdin", "-hide_banner", "-loglevel", "error", "-n"))
        self.assertIn("-filter_complex", command.argv)
        self.assertIn("ass=filename=", command.argv[command.argv.index("-filter_complex") + 1])
        self.assertEqual(command.partial_artifacts, (Path("out/render.partial.mp4"),))

    def test_concat_plan_retains_exact_generated_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            segments = (root / "segments" / "a.mp4", root / "segments" / "b.mp4")
            plan = plan_concat(
                ffmpeg="injected-ffmpeg",
                segment_paths=segments,
                concat_path=root / "build" / "concat.txt",
                partial_output=root / "out" / "joined.partial.mp4",
                final_output=root / "out" / "joined.mp4",
                audit_directory=root / "audit",
                working_directory=root,
            )
            self.assertEqual(plan.commands[0].spec.argv[0], "injected-ffmpeg")
            self.assertEqual(plan.generated_files[0].path, root / "build" / "concat.txt")
            self.assertEqual(
                plan.generated_files[0].content,
                "file '../segments/a.mp4'\nfile '../segments/b.mp4'\n",
            )

    def test_relative_plan_outputs_are_interpreted_from_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = plan_concat(
                ffmpeg="ffmpeg",
                segment_paths=(Path("segments/a.mp4"),),
                concat_path=Path("build/concat.txt"),
                partial_output=Path("out/joined.partial.mp4"),
                final_output=Path("out/joined.mp4"),
                audit_directory=root / "audit",
                working_directory=root,
            )
            self.assertEqual(plan.generated_files[0].path, root / "build/concat.txt")
            self.assertEqual(plan.generated_files[0].content, "file '../segments/a.mp4'\n")
            self.assertEqual(plan.partial_output, root / "out/joined.partial.mp4")
            self.assertEqual(plan.final_output, root / "out/joined.mp4")

    def test_execute_failure_keeps_partial_and_success_promotes_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            failing = plan_render(
                ffmpeg="ffmpeg",
                video_input=root / "video.mkv",
                audio_input=root / "audio.wav",
                partial_output=root / "failed.partial.mp4",
                final_output=root / "failed.mp4",
                audit_directory=root / "audit-failed",
                options=self.options,
            )

            def fail_runner(spec: CommandSpec, *, audit_directory: Path) -> CommandResult:
                failing.partial_output.write_bytes(b"failed partial")
                raise RuntimeError("synthetic encoder failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic encoder failure"):
                execute_render_plan(failing, command_runner=fail_runner)
            self.assertEqual(failing.partial_output.read_bytes(), b"failed partial")
            self.assertFalse(failing.final_output.exists())

            successful = plan_render(
                ffmpeg="ffmpeg",
                video_input=root / "video.mkv",
                audio_input=root / "audio.wav",
                partial_output=root / "success.partial.mp4",
                final_output=root / "success.mp4",
                audit_directory=root / "audit-success",
                options=self.options,
            )

            def success_runner(spec: CommandSpec, *, audit_directory: Path) -> CommandResult:
                successful.partial_output.parent.mkdir(parents=True, exist_ok=True)
                successful.partial_output.write_bytes(b"complete")
                return CommandResult(
                    spec=spec,
                    returncode=0,
                    stdout="",
                    stderr="",
                    status="succeeded",
                    audit_directory=audit_directory,
                    partial_artifacts=(
                        PartialArtifactSnapshot(successful.partial_output, True, 8),
                    ),
                )

            results = execute_render_plan(successful, command_runner=success_runner)
            self.assertEqual(len(results), 1)
            self.assertFalse(successful.partial_output.exists())
            self.assertEqual(successful.final_output.read_bytes(), b"complete")


if __name__ == "__main__":
    unittest.main()
