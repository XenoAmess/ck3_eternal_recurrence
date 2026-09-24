"""Copy one machine-checked IndexTTS MP4 into the fixed OneDrive client folder."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


DESTINATION_DIRECTORY = Path(r"C:\Users\1\OneDrive\CK3-War-AI-20260923")


def binding(path: Path) -> dict:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha.hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--speech-audit", type=Path, required=True)
    parser.add_argument("--review-package", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    film = args.film.resolve(strict=True)
    report = json.loads(args.verification.read_text(encoding="utf-8"))
    speech = json.loads(args.speech_audit.read_text(encoding="utf-8"))
    review = json.loads(args.review_package.read_text(encoding="utf-8"))
    source = binding(film)
    if report["state"] != "technical-checks-passed-pending-human-review" or report["video"]["sha256"] != source["sha256"]:
        raise ValueError("Final film lacks matching full decode and media verification")
    if speech["state"] != "advisory-screen-green" or speech["gross_screen_failures"]:
        raise ValueError("IndexTTS speech screen is not green")
    if (review["state"] != "pending-human-review" or review["approval_granted"]
            or review["artifact"]["sha256"].lower() != source["sha256"]):
        raise ValueError("Final film lacks matching unsigned review frames")
    if not DESTINATION_DIRECTORY.is_dir() or film.suffix.lower() != ".mp4":
        raise ValueError("Fixed OneDrive client folder or MP4 missing")
    target = DESTINATION_DIRECTORY / film.name
    if target.exists() or args.receipt.exists():
        raise FileExistsError("Delivery target or receipt already exists")
    shutil.copyfile(film, target)
    copied = binding(target)
    if copied["bytes"] != source["bytes"] or copied["sha256"] != source["sha256"]:
        raise ValueError("OneDrive local copy differs from verified film")
    result = {
        "schema": "ck3-war-ai.episode-one-index-onedrive.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "copy exactly one verified MP4 into fixed OneDrive desktop-client sync folder",
        "source": source, "destination": copied,
        "other_cloud_items_downloaded_by_this_task": 0,
        "status": "local-copy-byte-verified; client-upload-readback-pending",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"destination": copied, "status": result["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
