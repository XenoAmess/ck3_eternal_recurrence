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
    Phase2CaptureScenario,
    Phase2ChoreographyBlocked,
    phase2_choreography_readiness,
    run_phase2_capture_choreography,
)
from zhongguo_phase2_promo_producer import (  # noqa: E402
    Phase2PromoCaptureContext,
    canonical_phase2_capture_contract,
)
from zhongguo_phase2_visual_handlers import (  # noqa: E402
    CompositePhase2SpanDriver,
    ENDGAME_HANDLER,
    EVENT_PATH_PLANS,
    PROJECTS_HANDLER,
    PROMOTION_HANDLER,
    Phase2VisualHandlerAdapter,
    Phase2VisualHandlerError,
    SCOREBOARD_HANDLER,
)


VISUAL_HANDLERS = (
    SCOREBOARD_HANDLER,
    PROMOTION_HANDLER,
    PROJECTS_HANDLER,
    ENDGAME_HANDLER,
)


def _scenario(handler: str) -> Phase2CaptureScenario:
    return next(item for item in PHASE2_CAPTURE_SCENARIOS if item.handler == handler)


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def clean_hold(self, label: str, artifacts: Path, seconds: float = 2.5) -> None:
        self.calls.append(label)


class _EventService:
    def __init__(self, handler: str = PROMOTION_HANDLER) -> None:
        self.plan = EVENT_PATH_PLANS[handler]
        self.result = False
        self.calls: list[tuple[object, ...]] = []

    def snapshot(self) -> dict[str, object]:
        self.calls.append(("snapshot", self.result))
        return {
            "snapshot_id": "visual:result" if self.result else "visual:source",
            "revision": 12 if self.result else 10,
            "native_revision": 102 if self.result else 100,
            "date_raw": 53147016,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 29037},
            "diagnostics": {"bridge_pid": 4321, "connection_generation": 4},
            "active_event": {
                "instance_id": 902 if self.result else 901,
                "option_count": 3,
            },
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("query-event", event_instance_id, expected_revision))
        return {
            "status": "available",
            "current_event_window_context": {
                "status": "available",
                "event_definition_key": (
                    self.plan.result_event if self.result else self.plan.source_event
                ),
                "current_event_instance_id": 902 if self.result else 901,
                "snapshot_revision": 102 if self.result else 100,
                "date_raw": 53147016,
                "root_scope": {"typed_identity": {"status": "available"}},
                "saved_scopes": [],
                "options": [
                    {
                        "rendered_index": index,
                        "native_option_index": index,
                        "shown": True,
                        "enabled": True,
                    }
                    for index in range(3)
                ],
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                    "option_presentation_ready": True,
                },
            },
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.calls.append(
            ("select", option_number, event_instance_id, expected_revision)
        )
        return {"accepted": True, "status": "submitted"}


def _context(recorder: _Recorder, root: Path, *, seed_ready: bool = True) -> Phase2PromoCaptureContext:
    return Phase2PromoCaptureContext(
        stream="",
        artifacts=root,
        recorder=recorder,
        title_navigation_service=object(),
        tracked_ck3_pid=4321,
        native_bridge=object(),
        preflight_bridge_identity={"identity": "unit"},
        contract=canonical_phase2_capture_contract(),
        seed_contract={
            "status": "ready" if seed_ready else "blocked_seed_generation_required",
            "ready": seed_ready,
        },
        seed_install={"result": "GREEN"},
        native_session_binding={"bridge_pid": 4321, "connection_generation": 4},
        loader_gate={
            "result": "GREEN",
            "native_readiness": {"result": "GREEN"},
            "phase2_capability_preflight": {"result": "GREEN"},
        },
    )


def _runtime() -> dict[str, object]:
    return {
        "ready": True,
        "paused_snapshot": {"paused": True, "map_ready": True},
    }


def _green_scoreboard(_service, _artifacts):
    return {
        "result": "GREEN",
        "verified_pass": True,
        "production_capability_advertised": True,
        "action_request": {"action": "open"},
        "later_query": {
            "widgets": [
                {
                    "stable_identity": "zg361_scoreboard_modal",
                    "effective_visible": {"status": "available", "value": True},
                }
            ]
        },
    }


def _adapter(service: _EventService, *, provider_green: bool = True):
    def advance(_service, plan, _context, _runtime_value):
        service.calls.append(("advance", plan.handler))
        service.result = True
        return {"result": "GREEN", "provider_observed": True}

    def verify(_service, plan, before, after, _context, _runtime_value):
        service.calls.append(("verify", plan.handler))
        return {
            "result": "GREEN" if provider_green else "RED",
            "provider_observed": provider_green,
            "postcondition_green": provider_green,
            "source_snapshot_id": before["snapshot_id"],
            "result_snapshot_id": after["snapshot_id"],
        }

    return Phase2VisualHandlerAdapter(
        service,
        scoreboard_action_cell=_green_scoreboard,
        advance_to_result={handler: advance for handler in EVENT_PATH_PLANS},
        postcondition_verifiers={handler: verify for handler in EVENT_PATH_PLANS},
    )


class _OtherFourDriver:
    handlers = tuple(
        item.handler
        for item in PHASE2_CAPTURE_SCENARIOS
        if item.handler not in VISUAL_HANDLERS
    )

    def available_handlers(self) -> tuple[str, ...]:
        return self.handlers

    def run_span(self, scenario, context, runtime):
        return {
            "result": "GREEN",
            "surface_visible": True,
            "postcondition_green": True,
        }


class Phase2VisualHandlerTests(unittest.TestCase):
    def test_event_path_keys_exist_in_product_event_sources(self) -> None:
        event_sources = {
            PROMOTION_HANDLER: (
                "mod_zhongguo_style/events/zg361_feedback_promotion_pip_runtime_events.txt",
                "mod_zhongguo_style/events/zg361_generated_compensation_runtime_events.txt",
            ),
            PROJECTS_HANDLER: (
                "mod_zhongguo_style/events/zg361_credit_project_runtime_events.txt",
                "mod_zhongguo_style/events/zg361_phase3_metrics_delivery_runtime_events.txt",
            ),
            ENDGAME_HANDLER: (
                "mod_zhongguo_style/events/zg361_workforce_endgame_runtime_events.txt",
                "mod_zhongguo_style/events/zg361_workforce_endgame_runtime_events.txt",
            ),
        }
        repository = TOOLS.parent
        for handler, (source_path, result_path) in event_sources.items():
            with self.subTest(handler=handler):
                plan = EVENT_PATH_PLANS[handler]
                source = (repository / source_path).read_text(encoding="utf-8-sig")
                result = (repository / result_path).read_text(encoding="utf-8-sig")
                self.assertIn(f"\n{plan.source_event} = {{", "\n" + source)
                self.assertIn(f"\n{plan.result_event} = {{", "\n" + result)

    def test_adapter_statically_owns_the_four_previous_gaps(self) -> None:
        service = _EventService()
        adapter = _adapter(service)
        self.assertEqual(set(adapter.available_handlers()), set(VISUAL_HANDLERS))
        self.assertEqual(
            {item.source_event for item in EVENT_PATH_PLANS.values()},
            {"zg361pp.147", "zg361cp.26", "zg361we.356"},
        )
        self.assertEqual(
            {item.result_event for item in EVENT_PATH_PLANS.values()},
            {"zg361comp.1", "zg361p3.229", "zg361we.361"},
        )

    def test_scoreboard_requires_open_visible_and_verified_later_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _EventService()
            result = _adapter(service).run_span(
                _scenario(SCOREBOARD_HANDLER),
                _context(_Recorder(), Path(temporary)),
                _runtime(),
            )
        self.assertEqual(result["result"], "GREEN")
        self.assertTrue(result["surface_visible"])
        self.assertTrue(result["postcondition_green"])

        def ack_only(_service, _artifacts):
            return {
                "result": "RED",
                "verified_pass": False,
                "production_capability_advertised": False,
                "action_result": {"accepted": True},
            }

        adapter = Phase2VisualHandlerAdapter(
            service, scoreboard_action_cell=ack_only
        )
        with self.assertRaises(Phase2VisualHandlerError) as raised:
            adapter.run_span(
                _scenario(SCOREBOARD_HANDLER),
                _context(_Recorder(), Path("unit")),
                _runtime(),
            )
        self.assertEqual(raised.exception.reason_code, "scoreboard_surface_not_green")

    def test_each_event_adapter_selects_real_event_and_requires_provider_proof(self) -> None:
        for handler in (PROMOTION_HANDLER, PROJECTS_HANDLER, ENDGAME_HANDLER):
            with self.subTest(handler=handler), tempfile.TemporaryDirectory() as temporary:
                service = _EventService(handler)
                result = _adapter(service).run_span(
                    _scenario(handler),
                    _context(_Recorder(), Path(temporary)),
                    _runtime(),
                )
                self.assertEqual(result["result"], "GREEN")
                self.assertEqual(result["handler"], handler)
                self.assertTrue(result["provider_postcondition"]["provider_observed"])
                self.assertIn(("select", 1, 901, 10), service.calls)
                self.assertIn(("advance", handler), service.calls)
                self.assertIn(("verify", handler), service.calls)

    def test_ack_and_result_event_without_provider_proof_remain_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            service = _EventService(PROJECTS_HANDLER)
            adapter = _adapter(service, provider_green=False)
            with self.assertRaises(Phase2VisualHandlerError) as raised:
                adapter.run_span(
                    _scenario(PROJECTS_HANDLER),
                    _context(_Recorder(), Path(temporary)),
                    _runtime(),
                )
        self.assertEqual(
            raised.exception.reason_code, "provider_postcondition_not_green"
        )

    def test_composite_reports_all_eight_static_handlers(self) -> None:
        composite = CompositePhase2SpanDriver(
            _OtherFourDriver(), _adapter(_EventService())
        )
        self.assertEqual(
            set(composite.available_handlers()),
            {item.handler for item in PHASE2_CAPTURE_SCENARIOS},
        )

    def test_seed_not_ready_blocks_before_any_visual_handler_or_clean_gate(self) -> None:
        service = _EventService()
        visual = _adapter(service)
        composite = CompositePhase2SpanDriver(_OtherFourDriver(), visual)
        recorder = _Recorder()
        with tempfile.TemporaryDirectory() as temporary:
            context = _context(recorder, Path(temporary), seed_ready=False)
            readiness = phase2_choreography_readiness(
                context, _runtime(), composite
            )
            self.assertEqual(readiness["reason_code"], "seed_not_ready")
            with self.assertRaises(Phase2ChoreographyBlocked) as raised:
                run_phase2_capture_choreography(
                    context, _runtime(), composite, clean_hold_seconds=0.01
                )
        self.assertEqual(raised.exception.reason_code, "seed_not_ready")
        self.assertEqual(service.calls, [])
        self.assertEqual(recorder.calls, [])

    def test_duplicate_composite_owner_is_rejected(self) -> None:
        visual = _adapter(_EventService())
        with self.assertRaisesRegex(ValueError, "duplicate phase-two handler owner"):
            CompositePhase2SpanDriver(visual, visual)


if __name__ == "__main__":
    unittest.main()
