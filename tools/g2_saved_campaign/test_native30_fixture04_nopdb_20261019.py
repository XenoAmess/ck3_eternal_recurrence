"""Known predicted PDB is optional only under the exact observed no-debug contract."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).with_name("qualify_native30_fixture04_20261019.py")
SPEC = importlib.util.spec_from_file_location("native30_fixture04_tested", PATH)
Q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(Q)
COMMAND = 'link.exe /out:xar_ck3_bridge.dll /pdb:xar_ck3_bridge.pdb /dll /INCREMENTAL:NO /OPT:REF'

def proof():
    return {"line_sha256": "known-sha", "link_options": Q.link_without_pdb(COMMAND)}

class LinkProof(unittest.TestCase):
    def test_explicit_out_pdb_nondebug_nonincremental(self):
        self.assertEqual(Q.link_without_pdb(COMMAND)["pdb"], ["xar_ck3_bridge.pdb"])
    def test_debug_link_rejected(self):
        with self.assertRaises(RuntimeError): Q.link_without_pdb(COMMAND+" /DEBUG")
    def test_debug_full_rejected(self):
        with self.assertRaises(RuntimeError): Q.link_without_pdb(COMMAND+" /DEBUG:FULL")
    def test_even_debug_none_is_not_the_observed_contract(self):
        with self.assertRaises(RuntimeError): Q.link_without_pdb(COMMAND+" /DEBUG:NONE")
    def test_incremental_yes_rejected(self):
        with self.assertRaises(RuntimeError): Q.link_without_pdb(COMMAND+" /INCREMENTAL:YES")
    def test_other_pdb_path_rejected(self):
        with self.assertRaises(RuntimeError): Q.link_without_pdb(COMMAND.replace("xar_ck3_bridge.pdb", "other.pdb"))
    def test_missing_explicit_nondebug_recipe_not_guessed(self):
        with self.assertRaises(RuntimeError): Q.link_without_pdb(COMMAND.replace(" /INCREMENTAL:NO", ""))
    def test_actual_closed_command_has_exact_no_debug_flags(self):
        class Base:
            @staticmethod
            def pin(path): return {"path": str(path)}
        observed = Q.closed_link_proof(Base, Q.ROOT/"attempt02/actual-generated-commands.log")
        self.assertEqual(observed["link_options"]["pdb"], ["xar_ck3_bridge.pdb"])
        self.assertNotIn("debug", observed["link_options"])

class ArtifactPolicy(unittest.TestCase):
    def test_exact_predicted_absent_pdb_is_known_not_generated(self):
        self.assertEqual(Q.classify_artifact("xar_ck3_bridge", "xar_ck3_bridge.pdb", False, False, proof()),
                         "known_not_generated")
    def test_actual_pdb_present_fails(self):
        with self.assertRaises(RuntimeError):
            Q.classify_artifact("xar_ck3_bridge", "xar_ck3_bridge.pdb", True, False, proof())
    def test_old_inventory_pdb_present_fails(self):
        with self.assertRaises(RuntimeError):
            Q.classify_artifact("xar_ck3_bridge", "xar_ck3_bridge.pdb", False, True, proof())
    def test_missing_dll_still_fails(self):
        with self.assertRaises(RuntimeError):
            Q.classify_artifact("xar_ck3_bridge", "xar_ck3_bridge.dll", False, False, proof())
    def test_missing_lib_still_fails(self):
        with self.assertRaises(RuntimeError):
            Q.classify_artifact("xar_ck3_12002_runtime", "xar_ck3_12002_runtime.lib", False, False, proof())
    def test_other_predicted_pdb_is_not_admitted(self):
        with self.assertRaises(RuntimeError):
            Q.classify_artifact("xar_bridge_protocol", "xar_bridge_protocol.pdb", False, False, proof())
    def test_same_filename_other_target_not_admitted(self):
        with self.assertRaises(RuntimeError):
            Q.classify_artifact("other", "xar_ck3_bridge.pdb", False, False, proof())
    def test_absence_without_link_proof_fails(self):
        with self.assertRaises(RuntimeError):
            Q.classify_artifact("xar_ck3_bridge", "xar_ck3_bridge.pdb", False, False, {})
    def test_existing_required_dll_remains_required(self):
        self.assertEqual(Q.classify_artifact("xar_ck3_bridge", "xar_ck3_bridge.dll", True, True, proof()), "required")
    def test_outside_build_path_rejected_before_classification(self):
        class Base:
            @staticmethod
            def inside(path, root): return path.is_relative_to(root.resolve())
        with self.assertRaises(RuntimeError): Q.checked_artifact_path(Base, Path("C:/build"), "../foreign.dll")

class PreservedContracts(unittest.TestCase):
    def test_other_pure_contract_functions_are_AST_identical_to_frozen03(self):
        old = ast.parse(PATH.with_name("qualify_native30_fixture03_20261019.py").read_text())
        new = ast.parse(PATH.read_text())
        old_functions = {node.name: node for node in old.body if isinstance(node, ast.FunctionDef)}
        new_functions = {node.name: node for node in new.body if isinstance(node, ast.FunctionDef)}
        for name in ("fixture_delta", "rows_by_target", "argv", "exact_graph_delta", "production_rows",
                     "prior_output_boundary", "assert_no_work", "final_artifacts"):
            self.assertEqual(ast.dump(old_functions[name]), ast.dump(new_functions[name]), name)
        old_card = ast.dump(old_functions["validate_card"])
        new_card = ast.dump(new_functions["validate_card"]).replace("attempt04", "attempt03")
        self.assertEqual(old_card, new_card, "same admission checks with a new absent attempt root")
    def test_no_debug_guard_remains_in_final_artifacts(self):
        text = PATH.read_text()
        self.assertIn('not list(build.rglob("*.pdb")) and not list(build.rglob("*.ilk"))', text)
        self.assertIn('base.inside(path, build), "FileAPI artifact outside build:', text)

if __name__ == "__main__": unittest.main(verbosity=2)
