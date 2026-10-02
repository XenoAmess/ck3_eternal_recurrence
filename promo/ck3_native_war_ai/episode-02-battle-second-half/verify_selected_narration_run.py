"""Read-only verification of source-bound Episode 2 EdgeTTS chapter assets.

The optional report is a machine audit only; it never creates human signoff.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CHAPTER_IDS = ("opening", "pursuit", "knights", "reinforcement", "terminal", "closing")
HEADER = re.compile(r"^## (\d{2}:\d{2})[–-](\d{2}:\d{2}) (.+)$", re.M)
FOOTNOTE = re.compile(r"\[\^[^\]]+\]")


def spoken(value: str) -> str:
    return re.sub(r"\s+", " ", FOOTNOTE.sub("", value).replace("**", "").replace("`", "")).strip()


def source_sections(draft_path: Path) -> dict[str, tuple[str, list[str]]]:
    draft = draft_path.read_text(encoding="utf-8-sig")
    headings = list(HEADER.finditer(draft))
    if len(headings) != len(CHAPTER_IDS):
        raise ValueError("frozen draft chapter count changed")
    sections = {}
    for index, heading in enumerate(headings):
        block = draft[heading.end():headings[index + 1].start()
                      if index + 1 < len(headings) else len(draft)]
        start = block.index("**旁白**：") + len("**旁白**：")
        end = block.index("**录制缺口**", start)
        source = block[start:end]
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", source) if part.strip()]
        sections[CHAPTER_IDS[index]] = (spoken(source), paragraphs)
    return sections


def file_identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper()}


def check_identity(record: dict) -> None:
    actual = file_identity(Path(record["path"]))
    if actual != record:
        raise ValueError(f"asset identity changed: {record['path']}")


def probe(ffprobe: str, media: Path) -> float:
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                             "-of", "json", str(media)], capture_output=True,
                            text=True, check=True, timeout=30)
    return float(json.loads(result.stdout)["format"]["duration"])


def verify(manifest_path: Path, ffprobe: str) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["schema"] != "ck3.episode02.selected-narration-render.v1" or \
            manifest["status"] != "selected-chapters-rendered-not-human-reviewed":
        raise ValueError("run is not a completed selected-chapter render")
    selected = manifest["selected_chapters"]
    if [row["id"] for row in manifest["chapters"]] != selected:
        raise ValueError("chapter coverage/order mismatch")
    if set(selected) & set(manifest["held_chapters"]):
        raise ValueError("held chapter was rendered")
    if set(selected) & {"terminal", "closing"}:
        if manifest.get("usage_scope") != "historical-independent-replays-candidate-only" or \
                manifest.get("new_e2_09_live_verified") is not False:
            raise ValueError("terminal/closing lacks historical candidate boundary")
    checked = 0

    def check(record: dict) -> None:
        nonlocal checked
        check_identity(record)
        checked += 1

    check(manifest["source_draft"])
    check(manifest["wheel"])
    for record in manifest["snapshots"].values():
        check(record)
    if manifest["snapshots"]["draft"]["sha256"] != manifest["source_draft"]["sha256"]:
        raise ValueError("frozen draft snapshot differs from source")
    sections = source_sections(Path(manifest["snapshots"]["draft"]["path"]))
    source_text_checks = 0
    for chapter in manifest["chapters"]:
        for key in ("audio", "concat_input", "concat_receipt", "probe"):
            check(chapter[key])
        if abs(probe(ffprobe, Path(chapter["audio"]["path"])) - chapter["speech_seconds"]) > 0.005:
            raise ValueError(f"chapter duration changed: {chapter['id']}")
        if json.loads(Path(chapter["concat_receipt"]["path"]).read_text(encoding="utf-8"))["returncode"] != 0:
            raise ValueError(f"chapter concat failed: {chapter['id']}")
        rows = [row for row in manifest["paragraphs"] if row["chapter_id"] == chapter["id"]]
        full_text, source_paragraphs = sections[chapter["id"]]
        if hashlib.sha256(full_text.encode("utf-8")).hexdigest().upper() != chapter["text_sha256"] or \
                len(source_paragraphs) != chapter["paragraph_count"]:
            raise ValueError(f"chapter text differs from frozen draft: {chapter['id']}")
        if len(rows) != chapter["paragraph_count"] or \
                [row["paragraph_index"] for row in rows] != list(range(len(rows))):
            raise ValueError(f"paragraph coverage/order mismatch: {chapter['id']}")
        for row in rows:
            for key in ("request", "audio", "response_events", "probe"):
                check(row[key])
            request = json.loads(Path(row["request"]["path"]).read_text(encoding="utf-8"))
            if (request["chapter_id"], request["paragraph_index"],
                request["source_paragraph_sha256"], request["text_sha256"]) != \
                    (row["chapter_id"], row["paragraph_index"], row["source_paragraph_sha256"],
                     row["text_sha256"]):
                raise ValueError("request source binding changed")
            if (request["provider"], request["voice"], request["rate"]) != \
                    (manifest["provider"], manifest["voice"], manifest["rate"]):
                raise ValueError("provider/voice/rate changed")
            if "usage_scope" in manifest and request.get("usage_scope") != manifest["usage_scope"]:
                raise ValueError("request usage scope changed")
            if hashlib.sha256(request["text"].encode("utf-8")).hexdigest().upper() != row["text_sha256"]:
                raise ValueError("request text SHA mismatch")
            source = source_paragraphs[row["paragraph_index"]]
            if (hashlib.sha256(source.encode("utf-8")).hexdigest().upper() != row["source_paragraph_sha256"] or
                    spoken(source) != request["text"]):
                raise ValueError("request text differs from frozen draft paragraph")
            source_text_checks += 1
            if abs(probe(ffprobe, Path(row["audio"]["path"])) - row["duration_seconds"]) > 0.005:
                raise ValueError("paragraph duration changed")
    check(manifest["duration_report"])
    check(manifest["attempt_events"])
    report = json.loads(Path(manifest["duration_report"]["path"]).read_text(encoding="utf-8"))
    if report["selected_chapters"] != selected or report["held_chapters"] != manifest["held_chapters"]:
        raise ValueError("duration report chapter scope changed")
    if "usage_scope" in manifest and (report.get("usage_scope") != manifest["usage_scope"] or
                                      report.get("new_e2_09_live_verified") is not False):
        raise ValueError("duration report usage boundary changed")
    total = round(sum(row["speech_seconds"] for row in manifest["chapters"]), 3)
    if report["selected_speech_seconds"] != total:
        raise ValueError("duration report total changed")
    return {"schema": "ck3.episode02.selected-narration-audit.v1",
            "status": "green-machine-identity-only-not-human-reviewed",
            "manifest": file_identity(manifest_path), "selected_chapters": selected,
            "held_chapters": manifest["held_chapters"],
            "paragraph_count": len(manifest["paragraphs"]), "asset_identity_checks": checked,
            "source_text_checks": source_text_checks,
            "selected_speech_seconds": total,
            "limits": ["No human 1x listening review or signoff is asserted.",
                       "No CK3 footage or new E2-09 result is asserted."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.manifest, args.ffprobe)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
