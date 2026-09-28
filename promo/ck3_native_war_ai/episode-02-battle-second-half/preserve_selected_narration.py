"""Preserve one finished Episode 2 TTS render into its fresh native run.

Every render file is copied into append-only content-addressed storage. The
stable aliases used by subtitle admission are created first; all remaining
request/response/event/probe/partial files receive unique process IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def identity(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest().upper()}


def new_json(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def plan(render_dir: Path, native_path: Path) -> list[tuple[str, Path, str, str]]:
    render_path = render_dir / "manifest-final.json"
    render = json.loads(render_path.read_text(encoding="utf-8"))
    native = json.loads(native_path.read_text(encoding="utf-8"))
    if (render.get("schema") != "ck3.episode02.selected-narration-render.v1"
            or render.get("status") != "selected-chapters-rendered-not-human-reviewed"
            or native.get("kind") != "xar_promo_run_manifest"
            or native.get("artifacts")
            or native["project_config"]["sha256"].upper() !=
            render["snapshots"]["project_config"]["sha256"].upper()
            or native["project_config"]["bytes"] !=
            render["snapshots"]["project_config"]["bytes"]):
        raise ValueError("Render/native run is incomplete, mismatched or no longer fresh")
    if (identity(render_dir / "snapshot-draft.md") !=
            {key: render["source_draft"][key] for key in ("bytes", "sha256")}):
        raise ValueError("Frozen TTS draft differs from render source")
    wheel = Path(render["wheel"]["path"]).resolve(strict=True)
    if identity(wheel) != {key: render["wheel"][key] for key in ("bytes", "sha256")}:
        raise ValueError("Selected formal wheel bytes changed")
    aliases = [
        ("source-draft", render_dir / "snapshot-draft.md", "raw", "original-tts-source-draft"),
        ("render-manifest", render_path, "derived", "tts-render-manifest"),
        ("selected-wheel", wheel, "raw", "formal-toolchain-wheel"),
    ]
    for chapter in render["chapters"]:
        media = Path(chapter["audio"]["path"]).resolve(strict=True)
        if identity(media) != {key: chapter["audio"][key] for key in ("bytes", "sha256")}:
            raise ValueError(f"{chapter['id']} chapter MP3 differs from renderer")
        aliases.append((f"chapter-{chapter['id']}", media, "derived", "tts-chapter-audio"))
    facts = render.get("a05_fact_evidence")
    if facts is not None:
        path = render_dir / ("snapshot-" + Path(facts["path"]).name)
        if identity(path) != {key: facts[key] for key in ("bytes", "sha256")}:
            raise ValueError("A05 writer fact snapshot differs from render")
        aliases.append(("a05-facts", path, "raw", "a05-writer-fact-receipt"))
    covered = {path.resolve() for _, path, _, _ in aliases}
    for path in sorted(render_dir.rglob("*")):
        if not path.is_file() or path.resolve() in covered:
            continue
        relative = path.relative_to(render_dir).as_posix()
        item_id = "process-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:24]
        aliases.append((item_id, path, "derived", "tts-process-material"))
    if len({row[0] for row in aliases}) != len(aliases):
        raise ValueError("TTS preserve plan repeats an artifact ID")
    return aliases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-directory", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--audit-directory", type=Path, required=True)
    args = parser.parse_args()
    render_dir = args.render_directory.resolve(strict=True)
    native_path = args.run_manifest.resolve(strict=True)
    audit = args.audit_directory.resolve()
    if not audit.is_absolute() or audit.exists() or audit.is_relative_to(Path(__file__).resolve().parents[3]):
        raise ValueError("Audit directory must be a new absolute external attempt")
    rows = plan(render_dir, native_path)
    audit.mkdir(parents=True, exist_ok=False)
    new_json(audit / "source-inventory.json", {
        "schema": "ck3-war-ai.episode02.tts-preserve-inventory.v1",
        "render_manifest": {"path": str(render_dir / "manifest-final.json"),
                            **identity(render_dir / "manifest-final.json")},
        "native_run_before": {"path": str(native_path), **identity(native_path)},
        "preserver": {"path": str(Path(__file__).resolve()), **identity(Path(__file__))},
        "artifacts": [{"id": item_id, "source": str(path), **identity(path),
                       "collection": collection, "role": role}
                      for item_id, path, collection, role in rows],
    })
    for number, (item_id, path, collection, role) in enumerate(rows):
        argv = [sys.executable, "-m", "xar_promo", "preserve",
                "--run-manifest", str(native_path), "--artifact-id", item_id,
                "--collection", collection, "--role", role, str(path)]
        result = subprocess.run(argv, capture_output=True, text=True, check=False)
        new_json(audit / f"preserve-{number:03d}.json", {
            "argv": argv, "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr,
            "source": {"path": str(path), **identity(path)},
        })
        if result.returncode:
            raise RuntimeError(f"TTS preservation RED at {item_id}; partial run and logs retained")
    final = json.loads(native_path.read_text(encoding="utf-8"))
    if (len(final["artifacts"]) != len(rows)
            or {item["id"] for item in final["artifacts"]} != {row[0] for row in rows}):
        raise ValueError("Native run does not contain the exact complete TTS inventory")
    new_json(audit / "preservation-final.json", {
        "schema": "ck3-war-ai.episode02.tts-preservation.v1",
        "status": "all-render-material-preserved-not-human-reviewed",
        "run_manifest": {"path": str(native_path), **identity(native_path)},
        "artifact_count": len(rows),
    })
    print(json.dumps({"status": "all-render-material-preserved-not-human-reviewed",
                      "run_manifest": str(native_path), "artifact_count": len(rows)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
