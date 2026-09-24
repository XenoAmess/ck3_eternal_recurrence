"""Bind one native effect-root callback to its frozen day-26 event row.

The observed root RNG matches the static seed initializer. Deeper compiled
effect draws and the winner-selection draw remain outside this projection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pefile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.simulation.combat_core import DrawState, avalanche32  # noqa: E402
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_EFFECT_LOCAL_ROOT_SHA256,
    EPISODE01_SELECTED_EVENT_ROW_SHA256,
    load_episode01_effect_local_root_seed,
    load_episode01_selected_phase_event_row,
)

EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SOURCE_CHECKPOINT_SHA256 = "C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B"
MASK = 0xFFFFFFFF


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def receipt(run: Path, name: str) -> tuple[dict, str]:
    path = run / "ck3-output/interactive-requests-responses" / f"{name}.json"
    response = json.loads(path.read_text(encoding="utf-8"))
    if response.get("result") != "CALL_COMPLETED":
        raise ValueError(f"native response incomplete: {name}")
    return response["body"], digest(path)


def project(run: Path, cache: Path, bridge: Path, exe: Path) -> dict[str, object]:
    run = run.resolve()
    selected = load_episode01_selected_phase_event_row()
    static = load_episode01_effect_local_root_seed()
    copy = json.loads((run / "ck3-output/checkpoint-copy.json").read_text(encoding="utf-8"))
    if (copy["source"]["save"]["sha256"].upper() != SOURCE_CHECKPOINT_SHA256
            or copy["old_attempt_modified"] is not False):
        raise ValueError("source save was not restored from immutable day 26")
    if digest(exe) != EXE_SHA256:
        raise ValueError("wrong CK3 executable")
    cmake = cache.read_text(encoding="utf-8", errors="replace")
    if ("CMAKE_BUILD_TYPE:STRING=Release" not in cmake
            or "XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1:BOOL=ON"
            not in cmake):
        raise ValueError("effect-root bridge is not the Release research build")
    pe = pefile.PE(str(exe), fast_load=True)
    binary = exe.read_bytes()
    child_seed_rva = 0x3380C69
    child_seed_prefix = binary[pe.get_offset_from_rva(child_seed_rva):][:15]
    if child_seed_prefix != bytes.fromhex("69463861420F000FBAF21F03C24489"):
        raise ValueError("compiled-effect child seed instruction bytes changed")
    v3, v3_sha = receipt(run, "004-v3")
    if (v3["status"] != "available"
            or v3["combat_simulation_inputs"]["completeness"]["phase_event_inputs_ready"]
            is not True):
        raise ValueError("same-process v3 inputs unavailable")
    finish, trace_sha = receipt(run, "007-finish")
    trace = finish["managed_trace"]["trace"]
    records = trace["records"]
    if (finish["status"] != "bounded_trace_available"
            or trace["failure_flags"] != 0
            or len(records) != 7
            or any(row["capture_failure_flags"] != 0 for row in records)
            or trace["readiness"]["bounded_capture_complete"] is not True
            or trace["readiness"]["loaded_event_row_identity_map_available"] is not True
            or trace["readiness"]["full_mutable_transition_bundle_complete"] is not False):
        raise ValueError("effect-root native trace incomplete")
    roots = trace["effect_roots"]
    if (len(roots) != 1 or roots[0]["side_index"] != 1
            or roots[0]["native_event_load_index"] != 11
            or roots[0]["counter_before"] != static["derived_effect_local_root_counter"]
            or roots[0]["salt_before"] != 0
            or roots[0]["counter_after"] != roots[0]["counter_before"] + 1
            or roots[0]["salt_after"] != 0):
        raise ValueError("native root effect RNG disagrees with static projection")
    before = records[4]["sides"][1]["scheduled_knights"]
    if (len(before) != 1 or before[0]["native_event_load_index"] != 11
            or before[0]["regiment_id"] != 65
            or before[0]["current_character_id"] != 33437):
        raise ValueError("native effect root does not belong to target event")
    if (not any(event["stable_key"] == "knight_killed_by_enemy"
                and event["left_character_id"] == 33437
                and event["right_character_id"] == 34120
                for event in records[5]["battle_events"])):
        raise ValueError("target kill event did not append")
    target_at_final = next(c for c in records[6]["characters"]
                           if c["character_id"] == 33437)
    if target_at_final["death_marker_present"] is not True:
        raise ValueError("target death was not observed at final pause")
    after_save, after_save_sha = receipt(run, "008-after-save")
    if after_save["checkpoint"]["date_raw"] != 53146872:
        raise ValueError("post-event save date drifted")
    draw, state_after = DrawState(roots[0]["counter_before"], 0).draw31()
    if (draw != static["first_draw_if_root_dispatch_consumes"]
            or state_after.counter != roots[0]["counter_after"]):
        raise ValueError("observed native root draw counter disagrees with exact algorithm")
    mixed = (draw + roots[0]["node_hash"] * 0xF4261) & MASK
    child_seed = avalanche32((0x5EA6BA9F - mixed * 0x4AD685B3) & MASK)
    return {
        "schema": "xar.ck3.episode01.effect-root-observation/v1",
        "game_build": "CK3 1.19.0.6",
        "capture_run": str(run),
        "source_checkpoint_sha256": SOURCE_CHECKPOINT_SHA256,
        "release_build_cache_sha256": digest(cache),
        "release_bridge_dll_sha256": digest(bridge),
        "ck3_exe_sha256": EXE_SHA256,
        "v3_response_sha256": v3_sha,
        "trace_response_sha256": trace_sha,
        "after_save_receipt_sha256": after_save_sha,
        "after_native_save_sha256": after_save["checkpoint"]["sha256"].upper(),
        "selected_event_row_report_sha256": EPISODE01_SELECTED_EVENT_ROW_SHA256,
        "effect_local_static_projection_sha256": EPISODE01_EFFECT_LOCAL_ROOT_SHA256,
        "native_event_key": selected["native_event_key"],
        "native_effect_root": roots[0],
        "native_effect_root_first_draw_derived_from_observed_counter": draw,
        "native_effect_root_counter_advanced_once": True,
        "derived_first_child_seed_from_observed_node_hash": child_seed,
        "first_child_seed_instruction_rva": "0x3380C69",
        "first_child_seed_instruction_prefix_hex": child_seed_prefix.hex().upper(),
        "deep_effect_node_draws_observed": False,
        "killer_selection_draw_observed": False,
        "full_effect_write_set_proven": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--build-cache", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.run, args.build_cache, args.bridge_dll, args.exe)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
