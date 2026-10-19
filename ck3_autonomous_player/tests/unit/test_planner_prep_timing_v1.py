"""Software-only real planner calls: timers preserve work and original errors.

No SDK/Game, persistence, temporary files or performance benchmark. This proves
the four new call-site mechanics, not elapsed attribution in a future campaign.
"""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge import service


PHASES = {"snapshot": "service.planner_snapshot_prepare",
          "preflight": "service.planner_succession_preflight",
          "view": "service.planner_internal_view",
          "lifestyle": "service.planner_lifestyle_consumer"}


def exercise(*, timing, failure_at=None):
    counts = dict.fromkeys(PHASES, 0)
    finished = []
    failure = RuntimeError("original preparation failure")
    snapshot = {"snapshot_id": "fixture:1", "revision": 1, "native_revision": 1,
                "date_raw": 53144328, "paused": True, "map_ready": True,
                "episode_run_id": "fixture-episode", "active_wars": [],
                "played_character": {"id": 1, "alive": True}}

    def invoke(key, value):
        counts[key] += 1
        if failure_at == key:
            raise failure
        return value

    def take_snapshot():
        return invoke("snapshot", copy.deepcopy(snapshot))

    def planning_view(frame, planner):
        invoke("view", None)
        return copy.deepcopy(planner(frame, []))

    driver = SimpleNamespace(take_internal_semantic_snapshot=take_snapshot,
        _with_internal_planning_view=planning_view,
        capabilities=lambda: {"action_steps": ["life-advance"], "bridge_capabilities": []},
        allow_private_lifestyle_formal_trial=True, state_dir=None)
    owner = service.GameplayBridgeService(driver)

    def preflight(frame, steps, **kwargs):
        return invoke("preflight", frame)

    def lifestyle(planned, steps):
        return invoke("lifestyle", planned)

    def finish(token, **kwargs):
        if token is not None:
            finished.append(token)

    result = error = None
    with patch.object(service, "start_army_timing", side_effect=lambda stage: stage if timing else None), \
         patch.object(service, "finish_army_timing", side_effect=finish), \
         patch.object(service, "choose_one_life_turn", return_value={
             "policy": "fixture", "phase": "life_advance", "selected_step": "life-advance"}), \
         patch.object(owner, "_prepare_succession_transition_v1", side_effect=preflight), \
         patch.object(owner, "_plan_private_lifestyle_trial_v1", side_effect=lifestyle):
        try:
            result = owner.plan_turn()
        except RuntimeError as caught:
            error = caught
    return result, counts, finished, failure, error


def test_four_prep_timers_preserve_selected_plan_and_read_counts():
    off, off_counts, off_finished, _, off_error = exercise(timing=False)
    on, on_counts, on_finished, _, on_error = exercise(timing=True)
    assert off_error is on_error is None
    assert off == on
    assert off_counts == on_counts == dict.fromkeys(PHASES, 1)
    assert off_finished == []
    for stage in PHASES.values():
        assert on_finished.count(stage) == 1
    assert on_finished.index(PHASES["snapshot"]) < on_finished.index(PHASES["preflight"])
    assert on_finished.index(PHASES["view"]) < on_finished.index(PHASES["lifestyle"])


@pytest.mark.parametrize("failure_at", list(PHASES))
def test_prep_timer_finally_preserves_original_exception(failure_at):
    _, counts, finished, original, error = exercise(timing=True, failure_at=failure_at)
    assert error is original
    assert counts[failure_at] == 1
    assert finished.count(PHASES[failure_at]) == 1
