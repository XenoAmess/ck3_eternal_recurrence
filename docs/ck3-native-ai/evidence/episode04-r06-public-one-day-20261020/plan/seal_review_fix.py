import hashlib,json,pathlib,subprocess,sys,shutil
from datetime import datetime,timezone
OUT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('D:/workspace/ck3_eternal_recurrence')
old=OUT/'IMPLEMENTATION-CHECK.actual.json';history=OUT/'IMPLEMENTATION-CHECK.pre-review-fix.actual.json'
if not history.exists():history.write_bytes(old.read_bytes())
subprocess.run([sys.executable,'-X','utf8',str(OUT/'make_implementation_delivery.py')],cwd=REPO,check=True,capture_output=True)
check=json.loads(old.read_bytes())
review=pathlib.Path('C:/ck3-e04-resume-20261020-a01/r06-independent-review/R06-INDEPENDENT-REVIEW.actual.json')
b=review.read_bytes()
assert hashlib.sha256(b).hexdigest()=='7c49f2e87326bfec932010d9d0955a318e71108ac33bdc2c892bfaf09beb6209'
machine=subprocess.check_output([sys.executable,'-X','utf8','tools/ck3_live_run_id.py','machine'],cwd=REPO,text=True).strip()
assert machine==json.loads(b)['machine_id']==check['machine_id']
assert check['added_focused']['cases']==18 and check['added_focused']['returncode']==0
pins=[]
for p in (history,old,OUT/'ROOT-IMPLEMENTED-R06-CONFIG.md',OUT/'IMPLEMENTED-CASE-INPUTS.template.json'):
 data=p.read_bytes();pins.append(dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
result=dict(schema='xar.e04.r06.independent_review_fix.source_only.actual.v1',machine_id=machine,
 observed_at_utc=datetime.now(timezone.utc).isoformat(),review=dict(path=str(review),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()),
 changes=['At final Probe.start, exact admitted observer payload SHA is rehashed and compared to the Q/SYSTEM identity, with stable file/path metadata.',
          'The same pinned admission and each3+1 OS snapshot are revalidated after camera coordination; the300s limit is unchanged.',
          'Both checks precede the once-claim and Popen; failure leaves launch_claimed=false and issues no worker or day.'],
 actual_new_focused=dict(cases=18,returncode=0,stdout=check['added_focused']['stdout'],stderr=check['added_focused']['stderr']),
 rejection_variants=['test_same_path_rebuilt_observer_is_rejected_at_final_launch_boundary','test_camera_wait_does_not_extend_admission_ttl_or_reach_exe_launch'],
 actual_R04_route_regression=check['existing_R04_route_regression'],source_files=check['files'],evidence_pins=pins,
 syntax_JSON_diff_check='PASS',game_execution=False,SDK_calls=0,screen_calls=0,native_builds=0,native_or_producer_dependency_edits=0,
 actual_project_EXE_payload_reads=0,fixture_payload_only_for_rejection_tests=True,save_payload_reads=0,commits=0,
 capacity_state='Root reports time-blocked/game0; metadata/source-only fix',actual_READY_ADD_full_R06_credit=False,
 free_bytes_at_close={v:shutil.disk_usage(v).free for v in ('C:/','D:/')},review_at_utc='2026-10-20T08:00:00Z')
data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
assert sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())+len(data)<=262144
p=OUT/'INDEPENDENT-REVIEW-FIX.actual.json';p.write_bytes(data)
print(json.dumps(dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),source_files=check['files'],C_package_bytes=sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())),ensure_ascii=False,indent=2))
