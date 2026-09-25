"""Readable bilingual captions using the timing basis bound to each cue."""
import html
import math
import re

from xar_promo.subtitles import AssCue, AssDocumentConfig, AssStyleConfig, SubtitleTrackConfig, render_ass_document

from .common import font


def timed_groups(value, start, end, language, mode="short"):
    size = 49 if language == "zh" else 31
    value = value.strip()
    if language == "zh":
        # Keep spoken Chinese numbers and recurring combat terms intact.
        tokens = re.findall(
            r"[零〇一二三四五六七八九十百千万亿两点]+|\d[\d,，.]*|"
            r"(?:死亡|伤亡|追击|坚韧|战宽|软伤|硬伤|兵团)|\s+|[^\s]", value)
    else:
        tokens = re.findall(r"\S+\s*", value)
    if not tokens:
        raise ValueError("Empty caption interval")
    measure = font(size, language == "zh").getlength
    if mode == "paragraph":
        target = len(value) + 1
    elif mode == "short":
        count = max(1, math.ceil((end - start) / 5.5), math.ceil(measure(value) / 2180))
        target = max(1, math.ceil(len(value) / count))
    else:
        raise ValueError(f"Unknown caption mode: {mode}")
    lines_or_groups = []
    current = ""
    for token in tokens:
        candidate = current + token
        if current and (len(candidate) > target or measure(candidate) > 2180):
            lines_or_groups.append(current.strip())
            current = token
        else:
            current = candidate
    if current.strip():
        lines_or_groups.append(current.strip())
    groups = (["\n".join(lines_or_groups[index:index + 2])
               for index in range(0, len(lines_or_groups), 2)]
              if mode == "paragraph" else lines_or_groups)
    weights = [len(group) for group in groups]
    total = sum(weights)
    if total <= 0 or end <= start:
        raise ValueError("Empty or nonpositive caption interval")
    cursor = start
    result = []
    for group, weight in zip(groups, weights):
        stop = min(end, cursor + (end - start) * weight / total)
        result.append((cursor, stop, group))
        cursor = stop
    return result


def caption_cues(row):
    duration = row["speech_duration_seconds"]
    mode = row.get("subtitle_mode", "short")
    events = [event for event in row.get("sentence_boundaries", []) if event.get("type") == "SentenceBoundary"]
    chinese = []
    for index, event in enumerate(events):
        start = max(0.0, event["offset"] / 10_000_000)
        end = min(duration, start + event["duration"] / 10_000_000)
        if index + 1 < len(events):
            end = min(end, events[index + 1]["offset"] / 10_000_000)
        chinese.extend(timed_groups(html.unescape(event["text"]), start, end, "zh", mode))
    if not chinese:
        chinese = timed_groups(row["zh"], .12, duration, "zh", mode)
    english = []
    sentences = [value for value in re.split(r"(?<=[.!?])\s+", row["en"].strip()) if value]
    total = sum(map(len, sentences))
    cursor = chinese[0][0]
    available = duration - cursor
    for sentence in sentences:
        end = cursor + available * len(sentence) / total
        english.extend(timed_groups(sentence, cursor, end, "en", mode))
        cursor = end
    return [AssCue(f"{language}-{index}", language, start, end, text)
            for language, groups in [("zh", chinese), ("en", english)]
            for index, (start, end, text) in enumerate(groups)]


def subtitle_document(row):
    gameplay = row.get("visual_kind") == "gameplay"
    card_style = AssStyleConfig(
        name="ChineseCard" if gameplay else "Chinese",
        font_name="Microsoft YaHei", font_size=49, bold=True,
        alignment=2, margin_left=145, margin_right=145,
        margin_vertical=178, outline=2.5)
    cues = caption_cues(row)
    if gameplay:
        # Gameplay shots need top captions to keep the combat panel visible.
        # Hybrid shots change to a card after the gameplay interval; keep the
        # card title clear by moving the remaining captions back to the bottom.
        cut = min(float(row["gameplay_seconds"]), float(row["duration_seconds"]) - 5)
        tracks = [
            SubtitleTrackConfig("zh-gameplay", "zh-CN", 2, AssStyleConfig(
                name="ChineseGameplay", font_name="Microsoft YaHei",
                font_size=49, bold=True, alignment=8,
                margin_left=145, margin_right=145,
                margin_vertical=260, outline=2.5)),
            SubtitleTrackConfig("zh-card", "zh-CN", 2, card_style),
        ]
        positioned = []
        for cue in cues:
            if cue.track_id != "zh":
                continue
            if cue.start_seconds < cut:
                positioned.append(AssCue(cue.cue_id + "-gameplay", "zh-gameplay",
                                         cue.start_seconds, min(cue.end_seconds, cut), cue.text))
            if cue.end_seconds > cut:
                positioned.append(AssCue(cue.cue_id + "-card", "zh-card",
                                         max(cue.start_seconds, cut), cue.end_seconds, cue.text))
        cues = positioned
    else:
        tracks = [
            SubtitleTrackConfig("zh", "zh-CN", 2, card_style),
            SubtitleTrackConfig("en", "en", 1, AssStyleConfig(
                name="English", font_name="Microsoft YaHei", font_size=31,
                bold=False, primary_colour="&H00BBC4C9",
                margin_left=145, margin_right=145,
                margin_vertical=65, outline=2)),
        ]
    return render_ass_document(
        AssDocumentConfig(row["shot_title"], 2560, 1440, duration_seconds=row["duration_seconds"]),
        tracks, cues, available_font_names={"Microsoft YaHei"})
