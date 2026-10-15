"""R03 consumes a real callback/writer join without inventing siege-only cause."""
from __future__ import annotations

from .army_physical_loss_evidence_12004 import evaluate_army_physical_loss_evidence_12004
from .army_actual_supply_parent_join_summary import join_actual_supply_parent_writer_observations_v1


def evaluate_siege_parent_loss_evidence_12004(
    army: dict, *, game_version: str, executable_sha256: str,
    callback_after_sequence: int, loss_after_sequence: int,
    date_raw_min_exclusive: int | None = None,
    date_raw_max_inclusive: int | None = None,
    previously_reported_sequences: frozenset[int] = frozenset(),
) -> dict:
    """Select positive combined-stage writers with their exact daily callback.

    Input is one normalized whole-query Army row, already bound by the caller
    to one actual process/connection/episode and journal lifetime. The output
    records copied facts. Actual siege/raid predicates and clean video marks
    remain external observations, never inferred from these journal keys.
    """
    joined = join_actual_supply_parent_writer_observations_v1(
        army, game_version=game_version, executable_sha256=executable_sha256,
        callback_after_sequence=callback_after_sequence, loss_after_sequence=loss_after_sequence)
    result = {
        'basis': 'same_actual_daily_callback_and_complete_positive_physical_writer',
        'status': 'unavailable', 'same_callback_combined_stage_positive_observed': False,
        'combined_stage_positive_events': [], 'excluded_positive_events': [],
        'siege_only_positive_writer_events': [],
        'journal_join_coverage': joined, 'missing_inputs': [],
        'siege_only_causal_attribution_ready': False,
        'residual_cause_attribution_ready': False,
        'complete_interval_loss_total_ready': False,
        'callback_entry_stock_used': False, 'callback_return_stock_used': False,
        'regular_core_delta_used': False, 'new_live_evidence': False,
    }
    if 'exact_build_binding_missing_or_mismatched' in joined['unknown_reasons']:
        result['missing_inputs'] = ['exact_actual4_query_source']
        return result
    for name in ('actual_loss_writer_observations_v1', 'actual_supply_callback_observations_v1'):
        family = army.get(name)
        if not isinstance(family, dict) or family.get('observer_installed') is not True:
            result['missing_inputs'].append(name + '.observer_installed')
    if result['missing_inputs']:
        return result
    physical = evaluate_army_physical_loss_evidence_12004(
        army, exact_source=True, after_sequence=loss_after_sequence,
        date_raw_min_exclusive=date_raw_min_exclusive,
        date_raw_max_inclusive=date_raw_max_inclusive,
        previously_reported_sequences=previously_reported_sequences)
    result['physical_writer_evidence'] = physical
    by_writer = {event['writer_sequence']: event for event in joined['events']}
    callbacks = {event['sequence']: event for event in army['actual_supply_callback_observations_v1']['events']}
    for event in physical['positive_events']:
        matching = by_writer.get(event['sequence'])
        reason = None
        if matching is None or matching['status'] != 'joined':
            reason = 'copied_unique_callback_parent_not_joined'
        elif not matching['source_siege_or_raid_preferred']:
            reason = 'not_source_combined_siege_raid_preferred'
        else:
            callback = callbacks[matching['callback_sequence']]
            invocation = callback['supply_parent_invocation_v1']
            if (invocation['callback_caller_return_rva'] != 0x2A9AB4B
                    or callback['caller_return_rva'] != 0x2A9AB4B):
                reason = 'callback_not_source_daily_dispatch_return'
        if reason:
            result['excluded_positive_events'].append({'writer_sequence': event['sequence'], 'reason': reason})
            continue
        token = matching['invocation_token']
        siblings = [other for other in joined['events'] if other['status'] == 'joined'
                    and other['invocation_token'] == token and other['source_supply_preferred']]
        result['combined_stage_positive_events'].append({
            **event, 'callback_sequence': matching['callback_sequence'],
            'callback_invocation_token': token,
            'stock_at_writer_entry_raw': matching['stock_at_writer_entry_raw'], 'stock_scale': 100000,
            'same_callback_source_supply_preferred_writers': [
                {'writer_sequence': other['writer_sequence'],
                 'stock_at_writer_entry_raw': other['stock_at_writer_entry_raw'],
                 'physical_debit_soldiers': other['physical_debit_soldiers']} for other in siblings],
        })
    originals = {event['sequence']: event for event in army['actual_loss_writer_observations_v1']['events']}
    for event in result['combined_stage_positive_events']:
        leaf = originals[event['sequence']].get('siege_budget_at_writer_v1')
        event['source_siege_only_budget_bound'] = False
        event['original_supply_budget_soldiers'] = leaf.get('original_supply_budget_soldiers') if leaf else None
        if (leaf and leaf['siege_raid_capture_complete']
                and leaf['capture_failure_flags'] & 13 == 0
                and leaf['original_siege_budget_soldiers'] > 0
                and leaf['derived_original_raid_budget_soldiers'] == 0):
            event['source_siege_only_budget_bound'] = True
            event['siege_budget_at_writer_v1'] = leaf
            result['siege_only_positive_writer_events'].append(dict(event))
    result['siege_only_causal_attribution_ready'] = bool(result['siege_only_positive_writer_events'])
    result['same_callback_combined_stage_positive_observed'] = bool(result['combined_stage_positive_events'])
    result['status'] = ('same_callback_combined_stage_positive_observed'
                        if result['combined_stage_positive_events'] else 'no_qualified_combined_stage_event')
    return result
