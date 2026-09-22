"""Prepare actual per-cue speech, preserving requests, responses and timing."""
import argparse
import asyncio
from datetime import datetime, timezone
import math
from pathlib import Path
import shutil

from xar_promo.media import probe_media
from xar_promo.process import CommandSpec, run_command

from .common import binding, load, write_new


async def edge_cue(row, output, voice, rate):
    import edge_tts
    boundaries = []
    write_new(output.with_suffix(".request.json"), {"provider": "edge-tts", "voice": voice,
              "rate": rate, "text": row["zh"], "cue_id": row["id"]})
    try:
        with output.open("xb") as stream:
            async for event in edge_tts.Communicate(row["zh"], voice=voice, rate=rate).stream():
                if event["type"] == "audio":
                    stream.write(event["data"])
                else:
                    boundaries.append(event)
    except Exception as error:
        write_new(output.with_suffix(".failure.json"), {"type": type(error).__name__, "detail": str(error)})
        raise
    finally:
        write_new(output.with_suffix(".boundaries.json"), boundaries)


async def edge_batch(rows, output, voice, rate):
    """Retain failed takes and retry only their cue; keep the provider load small."""
    semaphore = asyncio.Semaphore(3)
    completed = 0

    async def prepare(row):
        nonlocal completed
        async with semaphore:
            attempts = output / "tts-attempts" / row["id"]
            attempts.mkdir(parents=True, exist_ok=False)
            for attempt in range(1, 4):
                take = attempts / f"attempt-{attempt:02d}.mp3"
                try:
                    await edge_cue(row, take, voice, rate)
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(attempt * 2)
            target = output / (row["id"] + ".mp3")
            for suffix in [".mp3", ".request.json", ".boundaries.json"]:
                with take.with_suffix(suffix).open("rb") as source, target.with_suffix(suffix).open("xb") as destination:
                    shutil.copyfileobj(source, destination)
            write_new(target.with_suffix(".take.json"), {"source": binding(take), "attempt": attempt})
            completed += 1
            print(f"Speech {completed}/{len(rows)}: {row['id']}", flush=True)

    await asyncio.gather(*(prepare(row) for row in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chapter", action="append")
    parser.add_argument("--provider", choices=["edge", "index"], required=True)
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--rate", default="-12%")
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--index-python", type=Path)
    parser.add_argument("--index-runner", type=Path)
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    args = parser.parse_args()
    script = load(args.script)
    shots = {row["id"]: row for row in load(args.timeline)["shots"]}
    rows = [dict(row) for row in script["cues"] if not args.chapter or row["chapter_id"] in args.chapter]
    if not rows or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Expected nonempty unique narration cues")
    if any(row["shot_id"] not in shots or not row["zh"].strip() or not row["en"].strip() for row in rows):
        raise ValueError("Unknown shot or missing bilingual narration")
    if args.provider == "index" and any(value is None or not value.is_file() for value in [args.reference, args.index_python, args.index_runner]):
        raise ValueError("IndexTTS needs the installed interpreter, batch runner and an explicit reference")
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.script, args.output / "narration-source.json")
    shutil.copyfile(args.timeline, args.output / "timeline-source.json")
    request = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "provider": args.provider,
               "script": binding(args.script), "timeline": binding(args.timeline), "chapter_selection": args.chapter,
               "reference": binding(args.reference) if args.reference else None,
               "voice": args.voice if args.provider == "edge" else "explicit-reference",
               "rate": args.rate if args.provider == "edge" else None}
    write_new(args.output / "request.json", request)
    suffix = ".mp3" if args.provider == "edge" else ".wav"
    if args.provider == "edge":
        asyncio.run(edge_batch(rows, args.output, args.voice, args.rate))
    else:
        batch = [{"id": row["id"], "text": row["zh"],
                  "output": str((args.output / (row["id"] + suffix)).resolve())} for row in rows]
        batch_file = args.output / "index-batch.json"
        write_new(batch_file, batch)
        run_command(CommandSpec.create([args.index_python, args.index_runner,
                    "--batch-file", batch_file, "--reference", args.reference, "--device", args.device],
                    label="IndexTTS documentary narration", cwd=args.index_runner.parent),
                    audit_directory=args.output / "index-command")
    for index, row in enumerate(rows):
        audio = args.output / (row["id"] + suffix)
        measured = probe_media("ffprobe", audio, audit_directory=args.output / "probe" / row["id"])
        duration = measured.require_duration()
        if not measured.audio_streams or duration <= .1:
            raise ValueError(f"No usable speech: {audio}")
        last_in_chapter = index == len(rows) - 1 or rows[index + 1]["chapter_id"] != row["chapter_id"]
        row.update({"audio": binding(audio), "audio_artifact_id": "audio." + row["id"],
                    "speech_duration_seconds": duration,
                    "duration_seconds": math.ceil((duration + (1.6 if last_in_chapter else .55)) * 30) / 30,
                    "shot_title": shots[row["shot_id"]]["title"]})
        if args.provider == "edge":
            row["sentence_boundaries"] = load(audio.with_suffix(".boundaries.json"))
    write_new(args.output / "production-inputs.json", {"format_version": 1,
              "media_scope": "teaching-graphics-radio-cut", "provider": args.provider, "cues": rows,
              "actual_duration_seconds": sum(row["duration_seconds"] for row in rows),
              "caption_timing": "Chinese provider sentence boundaries when available; English proportional sentence timing",
              "human_signoff": "not-provided", "music": "not-yet-added"})
    print(f"Prepared {len(rows)} cues, {sum(row['duration_seconds'] for row in rows):.2f} seconds", flush=True)


if __name__ == "__main__":
    main()
