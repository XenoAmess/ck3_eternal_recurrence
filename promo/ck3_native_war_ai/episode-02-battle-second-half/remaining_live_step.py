"""Bound one filmed E2-04, E2-05, or E2-06 replay to its exact native source.

`observe` only reads the paused game. `advance` makes one native save, arms the
private trace, advances exactly one day, and finishes that trace. All requests
and results are create-exclusive. This module does not start CK3 or FFmpeg.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time
from typing import Any

from pursuit_live_step import call, identity, utc, write_new


ACTOR = 29829
WAR = 4
COMBAT = 16777218
PLAYER_ARMY = 18
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
KNIGHT_DLL = "EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7"
KNIGHT_INJECTOR = "CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247"
JOIN_DLL = "1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F"
JOIN_INJECTOR = "34A1AB183F5173844A74E52A7F68195AAD859C380DFCA6B7E76F40611A51FB2D"

# Each row is a fresh one-day replay; historical 040/038 postevent cold loads
# are separate read-only comparison sources and cannot be spliced into these.
TRACKS = {
    "e2-04-d05": {
        "save": "695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885",
        "receipt": "6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7",
        "dll": KNIGHT_DLL, "injector": KNIGHT_INJECTOR,
        "date": 53146344, "control": True,
    },
    "e2-05-d26": {
        "save": "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B",
        "receipt": "78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C",
        "dll": KNIGHT_DLL, "injector": KNIGHT_INJECTOR,
        "date": 53146848, "control": True,
    },
    "e2-06-d11": {
        "save": "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953",
        "receipt": "DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5",
        "dll": JOIN_DLL, "injector": JOIN_INJECTOR,
        "date": 53146488, "control": False,
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(row: Any) -> str:
    return str((row or {}).get("sha256", "")).upper()


def private_call(output: Path, name: str, request: dict[str, Any],
                 timeout: float) -> tuple[dict[str, Any], dict[str, Any]]:
    """Use the owner's explicit private action envelope, not an MCP tool name."""
    target = output / "interactive-requests" / f"{name}.json"
    reply = output / "interactive-requests-responses" / f"{name}.json"
    temp = target.with_suffix(".json.pending")
    require(not target.exists() and not reply.exists() and not temp.exists(),
            f"private request name already used: {name}")
    write_new(temp, request)
    os.rename(temp, target)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if reply.is_file():
            try:
                row = json.loads(reply.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                time.sleep(0.25)
                continue
            receipt = {"request": identity(target), "response": identity(reply),
                       "result": row.get("result"), "error": row.get("error")}
            require(row.get("result") == "CALL_COMPLETED" and
                    isinstance(row.get("body"), dict),
                    f"private request returned RED: {receipt}")
            return row["body"], receipt
        time.sleep(0.25)
    raise TimeoutError(f"private request pending; inspect before retry: {target}")


def bind_session(output: Path, track: str) -> dict[str, Any]:
    spec = TRACKS[track]
    preflight_path = output / "preflight.json"
    readback_path = output / "native-start-readback.json"
    command_path = output / "command.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    command = json.loads(command_path.read_text(encoding="utf-8"))
    require(preflight.get("result") == "READY_FOR_BOUNDED_LIVE_ATTEMPT"
            and readback.get("postcondition_verified") is True,
            "managed native source load is not verified")
    for name, source in (("preflight", preflight.get("checkpoint_source") or {}),
                         ("loaded", readback.get("source_checkpoint") or {})):
        require((sha(source.get("save")), sha(source.get("receipt"))) ==
                (spec["save"], spec["receipt"]), f"{name} has a different source pair")
        require(source.get("actor") == ACTOR and source.get("date_raw") == spec["date"],
                f"{name} has a different source actor/date")
    require(sha(preflight.get("game")) == EXE_SHA, "CK3 executable differs")
    require(sha(preflight.get("bridge_dll")) == spec["dll"] and
            sha(preflight.get("bridge_injector")) == spec["injector"],
            "bridge pair differs from this replay's frozen pair")
    argv = command.get("argv") or []
    require("--capture" in argv and "--enable-private-phase-trace" in argv,
            "managed live attempt must opt into the private trace")
    require((output / "interactive-requests").is_dir() and
            (output / "interactive-requests-responses").is_dir(),
            "managed interactive request directories are missing")
    return {"track": track, "spec": spec, "preflight": identity(preflight_path),
            "loaded": identity(readback_path), "command": identity(command_path),
            "helper": identity(Path(__file__)),
            "request_primitive": identity(Path(__file__).with_name("pursuit_live_step.py"))}


def snapshot_case(body: dict[str, Any], date: int, *, require_combat: bool) -> tuple[bool, dict[str, Any]]:
    wars = [row for row in (body.get("active_wars") or []) if isinstance(row, dict)]
    war = next((row for row in wars if row.get("war_id") == WAR), {})
    army = next((row for row in (war.get("allied_armies") or [])
                 if isinstance(row, dict) and row.get("army_id") == PLAYER_ARMY), {})
    values = {"date_raw": body.get("date_raw"), "paused": body.get("paused"),
              "actor": (body.get("played_character") or {}).get("character_id"),
              "revision": body.get("revision"), "war_ids": [row.get("war_id") for row in wars],
              "army_id": army.get("army_id"), "army_state": army.get("army_state")}
    okay = (values["date_raw"] == date and values["paused"] is True and
            values["actor"] == ACTOR and type(values["revision"]) is int and
            WAR in values["war_ids"] and values["army_id"] == PLAYER_ARMY)
    if require_combat:
        okay = okay and values["army_state"] == "combat"
    return okay, values


def observe(output: Path, track: str, binding: dict[str, Any], timeout: float) -> int:
    spec = TRACKS[track]
    target = output / "operator-steps" / f"{track}-observe.json"
    require(not target.exists(), "observation name already used; preserve this attempt")
    body, snapshot = call(output, track + "-snapshot", "ck3_take_snapshot", {}, timeout)
    okay, values = snapshot_case(body, spec["date"], require_combat=True)
    control = None
    control_values = None
    if okay and spec["control"]:
        result, control = call(output, track + "-control",
                               "ck3_query_battle_control_snapshot_v1",
                               {"subject_army_id": PLAYER_ARMY,
                                "expected_revision": values["revision"]}, timeout)
        row = result.get("battle_control_snapshot") or {}
        control_values = {"combat_id": row.get("combat_id"),
                          "subject_army_id": result.get("subject_army_id"),
                          "snapshot_revision": result.get("snapshot_revision")}
        okay = (control_values["combat_id"] == COMBAT and
                control_values["subject_army_id"] == PLAYER_ARMY)
    # 085's historical sibling battle-control query returned RED. Its same
    # CombatID is bound only when the private trace begin explicitly accepts it.
    row = {"schema": "xar.war-promo.remaining-live-step/v1", "created_at": utc(),
           "mode": "observe", "track": track, "source_binding": binding,
           "same_source_war_army_frame": okay, "snapshot": snapshot,
           "snapshot_values": values, "control": control, "control_values": control_values,
           "combat_id_bound": bool(control_values and control_values["combat_id"] == COMBAT),
           "next_action": "review raw HUD, start one recorder, mark before advance" if okay else
                          "stop; preserve this branch"}
    write_new(target, row)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if okay else 2


def marked_running_recorder(output: Path, track: str, recorder: Path,
                            observation: dict[str, Any]) -> dict[str, Any]:
    import psutil

    intent = json.loads((recorder / "recorder-intent.json").read_text(encoding="utf-8"))
    start = json.loads((recorder / "recorder-start.json").read_text(encoding="utf-8"))
    require(not (recorder / "recorder-end.json").exists(), "recorder has ended")
    require(Path(intent.get("session_output", "")).resolve() == output.resolve() and
            (intent.get("source_save") or {}).get("sha256") == TRACKS[track]["save"] and
            (intent.get("source_receipt") or {}).get("sha256") == TRACKS[track]["receipt"] and
            intent.get("max_seconds") == 600, "recorder is not this exact 600-second source")
    process = psutil.Process(start["pid"])
    require(process.is_running() and process.name().lower() == "ffmpeg.exe",
            "bound FFmpeg recorder is not running")
    started_at = datetime.fromisoformat(start["started_at"]).timestamp()
    require(abs(process.create_time() - started_at) <= 5,
            "FFmpeg PID no longer belongs to the recorded start")
    marks_path = recorder / "marks.jsonl"
    marks = [json.loads(line) for line in marks_path.read_text(encoding="utf-8").splitlines()]
    reference = (observation.get("control") or observation["snapshot"])["response"]["sha256"]
    field = "control" if TRACKS[track]["control"] else "report"
    candidates = [row for row in marks if row.get("date_raw") == TRACKS[track]["date"]
                  and row.get("combat_id") == COMBAT and row.get("war_id") == WAR
                  and (row.get(field) or {}).get("sha256") == reference
                  and row.get("screenshot")]
    require(bool(candidates), "same-frame native response and screenshot mark missing")
    mark = candidates[-1]
    for name in (field, "screenshot"):
        require(identity(Path(mark[name]["path"])) == mark[name],
                f"marked {name} changed")
    return {"recorder_intent": identity(recorder / "recorder-intent.json"),
            "recorder_start": identity(recorder / "recorder-start.json"),
            "marks": identity(marks_path), "marked_reference": mark[field],
            "marked_screenshot": mark["screenshot"]}


def advance(output: Path, track: str, binding: dict[str, Any],
            recorder: Path, token: int, timeout: float) -> int:
    spec = TRACKS[track]
    steps = output / "operator-steps"
    observation_path = steps / f"{track}-observe.json"
    observation = json.loads(observation_path.read_text(encoding="utf-8"))
    require(observation.get("same_source_war_army_frame") is True and
            observation.get("source_binding") == binding, "matching observation required")
    require(1 <= token <= 2**31 - 1, "sequence token outside 1..2^31-1")
    marker = marked_running_recorder(output, track, recorder, observation)
    intent_path = steps / f"{track}-advance-intent.json"
    require(not intent_path.exists(), "advance already attempted; inspect pending native requests")
    before, before_receipt = call(output, track + "-pre-advance-snapshot",
                                  "ck3_take_snapshot", {}, timeout)
    okay, values = snapshot_case(before, spec["date"], require_combat=True)
    require(okay and values["revision"] == observation["snapshot_values"]["revision"],
            "same paused source frame/revision changed after observation")
    write_new(intent_path, {"schema": "xar.war-promo.remaining-advance-intent/v1",
                            "created_at": utc(), "track": track, "source_binding": binding,
                            "observation": identity(observation_path), "mark": marker,
                            "pre_advance_snapshot": before_receipt,
                            "sequence_token": token, "at_most_one_day": True})
    saved, save_receipt = call(output, track + "-before-save", "ck3_save_checkpoint",
                               {"expected_revision": values["revision"]}, timeout)
    require(saved.get("accepted") is True and
            (saved.get("checkpoint") or {}).get("status") == "saved" and
            (saved.get("checkpoint") or {}).get("date_raw") == spec["date"],
            "new pre-advance checkpoint was not saved")
    after_save, after_save_receipt = call(output, track + "-after-save-snapshot",
                                          "ck3_take_snapshot", {}, timeout)
    okay, after_save_values = snapshot_case(after_save, spec["date"], require_combat=True)
    require(okay and after_save_values["revision"] > values["revision"],
            "saved checkpoint did not leave the expected paused frame")
    control_receipt = None
    if spec["control"]:
        control, control_receipt = call(output, track + "-after-save-control",
                                        "ck3_query_battle_control_snapshot_v1",
                                        {"subject_army_id": PLAYER_ARMY,
                                         "expected_revision": after_save_values["revision"]}, timeout)
        require((control.get("battle_control_snapshot") or {}).get("combat_id") == COMBAT,
                "combat identity changed before arming private trace")
    begin_args = {"action": "private_phase_trace",
                  "step": "experimental-combat-phase-event-trace-begin-v1",
                  "expected_revision": after_save_values["revision"], "combat_id": COMBAT,
                  "managed_daily_sequence_token": token, "checkpoint_sequence": 1}
    if track == "e2-06-d11":
        begin_args.update(candidate_joining_army_id=22, capture_runtime_join_width=True,
                          capture_runtime_join_full_entries=True)
    begun, begin_receipt = private_call(output, track + "-trace-begin", begin_args, timeout)
    require(begun.get("accepted") is True and begun.get("combat_id") == COMBAT and
            begun.get("managed_daily_sequence_token") == token,
            "private trace did not bind the intended CombatID/token; no advance")
    advanced, advance_receipt = call(output, track + "-one-day", "ck3_execute_step",
                                     {"step": "life-advance",
                                      "expected_revision": after_save_values["revision"]}, timeout)
    new_revision = advanced.get("revision")
    require(type(new_revision) is int, "advance revision unavailable; inspect before trace finish")
    ended, end_receipt = private_call(
        output, track + "-trace-finish",
        {"action": "private_phase_trace",
         "step": "experimental-combat-phase-event-trace-finish-v1",
         "expected_revision": new_revision, "combat_id": COMBAT,
         "managed_daily_sequence_token": token}, timeout)
    post, post_receipt = call(output, track + "-post-snapshot", "ck3_take_snapshot", {}, timeout)
    post_ok, post_values = snapshot_case(post, spec["date"] + 24, require_combat=False)
    okay = (advanced.get("ending_date_raw") == spec["date"] + 24 and
            ended.get("accepted") is True and ended.get("combat_id") == COMBAT and
            ended.get("managed_daily_sequence_token") == token and post_ok)
    row = {"schema": "xar.war-promo.remaining-live-step/v1", "created_at": utc(),
           "mode": "advance", "track": track, "result": "ONE_DAY_ADVANCED_UNREVIEWED" if okay else
           "RED_PRESERVED", "source_binding": binding, "intent": identity(intent_path),
           "pre_save": save_receipt, "after_save_snapshot": after_save_receipt,
           "after_save_control": control_receipt, "trace_begin": begin_receipt,
           "one_day": advance_receipt, "trace_finish": end_receipt,
           "post_snapshot": post_receipt, "post_values": post_values,
           "event_outcome_and_clean_span_verified": False,
           "next_action": "review this run's event, HUD, raw PTS and native trace; no old-number substitution"}
    write_new(steps / f"{track}-advance.json", row)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if okay else 2


def finish(output: Path, track: str, binding: dict[str, Any], recorder: Path | None) -> int:
    for child in output.parent.iterdir():
        if child.is_dir() and (child / "recorder-start.json").is_file():
            require((child / "recorder-end.json").is_file(),
                    f"active recorder remains in this attempt: {child}")
    if recorder is not None:
        require((recorder / "recorder-final.json").is_file(),
                "wait for recorder probe/final receipt before ending the managed session")
    target = output / "interactive-requests" / f"999-{track}-finish.json"
    temp = target.with_suffix(".json.pending")
    require(not target.exists() and not temp.exists(), "finish already submitted")
    write_new(temp, {"action": "finish"})
    temp.rename(target)
    row = {"schema": "xar.war-promo.remaining-live-step/v1", "created_at": utc(),
           "mode": "finish", "track": track, "source_binding": binding,
           "finish_request": identity(target), "recorder":
           identity(recorder / "recorder-end.json") if recorder else None}
    write_new(output / "operator-steps" / f"{track}-finish.json", row)
    print(json.dumps(row, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("observe", "advance", "finish"))
    parser.add_argument("--track", choices=tuple(TRACKS), required=True)
    parser.add_argument("--session-output", type=Path, required=True)
    parser.add_argument("--recorder-workdir", type=Path)
    parser.add_argument("--sequence-token", type=int)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    if not 10 <= args.timeout <= 900:
        parser.error("timeout must be 10..900 seconds")
    if args.mode == "advance" and (args.recorder_workdir is None or args.sequence_token is None):
        parser.error("advance requires --recorder-workdir and --sequence-token")
    binding = bind_session(args.session_output, args.track)
    steps = args.session_output / "operator-steps"
    steps.mkdir(exist_ok=True)
    if args.mode == "observe":
        return observe(args.session_output, args.track, binding, args.timeout)
    if args.mode == "advance":
        return advance(args.session_output, args.track, binding,
                       args.recorder_workdir, args.sequence_token, args.timeout)
    return finish(args.session_output, args.track, binding, args.recorder_workdir)


if __name__ == "__main__":
    raise SystemExit(main())
