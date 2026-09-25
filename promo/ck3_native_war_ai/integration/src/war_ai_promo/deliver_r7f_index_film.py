"""Copy only the verified R7F formal MP4 to the selected OneDrive folder."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from .index_revoice import binding


EXPECTED_NAME = "CK3-War-AI-Episode-1-Messina-Original-IndexTTS-Formal-R7F-20260926.mp4"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--onedrive-folder", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.build_receipt.read_text(encoding="utf-8"))
    source = Path(receipt["output"]).resolve(strict=True)
    if (receipt["schema"] != "ck3-war-ai-episode-01-r7f-index-formal-build.v1" or
        receipt["state"] != "ready-for-onedrive-before-machine-review" or
        source.name != EXPECTED_NAME or receipt["chapter_count"] != 23 or
        binding(source)["sha256"] != receipt["output_sha256"] or
        source.stat().st_size != receipt["output_bytes"]):
        raise ValueError("R7F formal build is missing or changed")
    folder = args.onedrive_folder.resolve(strict=True)
    if folder.name != "CK3-War-AI-20260923" or not folder.is_dir() or args.receipt.exists():
        raise ValueError("Existing selected OneDrive folder and new receipt path required")
    target = folder / EXPECTED_NAME
    if target.exists():
        raise FileExistsError(target)
    with source.open("rb") as reader, target.open("xb") as writer:
        shutil.copyfileobj(reader, writer, length=1024 * 1024)
    if binding(target)["sha256"] != receipt["output_sha256"] or target.stat().st_size != receipt["output_bytes"]:
        raise ValueError("OneDrive local copy differs from formal build")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({
        "schema": "ck3-war-ai-r7f-index-one-film-upload.v1",
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source), "destination": str(target),
        "bytes": target.stat().st_size, "sha256": receipt["output_sha256"],
        "other_cloud_file_content_read_or_downloaded": False,
        "client_status": "pending-readback",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"destination": str(target), "bytes": target.stat().st_size,
                      "sha256": receipt["output_sha256"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
