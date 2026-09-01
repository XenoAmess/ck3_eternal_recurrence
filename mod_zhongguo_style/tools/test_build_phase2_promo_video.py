#!/usr/bin/env python3
"""Offline/fake-pipeline tests for the phase-two ZhongGuo promo entry."""

from __future__ import annotations

import ast
import contextlib
import hashlib
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

from xar_promo.errors import ArtifactError  # noqa: E402
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
    PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
    PHASE2_PROMO_CAPTURE_MODE,
    PHASE2_PROMO_CAPTURE_PRODUCER_ID,
    PHASE2_PROMO_CAPTURE_SPAN_MAP,
    PHASE2_PROMO_CLEAN_SPAN_IDS,
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
    seed_preflight_report: Path | None = None,
):
    values = [
        "--project-config",
        str(config),
        "--capture-root",
        str(capture),
        "--work-dir",
        str(workdir),
    ]
    if seed_preflight_report is not None:
        values.extend(("--seed-preflight-report", str(seed_preflight_report)))
    if validate_only:
        values.append("--validate-only")
    return promo.parser().parse_args(values)


def _write_seed_preflight_report(
    root: Path,
    *,
    artifact_root: Path,
    **overrides: object,
) -> Path:
    """Write a synthetic contract fixture; it is not CK3/live evidence."""

    root.mkdir(parents=True, exist_ok=True)
    checks = {
        name: "GREEN" for name in promo.SEED_PREFLIGHT_CHECKS
    }
    # The production runner uses evidence objects for its before/after CK3
    # process inventories; keep the fixture in that real wire shape.
    checks["ck3_process_inventory"] = {"result": "GREEN", "running": False}
    checks["ck3_process_inventory_after"] = {"result": "GREEN", "running": False}
    source_clean_tree = "a" * 64
    source_zip_tree = "b" * 64
    product_tree = "c" * 64
    fixture_tree = "d" * 64
    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": promo.SEED_PREFLIGHT_KIND,
        "mode": promo.SEED_PREFLIGHT_MODE,
        "result": promo.SEED_PREFLIGHT_RESULT,
        "status": promo.SEED_PREFLIGHT_STATUS,
        "ok": True,
        "readiness_scope": "frozen_inputs_and_projection_only",
        "seed_ready": False,
        "frozen_git_commit": "d7a28713fca39b70121e47cfa0a9838bf244774c",
        "paths": {"artifacts": str(artifact_root.resolve())},
        "source_identity": {
            "git": {
                "declared_sha": "d7a28713fca39b70121e47cfa0a9838bf244774c",
            },
            "source_zip": {"logical_tree_sha256": source_zip_tree},
            "clean_source_tree": {"tree_sha256": source_clean_tree},
        },
        "desktop_interaction": False,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "ck3_launch_attempted": False,
        "launch_boundary": "not-crossed",
        "native_session_started": False,
        "driver_opened": False,
        "checks": checks,
        "bootstrap": {
            "enabled_mods": list(promo.SEED_PREFLIGHT_ENABLED_MODS),
            "projection_only": True,
            "mounted": False,
            "tree_sha256": {
                "product": product_tree,
                "fixture": fixture_tree,
            },
        },
        "failure_reason": None,
        "failure_evidence": None,
        "traceback": None,
    }
    payload.update(overrides)
    path = root / "preflight.json"
    payload["report_path"] = str(path.resolve())
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _write_capture_timeline(
    root: Path,
    *,
    identity: dict[str, object] | None = None,
) -> Path:
    """Write a tiny source-identity projection, never a gameplay capture."""

    path = root / "cell" / "promo" / "capture-timeline.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "schema": 2,
        "capture_mode": PHASE2_PROMO_CAPTURE_MODE,
        "capture_contract_version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
        "capture_contract": {
            "mode": PHASE2_PROMO_CAPTURE_MODE,
            "version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
            "producer_id": PHASE2_PROMO_CAPTURE_PRODUCER_ID,
            "span_ids": list(PHASE2_PROMO_CLEAN_SPAN_IDS),
            "span_map": [
                {"chapter_id": chapter_id, "producer_key": producer_key}
                for chapter_id, producer_key in PHASE2_PROMO_CAPTURE_SPAN_MAP
            ],
        },
        "source_git_commit": "d7a28713fca39b70121e47cfa0a9838bf244774c",
        "source_clean_tree_sha256": "a" * 64,
        "source_zip_logical_tree_sha256": "b" * 64,
        "source_product_tree_sha256": "c" * 64,
        "source_fixture_tree_sha256": "d" * 64,
    }
    if identity is not None:
        payload.update(identity)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _write_capture_report(root: Path, *, identity: dict[str, object] | None = None) -> Path:
    """Write a synthetic GREEN acceptance report identity projection."""

    path = root / "report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "schema_version": 1,
        "result": "GREEN",
        "cell": {
            "schema_version": 1,
            "result": "GREEN",
            "runtime_tree_before_sha256": {
                "product": "c" * 64,
                "fixture": "d" * 64,
            },
            "product_runtime_manifest": {"tree_sha256": "c" * 64},
        },
    }
    if identity is not None:
        cell = payload["cell"]
        if isinstance(cell, dict):
            cell.update(identity)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


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

    def test_seed_preflight_binding_requires_green_no_launch_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "seed-attempt" / "artifacts"
            capture = root / "capture-attempt"
            timeline = _write_capture_timeline(capture)
            _write_capture_report(capture)
            report = _write_seed_preflight_report(
                artifacts,
                artifact_root=artifacts,
            )

            binding = promo.load_seed_preflight_binding(report, capture)

            self.assertEqual(report.resolve(), binding.path)
            self.assertEqual(report.stat().st_size, binding.bytes)
            self.assertEqual(promo.sha256_file(report), binding.sha256)
            self.assertEqual(artifacts.resolve(), binding.artifact_root)
            self.assertNotEqual(artifacts.resolve(), capture.resolve())
            self.assertEqual(timeline.resolve(), binding.capture_timeline_path)
            self.assertEqual("bound", binding.to_mapping()["capture_identity_status"])
            binding.verify_unchanged()

            timeline.write_text(
                timeline.read_text(encoding="utf-8").replace(
                    '"source_git_commit": "d7a28713fca39b70121e47cfa0a9838bf244774c"',
                    '"source_git_commit": "' + ("e" * 40) + '"',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "capture timeline changed during the attempt",
            ):
                binding.verify_unchanged()

            # Recreate the valid report/binding before exercising report drift.
            timeline.write_text(
                json.dumps(
                    {
                        "schema": 2,
                        "source_git_commit": "d7a28713fca39b70121e47cfa0a9838bf244774c",
                        "source_clean_tree_sha256": "a" * 64,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            binding = promo.load_seed_preflight_binding(report, capture)
            report.write_text(
                report.read_text(encoding="utf-8").replace(
                    '"result": "GREEN"', '"result": "RED"', 1
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "changed during the attempt",
            ):
                binding.verify_unchanged()

    def test_seed_preflight_binding_rejects_crossed_or_unrelated_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "seed-attempt" / "artifacts"
            artifacts.mkdir(parents=True)
            capture = root / "capture-attempt"
            capture.mkdir()

            for overrides, expected in (
                ({"result": "RED"}, "result must be 'GREEN'"),
                ({"launch_boundary": "crossed"}, "launch_boundary must be 'not-crossed'"),
                ({"mcp_only": False}, "mcp_only must be True"),
            ):
                report = _write_seed_preflight_report(
                    artifacts,
                    artifact_root=artifacts,
                    **overrides,
                )
                with self.assertRaisesRegex(promo.Phase2PromoBuildError, expected):
                    promo.load_seed_preflight_binding(report, capture)

            # Keep the minimal report/artifact-root consistency check while
            # allowing the later capture attempt to live elsewhere.
            declared_artifacts = root / "declared-artifacts"
            declared_artifacts.mkdir()
            mislocated_report = _write_seed_preflight_report(
                root / "mislocated-report",
                artifact_root=declared_artifacts,
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "located below paths.artifacts",
            ):
                promo.load_seed_preflight_binding(mislocated_report, capture)

            malformed_report = _write_seed_preflight_report(
                root / "malformed-report",
                artifact_root=root / "malformed-report",
            )
            malformed_payload = json.loads(
                malformed_report.read_text(encoding="utf-8")
            )
            malformed_payload.pop("report_path")
            malformed_report.write_text(
                json.dumps(malformed_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "report_path must be absolute",
            ):
                promo.load_seed_preflight_binding(malformed_report, capture)

            malformed_report = _write_seed_preflight_report(
                root / "malformed-check",
                artifact_root=root / "malformed-check",
            )
            malformed_payload = json.loads(
                malformed_report.read_text(encoding="utf-8")
            )
            malformed_payload["checks"]["config"] = {"result": "GREEN"}
            malformed_report.write_text(
                json.dumps(malformed_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "check config must be GREEN",
            ):
                promo.load_seed_preflight_binding(malformed_report, capture)

            report = _write_seed_preflight_report(artifacts, artifact_root=artifacts)
            unbound_capture = root / "other-attempt" / "capture"
            unbound_capture.mkdir(parents=True)
            binding = promo.load_seed_preflight_binding(report, unbound_capture)
            self.assertEqual("unbound", binding.to_mapping()["capture_identity_status"])
            self.assertTrue(
                any("capture_identity_unbound" in item for item in binding.release_blockers)
            )

            mismatch_timeline = _write_capture_timeline(
                unbound_capture,
                identity={
                    "source_git_commit": "e" * 40,
                },
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "source identity does not match",
            ):
                promo.load_seed_preflight_binding(report, unbound_capture)
            self.assertTrue(mismatch_timeline.is_file())

    def test_capture_report_identity_binds_sparse_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "seed-attempt" / "artifacts"
            capture = root / "capture-attempt"
            timeline = _write_capture_timeline(capture)
            timeline.write_text(
                json.dumps({"schema": 2, "marks": []}, indent=2) + "\n",
                encoding="utf-8",
            )
            capture_report = _write_capture_report(capture)
            report = _write_seed_preflight_report(
                artifacts,
                artifact_root=artifacts,
            )

            binding = promo.load_seed_preflight_binding(report, capture)

            self.assertEqual("bound", binding.to_mapping()["capture_identity_status"])
            self.assertEqual(capture_report.resolve(), binding.capture_report_path)
            self.assertEqual(
                capture_report.stat().st_size,
                binding.capture_report_bytes,
            )
            self.assertEqual(
                promo.sha256_file(capture_report),
                binding.capture_report_sha256,
            )
            self.assertEqual(timeline.stat().st_size, binding.capture_timeline_bytes)
            self.assertEqual(
                promo.sha256_file(timeline),
                binding.capture_timeline_sha256,
            )
            self.assertEqual(
                {"C" * 64, "D" * 64},
                {
                    binding.to_mapping()["capture_identity"][
                        "source_product_tree_sha256"
                    ],
                    binding.to_mapping()["capture_identity"][
                        "source_fixture_tree_sha256"
                    ],
                },
            )
            binding.verify_unchanged()

            capture_report.write_text(
                capture_report.read_text(encoding="utf-8").replace(
                    '"result": "GREEN"', '"result": "RED"', 1
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "capture report changed during the attempt",
            ):
                binding.verify_unchanged()

            missing_report_capture = root / "sparse-without-report"
            missing_timeline = _write_capture_timeline(missing_report_capture)
            missing_timeline.write_text(
                json.dumps({"schema": 2, "marks": []}, indent=2) + "\n",
                encoding="utf-8",
            )
            unbound = promo.load_seed_preflight_binding(
                report,
                missing_report_capture,
            )
            self.assertEqual(
                "unbound",
                unbound.to_mapping()["capture_identity_status"],
            )
            self.assertTrue(
                any(
                    "capture_identity_unbound" in item
                    for item in unbound.release_blockers
                )
            )

            # A matching timeline identity is not sufficient on its own: the
            # CK3 adapter also requires the GREEN root report.  Keep the
            # source identity for diagnosis, but retain a typed unbound
            # blocker instead of reporting a falsely bound capture.
            timeline_only_capture = root / "timeline-identity-without-report"
            _write_capture_timeline(timeline_only_capture)
            timeline_only = promo.load_seed_preflight_binding(
                report,
                timeline_only_capture,
            )
            self.assertEqual(
                "unbound",
                timeline_only.to_mapping()["capture_identity_status"],
            )
            self.assertEqual(
                "d7a28713fca39b70121e47cfa0a9838bf244774c",
                timeline_only.to_mapping()["capture_identity"]["source_git_commit"],
            )
            self.assertTrue(
                any(
                    "capture report is missing" in item
                    for item in timeline_only.release_blockers
                )
            )

    def test_bound_seed_preflight_is_recorded_and_preserved_in_candidate_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            artifacts = root / "seed-attempt" / "artifacts"
            capture = root / "capture-attempt"
            _write_capture_timeline(capture)
            _write_capture_report(capture)
            report = _write_seed_preflight_report(
                artifacts,
                artifact_root=artifacts,
            )
            workdir = root / "candidate-attempt"
            args = _args(
                config_path,
                capture,
                workdir,
                validate_only=False,
                seed_preflight_report=report,
            )

            outcome = promo.execute(
                args,
                composer_factory=_RealDurationFakeComposer,
                pipeline_runner=lambda _invocation, **_kwargs: _successful_result(
                    workdir,
                    load_phase2_project_config(config_path),
                ),
            )

            self.assertIsNotNone(outcome.seed_preflight)
            self.assertEqual(report.resolve(), outcome.seed_preflight.path)
            self.assertNotIn(
                "seed preflight report is not bound",
                " ".join(outcome.blockers),
            )
            summary = json.loads(
                (workdir / "phase2-pipeline-result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                outcome.seed_preflight.to_mapping(),
                summary["seed_preflight"],
            )
            loaded = load_document(outcome.run_manifest_path, check_files=True)
            self.assertIsNotNone(loaded.run)
            preflight_artifacts = [
                artifact
                for artifact in loaded.run.artifacts
                if artifact.artifact_id == promo.SEED_PREFLIGHT_ARTIFACT_ID
            ]
            self.assertEqual(1, len(preflight_artifacts))
            self.assertEqual("raw", preflight_artifacts[0].collection)
            self.assertEqual("preflight", preflight_artifacts[0].role)

    def test_unbound_seed_preflight_is_an_explicit_release_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "candidate-attempt"
            args = _args(
                config_path,
                root / "capture",
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

            self.assertFalse(outcome.release_ready)
            self.assertIsNone(outcome.seed_preflight)
            self.assertIn(
                "phase-two seed preflight report is not bound",
                " ".join(outcome.blockers),
            )
            summary = json.loads(
                (workdir / "phase2-pipeline-result.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(summary["seed_preflight"])

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

    def test_checked_in_cli_validate_only_preserves_no_write_boundary(self) -> None:
        """Exercise the documented executable preflight, not only ``execute``."""

        config_before = hashlib.sha256(CHECKED_CONFIG.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = root / "capture-root-not-created"
            workdir = root / "work-dir-not-created"
            tts_cache = root / "tts-cache-not-read"
            ffmpeg = root / "ffmpeg-not-run.exe"
            ffprobe = root / "ffprobe-not-run.exe"
            zh_font = root / "zh-font-not-read.ttf"
            en_font = root / "en-font-not-read.ttf"
            arguments = [
                "--project-config",
                str(CHECKED_CONFIG),
                "--capture-root",
                str(capture),
                "--work-dir",
                str(workdir),
                "--tts-cache",
                str(tts_cache),
                "--ffmpeg",
                str(ffmpeg),
                "--ffprobe",
                str(ffprobe),
                "--zh-font-file",
                str(zh_font),
                "--en-font-file",
                str(en_font),
                "--run-id",
                "phase2-cli-preflight-test",
                "--validate-only",
            ]
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = promo.main(arguments)

            self.assertEqual(2, exit_code)
            self.assertEqual("", stdout.getvalue())
            error = stderr.getvalue()
            self.assertIn("RELEASE: RED", error)
            self.assertIn("phase-two project remains planned", error)
            self.assertNotIn("Traceback", error)
            for sentinel in (
                capture,
                workdir,
                tts_cache,
                ffmpeg,
                ffprobe,
                zh_font,
                en_font,
            ):
                self.assertFalse(sentinel.exists(), sentinel)
            self.assertEqual(
                config_before,
                hashlib.sha256(CHECKED_CONFIG.read_bytes()).hexdigest(),
            )

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

    def test_candidate_run_persistence_failure_retains_partial_and_red_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "candidate-persistence-failure"
            args = _args(
                config_path,
                root / "fake-live-capture",
                workdir,
                validate_only=False,
            )
            original = ArtifactError(
                "refusing to overwrite conflicting artifact: target.mp4"
            )

            real_preserve = promo.preserve_artifact

            def fail_deliverable_preserve(run_path, source, **kwargs):
                if kwargs.get("artifact_id") == promo.DELIVERABLE_ARTIFACT_ID:
                    raise original
                return real_preserve(run_path, source, **kwargs)

            with mock.patch.object(
                promo,
                "preserve_artifact",
                side_effect=fail_deliverable_preserve,
            ):
                with self.assertRaisesRegex(
                    ArtifactError,
                    "refusing to overwrite conflicting artifact",
                ) as raised:
                    promo.execute(
                        args,
                        composer_factory=_RealDurationFakeComposer,
                        pipeline_runner=lambda _invocation, **_kwargs: _successful_result(
                            workdir,
                            load_phase2_project_config(config_path),
                        ),
                    )

            # The persistence error remains the caller-visible exception; the
            # partially-created candidate run is never cleaned up.
            self.assertIs(raised.exception, original)
            partial_manifest = workdir / "candidate-run" / "run-manifest.json"
            self.assertTrue(partial_manifest.is_file())
            loaded_partial = load_document(partial_manifest, check_files=True)
            self.assertIsNotNone(loaded_partial.run)
            self.assertEqual(10, len(loaded_partial.run.artifacts))
            receipt_path = workdir / "phase2-entry-failure.json"
            self.assertTrue(receipt_path.is_file())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual("RED", receipt["status"])
            self.assertEqual("candidate-run-persistence", receipt["phase"])
            self.assertEqual("ArtifactError", receipt["exception_type"])
            self.assertIn("conflicting artifact", receipt["message"])
            self.assertEqual(
                [str((workdir / "candidate-run").resolve())],
                receipt["retained_paths"],
            )
            self.assertTrue((workdir / "phase2-pipeline-result.json").is_file())

    def test_candidate_run_persistence_error_is_not_masked_by_receipt_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            workdir = root / "candidate-persistence-receipt-failure"
            args = _args(
                config_path,
                root / "fake-live-capture",
                workdir,
                validate_only=False,
            )
            original = ArtifactError("candidate target conflict")

            with (
                mock.patch.object(promo, "_persist_candidate_run", side_effect=original),
                mock.patch.object(
                    promo,
                    "_write_entry_failure",
                    side_effect=OSError("receipt filesystem unavailable"),
                ),
            ):
                with self.assertRaisesRegex(
                    ArtifactError,
                    "candidate target conflict",
                ) as raised:
                    promo.execute(
                        args,
                        composer_factory=_RealDurationFakeComposer,
                        pipeline_runner=lambda _invocation, **_kwargs: _successful_result(
                            workdir,
                            load_phase2_project_config(config_path),
                        ),
                    )

            self.assertIs(raised.exception, original)
            self.assertTrue(
                any(
                    "could not write phase2-entry-failure.json" in note
                    for note in getattr(raised.exception, "__notes__", ())
                )
            )

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
