"""Project copied .4 loan decision gates/costs, without actions or funding."""
from __future__ import annotations

from collections.abc import Mapping

from .bridge.version_identity import CK3_12004, require_exact_native_build

NATIVE_SCHEMA = "ck3_12004_holy_order_loan_decision_costs_v1"
SCHEMA = "xar.holy-order-loan-decision-observation.v1"


def _decision(value: object, *, key: str, available: bool) -> dict[str, object]:
    if not isinstance(value, Mapping) or value.get("decision_id") != key:
        raise ValueError("loan decision definition identity differs")
    gates = {name: value.get(name) for name in ("is_shown", "can_take", "affordable")}
    costs = value.get("costs_raw_by_native_index")
    if not available:
        if any(flag is not None for flag in gates.values()) or costs is not None:
            raise ValueError("unavailable loan decision carries observed gates/costs")
        passed = None
    else:
        if any(type(flag) is not bool for flag in gates.values()):
            raise ValueError("observed loan decision final gates are incomplete")
        if (not isinstance(costs, list) or len(costs) != 10
                or any(type(raw) is not int or not -(2**63) <= raw < 2**63 for raw in costs)):
            raise ValueError("loan decision must preserve all ten signed native resource slots")
        passed = all(gates.values())
    return {"decision_id": key, **gates,
            "native_gates_allow_decision": passed,
            "declared_costs_raw_by_native_index": list(costs) if available else None}


def project_holy_order_loan_decision_observation_v1(
    value: object, *, expected_played_character_id: int,
    expected_date_raw: int, expected_capture_epoch: int,
) -> dict[str, object]:
    """Consume a future owner's already frame-bound provider value, with no IO.

    The owner still must bind its native envelope to PID/episode/revision. This
    projection checks only the copied provider's actual actor/date/capture epoch;
    it neither manufactures that envelope nor grants submit qualification.
    """
    if not isinstance(value, Mapping) or value.get("schema") != NATIVE_SCHEMA:
        raise ValueError("unexpected loan decision observation schema")
    if require_exact_native_build(value.get("game_version"), value.get("executable_sha256")) != CK3_12004:
        raise ValueError("loan decision observation is not exact .4")
    for name, expected, minimum, maximum in (
        ("played_character_id", expected_played_character_id, 1, 2**31 - 1),
        ("date_raw", expected_date_raw, 0, 2**31 - 1),
        ("capture_epoch", expected_capture_epoch, 1, 2**64 - 1),
    ):
        if (type(expected) is not int or not minimum <= expected <= maximum
                or type(value.get(name)) is not int or value[name] != expected):
            raise ValueError(f"loan decision observation differs from owner frame: {name}")
    if (value.get("read_only") is not True
            or value.get("scope") != "decision_gates_and_costs_only"
            or type(value.get("raw_scale")) is not int or value["raw_scale"] != 100000
            or type(value.get("resource_slot_count")) is not int or value["resource_slot_count"] != 10
            or type(value.get("available")) is not bool):
        raise ValueError("loan decision observation scope or resource layout differs")
    # This provider has no principal/debt reader. Additional asserted money must
    # not become valid merely because final decision predicates were observed.
    if (value.get("complete_loan_terms") is not False
            or value.get("principal_quote_raw") is not None
            or value.get("typed_debt") is not None
            or type(value.get("funding_credit_raw")) is not int or value["funding_credit_raw"] != 0
            or value.get("submit_planned") is not False):
        raise ValueError("decision-cost provider cannot assert principal, debt, action or funds")
    available = value["available"]
    reason = value.get("unavailable_reason")
    if ((available and reason is not None)
            or (not available and (not isinstance(reason, str) or not reason))):
        raise ValueError("loan decision observation lost its availability reason")
    borrow = _decision(value.get("borrow_decision"),
                       key="borrow_from_holy_order_decision", available=available)
    repay = _decision(value.get("repay_decision"), key="repay_loan_decision", available=available)
    return {
        "schema": SCHEMA, "available": available, "unavailable_reason": reason,
        "source": {"game_version": CK3_12004.game_version,
                   "executable_sha256": CK3_12004.executable_sha256,
                   "played_character_id": expected_played_character_id,
                   "date_raw": expected_date_raw, "capture_epoch": expected_capture_epoch},
        "raw_scale": 100000, "resource_slot_count": 10,
        "borrow_decision": borrow, "repay_decision": repay,
        "principal_quote_raw": None, "existing_debt_principal_raw": None,
        "repayment_total_outlay_raw": None,
        "complete_loan_terms": False, "submission_qualified": False,
        "received_funds_verified": False, "funding_credit_raw": 0,
        "selected_action": None,
    }
