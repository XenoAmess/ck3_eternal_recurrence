#!/usr/bin/env python3
"""Executable, producer-neutral choreography for the eight phase-two spans.

The visual producer owns CK3/recorder lifecycle and registration.  This module
owns the stable scenario catalogue, pre-action readiness, ordered driver calls,
and the clean-span boundary.  It cannot launch CK3 and it cannot manufacture a
capture: the caller must supply the real runtime context, the real recorder,
and handlers that expose the product surfaces listed below.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Mapping, Protocol

from zhongguo_phase2_promo_producer import (
    PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
    PHASE2_PROMO_CAPTURE_MODE,
    PHASE2_PROMO_CAPTURE_SPAN_MAP,
    Phase2PromoCaptureContext,
    canonical_phase2_capture_contract,
)


@dataclass(frozen=True, slots=True)
class Phase2CaptureScenario:
    span_id: str
    producer_key: str
    handler: str
    gameplay_entrypoint: str
    loaded_feature_flags: tuple[str, ...]
    script_dlc_keys: tuple[str, ...]
    event_definition_keys: tuple[str, ...]
    gui_surfaces: tuple[str, ...]
    mcp_queries: tuple[str, ...]
    mcp_actions: tuple[str, ...]
    postcondition: str


PHASE2_CAPTURE_SCENARIOS: Final = (
    Phase2CaptureScenario(
        "phase2_fact_quota_calibration",
        "facts-quota-calibration",
        "capture_fact_quota_calibration",
        "run_phase2_scoreboard_gameplay_action_cell",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361b1.200", "zg361b1.201", "zg361.1"),
        (
            "named_widget:zg361_scoreboard_modal",
            "event_window:zg361b1.200",
            "event_window:zg361b1.201",
            "event_window:zg361.1",
        ),
        ("query-zhongguo-scoreboard-state-v1", "query-current-event-window-context-v1"),
        ("select-event-option-N",),
        "scoreboard/query revision changes and the visible calibration event is identity-ready",
    ),
    Phase2CaptureScenario(
        "phase2_receipt_appeal_pip",
        "receipts-appeals-pip",
        "capture_receipt_appeal_pip",
        "run_phase2_b2_pip_gameplay_action_cell",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361b2.40", "zg361.4"),
        ("event_window:zg361b2.40", "event_window:zg361.4"),
        ("query-zhongguo-b2-pip-snapshot-v1", "query-current-event-window-context-v1"),
        ("select-event-option-N",),
        "the same PIP owner/subject/cycle/case reaches the selected response state",
    ),
    Phase2CaptureScenario(
        "phase2_manager_governance",
        "manager-governance",
        "capture_manager_governance",
        "run_phase2_ai_owned_case_gameplay_action_cell",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361mg.120",),
        ("event_window:zg361mg.120",),
        ("query-zhongguo-ai-owned-case-snapshot-v1", "query-current-event-window-context-v1"),
        ("set-speed-1", "resume-map", "pause-map"),
        "the AI-owned case reaches a provider-observed terminal business state",
    ),
    Phase2CaptureScenario(
        "phase2_promotion_compensation",
        "promotion-compensation",
        "capture_promotion_compensation",
        "event-window option cell (promotion package/compensation runtime)",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361pp.147", "zg361pp.150", "zg361comp.1"),
        (
            "event_window:zg361pp.147",
            "event_window:zg361pp.150",
            "event_window:zg361comp.1",
        ),
        ("query-current-event-window-context-v1", "query-zhongguo-result-case-snapshot-v1"),
        ("select-event-option-N",),
        "promotion choice and compensation receipt remain bound to the same frozen case",
    ),
    Phase2CaptureScenario(
        "phase2_hc_workforce",
        "hc-workforce",
        "capture_hc_workforce",
        "run_phase2_workforce_m360_gameplay_action_cell",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361we.360", "zg361we.361"),
        ("event_window:zg361we.360", "event_window:zg361we.361"),
        ("query-zhongguo-workforce-collective-snapshot-v1", "query-current-event-window-context-v1"),
        ("select-event-option-N", "save-checkpoint", "restore-checkpoint"),
        "A/B/C each proves the same owner/subject case from a hash-identical checkpoint",
    ),
    Phase2CaptureScenario(
        "phase2_projects_metrics",
        "projects-metrics",
        "capture_projects_metrics",
        "event-window option cell (credit/project runtime)",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361cp.26", "zg361cp.31", "zg361p3.229"),
        (
            "event_window:zg361cp.26",
            "event_window:zg361cp.31",
            "event_window:zg361p3.229",
        ),
        ("query-current-event-window-context-v1", "query-loaded-feature-manifest-v1"),
        ("select-event-option-N",),
        "project choice and metrics result are visible on identity-ready product events",
    ),
    Phase2CaptureScenario(
        "phase2_incidents_operations",
        "incidents-operations",
        "capture_incidents_operations",
        "run_phase2_incident_gameplay_action_cell",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361ip.190", "zg361ip.290", "zg361ip.390"),
        (
            "event_window:zg361ip.190",
            "event_window:zg361ip.290",
            "event_window:zg361ip.390",
        ),
        ("query-zhongguo-incident-snapshot-v1", "query-current-event-window-context-v1"),
        ("select-event-option-N", "set-speed-1", "resume-map", "pause-map"),
        "X/Y/Z transitions and closure are provider-observed, never inferred from ACK",
    ),
    Phase2CaptureScenario(
        "phase2_cross_cycle_endgame",
        "cross-cycle-endgame",
        "capture_cross_cycle_endgame",
        "event-window option cell (workforce/endgame runtime)",
        ("all_under_heaven", "merit_admin"),
        ("All Under Heaven",),
        ("zg361we.356", "zg361we.361"),
        ("event_window:zg361we.356", "event_window:zg361we.361"),
        ("query-zhongguo-workforce-collective-snapshot-v1", "query-loaded-feature-manifest-v1"),
        ("set-speed-1", "resume-map", "pause-map", "select-event-option-N"),
        "the terminal event is bound to the carried debt/default-change cycle",
    ),
)


class Phase2SpanDriver(Protocol):
    """Product-specific visual actions supplied by the real producer."""

    def available_handlers(self) -> tuple[str, ...]: ...

    def run_span(
        self,
        scenario: Phase2CaptureScenario,
        context: Phase2PromoCaptureContext,
        runtime: Mapping[str, object],
    ) -> Mapping[str, object]: ...


class Phase2Recorder(Protocol):
    def clean_hold(self, label: str, artifacts: Path, seconds: float = 2.5) -> None: ...


class Phase2ChoreographyBlocked(RuntimeError):
    result: Final = "RED"

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {**dict(evidence), "result": "RED", "reason_code": reason_code}
        super().__init__(f"phase-two choreography RED [{reason_code}]")


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def phase2_choreography_readiness(
    context: Phase2PromoCaptureContext,
    runtime: Mapping[str, object],
    driver: Phase2SpanDriver,
) -> dict[str, object]:
    """Return one typed gate without touching CK3, the recorder, or artifacts."""

    seed = context.seed_contract
    install = context.seed_install
    binding = context.native_session_binding
    loader = context.loader_gate
    available = set(driver.available_handlers())
    required = {scenario.handler for scenario in PHASE2_CAPTURE_SCENARIOS}
    runtime_snapshot = runtime.get("paused_snapshot")
    checks = {
        "runtime_probe_ready": runtime.get("ready") is True,
        "seed_contract_ready": isinstance(seed, Mapping)
        and seed.get("ready") is True
        and seed.get("status") == "ready",
        "seed_install_green": isinstance(install, Mapping)
        and install.get("result") == "GREEN",
        "native_session_bound": isinstance(binding, Mapping)
        and binding.get("bridge_pid") == context.tracked_ck3_pid
        and _positive_integer(binding.get("connection_generation")),
        "loader_gate_green": isinstance(loader, Mapping)
        and loader.get("result") == "GREEN"
        and isinstance(loader.get("native_readiness"), Mapping)
        and loader["native_readiness"].get("result") == "GREEN"
        and isinstance(loader.get("phase2_capability_preflight"), Mapping)
        and loader["phase2_capability_preflight"].get("result") == "GREEN",
        "paused_map_ready": isinstance(runtime_snapshot, Mapping)
        and runtime_snapshot.get("paused") is True
        and runtime_snapshot.get("map_ready") is True,
        "all_span_handlers_available": required.issubset(available),
    }
    missing_handlers = sorted(required - available)
    blocker_order = (
        ("runtime_probe_ready", "runtime_probe_not_ready"),
        ("seed_contract_ready", "seed_not_ready"),
        ("seed_install_green", "seed_not_installed"),
        ("native_session_bound", "native_session_not_bound"),
        ("loader_gate_green", "loader_gate_not_green"),
        ("paused_map_ready", "paused_snapshot_not_ready"),
        ("all_span_handlers_available", "span_handlers_missing"),
    )
    reason = next((code for check, code in blocker_order if checks[check] is not True), None)
    ready = reason is None
    return {
        "schema_version": 1,
        "result": "GREEN" if ready else "RED",
        "ready": ready,
        "reason_code": reason,
        "checks": checks,
        "missing_handlers": missing_handlers,
        "span_readiness": [
            {
                "span_id": scenario.span_id,
                "producer_key": scenario.producer_key,
                "handler": scenario.handler,
                "handler_available": scenario.handler in available,
                "global_runtime_ready": all(
                    checks[name]
                    for name in checks
                    if name != "all_span_handlers_available"
                ),
            }
            for scenario in PHASE2_CAPTURE_SCENARIOS
        ],
    }


def run_phase2_capture_choreography(
    context: Phase2PromoCaptureContext,
    runtime: Mapping[str, object],
    driver: Phase2SpanDriver,
    *,
    clean_hold_seconds: float = 2.5,
) -> dict[str, object]:
    """Execute all eight product spans in contract order, then return evidence.

    A driver must establish and verify the named product surface before this
    function asks the already-running real recorder for its begin/end gate.
    """

    if clean_hold_seconds <= 0:
        raise ValueError("clean_hold_seconds must be positive")
    readiness = phase2_choreography_readiness(context, runtime, driver)
    if readiness["ready"] is not True:
        raise Phase2ChoreographyBlocked(str(readiness["reason_code"]), readiness)

    completed: list[dict[str, object]] = []
    recorder = context.recorder
    for scenario in PHASE2_CAPTURE_SCENARIOS:
        result = driver.run_span(scenario, context, runtime)
        if not isinstance(result, Mapping) or result.get("result") != "GREEN":
            raise Phase2ChoreographyBlocked(
                "span_action_not_green",
                {
                    "span_id": scenario.span_id,
                    "producer_key": scenario.producer_key,
                    "driver_result": dict(result) if isinstance(result, Mapping) else None,
                    "completed_spans": [item["span_id"] for item in completed],
                },
            )
        if result.get("surface_visible") is not True or result.get("postcondition_green") is not True:
            raise Phase2ChoreographyBlocked(
                "span_surface_or_postcondition_not_green",
                {"span_id": scenario.span_id, "driver_result": dict(result)},
            )
        recorder.clean_hold(
            scenario.span_id,
            context.artifacts,
            seconds=clean_hold_seconds,
        )
        completed.append(
            {
                "span_id": scenario.span_id,
                "producer_key": scenario.producer_key,
                "handler": scenario.handler,
                "gameplay_entrypoint": scenario.gameplay_entrypoint,
                "result": "GREEN",
                "surface_visible": True,
                "postcondition_green": True,
                "postcondition_evidence": dict(result),
            }
        )
    return {
        "result": "GREEN",
        "capture_mode": PHASE2_PROMO_CAPTURE_MODE,
        "capture_contract_version": PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
        "capture_contract": canonical_phase2_capture_contract(),
        "readiness": readiness,
        "completed_spans": completed,
        "scenario_definitions": [asdict(item) for item in PHASE2_CAPTURE_SCENARIOS],
    }


def _validate_catalogue() -> None:
    expected = tuple(PHASE2_PROMO_CAPTURE_SPAN_MAP)
    actual = tuple((item.span_id, item.producer_key) for item in PHASE2_CAPTURE_SCENARIOS)
    if actual != expected:
        raise RuntimeError("phase-two choreography catalogue drifted from capture contract")
    handlers = [item.handler for item in PHASE2_CAPTURE_SCENARIOS]
    if len(handlers) != len(set(handlers)):
        raise RuntimeError("phase-two choreography handlers are not unique")
    for scenario in PHASE2_CAPTURE_SCENARIOS:
        if not scenario.loaded_feature_flags or not scenario.script_dlc_keys:
            raise RuntimeError(
                f"phase-two span lacks loaded-feature requirements: {scenario.span_id}"
            )
        event_surfaces = {
            surface.removeprefix("event_window:")
            for surface in scenario.gui_surfaces
            if surface.startswith("event_window:")
        }
        if not set(scenario.event_definition_keys).issubset(event_surfaces):
            raise RuntimeError(
                f"phase-two span lacks an exact event-window surface: {scenario.span_id}"
            )


_validate_catalogue()


__all__ = [
    "PHASE2_CAPTURE_SCENARIOS",
    "Phase2CaptureScenario",
    "Phase2ChoreographyBlocked",
    "Phase2Recorder",
    "Phase2SpanDriver",
    "phase2_choreography_readiness",
    "run_phase2_capture_choreography",
]
