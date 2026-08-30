#!/usr/bin/env python3
"""Keep phase-two key coverage in the seven non-authoring locales.

Daily development authors Simplified Chinese and English only.  CK3 still
requires every active language to expose the same keys, so this generator
appends missing keys from the bounded English block as explicit placeholders.
Existing translated values in the canonical per-language files are preserved.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


MOD_ROOT = Path(__file__).resolve().parent.parent
SOURCE = MOD_ROOT / "localization" / "english" / "zg361_l_english.yml"
START_KEY = "zg361_view_result_statement_decision"
LANGUAGES = (
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)
BOM = b"\xef\xbb\xbf"


def phase2_lines() -> list[str]:
    lines = SOURCE.read_text(encoding="utf-8-sig").splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if line.lstrip().startswith(f"{START_KEY}:")
        )
    except StopIteration as exc:
        raise ValueError(f"phase-two localization marker missing from {SOURCE}") from exc
    selected = [
        line
        for line in lines[start:]
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not selected or not selected[-1].lstrip().startswith("zg361.53.a:"):
        raise ValueError("phase-two English localization block has an unexpected boundary")
    return selected


def outputs() -> dict[Path, bytes]:
    body = phase2_lines()
    source_by_key = {
        line.lstrip().split(":", 1)[0]: line
        for line in body
    }
    result: dict[Path, bytes] = {}
    for language in LANGUAGES:
        path = (
            MOD_ROOT
            / "localization"
            / language
            / f"zg361_l_{language}.yml"
        )
        if path.is_file():
            existing = path.read_text(encoding="utf-8-sig").splitlines()
            existing_keys = {
                line.lstrip().split(":", 1)[0]
                for line in existing
                if line.startswith(" ") and ":" in line
            }
            missing = [
                source_by_key[key]
                for key in source_by_key
                if key not in existing_keys
            ]
            lines = list(existing)
            if missing:
                lines.extend(
                    [
                        "",
                        " # English development placeholders for missing phase-two keys.",
                        *missing,
                    ]
                )
        else:
            lines = [
                f"l_{language}:",
                " # English development placeholders; not a release translation.",
                *body,
            ]
        result[path] = BOM + ("\n".join(lines) + "\n").encode("utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    stale: list[Path] = []
    for path, payload in outputs().items():
        if args.check:
            if not path.is_file() or path.read_bytes() != payload:
                stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    if stale:
        for path in stale:
            print(f"STALE: {path.relative_to(MOD_ROOT)}")
        return 1
    print(
        "GREEN: phase-two locale coverage "
        + ("is current" if args.check else "updated without replacing translations")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
