"""Make per-chapter contact sheets from a hashed xar-promo review package."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-package", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    package = json.loads(args.review_package.read_text(encoding="utf-8"))
    if package["state"] != "pending-human-review" or package["approval_granted"]:
        raise ValueError("Expected unsigned machine review package")
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in package["frames"]:
        path = args.review_package.parent / row["path"]
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"].upper():
            raise ValueError(f"Review frame changed: {row['id']}")
        for chapter_id in row["chapter_ids"]:
            groups[chapter_id].append(row)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
    report = {"package_sha256": digest(args.review_package), "chapter_sheets": []}
    for chapter_id, rows in groups.items():
        width, height, gap, label = 640, 360, 18, 38
        columns = 2
        lines = (len(rows) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * (width + gap) + gap,
                                  lines * (height + label + gap) + gap), "#1e1510")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(rows):
            x = gap + (index % columns) * (width + gap)
            y = gap + (index // columns) * (height + label + gap)
            with Image.open(args.review_package.parent / row["path"]) as frame:
                frame = frame.convert("RGB")
                frame.thumbnail((width, height), Image.Resampling.LANCZOS)
                sheet.paste(frame, (x, y))
            draw.text((x + 6, y + height + 4),
                      f"{row['id']}  {row['timestamp_seconds']}s  {','.join(row['roles'])}",
                      fill="#f4e7ce", font=font)
        output = args.output_dir / f"{chapter_id}-contact-sheet.png"
        with output.open("xb") as stream:
            sheet.save(stream, format="PNG")
        report["chapter_sheets"].append({"chapter_id": chapter_id, "frames": len(rows),
                                         "path": str(output), "sha256": digest(output)})
    (args.output_dir / "contact-sheet-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": len(groups), "frames": len(package["frames"])}))


if __name__ == "__main__":
    main()
