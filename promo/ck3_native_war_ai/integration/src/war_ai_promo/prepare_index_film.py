"""Bind completed IndexTTS cues to a new V3 render and continuous live spans."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

from .index_revoice import PROFILE, binding, write_new


def estimated_sentence_boundaries(text: str, duration: float) -> list[dict]:
    """Keep captions readable when IndexTTS supplies no sentence marks.

    These are duration-weighted script estimates, not phoneme or ASR alignment.
    The original EdgeTTS boundaries must never be carried into a new voice.
    """
    sentences = [part.strip() for part in
                 re.findall(r"[^。！？!?；;]+(?:[。！？!?；;]|$)", text) if part.strip()]
    weights = [sum(char.isalnum() for char in part) for part in sentences]
    if not sentences or not all(weights) or duration <= .12:
        raise ValueError("Cannot estimate positive IndexTTS sentence intervals")
    start_ticks = round(.12 * 10_000_000)
    end_ticks = round(duration * 10_000_000)
    total = sum(weights)
    cursor = start_ticks
    consumed = 0
    result = []
    for index, (sentence, weight) in enumerate(zip(sentences, weights)):
        consumed += weight
        stop = (end_ticks if index == len(sentences) - 1 else
                start_ticks + round((end_ticks - start_ticks) * consumed / total))
        if stop <= cursor:
            raise ValueError("IndexTTS sentence interval rounded to zero")
        result.append({"type": "SentenceBoundary", "offset": cursor,
                       "duration": stop - cursor, "text": sentence,
                       "timing_basis": "measured-audio-duration-and-script-character-weight"})
        cursor = stop
    return result


def prepare_inputs(base: dict, synth: dict, *, base_spec: dict) -> tuple[dict, dict]:
    rows = deepcopy(base["cues"])
    receipts = {row["id"]: row for row in synth["cues"]}
    if len(rows) != 45 or set(receipts) != {row["id"] for row in rows}:
        raise ValueError("Need exactly the frozen V3 45-cue script")
    identity = synth["identity"]
    if identity["profile"] != PROFILE:
        raise ValueError("IndexTTS profile differs from Project Causality r15/r16")
    for index, row in enumerate(rows):
        receipt = receipts[row["id"]]
        expected_text = hashlib.sha256(row["zh"].encode("utf-8")).hexdigest()
        if (receipt["text_sha256"] != expected_text
                or receipt["reference_sha256"] != identity["reference"]["sha256"]
                or receipt["model_revision"] != identity["model_revision"]
                or receipt["profile"] != PROFILE):
            raise ValueError(f"Wrong TTS provenance for {row['id']}")
        audio = Path(receipt["audio"]["path"])
        if binding(audio) != receipt["audio"]:
            raise ValueError(f"IndexTTS WAV changed: {row['id']}")
        duration = receipt["wave"]["duration_seconds"]
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"Invalid IndexTTS duration: {row['id']}")
        last_in_chapter = index == len(rows) - 1 or rows[index + 1]["chapter_id"] != row["chapter_id"]
        row["audio"] = receipt["audio"]
        row["speech_duration_seconds"] = duration
        row["duration_seconds"] = math.ceil((duration + (1.6 if last_in_chapter else .55)) * 30) / 30
        row["sentence_boundaries"] = estimated_sentence_boundaries(row["zh"], duration)
    result = deepcopy(base)
    result["cues"] = rows
    result["provider"] = "index"
    result["actual_duration_seconds"] = sum(row["duration_seconds"] for row in rows)
    result["caption_timing"] = ("IndexTTS measured audio with duration-weighted Chinese script-sentence estimates; "
                                "English remains proportional; no Edge sentence marks reused or exact alignment claimed")
    result["index_voice"] = {"reference": identity["reference"], "model_revision": identity["model_revision"],
                             "profile": PROFILE, "synthesis_receipt": binding(Path(synth["receipt_path"]))}

    clips = deepcopy(base_spec["clips"])
    by_id = {row["id"]: row for row in rows}
    if not {clip["cue_id"] for clip in clips}.issubset(by_id) or len(clips) != 5:
        raise ValueError("Expected five original continuous CK3 context clips")
    ends: dict[str, float] = {}
    for clip in clips:
        cue_id = clip["cue_id"]
        needed = by_id[cue_id]["duration_seconds"]
        original_end = clip["offset_seconds"] + clip["duration_seconds"]
        if cue_id == "V3-11":
            start = max(0.0, original_end - needed)
        elif cue_id == "V3-16":
            start = max(clip["offset_seconds"], ends["V3-11"] + 2.0)
        elif cue_id == "V3-17":
            start = clip["offset_seconds"]
        elif cue_id == "V3-22":
            start = max(clip["offset_seconds"], ends["V3-16"] + 10.0)
        elif cue_id == "V3-23":
            start = max(clip["offset_seconds"], ends["V3-22"] + 5.0)
        else:
            raise ValueError(f"Unexpected capture cue: {cue_id}")
        # Adapter validates the exact clean-span and source-recording bounds.
        clip["offset_seconds"] = round(start, 6)
        clip["duration_seconds"] = needed
        ends[cue_id] = start + needed
    return result, {"schema": base_spec["schema"], "clips": clips}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-inputs", type=Path, required=True)
    parser.add_argument("--synthesis", type=Path, required=True)
    parser.add_argument("--base-capture-spec", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    base = json.loads(args.base_inputs.read_text(encoding="utf-8"))
    synthesis = json.loads(args.synthesis.read_text(encoding="utf-8"))
    synthesis["receipt_path"] = args.synthesis.resolve().as_posix()
    spec = json.loads(args.base_capture_spec.read_text(encoding="utf-8"))
    inputs, captures = prepare_inputs(base, synthesis, base_spec=spec)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_new(args.output_dir / "production-inputs.json", inputs)
    write_new(args.output_dir / "capture-selection.json", captures)
    print(json.dumps({"cues": len(inputs["cues"]), "seconds": inputs["actual_duration_seconds"],
                      "capture_ids": [item["cue_id"] for item in captures["clips"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
