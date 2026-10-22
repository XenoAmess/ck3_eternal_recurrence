"""Finite admission, serialization and actual command-failure regressions."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from typing import Protocol, runtime_checkable

from build_native_configured_successor import (
    ChildEnvironment, Config, Fixture, MsvcInitializer, MsvcInstallation,
    Pin, Producer, ROOT, allocated, cmake_boolean_flags, config_json, load_shared, obj, parse_config, parse_pin, read,
    same_metadata_content,
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


@runtime_checkable
class ExactCommandBuildHook(Protocol):
    def __call__(self, repo: Path, source: Path, build: Path, compiler_argv: list[str],
                 exe_paths: list[Path], external_candidate: str | None = None,
                 return_code: int = 0,
                 source_commands: list[dict[str, object]] | None = None) -> object: ...


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

    def test_real_windows_cache_comment_bytes_preserve_exact_ascii_flags(self) -> None:
        cache = self.root / "CMakeCache.txt"
        cache.write_bytes("//缓存说明\n".encode("gbk") + b"XAR_FEATURE:BOOL=ON\nBUILD_TESTING:BOOL=OFF\n")
        self.assertEqual(cmake_boolean_flags(cache), {"XAR_FEATURE": "ON", "BUILD_TESTING": "OFF"})
        cache.write_bytes(b"XAR_FEATURE:BOOL=ON\nXAR_FEATURE:BOOL=OFF\n")
        with self.assertRaises(ValueError):
            cmake_boolean_flags(cache)

    def test_resume_json_roundtrip_allows_only_observation_time_change(self) -> None:
        self.assertTrue(same_metadata_content({"observed_at_utc": "old", "slots": [1, 2], "missing": None},
                                              {"observed_at_utc": "new", "slots": (1, 2), "missing": None}))
        self.assertFalse(same_metadata_content({"observed_at_utc": "old", "slots": [1, 2]},
                                               {"observed_at_utc": "new", "slots": [1, 3]}))
        self.assertFalse(same_metadata_content({"slots": []}, {"slots": None}))
        self.assertFalse(same_metadata_content({"identity": 1}, {"identity": True}))
        self.assertFalse(same_metadata_content({"identity": 1}, {"identity": 1.0}))

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

    def test_capacity_scan_accepts_only_an_actual_deleted_walk_entry(self) -> None:
        kept = self.root / "kept.bin"
        temporary = self.root / "tmp.json"
        kept.write_bytes(b"x" * 4097)
        temporary.write_bytes(b"transient CMake FileAPI output")
        original_stat = Path.stat
        deleted = False

        def remove_before_stat(path: Path, *, follow_symlinks: bool = True) -> os.stat_result:
            nonlocal deleted
            if path == temporary and follow_symlinks and not deleted:
                temporary.unlink()
                deleted = True
            return original_stat(path, follow_symlinks=follow_symlinks)

        with patch.object(Path, "stat", remove_before_stat):
            self.assertEqual(allocated(self.root), 4096 + 8192)
        self.assertTrue(deleted)
        self.assertFalse(temporary.exists())
        self.assertEqual(kept.stat().st_size, 4097)

    def test_capacity_scan_keeps_permission_and_unknown_stat_errors(self) -> None:
        present = self.root / "present.bin"
        present.write_bytes(b"present")
        original_stat = Path.stat
        for error_type in (PermissionError, OSError):
            def reject_stat(path: Path, *, follow_symlinks: bool = True) -> os.stat_result:
                if path == present and follow_symlinks:
                    raise error_type("fixture stat rejected")
                return original_stat(path, follow_symlinks=follow_symlinks)

            with self.subTest(error=error_type.__name__), patch.object(Path, "stat", reject_stat):
                with self.assertRaisesRegex(error_type, "fixture stat rejected"):
                    allocated(self.root)

    def test_actual_unused_off_transport_fails_direct_link_but_lazy_archive_passes(self) -> None:
        """Exercise the actual LNK2019 path that stopped the production successor."""
        producer = UngatedProducer(self.config)
        producer.build.mkdir(parents=True)
        shared = load_shared(ROOT / "tools/run_native_msvc.py", "lazy_link_regression_msvc")
        child: object = getattr(shared, "child_environment", None)
        install: object = getattr(shared, "visual_studio_installation", None)
        initialize: object = getattr(shared, "initialize_msvc", None)
        if not isinstance(child, ChildEnvironment) or not isinstance(install, MsvcInstallation) or not isinstance(initialize, MsvcInitializer):
            self.fail("Actual MSVC toolchain unavailable; this regression must not skip")
        producer.env = child(producer.build)
        producer.env, producer.tools = initialize(install(None, producer.env), producer.build, producer.env)
        bodies = {"main": "int wanted(); int main(){return wanted()==7?0:1;}\n",
                  "wanted": "int wanted(){return 7;}\n",
                  "unused_off_transport": "int missing_off_helper(); int unused(){return missing_off_helper();}\n"}
        objects: list[Path] = []
        commands: list[dict[str, object]] = []
        for name, body in bodies.items():
            source = producer.build / (name + ".cpp")
            output = producer.build / (name + ".obj")
            source.write_text(body, encoding="utf-8")
            argv = [producer.tools["cl"], "/nologo", "/c", "/O2", "/Fo" + str(output), str(source)]
            producer.execute("compile-" + name, argv, producer.build)
            commands.append({"argv": argv, "return_code": 0})
            objects.append(output)
        with self.assertRaisesRegex(ValueError, "Actual command failed"):
            producer.link("direct-link-must-fail", objects, [], producer.build / "direct.exe")
        failed = read(self.config.output / "direct-link-must-fail.actual.json")
        self.assertNotEqual(failed["original_wait_returncode"], 0)
        archive, archive_execution = producer.archive_runtime(objects[1:])
        self.assertIsNotNone(archive_execution)
        if archive is None:
            self.fail("Changed runtime archive was not produced")
        producer.link("lazy-link", objects[:1], [archive], producer.build / "lazy.exe")
        registry = load_shared(ROOT / "tools/register_project_exe_exclusions.py", "lazy_link_regression_defender")
        hook: object = getattr(registry, "after_successful_command_build", None)
        if not isinstance(hook, ExactCommandBuildHook):
            self.fail("Actual project EXE exclusion hook unavailable")
        link_argv = [str(Path(producer.tools["cl"]).parent / "link.exe"),
            *producer.arguments((producer.build / "lazy-link.rsp").read_text(encoding="utf-8"))]
        registration = obj(hook(ROOT, producer.build, producer.build, link_argv,
            [producer.build / "lazy.exe"], "configured-successor-lazy-link-real-regression", 0, commands))
        self.assertIn(registration["status"], ("verified", "disabled"))
        producer.execute("lazy-run", [str(producer.build / "lazy.exe")], producer.build)
        self.assertEqual(read(self.config.output / "lazy-run.actual.json")["original_wait_returncode"], 0)


if __name__ == "__main__":
    unittest.main()
