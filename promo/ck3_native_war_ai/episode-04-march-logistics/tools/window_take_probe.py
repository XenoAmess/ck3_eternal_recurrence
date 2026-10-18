"""Offline technical probe of a completed owned CK3 client-window raw take."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageStat
import window_take as film


def probe(spec, output):
    output = Path(output).resolve()
    film.need(output.parent == spec.scene and not output.exists(), "fresh scene-local media probe directory required")
    terminal_path = spec.workdir / "result.json"
    film_path = spec.receipt("film-result")
    terminal, take = film.read(terminal_path), film.read(film_path)
    film.need(terminal.get("machine_id") == take.get("machine_id") == spec.machine_id and
              take.get("run_id") == spec.live.name and
              film.pinned(film.pin(terminal_path), take.get("recorder_result")),
              "same-machine exact recorder terminal binding differs")
    raw_path = spec.workdir / "raw.mkv"
    film.need(raw_path.is_file() and raw_path.stat().st_size <= spec.raw_budget_bytes,
              "actual raw missing or exceeds root-adopted raw ceiling")
    raw = film.pin(raw_path)
    film.need(film.pinned(raw, terminal.get("raw")), "raw bytes/hash differ from terminal")
    source = terminal.get("capture_source") or {}
    rect = source.get("client_screen_rect") or []
    film.need(source.get("kind") == "gdigrab-desktop-client-region" and
              source.get("output_size") == spec.expected_size and len(rect) == 4 and
              [rect[2] - rect[0], rect[3] - rect[1]] == spec.expected_size and
              source.get("direct_hwnd_capture") is False and
              source.get("window_border_included") is False,
              "raw capture is not the verified CK3 client-only region")
    ffmpeg = film.pin(spec.ffmpeg_ref["path"])
    film.need(film.pinned(ffmpeg, spec.ffmpeg_ref), "exact FFmpeg binary changed")
    ffprobe = Path(ffmpeg["path"]).with_name("ffprobe.exe")
    ffprobe_ref = film.pin(ffprobe)
    observed = subprocess.run([str(ffprobe), "-v", "error", "-show_streams", "-show_format",
                              "-of", "json", str(raw_path)],
                             capture_output=True, text=True, timeout=30, check=True)
    metadata = json.loads(observed.stdout)
    streams = [x for x in metadata.get("streams", []) if x.get("codec_type") == "video"]
    film.need(len(streams) == 1 and [streams[0]["width"], streams[0]["height"]] == spec.expected_size,
              "decoded raw stream is not the planned CK3 client geometry")
    duration = float(metadata["format"]["duration"])
    film.need(duration > 2, "raw too short for three original review frames")
    output.mkdir(exist_ok=False)
    frames, images = [], []
    for label, second in (("early", 1.0), ("middle", duration / 2), ("late", max(1.0, duration - 1.0))):
        destination = output / ("frame-" + label + ".png")
        subprocess.run([ffmpeg["path"], "-hide_banner", "-loglevel", "error", "-ss", str(second),
                        "-i", str(raw_path), "-frames:v", "1", "-y", str(destination)],
                       capture_output=True, timeout=30, check=True)
        with Image.open(destination) as picture:
            image = picture.convert("RGB")
            film.need(list(image.size) == spec.expected_size, "sampled image size differs")
            stat = ImageStat.Stat(image)
            images.append(image.copy())
        frames.append({"label": label, "second": second, "original": film.pin(destination),
                       "rgb_mean": stat.mean, "rgb_stddev": stat.stddev,
                       "near_black": max(stat.mean) < 8 or max(stat.stddev) < 3})
    changes = []
    for first, second in zip(images, images[1:]):
        delta = ImageChops.difference(first, second)
        changes.append({"pixels_changed": delta.getbbox() is not None,
                        "mean_absolute_channel_delta": ImageStat.Stat(delta).mean})
    technical = (terminal.get("state") == "NORMAL_TREE_EMPTY" and
                 terminal.get("capture_guard_error") is None and
                 spec.min_seconds - 2 <= duration <= spec.record_seconds + 0.1 and
                 take.get("elapsed_wall_seconds_at_terminal", 0) >= spec.min_seconds and
                 take.get("hard_terminal_wall_seconds_met") is True and
                 all(not x["near_black"] for x in frames) and
                 any(x["pixels_changed"] for x in changes))
    return film.write_once(output / "PROBE.actual.json", {
        "schema": "xar.e04.owned-client-window-media-probe.v1",
        "machine_id": spec.machine_id, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": spec.live.name, "raw": raw, "terminal": film.pin(terminal_path),
        "film_result": film.pin(film_path), "ffprobe": ffprobe_ref,
        "capture_source": source, "video_stream": streams[0],
        "duration_seconds": duration, "frames": frames, "changes": changes,
        "technical_media_pass": technical, "human_original_frame_review_pending": True,
        "business_or_video_signoff": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(film.TakeSpec(args.config), args.output), ensure_ascii=False))
