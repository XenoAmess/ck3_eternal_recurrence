from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from xar_promo.evidence import (  # noqa: E402
    bind_external_artifact,
    write_evidence_bundle,
    write_sampling_plan,
)
from xar_promo.model import ProjectConfig, new_project_config  # noqa: E402
from xar_promo.operations import record_signoff, start_run  # noqa: E402
from xar_promo.pipeline import (  # noqa: E402
    PipelineDependencies,
    PipelineDraft,
    PipelineInvocation,
    SegmentDraft,
)
from xar_promo.pipeline_commands import (  # noqa: E402
    CommandOutcome,
    handle_audit,
    handle_build,
    handle_plan,
)
from xar_promo.process import CommandResult, CommandSpec, run_command  # noqa: E402
from xar_promo.project import load_document  # noqa: E402
from xar_promo.registry import ComponentRegistry  # noqa: E402
from xar_promo.render import RenderOptions  # noqa: E402
from xar_promo.runlog import (  # noqa: E402
    automated_audit_records_from_run,
    phase_records_from_run,
)
from xar_promo.sources import (  # noqa: E402
    GENERATED_CARD,
    STILL,
    VisualProbeResult,
    VisualSource,
)
from xar_promo.storyboard import TimelineSpacing, plan_storyboard  # noqa: E402


class _CountingFactory:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def __call__(self, *_: object, **__: object) -> object:
        self.calls += 1
        raise AssertionError(
            f"registry resolution must not invoke {self.name} directly"
        )


class _CommandRunner:
    def __init__(self, *, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.calls: list[tuple[CommandSpec, Path]] = []

    def __call__(
        self,
        spec: CommandSpec,
        *,
        audit_directory: Path,
    ) -> CommandResult:
        self.calls.append((spec, audit_directory))
        should_fail = self.fail_first and len(self.calls) == 1

        def execute(
            argv: list[str],
            **_: object,
        ) -> subprocess.CompletedProcess[str]:
            for partial in spec.partial_artifacts:
                path = partial if partial.is_absolute() else spec.cwd / partial
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(
                    f"materialized:{spec.label}:{len(self.calls)}".encode("utf-8")
                )
            return subprocess.CompletedProcess(
                argv,
                9 if should_fail else 0,
                stdout="retained stdout" if should_fail else "render stdout",
                stderr="retained stderr" if should_fail else "render stderr",
            )

        return run_command(
            spec,
            audit_directory=audit_directory,
            run=execute,
        )


class _FakeComposer:
    def __init__(
        self,
        *,
        visual_path: Path,
        narration_path: Path,
        adapter_factory: _CountingFactory,
        preset_factory: _CountingFactory,
        runner: _CommandRunner | None,
        generated_visual: bool,
    ) -> None:
        self.visual_path = visual_path
        self.narration_path = narration_path
        self.adapter_factory = adapter_factory
        self.preset_factory = preset_factory
        self.runner = runner
        self.generated_visual = generated_visual
        self.calls: list[dict[str, object]] = []
        self.duration_resolver_calls = 0
        self.visual_resolver_calls = 0
        self.visual_probe_calls = 0
        self.subtitle_calls = 0

    def __call__(
        self,
        config: ProjectConfig,
        run: object,
        *,
        config_path: Path,
        run_path: Path | None,
        workdir: Path,
        adapter_factory: object,
        preset_factory: object,
        validate_only: bool,
    ) -> PipelineInvocation:
        if adapter_factory is not self.adapter_factory:
            raise AssertionError("composer received the wrong adapter factory")
        if preset_factory is not self.preset_factory:
            raise AssertionError("composer received the wrong preset factory")

        def duration_resolver(*_: object) -> None:
            self.duration_resolver_calls += 1
            return None

        timeline = plan_storyboard(
            config,
            narration_duration_resolver=duration_resolver,
            draft_estimator=lambda *_: 1,
            spacing=TimelineSpacing(cue_gap_seconds=0, chapter_gap_seconds=0),
            available_artifact_ids=(),
            validate_only=validate_only,
        )
        self.calls.append(
            {
                "run": run,
                "config_path": config_path,
                "run_path": run_path,
                "workdir": workdir,
                "validate_only": validate_only,
                "timeline_seconds": timeline.duration_seconds,
            }
        )

        def visual_resolver(source: VisualSource, *, workdir: Path) -> Path:
            self.visual_resolver_calls += 1
            output = workdir / source.path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"generated visual bytes")
            return output

        def visual_probe(_: Path) -> VisualProbeResult:
            self.visual_probe_calls += 1
            return VisualProbeResult(media_type="image/png", width=640, height=360)

        def subtitle_renderer(*_: object, **__: object) -> str:
            self.subtitle_calls += 1
            return "[Script Info]\nTitle: fake integration\n[Events]\n"

        def forbidden_runner(*_: object, **__: object) -> CommandResult:
            raise AssertionError("validate-only invoked FFmpeg command execution")

        visual_source = VisualSource(
            source_id="visual.cue-001",
            kind=GENERATED_CARD if self.generated_visual else STILL,
            path=(
                Path("generated/card.png")
                if self.generated_visual
                else self.visual_path
            ),
            origin="fake-composer",
            requires_resolution=self.generated_visual,
        )
        segment = SegmentDraft(
            segment_id="cue-001",
            visual_source=visual_source,
            render_options=RenderOptions(
                width=640,
                height=360,
                fps=24,
                duration_seconds=float(timeline.duration_seconds),
            ),
            subtitles={"und": "Subtitle"},
            prepared_narration=self.narration_path,
        )
        dependencies = PipelineDependencies(
            ffmpeg="fake-ffmpeg",
            subtitle_renderer=subtitle_renderer,
            command_runner=self.runner or forbidden_runner,
            visual_probe=visual_probe,
            visual_resolver=visual_resolver if self.generated_visual else None,
        )
        return PipelineInvocation(
            PipelineDraft(
                config=config,
                segments=(segment,),
                deliverable_relative_path=Path("deliverables/final.mp4"),
                deliverable_artifact_id="final-video",
                deliverable_media_type="video/mp4",
            ),
            dependencies,
            workdir,
        )


class PipelineCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir(parents=True)
        config = new_project_config(
            "fake-promo",
            "Fake Promo",
            "und",
            ["und"],
            "fake-adapter",
            "fake-preset",
        ).to_dict()
        config["constraints"]["duration_limit_seconds"] = 30
        config["chapters"] = [
            {
                "id": "chapter-001",
                "type": "feature",
                "state": "ready",
                "title": {"und": "Feature"},
                "cues": [
                    {
                        "id": "cue-001",
                        "narration": {"und": "Narration"},
                        "subtitles": {"und": "Subtitle"},
                    }
                ],
                "artifact_ids": [],
            }
        ]
        self.config_path = self.root / "promo-project.json"
        self.config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.run_path = start_run(self.config_path, run_id="attempt-001")
        self.visual = self.root / "inputs" / "visual.png"
        self.narration = self.root / "inputs" / "narration.wav"
        self.visual.parent.mkdir(parents=True)
        self.visual.write_bytes(b"prepared visual")
        self.narration.write_bytes(b"prepared narration")
        self.adapter_factory = _CountingFactory("adapter")
        self.preset_factory = _CountingFactory("preset")
        self.registry = ComponentRegistry(
            adapters={"fake-adapter": self.adapter_factory},
            presets={"fake-preset": self.preset_factory},
            discover_entry_points=False,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _composer(
        self,
        *,
        runner: _CommandRunner | None = None,
        generated_visual: bool = False,
    ) -> _FakeComposer:
        return _FakeComposer(
            visual_path=self.visual,
            narration_path=self.narration,
            adapter_factory=self.adapter_factory,
            preset_factory=self.preset_factory,
            runner=runner,
            generated_visual=generated_visual,
        )

    def _history_files(self) -> set[Path]:
        return set(
            (self.run_path.parent / "artifacts" / "manifest-history").rglob(
                "*.json"
            )
        )

    def test_plan_on_run_is_strictly_read_only_and_effect_free(self) -> None:
        workdir = self.root / "plan-must-not-exist"
        composer = self._composer(generated_visual=True)
        before_manifest = self.run_path.read_bytes()
        before_history = self._history_files()

        outcome = handle_plan(
            self.run_path,
            workdir=workdir,
            registry=self.registry,
            composer=composer,
        )

        self.assertIsInstance(outcome, CommandOutcome)
        self.assertTrue(outcome.succeeded)
        self.assertEqual(0, outcome.exit_status)
        self.assertEqual("validated", outcome.pipeline_result.status)
        self.assertEqual(before_manifest, self.run_path.read_bytes())
        self.assertEqual(before_history, self._history_files())
        self.assertFalse(workdir.exists())
        self.assertEqual(0, composer.duration_resolver_calls)
        self.assertEqual(0, composer.visual_resolver_calls)
        self.assertEqual(0, composer.visual_probe_calls)
        self.assertEqual(0, composer.subtitle_calls)
        self.assertEqual(0, self.adapter_factory.calls)
        self.assertEqual(0, self.preset_factory.calls)

    def test_plan_accepts_project_config_without_creating_a_run_or_workdir(self) -> None:
        workdir = self.root / "config-plan-must-not-exist"
        composer = self._composer(generated_visual=True)
        before_config = self.config_path.read_bytes()
        before_run = self.run_path.read_bytes()
        before_history = self._history_files()

        outcome = handle_plan(
            self.config_path,
            workdir=workdir,
            registry=self.registry,
            composer=composer,
        )

        self.assertTrue(outcome.succeeded)
        self.assertIsNone(outcome.run_path)
        self.assertIsNone(composer.calls[0]["run"])
        self.assertEqual(before_config, self.config_path.read_bytes())
        self.assertEqual(before_run, self.run_path.read_bytes())
        self.assertEqual(before_history, self._history_files())
        self.assertFalse(workdir.exists())

    def test_missing_registry_component_returns_typed_exit_two_without_writes(self) -> None:
        workdir = self.root / "missing-component-work"
        before = self.run_path.read_bytes()
        empty = ComponentRegistry(discover_entry_points=False)
        outcome = handle_plan(
            self.run_path,
            workdir=workdir,
            registry=empty,
            composer=self._composer(),
        )
        self.assertFalse(outcome.succeeded)
        self.assertEqual(2, outcome.exit_status)
        self.assertEqual("ComponentNotFoundError", outcome.failure.exception_type)
        self.assertEqual(before, self.run_path.read_bytes())
        self.assertFalse(workdir.exists())

    def test_successful_build_preserves_all_outputs_and_typed_phases(self) -> None:
        runner = _CommandRunner()
        composer = self._composer(runner=runner)
        outcome = handle_build(
            self.run_path,
            workdir=self.root / "successful-build",
            registry=self.registry,
            composer=composer,
        )
        self.assertTrue(outcome.succeeded)
        self.assertEqual(0, outcome.exit_status)
        self.assertEqual("succeeded", outcome.pipeline_result.status)
        run = load_document(self.run_path).run
        self.assertIsNotNone(run)
        artifacts = {record.artifact_id: record for record in run.artifacts}
        self.assertIn("final-video", artifacts)
        self.assertEqual("deliverable", artifacts["final-video"].role)
        self.assertGreater(len(outcome.preserved_artifacts), 4)
        phases = phase_records_from_run(run)
        self.assertEqual("build.draft", phases[0].phase_id)
        self.assertEqual("build.audit-record-ready", phases[-1].phase_id)
        self.assertTrue(all(phase.recorded_at.endswith("Z") for phase in phases))
        self.assertEqual((), run.signoffs)
        self.assertGreaterEqual(len(runner.calls), 2)

    def test_failed_build_preserves_partial_logs_and_diagnostics(self) -> None:
        runner = _CommandRunner(fail_first=True)
        workdir = self.root / "failed-build"
        outcome = handle_build(
            self.run_path,
            workdir=workdir,
            registry=self.registry,
            composer=self._composer(runner=runner),
        )
        self.assertFalse(outcome.succeeded)
        self.assertEqual(2, outcome.exit_status)
        self.assertEqual("failed", outcome.pipeline_result.status)
        self.assertTrue(workdir.is_dir())
        failure = outcome.pipeline_result.failure
        self.assertIsNotNone(failure)
        self.assertTrue(failure.partial_paths)
        self.assertEqual(
            b"materialized:render media segment:1",
            failure.partial_paths[0].read_bytes(),
        )
        self.assertEqual("retained stdout", failure.stdout)
        self.assertEqual("retained stderr", failure.stderr)

        run = load_document(self.run_path).run
        self.assertIsNotNone(run)
        roles = {record.role for record in run.artifacts}
        self.assertTrue(
            {"partial-output", "process-stdout", "process-stderr"}.issubset(roles)
        )
        phases = phase_records_from_run(run)
        diagnostics = [
            phase for phase in phases if phase.phase_id == "build.failure-materials"
        ]
        self.assertEqual(1, len(diagnostics))
        self.assertEqual("failed", diagnostics[0].status)
        self.assertGreaterEqual(len(diagnostics[0].artifacts), 3)
        self.assertEqual((), run.signoffs)

    def _evidence_bundle(self, subject_path: Path) -> Path:
        producer_source = {
            "adapter_id": "fake-source",
            "tool": "fake-recorder",
            "tool_version": "1",
            "operation": "capture",
            "execution": "external",
        }
        producer_frame = {
            "adapter_id": "fake-frame",
            "tool": "fake-frame-extractor",
            "tool_version": "1",
            "operation": "extract-frame",
            "execution": "external",
        }
        producer_ocr = {
            "adapter_id": "fake-ocr",
            "tool": "fake-ocr",
            "tool_version": "1",
            "operation": "ocr-frame",
            "execution": "external",
        }
        source = bind_external_artifact(
            subject_path,
            project_root=self.run_path.parent,
            artifact_id="audit-source",
            collection="derived",
            role="capture",
            label="Audit source",
            media_type="video/mp4",
            producer=producer_source,
        )
        plan_path = self.run_path.parent / "audit-inputs" / "plan.json"
        plan = write_sampling_plan(
            plan_path,
            [
                {
                    "id": "chapter-001",
                    "kind": "video",
                    "source": source,
                    "start_seconds": 0,
                    "end_seconds": 1,
                }
            ],
            project_root=self.run_path.parent,
            interval_seconds=1,
            frame_producer=producer_frame,
            ocr_producer=producer_ocr,
        )
        submissions: list[dict[str, Any]] = []
        for sample in plan["samples"]:
            for role, producer, media_type in (
                ("frame", producer_frame, "image/png"),
                ("ocr", producer_ocr, "application/json"),
            ):
                path = (
                    self.run_path.parent
                    / "audit-inputs"
                    / f"{sample['id']}-{role}.bin"
                )
                path.write_bytes(
                    b"identical-frame-bytes"
                    if role == "frame"
                    else f"{sample['id']}:{role}".encode("ascii")
                )
                submissions.append(
                    {
                        "sample_id": sample["id"],
                        "role": role,
                        "path": path,
                        "media_type": media_type,
                        "producer": producer,
                    }
                )
        bundle_path = self.run_path.parent / "audit-inputs" / "bundle.json"
        write_evidence_bundle(
            bundle_path,
            project_root=self.run_path.parent,
            plan_path=plan_path,
            submissions=submissions,
        )
        return bundle_path

    def test_audit_preserves_evidence_and_report_but_never_signs_off(self) -> None:
        build = handle_build(
            self.run_path,
            workdir=self.root / "audit-subject-build",
            registry=self.registry,
            composer=self._composer(runner=_CommandRunner()),
        )
        self.assertTrue(build.succeeded)
        before = load_document(self.run_path).run
        subject = next(
            record for record in before.artifacts if record.artifact_id == "final-video"
        )
        record_signoff(
            self.run_path,
            artifact_id=subject.artifact_id,
            reviewer="Existing Human",
            decision="approved",
            note="Pre-existing and not created by audit",
            reviewed_at="2026-09-01T00:00:00Z",
        )
        before_signoffs = load_document(self.run_path).run.signoffs
        bundle_path = self._evidence_bundle(
            self.run_path.parent / Path(subject.path)
        )

        outcome = handle_audit(
            self.run_path,
            registry=self.registry,
            subject_artifact_id="final-video",
            evidence_bundle_path=bundle_path,
            report_path=Path("audit-output/report.json"),
            report_artifact_id="automated-audit-report",
            created_at_utc="2026-09-01T00:01:00Z",
        )
        self.assertTrue(outcome.succeeded)
        self.assertEqual(0, outcome.exit_status)
        self.assertEqual(
            {"state": "not-provided"},
            outcome.audit_report["manual_signoff"],
        )
        self.assertFalse(
            outcome.audit_report["automated_audit"]["manual_approval_granted"]
        )
        run = load_document(self.run_path).run
        self.assertEqual(before_signoffs, run.signoffs)
        artifacts = {record.artifact_id: record for record in run.artifacts}
        self.assertIn("automated-audit-report", artifacts)
        self.assertIn("evidence-bundle", {record.role for record in run.artifacts})
        self.assertTrue({"frame", "ocr"}.issubset({record.role for record in run.artifacts}))
        audits = automated_audit_records_from_run(run)
        self.assertEqual(1, len(audits))
        self.assertEqual("passed", audits[0].status)
        self.assertEqual("final-video", audits[0].subject.artifact_id)
        self.assertEqual("automated-audit-report", audits[0].report.artifact_id)
        raw_audit = run.audits[0]
        self.assertNotIn("reviewer", raw_audit)
        self.assertNotIn("decision", raw_audit)
        self.assertNotIn("approved", raw_audit)


if __name__ == "__main__":
    unittest.main()
