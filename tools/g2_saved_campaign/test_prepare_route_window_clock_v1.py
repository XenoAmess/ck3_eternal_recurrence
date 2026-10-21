"""Contract and RAM end-to-end qualification for the isolated clock delta.

Set XAR_ROUTE_WINDOW_SOURCE31 to the immutable package export for integration.
No test starts a game, native pipe, SDK process, or writes a candidate export.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
import importlib
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_loader
import json
import os
from pathlib import Path
import sys
from types import ModuleType
from collections.abc import Iterator, Mapping, Sequence
import unittest

from tools.g2_saved_campaign.prepare_route_window_clock_v1 import (
    MCP_PATH, MODEL_PATH, NATIVE_PATH, TEST_PATH, MODEL_SOURCE,
    RouteWindowColdDeltaV1, compose_route_window_clock_v1,
    route_window_clock_quote_v1,
)


class _RamLoader(Loader):
    def __init__(self, payload: bytes, filename: str) -> None:
        self.payload = payload
        self.filename = filename

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        return None

    def exec_module(self, module: ModuleType) -> None:
        exec(compile(self.payload, self.filename, "exec", dont_inherit=True), module.__dict__)


class _RamFinder(MetaPathFinder):
    def __init__(self, sources: Mapping[str, tuple[bytes, str]]) -> None:
        self.sources = sources

    def find_spec(self, fullname: str, path: Sequence[str] | None,
                  target: ModuleType | None = None) -> ModuleSpec | None:
        source = self.sources.get(fullname)
        if source is None:
            return None
        return spec_from_loader(fullname, _RamLoader(*source))


def _scoped_name(name: str) -> bool:
    return name == "xar_autoplayer" or name.startswith("xar_autoplayer.") or name == "xar_route_window_qualification_v1"


@contextmanager
def _modules(root: Path, delta: RouteWindowColdDeltaV1) -> Iterator[None]:
    sources: dict[str, tuple[bytes, str]] = {}
    for item in delta.sources:
        name = (item.relative_path[:-3].replace("/", ".") if item.role == "production"
                else "xar_route_window_qualification_v1")
        sources[name] = (item.payload, item.relative_path)
    finder = _RamFinder(sources)
    previous = {name: module for name, module in sys.modules.items() if _scoped_name(name)}
    previous_path = sys.path[:]
    for name in previous:
        del sys.modules[name]
    sys.meta_path.insert(0, finder)
    sys.path.insert(0, str(root))
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        sys.path[:] = previous_path
        for name in list(sys.modules):
            if _scoped_name(name):
                del sys.modules[name]
        sys.modules.update(previous)


def _invoke(module: ModuleType, name: str, *args: object, **kwargs: object) -> object:
    # A single dynamic module boundary. Every result is narrowed by its caller;
    # no Any/cast crosses from generated source into the assertions below.
    function = getattr(module, name)
    if not callable(function):
        raise AssertionError("generated entry is not callable")
    result: object = function(*args, **kwargs)
    return result


def _json_map(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(k) is not str for k in value):
        raise AssertionError("expected JSON object")
    return {str(k): v for k, v in value.items()}


@contextmanager
def _model() -> Iterator[ModuleType]:
    name = "xar_route_window_model_contract_test_v1"
    if name in sys.modules:
        raise AssertionError("test module collision")
    module = ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(MODEL_SOURCE, MODEL_PATH, "exec"), module.__dict__)
        yield module
    finally:
        del sys.modules[name]


class RouteWindowClockContractTests(unittest.TestCase):
    def test_json_roundtrip_and_frozen_model(self) -> None:
        with _model() as model:
            for speed, permission in ((3, False), (3, True), (4, True), (5, True)):
                raw = {"timeline_speed": speed, "research_high_speed_ab": permission}
                clock = _invoke(model, "parse_route_window_clock_v1", json.loads(json.dumps(raw)))
                self.assertEqual(_invoke(model, "route_window_clock_json_v1", clock), raw)
                with self.assertRaises(FrozenInstanceError):
                    setattr(clock, "timeline_speed", 5)

    def test_bad_json_fields_types_and_permission_are_rejected(self) -> None:
        bad: list[object] = [None, [], (), {}, {"timeline_speed": 3},
            {"research_high_speed_ab": False}, {"timeline_speed": None, "research_high_speed_ab": False},
            {"timeline_speed": 3, "research_high_speed_ab": None},
            {"timeline_speed": 3, "research_high_speed_ab": False, "speed": 3},
            {"speed": 3, "research_high_speed_ab": False}]
        for invalid_speed in (True, False, 3.0, 4.0, "3", "4", 0, 1, 2, 6, 2**53, 2**64):
            bad.append({"timeline_speed": invalid_speed, "research_high_speed_ab": True})
        invalid_permissions: tuple[object, ...] = (0, 1, "true", [], {})
        for invalid_permission in invalid_permissions:
            bad.append({"timeline_speed": 3, "research_high_speed_ab": invalid_permission})
        for speed in (4, 5):
            bad.append({"timeline_speed": speed, "research_high_speed_ab": False})
        with _model() as model:
            for value in bad:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    _invoke(model, "parse_route_window_clock_v1", value)

    def test_internal_constructor_and_validator_reject_wrong_types(self) -> None:
        with _model() as model:
            for args in ((True, True), (4.0, True), (4, 1), (4, False), (5, False)):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    _invoke(model, "RouteWindowClockConfigV1", *args)
            with self.assertRaises(ValueError):
                _invoke(model, "validate_route_window_clock_v1",
                        {"timeline_speed": 4, "research_high_speed_ab": True})

    def test_source31_pin_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            compose_route_window_clock_v1(b"bad", b"bad")


class RouteWindowClockSource31Tests(unittest.TestCase):
    root: Path
    native: bytes
    mcp: bytes
    delta: RouteWindowColdDeltaV1

    @classmethod
    def setUpClass(cls) -> None:
        configured = os.environ.get("XAR_ROUTE_WINDOW_SOURCE31")
        if not configured:
            raise unittest.SkipTest("exact XAR_ROUTE_WINDOW_SOURCE31 input is required")
        cls.root = Path(configured).resolve(strict=True)
        cls.native = (cls.root / NATIVE_PATH).read_bytes()
        cls.mcp = (cls.root / MCP_PATH).read_bytes()
        cls.delta = compose_route_window_clock_v1(cls.native, cls.mcp)

    def test_determinism_quote_and_source_roles(self) -> None:
        self.assertEqual(self.delta, compose_route_window_clock_v1(self.native, self.mcp))
        quote = route_window_clock_quote_v1(self.delta)
        self.assertEqual(quote, json.loads(json.dumps(quote)))
        self.assertEqual(len(quote["production"]), 3)
        self.assertEqual(quote["qualification"]["relative_path"], TEST_PATH)
        self.assertFalse(quote["runtime_mutated"])
        self.assertFalse(quote["game_executed"])
        self.assertFalse(quote["live_high_speed_qualified"])
        self.assertLess(sum(len(item.payload) for item in self.delta.sources), 3 * 1024**2)

    def test_byte_drift_rejected_before_composition(self) -> None:
        for native, mcp in ((self.native[:-1] + bytes([self.native[-1] ^ 1]), self.mcp),
                            (self.native, self.mcp[:-1] + bytes([self.mcp[-1] ^ 1]))):
            with self.assertRaises(ValueError):
                compose_route_window_clock_v1(native, mcp)

    def test_unmodified_functions_and_other_scopes_preserved(self) -> None:
        produced = {item.relative_path: item.payload for item in self.delta.sources}
        for before, after, changed in ((self.native, produced[NATIVE_PATH],
                                       {"__init__", "capabilities", "_execute_battle_sentinel_advance"}),
                                      (self.mcp, produced[MCP_PATH], {"load_driver"})):
            bt, at = ast.parse(before), ast.parse(after)
            def functions(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
                return {node.name: node for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            old, new = functions(bt), functions(at)
            self.assertEqual(set(old), set(new))
            for name in old:
                if name not in changed:
                    self.assertEqual(ast.dump(old[name]), ast.dump(new[name]), name)
        native_text = produced[NATIVE_PATH].decode("utf-8")
        self.assertIn('self.route_contact_effective_timeline_speed\n            if proof_kind == "contact_free"', native_text)
        self.assertIn('speed = parsed_route_speed', native_text)
        self.assertIn('speed = parsed_objective_hold_speed', native_text)
        self.assertIn('speed = 3\n            wire_mode = "decision"', native_text)
        self.assertIn('speed = 5\n            wire_mode = "terminal"', native_text)

    def test_real_service_driver_sentinel_producer_consumer(self) -> None:
        with _modules(self.root, self.delta):
            qualification = importlib.import_module("xar_route_window_qualification_v1")
            result = _json_map(_invoke(qualification, "run_route_window_clock_qualification_v1"))
            self.assertEqual(result, {"cases": 9, "native_transport": "synthetic", "live_qualified": False})

    def test_mcp_forwarding_and_non_native_rejection(self) -> None:
        with _modules(self.root, self.delta):
            model = importlib.import_module("xar_autoplayer.bridge.route_window_clock_v1")
            mcp = importlib.import_module("xar_autoplayer.bridge.mcp_server")
            clock = _invoke(model, "parse_route_window_clock_v1",
                            {"timeline_speed": 4, "research_high_speed_ab": True})
            with self.assertRaises(ValueError):
                _invoke(mcp, "load_driver", "vision-report", route_window_clock_v1=clock)
            with self.assertRaises(ValueError):
                _invoke(mcp, "load_driver", "native-headless", route_window_clock_v1={})
            captured: list[dict[str, object]] = []
            def constructor(*args: object, **kwargs: object) -> object:
                captured.append(dict(kwargs))
                # Stop before any genuine endpoint/driver construction or I/O.
                raise LookupError("synthetic constructor boundary reached")
            previous: object = getattr(mcp, "NativeHeadlessGameplayDriver")
            setattr(mcp, "NativeHeadlessGameplayDriver", constructor)
            try:
                with self.assertRaisesRegex(LookupError, "synthetic constructor"):
                    _invoke(mcp, "load_driver", "native-headless", state_dir="D:/unused-synthetic",
                            route_window_clock_v1=clock)
            finally:
                setattr(mcp, "NativeHeadlessGameplayDriver", previous)
            self.assertEqual(len(captured), 1)
            forwarded = captured[0]
            self.assertEqual(_invoke(model, "route_window_clock_json_v1", forwarded["route_window_clock_v1"]),
                             {"timeline_speed": 4, "research_high_speed_ab": True})
            self.assertEqual(forwarded["route_contact_timeline_speed"], 3)
            self.assertIs(forwarded["allow_route_contact_high_speed_ab"], False)


if __name__ == "__main__":
    unittest.main()
