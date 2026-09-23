"""Readable bilingual captions using the timing basis bound to each cue."""
import html
import re

from xar_promo.subtitles import AssCue, AssDocumentConfig, AssStyleConfig, SubtitleTrackConfig, render_ass_document

from .common import lines


def timed_groups(value, start, end, language):
    size = 49 if language == "zh" else 31
    wrapped = lines(value.strip(), size, 2180, language == "zh")
    groups = [wrapped[i:i + 2] for i in range(0, len(wrapped), 2)]
    weights = [sum(len(line) for line in group) for group in groups]
    total = sum(weights)
    if total <= 0 or end <= start:
        raise ValueError("Empty or nonpositive caption interval")
    cursor = start
    result = []
    for group, weight in zip(groups, weights):
        stop = min(end, cursor + (end - start) * weight / total)
        result.append((cursor, stop, "\n".join(group)))
        cursor = stop
    return result


def caption_cues(row):
    duration = row["speech_duration_seconds"]
    events = [event for event in row.get("sentence_boundaries", []) if event.get("type") == "SentenceBoundary"]
    chinese = []
    for index, event in enumerate(events):
        start = max(0.0, event["offset"] / 10_000_000)
        end = min(duration, start + event["duration"] / 10_000_000)
        if index + 1 < len(events):
            end = min(end, events[index + 1]["offset"] / 10_000_000)
        chinese.extend(timed_groups(html.unescape(event["text"]), start, end, "zh"))
    if not chinese:
        chinese = timed_groups(row["zh"], .12, duration, "zh")
    english = []
    sentences = [value for value in re.split(r"(?<=[.!?])\s+", row["en"].strip()) if value]
    total = sum(map(len, sentences))
    cursor = chinese[0][0]
    available = duration - cursor
    for sentence in sentences:
        end = cursor + available * len(sentence) / total
        english.extend(timed_groups(sentence, cursor, end, "en"))
        cursor = end
    return [AssCue(f"{language}-{index}", language, start, end, text)
            for language, groups in [("zh", chinese), ("en", english)]
            for index, (start, end, text) in enumerate(groups)]


def subtitle_document(row):
    tracks = [
        SubtitleTrackConfig("zh", "zh-CN", 2, AssStyleConfig(
            name="Chinese", font_name="Microsoft YaHei", font_size=49, bold=True,
            margin_left=145, margin_right=145, margin_vertical=178, outline=2.5)),
        SubtitleTrackConfig("en", "en", 1, AssStyleConfig(
            name="English", font_name="Microsoft YaHei", font_size=31, bold=False,
            primary_colour="&H00BBC4C9", margin_left=145, margin_right=145,
            margin_vertical=65, outline=2)),
    ]
    return render_ass_document(
        AssDocumentConfig(row["shot_title"], 2560, 1440, duration_seconds=row["duration_seconds"]),
        tracks, caption_cues(row), available_font_names={"Microsoft YaHei"})
