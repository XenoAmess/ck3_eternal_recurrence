"""Turn an editorial case/window list into hash-checkable V3 capture specs."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.capture_media import load_capture_spec


CASE_BUNDLES = {
    "CASE-W": ("D:/workspace/ck3_war_film_research_20260923/case-w-bundle-r1", "case-w-observation", 5.013, 390.0),
    "CASE-C": ("D:/workspace/ck3_war_film_research_20260923/case-c-bundle-r2", "case-c-observation", 5.031, 460.0),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = {row["id"]: row for row in json.loads(args.inputs.read_text(encoding="utf-8"))["cues"]}
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    if selection.get("schema") != "ck3-war-ai.v3-editorial-capture-selection.v1":
        raise ValueError("Unexpected V3 editorial selection schema")
    clips = []
    windows = {case: [] for case in CASE_BUNDLES}
    for choice in selection["clips"]:
        if set(choice) != {"cue_id", "case_id", "media_begin_seconds", "evidence_role"}:
            raise ValueError("Each selection needs the exact four editorial fields")
        cue, case = choice["cue_id"], choice["case_id"]
        if cue not in rows or case not in CASE_BUNDLES or choice["evidence_role"] != "context":
            raise ValueError("Only a bound V3 cue and explicit context role are allowed")
        bundle, span, clean_begin, clean_end = CASE_BUNDLES[case]
        duration = rows[cue]["duration_seconds"]
        absolute = float(choice["media_begin_seconds"])
        if absolute < clean_begin or absolute + duration > clean_end:
            raise ValueError(f"Selected footage exceeds the clean span: {cue}")
        for start, stop in windows[case]:
            if absolute < stop and absolute + duration > start:
                raise ValueError(f"Selected footage reuses a prior {case} interval: {cue}")
        windows[case].append((absolute, absolute + duration))
        clips.append({"cue_id": cue, "bundle_root": bundle, "span_id": span,
                      "offset_seconds": round(absolute - clean_begin, 6),
                      "duration_seconds": duration, "evidence_role": "context",
                      "claim_ids": rows[cue]["claim_ids"]})
    document = {"schema": "ck3-war-ai.capture-clips.v1", "clips": clips}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    if load_capture_spec(args.output) != clips:
        raise ValueError("Generated capture spec failed its importer preflight")
    print(json.dumps({"clips": len(clips), "windows": windows}, ensure_ascii=False))


if __name__ == "__main__":
    main()
