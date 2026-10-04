"""Root-operated bounded advance through the already-running MCP queue.

Default is a reviewable plan only. --execute publishes requests to the existing
client; there is no attach, reconnect, speed change, event selection or save.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import uuid

import persistent_native_mcp_queue as queue
from native_request_cli import read_response, validate_args

SIMULATION = "ck3_set_profile_simulation_v1"
SNAPSHOT = "ck3_take_profile_native_snapshot_v1"
PAUSE = "ck3_pause_profile_simulation_v1"
TERMINAL = re.compile(rb"(?:LYD_NP_THREE_ROUNDS_PASS|LYD_NP_[A-Z0-9_]*(?:FAIL|REJECTED))(?![A-Z0-9_])")


class StopAdvance(Exception):
    pass


def body(view: dict) -> dict:
    response = view.get("response", {})
    sdk = view.get("sdk_result", {})
    if response.get("status") != "MCP_RESULT_RECORDED" or sdk.get("isError") is True:
        raise RuntimeError("MCP result failed: " + str(response.get("reason", response.get("status"))))
    result = sdk.get("structuredContent")
    if not isinstance(result, dict) or result.get("schema") != "ck3.native-profile-receipt.v1":
        raise RuntimeError("native structuredContent receipt missing; ACK is insufficient")
    return result


def make_request(request_id: str, name: str, arguments: dict, schemas: Path) -> dict:
    validate_args(name, arguments, schemas)
    value = {"schema": "ck3.lyd.mcp-request.v1", "request_id": request_id,
             "operation": "call_tool", "name": name, "arguments": arguments}
    return queue.validate_request(value)


def check_frame(frame: dict) -> dict:
    if (not isinstance(frame, dict) or frame.get("map_ready") is not True
            or type(frame.get("paused")) is not bool or type(frame.get("revision")) is not int
            or type(frame.get("date_raw")) is not int):
        raise RuntimeError("native map-ready snapshot unavailable")
    return frame


def run(args) -> int:
    if not 8 <= args.timeout <= 45:
        raise ValueError("--timeout must be 8..45 seconds, including the final pause wait")
    args.output = queue.inside(args.output)
    if args.output.exists():
        raise ValueError("choose a fresh output directory")
    args.output.mkdir(parents=True)
    args.queue, args.evidence = queue.inside(args.queue), queue.inside(args.evidence)
    tag = "advance-" + uuid.uuid4().hex[:16]
    resume = make_request(tag + "-000-resume", SIMULATION,
                          {"action": "resume", "expected_revision": args.start_revision}, args.schemas)
    pause = make_request(tag + "-999-pause", PAUSE, {}, args.schemas)
    make_request(tag + "-001-snapshot", SNAPSHOT, {}, args.schemas)
    queue.write_fresh(args.output / "resume.request.json", resume)
    queue.write_fresh(args.output / "pause.request.json", pause)
    plan = {"schema": "ck3.lyd.bounded-advance-plan.v1", "created_at_utc": queue.now(),
            "queue": str(args.queue), "evidence": str(args.evidence), "debug_log": str(args.log),
            "start_request_id": args.start_id, "start_revision": args.start_revision,
            "timeout_seconds": args.timeout, "advance_budget_seconds": args.timeout - 7,
            "resume_request": resume, "final_pause_request": pause,
            "terminal_markers": ["LYD_NP_THREE_ROUNDS_PASS", "any LYD_NP_ marker ending in FAIL or REJECTED"],
            "snapshot_while_running": True, "stop_on_active_event_or_pending_interaction": True,
            "uses_existing_client_only": True, "attach": False, "reconnect": False,
            "boundary": "helper controls a bounded native probe advance; terminal marker alone is not product acceptance"}
    queue.write_fresh(args.output / "plan.json", plan)
    if not args.execute:
        print(json.dumps({"status": "PLAN_ONLY", "plan": str(args.output / "plan.json"), "game_called": False}, indent=2))
        return 0

    started = time.monotonic()
    end = started + args.timeout
    advance_end = end - 7
    report = {"schema": "ck3.lyd.bounded-advance-result.v1", "started_at_utc": queue.now(),
              "requests": [], "responses": [], "stop_reason": None, "pause": "PAUSE_UNCONFIRMED"}
    log_position = 0
    tail = b""
    log_index = 0
    response_index = 0

    def publish(value: dict, filename: str) -> None:
        path = args.output / filename
        if not path.exists():
            queue.write_fresh(path, value)
        receipt = queue.enqueue(args.queue, path)
        report["requests"].append(receipt)
        with (args.output / "requests.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt) + "\n")

    def preserve_view(view: dict, request_id: str) -> None:
        nonlocal response_index
        response_index += 1
        prefix = f"{response_index:03d}-{request_id}"
        raw_path = Path(view["response_path"])
        (args.output / (prefix + ".response.json")).write_bytes(raw_path.read_bytes())
        sdk_name = view.get("response", {}).get("sdk_result")
        if sdk_name:
            (args.output / (prefix + ".sdk-result.json")).write_bytes((args.evidence / sdk_name).read_bytes())
        report["responses"].append({"request_id": request_id, "response_path": str(raw_path),
                                     "sha256": view["sha256"], "preserved_prefix": prefix})

    def watch_log() -> None:
        nonlocal log_position, tail, log_index
        if args.log.stat().st_size < log_position:
            raise RuntimeError("debug log truncated during this bounded attempt")
        with args.log.open("rb") as stream:
            stream.seek(log_position)
            raw = stream.read()
        if not raw:
            return
        log_index += 1
        (args.output / f"debug-{log_index:03d}-offset-{log_position}.bin").write_bytes(raw)
        log_position += len(raw)
        combined = tail + raw
        match = TERMINAL.search(combined)
        tail = combined[-128:]
        if match:
            report["terminal_marker"] = match.group().decode("ascii")
            raise StopAdvance(report["terminal_marker"])

    def await_result(request_id: str, deadline: float, *, watch: bool = True) -> dict:
        while time.monotonic() < deadline:
            if watch:
                watch_log()
            view = read_response(args.evidence, request_id)
            if "response" in view:
                preserve_view(view, request_id)
                return body(view)
            if (args.evidence / "session-closed.json").exists() or (args.evidence / "session-terminated.json").exists():
                raise RuntimeError("existing MCP session stopped; no reconnect")
            time.sleep(0.1)
        raise TimeoutError("bounded wait expired for " + request_id)

    try:
        if not (args.queue / "consumer-session.json").is_file() or not (args.evidence / "ready.json").is_file():
            raise RuntimeError("existing persistent client evidence absent")
        before_view = read_response(args.evidence, args.start_id)
        if "response" not in before_view:
            raise RuntimeError("explicit root start snapshot is not a completed response")
        preserve_view(before_view, args.start_id)
        before = body(before_view)
        if before.get("status") != "native_snapshot_verified":
            raise RuntimeError("start request must be an actual native snapshot")
        frame = check_frame(before.get("snapshot"))
        report["start_frame"] = {key: frame[key] for key in ("revision", "date_raw", "paused", "speed")}
        if frame["revision"] != args.start_revision or frame["paused"] is not True:
            raise RuntimeError("explicit start revision is not the paused saved native frame")
        if frame.get("active_event") or frame.get("pending_character_interaction"):
            raise StopAdvance("START_FRAME_HAS_PENDING_UI")
        baseline = args.log.read_bytes()
        (args.output / "debug-before.bin").write_bytes(baseline)
        log_position = len(baseline)
        report["debug_before"] = {"bytes": len(baseline), "sha256": hashlib.sha256(baseline).hexdigest()}
        publish(resume, "resume.request.json")
        result = await_result(resume["request_id"], advance_end)
        frame = check_frame(result.get("snapshot_after"))
        if result.get("status") != "native_gameplay_postcondition_verified" or frame["paused"] is not False:
            raise RuntimeError("native resume business postcondition is unverified")
        report["resume_verified"] = True
        index = 0
        while time.monotonic() < advance_end:
            watch_log()
            index += 1
            request = make_request(tag + f"-{index:03d}-snapshot", SNAPSHOT, {}, args.schemas)
            publish(request, f"snapshot-{index:03d}.request.json")
            result = await_result(request["request_id"], advance_end)
            if result.get("status") != "native_snapshot_verified":
                raise RuntimeError("running native snapshot unverified")
            frame = check_frame(result.get("snapshot"))
            report["last_running_frame"] = {key: frame[key] for key in ("revision", "date_raw", "paused", "speed")}
            if frame.get("active_event") or frame.get("pending_character_interaction"):
                raise StopAdvance("PENDING_NATIVE_EVENT_OR_INTERACTION")
            if frame["paused"] is True:
                raise StopAdvance("ENGINE_PAUSED")
            time.sleep(min(0.25, max(0, advance_end - time.monotonic())))
        report["stop_reason"] = "ADVANCE_WALL_LIMIT"
    except StopAdvance as error:
        report["stop_reason"] = str(error)
    except BaseException as error:
        report["stop_reason"] = "ERROR"
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        try:
            publish(pause, "pause.request.json")
            result = await_result(pause["request_id"], end, watch=False)
            frame = check_frame(result.get("snapshot_after"))
            if result.get("status") != "native_gameplay_postcondition_verified" or frame["paused"] is not True:
                raise RuntimeError("native pause business postcondition is unverified")
            report["pause"] = "NATIVE_PAUSED_VERIFIED"
            report["final_frame"] = {key: frame[key] for key in ("revision", "date_raw", "paused", "speed")}
        except BaseException as error:
            report["pause_error"] = f"{type(error).__name__}: {error}"
        if args.log.is_file():
            final_log = args.log.read_bytes()
            (args.output / "debug-after.bin").write_bytes(final_log)
            report["debug_after"] = {"bytes": len(final_log), "sha256": hashlib.sha256(final_log).hexdigest()}
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["finished_at_utc"] = queue.now()
        report["status"] = "BOUNDED_ADVANCE_STOPPED_PAUSED" if report["pause"] == "NATIVE_PAUSED_VERIFIED" else "PAUSE_UNCONFIRMED"
        report["product_acceptance"] = "NOT_CLAIMED"
        queue.write_fresh(args.output / "report.json", report)
        print(json.dumps({key: report.get(key) for key in ("status", "stop_reason", "pause", "terminal_marker", "error", "elapsed_seconds", "final_frame")}, indent=2), flush=True)
    return 2 if report["pause"] != "NATIVE_PAUSED_VERIFIED" else (1 if report.get("error") else 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--start-id", required=True, help="root's completed fresh native snapshot request ID")
    parser.add_argument("--start-revision", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="root explicitly dispatches this reviewed plan")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
