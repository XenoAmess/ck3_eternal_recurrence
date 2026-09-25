"""Build the user's-voice R7F film from an immutable optimized IndexTTS attempt."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from .index_revoice import binding
from .produce_r7e_same_battle import SOURCE_SHA, MUSIC_SHA, command, digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--synthesis", type=Path, required=True)
    parser.add_argument("--toolchain-version", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--output-name", required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve(strict=True)
    manifest = args.manifest.resolve(strict=True)
    speech = attempt / "speech"
    inputs_path = speech / "production-inputs.json"
    if not inputs_path.is_file():
        raise FileNotFoundError("R7F IndexTTS production inputs missing")
    if any((attempt / name).exists() for name in ("automation", "build", "theme-mix", "build-receipt.json")):
        raise FileExistsError("R7F production already started; use a new attempt")
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    rows = inputs["cues"]
    if len(rows) != 23 or inputs["provider"] != "index" or not 1200 <= inputs["actual_duration_seconds"] <= 2400:
        raise ValueError("Expected 23 IndexTTS cues of 20–40 minutes")
    frozen = json.loads(args.script.read_text(encoding="utf-8"))["cues"]
    if len(frozen) != len(rows) or any(
        original["id"] != prepared["id"] or
        any(original[key] != prepared[key] for key in
            ("zh", "en", "visual_title", "visual_lines", "source_time_seconds", "target_time_seconds"))
        for original, prepared in zip(frozen, rows)
    ):
        raise ValueError("IndexTTS speech inputs do not match frozen R7E text and visuals")
    if args.output_name != Path(args.output_name).name or not args.output_name.lower().endswith(".mp4"):
        raise ValueError("Output name must be a single MP4 basename")
    if len(args.wheel_sha256) != 64:
        raise ValueError("Invalid selected wheel SHA")
    int(args.wheel_sha256, 16)
    source = args.source.resolve(strict=True)
    music = args.music.resolve(strict=True)
    reference = args.reference.resolve(strict=True)
    synthesis = args.synthesis.resolve(strict=True)
    if digest(source) != SOURCE_SHA or digest(music) != MUSIC_SHA:
        raise ValueError("Original game video or unique series music changed")
    if binding(reference) != inputs["index_voice"]["reference"]:
        raise ValueError("User reference voice changed")
    if binding(synthesis) != inputs["index_voice"]["synthesis_receipt"]:
        raise ValueError("IndexTTS synthesis receipt changed")
    cli = [sys.executable, "-m", "xar_promo"]
    version = subprocess.run(cli + ["--version"], capture_output=True, text=True, check=True).stdout.strip()
    if version != "xar-promo " + args.toolchain_version:
        raise ValueError(f"Installed xar-promo {version} differs from selected formal release")
    logs = attempt / "automation"
    logs.mkdir()
    sources = [
        ("r7f-production-inputs", inputs_path, "derived", "production-inputs"),
        ("r7e-frozen-script", args.script.resolve(strict=True), "raw", "script"),
        ("r7e-frozen-timeline", args.timeline.resolve(strict=True), "raw", "timeline"),
        ("messina-original-900s-film", source, "raw", "original-CK3-gameplay"),
        ("series-theme-master", music, "raw", "theme"),
        ("user-index-reference", reference, "raw", "voice-reference"),
        ("index-synthesis-completed", synthesis, "raw", "TTS-synthesis-receipt"),
    ]
    for row in rows:
        audio = Path(row["audio"]["path"])
        if binding(audio) != row["audio"]:
            raise ValueError(f"Audio changed before preserve: {row['id']}")
        sources.extend([
            ("audio." + row["id"], audio, "raw", "optimized-IndexTTS-audio"),
            ("tts-request." + row["id"], audio.with_suffix(".request.json"),
             "raw", "TTS-request"),
            ("tts-receipt." + row["id"], audio.with_suffix(".receipt.json"),
             "raw", "TTS-receipt"),
        ])
    for index, (identifier, item, collection, role) in enumerate(sources):
        command(cli + ["preserve", "--run-manifest", str(manifest),
                       "--artifact-id", identifier, "--collection", collection,
                       "--role", role, str(item.resolve(strict=True))],
                logs, f"preserve-{index:02d}")
        print(f"Preserved {index + 1}/{len(sources)}: {identifier}", flush=True)
    command(cli + ["validate", "--profile", "authoring", str(manifest)], logs, "validate")
    print("Frozen R7E script and optimized IndexTTS speech preserved; building R7F", flush=True)
    command(cli + ["build", str(manifest), "--workdir", str(attempt / "build"),
                   "--composer", "war_ai_promo.episode_one_r7f_index_same_battle:compose", "--offline-tts"],
            logs, "build")
    candidates = list((attempt / "build").rglob("episode-01-r7f-index-unmixed.mp4"))
    if len(candidates) != 1:
        raise ValueError(f"Expected one R7F unmixed film; got {len(candidates)}")
    unmixed = candidates[0]
    mixed = attempt / "episode-01-r7f-index-theme-mixed-before-chapters.mp4"
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
        "schema": "ck3-war-ai-episode-01-r7f-index-formal-build.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "ready-for-onedrive-before-machine-review",
        "output": str(output), "output_bytes": output.stat().st_size,
        "output_sha256": digest(output), "cue_count": len(rows),
        "chapter_count": len(result["chapters"]),
        "duration_seconds": float(result["format"]["duration"]),
        "source_video_sha256": SOURCE_SHA, "source_combat_id": 16777218,
        "source_run_manifest": str(manifest),
        "toolchain_version": version,
        "toolchain_wheel_sha256": args.wheel_sha256.lower(),
        "narration_provider": "IndexTTS 2.5", "user_reference_sha256": digest(reference),
        "index_revision": inputs["index_voice"]["model_revision"],
        "index_profile": inputs["index_voice"]["profile"],
        "synthesis_receipt_sha256": digest(synthesis),
        "theme_gain_db": -17, "theme_sha256": MUSIC_SHA,
        "palette": "Episode 0 brown and gold: BG #211813, PANEL #35291F, GOLD #CBA56A",
        "human_signoff": "not-provided",
    }
    (attempt / "build-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
