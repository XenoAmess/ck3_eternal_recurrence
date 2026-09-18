#!/usr/bin/env python3
"""Build the exact 08:20 non-music previsualization for Project Causality.

This adapter validates the editorial timeline and claim ledger, materializes a
manifest for ``build_full_agent_showcase.py``, and optionally renders a local
review copy. It does not launch CK3, operate Suno, add music, or publish media.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence


TOOLS_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = TOOLS_DIRECTORY.parent
PROMO_DIRECTORY = REPOSITORY_ROOT / "promo" / "project_causality"
DEFAULT_TIMELINE = PROMO_DIRECTORY / "timeline.json"
DEFAULT_CLAIMS = PROMO_DIRECTORY / "claims.json"
TARGET_DURATION_SECONDS = 500.0
TARGET_FPS = 30
TIME_EPSILON = 0.001

if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_full_agent_showcase as showcase  # noqa: E402


class ProjectCausalityError(RuntimeError):
    """Raised when the promo contract cannot be materialized or verified."""


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ProjectCausalityError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectCausalityError(
            f"invalid {label} JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ProjectCausalityError(f"{label} root must be an object: {path}")
    return value


def _required_text(container: dict[str, Any], key: str, context: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProjectCausalityError(f"{context}.{key} must be non-empty text")
    return value.strip()


def _required_number(container: dict[str, Any], key: str, context: str) -> float:
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProjectCausalityError(f"{context}.{key} must be a number")
    return float(value)


def _resolved_source(value: Any, timeline_directory: Path, context: str) -> Any:
    """Resolve relative media while preserving labels and environment paths."""

    if isinstance(value, str):
        source = value
        wrapper: dict[str, Any] | None = None
    elif isinstance(value, dict):
        source = _required_text(value, "path", context)
        wrapper = dict(value)
    else:
        raise ProjectCausalityError(f"{context} must be a path or source object")

    expanded = os.path.expandvars(os.path.expanduser(source))
    unresolved_environment_path = expanded == source and (
        source.startswith("%") or source.startswith("$")
    )
    if unresolved_environment_path:
        resolved = source
    else:
        path = Path(expanded)
        if not path.is_absolute():
            path = timeline_directory / path
        resolved = str(path.resolve())

    if wrapper is None:
        return resolved
    wrapper["path"] = resolved
    return wrapper


def _claim_ids(claims_path: Path) -> set[str]:
    ledger = _load_json(claims_path, "claim ledger")
    rows = ledger.get("claims")
    if not isinstance(rows, list) or not rows:
        raise ProjectCausalityError("claim ledger must contain a non-empty claims array")
    result: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ProjectCausalityError(f"claims[{index}] must be an object")
        claim_id = _required_text(row, "id", f"claims[{index}]")
        if claim_id in result:
            raise ProjectCausalityError(f"duplicate claim id: {claim_id}")
        result.add(claim_id)
    return result


def validate_timeline(
    timeline: dict[str, Any], *, claims_path: Path
) -> list[dict[str, Any]]:
    if timeline.get("format_version") != 1:
        raise ProjectCausalityError("timeline format_version must be 1")
    duration = _required_number(timeline, "duration_seconds", "timeline")
    if abs(duration - TARGET_DURATION_SECONDS) > TIME_EPSILON:
        raise ProjectCausalityError(
            f"timeline must be exactly {TARGET_DURATION_SECONDS:.1f}s, got {duration:.3f}s"
        )
    rows = timeline.get("cues")
    if not isinstance(rows, list) or not rows:
        raise ProjectCausalityError("timeline cues must be a non-empty array")

    known_claims = _claim_ids(claims_path)
    seen_ids: set[str] = set()
    cursor = 0.0
    for index, row in enumerate(rows):
        context = f"cues[{index}]"
        if not isinstance(row, dict):
            raise ProjectCausalityError(f"{context} must be an object")
        cue_id = _required_text(row, "id", context)
        if cue_id in seen_ids:
            raise ProjectCausalityError(f"duplicate cue id: {cue_id}")
        seen_ids.add(cue_id)
        start = _required_number(row, "start", context)
        end = _required_number(row, "end", context)
        if abs(start - cursor) > TIME_EPSILON:
            raise ProjectCausalityError(
                f"{context} starts at {start:.3f}s; expected contiguous {cursor:.3f}s"
            )
        if end <= start:
            raise ProjectCausalityError(f"{context} end must be greater than start")
        cursor = end

        for key in ("chapter", "title_zh", "title_en", "narration_zh", "subtitle_en"):
            _required_text(row, key, context)
        status = row.get("status")
        if not isinstance(status, dict):
            raise ProjectCausalityError(f"{context}.status must be an object")
        for key in ("en", "zh", "classification"):
            _required_text(status, key, f"{context}.status")
        visual = row.get("visual")
        if not isinstance(visual, dict):
            raise ProjectCausalityError(f"{context}.visual must be an object")
        visual_type = _required_text(visual, "type", f"{context}.visual")
        if visual_type not in {"title_card", "still", "video_clip", "evidence_card"}:
            raise ProjectCausalityError(
                f"{context}.visual.type is unsupported: {visual_type}"
            )

        claim_values = row.get("claim_ids")
        if not isinstance(claim_values, list) or not claim_values:
            raise ProjectCausalityError(f"{context}.claim_ids must be non-empty")
        unknown = [claim_id for claim_id in claim_values if claim_id not in known_claims]
        if unknown:
            raise ProjectCausalityError(
                f"{context} references unknown claim ids: {', '.join(map(str, unknown))}"
            )

    if abs(cursor - TARGET_DURATION_SECONDS) > TIME_EPSILON:
        raise ProjectCausalityError(
            f"last cue must end at {TARGET_DURATION_SECONDS:.1f}s, got {cursor:.3f}s"
        )
    return rows


def materialize_manifest(
    timeline_path: Path = DEFAULT_TIMELINE,
    claims_path: Path = DEFAULT_CLAIMS,
) -> dict[str, Any]:
    timeline_path = timeline_path.resolve()
    claims_path = claims_path.resolve()
    timeline = _load_json(timeline_path, "timeline")
    rows = validate_timeline(timeline, claims_path=claims_path)
    timeline_directory = timeline_path.parent
    chapters: list[dict[str, Any]] = []

    for index, cue in enumerate(rows):
        visual = cue["visual"]
        duration = float(cue["end"]) - float(cue["start"])
        row: dict[str, Any] = {
            "id": cue["id"],
            "type": visual["type"],
            "title_en": cue["title_en"],
            "title_zh": cue["title_zh"],
            # The generic builder's field predates Chinese-primary films. The
            # project sidecar below records the actual language hierarchy.
            "narration_en": cue["narration_zh"],
            "subtitle_zh": cue["narration_zh"],
            "subtitle_secondary": cue["subtitle_en"],
            "status": cue["status"],
            "min_duration_seconds": duration,
            "tail_padding_seconds": 0.25,
            "brand_en": "PROJECT CAUSALITY  /  GLORIOUS VISION",
            "audio_language": "zho",
            "timeline_start_seconds": cue["start"],
            "timeline_end_seconds": cue["end"],
            "claim_ids": cue["claim_ids"],
            "chapter_label": cue["chapter"],
        }
        if "fit" in visual:
            row["fit"] = visual["fit"]
        if visual["type"] in {"still", "video_clip"}:
            row["source"] = _resolved_source(
                visual.get("source"), timeline_directory, f"cues[{index}].visual.source"
            )
        if visual["type"] == "video_clip":
            row["start_seconds"] = float(visual.get("source_start", 0.0))
            if "source_end" in visual:
                row["end_seconds"] = float(visual["source_end"])
        if visual["type"] == "evidence_card":
            sources = visual.get("sources")
            if not isinstance(sources, list) or not sources:
                raise ProjectCausalityError(
                    f"cues[{index}].visual.sources must be non-empty"
                )
            row["sources"] = [
                _resolved_source(
                    source,
                    timeline_directory,
                    f"cues[{index}].visual.sources[{source_index}]",
                )
                for source_index, source in enumerate(sources)
            ]
        for key in ("body_en", "body_zh"):
            if key in visual:
                row[key] = visual[key]
        chapters.append(row)

    return {
        "format_version": 1,
        "kind": "project_causality_non_music_previsualization_manifest",
        "voice": timeline.get("voice", "zh-CN-XiaoxiaoNeural"),
        "minimum_chapter_seconds": 1.0,
        "narration_padding_seconds": 0.25,
        "target_duration_seconds": TARGET_DURATION_SECONDS,
        "target_frames": int(TARGET_DURATION_SECONDS * TARGET_FPS),
        "primary_language": "zh-Hans",
        "secondary_subtitle_language": "en",
        "music_status": "absent-pending-owner-operated-suno-generation",
        "publication_authorized": False,
        "timeline_source": str(timeline_path),
        "claims_source": str(claims_path),
        "chapters": chapters,
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _finalize_project_sidecar(output: Path, manifest: dict[str, Any]) -> Path:
    sidecar_path = output.with_suffix(".video.json")
    sidecar = _load_json(sidecar_path, "generated video sidecar")
    duration = float(sidecar.get("video", {}).get("duration_seconds", 0.0))
    # AAC packets can extend the MP4 container by slightly more than one video
    # frame even when the picture track is exactly 15,000 frames.
    tolerance = 2.0 / TARGET_FPS + 0.001
    if abs(duration - TARGET_DURATION_SECONDS) > tolerance:
        raise ProjectCausalityError(
            f"rendered duration is {duration:.3f}s; expected 500.000s (+/- {tolerance:.3f}s)"
        )
    sidecar["kind"] = "project_causality_820_non_music_previsualization"
    sidecar["language"] = {
        "primary": "Simplified Chinese narration, titles and primary subtitles",
        "secondary": "English burned subtitles and selected visual hierarchy",
    }
    sidecar["subtitles"]["kind"] = "Bilingual zh-Hans/en ASS, burned into video"
    sidecar["project_causality"] = {
        "title": "project因果律",
        "subtitle": "伪天司的辉煌愿景",
        "target_duration_seconds": TARGET_DURATION_SECONDS,
        "target_frames": int(TARGET_DURATION_SECONDS * TARGET_FPS),
        "timeline_sha256": _sha256(Path(manifest["timeline_source"])),
        "claims_sha256": _sha256(Path(manifest["claims_source"])),
        "music": {
            "included": False,
            "status": "pending-owner-operated-suno-generation-and-review",
            "operator_boundary": "This build did not open, log in to, or automate Suno.",
        },
        "review_status": "previsualization-awaiting-continuous-human-review",
        "publication_authorized": False,
    }
    _atomic_json(sidecar_path, sidecar)
    return sidecar_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--timeline", type=Path, default=DEFAULT_TIMELINE)
    result.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    result.add_argument("--manifest-output", type=Path, required=True)
    result.add_argument("--output", type=Path)
    result.add_argument("--work-dir", type=Path)
    result.add_argument("--manifest-only", action="store_true")
    result.add_argument("--validate-only", action="store_true")
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    result.add_argument("--preset", default="medium")
    result.add_argument("--crf", type=int, default=18)
    result.add_argument("--force", action="store_true")
    return result


def run(args: argparse.Namespace) -> tuple[Path | None, Path | None]:
    manifest = materialize_manifest(args.timeline, args.claims)
    manifest_output = args.manifest_output.expanduser().resolve()
    _atomic_json(manifest_output, manifest)
    print(f"MANIFEST: {manifest_output}")
    print(
        f"TIMELINE: {len(manifest['chapters'])} cues, "
        f"{manifest['target_duration_seconds']:.1f}s, {manifest['target_frames']} frames"
    )
    if args.manifest_only:
        return None, None
    if args.output is None or args.work_dir is None:
        raise ProjectCausalityError(
            "--output and --work-dir are required unless --manifest-only is used"
        )
    builder_args = argparse.Namespace(
        manifest=manifest_output,
        output=args.output,
        work_dir=args.work_dir,
        ffmpeg=args.ffmpeg,
        ffprobe=args.ffprobe,
        voice=None,
        fps=TARGET_FPS,
        crf=args.crf,
        preset=args.preset,
        force=args.force,
        validate_only=args.validate_only,
    )
    output, sidecar = showcase.build(builder_args)
    if args.validate_only:
        return None, None
    return output, _finalize_project_sidecar(output, manifest)


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        output, sidecar = run(args)
    except (ProjectCausalityError, showcase.ShowcaseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if output is not None:
        print(f"PROJECT VIDEO:   {output}")
    if sidecar is not None:
        print(f"PROJECT SIDECAR: {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
