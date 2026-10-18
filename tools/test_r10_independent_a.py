"""One production compound for explicit public A baseline/cold admission."""
from pathlib import Path
from types import SimpleNamespace as NS
from copy import deepcopy
import argparse, hashlib, importlib.util, json, sys, tempfile, unittest

p=argparse.ArgumentParser(add_help=False)
p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--dependencies-root',type=Path)
p.add_argument('--receipt',type=Path)
o,rest=p.parse_known_args();deps=o.dependencies_root or o.repo_root
sys.path[:0]=[str(deps/'tools'),str(deps/'ck3_autonomous_player/src')]
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.insert(0,str(o.repo_root/'tools/ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases import r10_common_arm as common, r10_arm_adapter as adapter
from ck3_live_run_id import current_machine_id
comparison=deps/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison'
sys.path.insert(0,str(comparison))
import r10_compare as c, strategy_a as a
from test_r10_compare import Fixture

class Compound(unittest.TestCase):
    def test_baseline_then_independent_A_and_joint_B0_rejection(self):
        with tempfile.TemporaryDirectory(prefix='r10-a-public-') as tmp:
            f=Fixture(tmp);e=c.Evidence(tmp);rt=f.results['arms'][0]['runtime'];cold=f.results['arms'][0]['cold_start']
            for ep in (f.plan['baseline'],cold):
                ep['snapshot']=f.edit(ep['snapshot'],lambda v:v['body']['player_armies'][0].update(controllable=True))
            machine=current_machine_id();rt['machine_id']=machine
            cold['snapshot']=f.edit(cold['snapshot'],lambda v:v.update(machine_id=machine))
            def preview(ep):
                s=c.body(e.json(ep['snapshot']));u=s['player_armies'][0]
                return f.put('synthetic-native-preview',{'step':'preview-move-army-1-to-30','accepted':True,
                    **{'queried_'+k:s[k] for k in ('snapshot_id','revision','native_revision','episode_run_id')},
                    'queried_connection_generation':1,'route_preview':{'status':'available','army_id':1,
                        'origin_province_id':10,'target_province_id':30,'route_province_ids':[30],'previewed_date_raw':1000}})
            bp=preview(f.plan['baseline']);fresh=preview(cold)
            plan=deepcopy(f.plan);plan.update(execution_scope='independent-A-only')
            plan['strategies']={'A':{'mode':'whole-direct','route_preview':bp},'B':None,'C':None}
            context={'case':'r10-independent-a','case_contract':{'schema':common.A_ONLY_SCHEMA},
                'case_inputs':{'arm':{'label':'A','phase':'collect-baseline'}}}
            seed=deepcopy(plan);seed.update(status='baseline-capture',baseline=None,original_regiment_ids=[])
            seed['strategies']['A']['route_preview']=None
            self.assertIsNone(common.public_plan_baseline(context,seed,e,c))
            # Invoke the actual production baseline method with native-shaped IO;
            # no CommonArmIO live constructor, SDK, or forged actual qualification.
            io=NS(context=context,plan=seed,e=e,c=c,runtime=rt,label='A',
                settings={'plan':f.proof},base=comparison.parent,endpoint=lambda name:cold,
                preview=lambda ep,target:(c.body(e.json(fresh)),fresh))
            stages=adapter.Stages(io);stages.save=lambda name,value:deepcopy(value)
            captured=stages.baseline()
            self.assertEqual(captured['original_regiment_ids'],[1,2]);self.assertEqual(captured['route'],[30])
            self.assertFalse(captured['Move_submitted']);self.assertEqual(captured['natural_days'],0)
            with self.assertRaisesRegex(ValueError,'Readonly A baseline'):
                stages.run({'stage':'Move-once'})
            # The public metadata freezer consumes the real production capture
            # shape and preserves its full pins. It does not start another run.
            spec=importlib.util.spec_from_file_location('r10_a_input_cli',o.repo_root/'tools/ck3_r10_a_inputs.py')
            cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
            seed_ref=f.put('readonly-seed',seed);captured['seed_plan']={**seed_ref,'path':str(Path(tmp)/seed_ref['path'])}
            capture=Path(tmp)/'capture.json';capture.write_text(json.dumps({'machine_id':machine,'state':captured}),encoding='utf-8')
            frozen_path=Path(tmp)/'A-frozen.json'
            cli.freeze(NS(capture=capture,repo_root=deps,evidence_root=Path(tmp),output=frozen_path))
            frozen=json.loads(frozen_path.read_bytes());self.assertEqual(frozen['status'],'frozen')
            self.assertIsNone(frozen['strategies']['B']);self.assertIsNone(frozen['strategies']['C'])
            with self.assertRaisesRegex(ValueError,'B/C require'):
                cli.bind(NS(label='B',frozen_plan=None))
            # A future frozen independent cold baseline uses the existing A.admit.
            context['case_inputs']['arm']['phase']='execute';io.plan=plan;io.preview=lambda ep,target:(c.body(e.json(fresh)),fresh)
            stages=adapter.Stages(io);stages.save=lambda name,value:deepcopy(value)
            admitted=stages.baseline()
            self.assertEqual(admitted['proposed_call']['arguments']['target_province_id'],30)
            self.assertFalse(admitted['live_execution_performed'])
            # Same plan cannot enter the joint case, and B0 sites still fail the
            # unmodified joint schema. The explicit A case never grants ABC.
            joint={'case':'r10-common-arm','case_contract':{'schema':'xar.e04.r10-common-arm-case.v1'},'case_inputs':context['case_inputs']}
            with self.assertRaisesRegex(ValueError,'schema plan'):
                common.public_plan_baseline(joint,plan,e,c)
            b0=deepcopy(f.plan);b0['strategies']['B']['site_actual_stock_increase_evidence']=[]
            with self.assertRaisesRegex(ValueError,'schema plan'):
                common.public_plan_baseline(joint,b0,e,c)
            bad=deepcopy(context);bad['case_inputs']['arm']['label']='B'
            with self.assertRaisesRegex(ValueError,'case/label'):
                common.public_plan_baseline(bad,plan,e,c)
            stale=f.edit(fresh,lambda v:v.update(queried_native_revision=999))
            io.preview=lambda ep,target:(c.body(e.json(stale)),stale)
            stages=adapter.Stages(io);stages.save=lambda name,value:value
            with self.assertRaisesRegex(ValueError,'preview frame'):
                stages.baseline()
            facts={'machine_id':current_machine_id(),'compound_tests':1,'production_baseline_and_A_admit':'PASS',
                'joint_ABC_with_B0_sites':'REJECTED','capture_Move_or_day':'REJECTED','stale_preview':'REJECTED',
                'synthetic_native_shaped_inputs':True,'actual_game_or_formal_credit':False,'SDK_calls':0}
            if o.receipt:
                o.receipt.parent.mkdir(parents=True,exist_ok=True)
                o.receipt.write_text(json.dumps(facts,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(facts))

if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest])
