"""Pure contract tests for the phase-two promo producer scaffold.

These tests intentionally do not import the CK3 acceptance runner, launch a
process, invoke FFmpeg, touch a desktop, or create capture artifacts.  They
exercise only the adapter's parameter and contract boundary.
"""

from __future__ import annotations

import copy
import ast
from pathlib import Path
import sys
import tempfile
import unittest

# Support both ``python tools/test_…py`` (the repository convention) and
# ``python -m unittest discover -s tools`` without making ``tools`` a package.
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_promo_producer import (
    PHASE2_PROMO_CAPTURE_SPAN_MAP,
    Phase2PromoProducerContractError,
    Phase2PromoProducerError,
    Phase2PromoProducerUnavailable,
    canonical_phase2_capture_contract,
    install_phase2_promo_capture_scaffold,
    make_managed_phase2_promo_capture_producer,
    make_phase2_promo_capture_scaffold,
)


class _Contract:
    def __init__(self, value: dict[str, object]) -> None:
        self.value = copy.deepcopy(value)

    def to_mapping(self) -> dict[str, object]:
        return copy.deepcopy(self.value)


class _Recorder:
    def __init__(self, contract: dict[str, object]) -> None:
        self.contract = _Contract(contract)
        self.calls: list[str] = []
        self.clean_labels: list[str] = []

    def resolve_reviewed_subject(self, history_id: str) -> None:
        self.calls.append(f"resolve:{history_id}")

    def start(self) -> None:
        self.calls.append("start")

    def clean_hold(self, label: str, *_args: object, **_kwargs: object) -> None:
        self.calls.append("clean_hold")
        self.clean_labels.append(label)

    def stop(self) -> None:
        self.calls.append("stop")


def _invoke(producer: object, recorder: _Recorder) -> dict[str, object]:
    assert callable(producer)
    with tempfile.TemporaryDirectory() as temporary:
        return producer(  # type: ignore[operator]
            object(),
            Path(temporary) / "artifacts",
            recorder,
            title_navigation_service=object(),
            tracked_ck3_pid=4321,
            native_bridge=object(),
            preflight_bridge_identity={},
        )


def _invoke_managed(producer: object, recorder: _Recorder) -> dict[str, object]:
    assert callable(producer)
    with tempfile.TemporaryDirectory() as temporary:
        return producer(  # type: ignore[operator]
            object(),
            Path(temporary) / "artifacts",
            recorder,
            title_navigation_service=object(),
            tracked_ck3_pid=4321,
            native_bridge=object(),
            preflight_bridge_identity={},
            seed_contract={"status": "ready", "ready": True},
            seed_install={
                "result": "GREEN",
                "contract": {"status": "ready", "ready": True},
            },
            native_session_binding={
                "bridge_pid": 4321,
                "connection_generation": 7,
            },
            loader_gate={
                "result": "GREEN",
                "mode": "phase2_promo_capture",
                "same_pid_gameplay_continuation_authorized": True,
                "native_readiness": {"result": "GREEN"},
                "phase2_capability_preflight": {"result": "GREEN"},
            },
        )


class Phase2PromoProducerScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = canonical_phase2_capture_contract()

    def test_module_has_no_process_desktop_or_artifact_side_effects(self) -> None:
        source = (TOOLS / "zhongguo_phase2_promo_producer.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        imported = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse(
            imported.intersection({"subprocess", "pyautogui", "cv2", "numpy"})
        )
        forbidden_calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        self.assertFalse(
            forbidden_calls.intersection(
                {
                    "start",
                    "stop",
                    "clean_hold",
                    "launch",
                    "Popen",
                    "mkdir",
                    "write_text",
                    "write_bytes",
                }
            )
        )

    def test_factory_returns_fresh_canonical_contract(self) -> None:
        first = make_phase2_promo_capture_scaffold()
        second = make_phase2_promo_capture_scaffold()
        self.assertEqual(first.contract, self.contract)
        self.assertEqual(second.contract, self.contract)
        self.assertIsNot(first.contract, second.contract)
        first.contract["span_ids"].append("must-not-leak")  # type: ignore[union-attr]
        self.assertEqual(second.contract, self.contract)

    def test_contract_snapshot_cannot_be_mutated_after_construction(self) -> None:
        producer = make_phase2_promo_capture_scaffold()
        exposed = producer.contract
        exposed["mode"] = "phase1"
        exposed["span_map"].clear()  # type: ignore[union-attr]
        self.assertEqual(producer.contract, self.contract)

    def test_contract_mismatch_is_typed_red_at_construction(self) -> None:
        malformed = copy.deepcopy(self.contract)
        malformed["span_ids"] = list(malformed["span_ids"])[::-1]  # type: ignore[index]
        with self.assertRaises(Phase2PromoProducerContractError) as raised:
            make_phase2_promo_capture_scaffold(contract=malformed)
        self.assertEqual(raised.exception.result, "RED")
        self.assertEqual(raised.exception.reason_code, "contract_mismatch")
        self.assertEqual(
            raised.exception.evidence["actual_contract"], malformed
        )

    def test_constructor_contract_requires_exact_scalar_types(self) -> None:
        for invalid_version in (True, 1.0):
            malformed = copy.deepcopy(self.contract)
            malformed["version"] = invalid_version
            with self.assertRaises(Phase2PromoProducerContractError) as raised:
                make_phase2_promo_capture_scaffold(contract=malformed)
            self.assertEqual(raised.exception.reason_code, "contract_mismatch")

    def test_missing_runtime_probe_is_typed_red_without_recorder_calls(self) -> None:
        recorder = _Recorder(self.contract)
        producer = make_phase2_promo_capture_scaffold()
        with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
            _invoke(producer, recorder)
        self.assertEqual(raised.exception.reason_code, "runtime_probe_unconfigured")
        self.assertEqual(raised.exception.result, "RED")
        self.assertEqual(raised.exception.evidence["tracked_ck3_pid"], 4321)
        self.assertEqual(recorder.calls, [])

    def test_unavailable_runtime_short_circuits_choreography(self) -> None:
        recorder = _Recorder(self.contract)
        probe_contexts: list[object] = []
        choreography_calls: list[object] = []

        def probe(context: object) -> dict[str, object]:
            probe_contexts.append(context)
            return {"ready": False, "reason": "seed_not_bound"}

        def choreography(context: object, runtime: object) -> dict[str, object]:
            choreography_calls.append((context, runtime))
            return {}

        producer = make_phase2_promo_capture_scaffold(
            runtime_probe=probe,
            choreography=choreography,
        )
        with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
            _invoke(producer, recorder)
        self.assertEqual(raised.exception.reason_code, "runtime_unavailable")
        self.assertEqual(raised.exception.evidence["runtime"]["reason"], "seed_not_bound")  # type: ignore[index]
        self.assertEqual(len(probe_contexts), 1)
        self.assertEqual(choreography_calls, [])
        self.assertEqual(recorder.calls, [])

    def test_probe_exception_becomes_typed_red(self) -> None:
        recorder = _Recorder(self.contract)

        def probe(_context: object) -> dict[str, object]:
            raise OSError("bridge is not running")

        producer = make_phase2_promo_capture_scaffold(runtime_probe=probe)
        with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
            _invoke(producer, recorder)
        self.assertEqual(raised.exception.reason_code, "runtime_probe_failed")
        self.assertEqual(raised.exception.evidence["exception_type"], "OSError")
        self.assertEqual(recorder.calls, [])

    def test_ready_runtime_forwards_context_and_evidence_without_lifecycle(self) -> None:
        recorder = _Recorder(self.contract)
        seen: dict[str, object] = {}
        expected_result = {
            "capture_mode": "zhongguo-361-phase2",
            "capture_contract_version": 1,
            "capture_contract": copy.deepcopy(self.contract),
            "producer_evidence": "delegate-owned",
        }

        def probe(context: object) -> dict[str, object]:
            seen["probe_context"] = context
            return {"ready": True, "source": "injected-live-probe"}

        def choreography(context: object, runtime: dict[str, object]) -> dict[str, object]:
            seen["choreography_context"] = context
            seen["runtime"] = runtime
            return copy.deepcopy(expected_result)

        producer = make_phase2_promo_capture_scaffold(
            runtime_probe=probe,
            choreography=choreography,
        )
        result = _invoke(producer, recorder)
        self.assertEqual(result, expected_result)
        self.assertIs(seen["probe_context"], seen["choreography_context"])
        context = seen["probe_context"]
        self.assertEqual(context.tracked_ck3_pid, 4321)  # type: ignore[union-attr]
        self.assertEqual(context.contract, self.contract)  # type: ignore[union-attr]
        self.assertEqual(seen["runtime"], {"ready": True, "source": "injected-live-probe"})
        self.assertEqual(recorder.calls, [])

    def test_missing_choreography_is_typed_red_after_ready_probe(self) -> None:
        recorder = _Recorder(self.contract)
        producer = make_phase2_promo_capture_scaffold(
            runtime_probe=lambda _context: {"ready": True}
        )
        with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
            _invoke(producer, recorder)
        self.assertEqual(raised.exception.reason_code, "choreography_unconfigured")
        self.assertEqual(recorder.calls, [])

    def test_delegate_contract_fields_are_required_and_never_defaulted(self) -> None:
        recorder = _Recorder(self.contract)
        producer = make_phase2_promo_capture_scaffold(
            runtime_probe=lambda _context: {"ready": True},
            choreography=lambda _context, _runtime: {
                "producer_evidence": "incomplete"
            },
        )
        with self.assertRaises(Phase2PromoProducerContractError) as raised:
            _invoke(producer, recorder)
        self.assertEqual(
            raised.exception.reason_code, "producer_contract_fields_missing"
        )
        self.assertEqual(
            raised.exception.evidence["missing_fields"],
            ["capture_mode", "capture_contract_version", "capture_contract"],
        )
        self.assertEqual(recorder.calls, [])

    def test_delegate_mode_and_contract_are_strict(self) -> None:
        recorder = _Recorder(self.contract)
        bad = {
            "capture_mode": "phase1",
            "capture_contract_version": 1,
            "capture_contract": copy.deepcopy(self.contract),
        }
        producer = make_phase2_promo_capture_scaffold(
            runtime_probe=lambda _context: {"ready": True},
            choreography=lambda _context, _runtime: bad,
        )
        with self.assertRaises(Phase2PromoProducerContractError) as raised:
            _invoke(producer, recorder)
        self.assertEqual(raised.exception.reason_code, "producer_mode_mismatch")
        self.assertEqual(recorder.calls, [])

    def test_explicit_non_green_result_cannot_pass_handoff(self) -> None:
        recorder = _Recorder(self.contract)
        for value in ("RED", "BOGUS", None, False):
            bad = {
                "result": value,
                "capture_mode": "zhongguo-361-phase2",
                "capture_contract_version": 1,
                "capture_contract": copy.deepcopy(self.contract),
            }
            producer = make_phase2_promo_capture_scaffold(
                runtime_probe=lambda _context: {"ready": True},
                choreography=lambda _context, _runtime, result=bad: result,
            )
            with self.assertRaises(Phase2PromoProducerContractError) as raised:
                _invoke(producer, recorder)
            self.assertEqual(raised.exception.reason_code, "producer_result_not_green")

    def test_absent_result_is_left_to_runner(self) -> None:
        recorder = _Recorder(self.contract)
        expected = {
            "capture_mode": "zhongguo-361-phase2",
            "capture_contract_version": 1,
            "capture_contract": copy.deepcopy(self.contract),
        }
        producer = make_phase2_promo_capture_scaffold(
            runtime_probe=lambda _context: {"ready": True},
            choreography=lambda _context, _runtime: copy.deepcopy(expected),
        )
        self.assertEqual(_invoke(producer, recorder), expected)

    def test_delegate_contract_version_requires_exact_integer_type(self) -> None:
        recorder = _Recorder(self.contract)
        for invalid_version in (True, 1.0):
            bad = {
                "capture_mode": "zhongguo-361-phase2",
                "capture_contract_version": invalid_version,
                "capture_contract": copy.deepcopy(self.contract),
            }
            producer = make_phase2_promo_capture_scaffold(
                runtime_probe=lambda _context: {"ready": True},
                choreography=lambda _context, _runtime, value=bad: value,
            )
            with self.assertRaises(Phase2PromoProducerContractError) as raised:
                _invoke(producer, recorder)
            self.assertEqual(
                raised.exception.reason_code,
                "producer_contract_version_mismatch",
            )

    def test_install_requires_dependencies_and_registers_only_explicitly(self) -> None:
        registrations: list[object] = []
        with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
            install_phase2_promo_capture_scaffold(registrations.append)
        self.assertEqual(raised.exception.reason_code, "dependencies_unconfigured")
        self.assertEqual(registrations, [])

        producer = install_phase2_promo_capture_scaffold(
            registrations.append,
            runtime_probe=lambda _context: {"ready": True},
            choreography=lambda _context, _runtime: {
                "capture_mode": "zhongguo-361-phase2",
                "capture_contract_version": 1,
                "capture_contract": copy.deepcopy(self.contract),
            },
        )
        self.assertEqual(registrations, [producer])

    def test_managed_runtime_gate_red_precedes_paused_probe_and_recording(self) -> None:
        recorder = _Recorder(self.contract)
        paused_calls: list[object] = []

        def paused(context: object) -> dict[str, object]:
            paused_calls.append(context)
            return {}

        producer = make_managed_phase2_promo_capture_producer(
            paused_snapshot_probe=paused,
            seed_proof_probe=lambda _context, _snapshot: {"result": "GREEN"},
            visual_primitives={},
            reviewed_history_id="han_6875",
        )
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
                producer(
                    object(),
                    Path(temporary) / "artifacts",
                    recorder,
                    title_navigation_service=object(),
                    tracked_ck3_pid=4321,
                    native_bridge=object(),
                    preflight_bridge_identity={},
                    seed_contract={"status": "ready", "ready": True},
                    seed_install={
                        "result": "GREEN",
                        "contract": {"status": "ready", "ready": True},
                    },
                    native_session_binding={
                        "bridge_pid": 9999,
                        "connection_generation": 7,
                    },
                    loader_gate={
                        "result": "GREEN",
                        "mode": "phase2_promo_capture",
                        "same_pid_gameplay_continuation_authorized": True,
                    },
                )
        self.assertEqual(
            raised.exception.reason_code, "native_session_not_bound"
        )
        self.assertIn(
            "native_session_pid_matches",
            raised.exception.evidence["failed_checks"],
        )
        self.assertEqual(paused_calls, [])
        self.assertEqual(recorder.calls, [])

    def test_managed_runtime_preserves_seed_not_ready_typed_red(self) -> None:
        recorder = _Recorder(self.contract)
        paused_calls: list[object] = []
        driver_factory_calls: list[object] = []

        def paused(context: object) -> dict[str, object]:
            paused_calls.append(context)
            return {}

        producer = make_managed_phase2_promo_capture_producer(
            paused_snapshot_probe=paused,
            seed_proof_probe=lambda _context, _snapshot: {"result": "GREEN"},
            visual_primitives={},
            reviewed_history_id="han_6875",
            span_driver_factory=lambda context: driver_factory_calls.append(context),
        )
        blocked_seed = {
            "status": "blocked_seed_generation_required",
            "ready": False,
        }
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
                producer(
                    object(),
                    Path(temporary) / "artifacts",
                    recorder,
                    title_navigation_service=object(),
                    tracked_ck3_pid=4321,
                    native_bridge=object(),
                    preflight_bridge_identity={},
                    seed_contract=blocked_seed,
                    seed_install={
                        "result": "RED",
                        "contract": copy.deepcopy(blocked_seed),
                    },
                    native_session_binding={
                        "bridge_pid": 4321,
                        "connection_generation": 7,
                    },
                    loader_gate={
                        "result": "GREEN",
                        "mode": "phase2_promo_capture",
                        "same_pid_gameplay_continuation_authorized": True,
                    },
                )
        self.assertEqual(raised.exception.reason_code, "seed_not_ready")
        self.assertEqual(paused_calls, [])
        self.assertEqual(driver_factory_calls, [])
        self.assertEqual(recorder.calls, [])

    def test_missing_visual_primitives_is_typed_red_before_recorder_start(self) -> None:
        recorder = _Recorder(self.contract)
        producer = make_managed_phase2_promo_capture_producer(
            paused_snapshot_probe=lambda _context: {
                "diagnostics": {"bridge_pid": 4321},
                "paused": True,
                "map_ready": True,
            },
            seed_proof_probe=lambda _context, _snapshot: {"result": "GREEN"},
            visual_primitives={},
            reviewed_history_id="han_6875",
        )
        with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
            _invoke_managed(producer, recorder)
        self.assertEqual(
            raised.exception.reason_code, "span_handlers_missing"
        )
        self.assertEqual(
            len(
                raised.exception.evidence["readiness"]["missing_handlers"]
            ),
            8,
        )
        self.assertEqual(recorder.calls, [])

    def test_managed_producer_records_exact_eight_span_order(self) -> None:
        recorder = _Recorder(self.contract)
        primitive_calls: list[tuple[str, str]] = []

        def primitive(
            _context: object,
            _runtime: object,
            chapter_id: str,
            producer_key: str,
        ) -> dict[str, object]:
            primitive_calls.append((chapter_id, producer_key))
            return {
                "result": "GREEN",
                "surface_visible": True,
                "postcondition_green": True,
            }

        primitives = {
            key: primitive for _, key in PHASE2_PROMO_CAPTURE_SPAN_MAP
        }
        producer = make_managed_phase2_promo_capture_producer(
            paused_snapshot_probe=lambda _context: {
                "diagnostics": {"bridge_pid": 4321},
                "paused": True,
                "map_ready": True,
            },
            seed_proof_probe=lambda _context, _snapshot: {"result": "GREEN"},
            visual_primitives=primitives,
            reviewed_history_id="han_6875",
        )
        result = _invoke_managed(producer, recorder)
        self.assertEqual(primitive_calls, list(PHASE2_PROMO_CAPTURE_SPAN_MAP))
        self.assertEqual(
            recorder.clean_labels,
            [chapter_id for chapter_id, _ in PHASE2_PROMO_CAPTURE_SPAN_MAP],
        )
        self.assertEqual(
            recorder.calls,
            ["resolve:han_6875", "start"] + ["clean_hold"] * 8,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["capture_contract"], self.contract)
        self.assertEqual(len(result["completed_spans"]), 8)

    def test_managed_producer_accepts_context_bound_span_driver_factory(self) -> None:
        recorder = _Recorder(self.contract)
        calls: list[str] = []

        class Driver:
            def available_handlers(self) -> tuple[str, ...]:
                return tuple(
                    {
                        "facts-quota-calibration": "capture_fact_quota_calibration",
                        "receipts-appeals-pip": "capture_receipt_appeal_pip",
                        "manager-governance": "capture_manager_governance",
                        "promotion-compensation": "capture_promotion_compensation",
                        "hc-workforce": "capture_hc_workforce",
                        "projects-metrics": "capture_projects_metrics",
                        "incidents-operations": "capture_incidents_operations",
                        "cross-cycle-endgame": "capture_cross_cycle_endgame",
                    }.values()
                )

            def run_span(self, scenario, _context, _runtime):
                calls.append(scenario.handler)
                return {
                    "result": "GREEN",
                    "surface_visible": True,
                    "postcondition_green": True,
                }

        seen_contexts: list[object] = []

        def factory(context: object) -> Driver:
            seen_contexts.append(context)
            return Driver()

        producer = make_managed_phase2_promo_capture_producer(
            paused_snapshot_probe=lambda _context: {
                "diagnostics": {"bridge_pid": 4321},
                "paused": True,
                "map_ready": True,
            },
            seed_proof_probe=lambda _context, _snapshot: {"result": "GREEN"},
            reviewed_history_id="han_6875",
            span_driver_factory=factory,
        )
        result = _invoke_managed(producer, recorder)
        self.assertEqual(len(seen_contexts), 1)
        self.assertEqual(len(calls), 8)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(recorder.calls[:2], ["resolve:han_6875", "start"])

    def test_runner_error_factory_keeps_typed_fields(self) -> None:
        class RunnerLikeError(RuntimeError):
            pass

        recorder = _Recorder(self.contract)
        producer = make_phase2_promo_capture_scaffold(
            error_factory=RunnerLikeError,
        )
        with self.assertRaises(RunnerLikeError) as raised:
            _invoke(producer, recorder)
        self.assertEqual(raised.exception.reason_code, "runtime_probe_unconfigured")
        self.assertEqual(raised.exception.result, "RED")
        self.assertEqual(raised.exception.evidence["result"], "RED")
        self.assertNotIsInstance(raised.exception, Phase2PromoProducerError)
        self.assertEqual(recorder.calls, [])

    def test_error_factory_cannot_replace_typed_red_with_base_exception(self) -> None:
        recorder = _Recorder(self.contract)
        producer = make_phase2_promo_capture_scaffold(
            error_factory=lambda _message: SystemExit(3),  # type: ignore[return-value]
        )
        with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
            _invoke(producer, recorder)
        self.assertEqual(raised.exception.reason_code, "runtime_probe_unconfigured")


if __name__ == "__main__":
    unittest.main()
