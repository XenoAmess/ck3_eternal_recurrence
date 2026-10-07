"""Exact paused checkpoint bookkeeping transition; no game or save body reads."""
from copy import deepcopy
import json
from pathlib import Path
import sdk_checkpoint_qualification as strict

SCHEMA = 'lyd.sdk-checkpoint-transition.v2'
DIAGNOSTIC_CHANGE_PATHS = frozenset({
    'last_heartbeat.main_thread_query_mailbox_v1.consecutive_verified',
    'last_heartbeat.main_thread_query_mailbox_v1.owner_verified_pump_epochs',
    'last_heartbeat.main_thread_query_mailbox_v1.pump_epochs',
    'last_heartbeat.monotonic_ms',
    'last_heartbeat.sequence',
    'last_heartbeat.snapshot_observer_12002.completed_ms',
    'last_heartbeat.snapshot_observer_12002.started_ms',
})
SNAPSHOT_BOOKKEEPING_KEYS = frozenset({
    'snapshot_id', 'revision', 'native_revision',
    'last_checkpoint_submission', 'native_command_history', 'diagnostics',
})

def same_json(left, right):
    return json.dumps(left, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(right, sort_keys=True, separators=(',', ':'), allow_nan=False)

def changed_paths(left, right, path=''):
    if type(left) is dict and type(right) is dict:
        result = []
        for key in sorted(left.keys() | right.keys()):
            current = path + '.' + key if path else key
            if key not in left or key not in right:
                result.append(current)
            else:
                result.extend(changed_paths(left[key], right[key], current))
        return result
    return [] if same_json(left, right) else [path]

def checkpoint_played_character_business(snapshot, binding):
    """Compare every business member; bind available query metadata to its own frame."""
    actor = deepcopy(snapshot['played_character'])
    membership = actor.get('event_trait_membership') if type(actor) is dict else None
    if type(membership) is dict and membership.get('status') == 'available':
        strict.exact(membership, {'schema', 'game_version', 'executable_sha256', 'status',
            'snapshot_revision', 'date_raw', 'played_character_id', 'traits', 'unavailable_reason'},
            'checkpoint available event trait membership')
        strict.need(membership['schema'] == 'xar.ck3.player-event-trait-membership/v1',
            'checkpoint event trait membership schema differs')
        for key, expected in (('snapshot_revision', binding['native_revision']),
                ('date_raw', binding['date_raw']), ('played_character_id', binding['played_character_id'])):
            strict.need(type(membership[key]) is int and membership[key] == expected,
                'checkpoint event trait membership frame differs ' + key)
        # This private comparison copy alone replaces the already-bound frame revision.
        # The receipt and returned original snapshots are never changed.
        membership['snapshot_revision'] = None
    return actor

def bind_checkpoint_transition(receipt, provenance):
    """Bind queries to the actual post-save frame without rewriting either frame."""
    need = strict.need
    strict.outer_identity(receipt, provenance)
    need(receipt.get('status') == 'native_gameplay_postcondition_verified' and receipt.get('uses_ocr') is False and receipt.get('uses_desktop_input') is False, 'checkpoint SDK postcondition missing')
    before, after = receipt.get('snapshot_before'), receipt.get('snapshot_after')
    prior, later = strict.frame_binding(before), strict.frame_binding(after)
    need(set(before) == set(after), 'checkpoint snapshot keys changed')
    for key in ('date_raw', 'game_pid', 'connection_generation', 'played_character_id'):
        need(type(prior[key]) is type(later[key]) and prior[key] == later[key], 'checkpoint transition identity changed ' + key)
    need(later['game_pid'] == provenance['game_pid'] and later['connection_generation'] == provenance['connection_generation'], 'checkpoint transition provenance PID/connection differs')
    need(later['revision'] == prior['revision'] + 1 and later['native_revision'] == prior['native_revision'] + 1, 'checkpoint transition must publish exactly one public/native revision')
    for frame in (prior, later):
        need(frame['snapshot_id'] == 'native:' + str(frame['native_revision']), 'checkpoint native snapshot identity differs')
    for key in sorted(set(before) - SNAPSHOT_BOOKKEEPING_KEYS):
        left, right = before[key], after[key]
        if key == 'played_character':
            left = checkpoint_played_character_business(before, prior)
            right = checkpoint_played_character_business(after, later)
        need(same_json(left, right), 'checkpoint business field changed ' + key)

    diag_before, diag_after = before['diagnostics'], after['diagnostics']
    diagnostic_changes = changed_paths(diag_before, diag_after)
    need(set(diagnostic_changes) <= DIAGNOSTIC_CHANGE_PATHS, 'checkpoint diagnostics changed outside whitelist: ' + ','.join(sorted(set(diagnostic_changes) - DIAGNOSTIC_CHANGE_PATHS)))
    for diag in (diag_before, diag_after):
        hello = diag['hello']
        need(diag.get('pipe_name') == provenance['pipe_name'] and diag.get('bridge_pid') == provenance['game_pid'] and hello.get('pid') == provenance['game_pid'], 'checkpoint diagnostic PID/pipe differs')

    result = receipt.get('result')
    need(type(result) is dict and result.get('step') == 'save-checkpoint' and result.get('accepted') is True and result.get('status') == 'submitted' and result.get('backend_id') == before.get('backend_id') == after.get('backend_id') == 'native-headless', 'exact one accepted native save result required')
    submission = strict.exact(result.get('submission'), {'sequence', 'requested_save_name', 'date_raw'}, 'checkpoint save submission')
    strict.positive(submission['sequence'], 'save submission sequence')
    need(type(submission['requested_save_name']) is str and submission['requested_save_name'] == 'xar_checkpoint' and submission['date_raw'] == prior['date_raw'], 'checkpoint submission name/date differs')
    previous_submission = before['last_checkpoint_submission']
    previous_sequence = 0
    if previous_submission is not None:
        strict.exact(previous_submission, {'sequence', 'requested_save_name', 'date_raw', 'status'}, 'prior checkpoint submission')
        strict.positive(previous_submission['sequence'], 'prior save sequence')
        need(previous_submission['status'] == 'submitted', 'prior save submission status')
        previous_sequence = previous_submission['sequence']
    need(submission['sequence'] == previous_sequence + 1, 'checkpoint save sequence is not exactly next')
    expected_submission = {**submission, 'status': 'submitted'}
    need(same_json(after['last_checkpoint_submission'], expected_submission), 'post-save last_checkpoint_submission does not match exact result')

    checkpoint = result.get('checkpoint')
    need(type(checkpoint) is dict and checkpoint.get('status') == 'saved' and type(checkpoint.get('path')) is str and Path(checkpoint['path']).is_absolute() and type(checkpoint.get('size')) is int and checkpoint['size'] > 0 and strict.valid_sha(checkpoint.get('sha256')) and checkpoint.get('date_raw') == prior['date_raw'], 'exact materialized checkpoint descriptor required')
    need(checkpoint.get('strategy') == 'native-autosave-command-v1' and checkpoint.get('name') == Path(checkpoint['path']).name == submission['requested_save_name'] + '.ck3', 'checkpoint strategy/path/name differs')
    materialization = result.get('materialization')
    need(type(materialization) is dict and materialization.get('available') is True and type(materialization.get('save_dir')) is str and Path(materialization['save_dir']) == Path(checkpoint['path']).parent, 'checkpoint isolated materialization directory differs')
    old_history, new_history = before['native_command_history'], after['native_command_history']
    need(type(old_history) is list and type(new_history) is list and len(new_history) == len(old_history) + 1 and same_json(new_history[:-1], old_history), 'checkpoint requires exactly one appended command with unchanged history prefix')
    command = strict.exact(new_history[-1], {'index', 'command', 'ok', 'result'}, 'single checkpoint command')
    need(type(command['index']) is int and command['index'] == checkpoint.get('history_index') == len(old_history) + 1 and command['command'] == 'save-checkpoint' and command['ok'] is True and same_json(command['result'], result), 'checkpoint appended command does not exactly match save result')

    transition = {'schema': SCHEMA, 'before_binding': deepcopy(prior), 'after_binding': deepcopy(later),
        'snapshot_before_original': deepcopy(before), 'snapshot_after_original': deepcopy(after),
        'submission_sequence': submission['sequence'], 'command_history_index': command['index'],
        'diagnostic_changed_paths': diagnostic_changes,
        'qualification': 'EXACT_CHECKPOINT_BOOKKEEPING_TRANSITION_OBSERVED',
        'business_fields_unchanged': True, 'raw_snapshot_rewritten': False,
        'actual_pass': None, 'formal_mandate_credit': None}
    return later, transition
