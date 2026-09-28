"""Preserve a few episode-02 EdgeTTS samples in a new external attempt.

The samples are timing probes. They are not narration approval or a finished edit.
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

from audit_narration_budget import HEADER, identity, spoken_text


VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-12%"
SELECTION = (("opening", 0, 0), ("pursuit", 1, 2), ("reinforcement", 3, 3), ("terminal", 4, 4))


def paragraphs(draft: str, chapter_index: int) -> list[str]:
    headings = list(HEADER.finditer(draft))
    heading = headings[chapter_index]
    block = draft[heading.end():headings[chapter_index + 1].start() if chapter_index + 1 < len(headings) else len(draft)]
    start = block.index("**旁白**：") + len("**旁白**：")
    end = block.index("**录制缺口**", start)
    return [value.strip() for value in re.split(r"\n\s*\n", block[start:end]) if value.strip()]


def probe(media: Path, ffprobe: str) -> tuple[float, str]:
    command = [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(media)]
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    return float(json.loads(result.stdout)["format"]["duration"]), result.stdout


async def render(text: str, media: Path, events: Path) -> None:
    communicator = edge_tts.Communicate(text=text, voice=VOICE, rate=RATE)
    with media.open("xb") as audio, events.open("x", encoding="utf-8") as timing:
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            else:
                timing.write(json.dumps(chunk, ensure_ascii=False) + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    draft_bytes = args.draft.read_bytes()
    draft = draft_bytes.decode("utf-8-sig")
    snapshot = args.output / "narration-script-draft.md"
    with snapshot.open("xb") as stream:
        stream.write(draft_bytes)
    result = {
        "schema": "ck3.episode02.tts-samples.v1",
        "status": "started",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_draft": identity(args.draft),
        "snapshot": identity(snapshot),
        "interpreter": sys.executable,
        "python": sys.version,
        "versions": {"edge-tts": importlib.metadata.version("edge-tts"),
                     "xar-promo-toolchain": importlib.metadata.version("xar-promo-toolchain")},
        "provider": "edge-tts",
        "voice": VOICE,
        "rate": RATE,
        "samples": [],
    }
    manifest = args.output / "manifest.json"
    try:
        for name, chapter_index, paragraph_index in SELECTION:
            source = paragraphs(draft, chapter_index)[paragraph_index]
            text = spoken_text(source)
            if "[^" in text or "`" in text or "**" in text:
                raise ValueError(f"unstripped source marker in {name}")
            target = args.output / name
            target.mkdir(exist_ok=False)
            request = target / "request.json"
            request.write_text(json.dumps({"source_paragraph_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest().upper(),
                                           "text": text, "voice": VOICE, "rate": RATE,
                                           "provider": "edge-tts", "edge_tts_version": result["versions"]["edge-tts"]},
                                          ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            media, events = target / "response.mp3", target / "response-events.jsonl"
            await asyncio.wait_for(render(text, media, events), timeout=120)
            duration, probe_stdout = probe(media, args.ffprobe)
            probe_file = target / "ffprobe.json"
            probe_file.write_text(probe_stdout, encoding="utf-8")
            result["samples"].append({"name": name, "chapter_index": chapter_index,
                                      "paragraph_index": paragraph_index, "duration_seconds": round(duration, 3),
                                      "request": identity(request), "audio": identity(media),
                                      "events": identity(events), "probe": identity(probe_file)})
            result["status"] = "partial"
            manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["status"] = "samples-rendered-not-human-reviewed"
    except Exception:
        result["status"] = "red-preserved"
        result["error"] = traceback.format_exc()
        raise
    finally:
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest), "samples": [{"name": x["name"], "seconds": x["duration_seconds"]}
                                                         for x in result["samples"]]}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
