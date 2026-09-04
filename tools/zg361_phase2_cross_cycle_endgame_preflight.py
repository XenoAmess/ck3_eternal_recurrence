#!/usr/bin/env python3
"""No-action preflight for the cross-cycle endgame gameplay cell."""

from __future__ import annotations

from typing import Mapping

from zg361_phase2_cross_cycle_endgame_action_cell import (
    HANDLER,
    QUERY_EVENT_CAPABILITY,
    SELECT_EVENT_OPTION_CAPABILITY,
    SOURCE_EVENT,
    SPAN_ID,
    WORKFORCE_QUERY_CAPABILITY,
    CompletionExecutor,
    CrossCycleEndgameCellError,
    EndgameOwnerService,
    SubjectSessionFactory,
    inspect_cross_cycle_endgame_source,
)


class CrossCycleEndgamePreflightError(RuntimeError):
    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **dict(evidence),
            "result": "RED",
            "reason_code": reason_code,
            "action_executed": False,
            "live_proof_claimed": False,
        }
        super().__init__(f"cross-cycle endgame preflight RED [{reason_code}]")


def preflight_cross_cycle_endgame_action_cell(
    owner_service: EndgameOwnerService,
    *,
    source_checkpoint_restore: Mapping[str, object],
    completion_executor: CompletionExecutor | None,
    subject_session_factory: SubjectSessionFactory | None,
) -> dict[str, object]:
    """Verify the source surface and every explicit live seam without mutation."""

    capabilities = owner_service.capabilities()
    advertised = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, Mapping)
        else None
    )
    required = (
        QUERY_EVENT_CAPABILITY,
        SELECT_EVENT_OPTION_CAPABILITY,
        WORKFORCE_QUERY_CAPABILITY,
    )
    missing = [
        capability
        for capability in required
        if not isinstance(advertised, list) or capability not in advertised
    ]
    if missing:
        raise CrossCycleEndgamePreflightError(
            "required_capability_missing",
            {
                "required_capabilities": list(required),
                "advertised_capabilities": advertised,
                "missing_capabilities": missing,
            },
        )
    if not callable(completion_executor):
        raise CrossCycleEndgamePreflightError(
            "completion_executor_missing",
            {"required_transition": "zg361we.356_to_m360_route_c_to_zg361we.361"},
        )
    if not callable(subject_session_factory):
        raise CrossCycleEndgamePreflightError(
            "subject_proof_session_factory_missing",
            {
                "required_transition": (
                    "hash_identical_result_checkpoint_owner_to_subject"
                )
            },
        )
    try:
        source = inspect_cross_cycle_endgame_source(
            owner_service, source_checkpoint_restore=source_checkpoint_restore
        )
    except CrossCycleEndgameCellError as error:
        raise CrossCycleEndgamePreflightError(
            "source_surface_not_ready",
            {
                "cell_reason_code": error.reason_code,
                "cell_evidence": error.evidence,
            },
        ) from error
    return {
        "schema_version": 1,
        "result": "GREEN",
        "readiness": "static-ready-live-pending",
        "span_id": SPAN_ID,
        "handler": HANDLER,
        "source_event_definition_key": SOURCE_EVENT,
        "required_capabilities": list(required),
        "source_checkpoint_ready": True,
        "completion_executor_ready": True,
        "subject_proof_session_factory_ready": True,
        "owner_event_subject_provider_split": True,
        "action_executed": False,
        "live_proof_claimed": False,
        "source": source,
    }


__all__ = [
    "CrossCycleEndgamePreflightError",
    "preflight_cross_cycle_endgame_action_cell",
]
