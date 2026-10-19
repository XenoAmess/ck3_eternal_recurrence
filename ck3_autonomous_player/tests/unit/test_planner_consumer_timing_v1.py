"""Real planner calls with in-memory scalar timing; no performance benchmark."""
import copy
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from xar_autoplayer.bridge import service


STAGES = {
    "pending": "service.planner_pending_material",
    "construction": "service.planner_construction_consumer",
    "family": "service.planner_family_consumer",
    "crown": "service.planner_governance_tail",
}


def exercise(*, timing, selected="life-advance", failure_at=None):
    counts = dict.fromkeys(("snapshot", "view", "capabilities", "state", "construction",
                            "family", "council", "crown", "feast", "arbitration"), 0)
    order, finished = [], []
    failure = RuntimeError("original consumer failure")
    snapshot = {"snapshot_id": "fixture:1", "revision": 1, "native_revision": 1,
                "date_raw": 53144328, "paused": True, "map_ready": True,
                "episode_run_id": "fixture-episode", "player_armies": [],
                "active_wars": [] if selected == "life-advance" else [{"war_id": 1}],
                "played_character": {"character_id": 31254, "alive": True}}

    def invoke(key, value):
        counts[key] += 1
        order.append(key)
        if failure_at == key:
            raise failure
        return value

    def take_snapshot():
        return invoke("snapshot", copy.deepcopy(snapshot))

    def view(frame, planner):
        invoke("view", None)
        return planner(frame, [])

    def capabilities():
        return invoke("capabilities", {"action_steps": ["life-advance", "query-army-strengths-v1"],
                                       "bridge_capabilities": []})

    driver = SimpleNamespace(take_internal_semantic_snapshot=take_snapshot,
        _with_internal_planning_view=view, capabilities=capabilities, state_dir=None,
        allow_private_lifestyle_formal_trial=True,
        allow_private_construction_formal_trial=True,
        allow_private_family_marriage_formal_trial=True)
    owner = service.GameplayBridgeService(driver)

    def state_dir():
        counts["state"] += 1
        if failure_at == "pending" and counts["state"] == 1:
            raise failure
        return None

    def construction(driver_arg, planned, frame, history, available, **kwargs):
        assert driver_arg is driver
        assert frame["snapshot_id"] == snapshot["snapshot_id"]
        assert history == []
        return invoke("construction", planned)

    def family(planned, frame, **kwargs):
        assert frame["snapshot_id"] == snapshot["snapshot_id"]
        return invoke("family", planned)

    def finish(token, **kwargs):
        assert kwargs == {"step": "plan-turn"}
        if token is not None:
            finished.append(token)

    result = error = None
    with patch.object(service, "start_army_timing", side_effect=lambda stage: stage if timing else None), \
         patch.object(service, "finish_army_timing", side_effect=finish), \
         patch.object(service, "choose_one_life_turn", return_value={
             "policy": "fixture", "phase": "fixture", "selected_step": selected}), \
         patch.object(service, "plan_construction_private", side_effect=construction), \
         patch.object(owner, "_strategy_state_dir", side_effect=state_dir), \
         patch.object(owner, "_prepare_succession_transition_v1", side_effect=lambda frame, *a, **k: frame), \
         patch.object(owner, "_plan_private_lifestyle_trial_v1", side_effect=lambda planned, *a: planned), \
         patch.object(owner, "_plan_private_family_wartime_v1", side_effect=family), \
         patch.object(owner, "_plan_private_family_opportunity_v1", side_effect=family), \
         patch.object(owner, "_plan_private_council_normal_v1", side_effect=lambda planned, *a: invoke("council", planned)), \
         patch.object(owner, "_plan_private_crown_normal_v1", side_effect=lambda planned: invoke("crown", planned)), \
         patch.object(owner, "_plan_private_feast_normal_v1", side_effect=lambda planned: invoke("feast", planned)), \
         patch.object(owner, "_finish_prewar_force_coalition_plan_v2", side_effect=lambda planned, *a, **k: invoke("arbitration", planned)):
        try:
            result = owner.plan_turn()
        except RuntimeError as caught:
            error = caught
    return result, counts, order, finished, failure, error


@pytest.mark.parametrize("selected", ["life-advance", "query-army-strengths-v1"])
def test_consumer_timing_on_off_preserves_plan_call_order_and_read_counts(selected):
    off, off_counts, off_order, off_finished, _, off_error = exercise(timing=False, selected=selected)
    on, on_counts, on_order, on_finished, _, on_error = exercise(timing=True, selected=selected)
    assert off_error is on_error is None
    assert off == on and off_counts == on_counts and off_order == on_order
    assert off_counts["snapshot"] == off_counts["view"] == 1
    for key in ("construction", "family", "council", "crown", "feast", "arbitration"):
        assert off_counts[key] == 1
    assert off_finished == []
    for stage in STAGES.values():
        assert on_finished.count(stage) == 1
    assert on_order.index("construction") < on_order.index("family")
    assert on_order.index("council") < on_order.index("crown") < on_order.index("feast")


@pytest.mark.parametrize("failure_at", list(STAGES))
def test_consumer_timing_finally_keeps_original_exception(failure_at):
    _, counts, _, finished, original, error = exercise(timing=True, failure_at=failure_at)
    assert error is original
    assert finished.count(STAGES[failure_at]) == 1
    assert counts["snapshot"] == 1
    if failure_at != "pending":
        assert counts[failure_at] == 1
