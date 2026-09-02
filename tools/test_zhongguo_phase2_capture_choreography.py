#!/usr/bin/env python3

from __future__ import annotations

import copy
from pathlib import Path
import re
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_capture_choreography import (  # noqa: E402
    PHASE2_CAPTURE_SCENARIOS,
    Phase2ChoreographyBlocked,
    phase2_choreography_readiness,
    run_phase2_capture_choreography,
)
from zhongguo_phase2_promo_producer import (  # noqa: E402
    PHASE2_PROMO_CAPTURE_SPAN_MAP,
    Phase2PromoCaptureContext,
    canonical_phase2_capture_contract,
)


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Path, float]] = []

    def clean_hold(self, label: str, artifacts: Path, seconds: float = 2.5) -> None:
        self.calls.append((label, artifacts, seconds))


class _Driver:
    def __init__(
        self,
        *,
        handlers: tuple[str, ...] | None = None,
        red_span: str | None = None,
        hidden_span: str | None = None,
    ) -> None:
        self.handlers = (
            tuple(item.handler for item in PHASE2_CAPTURE_SCENARIOS)
            if handlers is None
            else handlers
        )
        self.red_span = red_span
        self.hidden_span = hidden_span
        self.calls: list[str] = []

    def available_handlers(self) -> tuple[str, ...]:
        return self.handlers

    def run_span(self, scenario, context, runtime):
        self.calls.append(scenario.span_id)
        if scenario.span_id == self.red_span:
            return {"result": "RED", "surface_visible": False}
        return {
            "result": "GREEN",
            "surface_visible": scenario.span_id != self.hidden_span,
            "postcondition_green": True,
        }


def _context(recorder: _Recorder, artifacts: Path) -> Phase2PromoCaptureContext:
    return Phase2PromoCaptureContext(
        stream="",
        artifacts=artifacts,
        recorder=recorder,
        title_navigation_service=object(),
        tracked_ck3_pid=4321,
        native_bridge=object(),
        preflight_bridge_identity={"identity": "test"},
        contract=canonical_phase2_capture_contract(),
        seed_contract={"status": "ready", "ready": True},
        seed_install={"result": "GREEN"},
        native_session_binding={"bridge_pid": 4321, "connection_generation": 7},
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


class Phase2CaptureChoreographyTests(unittest.TestCase):
    def test_catalogue_is_exact_contract_order_and_maps_real_surfaces(self) -> None:
        self.assertEqual(
            tuple((item.span_id, item.producer_key) for item in PHASE2_CAPTURE_SCENARIOS),
            PHASE2_PROMO_CAPTURE_SPAN_MAP,
        )
        self.assertEqual(len(PHASE2_CAPTURE_SCENARIOS), 8)
        self.assertEqual(len({item.handler for item in PHASE2_CAPTURE_SCENARIOS}), 8)
        for scenario in PHASE2_CAPTURE_SCENARIOS:
            with self.subTest(span=scenario.span_id):
                self.assertTrue(scenario.event_definition_keys)
                self.assertEqual(
                    scenario.loaded_feature_flags,
                    ("all_under_heaven", "merit_admin"),
                )
                self.assertEqual(scenario.script_dlc_keys, ("All Under Heaven",))
                self.assertTrue(scenario.gui_surfaces)
                self.assertTrue(scenario.mcp_queries)
                self.assertTrue(scenario.mcp_actions)
                self.assertTrue(scenario.postcondition)
                self.assertFalse(scenario.gameplay_entrypoint.startswith("fixture"))

    def test_event_and_named_widget_requirements_exist_in_product_sources(self) -> None:
        repository = TOOLS.parent
        event_source = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in (repository / "mod_zhongguo_style" / "events").glob("*.txt")
        )
        gui_source = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in (repository / "mod_zhongguo_style" / "gui").rglob("*.gui")
        )
        for scenario in PHASE2_CAPTURE_SCENARIOS:
            for event_key in scenario.event_definition_keys:
                with self.subTest(span=scenario.span_id, event=event_key):
                    self.assertRegex(
                        "\n" + event_source,
                        rf"(?m)^\s*{re.escape(event_key)}\s*=\s*\{{",
                    )
                    self.assertIn(
                        f"event_window:{event_key}", scenario.gui_surfaces
                    )
            for surface in scenario.gui_surfaces:
                if surface.startswith("named_widget:"):
                    widget = surface.removeprefix("named_widget:")
                    with self.subTest(span=scenario.span_id, widget=widget):
                        self.assertRegex(
                            gui_source,
                            rf'name\s*=\s*"{re.escape(widget)}"',
                        )

    def test_readiness_reports_seed_gate_before_paused_and_handlers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            recorder = _Recorder()
            context = _context(recorder, Path(temporary))
            context = Phase2PromoCaptureContext(
                **{
                    **{name: getattr(context, name) for name in context.__dataclass_fields__},
                    "seed_contract": {
                        "status": "blocked_seed_generation_required",
                        "ready": False,
                    },
                }
            )
            driver = _Driver(handlers=())
            result = phase2_choreography_readiness(context, {"ready": True}, driver)
        self.assertEqual(result["result"], "RED")
        self.assertEqual(result["reason_code"], "seed_not_ready")
        self.assertFalse(result["checks"]["paused_map_ready"])
        self.assertEqual(len(result["missing_handlers"]), 8)
        self.assertTrue(all(not row["global_runtime_ready"] for row in result["span_readiness"]))
        self.assertEqual(recorder.calls, [])

    def test_readiness_binds_pid_and_requires_every_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            recorder = _Recorder()
            context = _context(recorder, Path(temporary))
            driver = _Driver(handlers=(PHASE2_CAPTURE_SCENARIOS[0].handler,))
            result = phase2_choreography_readiness(context, _runtime(), driver)
            self.assertEqual(result["reason_code"], "span_handlers_missing")
            self.assertEqual(len(result["missing_handlers"]), 7)

            bad_binding = copy.deepcopy(dict(context.native_session_binding or {}))
            bad_binding["bridge_pid"] = 999
            changed = Phase2PromoCaptureContext(
                **{
                    **{name: getattr(context, name) for name in context.__dataclass_fields__},
                    "native_session_binding": bad_binding,
                }
            )
            result = phase2_choreography_readiness(changed, _runtime(), _Driver())
            self.assertEqual(result["reason_code"], "native_session_not_bound")
        self.assertEqual(recorder.calls, [])

    def test_executor_runs_each_handler_then_exact_clean_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            recorder = _Recorder()
            driver = _Driver()
            evidence = run_phase2_capture_choreography(
                _context(recorder, root),
                _runtime(),
                driver,
                clean_hold_seconds=1.25,
            )
        expected = [item.span_id for item in PHASE2_CAPTURE_SCENARIOS]
        self.assertEqual(driver.calls, expected)
        self.assertEqual([item[0] for item in recorder.calls], expected)
        self.assertTrue(all(item[1] == root and item[2] == 1.25 for item in recorder.calls))
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(evidence["capture_mode"], "zhongguo-361-phase2")
        self.assertEqual(evidence["capture_contract_version"], 1)
        self.assertEqual(evidence["capture_contract"], canonical_phase2_capture_contract())
        self.assertEqual([item["span_id"] for item in evidence["completed_spans"]], expected)
        self.assertTrue(
            all(
                item["surface_visible"] is True
                and item["postcondition_green"] is True
                and item["postcondition_evidence"]["postcondition_green"] is True
                for item in evidence["completed_spans"]
            )
        )

    def test_executor_stops_before_clean_hold_when_action_is_red(self) -> None:
        red_span = PHASE2_CAPTURE_SCENARIOS[2].span_id
        with tempfile.TemporaryDirectory() as temporary:
            recorder = _Recorder()
            driver = _Driver(red_span=red_span)
            with self.assertRaises(Phase2ChoreographyBlocked) as raised:
                run_phase2_capture_choreography(
                    _context(recorder, Path(temporary)), _runtime(), driver
                )
        self.assertEqual(raised.exception.reason_code, "span_action_not_green")
        self.assertEqual(driver.calls, [item.span_id for item in PHASE2_CAPTURE_SCENARIOS[:3]])
        self.assertEqual([item[0] for item in recorder.calls], [item.span_id for item in PHASE2_CAPTURE_SCENARIOS[:2]])

    def test_hidden_surface_never_gets_a_clean_gate(self) -> None:
        hidden_span = PHASE2_CAPTURE_SCENARIOS[1].span_id
        with tempfile.TemporaryDirectory() as temporary:
            recorder = _Recorder()
            with self.assertRaises(Phase2ChoreographyBlocked) as raised:
                run_phase2_capture_choreography(
                    _context(recorder, Path(temporary)),
                    _runtime(),
                    _Driver(hidden_span=hidden_span),
                )
        self.assertEqual(
            raised.exception.reason_code,
            "span_surface_or_postcondition_not_green",
        )
        self.assertEqual([item[0] for item in recorder.calls], [PHASE2_CAPTURE_SCENARIOS[0].span_id])


if __name__ == "__main__":
    unittest.main()
