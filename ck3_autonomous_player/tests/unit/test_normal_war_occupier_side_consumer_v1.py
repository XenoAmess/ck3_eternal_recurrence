"""One ordinary-planner reproduction for an allied occupier without an army."""

from __future__ import annotations

import copy
import json

from test_gameplay_bridge import _army, _native_war_plan, _objective_state
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_occupation_targets_contract import (
    query_war_occupation_targets_v1_step,
)


def _occupation_query(*, side: str = "attacker", date_raw: int = 24_000):
    # Synthetic already-returned query material; this fixture executes no query.
    return {
        "index": 1,
        "command": query_war_occupation_targets_v1_step(88),
        "ok": True,
        "result": {
            "queried_snapshot_id": "session:90",
            "queried_revision": 90,
            "queried_native_revision": 90,
            "queried_connection_generation": 1,
            "queried_episode_run_id": None,
            "war_occupation_targets_v1": {
                "schema": "xar.ck3.war-occupation-targets.v1",
                "schema_version": 1,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "available": True,
                "status": "available",
                "collection_complete": True,
                "unavailable_reason": None,
                "war_id": 88,
                "actor_character_id": 707,
                "player_side": "attacker",
                "primary_attacker_character_id": 707,
                "primary_defender_character_id": 808,
                "snapshot_revision": 90,
                "date_raw": date_raw,
                "side_counts": [
                    {"territory_side": "attacker", "eligible": 0,
                     "occupied": 0, "native_candidate_count": 0,
                     "collection_complete": True},
                    {"territory_side": "defender", "eligible": 2,
                     "occupied": 1 if side == "attacker" else 0,
                     "native_candidate_count": 2, "collection_complete": True},
                ],
                "rows": [
                    {
                        "holding_title_id": 3585,
                        "county_title_id": 4585,
                        "province_id": 2585,
                        "legal_holder_character_id": 808,
                        "territory_side": "defender",
                        "occupation_observable": True,
                        "is_occupied": True,
                        "occupying_character_id": 999,
                        "occupier_side": side,
                        "counted_occupied_by_opposing_side": side == "attacker",
                        "fort_level": 2, "garrison_size": 500,
                        "besieging_strength": 650,
                        "siege_observable": True, "active_siege": None,
                    },
                    {
                        "holding_title_id": 3510,
                        "county_title_id": 4510,
                        "province_id": 2510,
                        "legal_holder_character_id": 808,
                        "territory_side": "defender",
                        "occupation_observable": True,
                        "is_occupied": False,
                        "occupying_character_id": None,
                        "occupier_side": "none",
                        "counted_occupied_by_opposing_side": False,
                        "fort_level": 2, "garrison_size": 500,
                        "besieging_strength": 650,
                        "siege_observable": True, "active_siege": None,
                    },
                ],
            },
        },
    }


def test_native_occupier_side_selects_remaining_objective_compound():
    player = _army(
        11, soldiers=None, province_id=2585, controllable=True,
        army_state="regular",
    )
    states = [_objective_state(2585, occupant=999), _objective_state(2510)]
    original_player, original_states = copy.deepcopy(player), copy.deepcopy(states)
    assert player["owner_character_id"] == 707  # Occupier999 has no field army.

    def plan(history):
        return _native_war_plan(
            player=player, allied_armies=[player], enemies=[], score=30,
            date_raw=24_000, objectives=[2585, 2510], objective_states=states,
            occupation_supported=True, siege_progress_supported=True,
            history=history, steps=("move-army-11-to-2510", "life-advance"),
        )

    missing = plan([])
    assert missing["selected_step"] != "move-army-11-to-2510", missing
    fresh_query = _occupation_query()
    original_query = copy.deepcopy(fresh_query)
    fresh = plan([fresh_query])
    assert fresh["selected_step"] == "move-army-11-to-2510", fresh
    assert fresh["pursuit"]["target_province_id"] == 2510, fresh

    auto_turn = {
        "index": 1, "command": "auto-turn", "ok": True,
        "result": {"auto_turn": {
            "selected_step": fresh_query["command"],
            "result": copy.deepcopy(fresh_query["result"]),
        }},
    }
    wrapped = plan([auto_turn])
    assert wrapped["selected_step"] == "move-army-11-to-2510", wrapped
    assert wrapped["pursuit"]["target_province_id"] == 2510, wrapped

    opposing = plan([_occupation_query(side="defender")])
    stale = plan([_occupation_query(date_raw=23_976)])
    for unchanged in (opposing, stale):
        assert unchanged["selected_step"] == missing["selected_step"], unchanged
        assert unchanged["phase"] == missing["phase"], unchanged
    assert fresh_query == original_query
    assert player == original_player
    assert states == original_states
    print(json.dumps({
        "status": "GREEN", "ordinary_planner_scenes": 5,
        "native_side_remaining_target_scenes": 2,
        "native_queries_executed": 0, "actions_executed": 0,
        "old_native_producer_replayed": False,
        "input_payload_rewritten": False, "synthetic_source_fixture": True,
        "live": False, "new_g2_credit": 0,
    }, sort_keys=True))
