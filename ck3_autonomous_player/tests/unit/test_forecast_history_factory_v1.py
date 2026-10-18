"""Keep complete forecast operands while skipping unused history expansion."""

from copy import deepcopy
from unittest.mock import Mock, patch

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.bridge.combat_phase_contract import query_combat_simulation_inputs_v3_step
from test_general_battle_strategy import _frame


def _general_inputs(kind):
    snapshot = _frame()
    plan = {"phase": "native_war_route", "selected_step": "move-army-11-to-31"}
    if kind == "no_snapshot":
        snapshot = None
    elif kind == "unpaused":
        snapshot["paused"] = False
    elif kind == "non_move":
        plan["selected_step"] = "life-advance"
    elif kind == "missing_armies":
        snapshot.pop("player_armies")
    elif kind == "absent_subject":
        snapshot["player_armies"] = []
    elif kind == "no_defender":
        snapshot["active_wars"][0]["enemy_armies"] = []
    elif kind == "existing_forecast":
        plan["qualified_forecast"] = {"status": "ready"}
    elif kind == "active_subject":
        snapshot["player_armies"][0].update(army_state="combat", in_combat=True)
    elif kind == "active_defender":
        snapshot["active_wars"][0]["enemy_armies"][0].update(
            army_state="combat", in_combat=True)
    return plan, snapshot


@pytest.mark.parametrize("kind", [
    "no_snapshot", "unpaused", "non_move", "missing_armies", "absent_subject",
    "no_defender", "existing_forecast", "active_subject", "active_defender",
])
def test_general_guards_do_not_materialize_history_or_change_their_result(kind):
    plan, snapshot = _general_inputs(kind)
    before = deepcopy((plan, snapshot))
    factory = Mock(side_effect=AssertionError("unused forecast history expanded"))
    expected = strategy._general_battle_forecast_ingress(
        plan, commands=[], snapshot=snapshot, action_steps=set(), bridge_capabilities=set())
    actual = strategy._general_battle_forecast_ingress(
        plan, commands=[], snapshot=snapshot, action_steps=set(), bridge_capabilities=set(),
        command_rows_factory=factory)
    assert actual == expected
    factory.assert_not_called()
    assert (plan, snapshot) == before


@pytest.mark.parametrize("kind", ["missing", "current", "stale"])
def test_general_relevant_contact_keeps_query_binding_and_risk_rejection(kind):
    plan, snapshot = _general_inputs("relevant")
    query = query_combat_simulation_inputs_v3_step(31, 30, [11], [21])
    query_row = {"command": query, "ok": True, "result": {
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": snapshot["revision"],
        "queried_native_revision": snapshot["native_revision"], "status": "available",
    }}
    if kind == "stale":
        query_row["result"]["queried_native_revision"] += 1
    raw = [{"command": "auto-run 1", "result": {
        "turns": [] if kind == "missing" else [query_row]}}]
    full = strategy._expanded_command_rows(raw)
    before = deepcopy((plan, snapshot, raw))
    factory = Mock(return_value=full)
    args = dict(snapshot=snapshot, action_steps={"preview-move-army-11-to-31"},
        bridge_capabilities={"game.command.query-combat-simulation-inputs-v3-N"})
    with patch.object(strategy, "_fresh_move_route_preview", return_value={
        "status": "available", "route_province_ids": [31],
    }), patch.object(strategy, "_fresh_route_contact_horizon", return_value={
        "conflicts": [{"province_id": 31, "hostile_army_id": 21}],
        "subject_route": {"arrival_date_raws": [101]},
    }), patch.object(strategy, "forecast_fixed_contact", return_value={"status": "estimated"}), \
            patch.object(strategy, "contact_admission", return_value={"admitted": False}):
        expected = strategy._general_battle_forecast_ingress(plan, commands=full, **args)
        actual = strategy._general_battle_forecast_ingress(
            plan, commands=raw, command_rows_factory=factory, **args)
    assert actual == expected
    factory.assert_called_once_with()
    assert (plan, snapshot, raw) == before
    assert actual["selected_step"] == (None if kind == "current" else query)
    assert actual["phase"] == (
        "native_war_general_battle_model_rejected" if kind == "current"
        else "native_war_general_battle_inputs_query")


@pytest.mark.parametrize("kind", ["no_snapshot", "unpaused", "other_phase", "no_arrays", "no_controlled"])
def test_siege_guards_do_not_materialize_history(kind):
    snapshot = _frame()
    plan = {"phase": "native_war_no_safe_exact_route", "selected_step": None}
    if kind == "no_snapshot":
        snapshot = None
    elif kind == "unpaused":
        snapshot["paused"] = False
    elif kind == "other_phase":
        plan["phase"] = "life_ready"
    elif kind == "no_arrays":
        snapshot.pop("active_wars")
    factory = Mock(side_effect=AssertionError("unused siege history expanded"))
    expected = strategy._primary_defender_siege_forecast_ingress(
        plan, commands=[], snapshot=snapshot, action_steps=set(), bridge_capabilities=set())
    actual = strategy._primary_defender_siege_forecast_ingress(
        plan, commands=[], snapshot=snapshot, action_steps=set(), bridge_capabilities=set(),
        command_rows_factory=factory)
    assert actual == expected
    factory.assert_not_called()


def test_siege_assessment_and_route_read_receive_the_complete_expansion_once():
    snapshot = _frame()
    snapshot["player_armies"][0]["controllable"] = True
    plan = {"phase": "native_war_no_safe_exact_route", "selected_step": None}
    raw = [{"command": "auto-run 2", "result": {"turns": [
        {"command": "old", "ok": None}, {"command": "restore-checkpoint", "ok": True},
    ]}}]
    full = strategy._expanded_command_rows(raw)
    before = deepcopy((plan, snapshot, raw))
    factory = Mock(return_value=full)
    args = dict(snapshot=snapshot, action_steps={"preview-move-army-11-to-31"},
        bridge_capabilities=set())
    with patch.object(strategy, "_primary_defender_siege_relief_assessment", return_value={
        "status": "forecast_required", "army_id": 11, "war_id": 1, "target_province_id": 31,
    }) as assessment:
        expected = strategy._primary_defender_siege_forecast_ingress(plan, commands=full, **args)
        actual = strategy._primary_defender_siege_forecast_ingress(
            plan, commands=raw, command_rows_factory=factory, **args)
    assert actual == expected
    assert actual["selected_step"] == "preview-move-army-11-to-31"
    assert all(call.kwargs["commands"] is full for call in assessment.call_args_list)
    factory.assert_called_once_with()
    assert (plan, snapshot, raw) == before


def test_ordinary_non_move_retains_other_reviewers_but_skips_both_forecast_expansions():
    snapshot = _frame()
    raw = [{"command": "auto-run 1", "result": {"turns": [{"command": "old"}]}}]
    baseline = {"phase": "life_ready", "selected_step": "life-advance"}
    with patch.object(strategy, "_choose_one_life_turn_core", return_value=baseline), \
            patch.object(strategy, "_expanded_command_rows", wraps=strategy._expanded_command_rows) as expand:
        actual = strategy.choose_one_life_turn(raw, snapshot=snapshot, action_steps=[])
    assert actual == baseline
    # The ordinary core is isolated above; none of the inapplicable post-reviews
    # or the unrelated formal review materializes another history here.
    assert expand.call_count == 0
