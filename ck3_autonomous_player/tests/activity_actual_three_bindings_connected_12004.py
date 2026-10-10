"""Consume the one new owned-memory native compound through existing parsers."""

from copy import deepcopy
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.activity_stage5_feast_full_cost_private_transport import (
    parse_activity_stage5_feast_full_cost_payload_v1,
)
from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_STEP, _parse_payload,
)


def run_new_activity_three_binding_wire_cases_12004(bundle: dict) -> list[str]:
    assert bundle["fixture_schema"] == "activity-actual-three-bindings-connected-12004"
    assert bundle["owned_memory_only"] is True and bundle["live_abi_credit"] is False
    assert bundle["native_checks"] == 10
    original = deepcopy(bundle)
    expected = {"expected_native_revision": 74, "expected_date_raw": 43800000,
                "expected_actor_character_id": 0x01000001}
    cost = parse_activity_stage5_feast_full_cost_payload_v1(bundle["cost"], **expected)
    assert cost["actor_gold_raw"] == 123456789
    assert cost["final_can_start"] is False
    assert cost["final_can_start_failure_display"] == {
        "state": "known", "value": "cannot host", "unknown_reason": None}
    assert [cost["resources"][key]["configured_cost_raw"] for key in (
        "gold", "treasury", "piety", "barter_goods")] == [1200000, -250000, 0, 700000]
    passed = ["actual_played_id_gold_and_signed_cost_wire",
              "actual_destructor_failure_display_wire"]
    for key in ("fallback_guest", "selected_guest", "unavailable_guest"):
        guest = _parse_payload(bundle[key], step=INPUT_STEP, native_revision=74,
                               date_raw=43800000, actor_id=0x01000001)
        assert guest["resources"] == cost["resources"]
        if key == "unavailable_guest":
            assert guest["guest_join_status"] == "arrival_source_unavailable"
            assert all(guest[field] is None for field in (
                "selected_nonhost_count", "positive_join_count", "timely_positive_join_count"))
            assert guest["arrival_time_observed"] is False
            assert guest["native_guest_route_qualified"] is False
        else:
            assert guest["guest_join_status"] == "observed"
            assert guest["selected_nonhost_count"] == guest["timely_positive_join_count"] == 1
            assert guest["native_guest_route_qualified"] is True
        passed.append("actual_" + key + "_strict_wire")
    damaged = deepcopy(bundle["cost"])
    damaged["actor_character_id"] ^= 0x02000000
    try:
        parse_activity_stage5_feast_full_cost_payload_v1(damaged, **expected)
    except BridgeUnavailableError:
        passed.append("other_generation_cost_actor_rejected")
    else:
        raise AssertionError("other-generation fullID accepted by existing strict parser")
    damaged = deepcopy(bundle["unavailable_guest"])
    damaged["selected_nonhost_count"] = 0
    try:
        _parse_payload(damaged, step=INPUT_STEP, native_revision=74,
                       date_raw=43800000, actor_id=0x01000001)
    except BridgeUnavailableError:
        passed.append("missing_fallback_does_not_become_zero_guest_count")
    else:
        raise AssertionError("unavailable fallback was accepted as a zero guest count")
    assert bundle == original
    return passed
