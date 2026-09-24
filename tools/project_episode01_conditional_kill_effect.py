"""Compare one possible stock knight-kill effect path with a native replay.

The chosen draw tape is a witness to reachability, not CK3's original RNG.
The report deliberately records every mismatch and keeps planner gates closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.simulation.native_battle_case import (  # noqa: E402
    EPISODE01_KILL_TRACE_RELEASE_SHA256,
    load_episode01_phase_event_kill_trace_release,
)
from xar_autoplayer.simulation.phase_event_evaluator import (  # noqa: E402
    execute_phase_event_effect,
)

V3_RESPONSE_SHA256 = "3A1D83EAB1EA2CE88B83042CF22B0B2E6FA5665A3C169D8A2A4BCF52306DFCA2"
TARGET_ID = 33437
KILLER_ID = 34120
SYNTHETIC_DRAWS = [8, 0]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def project(v3_path: Path) -> dict[str, object]:
    if digest(v3_path) != V3_RESPONSE_SHA256:
        raise ValueError("Release v3 response bytes changed")
    native = load_episode01_phase_event_kill_trace_release()
    response = json.loads(v3_path.read_text(encoding="utf-8"))
    if response.get("result") != "CALL_COMPLETED":
        raise ValueError("v3 native response did not complete")
    payload = response["body"]["combat_simulation_inputs"]["phase_event_inputs"]
    if payload["status"] != "available":
        raise ValueError("Release v3 phase-event context is unavailable")
    contexts = [
        row for row in payload["evaluation_contexts"]
        if row["root_character_id"] == TARGET_ID
    ]
    if len(contexts) != 1:
        raise ValueError("target phase-event context identity drifted")
    context = contexts[0]
    if (context["root_source_regiment_id"] != 65
            or context["combat_side_index"] != 1
            or context["native_state_refs"]["root.skills.prowess_raw"] != 400000):
        raise ValueError("target pre-event context changed")
    eligible = [
        row["character_id"] for row in context["candidate_rows"]
        if row["candidate_refs"].get(
            "derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter"
        ) is True
    ]
    if len(eligible) != 14 or KILLER_ID not in eligible:
        raise ValueError("eligible enemy source set changed")
    evaluated = [
        row for row in payload["row_evaluations"]["contexts"]
        if row["root_character_id"] == TARGET_ID
    ]
    if len(evaluated) != 1:
        raise ValueError("target evaluated row identity drifted")
    kill_weights = [
        row["int_weight"] for row in evaluated[0]["rows"]
        if row["key"] == "knight_killed" and row["trigger_valid"] is True
    ]
    if kill_weights != [27]:
        raise ValueError("pre-event knight-kill weight changed")

    projection = execute_phase_event_effect(
        context,
        event_key="knight_killed",
        draws=SYNTHETIC_DRAWS,
        advantage_model=payload["advantage_model"],
    )
    kills = [row for row in projection["transition_log"] if row["transition"] == "kill_character"]
    if (len(kills) != 1 or kills[0]["target_character_id"] != TARGET_ID
            or kills[0]["reason"] != "death_battle"
            or kills[0]["killer_character_id"] != KILLER_ID
            or projection["draw_tape"]["remaining_count"] != 0):
        raise ValueError("conditional stock kill path changed")
    after = projection["after_state"]
    modeled_detached = TARGET_ID not in after["sides"]["combat_membership"]
    if not modeled_detached or after["root"]["alive"] is not False:
        raise ValueError("conditional death/detachment projection changed")
    native_final = native["target_core_at_final_query"]
    if (native["appended_event"]["left_character_id"] != TARGET_ID
            or native["appended_event"]["right_character_id"] != KILLER_ID
            or native_final["prowess"] != 2
            or native_final["death_marker_present"] is not True
            or native["target_regiment_present_at_final_query"] is not False):
        raise ValueError("native final transition changed")

    return {
        "schema": "xar.ck3.episode01.conditional-kill-effect-audit/v1",
        "game_build": native["game_build"],
        "source_native_report_sha256": EPISODE01_KILL_TRACE_RELEASE_SHA256,
        "source_v3_response_sha256": V3_RESPONSE_SHA256,
        "root_character_id": TARGET_ID,
        "root_source_regiment_id": 65,
        "observed_killer_character_id": KILLER_ID,
        "eligible_enemy_character_ids": eligible,
        "stock_event_key": "knight_killed",
        "event_pre_event_int_weight": kill_weights[0],
        "draws": SYNTHETIC_DRAWS,
        "draw_provenance": "synthetic_reachability_witness_not_native_rng",
        "native_draw_trace_available": False,
        "offline_projection_result_sha256": projection["result_sha256"],
        "offline_projection_status": projection["status"],
        "conditional_death_reason_matches_native": True,
        "conditional_killer_matches_native": True,
        "conditional_participant_detach_matches_native": True,
        "modeled_root_prowess_raw_after": after["root"]["prowess_raw"],
        "native_derived_root_prowess_raw_after": native_final["prowess"] * 100000,
        "effective_character_stat_refresh_matches_native": False,
        "native_reward_prestige_delta": native["killer_prestige_currency_delta"],
        "reward_transition_modeled_by_effect_kernel": False,
        "full_effect_write_set_proven": False,
        "same_day_effect_order_proven": False,
        "whole_battle_win_probability_available": False,
        "planner_usable": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v3-response", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.v3_response)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
