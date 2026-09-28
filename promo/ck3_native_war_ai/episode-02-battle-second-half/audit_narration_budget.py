"""Read-only timing audit against preserved EdgeTTS requests and MP3 files.

This never invokes a TTS provider. The JSON output is a forecast, not a voice take.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import subprocess
from pathlib import Path


CHAPTERS = (
    ("opening", 90),
    ("pursuit", 340),
    ("knights", 400),
    ("reinforcement", 515),
    ("terminal", 350),
    ("closing", 95),
)
CJK = re.compile(r"[\u3400-\u9fff]")
DIGITS = re.compile(r"\d+(?:[,.]\d+)*")
FOOTNOTE = re.compile(r"\[\^[^\]]+\]")
HEADER = re.compile(r"^## (\d{2}:\d{2})[–-](\d{2}:\d{2}) (.+)$", re.M)


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest().upper()}


def spoken_text(value: str) -> str:
    value = FOOTNOTE.sub("", value)
    value = value.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", value).strip()


def counts(text: str) -> dict:
    return {
        "cjk_characters": len(CJK.findall(text)),
        "digit_tokens": len(DIGITS.findall(text)),
        "latin_characters": len(re.findall(r"[A-Za-z]", text)),
        "punctuation_marks": len(re.findall(r"[，。；：！？、,.!?;:]", text)),
    }


def seconds(stamp: str) -> int:
    minute, second = map(int, stamp.split(":"))
    return minute * 60 + second


def extract_narration(draft: str) -> list[dict]:
    headers = list(HEADER.finditer(draft))
    if len(headers) != len(CHAPTERS):
        raise ValueError(f"expected {len(CHAPTERS)} timestamped sections, found {len(headers)}")
    rows = []
    for index, header in enumerate(headers):
        block = draft[header.end():headers[index + 1].start() if index + 1 < len(headers) else len(draft)]
        start = block.find("**旁白**：")
        end = block.find("**录制缺口**")
        if start < 0 or end <= start:
            raise ValueError(f"section {index + 1} lacks a bounded narration block")
        speech = spoken_text(block[start + len("**旁白**："):end])
        key, budget = CHAPTERS[index]
        if seconds(header.group(2)) - seconds(header.group(1)) != budget:
            raise ValueError(f"section {key} timestamp disagrees with planned budget")
        rows.append({"id": key, "title": header.group(3), "budget_seconds": budget, "text": speech, **counts(speech)})
    return rows


def probe_duration(ffprobe: str, media: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(media)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    duration = float(result.stdout.strip())
    if duration <= 0:
        raise ValueError(f"invalid audio duration: {media}")
    return duration


def reference_cues(directory: Path, ffprobe: str) -> list[dict]:
    rows = []
    for request in sorted(directory.glob("*.request.json")):
        payload = json.loads(request.read_text(encoding="utf-8"))
        if (payload.get("provider"), payload.get("voice"), payload.get("rate")) != ("edge-tts", "zh-CN-XiaoxiaoNeural", "-12%"):
            continue
        media = directory / (request.name.removesuffix(".request.json") + ".mp3")
        if not media.is_file():
            continue
        text = spoken_text(payload["text"])
        rows.append({"cue_id": payload["cue_id"], "request": identity(request), "media": identity(media),
                     "duration_seconds": probe_duration(ffprobe, media), **counts(text)})
    if len(rows) < 10:
        raise ValueError(f"not enough matching historical takes: {len(rows)}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--reference-speech", type=Path, required=True)
    parser.add_argument("--sample-manifest", type=Path)
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    draft = args.draft.read_text(encoding="utf-8-sig")
    chapters = extract_narration(draft)
    cues = reference_cues(args.reference_speech, args.ffprobe)
    total_chars = sum(row["cjk_characters"] for row in cues)
    total_seconds = sum(row["duration_seconds"] for row in cues)
    rate = total_chars / total_seconds
    cue_rates = sorted(row["cjk_characters"] / row["duration_seconds"] for row in cues)
    sample_summary = None
    if args.sample_manifest:
        manifest = json.loads(args.sample_manifest.read_text(encoding="utf-8"))
        if manifest["status"] != "samples-rendered-not-human-reviewed":
            raise ValueError("sample run is not fully rendered")
        samples = []
        for row in manifest["samples"]:
            request = Path(row["request"]["path"])
            media = Path(row["audio"]["path"])
            if identity(request)["sha256"] != row["request"]["sha256"] or identity(media)["sha256"] != row["audio"]["sha256"]:
                raise ValueError("sample artifact identity changed")
            payload = json.loads(request.read_text(encoding="utf-8"))
            if (payload["provider"], payload["voice"], payload["rate"]) != ("edge-tts", "zh-CN-XiaoxiaoNeural", "-12%"):
                raise ValueError("sample voice or rate mismatch")
            duration = probe_duration(args.ffprobe, media)
            if abs(duration - row["duration_seconds"]) > 0.01:
                raise ValueError("sample duration disagrees with preserved manifest")
            sample_counts = counts(payload["text"])
            samples.append({"name": row["name"], "request": identity(request), "audio": identity(media),
                            "duration_seconds": round(duration, 3), **sample_counts,
                            "historical_rate_prediction_seconds": round(sample_counts["cjk_characters"] / rate, 3)})
        sample_cjk = sum(row["cjk_characters"] for row in samples)
        sample_seconds = sum(row["duration_seconds"] for row in samples)
        sample_summary = {"manifest": identity(args.sample_manifest), "samples": samples,
                          "cjk_characters": sample_cjk, "digit_tokens": sum(row["digit_tokens"] for row in samples),
                          "audio_seconds": round(sample_seconds, 3),
                          "cjk_characters_per_second": round(sample_cjk / sample_seconds, 4),
                          "full_draft_extrapolation_seconds": round(sum(row["cjk_characters"] for row in chapters) * sample_seconds / sample_cjk, 1)}
    for chapter in chapters:
        chapter["estimated_speech_seconds"] = round(chapter["cjk_characters"] / rate, 1)
        chapter["estimated_headroom_seconds"] = round(chapter["budget_seconds"] - chapter["estimated_speech_seconds"], 1)
        del chapter["text"]
    result = {
        "schema": "ck3.episode02.narration-budget-audit.v1",
        "status": "historical-voice-rate-estimate-not-new-tts",
        "draft": identity(args.draft),
        "normalization": "only bounded **旁白** blocks; remove footnote citations and markdown markers; keep spoken words/numerals",
        "reference_voice": {"provider": "edge-tts", "voice": "zh-CN-XiaoxiaoNeural", "rate": "-12%",
                            "cue_count": len(cues), "cjk_characters": total_chars,
                            "digit_tokens": sum(row["digit_tokens"] for row in cues),
                            "latin_characters": sum(row["latin_characters"] for row in cues),
                            "audio_seconds": round(total_seconds, 3), "cjk_characters_per_second": round(rate, 4),
                            "median_cue_cjk_per_second": round(statistics.median(cue_rates), 4),
                            "min_cue_cjk_per_second": round(cue_rates[0], 4),
                            "max_cue_cjk_per_second": round(cue_rates[-1], 4),
                            "cues": cues},
        "current_draft_samples": sample_summary,
        "chapters": chapters,
        "budget_seconds": sum(chapter["budget_seconds"] for chapter in chapters),
        "draft_cjk_characters": sum(chapter["cjk_characters"] for chapter in chapters),
        "draft_digit_tokens": sum(chapter["digit_tokens"] for chapter in chapters),
        "draft_latin_characters": sum(chapter["latin_characters"] for chapter in chapters),
        "draft_punctuation_marks": sum(chapter["punctuation_marks"] for chapter in chapters),
        "estimated_speech_seconds": round(sum(chapter["estimated_speech_seconds"] for chapter in chapters), 1),
        "limits": ["Not a provider render or measured duration for this draft.",
                   "Arabic numerals, abbreviations, pauses, sentence boundaries and edits may change pacing.",
                   "Opening/closing chapter cards and required picture holds are outside the speech estimate."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "reference_cues": len(cues),
                      "reference_rate": round(rate, 3), "budget_seconds": result["budget_seconds"],
                      "reference_cjk": total_chars, "reference_digits": result["reference_voice"]["digit_tokens"],
                      "draft_cjk": result["draft_cjk_characters"], "draft_digits": result["draft_digit_tokens"],
                      "median_cue_rate": result["reference_voice"]["median_cue_cjk_per_second"],
                      "min_cue_rate": result["reference_voice"]["min_cue_cjk_per_second"],
                      "max_cue_rate": result["reference_voice"]["max_cue_cjk_per_second"],
                      "sample_seconds": sample_summary["audio_seconds"] if sample_summary else None,
                      "sample_cjk": sample_summary["cjk_characters"] if sample_summary else None,
                      "sample_digits": sample_summary["digit_tokens"] if sample_summary else None,
                      "sample_extrapolation_seconds": sample_summary["full_draft_extrapolation_seconds"] if sample_summary else None,
                      "samples": [{"name": x["name"], "cjk": x["cjk_characters"], "digits": x["digit_tokens"],
                                   "seconds": x["duration_seconds"], "historical_prediction": x["historical_rate_prediction_seconds"]}
                                  for x in sample_summary["samples"]] if sample_summary else None,
                      "estimated_speech_seconds": result["estimated_speech_seconds"],
                      "chapters": [{"id": c["id"], "cjk": c["cjk_characters"], "speech": c["estimated_speech_seconds"],
                                    "headroom": c["estimated_headroom_seconds"]} for c in chapters]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
