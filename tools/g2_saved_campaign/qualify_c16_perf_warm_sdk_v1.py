"""Focused software qualification of the exact C16 in-memory SDK composition.

The untouched SDK imports from actual src13; only the composer's named changed
leaves use an in-memory loader.  No candidate tree, Game, Native or SDK owner is
created.  Existing tiny synthetic WAL tests retain their assertions; their two
unrelated M7 cleanup mocks are omitted because the actual C16 Driver has no M7
provider method.  That fixture adaptation never edits a production object.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import importlib.abc
import importlib.util
import io
import json
import linecache
from pathlib import Path
import sys
import tempfile
import types
import unittest

import prepare_c16_perf_warm_sdk_v1 as composer

REPO = composer.REPO
CONSTRUCTION = {"bytes": 40243, "sha256": "3bd067119b9d98eea6f1f57416fc5d42560dfde57183f67ff56926d314b62431"}
PRODUCTION_TEST = REPO / "ck3_autonomous_player/tests/unit/test_driver_state_wal_production_v1.py"
PRODUCTION_TEST_PIN = (21491, "7c6ceb55b6dd31ee6c972e03669d1075083df8cbe9ef63bbf78479986879de45")
TESTS = REPO / "ck3_autonomous_player/tests/unit"


class MemorySource(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, changed):
        self.sources = {name[:-3].replace("/", "."): (name, raw)
                        for name, raw in changed.items() if name.endswith(".py")}
        self.loaded = []

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.sources:
            relative, _ = self.sources[fullname]
            return importlib.util.spec_from_loader(fullname, self,
                                                  origin=str(composer.BASE_ROOT / relative))
        return None

    def create_module(self, spec):
        return None

    def get_source(self, fullname):
        return self.sources[fullname][1].decode("utf-8")

    def exec_module(self, module):
        relative, raw = self.sources[module.__name__]
        module.__file__ = str(composer.BASE_ROOT / relative)
        code_name = "<c16-warm-sdk-memory/" + relative + ">"
        source = raw.decode("utf-8")
        linecache.cache[code_name] = (len(raw), None, source.splitlines(keepends=True), code_name)
        exec(compile(raw, code_name, "exec", dont_inherit=True), module.__dict__)
        self.loaded.append({"module": module.__name__, "relative": relative, **composer.pin(raw)})


def load_wal_fixture_without_unrelated_m7_mocks():
    raw = composer.check_bytes(PRODUCTION_TEST.read_bytes(), PRODUCTION_TEST_PIN,
                               "original WAL production test")
    tree = ast.parse(raw)

    class RemoveUnrelatedMock(ast.NodeTransformer):
        removed = 0

        def visit_With(self, node):
            self.generic_visit(node)
            kept = []
            for item in node.items:
                call = item.context_expr
                match = (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                         and isinstance(call.func.value, ast.Name) and call.func.value.id == "patch"
                         and call.func.attr == "object" and len(call.args) == 2
                         and isinstance(call.args[0], ast.Name) and call.args[0].id in ("obj", "fresh")
                         and isinstance(call.args[1], ast.Constant)
                         and call.args[1].value == "_invalidate_player_heir_provider_v1"
                         and not call.keywords and item.optional_vars is None)
                if match:
                    self.removed += 1
                else:
                    kept.append(item)
            if kept:
                node.items = kept
                return node
            return ast.copy_location(ast.If(test=ast.Constant(True), body=node.body, orelse=[]), node)

    transform = RemoveUnrelatedMock()
    candidate = ast.fix_missing_locations(transform.visit(tree))
    composer.require(transform.removed == 2, "exact two unrelated M7 test mocks required")
    module = types.ModuleType("c16_warm_actual_production_wal_fixture")
    module.__file__ = str(PRODUCTION_TEST)
    exec(compile(candidate, str(PRODUCTION_TEST), "exec", dont_inherit=True), module.__dict__)
    composer.require(not hasattr(module.nd.NativeHeadlessGameplayDriver,
                                 "_invalidate_player_heir_provider_v1"),
                     "unrelated M7 provider accidentally entered actual composed Driver")
    return module, {"input": {"path": str(PRODUCTION_TEST), **composer.pin(raw)},
                    "removed_unrelated_M7_cleanup_mock_contexts": transform.removed,
                    "production_objects_or_assertions_modified": False,
                    "reason": "Actual C16 Driver predates M7; only the unrelated cleanup mocks are absent."}


class CompositionGuardTests(unittest.TestCase):
    def test_missing_and_ambiguous_hunk_refused(self):
        for original in (b"foreign\n", b"old\nold\n"):
            with self.subTest(original=original):
                with self.assertRaises(ValueError):
                    composer.transfer_exact_hunks(original, [(b"old\n", b"new\n")])

    def test_inverse_ambiguity_refused(self):
        with self.assertRaises(ValueError):
            composer.transfer_exact_hunks(b"old\nnew\n", [(b"old\n", b"new\n")])

    def test_hunks_preserve_foreign_surrounding_bytes(self):
        original = b"original-C16-cleanup\nold\nkeep-C16-provider\n"
        changed = composer.transfer_exact_hunks(original, [(b"old\n", b"new\n")])
        self.assertEqual(changed, b"original-C16-cleanup\nnew\nkeep-C16-provider\n")

    def test_unsafe_paths_refused(self):
        for path in ("../x.py", "x/../y.py", "/x.py", "D:/x.py", "x\\y.py", "x//y.py"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    composer.safe_relative(path)


def qualify():
    composer.require(sys.dont_write_bytecode, "qualification must run with -B")
    composer.require(not any(n == "xar_autoplayer" or n.startswith("xar_autoplayer.")
                            for n in sys.modules), "fresh qualification process required")
    changed, rows, plan = composer.compose(construction_pin=CONSTRUCTION)
    loader = MemorySource(changed)
    sys.meta_path.insert(0, loader)
    sys.path.insert(0, str(composer.BASE_ROOT))
    sys.path.insert(1, str(TESTS))
    original_tempdir = tempfile.tempdir
    # Existing synthetic fixtures clean their own TemporaryDirectory.  This
    # keeps all scratch on the current approved workspace; no system-temp roots.
    tempfile.tempdir = str(REPO / "_runtime")
    try:
        fixture, adaptation = load_wal_fixture_without_unrelated_m7_mocks()
        output = io.StringIO()
        suite = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(CompositionGuardTests),
            unittest.defaultTestLoader.loadTestsFromModule(fixture),
            unittest.defaultTestLoader.loadTestsFromName("test_exact_day_same_speed_configuration_v1"),
            unittest.defaultTestLoader.loadTestsFromName("test_exact_day_native_clock_paused_next_frame"),
            unittest.defaultTestLoader.loadTestsFromName("test_native_exact_day_speed_five"),
        ])
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
        print(output.getvalue())
        composer.require(result.wasSuccessful(), "actual composed-SDK focused unittest failed")
        import pytest
        pytest_args = ["-q", "-rs", "-p", "no:cacheprovider", "--basetemp=" + str(REPO / "_runtime/c16-warm-sdk-pytest92"),
                       str(TESTS / "test_construction_optional_source_8890.py"),
                       str(TESTS / "test_war_results_pause_wait_8495.py"),
                       str(TESTS / "test_sway_retained_wrapper_persistence_12004.py"),
                       str(TESTS / "test_reviewed_letter_source_rebind_v1.py")]
        pytest_code = pytest.main(pytest_args)
        composer.require(pytest_code == 0, "actual composed-SDK focused pytest failed")
        # Assert the import hook did not silently fall through to newest master.
        for name, module in list(sys.modules.items()):
            if name == "xar_autoplayer" or name.startswith("xar_autoplayer."):
                file = getattr(module, "__file__", None)
                if file:
                    composer.require(Path(file).resolve().is_relative_to(composer.BASE_ROOT.resolve()),
                                     "production dependency imported outside actual src13: " + name)
        plan.update({"qualification": {"scope": "Actual src13 imports plus exact in-memory composed leaves; tiny synthetic fixtures only",
                                      "unittest_cases": result.testsRun, "unittest_errors": len(result.errors),
                                      "unittest_failures": len(result.failures), "pytest_exit_code": pytest_code,
                                      "pytest_args": pytest_args, "WAL_fixture_adaptation": adaptation,
                                      "loaded_changed_modules": loader.loaded,
                                      "production_dependencies_only_actual_src13": True,
                                      "new_D_SDK_views_or_control_Task_Game_calls": 0},
                     "status": "COMPOSED_ACTUAL_SDK_FOCUSED_SOFTWARE_PASS_NOT_ADMITTED"})
        return plan
    finally:
        tempfile.tempdir = original_tempdir
        sys.meta_path.remove(loader)


def main():
    report = qualify()
    if len(sys.argv) == 2:
        path = Path(sys.argv[1]).resolve()
        composer.require(path.is_relative_to(REPO.resolve()), "report must remain in workspace")
        raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
        composer.require(len(raw) <= 64 * 1024, "small report budget exceeded")
        with path.open("xb") as stream:
            stream.write(raw)
        print(json.dumps({"report": {"path": str(path), **composer.pin(raw)}}))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
