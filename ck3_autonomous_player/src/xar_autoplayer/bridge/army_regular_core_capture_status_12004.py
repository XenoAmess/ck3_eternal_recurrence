"""Describe an actual retained regular-core export without inventing a callback.

Call after the day's full query and an independent sampling query, before OFF.
This is a pure reader; no native calls, inferred calendar or physical ADD claim.
"""
from copy import deepcopy
from .army_observed_phase_contract_12004 import normalize_army_observed_phase_family_12004
from .army_observer_research_sampling_control import normalize_result
from .army_strengths_profile_contract import OBSERVED_HISTORY_FULL_PROFILE, ORDINARY_CORE_PROFILE

CORE = 'actual_army_regular_core_observations_v1'

def _sampling(packet):
    if packet is None:
        return None
    keys = ('step', 'accepted', 'status', 'army_observer_research_sampling_v1', 'backend_id')
    result = normalize_result({key:packet[key] for key in keys},
        expected_step='query-army-observer-research-sampling-v1', observer_family='all')
    if result['accepted'] is not True:
        raise ValueError('Actual sampling query was not accepted')
    return deepcopy(result['army_observer_research_sampling_v1']['regular_core'])

def classify_regular_core_capture_window_12004(row, *, profile, before_sampling, after_sampling=None):
    """Keep missing/null/exported and post-OFF/missing status readback distinct."""
    if profile not in (OBSERVED_HISTORY_FULL_PROFILE, ORDINARY_CORE_PROFILE):
        raise ValueError('Explicit actual Army query profile required')
    if type(row) is not dict or type(row.get('army_id')) is not int or not 0 <= row['army_id'] < 2**31:
        raise ValueError('Actual public CUnit ID required, including zero')
    result = dict(army_id=row['army_id'], native_carmy_id=row.get('native_carmy_id'),
        family_key=CORE, profile=profile, field_state='missing' if CORE not in row else 'explicit_null' if row[CORE] is None else 'exported',
        callback_execution_claim=False, physical_ADD_claim=False, full_monthly_ready=False,
        historical_entry_filled_from_current=False, reasons=[])
    if profile == ORDINARY_CORE_PROFILE:
        if CORE in row:
            raise ValueError('Ordinary profile must not export retained phase fields')
        return {**result, 'status':'not_requested', 'before_sampling':None, 'after_sampling':None}
    if CORE not in row:
        raise ValueError('Observed full profile omitted the actual regular-core key')
    carmy = row.get('native_carmy_id')
    if type(carmy) is not int or not -(2**31) <= carmy < 2**31 or row.get('status') != 'available':
        raise ValueError('Actual available full CArmy identity required')
    family = normalize_army_observed_phase_family_12004(CORE, row[CORE], expected_carmy_id=carmy)
    before, after = _sampling(before_sampling), _sampling(after_sampling)
    result.update(before_sampling=before, after_sampling=after,
                  exported_event_count=len(family['events']) if family is not None else 0)
    if before is None or after is None:
        return {**result, 'status':'sampling_window_readback_missing',
                'reasons':['Actual independent ON status is required both before and after the day, before OFF/clear. Null alone cannot distinguish no capture, unqualified capture or no subject match.']}
    if any(s['installed'] is not True or s['available'] is not True for s in (before,after)):
        return {**result, 'status':'observer_unavailable'}
    if before['epoch'] != after['epoch']:
        return {**result, 'status':'sampling_epoch_changed'}
    if any(s['capture_enabled'] is not True or s['busy'] is not False for s in (before,after)):
        return {**result, 'status':'not_a_completed_enabled_window',
                'reasons':['OFF/clear counters cannot reconstruct the preceding enabled window.']}
    if before['retained_records'] != 0 or before['qualified_records'] != 0:
        return {**result, 'status':'baseline_already_has_retained_records'}
    if family is not None and family['events']:
        return {**result, 'status':'matching_core_events_exported',
                'reasons':['Pass these actual events to the existing strict core/physical application consumer; this status grants no ADD.']}
    if after['retained_records'] == 0 and after['qualified_records'] == 0:
        return {**result, 'status':'no_retained_core_in_enabled_window',
                'reasons':['No retained published core record is reported. This is not proof of no native invocation: publication failures are not supplied by this sampling status.']}
    if after['qualified_records'] == 0:
        return {**result, 'status':'retained_core_without_qualified_entry_return',
                'reasons':['Native sampled export suppresses a journal with zero qualified original entry/return records.']}
    return {**result, 'status':'no_exported_event_for_requested_carmy',
            'reasons':['Native serializer filters by the captured entry Army-refresh roster. Query-time roster membership cannot repair that historical association.']}
