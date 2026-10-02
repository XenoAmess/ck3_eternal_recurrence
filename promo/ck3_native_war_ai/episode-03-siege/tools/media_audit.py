"""Audit one exact Episode 3 movie; retain machine evidence and pending review.

Run with the explicitly verified project venv, for example (CMD):
  <verified-python> media_audit.py --run <prepared-run> --output-dir <new-attempt>

The run supplies final-artifact.json, timeline.json, subtitle-tracks.json,
dry-master.json, music-policy.json and fonts.json. Subtitle tracks contain
{path, global_start, duration, chapter_id, fonts_dir}; their ASS times are local.
Explicit --video/--timeline/--subtitles/--narration/--music inputs are also
accepted. --subtitles describes a single global ASS; --subtitle-tracks accepts
the producer's track receipt. Music gains/fades come from the policy or explicit
CLI flags, never from an inferred listening result.

Output is a NEW directory containing input bindings, command logs, full AV
decode, audio levels/silence intervals, retained decoded comparison stems,
actual final frames, libass RGBA glyph layers/bounds, timing/text bindings,
final-bound-probe.json, a pending-human-review package and media-report.json.
If a native manifest is supplied/found, real final frames are preserved and
audited with public toolchain APIs against its existing e3-deliverable.

Exit 0 = declared machine conditions passed, HUMAN REVIEW STILL PENDING.
Exit 2 = RED; diagnostics/partials remain. No overwrite, provider, live game,
upload, playback, or human signoff is performed. Pixel samples and audio
comparison windows do not establish full 1x human viewing/listening, semantic
correctness, or approval. Every changed final byte requires a new audit attempt.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import dataclasses
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback

import numpy as np
from PIL import Image
from xar_promo import append_automated_audit_record, probe_and_write_bound_media
from xar_promo.audit import write_audit_report
from xar_promo.evidence import (
    bind_external_artifact, write_evidence_bundle_v2, write_sampling_plan_v2,
)
from xar_promo.operations import preserve_artifact
from xar_promo.project import load_document
from xar_promo.render import ass_burn_in_filter, escape_filter_value
from xar_promo.review_commands import run_review_command


def stamp():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(json_value(value), stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def json_value(value):
    # Public review results contain immutable MappingProxyType values; asdict
    # deep-copies these and fails. Retain their structure without copying them.
    if dataclasses.is_dataclass(value):
        return {field.name: json_value(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    # Decimal timestamps and enum-like public API fields retain their exact
    # printable value in the informational review command result.
    return str(value)


def ref(path):
    path = Path(path).resolve(strict=True)
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"Input changed while hashing: {path}")
    return {"path": str(path), "bytes": after.st_size,
            "sha256": digest.hexdigest().upper()}


def pin_matches(actual, expected):
    return (actual["bytes"] == expected["bytes"]
            and actual["sha256"].upper() == expected["sha256"].upper())


def referenced_path(value, base):
    if isinstance(value, dict):
        value = value["path"]
    path = Path(value)
    return path if path.is_absolute() else base / path


class Audit:
    def __init__(self, output, subject):
        self.output, self.subject = output, subject
        self.checks, self.commands = {}, []

    def check(self, name, passed, detail):
        self.checks[name] = {"passed": bool(passed), "detail": detail}

    def command(self, name, argv):
        stem = self.output / "commands" / name
        stem.parent.mkdir(parents=True, exist_ok=True)
        started = stamp()
        with stem.with_suffix(".stdout.txt").open("xb") as stdout:
            with stem.with_suffix(".stderr.txt").open("xb") as stderr:
                result = subprocess.run([str(v) for v in argv], stdout=stdout,
                                        stderr=stderr, check=False)
        record = {"started_utc": started, "finished_utc": stamp(),
                  "argv": [str(v) for v in argv], "exit_code": result.returncode,
                  "stdout": str(stem.with_suffix(".stdout.txt")),
                  "stderr": str(stem.with_suffix(".stderr.txt"))}
        write(stem.with_suffix(".json"), record)
        self.commands.append(record)
        if result.returncode:
            raise RuntimeError(f"{name} exited {result.returncode}; retained {stem}")
        return (stem.with_suffix(".stdout.txt").read_text(encoding="utf-8", errors="replace"),
                stem.with_suffix(".stderr.txt").read_text(encoding="utf-8", errors="replace"))


def ass_time(text):
    hours, minutes, seconds = text.strip().split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def plain(text):
    text = re.sub(r"\{[^}]*\}", "", text)
    text = text.replace(r"\N", " ").replace(r"\n", " ").replace(r"\h", " ")
    return re.sub(r"\s+", "", text)


def parse_ass(path):
    section, event_format, styles, events = "", [], {}, []
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("["):
            section = line
        elif section == "[V4+ Styles]" and line.startswith("Style:"):
            values = line.split(":", 1)[1].strip().split(",")
            styles[values[0]] = {"font_name": values[1], "font_size": values[2]}
        elif section == "[Events]" and line.startswith("Format:"):
            event_format = [v.strip() for v in line.split(":", 1)[1].split(",")]
        elif section == "[Events]" and line.startswith("Dialogue:"):
            if not event_format:
                raise ValueError(f"ASS Events Format missing: {path}")
            values = line.split(":", 1)[1].strip().split(",", len(event_format) - 1)
            event = dict(zip(event_format, values, strict=True))
            events.append({"start": ass_time(event["Start"]),
                           "end": ass_time(event["End"]),
                           "style": event["Style"], "text": event["Text"]})
    if not events:
        raise ValueError(f"No ASS dialogue events: {path}")
    return styles, events


def freeze_font_pins(value, base):
    result = []
    if isinstance(value, dict):
        if all(k in value for k in ("path", "bytes", "sha256")):
            actual = ref(referenced_path(value, base))
            if not pin_matches(actual, value):
                raise ValueError(f"Font bytes changed: {actual['path']}")
            result.append(actual)
        else:
            for child in value.values():
                result.extend(freeze_font_pins(child, base))
    elif isinstance(value, list):
        for child in value:
            result.extend(freeze_font_pins(child, base))
    return result


def cue_rows(timeline):
    rows = []
    for chapter in timeline["chapters"]:
        for index, cue in enumerate(chapter.get("utterances", [])):
            rows.append({**cue, "key": cue.get("key", cue.get("id", f"{chapter['id']}/{index}")),
                         "chapter_id": chapter["id"],
                         "global_start": float(cue.get("global_start", chapter["global_start"]
                                              + cue.get("local_start", 0))),
                         "duration": float(cue["duration"])})
    return rows


def frame_samples(timeline, cues, duration, fps):
    samples = {}

    def add(seconds, reason):
        number = max(0, min(math.ceil(duration * fps) - 1, round(seconds * fps)))
        samples.setdefault(number, []).append(reason)
        return number

    add(0, "first-frame")
    add(max(0, duration - 1 / fps), "last-frame")
    for chapter in timeline["chapters"]:
        start, length = float(chapter["global_start"]), float(chapter["duration"])
        for when, label in [(start, "start"), (start + length / 2, "middle"),
                            (max(start, start + length - 2 / fps), "end")]:
            add(when, f"chapter:{chapter['id']}:{label}")
    for cue in cues:
        pad = min(.12, cue["duration"] / 4)
        for offset, label in [(pad, "start"), (cue["duration"] / 2, "middle"),
                              (cue["duration"] - pad, "end")]:
            add(cue["global_start"] + offset, f"cue:{cue['key']}:{label}")
    return samples


def extract_final_frames(audit, ffmpeg, video, samples, fps, video_start_seconds=0.):
    folder = audit.output / "final-frames"
    folder.mkdir()
    selected = sorted(samples)
    script = audit.output / "final-frame-filter.txt"
    # A flat addition chain exceeds FFmpeg's expression recursion limit on
    # a full episode. Keep the exact frame set with a balanced expression.
    terms = [f"eq(n,{number})" for number in selected]
    while len(terms) > 1:
        terms = [f"({terms[index]}+{terms[index + 1]})" if index + 1 < len(terms)
                 else terms[index] for index in range(0, len(terms), 2)]
    expression = terms[0] if terms else "0"
    script.write_text(f"[0:v:0]select='{expression}',showinfo=checksum=0[frames]\n", encoding="utf-8")
    _, log = audit.command("final-frames", [ffmpeg, "-hide_banner", "-nostdin", "-v", "info", "-n",
                  "-i", video, "-/filter_complex", script, "-map", "[frames]",
                  "-fps_mode", "vfr", "-frames:v", len(selected), "-pix_fmt", "rgb24",
                  folder / "frame-%05d.png"])
    files = sorted(folder.glob("frame-*.png"))
    if len(files) != len(selected):
        raise ValueError(f"Expected {len(selected)} final frames, received {len(files)}")
    # n/fps describes the render timeline, not a muxed presentation timestamp.
    # AAC concat can shift the video start. Bind each extracted image to its
    # decoder-reported PTS instead of silently labelling it with nominal time.
    time_base = re.search(r"config in time_base:\s*(\d+)/(\d+)", log)
    pts = re.findall(r"\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:", log)
    if time_base is None or len(pts) != len(selected):
        raise ValueError("Final frame extraction did not retain every actual PTS")
    numerator, denominator = map(int, time_base.groups())
    timestamps = [int(value) * numerator / denominator for value in pts]
    aligned = all(abs(actual - video_start_seconds - number / fps) <= 1e-5
                  for number, actual in zip(selected, timestamps, strict=True))
    audit.check("sampled_final_frame_pts", aligned,
                {"video_start_seconds": video_start_seconds,
                 "time_base": f"{numerator}/{denominator}",
                 "samples": len(selected), "method": "decoder PTS after frame-number selection"})
    return {number: {"frame_number": number, "seconds": actual,
                     "pts": int(value), "time_base": f"{numerator}/{denominator}",
                     "render_timeline_seconds": number / fps,
                     "video_start_seconds": video_start_seconds,
                     "reasons": samples[number], "frame": ref(path)}
            for number, path, actual, value in zip(selected, files, timestamps, pts, strict=True)}


def subtitle_audit(audit, ffmpeg, tracks, cues, frames, fps, width, height, margin):
    event_rows, timing, pixel_rows, frozen_ass = [], [], [], []
    all_pixels_ok, no_missing_glyphs = True, True
    for track_index, track in enumerate(tracks):
        path = Path(track["path"])
        frozen_ass.append(ref(path))
        styles, events = parse_ass(path)
        start, duration = float(track.get("global_start", 0)), float(track["duration"])
        start_frame = int(track.get("global_start_frame", round(start * fps)))
        duration_frames = int(track.get("duration_frames", round(duration * fps)))
        clock_aligned = (abs(start_frame / fps - start) <= 1e-6
                         and abs(duration_frames / fps - duration) <= 1e-6)
        audit.check(f"ass_track_{track_index}_frame_clock", clock_aligned,
                    {"global_start_frame": start_frame, "duration_frames": duration_frames,
                     "time_base": "1/30", "method": "integer producer burn clock, distinct from mux PTS"})
        for event in events:
            event_rows.append({**event, "track_index": track_index,
                               "global_start": start + event["start"],
                               "global_end": start + event["end"]})
        in_range = all(0 <= e["start"] < e["end"] <= duration + .04 for e in events)
        audit.check(f"ass_track_{track_index}_range", in_range,
                    {"track": track, "styles": styles, "events": len(events)})
        numbers = sorted(n for n in frames
                         if start_frame <= n < start_frame + duration_frames
                         and any(e["start"] <= (n - start_frame) / fps < e["end"] for e in events))
        if not numbers:
            raise ValueError(f"No active subtitle samples for {path}")
        folder = audit.output / "subtitle-pixels" / f"track-{track_index:03d}"
        folder.mkdir(parents=True)
        # Match the producer's integer frame clock before libass. Decimal
        # seconds divided by a microsecond TB can truncate 3.2s to 3199999us
        # and incorrectly keep the preceding ASS event at a cue boundary.
        local_frames = {number: number - start_frame for number in numbers}
        expression = str(local_frames[numbers[-1]])
        for index in range(len(numbers) - 2, -1, -1):
            expression = f"if(eq(N,{index}),{local_frames[numbers[index]]},{expression})"
        burn = ass_burn_in_filter(path) + ":alpha=1"
        if track.get("fonts_dir"):
            burn += ":fontsdir='" + escape_filter_value(track["fonts_dir"]) + "'"
        script = folder / "filter.txt"
        script.write_text(f"[0:v:0]format=rgba,settb=1/30,setpts='{expression}',{burn}[layer]\n",
                          encoding="utf-8")
        _, log = audit.command(f"subtitle-layer-{track_index:03d}",
                    [ffmpeg, "-hide_banner", "-nostdin", "-v", "info", "-n",
                     "-f", "lavfi", "-i", f"color=c=black@0.0:s={width}x{height}:r=30,format=rgba",
                     "-/filter_complex", script, "-map", "[layer]", "-frames:v", len(numbers),
                     "-fps_mode", "passthrough", "-pix_fmt", "rgba", folder / "layer-%05d.png"])
        no_missing_glyphs &= not bool(re.search(r"glyph.*not found|failed to find.*font", log, re.I))
        images = sorted(folder.glob("layer-*.png"))
        if len(images) != len(numbers):
            raise ValueError(f"Incomplete libass layers for {path}")
        for number, image in zip(numbers, images, strict=True):
            with Image.open(image) as source:
                layer = np.array(source.convert("RGBA"))
                box = source.getchannel("A").getbbox()
            inside = (box is not None and box[0] >= margin and box[1] >= margin
                      and box[2] <= width - margin and box[3] <= height - margin)
            # Compare opaque light glyph interiors against the ACTUAL final movie.
            # Shadows/outline and alpha edges are excluded; no OCR claim is made.
            mask = (layer[:, :, 3] >= 250) & (layer[:, :, :3].mean(axis=2) > 64)
            with Image.open(frames[number]["frame"]["path"]) as source:
                final_rgb = np.array(source.convert("RGB"))
            count = int(mask.sum())
            errors = np.abs(final_rgb.astype(np.int16) - layer[:, :, :3].astype(np.int16))
            matched = float((errors[mask].max(axis=1) <= 55).mean()) if count else 0.
            pixel_match = count >= 20 and matched >= .80
            all_pixels_ok &= inside and pixel_match
            pixel_rows.append({"track_index": track_index, "seconds": frames[number]["seconds"],
                               "render_timeline_seconds": number / fps,
                               "local_seconds": local_frames[number] / fps,
                               "local_frame_number": local_frames[number],
                               "ass_reference_time_base": "1/30",
                               "layer": ref(image), "final_frame": frames[number]["frame"],
                               "alpha_bbox": box, "safe_margin_pixels": margin,
                               "edge_clearance_pixels": [box[0], box[1], width - box[2], height - box[3]] if box else None,
                               "inside_safe_area": inside, "opaque_light_glyph_pixels": count,
                               "final_glyph_pixel_match_fraction": matched,
                               "passed": inside and pixel_match})
    for cue in cues:
        begin, end = cue["global_start"], cue["global_start"] + cue["duration"]
        for language in ("zh", "en"):
            matching = [e for e in event_rows if plain(e["text"]) == plain(cue[language])
                        and abs(e["global_start"] - begin) <= .04
                        and abs(e["global_end"] - end) <= .04]
            timing.append({"cue": cue["key"], "language": language, "start": begin, "end": end,
                           "matching_events": matching, "passed": len(matching) == 1})
    audit.check("subtitle_text_and_time_binding", all(r["passed"] for r in timing),
                {"cue_language_rows": len(timing), "method": "exact ASS plain text and global cue times, tolerance 40ms"})
    audit.check("subtitle_actual_pixels", all_pixels_ok,
                {"samples": len(pixel_rows), "safe_margin_pixels": margin,
                 "method": "actual libass/font RGBA bbox plus actual final encoded glyph-interior pixel comparison"})
    audit.check("subtitle_no_missing_glyph_diagnostics", no_missing_glyphs,
                "Retained libass logs inspected for missing glyph/font diagnostics; not a semantic reading test")
    write(audit.output / "subtitle-report.json", {"subject": audit.subject, "ass": frozen_ass,
          "timing": timing, "pixels": pixel_rows, "human_readability_review": "pending",
          "boundary": "Sampled static glyphs; no OCR, full-frame semantic verification or human signoff"})
    return frozen_ass


def audio_audit(audit, args, duration, timeline, narration, music, policy):
    _, volume_log = audit.command("audio-levels", [args.ffmpeg, "-hide_banner", "-nostdin",
              "-i", audit.subject["path"], "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"])
    def level(name):
        match = re.search(name + r":\s+(-?inf|[-\d.]+) dB", volume_log)
        if not match:
            raise ValueError(f"Missing {name} in volumedetect log")
        return float(match.group(1))
    mean, peak = level("mean_volume"), level("max_volume")
    audit.check("audio_present_and_not_clipped", math.isfinite(mean) and peak < args.peak_limit_dbfs,
                {"mean_dbfs": mean, "peak_dbfs": peak, "peak_limit_dbfs": args.peak_limit_dbfs,
                 "boundary": "Measured encoded peak/mean; not a listening assessment"})
    _, silence_log = audit.command("audio-silences", [args.ffmpeg, "-hide_banner", "-nostdin",
              "-i", audit.subject["path"], "-map", "0:a:0", "-af",
              f"silencedetect=noise={args.silence_noise_dbfs}dB:d={args.silence_duration}", "-f", "null", "-"])
    starts = [float(v) for v in re.findall(r"silence_start: ([-\d.]+)", silence_log)]
    ends = [float(v) for v in re.findall(r"silence_end: ([-\d.]+)", silence_log)]
    intervals = [{"start": s, "end": ends[i] if i < len(ends) else duration}
                 for i, s in enumerate(starts)]
    write(audit.output / "audio-levels.json", {"subject": audit.subject, "mean_dbfs": mean,
          "peak_dbfs": peak, "silence_noise_dbfs": args.silence_noise_dbfs,
          "silence_minimum_seconds": args.silence_duration, "silence_intervals": intervals,
          "boundary": "Silences are review material, including intentional pauses/fades; no invented hearing approval",
          "human_listening": "pending"})
    root = audit.output / "audio-proof"
    root.mkdir()
    fade_out_start = max(0., duration - policy["fade_out_seconds"])
    music_filter = (f"volume={policy['music_gain_db']}dB,afade=t=in:d={policy['fade_in_seconds']},"
                    f"afade=t=out:st={fade_out_start}:d={policy['fade_out_seconds']}")
    for name, path, filters, loop in [
            ("actual", audit.subject["path"], None, False),
            ("narration", narration, f"volume={policy['narration_gain_db']}dB", False),
            ("music", music, music_filter, policy["loop"])]:
        argv = [args.ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-n"]
        if loop:
            argv += ["-stream_loop", "-1"]
        argv += ["-i", path, "-map", "0:a:0"]
        if filters:
            argv += ["-af", filters]
        argv += ["-t", f"{duration:.9f}", "-ar", "8000", "-ac", "1", "-c:a", "pcm_f32le",
                 "-f", "f32le", root / f"{name}.f32"]
        audit.command(f"decode-{name}-stem", argv)
    actual, voice, bgm = [np.fromfile(root / f"{n}.f32", dtype="<f4")
                          for n in ("actual", "narration", "music")]
    lengths = {name: len(data) / 8000 for name, data in
               zip(("actual", "narration", "music"), (actual, voice, bgm), strict=True)}
    audit.check("decoded_audio_stems_span_final", all(abs(v - duration) < .15 for v in lengths.values()), lengths)
    n = min(len(actual), len(voice), len(bgm))
    if n < 8000:
        raise ValueError("Audio comparison requires at least one second")
    actual, voice, bgm = actual[:n], voice[:n], bgm[:n]
    fit_length = min(8 * 8000, n // 2)
    fit_begin = min(30 * 8000, max(240, (n - fit_length) // 2))
    expected = voice + bgm
    lags = list(range(-240, 241))
    errors = [float(np.mean((actual[fit_begin + lag:fit_begin + lag + fit_length]
                            - expected[fit_begin:fit_begin + fit_length]) ** 2)) for lag in lags]
    lag = lags[int(np.argmin(errors))]
    source_probe, _ = audit.command("music-source-probe", [args.ffprobe, "-v", "error", "-show_format",
                                                            "-of", "json", music])
    source_duration = float(json.loads(source_probe)["format"]["duration"])
    points = {float(c["global_start"]) + float(c["duration"]) / 2 for c in timeline["chapters"]}
    points.update([min(5., duration / 4), max(0., duration - min(12., duration / 4))])
    if policy["loop"]:
        points.update(float(t) + min(source_duration / 2, 40.)
                      for t in np.arange(0, duration, source_duration)
                      if t + min(source_duration / 2, 40.) < duration)
    rows = []
    for seconds in sorted(points):
        length = min(4 * 8000, n - 2 * abs(lag) - 1)
        begin = max(abs(lag), min(round(seconds * 8000), n - abs(lag) - length))
        end = begin + length
        residual, target = actual[begin + lag:end + lag] - voice[begin:end], bgm[begin:end]
        rms = lambda x: float(np.sqrt(np.mean(x * x)))
        target_rms = rms(target)
        correlation = float(np.corrcoef(residual, target)[0, 1]) if target_rms > 1e-6 else 0.
        gain = float(np.dot(residual, target) / np.dot(target, target)) if target_rms > 1e-6 else 0.
        error_ratio = rms(residual - target) / target_rms if target_rms > 1e-6 else None
        passed = (target_rms > 1e-6 and correlation > .90 and .85 < gain < 1.15
                  and error_ratio is not None and error_ratio < .5)
        rows.append({"seconds": begin / 8000, "duration": length / 8000,
                     "expected_music_rms": target_rms, "music_correlation": correlation,
                     "music_gain_ratio": gain, "residual_error_ratio": error_ratio, "passed": passed})
    audit.check("encoded_music_matches_declared_mix_windows", all(r["passed"] for r in rows),
                {"windows": len(rows), "global_sample_lag_at_8000hz": lag})
    write(audit.output / "music-presence.json", {"subject": audit.subject, "policy": policy,
          "music": ref(music), "narration": ref(narration), "decoded_seconds": lengths,
          "global_lag_samples_at_8000hz": lag, "windows": rows,
          "retained_stems": [ref(root / f"{name}.f32") for name in ("actual", "narration", "music")],
          "boundary": "Whole-duration decoding and sampled fixed-lag mix comparisons; not full human listening"})
    write(audit.output / "audio-review-plan.json", {"subject": audit.subject,
          "full_1x_continuous_review": "pending", "attention_windows": rows,
          "silence_intervals": intervals, "listen_for": ["narration intelligibility and pronunciation",
          "music balance under narration", "loop joins and chapter joins", "first/last fades and uninterrupted audio"],
          "human_signoff": "not-provided"})


def native_frame_audit(audit, manifest, frames, subject_id, prefix):
    loaded = load_document(manifest, check_files=True)
    record = next(a for a in loaded.run.artifacts if a.artifact_id == subject_id)
    root = manifest.parent
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", prefix):
        raise ValueError("Native audit artifact prefix must be a single artifact/folder identifier")
    native_output = root / "media-audit" / prefix
    native_output.mkdir(parents=True, exist_ok=False)
    source = root / record.path
    if not pin_matches(ref(source), audit.subject):
        raise ValueError("Native preserved deliverable differs from the audited final movie")
    producer = {"adapter_id": "ck3-native-war-ai-v1", "tool": "FFmpeg",
                "tool_version": (audit.output / "commands/ffmpeg-version.stdout.txt").read_text(
                    encoding="utf-8", errors="replace").splitlines()[0],
                "operation": "extract actual final movie frame at recorded frame/time", "execution": "external"}
    subject = bind_external_artifact(source, project_root=root, artifact_id=prefix + "-source",
                collection="derived", role="deliverable", label=source.name,
                media_type="video/mp4", producer=producer)
    rows, preserved = [], {}
    for index, frame in enumerate(frames.values()):
        saved = preserve_artifact(manifest, Path(frame["frame"]["path"]),
                    artifact_id=f"{prefix}-frame-{index:05d}", collection="derived", role="frame",
                    label=f"final frame {frame['frame_number']}", media_type="image/png")
        at = round(frame["seconds"], 6)
        preserved[at] = root / saved.path
        rows.append({"id": f"frame-{index:05d}", "kind": "video", "source": subject,
                     "start_seconds": at, "end_seconds": at})
    plan_path = native_output / "sampling-plan.json"
    plan = write_sampling_plan_v2(plan_path, rows, project_root=root, interval_seconds=1,
                                 required_roles=["frame"], external_producers={"frame": producer})
    submissions = [{"sample_id": s["id"], "role": "frame",
                    "path": str(preserved[round(float(s["timestamp_seconds"]), 6)]),
                    "media_type": "image/png", "producer": producer} for s in plan["samples"]]
    bundle = native_output / "evidence-bundle.json"
    write_evidence_bundle_v2(bundle, project_root=root, plan_path=plan_path, submissions=submissions)
    # The frames above are already immutable registered artifacts. The CLI audit
    # re-preserves all of them, rehashing the full manifest once per frame.
    # Keep the same public report verification and append only its three inputs.
    report_path = native_output / "native-frame-audit.json"
    verified = write_audit_report(report_path, project_root=root, subject=record,
                                  evidence_bundle_path=bundle, signoff_run_manifest_path=None)
    automated = verified["automated_audit"]
    if (automated["status"] != "passed" or automated["sample_count"] != len(frames)
            or automated["evidence_artifact_count"] != len(frames)
            or automated["subject_sha256"] != record.sha256
            or automated["manual_approval_granted"] is not False
            or verified["manual_signoff"] != {"state": "not-provided"}):
        raise ValueError("Native real-frame report failed binding, coverage or approval boundary")
    saved_inputs = []
    for suffix, path, role in (("plan", plan_path, "evidence-plan"),
                              ("bundle", bundle, "evidence-bundle"),
                              ("frames-audit", report_path, "audit")):
        saved_inputs.append(preserve_artifact(manifest, path,
                    artifact_id=prefix + "-" + suffix, collection="derived", role=role,
                    label=path.name, media_type="application/json"))
    registered = append_automated_audit_record(manifest,
                    check_id=automated["scope"], status=automated["status"],
                    subject_artifact_id=subject_id,
                    report_artifact_id=saved_inputs[-1].artifact_id)
    write(audit.output / "native-public-api.json", {
          "at_utc": stamp(), "toolchain_version": importlib.metadata.version("xar-promo-toolchain"),
          "interfaces": ["xar_promo.audit.write_audit_report",
                         "xar_promo.audit.verify_audit_report",
                         "xar_promo.preserve_artifact", "xar_promo.append_automated_audit_record"],
          "verified_report": ref(report_path), "audit_record": registered.to_dict(),
          "source_frame_count": len(frames), "human_signoff": "not-provided"})
    after = load_document(manifest, check_files=True)
    if len(after.run.signoffs) != len(loaded.run.signoffs):
        raise ValueError("Unexpected change to native human signoffs")
    write(audit.output / "native-frame-evidence.json", {
          "sampling_plan": ref(plan_path), "evidence_bundle": ref(bundle),
          "integrity_audit": ref(native_output / "native-frame-audit.json"),
          "manifest": str(manifest), "subject_artifact_id": subject_id,
          "human_signoffs_before": len(loaded.run.signoffs),
          "human_signoffs_after": len(after.run.signoffs)})


def arguments():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", type=Path, help="prepared run root; media inputs stay unchanged, existing native manifest receives frame/audit records")
    parser.add_argument("--output-dir", type=Path, required=True, help="new retained audit attempt; refuses existing directory")
    for name in ("video", "timeline", "subtitles", "subtitle-tracks", "narration", "music", "music-policy", "fonts", "native-manifest"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe"))
    parser.add_argument("--safe-margin", type=int, default=16, help="actual subtitle pixel margin on all edges; existing series layout uses 16px minimum")
    parser.add_argument("--peak-limit-dbfs", type=float, default=-.05)
    parser.add_argument("--silence-noise-dbfs", type=float, default=-50.)
    parser.add_argument("--silence-duration", type=float, default=2.)
    parser.add_argument("--music-gain-db", type=float)
    parser.add_argument("--narration-gain-db", type=float)
    parser.add_argument("--fade-in-seconds", type=float)
    parser.add_argument("--fade-out-seconds", type=float)
    parser.add_argument("--music-loop", action=argparse.BooleanOptionalAction, default=None,
                        help="explicit loop policy if no producer music-policy is provided")
    parser.add_argument("--subject-artifact-id", default="e3-deliverable")
    parser.add_argument("--audit-artifact-prefix", help="immutable native IDs; defaults to output-directory basename")
    args = parser.parse_args()
    if not args.ffmpeg or not args.ffprobe:
        parser.error("Explicit FFmpeg/FFprobe or verified PATH executables required")
    if args.safe_margin < 0 or args.silence_duration <= 0:
        parser.error("safe margin must be nonnegative and silence duration positive")
    return args


def main():
    args = arguments()
    output = args.output_dir.resolve()
    if output.exists():
        print("RED: output directory exists; use a new audit attempt", file=sys.stderr)
        return 2
    output.mkdir(parents=True)
    audit, input_pins = None, []
    try:
        base = args.run.resolve(strict=True) if args.run else Path.cwd()
        final = read(base / "final-artifact.json") if args.run else None
        video = args.video or (referenced_path(final, base) if final else None)
        timeline_path = args.timeline or base / "timeline.json"
        timeline = read(timeline_path)
        duration = float(timeline["total_duration"])
        if not video or duration <= 0:
            raise ValueError("Final video and a positive timeline.total_duration are required")
        subject = ref(video)
        if final and not pin_matches(subject, final):
            raise ValueError("Final-artifact binding differs from actual video")
        audit = Audit(output, subject)
        input_pins = [subject, ref(timeline_path)]
        tracks_path = args.subtitle_tracks or base / "subtitle-tracks.json"
        if args.subtitles:
            tracks = [{"path": str(args.subtitles.resolve(strict=True)), "global_start": 0., "duration": duration}]
        else:
            tracks = read(tracks_path)["tracks"]
            input_pins.append(ref(tracks_path))
        for track in tracks:
            track["path"] = str(referenced_path(track["path"], base).resolve(strict=True))
            if track.get("fonts_dir"):
                track["fonts_dir"] = str(referenced_path(track["fonts_dir"], base).resolve(strict=True))
            input_pins.append(ref(track["path"]))
        fonts_path = args.fonts or base / "fonts.json"
        font_pins = freeze_font_pins(read(fonts_path), base) if fonts_path.is_file() else []
        if fonts_path.is_file():
            input_pins += [ref(fonts_path), *font_pins]
        policy_path = args.music_policy or base / "music-policy.json"
        policy_source = read(policy_path) if policy_path.is_file() else (final or {}).get("music", {})
        if policy_path.is_file():
            input_pins.append(ref(policy_path))
        dry_path = base / "dry-master.json"
        dry_ref = read(dry_path) if dry_path.is_file() else None
        narration = args.narration or (referenced_path(dry_ref, base) if dry_ref else None)
        if not narration:
            raise ValueError("A dry narration artifact/--narration is required")
        if dry_ref:
            input_pins.append(ref(dry_path))
            if not pin_matches(ref(narration), dry_ref):
                raise ValueError("Dry narration differs from its producer binding")
        music = args.music or referenced_path(policy_source["source"], base)
        policy = {}
        aliases = {"fade_in_seconds": "fade_in", "fade_out_seconds": "fade_out"}
        for key in ("music_gain_db", "narration_gain_db", "fade_in_seconds", "fade_out_seconds"):
            explicit = getattr(args, key)
            policy[key] = float(explicit if explicit is not None else policy_source.get(key, policy_source.get(aliases.get(key, key))))
        policy["loop"] = args.music_loop if args.music_loop is not None else policy_source.get("loop")
        if not isinstance(policy["loop"], bool):
            raise ValueError("Explicit music loop policy required")
        if policy_source.get("normalize", False):
            raise ValueError("This series audit models fixed gains without normalization; input policy differs")
        if min(policy["fade_in_seconds"], policy["fade_out_seconds"]) <= 0:
            raise ValueError("Positive explicit music fades required")
        input_pins += [ref(narration), ref(music)]
        if policy_source.get("source", {}).get("sha256") and not pin_matches(ref(music), policy_source["source"]):
            raise ValueError("Music source binding changed")
        write(output / "input.json", {"at_utc": stamp(), "subject": subject, "inputs": input_pins,
              "font_pins": font_pins, "subtitle_tracks": tracks, "mix_policy": policy,
              "python": sys.executable, "python_version": sys.version,
              "toolchain_version": importlib.metadata.version("xar-promo-toolchain"),
              "ffmpeg": args.ffmpeg, "ffprobe": args.ffprobe, "human_signoff": "not-provided"})
        audit.command("ffmpeg-version", [args.ffmpeg, "-version"])
        audit.command("ffprobe-version", [args.ffprobe, "-version"])
        raw, _ = audit.command("final-probe", [args.ffprobe, "-v", "error", "-show_format",
                                               "-show_streams", "-show_chapters", "-of", "json", video])
        probe = json.loads(raw)
        write(output / "final-probe.json", probe)
        streams = probe["streams"]
        video_streams = [s for s in streams if s["codec_type"] == "video"]
        audio_streams = [s for s in streams if s["codec_type"] == "audio"]
        v, a = video_streams[0], audio_streams[0]
        fps = float(Fraction(v["r_frame_rate"]))
        audit.check("stream_shape", len(video_streams) == len(audio_streams) == 1
                    and v["codec_name"] == "h264" and (v["width"], v["height"], fps) == (1920, 1080, 30.)
                    and float(Fraction(v["avg_frame_rate"])) == 30.
                    and a["codec_name"] == "aac" and int(a["sample_rate"]) == 48000 and a["channels"] == 2,
                    {"video": v, "audio": a})
        durations = {"format": float(probe["format"]["duration"])}
        durations.update({name: float(stream["duration"]) for name, stream in (("video", v), ("audio", a)) if "duration" in stream})
        audit.check("duration_and_stream_alignment", all(abs(d - duration) < .15 for d in durations.values())
                    and max(durations.values()) - min(durations.values()) < .15,
                    {"expected": duration, "actual": durations, "tolerance_seconds": .15})
        chapters = probe.get("chapters", [])
        wanted = timeline["chapters"]
        chapter_match = len(chapters) == len(wanted) and all(
            abs(float(actual["start_time"]) - float(expected["global_start"])) < .04
            and abs(float(actual["end_time"]) - float(expected["global_start"]) - float(expected["duration"])) < .15
            and actual.get("tags", {}).get("title") == expected["title"]
            for actual, expected in zip(chapters, wanted))
        audit.check("chapters_match_timeline", chapter_match, {"expected": wanted, "actual": chapters})
        cues = cue_rows(timeline)
        audit.check("cue_ranges", bool(cues) and all(c["duration"] > 0 and c["global_start"] >= 0
                    and c["global_start"] + c["duration"] <= duration + .04 for c in cues),
                    {"cues": len(cues), "boundary": "Narration semantics and actual listening still require human review"})
        audit.command("full-av-decode", [args.ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-xerror",
                       "-i", video, "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"])
        audit.check("full_video_and_audio_decode", True, "Every video/audio packet decoded with -xerror; logs retained")
        audio_audit(audit, args, duration, timeline, narration, music, policy)
        samples = frame_samples(timeline, cues, duration, fps)
        frames = extract_final_frames(audit, args.ffmpeg, video, samples, fps,
                                      float(v.get("start_time", 0)))
        write(output / "final-frame-index.json", {"subject": subject, "frames": list(frames.values()),
              "human_full_1x_review": False, "boundary": "Actual decoded samples, including chapter ends and last frame; not continuous human viewing"})
        subtitle_audit(audit, args.ffmpeg, tracks, cues, frames, fps, v["width"], v["height"], args.safe_margin)
        audit.check("frozen_inputs_unchanged", all(pin_matches(ref(p["path"]), p) for p in input_pins),
                    "Final movie, ASS, font pins, timeline, dry voice and original music rehashed after evidence generation")
        bound_path = output / "final-bound-probe.json"
        probe_and_write_bound_media(args.ffprobe, Path(video), output_path=bound_path,
                                   audit_directory=output / "bound-probe-command")
        storyboard_path = output / "human-review-storyboard.json"
        write(storyboard_path, {"chapters": [{"id": c["id"], "title": c["title"],
              "start_seconds": c["global_start"], "end_seconds": c["global_start"] + c["duration"]} for c in wanted]})
        review_kwargs = dict(ffmpeg=args.ffmpeg, deliverable_path=Path(video),
              storyboard_path=storyboard_path, probe_path=bound_path,
              output_directory=output / "pending-human-review", audit_directory=output / "review-command")
        plan = run_review_command(**review_kwargs, plan_only=True)
        write(output / "review-plan.json", plan)
        if review_kwargs["output_directory"].exists() or review_kwargs["audit_directory"].exists():
            raise ValueError("Review plan unexpectedly created output directories")
        pending = run_review_command(**review_kwargs)
        write(output / "review-result.json", pending)
        audit.check("byte_bound_probe_and_pending_review", True, "Public 0.2.1 producer and review API; no signoff")
        manifest = args.native_manifest or base / "native-run/run-manifest.json"
        if manifest.is_file() and all(c["passed"] for c in audit.checks.values()):
            prefix = args.audit_artifact_prefix or re.sub(r"[^A-Za-z0-9_.-]", "-", output.name)
            native_frame_audit(audit, manifest, frames, args.subject_artifact_id, prefix)
            audit.check("native_real_frame_integrity_audit", True,
                        "Exact preserved deliverable and real frames audited; no human signoffs changed")
        passed = all(c["passed"] for c in audit.checks.values())
        write(output / "media-report.json", {"at_utc": stamp(), "kind": "ck3-episode03-media-audit",
              "subject": subject, "status": "PASS_PENDING_HUMAN_REVIEW" if passed else "RED",
              "machine_condition_status": "PASS" if passed else "RED", "checks": audit.checks,
              "commands": audit.commands, "human_signoff": "not-provided", "manual_approval_granted": False,
              "full_1x_human_review": False, "retention": "all inputs, outputs, logs and partials retained",
              "boundaries": ["Machine integrity and declared timing/mix/pixel samples only",
              "No human hearing, reading, continuous full-film viewing or semantic approval",
              "No new CK3 runtime acceptance or independent cloud upload verification"]})
        print(json.dumps({"status": "PASS_PENDING_HUMAN_REVIEW" if passed else "RED",
                          "report": str(output / "media-report.json"), "subject": subject,
                          "human_signoff": "not-provided"}, ensure_ascii=False), flush=True)
        return 0 if passed else 2
    except Exception as exc:
        write(output / "failure.json", {"at_utc": stamp(), "status": "RED", "error": str(exc),
              "traceback": traceback.format_exc(), "subject": audit.subject if audit else None,
              "checks": audit.checks if audit else {}, "human_signoff": "not-provided",
              "all_material_retained": True})
        print(f"RED: {exc}; retained {output}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
