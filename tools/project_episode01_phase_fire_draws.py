"""Derive day-26 phase-fire draws from live RNG boundaries and frozen algorithm.

The native state counters are observed; returned draws/seeds are exact-build
algorithm projections, not a callback trace of the compiled effect internals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.simulation.combat_core import DrawState, fire_phase_event_seeds  # noqa: E402
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_SELECTED_EVENT_ROW_SHA256,
    load_episode01_selected_phase_event_row,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def project(run: Path) -> dict[str, object]:
    selected = load_episode01_selected_phase_event_row()
    source = run / "ck3-output/interactive-requests-responses/007-finish.json"
    if digest(source) != selected["trace_response_sha256"]:
        raise ValueError("trace response bytes differ from selected-row evidence")
    response = json.loads(source.read_text(encoding="utf-8"))
    trace = response["body"]["managed_trace"]["trace"]
    if (trace["failure_flags"] != 0 or len(trace["records"]) != 7
            or trace["readiness"]["bounded_capture_complete"] is not True):
        raise ValueError("native seven-boundary trace is incomplete")
    records = trace["records"]
    if records[3]["global_rng"] != records[4]["global_rng"]:
        raise ValueError("global RNG changed between the two phase fires")
    fires = []
    for side, before_index, after_index in ((0, 2, 3), (1, 4, 5)):
        before = records[before_index]["global_rng"]
        after = records[after_index]["global_rng"]
        if (before["owner_thread_token"] <= 0
                or after["owner_thread_token"] != before["owner_thread_token"]
                or before["salt"] != after["salt"]
                or after["counter"] != before["counter"] + 1):
            raise ValueError(f"side {side} native global draw is not isolated")
        draw, next_state = DrawState(before["counter"], before["salt"]).draw31()
        if next_state.counter != after["counter"] or next_state.salt != after["salt"]:
            raise ValueError(f"side {side} draw algorithm disagrees with native state")
        side_before = records[before_index]["sides"][side]
        scheduled = side_before["scheduled_knights"]
        if side == 1 and (len(scheduled) != 1
                          or scheduled[0]["regiment_id"] != 65
                          or scheduled[0]["native_event_load_index"] != 11
                          or scheduled[0]["current_character_id"] != 33437
                          or not any(
                              row["regiment_id"] == 65 and row["character_id"] == 33437
                              for row in side_before["knights"]
                          )):
            raise ValueError("target event was not the sole scheduled side-1 knight")
        # This day's schedule has no invalid regiment skip. The seeded count
        # is still explicitly derived from the retained event list.
        seeds = fire_phase_event_seeds(
            draw,
            executed_knight_count=len(scheduled),
            commander_executes=(
                side_before["scheduled_commander_native_event_load_index"] is not None
            ),
        )
        fires.append({
            "side_index": side,
            "before_boundary": before_index,
            "after_boundary": after_index,
            "native_rng_counter_before": before["counter"],
            "native_rng_counter_after": after["counter"],
            "native_rng_salt": before["salt"],
            "derived_global_draw31": draw,
            "derived_phase_fire_base": seeds.base,
            "scheduled_knight_event_load_indices": [
                row["native_event_load_index"] for row in scheduled
            ],
            "derived_knight_effect_seeds": list(seeds.knight_effect_seeds),
            "derived_commander_effect_seed": seeds.commander_effect_seed,
        })
    if fires[1]["scheduled_knight_event_load_indices"] != [11]:
        raise ValueError("target phase fire event row changed")
    return {
        "schema": "xar.ck3.episode01.phase-fire-draw-projection/v1",
        "game_build": "CK3 1.19.0.6",
        "selected_event_row_report_sha256": EPISODE01_SELECTED_EVENT_ROW_SHA256,
        "trace_response_sha256": digest(source),
        "native_state_counter_salt_observed": True,
        "global_draw_and_effect_seed_provenance":
            "derived_from_native_state_with_exact_build_static_algorithm",
        "phase_fire_draws": fires,
        "target_event_key": "knight_killed",
        "target_effect_seed": fires[1]["derived_knight_effect_seeds"][0],
        "effect_local_draws_directly_observed": False,
        "effect_local_seed_to_draw_state_validated": False,
        "full_effect_write_set_proven": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.run)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
