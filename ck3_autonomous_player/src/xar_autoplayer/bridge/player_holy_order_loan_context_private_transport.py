"""Read native holy-order loan quotes and existing debt; never borrow or repay."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-holy-order-loan-context-v1"
DOMAIN_KEY = "player_holy_order_loan_context_v1"
SCHEMA = "ck3_12003_holy_order_loan_context_v1"
PERMISSION = "allow_private_player_religion_context_query"


def normalize_player_holy_order_loan_context_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("native holy-order loan context schema is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native holy-order loan context belongs to another build")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value.get("played_character_id") != actor.get("character_id")
            or value.get("date_raw") != snapshot.get("date_raw")
            or value.get("raw_scale") != 100000
            or type(value.get("available")) is not bool
            or type(value.get("capture_epoch")) is not int
            or value["capture_epoch"] <= 0):
        raise ValueError("native holy-order loan context differs from its queried player frame")
    if not value["available"]:
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
            raise ValueError("native holy-order loan context lost its unavailable reason")
        return dict(value)
    if value.get("unavailable_reason") is not None:
        raise ValueError("available native holy-order loan context has an unavailable reason")
    amount = value.get("loan_amount_quote_raw")
    if type(amount) is not int:
        raise ValueError("native holy-order loan quote is malformed")
    for flag, key in (
        ("loan_amount_owed_present", "loan_amount_owed_raw"),
        ("loan_holder_present", "loan_holder_character_id"),
        ("borrower_years_present", "borrower_years_raw"),
        ("lender_years_present", "lender_years_raw"),
    ):
        if type(value.get(flag)) is not bool:
            raise ValueError(f"native holy-order loan presence is malformed: {flag}")
        scalar = value.get(key)
        if (value[flag] and type(scalar) is not int) or (not value[flag] and scalar is not None):
            raise ValueError(f"native holy-order loan scalar/presence differs: {key}")
    if type(value.get("loan_holder_resolved")) is not bool:
        raise ValueError("native holy-order loan holder resolution is malformed")
    for key, decision_id in (
        ("borrow_decision", "borrow_from_holy_order_decision"),
        ("repay_decision", "repay_loan_decision"),
    ):
        decision = value.get(key)
        if not isinstance(decision, Mapping) or decision.get("decision_id") != decision_id:
            raise ValueError(f"native holy-order loan decision identity is malformed: {key}")
        if any(type(decision.get(field)) is not bool for field in ("is_shown", "can_take", "affordable")):
            raise ValueError(f"native holy-order loan final decision is malformed: {key}")
        costs = decision.get("costs_raw")
        if not isinstance(costs, Mapping) or any(type(costs.get(resource)) is not int for resource in ("gold", "treasury", "prestige", "piety")):
            raise ValueError(f"native holy-order loan evaluated costs are malformed: {key}")
    return dict(value)


def query_player_holy_order_loan_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-holy-order-loan-context-v1",
        )
        if (build != CK3_12003 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native holy-order loan envelope differs from the queried build/frame")
        value = normalize_player_holy_order_loan_context_v1(
            result.get("player_holy_order_loan_context"), snapshot=before,
        )
        expected_status = "observed" if value["available"] else "unavailable"
        if result.get("status") != expected_status:
            raise ValueError("native holy-order loan envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value,
        **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"],
        "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
