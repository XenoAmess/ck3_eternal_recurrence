"""Replay one actual R209 RED through common full-client/R05 recovery.

The successful native DTO and public queue are synthetic boundaries. No SDK,
native query, clock, initializer or new live qualification is executed.
"""
from pathlib import Path
import argparse,copy,gzip,hashlib,importlib.util,json,sys,tempfile,unittest
from types import SimpleNamespace
from unittest import mock

OPTIONS=None

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def from_source(name,path,source):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;exec(compile(source,str(path),'exec'),m.__dict__);return m

def zero_ids(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('army_id','subject_army_id') and v==18:value[k]=0
            elif k in ('native_carmy_id','subject_carmy_id') and v==85:value[k]=0
            else:zero_ids(v)
    elif isinstance(value,(list,tuple)):
        for v in value:zero_ids(v)

class ActualRedRecovery(unittest.TestCase):
    def test_actual_not_started_common_chain_and_bounded_counterexamples(self):
        repo=OPTIONS.repo_root.resolve()
        sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools')]
        paths=('ck3_autonomous_player/src/xar_autoplayer/bridge/r05_supply_observation_case.py','tools/ck3_mod_acceptance_full_army.py')
        if OPTIONS.candidate_builder:
            _,sources=load('pre_snapshot_builder',OPTIONS.candidate_builder).sources(repo)
        else:sources={p:(repo/p).read_text(encoding='utf-8-sig') for p in paths}
        from xar_autoplayer import bridge
        fixture=load('xar_autoplayer.bridge.r05_low_supply_fixture',repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/r05_low_supply_fixture.py')
        bridge.r05_low_supply_fixture=fixture
        O=from_source('xar_autoplayer.bridge.r05_supply_observation_case',repo/paths[0],sources[paths[0]])
        F=from_source('ck3_mod_acceptance_full_army',repo/paths[1],sources[paths[1]])
        T=load('pre_snapshot_existing_factory',repo/'tools/test_r05_supply_observation_case.py')
        T.I=load('pre_snapshot_initializer_factory',repo/'tools/test_r05_low_supply_fixture.py');T.I.M=fixture;T.O=O
        evidence=OPTIONS.actual_red or repo/'docs/ck3-native-ai/acceptance/2026-10-18-r209-r05-pre-snapshot-recovery/actual-R209-pre-snapshot-red.json.gz'
        raw=evidence.read_bytes();self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(544,'b51bc525a249619fceec77a2beb4d6cdc7b35a9bd5fa4440daf8af4a4c109a61'))
        expanded=gzip.decompress(raw);self.assertEqual((len(expanded),hashlib.sha256(expanded).hexdigest()),(1142,'6aca29df2851285eafead293f6211baf30359ae0dde2a3d59e9ab1c1958c6f79'))
        actual=json.loads(expanded);actual_row=actual['rows'][0]
        self.assertEqual(O.classify_strength_pre_snapshot_not_started(actual_row)['submit'],-1)
        for mutate in ('worker','native','reader','pre_snapshot','paused','map_ready','submit','native_returned'):
            bad=copy.deepcopy(actual_row)
            original=O.classify_strength_pre_snapshot_not_started(actual_row)[mutate]
            bad['error']=bad['error'].replace(mutate+'='+str(original),mutate+'=changed',1)
            self.assertIsNone(O.classify_strength_pre_snapshot_not_started(bad))
        counts={}
        for mode in ('actual_success','not_started_twice','native_started','unknown','changed_date'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory(dir=OPTIONS.temp_root,prefix='pre-snapshot-') as temp:
                root=Path(temp);c=T.Client(root)
                for value in (c.frame,c.query,c.before,c.after):zero_ids(value)
                c.frame['revision']=11;c.query['queried_revision']=11
                c.frame['managed_campaign_run_binding']={'run_id':'synthetic-episode'}
                c.selection.run_dir=Path('synthetic-episode');c.report_path=root/'synthetic-native-report.json'
                queries=[];seen=[];original=c.execute_plan
                def execute(steps,name,timeout=None,reserve=90):
                    s=steps[0];seen.append(copy.deepcopy(s))
                    if s['tool']=='ck3_query_army_strengths':
                        queries.append(copy.deepcopy(s))
                        if mode=='unknown':raise TimeoutError('synthetic lost result; never retry')
                        if len(queries)==1 or mode=='not_started_twice':
                            row=copy.deepcopy(actual_row);row['id']=s['id'];row['plan']=copy.deepcopy(s)
                            if mode=='native_started':row['error']=row['error'].replace(';submit=-1',';submit=1',1)
                            c.checkpoint(name+'.actual-results',{'rows':[row]})
                            if len(queries)==1:
                                c.frame['revision']+=1;c.frame['native_revision']+=1
                                c.frame['snapshot_id']='native:'+str(c.frame['native_revision'])
                                if mode=='changed_date':c.frame['date_raw']+=24
                                c.query.update(queried_revision=c.frame['revision'],queried_native_revision=c.frame['native_revision'],queried_snapshot_id=c.frame['snapshot_id'])
                            return [row]
                    rows=original(steps,name,timeout,reserve)
                    if s['tool']=='ck3_query_army_strengths':rows[0]['after_snapshot']=copy.deepcopy(c.frame)
                    return rows
                c.execute_plan=execute
                wire_calls=[]
                wire=SimpleNamespace(mark=lambda p:{'synthetic_wire_boundary':True},
                    recover=lambda *a,**kw:(wire_calls.append('recover') or copy.deepcopy(c.query),{'synthetic_full_DTO_boundary':True}))
                wrapped=F.FullArmyResultClient(c,wire,prefix='focused-pre-snapshot')
                initial=T.init_result(c);initial.update(army_id=0,carmy_id=0)
                io=O.ObservationIO(wrapped,T.settings(),context={'output':str(root),'machine_id':'synthetic-machine-not-live',
                    'command_timeout':10,'state_dir':str(root/'state')},initialization=initial)
                # Success decoding is synthetic; failure classification, public
                # step rebinding and all R05 fresh-frame/target guards are real.
                with mock.patch.object(F,'normalized_full',side_effect=lambda raw,*a,**kw:raw):
                    if mode=='actual_success':
                        got=io.sample('focused')
                        self.assertEqual(got['frame']['revision'],12)
                        self.assertEqual(len(queries),2);self.assertEqual(len(wire_calls),1)
                        proof=io.readonly_strength_recoveries[0]
                        self.assertEqual(proof['recovery_reason'],'pre_snapshot_failed_native_not_started')
                        self.assertEqual(proof['status'],'second_readonly_query_completed')
                        self.assertEqual(proof['first_RED']['terminal_row']['error'],actual_row['error'])
                        self.assertTrue(Path(proof['first_RED']['original']['path']).is_file())
                        self.assertEqual([s['args']['expected_revision'] for s in queries],[11,12])
                        self.assertTrue(all(s['args']['army_ids']==[0] and s['args']['profile']=='observed_history_full_v1' for s in queries))
                    else:
                        with self.assertRaises((ValueError,TimeoutError)):io.sample('focused')
                        self.assertTrue(io.strength_recovery_failed)
                        self.assertEqual(len(queries),2 if mode=='not_started_twice' else 1)
                self.assertEqual(len({s['id'] for s in queries}),len(queries))
                self.assertTrue(all(s['tool'] in ('ck3_take_snapshot','ck3_query_army_strengths') for s in seen))
                counts[mode]=len(queries)
        print(json.dumps({'status':'PASS' if len(counts)==5 else 'RED','actual_RED':'R209 day03 before pre_snapshot not started',
            'query_counts':counts,'SDK_calls':0,'native_query_executions':0,'R05_live_credit':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--candidate-builder',type=Path);p.add_argument('--actual-red',type=Path)
    p.add_argument('--temp-root',type=Path,required=True);OPTIONS=p.parse_args();OPTIONS.temp_root.mkdir(parents=True,exist_ok=True)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ActualRedRecovery))
    raise SystemExit(0 if r.wasSuccessful() else 1)
