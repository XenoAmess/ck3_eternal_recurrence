"""Summarize measured R7F synthesis speed and PCM clipping without changing WAVs."""

from __future__ import annotations

import argparse
from array import array
from datetime import datetime
import json
from pathlib import Path
import sys
import wave

from .index_revoice import binding


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesis", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    completed = json.loads(args.synthesis.read_text(encoding="utf-8"))
    request = json.loads(args.request.read_text(encoding="utf-8"))
    rows = []
    for cue in completed["cues"]:
        path = Path(cue["audio"]["path"])
        if binding(path) != cue["audio"]:
            raise ValueError(f"Changed audio: {cue['id']}")
        with wave.open(str(path), "rb") as stream:
            samples = array("h")
            samples.frombytes(stream.readframes(stream.getnframes()))
        if sys.byteorder != "little":
            samples.byteswap()
        clipped = sum(value <= -32768 or value >= 32767 for value in samples)
        rows.append({"id": cue["id"], "speech_seconds": cue["wave"]["duration_seconds"],
                     "inference_seconds": cue["inference_seconds"],
                     "clipped_samples": clipped, "total_samples": len(samples)})
    total_speech = sum(row["speech_seconds"] for row in rows)
    total_inference = sum(row["inference_seconds"] for row in rows)
    wall = (datetime.fromisoformat(completed["completed_at_utc"]) -
            datetime.fromisoformat(request["created_at_utc"])).total_seconds()
    clips = sum(row["clipped_samples"] for row in rows)
    samples = sum(row["total_samples"] for row in rows)
    report = {"schema": "ck3-war-ai-r7f-index-voice-performance.v1",
              "synthesis_receipt": binding(args.synthesis), "request": binding(args.request),
              "cue_count": len(rows), "speech_seconds": total_speech,
              "inference_seconds": total_inference, "inference_rtf": total_inference / total_speech,
              "wall_seconds_including_load": wall,
              "clipped_pcm16_samples": clips, "total_pcm16_samples": samples,
              "clipped_fraction": clips / samples, "cues": rows,
              "interpretation": "One full batch on this RTX 3060; not an A/B speed claim or human audio review"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("cue_count", "speech_seconds", "inference_seconds", "inference_rtf",
                       "wall_seconds_including_load", "clipped_pcm16_samples", "clipped_fraction")}),
          flush=True)


if __name__ == "__main__":
    main()
