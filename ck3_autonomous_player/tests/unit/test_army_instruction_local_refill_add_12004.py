"""New wire-level counterexamples; constructed packets grant no live qualification."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import struct
import unittest

base = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('instruction_add_contract', base/'src/xar_autoplayer/bridge/army_instruction_local_refill_add_12004.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def sample(before=80, q=10):
    after = (before+q) & 0xFFFFFFFF
    binding = {'schema':m.BINDING_SCHEMA,'machine_id':'fixture-machine','exact_executable_sha256':m.EXE_SHA256,
               'pid':123,'process_created_filetime':999,'thread_id':456,'regi_full_id_u32':0x1000042,
               'physical_slot':0,'arrg_full_id_i32':0x1000055,'army_full_id_i32':0x1000066,
               'connection_generation':1,'episode_run_id':'unit-constructed-not-live',
               'source_admission_receipt_sha256':'a'*64,'observer_build_and_SYSTEM_gate_receipt_sha256':'b'*64}
    data = [{'stored_index':0,'raw0':7,'raw4':8,'persistent_full_id_u32':0x1000042,'physical_ordinal_u32':0},
            {'stored_index':1,'raw0':9,'raw4':10,'persistent_full_id_u32':0x1000043,'physical_ordinal_u32':1}]
    rows = [{'kind':'start','schema':m.RAW_SCHEMA,'machine_id':'fixture-machine','exact_exe_sha256_basis':'external-frozen-runtime-admission',
             'pid':123,'process_created_filetime':999,'module_base':'0x140000000','fixture':False,'thread_id':456,
             'regi_full_id_u32':0x1000042,'physical_slot':0,'timeout_ms':1000,
             'verified_site_0_hex':'0150f4','verified_site_1_hex':'8b48f43b48f0'}]
    for i,current in enumerate((before,after)):
        seven = bytearray(252);struct.pack_into('<II',seven,0,100,current);struct.pack_into('<ii',seven,12,0,0x1000055)
        rows.append({'kind':'raw_ADD_boundary','machine_id':'fixture-machine','site_rva':('0x2A98B88','0x2A98B8B')[i],
                     'pid':123,'thread_id':456,'event_ordinal':i+1,'debug_event_ordinal':i+10,'qpc':i+100,
                     'regi_pointer':'0x200000000','regi_full_id_u32':0x1000042,'physical_slot':0,'rax_anchor':'0x200000028',
                     'rsp':'0x300000000','core_caller_raw':'0x140001234','manager_iterator':'0x400000000',
                     'q_index':0,'q_u32':q,'q_i32':m._i32(q),'current_u32':current,'maximum_u32':100,
                     'physical_complete':True,'native_core_token':None,'natural_parent_token':None,'natural_attribution_ready':False,
                     'arrg_raw':0x1000055,'arrg_resolved':0x1000055,'arrg_pointer':'0x500000000','army_raw':0x1000066,
                     'army_resolved':0x1000066,'data_count':2,'associated_ArRg_DATA_complete':True,
                     'DATA':copy.deepcopy(data),'physical_seven_hex':seven.hex()})
    rows += [{'kind':'physical_ADD_pair','machine_id':'fixture-machine','actual_ADD_observed':True,
              'native_instruction_replayed_by_probe':False,'q_i32':m._i32(q),'before_current_u32':before,'after_current_u32':after,
              'DWORD_wrap_matches':True,'associated_DATA_pair_complete':True,'natural_parent_token':None,
              'natural_attribution_ready':False,'full_window_coverage_ready':False},
             {'kind':'debug_hit_budget','debug_hits':11,'limit':100000},
             {'kind':'terminal','status':'paired','reason':'paired','debug_registers_cleared':True,'detached':True,'hit_count':2}]
    return rows,binding


def wire(rows): return ('\n'.join(json.dumps(r) for r in rows)+'\n').encode()


class NativeInstructionAddTests(unittest.TestCase):
    def test_wrap_zero_negative_and_mixed_DATA_are_distinct_native_operands(self):
        for before,q in [(0xFFFFFFFF,1),(80,0),(0,0xFFFFFFFF)]:
            with self.subTest(before=before,q=q):
                rows,binding=sample(before,q);item=m.normalize_instruction_local_refill_add_12004(wire(rows),binding)
                self.assertTrue(item['actual_ADD_observed']);self.assertEqual(item['instruction_operand_u32'],q)
                self.assertEqual(item['after_current_u32'],(before+q)&0xFFFFFFFF)
                self.assertEqual(item['matching_DATA_aliases'],1)
                self.assertFalse(item['refill_business_qualification_granted']);self.assertIsNone(item['native_event_date_raw'])

    def test_cross_process_generation_tid_or_regi_generation_rejected(self):
        for key in ('pid','thread_id','regi_full_id_u32'):
            rows,binding=sample();rows[2][key]+=1
            with self.subTest(key=key), self.assertRaises(ValueError):m.normalize_instruction_local_refill_add_12004(wire(rows),binding)
        rows,binding=sample();binding['process_created_filetime']+=1
        with self.assertRaises(ValueError):m.normalize_instruction_local_refill_add_12004(wire(rows),binding)

    def test_nonadjacent_trap_and_other_DWORD_change_rejected(self):
        rows,binding=sample();rows[2]['debug_event_ordinal']+=1
        with self.assertRaises(ValueError):m.normalize_instruction_local_refill_add_12004(wire(rows),binding)
        rows,binding=sample();b=bytearray.fromhex(rows[2]['physical_seven_hex']);b[100]=1;rows[2]['physical_seven_hex']=b.hex()
        with self.assertRaises(ValueError):m.normalize_instruction_local_refill_add_12004(wire(rows),binding)

    def test_synthetic_relabel_partial_and_bad_operand_rejected(self):
        for modify in [lambda r:r[0].update(fixture=True),lambda r:r[0].update(synthetic_binary_identity_basis='owned'),
                       lambda r:r[1].update(synthetic_site_address='0x123'),lambda r:r[2].update(physical_seven_hex='00'*251),
                       lambda r:r[3].update(q_i32=True),lambda r:r[1].update(q_u32=True)]:
            rows,binding=sample();modify(rows)
            with self.assertRaises(ValueError):m.normalize_instruction_local_refill_add_12004(wire(rows),binding)

    def test_timeout_or_cleanup_boolean_alias_cannot_qualify(self):
        for modify in [lambda r:r[-1].update(status='red',reason='timeout_before_unique_pair'),
                       lambda r:r[-1].update(detached=False),lambda r:r[-1].update(debug_registers_cleared=1)]:
            rows,binding=sample();modify(rows)
            with self.assertRaises(ValueError):m.normalize_instruction_local_refill_add_12004(wire(rows),binding)

    def test_external_cli_uses_colocated_contract_despite_old_package(self):
        cli = base/'native_bridge/research/refill_add_live_12004/consume_live_refill_add.py'
        temp_parent = os.environ.get('XAR_TEST_TEMP_ROOT')
        with tempfile.TemporaryDirectory(dir=temp_parent) as directory:
            root = Path(directory).resolve()
            if temp_parent: self.assertTrue(root.is_relative_to(Path(temp_parent).resolve()))
            package = root/'xar_autoplayer';package.mkdir()
            (package/'__init__.py').write_text("raise RuntimeError('OLD_PACKAGE_MUST_NOT_LOAD')\n")
            env = dict(os.environ, PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE='1')
            result = subprocess.run([sys.executable,'-B','-X','utf8',str(cli),'--help'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('--binding',result.stdout)

    def test_publishing_instruction_evidence_does_not_relabel_core_NET(self):
        rows,binding=sample();net={'actual_ADD_observed':False,'raw_current_net':-80,'missing_inputs':['instruction_local_ADD_producer_not_published']}
        combined=m.attach_instruction_local_refill_add_12004(net,wire(rows),binding)
        self.assertFalse(combined['actual_ADD_observed']);self.assertEqual(combined['raw_current_net'],-80)
        self.assertTrue(combined['instruction_local_ADD_v1']['actual_ADD_observed'])
        self.assertFalse(combined['instruction_and_NET_parent_join_ready'])


if __name__=='__main__':unittest.main()
