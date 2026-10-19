"""Current native military monthly rates and unapplied termination send quotes."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, private_g2_query_snapshot_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12003, CK3_12004, require_exact_native_build


CURRENT_STEP = "query-war-cash-current-resources-v1"
HOLY_ORDER_LOAN_KEY = "holy_order_loan_observation_v1"
HOLY_ORDER_LOAN_SCHEMA = "xar.ck3.holy-order-loan-war-cash.v1"
TERMINATION_PREFIX = "query-war-cash-termination-send-costs-v1-"
OUTCOMES = ("enforce_demands", "surrender", "white_peace")
MONTHLY_FLOW_SEMANTICS = {
    "version": "ck3-1.20.0.3-native-income-minus-total-expenses-v2",
    "time_basis": "month",
    "source_scope": "played_character_personal_gold",
    "income_source": "native_character_monthly_gold_income",
    "expense_source": "native_character_monthly_total_gold_expenses",
    "military_expenses_included": True,
}
MONTHLY_FLOW_SEMANTICS_12004 = {
    **MONTHLY_FLOW_SEMANTICS,
    "version": "ck3-1.20.0.4-native-income-minus-total-expenses-v2",
}
_MONTHLY_FLOW_SEMANTICS_BY_BUILD = {
    CK3_12003.game_version: MONTHLY_FLOW_SEMANTICS,
    CK3_12004.game_version: MONTHLY_FLOW_SEMANTICS_12004,
}


def _monthly_flow(current: Mapping[str, object]) -> None:
    # Historical v1 packets are retained unchanged, including their mislabeled
    # .3 income field. Only a new explicit semantics marker proves true NET.
    marker = current.get("monthly_income_semantics")
    if marker is None:
        if any(k in current for k in ("player_monthly_gross_income", "player_monthly_total_expenses")):
            raise ValueError("war cash monthly flow lacks its semantics marker")
        return
    expected = _MONTHLY_FLOW_SEMANTICS_BY_BUILD.get(current.get("game_version"))
    if (expected is None or marker != expected
            or not isinstance(marker, Mapping) or marker.get("military_expenses_included") is not True):
        raise ValueError("war cash monthly flow lost its exact-build semantics")
    ready = current.get("readiness")
    if not isinstance(ready, Mapping):
        raise ValueError("war cash monthly flow readiness is absent")
    values = {}
    for key, flag, reason in (
        ("player_monthly_gross_income", "monthly_gross_income_ready", "monthly_gross_income_unavailable_reason"),
        ("player_monthly_total_expenses", "monthly_total_expenses_ready", "monthly_total_expenses_unavailable_reason"),
        ("player_monthly_net_income", "monthly_net_income_ready", "monthly_net_income_unavailable_reason"),
    ):
        if key not in current:
            raise ValueError("war cash monthly flow scalar is absent")
        fixed = current[key]
        if fixed is not None and (not isinstance(fixed, Mapping) or type(fixed.get("raw")) is not int
                or not -(1 << 63) <= fixed["raw"] < (1 << 63)
                or type(fixed.get("scale")) is not int or fixed.get("scale") != 100000):
            raise ValueError("war cash monthly flow scalar is malformed")
        if ready.get(flag) is not (fixed is not None) or (fixed is None and not isinstance(current.get(reason), str)) or (fixed is not None and current.get(reason) is not None):
            raise ValueError("war cash monthly flow availability is inconsistent")
        values[key] = fixed
    gross, expenses, net = (values[k] for k in ("player_monthly_gross_income", "player_monthly_total_expenses", "player_monthly_net_income"))
    if net is not None and (gross is None or expenses is None or net["raw"] != gross["raw"] - expenses["raw"]):
        raise ValueError("war cash monthly NET is not income minus total expenses")
    if gross is not None and expenses is not None and net is None:
        difference = gross["raw"] - expenses["raw"]
        if -(1 << 63) <= difference < (1 << 63) or current.get("monthly_net_income_unavailable_reason") != "war_cash_monthly_net_income_overflow":
            raise ValueError("war cash available monthly flow was replaced by unknown NET")



def _native_frame(value: object, snapshot: Mapping[str, object], schema: str) -> dict[str, object]:
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise ValueError("war cash native schema is malformed")
    identity = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if identity != private_native_build_identity(snapshot):
        raise ValueError("war cash native source belongs to another build")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping) or value.get("played_character_id") != actor.get("character_id")
            or value.get("snapshot_revision") != snapshot.get("native_revision")
            or value.get("date_raw") != snapshot.get("date_raw")
            or value.get("read_only") is not True or value.get("advertised") is not False
            or value.get("formal_action_ready") is not False):
        raise ValueError("war cash source does not match its paused frame")
    return value


def _resource_vector(value: object) -> bool:
    return (isinstance(value, list) and len(value) == 10
            and all(type(raw) is int and -(1 << 63) <= raw < (1 << 63) for raw in value))


def _unavailable_holy_order_loan(reason: str) -> dict[str, object]:
    return {"schema": HOLY_ORDER_LOAN_SCHEMA, "status": "unavailable",
        "read_only": True, "advertised": False, "formal_action_ready": False,
        "source_frame": None, "decision_costs": None, "decision_observation": None,
        "decision_costs_unavailable_reason": reason, "principal": None,
        "principal_quote_raw": None, "principal_unavailable_reason": reason,
        "borrow_eligible": None, "complete_loan_terms": False,
        "existing_debt_principal_raw": None, "received_funds_verified": False,
        "funding_credit_raw": 0, "submit_planned": False}


def _normalize_holy_order_loan(value: object, current: Mapping[str, object],
                              snapshot: Mapping[str, object]) -> dict[str, object]:
    """Validate copied native inputs independently; never degrade valid cash."""
    def integer(raw: object, minimum: int, maximum: int) -> bool:
        return type(raw) is int and minimum <= raw <= maximum

    if (require_exact_native_build(current.get("game_version"), current.get("executable_sha256")) != CK3_12004
            or not isinstance(value, Mapping) or value.get("schema") != HOLY_ORDER_LOAN_SCHEMA
            or value.get("read_only") is not True or value.get("advertised") is not False
            or value.get("formal_action_ready") is not False
            or value.get("complete_loan_terms") is not False
            or value.get("existing_debt_principal_raw") is not None
            or value.get("received_funds_verified") is not False
            or type(value.get("funding_credit_raw")) is not int or value["funding_credit_raw"] != 0
            or value.get("submit_planned") is not False):
        return _unavailable_holy_order_loan("loan_scope_or_funding_assertion_unqualified")
    f = value.get("source_frame")
    readiness = current.get("readiness")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(f, Mapping) or not isinstance(readiness, Mapping)
            or readiness.get("same_frame_ready") is not True
            or f.get("full_snapshot_owner_retained") is not True or f.get("same_frame_ready") is not True
            or not integer(f.get("snapshot_revision"), 1, 2**64 - 1)
            or f["snapshot_revision"] != current.get("snapshot_revision")
            or not integer(f.get("played_character_id"), 1, 2**31 - 1)
            or f["played_character_id"] != current.get("played_character_id")
            or not integer(f.get("date_raw"), 0, 2**31 - 1) or f["date_raw"] != current.get("date_raw")
            or not integer(f.get("local_player_id"), -(2**31), 2**31 - 1)
            or not integer(f.get("ticket_sequence"), 1, 2**64 - 1)):
        return _unavailable_holy_order_loan("loan_native_source_frame_unqualified")
    stamp = f.get("execution_stamp")
    unsigned = {"pump_epoch": (1, 2**64 - 1), "thread_id": (1, 2**32 - 1),
        "rng_wrapper": (0, 2**64 - 1), "rng_state": (0, 2**64 - 1),
        "rng_owner_thread_id": (0, 2**32 - 1), "tls_initialized_flag_address": (0, 2**64 - 1),
        "tls_initialized": (0, 255), "tls_context": (0, 2**64 - 1),
        "tls_main_thread_marker": (0, 255), "jomini_state": (0, 2**64 - 1), "game_state": (0, 2**64 - 1)}
    if (not isinstance(stamp, Mapping) or stamp.get("paused") is not True
            or not integer(stamp.get("date_raw"), 0, 2**31 - 1) or stamp["date_raw"] != f["date_raw"]
            or any(not integer(stamp.get(key), *bounds) for key, bounds in unsigned.items())):
        return _unavailable_holy_order_loan("loan_execution_stamp_unqualified")
    result = _unavailable_holy_order_loan("not_sampled")
    result["source_frame"] = deepcopy(f)
    decisions = value.get("decision_costs")
    cost_reason = value.get("decision_costs_unavailable_reason")
    result["decision_costs_unavailable_reason"] = cost_reason if isinstance(cost_reason, str) and cost_reason else "decision_costs_unavailable"
    if decisions is not None:
        from ..holy_order_loan_decision_observation_v1 import project_holy_order_loan_decision_observation_v1
        try:
            projected = project_holy_order_loan_decision_observation_v1(decisions,
                expected_played_character_id=f["played_character_id"], expected_date_raw=f["date_raw"],
                expected_capture_epoch=stamp["pump_epoch"])
            result["decision_costs"] = deepcopy(decisions)
            result["decision_observation"] = projected
            result["decision_costs_unavailable_reason"] = projected["unavailable_reason"]
            result["borrow_eligible"] = projected["borrow_decision"]["native_gates_allow_decision"]
        except (ValueError, TypeError, KeyError):
            result["decision_costs_unavailable_reason"] = "loan_decision_child_malformed_or_mismatched"
    principal = value.get("principal")
    reason = principal.get("unavailable_reason") if isinstance(principal, Mapping) else None
    result["principal_unavailable_reason"] = reason if isinstance(reason, str) and reason else "principal_unavailable"
    if (isinstance(principal, Mapping) and principal.get("status") == "available"
            and principal.get("value_key") == "holy_order_gold_value"
            and type(principal.get("raw_scale")) is int and principal["raw_scale"] == 100000
            and principal.get("owned_temporaries_released") is True
            and principal.get("unavailable_reason") is None
            and integer(principal.get("prospective_principal_raw"), -(2**63), 2**63 - 1)):
        result["principal"] = deepcopy(principal)
        result["principal_quote_raw"] = principal["prospective_principal_raw"]
        result["principal_unavailable_reason"] = None
    cost_ready = isinstance(result["decision_observation"], Mapping) and result["decision_observation"]["available"] is True
    quote_ready = result["principal_quote_raw"] is not None
    result["status"] = "available" if cost_ready and quote_ready else "partial" if cost_ready or quote_ready else "unavailable"
    return result


def normalize_war_cash_current_resources_v1(value: object, *, snapshot: Mapping[str, object]) -> dict[str, object]:
    current = _native_frame(value, snapshot, "xar.ck3.war-cash-current-resources.v1")
    if current.get("status") not in {"available", "partial", "unavailable"}:
        raise ValueError("war cash current status is malformed")
    for key in ("active_war_ids", "player_army_ids"):
        ids = current.get(key)
        if not isinstance(ids, list) or len(set(ids)) != len(ids) or any(type(value) is not int or value < (0 if key == "player_army_ids" else 1) for value in ids):
            raise ValueError("war cash resource identities are malformed")
    for key in ("current_treasury", "player_monthly_net_income"):
        fixed = current.get(key)
        if fixed is not None and (not isinstance(fixed, Mapping) or type(fixed.get("raw")) is not int or fixed.get("scale") != 100000):
            raise ValueError("war cash fixed-point resource is malformed")
    expenses = current.get("military_expenses")
    if not isinstance(expenses, Mapping):
        raise ValueError("war cash military expense observations are absent")
    for kind in ("current", "all_raised"):
        row = expenses.get(kind)
        if (not isinstance(row, Mapping) or row.get("status") not in {"available", "unavailable"}
                or row.get("owner_character_id") != current["played_character_id"]
                or row.get("resource_id") != str(current["played_character_id"])
                or row.get("war_ids") != current["active_war_ids"]
                or row.get("raw_scale") != 100000 or row.get("time_basis") != "month"
                or row.get("source_scope") != "actor_owned_military_once_across_all_wars"
                or row.get("future_war_cost_upper_ready") is not False):
            raise ValueError("war cash expense source lost its actor-global semantics")
        vector = row.get("resource_raw_native")
        if row["status"] == "available":
            if not _resource_vector(vector) or row.get("gold_raw") != vector[0] or row.get("treasury_raw") != vector[6]:
                raise ValueError("war cash expense vector is malformed")
        elif vector is not None or row.get("gold_raw") is not None or not isinstance(row.get("unavailable_reason"), str):
            raise ValueError("war cash unavailable expenses were replaced by a cost")
    _monthly_flow(current)
    if "current_raw_context_v1" in current:
        from .war_cash_current_raw_context_v1 import validate_current_raw_context_v1
        validate_current_raw_context_v1(current, snapshot=snapshot)
    result = deepcopy(current)
    if HOLY_ORDER_LOAN_KEY in current:
        result[HOLY_ORDER_LOAN_KEY] = _normalize_holy_order_loan(current[HOLY_ORDER_LOAN_KEY], current, snapshot)
    return result


def normalize_war_cash_termination_send_costs_v1(
    value: object, *, snapshot: Mapping[str, object], war_id: int, outcome: str,
) -> dict[str, object]:
    costs = _native_frame(value, snapshot, "xar.ck3.war-cash-termination-send-costs.v1")
    if costs.get("war_id") != war_id or costs.get("outcome") != outcome or costs.get("status") not in {"available", "unavailable"}:
        raise ValueError("war cash termination quote is bound to another choice")
    send = costs.get("generic_send_costs")
    readiness = costs.get("readiness")
    if (not isinstance(send, Mapping) or not isinstance(readiness, Mapping)
            or send.get("raw_scale") != 100000 or send.get("payer_role") != "actor"
            or send.get("application_timing") != "on_send"
            or send.get("payment_state") != "not_yet_applied"
            or readiness.get("total_immediate_gold_cost_ready") is not False
            or costs.get("special_outcome_gold_cost_raw") is not None
            or costs.get("total_immediate_gold_cost_raw") is not None):
        raise ValueError("war cash generic send fees were promoted to total war costs")
    if costs["status"] == "available":
        vector = send.get("resource_raw_native")
        if not _resource_vector(vector) or send.get("gold_raw") != vector[0] or readiness.get("generic_send_costs_ready") is not True:
            raise ValueError("war cash termination send cost vector is malformed")
    return deepcopy(costs)


def query_war_cash_current_resources_private_v1(driver: object, *, expected_revision: int,
                                               timeout_seconds: float = 30.0,
                                               payment_sampling: str | None = None,
                                               payment_window_contract: str | None = None) -> dict[str, object]:
    from .war_payment_observations_v1 import normalize_payment_extras, payment_request_fields
    request_fields = payment_request_fields(payment_sampling, payment_window_contract)
    if request_fields is not None:
        source = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
        if private_native_build_identity(source) != CK3_12004:
            raise BridgeUnavailableError("payment observer control requires exact CK3 1.20.0.4")
    snapshot, result = read_private_g2_native_query_v1(
        driver, permission="allow_private_war_cash_query", step=CURRENT_STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
        include_native_command_history=False, request_fields=request_fields)
    try:
        value = normalize_war_cash_current_resources_v1(result.get("war_cash_current_resources"), snapshot=snapshot)
        extras = normalize_payment_extras(result, snapshot=snapshot, payment_sampling=payment_sampling)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_g2_query_metadata_v1(snapshot), **extras}


def query_war_cash_termination_send_costs_private_v1(
    driver: object, *, expected_revision: int, war_id: int, outcome: str,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if type(war_id) is not int or not 1 <= war_id < (1 << 31) or outcome not in OUTCOMES:
        raise ValueError("war cash termination requires a full native WarID and outcome")
    step = f"{TERMINATION_PREFIX}{war_id}-{outcome}"
    snapshot, result = read_private_g2_native_query_v1(
        driver, permission="allow_private_war_cash_query", step=step,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds)
    try:
        value = normalize_war_cash_termination_send_costs_v1(
            result.get("war_cash_termination_send_costs"), snapshot=snapshot, war_id=war_id, outcome=outcome)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_g2_query_metadata_v1(snapshot)}
