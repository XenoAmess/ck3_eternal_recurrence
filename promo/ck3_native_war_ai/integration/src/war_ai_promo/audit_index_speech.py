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
    failed = []
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
        target_chars = len(normalized(expected_text))
        transcript_chars = len(normalized(transcript))
        length_ratio = transcript_chars / target_chars if target_chars else 0.0
        segments = result["segments"]
        duration = receipt["wave"]["duration_seconds"]
        # Deliberately loose: this catches gross truncation, silence and runaway
        # repetition without pretending that ASR homophones prove exact wording.
        screen = bool(segments and .70 <= length_ratio <= 1.35
                      and segments[0]["start"] <= 3.0
                      and segments[-1]["end"] >= duration - 3.0)
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
            "gross_completeness_screen": {
                "passed": screen, "transcript_to_script_character_ratio": round(length_ratio, 4),
                "audio_duration_seconds": duration,
                "first_asr_start_seconds": segments[0]["start"] if segments else None,
                "last_asr_end_seconds": segments[-1]["end"] if segments else None,
                "scope": "Gross truncation/silence/repetition triage, not exact word verification",
            },
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "interpretation": "Machine screening only; not a transcript proof or human listening signoff",
        }
        write_new(args.output_dir / f"{cue_id}.whisper.json", row)
        rows.append({"id": cue_id, "score": row["normalized_character_similarity_advisory"],
                     "segments": len(row["segments"]), "gross_screen_passed": screen})
        if not screen:
            failed.append(cue_id)
        print(f"ASR {cue_id} similarity={score:.4f}", flush=True)
    write_new(args.output_dir / "audit-summary.json", {
        "state": "advisory-screen-red" if failed else "advisory-screen-green",
        "gross_screen_failures": failed, "model": model_binding,
        "inputs": binding(args.inputs), "cues": rows,
        "human_signoff": "not-provided",
    })
    if failed:
        raise RuntimeError(f"IndexTTS speech requires investigation: {failed}")


if __name__ == "__main__":
    main()
