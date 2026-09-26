"""Replay the day-26 kill effect using both directly bound native RNG scopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xar_autoplayer.simulation.phase_event_evaluator import execute_phase_event_effect
from project_native_knight_selector_receipt import project as project_selector, response


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def build(attempt: Path, growth_projection: Path) -> dict[str, object]:
    selector = project_selector(attempt)
    growth = json.loads(growth_projection.read_text(encoding="utf-8"))
    v3, _ = response(attempt, "004-v3.json")
    contexts = v3["combat_simulation_inputs"]["phase_event_inputs"]["evaluation_contexts"]
    matches = [row for row in contexts if row["root_character_id"] == 33437]
    if len(matches) != 1:
        raise ValueError("one native target context required")
    if (growth["trace_response_sha256"] != selector["trace_response_sha256"]
            or growth["directly_observed_selected_index"] != 0
            or growth["derived_draw31"] != 422551104):
        raise ValueError("growth selection is not bound to the same trace")
    replay = execute_phase_event_effect(
        matches[0], event_key="knight_killed",
        draws=[selector["selector_draw31"], growth["derived_draw31"]],
    )
    records = replay["draw_tape"]["records"]
    if len(records) != 2 or replay["draw_tape"]["consumed_count"] != 2:
        raise ValueError("frozen AST draw schedule changed")
    if (records[0]["random31"] != selector["selector_draw31"]
            or records[1]["random31"] != growth["derived_draw31"]
            or records[1]["selected_index"] != growth["directly_observed_selected_index"]):
        raise ValueError("frozen AST and native draw/branch disagree")
    scaled = [weight // 100000 for weight in records[1]["weights_source_order"]]
    if scaled != list(growth["conditional_adjusted_weights"]):
        raise ValueError("frozen AST conditional weights disagree")
    selections = [row for row in replay["transition_log"]
                  if row["transition"] == "select_side_knight"]
    kills = [row for row in replay["transition_log"]
             if row["transition"] == "kill_character"]
    growths = [row for row in replay["transition_log"]
               if row["transition"] == "knight_increase_prowess_chance"]
    if (len(selections) != 1 or len(kills) != 1 or len(growths) != 1
            or selections[0]["selected_character_id"] != 34120
            or kills[0]["target_character_id"] != 33437
            or kills[0]["killer_character_id"] != 34120
            or growths[0]["target_character_id"] != 34120
            or growths[0]["selected_branch"] != "no_op"
            or growths[0]["applied"] is not False):
        raise ValueError("effect state does not match native target and branch")
    return {
        "schema": "ck3.native_knight_kill_effect_direct_parity.v1",
        "game_build": "1.19.0.6",
        "combat_id": selector["combat_id"],
        "source_day": selector["source_day"],
        "source_checkpoint_sha256": selector["source_checkpoint_sha256"],
        "trace_response_sha256": selector["trace_response_sha256"],
        "v3_response_sha256": selector["v3_response_sha256"],
        "growth_projection_sha256": digest(growth_projection),
        "stock_event_manifest_sha256": selector["stock_event_manifest_sha256"],
        "native_selector_draw31": selector["selector_draw31"],
        "native_growth_draw31": growth["derived_draw31"],
        "native_selected_character_id": selector["selected_character_id"],
        "native_growth_entry_index": growth["directly_observed_selected_index"],
        "frozen_ast_draw_records": records,
        "frozen_ast_growth_transition": growths[0],
        "frozen_ast_death_transition": kills[0],
        "selected_character_and_growth_branch_direct_native_parity": True,
        "adjusted_weight_values_native_directly_observed": False,
        "complete_mutable_write_set_proven": False,
        "other_event_paths_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--growth-projection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build(args.attempt, args.growth_projection)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
