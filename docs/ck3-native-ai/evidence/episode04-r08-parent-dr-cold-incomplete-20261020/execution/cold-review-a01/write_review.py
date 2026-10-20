"""Offline metadata projection only; never import a runner or call native APIs."""
from pathlib import Path
import datetime,hashlib,json
B=Path('C:/w/e04parentdr01');R=B/'cold-a01';O=B/'cold-review-a01'
M='desktop-3fevhd2-1c74096080'
def raw(p):
 p=Path(p);s=p.stat();assert s.st_size<=262144
 b=p.read_bytes();assert len(b)==s.st_size;return b
def pin(p):
 p=Path(p);b=raw(p);return dict(path=str(p.relative_to(B)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(p):return json.loads(raw(p))
def same(ref):
 p=Path(ref['path']);q=pin(p);assert q['bytes']==ref['bytes'] and q['sha256']==ref['sha256'];return q
capfile=B/'capacity/PARENT-DR-NATIVE64-1915-COLD-ADMISSION.actual-a04.json'
cp=pin(capfile);assert cp['bytes']==6951 and cp['sha256']=='d6e13b67f5902834195372849613fd37818f0e8ad98ed8b53c5d39652e0d7574'
cap=load(capfile);assert cap['machine_id']==M and cap['cold_execution_admitted'] is True
now=datetime.datetime.now(datetime.timezone.utc);assert now<datetime.datetime.fromisoformat(cap['hard_deadline_utc'].replace('Z','+00:00'))
selected=cap['selected_cases'];assert len(selected)==17 and selected[-1]=='cancel_late'
globalwait=load(B/'cold-execution-a01/ORIGINAL-WAIT.actual-a01.json')
assert globalwait['machine_id']==M and globalwait['original_Popen'] is True and globalwait['original_wait'] is True and globalwait['exit_code']==1
assert globalwait['argv']==cap['allowed_phase_argv']['cold-selected-suite']
cases=[]
for name in selected:
 d=R/name
 if not d.exists():cases.append(dict(case=name,status='NOT_STARTED',qualification=False));continue
 if not (d/'CASE.actual.json').exists():
  before=load(d/'target.initial-debug.json');after=load(d/'target.after-debug.json');a={(x['tid'],x['created']):x for x in after};changes=[]
  for x in before:
   k=(x['tid'],x['created'])
   if k in a and x['dr']!=a[k]['dr']:changes.append(dict(tid=k[0],created=k[1],before=x['dr'],after=a[k]['dr']))
  lines=[json.loads(x) for x in raw(d/'observer.raw.ndjson').splitlines()]
  cases.append(dict(case=name,status='FAILED_NOT_QUALIFIED',source_files=[pin(d/f) for f in ['observer.raw.ndjson','observer.ORIGINAL-WAIT.actual.json','target.POPEN.actual.json','target.initial-debug.json','target.after-debug.json','target.result.json','UNRESOLVED-OWNER-HOLD.actual.json']],six_DR_changes=changes,observer_terminal=lines[-1],failed_arm_diagnostics=[x for x in lines if x.get('kind')=='arm'],target_original_wait_receipt_present=(d/'target.ORIGINAL-WAIT.actual.json').exists(),FAILED_receipt_present=(d/'FAILED.actual.json').exists(),target_exit_code=None,target_original_wait=None,qualification=False))
  continue
 c=load(d/'CASE.actual.json');assert c['machine_id']==M and c['status']=='PASS' and c['full_R08'] is False
 result=load(d/'target.result.json');assert result==c['actual_target_result'] and result['return_failures']==0 and result['audit_failures']==0
 tw=load(d/'target.ORIGINAL-WAIT.actual.json');ow=load(d/'observer.ORIGINAL-WAIT.actual.json')
 for label,w in [('target',tw),('observer',ow)]:
  p=load(d/(label+'.POPEN.actual.json'));assert w['machine_id']==M and w['original_Popen'] is True and w['original_wait'] is True and (w['pid'],w['created'])==(p['pid'],p['created'])
 assert tw['exit_code']==c['target_original_exit']==0 and ow['exit_code']==c['observer_original_exit']
 audit=load(d/'INDEPENDENT-DR-AUDIT.actual.json');assert audit['machine_id']==M and audit['all_required_owned_DR_vectors_equal'] is True
 before=load(d/'target.initial-debug.json');after=load(d/'target.after-debug.json');assert before==audit['before'] and after==audit['after']
 assert all(x['complete'] is True and len(x['dr'])==6 for x in before+after)
 amap={(x['tid'],x['created']):x['dr'] for x in after};bmap={(x['tid'],x['created']):x['dr'] for x in before}
 assert all(k not in amap or amap[k]==v for k,v in bmap.items())
 refs=[pin(d/f) for f in ['CASE.actual.json','target.result.json','target.ORIGINAL-WAIT.actual.json','observer.ORIGINAL-WAIT.actual.json','INDEPENDENT-DR-AUDIT.actual.json','target.initial-debug.json','target.after-debug.json']]
 assert same(c['independent_audit'])==refs[4]
 row=dict(case=name,status='ACTUAL_CASE_PASS',proofs=refs,body=result['actual_body_calls'],foreign_body=result['foreign_body_calls'],target_body=result['target_body_calls'],return_and_argument_failures=result['return_failures'],target_wait=tw['exit_code'],observer_wait=ow['exit_code'],independent_peer_count=len(after),six_DR_equal=True,semantic_qualification=False)
 if c['raw'] is not None:
  rp=Path(c['raw']['path']);rows=[json.loads(x) for x in raw(rp).splitlines()];refs.append(same(c['raw']));start=rows[0];term=rows[-1]
  assert start['pid']==tw['pid'] and start['created']==tw['created'] and term['cleanup_complete'] is True and term['restored'] is True and term['detached'] is True and term['pending_event'] is False
  retired={(x['thread_id'],x['thread_generation']) for x in rows if x['kind']=='thread_exited'}
  arms=[x for x in rows if x['kind']=='arm' and x['success'] is True]
  for x in arms:
   if (x['thread_id'],x['thread_generation']) not in retired:assert amap[(x['thread_id'],x['thread_created'])]==x['saved_debug']
  hit=[x for x in rows if x['kind']=='parent_entry'];marker=[x for x in rows if x['kind']=='foreign_resume']
  for h in hit:assert h['RDX']==start['character'] and h['RCX']==start['context'] and h['R9']==0xc001d00d12345678
  if name=='foreign257_then_target':assert term['foreign_count']==257 and result['actual_body_calls']==258 and len(hit)==1 and hit[0]['R8']==257 and marker[0]['RIP_unchanged'] and marker[0]['DR0_retained'] and marker[0]['RF_once'] and marker[0]['TF'] is False
  if name=='created_thread':assert result['worker_tid'] and any(x['thread_id']==result['worker_tid'] for x in arms) and hit[0]['thread_id']==result['worker_tid'] and hit[0]['R8']==0x1234
  if name=='foreign4096_limit':assert term['foreign_count']==4096 and term['reason']=='foreign_limit' and not hit and result['foreign_body_calls']==4096 and result['target_body_calls']==1
  if name=='timeout':assert term['reason']=='timeout' and not hit and result['actual_body_calls']==0
  row.update(reason=term['reason'],foreign_observed=term['foreign_count'],target_records=len(hit),armed_generations=len(arms),retired_generations=len(retired),new_worker_tid=result['worker_tid'],RF_marker_present=bool(marker),cleanup_complete=True)
  if name.endswith('-fault'):
   hold=load(d/'ACTUAL-NATIVE-FAULT-HOLD.actual.json');assert hold['injected_native_API_seam'] is True and hold['real_OS_fault_proven'] is False
   assert hold['observer_original_Popen']==dict(pid=ow['pid'],created=ow['created']) and hold['target_original_Popen']==dict(pid=tw['pid'],created=tw['created'])
   q=hold['raw_prefix'];blob=raw(rp);assert hashlib.sha256(blob[:q['bytes']]).hexdigest()==q['sha256']
   assert any(x['kind']=='unresolved_cleanup_hold' for x in rows);refs.append(pin(d/'ACTUAL-NATIVE-FAULT-HOLD.actual.json'));row.update(injected_native_seam=hold['fault'],real_OS_failure_proven=False,held_then_restored_and_detached=True)
 else:row.update(refusal_no_raw_no_READY=not (d/'READY.actual.json').exists())
 cases.append(row)
passed=[x['case'] for x in cases if x['status']=='ACTUAL_CASE_PASS'];failed=[x['case'] for x in cases if x['status']=='FAILED_NOT_QUALIFIED'];notstarted=[x['case'] for x in cases if x['status']=='NOT_STARTED']
assert len(passed)==10 and failed==['occupied-dr'] and len(notstarted)==6
v=dict(schema='xar.e04.parent-dr.actual-cold-independent-review.v1',machine_id=M,observed_at_utc=now.isoformat(),reference_paths_relative_to=str(B),capacity=cp,status='PARTIAL_REAL_COLD_NOT_QUALIFIED',global_original_wait=pin(B/'cold-execution-a01/ORIGINAL-WAIT.actual-a01.json'),global_exit=1,global_stderr=pin(B/'cold-execution-a01/stderr.log'),actual_SYSTEM_review=same(cap['Root_actual_SYSTEM_review']),source_manifest_reference=cap['frozen_source_manifest'],compiled_EXEs_references_only_not_rehashed=cap['selected_project_EXEs'],passed=passed,failed=failed,not_started=notstarted,case_evidence=cases,qualification_recommendation='Do not issue full selected17 execution-DR qualification. Preserve actual ten completed cells as limited standalone synthetic evidence; six later cells were not attempted; no automatic race replay.',blocking_findings=['Runner refusal guard treats any arm diagnostic as successful arm; occupied diagnostic success=false/saved_debug=[] causes first failure.','Independent occupied main thread six-slot equality fails: DR0 preserved, DR6 0 to0xffff0ff0 and DR7 1 to0x401. OS normalization is an unproved inference; exact original failed gate remains failed.','Nested audit failure prevents target original-wait and FAILED receipts; suite exits1 after hold. Target original exit/wait unavailable and not reconstructed from source or elapsed time.'],limits=dict(new_live_or_real_CK3=False,payment=False,payer=False,cadence=False,full_day=False,full_R08=False,Python_mocks_counted_as_real_cold=False,rerun_case_or_consumer=False,current_OS_absence_claim=False),future_source_suggestions=['Separate failed diagnostic arm from actual successful mutation; retain occupied refusal failure semantics.','Review a stable independently observed occupied baseline and any permitted OS-controlled-bit treatment using primary specs and a new source/admission; never mask this actual failure retroactively.','Always record original wait for every registered original Popen after it closes, including nested failure cleanup; retain unknown if original handle lost.'],primary_reference=dict(url='https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setthreadcontext',scope='Microsoft notes some OS-controlled CONTEXT values may be adjusted. This does not prove the cause of this observed delta.'))
payload=(json.dumps(v,separators=(',',':'))+'\n').encode();used=sum(p.stat().st_size for p in O.rglob('*') if p.is_file());total=sum(p.stat().st_size for p in B.rglob('*') if p.is_file())
assert used+len(payload)<=32768 and total+len(payload)<=31457280
out=O/'INDEPENDENT-ACTUAL-COLD-REVIEW.actual-a01.json'
with out.open('xb') as stream:stream.write(payload)
print(json.dumps(dict(review=pin(out),review_lane_bytes=used+len(payload),build_root_bytes=total+len(payload))))
