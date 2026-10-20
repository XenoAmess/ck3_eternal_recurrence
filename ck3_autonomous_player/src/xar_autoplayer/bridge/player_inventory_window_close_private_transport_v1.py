"""Typed current-player inventory Close, with its own once ledger and post proof."""
from __future__ import annotations
from collections.abc import Mapping
import uuid
from . import faith_observers_private_transport_v1 as R
from . import player_inventory_window_private_transport_v1 as I
from .driver import BridgeUnavailableError, UnsupportedStepError
from .g2_private_query_transport import private_g2_query_snapshot_v1, private_g2_query_metadata_v1
from .nonwar_private_build import private_native_provenance
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

PERMISSION = 'allow_private_player_inventory_window_close'
QUERY = 'query-player-inventory-window-close-v1-private'
CLOSE = 'close-player-inventory-window-v1-private'
POST = 'query-player-inventory-window-close-post-v1-private'
DOMAIN = 'player_inventory_window_close_v1'
KEY = 'player_inventory_window_close'
BODY_FIELDS = frozenset('''schema game_version executable_sha256 operation read_only available unavailable_reason
    loaded_code_pins_verified loaded_gui_sources_verified current intent_sequence intent_found once_intent_consumed
    invoked call_returned needs_recovery desired_window_observed status before after artifact_equipped_observed
    actor_aggregate_observed personal_net_effect_attributed business_outcome_observed automatic_retry'''.split())
POST_STATUSES = frozenset({'inventory_intent_pending_or_unknown', 'inventory_window_closed_observed',
    'inventory_intent_previously_resolved_current_window_not_observed'})


def _frame(driver, expected_revision):
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError('Inventory Close query/once/post permission is independently default OFF')
    R.integer(expected_revision, 'public revision', 1, 2**64-1)
    digest = I._source_inventory(driver)
    before = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
    binding = R.owner(before)
    actor = before.get('played_character', {})
    R.need(before.get('revision') == expected_revision and before.get('paused') is True and
        before.get('map_ready') is True and actor.get('alive') is True,
        'Inventory Close operation needs the current living paused player')
    R.integer(before.get('native_revision'), 'native revision', 1, 2**64-1)
    R.integer(before.get('date_raw'), 'actual native date', 0)
    R.integer(actor.get('character_id'), 'current full actor', 1, 2**32-2)
    return before, binding, (binding[1], actor['character_id']), digest


def _pending(driver):
    # Same mutex as Open makes opposite-operation admission atomic. Dictionaries
    # and native ledgers remain independent, including after reconnection.
    with I._LOCK:
        if not hasattr(driver, '_player_inventory_window_close_client_pending_v1'):
            driver._player_inventory_window_close_client_pending_v1 = {}
        return driver._player_inventory_window_close_client_pending_v1


def normalize_player_inventory_window_close_v1(value, *, snapshot, operation, expected_intent_sequence=None):
    R.need(operation in ('query', 'close', 'post'), 'Unknown inventory Close operation')
    r = R.shape(value, ' '.join(BODY_FIELDS), 'inventory Close result')
    R.need(r['schema'] == 'ck3_12004_player_inventory_window_close_v1' and
        require_exact_native_build(r['game_version'], r['executable_sha256']) == CK3_12004,
        'Inventory Close schema/build differs')
    R.availability(r, 'inventory Close result')
    R.need(r['operation'] == operation and r['read_only'] is (operation != 'close'),
        'Inventory Close operation/read-only role differs')
    binding = R.owner(snapshot)
    for key in ('loaded_code_pins_verified', 'loaded_gui_sources_verified', 'intent_found',
                'once_intent_consumed', 'invoked', 'call_returned', 'needs_recovery', 'desired_window_observed'):
        R.boolean(r[key], key)
    for key in ('artifact_equipped_observed', 'actor_aggregate_observed', 'personal_net_effect_attributed',
                'business_outcome_observed', 'automatic_retry'):
        R.need(r[key] is False, 'Inventory Close invented equip/aggregate/business/retry credit: ' + key)
    R.failure(r['status'], 'inventory Close status')
    R.integer(r['intent_sequence'], 'actual original Close intent', 0, 2**64-1)
    R.need(r['intent_found'] is (r['intent_sequence'] > 0), 'Close intent presence/sequence differ')
    R.need(not r['once_intent_consumed'] or r['intent_found'], 'Consumed Close intent was not retained')
    R.need(not r['invoked'] or r['once_intent_consumed'], 'Close invocation lacks a native once claim')
    R.need(not r['call_returned'] or r['invoked'], 'Close call return lacks invocation')
    current = I._view(r['current'], snapshot=snapshot, binding=binding)
    if r['available']:
        R.need(current['available'] and r['loaded_code_pins_verified'] and r['loaded_gui_sources_verified'],
            'Available Close result lacks current read/code/GUI source admission')
    else:
        R.need(current['available'] is False, 'Outer Close admission failure retained current facts')
    before, after = r['before'], r['after']
    if before is not None:
        I._view(before, snapshot=snapshot, binding=binding, historical=operation != 'close')
    if after is not None:
        I._view(after, snapshot=snapshot, binding=binding)
        R.need(operation == 'post' and after == current, 'Close post after must be the actual current VIEW')
    if operation == 'query':
        R.need(after is None and r['desired_window_observed'] is False, 'Close query cannot resolve an intent')
        R.need(r['status'] == ('inventory_window_observed' if r['available'] else 'inventory_window_unavailable'),
            'Inventory Close query status differs')
    elif operation == 'close':
        R.need(after is None and r['desired_window_observed'] is False, 'Close ACK cannot prove hidden state')
        R.need(r['intent_found'] is r['once_intent_consumed'], 'Close may retain only this ticket once claim')
        if r['once_intent_consumed']:
            R.need(r['needs_recovery'] is True, 'Close claim cannot self-resolve')
        if r['status'] == 'inventory_already_hidden_no_call':
            R.need(r['available'] and not r['once_intent_consumed'] and not r['invoked'] and
                not r['call_returned'] and not r['needs_recovery'] and
                current['native_visible'] is False and current['effective_visible'] is False,
                'Already-hidden no-call contradicted the actual current state')
    else:
        R.integer(expected_intent_sequence, 'exact original Close intent', 1, 2**64-1)
        R.need(r['intent_found'] is True and r['intent_sequence'] == expected_intent_sequence,
            'Close post must find the exact original intent; not-found has no body')
        R.need(r['status'] in POST_STATUSES, 'Inventory Close post status differs')
        R.need(r['desired_window_observed'] is (r['status'] == 'inventory_window_closed_observed') and
            r['needs_recovery'] is (r['status'] == 'inventory_intent_pending_or_unknown'),
            'Close post current proof and historical ledger status differ')
        if r['status'] == 'inventory_intent_previously_resolved_current_window_not_observed':
            R.need(r['available'] and r['once_intent_consumed'] and after is not None,
                'Historical Close resolution cannot replace a valid fresh owner frame')
    if r['once_intent_consumed']:
        R.need(before is not None and before['available'] and
            all(before[key] is True for key in I._STATES),
            'Consumed Close intent lacks its actual visible current-player inventory witness')
    if r['desired_window_observed']:
        R.need(operation == 'post' and r['available'] and r['once_intent_consumed'] and
            before is not None and after is not None and before['available'] and after['available'] and
            after['capture_epoch'] > before['capture_epoch'] and
            after['connection_generation'] == before['connection_generation'] and
            after['game_pid'] == before['game_pid'] and
            after['played_character_id'] == before['played_character_id'] and
            after['native_revision'] >= before['native_revision'] and after['date_raw'] >= before['date_raw'] and
            after['window_present'] is True and after['current_player_selected'] is True and
            after['native_visible'] is False and after['effective_visible'] is False,
            'Closed inventory lacks actual independent later current-player native/effective hidden proof')
    return r


def _exchange(driver, before, binding, digest, *, operation, expected_intent_sequence=None):
    step = {'query': QUERY, 'close': CLOSE, 'post': POST}[operation]
    request_id = 'inventory-close-' + operation + '-' + uuid.uuid4().hex
    request = {'type': 'execute_step', 'protocol_version': 1, 'request_id': request_id, 'step': step,
        'expected_revision': before['native_revision'], 'expected_snapshot_revision': before['native_revision'],
        'expected_date_raw': before['date_raw'], 'expected_actor_character_id': before['played_character']['character_id'],
        'expected_game_pid': binding[1], 'expected_connection_generation': binding[2], 'source_inventory_sha256': digest}
    if operation == 'post':
        request['expected_intent_sequence'] = expected_intent_sequence
    driver.endpoint.send(request)
    packet = driver.state.wait_for_command_result(request_id, 30.0)
    try:
        R.need(isinstance(packet, Mapping) and packet.get('type') == 'command_result' and
            type(packet.get('protocol_version')) is int and packet['protocol_version'] == 1 and
            packet.get('request_id') == request_id and packet.get('ok') is True,
            'Close response RED/unknown; retain the original intent, never replay')
        e = packet.get('result')
        R.need(type(e) is dict and e.get('step') == step and e.get('accepted') is True and
            e.get('private_build') is True and e.get('advertised') is False and
            e.get('read_only') is (operation != 'close') and e.get('domain_key') == DOMAIN and
            require_exact_native_backend(e.get('game_version'), e.get('executable_sha256'), e.get('backend_id'),
                suffix='player-inventory-window-close-v1-private') == CK3_12004 and
            type(e.get('snapshot_revision')) is int and e['snapshot_revision'] == before['native_revision'] and
            type(e.get('date_raw')) is int and e['date_raw'] == before['date_raw'] and
            type(e.get('game_pid')) is int and e['game_pid'] == binding[1] and
            type(e.get('connection_generation')) is int and e['connection_generation'] == binding[2],
            'Close response crossed actual build/process/generation/request frame')
        value = normalize_player_inventory_window_close_v1(e.get(KEY), snapshot=before, operation=operation,
            expected_intent_sequence=expected_intent_sequence)
        R.need(e.get('status') == ('observed' if value['available'] else 'unavailable'),
            'Inventory Close envelope availability differs')
        after = private_g2_query_snapshot_v1(driver, include_native_command_history=False)
        after_binding = R.owner(after)
        if operation != 'close':
            R.need(after_binding == binding, 'Close read crossed its exact current frame')
        else:
            R.need(after_binding[1:] == binding[1:] and
                after['played_character']['character_id'] == before['played_character']['character_id'] and
                after.get('paused') is True and after.get('map_ready') is True and
                after['played_character'].get('alive') is True and after['date_raw'] >= before['date_raw'],
                'Closing lost the original process/player frame')
    except (ValueError, KeyError, TypeError) as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        'backend_id': e['backend_id'], 'domain_key': DOMAIN, 'snapshot_revision': before['native_revision'],
        'client_source_inventory_sha256': digest, 'advertised': False, 'post_snapshot_id': after.get('snapshot_id')}


def query_player_inventory_window_close_private_v1(driver, *, expected_revision):
    before, binding, key, digest = _frame(driver, expected_revision)
    value = _exchange(driver, before, binding, digest, operation='query')
    pending = _pending(driver)
    with I._LOCK:
        # Latest retained native intent is only a recovery candidate. Without
        # this call's ACK sequence it might belong to older history; it cannot
        # be bound to, or resolve, the local unknown submission.
        value['client_replay_blocked'] = key in pending
    return value


def close_player_inventory_window_private_v1(driver, *, expected_revision):
    before, binding, key, digest = _frame(driver, expected_revision)
    pending, opening = _pending(driver), I._pending(driver)
    intent = {'intent_sequence': None}
    with I._LOCK:
        if key in opening:
            raise BridgeUnavailableError('Prior inventory opening remains unknown; resolve its exact Open intent before closing')
        if key in pending:
            raise BridgeUnavailableError('Prior Close remains unknown; use its exact independent post, never replay')
        pending[key] = intent
    value = _exchange(driver, before, binding, digest, operation='close')
    with I._LOCK:
        if pending.get(key) is intent:
            intent['intent_sequence'] = value['intent_sequence'] or None
            if (not value['once_intent_consumed'] and not value['invoked'] and not value['needs_recovery'] and
                    value['status'] != 'inventory_close_pending_or_once_intent_rejected'):
                del pending[key]
        value['client_replay_blocked'] = key in pending
    return value


def query_player_inventory_window_close_post_private_v1(driver, *, expected_revision, expected_intent_sequence):
    R.integer(expected_intent_sequence, 'exact original Close intent', 1, 2**64-1)
    before, binding, key, digest = _frame(driver, expected_revision)
    pending = _pending(driver)
    with I._LOCK:
        intent = pending.get(key)
        if intent is not None:
            R.need(intent['intent_sequence'] in (None, expected_intent_sequence), 'Post changed the retained Close intent')
    value = _exchange(driver, before, binding, digest, operation='post', expected_intent_sequence=expected_intent_sequence)
    with I._LOCK:
        if (value['desired_window_observed'] and intent is not None and pending.get(key) is intent and
                intent['intent_sequence'] == expected_intent_sequence):
            del pending[key]
        value['client_replay_blocked'] = key in pending
    return value
