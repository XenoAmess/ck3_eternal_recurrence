"""Pure exact-build character query contract checks; no driver or native runtime."""
from pathlib import Path
import ast
import copy
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge import ingame_ui_contract as contract
from xar_autoplayer.bridge.version_identity import CK3_11906, CK3_12003, CK3_12004

# Reuse only the sibling's pure wire DTO factory. Importing its entire test module
# would also import the driver/server; neither is needed for these two checks.
fixture_path = Path(__file__).with_name("test_ingame_ui_navigation_v1.py")
fixture_node = next(
    node for node in ast.parse(fixture_path.read_text(encoding="utf-8-sig")).body
    if isinstance(node, ast.FunctionDef) and node.name == "result"
)
scope = {}
exec(compile(ast.Module(body=[fixture_node], type_ignores=[]), str(fixture_path), "exec"), scope)

class QueryOnlyContractTests(unittest.TestCase):
    def test_exact4_query_admitted_without_open_or_other_build_kind_expansion(self):
        contract.validate_ui_build_scope(CK3_12004,'query','character')
        for build,op,kind in ((CK3_12004,'open_character','character'),(CK3_12003,'query','character'),
                              (CK3_12004,'query','combat'),(CK3_12004,'query','knights')):
            with self.subTest(build=build,op=op,kind=kind),self.assertRaises(ValueError):
                contract.validate_ui_build_scope(build,op,kind)
        for build in (CK3_11906,CK3_12003,CK3_12004):
            contract.validate_ui_build_scope(build,'query','army')
        contract.validate_ui_build_scope(CK3_11906,'open_character','character')

    def test_character_dto_keeps_owner_subject_and_action_proofs_separate(self):
        raw=scope['result']('character','query',0)
        raw.update(game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,
                   native_backend_id=CK3_12004.backend_id('ingame-ui-v1'),
                   owner_character_id_available=False,owner_character_id=None)
        kwargs=dict(operation='query',kind='character',subject_id=0,native_revision=3,
                    date_raw=53146848,actor_id=29829,expected_build=CK3_12004)
        observed=contract.normalize_ui_result(raw,**kwargs)
        self.assertEqual(observed['current_subject_id'],16777218)
        self.assertNotEqual(observed['current_subject_id'],observed['played_character_id'])
        self.assertFalse(observed['dispatch_invoked'])
        for changes in ({'window_name':'army_window'},{'current_subject_id':0},
                        {'current_subject_id':2**32-1},{'native_army_id':12},
                        {'owner_character_id_available':True,'owner_character_id':29829},
                        {'dispatch_invoked':True},{'verification_pending':True},
                        {'gui_owner_binding_verified':False},{'native_revision':4}):
            value=copy.deepcopy(raw);value.update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                contract.normalize_ui_result(value,**kwargs)

if __name__ == "__main__":
    unittest.main()
