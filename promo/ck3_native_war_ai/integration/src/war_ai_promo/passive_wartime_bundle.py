"""Read-only CASE-C producer for an existing, passively observed CK3 war.

The original CASE-W producer requires fresh operator declaration, raise and
move evidence. CASE-C has none: it follows those already committed routes and
stops on an unrelated pending interaction before any actual combat is bound.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil

from xar_promo.adapters.ck3 import load_capture_bundle

from .common import binding, load, write_new
from . import gameplay_bundle as gb
from . import wartime_bundle as wb
from .capture_timing import TIMING_POLICY


PRODUCER = "war-ai-promo.passive-wartime-observation.v1"
REVIEW_SCHEMA = "ck3-war-ai.passive-wartime-frame-review.v1"
SCOPE = "existing War4 routes during bounded passive observation; stopped on pending interaction"
BOUNDARIES = {**wb.BOUNDARIES,
    "actual_combat_id_bound": False,
    "native_battle_result_proven": False,
    "new_operator_war_order_in_case": False}
START_DATE = 53144784
END_DATE = 53145504
WAR_ID = 4
ACTOR = 29829
OPPONENT = 31549
ALLOWED_TOOLS = {"ck3_take_snapshot": 68, "ck3_execute_step": 3,
    "ck3_get_capabilities": 1, "ck3_get_war_state": 1}
STEPS = ("set-speed-2", "resume-map", "pause-map")
require = gb.require


def completed_passive_recording(recording_dir):
    return wb.completed_wartime_recording(recording_dir)


def extract_passive_frames(recording_dir, output, begin_seconds, end_seconds,
                           ffmpeg="ffmpeg", *, frame_probe=None, ffprobe="ffprobe"):
    return gb.extract_frames(recording_dir, output, begin_seconds, end_seconds, ffmpeg,
        frame_probe=frame_probe, ffprobe=ffprobe,
        recording_validator=completed_passive_recording)


def _war(snapshot):
    wars = [row for row in snapshot.get("active_wars", []) if row.get("war_id") == WAR_ID]
    require(len(wars) == 1 and wars[0].get("primary_opponent_character_id") == OPPONENT,
            "CASE-C War4/opponent identity changed")
    return wars[0]


def validate_observation_semantics(start, calls, outcome, observation_started):
    """Pure readback gate; synthetic tests need no CK3, FFmpeg or large media."""
    require(start.get("paused") is True and start.get("date_raw") == START_DATE and
            (start.get("played_character") or {}).get("character_id") == ACTOR,
            "CASE-C must start paused on the W day19 checkpoint")
    _war(start)
    require(observation_started.get("new_orders_submitted") == 0 and
            observation_started.get("maximum_game_days") == 120 and
            observation_started.get("maximum_wall_seconds") == 600,
            "Observation start budget or zero-new-order contract differs")
    first = observation_started.get("snapshot") or {}
    require(first.get("paused") is True and first.get("date_raw") == START_DATE and
            (first.get("played_character") or {}).get("character_id") == ACTOR,
            "Observation start snapshot differs")
    _war(first)
    require(Counter(row.get("tool") for row in calls) == ALLOWED_TOOLS,
            "CASE-C calls include missing, extra or forbidden native tools")
    sample_rows = [(index, row["body"]) for index, row in enumerate(calls)
                   if row["tool"] == "ck3_take_snapshot"]
    require(len(sample_rows) == 68 and sample_rows[0][1].get("paused") is True,
            "68 native snapshot publications and an initial pause are required")
    dates = []
    for _, snapshot in sample_rows:
        require((snapshot.get("played_character") or {}).get("character_id") == ACTOR and
                snapshot.get("map_ready") is True, "Actor or map identity changed")
        require(snapshot.get("active_event") is None and
                (snapshot.get("pending_character_interaction") is None or
                 snapshot.get("date_raw") == END_DATE),
                "An event or earlier pending interaction would have stopped this window")
        war = _war(snapshot)
        require(war.get("player_side") == "attacker" and
                war.get("player_relative_war_score") == 0,
                "War4 side or observed score differs")
        armies = [*war.get("allied_armies", []), *war.get("enemy_armies", [])]
        require(not any(row.get("in_combat") is True for row in armies),
                "Actual in_combat publication cannot be packaged as zero-contact CASE-C")
        dates.append(snapshot.get("date_raw"))
    require(all(type(date) is int for date in dates) and
            dates[0] == START_DATE and dates[-1] == END_DATE and
            all(a <= b for a, b in zip(dates, dates[1:])) and len(set(dates)) == 31,
            "CASE-C snapshots must cover ordered day19 to day49 publications")
    require(sample_rows[-1][1].get("paused") is True and
            sample_rows[-1][1].get("active_event") is None,
            "Final native snapshot must be paused without an active event")
    pending = sample_rows[-1][1].get("pending_character_interaction") or {}
    require(pending.get("instance_id") == 16777352 and
            pending.get("sender_character_id") == 32522 and
            pending.get("auto_accept_notification") is False,
            "Final pending interaction differs from the observed stop")
    steps = [(index, row) for index, row in enumerate(calls) if row["tool"] == "ck3_execute_step"]
    require(tuple(row["arguments"].get("step") for _, row in steps) == STEPS,
            "Only speed2/resume/pause in that order are allowed")
    for index, row in steps:
        prior = next(((j, snap) for j, snap in reversed(sample_rows) if j < index), None)
        require(prior is not None and row["arguments"].get("expected_revision") == prior[1].get("revision") and
                row.get("wrapper_result") == "CALL_COMPLETED" and
                (row.get("body") or {}).get("accepted") is True,
                "Step lacks matching pre-snapshot revision or accepted native response")
    require(steps[0][0] < steps[1][0] < steps[2][0] < sample_rows[-1][0] and
            sample_rows[-2][0] < steps[2][0],
            "Pause command or final state is out of sequence")
    prior_indices = {row.get("index") for row in start.get("native_command_history", [])}
    new_history = [row.get("command") for row in sample_rows[-1][1].get("native_command_history", [])
                   if row.get("index") not in prior_indices]
    require(tuple(new_history) == STEPS,
            "Native command history shows another action or omits speed/resume/pause")
    require(outcome.get("reason") == "event_or_interaction" and outcome.get("candidate") is None and
            outcome.get("observed_days") == 30.0 and
            0 < gb._number(outcome.get("wall_seconds"), "CASE-C wall duration") <= 600,
            "CASE-C must end on its observed interaction without CombatID")
    final = outcome.get("paused_snapshot") or {}
    require(final.get("snapshot_id") == sample_rows[-1][1].get("snapshot_id") and
            final.get("revision") == sample_rows[-1][1].get("revision") and
            final.get("date_raw") == END_DATE and final.get("paused") is True and
            final.get("pending_character_interaction") == pending,
            "Outcome does not bind the final paused publication")
    date_rows = outcome.get("date_observations") or []
    require(len(date_rows) == 31 and
            [row.get("date_raw") for row in date_rows] == list(range(START_DATE, END_DATE + 1, 24)),
            "Original observation log does not cover the declared 30 game days")
    war_state = outcome.get("war_state") or {}
    require(war_state.get("status") == "active" and
            any(row.get("war_id") == WAR_ID for row in war_state.get("active_wars", [])),
            "Final formal War4 state is missing")
    return {"start_date_raw": START_DATE, "end_date_raw": END_DATE,
        "observed_game_days": 30, "observed_wall_seconds": outcome["wall_seconds"],
        "sample_count": len(sample_rows), "distinct_dates": len(set(dates)),
        "steps": [row["arguments"]["step"] for _, row in steps],
        "stop_reason": outcome["reason"], "pending_interaction": pending,
        "war_id": WAR_ID, "actual_combat_id": None,
        "final_snapshot_id": final["snapshot_id"], "final_public_revision": final["revision"]}


def partition_preparation_and_recorded_calls(calls, recording_start, recording_end,
                                             recorder_monotonic_origin, observation_started):
    """Classify exact calls by two clocks, rejecting any recorder-boundary overlap.

    The frozen CASE-C preparation did one snapshot and one capabilities query
    before FFmpeg launched. Its observed window began with a fresh snapshot
    after launch. Both phases remain provenance; only the latter is in video.
    """
    start = gb._utc(recording_start, "recorder start")
    end = gb._utc(recording_end, "recorder end")
    origin = gb._number(recorder_monotonic_origin, "recorder monotonic origin")
    observed_at = gb._utc(observation_started.get("at"), "observation start")
    observed_mono = gb._number(observation_started.get("monotonic"),
                               "observation start monotonic")
    require(start < observed_at < end and origin < observed_mono,
            "Observation start must follow recording launch in both clocks")
    preparation, recorded = [], []
    last_submitted_mono = float("-inf")
    for row in calls:
        sent_at = gb._utc(row["submitted_at"], "native call submission")
        received_at = gb._utc(row["received_at"], "native call receipt")
        sent_mono = gb._number(row["submitted_monotonic"], "native call submitted monotonic")
        received_mono = gb._number(row["received_monotonic"], "native call received monotonic")
        require(sent_at <= received_at and sent_mono <= received_mono and
                sent_mono > last_submitted_mono,
                "Native call timestamps or ordering differ")
        last_submitted_mono = sent_mono
        before_in_utc, before_in_mono = sent_at < start, sent_mono < origin
        require(before_in_utc == before_in_mono,
                "UTC and monotonic clocks disagree on the recorder boundary")
        if before_in_utc:
            require(received_at <= start and received_mono <= origin and not recorded,
                    "Preparation call crossed recorder launch or followed observed calls")
            preparation.append(row)
        else:
            require(start <= sent_at <= received_at <= end and
                    origin <= sent_mono <= received_mono,
                    "Observed call lies outside completed recorder interval")
            recorded.append(row)
    require(Counter(row["tool"] for row in preparation) ==
            {"ck3_take_snapshot": 1, "ck3_get_capabilities": 1},
            "Pre-record preparation must contain only one snapshot and one capabilities query")
    require(bool(recorded) and recorded[0]["tool"] == "ck3_take_snapshot" and
            recorded[0]["received_monotonic"] <= observed_mono and
            gb._utc(recorded[0]["received_at"], "first in-record snapshot") <= observed_at,
            "Observation start must bind a completed fresh in-record snapshot")
    first = recorded[0]["body"] or {}
    declared = observation_started.get("snapshot") or {}
    require(all(first.get(key) == declared.get(key) for key in
                ("snapshot_id", "revision", "date_raw", "paused")) and
            first.get("played_character") == declared.get("played_character"),
            "Observation start does not match the first in-record native snapshot")
    require(all(gb._utc(row["submitted_at"], "later call") >= observed_at and
                row["submitted_monotonic"] >= observed_mono for row in recorded[1:]),
            "An observed call was submitted before the declared observation start")
    return {"pre_record_call_count": len(preparation),
        "pre_record_snapshot_count": sum(row["tool"] == "ck3_take_snapshot" for row in preparation),
        "in_record_call_count": len(recorded),
        "in_record_snapshot_count": sum(row["tool"] == "ck3_take_snapshot" for row in recorded),
        "phase_by_request": {str(row["request_path"]): phase for phase, rows in
            (("pre-record-preparation", preparation), ("recorded-observation", recorded))
            for row in rows if "request_path" in row}}


def validate_passive_case(recording, case_dir, session_dir):
    case_dir, session_dir = Path(case_dir).resolve(), Path(session_dir).resolve()
    identity = wb._snapshot_identity(recording["state"])
    require(identity["actor"] == ACTOR, "Unexpected CASE-C actor")
    run_id, session_sources = wb._session_sources(session_dir, identity)
    require(run_id == "desktop-3fevhd2-1c74096080--vanilla--R0005",
            "This CASE-C producer binds only the original R0005 session")
    case_input = load(case_dir / "case-input.json")
    wb._same_snapshot(case_input.get("snapshot", {}), identity, "CASE-C checkpoint input")
    seed = gb._bound(case_input.get("seed"), "CASE-W day19 seed")
    gb._bound(case_input.get("seed_receipt"), "CASE-W end checkpoint receipt")
    case_checkpoint = binding(case_dir / "pre-contact.ck3")
    recorder_checkpoint = gb._bound(load(recording["root"] / "recording-precondition.json").get("checkpoint"),
                                    "recorder pre-contact checkpoint")
    require((seed["bytes"], seed["sha256"]) ==
            (case_checkpoint["bytes"], case_checkpoint["sha256"]) ==
            (recorder_checkpoint["bytes"], recorder_checkpoint["sha256"]),
            "CASE-C controller and recorder were not seeded by identical W day19 bytes")
    calls = wb._read_calls(case_dir, identity, session_dir)
    started = load(case_dir / "observation-started.json")
    outcome = load(case_dir / "contact-observation-result.json")
    for label, snapshot in (("observation start", started.get("snapshot", {})),
                            ("observation result", outcome.get("paused_snapshot", {}))):
        wb._same_snapshot(snapshot, identity, label)
    summary = validate_observation_semantics(recording["state"], calls, outcome, started)
    command = load(recording["root"] / "recording-command.json")
    phases = partition_preparation_and_recorded_calls(calls,
        recording["recording_started_at"], recording["recording_completed_at"],
        command.get("monotonic_origin"), started)
    require(gb._utc(started.get("at"), "observation start") >=
            gb._utc(recording["recording_started_at"], "recording start") and
            gb._utc(outcome.get("at"), "observation result") <=
            gb._utc(recording["recording_completed_at"], "recording completion"),
            "Observation times exceed the recorder wall-clock window")
    end_call = next(row for row in reversed(calls) if row["tool"] == "ck3_take_snapshot")
    war_call = next(row for row in calls if row["tool"] == "ck3_get_war_state")
    require(war_call["body"] == outcome["war_state"] and
            gb._utc(war_call["response_at"], "war state") >=
            gb._utc(end_call["response_at"], "paused snapshot"),
            "Final War4 readback does not follow the paused snapshot")
    require(load(recording["root"] / "recording-result.json").get("clean_span_review") == "pending",
            "Original recorder must not claim reviewed clean spans")
    sources = [*session_sources, *case_dir.rglob("*"),
        recording["root"] / "recording-result.json"]
    sources.extend(path for row in calls for path in
        (row["request_path"], row["response_path"], row["submitted_path"], row["received_path"]))
    return {"identity": {"live_run_id": run_id, **identity},
        "summary": {**summary, **{k:v for k,v in phases.items() if k != "phase_by_request"}},
        "calls": [{**{k:v for k,v in row.items() if k != "body"},
                   "phase": phases["phase_by_request"][str(row["request_path"])]} for row in calls],
        "sources": [path for path in sources if path.is_file()]}


def _review(review_path, recording):
    review = load(review_path)
    require(review.get("schema") == REVIEW_SCHEMA and
            review.get("reviewer", {}).get("kind") == "agent" and
            bool(review.get("reviewer", {}).get("id")),
            "Explicit actual CASE-C agent image review required")
    require(review.get("review_scope") == "endpoint-images-and-sampled-foreground" and
            all(review.get(key) is False for key in BOUNDARIES),
            "CASE-C review must retain every no-causality/no-combat/no-signoff boundary")
    native = review.get("native_readback", {})
    require(native.get("association") == "bounded-passive-wartime-not-frame-synchronized" and
            bool(native.get("notes")), "No exact native-query/video-frame association is allowed")
    require(re.fullmatch(r"[a-zA-Z0-9_-]+", str(review.get("span_id", ""))),
            "Stable span_id required")
    reviewed_at = gb._utc(review.get("reviewed_at_utc"), "actual image review")
    require(reviewed_at >= gb._utc(recording["recording_completed_at"], "recording end"),
            "Review predates completed recording")
    extraction = load(gb._bound(review.get("extraction"), "review extraction")["path"])
    require(extraction.get("schema") == gb.EXTRACTION_SCHEMA and
            extraction.get("status") == "pending-agent-image-review" and
            gb._bound(extraction.get("source_recording"), "extraction raw") == recording["raw"] and
            gb._bound(extraction.get("recording_result"), "extraction completion") ==
            binding(recording["root"] / "recording-result.json"),
            "Extraction does not bind this original completed recording")
    require(reviewed_at >= gb._utc(extraction.get("created_at_utc"), "extraction time"),
            "Review predates endpoint extraction")
    timing = load(gb._bound(extraction.get("actual_frame_probe"), "actual timing")["path"])
    require(timing.get("schema") == gb.FRAME_PROBE_SCHEMA and
            gb._bound(timing.get("source_recording"), "timing raw") == recording["raw"] and
            all(row.get("capture_media_compatible") is True and
                row.get("capture_media_timing_policy") == TIMING_POLICY for row in (timing, extraction)),
            "Actual PTS timing must match the exact recorded bytes and current policy")
    begin, end = extraction["begin_seconds"], extraction["end_seconds"]
    require(extraction.get("end_is_exclusive") is True and
            0 <= begin < end <= recording["duration_seconds"] and
            end <= timing["supported_end_seconds"], "Reviewed span exceeds actual PTS support")
    selected = [row for row in timing["frames"] if begin <= row["pts_seconds"] < end]
    require(len(selected) >= 2 and len(extraction.get("frames", [])) == 2 and
            len(review.get("frames", [])) == 2, "Two actual PTS endpoint images required")
    for phase, source, extracted, inspected in zip(("begin", "end"),
                                                  (selected[0], selected[-1]),
                                                  extraction["frames"], review["frames"]):
        require(extracted.get("phase") == inspected.get("phase") == phase and
                extracted.get("pts") == source["pts"] and
                extracted.get("decoded_index") == source["decoded_index"] and
                extracted.get("media_seconds") == source["pts_seconds"],
                "Inspected endpoint differs from an actual timestamped frame")
        require(gb._bound(extracted.get("image"), "extracted image") ==
                gb._bound(inspected.get("image"), "inspected image"),
                "Review image differs from extracted endpoint bytes")
        require(extracted.get("returncode") == 0 and bool(extracted.get("audit_files")),
                "Successful actual extraction audit required")
        for record in extracted["audit_files"]:
            gb._bound(record, "endpoint extraction audit")
        flags = inspected.get("observations", {})
        require(all(flags.get(key) is True for key in
                    ("gameplay_hud", "visible_war_map", "no_loading", "no_foreign_overlay")) and
                type(flags.get("paused_map")) is bool and bool(inspected.get("notes")),
                "Each endpoint needs an actual observed CK3 map, pause state and scene notes")
    return review, extraction


def package_passive_bundle(recording_dir, case_dir, session_dir, review_json, output,
                           recorder_script, operator_script):
    """Copy exact sources into a new adapter bundle only after real PTS review."""
    recording = completed_passive_recording(recording_dir)
    case = validate_passive_case(recording, case_dir, session_dir)
    review_path = Path(review_json).resolve()
    review, extraction = _review(review_path, recording)
    out = Path(output).resolve()
    require(not out.exists() and all(not out.is_relative_to(Path(root).resolve()) for root in
            (recording_dir, case_dir, session_dir)),
            "New bundle must not overwrite or nest within source attempts")
    require(Path(recorder_script).is_file() and Path(operator_script).is_file(),
            "Actual recorder and observation-controller implementations required")
    paths = [*recording["root"].rglob("*"), *case["sources"], review_path,
        Path(recorder_script).resolve(), Path(operator_script).resolve(),
        Path(__file__).resolve(), Path(wb.__file__).resolve(), Path(gb.__file__).resolve()]
    sources = {path.resolve(): binding(path) for path in paths if path.is_file()}
    queue = list(sources)
    for path in queue:
        if path.suffix.lower() != ".json":
            continue
        for record in gb._file_records(load(path)):
            exact = gb._bound(record, f"source binding in {path.name}")
            linked = Path(exact["path"]).resolve()
            if linked not in sources:
                sources[linked] = exact
                queue.append(linked)
    require(all(not out.is_relative_to(path) for path in sources),
            "Bundle destination overlaps a source file")
    out.mkdir(parents=True, exist_ok=False)
    try:
        copied, mapping = {}, []
        for original, identity in sources.items():
            relative = (Path("source-recording") / original.relative_to(recording["root"])) if (
                original.is_relative_to(recording["root"])) else (
                Path("source-evidence") / identity["sha256"] / original.name)
            destination = out / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with original.open("rb") as source, destination.open("xb") as target:
                    shutil.copyfileobj(source, target)
            preserved = binding(destination)
            require((preserved["bytes"], preserved["sha256"]) ==
                    (identity["bytes"], identity["sha256"]),
                    f"Preserved source differs: {original}")
            copied[original] = preserved
            mapping.append({"original": identity, "preserved": preserved})

        def relocated(path):
            return copied[Path(path).resolve()]

        calls = [{**{key:value for key,value in row.items() if not key.endswith("_path")},
                  **{key.removesuffix("_path"): relocated(value) for key,value in row.items()
                     if key.endswith("_path")},
                  "exact_media_pts": None, "query_semantics_reinterpreted": False}
                 for row in case["calls"]]
        summary = {"schema": PRODUCER, "scope": SCOPE, **BOUNDARIES,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_mapping": mapping, "identity": case["identity"],
            "native_state": {**case["summary"],
                "snapshot_before": relocated(recording["root"] / "snapshot-before.json"),
                "snapshot_after": relocated(next(row["response_path"] for row in reversed(case["calls"])
                    if row["tool"] == "ck3_take_snapshot")),
                "association": "bounded-passive-wartime-not-frame-synchronized"},
            "native_calls": calls,
            "foreground_sampling": recording["foreground"],
            "actual_agent_image_review": relocated(review_path),
            "actual_frame_probe": relocated(extraction["actual_frame_probe"]["path"]),
            "capture_media_timing_policy": TIMING_POLICY,
            "sampling_quality": extraction["sampling_quality"],
            "limitations": [
                "No actual CombatID or battle was observed; the 30-day window stopped on a pending character interaction.",
                "The observation controller submitted speed2, resume and pause only; earlier CASE-W player orders are not new CASE-C orders.",
                "Native call times and actual video PTS are different clocks; endpoint review does not synchronize them.",
                "The long raw recording includes a paused wait after active observation; only the reviewed PTS span receives clean-frame gates.",
                "Original capture-session RED remains a separate historical result.",
                "No continuous visual review, human 1x film signoff or approval is created."]}
        summary_path = out / "producer-evidence.json"
        write_new(summary_path, summary)
        span, frames = review["span_id"], []
        for row in extraction["frames"]:
            frame = {"schema_version":1, "result":"GREEN", "span":span,
                "phase":row["phase"], "producer":PRODUCER, "scope":SCOPE,
                "media_seconds":row["media_seconds"],
                "image":relocated(row["image"]["path"]),
                "review":relocated(review_path),
                "extraction":relocated(review["extraction"]["path"]),
                "producer_evidence":binding(summary_path),
                "preserved_sources":[value for path,value in copied.items()
                    if path != Path(recording["raw"]["path"])], **BOUNDARIES}
            gate = out / "cell/promo" / f"{span}-{row['phase']}-gate.json"
            write_new(gate, frame)
            frames.append({**frame, "gate":binding(gate)})
        raw = relocated(recording["raw"]["path"])
        timeline = {"schema":PRODUCER,
            "source_kind":"real CK3 gameplay HUD; bounded passive wartime observation",
            "exclude_ck3_loading":True, "raw_path":raw["path"],
            "raw_bytes":raw["bytes"], "raw_sha256":raw["sha256"],
            "marks":[
                {"label":"recording_started_after_gameplay_hud","seconds":0},
                {"label":f"{span}_clean_begin","seconds":extraction["begin_seconds"]},
                {"label":f"{span}_clean_end","seconds":extraction["end_seconds"]},
                {"label":"recording_stop_requested","seconds":recording["duration_seconds"]}],
            "clean_capture_complete":True, "missing_clean_spans":[],
            "clean_frame_gates":[{"span_id":span, "result":"GREEN",
                "begin_mark":f"{span}_clean_begin", "end_mark":f"{span}_clean_end", "frames":frames}],
            "producer":PRODUCER, "scope":SCOPE, **BOUNDARIES,
            "mark_semantics":{
                "recording_stop_requested":"Actual media end, not observation stop or wall-clock stop marker.",
                "clean_end":"Exclusive PTS-supported boundary; end image is last actual frame before it.",
                "native_calls":"Original wall and monotonic times live in producer evidence; no exact media PTS inferred."}}
        write_new(out / "cell/promo/capture-timeline.json", timeline)
        write_new(out / "report.json", {"schema_version":1, "result":"GREEN",
            "producer":PRODUCER, "scope":SCOPE, "original_attempt_modified":False,
            **BOUNDARIES,
            "cell":{"schema_version":1,"result":"GREEN", "producer":PRODUCER,
                "scope":SCOPE,"promo_capture":timeline}})
        indexed = [{**binding(path), "path":path.relative_to(out).as_posix()}
                   for path in sorted(out.rglob("*")) if path.is_file()]
        write_new(out / "evidence-index.json", {"schema_version":1,"result":"GREEN",
            "artifact_root":out.as_posix(),"producer":PRODUCER,"scope":SCOPE,"files":indexed})
        adapter = load_capture_bundle(out, required_span_ids=[span])
        receipt = {"schema":PRODUCER,"status":"adapter-validated-passive-wartime-evidence",
            "scope":SCOPE, **BOUNDARIES, "bundle_root":out.as_posix(),"span_id":span,
            "begin_seconds":adapter.clean_span(span).begin_seconds,
            "end_seconds":adapter.clean_span(span).end_seconds,
            "report":binding(out / "report.json"),
            "timeline":binding(out / "cell/promo/capture-timeline.json"),
            "evidence_index":binding(out / "evidence-index.json"),
            "raw":raw,"producer_evidence":binding(summary_path),
            "identity":case["identity"],"native_call_count":len(calls),
            "sample_count":case["summary"]["sample_count"]}
        write_new(out / "bundle-receipt.json", receipt)
        return receipt
    except Exception as exc:
        write_new(out / "failure.json", {"status":"failed-retained",
            "error_type":type(exc).__name__,"error":str(exc), **BOUNDARIES})
        raise
