from __future__ import annotations
import ast
import copy
from pathlib import Path
import runpy
import unittest

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'src/xar_autoplayer/bridge'
CONTRACT=runpy.run_path(str(P/'frontend_game_rules_control_contract.py'))
QUERY=runpy.run_path(str(P/'frontend_game_rules_contract.py'))


def window(visible=True):
    return {'schema':'frontend_game_rules_window_v1','schema_version':1,
        'game_version':'1.20.0.3','executable_sha256':CONTRACT['EXE_SHA256'],
        'source':'CJominiGameRulesGui.owner_root_and_stock_predicates','read_only':True,
        'backend_id':'native-headless','uses_ocr':False,'uses_mouse':False,'uses_keyboard':False,
        'applied_settings_proven':False,'ready':True,'unavailable_reason':'',
        'window_visible':visible,'window_enabled':True,'is_host':True,
        'game_has_started':False,'may_edit':visible,'window_closed_proven':not visible}


def ack(action='select'):
    return {'schema':'frontend_game_rules_mutation_v1','schema_version':1,
        'game_version':'1.20.0.3','executable_sha256':CONTRACT['EXE_SHA256'],
        'source':'CJominiGameRulesGui.stock_methods','read_only':False,'backend_id':'native-headless',
        'uses_ocr':False,'uses_mouse':False,'uses_keyboard':False,'applied_settings_proven':False,
        'window_closed_proven':False,'ready':True,'unavailable_reason':'','action':action,
        'native_invoked':True,'selection_verified':action=='select',
        'apply_invoked':action=='apply_and_hide','hide_invoked':action!='select',
        'native_next_calls':1 if action=='select' else 0}


def values(current='zg361_on',other='zg361_freq_yearly'):
    return {'schema':'frontend_game_rule_selections_v1','schema_version':1,
        'game_version':'1.20.0.3','executable_sha256':CONTRACT['EXE_SHA256'],
        'source':'CJominiGameRulesGui.current_selections','read_only':True,
        'backend_id':'native-headless','uses_ocr':False,'uses_mouse':False,'uses_keyboard':False,
        'applied_settings_proven':False,'ready':True,'unavailable_reason':'','selection_count':2,
        'selections':[{'rule_key':'zg361_enabled','selected_setting_key':current},
            {'rule_key':'zg361_frequency','selected_setting_key':other}]}


class FakeTime:
    elapsed=0.0
    def monotonic(self):return self.elapsed
    def sleep(self,value):self.elapsed+=0.5


def driver_harness():
    tree=ast.parse((P/'native_driver.py').read_text(encoding='utf-8-sig'))
    names={'query_frontend_game_rules_window_v1','query_frontend_game_rule_selections_v1',
        'select_frontend_game_rule_v1','_wait_frontend_game_rules_closed_v1',
        '_apply_or_hide_frontend_game_rules_v1','apply_and_hide_frontend_game_rules_v1',
        'hide_frontend_game_rules_v1'}
    methods=[copy.deepcopy(n) for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(methods)==len(names)
    node=ast.ClassDef(name='Harness',bases=[],keywords=[],body=methods,decorator_list=[])
    module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
    namespace={**CONTRACT,**QUERY,'BridgeUnavailableError':RuntimeError,'time':FakeTime(),
        'frontend_gui_route_binding_from_capabilities':lambda caps:caps['binding']}
    exec(compile(module,'actual_driver_rules_methods','exec'),namespace)
    h=namespace['Harness']();h._request_sequence=0;h.current='zg361_on';h.other='zg361_freq_yearly'
    h.open=True;h.keep_open=False;h.change_other=False;h.calls=[]
    h.capabilities=lambda:{'binding':{'bridge_pid':123,'connection_generation':1}}
    def primitive(step,**kwargs):
        h._request_sequence+=1;h.calls.append((step,kwargs))
        if step==CONTRACT['QUERY_FRONTEND_GAME_RULES_WINDOW_V1_STEP']:return window(h.open)
        if step==QUERY['QUERY_FRONTEND_GAME_RULE_SELECTIONS_V1_STEP']:return values(h.current,h.other)
        if step==CONTRACT['SELECT_FRONTEND_GAME_RULE_V1_STEP']:
            h.current=kwargs['request_fields']['desired_setting_key']
            if h.change_other:h.other='zg361_freq_three_year'
            return ack()
        if step in {CONTRACT['APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_STEP'],CONTRACT['HIDE_FRONTEND_GAME_RULES_V1_STEP']}:
            h.open=h.keep_open
            return ack('apply_and_hide' if step==CONTRACT['APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_STEP'] else 'hide')
        raise AssertionError(step)
    h._execute_primitive_step=primitive
    return h


class GameRulesControlContractTests(unittest.TestCase):
    def test_real_visible_and_closed_window_states(self):
        normalize=CONTRACT['normalize_frontend_game_rules_window_v1']
        self.assertTrue(normalize(window())['may_edit'])
        self.assertTrue(normalize(window(False))['window_closed_proven'])
        unavailable={**window(False),'ready':False,'unavailable_reason':'bookmarks_route_unavailable',
            'window_enabled':False,'is_host':False,'window_closed_proven':False}
        self.assertFalse(normalize(unavailable)['window_closed_proven'])

    def test_twelve_invalid_window_observations(self):
        patches=[{'game_version':'1.20.0.2'},{'schema_version':True},{'uses_ocr':True},
            {'applied_settings_proven':True},{'window_visible':1},{'may_edit':False},
            {'window_closed_proven':True},{'ready':False},{'is_host':False},
            {'game_has_started':True},{'backend_id':'visual'},{'unavailable_reason':'guessed value'}]
        for patch in patches:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                CONTRACT['normalize_frontend_game_rules_window_v1']({**window(),**patch})

    def test_seven_invalid_action_acknowledgements(self):
        patches=[{'action':'hide'},{'window_closed_proven':True},{'native_next_calls':512},
            {'native_next_calls':True},{'selection_verified':False},{'apply_invoked':True},
            {'applied_settings_proven':True}]
        for patch in patches:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                CONTRACT['normalize_frontend_game_rules_mutation_v1']({**ack(),**patch},'select')

    def test_script_keys_are_explicit_bounded_identifiers(self):
        for key in ['',True,1,'x y','x'*97,'0x123->ptr']:
            with self.subTest(key=key),self.assertRaises(ValueError):CONTRACT['require_game_rule_script_key'](key)

    def test_driver_sends_only_three_keys_and_checks_actual_selected_value(self):
        h=driver_harness();result=h.select_frontend_game_rule_v1('zg361_enabled','zg361_on','zg361_off')
        actions=[c for c in h.calls if c[0]==CONTRACT['SELECT_FRONTEND_GAME_RULE_V1_STEP']]
        self.assertEqual(len(actions),1)
        self.assertEqual(actions[0][1]['request_fields'],{'rule_key':'zg361_enabled',
            'expected_current_setting_key':'zg361_on','desired_setting_key':'zg361_off'})
        self.assertEqual(result['observation']['selections'][0]['selected_setting_key'],'zg361_off')
        self.assertFalse(result['applied_settings_proven'])

    def test_driver_stale_current_value_never_submits_next(self):
        h=driver_harness()
        with self.assertRaises(ValueError):h.select_frontend_game_rule_v1('zg361_enabled','zg361_off','zg361_on')
        self.assertFalse(any(c[0]==CONTRACT['SELECT_FRONTEND_GAME_RULE_V1_STEP'] for c in h.calls))

    def test_driver_rejects_unrelated_rule_change_after_next(self):
        h=driver_harness();h.change_other=True
        with self.assertRaises(RuntimeError):h.select_frontend_game_rule_v1('zg361_enabled','zg361_on','zg361_off')
        self.assertEqual(sum(c[0]==CONTRACT['SELECT_FRONTEND_GAME_RULE_V1_STEP'] for c in h.calls),1)

    def test_apply_requires_later_actual_closure_and_keeps_applied_false(self):
        h=driver_harness();r=h.apply_and_hide_frontend_game_rules_v1()
        action_index=next(i for i,c in enumerate(h.calls) if c[0]==CONTRACT['APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_STEP'])
        self.assertEqual(h.calls[action_index+1][0],CONTRACT['QUERY_FRONTEND_GAME_RULES_WINDOW_V1_STEP'])
        self.assertTrue(r['window_closed_proven']);self.assertFalse(r['applied_settings_proven'])
        self.assertFalse(r['acknowledgement']['window_closed_proven'])

    def test_apply_ack_without_closed_window_does_not_pass_or_resubmit(self):
        h=driver_harness();h.keep_open=True
        with self.assertRaises(RuntimeError):h.apply_and_hide_frontend_game_rules_v1()
        self.assertEqual(sum(c[0]==CONTRACT['APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_STEP'] for c in h.calls),1)

    def test_hide_has_distinct_native_action_and_independent_closure(self):
        h=driver_harness();r=h.hide_frontend_game_rules_v1()
        self.assertTrue(r['window_closed_proven'])
        self.assertTrue(any(c[0]==CONTRACT['HIDE_FRONTEND_GAME_RULES_V1_STEP'] for c in h.calls))
        self.assertFalse(any(c[0]==CONTRACT['APPLY_AND_HIDE_FRONTEND_GAME_RULES_V1_STEP'] for c in h.calls))


if __name__=='__main__':unittest.main()
