"""Independently transcribe completed IndexTTS cues for advisory narration QA.

The recognizer is not given the expected script. Its similarity score can flag
missing speech, but homophones, numbers, and traditional Chinese make it an
imperfect proxy for listening. This command never records human approval.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import unicodedata

from .index_revoice import binding, write_new


def normalized(text: str) -> str:
    return "".join(char.casefold() for char in unicodedata.normalize("NFKC", text)
                   if char.isalnum())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True,
                        help="Existing local Whisper checkpoint; no model download")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if not args.model.is_file() or args.output_dir.exists():
        parser.error("Local model must exist and output directory must be new")
    source = json.loads(args.inputs.read_text(encoding="utf-8"))
    cues = source["cues"][:args.limit]
    if not cues:
        parser.error("No narration cues selected")
    model_binding = binding(args.model)
    import whisper  # Deferred so --help and source checks do not load torch.
    import torch
    torch.set_num_threads(4)
    model = whisper.load_model(str(args.model), device="cpu")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    rows = []
    for cue in cues:
        cue_id = cue["id"]
        expected_text = cue["zh"]
        audio = args.audio_dir / f"{cue_id}.wav"
        receipt_path = args.audio_dir / f"{cue_id}.receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        audio_binding = binding(audio)
        if (receipt["id"] != cue_id or receipt["audio"] != audio_binding
                or receipt["text_sha256"] != hashlib.sha256(expected_text.encode("utf-8")).hexdigest()):
            raise ValueError(f"Audio/script receipt mismatch: {cue_id}")
        result = model.transcribe(str(audio), language="zh", task="transcribe",
                                  fp16=False, verbose=False,
                                  condition_on_previous_text=False,
                                  temperature=0)
        transcript = result["text"].strip()
        score = SequenceMatcher(None, normalized(expected_text), normalized(transcript),
                                autojunk=False).ratio()
        row = {
            "cue_id": cue_id,
            "audio": audio_binding,
            "source_receipt": binding(receipt_path),
            "model": model_binding,
            "device": "cpu",
            "input_language": "zh",
            "recognizer_prompt": None,
            "expected_text_sha256": hashlib.sha256(expected_text.encode("utf-8")).hexdigest(),
            "transcript": transcript,
            "segments": [
                {"start": segment["start"], "end": segment["end"],
                 "text": segment["text"],
                 "avg_logprob": segment.get("avg_logprob"),
                 "no_speech_prob": segment.get("no_speech_prob")}
                for segment in result["segments"]
            ],
            "normalized_character_similarity_advisory": round(score, 4),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "interpretation": "Machine screening only; not a transcript proof or human listening signoff",
        }
        write_new(args.output_dir / f"{cue_id}.whisper.json", row)
        rows.append({"id": cue_id, "score": row["normalized_character_similarity_advisory"],
                     "segments": len(row["segments"])})
        print(f"ASR {cue_id} similarity={score:.4f}", flush=True)
    write_new(args.output_dir / "audit-summary.json", {
        "state": "advisory-complete", "model": model_binding,
        "inputs": binding(args.inputs), "cues": rows,
        "human_signoff": "not-provided",
    })


if __name__ == "__main__":
    main()
