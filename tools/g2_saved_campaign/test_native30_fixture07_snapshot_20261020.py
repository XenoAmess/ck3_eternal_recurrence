"""Finite synthetic contract checks; no Ninja/CMake/compiler/Game execution."""
import ast
import io
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent

def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

contract = module("native30_ninja_snapshot_contract_20261020")
environment = module("native30_capture_msvc_environment_20261020")
producer = module("qualify_native30_fixture07_20261020")

class SnapshotContract(unittest.TestCase):
    def guard(self, rows, reserve=0, hard=1610612736, free=10**12):
        data = {"files": rows, "eof":sum(r["eof"] for r in rows),
                "allocation":sum(r["allocation"] for r in rows), "raced":0}
        base = SimpleNamespace(MIB=1024**2, inventory=lambda *a:data, utc=lambda:"synthetic")
        card = {"deadline_utc":"2099-01-01T00:00:00Z", "hard_bytes":hard,"minimum_free_bytes":2048}
        guard = producer.SnapshotGuard(base,Path("C:/owned-test"),card,None)
        with patch.object(producer.shutil,"disk_usage",return_value=SimpleNamespace(free=free)): guard(reserve)
        return guard

    def test_metadata128_uses_per_file_max_and_keeps_source_temp_caps(self):
        rows = [{"path":"attempt07/a.json","eof":80*1024**2,"allocation":90*1024**2},
                {"path":"source/a.cpp","eof":2,"allocation":4096},
                {"path":"attempt07/.msvc-temp/a.txt","eof":3,"allocation":8192}]
        value = self.guard(rows)
        self.assertEqual(value.last["metadata"],90*1024**2)
        self.assertEqual((value.last["source"],value.last["temporary"]),(4096,8192))
        for path,cap in (("a.json",128),("source/a.cpp",96),("attempt07/.msvc-temp/a",384)):
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                self.guard([{"path":path,"eof":1,"allocation":cap*1024**2+1}])

    def test_parent_reserve_and_global_floor_unchanged(self):
        with self.assertRaisesRegex(RuntimeError,"reserve"): self.guard([],reserve=2,hard=1)
        with self.assertRaisesRegex(RuntimeError,"free floor"): self.guard([],free=2047)

    def configured(self, change=None, newer=False):
        build, source = Path("C:/native07/build"), Path("C:/native07/source/native")
        paths = [build/"CMakeCache.txt", build.parent/"attempt04/fixture-only-override.cmake",
                 build.parent/"attempt02/runtime-source-macro-restore.cmake"]
        escape = lambda p: p.as_posix().replace("$", "$$").replace(":", "$:").replace(" ", "$ ")
        raw = b"include CMakeFiles\\rules.ninja\n" + ("build build.ninja : RERUN_CMAKE | "+
            " ".join(escape(p) for p in paths)+"\n").encode()
        if change: raw = change(raw)
        def pinned(path):
            return {"path": str(path), "sha256":"fixture", "bytes":1,
                    "mtime_ns":2 if newer and Path(path).name == "CMakeCache.txt" else 1}
        with patch.object(Path, "stat") as stat, patch.object(Path, "open", side_effect=lambda *a,**k:io.BytesIO(raw)), \
                patch.object(contract,"pin",side_effect=pinned), patch.object(contract,"glob_contract",return_value={}):
            stat.return_value.st_size = len(raw)
            return contract.configured_inputs(build,source)

    def test_regeneration_complete_literal_inputs(self):
        self.assertEqual(len(self.configured()["inputs"]),3)

    def test_regeneration_missing_or_changed_grammar_reject(self):
        changes = [lambda b:b.replace(b"include CMakeFiles\\rules.ninja",b"include other.ninja"),
            lambda b:b.replace(b"CMakeCache.txt",b"wrong-cache.txt"),
            lambda b:b.replace(b" | ",b" || "),
            lambda b:b+b"builddir = elsewhere\n",
            lambda b:b+b"build build.ninja : RERUN_CMAKE | other\n",
            lambda b:b.replace(b"C$:/native07/build/CMakeCache.txt",b"$unknown/cache")]
        for number,change in enumerate(changes):
            with self.subTest(number=number), self.assertRaises(RuntimeError): self.configured(change)

    def test_real_newer_regeneration_input_reject(self):
        with self.assertRaisesRegex(RuntimeError,"newer"): self.configured(newer=True)

    def test_literal_tokens(self):
        self.assertEqual(contract.ninja_tokens(b"| C$:/Program$ Files/CMake/a.cmake x$$y"),
                         [b"|", b"C:/Program Files/CMake/a.cmake", b"x$y"])

    def test_unresolved_tokens_reject(self):
        for value in (b"$root/x", b"unfinished$", b"a$\tb"):
            with self.subTest(value=value), self.assertRaises(RuntimeError): contract.ninja_tokens(value)

    def test_two_globs_equal_and_bounded(self):
        source = Path("C:/frozen/native")
        text = "\n".join('file(GLOB NEW_GLOB LIST_DIRECTORIES true "'+(source/"src"/pattern).as_posix()+
            '")\nset(OLD_GLOB\n"'+(source/"src"/name).as_posix()+'"\n)'
            for pattern,name in (("ck3_12002*.cpp", "ck3_12002.cpp"),
                                 ("ck3_12002_*_test.cpp", "ck3_12002_a_test.cpp")))
        def found(path, pattern):
            return [source/"src"/("ck3_12002.cpp" if pattern == "ck3_12002*.cpp" else "ck3_12002_a_test.cpp")]
        with patch.object(Path, "stat") as stat, patch.object(Path, "read_text", return_value=text), \
                patch.object(Path, "glob", found), patch.object(contract, "pin", return_value={}):
            stat.return_value.st_size = len(text)
            self.assertEqual([v["entries"] for v in contract.glob_contract(Path("C:/build"),source)["families"]], [1,1])
            with patch.object(Path, "glob", return_value=[]):
                with self.assertRaisesRegex(RuntimeError, "glob differs"): contract.glob_contract(Path("C:/build"),source)
            stat.return_value.st_size = 128*1024+1
            with self.assertRaisesRegex(RuntimeError, "bounded"): contract.glob_contract(Path("C:/build"),source)

    def test_wrong_glob_family_reject(self):
        with patch.object(Path, "stat") as stat, patch.object(Path, "read_text", return_value=""):
            stat.return_value.st_size = 0
            with self.assertRaisesRegex(RuntimeError, "two actual"): contract.glob_contract(Path("C:/build"),Path("C:/source"))

    def test_only_literal_no_work(self):
        producer.assert_no_work("ninja: no work to do.\n")
        for value in ("[0/2] Re-checking globbed directories...", "ninja: no work to do.\n[1/2] compile", ""):
            with self.subTest(value=value), self.assertRaises(RuntimeError): producer.assert_no_work(value)

    def test_unchanged_secrets_are_not_persisted(self):
        self.assertEqual(environment.environment_delta({"Secret":"opaque","PATH":"old"},
            {"SECRET":"opaque","Path":"new","INCLUDE":"headers"}), {"PATH":"new","INCLUDE":"headers"})

    def test_changed_sensitive_key_reject(self):
        for key in ("password", "my_secret", "AUTH_TOKEN", "API_KEY"):
            with self.subTest(key=key), self.assertRaises(RuntimeError): environment.environment_delta({}, {key:"new"})

    def test_build_option_injection_reject(self):
        for key in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL"):
            with self.subTest(key=key), self.assertRaises(RuntimeError): environment.environment_delta({}, {key:"/unsafe"})

    def test_delta_size_reject(self):
        with self.assertRaises(RuntimeError): environment.environment_delta({}, {"X"+str(i):"v" for i in range(257)})

    def test_all_ninja_execution_uses_explicit_manifest(self):
        tree = ast.parse((HERE/"qualify_native30_fixture07_20261020.py").read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func,ast.Name)
            and n.func.id == "run" and n.args and isinstance(n.args[0],ast.List)]
        ninja = [n.args[0] for n in calls if ast.unparse(n.args[0].elts[0]) == "tools['ninja']"]
        self.assertEqual(len(ninja), 4) # original+snapshot commands loop, preview, fixture build, deps.
        for value in ninja: self.assertIn("-f", [n.value for n in value.elts if isinstance(n,ast.Constant)])
        text = ast.unparse(tree)
        self.assertNotIn("--build", text)
        self.assertNotIn("norebuild", text)

    def test_shared_preflight_precedes_first_mkdir(self):
        tree = ast.parse((HERE/"qualify_native30_fixture07_20261020.py").read_text())
        execute = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == "execute")
        calls = sorted((n.lineno, ast.unparse(n.func)) for n in ast.walk(execute) if isinstance(n,ast.Call))
        preflight = next(line for line,name in calls if name == "preflight")
        mkdir = next(line for line,name in calls if name.endswith(".mkdir"))
        self.assertLess(preflight,mkdir)
        text = ast.unparse(execute)
        self.assertIn("native_build_label_is_metadata",text)
        self.assertIn("Native30 continuous hotspot tracking and idle realm overview",text)

if __name__ == "__main__": unittest.main()
