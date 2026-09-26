"""Excise the audited duplicate phrase from the original C10 IndexTTS WAV.

The source cue, ASR proof, cut coordinates and resulting bytes remain immutable.
All other 22 cue receipts still refer to their original synthesized WAVs.
"""

from __future__ import annotations

import argparse
from array import array
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import wave

from .index_revoice import binding, probe_wav, write_new


SOURCE_C10_SHA = "ac6a5770375ed772c19ed992cb35d0a1ebf94356daaee84a0fbc382df19153cc"
SCRIPT_C10_SHA = "ccc0cfe22663ff83f12ec7ca4dcdee856eb98e919a09ecc33cdf445f0f60e522"
PHRASE = "折合六十二点七七五七五人当量"
NOMINAL_CUT_START = 87.15
NOMINAL_CUT_END = 89.95


def quiet_boundary(pcm: array, nominal: float, rate: int) -> int:
    center = round(nominal * rate)
    radius = round(.02 * rate)
    offset = min(range(center - radius, center + radius + 1),
                 key=lambda index: (abs(pcm[index]), abs(index - center)))
    if abs(pcm[offset]) > 350:
        raise ValueError(f"Cut boundary {nominal}s is not quiet: {pcm[offset]}")
    return offset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-completed", type=Path, required=True)
    parser.add_argument("--source-asr", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source_completed = args.source_completed.resolve(strict=True)
    source_asr = args.source_asr.resolve(strict=True)
    script = args.script.resolve(strict=True)
    original = json.loads(source_completed.read_text(encoding="utf-8"))
    cues = original["cues"]
    cue = next(row for row in cues if row["id"] == "C10")
    source_audio = Path(cue["audio"]["path"]).resolve(strict=True)
    source_receipt = source_audio.with_suffix(".receipt.json")
    source_request = source_audio.with_suffix(".request.json")
    source_proof = json.loads(source_asr.read_text(encoding="utf-8"))
    frozen_cue = next(row for row in json.loads(script.read_text(encoding="utf-8"))["cues"]
                      if row["id"] == "C10")
    if (len(cues) != 23 or source_audio.name != "C10.wav" or
        cue["audio"] != binding(source_audio) or cue["audio"]["sha256"] != SOURCE_C10_SHA or
        cue["text_sha256"] != SCRIPT_C10_SHA or frozen_cue["zh"].count(PHRASE) != 1 or
        source_proof["text"].count("62.775") != 2 or
        json.loads(source_receipt.read_text(encoding="utf-8")) != cue):
        raise ValueError("C10 source, one-time script or two-time ASR proof changed")
    with wave.open(str(source_audio), "rb") as reader:
        params = reader.getparams()
        if (reader.getnchannels(), reader.getsampwidth(), reader.getframerate(),
            reader.getcomptype()) != (1, 2, 22050, "NONE"):
            raise ValueError("Expected original IndexTTS mono PCM16 WAV")
        pcm = array("h")
        pcm.frombytes(reader.readframes(reader.getnframes()))
    if sys.byteorder != "little":
        pcm.byteswap()
    left = quiet_boundary(pcm, NOMINAL_CUT_START, 22050)
    right = quiet_boundary(pcm, NOMINAL_CUT_END, 22050)
    if not 2.7 < (right - left) / 22050 < 2.9:
        raise ValueError("Unexpected duplicate phrase duration")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    repaired = output / "C10.wav"
    stitched = pcm[:left] + pcm[right:]
    if sys.byteorder != "little":
        stitched.byteswap()
    with wave.open(str(repaired), "wb") as writer:
        writer.setparams(params)
        writer.writeframes(stitched.tobytes())
    shutil.copyfile(source_request, output / "C10.request.json")
    manifest = {
        "schema": "ck3-war-ai-r7f-c10-duplicate-excision.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "IndexTTS repeated a phrase which occurs once in the frozen script",
        "source_audio": binding(source_audio),
        "source_receipt": binding(source_receipt),
        "source_completed": binding(source_completed),
        "source_asr": binding(source_asr),
        "script": binding(script),
        "cue_id": "C10", "script_phrase_count": 1,
        "source_asr_numeric_phrase_count": 2,
        "cut": {"sample_rate": 22050, "start_sample": left, "end_sample": right,
                "start_seconds": left / 22050, "end_seconds": right / 22050,
                "removed_seconds": (right - left) / 22050,
                "boundary_pcm16": [pcm[left], pcm[right]]},
        "method": "single quiet-boundary PCM16 excision; no voice resynthesis",
        "repaired_audio": binding(repaired),
        "repaired_wave": probe_wav(repaired),
        "human_1x_signoff": "not-provided",
    }
    write_new(output / "repair-manifest.json", manifest)
    new_cue = deepcopy(cue)
    new_cue["audio"] = binding(repaired)
    new_cue["wave"] = probe_wav(repaired)
    new_cue["editorial_repair"] = binding(output / "repair-manifest.json")
    new_cue["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_new(output / "C10.receipt.json", new_cue)
    updated = deepcopy(original)
    updated["state"] = "synthesized-with-audited-C10-editorial-cut"
    updated["cues"] = [new_cue if row["id"] == "C10" else row for row in cues]
    updated["total_speech_seconds"] = sum(row["wave"]["duration_seconds"]
                                           for row in updated["cues"])
    updated["repair"] = {"manifest": binding(output / "repair-manifest.json"),
                         "source_audio": binding(source_audio),
                         "source_receipt": binding(source_receipt),
                         "source_asr": binding(source_asr),
                         "source_completed": binding(source_completed)}
    updated["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_new(output / "completed.json", updated)
    print(json.dumps({"cut": manifest["cut"], "repaired_audio": new_cue["audio"],
                      "total_speech_seconds": updated["total_speech_seconds"]},
                     ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
