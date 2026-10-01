"""Drain the independent passive observer and finish the failed owner attempt once."""
from pathlib import Path
import hashlib
import importlib.util
import json
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def main():
    helper = ROOT / 'scoped_ui_research_a05.py'
    with helper.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    require(digest == 'BF88D05E946233993F64F5F3275C11A20AE1297105F4194A0699586F45E90A6E', 'Controller changed')
    spec = importlib.util.spec_from_file_location('_failed_ui_cleanup', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bindings = ROOT / 'current-run-bindings.json'
    config = module.read(bindings)
    bound = module.bind(config)
    live, output, evidence, transport, steps = bound
    require((evidence / 'variable-monitor-begin.json').is_file(), 'No independent observer armed')
    require(not (evidence / 'one-day-intent.json').exists(), 'A day attempt exists; requires different cleanup analysis')
    require(not (evidence / 'variable-monitor-finish-intent.json').exists(), 'Normal finish already submitted')
    args = SimpleNamespace(bindings=bindings, label='failed-ui-owner-finish')
    result, error = None, None
    try:
        snapshot, receipt, values = module.snapshot(output, transport, steps, 'failed-ui-monitor-end-source', config['before_date_raw'])
        parameters = {'action': 'private_phase_trace', 'step': 'experimental-scoped-character-variable-monitor-finish-v1',
            'expected_revision': values['revision'], 'monitor_sequence_token': config['monitor_sequence_token']}
        module.write(evidence / 'failed-ui-monitor-end-intent.json', {'source_binding': module.identity(bindings),
            'source_values': values, 'source_snapshot': receipt, 'parameters': parameters,
            'normal_research_lifecycle_complete': False, 'reason': 'Original character action rejected; abandon this sampling attempt before any day advance'})
        body, native_receipt = steps.private_call(output, 'failed-ui-monitor-end-once', parameters, 120)
        path, payload = module.monitor_payload(body)
        result = {'source_binding': module.identity(bindings), 'source_values': values, 'native_envelope': body,
            'native_receipt': native_receipt, 'exact_payload_path': path, 'scoped_variable_monitor': payload,
            'normal_research_lifecycle_complete': False, 'research_status': 'RED_UI_ADMISSION_NO_DAY_ADVANCE',
            'day_advance_count': 0, 'human_movie_signoff': False}
        module.write(evidence / 'failed-ui-monitor-end.json', result)
        require(body.get('accepted') is True and body.get('status') == 'drained' and payload.get('detours_uninstalled') is True,
            'Passive observer did not confirm drain/uninstall; owned process cleanup remains mandatory')
    except BaseException as failure:
        error = repr(failure)
        module.write(evidence / 'failed-ui-monitor-end-error.json', {'error': error, 'retry_performed': False})
    finally:
        module.finish(args, config, bound)
        module.write(evidence / 'failed-ui-attempt-closure.json', {'status': 'RED_UI_ADMISSION_NO_DAY_ADVANCE',
            'failed_action_response': module.identity(output / 'interactive-requests-responses/before-victim-character-open.json'),
            'drain_preserved': result is not None, 'drain_error': error, 'day_advance_count': 0,
            'owner_finish_submitted_once': True, 'actual_process_cleanup': 'pending same-owner SDK completion',
            'video_changed': False, 'six_gap_evidence_closed': False})
    print(json.dumps({'attempt': 'RED_UI_ADMISSION_NO_DAY_ADVANCE', 'cleanup': 'OWNER_FINISH_SUBMITTED', 'monitor_drain_error': error}))

if __name__ == '__main__':
    main()
