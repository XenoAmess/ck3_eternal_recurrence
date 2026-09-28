"""Derive source-bound Episode 2 subtitle inputs from exact selected TTS runs.

This is read-only against TTS sources and writes only a new external attempt.
It does not synthesize audio, render video, or claim that anyone heard the MP3.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

SRC = Path(__file__).resolve().parents[1] / "integration" / "src"
sys.path.insert(0, str(SRC))
from war_ai_promo.episode_two_second_half import (  # noqa: E402
    CHAPTER_IDS, _bound_tts_sentences, script_chapters,
)
from war_ai_promo.episode_two_subtitle_contract import (  # noqa: E402
    A05_SCOPE, compact, derive_boundaries, identity, require_audio_coverage,
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
                 chapters: tuple[str, ...], selected: tuple[str, ...],
                 script: Path, source_draft: Path, config: Path,
                 narration: dict[str, str]) -> tuple[list[dict], list[dict]]:
    render_path = render_path.resolve(strict=True)
    native_path = native_path.resolve(strict=True)
    source_draft = source_draft.resolve(strict=True)
    render = json.loads(render_path.read_text(encoding="utf-8"))
    native = json.loads(native_path.read_text(encoding="utf-8"))
    source_artifacts = {item["id"]: item for item in native["artifacts"]}
    if (render.get("schema") != "ck3.episode02.selected-narration-render.v1"
            or render.get("status") != "selected-chapters-rendered-not-human-reviewed"
            or tuple(render.get("selected_chapters", [])) != selected
            or render.get("source_draft", {}).get("sha256", "").upper() != identity(source_draft)["sha256"]
            or render.get("source_draft", {}).get("bytes") != source_draft.stat().st_size
            or native["project_config"]["sha256"].upper() != identity(config)["sha256"]
            or native["project_config"]["bytes"] != config.stat().st_size):
        raise ValueError(f"{group} TTS source does not match this script/config")
    if (source_artifacts["render-manifest"]["sha256"].upper() != identity(render_path)["sha256"]
            or source_artifacts["render-manifest"]["bytes"] != render_path.stat().st_size
            or source_artifacts["source-draft"]["sha256"].upper() != identity(source_draft)["sha256"]
            or source_artifacts["source-draft"]["bytes"] != source_draft.stat().st_size):
        raise ValueError(f"{group} native run does not preserve the render/source bytes")
    selected_source = script_chapters(source_draft)
    if any(selected_source[chapter_id] != narration[chapter_id] for chapter_id in chapters):
        raise ValueError(f"{group} TTS source draft changed current selected narration")
    a05 = any(chapter_id in CHAPTER_IDS[4:] for chapter_id in chapters)
    if not chapters or not set(chapters).issubset(set(selected)):
        raise ValueError(f"{group} used chapters are not a subset of the original render selection")
    if a05 and (chapters != CHAPTER_IDS[4:] or selected != CHAPTER_IDS[4:]):
        raise ValueError("Current A05 terminal/closing must use one exact two-chapter TTS run")
    if not a05 and any(chapter_id in CHAPTER_IDS[4:] for chapter_id in selected):
        raise ValueError("Opening/middle TTS source may not select terminal chapters")
    if (a05 and (render.get("usage_scope") != A05_SCOPE
                 or render.get("a05_writer_facts_checked") is not True
                 or render.get("new_e2_09_live_verified") is not False)):
        raise ValueError("Terminal/closing TTS must bind the current A05 facts without claiming media review")
    if not a05 and render.get("usage_scope") not in (None, "source-bound-edit-proxy"):
        raise ValueError("Opening/middle TTS has unexpected usage scope")
    native_id = f"episode02-tts-native-{group}"
    render_id = f"episode02-tts-render-{group}"
    plan = [
        {"artifact_id": native_id, "source": str(native_path), **identity(native_path), "role": "tts-native-run"},
        {"artifact_id": render_id, "source": str(render_path), **identity(render_path), "role": "tts-render-manifest"},
    ]
    facts_id = None
    facts_path = script.parent / "cards" / "e2-09-a05-writer-facts-20260928-v2.json"
    if a05:
        facts_path = facts_path.resolve(strict=True)
        facts_identity = identity(facts_path)
        fact_source = render.get("a05_fact_evidence")
        preserved = source_artifacts.get("a05-facts")
        if (not isinstance(fact_source, dict)
                or fact_source.get("sha256", "").upper() != facts_identity["sha256"]
                or fact_source.get("bytes") != facts_identity["bytes"]
                or preserved is None
                or preserved["sha256"].upper() != facts_identity["sha256"]
                or preserved["bytes"] != facts_identity["bytes"]):
            raise ValueError("A05 TTS run lacks its exact checked-in writer fact receipt")
        facts = json.loads(facts_path.read_text(encoding="utf-8"))
        if (facts.get("schema") != "xar.war-ai.episode02.a05-writer-card-facts.v2"
                or facts.get("usage_scope") != A05_SCOPE
                or facts.get("run_identity", {}).get("run") !=
                "episode02-terminal-pair-20260928-a05-live"):
            raise ValueError("A05 fact receipt source scope changed")
        facts_id = "episode02-tts-a05-facts"
        plan.append({"artifact_id": facts_id, "source": str(facts_path),
                     **facts_identity, "role": "a05-writer-facts"})
    source_draft_id = None
    if identity(source_draft) != identity(script):
        source_draft_id = f"episode02-tts-source-draft-{group}"
        plan.append({"artifact_id": source_draft_id, "source": str(source_draft),
                     **identity(source_draft), "role": "tts-original-source-draft"})
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
                "usage_scope": A05_SCOPE if a05 else "general-edit-proxy",
                "run_selected_chapters": list(selected),
                "native_run_artifact_id": native_id,
                "native_run_sha256": identity(native_path)["sha256"],
                "native_run_bytes": native_path.stat().st_size,
                "render_manifest_artifact_id": render_id,
                "render_manifest_sha256": identity(render_path)["sha256"],
                "render_manifest_bytes": render_path.stat().st_size,
                "source_audio_artifact_id": f"chapter-{chapter_id}",
                "paragraphs": bound_paragraphs,
                **({"source_draft_artifact_id": source_draft_id,
                    "source_draft_sha256": identity(source_draft)["sha256"],
                    "source_draft_bytes": source_draft.stat().st_size}
                   if source_draft_id else {}),
                **({"a05_facts_artifact_id": facts_id,
                    "a05_facts_sha256": identity(facts_path)["sha256"],
                    "a05_facts_bytes": facts_path.stat().st_size}
                   if facts_id else {}),
            },
        })
    return output, plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--source-groups", type=Path, required=True,
                        help="Frozen path/bytes/SHA manifest of original TTS runs and used chapters")
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
    groups_path = args.source_groups.resolve(strict=True)
    groups = json.loads(groups_path.read_text(encoding="utf-8"))
    if (groups.get("schema") != "ck3-war-ai.episode02.tts-source-groups.v1"
            or groups.get("narration_script") != {"path": str(script), **identity(script)}
            or groups.get("project_config") != {"path": str(config), **identity(config)}
            or not isinstance(groups.get("groups"), list) or not groups["groups"]):
        raise ValueError("TTS source-group selection does not bind the current script/config")
    rows, plan, used, names = [], [], [], []
    for row in groups["groups"]:
        name = row.get("id")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("TTS source-group IDs must be unique and nonempty")
        names.append(name)
        chapters = tuple(row.get("used_chapters", ()))
        selected = tuple(row.get("selected_chapters", ()))
        used.extend(chapters)
        paths = {}
        for key in ("render_manifest", "native_run_manifest", "source_draft"):
            source = row.get(key)
            if not isinstance(source, dict) or not isinstance(source.get("path"), str):
                raise ValueError(f"{name} lacks exact {key} identity")
            path = Path(source["path"]).resolve(strict=True)
            if not path.is_absolute() or source != {"path": str(path), **identity(path)}:
                raise ValueError(f"{name} {key} bytes changed")
            paths[key] = path
        chapter_rows, source_plan = source_group(
            paths["render_manifest"], paths["native_run_manifest"], name,
            chapters, selected, script, paths["source_draft"], config, narration)
        rows.extend(chapter_rows)
        plan.extend(source_plan)
    if len(used) != len(CHAPTER_IDS) or set(used) != set(CHAPTER_IDS):
        raise ValueError("TTS source groups must cover every Episode 2 chapter exactly once")
    rows.sort(key=lambda item: CHAPTER_IDS.index(item["id"]))
    plan.insert(0, {"artifact_id": "episode02-tts-source-groups", "source": str(groups_path),
                    **identity(groups_path), "role": "tts-group-selection"})
    preflight_root = Path(root.anchor)
    if any(not Path(item["source"]).is_relative_to(preflight_root) for item in plan):
        raise ValueError("TTS sources cannot be checked across volumes")
    fake_run = SimpleNamespace(artifacts=tuple(
        SimpleNamespace(artifact_id=item["artifact_id"],
                        path=Path(item["source"]).relative_to(preflight_root),
                        bytes=item["bytes"], sha256=item["sha256"])
        for item in plan))
    fake_manifest = preflight_root / "__episode02_subtitle_preflight_only__.json"
    for row in rows:
        _bound_tts_sentences(fake_run, fake_manifest,
                             {**row, "zh": narration[row["id"]]}, script, config)
    root.mkdir(parents=True, exist_ok=False)
    subtitle = root / "subtitle-input-fragments.json"
    new_json(subtitle, {
        "schema": "ck3-war-ai.episode02.subtitle-input-fragments.v1",
        "status": "machine-source-checked-not-human-reviewed",
        "narration_script": identity(script), "project_config": identity(config),
        "source_groups": {"path": str(groups_path), **identity(groups_path)},
        "chapters": rows,
    })
    new_json(root / "preserve-plan.json", {
        "schema": "ck3-war-ai.episode02.subtitle-preserve-plan.v1",
        "status": "source-checked-not-preserved-in-assembly-run",
        "subtitle_fragments": {"source": str(subtitle), **identity(subtitle)},
        "artifacts": plan,
    })
    print(json.dumps({"status": "machine-source-checked-not-human-reviewed",
                      "subtitle_fragments": str(subtitle),
                      "chapters": len(rows),
                      "source_artifacts": len(plan)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
