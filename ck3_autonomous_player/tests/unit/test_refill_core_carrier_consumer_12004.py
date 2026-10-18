"""Constructed producer-shaped packets exercise joins; never live qualification."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'ck3_autonomous_player'
SPEC = importlib.util.spec_from_file_location(
    'carrier_contract_under_test', BASE / 'src/xar_autoplayer/bridge/army_instruction_local_refill_add_12004.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def wire(rows):
    return ('\n'.join(json.dumps(row, separators=(',', ':')) for row in rows) + '\n').encode()


def event(sequence):
    return {'clock_identity':0x8000000000000001, 'sequence':sequence, 'thread_id':456}


def occurrence(identity, pointer):
    return {'stored_index':0, 'raw_full_id':identity, 'resolved_full_id':identity,
            'physical_token':pointer, 'used_fallback':False, 'unavailable_reason':''}


def complete_frame(binding, current):
    regi = m._i32(binding['regi_full_id_u32'])
    arrg = binding['arrg_full_id_i32']; army = binding['army_full_id_i32']
    chunks = []
    context = ('owner_resolved_full_id owner_guard_138_raw origin_province_id origin_province_788_raw '
               'origin_province_73c_raw associated_arrg_resolved_full_id associated_army_raw_full_id '
               'associated_army_resolved_full_id army_byte_1d4_raw army_byte_1ec_raw associated_unit_raw_full_id '
               'associated_unit_resolved_full_id unit_170_raw unit_position_owner_resolved_full_id '
               'unit_position_holder_resolved_full_id owner_definition_magic_38_raw associated_arrg_magic_raw '
               'unit_position_province_magic_raw native_army_in_combat native_unit_position_eligible').split()
    for i in range(7):
        chunks.append(dict.fromkeys(context, None) | {
            'physical_index':i, 'current_soldiers':current if i == 2 else 0, 'maximum_soldiers':100,
            'owner_persistent_regiment_id':regi, 'q_ordinal_raw':5, 'army_regiment_id_raw':arrg,
            'exclusion_byte_14_raw':0, 'state_raw':1, 'context_unavailable_reason':'not required for raw closure'})
    return {
        'native_persistent_occurrence_count':1, 'native_army_refresh_occurrence_count':1,
        'capture_complete':True, 'persistent_occurrences':[occurrence(regi, 0x200000000)],
        'army_refresh_occurrences':[occurrence(army, 0x600000000)],
        'persistent_objects':[{'physical_token':0x200000000, 'resolved_full_id':regi,
            'unavailable_reason':'', 'physical_values':{'persistent_regiment_id':regi,
                'prepared_fraction_raw':100000, 'unavailable_reason':None, 'chunks':chunks}}],
        'army_objects':[{'physical_token':0x600000000, 'resolved_full_id':army,
            'native_arrg_occurrence_count':1, 'unavailable_reason':'', 'arrg_occurrences':[
                {'occurrence':occurrence(arrg, 0x500000000), 'resolved_magic_14_raw':0x41725267,
                 'native_refresh_admitted':True, 'native_loss_writer_skipped':False,
                 'native_record_count':1, 'records_complete':True, 'unavailable_reason':'',
                 'records':[{'record_index':0, 'persistent_regiment_id':regi, 'chunk_index':2,
                     'persistent_physical_token':0x200000000, 'state_raw':1,
                     'native_record_admitted':True, 'unavailable_reason':''}]}]}],
        'missing_inputs':[],
    }


def sample():
    binding = {'schema':m._BINDING_V2_SCHEMA, 'machine_id':'constructed-not-live',
        'exact_executable_sha256':m.EXE_SHA256, 'pid':123, 'process_created_filetime':999,
        'thread_id':456, 'regi_full_id_u32':0x81000042, 'physical_slot':2,
        'arrg_full_id_i32':m._i32(0x82000055), 'army_full_id_i32':m._i32(0x83000066),
        'connection_generation':1, 'episode_run_id':'unit-constructed-not-live',
        'source_admission_receipt_sha256':'a'*64, 'observer_build_and_SYSTEM_gate_receipt_sha256':'b'*64,
        'carrier_module_path':'D:/constructed/xar_ck3_bridge.dll', 'carrier_source_epoch':20261018,
        'source_dir':'D:/constructed/refill_add_live_12004'}
    frame = dict(zip(m._CARRIER_WORDS, (2,456,1,0xF000000000000001,0,1,
        event(20)['clock_identity'],20,456,event(10)['clock_identity'],10,456,
        53148912,0x700000000,0x700000008,0x800000000,0x2A9A8E2,0x2A9A570,1,1,3)))
    start = {'kind':'start', 'schema':m._V4_SCHEMA, 'machine_id':binding['machine_id'],
        'exact_exe_sha256_basis':'external-frozen-runtime-admission', 'pid':123,
        'process_created_filetime':999, 'module_base':'0x140000000', 'fixture':False,
        'thread_id':456, 'regi_full_id_u32':binding['regi_full_id_u32'], 'physical_slot':2,
        'timeout_ms':1000, 'verified_site_0_hex':'0150f4', 'verified_site_1_hex':'8b48f43b48f0',
        'carrier_module_path':binding['carrier_module_path'], 'carrier_module_base':'0x180000000',
        'carrier_export_rva':'0x10000', 'carrier_address':'0x180010000',
        'carrier_source_epoch':20261018, 'carrier_header_64_hex':m._CARRIER_HEADER_HEX}
    rows = [start]
    for i, current in enumerate((80,90)):
        seven = bytearray(252)
        struct.pack_into('<II', seven, 2*36, 100, current)
        struct.pack_into('<ii', seven, 2*36+12, 5, binding['arrg_full_id_i32'])
        rows.append({'kind':'raw_ADD_boundary', 'machine_id':binding['machine_id'],
            'site_rva':('0x2A98B88','0x2A98B8B')[i], 'pid':123, 'thread_id':456,
            'event_ordinal':i+1, 'debug_event_ordinal':i+10, 'qpc':i+100,
            'regi_pointer':'0x200000000', 'regi_full_id_u32':binding['regi_full_id_u32'],
            'physical_slot':2, 'rax_anchor':'0x200000070', 'rsp':'0x300000000',
            'core_caller_raw':'0x140001234', 'manager_iterator':'0x400000000',
            'q_index':5, 'q_u32':10, 'q_i32':10, 'current_u32':current, 'maximum_u32':100,
            'physical_complete':True, 'native_core_token':frame['invocation_token'],
            'natural_parent_token':None, 'natural_attribution_ready':False,
            'arrg_raw':binding['arrg_full_id_i32'], 'arrg_resolved':binding['arrg_full_id_i32'],
            'arrg_pointer':'0x500000000', 'army_raw':binding['army_full_id_i32'],
            'army_resolved':binding['army_full_id_i32'], 'data_count':1,
            'associated_ArRg_DATA_complete':True,
            'DATA':[{'stored_index':0, 'raw0':binding['regi_full_id_u32'], 'raw4':2,
                'persistent_full_id_u32':binding['regi_full_id_u32'], 'physical_ordinal_u32':2}],
            'physical_seven_hex':seven.hex(), 'stack_q_source_complete':True,
            'stack_q_window_28_hex':struct.pack('<7I', 0,0,0,0,0,10,0).hex(),
            'core_carrier_v1':{'module_path':binding['carrier_module_path'],
                'module_base':'0x180000000', 'export_rva':'0x10000', 'directory_address':'0x180010000',
                'source_epoch':20261018, 'header_64_hex':m._CARRIER_HEADER_HEX,
                'slot_index':3, 'slot_address':'0x180010238', 'first_168_hex':'',
                'second_168_hex':'', 'stable_active':True, 'frame':copy.deepcopy(frame),
                'owners_complete':True, 'owner_matches':1, 'header_complete':True,
                'first_complete':True, 'second_complete':True, 'diagnostic':'stable_active'}})
        repack(rows[-1])
    rows += [{'kind':'physical_ADD_pair', 'machine_id':binding['machine_id'], 'actual_ADD_observed':True,
        'native_instruction_replayed_by_probe':False, 'q_i32':10, 'before_current_u32':80,
        'after_current_u32':90, 'DWORD_wrap_matches':True, 'associated_DATA_pair_complete':True,
        'natural_parent_token':None, 'natural_attribution_ready':False, 'full_window_coverage_ready':False,
        'native_core_token':frame['invocation_token'], 'carrier_pair_same_token':True},
        {'kind':'debug_hit_budget', 'debug_hits':11, 'limit':100000},
        {'kind':'terminal', 'status':'paired', 'reason':'paired', 'debug_registers_cleared':True,
         'detached':True, 'hit_count':2}]
    scope = {'observed':True, 'phase':'post_date', 'actual_entry_rva':0x2A9A570,
        'caller_return_rva':0x1234, 'primary_manager_identity':0x700000000,
        'secondary_manager_identity':0x700000008, 'game_state_identity':0x800000000,
        'session_identity':None, 'entry_event':event(10), 'date_raw':53148912,
        'prefix_date_raw':None, 'absolute_day_raw':1, 'entry_c0_raw':0, 'saved_c0_raw':None,
        'saved_mask02_admitted':True, 'saved_c0_observed_rva':0x2A9A8E2, 'saved_c0_event':event(21),
        'original_army_roster':{'boundary':'parent_entry', 'capture_rva':0x2A9A570,
            'capture_event':event(11), 'begin_identity':0x900000000, 'end_identity':0x900000004,
            'count':1, 'complete':True, 'ordered_full_ids':[binding['army_full_id_i32'] & 0xFFFFFFFF]}}
    core = {'journal_sequence':1, 'manager_identity':0x700000000, 'caller_return_rva':0x2A9A8E2,
        'raw_return_bits':0, 'entry_date_raw':53148912, 'returned_date_raw':53148912,
        'observed':True, 'original_called':True, 'original_returned':True,
        'entry_provenance_complete':True, 'return_provenance_complete':True,
        'parent_scope':scope, 'entry_event':event(20), 'returned_event':event(30),
        'entry':complete_frame(binding,80), 'returned':complete_frame(binding,90),
        'provenance_failures':[], 'native_core_invocation_token':frame['invocation_token'],
        'parent_invocation_token':None, 'core_invocation_nesting_depth':1,
        'core_carrier_published':True, 'core_carrier_source_epoch':20261018}
    return rows, binding, core


def repack(hit):
    carrier = hit['core_carrier_v1']
    payload = struct.pack('<21Q', *(carrier['frame'][name] for name in m._CARRIER_WORDS)).hex()
    carrier['first_168_hex'] = carrier['second_168_hex'] = payload


def legacy(rows, binding, version):
    rows = copy.deepcopy(rows); binding = dict(binding)
    binding['schema'] = m.BINDING_SCHEMA
    for key in ('carrier_module_path','carrier_source_epoch','source_dir'): del binding[key]
    rows[0]['schema'] = m.RAW_SCHEMA if version == 2 else 'xar.ck3.refill_ADD_12004.hwprobe_raw.v3'
    for key in tuple(rows[0]):
        if key.startswith('carrier_'): del rows[0][key]
    for hit in rows[1:3]:
        del hit['core_carrier_v1']; hit['native_core_token'] = None
        if version == 2:
            del hit['stack_q_source_complete']; del hit['stack_q_window_28_hex']
    del rows[3]['carrier_pair_same_token']; del rows[3]['native_core_token']
    return rows, binding


class CarrierConsumerTests(unittest.TestCase):
    def normalize(self, rows, binding, core):
        return m.normalize_instruction_local_refill_add_12004(wire(rows),binding,core_observation=core)

    def test_actual_shaped_high_bit_ids_and_token_join_only(self):
        rows,binding,core = sample(); raw = wire(rows)
        item = self.normalize(rows,binding,core)
        self.assertEqual(item['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(item['owner_binding'], binding)
        self.assertEqual(item['native_core_token'], 0xF000000000000001)
        self.assertEqual(item['arrg_full_id_i32'], m._i32(0x82000055))
        self.assertTrue(item['same_core_invocation_join_ready'])
        self.assertTrue(item['natural_attribution_ready'])
        self.assertIsNone(item['natural_parent_token'])
        self.assertEqual(item['core_invocation_join_v1']['natural_parent_event'], event(10))
        for key in ('same_core_NET_cause_proven','full_window_coverage_ready','toggle_effect_proven',
                    'refill_business_qualification_granted','owner_admission_authority_verified_here'):
            self.assertFalse(item[key], key)
        net = {'actual_ADD_observed':False, 'raw_current_net':-80}
        attached = m.attach_instruction_local_refill_add_12004(net,raw,binding,core_observation=core)
        self.assertFalse(attached['actual_ADD_observed'])
        self.assertEqual(attached['raw_current_net'],-80)
        self.assertFalse(attached['instruction_and_NET_parent_join_ready'])

    def test_coherent_but_invalid_active_frames_are_rejected(self):
        cases = {'sequence':3, 'owner_tid':457, 'active':0, 'invocation_token':0,
            'parent_invocation_token':123, 'nesting_depth':0, 'core_clock_identity':1,
            'core_thread_id':457, 'natural_thread_id':457, 'natural_entry_sequence':20,
            'date_raw':0, 'secondary_manager_identity':0x700000009, 'game_state_identity':0,
            'caller_return_rva':0x2A9A8E3, 'natural_entry_rva':0x2A99DA0,
            'entry_provenance_complete':0, 'saved_mask02_admitted':0, 'invocation_kind':2}
        for key,value in cases.items():
            with self.subTest(key=key):
                rows,binding,core=sample()
                for hit in rows[1:3]: hit['core_carrier_v1']['frame'][key]=value;repack(hit)
                with self.assertRaises(ValueError): self.normalize(rows,binding,core)

    def test_each_snapshot_and_between_hit_fence_is_independently_verified(self):
        for mutate in (
            lambda r:r[1]['core_carrier_v1'].update(second_168_hex='00'*168),
            lambda r:r[2]['core_carrier_v1']['frame'].update(sequence=4),
            lambda r:r[1]['core_carrier_v1'].update(stable_active=False),
            lambda r:r[1]['core_carrier_v1'].update(owner_matches=True),
            lambda r:r[1]['core_carrier_v1'].update(owners_complete=False),
            lambda r:r[1]['core_carrier_v1'].update(first_complete=False),
            lambda r:r[2]['core_carrier_v1'].update(second_complete=False),
            lambda r:r[1]['core_carrier_v1'].update(diagnostic='carrier_unstable_inactive_or_wrong_provenance'),
            lambda r:r[1]['core_carrier_v1'].update(header_64_hex='00'*64),
            lambda r:r[1]['core_carrier_v1'].update(slot_address='0x180010240'),
            lambda r:r[3].update(native_core_token=123),
            lambda r:r[3].update(carrier_pair_same_token=1),
            lambda r:r[1].update(natural_parent_token=10),
            lambda r:r[2].update(stack_q_window_28_hex='00'*28),
            lambda r:r[2].update(unproven_alias=True)):
            rows,binding,core=sample();mutate(rows)
            with self.assertRaises(ValueError): self.normalize(rows,binding,core)
        rows,binding,core=sample()
        rows[2]['core_carrier_v1']['frame']['sequence']=4;repack(rows[2])
        with self.assertRaises(ValueError): self.normalize(rows,binding,core)

    def test_core_record_must_be_complete_and_match_actual_context(self):
        for mutate in (
            lambda c:c.update(native_core_invocation_token=123),
            lambda c:c.update(parent_invocation_token=123),
            lambda c:c.update(core_invocation_nesting_depth=2),
            lambda c:c.update(core_carrier_published=False),
            lambda c:c.update(core_carrier_source_epoch=20261017),
            lambda c:c.update(original_returned=False),
            lambda c:c.update(return_provenance_complete=False),
            lambda c:c.update(returned_date_raw=53148913),
            lambda c:c['entry_event'].update(thread_id=457),
            lambda c:c['parent_scope']['entry_event'].update(sequence=9),
            lambda c:c['parent_scope'].update(game_state_identity=0x800000008),
            lambda c:c['parent_scope'].update(saved_mask02_admitted=False),
            lambda c:c['parent_scope'].update(saved_c0_raw=0),
            lambda c:c['parent_scope']['saved_c0_event'].update(sequence=30),
            lambda c:c['entry'].update(capture_complete=False),
            lambda c:c['returned'].update(missing_inputs=['partial']),
            lambda c:c['entry']['persistent_objects'][0].update(physical_token=0x200000008),
            lambda c:c['returned']['army_objects'][0]['arrg_occurrences'][0]['records'][0].update(chunk_index=3),
            lambda c:c.update(projected_NET=10)):
            rows,binding,core=sample();mutate(core)
            with self.assertRaises(ValueError): self.normalize(rows,binding,core)
        rows,binding,core=sample()
        for invalid in (None, {}, {'events':[core]}):
            with self.assertRaises(ValueError): self.normalize(rows,binding,invalid)

    def test_binding_header_source_and_duplicate_json_are_strict(self):
        for key,value in (('carrier_module_path','D:/other.dll'),('carrier_source_epoch',True),
                          ('source_dir','D:/missing/other'),('unexpected',1)):
            rows,binding,core=sample();binding[key]=value
            with self.assertRaises(ValueError): self.normalize(rows,binding,core)
        rows,binding,core=sample();rows[0]['carrier_header_64_hex']='00'*64
        with self.assertRaises(ValueError): self.normalize(rows,binding,core)
        rows,binding,core=sample();wrong='D:/constructed/generic.dll'
        binding['carrier_module_path']=rows[0]['carrier_module_path']=wrong
        for hit in rows[1:3]: hit['core_carrier_v1']['module_path']=wrong
        with self.assertRaises(ValueError): self.normalize(rows,binding,core)
        rows,binding,core=sample();raw=wire(rows).replace(b'"active":1',b'"active":0,"active":1',1)
        with self.assertRaises(ValueError): m.normalize_instruction_local_refill_add_12004(raw,binding,core_observation=core)

    def test_recursive_parent_is_not_the_natural_parent_event(self):
        rows,binding,core=sample()
        for hit in rows[1:3]:
            hit['core_carrier_v1']['frame'].update(parent_invocation_token=0xE000000000000001,nesting_depth=2)
            repack(hit)
        core.update(parent_invocation_token=0xE000000000000001,core_invocation_nesting_depth=2)
        item=self.normalize(rows,binding,core)
        self.assertTrue(item['same_core_invocation_join_ready'])
        self.assertIsNone(item['natural_parent_token'])
        self.assertEqual(item['core_invocation_join_v1']['natural_parent_event'],event(10))

    def test_legacy_schemas_ignore_new_observation_without_promotion(self):
        rows,binding,core=sample()
        for version in (2,3):
            with self.subTest(version=version):
                old_rows,old_binding=legacy(rows,binding,version)
                before=m.normalize_instruction_local_refill_add_12004(wire(old_rows),old_binding)
                after=self.normalize(old_rows,old_binding,core)
                self.assertEqual(before,after)
                self.assertFalse(after['natural_attribution_ready'])
                self.assertFalse(after.get('same_core_invocation_join_ready',False))
                self.assertIsNone(after['native_core_token'])

    def test_cli_requires_bounded_independent_core_record_and_uses_colocated_contract(self):
        rows,binding,core=sample()
        cli=BASE/'native_bridge/research/refill_add_live_12004/consume_live_refill_add.py'
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as directory:
            root=Path(directory)
            raw=root/'raw.ndjson'; owner=root/'binding.json'; observation=root/'core.json'; output=root/'item.json'
            raw.write_bytes(wire(rows));owner.write_text(json.dumps(binding));observation.write_text(json.dumps(core))
            args=[sys.executable,'-B','-X','utf8',str(cli),'--raw',str(raw),'--binding',str(owner),'--output',str(output)]
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(output.exists())
            result=subprocess.run(args+['--core-observation',str(observation)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(json.loads(output.read_text())['same_core_invocation_join_ready'])
            summary=json.loads(result.stdout)
            self.assertTrue(summary['natural_attribution_ready'])
            self.assertFalse(summary['full_R06_qualified'])


if __name__ == '__main__':
    unittest.main()
