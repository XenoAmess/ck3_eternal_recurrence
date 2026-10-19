"""Three source-level ledger/inverse tests. No C++ or process execution."""
import ast
from pathlib import Path
import unittest

import native30_artifact_postcheck11_20261020 as p

ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")


def guard_from_actual_source(budget):
    node = next(n for n in ast.walk(ast.parse(p.generated_bytes()))
                if isinstance(n, ast.FunctionDef) and n.name == "scope_guard")
    namespace = {"budget": budget, "ROOT": ROOT, "STAGE": ROOT / "attempt11-artifact-postcheck",
                 "OWNER": ROOT / "owner11-artifact/owner-spec",
                 "require": lambda value, text: None if value else (_ for _ in ()).throw(RuntimeError(text))}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "actual-generated-scope", "exec"), namespace)
    return namespace["scope_guard"]


class GuardTests(unittest.TestCase):
    def test_parent64MiB_reserve_and_small_local_pass_unchanged_parent_call(self):
        calls = []
        ledger = {"allocation": 737770536, "files": [
            {"path": "attempt11-artifact-postcheck/metadata.json", "eof": 1000, "allocation": 4096},
            {"path": "owner11-artifact/owner-spec/SPEC.json", "eof": 2000, "allocation": 4096},
            {"path": "attempt10-artifact-postcheck/FILES-CLOSED.json", "eof": 1371755, "allocation": 1372160}]}
        def parent(reserve):
            calls.append(reserve)
            return ledger
        self.assertIs(guard_from_actual_source(parent)(64 * 1048576), ledger)
        self.assertEqual(calls, [64 * 1048576])

    def test_local_over8MiB_still_rejected(self):
        calls = []
        def parent(reserve):
            calls.append(reserve)
            return {"files": [{"path": "attempt11-artifact-postcheck/output.log", "eof": 1,
                               "allocation": 8388609}]}
        with self.assertRaisesRegex(RuntimeError, "new postcheck8M"):
            guard_from_actual_source(parent)(64 * 1048576)
        self.assertEqual(calls, [64 * 1048576])

    def test_parent_failure_same_object_and_full_inverse(self):
        original = RuntimeError("parent aggregate/floor rejected")
        def parent(reserve):
            raise original
        with self.assertRaises(RuntimeError) as caught:
            guard_from_actual_source(parent)(64 * 1048576)
        self.assertIs(caught.exception, original)
        before, after = p.base_bytes(), p.generated_bytes()
        self.assertEqual(p.transform(after, reverse=True), before)
        self.assertIn(b"latest = budget(reserve)", after)
        self.assertNotIn(b"owned + reserve <= 8388608", after)
        self.assertEqual(p.BASE_SHA, __import__("hashlib").sha256(before).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
