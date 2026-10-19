"""Synthetic regressions for preserving failed LIFE reads, without qualifying them."""

from __future__ import annotations

import pytest

from xar_autoplayer.lifestyle_formal_consumer import consume_lifestyle_private_query


def _consume(query):
    return consume_lifestyle_private_query(
        {"policy": "one-life-turn-v1", "selected_step": "life-advance"},
        scope={"status": "admitted", "at_peace": True},
        query=query,
    )


def test_combined_state_failure_keeps_exact_inner_reason_and_request_identity():
    query = {
        "status": "current_state_unavailable",
        "state": {
            "status": "native_query_unavailable",
            "step": "private-query-player-lifestyle-current-state-v1",
            "request_id": "synthetic-life-state-after-succession",
            "native_error": "native_lifestyle_current_state_current_lifestyle_getter_failed",
        },
    }
    plan = _consume(query)
    assert plan["selected_step"] is None
    assert plan["phase"] == "lifestyle_native_query_unavailable"
    assert plan["lifestyle_native_error"] == query["state"]["native_error"]
    assert plan["lifestyle_query"] == query
    assert "lifestyle_action" not in plan
    assert "lifestyle_decision" not in plan


@pytest.mark.parametrize("inner_status", [
    "paused_frame_unavailable", "native_query_binding_red",
    "native_query_timeout_or_malformed",
])
def test_unknown_or_mismatched_state_remains_blocked_with_original_evidence(inner_status):
    query = {"status": "current_state_unavailable", "state": {
        "status": inner_status, "request_id": "synthetic-unavailable",
        "native_result": {"player_character_id": 29829, "native_revision": 3133},
    }}
    plan = _consume(query)
    assert plan["selected_step"] is None
    assert plan["lifestyle_native_error"] is None
    assert plan["lifestyle_query"] == query
    assert "lifestyle_action" not in plan


def test_native_illegal_focus_is_retained_without_inventing_state_or_action():
    query = {"status": "stock_focus_readback_red", "state": {"status": "available"},
             "focus": {"status": "observed", "native_legal": False,
                       "native_status": "observed_native_illegal"}}
    plan = _consume(query)
    assert plan["selected_step"] is None
    assert plan["lifestyle_query"] == query
    assert plan["lifestyle_native_error"] is None
    assert "lifestyle_action" not in plan


def test_direct_error_keeps_precedence_and_focus_error_is_preserved_when_nested():
    direct = {"status": "native_query_unavailable", "native_error": "direct-error",
              "state": {"native_error": "inner-error"}}
    assert _consume(direct)["lifestyle_native_error"] == "direct-error"
    focus = {"status": "stock_focus_readback_red", "state": {"status": "available"},
             "focus": {"status": "native_query_unavailable", "native_error": "focus-error"}}
    assert _consume(focus)["lifestyle_native_error"] == "focus-error"


def test_missing_query_and_unrelated_business_plan_keep_existing_routing():
    plan = _consume(None)
    assert plan["selected_step"] is None
    assert plan["lifestyle_query_status"] == "not_executed"
    assert plan["lifestyle_query"] is None
    baseline = {"selected_step": "query-army-strengths-v1"}
    assert consume_lifestyle_private_query(
        baseline, scope={"status": "admitted"}, query={"status": "current_state_unavailable"},
    ) == baseline
