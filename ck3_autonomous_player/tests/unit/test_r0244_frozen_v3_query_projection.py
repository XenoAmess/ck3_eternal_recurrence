"""Replay the R0244 frozen *shape* to the new read-only v3 query literal.

The Git formal report retains the blocked plan's route/contact values but not
full transport command envelopes or the original save. Reconstructed envelopes
below exercise planner wiring only, never a live War48 result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from xar_autoplayer.bridge.combat_phase_contract import (
    query_combat_simulation_inputs_v3_step,
)
from xar_autoplayer.strategy import _general_battle_forecast_ingress


ROOT = Path(__file__).resolve().parents[3]
REQUEST = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0244-20260927.json"
FORMAL = ROOT / "docs/autonomous-agent-progress/coordination/war-requests/evidence/WAR-INPUT-R0244-20260927.formal-report.json"


def test_frozen_r0244_route_and_contact_project_exact_readonly_v3_query():
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    formal_bytes = FORMAL.read_bytes()
    assert hashlib.sha256(formal_bytes).hexdigest().upper() == request["evidence"]["git_formal_report_sha256"]
    formal = json.loads(formal_bytes)
    assert request["request_id"] == "WAR-INPUT-R0244-20260927"
    assert request["source"]["ck3_exe_sha256"] == (
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
    )
    # The formal run did not itself record an EXE hash; this assertion is the
    # request's source identity, not a live attestation by this report.
    assert formal["identity"]["ck3_executable_sha256"] is None
    assert request["source"]["bridge_dll_sha256"] == formal["identity"]["bridge_dll"]["sha256"].upper()
    assert request["reproduction"]["candidate_checkpoint_sha256"] == formal["fixed_seed"]["sha256"].upper()
    blocked = formal["first_blocker"]
    original_plan = blocked["plan"]
    before = blocked["before"]
    encounter = original_plan["encounter"]
    route = original_plan["route_preview"]
    contact = original_plan["route_contact_horizon"]
    assert original_plan["phase"] == "native_war_general_battle_inputs_query"
    assert original_plan["selected_step"] is None
    assert encounter == {
        "attacker_army_ids": [16777237],
        "defender_army_ids": [16777417],
        "target_province_id": 2640,
    }
    assert route["route_province_ids"] == [
        2624, 2631, 2630, 2629, 8753, 2626, 2627, 2633, 2634, 2640,
    ]
    assert contact["one_day_contact_free"] is True
    assert contact["conflicts"] == []
    assert before["snapshot_id"] == "native:3"
    assert before["revision"] == 4
    assert before["native_revision"] == 3
    assert before["date_raw"] == 53154936
    assert before["date_raw"] == request["reproduction"]["paused_date_raw"]
    assert before["snapshot_id"] == request["reproduction"]["snapshot_id"]
    assert before["revision"] == request["reproduction"]["snapshot_revision"]
    assert before["native_revision"] == request["reproduction"]["native_revision"]
    assert before["episode_run_id"] == request["reproduction"]["episode_run_id"]
    assert before["active_context"]["war_ids"] == [48]
    assert before["active_context"]["army_ids"] == [16777237]
    assert before["active_context"]["pending_character_interaction"] is None

    attacker_id = encounter["attacker_army_ids"][0]
    defender_id = encounter["defender_army_ids"][0]
    target = encounter["target_province_id"]
    generation = before["connection_generation"]
    snapshot = {
        "paused": before["paused"],
        "snapshot_id": before["snapshot_id"],
        "revision": before["revision"],
        "native_revision": before["native_revision"],
        "date_raw": before["date_raw"],
        "episode_run_id": before["episode_run_id"],
        "diagnostics": {"connection_generation": generation},
        "player_armies": [{"army_id": attacker_id,
                            "current_province_id": route["origin_province_id"],
                            "army_state": "moving"}],
        "active_wars": [{"war_id": 48, "enemy_armies": [{
            "army_id": defender_id, "current_province_id": target,
            "army_state": "stationary",
        }]}],
    }
    # The full command envelopes are not in the Git report. Reconstruct only
    # their transport identity from the frozen selected steps and return data.
    commands = [
        {"index": 1, "command": f"preview-move-army-{attacker_id}-to-{target}",
         "ok": True, "result": {"route_preview": route}},
        {"index": 2,
         "command": f"query-route-contact-horizon-v1-{attacker_id}-to-{target}-h-1-{defender_id}",
         "ok": True, "result": {
             "route_contact_horizon": contact,
             "queried_snapshot_id": before["snapshot_id"],
             "queried_revision": before["revision"],
             "queried_native_revision": before["native_revision"],
             "queried_connection_generation": generation,
             "queried_episode_run_id": before["episode_run_id"],
         }},
    ]
    plan = _general_battle_forecast_ingress(
        {"policy": "one-life-turn-v1", "phase": original_plan["baseline_phase"],
         "selected_step": original_plan["baseline_selected_step"]},
        commands=commands,
        snapshot=snapshot,
        action_steps={commands[0]["command"], commands[1]["command"],
                      original_plan["baseline_selected_step"]},
        bridge_capabilities={"game.command.query-combat-simulation-inputs-v3-N"},
    )
    assert plan["phase"] == "native_war_general_battle_inputs_query"
    assert plan["selected_step"] == query_combat_simulation_inputs_v3_step(
        2640, 2634, [16777237], [16777417]
    )
    assert plan["selected_step"] == (
        "query-combat-simulation-inputs-v3-2640-2634-a-1-16777237-d-1-16777417"
    )
    assert plan["selected_step"] not in {
        commands[0]["command"], commands[1]["command"],
        original_plan["baseline_selected_step"],
    }
