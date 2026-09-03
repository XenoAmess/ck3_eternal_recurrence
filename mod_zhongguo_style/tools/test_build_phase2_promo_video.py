#!/usr/bin/env python3
"""Offline/fake-pipeline tests for the phase-two ZhongGuo promo entry."""

from __future__ import annotations

import ast
import contextlib
import datetime as dt
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


TOOLS_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = TOOLS_DIRECTORY.parent
REPOSITORY_ROOT = PROJECT_DIRECTORY.parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

# Resolve the external released toolchain (or an explicit
# ``XAR_PROMO_SOURCE``/``XAR_PROMO_TOOLCHAIN_SOURCE`` checkout override) before
# importing the project builder.
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
if str(REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_TOOLS))
from promo_toolchain_loader import ensure_promo_toolchain  # noqa: E402

ensure_promo_toolchain()

import xar_promo  # noqa: E402

import build_phase2_promo_video as promo  # noqa: E402

from xar_promo.errors import ArtifactError  # noqa: E402
from xar_promo.adapters.ck3 import (  # noqa: E402
    CaptureBundle,
    CaptureFile,
    CaptureMark,
    CleanSpan,
)
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
    media_preflight_report: Path | None = None,
    expected_media_preflight_sha256: str | None = None,
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
    if media_preflight_report is not None:
        values.extend(("--media-preflight-report", str(media_preflight_report)))
    if expected_media_preflight_sha256 is not None:
        values.extend(
            ("--expected-media-preflight-sha256", expected_media_preflight_sha256)
        )
    if validate_only:
        values.append("--validate-only")
    return promo.parser().parse_args(values)


def _write_media_preflight_report(
    root: Path,
    *,
    config_path: Path,
    generated_at: dt.datetime | None = None,
) -> tuple[Path, str, dict[str, Path]]:
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "zh_font": root / "msyh.ttc",
        "en_font": root / "segoeui.ttf",
        "ffmpeg": root / "ffmpeg.exe",
        "ffprobe": root / "ffprobe.exe",
    }
    for name, path in files.items():
        path.write_bytes(("BOUND-" + name).encode("ascii"))

    def record(path: Path) -> dict[str, object]:
        return {
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        }

    config = load_phase2_project_config(config_path)
    created = generated_at or dt.datetime.now(dt.timezone.utc)
    expires = created + dt.timedelta(seconds=promo.MEDIA_PREFLIGHT_VALID_FOR_SECONDS)
    source_root = Path("C:/fake-promo-toolchain").resolve()
    payload = {
        "schema_version": 1,
        "kind": promo.MEDIA_PREFLIGHT_KIND,
        "result": "GREEN",
        "scope": promo.MEDIA_PREFLIGHT_SCOPE,
        "generated_at_utc": created.isoformat(timespec="seconds"),
        "valid_for_seconds": promo.MEDIA_PREFLIGHT_VALID_FOR_SECONDS,
        "expires_at_utc": expires.isoformat(timespec="seconds"),
        "project": {
            "id": config.project_id,
            "chapters": len(config.chapters),
            "config": record(config_path),
        },
        "promo_toolchain": {
            "version": xar_promo.__version__,
            "source_root": str(source_root),
            "head": "a" * 40,
            "origin_main": "a" * 40,
            "clean": True,
        },
        "packages": {"edge-tts": "7.2.8", "Pillow": "12.3.0"},
        "voice": {
            "id": promo.PHASE2_POLICY.voice,
            "catalogue_match": promo.PHASE2_POLICY.voice + " Female Warm",
        },
        "fonts": {
            "zh-CN": {"family": "Microsoft YaHei UI", **record(files["zh_font"])},
            "en": {"family": "Segoe UI", **record(files["en_font"])},
        },
        "subtitle_layout": {
            "frame": [promo.WIDTH, promo.HEIGHT],
            "safe_margins": {"left": 90, "top": 64, "right": 90, "bottom": 64},
            "tracks": [
                {
                    "id": "en",
                    "bounds": [110.0, 974.0, 1810.0, 1016.0],
                    "lines": [{"text": "English probe", "width": 200.0, "x": 860.0}],
                },
                {
                    "id": "zh-CN",
                    "bounds": [90.0, 898.0, 1830.0, 958.0],
                    "lines": [{"text": "Chinese probe", "width": 240.0, "x": 840.0}],
                },
            ],
        },
        "media": {
            "ffmpeg": record(files["ffmpeg"]),
            "ffmpeg_version": "fixture ffmpeg",
            "ffprobe": record(files["ffprobe"]),
            "ffprobe_version": "fixture ffprobe",
            "verified_filter": "ass/libass",
            "verified_video_encoder": "libx264",
            "verified_audio_encoder": "aac/48000Hz/stereo",
            "disposable_test_output_retained": False,
        },
    }
    report = root / "media-preflight.json"
    report.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report, hashlib.sha256(report.read_bytes()).hexdigest(), files


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
        bundle = SimpleNamespace(
            artifact_root=capture_root,
            # Full-build entry tests use a light fake bundle; production
            # candidates receive the real CaptureBundle verifier.
            verify_unchanged=lambda: None,
        )
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


def _capture_file(path: Path, root: Path) -> CaptureFile:
    resolved = path.resolve()
    return CaptureFile(
        resolved.relative_to(root.resolve()).as_posix(),
        resolved,
        resolved.stat().st_size,
        promo.sha256_file(resolved),
    )


def _minimal_capture_bundle(root: Path) -> CaptureBundle:
    """Build a tiny real CaptureBundle for source-drift entry tests."""

    capture_root = root / "capture-source"
    raw = capture_root / "cell" / "promo" / "raw" / "take-01.mkv"
    report = capture_root / "report.json"
    timeline = capture_root / "cell" / "promo" / "capture-timeline.json"
    index = capture_root / "evidence-index.json"
    frame = capture_root / "cell" / "promo" / "proof" / "frame.png"
    for path, payload in (
        (raw, b"raw-capture"),
        (report, b"report"),
        (timeline, b"timeline"),
        (index, b"index"),
        (frame, b"frame-proof"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    frame_record = _capture_file(frame, capture_root)
    return CaptureBundle(
        artifact_root=capture_root.resolve(),
        timeline_schema=2,
        source_kind="real CK3 desktop capture after gameplay HUD",
        report=_capture_file(report, capture_root),
        timeline=_capture_file(timeline, capture_root),
        evidence_index=_capture_file(index, capture_root),
        raw_capture=_capture_file(raw, capture_root),
        marks=(
            CaptureMark("recording_started_after_gameplay_hud", 0.0),
            CaptureMark("feature_demo_clean_begin", 1.0),
            CaptureMark("feature_demo_clean_end", 2.0),
            CaptureMark("recording_stop_requested", 3.0),
        ),
        clean_spans=(
            CleanSpan(
                "feature_demo",
                "feature_demo_clean_begin",
                "feature_demo_clean_end",
                1.0,
                2.0,
                (frame_record,),
            ),
        ),
        recording_start_seconds=0.0,
        recording_stop_seconds=3.0,
    )


class _BundleFakeComposer(_RealDurationFakeComposer):
    def __init__(self, *, bundle: CaptureBundle, **kwargs) -> None:
        self._bundle = bundle
        super().__init__(**kwargs)

    def __call__(self, config, run, **kwargs):
        self.config = config
        self.calls.append((config, run, kwargs))
        self.capture_candidate = _candidate(
            config,
            self.capture_root,
            bundle=self._bundle,
        )
        return SimpleNamespace(workdir=kwargs["workdir"])


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
    def test_dual_cut_contracts_use_unique_run_artifact_and_output_ids(self) -> None:
        promo_root = PROJECT_DIRECTORY / "promo"
        character_config = promo_root / "phase2-promo-character-project.json"
        institution_config = promo_root / "phase2-promo-institution-project.json"
        character = promo.select_cut(character_config)
        institution = promo.select_cut(institution_config)
        for config_path in (character_config, institution_config):
            loaded = load_phase2_project_config(config_path)
            self.assertEqual(loaded.project_id, "zhongguo-361-phase2-promo")
            self.assertEqual(len(loaded.chapters), 10)
        self.assertNotEqual(character.cut_id, institution.cut_id)
        self.assertNotEqual(character.default_run_id, institution.default_run_id)
        self.assertNotEqual(
            character.deliverable_artifact_id,
            institution.deliverable_artifact_id,
        )
        self.assertNotEqual(
            character.deliverable_relative_path,
            institution.deliverable_relative_path,
        )
        self.assertEqual(
            character.default_run_id, "phase2-character-led-candidate"
        )
        self.assertEqual(
            institution.default_run_id, "phase2-institution-led-candidate"
        )
        self.assertEqual(
            character.deliverable_artifact_id,
            "zhongguo-361-phase2-character-led-video",
        )
        self.assertEqual(
            institution.deliverable_artifact_id,
            "zhongguo-361-phase2-institution-led-video",
        )
        self.assertEqual(
            character.deliverable_relative_path.name,
            "zhongguo-361-phase2-character-led.mp4",
        )
        self.assertEqual(
            institution.deliverable_relative_path.name,
            "zhongguo-361-phase2-institution-led.mp4",
        )
        with self.assertRaisesRegex(promo.Phase2PromoBuildError, "requires project config"):
            promo.select_cut(
                promo_root / "phase2-promo-character-project.json",
                "institution-led",
            )

    def test_toolchain_identity_probes_bind_safe_directory_to_exact_checkout(self) -> None:
        source = Path("C:/promo/toolchain")
        responses = iter(
            (
                subprocess.CompletedProcess([], 0, "a" * 40 + "\n", ""),
                subprocess.CompletedProcess([], 0, "a" * 40 + "\n", ""),
                subprocess.CompletedProcess([], 0, "\n", ""),
            )
        )

        with mock.patch.object(promo, "PACKAGE_SOURCE", source), mock.patch.object(
            promo.subprocess, "run", side_effect=lambda *args, **_kwargs: next(responses)
        ) as run:
            identity = promo._current_toolchain_identity()

        safe_root = str(source.resolve())
        self.assertEqual(identity["head"], "a" * 40)
        self.assertEqual(identity["origin_main"], "a" * 40)
        self.assertTrue(identity["clean"])
        self.assertEqual(run.call_count, 3)
        for call in run.call_args_list:
            command = list(call.args[0])
            self.assertEqual(
                command[:5],
                ["git", "-c", f"safe.directory={safe_root}", "-C", safe_root],
            )

    def setUp(self) -> None:
        _FakeComposer.instances.clear()
        _RealDurationFakeComposer.instances.clear()
        _OverlongFakeComposer.instances.clear()
        self.real_footage_validator = promo.validate_footage_intake
        self.footage_validator_patch = mock.patch.object(
            promo,
            "validate_footage_intake",
            return_value={
                "schema_version": 1,
                "kind": "zg361_phase2_footage_intake",
                "scope": "phase2_media_entry_only_no_native_observer_schema",
                "result": "GREEN",
                "reason_code": None,
                "errors": [],
            },
        )
        self.footage_validator_patch.start()
        self.addCleanup(self.footage_validator_patch.stop)

    @staticmethod
    def _media_identity() -> dict[str, object]:
        return {
            "source_root": Path("C:/fake-promo-toolchain").resolve(),
            "head": "a" * 40,
            "origin_main": "a" * 40,
            "clean": True,
        }

    def test_media_preflight_is_hash_bound_unexpired_and_rechecked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, digest, files = _write_media_preflight_report(
                root / "media",
                config_path=CHECKED_CONFIG,
            )
            config = load_phase2_project_config(CHECKED_CONFIG)
            with mock.patch.object(
                promo,
                "_current_toolchain_identity",
                return_value=self._media_identity(),
            ):
                binding = promo.load_media_preflight_binding(
                    report,
                    digest,
                    project_config=config,
                    edge_tts_version=promo.DEFAULT_EDGE_TTS_VERSION,
                    ffmpeg=str(files["ffmpeg"]),
                    ffprobe=str(files["ffprobe"]),
                    zh_font_file=files["zh_font"],
                    en_font_file=files["en_font"],
                )
                self.assertEqual(report.resolve(), binding.path)
                self.assertEqual(digest.upper(), binding.sha256)
                self.assertEqual(4, len(binding.tracked_files))
                binding.verify_unchanged()
                original_font = files["zh_font"].read_bytes()
                files["zh_font"].write_bytes(original_font + b"-changed")
                with self.assertRaisesRegex(
                    promo.Phase2PromoBuildError,
                    "dependency changed during the attempt",
                ):
                    binding.verify_unchanged()
                files["zh_font"].write_bytes(original_font)
                report.write_text(
                    report.read_text(encoding="utf-8") + " ",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    promo.Phase2PromoBuildError,
                    "changed during the attempt",
                ):
                    binding.verify_unchanged()

    def test_media_preflight_rejects_expired_and_wrong_hash_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)
            report, digest, files = _write_media_preflight_report(
                root / "media",
                config_path=CHECKED_CONFIG,
                generated_at=old,
            )
            config = load_phase2_project_config(CHECKED_CONFIG)
            kwargs = {
                "project_config": config,
                "edge_tts_version": promo.DEFAULT_EDGE_TTS_VERSION,
                "ffmpeg": str(files["ffmpeg"]),
                "ffprobe": str(files["ffprobe"]),
                "zh_font_file": files["zh_font"],
                "en_font_file": files["en_font"],
            }
            with mock.patch.object(
                promo,
                "_current_toolchain_identity",
                return_value=self._media_identity(),
            ):
                with self.assertRaisesRegex(promo.Phase2PromoBuildError, "expired"):
                    promo.load_media_preflight_binding(report, digest, **kwargs)
                with self.assertRaisesRegex(
                    promo.Phase2PromoBuildError,
                    "SHA-256 does not match",
                ):
                    promo.load_media_preflight_binding(report, "0" * 64, **kwargs)

    def test_planned_authoring_stays_red_with_valid_media_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, digest, files = _write_media_preflight_report(
                root / "media",
                config_path=CHECKED_CONFIG,
            )
            workdir = root / "must-not-exist"
            args = _args(
                CHECKED_CONFIG,
                root / "missing-capture",
                workdir,
                validate_only=True,
                media_preflight_report=report,
                expected_media_preflight_sha256=digest,
            )
            args.ffmpeg = str(files["ffmpeg"])
            args.ffprobe = str(files["ffprobe"])
            args.zh_font_file = files["zh_font"]
            args.en_font_file = files["en_font"]
            runner = mock.Mock()
            with mock.patch.object(
                promo,
                "_current_toolchain_identity",
                return_value=self._media_identity(),
            ):
                with self.assertRaisesRegex(promo.Phase2PromoBuildError, "remains planned"):
                    promo.execute(args, pipeline_runner=runner)
            runner.assert_not_called()
            self.assertFalse(workdir.exists())

    def test_footage_pending_stops_before_authoring_tts_pipeline_or_workdir(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, digest, files = _write_media_preflight_report(
                root / "media",
                config_path=CHECKED_CONFIG,
            )
            capture = root / "missing-capture"
            for validate_only in (True, False):
                with self.subTest(validate_only=validate_only):
                    workdir = root / f"must-not-exist-{validate_only}"
                    tts_cache = root / f"tts-must-not-be-read-{validate_only}"
                    args = _args(
                        CHECKED_CONFIG,
                        capture,
                        workdir,
                        validate_only=validate_only,
                        media_preflight_report=report,
                        expected_media_preflight_sha256=digest,
                    )
                    args.tts_cache = tts_cache
                    args.ffmpeg = str(files["ffmpeg"])
                    args.ffprobe = str(files["ffprobe"])
                    args.zh_font_file = files["zh_font"]
                    args.en_font_file = files["en_font"]
                    composer = mock.Mock()
                    runner = mock.Mock()
                    with mock.patch.object(
                        promo,
                        "_current_toolchain_identity",
                        return_value=self._media_identity(),
                    ):
                        with self.assertRaises(promo.Phase2FootagePending) as raised:
                            promo.execute(
                                args,
                                composer_factory=composer,
                                pipeline_runner=runner,
                                footage_validator=self.real_footage_validator,
                            )

                    self.assertEqual(
                        raised.exception.reason_code, "footage_pending"
                    )
                    self.assertEqual(raised.exception.report["result"], "RED")
                    self.assertEqual(
                        raised.exception.report["scope"],
                        "phase2_media_entry_only_no_native_observer_schema",
                    )
                    self.assertEqual(
                        raised.exception.report["dependency_graph"],
                        promo.final_promo_execution_dag(),
                    )
                    composer.assert_not_called()
                    runner.assert_not_called()
                    self.assertFalse(capture.exists())
                    self.assertFalse(tts_cache.exists())
                    self.assertFalse(workdir.exists())

    def test_full_candidate_preserves_bound_media_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            report, digest, files = _write_media_preflight_report(
                root / "media",
                config_path=config_path,
            )
            workdir = root / "candidate"
            args = _args(
                config_path,
                root / "capture",
                workdir,
                validate_only=False,
                media_preflight_report=report,
                expected_media_preflight_sha256=digest,
            )
            args.ffmpeg = str(files["ffmpeg"])
            args.ffprobe = str(files["ffprobe"])
            args.zh_font_file = files["zh_font"]
            args.en_font_file = files["en_font"]
            with mock.patch.object(
                promo,
                "_current_toolchain_identity",
                return_value=self._media_identity(),
            ):
                outcome = promo.execute(
                    args,
                    composer_factory=_RealDurationFakeComposer,
                    pipeline_runner=lambda _invocation, **_kwargs: _successful_result(
                        workdir,
                        load_phase2_project_config(config_path),
                    ),
                )
            self.assertIsNotNone(outcome.media_preflight)
            self.assertNotIn("media environment preflight is not bound", " ".join(outcome.blockers))
            summary = json.loads(
                (workdir / "phase2-pipeline-result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(outcome.media_preflight.to_mapping(), summary["media_preflight"])
            self.assertEqual("GREEN", summary["footage_intake"]["result"])
            self.assertEqual(
                promo.final_promo_execution_dag(), summary["dependency_graph"]
            )
            loaded = load_document(outcome.run_manifest_path, check_files=True)
            artifacts = [
                artifact
                for artifact in loaded.run.artifacts
                if artifact.artifact_id == promo.MEDIA_PREFLIGHT_ARTIFACT_ID
            ]
            self.assertEqual(1, len(artifacts))
            self.assertEqual(("raw", "preflight"), (artifacts[0].collection, artifacts[0].role))

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

    def test_capture_source_mutation_after_pipeline_is_red_and_retained(self) -> None:
        """A source changed by the fake runner cannot become a candidate."""

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = _write_ready_config(root)
            for target_name in ("raw", "clean-frame-evidence"):
                with self.subTest(target=target_name):
                    capture_root = root / target_name
                    bundle = _minimal_capture_bundle(capture_root)
                    workdir = root / f"attempt-{target_name}"
                    args = _args(
                        config_path,
                        bundle.artifact_root,
                        workdir,
                        validate_only=False,
                    )

                    target = (
                        bundle.raw_capture.path
                        if target_name == "raw"
                        else bundle.clean_spans[0].evidence[0].path
                    )

                    def mutate_then_succeed(_invocation, **_kwargs):
                        target.write_bytes(target.read_bytes() + b"-mutated")
                        return _successful_result(
                            workdir,
                            load_phase2_project_config(config_path),
                        )

                    with self.assertRaisesRegex(
                        promo.Phase2PromoBuildError,
                        "capture source changed after bundle load",
                    ):
                        promo.execute(
                            args,
                            composer_factory=lambda **kwargs: _BundleFakeComposer(
                                bundle=bundle,
                                **kwargs,
                            ),
                            pipeline_runner=mutate_then_succeed,
                        )

                    receipt_path = workdir / "phase2-entry-failure.json"
                    self.assertTrue(receipt_path.is_file())
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                    self.assertEqual("RED", receipt["status"])
                    self.assertEqual(
                        "capture-source-immutability",
                        receipt["phase"],
                    )
                    self.assertIn(
                        "capture source changed after bundle load",
                        receipt["message"],
                    )
                    self.assertFalse((workdir / "candidate-run").exists())

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

    def test_institution_cut_reorders_front_end_and_reprises_without_changing_sources(self) -> None:
        cut = promo.cut_for_id("institution-led")
        chapters = tuple(
            SimpleNamespace(chapter_id=chapter_id)
            for chapter_id in promo.LEGACY_CUT.editorial_chapter_order
        )
        segments = {}
        for chapter in chapters:
            chapter_id = chapter.chapter_id
            segments[chapter_id] = [
                promo.SegmentDraft(
                    segment_id=chapter_id,
                    visual_source=promo.VisualSource(
                        f"visual.{chapter_id}",
                        promo.VIDEO,
                        Path("same-canonical-capture.mkv"),
                        "ck3-capture-bundle",
                        metadata={"clean_span_id": chapter_id},
                    ),
                    render_options=promo.RenderOptions(
                        width=1920,
                        height=1080,
                        fps=30,
                        duration_seconds=5,
                    ),
                    subtitles={},
                )
            ]
        result = promo._apply_editorial_cut(
            SimpleNamespace(chapters=chapters), segments, cut
        )
        ids = [segment.segment_id for segment in result]
        self.assertEqual(12, len(ids))
        self.assertLess(
            ids.index("phase2_manager_governance"),
            ids.index("phase2_receipt_appeal_pip"),
        )
        self.assertEqual(
            "phase2_receipt_appeal_pip.reprise1",
            ids[ids.index("phase2_projects_metrics") + 1],
        )
        self.assertEqual(
            "phase2_manager_governance.reprise2",
            ids[ids.index("phase2_cross_cycle_endgame") + 1],
        )
        self.assertEqual(
            "phase2_receipt_appeal_pip",
            result[ids.index("phase2_receipt_appeal_pip.reprise1")]
            .visual_source.metadata["clean_span_id"],
        )
        for reprise_id in (
            "phase2_receipt_appeal_pip.reprise1",
            "phase2_manager_governance.reprise2",
        ):
            reprise = result[ids.index(reprise_id)]
            self.assertEqual(2.0, reprise.render_options.duration_seconds)
            self.assertIsNone(reprise.narration_request)
            self.assertIsNone(reprise.prepared_narration)
            self.assertEqual("generated-silence", reprise.visual_source.metadata["editorial_reprise_narration"])
            self.assertEqual("none", reprise.visual_source.metadata["editorial_reprise_claim"])
            self.assertEqual(
                {"zh-CN": "制度回声", "en": "INSTITUTIONAL ECHO"},
                dict(reprise.subtitles),
            )

    def test_reprise_silence_is_exact_and_refuses_non_reprise(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = promo.VisualSource(
                "visual.reprise",
                promo.VIDEO,
                Path("capture.mkv"),
                "ck3-capture-bundle",
                metadata={"editorial_reprise": True},
            )
            segment = promo.SegmentDraft(
                segment_id="segment.reprise",
                visual_source=source,
                render_options=promo.RenderOptions(
                    width=1920,
                    height=1080,
                    fps=30,
                    duration_seconds=2.0,
                ),
                subtitles={"zh-CN": "制度回声", "en": "INSTITUTIONAL ECHO"},
            )
            artifact = promo._RepriseSilenceResolver()(segment, workdir=root)
            self.assertEqual("editorial-reprise-silence", artifact.origin)
            self.assertTrue(artifact.metadata["no_extra_narration"])
            with wave.open(str(artifact.path), "rb") as wav:
                self.assertEqual(48_000, wav.getframerate())
                self.assertEqual(2, wav.getnchannels())
                self.assertEqual(96_000, wav.getnframes())
                self.assertEqual(
                    b"\x00" * 256,
                    wav.readframes(64),
                )

            non_reprise = promo.replace(
                segment,
                segment_id="segment.normal",
                visual_source=promo.replace(source, metadata={}),
            )
            with self.assertRaisesRegex(
                promo.Phase2PromoBuildError,
                "no prepared Xiaoxiao narration",
            ):
                promo._RepriseSilenceResolver()(non_reprise, workdir=root)

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
