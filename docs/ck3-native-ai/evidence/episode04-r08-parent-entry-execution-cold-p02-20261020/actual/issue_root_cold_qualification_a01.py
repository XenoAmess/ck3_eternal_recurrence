"""Issue the limited cold qualification after actual Root and peer review."""
from pathlib import Path
import datetime,hashlib,json,sys
B=Path(__file__).parent
sys.path.insert(0,'D:/workspace/ck3_eternal_recurrence/tools')
from ck3_live_run_id import current_machine_id
def pin(path):
 path=Path(path);assert path.stat().st_size<=1048576
 raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def load(path):return json.loads(Path(path).read_bytes())
review=B/'cold-review-a01/INDEPENDENT-ACTUAL-17-COLD-REVIEW.actual-a01.json'
review_pin=pin(review)
assert review_pin['bytes']==105158 and review_pin['sha256']=='109784b48604c246334d5e2697d3cbf1d0271145ca0c6ab5503bccf6f65dc994'
peer=load(review)
assert peer['status']=='INDEPENDENT_REVIEW_PASS_RECOMMEND_STANDALONE_EXECUTION_COLD_ACCEPTANCE' and peer['actual_cases']==17
root=load(B/'ROOT-ACTUAL-COLD-READBACK.actual-a01.json')
assert root['accepted_readback'] is True and root['actual_full6_recomputed_from_raw_and_peer_rows'] is True and root['original_case_wait_count']==34
machine=current_machine_id();assert machine==root['machine_id']==peer['machine_id']=='desktop-3fevhd2-1c74096080'
gate=load(B/'EXECUTION-GATE.actual.json');record=load(B/'MACHINE-BUILD.actual.json')
suite_pin=pin(B/'cold-a01/SELECTED-COLD.actual.json');suite=load(suite_pin['path'])
assert suite_pin==peer['suite'] and suite_pin['sha256']==root['suite']['sha256']
assert set(suite['selected_cases'])==set(root['cases']) and len(suite['selected_cases'])==17
assert record['source_pins']==load(gate['source_manifest']['path'])['files']
observer_record=next(f for f in gate['files'] if Path(f['path']).name=='maintenance_parent_entry_observer.exe')
observer=pin(observer_record['path'])
assert observer['sha256']==observer_record['sha256']=='fe05bc177791fc6d41e25e1f05ab85e62c826e0f78c67dd066cbb0c477126c14'
for source in record['source_pins']:assert pin(source['path'])==source
mode='parent-entry-execution-once-v1'
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
accept=dict(schema='xar.maintenance.parent_entry.Root-cold-acceptance.v1',
 machine_id=machine,observed_at_utc=stamp,mode=mode,accepted=True,
 observer_sha256=observer['sha256'],source_pins=record['source_pins'],
 cold_suite_sha256=suite_pin['sha256'],accepted_cases=suite['selected_cases'],
 independent_review=review_pin,Root_actual_readback=pin(B/'ROOT-ACTUAL-COLD-READBACK.actual-a01.json'),
 Root_actual_SYSTEM_review=pin(B/'ROOT-ACTUAL-SYSTEM-REVIEW.actual-a01.json'),
 scope='Exact standalone synthetic execution-DR cold only; same machine/exact observer/source',
 actual_case_original_waits=34,full_six_DR_preserved=True,occupied_main_warmup_calls=1,
 native_API_fault_seams_only=True,spontaneous_OS_failure_coverage=False,
 CK3_or_public_live_qualification=False,parent_return_observed=False,
 paid_maintenance_raw=None,payer=None,cadence=None,full_R08=False,
 formal_dynamic_scenes='5/11',research='10/14',business='7/11',
 old_attempt='Retained10PASS/occupied-drFAIL/6notstarted/target original wait UNKNOWN',
 next_live_prerequisites=['fresh same-machine background Steam offline qualification',
   'fresh game EXE/runtime and budget/public entry admission',
   'exact original CaseClient owner pair and distinct finite Root scope'],
 retention_review_by_utc='2026-10-22T20:15:00Z')
accept_path=B/'ROOT-COLD-ACCEPTANCE.actual-a01.json'
accept_raw=(json.dumps(accept,indent=2)+'\n').encode()
with accept_path.open('xb') as out:out.write(accept_raw)
q=dict(schema='xar.maintenance.parent_entry.execution-qualification.v1',
 status='SELECTED_EXECUTION_COLD_PASS',mode=mode,machine_id=machine,observed_at_utc=stamp,
 observer_pin=observer,source_pins=record['source_pins'],
 SYSTEM_receipt_pin=gate['SYSTEM_receipt'],cold_suite_pin=suite_pin,
 Root_acceptance_pin=pin(accept_path),
 limited_to='Exact17 standalone synthetic cold; runtime requires separate fresh Root admission',
 real_CK3=False,public_runtime_qualification=False,paid_maintenance_raw=None,payer=None,
 cadence=None,full_R08=False,formal_dynamic_scenes='5/11')
q_path=B/'PARENT-ENTRY-EXECUTION-QUALIFICATION.actual-a01.json'
q_raw=(json.dumps(q,indent=2)+'\n').encode()
with q_path.open('xb') as out:out.write(q_raw)
print(json.dumps(dict(acceptance=pin(accept_path),qualification=pin(q_path),accepted_cases=17,CK3=False,full_R08=False)))
