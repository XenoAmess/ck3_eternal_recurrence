import datetime,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'D:/workspace/ck3_eternal_recurrence/tools')
from ck3_live_run_id import current_machine_id
B=Path('C:/w/e04parentdr02');out=B/'ROOT-ACTUAL-SYSTEM-REVIEW.actual-a01.json'
def pin(p):
 p=Path(p);assert p.stat().st_size<=1048576;b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def read(ref):
 got=pin(ref['path']);assert all(got[k]==ref[k] for k in ['bytes','sha256']);return json.loads(Path(ref['path']).read_bytes())
machine=current_machine_id();assert machine=='desktop-3fevhd2-1c74096080'
gpin=pin(B/'EXECUTION-GATE.actual.json');assert gpin['sha256']=='4129cdd7ca18df3d47fde54036a6ecb5cdbde4fe8d2283cb3087d42ea57bd8cf'
g=read(gpin);assert g['machine_id']==machine
report=read(g['producer']);record=read(g['original_build']);receipt=read(g['SYSTEM_receipt']);manifest=read(g['SYSTEM_manifest']);source=read(g['source_manifest'])
assert report['build_succeeded'] is True and report['defender_exclusions']['status']=='verified'
assert receipt['status']=='verified' and receipt['system_token_sid']=='S-1-5-18' and receipt['admin_token'] is True
assert receipt['missing_requested_paths']==[] and receipt['partial_mutation'] is False
for key in ['observed_extensions_unchanged','observed_processes_unchanged','observed_prior_settings_preserved']:assert receipt[key] is True
assert receipt['files']==manifest['files']==g['files'] and len(g['files'])==2
names={'maintenance_parent_entry_observer.exe','maintenance_parent_entry_cold_target.exe'}
assert {Path(r['path']).name for r in g['files']}==names
for r in g['files']:
 p=Path(r['path']);got=pin(p);assert p.parent==B/'build-a01' and got['bytes']==r['size'] and got['sha256']==r['sha256']
 assert str(p).casefold() in {str(x).casefold() for x in receipt['verified_requested_paths']}
assert record['machine_id']==machine and record['returncode']==0 and record['source_pins']==source['files'] and len(source['files'])==14
S=Path('C:/ck3-war-episode04-research-20261004-a01/e04-r08-parent-dr-source-p02')
assert Path(g['source_manifest']['path']).parent==S
for ref in source['files']:
 got=pin(ref['path']);assert Path(ref['path']).parent==S and all(got[k]==ref[k] for k in ['bytes','sha256'])
prepare=next(r for r in source['files'] if Path(r['path']).name=='prepare_parent_entry_admission.py')
assert prepare['sha256']=='9079d4dcd3fc3310ec276b32576245cd7065a5d05d3667bc3f966da104a4daa0'
wait=read(record['original_wait']);assert wait['original_Popen'] is True and wait['original_wait'] is True and wait['exit_code']==0 and wait['argv']==record['argv']
obj=dict(schema='xar.e04.Root.parent-dr.actual-SYSTEM-review.v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 accepted=True,scope='Actual standalone repaired candidate compile and exact2 project EXE permanent SYSTEM exclusions only',gate=gpin,producer=g['producer'],original_build=g['original_build'],source_manifest=g['source_manifest'],SYSTEM_receipt=g['SYSTEM_receipt'],SYSTEM_manifest=g['SYSTEM_manifest'],files=g['files'],
 actual_ROOT_read_full_receipt_manifest_report=True,all14_actual_p02_source_output_pins_verified=True,admin_token=True,system_token_sid='S-1-5-18',missing_requested_paths=[],prior_settings_preserved=True,
 cold_still_pending=True,game_or_public_runtime_qualification=False,original_compile_wait0=True,new_project_EXE_executions_before_this_review=0,
 formal_credits=[5,11],research_credits=[10,14],business_credits=[7,11],
 retention=dict(review_by_utc='2026-10-22T19:35:00Z',reason='Actual exact gate for bounded cold and next qualification; no automatic renewal'))
raw=(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n').encode();assert len(raw)+Path(__file__).stat().st_size<=16384
with out.open('xb') as f:f.write(raw)
print(json.dumps(dict(receipt=pin(out),SYSTEM_status=receipt['status'],files=g['files'],Root_bytes=len(raw)+Path(__file__).stat().st_size)))
