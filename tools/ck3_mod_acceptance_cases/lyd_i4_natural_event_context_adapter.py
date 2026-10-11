"""Discover the first naturally encountered event; select no event or school option."""
from __future__ import annotations

from pathlib import Path

from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as natural

require = natural.require
CASE = 'i4-natural-event-context'
RESULT = 'i4-natural-event-context-result'
TOOL = 'ck3_query_current_event_window_context_v1'


def contract():
    return natural.base.read_json(Path(__file__).with_name('lyd_i4_natural_event_context.json'))


def validate_contract(context):
    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == CASE and data == contract(), 'Exact event discovery case required')
    require(data['maximum_natural_days'] == 90 and data['event_choice_actions'] == 0 and
            data['school_choice_actions'] == 0 and data['business_contract_applicable'] is False,
            'Discovery cannot become a choice or expiry case')


def prepare_case(context):
    validate_contract(context)
    # Only preparation delegates to the unchanged original0240 product/profile
    # guards. Actual run, result and selected public case keep their own identity.
    inherited = {**context, 'case': natural.contract()['case_id'], 'case_contract': natural.contract()}
    result = natural.prepare_case(inherited)
    return {**result, 'business_contract_applicable': False, 'business_pass': False,
            'discovery_case': CASE, 'inherited_preparation_case': inherited['case']}


def same_event_frame(client, before, after, *, fresh=False):
    client.validate_frame(before, require_event_free=False)
    client.validate_frame(after, require_event_free=False)
    require(natural.frame_identity(before) == natural.frame_identity(after) and
            type(before.get('native_revision')) is int and
            type(after.get('native_revision')) is int and
            (after['native_revision'] >= before['native_revision'] if fresh else
             after['native_revision'] == before['native_revision']) and
            (not fresh or type(before.get('revision')) is int and type(after.get('revision')) is int and
             after['revision'] >= before['revision']), 'Event query crossed actual owner/date/native frame')
    left, right = before.get('active_event'), after.get('active_event')
    require(isinstance(left, dict) and isinstance(right, dict) and
            type(left.get('instance_id')) is int and left['instance_id'] > 0 and
            right.get('instance_id') == left['instance_id'], 'Actual event instance changed')


def validate_boundary(client, row, before, initial, elapsed, maximum_days):
    require(row.get('ok') is True and not row.get('error'), 'Original event-boundary advance failed; never replay')
    value = row['result']
    prior, after, event = value['before'], value['after'], value.get('event_boundary')
    client.validate_frame(prior)
    client.validate_frame(after, require_event_free=False)
    require(isinstance(event, dict), 'Actual event-boundary snapshot required')
    client.validate_frame(event, require_event_free=False, require_paused=False)
    boundary_event = event.get('active_event')
    hours = value.get('elapsed_hours')
    require(natural.frame_identity(prior) == natural.frame_identity(before) and
            natural.frame_identity(after)[:3] == natural.frame_identity(initial)[:3] and
            value.get('requested_days') == 1 and type(value.get('requested_interval_complete')) is bool and
            natural.frame_identity(event)[:3] == natural.frame_identity(initial)[:3] and
            isinstance(boundary_event, dict) and type(boundary_event.get('instance_id')) is int and
            boundary_event['instance_id'] > 0 and before['date_raw'] <= event['date_raw'] <= after['date_raw'] and
            isinstance(after.get('active_event'), dict) and
            after['active_event'].get('instance_id') == boundary_event['instance_id'] and
            value.get('selected_event_options') == 0 and value.get('event_resolution') == 'typed_query_required' and
            type(hours) is int and 0 <= hours < 48 and after['date_raw'] - before['date_raw'] == hours and
            elapsed + hours == after['date_raw'] - initial['date_raw'] and
            elapsed + hours <= maximum_days * 24, 'Contiguous bounded same-owner event interval required')
    same_event_frame(client, after, row['after_snapshot'])
    return elapsed + hours, row['after_snapshot']


def discover_context(client, boundary_frame):
    from ck3_mod_acceptance import pin
    frame = client.snapshot(require_event_free=False)
    same_event_frame(client, boundary_frame, frame, fresh=True)
    name = 'i4-first-natural-event-context'
    event_id = frame['active_event']['instance_id']
    rows = client.execute_plan([{'id': name, 'tool': TOOL, 'fresh_revision': False,
        'args': {'event_instance_id': event_id, 'expected_revision': frame['revision']}}], name)
    require(len(rows) == 1 and rows[0].get('id') == name and rows[0].get('ok') is True and
            not rows[0].get('error'), 'Original typed event query failed; never replay')
    row = rows[0]
    same_event_frame(client, frame, row['after_snapshot'])
    result, typed = row['result'], row['result'].get('current_event_window_context', {})
    require(result.get('accepted') is True and result.get('scope') == 'exact-current-event-window' and
            result.get('status') == 'available' and result.get('current_event_window_context_ready') is True and
            result.get('queried_revision') == frame['revision'] and
            result.get('queried_native_revision') == frame['native_revision'] and
            result.get('queried_snapshot_id') == frame['snapshot_id'] and
            typed.get('schema') == 'current-event-window-context-v1' and typed.get('status') == 'available' and
            typed.get('current_event_instance_id') == event_id and typed.get('date_raw') == frame['date_raw'] and
            typed.get('snapshot_revision') == frame['native_revision'] and
            isinstance(typed.get('event_definition_key'), str) and typed['event_definition_key'] and
            isinstance(typed.get('root_scope'), dict) and isinstance(typed.get('options'), list),
            'Qualified original typed event identity/presentation unavailable')
    # The selected frozen service normalizes every typed option; never fill a
    # missing option, invent enabled, select an option, or infer complete effects.
    return {'frame': frame, 'after_frame': row['after_snapshot'], 'typed_context': typed,
            'original_result': result, 'original_result_ref': pin(client.output / (name + '.actual-results.json')),
            'event_choice_actions': 0, 'school_choice_actions': 0,
            'complete_effect_preview_qualified': False}


def observe_until_event(client, data, initial, before):
    elapsed, intervals = 0, []
    for ordinal in range(1, data['maximum_natural_days'] + 1):
        require(elapsed + 24 <= data['maximum_natural_days'] * 24, 'Natural 90-day discovery cap exhausted')
        row = client.advance_day(days=1, timeout=data['one_day_timeout'], allow_event_boundary=True)
        if row['result'].get('event_boundary') is not None:
            elapsed, event_frame = validate_boundary(client, row, before, initial, elapsed, data['maximum_natural_days'])
            intervals.append({'step_id': row['id'], 'elapsed_hours': row['result']['elapsed_hours'],
                'date_raw': event_frame['date_raw'], 'interval_kind': 'event_boundary',
                'requested_interval_complete': row['result']['requested_interval_complete']})
            return {'status': 'PARTIAL_EVENT_CONTEXT_OBSERVED', 'event': discover_context(client, event_frame),
                    'natural_intervals': intervals, 'elapsed_natural_hours': elapsed}
        elapsed = natural.validate_day(row, before, initial, elapsed, data['maximum_natural_days'])
        before = natural.day_observation_frame(client, row)
        intervals.append({'step_id': row['id'], 'elapsed_hours': row['result']['elapsed_hours'],
            'date_raw': before['date_raw'], 'interval_kind': 'complete_natural_day',
            'requested_interval_complete': True})
    return {'status': 'NO_EVENT_OBSERVED', 'event': None, 'natural_intervals': intervals,
            'elapsed_natural_hours': elapsed}


def run_case(context, client):
    validate_contract(context)
    data = context['case_contract']
    seed = {k: context['saved_campaign'][k] for k in ('save', 'bytes', 'sha256', 'player_id', 'date_raw')}
    origin = natural.validate_origin(natural.base._checked_json(context['case_inputs']['origin_metadata']), seed, data)
    client.retain_process()
    initial = client.snapshot()
    require(initial['played_character']['character_id'] == data['saved_campaign']['player_id'] and
            initial['date_raw'] == data['saved_campaign']['date_raw'], 'Initial actor/date differs from original0240')
    _, frame = natural._call(client, 'i4-event-open-decisions', 'ck3_open_ingame_decisions_v1',
        {'expected_revision': initial['revision']}, initial)
    selected, _ = natural._call(client, 'i4-event-select-school-detail', 'ck3_select_ingame_decision_item_v1',
        {'decision_key': data['decision_key'], 'expected_revision': frame['revision']}, frame)
    first = natural.observe_decision(client, data, 0)
    selected_proof = natural.validate_selected(selected, frame, first, data['decision_key'])
    require(first['confirm_enabled'] is False, 'Initially enabled school decision cannot qualify this observation')
    saved, after_save = natural._call(client, 'i4-event-initial-save-once', 'ck3_save_checkpoint',
        {'expected_revision': first['frame']['revision']}, first['frame'])
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Initial actual SAVE not accepted')
    initial_saved = natural.read_saved(context, saved['checkpoint'], initial['date_raw'], data, True)
    client.checkpoint('i4-event-origin', {'origin': origin, 'initial_frame': initial, 'initial_saved': initial_saved,
        'initial_confirm_enabled': False, 'selection_proof': selected_proof,
        'origin_metadata': context['case_inputs']['origin_metadata'], 'source_inventory': context['case_inputs']['product_inventory']})
    observation = observe_until_event(client, data, initial, after_save)
    facts = {'schema': 'ck3-mod-acceptance-i4-natural-event-discovery-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'scope': data['scope'], **observation,
        'case_contract_qualified': True, 'gui_contract_qualified': observation['event'] is not None,
        'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False,
        'initial_saved': initial_saved, 'event_choice_actions': 0, 'school_choice_actions': 0,
        'normal_close_pending': True, 'expiry_observed': None, 'formal_I3b': None, 'C3': None, 'I4_complete': None,
        'cold_reload': None, 'fresh_full_365_cycle': None}
    client.checkpoint(RESULT, facts)
    return facts  # Shared entry now requests normal GUI Quit; no further simulation.


def verify_case(context):
    validate_contract(context)
    path = Path(context['output']) / (RESULT + '.json')
    if not path.is_file():
        return {'status': 'NOT_RUN_OR_PRESERVED_FAILURE', 'case_contract_qualified': False,
            'gui_contract_qualified': False, 'business_contract_applicable': False, 'business_pass': False,
            'product_release_pass': False}
    facts = natural.base.read_json(path)
    require(all(facts[k] == context[k] for k in ('run_id', 'product', 'case')) and
            facts['status'] in ('PARTIAL_EVENT_CONTEXT_OBSERVED', 'NO_EVENT_OBSERVED') and
            facts['event_choice_actions'] == facts['school_choice_actions'] == 0 and
            facts['business_pass'] is False and facts['business_contract_applicable'] is False and
            all(facts[k] is None for k in ('expiry_observed', 'formal_I3b', 'C3', 'I4_complete',
                                         'cold_reload', 'fresh_full_365_cycle')),
            'Discovery result crossed case or gained unsupported business credit')
    if facts['status'] == 'PARTIAL_EVENT_CONTEXT_OBSERVED':
        reference = facts['event']['original_result_ref']
        packet = natural.base._checked_json(reference)
        require(len(packet['rows']) == 1 and packet['rows'][0]['result'] == facts['event']['original_result'],
                'Original typed event result pin differs')
    else:
        require(facts['event'] is None and len(facts['natural_intervals']) == 90,
                'NO_EVENT requires the bounded 90 actual natural observations')
    return {**facts, 'verification_scope': 'Discovery only; shared normal close independently mandatory'}
