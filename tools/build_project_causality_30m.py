#!/usr/bin/env python3
"""Build the exact 30:00 non-music picture-lock candidate for Project Causality.

The source is a macro-segment radio script.  Each macro segment is bound to the
authoritative 30-minute structure and expands into short bilingual narration
cues suitable for the shared video builder.  This command never launches CK3,
operates Suno, or uploads media.
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
THIRTY_DIRECTORY = PROMO_DIRECTORY / "30m"
DEFAULT_SCRIPT = THIRTY_DIRECTORY / "radio-script.json"
DEFAULT_STRUCTURE = THIRTY_DIRECTORY / "structure.json"
DEFAULT_GATES = THIRTY_DIRECTORY / "chapter-gates.json"
DEFAULT_CLAIMS = PROMO_DIRECTORY / "claims.json"
TARGET_DURATION_SECONDS = 1800.0
TARGET_FPS = 30
TIME_EPSILON = 0.001

if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_full_agent_showcase as showcase  # noqa: E402


class ProjectCausalityThirtyMinuteError(RuntimeError):
    """Raised when the 30-minute editorial contract cannot be materialized."""


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ProjectCausalityThirtyMinuteError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectCausalityThirtyMinuteError(
            f"invalid {label} JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ProjectCausalityThirtyMinuteError(f"{label} root must be an object")
    return value


def _text(container: dict[str, Any], key: str, context: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProjectCausalityThirtyMinuteError(f"{context}.{key} must be text")
    return value.strip()


def _number(container: dict[str, Any], key: str, context: str) -> float:
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProjectCausalityThirtyMinuteError(f"{context}.{key} must be a number")
    return float(value)


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


def _known_claims(path: Path) -> set[str]:
    rows = _load_json(path, "claim ledger").get("claims")
    if not isinstance(rows, list) or not rows:
        raise ProjectCausalityThirtyMinuteError("claim ledger requires claims")
    result: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ProjectCausalityThirtyMinuteError(f"claims[{index}] must be an object")
        claim_id = _text(row, "id", f"claims[{index}]")
        if claim_id in result:
            raise ProjectCausalityThirtyMinuteError(f"duplicate claim id: {claim_id}")
        result.add(claim_id)
    return result


def _resolve_source(value: Any, base: Path, context: str) -> Any:
    if isinstance(value, str):
        raw_path = value
        wrapper: dict[str, Any] | None = None
    elif isinstance(value, dict):
        raw_path = _text(value, "path", context)
        wrapper = dict(value)
    else:
        raise ProjectCausalityThirtyMinuteError(f"{context} must be a path or object")

    expanded = os.path.expandvars(os.path.expanduser(raw_path))
    unresolved_environment_path = expanded == raw_path and (
        raw_path.startswith("%") or raw_path.startswith("$")
    )
    if unresolved_environment_path:
        resolved = raw_path
    else:
        path = Path(expanded)
        if not path.is_absolute():
            path = base / path
        resolved = str(path.resolve())
    if wrapper is None:
        return resolved
    wrapper["path"] = resolved
    return wrapper


def _structure_rows(path: Path) -> list[dict[str, Any]]:
    structure = _load_json(path, "30-minute structure")
    if float(structure.get("duration_seconds", 0.0)) != TARGET_DURATION_SECONDS:
        raise ProjectCausalityThirtyMinuteError("structure must be exactly 1800 seconds")
    rows = structure.get("segments")
    if not isinstance(rows, list) or not rows:
        raise ProjectCausalityThirtyMinuteError("structure requires segments")
    return rows


def _gate_contracts(path: Path) -> dict[str, dict[str, Any]]:
    rows = _load_json(path, "chapter gate contract").get("gates")
    if not isinstance(rows, list) or len(rows) != 4:
        raise ProjectCausalityThirtyMinuteError("chapter gate contract requires four gates")
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ProjectCausalityThirtyMinuteError(f"gates[{index}] must be an object")
        gate_id = _text(row, "id", f"gates[{index}]")
        _text(row, "sound_effect_asset", f"gates[{index}]")
        result[gate_id] = row
    return result


def validate_script(
    script: dict[str, Any],
    *,
    structure_path: Path,
    gates_path: Path,
    claims_path: Path,
) -> list[dict[str, Any]]:
    if script.get("format_version") != 1:
        raise ProjectCausalityThirtyMinuteError("radio script format_version must be 1")
    rows = script.get("segments")
    if not isinstance(rows, list) or not rows:
        raise ProjectCausalityThirtyMinuteError("radio script requires segments")

    structure_rows = _structure_rows(structure_path)
    expected = {str(row["id"]): row for row in structure_rows}
    actual = {
        _text(row, "id", f"segments[{index}]"): row
        for index, row in enumerate(rows)
        if isinstance(row, dict)
    }
    if list(actual) != list(expected):
        raise ProjectCausalityThirtyMinuteError(
            "radio-script segments must match structure order and ids exactly"
        )

    gate_ids = set(_gate_contracts(gates_path))
    known_claims = _known_claims(claims_path)
    cursor = 0.0
    cue_count = 0
    for index, row in enumerate(rows):
        context = f"segments[{index}]"
        segment_id = _text(row, "id", context)
        reference = expected[segment_id]
        start = _number(row, "start", context)
        end = _number(row, "end", context)
        if start != float(reference["start"]) or end != float(reference["end"]):
            raise ProjectCausalityThirtyMinuteError(
                f"{segment_id} timing does not match structure"
            )
        if abs(start - cursor) > TIME_EPSILON:
            raise ProjectCausalityThirtyMinuteError(f"{segment_id} is not contiguous")
        cursor = end
        _text(row, "chapter", context)
        _text(row, "title_zh", context)
        _text(row, "title_en", context)
        status = row.get("status")
        if not isinstance(status, dict):
            raise ProjectCausalityThirtyMinuteError(f"{context}.status must be an object")
        for key in ("en", "zh", "classification"):
            _text(status, key, f"{context}.status")
        claim_ids = row.get("claim_ids")
        if not isinstance(claim_ids, list) or not claim_ids:
            raise ProjectCausalityThirtyMinuteError(f"{context}.claim_ids must be non-empty")
        unknown = [claim_id for claim_id in claim_ids if claim_id not in known_claims]
        if unknown:
            raise ProjectCausalityThirtyMinuteError(
                f"{segment_id} references unknown claims: {unknown}"
            )
        lines = row.get("lines")
        if not isinstance(lines, list) or not lines:
            raise ProjectCausalityThirtyMinuteError(f"{context}.lines must be non-empty")
        line_total = 0.0
        for line_index, line in enumerate(lines):
            line_context = f"{context}.lines[{line_index}]"
            if not isinstance(line, dict):
                raise ProjectCausalityThirtyMinuteError(f"{line_context} must be an object")
            seconds = _number(line, "seconds", line_context)
            if seconds <= 0.0 or seconds > 35.0:
                raise ProjectCausalityThirtyMinuteError(
                    f"{line_context}.seconds must be within (0, 35]"
                )
            line_total += seconds
            zh = _text(line, "zh", line_context)
            en = _text(line, "en", line_context)
            if len(zh) > 150 or len(en) > 420:
                raise ProjectCausalityThirtyMinuteError(
                    f"{line_context} is too long for one bilingual subtitle cue"
                )
            cue_count += 1
        if abs(line_total - (end - start)) > TIME_EPSILON:
            raise ProjectCausalityThirtyMinuteError(
                f"{segment_id} line slots total {line_total:.3f}s; expected {end - start:.3f}s"
            )
        is_gate = row.get("chapter_gate", False)
        if not isinstance(is_gate, bool):
            raise ProjectCausalityThirtyMinuteError(f"{context}.chapter_gate must be boolean")
        if is_gate != (segment_id in gate_ids):
            raise ProjectCausalityThirtyMinuteError(
                f"{segment_id} chapter-gate status conflicts with the gate contract"
            )
        if is_gate and (len(lines) != 1 or end - start != 20.0):
            raise ProjectCausalityThirtyMinuteError(
                f"{segment_id} must be one exact twenty-second cue"
            )

    if abs(cursor - TARGET_DURATION_SECONDS) > TIME_EPSILON:
        raise ProjectCausalityThirtyMinuteError("radio script must end at 1800 seconds")
    serialized = json.dumps(script, ensure_ascii=False).lower()
    if "食人赋能" in serialized:
        raise ProjectCausalityThirtyMinuteError("removed project content appears in radio script")
    if cue_count < 70:
        raise ProjectCausalityThirtyMinuteError(
            f"radio script has only {cue_count} cues; long-form explanation requires at least 70"
        )
    return rows


def materialize_manifest(
    script_path: Path = DEFAULT_SCRIPT,
    structure_path: Path = DEFAULT_STRUCTURE,
    gates_path: Path = DEFAULT_GATES,
    claims_path: Path = DEFAULT_CLAIMS,
) -> dict[str, Any]:
    script_path = script_path.resolve()
    structure_path = structure_path.resolve()
    gates_path = gates_path.resolve()
    claims_path = claims_path.resolve()
    script = _load_json(script_path, "30-minute radio script")
    gate_contracts = _gate_contracts(gates_path)
    rows = validate_script(
        script,
        structure_path=structure_path,
        gates_path=gates_path,
        claims_path=claims_path,
    )
    base = script_path.parent
    chapters: list[dict[str, Any]] = []
    timeline_cursor = 0.0
    for segment in rows:
        segment_visual = segment.get("visual")
        for line_index, line in enumerate(segment["lines"]):
            seconds = float(line["seconds"])
            visual = line.get("visual", segment_visual)
            if not isinstance(visual, dict):
                raise ProjectCausalityThirtyMinuteError(
                    f"{segment['id']}.lines[{line_index}] requires a visual"
                )
            visual_type = _text(visual, "type", "visual")
            if visual_type not in {"title_card", "still", "video_clip", "evidence_card"}:
                raise ProjectCausalityThirtyMinuteError(
                    f"unsupported visual type: {visual_type}"
                )
            chapter: dict[str, Any] = {
                "id": f"{segment['id']}-{line_index + 1:02d}",
                "type": visual_type,
                "title_zh": line.get("title_zh", segment["title_zh"]),
                "title_en": line.get("title_en", segment["title_en"]),
                "narration_en": line["zh"],
                "subtitle_zh": line["zh"],
                "subtitle_secondary": line["en"],
                "status": dict(segment["status"]),
                "min_duration_seconds": seconds,
                "tail_padding_seconds": 0.25,
                "brand_en": "PROJECT CAUSALITY  /  30-MINUTE DOCUMENTARY",
                "audio_language": "zho",
                "timeline_start_seconds": timeline_cursor,
                "timeline_end_seconds": timeline_cursor + seconds,
                "macro_segment_id": segment["id"],
                "chapter_label": segment["chapter"],
                "claim_ids": list(segment["claim_ids"]),
            }
            if segment.get("chapter_gate") is True:
                chapter["chapter_gate"] = True
                chapter["narration_delay_seconds"] = 12.0
                sound_effect_asset = gate_contracts[segment["id"]]["sound_effect_asset"]
                chapter["sound_effect"] = str(
                    (gates_path.parent / sound_effect_asset).resolve()
                )
            if "fit" in visual:
                chapter["fit"] = visual["fit"]
            if "integrated_chapter_title" in visual:
                integrated_title = visual["integrated_chapter_title"]
                if not isinstance(integrated_title, bool):
                    raise ProjectCausalityThirtyMinuteError(
                        f"{chapter['id']}.visual.integrated_chapter_title must be boolean"
                    )
                if integrated_title and segment.get("chapter_gate") is not True:
                    raise ProjectCausalityThirtyMinuteError(
                        f"{chapter['id']}.visual.integrated_chapter_title is limited to chapter gates"
                    )
                chapter["integrated_chapter_title"] = integrated_title
            if visual_type in {"still", "video_clip"}:
                chapter["source"] = _resolve_source(
                    visual.get("source"), base, f"{chapter['id']}.visual.source"
                )
            if visual_type == "video_clip":
                chapter["start_seconds"] = float(visual.get("source_start", 0.0))
                if "source_end" in visual:
                    chapter["end_seconds"] = float(visual["source_end"])
                if "crop_embedded_lower_third" in visual:
                    chapter["crop_embedded_lower_third"] = visual[
                        "crop_embedded_lower_third"
                    ]
            if visual_type == "evidence_card":
                sources = visual.get("sources")
                if not isinstance(sources, list) or not sources:
                    raise ProjectCausalityThirtyMinuteError(
                        f"{chapter['id']} evidence card requires sources"
                    )
                chapter["sources"] = [
                    _resolve_source(source, base, f"{chapter['id']}.sources")
                    for source in sources
                ]
            for key in ("body_en", "body_zh"):
                if key in visual:
                    chapter[key] = visual[key]
            chapters.append(chapter)
            timeline_cursor += seconds

    return {
        "format_version": 1,
        "kind": "project_causality_30m_non_music_picture_lock_manifest",
        "voice": script.get("voice", "zh-CN-XiaoxiaoNeural"),
        "minimum_chapter_seconds": 1.0,
        "narration_padding_seconds": 0.25,
        "target_duration_seconds": TARGET_DURATION_SECONDS,
        "target_frames": int(TARGET_DURATION_SECONDS * TARGET_FPS),
        "enforce_exact_total_seconds": True,
        "primary_language": "zh-Hans",
        "secondary_subtitle_language": "en",
        "music_status": "absent-pending-owner-operated-suno-generation",
        "publication_authorized": False,
        "radio_script_source": str(script_path),
        "structure_source": str(structure_path),
        "chapter_gate_contract_source": str(gates_path),
        "claims_source": str(claims_path),
        "chapters": chapters,
    }


def _finalize_sidecar(output: Path, manifest: dict[str, Any]) -> Path:
    sidecar_path = output.with_suffix(".video.json")
    sidecar = _load_json(sidecar_path, "generated video sidecar")
    duration = float(sidecar.get("video", {}).get("duration_seconds", 0.0))
    tolerance = 2.0 / TARGET_FPS + 0.001
    if abs(duration - TARGET_DURATION_SECONDS) > tolerance:
        raise ProjectCausalityThirtyMinuteError(
            f"rendered duration is {duration:.3f}s; expected 1800.000s"
        )
    sidecar["kind"] = "project_causality_30m_non_music_picture_lock_candidate"
    sidecar["language"] = {
        "primary": "Simplified Chinese synthetic narration and subtitles",
        "secondary": "English burned subtitles",
    }
    sidecar["project_causality"] = {
        "title": "project因果律",
        "subtitle": "伪天司的辉煌愿景",
        "target_duration_seconds": TARGET_DURATION_SECONDS,
        "target_frames": int(TARGET_DURATION_SECONDS * TARGET_FPS),
        "radio_script_sha256": _sha256(Path(manifest["radio_script_source"])),
        "structure_sha256": _sha256(Path(manifest["structure_source"])),
        "chapter_gate_contract_sha256": _sha256(
            Path(manifest["chapter_gate_contract_source"])
        ),
        "claims_sha256": _sha256(Path(manifest["claims_source"])),
        "music": {
            "included": False,
            "status": "pending-owner-operated-suno-generation-after-picture-lock",
            "operator_boundary": "This build did not open, log in to, or automate Suno.",
        },
        "review_status": "picture-lock-candidate-awaiting-continuous-human-review",
        "publication_authorized": False,
    }
    _atomic_json(sidecar_path, sidecar)
    return sidecar_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--script", type=Path, default=DEFAULT_SCRIPT)
    result.add_argument("--structure", type=Path, default=DEFAULT_STRUCTURE)
    result.add_argument("--gates", type=Path, default=DEFAULT_GATES)
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
    manifest = materialize_manifest(
        args.script, args.structure, args.gates, args.claims
    )
    manifest_output = args.manifest_output.expanduser().resolve()
    _atomic_json(manifest_output, manifest)
    print(f"MANIFEST: {manifest_output}")
    print(
        f"TIMELINE: {len(manifest['chapters'])} cues, "
        f"{manifest['target_duration_seconds']:.1f}s, {manifest['target_frames']} frames"
    )
    if args.manifest_only:
        return None, None
    if args.validate_only:
        output = args.output or manifest_output.with_name(
            f"{manifest_output.stem}.validation.mp4"
        )
        work_dir = args.work_dir or (
            manifest_output.parent / ".project-causality-validation-work"
        )
    elif args.output is None or args.work_dir is None:
        raise ProjectCausalityThirtyMinuteError(
            "--output and --work-dir are required for rendering"
        )
    else:
        output = args.output
        work_dir = args.work_dir
    builder_args = argparse.Namespace(
        manifest=manifest_output,
        output=output,
        work_dir=work_dir,
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
    return output, _finalize_sidecar(output, manifest)


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        output, sidecar = run(args)
    except (ProjectCausalityThirtyMinuteError, showcase.ShowcaseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if output is not None:
        print(f"PROJECT VIDEO:   {output}")
    if sidecar is not None:
        print(f"PROJECT SIDECAR: {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
