"""Use existing route fixtures; no new Native, gameplay or media operations."""
from copy import deepcopy
from unittest.mock import Mock

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.bridge.war_contract import MERGE_ARMIES_CAPABILITY
from xar_autoplayer.war_safe_rendezvous_v1 import review_safe_war_rendezvous_v1 as review
from test_war_safe_rendezvous_v1 import MOVER, history, material


@pytest.fixture(scope="module")
def seed():
    return material()


def compare(seed, kind, count=3):
    _, old, baseline, snapshot, steps, caps = deepcopy(seed)
    rows = history(snapshot, old)[:count]
    if kind == "non_hold":
        baseline.update(phase="life_ready", selected_step="life-advance")
    elif kind == "no_merge":
        caps.remove(MERGE_ARMIES_CAPABILITY)
    elif kind == "unpaused":
        snapshot["paused"] = False
    elif kind == "event":
        snapshot["active_event"] = {}
    elif kind == "stale_strength":
        snapshot["army_strengths_queried_revision"] += 1
    elif kind == "other_war":
        snapshot["active_wars"].append({"war_id": 2})
    elif kind == "committed_friend":
        snapshot["player_armies"][0]["route_province_ids"] = [999]
    elif kind == "missing_occupation":
        snapshot["active_wars"][0]["objective_province_states"] = None
    elif kind == "waiting_not_free":
        rows[2]["result"]["route_contact_horizon"]["one_day_contact_free"] = False
    elif kind == "stale_preview":
        rows[0]["result"]["queried_native_revision"] += 1
    raw = [{"command": "auto-run 3", "result": {"turns": rows}}]
    before = deepcopy((baseline, snapshot, raw))
    factory = Mock(side_effect=lambda: strategy._expanded_command_rows(raw))
    args = dict(snapshot=snapshot, action_steps=steps, bridge_capabilities=caps)
    expected = review(baseline, commands=strategy._expanded_command_rows(raw), **args)
    actual = review(baseline, commands=raw, command_rows_factory=factory, **args)
    assert actual == expected
    assert (baseline, snapshot, raw) == before
    return actual, factory, rows


@pytest.mark.parametrize("kind", [
    "non_hold", "no_merge", "unpaused", "event", "stale_strength",
    "other_war", "committed_friend", "missing_occupation",
])
def test_inapplicable_rendezvous_does_not_expand_history(seed, kind):
    _, factory, _ = compare(seed, kind)
    factory.assert_not_called()


@pytest.mark.parametrize("count", [0, 1, 2, 3])
def test_relevant_rendezvous_keeps_every_friendly_horizon_before_move(seed, count):
    actual, factory, _ = compare(seed, "sequence", count)
    factory.assert_called_once_with()
    expected = (f"preview-move-army-{MOVER}-to-2619" if count == 0 else
        history(seed[3], seed[1])[count]["command"] if count < 3 else
        f"move-army-{MOVER}-to-2619")
    assert actual["selected_step"] == expected
    assert actual["active_attack_allowed"] is False
    if count == 3:
        assert actual["war_safe_rendezvous_v1"]["arrival_guaranteed"] is False


@pytest.mark.parametrize("kind", ["waiting_not_free", "stale_preview"])
def test_negative_friendly_horizon_and_stale_query_keep_original_refusal(seed, kind):
    actual, factory, _ = compare(seed, kind)
    factory.assert_called_once_with()
    assert actual["selected_step"] != f"move-army-{MOVER}-to-2619"
    assert actual["active_attack_allowed"] is False
