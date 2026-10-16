"""Execute only the seven exact Root-reviewed E01 paths from the frozen plan."""
from pathlib import Path
import argparse,ctypes as c,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
OUT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('plan_module',OUT/'plan_e01_exact_duplicates.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
base=p.base;lib=p.lib;k=p.k

def total_output():
    return sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())

def main(expected):
    pp=OUT/'E01-SEVEN.plan.actual-a01.json'
    if p.sha(pp)!=expected:raise RuntimeError('Root-reviewed plan SHA differs')
    plan=json.loads(pp.read_text(encoding='utf-8'))
    assert plan['machine_id']==p.M and plan['count']==7
    assert [r['path'] for r in plan['rows']]==[str(x) for x in p.TARGETS]
    base.machine_guard()
    assert p.sha(p.CAP)==plan['capacity_sha256'] and p.sha(p.PRO)==plan['R185_protection_sha256']
    if total_output()+18000>65536:raise RuntimeError('Reserve18k for actual receipts before mutation')
    if (OUT/'E01-SEVEN.intent.actual-a01.json').exists():raise RuntimeError('Intent already exists; do not replay')
    refs=p.active_refs()
    if refs['matches'] or refs['access_denied_pids']:raise RuntimeError('Producer query incomplete or old roots active')
    check=p.consumers()
    if check['matches'] or check['skipped']:raise RuntimeError('Fresh current-consumer query not clear')
    cp=p.write(OUT/'E01-CURRENT-CONSUMERS.actual-a02.json',check)
    original=json.loads(Path(plan['consumer_query']['path']).read_text(encoding='utf-8'))
    assert p.sha(Path(plan['consumer_query']['path']))==plan['consumer_query']['sha256']
    if check['ordered_path_bytes_sha256_manifest_digest']!=original['ordered_path_bytes_sha256_manifest_digest']:
        raise RuntimeError('Current consumer manifest changed after Root-reviewed plan; no deletion')
    handles=[];pending=[];rows=[]
    try:
        keep=plan['retained_replica'];kp=base.checked(keep['path'],[p.ROOT])
        kh=lib.open_handle(kp,0x80000000|0x80,1);handles.append(kh)
        if lib.get_info(kh,kp)!=keep['info'] or base.hash_handle(kh)!=keep['sha256']:raise RuntimeError('Keeper changed')
        for ref in plan['rows']:
            target=base.checked(ref['path'],[p.ROOT]);h=lib.open_handle(target,0x80000000|0x10000|0x80,0);handles.append(h)
            if lib.get_info(h,target)!=ref['info'] or base.hash_handle(h)!=ref['sha256']:raise RuntimeError('Target changed under exclusive handle')
            pending.append((h,target,ref))
            print(json.dumps({'reverified':len(pending),'of':7}),flush=True)
        before={v:shutil.disk_usage(v).free for v in ('C:/','D:/')}
        intent={'schema':'xar.r185-e01-seven-delete-intent.v1','machine_id':p.M,'at_utc':p.now(),'policy_version':'1.0.0','plan_sha256':expected,'root_review':'Root reviewed this exact plan hash/count/scoped D credit in collaboration before this invocation','fresh_consumer_query':cp,'current_consumer_manifest_unchanged':True,'producer_query':refs,'targets_and_keeper_all_sha_identity_reverified':True,'method':'Keeper shareREAD denies write/delete; seven target handles exclusive READ+DELETE, all frozen identities and SHA matched before any disposition. Exact7 only, no directory deletion.','free_before':before,'remaining_package_output_reserve_bytes':65536-total_output()}
        p.write(OUT/'E01-SEVEN.intent.actual-a01.json',intent)
        with (OUT/'E01-SEVEN.files.actual-a01.jsonl').open('x',encoding='utf-8') as ledger:
            for h,target,ref in pending:
                row={'machine_id':p.M,'at_utc':p.now(),'path':str(target),'sha256':ref['sha256'],'logical_bytes':ref['info']['b'],'allocation_bytes':ref['info']['allocation'],'file_id':ref['info']['id'],'retained_replica':keep['path'],'status':'not_deleted'}
                try:
                    if lib.get_info(h,target)!=ref['info'] or lib.get_info(kh,kp)!=keep['info']:raise RuntimeError('Frozen identity changed')
                    flag=lib.Disposition(True)
                    if not k.SetFileInformationByHandle(h,4,c.byref(flag),c.sizeof(flag)):raise c.WinError(c.get_last_error())
                    k.CloseHandle(h);handles.remove(h)
                    if target.exists():raise RuntimeError('Absence not confirmed')
                    row.update(status='deleted_unavailable',exists_after=False)
                except Exception as ex:row['error']=str(ex)
                rows.append(row);ledger.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n');ledger.flush()
        deleted=[r for r in rows if r['status']=='deleted_unavailable']
        retained_ok=lib.get_info(kh,kp)==keep['info'] and kp.is_file()
        result={'schema':'xar.r185-e01-seven-duplicate-retirement.actual.v1','machine_id':p.M,'at_utc':p.now(),'policy_version':'1.0.0','plan':{'path':str(pp),'sha256':expected},'attempted':len(rows),'deleted':len(deleted),'failed':len(rows)-len(deleted),'actual_C_credit_bytes':0,'actual_D_logical_bytes':sum(r['logical_bytes'] for r in deleted),'actual_D_single_link_allocation_bytes':sum(r['allocation_bytes'] for r in deleted),'unique_deleted_path_count':len({r['path'] for r in deleted}),'unique_deleted_file_id_count':len({tuple(r['file_id']) for r in deleted}),'source_protection_excluded_overlap':0,'retained_replica':keep,'retained_replica_unchanged_under_handle':retained_ok,'retained_replica_owner':plan['retained_replica_owner'],'retained_replica_protected_until_utc':plan['retained_replica_protected_until_utc'],'retained_replica_auto_renew':False,'free_before':before,'free_after':{v:shutil.disk_usage(v).free for v in before},'whole_volume_free_delta_not_exclusively_credited':True,'current_consumer_query':cp,'files_ledger':{'path':str(OUT/'E01-SEVEN.files.actual-a01.jsonl'),'sha256':p.sha(OUT/'E01-SEVEN.files.actual-a01.jsonl')},'old_run_manifests_changed':False,'historical_path_availability_map':[{'old_path':r['path'],'availability':r['status'],'sha256':r['sha256'],'keeper_path':keep['path']} for r in rows],'no_same_name_replacement':True,'directory_deletions':0,'active_R185_a28_R184_normal_raw_game_dependencies_untouched':True,'main_repo_TaskBus_SDK_screen_actions':0,'automatic_gc_implemented':False}
        rp=p.write(OUT/'E01-SEVEN.result.actual-a01.json',result)
        assert total_output()<=65536
        print(json.dumps({'result':rp,'actual_C_credit':0,'actual_D_allocation_credit':result['actual_D_single_link_allocation_bytes'],'deleted':len(deleted),'failed':result['failed'],'keeper_unchanged':retained_ok,'free_after':result['free_after'],'package_bytes':total_output()},ensure_ascii=False))
    finally:
        for h in reversed(handles):k.CloseHandle(h)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-approved-plan-sha256',required=True)
    args=parser.parse_args();main(args.root_approved_plan_sha256)
