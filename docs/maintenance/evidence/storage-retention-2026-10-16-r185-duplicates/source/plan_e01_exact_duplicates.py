"""Plan only seven Root-scoped E01 duplicates. No deletion entrypoint."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,importlib.util,json,os,time,psutil

OUT=Path(__file__).parent;ROOT=Path('D:/workspace/ck3_native_war_ai_promo_work')
M='desktop-3fevhd2-1c74096080';DIGEST='0e7699911b05ec54acc852c6fcb31cb77e32d1de5bca8ba2a6fd054c3903589f'
LEAF='run/artifacts/raw/sha256/0E/'+DIGEST.upper()+'.mkv'
KEEP=ROOT/'episode01-r7f-index-formal-002'/LEAF
TARGETS=[ROOT/x for x in (
 'episode01-r7f-index-formal-001/'+LEAF,
 'episode01-r7e-recut-001/'+LEAF,
 'episode01-r7c-muted-palette-001/'+LEAF,
 'episode01-r7-same-battle-002/messina-original-900s.mkv',
 'episode01-r7-same-battle-002/'+LEAF,
 'episode01-r7-same-battle-001/messina-original-900s.mkv',
 'episode01-full-edge-attempt-002/gameplay-precontact-r2.mkv')]
CAP=OUT.parent/'capacity-r185-a02/R185-CAPACITY.actual-root-a01.json'
PRO=OUT.parent/'capacity-r185-a02/R185-PROTECTIONS.actual.json'
spec=importlib.util.spec_from_file_location('base',OUT.parent/'disk-reclamation-worker-a01/reclaim_superman_melts.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
lib=base.lib;k=base.k
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):
    b=json.dumps(j,ensure_ascii=False,indent=2).encode('utf-8')
    if len(b)>20000:raise RuntimeError('Per-report20k cap')
    if sum(x.stat().st_size for x in OUT.iterdir() if x.is_file())+len(b)>65536:raise RuntimeError('Total64KiB output cap')
    with p.open('xb') as f:f.write(b)
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def active_refs():
    roots={str(ROOT/p.relative_to(ROOT).parts[0]).lower() for p in TARGETS+[KEEP]};hits=[];denied=[]
    for p in psutil.process_iter(['pid','name','cmdline']):
        try:
            cmd=' '.join(p.info['cmdline'] or []).lower()
            if any(r in cmd for r in roots):hits.append({'pid':p.pid,'name':p.info['name']})
        except (psutil.NoSuchProcess,psutil.AccessDenied):denied.append(p.pid)
    return {'matches':hits,'access_denied_pids':denied}
def consumers():
    start=time.monotonic();repo=Path('D:/workspace/ck3_eternal_recurrence');ep=repo/'promo/ck3_native_war_ai/episode-04-march-logistics'
    roots=[ep/'review02',ep/'picture-production-a01/project',ep/'production/review01-machine-a02']
    roots += sorted(p for p in OUT.parent.iterdir() if p.is_dir() and p.name.startswith('review02-'))
    target_strings=[str(p).lower().replace('\\','/') for p in TARGETS]
    target_roots=sorted({p.relative_to(ROOT).parts[0].lower() for p in TARGETS})
    pending=[p for p in roots if p.is_dir()];entries=0;files=[];matches=[];skipped=[];total=0
    while pending:
        if entries>=20000 or time.monotonic()-start>30:raise RuntimeError('Consumer metadata/time bound reached')
        d=pending.pop()
        for p in d.iterdir():
            entries+=1;s=p.lstat()
            if s.st_file_attributes&0x400:skipped.append({'path':str(p),'reason':'reparse'});continue
            if p.is_dir():
                if p.name not in ('.git','.venv','node_modules','__pycache__'):pending.append(p)
                continue
            if p.suffix.lower() not in ('.json','.toml','.yaml','.yml','.py','.md','.txt'):continue
            if s.st_size>2097152:skipped.append({'path':str(p),'reason':'over2MiB'});continue
            if total+s.st_size>67108864:raise RuntimeError('Consumer body64MiB read bound reached')
            raw=p.read_bytes();total+=len(raw);text=raw.decode('utf-8-sig',errors='replace').lower().replace('\\\\','\\').replace('\\','/')
            hits=[n for n in target_strings+target_roots+[DIGEST] if n in text]
            files.append({'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            if hits:matches.append({'path':str(p),'matches':hits})
    files.sort(key=lambda r:r['path'].lower())
    stamp=hashlib.sha256(json.dumps(files,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return {'schema':'xar.r185-e01-current-consumer-query.v1','machine_id':M,'at_utc':now(),'roots':[str(p) for p in roots],'needles':target_strings+target_roots+[DIGEST],'metadata_entries':entries,'source_file_count':len(files),'read_bytes':total,'ordered_path_bytes_sha256_manifest_digest':stamp,'matches':matches,'skipped':skipped,'complete_scoped_query':True,'seconds':time.monotonic()-start,'boundary':'Known current E04Review02/Review01 config, code, manifests and preparation roots only. No liveR185 scene or TaskBus read; Root separately owns frozen R185 inputs and requires plan review. Old E01 run-manifest paths are historical, preserved separately. No mutation or directory-wide source copy.'}
def main():
    base.machine_guard();cap=json.loads(CAP.read_text(encoding='utf-8'));pro=json.loads(PRO.read_text(encoding='utf-8'))
    assert cap['machine_id']==pro['machine_id']==M and sha(PRO)==cap['minimum_necessary_protections']['sha256']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(cap['quota_review_at_utc'])
    refs=active_refs()
    if refs['matches']:raise RuntimeError('Old E01 root referenced by active process')
    check=consumers();cp=write(OUT/'E01-CURRENT-CONSUMERS.actual-a01.json',check)
    print(json.dumps({'consumer_files':check['source_file_count'],'consumer_bytes':check['read_bytes'],'matches':len(check['matches']),'skipped':len(check['skipped'])}),flush=True)
    if check['matches'] or check['skipped']:raise RuntimeError('Current-consumer query not clear; inspect exact matches')
    handles=[]
    try:
        kp=base.checked(KEEP,[ROOT]);kh=lib.open_handle(kp,0x80000000|0x80,1);handles.append(kh)
        keeper={'path':str(kp),'sha256':base.hash_handle(kh),'info':lib.get_info(kh,kp)}
        assert keeper['sha256']==DIGEST and keeper['info']['b']==804139793
        build=KEEP.parents[6]/'build-receipt.json'
        if not build.is_file():build=ROOT/'episode01-r7f-index-formal-002/build-receipt.json'
        bj=json.loads(build.read_text(encoding='utf-8'));assert bj['source_video_sha256']==DIGEST
        seen=set();rows=[]
        for target in TARGETS:
            p=base.checked(target,[ROOT]);h=lib.open_handle(p,0x80000000|0x80,0);handles.append(h)
            info=lib.get_info(h,p);digest=base.hash_handle(h)
            assert digest==DIGEST and info['b']==804139793 and info['links']==1
            assert info['id']!=keeper['info']['id'] and tuple(info['id']) not in seen
            seen.add(tuple(info['id']));rows.append({'path':str(p),'sha256':digest,'info':info,'retained_replica':str(kp),'historical_path_after_execution':'deleted_unavailable; no same-name replacement; exact bytes at retained_replica'})
            print(json.dumps({'qualified':len(rows),'logical':info['b'],'allocation':info['allocation']}),flush=True)
        assert lib.get_info(kh,kp)==keeper['info']
        stamp=datetime.now(timezone.utc)
        plan={'schema':'xar.r185-e01-seven-exact-duplicate-plan.v1','machine_id':M,'at_utc':stamp.isoformat(),'policy_version':'1.0.0','state':'PLAN_ONLY_ROOT_REVIEW_REQUIRED_BEFORE_EXECUTION','capacity_sha256':sha(CAP),'R185_protection_sha256':sha(PRO),'count':len(rows),'logical_bytes':sum(r['info']['b'] for r in rows),'single_link_allocated_bytes':sum(r['info']['allocation'] for r in rows),'volume':'D:/','unique_target_file_ids':len(seen),'allocation_credit_before_actual_deletion':0,'retained_replica':keeper,'retained_replica_owner':'Root','retained_replica_purpose':'Single immutable E01 canonical raw supports completed formal002 provenance and exact byte recovery for these seven retired historical paths. Preserve unchanged until explicit review.','retained_replica_protected_until_utc':(stamp+timedelta(days=7)).isoformat(),'retained_replica_auto_renew':False,'category':'raw_evidence','eligibility':'Verified independently allocated exact SHA duplicate early-reclamation exception; no claim natural30day expiry. Old output not an active producer; exact current E04review consumption query clear. Keeper physically read and write/delete-protected, targets exclusive readable; no delete was performed during planning.','consumer_query':cp,'active_process_query':refs,'formal002_build_receipt':{'path':str(build),'sha256':sha(build),'source_video_sha256':bj['source_video_sha256'],'created_at_utc':bj['created_at_utc'],'historical_machine_id_in_old_receipt':'unknown; current file identity reverified on this machine'},'rows':rows,'protected_scopes_untouched':['R185 live scene','native12004-r185-a28','R184 normal/raw/source','game/dependencies','TaskBus','main repo mutation'],'new_game_SDK_screen_tasks':0,'automatic_gc_implemented':False}
        pp=write(OUT/'E01-SEVEN.plan.actual-a01.json',plan)
        print(json.dumps({'plan':pp,'targets':len(rows),'D_unique_allocated_candidate_bytes':plan['single_link_allocated_bytes'],'keeper':keeper,'keeper_protected_until_utc':plan['retained_replica_protected_until_utc'],'delete_performed':False},ensure_ascii=False))
    finally:
        for h in reversed(handles):k.CloseHandle(h)
if __name__=='__main__':main()
