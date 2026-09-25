"""Make a new R7 derivative with a clear subtitle strip and original audio."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def parse_time(value: str) -> int:
    hours, minutes, rest = value.split(":")
    seconds, centiseconds = rest.split(".")
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 100 + int(centiseconds)


def format_time(value: int) -> str:
    seconds, centiseconds = divmod(value, 100)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"


def combine_subtitles(rows: list[dict], subtitle_directory: Path, output: Path) -> None:
    header = None
    events = []
    elapsed_ms = 0
    for index, row in enumerate(rows, 1):
        path = subtitle_directory / f"{index:04d}-{row['id']}.ass"
        document = path.read_text(encoding="utf-8-sig")
        intro, event_block = document.split("[Events]\n", 1)
        event_lines = event_block.splitlines()
        if not event_lines[0].startswith("Format:"):
            raise ValueError(f"Missing ASS event format: {path}")
        if header is None:
            header = intro + "[Events]\n" + event_lines[0] + "\n"
        elif intro.split("[V4+ Styles]\n", 1)[1] != first_styles:
            raise ValueError(f"Inconsistent ASS styles: {path}")
        if index == 1:
            first_styles = intro.split("[V4+ Styles]\n", 1)[1]
        for line in event_lines[1:]:
            if not line.startswith("Dialogue: "):
                continue
            values = line[len("Dialogue: "):].split(",", 9)
            if len(values) != 10:
                raise ValueError(f"Invalid ASS event: {path}")
            offset_cs = round(elapsed_ms / 10)
            values[1] = format_time(parse_time(values[1]) + offset_cs)
            values[2] = format_time(parse_time(values[2]) + offset_cs)
            events.append("Dialogue: " + ",".join(values))
        elapsed_ms += round(row["duration_seconds"] * 1000)
    if header is None or len(events) < len(rows) * 2:
        raise ValueError("Combined ASS has too few events")
    output.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def command(argv: list[str], logs: Path, label: str, *, cwd: Path | None = None) -> None:
    (logs / f"{label}.argv.json").write_text(
        json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (logs / f"{label}.stdout").open("xb") as stdout, (logs / f"{label}.stderr").open("xb") as stderr:
        result = subprocess.run(argv, cwd=cwd, stdout=stdout, stderr=stderr, check=False)
    if result.returncode:
        raise RuntimeError(f"{label} failed {result.returncode}: " +
                           (logs / f"{label}.stderr").read_text(encoding="utf-8", errors="replace")[-4000:])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--source-attempt", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-name", required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve(strict=True)
    source_attempt = args.source_attempt.resolve(strict=True)
    original = json.loads((source_attempt / "build-receipt.json").read_text(encoding="utf-8"))
    source = Path(original["output"]).resolve(strict=True)
    if digest(source) != original["output_sha256"]:
        raise ValueError("R7 source film bytes changed")
    inputs = json.loads((source_attempt / "speech" / "production-inputs.json").read_text(encoding="utf-8"))
    rows = inputs["cues"]
    if len(rows) != 23 or original["chapter_count"] != 23:
        raise ValueError("Expected source with 23 chapters")
    if args.output_name != Path(args.output_name).name or not args.output_name.endswith(".mp4"):
        raise ValueError("Output name must be one MP4 basename")
    if (attempt / "automation").exists() or (attempt / args.output_name).exists():
        raise FileExistsError("Use a fresh repair attempt")
    logs = attempt / "automation"
    logs.mkdir()
    subtitles = attempt / "combined-subtitles.ass"
    combine_subtitles(rows, source_attempt / "build" / "subtitles", subtitles)
    cli = [sys.executable, "-m", "xar_promo"]
    manifest = args.manifest.resolve(strict=True)
    for label, identifier, path, collection, role in [
        ("preserve-source", "r7-source-uploaded-film", source, "raw", "source-deliverable"),
        ("preserve-subtitles", "r7-combined-subtitles", subtitles, "raw", "subtitle"),
    ]:
        command(cli + ["preserve", "--run-manifest", str(manifest), "--artifact-id", identifier,
                       "--collection", collection, "--role", role, str(path)], logs, label)
    command(cli + ["validate", "--profile", "authoring", str(manifest)], logs, "validate")
    output = attempt / args.output_name
    filter_graph = "drawbox=x=0:y=1127:w=iw:h=ih-1127:color=0x10151C:t=fill,ass=combined-subtitles.ass"
    command(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
             "-i", str(source), "-map", "0:v:0", "-map", "0:a:0", "-map_chapters", "0",
             "-vf", filter_graph, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
             "-threads", "8", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart",
             str(output)], logs, "render-clean-footer", cwd=attempt)
    measured = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-show_chapters",
         "-of", "json", str(output)], capture_output=True, check=True).stdout)
    if len(measured["chapters"]) != 23 or abs(float(measured["format"]["duration"]) - original["duration_seconds"]) > .15:
        raise ValueError("Clean derivative chapter/duration mismatch")
    command(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(output),
             "-f", "null", "NUL"], logs, "full-decode")
    receipt = {
        "schema": "ck3-war-ai-r7b-caption-overlap-repair.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "ready-for-onedrive-before-machine-review",
        "output": str(output), "output_bytes": output.stat().st_size,
        "output_sha256": digest(output), "duration_seconds": float(measured["format"]["duration"]),
        "cue_count": 23, "chapter_count": len(measured["chapters"]),
        "source_film_sha256": original["output_sha256"],
        "source_combat_id": original["source_combat_id"],
        "subtitle_document_sha256": digest(subtitles),
        "repair": "clear overlapping footer text and reapply identical Chinese/English ASS captions",
        "audio": "stream-copied from uploaded R7 source; theme mix unchanged",
        "human_signoff": "not-provided",
    }
    (attempt / "build-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
