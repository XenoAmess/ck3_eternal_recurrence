"""New connected capacity cases; Driver sizes are stat-only mocked, no large file."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from copy import deepcopy
from datetime import datetime,timezone
import argparse,ast,hashlib,importlib.util,json,os,sys,tempfile,unittest
P=argparse.ArgumentParser();P.add_argument('--candidate-dir',type=Path)
opts,rest=P.parse_known_args();sys.dont_write_bytecode=True
HERE=opts.candidate_dir or Path(__file__).parent
spec=importlib.util.spec_from_file_location('runtime_budget_subject',HERE/'r10_compare.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
M=1024*1024;S='c4992c304d196135d9590799d69ffb3c9f5510e6';NOW=datetime(2026,10,16,1,tzinfo=timezone.utc);END='2080-01-01T00:00:00+00:00'
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.scene=self.root/'scene';self.scene.mkdir();self.admit=self.root/'capacity.json'
  self.row={'admitted':True,'machine_id':'synthetic-runtime','source_head':S,'source_binding':{'new_clean_integrated_source_head':S},
   'scene_root':str(self.scene),'component_ceiling_bytes':{'driver':2*1024*M},'new_scene_aggregate_bytes':3*1024*M,'quota_review_at_utc':END}
  self.pin=self.save(self.row)
 def save(self,row):
  raw=json.dumps(row).encode();self.admit.write_bytes(raw);return [str(self.admit),hashlib.sha256(raw).hexdigest()]
 def budget(self,n=1024*M,pin=None,clock=lambda:NOW):
  return c.RuntimeTotalBudget(n,self.pin if pin is None else pin,scene_root=self.scene,source_head=S,machine_id='synthetic-runtime',deadline_utc=END,clock=clock)
 def io(self):
  run=self.scene/'run';case=self.scene/'ledger'/'case';state=self.scene/'state-a01'/'native-session'/'army-query-history-results'
  for p in (run/'requests',run/'responses',case,state):p.mkdir(parents=True,exist_ok=True)
  self.driver=state/'driver.json';self.driver.write_bytes(b'{}');self.calls=[]
  io=SimpleNamespace(assets=self.scene,run=run,case=case,ledger=case.parent,
      binding={'pid':7,'process_create_time_100ns':8,'generation':1,'actor':9,'episode':'synthetic'},meta={'machine_id':'synthetic-runtime','source_head':S})
  def request(name,tool,args):
   self.calls.append(tool);(run/'responses'/'original.json').write_bytes(b'{}');return {'original':True},{'pin':'original'}
  io.request=request;return io
 def virtual_size(self,size):
  original=Path.stat;target=self.driver
  def stat(p,*a,**kw):
   value=original(p,*a,**kw)
   if p==target:
    fields=list(value);fields[6]=size() if callable(size) else size;return os.stat_result(fields)
   return value
  return patch.object(Path,'stat',stat)
 def test_default_and_precise_Root_admission_rejections(self):
  b=c.runtime_total_budget({},scene_root=self.scene,source_head=S,machine_id='synthetic-runtime',deadline_utc=END)
  self.assertEqual(b.limit_bytes,512*M)
  with self.assertRaisesRegex(ValueError,'requires exact'):c.runtime_total_budget({'max_runtime_total_bytes':1024*M},scene_root=self.scene,source_head=S,machine_id='synthetic-runtime',deadline_utc=END)
  self.assertEqual(self.budget().limit_bytes,1024*M)
  for edit in (lambda r:r.update(machine_id='other'),lambda r:r.update(source_head='d'*40),
    lambda r:r.update(scene_root=str(self.root/'other')),lambda r:r.update(admitted=False),
    lambda r:r['source_binding'].update(new_clean_integrated_source_head='d'*40),
    lambda r:r['component_ceiling_bytes'].update(driver=512*M),lambda r:r.update(new_scene_aggregate_bytes=100),
    lambda r:r.update(quota_review_at_utc='2020-01-01T00:00:00+00:00')):
   row=deepcopy(self.row);edit(row);pin=self.save(row)
   with self.assertRaises(ValueError):self.budget(pin=pin)
  self.pin=self.save(self.row)
  with self.assertRaisesRegex(ValueError,'SHA'):self.budget(pin=[str(self.admit),'0'*64])
  with self.assertRaisesRegex(ValueError,'expired'):self.budget(clock=lambda:datetime(2081,1,1,tzinfo=timezone.utc))
 def test_raw_sidecars_counted_once_and_before_transport_budget_gate(self):
  io=self.io();budget=c.RuntimeTotalBudget(scene_root=self.scene,source_head=S,machine_id='synthetic-runtime',deadline_utc=END,clock=lambda:NOW)
  base=SimpleNamespace(RUN_BUDGET=512*M)
  with self.virtual_size(500*M):
   budget.bind_live(io,base_module=base,raw_file_max=32*M)
   self.assertLess(budget.used_bytes([self.scene/'state-a01',self.scene/'state-a01/native-session']),501*M)
   with self.assertRaisesRegex(ValueError,'reserve next'):io.request('query','ck3_query_army_strengths',{})
  self.assertEqual(self.calls,[]);self.assertEqual(base.RUN_BUDGET,512*M)
 def test_optin_transport_once_and_postfailure_retains_original(self):
  io=self.io();budget=self.budget();base=SimpleNamespace(RUN_BUDGET=512*M)
  with self.virtual_size(500*M):
   budget.bind_live(io,base_module=base,raw_file_max=32*M)
   value=io.request('query','ck3_query_army_strengths',{})
  self.assertTrue(value[0]['original']);self.assertEqual(self.calls,['ck3_query_army_strengths']);self.assertEqual(base.RUN_BUDGET,512*M)
  # CArmy is resolved lazily by the existing Root reader; capacity binds the
  # process while the unchanged Root cohort guards own Army identity.
  second=self.io();second.binding['native_carmy_id']=42;self.budget().bind_live(second)
  with self.assertRaisesRegex(ValueError,'changed'):
   second=self.io();self.budget(n=768*M).bind_live(second)
  # Original response survives an unexpected write after the preflight check.
  other=self.scene/'ledger2'/'case';other.mkdir(parents=True);io.case=other;io.ledger=other.parent;io._runtime_total_bound=False
  changed={'n':0};prior=io.request
  def grow(*args):
   self.calls.append('original-once');changed['n']=1100*M
   (io.run/'responses'/'overflow-original.json').write_bytes(b'{}');return 'original-return'
  io.request=grow
  fresh=self.budget();fresh.bind_live(io,base_module=base)
  with self.virtual_size(lambda:changed['n']):
   with self.assertRaisesRegex(ValueError,'crossed bound'):io.request('once','ck3_execute_step',{})
  self.assertTrue((io.run/'responses'/'overflow-original.json').is_file());self.assertEqual(self.calls.count('original-once'),1);self.assertEqual(base.RUN_BUDGET,512*M)
 def test_expiry_or_mutated_admission_stops_before_request(self):
  io=self.io();now=[NOW];budget=self.budget(clock=lambda:now[0]);budget.bind_live(io)
  now[0]=datetime(2081,1,1,tzinfo=timezone.utc)
  with self.assertRaisesRegex(ValueError,'expired'):io.request('expired','ck3_take_snapshot',{})
  now[0]=NOW;self.admit.write_bytes(b'{}')
  with self.assertRaisesRegex(ValueError,'changed'):io.request('changed','ck3_take_snapshot',{})
  self.assertEqual(self.calls,[])
 def test_A_real_parser_and_constructor_budget_seam(self):
  if opts.candidate_dir is None:self.skipTest('explicit external A source rebuild only; installed parser checked by integration')
  spec=importlib.util.spec_from_file_location('A_runtime_builder',HERE/'build_runtime_candidate.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
  source=builder.sources()[builder.REL+'strategy_a_stages.py'][1];module=ast.parse(source)
  parser=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='parser')
  ns={'argparse':argparse,'Path':Path,'__doc__':'synthetic parser'};exec(compile(ast.Module(body=[parser],type_ignores=[]),'A-real-parser','exec'),ns)
  cli=ns['parser']();argv=['advance-common-horizon']
  for action in cli._actions:
   if action.required and action.option_strings:argv.extend([action.option_strings[0],'1' if action.type is int else str(self.root)])
  argv.extend(['--max-runtime-total-bytes',str(1024*M),'--runtime-capacity-admission',*self.pin]);args=cli.parse_args(argv)
  self.assertEqual(args.max_runtime_total_bytes,1024*M);self.assertEqual(args.runtime_capacity_admission,self.pin)
  ctor=next(n for n in ast.walk(module) if isinstance(n,ast.FunctionDef) and n.name=='__init__')
  nodes=[]
  for i,node in enumerate(ctor.body):
   if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='budget' for t in node.targets):nodes=ctor.body[i:i+2];break
  io=self.io();io.machine='synthetic-runtime';io.deadline=datetime.fromisoformat(END)
  ns={'self':io,'args':args,'c':c,'source':S,'h':SimpleNamespace(RUN_BUDGET=512*M)}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'A-real-constructor-budget','exec'),ns)
  self.assertEqual(io.runtime_total_budget_bytes,1024*M);self.assertTrue(io._runtime_total_bound)
if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest],verbosity=2)
