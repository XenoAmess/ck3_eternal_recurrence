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
    Phase2PromoProducerContractError,
    Phase2PromoProducerError,
    Phase2PromoProducerUnavailable,
    canonical_phase2_capture_contract,
    install_phase2_promo_capture_scaffold,
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

    def start(self) -> None:
        self.calls.append("start")

    def clean_hold(self, *_args: object, **_kwargs: object) -> None:
        self.calls.append("clean_hold")

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


if __name__ == "__main__":
    unittest.main()
