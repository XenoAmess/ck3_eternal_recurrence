#!/usr/bin/env python3
"""Build a bilingual 2560x1440 CK3 autonomous-agent showcase.

The builder is deliberately manifest-driven.  It never launches CK3 and it never
interprets an evidence artifact as a capability claim: the caller supplies the
classification that is rendered on screen and copied verbatim into the sidecar.

Minimal manifest (UTF-8 JSON)::

    {
      "format_version": 1,
      "voice": "en-GB-SoniaNeural",
      "chapters": [
        {
          "id": "opening",
          "type": "title_card",
          "title_en": "The CK3 Autonomous Agent",
          "title_zh": "CK3 自动游玩智能体",
          "narration_en": "This film shows the capabilities that exist today.",
          "subtitle_zh": "本片展示智能体今天已经具备的能力。",
          "status": {
            "en": "CAPABILITY SHOWCASE",
            "zh": "能力总览",
            "classification": "showcase"
          },
          "body_en": ["Observe", "Decide", "Act", "Verify"],
          "body_zh": ["观察", "决策", "操作", "验证"]
        },
        {
          "id": "war-still",
          "type": "still",
          "source": "../artifacts/war.png",
          "title_en": "War: movement and siege",
          "title_zh": "战争：行军与围城",
          "narration_en": "The agent selects an army and issues a siege order.",
          "subtitle_zh": "智能体选择军队并下达围城命令。",
          "status": {
            "en": "HISTORICAL VISUAL",
            "zh": "历史实机画面",
            "classification": "historical-visual"
          }
        },
        {
          "id": "event-video",
          "type": "video_clip",
          "source": "../artifacts/event.mp4",
          "start_seconds": 41.0,
          "end_seconds": 66.0,
          "title_en": "Exact-build event observation",
          "title_zh": "精确版本事件观测",
          "narration_en": "The native bridge reads the paused event window.",
          "subtitle_zh": "原生桥读取暂停状态下的事件窗口。",
          "status": {
            "en": "FIXTURE LIVE",
            "zh": "夹具实机",
            "classification": "fixture-live"
          }
        },
        {
          "id": "evidence",
          "type": "evidence_card",
          "sources": [
            {"path": "../artifacts/live.json", "label": "Live artifact"}
          ],
          "title_en": "Evidence and honest boundary",
          "title_zh": "证据与真实边界",
          "narration_en": "The immutable artifact is green, but the query is read only.",
          "subtitle_zh": "不可变实机证据为绿色，但该查询仍是只读能力。",
          "status": {
            "en": "FIXTURE LIVE",
            "zh": "夹具实机",
            "classification": "fixture-live"
          },
          "body_en": ["Artifact: GREEN", "Action: not executed"],
          "body_zh": ["证据：绿色", "动作：未执行"]
        }
      ]
    }

Every chapter is narrated with the online Microsoft Edge text-to-speech service
through ``edge-tts``.  The default voice is ``en-GB-SoniaNeural``.  Its shot
length is the greater of the narration duration plus tail padding and
``min_duration_seconds``.  A short video source is extended by cloning its final
frame; narration is never cut.
Chinese narration translations are split at semantic punctuation, wrapped by
measured font width, divided into short timed ASS cues, and burned into each
segment.  The final MP4 is H.264/yuv420p plus 48 kHz stereo AAC.  A sibling
``*.video.json`` records chapter timing, source hashes and classifications.

Paths in the manifest are resolved relative to the manifest. Environment-variable
expansion is supported. All subprocesses receive argv lists, so spaces in paths are
safe. The work directory is content-addressed and may be reused on another run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


from promo_toolchain_loader import ensure_promo_toolchain  # noqa: E402


# The reusable package is installed from the independent GitHub release in
# normal runs.  ``XAR_PROMO_SOURCE`` (or the longer compatibility alias) may
# explicitly point at a checkout/src directory for local development.
PROMO_TOOLCHAIN_SOURCE = ensure_promo_toolchain()

from xar_promo.media import MediaProbeError, ffprobe_command, parse_ffprobe_json  # noqa: E402
from xar_promo.layout import LayoutError, balance_lines  # noqa: E402
from xar_promo.legacy import (  # noqa: E402
    LegacyCompatibilityError,
    LegacyPipelineSegment,
    compatible_ass_escape,
    compatible_ass_timestamp,
    compatible_concat_manifest,
    compatible_seconds,
    validate_legacy_pipeline_projection,
)
from xar_promo.tts import EdgeTtsProvider, TtsRequest  # noqa: E402


try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as exc:  # handled with a repository-specific hint in main()
    Image = ImageDraw = ImageFont = ImageOps = None  # type: ignore[assignment]
    PIL_IMPORT_ERROR: Exception | None = exc
else:
    PIL_IMPORT_ERROR = None

try:
    import edge_tts
except ImportError as exc:  # handled with a repository-specific hint in build()
    edge_tts = None  # type: ignore[assignment]
    EDGE_TTS_IMPORT_ERROR: Exception | None = exc
    EDGE_TTS_VERSION: str | None = None
else:
    EDGE_TTS_IMPORT_ERROR = None
    try:
        EDGE_TTS_VERSION = importlib.metadata.version("edge-tts")
    except importlib.metadata.PackageNotFoundError:
        EDGE_TTS_VERSION = "unknown"


FORMAT_VERSION = 1
BUILD_FORMAT_VERSION = 4
WIDTH = 2560
HEIGHT = 1440
DEFAULT_FPS = 30
DEFAULT_MIN_DURATION = 3.0
DEFAULT_TAIL_PADDING = 0.75
DEFAULT_CRF = 18
DEFAULT_PRESET = "medium"
EDGE_TTS_PROVIDER = "edge-tts"
DEFAULT_EDGE_TTS_VOICE = "en-GB-SoniaNeural"
EDGE_TTS_RATE = "+0%"
EDGE_TTS_VOLUME = "+0%"
EDGE_TTS_PITCH = "+0Hz"
ALLOWED_TYPES = {"title_card", "still", "video_clip", "evidence_card"}
SUBTITLE_FONT_NAME = "Microsoft YaHei UI"
SUBTITLE_FONT_SIZE = 42
SUBTITLE_MARGIN_HORIZONTAL = 300
SUBTITLE_MARGIN_VERTICAL = 175
# Pillow measures the exact bold Chinese font used to author the ASS layout.  The
# rendered line is kept narrower than the ASS margins as a guard against small
# metric differences between Pillow/FreeType and libass/fontconfig.
SUBTITLE_MAX_TEXT_WIDTH = 1840
SUBTITLE_MAX_TOTAL_LINES = 6
SUBTITLE_MAX_LINES_PER_CUE = 3
SUBTITLE_MAJOR_BREAKS = frozenset("。！？；!?;")
SUBTITLE_MINOR_BREAKS = frozenset("，、：,:")


class ShowcaseError(RuntimeError):
    """A user-actionable manifest, dependency, or encoding failure."""


@dataclass(frozen=True)
class SourceRecord:
    path: Path
    label: str
    role: str
    bytes: int
    sha256: str

    def sidecar(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "label": self.label,
            "role": self.role,
            "bytes": self.bytes,
            "sha256": self.sha256,
        }


@dataclass
class Chapter:
    index: int
    chapter_id: str
    kind: str
    title_en: str
    title_zh: str
    narration_en: str
    subtitle_zh: str
    status_en: str
    status_zh: str
    classification: str
    body_en: list[str]
    body_zh: list[str]
    sources: list[SourceRecord]
    source_path: Path | None
    start_seconds: float
    end_seconds: float | None
    min_duration_seconds: float
    tail_padding_seconds: float
    fit: str
    raw: dict[str, Any]
    source_duration_seconds: float | None = None
    narration_path: Path | None = None
    narration_duration_seconds: float | None = None
    voice: str | None = None
    tts_provider: str | None = None
    tts_provider_version: str | None = None
    tts_settings: dict[str, str] | None = None
    shot_duration_seconds: float | None = None
    encoded_duration_seconds: float | None = None
    segment_path: Path | None = None
    subtitle_lines: list[str] | None = None
    subtitle_line_widths: list[float] | None = None
    subtitle_cue_blocks: list[list[str]] | None = None


@dataclass(frozen=True)
class Fonts:
    english_regular_path: Path
    english_bold_path: Path
    chinese_regular_path: Path
    chinese_bold_path: Path

    def english(self, size: int, *, bold: bool = False):
        return ImageFont.truetype(
            str(self.english_bold_path if bold else self.english_regular_path), size
        )

    def chinese(self, size: int, *, bold: bool = False):
        return ImageFont.truetype(
            str(self.chinese_bold_path if bold else self.chinese_regular_path), size
        )


def _sha256(path: Path, cache: dict[Path, str] | None = None) -> str:
    canonical = path.resolve()
    if cache is not None and canonical in cache:
        return cache[canonical]
    digest = hashlib.sha256()
    with canonical.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    value = digest.hexdigest().upper()
    if cache is not None:
        cache[canonical] = value
    return value


def _json_fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _required_string(container: dict[str, Any], key: str, context: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ShowcaseError(f"{context}: '{key}' must be a non-empty string")
    return value.strip()


def _optional_string(container: dict[str, Any], key: str, default: str = "") -> str:
    value = container.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ShowcaseError(f"'{key}' must be a string when present")
    return value.strip()


def _number(
    container: dict[str, Any],
    key: str,
    default: float,
    context: str,
    *,
    minimum: float = 0.0,
) -> float:
    value = container.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ShowcaseError(f"{context}: '{key}' must be a number")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise ShowcaseError(f"{context}: '{key}' must be >= {minimum}")
    return result


def _as_text_lines(value: Any, key: str, context: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, list):
        result: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                raise ShowcaseError(
                    f"{context}: '{key}[{index}]' must be a non-empty string"
                )
            result.append(item.strip())
        return result
    raise ShowcaseError(f"{context}: '{key}' must be a string or array of strings")


def _resolve_material_path(value: str, manifest_directory: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    candidate = Path(expanded)
    if not candidate.is_absolute():
        candidate = manifest_directory / candidate
    return candidate.resolve()


def _normalize_kind(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip(".-")
    return (slug or "chapter")[:64]


def _load_json(path: Path, context: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ShowcaseError(f"{context} was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ShowcaseError(
            f"{context} is not valid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ShowcaseError(f"could not read {context} {path}: {exc}") from exc


def _source_spec(
    value: Any,
    *,
    role: str,
    default_label: str,
    context: str,
    manifest_directory: Path,
) -> tuple[Path, str, str]:
    if isinstance(value, str):
        raw_path = value
        label = default_label
        source_role = role
    elif isinstance(value, dict):
        raw_path = _required_string(value, "path", context)
        label = _optional_string(value, "label", default_label) or default_label
        source_role = _optional_string(value, "role", role) or role
    else:
        raise ShowcaseError(f"{context}: source must be a path string or object")
    return (
        _resolve_material_path(raw_path, manifest_directory),
        label,
        source_role,
    )


def load_manifest(path: Path) -> tuple[dict[str, Any], list[Chapter]]:
    manifest = _load_json(path, "manifest")
    if not isinstance(manifest, dict):
        raise ShowcaseError("manifest root must be a JSON object")
    version = manifest.get("format_version")
    if version != FORMAT_VERSION:
        raise ShowcaseError(
            f"manifest format_version must be {FORMAT_VERSION}, got {version!r}"
        )
    rows = manifest.get("chapters")
    if not isinstance(rows, list) or not rows:
        raise ShowcaseError("manifest 'chapters' must be a non-empty array")

    manifest_directory = path.resolve().parent
    pending_sources: list[tuple[Path, str, str, str]] = []
    preliminary: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    global_minimum = _number(
        manifest,
        "minimum_chapter_seconds",
        DEFAULT_MIN_DURATION,
        "manifest",
        minimum=0.1,
    )
    global_padding = _number(
        manifest,
        "narration_padding_seconds",
        DEFAULT_TAIL_PADDING,
        "manifest",
        minimum=0.0,
    )

    for index, raw in enumerate(rows):
        context = f"chapter[{index}]"
        if not isinstance(raw, dict):
            raise ShowcaseError(f"{context} must be a JSON object")
        chapter_id = _required_string(raw, "id", context)
        if chapter_id in seen_ids:
            raise ShowcaseError(f"{context}: duplicate id {chapter_id!r}")
        seen_ids.add(chapter_id)
        kind = _normalize_kind(_required_string(raw, "type", context))
        if kind not in ALLOWED_TYPES:
            raise ShowcaseError(
                f"{context}: unsupported type {kind!r}; expected one of "
                + ", ".join(sorted(ALLOWED_TYPES))
            )
        title_en = _required_string(raw, "title_en", context)
        title_zh = _required_string(raw, "title_zh", context)
        narration_en = _required_string(raw, "narration_en", context)
        subtitle_zh = _required_string(raw, "subtitle_zh", context)
        status = raw.get("status")
        if not isinstance(status, dict):
            raise ShowcaseError(f"{context}: 'status' must be an object")
        status_en = _required_string(status, "en", f"{context}.status")
        status_zh = _required_string(status, "zh", f"{context}.status")
        classification = _required_string(
            status, "classification", f"{context}.status"
        )
        fit = _optional_string(raw, "fit", "contain").lower()
        if fit not in {"contain", "cover"}:
            raise ShowcaseError(f"{context}: 'fit' must be 'contain' or 'cover'")

        source_specs: list[tuple[Path, str, str]] = []
        source_path: Path | None = None
        if kind in {"still", "video_clip"}:
            if "source" not in raw:
                raise ShowcaseError(f"{context}: '{kind}' requires 'source'")
            spec = _source_spec(
                raw["source"],
                role="visual",
                default_label="Visual source",
                context=f"{context}.source",
                manifest_directory=manifest_directory,
            )
            source_specs.append(spec)
            source_path = spec[0]
        elif kind == "evidence_card":
            source_values = raw.get("sources")
            if not isinstance(source_values, list) or not source_values:
                raise ShowcaseError(
                    f"{context}: 'evidence_card' requires a non-empty 'sources' array"
                )
            for source_index, value in enumerate(source_values):
                source_specs.append(
                    _source_spec(
                        value,
                        role="evidence",
                        default_label=f"Evidence {source_index + 1}",
                        context=f"{context}.sources[{source_index}]",
                        manifest_directory=manifest_directory,
                    )
                )

        for source, label, role in source_specs:
            pending_sources.append((source, label, role, context))

        start_seconds = _number(raw, "start_seconds", 0.0, context)
        end_seconds: float | None = None
        if "end_seconds" in raw:
            end_seconds = _number(raw, "end_seconds", 0.0, context, minimum=0.001)
            if end_seconds <= start_seconds:
                raise ShowcaseError(
                    f"{context}: 'end_seconds' must be greater than 'start_seconds'"
                )
        elif "clip_duration_seconds" in raw:
            clip_duration = _number(
                raw, "clip_duration_seconds", 0.0, context, minimum=0.001
            )
            end_seconds = start_seconds + clip_duration
        if kind != "video_clip" and (start_seconds != 0.0 or end_seconds is not None):
            raise ShowcaseError(
                f"{context}: clip timing is only valid for a video_clip chapter"
            )

        preliminary.append(
            {
                "index": index,
                "chapter_id": chapter_id,
                "kind": kind,
                "title_en": title_en,
                "title_zh": title_zh,
                "narration_en": narration_en,
                "subtitle_zh": subtitle_zh,
                "status_en": status_en,
                "status_zh": status_zh,
                "classification": classification,
                "body_en": _as_text_lines(raw.get("body_en"), "body_en", context),
                "body_zh": _as_text_lines(raw.get("body_zh"), "body_zh", context),
                "source_specs": source_specs,
                "source_path": source_path,
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "min_duration_seconds": _number(
                    raw,
                    "min_duration_seconds",
                    global_minimum,
                    context,
                    minimum=0.1,
                ),
                "tail_padding_seconds": _number(
                    raw,
                    "tail_padding_seconds",
                    global_padding,
                    context,
                    minimum=0.0,
                ),
                "fit": fit,
                "raw": raw,
            }
        )

    missing: list[str] = []
    non_files: list[str] = []
    for source, _label, _role, context in pending_sources:
        if not source.exists():
            missing.append(f"  - {context}: {source}")
        elif not source.is_file():
            non_files.append(f"  - {context}: {source}")
    if missing:
        raise ShowcaseError(
            "required showcase material was not found:\n" + "\n".join(missing)
        )
    if non_files:
        raise ShowcaseError(
            "showcase material must be regular files:\n" + "\n".join(non_files)
        )

    hash_cache: dict[Path, str] = {}
    chapters: list[Chapter] = []
    for values in preliminary:
        sources = [
            SourceRecord(
                path=source,
                label=label,
                role=role,
                bytes=source.stat().st_size,
                sha256=_sha256(source, hash_cache),
            )
            for source, label, role in values.pop("source_specs")
        ]
        chapters.append(Chapter(sources=sources, **values))
    return manifest, chapters


def find_program(explicit: str | None, name: str, *, sibling_of: Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(os.path.expandvars(os.path.expanduser(explicit))))
    if sibling_of is not None:
        candidates.append(sibling_of.parent / f"{name}.exe")
        candidates.append(sibling_of.parent / name)
    located = shutil.which(name)
    if located:
        candidates.append(Path(located))
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    hint = f" (requested path: {explicit})" if explicit else ""
    raise ShowcaseError(f"could not find required program '{name}'{hint}")


def find_fonts() -> Fonts:
    windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
    directory = windows / "Fonts"

    def first(names: Iterable[str], label: str) -> Path:
        for name in names:
            candidate = directory / name
            if candidate.is_file():
                return candidate.resolve()
        raise ShowcaseError(
            f"could not find a Windows system font for {label} under {directory}"
        )

    return Fonts(
        english_regular_path=first(("segoeui.ttf", "arial.ttf"), "English text"),
        english_bold_path=first(("segoeuib.ttf", "arialbd.ttf"), "English bold text"),
        chinese_regular_path=first(("msyh.ttc", "msyhl.ttc"), "Simplified Chinese text"),
        chinese_bold_path=first(("msyhbd.ttc", "msyh.ttc"), "Simplified Chinese bold text"),
    )


def run_checked(command: Sequence[str | Path], *, cwd: Path | None, action: str) -> subprocess.CompletedProcess[str]:
    argv = [str(value) for value in command]
    try:
        result = subprocess.run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        raise ShowcaseError(f"{action} could not start {argv[0]}: {exc}") from exc
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        if len(details) > 8000:
            details = details[-8000:]
        rendered = subprocess.list2cmdline(argv)
        raise ShowcaseError(
            f"{action} failed with exit code {result.returncode}\n"
            f"command: {rendered}\n{details}"
        )
    return result


def probe_media(ffprobe: Path, path: Path) -> dict[str, Any]:
    result = run_checked(
        ffprobe_command(ffprobe, path),
        cwd=None,
        action=f"probing media {path}",
    )
    try:
        return dict(parse_ffprobe_json(result.stdout).raw)
    except MediaProbeError as exc:
        raise ShowcaseError(f"ffprobe returned invalid JSON for {path}: {exc}") from exc


def _duration_from_probe(payload: dict[str, Any], path: Path) -> float:
    candidates: list[Any] = []
    format_row = payload.get("format")
    if isinstance(format_row, dict):
        candidates.append(format_row.get("duration"))
    for stream in payload.get("streams", []):
        if isinstance(stream, dict):
            candidates.append(stream.get("duration"))
    for candidate in candidates:
        try:
            value = float(candidate)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value) and value > 0:
            return value
    raise ShowcaseError(f"media duration is unavailable or invalid: {path}")


def preflight_video_sources(chapters: list[Chapter], ffprobe: Path) -> None:
    for chapter in chapters:
        if chapter.kind != "video_clip" or chapter.source_path is None:
            continue
        payload = probe_media(ffprobe, chapter.source_path)
        video_streams = [
            row
            for row in payload.get("streams", [])
            if isinstance(row, dict) and row.get("codec_type") == "video"
        ]
        if not video_streams:
            raise ShowcaseError(
                f"chapter[{chapter.index}] video source has no video stream: "
                f"{chapter.source_path}"
            )
        duration = _duration_from_probe(payload, chapter.source_path)
        chapter.source_duration_seconds = duration
        if chapter.start_seconds >= duration:
            raise ShowcaseError(
                f"chapter[{chapter.index}] start_seconds {chapter.start_seconds:.3f} "
                f"is outside {duration:.3f}s source: {chapter.source_path}"
            )
        if chapter.end_seconds is not None and chapter.end_seconds > duration + 0.05:
            raise ShowcaseError(
                f"chapter[{chapter.index}] end_seconds {chapter.end_seconds:.3f} "
                f"exceeds {duration:.3f}s source: {chapter.source_path}"
            )


def resolve_requested_voice(
    cli_voice: str | None, manifest: dict[str, Any]
) -> str:
    if cli_voice is not None and cli_voice.strip():
        return cli_voice.strip()
    raw_voice = manifest.get("voice", DEFAULT_EDGE_TTS_VOICE)
    if raw_voice is None:
        return DEFAULT_EDGE_TTS_VOICE
    if not isinstance(raw_voice, str):
        raise ShowcaseError("manifest 'voice' must be a string when present")
    return raw_voice.strip() or DEFAULT_EDGE_TTS_VOICE


def _cached_edge_tts_metadata(
    media_path: Path,
    metadata_path: Path,
    *,
    fingerprint: str,
) -> dict[str, Any] | None:
    if not media_path.is_file() or not metadata_path.is_file():
        return None
    try:
        candidate = _load_json(metadata_path, "cached Edge TTS metadata")
    except ShowcaseError:
        return None
    if (
        isinstance(candidate, dict)
        and candidate.get("fingerprint") == fingerprint
        and candidate.get("media_sha256") == _sha256(media_path)
        and candidate.get("provider") == EDGE_TTS_PROVIDER
        and isinstance(candidate.get("provider_version"), str)
        and isinstance(candidate.get("voice"), str)
        and isinstance(candidate.get("settings"), dict)
    ):
        return candidate
    return None


def _narration_duration(payload: dict[str, Any], path: Path) -> float:
    audio_streams = [
        row
        for row in payload.get("streams", [])
        if isinstance(row, dict) and row.get("codec_type") == "audio"
    ]
    if not audio_streams:
        raise ShowcaseError(f"narration media has no audio stream: {path}")
    codec = audio_streams[0].get("codec_name")
    if codec != "mp3":
        raise ShowcaseError(
            f"narration media codec is {codec!r}, expected 'mp3': {path}"
        )
    return _duration_from_probe(payload, path)


def _commit_edge_tts_cache(
    temporary_media: Path,
    media_path: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
) -> None:
    staged_metadata = metadata_path.with_name(
        f".{metadata_path.name}.{os.getpid()}.staged"
    )
    rollback_media = media_path.with_name(
        f".{media_path.name}.{os.getpid()}.rollback"
    )
    if staged_metadata.exists() or rollback_media.exists():
        raise ShowcaseError(
            "stale Edge TTS cache transaction file exists; remove it before retrying: "
            f"{staged_metadata if staged_metadata.exists() else rollback_media}"
        )

    _atomic_json(staged_metadata, metadata)
    old_media_saved = False
    new_media_installed = False
    committed = False
    try:
        if media_path.exists():
            os.replace(media_path, rollback_media)
            old_media_saved = True
        os.replace(temporary_media, media_path)
        new_media_installed = True
        os.replace(staged_metadata, metadata_path)
        committed = True
    except BaseException:
        if old_media_saved and rollback_media.exists():
            os.replace(rollback_media, media_path)
        elif new_media_installed and media_path.exists():
            media_path.unlink()
        raise
    finally:
        if staged_metadata.exists():
            try:
                staged_metadata.unlink()
            except OSError:
                pass
        if committed and rollback_media.exists():
            try:
                rollback_media.unlink()
            except OSError:
                pass


def synthesize_narration(
    chapter: Chapter,
    chapter_directory: Path,
    *,
    requested_voice: str,
    ffprobe: Path,
    force: bool,
) -> None:
    text_path = chapter_directory / "narration.en.txt"
    media_path = chapter_directory / "narration.en.mp3"
    metadata_path = chapter_directory / "narration.edge-tts.json"
    text_path.write_text(chapter.narration_en + "\n", encoding="utf-8")
    settings = {
        "rate": EDGE_TTS_RATE,
        "volume": EDGE_TTS_VOLUME,
        "pitch": EDGE_TTS_PITCH,
    }
    provider_version = EDGE_TTS_VERSION or "unknown"
    fingerprint = _json_fingerprint(
        {
            "format": 1,
            "provider": EDGE_TTS_PROVIDER,
            "provider_version": provider_version,
            "narration_en": chapter.narration_en,
            "requested_voice": requested_voice,
            "settings": settings,
        }
    )

    metadata: dict[str, Any] | None = None
    duration: float | None = None
    if not force:
        metadata = _cached_edge_tts_metadata(
            media_path,
            metadata_path,
            fingerprint=fingerprint,
        )
        if metadata is not None:
            try:
                duration = _narration_duration(
                    probe_media(ffprobe, media_path), media_path
                )
            except ShowcaseError:
                metadata = None

    if metadata is None:
        temporary = chapter_directory / (
            f".narration.en.{os.getpid()}.partial.mp3"
        )
        if temporary.exists():
            temporary.unlink()
        try:
            if edge_tts is None:
                raise ShowcaseError(
                    "edge-tts is required for narration synthesis; install "
                    "tools\\requirements.txt"
                )
            provider = EdgeTtsProvider(
                module=edge_tts,
                tool_version=provider_version,
            )
            provider.synthesize(
                TtsRequest(
                    text=chapter.narration_en,
                    voice=requested_voice,
                    rate=EDGE_TTS_RATE,
                    volume=EDGE_TTS_VOLUME,
                    pitch=EDGE_TTS_PITCH,
                ),
                temporary,
            )
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise ShowcaseError(
                    "Edge TTS did not create narration MP3 for chapter "
                    f"'{chapter.chapter_id}'"
                )
            duration = _narration_duration(
                probe_media(ffprobe, temporary), temporary
            )
            metadata = {
                "format_version": 1,
                "fingerprint": fingerprint,
                "provider": EDGE_TTS_PROVIDER,
                "provider_version": provider_version,
                "voice": requested_voice,
                "settings": settings,
                "media_sha256": _sha256(temporary),
            }
            _commit_edge_tts_cache(
                temporary,
                media_path,
                metadata_path,
                metadata,
            )
        except ShowcaseError:
            raise
        except Exception as exc:
            raise ShowcaseError(
                "Edge TTS narration synthesis failed for chapter "
                f"'{chapter.chapter_id}' with voice '{requested_voice}': {exc}"
            ) from exc
        finally:
            if temporary.exists():
                temporary.unlink()

    if duration is None:
        duration = _narration_duration(probe_media(ffprobe, media_path), media_path)
    chapter.narration_path = media_path
    chapter.narration_duration_seconds = duration
    chapter.voice = str(metadata["voice"])
    chapter.tts_provider = str(metadata["provider"])
    chapter.tts_provider_version = str(metadata["provider_version"])
    chapter.tts_settings = dict(metadata["settings"])
    chapter.shot_duration_seconds = max(
        chapter.min_duration_seconds, duration + chapter.tail_padding_seconds
    )


def _base_background():
    gradient = Image.linear_gradient("L").resize((WIDTH, HEIGHT))
    dark = Image.new("RGB", (WIDTH, HEIGHT), (10, 14, 25))
    blue = Image.new("RGB", (WIDTH, HEIGHT), (25, 39, 64))
    image = Image.composite(blue, dark, gradient)
    vignette = Image.new("L", (WIDTH, HEIGHT), 255)
    vignette_draw = ImageDraw.Draw(vignette)
    for inset in range(0, 240, 12):
        alpha = int(255 * (inset / 240) ** 1.7)
        vignette_draw.rounded_rectangle(
            (inset, inset, WIDTH - inset, HEIGHT - inset),
            radius=80,
            outline=alpha,
            width=14,
        )
    black = Image.new("RGB", (WIDTH, HEIGHT), (5, 7, 12))
    return Image.composite(image, black, vignette)


def _break_long_token(draw, token: str, font, max_width: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for char in token:
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            pieces.append(current)
            current = char
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces or [token]


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        if re.search(r"\s", paragraph):
            tokens = re.findall(r"\S+", paragraph)
            current = ""
            for token in tokens:
                candidates = (
                    _break_long_token(draw, token, font, max_width)
                    if draw.textlength(token, font=font) > max_width
                    else [token]
                )
                for piece in candidates:
                    candidate = piece if not current else f"{current} {piece}"
                    if current and draw.textlength(candidate, font=font) > max_width:
                        lines.append(current)
                        current = piece
                    else:
                        current = candidate
            if current:
                lines.append(current)
        else:
            current = ""
            for char in paragraph:
                candidate = current + char
                if current and draw.textlength(candidate, font=font) > max_width:
                    lines.append(current)
                    current = char
                else:
                    current = candidate
            if current:
                lines.append(current)
    return lines


def draw_text_block(
    draw,
    xy: tuple[int, int],
    text: str,
    *,
    font,
    fill: tuple[int, ...],
    max_width: int,
    line_height: int,
    max_lines: int | None = None,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1].rstrip()
        while last and draw.textlength(last + "…", font=font) > max_width:
            last = last[:-1]
        lines[-1] = last + "…"
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _classification_color(classification: str) -> tuple[int, int, int]:
    value = classification.lower()
    if "complete" in value:
        return (218, 170, 74)
    if "production-live loop" in value or "production_live_loop" in value:
        return (38, 201, 180)
    if "production-live" in value or "production_live" in value:
        return (60, 187, 111)
    if "fixture-live" in value or "fixture_live" in value:
        return (224, 157, 56)
    if "static" in value:
        return (76, 151, 232)
    if "research" in value:
        return (157, 108, 224)
    if "historical" in value:
        return (130, 145, 170)
    if "red" in value or "failed" in value:
        return (218, 78, 82)
    return (80, 145, 210)


def draw_status_badge(image, chapter: Chapter, fonts: Fonts) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    en_font = fonts.english(25, bold=True)
    zh_font = fonts.chinese(21, bold=True)
    en_box = draw.textbbox((0, 0), chapter.status_en, font=en_font)
    zh_box = draw.textbbox((0, 0), chapter.status_zh, font=zh_font)
    text_width = max(en_box[2] - en_box[0], zh_box[2] - zh_box[0])
    badge_width = max(330, text_width + 92)
    badge_height = 92
    right = WIDTH - 72
    bottom = HEIGHT - 48
    left = right - badge_width
    top = bottom - badge_height
    color = _classification_color(chapter.classification)
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=24,
        fill=(10, 14, 24, 224),
        outline=(*color, 255),
        width=4,
    )
    draw.rounded_rectangle(
        (left + 17, top + 17, left + 31, bottom - 17),
        radius=7,
        fill=(*color, 255),
    )
    draw.text((left + 52, top + 12), chapter.status_en, font=en_font, fill=(246, 248, 252, 255))
    draw.text((left + 52, top + 51), chapter.status_zh, font=zh_font, fill=(185, 207, 235, 255))


def draw_chapter_overlay(chapter: Chapter, fonts: Fonts):
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    color = _classification_color(chapter.classification)
    panel = (66, 70, 1580, 270)
    draw.rounded_rectangle(panel, radius=30, fill=(8, 12, 22, 202))
    draw.rounded_rectangle((66, 70, 82, 270), radius=8, fill=(*color, 255))
    kicker = f"CHAPTER {chapter.index + 1:02d}  /  {chapter.kind.replace('_', ' ').upper()}"
    draw.text((112, 92), kicker, font=fonts.english(23, bold=True), fill=(*color, 255))
    draw_text_block(
        draw,
        (112, 132),
        chapter.title_en,
        font=fonts.english(46, bold=True),
        fill=(250, 251, 254, 255),
        max_width=1395,
        line_height=55,
        max_lines=1,
    )
    draw_text_block(
        draw,
        (114, 196),
        chapter.title_zh,
        font=fonts.chinese(29, bold=False),
        fill=(180, 207, 240, 255),
        max_width=1390,
        line_height=38,
        max_lines=1,
    )
    draw_status_badge(overlay, chapter, fonts)
    return overlay


def _fit_image(source, *, mode: str):
    source = ImageOps.exif_transpose(source).convert("RGB")
    if mode == "cover":
        return ImageOps.fit(source, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    contained = ImageOps.contain(source, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    background = Image.new("RGB", (WIDTH, HEIGHT), (6, 9, 16))
    x = (WIDTH - contained.width) // 2
    y = (HEIGHT - contained.height) // 2
    background.paste(contained, (x, y))
    return background


def render_title_card(chapter: Chapter, fonts: Fonts, destination: Path) -> None:
    image = _base_background().convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    accent = _classification_color(chapter.classification)
    draw.text(
        (176, 106),
        "XAR  /  CK3 AUTONOMOUS AGENT",
        font=fonts.english(27, bold=True),
        fill=(*accent, 255),
    )
    draw.rounded_rectangle((176, 168, WIDTH - 176, 180), radius=6, fill=(*accent, 255))
    title_bottom = draw_text_block(
        draw,
        (176, 242),
        chapter.title_en,
        font=fonts.english(78, bold=True),
        fill=(250, 251, 254, 255),
        max_width=WIDTH - 352,
        line_height=92,
        max_lines=3,
    )
    chinese_bottom = draw_text_block(
        draw,
        (180, title_bottom + 24),
        chapter.title_zh,
        font=fonts.chinese(43, bold=False),
        fill=(186, 210, 239, 255),
        max_width=WIDTH - 360,
        line_height=57,
        max_lines=2,
    )
    if chapter.body_en or chapter.body_zh:
        panel_top = max(chinese_bottom + 54, 680)
        panel_bottom = HEIGHT - 200
        draw.rounded_rectangle(
            (176, panel_top, WIDTH - 176, panel_bottom),
            radius=28,
            fill=(8, 12, 22, 150),
            outline=(77, 94, 125, 170),
            width=2,
        )
        middle = WIDTH // 2
        draw.line((middle, panel_top + 35, middle, panel_bottom - 35), fill=(72, 88, 116, 180), width=2)
        en_y = panel_top + 42
        for line in chapter.body_en:
            en_y = draw_text_block(
                draw,
                (224, en_y),
                f"• {line}",
                font=fonts.english(31, bold=True),
                fill=(230, 235, 245, 255),
                max_width=middle - 300,
                line_height=43,
                max_lines=3,
            ) + 16
        zh_y = panel_top + 42
        for line in chapter.body_zh:
            zh_y = draw_text_block(
                draw,
                (middle + 52, zh_y),
                f"• {line}",
                font=fonts.chinese(29),
                fill=(181, 204, 235, 255),
                max_width=middle - 300,
                line_height=43,
                max_lines=3,
            ) + 16
    draw_status_badge(image, chapter, fonts)
    image.convert("RGB").save(destination, format="PNG", optimize=True)


def render_still(chapter: Chapter, fonts: Fonts, destination: Path) -> None:
    if chapter.source_path is None:
        raise ShowcaseError(f"chapter '{chapter.chapter_id}' has no still source")
    try:
        with Image.open(chapter.source_path) as source:
            image = _fit_image(source, mode=chapter.fit).convert("RGBA")
    except (OSError, ValueError) as exc:
        raise ShowcaseError(
            f"could not decode still image for chapter '{chapter.chapter_id}': "
            f"{chapter.source_path}: {exc}"
        ) from exc
    shading = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shading, "RGBA")
    shade_draw.rectangle((0, 0, WIDTH, 330), fill=(4, 7, 14, 52))
    shade_draw.rectangle((0, HEIGHT - 230, WIDTH, HEIGHT), fill=(4, 7, 14, 35))
    image.alpha_composite(shading)
    image.alpha_composite(draw_chapter_overlay(chapter, fonts))
    image.convert("RGB").save(destination, format="PNG", optimize=True)


def render_evidence_card(chapter: Chapter, fonts: Fonts, destination: Path) -> None:
    image = _base_background().convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    accent = _classification_color(chapter.classification)
    draw.text(
        (150, 86),
        f"EVIDENCE  /  CHAPTER {chapter.index + 1:02d}",
        font=fonts.english(25, bold=True),
        fill=(*accent, 255),
    )
    draw.rounded_rectangle((150, 140, WIDTH - 150, 151), radius=5, fill=(*accent, 255))
    title_bottom = draw_text_block(
        draw,
        (150, 205),
        chapter.title_en,
        font=fonts.english(63, bold=True),
        fill=(250, 251, 254, 255),
        max_width=WIDTH - 300,
        line_height=74,
        max_lines=2,
    )
    draw_text_block(
        draw,
        (154, title_bottom + 14),
        chapter.title_zh,
        font=fonts.chinese(36),
        fill=(181, 207, 239, 255),
        max_width=WIDTH - 308,
        line_height=48,
        max_lines=2,
    )
    panel_top = 500
    panel_bottom = 1160
    middle = WIDTH // 2
    draw.rounded_rectangle(
        (150, panel_top, WIDTH - 150, panel_bottom),
        radius=30,
        fill=(7, 11, 20, 172),
        outline=(70, 87, 116, 210),
        width=2,
    )
    draw.line((middle, panel_top + 42, middle, panel_bottom - 42), fill=(70, 87, 116, 210), width=2)
    en_lines = chapter.body_en or ["Evidence source is hashed in the video sidecar."]
    zh_lines = chapter.body_zh or ["证据来源及其哈希记录在视频 sidecar 中。"]
    en_y = panel_top + 50
    for line in en_lines:
        en_y = draw_text_block(
            draw,
            (205, en_y),
            f"• {line}",
            font=fonts.english(30, bold=True),
            fill=(231, 236, 246, 255),
            max_width=middle - 285,
            line_height=42,
            max_lines=3,
        ) + 20
    zh_y = panel_top + 50
    for line in zh_lines:
        zh_y = draw_text_block(
            draw,
            (middle + 55, zh_y),
            f"• {line}",
            font=fonts.chinese(28),
            fill=(184, 207, 236, 255),
            max_width=middle - 285,
            line_height=42,
            max_lines=3,
        ) + 20

    source_y = panel_bottom - 150
    for source in chapter.sources[:2]:
        sha_line = f"{source.label}: {source.path.name}  /  SHA-256 {source.sha256[:16]}…"
        draw_text_block(
            draw,
            (205, source_y),
            sha_line,
            font=fonts.english(20),
            fill=(139, 157, 186, 255),
            max_width=WIDTH - 410,
            line_height=27,
            max_lines=1,
        )
        source_y += 37
    if len(chapter.sources) > 2:
        draw.text(
            (205, source_y),
            f"+ {len(chapter.sources) - 2} additional hashed source(s) in sidecar",
            font=fonts.english(20),
            fill=(139, 157, 186, 255),
        )
    draw_status_badge(image, chapter, fonts)
    image.convert("RGB").save(destination, format="PNG", optimize=True)


def render_visual(chapter: Chapter, fonts: Fonts, chapter_directory: Path) -> tuple[Path, bool]:
    if chapter.kind == "video_clip":
        destination = chapter_directory / "overlay.png"
        draw_chapter_overlay(chapter, fonts).save(destination, format="PNG", optimize=True)
        return destination, True
    destination = chapter_directory / "frame.png"
    if chapter.kind == "title_card":
        render_title_card(chapter, fonts, destination)
    elif chapter.kind == "still":
        render_still(chapter, fonts, destination)
    elif chapter.kind == "evidence_card":
        render_evidence_card(chapter, fonts, destination)
    else:  # manifest validation should make this unreachable
        raise ShowcaseError(f"unsupported chapter type: {chapter.kind}")
    return destination, False


def _ass_timestamp(seconds: float) -> str:
    return compatible_ass_timestamp(seconds)


def _ass_escape(text: str) -> str:
    return compatible_ass_escape(text)


def _subtitle_width(draw, text: str, font) -> float:
    return float(draw.textlength(text, font=font))


def _subtitle_clauses(paragraph: str) -> list[tuple[str, bool]]:
    """Split at semantic punctuation and mark sentence-level hard breaks.

    Punctuation stays with the clause it closes.  A full stop between two digits
    is treated as part of a version/decimal number rather than a sentence break.
    """

    clauses: list[tuple[str, bool]] = []
    current: list[str] = []
    for index, char in enumerate(paragraph):
        current.append(char)
        hard_break = char in SUBTITLE_MAJOR_BREAKS
        if char == ".":
            previous_is_digit = index > 0 and paragraph[index - 1].isdigit()
            next_is_digit = index + 1 < len(paragraph) and paragraph[index + 1].isdigit()
            hard_break = not (previous_is_digit and next_is_digit)
        if hard_break or char in SUBTITLE_MINOR_BREAKS:
            clauses.append(("".join(current), hard_break))
            current = []
    if current:
        clauses.append(("".join(current), False))
    return clauses


def _longest_fitting_prefix(draw, text: str, font, max_width: int) -> int:
    low = 1
    high = len(text)
    best = 0
    while low <= high:
        middle = (low + high) // 2
        if _subtitle_width(draw, text[:middle].rstrip(), font) <= max_width:
            best = middle
            low = middle + 1
        else:
            high = middle - 1
    return best


def _split_long_subtitle_clause(draw, clause: str, font, max_width: int) -> list[str]:
    """Fit an overlong clause, preferring punctuation and word boundaries."""

    pieces: list[str] = []
    remainder = clause.strip()
    natural_breaks = SUBTITLE_MAJOR_BREAKS | SUBTITLE_MINOR_BREAKS
    while remainder:
        if _subtitle_width(draw, remainder, font) <= max_width:
            pieces.append(remainder)
            break
        fitting = _longest_fitting_prefix(draw, remainder, font, max_width)
        if fitting <= 0:
            raise ShowcaseError(
                "subtitle font metrics could not fit even one character inside "
                f"the {max_width}px safe width"
            )

        # Select the latest natural boundary in the latter half of the fitting
        # prefix.  Major punctuation wins over commas/spaces when both are near.
        floor = max(1, fitting // 2)
        major = [
            index
            for index in range(floor, fitting + 1)
            if remainder[index - 1] in SUBTITLE_MAJOR_BREAKS
            or (
                remainder[index - 1] == "."
                and not (
                    index >= 2
                    and index < len(remainder)
                    and remainder[index - 2].isdigit()
                    and remainder[index].isdigit()
                )
            )
        ]
        minor = [
            index
            for index in range(floor, fitting + 1)
            if remainder[index - 1].isspace()
            or remainder[index - 1] in natural_breaks
        ]
        split_at = (major or minor or [fitting])[-1]

        # Do not cut an ASCII word when a nearby word boundary is available.
        if (
            split_at == fitting
            and split_at < len(remainder)
            and remainder[split_at - 1].isascii()
            and remainder[split_at - 1].isalnum()
            and remainder[split_at].isascii()
            and remainder[split_at].isalnum()
        ):
            word_breaks = [
                index
                for index in range(floor, fitting + 1)
                if remainder[index - 1].isspace()
            ]
            if word_breaks:
                split_at = word_breaks[-1]

        piece = remainder[:split_at].strip()
        if not piece:
            split_at = fitting
            piece = remainder[:split_at].strip()
        pieces.append(piece)
        remainder = remainder[split_at:].lstrip()
    return pieces


def layout_subtitle(text: str, font) -> tuple[list[str], list[float]]:
    """Wrap Chinese subtitles by meaning first and measured pixels second."""

    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines: list[str] = []
    for raw_paragraph in text.splitlines() or [text]:
        paragraph = raw_paragraph.strip()
        if not paragraph:
            continue
        current = ""
        for clause, hard_break in _subtitle_clauses(paragraph):
            candidate = (current + clause).strip()
            if current and _subtitle_width(draw, candidate, font) > SUBTITLE_MAX_TEXT_WIDTH:
                lines.append(current.strip())
                current = ""

            if not current and _subtitle_width(draw, clause.strip(), font) > SUBTITLE_MAX_TEXT_WIDTH:
                fragments = _split_long_subtitle_clause(
                    draw, clause, font, SUBTITLE_MAX_TEXT_WIDTH
                )
                lines.extend(fragments[:-1])
                current = fragments[-1]
            else:
                current = (current + clause).strip()

            if hard_break and current:
                lines.append(current)
                current = ""
        if current:
            lines.append(current)

    if not lines:
        raise ShowcaseError("subtitle text produced no renderable lines")
    widths = [_subtitle_width(draw, line, font) for line in lines]
    overflowing = [width for width in widths if width > SUBTITLE_MAX_TEXT_WIDTH + 0.01]
    if overflowing:
        raise ShowcaseError(
            "subtitle layout exceeded its measured safe width: "
            f"max={max(overflowing):.1f}px limit={SUBTITLE_MAX_TEXT_WIDTH}px"
        )
    if len(lines) > SUBTITLE_MAX_TOTAL_LINES:
        raise ShowcaseError(
            f"subtitle requires {len(lines)} lines; limit is {SUBTITLE_MAX_TOTAL_LINES}. "
            "Shorten the translation or split the chapter."
        )
    return lines, widths


def _balanced_subtitle_blocks(lines: Sequence[str]) -> list[list[str]]:
    try:
        return [
            list(block)
            for block in balance_lines(
                lines,
                max_lines_per_block=SUBTITLE_MAX_LINES_PER_CUE,
            )
        ]
    except LayoutError as exc:
        raise ShowcaseError("internal error: invalid subtitle cue partition") from exc


def prepare_subtitle_layouts(chapters: Sequence[Chapter], fonts: Fonts) -> None:
    font = fonts.chinese(SUBTITLE_FONT_SIZE, bold=True)
    for chapter in chapters:
        lines, widths = layout_subtitle(chapter.subtitle_zh, font)
        chapter.subtitle_lines = lines
        chapter.subtitle_line_widths = widths
        chapter.subtitle_cue_blocks = _balanced_subtitle_blocks(lines)


def _ass_document(cues: Sequence[tuple[float, float, str]]) -> str:
    header = f"""[Script Info]
Title: XAR CK3 Autonomous Agent - Simplified Chinese subtitles
ScriptType: v4.00+
PlayResX: 2560
PlayResY: 1440
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chinese,{SUBTITLE_FONT_NAME},{SUBTITLE_FONT_SIZE},&H00FFFFFF,&H000000FF,&H00101018,&H78081018,-1,0,0,0,100,100,0,0,1,3,1,2,{SUBTITLE_MARGIN_HORIZONTAL},{SUBTITLE_MARGIN_HORIZONTAL},{SUBTITLE_MARGIN_VERTICAL},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = [
        f"Dialogue: 0,{_ass_timestamp(start)},{_ass_timestamp(end)},Chinese,,0,0,0,,{{\\q2}}{_ass_escape(text)}"
        for start, end, text in cues
    ]
    return header + "\n".join(events) + "\n"


def _chapter_subtitle_cues(
    chapter: Chapter, *, timeline_offset: float = 0.0
) -> list[tuple[float, float, str]]:
    if chapter.shot_duration_seconds is None or chapter.narration_duration_seconds is None:
        raise ShowcaseError("internal error: chapter duration is not ready")
    if not chapter.subtitle_cue_blocks:
        raise ShowcaseError("internal error: subtitle cue layout is not ready")
    local_start = min(0.20, chapter.shot_duration_seconds / 10)
    local_end = min(
        chapter.shot_duration_seconds - 0.10,
        chapter.narration_duration_seconds + 0.25,
    )
    local_end = max(local_end, local_start + 0.20)
    weights = [
        max(1, sum(len(line.replace(" ", "")) for line in block))
        for block in chapter.subtitle_cue_blocks
    ]
    total_weight = sum(weights)
    duration = local_end - local_start
    cues: list[tuple[float, float, str]] = []
    cursor = local_start
    consumed_weight = 0
    for index, (block, weight) in enumerate(zip(chapter.subtitle_cue_blocks, weights)):
        consumed_weight += weight
        block_end = (
            local_end
            if index == len(weights) - 1
            else local_start + duration * consumed_weight / total_weight
        )
        cues.append(
            (
                timeline_offset + cursor,
                timeline_offset + block_end,
                "\n".join(block),
            )
        )
        cursor = block_end
    return cues


def write_chapter_ass(chapter: Chapter, destination: Path) -> None:
    destination.write_text(
        _ass_document(_chapter_subtitle_cues(chapter)),
        encoding="utf-8-sig",
    )


def write_global_ass(chapters: Sequence[Chapter], destination: Path) -> None:
    cues: list[tuple[float, float, str]] = []
    cursor = 0.0
    for chapter in chapters:
        if chapter.shot_duration_seconds is None or chapter.narration_duration_seconds is None:
            raise ShowcaseError("internal error: chapter duration is not ready")
        cues.extend(_chapter_subtitle_cues(chapter, timeline_offset=cursor))
        cursor += chapter.encoded_duration_seconds or chapter.shot_duration_seconds
    destination.write_text(_ass_document(cues), encoding="utf-8-sig")


def _seconds(value: float) -> str:
    return compatible_seconds(value)


def encode_segment(
    chapter: Chapter,
    chapter_directory: Path,
    *,
    fonts: Fonts,
    ffmpeg: Path,
    ffprobe: Path,
    fps: int,
    crf: int,
    preset: str,
    force: bool,
) -> None:
    if chapter.narration_path is None or chapter.shot_duration_seconds is None:
        raise ShowcaseError("internal error: narration was not prepared")
    visual_path, is_video = render_visual(chapter, fonts, chapter_directory)
    ass_path = chapter_directory / "chapter.zh-CN.ass"
    write_chapter_ass(chapter, ass_path)
    segment = chapter_directory / "segment.mp4"
    metadata_path = chapter_directory / "segment.build.json"

    fingerprint_payload = {
        "build_format": BUILD_FORMAT_VERSION,
        "chapter": chapter.raw,
        "classification": chapter.classification,
        "sources": [row.sidecar() for row in chapter.sources],
        "narration_sha256": _sha256(chapter.narration_path),
        "narration_duration_seconds": chapter.narration_duration_seconds,
        "shot_duration_seconds": chapter.shot_duration_seconds,
        "visual_sha256": _sha256(visual_path),
        "ass_sha256": _sha256(ass_path),
        "width": WIDTH,
        "height": HEIGHT,
        "fps": fps,
        "crf": crf,
        "preset": preset,
    }
    fingerprint = _json_fingerprint(fingerprint_payload)
    if not force and segment.is_file() and metadata_path.is_file():
        cached = _load_json(metadata_path, "cached segment metadata")
        if isinstance(cached, dict) and cached.get("fingerprint") == fingerprint:
            try:
                cached_info = validate_encoded_media(
                    probe_media(ffprobe, segment),
                    segment,
                    expected_duration=chapter.shot_duration_seconds,
                    duration_tolerance=0.20,
                )
            except ShowcaseError:
                pass
            else:
                chapter.segment_path = segment
                chapter.encoded_duration_seconds = float(cached_info["duration"])
                print(f"[{chapter.index + 1:02d}] reuse {chapter.chapter_id}: {segment}")
                return

    common_tail = [
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-t",
        _seconds(chapter.shot_duration_seconds),
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-profile:v",
        "high",
        "-level:v",
        "5.1",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-metadata:s:a:0",
        "language=eng",
        "-movflags",
        "+faststart",
        segment,
    ]
    audio_filter = (
        f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"apad,atrim=duration={_seconds(chapter.shot_duration_seconds)},"
        "asetpts=N/SR/TB"
    )
    if is_video:
        if chapter.source_path is None or chapter.source_duration_seconds is None:
            raise ShowcaseError("internal error: video source was not probed")
        available_end = chapter.end_seconds or chapter.source_duration_seconds
        available = available_end - chapter.start_seconds
        video_filter = (
            f"[0:v]trim=duration={_seconds(available)},setpts=PTS-STARTPTS,"
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x060910,setsar=1,"
            f"fps={fps},tpad=stop_mode=clone:stop_duration={_seconds(chapter.shot_duration_seconds)},"
            f"trim=duration={_seconds(chapter.shot_duration_seconds)}[base];"
            "[1:v]format=rgba[overlay];"
            "[base][overlay]overlay=0:0:shortest=1,ass=chapter.zh-CN.ass,format=yuv420p[v];"
            f"[2:a]{audio_filter}[a]"
        )
        command: list[str | Path] = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            _seconds(chapter.start_seconds),
            "-i",
            chapter.source_path,
            "-loop",
            "1",
            "-framerate",
            str(fps),
            "-i",
            visual_path.name,
            "-i",
            chapter.narration_path,
            "-filter_complex",
            video_filter,
            *common_tail,
        ]
    else:
        video_filter = (
            f"[0:v]trim=duration={_seconds(chapter.shot_duration_seconds)},"
            f"setpts=PTS-STARTPTS,fps={fps},ass=chapter.zh-CN.ass,format=yuv420p[v];"
            f"[1:a]{audio_filter}[a]"
        )
        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(fps),
            "-i",
            visual_path.name,
            "-i",
            chapter.narration_path,
            "-filter_complex",
            video_filter,
            *common_tail,
        ]
    print(
        f"[{chapter.index + 1:02d}] encode {chapter.chapter_id}: "
        f"{chapter.shot_duration_seconds:.2f}s"
    )
    run_checked(command, cwd=chapter_directory, action=f"encoding chapter '{chapter.chapter_id}'")
    encoded_info = validate_encoded_media(
        probe_media(ffprobe, segment),
        segment,
        expected_duration=chapter.shot_duration_seconds,
        duration_tolerance=0.20,
    )
    chapter.encoded_duration_seconds = float(encoded_info["duration"])
    _atomic_json(
        metadata_path,
        {
            "format_version": 1,
            "fingerprint": fingerprint,
            "segment": str(segment),
            "segment_sha256": _sha256(segment),
        },
    )
    chapter.segment_path = segment


def validate_encoded_media(
    payload: dict[str, Any],
    path: Path,
    *,
    expected_duration: float | None = None,
    duration_tolerance: float = 0.35,
) -> dict[str, Any]:
    streams = [row for row in payload.get("streams", []) if isinstance(row, dict)]
    video = next((row for row in streams if row.get("codec_type") == "video"), None)
    audio = next((row for row in streams if row.get("codec_type") == "audio"), None)
    if video is None or audio is None:
        raise ShowcaseError(f"encoded media is missing video or audio: {path}")
    problems: list[str] = []
    if video.get("codec_name") != "h264":
        problems.append(f"video codec={video.get('codec_name')!r}, expected h264")
    if video.get("pix_fmt") != "yuv420p":
        problems.append(f"pixel format={video.get('pix_fmt')!r}, expected yuv420p")
    if video.get("width") != WIDTH or video.get("height") != HEIGHT:
        problems.append(
            f"geometry={video.get('width')}x{video.get('height')}, expected {WIDTH}x{HEIGHT}"
        )
    if audio.get("codec_name") != "aac":
        problems.append(f"audio codec={audio.get('codec_name')!r}, expected aac")
    if str(audio.get("sample_rate")) != "48000":
        problems.append(f"audio sample_rate={audio.get('sample_rate')!r}, expected 48000")
    if audio.get("channels") != 2:
        problems.append(f"audio channels={audio.get('channels')!r}, expected 2")
    duration = _duration_from_probe(payload, path)
    if expected_duration is not None and abs(duration - expected_duration) > duration_tolerance:
        problems.append(
            f"duration={duration:.3f}s, expected {expected_duration:.3f}s "
            f"(+/- {duration_tolerance:.3f}s)"
        )
    if problems:
        raise ShowcaseError(f"encoded media validation failed for {path}: " + "; ".join(problems))
    return {"video": video, "audio": audio, "duration": duration}


def concat_segments(
    chapters: Sequence[Chapter],
    *,
    build_directory: Path,
    output: Path,
    ffmpeg: Path,
    ffprobe: Path,
) -> dict[str, Any]:
    concat_path = build_directory / "concat.txt"
    segment_paths: list[Path] = []
    for chapter in chapters:
        if chapter.segment_path is None:
            raise ShowcaseError("internal error: segment was not encoded")
        segment_paths.append(chapter.segment_path)
    try:
        concat_text = compatible_concat_manifest(
            segment_paths,
            build_directory=build_directory,
        )
    except LegacyCompatibilityError as exc:
        raise ShowcaseError(f"internal {exc}") from exc
    concat_path.write_text(concat_text, encoding="utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.{os.getpid()}.partial.mp4")
    if temporary.exists():
        temporary.unlink()
    run_checked(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_path.name,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            temporary,
        ],
        cwd=build_directory,
        action="concatenating showcase chapters",
    )
    payload = probe_media(ffprobe, temporary)
    expected_duration = sum(
        row.encoded_duration_seconds or row.shot_duration_seconds or 0.0
        for row in chapters
    )
    info = validate_encoded_media(
        payload,
        temporary,
        expected_duration=expected_duration,
        duration_tolerance=max(0.40, len(chapters) * 0.08),
    )
    os.replace(temporary, output)
    return info


def _frame_rate(stream: dict[str, Any]) -> float | None:
    for key in ("avg_frame_rate", "r_frame_rate"):
        value = stream.get(key)
        if not isinstance(value, str) or "/" not in value:
            continue
        numerator, denominator = value.split("/", 1)
        try:
            denominator_value = float(denominator)
            if denominator_value:
                return float(numerator) / denominator_value
        except ValueError:
            continue
    return None


def write_sidecar(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    chapters: Sequence[Chapter],
    output: Path,
    output_info: dict[str, Any],
    global_ass: Path,
    ffmpeg: Path,
    ffprobe: Path,
) -> Path:
    cursor = 0.0
    chapter_rows: list[dict[str, Any]] = []
    for chapter in chapters:
        duration = chapter.encoded_duration_seconds or chapter.shot_duration_seconds or 0.0
        chapter_rows.append(
            {
                "index": chapter.index,
                "id": chapter.chapter_id,
                "type": chapter.kind,
                "title_en": chapter.title_en,
                "title_zh": chapter.title_zh,
                "start_seconds": round(cursor, 3),
                "end_seconds": round(cursor + duration, 3),
                "duration_seconds": round(duration, 3),
                "narration_duration_seconds": round(
                    chapter.narration_duration_seconds or 0.0, 3
                ),
                "voice": chapter.voice,
                "classification": chapter.classification,
                "status": {"en": chapter.status_en, "zh": chapter.status_zh},
                "source_clip": (
                    {
                        "start_seconds": chapter.start_seconds,
                        "end_seconds": chapter.end_seconds,
                        "source_duration_seconds": chapter.source_duration_seconds,
                    }
                    if chapter.kind == "video_clip"
                    else None
                ),
                "sources": [
                    {**source.sidecar(), "classification": chapter.classification}
                    for source in chapter.sources
                ],
                "narration": {
                    "provider": chapter.tts_provider,
                    "provider_version": chapter.tts_provider_version,
                    "voice": chapter.voice,
                    "settings": chapter.tts_settings,
                    "path": str(chapter.narration_path),
                    "sha256": _sha256(chapter.narration_path) if chapter.narration_path else None,
                    "text_sha256": hashlib.sha256(
                        chapter.narration_en.encode("utf-8")
                    ).hexdigest().upper(),
                },
                "subtitle_layout": {
                    "lines": chapter.subtitle_lines,
                    "cue_blocks": chapter.subtitle_cue_blocks,
                    "line_widths_px": [
                        round(width, 2) for width in (chapter.subtitle_line_widths or [])
                    ],
                    "max_text_width_px": SUBTITLE_MAX_TEXT_WIDTH,
                    "ass_margin_left_px": SUBTITLE_MARGIN_HORIZONTAL,
                    "ass_margin_right_px": SUBTITLE_MARGIN_HORIZONTAL,
                    "font": SUBTITLE_FONT_NAME,
                    "font_size": SUBTITLE_FONT_SIZE,
                    "max_lines_per_cue": SUBTITLE_MAX_LINES_PER_CUE,
                },
                "segment": {
                    "path": str(chapter.segment_path),
                    "sha256": _sha256(chapter.segment_path) if chapter.segment_path else None,
                },
            }
        )
        cursor += duration

    video = output_info["video"]
    audio = output_info["audio"]
    sidecar = {
        "format_version": 1,
        "kind": "ck3_autonomous_agent_full_showcase_video",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "manifest": {
            "path": str(manifest_path),
            "bytes": manifest_path.stat().st_size,
            "sha256": _sha256(manifest_path),
            "format_version": manifest.get("format_version"),
        },
        "language": {
            "primary": "English narration and visual hierarchy",
            "secondary": "Simplified Chinese in-frame titles and burned ASS subtitles",
        },
        "video": {
            "path": str(output),
            "bytes": output.stat().st_size,
            "sha256": _sha256(output),
            "duration_seconds": round(float(output_info["duration"]), 3),
            "width": video.get("width"),
            "height": video.get("height"),
            "frame_rate": _frame_rate(video),
            "codec": video.get("codec_name"),
            "pixel_format": video.get("pix_fmt"),
            "audio_codec": audio.get("codec_name"),
            "audio_sample_rate": int(audio.get("sample_rate", 0)),
            "audio_channels": audio.get("channels"),
        },
        "subtitles": {
            "kind": "Simplified Chinese ASS, burned into video",
            "path": str(global_ass),
            "bytes": global_ass.stat().st_size,
            "sha256": _sha256(global_ass),
            "layout_policy": "semantic punctuation first, measured pixel width second",
            "max_text_width_px": SUBTITLE_MAX_TEXT_WIDTH,
            "max_total_lines_per_chapter": SUBTITLE_MAX_TOTAL_LINES,
            "max_lines_per_cue": SUBTITLE_MAX_LINES_PER_CUE,
            "ass_margins_px": {
                "left": SUBTITLE_MARGIN_HORIZONTAL,
                "right": SUBTITLE_MARGIN_HORIZONTAL,
                "vertical": SUBTITLE_MARGIN_VERTICAL,
            },
        },
        "tools": {"ffmpeg": str(ffmpeg), "ffprobe": str(ffprobe)},
        "chapters": chapter_rows,
    }
    sidecar_path = output.with_suffix(".video.json")
    _atomic_json(sidecar_path, sidecar)
    return sidecar_path


def _positive_integer(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if result <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def _crf(value: str) -> int:
    result = _positive_integer(value)
    if result > 51:
        raise argparse.ArgumentTypeError("must be in the range 1..51")
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", required=True, type=Path, help="UTF-8 JSON showcase manifest")
    result.add_argument("--output", required=True, type=Path, help="destination .mp4")
    result.add_argument("--work-dir", required=True, type=Path, help="reusable build/cache directory")
    result.add_argument("--ffmpeg", help="explicit ffmpeg executable")
    result.add_argument("--ffprobe", help="explicit ffprobe executable")
    result.add_argument(
        "--voice",
        help=(
            "override the manifest Edge TTS voice short name "
            f"(default: {DEFAULT_EDGE_TTS_VOICE})"
        ),
    )
    result.add_argument("--fps", type=_positive_integer, default=DEFAULT_FPS)
    result.add_argument("--crf", type=_crf, default=DEFAULT_CRF)
    result.add_argument("--preset", default=DEFAULT_PRESET, help="libx264 preset")
    result.add_argument("--force", action="store_true", help="ignore cached narration and segments")
    result.add_argument(
        "--validate-only",
        action="store_true",
        help="validate dependencies, manifest, source hashes and clip ranges without writing or encoding",
    )
    return result


def build(args: argparse.Namespace) -> tuple[Path, Path]:
    if PIL_IMPORT_ERROR is not None:
        raise ShowcaseError(
            "Pillow is required. Use tools\\.venv\\Scripts\\python.exe or install "
            "tools\\requirements-static.txt"
        ) from PIL_IMPORT_ERROR
    if EDGE_TTS_IMPORT_ERROR is not None:
        raise ShowcaseError(
            "edge-tts is required. Use tools\\.venv\\Scripts\\python.exe or install "
            "tools\\requirements.txt"
        ) from EDGE_TTS_IMPORT_ERROR
    manifest_path = args.manifest.expanduser().resolve()
    output = args.output.expanduser().resolve()
    work_directory = args.work_dir.expanduser().resolve()
    if output.suffix.lower() != ".mp4":
        raise ShowcaseError(f"--output must use the .mp4 extension: {output}")

    # Material existence is checked before any build/output directory is created.
    manifest, chapters = load_manifest(manifest_path)
    ffmpeg = find_program(args.ffmpeg, "ffmpeg")
    ffprobe = find_program(args.ffprobe, "ffprobe", sibling_of=ffmpeg)
    fonts = find_fonts()
    preflight_video_sources(chapters, ffprobe)
    prepare_subtitle_layouts(chapters, fonts)
    requested_voice = resolve_requested_voice(args.voice, manifest)
    try:
        validate_legacy_pipeline_projection(
            tuple(
                LegacyPipelineSegment(
                    segment_id=chapter.chapter_id,
                    visual_kind={
                        "video_clip": "video",
                        "still": "still",
                        "title_card": "generated-card",
                        "evidence_card": "evidence-card",
                    }[chapter.kind],
                    source_path=chapter.source_path,
                    subtitle_tracks={"zh-CN": chapter.subtitle_zh},
                    duration_seconds=chapter.min_duration_seconds,
                    start_seconds=chapter.start_seconds,
                )
                for chapter in chapters
            ),
            work_directory=work_directory,
            ffmpeg=ffmpeg,
            width=WIDTH,
            height=HEIGHT,
            fps=args.fps,
            crf=args.crf,
            render_preset=args.preset,
        )
    except LegacyCompatibilityError as exc:
        raise ShowcaseError(f"generic pipeline compatibility validation failed: {exc}") from exc
    if args.validate_only:
        classifications = sorted({chapter.classification for chapter in chapters})
        print(
            f"VALID: {len(chapters)} chapters; "
            f"{sum(len(chapter.sources) for chapter in chapters)} source reference(s); "
            f"classifications={classifications}"
        )
        return output, output.with_suffix(".video.json")

    manifest_hash = _sha256(manifest_path)
    build_directory = work_directory / f"showcase-{manifest_hash[:16].lower()}"
    build_directory.mkdir(parents=True, exist_ok=True)

    for chapter in chapters:
        chapter_directory = build_directory / f"{chapter.index:03d}-{_safe_slug(chapter.chapter_id)}"
        chapter_directory.mkdir(parents=True, exist_ok=True)
        synthesize_narration(
            chapter,
            chapter_directory,
            requested_voice=requested_voice,
            ffprobe=ffprobe,
            force=args.force,
        )

    for chapter in chapters:
        chapter_directory = build_directory / f"{chapter.index:03d}-{_safe_slug(chapter.chapter_id)}"
        encode_segment(
            chapter,
            chapter_directory,
            fonts=fonts,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            fps=args.fps,
            crf=args.crf,
            preset=args.preset,
            force=args.force,
        )

    global_ass = build_directory / "showcase.zh-CN.ass"
    write_global_ass(chapters, global_ass)

    output_info = concat_segments(
        chapters,
        build_directory=build_directory,
        output=output,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    sidecar = write_sidecar(
        manifest_path=manifest_path,
        manifest=manifest,
        chapters=chapters,
        output=output,
        output_info=output_info,
        global_ass=global_ass,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    print(f"VIDEO:   {output}")
    print(f"SIDECAR: {sidecar}")
    return output, sidecar


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        build(args)
    except ShowcaseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
