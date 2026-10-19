"""Focused path semantics and unchanged retained guards; no Native writes."""
import ast
import copy
import importlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

q = importlib.import_module("tools.g2_saved_campaign.qualify_native30_fixture05_20261020")
old = importlib.import_module("tools.g2_saved_campaign.qualify_native30_fixture04_20261019")
guard = importlib.import_module("tools.g2_saved_campaign.native30_resume_guard_20261019")

def row(source, absolute=False):
    build = (q.ROOT / "build").resolve()
    part = "src" if source == q.ROOT / "source" / q.FIXTURE else source.parent.name
    relative = Path("CMakeFiles") / (q.TEST+".dir") / part / (source.name+".obj")
    obj = build / relative
    return {"directory": str(build), "file": str(source), "output": str(obj),
        "arguments": ["C:/MSVC/cl.exe", "/W4", "/WX", "/UNDEBUG", "/Fo"+str(obj if absolute else relative),
                      "-c", str(source)]}

def graph(item):
    return {"selected_compile_rows": [item], "link_contract": {"all12": "unchanged"}}

def compare(left, right):
    return q.exact_graph_delta(graph(left), graph(right), guard, Path(left["file"]), Path(right["file"]))

class Paths(unittest.TestCase):
    def setUp(self):
        self.a = row(q.ROOT / "source" / q.FIXTURE)
        self.b = row(q.COPY)

    def reject(self, changed):
        with self.assertRaises(RuntimeError): compare(self.a, changed)

    def test_relative_absolute(self):
        self.assertEqual(q.normalize_fixture_row(self.b, guard, q.COPY),
                         q.normalize_fixture_row(row(q.COPY, True), guard, q.COPY))

    def test_chain_current04_then05(self):
        for source in (q.PRIOR_COPY, q.COPY):
            self.assertEqual(compare(self.a, row(source))["selected_commands"], 1)

    def test_quoted_spaces(self):
        root = Path("C:/owned qualification space")
        with patch.multiple(q, ROOT=root, COPY=root/"build/native30-fixture05/camera_tracking_v1_test.cpp",
                            PRIOR_COPY=root/"build/native30-fixture04/camera_tracking_v1_test.cpp"):
            item = row(q.COPY)
            expected = q.normalize_fixture_row(item, guard, q.COPY)
            item["command"] = " ".join('"'+v+'"' for v in item.pop("arguments"))
            self.assertEqual(q.normalize_fixture_row(item, guard, q.COPY), expected)

    def test_wrong_source(self):
        self.b["arguments"][-1] += ".wrong"
        self.reject(self.b)

    def test_duplicate_source(self):
        self.b["arguments"].append(str(q.COPY))
        self.reject(self.b)

    def test_wrong_row_source(self):
        self.b["file"] += ".wrong"
        self.reject(self.b)

    def test_wrong_Fo(self):
        self.b["arguments"][4] += ".wrong"
        self.reject(self.b)

    def test_wrong_output_and_Fo_together(self):
        self.b["output"] += ".wrong"
        self.b["arguments"][4] = "/Fo"+self.b["output"]
        self.reject(self.b)

    def test_duplicate_Fo(self):
        self.b["arguments"].append(self.b["arguments"][4])
        self.reject(self.b)

    def test_empty_Fo(self):
        self.b["arguments"][4] = "/Fo"
        self.reject(self.b)

    def test_target_outside(self):
        self.b["output"] = str(q.ROOT/"foreign.obj")
        self.b["arguments"][4] = "/Fo"+self.b["output"]
        self.reject(self.b)

    def test_wrong_directory(self):
        self.b["directory"] = str(q.ROOT)
        self.reject(self.b)

    def test_extra_flag_or_tool(self):
        for change in (lambda r:r["arguments"].append("/DUNADMITTED=1"),
                       lambda r:r["arguments"].__setitem__(0, "C:/other/cl.exe")):
            item = copy.deepcopy(self.b)
            change(item)
            self.reject(item)

    def test_link_drift(self):
        right = graph(self.b)
        right["link_contract"]["all12"] = "changed"
        with self.assertRaises(RuntimeError):
            q.exact_graph_delta(graph(self.a), right, guard, Path(self.a["file"]), q.COPY)

    def test_other_fixture_argv_drift(self):
        left, right = graph(self.a), graph(self.b)
        other = row(q.ROOT/"source"/q.FIXTURE)
        other["output"] = other["output"].replace(q.TEST, "another_fixture")
        left["selected_compile_rows"].append(other)
        right["selected_compile_rows"].append(copy.deepcopy(other))
        right["selected_compile_rows"][1]["arguments"].append("/DCHANGED")
        with self.assertRaises(RuntimeError):
            q.exact_graph_delta(left, right, guard, Path(self.a["file"]), q.COPY)

    def test_retained_guards_AST_unchanged(self):
        def functions(module):
            return {n.name: ast.dump(n, include_attributes=False) for n in
                    ast.parse(Path(module.__file__).read_text()).body if isinstance(n, ast.FunctionDef)}
        left, right = functions(old), functions(q)
        for name in ("rows_by_target", "production_rows", "prior_output_boundary", "link_without_pdb",
                     "closed_link_proof", "classify_artifact", "checked_artifact_path", "retain_outputs",
                     "assert_no_work", "final_artifacts"):
            self.assertEqual(left[name], right[name], name)

    def test_other_commands_and_link_checks_AST(self):
        def function(module, name):
            return next(n for n in ast.parse(Path(module.__file__).read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == name)
        for a, b in zip(function(old, "exact_graph_delta").body[:10],
                        function(q, "exact_graph_delta").body[:10]):
            self.assertEqual(ast.dump(a), ast.dump(b))
        def fixture_loop(module):
            return next(n for n in ast.walk(function(module, "execute")) if isinstance(n, ast.For)
                        and isinstance(n.target, ast.Tuple) and
                        [getattr(v, "id", None) for v in n.target.elts] == ["number", "fixture"])
        class Labels(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str): node.value = node.value.replace("fixture05", "fixture04")
                return node
        self.assertEqual(ast.dump(fixture_loop(old)), ast.dump(Labels().visit(fixture_loop(q))))

if __name__ == "__main__": unittest.main()
