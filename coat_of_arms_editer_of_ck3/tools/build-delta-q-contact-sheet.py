from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CELL = 230
GAP = 18
LABEL = 26
BACKGROUND = (24, 21, 18)
PANEL = (43, 38, 32)
FOREGROUND = (236, 225, 207)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fitted(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = source.convert("RGBA")
    image.thumbnail((CELL, CELL), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CELL, CELL), PANEL + (255,))
    canvas.alpha_composite(image, ((CELL - image.width) // 2, (CELL - image.height) // 2))
    return canvas.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic Delta-Q anonymous A/B sheet.")
    parser.add_argument("--repository", type=Path, default=Path(".."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repository = args.repository.resolve()
    project = repository / "coat_of_arms_editer_of_ck3"
    corpus = json.loads((project / "e2e/fixtures/pictures/cases.json").read_text(encoding="utf-8"))
    baseline = repository / "docs/coat-of-arms-fit-artifacts/user-picture-corpus-v14-pareto-budget-1024"
    final = repository / "docs/coat-of-arms-fit-artifacts/delta-q-residual-repair-v1/real-budget-1024-v9-final-quality-first"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    width = GAP * 4 + CELL * 3
    row_height = LABEL + CELL + GAP
    height = LABEL + GAP + row_height * len(corpus["cases"])
    sheet = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    headers = ("INPUT", "A", "B")
    for column, header in enumerate(headers):
        draw.text((GAP + column * (CELL + GAP), GAP), header, fill=FOREGROUND, font=font)

    mappings = []
    for row, case in enumerate(corpus["cases"]):
        case_id = case["id"]
        input_path = project / "e2e/fixtures/pictures" / case["file"]
        old_path = baseline / case_id / "canonical-preview-230.png"
        new_path = final / case_id / "canonical-preview-230.png"
        final_is_a = hashlib.sha256(f"delta-q-ab-v1:{case_id}".encode("ascii")).digest()[0] % 2 == 0
        a_path, b_path = (new_path, old_path) if final_is_a else (old_path, new_path)
        y = LABEL + GAP + row * row_height
        draw.text((GAP, y), case_id, fill=FOREGROUND, font=font)
        image_y = y + LABEL
        for column, path in enumerate((input_path, a_path, b_path)):
            sheet.paste(fitted(path), (GAP + column * (CELL + GAP), image_y))
        mappings.append({
            "id": case_id,
            "input": {"path": str(input_path.relative_to(repository)).replace("\\", "/"), "sha256": sha256(input_path)},
            "A": {"role": "delta-q" if final_is_a else "v14", "sha256": sha256(a_path)},
            "B": {"role": "v14" if final_is_a else "delta-q", "sha256": sha256(b_path)},
        })

    sheet_path = output / "contact-sheet.png"
    sheet.save(sheet_path, format="PNG", optimize=False)
    receipt = {
        "schema": "ck3-coa-delta-q-anonymous-ab-v1",
        "status": "pending-human-review",
        "assignment": "sha256(delta-q-ab-v1:<case-id>)[0] parity",
        "sheet": {
            "path": sheet_path.name,
            "width": sheet.width,
            "height": sheet.height,
            "sha256": sha256(sheet_path),
        },
        "cases": mappings,
        "boundary": "Machine-generated review material only; no human preference or signoff is inferred.",
    }
    (output / "mapping.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt["sheet"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
