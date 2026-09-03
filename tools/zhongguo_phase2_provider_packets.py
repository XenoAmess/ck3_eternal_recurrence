#!/usr/bin/env python3
"""Production adapters for Phase2 business-postcondition packets.

All inputs are already-normalized public service responses or action-cell
artifacts.  The adapters never read arbitrary variables and never accept the
canonical test fixture as an input.  Existing providers can build scoreboard
and endgame packets.  Promotion and projects remain fail-closed until their
two explicitly named native-headless queries exist.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from zhongguo_phase2_business_postconditions import (
    ENDGAME_HANDLER,
    PROJECTS_HANDLER,
    PROMOTION_HANDLER,
    SCOREBOARD_HANDLER,
    verify_phase2_business_postcondition,
)


PROMOTION_COMPENSATION_QUERY_CAPABILITY: Final = (
    "game.command.query-zhongguo-promotion-compensation-postcondition-v1"
)
PROJECTS_METRICS_QUERY_CAPABILITY: Final = (
    "game.command.query-zhongguo-projects-metrics-postcondition-v1"
)
NATIVE_BACKEND: Final = "native-headless"
_FUTURE_BINDING_KEYS: Final = (
    "connection_generation",
    "player_character_id",
    "source_snapshot_id",
    "result_snapshot_id",
    "source_revision",
    "result_revision",
    "source_native_revision",
    "result_native_revision",
)


def _positive(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _red(handler: str, reason: str, *, missing: tuple[str, ...] = ()) -> dict[str, object]:
    return {
        "schema_version": 1,
        "result": "RED",
        "handler": handler,
        "reason_code": reason,
        "provider_packet": None,
        "postcondition": None,
        "missing_provider_fields": list(missing),
    }


def _finish(handler: str, packet: dict[str, object]) -> dict[str, object]:
    proof = verify_phase2_business_postcondition(handler, packet)
    if proof.get("result") != "GREEN":
        return {
            "schema_version": 1,
            "result": "RED",
            "handler": handler,
            "reason_code": "business_postcondition_not_green",
            "provider_packet": packet,
            "postcondition": proof,
            "missing_provider_fields": [],
        }
    return {
        "schema_version": 1,
        "result": "GREEN",
        "handler": handler,
        "reason_code": None,
        "provider_packet": packet,
        "postcondition": proof,
        "missing_provider_fields": [],
    }


def _binding(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    raw = value.get("binding")
    if not isinstance(raw, Mapping):
        return None
    result = dict(raw)
    if not (
        isinstance(result.get("snapshot_id"), str)
        and result.get("snapshot_id")
        and _nonnegative(result.get("revision"))
        and _positive(result.get("native_revision"))
    ):
        return None
    return result


def _source(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    raw = value.get("source")
    return dict(raw) if isinstance(raw, Mapping) else None


def _typed_value(group: object, key: str) -> object | None:
    if not isinstance(group, Mapping):
        return None
    field = group.get(key)
    if not isinstance(field, Mapping):
        return None
    if field.get("status") != "available" or field.get("unavailable_reason") is not None:
        return None
    return field.get("value")


def _case_identity(group: object) -> dict[str, object] | None:
    result = {
        key: _typed_value(group, key)
        for key in (
            "owner_character_id",
            "subject_character_id",
            "cycle_serial",
            "case_serial",
        )
    }
    if not all(_positive(value) for value in result.values()):
        return None
    return result


def _event_query(value: object, expected_key: str) -> dict[str, object] | None:
    if not isinstance(value, Mapping) or value.get("status") != "available":
        return None
    context = value.get("current_event_window_context")
    binding = _binding(value)
    if not isinstance(context, Mapping) or binding is None:
        return None
    readiness = context.get("readiness")
    root = context.get("root_scope")
    identity = root.get("typed_identity") if isinstance(root, Mapping) else None
    root_character_id = (
        identity.get("character_id") if isinstance(identity, Mapping) else None
    )
    instance_id = context.get("current_event_instance_id")
    if not (
        context.get("event_definition_key") == expected_key
        and isinstance(readiness, Mapping)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and _positive(instance_id)
        and _positive(root_character_id)
        and context.get("snapshot_revision") == binding.get("native_revision")
    ):
        return None
    return {
        "definition_key": expected_key,
        "visible": True,
        "identity_ready": True,
        "snapshot_revision": binding["native_revision"],
        "event_instance_id": instance_id,
        "root_character_id": root_character_id,
        "binding": binding,
        "saved_scopes": context.get("saved_scopes"),
    }


def _event_has_character(event: Mapping[str, object], character_id: int) -> bool:
    if event.get("root_character_id") == character_id:
        return True
    scopes = event.get("saved_scopes")
    if not isinstance(scopes, list):
        return False
    for row in scopes:
        scope = row.get("scope") if isinstance(row, Mapping) else None
        identity = scope.get("typed_identity") if isinstance(scope, Mapping) else None
        if isinstance(identity, Mapping) and identity.get("character_id") == character_id:
            return True
    return False


def _widget_visible(state: Mapping[str, object], identity: str) -> bool | None:
    widgets = state.get("widgets")
    if not isinstance(widgets, list):
        return None
    for row in widgets:
        if not isinstance(row, Mapping) or row.get("stable_identity") != identity:
            continue
        visible = row.get("effective_visible")
        if (
            isinstance(visible, Mapping)
            and visible.get("status") == "available"
            and isinstance(visible.get("value"), bool)
        ):
            return bool(visible["value"])
    return None


def build_scoreboard_calibration_provider_packet(
    action_cell: object,
    calibration_event_query: object,
) -> dict[str, object]:
    """Build from the existing verified scoreboard cell and event provider."""

    if not isinstance(action_cell, Mapping):
        return _red(SCOREBOARD_HANDLER, "scoreboard_action_cell_missing")
    if not (
        action_cell.get("result") == "GREEN"
        and action_cell.get("verified_pass") is True
        and action_cell.get("production_capability_advertised") is True
        and isinstance(action_cell.get("verified_postcondition"), Mapping)
        and action_cell["verified_postcondition"].get("postcondition_verified") is True
    ):
        return _red(SCOREBOARD_HANDLER, "scoreboard_action_cell_not_verified")
    request = action_cell.get("action_request")
    source_state = action_cell.get("source_query")
    result_state = action_cell.get("later_query")
    if not (
        isinstance(request, Mapping)
        and request.get("action") == "open"
        and isinstance(source_state, Mapping)
        and source_state.get("status") == "available"
        and isinstance(result_state, Mapping)
        and result_state.get("status") == "available"
    ):
        return _red(SCOREBOARD_HANDLER, "scoreboard_open_transition_missing")
    before = _binding(source_state)
    after = _binding(result_state)
    before_source = _source(source_state)
    after_source = _source(result_state)
    event = _event_query(calibration_event_query, "zg361.1")
    if None in (before, after, before_source, after_source, event):
        return _red(
            SCOREBOARD_HANDLER,
            "scoreboard_or_calibration_provider_binding_missing",
            missing=("verified scoreboard source/later binding", "zg361.1 current-event identity"),
        )
    assert before is not None and after is not None
    assert before_source is not None and after_source is not None and event is not None
    generation = before_source.get("connection_generation")
    player = before.get("player_character_id")
    event_binding = event["binding"]
    if not (
        _positive(generation)
        and _positive(player)
        and after_source.get("connection_generation") == generation
        and after.get("player_character_id") == player
        and event.get("root_character_id") == player
        and isinstance(event_binding, Mapping)
        and event_binding.get("snapshot_id") == after.get("snapshot_id")
        and event_binding.get("revision") == after.get("revision")
        and event_binding.get("native_revision") == after.get("native_revision")
    ):
        return _red(SCOREBOARD_HANDLER, "scoreboard_calibration_binding_drift")
    before_visible = _widget_visible(source_state, "zg361_scoreboard_modal")
    after_visible = _widget_visible(result_state, "zg361_scoreboard_modal")
    packet = {
        "schema_version": 1,
        "handler": SCOREBOARD_HANDLER,
        "observation": {
            "provider_observed": True,
            "action_ack_only": False,
            "connection_generation": generation,
            "player_character_id": player,
            "source_snapshot_id": before["snapshot_id"],
            "result_snapshot_id": after["snapshot_id"],
            "source_revision": before["revision"],
            "result_revision": after["revision"],
            "source_native_revision": before["native_revision"],
            "result_native_revision": after["native_revision"],
        },
        "calibration_event": {
            key: event[key]
            for key in (
                "definition_key",
                "visible",
                "identity_ready",
                "snapshot_revision",
                "event_instance_id",
                "root_character_id",
            )
        },
        "scoreboard_before": {
            "observed_state_revision": source_state.get("observed_state_revision"),
            "semantic_fingerprint": source_state.get("semantic_fingerprint_v1"),
            "modal_visible": before_visible,
        },
        "scoreboard_after": {
            "observed_state_revision": result_state.get("observed_state_revision"),
            "semantic_fingerprint": result_state.get("semantic_fingerprint_v1"),
            "modal_visible": after_visible,
        },
    }
    return _finish(SCOREBOARD_HANDLER, packet)


def _future_business_query(
    value: object,
    *,
    capability: str,
    payload_key: str,
) -> tuple[dict[str, object], dict[str, object]] | None:
    if not isinstance(value, Mapping):
        return None
    if not (
        type(value.get("schema_version")) is int
        and value.get("schema_version") == 1
        and value.get("status") == "available"
        and value.get("capability") == capability
        and value.get("source_backend_id") == NATIVE_BACKEND
        and isinstance(value.get("readiness"), Mapping)
        and value["readiness"].get("ready") is True
        and isinstance(value.get("binding"), Mapping)
        and isinstance(value.get(payload_key), Mapping)
    ):
        return None
    return dict(value["binding"]), dict(value[payload_key])


def _event_path_packet_from_future_query(
    handler: str,
    source_event_query: object,
    result_event_query: object,
    business_query: object,
) -> dict[str, object]:
    config = {
        PROMOTION_HANDLER: (
            "zg361pp.147",
            "zg361comp.1",
            PROMOTION_COMPENSATION_QUERY_CAPABILITY,
            "promotion_compensation",
            ("frozen_case", "promotion_choice", "compensation_receipt"),
        ),
        PROJECTS_HANDLER: (
            "zg361cp.26",
            "zg361p3.229",
            PROJECTS_METRICS_QUERY_CAPABILITY,
            "projects_metrics",
            ("contribution", "metrics_result"),
        ),
    }
    source_key, result_key, capability, payload_key, groups = config[handler]
    source_event = _event_query(source_event_query, source_key)
    result_event = _event_query(result_event_query, result_key)
    queried = _future_business_query(
        business_query, capability=capability, payload_key=payload_key
    )
    if source_event is None or result_event is None:
        return _red(handler, "event_provider_binding_missing")
    if queried is None:
        return _red(
            handler,
            "required_business_provider_unavailable",
            missing=(capability,),
        )
    binding, payload = queried
    if not set(_FUTURE_BINDING_KEYS).issubset(binding) or any(
        group not in payload
        for group in (*groups, "source_identity", "result_identity")
    ):
        return _red(handler, "business_provider_projection_incomplete")
    source_binding = source_event["binding"]
    result_binding = result_event["binding"]
    if not (
        isinstance(source_binding, Mapping)
        and isinstance(result_binding, Mapping)
        and source_binding.get("snapshot_id") == binding.get("source_snapshot_id")
        and source_binding.get("revision") == binding.get("source_revision")
        and source_binding.get("native_revision") == binding.get("source_native_revision")
        and result_binding.get("snapshot_id") == binding.get("result_snapshot_id")
        and result_binding.get("revision") == binding.get("result_revision")
        and result_binding.get("native_revision") == binding.get("result_native_revision")
        and source_event.get("root_character_id") == binding.get("player_character_id")
        and result_event.get("root_character_id") == binding.get("player_character_id")
        and _positive(binding.get("connection_generation"))
    ):
        return _red(handler, "business_provider_event_binding_drift")
    packet: dict[str, object] = {
        "schema_version": 1,
        "handler": handler,
        "observation": {
            "provider_observed": True,
            "action_ack_only": False,
            **{key: binding[key] for key in _FUTURE_BINDING_KEYS},
        },
        "source_event": {
            "definition_key": source_event["definition_key"],
            "visible": True,
            "identity_ready": True,
            "snapshot_revision": source_event["snapshot_revision"],
            "identity": payload["source_identity"],
        },
        "result_event": {
            "definition_key": result_event["definition_key"],
            "visible": True,
            "identity_ready": True,
            "snapshot_revision": result_event["snapshot_revision"],
            "identity": payload["result_identity"],
        },
    }
    for group in groups:
        packet[group] = payload[group]
    return _finish(handler, packet)


def build_promotion_compensation_provider_packet(
    source_event_query: object,
    result_event_query: object,
    business_query: object = None,
) -> dict[str, object]:
    return _event_path_packet_from_future_query(
        PROMOTION_HANDLER, source_event_query, result_event_query, business_query
    )


def build_projects_metrics_provider_packet(
    source_event_query: object,
    result_event_query: object,
    business_query: object = None,
) -> dict[str, object]:
    return _event_path_packet_from_future_query(
        PROJECTS_HANDLER, source_event_query, result_event_query, business_query
    )


def build_cross_cycle_endgame_provider_packet(
    source_event_query: object,
    result_event_query: object,
    source_workforce_query: object,
    result_workforce_query: object,
) -> dict[str, object]:
    """Adapt the existing validated Workforce collective response."""

    source_event = _event_query(source_event_query, "zg361we.356")
    result_event = _event_query(result_event_query, "zg361we.361")
    if source_event is None or result_event is None:
        return _red(ENDGAME_HANDLER, "event_provider_binding_missing")
    if not (
        isinstance(source_workforce_query, Mapping)
        and source_workforce_query.get("status") == "available"
        and isinstance(result_workforce_query, Mapping)
        and result_workforce_query.get("status") == "available"
        and isinstance(source_workforce_query.get("readiness"), Mapping)
        and source_workforce_query["readiness"].get("ready") is True
        and isinstance(result_workforce_query.get("readiness"), Mapping)
        and result_workforce_query["readiness"].get("ready") is True
    ):
        return _red(ENDGAME_HANDLER, "workforce_collective_provider_unavailable")
    before = _binding(source_workforce_query)
    after = _binding(result_workforce_query)
    before_source = _source(source_workforce_query)
    after_source = _source(result_workforce_query)
    source_identity = _case_identity(source_workforce_query.get("al_case"))
    result_identity = _case_identity(result_workforce_query.get("al_case"))
    debt_group = result_workforce_query.get("route_c_debt")
    charter_group = result_workforce_query.get("charter_gate")
    debt_identity = _case_identity(debt_group)
    charter_identity = _case_identity(charter_group)
    if None in (
        before,
        after,
        before_source,
        after_source,
        source_identity,
        result_identity,
        debt_identity,
        charter_identity,
    ):
        return _red(ENDGAME_HANDLER, "workforce_business_projection_incomplete")
    assert before is not None and after is not None
    assert before_source is not None and after_source is not None
    assert source_identity is not None and result_identity is not None
    assert debt_identity is not None and charter_identity is not None
    source_event_binding = source_event["binding"]
    result_event_binding = result_event["binding"]
    generation = before_source.get("connection_generation")
    player = before.get("player_character_id")
    if not (
        source_identity == result_identity
        and isinstance(source_event_binding, Mapping)
        and isinstance(result_event_binding, Mapping)
        and source_event_binding.get("snapshot_id") == before.get("snapshot_id")
        and source_event_binding.get("native_revision") == before.get("native_revision")
        and result_event_binding.get("snapshot_id") == after.get("snapshot_id")
        and result_event_binding.get("native_revision") == after.get("native_revision")
        and _positive(generation)
        and after_source.get("connection_generation") == generation
        and _positive(player)
        and after.get("player_character_id") == player
        and source_identity["owner_character_id"] == player
        and _event_has_character(source_event, int(source_identity["subject_character_id"]))
        and _event_has_character(result_event, int(result_identity["subject_character_id"]))
    ):
        return _red(ENDGAME_HANDLER, "workforce_event_case_binding_drift")
    packet = {
        "schema_version": 1,
        "handler": ENDGAME_HANDLER,
        "observation": {
            "provider_observed": True,
            "action_ack_only": False,
            "connection_generation": generation,
            "player_character_id": player,
            "source_snapshot_id": before["snapshot_id"],
            "result_snapshot_id": after["snapshot_id"],
            "source_revision": before["revision"],
            "result_revision": after["revision"],
            "source_native_revision": before["native_revision"],
            "result_native_revision": after["native_revision"],
        },
        "source_event": {
            "definition_key": "zg361we.356",
            "visible": True,
            "identity_ready": True,
            "snapshot_revision": before["native_revision"],
            "identity": source_identity,
        },
        "result_event": {
            "definition_key": "zg361we.361",
            "visible": True,
            "identity_ready": True,
            "snapshot_revision": after["native_revision"],
            "identity": result_identity,
        },
        "carried_debt": {
            "identity": debt_identity,
            "origin_cycle_serial": _typed_value(debt_group, "cycle_serial"),
            "carried_into_cycle_serial": _typed_value(debt_group, "due_cycle_serial"),
            "provider_observed": True,
        },
        "default_change": {
            "identity": charter_identity,
            "charter_id": _typed_value(charter_group, "prepared_charter_id"),
            "adopted_cycle_serial": _typed_value(charter_group, "adopted_cycle_serial"),
            "effective_cycle_serial": _typed_value(charter_group, "effective_cycle_serial"),
            "provider_observed": True,
        },
    }
    return _finish(ENDGAME_HANDLER, packet)


__all__ = [
    "PROJECTS_METRICS_QUERY_CAPABILITY",
    "PROMOTION_COMPENSATION_QUERY_CAPABILITY",
    "build_cross_cycle_endgame_provider_packet",
    "build_projects_metrics_provider_packet",
    "build_promotion_compensation_provider_packet",
    "build_scoreboard_calibration_provider_packet",
]
