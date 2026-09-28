"""Derive source-bound Episode 2 subtitle inputs from two existing TTS runs.

This is read-only against TTS sources and writes only a new external attempt.
It does not synthesize audio, render video, or claim that anyone heard the MP3.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "integration" / "src"
sys.path.insert(0, str(SRC))
from war_ai_promo.episode_two_second_half import CHAPTER_IDS, script_chapters  # noqa: E402
from war_ai_promo.episode_two_subtitle_contract import (  # noqa: E402
    HISTORICAL_SCOPE, compact, derive_boundaries, identity, require_audio_coverage,
)


def checked(path: Path, expected: dict, label: str) -> Path:
    path = path.resolve(strict=True)
    if identity(path) != {"bytes": expected["bytes"], "sha256": expected["sha256"].upper()}:
        raise ValueError(f"{label} differs from frozen TTS manifest")
    return path


def new_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def source_group(render_path: Path, native_path: Path, group: str,
                 chapters: tuple[str, ...], script: Path, config: Path,
                 narration: dict[str, str]) -> tuple[list[dict], list[dict]]:
    render_path = render_path.resolve(strict=True)
    native_path = native_path.resolve(strict=True)
    render = json.loads(render_path.read_text(encoding="utf-8"))
    native = json.loads(native_path.read_text(encoding="utf-8"))
    source_artifacts = {item["id"]: item for item in native["artifacts"]}
    if (render.get("schema") != "ck3.episode02.selected-narration-render.v1"
            or render.get("status") != "selected-chapters-rendered-not-human-reviewed"
            or tuple(render.get("selected_chapters", [])) != chapters
            or render.get("source_draft", {}).get("sha256", "").upper() != identity(script)["sha256"]
            or render.get("source_draft", {}).get("bytes") != script.stat().st_size
            or native["project_config"]["sha256"].upper() != identity(config)["sha256"]
            or native["project_config"]["bytes"] != config.stat().st_size):
        raise ValueError(f"{group} TTS source does not match this script/config")
    if (source_artifacts["render-manifest"]["sha256"].upper() != identity(render_path)["sha256"]
            or source_artifacts["render-manifest"]["bytes"] != render_path.stat().st_size
            or source_artifacts["source-draft"]["sha256"].upper() != identity(script)["sha256"]):
        raise ValueError(f"{group} native run does not preserve the render/source bytes")
    historical = group == "last-two"
    if (historical and (render.get("usage_scope") != HISTORICAL_SCOPE
                        or render.get("new_e2_09_live_verified") is not False)):
        raise ValueError("Terminal/closing TTS must remain historical only")
    if not historical and render.get("usage_scope") is not None:
        raise ValueError("First four chapters have unexpected TTS usage scope")
    native_id = f"episode02-tts-native-{group}"
    render_id = f"episode02-tts-render-{group}"
    plan = [
        {"artifact_id": native_id, "source": str(native_path), **identity(native_path), "role": "tts-native-run"},
        {"artifact_id": render_id, "source": str(render_path), **identity(render_path), "role": "tts-render-manifest"},
    ]
    output = []
    for chapter_id in chapters:
        rows = [item for item in render["chapters"] if item["id"] == chapter_id]
        if len(rows) != 1:
            raise ValueError(f"{chapter_id} needs exactly one source TTS chapter")
        original = rows[0]
        audio = checked(Path(original["audio"]["path"]), original["audio"], f"{chapter_id} MP3")
        if (source_artifacts[f"chapter-{chapter_id}"]["sha256"].upper() != identity(audio)["sha256"]
                or source_artifacts[f"chapter-{chapter_id}"]["bytes"] != audio.stat().st_size):
            raise ValueError(f"{chapter_id} chapter MP3 differs from native run")
        plan.append({"artifact_id": f"audio.{chapter_id}", "source": str(audio),
                     **identity(audio), "role": "tts-chapter-audio"})
        paragraph_source = [item for item in render["paragraphs"] if item["chapter_id"] == chapter_id]
        bound_paragraphs = []
        paths = {}
        for index, item in enumerate(paragraph_source):
            if item["paragraph_index"] != index:
                raise ValueError(f"{chapter_id} TTS paragraph order changed")
            request = checked(Path(item["request"]["path"]), item["request"],
                              f"{chapter_id} request {index}")
            events = checked(Path(item["response_events"]["path"]), item["response_events"],
                             f"{chapter_id} Edge events {index}")
            checked(Path(item["audio"]["path"]), item["audio"], f"{chapter_id} response {index}")
            request_id = f"episode02-tts-{chapter_id}-p{index:02d}-request"
            events_id = f"episode02-tts-{chapter_id}-p{index:02d}-events"
            plan.extend((
                {"artifact_id": request_id, "source": str(request), **identity(request), "role": "tts-request"},
                {"artifact_id": events_id, "source": str(events), **identity(events), "role": "tts-edge-events"},
            ))
            bound_paragraphs.append({
                "paragraph_index": index, "duration_seconds": item["duration_seconds"],
                "text_sha256": item["text_sha256"],
                "request_artifact_id": request_id,
                "request_sha256": item["request"]["sha256"], "request_bytes": item["request"]["bytes"],
                "events_artifact_id": events_id,
                "events_sha256": item["response_events"]["sha256"],
                "events_bytes": item["response_events"]["bytes"],
            })
            paths[index] = (request, events)
        boundaries, text, last_end = derive_boundaries(
            chapter_id, bound_paragraphs, lambda item: paths[item["paragraph_index"]])
        speech = original["speech_seconds"]
        if text != compact(narration[chapter_id]):
            raise ValueError(f"{chapter_id} TTS response text differs from frozen narration")
        require_audio_coverage(chapter_id, boundaries, speech, last_end)
        output.append({
            "id": chapter_id, "audio_sha256": identity(audio)["sha256"],
            "audio_bytes": audio.stat().st_size, "speech_duration_seconds": speech,
            "sentence_boundaries": boundaries,
            "tts_source": {
                "run_id": native["run"]["id"],
                "usage_scope": HISTORICAL_SCOPE if historical else "general-edit-proxy",
                "native_run_artifact_id": native_id,
                "native_run_sha256": identity(native_path)["sha256"],
                "native_run_bytes": native_path.stat().st_size,
                "render_manifest_artifact_id": render_id,
                "render_manifest_sha256": identity(render_path)["sha256"],
                "render_manifest_bytes": render_path.stat().st_size,
                "source_audio_artifact_id": f"chapter-{chapter_id}",
                "paragraphs": bound_paragraphs,
            },
        })
    return output, plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--first-four-render", type=Path, required=True)
    parser.add_argument("--first-four-run", type=Path, required=True)
    parser.add_argument("--last-two-render", type=Path, required=True)
    parser.add_argument("--last-two-run", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_directory.resolve()
    if not root.is_absolute() or root.exists():
        raise ValueError("Output must be a new absolute external attempt directory")
    if root.is_relative_to(Path(__file__).resolve().parents[3]):
        raise ValueError("Subtitle attempt must be outside the project checkout")
    script = args.draft.resolve(strict=True)
    config = args.project_config.resolve(strict=True)
    narration = script_chapters(script)
    first, first_plan = source_group(
        args.first_four_render, args.first_four_run, "first-four",
        CHAPTER_IDS[:4], script, config, narration)
    last, last_plan = source_group(
        args.last_two_render, args.last_two_run, "last-two",
        CHAPTER_IDS[4:], script, config, narration)
    rows = first + last
    if [item["id"] for item in rows] != list(CHAPTER_IDS):
        raise ValueError("Subtitle chapters differ from ProjectConfig order")
    root.mkdir(parents=True, exist_ok=False)
    subtitle = root / "subtitle-input-fragments.json"
    new_json(subtitle, {
        "schema": "ck3-war-ai.episode02.subtitle-input-fragments.v1",
        "status": "machine-source-checked-not-human-reviewed",
        "narration_script": identity(script), "project_config": identity(config),
        "chapters": rows,
    })
    new_json(root / "preserve-plan.json", {
        "schema": "ck3-war-ai.episode02.subtitle-preserve-plan.v1",
        "status": "source-checked-not-preserved-in-assembly-run",
        "subtitle_fragments": {"source": str(subtitle), **identity(subtitle)},
        "artifacts": first_plan + last_plan,
    })
    print(json.dumps({"status": "machine-source-checked-not-human-reviewed",
                      "subtitle_fragments": str(subtitle),
                      "chapters": len(rows), "source_artifacts": len(first_plan + last_plan)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
