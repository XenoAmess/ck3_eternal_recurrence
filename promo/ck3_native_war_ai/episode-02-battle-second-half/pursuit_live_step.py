"""Explicit one-day E2-02/03 observation or advance through a managed session.

This script does not launch CK3 or record the desktop. `advance` is a game
mutation and must be invoked only after the operator has reviewed that day's
raw picture and observation. Requests, responses, and step receipts are new.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any


SOURCE_SAVE_SHA = "F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3"
SOURCE_RECEIPT_SHA = "5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012"
FIRST_DATE_RAW = 53146872
EXPECTED_ACTOR = 29829
EXPECTED_COMBAT = 16777218
EXPECTED_WAR = 4
PLAYER_ARMY = 18


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def identity(path: Path) -> dict[str, Any]:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size,
            "sha256": h.hexdigest().upper()}


def write_new(path: Path, data: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def verify_session(output: Path) -> dict[str, Any]:
    preflight_path = output / "preflight.json"
    readback_path = output / "native-start-readback.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    for label, source in (("preflight", preflight.get("checkpoint_source") or {}),
                          ("managed-load", readback.get("source_checkpoint") or {})):
        save = str((source.get("save") or {}).get("sha256", "")).upper()
        receipt = str((source.get("receipt") or {}).get("sha256", "")).upper()
        if (save, receipt) != (SOURCE_SAVE_SHA, SOURCE_RECEIPT_SHA):
            raise ValueError(f"{label} does not bind the frozen day-27 source pair")
    if preflight.get("result") != "READY_FOR_BOUNDED_LIVE_ATTEMPT" or \
            readback.get("postcondition_verified") is not True:
        raise ValueError("managed source load is not verified")
    if not (output / "interactive-requests").is_dir() or not \
            (output / "interactive-requests-responses").is_dir():
        raise FileNotFoundError("managed interactive request directories are absent")
    return {"preflight": identity(preflight_path), "managed_load": identity(readback_path),
            "script": identity(Path(__file__))}


def call(output: Path, name: str, tool: str, arguments: dict[str, Any], timeout: float) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = output / "interactive-requests"
    responses = output / "interactive-requests-responses"
    target = requests / f"{name}.json"
    reply = responses / f"{name}.json"
    temp = requests / f"{name}.json.pending"
    if target.exists() or reply.exists() or temp.exists():
        raise FileExistsError(f"request name is already used: {name}")
    write_new(temp, {"action": "mcp", "tool": tool, "arguments": arguments})
    # Windows rename refuses an existing destination; the owner sees only full JSON.
    os.rename(temp, target)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if reply.is_file():
            try:
                row = json.loads(reply.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                time.sleep(0.25)
                continue
            evidence = {"request": identity(target), "response": identity(reply),
                        "result": row.get("result"), "error": row.get("error")}
            if row.get("result") != "CALL_COMPLETED" or not isinstance(row.get("body"), dict):
                raise RuntimeError(f"managed request {name} returned {evidence}")
            return row["body"], evidence
        time.sleep(0.25)
    raise TimeoutError(f"request {name} pending; inspect before any retry: {target}")


def snapshot_ok(body: dict[str, Any], day: int) -> tuple[bool, dict[str, Any]]:
    date = FIRST_DATE_RAW + (day - 27) * 24
    actor = (body.get("played_character") or {}).get("character_id")
    war_rows = [war for war in (body.get("active_wars") or []) if isinstance(war, dict)]
    wars = [war.get("war_id") for war in war_rows]
    current_war = next((war for war in war_rows if war.get("war_id") == EXPECTED_WAR), {})
    player_army = next((army for army in (current_war.get("allied_armies") or [])
                        if army.get("army_id") == PLAYER_ARMY), {})
    values = {"date_raw": body.get("date_raw"), "paused": body.get("paused"),
              "actor": actor, "active_war_ids": wars, "revision": body.get("revision"),
              "war_score_raw": current_war.get("player_relative_war_score"),
              "player_army_state": player_army.get("army_state"),
              "player_army_retreating": player_army.get("retreating")}
    good = (values["date_raw"] == date and values["paused"] is True and
            actor == EXPECTED_ACTOR and EXPECTED_WAR in wars and
            type(values["revision"]) is int)
    return good, values


def observe(args: argparse.Namespace, binding: dict[str, Any]) -> int:
    name = f"e2-d{args.day:02d}"
    target = args.session_output / "operator-steps" / f"{name}-observe.json"
    if target.exists():
        raise FileExistsError(target)
    snapshot, snapshot_receipt = call(args.session_output, name + "-snapshot",
                                      "ck3_take_snapshot", {}, args.timeout)
    okay, values = snapshot_ok(snapshot, args.day)
    control_receipt = None
    case = None
    if okay:
        revision = values["revision"]
        if args.day < 32:
            body, control_receipt = call(args.session_output, name + "-control",
                                         "ck3_query_battle_control_snapshot_v1",
                                         {"subject_army_id": PLAYER_ARMY,
                                          "expected_revision": revision}, args.timeout)
            control = body.get("battle_control_snapshot") or {}
            case = {"combat_id": control.get("combat_id"),
                    "phase_raw": control.get("phase_raw"),
                    "phase_day": control.get("phase_day"),
                    "winner_raw": control.get("winner_raw")}
            expected_phase = 1 if args.day == 27 else 2
            expected_phase_day = 23 if args.day == 27 else args.day - 28
            case["matches_historical_phase"] = (
                case["phase_raw"] == expected_phase and
                case["phase_day"] == expected_phase_day)
            okay = (case["combat_id"] == EXPECTED_COMBAT and
                    case["matches_historical_phase"])
        else:
            body, control_receipt = call(args.session_output, name + "-terminal",
                                         "ck3_query_battle_terminal_transition_v1",
                                         {"prior_combat_id": EXPECTED_COMBAT,
                                          "subject_public_cunit_id": PLAYER_ARMY,
                                          "expected_revision": revision}, args.timeout)
            case = {"terminal_status": body.get("status"),
                    "prior_combat_id": EXPECTED_COMBAT}
            prior = ((body.get("battle_terminal_transition") or {}).get("prior") or {})
            case.update(terminal_kind=prior.get("terminal_kind"),
                        winner_raw=prior.get("winner_raw"))
            okay = (case["terminal_status"] == "available" and
                    case["terminal_kind"] == "normal_result" and
                    case["winner_raw"] == 0)
    row = {"schema": "xar.war-promo.pursuit-operator-step/v1", "created_at": utc(),
           "mode": "observe", "day": args.day, "same_case": okay,
           "source_binding": binding, "snapshot": snapshot_receipt,
           "snapshot_values": values, "control": control_receipt, "case": case,
           "next_action": "review raw HUD and mark, then explicitly advance" if okay else
                          "stop; freeze divergence and rebind script/cards"}
    write_new(target, row)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if okay else 2


def advance(args: argparse.Namespace, binding: dict[str, Any]) -> int:
    if args.day >= 32:
        raise ValueError("day 32 is terminal; no advance")
    name = f"e2-d{args.day:02d}"
    observed_path = args.session_output / "operator-steps" / f"{name}-observe.json"
    target = args.session_output / "operator-steps" / f"{name}-advance.json"
    if target.exists():
        raise FileExistsError(target)
    observed = json.loads(observed_path.read_text(encoding="utf-8"))
    if observed.get("same_case") is not True or observed.get("source_binding") != binding:
        raise ValueError("same-day observation and source binding are required")
    if args.recorder_workdir is None:
        raise ValueError("advance requires --recorder-workdir with a visible same-day mark")
    recorder_start = args.recorder_workdir / "recorder-start.json"
    recorder_end = args.recorder_workdir / "recorder-end.json"
    recorder_intent = args.recorder_workdir / "recorder-intent.json"
    marks_path = args.recorder_workdir / "marks.jsonl"
    if not recorder_start.is_file() or not recorder_intent.is_file() or \
            recorder_end.exists() or not marks_path.is_file():
        raise ValueError("the 600-second recorder must still be running")
    intent = json.loads(recorder_intent.read_text(encoding="utf-8"))
    if (Path(intent.get("session_output", "")).resolve() != args.session_output.resolve() or
            (intent.get("source_save") or {}).get("sha256") != SOURCE_SAVE_SHA or
            (intent.get("source_receipt") or {}).get("sha256") != SOURCE_RECEIPT_SHA or
            intent.get("max_seconds") != 600):
        raise ValueError("recorder is not the same 600-second source-bound live attempt")
    import psutil
    recorder_pid = json.loads(recorder_start.read_text(encoding="utf-8")).get("pid")
    try:
        process = psutil.Process(recorder_pid)
        if process.name().lower() != "ffmpeg.exe" or not process.is_running():
            raise ValueError("the bound FFmpeg recorder is not active")
    except psutil.NoSuchProcess as exc:
        raise ValueError("the bound FFmpeg recorder has exited") from exc
    expected_date = FIRST_DATE_RAW + (args.day - 27) * 24
    control_sha = (observed.get("control") or {}).get("response", {}).get("sha256")
    if not control_sha:
        raise ValueError("same-day native control response is missing")
    marks = [json.loads(line) for line in marks_path.read_text(encoding="utf-8").splitlines()]
    matching = [mark for mark in marks if mark.get("date_raw") == expected_date and
                (mark.get("control") or {}).get("sha256") == control_sha and
                mark.get("screenshot") is not None]
    if not matching:
        raise ValueError("same-day native control and screenshot mark missing; do not advance")
    mark = matching[-1]
    screenshot = mark["screenshot"]
    if identity(Path(screenshot["path"])) != screenshot:
        raise ValueError("same-day marked screenshot identity changed")
    if identity(Path(mark["control"]["path"])) != mark["control"]:
        raise ValueError("same-day marked control identity changed")
    mark_binding = {"marks": identity(marks_path), "screenshot": screenshot,
                    "control_response_sha256": control_sha}
    snapshot, snapshot_receipt = call(args.session_output, name + "-pre-advance-snapshot",
                                      "ck3_take_snapshot", {}, args.timeout)
    okay, values = snapshot_ok(snapshot, args.day)
    if not okay:
        write_new(target, {"mode": "advance", "day": args.day, "result": "RED_BEFORE_MUTATION",
                           "source_binding": binding, "snapshot": snapshot_receipt,
                           "snapshot_values": values, "mark_binding": mark_binding,
                           "created_at": utc()})
        return 2
    body, advance_receipt = call(args.session_output, name + "-advance",
                                 "ck3_execute_step", {"step": "life-advance",
                                                      "expected_revision": values["revision"]},
                                 args.timeout)
    expected = FIRST_DATE_RAW + (args.day - 26) * 24
    okay = body.get("ending_date_raw") == expected
    row = {"schema": "xar.war-promo.pursuit-operator-step/v1", "created_at": utc(),
           "mode": "advance", "day": args.day, "expected_next_date_raw": expected,
           "actual_next_date_raw": body.get("ending_date_raw"), "same_case": okay,
           "source_binding": binding, "snapshot": snapshot_receipt,
           "snapshot_values": values, "mark_binding": mark_binding,
           "advance": advance_receipt,
           "next_action": "observe next paused day" if okay else
                          "stop; inspect actual date and preserve branch"}
    write_new(target, row)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if okay else 2


def finish(args: argparse.Namespace, binding: dict[str, Any]) -> int:
    requests = args.session_output / "interactive-requests"
    target = requests / "999-e2-finish.json"
    temp = requests / "999-e2-finish.json.pending"
    record = args.session_output / "operator-steps" / "e2-finish.json"
    if target.exists() or temp.exists() or record.exists():
        raise FileExistsError("finish request already exists; inspect the managed session")
    write_new(temp, {"action": "finish"})
    os.rename(temp, target)
    row = {"schema": "xar.war-promo.pursuit-operator-step/v1",
           "mode": "finish", "created_at": utc(), "operator_last_day": args.day,
           "source_binding": binding, "finish_request": identity(target),
           "next_action": "wait for capture_session exit and hash capture-report; keep every RED/partial"}
    write_new(record, row)
    print(json.dumps(row, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("observe", "advance", "finish"))
    parser.add_argument("--session-output", type=Path, required=True)
    parser.add_argument("--day", type=int, required=True, choices=range(27, 33))
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--recorder-workdir", type=Path,
                        help="required by advance; active 600s recorder with a same-day screenshot/control mark")
    args = parser.parse_args()
    if args.timeout < 10 or args.timeout > 900:
        parser.error("timeout must be 10..900 seconds")
    binding = verify_session(args.session_output)
    steps = args.session_output / "operator-steps"
    steps.mkdir(exist_ok=True)
    if args.mode == "observe":
        return observe(args, binding)
    if args.mode == "advance":
        return advance(args, binding)
    return finish(args, binding)


if __name__ == "__main__":
    raise SystemExit(main())
