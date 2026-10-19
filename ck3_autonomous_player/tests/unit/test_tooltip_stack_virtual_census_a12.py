"""Actual R32 RED projection; offline Python parsing only, no native invocation."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.ingame_ui_contract import normalize_ui_result
from xar_autoplayer.bridge.version_identity import CK3_12003, CK3_12004

FIXTURE=Path(__file__).with_name('fixtures')/'tooltip_stack_unavailable_r32_actual.json'

def actual():
    d=json.loads(FIXTURE.read_text(encoding='utf-8'))
    return d['result'],dict(d['normalizer_call'],expected_build=CK3_12004)

def observed_virtual():
    value,kwargs=actual()
    value.update(accepted=True,available=True,status='observed',unavailable_reason='',
        window_exists=True,enabled=True)
    value['tree']['scope_root_name']='tooltip_stack'
    leaf=value['presentation_ui']
    leaf.update(available=True,status='observed',unavailable_reason=None,
        receipt_id='a'*32,observation_owner_epoch=value['pump_epoch'])
    leaf['tooltip_clear'].update(available=True,phase='observed',active_count=0,deferred=False)
    return value,kwargs

class TooltipStackVirtualCensusA12Tests(unittest.TestCase):
    def test_actual_unavailable_empty_scope_preserves_native_red(self):
        value,kwargs=actual();before=copy.deepcopy(value)
        result=normalize_ui_result(value,**kwargs)
        self.assertEqual(result,before)
        self.assertFalse(result['available'])
        self.assertEqual(result['unavailable_reason'],'tooltip_stack_exact_source_or_owner_frame_unverified')
        self.assertIsNone(result['presentation_ui']['receipt_id'])
        self.assertFalse(result['native_dispatch_attempted'])

    def test_virtual_empty_census_rejects_root_rows_truncation_and_other_scope(self):
        for field,new in [('root_available',True),('truncated',True),('scope_root_name','army_window')]:
            value,kwargs=actual();value['tree'][field]=new
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'empty virtual-window census'):
                normalize_ui_result(value,**kwargs)
        value,kwargs=actual()
        value['tree'].update(widget_count=1,widgets=[{'runtime_name':'tooltip_stack','child_path':'','depth':0,
            'child_count':0,'vtable_rva':1,'effective_visible':False,'enabled':False}])
        with self.assertRaisesRegex(ValueError,'empty virtual-window census'):
            normalize_ui_result(value,**kwargs)

    def test_available_scope_strict_and_later_unavailable_scope_retained(self):
        value,kwargs=observed_virtual()
        self.assertTrue(normalize_ui_result(value,**kwargs)['available'])
        value['tree']['scope_root_name']=''
        with self.assertRaisesRegex(ValueError,'empty virtual-window census'):
            normalize_ui_result(value,**kwargs)
        value,kwargs=actual()
        value['tree']['scope_root_name']='tooltip_stack'
        self.assertFalse(normalize_ui_result(value,**kwargs)['available'])

    def test_original_army_unopened_ack_empty_census_guard_unchanged(self):
        import test_ingame_ui_navigation_v1 as helper
        for build in (CK3_12003,CK3_12004):
            value=helper.current_result('select_army',0,unopened=True)
            value.update(game_version=build.game_version,executable_sha256=build.executable_sha256,
                native_backend_id=build.backend_id('ingame-ui-v1'))
            kwargs=dict(operation='select_army',kind='army',subject_id=0,native_revision=3,date_raw=53146848,
                actor_id=29829,expected_build=build)
            self.assertTrue(normalize_ui_result(value,**kwargs)['verification_pending'])
            value['tree'].update(widget_count=1,widgets=[{'runtime_name':'army_window','child_path':'','depth':0,
                'child_count':0,'vtable_rva':1,'effective_visible':False,'enabled':False}])
            with self.subTest(build=build.game_version),self.assertRaisesRegex(ValueError,'unopened army ACK must keep an empty target-window census'):
                normalize_ui_result(value,**kwargs)

if __name__=='__main__':unittest.main()
