"""Finite split-only exception for a removed zero-DATA current-role record.

Pure normal DTO consumer. Legacy strict remains false. No role blanket waiver,
source-PC/birth claim, action, SDK, file/EXE access or current-field invention.
"""
from xar_autoplayer.bridge import army_split_transfer_assertions_12004 as transfer
from xar_autoplayer.bridge import army_split_merge_observation_12004 as observation

def need(ok,why):
    if not ok:raise ValueError(why)

def qualify_unrelated_role_removal(before,after,*,source_army_id):
    identity=observation.identify_split_sibling(before['frame'],after['frame'],source_army_id=source_army_id,
      pre_strengths=before['query'],post_strengths=after['query'])
    sibling=identity['sibling_army_id'];pre={r['army_id']:r for r in before['query']['army_strengths']}
    post={r['army_id']:r for r in after['query']['army_strengths']}
    child_commander=observation.read_bound_current_commander(after['commanders'][str(sibling)],after['frame'],
      army_id=sibling,native_carmy_id=post[sibling]['native_carmy_id'])
    need(type(child_commander) is int,'fresh sibling needs an actual positive assigned Character')
    pre_ex=before['excluded_unavailable_cohorts'];post_ex=after['excluded_unavailable_cohorts']
    need(pre_ex==post_ex,'unavailable row status/identity/reason changed')
    excluded={r['army_id'] for r in pre_ex};ids=sorted(set(pre)-{source_army_id}-excluded)
    need(set(ids)<=set(post),'unrelated Army missing')
    old_armies=[pre[i] for i in ids];new_armies=[post[i] for i in ids]
    legacy=observation.compare_split_merge_cohorts(old_armies,new_armies)
    need(legacy['frozen_exact_cohort_pass'] is False,'this exception does not replace an already passing strict guard')
    old,physical0,occ0=transfer._observe(old_armies);new,physical1,occ1=transfer._observe(new_armies)
    need(physical0==physical1,'unrelated unique physical DATA ID/current/max/state changed')
    need(occ0==occ1,'unrelated DATA aliases/occurrence/backlink changed')
    need(not(set(new)-set(old)),'unrelated ArRg was added; no role-birth exemption')
    removed=sorted(set(old)-set(new));need(len(removed)==1,'only one independently explained role removal is admitted')
    identity_removed=removed[0];row=old[identity_removed];data=row['data'];role=data.get('native_character_role_v1') or {}
    army=row['army_id'];native=pre[army]['native_carmy_id']
    need(transfer._empty_character(row) and data['native_data_record_count']==0 and data['records']==[],
      'removed unrelated row is not exact available zero-DATA cached1/1 Character')
    need(role.get('resolved_character_id')==role.get('character_raw_id_148')==child_commander
      and role.get('native_carmy_id')==role.get('arrg_army_id_140')==native
      and role.get('extension_arrg_id_f8')==identity_removed and role.get('extension_army_id_f4')==-1,
      'removed role FullID/backlink/Character is not fresh sibling assigned commander')
    for i in set(old)&set(new):
        need(old[i]['strength']==new[i]['strength'],'remaining unrelated ArRg cache/current/max changed')
        need(old[i]['data']==new[i]['data'],'remaining unrelated complete DATA/predicate/role leaf changed')
    scalar_fields=('current_supply_raw','current_supply_scale','current_supply_capacity_raw','current_supply_capacity_scale',
      'merge_supply_destination_weight_raw','merge_supply_destination_weight_scale')
    old_roster=observation._roster(before['frame']);new_roster=observation._roster(after['frame'])
    commanders={}
    for i in ids:
        a,b=pre[i],post[i]
        need(a['status']==b['status']=='available' and a['native_carmy_id']==b['native_carmy_id'],
          'unrelated Army availability or native generation changed')
        need(old_roster[i]==new_roster[i],'unrelated actual roster owner/province/control/route/state changed')
        for field in scalar_fields:
            need(type(a.get(field)) is int and a[field]==b.get(field),'unrelated stock/cap/Dweight changed or unavailable: '+field)
        old_current=observation.read_bound_current_commander(before['commanders'][str(i)],before['frame'],army_id=i,native_carmy_id=a['native_carmy_id'])
        new_current=observation.read_bound_current_commander(after['commanders'][str(i)],after['frame'],army_id=i,native_carmy_id=b['native_carmy_id'])
        need(old_current==new_current,'unrelated actual assigned commander changed')
        delta=1 if i==army else 0
        need(a['current_soldiers']-b['current_soldiers']==delta and a['maximum_soldiers']-b['maximum_soldiers']==delta,
          'unrelated total cache delta exceeds the one removed1/1 role')
        commanders[str(i)]=old_current
    return {'role_aware_physical_guard_pass':True,'frozen_exact_cohort_pass':False,
      'legacy_frozen_exact_cohort_pass':False,'legacy_strict_result':legacy,'role_transfer_observed':True,
      'qualification_policy':'one zeroDATA/cache1:1 role removal linked to fresh child current typed commander; all other unrelated values strict',
      'removed_role':{'army_id':army,'army_regiment_id':identity_removed,'native_carmy_id':native,
        'character_id':child_commander,'native_character_role_v1':role},
      'fresh_sibling_army_id':sibling,'fresh_sibling_native_carmy_id':post[sibling]['native_carmy_id'],
      'actual_child_current_commander':child_commander,'unrelated_actual_commanders_unchanged':commanders,
      'unrelated_physical_DATA_values_and_aliases_unchanged':True,'unrelated_stock_cap_Dweight_and_roster_unchanged':True,
      'excluded_unavailable_cohorts':post_ex,'all_roster_strengths_qualified':False,
      'actual_native_cause_PC_observed':False,'birth_producer_observed':False,'physical_refill_or_loss_observed':False,
      'original_failed_attempt_rewritten':False}

def relay_class(base):
    """Apply only to future split postcondition; Merge keeps original strict."""
    class RoleAwareSplitRelay(base):
        def unchanged_others(self,before,after,selected):
            try:return super().unchanged_others(before,after,selected)
            except RuntimeError as error:
                if len(selected)!=1 or str(error)!='unrelated Army cohort changed':raise
                return qualify_unrelated_role_removal(before,after,source_army_id=selected[0])
    return RoleAwareSplitRelay
