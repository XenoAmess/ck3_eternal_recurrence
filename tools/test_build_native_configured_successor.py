"""Finite admission, serialization and actual command-failure regressions."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from typing import Protocol, runtime_checkable

from build_native_configured_successor import (
    ChildEnvironment, Compile, Config, Fixture, MsvcInitializer, MsvcInstallation,
    HOST_TEST_COMPANION_RELATIVE, NONCOMPILED_CONSUMER_RELATIVE, NoncompiledConsumerReplay, NoncompiledReplayProof,
    Pin, Producer, ROOT, allocated, arr, cmake_boolean_flags,
    config_json, git, load_shared, obj, parse_config, parse_pin, pin, read,
    same_metadata_content, verified_fixture_object_bindings, verified_noncompiled_consumer_replay,
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


class ProcessFixtureProducer(UngatedProducer):
    """Real CL/link/process regression; OS registration and public Q are separate tests."""
    def defender(self, fixtures: list[dict[str, object]], label: str) -> Pin:
        return self.save(label + "-test-only-admin-boundary.json", {
            "test_only": True, "actual_administrative_readback_qualified": False})

    def seal(self, rows: list[Compile], fixtures: list[dict[str, object]], build_execution: Pin,
             defender: Pin, plan: Pin, dll: Path, *, resume: bool = False) -> Pin:
        return self.save("TEST-ONLY-COMPLETE.json", {"test_only": True, "fixture_results": fixtures,
            "production_execution": build_execution, "public_runtime_qualified": False})


@dataclass
class RetainedPlanFixture:
    """Authored evidence exercises the real producer, without claiming native Q."""
    producer: UngatedProducer
    rows: list[Compile]
    names: list[str]
    documents: dict[str, dict[str, object]]
    paths: dict[str, Path]
    current_text: str

    def refresh(self) -> None:
        edges = {
            "verification": {"source_manifest": "source"},
            "incremental": {"production_plan": "plan", "actual_link": "execution"},
            "freeze": {"incremental_production_plan": "plan", "incremental_production_result": "incremental",
                "source_manifest": "source", "source_verification": "verification", "profile": "profile",
                "scope": "scope", "build_execution": "execution"},
            "qualification": {"snapshot": "source", "source_verification": "verification", "profile": "profile",
                "configured_scope": "scope", "production_freeze": "freeze", "production_build_receipt": "execution"},
        }
        for name in ("source", "verification", "profile", "scope", "plan", "execution", "incremental", "freeze", "qualification"):
            for field, dependency in edges.get(name, {}).items():
                self.documents[name][field] = pin(self.paths[dependency])
            self.paths[name].write_text(json.dumps(self.documents[name]), encoding="utf-8")
        self.producer.config = replace(self.producer.config,
            retained_dependency_evidence={"qualification": pin(self.paths["qualification"])})

    def git_output(self, *arguments: str) -> str:
        if arguments[0] == "merge-base":
            return "b" * 40
        if arguments[0] == "ls-files":
            return "\n".join(self.names)
        raise AssertionError("Unexpected Git boundary: " + repr(arguments))


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

    def test_v2_dependency_evidence_roundtrip_preserves_null_and_rejects_undeclared_authorities(self) -> None:
        v2 = replace(self.config, schema="ck3-configured-native-successor-v2")
        for config in (v2, replace(v2, retained_dependency_evidence={"qualification": reference("old-qualified.json")})):
            self.assertEqual(parse_config(json.loads(json.dumps(config_json(config)))), config)
        self.assertIsNone(config_json(v2)["retained_dependency_evidence"])
        missing = config_json(v2)
        del missing["retained_dependency_evidence"]
        invalid: list[dict[str, object]] = [missing]
        invalid_evidence: tuple[object, ...] = (
            {}, [], {"qualification": None}, {"qualification": reference("q"), "undeclared": None},
        )
        for value in invalid_evidence:
            item = config_json(v2)
            item["retained_dependency_evidence"] = value
            invalid.append(item)
        v1 = config_json(self.config)
        v1["retained_dependency_evidence"] = None
        invalid.append(v1)
        conflicting = config_json(replace(v2, retained_dependency_evidence={"qualification": reference("q")},
                                         compiled_seed=reference("seed")))
        invalid.append(conflicting)
        for item in invalid:
            with self.subTest(value=item), self.assertRaises(ValueError):
                parse_config(item)

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

    def test_budget_accepts_192_mib_and_smaller_lanes_through_json_roundtrip(self) -> None:
        for schema in ("ck3-configured-native-successor-v1", "ck3-configured-native-successor-v2"):
            for size in (1, 160 * 1024 * 1024, 176705326, 192 * 1024 * 1024):
                expected = replace(self.config, schema=schema, budget=size)
                with self.subTest(schema=schema, size=size):
                    actual = parse_config(json.loads(json.dumps(config_json(expected))))
                    self.assertEqual(actual, expected)
                    self.assertEqual(actual.budget, size)

    def test_budget_rejects_noninteger_and_nonpositive_sizes(self) -> None:
        for size in (True, False, 160.0, float(192 * 1024 * 1024), "201326592", None, 0, -1):
            value = config_json(self.config)
            value["budget_bytes"] = size
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, "Exact bounded integer required"):
                parse_config(value)

    def test_budget_rejects_one_byte_above_192_mib(self) -> None:
        for schema in ("ck3-configured-native-successor-v1", "ck3-configured-native-successor-v2"):
            value = config_json(replace(self.config, schema=schema))
            value["budget_bytes"] = 192 * 1024 * 1024 + 1
            with self.subTest(schema=schema), self.assertRaisesRegex(ValueError, "Native lane exceeds 192 MiB"):
                parse_config(json.loads(json.dumps(value)))

    def _budget_gated_producer(self, budget: int, grant_budget: object, *, include_budget: bool = True) -> Producer:
        admission: dict[str, object] = {
            "machine_id": self.config.machine_id, "active": True,
            "capacity_passed": True, "quota_passed": True,
            "approved_root": str(self.root), "expires_at_utc": "2099-01-01T00:00:00+00:00",
            "required_free_bytes": 0,
        }
        if include_budget:
            admission["budget_bytes"] = grant_budget
        path = self.root / "admission.json"
        path.write_text(json.dumps(admission), encoding="utf-8")
        config = replace(self.config, schema="ck3-configured-native-successor-v2",
                         budget=budget, admission=pin(path))
        return Producer(parse_config(json.loads(json.dumps(config_json(config)))))

    def test_real_gate_accepts_roundtripped_budget_at_or_below_192_mib_grant(self) -> None:
        for size in (160 * 1024 * 1024, 176705326, 192 * 1024 * 1024):
            producer = self._budget_gated_producer(size, 192 * 1024 * 1024)
            with self.subTest(size=size), patch("build_native_configured_successor.git",
                                               side_effect=[producer.config.source_commit, ""]):
                producer.gate()
            self.assertEqual(producer.config.budget, size)
            self.assertFalse(producer.config.output.exists())

    def test_real_gate_rejects_budget_one_byte_above_actual_grant(self) -> None:
        producer = self._budget_gated_producer(192 * 1024 * 1024, 192 * 1024 * 1024 - 1)
        with patch("build_native_configured_successor.git", side_effect=[producer.config.source_commit, ""]), \
             self.assertRaisesRegex(ValueError, "Native lane exceeds admitted budget"):
            producer.gate()
        self.assertFalse(producer.config.output.exists())

    def test_real_gate_rejects_missing_or_noninteger_grant_budget(self) -> None:
        for grant_budget in (True, False, float(192 * 1024 * 1024), "201326592", None, 0, -1):
            producer = self._budget_gated_producer(192 * 1024 * 1024, grant_budget)
            with self.subTest(grant_budget=grant_budget), \
                 patch("build_native_configured_successor.git", side_effect=[producer.config.source_commit, ""]), \
                 self.assertRaisesRegex(ValueError, "Exact bounded integer required"):
                producer.gate()
            self.assertFalse(producer.config.output.exists())
        producer = self._budget_gated_producer(192 * 1024 * 1024, None, include_budget=False)
        with patch("build_native_configured_successor.git", side_effect=[producer.config.source_commit, ""]), \
             self.assertRaisesRegex(ValueError, "Exact bounded integer required"):
            producer.gate()
        self.assertFalse(producer.config.output.exists())

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

    def partial_fixture(self) -> ProcessFixtureProducer:
        """Produce the real pre-execution failure, including an unknown old EXE."""
        machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
            str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT).decode().strip()
        references: list[Pin] = []
        for name in ("baseline.json", "inputs.json", "profile.cmake"):
            path = self.root / name
            path.write_text("" if name.endswith("cmake") else "{}", encoding="utf-8")
            references.append(pin(path))
        self.config = replace(self.config, machine_id=machine, source_commit=git("rev-parse", "HEAD"),
            baseline=references[0], incremental_inputs=references[1], profile_cmake=references[2],
            fixtures=(Fixture("wire_fixture", (), (), ()),))
        producer = ProcessFixtureProducer(self.config)
        producer.native = self.root / "native"
        producer.native.mkdir()
        bodies = {"protocol.cpp": "int protocol(){return 1;}\n",
            "runtime.cpp": "int wanted(){return 7;}\n", "bridge.cpp": "int bridge(){return 2;}\n",
            "main.cpp": "int wanted(); int main(){return wanted()==7?0:1;}\n"}
        for name, body in bodies.items():
            (producer.native / name).write_text(body, encoding="utf-8")
        (producer.native / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n"
            "project(FixtureResume LANGUAGES CXX)\n"
            "add_library(xar_bridge_protocol STATIC protocol.cpp)\n"
            "add_library(xar_ck3_12002_runtime STATIC runtime.cpp)\n"
            "add_library(xar_ck3_bridge SHARED bridge.cpp)\n"
            "add_executable(wire_fixture main.cpp)\n"
            "target_link_libraries(wire_fixture PRIVATE xar_ck3_12002_runtime)\n", encoding="utf-8")
        producer.initialize()
        producer.configure()
        rows = producer.commands()
        production_compiles: list[dict[str, object]] = []
        selection: list[dict[str, object]] = []
        self.config.complete_build.mkdir()
        for row in rows:
            if row.target == "wire_fixture":
                continue
            actual = producer.compile(row, "original-" + row.target)
            production_compiles.append({"target": row.target, "source": pin(row.source), "object": pin(row.output),
                "actual_compile": actual, "compile_reused": False})
            selection.append({"target": row.target, "source": row.source.relative_to(producer.native).as_posix(),
                "output": row.output.relative_to(producer.build).as_posix(), "compiled": True})
            if row.target != "xar_ck3_bridge":
                producer.execute("original-archive-" + row.target, [str(Path(producer.tools["cl"]).parent / "lib.exe"),
                    "/nologo", "/OUT:" + str(self.config.complete_build / (row.target + ".lib")), str(row.output)], producer.build)
        libraries = [self.config.complete_build / "xar_bridge_protocol.lib",
                     self.config.complete_build / "xar_ck3_12002_runtime.lib"]
        dependencies = producer.save("dependencies.json", {"test_only": True})
        bridge = next(row for row in rows if row.target == "xar_ck3_bridge")
        plan = producer.save("native-a01/PLAN.actual.json", {"machine_id": self.config.machine_id,
            "source_commit": self.config.source_commit, "baseline_qualification": self.config.baseline,
            "baseline_incremental_inputs": self.config.incremental_inputs, "original_dependencies": dependencies,
            "production_selections": selection, "retained_link_inputs": [pin(path) for path in libraries],
            "retained_incremental_object": pin(bridge.output)})
        dll = producer.build / "xar_ck3_bridge.dll"
        link = producer.link("link-production", [bridge.output], libraries, dll, True)
        producer.save("native-a01/INCREMENTAL-RESULT.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": "test-only", "retained_archive_mode": "test-only actual small archives",
            "source_commit": self.config.source_commit, "game_started_or_attached": False, "archive_copies": 0,
            "compiled_seed": None, "production_plan": plan, "production_compiles": production_compiles,
            "actual_link": link, "dll": pin(dll), "changed_runtime_archive": None,
            "changed_runtime_archive_execution": None})
        own = next(row for row in rows if row.target == "wire_fixture")
        producer.compile(own, "wire_fixture-compile-0")
        original_save = producer.save

        def fail_after_actual_link(name: str, value: object) -> Pin:
            if name == "wire_fixture-link.actual.json":
                raise ValueError("Native metadata budget exhausted")
            return original_save(name, value)

        with patch.object(producer, "save", fail_after_actual_link):
            with self.assertRaisesRegex(ValueError, "Native metadata budget exhausted"):
                producer.link("wire_fixture-link", [own.output], libraries, producer.build / "wire_fixture.exe")
        self.assertFalse((producer.meta / "ALL-FIXTURES.actual.json").exists())
        self.assertFalse((producer.config.output / "wire_fixture-link.actual.json").exists())
        self.assertTrue((producer.config.output / "wire_fixture-link.log").is_file())
        self.assertTrue((producer.build / "wire_fixture.exe").is_file())
        return producer

    def test_real_partial_fixture_resume_preserves_unknown_exe_and_relinks_without_production(self) -> None:
        producer = self.partial_fixture()
        executable = producer.build / "wire_fixture.exe"
        old_pin, old_id = pin(executable), executable.stat().st_ino
        unchanged = [producer.config.output / "link-production.actual.json", producer.build / "xar_ck3_bridge.dll",
            producer.config.output / "wire_fixture-link.log", producer.build / "wire_fixture-link.rsp"]
        old_inputs = [pin(path) for path in unchanged]
        with patch.object(producer, "configure", side_effect=AssertionError("Production must not reconfigure")), \
             patch.object(producer, "archive_runtime", side_effect=AssertionError("Production must not rearchive")):
            result = producer.resume_fixtures("fresh-a01")
        archived = producer.config.output / "fresh-a01-preserved/wire_fixture.exe"
        self.assertEqual(archived.stat().st_ino, old_id)
        self.assertEqual(pin(archived)["sha256"], old_pin["sha256"])
        self.assertNotEqual(executable.stat().st_ino, old_id)
        self.assertEqual([pin(path) for path in unchanged], old_inputs)
        self.assertEqual(read(Path(result["path"]))["production_execution"], pin(unchanged[0]))
        for label in ("fresh-a01-wire_fixture-link", "fresh-a01-test-wire_fixture"):
            self.assertEqual(read(producer.config.output / (label + ".actual.json"))["original_wait_returncode"], 0)
        self.assertFalse(list(producer.config.output.glob("fresh-a01-production*")))

    def test_partial_resume_rejects_wrong_missing_and_bool_original_execution_before_mutation(self) -> None:
        producer = self.partial_fixture()
        original = producer.meta / "INCREMENTAL-RESULT.actual.json"
        saved = original.read_bytes()
        executable = pin(producer.build / "wire_fixture.exe")
        for field, value in (("source_commit", "b" * 40), ("compiled_seed", reference("seed")),
                             ("archive_copies", True), ("production_compiles", [])):
            data = read(original)
            data[field] = value
            original.write_text(json.dumps(data), encoding="utf-8")
            with self.subTest(field=field), self.assertRaises(ValueError):
                producer.resume_fixtures("reject-" + field)
            self.assertEqual(pin(Path(executable["path"])), executable)
            self.assertFalse(list(producer.config.output.glob("reject-*-preserved")))
            original.write_bytes(saved)
        data = read(original)
        del data["actual_link"]
        original.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Exact original production result"):
            producer.resume_fixtures("reject-missing")
        self.assertEqual(pin(Path(executable["path"])), executable)
        original.write_bytes(saved)
        execution = producer.config.output / "link-production.actual.json"
        data = read(execution)
        data["original_wait_returncode"] = True
        execution.write_text(json.dumps(data), encoding="utf-8")
        data = read(original)
        data["actual_link"] = pin(execution)
        original.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "successful command"):
            producer.resume_fixtures("reject-bool")
        self.assertEqual(pin(Path(executable["path"])), executable)

    def test_partial_resume_refuses_completed_or_already_executed_fixtures(self) -> None:
        producer = UngatedProducer(self.config)
        producer.meta.mkdir(parents=True)
        # Refusal precedes all compiler/rename activity; machine is the only boundary stub.
        with patch("build_native_configured_successor.subprocess.check_output", return_value=b"fixture-machine"):
            complete = producer.meta / "ALL-FIXTURES.actual.json"
            complete.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "metadata-only"):
                producer.resume_fixtures("fresh")
            complete.unlink()
            (self.config.output / "earlier-test-wire_fixture.log").write_text("started", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "before any original fixture execution"):
                producer.resume_fixtures("fresh")

    def test_link_refuses_an_existing_response_without_overwriting_or_starting(self) -> None:
        producer = UngatedProducer(self.config)
        producer.build.mkdir(parents=True)
        producer.tools = {"cl": "unused/cl.exe"}
        response = producer.build / "existing.rsp"
        response.write_text("immutable unknown original", encoding="utf-8")
        before = pin(response)
        with patch.object(producer, "execute", side_effect=AssertionError("Must not start")):
            with self.assertRaises(FileExistsError):
                producer.link("existing", [], [], producer.build / "unused.exe")
        self.assertEqual(pin(response), before)

    def test_readonly_object_contract_refuses_relative_empty_and_foreign_paths(self) -> None:
        for outputs in ([], ["relative.obj"], [str(self.root / "foreign.obj")]):
            with self.subTest(outputs=outputs), self.assertRaises(ValueError):
                verified_fixture_object_bindings(config_json(self.config), outputs)

    def test_readonly_existing_plan_recomputes_sources_options_and_dependencies_without_writes(self) -> None:
        self._readonly_plan_replay(consumer=False)

    def retained_plan_fixture(self) -> RetainedPlanFixture:
        """The changed macro header is visible only in the old compiler inventory."""
        repository = self.root / "repo"
        native = repository / "ck3_autonomous_player/native_bridge"
        header = native / "include/xar/activity_typed_planner_v1.hpp"
        header.parent.mkdir(parents=True)
        header.write_text("// source-root identity\n", encoding="utf-8")
        indirect = header.parent / "macro_selected.inc"
        indirect.write_text("// changed macro-selected header\n", encoding="utf-8")
        rows: list[Compile] = []
        names = [path.relative_to(repository).as_posix() for path in (header, indirect)]
        snapshot: list[dict[str, object]] = [{"native_relative": path.relative_to(native).as_posix(),
            "bytes": 0 if path == indirect else pin(path)["bytes"], "sha256": pin(path)["sha256"]}
            for path in (header, indirect)]
        commands: list[dict[str, object]] = []
        blocks: list[str] = []
        for target, name in (("xar_bridge_protocol", "protocol"), ("xar_ck3_12002_runtime", "runtime"),
                             ("xar_ck3_bridge", "bridge")):
            source = native / ("src/" + name + ".cpp")
            source.parent.mkdir(exist_ok=True)
            source.write_text("#include MACRO_HEADER\nint " + name + ";\n", encoding="utf-8")
            names.append(source.relative_to(repository).as_posix())
            snapshot.append({"native_relative": source.relative_to(native).as_posix(),
                "bytes": pin(source)["bytes"], "sha256": pin(source)["sha256"]})
            output_name = "CMakeFiles/" + target + ".dir/src/" + name + ".cpp.obj"
            output = self.config.output / "build" / output_name
            old_output = self.config.complete_build / output_name
            argv = (sys.executable, "/c", str(source), "/Fo" + str(output))
            rows.append(Compile(target, source, output, argv))
            commands.append({"directory": str(self.config.complete_build), "file": str(source),
                "output": str(old_output), "command": subprocess.list2cmdline([
                    sys.executable, "/c", str(source), "/Fo" + str(old_output)])})
            deps = [str(source), str(header), *([str(indirect)] if name == "runtime" else [])]
            blocks.append(output_name + ": #deps " + str(len(deps)) + ", deps mtime 123 (VALID)\n"
                + "".join("    " + dependency + "\n" for dependency in deps) + "\n")
        self.config.complete_build.mkdir(parents=True)
        borrowed = self.config.complete_build / "CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj"
        borrowed.parent.mkdir(parents=True)
        borrowed.write_bytes(b"unchanged physical bridge object")
        libraries = [self.config.complete_build / name for name in ("xar_ck3_12002_runtime.lib", "xar_bridge_protocol.lib")]
        for library in libraries:
            library.write_bytes(b"immutable authored archive fixture")
        retained = [pin(borrowed), *(pin(path) for path in libraries)]

        def put(name: str, value: object) -> Pin:
            path = self.root / name
            path.write_text(json.dumps(value), encoding="utf-8")
            return pin(path)

        command_ref = put("old-commands.json", commands)
        scope_ref = put("baseline-scope.json", {"compile_commands": command_ref})
        snapshot_ref = put("baseline-source.json", {"snapshot_native_base": str(native), "files": snapshot})
        baseline = put("baseline.json", {"machine_id": self.config.machine_id, "snapshot": snapshot_ref, "configured_scope": scope_ref})
        inputs = put("inputs.json", {"inputs": retained, "new_object": pin(borrowed)})
        profile_cmake = self.root / "profile.cmake"
        profile_cmake.write_bytes(b"# same retained profile\n")
        dependency_path = self.root / "old-dependencies.txt"
        text = "".join(blocks)
        dependency_path.write_text(text, encoding="utf-8")
        log = self.root / "old-link.log"
        log.write_bytes(b"authored successful link boundary\n")
        dll = self.root / "old.dll"
        dll.write_bytes(b"authored retained DLL identity\n")
        unused = put("unconsumed-original.json", {"test_only": True})
        config = replace(self.config, baseline=baseline, incremental_inputs=inputs, profile_cmake=pin(profile_cmake),
            schema="ck3-configured-native-successor-v2")
        producer = UngatedProducer(config)
        producer.native = native
        producer.tools = {"ninja": "authored-ninja-boundary"}
        config.output.mkdir()
        machine, commit = config.machine_id, "b" * 40
        documents: dict[str, dict[str, object]] = {
            "source": {"machine_id": machine, "root_commit": commit, "native_source_commit": commit,
                "source_count": len(snapshot), "files": snapshot},
            "verification": {"machine_id": machine, "root_commit": commit,
                "all_snapshot_files_exactly_verified": len(snapshot), "all_original_inputs_still_exactly_verified": len(snapshot)},
            "profile": {"machine_id": machine, "repository_default_flags_changed": False, "profile": pin(profile_cmake)},
            "scope": {"compile_commands": command_ref},
            "plan": {"machine_id": machine, "observed_at_utc": "authored", "source_commit": commit,
                "baseline_qualification": baseline, "baseline_incremental_inputs": inputs,
                "original_dependencies": pin(dependency_path), "changed_native_paths": [], "production_selections": [],
                "retained_link_inputs": retained, "retained_incremental_object": pin(borrowed), "archive_copies": 0},
            "execution": {"machine_id": machine, "source_commit": commit, "original_wait_returncode": 0,
                "stopped_reason": None, "game_started_or_attached": False, "actual_live_business_qualified": False,
                "log": pin(log), "response_files": []},
            "incremental": {"machine_id": machine, "source_commit": commit, "dll": pin(dll), "archive_copies": 0,
                "game_started_or_attached": False},
            "freeze": {"machine_id": machine, "observed_at_utc": "authored", "root_commit": commit,
                "original_DLL": pin(dll), "published_DLL": pin(dll), "no_fixture_target_in_production_dependency_closure": True,
                "repository_default_flags_changed": False, "game_started_or_attached": False},
            "qualification": {"schema": "ck3-qualified-native-build-v1", "machine_id": machine,
                "observed_at_utc": "authored", "source_commit": commit, "actual_live_business_qualified": False,
                "original_dll": pin(dll), "published_dll": pin(dll), "delivery": unused,
                "defender_binding": unused, "fixture_results": [], "execution_wire_packets": unused},
        }
        fixture = RetainedPlanFixture(producer, rows, names, documents,
            {name: self.root / ("old-" + name + ".json") for name in documents},
            text.replace("runtime.cpp.obj: #deps 3, deps mtime 123 (VALID)",
                         "runtime.cpp.obj: #deps 3, deps mtime 123 (STALE)"))
        fixture.refresh()
        return fixture

    def test_actual_plan_reuses_qualified_inventory_for_indirect_macro_header_and_replays_without_writes(self) -> None:
        fixture = self.retained_plan_fixture()
        producer = fixture.producer
        config = parse_config(json.loads(json.dumps(config_json(producer.config))))
        self.assertEqual(config, producer.config)
        with patch("build_native_configured_successor.ROOT", producer.native.parent.parent), \
             patch("build_native_configured_successor.git", side_effect=fixture.git_output), \
             patch("build_native_configured_successor.subprocess.run", return_value=SimpleNamespace(stdout=fixture.current_text)) as query:
            without = replace(config, schema="ck3-configured-native-successor-v1", retained_dependency_evidence=None)
            producer.config = without
            with self.assertRaisesRegex(ValueError, "Actual old compiler dependencies missing"):
                producer.plan(fixture.rows)
            producer.config = config
            selected, borrowed, plan_ref = producer.plan(fixture.rows)
            self.assertEqual([row.target for row in selected], ["xar_ck3_12002_runtime"])
            self.assertEqual(set(borrowed), {"CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj"})
            query.assert_called_with(["authored-ninja-boundary", "-C", str(config.complete_build), "-t", "deps"],
                env={}, capture_output=True, check=True, text=True, encoding="utf-8")
            plan = read(Path(plan_ref["path"]))
            self.assertEqual(plan["original_dependencies"], fixture.documents["plan"]["original_dependencies"])
            reuse = obj(plan["retained_dependency_reuse"])
            self.assertEqual(reuse["stale_outputs"], ["CMakeFiles/xar_ck3_12002_runtime.dir/src/runtime.cpp.obj"])
            capture = Path(parse_pin(reuse["current_capture"])["path"])
            self.assertIn("(STALE)", capture.read_text())
            self.assertEqual(obj(arr(plan["production_selections"])[1])["changed_dependencies"],
                             ["include/xar/macro_selected.inc"])
            # Authored process receipts exercise the public proof consumer, not a
            # claim that these small fixture bytes were compiled by native CL.
            log = config.output / "fixture-boundary.log"
            log.write_bytes(b"authored process boundary, not actual native qualification")

            def receipt(name: str, argv: list[str]) -> Pin:
                return producer.save(name, {"machine_id": config.machine_id, "source_commit": config.source_commit,
                    "original_wait_returncode": 0, "stopped_reason": None, "game_started_or_attached": False,
                    "actual_live_business_qualified": False, "log": pin(log), "response_files": [],
                    "argv": argv, "cwd": str(producer.build)})

            producer.build.mkdir()
            receipt("configure.actual.json", ["cmake", "-S", str(producer.native), "-B", str(producer.build),
                "-G", "Ninja", "-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES=" + config.profile_cmake["path"],
                "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])
            runtime = selected[0]
            runtime.output.parent.mkdir(parents=True)
            runtime.output.write_bytes(b"authored new runtime object identity")
            compile_ref = receipt("runtime-compile.actual.json", list(runtime.argv))
            link_ref = receipt("link-production.actual.json", ["link.exe", "/DLL"])
            dll = producer.build / "xar_ck3_bridge.dll"
            dll.write_bytes(b"authored completed DLL identity")
            producer.save("native-a01/INCREMENTAL-RESULT.actual.json", {"machine_id": config.machine_id,
                "observed_at_utc": "authored", "source_commit": config.source_commit, "production_plan": plan_ref,
                "production_compiles": [{"target": runtime.target, "source": pin(runtime.source),
                    "object": pin(runtime.output), "actual_compile": compile_ref, "compile_reused": False}],
                "actual_link": link_ref, "dll": pin(dll), "archive_copies": 0,
                "changed_runtime_archive": None, "changed_runtime_archive_execution": None,
                "compiled_seed": None, "retained_archive_mode": "authored", "game_started_or_attached": False})
            (producer.build / "compile_commands.json").write_text(json.dumps([
                {"directory": str(producer.build), "file": str(row.source), "output": str(row.output),
                 "command": subprocess.list2cmdline(row.argv)} for row in fixture.rows]), encoding="utf-8")
            with patch("build_native_configured_successor.Producer", return_value=producer), \
                 patch.object(producer, "commands", return_value=fixture.rows):
                proof = verified_fixture_object_bindings(config_json(config), [str(runtime.output)])
                self.assertEqual(proof.production_plan, plan_ref)
                self.assertEqual(proof.original_dependencies, plan["original_dependencies"])
                self.assertEqual(proof.objects[0]["object"], pin(runtime.output))
            with patch.object(producer, "save", side_effect=AssertionError("Replay cannot write")), \
                 patch("build_native_configured_successor.subprocess.run", side_effect=AssertionError("Replay cannot query Ninja")):
                self.assertEqual(producer.plan(fixture.rows, existing_plan=plan_ref)[2], plan_ref)
                output = config.complete_build / str(arr(reuse["stale_outputs"])[0])
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"object reappeared after capture")
                with self.assertRaisesRegex(ValueError, "Stale dependency output is present"):
                    producer.plan(fixture.rows, existing_plan=plan_ref)
                with self.assertRaisesRegex(ValueError, "Stale dependency output is present"):
                    producer.original_fixture_inputs(fixture.rows)
                output.unlink()
                capture.write_text(capture.read_text().replace("mtime 123", "mtime 124"), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Pinned input changed"):
                    producer.plan(fixture.rows, existing_plan=plan_ref)

    def test_actual_plan_rejects_dependency_record_drift_instead_of_reinterpreting_stale(self) -> None:
        fixture = self.retained_plan_fixture()
        text = fixture.current_text
        records = text.split("\n\n")
        runtime = records[1].splitlines()
        variants = [text.replace("#deps 3", "#deps 2"), text.replace("mtime 123", "mtime 124"),
            text.replace("(STALE)", "(UNKNOWN)"), text.replace("CMakeFiles/", "../CMakeFiles/", 1),
            text.replace("runtime.cpp.obj", "substituted.cpp.obj"),
            text.replace("macro_selected.inc", "substituted.inc"), "\n\n".join(records[:-2]) + "\n\n",
            text + records[0] + "\n\n", text.replace("#deps 3,", "#deps 4,"),
            text.replace("\n".join(runtime), "\n".join([runtime[0], runtime[2], runtime[1], runtime[3]])),
            text.replace(runtime[3], runtime[2])]
        with patch("build_native_configured_successor.ROOT", fixture.producer.native.parent.parent), \
             patch("build_native_configured_successor.git", side_effect=fixture.git_output):
            for changed in variants:
                with self.subTest(capture=changed), \
                     patch("build_native_configured_successor.subprocess.run", return_value=SimpleNamespace(stdout=changed)), \
                     self.assertRaises(ValueError):
                    fixture.producer.plan(fixture.rows)

    def test_metadata_resume_and_final_seal_revalidate_retained_evidence_before_writes(self) -> None:
        fixture = self.retained_plan_fixture()
        producer = fixture.producer
        with patch("build_native_configured_successor.ROOT", producer.native.parent.parent), \
             patch("build_native_configured_successor.git", side_effect=fixture.git_output), \
             patch("build_native_configured_successor.subprocess.run", return_value=SimpleNamespace(stdout=fixture.current_text)):
            _, _, plan_ref = producer.plan(fixture.rows)
            output = producer.config.complete_build / "CMakeFiles/xar_ck3_12002_runtime.dir/src/runtime.cpp.obj"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"stale object reappeared before metadata continuation")
            with patch.object(producer, "save", side_effect=AssertionError("Invalid evidence cannot write")), \
                 patch.object(producer, "commands", return_value=fixture.rows), \
                 patch("build_native_configured_successor.subprocess.check_output",
                       return_value=producer.config.machine_id.encode("utf-8")):
                with self.assertRaisesRegex(ValueError, "Stale dependency output is present"):
                    producer.resume_seal()
                with self.assertRaisesRegex(ValueError, "Stale dependency output is present"):
                    producer.seal(fixture.rows, [], reference("unused-build"), reference("unused-defender"),
                                  plan_ref, self.root / "unused.dll")

    def test_actual_plan_rejects_rewritten_provenance_source_archives_and_present_stale_outputs(self) -> None:
        fixture = self.retained_plan_fixture()
        with patch("build_native_configured_successor.ROOT", fixture.producer.native.parent.parent), \
             patch("build_native_configured_successor.git", side_effect=fixture.git_output), \
             patch("build_native_configured_successor.subprocess.run", return_value=SimpleNamespace(stdout=fixture.current_text)):
            mutations: tuple[tuple[str, str, object], ...] = (
                ("qualification", "machine_id", "another-machine"), ("freeze", "root_commit", "c" * 40),
                ("plan", "baseline_qualification", reference("other-baseline.json")),
                ("plan", "baseline_incremental_inputs", reference("other-inputs.json")),
                ("profile", "profile", reference("other-profile.cmake")), ("source", "root_commit", "c" * 40),
                ("source", "source_count", True), ("verification", "all_snapshot_files_exactly_verified", 0),
                ("execution", "original_wait_returncode", True), ("incremental", "game_started_or_attached", True))
            for name, field, changed in mutations:
                previous = fixture.documents[name][field]
                fixture.documents[name][field] = changed
                fixture.refresh()
                with self.subTest(document=name, field=field), self.assertRaises((ValueError, FileNotFoundError)):
                    fixture.producer.plan(fixture.rows)
                fixture.documents[name][field] = previous
                fixture.refresh()
            with patch("build_native_configured_successor.git", side_effect=lambda *args: "c" * 40
                       if args[0] == "merge-base" else fixture.git_output(*args)), \
                 self.assertRaisesRegex(ValueError, "ancestor"):
                fixture.producer.plan(fixture.rows)
            archive = fixture.producer.config.complete_build / "xar_ck3_12002_runtime.lib"
            original = archive.read_bytes()
            archive.write_bytes(original + b"tamper")
            with self.assertRaisesRegex(ValueError, "Pinned input changed"):
                fixture.producer.plan(fixture.rows)
            archive.write_bytes(original)
            original_capture = Path(parse_pin(fixture.documents["plan"]["original_dependencies"])["path"])
            valid_bytes = original_capture.read_bytes()
            original_capture.write_bytes(valid_bytes.replace(b"(VALID)", b"(STALE)", 1))
            fixture.documents["plan"]["original_dependencies"] = pin(original_capture)
            fixture.refresh()
            with self.assertRaisesRegex(ValueError, "beyond VALID/STALE"):
                fixture.producer.plan(fixture.rows)
            original_capture.write_bytes(valid_bytes)
            fixture.documents["plan"]["original_dependencies"] = pin(original_capture)
            fixture.refresh()
            output = fixture.producer.config.complete_build / "CMakeFiles/xar_ck3_12002_runtime.dir/src/runtime.cpp.obj"
            output.parent.mkdir(parents=True)
            for directory in (False, True):
                if directory:
                    output.mkdir()
                else:
                    output.write_bytes(b"present object")
                with self.subTest(directory=directory), self.assertRaisesRegex(ValueError, "Stale dependency output is present"):
                    fixture.producer.plan(fixture.rows)
                if directory:
                    output.rmdir()
                else:
                    output.unlink()
            proof = fixture.paths["qualification"]
            proof.write_bytes(proof.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "Pinned input changed"):
                fixture.producer.plan(fixture.rows)

    def test_noncompiled_replay_preserves_original_plan_and_rejects_compiler_dependencies(self) -> None:
        self._readonly_plan_replay(consumer=True)

    def test_noncompiled_replay_ignores_unbuilt_generated_sources_but_requires_declared_inputs(self) -> None:
        self._readonly_plan_replay(consumer=True, unbuilt_generated=True)

    def test_new_runtime_unit_replay_requires_actual_current_source_and_target_options(self) -> None:
        self._readonly_plan_replay(consumer=False, new_unit="xar_ck3_12002_runtime")

    def test_new_bridge_unit_is_compiled_and_never_borrowed(self) -> None:
        self._readonly_plan_replay(consumer=False, new_unit="xar_ck3_bridge")

    def _readonly_plan_replay(self, *, consumer: bool, unbuilt_generated: bool = False,
                              new_unit: str | None = None) -> None:
        native = self.root / "ck3_autonomous_player/native_bridge"
        native.mkdir(parents=True)
        header = native / "include/xar/activity_typed_planner_v1.hpp"
        header.parent.mkdir(parents=True)
        header.write_text("// owned dependency identity\n", encoding="utf-8")
        rows: list[Compile] = []
        names: list[str] = []
        old_commands: list[dict[str, object]] = []
        snapshot: list[dict[str, object]] = []
        dependencies: list[str] = []
        selections: list[dict[str, object]] = []
        for target, name in (("xar_bridge_protocol", "protocol"), ("xar_ck3_12002_runtime", "runtime"),
                             ("xar_ck3_bridge", "bridge")):
            source = native / ("src/" + name + ".cpp")
            source.parent.mkdir(exist_ok=True)
            source.write_text("int " + name + "_source;\n", encoding="utf-8")
            names.append(source.relative_to(self.root).as_posix())
            output_name = "CMakeFiles/" + target + ".dir/src/" + name + ".cpp.obj"
            output, old_output = self.config.output / "build" / output_name, self.config.complete_build / output_name
            argv = (sys.executable, "/c", str(source), "/Fo" + str(output))
            rows.append(Compile(target, source, output, argv))
            old_commands.append({"directory": str(self.config.complete_build), "file": str(source),
                "output": str(old_output), "command": subprocess.list2cmdline([sys.executable, "/c", str(source), "/Fo" + str(old_output)])})
            signature = pin(source)
            snapshot.append({"native_relative": source.relative_to(native).as_posix(),
                "bytes": 0 if name == "runtime" else signature["bytes"], "sha256": signature["sha256"]})
            dependencies.extend([output_name + ": #deps 2, deps mtime 1 (VALID)", "    " + str(source), "    " + str(header)])
            selections.append({"target": target, "output": output_name, "source": source.relative_to(native).as_posix(),
                "changed_dependencies": ["src/runtime.cpp"] if name == "runtime" else [], "compiled": name == "runtime"})
        names.append(header.relative_to(self.root).as_posix())
        snapshot.append({"native_relative": header.relative_to(native).as_posix(),
            "bytes": pin(header)["bytes"], "sha256": pin(header)["sha256"]})
        leaf = native / NONCOMPILED_CONSUMER_RELATIVE
        replay: NoncompiledConsumerReplay | None = None
        proof: NoncompiledReplayProof | None = None
        if consumer:
            leaf.parent.mkdir(parents=True)
            leaf.write_bytes(b"# exact new noncompiled consumer\n")
            before = self.root / "original-consumer.py"
            before.write_bytes(b"# exact original consumer\n")
            binding = self.root / "binding.json"
            binding.write_bytes(b"{}\n")
            replay = {"before_blob": pin(before), "after": pin(leaf), "binding": pin(binding)}
            names.append(leaf.relative_to(self.root).as_posix())
            snapshot.append({"native_relative": NONCOMPILED_CONSUMER_RELATIVE,
                             "bytes": pin(before)["bytes"], "sha256": pin(before)["sha256"]})
            companion = native / HOST_TEST_COMPANION_RELATIVE
            companion.write_bytes(b"# current host regression companion\n")
            original_test = self.root / "original-host-test.py"
            original_test.write_bytes(b"# original host regression companion\n")
            names.append(companion.relative_to(self.root).as_posix())
            snapshot.append({"native_relative": HOST_TEST_COMPANION_RELATIVE,
                             "bytes": pin(original_test)["bytes"], "sha256": pin(original_test)["sha256"]})
            proof = NoncompiledReplayProof(replay,
                {NONCOMPILED_CONSUMER_RELATIVE: pin(before), HOST_TEST_COMPANION_RELATIVE: pin(original_test)},
                {NONCOMPILED_CONSUMER_RELATIVE: pin(leaf), HOST_TEST_COMPANION_RELATIVE: pin(companion)})

        def put(name: str, value: object) -> Pin:
            path = self.root / name
            path.write_text(json.dumps(value), encoding="utf-8")
            return pin(path)

        commands = put("old-commands.json", old_commands)
        scope = put("old-scope.json", {"compile_commands": commands})
        frozen = put("old-source.json", {"snapshot_native_base": str(native), "files": snapshot})
        baseline = put("baseline.json", {"machine_id": self.config.machine_id, "snapshot": frozen, "configured_scope": scope})
        borrowed = self.config.complete_build / "CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj"
        borrowed.parent.mkdir(parents=True)
        borrowed.write_bytes(b"owned retained identity; never executed")
        inputs = put("inputs.json", {"inputs": [pin(borrowed)], "new_object": pin(borrowed)})
        dependency_path = self.root / "original-dependencies.txt"
        dependency_path.write_text("\n".join(dependencies), encoding="utf-8")
        config = replace(self.config, baseline=baseline, incremental_inputs=inputs)
        producer = UngatedProducer(config)
        producer.native = native
        dormant: Compile | None = None
        if unbuilt_generated:
            missing = producer.build / "ck3_12003_initialization_context_stats_wire/production_regiment_serializer.cpp"
            self.assertFalse(missing.exists())
            dormant = Compile("unbuilt_generated_fixture", missing,
                              producer.build / "CMakeFiles/unbuilt_generated_fixture.dir/generated.cpp.obj",
                              (sys.executable, "/c", str(missing)))
            rows.append(dormant)
        added: Compile | None = None
        changed_paths = ["src/runtime.cpp"]
        if new_unit is not None:
            source = native / "src/added.cpp"
            source.write_text("int added_source;\n", encoding="utf-8")
            names.append(source.relative_to(self.root).as_posix())
            output_name = "CMakeFiles/" + new_unit + ".dir/src/added.cpp.obj"
            output = producer.build / output_name
            added = Compile(new_unit, source, output,
                            (sys.executable, "/c", str(source), "/Fo" + str(output)))
            rows.append(added)
            changed_paths.append("src/added.cpp")
            selections.append({"target": new_unit, "output": output_name, "source": "src/added.cpp",
                               "changed_dependencies": ["src/added.cpp"], "compiled": True,
                               "new_translation_unit": True})
        plan = {"machine_id": config.machine_id, "observed_at_utc": "owned fixture",
            "source_commit": config.source_commit, "baseline_qualification": baseline, "baseline_incremental_inputs": inputs,
            "original_dependencies": pin(dependency_path), "changed_native_paths": sorted(changed_paths),
            "production_selections": selections, "retained_link_inputs": [pin(borrowed)],
            "retained_incremental_object": pin(borrowed), "archive_copies": 0}
        reference = put("original-plan.json", plan)
        with patch("build_native_configured_successor.ROOT", self.root), \
             patch("build_native_configured_successor.git", return_value="\n".join(names)), \
             patch("build_native_configured_successor.subprocess.run", side_effect=AssertionError("Read-only replay cannot run Ninja")), \
             patch("build_native_configured_successor.verified_noncompiled_consumer_replay", return_value=proof), \
             patch.object(producer, "save", side_effect=AssertionError("Read-only replay cannot write")):
            if consumer:
                with self.assertRaisesRegex(ValueError, "Recomputed source/options/dependency"):
                    producer.plan(rows, existing_plan=reference)
            selected, actual_borrowed, original = producer.plan(rows, existing_plan=reference, noncompiled_replay=replay)
            self.assertEqual([row.target for row in selected],
                             ["xar_ck3_12002_runtime", *([new_unit] if new_unit is not None else [])])
            self.assertEqual(actual_borrowed, {"CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj": borrowed})
            self.assertEqual(original, reference)
            if added is not None:
                with self.assertRaisesRegex(ValueError, "target compiler options"):
                    producer.plan([*rows[:-1], replace(added, argv=(*added.argv, "/DUNREVIEWED=1"))],
                                  existing_plan=reference)
                with self.assertRaisesRegex(ValueError, "genuinely new"):
                    old_source = native / "src/runtime.cpp"
                    producer.plan([*rows[:-1], replace(added, source=old_source,
                        argv=(sys.executable, "/c", str(old_source), "/Fo" + str(added.output)))], existing_plan=reference)
                with self.assertRaisesRegex(ValueError, "Duplicate production output"):
                    producer.plan([*rows, added], existing_plan=reference)
                with self.assertRaisesRegex(ValueError, "Removing or renaming"):
                    removed = "runtime.cpp" if new_unit == "xar_ck3_12002_runtime" else "bridge.cpp"
                    producer.plan([row for row in rows if row.source.name != removed], existing_plan=reference)
                previous_dependencies = dependency_path.read_bytes()
                dependency_path.write_bytes(previous_dependencies + ("\n" + added.output.relative_to(producer.build).as_posix()
                    + ": #deps 1, deps mtime 1 (VALID)\n    " + str(added.source) + "\n").encode())
                plan["original_dependencies"] = pin(dependency_path)
                dependency_plan = put("new-unit-invented-old-dependency-plan.json", plan)
                with self.assertRaisesRegex(ValueError, "genuinely new"):
                    producer.plan(rows, existing_plan=dependency_plan)
                dependency_path.write_bytes(previous_dependencies)
                plan["original_dependencies"] = pin(dependency_path)
            if dormant is not None:
                self.assertFalse(dormant.source.exists())
                for required_target in ("wire_fixture", "xar_ck3_bridge"):
                    with self.subTest(required_target=required_target), self.assertRaises(FileNotFoundError):
                        producer.plan([*rows, replace(dormant, target=required_target)],
                                      existing_plan=reference, noncompiled_replay=replay)
                self.assertEqual(pin(Path(reference["path"])), reference)
            if consumer:
                with self.assertRaisesRegex(ValueError, "existing read-only"):
                    producer.plan(rows, noncompiled_replay=replay)
                with self.assertRaisesRegex(ValueError, "configured compiler command"):
                    producer.plan([*rows, Compile("fixture", leaf, self.root / "leaf.obj", (str(leaf),))],
                                  existing_plan=reference, noncompiled_replay=replay)
                with patch.object(producer, "closure", return_value={leaf}), \
                     self.assertRaisesRegex(ValueError, "current include closure"):
                    producer.plan(rows, existing_plan=reference, noncompiled_replay=replay)
                previous = dependency_path.read_bytes()
                dependency_path.write_bytes(previous + ("\n    " + str(leaf) + "\n").encode())
                plan["original_dependencies"] = pin(dependency_path)
                dependency_plan = put("dependency-plan.json", plan)
                with self.assertRaisesRegex(ValueError, "original compiler dependencies"):
                    producer.plan(rows, existing_plan=dependency_plan, noncompiled_replay=replay)
                dependency_path.write_bytes(previous)
                plan["original_dependencies"] = pin(dependency_path)
            selections[1]["compiled"] = False
            changed = put("changed-plan.json", plan)
            with self.assertRaisesRegex(ValueError, "Recomputed source/options/dependency"):
                producer.plan(rows, existing_plan=changed, noncompiled_replay=replay)

    def test_noncompiled_replay_revalidates_binding_git_blob_and_exact_pins(self) -> None:
        repo = self.root / "repo"
        leaf = repo / "ck3_autonomous_player/native_bridge" / NONCOMPILED_CONSUMER_RELATIVE
        leaf.parent.mkdir(parents=True)
        before = self.root / "original-consumer.py"
        before.write_bytes(b"# original bytes retain final newline\n")
        leaf.write_bytes(before.read_bytes())
        companion = leaf.parents[1] / "test_ck3_12002_mcp_live.py"
        original_test = self.root / "original-host-test.py"
        original_test.write_bytes(b"# original companion bytes\n")
        companion.write_bytes(original_test.read_bytes())
        for arguments in (("init", "-q"), ("add", "."), ("-c", "user.name=Fixture", "-c",
                          "user.email=fixture@example.invalid", "-c", "core.autocrlf=false", "commit", "-qm", "original")):
            subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
        config = replace(self.config, source_commit=commit)
        leaf.write_bytes(b"# new consumer bytes\n")
        companion.write_bytes(b"# new companion bytes\n")

        def put(name: str, value: object) -> Pin:
            path = self.root / name
            path.write_text(json.dumps(value), encoding="utf-8", newline="\n")
            return pin(path)

        snapshot = put("snapshot.json", {})
        qualification = put("qualification.json", {"snapshot": snapshot})
        delta = put("delta.json", {})
        binding = put("binding.json", {"schema": "ck3-native-same-root-host-and-wire-consumer-binding-v1",
            "qualified_native": qualification, "snapshot": snapshot, "shared_python_host_delta": delta})
        replay: NoncompiledConsumerReplay = {"before_blob": pin(before), "after": pin(leaf), "binding": binding}
        calls: list[str] = []
        valid_context = [True]
        include_companion = [False]

        def qualify(binding_path: Path | None, *, root: Path, runtime_commit: str, native_commit: str,
                    machine: str, qualified_native_ref: object, qualification: dict[str, object],
                    snapshot_ref: object, snapshot: dict[str, object],
                    native_shared_python_host_delta: Path | None = None) -> dict[str, object]:
            self.assertEqual((binding_path, root, runtime_commit, native_commit, machine),
                             (Path(binding["path"]), repo, commit, commit, config.machine_id))
            self.assertEqual((qualified_native_ref, snapshot_ref, native_shared_python_host_delta),
                             (pin(self.root / "qualification.json"), pin(self.root / "snapshot.json"), Path(delta["path"])))
            calls.append("full binding qualifier")
            if not valid_context[0]:
                return {}
            originals = {NONCOMPILED_CONSUMER_RELATIVE: replay["before_blob"]}
            currents = {NONCOMPILED_CONSUMER_RELATIVE: replay["after"]}
            if include_companion[0]:
                originals[HOST_TEST_COMPANION_RELATIVE] = pin(original_test)
                currents[HOST_TEST_COMPANION_RELATIVE] = pin(companion)
            return {"noncompiled_replay": replay, "original_research_blobs": originals,
                    "runtime_research_pins": currents}

        with patch("build_native_configured_successor.ROOT", repo), \
             patch("build_native_configured_successor.load_shared", return_value=SimpleNamespace(qualified_native_source_checkout=qualify)):
            decoded: object = json.loads(json.dumps(replay))
            self.assertEqual(verified_noncompiled_consumer_replay(config, decoded).replay, replay)
            self.assertEqual(calls, ["full binding qualifier"])
            include_companion[0] = True
            proof = verified_noncompiled_consumer_replay(config, decoded)
            self.assertEqual(set(proof.originals), {NONCOMPILED_CONSUMER_RELATIVE, HOST_TEST_COMPANION_RELATIVE})
            original_test.write_bytes(b"# forged original companion\n")
            with self.assertRaisesRegex(ValueError, "actual compile Git blob"):
                verified_noncompiled_consumer_replay(config, replay)
            original_test.write_bytes(b"# original companion bytes\n")
            for value in (None, {"before_blob": replay["before_blob"]}, {**replay, "unknown": True},
                          {**replay, "after": replay["before_blob"]},
                          {**replay, "before_blob": {**replay["before_blob"], "bytes": True}}):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    verified_noncompiled_consumer_replay(config, value)
            before.write_bytes(before.read_bytes().rstrip(b"\n"))
            altered = {**replay, "before_blob": pin(before)}
            with self.assertRaisesRegex(ValueError, "actual compile Git blob"):
                verified_noncompiled_consumer_replay(config, altered)
            before.write_bytes(b"# original bytes retain final newline\n")
            valid_context[0] = False
            with self.assertRaises(ValueError):
                verified_noncompiled_consumer_replay(config, replay)

    def v3_fixture(self) -> tuple[RetainedPlanFixture, UngatedProducer, list[Compile], Path]:
        fixture = self.retained_plan_fixture()
        prior = fixture.producer
        native = prior.native
        fixture.documents["source"]["snapshot_native_base"] = str(native)
        fixture.documents["incremental"].update(production_compiles=[], changed_runtime_archive=None,
            changed_runtime_archive_execution=None)
        objects = obj(fixture.documents["plan"])["retained_link_inputs"]
        response = self.root/"actual-linked-predecessor.rsp"
        references = [parse_pin(raw) for raw in arr(objects)]
        response.write_text(subprocess.list2cmdline([str(ref["path"]) for ref in references]),encoding="utf-8")
        fixture.documents["execution"].update(response_files=[pin(response)],argv=["authored-linker","@"+str(response)])
        fixture.refresh()
        predecessor = pin(fixture.paths["qualification"])
        workspace = self.root/"development"
        development = workspace/"native"; development.mkdir(parents=True)
        (native/"src/bridge.cpp").write_text("#include MACRO_HEADER\nint changed_bridge;\n",encoding="utf-8")
        for name in fixture.names:
            relative_name = name.removeprefix("ck3_autonomous_player/native_bridge/")
            destination = development/relative_name; destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes((native/relative_name).read_bytes())
        config = replace(prior.config,schema="ck3-configured-native-successor-v3",baseline=predecessor,
            predecessor_qualification=predecessor,retained_dependency_evidence=None,
            native_source_dir=development,development_build_dir=workspace/"build",output=workspace/"attempt-a01")
        producer = UngatedProducer(config);config.output.mkdir()
        rows = [Compile(row.target,development/row.source.relative_to(native),
            producer.build/row.output.relative_to(prior.build),tuple(value.replace(str(native),str(development))
                .replace(str(prior.build),str(producer.build)) for value in row.argv)) for row in fixture.rows]
        return fixture,producer,rows,native.parent.parent

    def test_v3_json_contract_retains_independent_development_paths_and_rejects_mixed_authorities(self) -> None:
        _,producer,_,_ = self.v3_fixture()
        value = config_json(producer.config)
        self.assertEqual(parse_config(json.loads(json.dumps(value))),producer.config)
        for field in ("native_source_dir","development_build_dir","predecessor_qualification"):
            missing = dict(value);del missing[field]
            with self.subTest(missing=field),self.assertRaises(ValueError):parse_config(missing)
        for field,bad in (("compiled_seed",reference("seed.json")),("retained_dependency_evidence",{}),
                ("native_source_dir","relative-native"),("development_build_dir",str(producer.native))):
            with self.subTest(field=field),self.assertRaises(ValueError):parse_config({**value,field:bad})

    def test_v3_actual_predecessor_producer_readonly_consumer_replay_reuses_all_objects_and_archives(self) -> None:
        fixture,producer,rows,repository = self.v3_fixture()
        with patch("build_native_configured_successor.ROOT",repository),patch("build_native_configured_successor.git",fixture.git_output):
            selected,borrowed,plan = producer.plan(rows)
            self.assertEqual({row.target for row in selected},{"xar_ck3_bridge","xar_ck3_12002_runtime"})
            self.assertEqual(len(borrowed),1)
            before = sorted(str(path) for path in producer.config.output.rglob("*"))
            replay = producer.plan(rows,existing_plan=plan)
            self.assertEqual(replay,(selected,borrowed,plan))
            self.assertEqual(before,sorted(str(path) for path in producer.config.output.rglob("*")))
            record = read(Path(plan["path"]))
            self.assertEqual(record["predecessor_qualification"],producer.config.predecessor_qualification)
            self.assertEqual(len(arr(record["predecessor_libraries"])),2)
            self.assertEqual(record["archive_copies"],0)

    def test_v3_actual_producer_rejects_link_response_object_source_and_original_wait_drift(self) -> None:
        fixture,producer,rows,repository = self.v3_fixture()
        with patch("build_native_configured_successor.ROOT",repository),patch("build_native_configured_successor.git",fixture.git_output):
            _,_,plan = producer.plan(rows)
            paths = [self.root/"actual-linked-predecessor.rsp",
                Path(parse_pin(arr(fixture.documents["plan"]["retained_link_inputs"])[0])["path"]),
                producer.native/"src/bridge.cpp"]
            for path in paths:
                original = path.read_bytes();path.write_bytes(original+b" drift")
                with self.subTest(path=path),self.assertRaises(ValueError):producer.plan(rows,existing_plan=plan)
                path.write_bytes(original)
            extra = producer.native/"stale-deleted-header.hpp";extra.write_bytes(b"stale previous-attempt header")
            with self.assertRaisesRegex(ValueError,"stale or untracked"):producer.plan(rows,existing_plan=plan)
            extra.unlink()
            fixture.documents["execution"]["original_wait_returncode"] = True
            fixture.refresh()
            producer.config = replace(producer.config,predecessor_qualification=pin(fixture.paths["qualification"]))
            with self.assertRaises(ValueError):producer.plan(rows,existing_plan=plan)

    def test_v3_run_refuses_unqualified_predecessor_before_any_compile_or_link(self) -> None:
        fixture,producer,rows,repository = self.v3_fixture()
        fixture.documents["qualification"]["actual_live_business_qualified"] = True
        fixture.refresh()
        producer.config = replace(producer.config,predecessor_qualification=pin(fixture.paths["qualification"]),
            baseline=pin(fixture.paths["qualification"]))
        with patch("build_native_configured_successor.ROOT",repository),patch("build_native_configured_successor.git",fixture.git_output),\
                patch.object(producer,"initialize"),patch.object(producer,"configure"),patch.object(producer,"commands",return_value=rows),\
                patch.object(producer,"compile") as compile_call,patch.object(producer,"link") as link_call:
            with self.assertRaisesRegex(ValueError,"predecessor identity"):producer.run()
            compile_call.assert_not_called();link_call.assert_not_called()

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
