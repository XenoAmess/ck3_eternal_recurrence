#!/usr/bin/env python3
"""Verify the local media environment for the ZhongGuo phase-two film.

This command does not consume CK3 captures, synthesize narration, or create a
promo candidate.  It performs a short disposable encoder test and writes one
exclusive JSON receipt describing the environment that passed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_TOOLS = REPOSITORY_ROOT / "tools"
if str(REPOSITORY_TOOLS) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_TOOLS))

import promo_toolchain_loader as toolchain_loader  # noqa: E402


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
VOICE = "zh-CN-XiaoxiaoNeural"
ZH_FONT_NAME = "Microsoft YaHei UI"
EN_FONT_NAME = "Segoe UI"
DEFAULT_PROJECT_CONFIG = (
    REPOSITORY_ROOT / "mod_zhongguo_style" / "promo" / "phase2-promo-project.json"
)


class MediaPreflightError(RuntimeError):
    """The local machine cannot yet render the final phase-two media."""


RunProcess = Callable[..., subprocess.CompletedProcess[str]]


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


def _toolchain_source_main(*, runner: RunProcess) -> dict[str, object]:
    if PACKAGE_SOURCE is None:
        raise MediaPreflightError(
            "phase-two production preflight requires XAR_PROMO_SOURCE to point "
            "at the updated standalone promo-toolchain main checkout"
        )
    source_root = PACKAGE_SOURCE.parent if PACKAGE_SOURCE.name == "src" else PACKAGE_SOURCE
    head = _run(
        ("git", "-C", source_root, "rev-parse", "HEAD"),
        action="reading promo-toolchain HEAD",
        runner=runner,
    ).stdout.strip()
    remote_main = _run(
        ("git", "-C", source_root, "rev-parse", "origin/main"),
        action="reading promo-toolchain origin/main",
        runner=runner,
    ).stdout.strip()
    if head != remote_main:
        raise MediaPreflightError(
            f"promo-toolchain HEAD is not local origin/main: {head} != {remote_main}"
        )
    status = _run(
        ("git", "-C", source_root, "status", "--short"),
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
    }


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
    with tempfile.TemporaryDirectory(prefix="xar-phase2-media-preflight-") as raw_temp:
        temp = Path(raw_temp)
        ass_path = temp / "probe.ass"
        ass_path.write_text(ass, encoding="utf-8")
        _run(
            (
                ffmpeg,
                "-hide_banner",
                "-nostdin",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}:d=0.25",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=48000:cl=stereo:d=0.25",
                "-vf",
                "ass=probe.ass",
                "-t",
                "0.25",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-f",
                "null",
                "-",
            ),
            action="checking libass/libx264/AAC render path",
            cwd=temp,
            timeout=args.encoder_timeout_seconds,
            runner=runner,
        )

    return {
        "schema_version": 1,
        "kind": "zhongguo-361-phase2-media-environment-preflight",
        "result": "GREEN",
        "scope": "environment-only; no CK3 capture, narration, candidate, review, or release claim",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "project": {"id": config.project_id, "chapters": len(config.chapters)},
        "promo_toolchain": {
            "version": xar_promo.__version__,
            **_toolchain_source_main(runner=runner),
        },
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "packages": {"edge-tts": edge_version, "Pillow": pillow_version},
        "voice": {"id": VOICE, "catalogue_match": voice_lines[0]},
        "fonts": {
            "zh-CN": {"family": ZH_FONT_NAME, "path": str(args.zh_font_file.resolve())},
            "en": {"family": EN_FONT_NAME, "path": str(args.en_font_file.resolve())},
        },
        "subtitle_layout": layout,
        "media": {
            "ffmpeg": str(ffmpeg),
            "ffmpeg_version": ffmpeg_version,
            "ffprobe": str(ffprobe),
            "ffprobe_version": ffprobe_version,
            "verified_filter": "ass/libass",
            "verified_video_encoder": "libx264",
            "verified_audio_encoder": "aac/48000Hz/stereo",
            "disposable_test_output_retained": False,
        },
    }


def _write_new(path: Path, payload: dict[str, object]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
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
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    windows_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    result.add_argument("--zh-font-file", type=Path, default=windows_fonts / "msyh.ttc")
    result.add_argument("--en-font-file", type=Path, default=windows_fonts / "segoeui.ttf")
    result.add_argument("--voice-timeout-seconds", type=float, default=60.0)
    result.add_argument("--encoder-timeout-seconds", type=float, default=60.0)
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
