"""Owned tiny Windows processes/files + parser tests, never a C++ qualification."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import unittest

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("build_native30_wholeclean_20261019.py")
spec = importlib.util.spec_from_file_location("native30_producer", SCRIPT)
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)
OWNED = REPO / ".codex-tmp/native30-producer-owned-test01"
OBS = {"scope": "OWNED_PYTHON_TINY_FILES_AND_SYNTHETIC_PARSER_ONLY", "processes": [],
       "CPP_compile_or_run": 0, "Game_OBS_MCP": 0, "peak_eof": 0, "peak_allocation": 0}

def check(reserve=0):
    data = producer.inventory(OWNED, API)
    OBS["peak_eof"] = max(OBS["peak_eof"], data["eof"])
    OBS["peak_allocation"] = max(OBS["peak_allocation"], data["allocation"])
    if data["eof"] > 8192 or data["allocation"] > 32768:
        raise RuntimeError("tiny test scratch cap")
    return data

class Mechanics(unittest.TestCase):
    def setUp(self):
        self.case = OWNED / self._testMethodName
        self.case.mkdir()
    def tearDown(self):
        check()
        require_owned(self.case)
        # Only this create-only test case root and exact discovered own leaves.
        for directory, dirs, files in os.walk(self.case, topdown=False, followlinks=False):
            for name in files:
                p = Path(directory) / name
                require_owned(p)
                until = time.monotonic() + 1
                while True:
                    try:
                        p.unlink()
                        break
                    except PermissionError as error:
                        if error.winerror != 32 or time.monotonic() >= until: raise
                        time.sleep(.02) # Own tiny log only; no process/production retry.
            for name in dirs:
                p = Path(directory) / name
                require_owned(p)
                p.rmdir()
        self.case.rmdir()
    def test_source_parses_and_bad_flags(self):
        ast.parse(SCRIPT.read_bytes())
        for flag in ("/MP", "/MP4", "/Zi", "/Z7", "/GL", "/DEBUG:FULL", "/LTCG"):
            self.assertIsNotNone(producer.BAD_FLAGS.search("/O2 " + flag))
        self.assertIsNone(producer.BAD_FLAGS.search("/O2 /Ob2 /MD /UNDEBUG"))
    def test_actual_file_standard_info(self):
        p = self.case / "own.txt"
        p.write_bytes(b"bounded own file\n")
        eof, allocated = API.sizes(p)
        self.assertEqual(eof, 17)
        self.assertGreaterEqual(allocated, 0)
        OBS["FileStandardInfo"] = {"eof": eof, "allocation": allocated}
    def test_actual_owned_normal_process(self):
        marker = self.case / "normal.bin"
        command = [sys.executable, "-B", "-c",
                   "from pathlib import Path; Path(" + repr(str(marker)) + ").write_bytes(b'x'*32)"]
        row = producer.run_owned(command, self.case, dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                                 self.case / "child.log", check, timeout=10, reserve=0)
        self.assertEqual(marker.stat().st_size, 32)
        self.assertEqual(row["owned_active_after"], 0)
        OBS["processes"].append(row)
    def test_actual_guard_stops_only_owned_job(self):
        marker = self.case / "guard.bin"
        command = [sys.executable, "-B", "-c", "from pathlib import Path; import time; Path(" +
                   repr(str(marker)) + ").write_bytes(b'x'*4096); time.sleep(30)"]
        def guard(reserve=0):
            check()
            if marker.exists(): raise RuntimeError("expected owned test guard")
        started = time.monotonic()
        with self.assertRaisesRegex(RuntimeError, "expected owned test guard"):
            producer.run_owned(command, self.case, dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                               self.case / "guard.log", guard, timeout=10, reserve=0)
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual(marker.stat().st_size, 4096)
        OBS["guard_stop"] = "real owned Job stop+active0 readback required by run_owned; no PID enumeration"
    def make_graph(self, flags="/O2 /UNDEBUG", include=None):
        source, build = self.case / "source", self.case / "build"
        source.mkdir()
        reply = build / ".cmake/api/v1/reply"
        reply.mkdir(parents=True)
        (source / "test.cpp").write_text("// metadata fixture; never compiled\n")
        name = "xar_ck3_camera_tracking_v1_test"
        def put(filename, body):
            (reply / filename).write_text(json.dumps(body))
        put("index-a.json", {"objects": [{"kind": "codemodel", "version": {"major": 2}, "jsonFile": "model.json"}]})
        put("model.json", {"paths": {"source": str(source), "build": str(build)},
            "configurations": [{"name": "Release", "targets": [{"name": name, "id": "test", "jsonFile": "target.json"}]}]})
        put("target.json", {"name": name, "id": "test", "type": "EXECUTABLE",
            "sources": [{"path": str(source / "test.cpp"), "compileGroupIndex": 0}],
            "compileGroups": [{"defines": [{"define": "EXPECTED=1"}], "includes":
                [] if include is None else [{"path": include}],
                "compileCommandFragments": [{"fragment": flags}]}],
            "artifacts": [{"path": "metadata-only.exe"}]})
        (build / "compile_commands.json").write_text(json.dumps([{"file": str(source / "test.cpp"),
            "output": "CMakeFiles/" + name + ".dir/test.cpp.obj",
            "directory": str(build), "command": "cl " + flags + " /c " + str(source / "test.cpp")}]))
        return build, source, [name], {name: ["EXPECTED=1"]}, []
    def test_synthetic_graph_accepts_finite_fixture(self):
        result = producer.graph(*self.make_graph())
        self.assertEqual(result["source_count"], 1)
        self.assertEqual(len(result["selected_compile_rows"]), 1)
    def test_synthetic_graph_rejects_mp(self):
        with self.assertRaisesRegex(RuntimeError, "forbidden compiler flag"):
            producer.graph(*self.make_graph(flags="/O2 /UNDEBUG /MP4"))
    def test_synthetic_graph_rejects_external_headers(self):
        with self.assertRaisesRegex(RuntimeError, "external include"):
            producer.graph(*self.make_graph(include="C:/not-owned/old-native29"))
    def test_synthetic_graph_requires_active_assertions(self):
        with self.assertRaisesRegex(RuntimeError, "assertions disabled"):
            producer.graph(*self.make_graph(flags="/O2 /DNDEBUG"))
    def test_synthetic_always_on_checker_not_assert_fixture(self):
        self.assertEqual(producer.graph(*self.make_graph(flags="/O2 /DNDEBUG"),
                         assertion_targets=[])["source_count"], 1)
    def test_synthetic_graph_requires_source_macro(self):
        values = self.make_graph()
        with self.assertRaisesRegex(RuntimeError, "required source macro missing"):
            producer.graph(*values, source_defines={values[2][0] + ":test.cpp": ["MISSING=1"]})
    def test_synthetic_graph_ignores_unselected_same_file(self):
        values = self.make_graph()
        commands = values[0] / "compile_commands.json"
        rows = json.loads(commands.read_text())
        rows.append(dict(rows[0], output="CMakeFiles/unselected.dir/test.cpp.obj", command="cl /MP4"))
        commands.write_text(json.dumps(rows))
        self.assertEqual(len(producer.graph(*values)["selected_compile_rows"]), 1)

def require_owned(path):
    producer.require(path.resolve().is_relative_to(OWNED.resolve()) and
                     not (path.lstat().st_file_attributes & 0x400), "test ownership/reparse guard")

def main():
    global API
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    producer.require(os.name == "nt" and not OWNED.exists() and not args.receipt.exists(),
                     "Windows create-only test roots/receipt")
    # Source/test/plan/proofs +8KiB transient logical fit the one64KiB scope.
    planned = [SCRIPT, Path(__file__), REPO / "docs/ck3-native-ai/evidence/native30-wholeclean-producer-plan-2026-10-19.json"]
    prior = list((REPO / "docs/ck3-native-ai/evidence").glob("native30-wholeclean-producer-mechanics-2026-10-19-*.json"))
    existing = sum(p.stat().st_size for p in planned + prior if p.exists())
    producer.require(existing + 2048 + 8192 <= 65536, "64KiB source/test/proof/scratch scope")
    API = producer.FileAPI()
    OWNED.mkdir(parents=True, exist_ok=False)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Mechanics))
    final = check()
    OBS.update(machine_id=producer.machine(), utc=datetime.now(timezone.utc).isoformat(),
               tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
               producer=producer.pin(SCRIPT), test_source=producer.pin(Path(__file__)),
               final_scratch_eof=final["eof"], final_scratch_allocation=final["allocation"],
               future_writes=0, qualified="PRODUCER_MECHANICS_ONLY_NOT_CPP")
    OWNED.rmdir()
    OBS["owned_root_absent"] = not OWNED.exists()
    producer.write(args.receipt, OBS)
    print(json.dumps({"receipt": producer.pin(args.receipt), "status": "PASS" if result.wasSuccessful() else "FAIL"}))
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__": raise SystemExit(main())
