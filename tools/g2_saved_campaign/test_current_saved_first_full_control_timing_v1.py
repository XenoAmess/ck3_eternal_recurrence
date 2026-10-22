"""Software-only first-FULL admission -> existing timing binder regression."""
from __future__ import annotations

import asyncio
from contextlib import redirect_stderr
from io import StringIO
import importlib.util
import json
from enum import IntEnum
from pathlib import Path
import sys
from types import ModuleType
from typing import Callable, Protocol, runtime_checkable
import unittest

from tools.g2_saved_campaign.current_saved_basis_v1 import JsonObject, integer, json_object, record
from tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1 import (
    build_current_saved_first_full_control_timing_v1,
)

MACHINE = "software-timing-fixture"
SOURCE = Path(__file__).resolve().parent


def _actual_module_v1(name: str) -> ModuleType:
    """Load the real optional adapter dependency, never an SDK or game module."""
    path = SOURCE / (name + ".py")
    prior = sys.modules.get(name)
    if prior is not None:
        if Path(str(prior.__file__)).resolve() != path:
            raise ValueError("foreign cached timing module")
        return prior
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("actual timing module loader")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    return module


@runtime_checkable
class _ControlCallV1(Protocol):
    def __call__(self, phase: str, operation: Callable[[], None]) -> None: ...


class _OriginalQueueV1:
    def __init__(self) -> None:
        self.full_loop_state: dict[str, int] = {"completed_cycles": 0}
        self._normal_cold: dict[str, object] = {"admission": {"control_timing": None}}
        self.control_call: _ControlCallV1 | None = None
        self.original_calls = 0
        self.guard_calls = 0
        self.relay_calls = 0
        self.original_error: RuntimeError | None = None

    def guard(self) -> None:
        self.guard_calls += 1

    def relay(self) -> None:
        self.relay_calls += 1

    async def full_loop(
        self, session: object, request: JsonObject, path: Path,
    ) -> JsonObject:
        self.original_calls += 1
        maximum = integer(record(request["arguments"])["max_turns"], 1, 30)
        hook = self.control_call
        if hook is None:
            raise ValueError("actual hook required")
        hook("consume_guard", self.guard)
        hook("relay_total", self.relay)
        if self.original_error is not None:
            raise self.original_error
        self.full_loop_state["completed_cycles"] += maximum
        return {"status": "bounded_loop_finished", "actual_turns": maximum}


@runtime_checkable
class _TimingBinderV1(Protocol):
    def __call__(
        self, base: type[_OriginalQueueV1], env: dict[str, object], *,
        admission_getter: Callable[[_OriginalQueueV1], JsonObject | None],
    ) -> type[_OriginalQueueV1]: ...


def _admission_v1(queue: _OriginalQueueV1) -> JsonObject | None:
    value = record(queue._normal_cold["admission"])["control_timing"]
    return None if value is None else json_object(value)


class _CaptureV1:
    def __init__(self) -> None:
        self.rows: list[tuple[Path, JsonObject, int]] = []
        self.fail = False

    def atomic(self, path: Path, value: object, *, limit: int) -> None:
        payload = json_object(value)
        if len(json.dumps(payload, separators=(",", ":")).encode()) > limit:
            raise ValueError("bounded timing output")
        self.rows.append((path, payload, limit))
        if self.fail:
            raise OSError("injected optional timing writer failure")


def _queue_v1(
    control: JsonObject | None,
) -> tuple[_OriginalQueueV1, _CaptureV1]:
    _actual_module_v1("queue_control_timing_v1")
    adapter = _actual_module_v1("queue_control_timing_adapter_v1")
    # The historical adapter is dynamic. Narrow its two real public callables
    # once at this boundary; the regression below executes their original code.
    binder: object = getattr(adapter, "bind_queue_control_timing_v1")
    hook: object = getattr(adapter, "control_call_v1")
    if not isinstance(binder, _TimingBinderV1) or not isinstance(hook, _ControlCallV1):
        raise ValueError("actual timing interfaces")
    capture = _CaptureV1()
    cls = binder(_OriginalQueueV1, {"Q": Path("/no-files-created"), "atomic": capture.atomic},
                 admission_getter=_admission_v1)
    queue = cls()
    queue.control_call = hook
    queue._normal_cold = {"admission": {"control_timing": control}}
    return queue, capture


def _run_v1(queue: _OriginalQueueV1, sequence: int, maximum: int = 30) -> JsonObject:
    return asyncio.run(queue.full_loop(None,
        {"sequence": sequence, "arguments": {"max_turns": maximum}},
        Path("/no-request-created")))


class _IntegerEnumV1(IntEnum):
    VALUE = 41


class FirstFullControlTimingTests(unittest.TestCase):
    def control(self) -> JsonObject:
        return build_current_saved_first_full_control_timing_v1(
            machine_id=MACHINE, next_sequence=41).to_wire()

    def test_exact_existing_five_field_contract_and_json_roundtrip(self) -> None:
        control = self.control()
        self.assertEqual(control, {
            "schema": "xar.ck3.queue-control-timing-admission/v1",
            "enabled": True, "machine_id": MACHINE, "control_sequence": 43,
            "cycle_budget": 30})
        queue, capture = _queue_v1(json_object(json.loads(json.dumps(control))))
        self.assertEqual(_run_v1(queue, 43)["actual_turns"], 30)
        self.assertEqual((queue.original_calls, queue.guard_calls, queue.relay_calls), (1, 1, 1))
        self.assertEqual(len(capture.rows), 1)
        path, payload, limit = capture.rows[0]
        self.assertEqual(path.name, "CONTROL-TIMING-0043.json")
        self.assertEqual(limit, 65536)
        self.assertEqual(payload["actual_cycle_delta"], 30)
        serialized = json.dumps(payload)
        self.assertIn('"consume_guard"', serialized)
        self.assertIn('"relay_total"', serialized)

    def test_numbers_reject_bool_float_enum_and_unsafe_addition(self) -> None:
        for value in (True, False, 41.0, _IntegerEnumV1.VALUE, 0, -1, (1 << 53) - 2):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_current_saved_first_full_control_timing_v1(
                    machine_id=MACHINE, next_sequence=value)
        last = build_current_saved_first_full_control_timing_v1(
            machine_id=MACHINE, next_sequence=(1 << 53) - 3).to_wire()
        self.assertEqual(last["control_sequence"], (1 << 53) - 1)

    def test_machine_is_explicit_canonical_nonempty_string(self) -> None:
        for value in (None, True, 7, "", " ", " machine", "machine "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_current_saved_first_full_control_timing_v1(
                    machine_id=value, next_sequence=41)

    def test_disabled_null_keeps_the_original_loop_and_guards(self) -> None:
        queue, capture = _queue_v1(None)
        self.assertEqual(_run_v1(queue, 43)["actual_turns"], 30)
        self.assertEqual((queue.original_calls, queue.guard_calls, queue.relay_calls), (1, 1, 1))
        self.assertEqual(capture.rows, [])

    def test_only_the_exact_first_full_is_measured_once(self) -> None:
        queue, capture = _queue_v1(self.control())
        _run_v1(queue, 43)
        _run_v1(queue, 104)
        self.assertEqual(len(capture.rows), 1)
        self.assertEqual((queue.original_calls, queue.guard_calls, queue.relay_calls), (2, 2, 2))

    def test_wrong_sequence_and_overbound_preserve_original_behavior(self) -> None:
        queue, capture = _queue_v1(self.control())
        _run_v1(queue, 42)
        self.assertEqual(capture.rows, [])
        with self.assertRaises(ValueError):
            _run_v1(queue, 43, 31)
        self.assertEqual(capture.rows, [])
        self.assertEqual(queue.original_calls, 2)

    def test_original_failure_is_retained_without_retry_or_credit(self) -> None:
        queue, capture = _queue_v1(self.control())
        original = RuntimeError("original FULL failed; never replay")
        queue.original_error = original
        with self.assertRaises(RuntimeError) as caught:
            _run_v1(queue, 43)
        self.assertIs(caught.exception, original)
        self.assertEqual(queue.original_calls, 1)
        self.assertEqual(queue.full_loop_state["completed_cycles"], 0)
        self.assertEqual(capture.rows[0][1]["actual_cycle_delta"], 0)

    def test_optional_writer_failure_does_not_retry_original_failure(self) -> None:
        queue, capture = _queue_v1(self.control())
        original = RuntimeError("original failure")
        queue.original_error = original
        capture.fail = True
        diagnostic = StringIO()
        with redirect_stderr(diagnostic), self.assertRaises(RuntimeError) as caught:
            _run_v1(queue, 43)
        self.assertIn("CONTROL_TIMING_SNAPSHOT_UNAVAILABLE", diagnostic.getvalue())
        self.assertIs(caught.exception, original)
        self.assertEqual(queue.original_calls, 1)
        self.assertEqual(capture.rows[0][2], 65536)


if __name__ == "__main__":
    unittest.main()
