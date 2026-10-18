"""Preserve both origin checks and post-rejection escape history consumers."""
from copy import deepcopy
from unittest.mock import Mock

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.war_route_origin_exposure_v1 import review_war_route_origin_exposure_v1 as review
from test_war_route_origin_exposure_v1 import HOSTILES, material


@pytest.fixture(scope="module")
def seed():
    return material()


def compare(seed, kind):
    _, plan, snapshot, rows, steps, caps = deepcopy(seed)
    if kind == "ordinary":
        plan.update(phase="life_ready", selected_step="life-advance")
    elif kind == "no_snapshot":
        snapshot = None
    elif kind == "no_plan":
        plan = None
    elif kind == "committed":
        snapshot["player_armies"][0].update(route_province_ids=[2619], move_target_province_id=2619)
    elif kind == "missing_subject":
        snapshot["player_armies"] = []
    elif kind in {"risk_only", "invalid_risk"}:
        plan = {"phase": "native_war_general_battle_model_rejected", "selected_step": None,
            "contact_admission": {"admitted": False, "reason": (
                "bounded_model_risk_budget_exceeded" if kind == "risk_only" else "unknown")}}
    elif kind == "safe":
        rows[-1]["result"]["route_contact_horizon"]["hostile_routes"][0][
            "arrival_date_raws"] = [snapshot["date_raw"] + 216]
    elif kind == "alternate":
        alternate = deepcopy(rows)
        alternate[0]["command"] = "preview-move-army-167772577-to-8755"
        alternate[0]["result"]["route_preview"].update(target_province_id=8755, route_province_ids=[8755])
        alternate[1]["command"] = strategy.query_route_contact_horizon_step(167772577,8755,HOSTILES)
        horizon = alternate[1]["result"]["route_contact_horizon"]
        horizon["target_province_id"] = 8755
        horizon["subject_route"].update(route_province_ids=[8755], arrival_date_raws=[snapshot["date_raw"]+48])
        rows += alternate
    raw = [{"command": "auto-run 4", "result": {"turns": rows}}]
    full = strategy._expanded_command_rows(raw)
    before = deepcopy((plan, snapshot, raw))
    factory = Mock(return_value=full)
    args = dict(snapshot=snapshot, action_steps=steps, bridge_capabilities=caps)
    expected = review(plan, commands=full, **args)
    actual = review(plan, commands=raw, command_rows_factory=factory, **args)
    assert actual == expected
    assert (plan, snapshot, raw) == before
    return actual, factory


@pytest.mark.parametrize("kind", [
    "ordinary", "no_snapshot", "no_plan", "committed", "missing_subject", "invalid_risk",
])
def test_neither_origin_nor_escape_consumer_requires_history(seed, kind):
    _, factory = compare(seed, kind)
    factory.assert_not_called()


@pytest.mark.parametrize("kind,step", [
    ("exposed", "preview-move-army-167772577-to-8755"),
    ("risk_only", "preview-move-army-167772577-to-8755"),
    ("alternate", "move-army-167772577-to-8755"),
    ("safe", "move-army-167772577-to-2619"),
])
def test_origin_and_escape_keep_complete_history_with_one_factory_call(seed, kind, step):
    actual, factory = compare(seed, kind)
    factory.assert_called_once_with()
    assert actual["selected_step"] == step
    assert actual["active_attack_allowed"] is False
