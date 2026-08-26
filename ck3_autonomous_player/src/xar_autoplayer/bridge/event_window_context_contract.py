"""Strict wire contract for the exact-build current event-window query."""

from __future__ import annotations

import copy
from typing import Any


QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY = (
    "game.command.query-current-event-window-context-v1"
)
QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP = (
    "query-current-event-window-context-v1"
)

_FIELDS = {
    "schema",
    "schema_version",
    "status",
    "snapshot_revision",
    "date_raw",
    "current_event_instance_id",
    "window_match_count",
    "unavailable_reason",
    "event_definition_key",
    "calculated_event_id",
    "runtime_stats_ordinal",
    "root_scope",
    "saved_scopes",
    "options",
    "readiness",
    "provenance",
}
_OPTION_FIELDS = {
    "rendered_index",
    "native_option_index",
    "shown",
    "enabled",
    "fallback",
    "cancel",
    "resolved_name",
    "unavailable_reason",
    "effect_preview",
}
_READINESS_FIELDS = {
    "event_definition_identity_ready",
    "option_presentation_ready",
    "effect_preview_ready",
    "semantic_decision_ready",
}
_PROVENANCE_FIELDS = {
    "root",
    "idler_vtable_rva",
    "manager_offset",
    "backend_id",
}


def _exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} fields are invalid")
    return value


def _int(value: Any, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{label} is out of range")
    return value


def _string(value: Any, label: str, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise ValueError(f"{label} must be a{' non-empty' if nonempty else ''} string")
    return value


def normalize_current_event_window_context_v1(
    value: Any,
    *,
    expected_event_instance_id: int,
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, Any]:
    """Validate and detach one native current-event-window context frame."""
    frame = _exact_object(value, _FIELDS, "current_event_window_context")
    if frame["schema"] != "current-event-window-context-v1":
        raise ValueError("current_event_window_context.schema is invalid")
    if frame["schema_version"] != 1:
        raise ValueError("current_event_window_context.schema_version must be 1")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("current_event_window_context.status is invalid")
    revision = _int(
        frame["snapshot_revision"],
        "current_event_window_context.snapshot_revision",
        1,
        2**64 - 1,
    )
    date_raw = _int(
        frame["date_raw"],
        "current_event_window_context.date_raw",
        -(2**31),
        2**31 - 1,
    )
    event_id = _int(
        frame["current_event_instance_id"],
        "current_event_window_context.current_event_instance_id",
        1,
        2**31 - 1,
    )
    if (
        revision != expected_snapshot_revision
        or date_raw != expected_date_raw
        or event_id != expected_event_instance_id
    ):
        raise ValueError("current_event_window_context frame binding changed")
    match_count = _int(
        frame["window_match_count"],
        "current_event_window_context.window_match_count",
        0,
        32,
    )
    if frame["root_scope"] is not None or frame["saved_scopes"] is not None:
        raise ValueError("unclosed event scopes must remain null")
    readiness = _exact_object(
        frame["readiness"], _READINESS_FIELDS, "event readiness"
    )
    if any(not isinstance(readiness[key], bool) for key in _READINESS_FIELDS):
        raise ValueError("event readiness values must be booleans")
    provenance = _exact_object(
        frame["provenance"], _PROVENANCE_FIELDS, "event provenance"
    )
    for key in _PROVENANCE_FIELDS:
        _string(provenance[key], f"event provenance.{key}", nonempty=True)
    if (
        provenance["root"] != "module+0x570F7B8->+0x10"
        or provenance["idler_vtable_rva"] != "0x40B1D30"
        or provenance["manager_offset"] != "+0x28"
        or provenance["backend_id"]
        != "ck3-1.19.0.6-native-event-window-v1"
    ):
        raise ValueError("event provenance exact-build locator drifted")

    if frame["status"] == "unavailable":
        _string(
            frame["unavailable_reason"],
            "current_event_window_context.unavailable_reason",
            nonempty=True,
        )
        if (
            frame["event_definition_key"] is not None
            or frame["calculated_event_id"] is not None
            or frame["runtime_stats_ordinal"] is not None
            or frame["options"] is not None
            or any(readiness.values())
        ):
            raise ValueError("unavailable event-window frame is actionable")
        return copy.deepcopy(frame)

    if frame["unavailable_reason"] is not None or match_count != 1:
        raise ValueError("available event-window frame lacks one exact match")
    definition_key = _string(
        frame["event_definition_key"],
        "current_event_window_context.event_definition_key",
        nonempty=True,
    )
    try:
        definition_key_bytes = definition_key.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(
            "current_event_window_context.event_definition_key is not UTF-8"
        ) from error
    if len(definition_key_bytes) > 16_384:
        raise ValueError(
            "current_event_window_context.event_definition_key is too long"
        )
    _int(
        frame["calculated_event_id"],
        "current_event_window_context.calculated_event_id",
        -(2**31),
        2**31 - 1,
    )
    _int(
        frame["runtime_stats_ordinal"],
        "current_event_window_context.runtime_stats_ordinal",
        -(2**31),
        2**31 - 1,
    )
    if readiness != {
        "event_definition_identity_ready": True,
        "option_presentation_ready": True,
        "effect_preview_ready": False,
        "semantic_decision_ready": False,
    }:
        raise ValueError("available event-window readiness is invalid")
    options = frame["options"]
    if not isinstance(options, list) or len(options) > 64:
        raise ValueError("event options must be a bounded list")
    native_indices: set[int] = set()
    cancel_count = 0
    for rendered_index, raw_option in enumerate(options):
        option = _exact_object(
            raw_option, _OPTION_FIELDS, f"event option {rendered_index}"
        )
        if option["rendered_index"] != rendered_index:
            raise ValueError("event option rendered order changed")
        native_index = _int(
            option["native_option_index"],
            "event option native_option_index",
            0,
            2**31 - 1,
        )
        if native_index in native_indices:
            raise ValueError("event option native indices are not unique")
        native_indices.add(native_index)
        if option["shown"] is not True:
            raise ValueError("materialized event options must be shown")
        for key in ("enabled", "fallback", "cancel"):
            if not isinstance(option[key], bool):
                raise ValueError(f"event option {key} must be boolean")
        _string(option["resolved_name"], "event option resolved_name")
        _string(
            option["unavailable_reason"],
            "event option unavailable_reason",
        )
        effect = _exact_object(
            option["effect_preview"],
            {"status", "reason"},
            "event option effect_preview",
        )
        if effect != {
            "status": "unavailable",
            "reason": "full_effect_preview_unavailable",
        }:
            raise ValueError("full event effect preview must remain unavailable")
        cancel_count += int(option["cancel"])
    if cancel_count > 1:
        raise ValueError("multiple event options claim the cancel index")
    return copy.deepcopy(frame)
