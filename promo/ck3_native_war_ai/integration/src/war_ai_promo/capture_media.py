"""Prepare a continuous clip from an existing verified CK3 capture bundle.

This module never creates capture reports, launches CK3, fills missing footage,
or treats an editorial evidence label as a proof of native AI causality.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction
import json
import math
from pathlib import Path
import shutil
from typing import Any, Mapping

from xar_promo.adapters.ck3 import load_capture_bundle
from xar_promo.media import probe_and_write_bound_media
from xar_promo.process import CommandSpec, run_command

from .common import binding, load, write_new
from .capture_timing import display_sampling
from .gameplay_bundle import probe_frame_timestamps


SPEC_SCHEMA = "ck3-war-ai.capture-clips.v1"
RECEIPT_SCHEMA = "ck3-war-ai.prepared-capture-clip.v2"
EVIDENCE_ROLES = frozenset({
    "context", "mechanism-illustration", "candidate-causal-case", "controlled-experiment",
})
CLIP_FIELDS = frozenset({
    "cue_id", "bundle_root", "span_id", "offset_seconds", "duration_seconds",
    "evidence_role", "claim_ids",
})
FPS = 30


class CaptureClipError(ValueError):
    """A requested clip cannot be prepared under the continuous-footage contract."""


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise CaptureClipError(f"{label} must be a non-empty NUL-free string")
    return value


def _seconds(value: Any, label: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CaptureClipError(f"{label} must be finite numeric seconds")
    number = Decimal(str(value))
    if number < 0 or (positive and number <= 0):
        raise CaptureClipError(f"{label} must be {'positive' if positive else 'non-negative'}")
    return number


def _clip_spec(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != CLIP_FIELDS:
        raise CaptureClipError(f"clip requires exactly these fields: {sorted(CLIP_FIELDS)}")
    row = dict(value)
    for key in ("cue_id", "bundle_root", "span_id", "evidence_role"):
        _string(row[key], key)
    if not Path(row["bundle_root"]).is_absolute():
        raise CaptureClipError("bundle_root must be absolute")
    if row["evidence_role"] not in EVIDENCE_ROLES:
        raise CaptureClipError(f"evidence_role must be one of {sorted(EVIDENCE_ROLES)}")
    _seconds(row["offset_seconds"], "offset_seconds")
    _seconds(row["duration_seconds"], "duration_seconds", positive=True)
    claims = row["claim_ids"]
    if not isinstance(claims, list) or not claims:
        raise CaptureClipError("claim_ids must be a non-empty list")
    for claim in claims:
        _string(claim, "claim_id")
    if len(set(claims)) != len(claims):
        raise CaptureClipError("claim_ids must not repeat")
    row["claim_ids"] = list(claims)
    return row


def load_capture_spec(path: str | Path) -> list[dict[str, Any]]:
    """Read a project selection file; paths remain explicit and absolute.

    The caller should preserve the original spec bytes in its run. Individual
    preparations also save their exact normalized request as a new JSON file.
    """
    document = load(path)
    if not isinstance(document, dict) or set(document) != {"schema", "clips"}:
        raise CaptureClipError("capture spec requires schema and clips")
    if document["schema"] != SPEC_SCHEMA or not isinstance(document["clips"], list):
        raise CaptureClipError(f"capture spec schema must be {SPEC_SCHEMA}")
    if not document["clips"]:
        raise CaptureClipError("capture spec clips must not be empty")
    rows = [_clip_spec(row) for row in document["clips"]]
    if len({row["cue_id"] for row in rows}) != len(rows):
        raise CaptureClipError("one capture clip per cue; duplicate cue_id")
    return rows


def _capture_binding(record: Any) -> dict[str, Any]:
    return {"path": record.path.resolve().as_posix(), "relative_path": record.relative_path,
            "bytes": record.bytes, "sha256": record.sha256.lower()}


def _same_binding(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    return actual["bytes"] == expected["bytes"] and actual["sha256"].lower() == expected["sha256"].lower()


def _copy_control(record: Any, controls_root: Path) -> dict[str, Any]:
    """Copy exact control bytes under a digest name; never rewrite JSON paths."""
    expected = _capture_binding(record)
    suffix = record.path.suffix or ".bin"
    destination = controls_root / f"{record.sha256.lower()}{suffix}"
    if not destination.exists():
        with record.path.open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target, 1024 * 1024)
    actual = binding(destination)
    if not _same_binding(actual, expected):
        raise CaptureClipError(f"control bytes changed during preservation: {record.relative_path}")
    return {"source": expected, "preserved": actual}


def _video_stream(probe: Any) -> Mapping[str, Any]:
    streams = [row for row in probe.raw.get("streams", []) if row.get("codec_type") == "video"]
    if len(streams) != 1:
        raise CaptureClipError("capture requires exactly one video stream")
    return streams[0]


def _require_30fps(stream: Mapping[str, Any]) -> None:
    try:
        rates = [Fraction(str(stream[key])) for key in ("r_frame_rate", "avg_frame_rate")]
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise CaptureClipError("missing or invalid frame rate") from exc
    if any(rate != FPS for rate in rates):
        raise CaptureClipError("prepared output must be 30 fps; this is not a source frame-rate requirement")


def _frame_window(span: Any, spec: Mapping[str, Any], source_duration: float) -> dict[str, Any]:
    begin = Decimal(str(span.begin_seconds))
    end = Decimal(str(span.end_seconds))
    requested_begin = begin + _seconds(spec["offset_seconds"], "offset_seconds")
    requested_end = requested_begin + _seconds(spec["duration_seconds"], "duration_seconds", positive=True)
    if requested_begin < begin or requested_end > end:
        raise CaptureClipError("requested clip extends outside the selected clean span")
    if requested_end > Decimal(str(source_duration)):
        raise CaptureClipError("requested clip extends beyond probed recording duration")
    # Round inward. No frame, including its display duration, crosses the
    # requested interval or clean-span boundary. A short remainder is not padded.
    first = int((requested_begin * FPS).to_integral_value(rounding=ROUND_CEILING))
    stop = int((requested_end * FPS).to_integral_value(rounding=ROUND_FLOOR))
    if stop <= first:
        raise CaptureClipError("requested clip contains no complete 30 fps frame")
    if Decimal(str(spec["duration_seconds"])) - Decimal(stop - first) / FPS > Decimal(1) / FPS + Decimal('0.000000001'):
        raise CaptureClipError("inward trim loses more than one frame; select a frame-aligned window")
    return {
        "requested_source_begin_seconds": float(requested_begin),
        "requested_source_end_seconds": float(requested_end),
        "output_grid_first_frame": first, "output_grid_stop_frame_exclusive": stop,
        "source_begin_seconds": first / FPS, "source_end_seconds": stop / FPS,
        "expected_frame_count": stop - first, "expected_duration_seconds": (stop - first) / FPS,
        "quantization": "inward-30fps-output-time-grid; actual source PTS sampled at 1x; no-loop-no-tail-padding",
        "omitted_boundary_seconds": float(_seconds(spec["duration_seconds"], "duration_seconds") - Decimal(stop-first)/FPS),
    }


def _frame_audit(ffprobe: str | Path, video: Path, audit: Path, expected: int) -> dict[str, Any]:
    result = run_command(CommandSpec.create([
        ffprobe, "-v", "error", "-select_streams", "v:0", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", video,
    ], label="capture clip frame timestamp audit"), audit_directory=audit)
    rows = json.loads(result.stdout).get("frames", [])
    if len(rows) != expected:
        raise CaptureClipError(f"clip decoded {len(rows)} frames, expected {expected}")
    times = [float(row["best_effort_timestamp_time"]) for row in rows]
    if any(not math.isfinite(value) or abs(value - index / FPS) > 0.0001
           for index, value in enumerate(times)):
        raise CaptureClipError("clip is not a continuous 30 fps 1x timestamp sequence")
    return {"decoded_frame_count": len(times), "first_seconds": times[0],
            "last_seconds": times[-1], "max_timestamp_error_seconds": max(
                abs(value - index / FPS) for index, value in enumerate(times)),
            "scope": "timing/layout/media integrity; not scene semantics or native-AI causality"}


def prepare_capture_clip(
    spec: Mapping[str, Any], destination: str | Path, ffmpeg: str | Path,
    ffprobe: str | Path, audit_directory: str | Path,
) -> dict[str, Any]:
    """Prepare one new silent 2560x1440 clip and retained provenance receipt.

    ``spec`` is one row returned by :func:`load_capture_spec`. Offset is relative
    to its clean span. Source may be CFR or VFR with actual increasing PTS.
    The selected duration rounds inward to full output frames; 30fps delivery
    samples the current source frame at 1x, never inventing intervening motion.
    The caller must use the returned measured duration.
    Failures retain their audit, copied controls and any partial output.
    """
    row = _clip_spec(spec)
    destination = Path(destination).resolve()
    audit = Path(audit_directory).resolve()
    root = Path(row["bundle_root"]).resolve()
    if destination.suffix.lower() != ".mp4":
        raise CaptureClipError("destination must be a new .mp4 file")
    if destination.exists() or audit.exists():
        raise FileExistsError("destination and audit_directory must both be new")
    if destination.is_relative_to(root) or audit.is_relative_to(root):
        raise CaptureClipError("outputs must not mutate the capture bundle")
    audit.mkdir(parents=True, exist_ok=False)
    write_new(audit / "request.json", {"schema": SPEC_SCHEMA, "clips": [row]})
    try:
        bundle = load_capture_bundle(root, required_span_ids=[row["span_id"]])
        span = bundle.clean_span(row["span_id"])
        controls_root = audit / "controls"
        controls_root.mkdir()
        records = [bundle.report, bundle.timeline, bundle.evidence_index]
        # Preserve every control file that the adapter validated, including
        # evidence for other spans referenced by the immutable timeline.
        records.extend(record for clean in bundle.clean_spans for record in clean.evidence)
        seen = set()
        controls = []
        for record in records:
            key = record.path.resolve()
            if key not in seen:
                controls.append(_copy_control(record, controls_root))
                seen.add(key)
        write_new(audit / "control-index.json", {"files": controls,
                  "note": "Exact source bytes; original absolute paths intentionally preserved. Not a rewritten capture bundle."})
        source_probe_path = audit / "source.bound-probe.json"
        source = probe_and_write_bound_media(ffprobe, bundle.raw_capture.path,
            output_path=source_probe_path, audit_directory=audit / "probe-source")
        expected_source = _capture_binding(bundle.raw_capture)
        if not _same_binding({"bytes": source.subject_bytes, "sha256": source.subject_sha256}, expected_source):
            raise CaptureClipError("source probe bytes differ from the verified capture bundle")
        stream = _video_stream(source.probe)
        if abs(float(stream.get("start_time", source.probe.format.get("start_time", 0)))) > 0.0001:
            raise CaptureClipError("source video must start at zero for capture-timeline seconds")
        rotation = [side.get("rotation", 0) for side in stream.get("side_data_list", [])]
        if any(float(angle) % 360 for angle in rotation) or float(stream.get("tags", {}).get("rotate", 0)) % 360:
            raise CaptureClipError("rotated capture sources need an explicit separate preparation")
        window = _frame_window(span, row, source.probe.require_duration())
        timing_result = probe_frame_timestamps(bundle.raw_capture.path, audit / "source-timing", str(ffprobe))
        timing = load(timing_result["report"]["path"])
        if not _same_binding(timing["source_recording"], expected_source):
            raise CaptureClipError("actual PTS probe source differs from capture bundle")
        try:
            sampling = display_sampling(timing, window, span.begin_seconds)
        except ValueError as exc:
            raise CaptureClipError(str(exc)) from exc
        sampling_path = audit / "display-sampling.json"
        write_new(sampling_path, sampling)
        write_new(audit / "selection.json", {"span_id": span.span_id,
                  "clean_begin_seconds": span.begin_seconds, "clean_end_seconds": span.end_seconds, **window})
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Keep one real successor PTS when available so the fps filter has a
        # genuine timing boundary. round=up delays a new frame until its PTS;
        # the explicit output limit cannot extend the verified source window.
        filters = (f"trim=start_frame={sampling['first_source_decoded_index']}:end_frame={sampling['decode_stop_frame_exclusive']},"
                   f"settb=expr=1/{sampling['filter_time_base_denominator']},setpts=PTS-{sampling['filter_start_offset_ticks']},"
                   f"fps=30:start_time=0:round=up:eof_action=pass,trim=end_frame={window['expected_frame_count']},"
                   "scale=2560:1440:force_original_aspect_ratio=decrease:force_divisible_by=2:reset_sar=1,"
                   "pad=2560:1440:(ow-iw)/2:(oh-ih)/2:color=black")
        command = CommandSpec.create([
            ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "warning", "-n",
            "-i", bundle.raw_capture.path, "-map", "0:v:0", "-an", "-sn", "-dn",
            "-vf", filters, "-fps_mode", "passthrough", "-c:v", "libx264",
            "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-frames:v", str(window["expected_frame_count"]),
            "-map_metadata", "-1", "-movflags", "+faststart", destination,
        ], label="prepare continuous CK3 capture clip", partial_artifacts=[destination])
        run_command(command, audit_directory=audit / "encode")
        output_probe_path = audit / "clip.bound-probe.json"
        output = probe_and_write_bound_media(ffprobe, destination,
            output_path=output_probe_path, audit_directory=audit / "probe-output")
        output_stream = _video_stream(output.probe)
        _require_30fps(output_stream)
        if (output_stream.get("width"), output_stream.get("height")) != (2560, 1440):
            raise CaptureClipError("clip dimensions are not 2560x1440")
        if output.probe.audio_streams:
            raise CaptureClipError("prepared clip unexpectedly contains source audio")
        duration = output.probe.require_duration()
        if abs(duration - window["expected_duration_seconds"]) > 0.002:
            raise CaptureClipError("clip duration differs from selected source frames")
        frame_check = _frame_audit(ffprobe, destination, audit / "frame-timestamps", window["expected_frame_count"])
        bundle.verify_unchanged()
        video_binding = binding(destination)
        if not _same_binding(video_binding, {"bytes": output.subject_bytes, "sha256": output.subject_sha256}):
            raise CaptureClipError("clip changed after its bound probe")
        receipt = {
            "schema": RECEIPT_SCHEMA, "status": "prepared-media-not-causal-approval",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "cue_id": row["cue_id"], "claim_ids": row["claim_ids"],
            "evidence_role": row["evidence_role"], "source_kind": bundle.source_kind,
            "editorial_label_proves_causality": False, "native_ai_causality_verified": False,
            "human_1x_review_performed": False, "signoff_granted": False,
            "source_recording": expected_source, "source_bundle_root": root.as_posix(),
            "span_id": span.span_id, "clean_begin_seconds": span.begin_seconds,
            "clean_end_seconds": span.end_seconds, "selection": window,
            "media": video_binding, "duration_seconds": duration, "fps": FPS,
            "resolution": [2560,1440], "source_audio_included": False,
            "controls": controls, "control_index": binding(audit / "control-index.json"),
            "request": binding(audit / "request.json"),
            "source_bound_probe": binding(source_probe_path),
            "source_actual_timing": timing_result["report"],
            "source_sampling_quality": {key: timing[key] for key in (
                "decoded_frame_count", "first_pts_seconds", "last_pts_seconds", "minimum_gap_seconds",
                "maximum_gap_seconds", "mean_gap_seconds", "median_gap_seconds", "mean_observed_frame_rate",
                "supported_end_seconds", "tail_support", "contiguous_zero_based_30fps", "sampling_quality")},
            "display_sampling": binding(sampling_path),
            "delivery_sampling": {key: value for key, value in sampling.items() if key != "mapping"},
            "output_bound_probe": binding(output_probe_path), "frame_check": frame_check,
            "source_integrity_rechecked": True,
            "commands": [binding(path) for path in sorted(audit.glob("*/command.json"))],
            "preservation_note": "Preserve the rendered clip, receipt and entire audit tree. Raw recording remains in its original retained bundle; copied controls do not constitute a relocated adapter bundle.",
        }
        receipt_path = audit / "receipt.json"
        write_new(receipt_path, receipt)
        return {**receipt, "receipt": binding(receipt_path), "audit_directory": audit.as_posix()}
    except Exception as exc:
        write_new(audit / "failure.json", {
            "schema": RECEIPT_SCHEMA, "status": "failed-retained",
            "error_type": type(exc).__name__, "error": str(exc),
            "partial_media": binding(destination) if destination.is_file() else None,
            "native_ai_causality_verified": False, "signoff_granted": False,
        })
        raise
