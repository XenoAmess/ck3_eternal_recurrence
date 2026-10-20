"""Focused new contract and actual CLI tests; no CK3/native execution."""
from pathlib import Path
import copy,json,os,subprocess,sys,tempfile,unittest
from parent_entry_execution_contract import MODE,PREFIX_SHA,SCHEMA,normalize_rows,parse_meta
HERE=Path(__file__).resolve().parent
def sample():
 e=dict(machine_id="fixture-machine",synthetic=True,pid=20,created=100,entry=0x1000,character=0x4000,full_id=33388,context=0x8000,local_player_id=1,game_state=0xa000,date_raw=100,absolute_day=10,foreign_limit=512,capture_ms=30000,admission_id="synthetic-cold",owner_binding=None)
 s=dict(kind="start",schema=SCHEMA,mode=MODE,prefix_sha256=PREFIX_SHA,target_record_limit=1,**e)
 arm=dict(kind="arm",thread_id=7,thread_generation=1,thread_created=500,success=True,readback=True,saved_debug=[0,0,0,0,0xffff0ff0,0x400],armed_debug=[0x1000,0,0,0,0xffff0ff0,0x401])
 ready=dict(kind="ready",census_complete=True)
 foreign=dict(kind="foreign_resume",count=1,thread_id=7,thread_generation=1,thread_created=500,RIP_unchanged=True,DR0_retained=True,RF_once=True,TF=False)
 hit=dict(kind="parent_entry",thread_id=7,thread_generation=1,thread_created=500,RIP=0x1000,RDX=0x4000,RCX=0xb000,R8=2,R9=3,RSP=0xc000,DR6=0xffff0ff1,qpc=123,first_read_complete=True,second_read_complete=True,full_id_before=33388,full_id_after=33388,magic_before=0x43686172,magic_after=0x43686172,death_before=0,death_after=0,context_before=0x8000,context_after=0x8000,return_before=0xd000,return_after=0xd000,state_before=0xa000,state_after=0xa000,date_before=124,date_after=124,day_before=11,day_after=11,source_anchor_matches=True,entry_owner_clock_qualified=True,admitted_context_unchanged=True,parent_return_observed=False,paid_maintenance_raw=None,payer=None,cadence=None)
 restore=dict(kind="restore",thread_id=7,thread_generation=1,thread_created=500,readback=True,equal_original=True,debug=arm["saved_debug"][:])
 terminal=dict(kind="terminal",reason="target_captured",capture_count=1,foreign_count=257,restored=True,detached=True,pending_event=False,cleanup_complete=True,process_exited=False,observation_thread_admission_complete=True,window_complete=False,full_R08=False)
 return [s,arm,ready,foreign,hit,restore,terminal],e
class ContractTests(unittest.TestCase):
 def test_target_after257_and_context_drift(self):
  rows,e=sample();r=normalize_rows(rows,e);self.assertTrue(r["target_entry_qualified"]);self.assertFalse(r["full_R08"])
  rows[4].update(context_before=0x9000,context_after=0x9000,admitted_context_unchanged=False)
  r=normalize_rows(rows,e);self.assertTrue(r["target_entry_retained"]);self.assertTrue(r["target_entry_qualified"]);self.assertFalse(r["admitted_context_unchanged"])
 def test_incomplete_identity_clock_not_payment(self):
  for field in ("full_id_after","magic_after","state_after","date_after","day_after"):
   with self.subTest(field=field):
    rows,e=sample();rows[4][field]+=1;rows[4]["entry_owner_clock_qualified"]=False;rows[-1]["reason"]="target_read_incomplete"
    r=normalize_rows(rows,e);self.assertTrue(r["target_entry_retained"]);self.assertFalse(r["target_entry_qualified"]);self.assertIsNone(r["paid_maintenance_raw"])
 def test_real_semantic_mutations_rejected(self):
  changes=[(0,"pid",21),(1,"thread_created",0),(1,"saved_debug",[1,0,0,0,0,0]),(1,"armed_debug",[0x1000,0,0,0,0,1<<64]),
   (3,"thread_generation",2),(3,"RF_once",False),(3,"TF",True),(4,"RDX",0x4008),(4,"thread_created",501),
   (4,"entry_owner_clock_qualified",False),(4,"paid_maintenance_raw",0),(5,"debug",[0]*6),(5,"thread_created",501),
   (6,"reason","timeout"),(6,"cleanup_complete",False),(6,"pending_event",True)]
  for i,key,value in changes:
   with self.subTest(i=i,key=key):
    rows,e=sample();rows[i][key]=value
    with self.assertRaises(ValueError):normalize_rows(rows,e)
 def test_cleanup_new_generation_requires_real_readback(self):
  rows,e=sample();late=dict(kind="cleanup_thread_unarmed",thread_id=8,thread_generation=1,thread_created=600,readback=True,debug=[0,0,0,0,0xffff0ff0,0x400])
  rows.insert(-1,late);self.assertTrue(normalize_rows(rows,e)["cleanup_complete"])
  for k,v in (("readback",False),("thread_generation",0),("debug",[0x1000,0,0,0,0,1])):
   with self.subTest(k=k):
    bad=copy.deepcopy(rows);bad[-2][k]=v
    with self.assertRaises(ValueError):normalize_rows(bad,e)
 def test_zero_timeout_and_foreign_limit_are_partial(self):
  rows,e=sample();rows=[r for r in rows if r["kind"] not in ("parent_entry","foreign_resume")]
  rows[-1].update(reason="timeout",capture_count=0,foreign_count=0)
  r=normalize_rows(rows,e);self.assertFalse(r["target_entry_retained"]);self.assertFalse(r["window_complete"])
  rows,e=sample();rows=[r for r in rows if r["kind"]!="parent_entry"];rows[-1].update(reason="foreign_limit",capture_count=0,foreign_count=512)
  self.assertFalse(normalize_rows(rows,e)["target_entry_retained"])
  rows[-1]["foreign_count"]=511
  with self.assertRaises(ValueError):normalize_rows(rows,e)
 def test_missing_restore_and_unknown_hold_reject(self):
  rows,e=sample();rows=[r for r in rows if r["kind"]!="restore"]
  with self.assertRaises(ValueError):normalize_rows(rows,e)
  rows,e=sample();rows.insert(3,dict(kind="unresolved_cleanup_hold",cleanup_complete=False,no_more_capture=True,Popen_must_remain_retained=True))
  with self.assertRaises(ValueError):normalize_rows(rows,e)
 def test_script_actual_empty_cwd_and_stat_cap(self):
  root=HERE/"test-tmp";root.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as name:
   cwd=Path(name);rows,e=sample();raw=cwd/"raw.jsonl";binding=cwd/"binding.json";out=cwd/"result.json"
   raw.write_text("".join(json.dumps(r)+"\n" for r in rows),encoding="utf-8");binding.write_text(json.dumps(e),encoding="utf-8")
   args=[sys.executable,"-B",str(HERE/"consume_parent_entry_actual.py"),"--raw",str(raw),"--binding",str(binding),"--output",str(out)]
   p=subprocess.run(args,cwd=cwd,capture_output=True);self.assertEqual(p.returncode,0,p.stderr.decode())
   self.assertTrue(json.loads(out.read_bytes())["target_entry_qualified"])
   blob=b"x"*(1024*1024+1)
   aggregate=HERE.parent.parent
   current=sum(f.stat().st_size for f in aggregate.rglob("*") if f.is_file())
   self.assertLessEqual(current-raw.stat().st_size+len(blob),4*1024*1024)
   raw.write_bytes(blob);out.unlink();p=subprocess.run(args,cwd=cwd,capture_output=True)
   self.assertEqual(p.returncode,2);self.assertIn(b"stat cap",p.stderr);self.assertFalse(out.exists())
 def test_prepare_rejects_old_qualification_in_actual_script(self):
  root=HERE/"test-tmp";root.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as name:
   cwd=Path(name);scope=cwd/"scope.json";q=cwd/"old-q.json";scope.write_text("{}");q.write_text('{"schema":"old-A08","compiled_bytes_qualified":true}')
   args=[sys.executable,"-B",str(HERE/"prepare_parent_entry_admission.py"),"--prepare-parent-entry"]
   for key,path in (("repo",cwd),("snapshot",cwd/"none"),("cash",cwd/"none"),("root-scope",scope),("qualification",q),("observer",cwd/"none.exe"),("output-root",cwd/"out")):args+=["--"+key,str(path)]
   p=subprocess.run(args,cwd=cwd,capture_output=True);self.assertEqual(p.returncode,2);self.assertIn(b"new execution qualification",p.stderr);self.assertFalse((cwd/"out").exists())
 def test_metadata_rejects_duplicate_and_wrong_schema(self):
  with self.assertRaises(ValueError):parse_meta("x=1\nx=2\n")
 def test_capture_and_foreign_after_cleanup_rejected(self):
  rows,e=sample();restore=rows.pop(5);rows.insert(4,restore)
  with self.assertRaises(ValueError):normalize_rows(rows,e)
  rows,e=sample();foreign=rows.pop(3);rows.insert(-1,foreign)
  with self.assertRaises(ValueError):normalize_rows(rows,e)
 def test_queued_owned_event_and_real_runner_audit_boundary(self):
  import run_parent_entry_cold as runner
  rows,e=sample()
  late=dict(kind="cleanup_owned_execution",owned_late_event=True,thread_id=7,thread_generation=1,thread_created=500,RIP=e["entry"],restored_generation=True,debug=rows[1]["saved_debug"][:])
  rows.insert(-1,late);self.assertTrue(normalize_rows(rows,e)["cleanup_complete"])
  before=[dict(tid=7,created=500,complete=True,dr=rows[1]["saved_debug"][:])]
  self.assertTrue(runner.verify_audit(rows,before,copy.deepcopy(before))["all_required_owned_DR_vectors_equal"])
  with self.assertRaises(ValueError):runner.verify_audit(rows,before,[dict(tid=7,created=501,complete=True,dr=before[0]["dr"])])
  rows[-2]["thread_generation"]=2
  with self.assertRaises(ValueError):normalize_rows(rows,e)
if __name__=="__main__":unittest.main()
