#!/usr/bin/env python3
"""Verify the local media environment for the ZhongGuo phase-two film.

This command does not consume CK3 captures, synthesize narration, write
subtitle media, encode a probe, or create a promo candidate/work directory.
It queries installed capabilities and writes one exclusive JSON receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
if str(REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_TOOLS))

import promo_toolchain_loader as toolchain_loader  # noqa: E402
from zhongguo_phase2_footage_intake import validate_footage_intake  # noqa: E402
from zhongguo_phase2_publish_target import (  # noqa: E402
    validate_publish_target_authority,
)


PACKAGE_SOURCE = toolchain_loader.ensure_promo_toolchain()

import xar_promo  # noqa: E402
from xar_promo.layout import (  # noqa: E402
    FontSpec,
    SafeArea,
    TrackLayoutConfig,
    WrapPolicy,
    layout_tracks,
)
from xar_promo.presets.zhongguo_361_phase2 import (  # noqa: E402
    PHASE2_POLICY,
    load_phase2_project_config,
)
from xar_promo.subtitles import (  # noqa: E402
    AssCue,
    AssDocumentConfig,
    AssStyleConfig,
    SubtitleTrackConfig,
    render_ass_document,
)


WIDTH = 1920
HEIGHT = 1080
FPS = 30
EXPECTED_EDGE_TTS_VERSION = "7.2.8"
EXPECTED_PILLOW_VERSION = "12.3.0"
EXPECTED_TOOLCHAIN_VERSION = toolchain_loader.PROMO_TOOLCHAIN_VERSION
RECEIPT_VALID_FOR_SECONDS = 24 * 60 * 60
VOICE = "zh-CN-XiaoxiaoNeural"
ZH_FONT_NAME = "Microsoft YaHei UI"
EN_FONT_NAME = "Segoe UI"
DEFAULT_PROJECT_CONFIG = (
    REPOSITORY_ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json"
)


class MediaPreflightError(RuntimeError):
    """The local machine cannot yet render the final phase-two media."""


RunProcess = Callable[..., subprocess.CompletedProcess[str]]


def _file_record(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    digest = hashlib.sha256()
    try:
        size = resolved.stat().st_size
        with resolved.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise MediaPreflightError(f"could not bind environment file {resolved}: {exc}") from exc
    return {"path": str(resolved), "bytes": size, "sha256": digest.hexdigest().upper()}


def _program(value: str | None, name: str) -> Path:
    raw = value or shutil.which(name)
    if not raw:
        raise MediaPreflightError(f"could not find required executable: {name}")
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise MediaPreflightError(f"required executable is not a file: {path}")
    return path


def _run(
    argv: Sequence[str | os.PathLike[str]],
    *,
    action: str,
    cwd: Path | None = None,
    timeout: float = 60.0,
    runner: RunProcess = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    command = [os.fspath(value) for value in argv]
    try:
        result = runner(
            command,
            cwd=None if cwd is None else os.fspath(cwd),
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaPreflightError(f"{action} could not complete: {exc}") from exc
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()[-2000:]
        raise MediaPreflightError(
            f"{action} failed with exit code {result.returncode}: {details}"
        )
    return result


def _first_line(result: subprocess.CompletedProcess[str]) -> str:
    for stream in (result.stdout, result.stderr):
        for line in (stream or "").splitlines():
            if line.strip():
                return line.strip()
    raise MediaPreflightError("external command returned no version text")


def _git_checkout_command(source_root: Path, *arguments: str) -> tuple[str, ...]:
    """Build a read-only Git probe bound to this exact checkout.

    The promo checkout can be materialized by a different Windows service
    account than the one running this process.  Recent Git versions then
    reject even harmless ``rev-parse``/``status`` calls as a dubious-ownership
    repository.  Supplying a path-scoped safe-directory exception avoids a
    global Git configuration mutation while keeping the identity check tied
    to the explicitly selected checkout.
    """

    safe_root = str(source_root.expanduser().resolve())
    return (
        "git",
        "-c",
        f"safe.directory={safe_root}",
        "-C",
        safe_root,
        *arguments,
    )


def _toolchain_source_main(*, runner: RunProcess) -> dict[str, object]:
    if PACKAGE_SOURCE is None:
        raise MediaPreflightError(
            "phase-two production preflight requires XAR_PROMO_SOURCE to point "
            "at the updated standalone promo-toolchain main checkout"
        )
    source_root = PACKAGE_SOURCE.parent if PACKAGE_SOURCE.name == "src" else PACKAGE_SOURCE
    head = _run(
        _git_checkout_command(source_root, "rev-parse", "HEAD"),
        action="reading promo-toolchain HEAD",
        runner=runner,
    ).stdout.strip()
    remote_main = _run(
        _git_checkout_command(source_root, "rev-parse", "origin/main"),
        action="reading promo-toolchain origin/main",
        runner=runner,
    ).stdout.strip()
    if head != remote_main:
        raise MediaPreflightError(
            f"promo-toolchain HEAD is not local origin/main: {head} != {remote_main}"
        )
    status = _run(
        _git_checkout_command(source_root, "status", "--short"),
        action="checking promo-toolchain cleanliness",
        runner=runner,
    ).stdout.strip()
    if status:
        raise MediaPreflightError("promo-toolchain checkout is not clean")
    return {
        "source_root": str(source_root.resolve()),
        "head": head,
        "origin_main": remote_main,
        "clean": True,
        "remote_fetch_performed_by_preflight": False,
        "production_refresh_still_required": True,
    }


def _planned_path(path: Path | None) -> dict[str, object]:
    """Inspect a future output path without creating it or probing with a file."""

    if path is None:
        return {
            "configured": False,
            "ready": False,
            "path_created": False,
            "write_probe_performed": False,
        }
    resolved = path.expanduser().resolve()
    ancestor = resolved
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    ancestor_ready = ancestor.is_dir() and os.access(ancestor, os.W_OK)
    target_shape_ok = not resolved.exists() or resolved.is_dir()
    free_bytes = shutil.disk_usage(ancestor).free if ancestor.is_dir() else 0
    return {
        "configured": True,
        "path": str(resolved),
        "target_exists": resolved.exists(),
        "target_is_directory_or_absent": target_shape_ok,
        "nearest_existing_ancestor": str(ancestor),
        "ancestor_writable": ancestor_ready,
        "free_bytes_observed": free_bytes,
        "ready": ancestor_ready and target_shape_ok and free_bytes > 0,
        "path_created": False,
        "write_probe_performed": False,
    }


def _require_capability(text: str, token: str, label: str) -> None:
    if token.casefold() not in text.casefold():
        raise MediaPreflightError(f"FFmpeg capability is missing: {label}")


def _load_fonts(zh_font: Path, en_font: Path):
    try:
        from PIL import ImageFont
    except ImportError as exc:
        raise MediaPreflightError("Pillow is required for measured subtitle layout") from exc
    handles = {}
    for key, path, size in (
        ("zh", zh_font, 46),
        ("en", en_font, 30),
    ):
        if not path.is_file():
            raise MediaPreflightError(f"required {key} font is missing: {path}")
        try:
            handles[key] = ImageFont.truetype(str(path), size=size)
        except OSError as exc:
            raise MediaPreflightError(f"could not load {key} font {path}: {exc}") from exc
    return handles


def _layout_and_ass(zh_font: Path, en_font: Path) -> tuple[dict[str, object], str]:
    handles = _load_fonts(zh_font, en_font)
    fonts = {
        "zh": FontSpec("zh", ZH_FONT_NAME, 46, 700),
        "en": FontSpec("en", EN_FONT_NAME, 30, 600),
    }

    def measure(text: str, font: FontSpec) -> float:
        return float(handles[font.key].getlength(text))

    punctuation = WrapPolicy(
        force_break_after=frozenset({"。", "！", "？"}),
        prefer_break_after=frozenset({"，", "、", "：", ",", ":", ";"}),
        decimal_separators=frozenset({".", "。"}),
    )
    tracks = (
        TrackLayoutConfig(
            "en",
            "en",
            layer=0,
            stack_order=0,
            max_lines=2,
            line_height_px=42,
            horizontal_inset_px=20,
            gap_above_px=16,
        ),
        TrackLayoutConfig(
            "zh-CN",
            "zh",
            layer=1,
            stack_order=1,
            max_lines=2,
            line_height_px=60,
            wrap_policy=punctuation,
        ),
    )
    text = {
        "zh-CN": "双语字幕预检：中文按句意换行，并保持在画面安全区内。",
        "en": "Bilingual subtitle preflight: English wrapping stays inside the frame-safe area.",
    }
    positioned = layout_tracks(
        text,
        tracks=tracks,
        fonts=fonts,
        safe_area=SafeArea.from_margins(
            frame_width=WIDTH,
            frame_height=HEIGHT,
            left=90,
            top=64,
            right=90,
            bottom=64,
        ),
        measure=measure,
    )
    wrapped = {
        track.track_id: "\\N".join(line.text for line in track.lines)
        for track in positioned
    }
    ass = render_ass_document(
        AssDocumentConfig("ZhongGuo phase-two media preflight", WIDTH, HEIGHT, 1.0),
        (
            SubtitleTrackConfig(
                "zh-CN",
                "zh-CN",
                1,
                AssStyleConfig(
                    "ChinesePrimary", ZH_FONT_NAME, 46, outline=3, shadow=1,
                    alignment=2, margin_left=90, margin_right=90, margin_vertical=142,
                ),
            ),
            SubtitleTrackConfig(
                "en",
                "en",
                0,
                AssStyleConfig(
                    "EnglishSecondary", EN_FONT_NAME, 30, outline=2, shadow=1,
                    alignment=2, margin_left=110, margin_right=110, margin_vertical=64,
                ),
            ),
        ),
        tuple(
            AssCue(f"{locale}-probe", locale, 0, 1.0, wrapped[locale])
            for locale in PHASE2_POLICY.subtitle_locales
        ),
        available_font_names={ZH_FONT_NAME, EN_FONT_NAME},
    )
    summary = {
        "frame": [WIDTH, HEIGHT],
        "safe_margins": {"left": 90, "top": 64, "right": 90, "bottom": 64},
        "tracks": [
            {
                "id": track.track_id,
                "bounds": [track.left, track.top, track.right, track.bottom],
                "lines": [
                    {"text": line.text, "width": round(line.width, 3), "x": round(line.x, 3)}
                    for line in track.lines
                ],
            }
            for track in positioned
        ],
    }
    return summary, ass


def run_preflight(args: argparse.Namespace, *, runner: RunProcess = subprocess.run) -> dict[str, object]:
    if getattr(xar_promo, "__version__", None) != EXPECTED_TOOLCHAIN_VERSION:
        raise MediaPreflightError(
            f"xar-promo-toolchain {EXPECTED_TOOLCHAIN_VERSION} is required; "
            f"got {getattr(xar_promo, '__version__', None)!r}"
        )
    edge_version = importlib.metadata.version("edge-tts")
    pillow_version = importlib.metadata.version("Pillow")
    if edge_version != EXPECTED_EDGE_TTS_VERSION:
        raise MediaPreflightError(
            f"edge-tts {EXPECTED_EDGE_TTS_VERSION} is required; got {edge_version}"
        )
    if pillow_version != EXPECTED_PILLOW_VERSION:
        raise MediaPreflightError(
            f"Pillow {EXPECTED_PILLOW_VERSION} is required; got {pillow_version}"
        )

    config = load_phase2_project_config(args.project_config)
    if config.subtitle_locales != ("zh-CN", "en") or PHASE2_POLICY.voice != VOICE:
        raise MediaPreflightError("phase-two locale or voice policy drifted")
    ffmpeg = _program(args.ffmpeg, "ffmpeg")
    ffprobe = _program(args.ffprobe, "ffprobe")
    ffmpeg_version = _first_line(
        _run((ffmpeg, "-version"), action="checking FFmpeg", runner=runner)
    )
    ffprobe_version = _first_line(
        _run((ffprobe, "-version"), action="checking ffprobe", runner=runner)
    )
    voice_result = _run(
        (sys.executable, "-m", "edge_tts", "--list-voices"),
        action="checking live Edge TTS voice catalogue",
        timeout=args.voice_timeout_seconds,
        runner=runner,
    )
    voice_lines = [line.strip() for line in voice_result.stdout.splitlines() if VOICE in line]
    if not voice_lines:
        raise MediaPreflightError(f"Edge TTS voice catalogue does not contain {VOICE}")

    layout, ass = _layout_and_ass(args.zh_font_file, args.en_font_file)
    if not ass.startswith("[Script Info]") or not all(
        style in ass for style in ("ChinesePrimary", "EnglishSecondary")
    ):
        raise MediaPreflightError("in-memory subtitle document contract drifted")

    capability_results = {
        "encoders": _run(
            (ffmpeg, "-hide_banner", "-encoders"),
            action="querying FFmpeg encoders",
            timeout=args.encoder_timeout_seconds,
            runner=runner,
        ),
        "filters": _run(
            (ffmpeg, "-hide_banner", "-filters"),
            action="querying FFmpeg filters",
            timeout=args.encoder_timeout_seconds,
            runner=runner,
        ),
        "pixel_formats": _run(
            (ffmpeg, "-hide_banner", "-pix_fmts"),
            action="querying FFmpeg pixel formats",
            timeout=args.encoder_timeout_seconds,
            runner=runner,
        ),
        "formats": _run(
            (ffmpeg, "-hide_banner", "-formats"),
            action="querying FFmpeg formats",
            timeout=args.encoder_timeout_seconds,
            runner=runner,
        ),
        "ffprobe_formats": _run(
            (ffprobe, "-hide_banner", "-formats"),
            action="querying ffprobe formats",
            timeout=args.encoder_timeout_seconds,
            runner=runner,
        ),
    }
    capability_text = {
        key: f"{value.stdout}\n{value.stderr}" for key, value in capability_results.items()
    }
    _require_capability(capability_text["encoders"], "libx264", "libx264 encoder")
    _require_capability(capability_text["encoders"], "aac", "AAC encoder")
    _require_capability(capability_text["filters"], "ass", "ASS/libass filter")
    _require_capability(capability_text["pixel_formats"], "yuv420p", "yuv420p")
    _require_capability(capability_text["formats"], "mp4", "MP4 muxer")
    _require_capability(capability_text["ffprobe_formats"], "mp4", "MP4 demuxer")

    path_targets = {
        "work_dir": _planned_path(args.planned_work_dir),
        "tts_cache": _planned_path(args.planned_tts_cache),
        "export_dir": _planned_path(args.planned_export_dir),
    }
    configured_paths = [row for row in path_targets.values() if row["configured"]]
    if configured_paths and not all(row["ready"] for row in configured_paths):
        raise MediaPreflightError("one or more planned output paths are not usable")

    footage = validate_footage_intake(args.capture_root)
    publish_target = validate_publish_target_authority(args.publish_target_authority)
    toolchain = _toolchain_source_main(runner=runner)
    expected_head = args.expected_toolchain_head
    fresh_fetch_verified = (
        isinstance(expected_head, str)
        and expected_head.strip() == toolchain["head"]
        and toolchain["head"] == toolchain["origin_main"]
        and toolchain["clean"] is True
    )
    production_blockers = [] if fresh_fetch_verified else ["fresh_promo_tool_fetch_required"]
    if footage["result"] != "GREEN":
        production_blockers.append("footage_pending")
    if publish_target["result"] != "GREEN":
        production_blockers.append("publish_target_pending")

    generated_at = dt.datetime.now(dt.timezone.utc)
    expires_at = generated_at + dt.timedelta(seconds=RECEIPT_VALID_FOR_SECONDS)
    return {
        "schema_version": 1,
        "kind": "zhongguo-361-phase2-media-environment-preflight",
        "result": "GREEN",
        "scope": "environment-only; no CK3 capture, narration, candidate, review, or release claim",
        "generated_at_utc": generated_at.isoformat(timespec="seconds"),
        "valid_for_seconds": RECEIPT_VALID_FOR_SECONDS,
        "expires_at_utc": expires_at.isoformat(timespec="seconds"),
        "preflight_implementation": _file_record(Path(__file__)),
        "project": {
            "id": config.project_id,
            "chapters": len(config.chapters),
            "config": _file_record(args.project_config),
        },
        "promo_toolchain": {
            "version": xar_promo.__version__,
            **toolchain,
            "expected_head_from_fresh_fetch": expected_head,
            "fresh_fetch_verified": fresh_fetch_verified,
            "production_refresh_still_required": not fresh_fetch_verified,
        },
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "packages": {"edge-tts": edge_version, "Pillow": pillow_version},
        "voice": {
            "id": VOICE,
            "provider": "edge-tts",
            "configured": True,
            "live_catalogue_checked": True,
            "catalogue_match": voice_lines[0],
            "credential_required": False,
            "credential_presence": "not-applicable",
            "credential_value_exposed": False,
            "synthesis_performed": False,
        },
        "fonts": {
            "zh-CN": {"family": ZH_FONT_NAME, **_file_record(args.zh_font_file)},
            "en": {"family": EN_FONT_NAME, **_file_record(args.en_font_file)},
        },
        "subtitle_layout": layout,
        "subtitle_engine": {
            "layout_module": "xar_promo.layout",
            "render_module": "xar_promo.subtitles",
            "pillow_version": pillow_version,
            "automatic_wrap_measured_in_memory": True,
            "ass_written": False,
        },
        "media": {
            "ffmpeg": _file_record(ffmpeg),
            "ffmpeg_version": ffmpeg_version,
            "ffprobe": _file_record(ffprobe),
            "ffprobe_version": ffprobe_version,
            "capability_query": {
                "filter": "ass/libass",
                "video_encoder": "libx264",
                "video_geometry": [WIDTH, HEIGHT],
                "frame_rate": FPS,
                "pixel_format": "yuv420p",
                "audio_encoder": "aac",
                "audio_sample_rate": 48000,
                "audio_channels": 2,
                "container_muxer": "mp4",
                "ffprobe_demuxer": "mp4",
            },
            "verified_filter": "ass/libass",
            "verified_video_encoder": "libx264",
            "verified_audio_encoder": "aac/48000Hz/stereo",
            "ffmpeg_encode_started": False,
            "probe_media_created": False,
            "disposable_test_output_retained": False,
        },
        "planned_paths": path_targets,
        "footage_gate": footage,
        "publish_target_gate": publish_target,
        "final_promo_readiness": {
            "result": "RED" if production_blockers else "GREEN",
            "status": "waiting-for-inputs" if production_blockers else "ready",
            "reason_codes": production_blockers,
            "environment_preflight_green": True,
        },
        "execution_attestation": {
            "ck3_started": False,
            "tts_synthesis_performed": False,
            "subtitle_media_written": False,
            "ffmpeg_encode_started": False,
            "work_directory_created": False,
            "candidate_generated": False,
        },
    }


def _write_new(path: Path, payload: dict[str, object]) -> None:
    path = path.expanduser().resolve()
    if not path.parent.is_dir():
        raise MediaPreflightError(f"receipt parent does not exist: {path.parent}")
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise MediaPreflightError(f"refusing to overwrite preflight receipt: {path}") from exc


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--project-config", type=Path, default=DEFAULT_PROJECT_CONFIG)
    result.add_argument(
        "--expected-toolchain-head",
        help=(
            "HEAD printed by the immediately preceding fetch/ff-only verification; "
            "must still equal clean origin/main to clear the production refresh gate"
        ),
    )
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    windows_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    result.add_argument("--zh-font-file", type=Path, default=windows_fonts / "msyh.ttc")
    result.add_argument("--en-font-file", type=Path, default=windows_fonts / "segoeui.ttf")
    result.add_argument("--voice-timeout-seconds", type=float, default=60.0)
    result.add_argument("--encoder-timeout-seconds", type=float, default=60.0)
    result.add_argument("--planned-work-dir", type=Path)
    result.add_argument("--planned-tts-cache", type=Path)
    result.add_argument("--planned-export-dir", type=Path)
    result.add_argument("--capture-root", type=Path)
    result.add_argument("--publish-target-authority", type=Path)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        payload = run_preflight(args)
        _write_new(args.output, payload)
    except Exception as exc:
        print(f"PHASE2 MEDIA PREFLIGHT: RED\nERROR: {exc}", file=sys.stderr)
        return 2
    print(f"PHASE2 MEDIA PREFLIGHT: GREEN\nRECEIPT: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
