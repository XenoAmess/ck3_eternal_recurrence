"""Extract only the 45 spoken paragraphs from the reviewed v3 director script.

This is an input bridge for the existing prepare_narration command. It does
not promote the old S30 storyboard or claim that v3 visuals are bound.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "narration-v3-review.md"
TRANSLATIONS = HERE / "english-captions-draft.json"
SCRIPT = HERE / "narration-spoken.json"
TIMELINE = HERE / "timeline.json"

HEADING = re.compile(r"^### V3-(\d{2}) · (.+)$", re.MULTILINE)
HAN = re.compile(r"[\u4e00-\u9fff]")
CHAPTERS = (
    (1, 2, "hook"),
    (3, 10, "declaration"),
    (11, 17, "targets"),
    (18, 23, "movement"),
    (24, 29, "help"),
    (30, 34, "battle-end"),
    (35, 42, "peace"),
    (43, 45, "epilogue"),
)


def chapter(number: int) -> str:
    return next(name for first, last, name in CHAPTERS if first <= number <= last)


def extract() -> tuple[list[dict], bytes]:
    raw = SOURCE.read_bytes()
    source = raw.decode("utf-8-sig")
    found = list(HEADING.finditer(source))
    if len(found) != 45 or [int(match.group(1)) for match in found] != list(range(1, 46)):
        raise ValueError("Expected ordered V3-01 through V3-45 sections")
    result = []
    for index, match in enumerate(found):
        section = source[match.end():found[index + 1].start() if index + 1 < len(found) else len(source)]
        opening = re.search(r"\*\*朗读\*\*\s*\n\s*([^\n]+)", section)
        if not opening or section.count("**朗读**") != 1:
            raise ValueError(f"Exactly one spoken paragraph required: {match.group(0)}")
        spoken = opening.group(1).strip()
        if any(value in spoken for value in ("**", "待拍/unbound", "（不朗读）")):
            raise ValueError(f"Production annotation leaked into speech: {match.group(0)}")
        result.append({"number": index + 1, "title": match.group(2).strip(), "zh": spoken})
    if sum(len(HAN.findall(row["zh"])) for row in result) != 7516:
        raise ValueError("Reviewed 7,516 Han-character speech contract changed")
    return result, raw


def build() -> tuple[dict, dict]:
    paragraphs, source = extract()
    translations = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    english = translations["captions"]
    if (translations["schema"] != "ck3-war-ai.v3-english-caption-draft.v1"
            or set(english) != {f"V3-{number:02d}" for number in range(1, 46)}
            or any(not isinstance(value, str) or not value.strip() or HAN.search(value)
                   for value in english.values())):
        raise ValueError("The draft English caption set must contain every v3 cue exactly once")
    cues, shots = [], []
    for row in paragraphs:
        number = row["number"]
        identifier = f"V3-{number:02d}"
        shot = f"S3-{number:02d}"
        section = chapter(number)
        cues.append({
            "id": identifier,
            "shot_id": shot,
            "chapter_id": section,
            "claim_ids": [],
            "zh": row["zh"],
            "en": english[identifier].strip(),
            "subtitle_translation_state": "editorial-draft-requires-review",
            "visual_binding_state": "unbound-v3-shot",
        })
        shots.append({
            "id": shot,
            "chapter_id": section,
            "title": row["title"],
            "visual_binding_state": "unbound-v3-shot",
            "cue_id": identifier,
        })
    script = {
        "format_version": 1,
        "kind": "ck3_native_war_ai_v3_spoken_narration",
        "source": "../narration-v3-review.md",
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "game_build": "1.19.0.6",
        "narration_locale": "zh-CN",
        "voice_candidate": "zh-CN-XiaoxiaoNeural",
        "media_binding_state": "unbound",
        "subtitle_translation_state": "editorial-draft-requires-review",
        "cues": cues,
    }
    timeline = {
        "format_version": 1,
        "kind": "ck3_native_war_ai_v3_narration_shot_index",
        "purpose": "Prepare narration and give every spoken cue a unique title; visual bindings pending",
        "source_sha256": script["source_sha256"],
        "shots": shots,
    }
    return script, timeline


def encoded(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Create both versioned JSON inputs once")
    parser.add_argument("--check", action="store_true", help="Check existing bytes without changing them")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("Choose exactly one of --write and --check")
    script, timeline = build()
    for path, data in ((SCRIPT, script), (TIMELINE, timeline)):
        expected = encoded(data)
        if args.write:
            with path.open("xb") as stream:
                stream.write(expected)
        elif path.read_bytes() != expected:
            raise ValueError(f"Generated input differs from checked-in bytes: {path}")
    print(f"V3 text contract PASS: {len(script['cues'])} spoken cues, 7516 Han characters; visual binding pending")


if __name__ == "__main__":
    main()
