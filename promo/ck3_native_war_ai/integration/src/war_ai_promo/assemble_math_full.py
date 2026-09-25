"""Assemble the native-order EdgeTTS long cut from immutable source attempts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from war_ai_promo.captions import subtitle_document


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def run(argv: list[str], logs: Path, label: str) -> None:
    (logs / f"{label}.argv.json").write_text(json.dumps(argv, indent=2) + "\n", encoding="utf-8")
    with (logs / f"{label}.stdout").open("xb") as stdout, (logs / f"{label}.stderr").open("xb") as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False)
    if result.returncode:
        raise RuntimeError(f"{label} returned {result.returncode}: " +
                           (logs / f"{label}.stderr").read_text(encoding="utf-8", errors="replace")[-2000:])


def probe(path: Path) -> dict:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                             "-show_chapters", "-of", "json", str(path)], check=True, capture_output=True)
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--observation-speech", type=Path,
                        help="prepared speech when stored in a separate immutable attempt")
    parser.add_argument("--math", type=Path, required=True)
    parser.add_argument("--casualty", type=Path,
                        help="optional immutable casualty-chain addendum attempt")
    parser.add_argument("--pursuit-detail", type=Path,
                        help="optional immutable C12 pursuit arithmetic attempt")
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--output-name", required=True)
    parser.add_argument("--correct-gameplay-captions", action="store_true",
                        help="rerender gameplay segments from an older observation build")
    args = parser.parse_args()
    attempt = args.attempt.resolve()
    observation = args.observation.resolve(strict=True)
    observation_speech = (args.observation_speech or observation / "speech").resolve(strict=True)
    math = args.math.resolve(strict=True)
    casualty = args.casualty.resolve(strict=True) if args.casualty else None
    pursuit_detail = args.pursuit_detail.resolve(strict=True) if args.pursuit_detail else None
    if pursuit_detail and not casualty:
        parser.error("--pursuit-detail requires --casualty")
    music = args.music.resolve(strict=True)
    if Path(args.output_name).name != args.output_name or not args.output_name.lower().endswith(".mp4"):
        parser.error("--output-name must be one MP4 basename")
    if attempt.exists():
        if not (attempt / "run" / "run-manifest.json").is_file() or any(
            (attempt / name).exists() for name in ("logs", "edit-list.json", "segments.json")
        ):
            parser.error("attempt already started; preserve old attempts and select a new path")
    else:
        attempt.mkdir(parents=True)
    logs = attempt / "logs"
    logs.mkdir()

    observation_inputs = json.loads((observation_speech / "production-inputs.json").read_text(encoding="utf-8"))
    math_inputs = json.loads((math / "speech" / "production-inputs.json").read_text(encoding="utf-8"))
    casualty_inputs = (json.loads((casualty / "speech" / "production-inputs.json").read_text(encoding="utf-8"))
                       if casualty else None)
    pursuit_detail_inputs = (json.loads((pursuit_detail / "speech" / "production-inputs.json").read_text(encoding="utf-8"))
                             if pursuit_detail else None)
    observation_rows = {row["id"]: row for row in observation_inputs["cues"]}
    math_rows = {row["id"]: row for row in math_inputs["cues"]}
    casualty_rows = ({row["id"]: row for row in casualty_inputs["cues"]}
                     if casualty_inputs else {})
    detail_rows = ({row["id"]: row for row in pursuit_detail_inputs["cues"]}
                   if pursuit_detail_inputs else {})
    casualty_ids = ([f"C{i:02d}" for i in range(1, 11)] +
                    (["C12"] if pursuit_detail else []) + ["C11"] if casualty else [])
    ordered_ids = ([f"E1-F{i:02d}" for i in range(1, 11)] +
                   [f"M{i:02d}" for i in range(2, 8)] +
                   [f"E1-F{i:02d}" for i in range(13, 16)] + ["M08"] +
                   casualty_ids +
                   [f"E1-F{i:02d}" for i in range(16, 26)])
    assert len(ordered_ids) == (30 + len(casualty_ids)) and len(set(ordered_ids)) == len(ordered_ids)
    rows = [observation_rows.get(cue_id) or math_rows.get(cue_id) or casualty_rows.get(cue_id) or detail_rows[cue_id]
            for cue_id in ordered_ids]
    for row in rows:
        for key in ("zh", "en", "visual_title"):
            if any(term in row[key] for term in ("旧顺序", "旧乘法", "old order", "样稿")):
                raise ValueError(f"historical comparison or pilot wording in {row['id']} {key}")
    (attempt / "edit-list.json").write_text(json.dumps({"schema": "ck3-war-ai-edge-math-full-edit.v1",
        "source_observation": str(observation), "source_observation_speech": str(observation_speech),
        "source_math": str(math), "source_casualty": str(casualty) if casualty else None,
        "source_pursuit_detail": str(pursuit_detail) if pursuit_detail else None,
        "cue_ids": ordered_ids,
        "policy": "native CK3 calculation only; no old-order comparisons"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # The older observation attempt predates hybrid gameplay/card caption positioning.
    # New observation builds already use the current caption renderer.
    corrected = {}
    for cue_id in ordered_ids if args.correct_gameplay_captions else ():
        row = observation_rows.get(cue_id)
        if row is None or row.get("visual_kind") != "gameplay":
            continue
        corrected_ass = attempt / f"{cue_id}-corrected.ass"
        corrected_ass.write_text(subtitle_document(row), encoding="utf-8")
        command = json.loads((observation / "build" / "audit" / "segments" / cue_id / "render" / "command.json").read_text(encoding="utf-8"))["argv"]
        corrected_mp4 = attempt / f"{cue_id}-corrected.mp4"
        filter_index = command.index("-filter_complex") + 1
        ass_path = corrected_ass.as_posix().replace(":", r"\:")
        command[filter_index], count = re.subn(r"ass=filename='[^']+'", lambda _: f"ass=filename='{ass_path}'", command[filter_index])
        if count != 1:
            raise ValueError(f"could not locate original {cue_id} subtitle filter")
        command[-1] = str(corrected_mp4)
        run(command, logs, f"01-correct-{cue_id}")
        corrected[cue_id] = corrected_mp4

    segments = []
    chapters = []
    elapsed_ms = 0
    for index, cue_id in enumerate(ordered_ids):
        if cue_id in corrected:
            source = corrected[cue_id]
        elif cue_id.startswith("M"):
            source = math / "build" / "segments" / f"{int(cue_id[1:]):04d}-{cue_id}.mp4"
        elif cue_id.startswith("C"):
            source_attempt = pursuit_detail if cue_id == "C12" else casualty
            assert source_attempt is not None
            source_index = 1 if cue_id == "C12" else int(cue_id[1:])
            source = source_attempt / "build" / "segments" / f"{source_index:04d}-{cue_id}.mp4"
        else:
            source = observation / "build" / "segments" / f"{int(cue_id[-2:]):04d}-{cue_id}.mp4"
        source.resolve(strict=True)
        info = probe(source)
        duration_ms = round(float(info["format"]["duration"]) * 1000)
        if duration_ms <= 0:
            raise ValueError(f"empty segment {cue_id}")
        segments.append({"cue_id": cue_id, "source": str(source), "bytes": source.stat().st_size,
                         "sha256": digest(source), "duration_ms": duration_ms,
                         "start_ms": elapsed_ms, "end_ms": elapsed_ms + duration_ms})
        chapters.append((elapsed_ms, elapsed_ms + duration_ms, cue_id + " " + rows[index]["shot_title"]))
        elapsed_ms += duration_ms
    duration = elapsed_ms / 1000
    if not 1200 <= duration <= 2400:
        raise ValueError(f"full cut duration {duration:.3f}s outside 20–40 minutes")
    (attempt / "segments.json").write_text(json.dumps(segments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    concat = attempt / "concat-inputs.txt"
    concat.write_text("".join("file '" + entry["source"].replace("\\", "/").replace("'", "'\\''") + "'\n" for entry in segments), encoding="utf-8")
    ffmeta = attempt / "chapters.ffmeta"
    ffmeta.write_text(";FFMETADATA1\n" + "".join(
        f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={start}\nEND={end}\ntitle={title}\n"
        for start, end, title in chapters), encoding="utf-8")
    unmixed = attempt / "episode-01-native-math-full-unmixed.mp4"
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-f", "concat",
         "-safe", "0", "-i", str(concat), "-f", "ffmetadata", "-i", str(ffmeta),
         "-map", "0:v:0", "-map", "0:a:0", "-map_chapters", "1", "-c", "copy",
         "-movflags", "+faststart", str(unmixed)], logs, "02-concat")
    output = attempt / args.output_name
    run([sys.executable, "-m", "war_ai_promo.theme_mix", "--film", str(unmixed),
         "--music", str(music), "--output", str(output), "--work-directory", str(attempt / "theme-mix"),
         "--music-gain-db=-17"], logs, "03-theme-mix")
    run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(output), "-f", "null", "NUL"], logs, "04-full-decode")
    result = probe(output)
    actual = float(result["format"]["duration"])
    if abs(actual - duration) > 0.1 or len(result["chapters"]) != len(ordered_ids):
        raise ValueError("final duration or chapter count mismatch")
    receipt = {"schema": "ck3-war-ai-edge-math-full-build.v1", "state": "ready-for-onedrive-before-machine-review",
               "output": str(output), "output_bytes": output.stat().st_size, "output_sha256": digest(output),
               "duration_seconds": actual, "cue_count": len(ordered_ids), "chapter_count": len(result["chapters"]),
               "observation_inputs_sha256": digest(observation_speech / "production-inputs.json"),
               "math_inputs_sha256": digest(math / "speech" / "production-inputs.json"),
               "casualty_inputs_sha256": (digest(casualty / "speech" / "production-inputs.json")
                                          if casualty else None),
               "pursuit_detail_inputs_sha256": (digest(pursuit_detail / "speech" / "production-inputs.json")
                                                if pursuit_detail else None),
               "music_sha256": digest(music), "human_signoff": "not-provided"}
    (attempt / "build-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
