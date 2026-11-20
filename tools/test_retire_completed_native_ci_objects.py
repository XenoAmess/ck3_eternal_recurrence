"""Focused filesystem checks for completed CI native-object retirement."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from retire_completed_native_ci_objects import BUILD_NAMES, retire

class CompletedNativeObjectsTest(unittest.TestCase):
    def fixture(self, base: Path) -> tuple[Path, Path]:
        repo = base / "repo"
        native = repo / "ck3_autonomous_player" / "native_bridge"
        native.mkdir(parents=True)
        runner = base / "runner"
        runner.mkdir()
        for name in BUILD_NAMES:
            build = runner / name
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

    def test_retires_only_completed_objects_and_preserves_wire_executables_and_logs(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, runner = self.fixture(Path(temporary))
            retained = {path: path.read_bytes() for path in runner.rglob("*")
                        if path.is_file() and path.suffix not in (".obj", ".pdb")}
            report = retire(repo, runner)
            self.assertEqual(8, report["removed_files"])
            self.assertGreater(report["removed_bootstrap_inventory_charge_bytes"], 8 * 65536)
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
            self.assertEqual(8, len(list(runner.rglob("*.obj"))) + len(list(runner.rglob("*.pdb"))))

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
            self.assertEqual(8, len(list(runner.rglob("*.obj"))) + len(list(runner.rglob("*.pdb"))))

if __name__ == "__main__":
    unittest.main()
