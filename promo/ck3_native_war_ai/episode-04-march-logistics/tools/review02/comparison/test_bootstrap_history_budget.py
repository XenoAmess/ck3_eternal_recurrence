"""One connected synthetic pipeline, no SDK construction or game connection.

Execute the real bootstrap budget statement and Driver call AST. A neutral SDK
boundary executes the real Driver budget-field assignments and store call AST;
the actual ArmyQueryHistoryStore and JSON writer then run unchanged.
"""
from pathlib import Path
from types import SimpleNamespace,ModuleType
import argparse,ast,hashlib,importlib.util,json,sys,tempfile,unittest
P=argparse.ArgumentParser();P.add_argument('--candidate-dir',type=Path);P.add_argument('--repo',type=Path);P.add_argument('--scratch-root',type=Path)
args,rest=P.parse_known_args();sys.dont_write_bytecode=True;O=args.candidate_dir
prefix='promo/ck3_native_war_ai/episode-04-march-logistics/tools/'
driver_prefix='ck3_autonomous_player/src/xar_autoplayer/bridge/'
if O is not None:
 spec=importlib.util.spec_from_file_location('bootstrap_budget_builder',O/'build_candidate.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
 data=build.sources();R=build.R
else:
 candidates=([args.repo] if args.repo else [])+[p for start in (Path(__file__).resolve().parent,Path.cwd()) for p in (start,*start.parents)]
 R=next(p for p in candidates if (p/prefix/'capture_bootstrap.py').is_file())
 data={p:(s,s) for p in (prefix+'capture_runtime_evidence.py',prefix+'capture_bootstrap.py',driver_prefix+'army_query_history_store.py',driver_prefix+'native_driver.py') for s in [(R/p).read_text(encoding='utf-8')]}
sys.path.insert(0,str(R/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison'))
import r10_compare as c
def load(name,source):
 m=ModuleType(name);m.__file__='synthetic-boundary-'+name;sys.modules[name]=m;exec(compile(source,m.__file__,'exec'),m.__dict__);return m
e=load('actual_capture_budget_evidence',data[prefix+'capture_runtime_evidence.py'][1])
store=load('actual_army_budget_store',data[driver_prefix+'army_query_history_store.py'][1])
boot_tree=ast.parse(data[prefix+'capture_bootstrap.py'][1]);driver_tree=ast.parse(data[driver_prefix+'native_driver.py'][1])
run=next(n for n in boot_tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_owned')
budget_node=next(n for n in run.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id',None)=='admit_army_history_budget')
driver_call=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and getattr(n.func,'id',None)=='NativeHeadlessGameplayDriver')
driver_class=next(n for n in driver_tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeHeadlessGameplayDriver')
ctor=next(n for n in driver_class.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
fields={'army_query_history_sidecar_limit_bytes','_army_query_history_sidecar_guard','_army_query_history_store'}
nodes=[]
for node in ctor.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr in fields for t in node.targets):nodes.append(node)
 elif isinstance(node,ast.If) and any(isinstance(v,ast.Name) and v.id in {'army_query_history_sidecar_limit_bytes','army_query_history_sidecar_guard'} for v in ast.walk(node)):nodes.append(node)
store_call=next(n for n in ast.walk(driver_class) if isinstance(n,ast.Call) and getattr(n.func,'id',None)=='ArmyQueryHistoryStore')
M=1024*1024;S='c4992c304d196135d9590799d69ffb3c9f5510e6'
class Tests(unittest.TestCase):
 def test_launch_to_actual_Driver_fields_to_writer_and_rejections(self):
  with tempfile.TemporaryDirectory(dir=args.scratch_root or O) as temp:
   root=Path(temp);scene=root/'scene';scene.mkdir();profile=scene/'profile';profile.mkdir();state=scene/'state-a01';state.mkdir()
   cap=root/'capacity.json';row={'admitted':True,'machine_id':'synthetic-bootstrap','source_head':S,'source_binding':{'new_clean_integrated_source_head':S},
    'scene_root':str(scene),'component_ceiling_bytes':{'driver':2*1024*M},'new_scene_aggregate_bytes':3*1024*M,'quota_review_at_utc':'2080-01-01T00:00:00+00:00'}
   raw=json.dumps(row).encode();cap.write_bytes(raw);pin=[str(cap),hashlib.sha256(raw).hexdigest()]
   body={'machine_id':'synthetic-bootstrap','target_build':{'version':'1.20.0.4'},'assets_root':str(scene),
    'pipe_name':'NEVER-OPENED','state_dir':str(state),'profile_dir':str(profile),'succession_lifecycle':{}}
   options=SimpleNamespace(army_history_sidecar_limit_bytes=1024*M,runtime_capacity_admission=pin)
   made=[]
   class OfflineDriverBoundary:
    def __init__(self,*unused,**kw):
     made.append(kw);self.state_dir=Path(kw['state_dir'])
     scope={'self':self,'army_query_history_sidecar_limit_bytes':kw['army_query_history_sidecar_limit_bytes'],
        'army_query_history_sidecar_guard':kw['army_query_history_sidecar_guard']}
     exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-Driver-field-statements','exec'),scope)
    def _native_driver_state_path(self):return self.state_dir/'driver-state.json'
   scope={'args':options,'body':body,'ROOT':R,'current_machine_id':lambda:'synthetic-bootstrap',
    'subprocess':SimpleNamespace(check_output=lambda *a,**kw:S+'\n'),
    'admit_army_history_budget':lambda *a,**kw:e.admit_army_history_budget(*a,**kw,budget_factory=c.runtime_total_budget),
    'NativeHeadlessGameplayDriver':OfflineDriverBoundary,'Path':Path}
   exec(compile(ast.Module(body=[budget_node],type_ignores=[]),'actual-bootstrap-budget-statement','exec'),scope)
   driver=eval(compile(ast.Expression(driver_call),'actual-bootstrap-Driver-construction','eval'),scope)
   self.assertEqual(driver.army_query_history_sidecar_limit_bytes,1024*M)
   actual=eval(compile(ast.Expression(store_call),'actual-Driver-store-call','eval'),{'self':driver,'ArmyQueryHistoryStore':store.ArmyQueryHistoryStore})
   self.assertEqual(actual.limit_bytes,1024*M);self.assertTrue(callable(actual.admission_guard))
   actual._budget=store.ByteBudget(actual.limit_bytes);actual._budget.used=512*M
   payload={'step':'query-army-strengths-v1','accepted':True,'status':'available','query_sequence':1,'army_strengths':[{'army_id':18,'status':'available'}]}
   result=actual.record(payload);ref=result.get('raw_result_reference');self.assertIsInstance(ref,dict)
   self.assertEqual(json.loads(Path(ref['path']).read_text()),payload)
   files=list(actual.evidence_dir.iterdir());cap.write_bytes(b'{}')
   refused=actual.record(payload);self.assertEqual(refused.get('unavailable_reason'),'sidecar_admission_rejected')
   self.assertIsNone(refused.get('raw_result_reference'));self.assertEqual(list(actual.evidence_dir.iterdir()),files)
   self.assertEqual(payload['accepted'],True)
   # Legacy/default API stays unchanged; the prior hard cap still refuses an
   # unbound extension, and no neutral Driver is constructed on that failure.
   for n in (0,512*M):
    limit,budget=e.admit_army_history_budget(SimpleNamespace(army_history_sidecar_limit_bytes=n),{},source_head=None,machine_id='unused')
    self.assertEqual(limit,n);self.assertIsNone(budget)
   before=len(made);options.runtime_capacity_admission=None
   with self.assertRaises(ValueError):exec(compile(ast.Module(body=[budget_node],type_ignores=[]),'missing-admission-before-Driver','exec'),scope)
   self.assertEqual(len(made),before)
   options.runtime_capacity_admission=pin;cap.write_bytes(raw)
   with self.assertRaises(ValueError):e.admit_army_history_budget(options,body,source_head='d'*40,machine_id='synthetic-bootstrap',budget_factory=c.runtime_total_budget)
   with self.assertRaises(ValueError):e.admit_army_history_budget(options,body,source_head=S,machine_id='other',budget_factory=c.runtime_total_budget)
   row['quota_review_at_utc']='2020-01-01T00:00:00+00:00';raw2=json.dumps(row).encode();cap.write_bytes(raw2);options.runtime_capacity_admission=[str(cap),hashlib.sha256(raw2).hexdigest()]
   with self.assertRaises(ValueError):e.admit_army_history_budget(options,body,source_head=S,machine_id='synthetic-bootstrap',budget_factory=c.runtime_total_budget)
if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest],verbosity=2)
