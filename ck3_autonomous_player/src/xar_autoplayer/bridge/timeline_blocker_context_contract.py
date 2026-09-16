"""Fail-closed contract for the private current timeline-blocker query."""

from __future__ import annotations

import copy
from typing import Any


QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_CAPABILITY = (
    "game.command.query-current-timeline-blocker-context-v1"
)
QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP = (
    "query-current-timeline-blocker-context-v1"
)

_FIELDS = {
    "schema",
    "schema_version",
    "status",
    "snapshot_revision",
    "date_raw",
    "identity",
    "blocks_simulation",
    "can_continue",
    "evidence_source",
    "unavailable_reason",
}
_TYPED_BOOLEAN_FIELDS = {"status", "value", "unavailable_reason"}
_EVIDENCE_FIELDS = {"kind", "path", "root_name", "decisive_widget_name"}
_IDENTITIES = {
    "none",
    "death_succession_modal",
    "game_over_modal",
    "succession_select_destiny_modal",
}


def _exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} must contain exactly {sorted(fields)}")
    return value


def _int(value: Any, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{label} is outside its frozen range")
    return value


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _typed_boolean(value: Any, label: str) -> dict[str, Any]:
    field = _exact_object(value, _TYPED_BOOLEAN_FIELDS, label)
    status = field["status"]
    if status == "available":
        if not isinstance(field["value"], bool) or field["unavailable_reason"] is not None:
            raise ValueError(f"{label} available value is malformed")
    elif status == "unavailable":
        if field["value"] is not None:
            raise ValueError(f"{label} unavailable value must remain null")
        _nonempty_string(field["unavailable_reason"], f"{label}.unavailable_reason")
    else:
        raise ValueError(f"{label}.status is invalid")
    return field


def normalize_current_timeline_blocker_context_v1(
    value: Any,
    *,
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, Any]:
    """Validate and detach one exact same-frame timeline blocker result."""
    frame = _exact_object(value, _FIELDS, "current_timeline_blocker_context")
    if frame["schema"] != "current-timeline-blocker-context-v1":
        raise ValueError("current_timeline_blocker_context.schema is invalid")
    if frame["schema_version"] != 1:
        raise ValueError("current_timeline_blocker_context.schema_version must be 1")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("current_timeline_blocker_context.status is invalid")
    revision = _int(
        frame["snapshot_revision"],
        "current_timeline_blocker_context.snapshot_revision",
        1,
        2**64 - 1,
    )
    date_raw = _int(
        frame["date_raw"],
        "current_timeline_blocker_context.date_raw",
        -(2**31),
        2**31 - 1,
    )
    if revision != expected_snapshot_revision or date_raw != expected_date_raw:
        raise ValueError("current_timeline_blocker_context frame binding changed")
    identity = frame["identity"]
    if identity not in _IDENTITIES:
        raise ValueError("current_timeline_blocker_context.identity is invalid")
    blocks = _typed_boolean(frame["blocks_simulation"], "blocks_simulation")
    can_continue = _typed_boolean(frame["can_continue"], "can_continue")
    evidence = _exact_object(
        frame["evidence_source"], _EVIDENCE_FIELDS, "evidence_source"
    )

    if frame["status"] == "unavailable":
        _nonempty_string(frame["unavailable_reason"], "unavailable_reason")
        if identity != "none" or blocks["status"] != "unavailable" or can_continue["status"] != "unavailable":
            raise ValueError("unavailable timeline-blocker frame became actionable")
        if any(evidence[field] != "" for field in _EVIDENCE_FIELDS):
            raise ValueError("unavailable timeline-blocker frame carries evidence")
        return copy.deepcopy(frame)

    if frame["unavailable_reason"] is not None:
        raise ValueError("available timeline-blocker frame carries a top-level reason")
    if blocks != {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": "succession_simulation_block_predicate_not_frozen",
    }:
        raise ValueError("blocks_simulation must preserve the frozen unknown")
    if evidence["kind"] != "exact-build-stock-gui-plus-native-widget-state":
        raise ValueError("timeline-blocker evidence kind drifted")
    if evidence["path"] != "game/gui/window_succession_event.gui":
        raise ValueError("timeline-blocker evidence path drifted")
    _nonempty_string(evidence["root_name"], "evidence_source.root_name")
    _nonempty_string(
        evidence["decisive_widget_name"],
        "evidence_source.decisive_widget_name",
    )
    if identity == "none":
        if can_continue["status"] != "unavailable":
            raise ValueError("no timeline surface cannot claim can_continue")
    elif can_continue["status"] != "available":
        raise ValueError("recognized timeline surface lacks typed can_continue")
    return copy.deepcopy(frame)
