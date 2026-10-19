"""Focused current-vs-historical metadata and no-configure invariants."""
import ast
import copy
import importlib
from pathlib import Path
import unittest

q = importlib.import_module("tools.g2_saved_campaign.qualify_native30_fixture06_20261020")
old = importlib.import_module("tools.g2_saved_campaign.qualify_native30_fixture05_20261020")
guard = importlib.import_module("tools.g2_saved_campaign.native30_resume_guard_20261019")

def functions(module):
    return {n.name:n for n in ast.parse(Path(module.__file__).read_text()).body if isinstance(n, ast.FunctionDef)}

def row(source, directory="src"):
    build = q.ROOT / "build"
    obj = Path("CMakeFiles")/(q.TEST+".dir")/directory/(source.name+".obj")
    return {"directory": str(build), "file": str(source), "output": str(build/obj),
            "arguments": ["C:/MSVC/cl.exe", "/WX", "/UNDEBUG", "/Fo"+str(obj), "-c", str(source)]}

def graphs():
    left = {"selected_compile_rows": [row(q.ROOT/"source"/q.FIXTURE)],
            "targets": [{"name": "historical_target", "fileapi": {"path": "deliberately-absent-old-reply.json"}}],
            "link_contract": {"all12": {"type": "EXECUTABLE", "artifacts": ["fixture.exe"]}}}
    right = {**copy.deepcopy(left), "selected_compile_rows": [row(q.COPY, "native30-fixture04")]}
    return left, right

class CurrentGraph(unittest.TestCase):
    def test_obsolete_historical_reply_is_not_graph_authority(self):
        left, right = graphs()
        self.assertFalse(Path(left["targets"][0]["fileapi"]["path"]).exists())
        delta = q.exact_graph_delta(left, right, guard, q.ROOT/"source"/q.FIXTURE, q.COPY)
        self.assertTrue(delta["production_and_other_fixture_argv_identical"])

    def test_current_artifact_drift_rejected(self):
        left, right = graphs()
        right["link_contract"]["all12"]["artifacts"].append("unadmitted.pdb")
        with self.assertRaises(RuntimeError):
            q.exact_graph_delta(left, right, guard, q.ROOT/"source"/q.FIXTURE, q.COPY)

    def test_extra_compile_argument_rejected(self):
        left, right = graphs()
        right["selected_compile_rows"][0]["arguments"].append("/DUNADMITTED")
        with self.assertRaises(RuntimeError):
            q.exact_graph_delta(left, right, guard, q.ROOT/"source"/q.FIXTURE, q.COPY)

    def test_configured_fixed_source_is04_and_new_attempt_only06(self):
        self.assertEqual(q.COPY, q.PRIOR_COPY)
        self.assertEqual(q.COPY.parent.name, "native30-fixture04")
        self.assertEqual(q.ATTEMPT.name, "attempt06")

    def test_preflight_never_iterates_old_reply_names(self):
        source = ast.unparse(functions(q)["preflight"])
        self.assertNotIn("before['targets']", source)
        self.assertIn("for target in current['targets']", source)
        self.assertIn("resume.link_contract(base, current)", source)
        self.assertIn("exact_graph_delta(before, current", source)

    def test_shared_preflight_is_before_first_write(self):
        source = ast.unparse(functions(q)["execute"])
        self.assertLess(source.index("checked = preflight("), source.index("ATTEMPT.mkdir("))
        self.assertNotIn("--configure", source)
        self.assertNotIn("COPY.open(", source)
        self.assertNotIn("COPY.parent.mkdir(", source)
        self.assertIn("after = current", source)

    def test_preflight_has_no_Native_write_or_process_launch(self):
        prohibited = {"mkdir", "write", "write_bytes", "write_text", "unlink", "run_owned", "Popen", "execute"}
        for node in ast.walk(functions(q)["preflight"]):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", getattr(node.func, "id", ""))
                self.assertNotIn(name, prohibited)
                if name == "CreateFile":
                    self.assertEqual([ast.literal_eval(v) for v in node.args[1:6]], [0x80000000, 1, None, 3, 0x80])

    def test_retained_guard_functions_AST(self):
        a, b = functions(old), functions(q)
        for name in ("rows_by_target", "exact_graph_delta", "production_rows", "prior_output_boundary",
                     "link_without_pdb", "closed_link_proof", "classify_artifact", "checked_artifact_path",
                     "retain_outputs", "assert_no_work", "final_artifacts"):
            self.assertEqual(ast.dump(a[name]), ast.dump(b[name]), name)

    def test_fixture_execution_Defender_and_final_guards_AST(self):
        def loop(module):
            return next(n for n in ast.walk(functions(module)["execute"]) if isinstance(n, ast.For)
                and isinstance(n.target, ast.Tuple) and
                [getattr(v, "id", None) for v in n.target.elts] == ["number", "fixture"])
        class Labels(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str): node.value = node.value.replace("fixture06", "fixture05")
                return node
        self.assertEqual(ast.dump(loop(old)), ast.dump(Labels().visit(loop(q))))

if __name__ == "__main__": unittest.main()
