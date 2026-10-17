"""Mock-only checks for independent incremental-build evidence paths."""
from __future__ import annotations

from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest import mock


HELPER = Path(__file__).with_name("run_native_msvc.py")
REPORT = "native-msvc-result.json"
LOGS = ("msvc-configure.log", "msvc-build.log")


def load_helper():
    registration = ModuleType("register_project_exe_exclusions")
    for name in ("after_successful_build", "has_codemodel_reply", "opted_in", "request_codemodel", "validate_source"):
        setattr(registration, name, mock.Mock(name=name))
    spec = importlib.util.spec_from_file_location("native_msvc_evidence_candidate", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the candidate helper")
    module = importlib.util.module_from_spec(spec)
    original_path = sys.path[:]
    try:
        with mock.patch.dict(sys.modules, {"register_project_exe_exclusions": registration}):
            spec.loader.exec_module(module)
    finally:
        sys.path[:] = original_path
    return module


class NativeMsvcEvidenceDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        self.directory = tempfile.TemporaryDirectory(prefix="native-msvc-evidence-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source with spaces"
        self.source.mkdir()
        (self.source / "CMakeLists.txt").write_text("# mock-only fixture\n", encoding="utf-8")
        self.build = self.root / "build with spaces"
        self.build.mkdir()
        self.old = {}
        for name in (*LOGS, REPORT):
            self.old[name] = ("frozen old " + name + "\n").encode("utf-8")
            (self.build / name).write_bytes(self.old[name])
        self.calls = []

    def invoke(self, evidence=None, failure=None, extra=()):
        argv = ["--source-dir", str(self.source), "--build-dir", str(self.build),
                "--jobs", "2", "--target", "mock_target", *extra]
        if evidence is not None:
            argv.extend(["--evidence-dir", str(evidence)])
        args = self.helper.parser().parse_args(argv)

        def run_logged(command, log, environment, cwd):
            stage = "build" if "--build" in command else "configure"
            self.calls.append((stage, log, cwd, dict(environment)))
            log.write_bytes(("mock " + stage + "\n").encode("utf-8"))
            if failure == stage:
                raise subprocess.CalledProcessError(23, command)

        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "pycache_prefix", sys.pycache_prefix))
            stack.enter_context(mock.patch.object(self.helper, "opted_in", return_value=False))
            stack.enter_context(mock.patch.object(self.helper, "visual_studio_installation", return_value=self.root / "mock VS"))
            stack.enter_context(mock.patch.object(self.helper, "initialize_msvc", side_effect=lambda installation, build, environment: (
                environment, {"vcvars64": "mock-vcvars", "cmake": "mock-cmake", "ninja": "mock-ninja", "cl": "mock-cl"})))
            stack.enter_context(mock.patch.object(self.helper, "run_logged", side_effect=run_logged))
            stack.enter_context(mock.patch.object(self.helper, "repair_dependency_prefix", return_value="mock unchanged"))
            self.after_build = stack.enter_context(mock.patch.object(self.helper, "after_successful_build", return_value={"status": "disabled"}))
            stack.enter_context(mock.patch.object(self.helper.subprocess, "Popen", side_effect=AssertionError("A test must never start a native process")))
            stack.enter_context(mock.patch.object(self.helper.subprocess, "run", side_effect=AssertionError("A test must never run a native command")))
            return self.helper.run(args)

    def assert_old_build_evidence_preserved(self):
        for name, value in self.old.items():
            self.assertEqual((self.build / name).read_bytes(), value, name)

    def assert_build_environment_unchanged(self):
        for stage, log, cwd, environment in self.calls:
            self.assertEqual(cwd, self.build.resolve(), stage)
            self.assertEqual(Path(environment["TEMP"]), self.build.resolve() / ".msvc-temp")
            self.assertEqual(Path(environment["PYTHONPYCACHEPREFIX"]), self.build.resolve() / ".python-cache")

    def test_optional_parser_argument_defaults_to_none_and_preserves_spaced_path(self):
        parser = self.helper.parser()
        self.assertIsNone(parser.parse_args(["--build-dir", str(self.build)]).evidence_dir)
        evidence = self.root / "separate evidence with spaces"
        self.assertEqual(parser.parse_args(["--build-dir", str(self.build), "--evidence-dir", str(evidence)]).evidence_dir, evidence)

    def test_default_success_keeps_existing_destinations_and_report_keys(self):
        result = self.invoke()
        self.assertEqual(result["status"], "built")
        self.assertEqual({call[1] for call in self.calls}, {self.build / name for name in LOGS})
        self.assertEqual(json.loads((self.build / REPORT).read_text(encoding="utf-8")), result)
        self.assertEqual(set(result), {"schema", "source_dir", "build_dir", "configuration", "jobs", "targets", "tools",
            "local_ck3_contacted", "temporary_dir", "python_cache", "configured", "built", "dependency_prefix_mode",
            "status", "build_succeeded", "defender_exclusions"})
        self.assertEqual(result["schema"], "xar.native.msvc-build.v1")
        self.assert_build_environment_unchanged()

    def test_redirect_success_preserves_all_three_old_paths(self):
        evidence = self.root / "independent evidence with spaces" / "nested"
        result = self.invoke(evidence)
        self.assertEqual(result["status"], "built")
        self.assertEqual({call[1] for call in self.calls}, {evidence / name for name in LOGS})
        self.assertEqual(json.loads((evidence / REPORT).read_text(encoding="utf-8")), result)
        self.assert_old_build_evidence_preserved()
        self.assert_build_environment_unchanged()
        self.after_build.assert_called_once()

    def test_redirect_configure_failure_records_failure_in_new_directory(self):
        evidence = self.root / "configure failure evidence"
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(evidence, failure="configure")
        result = json.loads((evidence / REPORT).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "failed")
        self.assertIn("23", result["error"])
        self.assertTrue((evidence / LOGS[0]).is_file())
        self.assertFalse((evidence / LOGS[1]).exists())
        self.assert_old_build_evidence_preserved()
        self.after_build.assert_not_called()

    def test_redirect_build_failure_records_both_new_logs_and_failure_report(self):
        evidence = self.root / "build failure evidence"
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(evidence, failure="build")
        result = json.loads((evidence / REPORT).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["dependency_prefix_mode"], "mock unchanged")
        self.assertTrue(all((evidence / name).is_file() for name in LOGS))
        self.assert_old_build_evidence_preserved()
        self.after_build.assert_not_called()

    def test_default_build_failure_retains_existing_failure_report_location(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(failure="build")
        result = json.loads((self.build / REPORT).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "failed")
        self.assertTrue(all((self.build / name).is_file() for name in LOGS))

    def test_redirect_build_only_does_not_write_configure_log(self):
        evidence = self.root / "build only evidence"
        result = self.invoke(evidence, extra=("--build",))
        self.assertFalse(result["configured"])
        self.assertEqual([call[0] for call in self.calls], ["build"])
        self.assertFalse((evidence / LOGS[0]).exists())
        self.assert_old_build_evidence_preserved()


if __name__ == "__main__":
    unittest.main(verbosity=2)
