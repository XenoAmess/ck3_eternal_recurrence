"""Finish the actual submitted day; never resubmit life-advance."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import importlib.util
import json
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_finish_actual_day', ROOT / 'scoped_ui_research_a09.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
bindings = ROOT / 'current-run-bindings.json'
cfg = m.read(bindings)
live, output, evidence, transport, steps = m.bind(cfg)
day_path = output / 'interactive-requests-responses/scoped-a12-one-day.json'
day = m.read(day_path)
changed = day['body']
m.require(day['result'] == 'CALL_COMPLETED' and changed['starting_date_raw'] == cfg['before_date_raw'] and changed['ending_date_raw'] == cfg['after_date_raw'] and changed['elapsed_days'] == 1 and changed['requested_horizon_days'] == 1 and changed['progress_status'] == 'postcondition' and changed['paused'] is True, 'Actual single-day postcondition not proven')
m.require((evidence / 'one-day-intent.json').is_file() and not (evidence / 'one-day-finished.json').exists(), 'Original day intent or finish state differs')
trace_label = 'scoped-a12-chain-finish-once'
m.require(not (output / 'interactive-requests' / (trace_label + '.json')).exists() and not (evidence / 'variable-monitor-finish-intent.json').exists(), 'A finish has already been submitted; never retry')
begun = m.read(evidence / 'variable-monitor-begin.json')
m.require(begun['native_envelope']['accepted'] is True and begun['scoped_variable_monitor']['detours_uninstalled'] is False, 'Monitor was not armed')
token, monitor_token = cfg['managed_daily_sequence_token'], cfg['monitor_sequence_token']
dr = {'request': m.identity(output / 'interactive-requests/scoped-a12-one-day.json'), 'response': m.identity(day_path), 'result': day['result'], 'error': day.get('error')}
end, er, ev = m.snapshot(output, transport, steps, 'scoped-a14-post-day-snapshot-only', cfg['after_date_raw'])
m.write(evidence / 'actual-submitted-day-finish-continuation-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'consumer': m.identity(Path(__file__)), 'original_day_response': m.identity(day_path), 'cause': 'Caller checked requested_days; original composite return actually uses requested_horizon_days. Actual date/elapsed/postcondition independently verified.', 'no_life_advance_in_this_consumer': True, 'post_day_snapshot': er, 'post_day_values': ev})
finished, trace_error = None, None
try:
    finished, tr = steps.private_call(output, trace_label, {'action': 'private_phase_trace', 'step': 'experimental-combat-phase-event-trace-finish-v1', 'expected_revision': ev['revision'], 'combat_id': cfg['combat_id'], 'managed_daily_sequence_token': token}, 120)
except Exception as error:
    trace_error = {'type': type(error).__name__, 'message': str(error)}
    request_path = output / 'interactive-requests' / (trace_label + '.json')
    response_path = output / 'interactive-requests-responses' / (trace_label + '.json')
    tr = {'request': m.identity(request_path), 'response': m.identity(response_path) if response_path.is_file() else None, 'result': 'RED', 'error': trace_error}
m.write(evidence / 'one-day-finished.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'one_day': dr, 'one_day_body': changed, 'post_day_snapshot': er, 'post_day_values': ev, 'trace_finish': tr, 'trace_finish_body': finished, 'trace_error': trace_error, 'day_postcondition_verified': True, 'source_binding': m.identity(bindings), 'advance_consumer': m.identity(ROOT / 'advance_and_drain_immediately_a13.py'), 'finish_continuation': m.identity(Path(__file__)), 'complete_causal_chain': 'pending independent original records and save verification', 'trace_retry_or_extra_day': False})
# Reuse only the already-bound monitor function definition, never the day program.
source = ROOT / 'advance_and_drain_immediately_a13.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'monitor']
m.require(len(functions) == 1, 'One exact monitor function required')
exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), globals())
monitor(False, ev, er)
print(json.dumps({'result': 'ACTUAL_ONE_DAY_FINISHED_MONITOR_DRAINED_BEFORE_AFTER_UI', 'trace_export_returned': finished is not None, 'trace_error': trace_error, 'values': ev}))
