"""One portable actual-R207 replay; no host, game, SDK or original-machine paths."""
from pathlib import Path
from decimal import Decimal
from types import SimpleNamespace
import argparse,gzip,hashlib,importlib.util,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
class ActualR207(unittest.TestCase):
    def test_actual_units_legacy_preservation_and_common_full(self):
        e=REPO/'docs/ck3-native-ai/acceptance/2026-10-18-r207-r05-initializer-units'
        index=json.loads((e/'source-index.actual.json').read_bytes())
        for ref in index['portable_sources']:
            p=REPO/ref['portable']['relative_path'];raw=p.read_bytes()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(ref['portable']['bytes'],ref['portable']['sha256']))
            original=gzip.decompress(raw) if ref['compression']=='gzip' else raw
            self.assertEqual(hashlib.sha256(original).hexdigest(),ref['source']['sha256'])
        def read(name):
            raw=(e/name).read_bytes();return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
        before=read('public-before-snapshot.actual.json.gz')['rows'][0]['result']
        public=read('public-compact-query.actual.json.gz')['rows'][0]
        raw=read('native-wire-query-seq1-response.actual.jsonl.gz')['message']['result']
        outcome=read('initializer-outcome.actual.json.gz');claim=read('initializer-once-claim.actual.json.gz')
        from xar_autoplayer import bridge
        fixture=load('xar_autoplayer.bridge.r05_low_supply_fixture',REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
        bridge.r05_low_supply_fixture=fixture
        full=load('ck3_mod_acceptance_full_army',REPO/'tools/ck3_mod_acceptance_full_army.py')
        from ck3_mod_acceptance_client import CaseClient
        run_id=index['run_id']
        class ReplayQueue(CaseClient):
            def __init__(self):
                self.selection=SimpleNamespace(run_dir=Path(run_id));self.report_path=Path('synthetic-wire-not-opened.json');self.output=Path('synthetic-output-not-created');self.saved=[]
            def validate_frame(self,frame,*args,**kwargs):return frame
            def execute_plan(self,steps,name,timeout=None,reserve=90):
                step=steps[0];result=before if step['tool']=='ck3_take_snapshot' else public['result']
                return [{'id':step['id'],'ok':True,'result':result,'after_snapshot':public['after_snapshot']}]
            def checkpoint(self,name,value):self.saved.append((name,value))
        wire=SimpleNamespace(mark=lambda p:{'synthetic_queue_boundary':True},recover=lambda *a,**kw:(raw,{'actual_portable_native_wire':True,'complete_Driver_packet':False}))
        queue=ReplayQueue();wrapped=full.FullArmyResultClient(queue,wire,prefix='portable-replay')
        f=wrapped.snapshot();self.assertNotIn('episode_run_id',before);self.assertEqual(f['episode_run_id'],run_id)
        rows=wrapped.execute_plan([{'id':'strengths','tool':'ck3_query_army_strengths','args':{'army_ids':[0],'expected_revision':f['revision'],'profile':'observed_history_full_v1'}}],'strengths')
        self.assertEqual(rows[0]['id'],'strengths');self.assertEqual(rows[0]['continuation_public_step_id'],'portable-replay-strengths')
        witness=fixture.target_witness(f,rows[0]['result'],actor_id=33388,army_id=0,carmy_id=0,province_id=1506)
        self.assertEqual(witness['current_supply_raw'],11651751);self.assertEqual(len(wrapped.full_proofs),1)
        self.assertIs(full.ensure_common_full_army_client(wrapped),wrapped)
        self.assertIsInstance(full.ensure_common_full_army_client(queue),full.FullArmyResultClient)
        drift=dict(public['after_snapshot']);drift['revision']+=1
        old_after=public['after_snapshot'];public['after_snapshot']=drift
        failed=wrapped.execute_plan([{'id':'drift','tool':'ck3_query_army_strengths','args':{'army_ids':[0],'expected_revision':f['revision'],'profile':'observed_history_full_v1'}}],'drift')[0]
        from xar_autoplayer.bridge.r05_supply_observation_case import is_strength_revision_drift
        self.assertTrue(is_strength_revision_drift(failed));self.assertTrue(failed['derived_full_result_error'])
        self.assertTrue(failed['wire_full_result_proof']['original_public_row_ok'])
        public['after_snapshot']=old_after
        bad=dict(before);bad['episode_run_id']='other-run'
        with self.assertRaises(ValueError):full.bind_common_frame(bad,run_id)
        # The real negative case remains negative under the same production classifier.
        assessment=fixture.assess_initialization(claim['before'],outcome['independent_after'])
        self.assertEqual(assessment,outcome['assessment']);self.assertEqual(assessment['status'],'supply_changed_not_low_stock')
        self.assertEqual(11651751-11551851,99900);self.assertTrue(assessment['physical_soldiers_unchanged'])
        legacy=fixture.config(1506,'0.999');self.assertEqual(legacy,claim['config'])
        self.assertEqual(fixture.render_files(legacy)['common/decisions/xar_r05_low_supply_fixture.txt'],(e/'original-decision.actual.txt').read_bytes())
        new=fixture.config(1506,supply_loss_amount='116.51751')
        self.assertEqual(new['supply_loss_amount'],'116.51751');self.assertNotIn('supply_loss_fraction',new)
        decision=fixture.render_files(new)['common/decisions/xar_r05_low_supply_fixture.txt']
        self.assertIn(b'subtract_supply = 116.51751',decision);self.assertNotIn(b'deplete',decision)
        self.assertEqual(Decimal(new['supply_loss_amount'])*100000,witness['current_supply_raw'])
        for value in ('0','1.000001','1e2'):
            with self.assertRaises(ValueError):fixture.config(1506,supply_loss_amount=value)
        with self.assertRaises(ValueError):fixture.config(1506,'0.999',supply_loss_amount='116.51751')
        fixture.validate_fixture(e/'next-fixture-preview/fixture-manifest.json')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,default=ROOT);p.add_argument('--dependencies-root',type=Path)
    p.add_argument('--receipt',type=Path);a=p.parse_args();REPO=a.repo_root.resolve();deps=(a.dependencies_root or REPO).resolve()
    sys.path[:0]=[str(REPO/'tools'),str(deps/'tools'),str(deps/'ck3_autonomous_player/src')]
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ActualR207))
    if a.receipt:
        from ck3_live_run_id import current_machine_id
        v={'machine_id':current_machine_id(),'status':'PASS' if result.wasSuccessful() else 'RED','tests':result.testsRun,
            'scope':'one portable actual R207 negative replay plus exact old config and new amount/common wire source boundaries',
            'source_evidence_machine_id':'desktop-3fevhd2-1c74096080','SDK_calls':0,'new_amount_live_qualified':False,'R05_positive':False}
        with a.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
