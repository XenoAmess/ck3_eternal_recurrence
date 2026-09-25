"""Preserve and produce the Episode 0 brown-and-gold R7D Messina film."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


SOURCE_SHA = "0e7699911b05ec54acc852c6fcb31cb77e32d1de5bca8ba2a6fd054c3903589f"
MUSIC_SHA = "fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def command(argv: list[str], logs: Path, label: str) -> str:
    (logs / (label + ".argv.json")).write_text(
        json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--toolchain-version", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--output-name", required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve(strict=True)
    manifest = args.manifest.resolve(strict=True)
    speech = attempt / "speech"
    inputs_path = speech / "production-inputs.json"
    if not inputs_path.is_file():
        raise FileNotFoundError("R7 speech inputs missing")
    if any((attempt / name).exists() for name in ("automation", "build", "theme-mix", "build-receipt.json")):
        raise FileExistsError("R7 production already started; use a new attempt")
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    rows = inputs["cues"]
    if len(rows) != 23 or inputs["provider"] != "edge" or not 1200 <= inputs["actual_duration_seconds"] <= 2400:
        raise ValueError("Expected 23 EdgeTTS cues of 20–40 minutes")
    if args.output_name != Path(args.output_name).name or not args.output_name.lower().endswith(".mp4"):
        raise ValueError("Output name must be a single MP4 basename")
    if len(args.wheel_sha256) != 64:
        raise ValueError("Invalid selected wheel SHA")
    int(args.wheel_sha256, 16)
    source = args.source.resolve(strict=True)
    music = args.music.resolve(strict=True)
    if digest(source) != SOURCE_SHA or digest(music) != MUSIC_SHA:
        raise ValueError("Original game video or series music changed")
    cli = [sys.executable, "-m", "xar_promo"]
    version = subprocess.run(cli + ["--version"], capture_output=True, text=True, check=True).stdout.strip()
    if version != "xar-promo " + args.toolchain_version:
        raise ValueError(f"Installed xar-promo {version} differs from selected release")
    logs = attempt / "automation"
    logs.mkdir()
    sources = [
        ("r7-production-inputs", inputs_path, "derived", "production-inputs"),
        ("r7d-script", args.script.resolve(strict=True), "raw", "script"),
        ("r7d-timeline", args.timeline.resolve(strict=True), "raw", "timeline"),
        ("messina-original-900s-film", source, "raw", "original-CK3-gameplay"),
        ("series-theme-master", music, "raw", "theme"),
    ]
    sources += [("audio." + row["id"], speech / (row["id"] + ".mp3"),
                 "raw", "EdgeTTS-audio") for row in rows]
    for index, (identifier, item, collection, role) in enumerate(sources):
        command(cli + ["preserve", "--run-manifest", str(manifest),
                       "--artifact-id", identifier, "--collection", collection,
                       "--role", role, str(item.resolve(strict=True))],
                logs, f"preserve-{index:02d}")
        print(f"Preserved {index + 1}/{len(sources)}: {identifier}", flush=True)
    command(cli + ["validate", "--profile", "authoring", str(manifest)], logs, "validate")
    print("Source and narration preserved; building exact-video paired film", flush=True)
    command(cli + ["build", str(manifest), "--workdir", str(attempt / "build"),
                   "--composer", "war_ai_promo.episode_one_r7d_same_battle:compose", "--offline-tts"],
            logs, "build")
    candidates = list((attempt / "build").rglob("episode-01-r7d-messina-unmixed.mp4"))
    if len(candidates) != 1:
        raise ValueError(f"Expected one R7 unmixed film; got {len(candidates)}")
    unmixed = candidates[0]
    mixed = attempt / "episode-01-r7d-theme-mixed-before-chapters.mp4"
    command([sys.executable, "-m", "war_ai_promo.theme_mix", "--film", str(unmixed),
             "--music", str(music), "--output", str(mixed),
             "--work-directory", str(attempt / "theme-mix"), "--music-gain-db=-17"],
            logs, "theme-mix")
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
        raise ValueError("Final chapter count or duration mismatch")
    command(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(output),
             "-f", "null", "NUL"], logs, "full-decode")
    receipt = {
        "schema": "ck3-war-ai-episode-01-r7d-build.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "ready-for-onedrive-before-machine-review",
        "output": str(output), "output_bytes": output.stat().st_size,
        "output_sha256": digest(output), "cue_count": len(rows),
        "chapter_count": len(result["chapters"]),
        "duration_seconds": float(result["format"]["duration"]),
        "source_video_sha256": SOURCE_SHA,
        "source_combat_id": 16777218,
        "source_run_manifest": str(manifest),
        "toolchain_version": version,
        "toolchain_wheel_sha256": args.wheel_sha256.lower(),
        "narration_provider": "edge-tts", "voice": "zh-CN-XiaoxiaoNeural", "rate": "-12%",
        "theme_gain_db": -17, "theme_sha256": MUSIC_SHA,
        "palette": "Episode 0 brown and gold: BG #211813, PANEL #35291F, GOLD #CBA56A; blank brown subtitle strip",
        "human_signoff": "not-provided",
    }
    (attempt / "build-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
