"""Synthetic copy-boundary regressions; no game, timing or adoption credit."""
from copy import deepcopy
import inspect
from types import SimpleNamespace

from xar_autoplayer import m5_formal_proposal_collector as collector
from xar_autoplayer.bridge.driver import PreSubmissionRevisionMismatchError


class PrivateCopyBomb:
    def __deepcopy__(self, memo):
        raise AssertionError("discarded private view must not be cloned")


def invoke(planned, snapshot=None, driver=None, function=None):
    return (function or collector.plan_m5_formal_query_only)(
        driver or SimpleNamespace(), planned,
        snapshot=snapshot or {"paused": True, "map_ready": True},
        history=[], available_steps=set())


def test_private_views_are_discarded_without_deepcopy_or_reader_calls():
    calls = []
    driver = SimpleNamespace(query_m5_joint_proposal_sources_private_v1=
                             lambda **kwargs: calls.append(kwargs))
    planned = {"revision": 7, "plan": {"selected_step": "query-army-strengths-v1"},
               "_private_m5_history_v1": [PrivateCopyBomb()],
               "_private_construction_snapshot_v1": PrivateCopyBomb()}
    result = invoke(planned, driver=driver)
    assert result == {"revision": 7, "plan": {"selected_step": "query-army-strengths-v1"}}
    assert not calls


def test_public_nested_values_remain_detached_and_preserve_shared_aliases():
    shared = {"values": [{"war_id": 42}]}
    planned = {"revision": 7,
               "plan": {"selected_step": "query-army-strengths-v1", "metadata": shared},
               "public_metadata": shared, "_private_alias": shared}
    result = invoke(planned)
    assert result["plan"]["metadata"] is result["public_metadata"]
    assert result["public_metadata"] is not shared
    result["public_metadata"]["values"][0]["war_id"] = 99
    assert shared["values"][0]["war_id"] == 42
    shared["values"].append({"war_id": 43})
    assert len(result["public_metadata"]["values"]) == 1


def test_public_contract_matches_original_prefix_across_selection_none_and_error():
    # Reconstruct only the exact reversible prefix hunk of the pinned baseline.
    # Execute the complete real collector for both sides, not a mock decision.
    candidate = inspect.getsource(collector.plan_m5_formal_query_only)
    new = '''    # Runner-private views are discarded here; detach only the public result.
    cleaned = deepcopy({
        key: value for key, value in dict(planned).items()
        if not key.startswith("_private_")
    })
    plan = cleaned.get("plan")
    if not isinstance(plan, Mapping):
        raise ValueError("M5 formal collector lacks a baseline plan")
'''
    old = '''    result = deepcopy(dict(planned))
    plan = result.get("plan")
    if not isinstance(plan, Mapping):
        raise ValueError("M5 formal collector lacks a baseline plan")
    cleaned = {
        key: value for key, value in result.items()
        if not key.startswith("_private_")
    }
'''
    assert candidate.count(new) == 1
    namespace = dict(vars(collector))
    exec(compile(candidate.replace(new, old, 1), "<pinned-original-prefix-shadow>", "exec"), namespace)
    original = namespace["plan_m5_formal_query_only"]

    def run(function, mode):
        calls = []
        def reader(**kwargs):
            calls.append(deepcopy(kwargs))
            if mode == "binding_error":
                raise PreSubmissionRevisionMismatchError("synthetic foreign revision")
            return None
        planned = {"revision": None if mode == "bad_revision" else 7,
                   "plan": None if mode == "no_plan" else {
                       "policy": "synthetic", "selected_step": (
                           "query-campaign-root-context-v1" if mode == "selected" else "life-advance"),
                       "reason": "original public reason", "metadata": {"nested": [1, 2]}},
                   "_private_history": [{"synthetic": True}]}
        try:
            result = invoke(planned, snapshot={"paused": mode != "unpaused", "map_ready": True},
                driver=SimpleNamespace(query_m5_joint_proposal_sources_private_v1=reader),
                function=function)
            return ("return", result), calls
        except (ValueError, PreSubmissionRevisionMismatchError) as error:
            return ("error", type(error).__name__, str(error)), calls

    for mode in ("selected", "unpaused", "bad_revision", "no_plan", "none_source", "binding_error"):
        expected, expected_calls = run(original, mode)
        actual, calls = run(collector.plan_m5_formal_query_only, mode)
        assert actual == expected
        assert calls == expected_calls
        assert len(calls) == (1 if mode in {"none_source", "binding_error"} else 0)
