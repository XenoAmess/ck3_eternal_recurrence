from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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
        self.assertIn(
            '"game.command.commit-frontend-dynasty-coat-of-arms-v1"',
            source,
        )
        self.assertIn(
            '"ck3_commit_frontend_dynasty_coat_of_arms_v1"', source
        )
        self.assertIn('== "coat_of_arms_designer"', source)
        self.assertIn('row.get("runtime_name") == "coat_of_arms_page"', source)

    def test_runner_has_opt_in_native_finish_roundtrip(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        self.assertIn('"--commit-roundtrip"', source)
        self.assertIn('"commit_dynasty_coat_of_arms"', source)
        self.assertIn(
            '"native_copy_bytes_preserved_after_commit_reopen"', source
        )

    def test_runner_has_opt_in_chunked_large_source_roundtrip(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        self.assertIn('"--large-source"', source)
        self.assertIn('"ck3_begin_coat_of_arms_source_upload_v2"', source)
        self.assertIn('"ck3_append_coat_of_arms_source_chunk_v2"', source)
        self.assertIn('"ck3_commit_coat_of_arms_source_upload_v2"', source)
        self.assertIn('"semantic_field_sequences_preserved"', source)

    def test_runner_has_opt_in_route_bound_framebuffer_comparison(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        self.assertIn('"--reference-preview"', source)
        self.assertIn(
            '"ck3_compare_frontend_coat_of_arms_framebuffer_v1"', source
        )
        self.assertIn(
            '"ck3_prepare_frontend_coat_of_arms_framebuffer_v1"', source
        )
        self.assertIn('"--native-crop-output"', source)
        self.assertIn('"--picture-corpus"', source)
        self.assertIn('"--picture-crop-dir"', source)

    def test_picture_corpus_loader_requires_all_seven_ordered_cases(self) -> None:
        module = _load_runner_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for number in range(1, 8):
                case = root / f"picture-{number:02d}"
                case.mkdir()
                (case / "coat_of_arms.txt").write_text(
                    "coa = {}\n", encoding="ascii"
                )
                (case / "canonical-preview-230.png").write_bytes(
                    f"png-{number}".encode("ascii")
                )

            cases = module._load_picture_corpus(root)

        self.assertEqual(
            [case["id"] for case in cases],
            [f"picture-{number:02d}" for number in range(1, 8)],
        )
        self.assertTrue(
            all(
                case["source_receipt"]["structure"]["instances"] == 0
                for case in cases
            )
        )

    def test_framebuffer_gate_and_crop_receipt_are_hash_bound(self) -> None:
        module = _load_runner_module()
        crop = b"native-png-fixture"
        crop_sha256 = hashlib.sha256(crop).hexdigest().upper()
        spatial = [[0.1 for _ in range(8)] for _ in range(8)]
        call = {
            "is_error": False,
            "structured_content": {
                "schema": "ck3-coat-of-arms-framebuffer-comparison-v1",
                "routeStable": True,
                "readOnly": True,
                "usesOcr": False,
                "usesKeyboard": False,
                "usesMouse": False,
                "comparison": {
                    "bestMatch": {
                        "locatorLoss": 0.2,
                        "distinctMargin": 0.02,
                        "cropPngBase64": base64.b64encode(crop).decode("ascii"),
                        "cropPngSha256": crop_sha256,
                    },
                    "metrics": {
                        "meanAbsoluteError": 0.1,
                        "colorMse": 0.02,
                        "edgeLoss": 0.1,
                        "spatialMeanAbsoluteError8x8": spatial,
                    },
                },
            },
        }

        gate = module._framebuffer_gate(call)

        self.assertTrue(gate["ok"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "native.png"
            receipt = module._write_native_crop(
                output, {"reference_framebuffer": {**gate, "call": call}}
            )
            self.assertEqual(output.read_bytes(), crop)
            self.assertEqual(receipt["sha256"], crop_sha256)

    def test_large_source_receipt_and_numeric_semantics_are_stable(self) -> None:
        module = _load_runner_module()
        raw = (
            b'coa={\n pattern="pattern_solid.dds"\n'
            b' colored_emblem={ texture="ce_block_02.dds" color1=rgb { 1 2 3 }\n'
            b' instance={ position={ 0.12345678 0.5 } scale={ 1 1 } '
            b'rotation=0 depth=1 } }\n}\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.txt"
            path.write_bytes(raw)
            source, receipt = module._load_large_source(path)

        self.assertTrue(receipt["line_endings_normalized"])
        self.assertEqual(receipt["raw_bytes"], len(raw))
        self.assertEqual(receipt["wire_bytes"], len(source.encode("ascii")))
        self.assertEqual(receipt["structure"]["instances"], 1)
        expected = module._semantic_projection(source)
        canonical = source.replace("0.12345678", "0.123457").replace(
            "depth=1", "depth=1.000000"
        )
        actual = module._semantic_projection(canonical)
        checks = module._semantic_projection_checks(expected, actual)
        self.assertTrue(all(checks.values()))

    def test_native_color_domain_and_default_rotation_are_semantic_equals(self) -> None:
        module = _load_runner_module()
        expected = module._semantic_projection(
            'coa={ color1=rgb { 1 0 0 } colored_emblem={ color1=rgb { 253 0 0 } '
            'instance={ rotation=0 depth=1 } instance={ rotation=17 depth=2 } } }'
        )
        native_copy = module._semantic_projection(
            'coa_rd_dynasty_1={ color1=rgb { 255 0 0 } '
            'colored_emblem={ color1=rgb { 253 0 0 } instance={ depth=1.000000 } '
            'instance={ rotation=17.000000 depth=2.000000 } } }'
        )

        checks = module._semantic_projection_checks(expected, native_copy)

        self.assertTrue(checks["colors"])
        self.assertTrue(checks["rotations"])

    def test_large_source_collector_round_trips_through_v2_tools(self) -> None:
        module = _load_runner_module()
        source = (
            "coa={\r\n"
            + (
                ' colored_emblem={ texture="ce_block_02.dds" '
                "color1=rgb { 1 2 3 } instance={ position={ 0.1 0.2 } "
                "scale={ 0.3 0.4 } rotation=0 depth=1 } }\r\n"
            )
            * 1_500
            + "}\r\n"
        )
        self.assertGreater(len(source.encode("ascii")), 128 * 1024)
        digest = hashlib.sha256(source.encode("ascii")).hexdigest()

        class FakeClient:
            def __init__(self) -> None:
                self.calls: list[tuple[str, dict[str, object]]] = []

            async def call_tool(self, name, arguments):
                arguments = dict(arguments)
                self.calls.append((name, arguments))
                if name == "ck3_get_capabilities":
                    body = {"snapshot": False}
                elif name == module.BEGIN_COAT_OF_ARMS_UPLOAD_TOOL:
                    body = {
                        "status": "receiving",
                        "upload_id": "1" * 32,
                        "generation": 1,
                    }
                elif name == module.APPEND_COAT_OF_ARMS_UPLOAD_TOOL:
                    body = {
                        "status": (
                            "ready"
                            if arguments["chunk_index"]
                            == arguments["chunk_count"] - 1
                            else "receiving"
                        )
                    }
                elif name == module.COMMIT_COAT_OF_ARMS_UPLOAD_TOOL:
                    body = {
                        "status": "committed",
                        "result": {
                            "status": "applied",
                            "detected": True,
                            "applied": True,
                            "source_bytes": len(source.encode("ascii")),
                            "source_sha256": digest,
                        },
                    }
                elif name == module.EXPORT_COAT_OF_ARMS_TOOL:
                    exported = source.replace("coa={", "coa_rd_dynasty_1={", 1)
                    body = {
                        "status": "exported",
                        "source": exported,
                        "source_bytes": len(exported.encode("ascii")),
                        "source_sha256": hashlib.sha256(
                            exported.encode("ascii")
                        ).hexdigest(),
                    }
                else:
                    raise AssertionError(name)
                return SimpleNamespace(
                    content=[],
                    is_error=False,
                    structured_content=body,
                )

        receipt = {
            "wire_bytes": len(source.encode("ascii")),
            "wire_sha256": digest,
            "structure": module._source_structure(source),
            "semantic_projection": module._projection_summary(
                module._semantic_projection(source)
            ),
        }
        client = FakeClient()
        recorded = []
        result = asyncio.run(
            module._collect_large_source_roundtrip(
                client,
                source,
                receipt,
                recorded.append,
            )
        )

        self.assertTrue(result["ok"])
        self.assertGreater(result["chunk_count"], 1)
        self.assertTrue(all(result["semantic_checks"].values()))
        self.assertEqual(
            len(
                [
                    name
                    for name, _ in client.calls
                    if name == module.COMMIT_COAT_OF_ARMS_UPLOAD_TOOL
                ]
            ),
            1,
        )

    def test_runner_has_opt_in_native_custom_mode_census(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        self.assertIn('"--custom-mode-census"', source)
        self.assertIn(
            '"game.command.inspect-frontend-coat-of-arms-tree-v1"', source
        )
        self.assertIn(
            '"ck3_inspect_frontend_coat_of_arms_tree_v1"', source
        )
        self.assertIn(
            '"game.command.inspect-frontend-coat-of-arms-pattern-grid-v1"',
            source,
        )
        self.assertIn(
            '"ck3_inspect_frontend_coat_of_arms_pattern_grid_v1"', source
        )
        self.assertIn(
            '"game.command.activate-frontend-coat-of-arms-custom-mode-v1"',
            source,
        )
        self.assertIn(
            '"ck3_activate_frontend_coat_of_arms_custom_mode_v1"', source
        )
        self.assertIn('"pattern_grid_census_recorded"', source)

    def test_custom_mode_collector_records_materialized_pattern_subtree(
        self,
    ) -> None:
        module = _load_runner_module()

        def inspection(*, custom_target: bool, patterns: bool):
            widgets = []
            if custom_target:
                widgets.append(
                    {
                        "runtime_name": "button_custom_mode",
                        "child_path": "0/3/0/2/1/0/0/1/1/0",
                        "depth": 10,
                        "child_count": 0,
                        "vtable_rva": 1,
                        "effective_visible": True,
                        "enabled": True,
                    }
                )
            if patterns:
                widgets.extend(
                    [
                        {
                            "runtime_name": "coa_designer_tabs",
                            "child_path": "0/3/0/2/0",
                            "effective_visible": True,
                            "enabled": True,
                        },
                        {
                            "runtime_name": "background_panel",
                            "child_path": "0/3/0/2/1/1",
                            "effective_visible": True,
                            "enabled": True,
                        },
                        {
                            "runtime_name": "patterns",
                            "child_path": "0/3/0/2/1/1/2",
                            "effective_visible": True,
                            "enabled": True,
                        },
                        {
                            "runtime_name": "patterns_scrollbox",
                            "child_path": "0/3/0/2/1/1/2/0/0",
                            "effective_visible": True,
                            "enabled": True,
                        },
                        {
                            "runtime_name": "pattern_item",
                            "child_path": "0/3/0/2/1/1/2/0/0/0",
                            "child_count": 3,
                            "effective_visible": True,
                            "enabled": True,
                        },
                    ]
                )
            return {
                "schema": "ck3-frontend-gui-tree-inspection-v1",
                "schema_version": 1,
                "step": "inspect-frontend-coat-of-arms-tree-v1",
                "status": "available",
                "scope_root_name": "coat_of_arms_page",
                "root_available": True,
                "truncated": False,
                "widget_count": len(widgets),
                "widgets": widgets,
            }

        before = inspection(custom_target=True, patterns=False)
        after = inspection(custom_target=False, patterns=True)

        class FakeClient:
            def __init__(self) -> None:
                self.responses = [
                    before,
                    {
                        "status": "verified",
                        "action": "enter_coat_of_arms_custom_mode",
                        "postcondition_verified": True,
                        "uses_ocr": False,
                        "uses_keyboard": False,
                        "uses_mouse": False,
                        "after": {"route": "coat_of_arms_designer"},
                        "after_inspection": after,
                    },
                    after,
                    {
                        "schema": "ck3-frontend-gui-tree-inspection-v1",
                        "schema_version": 1,
                        "step": "inspect-frontend-coat-of-arms-pattern-grid-v1",
                        "status": "available",
                        "scope_root_name": "coat_of_arms_pattern_grid",
                        "root_available": True,
                        "truncated": False,
                        "widget_count": 39,
                        "direct_child_count": 38,
                        "direct_children_complete": True,
                        "widgets": [],
                        "read_only": True,
                        "uses_ocr": False,
                        "uses_keyboard": False,
                        "uses_mouse": False,
                    },
                ]

            async def call_tool(self, name, arguments):
                return SimpleNamespace(
                    content=[],
                    is_error=False,
                    structured_content=self.responses.pop(0),
                )

        recorded = []
        result = asyncio.run(
            module._collect_custom_mode_census(FakeClient(), recorded.append)
        )

        self.assertTrue(result["ok"])
        self.assertEqual(len(recorded), 4)
        self.assertFalse(result["pattern_grid"]["is_error"])
        self.assertEqual(
            result["pattern_grid"]["structured_content"]["direct_child_count"],
            38,
        )

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
