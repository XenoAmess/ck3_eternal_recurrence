from __future__ import annotations
import ast,copy
from pathlib import Path
import runpy,unittest
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'src/xar_autoplayer/bridge'
CONTRACT=runpy.run_path(str(P/'frontend_applied_game_rules_contract.py'))
normalize=CONTRACT['normalize_frontend_applied_game_rules_v1']


def observed():
    return {'schema':'frontend_applied_game_rules_v1','schema_version':1,
        'game_version':'1.20.0.3','executable_sha256':CONTRACT['EXE_SHA256'],
        'source':'CGameRuleInstance.selected_settings','backend_id':'native-headless',
        'read_only':True,'uses_ocr':False,'uses_mouse':False,'uses_keyboard':False,
        'ready':True,'applied_settings_proven':True,'unavailable_reason':'','selection_count':1,
        'selections':[{'rule_key':'zg361_enabled','selected_setting_key':'zg361_off'}]}


class AppliedRulesContractTests(unittest.TestCase):
    def test_actual_off_value_and_unavailability_are_preserved(self):
        self.assertEqual(normalize(observed())['selections'][0]['selected_setting_key'],'zg361_off')
        unavailable={**observed(),'ready':False,'applied_settings_proven':False,
            'unavailable_reason':'applied_game_rule_instance_unverified','selection_count':0,'selections':[]}
        self.assertFalse(normalize(unavailable)['applied_settings_proven'])

    def test_ten_invalid_applied_observations_are_rejected(self):
        patches=[{'source':'CJominiGameRulesGui.current_selections'},{'applied_settings_proven':False},
            {'ready':False},{'game_version':'1.20.0.2'},{'uses_ocr':True},
            {'selection_count':True},{'selection_count':2},{'schema_version':True},
            {'selections':[{'rule_key':'zg361_enabled','selected_setting_key':'guessed value'}]},
            {'backend_id':'visual'}]
        for patch in patches:
            with self.subTest(patch=patch),self.assertRaises(ValueError):normalize({**observed(),**patch})

    def test_actual_driver_requires_one_readonly_native_ticket_and_retains_off(self):
        tree=ast.parse((P/'native_driver.py').read_text(encoding='utf-8-sig'))
        method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='query_frontend_applied_game_rules_v1')
        node=ast.ClassDef(name='Harness',bases=[],keywords=[],body=[copy.deepcopy(method)],decorator_list=[])
        module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
        binding={'bridge_pid':123,'connection_generation':1}
        namespace={**CONTRACT,'BridgeUnavailableError':RuntimeError,
            'frontend_gui_route_binding_from_capabilities':lambda caps:caps['binding']}
        exec(compile(module,'actual_applied_query_driver','exec'),namespace)
        h=namespace['Harness']();h._request_sequence=3;h.capabilities=lambda:{'binding':binding};calls=[]
        def primitive(step,**kwargs):calls.append((step,kwargs));h._request_sequence+=1;return observed()
        h._execute_primitive_step=primitive;result=h.query_frontend_applied_game_rules_v1()
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],CONTRACT['QUERY_FRONTEND_APPLIED_GAME_RULES_V1_STEP'])
        self.assertEqual(calls[0][1]['expected_revision'],0)
        self.assertTrue(result['applied_settings_proven']);self.assertEqual(result['selections'][0]['selected_setting_key'],'zg361_off')

if __name__=='__main__':unittest.main()
