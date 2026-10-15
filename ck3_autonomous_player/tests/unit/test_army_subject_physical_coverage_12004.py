"""Owned subject wire to strict normalizer and independent raw-delta consumer."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.army_observed_phase_contract_12004 import (
    _SHAPES, normalize_army_observed_phase_family_12004 as normalize,
)
from xar_autoplayer.bridge.army_observed_phase_consumption_12004 import project_army_observed_phases_12004
from xar_autoplayer.bridge.army_scoped_ordered_refill_contract import _RAW, _CONTEXT, _MAGIC, _BOOL
from xar_autoplayer.simulation.army_actual_regular_core_stage_12004 import map_actual_regular_core_entry_12004

CORE='actual_army_regular_core_observations_v1'
SUBJECT=-2130706431
P1,P2,P3=0x12000003,0x13000004,0x14000005
ARMY,FOREIGN,ARRG=0x1000,0x2000,0x3000
T1,T2,T3=0x4000,0x5000,0x6000
OMISSION='scoped_capture_omits_unselected_physical_context'

def shape(kind):
    if kind.endswith('?'):return None
    if kind.endswith('[]'):return []
    if kind in _SHAPES:return {key:shape(child) for key,child in _SHAPES[kind].items()}
    if kind=='bool':return False
    if kind=='str':return ''
    if kind[0] in 'ui':return 0
    raise ValueError(kind)

def token(sequence):return {'clock_identity':0x7000,'sequence':sequence,'thread_id':37}

def occurrence(index, full, physical):
    return {'stored_index':index,'raw_full_id':full,'resolved_full_id':full,
            'physical_token':physical,'used_fallback':False,'unavailable_reason':''}

def persistent(full, physical, *, returned=False):
    chunks=[]
    for index in range(7):
        chunk={key:None for key in _CONTEXT+_MAGIC+_BOOL}
        chunk.update({key:0 for key in _RAW})
        chunk.update(physical_index=index,current_soldiers=40+index,maximum_soldiers=100+index,
            owner_persistent_regiment_id=full,q_ordinal_raw=index,army_regiment_id_raw=0x15000006,
            context_unavailable_reason='optional_political_context_unavailable')
        if returned and full==P1 and index==0:chunk['current_soldiers']+=6
        if returned and full==P2 and index==1:chunk['current_soldiers']-=3
        chunks.append(chunk)
    return {'physical_token':physical,'resolved_full_id':full,'unavailable_reason':'',
        'physical_values':{'persistent_regiment_id':full,'prepared_fraction_raw':None,
            'unavailable_reason':None,'chunks':chunks}}

def frame(*,returned=False):
    value=shape('CoreFrame')
    value.update(native_persistent_occurrence_count=3,native_army_refresh_occurrence_count=3,
        capture_complete=False,missing_inputs=[OMISSION,'optional_context_is_unknown'])
    value['persistent_occurrences']=[occurrence(0,P1,T1),occurrence(1,P1,T1),occurrence(2,P3,T3)]
    value['army_refresh_occurrences']=[occurrence(0,SUBJECT,ARMY),occurrence(1,SUBJECT,ARMY),occurrence(2,8,FOREIGN)]
    value['persistent_objects']=[persistent(P1,T1,returned=returned),persistent(P2,T2,returned=returned)]
    records=[{'record_index':i,'persistent_regiment_id':p,'chunk_index':slot,
              'persistent_physical_token':physical,'state_raw':0,
              'native_record_admitted':True,'unavailable_reason':''}
             for i,(p,slot,physical) in enumerate([(P1,0,T1),(P2,1,T2),(P1,0,T1)])]
    arrg={'occurrence':occurrence(0,0x15000006,ARRG),'resolved_magic_14_raw':0x41725267,
          'native_refresh_admitted':True,'native_loss_writer_skipped':False,
          'native_record_count':3,'records_complete':True,'unavailable_reason':'','records':records}
    value['army_objects']=[{'physical_token':ARMY,'resolved_full_id':SUBJECT,
        'native_arrg_occurrence_count':1,'unavailable_reason':'','arrg_occurrences':[arrg]}]
    value['subject_coverage_v1']={'schema_version':1,'mode':'explicit_full_carmy_physical_closure',
        'scope_epoch':5,'bound_game_state_identity':0x8000,'bound_owner_character_id':101,
        'requested_full_carmy_ids':[SUBJECT],'manager_occurrences_complete':True,
        'physical_closure_complete':True,'subject_identity_witnesses':[{
            'full_carmy_id':SUBJECT,'resolved_full_carmy_id':SUBJECT,'carmy_magic_14_raw':0x41726D79,
            'public_unit_id':-2113929215,'unit_resolved_full_id':-2113929215,'unit_magic_14_raw':0x556E6974,
            'unit_owner_character_id':101,'unit_full_carmy_id':SUBJECT}], 'missing_inputs':[]}
    return value

def family():
    event=shape('CoreEvent')
    scope=shape('Scope')
    scope.update(observed=True,phase='post_date',actual_entry_rva=0x2A9A570,
        primary_manager_identity=0x9000,secondary_manager_identity=0x9008,
        game_state_identity=0x8000,date_raw=123,entry_event=token(10),saved_mask02_admitted=True,
        saved_c0_observed_rva=0x2A9A8E2,saved_c0_event=token(21))
    scope['original_army_roster'].update(boundary='parent_entry',capture_rva=0x2A9A570,
        capture_event=token(10),count=3,complete=True,ordered_full_ids=[SUBJECT & 0xFFFFFFFF,SUBJECT & 0xFFFFFFFF,8])
    event.update(journal_sequence=1,manager_identity=0x9000,caller_return_rva=0x2A9A8E2,
        observed=True,original_called=True,original_returned=True,entry_provenance_complete=True,
        return_provenance_complete=True,parent_scope=scope,entry_event=token(20),returned_event=token(30),
        entry_date_raw=123,returned_date_raw=123,entry=frame(),returned=frame(returned=True))
    return {'schema_version':1,'source':'native_natural_army_regular_core_entry_return',
        'membership_basis':'captured_core_entry_resolved_Army_roster_full_ID','observer_initialized':True,
        'observer_installed':True,'latest_journal_sequence':1,'overwritten_events':0,
        'publication_failures':0,'events':[event]}

def consume(value):
    normalized=normalize(CORE,value,expected_carmy_id=SUBJECT)
    row={'army_id':901,'native_carmy_id':SUBJECT,CORE:normalized}
    return normalized,project_army_observed_phases_12004(row,exact_source=True)

def delta(value):return consume(value)[1]['ordered_regular_core'][0]['subject_raw_physical_delta_v1']

class SubjectPhysicalCoverageTests(unittest.TestCase):
    def test_actual_normalizer_preserves_owned_input_and_produces_raw_delta_only(self):
        value=family();before=deepcopy(value)
        normalized,consumed=consume(value)
        self.assertEqual(value,before)
        self.assertEqual(normalized,before)
        self.assertIsNot(normalized,value)
        core=consumed['ordered_regular_core'][0]
        result=core['subject_raw_physical_delta_v1']
        self.assertEqual(result['status'],'available')
        self.assertEqual(len(result['physical_objects']),2)
        self.assertEqual([len(p['chunks']) for p in result['physical_objects']],[7,7])
        self.assertEqual(result['physical_objects'][0]['chunks'][0]['delta_current_soldiers'],6)
        self.assertEqual(result['physical_objects'][1]['chunks'][1]['delta_current_soldiers'],-3)
        self.assertIsNone(core['conditional_entry_projection'])
        self.assertEqual(core['missing_inputs'],['actual_core_complete_entry_copy'])
        self.assertFalse(result['actual_ADD_observed'] or result['causal_attribution_ready']
            or result['full_manager_ready'] or result['full_monthly_ready'] or consumed['full_monthly_ready'])

    def test_absent_field_preserves_legacy_normalization_and_consumer_output(self):
        value=family()
        for event in value['events']:
            for name in ('entry','returned'):event[name].pop('subject_coverage_v1')
        normalized,consumed=consume(value)
        self.assertEqual(normalized,value)
        self.assertNotIn('subject_raw_physical_delta_v1',consumed['ordered_regular_core'][0])
        self.assertIsNone(consumed['ordered_regular_core'][0]['conditional_entry_projection'])

    def test_duplicate_occurrences_data_alias_and_foreign_physical_are_preserved_not_summed_twice(self):
        normalized,consumed=consume(family());f=normalized['events'][0]['entry']
        self.assertEqual(len(f['persistent_occurrences']),3)
        self.assertEqual(len(f['army_refresh_occurrences']),3)
        self.assertEqual(len(f['army_objects'][0]['arrg_occurrences'][0]['records']),3)
        self.assertEqual([p['persistent_full_id'] for p in consumed['ordered_regular_core'][0]['subject_raw_physical_delta_v1']['physical_objects']],[P1,P2])

    def test_unknown_optional_context_does_not_require_prepared148_or_full_global_materialization(self):
        value=family();result=delta(value)
        self.assertEqual(result['status'],'available')
        self.assertTrue(value['events'][0]['entry']['missing_inputs'])
        self.assertIsNone(value['events'][0]['entry']['persistent_objects'][0]['physical_values']['prepared_fraction_raw'])
        self.assertIsNone(map_actual_regular_core_entry_12004(value['events'][0])['entry'])

    def test_exact_optional_shape_and_uint_bool_types(self):
        for mutation in (lambda c:c.update(extra=True),lambda c:c.update(scope_epoch=True),
                         lambda c:c.update(scope_epoch=0),lambda c:c.update(schema_version=2),
                         lambda c:c.update(mode='full_manager'),lambda c:c.update(requested_full_carmy_ids=[]),
                         lambda c:c.update(requested_full_carmy_ids=[SUBJECT,SUBJECT]),
                         lambda c:c.update(requested_full_carmy_ids=[-1]),
                         lambda c:c.update(missing_inputs=['','']),lambda c:c.update(missing_inputs=['x','x'])):
            value=family();mutation(value['events'][0]['entry']['subject_coverage_v1'])
            with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_false_complete_identity_witness_is_rejected(self):
        for key,bad in [('resolved_full_carmy_id',SUBJECT+1),('carmy_magic_14_raw',0),
                        ('unit_magic_14_raw',0),('unit_resolved_full_id',12),
                        ('unit_owner_character_id',202),('unit_full_carmy_id',SUBJECT+1),('public_unit_id',-1)]:
            value=family();value['events'][0]['entry']['subject_coverage_v1']['subject_identity_witnesses'][0][key]=bad
            with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_unknown_witness_is_preserved_only_when_local_closure_not_complete(self):
        value=family();c=value['events'][0]['entry']['subject_coverage_v1']
        c.update(physical_closure_complete=False,missing_inputs=['identity_read_failed'])
        c['subject_identity_witnesses'][0]['resolved_full_carmy_id']=None
        normalized,consumed=consume(value)
        self.assertIsNone(normalized['events'][0]['entry']['subject_coverage_v1']['subject_identity_witnesses'][0]['resolved_full_carmy_id'])
        self.assertEqual(consumed['ordered_regular_core'][0]['subject_raw_physical_delta_v1']['status'],'unavailable')

    def test_requested_generation_outside_scope_and_fallback_are_rejected(self):
        value=family()
        with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT+1)
        value['events'][0]['entry']['army_refresh_occurrences'][0]['used_fallback']=True
        with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_false_complete_manager_roster_is_rejected(self):
        value=family();value['events'][0]['entry']['native_persistent_occurrence_count']=4
        with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_scoped_frame_can_never_promote_global_complete(self):
        for mutate in (lambda f:f.update(capture_complete=True),lambda f:f.update(missing_inputs=[])):
            value=family();mutate(value['events'][0]['entry'])
            with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_missing_physical_seven_or_incomplete_data_cannot_qualify(self):
        for mutate in (lambda f:f['persistent_objects'][0]['physical_values']['chunks'].pop(),
                       lambda f:f['persistent_objects'].pop(),
                       lambda f:f['army_objects'][0]['arrg_occurrences'][0].update(records_complete=False)):
            value=family();mutate(value['events'][0]['entry'])
            with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_explicit_coverage_missing_and_manager_incomplete_disable_delta_without_losing_raw(self):
        for mutate in (lambda c:c.update(missing_inputs=['bounded_copy']),
                       lambda c:c.update(manager_occurrences_complete=False),
                       lambda c:c.update(physical_closure_complete=False)):
            value=family();mutate(value['events'][0]['entry']['subject_coverage_v1'])
            normalized,consumed=consume(value)
            self.assertEqual(normalized,value)
            self.assertEqual(consumed['ordered_regular_core'][0]['subject_raw_physical_delta_v1']['status'],'unavailable')

    def test_scope_epoch_state_or_owner_change_disables_pair(self):
        for key,bad in [('scope_epoch',6),('bound_game_state_identity',0x8001),('bound_owner_character_id',102)]:
            value=family();c=value['events'][0]['returned']['subject_coverage_v1'];c[key]=bad
            if key=='bound_owner_character_id':c['subject_identity_witnesses'][0]['unit_owner_character_id']=bad
            self.assertEqual(delta(value)['status'],'unavailable')

    def test_requested_list_and_witness_order_remain_exact_across_frames(self):
        value=family()
        for name in ('entry','returned'):
            f=value['events'][0][name];c=f['subject_coverage_v1']
            c['requested_full_carmy_ids'].append(8)
            c['subject_identity_witnesses'].append({'full_carmy_id':8,'resolved_full_carmy_id':8,
                'carmy_magic_14_raw':0x41726D79,'public_unit_id':7,'unit_resolved_full_id':7,
                'unit_magic_14_raw':0x556E6974,'unit_owner_character_id':101,'unit_full_carmy_id':8})
            f['army_objects'].append({'physical_token':FOREIGN,'resolved_full_id':8,
                'native_arrg_occurrence_count':0,'unavailable_reason':'','arrg_occurrences':[]})
        self.assertEqual(delta(value)['status'],'available')
        coverage=value['events'][0]['returned']['subject_coverage_v1']
        coverage['requested_full_carmy_ids'].reverse()
        coverage['subject_identity_witnesses'].reverse()
        self.assertEqual(delta(value)['status'],'unavailable')
        coverage['subject_identity_witnesses'].reverse()
        with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_pointer_or_generation_change_cannot_be_raw_delta(self):
        for kind in ('army','persistent_pointer','persistent_generation'):
            value=family();f=value['events'][0]['returned']
            if kind=='army':
                for row in f['army_refresh_occurrences'][:2]:row['physical_token']=0x1001
                f['army_objects'][0]['physical_token']=0x1001
            elif kind=='persistent_pointer':
                for row in f['persistent_occurrences'][:2]:row['physical_token']=0x4001
                f['persistent_objects'][0]['physical_token']=0x4001
                for row in f['army_objects'][0]['arrg_occurrences'][0]['records']:
                    if row['persistent_regiment_id']==P1:row['persistent_physical_token']=0x4001
            else:
                changed=P1+0x1000000
                for row in f['persistent_occurrences'][:2]:row['raw_full_id']=row['resolved_full_id']=changed
                p=f['persistent_objects'][0];p['resolved_full_id']=changed;p['physical_values']['persistent_regiment_id']=changed
                for row in f['army_objects'][0]['arrg_occurrences'][0]['records']:
                    if row['persistent_regiment_id']==P1:row['persistent_regiment_id']=changed
            self.assertEqual(delta(value)['status'],'unavailable')

    def test_no_return_coverage_or_provenance_never_fills_entry(self):
        value=family();value['events'][0]['returned'].pop('subject_coverage_v1')
        self.assertEqual(delta(value)['status'],'unavailable')
        value=family();value['events'][0]['return_provenance_complete']=False
        self.assertEqual(delta(value)['status'],'unavailable')

    def test_clock_date_or_parent_mismatch_is_rejected_by_existing_guard(self):
        for mutate in (lambda e:e['returned_event'].update(thread_id=38),
                       lambda e:e.update(returned_date_raw=124),
                       lambda e:e['parent_scope'].update(primary_manager_identity=0x9001)):
            value=family();mutate(value['events'][0])
            with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_control_bound_64_subjects_does_not_shrink_full_manager_roster_bound(self):
        value=family()
        for name in ('entry','returned'):
            f=value['events'][0][name];c=f['subject_coverage_v1']
            c['requested_full_carmy_ids']=[SUBJECT]+list(range(1,64))
            by_id={8:FOREIGN}
            for full in range(1,64):
                if full!=8:
                    by_id[full]=0x10000+full*16
                    f['army_refresh_occurrences'].append(occurrence(len(f['army_refresh_occurrences']),full,by_id[full]))
            f['native_army_refresh_occurrence_count']=len(f['army_refresh_occurrences'])
            order=[8]+[full for full in range(1,64) if full!=8]
            for full in order:
                f['army_objects'].append({'physical_token':by_id[full],'resolved_full_id':full,
                    'native_arrg_occurrence_count':0,'unavailable_reason':'','arrg_occurrences':[]})
            for full in range(1,64):
                c['subject_identity_witnesses'].append({'full_carmy_id':full,'resolved_full_carmy_id':full,
                    'carmy_magic_14_raw':0x41726D79,'public_unit_id':1000+full,'unit_resolved_full_id':1000+full,
                    'unit_magic_14_raw':0x556E6974,'unit_owner_character_id':101,'unit_full_carmy_id':full})
        self.assertGreater(value['events'][0]['entry']['native_army_refresh_occurrence_count'],64)
        self.assertEqual(delta(value)['status'],'available')
        value['events'][0]['entry']['subject_coverage_v1']['requested_full_carmy_ids'].append(64)
        with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_zero_bound_owner_cannot_qualify_even_when_unit_witness_agrees(self):
        value=family();c=value['events'][0]['entry']['subject_coverage_v1']
        c['bound_owner_character_id']=0;c['subject_identity_witnesses'][0]['unit_owner_character_id']=0
        with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)

    def test_character_override_without_data_retains_raw_but_cannot_claim_local_delta(self):
        value=family()
        for name in ('entry','returned'):
            arrg=value['events'][0][name]['army_objects'][0]['arrg_occurrences'][0]
            arrg.update(native_loss_writer_skipped=True,records_complete=True,records=[])
        with self.assertRaises(ValueError):normalize(CORE,value,expected_carmy_id=SUBJECT)
        for name in ('entry','returned'):
            value['events'][0][name]['subject_coverage_v1'].update(physical_closure_complete=False,
                missing_inputs=['subject_character_override_has_no_physical_DATA_closure'])
        normalized,consumed=consume(value)
        self.assertEqual(normalized,value)
        self.assertEqual(consumed['ordered_regular_core'][0]['subject_raw_physical_delta_v1']['status'],'unavailable')

if __name__=='__main__':unittest.main()
