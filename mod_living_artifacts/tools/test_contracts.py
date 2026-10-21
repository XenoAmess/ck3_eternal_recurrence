"""Regression tests for file/JSON contracts and reversible source integration."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from generate import apply_source_patches, merge_localization, split_definitions
from living_artifacts_model import RuntimeInventory, SourcePatch
from ck3_text_projection import blocks, digest


class BoundaryTests(unittest.TestCase):
    def test_release_cli_keeps_product_validator_ahead_of_shared_namesake(self) -> None:
        script = Path(__file__).with_name("build_release.py")
        result = subprocess.run([sys.executable, str(script), "--help"], cwd=script.parents[2], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--manifest", result.stdout)

    def test_native_effect_projection_preserves_definitions_in_bounded_groups(self) -> None:
        source = "@amount = 3\n" + "\n".join(f"native_{i} = {{ add_gold = @amount }}" for i in range(14))
        patch = SourcePatch("common/scripted_effects/native.txt", digest(source), ((source, source + "\nxalw_hook = { add_gold = 0 }\n"),))
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            path = game / patch.relative_path
            path.parent.mkdir(parents=True)
            path.write_text(source, encoding="utf-8")
            output = apply_source_patches(game, (patch,))
            self.assertEqual(blocks(output[patch.relative_path]), [])
            projected = [value for key, value in output.items() if key != patch.relative_path]
            self.assertEqual(len(projected), 2)
            keys = [block.key for value in projected for block in blocks(value)]
            self.assertEqual(set(keys), {*(f"native_{i}" for i in range(14)), "xalw_hook"})
            self.assertTrue(all("@amount = 3" in value for value in projected))

    def test_runtime_inventory_round_trip(self) -> None:
        value = {"schema_version": 1, "paths": ["descriptor.mod", "events/xalw.txt", "thumbnail.png"]}
        parsed = RuntimeInventory.parse(value)
        self.assertEqual(parsed, RuntimeInventory.parse(json.loads(json.dumps(parsed.to_json()))))

    def test_inventory_rejects_wrong_types_fields_and_paths(self) -> None:
        for value in (
            {"schema_version": True, "paths": ["descriptor.mod", "thumbnail.png"]},
            {"schema_version": 1.0, "paths": ["descriptor.mod", "thumbnail.png"]},
            {"schema_version": 1, "paths": None},
            {"schema_version": 1, "paths": ["../descriptor.mod", "thumbnail.png"]},
            {"schema_version": 1, "paths": ["descriptor.mod", "thumbnail.png"], "extra": 0},
            {"schema_version": 1, "paths": ["descriptor.mod", "descriptor.mod", "thumbnail.png"]},
            {"schema_version": 1},
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                RuntimeInventory.parse(value)

    def test_source_patch_checks_actual_original_and_recovery(self) -> None:
        original = 'native_effect = {\n add_gold = 10\n}\n'
        patch = SourcePatch("common/native.txt", digest(original), (("add_gold = 10", "add_gold = 10\n xalw_callback_effect = yes"),))
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            path = game / "common/native.txt"
            path.parent.mkdir()
            path.write_text(original, encoding="utf-8")
            output = apply_source_patches(game, (patch,))
            self.assertIn("add_gold = 10", output[patch.relative_path])
            self.assertIn("xalw_callback_effect", output[patch.relative_path])
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            path.write_text(original.replace("10", "11"), encoding="utf-8")
            with self.assertRaises(ValueError):
                apply_source_patches(game, (patch,))

    def test_source_patch_rejects_ambiguous_anchor(self) -> None:
        source = "a = { gold = 1 }\nb = { gold = 1 }\n"
        patch = SourcePatch("test.txt", digest(source), (("gold = 1", "gold = 2"),))
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            (game / "test.txt").write_text(source, encoding="utf-8")
            with self.assertRaises(ValueError):
                apply_source_patches(game, (patch,))

    def test_split_preserves_each_effect_and_ignores_quoted_braces(self) -> None:
        source = "\n".join(f'effect_{number} = {{ nested = {{ value = {number} }} log = "{{quoted}}" }}' for number in range(23))
        files = split_definitions(source, "xalw_test")
        self.assertEqual(len(files), 3)
        actual: list[str] = []
        for text in files.values():
            definitions = blocks(text)
            top = [block for block in definitions if block.key.startswith("effect_")]
            self.assertLessEqual(len(top), 10)
            actual.extend(block.key for block in top)
        self.assertEqual(actual, [f"effect_{number}" for number in range(23)])

    def test_localization_cannot_silently_override_other_producer(self) -> None:
        with self.assertRaises(ValueError):
            merge_localization({"xalw_a": "甲"}, {"xalw_a": "乙"})


if __name__ == "__main__":
    unittest.main()
