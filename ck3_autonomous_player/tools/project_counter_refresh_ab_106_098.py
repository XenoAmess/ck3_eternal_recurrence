#!/usr/bin/env python3
"""Compare paused-frame counter inputs before and after the 098/106 reinforcement day."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from project_advantage_reinforcement_ab_106_098 import project as validate_trace_pair


FROZEN = {
    "098": {
        "before": "2244E1144D7F5708B19BD2DE50311BCCA38481EFD0BC98165FC48AEA8C0602AA",
        "after": "236E67C10CFABBABEDE2822A40074458ABF8EFCA019CE54A3C88CC669EA217EC",
    },
    "106": {
        "before": "77C2084B8638598A805434CDE4ACA76EA2BE5635282C338550294A2C075FFE2C",
        "after": "6D024AD861F07DF056D2B7118E2C0607B5E52A3CC7F1DC6F6AC858C86919198E",
    },
}


def _control(root: Path, number: str, moment: str) -> dict:
    relative = f"ck3-output/interactive-requests-responses/c{number}-{moment}-control.json"
    raw = (root / relative).read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    if actual != FROZEN[number][moment]:
        raise ValueError(f"{relative}: SHA differs")
    response = json.loads(raw)
    body = response["body"]
    battle = body["battle_control_snapshot"]
    counter = battle["active_counter_inputs_v1"]
    expected_date = 53146488 if moment == "before" else 53146512
    if (response["result"] != "CALL_COMPLETED" or body["accepted"] is not True
            or battle["combat_id"] != 16777218
            or battle["observed_date_raw"] != expected_date
            or counter["status"] != "available" or counter["class_count"] != 13
            or counter["source_combat_id"] != 16777218
            or len(counter["sides"]) != 2):
        raise ValueError(f"{number} {moment}: paused-frame counter input differs")
    return counter


def project(attempt_106: Path, attempt_098: Path) -> dict:
    prior = validate_trace_pair(attempt_106, attempt_098)
    controls = {
        number: {moment: _control(root, number, moment)
                 for moment in ("before", "after")}
        for number, root in (("098", attempt_098), ("106", attempt_106))
    }
    for moment in ("before", "after"):
        if controls["098"][moment]["sides"] != controls["106"][moment]["sides"]:
            raise ValueError(f"{moment}: same-source side entries differ")
    before = controls["106"]["before"]["sides"]
    after = controls["106"]["after"]["sides"]
    first = before[0]["men_at_arms_entries"]
    second = after[0]["men_at_arms_entries"]
    if (len(first) != 18 or len(second) != 24
            or len(before[1]["men_at_arms_entries"]) != 14
            or len(after[1]["men_at_arms_entries"]) != 14
            or any(item["native_carmy_id"] == 22 for item in first)
            or [item["regiment_id"] for item in second if item["native_carmy_id"] == 22]
               != [176, 177, 179, 180, 181, 182]
            or prior["comparison"]["join_full_side0_entry_counts"] != [27, 40]
            or prior["gates"]["overall"] != "GREEN"):
        raise ValueError("paused next frame does not expose incoming Army 22")
    return {
        "schema": "ck3.counter_inputs_reinforcement_frame_refresh_ab_106_098.v1",
        "trace_pair_schema": prior["schema"],
        "trace_pair_evidence_sha256": prior["evidence_sha256"],
        "control_response_sha256": FROZEN,
        "before_date_raw": 53146488,
        "after_date_raw": 53146512,
        "same_source_counter_entries_equal": True,
        "before_side_maa_entry_counts": [len(side["men_at_arms_entries"]) for side in before],
        "after_side_maa_entry_counts": [len(side["men_at_arms_entries"]) for side in after],
        "joined_army_id": 22,
        "joined_army_maa_regiment_ids_in_after_frame": [
            item["regiment_id"] for item in second if item["native_carmy_id"] == 22],
        "native_join_full_side0_entry_counts": [27, 40],
        "gates": {"before_after_frame_binding": "GREEN",
                  "same_source_098_106": "GREEN",
                  "after_frame_joined_army_visible": "GREEN", "overall": "GREEN"},
        "scope": "paused_after_frame_input_refresh_only_not_future_join_prediction",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-106", required=True, type=Path)
    parser.add_argument("--attempt-098", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = project(args.attempt_106, args.attempt_098)
    raw = (json.dumps(result, indent=2) + "\n").encode()
    if args.expected is not None and args.expected.read_bytes() != raw:
        raise ValueError("frozen 106/098 counter refresh projection differs")
    if args.output is None:
        print(raw.decode(), end="")
    else:
        with args.output.open("xb") as stream:
            stream.write(raw)
    if args.check and result["gates"]["overall"] != "GREEN":
        raise SystemExit("106/098 counter refresh gate RED")


if __name__ == "__main__":
    main()
