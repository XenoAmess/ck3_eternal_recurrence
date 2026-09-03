#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_capture_choreography import (  # noqa: E402
    PHASE2_CAPTURE_SCENARIOS,
    run_phase2_capture_choreography,
)
from zhongguo_phase2_event_choreography import (  # noqa: E402
    PHASE2_EVENT_SEQUENCE_PLANS,
    Phase2EventChoreographer,
    Phase2EventChoreographyError,
    SequencedPhase2SpanDriver,
    phase2_event_sequence_plan,
)
from zhongguo_phase2_promo_producer import (  # noqa: E402
    Phase2PromoCaptureContext,
    canonical_phase2_capture_contract,
)


def _receipt(span_id: str, **values: object) -> dict[str, object]:
    return {
        "result": "GREEN",
        "span_id": span_id,
        "provider_observed": True,
        "ui_state_verified": True,
        "console_used": False,
        "test_fixture_used": False,
        **values,
    }


class _Recorder:
    def __init__(self, calls: list[tuple[object, ...]]) -> None:
        self.calls = calls

    def clean_hold(self, label: str, artifacts: Path, seconds: float = 2.5) -> None:
        self.calls.append(("hold", label, seconds))


class _Service:
    def __init__(self, calls: list[tuple[object, ...]]) -> None:
        self.calls = calls
        self.bad_drain = False
        self.console_stage = False

    def stage_span_source(self, plan, scenario, context, runtime):
        self.calls.append(("stage", plan.span_id, plan.source_event))
        if plan.source_kind == "event_free_map":
            return _receipt(
                plan.span_id,
                no_active_event=True,
                console_used=self.console_stage,
            )
        return _receipt(
            plan.span_id,
            event_definition_key=plan.source_event,
            surface_visible=True,
            console_used=self.console_stage,
        )

    def wait_for_product_event(self, event_definition_key, plan, context, runtime):
        self.calls.append(("wait", plan.span_id, event_definition_key))
        return _receipt(
            plan.span_id,
            event_definition_key=event_definition_key,
            surface_visible=True,
        )

    def close_capture_surface(
        self, surface_kind, surface_id, plan, context, runtime
    ):
        self.calls.append(("close", plan.span_id, surface_kind, surface_id))
        return _receipt(
            plan.span_id,
            surface_kind=surface_kind,
            surface_id=surface_id,
            transition_materialized=True,
        )

    def drain_after_span(self, plan, context, runtime):
        self.calls.append(("drain", plan.span_id))
        return _receipt(
            plan.span_id,
            no_active_event=not self.bad_drain,
            no_blocking_surface=not self.bad_drain,
        )


class _Delegate:
    def __init__(self, calls, choreographer) -> None:
        self.calls = calls
        self.choreographer = choreographer

    def available_handlers(self):
        return tuple(scenario.handler for scenario in PHASE2_CAPTURE_SCENARIOS)

    def run_span(self, scenario, context, runtime):
        self.calls.append(("action", scenario.span_id))
        post_action = None
        plan = phase2_event_sequence_plan(scenario.handler)
        if plan.post_action_events:
            post_action = self.choreographer.present_post_action_events(
                scenario, context, runtime
            )
        return {
            "result": "GREEN",
            "surface_visible": True,
            "postcondition_green": True,
            "post_action_event_sequence": post_action,
        }


def _context(recorder: _Recorder, artifacts: Path) -> Phase2PromoCaptureContext:
    return Phase2PromoCaptureContext(
        stream="",
        artifacts=artifacts,
        recorder=recorder,
        title_navigation_service=object(),
        tracked_ck3_pid=4321,
        native_bridge=object(),
        preflight_bridge_identity={"identity": "unit"},
        contract=canonical_phase2_capture_contract(),
        seed_contract={"status": "ready", "ready": True},
        seed_install={"result": "GREEN"},
        native_session_binding={"bridge_pid": 4321, "connection_generation": 3},
        loader_gate={
            "result": "GREEN",
            "native_readiness": {"result": "GREEN"},
            "phase2_capability_preflight": {"result": "GREEN"},
        },
    )


def _runtime() -> dict[str, object]:
    return {"ready": True, "paused_snapshot": {"paused": True, "map_ready": True}}


class Phase2EventChoreographyTests(unittest.TestCase):
    def test_plans_keep_canonical_order_and_special_event_sequences(self) -> None:
        self.assertEqual(
            tuple((plan.span_id, plan.handler) for plan in PHASE2_EVENT_SEQUENCE_PLANS),
            tuple((scenario.span_id, scenario.handler) for scenario in PHASE2_CAPTURE_SCENARIOS),
        )
        self.assertEqual(
            phase2_event_sequence_plan("capture_manager_governance").post_action_events,
            ("zg361mg.120",),
        )
        self.assertEqual(
            phase2_event_sequence_plan("capture_incidents_operations").post_action_events,
            ("zg361ip.190", "zg361ip.290", "zg361ip.390"),
        )
        self.assertEqual(
            phase2_event_sequence_plan("capture_incidents_operations").source_event,
            "zg361.50",
        )

    def test_executor_stages_then_holds_then_closes_and_drains_every_span(self) -> None:
        calls: list[tuple[object, ...]] = []
        service = _Service(calls)
        event_choreographer = Phase2EventChoreographer(service)
        driver = SequencedPhase2SpanDriver(
            _Delegate(calls, event_choreographer), event_choreographer
        )
        with tempfile.TemporaryDirectory() as temporary:
            evidence = run_phase2_capture_choreography(
                _context(_Recorder(calls), Path(temporary)),
                _runtime(),
                driver,
                clean_hold_seconds=0.25,
            )

        spans = [scenario.span_id for scenario in PHASE2_CAPTURE_SCENARIOS]
        self.assertEqual([row[1] for row in calls if row[0] == "stage"], spans)
        self.assertEqual([row[1] for row in calls if row[0] == "action"], spans)
        self.assertEqual([row[1] for row in calls if row[0] == "hold"], spans)
        self.assertEqual([row[1] for row in calls if row[0] == "drain"], spans)
        for span_id in spans:
            operations = [row[0] for row in calls if len(row) > 1 and row[1] == span_id]
            self.assertLess(operations.index("stage"), operations.index("action"))
            self.assertLess(operations.index("action"), operations.index("hold"))
            self.assertLess(operations.index("hold"), len(operations) - 1 - operations[::-1].index("close"))
            self.assertLess(len(operations) - 1 - operations[::-1].index("close"), operations.index("drain"))
        self.assertEqual(evidence["result"], "GREEN")
        self.assertTrue(
            all("source_staging" in row and "surface_close_and_drain" in row for row in evidence["completed_spans"])
        )

    def test_incident_events_are_visible_in_order_and_only_final_stays_for_hold(self) -> None:
        calls: list[tuple[object, ...]] = []
        service = _Service(calls)
        event_choreographer = Phase2EventChoreographer(service)
        scenario = next(
            row for row in PHASE2_CAPTURE_SCENARIOS if row.handler == "capture_incidents_operations"
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = event_choreographer.present_post_action_events(
                scenario,
                _context(_Recorder(calls), Path(temporary)),
                _runtime(),
            )
        self.assertEqual(
            [row[2] for row in calls if row[0] == "wait"],
            ["zg361ip.190", "zg361ip.290", "zg361ip.390"],
        )
        self.assertEqual(
            [row[3] for row in calls if row[0] == "close"],
            ["zg361ip.190", "zg361ip.290"],
        )
        self.assertEqual(result["capture_event_left_visible"], "zg361ip.390")

    def test_console_staging_and_nonempty_drain_are_typed_red(self) -> None:
        calls: list[tuple[object, ...]] = []
        service = _Service(calls)
        event_choreographer = Phase2EventChoreographer(service)
        scenario = PHASE2_CAPTURE_SCENARIOS[0]
        with tempfile.TemporaryDirectory() as temporary:
            context = _context(_Recorder(calls), Path(temporary))
            service.console_stage = True
            with self.assertRaises(Phase2EventChoreographyError) as raised:
                event_choreographer.prepare_span(scenario, context, _runtime())
            self.assertEqual(
                raised.exception.reason_code, "event_choreography_receipt_invalid"
            )
            service.console_stage = False
            service.bad_drain = True
            with self.assertRaises(Phase2EventChoreographyError) as raised:
                event_choreographer.finalize_span(scenario, context, _runtime())
            self.assertEqual(raised.exception.reason_code, "span_drain_not_empty")


if __name__ == "__main__":
    unittest.main()
