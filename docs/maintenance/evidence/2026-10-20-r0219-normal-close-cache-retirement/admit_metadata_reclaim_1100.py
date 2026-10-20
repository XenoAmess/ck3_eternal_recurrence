"""Explicit Root-authorized post-close metadata/reclamation phase, no scene renewal."""
from capacity_common import *
approval=put(B/'ROOT-THREE-EXACT-CACHE-BATCHES-1100Z-APPROVAL.actual-a01.json',{
 'machine_id':M,'observed_at_utc':now(),'authorized_by':'/root','source':'Direct collaboration message after independent R0219 typed normal closure',
 'proposal':pin(B/'REBUILDABLE-OBJECT-STATIC-LIB-PROPOSAL.actual-a01.json'),
 'scope':'A40 756, A39 788, A38 732 exact manifest .obj files and each root unique xar_ck3_12002_runtime.lib; exact resolved paths, reliable exclusive identity handles, per-file skip on discrepancy. No directories, permission changes, DLL/EXE/PDB/Q/source/flags/Git/ACL restore/S0 deletion.',
 'a38_old_whole_build_protection_narrowed_only_for_exact_rebuildable_candidates':True,
 'reason':'Root reviewed unified storage policy early reclamation rule; current A41 and R0219 normal closure consume retained linked images; relinking requires retained exact-source/flags/graph reconstruction.',
 'deadline_utc':'2026-10-20T11:00:00Z','shared_existing_ceiling_bytes':128*Mi,'new_global_future_bytes':0,
 'old_1030_scene_native_game_authority_not_renewed':True,'new_game_build_or_media_execution_admitted':False,
 'candidate_free_credit_bytes':0,'payload_SHA_unknown_preserved':True})
ledger, identity, before=snapshot(); c=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
assert c['scene_remaining_future_bytes']==0 and c['native_a41_remaining_future_bytes']==0
assert c['reserved_future_bytes_by_volume']['C:/']==128*Mi
c['previous_runtime_phase_review_at_utc']=c['review_at_utc']
c['review_at_utc']='2026-10-20T11:00:00Z'
c['phase_kind']='explicit-post-close-metadata-and-three-exact-reclamation-batches-only'
c['metadata_reclamation_approval']=approval
c['game_execution_admitted']=False; c['native_build_execution_admitted']=False
c['scene_execution_admitted']=False; c['scene_prepare_execution_admitted']=False
c['automatic_renewal']=False
v=volumes(); a=balances(ledger); checks=budget(v,a)
assert checks['C_quota_margin_bytes']>=0 and checks['C_floor_margin_bytes']>=0 and checks['D_floor_margin_bytes']>=0
commit=commit_ledger(ledger,identity)
tx=put(B/'METADATA-RECLAMATION-1100Z-TRANSACTION.actual-a01.json',{'machine_id':M,'observed_at_utc':now(),'approval':approval,'ledger_before':before,'commit':commit,'fresh_volumes':v,'active_balances':a,'budget':checks,'no_extra_future_or_credit':True})
print(json.dumps({'approval':approval,'transaction':tx}))
