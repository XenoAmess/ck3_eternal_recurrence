"""Copy exactly one finished pilot MP4 into the established OneDrive sync folder."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination-folder", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    folder = args.destination_folder.resolve(strict=True)
    if source.suffix.lower() != ".mp4":
        raise ValueError("Only the finished MP4 may be copied")
    if folder.name != "CK3-War-AI-20260923" or folder.parent.name != "OneDrive":
        raise ValueError("Destination must be the established selective-sync folder")
    target = folder / source.name
    if target.exists() or args.receipt.exists():
        raise FileExistsError("Do not replace an existing delivery or receipt")
    original = digest(source)
    with source.open("rb") as input_file, target.open("xb") as output_file:
        shutil.copyfileobj(input_file, output_file, length=8 * 1024 * 1024)
    copied = digest(target)
    if original != copied or source.stat().st_size != target.stat().st_size:
        raise ValueError("Local sync-folder copy failed byte verification")
    receipt = {
        "schema": "ck3-war-ai-one-file-onedrive-delivery.v1",
        "copied_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "OneDrive desktop client selective-sync folder; one MP4 local copy",
        "source": str(source), "destination": str(target),
        "bytes": target.stat().st_size, "sha256": copied,
        "client_upload_status": "pending independent client activity readback",
        "other_cloud_file_content_read_or_downloaded_by_this_task": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False,
                                      indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
