"""Exercise process-local MSVC setup and a real incremental native build."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "tools/run_native_msvc.py"
OUTPUT = Path(r"Z:\ck3_mod_rewrite\artifacts\offline-nonwar-2026-10-01\native-msvc-wrapper-tests")


def load_helper():
    spec = importlib.util.spec_from_file_location("run_native_msvc_for_test", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load MSVC build helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeMsvcBuildTests(unittest.TestCase):
    def test_temporary_environment_is_process_local(self) -> None:
        helper = load_helper()
        OUTPUT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=OUTPUT, prefix="environment-") as temporary:
            with mock.patch.dict(os.environ, {"TEMP": "existing-parent-temp", "TMP": "existing-parent-tmp"}):
                child = helper.child_environment(Path(temporary))
                self.assertEqual(os.environ["TEMP"], "existing-parent-temp")
                self.assertEqual(os.environ["TMP"], "existing-parent-tmp")
            for key in ("TEMP", "TMP", "PYTHONPYCACHEPREFIX", "XDG_CACHE_HOME", "CCACHE_DIR", "SCCACHE_DIR"):
                self.assertTrue(Path(child[key]).resolve().is_relative_to(Path(temporary).resolve()))

    @unittest.skipUnless(os.name == "nt", "MSVC integration requires Windows")
    def test_spaced_arguments_and_incremental_header_dependencies(self) -> None:
        source = OUTPUT / "tiny source"
        build = OUTPUT / "tiny build"
        source.mkdir(parents=True, exist_ok=True)
        source.joinpath("CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.25)\n"
            "project(xar_msvc_wrapper_fixture LANGUAGES CXX)\n"
            "add_executable(tiny_fixture main.cpp)\n"
            "target_compile_features(tiny_fixture PRIVATE cxx_std_20)\n",
            encoding="utf-8",
        )
        source.joinpath("main.cpp").write_text(
            '#include <iostream>\n#include "value.hpp"\nint main() { std::cout << fixture_value; }\n',
            encoding="utf-8",
        )
        header = source / "value.hpp"
        header.write_text("inline constexpr int fixture_value = 7;\n", encoding="utf-8")
        base = [sys.executable, str(HELPER), "--source-dir", str(source), "--build-dir", str(build),
                "--jobs", "1", "--target", "tiny_fixture"]
        initial = subprocess.run(base + ["--cmake-define", "FIXTURE_LABEL=label with spaces"],
                                 capture_output=True, check=False)
        initial_log = OUTPUT / "initial.log"
        initial_log.write_bytes(initial.stdout + initial.stderr)
        self.assertEqual(initial.returncode, 0, initial_log.read_text(encoding="utf-8", errors="replace"))
        program = build / "tiny_fixture.exe"
        self.assertEqual(subprocess.check_output([str(program)], cwd=build), b"7")
        cache = (build / "CMakeCache.txt").read_text(encoding="utf-8")
        self.assertIn("FIXTURE_LABEL:UNINITIALIZED=label with spaces", cache)
        report = json.loads((build / "native-msvc-result.json").read_text(encoding="utf-8"))
        self.assertEqual(report["targets"], ["tiny_fixture"])
        self.assertFalse(report["local_ck3_contacted"])

        header.write_text("inline constexpr int fixture_value = 8;\n", encoding="utf-8")
        incremental = subprocess.run(base + ["--build"], capture_output=True, check=False)
        incremental_log = OUTPUT / "incremental.log"
        incremental_log.write_bytes(incremental.stdout + incremental.stderr)
        self.assertEqual(incremental.returncode, 0,
                         incremental_log.read_text(encoding="utf-8", errors="replace"))
        self.assertEqual(subprocess.check_output([str(program)], cwd=build), b"8")
        report = json.loads((build / "native-msvc-result.json").read_text(encoding="utf-8"))
        self.assertFalse(report["configured"])
        self.assertTrue(report["built"])
        OUTPUT.joinpath("assessment.json").write_text(json.dumps({
            "status": "GREEN", "local_ck3_contacted": False,
            "spaced_source_and_build_paths": True, "spaced_define_value_preserved": True,
            "initial_fixture_output": "7", "incremental_header_rebuild_output": "8",
            "targets": ["tiny_fixture"], "parent_temporary_environment_unchanged": True,
            "initial_log": str(initial_log), "incremental_log": str(incremental_log),
            "build_report": str(build / "native-msvc-result.json"),
        }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    unittest.main()
