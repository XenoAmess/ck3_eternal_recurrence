"""The full hostile route proof may avoid strength queries only before contact."""
from __future__ import annotations

from unittest.mock import patch

from xar_autoplayer import strategy
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP
from test_gameplay_bridge import _army, _native_war_plan

ARMY, ENEMY, ORIGIN, TARGET, DATE = 318767248, 218103869, 2634, 2638, 53328720


def _moving_plan(contact_free: bool | None):
    player = _army(ARMY, soldiers=427, province_id=ORIGIN, controllable=True,
                   move_target_province_id=TARGET, army_state="moving",
                   route_province_ids=[2635, TARGET])
    enemy = _army(ENEMY, soldiers=100, province_id=2640, controllable=False,
                  army_state="regular", route_province_ids=[])
    query = strategy.query_route_contact_horizon_step(ARMY, TARGET, (ENEMY,))
    advance = strategy.advance_route_contact_horizon_step(ARMY, TARGET, (ENEMY,))
    history = []
    if contact_free is not None:
        history.append({"index": 1, "command": query, "ok": True, "result": {
            "queried_snapshot_id": "session:90", "queried_revision": 90,
            "queried_native_revision": 90, "queried_connection_generation": 1,
            "queried_episode_run_id": None,
            "route_contact_horizon": {
                "status": "available", "subject_army_id": ARMY,
                "target_province_id": TARGET, "hostile_army_ids": [ENEMY],
                "date_raw": DATE, "snapshot_revision": 90,
                "subject_route": {"army_id": ARMY, "current_province_id": ORIGIN,
                                  "route_province_ids": [2635, TARGET]},
                "one_day_contact_free": contact_free,
            },
        }})
    plan = _native_war_plan(
        player=player, enemies=[enemy], score=0, date_raw=DATE,
        objective=TARGET, history=history,
        steps=(QUERY_ARMY_STRENGTHS_STEP, query, advance),
        route_contact_horizon_supported=True,
    )
    return plan, query, advance


def test_missing_contact_proof_asks_existing_readonly_route_query():
    plan, query, _ = _moving_plan(None)
    assert plan["phase"] == "native_war_moving_contact_before_strength_query"
    assert plan["selected_step"] == query


def test_contact_free_exact_proof_selects_bound_advance():
    plan, _, advance = _moving_plan(True)
    assert plan["phase"] == "native_war_moving_contact_before_strength_progress"
    assert plan["selected_step"] == advance


def test_predicted_contact_returns_to_full_strength_scope():
    plan, _, _ = _moving_plan(False)
    assert plan["phase"] == "native_war_army_strength_query"
    assert plan["selected_step"] == QUERY_ARMY_STRENGTHS_STEP


def test_same_date_old_connection_preview_is_rejected():
    step = strategy.preview_move_army_step(ARMY, 470)
    row = {"index": 1, "command": step, "ok": True, "result": {
        "route_preview": {"status": "available", "army_id": ARMY,
            "origin_province_id": 2635, "target_province_id": 470,
            "route_province_ids": [1032, 470], "previewed_date_raw": DATE},
        "queried_snapshot_id": "native:143", "queried_revision": 2,
        "queried_native_revision": 143, "queried_connection_generation": 7,
        "queried_episode_run_id": "native-40526-c7a6edcc32b8",
    }}
    current = {"snapshot_id": "native:144", "revision": 2,
               "native_revision": 144, "episode_run_id": "native-40526-c7a6edcc32b8",
               "diagnostics": {"connection_generation": 8}}
    old = {**current, "snapshot_id": "native:143", "native_revision": 143,
           "diagnostics": {"connection_generation": 7}}
    def read(frame):
        return strategy._fresh_move_route_preview(
            [row], army_id=ARMY, origin_province_id=2635,
            target_province_id=470, date_raw=DATE, snapshot=frame)
    assert read(current) is None
    assert read(old)["route_province_ids"] == [1032, 470]


def test_unknown_siege_partition_can_only_request_first_hop_preview():
    relief = {"status": "forecast_required", "war_id": 150995049,
              "army_id": ARMY, "target_province_id": 470,
              "army_strength_balance": {"friendly_army_ids": [ARMY, 385876072],
                                       "enemy_army_ids": [419430694]}}
    preview = {"status": "available", "army_id": ARMY,
               "origin_province_id": 2635, "target_province_id": 470,
               "route_province_ids": [1032, 470], "previewed_date_raw": DATE}
    contact = {"status": "available", "hostile_army_ids": [419430694],
               "one_day_contact_free": True, "conflicts": [],
               "hostile_routes": [{"army_id": 419430694,
                   "current_province_id": 470, "timeline_observable": True,
                   "route_province_ids": [], "arrival_date_raws": []}]}
    snapshot = {"paused": True, "date_raw": DATE,
        "player_armies": [{"army_id": ARMY, "current_province_id": 2635,
                           "controllable": True, "army_state": "regular"}],
        "active_wars": [{"war_id": 150995049, "enemy_armies": [
            {"army_id": 419430694, "current_province_id": 470,
             "army_state": "sieging", "retreating": False}]}]}
    first_hop = strategy.preview_move_army_step(ARMY, 1032)
    with (patch.object(strategy, "_primary_defender_siege_relief_assessment", return_value=relief),
          patch.object(strategy, "_fresh_move_route_preview",
                       side_effect=lambda *args, **kw: preview if kw.get("target_province_id") == 470 else None),
          patch.object(strategy, "_fresh_route_contact_horizon", return_value=contact)):
        plan = strategy._primary_defender_siege_forecast_ingress(
            {"phase": "native_war_no_safe_exact_route", "selected_step": None},
            commands=[], snapshot=snapshot, action_steps={first_hop},
            bridge_capabilities=set())
    assert plan["phase"] == "native_war_siege_uncertain_first_hop_preview"
    assert plan["selected_step"] == first_hop
    assert plan["active_attack_allowed"] is False
    assert plan["participant_partition"]["reason"] == "strength_or_contact_roster_mismatch"
