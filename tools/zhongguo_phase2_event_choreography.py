#!/usr/bin/env python3
"""Strict live event staging and teardown for Phase2 promo spans.

This module owns only cross-span UI choreography.  It never launches CK3 and
cannot synthesize a product event.  Its injected service must stage events
through a canonical save/timeline route, then prove every visible identity and
every close/drain transition from the real provider.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final, Mapping, Protocol

from zhongguo_phase2_capture_choreography import (
    PHASE2_CAPTURE_SCENARIOS,
    Phase2CaptureScenario,
    Phase2SpanDriver,
)
from zhongguo_phase2_promo_producer import Phase2PromoCaptureContext


@dataclass(frozen=True, slots=True)
class Phase2EventSequencePlan:
    span_id: str
    handler: str
    source_kind: str
    source_event: str | None
    capture_surface_kind: str
    capture_surface: str
    post_action_events: tuple[str, ...] = ()


PHASE2_EVENT_SEQUENCE_PLANS: Final = (
    Phase2EventSequencePlan(
        "phase2_fact_quota_calibration",
        "capture_fact_quota_calibration",
        "event_free_map",
        None,
        "named_widget",
        "zg361_scoreboard_modal",
    ),
    Phase2EventSequencePlan(
        "phase2_receipt_appeal_pip",
        "capture_receipt_appeal_pip",
        "product_event",
        "zg361b2.40",
        "product_event",
        "zg361.4",
    ),
    Phase2EventSequencePlan(
        "phase2_manager_governance",
        "capture_manager_governance",
        "event_free_map",
        None,
        "product_event",
        "zg361mg.120",
        ("zg361mg.120",),
    ),
    Phase2EventSequencePlan(
        "phase2_promotion_compensation",
        "capture_promotion_compensation",
        "product_event",
        "zg361pp.147",
        "product_event",
        "zg361comp.1",
    ),
    Phase2EventSequencePlan(
        "phase2_hc_workforce",
        "capture_hc_workforce",
        "product_event",
        "zg361we.360",
        "product_event",
        "zg361we.361",
    ),
    Phase2EventSequencePlan(
        "phase2_projects_metrics",
        "capture_projects_metrics",
        "product_event",
        "zg361cp.26",
        "product_event",
        "zg361p3.229",
    ),
    Phase2EventSequencePlan(
        "phase2_incidents_operations",
        "capture_incidents_operations",
        "product_event",
        "zg361.50",
        "product_event",
        "zg361ip.390",
        ("zg361ip.190", "zg361ip.290", "zg361ip.390"),
    ),
    Phase2EventSequencePlan(
        "phase2_cross_cycle_endgame",
        "capture_cross_cycle_endgame",
        "product_event",
        "zg361we.356",
        "product_event",
        "zg361we.361",
    ),
)

_PLAN_BY_HANDLER: Final = {
    plan.handler: plan for plan in PHASE2_EVENT_SEQUENCE_PLANS
}


class Phase2EventChoreographyService(Protocol):
    """Real-provider callbacks supplied by the acceptance runner."""

    def stage_span_source(
        self,
        plan: Phase2EventSequencePlan,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]: ...

    def wait_for_product_event(
        self,
        event_definition_key: str,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]: ...

    def close_capture_surface(
        self,
        surface_kind: str,
        surface_id: str,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]: ...

    def drain_after_span(
        self,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]: ...


class Phase2EventChoreographyError(RuntimeError):
    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {**dict(evidence), "result": "RED", "reason_code": reason_code}
        super().__init__(f"phase-two event choreography RED [{reason_code}]")


def phase2_event_sequence_plan(handler: str) -> Phase2EventSequencePlan:
    try:
        return _PLAN_BY_HANDLER[handler]
    except KeyError as error:
        raise Phase2EventChoreographyError(
            "event_sequence_plan_missing", {"handler": handler}
        ) from error


def _common_receipt(
    value: object,
    *,
    plan: Phase2EventSequencePlan,
    operation: str,
) -> dict[str, object]:
    receipt = dict(value) if isinstance(value, Mapping) else {}
    if not (
        receipt.get("result") == "GREEN"
        and receipt.get("span_id") == plan.span_id
        and receipt.get("provider_observed") is True
        and receipt.get("ui_state_verified") is True
        and receipt.get("console_used") is False
        and receipt.get("test_fixture_used") is False
    ):
        raise Phase2EventChoreographyError(
            "event_choreography_receipt_invalid",
            {
                "span_id": plan.span_id,
                "operation": operation,
                "receipt": receipt,
            },
        )
    return receipt


class Phase2EventChoreographer:
    """Stage, present, close and drain one canonical span at a time."""

    def __init__(self, service: Phase2EventChoreographyService) -> None:
        self.service = service

    def preflight(
        self,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> dict[str, object]:
        hook = getattr(self.service, "preflight_source_checkpoints", None)
        if hook is None:
            return {"result": "GREEN", "source_checkpoint_preflight": "not_required"}
        if not callable(hook):
            raise Phase2EventChoreographyError(
                "source_checkpoint_preflight_invalid", {}
            )
        value = hook(context, runtime)
        receipt = dict(value) if isinstance(value, Mapping) else {}
        if receipt.get("result") != "GREEN":
            raise Phase2EventChoreographyError(
                "source_checkpoint_preflight_red", {"receipt": receipt}
            )
        return receipt

    def prepare_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> dict[str, object]:
        plan = phase2_event_sequence_plan(scenario.handler)
        receipt = _common_receipt(
            self.service.stage_span_source(plan, scenario, context, runtime),
            plan=plan,
            operation="stage_span_source",
        )
        source_ready = (
            receipt.get("no_active_event") is True
            if plan.source_kind == "event_free_map"
            else receipt.get("event_definition_key") == plan.source_event
            and receipt.get("surface_visible") is True
        )
        if not source_ready:
            raise Phase2EventChoreographyError(
                "span_source_not_ready",
                {"plan": asdict(plan), "receipt": receipt},
            )
        return {
            "result": "GREEN",
            "span_id": plan.span_id,
            "provider_observed": True,
            "ui_state_verified": True,
            "plan": asdict(plan),
            "source": receipt,
        }

    def present_post_action_events(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> dict[str, object]:
        """Leave the last required event visible for the outer clean hold."""

        plan = phase2_event_sequence_plan(scenario.handler)
        presentations: list[dict[str, object]] = []
        intermediate_closes: list[dict[str, object]] = []
        for index, event_key in enumerate(plan.post_action_events):
            shown = _common_receipt(
                self.service.wait_for_product_event(
                    event_key, plan, context, runtime
                ),
                plan=plan,
                operation="wait_for_product_event",
            )
            if not (
                shown.get("event_definition_key") == event_key
                and shown.get("surface_visible") is True
            ):
                raise Phase2EventChoreographyError(
                    "post_action_event_not_visible",
                    {
                        "plan": asdict(plan),
                        "expected_event": event_key,
                        "receipt": shown,
                    },
                )
            presentations.append(shown)
            if index + 1 < len(plan.post_action_events):
                closed = self._close_surface(
                    plan,
                    context,
                    runtime,
                    surface_kind="product_event",
                    surface_id=event_key,
                    operation="close_intermediate_post_action_event",
                )
                intermediate_closes.append(closed)
        return {
            "result": "GREEN",
            "span_id": plan.span_id,
            "provider_observed": True,
            "ui_state_verified": True,
            "presented_events": presentations,
            "intermediate_closes": intermediate_closes,
            "capture_event_left_visible": (
                plan.post_action_events[-1] if plan.post_action_events else None
            ),
        }

    def _close_surface(
        self,
        plan: Phase2EventSequencePlan,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
        *,
        surface_kind: str,
        surface_id: str,
        operation: str,
    ) -> dict[str, object]:
        receipt = _common_receipt(
            self.service.close_capture_surface(
                surface_kind, surface_id, plan, context, runtime
            ),
            plan=plan,
            operation=operation,
        )
        if not (
            receipt.get("surface_kind") == surface_kind
            and receipt.get("surface_id") == surface_id
            and receipt.get("transition_materialized") is True
        ):
            raise Phase2EventChoreographyError(
                "capture_surface_close_not_materialized",
                {
                    "plan": asdict(plan),
                    "expected_surface_kind": surface_kind,
                    "expected_surface_id": surface_id,
                    "receipt": receipt,
                },
            )
        return receipt

    def finalize_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> dict[str, object]:
        plan = phase2_event_sequence_plan(scenario.handler)
        closed = self._close_surface(
            plan,
            context,
            runtime,
            surface_kind=plan.capture_surface_kind,
            surface_id=plan.capture_surface,
            operation="close_capture_surface",
        )
        drained = _common_receipt(
            self.service.drain_after_span(plan, context, runtime),
            plan=plan,
            operation="drain_after_span",
        )
        if not (
            drained.get("no_active_event") is True
            and drained.get("no_blocking_surface") is True
        ):
            raise Phase2EventChoreographyError(
                "span_drain_not_empty",
                {"plan": asdict(plan), "receipt": drained},
            )
        return {
            "result": "GREEN",
            "span_id": plan.span_id,
            "provider_observed": True,
            "ui_state_verified": True,
            "closed": closed,
            "drained": drained,
        }


class SequencedPhase2SpanDriver:
    """Add source staging and post-hold teardown to an existing driver."""

    def __init__(
        self,
        delegate: Phase2SpanDriver,
        event_choreographer: Phase2EventChoreographer,
    ) -> None:
        self.delegate = delegate
        self.event_choreographer = event_choreographer

    def available_handlers(self) -> tuple[str, ...]:
        return self.delegate.available_handlers()

    def preflight(
        self,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        return self.event_choreographer.preflight(context, runtime)

    def prepare_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        return self.event_choreographer.prepare_span(scenario, context, runtime)

    def run_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        return self.delegate.run_span(scenario, context, runtime)

    def finalize_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]:
        return self.event_choreographer.finalize_span(scenario, context, runtime)


def _validate_plans() -> None:
    expected = tuple((scenario.span_id, scenario.handler) for scenario in PHASE2_CAPTURE_SCENARIOS)
    actual = tuple((plan.span_id, plan.handler) for plan in PHASE2_EVENT_SEQUENCE_PLANS)
    if actual != expected:
        raise RuntimeError("phase-two event sequence plans drifted from canonical span order")
    for plan in PHASE2_EVENT_SEQUENCE_PLANS:
        if plan.source_kind not in {"event_free_map", "product_event"}:
            raise RuntimeError(f"unsupported source kind for {plan.span_id}")
        if plan.source_kind == "product_event" and not plan.source_event:
            raise RuntimeError(f"product-event source missing for {plan.span_id}")
        if plan.post_action_events and plan.post_action_events[-1] != plan.capture_surface:
            raise RuntimeError(f"post-action sequence does not end on capture surface: {plan.span_id}")


_validate_plans()


__all__ = [
    "PHASE2_EVENT_SEQUENCE_PLANS",
    "Phase2EventChoreographer",
    "Phase2EventChoreographyError",
    "Phase2EventChoreographyService",
    "Phase2EventSequencePlan",
    "SequencedPhase2SpanDriver",
    "phase2_event_sequence_plan",
]
