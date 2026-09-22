"""Project producer for completed, paused CK3 map recordings.

The CK3 adapter remains read-only.  This producer makes a new bundle from real
recorder receipts and an explicitly supplied agent image review.  It does not
infer visual observations, native-AI causality, or human approval.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
from typing import Any

from PIL import Image
from xar_promo.adapters.ck3 import load_capture_bundle
from xar_promo.process import CommandSpec, run_command

from .common import binding, load, write_new
from .capture_timing import FRAME_PROBE_SCHEMA, TIMING_POLICY, analyze_timestamps


EXTRACTION_SCHEMA = "ck3-war-ai.gameplay-frame-extraction.v1"
REVIEW_SCHEMA = "ck3-war-ai.gameplay-frame-review.v1"
PRODUCER = "war-ai-promo.paused-map-gameplay-bundle.v1"
FPS = 30
SCOPE = "paused-map endpoints, sampled foreground, and associated native readback"
BOUNDARIES = {
    "native_ai_causality_verified": False,
    "human_1x_review_performed": False,
    "signoff_granted": False,
    "frame_synchronous_query_proven": False,
    "continuous_visual_review_performed": False,
}


class GameplayBundleError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GameplayBundleError(message)


def _utc(value: Any, label: str) -> datetime:
    require(isinstance(value, str), f"{label}: explicit timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, f"{label}: timezone required")
    return parsed


def _number(value: Any, label: str) -> float:
    require(not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value), f"{label}: finite number required")
    return float(value)


def _bound(row: dict, label: str) -> dict:
    require(isinstance(row, dict) and {"path", "bytes", "sha256"} <= row.keys(),
            f"{label}: path/bytes/sha256 required")
    require(Path(row["path"]).is_absolute(), f"{label}: absolute path required")
    actual = binding(row["path"])
    require(actual["bytes"] == row["bytes"] and
            actual["sha256"].lower() == str(row["sha256"]).lower(),
            f"{label}: bytes/SHA mismatch: {row['path']}")
    return actual


def _body(path: Path) -> dict:
    payload = load(path)
    require(isinstance(payload, dict), f"{path}: object required")
    if "body" in payload:
        require(payload.get("result") == "CALL_COMPLETED", f"{path}: native call incomplete")
        payload = payload["body"]
    require(isinstance(payload, dict), f"{path}: native body must be an object")
    return payload


def _snapshot(path: Path, actor: int, date: int) -> dict:
    state = _body(path)
    require(state.get("paused") is True and state.get("map_ready") is True,
            f"{path}: paused map readback required")
    require(state.get("played_character", {}).get("character_id") == actor and
            state.get("date_raw") == date, f"{path}: actor/date differs")
    require(state.get("source") == "injected-dll-named-pipe" and
            state.get("diagnostics", {}).get("hello", {}).get("ck3_build_match") is True,
            f"{path}: matched native bridge readback required")
    return state


def _recording_input_matches(argv, desktop):
    if not isinstance(argv, list):
        return False
    if "gdigrab" in argv and "desktop" in argv:
        return True
    inputs = [arg for arg in argv if isinstance(arg, str) and arg.startswith("gfxcapture=")]
    if len(inputs) != 1:
        return False
    match = re.search(r"(?:gfxcapture=|:)hwnd=(0x[0-9a-fA-F]+|[0-9]+)(?=:|$)", inputs[0])
    if match is None:
        return False
    value = match.group(1)
    hwnd = int(value, 16 if value.lower().startswith("0x") else 10)
    return hwnd > 0 and hwnd == desktop.get("hwnd")


def completed_recording(recording_dir: str | Path) -> dict:
    """Validate existing recorder output; no desktop or media process is used."""
    root = Path(recording_dir).resolve()
    required = ("recording-result.json", "recording-precondition.json", "recording-command.json",
                "foreground-monitor.json", "ffprobe.json", "start-readback.json",
                "snapshot-before.json", "desktop-before.png", "desktop-after.png",
                "ffmpeg.stderr.txt", "gameplay.mkv")
    require(all((root / name).is_file() for name in required),
            "Recording is incomplete: completion, probe, monitor, endpoint screenshots and raw are required")
    result, pre, command = (load(root / name) for name in required[:3])
    require(result.get("recorder_exit") == 0 and result.get("probe_exit") == 0,
            "Recorder/probe did not finish successfully")
    raw = _bound(result.get("raw"), "recording-result.raw")
    require(Path(raw["path"]) == root / "gameplay.mkv", "Recorder raw path differs")
    require(result.get("foreground_always_ck3") is True, "Recorder reports foreground failure")
    require(pre.get("gameplay_hud_visually_observed") is True and
            bool(pre.get("observation")), "No actual pre-recording HUD observation")
    for field in ("hud_image_source", "native_start_source", "snapshot_source", "checkpoint"):
        _bound(pre.get(field), f"precondition.{field}")
    require(load(root / "start-readback.json").get("postcondition_verified") is True,
            "StartGame postcondition was not verified")
    state = _snapshot(root / "snapshot-before.json", pre["actor"], pre["date_raw"])
    before, after = _utc(command.get("at"), "recording start"), _utc(result.get("at"), "recording end")
    require(after > before, "Completion timestamp does not follow recorder start")
    require(_utc(pre.get("at"), "recording precondition") <= before,
            "HUD precondition occurred after recording start")
    argv = command.get("argv", [])
    require(_recording_input_matches(argv, pre["desktop"])
            and Path(argv[-1]).resolve() == Path(raw["path"]), "Not the declared desktop recorder output")
    probe_wrapper = load(root / "ffprobe.json")
    require(probe_wrapper.get("returncode") == 0, "Recorded ffprobe failed")
    probe = json.loads(probe_wrapper["stdout"])
    videos = [row for row in probe.get("streams", []) if row.get("codec_type") == "video"]
    require(len(videos) == 1, "Exactly one recorded video stream required")
    stream = videos[0]
    duration = _number(float(probe["format"]["duration"]), "recorded duration")
    require(duration > 0, "Positive recorded duration required")
    require(abs(float(stream.get("start_time", probe["format"].get("start_time", 0)))) < 0.0001,
            "Recording must have zero-based media time; do not silently shift raw evidence")
    monitor = load(root / "foreground-monitor.json")
    require(isinstance(monitor, list) and len(monitor) >= 2, "Foreground samples missing")
    pid = pre["desktop"]["pid"]
    times = [_number(row.get("seconds"), "foreground sample seconds") for row in monitor]
    require(all(row.get("pid") == pid and row.get("alive") is True and
                row.get("title") == "Crusader Kings III" for row in monitor),
            "Foreground samples include a different window or dead process")
    require(all(b > a for a, b in zip(times, times[1:])), "Foreground samples are not ordered")
    require(times[0] <= 5 and times[-1] >= duration - 5 and
            max(b-a for a, b in zip(times, times[1:])) <= 5,
            "Foreground sampling has a gap over five seconds or does not cover recording endpoints")
    return {"root": root, "raw": raw, "duration_seconds": duration,
            "resolution": [stream["width"], stream["height"]],
            "actor": pre["actor"], "date_raw": pre["date_raw"], "state": state,
            "recording_started_at": before.isoformat(), "recording_completed_at": after.isoformat(),
            "foreground": {"sample_count": len(monitor), "first_seconds": times[0],
                "last_seconds": times[-1], "max_gap_seconds": max(b-a for a, b in zip(times, times[1:])),
                "coverage": "sampled; cannot exclude events between samples",
                "clock_relation": "wall-clock seconds since recorder Popen preparation; not exact media PTS"}}


def probe_frame_timestamps(raw_path: str | Path, output: str | Path, ffprobe: str = "ffprobe") -> dict:
    """Decode actual frame timing once; header frame-rate values are not evidence of CFR."""
    raw = binding(raw_path)
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    try:
        audit = out / "ffprobe-frames"
        result = run_command(CommandSpec.create([ffprobe, "-v", "error", "-select_streams", "v:0",
            "-show_frames", "-show_streams", "-show_format", "-show_entries",
            "frame=pts,pts_time,best_effort_timestamp,best_effort_timestamp_time,duration,duration_time,pkt_duration,pkt_duration_time:stream=time_base,r_frame_rate,avg_frame_rate,width,height,start_time:format=duration",
            "-of", "json", raw["path"]], label="probe actual gameplay frame timestamps"), audit_directory=audit)
        payload = json.loads(result.stdout)
        try:
            facts = analyze_timestamps(payload)
        except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
            raise GameplayBundleError(f"Invalid actual capture timing: {exc}") from exc
        _bound(raw, "raw after actual frame probe")
        report = {"schema": FRAME_PROBE_SCHEMA, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_recording": raw, **facts,
            "scope": "Decoded media timing only; no scene review, capture approval, or native-AI inference",
            "audit_files": [binding(path) for path in sorted(audit.rglob("*")) if path.is_file()],
            **BOUNDARIES}
        write_new(out / "frame-timestamps.json", report)
        return {"report": binding(out / "frame-timestamps.json"), **{key: report[key] for key in
            ("decoded_frame_count", "nominal_30fps_frame_count", "first_pts_seconds", "last_pts_seconds",
             "maximum_gap_seconds", "maximum_zero_based_30fps_error_seconds", "capture_media_compatible")}}
    except Exception as exc:
        write_new(out / "failure.json", {"status": "failed-retained", "error": str(exc), **BOUNDARIES})
        raise


def extract_frames(recording_dir: str | Path, output: str | Path,
                   begin_seconds: float, end_seconds: float, ffmpeg: str = "ffmpeg", *,
                   frame_probe: str | Path | None = None, ffprobe: str = "ffprobe") -> dict:
    """Extract two real endpoint images for later inspection; always pending."""
    state = completed_recording(recording_dir)
    start, stop = _number(begin_seconds, "begin"), _number(end_seconds, "end")
    require(0 <= start < stop <= state["duration_seconds"], "Span outside actual recording")
    out = Path(output).resolve()
    require(not out.is_relative_to(state["root"]), "Extraction must not modify the recording attempt")
    out.mkdir(parents=True, exist_ok=False)
    try:
        if frame_probe is None:
            probe_record = probe_frame_timestamps(state["raw"]["path"], out / "actual-frame-probe", ffprobe)["report"]
        else:
            probe_record = binding(frame_probe)
        timing = load(probe_record["path"])
        require(timing.get("schema") == FRAME_PROBE_SCHEMA and
                _bound(timing.get("source_recording"), "frame probe source") == state["raw"],
                "Frame probe does not bind this exact raw recording")
        for record in timing.get("audit_files", []):
            _bound(record, "actual frame probe audit")
        require(stop <= timing["supported_end_seconds"],
                "Extraction end exceeds actual PTS/final-frame-duration support; no tail extension")
        selected = [row for row in timing["frames"] if start <= row["pts_seconds"] < stop]
        require(len(selected) >= 2, "Requested interval contains fewer than two actual timestamped frames")
        frames = []
        for phase, source_frame in (("begin", selected[0]), ("end", selected[-1])):
            seconds = source_frame["pts_seconds"]
            image = out / f"{phase}.png"
            audit = out / f"extract-{phase}"
            actual_pts = source_frame["pts"]
            command = CommandSpec.create([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "warning", "-n",
                "-i", state["raw"]["path"], "-map", "0:v:0", "-vf", f"select=eq(pts\\,{actual_pts})",
                "-frames:v", "1", "-fps_mode", "passthrough", "-an", image], label=f"extract gameplay {phase} endpoint by actual PTS",
                partial_artifacts=[image])
            result = run_command(command, audit_directory=audit)
            require(image.is_file() and image.stat().st_size > 0,
                    f"FFmpeg exited {result.returncode} without an endpoint PNG: {phase}, actual PTS "
                    f"{actual_pts} ({seconds}s), decoded frame {source_frame['decoded_index']} of "
                    f"{timing['decoded_frame_count']}; metadata FPS cannot establish a frame's existence. "
                    f"Command and stderr retained in {audit}")
            with Image.open(image) as picture:
                require(list(picture.size) == state["resolution"], "Extracted endpoint dimensions differ")
            frames.append({"phase": phase, "media_seconds": seconds, "pts": actual_pts,
                "decoded_index": source_frame["decoded_index"], "time_base": timing["stream"]["time_base"],
                "media_time_basis": "actual probed frame PTS; no frame inferred from header FPS",
                "image": binding(image),
                "command_argv": list(command.argv), "returncode": result.returncode,
                "audit_files": [binding(path) for path in sorted(audit.rglob("*")) if path.is_file()]})
        _bound(state["raw"], "raw after extraction")
        manifest = {"schema": EXTRACTION_SCHEMA, "status": "pending-agent-image-review",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_recording": state["raw"], "recording_dir": state["root"].as_posix(),
            "recording_result": binding(state["root"] / "recording-result.json"),
            "requested_begin_seconds": start, "begin_seconds": selected[0]["pts_seconds"],
            "end_seconds": stop, "end_is_exclusive": True,
            "endpoint_selection": "first existing PTS at/after begin; last existing PTS strictly before end",
            "actual_frame_probe": probe_record, "capture_media_compatible": timing["capture_media_compatible"],
            "capture_media_timing_policy": timing.get("capture_media_timing_policy"),
            "sampling_quality": timing.get("sampling_quality"),
            "import_limitation": "PTS-supported windows only; final 30fps delivery reuses/drops source samples without increasing observation resolution.",
            "frames": frames, **BOUNDARIES}
        write_new(out / "extraction.json", manifest)
        return {"extraction": binding(out / "extraction.json"), "status": manifest["status"],
            "capture_media_compatible": manifest["capture_media_compatible"],
            "import_limitation": manifest["import_limitation"], "frames": frames}
    except Exception as exc:
        write_new(out / "failure.json", {"status": "failed-retained", "error": str(exc), **BOUNDARIES})
        raise


def _review(review_path: Path, state: dict) -> tuple[dict, dict]:
    review = load(review_path)
    require(review.get("schema") == REVIEW_SCHEMA, "Unexpected image review schema")
    require(review.get("reviewer", {}).get("kind") == "agent" and
            bool(review.get("reviewer", {}).get("id")), "Explicit actual agent reviewer required")
    reviewed_at = _utc(review.get("reviewed_at_utc"), "image review")
    require(reviewed_at >= _utc(state["recording_completed_at"], "completion"), "Review predates completed recording")
    require(review.get("review_scope") == "endpoint-images-and-sampled-foreground",
            "This producer only supports endpoint images plus sampled foreground review")
    require(all(review.get(key) is False for key in BOUNDARIES),
            "Review must explicitly retain no-causality/no-human-signoff/no-frame-sync boundaries")
    require(re.fullmatch(r"[a-zA-Z0-9_-]+", str(review.get("span_id", ""))) is not None,
            "A stable nonempty span_id is required")
    extraction_record = _bound(review.get("extraction"), "review.extraction")
    extraction = load(extraction_record["path"])
    require(extraction.get("schema") == EXTRACTION_SCHEMA and
            extraction.get("status") == "pending-agent-image-review", "Unsupported extraction receipt")
    timing_record = _bound(extraction.get("actual_frame_probe"), "extraction actual frame probe")
    timing = load(timing_record["path"])
    require(timing.get("schema") == FRAME_PROBE_SCHEMA and
            _bound(timing.get("source_recording"), "actual frame probe source") == state["raw"],
            "Actual frame probe source differs")
    require(timing.get("capture_media_compatible") is True and extraction.get("capture_media_compatible") is True
            and timing.get("capture_media_timing_policy") == TIMING_POLICY
            and extraction.get("capture_media_timing_policy") == TIMING_POLICY,
            "A fresh actual-PTS timing report and matching reviewed extraction are required; old CFR-only receipts remain unchanged.")
    require(reviewed_at >= _utc(extraction.get("created_at_utc"), "extraction"), "Review predates extracted images")
    raw = _bound(extraction.get("source_recording"), "extraction source")
    require(raw == state["raw"], "Reviewed frame source differs from completed recording")
    _bound(extraction.get("recording_result"), "extraction completion receipt")
    begin, end = extraction["begin_seconds"], extraction["end_seconds"]
    require(0 <= begin < end <= state["duration_seconds"] and extraction.get("end_is_exclusive") is True,
            "Reviewed extraction span lies outside recording")
    require(len(extraction.get("frames", [])) == 2 and len(review.get("frames", [])) == 2,
            "Both exact endpoint images require actual inspection")
    selected = [row for row in timing["frames"] if begin <= row["pts_seconds"] < end]
    require(len(selected) >= 2, "Review interval contains fewer than two actual frames")
    for phase, source_frame, image_row, observed in zip(("begin", "end"), (selected[0], selected[-1]),
            extraction["frames"], review["frames"]):
        require(image_row.get("phase") == phase and observed.get("phase") == phase and
                image_row.get("pts") == source_frame["pts"] and
                image_row.get("decoded_index") == source_frame["decoded_index"] and
                image_row.get("media_seconds") == source_frame["pts_seconds"],
                "Review/extraction endpoint phases or media times differ")
        image = _bound(image_row.get("image"), f"{phase} extracted image")
        require(_bound(observed.get("image"), f"{phase} inspected image") == image,
                "Review does not bind the extracted image")
        require(image_row.get("returncode") == 0 and bool(image_row.get("audit_files")),
                "Successful actual extraction command audit missing")
        for audit in image_row["audit_files"]:
            _bound(audit, f"{phase} extraction audit")
        flags = observed.get("observations", {})
        require(all(flags.get(key) is True for key in
                ("gameplay_hud", "paused_map", "no_loading", "no_foreign_overlay")) and bool(observed.get("notes")),
                f"{phase}: actual HUD/paused/no-loading/no-overlay observations and notes required")
    native = review.get("native_readback", {})
    require(native.get("association") == "same-paused-state-not-frame-synchronized" and bool(native.get("notes")),
            "Native readback must state its limited association; no exact same-frame inference")
    after = _bound(native.get("snapshot_after"), "native snapshot after")
    _snapshot(Path(after["path"]), state["actor"], state["date_raw"])
    after_payload = load(after["path"])
    require(_utc(after_payload.get("at"), "snapshot after") >=
            _utc(state["recording_completed_at"], "completion"), "Post-recording snapshot predates recording completion")
    queries = native.get("queries", [])
    require(isinstance(queries, list) and len(queries) > 0, "At least one explicit native query evidence file required")
    for query in queries:
        item = _bound(query, "native query")
        _body(Path(item["path"]))
        _utc(load(item["path"]).get("at"), "native query receipt")
    return review, extraction


def _file_records(value: Any):
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"} <= value.keys():
            yield value
        for item in value.values():
            yield from _file_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from _file_records(item)


def package_gameplay_bundle(recording_dir: str | Path, review_json: str | Path,
                            output: str | Path, producer_script: str | Path,
                            evidence: list[str | Path] = ()) -> dict:
    """Create a new adapter bundle only after actual image review was supplied."""
    state = completed_recording(recording_dir)
    review_path, script = Path(review_json).resolve(), Path(producer_script).resolve()
    review, extraction = _review(review_path, state)
    out = Path(output).resolve()
    require(not out.is_relative_to(state["root"]), "Bundle must not modify the original recording attempt")
    require(not out.exists(), "Bundle destination already exists; select a new attempt")
    # Freeze the source set and recursively collect explicit exact-bound inputs.
    sources = {path.resolve(): binding(path) for path in state["root"].rglob("*") if path.is_file()}
    for path in (review_path, script, Path(__file__).resolve(), *(Path(p).resolve() for p in evidence)):
        sources[path] = binding(path)
    queue = list(sources)
    for path in queue:
        if path.suffix.lower() != ".json":
            continue
        for record in _file_records(load(path)):
            actual = _bound(record, f"source reference in {path.name}")
            linked = Path(actual["path"])
            if linked not in sources:
                sources[linked] = actual
                queue.append(linked)
    require(all(not out.is_relative_to(path) for path in sources), "Invalid nested bundle destination")
    out.mkdir(parents=True, exist_ok=False)
    try:
        copied = {}
        mapping = []
        for original, identity in sources.items():
            if original.is_relative_to(state["root"]):
                relative = Path("source-recording") / original.relative_to(state["root"])
            else:
                relative = Path("source-evidence") / identity["sha256"] / original.name
            destination = out / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with original.open("rb") as src, destination.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
            preserved = binding(destination)
            require((preserved["bytes"], preserved["sha256"]) == (identity["bytes"], identity["sha256"]),
                    f"Copy differs: {original}")
            copied[original] = preserved
            mapping.append({"original": identity, "preserved": preserved})
        def relocated(path: str | Path) -> dict:
            return copied[Path(path).resolve()]
        queries = []
        start_at = _utc(state["recording_started_at"], "recording start")
        stop_at = _utc(state["recording_completed_at"], "recording end")
        for item in review["native_readback"]["queries"]:
            at = _utc(load(item["path"])["at"], "query timestamp")
            queries.append({"evidence": relocated(item["path"]), "recorded_at": at.isoformat(),
                "temporal_relation": "before-recording" if at < start_at else
                    "after-recording" if at > stop_at else "during-recorder-wall-clock-window",
                "exact_media_frame_relation": "not-established", "query_payload_semantics_verified": False})
        evidence_summary = {"schema": PRODUCER, "scope": SCOPE, **BOUNDARIES,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_mapping": mapping, "foreground_sampling": state["foreground"],
            "native_state": {"actor": state["actor"], "date_raw": state["date_raw"],
                "paused_at_readback_endpoints": True,
                "snapshot_before": relocated(state["root"] / "snapshot-before.json"),
                "snapshot_after": relocated(review["native_readback"]["snapshot_after"]["path"]),
                "queries": queries, "association": review["native_readback"]["association"]},
            "actual_agent_image_review": relocated(review_path),
            "actual_frame_probe": relocated(extraction["actual_frame_probe"]["path"]),
            "capture_media_timing_policy": extraction["capture_media_timing_policy"],
            "sampling_quality": extraction["sampling_quality"],
            "recorder_implementation": relocated(script), "bundle_implementation": relocated(__file__),
            "limitations": ["Endpoint images and sampled foreground do not establish every intervening frame.",
                "Native queries retain their actual receipt times; no synchronized-frame or autonomous-AI cause is inferred.",
                "GREEN is this producer's paused-map capture evidence result, not a research or film approval."]}
        summary_path = out / "producer-evidence.json"
        write_new(summary_path, evidence_summary)
        span = review["span_id"]
        frames = []
        for row in extraction["frames"]:
            frame = {"schema_version": 1, "result": "GREEN", "span": span, "phase": row["phase"],
                "producer": PRODUCER, "scope": SCOPE, "media_seconds": row["media_seconds"],
                "image": relocated(row["image"]["path"]),
                "review": relocated(review_path), "extraction": relocated(review["extraction"]["path"]),
                "producer_evidence": binding(summary_path),
                "preserved_sources": [value for path, value in copied.items()
                    if path != Path(state["raw"]["path"])], **BOUNDARIES}
            gate = out / "cell" / "promo" / f"{span}-{row['phase']}-gate.json"
            write_new(gate, frame)
            frames.append({**frame, "gate": binding(gate)})
        raw = relocated(state["raw"]["path"])
        marks = [{"label": "recording_started_after_gameplay_hud", "seconds": 0},
            {"label": f"{span}_clean_begin", "seconds": extraction["begin_seconds"]},
            {"label": f"{span}_clean_end", "seconds": extraction["end_seconds"]},
            {"label": "recording_stop_requested", "seconds": state["duration_seconds"]}]
        timeline = {"schema": PRODUCER, "source_kind": "real CK3 gameplay HUD; paused-map observational recording",
            "exclude_ck3_loading": True, "raw_path": raw["path"], "raw_bytes": raw["bytes"],
            "raw_sha256": raw["sha256"], "marks": marks, "clean_capture_complete": True,
            "missing_clean_spans": [], "clean_frame_gates": [{"span_id": span, "result": "GREEN",
                "begin_mark": f"{span}_clean_begin", "end_mark": f"{span}_clean_end", "frames": frames}],
            "producer": PRODUCER, "scope": SCOPE, **BOUNDARIES,
            "mark_semantics": {"recording_started_after_gameplay_hud": "Media time zero; independent HUD observation predates recorder launch.",
                "recording_stop_requested": "Actual probed media end after recorder's duration-limited successful completion; not a user stop event.",
                "clean_end": "Exclusive media boundary; endpoint image is the last actual probed PTS strictly before it."}}
        write_new(out / "cell" / "promo" / "capture-timeline.json", timeline)
        report = {"schema_version": 1, "result": "GREEN", "producer": PRODUCER, "scope": SCOPE,
            "original_attempt_modified": False, **BOUNDARIES,
            "cell": {"schema_version": 1, "result": "GREEN", "producer": PRODUCER,
                "scope": SCOPE, "promo_capture": timeline}}
        write_new(out / "report.json", report)
        indexed = [{**binding(path), "path": path.relative_to(out).as_posix()}
            for path in sorted(out.rglob("*")) if path.is_file()]
        write_new(out / "evidence-index.json", {"schema_version": 1, "result": "GREEN",
            "artifact_root": out.as_posix(), "producer": PRODUCER, "scope": SCOPE, "files": indexed})
        bundle = load_capture_bundle(out, required_span_ids=[span])
        receipt = {"schema": PRODUCER, "status": "adapter-validated-paused-map-evidence",
            "scope": SCOPE, **BOUNDARIES, "bundle_root": out.as_posix(), "span_id": span,
            "begin_seconds": bundle.clean_span(span).begin_seconds,
            "end_seconds": bundle.clean_span(span).end_seconds,
            "report": binding(out / "report.json"), "timeline": binding(out / "cell/promo/capture-timeline.json"),
            "evidence_index": binding(out / "evidence-index.json"), "raw": raw,
            "producer_evidence": binding(summary_path)}
        write_new(out / "bundle-receipt.json", receipt)
        return receipt
    except Exception as exc:
        write_new(out / "failure.json", {"status": "failed-retained", "error": str(exc), **BOUNDARIES})
        raise
