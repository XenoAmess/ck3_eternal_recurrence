#!/usr/bin/env python3
"""Static contract for the open_kaishek acceptance boundary.

This test intentionally inspects source/AST only.  It does not import a CK3
runner, touch a desktop, start a process, or invoke the JVM preflight.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent


def _tree(name: str) -> ast.Module:
    path = ROOT / "tools" / name
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _function(name: str, function_name: str) -> ast.FunctionDef:
    for node in ast.walk(_tree(name)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return node
    raise AssertionError(f"{name} has no {function_name}()")


def _call_name(node: ast.Call) -> str:
    value = node.func
    parts: list[str] = []
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
    return ".".join(reversed(parts))


def _calls(node: ast.AST) -> list[tuple[int, str]]:
    return [(_call.lineno, _call_name(_call)) for _call in ast.walk(node) if isinstance(_call, ast.Call)]


class AcceptanceCoverageTests(unittest.TestCase):
    def assert_offline_call_before_desktop(self, filename: str, expected: str) -> None:
        calls = _calls(_function(filename, "preflight"))
        offline = [line for line, name in calls if name == expected]
        self.assertEqual(len(offline), 1, f"{filename} must call {expected} exactly once")
        desktop = [
            line for line, name in calls
            if name in {"acceptance.pyautogui.size", "pyautogui.size"}
        ]
        self.assertTrue(desktop, f"{filename} has no desktop query to order")
        self.assertLess(offline[0], min(desktop), f"{filename} queries desktop before offline preflight")

    def test_each_desktop_runner_has_an_ordered_offline_gate(self) -> None:
        self.assert_offline_call_before_desktop(
            "run_acceptance.py", "run_open_kaishek_preflight"
        )
        self.assert_offline_call_before_desktop(
            "run_vivhite_acceptance.py",
            "acceptance.run_open_kaishek_preflight",
        )
        self.assert_offline_call_before_desktop(
            "run_ox_here_acceptance.py",
            "acceptance.run_open_kaishek_preflight",
        )
        self.assert_offline_call_before_desktop(
            "run_ox_here_loc_smoke.py",
            "acceptance.run_open_kaishek_preflight",
        )
        self.assert_offline_call_before_desktop(
            "run_zhongguo_acceptance.py", "kaishek_preflight.run_preflight"
        )

    def test_terminal_reuses_base_gate_once(self) -> None:
        calls = _calls(_function("run_terminal_acceptance.py", "main"))
        self.assertEqual(
            sum(name == "acceptance.main" for _, name in calls),
            1,
            "terminal wrapper must delegate to the base runner exactly once",
        )
        self.assertFalse(
            any(name in {"acceptance.launch_ck3_process", "launch_ck3_process"} for _, name in calls),
            "terminal wrapper must not introduce a second launch boundary",
        )
        base_calls = _calls(_function("run_acceptance.py", "preflight"))
        self.assertEqual(
            sum(name == "run_open_kaishek_preflight" for _, name in base_calls),
            1,
            "terminal's delegated base path must contain one offline gate",
        )

    def test_main_paths_invoke_preflight_before_live_cells(self) -> None:
        for filename in (
            "run_acceptance.py",
            "run_vivhite_acceptance.py",
            "run_ox_here_acceptance.py",
            "run_ox_here_loc_smoke.py",
            "run_zhongguo_acceptance.py",
        ):
            calls = _calls(_function(filename, "main"))
            self.assertEqual(
                sum(name == "preflight" for _, name in calls),
                1,
                f"{filename}.main must invoke its own preflight once",
            )

    def test_phase2_seed_capture_covers_direct_native_boundary(self) -> None:
        helper_calls = _calls(
            _function("run_zg361_phase2_seed_capture.py", "_run_open_kaishek_seed_preflight")
        )
        self.assertEqual(
            sum(name == "kaishek_preflight.run_preflight" for _, name in helper_calls),
            1,
            "phase-two seed helper must use the shared offline adapter exactly once",
        )
        for function_name, boundary_names in (
            (
                "run_preflight",
                {"_ck3_is_running", "load_runtime"},
            ),
            (
                "run_capture",
                {"zgrun.start_phase2_native_session_supervisor", "launch_native_ck3"},
            ),
        ):
            calls = _calls(_function("run_zg361_phase2_seed_capture.py", function_name))
            offline = [
                line for line, name in calls
                if name == "_run_open_kaishek_seed_preflight"
            ]
            self.assertEqual(len(offline), 1, f"phase2 {function_name} must run one offline gate")
            boundaries = [line for line, name in calls if name in boundary_names]
            self.assertTrue(boundaries, f"phase2 {function_name} has no launch/process boundary")
            self.assertLess(
                offline[0], min(boundaries),
                f"phase2 {function_name} crosses a CK3 boundary before open_kaishek",
            )

        helper_source = (
            ROOT / "tools" / "run_zg361_phase2_seed_capture.py"
        ).read_text(encoding="utf-8-sig")
        self.assertIn('profile="ck3-1.19.0.6-zg361"', helper_source)
        self.assertIn('fixture="synthetic-361-014"', helper_source)


if __name__ == "__main__":
    unittest.main()
