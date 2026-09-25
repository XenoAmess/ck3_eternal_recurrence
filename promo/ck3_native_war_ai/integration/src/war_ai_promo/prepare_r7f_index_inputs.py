"""Bind verified optimized IndexTTS speech to the frozen R7E Messina script."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from .index_revoice import binding, write_new
from .prepare_index_film import estimated_sentence_boundaries


REFERENCE_SHA = "061fe25b425752776da6c35eb2c634e2424239a8b5a2ea694bdee5a850e6d8b1"
MODEL_REVISION = "5bb1a21d0add49e164e1438144e48da31bb34582"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--base-inputs", type=Path, required=True)
    parser.add_argument("--synthesis", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    script = json.loads(args.script.read_text(encoding="utf-8"))
    base = json.loads(args.base_inputs.read_text(encoding="utf-8"))
    synthesis = json.loads(args.synthesis.read_text(encoding="utf-8"))
    frozen = script["cues"]
    rows = deepcopy(base["cues"])
    receipts = {row["id"]: row for row in synthesis["cues"]}
    if len(frozen) != len(rows) or len(rows) != 23 or len(receipts) != 23:
        raise ValueError("Expected 23 frozen R7E cues and 23 synthesized WAVs")
    identity = synthesis["identity"]
    profile = identity["profile"]
    if (identity["model_revision"] != MODEL_REVISION or
        identity["reference"]["sha256"] != REFERENCE_SHA or
        profile["duration_factor"] != .90 or
        profile["interval_silence_ms"] != 100 or
        profile["text_normalization"] is not True or
        profile["mode"] != "natural-reference-emotion" or
        profile["reference_device"] != "cpu" or
        profile["reuse_spk_cond_for_emo"] is not False or
        profile["use_qwen_emo"] is not False):
        raise ValueError("IndexTTS voice, Project Causality profile or PR #795 optimization differs")
    if binding(Path(identity["reference"]["path"])) != identity["reference"]:
        raise ValueError("Reference voice bytes changed")
    for index, (row, original) in enumerate(zip(rows, frozen)):
        if any(row[key] != original[key] for key in
               ("id", "zh", "en", "visual_title", "visual_lines",
                "source_time_seconds", "target_time_seconds")):
            raise ValueError(f"R7E script and prepared base differ: {row['id']}")
        receipt = receipts[row["id"]]
        if (receipt["text_sha256"] != hashlib.sha256(row["zh"].encode("utf-8")).hexdigest() or
            receipt["reference_sha256"] != REFERENCE_SHA or
            receipt["model_revision"] != MODEL_REVISION or
            receipt["profile"] != profile):
            raise ValueError(f"Wrong synthesis provenance: {row['id']}")
        audio = Path(receipt["audio"]["path"])
        if binding(audio) != receipt["audio"]:
            raise ValueError(f"IndexTTS audio changed: {row['id']}")
        duration = float(receipt["wave"]["duration_seconds"])
        if not math.isfinite(duration) or duration <= .12:
            raise ValueError(f"Invalid audio duration: {row['id']}")
        last = index == len(rows) - 1
        row["audio"] = receipt["audio"]
        row["audio_artifact_id"] = "audio." + row["id"]
        row["speech_duration_seconds"] = duration
        row["duration_seconds"] = math.ceil((duration + (1.6 if last else .55)) * 30) / 30
        row["sentence_boundaries"] = estimated_sentence_boundaries(row["zh"], duration)
        if "".join(event["text"] for event in row["sentence_boundaries"]) != row["zh"]:
            raise ValueError(f"IndexTTS subtitle sentence text differs from frozen script: {row['id']}")
    result = deepcopy(base)
    result["cues"] = rows
    result["provider"] = "index"
    result["actual_duration_seconds"] = sum(row["duration_seconds"] for row in rows)
    result["caption_timing"] = ("IndexTTS measured WAV duration and script-sentence character weighting; "
                                "no EdgeTTS marks reused or exact phoneme alignment claimed")
    result["index_voice"] = {"reference": identity["reference"],
                             "model_revision": MODEL_REVISION, "profile": profile,
                             "synthesis_receipt": binding(args.synthesis)}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_new(args.output_dir / "production-inputs.json", result)
    print(json.dumps({"cues": len(rows), "duration_seconds": result["actual_duration_seconds"],
                      "reference_sha256": REFERENCE_SHA, "model_revision": MODEL_REVISION,
                      "reference_device": "cpu"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
