"""Current persistent refill inputs, normal preparation, and cached core gates.

Consumes complete same-frame actual4 Strength DTOs. Never labels a permanent
troop category from headcount/MAA absence, calls native code, or claims an ADD.
"""
from __future__ import annotations
from collections.abc import Mapping

from .army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
from .army_fixed_chunk0_preparation_contract import normalize_fixed_chunk0_preparation_inputs_v1
from .army_fixed_chunk0_preparation_projection import project_fixed_chunk0_preparation_family_v1
from .army_split_merge_observation_12004 import compare_split_merge_cohorts

_GDbo=0x4744624F
_SHA='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'

def _need(ok,reason):
    if not ok:raise ValueError(reason)

def _bind(frame,packet):
    _need(frame.get('paused') is True and frame.get('map_ready') is True,'paused ready frame required')
    diagnostic=frame.get('diagnostics') or {};hello=diagnostic.get('hello') or {}
    _need(type(diagnostic.get('bridge_pid')) is int and diagnostic['bridge_pid']>0
          and type(diagnostic.get('connection_generation')) is int and diagnostic['connection_generation']>0,
          'actual process/connection identity missing')
    _need(hello.get('expected_ck3_version')=='1.20.0.4'
          and str(hello.get('expected_ck3_sha256','')).lower()==_SHA,
          'refill eligibility requires the frozen actual4 build')
    _need(packet.get('accepted') is True,'actual Strength query not accepted')
    for query_key,frame_key in (('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),
                               ('queried_native_revision','native_revision'),('queried_date_raw','date_raw'),
                               ('queried_episode_run_id','episode_run_id')):
        if (frame_key == 'episode_run_id' and frame.get('episode_projection') == 'native_campaign'
                and frame.get(frame_key) is None):
            _need(query_key in packet and packet[query_key] is None,
                  'ordinary native refill query must preserve absent/null game episode')
        else:
            _need(frame.get(frame_key) is not None and packet.get(query_key)==frame[frame_key],
                  'refill query differs from its actual frame: '+query_key)
    _need(packet.get('queried_connection_generation')==diagnostic['connection_generation'],
          'refill query connection changed')

def classify_army_persistent_refill_eligibility_12004(
    frame: Mapping[str,object], packet: Mapping[str,object], *, army_id: int,
) -> dict[str,object]:
    """Join existing allDATA and fixed-chunk0 leaves without adding a reader.

    The raw containing +138 is not a published special-troop enum name. Missing
    inputs stay unknown. A source conditional preparation result is explicitly
    different from the observed prepared148 and from a later executed request.
    """
    _bind(frame,packet)
    armies=packet.get('army_strengths')
    _need(type(armies) is list,'complete typed Army rows required')
    ids=[row.get('army_id') for row in armies]
    _need(len(ids)==len(set(ids)) and army_id in ids,'duplicate or missing queried Army FullID')
    army=armies[ids.index(army_id)]
    compare_split_merge_cohorts([army],[army])
    data=normalize_regiment_replenishment_records_v1(army['regiment_replenishment_records_v1'])
    family=normalize_fixed_chunk0_preparation_inputs_v1(
        army.get('fixed_chunk0_preparation_inputs_v1'),expected_army_id=army_id,
        expected_carmy_id=army['native_carmy_id'])
    projected=project_fixed_chunk0_preparation_family_v1(
        family,army_id=army_id,native_carmy_id=army['native_carmy_id'])
    raw_rows={} if family is None else {row['persistent_regiment_id']:row for row in family['persistent_regiments']}
    if family is not None:
        _need(len(raw_rows)==len(family['persistent_regiments']),'duplicate containing persistent FullID')
    projections={row['persistent_regiment_id']:row for row in projected['persistent_regiments']}
    physical={};occurrences=[];empty=[]
    for ar in data:
        _need(ar['status']=='available' and ar['ready'] is True,'partial allDATA is not zero eligibility')
        if not ar['records']:
            role=ar.get('native_character_role_v1')
            character=(ar.get('native_loss_writer_skipped') is True and role is not None
                       and role.get('status')=='available' and role.get('native_character_predicate') is True
                       and role.get('same_ArRg_instance_after') is True
                       and role.get('native_carmy_id')==army['native_carmy_id'])
            empty.append({'army_regiment_id':ar['army_regiment_id'],
              'kind':'empty_Character_role_record' if character else 'empty_ArRg_unclassified',
              'persistent_refill_eligibility':None,'physical_DATA_records':0,
              'is_physical_refill':False})
        for record in ar['records']:
            _need(record['status']=='available' and record.get('chunk_army_regiment_id')==ar['army_regiment_id'],
                  'available physical DATA with actual ArRg backlink required')
            key=(record['persistent_regiment_id'],record['chunk_index'])
            _need(key[0]!=-1 and type(key[1]) is int and 0<=key[1]<7,'invalid persistent/physical chunk identity')
            # record_index belongs to the ArRg DATA occurrence, not the physical
            # token; do not drop or double-count aliases when comparing values.
            signature={k:v for k,v in record.items() if k!='record_index'}
            _need(key not in physical or physical[key]==signature,'aliased physical DATA observations disagree')
            physical[key]=signature
            occurrences.append({'army_regiment_id':ar['army_regiment_id'],'record_index':record['record_index'],
                                'persistent_regiment_id':key[0],'chunk_index':key[1]})
    referenced={key[0] for key in physical}
    if family is not None and family['referenced_persistent_ids_complete']:
        _need(set(raw_rows)==referenced,'containing input family differs from the actual allDATA persistent set')
    output=[]
    for (persistent,index),record in sorted(physical.items()):
        raw=raw_rows.get(persistent) or {};projection=projections.get(persistent) or {}
        guard=raw.get('containing_guard_138_raw');magic=raw.get('containing_definition_magic_38')
        can=record['native_can_replenish'];chunk_can=record['native_chunk_can_replenish']
        observed=record['persistent_prepared_replenishment_fraction_raw']
        fresh=record['persistent_monthly_replenishment_fraction_raw']
        if raw.get('fresh_fraction_raw') is not None:
            _need(raw['fresh_fraction_raw']==fresh,'same-query fresh fraction differs for one persistent FullID')
        conditional=projection.get('conditional_prepared_fraction_raw')
        branch=projection.get('preparation_branch','unknown')
        if guard==1:
            _need(can is False and raw.get('native_fixed_chunk0_can_replenish') is not True,
                  'actual guard138==1 conflicts with native permission early-false branch')
            # Source-derived constant: do not pretend the missing native bool was
            # observed. This branch rejects every chunk before Army/definition.
            conditional=0;branch='guard138_eq1_source_early_false'
            reason='persistent_guard138_eq1_rejected_before_Army_definition_or_switch'
        elif guard is not None and magic is not None and magic!=_GDbo:
            reason=('non_GDbo_direct_true_after_Army_guards' if can else
                    'non_GDbo_permission_rejected_by_resolved_Army_raw_flags')
        elif magic==_GDbo:
            reason='GDbo_Army_source_Character_switch_resource_and_chunk_path'
        else:reason='native_permission_observed_cause_unresolved'
        output.append({'persistent_regiment_id':persistent,'chunk_index':index,
          'current_soldiers':record['current_soldiers'],'maximum_soldiers':record['maximum_soldiers'],
          'state_raw':record['state_raw'],'native_can_replenish':can,
          'native_chunk_can_replenish':chunk_can,'permission_source_branch':reason,
          'containing_guard_138_raw':guard,'containing_definition_magic_38':magic,
          'persistent_enum_name':None,'player_origin_category':None,
          'observed_prepared148_raw':observed,'observed_fresh_fraction_raw':fresh,
          'conditional_prepared_if_normal_preparation_called_raw':conditional,
          'conditional_preparation_branch':branch,'fraction_scale':100000,
          'stored_prepared_is_positive':observed>0,
          'independent_chunk_gate_for_stored_core':chunk_can,
          'current_permission_false_does_not_rule_out_stored_core_request':
              can is False and observed>0 and chunk_can is True,
          'integer_request_can_still_truncate_to_zero':True,
          'actual_preparation_observed':False,'actual_ADD_observed':False})
    return {'status':'CURRENT_REFILL_INPUTS_CLASSIFIED','army_id':army_id,'native_carmy_id':army['native_carmy_id'],
      'queried_snapshot_id':frame['snapshot_id'],'queried_revision':frame['revision'],
      'queried_native_revision':frame['native_revision'],'date_raw':frame['date_raw'],
      'source_contract_game_version':'1.20.0.4','physical_chunks':output,'DATA_occurrences':occurrences,
      'empty_ArRg_rows':empty,'unique_physical_chunk_count':len(physical),
      'containing_inputs_available':family is not None,'new_native_field_required':False,
      'permanent_nonreplenishing_category_proven':False,'special_or_activity_creation_producer_observed':False,
      'native_Knight_membership':None,'actual_physical_refill':None,'actual_ADD_observed':False,
      'agent_conclusion':'Use actual branch-specific current eligibility; keep stored core/preparation/applied refill separate',
      'video_claim':'1/1 Character rows are not physical refill. Current native permission and a positive fresh rate do not prove soldiers were added.'}
