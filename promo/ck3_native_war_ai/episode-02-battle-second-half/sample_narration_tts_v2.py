"""Create a fresh, append-only EdgeTTS timing probe for six Episode 2 chapters.

This is a project-owned timing sampler, not an xar-promo CLI command or a final
IndexTTS voice take. It never edits a prior attempt or the source narration.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import edge_tts

from audit_narration_budget import HEADER, counts, extract_narration, identity, spoken_text


VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-12%"
SELECTION = (
    ("opening", 0, 0),
    ("pursuit", 1, 2),
    ("knights", 2, 6),
    ("reinforcement", 3, 3),
    ("terminal", 4, 4),
    ("closing", 5, 1),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_new(path: Path, content: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(content)


def write_json_new(path: Path, payload: dict) -> None:
    write_new(path, (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def source_paragraphs(draft: str, chapter_index: int) -> list[str]:
    headings = list(HEADER.finditer(draft))
    heading = headings[chapter_index]
    block = draft[heading.end():headings[chapter_index + 1].start()
                  if chapter_index + 1 < len(headings) else len(draft)]
    start = block.index("**旁白**：") + len("**旁白**：")
    end = block.index("**录制缺口**", start)
    return [value.strip() for value in re.split(r"\n\s*\n", block[start:end]) if value.strip()]


def plan(draft_path: Path) -> dict:
    raw = draft_path.read_bytes()
    draft = raw.decode("utf-8-sig")
    chapters = extract_narration(draft)
    rows = []
    for name, chapter_index, paragraph_index in SELECTION:
        if chapters[chapter_index]["id"] != name:
            raise ValueError(f"chapter index drift: {name}")
        paragraphs = source_paragraphs(draft, chapter_index)
        if paragraph_index >= len(paragraphs):
            raise ValueError(f"paragraph index drift: {name}/{paragraph_index}")
        source = paragraphs[paragraph_index]
        text = spoken_text(source)
        if not text or any(marker in text for marker in ("[^", "`", "**")):
            raise ValueError(f"unstripped or empty sample: {name}")
        rows.append({"name": name, "chapter_index": chapter_index,
                     "paragraph_index": paragraph_index, "paragraph_count": len(paragraphs),
                     "source_paragraph_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest().upper(),
                     "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest().upper(),
                     "text": text, **counts(text)})
    return {"schema": "ck3.episode02.tts-six-chapter-plan.v2",
            "draft": {"path": str(draft_path.resolve()), "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest().upper()},
            "selection": rows}


def emit_event(events: Path, kind: str, **details: object) -> None:
    with events.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"at_utc": utc_now(), "kind": kind, **details},
                                ensure_ascii=False) + "\n")


async def synthesize(text: str, media: Path, events: Path) -> None:
    communicator = edge_tts.Communicate(text=text, voice=VOICE, rate=RATE)
    with media.open("xb") as audio, events.open("xb") as timing:
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            else:
                timing.write((json.dumps(chunk, ensure_ascii=False) + "\n").encode("utf-8"))


def probe(ffprobe: Path, media: Path, target: Path) -> float:
    command = [str(ffprobe), "-v", "error", "-show_entries", "format=duration",
               "-of", "json", str(media)]
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    write_json_new(target, {"argv": command, "returncode": result.returncode,
                            "stdout": result.stdout, "stderr": result.stderr})
    duration = float(json.loads(result.stdout)["format"]["duration"])
    if duration <= 0:
        raise ValueError(f"invalid audio duration for {media}")
    return round(duration, 3)


async def run(args: argparse.Namespace, planned: dict) -> None:
    ffprobe = Path(shutil.which(args.ffprobe) or args.ffprobe).resolve()
    if not ffprobe.is_file():
        raise FileNotFoundError(f"ffprobe missing: {ffprobe}")
    if not args.project_config.is_file() or not args.run_manifest.is_file():
        raise FileNotFoundError("project config or native run manifest missing")
    versions = {"edge-tts": importlib.metadata.version("edge-tts"),
                "xar-promo-toolchain": importlib.metadata.version("xar-promo-toolchain")}
    if versions["xar-promo-toolchain"] != args.toolchain_version:
        raise ValueError("selected xar-promo release differs from installed package")
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output
    events = out / "attempt-events.jsonl"
    snapshot = out / "narration-script-draft.md"
    script_snapshot = out / "sample_narration_tts_v2.py"
    config_snapshot = out / "promo-project.json"
    write_new(snapshot, args.draft.read_bytes())
    write_new(script_snapshot, Path(__file__).read_bytes())
    write_new(config_snapshot, args.project_config.read_bytes())
    if identity(snapshot)["sha256"] != planned["draft"]["sha256"]:
        raise ValueError("draft changed while snapshotting")
    write_json_new(out / "selection-plan.json", planned)
    manifest = {"schema": "ck3.episode02.tts-six-chapter-samples.v2",
                "status": "started", "created_utc": utc_now(),
                "source_draft": planned["draft"], "snapshot": identity(snapshot),
                "script_snapshot": identity(script_snapshot),
                "project_config_snapshot": identity(config_snapshot),
                "native_run_manifest": identity(args.run_manifest),
                "interpreter": str(Path(sys.executable).resolve()), "python": sys.version,
                "versions": versions, "wheel_sha256": args.wheel_sha256.upper(),
                "provider": "edge-tts", "voice": VOICE, "rate": RATE,
                "ffprobe": str(ffprobe), "samples": []}
    emit_event(events, "attempt_started", draft_sha256=planned["draft"]["sha256"])
    try:
        for row in planned["selection"]:
            name = row["name"]
            target = out / name
            target.mkdir(exist_ok=False)
            request = target / "request.json"
            write_json_new(request, {"provider": "edge-tts", "voice": VOICE,
                                     "rate": RATE, "edge_tts_version": versions["edge-tts"],
                                     "source_paragraph_sha256": row["source_paragraph_sha256"],
                                     "text_sha256": row["text_sha256"], "text": row["text"]})
            emit_event(events, "sample_started", name=name,
                       request_sha256=identity(request)["sha256"])
            media = target / "response.mp3"
            timing = target / "response-events.jsonl"
            await asyncio.wait_for(synthesize(row["text"], media, timing), timeout=150)
            duration = probe(ffprobe, media, target / "ffprobe-receipt.json")
            entry = {"name": name, "chapter_index": row["chapter_index"],
                     "paragraph_index": row["paragraph_index"],
                     "source_paragraph_sha256": row["source_paragraph_sha256"],
                     "text_sha256": row["text_sha256"], "duration_seconds": duration,
                     "counts": counts(row["text"]), "request": identity(request),
                     "audio": identity(media), "events": identity(timing),
                     "probe": identity(target / "ffprobe-receipt.json")}
            manifest["samples"].append(entry)
            write_json_new(out / f'manifest-after-{len(manifest["samples"]):02d}.json',
                           {**manifest, "status": "partial"})
            emit_event(events, "sample_completed", name=name, duration_seconds=duration,
                       media_sha256=entry["audio"]["sha256"])
        manifest["status"] = "six-samples-rendered-not-human-reviewed"
    except Exception:
        manifest["status"] = "red-preserved"
        manifest["error"] = traceback.format_exc()
        emit_event(events, "attempt_red", error=manifest["error"])
        raise
    finally:
        manifest["finished_utc"] = utc_now()
        manifest["attempt_events"] = identity(events)
        write_json_new(out / "manifest-final.json", manifest)
    print(json.dumps({"manifest": str(out / "manifest-final.json"),
                      "samples": [{"name": row["name"], "seconds": row["duration_seconds"]}
                                  for row in manifest["samples"]]}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-draft-sha256", required=True)
    parser.add_argument("--toolchain-version", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--plan-only", action="store_true", help="Read-only paragraph/SHA preview")
    args = parser.parse_args()
    planned = plan(args.draft)
    if planned["draft"]["sha256"] != args.expected_draft_sha256.upper():
        raise ValueError("draft SHA differs from frozen selected bytes")
    if not re.fullmatch(r"[0-9A-Fa-f]{64}", args.wheel_sha256):
        raise ValueError("wheel SHA-256 must be 64 hexadecimal characters")
    if args.plan_only:
        print(json.dumps(planned, ensure_ascii=False, indent=2))
        return
    asyncio.run(run(args, planned))


if __name__ == "__main__":
    main()
