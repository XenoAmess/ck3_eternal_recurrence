"""An aggregate prewar prior must not disable an already observed war."""

from __future__ import annotations

import copy
from unittest.mock import Mock

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP
from xar_autoplayer.simulation.prewar_battle_proxy import prewar_declaration_admission

from test_battle_control_snapshot_v1_bridge import (
    STEP as BATTLE_QUERY_STEP,
    _battle_frame,
    _battle_query_row,
    _planner_battle_snapshot,
)
from test_gameplay_bridge import _army, _army_strength, _native_war_plan


@pytest.fixture
def blocked_declaration_prior(monkeypatch):
    # Even a favorable aggregate prior lacks independent declaration evidence.
    decision = prewar_declaration_admission(
        {
            "status": "estimated",
            "sample_count": 256,
            "no_resolution": 0,
            "resolved_win_wilson95_lower": 1.0,
        }
    )
    assert decision["proxy_risk_budget_passed"] is True
    assert decision["admitted"] is False
    admission = Mock(wraps=prewar_declaration_admission)
    monkeypatch.setattr(strategy, "prewar_declaration_admission", admission)
    yield admission
    admission.assert_not_called()


def _regular_armies():
    player = _army(
        11,
        soldiers=900,
        province_id=20,
        controllable=True,
        army_state="regular",
        route_province_ids=[],
    )
    enemy = _army(
        21,
        soldiers=800,
        province_id=99,
        controllable=False,
        army_state="regular",
        route_province_ids=[],
    )
    return player, enemy


def test_current_war_still_requests_same_frame_army_strengths(
    blocked_declaration_prior,
):
    player, enemy = _regular_armies()
    plan = _native_war_plan(
        player=player,
        enemies=[enemy],
        score=0,
        date_raw=24_000,
        objective=2585,
        steps=(
            QUERY_ARMY_STRENGTHS_STEP,
            "preview-move-army-11-to-2585",
            "life-advance",
        ),
    )

    assert plan["phase"] == "native_war_army_strength_query"
    assert plan["selected_step"] == QUERY_ARMY_STRENGTHS_STEP
    assert plan["army_strength_scope"]["enemy_army_ids"] == [21]


def test_current_defensive_war_still_mobilizes(blocked_declaration_prior):
    player, _ = _regular_armies()
    plan = _native_war_plan(
        player=player,
        players=[],
        allied_armies=[],
        enemies=[],
        player_side="defender",
        score=-10,
        date_raw=24_000,
        steps=("raise-troops-default", "life-advance"),
    )

    assert plan["phase"] == "native_war_raise"
    assert plan["selected_step"] == "raise-troops-default"


def test_current_war_routes_after_observing_force_balance(
    blocked_declaration_prior,
):
    player, enemy = _regular_armies()
    strengths = [
        _army_strength(11, "player", [88], current=900, base_power_raw=900_000),
        _army_strength(
            21, "active_war_enemy", [88], current=800, base_power_raw=800_000
        ),
    ]
    plan = _native_war_plan(
        player=player,
        enemies=[enemy],
        score=0,
        date_raw=24_000,
        objective=2585,
        steps=(
            QUERY_ARMY_STRENGTHS_STEP,
            "preview-move-army-11-to-2585",
            "life-advance",
        ),
        army_strengths=strengths,
        army_strengths_status="available",
    )

    assert plan["phase"] == "native_war_route_preview"
    assert plan["selected_step"] == "preview-move-army-11-to-2585"
    balance = plan["active_wars"][0]["army_strength_balance"]
    assert balance["friendly_current_soldiers"] == 900
    assert balance["enemy_current_soldiers"] == 800


def test_current_combat_service_still_selects_its_readonly_query(
    blocked_declaration_prior,
):
    snapshot = _planner_battle_snapshot(frame=None)

    def unexpected_execute(_step, _revision):
        raise AssertionError("plan_turn must not submit a gameplay command")

    driver = CallbackGameplayDriver(
        backend_id="native-headless",
        snapshot=lambda: copy.deepcopy(snapshot),
        execute=unexpected_execute,
        action_steps=(BATTLE_QUERY_STEP, "life-advance"),
    )
    plan = GameplayBridgeService(driver).plan_turn()["plan"]

    assert plan["phase"] == "native_war_battle_control_query"
    assert plan["selected_step"] == BATTLE_QUERY_STEP


def test_current_combat_can_continue_from_its_own_fresh_inputs(
    blocked_declaration_prior,
):
    frame = _battle_frame()
    snapshot = _planner_battle_snapshot(frame=frame)
    plan = strategy.choose_one_life_turn(
        [_battle_query_row(1, frame)],
        snapshot=snapshot,
        action_steps=(BATTLE_QUERY_STEP, "life-advance"),
    )

    assert plan["phase"] == "native_war_global_battle_control_progress"
    assert plan["selected_step"] == "life-advance"
    assert plan["battle_control_frames"][0]["combat_id"] == frame["combat_id"]
