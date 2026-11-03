"""SOURCE_NOT_RUN: independent DATA tests; Native is the sole future executor.

Expectations were frozen in ORACLE-FROZEN.json before reading the public API.
All class/jar/Native receipts below are synthetic local metadata, never JVM
bytecode, actual execution evidence, SDK qualification, approval, or a lease.
The suite uses no network, subprocess, database, Java, Game, or Git API.
"""

import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


def _pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": path.as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return _pin(path)


def _args(path, tokens):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(token) + "\n" for token in tokens), encoding="utf-8", newline="\n")
    return _pin(path)


def _read(path):
    return json.loads(Path(path).read_bytes())


def _tokens(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _command(argfile):
    return ["C:/jdk-21/bin/javac.exe", "-J-Xmx192m", "-J-XX:ActiveProcessorCount=1", "@" + argfile.as_posix()]


def _guard(argfile, tokens):
    return {"argfile": _pin(argfile), "argfile_VM_tokens": 0,
            "direct_VM_options": ["-J-Xmx192m", "-J-XX:ActiveProcessorCount=1"],
            "compiler_tokens": len(tokens), "Java_started": False}


class _Fixture:
    """Only temporary local metadata; no imported helper or candidate runs here."""

    def __init__(self, root):
        self.root = root
        self.prod = root / "sources/data/Production.java"
        self.test = root / "sources/data/SelectedTest.java"
        self.prod.parent.mkdir(parents=True)
        self.prod.write_text("package data;\npublic final class Production {}\n", encoding="utf-8")
        self.test.write_text("package data;\npublic final class SelectedTest {\n"
                             " @org.junit.jupiter.api.Test void freshOne() {}\n"
                             " @org.junit.jupiter.api.Test void freshTwo() {}\n}\n", encoding="utf-8")
        prod_ready = _json(root / "source-ready-production.json", {"synthetic_DATA_only": True, "nested": {"source": _pin(self.prod)}})
        test_ready = _json(root / "source-ready-test.json", {"synthetic_DATA_only": True, "nested": {"source": _pin(self.test)}})
        sdk_a, sdk_b = root / "sdk/first", root / "sdk/shadow"
        for directory in (sdk_a, sdk_b):
            (directory / "data").mkdir(parents=True)
            (directory / "data/Api.class").write_bytes(b"SYNTHETIC DATA ONLY: not JVM bytecode\n" + directory.name.encode())
        self.entries = [sdk_a.as_posix(), sdk_b.as_posix()] + [sdk_a.as_posix()] * 314
        self.family = {"index": 0, "root": self.entries[0], "relative": "data/Api.class", "pin": _pin(sdk_a / "data/Api.class")}
        self.jar = root / "sdk/junit-platform-console-standalone.jar"
        self.jar.write_bytes(b"SYNTHETIC DATA ONLY: not a runnable jar\n")
        template = root / "templates"
        template.mkdir()
        prod_args, test_args, junit_args = (template / name for name in ("PROD.args", "TEST.args", "JUNIT.args"))
        sdk_empty = template / "prod-empty-source"
        old_test = template / "old-test"
        for directory in (sdk_empty, old_test / "classes-test", old_test / "empty-source", old_test / "reports", old_test / "tmp"):
            directory.mkdir(parents=True, exist_ok=True)
        cp = ";".join(self.entries)
        prod_tokens = ["--release", "21", "-Xlint:all,-try", "-Werror", "-proc:none", "-implicit:none",
                       "-sourcepath", sdk_empty.as_posix(), "-cp", cp, "-d", sdk_a.as_posix(), self.prod.as_posix()]
        test_tokens = ["--release", "21", "-encoding", "UTF-8", "-proc:none", "-Xlint:all,-try", "-Werror", "-implicit:none",
                       "-sourcepath", (old_test / "empty-source").as_posix(), "-cp",
                       ";".join([sdk_a.as_posix(), self.jar.as_posix(), *self.entries]),
                       "-d", (old_test / "classes-test").as_posix(), self.test.as_posix()]
        junit_tokens = ["-Djava.io.tmpdir=" + (old_test / "tmp").as_posix(), "-jar", self.jar.as_posix(), "execute", "--class-path",
                        ";".join([(old_test / "classes-test").as_posix(), sdk_a.as_posix(), *self.entries]),
                        "--disable-banner", "--details=summary", "--fail-if-no-tests", "--reports-dir=" + (old_test / "reports").as_posix(),
                        "--select-method=data.SelectedTest#historicalOne", "--select-method=data.SelectedTest#historicalTwo"]
        _args(prod_args, prod_tokens)
        _args(test_args, test_tokens)
        _args(junit_args, junit_tokens)
        prod_config = {"source_ready": prod_ready, "pins": [_pin(self.prod), prod_ready, _pin(prod_args), self.family["pin"]],
                       "methods": [], "expected_class": None, "reports": None,
                       "qualifiedDirectAndSamePackageFamilies": {"data.Api": self.family}, "CP316LiteralRetained": True,
                       "source_only_compile_compatibility": True, "current_runtime_source_or_loaded_parity": False,
                       "newPrivateHelperAndLambda": False, "productionTUs": 1, "TestRUN": 0, "GameGETAdoption": 0,
                       "phases": {"prod": {"command": _command(prod_args), "args": _pin(prod_args), "guard": _guard(prod_args, prod_tokens),
                                            "sources": [_pin(self.prod)], "output": sdk_a.as_posix(), "timeout_seconds": 30}}}
        prod_config_pin = _json(template / "PROD-CONFIG.json", prod_config)
        sdk_actual, sdk_verified = self.receipts(template / "sdk-data-receipts", prod_config_pin, prod_config["phases"]["prod"]["command"], [self.family["pin"]])
        test_family = dict(self.family, index=2)
        test_config = {"source_ready": test_ready, "pins": [_pin(self.test), test_ready, _pin(test_args), _pin(junit_args), _pin(self.jar), sdk_actual, self.family["pin"]],
                       "methods": ["historicalOne", "historicalTwo"], "expected_class": "data.SelectedTest", "reports": (old_test / "reports").as_posix(),
                       "named_current_API_families": {"data.Api": test_family}, "only_new_selectors": True,
                       "old_methods_RUN": 0, "actual_prod": sdk_actual, "classpath_base316_literal": True, "CP_test": 318, "CP_run": 318, "production_compile": 0,
                       "fixture": {"Windows_JNA_required": False, "task_root": root.as_posix(),
                                   "effective_fixture_properties": {"java.io.tmpdir": (old_test / "tmp").as_posix()}, "Java_started": False},
                       "phases": {"test": {"command": _command(test_args), "args": _pin(test_args), "guard": _guard(test_args, test_tokens),
                                            "sources": [_pin(self.test)], "output": (old_test / "classes-test").as_posix(), "timeout_seconds": 30},
                                  "junit": {"command": ["C:/jdk-21/bin/java.exe", "@" + junit_args.as_posix()], "args": _pin(junit_args), "timeout_seconds": 30}}}
        test_config_pin = _json(template / "TEST-CONFIG.json", test_config)
        self.declaration = {"schema": "xar.native-sdk-declaration/v1", "issuer": "/root/native_continue",
                            "scope": "SYNTHETIC DATA ONLY; no actual SDK qualification or execution",
                            "sources": {"production": _pin(self.prod), "test": _pin(self.test)},
                            "sdk_config": prod_config_pin, "sdk_actual": sdk_actual, "sdk_verified": sdk_verified,
                            "sdk_args": _pin(prod_args), "sdk_entries": self.entries,
                            "required_families": {"production": ["data.Api"], "test": ["data.Api", "data.Production"]},
                            "families": {"data.Api": self.family}}
        self.declaration_path = root / "native-sdk-declaration-DATA.json"
        self.output = root / "prepared"
        self.request = {"schema": "xar.verification-recipe-request/v1", "profile": "one-prod-one-test-explicit-methods",
                        "output_root": self.output.as_posix(), "production_source": _pin(self.prod), "test_source": _pin(self.test),
                        "production_ready": prod_ready, "test_ready": test_ready, "production_class": "data.Production", "test_class": "data.SelectedTest",
                        "methods": ["freshOne", "freshTwo"],
                        "templates": {"prod_config": prod_config_pin, "prod_args": _pin(prod_args), "test_config": test_config_pin,
                                      "test_args": _pin(test_args), "junit_args": _pin(junit_args)},
                        "sdk_declaration": _json(self.declaration_path, self.declaration)}
        self.request_path = root / "REQUEST.json"
        self.save_request()

    def save_request(self):
        return _json(self.request_path, self.request)

    def save_declaration(self):
        self.request["sdk_declaration"] = _json(self.declaration_path, self.declaration)
        self.save_request()

    @staticmethod
    def receipts(directory, config_pin, command, classes):
        actual = _json(directory / "ACTUAL.json", {"synthetic_DATA_only": True, "phase": "prod", "config": config_pin,
                       "command": command, "exit_code": 0, "error": None, "timeout": False, "pins_unchanged": True, "classes": classes})
        verified = _json(directory / "VERIFIED.json", {"synthetic_DATA_only": True, "actual": actual, "phase": "prod", "classes": classes})
        return actual, verified

    def production_receipts(self):
        config_path = self.output / "production/CONFIG.json"
        config = _read(config_path)
        classes = self.output / "production/classes/data"
        classes.mkdir(parents=True, exist_ok=True)
        (classes / "Production.class").write_bytes(b"SYNTHETIC DATA ONLY: selected top-level\n")
        (classes / "Production$Nested.class").write_bytes(b"SYNTHETIC DATA ONLY: nested output\n")
        rows = [_pin(path) for path in sorted(classes.glob("*.class"))]
        return self.receipts(self.root / "new-production-DATA-receipts", _pin(config_path), config["phases"]["prod"]["command"], rows)


@contextlib.contextmanager
def _fixture():
    with tempfile.TemporaryDirectory(prefix="recipe-DATA-", dir=Path(__file__).parent) as directory:
        yield _Fixture(Path(directory))


class VerificationRecipeDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if Path(__file__).resolve().drive.upper() != "D:":
            raise unittest.SkipTest("Native DATA fixture requires its isolated D owner directory")
        path = Path(__file__).parent.parent / "prepare_verification_recipe.py"
        spec = importlib.util.spec_from_file_location("verification_recipe_under_test", path)
        cls.api = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.api
        spec.loader.exec_module(cls.api)

    def _rejected(self, fixture, codes, call=None):
        with self.assertRaises(self.api.RecipeError) as raised:
            (call or (lambda: self.api.prepare_production(fixture.request_path)))()
        self.assertIn(raised.exception.code, codes)
        self.assertIsInstance(raised.exception.detail, str)
        self.assertTrue(raised.exception.detail)
        self.assertFalse((fixture.output / "tests/PREPARED-READY.json").exists())

    def test_accepted_profile_preserves_metadata_and_exact_new_output_prefix(self):
        with _fixture() as f:
            frozen_inputs = {path: path.read_bytes() for path in f.root.rglob("*") if path.is_file()}
            ready = self.api.prepare_production(f.request_path)
            self.assertEqual(ready, _pin(f.output / "production/PREPARED-READY.json"))
            self.assertFalse((f.output / "tests").exists())
            config = _read(f.output / "production/CONFIG.json")
            prod_tokens = _tokens(f.output / "production/PROD.args")
            self.assertEqual(prod_tokens[prod_tokens.index("-cp") + 1], ";".join(f.entries))
            self.assertEqual(config["phases"]["prod"]["sources"], [_pin(f.prod)])
            self.assertEqual([token for token in prod_tokens if token.endswith(".java")], [f.prod.as_posix()])
            actual, verified = f.production_receipts()
            test_ready = self.api.prepare_tests(ready, actual, verified)
            self.assertEqual(test_ready, _pin(f.output / "tests/PREPARED-READY.json"))
            test_config = _read(f.output / "tests/CONFIG.json")
            tt, jt = _tokens(f.output / "tests/TEST.args"), _tokens(f.output / "tests/JUNIT.args")
            prod_out, test_out = f.output / "production/classes", f.output / "tests/classes-test"
            self.assertEqual(tt[tt.index("-cp") + 1].split(";"), [prod_out.as_posix(), f.jar.as_posix(), *f.entries])
            self.assertEqual(jt[jt.index("--class-path") + 1].split(";"), [test_out.as_posix(), prod_out.as_posix(), *f.entries])
            self.assertEqual([token for token in jt if token.startswith("--select-")], ["--select-method=data.SelectedTest#freshOne", "--select-method=data.SelectedTest#freshTwo"])
            self.assertFalse(any("scan-class" in token or "historicalOne" in token or "historicalTwo" in token for token in jt))
            self.assertEqual(test_config["methods"], ["freshOne", "freshTwo"])
            self.assertEqual(test_config["phases"]["test"]["sources"], [_pin(f.test)])
            self.assertEqual(test_config["actual_prod"], actual)
            for row in _read(actual["path"])["classes"]:
                self.assertIn(row, test_config["pins"])
            self.assertIn("--fail-if-no-tests", jt)
            self.assertIn("-Djava.io.tmpdir=" + (f.output / "tests/tmp").as_posix(), jt)
            self.assertIn("--reports-dir=" + (f.output / "tests/reports").as_posix(), jt)
            for configuration, phase, tokens in ((config, "prod", prod_tokens), (test_config, "test", tt)):
                command = configuration["phases"][phase]["command"]
                self.assertEqual([x for x in command if x.startswith("-J")], ["-J-Xmx192m", "-J-XX:ActiveProcessorCount=1"])
                self.assertFalse(any(x.startswith("-J") or x.startswith("@") for x in tokens))
                self.assertEqual(configuration["phases"][phase]["guard"]["argfile_VM_tokens"], 0)
                self.assertFalse(configuration["phases"][phase]["guard"]["Java_started"])
                self.assertEqual(configuration["phases"][phase]["args"], _pin(f.output / ("production/PROD.args" if phase == "prod" else "tests/TEST.args")))
            for path, original_bytes in frozen_inputs.items():
                self.assertEqual(path.read_bytes(), original_bytes)
            for path in f.output.rglob("*.json"):
                document = _read(path)
                for key in ("qualification_granted", "lease_granted", "approval_granted", "Java_started", "TestRUN", "tests_RUN", "GameGETAdoption", "old_methods_RUN"):
                    if key in document:
                        self.assertFalse(document[key], (path, key))
            self.assertFalse(list(f.output.rglob("*.py")))
            self.assertFalse(list(f.output.rglob("BEGIN.json")))

    def test_unsupported_profile_and_nonexplicit_selectors_fail_named(self):
        mutations = [("profile", "two-prod-one-test", {"UNSUPPORTED_PROFILE"}),
                     ("production_source", "two-tu-list", {"REQUEST_SCHEMA"}),
                     ("methods", [], {"INVALID_SELECTOR"}),
                     ("methods", ["--select-class=data.SelectedTest"], {"INVALID_SELECTOR"}),
                     ("methods", ["--scan-classpath"], {"INVALID_SELECTOR"})]
        for key, value, codes in mutations:
            with self.subTest(key=key, value=value), _fixture() as f:
                f.request[key] = [f.request["production_source"]] * 2 if value == "two-tu-list" else value
                f.save_request()
                self._rejected(f, codes)
                self.assertFalse(f.output.exists())

    def test_missing_or_inconsistent_proof_and_output_manifest_fail_named(self):
        for case, codes in (("missing-declaration", {"SDK_DECLARATION_REQUIRED"}),
                            ("changed-sdk-tail", {"SDK_QUALIFICATION"}),
                            ("stale-source", {"PIN_MISMATCH"}),
                            ("unmanifested-output", {"OUTPUT_MANIFEST"})):
            with self.subTest(case=case), _fixture() as f:
                if case == "missing-declaration":
                    del f.request["sdk_declaration"]
                    f.save_request()
                elif case == "changed-sdk-tail":
                    f.declaration["sdk_entries"] = [f.entries[1], f.entries[0], *f.entries[2:]]
                    f.save_declaration()
                elif case == "stale-source":
                    f.prod.write_bytes(f.prod.read_bytes() + b"// changed after pin\n")
                else:
                    ready = self.api.prepare_production(f.request_path)
                    actual, verified = f.production_receipts()
                    (f.output / "production/classes/data/Unmanifested.class").write_bytes(b"SYNTHETIC unmanifested DATA\n")
                    self._rejected(f, codes, lambda: self.api.prepare_tests(ready, actual, verified))
                    continue
                self._rejected(f, codes)
                self.assertFalse(f.output.exists())


    def test_standalone_junit_jar_drift_rejected_against_original_template_pin(self):
        # New owner boundary from independent sourcecounter; original three stay frozen.
        for phase in ('before-production', 'after-production'):
            with self.subTest(phase=phase), _fixture() as f:
                if phase == 'after-production':
                    ready = self.api.prepare_production(f.request_path)
                    actual, verified = f.production_receipts()
                f.jar.write_bytes(f.jar.read_bytes() + b'changed after original template pin\n')
                if phase == 'before-production':
                    self._rejected(f, {'PIN_MISMATCH'})
                    self.assertFalse(f.output.exists())
                else:
                    self._rejected(f, {'PIN_MISMATCH'}, lambda: self.api.prepare_tests(ready, actual, verified))
                    self.assertFalse((f.output / 'tests').exists())


if __name__ == "__main__":
    unittest.main()
