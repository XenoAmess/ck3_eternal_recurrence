from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_frontend_gui_route_v1_live_acceptance.py"
)
MATRIX = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "coat_of_arms_syntax_matrix_v1.json"
)


def _load_runner_module():
    spec = importlib.util.spec_from_file_location(
        "frontend_gui_route_v1_live_acceptance_for_test", RUNNER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frontend route runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FrontendGuiRouteLiveAcceptanceContractTests(unittest.TestCase):
    def test_shared_ck3_slot_wraps_launch_and_cleanup(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        launch_lock = source.index(
            "slot_stack.enter_context(exclusive_launch_lock(spec.game_exe))"
        )
        state_lock = source.index("exclusive_state_lock(", launch_lock)
        launch = source.index("handle = launch(", state_lock)
        cleanup = source.index("cleanup = stop_tracked(", launch)
        release = source.index("slot_stack.close()", cleanup)

        self.assertLess(launch_lock, state_lock)
        self.assertLess(state_lock, launch)
        self.assertLess(launch, cleanup)
        self.assertLess(cleanup, release)

    def test_runner_requires_and_checks_the_coat_of_arms_route(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        self.assertIn(
            '"game.command.activate-frontend-coat-of-arms-designer-v1"',
            source,
        )
        self.assertIn(
            '"ck3_activate_frontend_coat_of_arms_designer_v1"', source
        )
        self.assertIn('== "coat_of_arms_designer"', source)
        self.assertIn('row.get("runtime_name") == "coat_of_arms_page"', source)

    def test_checked_in_syntax_matrix_is_closed_and_targeted(self) -> None:
        payload = json.loads(MATRIX.read_text(encoding="utf-8"))

        self.assertEqual(
            set(payload), {"schema", "schema_version", "cases"}
        )
        self.assertEqual(
            payload["schema"], "ck3-coat-of-arms-syntax-matrix-v1"
        )
        self.assertEqual(payload["schema_version"], 1)
        cases = payload["cases"]
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        self.assertEqual(
            {case["apply_expectation"] for case in cases},
            {"required", "observe", "never"},
        )
        identifiers = {case["id"] for case in cases}
        self.assertTrue(
            {
                "core_roundtrip",
                "duplicate_scalar_precedence",
                "multiple_outer_precedence",
                "parent_with_override",
                "comment_hsv_canonicalization",
                "textured_emblem_apply",
                "effect_rejected",
            }
            <= identifiers
        )
        for case in cases:
            self.assertEqual(
                set(case),
                {
                    "id",
                    "purpose",
                    "expected_detection",
                    "apply_expectation",
                    "source",
                },
            )
            case["source"].encode("ascii")

    def test_syntax_collector_applies_only_detected_cases_and_checks_negative_state(
        self,
    ) -> None:
        module = _load_runner_module()
        loaded_matrix = module._load_syntax_matrix(MATRIX)
        self.assertEqual(
            loaded_matrix["schema"], "ck3-coat-of-arms-syntax-matrix-v1"
        )
        self.assertEqual(len(loaded_matrix["cases"]), 15)
        self.assertTrue(
            module._schema_is_zero_input(
                {"type": "object", "properties": {}}
            )
        )
        self.assertTrue(
            module._schema_has_required_fields(
                {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"expected_revision": {"type": "integer"}},
                    "required": ["expected_revision"],
                },
                {"expected_revision"},
            )
        )

        class FakeClient:
            def __init__(self) -> None:
                self.responses = [
                    {"snapshot": False},
                    {"status": "exported", "source_sha256": "a" * 64},
                    {"status": "detected"},
                    {"status": "applied"},
                    {"status": "exported", "source_sha256": "b" * 64},
                    {"status": "not_detected"},
                    {"status": "exported", "source_sha256": "b" * 64},
                ]
                self.calls: list[tuple[str, dict[str, object]]] = []

            async def call_tool(self, name, arguments):
                self.calls.append((name, dict(arguments)))
                return SimpleNamespace(
                    content=[],
                    is_error=False,
                    structured_content=self.responses.pop(0),
                )

        matrix = {
            "schema": "ck3-coat-of-arms-syntax-matrix-v1",
            "schema_version": 1,
            "path": "fixture",
            "sha256": "c" * 64,
            "cases": [
                {
                    "id": "valid",
                    "purpose": "fixture",
                    "expected_detection": "detected",
                    "apply_expectation": "required",
                    "source": "coa = {}",
                },
                {
                    "id": "invalid",
                    "purpose": "fixture",
                    "expected_detection": "not_detected",
                    "apply_expectation": "never",
                    "source": "invalid",
                },
            ],
        }
        client = FakeClient()
        recorded = []
        result = asyncio.run(
            module._collect_syntax_matrix(client, matrix, recorded.append)
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["binding_mode"], "frontend")
        self.assertEqual(result["expected_revision"], 0)
        self.assertEqual(len(recorded), 7)
        apply_calls = [
            arguments
            for name, arguments in client.calls
            if name == module.PROBE_COAT_OF_ARMS_TOOL
            and arguments.get("apply") is True
        ]
        self.assertEqual(len(apply_calls), 1)
        self.assertTrue(
            result["cases"][1]["checks"]["negative_state_unchanged"]
        )


if __name__ == "__main__":
    unittest.main()
