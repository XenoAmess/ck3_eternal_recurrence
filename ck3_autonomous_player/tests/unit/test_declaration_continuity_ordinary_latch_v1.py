"""An unresolved original declaration retains its existing ordinary latch."""

from copy import deepcopy

from test_prewar_surrogate_authority_regression import DECLARE, QUERY, _snapshot
from xar_autoplayer.strategy import choose_one_life_turn


def test_original_declaration_response_and_single_advance_remain_distinct():
    baseline = _snapshot()
    history = [
        {"index": 1, "command": "save-checkpoint", "ok": True},
        {"index": 2, "command": DECLARE, "ok": True},
    ]
    for status, response, in_flight, progressed, expected_step in (
        ("submission_unknown", "unknown", False, False, None),
        ("submission_unknown", "unknown", True, False, None),
        ("declaration_submitted", "accepted", False, False, "life-advance"),
        ("declaration_submitted", "accepted", False, True, None),
    ):
        snapshot = deepcopy(baseline)
        snapshot["war_declaration_continuity_v1"] = {
            "schema": "war-declaration-continuity-v1",
            "status": status,
            "native_response": response,
            "in_flight": in_flight,
            "request_id": "original-declaration-request",
        }
        rows = deepcopy(history)
        if progressed:
            rows.append({"index": 3, "command": "life-advance", "ok": True})
        original = deepcopy(snapshot)

        plan = choose_one_life_turn(
            rows, snapshot=snapshot, action_steps={DECLARE, QUERY, "life-advance"}
        )

        assert plan["phase"] == "native_war_declaration_pending", plan
        assert plan["selected_step"] == expected_step, plan
        assert plan["request_retried"] is False
        assert plan["war_declaration_continuity_v1"]["request_id"] == (
            "original-declaration-request"
        )
        assert snapshot == original
