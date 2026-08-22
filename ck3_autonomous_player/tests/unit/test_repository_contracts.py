from __future__ import annotations

import ast
import json
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]


class RepositoryContractTests(unittest.TestCase):
    def test_ocr_and_schema_runtime_dependencies_are_pinned_and_fingerprinted(
        self,
    ) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        dependencies = set(project["project"]["dependencies"])
        expected = {
            "attrs": "attrs==26.1.0",
            "jsonschema": "jsonschema==4.25.1",
            "jsonschema-specifications": "jsonschema-specifications==2025.9.1",
            "onnxruntime": "onnxruntime==1.28.0",
            "opencv-python": "opencv-python==5.0.0.93",
            "pyclipper": "pyclipper==1.4.0",
            "PyYAML": "PyYAML==6.0.3",
            "rapidocr-onnxruntime": "rapidocr-onnxruntime==1.2.3",
            "rfc3339-validator": "rfc3339-validator==0.1.4",
            "referencing": "referencing==0.37.0",
            "rpds-py": "rpds-py==2026.6.3",
            "Shapely": "Shapely==2.1.2",
            "six": "six==1.17.0",
        }
        self.assertLessEqual(set(expected.values()), dependencies)

        source = ast.parse(
            (ROOT / "src" / "xar_autoplayer" / "environment.py").read_text(
                encoding="utf-8"
            )
        )
        runtime_distributions: set[str] | None = None
        for node in source.body:
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "RUNTIME_DISTRIBUTIONS"
                    for target in node.targets
                )
                and isinstance(node.value, ast.Tuple)
            ):
                runtime_distributions = {
                    item.value
                    for item in node.value.elts
                    if isinstance(item, ast.Constant)
                    and isinstance(item.value, str)
                }
                break
        self.assertIsNotNone(runtime_distributions)
        self.assertLessEqual(set(expected), runtime_distributions or set())

    def test_all_json_contracts_parse(self) -> None:
        paths = sorted((ROOT / "schemas").glob("*.json"))
        paths.append(ROOT / "strategies" / "growth_100_v1.json")
        self.assertEqual(len(paths), 9)
        for path in paths:
            with self.subTest(path=path.name):
                payload = json.loads(path.read_text(encoding="utf-8"))
                if path.parent.name == "schemas":
                    expected_version = 2 if "-v2." in path.name else 1
                    self.assertEqual(
                        payload["properties"]["format_version"]["const"],
                        expected_version,
                    )
                else:
                    self.assertEqual(payload["format_version"], 1)

    def test_default_config_is_exact_growth_100_single_mod(self) -> None:
        payload = tomllib.loads(
            (ROOT / "configs" / "default.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["mod"]["enabled_mod_count"], 1)
        self.assertEqual(payload["rules"]["xar_enabled"], "xar_on")
        self.assertEqual(payload["rules"]["xar_inheritance"], "xar_inherit_100")
        self.assertEqual(payload["rules"]["xar_score_basis"], "xar_score_growth")
        self.assertFalse(payload["safety"]["debug_mode"])

    def test_ui_contract_filename_freezes_language_and_runtime_dimensions(self) -> None:
        paths = sorted((ROOT / "configs" / "ui").glob("*.json"))
        self.assertEqual(
            [path.name for path in paths],
            [
                "ck3-1.19.0.6.zh-hans.2560x1440.json",
                "ck3-1.19.0.6.zh-hans.2560x1440.opening.json",
            ],
        )
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["game_version"], "1.19.0.6")
            self.assertEqual(payload["language"], "l_simp_chinese")
            self.assertEqual(payload["resolution"], [2560, 1440])

    def test_visible_v2_schemas_cover_the_current_producer_surface(self) -> None:
        observation = json.loads(
            (ROOT / "schemas" / "observation-v2.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            set(observation["properties"]),
            {
                "format_version",
                "observation_id",
                "frame_id",
                "captured_at",
                "screen",
                "image",
                "ocr",
                "visible_anchors",
                "visible_controls",
                "visible_facts",
                "confidence",
                "unknown_reasons",
                "stability",
                "policy_boundary",
            },
        )
        self.assertEqual(
            set(observation["properties"]["stability"]["required"]),
            {"stable_frames", "expected_screen", "frames", "monotonic_delta"},
        )

        receipt = json.loads(
            (
                ROOT
                / "schemas"
                / "visible-control-action-receipt-v2.schema.json"
            ).read_text(encoding="utf-8")
        )
        source = ast.parse(
            (
                ROOT
                / "src"
                / "xar_autoplayer"
                / "control"
                / "executor.py"
            ).read_text(encoding="utf-8")
        )
        produced: set[str] = set()

        def result_path(node: ast.AST) -> list[str] | None:
            parts: list[str] = []
            while isinstance(node, ast.Subscript):
                if not (
                    isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str)
                ):
                    return None
                parts.append(node.slice.value)
                node = node.value
            if not isinstance(node, ast.Name) or node.id != "result":
                return None
            return list(reversed(parts))

        for node in ast.walk(source):
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "result"
                and isinstance(node.value, ast.Dict)
            ):
                produced.update(
                    key.value
                    for key in node.value.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                )
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    path = result_path(target)
                    if path:
                        produced.add(path[0])
        self.assertEqual(produced, set(receipt["properties"]))
        self.assertLessEqual(set(receipt["required"]), produced)
        self.assertEqual(
            set(receipt["properties"]["target"]["properties"]),
            {
                "issued",
                "fresh",
                "hover",
                "final_patch_sha256",
                "hover_patch_artifact",
                "final_patch_artifact",
            },
        )
        self.assertEqual(
            set(receipt["properties"]["durable_events"]["properties"]),
            {"planned", "armed", "finished"},
        )


if __name__ == "__main__":
    unittest.main()
