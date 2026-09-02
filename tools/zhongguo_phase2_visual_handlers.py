#!/usr/bin/env python3
"""Real-surface adapters for the four phase-two promo handler gaps.

The adapters reuse the production scoreboard action cell and the public
paused event-window/select-option primitives.  They do not launch CK3, control
the recorder, register a producer, or infer success from an action ACK.  A
caller must provide bounded real-game advancement and provider postcondition
verifiers for the three multi-event product paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Mapping, Protocol

from zhongguo_phase2_capture_choreography import (
    Phase2CaptureScenario,
    Phase2SpanDriver,
)
from zhongguo_phase2_promo_producer import Phase2PromoCaptureContext


SCOREBOARD_HANDLER: Final = "capture_fact_quota_calibration"
PROMOTION_HANDLER: Final = "capture_promotion_compensation"
PROJECTS_HANDLER: Final = "capture_projects_metrics"
ENDGAME_HANDLER: Final = "capture_cross_cycle_endgame"


@dataclass(frozen=True, slots=True)
class EventPathPlan:
    handler: str
    source_event: str
    result_event: str
    option_number: int
    semantic_path: str


EVENT_PATH_PLANS: Final = {
    PROMOTION_HANDLER: EventPathPlan(
        PROMOTION_HANDLER,
        "zg361pp.147",
        "zg361comp.1",
        1,
        "promotion-package choice -> compensation result",
    ),
    PROJECTS_HANDLER: EventPathPlan(
        PROJECTS_HANDLER,
        "zg361cp.26",
        "zg361p3.229",
        1,
        "project credit choice -> metric-dictionary result",
    ),
    ENDGAME_HANDLER: EventPathPlan(
        ENDGAME_HANDLER,
        "zg361we.356",
        "zg361we.361",
        1,
        "cross-cycle debt/default path -> institutional charter",
    ),
}


class VisualGameplayService(Protocol):
    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]: ...


ScoreboardActionCell = Callable[
    [VisualGameplayService, Path], Mapping[str, object]
]
AdvanceToResult = Callable[
    [
        VisualGameplayService,
        EventPathPlan,
        Phase2PromoCaptureContext,
        Mapping[str, object],
    ],
    Mapping[str, object],
]
PostconditionVerifier = Callable[
    [
        VisualGameplayService,
        EventPathPlan,
        Mapping[str, object],
        Mapping[str, object],
        Phase2PromoCaptureContext,
        Mapping[str, object],
    ],
    Mapping[str, object],
]


class Phase2VisualHandlerError(RuntimeError):
    result: Final = "RED"

    def __init__(
        self, reason_code: str, evidence: Mapping[str, object] | None = None
    ) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **dict(evidence or {}),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"phase-two visual handler RED [{reason_code}]")


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _paused_event_binding(
    service: VisualGameplayService,
    context: Phase2PromoCaptureContext,
    *,
    label: str,
) -> dict[str, object]:
    snapshot = service.snapshot()
    active = snapshot.get("active_event") if isinstance(snapshot, dict) else None
    played = snapshot.get("played_character") if isinstance(snapshot, dict) else None
    diagnostics = snapshot.get("diagnostics") if isinstance(snapshot, dict) else None
    values = {
        "snapshot_id": snapshot.get("snapshot_id") if isinstance(snapshot, dict) else None,
        "revision": snapshot.get("revision") if isinstance(snapshot, dict) else None,
        "native_revision": snapshot.get("native_revision") if isinstance(snapshot, dict) else None,
        "date_raw": snapshot.get("date_raw") if isinstance(snapshot, dict) else None,
        "event_instance_id": active.get("instance_id") if isinstance(active, dict) else None,
        "event_option_count": active.get("option_count") if isinstance(active, dict) else None,
        "player_character_id": played.get("character_id") if isinstance(played, dict) else None,
        "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, dict) else None,
        "connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None,
    }
    checks = {
        "snapshot_object": isinstance(snapshot, dict),
        "paused": isinstance(snapshot, dict) and snapshot.get("paused") is True,
        "map_ready": isinstance(snapshot, dict) and snapshot.get("map_ready") is True,
        "snapshot_id": isinstance(values["snapshot_id"], str) and bool(values["snapshot_id"]),
        "revision": isinstance(values["revision"], int) and not isinstance(values["revision"], bool) and values["revision"] >= 0,
        "native_revision": _positive_integer(values["native_revision"]),
        "date_raw": isinstance(values["date_raw"], int) and not isinstance(values["date_raw"], bool),
        "event_instance": _positive_integer(values["event_instance_id"]),
        "event_option_count": _positive_integer(values["event_option_count"]),
        "player_character": _positive_integer(values["player_character_id"]),
        "tracked_pid": values["bridge_pid"] == context.tracked_ck3_pid,
        "connection_generation": _positive_integer(values["connection_generation"]),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        raise Phase2VisualHandlerError(
            "paused_event_binding_not_ready",
            {"label": label, "failed_checks": failed, "observed": values},
        )
    return {"snapshot": snapshot, **values}


def _event_surface(
    service: VisualGameplayService,
    binding: Mapping[str, object],
    *,
    expected_event: str,
    option_number: int | None,
) -> dict[str, object]:
    response = service.query_current_event_window_context_v1(
        int(binding["event_instance_id"]),
        expected_revision=int(binding["revision"]),
    )
    context = response.get("current_event_window_context") if isinstance(response, dict) else None
    readiness = context.get("readiness") if isinstance(context, dict) else None
    if not (
        isinstance(response, dict)
        and response.get("status") == "available"
        and isinstance(context, dict)
        and context.get("status") == "available"
        and context.get("event_definition_key") == expected_event
        and context.get("current_event_instance_id") == binding["event_instance_id"]
        and context.get("snapshot_revision") == binding["native_revision"]
        and context.get("date_raw") == binding["date_raw"]
        and isinstance(readiness, dict)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True
    ):
        raise Phase2VisualHandlerError(
            "event_surface_not_ready",
            {"expected_event": expected_event, "response": response},
        )
    if option_number is not None:
        options = context.get("options")
        target = next(
            (
                row
                for row in options
                if isinstance(row, dict)
                and row.get("native_option_index") == option_number - 1
            ),
            None,
        ) if isinstance(options, list) else None
        if not (
            isinstance(target, dict)
            and target.get("shown") is True
            and target.get("enabled") is True
        ):
            raise Phase2VisualHandlerError(
                "event_option_not_actionable",
                {"expected_event": expected_event, "option_number": option_number},
            )
    return context


def _typed_scoreboard_visible(evidence: Mapping[str, object]) -> bool:
    if not (
        evidence.get("result") == "GREEN"
        and evidence.get("verified_pass") is True
        and evidence.get("production_capability_advertised") is True
    ):
        return False
    request = evidence.get("action_request")
    later = evidence.get("later_query")
    if not isinstance(request, Mapping) or request.get("action") != "open":
        return False
    widgets = later.get("widgets") if isinstance(later, Mapping) else None
    if not isinstance(widgets, list):
        return False
    modal = next(
        (
            row
            for row in widgets
            if isinstance(row, Mapping)
            and row.get("stable_identity") == "zg361_scoreboard_modal"
        ),
        None,
    )
    visible = modal.get("effective_visible") if isinstance(modal, Mapping) else None
    return (
        isinstance(visible, Mapping)
        and visible.get("status") == "available"
        and visible.get("value") is True
    )


class Phase2VisualHandlerAdapter:
    """Concrete driver delegate for scoreboard and three event paths."""

    def __init__(
        self,
        service: VisualGameplayService,
        *,
        scoreboard_action_cell: ScoreboardActionCell | None = None,
        advance_to_result: Mapping[str, AdvanceToResult] | None = None,
        postcondition_verifiers: Mapping[str, PostconditionVerifier] | None = None,
    ) -> None:
        self.service = service
        self.scoreboard_action_cell = scoreboard_action_cell
        self.advance_to_result = dict(advance_to_result or {})
        self.postcondition_verifiers = dict(postcondition_verifiers or {})

    def available_handlers(self) -> tuple[str, ...]:
        result: list[str] = []
        if callable(self.scoreboard_action_cell):
            result.append(SCOREBOARD_HANDLER)
        for handler in EVENT_PATH_PLANS:
            if callable(self.advance_to_result.get(handler)) and callable(
                self.postcondition_verifiers.get(handler)
            ):
                result.append(handler)
        return tuple(result)

    def run_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        if scenario.handler == SCOREBOARD_HANDLER:
            return self._scoreboard(context)
        plan = EVENT_PATH_PLANS.get(scenario.handler)
        if plan is None:
            raise Phase2VisualHandlerError(
                "handler_not_owned", {"handler": scenario.handler}
            )
        return self._event_path(plan, context, runtime)

    def _scoreboard(
        self, context: Phase2PromoCaptureContext
    ) -> dict[str, object]:
        if not callable(self.scoreboard_action_cell):
            raise Phase2VisualHandlerError("scoreboard_action_cell_unconfigured")
        evidence = self.scoreboard_action_cell(
            self.service, context.artifacts
        )
        if not isinstance(evidence, Mapping) or not _typed_scoreboard_visible(evidence):
            raise Phase2VisualHandlerError(
                "scoreboard_surface_not_green",
                {"action_cell": dict(evidence) if isinstance(evidence, Mapping) else None},
            )
        return {
            "result": "GREEN",
            "surface_visible": True,
            "postcondition_green": True,
            "handler": SCOREBOARD_HANDLER,
            "action_cell": dict(evidence),
        }

    def _event_path(
        self,
        plan: EventPathPlan,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> dict[str, object]:
        advance = self.advance_to_result.get(plan.handler)
        verifier = self.postcondition_verifiers.get(plan.handler)
        if not callable(advance) or not callable(verifier):
            raise Phase2VisualHandlerError(
                "event_path_dependencies_unconfigured", {"handler": plan.handler}
            )
        before = _paused_event_binding(
            self.service, context, label=f"{plan.handler}.source"
        )
        source_context = _event_surface(
            self.service,
            before,
            expected_event=plan.source_event,
            option_number=plan.option_number,
        )
        ack = self.service.select_event_option(
            plan.option_number,
            event_instance_id=int(before["event_instance_id"]),
            expected_revision=int(before["revision"]),
        )
        if not (
            isinstance(ack, dict)
            and ack.get("accepted") is True
            and ack.get("status") == "submitted"
        ):
            raise Phase2VisualHandlerError(
                "event_action_not_submitted",
                {"handler": plan.handler, "action_ack": ack},
            )
        advanced = advance(self.service, plan, context, runtime)
        if not isinstance(advanced, Mapping) or advanced.get("result") != "GREEN":
            raise Phase2VisualHandlerError(
                "result_event_advance_not_green",
                {"handler": plan.handler, "advance": dict(advanced) if isinstance(advanced, Mapping) else None},
            )
        after = _paused_event_binding(
            self.service, context, label=f"{plan.handler}.result"
        )
        result_context = _event_surface(
            self.service,
            after,
            expected_event=plan.result_event,
            option_number=None,
        )
        proof = verifier(
            self.service,
            plan,
            before,
            after,
            context,
            runtime,
        )
        if not (
            isinstance(proof, Mapping)
            and proof.get("result") == "GREEN"
            and proof.get("provider_observed") is True
            and proof.get("postcondition_green") is True
        ):
            raise Phase2VisualHandlerError(
                "provider_postcondition_not_green",
                {"handler": plan.handler, "postcondition": dict(proof) if isinstance(proof, Mapping) else None},
            )
        return {
            "result": "GREEN",
            "surface_visible": True,
            "postcondition_green": True,
            "handler": plan.handler,
            "semantic_path": plan.semantic_path,
            "source_event_context": source_context,
            "action_ack": ack,
            "advance": dict(advanced),
            "result_event_context": result_context,
            "provider_postcondition": dict(proof),
        }


class CompositePhase2SpanDriver:
    """Compose non-overlapping handler delegates into one eight-span driver."""

    def __init__(self, *delegates: Phase2SpanDriver) -> None:
        if not delegates:
            raise ValueError("at least one phase-two span driver is required")
        owners: dict[str, Phase2SpanDriver] = {}
        for delegate in delegates:
            for handler in delegate.available_handlers():
                if handler in owners:
                    raise ValueError(f"duplicate phase-two handler owner: {handler}")
                owners[handler] = delegate
        self._owners = owners

    def available_handlers(self) -> tuple[str, ...]:
        return tuple(self._owners)

    def run_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        delegate = self._owners.get(scenario.handler)
        if delegate is None:
            raise Phase2VisualHandlerError(
                "handler_unavailable", {"handler": scenario.handler}
            )
        return delegate.run_span(scenario, context, runtime)


__all__ = [
    "AdvanceToResult",
    "CompositePhase2SpanDriver",
    "ENDGAME_HANDLER",
    "EVENT_PATH_PLANS",
    "EventPathPlan",
    "PROJECTS_HANDLER",
    "PROMOTION_HANDLER",
    "Phase2VisualHandlerAdapter",
    "Phase2VisualHandlerError",
    "PostconditionVerifier",
    "SCOREBOARD_HANDLER",
    "ScoreboardActionCell",
    "VisualGameplayService",
]
