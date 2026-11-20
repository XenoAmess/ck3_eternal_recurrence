"""Focused filesystem checks for completed CI native-object retirement."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from retire_completed_native_ci_objects import ARMY_BUILD_NAME, ARMY_INPUTS, ARMY_UNITS, BUILD_NAMES, retire

class CompletedNativeObjectsTest(unittest.TestCase):
    expected_objects = 2 * (len(BUILD_NAMES) - 1) + len(ARMY_UNITS)

    def fixture(self, base: Path) -> tuple[Path, Path]:
        repo = base / "repo"
        native = repo / "ck3_autonomous_player" / "native_bridge"
        native.mkdir(parents=True)
        runner = base / "runner"
        runner.mkdir()
        for name in BUILD_NAMES:
            build = runner / name
            if name == ARMY_BUILD_NAME:
                self.army_fixture(build, native, base)
                continue
            (build / "CMakeFiles" / "target.dir").mkdir(parents=True)
            (build / "wire").mkdir()
            (build / "Testing" / "Temporary").mkdir(parents=True)
            (build / "CMakeCache.txt").write_text(
                "CMAKE_HOME_DIRECTORY:INTERNAL=" + str(native.resolve()) + "\n"
                "CMAKE_CACHEFILE_DIR:INTERNAL=" + str(build.resolve()) + "\n", encoding="utf-8")
            (build / "CMakeFiles" / "target.dir" / "one.obj").write_bytes(b"actual object")
            (build / "CMakeFiles" / "target.dir" / "one.pdb").write_bytes(b"actual debug data")
            (build / "wire" / "lobby.json").write_bytes(b"actual preserved wire")
            (build / "target.exe").write_bytes(b"actual executable")
            (build / "CMakeFiles" / "configure.log").write_bytes(b"actual configure log")
            (build / "Testing" / "Temporary" / "LastTest.log").write_bytes(b"actual CTest log")
        return repo, runner

    def army_fixture(self, build: Path, native: Path, base: Path) -> None:
        # Filesystem protocol stimulus, not a claimed real compiler/test execution.
        build.mkdir()
        inputs = {}
        for relative in ARMY_INPUTS:
            source = native / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(("finite source " + relative).encode("utf-8"))
            inputs[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
        executable = build / "xar_ck3_12002_army_test.exe"
        executable.write_bytes(b"retained fixture executable bytes")
        for relative in ARMY_UNITS:
            (build / (Path(relative).stem + ".obj")).write_bytes(b"completed command object")
        compiler = [str((base / 'compiler' / 'cl.exe').resolve()), "/nologo", "/std:c++20", "/O2", "/MD", "/W4",
                    "/permissive-", "/EHsc", "/utf-8", "/UNDEBUG", "/DNOMINMAX", f"/I{native / 'include'}",
                    *(str(native / name) for name in ARMY_UNITS), f"/Fe{executable}"]
        steps = [{"name": "msvc-environment", "argv": ["environment setup fixture"], "exit_code": 0}]
        for name, argv in (("compile", compiler), ("army-fixtures", [str(executable)])):
            stdout, stderr = build / (name + ".stdout.bin"), build / (name + ".stderr.bin")
            stdout.write_bytes(b"original finite command log"); stderr.write_bytes(b"")
            steps.append({"name": name, "argv": argv, "exit_code": 0, "stdout": str(stdout), "stderr": str(stderr)})
        report = {"schema": "xar.native.army-reader-ci.v1", "status": "passed", "build_status": "build_succeeded",
                  "build_dir": str(build), "steps": steps, "local_ck3_contacted": False,
                  "private_feature_definitions": [], "inputs": inputs,
                  "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()}
        (build / "army-reader-ci-result.json").write_text(json.dumps(report), encoding="utf-8")

    def assert_all_objects_retained(self, runner: Path) -> None:
        self.assertEqual(self.expected_objects,
                         len(list(runner.rglob("*.obj"))) + len(list(runner.rglob("*.pdb"))))

    def test_retires_only_completed_objects_and_preserves_wire_executables_and_logs(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, runner = self.fixture(Path(temporary))
            army = runner / ARMY_BUILD_NAME
            self.assertFalse((army / "CMakeCache.txt").exists())
            self.assertFalse((army / "CMakeFiles").exists())
            retained = {path: path.read_bytes() for path in runner.rglob("*")
                        if path.is_file() and path.suffix not in (".obj", ".pdb")}
            report = retire(repo, runner)
            self.assertEqual(self.expected_objects, report["removed_files"])
            self.assertGreater(report["removed_bootstrap_inventory_charge_bytes"], self.expected_objects * 65536)
            self.assertFalse(report["quota_or_admission_changed"])
            self.assertFalse(list(runner.rglob("*.obj")))
            self.assertFalse(list(runner.rglob("*.pdb")))
            self.assertEqual(retained, {path: path.read_bytes() for path in retained})

    def test_foreign_source_is_rejected_before_any_object_is_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, runner = self.fixture(Path(temporary))
            cache = runner / BUILD_NAMES[-1] / "CMakeCache.txt"
            cache.write_text(cache.read_text(encoding="utf-8").replace(
                str((repo / "ck3_autonomous_player" / "native_bridge").resolve()), str(runner.resolve())),
                encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "foreign native CMake source"):
                retire(repo, runner)
            self.assert_all_objects_retained(runner)

    def test_directory_link_cannot_retire_an_outside_object(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo, runner = self.fixture(base)
            outside = base / "outside"
            outside.mkdir()
            survivor = outside / "outside.obj"
            survivor.write_bytes(b"outside object must survive")
            link = runner / BUILD_NAMES[-1] / "CMakeFiles" / "outside"
            if os.name == "nt":
                subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                link.symlink_to(outside, target_is_directory=True)
            try:
                with self.assertRaisesRegex(ValueError, "directory link rejected"):
                    retire(repo, runner)
                self.assertEqual(b"outside object must survive", survivor.read_bytes())
            finally:
                if os.name == "nt":
                    link.rmdir()
                else:
                    link.unlink()
            self.assert_all_objects_retained(runner)

    def test_missing_army_completion_report_rejects_before_any_retirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, runner = self.fixture(Path(temporary))
            (runner / ARMY_BUILD_NAME / "army-reader-ci-result.json").unlink()
            with self.assertRaisesRegex(ValueError, "completed native evidence"):
                retire(repo, runner)
            self.assert_all_objects_retained(runner)

    def test_failed_army_compile_or_fixture_never_becomes_completed(self):
        for step in (1, 2):
            with self.subTest(step=step), tempfile.TemporaryDirectory() as temporary:
                repo, runner = self.fixture(Path(temporary))
                path = runner / ARMY_BUILD_NAME / "army-reader-ci-result.json"
                report = json.loads(path.read_text(encoding="utf-8"))
                report["steps"][step]["exit_code"] = 1
                path.write_text(json.dumps(report), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "compile and fixture exits"):
                    retire(repo, runner)
                self.assert_all_objects_retained(runner)

    def test_changed_army_source_or_executable_rejects_all_roles(self):
        for kind in ("source", "executable"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                repo, runner = self.fixture(Path(temporary))
                target = ((repo / "ck3_autonomous_player/native_bridge" / ARMY_INPUTS[0]) if kind == "source"
                          else runner / ARMY_BUILD_NAME / "xar_ck3_12002_army_test.exe")
                target.write_bytes(b"changed after completed report")
                with self.assertRaisesRegex(ValueError, "completed army (source|executable) differs"):
                    retire(repo, runner)
                self.assert_all_objects_retained(runner)

    def test_army_compiler_cannot_hide_other_output_or_feature_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, runner = self.fixture(Path(temporary))
            path = runner / ARMY_BUILD_NAME / "army-reader-ci-result.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["steps"][1]["argv"].insert(1, "/DUNREVIEWED_FEATURE=1")
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "compiler and fixture command"):
                retire(repo, runner)
            self.assert_all_objects_retained(runner)

    def test_unexpected_army_root_object_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, runner = self.fixture(Path(temporary))
            extra = runner / ARMY_BUILD_NAME / "other-owner.obj"
            extra.write_bytes(b"unattributed object")
            with self.assertRaisesRegex(ValueError, "unexpected army command intermediate"):
                retire(repo, runner)
            self.assertTrue(extra.is_file())
            self.assertEqual(self.expected_objects + 1, len(list(runner.rglob("*.obj"))) + len(list(runner.rglob("*.pdb"))))

    def test_missing_original_army_object_does_not_allow_partial_retirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, runner = self.fixture(Path(temporary))
            (runner / ARMY_BUILD_NAME / (Path(ARMY_UNITS[0]).stem + ".obj")).unlink()
            with self.assertRaisesRegex(ValueError, "complete original army object inventory"):
                retire(repo, runner)
            self.assertEqual(self.expected_objects - 1, len(list(runner.rglob("*.obj"))) + len(list(runner.rglob("*.pdb"))))

if __name__ == "__main__":
    unittest.main()
