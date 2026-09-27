"""Read-only, hash-bound projection of CK3 1.19.0.6 attempt 098.

The fixture is a projection of observed native output and a conditional
recalculation, not a calibrated active-battle forecast.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
from xar_autoplayer.simulation.combat_core import FIXED_SCALE, fixed_div, fixed_mul

DEFAULT_ATTEMPT = Path(
    r"D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-output-attempt-098"
)
FIXTURE = ROOT / "ck3_autonomous_player" / "src" / "xar_autoplayer" / "simulation" / "data" / "ck3_1_19_0_6_episode01_counter_output_098_projection.json"
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
DLL_SHA = "ABEE0A5AD16347A9EA2F10454D111A769CEDB84E343010792619CBB27A4CD858"
RESPONSE_SHA = {
    "before-control": "2244E1144D7F5708B19BD2DE50311BCCA38481EFD0BC98165FC48AEA8C0602AA",
    "trace-finish": "6B158A07A6071D058DE6F3E8994CA0065F09B2311EF79004EB1DDD445B1B8198",
    "after-control": "236E67C10CFABBABEDE2822A40074458ABF8EFCA019CE54A3C88CC669EA217EC",
}
JOIN_COLUMNS = (
    "regiment_id", "army_id", "bucket", "bucket_index", "starting_raw",
    "current_raw", "soft_raw", "effective_damage_raw", "effective_toughness_raw",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_response(attempt: Path, name: str) -> dict:
    path = attempt / "ck3-output" / "interactive-requests-responses" / f"c098-{name}.json"
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    require(actual == RESPONSE_SHA[name], f"{name} bytes SHA-256 drift: {actual}")
    response = json.loads(raw)
    require(response.get("result") == "CALL_COMPLETED", f"{name} not completed")
    return response["body"]


def indexed_maa(control: dict, side_index: int) -> dict[int, dict]:
    side = control["attacker" if side_index == 0 else "defender"]
    result = {row["regiment_id"]: row for row in side["men_at_arms_entries"]}
    require(len(result) == len(side["men_at_arms_entries"]), "duplicate MAA regiment ID")
    return result


def indexed_counter(control: dict, side_index: int) -> dict[int, dict]:
    census = control["active_counter_inputs_v1"]
    require(census["status"] == "available" and census["operand_census_complete"] is True,
            "counter census unavailable")
    row = census["sides"][side_index]
    require(row["side_index"] == side_index, "counter side order drift")
    return {item["regiment_id"]: item for item in row["men_at_arms_entries"]}


def join_entries(boundary: dict, side_index: int) -> tuple[dict[int, dict], dict]:
    side = boundary["sides"][side_index]
    entries = [dict(zip(JOIN_COLUMNS, row, strict=True)) for row in side["entries"]]
    result = {row["regiment_id"]: row for row in entries if row["bucket"] == 1}
    require(len(result) == sum(row["bucket"] == 1 for row in entries), "duplicate join MAA ID")
    return result, side


def predict_retention(
    current: tuple[dict[int, int], dict[int, int]],
    meta: tuple[dict[int, dict], dict[int, dict]],
    context: tuple[int, int],
    class_count: int,
) -> tuple[list[int], list[int]]:
    """Re-evaluate combat_input.dynamic_counter_retention_by_class_raw math."""
    predicted: list[list[int]] = []
    for side in (0, 1):
        own_chunks = [0] * class_count
        pressure = [0] * class_count
        for regiment_id, current_raw in current[side].items():
            row = meta[side][regiment_id]
            if row["status"] != "available" or current_raw <= 0:
                continue
            cls = row["class_index"]
            own_chunks[cls] += fixed_div(
                current_raw, row["stack_size_soldiers"] * FIXED_SCALE
            )
        for regiment_id, current_raw in current[1 - side].items():
            row = meta[1 - side][regiment_id]
            if row["status"] != "available" or current_raw <= 0:
                continue
            chunk = fixed_div(current_raw, row["stack_size_soldiers"] * FIXED_SCALE)
            for target in row["targets"]:
                cls = target["class_index"]
                pressure[cls] += fixed_mul(
                    fixed_mul(chunk, target["effectiveness_raw"]), context[side]
                )
        vector = []
        for cls in range(class_count):
            if own_chunks[cls] <= 0:
                vector.append(FIXED_SCALE)
            else:
                ratio = fixed_div(fixed_div(pressure[cls], own_chunks[cls]), 200_000)
                vector.append(FIXED_SCALE - fixed_mul(min(FIXED_SCALE, ratio), 90_000))
        predicted.append(vector)
    return predicted[0], predicted[1]


def project(attempt: Path) -> dict:
    freeze = json.loads((attempt / "input-freeze.json").read_text(encoding="utf-8"))
    require(freeze["exe_sha256"].upper() == EXE_SHA, "EXE provenance drift")
    require(freeze["bridge"]["sha256"].upper() == DLL_SHA, "DLL provenance drift")
    bridge_path = Path(freeze["bridge"]["path"])
    require(hashlib.sha256(bridge_path.read_bytes()).hexdigest().upper() == DLL_SHA,
            "frozen DLL bytes drift")
    require(freeze["capture_runtime_counter_output"] is True, "counter capture disabled")
    before_body = load_response(attempt, "before-control")
    finish = load_response(attempt, "trace-finish")
    after_body = load_response(attempt, "after-control")
    before = before_body["battle_control_snapshot"]
    after = after_body["battle_control_snapshot"]
    trace = finish["managed_trace"]["trace"]
    native = trace["runtime_counter_output"]
    joins = trace["runtime_join_full_entries"]
    require(trace["failure_flags"] == 0 and native["pair_complete"] is True,
            "trace/counter capture incomplete")
    require(native["count"] == 2 and [s["side_index"] for s in native["sides"]] == [0, 1],
            "counter side pair drift")
    require(before["combat_id"] == after["combat_id"] == finish["combat_id"],
            "CombatID drift")
    require(after["observed_date_raw"] - before["observed_date_raw"] == 24,
            "not exactly one day")
    require(before["phase_day"] + 1 == after["phase_day"], "phase day drift")
    require(joins["status"] == "captured" and joins["count"] == 2,
            "join full entries missing")
    require(tuple(joins["entry_columns"]) == JOIN_COLUMNS, "join column order drift")
    boundary = joins["boundaries"][1]
    require(boundary["boundary"] == 1 and boundary["joined_side_index"] == 0,
            "post-join boundary drift")
    require(boundary["combat_id"] == after["combat_id"], "join CombatID drift")
    require(boundary["native_date_raw"] == after["observed_date_raw"],
            "join date drift")

    current = []
    meta = []
    before_rows = []
    after_rows = []
    mapping = []
    for side in (0, 1):
        joined, joined_side = join_entries(boundary, side)
        earlier = indexed_maa(before, side)
        later = indexed_maa(after, side)
        metadata = indexed_counter(after, side)
        require(set(joined) == set(later) == set(metadata),
                f"side {side} post-join/census regiment identity mismatch")
        require(len(joined) == native["sides"][side]["countered_entry_count"],
                f"side {side} native countered entry count mismatch")
        require(set(earlier).issubset(joined), f"side {side} lost pre-join regiment ID")
        owner_by_army = {
            row["native_carmy_id"]: row["owner_character_id"]
            for row in after["attacker" if side == 0 else "defender"]["ordered_armies"]
        }
        side_rows = []
        for regiment_id, item in joined.items():
            observed = later[regiment_id]
            classification = metadata[regiment_id]
            require(item["army_id"] == observed["native_carmy_id"]
                    == classification["native_carmy_id"],
                    f"regiment {regiment_id} army identity drift")
            require(item["army_id"] in owner_by_army, f"regiment {regiment_id} owner missing")
            require(owner_by_army[item["army_id"]] == observed["owner_character_id"],
                    f"regiment {regiment_id} owner drift")
            side_rows.append({
                "regiment_id": regiment_id,
                "army_id": item["army_id"],
                "owner_character_id": owner_by_army[item["army_id"]],
                "class_index": classification["class_index"],
                "class_status": classification["status"],
                "before_current_raw": (
                    earlier[regiment_id]["current_fighting_raw"]
                    if regiment_id in earlier else None
                ),
                "post_join_current_raw": item["current_raw"],
                "post_tick_current_raw": observed["current_fighting_raw"],
            })
            if regiment_id in earlier:
                old_meta = indexed_counter(before, side)[regiment_id]
                for key in ("status", "class_index", "stack_size_soldiers", "targets"):
                    require(old_meta[key] == classification[key],
                            f"regiment {regiment_id} counter metadata drift: {key}")
        side_rows.sort(key=lambda row: row["regiment_id"])
        mapping.append(side_rows)
        current.append({k: v["current_raw"] for k, v in joined.items()})
        before_rows.append({k: v["current_fighting_raw"] for k, v in earlier.items()})
        after_rows.append({k: v["current_fighting_raw"] for k, v in later.items()})
        meta.append(metadata)
        require(set(joined_side["army_ids"]) == set(owner_by_army),
                f"side {side} join/after army roster mismatch")
    contexts = after["active_counter_inputs_v1"]["contexts"]
    context = tuple(row["context_scale_raw"] for row in contexts)
    require(context == tuple(row["context_raw"] for row in native["sides"]),
            "native/census counter context drift")
    count = native["sides"][0]["class_count"]
    require(count == native["sides"][1]["class_count"] == 13, "class count drift")
    for side in (0, 1):
        require(native["sides"][side]["countering_entry_count"] == len(current[1 - side]),
                f"side {side} native countering entry count mismatch")
    predicted = predict_retention(tuple(current), tuple(meta), context, count)
    before_predicted = predict_retention(tuple(before_rows), tuple(meta), context, count)
    after_predicted = predict_retention(tuple(after_rows), tuple(meta), context, count)
    rows = []
    for side in (0, 1):
        observed = native["sides"][side]["retention_raw"]
        rows.append({
            "side_index": side,
            "primary_owner_character_id": after["attacker" if side == 0 else "defender"]["primary_participant_character_id"],
            "context_raw": context[side],
            "before_maa_count": len(before_rows[side]),
            "post_join_maa_count": len(current[side]),
            "after_maa_count": len(after_rows[side]),
            "new_regiment_ids": sorted(set(current[side]) - set(before_rows[side])),
            "native_retention_raw": observed,
            "post_join_model_retention_raw": predicted[side],
            "before_model_retention_raw": before_predicted[side],
            "after_model_retention_raw": after_predicted[side],
            "post_join_model_matches_native": predicted[side] == observed,
            "mismatch_class_indices": [i for i in range(count) if predicted[side][i] != observed[i]],
            "entry_mapping": mapping[side],
        })
    return {
        "fixture_kind": "ck3-1.19.0.6-active-counter-output-098-cross-check",
        "source": {
            "attempt": 98, "game_version": "1.19.0.6", "exe_sha256": EXE_SHA,
            "bridge_sha256": DLL_SHA, "response_sha256": RESPONSE_SHA,
            "combat_id": before["combat_id"],
            "before_date_raw": before["observed_date_raw"],
            "after_date_raw": after["observed_date_raw"],
            "before_phase_day": before["phase_day"],
            "after_phase_day": after["phase_day"],
            "trace_failure_flags": trace["failure_flags"],
            "original_trace_ready": trace["readiness"]["original_trace_ready"],
            "full_mutable_transition_bundle_complete": trace["readiness"]["full_mutable_transition_bundle_complete"],
        },
        "join": {
            "incoming_army_id": boundary["incoming_army_id"],
            "joined_side_index": boundary["joined_side_index"],
            "boundary": boundary["boundary"],
        },
        "counter": {
            "source": native["source"], "pair_complete": native["pair_complete"],
            "class_count": count, "scale": FIXED_SCALE, "sides": rows,
        },
        "interpretation": {
            "post_join_model_is_conditional": True,
            "whole_battle_win_probability": None,
            "active_resume_input_ready": False,
        },
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
        "post_join_matches": [x["post_join_model_matches_native"] for x in projection["counter"]["sides"]],
        "mismatch_classes": [x["mismatch_class_indices"] for x in projection["counter"]["sides"]],
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"counter output 098 projection RED: {exc}", file=sys.stderr)
        raise SystemExit(1)
