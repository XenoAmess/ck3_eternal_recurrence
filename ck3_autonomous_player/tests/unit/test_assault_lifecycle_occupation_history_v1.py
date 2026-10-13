"""An open assault lifecycle must consume the current occupation history."""

from __future__ import annotations

import copy
from unittest import mock

from test_gameplay_bridge import _army, _assault_action_row, _native_war_plan, _objective_state
from test_normal_war_occupier_side_consumer_v1 import _occupation_query
from xar_autoplayer.bridge.driver import CallbackGameplayDriver


def test_started_assault_consumes_fresh_native_occupier_side_history():
    player = _army(11, soldiers=None, province_id=2585, controllable=True,
                   army_state="regular")
    states = [
        _objective_state(2585, occupant=999, siege_observable=False),
        _objective_state(2510),
    ]
    started = _assault_action_row(1, status="assault_started", decorated=True)
    original_inputs = copy.deepcopy((player, states, started))

    def plan(query):
        query["index"] = 2
        history = [copy.deepcopy(started), query]
        original_history = copy.deepcopy(history)
        with mock.patch.object(CallbackGameplayDriver, "execute_step") as execute:
            result = _native_war_plan(
                player=player, allied_armies=[player], enemies=[], score=30,
                date_raw=24_000, objectives=[2585, 2510], objective_states=states,
                occupation_supported=True, siege_progress_supported=True,
                assault_supported=True, history=history,
                steps=("move-army-11-to-2510", "life-advance"),
            )
            execute.assert_not_called()
        assert history == original_history
        return result

    fresh = plan(_occupation_query())
    assert fresh["selected_step"] == "move-army-11-to-2510", fresh
    assert fresh["pursuit"]["target_province_id"] == 2510, fresh

    for query in (_occupation_query(side="defender"),
                  _occupation_query(date_raw=23_976)):
        blocked = plan(query)
        assert blocked["phase"] == "native_war_assault_lifecycle_blocked", blocked
        assert blocked["selected_step"] is None, blocked
        assert blocked["assault_lifecycles"][0]["reason"] == "siege_unobservable_after_start"

    assert (player, states, started) == original_inputs
