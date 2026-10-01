"""Submit one original day with an observer confined to the daily window."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_daily_window', ROOT / 'scoped_ui_research_a08.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
bindings = ROOT / 'current-run-bindings.json'
cfg = m.read(bindings)
live, output, evidence, transport, steps = m.bind(cfg)
m.require(not (evidence / 'one-day-intent.json').exists(), 'Day already submitted; never retry')
m.require(not (evidence / 'variable-monitor-begin-intent.json').exists(), 'Monitor already submitted; never retry')
review = m.read(evidence / 'before-ui-root-review.json')
m.require(review['original_pixels_actually_reviewed'] is True, 'Actual original pixel inspection required')
for img in review['reviewed_images']:
    m.require(m.identity(img['path']) == img, 'Reviewed original bytes changed')
pair_path = evidence / 'before-saved-pair.json'
pair = m.read(pair_path)
save = pair['save_body']
submission, checkpoint = save['submission'], save['checkpoint']
sequence = submission['sequence']
m.require(type(sequence) is int and sequence > 0 and save['accepted'] is True and checkpoint['status'] == 'saved' and save['materialization']['available'] is True, 'Actual materialized checkpoint required')
m.require(submission['date_raw'] == checkpoint['date_raw'] == cfg['before_date_raw'] and checkpoint['episode_run_id'] == cfg['native_session_binding']['episode_run_id'], 'Wrong current checkpoint')
m.require(m.identity(pair['immutable']['path']) == pair['immutable'] and m.identity(checkpoint['path'])['sha256'] == pair['immutable']['sha256'], 'Current materialized and immutable checkpoint differ')
start, sr, values = m.snapshot(output, transport, steps, 'scoped-a12-day-source', cfg['before_date_raw'])
m.require(values == review['source_values'], 'Current post-save source differs from reviewed source')
token = cfg['managed_daily_sequence_token']
monitor_token = cfg['monitor_sequence_token']
m.require(type(token) is int and type(monitor_token) is int and 0 < token < 2**64 and 0 < monitor_token < 2**64 and token != monitor_token, 'Independent unique tokens required')

def monitor(begin, current_values, current_snapshot):
    label = 'variable-monitor-begin' if begin else 'variable-monitor-finish'
    m.require(not (evidence / (label + '-intent.json')).exists(), 'Monitor intent already exists; never retry')
    params = {'action': 'private_phase_trace', 'step': 'experimental-scoped-character-variable-monitor-' + ('begin' if begin else 'finish') + '-v1', 'expected_revision': current_values['revision'], 'monitor_sequence_token': monitor_token}
    if begin:
        params.update(scoped_character_id=cfg['victim_id'], scoped_related_character_id=cfg['killer_id'])
    m.write(evidence / (label + '-intent.json'), {'at_utc': datetime.now(timezone.utc).isoformat(), 'source_binding': m.identity(bindings), 'source_snapshot': current_snapshot, 'source_values': current_values, 'request_parameters': params, 'window': 'Immediately before and after one original day; after all beforeUI and before all afterUI', 'no_gameplay_write': True})
    body, receipt = steps.private_call(output, label + '-once', params, 120)
    path, payload = m.monitor_payload(body)
    # Preserve the exact original published payload before evaluating its flags.
    valid = body.get('accepted') is True and body.get('status') == ('armed' if begin else 'drained') and payload.get('failure_flags') == 0 and payload.get('truncated') is False
    m.write(evidence / (label + '.json'), {'source_binding': m.identity(bindings), 'source_snapshot': current_snapshot, 'source_values': current_values, 'native_receipt': receipt, 'native_envelope': body, 'exact_payload_path': path, 'scoped_variable_monitor': payload, 'status': ('ARMED_IMMEDIATELY_BEFORE_DAY' if begin else 'DRAINED_BEFORE_AFTER_UI_PENDING_INDEPENDENT_SEMANTIC_VERIFICATION') if valid else 'NATIVE_RED_PRESERVED', 'human_movie_signoff': False})
    expected = {'schema_version': 1, 'monitor_sequence_token': monitor_token, 'character_ids': [cfg['victim_id'], cfg['killer_id']], 'begin_date_raw': cfg['before_date_raw'], 'whole_game_mutable_bundle_complete': False, 'battle_event_causality_inferred_from_endpoint': False}
    for key, wanted in expected.items():
        m.require(type(payload.get(key)) is type(wanted) and payload.get(key) == wanted, 'Monitor binding differs: ' + key)
    m.require(payload.get('detours_uninstalled') is (not begin), 'Monitor lifecycle differs')
    m.require(valid and all(row.get('failure_flags') == 0 for row in payload['records']), 'Original monitor RED; exact return retained')
    return receipt

monitor(True, values, sr)
params = {'action': 'private_phase_trace', 'step': 'experimental-combat-phase-event-trace-begin-v1', 'expected_revision': values['revision'], 'combat_id': cfg['combat_id'], 'managed_daily_sequence_token': token, 'checkpoint_sequence': sequence, 'capture_runtime_scoped_chain': True, 'scoped_character_id': cfg['victim_id'], 'scoped_related_character_id': cfg['killer_id'], 'scoped_event_load_index': cfg['event_load_index']}
m.write(evidence / 'actual-checkpoint-trace-begin-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'consumer': m.identity(Path(__file__)), 'actual_saved_pair': m.identity(pair_path), 'actual_checkpoint_sequence': sequence, 'parameters': params, 'game_day_not_yet_submitted': True})
begun, br = steps.private_call(output, 'scoped-a12-chain-begin', params, 120)
m.require(begun.get('accepted') is True and begun.get('managed_daily_sequence_token') == token, 'Daily trace refused; no game day')
m.write(evidence / 'one-day-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'source_values': values, 'source_snapshot': sr, 'token': token, 'trace_begin': br, 'trace_begin_body': begun, 'actual_checkpoint_sequence': sequence, 'advance_consumer': m.identity(Path(__file__)), 'at_most_one_day': True})
changed, dr = transport.call(output, 'scoped-a12-one-day', 'ck3_execute_step', {'step': 'life-advance', 'expected_revision': values['revision']}, 150)
m.require(changed.get('starting_date_raw') == cfg['before_date_raw'] and changed.get('ending_date_raw') == cfg['after_date_raw'] and changed.get('elapsed_days') == 1 and changed.get('requested_days') == 1 and changed.get('progress_status') == 'postcondition', 'Submitted day ambiguous; never retry')
end, er, ev = m.snapshot(output, transport, steps, 'scoped-a12-post-day-snapshot-only', cfg['after_date_raw'])
finished = None
trace_error = None
trace_label = 'scoped-a12-chain-finish-once'
try:
    finished, tr = steps.private_call(output, trace_label, {'action': 'private_phase_trace', 'step': 'experimental-combat-phase-event-trace-finish-v1', 'expected_revision': ev['revision'], 'combat_id': cfg['combat_id'], 'managed_daily_sequence_token': token}, 120)
except Exception as error:
    trace_error = {'type': type(error).__name__, 'message': str(error)}
    request_path = output / 'interactive-requests' / (trace_label + '.json')
    response_path = output / 'interactive-requests-responses' / (trace_label + '.json')
    tr = {'request': m.identity(request_path), 'response': m.identity(response_path) if response_path.is_file() else None, 'result': 'RED', 'error': trace_error}
m.write(evidence / 'one-day-finished.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'one_day': dr, 'one_day_body': changed, 'post_day_snapshot': er, 'post_day_values': ev, 'trace_finish': tr, 'trace_finish_body': finished, 'trace_error': trace_error, 'day_postcondition_verified': True, 'source_binding': m.identity(bindings), 'advance_consumer': m.identity(Path(__file__)), 'complete_causal_chain': 'pending independent original records and save verification', 'trace_retry_or_extra_day': False})
# Drain before any next-day role page can create repeated dead/null getter reads.
monitor(False, ev, er)
print(json.dumps({'result': 'ONE_ORIGINAL_DAY_OBSERVER_DRAINED_BEFORE_AFTER_UI', 'actual_checkpoint_sequence': sequence, 'trace_export_returned': finished is not None, 'trace_error': trace_error, 'values': ev}))
