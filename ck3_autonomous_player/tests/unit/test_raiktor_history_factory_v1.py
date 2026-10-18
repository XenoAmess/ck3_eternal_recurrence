"""Exercise the real formal consumer and its ordinary-planner call boundary."""

from copy import deepcopy
from unittest.mock import Mock, patch

import pytest

from xar_autoplayer import strategy
from xar_autoplayer.bridge.war_contract import offer_white_peace_step
from xar_autoplayer.raiktor_formal_exit import plan_raiktor_formal_exit
from test_raiktor_formal_exit_consumer import OPTIONS, POWER, WAR_ID, _query_row, _snapshot


def _unrelated_frame(kind):
    snapshot = _snapshot()
    if kind == "none":
        return None
    if kind == "unpaused":
        snapshot["paused"] = False
    elif kind == "event":
        snapshot["active_event"] = {}
    elif kind == "interaction":
        snapshot["pending_character_interaction"] = {}
    elif kind == "missing_options":
        snapshot.pop("war_termination_options")
    elif kind == "no_options":
        snapshot["war_termination_options"] = []
    elif kind == "foreign_cb":
        snapshot["war_termination_options"][0]["active_casus_belli_identity"][
            "canonical_key"
        ] = "refused_liege_demand_war"
    elif kind == "invalid_war_identity":
        snapshot["active_wars"] = []
    elif kind == "enforce_priority":
        snapshot["active_wars"][0]["player_relative_war_score"] = 100
    return snapshot


@pytest.mark.parametrize("kind", [
    "none", "unpaused", "event", "interaction", "missing_options",
    "no_options", "foreign_cb", "invalid_war_identity", "enforce_priority",
])
def test_pre_history_guards_keep_their_result_without_invoking_factory(kind):
    snapshot = _unrelated_frame(kind)
    rows = [{"command": offer_white_peace_step(WAR_ID), "ok": None}]
    before = deepcopy((snapshot, rows))
    factory = Mock(side_effect=AssertionError("irrelevant history was expanded"))
    expected = plan_raiktor_formal_exit(
        snapshot, rows, action_steps=[OPTIONS, POWER], bridge_capabilities=[]
    )

    actual = plan_raiktor_formal_exit(
        snapshot, rows, action_steps=[OPTIONS, POWER], bridge_capabilities=[],
        command_rows_factory=factory,
    )

    assert actual == expected
    factory.assert_not_called()
    assert (snapshot, rows) == before


@pytest.mark.parametrize("kind", [
    "missing_query", "current_query", "stale_query", "restored_query",
    "unknown_terminal", "failed_terminal",
])
def test_relevant_history_is_expanded_once_with_restore_and_unknown_ack_preserved(kind):
    snapshot = _snapshot()
    query = _query_row(OPTIONS, snapshot)
    turns = [] if kind == "missing_query" else [query]
    if kind == "stale_query":
        query["result"]["queried_connection_generation"] = 99
    elif kind == "restored_query":
        turns.append({"command": "restore-checkpoint", "ok": True})
    elif kind in {"unknown_terminal", "failed_terminal"}:
        turns.append({
            "command": offer_white_peace_step(WAR_ID),
            "ok": None if kind == "unknown_terminal" else False,
        })
    rows = [{"command": "auto-run 2", "ok": True, "result": {"turns": turns}}]
    before = deepcopy((snapshot, rows))
    factory = Mock(side_effect=lambda: strategy._expanded_command_rows(rows))
    expected = plan_raiktor_formal_exit(
        snapshot, strategy._expanded_command_rows(rows),
        action_steps=[OPTIONS, POWER], bridge_capabilities=[],
    )

    actual = plan_raiktor_formal_exit(
        snapshot, rows, action_steps=[OPTIONS, POWER], bridge_capabilities=[],
        command_rows_factory=factory,
    )

    assert actual == expected
    factory.assert_called_once_with()
    assert (snapshot, rows) == before
    if kind == "unknown_terminal":
        assert actual["selected_step"] is None
        assert actual["reason"] == "previous_terminal_submission_requires_fresh_status"
    else:
        assert actual["selected_step"] == (
            OPTIONS if kind in {"missing_query", "stale_query", "restored_query"} else POWER
        )


def test_ordinary_planner_skips_formal_expansion_before_entering_ordinary_core():
    snapshot = _unrelated_frame("foreign_cb")
    rows = [{"command": "auto-run", "result": {"turns": [{"command": "old"}]}}]
    # Stop at the following planner boundary, so other consumers' independent
    # history needs cannot obscure the Raiktor call's expansion count.
    with patch.object(strategy, "_expanded_command_rows", side_effect=AssertionError(
        "formal consumer expanded unrelated history"
    )) as expand, patch.object(strategy, "_choose_one_life_turn_core", side_effect=LookupError(
        "ordinary core reached"
    )) as ordinary:
        with pytest.raises(LookupError, match="ordinary core reached"):
            strategy.choose_one_life_turn(rows, snapshot=snapshot, action_steps=[])
    expand.assert_not_called()
    assert ordinary.call_args.args[0] is rows


def test_ordinary_planner_relevant_query_uses_the_original_complete_expansion():
    snapshot = _snapshot()
    rows = [{"command": "auto-run 1", "result": {
        "turns": [_query_row(OPTIONS, snapshot)],
    }}]
    expected = plan_raiktor_formal_exit(
        snapshot, strategy._expanded_command_rows(rows),
        action_steps=[OPTIONS, POWER], bridge_capabilities=[],
    )
    with patch.object(strategy, "_expanded_command_rows", wraps=strategy._expanded_command_rows) as expand:
        actual = strategy.choose_one_life_turn(
            rows, snapshot=snapshot, action_steps=[OPTIONS, POWER],
        )
    expand.assert_called_once_with(rows)
    assert actual == expected
