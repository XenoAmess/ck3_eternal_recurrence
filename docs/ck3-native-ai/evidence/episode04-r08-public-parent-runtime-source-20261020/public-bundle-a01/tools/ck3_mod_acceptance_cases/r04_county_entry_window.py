"""Existing one-day arm and direct-v2 physical consumer; no live owner."""
from copy import deepcopy
from .r10_prepare_adapter import need

def arm_window(current, *, sample, sampling, snapshot, army_id, native_carmy_id, selected_unit):
    """Full OFF baseline, explicit natural-phase ON, independent state and frame."""
    before = sample('entry-window-baseline', current)
    row = before['army']
    writer = row['actual_loss_writer_observations_v1']
    need(writer['observer_installed'], 'actual physical writer is not installed')
    need(row['army_id'] == army_id and row['native_carmy_id'] == native_carmy_id, 'actual late baseline full Army identity differs')
    off = sampling(None, 'all')
    need(all((not x['capture_enabled'] and (not x['busy']) for x in off['army_observer_research_sampling_v1'].values())), 'another sampling owner remains active before entry window')
    sampling(True, 'natural_phase')
    on = sampling(None, 'all')
    families = on['army_observer_research_sampling_v1']
    n = families['natural_phase']
    need(n['installed'] and n['available'] and n['capture_enabled'] and (not n['busy']), 'actual fresh natural-phase ON readback is incomplete')
    need(all((k == 'natural_phase' or (not x['capture_enabled'] and (not x['busy'])) for k, x in families.items())), 'entry window must own only natural-phase sampling')
    fresh = snapshot('entry-window-post-enable')
    need(fresh.get('paused') is True and fresh['date_raw'] == before['frame']['date_raw'], 'entry window baseline/ON crossed a real day')
    old = selected_unit(before['frame'], army_id)
    new = selected_unit(fresh, army_id)
    need(all((old.get(k) == new.get(k) for k in ('army_id', 'owner_character_id', 'current_province_id', 'route_province_ids', 'move_target_province_id', 'in_combat', 'retreating'))), 'actual Army movement fence changed before the single entry day')
    for key in ('bridge_pid', 'connection_generation'):
        need(fresh['diagnostics'][key] == before['frame']['diagnostics'][key], 'entry window process/generation changed')
    need(fresh.get('episode_run_id') == before['frame'].get('episode_run_id') and fresh['played_character']['character_id'] == before['frame']['played_character']['character_id'], 'entry window native/managed identity or actor changed')
    return (before, on, fresh)

def consume_window(before, after, *, exe_sha256, endpoint_compare, after_sampling, on_sampling):
    from xar_autoplayer.bridge.army_county_primary_direct_owner_12004 import KEY, evaluate_county_primary_direct_owner_evidence_12004
    from xar_autoplayer.bridge.army_county_entry_loss_evidence_12004 import classify_retained_loss_writer_window_v1
    b = before['army']['actual_loss_writer_observations_v1']
    a = after['army']['actual_loss_writer_observations_v1']
    bf, af = (before['frame'], after['frame'])
    need(af['date_raw'] == bf['date_raw'] + 24 and af['paused'] is True, 'one actual paused exact day required')
    for k in ('bridge_pid', 'connection_generation'):
        need(bf['diagnostics'][k] == af['diagnostics'][k], 'actual process/generation changed')
    need(bf.get('episode_run_id') == af.get('episode_run_id') and bf['played_character']['character_id'] == af['played_character']['character_id'], 'actual frame identity/actor changed')
    n = after_sampling['army_observer_research_sampling_v1']['natural_phase']
    on = on_sampling['army_observer_research_sampling_v1']['natural_phase']
    need(n['capture_enabled'] and (not n['busy']) and (n['epoch'] == on['epoch']), 'natural epoch changed before consume')
    owner = evaluate_county_primary_direct_owner_evidence_12004(after['army'], executable_sha256=exe_sha256, after_sequence=b['latest_sequence'], before_unattributed_capture_failures=b['unattributed_capture_failures'])
    legacy = classify_retained_loss_writer_window_v1(a, current_regiment_ids=after['physical']['ordered_regiment_ids'], executable_sha256=exe_sha256, after_sequence=b['latest_sequence'], before_unattributed_capture_failures=b['unattributed_capture_failures'])
    facts = owner['positive_invocations'] + owner['other_qualified_invocations']
    mismatched = [e['sequence'] for e in facts if e[KEY]['natural_sampling_epoch'] != on['epoch']]
    positive = [e for e in owner['positive_invocations'] if e['sequence'] not in mismatched]
    other = [e for e in owner['other_qualified_invocations'] if e['sequence'] not in mismatched]
    dates = [dict(sequence=e['sequence'], writer_date_raw=e.get('observed_date_raw'), writer_date_raw64=e[KEY]['observed_date_raw64'], writer_invocation_token=e[KEY]['writer_invocation_token'], writer_thread_id=e[KEY]['writer_thread_id'], writer_event=deepcopy(e[KEY]['writer_event']), natural_sampling_epoch=e[KEY]['natural_sampling_epoch'], active_phase_diagnostic={k: e[KEY][k] for k in ('active_phase_observed', 'active_phase_kind', 'active_phase_entry_rva')}) for e in facts]
    delta = a['latest_sequence'] - b['latest_sequence']
    return dict(schema='xar.e04.one-entry-day-direct-owner-window.v2', baseline_date_raw=bf['date_raw'], after_date_raw=af['date_raw'], actual_process_fence=dict(pid=af['diagnostics']['bridge_pid'], generation=af['diagnostics']['connection_generation'], actor_id=af['played_character']['character_id'], consumer_frame_episode_value=af.get('episode_run_id'), research_derived_episode_binding=deepcopy(af.get('research_derived_episode_binding')), actual_native_game_episode_not_inferred_from_managed_alias=True), global_writer_delta=delta, global_writer_capacity=512, delta_within_512=0 <= delta <= 512, baseline_writer_fences={k: b[k] for k in ('latest_sequence', 'oldest_available_sequence', 'overwritten_events', 'unattributed_capture_failures')}, after_writer_fences={k: a[k] for k in ('latest_sequence', 'oldest_available_sequence', 'overwritten_events', 'unattributed_capture_failures')}, global_new_window_continuous=owner['global_window_continuous'], legacy_unowned_physical_window=legacy, direct_invocation_owner_v2=owner, window_epoch_mismatched_sequences=mismatched, window_positive_sequences=[e['sequence'] for e in positive], qualified_positive_invocations=len(positive), qualified_zero_or_other_invocations=len(other), retained_individual_debit_sum=sum((e['actual_physical_soldier_debit'] for e in positive)), actual_writer_dates_and_direct_tokens=dates, endpoint_unique_physical=endpoint_compare(before['physical'], after['physical']), phase_coverage_as_published=deepcopy(after['query'].get('army_observed_phase_coverage')), natural_phase_after_ON_state=deepcopy(n), strict_v1_used_as_owner=False, pre_date_TLS_required=False, returned_phase_parent_claimed=False, parent_dates_forced_to_arrival=False, query_membership_backfilled=False, complete_army_county_debit=None, R04_entire_card_closed=False, note='Only exact new direct-v2 writer/registry/DATA/physical facts qualify individual calls. Global continuity, endpoint NET and whole-Army totals remain separate.')
