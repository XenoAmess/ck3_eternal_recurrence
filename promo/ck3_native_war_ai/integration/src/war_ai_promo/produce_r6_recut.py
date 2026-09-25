"""Preserve, render and mix the 32-cue Episode 1 R6 EdgeTTS recut."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .episode_one_r6_recut import NEW_CARDS


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def command(argv: list[str], logs: Path, label: str) -> str:
    (logs / (label + ".argv.json")).write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (logs / (label + ".stdout")).open("xb") as stdout, (logs / (label + ".stderr")).open("xb") as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}): " +
                           (logs / (label + ".stderr")).read_text(encoding="utf-8", errors="replace")[-3000:])
    return (logs / (label + ".stdout")).read_text(encoding="utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--math", type=Path, required=True)
    parser.add_argument("--casualty", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--toolchain-version", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--output-name", required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve(strict=True)
    speech = attempt / "speech"
    inputs_path = speech / "production-inputs.json"
    if not inputs_path.is_file() or not args.manifest.is_file():
        raise FileNotFoundError("Speech inputs or xar-promo run manifest missing")
    if any((attempt / name).exists() for name in ("automation", "build", "theme-mix", "build-receipt.json")):
        raise FileExistsError("R6 production already started; use a new attempt")
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    rows = inputs["cues"]
    if len(rows) not in (32, 33) or inputs["provider"] != "edge":
        raise ValueError("Expected 32 or 33 EdgeTTS cues")
    if args.output_name != Path(args.output_name).name or not args.output_name.lower().endswith(".mp4"):
        raise ValueError("Output name must be a single MP4 basename")
    if len(args.wheel_sha256) != 64:
        raise ValueError("Invalid wheel SHA")
    int(args.wheel_sha256, 16)
    cli = [sys.executable, "-m", "xar_promo"]
    version = subprocess.run(cli + ["--version"], capture_output=True, text=True, check=True).stdout.strip()
    if version != "xar-promo " + args.toolchain_version:
        raise ValueError(f"Installed toolchain {version} differs from selected release")
    if digest(args.music.resolve(strict=True)) != "fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f":
        raise ValueError("Series theme bytes changed")
    logs = attempt / "automation"
    logs.mkdir()
    manifest = args.manifest.resolve(strict=True)
    sources = [
        ("r6-production-inputs", inputs_path, "derived", "production-inputs"),
        ("r6-script", args.script.resolve(strict=True), "raw", "script"),
        ("r6-timeline", args.timeline.resolve(strict=True), "raw", "timeline"),
        ("series-theme-master", args.music.resolve(strict=True), "raw", "theme"),
    ]
    for row in rows:
        cue_id = row["id"]
        sources.append(("audio." + cue_id, speech / (cue_id + ".mp3"), "raw", "EdgeTTS-audio"))
        if cue_id in NEW_CARDS or row.get("redraw_card"):
            continue
        original = (args.observation if cue_id.startswith("E1-") else
                    args.math if cue_id.startswith("M") else args.casualty)
        sources.append(("source-visual." + cue_id, original / "build" / "visuals" / (cue_id + ".mp4"),
                        "raw", "frozen-source-visual"))
    for index, (identifier, source, collection, role) in enumerate(sources):
        source = source.resolve(strict=True)
        command(cli + ["preserve", "--run-manifest", str(manifest),
                       "--artifact-id", identifier, "--collection", collection,
                       "--role", role, str(source)], logs, f"preserve-{index:02d}")
        print(f"Preserved {index + 1}/{len(sources)}: {identifier}", flush=True)
    command(cli + ["validate", "--profile", "authoring", str(manifest)], logs, "validate")
    command(cli + ["build", str(manifest), "--workdir", str(attempt / "build"),
                   "--composer", "war_ai_promo.episode_one_r6_recut:compose", "--offline-tts"], logs, "build")
    candidates = list((attempt / "build").rglob("episode-01-r6-unmixed.mp4"))
    if len(candidates) != 1:
        raise ValueError(f"Expected one unmixed film; found {len(candidates)}")
    unmixed = candidates[0]
    mixed = attempt / "episode-01-mixed-before-chapters.mp4"
    command([sys.executable, "-m", "war_ai_promo.theme_mix", "--film", str(unmixed),
             "--music", str(args.music.resolve(strict=True)), "--output", str(mixed),
             "--work-directory", str(attempt / "theme-mix"), "--music-gain-db=-17"], logs, "theme-mix")
    chapters = attempt / "chapters.ffmeta"
    elapsed = 0
    parts = [";FFMETADATA1\n"]
    for row in rows:
        end = elapsed + round(row["duration_seconds"] * 1000)
        parts.append(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={elapsed}\nEND={end}\n"
                     f"title={row['id']} {row['shot_title']}\n")
        elapsed = end
    chapters.write_text("".join(parts), encoding="utf-8")
    output = attempt / args.output_name
    command(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
             "-i", str(mixed), "-f", "ffmetadata", "-i", str(chapters),
             "-map", "0:v:0", "-map", "0:a:0", "-map_chapters", "1", "-c", "copy",
             "-movflags", "+faststart", str(output)], logs, "chapters")
    result = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_chapters",
                                        "-of", "json", str(output)], capture_output=True, check=True).stdout)
    if len(result.get("chapters", [])) != len(rows) or abs(float(result["format"]["duration"]) * 1000 - elapsed) > 150:
        raise ValueError("Final chapter count or film duration mismatch")
    command(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(output),
             "-f", "null", "NUL"], logs, "full-decode")
    receipt = {
        "schema": "ck3-war-ai-episode-01-r6-build.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "ready-for-onedrive-before-machine-review",
        "output": str(output), "output_bytes": output.stat().st_size,
        "output_sha256": digest(output), "cue_count": len(rows),
        "chapter_count": len(result["chapters"]),
        "duration_seconds": inputs["actual_duration_seconds"],
        "source_run_manifest": str(manifest),
        "toolchain_version": version,
        "toolchain_wheel_sha256": args.wheel_sha256.lower(),
        "narration_provider": "edge-tts", "voice": "zh-CN-XiaoxiaoNeural", "rate": "-12%",
        "theme_gain_db": -17, "theme_sha256": digest(args.music),
        "human_signoff": "not-provided",
    }
    (attempt / "build-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
