"""Verify the C10 duplicate excision against original and repaired audio/ASR."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import wave

from .index_revoice import binding, write_new


def pcm(path: Path) -> tuple[int, bytes]:
    with wave.open(str(path), "rb") as stream:
        if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) != (1, 2, 22050):
            raise ValueError("Wrong C10 PCM format")
        return stream.getnframes(), stream.readframes(stream.getnframes())


def occurrences(path: Path) -> int:
    return len(re.findall(r"62[.．]77", json.loads(path.read_text(encoding="utf-8"))["text"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repaired-completed", type=Path, required=True)
    parser.add_argument("--source-crop-asr", type=Path, required=True)
    parser.add_argument("--repaired-crop-asr", type=Path, required=True)
    parser.add_argument("--repaired-full-asr", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    completed = json.loads(args.repaired_completed.read_text(encoding="utf-8"))
    if (manifest["schema"] != "ck3-war-ai-r7f-c10-duplicate-excision.v1" or
        completed["repair"]["manifest"] != binding(args.manifest)):
        raise ValueError("Repair manifest binding changed")
    source = Path(manifest["source_audio"]["path"])
    repaired = Path(manifest["repaired_audio"]["path"])
    if binding(source) != manifest["source_audio"] or binding(repaired) != manifest["repaired_audio"]:
        raise ValueError("C10 source or repaired bytes changed")
    old_frames, old_pcm = pcm(source)
    new_frames, new_pcm = pcm(repaired)
    left = manifest["cut"]["start_sample"]
    right = manifest["cut"]["end_sample"]
    if (new_frames != old_frames - (right - left) or
        new_pcm != old_pcm[:left * 2] + old_pcm[right * 2:]):
        raise ValueError("Repaired PCM is not the exact single audited excision")
    counts = {"source_crop": occurrences(args.source_crop_asr),
              "repaired_crop": occurrences(args.repaired_crop_asr),
              "repaired_full_cue": occurrences(args.repaired_full_asr)}
    if counts != {"source_crop": 2, "repaired_crop": 1, "repaired_full_cue": 1}:
        raise ValueError(f"Repaired ASR still suggests repeated phrase: {counts}")
    source_completed = json.loads(Path(completed["repair"]["source_completed"]["path"])
                                  .read_text(encoding="utf-8"))
    changed = [row["id"] for old, row in zip(source_completed["cues"], completed["cues"])
               if old["audio"] != row["audio"]]
    if changed != ["C10"]:
        raise ValueError(f"Only C10 audio may change: {changed}")
    report = {
        "schema": "ck3-war-ai-r7f-c10-duplicate-repair-audit.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "GREEN", "changed_cues": changed,
        "source_and_repaired_pcm_exact_outside_cut": True,
        "cut": manifest["cut"], "asr_numeric_phrase_counts": counts,
        "source_crop_asr": binding(args.source_crop_asr),
        "repaired_crop_asr": binding(args.repaired_crop_asr),
        "repaired_full_asr": binding(args.repaired_full_asr),
        "interpretation": "ASR and PCM machine audit, not 1x human listening",
    }
    write_new(args.output, report)
    print(json.dumps({"status": "GREEN", "changed_cues": changed,
                      "numeric_phrase_counts": counts}), flush=True)


if __name__ == "__main__":
    main()
