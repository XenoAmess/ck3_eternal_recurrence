"""Check the repaired C10 phrase in the OneDrive-uploaded final MP4."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from .index_revoice import binding, write_new


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--upload-readback", type=Path, required=True)
    parser.add_argument("--repair-audit", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    film = args.film.resolve(strict=True)
    build = json.loads(args.build_receipt.read_text(encoding="utf-8"))
    upload = json.loads(args.upload_readback.read_text(encoding="utf-8"))
    repair = json.loads(args.repair_audit.read_text(encoding="utf-8"))
    if (film.name != Path(build["output"]).name or
        film.stat().st_size != build["output_bytes"] or
        binding(film)["sha256"] != build["output_sha256"] or
        upload.get("status") != "uploaded" or upload.get("target") != film.name or
        upload.get("folder") != "CK3-War-AI-20260923" or
        repair.get("status") != "GREEN" or repair.get("changed_cues") != ["C10"]):
        raise ValueError("Corrected uploaded film or source repair evidence is not verified")
    chapters = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(film)],
        capture_output=True, check=True).stdout)["chapters"]
    matches = [chapter for chapter in chapters if chapter["tags"].get("title", "").startswith("C10 ")]
    if len(chapters) != 23 or len(matches) != 1:
        raise ValueError("Expected exactly one C10 chapter in the 23-chapter film")
    start = float(matches[0]["start_time"]) + 84.0
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    excerpt = output / "uploaded-C10-84to97.wav"
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
               "-ss", f"{start:.6f}", "-t", "13", "-i", str(film),
               "-vn", "-ac", "1", "-ar", "22050", str(excerpt)]
    write_new(output / "extract-command.json", {"argv": command})
    subprocess.run(command, capture_output=True, check=True)
    import torch
    import whisper
    torch.set_num_threads(4)
    model = whisper.load_model(str(args.model.resolve(strict=True)), device="cpu")
    result = model.transcribe(str(excerpt), language="zh", task="transcribe",
                              fp16=False, verbose=False,
                              condition_on_previous_text=False, temperature=0)
    count = len(re.findall(r"62[.．]77", result["text"]))
    report = {
        "schema": "ck3-war-ai-r7f-corrected-uploaded-phrase-audit.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "uploaded_film": binding(film), "upload_readback": binding(args.upload_readback),
        "source_repair_audit": binding(args.repair_audit),
        "model": binding(args.model), "chapter_start_seconds": float(matches[0]["start_time"]),
        "excerpt_start_seconds": start, "excerpt": binding(excerpt),
        "transcript": result["text"],
        "segments": [{"start": row["start"], "end": row["end"], "text": row["text"]}
                     for row in result["segments"]],
        "numeric_phrase_count": count,
        "status": "GREEN" if count == 1 else "REVIEW_REQUIRED",
        "interpretation": "Independent CPU ASR on uploaded film audio, not human listening",
    }
    write_new(output / "uploaded-phrase-audit.json", report)
    print(json.dumps({"status": report["status"], "numeric_phrase_count": count,
                      "transcript": result["text"]}, ensure_ascii=False), flush=True)
    if count != 1:
        raise RuntimeError("Uploaded final film does not independently show one phrase reading")


if __name__ == "__main__":
    main()
