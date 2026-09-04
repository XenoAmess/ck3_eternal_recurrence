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
    "effect_indicators",
    "effect_preview",
    "resource_deltas",
    "relationship_deltas",
}
_READINESS_FIELDS = {
    "event_definition_identity_ready",
    "root_scope_ready",
    "saved_scopes_ready",
    "option_presentation_ready",
    "effect_indicators_ready",
    "effect_preview_ready",
    "semantic_decision_ready",
}
_SCOPE_FIELDS = {
    "status",
    "raw_type_index",
    "type_key",
    "subtype",
    "typed_identity",
}
_SAVED_SCOPE_FIELDS = {"name", "name_identifier", "scope"}

_EFFECT_INDICATOR_COVERAGE = (
    "played-character-event-icon-indicators-1.19.0.6-v1"
)
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


def _stable_key(value: Any, label: str) -> str:
    key = _string(value, label, nonempty=True)
    try:
        encoded = key.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(f"{label} is not UTF-8") from error
    if len(encoded) > 16_384:
        raise ValueError(f"{label} is too long")
    return key


def _effect_indicator(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    kind = value.get("kind")
    if kind == "trait":
        row = _exact_object(value, {"kind", "operation", "trait"}, label)
        if row["operation"] not in {"add", "remove"}:
            raise ValueError(f"{label}.operation is invalid")
        trait = row["trait"]
        if not isinstance(trait, dict):
            raise ValueError(f"{label}.trait must be an object")
        if trait.get("status") == "available":
            trait = _exact_object(
                trait, {"status", "native_id", "key"}, f"{label}.trait"
            )
            _int(trait["native_id"], f"{label}.trait.native_id", 0, 2**31 - 1)
            _stable_key(trait["key"], f"{label}.trait.key")
        elif trait.get("status") == "unavailable":
            trait = _exact_object(
                trait, {"status", "reason"}, f"{label}.trait"
            )
            if trait["reason"] != "trait_identity_unavailable":
                raise ValueError(f"{label}.trait reason is invalid")
        else:
            raise ValueError(f"{label}.trait status is invalid")
        return
    if kind == "stress":
        row = _exact_object(
            value,
            {
                "kind",
                "direction",
                "magnitude",
                "affected_by_trait",
                "critical",
            },
            label,
        )
        if row["direction"] not in {"increase", "decrease"}:
            raise ValueError(f"{label}.direction is invalid")
        if row["magnitude"] != {"status": "unavailable"}:
            raise ValueError(f"{label}.magnitude must remain unavailable")
        if not isinstance(row["affected_by_trait"], bool) or not isinstance(
            row["critical"], bool
        ):
            raise ValueError(f"{label} stress flags must be booleans")
        return
    if kind == "death":
        row = _exact_object(
            value, {"kind", "subject", "direction"}, label
        )
        if (
            row["subject"] != "played_character"
            or row["direction"] != "not_applicable"
        ):
            raise ValueError(f"{label} death semantics are invalid")
        return
    if kind == "scheme":
        row = _exact_object(
            value,
            {"kind", "subject", "operation", "direction", "scheme"},
            label,
        )
        if (
            row["subject"] != "played_character"
            or row["operation"] != "start"
            or row["direction"] != "not_applicable"
        ):
            raise ValueError(f"{label} scheme semantics are invalid")
        scheme = row["scheme"]
        if not isinstance(scheme, dict):
            raise ValueError(f"{label}.scheme must be an object")
        if scheme.get("status") == "available":
            scheme = _exact_object(
                scheme,
                {"status", "scheme_type_key"},
                f"{label}.scheme",
            )
            _stable_key(
                scheme["scheme_type_key"],
                f"{label}.scheme.scheme_type_key",
            )
        elif scheme.get("status") == "unavailable":
            scheme = _exact_object(
                scheme, {"status", "reason"}, f"{label}.scheme"
            )
            if scheme["reason"] != "scheme_type_identity_unavailable":
                raise ValueError(f"{label}.scheme reason is invalid")
        else:
            raise ValueError(f"{label}.scheme status is invalid")
        return
    if kind == "unknown":
        row = _exact_object(value, {"kind", "raw_kind"}, label)
        raw_kind = _int(
            row["raw_kind"], f"{label}.raw_kind", -(2**31), 2**31 - 1
        )
        if raw_kind in {0, 1, 2, 3}:
            raise ValueError(f"{label}.raw_kind aliases a known kind")
        return
    raise ValueError(f"{label}.kind is invalid")


def _event_scope(
    value: Any,
    label: str,
    *,
    allow_unavailable_character_identity: bool = False,
) -> None:
    scope = _exact_object(value, _SCOPE_FIELDS, label)
    if scope["status"] != "available":
        raise ValueError(f"{label}.status is invalid")
    raw_type_index = _int(
        scope["raw_type_index"],
        f"{label}.raw_type_index",
        1,
        2**16 - 1,
    )
    type_key = _stable_key(scope["type_key"], f"{label}.type_key")
    _int(scope["subtype"], f"{label}.subtype", 0, 2**16 - 1)
    identity = scope["typed_identity"]
    if raw_type_index == 4:
        if type_key != "character":
            raise ValueError(f"{label} character type key drifted")
        if isinstance(identity, dict) and identity.get("status") == "unavailable":
            identity = _exact_object(
                identity,
                {"status", "reason"},
                f"{label}.typed_identity",
            )
            if not allow_unavailable_character_identity or identity != {
                "status": "unavailable",
                "reason": "character_scope_identity_unavailable",
            }:
                raise ValueError(f"{label}.typed_identity is invalid")
            return
        identity = _exact_object(
            identity,
            {"status", "kind", "character_id"},
            f"{label}.typed_identity",
        )
        if identity["status"] != "available" or identity["kind"] != "character":
            raise ValueError(f"{label}.typed_identity is invalid")
        _int(
            identity["character_id"],
            f"{label}.typed_identity.character_id",
            1,
            2**31 - 1,
        )
        return
    if type_key == "character":
        raise ValueError(f"{label} aliases the character type index")
    identity = _exact_object(
        identity,
        {"status", "reason"},
        f"{label}.typed_identity",
    )
    if identity != {
        "status": "unavailable",
        "reason": "generic_scope_payload_identity_not_closed",
    }:
        raise ValueError(f"{label}.typed_identity exceeds closed coverage")


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
            or frame["root_scope"] is not None
            or frame["saved_scopes"] is not None
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
    _event_scope(frame["root_scope"], "current event root_scope")
    saved_scopes = frame["saved_scopes"]
    if not isinstance(saved_scopes, list) or len(saved_scopes) > 1_024:
        raise ValueError("current event saved_scopes must be a bounded list")
    saved_names: set[str] = set()
    saved_identifiers: set[int] = set()
    for index, raw_saved in enumerate(saved_scopes):
        saved = _exact_object(
            raw_saved,
            _SAVED_SCOPE_FIELDS,
            f"current event saved scope {index}",
        )
        name = _stable_key(
            saved["name"], f"current event saved scope {index}.name"
        )
        identifier = _int(
            saved["name_identifier"],
            f"current event saved scope {index}.name_identifier",
            -(2**31),
            2**31 - 1,
        )
        if name in saved_names or identifier in saved_identifiers:
            raise ValueError("current event saved scope names are not unique")
        saved_names.add(name)
        saved_identifiers.add(identifier)
        _event_scope(
            saved["scope"],
            f"current event saved scope {index}.scope",
            allow_unavailable_character_identity=True,
        )
    if readiness != {
        "event_definition_identity_ready": True,
        "root_scope_ready": True,
        "saved_scopes_ready": True,
        "option_presentation_ready": True,
        "effect_indicators_ready": True,
        "effect_preview_ready": False,
        "semantic_decision_ready": False,
    }:
        raise ValueError("available event-window readiness is invalid")
    options = frame["options"]
    if not isinstance(options, list) or len(options) > 64:
        raise ValueError("event options must be a bounded list")
    native_indices: set[int] = set()
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
        indicators = _exact_object(
            option["effect_indicators"],
            {"status", "coverage", "complete_effect_set", "rows"},
            "event option effect_indicators",
        )
        if (
            indicators["status"] != "available"
            or indicators["coverage"] != _EFFECT_INDICATOR_COVERAGE
            or indicators["complete_effect_set"] is not False
            or not isinstance(indicators["rows"], list)
            or len(indicators["rows"]) > 128
        ):
            raise ValueError("event effect indicators are invalid")
        for row_index, indicator in enumerate(indicators["rows"]):
            _effect_indicator(
                indicator,
                f"event option effect indicator {row_index}",
            )
        effect = _exact_object(
            option["effect_preview"],
            {"status", "reason"},
            "event option effect_preview",
        )
        if effect != {
            "status": "unavailable",
            "reason": "indicator_subset_has_no_completeness_signal",
        }:
            raise ValueError("full event effect preview must remain unavailable")
        for field in ("resource_deltas", "relationship_deltas"):
            unavailable = _exact_object(
                option[field], {"status"}, f"event option {field}"
            )
            if unavailable != {"status": "unavailable"}:
                raise ValueError(f"event option {field} must remain unavailable")
    return copy.deepcopy(frame)
