"""Read-only source audit for Episode 2 subtitle fragments.

This uses the production composer gate against the original TTS files. It does
not assert that those files have already been preserved into an assembly run,
and it is not a human listening review.
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
from war_ai_promo.episode_two_subtitle_contract import identity  # noqa: E402
from war_ai_promo.captions import caption_cues  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=Path, required=True)
    parser.add_argument("--preserve-plan", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    source_root = args.source_root.resolve(strict=True)
    fragments_path = args.fragments.resolve(strict=True)
    plan_path = args.preserve_plan.resolve(strict=True)
    script = args.draft.resolve(strict=True)
    config = args.project_config.resolve(strict=True)
    if args.audit_output.exists():
        raise FileExistsError(args.audit_output)
    fragments = json.loads(fragments_path.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (fragments.get("schema") != "ck3-war-ai.episode02.subtitle-input-fragments.v1"
            or plan.get("schema") != "ck3-war-ai.episode02.subtitle-preserve-plan.v1"
            or fragments.get("narration_script") != identity(script)
            or fragments.get("project_config") != identity(config)
            or plan.get("subtitle_fragments") != {"source": str(fragments_path), **identity(fragments_path)}
            or [row["id"] for row in fragments["chapters"]] != list(CHAPTER_IDS)):
        raise ValueError("Subtitle fragments/plan do not bind this frozen script/config")
    artifact_rows = []
    for item in plan["artifacts"]:
        subject = Path(item["source"]).resolve(strict=True)
        if not subject.is_relative_to(source_root):
            raise ValueError("TTS source escapes explicit audit root")
        if identity(subject) != {"bytes": item["bytes"], "sha256": item["sha256"].upper()}:
            raise ValueError(f"TTS source bytes changed: {item['artifact_id']}")
        artifact_rows.append(SimpleNamespace(
            artifact_id=item["artifact_id"],
            path=subject.relative_to(source_root),
            bytes=item["bytes"],
            sha256=item["sha256"],
        ))
    if len({row.artifact_id for row in artifact_rows}) != len(artifact_rows):
        raise ValueError("Preserve plan repeats an artifact ID")
    run = SimpleNamespace(artifacts=tuple(artifact_rows))
    fake_path = source_root / "__source_audit_only__.json"
    narration = script_chapters(script)
    checked = []
    for row in fragments["chapters"]:
        candidate = {**row, "zh": narration[row["id"]]}
        events = _bound_tts_sentences(run, fake_path, candidate, script, config)
        zh_cues = [cue for cue in caption_cues({
            **candidate, "en": "", "subtitle_mode": "short",
        }) if cue.track_id == "zh"]
        if not zh_cues or len(events) > len(zh_cues):
            raise ValueError(f"{row['id']} source timed events did not reach caption renderer")
        checked.append({"id": row["id"], "sentences": len(events),
                        "source_timed_zh_cues": len(zh_cues),
                        "source_run_id": row["tts_source"]["run_id"],
                        "source_usage_scope": row["tts_source"]["usage_scope"],
                        "audio_sha256": row["audio_sha256"]})
    negative_checks = []
    for label, chapter_id, mutate in (
            ("sentence-text-tamper", "opening",
             lambda value: value["sentence_boundaries"][0].__setitem__(
                 "text", value["sentence_boundaries"][0]["text"] + "伪")),
            ("historical-scope-tamper", "terminal",
             lambda value: value["tts_source"].__setitem__("usage_scope", "current-run"))):
        candidate = json.loads(json.dumps(next(row for row in fragments["chapters"]
                                               if row["id"] == chapter_id)))
        candidate["zh"] = narration[chapter_id]
        mutate(candidate)
        try:
            _bound_tts_sentences(run, fake_path, candidate, script, config)
        except ValueError:
            negative_checks.append(label)
        else:
            raise ValueError(f"Subtitle source gate accepted {label}")
    output = {
        "schema": "ck3-war-ai.episode02.subtitle-source-audit.v1",
        "status": "machine-source-checked-not-human-reviewed",
        "assembly_run_preservation": "not-checked",
        "source_root": str(source_root),
        "fragments": {"path": str(fragments_path), **identity(fragments_path)},
        "preserve_plan": {"path": str(plan_path), **identity(plan_path)},
        "chapters": checked,
        "negative_checks_rejected": negative_checks,
    }
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    with args.audit_output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": output["status"], "chapters": len(checked),
                      "sentences": sum(row["sentences"] for row in checked),
                      "audit": str(args.audit_output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
