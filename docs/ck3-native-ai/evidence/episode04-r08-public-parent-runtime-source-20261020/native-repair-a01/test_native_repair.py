"""Python control-flow mocks only. Never launches native binaries or DR APIs."""
import copy,importlib.util,json,pathlib,sys,tempfile,types,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT));sys.path.insert(1,'C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p01')
spec=importlib.util.spec_from_file_location('repair_runner',ROOT/'run_parent_entry_cold.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
M='desktop-3fevhd2-1c74096080'
def arm():return dict(kind='arm',success=False,saved_debug=[],readback=True,armed_debug=[100,0,0,0,0xffff0ff0,0x401],thread_id=11,thread_generation=1,thread_created=12)
class Checks(unittest.TestCase):
 def test_refusal_accepts_only_complete_nonmutating_diagnostic(self):
  m.assert_zero_arm_refusal([arm()],1,False);m.assert_zero_arm_refusal([],2,False)
  changes=[{'success':True},{'success':0},{'saved_debug':[0]*6},{'saved_debug':None},{'readback':False},{'readback':1},{'armed_debug':[]},{'armed_debug':[False]*6},{'armed_debug':[-1]*6},{'armed_debug':[2**64]*6},{'thread_id':True},{'thread_generation':0},{'thread_created':None}]
  for fields in changes:
   with self.subTest(fields=fields),self.assertRaises(ValueError):m.assert_zero_arm_refusal([dict(arm(),**fields)],1,False)
  for kind in ('parent_entry','restore','foreign_resume','ready','cleanup_owned_execution'):
   with self.subTest(kind=kind),self.assertRaises(ValueError):m.assert_zero_arm_refusal([dict(kind=kind)],1,False)
  for code,ready in [(0,False),(127,False),(1,True)]:
   with self.assertRaises(ValueError):m.assert_zero_arm_refusal([],code,ready)
 def exercise(self,detached,valid_diagnostic):
  with tempfile.TemporaryDirectory(prefix='native-repair-mock-',dir=ROOT) as tmp:
   root=pathlib.Path(tmp);out=root/'occupied-dr';objects=[];events=[]
   meta={'parent_schema':'xar.maintenance.parent_entry.cold-meta.v1','pid':'1001','created':'10','tid':'11','full_id':'33388','local_player_id':'1','character':'100','context':'200','module_base':'1000','module_size':'4000','parent_entry':'1100','clock_pointer':'300','game_state':'400','date_raw':'53149056','absolute_day':'2214544','foreign_limit':'512'}
   for e in ('go','cancel','audit','finish','fault_release'):meta[e+'_event']='Local\\MOCK1001'+e
   start=dict(kind='start',schema='xar.maintenance.parent_entry.raw.v1',mode='parent-entry-execution-once-v1',machine_id=M,synthetic=True,owner_binding=None,pid=1001,created=10,entry=1100)
   terminal=dict(kind='terminal',restored=True,detached=detached,cleanup_complete=True,pending_event=False)
   diag=arm()
   if not valid_diagnostic:diag['readback']=False
   rows=[start,diag,terminal]
   before=[dict(tid=11,created=12,complete=True,dr=[100,0,0,0,0,1],eflags=2)]
   after=[dict(tid=11,created=12,complete=True,dr=[100,0,0,0,0xffff0ff0,0x401],eflags=2)]
   class Fake:
    def __init__(self,pid):self.pid=pid;self.returncode=None if pid==1001 else 1;self.wait_calls=0
    def poll(self):return self.returncode
    def wait(self,timeout=None):
     self.wait_calls+=1
     if self.returncode is None:self.returncode=9
     return self.returncode
   def popen(argv,**kwargs):
    p=Fake(1001+len(objects));objects.append(p)
    if p.pid==1001:
     (out/'target.meta.txt').write_text(''.join(k+'='+v+'\n' for k,v in meta.items()))
     (out/'target.initial-debug.json').write_text(json.dumps(before))
    else:(out/'observer.raw.ndjson').write_text(''.join(json.dumps(dict(r,python_control_flow_mock=True))+'\n' for r in rows))
    return p
   class Win:
    def identity(self,p):return dict(pid=p.pid,created=10 if p.pid==1001 else 20)
    def event(self,n):
     events.append(n)
     if n.endswith('audit'):(out/'target.after-debug.json').write_text(json.dumps(after))
     if n.endswith('finish'):objects[0].returncode=0
   real=m.write
   def write(p,v):real(p,dict(v,python_control_flow_mock=True,native_EXE_execution=False))
   opts=types.SimpleNamespace(output_root=root,build_dir=ROOT/'NO-NATIVE-EXE')
   with patch.object(m.subprocess,'Popen',popen),patch.object(m,'write',write),patch.object(m.time,'sleep',lambda x:None):
    with self.assertRaises(ValueError):m.run_case(opts,'occupied-dr',M,{'python_control_flow_mock':True},Win())
   self.assertEqual(len(objects),2)
   for label,p in zip(('target','observer'),objects):
    actual=json.loads((out/(label+'.ORIGINAL-WAIT.actual.json')).read_text())
    self.assertEqual(actual['pid'],p.pid);self.assertEqual(actual['exit_code'],p.returncode);self.assertGreater(p.wait_calls,0)
   self.assertFalse(json.loads((out/'FAILED.actual.json').read_text())['qualified'])
   self.assertTrue((out/'INDEPENDENT-DR-AUDIT-FAILED.actual.json').exists())
   self.assertEqual(any(x.endswith('finish') for x in events),detached)
   self.assertEqual(objects[0].returncode,0 if detached else 9)
   return
 def test_audit_failure_can_finish_only_exact_detached_synthetic_and_stays_failed(self):self.exercise(True,True)
 def test_exception_cleanup_hold_exit_still_persists_closed_original_wait(self):self.exercise(False,False)
 def test_six_register_comparison_is_not_masked(self):
  a=[dict(tid=1,created=2,complete=True,dr=[1,0,0,0,0,1])]
  b=copy.deepcopy(a);b[0]['dr'][4]=0xffff0ff0;b[0]['dr'][5]=0x401
  with self.assertRaises(ValueError):m.verify_audit([],a,b,True)
 def test_fixture_source_keeps_TF_held_and_adds_main_roundtrip(self):
  t=(ROOT/'parent_entry_cold_target.cpp').read_text()
  self.assertIn('c.Dr6=0xffff0ff0ULL',t);self.assertIn('|0x401ULL',t)
  self.assertIn('if(mode==L"occupied-dr"){\n   SetEvent(warmup_event)',t)
  self.assertIn('InterlockedIncrement(&occupied_warmup_calls);SetEvent(warmed_event)',t)
  self.assertIn('tf_held=mode==L"occupied-tf"',t)
if __name__=='__main__':unittest.main(verbosity=2)
