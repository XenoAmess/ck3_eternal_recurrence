"""Create compact durable exact-deletion inventory and a small prepared copyplan."""
from capacity_common import *
proposal_ref=pin(B/'REBUILDABLE-OBJECT-STATIC-LIB-PROPOSAL.actual-a01.json'); proposal=exact(proposal_ref)
groups=[]
for group in proposal['groups']:
    source=exact(group['objects']['manifest'])
    if 'group_id' in group['objects']:
        source=next(x for x in source['candidate_groups'] if x['asset_id']==group['objects']['group_id'])
    candidates=[*source['candidates'],group['static_library_exact_metadata']]
    result_ref=pin(B/(group['id'].upper()+'-CACHE-EXECUTION-RESULT.actual-a01.json')); result=exact(result_ref)
    assert result['status']=='COMPLETE_EXACT_BATCH'
    assert [x['relative_path'] for x in candidates]==[x['relative_path'] for x in result['results']]
    groups.append({'id':group['id'],'root':group['root'],'original_source_head':source['source_head'],'native_tree':source['native_tree'],
      'original_inventory':group['objects']['manifest'],'actual_retirement':result_ref,
      'files':[[x['relative_path'],x['bytes'],x['st_dev'],x['st_ino'],x['mtime_ns'],x['allocated_bytes']] for x in candidates]})
compact={'schema':'xar.e04.exact-deleted-rebuildable-cache-compact-inventory.v1','machine_id':M,'observed_at_utc':now(),
  'columns':['relative_path','bytes','st_dev','st_ino','mtime_ns','single_link_allocated_bytes'],
  'all_rows_status':'deleted_original_unavailable_confirmed','all_rows_original_sha256':None,'unknown_SHA_not_replaced_by_hash_of_rebuilt_content':True,
  'all_rows_st_nlink':1,'groups':groups,'proposal':proposal_ref,
  'retirement':pin(B/'THREE-EXACT-CACHE-BATCHES-RETIREMENT.actual-a01.json'),'future_relink_requires_original_exact_tree_flags_graph_rebuild':True,
  'retained_originals':'Linked DLL/EXE/PDB/Q, producer flags, dependency graphs, Git source, unique ACL restore inputs and normal Mar31 S0 are excluded and retained.',
  'purpose_review_at_utc':'2026-10-22T10:22:22Z'}
raw=json.dumps(compact,ensure_ascii=False,separators=(',',':')).encode('utf-8')
assert len(raw)<1024*1024
compact_path=B/'THREE-CACHE-BATCHES-DELETED-ORIGINALS.compact-a01.json'
with compact_path.open('xb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
names=[
 'THREE-CACHE-BATCHES-DELETED-ORIGINALS.compact-a01.json',
 'THREE-EXACT-CACHE-BATCHES-RETIREMENT.actual-a01.json',
 'THREE-EXACT-CACHE-BATCHES-TRANSACTION.actual-a01.json',
 'REBUILDABLE-OBJECT-STATIC-LIB-PROPOSAL.actual-a01.json',
 'ROOT-THREE-EXACT-CACHE-BATCHES-1100Z-APPROVAL.actual-a01.json',
 'METADATA-RECLAMATION-1100Z-TRANSACTION.actual-a01.json',
 'R0219-NORMAL-CLOSED-BUSINESS-REFUSED-SETTLEMENT.actual-a01.json',
 'R0219-CLOSED-SETTLEMENT-TRANSACTION.actual-a01.json',
 'R0219-CLEANUP-COMPONENT-MONITOR-ORIGINAL-WAIT.actual-a02.json',
 'A02-1030Z-VOLUME-MONITOR-ORIGINAL-WAIT.actual-a01.json',
 'retire_exact_build_intermediates.py','capacity_common.py','settle_r0219_closed.py',
 'seal_reclamation_summary.py','admit_metadata_reclaim_1100.py','prepare_capacity_closeout_copyplan.py']
selected=[pin(B/name) for name in names]
copyplan=put(B/'CAPACITY-R0219-RECLAMATION-SMALL-COPYPLAN.prepared-a01.json',{
 'schema':'xar.e04.capacity-small-exact-copyplan-prepared.v1','machine_id':M,'observed_at_utc':now(),
 'state':'PREPARED_NOT_COPIED_OR_STAGED','files':selected,'file_count':len(selected),'selected_bytes':sum(x['bytes'] for x in selected),
 'compact_inventory_exact_rows':2276,'large_formatted_local_candidates_and_perfile_results_retained_at_original_paths':True,
 'typed_scene_originals_not_duplicated_here':'R0219 evidence package supplied by public agent; settlement includes exact original pins.',
 'shared128_still_active_until_Root_explicit_close':True,'no_new_native_game_media':True,
 'purpose_review_at_utc':'2026-10-22T10:22:22Z'})
print(json.dumps({'copyplan':copyplan,'selected_count':len(selected),'selected_bytes':sum(x['bytes'] for x in selected),'compact_inventory':pin(compact_path)}))
