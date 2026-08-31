#!/usr/bin/env python3
"""Offline/fake-pipeline tests for the phase-two ZhongGuo promo entry."""

from __future__ import annotations

import ast
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


TOOLS_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = TOOLS_DIRECTORY.parent
REPOSITORY_ROOT = PROJECT_DIRECTORY.parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_phase2_promo_video as promo  # noqa: E402

from xar_promo.pipeline import (  # noqa: E402
    AuditRecordReady,
    PipelineArtifactRecord,
    PipelineFailure,
    PipelinePhaseRecord,
    PipelineResult,
)
from xar_promo.operations import (  # noqa: E402
    preserve_artifact,
    record_signoff,
    start_run,
)
from xar_promo.presets.zhongguo_361_phase2 import (  # noqa: E402
    CaptureRequirements,
    Phase2CaptureCandidate,
    load_phase2_project_config,
)
from xar_promo.project import load_document  # noqa: E402


CHECKED_CONFIG = PROJECT_DIRECTORY / "promo" / "phase2-promo-project.json"


def _write_ready_config(root: Path) -> Path:
    payload = json.loads(CHECKED_CONFIG.read_text(encoding="utf-8-sig"))
    for index, chapter in enumerate(payload["chapters"], start=1):
        cue_id = f"phase2-cue-{index:02d}"
        chapter["state"] = "ready"
        chapter["cues"] = [
            {
                "id": cue_id,
                "narration": {"zh-CN": f"这是二期第 {index} 段的真实旁白。"},
                "subtitles": {
                    "zh-CN": f"二期第 {index} 段。",
                    "en": f"Phase-two segment {index}.",
                },
            }
        ]
        chapter["artifact_ids"] = [
            promo._narration_artifact_id(chapter["id"], cue_id)
        ]
    path = root / "phase2-ready.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _args(
    config: Path,
    capture: Path,
    workdir: Path,
    *,
    validate_only: bool,
):
    values = [
        "--project-config",
        str(config),
        "--capture-root",
        str(capture),
        "--work-dir",
        str(workdir),
    ]
    if validate_only:
        values.append("--validate-only")
    return promo.parser().parse_args(values)


def _candidate(config, capture_root: Path, bundle=None):
    if bundle is None:
        bundle = SimpleNamespace(artifact_root=capture_root)
    return SimpleNamespace(
        config=config,
        bundle=bundle,
        phase_two_runtime_claims_verified=False,
        blockers=("phase-two runtime claims remain pending",),
    )


class _FakeComposer:
    real_durations = False
    instances: list["_FakeComposer"] = []

    def __init__(self, *, capture_root: Path, **_kwargs) -> None:
        self.capture_root = capture_root
        self.capture_candidate = None
        self.real_narration_durations = self.real_durations
        self.final_probe_calls = 0
        self.calls = []
        self.__class__.instances.append(self)

    def __call__(self, config, run, **kwargs):
        self.config = config
        self.calls.append((config, run, kwargs))
        self.capture_candidate = _candidate(config, self.capture_root)
        return SimpleNamespace(workdir=kwargs["workdir"])

    def verify_final_deliverable(self, result):
        self.final_probe_calls += 1
        self.final_duration_seconds = 449.286
        return self.final_duration_seconds


class _RealDurationFakeComposer(_FakeComposer):
    real_durations = True
    instances: list["_RealDurationFakeComposer"] = []


class _OverlongFakeComposer(_RealDurationFakeComposer):
    instances: list["_OverlongFakeComposer"] = []

    def verify_final_deliverable(self, result):
        self.final_probe_calls += 1
        self.final_duration_seconds = 1200.0
        return promo.validate_rendered_duration(
            self.final_duration_seconds,
            self.config,
        )


def _validated_result(workdir: Path) -> PipelineResult:
    return PipelineResult(
        status="validated",
        validate_only=True,
        workdir=workdir.resolve(),
        phases=(PipelinePhaseRecord(1, "draft", "validated"),),
        artifacts=(),
        audit_record=None,
        failure=None,
        signoff_recorded=False,
    )


def _successful_result(workdir: Path, config=None) -> PipelineResult:
    artifacts = []
    if config is not None:
        for chapter in config.chapters:
            for artifact_id in chapter.artifact_ids:
                narration = workdir / "fake-narration" / f"{artifact_id}.mp3"
                narration.parent.mkdir(parents=True, exist_ok=True)
                narration.write_bytes(f"FAKE-{artifact_id}".encode("utf-8"))
                artifacts.append(
                    PipelineArtifactRecord.from_path(
                        narration,
                        artifact_id=artifact_id,
                        role="narration",
                        media_type="audio/mpeg",
                    )
                )
    output = workdir / promo.DELIVERABLE_RELATIVE_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"FAKE-PHASE-TWO-MP4")
    deliverable = PipelineArtifactRecord.from_path(
        output,
        artifact_id=promo.DELIVERABLE_ARTIFACT_ID,
        role="deliverable",
        media_type="video/mp4",
    )
    phase = PipelinePhaseRecord(
        1,
        "audit-record-ready",
        "succeeded",
        (deliverable.artifact_id,),
    )
    audit = AuditRecordReady(
        project_id="zhongguo-361-phase2-promo",
        deliverable=deliverable,
        phase_records=(phase,),
    )
    return PipelineResult(
        status="succeeded",
        validate_only=False,
        workdir=workdir.resolve(),
        phases=(phase,),
        artifacts=tuple(artifacts) + (deliverable,),
        audit_record=audit,
        failure=None,
        signoff_recorded=False,
    )


class Phase2PromoEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        _FakeComposer.instances.clear()
        _RealDurationFakeComposer.instances.clear()
        _OverlongFakeComposer.instances.clear()

    def test_checked_in_planned_project_is_red_without_pipeline_or_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workdir = root / "must-not-exist"
            runner = mock.Mock()
            args = _args(
                CHECKED_CONFIG,
                root / "missing-capture",
                workdir,
                validate_only=True,
            )

            with self.assertRaisesRegex(promo.Phase2PromoBuildError, "remains planned"):
                promo.execute(args, pipeline_runner=runner)

            runner.assert_not_called()
            self.assertFalse(workdir.exists())

    def test_validate_only_uses_fake_pipeline_but_stays_release_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "read-only-attempt"
            args = _args(
                config_path,
                root / "fake-live-capture",
                workdir,
                validate_only=True,
            )
            calls = []

            def runner(invocation, **kwargs):
                calls.append((invocation, kwargs))
                return _validated_result(workdir)

            outcome = promo.execute(
                args,
                composer_factory=_FakeComposer,
                pipeline_runner=runner,
            )

            self.assertTrue(outcome.result.succeeded)
            self.assertFalse(outcome.release_ready)
            self.assertFalse(outcome.result.signoff_recorded)
            self.assertIn("authoring estimates", " ".join(outcome.blockers))
            self.assertIn("human sign-off", " ".join(outcome.blockers))
            self.assertEqual(1, len(calls))
            self.assertTrue(calls[0][1]["validate_only"])
            self.assertTrue(calls[0][1]["offline_tts"])
            self.assertEqual(0, _FakeComposer.instances[0].final_probe_calls)
            self.assertFalse(workdir.exists())

    def test_fake_full_build_preserves_candidate_run_without_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "candidate-attempt"
            args = _args(
                config_path,
                root / "fake-live-capture",
                workdir,
                validate_only=False,
            )

            outcome = promo.execute(
                args,
                composer_factory=_RealDurationFakeComposer,
                pipeline_runner=lambda _invocation, **_kwargs: _successful_result(
                    workdir,
                    load_phase2_project_config(config_path),
                ),
            )

            self.assertTrue(outcome.result.succeeded)
            self.assertFalse(outcome.release_ready)
            self.assertIsNotNone(outcome.run_manifest_path)
            self.assertTrue((workdir / "phase2-pipeline-result.json").is_file())
            loaded = load_document(outcome.run_manifest_path, check_files=True)
            self.assertIsNotNone(loaded.run)
            self.assertEqual(11, len(loaded.run.artifacts))
            self.assertEqual(
                1,
                sum(artifact.role == "deliverable" for artifact in loaded.run.artifacts),
            )
            self.assertEqual((), loaded.run.signoffs)
            summary = json.loads(
                (workdir / "phase2-pipeline-result.json").read_text(encoding="utf-8")
            )
            self.assertEqual("succeeded", summary["status"])
            self.assertFalse(summary["signoff_recorded"])
            self.assertEqual("GREEN", summary["final_duration_gate"]["status"])
            self.assertEqual(
                449.286,
                summary["final_duration_gate"]["observed_seconds"],
            )
            self.assertEqual(
                1,
                _RealDurationFakeComposer.instances[0].final_probe_calls,
            )

    def test_exact_deliverable_at_twenty_minutes_is_red_and_retained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "overlong-attempt"
            args = _args(
                config_path,
                root / "fake-live-capture",
                workdir,
                validate_only=False,
            )

            with self.assertRaisesRegex(Exception, "shorter than 1200"):
                promo.execute(
                    args,
                    composer_factory=_OverlongFakeComposer,
                    pipeline_runner=lambda _invocation, **_kwargs: _successful_result(
                        workdir
                    ),
                )

            self.assertEqual(
                b"FAKE-PHASE-TWO-MP4",
                (workdir / promo.DELIVERABLE_RELATIVE_PATH).read_bytes(),
            )
            receipt = json.loads(
                (workdir / "phase2-entry-failure.json").read_text(encoding="utf-8")
            )
            self.assertEqual("final-duration", receipt["phase"])
            summary = json.loads(
                (workdir / "phase2-pipeline-result.json").read_text(encoding="utf-8")
            )
            self.assertEqual("RED", summary["final_duration_gate"]["status"])
            self.assertEqual(1200.0, summary["final_duration_gate"]["observed_seconds"])
            self.assertFalse((workdir / "candidate-run" / "run-manifest.json").exists())
            self.assertEqual(1, _OverlongFakeComposer.instances[0].final_probe_calls)

    def test_fake_pipeline_failure_retains_partial_and_red_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "failed-attempt"
            args = _args(
                config_path,
                root / "fake-live-capture",
                workdir,
                validate_only=False,
            )

            def failed(_invocation, **_kwargs):
                workdir.mkdir(parents=True)
                partial = workdir / "partial" / "retained.partial.mp4"
                partial.parent.mkdir()
                partial.write_bytes(b"RETAIN-ME")
                failure = PipelineFailure(
                    phase="segment-render",
                    exception_type="FakeEncoderError",
                    message="intentional failure",
                    stdout="",
                    stderr="fake stderr",
                    partial_paths=(partial.resolve(),),
                    stdout_paths=(),
                    stderr_paths=(),
                    retained_paths=(partial.resolve(),),
                )
                phase = PipelinePhaseRecord(
                    1,
                    "segment-render",
                    "failed",
                    detail="FakeEncoderError: intentional failure",
                )
                return PipelineResult(
                    "failed",
                    False,
                    workdir.resolve(),
                    (phase,),
                    (),
                    None,
                    failure,
                    False,
                )

            outcome = promo.execute(
                args,
                composer_factory=_RealDurationFakeComposer,
                pipeline_runner=failed,
            )

            self.assertFalse(outcome.result.succeeded)
            self.assertFalse(outcome.release_ready)
            self.assertEqual(
                b"RETAIN-ME",
                (workdir / "partial" / "retained.partial.mp4").read_bytes(),
            )
            self.assertTrue((workdir / "phase2-pipeline-result.json").is_file())
            self.assertFalse((workdir / "candidate-run" / "run-manifest.json").exists())

    def test_missing_real_capture_writes_failure_attempt_in_build_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "missing-capture-attempt"
            args = _args(
                config_path,
                root / "missing-live-capture",
                workdir,
                validate_only=False,
            )

            with self.assertRaisesRegex(Exception, "capture artifact root"):
                promo.execute(args)

            receipt = json.loads(
                (workdir / "phase2-entry-failure.json").read_text(encoding="utf-8")
            )
            self.assertEqual("RED", receipt["status"])
            self.assertIn("capture artifact root", receipt["message"])

    def test_real_composer_validate_only_reads_capture_projection_without_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            config = load_phase2_project_config(config_path)
            raw_capture = root / "real-character-capture.mkv"
            raw_capture.write_bytes(b"HASH-BOUND-CK3-CAPTURE")
            spans = {
                chapter.chapter_id: SimpleNamespace(
                    span_id=chapter.chapter_id,
                    begin_mark=f"{chapter.chapter_id}_clean_begin",
                    end_mark=f"{chapter.chapter_id}_clean_end",
                    begin_seconds=10.0,
                    end_seconds=110.0,
                    duration_seconds=100.0,
                )
                for chapter in config.chapters
                if chapter.kind == promo.CAPTURE_CHAPTER_KIND
            }

            bundle = SimpleNamespace(
                artifact_root=root / "capture",
                raw_capture=SimpleNamespace(
                    path=raw_capture.resolve(),
                    sha256="A" * 64,
                ),
                clean_span=lambda span_id: spans[span_id],
            )

            candidate = Phase2CaptureCandidate(
                config=config,
                bundle=bundle,  # type: ignore[arg-type]
                requirements=CaptureRequirements(tuple(spans), ()),
                historical_subjects=(),
                title_history_source=SimpleNamespace(),  # type: ignore[arg-type]
                fixture_ui_attested_absent=True,
                test_decisions_attested_absent=True,
                capture_report_verified=True,
                phase_two_runtime_claims_verified=False,
                human_visual_review_verified=False,
                release_ready=False,
                blockers=("runtime pending", "human review pending"),
            )
            workdir = root / "must-not-be-created"
            composer = promo.Phase2ProjectComposer(
                capture_root=root / "capture",
                tts_cache_root=None,
                edge_tts_version=promo.DEFAULT_EDGE_TTS_VERSION,
                ffmpeg="must-not-run-ffmpeg",
                ffprobe="must-not-run-ffprobe",
                zh_font_file=root / "missing-zh-font",
                en_font_file=root / "missing-en-font",
                command_runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("validate-only must not run a process")
                ),
            )
            invocation = composer(
                config,
                None,
                config_path=config_path,
                run_path=None,
                workdir=workdir,
                adapter_factory=lambda _config, _root: candidate,
                preset_factory=lambda value: value,
                validate_only=True,
            )

            result = promo.run_invocation(
                invocation,
                validate_only=True,
                offline_tts=True,
            )

            self.assertEqual("validated", result.status)
            self.assertFalse(workdir.exists())
            self.assertFalse(composer.real_narration_durations)
            self.assertIs(candidate, composer.capture_candidate)
            self.assertEqual(10, len(invocation.draft.segments))

    def test_entry_imports_no_ocr_runtime(self) -> None:
        source = Path(promo.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(
            any("ocr" in name.casefold() or "tesseract" in name.casefold() for name in imports)
        )

    def test_exact_target_latest_rejection_beats_older_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            payload = json.loads(config_path.read_text(encoding="utf-8"))
            for chapter in payload["chapters"]:
                chapter["artifact_ids"] = []
            config_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            run_path = start_run(
                config_path,
                run_id="signoff-order",
                run_directory=root / "signed-run",
            )
            target = root / "target.mp4"
            other = root / "other.mp4"
            target.write_bytes(b"TARGET-BYTES")
            # Even identical bytes on another approved deliverable must not
            # resurrect the exact target's superseded approval.
            other.write_bytes(b"TARGET-BYTES")
            preserve_artifact(
                run_path,
                target,
                artifact_id="target-deliverable",
                collection="derived",
                role="deliverable",
                label="target",
                media_type="video/mp4",
            )
            preserve_artifact(
                run_path,
                other,
                artifact_id="other-deliverable",
                collection="derived",
                role="deliverable",
                label="other",
                media_type="video/mp4",
            )
            record_signoff(
                run_path,
                artifact_id="target-deliverable",
                reviewer="Reviewer",
                decision="approved",
                note=None,
                reviewed_at="2026-09-01T00:00:00Z",
            )
            record_signoff(
                run_path,
                artifact_id="target-deliverable",
                reviewer="Reviewer",
                decision="rejected",
                note="supersedes approval",
                reviewed_at="2026-09-01T00:01:00Z",
            )
            record_signoff(
                run_path,
                artifact_id="other-deliverable",
                reviewer="Reviewer",
                decision="approved",
                note=None,
                reviewed_at="2026-09-01T00:02:00Z",
            )
            pipeline_target = PipelineArtifactRecord.from_path(
                target,
                artifact_id="target-deliverable",
                role="deliverable",
                media_type="video/mp4",
            )
            phase = PipelinePhaseRecord(
                1,
                "audit-record-ready",
                "succeeded",
                (pipeline_target.artifact_id,),
            )
            result = PipelineResult(
                "succeeded",
                False,
                root,
                (phase,),
                (pipeline_target,),
                AuditRecordReady(
                    "zhongguo-361-phase2-promo",
                    pipeline_target,
                    (phase,),
                ),
                None,
                False,
            )

            self.assertFalse(
                promo._approved_deliverable(
                    run_path,
                    config_path=config_path,
                    result=result,
                )
            )


if __name__ == "__main__":
    unittest.main()
