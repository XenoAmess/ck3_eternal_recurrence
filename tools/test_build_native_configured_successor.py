"""Finite admission, serialization and actual command-failure regressions."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from build_native_configured_successor import (
    Config, Fixture, Pin, Producer, config_json, parse_config, parse_pin, read,
)


def reference(name: str) -> Pin:
    return {"path": str(Path(name).resolve()), "bytes": 0, "sha256": "a" * 64}


def fixture_config(root: Path) -> Config:
    return Config("fixture-machine", "a" * 40, root / "new", reference(str(root / "admission.json")),
        160 * 1024 * 1024, reference(str(root / "baseline.json")), root / "baseline-build",
        reference(str(root / "inputs.json")), reference(str(root / "profile.cmake")),
        (Fixture("wire_fixture", ("{output}/wire",), (), ()),), ("wire_fixture",), "wire_fixture",
        "src/wire.cpp", "wire", ("read.json",))


class UngatedProducer(Producer):
    """Only process execution is exercised; no storage or game admission exists."""
    def gate(self) -> None:
        return None


class ConfiguredSuccessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.config = fixture_config(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_producer_to_consumer_json_roundtrip(self) -> None:
        raw = json.dumps(config_json(self.config))
        decoded: object = json.loads(raw)
        self.assertEqual(parse_config(decoded), self.config)
        self.assertIsInstance(config_json(self.config)["fixtures"], list)

    def test_bool_float_and_negative_identity_sizes_rejected(self) -> None:
        for size in (True, 0.0, -1):
            with self.subTest(size=size), self.assertRaises(ValueError):
                parse_pin({"path": str(self.root / "input"), "bytes": size, "sha256": "a" * 64})

    def test_wrong_missing_and_unknown_fields_rejected(self) -> None:
        for field in ("budget_bytes", "source_commit", "fixtures", "storage_admission"):
            value = config_json(self.config)
            del value[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_config(value)
        value = config_json(self.config)
        value["undeclared"] = 1
        with self.assertRaises(ValueError):
            parse_config(value)

    def test_budget_rejects_bool_float_and_archive_sized_lane(self) -> None:
        for size in (True, 160.0, 176705326):
            value = config_json(self.config)
            value["budget_bytes"] = size
            with self.subTest(size=size), self.assertRaises(ValueError):
                parse_config(value)

    def test_missing_null_and_empty_fixture_are_distinct_invalid_inputs(self) -> None:
        cases: tuple[object, ...] = (None, [], {})
        for value in cases:
            raw = config_json(self.config)
            raw["fixtures"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_config(raw)

    def test_duplicate_or_production_fixture_rejected(self) -> None:
        duplicate = replace(self.config, fixtures=self.config.fixtures * 2)
        production = replace(self.config, fixtures=(replace(self.config.fixtures[0], target="xar_ck3_bridge"),))
        for value in (duplicate, production):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_config(config_json(value))

    def test_output_cannot_overlap_immutable_baseline(self) -> None:
        for path in (self.config.complete_build, self.config.complete_build / "child", self.root):
            with self.subTest(path=path), self.assertRaises(ValueError):
                parse_config(config_json(replace(self.config, output=path)))

    def test_traversal_in_wire_or_source_rejected(self) -> None:
        for value in (replace(self.config, wire_source="../escape.cpp"),
                      replace(self.config, wire_directory="../escape")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_config(config_json(value))

    def test_real_ninja_edge_keeps_object_library_inputs(self) -> None:
        producer = UngatedProducer(self.config)
        producer.build.mkdir(parents=True)
        (producer.build / "build.ninja").write_text(
            "build wire_fixture.exe: CXX_EXECUTABLE_LINKER CMakeFiles/wire_fixture.dir/main.cpp.obj "
            "CMakeFiles/gate_off.dir/router.cpp.obj | runtime.lib || order_depends\n", encoding="utf-8")
        actual = producer.fixture_link_objects(self.config.fixtures[0])
        self.assertEqual(actual, [producer.build / "CMakeFiles/wire_fixture.dir/main.cpp.obj",
                                  producer.build / "CMakeFiles/gate_off.dir/router.cpp.obj"])

    def test_command_failure_keeps_original_exit_and_stops(self) -> None:
        producer = UngatedProducer(self.config)
        self.config.output.mkdir()
        producer.env = dict(os.environ)
        with self.assertRaisesRegex(ValueError, "Actual command failed"):
            producer.execute("failed-command", [sys.executable, "-c", "raise SystemExit(7)"], self.root)
        result = read(self.config.output / "failed-command.actual.json")
        self.assertEqual(result["original_wait_returncode"], 7)
        self.assertIsNone(result["stopped_reason"])
        self.assertFalse(result["game_started_or_attached"])


if __name__ == "__main__":
    unittest.main()
