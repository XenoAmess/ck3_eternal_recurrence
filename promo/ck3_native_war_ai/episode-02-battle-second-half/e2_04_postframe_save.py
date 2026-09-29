"""Preserve one E2-04 d06 native checkpoint after one verified d05 advance.

This operator only attaches to an already running managed capture_session. It
does not launch CK3, advance the date, record video, or retry an uncertain save.
The d06 checkpoint and its original MCP response remain research evidence
until a separate exact-source cold load proves the next-frame combat inputs.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pursuit_live_step import call, identity, utc, write_new
from remaining_live_step import (
    ACTOR, COMBAT, EXE_SHA, PLAYER_ARMY, PROVINCE, TRACKS, WAR,
    battle_control_case, bind_session, require, snapshot_case,
)


TRACK = "e2-04-d05"
POST_DATE = TRACKS[TRACK]["date"] + 24
PRE_SAVE_NAME = f"{TRACK}-before-save"
SAVE_NAME = f"{TRACK}-postframe-save"
PRESERVATION_NAME = "e2-04-d06-postframe-preservation-a01"


def matching_original(path: Path, recorded: dict[str, Any]) -> dict[str, Any]:
    require(not path.is_symlink(), f"original is symlinked: {path}")
    require(path.resolve() == Path(recorded["path"]).resolve(),
            f"receipt points outside its expected original: {path}")
    actual = identity(path)
    require(actual == recorded, f"original bytes changed: {path}")
    return actual


def response_body(output: Path, name: str, recorded: dict[str, Any]) -> dict[str, Any]:
    response = output / "interactive-requests-responses" / f"{name}.json"
    request = output / "interactive-requests" / f"{name}.json"
    matching_original(response, recorded["response"])
    matching_original(request, recorded["request"])
    row = json.loads(response.read_text(encoding="utf-8"))
    require(row.get("result") == recorded.get("result") == "CALL_COMPLETED" and
            isinstance(row.get("body"), dict), f"original response is not completed: {name}")
    return row


def checkpoint_case(row: dict[str, Any], date: int, save_path: Path) -> dict[str, Any]:
    body = row.get("body") or {}
    saved = body.get("checkpoint") or {}
    lifecycle = saved.get("succession_lifecycle") or {}
    hello = (row.get("driver_state") or {}).get("hello") or {}
    require(body.get("step") == "save-checkpoint" and body.get("accepted") is True and
            saved.get("status") == "saved" and saved.get("date_raw") == date and
            saved.get("episode_character_id") == ACTOR and
            saved.get("name") == "xar_checkpoint.ck3" and
            Path(saved.get("path", "")).resolve() == save_path.resolve() and
            type(saved.get("size")) is int and saved["size"] > 0 and
            isinstance(saved.get("sha256"), str) and len(saved["sha256"]) == 64,
            "native checkpoint actor/date/path/size does not match")
    require(lifecycle.get("lifecycle") == "ordinary_campaign_succession" and
            lifecycle.get("xar_enabled") == "xar_off" and
            lifecycle.get("pact_contract") == "absent_by_fresh_campaign_xar_off_contract" and
            lifecycle.get("source") == "pure-vanilla-enabled-mods-empty" and
            hello.get("ck3_build_match") is True and
            str(hello.get("expected_ck3_sha256", "")).upper() == EXE_SHA,
            "native checkpoint lacks exact vanilla lifecycle/build hello")
    return saved


def checkpoint_identity(path: Path, saved: dict[str, Any]) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), "native checkpoint path missing or symlinked")
    actual = identity(path)
    require(actual["bytes"] == saved["size"] and
            actual["sha256"] == saved["sha256"].upper(),
            "native checkpoint bytes differ from actual save response")
    return actual


def copy_exclusive(source: Path, target: Path, expected: dict[str, Any]) -> dict[str, Any]:
    require(not target.exists() and not target.is_symlink(), f"preservation target exists: {target}")
    before_stat = source.stat()
    before = identity(source)
    require(before == expected, "checkpoint changed before copy")
    with source.open("rb") as src, target.open("xb") as dst:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())
    after = identity(source)
    after_stat = source.stat()
    copy = identity(target)
    require(before == after and
            (before["bytes"], before["sha256"]) ==
            (copy["bytes"], copy["sha256"]) and
            before_stat.st_mtime_ns == after_stat.st_mtime_ns,
            "checkpoint changed during copy; preserve partial and stop")
    return copy


def save_inventory(save_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(save_dir.iterdir()):
        if path.is_file():
            info = path.stat()
            rows.append({"name": path.name, "bytes": info.st_size,
                         "mtime_ns": info.st_mtime_ns, "symlink": path.is_symlink()})
    return rows


def frozen_advance(output: Path, binding: dict[str, Any]) -> dict[str, Any]:
    steps = output / "operator-steps"
    advance_path = steps / f"{TRACK}-advance.json"
    intent_path = steps / f"{TRACK}-advance-intent.json"
    advance = json.loads(advance_path.read_text(encoding="utf-8"))
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    require(advance.get("mode") == "advance" and advance.get("track") == TRACK and
            advance.get("result") == "ONE_DAY_ADVANCED_UNREVIEWED" and
            advance.get("source_binding") == intent.get("source_binding") == binding and
            intent.get("track") == TRACK and intent.get("at_most_one_day") is True,
            "advance/source binding is not an accepted one-day replay")
    matching_original(intent_path, advance["intent"])
    token = intent.get("sequence_token")
    require(type(token) is int and 1 <= token <= 2**31 - 1,
            "advance sequence token is missing or invalid")
    pre_row = response_body(output, PRE_SAVE_NAME, advance["pre_save"])
    after_save = response_body(output, f"{TRACK}-after-save-snapshot",
                               advance["after_save_snapshot"])
    before_ok, before_values = snapshot_case(
        after_save["body"], TRACKS[TRACK]["date"], require_combat=True)
    require(before_ok, "pre-advance saved frame no longer identifies d05 combat")
    begin = response_body(output, f"{TRACK}-trace-begin", advance["trace_begin"])
    one_day = response_body(output, f"{TRACK}-one-day", advance["one_day"])
    trace = response_body(output, f"{TRACK}-trace-finish", advance["trace_finish"])
    post = response_body(output, f"{TRACK}-post-snapshot", advance["post_snapshot"])
    post_ok, post_values = snapshot_case(post["body"], POST_DATE, require_combat=True)
    require(post_ok and post_values == advance.get("post_values") and
            type(post_values.get("native_revision")) is int and
            isinstance(post_values.get("snapshot_id"), str) and
            post_values["snapshot_id"], "d06 post-snapshot identity changed")
    require(one_day["body"].get("ending_date_raw") == POST_DATE and
            begin["body"].get("accepted") is True and
            begin["body"].get("combat_id") == COMBAT and
            begin["body"].get("managed_daily_sequence_token") == token and
            (trace["body"].get("accepted") is True) and
            trace["body"].get("combat_id") == COMBAT and
            trace["body"].get("managed_daily_sequence_token") == token,
            "one-day/trace identity does not match d06 post-snapshot")
    begin_request = json.loads((output / "interactive-requests" /
                               f"{TRACK}-trace-begin.json").read_text(encoding="utf-8"))
    day_request = json.loads((output / "interactive-requests" /
                             f"{TRACK}-one-day.json").read_text(encoding="utf-8"))
    finish_request = json.loads((output / "interactive-requests" /
                                f"{TRACK}-trace-finish.json").read_text(encoding="utf-8"))
    require(begin_request.get("expected_revision") == before_values["revision"] and
            begin_request.get("combat_id") == COMBAT and
            begin_request.get("managed_daily_sequence_token") == token and
            day_request.get("action") == "mcp" and
            day_request.get("tool") == "ck3_execute_step" and
            day_request.get("arguments") == {
                "step": "life-advance", "expected_revision": before_values["revision"]} and
            finish_request.get("combat_id") == COMBAT and
            finish_request.get("managed_daily_sequence_token") == token and
            finish_request.get("expected_revision") == one_day["body"].get("revision"),
            "one-day action revision/token differs from frozen trace")
    return {"advance": identity(advance_path), "intent": identity(intent_path),
            "token": token, "pre_save": pre_row, "post_values": post_values,
            "one_day": advance["one_day"], "trace_finish": advance["trace_finish"],
            "post_snapshot": advance["post_snapshot"]}


def run(output: Path, timeout: float) -> dict[str, Any]:
    output = output.resolve()
    require(output.name == "ck3-output" and output.is_dir(), "expected managed ck3-output")
    require(not (output / "session-result.json").exists() and
            not (output / "operator-steps" / f"{TRACK}-finish.json").exists(),
            "managed session already finished")
    request = output / "interactive-requests" / f"{SAVE_NAME}.json"
    reply = output / "interactive-requests-responses" / f"{SAVE_NAME}.json"
    preservation = output.parent / PRESERVATION_NAME
    intent_path = output / "operator-steps" / f"{TRACK}-post-save-intent.json"
    for path in (request, request.with_suffix(".json.pending"), reply,
                 preservation, intent_path):
        require(not path.exists() and not path.is_symlink(),
                f"postframe attempt already used; inspect, never retry: {path}")

    binding = bind_session(output, TRACK)
    prior = frozen_advance(output, binding)
    current, current_receipt = call(output, f"{TRACK}-postframe-current-snapshot",
                                    "ck3_take_snapshot", {}, timeout)
    current_ok, current_values = snapshot_case(current, POST_DATE, require_combat=True)
    require(current_ok and current_values == prior["post_values"],
            "paused d06 wrapper/native snapshot changed since advance")
    control, control_receipt = call(
        output, f"{TRACK}-postframe-current-control",
        "ck3_query_battle_control_snapshot_v1",
        {"subject_army_id": PLAYER_ARMY, "expected_revision": current_values["revision"]}, timeout)
    control_ok, control_values = battle_control_case(control, current_values, POST_DATE)
    require(control_ok and control_values["combat_id"] == COMBAT and
            control_values["combat_province_id"] == PROVINCE,
            "paused d06 battle identity is no longer same-frame")

    save_dir = output.parent / "ck3-state" / "profile" / "save games"
    save_path = save_dir / "xar_checkpoint.ck3"
    require(save_dir.is_dir() and not save_dir.is_symlink(),
            "isolated managed save directory missing")
    pre_saved = checkpoint_case(prior["pre_save"], TRACKS[TRACK]["date"], save_path)
    pre_identity = checkpoint_identity(save_path, pre_saved)
    preservation.mkdir(exist_ok=False)
    pre_inventory = save_inventory(save_dir)
    pre_copy = copy_exclusive(save_path,
                              preservation / "d05-preserved-before-post-save.ck3", pre_identity)
    write_new(preservation / "d05-preservation.json", {
        "schema": "xar.war-promo.pre-post-save-preservation/v1", "created_at": utc(),
        "source_binding": binding, "original": pre_identity, "copy": pre_copy,
        "native_request": prior["pre_save"].get("request"),
        "native_response_original": identity(
            output / "interactive-requests-responses" / f"{PRE_SAVE_NAME}.json"),
        "save_inventory": pre_inventory})
    # Freeze the one-shot action before submitting the native request. Any
    # timeout leaves both this intent and the request for manual inspection.
    write_new(intent_path, {
        "schema": "xar.war-promo.postframe-save-intent/v1", "created_at": utc(),
        "source_binding": binding, "advance": prior["advance"],
        "advance_intent": prior["intent"], "sequence_token": prior["token"],
        "post_snapshot": prior["post_snapshot"],
        "current_snapshot": current_receipt, "current_control": control_receipt,
        "d05_preservation": identity(preservation / "d05-preservation.json"),
        "expected_date_raw": POST_DATE, "expected_revision": current_values["revision"],
        "one_save_request_only": True})
    saved_body, saved_receipt = call(output, SAVE_NAME, "ck3_save_checkpoint",
                                     {"expected_revision": current_values["revision"]}, timeout)
    response_row = response_body(output, SAVE_NAME, saved_receipt)
    require(saved_body == response_row["body"], "save response changed after managed call")
    saved = checkpoint_case(response_row, POST_DATE, save_path)
    d06_identity = checkpoint_identity(save_path, saved)
    d06_copy = copy_exclusive(save_path, preservation / "d06-immutable.ck3", d06_identity)
    after_inventory = save_inventory(save_dir)
    preservation_row = {
        "schema": "xar.war-promo.postframe-save-preservation/v1", "created_at": utc(),
        "result": "D06_SAVED_UNREVIEWED", "source_binding": binding,
        "intent": identity(intent_path), "native_save": saved_receipt,
        "native_save_original": d06_identity, "immutable_copy": d06_copy,
        "pre_save_copy": pre_copy, "save_inventory_before": pre_inventory,
        "save_inventory_after": after_inventory,
        "coldload_checkpoint_receipt": saved_receipt["response"],
        "trait_and_v3_result_known": False,
    }
    write_new(preservation / "d06-preservation.json", preservation_row)
    after, after_receipt = call(output, f"{TRACK}-postframe-after-save-snapshot",
                               "ck3_take_snapshot", {}, timeout)
    after_ok, after_values = snapshot_case(after, POST_DATE, require_combat=True)
    require(after_ok and type(after_values.get("native_revision")) is int and
            isinstance(after_values.get("snapshot_id"), str),
            "post-save paused d06 identity is unavailable")
    after_control, after_control_receipt = call(
        output, f"{TRACK}-postframe-after-save-control",
        "ck3_query_battle_control_snapshot_v1",
        {"subject_army_id": PLAYER_ARMY, "expected_revision": after_values["revision"]}, timeout)
    after_control_ok, after_control_values = battle_control_case(
        after_control, after_values, POST_DATE)
    require(after_control_ok and after_control_values["combat_id"] == COMBAT and
            after_control_values["combat_province_id"] == PROVINCE,
            "post-save battle identity changed; preserved pair remains unadmitted")
    matching_original(output / "interactive-requests-responses" /
                      f"{SAVE_NAME}.json", saved_receipt["response"])
    require(identity(preservation / "d06-immutable.ck3") == d06_copy,
            "immutable d06 copy changed before operator admission")
    result = {"schema": "xar.war-promo.postframe-save-operator/v1", "created_at": utc(),
              "result": "D06_PAIR_READY_FOR_SEPARATE_COLDLOAD_UNREVIEWED",
              "source_binding": binding, "sequence_token": prior["token"],
              "preservation": identity(preservation / "d06-preservation.json"),
              "d06_save": d06_copy, "d06_receipt": saved_receipt["response"],
              "after_save_snapshot": after_receipt,
              "after_save_control": after_control_receipt,
              "after_save_values": after_values,
              "trait_and_v3_result_known": False}
    write_new(preservation / "postframe-save-result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    if not 10 <= args.timeout <= 900:
        parser.error("timeout must be 10..900 seconds")
    row = run(args.session_output, args.timeout)
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
