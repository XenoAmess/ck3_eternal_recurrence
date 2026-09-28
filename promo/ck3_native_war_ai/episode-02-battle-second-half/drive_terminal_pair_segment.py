"""One-day, recorder-bound E2-09 observer/advance for a new paired terminal run.

Observe and advance are separate invocations. Each advance requires a same-day
native response and a visible screenshot mark in the active 600s raw recorder.
No request is submitted when the recorder has less than one request timeout
plus 30 seconds remaining. This script never starts CK3 or records video.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

import psutil


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(path: Path) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {"path": str(path.resolve()), "bytes": size,
            "sha256": digest.hexdigest().upper()}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def recorder_gate(workdir: Path, output: Path, frozen: dict,
                  request_seconds: int) -> dict:
    require(workdir.parent.resolve() == output.parent.resolve(),
            "recorder is not a child of this live attempt")
    intent_path = workdir / "recorder-intent.json"
    start_path = workdir / "recorder-start.json"
    require(intent_path.is_file() and start_path.is_file() and
            not (workdir / "recorder-end.json").exists(), "recorder is not active")
    intent, start = read(intent_path), read(start_path)
    require(Path(intent.get("session_output", "")).resolve() == output.resolve() and
            intent.get("max_seconds") == 600 and
            (intent.get("source_save") or {}).get("sha256") ==
            frozen["checkpoint_save"]["sha256"] and
            (intent.get("source_receipt") or {}).get("sha256") ==
            frozen["checkpoint_receipt"]["sha256"],
            "recorder source/session identity mismatch")
    raw = Path(intent.get("raw_path", ""))
    require(raw.is_file() and raw.stat().st_size > 0 and
            raw.parent.parent.resolve() == workdir.resolve(),
            "recorder raw file has not started in selected workdir")
    require(intent.get("argv") == start.get("argv") and
            Path(intent["argv"][-1]).resolve() == raw.resolve(),
            "recorder start argv does not bind selected raw")
    pid = start.get("pid")
    require(type(pid) is int and type(start.get("monotonic_ns")) is int,
            "recorder start identity incomplete")
    try:
        process = psutil.Process(pid)
        require(process.is_running() and process.name().lower() == "ffmpeg.exe",
                "bound FFmpeg process is not running")
        require(Path(process.cmdline()[-1]).resolve() == raw.resolve(),
                "bound FFmpeg PID command line differs from raw")
    except psutil.NoSuchProcess as exc:
        raise ValueError("bound FFmpeg process has exited") from exc
    remaining = 600 - (time.monotonic_ns() - start["monotonic_ns"]) / 1e9
    require(remaining > request_seconds + 30,
            f"recorder boundary too close: {remaining:.1f}s remain")
    return {"intent": identity(intent_path), "start": identity(start_path),
            "raw_path": str(raw.resolve()), "recorder_pid": pid,
            "remaining_seconds_at_gate": round(remaining, 3)}


def call(output: Path, label: str, tool: str, arguments: dict,
         workdir: Path, frozen: dict, timeout: int) -> tuple[dict, dict, dict]:
    gate = recorder_gate(workdir, output, frozen, timeout)
    requests = output / "interactive-requests"
    responses = output / "interactive-requests-responses"
    require(requests.is_dir() and responses.is_dir(), "hot service not ready")
    request = requests / f"{label}.json"
    response = responses / f"{label}.json"
    pending = output / f"{label}.pending"
    require(not request.exists() and not response.exists() and not pending.exists(),
            f"native request label already used: {label}")
    write_new(pending, {"action": "mcp", "tool": tool, "arguments": arguments})
    os.replace(pending, request)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if response.exists():
            try:
                value = read(response)
            except json.JSONDecodeError:
                time.sleep(0.2)
                continue
            receipt = identity(response)
            require(value.get("result") == "CALL_COMPLETED" and
                    isinstance(value.get("body"), dict), f"native call failed: {label}")
            # If FFmpeg exited while the native call ran, keep the response but
            # refuse to use it as a clean paired video observation.
            recorder_gate(workdir, output, frozen, 0)
            return value["body"], receipt, gate
        time.sleep(0.2)
    raise TimeoutError(label)


def validate_writer(terminal: dict, frozen: dict) -> dict:
    prior = terminal.get("prior") or {}
    require(prior.get("terminal_kind") == "normal_result",
            "terminal is not a normal_result")
    score = prior.get("battle_warscore") or {}
    denominator = score.get("denominator_inputs") or {}
    participants = denominator.get("participants") or []
    require(isinstance(prior.get("hard_loss_inputs"), dict) and
            type(prior["hard_loss_inputs"].get("hard_loss_raw")) is int and
            score.get("status") == "recorded" and
            score.get("war_id") == frozen["expected_war_id"] and
            type(score.get("value_raw_q100000")) is int and
            type(score.get("attacker_relative_delta_raw_q100000")) is int and
            type(score.get("selected_cb_battle_scale_raw_q100000")) is int and
            type(denominator.get("after_minimum_int32")) is int and
            isinstance(participants, list) and bool(participants) and
            all(isinstance(row, dict) and
                len(row.get("buckets_native_add_order_int32", [])) == 8
                for row in participants), "same-run WarID 4 writer inputs incomplete")
    return {"hard_loss_inputs": prior["hard_loss_inputs"], "battle_warscore": score}


def check_mark(workdir: Path, label: str, date_raw: int,
               response_receipt: dict) -> dict:
    marks = workdir / "marks.jsonl"
    require(marks.is_file(), "recorder mark journal missing")
    rows = [json.loads(line) for line in marks.read_text(encoding="utf-8").splitlines()]
    matches = [row for row in rows if row.get("kind") == label and
               row.get("date_raw") == date_raw and
               row.get("combat_id") == 16777218 and row.get("war_id") == 4 and
               (row.get("control") or row.get("report") or {}).get("sha256") ==
               response_receipt["sha256"] and row.get("screenshot")]
    require(bool(matches), "same-day native response and visible screenshot mark missing")
    mark = matches[-1]
    source = mark.get("control") or mark.get("report")
    require(identity(Path(source["path"])) == source and
            identity(Path(mark["screenshot"]["path"])) == mark["screenshot"],
            "marked response/screenshot bytes changed")
    return {"marks": identity(marks), "kind": label,
            "response_sha256": source["sha256"],
            "screenshot": mark["screenshot"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("observe", "advance", "verify-terminal"))
    parser.add_argument("--static-receipt", type=Path, required=True)
    parser.add_argument("--session-output", type=Path, required=True)
    parser.add_argument("--recorder-workdir", type=Path, required=True)
    parser.add_argument("--segment", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--request-seconds", type=int, default=150)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require(1 <= args.segment <= 9 and 27 <= args.day <= 36 and
            30 <= args.request_seconds <= 150, "segment/day/request bound invalid")
    frozen = read(args.static_receipt)
    require(frozen.get("status") == "STATIC_GREEN_FOR_NEW_NO_LAUNCH_PREFLIGHT_ONLY",
            "static receipt not GREEN")
    live_root = Path(frozen["live_argv_without_fresh_steam_offline_receipt"][-2]).parent
    require(args.session_output.resolve() == (live_root / "ck3-output").resolve(),
            "session output differs from frozen a05 live root")
    expected_date = frozen["checkpoint_date_raw"] + 24 * (args.day - 27)
    prefix = f"e2t-s{args.segment:02d}-d{args.day:02d}"
    steps = live_root / "terminal-pair-steps"
    target = steps / f"{prefix}-{args.mode}.json"
    if not args.execute:
        print(json.dumps({"mode": "plan-only", "operation": args.mode,
                          "day": args.day, "segment": args.segment,
                          "date_raw": expected_date, "target": str(target),
                          "recorder_seconds": 600, "request_seconds": args.request_seconds}))
        return
    require(args.session_output.is_dir() and not target.exists(),
            "live session absent or step already exists")
    preflight = read(args.session_output / "preflight.json")
    require(preflight.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT" and
            (preflight.get("bridge_dll") or {}).get("sha256") == frozen["bridge"]["sha256"] and
            (preflight.get("bridge_injector") or {}).get("sha256") == frozen["injector"]["sha256"] and
            (preflight.get("checkpoint_source") or {}).get("save", {}).get("sha256") ==
            frozen["checkpoint_save"]["sha256"], "live preflight identity mismatch")
    if not steps.exists():
        steps.mkdir()
    result = {"schema": "ck3.episode02.terminal-pair-segment.v1",
              "created_utc": utc(), "mode": args.mode, "segment": args.segment,
              "day": args.day, "date_raw": expected_date,
              "static_receipt": identity(args.static_receipt),
              "recorder_workdir": str(args.recorder_workdir.resolve())}
    try:
        if args.mode == "observe":
            snapshot, snap_receipt, gate = call(args.session_output, prefix + "-snapshot",
                                                "ck3_take_snapshot", {}, args.recorder_workdir,
                                                frozen, args.request_seconds)
            require(snapshot.get("paused") is True and snapshot.get("map_ready") is True and
                    snapshot.get("date_raw") == expected_date and
                    type(snapshot.get("revision")) is int, "paused source day drifted")
            revision = snapshot["revision"]
            result.update({"snapshot": snap_receipt, "recorder_gate": gate,
                           "snapshot_revision": revision})
            if args.day <= 31:
                body, receipt, _ = call(args.session_output, prefix + "-control",
                                        "ck3_query_battle_control_snapshot_v1",
                                        {"subject_army_id": 18, "expected_revision": revision},
                                        args.recorder_workdir, frozen, args.request_seconds)
                control = body.get("battle_control_snapshot") or {}
                result["control_probe"] = receipt
                if control.get("status") == "available":
                    require(control.get("combat_id") == frozen["expected_combat_id"],
                            "available combat is not original CombatID")
                    result.update({"status": "observed-await-visible-mark",
                                   "native_response": receipt,
                                   "native_kind": "control",
                                   "queried_revision": body.get("queried_revision"),
                                   "battle_phase": control.get("phase")})
                else:
                    # Early normal terminal can precede the historical day-32
                    # boundary. Keep the unavailable control response, then
                    # query the writer at that exact paused revision.
                    require(body.get("queried_revision") == revision,
                            "control probe changed the paused revision")
                    body, receipt, _ = call(args.session_output, prefix + "-early-terminal",
                                            "ck3_query_battle_terminal_transition_v1",
                                            {"prior_combat_id": frozen["expected_combat_id"],
                                             "subject_public_cunit_id": 18,
                                             "expected_revision": revision},
                                            args.recorder_workdir, frozen, args.request_seconds)
                    terminal = body.get("battle_terminal_transition") or {}
                    prior = terminal.get("prior") or {}
                    result.update({"native_response": receipt,
                                   "native_kind": "report",
                                   "queried_revision": body.get("queried_revision"),
                                   "terminal_kind": prior.get("terminal_kind")})
                    if prior.get("terminal_kind") in ("normal_result", "no_normal_result"):
                        result["writer"] = validate_writer(terminal, frozen)
                        result["status"] = "new-run-writer-captured-await-after-panel"
                    else:
                        result["status"] = "observed-await-visible-mark"
            else:
                body, receipt, _ = call(args.session_output, prefix + "-terminal",
                                        "ck3_query_battle_terminal_transition_v1",
                                        {"prior_combat_id": frozen["expected_combat_id"],
                                         "subject_public_cunit_id": 18,
                                         "expected_revision": revision},
                                        args.recorder_workdir, frozen, args.request_seconds)
                terminal = body.get("battle_terminal_transition") or {}
                prior = terminal.get("prior") or {}
                result.update({"native_response": receipt,
                               "native_kind": "report",
                               "queried_revision": body.get("queried_revision"),
                               "terminal_kind": prior.get("terminal_kind")})
                if prior.get("terminal_kind") in ("normal_result", "no_normal_result"):
                    result["writer"] = validate_writer(terminal, frozen)
                    result["status"] = "new-run-writer-captured-await-after-panel"
                else:
                    result["status"] = "observed-await-visible-mark"
            require(type(result.get("queried_revision")) is int,
                    "native query revision missing")
        elif args.mode == "advance":
            observed_path = steps / f"{prefix}-observe.json"
            observed = read(observed_path)
            require(observed.get("status") == "observed-await-visible-mark" and
                    observed.get("date_raw") == expected_date and
                    observed.get("recorder_workdir") == str(args.recorder_workdir.resolve()),
                    "same-day observation or recorder identity missing")
            result["observed"] = identity(observed_path)
            result["mark"] = check_mark(args.recorder_workdir, prefix + "-visible",
                                        expected_date, observed["native_response"])
            snapshot, receipt, gate = call(args.session_output, prefix + "-pre-advance-snapshot",
                                           "ck3_take_snapshot", {}, args.recorder_workdir,
                                           frozen, args.request_seconds)
            require(snapshot.get("paused") is True and snapshot.get("map_ready") is True and
                    snapshot.get("date_raw") == expected_date and
                    snapshot.get("revision") == observed["queried_revision"],
                    "state changed after visible mark; redo on a new segment")
            result.update({"pre_advance_snapshot": receipt, "recorder_gate": gate})
            body, receipt, gate = call(args.session_output, prefix + "-advance",
                                       "ck3_execute_step",
                                       {"step": "life-advance",
                                        "expected_revision": snapshot["revision"]},
                                       args.recorder_workdir, frozen, args.request_seconds)
            result.update({"advance_response": receipt, "advance_recorder_gate": gate,
                           "starting_date_raw": body.get("starting_date_raw"),
                           "ending_date_raw": body.get("ending_date_raw")})
            require(body.get("starting_date_raw") == expected_date and
                    body.get("ending_date_raw") == expected_date + 24,
                    "life-advance crossed an unexpected day boundary")
            result["status"] = "one-day-advanced-with-active-recorder"
        else:
            observed_path = steps / f"{prefix}-observe.json"
            observed = read(observed_path)
            require(observed.get("status") == "new-run-writer-captured-await-after-panel" and
                    observed.get("date_raw") == expected_date and
                    observed.get("recorder_workdir") == str(args.recorder_workdir.resolve()),
                    "normal writer observation in this recorder is missing")
            result["observed"] = identity(observed_path)
            result["recorder_gate"] = recorder_gate(args.recorder_workdir,
                                                     args.session_output, frozen, 0)
            result["mark"] = check_mark(args.recorder_workdir,
                                        prefix + "-war4-after", expected_date,
                                        observed["native_response"])
            result["status"] = "same-recorder-terminal-mark-bound-unreviewed"
    except Exception:
        result["status"] = "red-preserved"
        result["error"] = traceback.format_exc()
        write_new(target, result)
        raise
    result["finished_utc"] = utc()
    write_new(target, result)
    print(json.dumps({"status": result["status"], "day": args.day,
                      "segment": args.segment, "result": str(target)}))


if __name__ == "__main__":
    main()
