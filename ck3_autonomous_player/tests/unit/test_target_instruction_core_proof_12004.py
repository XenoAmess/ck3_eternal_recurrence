"""One focused synthetic compound; no SDK, OS process query, or live ADD claim."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = Path(os.environ.get('XAR_TARGET_FIXTURE_REPO', str(ROOT)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


m = _load('target_core_under_test', ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/army_target_instruction_core_proof_12004.py')
old = _load('original_carrier_fixture', FIXTURE_ROOT / 'ck3_autonomous_player/tests/unit/test_refill_core_carrier_consumer_12004.py')


def wire(rows):
    return b'\n'.join(json.dumps(r, separators=(',', ':')).encode() for r in rows) + b'\n'


def parent_bytes(core):
    return wire([{'direction':'dll-to-python', 'message':{'type':'command_result',
        'request_id':'synthetic-request-not-live', 'protocol_version':1, 'ok':True,
        'result':{'step':'query-army-strengths-v1', 'accepted':True, 'status':'partial',
            'query_sequence':7, 'army_strengths_profile':'observed_history_full_v1',
            'army_strengths':[{'army_id':0, 'native_carmy_id':0,
                m.FAMILY:{'schema_version':1, 'source':'native_natural_army_regular_core_entry_return',
                    'membership_basis':'synthetic source-shaped fixture; not live qualification',
                    'observer_initialized':True, 'observer_installed':True, 'latest_journal_sequence':1,
                    'overwritten_events':0, 'publication_failures':0, 'events':[core]}}]}}}])


def sample(*, null_episode=False):
    """Small reusable fixture for the parent transport seam; all input is synthetic."""
    rows, binding, core = old.sample()
    binding.update(schema=m.BINDING_SCHEMA, thread_id=None, admission_mailbox_thread_id=12345,
        thread_policy='carrier_owned_target', maximum_owned_threads=8, episode_projection=None,
        army_full_id_i32=0, arrg_full_id_i32=82, regi_full_id_u32=2602)
    if null_episode: binding.update(episode_run_id=None, episode_projection='native_campaign')
    rows[0].update(schema=m.RAW_SCHEMA, thread_id=None, thread_policy='carrier_owned_target',
        maximum_owned_threads=8, armed_thread_ids=[], armed_thread_count=0, regi_full_id_u32=2602)
    for i,hit in enumerate(rows[1:3]):
        hit.update(thread_generation=555, all_debug_event_ordinal=20+i,
            arrg_raw=82, arrg_resolved=82, army_raw=0, army_resolved=0, regi_full_id_u32=2602)
        hit['DATA'][0].update(raw0=2602, persistent_full_id_u32=2602)
        seven=bytearray.fromhex(hit['physical_seven_hex']);struct.pack_into('<i',seven,2*36+16,82)
        hit['physical_seven_hex']=seven.hex()
    rows[3].update(selected_thread_id=456, selected_thread_generation=555)
    rows[5].update(thread_policy='carrier_owned_target', maximum_owned_threads=8,
        peak_owned_thread_count=2, selected_thread_id=456, selected_thread_generation=555)
    # Retire and re-arm a recycled numeric TID before the selected worker hits;
    # an old generation cannot supply either boundary's ownership.
    lifecycle=[{'kind':'thread_armed','thread_id':12345,'thread_generation':444,
        'all_debug_event_ordinal':1,'source':'CREATE_PROCESS_DEBUG_EVENT',
        'owned_handle_verified':True,'debug_registers_armed':True},
        {'kind':'thread_armed','thread_id':456,'thread_generation':554,
        'all_debug_event_ordinal':2,'source':'CREATE_THREAD_DEBUG_EVENT',
        'owned_handle_verified':True,'debug_registers_armed':True},
        {'kind':'thread_retired','thread_id':456,'thread_generation':554,
        'all_debug_event_ordinal':3,'had_saved_debug':True,'owned_handle_closed':True,'saved_debug_retired':True},
        {'kind':'thread_armed','thread_id':456,'thread_generation':555,
        'all_debug_event_ordinal':4,'source':'CREATE_THREAD_DEBUG_EVENT',
        'owned_handle_verified':True,'debug_registers_armed':True}]
    rows=rows[:1]+lifecycle+rows[1:]
    core['parent_scope']['original_army_roster']['ordered_full_ids']=[0]
    for label in ('entry','returned'):
        frame=core[label];frame.update(capture_complete=False,missing_inputs=['subject_character_override_has_no_physical_DATA_closure'])
        frame['army_refresh_occurrences'][0].update(raw_full_id=0,resolved_full_id=0)
        frame['persistent_occurrences'][0].update(raw_full_id=2602,resolved_full_id=2602)
        obj=frame['persistent_objects'][0];obj['resolved_full_id']=2602
        obj['physical_values']['persistent_regiment_id']=2602
        for chunk in obj['physical_values']['chunks']:
            chunk.update(owner_persistent_regiment_id=2602,army_regiment_id_raw=82)
        army=frame['army_objects'][0];army['resolved_full_id']=0;army['native_arrg_occurrence_count']=2
        arrg=army['arrg_occurrences'][0];arrg['occurrence'].update(raw_full_id=82,resolved_full_id=82)
        arrg['records'][0]['persistent_regiment_id']=2602
        skipped={'occurrence':old.occurrence(83,0x500000100),'resolved_magic_14_raw':0x41725267,
            'native_refresh_admitted':True,'native_loss_writer_skipped':True,'native_record_count':99,
            'records_complete':True,'unavailable_reason':'','records':[]}
        skipped['occurrence']['stored_index']=1;army['arrg_occurrences'].append(skipped)
        frame['subject_coverage_v1']={'schema_version':1,'mode':'explicit_full_carmy_physical_closure',
            'scope_epoch':6,'bound_game_state_identity':0x800000000,'bound_owner_character_id':33388,
            'requested_full_carmy_ids':[0],'manager_occurrences_complete':True,'physical_closure_complete':False,
            'subject_identity_witnesses':[{'full_carmy_id':0,'resolved_full_carmy_id':0,
                'carmy_magic_14_raw':0x41726D79,'public_unit_id':0,'unit_resolved_full_id':0,
                'unit_magic_14_raw':0x556E6974,'unit_owner_character_id':33388,'unit_full_carmy_id':0}],
            'missing_inputs':['subject_character_override_has_no_physical_DATA_closure']}
    response=parent_bytes(core)
    parent={'path':'D:/synthetic-not-live/original.native-wire.jsonl','file_identity':[1,2],
        'response_line':{'begin':100,'end':100+len(response),'sha256':hashlib.sha256(response).hexdigest()},
        'native_request_id':'synthetic-request-not-live','query_sequence':7,
        'source':'synthetic source-shaped bytes; never actual game evidence'}
    return rows,binding,core,response,parent


class TargetInstructionCompound(unittest.TestCase):
    def test_focused_target_contract_compound(self):
        def build(rows,binding,response,parent):
            return m.build_target_instruction_core_proof_12004(
                raw=wire(rows),binding=binding,parent_response=response,parent_proof=parent)
        for null_episode in (False,True):
            with self.subTest(positive='ordinary_null' if null_episode else 'original_nonnull'):
                rows,binding,core,response,parent=sample(null_episode=null_episode)
                proof=build(rows,binding,response,parent)
                item=m.normalize_target_instruction_core_proof_12004(wire(rows),binding,
                    target_core_proof=proof,parent_response=response,parent_proof=parent)
                self.assertTrue(item['same_core_invocation_join_ready'])
                self.assertEqual(item['owner_binding'],binding)
                self.assertIs(item['owner_binding']['episode_run_id'],None) if null_episode else self.assertEqual(item['owner_binding']['episode_run_id'],binding['episode_run_id'])
                self.assertEqual(item['selected_thread_id'],456)
                self.assertNotEqual(item['selected_thread_id'],binding['admission_mailbox_thread_id'])
                self.assertEqual(item['selected_thread_generation'],555)
                self.assertEqual(item['physical_seven_before_hex'],rows[5]['physical_seven_hex'])
                self.assertEqual(item['instruction_stack_q_source_v1']['stack_window_before_hex'],rows[5]['stack_q_window_28_hex'])
                self.assertFalse(proof['entry_target']['global_capture_complete_as_observed'])
                self.assertFalse(proof['entry_target']['subject_coverage_v1']['physical_closure_complete'])
                self.assertTrue(proof['entry_target']['target_DATA_alias_enumeration_complete'])
                for key in ('same_core_NET_cause_proven','whole_core_NET_cause_proven',
                        'global_physical_closure_qualification_granted','full_window_coverage_ready',
                        'toggle_effect_proven','refill_business_qualification_granted',
                        'owner_admission_authority_verified_here'):
                    self.assertFalse(item[key],key)
                # The legacy full-manager guard still rejects this scoped input.
                with self.assertRaises(ValueError):
                    m._shared._core_complete_frame(core['entry'],binding,rows[5])
        # One existing source-shaped full input verifies that the small shared
        # provenance factor preserves the legacy result exactly; no old matrix.
        legacy_rows,legacy_binding,legacy_core=old.sample()
        self.assertEqual(m._shared.normalize_instruction_local_refill_add_12004(
            wire(legacy_rows),legacy_binding,core_observation=legacy_core),
            old.m.normalize_instruction_local_refill_add_12004(
                wire(legacy_rows),legacy_binding,core_observation=legacy_core))
        for name,mutate in (
            ('wrong_worker_generation',lambda r,b,c,p:r[6].update(thread_generation=556)),
            ('retired_worker_reuse',lambda r,b,c,p:r[4].update(thread_generation=556)),
            ('wrong_token',lambda r,b,c,p:r[7].update(native_core_token=123)),
            ('wrong_parent_sha',lambda r,b,c,p:p['response_line'].update(sha256='0'*64)),
            ('wrong_parent_query',lambda r,b,c,p:p.update(query_sequence=8)),
            ('mailbox_promoted',lambda r,b,c,p:b.update(thread_id=b['admission_mailbox_thread_id'])),
            ('total_generation_bound',lambda r,b,c,p:(b.update(maximum_owned_threads=2),
                r[0].update(maximum_owned_threads=2),r[9].update(maximum_owned_threads=2))),
            ('lost_all_event_adjacency',lambda r,b,c,p:r[6].update(all_debug_event_ordinal=22)),
            ('target_non_DATA_branch',lambda r,b,c,p:c['entry']['army_objects'][0]['arrg_occurrences'][0].update(native_loss_writer_skipped=True)),
            ('target_alias_mismatch',lambda r,b,c,p:c['returned']['army_objects'][0]['arrg_occurrences'][0]['records'][0].update(chunk_index=3)),
            ('wrong_raw_252B',lambda r,b,c,p:r[6].update(physical_seven_hex='00'*252)),
            ('wrong_q_bytes',lambda r,b,c,p:r[6].update(stack_q_window_28_hex='00'*28))):
            with self.subTest(rejected=name):
                rows,binding,core,response,parent=sample();mutate(rows,binding,core,parent)
                if name.startswith('target_'):
                    response=parent_bytes(core);parent['response_line'].update(end=100+len(response),sha256=hashlib.sha256(response).hexdigest())
                with self.assertRaises(ValueError):build(rows,binding,response,parent)
        rows,binding,core,response,parent=sample();proof=build(rows,binding,response,parent)
        altered=copy.deepcopy(proof);altered['entry_target']['target_DATA_alias_enumeration_complete']=False
        with self.assertRaises(ValueError):
            m.normalize_target_instruction_core_proof_12004(wire(rows),binding,
                target_core_proof=altered,parent_response=response,parent_proof=parent)
        altered=copy.deepcopy(proof);altered['target_scope_complete']=1
        with self.assertRaises(ValueError):
            m.normalize_target_instruction_core_proof_12004(wire(rows),binding,
                target_core_proof=altered,parent_response=response,parent_proof=parent)
        # No original parent bytes => no qualification from a small summary.
        with self.assertRaises(ValueError):
            m.normalize_target_instruction_core_proof_12004(wire(rows),binding,
                target_core_proof=proof,parent_response=b'',parent_proof=parent)


class TargetProofCliSerialization(unittest.TestCase):
    """Actual file/CLI seams with synthetic bytes, never live qualification."""

    CLI = ROOT / 'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/consume_live_refill_add.py'

    def inputs(self, directory, *, file_bytes=None):
        rows, binding, core, _response, parent = sample(null_episode=True)
        parent_path = directory / 'original.native-wire.jsonl'

        def refresh():
            response = parent_bytes(core)
            parent_path.write_bytes(response)
            identity = parent_path.stat()
            parent.update(path=str(parent_path), file_identity=[identity.st_dev, identity.st_ino])
            parent['response_line'].update(begin=0, end=len(response), sha256=hashlib.sha256(response).hexdigest())
            return m.build_target_instruction_core_proof_12004(
                raw=wire(rows), binding=binding, parent_response=response, parent_proof=parent)

        # Every skipped non-target branch stays present and validated. Grow a
        # valid complete roster until pretty printing alone crosses the cap.
        for index in range(2, 128):
            for label in ('entry', 'returned'):
                army = core[label]['army_objects'][0]
                branch = copy.deepcopy(army['arrg_occurrences'][1])
                branch['occurrence'] = old.occurrence(83 + index, 0x500001000 + index * 0x100)
                branch['occurrence']['stored_index'] = index
                army['arrg_occurrences'].append(branch)
                army['native_arrg_occurrence_count'] = len(army['arrg_occurrences'])
            proof = refresh()
            if len((json.dumps(proof, ensure_ascii=False, indent=2) + '\n').encode('utf-8')) > 65536:
                break
        else:
            self.fail('valid roster did not reach the indented transport regression')
        if file_bytes is not None:
            reason = core['entry']['missing_inputs'][0] + ': synthetic UTF-8 汉 boundary '
            padding = 0
            for _ in range(8):
                core['entry']['missing_inputs'][0] = reason + 'x' * padding
                proof = refresh()
                difference = file_bytes - len(m._encoded(proof) + b'\n')
                if difference == 0:
                    break
                padding += difference
                self.assertGreaterEqual(padding, 0)
            else:
                self.fail('could not construct exact encoded file boundary')
        paths = {key: directory / name for key, name in (
            ('raw', 'observer.raw.ndjson'), ('binding', 'owner-binding.json'),
            ('parent', 'full-parent-proof.json'), ('proof', 'derived-target-proof.json'), ('output', 'item.json'))}
        paths['raw'].write_bytes(wire(rows))
        paths['binding'].write_bytes(m._encoded(binding))
        paths['parent'].write_bytes(m._encoded(parent))
        return rows, binding, core, parent, proof, paths

    def run_cli(self, paths, *, consume=False):
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(self.CLI),
            '--raw', str(paths['raw']), '--binding', str(paths['binding']),
            '--full-parent-proof', str(paths['parent']),
            '--target-core-proof' if consume else '--create-target-core-proof', str(paths['proof']),
            '--output', str(paths['output'])], capture_output=True, timeout=45)

    def assert_scope(self, item):
        self.assertTrue(item['same_core_invocation_join_ready'])
        self.assertIsNone(item['owner_binding']['episode_run_id'])
        self.assertEqual(item['owner_binding']['episode_projection'], 'native_campaign')
        for key in ('global_physical_closure_qualification_granted', 'whole_core_NET_cause_proven',
                    'same_core_NET_cause_proven', 'refill_business_qualification_granted',
                    'full_window_coverage_ready', 'owner_admission_authority_verified_here'):
            self.assertFalse(item[key], key)

    def test_pretty_over_cap_complete_proof_roundtrips_real_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _rows, _binding, core, _parent, proof, paths = self.inputs(directory)
            self.assertGreater(len((json.dumps(proof, ensure_ascii=False, indent=2) + '\n').encode('utf-8')), 65536)
            result = self.run_cli(paths)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual(paths['proof'].read_bytes(), m._encoded(proof) + b'\n')
            self.assertLessEqual(paths['proof'].stat().st_size, 65536)
            self.assertEqual(json.loads(paths['proof'].read_bytes()), proof)
            for label in ('entry', 'returned'):
                self.assertEqual(len(proof[label + '_target']['entire_target_army_arrg_branch_roster']),
                                 len(core[label]['army_objects'][0]['arrg_occurrences']))
            self.assert_scope(json.loads(paths['output'].read_bytes()))
            paths['output'] = directory / 'read-back-item.json'
            reread = self.run_cli(paths, consume=True)
            self.assertEqual(reread.returncode, 0, reread.stderr.decode())
            self.assert_scope(json.loads(paths['output'].read_bytes()))

    def test_utf8_and_newline_exact_65536_bytes_are_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            *_prefix, proof, paths = self.inputs(Path(temporary), file_bytes=65536)
            result = self.run_cli(paths)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual(paths['proof'].stat().st_size, 65536)
            self.assertEqual(paths['proof'].read_bytes(), m._encoded(proof) + b'\n')
            self.assertIn('汉'.encode('utf-8'), paths['proof'].read_bytes())
            self.assert_scope(json.loads(paths['output'].read_bytes()))

    def test_newline_65537th_byte_is_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            *_prefix, proof, paths = self.inputs(Path(temporary), file_bytes=65537)
            self.assertEqual(len(m._encoded(proof)), 65536)
            result = self.run_cli(paths)
            self.assertEqual(result.returncode, 2, result.stderr.decode())
            self.assertIn(b'derived target proof exceeds64KiB', result.stderr)
            self.assertFalse(paths['proof'].exists())
            self.assertFalse(paths['output'].exists())

    def test_parent_owner_token_generation_and_unselected_tail_stay_strict(self):
        for mutation in ('parent_sha', 'owner', 'token', 'generation', 'tail_branch'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                rows, binding, core, parent, _proof, paths = self.inputs(Path(temporary))
                if mutation == 'parent_sha': parent['response_line']['sha256'] = '0' * 64
                elif mutation == 'owner': binding['army_full_id_i32'] = 1
                elif mutation == 'token': rows[7]['native_core_token'] = 123
                elif mutation == 'generation': rows[6]['thread_generation'] = 556
                else:
                    core['entry']['army_objects'][0]['arrg_occurrences'][-1]['records_complete'] = False
                    response = parent_bytes(core)
                    Path(parent['path']).write_bytes(response)
                    parent['response_line'].update(end=len(response), sha256=hashlib.sha256(response).hexdigest())
                paths['raw'].write_bytes(wire(rows))
                paths['binding'].write_bytes(m._encoded(binding))
                paths['parent'].write_bytes(m._encoded(parent))
                result = self.run_cli(paths)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(paths['proof'].exists())
                self.assertFalse(paths['output'].exists())


if __name__ == '__main__':
    unittest.main()
