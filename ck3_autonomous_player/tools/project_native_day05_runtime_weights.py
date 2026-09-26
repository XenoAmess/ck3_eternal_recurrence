#!/usr/bin/env python3
"""Project the immutable attempt-066 day-05 native random-list weight receipt.

This reads the original bridge response and same-frame v3 facts. It does not
start CK3, change a save, or promote the phase evaluator's fidelity gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.simulation.combat_core import DrawState, weighted_choice_index
from xar_autoplayer.simulation.phase_event_evaluator import (
    PhaseEventTrialState,
    _DrawTape,
    _knight_increase_prowess_chance,
    _maim_random,
)

EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
DLL_SHA256 = "03233A863F68D31FF123037A711CC22D7C489612E5C212145FB28B0650614F6B"
SOURCE_SHA256 = "695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885"
V3_SHA256 = "45F90F25BD13934083B53C7F83603DCEA8B699633EE77403244AA00C1380A964"
BEGIN_SHA256 = "019D783A6F43E1FD54600743FD55100AF7223E64C0FACF4F61040FD80E7C621A"
FINISH_SHA256 = "069584BF9134BA8949D5AB47ED36C925ADFD774DF10C5DA0055B1703BFB27AFF"
EXPECTED = {
    8: ("knight_increase_prowess_chance_effect", [54, 30, 10], 0),
    15: ("maimed_in_battle_effect", [4, 2, 4, 4], 0),
    49: ("safe_wound_treatment_effect", [40, 50], 1),
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def validate_weight_record(row: dict, nodes: list[dict]) -> dict:
    """Bind one picker row to the executed AST child and native draw."""

    token = row["effect_node_identity_token"]
    root = [n for n in nodes if n["node_identity_token"] == token]
    assert len(root) == 1 and root[0]["node_vtable_rva"] == 0x44782B0
    call = root[0]["call_index"]
    effect, expected_weights, expected_index = EXPECTED[call]
    assert row["side_index"] == root[0]["side_index"] == 1
    assert row["native_event_load_index"] == root[0]["native_event_load_index"] == 10
    weights = row["weights"]
    assert weights == expected_weights
    assert row["entry_count"] == len(weights) == len(row["entry_node_identity_tokens"])
    assert row["pick_count"] == 1
    assert bytes.fromhex(row["weights_bytes_hex"]) == struct.pack(
        "<" + "i" * len(weights), *weights
    )
    selected_tokens = row["selected_entry_identity_tokens"]
    assert len(selected_tokens) == 1
    selected = row["entry_node_identity_tokens"].index(selected_tokens[0])
    assert selected == expected_index
    children = [n for n in nodes if n["parent_node_identity_token"] == token]
    assert len(children) == 1
    assert children[0]["node_vtable_rva"] == 0x4478388
    assert children[0]["node_identity_token"] == selected_tokens[0]
    draw, after_one = DrawState(
        row["child_counter_before"], row["child_salt_before"]
    ).draw31()
    assert after_one.counter == children[0]["counter_before"]
    assert children[0]["counter_after"] == row["child_counter_after"]
    assert row["child_salt_before"] == row["child_salt_after"] == 0
    assert weighted_choice_index(tuple(weights), draw) == selected
    positive_total = sum(max(weight, 0) for weight in weights)
    return {
        "call_index": call,
        "effect": effect,
        "side_index": row["side_index"],
        "native_event_load_index": row["native_event_load_index"],
        "effect_node_identity_token": token,
        "entry_node_identity_tokens": row["entry_node_identity_tokens"],
        "selected_entry_identity_token": selected_tokens[0],
        "weights_native_int32": weights,
        "weights_bytes_hex": row["weights_bytes_hex"],
        "positive_weight_total": positive_total,
        "child_counter_before": row["child_counter_before"],
        "selection_draw31": draw,
        "threshold": draw * positive_total // (1 << 31),
        "selected_source_order_index": selected,
        "child_counter_after": row["child_counter_after"],
    }


def project(attempt: Path, game_exe: Path, bridge_dll: Path, source_save: Path) -> dict:
    response_dir = attempt / "ck3-output/interactive-requests-responses"
    paths = {
        "v3": response_dir / "004-v3.json",
        "begin": response_dir / "005-begin.json",
        "finish": response_dir / "007-finish.json",
        "session_result": attempt / "ck3-output/session-result.json",
    }
    hashes = {name: digest(path) for name, path in paths.items()}
    assert hashes["v3"] == V3_SHA256
    assert hashes["begin"] == BEGIN_SHA256
    assert hashes["finish"] == FINISH_SHA256
    assert digest(game_exe) == EXE_SHA256
    assert digest(bridge_dll) == DLL_SHA256
    assert digest(source_save) == SOURCE_SHA256

    begin = json.loads(paths["begin"].read_text(encoding="utf-8"))
    begin_request = json.loads(
        (attempt / "ck3-output/interactive-requests/005-begin.json").read_text(
            encoding="utf-8"
        )
    )
    assert begin_request["capture_runtime_random_list_weights"] is True
    assert begin["result"] == "CALL_COMPLETED"
    assert begin["body"]["status"] == "armed" and begin["body"]["accepted"] is True
    assert begin["body"]["combat_id"] == 16777218
    assert begin["body"]["managed_daily_sequence_token"] == 66005
    finish = json.loads(paths["finish"].read_text(encoding="utf-8"))
    assert finish["result"] == "CALL_COMPLETED"
    body = finish["body"]
    assert body["status"] == "bounded_trace_available"
    assert body["combat_id"] == 16777218
    trace = body["managed_trace"]["trace"]
    assert trace["failure_flags"] == 0 and trace["record_count"] == 7
    assert (trace["records"][0]["native_date_raw"], trace["records"][-1]["native_date_raw"]) == (
        53146344, 53146368
    )
    runtime = trace["runtime_random_list_weights"]
    assert runtime["status"] == "captured" and runtime["count"] == 3
    projections = [
        validate_weight_record(row, trace["effect_node_draws"])
        for row in runtime["records"]
    ]
    assert [row["call_index"] for row in projections] == list(EXPECTED)

    v3 = json.loads(paths["v3"].read_text(encoding="utf-8"))
    contexts = v3["body"]["combat_simulation_inputs"]["phase_event_inputs"][
        "evaluation_contexts"
    ]
    context = next(row for row in contexts if row["root_character_id"] == 34333)
    growth = PhaseEventTrialState.from_context(context)
    growth.selected_enemy_character_id = 47032
    _knight_increase_prowess_chance(
        growth, _DrawTape.from_value([projections[0]["selection_draw31"]]),
        target="selected_enemy_knight",
    )
    growth_weights = growth.transition_log[0]["weights_source_order"]
    assert growth_weights == [weight * 100000 for weight in projections[0]["weights_native_int32"]]
    assert growth.transition_log[0]["selected_branch"] == "no_op"
    maim = PhaseEventTrialState.from_context(context)
    _maim_random(maim, _DrawTape.from_value([projections[1]["selection_draw31"]]))
    maim_weights = maim.transition_log[0]["weights_source_order"]
    assert maim_weights == [weight * 100000 for weight in projections[1]["weights_native_int32"]]
    assert maim.transition_log[0]["selected_branch"] == "one_legged_then_wound"
    selected = next(
        row for row in context["candidate_rows"] if row["character_id"] == 47032
    )["selected_enemy_knight_refs"]
    assert selected["selected_enemy_knight.skills.learning_raw"] == 300000
    assert selected["selected_enemy_knight.dynasty.perks.warfare_legacy_3"] is False
    blade_facts = selected["selected_enemy_knight.traits_and_culture_for_blademaster"]
    assert blade_facts["lifestyle_blademaster_xp_raw"] == 0
    assert all(
        not any(value) if isinstance(value, list) else value is False
        for key, value in blade_facts.items()
        if key != "lifestyle_blademaster_xp_raw"
    )
    session = json.loads(paths["session_result"].read_text(encoding="utf-8"))
    assert session["shutdown"]["cleanup_proven"] is True
    assert session["shutdown"]["job_active_processes_final"] == 0
    return {
        "schema": "ck3.native_day05_runtime_random_list_weights.v1",
        "game_executable_sha256": EXE_SHA256,
        "bridge_dll_sha256": DLL_SHA256,
        "source_save_sha256": SOURCE_SHA256,
        "raw_response_sha256": hashes,
        "capture_status": body["status"],
        "capture_failure_flags": trace["failure_flags"],
        "combat_id": body["combat_id"],
        "source_date_raw": 53146344,
        "next_date_raw": 53146368,
        "choices": projections,
        "simulator_growth_weights_raw": growth_weights,
        "simulator_maim_weights_raw": maim_weights,
        "simulator_growth_and_maim_equal_runtime_weights": True,
        "safe_wound_treatment_model_status": "not_in_phase_event_evaluator_v3_context",
        "day26_growth_runtime_weights_observed": False,
        "full_effect_feedback_or_probability_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", required=True, type=Path)
    parser.add_argument("--game-exe", required=True, type=Path)
    parser.add_argument("--bridge-dll", required=True, type=Path)
    parser.add_argument("--source-save", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), f"refusing to overwrite {args.output}"
    result = project(args.attempt_root, args.game_exe, args.bridge_dll, args.source_save)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
