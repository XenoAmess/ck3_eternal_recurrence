"""Rebuild a paused CK3 knight's effectiveness from nine native modifier operands.

The new receipt must be an isolated, no-day-advance read of the same immutable
save as a previously accepted v2 receipt. A missing component is a RED, not 0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from project_native_knight_effectiveness_sources import project as project_sources


def _read(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest().upper()


def _body(attempt: Path, name: str) -> tuple[dict, str]:
    row, digest = _read(attempt / "ck3-output/interactive-requests-responses" / f"{name}.json")
    if row.get("result") != "CALL_COMPLETED":
        raise ValueError(f"request failed: {name}")
    return row["body"], digest


def _trunc_q100000(left: int, right: int) -> int:
    product = left * right
    return (abs(product) // 100_000) * (-1 if product < 0 else 1)


def project(attempt: Path, reference_attempt: Path, exe: Path) -> dict:
    source = project_sources(exe)
    checkpoint, checkpoint_sha = _read(attempt / "ck3-output/checkpoint-copy.json")
    reference, reference_sha = _read(reference_attempt / "ck3-output/checkpoint-copy.json")
    if (checkpoint["source"]["save"]["sha256"] != reference["source"]["save"]["sha256"]
            or checkpoint["source"]["date_raw"] != 53146488):
        raise ValueError("component receipt does not use the accepted day-11 save")
    preflight, preflight_sha = _read(attempt / "ck3-output/preflight.json")
    session, session_sha = _read(attempt / "ck3-output/session-result.json")
    if (preflight["game"]["sha256"] != source["exe_sha256"]
            or session["shutdown"]["cleanup_proven"] is not True):
        raise ValueError("exact-build or cleanup gate failed")
    before, before_sha = _body(attempt, "d11-before-snapshot")
    direct, direct_sha = _body(attempt, "d11-direct-stats-v2")
    v3, v3_sha = _body(attempt, "d11-direct-stats-v3")
    after, after_sha = _body(attempt, "d11-after-snapshot")
    old, old_sha = _body(reference_attempt, "d11-direct-stats-v2")
    if (not before["paused"] or not after["paused"]
            or before["date_raw"] != 53146488 or after["date_raw"] != 53146488
            or before["revision"] != after["revision"]
            or direct["status"] != "available"
            or direct["queried_revision"] != before["revision"]
            or direct["target_province_id"] != 2633
            or direct["combat_simulation_inputs"] !=
            v3["combat_simulation_inputs"]["base_inputs"]):
        raise ValueError("paused same-frame v2/v3 gate failed")
    current_base = direct["combat_simulation_inputs"]
    old_base = old["combat_simulation_inputs"]
    stripped = json.loads(json.dumps(current_base))
    rows = []
    for army in stripped["armies"]:
        for knight in army["knights"]["members"]:
            knight.pop("effectiveness_components")
    # The native 0x21D3F20 correction also fixes two commander roll fields
    # and one counter modifier that the old wrapper reader returned as zero.
    # Require these exact differences and reject every other changed input.
    corrections = (
        (1, ("commander", "battle_context", "effective_max_roll"), 10, 9),
        (1, ("commander", "battle_context", "effective_min_roll"), 0, 2),
        (3, ("owner", "counter_efficiency_raw"), 0, 25_000),
    )
    if ([army["army_id"] for army in stripped["armies"]] !=
            [16777221, 16777231, 27, 18]):
        raise ValueError("battle army identity changed")
    reader_changes = []
    baseline_equivalent = json.loads(json.dumps(stripped))
    for army_index, keys, before_value, after_value in corrections:
        old_node = old_base["armies"][army_index]
        new_node = stripped["armies"][army_index]
        equivalent_node = baseline_equivalent["armies"][army_index]
        for key in keys[:-1]:
            old_node, new_node, equivalent_node = (
                old_node[key], new_node[key], equivalent_node[key]
            )
        last = keys[-1]
        if old_node[last] != before_value or new_node[last] != after_value:
            raise ValueError("native modifier-reader correction drifted")
        equivalent_node[last] = before_value
        reader_changes.append({
            "army_id": stripped["armies"][army_index]["army_id"],
            "field": ".".join(keys),
            "before_raw": before_value,
            "after_raw": after_value,
        })
    if baseline_equivalent != old_base:
        raise ValueError("corrected reader changed an unaccounted battle input")
    names = [row["name"] for row in source["modifier_components_in_reader_order"]]
    for army in current_base["armies"]:
        for knight in army["knights"]["members"]:
            component = knight["effectiveness_components"]
            if component["status"] != "available":
                raise ValueError("knight effectiveness component read unavailable")
            modifiers = component["modifier_raw"]
            operands = component["operand_raw"]
            if len(modifiers) != 9 or len(operands) != 9 or operands[0] != 100_000:
                raise ValueError("knight effectiveness operand shape drifted")
            contributions = [_trunc_q100000(modifier, operand)
                             for modifier, operand in zip(modifiers, operands)]
            rebuilt = 100_000 + sum(contributions)
            if rebuilt != knight["knight_effectiveness_raw"]:
                raise ValueError(f"native knight effectiveness residual: {knight['character_id']}")
            rows.append({
                "army_id": army["army_id"], "character_id": knight["character_id"],
                "regiment_id": knight["source_regiment_id"],
                "effective_prowess": knight["prowess"],
                "component_names": names, "modifier_raw": modifiers,
                "operand_raw": operands, "contribution_raw": contributions,
                "base_raw": 100_000, "rebuilt_effectiveness_raw": rebuilt,
                "native_effectiveness_raw": knight["knight_effectiveness_raw"],
            })
    rows.sort(key=lambda row: (row["army_id"], row["regiment_id"]))
    if len(rows) != 24:
        raise ValueError("day-11 knight census drifted")
    return {
        "schema": "ck3.native_knight_effectiveness_component_parity.v1",
        "game_build": "1.19.0.6", "exe_sha256": source["exe_sha256"],
        "source_save_sha256": checkpoint["source"]["save"]["sha256"],
        "checkpoint_copy_sha256": checkpoint_sha,
        "reference_checkpoint_copy_sha256": reference_sha,
        "preflight_sha256": preflight_sha, "session_result_sha256": session_sha,
        "response_sha256": {"before": before_sha, "direct_v2": direct_sha,
                            "direct_v3": v3_sha, "after": after_sha,
                            "reference_v2": old_sha},
        "static_component_source": source,
        "knight_count": len(rows), "component_count_per_knight": 9,
        "all_rebuilt_effectiveness_equal_native": True,
        "v2_and_v3_base_inputs_equal": True,
        "prior_v2_deltas_limited_to_corrected_modifier_reader": True,
        "prior_v2_reader_corrections": reader_changes,
        "native_modifier_aggregator_reader_rva": "0x21D3F20",
        "prior_incorrect_inner_reader_rva": "0x20AB950",
        "knights": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--reference-attempt", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.attempt, args.reference_attempt, args.exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "knight_count": report["knight_count"]}))


if __name__ == "__main__":
    main()
