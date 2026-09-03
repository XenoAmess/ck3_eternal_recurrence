#!/usr/bin/env python3
"""Strict, read-only business postconditions for Phase2 promo spans.

The visual handlers already prove that an action was submitted and that an
expected event surface became visible.  That is transport evidence, not a
business result.  This module validates provider-produced evidence packets
which bind the visible surfaces to product identities and receipts.

It does not query CK3, write artifacts, advance time, or turn an ACK/revision
change into success.  A live producer must first obtain the packet fields from
paused, provider-owned observations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final


SCOREBOARD_HANDLER: Final = "capture_fact_quota_calibration"
PROMOTION_HANDLER: Final = "capture_promotion_compensation"
PROJECTS_HANDLER: Final = "capture_projects_metrics"
ENDGAME_HANDLER: Final = "capture_cross_cycle_endgame"

_HANDLERS: Final = {
    SCOREBOARD_HANDLER,
    PROMOTION_HANDLER,
    PROJECTS_HANDLER,
    ENDGAME_HANDLER,
}
_IDENTITY_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
}
_EVENT_KEYS: Final = {
    "definition_key",
    "visible",
    "identity_ready",
    "snapshot_revision",
    "identity",
}
_CALIBRATION_EVENT_KEYS: Final = {
    "definition_key",
    "visible",
    "identity_ready",
    "snapshot_revision",
    "event_instance_id",
    "root_character_id",
}
_OBSERVATION_KEYS: Final = {
    "provider_observed",
    "action_ack_only",
    "connection_generation",
    "player_character_id",
    "source_snapshot_id",
    "result_snapshot_id",
    "source_revision",
    "result_revision",
    "source_native_revision",
    "result_native_revision",
}


def _is_int(value: object, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _exact(value: object, keys: set[str]) -> dict[str, object] | None:
    if not isinstance(value, dict) or set(value) != keys:
        return None
    return value


def _identity(value: object) -> tuple[int, int, int, int] | None:
    row = _exact(value, _IDENTITY_KEYS)
    if row is None:
        return None
    values = tuple(row[key] for key in (
        "owner_character_id",
        "subject_character_id",
        "cycle_serial",
        "case_serial",
    ))
    if not all(_is_int(item, minimum=1) for item in values):
        return None
    return values  # type: ignore[return-value]


def _event(value: object, expected_key: str) -> tuple[dict[str, object] | None, bool]:
    row = _exact(value, _EVENT_KEYS)
    valid = bool(
        row is not None
        and row.get("definition_key") == expected_key
        and row.get("visible") is True
        and row.get("identity_ready") is True
        and _is_int(row.get("snapshot_revision"), minimum=1)
        and _identity(row.get("identity")) is not None
    )
    return row, valid


def _calibration_event(value: object) -> tuple[dict[str, object] | None, bool]:
    row = _exact(value, _CALIBRATION_EVENT_KEYS)
    valid = bool(
        row is not None
        and row.get("definition_key") == "zg361.1"
        and row.get("visible") is True
        and row.get("identity_ready") is True
        and _is_int(row.get("snapshot_revision"), minimum=1)
        and _is_int(row.get("event_instance_id"), minimum=1)
        and _is_int(row.get("root_character_id"), minimum=1)
    )
    return row, valid


def _observation(value: object) -> tuple[dict[str, object] | None, dict[str, bool]]:
    row = _exact(value, _OBSERVATION_KEYS)
    checks = {
        "provider_observed": row is not None and row.get("provider_observed") is True,
        "not_ack_only": row is not None and row.get("action_ack_only") is False,
        "connection_generation": row is not None
        and _is_int(row.get("connection_generation"), minimum=1),
        "player_character": row is not None
        and _is_int(row.get("player_character_id"), minimum=1),
        "snapshot_advanced": row is not None
        and isinstance(row.get("source_snapshot_id"), str)
        and bool(row.get("source_snapshot_id"))
        and isinstance(row.get("result_snapshot_id"), str)
        and bool(row.get("result_snapshot_id"))
        and row.get("source_snapshot_id") != row.get("result_snapshot_id"),
        "revision_advanced": row is not None
        and _is_int(row.get("source_revision"))
        and _is_int(row.get("result_revision"))
        and int(row["result_revision"]) > int(row["source_revision"]),
        "native_revision_advanced": row is not None
        and _is_int(row.get("source_native_revision"), minimum=1)
        and _is_int(row.get("result_native_revision"), minimum=1)
        and int(row["result_native_revision"]) > int(row["source_native_revision"]),
    }
    return row, checks


def _result(handler: str, checks: dict[str, bool]) -> dict[str, object]:
    failed = [name for name, passed in checks.items() if passed is not True]
    green = not failed
    return {
        "schema_version": 1,
        "result": "GREEN" if green else "RED",
        "provider_observed": checks.get("provider_observed") is True,
        "postcondition_green": green,
        "handler": handler,
        "reason_code": None if green else failed[0],
        "checks": checks,
    }


def _base(value: object, handler: str, keys: set[str]) -> tuple[dict[str, object] | None, dict[str, object] | None, dict[str, bool]]:
    evidence = _exact(value, keys)
    observation, checks = _observation(
        evidence.get("observation") if evidence is not None else None
    )
    checks = {
        "schema_version": evidence is not None
        and type(evidence.get("schema_version")) is int
        and evidence.get("schema_version") == 1,
        "handler": evidence is not None
        and type(evidence.get("handler")) is str
        and evidence.get("handler") == handler,
        **checks,
    }
    return evidence, observation, checks


def verify_scoreboard_calibration_postcondition(value: object) -> dict[str, object]:
    """Require a visible calibration event plus a changed scoreboard state."""

    handler = SCOREBOARD_HANDLER
    evidence, observation, checks = _base(
        value,
        handler,
        {"schema_version", "handler", "observation", "calibration_event", "scoreboard_before", "scoreboard_after"},
    )
    event, event_ok = _calibration_event(
        evidence.get("calibration_event") if evidence else None
    )
    before = _exact(
        evidence.get("scoreboard_before") if evidence else None,
        {"observed_state_revision", "semantic_fingerprint", "modal_visible"},
    )
    after = _exact(
        evidence.get("scoreboard_after") if evidence else None,
        {"observed_state_revision", "semantic_fingerprint", "modal_visible"},
    )
    checks.update(
        {
            "observation_frames_typed": observation is not None
            and isinstance(observation.get("source_snapshot_id"), str)
            and bool(observation.get("source_snapshot_id"))
            and isinstance(observation.get("result_snapshot_id"), str)
            and bool(observation.get("result_snapshot_id"))
            and _is_int(observation.get("source_revision"), minimum=0)
            and _is_int(observation.get("result_revision"), minimum=0)
            and _is_int(observation.get("source_native_revision"), minimum=1)
            and _is_int(observation.get("result_native_revision"), minimum=1),
            "calibration_event_visible_and_identity_ready": event_ok,
            "calibration_event_bound_to_result_frame": event is not None
            and observation is not None
            and event.get("snapshot_revision") == observation.get("result_native_revision"),
            "calibration_event_bound_to_player": event is not None
            and observation is not None
            and event.get("root_character_id") == observation.get("player_character_id"),
            "scoreboard_states_typed": before is not None
            and after is not None
            and _is_int(before.get("observed_state_revision"), minimum=1)
            and _is_int(after.get("observed_state_revision"), minimum=1)
            and isinstance(before.get("semantic_fingerprint"), str)
            and bool(before.get("semantic_fingerprint"))
            and isinstance(after.get("semantic_fingerprint"), str)
            and bool(after.get("semantic_fingerprint"))
            and isinstance(before.get("modal_visible"), bool)
            and isinstance(after.get("modal_visible"), bool),
            "scoreboard_observation_revision_advanced": before is not None
            and after is not None
            and _is_int(before.get("observed_state_revision"), minimum=1)
            and _is_int(after.get("observed_state_revision"), minimum=1)
            and int(after["observed_state_revision"])
            > int(before["observed_state_revision"]),
            "scoreboard_semantic_fingerprint_changed": before is not None
            and after is not None
            and before.get("semantic_fingerprint") != after.get("semantic_fingerprint"),
            "scoreboard_visible_after_calibration": after is not None
            and after.get("modal_visible") is True,
        }
    )
    # Opening the read-only scoreboard is a provider-local UI transition on a
    # paused world.  Public/native world revisions may legitimately remain
    # stable, so those generic event-path checks are not part of this gate.
    # The scoreboard-owned revision/fingerprint checks below carry the actual
    # semantic transition.
    checks.pop("snapshot_advanced")
    checks.pop("revision_advanced")
    checks.pop("native_revision_advanced")
    return _result(handler, checks)


def verify_promotion_compensation_postcondition(value: object) -> dict[str, object]:
    """Bind the promotion choice and compensation receipt to one frozen case."""

    handler = PROMOTION_HANDLER
    evidence, observation, checks = _base(
        value,
        handler,
        {
            "schema_version",
            "handler",
            "observation",
            "source_event",
            "result_event",
            "frozen_case",
            "promotion_choice",
            "compensation_receipt",
        },
    )
    source, source_ok = _event(
        evidence.get("source_event") if evidence else None, "zg361pp.147"
    )
    result, result_ok = _event(
        evidence.get("result_event") if evidence else None, "zg361comp.1"
    )
    frozen = _exact(
        evidence.get("frozen_case") if evidence else None,
        {"identity", "frozen"},
    )
    choice = _exact(
        evidence.get("promotion_choice") if evidence else None,
        {"identity", "option_number", "receipt_serial", "provider_observed"},
    )
    compensation = _exact(
        evidence.get("compensation_receipt") if evidence else None,
        {"identity", "receipt_serial", "posted", "provider_observed"},
    )
    identities = [
        _identity(source.get("identity")) if source else None,
        _identity(result.get("identity")) if result else None,
        _identity(frozen.get("identity")) if frozen else None,
        _identity(choice.get("identity")) if choice else None,
        _identity(compensation.get("identity")) if compensation else None,
    ]
    checks.update(
        {
            "source_event_visible_and_identity_ready": source_ok,
            "result_event_visible_and_identity_ready": result_ok,
            "events_bound_to_observation_frames": source is not None
            and result is not None
            and observation is not None
            and source.get("snapshot_revision") == observation.get("source_native_revision")
            and result.get("snapshot_revision") == observation.get("result_native_revision"),
            "frozen_case_observed": frozen is not None
            and frozen.get("frozen") is True
            and identities[2] is not None,
            "promotion_choice_receipt_observed": choice is not None
            and choice.get("provider_observed") is True
            and _is_int(choice.get("option_number"), minimum=1)
            and _is_int(choice.get("receipt_serial"), minimum=1),
            "compensation_receipt_posted": compensation is not None
            and compensation.get("provider_observed") is True
            and compensation.get("posted") is True
            and _is_int(compensation.get("receipt_serial"), minimum=1),
            "same_frozen_case_identity": None not in identities
            and len(set(identities)) == 1,
            "case_owner_is_observed_player": identities[0] is not None
            and observation is not None
            and identities[0][0] == observation.get("player_character_id"),
        }
    )
    return _result(handler, checks)


def verify_projects_metrics_postcondition(value: object) -> dict[str, object]:
    """Bind contribution and metrics records to one identity-ready project case."""

    handler = PROJECTS_HANDLER
    evidence, observation, checks = _base(
        value,
        handler,
        {
            "schema_version",
            "handler",
            "observation",
            "source_event",
            "result_event",
            "contribution",
            "metrics_result",
        },
    )
    source, source_ok = _event(
        evidence.get("source_event") if evidence else None, "zg361cp.26"
    )
    result, result_ok = _event(
        evidence.get("result_event") if evidence else None, "zg361p3.229"
    )
    contribution = _exact(
        evidence.get("contribution") if evidence else None,
        {"identity", "receipt_id", "value", "provider_observed"},
    )
    metrics = _exact(
        evidence.get("metrics_result") if evidence else None,
        {
            "identity",
            "source_contribution_receipt_id",
            "metrics_revision",
            "dictionary_key",
            "provider_observed",
        },
    )
    identities = [
        _identity(source.get("identity")) if source else None,
        _identity(result.get("identity")) if result else None,
        _identity(contribution.get("identity")) if contribution else None,
        _identity(metrics.get("identity")) if metrics else None,
    ]
    checks.update(
        {
            "source_event_visible_and_identity_ready": source_ok,
            "result_event_visible_and_identity_ready": result_ok,
            "events_bound_to_observation_frames": source is not None
            and result is not None
            and observation is not None
            and source.get("snapshot_revision") == observation.get("source_native_revision")
            and result.get("snapshot_revision") == observation.get("result_native_revision"),
            "contribution_provider_observed": contribution is not None
            and contribution.get("provider_observed") is True
            and _is_int(contribution.get("receipt_id"), minimum=1)
            and _is_integer(contribution.get("value")),
            "metrics_provider_observed": metrics is not None
            and metrics.get("provider_observed") is True
            and _is_int(metrics.get("source_contribution_receipt_id"), minimum=1)
            and _is_int(metrics.get("metrics_revision"), minimum=1)
            and isinstance(metrics.get("dictionary_key"), str)
            and bool(metrics.get("dictionary_key")),
            "contribution_metrics_receipt_identity": contribution is not None
            and metrics is not None
            and contribution.get("receipt_id")
            == metrics.get("source_contribution_receipt_id"),
            "same_project_case_identity": None not in identities
            and len(set(identities)) == 1,
            "case_owner_is_observed_player": identities[0] is not None
            and observation is not None
            and identities[0][0] == observation.get("player_character_id"),
        }
    )
    return _result(handler, checks)


def verify_cross_cycle_endgame_postcondition(value: object) -> dict[str, object]:
    """Require observed carried debt and next-cycle default-change semantics."""

    handler = ENDGAME_HANDLER
    evidence, observation, checks = _base(
        value,
        handler,
        {
            "schema_version",
            "handler",
            "observation",
            "source_event",
            "result_event",
            "carried_debt",
            "default_change",
        },
    )
    source, source_ok = _event(
        evidence.get("source_event") if evidence else None, "zg361we.356"
    )
    result, result_ok = _event(
        evidence.get("result_event") if evidence else None, "zg361we.361"
    )
    debt = _exact(
        evidence.get("carried_debt") if evidence else None,
        {
            "identity",
            "origin_cycle_serial",
            "carried_into_cycle_serial",
            "provider_observed",
        },
    )
    default = _exact(
        evidence.get("default_change") if evidence else None,
        {
            "identity",
            "charter_id",
            "adopted_cycle_serial",
            "effective_cycle_serial",
            "provider_observed",
        },
    )
    source_identity = _identity(source.get("identity")) if source else None
    result_identity = _identity(result.get("identity")) if result else None
    debt_identity = _identity(debt.get("identity")) if debt else None
    default_identity = _identity(default.get("identity")) if default else None
    terminal_cycle = result_identity[2] if result_identity else None
    terminal_owner_subject = result_identity[:2] if result_identity else None
    checks.update(
        {
            "source_event_visible_and_identity_ready": source_ok,
            "result_event_visible_and_identity_ready": result_ok,
            "events_bound_to_observation_frames": source is not None
            and result is not None
            and observation is not None
            and source.get("snapshot_revision") == observation.get("source_native_revision")
            and result.get("snapshot_revision") == observation.get("result_native_revision"),
            "same_terminal_case_identity": source_identity is not None
            and source_identity == result_identity,
            "carried_debt_provider_observed": debt is not None
            and debt.get("provider_observed") is True,
            "default_change_provider_observed": default is not None
            and default.get("provider_observed") is True
            and _is_int(default.get("charter_id"), minimum=1),
            "debt_bound_to_terminal_owner_subject": debt_identity is not None
            and terminal_owner_subject is not None
            and debt_identity[:2] == terminal_owner_subject,
            "default_bound_to_terminal_owner_subject": default_identity is not None
            and terminal_owner_subject is not None
            and default_identity[:2] == terminal_owner_subject,
            "debt_carried_into_terminal_cycle": debt is not None
            and terminal_cycle is not None
            and _is_int(debt.get("origin_cycle_serial"), minimum=1)
            and debt.get("origin_cycle_serial") == terminal_cycle
            and debt.get("carried_into_cycle_serial") == terminal_cycle + 1,
            "default_changes_next_cycle": default is not None
            and terminal_cycle is not None
            and default.get("adopted_cycle_serial") == terminal_cycle
            and default.get("effective_cycle_serial") == terminal_cycle + 1,
            "terminal_owner_is_observed_player": result_identity is not None
            and observation is not None
            and result_identity[0] == observation.get("player_character_id"),
        }
    )
    return _result(handler, checks)


def verify_phase2_business_postcondition(
    handler: str, value: object
) -> dict[str, object]:
    """Dispatch one exact handler without normalizing a malformed name."""

    if handler not in _HANDLERS:
        return _result(str(handler), {"supported_handler": False})
    verifier = {
        SCOREBOARD_HANDLER: verify_scoreboard_calibration_postcondition,
        PROMOTION_HANDLER: verify_promotion_compensation_postcondition,
        PROJECTS_HANDLER: verify_projects_metrics_postcondition,
        ENDGAME_HANDLER: verify_cross_cycle_endgame_postcondition,
    }[handler]
    return verifier(value)


__all__ = [
    "ENDGAME_HANDLER",
    "PROJECTS_HANDLER",
    "PROMOTION_HANDLER",
    "SCOREBOARD_HANDLER",
    "verify_cross_cycle_endgame_postcondition",
    "verify_phase2_business_postcondition",
    "verify_projects_metrics_postcondition",
    "verify_promotion_compensation_postcondition",
    "verify_scoreboard_calibration_postcondition",
]
