"""Synthetic metadata builders only; no old Test or executable production evidence.

Copied synthetic builders from the original one-TU fixture; new v2 tests know the public contract.
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
