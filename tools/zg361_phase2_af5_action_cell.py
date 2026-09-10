#!/usr/bin/env python3
"""Reach the real AF5 card, choose route 3, and independently observe closure."""

from __future__ import annotations

import copy
import time
from collections.abc import Callable, Mapping

from zg361_phase2_promotion_compensation_action_cell import (
    _event_context,
    _snapshot_binding,
)
from zg361_phase2_promotion_source_production_entry import (
    _event_definition,
    enter_promotion_source_checkpoint_v1,
)

EVENT = "zg361comp.1"
OPTION = 42
QUERY_CAPABILITY = "game.command.query-zhongguo-compensation-af5-snapshot-v1"


class Af5ActionCellError(RuntimeError):
    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {**copy.deepcopy(dict(evidence)), "result": "RED",
                         "reason_code": reason_code}
        super().__init__(f"AF5 action cell RED [{reason_code}]")


def advance_to_af5(service: object) -> dict[str, object]:
    """Use the existing product driver, including real clock/event transitions."""
    snapshot = service.snapshot()
    origin = int(snapshot["date_raw"])
    # R185 -> R192 reached AF5 in 55 days. Keep this suffix bounded; never
    # silently wait a new annual cycle after loading an unsuitable checkpoint.
    evidence: dict[str, object] = {
        "timeline_origin_date_raw": origin,
        "absolute_end_date_raw": origin + 180 * 24,
    }
    try:
        return enter_promotion_source_checkpoint_v1(
            service,
            pause_on_event_definition_key=EVENT,
            pause_on_event_option_number=OPTION,
            prefer_natural_cycle=True,
            timeout_seconds=600.0,
            evidence_out=evidence,
        )
    except Exception as error:
        evidence["driver_error"] = str(error)
        evidence["driver_error_evidence"] = copy.deepcopy(getattr(error, "evidence", None))
        raise Af5ActionCellError("advance_to_af5", evidence) from error


def _value(group: Mapping[str, object], key: str) -> object:
    leaf = group.get(key)
    if not isinstance(leaf, Mapping) or leaf.get("status") != "available":
        raise ValueError(f"AF5 field unavailable: {key}")
    return leaf.get("value")


def _case_identity(frame: Mapping[str, object]) -> dict[str, object]:
    identity = frame["af5"]["case"]["identity"]
    return {key: _value(identity, key) for key in (
        "owner_character_id", "subject_character_id", "cycle_serial", "case_serial",
    )}


def _read_event(service: object) -> tuple[dict[str, object], dict[str, object]]:
    binding = _snapshot_binding(service.snapshot(), expected_event=True)
    key, query = _event_definition(service, binding)
    if key != EVENT:
        raise ValueError(f"AF5 target changed to {key!r}")
    binding.update(query["binding"])
    _event_context(query, binding=binding, expected_definition_key=EVENT,
                   require_source_scopes=False)
    options = query["current_event_window_context"]["options"]
    if not any(row.get("native_option_index") == OPTION - 1
               and row.get("shown") is True and row.get("enabled") is True
               for row in options):
        raise ValueError("AF5 authored 42/native 41 is not selectable")
    return binding, query


def _read_af5(service: object, nonce: str) -> dict[str, object]:
    snapshot = _snapshot_binding(service.snapshot(), expected_event=False)
    frame = service.query_zhongguo_compensation_af5_snapshot_v1(
        nonce, expected_revision=int(snapshot["revision"]),
    )
    if (frame.get("status") != "available"
            or frame.get("source_backend_id") != "native-headless"
            or frame.get("readiness", {}).get("ready") is not True):
        raise ValueError(f"independent AF5 observer unavailable: {frame!r}")
    return frame


def run_af5_terminal_action_cell(
    service: object,
    *,
    advance_to_af5: Callable[[object], Mapping[str, object]],
    request_nonce: str,
    terminal_timeout_seconds: float = 10.0,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_af5_terminal_action_cell",
        "result": "RED",
        "event_definition_key": EVENT,
        "selected_option_number": None,
        "selected_native_option_index": None,
        "provider_observed": False,
        "terminal_postcondition_verified": False,
        "action_ack_is_business_postcondition": False,
        "fixture_used": False,
        "console_used": False,
    }
    stage = "advance_to_af5"
    try:
        capabilities = service.capabilities().get("bridge_capabilities", [])
        if QUERY_CAPABILITY not in capabilities:
            raise ValueError("standalone native AF5 capability is absent")
        if terminal_timeout_seconds <= 0:
            raise ValueError("terminal timeout must be positive")
        evidence["advance"] = dict(advance_to_af5(service))
        if evidence["advance"].get("result") != "GREEN":
            raise ValueError("product timeline did not reach the target")
        stage = "af5_before"
        before_binding, event_query = _read_event(service)
        evidence["event_before"] = event_query
        before = _read_af5(service, request_nonce + ".before")
        evidence["before"] = before
        portfolio = before["af5"]["portfolio"]
        case = before["af5"]["case"]
        if not (_value(portfolio, "domain") == 3
                and _value(portfolio, "stage") == 5
                and _value(case, "state") == 5
                and _value(case, "active") is True
                and before["terminal"] is False):
            raise ValueError("observed case is not awaiting AF5 closure")
        identity = _case_identity(before)
        if identity["owner_character_id"] != before_binding["player_character_id"]:
            raise ValueError("AF5 case owner is not the played event owner")
        stage = "af5_select"
        selected_binding, selected_query = _read_event(service)
        evidence["event_pre_selection"] = selected_query
        for key in ("player_character_id", "connection_generation", "date_raw", "event_instance_id"):
            if selected_binding[key] != before_binding[key]:
                raise ValueError(f"AF5 event changed before input: {key}")
        # Read-only queries can publish a fresh public revision. Bind the input
        # to the current paused frame while retaining the exact event identity.
        latest = _snapshot_binding(service.snapshot(), expected_event=True)
        for key in ("player_character_id", "connection_generation", "date_raw", "event_instance_id"):
            if latest[key] != before_binding[key]:
                raise ValueError(f"AF5 input binding changed: {key}")
        selection = service.select_event_option(
            OPTION, event_instance_id=int(latest["event_instance_id"]),
            expected_revision=int(latest["revision"]),
        )
        evidence["selection"] = copy.deepcopy(selection)
        evidence["selected_option_number"] = OPTION
        evidence["selected_native_option_index"] = OPTION - 1
        if selection.get("accepted") is not True:
            raise ValueError("AF5 option submission was not accepted")
        stage = "af5_terminal_observation"
        deadline = clock() + terminal_timeout_seconds
        while True:
            after_binding = _snapshot_binding(service.snapshot(), expected_event=False)
            evidence["after_binding"] = after_binding
            if any(after_binding[key] != before_binding[key] for key in (
                "player_character_id", "connection_generation", "date_raw",
            )):
                raise ValueError("AF5 terminal observation crossed its paused owner frame")
            # The service validates native provenance and same-frame semantics.
            after = _read_af5(service, request_nonce + ".after")
            evidence["after"] = after
            evidence["provider_observed"] = True
            if _case_identity(after) != identity:
                raise ValueError("AF5 observer changed the case identity")
            if (after["terminal"] is True
                    and after_binding["event_instance_id"] != before_binding["event_instance_id"]
                    and _value(after["af5"]["case"]["identity"], "revision")
                    > _value(case["identity"], "revision")):
                evidence["terminal_postcondition_verified"] = True
                evidence["result"] = "GREEN"
                return evidence
            if clock() >= deadline:
                raise ValueError("native AF5 terminal was not observed before the deadline")
            sleeper(0.05)
    except Exception as error:
        evidence["failure_stage"] = stage
        evidence["error"] = str(error)
        if hasattr(error, "evidence"):
            evidence["cause_evidence"] = copy.deepcopy(error.evidence)
        raise Af5ActionCellError(stage, evidence) from error
