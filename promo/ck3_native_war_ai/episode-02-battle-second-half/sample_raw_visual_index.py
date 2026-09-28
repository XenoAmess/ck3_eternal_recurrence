"""Take sparse, reproducible review stills from the preserved E2 raw captures.

This is a seek-based observation aid. It does not certify clean spans or replace a
full-speed human review. The output directory must be new and remains immutable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SAMPLES = {
    "a01": (10, 70, 130, 150, 210, 230, 270, 335, 350, 390, 480, 580),
    "a02": (10, 70, 130, 180, 195, 265, 335, 350, 390, 480, 580),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a01", type=Path, required=True)
    parser.add_argument("--a02", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("ffmpeg not found")
    sources = {"a01": args.a01.resolve(strict=True), "a02": args.a02.resolve(strict=True)}
    if args.output.exists():
        parser.error("output already exists; use a new append-only attempt")
    args.output.mkdir(parents=True)
    records = []
    for label, seconds in SAMPLES.items():
        source = sources[label]
        destination = args.output / label
        destination.mkdir()
        for second in seconds:
            still = destination / f"t{second:03d}.jpg"
            argv = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
                "-threads", "1", "-ss", str(second), "-i", str(source),
                "-map", "0:v:0", "-frames:v", "1", "-q:v", "3", str(still),
            ]
            completed = subprocess.run(argv, capture_output=True, text=True, check=False)
            if completed.returncode != 0 or not still.is_file():
                raise RuntimeError(f"sample {label}@{second} failed: {completed.stderr}")
            records.append({
                "source": label,
                "requested_seek_seconds": second,
                "seek_is_not_exact_frame_pts": True,
                "still": str(still),
                "bytes": still.stat().st_size,
                "sha256": sha256(still),
                "argv": argv,
            })
    payload = {
        "schema": "xar.war-promo.sparse-visual-samples/v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SAMPLED_UNREVIEWED",
        "human_full_speed_review": False,
        "clean_spans_certified": False,
        "source_files": {label: {"path": str(path), "bytes": path.stat().st_size}
                         for label, path in sources.items()},
        "samples": records,
    }
    (args.output / "sample-index.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output / "sample-index.json")


if __name__ == "__main__":
    main()
