"""Three Root-approved exact, source-rebuildable batches; no recursive deletion."""
from capacity_common import *
import argparse, ctypes as ct, importlib.util, psutil
from ctypes import wintypes as wt

RECLAIM_DEADLINE = datetime.fromisoformat('2026-10-20T11:00:00+00:00')
spec=importlib.util.spec_from_file_location('retire_win32', 'C:/ck3-e04-resume-20261015-a01/capacity-lane/win32_exact_retire_lib.py')
win=importlib.util.module_from_spec(spec); spec.loader.exec_module(win)

def clock_guard():
    assert datetime.now(timezone.utc)<RECLAIM_DEADLINE, 'Explicit reclamation deadline reached'

def norm(p): return os.path.normcase(os.path.abspath(str(p)))

def stat_key(p):
    s=p.stat(follow_symlinks=False)
    assert not s.st_file_attributes & 0x400, 'Reparse path rejected'
    return {'st_dev':s.st_dev,'st_ino':s.st_ino,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'st_nlink':s.st_nlink}

def writer_census(roots):
    blocked=[]; errors=[]
    names={'cl.exe','link.exe','lib.exe','ninja.exe','cmake.exe','msbuild.exe','ck3.exe','ffmpeg.exe','ffprobe.exe'}
    for p in psutil.process_iter(['pid','name','create_time']):
        try:
            name=(p.info['name'] or '').lower()
            if not name: errors.append({'pid':p.pid,'error':'No process name available'})
            if name in names: blocked.append(p.info)
            if name in {'python.exe','pythonw.exe'} and p.pid!=os.getpid():
                argv=p.cmdline()
                if any(any(norm(root) in norm(arg) for root in roots) for arg in argv):
                    blocked.append({**p.info,'argv':argv,'reason':'Python references an exact retired build root'})
        except psutil.NoSuchProcess: pass
        except psutil.AccessDenied as e: errors.append({'pid':p.pid,'error':repr(e)})
    return {'observed_at_utc':now(),'blocking_named_or_root_bound_processes':blocked,'read_errors':errors,
            'scope':'Names of build tools, CK3 and media writers; ordinary Python command lines referencing approved build roots. Typed original close proves owned session closure separately.',
            'global_process_absence_claimed':False}

def restart_manager(paths):
    r=ct.WinDLL('rstrtmgr',use_last_error=True); session=wt.DWORD(); key=ct.create_unicode_buffer(33)
    r.RmStartSession.argtypes=[ct.POINTER(wt.DWORD),wt.DWORD,wt.LPWSTR]
    r.RmRegisterResources.argtypes=[wt.DWORD,wt.UINT,ct.POINTER(wt.LPCWSTR),wt.UINT,ct.c_void_p,wt.UINT,ct.c_void_p]
    r.RmGetList.argtypes=[wt.DWORD,ct.POINTER(wt.UINT),ct.POINTER(wt.UINT),ct.c_void_p,ct.POINTER(wt.DWORD)]
    r.RmEndSession.argtypes=[wt.DWORD]
    assert r.RmStartSession(ct.byref(session),0,key)==0
    try:
        arr=(wt.LPCWSTR*len(paths))(*[str(p) for p in paths])
        reg=r.RmRegisterResources(session,len(paths),arr,0,None,0,None); assert reg==0
        need=wt.UINT(); count=wt.UINT(); reason=wt.DWORD()
        rc=r.RmGetList(session,ct.byref(need),ct.byref(count),None,ct.byref(reason))
        return {'registration_returncode':reg,'query_returncode':rc,'consumer_count_needed':need.value,
                'consumer_count_returned':count.value,'shutdown_or_restart_called':False}
    finally: r.RmEndSession(session)

def directory_lease(p):
    assert p.is_dir() and not p.lstat().st_file_attributes & 0x400
    h=win.k.CreateFileW(str(p),0x80,3,None,3,0x02000000|0x00200000,None)
    if h==win.BAD: raise ct.WinError(ct.get_last_error())
    try:
        info=win.Info()
        assert win.k.GetFileInformationByHandle(h,ct.byref(info))
        assert info.attr&0x10 and not info.attr&0x400
        buf=ct.create_unicode_buffer(32768)
        n=win.k.GetFinalPathNameByHandleW(h,buf,len(buf),0)
        assert n and n<len(buf)
        final=buf.value[4:] if buf.value.startswith('\\\\?\\') else buf.value
        assert norm(final)==norm(p), 'Directory handle resolved outside exact named path'
        return h, {'path':str(p),'file_id':(info.index_high<<32)|info.index_low,'volume_serial32':info.volume,
                   'lease':'READ_ATTRIBUTES; share read/write, deny delete; OPEN_REPARSE_POINT|BACKUP_SEMANTICS'}
    except BaseException:
        win.k.CloseHandle(h); raise

def saved_artifacts(root):
    result=[]
    for p in root.iterdir():
        if p.is_file() and (p.suffix.lower() in {'.dll','.exe','.pdb'} or (p.name.startswith('ROOT-') and p.suffix=='.json')):
            result.append({'path':str(p),'identity':stat_key(p)})
    assert any(Path(x['path']).suffix.lower()=='.dll' for x in result)
    return sorted(result,key=lambda x:x['path'])

def recipe_check(group):
    def visit(value):
        if isinstance(value,dict):
            if {'path','bytes','sha256'}<=value.keys() and value['sha256'] is not None:
                ref={k:value[k] for k in ['path','bytes','sha256']}; assert pin(ref['path'])==ref
            else:
                for x in value.values(): visit(x)
        elif isinstance(value,list):
            for x in value: visit(x)
    visit(group['source_rebuild_recipe'])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',required=True,choices=['a40','a39','a38'])
    parser.add_argument('--execute',action='store_true')
    a=parser.parse_args(); clock_guard(); started=time.monotonic()
    proposal_ref=pin(B/'REBUILDABLE-OBJECT-STATIC-LIB-PROPOSAL.actual-a01.json')
    assert proposal_ref['sha256']=='a06f7111501f252a850f94f10829b07938abde78f6a9194c9d703c43f89d0eb4'
    proposal=exact(proposal_ref); assert proposal['machine_id']==M
    approval_ref=pin(B/'ROOT-THREE-EXACT-CACHE-BATCHES-1100Z-APPROVAL.actual-a01.json')
    approval=exact(approval_ref); assert approval['proposal']==proposal_ref
    closed_ref=pin(B/'R0219-NORMAL-CLOSED-BUSINESS-REFUSED-SETTLEMENT.actual-a01.json')
    closed=exact(closed_ref); assert closed['normal_close_qualified'] is True and closed['machine_id']==M
    group=next(x for x in proposal['groups'] if x['id']==a.batch)
    source=exact(group['objects']['manifest'])
    if 'group_id' in group['objects']:
        source=next(x for x in source['candidate_groups'] if x['asset_id']==group['objects']['group_id'])
    assert source['machine_id']==M
    root=Path(group['root']).resolve(strict=True)
    assert norm(root)==norm(source['root']) and root.drive.upper()=='C:'
    rows=[*source['candidates'],group['static_library_exact_metadata']]
    assert len(rows)==group['exact_file_count_in_batch']<=1000
    assert sum(x['bytes'] for x in rows)==group['logical_candidate_bytes']
    assert sum(x['allocated_bytes'] for x in rows)==group['allocated_candidate_upper_bound_bytes']
    assert len({norm(root/x['relative_path']) for x in rows})==len(rows)
    assert git('rev-parse',source['source_head']+':ck3_autonomous_player/native_bridge')==source['native_tree']
    recipe_check(group)
    index_ref=pin(R/'docs/maintenance/user-permanent-assets.json'); index=exact(index_ref)
    assert index_ref==proposal['permanent_asset_index']
    permanent=[Path(x['absolute_path']) for x in index['assets'] if x['machine_id']==M]
    # Current runtime and coherent native-Q contain only linked inputs, not cache payloads.
    ledger,_,ledger_ref=snapshot(); claim=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
    assert claim['scene_remaining_future_bytes']==claim['native_a41_remaining_future_bytes']==0
    assert claim['phase_kind']=='explicit-post-close-metadata-and-three-exact-reclamation-batches-only'
    runtime_ref=pin(ROOT/'common-runtime-a41-a03/runtime.local.json')
    runtime=exact(runtime_ref); active_text=json.dumps(runtime).replace('\\\\','/').lower()
    paths=[]; early_skips=[]
    for i,row in enumerate(rows):
        relative=Path(row['relative_path']); p=root/relative
        assert not relative.is_absolute() and '..' not in relative.parts
        assert p.resolve(strict=True).is_relative_to(root)
        assert (p.suffix.lower()=='.obj' and relative.parts[0]=='CMakeFiles') or relative==Path('xar_ck3_12002_runtime.lib')
        assert not any(norm(p)==norm(x) or p.is_relative_to(x) for x in permanent)
        assert str(p).replace('\\','/').lower() not in active_text, 'Candidate is a declared runtime input'
        paths.append(p)
    census=writer_census([Path(x['root']) for x in proposal['groups']])
    assert not census['blocking_named_or_root_bound_processes'] and not census['read_errors'], census
    rm=restart_manager(paths)
    assert rm['query_returncode']==0 and rm['consumer_count_needed']==0, rm
    protected_before=saved_artifacts(root)
    before=volumes(); active=balances(ledger); checks=budget(before,active)
    assert min(checks['C_floor_margin_bytes'],checks['C_quota_margin_bytes'],checks['D_floor_margin_bytes'])>=0
    shared=shared_measure(claim['shared_accounting_excludes'])
    assert shared['logical_bytes']+3*Mi<=128*Mi
    handles=[]; dirs=[]; locks=[]; results=[]; failure=None
    mode='EXECUTION' if a.execute else 'PREFLIGHT'
    try:
        ancestors=set()
        for p in paths:
            for parent in p.parents:
                ancestors.add(parent)
        for directory in sorted(ancestors,key=lambda p:(len(p.parts),str(p))):
            h,info=directory_lease(directory); dirs.append((h,info))
        for i,(p,row) in enumerate(zip(paths,rows)):
            clock_guard(); h=None
            try:
                current=stat_key(p)
                assert current=={k:row[k] for k in ['st_dev','st_ino','bytes','mtime_ns','st_nlink']}, 'Exact reviewed filesystem metadata changed'
                assert row['st_nlink']==1 and row['sha256'] is None
                h=win.open_handle(p,0x10000|0x80,0)
                info=win.get_info(h,p)
                assert info['id'][1]==row['st_ino'] and info['b']==row['bytes']
                assert info['ft']==row['mtime_ns']//100+116444736000000000
                assert info['links']==1 and info['allocation']==row['allocated_bytes']
                handles.append(h); locks.append((i,p,row,h,info)); h=None
            except Exception as error:
                early_skips.append({'manifest_index':i,'relative_path':row['relative_path'],'status':'skipped_no_delete','error':repr(error)})
            finally:
                if h is not None: win.k.CloseHandle(h)
        assert time.monotonic()-started<120, 'Preflight inventory bound exceeded'
        intent=put(B/(a.batch.upper()+'-CACHE-'+mode+'-INTENT.actual-a01.json'),{
            'schema':'xar.e04.exact-rebuildable-intermediates-retirement-intent.v1','machine_id':M,'observed_at_utc':now(),
            'batch':a.batch,'root':str(root),'proposal':proposal_ref,'approval':approval_ref,'typed_scene_closed':closed_ref,
            'exact_candidate_manifest':group['objects']['manifest'],'candidate_count':len(rows),'exclusive_handles_acquired':len(locks),
            'skipped':early_skips,'candidate_payload_SHA_unknown':True,'payload_bytes_read':0,'writer_census':census,'RestartManager':rm,
            'source_head':source['source_head'],'native_tree':source['native_tree'],'recipe_revalidated':True,
            'runtime':runtime_ref,'permanent_index':index_ref,'ledger_observed':ledger_ref,
            'directory_rename_delete_denial_leases':len(dirs),'leaf_lease':'DELETE|READ_ATTRIBUTES share=0; resolved handle path, file ID, size, LastWrite, links and allocation equal exact manifest',
            'protected_linked_artifacts_before':protected_before,'fresh_volumes_before':before,'budget_before':checks,
            'execute':a.execute,'reclamation_deadline_utc':'2026-10-20T11:00:00Z','physical_or_unused_credit_bytes':0,
            'scheme':pin(__file__),'Win32_library':pin(spec.origin)})
        for i,p,row,h,info in locks:
            clock_guard()
            r={'manifest_index':i,'relative_path':row['relative_path'],'bytes':row['bytes'],'allocated_bytes':row['allocated_bytes'],'original_payload_sha256':None}
            try:
                assert win.get_info(h,p)==info, 'Leased identity changed before disposition'
                if a.execute:
                    flag=win.Disposition(True)
                    if not win.k.SetFileInformationByHandle(h,4,ct.byref(flag),ct.sizeof(flag)):
                        raise ct.WinError(ct.get_last_error())
                    assert win.k.CloseHandle(h); handles.remove(h)
                    try: p.stat(); raise RuntimeError('Original still present after disposition and close')
                    except FileNotFoundError: pass
                    r['status']='deleted_original_unavailable'
                else:
                    r['status']='exclusive_identity_preflight_pass_original_retained'
            except Exception as error:
                r.update(status='not_confirmed_deleted_preserve_diagnostic',error=repr(error))
            results.append(r)
    except BaseException as error:
        failure=repr(error)
        raise
    finally:
        for h in handles: win.k.CloseHandle(h)
        for h,_ in reversed(dirs): win.k.CloseHandle(h)
        after=volumes()
        # Every linked image/PDB/Q is outside the candidate set and must remain exact metadata-identical.
        protected_after=saved_artifacts(root)
        retained_unchanged=protected_before==protected_after
        recipe_check(group)
        deleted=[x for x in results if x['status']=='deleted_original_unavailable']
        receipt=put(B/(a.batch.upper()+'-CACHE-'+mode+'-RESULT.actual-a01.json'),{
            'schema':'xar.e04.exact-rebuildable-intermediates-retirement-result.v1','machine_id':M,'observed_at_utc':now(),
            'batch':a.batch,'root':str(root),'intent':locals().get('intent'),'proposal':proposal_ref,'approval':approval_ref,
            'status':'COMPLETE_EXACT_BATCH' if a.execute and len(deleted)==len(rows) and retained_unchanged else 'PREFLIGHT_OR_PARTIAL_WITH_ORIGINAL_DIAGNOSTICS',
            'results':results,'skipped':early_skips,'failure':failure,'deleted_count':len(deleted),
            'deleted_logical_bytes':sum(x['bytes'] for x in deleted),'deleted_single_link_allocated_bytes':sum(x['allocated_bytes'] for x in deleted),
            'fresh_volumes_before':before,'fresh_volumes_after':after,'observed_C_free_delta_bytes':after['C:/']['free_bytes']-before['C:/']['free_bytes'],
            'whole_volume_free_change_exclusively_attributed_to_this_deletion':False,'physical_or_unused_credit_bytes':0,
            'all_protected_linked_artifacts_metadata_unchanged':retained_unchanged,'protected_artifact_count':len(protected_after),
            'source_flags_graph_and_original_proofs_retained':True,'all_directory_leases_and_leaf_handles_closed':True,
            'original_payload_SHA_unknown_preserved':True,'payload_body_bytes_read':0,'no_directories_or_permissions_modified':True,
            'future_relink_requires_exact_source_reconstruction':True,'purpose_review_at_utc':'2026-10-22T10:22:22Z',
            'elapsed_seconds':round(time.monotonic()-started,3),'new_build_game_SDK_screen_actions':0})
        print(json.dumps({'receipt':receipt,'deleted_count':len(deleted),'skipped_count':len(early_skips),'retained_unchanged':retained_unchanged,'C_free_delta_bytes':after['C:/']['free_bytes']-before['C:/']['free_bytes'],'failure':failure}),flush=True)
        assert retained_unchanged, 'Protected linked artifact metadata changed; stop next batch'

if __name__=='__main__': main()
