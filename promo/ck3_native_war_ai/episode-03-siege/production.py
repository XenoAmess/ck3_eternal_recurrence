"""Episode03 preparation, a09 voice/picture reuse, and native build entry point.

Every attempt owns a new directory. Pending editorial inputs may be prepared,
but production consumes only the root's frozen, ready, exact input bytes. The
separate media_audit.py owns final media checks and pending-human review.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone
import urllib.request

P = Path(__file__).resolve().parent
E2 = P.parent / "episode-02-battle-second-half"
OUTPUT = "CK3-War-AI-Episode03-Siege-BrownGold.mp4"
MUSIC = Path("D:/workspace/ck3_native_war_ai_promo_work/v5-theme-film-attempt-001/run/artifacts/raw/sha256/FD/FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F.wav")
MUSIC_SHA = "FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F"
VOICE, RATE = "zh-CN-XiaoxiaoNeural", "-5%"
RELEASE_API = "https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest"
RELEASE_MAX_AGE_SECONDS = 900


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def ref(path):
    path = Path(path).resolve()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest().upper()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def exact(pin):
    actual = ref(pin["path"])
    require(actual["bytes"] == pin["bytes"] and actual["sha256"] == pin["sha256"].upper(),
            "Input bytes changed: " + str(pin["path"]))
    return actual


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def pins(value):
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"}.issubset(value):
            yield {key: value[key] for key in ("path", "bytes", "sha256")}
        for child in value.values():
            yield from pins(child)
    elif isinstance(value, list):
        for child in value:
            yield from pins(child)


def release_identity(release):
    release_data = release["latest_release"]
    require(release_data.get("draft") is False and release_data.get("prerelease") is False,
            "Use the latest official stable release")
    version = importlib.metadata.version("xar-promo-toolchain")
    require(release_data["tag_name"] == "v" + version,
            "Verified latest formal release differs from the selected interpreter")
    wheel = next(asset for asset in release_data["assets"] if asset["name"].endswith("-py3-none-any.whl"))
    provenance = json.loads(importlib.metadata.distribution("xar-promo-toolchain").read_text("direct_url.json"))
    digest = provenance["archive_info"]["hashes"]["sha256"]
    require(wheel["digest"].lower() == "sha256:" + digest.lower(),
            "Installed wheel SHA differs from the verified release")
    require(release["wheel_sha256"].upper() == digest.upper(), "Release receipt wheel SHA differs")
    return version, provenance


def checked_release(path, *, now=None):
    release = read(path)
    require(release.get("schema") == "ck3.episode03.release-query/v1" and release.get("official_api_url") == RELEASE_API,
            "New run requires a fresh official latest-release query receipt")
    exact(release["api_response"])
    require(read(release["api_response"]["path"]) == release["latest_release"],
            "Release API response differs from receipt metadata")
    queried = datetime.fromisoformat(release["queried_at_utc"])
    require(queried.tzinfo is not None, "Latest-release query timestamp needs a timezone")
    age = ((now or datetime.now(timezone.utc)) - queried).total_seconds()
    require(-60 <= age <= RELEASE_MAX_AGE_SECONDS,
            "Latest-release query is stale or in the future; query again for this new run")
    version, provenance = release_identity(release)
    return release, version, provenance, age


def check_release(args):
    output = args.output_dir.resolve()
    require(not output.exists(), "Use a new release-query directory; retain every earlier query")
    output.mkdir(parents=True)
    request = urllib.request.Request(RELEASE_API, headers={"Accept": "application/vnd.github+json",
                                                        "User-Agent": "CK3-Episode03-Production"})
    with urllib.request.urlopen(request, timeout=30) as response:
        require(response.geturl() == RELEASE_API, "Latest-release query was redirected from its official API")
        raw = response.read()
    response_path = output / "official-api-response.json"
    with response_path.open("xb") as stream:
        stream.write(raw)
    release_data = json.loads(raw)
    wheel = next(asset for asset in release_data["assets"] if asset["name"].endswith("-py3-none-any.whl"))
    receipt = {"schema": "ck3.episode03.release-query/v1", "queried_at_utc": stamp(),
               "official_api_url": RELEASE_API, "api_response": ref(response_path),
               "latest_release": release_data, "wheel_sha256": wheel["digest"].removeprefix("sha256:").upper()}
    receipt_path = output / "release-query.json"
    write(receipt_path, receipt)
    checked_release(receipt_path)
    print(json.dumps({"receipt": str(receipt_path), "tag": release_data["tag_name"],
                      "wheel_sha256": receipt["wheel_sha256"]}))


def _frame_ass_timestamp(seconds):
    # ASS stores centiseconds. Flooring a frame boundary places it after the
    # previous picture frame and at or before the intended first frame.
    frame = round(seconds * 30)
    require(frame >= 0 and abs(seconds - frame / 30) < 1e-8,
            "Subtitle time is not on the integer 30fps grid")
    centiseconds = frame * 100 // 30
    return f"{centiseconds // 360000}:{centiseconds // 6000 % 60:02d}:{centiseconds // 100 % 60:02d}.{centiseconds % 100:02d}"


def _native_ass_text(text, limit, original):
    """Keep revision Chinese punctuation and the word 控制 on their text line."""
    if limit != 40:
        return original(text, limit)
    # Preserve the legacy ASS control-character validation.
    original(text, limit)
    closing = "，。；、：！？）】》〉」』〕”’…,.!?;:%)]}"
    opening = "（【《〈「『〔“‘([{"
    lines = []
    for paragraph in text.splitlines():
        if len(paragraph) <= limit:
            lines.append(paragraph)
            continue
        protected = [match.span() for match in re.finditer("控制", paragraph)]
        cuts = [cut for cut in range(max(1, len(paragraph) - limit), min(limit, len(paragraph) - 1) + 1)
                if paragraph[cut] not in closing and paragraph[cut - 1] not in opening
                and not any(begin < cut < end for begin, end in protected)]
        require(cuts, "Revision Chinese subtitle has no safe two-line break")
        cut = min(cuts, key=lambda n: (paragraph[n - 1] not in "，。；、：！？", abs(n - len(paragraph) / 2)))
        lines.extend((paragraph[:cut], paragraph[cut:]))
    return r"\N".join(lines)


def _legacy(run=None):
    for path in (E2, P.parent / "integration/src"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    producer = importlib.import_module("review_story_a04")
    boards = importlib.import_module("compose_review_boards_a04")
    if run is not None:
        env = environment(run)
        producer.FFMPEG, producer.FFPROBE = Path(env["ffmpeg"]), Path(env["ffprobe"])
        original = producer.__dict__.setdefault("_episode03_ass_burn_original", producer.ass_burn_in_filter)
        # concat uses microsecond timestamps; fractional cue boundaries can be
        # one microsecond early for libass. Restore integer 30fps PTS before
        # burning the ASS. These callbacks change only this E3 process.
        producer.ass_burn_in_filter = lambda *args, **kwargs: "fps=30,settb=1/30,setpts=N," + original(*args, **kwargs)
        producer.at = _frame_ass_timestamp
        ass_original = producer.__dict__.setdefault("_episode03_ass_text_original", producer.ass_text)
        live_path = Path(run) / "sources/live-source.json"
        if live_path.is_file() and read(live_path).get("visual_policy", {}).get("require_native_presentation"):
            producer.ass_text = lambda text, limit: _native_ass_text(text, limit, ass_original)
        else:
            producer.ass_text = ass_original
    return producer, boards


def environment(run):
    return read(Path(run) / "sources/environment.json")


def command(run, label, argv):
    producer, _ = _legacy(run)
    return producer.command(Path(run), label, [str(item) for item in argv])


def cues(story):
    for chapter in story["chapters"]:
        for cue in chapter["utterances"]:
            yield chapter, cue, chapter["id"] + "-" + cue["id"]


def selected_shot(cue, lookup, key):
    selected = cue.get("primary_shot_id", cue["shot_ids"][0])
    require(selected in cue["shot_ids"] and selected in lookup,
            "Cue has no frozen primary picture: " + key)
    return lookup[selected]


def clip_selection(shot, cue, key):
    source_begin, source_end = float(shot["source_begin_seconds"]), float(shot["source_end_seconds"])
    span = cue.get("clip_span") or {}
    begin = float(span.get("source_begin_seconds", source_begin))
    end = float(span.get("source_end_seconds", source_end))
    require(all(math.isfinite(value) for value in (source_begin, source_end, begin, end))
            and 0 <= source_begin <= begin < end <= source_end,
            "Cue clip selection is outside the finite frozen shot range: " + key)
    return begin, end


def presentation(shot, cue, key):
    """Optional project-owned revision policy; legacy inputs keep their layout."""
    value = {**shot.get("presentation", {}), **cue.get("presentation", {})}
    if not value:
        return None
    require(value.get("layout") in ("native-panel", "full-native"), "Unknown native layout: " + key)
    rect = value.get("crop_xyxy")
    require(isinstance(rect, list) and len(rect) == 4 and
            all(isinstance(n, int) and not isinstance(n, bool) for n in rect) and
            0 <= rect[0] < rect[2] and 0 <= rect[1] < rect[3], "Invalid original-pixel crop: " + key)
    require(value.get("source_role") in ("observed-change", "paused-ui", "new-ui-demo", "still-source"),
            "Declare the actual visual source role: " + key)
    require(isinstance(value.get("title"), str) and value["title"].strip(), "Native title is missing: " + key)
    notes = value.get("notes", [])
    require(isinstance(notes, list) and len(notes) <= 3 and
            all(isinstance(note, str) and note.strip() for note in notes), "Select at most three brief notes: " + key)
    rate = float(value.get("playback_rate", 1))
    hold = float(value.get("max_end_hold_seconds", 0))
    require(math.isfinite(rate) and .5 <= rate <= 1 and math.isfinite(hold) and 0 <= hold <= 3,
            "Use declared 0.5–1x playback and at most three seconds of end hold: " + key)
    raw = shot.get("kind") == "raw_clip"
    require(raw or value["source_role"] == "still-source", "A still source cannot claim recorded change: " + key)
    require(not raw or value["source_role"] != "still-source", "Raw footage needs its actual recorded role: " + key)
    replay = value.get("replay_label")
    require(replay is None or isinstance(replay, str) and replay.strip(), "Replay needs a visible label: " + key)
    return {**value, "notes": notes, "playback_rate": rate, "max_end_hold_seconds": hold}


def output_name(run):
    policy = read(Path(run) / "sources/live-source.json").get("visual_policy", {})
    name = policy.get("output_filename", OUTPUT)
    require(isinstance(name, str) and Path(name).name == name and name.endswith(".mp4"),
            "Final output must be one explicit MP4 basename")
    return name


def native_plate(run, key, policy, *, source_path=None):
    """One original UI area and concise notes, with the a09 subtitle band."""
    from PIL import Image, ImageDraw
    _, painter = _legacy(run)
    image = Image.new("RGB", (1920, 1080), painter.BG)
    draw = ImageDraw.Draw(image)
    full_native = policy["layout"] == "full-native"
    box = (32, 100, 1232, 790) if not full_native else (160, 0, 1600, 900)
    title_lines = painter.wrap(draw, policy["title"], 1816, 44)
    require(len(title_lines) == 1, "Native title exceeds its fixed line: " + key)
    if not full_native:
        draw.text((40, 26), title_lines[0], font=painter.font(44), fill=painter.INK)
    if policy["layout"] == "native-panel":
        draw.rounded_rectangle((1296, 100, 1888, 790), radius=16, fill=painter.PANEL)
        y = 134
        for note in policy["notes"]:
            lines, line = [], ""
            for token in re.findall(r"\d+(?:\.\d+)*|.", note):
                if line and draw.textlength(line + token, font=painter.font(36)) > 520:
                    lines.append(line)
                    line = token
                else:
                    line += token
            if line:
                lines.append(line)
            require(len(lines) <= 2, "Native explanation exceeds two lines: " + key)
            for line in lines:
                draw.text((1324, y), line, font=painter.font(36), fill=painter.INK)
                y += 50
            y += 32
        require(y <= 670, "Native notes overlap their source label: " + key)
    else:
        require(not policy["notes"], "Full-native reserves its area for the original UI: " + key)
    labels = {"observed-change": "实机录像", "paused-ui": "界面展示（已暂停）",
              "new-ui-demo": "新录界面演示", "still-source": "原图说明"}
    badge = labels[policy["source_role"]]
    if policy["playback_rate"] != 1:
        badge += f" · {policy['playback_rate']:g}× 慢放"
    if policy.get("replay_label"):
        badge += " · " + policy["replay_label"]
    badge_font = 22 if full_native else 26
    if full_native and not policy.get("replay_label"):
        badge_lines = painter.wrap(draw, labels[policy["source_role"]], 128, badge_font)
        if policy["playback_rate"] != 1:
            badge_lines += [f"{policy['playback_rate']:g}×", "慢放"]
    else:
        badge_lines = painter.wrap(draw, badge, 128 if full_native else 520, badge_font)
    require(len(badge_lines) <= (4 if full_native else 2), "Native source label exceeds its area: " + key)
    for number, line in enumerate(badge_lines):
        draw.text((24, 776 + number * 28) if full_native else (1324, 708 + number * 34),
                  line, font=painter.font(badge_font), fill=painter.GOLD)
    draw.line((0, 900, 1920, 900), fill=painter.GOLD, width=2)
    crop = policy["crop_xyxy"]
    fitted = None
    if source_path is not None:
        with Image.open(source_path) as source:
            require(crop[2] <= source.width and crop[3] <= source.height, "Native crop exceeds the original image: " + key)
            cropped = source.crop(crop).convert("RGB")
            scale = min(box[2] / cropped.width, box[3] / cropped.height)
            size = (round(cropped.width * scale), round(cropped.height * scale))
            fitted = [box[0] + (box[2] - size[0]) // 2, box[1] + (box[3] - size[1]) // 2, *size]
            image.paste(cropped.resize(size, Image.Resampling.LANCZOS), fitted[:2])
    output = Path(run) / "visuals" / (key + ".png")
    with output.open("xb") as stream:
        image.save(stream, format="PNG")
    hold = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hold)
    hd.rounded_rectangle((1772, 836, 1904, 885) if full_native else (1660, 832, 1888, 885),
                         radius=10, fill=painter.PANEL)
    hd.text((1798, 842) if full_native else (1716, 840), "停格",
            font=painter.font(26 if full_native else 28), fill=painter.GOLD)
    hold_path = Path(run) / "visuals" / (key + "-hold.png")
    with hold_path.open("xb") as stream:
        hold.save(stream, format="PNG")
    return {"plate": ref(output), "hold_label": ref(hold_path), "viewport_xywh": list(box),
            "source_crop_xyxy": crop, "fitted_source_xywh": fitted, "presentation": policy}


def native_picture(run, key, shot, cue, producer):
    policy = presentation(shot, cue, key)
    require(policy is not None, "Native picture needs explicit presentation: " + key)
    if shot.get("kind") == "raw_clip":
        pin = exact(shot["raw_recording"])
        begin, end = clip_selection(shot, cue, key)
        probe = producer.probe(run, key + "-source-span-probe", pin["path"])
        video = next(item for item in probe["streams"] if item["codec_type"] == "video")
        rect = policy["crop_xyxy"]
        require(rect[2] <= video["width"] and rect[3] <= video["height"] and
                end <= float(probe["format"]["duration"]) + .001, "Native selection exceeds its exact source: " + key)
        plate = native_plate(run, key, policy)
        return {"kind": "native-excerpt", "image": pin["path"], "source_binding": pin,
                "start": begin, "source_duration": end - begin, "source_time_base": video["time_base"], **plate}
    spec = shot.get("board_spec") or (shot.get("board") if isinstance(shot.get("board"), dict) else {})
    frames = shot.get("frames", [])
    source = policy.get("source_image") or spec.get("source_image")
    if source:
        pin = next((item for item in pins(read(Path(run) / "sources/live-source.json"))
                    if Path(item["path"]).resolve() == Path(source).resolve()), None)
        require(pin is not None, "Native source image is absent from the frozen media pool: " + key)
    else:
        index = policy.get("source_frame_index", 0)
        require(isinstance(index, int) and 0 <= index < max(1, len(frames)), "Invalid selected original frame: " + key)
        pin = frames[index].get("image", frames[index]) if frames else shot.get("frame") or shot.get("board")
    exact(pin)
    plate = native_plate(run, key, policy, source_path=pin["path"])
    return {"kind": "native-still", "image": plate["plate"]["path"], "source_binding": pin,
            "rendered_image": plate["plate"], **plate}


def require_ready(run):
    run = Path(run)
    freeze = read(run / "input-freeze.json")
    for pin in freeze["inputs"] + freeze["scripts"] + freeze.get("snapshots", []) + freeze.get("release_inputs", []):
        exact(pin)
    story = read(run / "sources/story.json")
    require(story.get("editorial_ready") is True, "Episode03 editorial input is still pending")
    receipt_path = story.get("editorial_freeze_receipt")
    require(isinstance(receipt_path, str) and receipt_path, "Root's production-input freeze receipt is required")
    receipt = read(receipt_path)
    require(receipt.get("status") == "ready-for-production", "Production inputs have not been frozen ready")
    bound = {(str(Path(pin["path"]).resolve()), pin["sha256"].upper(), pin["bytes"])
             for pin in receipt["inputs"]}
    for pin in freeze["inputs"]:
        require((str(Path(pin["path"]).resolve()), pin["sha256"].upper(), pin["bytes"]) in bound,
                "Production freeze does not bind input: " + pin["path"])
    chapter_ids = [chapter["id"] for chapter in story["chapters"]]
    require(len(set(chapter_ids)) == len(chapter_ids), "Duplicate chapter id")
    require(all(isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9_-]+", identifier)
                for identifier in chapter_ids), "Chapter ids must be safe file identifiers")
    rows = list(cues(story))
    keys = [key for _, _, key in rows]
    require(keys and len(set(keys)) == len(keys), "Frozen story has no cues or duplicate cue keys")
    lookup = _shot_lookup(run)
    native_required = read(run / "sources/live-source.json").get("visual_policy", {}).get("require_native_presentation", False)
    bound_media = {str(Path(pin["path"]).resolve()): exact(pin)
                   for pin in pins(read(run / "sources/live-source.json"))}
    for chapter, cue, key in cues(story):
        require(isinstance(cue["id"], str) and re.fullmatch(r"[A-Za-z0-9_-]+", cue["id"]),
                "Cue id must be a safe file identifier: " + key)
        require(cue.get("status") == "ready" and all(isinstance(cue.get(lang), str) and cue[lang].strip()
                                                      for lang in ("zh", "en")),
                "Cue is pending or missing bilingual text: " + key)
        require(not cue.get("contains_pending_slot", False), "Cue still contains a pending live slot: " + key)
        require(cue.get("shot_ids"), "Cue lacks a frozen picture: " + key)
        require(cue.get("facts") or cue.get("evidence_level") == "editorial-transition",
                "Fact cue lacks frozen evidence: " + key)
        shot = selected_shot(cue, lookup, key)
        policy = presentation(shot, cue, key)
        require(not native_required or policy is not None, "Revision cue lacks its native presentation: " + key)
        require(not native_required or not cue.get("revision_visual_pending"),
                "Revision cue still awaits its declared media binding: " + key)
        if shot.get("kind") == "raw_clip":
            require(shot.get("raw_recording"), "Raw shot has no recording: " + key)
            exact(shot["raw_recording"])
            clip_selection(shot, cue, key)
        elif shot.get("board_spec") or (isinstance(shot.get("board"), dict) and "source_image" in shot["board"]):
            spec = shot.get("board_spec") or shot["board"]
            paths = [spec["source_image"], *[item["image"] for item in spec.get("extra_ui", [])]]
            require(all(str(Path(path).resolve()) in bound_media for path in paths),
                    "Board source is absent from frozen live-source media pins: " + key)
        else:
            frames = shot.get("frames", [])
            pin = shot.get("frame") or (shot.get("board") if shot.get("prepared_board") else None)
            media = ([pin] if shot.get("prepared_board") and pin else
                     [item.get("image", item) for item in frames] or ([pin] if pin else []))
            require(media and len(media) <= 2, "Shot needs one or two frozen pictures: " + key)
            for pin in media:
                exact(pin)
    return story


def prepare(args):
    run = args.run.resolve()
    require(not run.exists(), "Use a fresh run directory; keep every earlier attempt")
    originals = {"project-config.json": args.project, "story.json": args.script,
                  "live-source.json": args.live_source, "shot-list.json": args.shot_list}
    for path in getattr(args, "supporting_input", []):
        name = "supporting/" + path.name
        require(name not in originals, "Duplicate supporting input filename: " + path.name)
        originals[name] = path
    inputs = [ref(path) for path in originals.values()]
    producer, _ = _legacy()
    source_paths = [Path(__file__), P / "composer.py", E2 / "review_story_a04.py",
                    E2 / "compose_review_boards_a04.py", P.parent / "integration/src/war_ai_promo/series_palette.py"]
    scripts = [ref(path) for path in source_paths]
    release, version, provenance, release_age = checked_release(args.release_receipt)
    release_data = release["latest_release"]
    run.mkdir(parents=True)
    (run / "logs").mkdir()
    (run / "sources").mkdir()
    for name, path in originals.items():
        snapshot = run / "sources" / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, snapshot)
    snapshots = [ref(run / "sources" / name) for name in originals]
    require(all(snapshot["bytes"] == original["bytes"] and snapshot["sha256"] == original["sha256"]
                for snapshot, original in zip(snapshots, inputs)), "An input changed while being snapshotted")
    release_inputs = [ref(args.release_receipt), release["api_response"]]
    for name, pin in zip(("release-query.json", "release-api-response.json"), release_inputs):
        shutil.copyfile(pin["path"], run / "sources" / name)
        snapshots.append(ref(run / "sources" / name))
    for path in source_paths:
        shutil.copyfile(path, run / "sources" / (path.parent.name + "-" + path.name))
    write(run / "input-freeze.json", {"at_utc": stamp(), "inputs": inputs, "scripts": scripts,
                                     "snapshots": snapshots, "input_snapshot_names": list(originals),
                                     "release_inputs": release_inputs,
                                     "human_signoff": "not-provided"})
    write(run / "sources/environment.json", {
        "at_utc": stamp(), "python": sys.executable, "python_version": sys.version,
        "promo_version": version, "installed_wheel_provenance": provenance,
        "latest_release_receipt": ref(args.release_receipt), "latest_release": release_data,
        "latest_release_query_at_utc": release["queried_at_utc"], "latest_release_query_age_seconds_at_prepare": release_age,
        "latest_release_official_api": RELEASE_API, "latest_release_api_response": release["api_response"],
        "dependencies": {name: importlib.metadata.version(name) for name in ("Pillow", "edge-tts")},
        "ffmpeg": str(args.ffmpeg or producer.FFMPEG), "ffprobe": str(args.ffprobe or producer.FFPROBE),
        "voice": VOICE, "rate": RATE,
    })
    music_pin = ref(args.music or MUSIC)
    require(music_pin["sha256"] == MUSIC_SHA, "Use the exact established Quiet Courtly Tension source")
    write(run / "music-policy.json", {"title": "Quiet Courtly Tension", "source": music_pin,
                                       "narration_gain_db": 0, "music_gain_db": -17,
                                       "fade_in_seconds": 2, "fade_out_seconds": 8,
                                       "loop": True, "normalize": False,
                                       "policy": "same original theme loop; narration 0dB; music -17dB; 2s/8s exterior fades; no normalization",
                                       "human_listening_signoff": "not-provided"})
    write(run / "fonts.json", {"fonts": [ref("C:/Windows/Fonts/msyh.ttc"), ref("C:/Windows/Fonts/arial.ttf")],
                               "ass_font_names": ["Microsoft YaHei", "Arial"]})
    command(run, "native-start-run", [sys.executable, "-B", "-m", "xar_promo", "start-run",
                                     run / "sources/project-config.json", "--run-id", run.name,
                                     "--run-directory", run / "native-run"])
    print(json.dumps({"run": str(run), "editorial_ready": read(run / "sources/story.json").get("editorial_ready", False)}))


def _timeline(run, story, results):
    bykey = {row["key"]: row for row in results}
    chapters, start_frame = [], 0
    for chapter in story["chapters"]:
        if not chapter["utterances"]:
            continue  # An omitted conditional chapter has no picture or hold.
        local_frame, utterances = 0, []
        for cue in chapter["utterances"]:
            prepared = bykey[chapter["id"] + "-" + cue["id"]]
            duration_frames = round(prepared["duration"] * 30)
            require(duration_frames > 0 and abs(prepared["duration"] - duration_frames / 30) < 1e-8,
                    "Prepared cue is not on the integer 30fps grid: " + prepared["key"])
            row = {**prepared, "duration": duration_frames / 30, "duration_frames": duration_frames,
                   "local_start": local_frame / 30, "global_start": (start_frame + local_frame) / 30,
                   "local_start_frame": local_frame, "global_start_frame": start_frame + local_frame}
            utterances.append(row)
            local_frame += duration_frames
        chapters.append({"id": chapter["id"], "title": chapter["title"], "global_start": start_frame / 30,
                          "global_start_frame": start_frame, "duration": local_frame / 30,
                          "duration_frames": local_frame, "utterances": utterances})
        start_frame += local_frame
    start = start_frame / 30
    write(run / "timeline.json", {"kind": "pending-human-review", "human_signoff": "not-provided",
                                   "production_clean_admission": False, "total_duration": start,
                                   "chapters": chapters, "voice": VOICE, "rate": RATE,
                                   "narration_provider": "prepared-audio" if any("prepared_audio_provenance" in row for row in results) else "edge-tts",
                                    "fps": 30, "width": 1920, "height": 1080,
                                    "total_duration_frames": start_frame,
                                   "editorial_duration_target_seconds": [1200, 1500],
                                   "within_editorial_target": 1200 <= start <= 1500,
                                   "timing_basis": "measured prepared narration, rounded up to 30fps; no artificial duration padding"})


def prepared_narration_slot(row, probe, key):
    """Legacy arbitrary audio gets a tail; marked series WAVs already have it."""
    speech_duration = float(probe["format"]["duration"])
    require(math.isfinite(speech_duration) and speech_duration > 0,
            "Prepared narration has no finite positive duration: " + key)
    contract = row.get("audio_contract")
    require(contract in (None, "episode03-series-trimmed-wav-v1"), "Unknown prepared audio contract: " + key)
    if contract is None:
        return math.ceil((speech_duration + .18) * 30) / 30, speech_duration, {}
    require(row.get("voice") == VOICE and row.get("rate") == RATE,
            "Series prepared narration has a different voice or rate: " + key)
    import wave
    with wave.open(row["audio"]["path"], "rb") as stream:
        require((stream.getframerate(), stream.getnchannels(), stream.getsampwidth(), stream.getcomptype()) ==
                (48000, 2, 2, "NONE"), "Series narration must retain its original 48k stereo 16-bit PCM: " + key)
        samples = stream.getnframes()
        speech_duration = samples / 48000
        require(abs(float(probe["format"]["duration"]) - speech_duration) <= 1 / 48000,
                "Prepared series probe differs from actual PCM sample count: " + key)
        tail_samples = 8160  # The existing 0.18s trim tail remains at least 0.17s after resampling.
        require(samples >= tail_samples, "Prepared series WAV has no complete exterior tail: " + key)
        stream.setpos(samples - tail_samples)
        require(not any(stream.readframes(tail_samples)), "Prepared series WAV lacks the existing silent tail: " + key)
    duration_frames = (samples + 1599) // 1600
    return duration_frames / 30, speech_duration, {"audio_contract": contract, "voice": VOICE, "rate": RATE,
            "prepared_pcm_samples": samples, "existing_series_tail_verified_minimum_samples": tail_samples,
            "additional_series_tail_seconds": 0}


def narrate(args):
    run = args.run.resolve()
    story = require_ready(run)
    producer, _ = _legacy(run)
    rows = list(cues(story))
    for chapter, cue, key in rows:
        for language, limit in (("zh", 40), ("en", 100)):
            require(producer.ass_text(cue[language], limit).count(r"\N") <= 1,
                    "More than two subtitle lines: " + key + "/" + language)
    if args.prepared_audio:
        imported = {row["key"]: row for row in read(args.prepared_audio)["cues"]}
        require(set(imported) == {key for _, _, key in rows}, "Prepared audio does not cover the frozen script")
        results = []
        for chapter, cue, key in rows:
            row = imported[key]
            require(row["text_sha256"].upper() == hashlib.sha256(cue["zh"].encode("utf-8")).hexdigest().upper(),
                    "Prepared audio belongs to different narration: " + key)
            exact(row["audio"])
            probe = producer.probe(run, key + "-prepared-audio-probe", row["audio"]["path"])
            duration, speech_duration, audio_contract = prepared_narration_slot(row, probe, key)
            results.append({**cue, "chapter": chapter["id"], "key": key, "audio": row["audio"]["path"],
                             "tts_raw": row["audio"], "tts_trimmed": row["audio"], "duration": duration,
                            "prepared_source_duration_seconds": speech_duration,
                            "prepared_tail_seconds": duration - speech_duration,
                            **audio_contract,
                            "prepared_audio_provenance": row.get("provenance", "externally-prepared")})
        write(run / "prepared-audio-import.json", {"source": ref(args.prepared_audio), "cues": results})
    else:
        # Calls the existing a09 voice service only in this explicit production phase.
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda row: producer.narrate_one(run, row[0], row[1]), rows))
    _timeline(run, story, results)


def _shot_lookup(run):
    definitions = read(run / "sources/shot-list.json")["shots"]
    live = read(run / "sources/live-source.json")
    rows = live.get("shots", [])
    if isinstance(rows, dict):
        rows = [{"id": key, **value} for key, value in rows.items()]
    return {row["id"]: {**next((item for item in definitions if item["id"] == row["id"]), {}), **row}
            for row in rows}


def boards(args):
    run = args.run.resolve()
    story = require_ready(run)
    producer, painter = _legacy(run)
    lookup, result = _shot_lookup(run), {}
    (run / "visuals").mkdir(exist_ok=False)
    for chapter, cue, key in cues(story):
        shot = selected_shot(cue, lookup, key)
        if presentation(shot, cue, key) is not None:
            result[key] = native_picture(run, key, shot, cue, producer)
        elif shot.get("raw_recording") and shot.get("kind") == "raw_clip":
            pin = shot["raw_recording"]
            exact(pin)
            begin, end = clip_selection(shot, cue, key)
            probe = producer.probe(run, key + "-source-span-probe", pin["path"])
            require(end <= float(probe["format"]["duration"]) + .001,
                    "Source selection runs beyond the exact recording: " + shot["id"])
            result[key] = {"kind": "raw-excerpt", "image": pin["path"], "start": begin,
                           "source_duration": end - begin, "source_binding": pin,
                           "case": shot.get("case", shot.get("label", "")), "evidence": cue["facts"]}
        elif shot.get("board_spec") or (isinstance(shot.get("board"), dict) and "source_image" in shot["board"]):
            result[key] = painter.board(run, key, shot.get("board_spec") or shot["board"])
        else:
            from PIL import Image, ImageDraw
            frames = shot.get("frames", [])
            pin = shot.get("frame") or (shot.get("board") if shot.get("prepared_board") else None)
            if pin is None:
                require(frames, "Shot has no ready frame or board: " + shot["id"])
                pin = frames[0].get("image", frames[0])
            exact(pin)
            source = Image.open(pin["path"])
            if shot.get("prepared_board"):
                require(source.size == (1920, 1080), "Prepared board must reserve the a09 subtitle canvas")
                result[key] = {"kind": "still", "image": pin["path"], "source_binding": pin}
            else:
                image = Image.new("RGB", (1920, 1080), painter.BG)
                source_pins = [item.get("image", item) for item in frames] or [pin]
                require(len(source_pins) <= 2, "Select at most two original frames for this picture")
                for index, frame_pin in enumerate(source_pins):
                    exact(frame_pin)
                    painter.paste_fit(image, Image.open(frame_pin["path"]),
                                      (index * (1920 // len(source_pins)), 0, 1920 // len(source_pins), 900))
                ImageDraw.Draw(image).line((0, 900, 1920, 900), fill=painter.GOLD, width=2)
                output = run / "visuals" / (key + ".png")
                with output.open("xb") as stream:
                    image.save(stream, format="PNG")
                result[key] = {"kind": "still", "image": str(output), "source_binding": pin,
                               "source_bindings": source_pins, "rendered_image": ref(output)}
        result[key].update({"shot_id": shot["id"], "evidence": cue["facts"]})
    allocated = []
    for key, shot in result.items():
        if shot["kind"] != "native-excerpt":
            continue
        begin, end = shot["start"], shot["start"] + shot["source_duration"]
        for prior in allocated:
            overlaps = (prior["path"] == shot["image"] and max(begin, prior["begin"]) < min(end, prior["end"]) - .000001)
            require(not overlaps or shot["presentation"].get("replay_label") or prior["replay_label"],
                    "Repeated raw range needs an explicit visible replay label: " + prior["key"] + "/" + key)
        allocated.append({"key": key, "path": shot["image"], "begin": begin, "end": end,
                          "replay_label": shot["presentation"].get("replay_label")})
    write(run / "edit.json", {"kind": "episode03-brown-gold-existing-media", "utterances": result,
                               "human_signoff": "not-provided", "production_clean_admission": False})



def render_native_chunk(run, chapter, edit, items, index):
    """Render declared raw PTS once into one native viewport; never loop it."""
    producer, _ = _legacy(run)
    root = Path(run) / "chapters" / chapter["id"] / f"chunk-{index:02d}"
    root.mkdir(parents=True, exist_ok=False)
    start_frame = items[0]["local_start_frame"]
    local = [{**item, "local_start": (item["local_start_frame"] - start_frame) / 30,
              "duration": item["duration_frames"] / 30} for item in items]
    duration_frames = sum(item["duration_frames"] for item in local)
    ass = root / "subtitles.ass"
    producer.text_once(ass, producer.subtitles({**chapter, "utterances": local}, edit))
    argv = [str(producer.FFMPEG), "-hide_banner", "-nostdin", "-n", "-copyts"]
    filters, inputs, receipts = [], 0, []
    for i, cue in enumerate(local):
        shot = edit["utterances"][cue["key"]]
        require(shot["kind"] in ("native-excerpt", "native-still"), "A native chunk cannot mix legacy layouts")
        if shot["kind"] == "native-still":
            argv += ["-threads", "1", "-loop", "1", "-framerate", "30", "-t", str(cue["duration"]), "-i", shot["image"]]
            filters.append(f"[{inputs}:v]trim=end_frame={cue['duration_frames']},settb=1/30,setpts=N,setsar=1,format=yuv420p[v{i}]")
            inputs += 1
            receipts.append({"key": cue["key"], "kind": "still-source", "duration_frames": cue["duration_frames"],
                             "presentation": shot["presentation"]})
            continue
        policy = shot["presentation"]
        begin, end = shot["start"], shot["start"] + shot["source_duration"]
        playback_frames = math.ceil(shot["source_duration"] / policy["playback_rate"] * 30 - 1e-8)
        hold_frames = cue["duration_frames"] - playback_frames
        require(hold_frames >= 0, "Selected raw change exceeds its spoken cue; choose a shorter exact range or a new edit: " + cue["key"])
        require(hold_frames / 30 <= policy["max_end_hold_seconds"] + 1e-8,
                "Raw tail would become an undeclared long still: " + cue["key"])
        argv += ["-threads", "1", "-ss", f"{begin:.6f}", "-to", f"{end:.6f}", "-i", shot["image"],
                 "-threads", "1", "-loop", "1", "-framerate", "30", "-t", str(cue["duration"]), "-i", shot["plate"]["path"],
                 "-threads", "1", "-loop", "1", "-framerate", "30", "-t", str(cue["duration"]), "-i", shot["hold_label"]["path"]]
        x0, y0, x1, y1 = shot["source_crop_xyxy"]
        x, y, w, h = shot["viewport_xywh"]
        # showinfo precedes PTS reset: its log is the actual decoded source clock.
        filters.append(f"[{inputs}:v]trim=start={begin:.6f}:end={end:.6f},showinfo@source_{i},"
                       f"setpts=(PTS-STARTPTS)/{policy['playback_rate']:.9f},crop={x1-x0}:{y1-y0}:{x0}:{y0},"
                       f"scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                       f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x{producer.BG[1:]},setsar=1,fps=30,"
                       f"tpad=stop_mode=clone:stop_duration={cue['duration']:.9f},trim=end_frame={cue['duration_frames']},"
                       f"settb=1/30,setpts=N[ui{i}]")
        filters.append(f"[{inputs+1}:v]settb=1/30,setpts=N[plate{i}]")
        filters.append(f"[plate{i}][ui{i}]overlay=x={x}:y={y}:shortest=1[scene{i}]")
        filters.append(f"[{inputs+2}:v]settb=1/30,setpts=N[hold{i}]")
        filters.append(f"[scene{i}][hold{i}]overlay=enable='gte(n,{playback_frames})':shortest=1,"
                       f"trim=end_frame={cue['duration_frames']},settb=1/30,setpts=N,format=yuv420p[v{i}]")
        inputs += 3
        receipts.append({"key": cue["key"], "kind": shot["kind"], "source": shot["source_binding"],
                         "source_begin_pts_seconds": begin, "source_end_pts_seconds_exclusive": end,
                         "source_time_base": shot["source_time_base"], "presentation": policy,
                         "playback_frames": playback_frames, "end_hold_frames": hold_frames,
                         "duration_frames": cue["duration_frames"], "showinfo_filter": f"source_{i}"})
    audio_index = inputs
    for cue in local:
        argv += ["-i", cue["audio"]]
    filters.append("".join(f"[v{i}]" for i in range(len(local))) +
                   f"concat=n={len(local)}:v=1:a=0," + producer.ass_burn_in_filter(ass) + "[video]")
    for i, cue in enumerate(local):
        filters.append(f"[{audio_index+i}:a]apad,atrim=end_sample={cue['duration_frames']*1600},asetpts=PTS-STARTPTS[a{i}]")
    filters.append("".join(f"[a{i}]" for i in range(len(local))) + f"concat=n={len(local)}:v=0:a=1[audio]")
    graph = root / "filter.txt"
    producer.text_once(graph, ";\n".join(filters))
    output = root / "chunk.mp4"
    label = chapter["id"] + f"-chunk-{index:02d}-render"
    argv += ["-filter_complex_threads", "2", "-/filter_complex", str(graph), "-map", "[video]", "-map", "[audio]",
             "-frames:v", str(duration_frames), "-t", str(duration_frames / 30), "-c:v", "libx264", "-preset", "ultrafast",
             "-crf", "22", "-threads", "3", "-r", "30", "-fps_mode", "cfr", "-c:a", "aac", "-b:a", "160k",
             "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(output)]
    command(run, label, argv)
    log = Path(run) / "logs" / (label + ".stderr.txt")
    actual = {}
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        name = re.search(r"showinfo@(source_\d+)", line)
        pts = re.search(r"\bpts_time:\s*([-+\d.eE]+)", line)
        if name and pts:
            actual.setdefault(name[1], []).append(float(pts[1]))
    for receipt in receipts:
        if receipt["kind"] == "native-excerpt":
            decoded = actual.get(receipt["showinfo_filter"], [])
            require(decoded and all(receipt["source_begin_pts_seconds"] - .000001 <= n <
                                    receipt["source_end_pts_seconds_exclusive"] for n in decoded),
                    "Actual decoded source PTS is absent or outside the chosen range: " + receipt["key"])
            receipt["actual_decoded_source_pts_seconds"] = decoded
            receipt["actual_decoded_source_frame_count"] = len(decoded)
    path = root / "visual-render-receipt.json"
    write(path, {"output": ref(output), "filter": ref(graph), "source_pts_log": ref(log), "cues": receipts,
                 "duration_frames": duration_frames, "human_signoff": "not-provided"})
    return {**ref(output), "duration_expected": duration_frames / 30, "visual_render_receipt": ref(path)}


def frame_aligned_narration(run, timeline):
    """Keep original PCM samples, adding only each cue's allocated silent tail."""
    import wave
    output = run / "narration-frame-grid.wav"
    rows, expected_start = [], 0
    with output.open("xb") as stream, wave.open(stream, "wb") as target:
        target.setparams((2, 2, 48000, 0, "NONE", "not compressed"))
        for chapter in timeline["chapters"]:
            for cue in chapter["utterances"]:
                require(cue["global_start_frame"] == expected_start, "Cue PCM grid is discontinuous")
                pin = exact(cue["tts_trimmed"])
                allocated = cue["duration_frames"] * 1600
                with wave.open(pin["path"], "rb") as source:
                    require((source.getnchannels(), source.getsampwidth(), source.getframerate(), source.getcomptype()) ==
                            (2, 2, 48000, "NONE"), "Narration must be exact 48kHz stereo PCM16")
                    samples = source.getnframes()
                    require(0 < samples <= allocated, "Cue audio exceeds its picture grid; never cut speech")
                    while data := source.readframes(65536):
                        target.writeframesraw(data)
                target.writeframesraw(bytes((allocated - samples) * 4))
                rows.append({"id": cue["id"], "source": pin, "global_start_frame": expected_start,
                             "source_samples": samples, "allocated_samples": allocated,
                             "added_silent_samples": allocated - samples})
                expected_start += cue["duration_frames"]
    require(expected_start == timeline["total_duration_frames"], "Narration frame-grid total differs")
    with wave.open(str(output), "rb") as result:
        require(result.getnframes() == expected_start * 1600, "PCM master sample count differs")
    write(run / "narration-frame-grid.json", {**ref(output), "sample_rate": 48000, "channels": 2,
          "sample_width_bytes": 2, "total_samples": expected_start * 1600, "cues": rows,
          "policy": "Original PCM samples copied unchanged; only allocated silence added; no speed change or trimming",
          "human_signoff": "not-provided"})
    return output


def reuse_render(args):
    """New run recovery: exact previous picture/ASS, original WAV cues, new PCM mux."""
    run, previous = args.run.resolve(), args.previous_run.resolve()
    require_ready(run)
    prior_freeze = read(previous / "input-freeze.json")
    # Historical producer hashes remain historical. Only immutable data is imported.
    for pin in prior_freeze["snapshots"]:
        exact(pin)
    historical_scripts = []
    for pin in prior_freeze["scripts"]:
        path = Path(pin["path"])
        preserved = ref(previous / "sources" / (path.parent.name + "-" + path.name))
        require(preserved["bytes"] == pin["bytes"] and preserved["sha256"] == pin["sha256"],
                "Previous producer snapshot differs from its historical freeze")
        historical_scripts.append(preserved)
    current_names = read(run / "input-freeze.json")["input_snapshot_names"]
    require(current_names == prior_freeze["input_snapshot_names"], "Recovery editorial input roles differ")
    for name in current_names:
        require(ref(run / "sources" / name)["sha256"] == ref(previous / "sources" / name)["sha256"],
                "Recovery inputs differ from the previous exact editorial/media snapshots: " + name)
    require(ref(previous / "timeline.json")["sha256"] == args.previous_timeline_sha256.upper(),
            "Previous timeline differs from the explicitly selected recovery subject")
    timeline, edit = read(previous / "timeline.json"), read(previous / "edit.json")
    picture = read(previous / "dry-master.json")
    exact(picture)
    for pin in pins(edit):
        exact(pin)
    tracks = read(previous / "subtitle-tracks.json")
    imported = [ref(previous / name) for name in ("input-freeze.json", "timeline.json", "edit.json", "subtitle-tracks.json", "fonts.json", "chapters.ffmetadata")]
    imported.extend(ref(track["path"]) for track in tracks["tracks"])
    imported.extend(exact(track["chunk_probe"]) for track in tracks["tracks"])
    write(run / "timeline.json", timeline)
    write(run / "edit.json", edit)
    write(run / "subtitle-tracks.json", tracks)
    # prepare already writes fonts.json; compare the exact font policy.
    require(read(run / "fonts.json") == read(previous / "fonts.json"), "Recovery font policy differs")
    write(run / "reuse-render-inputs.json", {"previous_run": str(previous), "picture": picture,
          "inputs": imported, "historical_scripts": historical_scripts,
          "new_input_freeze": ref(run / "input-freeze.json"),
          "scope": "Reuse exact encoded picture and ASS; discard previous concatenated AAC from recovery output",
          "human_signoff": "not-provided"})
    audio = frame_aligned_narration(run, timeline)
    output = run / "dry-master.mov"
    env = environment(run)
    command(run, "recovered-PCM-picture-mux", [env["ffmpeg"], "-hide_banner", "-nostdin", "-n",
            "-i", picture["path"], "-i", audio, "-f", "ffmetadata", "-i", previous / "chapters.ffmetadata",
            "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2", "-map_chapters", "2",
            "-c:v", "copy", "-c:a", "pcm_s16le", "-movflags", "+faststart", output])
    producer, _ = _legacy(run)
    probe = producer.probe(run, "dry-master-probe", output)
    write(run / "dry-master-probe.json", probe)
    video = next(row for row in probe["streams"] if row["codec_type"] == "video")
    audio_probe = next(row for row in probe["streams"] if row["codec_type"] == "audio")
    require(int(video["nb_frames"]) == timeline["total_duration_frames"], "Recovered picture frame count differs")
    require(audio_probe["codec_name"] == "pcm_s16le" and int(audio_probe["duration_ts"]) == timeline["total_duration_frames"] * 1600,
            "Recovered PCM sample count differs")
    write(run / "dry-master.json", {**ref(output), "duration_expected": timeline["total_duration"], "music": False,
          "duration_frames_expected": timeline["total_duration_frames"],
          "actual_video_start_pts_seconds": float(video["start_time"]), "actual_video_time_base": video["time_base"],
          "cue_count": sum(len(chapter["utterances"]) for chapter in timeline["chapters"]),
          "narration": ref(audio), "human_signoff": "not-provided"})


def render(args):
    run = args.run.resolve()
    require_ready(run)
    producer, _ = _legacy(run)
    timeline, edit = read(run / "timeline.json"), read(run / "edit.json")
    require(timeline["total_duration"] <= read(run / "sources/project-config.json")["constraints"]["duration_limit_seconds"],
            "Measured narration exceeds the frozen duration limit; revise a new editorial attempt")
    tasks = []
    for chapter in timeline["chapters"]:
        group, index = [], 1
        for cue in chapter["utterances"]:
            native = edit["utterances"][cue["key"]]["kind"].startswith("native-")
            if group and (len(group) == 8 or native != edit["utterances"][group[0]["key"]]["kind"].startswith("native-")):
                tasks.append((chapter, index, group))
                group, index = [], index + 1
            group.append(cue)
        if group:
            tasks.append((chapter, index, group))
    for chapter, index, items in tasks:
        for cue in items:
            exact(cue["tts_trimmed"])
            shot = edit["utterances"][cue["key"]]
            if shot.get("source_binding"):
                exact(shot["source_binding"])
            if shot.get("rendered_image"):
                exact(shot["rendered_image"])
            for name in ("plate", "hold_label"):
                if shot.get(name):
                    exact(shot[name])
    def render_task(row):
        renderer = render_native_chunk if edit["utterances"][row[2][0]["key"]]["kind"].startswith("native-") else producer.render_chunk
        return renderer(run, row[0], edit, row[2], row[1])
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        receipts = list(pool.map(render_task, tasks))
    tracks = []
    for (chapter, index, items), receipt in zip(tasks, receipts):
        expected_frames = sum(item["duration_frames"] for item in items)
        probe = producer.probe(run, chapter["id"] + f"-chunk-{index:02d}-picture-probe", receipt["path"])
        observation = next(row for row in probe["streams"] if row["codec_type"] == "video")
        require(int(observation["nb_frames"]) == expected_frames and observation["r_frame_rate"] == "30/1",
                "Chunk picture frame count differs from the frozen cue grid")
        probe_path = run / "chapters" / chapter["id"] / f"chunk-{index:02d}" / "picture-probe.json"
        write(probe_path, probe)
        tracks.append({"path": str(probe_path.parent / "subtitles.ass"),
                       "global_start": items[0]["global_start_frame"] / 30, "duration": expected_frames / 30,
                       "global_start_frame": items[0]["global_start_frame"], "duration_frames": expected_frames,
                       "chapter_id": chapter["id"], "fonts_dir": None, "chunk_probe": ref(probe_path),
                       "actual_chunk_video_start_pts_seconds": float(observation["start_time"]),
                       "actual_chunk_video_time_base": observation["time_base"],
                       "timing_basis": "logical integer 30fps sequence; actual chunk start PTS recorded separately"})
    write(run / "subtitle-tracks.json", {"tracks": tracks, "fonts": read(run / "fonts.json"),
                                        "layout": "a09 1920x1080; content y0..900; Chinese y910/935; English y1008/1030"})
    chapters = []
    for chapter in timeline["chapters"]:
        chunk_receipts = [receipt for task, receipt in zip(tasks, receipts) if task[0]["id"] == chapter["id"]]
        root = run / "chapters" / chapter["id"]
        producer.text_once(root / "concat.txt", "".join("file '" + receipt["path"].replace(chr(92), "/") + "'\n" +
                                                       f"duration {receipt['duration_expected']:.9f}\n" for receipt in chunk_receipts))
        output = root / "chapter.mp4"
        command(run, chapter["id"] + "-join", [producer.FFMPEG, "-hide_banner", "-nostdin", "-n", "-f", "concat", "-safe", "0",
                                              "-i", root / "concat.txt", "-c", "copy", "-movflags", "+faststart", output])
        chapters.append({**ref(output), "duration_expected": chapter["duration"]})
    write(run / "chapter-render-receipts.json", chapters)
    visual_receipts = [row["visual_render_receipt"] for row in receipts if row.get("visual_render_receipt")]
    if visual_receipts:
        write(run / "visual-render-receipts.json", {"chunks": visual_receipts, "timeline": ref(run / "timeline.json"),
              "edit": ref(run / "edit.json"), "total_duration_frames": timeline["total_duration_frames"],
              "human_signoff": "not-provided"})
    producer.text_once(run / "concat.txt", "".join("file '" + row["path"].replace(chr(92), "/") + "'\n" +
                                                  f"duration {row['duration_expected']:.9f}\n" for row in chapters))
    metadata = [";FFMETADATA1"]
    for chapter in timeline["chapters"]:
        title = chapter["title"].replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#").replace("\n", " ")
        metadata.extend(["[CHAPTER]", "TIMEBASE=1/1000", f"START={round(chapter['global_start'] * 1000)}",
                         f"END={round((chapter['global_start'] + chapter['duration']) * 1000)}", "title=" + title])
    producer.text_once(run / "chapters.ffmetadata", "\n".join(metadata) + "\n")
    audio = frame_aligned_narration(run, timeline)
    output = run / "dry-master.mov"
    command(run, "dry-final-join", [producer.FFMPEG, "-hide_banner", "-nostdin", "-n", "-f", "concat", "-safe", "0", "-i", run / "concat.txt",
                                     "-i", audio, "-f", "ffmetadata", "-i", run / "chapters.ffmetadata",
                                     "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2", "-map_chapters", "2",
                                     "-c:v", "copy", "-c:a", "pcm_s16le", "-movflags", "+faststart", output])
    probe = producer.probe(run, "dry-master-probe", output)
    write(run / "dry-master-probe.json", probe)
    video = next(row for row in probe["streams"] if row["codec_type"] == "video")
    require(int(video["nb_frames"]) == timeline["total_duration_frames"], "Dry picture frame count differs from cue grid")
    write(run / "dry-master.json", {**ref(output), "duration_expected": timeline["total_duration"], "music": False,
                                     "duration_frames_expected": timeline["total_duration_frames"],
                                     "actual_video_start_pts_seconds": float(video["start_time"]),
                                     "actual_video_time_base": video["time_base"],
                                     "cue_count": sum(len(chapter["utterances"]) for chapter in timeline["chapters"]),
                                     **({"visual_render_receipts": ref(run / "visual-render-receipts.json")} if visual_receipts else {}),
                                     "human_signoff": "not-provided"})


def build(args):
    run = args.run.resolve()
    require_ready(run)
    env = {**os.environ, "PYTHONPATH": str(P) + os.pathsep + str(P.parent / "integration/src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    # The child uses the explicitly selected interpreter and the current worktree modules.
    os.environ.update({"PYTHONPATH": env["PYTHONPATH"]})
    manifest = run / "native-run/run-manifest.json"
    attempt = args.workdir.resolve()
    common = [manifest, "--workdir", attempt, "--composer", "composer:compose"]
    command(run, "native-read-only-plan", [sys.executable, "-B", "-m", "xar_promo", "plan", *common])
    require(not attempt.exists(), "Native plan wrote its proposed workdir")
    command(run, "native-episode03-build", [sys.executable, "-B", "-m", "xar_promo", "build", *common, "--offline-tts"])
    output = attempt / output_name(run)
    write(run / "final-artifact.json", {**ref(output), "duration_expected": read(run / "timeline.json")["total_duration"],
                                        "music": read(run / "music-policy.json"), "human_signoff": "not-provided",
                                        "production_clean_admission": False, "status": "pending-machine-and-human-review"})
    from xar_promo.operations import preserve_artifact
    visual_records = [run / "visual-render-receipts.json"] if (run / "visual-render-receipts.json").exists() else []
    if visual_records:
        visual_records.extend(Path(pin["path"]) for pin in read(visual_records[0])["chunks"])
    for index, path in enumerate([run / "input-freeze.json", run / "timeline.json", run / "edit.json", run / "music-policy.json",
                                  run / "subtitle-tracks.json", run / "fonts.json", *visual_records,
                                  *[Path(row["path"]) for row in read(run / "subtitle-tracks.json")["tracks"]]]):
        preserve_artifact(manifest, path, artifact_id=f"e3-input-{index:03d}", collection="derived", role="process-evidence",
                          label=path.name, media_type="text/x-ssa" if path.suffix == ".ass" else "application/json")
    print(json.dumps({"final": str(output), "human_signoff": "not-provided"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="phase", required=True)
    release_parser = sub.add_parser("check-release", help="Query official latest release into a fresh receipt and verify this interpreter")
    release_parser.add_argument("--output-dir", required=True, type=Path)
    prepare_parser = sub.add_parser("prepare", help="Freeze current intent into a fresh attempt; pending cues are allowed")
    for flag in ("project", "script", "live-source", "shot-list", "release-receipt"):
        prepare_parser.add_argument("--" + flag, required=True, type=Path)
    for flag in ("music", "ffmpeg", "ffprobe"):
        prepare_parser.add_argument("--" + flag, type=Path)
    prepare_parser.add_argument("--supporting-input", action="append", type=Path, default=[],
                                help="Additional exact editorial source; may be repeated; included in the root input freeze")
    for phase in ("narrate", "boards", "render", "reuse-render", "build"):
        sub.add_parser(phase)
    for phase, child in sub.choices.items():
        if phase != "check-release":
            child.add_argument("--run", required=True, type=Path)
    sub.choices["narrate"].add_argument("--prepared-audio", type=Path,
                                       help="Existing exact audio receipts instead of calling the provider")
    for phase in ("narrate", "render"):
        sub.choices[phase].add_argument("--workers", type=int, default=3)
    sub.choices["build"].add_argument("--workdir", required=True, type=Path)
    sub.choices["reuse-render"].add_argument("--previous-run", required=True, type=Path)
    sub.choices["reuse-render"].add_argument("--previous-timeline-sha256", required=True)
    args = parser.parse_args()
    require(getattr(args, "workers", 1) > 0, "Worker count must be positive")
    failed_root = getattr(args, "run", getattr(args, "output_dir", None))
    target_existed = failed_root is not None and failed_root.exists()
    try:
        globals()[args.phase.replace("-", "_")](args)
    except Exception as error:
        # Keep a failed phase's process inputs and partials; reruns use new attempts.
        if (failed_root is not None and failed_root.exists()
                and not (target_existed and args.phase in ("prepare", "check-release"))):
            failure = failed_root / ("failure-" + args.phase + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
            write(failure, {"at_utc": stamp(), "phase": args.phase,
                            "error": type(error).__name__ + ": " + str(error),
                            "human_signoff": "not-provided", "partial_assets_retained": True})
        raise


if __name__ == "__main__":
    main()
