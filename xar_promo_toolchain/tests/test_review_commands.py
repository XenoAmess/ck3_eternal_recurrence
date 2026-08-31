from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_promo.process import (  # noqa: E402
    CommandFailedError,
    CommandResult,
    CommandSpec,
    run_command,
)
from xar_promo.media import parse_ffprobe_json, write_bound_media_probe  # noqa: E402
from xar_promo.review import PENDING_REVIEW_STATE  # noqa: E402
from xar_promo.review_commands import (  # noqa: E402
    REVIEW_PACKAGE_KIND,
    REVIEW_PACKAGE_NAME,
    REVIEW_TEMPLATE_NAME,
    ReviewCommandError,
    run_review_command,
)


def _probe_payload(subject: Path) -> dict[str, object]:
    return {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1280,
                "height": 720,
                "avg_frame_rate": "2/1",
            },
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
            },
        ],
        "format": {
            "filename": str(subject.resolve()),
            "size": str(subject.stat().st_size),
            "duration": "4",
            "format_name": "mov,mp4",
        },
    }


def _storyboard_payload() -> dict[str, object]:
    return {
        "chapters": [
            {
                "id": "only-chapter",
                "start_seconds": 0,
                "end_seconds": 4,
                "boundary_seconds": [2],
            }
        ]
    }


def _json_scalars(value: object) -> list[object]:
    if isinstance(value, dict):
        result: list[object] = []
        for item in value.values():
            result.extend(_json_scalars(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_json_scalars(item))
        return result
    return [value]


class ReviewCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.deliverable = self.root / "deliverable.mp4"
        self.storyboard = self.root / "storyboard.json"
        self.probe = self.root / "probe.json"
        self.output = self.root / "review"
        self.audit = self.root / "audit"
        self.deliverable.write_bytes(b"finished-deliverable-bytes")
        self.storyboard.write_text(
            json.dumps(_storyboard_payload(), sort_keys=True),
            encoding="utf-8",
        )
        write_bound_media_probe(
            self.probe,
            media_path=self.deliverable,
            probe=parse_ffprobe_json(json.dumps(_probe_payload(self.deliverable))),
        )

    def _run(self, **overrides: object):
        values: dict[str, object] = {
            "ffmpeg": "injected-ffmpeg",
            "deliverable_path": self.deliverable,
            "storyboard_path": self.storyboard,
            "probe_path": self.probe,
            "output_directory": self.output,
            "audit_directory": self.audit,
        }
        values.update(overrides)
        return run_review_command(**values)  # type: ignore[arg-type]

    def test_plan_only_returns_frame_plan_with_exactly_zero_writes(self) -> None:
        before = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        def forbidden_runner(*_args: object, **_kwargs: object) -> CommandResult:
            raise AssertionError("plan-only must not invoke the command runner")

        result = self._run(plan_only=True, command_runner=forbidden_runner)
        after = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.audit.exists())
        self.assertTrue(result.plan_only)
        self.assertEqual("planned", result.state)
        self.assertEqual(4, len(result.frames))
        self.assertEqual((), result.command_results)
        self.assertIsNone(result.template_path)
        self.assertIsNone(result.package_path)
        self.assertEqual(
            ["0.000000", "1.500000", "2.000000", "3.500000"],
            [f"{frame.timestamp_seconds:.6f}" for frame in result.frames],
        )
        payload = result.to_dict()
        self.assertIs(payload["plan_only"], True)
        self.assertIs(payload["writes_performed"], False)
        self.assertNotIn("review_template", payload)
        self.assertNotIn("review_package", payload)
        self.assertNotIn("commands", payload)
        self.assertEqual(
            "injected-ffmpeg",
            payload["frame_plan"][0]["command"]["argv"][0],
        )

    def test_execution_creates_only_pending_byte_bound_review_material(self) -> None:
        calls: list[tuple[CommandSpec, Path]] = []

        def successful_runner(
            spec: CommandSpec, *, audit_directory: Path
        ) -> CommandResult:
            calls.append((spec, audit_directory))
            partial = spec.partial_artifacts[0]
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes((spec.label + "-png").encode("utf-8"))
            audit_directory.mkdir(parents=True, exist_ok=False)
            (audit_directory / "test-runner.txt").write_text(
                "retained", encoding="utf-8"
            )
            return CommandResult(
                spec,
                0,
                "",
                "",
                "succeeded",
                audit_directory,
                (),
            )

        with mock.patch("xar_promo.operations.record_signoff") as signoff:
            result = self._run(command_runner=successful_runner)
        signoff.assert_not_called()
        self.assertFalse(result.plan_only)
        self.assertEqual(PENDING_REVIEW_STATE, result.state)
        self.assertEqual(len(result.frames), len(calls))
        self.assertTrue((self.output / REVIEW_TEMPLATE_NAME).is_file())
        self.assertTrue((self.output / REVIEW_PACKAGE_NAME).is_file())
        self.assertTrue(all(frame.final_output.is_file() for frame in result.frames))
        self.assertTrue(all(not frame.partial_output.exists() for frame in result.frames))

        template = json.loads(
            (self.output / REVIEW_TEMPLATE_NAME).read_text(encoding="utf-8")
        )
        package = json.loads(
            (self.output / REVIEW_PACKAGE_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(PENDING_REVIEW_STATE, template["state"])
        self.assertIs(template["is_signoff"], False)
        self.assertIs(template["approval_granted"], False)
        self.assertIsNone(template["human_response"]["decision"])
        self.assertEqual(REVIEW_PACKAGE_KIND, package["kind"])
        self.assertEqual(PENDING_REVIEW_STATE, package["state"])
        self.assertIs(package["is_signoff"], False)
        self.assertIs(package["approval_granted"], False)
        self.assertNotIn("approved", _json_scalars(template))
        self.assertNotIn("approved", _json_scalars(package))

        template_record = package["review_template"]
        template_bytes = (self.output / template_record["path"]).read_bytes()
        self.assertEqual(len(template_bytes), template_record["bytes"])
        self.assertEqual(
            hashlib.sha256(template_bytes).hexdigest().upper(),
            template_record["sha256"],
        )
        for row in package["frames"]:
            frame_path = self.output / row["path"]
            frame_bytes = frame_path.read_bytes()
            self.assertEqual(len(frame_bytes), row["bytes"])
            self.assertEqual(
                hashlib.sha256(frame_bytes).hexdigest().upper(),
                row["sha256"],
            )
            self.assertEqual("succeeded", row["command"]["status"])

        result_payload = result.to_dict()
        self.assertEqual(PENDING_REVIEW_STATE, result_payload["state"])
        self.assertIs(result_payload["is_signoff"], False)
        self.assertIs(result_payload["approval_granted"], False)

    def test_relative_inputs_and_outputs_resolve_from_explicit_working_directory(
        self,
    ) -> None:
        calls: list[CommandSpec] = []

        def successful_runner(
            spec: CommandSpec, *, audit_directory: Path
        ) -> CommandResult:
            calls.append(spec)
            partial = spec.partial_artifacts[0]
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"frame")
            return CommandResult(spec, 0, "", "", "succeeded", audit_directory, ())

        result = run_review_command(
            ffmpeg="ffmpeg-token",
            deliverable_path=Path("deliverable.mp4"),
            storyboard_path=Path("storyboard.json"),
            probe_path=Path("probe.json"),
            output_directory=Path("review-relative"),
            audit_directory=Path("audit-relative"),
            working_directory=self.root,
            command_runner=successful_runner,
        )
        self.assertEqual(self.root, calls[0].cwd)
        self.assertEqual(
            self.root / "review-relative" / REVIEW_PACKAGE_NAME,
            result.package_path,
        )
        self.assertTrue(result.package_path.is_file())

    def test_failure_retains_completed_frame_partial_and_process_audit(self) -> None:
        attempt = 0

        def audited_runner(
            spec: CommandSpec, *, audit_directory: Path
        ) -> CommandResult:
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                partial = spec.partial_artifacts[0]
                partial.parent.mkdir(parents=True, exist_ok=True)
                partial.write_bytes(b"completed-first-frame")
                return CommandResult(
                    spec, 0, "", "", "succeeded", audit_directory, ()
                )

            def failed_process(
                argv: list[str], **_kwargs: object
            ) -> subprocess.CompletedProcess[str]:
                partial = spec.partial_artifacts[0]
                partial.parent.mkdir(parents=True, exist_ok=True)
                partial.write_bytes(b"failed-second-frame")
                return subprocess.CompletedProcess(
                    argv,
                    9,
                    stdout="retained stdout",
                    stderr="retained stderr",
                )

            return run_command(
                spec,
                audit_directory=audit_directory,
                run=failed_process,
            )

        with self.assertRaises(CommandFailedError):
            self._run(command_runner=audited_runner)

        first_final = self.output / "frames" / "frame-000001.png"
        second_partial = self.output / "frames" / ".frame-000002.partial.png"
        second_audit = self.audit / "frames" / "frame-000002"
        self.assertEqual(b"completed-first-frame", first_final.read_bytes())
        self.assertEqual(b"failed-second-frame", second_partial.read_bytes())
        self.assertEqual(
            "retained stdout",
            (second_audit / "stdout.txt").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "retained stderr",
            (second_audit / "stderr.txt").read_text(encoding="utf-8"),
        )
        self.assertTrue((second_audit / "command.json").is_file())
        self.assertTrue((second_audit / "result.json").is_file())
        self.assertFalse((self.output / REVIEW_TEMPLATE_NAME).exists())
        self.assertFalse((self.output / REVIEW_PACKAGE_NAME).exists())

    def test_permissive_failed_runner_cannot_promote_partial(self) -> None:
        def permissive_runner(
            spec: CommandSpec, *, audit_directory: Path
        ) -> CommandResult:
            partial = spec.partial_artifacts[0]
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"failed-but-returned")
            return CommandResult(
                spec,
                5,
                "",
                "failed",
                "failed",
                audit_directory,
                (),
            )

        with self.assertRaisesRegex(ReviewCommandError, "did not succeed"):
            self._run(command_runner=permissive_runner)
        self.assertTrue(
            (self.output / "frames" / ".frame-000001.partial.png").is_file()
        )
        self.assertFalse(
            (self.output / "frames" / "frame-000001.png").exists()
        )

    def test_runner_cannot_return_a_stale_success_result(self) -> None:
        def stale_runner(
            spec: CommandSpec, *, audit_directory: Path
        ) -> CommandResult:
            partial = spec.partial_artifacts[0]
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"stale-result-partial")
            stale_spec = CommandSpec.create(("other-tool",), label="other command")
            return CommandResult(
                stale_spec,
                0,
                "",
                "",
                "succeeded",
                audit_directory,
                (),
            )

        with self.assertRaisesRegex(ReviewCommandError, "different command"):
            self._run(command_runner=stale_runner)
        self.assertTrue(
            (self.output / "frames" / ".frame-000001.partial.png").is_file()
        )
        self.assertFalse(
            (self.output / "frames" / "frame-000001.png").exists()
        )

    def test_existing_package_or_template_fails_before_any_command(self) -> None:
        self.output.mkdir(parents=True)
        template = self.output / REVIEW_TEMPLATE_NAME
        template.write_bytes(b"do-not-overwrite")
        calls: list[object] = []

        def forbidden_runner(*args: object, **_kwargs: object) -> CommandResult:
            calls.extend(args)
            raise AssertionError("preflight collision must happen first")

        with self.assertRaisesRegex(ReviewCommandError, "overwrite review template"):
            self._run(command_runner=forbidden_runner)
        self.assertEqual([], calls)
        self.assertEqual(b"do-not-overwrite", template.read_bytes())
        self.assertEqual([], list((self.output / "frames").glob("*")) if (self.output / "frames").exists() else [])

    def test_invalid_storyboard_or_probe_is_typed_and_writes_nothing(self) -> None:
        self.storyboard.write_text("{bad", encoding="utf-8")
        with self.assertRaisesRegex(ReviewCommandError, "invalid storyboard"):
            self._run(plan_only=True)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.audit.exists())

        self.storyboard.write_text(
            json.dumps(_storyboard_payload()), encoding="utf-8"
        )
        self.probe.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ReviewCommandError, "invalid ffprobe"):
            self._run(plan_only=True)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.audit.exists())

    def test_raw_or_stale_probe_cannot_create_a_pending_review(self) -> None:
        raw = _probe_payload(self.deliverable)
        raw_probe = self.root / "raw-unbound-probe.json"
        raw_probe.write_text(json.dumps(raw), encoding="utf-8")
        self.probe = raw_probe
        with self.assertRaisesRegex(ReviewCommandError, "unbound ffprobe envelope"):
            self._run(plan_only=True)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.audit.exists())

        self.probe = self.root / "bound-before-subject-change.json"
        write_bound_media_probe(
            self.probe,
            media_path=self.deliverable,
            probe=parse_ffprobe_json(json.dumps(raw)),
        )
        self.deliverable.write_bytes(b"different deliverable bytes")
        with self.assertRaisesRegex(ReviewCommandError, "mismatch"):
            self._run(plan_only=True)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.audit.exists())


if __name__ == "__main__":
    unittest.main()
