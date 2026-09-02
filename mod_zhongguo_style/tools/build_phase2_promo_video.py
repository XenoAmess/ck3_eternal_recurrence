#!/usr/bin/env python3
"""Build or validate the ZhongGuo 361 phase-two promo candidate.

This entry point is intentionally project-specific.  It resolves the reusable
``xar_promo`` registry/pipeline with the CK3 capture adapter and the ZhongGuo
phase-two preset, while keeping voice, sequel scope, real-character provenance,
and clean-capture policy out of the generic package.

``--validate-only`` is read-only.  A full build consumes an already-populated,
content-addressed Edge TTS cache, probes the real narration durations, and
retains the complete attempt.  It never invokes OCR or silently synthesizes
missing narration.  Rendering a candidate is not a release approval: missing
phase-two live claims or a byte-bound human sign-off remains RED. Release,
export, and external publication also require a fresh byte-bound receipt from
``preflight_phase2_media.py`` preserved in the signed candidate run.

Both modes run the same strict footage intake immediately after an optional
fresh media receipt is bound and before authoring, TTS-cache access, composer
construction, pipeline invocation, or work-directory creation.  A RED intake
raises typed ``footage_pending`` and creates no attempt artifact.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
if str(REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_TOOLS))

from promo_toolchain_loader import (  # noqa: E402
    PROMO_TOOLCHAIN_VERSION,
    ensure_promo_toolchain,
)
from zhongguo_phase2_footage_intake import (  # noqa: E402
    final_promo_execution_dag,
    validate_footage_intake,
)


# The reusable package is installed from the independent GitHub release in
# normal runs.  ``XAR_PROMO_SOURCE`` (or the longer compatibility alias) may
# explicitly point at a checkout/src directory for local development.
PACKAGE_SOURCE = ensure_promo_toolchain()

import xar_promo  # noqa: E402
from xar_promo.errors import ArtifactError, ManifestError, PromoToolchainError  # noqa: E402
from xar_promo.adapters.ck3 import CK3CaptureError  # noqa: E402
from xar_promo.layout import FontSpec, SafeArea, WrapPolicy  # noqa: E402
from xar_promo.media import probe_media, require_streams  # noqa: E402
from xar_promo.operations import preserve_artifact, start_run  # noqa: E402
from xar_promo.pipeline import (  # noqa: E402
    PipelineDependencies,
    PipelineDraft,
    PipelineInvocation,
    PipelineResult,
    SegmentDraft,
    run_invocation,
)
from xar_promo.presets.zhongguo_361_phase2 import (  # noqa: E402
    ADAPTER_ID,
    CAPTURE_CHAPTER_KIND,
    GENERATED_CHAPTER_KIND,
    PHASE2_POLICY,
    PRESET_ID,
    Phase2CaptureCandidate,
    build_narration_request,
    load_phase2_capture_candidate,
    load_phase2_project_config,
    validate_phase2_project_config,
    validate_rendered_duration,
)
from xar_promo.process import CommandResult, run_command  # noqa: E402
from xar_promo.project import load_document, sha256_file, validate_profile  # noqa: E402
from xar_promo.registry import ComponentRegistry  # noqa: E402
from xar_promo.render import RenderOptions  # noqa: E402
from xar_promo.sources import (  # noqa: E402
    GENERATED_CARD,
    VIDEO,
    VisualProbeResult,
    VisualSource,
)
from xar_promo.storyboard import (  # noqa: E402
    ResolvedNarrationDuration,
    TimelineSpacing,
    plan_storyboard,
)
from xar_promo.subtitles import (  # noqa: E402
    AssCue,
    AssDocumentConfig,
    AssStyleConfig,
    SubtitleTrackConfig,
    render_ass_document,
)
from xar_promo.tts import ProviderIdentity, TtsCache  # noqa: E402
from xar_promo.visuals import (  # noqa: E402
    BackgroundSpec,
    Box,
    CanvasSpec,
    LayerGroup,
    Palette,
    PillowFont,
    TextElement,
    TextStyle,
    TitleCardSpec,
    render_title_card,
)


DEFAULT_PROJECT_CONFIG = (
    REPOSITORY_ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json"
)
DEFAULT_EDGE_TTS_VERSION = "7.2.8"
MEDIA_PREFLIGHT_KIND = "zhongguo-361-phase2-media-environment-preflight"
MEDIA_PREFLIGHT_SCOPE = (
    "environment-only; no CK3 capture, narration, candidate, review, or release claim"
)
MEDIA_PREFLIGHT_ARTIFACT_ID = "phase2-media-environment-preflight"
MEDIA_PREFLIGHT_VALID_FOR_SECONDS = 24 * 60 * 60
MEDIA_PREFLIGHT_MAX_FUTURE_SKEW_SECONDS = 5 * 60
DELIVERABLE_ARTIFACT_ID = "zhongguo-361-phase2-video"
DELIVERABLE_RELATIVE_PATH = Path("deliverable/zhongguo-361-phase2.mp4")
WIDTH = 1920
HEIGHT = 1080
FPS = 30
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")

# ``run_zg361_phase2_seed_capture.py --preflight-only`` is the upstream
# no-launch gate for a phase-two seed.  Keep this contract local to the
# project-specific builder: the reusable package must not know anything about
# CK3 seed runners or their process boundary.
SEED_PREFLIGHT_KIND = "zg361_phase2_seed_preflight"
SEED_PREFLIGHT_MODE = "preflight-only"
SEED_PREFLIGHT_RESULT = "GREEN"
SEED_PREFLIGHT_STATUS = "preflight-ready"
SEED_PREFLIGHT_ARTIFACT_ID = "phase2-seed-preflight"
SEED_PREFLIGHT_CHECKS = (
    "config",
    "ck3_process_inventory",
    "source_archive_equivalence",
    "external_dependencies",
    "bridge",
    "static_preflight",
    "product_fixture_projection",
    "ck3_process_inventory_after",
    "clean_source_unchanged",
    "external_dependencies_unchanged",
    "runtime_projection_unchanged",
)
SEED_PREFLIGHT_ENABLED_MODS = (
    "mod/zg361_acceptance.mod",
    "mod/zga_acceptance_fixture.mod",
)
CAPTURE_TIMELINE_RELATIVE_PATHS = (
    Path("cell") / "promo" / "capture-timeline.json",
    Path("promo") / "capture-timeline.json",
    Path("capture-timeline.json"),
)
CAPTURE_REPORT_RELATIVE_PATHS = (
    Path("report.json"),
    Path("cell") / "report.json",
)


class Phase2PromoBuildError(PromoToolchainError):
    """The project-specific entry cannot honestly produce the requested state."""


class Phase2FootagePending(Phase2PromoBuildError):
    """Typed pre-composition stop for absent or unverified real footage."""

    reason_code = "footage_pending"

    def __init__(self, report: Mapping[str, object]) -> None:
        self.report = dict(report)
        errors = self.report.get("errors")
        detail = ", ".join(str(value) for value in errors) if isinstance(errors, list) else ""
        super().__init__(
            "footage_pending: strict eight-span footage intake is RED"
            + (f" ({detail})" if detail else "")
        )


@dataclass(frozen=True, slots=True)
class MediaPreflightBinding:
    """Byte-bound, short-lived proof of the actual media production host."""

    path: Path
    bytes: int
    sha256: str
    generated_at_utc: dt.datetime
    expires_at_utc: dt.datetime
    toolchain_source_root: Path
    toolchain_head: str
    tracked_files: tuple[tuple[Path, int, str], ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "bytes": self.bytes,
            "sha256": self.sha256,
            "generated_at_utc": self.generated_at_utc.isoformat(timespec="seconds"),
            "expires_at_utc": self.expires_at_utc.isoformat(timespec="seconds"),
            "toolchain_source_root": str(self.toolchain_source_root),
            "toolchain_head": self.toolchain_head,
            "result": "GREEN",
        }

    def verify_unchanged(self, *, now: dt.datetime | None = None) -> None:
        _require_unexpired_media_preflight(
            self.generated_at_utc,
            self.expires_at_utc,
            now=now,
        )
        try:
            current = (self.path.stat().st_size, sha256_file(self.path).upper())
        except OSError as exc:
            raise Phase2PromoBuildError(
                f"bound phase-two media preflight became unavailable: {self.path}"
            ) from exc
        if current != (self.bytes, self.sha256):
            raise Phase2PromoBuildError(
                f"bound phase-two media preflight changed during the attempt: {self.path}"
            )
        for path, size, digest in self.tracked_files:
            try:
                current_file = (path.stat().st_size, sha256_file(path).upper())
            except OSError as exc:
                raise Phase2PromoBuildError(
                    f"media preflight dependency became unavailable: {path}"
                ) from exc
            if current_file != (size, digest):
                raise Phase2PromoBuildError(
                    f"media preflight dependency changed during the attempt: {path}"
                )
        checkout = _current_toolchain_identity()
        if (
            checkout["source_root"] != self.toolchain_source_root
            or checkout["head"] != self.toolchain_head
            or checkout["origin_main"] != self.toolchain_head
            or checkout["clean"] is not True
        ):
            raise Phase2PromoBuildError(
                "promo-toolchain checkout changed after the bound media preflight"
            )


def _read_media_preflight(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise Phase2PromoBuildError(
            f"could not read phase-two media preflight: {path}: {exc}"
        ) from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Phase2PromoBuildError(
            f"invalid phase-two media preflight: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise Phase2PromoBuildError("phase-two media preflight root must be an object")
    return payload


def _utc_timestamp(value: object, label: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise Phase2PromoBuildError(f"phase-two media preflight {label} must be a timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise Phase2PromoBuildError(
            f"phase-two media preflight {label} is invalid"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise Phase2PromoBuildError(
            f"phase-two media preflight {label} must include a UTC offset"
        )
    return parsed.astimezone(dt.timezone.utc)


def _require_unexpired_media_preflight(
    generated: dt.datetime,
    expires: dt.datetime,
    *,
    now: dt.datetime | None = None,
) -> None:
    current = dt.datetime.now(dt.timezone.utc) if now is None else now
    if current.tzinfo is None or current.utcoffset() is None:
        raise Phase2PromoBuildError("media preflight comparison time must be timezone-aware")
    current = current.astimezone(dt.timezone.utc)
    if expires - generated != dt.timedelta(seconds=MEDIA_PREFLIGHT_VALID_FOR_SECONDS):
        raise Phase2PromoBuildError("phase-two media preflight validity window must be 24 hours")
    if generated > current + dt.timedelta(seconds=MEDIA_PREFLIGHT_MAX_FUTURE_SKEW_SECONDS):
        raise Phase2PromoBuildError("phase-two media preflight timestamp is in the future")
    if current >= expires:
        raise Phase2PromoBuildError("phase-two media preflight has expired")


def _resolve_media_program(value: str, label: str) -> Path:
    located = shutil.which(value)
    candidate = Path(located if located is not None else value).expanduser().resolve()
    if not candidate.is_file():
        raise Phase2PromoBuildError(f"could not resolve phase-two {label}: {value}")
    return candidate


def _current_toolchain_identity() -> dict[str, object]:
    if PACKAGE_SOURCE is None:
        raise Phase2PromoBuildError(
            "phase-two release media requires XAR_PROMO_SOURCE bound to the updated promo-toolchain main checkout"
        )
    source_root = PACKAGE_SOURCE.parent if PACKAGE_SOURCE.name == "src" else PACKAGE_SOURCE

    def git(*arguments: str) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", os.fspath(source_root), *arguments],
                shell=False,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise Phase2PromoBuildError(
                f"could not inspect promo-toolchain checkout: {exc}"
            ) from exc
        if result.returncode != 0:
            raise Phase2PromoBuildError(
                "could not inspect promo-toolchain checkout: "
                + (result.stderr or result.stdout).strip()
            )
        return result.stdout.strip()

    return {
        "source_root": source_root.resolve(),
        "head": git("rev-parse", "HEAD"),
        "origin_main": git("rev-parse", "origin/main"),
        "clean": not bool(git("status", "--short")),
    }


def _bound_environment_file(
    value: object,
    *,
    label: str,
    expected_path: Path,
) -> tuple[Path, int, str]:
    if not isinstance(value, Mapping):
        raise Phase2PromoBuildError(f"phase-two media preflight {label} must be a file record")
    raw_path = value.get("path")
    raw_bytes = value.get("bytes")
    raw_sha = value.get("sha256")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        raise Phase2PromoBuildError(f"phase-two media preflight {label}.path must be absolute")
    path = Path(raw_path).expanduser().resolve()
    if path != expected_path:
        raise Phase2PromoBuildError(
            f"phase-two media preflight {label} is bound to {path}, expected {expected_path}"
        )
    if isinstance(raw_bytes, bool) or not isinstance(raw_bytes, int) or raw_bytes < 0:
        raise Phase2PromoBuildError(f"phase-two media preflight {label}.bytes is invalid")
    if not isinstance(raw_sha, str) or _SHA256.fullmatch(raw_sha) is None:
        raise Phase2PromoBuildError(f"phase-two media preflight {label}.sha256 is invalid")
    digest = raw_sha.upper()
    try:
        actual = (path.stat().st_size, sha256_file(path).upper())
    except OSError as exc:
        raise Phase2PromoBuildError(
            f"phase-two media preflight {label} is unavailable: {path}"
        ) from exc
    if actual != (raw_bytes, digest):
        raise Phase2PromoBuildError(
            f"phase-two media preflight {label} no longer matches its bound bytes"
        )
    return path, raw_bytes, digest


def _validate_media_layout(value: object) -> None:
    if not isinstance(value, Mapping):
        raise Phase2PromoBuildError("phase-two media preflight subtitle_layout must be an object")
    if value.get("frame") != [WIDTH, HEIGHT]:
        raise Phase2PromoBuildError("phase-two media preflight subtitle frame must be 1920x1080")
    expected_margins = {"left": 90, "top": 64, "right": 90, "bottom": 64}
    if value.get("safe_margins") != expected_margins:
        raise Phase2PromoBuildError("phase-two media preflight subtitle safe margins drifted")
    tracks = value.get("tracks")
    if not isinstance(tracks, list) or {row.get("id") for row in tracks if isinstance(row, Mapping)} != {"zh-CN", "en"}:
        raise Phase2PromoBuildError("phase-two media preflight must contain exact zh-CN/en tracks")
    safe_left, safe_top = 90.0, 64.0
    safe_right, safe_bottom = WIDTH - 90.0, HEIGHT - 64.0
    for row in tracks:
        if not isinstance(row, Mapping):
            raise Phase2PromoBuildError("phase-two media preflight subtitle track is invalid")
        bounds = row.get("bounds")
        lines = row.get("lines")
        if not isinstance(bounds, list) or len(bounds) != 4 or not isinstance(lines, list) or not lines:
            raise Phase2PromoBuildError("phase-two media preflight subtitle track lacks bounds or lines")
        if any(isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)) for number in bounds):
            raise Phase2PromoBuildError("phase-two media preflight subtitle bounds are invalid")
        left, top, right, bottom = (float(number) for number in bounds)
        if not (safe_left <= left < right <= safe_right and safe_top <= top < bottom <= safe_bottom):
            raise Phase2PromoBuildError("phase-two media preflight subtitle track escaped the safe area")
        for line in lines:
            if not isinstance(line, Mapping) or not isinstance(line.get("text"), str) or not line["text"].strip():
                raise Phase2PromoBuildError("phase-two media preflight subtitle line is invalid")
            width, x = line.get("width"), line.get("x")
            if any(isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)) for number in (width, x)):
                raise Phase2PromoBuildError("phase-two media preflight subtitle line geometry is invalid")
            if float(width) < 0 or float(x) < left or float(x) + float(width) > right + 0.01:
                raise Phase2PromoBuildError("phase-two media preflight subtitle line escaped its track")


def load_media_preflight_binding(
    report_path: str | Path,
    expected_sha256: str,
    *,
    project_config,
    edge_tts_version: str,
    ffmpeg: str,
    ffprobe: str,
    zh_font_file: Path,
    en_font_file: Path,
    now: dt.datetime | None = None,
) -> MediaPreflightBinding:
    path = Path(report_path).expanduser().resolve()
    if not path.is_file():
        raise Phase2PromoBuildError(f"phase-two media preflight does not exist: {path}")
    if not isinstance(expected_sha256, str) or _SHA256.fullmatch(expected_sha256) is None:
        raise Phase2PromoBuildError("--expected-media-preflight-sha256 must be a SHA-256 digest")
    expected_digest = expected_sha256.upper()
    actual_digest = sha256_file(path).upper()
    if actual_digest != expected_digest:
        raise Phase2PromoBuildError("phase-two media preflight SHA-256 does not match")
    payload = _read_media_preflight(path)
    expected_scalars = {
        "schema_version": 1,
        "kind": MEDIA_PREFLIGHT_KIND,
        "result": "GREEN",
        "scope": MEDIA_PREFLIGHT_SCOPE,
        "valid_for_seconds": MEDIA_PREFLIGHT_VALID_FOR_SECONDS,
    }
    for key, expected in expected_scalars.items():
        if payload.get(key) != expected:
            raise Phase2PromoBuildError(
                f"phase-two media preflight {key} must be {expected!r}"
            )
    generated = _utc_timestamp(payload.get("generated_at_utc"), "generated_at_utc")
    expires = _utc_timestamp(payload.get("expires_at_utc"), "expires_at_utc")
    _require_unexpired_media_preflight(generated, expires, now=now)

    project = payload.get("project")
    if not isinstance(project, Mapping) or project.get("id") != project_config.project_id or project.get("chapters") != len(project_config.chapters):
        raise Phase2PromoBuildError("phase-two media preflight is bound to a different project config")
    tool = payload.get("promo_toolchain")
    checkout = _current_toolchain_identity()
    if not isinstance(tool, Mapping) or tool.get("version") != PROMO_TOOLCHAIN_VERSION:
        raise Phase2PromoBuildError("phase-two media preflight promo-toolchain version is invalid")
    if getattr(xar_promo, "__version__", None) != tool.get("version"):
        raise Phase2PromoBuildError("active promo-toolchain version differs from media preflight")
    if (
        tool.get("source_root") != str(checkout["source_root"])
        or tool.get("head") != checkout["head"]
        or tool.get("origin_main") != checkout["origin_main"]
        or checkout["head"] != checkout["origin_main"]
        or tool.get("clean") is not True
        or checkout["clean"] is not True
    ):
        raise Phase2PromoBuildError("phase-two media preflight is not bound to the active clean promo-toolchain main")

    packages = payload.get("packages")
    if not isinstance(packages, Mapping) or packages.get("edge-tts") != DEFAULT_EDGE_TTS_VERSION or packages.get("Pillow") != "12.3.0":
        raise Phase2PromoBuildError("phase-two media preflight package versions are invalid")
    if edge_tts_version != packages["edge-tts"]:
        raise Phase2PromoBuildError("builder Edge TTS version differs from media preflight")
    if importlib.metadata.version("edge-tts") != packages["edge-tts"] or importlib.metadata.version("Pillow") != packages["Pillow"]:
        raise Phase2PromoBuildError("active media package versions differ from preflight")
    voice = payload.get("voice")
    if not isinstance(voice, Mapping) or voice.get("id") != PHASE2_POLICY.voice or PHASE2_POLICY.voice not in str(voice.get("catalogue_match", "")):
        raise Phase2PromoBuildError("phase-two media preflight did not bind XiaoxiaoNeural")

    fonts = payload.get("fonts")
    if not isinstance(fonts, Mapping):
        raise Phase2PromoBuildError("phase-two media preflight fonts must be an object")
    zh = fonts.get("zh-CN")
    en = fonts.get("en")
    if not isinstance(zh, Mapping) or zh.get("family") != "Microsoft YaHei UI":
        raise Phase2PromoBuildError("phase-two media preflight Chinese font family is invalid")
    if not isinstance(en, Mapping) or en.get("family") != "Segoe UI":
        raise Phase2PromoBuildError("phase-two media preflight English font family is invalid")
    tracked = [
        _bound_environment_file(zh, label="fonts.zh-CN", expected_path=zh_font_file.expanduser().resolve()),
        _bound_environment_file(en, label="fonts.en", expected_path=en_font_file.expanduser().resolve()),
    ]
    _validate_media_layout(payload.get("subtitle_layout"))

    media = payload.get("media")
    if not isinstance(media, Mapping):
        raise Phase2PromoBuildError("phase-two media preflight media must be an object")
    expected_media = {
        "verified_filter": "ass/libass",
        "verified_video_encoder": "libx264",
        "verified_audio_encoder": "aac/48000Hz/stereo",
        "disposable_test_output_retained": False,
    }
    for key, expected in expected_media.items():
        if media.get(key) != expected:
            raise Phase2PromoBuildError(f"phase-two media preflight {key} must be {expected!r}")
    if not isinstance(media.get("ffmpeg_version"), str) or not media["ffmpeg_version"].strip():
        raise Phase2PromoBuildError("phase-two media preflight lacks FFmpeg version evidence")
    if not isinstance(media.get("ffprobe_version"), str) or not media["ffprobe_version"].strip():
        raise Phase2PromoBuildError("phase-two media preflight lacks ffprobe version evidence")
    tracked.extend(
        (
            _bound_environment_file(
                media.get("ffmpeg"),
                label="media.ffmpeg",
                expected_path=_resolve_media_program(ffmpeg, "ffmpeg"),
            ),
            _bound_environment_file(
                media.get("ffprobe"),
                label="media.ffprobe",
                expected_path=_resolve_media_program(ffprobe, "ffprobe"),
            ),
        )
    )
    return MediaPreflightBinding(
        path=path,
        bytes=path.stat().st_size,
        sha256=actual_digest,
        generated_at_utc=generated,
        expires_at_utc=expires,
        toolchain_source_root=checkout["source_root"],
        toolchain_head=str(checkout["head"]),
        tracked_files=tuple(tracked),
    )


@dataclass(frozen=True, slots=True)
class SeedPreflightBinding:
    """Immutable identity of an upstream no-launch seed preflight report.

    The report is deliberately retained as an input artifact rather than
    treated as a live claim.  ``verify_unchanged`` is called after composition
    so a producer cannot replace the gate while a long render is running.
    """

    path: Path
    bytes: int
    sha256: str
    frozen_git_commit: str
    artifact_root: Path
    capture_root: Path
    seed_identity: tuple[tuple[str, str], ...] = ()
    capture_timeline_path: Path | None = None
    capture_timeline_bytes: int | None = None
    capture_timeline_sha256: str | None = None
    capture_report_path: Path | None = None
    capture_report_bytes: int | None = None
    capture_report_sha256: str | None = None
    capture_identity: tuple[tuple[str, str], ...] = ()
    capture_identity_blocker: str | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "bytes": self.bytes,
            "sha256": self.sha256,
            "frozen_git_commit": self.frozen_git_commit,
            "artifact_root": str(self.artifact_root),
            "capture_root": str(self.capture_root),
            "capture_timeline_path": (
                None
                if self.capture_timeline_path is None
                else str(self.capture_timeline_path)
            ),
            "capture_timeline_bytes": self.capture_timeline_bytes,
            "capture_timeline_sha256": self.capture_timeline_sha256,
            "capture_report_path": (
                None
                if self.capture_report_path is None
                else str(self.capture_report_path)
            ),
            "capture_report_bytes": self.capture_report_bytes,
            "capture_report_sha256": self.capture_report_sha256,
            "result": SEED_PREFLIGHT_RESULT,
            "mode": SEED_PREFLIGHT_MODE,
            "seed_identity": (
                None if not self.seed_identity else dict(self.seed_identity)
            ),
            "capture_identity_status": (
                "bound"
                if self.capture_identity_blocker is None and self.capture_identity
                else "unbound"
            ),
            "capture_identity": (
                None if not self.capture_identity else dict(self.capture_identity)
            ),
            "capture_identity_blocker": self.capture_identity_blocker,
        }

    @property
    def release_blockers(self) -> tuple[str, ...]:
        if self.capture_identity_blocker is None:
            return ()
        return (self.capture_identity_blocker,)

    def _bind_capture_source(
        self,
        identity: Mapping[str, str],
        *,
        source_kind: str,
    ) -> "SeedPreflightBinding":
        """Merge one capture provenance source and compare it to the seed."""

        merged = dict(self.capture_identity)
        for key, value in identity.items():
            prior = merged.get(key)
            if prior is not None and prior != value:
                raise Phase2PromoBuildError(
                    "phase-two capture source identity disagrees between "
                    f"capture sources for {key}: {value} != {prior}"
                )
            merged[key] = value

        expected = dict(self.seed_identity)
        comparable = set(expected).intersection(merged)
        for key in sorted(comparable):
            if expected[key] != merged[key]:
                raise Phase2PromoBuildError(
                    "phase-two capture source identity does not match the bound "
                    f"seed preflight for {key}: {merged[key]} != {expected[key]}"
                )
        blocker = None
        if not comparable:
            blocker = (
                "capture_identity_unbound: capture "
                f"{source_kind} does not expose a source_git_commit or "
                "clean-source/tree hash shared with the seed preflight"
            )
        return replace(
            self,
            capture_identity=tuple(sorted(merged.items())),
            capture_identity_blocker=blocker,
        )

    def bind_capture_timeline(self, timeline_path: str | Path) -> "SeedPreflightBinding":
        """Bind the preflight to a later capture timeline by shared source identity.

        A seed preflight and its eventual desktop capture intentionally live in
        separate attempt directories.  The timeline is therefore bound by the
        producer's frozen source commit/tree hashes, never by a directory
        ancestry assumption.  Missing identity remains a typed candidate
        blocker so an old capture can be retained without being called live.
        """

        timeline = Path(timeline_path).expanduser().resolve()
        if not timeline.is_file():
            return replace(
                self,
                capture_timeline_path=timeline,
                capture_timeline_bytes=None,
                capture_timeline_sha256=None,
                capture_identity=(),
                capture_identity_blocker=(
                    "capture_identity_unbound: capture timeline is missing; "
                    f"expected {timeline}"
                ),
            )
        payload = _read_capture_timeline(timeline)
        capture_identity = _capture_identity(payload)
        try:
            timeline_bytes = timeline.stat().st_size
            timeline_sha256 = sha256_file(timeline)
        except OSError as exc:
            raise Phase2PromoBuildError(
                f"could not stat phase-two capture timeline: {timeline}: {exc}"
            ) from exc

        binding = self._bind_capture_source(
            capture_identity,
            source_kind="timeline",
        )
        return replace(
            binding,
            capture_timeline_path=timeline,
            capture_timeline_bytes=timeline_bytes,
            capture_timeline_sha256=timeline_sha256,
        )

    def bind_capture_report(self, report_path: str | Path) -> "SeedPreflightBinding":
        """Bind identity from the acceptance report when the timeline is sparse.

        The full capture runner keeps runtime projection hashes in its
        ``report.json`` (usually under ``cell``), while its timeline predates
        that identity extension.  The report is read and hash-bound as a
        second provenance source; it is never treated as gameplay evidence by
        this method.
        """

        report = Path(report_path).expanduser().resolve()
        if not report.is_file():
            missing_report_blocker = (
                "capture_identity_unbound: capture report is missing; "
                f"expected {report}"
            )
            blocker = self.capture_identity_blocker
            if blocker is None:
                blocker = missing_report_blocker
            elif missing_report_blocker not in blocker:
                # Keep an earlier timeline blocker for diagnosis, but never
                # let a matching timeline identity imply a bound capture when
                # the report required by the CK3 adapter is absent.
                blocker = f"{blocker}; {missing_report_blocker}"
            return replace(
                self,
                capture_report_path=report,
                capture_report_bytes=None,
                capture_report_sha256=None,
                capture_identity_blocker=blocker,
            )
        payload = _read_capture_report(report)
        capture_identity = _capture_identity(payload)
        try:
            report_bytes = report.stat().st_size
            report_sha256 = sha256_file(report)
        except OSError as exc:
            raise Phase2PromoBuildError(
                f"could not stat phase-two capture report: {report}: {exc}"
            ) from exc
        binding = self._bind_capture_source(
            capture_identity,
            source_kind="report",
        )
        return replace(
            binding,
            capture_report_path=report,
            capture_report_bytes=report_bytes,
            capture_report_sha256=report_sha256,
        )

    def verify_unchanged(self) -> None:
        try:
            current_bytes = self.path.stat().st_size
            current_sha = sha256_file(self.path)
        except OSError as exc:
            raise Phase2PromoBuildError(
                f"bound phase-two seed preflight report became unavailable: {self.path}"
            ) from exc
        if (current_bytes, current_sha) != (self.bytes, self.sha256):
            raise Phase2PromoBuildError(
                "bound phase-two seed preflight report changed during the attempt: "
                f"{self.path}"
            )
        if self.capture_timeline_path is not None:
            try:
                timeline_bytes = self.capture_timeline_path.stat().st_size
                timeline_sha = sha256_file(self.capture_timeline_path)
            except OSError as exc:
                raise Phase2PromoBuildError(
                    "bound phase-two capture timeline became unavailable: "
                    f"{self.capture_timeline_path}"
                ) from exc
            if (timeline_bytes, timeline_sha) != (
                self.capture_timeline_bytes,
                self.capture_timeline_sha256,
            ):
                raise Phase2PromoBuildError(
                    "bound phase-two capture timeline changed during the attempt: "
                    f"{self.capture_timeline_path}"
                )
        if (
            self.capture_report_path is not None
            and self.capture_report_bytes is not None
            and self.capture_report_sha256 is not None
        ):
            try:
                report_bytes = self.capture_report_path.stat().st_size
                report_sha = sha256_file(self.capture_report_path)
            except OSError as exc:
                raise Phase2PromoBuildError(
                    "bound phase-two capture report became unavailable: "
                    f"{self.capture_report_path}"
                ) from exc
            if (report_bytes, report_sha) != (
                self.capture_report_bytes,
                self.capture_report_sha256,
            ):
                raise Phase2PromoBuildError(
                    "bound phase-two capture report changed during the attempt: "
                    f"{self.capture_report_path}"
                )


def _read_seed_preflight_report(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise Phase2PromoBuildError(
            f"could not read phase-two seed preflight report: {path}: {exc}"
        ) from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Phase2PromoBuildError(
            f"invalid phase-two seed preflight report: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise Phase2PromoBuildError("phase-two seed preflight report root must be an object")
    return payload


def _read_capture_timeline(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise Phase2PromoBuildError(
            f"could not read phase-two capture timeline: {path}: {exc}"
        ) from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Phase2PromoBuildError(
            f"invalid phase-two capture timeline: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise Phase2PromoBuildError(
            f"phase-two capture timeline root must be an object: {path}"
        )
    return payload


def _read_capture_report(path: Path) -> dict[str, object]:
    payload = _read_capture_timeline(path)
    if payload.get("schema_version") != 1 or payload.get("result") != "GREEN":
        raise Phase2PromoBuildError(
            f"phase-two capture report schema_version/result must be 1/GREEN: {path}"
        )
    cell = payload.get("cell")
    if isinstance(cell, Mapping) and (
        cell.get("schema_version") != 1 or cell.get("result") != "GREEN"
    ):
        raise Phase2PromoBuildError(
            f"phase-two capture report cell must be schema-v1 GREEN: {path}"
        )
    return payload


def _identity_value(
    value: Any,
    *,
    key: str,
    context: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise Phase2PromoBuildError(
            f"phase-two capture {context}.{key} must be a hexadecimal string"
        )
    normalized = value.strip()
    pattern = _GIT_SHA if key == "source_git_commit" else _SHA256
    if pattern.fullmatch(normalized) is None:
        raise Phase2PromoBuildError(
            f"phase-two capture {context}.{key} has a non-canonical hexadecimal value"
        )
    return normalized.lower() if key == "source_git_commit" else normalized.upper()


def _capture_identity(payload: Mapping[str, Any]) -> dict[str, str]:
    """Project optional source identity fields from capture evidence.

    The recorder may expose identity directly, under the same nested
    ``source_identity`` shape emitted by the seed preflight, or in the
    acceptance report's runtime projection fields.  Only these explicitly
    named fields are considered; unrelated report metadata cannot accidentally
    satisfy the binding.
    """

    projected: dict[str, str] = {}

    def add(key: str, value: Any, context: str) -> None:
        normalized = _identity_value(value, key=key, context=context)
        if normalized is None:
            return
        prior = projected.get(key)
        if prior is not None and prior != normalized:
            raise Phase2PromoBuildError(
                f"phase-two capture source identity repeats {key} with conflicting values"
            )
        projected[key] = normalized

    direct_aliases = {
        "source_git_commit": ("source_git_commit", "source_commit", "git_head"),
        "source_clean_tree_sha256": (
            "source_clean_tree_sha256",
            "clean_source_tree_sha256",
            "source_tree_sha256",
            "clean_source_sha256",
        ),
        "source_zip_logical_tree_sha256": (
            "source_zip_logical_tree_sha256",
            "source_zip_tree_sha256",
        ),
        "source_product_tree_sha256": ("source_product_tree_sha256",),
        "source_fixture_tree_sha256": ("source_fixture_tree_sha256",),
    }
    for canonical, aliases in direct_aliases.items():
        for alias in aliases:
            if alias in payload:
                add(canonical, payload.get(alias), "timeline")

    source_identity = payload.get("source_identity")
    if isinstance(source_identity, Mapping):
        git = source_identity.get("git")
        if isinstance(git, Mapping):
            for alias in ("declared_sha", "observed_sha", "head", "sha256"):
                if alias in git:
                    add("source_git_commit", git.get(alias), "source_identity.git")
        for alias in ("source_git_commit", "source_commit", "git_sha"):
            if alias in source_identity:
                add("source_git_commit", source_identity.get(alias), "source_identity")
        for container_key, canonical in (
            ("clean_source_tree", "source_clean_tree_sha256"),
            ("clean_source_tree_before", "source_clean_tree_sha256"),
            ("clean_source_tree_after", "source_clean_tree_sha256"),
        ):
            container = source_identity.get(container_key)
            if isinstance(container, Mapping) and "tree_sha256" in container:
                add(canonical, container.get("tree_sha256"), f"source_identity.{container_key}")
        source_zip = source_identity.get("source_zip")
        if isinstance(source_zip, Mapping):
            add(
                "source_zip_logical_tree_sha256",
                source_zip.get("logical_tree_sha256"),
                "source_identity.source_zip",
            )

    for container_key, canonical in (
        ("clean_source_tree", "source_clean_tree_sha256"),
        ("clean_source_tree_before", "source_clean_tree_sha256"),
        ("clean_source_tree_after", "source_clean_tree_sha256"),
    ):
        container = payload.get(container_key)
        if isinstance(container, Mapping) and "tree_sha256" in container:
            add(canonical, container.get("tree_sha256"), f"timeline.{container_key}")

    def project_runtime(container: Mapping[str, Any], context: str) -> None:
        runtime = container.get("runtime")
        if isinstance(runtime, Mapping):
            for key in ("source_product_tree_sha256", "source_fixture_tree_sha256"):
                if key in runtime:
                    add(key, runtime.get(key), f"{context}.runtime")
        for field in ("runtime_tree_before_sha256", "runtime_tree_after_sha256"):
            runtime_trees = container.get(field)
            if isinstance(runtime_trees, Mapping):
                for name, canonical in (
                    ("product", "source_product_tree_sha256"),
                    ("fixture", "source_fixture_tree_sha256"),
                ):
                    if name in runtime_trees:
                        add(canonical, runtime_trees.get(name), f"{context}.{field}")
        product_manifest = container.get("product_runtime_manifest")
        if isinstance(product_manifest, Mapping) and "tree_sha256" in product_manifest:
            add(
                "source_product_tree_sha256",
                product_manifest.get("tree_sha256"),
                f"{context}.product_runtime_manifest",
            )

    project_runtime(payload, "capture")
    cell = payload.get("cell")
    if isinstance(cell, Mapping):
        project_runtime(cell, "capture.cell")
        # A root acceptance report can carry the source identity in its cell's
        # nested report while the timeline remains deliberately compact.
        nested_identity = _capture_identity(cell)
        for key, value in nested_identity.items():
            add(key, value, "capture.cell")
    return projected


def _seed_identity(payload: Mapping[str, Any], frozen_git_commit: str) -> dict[str, str]:
    """Project the source identity available in a GREEN seed preflight report."""

    identity = {"source_git_commit": frozen_git_commit}
    source_identity = payload.get("source_identity")
    if isinstance(source_identity, Mapping):
        clean_tree = source_identity.get("clean_source_tree")
        if isinstance(clean_tree, Mapping):
            value = clean_tree.get("tree_sha256")
            if value is not None:
                normalized = _identity_value(
                    value,
                    key="source_clean_tree_sha256",
                    context="source_identity.clean_source_tree",
                )
                if normalized is not None:
                    identity["source_clean_tree_sha256"] = normalized
        source_zip = source_identity.get("source_zip")
        if isinstance(source_zip, Mapping):
            value = source_zip.get("logical_tree_sha256")
            if value is not None:
                normalized = _identity_value(
                    value,
                    key="source_zip_logical_tree_sha256",
                    context="source_identity.source_zip",
                )
                if normalized is not None:
                    identity["source_zip_logical_tree_sha256"] = normalized
    bootstrap = payload.get("bootstrap")
    if isinstance(bootstrap, Mapping):
        trees = bootstrap.get("tree_sha256")
        if isinstance(trees, Mapping):
            for name, canonical in (
                ("product", "source_product_tree_sha256"),
                ("fixture", "source_fixture_tree_sha256"),
            ):
                value = trees.get(name)
                if value is not None:
                    normalized = _identity_value(value, key=canonical, context="bootstrap.tree_sha256")
                    if normalized is not None:
                        identity[canonical] = normalized
    return identity


def _capture_timeline_for_root(capture_root: Path) -> Path | None:
    for relative in CAPTURE_TIMELINE_RELATIVE_PATHS:
        candidate = (capture_root / relative).resolve()
        if candidate.is_file():
            return candidate
    return None


def _capture_report_for_root(capture_root: Path) -> Path | None:
    for relative in CAPTURE_REPORT_RELATIVE_PATHS:
        candidate = (capture_root / relative).resolve()
        if candidate.is_file():
            return candidate
    return None


def _require_green_check(value: Any, name: str) -> None:
    """Accept the runner's scalar or evidence-object GREEN check form.

    Most preflight checks are persisted as the scalar ``"GREEN"``.  The two
    process-inventory checks are persisted as
    ``{"result": "GREEN", "running": false}``; accepting that documented
    shape keeps this gate bound to the real runner rather than only to a test
    fixture.
    """

    if value == "GREEN":
        return
    if (
        name in {"ck3_process_inventory", "ck3_process_inventory_after"}
        and isinstance(value, Mapping)
        and value.get("result") == "GREEN"
    ):
        if value.get("running") is not False:
            raise Phase2PromoBuildError(
                f"phase-two seed preflight check {name} must attest running=false"
            )
        return
    raise Phase2PromoBuildError(
        f"phase-two seed preflight check {name} must be GREEN"
    )


def load_seed_preflight_binding(
    report_path: str | Path,
    capture_root: str | Path,
) -> SeedPreflightBinding:
    """Load and verify a GREEN, no-launch seed preflight report.

    This is intentionally a narrow *provenance* gate.  It does not make a
    capture live or prove any gameplay claim; the CK3 adapter still verifies
    the capture bundle independently.  A preflight attempt and its later
    capture are allowed to be sibling directories (or to live on different
    volumes); when the capture timeline exposes source identity, the shared
    commit/tree hashes provide the binding.  Legacy timelines can instead be
    supplemented by the capture root's GREEN ``report.json`` runtime hashes.
    """

    path = Path(report_path).expanduser().resolve()
    if not path.is_file():
        raise Phase2PromoBuildError(
            f"phase-two seed preflight report does not exist: {path}"
        )
    capture = Path(capture_root).expanduser().resolve()
    payload = _read_seed_preflight_report(path)

    expected_scalars = {
        "schema_version": 1,
        "kind": SEED_PREFLIGHT_KIND,
        "mode": SEED_PREFLIGHT_MODE,
        "result": SEED_PREFLIGHT_RESULT,
        "status": SEED_PREFLIGHT_STATUS,
        "ok": True,
        "readiness_scope": "frozen_inputs_and_projection_only",
        "seed_ready": False,
        "mcp_only": True,
        "desktop_interaction": False,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "ck3_launch_attempted": False,
        "launch_boundary": "not-crossed",
        "native_session_started": False,
        "driver_opened": False,
    }
    for key, expected in expected_scalars.items():
        actual = payload.get(key)
        if isinstance(expected, bool):
            matches = actual is expected
        elif isinstance(expected, int):
            matches = type(actual) is int and actual == expected
        else:
            matches = actual == expected
        if not matches:
            raise Phase2PromoBuildError(
                f"phase-two seed preflight report {key} must be {expected!r}"
            )
    if payload.get("failure_reason") is not None or payload.get("failure_evidence") is not None:
        raise Phase2PromoBuildError(
            "GREEN phase-two seed preflight report contains failure evidence"
        )
    if payload.get("traceback") is not None:
        raise Phase2PromoBuildError(
            "GREEN phase-two seed preflight report contains a traceback"
        )

    frozen_git_commit = payload.get("frozen_git_commit")
    if not isinstance(frozen_git_commit, str) or _GIT_SHA.fullmatch(frozen_git_commit) is None:
        raise Phase2PromoBuildError(
            "phase-two seed preflight report frozen_git_commit must be a 40-character git SHA"
        )
    frozen_git_commit = frozen_git_commit.lower()
    declared_identity = _capture_identity(payload).get("source_git_commit")
    if declared_identity is not None and declared_identity != frozen_git_commit:
        raise Phase2PromoBuildError(
            "phase-two seed preflight source_identity git SHA does not match frozen_git_commit"
        )

    paths = payload.get("paths")
    if not isinstance(paths, dict):
        raise Phase2PromoBuildError("phase-two seed preflight report paths must be an object")
    raw_artifacts = paths.get("artifacts")
    if not isinstance(raw_artifacts, str) or not Path(raw_artifacts).is_absolute():
        raise Phase2PromoBuildError(
            "phase-two seed preflight report paths.artifacts must be absolute"
        )
    artifact_root = Path(raw_artifacts).expanduser().resolve()
    if not artifact_root.is_dir():
        raise Phase2PromoBuildError(
            "phase-two seed preflight report paths.artifacts must be an existing directory"
        )
    try:
        path.relative_to(artifact_root)
    except ValueError as exc:
        raise Phase2PromoBuildError(
            "phase-two seed preflight report must be located below paths.artifacts"
        ) from exc
    report_path_value = payload.get("report_path")
    if not isinstance(report_path_value, str) or not Path(report_path_value).is_absolute():
        raise Phase2PromoBuildError(
            "phase-two seed preflight report report_path must be absolute"
        )
    declared_report_path = Path(report_path_value).expanduser().resolve()
    if declared_report_path != path:
        raise Phase2PromoBuildError(
            "phase-two seed preflight report report_path does not bind the supplied file"
        )
    if declared_report_path != artifact_root / "preflight.json":
        raise Phase2PromoBuildError(
            "phase-two seed preflight report must be paths.artifacts/preflight.json"
        )

    checks = payload.get("checks")
    if not isinstance(checks, dict):
        raise Phase2PromoBuildError("phase-two seed preflight report checks must be an object")
    for name in SEED_PREFLIGHT_CHECKS:
        _require_green_check(checks.get(name), name)

    bootstrap = payload.get("bootstrap")
    if not isinstance(bootstrap, dict):
        raise Phase2PromoBuildError("phase-two seed preflight report bootstrap is missing")
    if bootstrap.get("projection_only") is not True or bootstrap.get("mounted") is not False:
        raise Phase2PromoBuildError(
            "phase-two seed preflight report bootstrap must attest projection_only=true and mounted=false"
        )
    enabled_mods = bootstrap.get("enabled_mods")
    if not isinstance(enabled_mods, list) or tuple(enabled_mods) != SEED_PREFLIGHT_ENABLED_MODS:
        raise Phase2PromoBuildError(
            "phase-two seed preflight report must bind exactly product+fixture projections"
        )

    try:
        size = path.stat().st_size
        digest = sha256_file(path)
    except OSError as exc:
        raise Phase2PromoBuildError(
            f"could not stat phase-two seed preflight report: {path}: {exc}"
        ) from exc
    binding = SeedPreflightBinding(
        path=path,
        bytes=size,
        sha256=digest,
        frozen_git_commit=frozen_git_commit,
        artifact_root=artifact_root,
        capture_root=capture,
        seed_identity=tuple(
            sorted(_seed_identity(payload, frozen_git_commit).items())
        ),
    )
    timeline = _capture_timeline_for_root(capture)
    capture_report = _capture_report_for_root(capture)
    if timeline is None:
        binding = replace(
            binding,
            capture_identity_blocker=(
                "capture_identity_unbound: capture timeline was not found under "
                f"{capture}"
            ),
        )
    else:
        binding = binding.bind_capture_timeline(timeline)
    if capture_report is not None:
        binding = binding.bind_capture_report(capture_report)
        if timeline is None:
            # A report can provide useful source identity, but the adapter
            # still requires its canonical timeline before a candidate can be
            # considered capture-ready.
            binding = replace(
                binding,
                capture_identity_blocker=(
                    "capture_identity_unbound: capture timeline was not found under "
                    f"{capture}"
                ),
            )
    else:
        binding = binding.bind_capture_report(
            capture / CAPTURE_REPORT_RELATIVE_PATHS[0]
        )
    return binding


@dataclass(frozen=True, slots=True)
class Phase2BuildOutcome:
    result: PipelineResult
    candidate: Phase2CaptureCandidate
    release_ready: bool
    blockers: tuple[str, ...]
    run_manifest_path: Path | None
    seed_preflight: SeedPreflightBinding | None = None
    media_preflight: MediaPreflightBinding | None = None
    footage_intake: Mapping[str, object] | None = None
    dependency_graph: Mapping[str, Sequence[str]] | None = None


def _portable_id(value: str, *, prefix: str = "") -> str:
    candidate = f"{prefix}{value}"
    if _IDENTIFIER.fullmatch(candidate) is not None:
        return candidate
    digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:16]
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", candidate).strip("._-")[:100]
    result = f"{stem or 'item'}-{digest}"
    if _IDENTIFIER.fullmatch(result) is None:
        raise Phase2PromoBuildError(f"could not derive a portable id from {value!r}")
    return result


def _segment_id(chapter_id: str, cue_id: str) -> str:
    raw = f"{chapter_id}.{cue_id}"
    if len(raw) <= 96 and _IDENTIFIER.fullmatch(raw) is not None:
        return raw
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", raw).strip("._-")[:72]
    result = f"{stem or 'segment'}-{digest}"
    if len(result) > 96 or _IDENTIFIER.fullmatch(result) is None:
        raise Phase2PromoBuildError(
            f"could not derive a bounded segment id from {chapter_id!r}/{cue_id!r}"
        )
    return result


def _narration_artifact_id(chapter_id: str, cue_id: str) -> str:
    # This is exactly the generic pipeline's narration artifact id for the
    # segment, so a candidate run can preserve every config-declared input.
    return f"narration.{_segment_id(chapter_id, cue_id)}"


def _phase2_preset_factory(config):
    return validate_phase2_project_config(config)


def _phase2_ck3_adapter_factory(config, artifact_root: Path):
    # The preset's public loader calls the reusable CK3 adapter and then applies
    # only this project's provenance/clean-UI attestations to the verified bundle.
    return load_phase2_capture_candidate(config, artifact_root)


def _registry() -> ComponentRegistry:
    return ComponentRegistry(
        adapters=((ADAPTER_ID, _phase2_ck3_adapter_factory),),
        presets=((PRESET_ID, _phase2_preset_factory),),
        discover_entry_points=False,
    )


def _require_ready_authoring(config) -> None:
    planned = [chapter.chapter_id for chapter in config.chapters if chapter.state != "ready"]
    if planned:
        raise Phase2PromoBuildError(
            "phase-two project remains planned; no footage or release claim may be made: "
            + ", ".join(planned)
        )
    empty = [chapter.chapter_id for chapter in config.chapters if not chapter.cues]
    if empty:
        raise Phase2PromoBuildError(
            "ready phase-two chapters need authored narration/subtitle cues: "
            + ", ".join(empty)
        )
    cue_ids = [cue.cue_id for chapter in config.chapters for cue in chapter.cues]
    if len(cue_ids) != len(set(cue_ids)):
        raise Phase2PromoBuildError(
            "phase-two cue ids must be globally unique for narration/artifact binding"
        )


def _draft_duration(_project, _chapter, cue) -> Decimal:
    # Authoring-only estimate.  A full build replaces this with ffprobe-observed
    # cache audio through Storyboard's narration-duration resolver.
    text = cue.narration[PHASE2_POLICY.narration_locale]
    visible = sum(not character.isspace() for character in text)
    return Decimal(str(max(2.5, 0.8 + visible / 4.2)))


class _VisualProbe:
    def __init__(self, ffprobe: str, workdir: Path, command_runner: Callable[..., CommandResult]):
        self.ffprobe = ffprobe
        self.workdir = workdir
        self.command_runner = command_runner
        self.sequence = 0

    def __call__(self, path: Path) -> VisualProbeResult:
        self.sequence += 1
        inspected = require_streams(
            probe_media(
                self.ffprobe,
                path,
                audit_directory=self.workdir
                / "audit"
                / "visual-probe"
                / f"probe-{self.sequence:04d}",
                command_runner=self.command_runner,
            ),
            video=True,
        )
        stream = inspected.video_streams[0]
        if stream.width is None or stream.height is None:
            raise Phase2PromoBuildError(f"visual probe lacks dimensions: {path}")
        media_type = mimetypes.guess_type(path.name)[0]
        if media_type is None or not media_type.startswith(("image/", "video/")):
            media_type = "image/png" if stream.codec_name == "png" else "video/mp4"
        return VisualProbeResult(media_type, stream.width, stream.height)


class _GeneratedCardResolver:
    def __init__(self, zh_font_file: Path, en_font_file: Path):
        self.zh_font_file = zh_font_file
        self.en_font_file = en_font_file

    @staticmethod
    def _font(path: Path, *, key: str, family: str, size: int, weight: int) -> PillowFont:
        if not path.is_file():
            raise Phase2PromoBuildError(f"required generated-card font is missing: {path}")
        try:
            from PIL import ImageFont
        except ImportError as exc:
            raise Phase2PromoBuildError(
                "Pillow is required for generated phase-two cards"
            ) from exc
        try:
            handle = ImageFont.truetype(str(path), size=size)
        except OSError as exc:
            raise Phase2PromoBuildError(f"could not load generated-card font {path}: {exc}") from exc
        return PillowFont(FontSpec(key, family, size, weight), handle)

    def __call__(self, source: VisualSource, *, workdir: Path) -> Path:
        if source.kind != GENERATED_CARD or not source.requires_resolution:
            raise Phase2PromoBuildError(
                f"generated-card resolver rejected source {source.source_id!r}"
            )
        output = (workdir / source.path).resolve() if not source.path.is_absolute() else source.path.resolve()
        if output.exists():
            raise Phase2PromoBuildError(f"refusing to overwrite generated card: {output}")
        metadata = source.metadata
        zh_title = metadata.get("zh_title")
        en_title = metadata.get("en_title")
        if not isinstance(zh_title, str) or not zh_title.strip():
            raise Phase2PromoBuildError("generated card lacks zh_title metadata")
        if not isinstance(en_title, str) or not en_title.strip():
            raise Phase2PromoBuildError("generated card lacks en_title metadata")

        fonts = {
            "zh-title": self._font(
                self.zh_font_file,
                key="zh-title",
                family="Microsoft YaHei UI",
                size=72,
                weight=700,
            ),
            "en-title": self._font(
                self.en_font_file,
                key="en-title",
                family="Segoe UI",
                size=40,
                weight=600,
            ),
            "label": self._font(
                self.zh_font_file,
                key="label",
                family="Microsoft YaHei UI",
                size=28,
                weight=600,
            ),
        }
        palette = Palette(
            {
                "background-top": (16, 20, 31, 255),
                "background-bottom": (41, 19, 25, 255),
                "primary": (248, 238, 215, 255),
                "secondary": (204, 214, 230, 255),
                "accent": (244, 178, 76, 255),
            }
        )
        canvas = CanvasSpec(
            WIDTH,
            HEIGHT,
            SafeArea.from_margins(
                frame_width=WIDTH,
                frame_height=HEIGHT,
                left=96,
                top=80,
                right=96,
                bottom=80,
            ),
            palette,
            BackgroundSpec("gradient", "background-top", "background-bottom"),
        )
        punctuation = WrapPolicy(
            force_break_after=frozenset({"。", "！", "？"}),
            prefer_break_after=frozenset({"，", "；", ":", ",", ";"}),
            decimal_separators=frozenset({".", "。"}),
        )
        spec = TitleCardSpec(
            canvas=canvas,
            layers=LayerGroup(
                texts=(
                    TextElement(
                        "二期新增 · PHASE 2 INCREMENTS",
                        Box(120, 100, 1800, 170),
                        TextStyle("label", "accent", 42, 1, alignment="center"),
                    ),
                    TextElement(
                        zh_title,
                        Box(150, 270, 1770, 540),
                        TextStyle(
                            "zh-title",
                            "primary",
                            92,
                            3,
                            alignment="center",
                            vertical_alignment="center",
                            wrap_policy=punctuation,
                        ),
                    ),
                    TextElement(
                        en_title,
                        Box(190, 590, 1730, 800),
                        TextStyle(
                            "en-title",
                            "secondary",
                            54,
                            3,
                            alignment="center",
                            vertical_alignment="center",
                        ),
                    ),
                    TextElement(
                        "默认观众已看过一期 · ONLY NEW PHASE-TWO SYSTEMS",
                        Box(180, 890, 1740, 950),
                        TextStyle("label", "accent", 42, 1, alignment="center"),
                    ),
                )
            ),
        )
        payload = render_title_card(spec, fonts=fonts, assets={})
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise Phase2PromoBuildError(f"refusing to overwrite generated card: {output}") from exc
        return output


class _SubtitleRenderer:
    ZH_FONT = "Microsoft YaHei UI"
    EN_FONT = "Segoe UI"

    def __call__(self, segment: SegmentDraft, _narration, *, workdir: Path) -> str:
        del workdir
        if set(segment.subtitles) != set(PHASE2_POLICY.subtitle_locales):
            raise Phase2PromoBuildError(
                f"segment {segment.segment_id!r} lacks exact zh-CN/en subtitles"
            )
        duration = segment.render_options.duration_seconds
        tracks = (
            SubtitleTrackConfig(
                "zh-CN",
                "zh-CN",
                1,
                AssStyleConfig(
                    "ChinesePrimary",
                    self.ZH_FONT,
                    46,
                    outline=3,
                    shadow=1,
                    alignment=2,
                    margin_left=90,
                    margin_right=90,
                    margin_vertical=142,
                ),
            ),
            SubtitleTrackConfig(
                "en",
                "en",
                0,
                AssStyleConfig(
                    "EnglishSecondary",
                    self.EN_FONT,
                    30,
                    outline=2,
                    shadow=1,
                    alignment=2,
                    margin_left=110,
                    margin_right=110,
                    margin_vertical=64,
                ),
            ),
        )
        cues = tuple(
            AssCue(
                f"{locale}-line",
                locale,
                0,
                duration,
                segment.subtitles[locale],
            )
            for locale in PHASE2_POLICY.subtitle_locales
        )
        return render_ass_document(
            AssDocumentConfig(
                f"ZhongGuo phase two {segment.segment_id}",
                WIDTH,
                HEIGHT,
                duration_seconds=duration,
            ),
            tracks,
            cues,
            available_font_names={self.ZH_FONT, self.EN_FONT},
        )


def _validation_narration_resolver(segment: SegmentDraft, *, workdir: Path):
    del segment, workdir
    raise Phase2PromoBuildError("validation-only narration resolver must never execute")


class Phase2ProjectComposer:
    """Project-owned implementation of the frozen ``PipelineComposer`` seam."""

    def __init__(
        self,
        *,
        capture_root: Path,
        tts_cache_root: Path | None,
        edge_tts_version: str,
        ffmpeg: str,
        ffprobe: str,
        zh_font_file: Path,
        en_font_file: Path,
        command_runner: Callable[..., CommandResult] = run_command,
    ) -> None:
        self.capture_root = capture_root.expanduser().resolve()
        self.tts_cache_root = (
            None if tts_cache_root is None else tts_cache_root.expanduser().resolve()
        )
        self.edge_tts_version = edge_tts_version
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe
        self.zh_font_file = zh_font_file.expanduser().resolve()
        self.en_font_file = en_font_file.expanduser().resolve()
        self.command_runner = command_runner
        self.capture_candidate: Phase2CaptureCandidate | None = None
        self.real_narration_durations = False
        self.composed_config = None
        self.final_duration_seconds: float | None = None

    def _cached_narration(self, config, workdir: Path):
        if self.tts_cache_root is None:
            raise Phase2PromoBuildError(
                "full build requires --tts-cache with pre-generated Xiaoxiao narration"
            )
        identity = ProviderIdentity("edge-tts", self.edge_tts_version)
        cache = TtsCache(self.tts_cache_root)
        entries = {}
        durations = {}
        for chapter in config.chapters:
            for cue in chapter.cues:
                artifact_id = _narration_artifact_id(
                    chapter.chapter_id,
                    cue.cue_id,
                )
                if artifact_id not in chapter.artifact_ids:
                    raise Phase2PromoBuildError(
                        f"chapter {chapter.chapter_id!r} must declare cached narration "
                        f"artifact id {artifact_id!r}"
                    )
                request = build_narration_request(
                    cue.narration[PHASE2_POLICY.narration_locale]
                )
                try:
                    entry = cache.validate_cached(request, identity)
                except Exception as exc:
                    raise Phase2PromoBuildError(
                        f"missing or invalid offline narration cache for cue {cue.cue_id!r}: {exc}"
                    ) from exc
                segment_id = _segment_id(chapter.chapter_id, cue.cue_id)
                inspected = require_streams(
                    probe_media(
                        self.ffprobe,
                        entry.media_path,
                        audit_directory=workdir
                        / "audit"
                        / "narration-probe"
                        / segment_id,
                        command_runner=self.command_runner,
                    ),
                    audio=True,
                )
                duration = inspected.require_duration()
                key = (chapter.chapter_id, cue.cue_id)
                entries[key] = entry
                durations[key] = (duration, artifact_id)
        return entries, durations

    def __call__(
        self,
        config,
        run,
        *,
        config_path: Path,
        run_path: Path | None,
        workdir: Path,
        adapter_factory,
        preset_factory,
        validate_only: bool,
    ) -> PipelineInvocation:
        del run, config_path, run_path
        config = preset_factory(config)
        self.composed_config = config
        candidate = adapter_factory(config, self.capture_root)
        if not isinstance(candidate, Phase2CaptureCandidate):
            raise Phase2PromoBuildError(
                "phase-two CK3 adapter must return Phase2CaptureCandidate"
            )
        self.capture_candidate = candidate

        entries: Mapping[tuple[str, str], object] = {}
        durations: Mapping[tuple[str, str], tuple[float, str]] = {}
        if not validate_only:
            entries, durations = self._cached_narration(config, workdir)

        def duration_resolver(_project, chapter, cue):
            value = durations.get((chapter.chapter_id, cue.cue_id))
            if value is None:
                return None
            seconds, artifact_id = value
            return ResolvedNarrationDuration(seconds, artifact_id)

        timeline = plan_storyboard(
            config,
            narration_duration_resolver=duration_resolver,
            draft_estimator=_draft_duration,
            spacing=TimelineSpacing(cue_gap_seconds=0, chapter_gap_seconds=0),
            available_artifact_ids=(
                artifact_id
                for chapter in config.chapters
                for artifact_id in chapter.artifact_ids
            ),
            validate_only=validate_only,
        )
        timing_by_cue = {
            (row.chapter_id, row.cue_id): row for row in timeline.cues
        }
        chapter_timing = {row.chapter_id: row for row in timeline.chapters}
        self.real_narration_durations = bool(timeline.cues) and all(
            row.duration_source == "resolved-narration" for row in timeline.cues
        )

        segments: list[SegmentDraft] = []
        for chapter in config.chapters:
            span = (
                candidate.bundle.clean_span(chapter.chapter_id)
                if chapter.kind == CAPTURE_CHAPTER_KIND
                else None
            )
            chapter_row = chapter_timing[chapter.chapter_id]
            if span is not None and float(chapter_row.duration_seconds) > span.duration_seconds:
                raise Phase2PromoBuildError(
                    f"chapter {chapter.chapter_id!r} narration needs "
                    f"{float(chapter_row.duration_seconds):.3f}s but clean span has "
                    f"{span.duration_seconds:.3f}s"
                )
            for cue in chapter.cues:
                key = (chapter.chapter_id, cue.cue_id)
                timing = timing_by_cue[key]
                segment_id = _segment_id(chapter.chapter_id, cue.cue_id)
                if chapter.kind == CAPTURE_CHAPTER_KIND:
                    if span is None:
                        raise Phase2PromoBuildError(
                            f"capture chapter {chapter.chapter_id!r} lacks its clean span"
                        )
                    relative_start = float(timing.start_seconds - chapter_row.start_seconds)
                    visual = VisualSource(
                        _portable_id(segment_id, prefix="capture."),
                        VIDEO,
                        candidate.bundle.raw_capture.path,
                        "ck3-capture-bundle",
                        metadata={
                            "clean_span_id": span.span_id,
                            "begin_mark": span.begin_mark,
                            "end_mark": span.end_mark,
                            "capture_sha256": candidate.bundle.raw_capture.sha256,
                        },
                    )
                    start_seconds = span.begin_seconds + relative_start
                elif chapter.kind == GENERATED_CHAPTER_KIND:
                    visual = VisualSource(
                        _portable_id(segment_id, prefix="card."),
                        GENERATED_CARD,
                        Path("visuals") / f"{segment_id}.png",
                        "zhongguo-phase2-card",
                        requires_resolution=True,
                        metadata={
                            "chapter_id": chapter.chapter_id,
                            "zh_title": chapter.title["zh-CN"],
                            "en_title": chapter.title["en"],
                        },
                    )
                    start_seconds = 0.0
                else:  # Defensive even though the preset already rejects this.
                    raise Phase2PromoBuildError(
                        f"unsupported phase-two chapter type: {chapter.kind}"
                    )
                entry = entries.get(key)
                segments.append(
                    SegmentDraft(
                        segment_id=segment_id,
                        visual_source=visual,
                        render_options=RenderOptions(
                            width=WIDTH,
                            height=HEIGHT,
                            fps=FPS,
                            duration_seconds=float(timing.duration_seconds),
                            crf=18,
                            preset="medium",
                        ),
                        subtitles=cue.subtitles,
                        narration_request=build_narration_request(
                            cue.narration[PHASE2_POLICY.narration_locale]
                        ),
                        prepared_narration=(
                            None if entry is None else entry.media_path  # type: ignore[attr-defined]
                        ),
                        start_seconds=start_seconds,
                    )
                )

        dependencies = PipelineDependencies(
            ffmpeg=self.ffmpeg,
            subtitle_renderer=_SubtitleRenderer(),
            command_runner=self.command_runner,
            visual_probe=_VisualProbe(self.ffprobe, workdir, self.command_runner),
            visual_resolver=_GeneratedCardResolver(
                self.zh_font_file,
                self.en_font_file,
            ),
            narration_resolver=(
                _validation_narration_resolver if validate_only else None
            ),
        )
        return PipelineInvocation(
            PipelineDraft(
                config=config,
                segments=tuple(segments),
                deliverable_relative_path=DELIVERABLE_RELATIVE_PATH,
                deliverable_artifact_id=DELIVERABLE_ARTIFACT_ID,
                deliverable_media_type="video/mp4",
            ),
            dependencies,
            workdir,
        )

    def verify_final_deliverable(self, result: PipelineResult) -> float:
        """Probe exact rendered bytes and apply the preset's strict duration gate."""

        if self.composed_config is None:
            raise Phase2PromoBuildError("phase-two composer has no bound project config")
        if result.audit_record is None:
            raise Phase2PromoBuildError("successful pipeline lacks an exact deliverable")
        deliverable = result.audit_record.deliverable
        inspected = require_streams(
            probe_media(
                self.ffprobe,
                deliverable.path,
                audit_directory=result.workdir / "audit" / "final-deliverable-probe",
                command_runner=self.command_runner,
            ),
            video=True,
            audio=True,
        )
        observed_duration = inspected.require_duration()
        self.final_duration_seconds = float(observed_duration)
        return validate_rendered_duration(
            observed_duration,
            self.composed_config,
        )


def _result_mapping(
    result: PipelineResult,
    *,
    final_duration_seconds: float | None = None,
    seed_preflight: SeedPreflightBinding | None = None,
    media_preflight: MediaPreflightBinding | None = None,
    footage_intake: Mapping[str, object] | None = None,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "kind": "zhongguo-361-phase2-pipeline-attempt",
        "status": result.status,
        "validate_only": result.validate_only,
        "signoff_recorded": result.signoff_recorded,
        "workdir": str(result.workdir),
        "phases": [phase.to_mapping() for phase in result.phases],
        "artifacts": [artifact.to_audit_mapping() for artifact in result.artifacts],
        "audit_record": (
            None if result.audit_record is None else result.audit_record.to_mapping()
        ),
        "seed_preflight": (
            None if seed_preflight is None else seed_preflight.to_mapping()
        ),
        "media_preflight": (
            None if media_preflight is None else media_preflight.to_mapping()
        ),
        "footage_intake": (
            None if footage_intake is None else dict(footage_intake)
        ),
        "dependency_graph": final_promo_execution_dag(),
    }
    if result.failure is not None:
        value["failure"] = {
            "phase": result.failure.phase,
            "exception_type": result.failure.exception_type,
            "message": result.failure.message,
            "stdout_paths": [str(path) for path in result.failure.stdout_paths],
            "stderr_paths": [str(path) for path in result.failure.stderr_paths],
            "partial_paths": [str(path) for path in result.failure.partial_paths],
            "retained_paths": [str(path) for path in result.failure.retained_paths],
        }
    if final_duration_seconds is not None:
        value["final_duration_gate"] = {
            "source": "exact-deliverable-ffprobe",
            "observed_seconds": final_duration_seconds,
            "exclusive_limit_seconds": PHASE2_POLICY.duration_limit_seconds_exclusive,
            "status": (
                "GREEN"
                if 0 < final_duration_seconds
                < PHASE2_POLICY.duration_limit_seconds_exclusive
                else "RED"
            ),
        }
    return value


def _write_new_json(path: Path, value: Mapping[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise Phase2PromoBuildError(f"refusing to overwrite process material: {path}") from exc
    return path


def _write_entry_failure(
    workdir: Path,
    phase: str,
    error: Exception,
    *,
    retained_paths: Sequence[Path] = (),
) -> Path:
    """Write the immutable entry failure receipt for a retained attempt.

    A candidate run can be created incrementally.  If persistence fails after
    its manifest or some artifacts have landed, callers pass that path here so
    the receipt makes the retention boundary explicit.  The helper itself is
    intentionally exclusive: an attempt receipt is process material and must
    never be overwritten by a retry.
    """

    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": "zhongguo-361-phase2-entry-failure",
        "status": "RED",
        "phase": phase,
        "exception_type": type(error).__name__,
        "message": str(error),
        "recorded_at_utc": dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }
    if retained_paths:
        payload["retained_paths"] = [
            str(path.expanduser().resolve()) for path in retained_paths
        ]
    return _write_new_json(workdir / "phase2-entry-failure.json", payload)


def _persist_candidate_run(
    config_path: Path,
    result: PipelineResult,
    run_id: str,
    *,
    seed_preflight: SeedPreflightBinding | None = None,
    media_preflight: MediaPreflightBinding | None = None,
) -> Path:
    if result.audit_record is None:
        raise Phase2PromoBuildError("successful build lacks a byte-bound deliverable record")
    run_path = start_run(
        config_path,
        run_id=run_id,
        run_directory=result.workdir / "candidate-run",
    )
    config = load_phase2_project_config(config_path)
    required_ids = {
        artifact_id
        for chapter in config.chapters
        for artifact_id in chapter.artifact_ids
    }
    selected = {
        artifact.artifact_id: artifact
        for artifact in result.artifacts
        if artifact.artifact_id in required_ids or artifact.role == "deliverable"
    }
    missing = sorted(required_ids - set(selected))
    if missing:
        raise Phase2PromoBuildError(
            "pipeline result lacks config-declared candidate artifacts: "
            + ", ".join(missing)
        )
    deliverable = result.audit_record.deliverable
    selected[deliverable.artifact_id] = deliverable
    for artifact in selected.values():
        preserve_artifact(
            run_path,
            artifact.path,
            artifact_id=artifact.artifact_id,
            collection="derived",
            role=artifact.role,
            label=(
                "ZhongGuo 361 phase-two unreviewed promo candidate"
                if artifact.role == "deliverable"
                else artifact.path.name
            ),
            media_type=artifact.media_type,
        )
    if seed_preflight is not None:
        # Keep the exact upstream gate in the candidate run's raw collection;
        # this makes the provenance portable even after the external attempt
        # directory is archived or moved.
        preserve_artifact(
            run_path,
            seed_preflight.path,
            artifact_id=SEED_PREFLIGHT_ARTIFACT_ID,
            collection="raw",
            role="preflight",
            label="ZhongGuo 361 phase-two seed no-launch preflight",
            media_type="application/json",
        )
    if media_preflight is not None:
        preserve_artifact(
            run_path,
            media_preflight.path,
            artifact_id=MEDIA_PREFLIGHT_ARTIFACT_ID,
            collection="raw",
            role="preflight",
            label="ZhongGuo 361 phase-two media environment preflight",
            media_type="application/json",
        )
    return run_path


def _approved_deliverable(
    run_manifest_path: Path | None,
    *,
    config_path: Path,
    result: PipelineResult,
    media_preflight: MediaPreflightBinding | None = None,
) -> bool:
    if run_manifest_path is None:
        return False
    loaded = load_document(run_manifest_path, check_files=True)
    validate_profile(loaded, "release")
    if loaded.run is None:
        return False
    if media_preflight is not None:
        retained_media_preflight = next(
            (
                artifact
                for artifact in loaded.run.artifacts
                if artifact.artifact_id == MEDIA_PREFLIGHT_ARTIFACT_ID
                and artifact.collection == "raw"
                and artifact.role == "preflight"
            ),
            None,
        )
        if (
            retained_media_preflight is None
            or (retained_media_preflight.bytes, retained_media_preflight.sha256)
            != (media_preflight.bytes, media_preflight.sha256)
        ):
            return False
    if (
        loaded.run.project_config.bytes != config_path.stat().st_size
        or loaded.run.project_config.sha256 != sha256_file(config_path)
    ):
        raise Phase2PromoBuildError(
            "signed run is not bound to the exact phase-two project config bytes"
        )
    latest_by_artifact = {
        signoff.artifact_id: signoff for signoff in loaded.run.signoffs
    }
    if result.audit_record is None:
        return any(
            artifact.role == "deliverable"
            and artifact.artifact_id in latest_by_artifact
            and latest_by_artifact[artifact.artifact_id].decision == "approved"
            for artifact in loaded.run.artifacts
        )
    subject = result.audit_record.deliverable
    target = next(
        (
            artifact
            for artifact in loaded.run.artifacts
            if artifact.artifact_id == subject.artifact_id
            and artifact.role == "deliverable"
        ),
        None,
    )
    latest = latest_by_artifact.get(subject.artifact_id)
    return bool(
        target is not None
        and latest is not None
        and latest.decision == "approved"
        and (target.bytes, target.sha256) == (subject.bytes, subject.sha256)
    )


def execute(
    args: argparse.Namespace,
    *,
    registry: ComponentRegistry | None = None,
    composer_factory=None,
    pipeline_runner=None,
    footage_validator=None,
) -> Phase2BuildOutcome:
    config_path = args.project_config.expanduser().resolve()
    capture_root = args.capture_root.expanduser().resolve()
    workdir = args.work_dir.expanduser().resolve()
    seed_preflight: SeedPreflightBinding | None = None
    media_preflight: MediaPreflightBinding | None = None
    footage_intake: dict[str, object] | None = None
    if not args.validate_only and workdir.exists():
        raise Phase2PromoBuildError(
            f"full build requires a new attempt directory; retain the existing one: {workdir}"
        )

    failure_phase = "entry-preflight"
    final_duration_seconds: float | None = None
    try:
        config = load_phase2_project_config(config_path)
        media_report = getattr(args, "media_preflight_report", None)
        media_sha = getattr(args, "expected_media_preflight_sha256", None)
        if (media_report is None) != (media_sha is None):
            raise Phase2PromoBuildError(
                "--media-preflight-report and --expected-media-preflight-sha256 must be supplied together"
            )
        if media_report is not None:
            media_preflight = load_media_preflight_binding(
                media_report,
                media_sha,
                project_config=config,
                edge_tts_version=args.edge_tts_version,
                ffmpeg=args.ffmpeg,
                ffprobe=args.ffprobe,
                zh_font_file=args.zh_font_file,
                en_font_file=args.en_font_file,
            )
        validator = (
            validate_footage_intake
            if footage_validator is None
            else footage_validator
        )
        raw_footage_intake = validator(capture_root)
        if not isinstance(raw_footage_intake, Mapping):
            raise Phase2PromoBuildError(
                "phase-two footage validator must return a typed mapping"
            )
        footage_intake = {
            **dict(raw_footage_intake),
            "dependency_graph": final_promo_execution_dag(),
        }
        if footage_intake.get("result") != "GREEN":
            raise Phase2FootagePending(footage_intake)
        _require_ready_authoring(config)
        seed_preflight_path = getattr(args, "seed_preflight_report", None)
        if seed_preflight_path is not None:
            seed_preflight = load_seed_preflight_binding(
                seed_preflight_path,
                capture_root,
            )
        selected_registry = _registry() if registry is None else registry
        adapter_factory = selected_registry.resolve_adapter(config.adapter)
        preset_factory = selected_registry.resolve_preset(config.preset)
        factory = Phase2ProjectComposer if composer_factory is None else composer_factory
        composer = factory(
            capture_root=capture_root,
            tts_cache_root=args.tts_cache,
            edge_tts_version=args.edge_tts_version,
            ffmpeg=args.ffmpeg,
            ffprobe=args.ffprobe,
            zh_font_file=args.zh_font_file,
            en_font_file=args.en_font_file,
        )
        invocation = composer(
            config,
            None,
            config_path=config_path,
            run_path=None,
            workdir=workdir,
            adapter_factory=adapter_factory,
            preset_factory=preset_factory,
            validate_only=args.validate_only,
        )
        candidate = composer.capture_candidate
        if candidate is None:
            raise Phase2PromoBuildError("phase-two composer did not retain its capture candidate")
        if seed_preflight is not None:
            # The adapter is authoritative for the timeline location.  Rebind
            # through it after composition so custom test seams and future
            # capture layouts cannot accidentally rely on directory ancestry.
            timeline = getattr(getattr(candidate.bundle, "timeline", None), "path", None)
            if timeline is not None and (
                seed_preflight.capture_timeline_path is None
                or Path(timeline).expanduser().resolve()
                != seed_preflight.capture_timeline_path
            ):
                seed_preflight = seed_preflight.bind_capture_timeline(timeline)
            candidate_capture_root = getattr(candidate.bundle, "artifact_root", None)
            report_roots = [capture_root]
            if candidate_capture_root is not None:
                report_roots.insert(0, Path(candidate_capture_root).expanduser().resolve())
            capture_report = next(
                (
                    report
                    for report_root in report_roots
                    if (report := _capture_report_for_root(report_root)) is not None
                ),
                None,
            )
            if capture_report is not None and (
                seed_preflight.capture_report_path is None
                or capture_report != seed_preflight.capture_report_path
            ):
                seed_preflight = seed_preflight.bind_capture_report(capture_report)
        runner = run_invocation if pipeline_runner is None else pipeline_runner
        result = runner(
            invocation,
            validate_only=args.validate_only,
            offline_tts=True,
        )
        if not isinstance(result, PipelineResult):
            raise Phase2PromoBuildError("pipeline runner must return PipelineResult")
        if not args.validate_only and result.succeeded:
            failure_phase = "final-duration"
            try:
                final_duration_seconds = composer.verify_final_deliverable(result)
            except Exception:
                _write_new_json(
                    workdir / "phase2-pipeline-result.json",
                    _result_mapping(
                        result,
                        final_duration_seconds=getattr(
                            composer,
                            "final_duration_seconds",
                            None,
                        ),
                        seed_preflight=seed_preflight,
                        media_preflight=media_preflight,
                        footage_intake=footage_intake,
                    ),
                )
                raise
            # The capture adapter hashes its source files at composition time;
            # recheck that immutable snapshot before accepting this long-running
            # build as a candidate.
            failure_phase = "capture-source-immutability"
            try:
                candidate.bundle.verify_unchanged()
            except CK3CaptureError as exc:
                raise Phase2PromoBuildError(
                    "phase-two capture source changed during pipeline: "
                    f"{exc}"
                ) from exc
        if seed_preflight is not None:
            seed_preflight.verify_unchanged()
        if media_preflight is not None:
            media_preflight.verify_unchanged()
    except Phase2FootagePending:
        # This is a pre-composition input state, not a failed media attempt.
        # Do not create a work directory or a synthetic failure artifact.
        raise
    except Exception as exc:
        if not args.validate_only and not workdir.exists():
            _write_entry_failure(workdir, failure_phase, exc)
        elif not args.validate_only and workdir.is_dir():
            marker = workdir / "phase2-entry-failure.json"
            if not marker.exists():
                _write_entry_failure(workdir, failure_phase, exc)
        raise

    run_path: Path | None = None
    if not args.validate_only:
        _write_new_json(
            workdir / "phase2-pipeline-result.json",
            _result_mapping(
                result,
                final_duration_seconds=final_duration_seconds,
                seed_preflight=seed_preflight,
                media_preflight=media_preflight,
                footage_intake=footage_intake,
            ),
        )
        if result.succeeded:
            failure_phase = "candidate-run-persistence"
            try:
                run_path = _persist_candidate_run(
                    config_path,
                    result,
                    args.run_id,
                    seed_preflight=seed_preflight,
                    media_preflight=media_preflight,
                )
            except Exception as exc:
                # ``_persist_candidate_run`` creates the run incrementally.
                # Keep any manifest/artifacts already written and record the
                # exact boundary instead of deleting or retrying the attempt.
                candidate_run = workdir / "candidate-run"
                try:
                    retained_paths = (
                        (candidate_run.resolve(),)
                        if candidate_run.exists()
                        else ()
                    )
                except OSError:
                    # A stat failure must not replace the persistence error;
                    # the attempt directory itself is still left untouched.
                    retained_paths = ()
                try:
                    if retained_paths:
                        _write_entry_failure(
                            workdir,
                            failure_phase,
                            exc,
                            retained_paths=retained_paths,
                        )
                    else:
                        _write_entry_failure(workdir, failure_phase, exc)
                except Exception as receipt_error:
                    # Preserve the original persistence exception even if a
                    # hostile/partial filesystem prevents writing the receipt.
                    exc.add_note(
                        "could not write phase2-entry-failure.json: "
                        f"{type(receipt_error).__name__}: {receipt_error}"
                    )
                raise

    blockers: list[str] = []
    if not result.succeeded:
        detail = "pipeline failed"
        if result.failure is not None:
            detail = (
                f"pipeline {result.failure.phase} failed: "
                f"{result.failure.exception_type}: {result.failure.message}"
            )
        blockers.append(detail)
    if not composer.real_narration_durations:
        blockers.append(
            "storyboard uses authoring estimates; final render needs ffprobe-observed cached narration"
        )
    if not candidate.phase_two_runtime_claims_verified:
        blockers.append("phase-two project-specific live runtime claim matrix is not verified")
    try:
        human_approved = _approved_deliverable(
            args.signed_run_manifest,
            config_path=config_path,
            result=result,
            media_preflight=media_preflight,
        )
    except (ArtifactError, ManifestError) as exc:
        raise Phase2PromoBuildError(f"invalid signed run manifest: {exc}") from exc
    if not human_approved:
        blockers.append("exact rendered bytes lack an approved full-duration human sign-off")
    if seed_preflight is None:
        blockers.append(
            "phase-two seed preflight report is not bound; pass --seed-preflight-report before release"
        )
    else:
        blockers.extend(seed_preflight.release_blockers)
    if media_preflight is None:
        blockers.append(
            "phase-two media environment preflight is not bound; pass --media-preflight-report and --expected-media-preflight-sha256 before release/export/publish"
        )
    blockers.extend(candidate.blockers)
    blockers = list(dict.fromkeys(blockers))
    return Phase2BuildOutcome(
        result=result,
        candidate=candidate,
        release_ready=not blockers,
        blockers=tuple(blockers),
        run_manifest_path=run_path,
        seed_preflight=seed_preflight,
        media_preflight=media_preflight,
        footage_intake=footage_intake,
        dependency_graph=final_promo_execution_dag(),
    )


def _default_font(name: str) -> Path:
    windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
    return windows / "Fonts" / name


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--project-config",
        type=Path,
        default=DEFAULT_PROJECT_CONFIG,
        help="phase-two xar_promo ProjectConfig",
    )
    result.add_argument("--capture-root", type=Path, required=True)
    result.add_argument(
        "--seed-preflight-report",
        type=Path,
        help=(
            "optional GREEN preflight.json from run_zg361_phase2_seed_capture.py "
            "--preflight-only; required for a release-ready outcome"
        ),
    )
    result.add_argument(
        "--media-preflight-report",
        type=Path,
        help=(
            "optional GREEN receipt from preflight_phase2_media.py; required "
            "with its SHA-256 for release/export/publish readiness"
        ),
    )
    result.add_argument(
        "--expected-media-preflight-sha256",
        help="expected SHA-256 of --media-preflight-report",
    )
    result.add_argument("--work-dir", type=Path, required=True)
    result.add_argument(
        "--tts-cache",
        type=Path,
        help="content-addressed xar_promo TTS cache; required for full build",
    )
    result.add_argument("--edge-tts-version", default=DEFAULT_EDGE_TTS_VERSION)
    result.add_argument("--ffmpeg", default="ffmpeg")
    result.add_argument("--ffprobe", default="ffprobe")
    result.add_argument("--zh-font-file", type=Path, default=_default_font("msyh.ttc"))
    result.add_argument("--en-font-file", type=Path, default=_default_font("segoeui.ttf"))
    result.add_argument("--run-id", default="phase2-candidate")
    result.add_argument(
        "--signed-run-manifest",
        type=Path,
        help="optional existing run whose approved deliverable must match exact candidate bytes",
    )
    result.add_argument(
        "--validate-only",
        action="store_true",
        help="read-only config/capture/draft validation; no TTS, probes, directories, or media writes",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        outcome = execute(args)
    except KeyboardInterrupt:
        print("RELEASE: RED\nERROR: interrupted", file=sys.stderr)
        return 130
    except Phase2FootagePending as exc:
        print(
            "RELEASE: RED\n"
            f"REASON_CODE: {exc.reason_code}\n"
            f"FOOTAGE INTAKE: {json.dumps(exc.report, ensure_ascii=False, sort_keys=True)}",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:
        print(f"RELEASE: RED\nERROR: {exc}", file=sys.stderr)
        return 2

    label = "VALIDATION" if args.validate_only else "CANDIDATE BUILD"
    print(f"{label}: {'GREEN' if outcome.result.succeeded else 'RED'}")
    print(f"RELEASE: {'GREEN' if outcome.release_ready else 'RED'}")
    print(f"CAPTURE: {outcome.candidate.bundle.artifact_root}")
    print(f"FOOTAGE INTAKE: {outcome.footage_intake['result']}")
    if outcome.seed_preflight is None:
        print("PREFLIGHT: unbound")
    else:
        print(
            "PREFLIGHT: "
            f"{outcome.seed_preflight.path} "
            f"sha256={outcome.seed_preflight.sha256}"
        )
    if outcome.media_preflight is None:
        print("MEDIA PREFLIGHT: unbound")
    else:
        print(
            "MEDIA PREFLIGHT: "
            f"{outcome.media_preflight.path} "
            f"sha256={outcome.media_preflight.sha256}"
        )
    print(f"WORK: {outcome.result.workdir}")
    if outcome.run_manifest_path is not None:
        print(f"UNREVIEWED RUN: {outcome.run_manifest_path}")
    for blocker in outcome.blockers:
        print(f"BLOCKER: {blocker}")
    return 0 if outcome.release_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
