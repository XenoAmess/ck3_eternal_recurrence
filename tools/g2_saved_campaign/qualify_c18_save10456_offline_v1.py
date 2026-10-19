"""Source-only RAM qualification; no file writer other than the small proof."""
import argparse
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import reconcile_c18_save10456_offline_v1 as p

OWN = Path(__file__).resolve().parent
REPO = OWN.parent.parent
F96 = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c18-campaign10453-readonly-repeat96')
T = Path(str(p.T))
QUEUE = T/'root_p37c18_sdk_queue.py'
CADENCE = T/'root_p37_checkpoint_cadence.py'
NOTICE = F96/'MAINTENANCE-SAVE10456-CLOSED-NOTICE.json'


def pinned(path):
    raw = path.read_bytes()
    return p.parse_document_v1(raw, {'path':str(path), 'bytes':len(raw), 'sha256':p.sha(raw)})


def invented(value, name):
    raw = json.dumps(value, separators=(',', ':')).encode()
    return p.parse_document_v1(raw, {'path':str(p.T/'SOURCE-FIXTURE-NOT-ACTUAL'/name),
        'bytes':len(raw), 'sha256':p.sha(raw)})


def fixture_documents():
    notice = pinned(NOTICE)
    response = {name:pinned(Path(notice['value']['sources'][key]['path']))
        for name,key in (('semantic','SEM'),('save','SAVE'))}
    # This is deliberately a software fixture, not the unavailable-at-construction
    # original clean snapshot or any assertion that the live SDK has closed.
    state = json.loads((F96/'state.json').read_bytes()); state['pending_cycle'] = None
    gov = json.loads((F96/'governance.json').read_bytes()); gov['pending_cycle'] = None
    owner = {'machine_id':p.MACHINE, 'normal':True, 'launcher_exit_code':0,
        'Game_stopped':False, 'recording_stopped':False, 'processes':[
        {'role':role,'pid':pid,'creation_filetime':birth,'kernel_exit_observed':True,'exit_code':0}
        for role,pid,birth in sorted(p.PAIR)]}
    task = {'machine_id':p.MACHINE, 'child_exit_code':0, 'bootstrap_exit_code':0,
        'job_active_after_stage':0, 'forced_remaining_cleanup':False,
        'child':{'pid':53064,'creation_filetime':'134369092458681624'}}
    documents = dict(response, notice=notice,
        state=invented(state, 'state.json'), gov=invented(gov, 'gov.json'),
        owner_closed=invented(owner, 'ROOT-P37C18-OWNER-CLOSED.json'),
        task_closed=invented(task, 'CLOSED.json'), next=invented({'next_sequence':10457}, 'NEXT.json'))
    return documents


def project_fixture(documents, **kwargs):
    return p.project_saved_checkpoint_v1(documents, queue_source=QUEUE.read_bytes(),
        cadence_source=CADENCE.read_bytes(), target_exists=kwargs.get('target_exists', False), source_fixture=True)


class Qualification(unittest.TestCase):
    def setUp(self):
        self.documents = fixture_documents()

    def test_original_finish_once_and_diff_whitelist(self):
        original = copy.deepcopy(self.documents)
        output = project_fixture(self.documents)
        self.assertEqual(self.documents, original)
        self.assertEqual(output['state']['counts']['checkpoint_saved'], 73)
        self.assertEqual(output['state']['completed_cycles'], 4748)
        self.assertEqual(output['state']['before'], original['state']['value']['before'])
        self.assertEqual(output['governance'], original['gov']['value'])
        self.assertEqual(output['audit']['original_finish_calls'], 1)
        self.assertEqual(output['audit']['business_or_cycle_credit'], 0)
        self.assertTrue(output['audit']['source_fixture'])
        self.assertEqual(output['cumulative_save']['global_turn'], 4748)
        self.assertEqual(output['cumulative_save']['checkpoint']['history_index'], 5254)
        self.assertFalse(output['state']['checkpoint_dirty_since_save'])

    def test_semantic_drift_and_unknown_SAVE_rejected(self):
        for kind in ('date', 'unknown_save', 'sdk_abnormal'):
            with self.subTest(kind=kind):
                docs = copy.deepcopy(self.documents)
                if kind == 'date':
                    value = copy.deepcopy(docs['semantic']['value'])
                    value['result']['structured_content']['date_raw'] += 24
                    raw = json.dumps(value, separators=(',', ':')).encode()
                    ref = dict(docs['semantic']['ref'], bytes=len(raw), sha256=p.sha(raw))
                    docs['semantic'] = p.parse_document_v1(raw, ref)
                elif kind == 'unknown_save':
                    value = copy.deepcopy(docs['save']['value']); value['result']['is_error'] = True
                    raw = json.dumps(value, separators=(',', ':')).encode()
                    docs['save'] = p.parse_document_v1(raw, dict(docs['save']['ref'], bytes=len(raw), sha256=p.sha(raw)))
                else:
                    value = copy.deepcopy(docs['owner_closed']['value']); value['processes'][0]['exit_code'] = 1
                    docs['owner_closed'] = invented(value, 'ROOT-P37C18-OWNER-CLOSED.json')
                before = copy.deepcopy(docs)
                with self.assertRaises(ValueError): project_fixture(docs)
                self.assertEqual(docs, before)

    def test_existing_CUM_or_recount_rejected(self):
        with self.assertRaises(ValueError): project_fixture(self.documents, target_exists=True)
        output = project_fixture(self.documents)
        docs = copy.deepcopy(self.documents); docs['state'] = invented(output['state'], 'state.json')
        with self.assertRaises(ValueError): project_fixture(docs)

    def test_source_or_parsed_document_mutation_rejected(self):
        docs = copy.deepcopy(self.documents); docs['state']['value']['counts']['checkpoint_saved'] += 1
        with self.assertRaises(ValueError): project_fixture(docs)
        with self.assertRaises(ValueError):
            p.project_saved_checkpoint_v1(self.documents, queue_source=QUEUE.read_bytes()+b'\n',
                cadence_source=CADENCE.read_bytes(), target_exists=False, source_fixture=True)


def project_actual_closed_inputs_v1(input_manifest):
    """Read only the named small metadata; return RAM outputs, never adopt them."""
    manifest = json.loads(Path(input_manifest).read_bytes())
    p.require(manifest.get('machine_id') == p.MACHINE and manifest.get('status') == 'C18_NORMAL_CLOSED_SAVE10456_INPUTS',
        'actual normal-closure input manifest required')
    refs = manifest['sources']
    p.require(set(refs) == {'state','gov','semantic','save','owner_closed','task_closed','next','notice'}, 'closed source set differs')
    documents = {}
    for name,ref in refs.items():
        path = Path(ref['path'])
        p.require(path.suffix.lower() == '.json' and 'driver-state' not in path.name.lower()
            and path.stat().st_size == ref['bytes'] <= 2*1024**2, 'small metadata source required')
        documents[name] = p.parse_document_v1(path.read_bytes(), ref)
    target = T/'p37-queue/CUMULATIVE-SAVE-004748.json'
    p.require(manifest.get('cumulative_save_target') == str(target), 'canonical CUM target differs')
    return p.project_saved_checkpoint_v1(documents, queue_source=QUEUE.read_bytes(), cadence_source=CADENCE.read_bytes(),
        target_exists=target.exists(), source_fixture=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--proof', type=Path)
    parser.add_argument('--actual-inputs', type=Path); args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Qualification))
    if not result.wasSuccessful(): raise SystemExit(1)
    actual = project_actual_closed_inputs_v1(args.actual_inputs) if args.actual_inputs else None
    files = [Path(p.__file__), Path(__file__)]
    proof = {'schema':'xar.C18-SAVE10456-offline-reconcile-source-qualification/v1',
        'machine_id':p.MACHINE, 'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'machine_source':'tools/ck3_live_run_id.py machine; current execution readback',
        'status':'SOURCE_QUALIFIED_NOT_ADOPTED', 'tests_passed':result.testsRun,
        'positive_fixture':'actual closed10455/10456 responses and original Queue/cadence source; synthetic SDK closure/cleanstate explicitly source_fixture True',
        'actual_SDK_closure_or_loop_snapshot_claimed_by_fixture':False,
        'files':[{'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':p.sha(path.read_bytes())} for path in files],
        'original_source_pins':{'Queue':p.QUEUE_SHA,'cadence':p.CADENCE_SHA,'SAVE_notice':p.NOTICE_SHA},
        'original_finish_calls_per_projection':1, 'original_atomic_and_persist_side_effects':'captured only in RAM',
        'diff_whitelist':sorted(p.ALLOWED), 'governance_or_original_inputs_modified':False,
        'duplicate_CUM_recount_drift_unknown_SAVE_abnormal_SDK_refused':True,
        'actual_closed_input_RAM_projection':actual['audit'] if actual else None,
        'D_Git_Task_Game_RPC_Driver_SAVE_operations':0, 'scratch_files':0,
        'source_cap_bytes':32768, 'separate_scratch_cap_bytes':16384,
        'source_card_sha256':'e3df047a164191676a445ede507a4c8f9419c6893ad1bf5e11feafced6ba44b1',
        'runtime_adoption_requires_separate_release_and_fresh_target_absence_recheck':True,
        'record_review_at_utc':'2027-04-17T20:47:44+00:00', 'future_writes_after_freeze':0}
    raw = (json.dumps(proof, ensure_ascii=False, indent=2)+'\n').encode()
    total = sum(path.stat().st_size for path in files)+len(raw)
    if total > 32768: raise ValueError('complete32KiB source cap exceeded')
    if args.proof:
        with args.proof.open('xb') as output: output.write(raw)
    print(json.dumps({'tests':result.testsRun, 'source_gross_bytes':total,
        'proof_bytes':len(raw),'proof_sha256':p.sha(raw),'actual_inputs_verified':actual is not None}))
