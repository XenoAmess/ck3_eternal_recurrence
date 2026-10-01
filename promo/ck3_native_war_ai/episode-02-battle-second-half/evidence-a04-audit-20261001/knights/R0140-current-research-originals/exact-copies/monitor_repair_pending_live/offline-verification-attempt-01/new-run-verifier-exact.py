"""Verify original begin/finish monitor receipts against a same-run save projection.

Reads only existing local evidence. Creates a new output directory and exact
copies, never calls CK3, a provider, desktop, transport or network operations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.simulation.knight_variable_monitor_projection import validate_variable_monitor
from xar_autoplayer.simulation.knight_causal_save_projection import find_key_blocks, one


def identity(path: Path) -> dict:
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size, 'sha256': digest}


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path: Path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def payloads(value, path=None):
    path = [] if path is None else path
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'scoped_variable_monitor':
                result.append((path + [key], child))
            else:
                result.extend(payloads(child, path + [key]))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(payloads(child, path + [index]))
    return result


def saved_signature(character: dict):
    matches = []
    for variables in find_key_blocks(character['entries'], 'variables'):
        rows = one(variables['entries'], 'data')
        if rows is None:
            continue
        for row in rows:
            if not isinstance(row['value'], list):
                continue
            value = row['value']
            if one(value, 'flag') != '"signature_weapon"':
                continue
            data = one(value, 'data', required=True)
            if one(data, 'type', required=True) != 'flag':
                raise ValueError('saved signature_weapon is not a typed flag')
            flag = one(data, 'flag', required=True)
            matches.append({'native_name': flag.removeprefix('"').removesuffix('"'),
                            'saved_path': variables['path'], 'full_saved_variable': value})
    if len(matches) > 1:
        raise ValueError('multiple saved signature_weapon rows')
    return matches[0] if matches else None


def verify(args):
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    checks, copies = [], []
    report = {'schema': 'ck3.knight-variable-monitor-run-projection.v1', 'status': 'UNKNOWN',
              'checks': checks, 'exact_sources': copies, 'no_game_launch': True, 'desktop_inputs': 0,
              'master_intake': False, 'whole_game_mutable_bundle_complete': False,
              'sole_cause_proven': False}

    def gate(name, passed):
        checks.append({'name': name, 'pass': bool(passed)})
        if not passed:
            raise ValueError(name)

    def freeze(path: Path, label: str):
        original = identity(path)
        target = out / label
        with path.open('rb') as incoming, target.open('xb') as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        exact = identity(target)
        gate('exact copy ' + label, original['sha256'] == exact['sha256'] and original['bytes'] == exact['bytes'])
        copies.append({'original': original, 'exact_copy': exact})
        return original

    def bound(entry, label):
        path = Path(entry['path']).resolve()
        actual = identity(path)
        gate('declared original bytes ' + label, actual['bytes'] == entry['bytes'] and actual['sha256'] == entry['sha256'].upper())
        freeze(path, label)
        return path

    try:
        freeze(Path(__file__), 'monitor-verifier-exact.py')
        for module_name, name in [('xar_autoplayer.simulation.knight_variable_monitor_projection', 'pure-monitor-exact.py'),
                                  ('xar_autoplayer.simulation.knight_causal_save_projection', 'pure-save-exact.py'),
                                  ('xar_autoplayer.simulation.knight_selector_replay', 'pure-selector-exact.py')]:
            freeze(Path(sys.modules[module_name].__file__), name)
        projection = read(args.causal_projection)
        freeze(args.causal_projection, 'causal-projection-exact.json')
        gate('same-run full saved projection passed', projection['status'] == 'PASS_SAME_RUN_SELECTED_SAVED_BLOCKS_AND_ORIGINAL_TRACE' and
             projection['input_format'] == 'explicit_binding_identity_saved_pair_v1')
        binding_identity = projection['source_binding']['original']
        config_path = bound(binding_identity, 'binding-exact.json')
        config = read(config_path)
        characters = [config['victim_id'], config['killer_id']]
        dates = [config['before_date_raw'], config['after_date_raw']]
        connection = tuple(projection['native_connection'])
        token = config['monitor_sequence_token']
        gate('independent monitor/daily tokens', token != config['managed_daily_sequence_token'])
        monitor_rows = []
        gate('monitor wrappers same directory', args.begin.resolve().parent == args.finish.resolve().parent)
        for phase, wrapper_path, date, status in [('begin', args.begin, dates[0], 'armed'), ('finish', args.finish, dates[1], 'drained')]:
            wrapper = read(wrapper_path)
            freeze(wrapper_path, phase + '-wrapper-exact.json')
            gate(phase + ' source binding exact', wrapper['source_binding'] == binding_identity)
            receipt_path = bound(wrapper['native_receipt']['response'], phase + '-native-response-exact.json')
            request_path = bound(wrapper['native_receipt']['request'], phase + '-native-request-exact.json')
            receipt, request = read(receipt_path), read(request_path)
            gate(phase + ' original accepted lifecycle', receipt['result'] == 'CALL_COMPLETED' and receipt['body']['accepted'] is True and
                 receipt['body']['status'] == status and wrapper['native_envelope'] == receipt['body'])
            found = payloads(receipt['body'])
            gate(phase + ' unique exact additive payload', len(found) == 1 and found[0][0] == wrapper['exact_payload_path'] and
                 found[0][1] == wrapper['scoped_variable_monitor'])
            monitor = found[0][1]
            gate(phase + ' raw request exact collector ABI/token', request['action'] == 'private_phase_trace' and
                 request['step'] == 'experimental-scoped-character-variable-monitor-' + phase + '-v1' and
                 request['monitor_sequence_token'] == token)
            if phase == 'begin':
                gate('raw begin two full characters', [request['scoped_character_id'], request['scoped_related_character_id']] == characters)
            actual_connection = tuple(receipt['driver_state'][key] for key in ('pipe_name', 'connection_generation', 'bridge_pid'))
            gate(phase + ' same process/connection as day and saves', actual_connection == connection)
            snap_path = bound(wrapper['source_snapshot']['response'], phase + '-snapshot-exact.json')
            snapshot = read(snap_path)
            values, body = wrapper['source_values'], snapshot['body']
            gate(phase + ' raw current paused snapshot', snapshot['result'] == 'CALL_COMPLETED' and body['paused'] is True and
                 body['date_raw'] == date and all(values[key] == body[key] for key in ('date_raw', 'paused', 'revision', 'native_revision', 'snapshot_id')) and
                 request['expected_revision'] == body['revision'])
            diagnostics = body['diagnostics']
            actual_session = {'episode_run_id': body['episode_run_id'], 'connection_generation': diagnostics['connection_generation'],
                              'bridge_pid': diagnostics['bridge_pid'], 'native_hello_session_generation': diagnostics['hello']['session_generation']}
            gate(phase + ' same admitted native hello/session', actual_session == config['native_session_binding'] and
                 all(values[key] == value for key, value in actual_session.items()))
            gate(phase + ' zero flags same scope/token/begin date', monitor['failure_flags'] == 0 and monitor['truncated'] is False and
                 monitor['monitor_sequence_token'] == token and monitor['character_ids'] == characters and monitor['begin_date_raw'] == dates[0])
            monitor_rows.append(monitor)
        beginning, final = monitor_rows
        gate('begin remains armed before actual drain', beginning['detours_uninstalled'] is False and final['detours_uninstalled'] is True)
        stable = ('character_ids', 'begin_date_raw', 'signature_weapon_key_id', 'native_identifier_table_token',
                  'native_identifier_epoch', 'native_identifier_count', 'prearmed_event_definitions',
                  'event_producer_definitions_read', 'event_manager_token', 'event_definition_count')
        gate('same original prearmed identities throughout window', all(beginning[key] == final[key] for key in stable))
        gate('exact initial records retained as prefix', final['records'][:len(beginning['records'])] == beginning['records'])
        controlled_lifecycle_thread = projection['managed_checkpoint']['before']['thread_id']
        # GUI getter callbacks may run on the GUI owner thread. Only arm/final
        # lifecycle binds this controlled thread; each original operation pair
        # retains its actual thread/context, and commit causality is separate.
        monitor_projection = validate_variable_monitor(final, character_ids=characters, expected_monitor_token=token,
               before_date_raw=dates[0], after_date_raw=dates[1], expected_thread=controlled_lifecycle_thread)
        report['actual_monitor_projection'] = monitor_projection
        comparisons = []
        for index, cid in enumerate(characters):
            before = projection['saved_states'][0]['projection']['characters'][index]
            after = projection['saved_states'][1]['projection']['characters'][index]
            gate('saved endpoint full character ' + str(cid), before['character_id'] == after['character_id'] == cid)
            old, saved = saved_signature(before), saved_signature(after)
            writes = [row for row in monitor_projection['actual_write_pairs'] if row['character_id'] == cid]
            last = writes[-1] if writes else None
            endpoint_agrees = last is not None and saved is not None and last['after_flag']['native_name'] == saved['native_name']
            comparisons.append({'character_id': cid, 'before_saved_signature': old, 'after_saved_signature': saved,
                                'actual_write_count': len(writes), 'last_actual_write': last,
                                'first_original_native_owner_observation': monitor_projection['first_original_owner_observations'][index],
                                'after_save_equals_last_independently_decoded_write': endpoint_agrees,
                                'endpoint_save_relative_to_preUI_window': 'UI_WINDOW_ORDER_NOT_DECODED'})
        report['same_run_saved_endpoint_comparisons'] = comparisons
        report['signature_producer_closed'] = monitor_projection['producer_closed']
        report['signature_write_and_after_endpoint_closed'] = bool(monitor_projection['actual_write_pairs']) and all(
            row['after_save_equals_last_independently_decoded_write'] for row in comparisons if row['actual_write_count'])
        report['limits'] = ['Saved pair wrapper alone does not establish its order relative to UI getters; do not treat it as monitor arm state.',
                             'Monitor and daily tokens differ and are bound to this exact native process.',
                             'GUI observations retain their actual threads. Only controlled arm/final lifecycle and each original call pair require thread equality.',
                             'Missing first original getter is UNKNOWN, not an absent initial signature; saved endpoints are independent observations.',
                            'Source-bound TLS producer proves nearest matched immediate ancestor, not root receiver equals victim.',
                            'No per-window UI/RNG or 13-domain/global completion is inferred by this receipt.']
        report['status'] = 'PASS_SAME_RUN_ORIGINAL_MONITOR_OPERATIONS_AND_SAVED_ENDPOINT_PROJECTION'
    except Exception as error:
        report['status'] = 'RED_INPUT_OR_FACT_GATE'
        report['error'] = type(error).__name__ + ': ' + str(error)
    target = out / 'knight-variable-monitor-run-verification.json'
    write(target, report)
    print(json.dumps({'status': report['status'], 'error': report.get('error'), 'receipt': identity(target)}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('begin', 'finish', 'causal-projection', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    return 0 if verify(args)['status'].startswith('PASS') else 2


if __name__ == '__main__':
    raise SystemExit(main())
