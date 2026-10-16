"""Exact one-batch reclamation; no recursive deletion or source mutation."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, ctypes as c, hashlib, importlib.util, json, os, shutil, subprocess, sys

BASE=Path(__file__).parent
REPO=Path('D:/workspace/ck3_eternal_recurrence')
MACHINE='desktop-3fevhd2-1c74096080'
INPUT=Path('C:/ck3-e04-resume-20261015-a01/capacity-r183-a01/R183-OLD-MELTS.readonly-a01.json')
ROOTS=[Path('C:/ck3-superman-qiang-20261004'),Path('C:/ck3-superman-qiang-110-20261004'),Path('C:/ck3-superman-qiang-media-redo-20261004')]
DECODER=Path('D:/workspace/ck3_native_war_ai_promo_work/episode01-effect-save-attempt-008/rakaly-0.8.19-x86_64-pc-windows-msvc/rakaly.exe')
spec=importlib.util.spec_from_file_location('retire','C:/ck3-e04-resume-20261015-a01/capacity-lane/win32_exact_retire_lib.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
k=lib.k
k.ReadFile.argtypes=[c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32),c.c_void_p];k.ReadFile.restype=c.c_int
k.SetFilePointerEx.argtypes=[c.c_void_p,c.c_longlong,c.POINTER(c.c_longlong),c.c_uint32];k.SetFilePointerEx.restype=c.c_int
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    raw=(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    if len(raw)>1048576:raise RuntimeError('Report exceeds 1 MiB')
    with Path(p).open('xb') as f:f.write(raw)
def checked(p,roots):
    p=Path(os.path.abspath(p))
    if p.resolve(strict=True)!=p:raise RuntimeError('Resolved path differs')
    if not any(p.is_relative_to(r) for r in roots):raise RuntimeError('Outside exact authorized roots')
    for q in [p,*p.parents]:
        if q.lstat().st_file_attributes&0x400:raise RuntimeError('Reparse ancestor rejected: '+str(q))
    return p
def hash_handle(h):
    if not k.SetFilePointerEx(h,0,None,0):raise c.WinError(c.get_last_error())
    out=hashlib.sha256();buf=c.create_string_buffer(1024*1024);n=c.c_uint32()
    while True:
        if not k.ReadFile(h,buf,len(buf),c.byref(n),None):raise c.WinError(c.get_last_error())
        if not n.value:break
        out.update(buf.raw[:n.value])
    return out.hexdigest()
def protect(p,expected=None):
    p=checked(p,ROOTS+[DECODER.parent]);h=lib.open_handle(p,0x80000000|0x80,1)
    try:
        info=lib.get_info(h,p);actual=hash_handle(h)
        if expected and actual!=expected:raise RuntimeError('Retained source SHA mismatch: '+str(p))
        return h,{'path':str(p),'sha256':actual,'info':info}
    except BaseException:k.CloseHandle(h);raise
def machine_guard():
    r=subprocess.run([sys.executable,'-B',str(REPO/'tools/ck3_live_run_id.py'),'machine'],cwd=REPO,capture_output=True,text=True,check=True)
    if r.stdout.strip()!=MACHINE:raise RuntimeError('Wrong machine')
def make_plan():
    machine_guard();data=json.loads(INPUT.read_text(encoding='utf-8'));rows=[];rejected=[];locks={}
    context=json.loads((BASE/'CONTEXT.actual-a01.json').read_text(encoding='utf-8'))
    if context['relevant_processes']:raise RuntimeError('Relevant process requires fresh review')
    try:
        for old in data['rows']:
            if not old.get('decoder_path'):
                rejected.append({'path':old['path'],'reason':'Missing checkpoint SHA / exact decoder recipe; R0014 retained'});continue
            p=checked(old['path'],ROOTS);rp=checked(old['report_path'],ROOTS)
            report=json.loads(rp.read_text(encoding='utf-8'));cmd=report['melt_command']
            if Path(cmd[0])!=DECODER or cmd[1]!='melt' or cmd[3:7]!=['--format','ck3','--unknown-key','stringify'] or cmd[7]!='-o' or Path(cmd[8])!=p:raise RuntimeError('Unrecognized exact recipe')
            src=checked(cmd[2],ROOTS)
            evidence=[]
            for source,expected in [(src,report['retained_checkpoint_sha256']),(DECODER,report['decoder_sha256']),(rp,None)]:
                key=str(source)
                if key not in locks:locks[key]=protect(source,expected)
                elif expected and locks[key][1]['sha256']!=expected:raise RuntimeError('Inconsistent input identity')
                evidence.append(locks[key][1])
            h=lib.open_handle(p,0x80000000|0x80,0)
            try:
                info=lib.get_info(h,p)
                if info['links']!=1:raise RuntimeError('Hard-linked candidate rejected')
                if info['b']!=old['logical_bytes']:raise RuntimeError('Candidate size changed')
                actual=hash_handle(h)
                if actual!=report['melted_sha256'] or report['melt_exit_code']!=0:raise RuntimeError('Historical export SHA / exit mismatch')
            finally:k.CloseHandle(h)
            rows.append({'asset_id':'derived-superman-melt-'+actual,'replica_id':MACHINE+':'+str(p),'path':str(p),'sha256':actual,'info':info,'category':'derived','state':'closed_and_superseded','last_used_at_utc':report['at_utc'],'expires_at_utc':(datetime.fromisoformat(report['at_utc'])+timedelta(hours=48)).isoformat(),'active_references':[],'protected_until_utc_or_null':None,'reason':'Closed Oct4 published Superman acceptance/media; decoded text is reconstructible from retained immutable binary and pinned exact decoder; no current consumer or valid protection identified','melt_command':cmd,'retained_inputs':evidence,'summary_evidence':str(rp)})
        plan={'schema':'xar.storage-superman-melt-plan.v1','machine_id':MACHINE,'at_utc':now(),'policy_version':'1.0.0','input_manifest_sha256':sha(INPUT),'context_sha256':sha(BASE/'CONTEXT.actual-a01.json'),'closure_evidence':['docs/release-changelogs/superman-qiang/1.0.0.md','docs/release-changelogs/superman-qiang/1.1.0.md'],'task':'disk-reclamation-20261016-a01','authorized_roots':[str(r) for r in ROOTS],'candidate_count':len(rows),'logical_candidate_bytes':sum(x['info']['b'] for x in rows),'allocated_single_link_candidate_bytes':sum(x['info']['allocation'] or 0 for x in rows),'retained_input_review_at_utc':(datetime.now(timezone.utc)+timedelta(hours=48)).isoformat(),'retention_note':'Current original binary saves and exact decoder remain readable; review sources at this deadline without automatic renewal. This receipt does not change their independent lifecycle.','rows':rows,'excluded':rejected,'method':'Target SHA under exclusive read handle; retained checkpoint and decoder current SHA under write/delete-denying handles; no directory deletion'}
        if len(rows)!=21 or len(rows)>1000:raise RuntimeError('Unexpected scope')
        write(BASE/'BATCH01.plan.actual-a01.json',plan)
        print(json.dumps({k:v for k,v in plan.items() if k not in ('rows',)},ensure_ascii=False,indent=2))
        print('PLAN_SHA256',sha(BASE/'BATCH01.plan.actual-a01.json'))
    finally:
        for h,_ in locks.values():k.CloseHandle(h)
def execute(expected):
    machine_guard();pp=BASE/'BATCH01.plan.actual-a01.json'
    if sha(pp)!=expected:raise RuntimeError('Plan SHA changed')
    plan=json.loads(pp.read_text(encoding='utf-8'))
    if plan['machine_id']!=MACHINE or plan['candidate_count']!=21:raise RuntimeError('Wrong exact batch')
    locks={};results=[];before={v:shutil.disk_usage(v).free for v in ('C:/','D:/')}
    write(BASE/'BATCH01.intent.actual-a01.json',{'machine_id':MACHINE,'at_utc':now(),'plan_sha256':expected,'count':21,'logical_bytes':plan['logical_candidate_bytes'],'authorization':'User 2026-10-16 dedicated disk reclamation task; shared policy 1.0.0; Root delegated exact expired project-derived files','method':'Win32 exclusive GENERIC_READ+DELETE+READ_ATTRIBUTES share0; current content and identity equal plan; same handle deletion; original inputs protected from write/delete throughout'})
    try:
        for row in plan['rows']:
            for ref in row['retained_inputs']:
                if ref['path'] in locks:continue
                lock,actual=protect(ref['path'],ref['sha256'])
                if actual['info']!=ref['info']:k.CloseHandle(lock);raise RuntimeError('Protected input metadata changed')
                locks[ref['path']]=(lock,actual)
        with (BASE/'BATCH01.files.actual-a01.jsonl').open('x',encoding='utf-8') as ledger:
            for row in plan['rows']:
                result={'path':row['path'],'status':'not_deleted','logical_bytes':row['info']['b']};h=None
                try:
                    p=checked(row['path'],ROOTS)
                    if p.name!='melted.ck3':raise RuntimeError('Unexpected leaf')
                    h=lib.open_handle(p,0x80000000|0x10000|0x80,0);info=lib.get_info(h,p)
                    if info!=row['info'] or info['links']!=1:raise RuntimeError('Frozen candidate identity/metadata changed')
                    if hash_handle(h)!=row['sha256']:raise RuntimeError('Candidate SHA changed')
                    flag=lib.Disposition(True)
                    if not k.SetFileInformationByHandle(h,4,c.byref(flag),c.sizeof(flag)):raise c.WinError(c.get_last_error())
                    k.CloseHandle(h);h=None
                    if p.exists():raise RuntimeError('Absence readback failed')
                    result.update(status='deleted_unavailable',sha256=row['sha256'],allocated_bytes=info['allocation'],file_id=info['id'],links=info['links'],exists_after=False,deleted_at_utc=now())
                except Exception as ex:result['error']=str(ex)
                finally:
                    if h is not None:k.CloseHandle(h)
                results.append(result);ledger.write(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n');ledger.flush()
        retained=[]
        for h,ref in locks.values():
            actual=lib.get_info(h,Path(ref['path']));retained.append({'path':ref['path'],'sha256':ref['sha256'],'identity_metadata_unchanged':actual==ref['info'],'exists_after':Path(ref['path']).exists()})
        gone=[r for r in results if r['status']=='deleted_unavailable'];result={'schema':'xar.storage-superman-melt-retirement.v1','machine_id':MACHINE,'at_utc':now(),'policy_version':'1.0.0','plan_sha256':expected,'attempted':len(results),'deleted':len(gone),'failed':len(results)-len(gone),'deleted_logical_bytes':sum(r['logical_bytes'] for r in gone),'deleted_single_link_allocated_bytes':sum(r['allocated_bytes'] or 0 for r in gone),'free_before':before,'free_after':{v:shutil.disk_usage(v).free for v in before},'volume_change_attribution':'Only same-handle confirmed single-link allocation counted as retired; C/D whole-volume delta includes concurrent Root/OS activity and is not attributed entirely to reclamation','retained_inputs_after':retained,'excluded':plan['excluded'],'directory_deletions':0,'recovery_note':'Deleted original melted paths are no longer readable; original historical results/SHA remain true. Rebuild only to a NEW derived output path with preserved command and retained binary; do not fabricate the original file.','detailed_ledger_sha256':sha(BASE/'BATCH01.files.actual-a01.jsonl')}
        write(BASE/'BATCH01.result.actual-a01.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('retained_inputs_after',)},ensure_ascii=False,indent=2))
        print('RETAINED',len(retained),'UNCHANGED',all(r['identity_metadata_unchanged'] and r['exists_after'] for r in retained))
    finally:
        for h,_ in locks.values():k.CloseHandle(h)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['plan','execute']);p.add_argument('--plan-sha256');a=p.parse_args()
    if a.mode=='plan':make_plan()
    elif not a.plan_sha256:p.error('--plan-sha256 required')
    else:execute(a.plan_sha256)
