"""Verify narrow E2-05 a02 native receipt facts without reading gameplay video.

This is a candidate evidence check. A successful result does not certify a
production trace, character death, clean span, or human media review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DEFAULT_ROOT = Path(
    "D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02"
)
EXPECTED = {
    "ck3-output/capture-report.json": (8654, "F0A9F2461F72C2B2B55109142C796F14D09097439824CFADFE19F5C8DB537859"),
    "ck3-output/preflight.json": (12474, "7CBEDAF1C6570749EB76E35C3FF8FE2EBA13EE16E6CE9F67D78401D880C02195"),
    "ck3-output/native-start-readback.json": (31073, "770C548326563DF052C935F73EAE7C0FFDA73837A9CDF34C566DB75AAE79D94C"),
    "ck3-output/interactive-requests-responses/e2-05-d26-control.json": (83317, "D41E384CE022C261E15E3761980A0A78E26BA0B21C9FCF3F2393F062F03CEC1F"),
    "ck3-output/interactive-requests-responses/e2-05-d26-snapshot.json": (36677, "129D2DC384C53634C85987C37AC3B7D80E7B25589F036B804F13A3476A1D2113"),
    "ck3-output/interactive-requests-responses/e2-05-d26-after-save-control.json": (83331, "79B1D1E35A08D8B20C66284103CE3C280BDE6F0CF0963086BD5BB1B2FDD819EC"),
    "ck3-output/interactive-requests-responses/e2-05-d26-trace-begin.json": (11489, "95E81F63B449EB9E4AA301672CD95053F241C60723C34A4BE1B70E481E9F91B9"),
    "ck3-output/interactive-requests-responses/e2-05-d26-one-day.json": (19929, "ED502C01BEBDDA1887D2A48133D8807C98A2547D7008706FED6528F32461BB95"),
    "ck3-output/interactive-requests-responses/e2-05-d26-trace-finish.json": (431957, "BFF0A9CFCE858C88B9FEA67D0FB646CDB7175BA7DC957898769BE02D5479C7D0"),
    "ck3-output/interactive-requests-responses/e2-05-d26-post-snapshot.json": (215859, "062907DC73AAD127C766F45E754BEC7457E8C6B956D842A87DB2BF35B6030249"),
    "ck3-output/operator-steps/e2-05-d26-observe.json": (4240, "7239F68CFE7C517468628E061BD50AD84E44E0492D965F010972DBD0FC1E9294"),
    "ck3-output/operator-steps/e2-05-d26-advance.json": (7324, "304EFA9223DCB2DC5313736938E890382139FBE2BA85E43E1910DD0ADA22C6CA"),
    "recording-e2-05-d26-a01/marks.jsonl": (3307, "3266390257DAEFF91114FF1E7D017192ECF50D836776D1BC5E8191643C9C5337"),
    "recording-e2-05-d26-a01/recorder-final.json": (1927, "B27C9434789CF4BD8F0F6BE3273902AE1274DBE1DD1D614D40F6068CC78AD7F4"),
    "ck3-output/session-result.json": (7433, "09D67A493473ED4FA6C65B643114B6EBE92AC40B9E2E5CD356B02E2A1AA76D42"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def source(root: Path, relative: str) -> dict:
    path = root / relative
    expected_size, expected_sha = EXPECTED[relative]
    require(path.is_file() and path.stat().st_size == expected_size and
            sha(path) == expected_sha, f"source bytes: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def ids(rows: list[dict], key: str) -> set[int]:
    return {row[key] for row in rows}


PREEXISTING_EVENTS = [
    {"left_character_id": 47029, "right_character_id": 33435,
     "stable_key": "knight_wounded_by_enemy", "type_raw": 2,
     "side_index": 0, "target_right": False},
    {"left_character_id": 33884, "right_character_id": 32440,
     "stable_key": "knight_wounded_by_enemy", "type_raw": 2,
     "side_index": 0, "target_right": False},
]


def verify_trace_binding(finish: dict) -> None:
    """Check the managed-day identity and exact preexisting-event prefix.

    Kept separate from byte loading so a mutated in-memory trace can test the
    semantic gate independently of source SHA verification.
    """
    checkpoint = finish["managed_trace"]["managed_checkpoint"]
    records = finish["managed_trace"]["trace"]["records"]
    require(finish["managed_daily_sequence_token"] == 101 and
            finish["combat_id"] == 16777218 and
            all(checkpoint[edge]["managed_daily_sequence_token"] == 101 and
                checkpoint[edge]["combat_id"] == 16777218 and
                checkpoint[edge]["paused"] is True
                for edge in ("before", "after")) and
            [checkpoint[edge]["date_raw"] for edge in ("before", "after")] ==
            [53146848, 53146872] and
            len(records) == 7 and
            all(r["managed_daily_sequence_token"] == 101 and
                r["combat_id"] == 16777218 for r in records) and
            [r["native_date_raw"] for r in records] ==
            [53146848, 53146848, 53146872, 53146872,
             53146872, 53146872, 53146872],
            "one managed sequence, combat and exact d26/d27 dates")
    require(all(r["battle_events"] == PREEXISTING_EVENTS
                for r in records[:5]) and
            records[5]["battle_events"][:2] == PREEXISTING_EVENTS,
            "first five boundaries preserve the exact two wound events")
    require(33437 in ids(records[5]["sides"][1]["knights"], "character_id") and
            34120 in ids(records[5]["sides"][0]["knights"], "character_id"),
            "event left and right characters belong to opposite battle sides")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.external_root
    data = {name: source(root, name) for name in EXPECTED if not name.endswith(".jsonl")}

    capture = data["ck3-output/capture-report.json"]
    preflight = data["ck3-output/preflight.json"]
    observe = data["ck3-output/operator-steps/e2-05-d26-observe.json"]
    control = data["ck3-output/interactive-requests-responses/e2-05-d26-control.json"]["body"]
    after_save = data["ck3-output/interactive-requests-responses/e2-05-d26-after-save-control.json"]["body"]
    begin = data["ck3-output/interactive-requests-responses/e2-05-d26-trace-begin.json"]["body"]
    one_day = data["ck3-output/interactive-requests-responses/e2-05-d26-one-day.json"]["body"]
    finish = data["ck3-output/interactive-requests-responses/e2-05-d26-trace-finish.json"]["body"]
    post = data["ck3-output/interactive-requests-responses/e2-05-d26-post-snapshot.json"]["body"]
    advance = data["ck3-output/operator-steps/e2-05-d26-advance.json"]
    recorder = data["recording-e2-05-d26-a01/recorder-final.json"]
    session = data["ck3-output/session-result.json"]

    checkpoint = capture["checkpoint_source"]
    require(checkpoint["save"]["sha256"] ==
            "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B" and
            Path(checkpoint["save"]["path"]).stat().st_size == checkpoint["save"]["bytes"] and
            sha(Path(checkpoint["save"]["path"])) == checkpoint["save"]["sha256"] and
            sha(Path(checkpoint["receipt"]["path"])) == checkpoint["receipt"]["sha256"] and
            checkpoint["date_raw"] == 53146848 and checkpoint["actor"] == 29829 and
            preflight["game"]["sha256"] ==
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" and
            preflight["bridge_dll"]["sha256"] ==
            "EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7",
            "a02 independent source save and exact build")
    require(observe["same_source_war_army_frame"] is True and
            observe["combat_id_bound"] is True and
            observe["subject_combat_membership_verified"] is True and
            observe["snapshot"]["response"]["sha256"] ==
            EXPECTED["ck3-output/interactive-requests-responses/e2-05-d26-snapshot.json"][1] and
            observe["control"]["response"]["sha256"] ==
            EXPECTED["ck3-output/interactive-requests-responses/e2-05-d26-control.json"][1] and
            observe["snapshot_values"]["war_ids"] == [4] and
            (observe["snapshot_values"]["date_raw"],
             observe["snapshot_values"]["army_id"],
             observe["snapshot_values"]["actor"]) == (53146848, 18, 29829),
            "a02 same-source war, army, combat observation")
    for item in (control, after_save):
        native = item["battle_control_snapshot"]
        require(item["accepted"] is True and item["battle_control_ready"] is True and
                native["status"] == "available" and
                (native["observed_date_raw"], native["combat_id"], native["province_id"],
                 native["subject_public_cunit_id"], native["side_index"],
                 native["phase"], native["phase_day"]) ==
                (53146848, 16777218, 2633, 18, 1, "main", 22),
                "same pre-advance d26 combat control")
    require(begin["accepted"] is True and begin["status"] == "armed" and
            begin["private_build"] is True and
            begin["production_trace_ready"] is False and
            (begin["managed_daily_sequence_token"], begin["combat_id"]) ==
            (101, 16777218) and
            (one_day["starting_date_raw"], one_day["ending_date_raw"],
             one_day["elapsed_days"], one_day["requested_horizon_days"],
             one_day["paused"]) == (53146848, 53146872, 1, 1, True) and
            advance["result"] == "ONE_DAY_ADVANCED_UNREVIEWED" and
            advance["event_outcome_and_clean_span_verified"] is False and
            (post["date_raw"], post["paused"]) == (53146872, True) and
            ids(post["active_wars"], "war_id") == {4} and
            any(a["army_id"] == 18 and a["in_combat"] is True for a in post["player_armies"]),
            "one day and ordinary paused poststate")

    checkpoint = finish["managed_trace"]["managed_checkpoint"]
    trace = finish["managed_trace"]["trace"]
    records = trace["records"]
    verify_trace_binding(finish)
    require(finish["accepted"] is True and finish["production_trace_ready"] is False and
            finish["status"] == "trace_unavailable" and
            checkpoint["exact_one_day_observed"] is True and
            checkpoint["boundary_dates_match_checkpoint"] is True and
            checkpoint["detours_uninstalled"] is True and
            checkpoint["before"]["date_raw"] == 53146848 and
            checkpoint["after"]["date_raw"] == 53146872 and
            trace["status"] == "failed" and trace["failure_flags"] == 1040 and
            trace["record_count"] == len(records) == 7 and
            trace["readiness"]["exact_boundary_sequence"] is False and
            trace["readiness"]["bounded_capture_complete"] is False and
            trace["readiness"]["full_mutable_transition_bundle_complete"] is False and
            trace["readiness"]["original_trace_ready"] is False,
            "private partial trace remains RED")
    require([len(r["battle_events"]) for r in records] == [2, 2, 2, 2, 2, 3, 0] and
            records[5]["battle_events"][:2] == records[4]["battle_events"] and
            records[5]["battle_events"][2] == {
                "left_character_id": 33437, "right_character_id": 34120,
                "stable_key": "knight_killed_by_enemy", "type_raw": 3,
                "side_index": 1, "target_right": False,
            } and records[5]["capture_failure_flags"] == 0 and
            records[5]["boundary"] ==
            "native_capture_after_side1_phase_fire_return_0x2309EFF",
            "new same-run battle-event row at side1 fire return")
    for r in records[:6]:
        require(len(r["characters"]) == 36 and
                all(c["death_marker_present"] is False for c in r["characters"]),
                "no true death marker in captured character arrays")
    fifth, paused = records[5], records[6]
    require(paused["boundary"] == "paused_next_day_stable_query" and
            paused["native_date_raw"] == 53146872 and
            paused["capture_failure_flags"] == 16 and
            not paused["characters"] and not paused["battle_events"] and
            not paused["accolades"],
            "paused character and event arrays unavailable")
    before_side, after_side = fifth["sides"][1], paused["sides"][1]
    require(ids(before_side["regiments"], "regiment_id") -
            ids(after_side["regiments"], "regiment_id") == {65} and
            ids(before_side["knights"], "character_id") -
            ids(after_side["knights"], "character_id") == {33437} and
            (len(before_side["regiments"]), len(after_side["regiments"]),
             len(before_side["knights"]), len(after_side["knights"])) ==
            (24, 23, 14, 13) and
            before_side["scheduled_knights"][0]["current_character_id"] == 33437 and
            after_side["scheduled_knights"][0]["current_character_id"] == 0 and
            ids(fifth["sides"][0]["knights"], "character_id") ==
            ids(paused["sides"][0]["knights"], "character_id"),
            "partial paused roster removal, not a death or selector proof")
    require(any(c["character_id"] == 33437 and
                c["death_marker_present"] is False and c["current_regiment_id"] == 65
                for c in fifth["characters"]),
            "event boundary still contains character 33437 with false death marker")

    marks_path = root / "recording-e2-05-d26-a01/marks.jsonl"
    require(marks_path.stat().st_size == EXPECTED["recording-e2-05-d26-a01/marks.jsonl"][0] and
            sha(marks_path) == EXPECTED["recording-e2-05-d26-a01/marks.jsonl"][1] ==
            recorder["marks"]["sha256"], "same recorder marks bytes")
    marks = [json.loads(line) for line in marks_path.read_text(encoding="utf-8").splitlines()]
    require([m["kind"] for m in marks] ==
            ["recorder-start", "d26-before", "d27-after", "d27-player-knights", "recorder-end"] and
            [m["date_raw"] for m in marks[1:4]] ==
            [53146848, 53146872, 53146872], "ordered same-run marks")
    for mark in marks[1:4]:
        require(mark["approx_seconds_are_not_video_pts"] is True,
                "marks do not certify video PTS")
        for name in ("control", "report", "screenshot"):
            item = mark.get(name)
            if item is not None:
                path = Path(item["path"])
                require(path.is_file() and path.stat().st_size == item["bytes"] and
                        sha(path) == item["sha256"], f"marked {name} exact bytes")
    raw = recorder["raw"]
    require(recorder["result"] == "ENCODED_UNREVIEWED" and
            recorder["clean_spans_certified"] is False and
            recorder["human_review_completed"] is False and
            recorder["ffmpeg_exit_code"] == recorder["ffprobe_exit_code"] == 0 and
            recorder["format_duration_seconds"] == "600.000000" and
            recorder["frame_pts_by_stream"]["0"]["count"] == 12656 and
            raw["sha256"] ==
            "7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F" and
            Path(raw["path"]).stat().st_size == raw["bytes"] and
            session["ok"] is True and session["shutdown"]["ok"] is True and
            session["shutdown"]["cleanup_proven"] is True,
            "sealed recorder identity; video SHA reported, not rehashed or reviewed")
    print("E2-05 a02 candidate facts GREEN; production trace, death, selector and media remain unproven")


if __name__ == "__main__":
    main()
