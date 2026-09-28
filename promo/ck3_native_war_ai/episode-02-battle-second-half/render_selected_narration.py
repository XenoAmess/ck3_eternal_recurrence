"""Render selected, source-bound Episode 2 narration chapters as an immutable EdgeTTS run.

This is a project adapter, not an xar-promo CLI command or a final voice take.
It never edits earlier attempts and never marks footage or human review as approved.
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


VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-12%"
CHAPTER_IDS = ("opening", "pursuit", "knights", "reinforcement", "terminal", "closing")
BUDGETS = (90, 340, 400, 515, 350, 95)
HEADER = re.compile(r"^## (\d{2}:\d{2})[–-](\d{2}:\d{2}) (.+)$", re.M)
FOOTNOTE = re.compile(r"\[\^[^\]]+\]")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper()}


def write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)


def write_json_new(path: Path, data: dict) -> None:
    write_new(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def spoken(value: str) -> str:
    value = FOOTNOTE.sub("", value).replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", value).strip()


def parse_draft(path: Path, selected: tuple[str, ...]) -> dict:
    raw = path.read_bytes()
    draft = raw.decode("utf-8-sig")
    headings = list(HEADER.finditer(draft))
    if len(headings) != len(CHAPTER_IDS):
        raise ValueError(f"expected six chapter headings, got {len(headings)}")
    chapters = []
    for index, heading in enumerate(headings):
        block = draft[heading.end():headings[index + 1].start()
                      if index + 1 < len(headings) else len(draft)]
        start_marker, end_marker = "**旁白**：", "**录制缺口**"
        start = block.find(start_marker)
        end = block.find(end_marker, start + len(start_marker))
        if start < 0 or end < 0:
            raise ValueError(f"chapter {index} narration bounds missing")
        source_text = block[start + len(start_marker):end]
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", source_text) if part.strip()]
        pieces = []
        for number, source in enumerate(paragraphs):
            text = spoken(source)
            if not text or any(marker in text for marker in ("[^", "`", "**")):
                raise ValueError(f"invalid spoken paragraph {index}/{number}")
            if len(text) > 1400:
                raise ValueError(f"paragraph {index}/{number} is too long for one TTS request")
            pieces.append({"index": number, "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest().upper(),
                           "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest().upper(),
                           "characters": len(text), "text": text})
        if spoken(source_text) != spoken(" ".join(piece["text"] for piece in pieces)):
            raise ValueError(f"chapter {index} narration changed at paragraph split")
        chapter_id = CHAPTER_IDS[index]
        chapters.append({"id": chapter_id, "title": heading.group(3),
                         "budget_seconds": BUDGETS[index], "paragraphs": pieces,
                         "text_sha256": hashlib.sha256(spoken(source_text).encode("utf-8")).hexdigest().upper(),
                         "selected": chapter_id in selected})
    return {"schema": "ck3.episode02.narration-selection.v1", "draft": identity(path),
            "selected_chapters": list(selected), "held_chapters": [x for x in CHAPTER_IDS if x not in selected],
            "chapters": chapters}


def event(path: Path, kind: str, **details: object) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"at_utc": now(), "kind": kind, **details}, ensure_ascii=False) + "\n")


async def synthesize(text: str, media: Path, metadata: Path) -> None:
    communicator = edge_tts.Communicate(text=text, voice=VOICE, rate=RATE)
    with media.open("xb") as audio, metadata.open("xb") as events:
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            else:
                events.write((json.dumps(chunk, ensure_ascii=False) + "\n").encode("utf-8"))


def run_command(argv: list[str], receipt: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    write_json_new(receipt, {"argv": argv, "returncode": result.returncode,
                             "stdout": result.stdout, "stderr": result.stderr})
    result.check_returncode()
    return result


def probe(ffprobe: Path, media: Path, receipt: Path) -> float:
    result = run_command([str(ffprobe), "-v", "error", "-show_entries", "format=duration",
                          "-of", "json", str(media)], receipt, 30)
    duration = float(json.loads(result.stdout)["format"]["duration"])
    if duration <= 0:
        raise ValueError(f"invalid media duration: {media}")
    return round(duration, 3)


def concat(ffmpeg: Path, chapter_dir: Path, paragraph_count: int) -> tuple[Path, Path, Path]:
    list_file = chapter_dir / "concat-input.txt"
    lines = [f"file 'paragraph-{number:02d}/response.mp3'" for number in range(paragraph_count)]
    write_new(list_file, ("\n".join(lines) + "\n").encode("utf-8"))
    output = chapter_dir / "chapter-speech.mp3"
    receipt = chapter_dir / "concat-receipt.json"
    run_command([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-f", "concat",
                 "-safe", "0", "-i", str(list_file), "-c", "copy", str(output)], receipt, 120)
    return output, list_file, receipt


def validate_inputs(args: argparse.Namespace) -> tuple[dict, Path, Path]:
    wheel = identity(args.wheel_file)
    if wheel["sha256"] != args.wheel_sha256.upper():
        raise ValueError("downloaded wheel SHA differs from selected release")
    release = json.loads(args.release_receipt.read_text(encoding="utf-8"))
    if release["tag_name"] != f"v{args.toolchain_version}" or release["draft"] or release["prerelease"]:
        raise ValueError("release receipt does not describe selected stable release")
    wheel_assets = [asset for asset in release["assets"] if asset["name"] == args.wheel_file.name]
    if len(wheel_assets) != 1 or wheel_assets[0].get("digest", "").upper() != f"SHA256:{wheel['sha256']}":
        raise ValueError("wheel bytes differ from release asset digest")
    if importlib.metadata.version("xar-promo-toolchain") != args.toolchain_version:
        raise ValueError("installed xar-promo version differs from selected release")
    config = json.loads(args.project_config.read_text(encoding="utf-8"))
    if [chapter["id"] for chapter in config["chapters"]] != list(CHAPTER_IDS):
        raise ValueError("ProjectConfig chapter order changed")
    if not args.run_manifest.is_file():
        raise FileNotFoundError(args.run_manifest)
    ffprobe = Path(shutil.which(args.ffprobe) or args.ffprobe).resolve()
    ffmpeg = Path(shutil.which(args.ffmpeg) or args.ffmpeg).resolve()
    if not ffprobe.is_file() or not ffmpeg.is_file():
        raise FileNotFoundError("ffprobe or ffmpeg missing")
    return wheel, ffprobe, ffmpeg


async def render(args: argparse.Namespace, plan: dict, wheel: dict, ffprobe: Path, ffmpeg: Path) -> None:
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output
    snapshots = {}
    for label, source in (("draft", args.draft), ("project_config", args.project_config),
                          ("script", Path(__file__)), ("release_receipt", args.release_receipt)):
        destination = out / f"snapshot-{label}{source.suffix}"
        write_new(destination, source.read_bytes())
        snapshots[label] = identity(destination)
    write_json_new(out / "selection-plan.json", plan)
    events = out / "attempt-events.jsonl"
    manifest = {"schema": "ck3.episode02.selected-narration-render.v1",
                "status": "started", "created_utc": now(),
                "source_draft": plan["draft"], "snapshots": snapshots,
                "native_run_manifest_before_preserve": identity(args.run_manifest),
                "wheel": wheel, "installed_toolchain_version": args.toolchain_version,
                "interpreter": str(Path(sys.executable).resolve()), "python": sys.version,
                "edge_tts_version": importlib.metadata.version("edge-tts"),
                "provider": "edge-tts", "voice": VOICE, "rate": RATE,
                "ffprobe": str(ffprobe), "ffmpeg": str(ffmpeg),
                "selected_chapters": plan["selected_chapters"], "held_chapters": plan["held_chapters"],
                "paragraphs": [], "chapters": []}
    event(events, "attempt_started", selected_chapters=plan["selected_chapters"])
    try:
        for chapter in plan["chapters"]:
            if not chapter["selected"]:
                continue
            chapter_dir = out / chapter["id"]
            chapter_dir.mkdir(exist_ok=False)
            paragraph_rows = []
            for piece in chapter["paragraphs"]:
                paragraph_dir = chapter_dir / f"paragraph-{piece['index']:02d}"
                paragraph_dir.mkdir(exist_ok=False)
                request = paragraph_dir / "request.json"
                write_json_new(request, {"provider": "edge-tts", "voice": VOICE, "rate": RATE,
                                         "edge_tts_version": manifest["edge_tts_version"],
                                         "chapter_id": chapter["id"], "paragraph_index": piece["index"],
                                         "source_paragraph_sha256": piece["source_sha256"],
                                         "text_sha256": piece["text_sha256"], "text": piece["text"]})
                event(events, "paragraph_started", chapter=chapter["id"], index=piece["index"],
                      request_sha256=identity(request)["sha256"])
                audio = paragraph_dir / "response.mp3"
                metadata = paragraph_dir / "response-events.jsonl"
                await asyncio.wait_for(synthesize(piece["text"], audio, metadata), timeout=180)
                duration = probe(ffprobe, audio, paragraph_dir / "ffprobe-receipt.json")
                row = {"chapter_id": chapter["id"], "paragraph_index": piece["index"],
                       "source_paragraph_sha256": piece["source_sha256"],
                       "text_sha256": piece["text_sha256"], "characters": piece["characters"],
                       "duration_seconds": duration, "request": identity(request), "audio": identity(audio),
                       "response_events": identity(metadata),
                       "probe": identity(paragraph_dir / "ffprobe-receipt.json")}
                paragraph_rows.append(row)
                manifest["paragraphs"].append(row)
                write_json_new(out / f"manifest-after-paragraph-{len(manifest['paragraphs']):02d}.json",
                               {**manifest, "status": "partial"})
                event(events, "paragraph_completed", chapter=chapter["id"], index=piece["index"],
                      seconds=duration, audio_sha256=row["audio"]["sha256"])
            chapter_audio, list_file, concat_receipt = concat(ffmpeg, chapter_dir, len(paragraph_rows))
            chapter_duration = probe(ffprobe, chapter_audio, chapter_dir / "chapter-ffprobe-receipt.json")
            manifest["chapters"].append({"id": chapter["id"], "title": chapter["title"],
                                         "budget_seconds": chapter["budget_seconds"],
                                         "paragraph_count": len(paragraph_rows),
                                         "text_sha256": chapter["text_sha256"],
                                         "speech_seconds": chapter_duration,
                                         "paragraph_seconds_sum": round(sum(row["duration_seconds"] for row in paragraph_rows), 3),
                                         "audio": identity(chapter_audio), "concat_input": identity(list_file),
                                         "concat_receipt": identity(concat_receipt),
                                         "probe": identity(chapter_dir / "chapter-ffprobe-receipt.json")})
            event(events, "chapter_completed", chapter=chapter["id"], seconds=chapter_duration)
        report = {"schema": "ck3.episode02.selected-narration-duration-report.v1",
                  "status": "selected-chapters-rendered-not-human-reviewed",
                  "draft_sha256": plan["draft"]["sha256"],
                  "selected_chapters": plan["selected_chapters"], "held_chapters": plan["held_chapters"],
                  "voice": VOICE, "rate": RATE,
                  "chapters": [{"id": row["id"], "speech_seconds": row["speech_seconds"],
                                "budget_seconds": row["budget_seconds"],
                                "budget_minus_speech_seconds": round(row["budget_seconds"] - row["speech_seconds"], 3),
                                "paragraph_count": row["paragraph_count"], "audio": row["audio"]}
                               for row in manifest["chapters"]],
                  "selected_speech_seconds": round(sum(row["speech_seconds"] for row in manifest["chapters"]), 3),
                  "limits": ["EdgeTTS edit proxy, not final IndexTTS voice or human signoff.",
                             "Terminal and closing chapters are intentionally held for E2-09 fact correction.",
                             "New live CK3 attempts require their own source cards and number verification."]}
        write_json_new(out / "duration-report.json", report)
        manifest["duration_report"] = identity(out / "duration-report.json")
        manifest["status"] = "selected-chapters-rendered-not-human-reviewed"
    except Exception:
        manifest["status"] = "red-preserved"
        manifest["error"] = traceback.format_exc()
        event(events, "attempt_red", error=manifest["error"])
        raise
    finally:
        manifest["finished_utc"] = now()
        manifest["attempt_events"] = identity(events)
        write_json_new(out / "manifest-final.json", manifest)
    print(json.dumps({"manifest": str(out / "manifest-final.json"),
                      "chapters": [{"id": x["id"], "seconds": x["speech_seconds"]}
                                   for x in manifest["chapters"]]}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chapters", nargs="+", choices=CHAPTER_IDS, required=True)
    parser.add_argument("--expected-draft-sha256", required=True)
    parser.add_argument("--toolchain-version", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--wheel-file", type=Path, required=True)
    parser.add_argument("--release-receipt", type=Path, required=True)
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    selected = tuple(args.chapters)
    if len(set(selected)) != len(selected) or selected != tuple(x for x in CHAPTER_IDS if x in selected):
        raise ValueError("chapters must be unique and in ProjectConfig order")
    plan = parse_draft(args.draft, selected)
    if plan["draft"]["sha256"] != args.expected_draft_sha256.upper():
        raise ValueError("draft SHA differs from frozen selected bytes")
    wheel, ffprobe, ffmpeg = validate_inputs(args)
    if args.plan_only:
        print(json.dumps({"draft": plan["draft"], "selected_chapters": list(selected),
                          "held_chapters": plan["held_chapters"],
                          "paragraphs": {chapter["id"]: [{"characters": x["characters"],
                                                             "text_sha256": x["text_sha256"]}
                                                            for x in chapter["paragraphs"]]
                                         for chapter in plan["chapters"] if chapter["selected"]},
                          "chapter_text_sha256": {chapter["id"]: chapter["text_sha256"]
                                                  for chapter in plan["chapters"] if chapter["selected"]},
                          "wheel": wheel, "ffprobe": str(ffprobe), "ffmpeg": str(ffmpeg)}, ensure_ascii=False))
        return
    asyncio.run(render(args, plan, wheel, ffprobe, ffmpeg))


if __name__ == "__main__":
    main()
