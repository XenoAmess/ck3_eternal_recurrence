#!/usr/bin/env python3
"""Bind one frozen day-26 original picker to its same-frame agent model input."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.simulation.combat_core import DrawState, weighted_choice_index
from xar_autoplayer.simulation.phase_event_evaluator import execute_phase_event_effect
from xar_autoplayer.simulation.phase_event_manifest import load_stock_phase_event_manifest


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
DLL_SHA256 = "03233A863F68D31FF123037A711CC22D7C489612E5C212145FB28B0650614F6B"
SOURCE_SHA256 = "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"
SOURCE_RECEIPT_SHA256 = "78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C"
V3_SHA256 = "83BEC53806DE6FECF2A73B3A18D205CABF71A5E5E724B7C08ABC1452A3774B6E"
BEGIN_SHA256 = "D106084F49A5ADC1BCB6B28C9FE8E58DB10C84CCB9D36FF6A6A01CE09C4E3F41"
FINISH_SHA256 = "35ADD14D501D094B32D40564B39B713705AE5A46FB6670024ADA776A4C1A0A47"
SESSION_SHA256 = "C79D8F553D7485254EADE9EB1F2DBF363AEE466C307A4E512B55A033FC0DCB07"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def _token_number(token: str) -> int:
    prefix = "process-local-0x"
    assert isinstance(token, str) and token.startswith(prefix)
    return int(token[len(prefix):], 16)


def validate_weight_record(row: dict, nodes: list[dict]) -> dict:
    """Reject weight, identity, child, and RNG mismatches before model comparison."""

    token = row["effect_node_identity_token"]
    roots = [n for n in nodes if n["node_identity_token"] == token]
    assert len(roots) == 1
    root = roots[0]
    assert (root["call_index"], root["node_vtable_rva"], root["side_index"],
            root["native_event_load_index"]) == (14, 0x44782B0, 1, 11)
    assert row["side_index"] == 1 and row["native_event_load_index"] == 11
    weights = row["weights"]
    assert weights == [40, 30, 15]
    assert row["entry_count"] == len(weights) == len(row["entry_node_identity_tokens"])
    assert row["pick_count"] == 1 and len(row["selected_entry_identity_tokens"]) == 1
    assert bytes.fromhex(row["weights_bytes_hex"]) == struct.pack("<iii", *weights)
    selected_token = row["selected_entry_identity_tokens"][0]
    assert selected_token in row["entry_node_identity_tokens"]
    selected_index = row["entry_node_identity_tokens"].index(selected_token)
    children = [n for n in nodes if n["parent_node_identity_token"] == token]
    assert len(children) == 1
    child = children[0]
    assert child["node_identity_token"] == selected_token
    assert (child["call_index"], child["node_vtable_rva"]) == (15, 0x4478388)
    draw, next_state = DrawState(row["child_counter_before"], row["child_salt_before"]).draw31()
    assert row["child_salt_before"] == row["child_salt_after"] == 0
    assert next_state.counter == child["counter_before"]
    assert child["counter_after"] == row["child_counter_after"]
    assert weighted_choice_index(tuple(weights), draw) == selected_index == 0
    total = sum(max(weight, 0) for weight in weights)
    return {
        "call_index": root["call_index"],
        "side_index": 1,
        "native_event_load_index": 11,
        "effect_node_identity_token": token,
        "entry_node_identity_tokens": row["entry_node_identity_tokens"],
        "selected_entry_identity_token": selected_token,
        "weights_native_int32": weights,
        "weights_bytes_hex": row["weights_bytes_hex"],
        "positive_weight_total": total,
        "child_counter_before": row["child_counter_before"],
        "selection_draw31": draw,
        "threshold": draw * total // (1 << 31),
        "selected_source_order_index": selected_index,
        "child_counter_after": row["child_counter_after"],
    }


def project(attempt: Path, game_exe: Path, bridge_dll: Path,
            source_save: Path, source_receipt: Path) -> dict:
    response_dir = attempt / "ck3-output/interactive-requests-responses"
    paths = {
        "v3": response_dir / "004-v3.json",
        "begin": response_dir / "005-begin.json",
        "finish": response_dir / "007-finish.json",
        "session_result": attempt / "ck3-output/session-result.json",
    }
    hashes = {name: digest(path) for name, path in paths.items()}
    assert hashes == {"v3": V3_SHA256, "begin": BEGIN_SHA256,
                      "finish": FINISH_SHA256, "session_result": SESSION_SHA256}
    assert digest(game_exe) == EXE_SHA256
    assert digest(bridge_dll) == DLL_SHA256
    assert digest(source_save) == SOURCE_SHA256
    assert digest(source_receipt) == SOURCE_RECEIPT_SHA256
    saved = json.loads(source_receipt.read_text(encoding="utf-8"))
    assert saved["body"]["checkpoint"]["sha256"].upper() == SOURCE_SHA256
    assert saved["body"]["checkpoint"]["date_raw"] == 53146848
    begin_request = json.loads((attempt / "ck3-output/interactive-requests/005-begin.json").read_text(encoding="utf-8"))
    assert begin_request["capture_runtime_random_list_weights"] is True
    assert begin_request["managed_daily_sequence_token"] == 68026
    begin = json.loads(paths["begin"].read_text(encoding="utf-8"))
    assert begin["result"] == "CALL_COMPLETED" and begin["body"]["status"] == "armed"
    finish = json.loads(paths["finish"].read_text(encoding="utf-8"))
    assert finish["result"] == "CALL_COMPLETED"
    body = finish["body"]
    assert body["status"] == "bounded_trace_available" and body["combat_id"] == 16777218
    trace = body["managed_trace"]["trace"]
    assert trace["failure_flags"] == 0 and trace["record_count"] == 7
    assert all(row["capture_failure_flags"] == 0 for row in trace["records"])
    assert (trace["records"][0]["native_date_raw"],
            trace["records"][-1]["native_date_raw"]) == (53146848, 53146872)
    runtime = trace["runtime_random_list_weights"]
    assert runtime["status"] == "captured" and runtime["count"] == 1
    choice = validate_weight_record(runtime["records"][0], trace["effect_node_draws"])

    roots = [row for row in trace["effect_roots"] if row["side_index"] == 1
             and row["native_event_load_index"] == 11]
    selects = [row for row in trace["knight_selects"] if row["side_index"] == 1
               and row["native_event_load_index"] == 11]
    assert len(roots) == len(selects) == 1
    assert roots[0]["node_hash"] == 3689483501
    selector = selects[0]
    selector_draw, after_selector = DrawState(selector["counter_before"],
                                              selector["salt_before"]).draw31()
    assert after_selector.counter == selector["counter_after"]
    assert selector["candidate_count"] == 14
    assert selector_draw % 14 == selector["selected_index"] == 8
    assert _token_number(selector["selected_candidate_word0_token"]) == 4
    assert _token_number(selector["selected_candidate_word1_token"]) == 34120
    before_events = trace["records"][4]["battle_events"]
    after_events = trace["records"][5]["battle_events"]
    assert after_events[:len(before_events)] == before_events
    assert len(after_events) == len(before_events) + 1
    event = after_events[-1]
    assert (event["stable_key"], event["left_character_id"],
            event["right_character_id"]) == ("knight_killed_by_enemy", 33437, 34120)

    v3 = json.loads(paths["v3"].read_text(encoding="utf-8"))
    contexts = v3["body"]["combat_simulation_inputs"]["phase_event_inputs"]["evaluation_contexts"]
    matches = [row for row in contexts if row["root_character_id"] == 33437]
    assert len(matches) == 1
    context = matches[0]
    assert (context["combat_side_index"], context["root_source_regiment_id"]) == (1, 65)
    manifest = load_stock_phase_event_manifest()
    stock_events = [row for row in manifest.event_rows if row.key == "knight_killed"]
    assert len(stock_events) == 1 and stock_events[0].global_load_index == 11
    replay = execute_phase_event_effect(
        context, event_key="knight_killed", draws=[selector_draw, choice["selection_draw31"]]
    )
    draw_records = replay["draw_tape"]["records"]
    assert len(draw_records) == 2 and replay["draw_tape"]["consumed_count"] == 2
    growth_draw = draw_records[1]
    assert growth_draw["random31"] == choice["selection_draw31"]
    assert growth_draw["weights_source_order"] == [w * 100000 for w in choice["weights_native_int32"]]
    assert growth_draw["selected_index"] == choice["selected_source_order_index"]
    growths = [row for row in replay["transition_log"] if row["transition"] == "knight_increase_prowess_chance"]
    kills = [row for row in replay["transition_log"] if row["transition"] == "kill_character"]
    assert len(growths) == len(kills) == 1
    assert growths[0]["target_character_id"] == 34120
    assert growths[0]["selected_branch"] == "no_op" and growths[0]["applied"] is False
    assert kills[0]["target_character_id"] == 33437 and kills[0]["killer_character_id"] == 34120
    session = json.loads(paths["session_result"].read_text(encoding="utf-8"))
    assert session["shutdown"]["cleanup_proven"] is True
    assert session["shutdown"]["job_active_processes_final"] == 0
    return {
        "schema": "ck3.native_day26_runtime_random_list_weights.v1",
        "game_executable_sha256": EXE_SHA256,
        "bridge_dll_sha256": DLL_SHA256,
        "source_save_sha256": SOURCE_SHA256,
        "source_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "raw_response_sha256": hashes,
        "combat_id": 16777218,
        "source_date_raw": 53146848,
        "next_date_raw": 53146872,
        "native_event_load_index": 11,
        "native_selector_draw31": selector_draw,
        "native_selector_selected_character_id": 34120,
        "native_choice": choice,
        "native_battle_event": event,
        "same_frame_v3_context": context,
        "stock_event_manifest_sha256": manifest.canonical_manifest_sha256,
        "model_growth_draw_record": growth_draw,
        "model_growth_transition": growths[0],
        "model_death_transition": kills[0],
        "runtime_weights_match_model_source_order": True,
        "selected_growth_branch_matches_original": True,
        "complete_mutable_write_set_proven": False,
        "whole_battle_win_probability_available": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", required=True, type=Path)
    parser.add_argument("--game-exe", required=True, type=Path)
    parser.add_argument("--bridge-dll", required=True, type=Path)
    parser.add_argument("--source-save", required=True, type=Path)
    parser.add_argument("--source-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), f"refusing to overwrite {args.output}"
    result = project(args.attempt_root, args.game_exe, args.bridge_dll,
                     args.source_save, args.source_receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
