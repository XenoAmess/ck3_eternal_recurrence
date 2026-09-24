"""Bind measured owner-voice IndexTTS audio to Episode 1's frozen script."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from .index_revoice import PROFILE, binding, write_new
from .prepare_index_film import estimated_sentence_boundaries


def prepare_inputs(base: dict, synthesis: dict, receipt: Path) -> dict:
    rows = deepcopy(base["cues"])
    got = {item["id"]: item for item in synthesis["cues"]}
    if len(rows) != 25 or set(got) != {row["id"] for row in rows}:
        raise ValueError("Expected the 25 frozen Episode 1 cues")
    identity = synthesis["identity"]
    if identity["profile"] != PROFILE:
        raise ValueError("IndexTTS profile differs from Project Causality r15/r16")
    for index, row in enumerate(rows):
        item = got[row["id"]]
        expected_text = hashlib.sha256(row["zh"].encode("utf-8")).hexdigest()
        if (item["text_sha256"] != expected_text
                or item["reference_sha256"] != identity["reference"]["sha256"]
                or item["model_revision"] != identity["model_revision"]
                or item["profile"] != PROFILE):
            raise ValueError(f"Wrong voice provenance: {row['id']}")
        audio = Path(item["audio"]["path"])
        if binding(audio) != item["audio"]:
            raise ValueError(f"IndexTTS WAV changed: {row['id']}")
        seconds = item["wave"]["duration_seconds"]
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError(f"Invalid measured voice duration: {row['id']}")
        chapter_end = index == len(rows) - 1 or rows[index + 1]["chapter_id"] != row["chapter_id"]
        row["audio"] = item["audio"]
        row["audio_artifact_id"] = "audio." + row["id"]
        row["speech_duration_seconds"] = seconds
        row["duration_seconds"] = math.ceil((seconds + (1.6 if chapter_end else .55)) * 30) / 30
        row["sentence_boundaries"] = estimated_sentence_boundaries(row["zh"], seconds)
        row["shot_title"] = row["visual_title"]
    result = deepcopy(base)
    result["cues"] = rows
    result["provider"] = "index"
    result["actual_duration_seconds"] = sum(row["duration_seconds"] for row in rows)
    if not 1200 <= result["actual_duration_seconds"] <= 2400:
        raise ValueError("IndexTTS edit outside the authorized 20–40 minutes")
    result["caption_timing"] = (
        "Measured IndexTTS WAV duration and Chinese script sentence-length estimates; "
        "not phoneme alignment; English proportional timing")
    result["index_voice"] = {
        "reference": identity["reference"],
        "model_revision": identity["model_revision"],
        "profile": PROFILE,
        "synthesis_receipt": binding(receipt),
    }
    result["human_signoff"] = "not-provided"
    result["music"] = "single-series-theme-fixed-level-no-ducking"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-inputs", type=Path, required=True)
    parser.add_argument("--synthesis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = json.loads(args.base_inputs.read_text(encoding="utf-8"))
    synthesis = json.loads(args.synthesis.read_text(encoding="utf-8"))
    result = prepare_inputs(base, synthesis, args.synthesis.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_new(args.output, result)
    print(json.dumps({"cues": len(result["cues"]),
                      "seconds": result["actual_duration_seconds"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
