"""Root's actual readback of retained synthetic evidence; no EXE execution."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,sys
B=Path(__file__).parent
S=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p02')
sys.path.insert(0,str(S))
spec=importlib.util.spec_from_file_location('root_cold_reader',S/'run_parent_entry_cold.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
from parent_entry_execution_contract import normalize_rows
def pin(path):
 path=Path(path);assert path.stat().st_size<=1048576
 raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def read(ref):
 assert pin(ref['path'])==ref
 return json.loads(Path(ref['path']).read_bytes())
def load(path):return json.loads(Path(path).read_bytes())
suite_pin=pin(B/'cold-a01/SELECTED-COLD.actual.json')
assert suite_pin['sha256']=='283358b05236d5ae92b74fd671587ea5635dd8f54759f0f940af8656b9a6b7fa'
suite=read(suite_pin);machine='desktop-3fevhd2-1c74096080'
assert suite['machine_id']==machine and len(suite['selected_cases'])==17
assert len(set(suite['selected_cases']))==17 and suite['selected_cases'][-1]=='cancel_late'
assert set(suite['selected_cases'])==set(runner.CASES)
root_system=load(B/'ROOT-ACTUAL-SYSTEM-REVIEW.actual-a01.json')
assert root_system['accepted'] is True
names={};case_pins=[]
for case_pin in suite['cases']:
 case=read(case_pin);name=case['case'];base=Path(case_pin['path']).parent
 assert name not in names and case['machine_id']==machine and case['status']=='PASS'
 assert case['real_CK3'] is False and case['full_R08'] is False
 target=case['actual_target_result']
 assert target['synthetic'] is True and target['return_failures']==target['audit_failures']==0
 rows=[]
 if case['raw'] is not None:
  read_bytes=Path(case['raw']['path']).read_bytes();assert pin(case['raw']['path'])==case['raw']
  rows=[json.loads(line) for line in read_bytes.splitlines() if line.strip()]
 audit=read(case['independent_audit'])
 assert audit['all_required_owned_DR_vectors_equal'] is True
 computed=runner.verify_audit(rows,audit['before'],audit['after'],name in runner.REFUSALS)
 assert computed['all_required_owned_DR_vectors_equal'] is True
 for label in ('target','observer'):
  wait=load(base/(label+'.ORIGINAL-WAIT.actual.json'))
  original=load(base/(label+'.POPEN.actual.json'))
  assert wait['machine_id']==machine and wait['original_Popen'] is True and wait['original_wait'] is True
  assert wait['exit_code']==case[label+'_original_exit'] and wait['pid']==original['pid'] and wait['created']==original['created']
  expected='maintenance_parent_entry_'+('cold_target' if label=='target' else 'observer')+'.exe'
  assert Path(original['argv'][0])==B/'build-a01'/expected
 assert case['target_original_exit']==0
 if name in runner.REFUSALS:
  runner.assert_zero_arm_refusal(rows,case['observer_original_exit'],(base/'READY.actual.json').exists())
  assert target['actual_body_calls']==0 and case['native_consumer'] is None
 else:
  assert rows[0]['machine_id']==machine and rows[0]['synthetic'] is True
  meta=runner.read_meta(base/'target.meta.txt')
  actual=normalize_rows(rows,runner.expected_from_meta(meta,machine,rows[0]['capture_ms']))
  assert actual==case['native_consumer'] and actual['cleanup_complete'] is True
 if name=='foreign257_then_target':
  assert (target['foreign_body_calls'],target['target_body_calls'])==(257,1)
  assert any(r.get('kind')=='foreign_resume' and r.get('RF_once') is True and r.get('RIP_unchanged') is True and r.get('DR0_retained') is True and r.get('TF') is False for r in rows)
 if name=='occupied-dr':assert target['occupied_warmup_calls']==1
 if name=='occupied-tf':assert audit['independent_preexisting_TF_preserved_before_target_release'] is True
 if name in runner.FAULTS:
  hold=load(base/'ACTUAL-NATIVE-FAULT-HOLD.actual.json')
  assert hold['injected_native_API_seam'] is True and hold['real_OS_fault_proven'] is False
 if name=='cancel_late':
  assert any(r.get('owned_late_event') is True for r in rows)
  assert case['native_consumer']['reason']=='cancel' and case['native_consumer']['target_entry_retained'] is False
 names[name]={'target_exit':case['target_original_exit'],'observer_exit':case['observer_original_exit'],'full6':True,'raw_rows':len(rows)}
 case_pins.append(case_pin)
assert set(names)==set(suite['selected_cases'])
wait=load(B/'cold-execution-a02/ORIGINAL-WAIT.actual-a01.json')
assert wait['original_Popen'] is True and wait['original_wait'] is True and wait['exit_code']==0
value=dict(schema='xar.e04.Root.actual-cold-readback.v1',machine_id=machine,
 observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted_readback=True,
 suite=suite_pin,cases=names,case_pin_count=len(case_pins),original_case_wait_count=34,
 actual_full6_recomputed_from_raw_and_peer_rows=True,real_CK3=False,full_R08=False,
 qualification_pending_independent_review=True,old_attempt_unchanged='10PASS/occupied-drFAIL/6notstarted/target wait UNKNOWN',formal_dynamic_scenes='5/11')
raw=(json.dumps(value,indent=2)+'\n').encode()
out=B/'ROOT-ACTUAL-COLD-READBACK.actual-a01.json'
with out.open('xb') as f:f.write(raw)
print(json.dumps(dict(readback=pin(out),actual_cases=17,case_original_waits=34,full6=True)))
