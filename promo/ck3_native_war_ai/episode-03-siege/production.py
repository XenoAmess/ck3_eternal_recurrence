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
            speech_duration = float(probe["format"]["duration"])
            require(math.isfinite(speech_duration) and speech_duration > 0,
                    "Prepared narration has no finite positive duration: " + key)
            # Match the a09 Edge branch's 0.18s exterior tail. render_chunk's
            # apad supplies it without touching the exact imported source WAV.
            # This keeps spoken endpoints clear of AAC concat/remux padding.
            duration = math.ceil((speech_duration + .18) * 30) / 30
            results.append({**cue, "chapter": chapter["id"], "key": key, "audio": row["audio"]["path"],
                             "tts_raw": row["audio"], "tts_trimmed": row["audio"], "duration": duration,
                            "prepared_source_duration_seconds": speech_duration,
                            "prepared_tail_seconds": duration - speech_duration,
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
        if shot.get("raw_recording") and shot.get("kind") == "raw_clip":
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
    write(run / "edit.json", {"kind": "episode03-brown-gold-existing-media", "utterances": result,
                               "human_signoff": "not-provided", "production_clean_admission": False})


def render(args):
    run = args.run.resolve()
    require_ready(run)
    producer, _ = _legacy(run)
    timeline, edit = read(run / "timeline.json"), read(run / "edit.json")
    require(timeline["total_duration"] <= read(run / "sources/project-config.json")["constraints"]["duration_limit_seconds"],
            "Measured narration exceeds the frozen duration limit; revise a new editorial attempt")
    tasks = [(chapter, index, chapter["utterances"][start:start + 8])
             for chapter in timeline["chapters"]
             for index, start in enumerate(range(0, len(chapter["utterances"]), 8), 1)]
    for chapter, index, items in tasks:
        for cue in items:
            exact(cue["tts_trimmed"])
            shot = edit["utterances"][cue["key"]]
            if shot.get("source_binding"):
                exact(shot["source_binding"])
            if shot.get("rendered_image"):
                exact(shot["rendered_image"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        receipts = list(pool.map(lambda row: producer.render_chunk(run, row[0], edit, row[2], row[1]), tasks))
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
    producer.text_once(run / "concat.txt", "".join("file '" + row["path"].replace(chr(92), "/") + "'\n" +
                                                  f"duration {row['duration_expected']:.9f}\n" for row in chapters))
    metadata = [";FFMETADATA1"]
    for chapter in timeline["chapters"]:
        title = chapter["title"].replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#").replace("\n", " ")
        metadata.extend(["[CHAPTER]", "TIMEBASE=1/1000", f"START={round(chapter['global_start'] * 1000)}",
                         f"END={round((chapter['global_start'] + chapter['duration']) * 1000)}", "title=" + title])
    producer.text_once(run / "chapters.ffmetadata", "\n".join(metadata) + "\n")
    output = run / "dry-master.mp4"
    command(run, "dry-final-join", [producer.FFMPEG, "-hide_banner", "-nostdin", "-n", "-f", "concat", "-safe", "0", "-i", run / "concat.txt",
                                     "-f", "ffmetadata", "-i", run / "chapters.ffmetadata", "-map", "0", "-map_metadata", "1", "-map_chapters", "1",
                                     "-c", "copy", "-movflags", "+faststart", output])
    probe = producer.probe(run, "dry-master-probe", output)
    write(run / "dry-master-probe.json", probe)
    video = next(row for row in probe["streams"] if row["codec_type"] == "video")
    require(int(video["nb_frames"]) == timeline["total_duration_frames"], "Dry picture frame count differs from cue grid")
    write(run / "dry-master.json", {**ref(output), "duration_expected": timeline["total_duration"], "music": False,
                                     "duration_frames_expected": timeline["total_duration_frames"],
                                     "actual_video_start_pts_seconds": float(video["start_time"]),
                                     "actual_video_time_base": video["time_base"],
                                     "cue_count": sum(len(chapter["utterances"]) for chapter in timeline["chapters"]),
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
    output = attempt / OUTPUT
    write(run / "final-artifact.json", {**ref(output), "duration_expected": read(run / "timeline.json")["total_duration"],
                                        "music": read(run / "music-policy.json"), "human_signoff": "not-provided",
                                        "production_clean_admission": False, "status": "pending-machine-and-human-review"})
    from xar_promo.operations import preserve_artifact
    for index, path in enumerate([run / "input-freeze.json", run / "timeline.json", run / "edit.json", run / "music-policy.json",
                                  run / "subtitle-tracks.json", run / "fonts.json", *[Path(row["path"]) for row in read(run / "subtitle-tracks.json")["tracks"]]]):
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
    for phase in ("narrate", "boards", "render", "build"):
        sub.add_parser(phase)
    for phase, child in sub.choices.items():
        if phase != "check-release":
            child.add_argument("--run", required=True, type=Path)
    sub.choices["narrate"].add_argument("--prepared-audio", type=Path,
                                       help="Existing exact audio receipts instead of calling the provider")
    for phase in ("narrate", "render"):
        sub.choices[phase].add_argument("--workers", type=int, default=3)
    sub.choices["build"].add_argument("--workdir", required=True, type=Path)
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
