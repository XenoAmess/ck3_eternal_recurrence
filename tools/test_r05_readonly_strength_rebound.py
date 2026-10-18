"""One focused common-queue smoke for a readonly snapshot-revision rebound.

Synthetic queue rows exercise production consumers; no SDK or live credit.
"""
from pathlib import Path
import argparse,copy,importlib.util,json,sys,tempfile,unittest
from types import SimpleNamespace
from unittest import mock

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

class ReboundContract(unittest.TestCase):
    def test_readonly_rebound_and_zero_full_id(self):
        counts={}
        for mode in ('success','second_drift','changed_date','unrelated','unknown'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory(dir=TEMP) as t:
                root=Path(t);c=T.Client(root);original=c.execute_plan;queries=[];steps_seen=[]
                def execute(steps,name,timeout=None,reserve=90):
                    s=steps[0];steps_seen.append(copy.deepcopy(s))
                    if s['tool']=='ck3_query_army_strengths':
                        self.assertTrue(s['continue_on_error']);queries.append(s['id'])
                        # Start after the successful before frame in the full
                        # observer case, so outer convergence cannot add query3.
                        fail=(mode!='second_drift' or c.frame['date_raw']>c.before[0]['date_raw'])
                        if fail and (mode!='success' or len(queries)==1):
                            c.calls.append((s['tool'],copy.deepcopy(s['args'])))
                            if mode=='unknown':raise TimeoutError('synthetic unknown readonly result')
                            error='RuntimeError: '+(O.STRENGTH_REVISION_DRIFT if mode!='unrelated' else 'unrelated read failure')
                            row={'id':s['id'],'ok':False,'error':error,'finished_at':'synthetic'}
                            c.checkpoint(name+'.actual-results',{'rows':[row]})
                            if mode in ('success','changed_date'):
                                c.frame['revision']+=1;c.frame['native_revision']+=1
                                c.frame['snapshot_id']='native:'+str(c.frame['native_revision'])
                                if mode=='changed_date':c.frame['date_raw']+=24
                                c.query.update(queried_revision=c.frame['revision'],queried_native_revision=c.frame['native_revision'],
                                    queried_snapshot_id=c.frame['snapshot_id'])
                            return [row]
                    return original(steps,name,timeout,reserve)
                c.execute_plan=execute
                ctx=dict(output=str(root),machine_id='synthetic-machine-not-live',command_timeout=10,state_dir=str(root/'state'))
                if mode=='second_drift':
                    result=O.observe_initialized_supply(c,T.settings(),context=ctx,initialization=T.init_result(c))
                    self.assertEqual(len(queries),3) # one before + two after
                    self.assertFalse(result['R05_positive']);self.assertEqual(result['verified_actual_days'],0)
                    self.assertNotIn('unverified_day_readonly_assessment',result)
                    self.assertTrue(result['cleanup']['sampling_OFF_clear_verified']);self.assertTrue(result['cleanup']['save_verified'])
                    self.assertEqual(sum(a['tool']=='ck3_execute_step' and a['args']['step']=='resume-map' for a in steps_seen),1)
                    self.assertEqual(len(result['readonly_strength_recoveries']),1)
                else:
                    io=O.ObservationIO(c,T.settings(),context=ctx,initialization=T.init_result(c))
                    if mode=='success':
                        got=io.sample('focused',frame=copy.deepcopy(c.frame))
                        self.assertEqual(got['frame']['revision'],c.frame['revision'])
                        self.assertEqual(len(queries),2);self.assertEqual(len(set(queries)),2)
                        self.assertEqual(io.readonly_strength_recoveries[0]['status'],'second_readonly_query_completed')
                        self.assertTrue(io.readonly_strength_recoveries[0]['first_RED']['original']['path'])
                    else:
                        with self.assertRaises((ValueError,TimeoutError)):io.sample('focused',frame=copy.deepcopy(c.frame))
                        self.assertEqual(len(queries),1);self.assertTrue(io.strength_recovery_failed)
                    self.assertFalse(any(a['tool']=='ck3_execute_step' for a in steps_seen))
                counts[mode]=len(queries)
        # Exercise the actual initializer adapter, not a copied integer check.
        with tempfile.TemporaryDirectory(dir=TEMP) as t:
            root=Path(t);f,q=T.I.inputs()
            def zero_army(value):
                if isinstance(value,dict):
                    for k,v in value.items():
                        if k in ('army_id','subject_army_id') and v==18:value[k]=0
                        else:zero_army(v)
                elif isinstance(value,list):
                    for v in value:zero_army(v)
            zero_army(f);zero_army(q)
            p=root/'prepared.json';p.write_text(json.dumps({'r05_low_supply_fixture':{'manifest':{'path':'synthetic'}}}))
            captured={}
            def init(relay,m,**kw):
                captured.update(kw);return {'assessment':{'status':'prepared_low_stock'}}
            class Client:
                _process={'pid':101,'create_time':1};selection=SimpleNamespace(prepared={'preparation':{'root_prepared':M.pin(p)}})
                def retain_process(self):pass
                def snapshot(self):return f
                def checkpoint(self,*a):pass
                def execute_plan(self,steps,name,**kw):
                    s=steps[0];return [{'id':s['id'],'ok':True,'result':q}]
            context={'case_inputs':{'province_id':2644},'saved_campaign':{'player_id':42},'run_dir':str(root),
                'state_dir':str(root),'repo_root':str(REPO)}
            # The known source capability packet is used directly rather than
            # guessing which capability names the adapter requires.
            def request(self,identifier,tool,args):return {'body':q}
            with mock.patch('ck3_live_run_id.current_machine_id',return_value='synthetic-machine-not-live'),\
                 mock.patch.object(A.CommonRelay,'request',request),mock.patch.object(M,'require_capabilities'),\
                 mock.patch.object(M,'validate_fixture',return_value={}),mock.patch.object(A,'load',return_value=SimpleNamespace(initialize_once=init)):
                result=A.run_case(context,Client())
            self.assertEqual(captured['army_id'],0);self.assertTrue(result['controlled_initializer_qualified'])
        if RECEIPT:
            RECEIPT.write_text(json.dumps({'machine_id':MACHINE,'status':'PASS','test':'readonly_rebound_and_zero_full_id',
                'synthetic_cases':counts,'actual_live_calls':0,'R05_pass':False},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--candidate-root',type=Path)
    p.add_argument('--temp-root',type=Path,required=True);p.add_argument('--receipt',type=Path);a=p.parse_args()
    REPO=a.repo_root.resolve();CANDIDATE=(a.candidate_root or REPO).resolve();TEMP=a.temp_root;TEMP.mkdir(parents=True,exist_ok=True)
    RECEIPT=a.receipt
    sys.path[:0]=[str(REPO/'ck3_autonomous_player/src'),str(REPO/'tools')]
    from ck3_live_run_id import current_machine_id
    MACHINE=current_machine_id()
    M=load('xar_autoplayer.bridge.r05_low_supply_fixture',REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
    T=load('r05_existing_observe_factory',REPO/'tools/test_r05_supply_observation_case.py')
    T.I=load('r05_existing_initializer_factory',REPO/'tools/test_r05_low_supply_fixture.py');T.I.M=M
    O=load('xar_autoplayer.bridge.r05_supply_observation_case',CANDIDATE/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_supply_observation_case.py')
    T.M=M;T.O=O
    A=load('r05_actual_initializer_adapter',CANDIDATE/'tools/ck3_mod_acceptance_cases/r05_low_supply_adapter.py')
    unittest.main(argv=[__file__],verbosity=2)
