"""Machine-check the IndexTTS Episode 1 candidate and bind its review frames."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from xar_promo.media import probe_and_write_bound_media


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def storyboard(rows: list[dict], actual: float) -> dict:
    cursor = 0.0
    chapters: list[dict] = []
    for row in rows:
        start = cursor
        cursor += row["duration_seconds"]
        if not chapters or chapters[-1]["id"] != row["chapter_id"]:
            chapters.append({"id": row["chapter_id"], "start_seconds": round(start, 6),
                             "end_seconds": 0.0, "boundary_seconds": []})
        chapters[-1]["end_seconds"] = round(min(cursor, actual), 6)
        chapters[-1]["boundary_seconds"].append(round((start + cursor) / 2, 6))
    return {"chapters": chapters}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--mix-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    film = args.film.resolve(strict=True)
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    mix = json.loads(args.mix_receipt.read_text(encoding="utf-8"))
    rows = inputs["cues"]
    if len(rows) != 25 or inputs["provider"] != "index":
        raise ValueError("Expected 25 measured IndexTTS cues")
    if mix["state"] != "rendered-technical-checks-passed" or mix["output_sha256"].lower() != digest(film):
        raise ValueError("Film differs from completed theme mix")
    if (mix["voice_gain_db"] != 0 or mix["music_gain_db"] != -17
            or mix["duck_windows"] or mix["automatic_normalization"]):
        raise ValueError("Series theme mixing policy changed")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    bound_path = args.output_dir / "video.bound-probe.json"
    bound = probe_and_write_bound_media(
        "ffprobe", film, output_path=bound_path,
        audit_directory=args.output_dir / "probe-audit")
    probe = bound.probe
    actual = probe.require_duration()
    expected = sum(row["duration_seconds"] for row in rows)
    if not 1200 <= actual <= 2400 or abs(actual - expected) > .2:
        raise ValueError("Film duration differs from measured voice edit")
    if len(probe.video_streams) != 1 or len(probe.audio_streams) != 1:
        raise ValueError("Expected one video and one audio stream")
    if (probe.video_streams[0].width, probe.video_streams[0].height) != (2560, 1440):
        raise ValueError("Resolution changed")
    story = args.output_dir / "review-storyboard.json"
    story.write_text(json.dumps(storyboard(rows, actual), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.output_dir / "full-decode.stdout").open("xb") as stdout, (
            args.output_dir / "full-decode.stderr").open("xb") as stderr:
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(film),
             "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"],
            stdout=stdout, stderr=stderr, check=False)
    if result.returncode:
        raise RuntimeError("Full audio/video decode failed; retained stderr has details")
    report = {
        "schema": "ck3-war-ai.episode-one-index-technical.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "state": "technical-checks-passed-pending-human-review",
        "video": {"path": str(film), "bytes": film.stat().st_size, "sha256": digest(film)},
        "actual_duration_seconds": actual,
        "measured_script_duration_seconds": expected,
        "resolution": [2560, 1440], "cue_count": len(rows),
        "provider": "IndexTTS-2.5", "voice_profile": inputs["index_voice"]["profile"],
        "reference_sha256": inputs["index_voice"]["reference"]["sha256"],
        "music_source_sha256": mix["music"]["sha256"],
        "music_gain_db": -17, "voice_gain_db": 0, "ducking": False,
        "full_decode_exit_code": result.returncode,
        "bound_probe": str(bound_path), "storyboard": str(story),
        "human_1x_review": "not-performed", "approval": "not-provided",
    }
    output = args.output_dir / "technical-verification.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"state": report["state"], "duration": actual,
                      "bytes": report["video"]["bytes"], "sha256": report["video"]["sha256"]}))


if __name__ == "__main__":
    main()
