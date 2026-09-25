"""Inspect representative final frames only after OneDrive client upload readback."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--upload-readback", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    film = args.film.resolve(strict=True)
    segments = json.loads(args.segments.resolve(strict=True).read_text(encoding="utf-8"))
    readback = json.loads(args.upload_readback.resolve(strict=True).read_text(encoding="utf-8"))
    if readback["status"] != "uploaded" or readback["target"] != film.name:
        raise ValueError("exact film must be uploaded by the OneDrive client before review")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    frames = output / "frames"
    frames.mkdir()
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    report = {"schema": "ck3-war-ai-edge-math-full-machine-review.v1",
              "created_at_utc": datetime.now(timezone.utc).isoformat(), "film": str(film),
              "film_sha256": sha(film), "upload_readback": str(args.upload_readback.resolve()),
              "human_signoff": "not-provided", "frames": [], "sheets": []}
    for page_start in range(0, len(segments), 4):
        sheet = Image.new("RGB", (1322, 1726), "#1e1510")
        draw = ImageDraw.Draw(sheet)
        for local, segment in enumerate(segments[page_start:page_start + 4]):
            start = segment["start_ms"] / 1000
            duration = segment["duration_ms"] / 1000
            for stage, fraction in enumerate((0.22, 0.78)):
                timestamp = start + fraction * duration
                path = frames / f"{page_start + local + 1:02d}-{segment['cue_id']}-{stage + 1}.png"
                subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-ss",
                                f"{timestamp:.6f}", "-i", str(film), "-frames:v", "1", str(path)],
                               check=True, capture_output=True)
                with Image.open(path) as frame:
                    image = frame.convert("RGB")
                    if image.size != (2560, 1440):
                        raise ValueError(f"unexpected frame size {image.size} at {timestamp}")
                    image.thumbnail((640, 360), Image.Resampling.LANCZOS)
                    x, y = 18 + 658 * stage, 18 + 426 * local
                    sheet.paste(image, (x, y))
                draw.text((x + 6, y + 368), f"{segment['cue_id']}  {timestamp:.2f}s", font=font, fill="#f0e5cf")
                report["frames"].append({"cue_id": segment["cue_id"], "timestamp_seconds": timestamp,
                                         "path": str(path), "sha256": sha(path)})
        sheet_path = output / f"contact-{page_start // 4 + 1:02d}.png"
        sheet.save(sheet_path)
        report["sheets"].append({"path": str(sheet_path), "sha256": sha(sheet_path)})
    (output / "machine-review-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"frames": len(report["frames"]), "sheets": len(report["sheets"]),
                      "human_signoff": "not-provided"}))


if __name__ == "__main__":
    main()
