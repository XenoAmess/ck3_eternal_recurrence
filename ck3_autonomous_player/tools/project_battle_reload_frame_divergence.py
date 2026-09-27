#!/usr/bin/env python3
"""Hash-bound comparison of continuous and freshly loaded day-12 combat frames."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from project_advantage_components_ab_104_100 import project as validate_reload_pair
from project_advantage_reinforcement_ab_106_098 import project as validate_direct_pair


SAVE_SHA = "E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731"
FROZEN = {
    "099_after": "FFE286DC1422A54A330A53F29BD4541512F9E75A4C0DE112584CFC934F2022B6",
    "099_save_receipt": "A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415",
    "100_before": "428B64DEA74202B5C5A2835E3079964C2227EC83946B3BB7A666E6D3CAB364EF",
    "104_before": "1B6C78931B72C749F71E948477E568012BF9B40475D4A6105E94C9D05DE71D0A",
    "106_after": "6D024AD861F07DF056D2B7118E2C0607B5E52A3CC7F1DC6F6AC858C86919198E",
}
BASE_FIELDS = (
    "combat_id", "observed_date_raw", "phase_day", "base_advantage_raw",
    "base_combat_width", "final_combat_width", "active_counter_inputs_v1",
)
CHANGED_ENTRY_FIELDS = {
    "attacker": {"effective_damage_raw": 17, "effective_toughness_raw": 24,
                 "entry_strength_raw": 22},
    "defender": {"effective_damage_raw": 12, "effective_toughness_raw": 14,
                 "effective_siege_raw": 3, "entry_strength_raw": 13},
}


def _load(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    if actual != expected_sha:
        raise ValueError(f"{path}: expected {expected_sha}, got {actual}")
    result = json.loads(raw)
    if not isinstance(result, dict) or result.get("result") != "CALL_COMPLETED":
        raise ValueError(f"{path}: response not complete")
    return result


def _control(root: Path, number: str, moment: str, name: str) -> dict:
    path = (root / "ck3-output/interactive-requests-responses" /
            f"c{number}-{moment}-control.json")
    response = _load(path, FROZEN[name])
    battle = response["body"]["battle_control_snapshot"]
    if (battle["combat_id"] != 16777218
            or battle["observed_date_raw"] != 53146512
            or battle["phase_day"] != 8
            or battle["active_counter_inputs_v1"]["status"] != "available"):
        raise ValueError(f"{name}: wrong battle frame")
    return battle


def _changes(continuous: dict, reloaded: dict) -> dict:
    changes = {}
    for side in ("attacker", "defender"):
        old = continuous[side]["men_at_arms_entries"]
        new = reloaded[side]["men_at_arms_entries"]
        if len(old) != len(new):
            raise ValueError(f"{side}: entry count differs")
        counts: dict[str, int] = {}
        for a, b in zip(old, new):
            if a["regiment_id"] != b["regiment_id"]:
                raise ValueError(f"{side}: regiment order differs")
            for field in sorted(set(a) | set(b)):
                if a.get(field) != b.get(field):
                    counts[field] = counts.get(field, 0) + 1
        if counts != CHANGED_ENTRY_FIELDS[side]:
            raise ValueError(f"{side}: effective entry changes differ: {counts}")
        old_without_entries = {k: v for k, v in continuous[side].items()
                               if k != "men_at_arms_entries"}
        new_without_entries = {k: v for k, v in reloaded[side].items()
                               if k != "men_at_arms_entries"}
        non_entry_changed = {key for key in set(old_without_entries) | set(new_without_entries)
                             if old_without_entries.get(key) != new_without_entries.get(key)}
        if non_entry_changed != {"side_strength_raw"}:
            raise ValueError(f"{side}: side fields differ: {non_entry_changed}")
        changes[side] = {
            "maa_entries": len(old), "entry_changed_field_counts": counts,
            "side_strength_raw_continuous": continuous[side]["side_strength_raw"],
            "side_strength_raw_reloaded": reloaded[side]["side_strength_raw"],
        }
    return changes


def project(roots: dict[str, Path]) -> dict:
    validate_direct_pair(roots["106"], roots["098"])
    validate_reload_pair(roots["104"], roots["100"])
    save_receipt = _load(
        roots["099"] / "ck3-output/interactive-requests-responses/c099-save-day12.json",
        FROZEN["099_save_receipt"])
    checkpoint = save_receipt["body"]["checkpoint"]
    saved_path = roots["099"] / "ck3-state/profile/save games/xar_checkpoint.ck3"
    if (checkpoint["status"] != "saved" or checkpoint["date_raw"] != 53146512
            or checkpoint["sha256"].upper() != SAVE_SHA
            or hashlib.sha256(saved_path.read_bytes()).hexdigest().upper() != SAVE_SHA):
        raise ValueError("099 day-12 save/receipt pairing differs")
    frames = {
        "099_after": _control(roots["099"], "099", "after", "099_after"),
        "100_before": _control(roots["100"], "100", "before", "100_before"),
        "104_before": _control(roots["104"], "104", "before", "104_before"),
        "106_after": _control(roots["106"], "106", "after", "106_after"),
    }
    continuous = frames["099_after"]
    reloaded = frames["100_before"]
    for first, second in (("099_after", "106_after"), ("100_before", "104_before")):
        for field in BASE_FIELDS + ("resolved_advantage_raw", "attacker", "defender"):
            if frames[first][field] != frames[second][field]:
                raise ValueError(f"{first}/{second}: {field} differs within paired condition")
    for field in BASE_FIELDS:
        if continuous[field] != reloaded[field]:
            raise ValueError(f"cross-condition {field} differs")
    if (continuous["resolved_advantage_raw"] != -1100000
            or reloaded["resolved_advantage_raw"] != -600000
            or continuous["attacker"]["side_strength_raw"] != 125474
            or reloaded["attacker"]["side_strength_raw"] != 120954
            or continuous["defender"]["side_strength_raw"] != 36020
            or reloaded["defender"]["side_strength_raw"] != 24640):
        raise ValueError("cross-condition cached advantage or side strength differs")
    changes = _changes(continuous, reloaded)
    return {
        "schema": "ck3.battle_fresh_load_frame_divergence_099_100_104_106.v1",
        "day12_save_sha256": SAVE_SHA,
        "control_response_sha256": FROZEN,
        "combat_id": 16777218,
        "date_raw": 53146512,
        "phase_day": 8,
        "continuous_pair": ["099_after", "106_after"],
        "fresh_load_pair": ["100_before", "104_before"],
        "counter_inputs_equal_across_all_four": True,
        "base_advantage_raw": continuous["base_advantage_raw"],
        "resolved_advantage_raw_continuous": -1100000,
        "resolved_advantage_raw_fresh_load": -600000,
        "sides": changes,
        "gates": {"paired_save_identity": "GREEN", "within_condition_repetition": "GREEN",
                  "cross_condition_difference": "GREEN", "overall": "GREEN"},
        "scope": "observed_frame_divergence_not_a_causal_attribution_to_serialization",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for number in ("098", "099", "100", "104", "106"):
        parser.add_argument(f"--attempt-{number}", required=True, type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    roots = {number: getattr(args, f"attempt_{number}")
             for number in ("098", "099", "100", "104", "106")}
    result = project(roots)
    raw = (json.dumps(result, indent=2) + "\n").encode()
    if args.expected is not None and args.expected.read_bytes() != raw:
        raise ValueError("frozen fresh-load divergence projection differs")
    if args.output is None:
        print(raw.decode(), end="")
    else:
        with args.output.open("xb") as stream:
            stream.write(raw)
    if args.check and result["gates"]["overall"] != "GREEN":
        raise SystemExit("fresh-load divergence gate RED")


if __name__ == "__main__":
    main()
