"""Actual military expenses and termination send fees, without future estimates."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity
from .version_identity import require_exact_native_build


CURRENT_STEP = "query-war-cash-current-resources-v1"
TERMINATION_PREFIX = "query-war-cash-termination-send-costs-v1-"
OUTCOMES = ("enforce_demands", "surrender", "white_peace")


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
    return deepcopy(current)


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
                                               timeout_seconds: float = 30.0) -> dict[str, object]:
    snapshot, result = read_private_g2_native_query_v1(
        driver, permission="allow_private_war_cash_query", step=CURRENT_STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds)
    try:
        value = normalize_war_cash_current_resources_v1(result.get("war_cash_current_resources"), snapshot=snapshot)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_g2_query_metadata_v1(snapshot)}


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
