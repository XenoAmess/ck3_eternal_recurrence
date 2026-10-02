"""Freeze chosen Episode 2 TTS runs and original drafts by exact source bytes.

Input selection is a small external JSON file. Output goes to a new external
directory and is consumed by prepare_subtitle_inputs.py. This never calls a
provider, edits a source run, or claims human voice review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CHAPTERS = ("opening", "pursuit", "knights", "reinforcement", "terminal", "closing")


def bound(path: Path) -> dict:
    path = path.resolve(strict=True)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest().upper()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    selection = args.selection.resolve(strict=True)
    source = json.loads(selection.read_text(encoding="utf-8"))
    if (source.get("schema") != "ck3-war-ai.episode02.tts-source-selection.v1"
            or not isinstance(source.get("groups"), list) or not source["groups"]):
        raise ValueError("Expected explicit Episode 2 TTS source selection")
    rows, used, names = [], [], set()
    for group in source["groups"]:
        name = group.get("id")
        selected = tuple(group.get("selected_chapters", ()))
        chapters = tuple(group.get("used_chapters", ()))
        if (not isinstance(name, str) or not name or name in names
                or not selected or selected != tuple(item for item in CHAPTERS if item in selected)
                or not chapters or not set(chapters).issubset(selected)):
            raise ValueError("TTS selection group order/identity changed")
        names.add(name)
        used.extend(chapters)
        row = {"id": name, "selected_chapters": list(selected),
               "used_chapters": list(chapters)}
        for key in ("render_manifest", "native_run_manifest", "source_draft"):
            path = Path(group[key])
            if not path.is_absolute():
                raise ValueError(f"{name} {key} must be an absolute original path")
            row[key] = bound(path)
        rows.append(row)
    if len(used) != len(CHAPTERS) or set(used) != set(CHAPTERS):
        raise ValueError("TTS selection must cover each of six chapters exactly once")
    output = args.output_directory.resolve()
    if (not output.is_absolute() or output.exists()
            or output.is_relative_to(Path(__file__).resolve().parents[3])):
        raise ValueError("TTS selection output must be a new external directory")
    output.mkdir(parents=True, exist_ok=False)
    document = {"schema": "ck3-war-ai.episode02.tts-source-groups.v1",
                "status": "frozen-selection-not-human-reviewed",
                "selection_source": bound(selection),
                "narration_script": bound(args.draft),
                "project_config": bound(args.project_config),
                "groups": rows}
    with (output / "source-groups.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": document["status"], "groups": len(rows),
                      "source_groups": str(output / "source-groups.json")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
