"""Hash-bound read-only check of the next-day native counter pair (attempt 100).

The vector comparison is conditional on the observed paused census. It does
not turn an active battle into a calibrated whole-battle forecast.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from project_active_counter_output_098 import (
    DLL_SHA,
    EXE_SHA,
    FIXED_SCALE,
    indexed_counter,
    indexed_maa,
    predict_retention,
    require,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTEMPT = Path(
    r"D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-100"
)
FIXTURE = (
    ROOT / "ck3_autonomous_player/src/xar_autoplayer/simulation/data/"
    "ck3_1_19_0_6_episode01_counter_output_100_projection.json"
)
SOURCE_SAVE_SHA = "E6155C9C127EC3D1D758468653E8ABC3458A96B50EA053E303FDCCAD18C0B731"
SOURCE_RECEIPT_SHA = "A68C4D38CC14B11FCB4078E8D9074C9EE5793B0EF20674199327E6D0A983B415"
RESPONSE_SHA = {
    "before-control": "428B64DEA74202B5C5A2835E3079964C2227EC83946B3BB7A666E6D3CAB364EF",
    "trace-finish": "644580703FE18769B081CCEBCC96B473BF459E4489835777117D6B070014FBFC",
    "after-control": "14055050DBA2548FFEB71B14CF4D32CFC1C55F7170D345C1EA5D1C8415EEC089",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_response(attempt: Path, name: str) -> dict:
    path = attempt / "ck3-output/interactive-requests-responses" / f"c100-{name}.json"
    require(sha(path) == RESPONSE_SHA[name], f"{name} bytes SHA-256 drift")
    response = json.loads(path.read_bytes())
    require(response.get("result") == "CALL_COMPLETED", f"{name} not completed")
    return response["body"]


def project(attempt: Path) -> dict:
    freeze = json.loads((attempt / "input-freeze.json").read_text(encoding="utf-8"))
    require(freeze["exe_sha256"].upper() == EXE_SHA, "EXE provenance drift")
    require(freeze["bridge"]["sha256"].upper() == DLL_SHA, "DLL provenance drift")
    require(sha(Path(freeze["bridge"]["path"])) == DLL_SHA, "DLL actual bytes drift")
    require(freeze["source"]["sha256"].upper() == SOURCE_SAVE_SHA,
            "source save declaration drift")
    require(sha(Path(freeze["source"]["path"])) == SOURCE_SAVE_SHA,
            "source save actual bytes drift")
    require(freeze["paired_receipt"]["sha256"].upper() == SOURCE_RECEIPT_SHA,
            "source receipt declaration drift")
    require(sha(Path(freeze["paired_receipt"]["path"])) == SOURCE_RECEIPT_SHA,
            "source receipt actual bytes drift")
    require(freeze["capture_runtime_counter_output"] is True,
            "counter output capture was not requested")

    before_body = load_response(attempt, "before-control")
    finish = load_response(attempt, "trace-finish")
    after_body = load_response(attempt, "after-control")
    before = before_body["battle_control_snapshot"]
    after = after_body["battle_control_snapshot"]
    trace = finish["managed_trace"]["trace"]
    native = trace["runtime_counter_output"]
    require(trace["failure_flags"] == 0, "bounded trace failed")
    require(native["pair_complete"] is True and native["count"] == 2,
            "native counter output pair incomplete")
    require([row["side_index"] for row in native["sides"]] == [0, 1],
            "native side order drift")
    require(before["combat_id"] == after["combat_id"] == finish["combat_id"] == 16777218,
            "CombatID drift")
    require(before["observed_date_raw"] == 53146512 and
            after["observed_date_raw"] == 53146536,
            "date split drift")
    require(before["phase_day"] == 8 and after["phase_day"] == 9,
            "main phase day drift")
    require(native["sides"][0]["class_count"] ==
            native["sides"][1]["class_count"] == 13, "counter class count drift")

    before_current: list[dict[int, int]] = []
    after_current: list[dict[int, int]] = []
    before_meta: list[dict[int, dict]] = []
    after_meta: list[dict[int, dict]] = []
    entry_mappings: list[list[dict]] = []
    roster_same: list[bool] = []
    metadata_same: list[bool] = []
    for side in (0, 1):
        old_entries = indexed_maa(before, side)
        new_entries = indexed_maa(after, side)
        old_meta = indexed_counter(before, side)
        new_meta = indexed_counter(after, side)
        require(set(old_entries) == set(old_meta), f"side {side} before census mismatch")
        require(set(new_entries) == set(new_meta), f"side {side} after census mismatch")
        require(len(old_entries) == native["sides"][side]["countered_entry_count"],
                f"side {side} native countered count differs from paused entry count")
        before_current.append({ident: item["current_fighting_raw"]
                               for ident, item in old_entries.items()})
        after_current.append({ident: item["current_fighting_raw"]
                              for ident, item in new_entries.items()})
        before_meta.append(old_meta)
        after_meta.append(new_meta)
        same_ids = set(old_entries) == set(new_entries)
        roster_same.append(same_ids)
        stable = same_ids and all(
            all(old_meta[ident][key] == new_meta[ident][key]
                for key in ("status", "class_index", "stack_size_soldiers", "targets"))
            for ident in old_entries
        )
        metadata_same.append(stable)
        entries = []
        for ident in sorted(old_entries):
            row = old_entries[ident]
            meta = old_meta[ident]
            entries.append({
                "regiment_id": ident,
                "native_carmy_id": row["native_carmy_id"],
                "owner_character_id": row["owner_character_id"],
                "class_index": meta["class_index"],
                "stack_size_soldiers": meta["stack_size_soldiers"],
                "targets": meta["targets"],
                "before_current_raw": row["current_fighting_raw"],
                "after_current_raw": (new_entries[ident]["current_fighting_raw"]
                                      if ident in new_entries else None),
            })
        entry_mappings.append(entries)
    for side in (0, 1):
        require(native["sides"][side]["countering_entry_count"] ==
                len(before_current[1 - side]),
                f"side {side} native countering count differs from paused entry count")
    before_context = tuple(
        row["context_scale_raw"] for row in before["active_counter_inputs_v1"]["contexts"]
    )
    after_context = tuple(
        row["context_scale_raw"] for row in after["active_counter_inputs_v1"]["contexts"]
    )
    native_context = tuple(row["context_raw"] for row in native["sides"])
    require(before_context == native_context, "paused/native counter context drift")
    predicted_before = predict_retention(tuple(before_current), tuple(before_meta),
                                         native_context, 13)
    predicted_after = predict_retention(tuple(after_current), tuple(after_meta),
                                        native_context, 13)
    sides = []
    for side in (0, 1):
        observed = native["sides"][side]["retention_raw"]
        sides.append({
            "side_index": side,
            "primary_owner_character_id": before[
                "attacker" if side == 0 else "defender"
            ]["primary_participant_character_id"],
            "context_raw": native_context[side],
            "native_countered_entry_count": native["sides"][side]["countered_entry_count"],
            "native_countering_entry_count": native["sides"][side]["countering_entry_count"],
            "same_regiment_ids_before_after": roster_same[side],
            "same_counter_metadata_before_after": metadata_same[side],
            "native_retention_raw": observed,
            "before_model_retention_raw": predicted_before[side],
            "after_model_retention_raw": predicted_after[side],
            "before_model_matches_native": predicted_before[side] == observed,
            "mismatch_class_indices": [i for i in range(13)
                                       if predicted_before[side][i] != observed[i]],
            "entry_mapping": entry_mappings[side],
        })
    return {
        "fixture_kind": "ck3-1.19.0.6-active-counter-output-100-cross-check",
        "source": {"attempt": 100, "source_checkpoint_attempt": 99,
                   "exe_sha256": EXE_SHA, "bridge_sha256": DLL_SHA,
                   "source_save_sha256": SOURCE_SAVE_SHA,
                   "source_receipt_sha256": SOURCE_RECEIPT_SHA,
                   "response_sha256": RESPONSE_SHA,
                   "combat_id": before["combat_id"],
                   "before_date_raw": before["observed_date_raw"],
                   "after_date_raw": after["observed_date_raw"],
                   "before_phase_day": before["phase_day"],
                   "after_phase_day": after["phase_day"],
                   "trace_failure_flags": trace["failure_flags"],
                   "original_trace_ready": trace["readiness"]["original_trace_ready"],
                   "full_mutable_transition_bundle_complete": trace["readiness"]["full_mutable_transition_bundle_complete"]},
        "trace": {"post_counter_attack_raw": [trace["post_counter_attack"]["side0_raw"],
                                              trace["post_counter_attack"]["side1_raw"]],
                  "outgoing_damage_raw": [trace["outgoing_damage"]["side0_raw"],
                                          trace["outgoing_damage"]["side1_raw"]]},
        "counter": {"source": native["source"], "pair_complete": native["pair_complete"],
                    "class_count": 13, "scale": FIXED_SCALE,
                    "before_context_raw": before_context,
                    "after_context_raw": after_context,
                    "sides": sides},
        "interpretation": {"before_model_is_conditional": True,
                           "whole_battle_win_probability": None,
                           "active_resume_input_ready": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write-fixture", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    projection = project(args.attempt)
    rendered = json.dumps(projection, ensure_ascii=False, indent=2) + "\n"
    if args.write_fixture:
        FIXTURE.write_text(rendered, encoding="utf-8")
    elif args.check:
        require(FIXTURE.read_text(encoding="utf-8") == rendered,
                "checked-in projection drift")
    else:
        print(rendered, end="")
    print(json.dumps({
        "status": "checked" if args.check else "written" if args.write_fixture else "projected",
        "before_matches": [x["before_model_matches_native"]
                           for x in projection["counter"]["sides"]],
        "mismatch_classes": [x["mismatch_class_indices"]
                             for x in projection["counter"]["sides"]],
        "same_roster": [x["same_regiment_ids_before_after"]
                        for x in projection["counter"]["sides"]],
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"counter output 100 projection RED: {exc}", file=sys.stderr)
        raise SystemExit(1)
