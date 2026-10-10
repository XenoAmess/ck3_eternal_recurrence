"""Consume owned Army stage observations without filling historical frames."""
from __future__ import annotations
from copy import deepcopy
from .army_observed_phase_contract_12004 import _token_key

PHASE='army_natural_phase_observations_v1'
CORE='actual_army_regular_core_observations_v1'
PREP='actual_army_daily_assault_preparation_observations_v1'
PLACE='actual_army_assault_placement_observations_v1'
DAILY='army_actual_assault_consumer_observations_v1'
RELEASE='actual_army_assault_group_release_observations_v1'
DUE='native_gathering_due_natural_stage_12004'
CLEANUP='actual_army_cleanup_observations_v1'
PREFIX='actual_army_pre_date_prefix_observations_v1'

def _family(row,key):
    value=row.get(key)
    return value if isinstance(value,dict) else None

def _phase_for(phase_records,token):
    matches=[record for record in phase_records if _token_key(record['scope']['entry_event'])==_token_key(token)]
    return matches[0] if len(matches)==1 else None

def _state(family, *, events=None):
    if family is None: return 'unavailable'
    if family.get('observer_installed') is False or family.get('current_session_guard') is False:
        return 'partial'
    if any(family.get(key,0)>0 for key in ('overwritten_events','unattributed_capture_failures',
           'publication_failures','dropped_owned_copy_events','overwritten_records','unattributed_invocations','dropped_record_copies')):
        return 'partial'
    return 'available' if events is None or events else 'partial'

def project_army_observed_phases_12004(row, *, exact_source):
    result={'army_id':row['army_id'],'native_carmy_id':row.get('native_carmy_id'),
        'source_contract_game_version':'1.20.0.4',
        'input_basis':'owned_natural_stage_copies_joined_by_captured_full_CArmy_ID',
        'later_current_query_used':False,'game_load_epoch_inferred':False,
        'full_daily_assault_ready':False,'full_monthly_ready':False,
        'phase_lineage':[], 'ordered_regular_core':[], 'preparation':[], 'placement':[],
        'daily_assault':[], 'group_release':[], 'gathering_due':[], 'monthfirst_cleanup':[], 'pre_date_prefix':[]}
    if not exact_source:
        return {**result,'status':'unavailable','missing_inputs':['exact_actual4_query_source']}
    phase=_family(row,PHASE)
    phases=phase['records'] if phase else []
    for record in phases:
        scope=record['scope']
        result['phase_lineage'].append({'entry_event':deepcopy(scope['entry_event']),
            'returned_event':deepcopy(record['returned_event']), 'phase':scope['phase'],
            'primary_manager_identity':scope['primary_manager_identity'],
            'date_raw':scope['date_raw'],'prefix_date_raw':scope['prefix_date_raw'],
            'session_identity':scope['session_identity'],
            'session_identity_known':scope['session_identity'] not in (None, 0),
            'original_roster_boundary':scope['original_army_roster']['boundary'],
            'original_roster_complete':scope['original_army_roster']['complete'],
            'ordered_full_id_occurrences':deepcopy(scope['original_army_roster']['ordered_full_ids']),
            'owned_original_return_observed':record['original_called'] and record['original_returned'],
            'same_clock_thread_order':record['same_clock_thread_order']})
    core=_family(row,CORE)
    if core:
        from ..simulation.army_actual_regular_core_stage_12004 import map_actual_regular_core_entry_12004
        from .army_ordered_monthly_core_12004 import project_army_ordered_monthly_core_12004
        for event in core['events']:
            mapped=map_actual_regular_core_entry_12004(event)
            projected=project_army_ordered_monthly_core_12004(mapped['entry']) if mapped['entry'] is not None else None
            result['ordered_regular_core'].append({'journal_sequence':event['journal_sequence'],
                'entry_event':deepcopy(event['entry_event']),'returned_event':deepcopy(event['returned_event']),
                'owned_original_return_observed':event['original_called'] and event['original_returned'],
                'entry_capture_complete':event['entry']['capture_complete'],
                'returned_capture_complete':event['returned']['capture_complete'],
                'conditional_entry_projection':projected,'missing_inputs':mapped['missing'],
                'returned_frame_used_to_fill_entry':False})
    preparation=_family(row,PREP)
    if preparation:
        for event in preparation['events']:
            result['preparation'].append({'sequence':event['sequence'],
                'entry_event':deepcopy(event['active']['entry_event']),
                'returned_event':deepcopy(event['returned_event']),
                'parent_bound':event['active']['parent_bound'],
                'original_occurrence_bound':event['active']['original_occurrence_bound'],
                'owned_original_return_observed':event['original_called'] and event['original_returned'],
                'original_rax_raw_u64':event['original_rax_raw_u64'],
                'source_inputs_ready':event['before']['source_inputs_ready'],
                'copied_entry_stage':deepcopy(event['before']['copied_stage_input']),
                'same_selected_army_generation_after':event['same_selected_army_generation_after'],
                'capture_failure_flags':event['capture_failure_flags']})
    placement=_family(row,PLACE)
    if placement:
        for event, projected in zip(placement['events'],placement['conditional_preparation_append_projections']):
            result['placement'].append({'sequence':event['sequence'],
                'entry_event':deepcopy(event['entry_event']),'returned_event':deepcopy(event['returned_event']),
                'parent_bound':event['parent_bound'],
                'owned_original_return_observed':event['original_called'] and event['original_returned'],
                'actual_returned_physical_slot_i64':event['returned_physical_slot_i64'],
                'actual_returned_inserted_raw_u8':event['returned_inserted_raw_u8'],
                'observed_after_stage':event['after']['stage'],
                'observed_after_capture_complete':event['after']['capture_complete'],
                'conditional_preparation_append':deepcopy(projected),
                'after_table_promoted_to_later_append':False})
    consumer=_family(row,DAILY)
    consumer_stages=[]
    if consumer:
        from ..simulation.army_actual_assault_consumer_stage_12004 import map_actual_assault_consumer_stage_12004
        from ..simulation.army_daily_assault_loss_consumer_12004 import project_army_daily_assault_loss_stage_12004
        for event in consumer['events']:
            phase_record=_phase_for(phases,event['parent']['phase_entry_event'])
            mapped=map_actual_assault_consumer_stage_12004(event,phase_record)
            projected=None
            if mapped['army'] is not None and mapped['stage'] is not None:
                army={**mapped['army'],'army_id':row['army_id']}
                projected=project_army_daily_assault_loss_stage_12004(army,stage=mapped['stage'])
            wrapper={'native_event':event,'phase_record':phase_record,'mapped':mapped,'projection':projected}
            consumer_stages.append(wrapper)
            budgets=[{'group_native_index':group['native_index'],'physical_slot_i64':group['physical_slot_i64'],
                'native_expected_loss_i32':group['native_current_expected_loss'],
                'natural_budget_observed':group['natural_budget_observed'],
                'budget_entry_event':deepcopy(group['budget_entry_event']),
                'budget_returned_event':deepcopy(group['budget_returned_event']),
                'basis':'actual_group_child_return_after_preceding_group_writes',
                'full_besieging_dependencies_captured':group['besieging_dependencies_complete']}
                for group in event['entry_table']['groups']]
            result['daily_assault'].append({'journal_sequence':event['journal_sequence'],
                'entry_event':deepcopy(event['parent']['entry_event']),
                'returned_event':deepcopy(event['returned_event']),
                'owned_original_return_observed':event['original_called'] and event['original_returned'],
                'exact_post_date_parent':event['parent']['exact_post_date_parent'],
                'entry_dependencies_complete':event['entry_dependencies_complete'],
                'returned_dependencies_complete':event['returned_dependencies_complete'],
                'native_group_budget_observations':budgets,
                'conditional_numerical_projection':projected,'missing_inputs':mapped['missing'],
                'child_budget_promoted_to_simultaneous_entry_B':False})
    release=_family(row,RELEASE)
    if release:
        from ..simulation.army_actual_assault_release_stage_12004 import map_actual_assault_release_stage_12004
        from .army_assault_group_release_12004 import project_army_assault_group_release_stage_12004
        for event in release['events']:
            matches=[wrapper for wrapper in consumer_stages if _token_key(wrapper['native_event']['parent']['entry_event'])==_token_key(event['consumer_entry_event'])]
            wrapper=matches[0] if len(matches)==1 else None
            mapped=map_actual_assault_release_stage_12004(event,wrapper)
            projected=None
            if mapped['stage'] is not None and wrapper is not None and wrapper['mapped']['army'] is not None and wrapper['projection'] is not None:
                army={**wrapper['mapped']['army'],'army_id':row['army_id']}
                projected=project_army_assault_group_release_stage_12004(army,
                    numerical_stage=wrapper['projection'],stage=mapped['stage'])
            result['group_release'].append({'sequence':event['sequence'],
                'entry_event':deepcopy(event['entry_event']),'returned_event':deepcopy(event['returned_event']),
                'owned_original_return_observed':event['original_returned'],
                'post_stage':event['post_stage'],'observed':mapped['observed'],
                'conditional_release_projection':projected,'missing_inputs':mapped['missing'],
                'later_caller_bookkeeping_inferred':False})
    due=_family(row,DUE)
    if due:
        for event in due['records']:
            result['gathering_due'].append({'entry_event':deepcopy(event['entry']['event']),
                'returned_event':deepcopy(event['returned']['event']),
                'owned_original_return_observed':event['original_called'] and event['original_returned'],
                'actual_boundary_admitted':event['actual_boundary_admitted'],
                'actual_poststage_observed':event['actual_poststage_observed'],
                'entry_queue_complete':event['entry']['queue158']['complete'],
                'returned_queue_complete':event['returned']['queue158']['complete'],
                'entry_queue_extent_backing_full_ids':deepcopy(event['returned']['entry_queue_extent_backing_full_ids']),
                'returned_physical_read_complete':event['returned']['all_declared_reads_complete'],
                'missing_inputs':deepcopy(event['returned']['missing_fields']),
                'returned_frame_used_to_fill_regular_core_entry':False})
    cleanup=_family(row,CLEANUP)
    if cleanup:
        for event in cleanup['journal']['events']:
            result['monthfirst_cleanup'].append({'journal_ordinal':event['journal_ordinal'],
                'membership_basis':cleanup['membership_basis'],
                'before_event':deepcopy(event['before_event']),'returned_event':deepcopy(event['returned_event']),
                'owned_original_return_observed':event['original_called'] and event['original_returned'],
                'saved_mask02_admitted_by_literal_call':event['saved_mask02_admitted_by_literal_call'],
                'before_physical_copy_complete':event['before']['physical_copy_complete'],
                'after_physical_copy_complete':event['after']['physical_copy_complete'],
                'actual_live_count_before':event['before']['live_count_raw_i32'],
                'actual_live_count_after':event['after']['live_count_raw_i32'],
                'unknown_callback_physical_indices':[slot['physical_index'] for slot in event['before']['physical_slots'] if slot['slot0_matches_known_mode0_source'] is not True],
                'conditional_predictor_executed':False,'cleanup_entry_Army_membership_inferred':False})
    prefix=_family(row,PREFIX)
    if prefix:
        for journal in prefix['journals']:
            for event in journal['events']:
                result['pre_date_prefix'].append({'sequence':event['sequence'],
                    'entry_event':deepcopy(event['entry_event']),'returned_event':deepcopy(event['returned_event']),
                    'owned_original_return_observed':event['original_called'] and event['original_returned'],
                    'original_roster_capture_complete':event['original_roster_capture_complete'],
                    'ordered_full_id_occurrences':deepcopy(event['captured_original_roster']['ordered_full_ids']),
                    'conditional_no_work_arm':event['before']['conditional_no_work_arm'],
                    'before_queue_complete':event['before']['destination_158']['copied_complete'],
                    'after_queue_complete':event['after']['destination_158']['copied_complete'],
                    'positive_physical_transition_complete':False})
    known=[key for key in (PHASE,CORE,PREP,PLACE,DAILY,RELEASE,DUE,CLEANUP,PREFIX) if _family(row,key) is not None]
    result['family_status']={key:_state(_family(row,key)) for key in (PHASE,CORE,PREP,PLACE,DAILY,RELEASE,DUE,CLEANUP,PREFIX)}
    result['status']='partial' if known else 'unavailable'
    result['missing_inputs']=['owned_'+key for key in (PHASE,CORE,PREP,PLACE,DAILY,RELEASE,DUE,CLEANUP,PREFIX) if key not in known]
    return result
