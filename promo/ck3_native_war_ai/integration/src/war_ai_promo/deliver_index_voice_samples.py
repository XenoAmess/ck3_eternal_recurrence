"""Copy two verified R7F IndexTTS WAVs into the fixed OneDrive upload folder."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from .index_revoice import binding


EXPECTED = ("E1-F01", "E1-F03")
REFERENCE_SHA = "061fe25b425752776da6c35eb2c634e2424239a8b5a2ea694bdee5a850e6d8b1"
MODEL_REVISION = "5bb1a21d0add49e164e1438144e48da31bb34582"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speech-dir", type=Path, required=True)
    parser.add_argument("--onedrive-folder", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if not args.onedrive_folder.is_dir() or args.receipt.exists():
        raise ValueError("Existing selected OneDrive folder and new receipt path required")
    planned = []
    for cue_id in EXPECTED:
        source = args.speech_dir / (cue_id + ".wav")
        note = json.loads((args.speech_dir / (cue_id + ".receipt.json")).read_text(encoding="utf-8"))
        actual = binding(source)
        if (actual != note["audio"] or note["id"] != cue_id or
            note["reference_sha256"] != REFERENCE_SHA or
            note["model_revision"] != MODEL_REVISION or
            note["profile"]["reference_device"] != "cpu" or
            note["profile"]["reuse_spk_cond_for_emo"] is not False):
            raise ValueError(f"Wrong or changed optimized IndexTTS WAV: {cue_id}")
        target = args.onedrive_folder / f"CK3-War-AI-Episode-1-R7F-IndexTTS-{cue_id}.wav"
        if target.exists():
            raise FileExistsError(target)
        planned.append((cue_id, source, target))
    rows = []
    for cue_id, source, target in planned:
        with source.open("rb") as reader, target.open("xb") as writer:
            shutil.copyfileobj(reader, writer)
        if binding(source)["sha256"] != binding(target)["sha256"]:
            raise ValueError(f"OneDrive local copy differs: {cue_id}")
        rows.append({"cue_id": cue_id, "source": binding(source),
                     "destination": binding(target)})
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({
        "schema": "ck3-war-ai-r7f-index-two-sample-upload.v1",
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "files_copied": len(rows), "files": rows,
        "other_cloud_file_content_read_or_downloaded": False,
        "client_status": "pending-readback",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files_copied": len(rows),
                      "destinations": [row["destination"]["path"] for row in rows]},
                     ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
