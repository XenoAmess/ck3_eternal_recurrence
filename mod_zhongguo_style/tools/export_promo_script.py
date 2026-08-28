#!/usr/bin/env python3
"""Export a human review copy of the authoritative promo JSON script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import build_promo_video as promo  # noqa: E402


def _timecode(seconds: float) -> str:
    whole = int(round(seconds))
    minutes, remainder = divmod(whole, 60)
    return f"{minutes:02d}:{remainder:02d}"


def render(manifest_path: Path) -> str:
    manifest, chapters = promo.load_manifest(manifest_path)
    rows = [
        "<!-- GENERATED FILE: edit promo-manifest.json, then rerun export_promo_script.py -->",
        "",
        "# 361 宣传片中文配音与英文字幕审阅稿",
        "",
        "权威输入：`promo-manifest.json`。中文是 Xiaoxiao 配音和主字幕；每条英文与同一中文 cue 同时显示。",
        f"离线估算总时长：`{_timecode(float(manifest['_estimated_duration_seconds']))}`；硬上限 `<20:00`。",
        "",
    ]
    cursor = 0.0
    for chapter in chapters:
        end = cursor + chapter.estimated_duration_seconds
        rows.extend(
            [
                f"## {_timecode(cursor)}–{_timecode(end)} · {chapter.title_zh}",
                "",
                f"*{chapter.title_en}*  ",
                f"状态：`{chapter.material_status}` / `{chapter.status_en}`",
                "",
            ]
        )
        for index, cue in enumerate(chapter.promo_cues, start=1):
            rows.extend(
                [
                    f"**{index}. 中文配音 / 主字幕**",
                    "",
                    cue["zh"],
                    "",
                    "**English subtitle**",
                    "",
                    cue["en"],
                    "",
                ]
            )
        cursor = end
    return "\n".join(rows).rstrip() + "\n"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--check", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        rendered = render(args.manifest.expanduser().resolve())
        output = args.output.expanduser().resolve()
        if args.check:
            if not output.is_file():
                print(f"RED: generated script is missing: {output}", file=sys.stderr)
                return 2
            existing = output.read_text(encoding="utf-8-sig")
            if existing != rendered:
                print(
                    "RED: generated script is stale; rerun export_promo_script.py",
                    file=sys.stderr,
                )
                return 2
            print(f"GREEN: generated promo script is current: {output}")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"WROTE: {output}")
        return 0
    except promo.PromoError as exc:
        print(f"RED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
