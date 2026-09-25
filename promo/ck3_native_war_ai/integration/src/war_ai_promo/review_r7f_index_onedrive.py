"""Machine-check the exact R7F MP4 only after OneDrive reports its upload."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

from .produce_r7e_same_battle import digest
from .audit_r61_film import CHINESE_NUMERAL, seconds


def call(argv: list[str], output: Path, label: str) -> bytes:
    (output / (label + ".argv.json")).write_text(
        json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = subprocess.run(argv, capture_output=True, check=False)
    (output / (label + ".stdout")).write_bytes(result.stdout)
    (output / (label + ".stderr")).write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode})")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", type=Path, required=True)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--upload-readback", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--subtitles", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    film = args.film.resolve(strict=True)
    receipt = json.loads(args.build_receipt.read_text(encoding="utf-8"))
    readback = json.loads(args.upload_readback.read_text(encoding="utf-8"))
    if (readback.get("status") != "uploaded" or readback.get("target") != film.name or
        readback.get("folder") != "CK3-War-AI-20260923"):
        raise ValueError("Exact OneDrive MP4 must be uploaded before machine review")
    if (film.name != Path(receipt["output"]).name or film.stat().st_size != receipt["output_bytes"] or
        digest(film) != receipt["output_sha256"]):
        raise ValueError("Uploaded local MP4 differs from the R7F build")
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    rows = inputs["cues"]
    if len(rows) != 23 or any(row.get("subtitle_mode") != "paragraph" for row in rows):
        raise ValueError("Expected 23 paragraph-caption cues")
    caption_events = Counter()
    for index, row in enumerate(rows, 1):
        subtitle = args.subtitles / f"{index:04d}-{row['id']}.ass"
        for line in subtitle.read_text(encoding="utf-8-sig").splitlines():
            if not line.startswith("Dialogue: "):
                continue
            parts = line.removeprefix("Dialogue: ").split(",", 9)
            if len(parts) != 10 or seconds(parts[2]) <= seconds(parts[1]):
                raise ValueError(f"Malformed or nonpositive caption: {subtitle}")
            language = "zh" if parts[3].startswith("Chinese") else "en"
            caption_events[language] += 1
            chunks = parts[9].replace("{\\q2}", "").split("\\N")
            if len(chunks) > 2:
                raise ValueError(f"More than two subtitle lines: {subtitle}")
            if (language == "zh" and len(chunks) == 2 and chunks[0] and chunks[1] and
                chunks[0][-1] in CHINESE_NUMERAL and chunks[1][0] in CHINESE_NUMERAL):
                raise ValueError(f"Chinese numeral split across lines: {subtitle}")
    if not caption_events["zh"] or not caption_events["en"]:
        raise ValueError("Missing Chinese or English subtitle events")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    probe = json.loads(call(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                             "-show_chapters", "-of", "json", str(film)],
                            args.output_dir, "probe"))
    chapters = probe.get("chapters", [])
    video = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    audio = [stream for stream in probe["streams"] if stream["codec_type"] == "audio"]
    duration = float(probe["format"]["duration"])
    if (len(chapters) != 23 or abs(duration - receipt["duration_seconds"]) > .15 or
        len(video) != 1 or (video[0]["width"], video[0]["height"]) != (2560, 1440) or
        len(audio) != 1 or audio[0]["codec_name"] != "aac" or
        int(audio[0]["sample_rate"]) != 48000 or audio[0]["channels"] != 2):
        raise ValueError("Uploaded R7F stream, duration or chapter mismatch")
    call(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(film),
          "-f", "null", "NUL"], args.output_dir, "full-decode")
    frame_rows = []
    firsts = [(float(chapter["start_time"]), float(chapter["end_time"])) for chapter in chapters]
    samples = [(f"opening-{index:02d}", second) for index, second in enumerate((1, 8, 18, 30), 1)]
    samples += [(f"chapter-{index:02d}", min(end - .2, start + max(2.0, (end - start) * .45)))
                for index, (start, end) in enumerate(firsts, 1)]
    for label, second in samples:
        target = args.output_dir / (label + ".png")
        call(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{second:.6f}",
              "-i", str(film), "-frames:v", "1", "-y", str(target)],
             args.output_dir, label)
        with Image.open(target) as image:
            if image.size != (2560, 1440):
                raise ValueError(f"Wrong review frame size: {label}")
            rgb = image.convert("RGB")
            header = rgb.getpixel((2500, 50))
            subtitle_bed = rgb.getpixel((10, 1300))
        expected = {"header": (53, 41, 31), "subtitle_bed": (33, 24, 19)}
        observed = {"header": header, "subtitle_bed": subtitle_bed}
        pass_palette = all(max(abs(a - b) for a, b in zip(observed[key], wanted)) <= 18
                           for key, wanted in expected.items())
        frame_rows.append({"label": label, "second": second, "path": str(target),
                           "sha256": digest(target), "palette": observed,
                           "palette_pass": pass_palette})
    if not all(row["palette_pass"] for row in frame_rows):
        raise ValueError("R7F uploaded film has off-palette sampled packaging")
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
    sheets = []
    chapter_rows = frame_rows[4:]
    for page in range(4):
        group = chapter_rows[page * 6:(page + 1) * 6]
        if not group:
            continue
        sheet = Image.new("RGB", (1296, len(group) // 2 * 390 + (len(group) % 2) * 390), "#211813")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(group):
            with Image.open(row["path"]) as frame:
                picture = frame.convert("RGB").resize((624, 351), Image.Resampling.LANCZOS)
            x = 16 + (index % 2) * 640
            y = 12 + (index // 2) * 390
            sheet.paste(picture, (x, y))
            draw.text((x, y + 354), f"{row['label']}  {row['second']:.1f}s", font=font, fill="#f0e5cf")
        target = args.output_dir / f"contact-{page + 1:02d}.png"
        sheet.save(target)
        sheets.append(str(target))
    report = {
        "schema": "ck3-war-ai-r7f-index-post-upload-machine-review.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "file": str(film), "bytes": film.stat().st_size, "sha256": digest(film),
        "duration_seconds": duration, "chapter_count": len(chapters),
        "source_build_receipt": str(args.build_receipt.resolve()),
        "upload_readback": str(args.upload_readback.resolve()),
        "full_decode": "GREEN", "palette_samples": len(frame_rows),
        "caption_events": dict(caption_events),
        "palette_all_pass": True, "frames": frame_rows,
        "contact_sheets": sheets, "human_1x_signoff": "not-provided",
    }
    (args.output_dir / "review-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": report["sha256"], "chapters": 23,
                      "palette_samples": len(frame_rows), "full_decode": "GREEN"}), flush=True)


if __name__ == "__main__":
    main()
