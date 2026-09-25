"""After OneDrive upload, sample each cue's actual frames for machine review."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--production-inputs", type=Path, required=True)
    parser.add_argument("--upload-readback", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    film = args.film.resolve(strict=True)
    upload = json.loads(args.upload_readback.read_text(encoding="utf-8"))
    if upload["status"] != "uploaded" or upload["target"] != film.name:
        raise ValueError("Visual review requires the exact OneDrive client upload readback first")
    rows = json.loads(args.production_inputs.read_text(encoding="utf-8"))["cues"]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    frames = output / "frames"
    frames.mkdir()
    report = {"schema": "ck3-r0217-math-pilot-machine-review.v1",
              "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
              "subject": {"path": str(film), "sha256": sha256(film)},
              "upload_readback": str(args.upload_readback.resolve(strict=True)),
              "human_signoff": "not-provided", "frames": [], "sheets": []}
    offset = 0.0
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 23)
    for group_start in (0, 4):
        sheet = Image.new("RGB", (1322, 1726), "#1e1510")
        draw = ImageDraw.Draw(sheet)
        for local_index, row in enumerate(rows[group_start:group_start + 4]):
            cue_index = group_start + local_index
            base = sum(float(item["duration_seconds"]) for item in rows[:cue_index])
            duration = float(row["duration_seconds"])
            for stage, fraction in enumerate((0.22, 0.78)):
                timestamp = base + fraction * duration
                path = frames / f"{row['id']}-{stage + 1}.png"
                argv = ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-ss",
                        f"{timestamp:.6f}", "-i", str(film), "-frames:v", "1", str(path)]
                subprocess.run(argv, check=True, capture_output=True)
                with Image.open(path) as source:
                    actual = source.convert("RGB")
                    if actual.size != (2560, 1440):
                        raise ValueError(f"Unexpected frame size {actual.size}")
                    actual.thumbnail((640, 360), Image.Resampling.LANCZOS)
                    x = 18 + stage * 658
                    y = 18 + local_index * 426
                    sheet.paste(actual, (x, y))
                draw.text((x + 6, y + 368), f"{row['id']}  {timestamp:.2f}s",
                          font=font, fill="#f0e5cf")
                report["frames"].append({"cue_id": row["id"], "timestamp_seconds": timestamp,
                                          "path": str(path), "sha256": sha256(path)})
        sheet_path = output / f"contact-{group_start // 4 + 1}.png"
        with sheet_path.open("xb") as stream:
            sheet.save(stream, format="PNG")
        report["sheets"].append({"path": str(sheet_path), "sha256": sha256(sheet_path)})
    (output / "machine-review-report.json").write_text(json.dumps(report, ensure_ascii=False,
                                                            indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"frames": len(report["frames"]), "sheets": len(report["sheets"]),
                      "human_signoff": "not-provided"}))


if __name__ == "__main__":
    main()
