"""Episode 2 EdgeTTS sentence timing checks; no media or provider side effects."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re


HISTORICAL_SCOPE = "historical-independent-replays-candidate-only"
TICKS_PER_SECOND = 10_000_000


def identity(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest().upper()}


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _positive_seconds(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a positive number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return number


def derive_boundaries(chapter_id: str, paragraphs: list[dict],
                      read_files) -> tuple[list[dict], str, float]:
    """Rebuild chapter-relative Edge events from exact request/event bytes.

    `read_files` returns (request Path, events Path) for a paragraph row. The
    caller must first verify those files against preserved SHA/byte identities.
    """
    if not isinstance(paragraphs, list) or not paragraphs:
        raise ValueError(f"{chapter_id} has no source TTS paragraphs")
    cues: list[dict] = []
    source_text: list[str] = []
    base_ticks = 0
    last_start = -1
    last_end = -1
    for index, paragraph in enumerate(paragraphs):
        if paragraph.get("paragraph_index") != index:
            raise ValueError(f"{chapter_id} TTS paragraph order changed")
        duration = _positive_seconds(paragraph.get("duration_seconds"),
                                     f"{chapter_id} paragraph duration")
        request_path, events_path = read_files(paragraph)
        request = json.loads(request_path.read_text(encoding="utf-8"))
        if (request.get("provider") != "edge-tts"
                or request.get("chapter_id") != chapter_id
                or request.get("paragraph_index") != index
                or not isinstance(request.get("text"), str)
                or not request["text"].strip()
                or request.get("text_sha256", "").upper() !=
                hashlib.sha256(request["text"].encode("utf-8")).hexdigest().upper()):
            raise ValueError(f"{chapter_id} TTS request identity/text changed: {index}")
        if request.get("text_sha256", "").upper() != paragraph.get("text_sha256", "").upper():
            raise ValueError(f"{chapter_id} TTS paragraph text SHA changed: {index}")
        source_text.append(request["text"])
        events = []
        for line in events_path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("type") == "SentenceBoundary":
                events.append(event)
        if not events or compact("".join(item.get("text", "") for item in events)) != compact(request["text"]):
            raise ValueError(f"{chapter_id} Edge sentence text does not cover request: {index}")
        for event in events:
            offset = event.get("offset")
            length = event.get("duration")
            text = event.get("text")
            if (type(offset) is not int or type(length) is not int
                    or offset < 0 or length <= 0 or not isinstance(text, str) or not text.strip()
                    or offset + length > round(duration * TICKS_PER_SECOND) + 1_500_000):
                raise ValueError(f"{chapter_id} invalid Edge sentence time: {index}")
            start = base_ticks + offset
            end = start + length
            if start < last_start or end < last_end:
                raise ValueError(f"{chapter_id} sentence boundaries are not monotonic")
            cues.append({"type": "SentenceBoundary", "offset": start,
                         "duration": length, "text": text})
            last_start, last_end = start, end
        base_ticks += round(duration * TICKS_PER_SECOND)
    return cues, compact("".join(source_text)), last_end / TICKS_PER_SECOND


def require_audio_coverage(chapter_id: str, events: list[dict], speech_seconds: float,
                           last_end: float) -> None:
    speech = _positive_seconds(speech_seconds, f"{chapter_id} speech duration")
    if (not events or events[0]["offset"] / TICKS_PER_SECOND > 1.0
            or last_end > speech + .15 or speech - last_end > .15):
        raise ValueError(f"{chapter_id} sentence timing does not cover the source audio")
