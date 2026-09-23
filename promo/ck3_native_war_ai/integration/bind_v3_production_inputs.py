"""Bind preserved V3 speech cues to the reviewed, limited evidence ledger."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
V3 = HERE.parent / "longform" / "v3"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bind(speech_root: Path, ledger_path: Path) -> dict:
    source = speech_root / "production-inputs.json"
    inputs = json.loads(source.read_text(encoding="utf-8"))
    script = speech_root / "narration-source.json"
    checked_in = V3 / "narration-spoken.json"
    if sha256(script) != sha256(checked_in):
        raise ValueError("Prepared speech used a different checked-in V3 script")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("schema") != "ck3-war-ai.v3-evidence-visual-ledger.v1" or ledger.get("spoken_script_sha256") != sha256(checked_in):
        raise ValueError("Evidence ledger does not bind the prepared V3 script")
    source_cues = json.loads(script.read_text(encoding="utf-8"))["cues"]
    rows = inputs["cues"]
    evidence = ledger["cues"]
    ids = [f"V3-{index:02d}" for index in range(1, 46)]
    if any([row["id"] for row in group] != ids for group in (rows, source_cues, evidence)):
        raise ValueError("Expected all 45 V3 cues in exact order")
    if any(row["state"] == "unbound" for row in evidence):
        raise ValueError("An unbound V3 cue may not enter full-film composition")
    output = deepcopy(inputs)
    for row, spoken, proof in zip(output["cues"], source_cues, evidence):
        if (row["zh"] != spoken["zh"] or row["en"] != spoken["en"]
                or row["shot_id"] != proof["shot_id"] or row["claim_ids"]):
            raise ValueError(f"Spoken text or visual identity differs: {row['id']}")
        request = speech_root / (row["id"] + ".request.json")
        if json.loads(request.read_text(encoding="utf-8"))["text"] != row["zh"]:
            raise ValueError(f"TTS request text differs: {row['id']}")
        audio = Path(row["audio"]["path"])
        if audio.stat().st_size != row["audio"]["bytes"] or sha256(audio) != row["audio"]["sha256"]:
            raise ValueError(f"Prepared audio changed: {row['id']}")
        row["claim_ids"] = [row["id"]]
        row["visual_binding_state"] = proof["state"]
        row["evidence_claim_scope"] = proof["claim_scope"]
        row["evidence_limits"] = proof["limits"]
    output["v3_evidence_ledger"] = {"path": ledger_path.resolve().as_posix(), "sha256": sha256(ledger_path)}
    output["v3_spoken_script_sha256"] = sha256(checked_in)
    output["v3_binding_scope"] = "visual sources and limited evidence claims; no human film signoff"
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speech-root", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=V3 / "evidence-visual-ledger.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = bind(args.speech_root, args.ledger)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"V3 production inputs bound: {len(data['cues'])} cues, {data['actual_duration_seconds']:.2f} seconds")


if __name__ == "__main__":
    main()
