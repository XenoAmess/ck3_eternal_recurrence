#!/usr/bin/env python3
"""Verify a paused native random-list receipt and project its weighted draw.

The compiled list's base weights are directly observed; adjusted weights are
an explicit, conditional input until captured inside the dynamic selector.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import pefile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.simulation.combat_core import (
    DrawState, effect_child_state, weighted_choice_index,
)


GAME_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
WEIGHT_SCALE_RVA = 0x4594650  # 0x3BB6EE0 mulsd [rip + 0x9DD768]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--classification", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--conditional-weights", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    memory = json.loads(args.receipt.read_text(encoding="utf-8"))
    classification = json.loads(args.classification.read_text(encoding="utf-8"))
    assert digest(args.exe) == GAME_EXE_SHA256
    assert memory["game_executable_sha256"] == GAME_EXE_SHA256
    assert digest(args.classification) == memory["classification_sha256"]
    assert classification["trace_response_sha256"] == memory["trace_response_sha256"]
    assert classification["status"] == "bounded_trace_available"
    assert classification["failure_flags"] == 0
    assert len(classification["random_list_nodes"]) == 1
    node = classification["random_list_nodes"][0]
    root = node["random_list_node"]
    children = node["direct_children"]
    assert len(children) == 1
    assert root["node_identity_token"] == memory["node_identity_token"]
    assert root["node_vtable_rva"] == memory["node_vtable_rva"] == 0x44782B0
    assert root["counter_before"] == memory["node_counter_before"]
    assert root["counter_after"] == memory["node_counter_after"]
    assert children[0]["node_identity_token"] == memory["selected_entry_identity_token"]
    assert children[0]["node_vtable_rva"] == 0x4478388
    assert memory["entry_count"] == memory["weight_count"] == 3
    assert len(memory["entry_identity_tokens"]) == 3
    assert memory["selected_source_order_index"] == 0
    assert (memory["selected_entry_identity_token"].lower()
            == f"process-local-{memory['entry_identity_tokens'][0]}".lower())
    assert memory["weights_native_int32"] == [60, 30, 10]
    assert memory["static_total_native_int32"] == 100
    assert memory["flags_bc_bd"] == [0, 1]  # dynamic weights
    for name, expected in memory["raw_sha256"].items():
        assert digest(args.receipt.parent / name) == expected

    image = pefile.PE(str(args.exe), fast_load=True)
    scale = struct.unpack("<d", image.get_data(WEIGHT_SCALE_RVA, 8))[0]
    assert scale == 2.0**-31
    parent_draw, parent_after, child_state = effect_child_state(
        DrawState(root["counter_before"], root["salt_before"]), root["node_hash"]
    )
    assert parent_after.counter == root["counter_after"]
    assert parent_after.salt == root["salt_after"]
    selection_draw, child_after = child_state.draw31()
    assert child_after.counter == children[0]["counter_before"]
    assert child_after.salt == children[0]["salt_before"] == 0

    weights = tuple(int(part) for part in args.conditional_weights.split(","))
    assert len(weights) == memory["entry_count"]
    positive_sum = sum(max(0, weight) for weight in weights)
    assert positive_sum > 0
    threshold = int((float(selection_draw) * scale) * float(positive_sum))
    candidate = weighted_choice_index(weights, selection_draw)
    report = {
        "schema": "ck3.native_random_list_choice_projection.v2",
        "game_build": "1.19.0.6",
        "game_executable_sha256": GAME_EXE_SHA256,
        "receipt_sha256": digest(args.receipt),
        "classification_sha256": digest(args.classification),
        "trace_response_sha256": memory["trace_response_sha256"],
        "parent_scope_counter_before": root["counter_before"],
        "parent_scope_counter_after": root["counter_after"],
        "parent_scope_seed_draw31": parent_draw,
        "derived_list_scope_counter_before_selection": child_state.counter,
        "actual_selection_draw31": selection_draw,
        "entry_dispatch_counter_before": children[0]["counter_before"],
        "native_scale_rva": hex(WEIGHT_SCALE_RVA),
        "native_binary64_scale": scale,
        "directly_observed_base_weights": memory["weights_native_int32"],
        "conditional_adjusted_weights": weights,
        "adjusted_weights_directly_observed": False,
        "conditional_positive_weight_sum": positive_sum,
        "conditional_threshold": threshold,
        "conditional_selected_index": candidate,
        "directly_observed_selected_index": memory["selected_source_order_index"],
        "candidate_matches_direct_selection": candidate == memory["selected_source_order_index"],
    }
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
