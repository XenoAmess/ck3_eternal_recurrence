"""Per-writer periodic causes; merged native losses retain a cause set, no split."""
from __future__ import annotations

from .army_physical_loss_evidence_12004 import evaluate_army_physical_loss_evidence_12004
from .army_actual_supply_parent_join_summary import join_actual_supply_parent_writer_observations_v1


def _combined_causes(leaf, residual):
    if not leaf:
        return None, 'original_combined_operands_not_captured', None
    if residual:
        valid=leaf['capture_failure_flags']==0
    else:
        valid=leaf['siege_raid_capture_complete'] and leaf['capture_failure_flags']&13==0
    if not valid:
        return None, 'original_combined_operands_unreadable', None
    siege=leaf['original_siege_budget_soldiers']
    combined=leaf['combined_siege_raid_budget_soldiers']
    raid=((combined-siege+(1<<31))%(1<<32))-(1<<31)
    operands={'original_siege_budget_soldiers':siege,
              'derived_original_raid_budget_soldiers':raid,
              'combined_siege_raid_budget_soldiers':combined}
    # Preserve native signed add semantics. A wrapped or nonpositive merge
    # does not support a positive-contribution causal claim.
    if siege<0 or raid<0 or combined<=0 or siege+raid!=combined:
        return None, 'combined_operands_not_nonnegative_unwrapped_positive', operands
    return (['siege'] if siege>0 else [])+(['raid'] if raid>0 else []), None, operands


def evaluate_periodic_loss_cause_evidence_12004(
    army:dict, *, game_version:str, executable_sha256:str,
    callback_after_sequence:int, loss_after_sequence:int,
    date_raw_min_exclusive:int|None=None, date_raw_max_inclusive:int|None=None,
    previously_reported_sequences:frozenset[int]=frozenset(),
) -> dict:
    """Consume one already process/session-bound, normalized actual4 Army row.

    Positive unique-slot physical facts, exact daily callback token and actual
    residual membership are required. Known mixed causes never receive a
    fabricated allocation of their shared native physical debit.
    """
    joined=join_actual_supply_parent_writer_observations_v1(
        army,game_version=game_version,executable_sha256=executable_sha256,
        callback_after_sequence=callback_after_sequence,loss_after_sequence=loss_after_sequence)
    out={'scope':'individual_retained_periodic_positive_physical_writer_invocations',
         'status':'unavailable','qualified_events':[],'excluded_events':[],
         'per_cause_physical_debit_split_observed':False,
         'complete_interval_loss_total_ready':False,'new_live_evidence':False,
         'journal_join_coverage':joined,'missing_inputs':[]}
    if 'exact_build_binding_missing_or_mismatched' in joined['unknown_reasons']:
        out['missing_inputs']=['exact_actual4_query_source'];return out
    for family in ('actual_loss_writer_observations_v1','actual_supply_callback_observations_v1'):
        if not isinstance(army.get(family),dict) or army[family].get('observer_installed') is not True:
            out['missing_inputs'].append(family+'.observer_installed')
    if out['missing_inputs']:return out
    physical=evaluate_army_physical_loss_evidence_12004(
        army,exact_source=True,after_sequence=loss_after_sequence,
        date_raw_min_exclusive=date_raw_min_exclusive,date_raw_max_inclusive=date_raw_max_inclusive,
        previously_reported_sequences=previously_reported_sequences)
    out['physical_writer_evidence']=physical
    writers={e['sequence']:e for e in army['actual_loss_writer_observations_v1']['events']}
    matches={e['writer_sequence']:e for e in joined['events']}
    callbacks={e['sequence']:e for e in army['actual_supply_callback_observations_v1']['events']}
    for fact in physical['positive_events']:
        seq=fact['sequence'];writer=writers[seq];match=matches.get(seq);reason=None
        stage=None;causes=None;operands=None
        if match is None or match['status']!='joined':reason='unique_actual_callback_parent_not_joined'
        else:
            callback=callbacks[match['callback_sequence']]
            inv=callback['supply_parent_invocation_v1']
            if callback['caller_return_rva']!=0x2A9AB4B or inv['callback_caller_return_rva']!=0x2A9AB4B:
                reason='not_actual_daily_dispatch_callback'
            elif writer['caller_return_rva']==0x24E377C and writer['caller_kind']=='siege_or_raid_preferred':
                stage='siege_raid_preferred'
                causes,reason,operands=_combined_causes(writer.get('siege_budget_at_writer_v1'),False)
            elif writer['caller_return_rva']==0x2A958E8 and writer['caller_kind']=='residual_allocator':
                parent=writer.get('residual_parent_context_v1')
                if (not parent or not parent['source_complete'] or parent['request_source']!='periodic_callback'
                        or parent['parent_invocation_token']!=inv['invocation_token']
                        or parent['native_thread_id']!=inv['native_thread_id']
                        or parent['nesting_depth']!=inv['nesting_depth']+1
                        or parent['enclosing_parent_kind']!=1
                        or parent['army_id']!=army['army_id'] or parent['native_carmy_id']!=army['native_carmy_id']):
                    reason='actual_direct_periodic_allocator_parent_not_proved'
                elif parent['allocator_caller_return_rva']==0x24E3638 and parent['flags_raw']==2:
                    stage='supply_residual';causes=['supply']
                elif parent['allocator_caller_return_rva']==0x24E37B3 and parent['flags_raw']==0:
                    stage='siege_raid_residual'
                    causes,reason,operands=_combined_causes(parent.get('siege_budget_at_allocator_v1'),True)
                else:reason='allocator_call_not_exact_periodic_stage'
            else:reason='not_selected_periodic_combined_or_residual_stage'
        if reason:
            out['excluded_events'].append({'writer_sequence':seq,'source_stage':stage,
                'reason':reason,'original_budget_operands':operands})
            continue
        out['qualified_events'].append({**fact,'source_stage':stage,'source_cause_set':causes,
            'original_budget_operands':operands,'callback_sequence':match['callback_sequence'],
            'callback_invocation_token':match['invocation_token'],
            'physical_debit_scope':'this_whole_native_writer_invocation',
            'per_cause_physical_debit_soldiers':None})
    out['status']='qualified_individual_periodic_loss_causes' if out['qualified_events'] else 'no_qualified_individual_periodic_loss_cause'
    return out
