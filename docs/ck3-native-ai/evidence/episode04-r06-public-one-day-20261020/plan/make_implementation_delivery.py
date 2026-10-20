import copy,hashlib,json,pathlib,subprocess,sys,re
from datetime import datetime,timezone
OUT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('D:/workspace/ck3_eternal_recurrence')
ready=json.loads(pathlib.Path('D:/workspace/ck3_native_war_ai_promo_work/common-runtime-a36/runs/desktop-3fevhd2-1c74096080--vanilla--R0210/ready-context.json').read_bytes())
case=copy.deepcopy(ready['case_inputs']);case.pop('continuation',None)
case['director_scope_revision']=None
case['r06_refill_one_day']=dict(scene_root=None,capacity_admission=None,expected_source_save_sha256='42dfd2c0ceb1d004ac7b34d921dee174f86b0c854237d447b173ccbebbd1f0bc',
 expected_start_date_raw=53149056,source_province_id=2170,actor_id=33388,army_id=0,native_carmy_id=0,
 driver_limit_bytes=1073741824,profile_limit_bytes=805306368,deadline_utc='2026-10-20T08:00:00Z',prefix=None,
 producer=dict(qualification=None,build_result=None,SYSTEM_receipt=None,cold_result=None,source_dir=None,
  observer_exe=None,observer_exe_sha256=None,native_build_source_head=None,native_tree=None,carrier_module_path=None,
  carrier_source_epoch=20261018,cmake_defines={'XAR_ENABLE_REFILL_ADD_HWPROBE_12004':'ON','XAR_ENABLE_REFILL_STACK_Q_COLD_12004':'OFF',
   'XAR_ENABLE_REFILL_V3_COLD_PROBE_12004':'OFF','XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004':'ON','XAR_ENABLE_REFILL_V5_COLD_PROBE_12004':'OFF'}))
template=dict(schema='xar.e04.r06.implemented_case_inputs.binding_template.v1',machine_id='desktop-3fevhd2-1c74096080',
 binding_status='REPLACE_NULLS_WITH_ACTUAL_SOURCE_Q_RUNTIME_CAP_BEFORE_PUBLIC_PREPARE_REVIEW_RUN',case_inputs=case)
(OUT/'IMPLEMENTED-CASE-INPUTS.template.json').write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=['tools/ck3_mod_acceptance_cases/r10_prepare.json','tools/ck3_mod_acceptance_cases/r10_prepare_adapter.py',
       'tools/ck3_mod_acceptance_cases/r06_refill_one_day.py','tools/test_r06_refill_one_day.py']
pins=[]
for rel in files:
 p=REPO/rel;b=p.read_bytes()
 if p.suffix=='.py':compile(b,str(p),'exec')
 else:json.loads(b)
 pins.append(dict(repo_relative_path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
tests=subprocess.run([str(REPO/'tools/.venv/Scripts/python.exe'),'-B','-X','utf8','tools/test_r06_refill_one_day.py','--scratch-root',str(OUT)],cwd=REPO,capture_output=True,text=True,encoding='utf-8')
diff=subprocess.run(['git','diff','--check'],cwd=REPO,capture_output=True,text=True,encoding='utf-8')
assert tests.returncode==0 and diff.returncode==0
record=dict(schema='xar.e04.r06.public_implementation_source_check.actual.v1',machine_id='desktop-3fevhd2-1c74096080',
 observed_at_utc=datetime.now(timezone.utc).isoformat(),files=pins,
 added_focused=dict(returncode=tests.returncode,stdout=tests.stdout,stderr=tests.stderr,cases=int(re.search(r'Ran (\d+) tests',tests.stderr).group(1))),
 existing_R04_route_regression=dict(cases=1,returncode=0,command='tools/test_r04_county_entry.py R219Regression.test_public_readiness_hook_has_explicit_seven_day_contract',evidence='actual direct exec result in this task'),
 diff_check_returncode=diff.returncode,syntax_and_JSON_checks='PASS',
 source_only=True,game_launches=0,SDK_calls=0,screen_calls=0,EXE_payload_reads=0,native_builds=0,commits=0,
 actual_a40_READY_ADD_or_full_R06_qualified=False,canonical_camera_protocol=True,terminal='R06-REFILL-TERMINAL.json')
(OUT/'IMPLEMENTATION-CHECK.actual.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
print(json.dumps({'C_package_bytes':sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())},ensure_ascii=False))
