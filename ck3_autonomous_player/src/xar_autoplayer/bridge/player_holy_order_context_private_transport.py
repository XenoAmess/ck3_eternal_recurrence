"""Read native holy-order identities, leases and military hire terms only."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-holy-order-context-v1"
DOMAIN_KEY = "player_holy_order_context_v1"
SCHEMA = "ck3_12003_player_holy_order_context_v1"
PERMISSION = "allow_private_player_religion_context_query"


def _full_reference(value: object) -> bool:
    return type(value) is int and 0 <= value <= 0xFFFFFFFF


def normalize_player_holy_order_context_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Keep full native references and independent hire/afford observations."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("native holy-order context schema is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native holy-order context belongs to another build")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value.get("played_character_id") != actor.get("character_id")
            or value.get("date_raw") != snapshot.get("date_raw")
            or value.get("raw_scale") != 100000
            or value.get("read_only") is not True
            or type(value.get("available")) is not bool
            or type(value.get("capture_epoch")) is not int
            or value["capture_epoch"] <= 0):
        raise ValueError("native holy-order context differs from its queried player frame")
    if not value["available"]:
        if not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
            raise ValueError("native holy-order context lost its unavailable reason")
    elif value.get("unavailable_reason") is not None:
        raise ValueError("available native holy-order context has an unavailable reason")
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise ValueError("native holy-order rows are malformed")
    for row in rows:
        if (not isinstance(row, Mapping)
                or not _full_reference(row.get("holy_order_id"))
                or not _full_reference(row.get("rite_id"))
                or type(row.get("is_military")) is not bool):
            raise ValueError("native holy-order identity is malformed")
        for key in ("founder_id", "patron_id", "employer_id"):
            if row.get(key) is not None and not _full_reference(row[key]):
                raise ValueError(f"native holy-order character reference is malformed: {key}")
        leases = row.get("leased_title_ids")
        if not isinstance(leases, list) or any(not _full_reference(item) for item in leases):
            raise ValueError("native holy-order leases are malformed")
        terms = row.get("military_terms")
        if not row["is_military"]:
            if terms is not None:
                raise ValueError("nonmilitary holy order has military hire terms")
            continue
        if (not isinstance(terms, Mapping) or type(terms.get("available")) is not bool
                or terms.get("resource_scale") != 100000):
            raise ValueError("native holy-order military terms are malformed")
        if terms["available"]:
            if terms.get("unavailable_reason") is not None:
                raise ValueError("available native holy-order terms have an unavailable reason")
            if any(type(terms.get(key)) is not bool for key in ("can_hire", "can_afford")):
                raise ValueError("native holy-order final hire predicates are malformed")
            costs = terms.get("resource_costs_raw")
            if (not isinstance(costs, list) or len(costs) != 10
                    or any(type(item) is not int for item in costs)):
                raise ValueError("native holy-order evaluated ten-resource costs are malformed")
        else:
            reason = terms.get("unavailable_reason")
            if not isinstance(reason, str) or not reason:
                raise ValueError("native holy-order military terms lost their unavailable reason")
            for key in ("can_hire", "can_afford"):
                if terms.get(key) is not None and type(terms[key]) is not bool:
                    raise ValueError(f"native holy-order partial predicate is malformed: {key}")
            costs = terms.get("resource_costs_raw")
            if costs is not None and (not isinstance(costs, list) or len(costs) != 10
                    or any(type(item) is not int for item in costs)):
                raise ValueError("native holy-order partial resource costs are malformed")
        for prefix in ("can_hire", "can_afford"):
            sampled = terms.get(prefix + "_reasons_available")
            literal = terms.get(prefix + "_reason_literal")
            if (type(sampled) is not bool
                    or (sampled and not isinstance(literal, str))
                    or (not sampled and literal is not None)):
                raise ValueError(f"native holy-order source reason is malformed: {prefix}")
    return dict(value)


def query_player_holy_order_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-holy-order-context-v1",
        )
        if (build != CK3_12003 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native holy-order envelope differs from its queried build/frame")
        value = normalize_player_holy_order_context_v1(
            result.get("player_holy_order_context"), snapshot=before,
        )
        expected_status = "observed" if value["available"] else "unavailable"
        if result.get("status") != expected_status:
            raise ValueError("native holy-order envelope lost its source status")
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
