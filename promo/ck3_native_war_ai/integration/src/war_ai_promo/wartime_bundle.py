"""Preserve a bounded wartime observation without changing the paused-map contract.

Only reads completed recorder/case/session evidence.  No CK3, capture, mutation,
OCR, inferred approval, or reconstruction of missing native observations occurs.
The CASE-W controller's existing filenames are the documented producer input.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

from xar_promo.adapters.ck3 import load_capture_bundle

from .common import binding, load, write_new
from . import gameplay_bundle as gb
from .capture_timing import TIMING_POLICY


PRODUCER = "war-ai-promo.bounded-wartime-observation.v1"
REVIEW_SCHEMA = "ck3-war-ai.wartime-frame-review.v1"
SCOPE = "bounded wartime observation after explicit operator declaration, raise and move"
BOUNDARIES = {**gb.BOUNDARIES, "natural_ai_declaration_proven": False,
    "complete_target_score_causality_proven": False,
    "narrow_query_ready_conflicts_resolved": False}
EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
ACTION_TOOLS = {"declaration": "ck3_declare_war", "raise": "ck3_raise_troops_default",
    "move": "ck3_move_army"}
require = gb.require


def _pointer(value, pointer):
    require(isinstance(pointer, str) and (not pointer or pointer.startswith("/")),
            "Snapshot pointer must be an explicit JSON pointer")
    for part in pointer.split("/")[1:] if pointer else ():
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def _bridge_identity(diagnostics):
    hello = diagnostics.get("hello", {})
    require(hello.get("ck3_build_match") is True and
            hello.get("expected_ck3_version") == "1.19.0.6" and
            str(hello.get("expected_ck3_sha256", "")).lower() == EXE_SHA256,
            "Exact CK3 1.19.0.6 bridge identity required")
    pid, generation = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation")
    require(type(pid) is int and pid > 0 and type(generation) is int and generation > 0
            and hello.get("pid") == pid and hello.get("connection_generation") == generation
            and bool(diagnostics.get("pipe_name")), "Bridge PID/generation/pipe identity incomplete")
    return {"pid": pid, "connection_generation": generation,
        "session_generation": hello.get("session_generation"),
        "pipe_name": diagnostics["pipe_name"], "exe_sha256": EXE_SHA256}


def _snapshot_identity(snapshot):
    require(snapshot.get("source") == "injected-dll-named-pipe" and snapshot.get("map_ready") is True,
            "Native map snapshot required")
    actor = (snapshot.get("played_character") or {}).get("character_id")
    require(type(actor) is int and actor > 0 and snapshot.get("episode_character_id") == actor
            and isinstance(snapshot.get("episode_run_id"), str) and bool(snapshot["episode_run_id"])
            and snapshot.get("episode_identity_pending") is False, "Native episode/actor identity incomplete")
    lifecycle = snapshot.get("succession_lifecycle", {})
    require(lifecycle.get("xar_enabled") == "xar_off" and
            lifecycle.get("source") == "pure-vanilla-enabled-mods-empty",
            "Independent pure-vanilla profile evidence required")
    require(type(snapshot.get("date_raw")) is int and snapshot["date_raw"] > 0,
            "Native date is missing")
    return {**_bridge_identity(snapshot.get("diagnostics", {})), "actor": actor,
        "episode_run_id": snapshot["episode_run_id"],
        "environment_sha256": lifecycle.get("environment_sha256")}


def _initial_snapshot(path, actor, date):
    # The real recorder stores {at, body}; it is a recorder projection, not an
    # MCP CALL_COMPLETED wrapper.  Preserve it as-is, with that narrower label.
    wrapper = load(path)
    gb._utc(wrapper.get("at"), "initial recorder snapshot timestamp")
    if "result" in wrapper:
        require(wrapper["result"] == "CALL_COMPLETED", "Initial snapshot call failed")
    snapshot = wrapper.get("body")
    require(isinstance(snapshot, dict), "Initial recorder snapshot body missing")
    identity = _snapshot_identity(snapshot)
    require(snapshot.get("paused") is True and identity["actor"] == actor and snapshot["date_raw"] == date,
            "Initial paused actor/date differs from recording precondition")
    return snapshot


def completed_wartime_recording(recording_dir):
    return gb.completed_recording(recording_dir, snapshot_reader=_initial_snapshot)


def extract_wartime_frames(recording_dir, output, begin_seconds, end_seconds,
                           ffmpeg="ffmpeg", *, frame_probe=None, ffprobe="ffprobe"):
    return gb.extract_frames(recording_dir, output, begin_seconds, end_seconds, ffmpeg,
        frame_probe=frame_probe, ffprobe=ffprobe, recording_validator=completed_wartime_recording)


def _same_snapshot(snapshot, identity, label):
    require(_snapshot_identity(snapshot) == identity, f"{label}: run/bridge/episode/actor changed")
    return snapshot


def _snapshots(value):
    if isinstance(value, dict):
        if value.get("source") == "injected-dll-named-pipe" and "date_raw" in value:
            yield value
        for child in value.values():
            yield from _snapshots(child)
    elif isinstance(value, list):
        for child in value:
            yield from _snapshots(child)


def _session_sources(session_dir, identity):
    root = Path(session_dir).resolve()
    names = ("live-run-identity.json", "preflight.json", "command.json", "session.jsonl")
    require(all((root / name).is_file() for name in names), "Session run/preflight/command/log evidence missing")
    receipt = load(root / names[0])
    rows = receipt.get("identities", [])
    require(receipt.get("schema") == "xar.ck3-live-run-receipt.v1" and len(rows) == 1
            and rows[0].get("mod_key") == "vanilla" and bool(rows[0].get("run_id")),
            "One explicit vanilla live-run identity required")
    preflight = load(root / "preflight.json")
    require(preflight.get("pipe_name") == identity["pipe_name"] and
            str(preflight.get("game", {}).get("sha256", "")).lower() == EXE_SHA256,
            "Session preflight pipe/build differs")
    command = load(root / "command.json").get("argv", [])
    require("--output-dir" in command and
            Path(command[command.index("--output-dir") + 1]).resolve() == root and
            "--pipe-name" in command and command[command.index("--pipe-name") + 1] == identity["pipe_name"],
            "Session command does not bind this session directory and pipe")
    events = [json.loads(line) for line in (root / "session.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    ready = [row for row in events if row.get("type") == "native_session_ready"]
    require(len(ready) == 1 and ready[0].get("pid") == identity["pid"]
            and ready[0].get("pipe") == identity["pipe_name"], "Session ready PID/pipe differs")
    return rows[0]["run_id"], [root / name for name in names]


def _read_calls(case_dir, identity, session_dir):
    calls = []
    for submitted_path in sorted(case_dir.glob("*.submitted.json")):
        submitted = load(submitted_path)
        received_path = submitted_path.with_name(submitted_path.name.removesuffix(".submitted.json") + ".received.json")
        received = load(received_path)
        response_record = gb._bound(received.get("response"), "case response receipt")
        response = load(response_record["path"])
        request_record = gb._bound(response.get("request"), "native response request")
        request = load(request_record["path"])
        require(Path(submitted.get("request", "")).resolve() == Path(request_record["path"]),
                "Submitted request differs from exact native receipt")
        require(Path(request_record["path"]).parent == session_dir / "recovery-requests" and
                Path(response_record["path"]).parent == session_dir / "recovery-requests-responses",
                "Case call belongs to a different owning session")
        require(request.get("action") == "mcp" and request.get("tool") == submitted.get("tool")
                and request.get("arguments") == submitted.get("arguments"), "Submitted native arguments differ")
        bridge = _bridge_identity(response.get("driver_state", {}))
        require(bridge == {key: identity[key] for key in bridge},
                "Native call belongs to a different bridge identity")
        sent_at = gb._utc(submitted.get("at"), "call submitted")
        received_at = gb._utc(received.get("at"), "call received")
        at = gb._utc(response.get("at"), "native response")
        sent_mono = gb._number(submitted.get("monotonic"), "call submitted monotonic")
        received_mono = gb._number(received.get("monotonic"), "call received monotonic")
        require(sent_at <= at <= received_at and sent_mono <= received_mono, "Native call timestamps out of order")
        for snapshot in _snapshots(response.get("body")):
            _same_snapshot(snapshot, identity, "native call snapshot")
        calls.append({"tool": request["tool"], "arguments": request["arguments"],
            "submitted_at": submitted["at"], "received_at": received["at"],
            "response_at": response["at"], "submitted_monotonic": sent_mono,
            "received_monotonic": received_mono, "wrapper_result": response.get("result"),
            "native_status": response.get("body", {}).get("status"),
            "body": response.get("body"), "submitted_path": submitted_path,
            "received_path": received_path, "response_path": Path(response_record["path"]),
            "request_path": Path(request_record["path"])})
    require(bool(calls), "No exact submitted/received native calls supplied")
    return calls


def validate_wartime_case(recording, case_dir, session_dir, snapshot_after, snapshot_pointer="/body"):
    """Read-only native evidence validation; does not review or mark footage GREEN."""
    case_dir, session_dir, after_path = (Path(p).resolve() for p in (case_dir, session_dir, snapshot_after))
    identity = _snapshot_identity(recording["state"])
    run_id, session_sources = _session_sources(session_dir, identity)
    after_wrapper = load(after_path)
    require(after_wrapper.get("result") == "CALL_COMPLETED", "Final endpoint must be a completed native snapshot receipt")
    after = _same_snapshot(_pointer(after_wrapper, snapshot_pointer), identity, "final snapshot")
    require(after.get("paused") is True and after["date_raw"] > recording["date_raw"],
            "Wartime observation requires paused endpoints with an increased final date")
    require(gb._utc(after_wrapper.get("at"), "final snapshot") >=
            gb._utc(recording["recording_completed_at"], "recorder completed"),
            "Final endpoint readback must follow completed recording")
    for path in case_dir.glob("*.json"):
        for snapshot in _snapshots(load(path)):
            _same_snapshot(snapshot, identity, path.name)
    calls = _read_calls(case_dir, identity, session_dir)
    command = load(recording["root"] / "recording-command.json")
    origin = gb._number(command.get("monotonic_origin"), "recorder monotonic origin")
    actions = []
    for kind, tool in ACTION_TOOLS.items():
        matched = [call for call in calls if call["tool"] == tool]
        require(len(matched) == 1, f"Exactly one explicit operator {kind} call required")
        call = matched[0]
        intent_path, result_path = case_dir / f"{kind}-intent.json", case_dir / f"{kind}-result.json"
        intent, result = load(intent_path), load(result_path)
        before = _same_snapshot(intent.get("precondition", {}), identity, f"{kind} before")
        post = _same_snapshot(result.get("snapshot", {}), identity, f"{kind} after")
        body = call["body"] or {}
        require(call["wrapper_result"] == "CALL_COMPLETED" and body.get("accepted") is True
                and result.get("response") == body, f"{kind}: successful exact native response missing")
        require(before.get("paused") is True and post.get("paused") is True and
                before["date_raw"] == post["date_raw"] and
                call["arguments"].get("expected_revision") == before.get("revision"),
                f"{kind}: paused same-date expected revision binding differs")
        intent_mono = gb._number(intent.get("monotonic"), f"{kind} intent monotonic")
        require(origin <= intent_mono <= call["submitted_monotonic"] and
                gb._utc(intent.get("at"), f"{kind} intent") <= gb._utc(call["submitted_at"], "submission"),
                f"{kind}: action intent does not precede submission within recording")
        require(gb._utc(call["received_at"], "action completion") <=
                gb._utc(recording["recording_completed_at"], "recording completion"),
                f"{kind}: action completed after recording")
        war_action = body.get("war_action", {})
        if kind == "declaration":
            new_wars = [war for war in post.get("active_wars", [])
                if war.get("war_id") not in {war.get("war_id") for war in before.get("active_wars", [])}]
            require(war_action.get("status") == "war_started" and len(new_wars) == 1
                    and war_action.get("declaration_id") == call["arguments"].get("declaration_id")
                    and new_wars[0].get("primary_opponent_character_id") == war_action.get("target_character_id"),
                    "Declaration requires a new matching war in the subsequent snapshot")
            war_id = new_wars[0]["war_id"]
        elif kind == "raise":
            ids = war_action.get("raised_army_ids", [])
            owned = {army.get("army_id") for army in post.get("player_armies", [])
                     if army.get("owner_character_id") == identity["actor"]}
            previous = {army.get("army_id") for army in before.get("player_armies", [])}
            require(war_action.get("status") == "raised" and bool(ids)
                    and set(ids) <= owned and set(ids).isdisjoint(previous),
                    "Raise requires new owned armies in the subsequent snapshot")
        else:
            army_id, target = call["arguments"].get("army_id"), call["arguments"].get("target_province_id")
            army = next((row for row in post.get("player_armies", []) if row.get("army_id") == army_id), {})
            require(war_action.get("status") == "moving" and war_action.get("army_id") == army_id
                    and army.get("owner_character_id") == identity["actor"]
                    and army.get("move_target_province_id") == target and bool(army.get("route_province_ids")),
                    "Move requires a matching owned army target and committed route in its subsequent snapshot")
        actions.append({"kind": kind, "operator_initiated": True, "intent": binding(intent_path),
            "result": binding(result_path), "request": binding(call["request_path"]),
            "native_response": binding(call["response_path"]),
            "intent_at": intent["at"], "intent_monotonic": intent_mono,
            "wall_offset_from_recorder_launch_seconds": intent_mono - origin,
            "exact_media_pts": None, "temporal_relation": "wall-clock launch association only",
            "postcondition_date_raw": post["date_raw"]})
    advances = []
    previous_date = recording["date_raw"]
    for path in sorted(case_dir.glob("advance-*.json")):
        row = load(path)
        start = _same_snapshot(row.get("start", {}), identity, f"{path.name} start")
        end = _same_snapshot(row.get("end", {}), identity, f"{path.name} end")
        require(start.get("paused") is True and end.get("paused") is True and
                start["date_raw"] == previous_date and start["date_raw"] < end["date_raw"] <= after["date_raw"],
                "Advance records must be ordered, contiguous, positive, paused bounded slices")
        rows = row.get("observations", [])
        require(bool(rows) and any(item.get("paused") is False for item in rows),
                "Advance has no actual unpaused native observation")
        dates = [start["date_raw"], *(item.get("date_raw") for item in rows), end["date_raw"]]
        require(all(type(date) is int for date in dates) and all(a <= b for a, b in zip(dates, dates[1:])),
                "Advance observations contain a date reversal")
        require(all(any(war.get("war_id") == war_id for war in point.get("active_wars", []))
                    for point in (start, end)), "Observed war identity changed during time slice")
        at = gb._utc(row.get("at"), "advance receipt")
        require(gb._utc(recording["recording_started_at"], "recording start") <= at <=
                gb._utc(recording["recording_completed_at"], "recording end"), "Advance lies outside recording wall-clock window")
        advances.append({"evidence": binding(path), "recorded_at": row["at"],
            "start_date_raw": start["date_raw"], "end_date_raw": end["date_raw"],
            "requested_days": row.get("requested_days"), "observed_raw_date_delta": end["date_raw"] - start["date_raw"],
            "observation_count": len(rows), "exact_media_pts": None})
        previous_date = end["date_raw"]
    require(bool(advances) and previous_date == after["date_raw"], "Advance records do not cover final date")
    # Check the end native history as well as the submitted call files.  An
    # execute_step alias must not conceal an additional order of these kinds.
    old_indices = {row.get("index") for row in recording["state"].get("native_command_history", [])}
    history = [row for row in after.get("native_command_history", []) if row.get("index") not in old_indices]
    for prefix in ("declare-war-", "raise-troops-default", "move-army-"):
        require(sum(str(row.get("command", "")).startswith(prefix) for row in history) == 1,
                f"Final native command history must contain exactly one {prefix} operator order")
    sources = [*session_sources, after_path, *case_dir.rglob("*")]
    sources.extend(path for call in calls for path in
        (call["request_path"], call["response_path"], call["submitted_path"], call["received_path"]))
    return {"identity": {"live_run_id": run_id, **identity}, "snapshot_after": binding(after_path),
        "snapshot_pointer": snapshot_pointer, "start_date_raw": recording["date_raw"],
        "end_date_raw": after["date_raw"], "war_id": war_id, "actions": actions, "advances": advances,
        "calls": [{key: value for key, value in call.items() if key != "body"} for call in calls],
        "sources": [path for path in sources if path.is_file()]}


def _review(review_path, recording):
    """Validate independent dynamic review; never use the same-date paused review."""
    review = load(review_path)
    require(review.get("schema") == REVIEW_SCHEMA, "Wartime review schema required")
    require(review.get("reviewer", {}).get("kind") == "agent" and bool(review.get("reviewer", {}).get("id")),
            "Explicit actual agent image reviewer required")
    require(review.get("review_scope") == "endpoint-images-and-sampled-foreground" and
            all(review.get(key) is False for key in BOUNDARIES), "Wartime review boundaries must remain explicit")
    native = review.get("native_readback", {})
    require(native.get("association") == "bounded-wartime-not-frame-synchronized" and bool(native.get("notes")),
            "Wartime review must retain the unsynchronized native-readback boundary")
    require(re.fullmatch(r"[a-zA-Z0-9_-]+", str(review.get("span_id", ""))), "Stable span_id required")
    reviewed_at = gb._utc(review.get("reviewed_at_utc"), "actual image review")
    require(reviewed_at >= gb._utc(recording["recording_completed_at"], "recording end"), "Review predates recording end")
    extraction = load(gb._bound(review.get("extraction"), "review extraction")["path"])
    require(extraction.get("schema") == gb.EXTRACTION_SCHEMA and
            extraction.get("status") == "pending-agent-image-review" and
            gb._bound(extraction.get("source_recording"), "extraction raw") == recording["raw"] and
            gb._bound(extraction.get("recording_result"), "extraction completion") ==
            binding(recording["root"] / "recording-result.json"), "Extraction does not bind this completed recording")
    require(reviewed_at >= gb._utc(extraction.get("created_at_utc"), "extraction time"), "Review predates extraction")
    timing = load(gb._bound(extraction.get("actual_frame_probe"), "extraction timing")["path"])
    require(timing.get("schema") == gb.FRAME_PROBE_SCHEMA and
            gb._bound(timing.get("source_recording"), "timing raw") == recording["raw"] and
            all(row.get("capture_media_compatible") is True and row.get("capture_media_timing_policy") == TIMING_POLICY
                for row in (timing, extraction)), "Exact actual-PTS timing and current policy required")
    begin, end = extraction["begin_seconds"], extraction["end_seconds"]
    require(extraction.get("end_is_exclusive") is True and 0 <= begin < end <= recording["duration_seconds"]
            and end <= timing["supported_end_seconds"], "Review span exceeds actual PTS support")
    selected = [row for row in timing["frames"] if begin <= row["pts_seconds"] < end]
    require(len(selected) >= 2 and len(extraction.get("frames", [])) == 2 and len(review.get("frames", [])) == 2,
            "Two actual PTS endpoint images and observations required")
    for phase, source, extracted, inspected in zip(("begin", "end"), (selected[0], selected[-1]),
                                                   extraction["frames"], review["frames"]):
        require(extracted.get("phase") == inspected.get("phase") == phase and
                extracted.get("pts") == source["pts"] and extracted.get("decoded_index") == source["decoded_index"]
                and extracted.get("media_seconds") == source["pts_seconds"], "Endpoint PTS/phase mismatch")
        require(gb._bound(inspected.get("image"), "review image") == gb._bound(extracted.get("image"), "extracted image"),
                "Review image differs from extracted endpoint")
        require(extracted.get("returncode") == 0 and bool(extracted.get("audit_files")), "Actual extraction audit required")
        for record in extracted["audit_files"]:
            gb._bound(record, "extraction audit")
        require(all(inspected.get("observations", {}).get(key) is True for key in
                    ("gameplay_hud", "paused_map", "no_loading", "no_foreign_overlay")) and bool(inspected.get("notes")),
                "Actual paused HUD endpoint observation and notes required")
    return review, extraction


def package_wartime_bundle(recording_dir, case_dir, session_dir, snapshot_after, review_json,
                            output, recorder_script, operator_script, *, snapshot_pointer="/body"):
    """Copy exact evidence and produce an adapter-compatible bounded-observation bundle."""
    recording = completed_wartime_recording(recording_dir)
    case = validate_wartime_case(recording, case_dir, session_dir, snapshot_after, snapshot_pointer)
    review_path = Path(review_json).resolve()
    review, extraction = _review(review_path, recording)
    out = Path(output).resolve()
    require(not out.exists(), "Bundle destination exists; preserve it and use a new attempt")
    require(all(not out.is_relative_to(Path(root).resolve()) for root in (recording_dir, case_dir, session_dir)),
            "New bundle must be outside every original source attempt")
    require(Path(recorder_script).is_file() and Path(operator_script).is_file(),
            "Actual recorder and case-controller implementation files are required")
    paths = [*recording["root"].rglob("*"), *case["sources"], review_path,
        Path(recorder_script).resolve(), Path(operator_script).resolve(), Path(__file__).resolve(), Path(gb.__file__).resolve()]
    sources = {path.resolve(): binding(path) for path in paths if path.is_file()}
    queue = list(sources)
    for path in queue:
        if path.suffix.lower() != ".json":
            continue
        for record in gb._file_records(load(path)):
            actual = gb._bound(record, f"exact source reference in {path.name}")
            linked = Path(actual["path"]).resolve()
            if linked not in sources:
                sources[linked] = actual
                queue.append(linked)
    out.mkdir(parents=True, exist_ok=False)
    try:
        copied, mapping = {}, []
        for original, identity in sources.items():
            relative = (Path("source-recording") / original.relative_to(recording["root"])) if original.is_relative_to(recording["root"]) else (
                Path("source-evidence") / identity["sha256"] / original.name)
            destination = out / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with original.open("rb") as source, destination.open("xb") as target:
                    shutil.copyfileobj(source, target)
            preserved = binding(destination)
            require((preserved["bytes"], preserved["sha256"]) == (identity["bytes"], identity["sha256"]),
                    f"Source changed while preserving {original}")
            copied[original] = preserved
            mapping.append({"original": identity, "preserved": preserved})
        def relocated(path):
            return copied[Path(path).resolve()]
        call_rows = []
        for row in case["calls"]:
            call_rows.append({**{key: value for key, value in row.items() if not key.endswith("_path")},
                **{key.removesuffix("_path"): relocated(value) for key, value in row.items() if key.endswith("_path")},
                "exact_media_pts": None, "query_semantics_reinterpreted": False})
        summary = {"schema": PRODUCER, "scope": SCOPE, **BOUNDARIES,
            "created_at_utc": datetime.now(timezone.utc).isoformat(), "source_mapping": mapping,
            "identity": case["identity"], "war_id": case["war_id"],
            "native_state": {"start_date_raw": case["start_date_raw"], "end_date_raw": case["end_date_raw"],
                "paused_at_readback_endpoints": True, "snapshot_before": relocated(recording["root"] / "snapshot-before.json"),
                "snapshot_after": relocated(snapshot_after), "snapshot_after_pointer": snapshot_pointer,
                "association": "bounded-wartime-not-frame-synchronized"},
            "operator_marks": [{**row, **{key: relocated(row[key]["path"]) for key in
                ("intent", "result", "request", "native_response")}} for row in case["actions"]],
            "bounded_advances": [{**row, "evidence": relocated(row["evidence"]["path"])} for row in case["advances"]],
            "native_calls": call_rows,
            "foreground_sampling": recording["foreground"], "actual_agent_image_review": relocated(review_path),
            "actual_frame_probe": relocated(extraction["actual_frame_probe"]["path"]),
            "capture_media_timing_policy": TIMING_POLICY, "sampling_quality": extraction["sampling_quality"],
            "limitations": ["Endpoint images and foreground samples do not prove every intervening frame.",
                "Operator declaration/raise/move are explicit. NPC responses are observed states, not a complete score or cause trace.",
                "Native timestamps and video PTS are separate clocks; no same-frame mapping is inferred.",
                "Unavailable and conflicting narrow query fields remain as returned; capture GREEN does not resolve them.",
                "The session's earlier RED evidence remains RED; this independent completed recording does not rewrite it.",
                "No human 1x full-film signoff or approval is created."]}
        summary_path = out / "producer-evidence.json"
        write_new(summary_path, summary)
        span, frames = review["span_id"], []
        for row in extraction["frames"]:
            frame = {"schema_version": 1, "result": "GREEN", "span": span, "phase": row["phase"],
                "producer": PRODUCER, "scope": SCOPE, "media_seconds": row["media_seconds"],
                "image": relocated(row["image"]["path"]), "review": relocated(review_path),
                "extraction": relocated(review["extraction"]["path"]), "producer_evidence": binding(summary_path),
                "preserved_sources": [value for path, value in copied.items() if path != Path(recording["raw"]["path"])],
                **BOUNDARIES}
            gate = out / "cell/promo" / f"{span}-{row['phase']}-gate.json"
            write_new(gate, frame)
            frames.append({**frame, "gate": binding(gate)})
        raw = relocated(recording["raw"]["path"])
        timeline = {"schema": PRODUCER, "source_kind": "real CK3 gameplay HUD; bounded wartime observation",
            "exclude_ck3_loading": True, "raw_path": raw["path"], "raw_bytes": raw["bytes"], "raw_sha256": raw["sha256"],
            "marks": [{"label": "recording_started_after_gameplay_hud", "seconds": 0},
                {"label": f"{span}_clean_begin", "seconds": extraction["begin_seconds"]},
                {"label": f"{span}_clean_end", "seconds": extraction["end_seconds"]},
                {"label": "recording_stop_requested", "seconds": recording["duration_seconds"]}],
            "clean_capture_complete": True, "missing_clean_spans": [],
            "clean_frame_gates": [{"span_id": span, "result": "GREEN", "begin_mark": f"{span}_clean_begin",
                "end_mark": f"{span}_clean_end", "frames": frames}],
            "producer": PRODUCER, "scope": SCOPE, **BOUNDARIES,
            "mark_semantics": {"recording_stop_requested": "Actual probed media end, not the wall-clock stop-marker timestamp.",
                "clean_end": "Exclusive PTS-supported boundary; end image is the last existing frame before it.",
                "operator_marks": "Stored separately in producer evidence as original timestamps; not inserted as exact media marks."}}
        write_new(out / "cell/promo/capture-timeline.json", timeline)
        write_new(out / "report.json", {"schema_version": 1, "result": "GREEN", "producer": PRODUCER,
            "scope": SCOPE, "original_attempt_modified": False, **BOUNDARIES,
            "cell": {"schema_version": 1, "result": "GREEN", "producer": PRODUCER, "scope": SCOPE, "promo_capture": timeline}})
        indexed = [{**binding(path), "path": path.relative_to(out).as_posix()}
                   for path in sorted(out.rglob("*")) if path.is_file()]
        write_new(out / "evidence-index.json", {"schema_version": 1, "result": "GREEN",
            "artifact_root": out.as_posix(), "producer": PRODUCER, "scope": SCOPE, "files": indexed})
        bundle = load_capture_bundle(out, required_span_ids=[span])
        receipt = {"schema": PRODUCER, "status": "adapter-validated-bounded-wartime-evidence", "scope": SCOPE,
            **BOUNDARIES, "bundle_root": out.as_posix(), "span_id": span,
            "begin_seconds": bundle.clean_span(span).begin_seconds, "end_seconds": bundle.clean_span(span).end_seconds,
            "report": binding(out / "report.json"), "timeline": binding(out / "cell/promo/capture-timeline.json"),
            "evidence_index": binding(out / "evidence-index.json"), "raw": raw,
            "producer_evidence": binding(summary_path), "identity": case["identity"],
            "native_call_count": len(call_rows), "advance_count": len(case["advances"])}
        write_new(out / "bundle-receipt.json", receipt)
        return receipt
    except Exception as exc:
        write_new(out / "failure.json", {"status": "failed-retained", "error": str(exc), **BOUNDARIES})
        raise
