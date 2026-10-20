"""Verify exact deleted originals, preserve recipes and summarize measured volumes."""
from capacity_common import *
refs=[]; rows=[]
for batch in ['A40','A39','A38']:
    ref=pin(B/(batch+'-CACHE-EXECUTION-RESULT.actual-a01.json')); result=exact(ref)
    assert result['machine_id']==M and result['status']=='COMPLETE_EXACT_BATCH'
    assert result['skipped']==[] and result['failure'] is None
    assert result['all_protected_linked_artifacts_metadata_unchanged'] is True
    root=Path(result['root']).resolve(strict=True)
    for x in result['results']:
        p=root/x['relative_path']
        assert p.resolve().is_relative_to(root)
        try: p.stat(); raise RuntimeError('Deleted original reappeared: '+str(p))
        except FileNotFoundError: pass
    refs.append(ref); rows.append(result)
ledger,identity,before=snapshot(); active=balances(ledger); v=volumes(); checks=budget(v,active)
shared=shared_measure()
assert active['known_future']=={'C:/':128*Mi,'D:/':0}
assert active['legacy']=={'C:/':42132678,'D:/':0}
assert sum(x['deleted_count'] for x in rows)==2276
assert sum(x['deleted_single_link_allocated_bytes'] for x in rows)==1109104536
wait=put(B/'A02-1030Z-VOLUME-MONITOR-ORIGINAL-WAIT.actual-a01.json',{
    'machine_id':M,'observed_at_utc':now(),'original_exec_session_id':46024,
    'actual_original_wait_returncode':0,'original_tool_observation':'write_stdin original session46024 returned exit_code0; final monitor_stopped at10:30:17.935844Z, deadline reached, no stopflag',
    'owner':pin(B/'A02-FINITE-VOLUME-MONITOR-OWNED.actual-a01.json'),'journal':pin(B/'A02-FINITE-VOLUME-MONITOR.actual.jsonl'),
    'old_native_scene_game_quota_not_renewed':True})
summary=put(B/'THREE-EXACT-CACHE-BATCHES-RETIREMENT.actual-a01.json',{
    'schema':'xar.e04.three-exact-rebuildable-cache-batches-actual-retirement.v1',
    'machine_id':M,'observed_at_utc':now(),'status':'ALL_2276_EXACT_FILES_DELETED_ORIGINALS_UNAVAILABLE',
    'approval':pin(B/'ROOT-THREE-EXACT-CACHE-BATCHES-1100Z-APPROVAL.actual-a01.json'),
    'proposal':pin(B/'REBUILDABLE-OBJECT-STATIC-LIB-PROPOSAL.actual-a01.json'),'batch_results':refs,
    'batch_summaries':[{'batch':x['batch'],'deleted_count':x['deleted_count'],'deleted_logical_bytes':x['deleted_logical_bytes'],
      'deleted_single_link_allocated_bytes':x['deleted_single_link_allocated_bytes'],'observed_C_free_delta_bytes':x['observed_C_free_delta_bytes'],
      'protected_linked_artifact_count':x['protected_artifact_count'],'originals_now_unavailable':True} for x in rows],
    'deleted_count':sum(x['deleted_count'] for x in rows),'deleted_logical_bytes':sum(x['deleted_logical_bytes'] for x in rows),
    'deleted_single_link_allocated_bytes':sum(x['deleted_single_link_allocated_bytes'] for x in rows),
    'first_batch_C_free_before_bytes':rows[0]['fresh_volumes_before']['C:/']['free_bytes'],
    'last_batch_C_free_after_bytes':rows[-1]['fresh_volumes_after']['C:/']['free_bytes'],
    'observed_C_free_delta_first_to_last_bytes':rows[-1]['fresh_volumes_after']['C:/']['free_bytes']-rows[0]['fresh_volumes_before']['C:/']['free_bytes'],
    'whole_volume_free_change_exclusively_attributed_to_retirement':False,'physical_or_unused_credit_bytes':0,
    'fresh_volumes':v,'active_balances':active,'budget_after':checks,'collective_shared':shared,
    'original_payload_SHA_unknown_preserved':True,'new_cache_payload_hash_bytes_read':0,
    'linked_DLL_EXE_PDB_Q_flags_graph_source_ACL_restore_and_normal_S0_preserved':True,
    'future_relink_requires_rebuild_from_each_original_exact_Git_tree_flags_graph':True,
    'regenerated_files_must_not_impersonate_deleted_originals':True,'directories_deleted':0,'permissions_modified':False,
    'R0219_closed_settlement':pin(B/'R0219-NORMAL-CLOSED-BUSINESS-REFUSED-SETTLEMENT.actual-a01.json'),
    'old_volume_monitor_original_wait':wait,'metadata_phase_deadline_utc':'2026-10-20T11:00:00Z',
    'new_game_scene_native_admission':False,'purpose_review_at_utc':'2026-10-22T10:22:22Z',
    'scheme':pin(__file__),'exact_retirement_executor':pin(B/'retire_exact_build_intermediates.py')})
c=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
c['exact_cache_reclamation']=summary
c['physical_or_unused_credit_bytes']=0
c['old_1030_volume_monitor_actual_wait']=wait
commit=commit_ledger(ledger,identity)
tx=put(B/'THREE-EXACT-CACHE-BATCHES-TRANSACTION.actual-a01.json',{'machine_id':M,'observed_at_utc':now(),'summary':summary,'ledger_before':before,'commit':commit,'future_and_legacy_unchanged':True,'physical_or_unused_credit_bytes':0})
print(json.dumps({'summary':summary,'transaction':tx,'fresh_volumes':v,'budget':checks,'shared':shared},indent=2))
