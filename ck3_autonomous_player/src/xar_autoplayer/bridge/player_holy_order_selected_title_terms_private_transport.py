"""Read native holy-order decision candidates and each selected title's final terms."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1,
    read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003, require_exact_native_backend, require_exact_native_build


STEP = "query-player-holy-order-selected-title-terms-v1"
DOMAIN_KEY = "player_holy_order_selected_title_terms_v1"
SCHEMA = "ck3_12003_holy_order_selected_title_terms_v1"
PERMISSION = "allow_private_player_religion_context_query"
DECISIONS = {
    "create_holy_order_decision": ("barony", 1),
    "cancel_holy_order_lease_decision": ("barony", 1),
    "create_holy_order_monastic_decision": ("title", 2),
}


def _availability(value: Mapping[str, object], label: str) -> None:
    if type(value.get("available")) is not bool:
        raise ValueError(f"native {label} availability is malformed")
    reason = value.get("unavailable_reason")
    if ((value["available"] and reason is not None)
            or (not value["available"] and (not isinstance(reason, str) or not reason))):
        raise ValueError(f"native {label} lost its availability reason")


def normalize_player_holy_order_selected_title_terms_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve native candidate order, generation-bearing IDs and signed ten-slot costs."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("native holy-order selected-title schema is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if build != CK3_12003 or build != private_native_build_identity(snapshot):
        raise ValueError("native holy-order selected-title terms belong to another build")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value.get("played_character_id") != actor.get("character_id")
            or value.get("date_raw") != snapshot.get("date_raw")
            or value.get("raw_scale") != 100000 or value.get("read_only") is not True
            or type(value.get("capture_epoch")) is not int or value["capture_epoch"] <= 0):
        raise ValueError("native holy-order selected-title terms differ from their queried player frame")
    _availability(value, "holy-order selected-title context")
    decisions = value.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("native holy-order selected decisions are malformed")
    if decisions and [row.get("decision_id") if isinstance(row, Mapping) else None
                      for row in decisions] != list(DECISIONS):
        raise ValueError("native holy-order selected decisions lost their fixed definitions")
    if value["available"] and len(decisions) != len(DECISIONS):
        raise ValueError("available native holy-order context lost its decisions")
    for decision in decisions:
        _availability(decision, "holy-order selected decision")
        scope, tier = DECISIONS[decision["decision_id"]]
        if (decision.get("selected_scope_name") != scope
                or type(decision.get("selected_title_tier")) is not int
                or decision["selected_title_tier"] not in (-1, tier)
                or type(decision.get("candidates_available")) is not bool
                or (decision.get("is_shown") is not None
                    and type(decision["is_shown"]) is not bool)):
            raise ValueError("native holy-order selected decision metadata is malformed")
        if decision["available"] and (decision["selected_title_tier"] != tier
                or decision["candidates_available"] is not True
                or type(decision.get("is_shown")) is not bool):
            raise ValueError("available native holy-order decision lost its observations")
        candidates = decision.get("candidates")
        if not isinstance(candidates, list):
            raise ValueError("native holy-order title candidates are malformed")
        for title in candidates:
            if (not isinstance(title, Mapping) or type(title.get("title_id")) is not int
                    or not 0 <= title["title_id"] <= 0xFFFFFFFF
                    or title.get("resource_scale") != 100000):
                raise ValueError("native holy-order selected title identity is malformed")
            _availability(title, "holy-order selected title")
            for key in ("title_valid", "can_take", "can_afford"):
                if ((title["available"] and type(title.get(key)) is not bool)
                        or (title.get(key) is not None and type(title[key]) is not bool)):
                    raise ValueError(f"native holy-order selected predicate is malformed: {key}")
            costs = title.get("resource_costs_raw")
            if ((title["available"] and costs is None)
                    or (costs is not None and (not isinstance(costs, list) or len(costs) != 10
                        or any(type(cost) is not int for cost in costs)))):
                raise ValueError("native holy-order selected ten-resource costs are malformed")
            for prefix in ("can_take", "can_afford"):
                sampled = title.get(prefix + "_reasons_available")
                literal = title.get(prefix + "_reason_literal")
                if (type(sampled) is not bool or (title["available"] and sampled is not True)
                        or (sampled and not isinstance(literal, str))
                        or (not sampled and literal is not None)):
                    raise ValueError(f"native holy-order selected reason is malformed: {prefix}")
    return dict(value)


def query_player_holy_order_selected_title_terms_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-holy-order-selected-title-terms-v1",
        )
        if (build != CK3_12003 or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native holy-order selected envelope differs from its queried build/frame")
        value = normalize_player_holy_order_selected_title_terms_v1(
            result.get("player_holy_order_selected_title_terms"), snapshot=before,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native holy-order selected envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
