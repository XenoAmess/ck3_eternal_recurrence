"""Screen existing ASR segments for repeated nearby numeric phrases.

This is an advisory detector: a hit requires listening or source comparison.
It catches the C10 double reading missed by gross completeness checks.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .index_revoice import binding, write_new


NUMERIC = re.compile(r"\d+(?:[.,]\d+)*")


def candidates(segments: list[dict]) -> list[dict]:
    found = []
    for index, first in enumerate(segments):
        for token in NUMERIC.findall(first["text"]):
            normalized = token.replace(",", "")
            if sum(char.isdigit() for char in normalized) < 5:
                continue
            for later in segments[index + 1:index + 4]:
                if later["start"] - first["start"] > 6.0:
                    break
                others = [value.replace(",", "") for value in NUMERIC.findall(later["text"])]
                if normalized in others:
                    found.append({"numeric_phrase": normalized,
                                  "first_start_seconds": first["start"],
                                  "later_start_seconds": later["start"],
                                  "first_asr_text": first["text"],
                                  "later_asr_text": later["text"]})
                    break
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-asr-dir", type=Path, required=True)
    parser.add_argument("--corrected-c10-asr", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.source_asr_dir.glob("*.whisper.json"))
    if len(files) != 23:
        raise ValueError("Expected 23 complete IndexTTS ASR cue records")
    rows = []
    for source in files:
        cue_id = source.name.removesuffix(".whisper.json")
        selected = (args.corrected_c10_asr if cue_id == "C10" and args.corrected_c10_asr
                    else source)
        doc = json.loads(selected.read_text(encoding="utf-8"))
        rows.append({"cue_id": cue_id, "asr": binding(selected),
                     "candidates": candidates(doc["segments"])})
    hits = [row for row in rows if row["candidates"]]
    report = {"schema": "ck3-war-ai-index-local-numeric-repetition-screen.v1",
              "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "state": "candidates-need-review" if hits else "no-nearby-numeric-repetition-candidates",
              "cues": 23, "hit_cues": [row["cue_id"] for row in hits], "rows": rows,
              "interpretation": "Advisory ASR screen, not exact-word or human listening proof"}
    write_new(args.output, report)
    print(json.dumps({"state": report["state"], "hit_cues": report["hit_cues"]}), flush=True)


if __name__ == "__main__":
    main()
