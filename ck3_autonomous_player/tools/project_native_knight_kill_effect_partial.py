"""Replay native knight-kill RNG states through the frozen effect AST.

The selector draw and effect-root counter advance are separately observed.
Attributing the latter draw to the growth callback remains conditional until
that callback is itself instrumented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xar_autoplayer.simulation.phase_event_evaluator import (  # noqa: E402
    execute_phase_event_effect,
)
from xar_autoplayer.simulation.combat_core import DrawState  # noqa: E402
from project_native_knight_selector_receipt import project, response  # noqa: E402


def build(attempt: Path) -> dict[str, object]:
    native = project(attempt)
    v3, _ = response(attempt, "004-v3.json")
    contexts = v3["combat_simulation_inputs"]["phase_event_inputs"]["evaluation_contexts"]
    context = next(row for row in contexts if row["root_character_id"] == 33437)
    finish, _ = response(attempt, "007-finish.json")
    roots = [row for row in finish["managed_trace"]["trace"]["effect_roots"]
             if row["side_index"] == 1 and row["native_event_load_index"] == 11]
    if len(roots) != 1 or roots[0]["counter_after"] != roots[0]["counter_before"] + 1:
        raise ValueError("original effect-root RNG schedule changed")
    root = roots[0]
    root_draw, root_next = DrawState(root["counter_before"], root["salt_before"]).draw31()
    if (root_next.counter != root["counter_after"]
            or root_next.salt != root["salt_after"]):
        raise ValueError("effect-root RNG draw replay changed")
    # The root RNG consumes one draw and the nested selector RNG consumes one
    # draw.  Native capture does not yet bind the root draw to the growth
    # transition; that attribution remains conditional on effect AST order.
    replay = execute_phase_event_effect(
        context,
        event_key="knight_killed",
        draws=[native["selector_draw31"], root_draw],
    )
    records = replay["draw_tape"]["records"]
    if len(records) != 2 or replay["draw_tape"]["consumed_count"] != 2:
        raise ValueError("knight_killed effect draw schedule changed")
    if records[0]["random31"] != native["selector_draw31"]:
        raise ValueError("observed selector draw did not reach first AST draw")
    selects = [row for row in replay["transition_log"]
               if row["transition"] == "select_side_knight"]
    if len(selects) != 1 or selects[0]["selected_character_id"] != native["selected_character_id"]:
        raise ValueError("frozen AST selector disagrees with native character")
    death = replay["after_state"]["root"]
    kills = [row for row in replay["transition_log"]
             if row["transition"] == "kill_character"]
    if (death["alive"] is not False or len(kills) != 1
            or kills[0]["target_character_id"] != 33437
            or kills[0]["killer_character_id"] != native["selected_character_id"]):
        raise ValueError("frozen AST death attribution disagrees with native")
    growth = [row for row in replay["transition_log"]
              if row["transition"] == "knight_increase_prowess_chance"]
    if len(growth) != 1 or growth[0]["target_character_id"] != native["selected_character_id"]:
        raise ValueError("frozen AST growth target changed")
    return {
        "schema": "ck3.native_knight_kill_effect_partial_parity.v2",
        "game_build": "1.19.0.6",
        "combat_id": native["combat_id"],
        "source_day": native["source_day"],
        "trace_response_sha256": native["trace_response_sha256"],
        "v3_response_sha256": native["v3_response_sha256"],
        "stock_event_manifest_sha256": native["stock_event_manifest_sha256"],
        "native_observed": {
            "draw_ordinal": 0,
            "selector_draw31": native["selector_draw31"],
            "candidate_count": native["candidate_count"],
            "selected_index": native["selected_index"],
            "selected_character_id": native["selected_character_id"],
            "battle_event_right_character_id": native["battle_event"]["right_character_id"],
        },
        "frozen_ast_replay": {
            "first_draw_record": records[0],
            "selected_character_id": selects[0]["selected_character_id"],
            "root_alive_after": death["alive"],
            "root_killer_character_id_in_transition": kills[0]["killer_character_id"],
            "second_draw_root_rng_candidate": root_draw,
            "second_draw_record_conditional": records[1],
            "growth_transition_conditional": growth[0],
            "selector_mode_in_projection": records[0]["selection_mode"],
        },
        "first_draw_native_parity": True,
        "selector_mode_in_native": native["selection_mode"],
        "selector_index_equivalence_for_equal_weights": True,
        "root_rng_one_draw_observed": True,
        "second_draw_growth_callback_native_bound": False,
        "full_effect_write_set_proven": False,
        "battle_horizon_feedback_ready": False,
        "whole_battle_win_probability_available": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.attempt)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper()}))


if __name__ == "__main__":
    main()
