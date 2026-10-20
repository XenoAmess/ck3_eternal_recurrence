"""Test the actual OBS Number and wait helpers without OBS."""
from __future__ import annotations

import ast
from collections.abc import Callable
from decimal import Decimal
import math
from pathlib import Path
from typing import cast
import unittest

Dim = Callable[[object], int]
Wait = Callable[[Callable[[], None]], None]


class Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def hooks(clock: Clock) -> tuple[Dim, type[RuntimeError], Wait]:
    path = Path(__file__).with_name("prepare_source28_a13_display_v1.py")
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    values = [n.value for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "HOOK_HELPERS" for t in n.targets)]
    assert len(values) == 1
    literal: object = ast.literal_eval(values[0])
    assert isinstance(literal, str)
    nodes = ast.parse(literal).body
    assert len(nodes) == 3 and all(isinstance(n, (ast.FunctionDef, ast.ClassDef)) for n in nodes)
    ns: dict[str, object] = {"math": math, "Callable": Callable, "time": clock}
    exec(literal, ns)
    dim = ns["_native_obs_dimension_v1"]
    pending = ns["_NativeHookPendingV1"]
    wait = ns["_wait_native_hook_v1"]
    assert callable(dim) and callable(wait)
    assert isinstance(pending, type) and issubclass(pending, RuntimeError)
    # Cast only the selected annotated production functions.
    return cast(Dim, dim), pending, cast(Wait, wait)


class DimensionTests(unittest.TestCase):
    def test_numbers_and_zero_to_native_size(self) -> None:
        clock = Clock()
        dim, pending, wait = hooks(clock)
        for value in (0, 1440, 2560, 0.0, 1440.0, 2560.0):
            self.assertIs(type(dim(value)), int)
            self.assertEqual(dim(value), value)
        states = iter(((0, 0), (0.0, 0.0), (2560.0, 1440.0)))
        observed: list[tuple[int, int]] = []

        def check() -> None:
            width, height = next(states)
            size = (dim(width), dim(height))
            observed.append(size)
            if size == (0, 0):
                raise pending()
            self.assertEqual(size, (2560, 1440))

        wait(check)
        self.assertEqual(observed, [(0, 0), (0, 0), (2560, 1440)])
        self.assertEqual(clock.sleeps, [.25, .25])

    def test_invalid_numbers(self) -> None:
        dim, pending, _ = hooks(Clock())
        for value in (True, False, Decimal("2560"), 2560.5, math.nan,
                      math.inf, -math.inf, "2560", None):
            with self.subTest(value=value), self.assertRaises(RuntimeError) as raised:
                dim(value)
            self.assertNotIsInstance(raised.exception, pending)

    def test_pending_timeout_240_seconds(self) -> None:
        clock = Clock()
        _, pending, wait = hooks(clock)
        calls = 0

        def check() -> None:
            nonlocal calls
            calls += 1
            raise pending()

        with self.assertRaises(TimeoutError) as raised:
            wait(check)
        self.assertIsInstance(raised.exception.__cause__, pending)
        self.assertEqual(clock.now, 240.0)
        self.assertEqual(calls, len(clock.sleeps) + 1)
        self.assertTrue(all(0 < step <= .25 for step in clock.sleeps))

    def test_nonpending_exceptions_have_no_retry(self) -> None:
        for error in (RuntimeError(), ValueError(), TimeoutError()):
            clock = Clock()
            _, _, wait = hooks(clock)
            calls = 0

            def check() -> None:
                nonlocal calls
                calls += 1
                raise error

            with self.assertRaises(type(error)) as raised:
                wait(check)
            self.assertIs(raised.exception, error)
            self.assertEqual(calls, 1)
            self.assertEqual(clock.sleeps, [])


if __name__ == "__main__":
    unittest.main()
