"""Verify one exact native knight run and project its full selected saved blocks.

Only existing original request/result JSON, immutable CK3 saves and the pinned
Rakaly decoder are read. No CK3, desktop, provider, Git mutation or network operation.
The new output directory is create-only and keeps successful and failed assets.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.simulation.knight_causal_save_projection import (
    block_body, character_snapshot, delta, extract_exact_indented_block,
    find_key_blocks, parse_block, validate_scoped_journal,
)

RAKALY_SHA = 'E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D'


def identity(path: Path) -> dict:
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size, 'sha256': digest}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path: Path, value) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def freeze(source: Path, target: Path) -> dict:
    wanted = identity(source)
    with source.open('rb') as incoming, target.open('xb') as outgoing:
        shutil.copyfileobj(incoming, outgoing)
    got = identity(target)
    if got['sha256'] != wanted['sha256'] or got['bytes'] != wanted['bytes']:
        raise ValueError('exact source copy failed')
    return {'original': wanted, 'exact_frozen_copy': got}


def verify(args) -> dict:
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    checks = []
    report = {'schema': 'ck3.knight-causal-run-projection.v1', 'status': 'UNKNOWN',
              'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'no_game_launch': True, 'desktop_inputs': 0, 'master_intake': False,
              'global_bundle_complete': False, 'full_mutable_transition_bundle_complete': False,
              'sole_cause_proven': False, 'checks': checks}

    def gate(name: str, passed: bool) -> None:
        checks.append({'name': name, 'pass': passed})
        if not passed:
            raise ValueError(name)

    def bound(entry: dict) -> Path:
        path = Path(entry['path']).resolve()
        actual = identity(path)
        gate('declared exact file ' + str(path), actual['bytes'] == entry['bytes'] and
             actual['sha256'] == entry['sha256'].upper())
        return path

    try:
        module = Path(sys.modules['xar_autoplayer.simulation.knight_causal_save_projection'].__file__)
        selector_module = Path(sys.modules['xar_autoplayer.simulation.knight_selector_replay'].__file__)
        report['verifier_sources'] = [freeze(Path(__file__), out / 'verifier-exact.py'),
                                      freeze(module, out / 'pure-projection-exact.py'),
                                      freeze(selector_module, out / 'pure-selector-replay-exact.py')]
        source_pairs = [args.before_pair.resolve(), args.after_pair.resolve()]
        gate('pair originals same directory', source_pairs[0].parent == source_pairs[1].parent)
        pairs = [read(path) for path in source_pairs]
        report['pair_originals'] = [freeze(path, out / (label + '-pair-exact.json'))
                                    for path, label in zip(source_pairs, ('before', 'after'))]
        explicit_binding = 'source_head' not in pairs[0]['source_binding']
        day_finished = None
        if explicit_binding:
            report['input_format'] = 'explicit_binding_identity_saved_pair_v1'
            gate('both phases point to same binding bytes', pairs[0]['source_binding'] == pairs[1]['source_binding'])
            config_path = bound(pairs[0]['source_binding'])
            config = read(config_path)
            report['source_binding'] = freeze(config_path, out / 'research-binding-exact.json')
            gate('expected explicit source commit', config['source_commit'] == args.expected_source_head)
            gate('actual local frozen source HEAD matches', subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=config['source_root'], text=True).strip() == config['source_commit'])
            for pin in config['pins']:
                bound(pin)
            dll = Path(config['bridge_dll']).resolve()
            dll_identity = identity(dll)
            gate('expected explicit DLL bytes', dll_identity['sha256'] == args.expected_dll_sha256.upper() and
                 any(Path(pin['path']).resolve() == dll and pin['sha256'].upper() == dll_identity['sha256'] for pin in config['pins']))
            gate('config actor/characters/day match', config['actor_id'] == args.episode_character_id and
                 config['victim_id'] == args.victim and config['killer_id'] == args.related and
                 config['after_date_raw'] - config['before_date_raw'] == 24)
            live_output = Path(config['live_root']) / 'ck3-output'
            live_identity = read(live_output / 'live-run-identity.json')
            gate('config real run ID match', len(live_identity['identities']) == 1 and
                 live_identity['identities'][0]['run_id'] == config['run_id'])
            preflight = read(live_output / 'preflight.json')
            gate('config actual loader preflight actor/date', preflight['checkpoint_source']['date_raw'] == config['before_date_raw'] and
                 preflight['checkpoint_source']['actor'] == config['actor_id'])
            for key in ('bridge_dll', 'bridge_injector'):
                actual = identity(Path(config[key]))
                gate('actual loader ' + key, preflight[key]['sha256'].upper() == actual['sha256'] and preflight[key]['bytes'] == actual['bytes'])
            report['live_identity'] = freeze(live_output / 'live-run-identity.json', out / 'live-run-identity-exact.json')
            report['preflight'] = freeze(live_output / 'preflight.json', out / 'preflight-exact.json')
            episodes = []
            for label, pair in zip(('before', 'after'), pairs):
                gate(label + ' declared save phase', pair['phase'] == label)
                receipt = read(bound(pair['save']['response']))
                gate(label + ' embedded native save body exact', pair['save_body'] == receipt['body'])
                episodes.append(receipt['body']['checkpoint']['episode_run_id'])
            gate('same native checkpoint episode', bool(episodes[0]) and episodes[0] == episodes[1])
            episode = episodes[0]
            gate('explicit one-day finished input required', args.day_finished is not None)
            day_finished = read(args.day_finished)
            gate('day finished same explicit binding', day_finished['source_binding'] == pairs[0]['source_binding'])
            report['day_finished_original'] = freeze(args.day_finished, out / 'one-day-finished-exact.json')
        else:
            report['input_format'] = 'legacy_inline_source_binding_pair_v1'
            episode = pairs[0]['episode_run_id']
            gate('same episode run', bool(episode) and episode == pairs[1]['episode_run_id'])
            for pair in [pair for pair in pairs if 'source_binding' in pair]:
                binding = pair['source_binding']
                gate('expected exact source head', binding['source_head'] == args.expected_source_head)
                dlls = [pin for pin in binding['declared_pins'] if Path(pin['path']).suffix.lower() == '.dll']
                gate('expected exact DLL', len(dlls) == 1 and dlls[0]['sha256'].upper() == args.expected_dll_sha256.upper())
                for entry in binding['declared_pins']:
                    bound(entry)
                for key in ('preflight', 'readback'):
                    bound(binding[key])
            if 'source_binding' in pairs[1]:
                gate('same original live source identity', pairs[0]['source_binding'] == pairs[1]['source_binding'])
            report['source_binding'] = pairs[0]['source_binding']
        report['episode_run_id'] = episode
        trace_wrapper = read(args.trace)
        report['trace_original'] = freeze(args.trace, out / 'trace-exact.json')
        gate('native trace completed/accepted', trace_wrapper['result'] == 'CALL_COMPLETED' and
             trace_wrapper['body']['accepted'] is True)
        managed = trace_wrapper['body']['managed_trace']
        finish_container = day_finished if explicit_binding else pairs[1]
        after_finish = bound(finish_container['trace_finish']['response'])
        gate('after pair references this exact trace', after_finish == args.trace.resolve() and
             finish_container['trace_finish_body'] == trace_wrapper['body'])
        if not explicit_binding:
            gate('legacy trace error absent', pairs[1]['trace_error'] is None)
        trace, checkpoint = managed['trace'], managed['managed_checkpoint']
        gate('native captured flags0 seven records', trace['status'] == 'captured' and
             trace['failure_flags'] == 0 and trace['record_count'] == 7 and len(trace['records']) == 7 and
             all(record['capture_failure_flags'] == 0 for record in trace['records']))
        gate('global false never upgraded', trace['readiness']['full_mutable_transition_bundle_complete'] is False and
             all(record['full_mutable_transition_bundle_complete'] is False for record in trace['records']))
        gate('paused exactly one native day', checkpoint['exact_one_day_observed'] is True and
             checkpoint['before']['paused'] is True and checkpoint['after']['paused'] is True and
             checkpoint['after']['date_raw'] - checkpoint['before']['date_raw'] == 24)
        gate('same daily tuple', all(checkpoint['before'][key] == checkpoint['after'][key]
             for key in ('combat_id', 'thread_id', 'managed_daily_sequence_token')))
        if explicit_binding:
            gate('journal checkpoint tuple equals explicit binding', checkpoint['before']['combat_id'] == config['combat_id'] and
                 checkpoint['before']['date_raw'] == config['before_date_raw'] and checkpoint['after']['date_raw'] == config['after_date_raw'] and
                 checkpoint['before']['managed_daily_sequence_token'] == config['managed_daily_sequence_token'])
        gate('detours uninstalled', checkpoint['detours_uninstalled'] is True)
        report['managed_checkpoint'] = checkpoint
        report['all_original_phase_records'] = trace['records']
        report['all_original_trace_nonrecord_fields'] = {key: value for key, value in trace.items() if key != 'records'}
        driver_connections = []
        states = []
        parsed = []
        gate('pinned Rakaly exact executable', identity(args.rakaly)['sha256'] == RAKALY_SHA)
        report['rakaly'] = identity(args.rakaly)
        for label, pair, input_raw in zip(('before', 'after'), pairs, (args.before_save, args.after_save)):
            raw = bound(pair['immutable'])
            gate(label + ' explicit raw is declared original', input_raw.resolve() == raw)
            receipt_path = bound(pair['save']['response'])
            receipt = read(receipt_path)
            gate(label + ' saved receipt accepted', receipt['result'] == 'CALL_COMPLETED' and
                 receipt['body']['accepted'] is True and receipt['body']['checkpoint']['status'] == 'saved')
            saved = receipt['body']['checkpoint']
            gate(label + ' saved native actor episode date/hash', saved['episode_run_id'] == episode and
                 saved['episode_character_id'] == args.episode_character_id and
                 saved['date_raw'] == checkpoint[label]['date_raw'] and saved['size'] == raw.stat().st_size and
                 saved['sha256'].upper() == identity(raw)['sha256'])
            request_path = Path(receipt['request']['path'])
            request = read(request_path)
            snapshot_path = bound(pair['snapshot']['response'])
            snapshot = read(snapshot_path)
            if explicit_binding:
                values = pair['source_values']
                actual_snapshot = snapshot['body']
                gate(label + ' source_values equal original snapshot fields', all(
                    values[key] == actual_snapshot[key] for key in
                    ('date_raw', 'paused', 'revision', 'native_revision', 'snapshot_id')) and
                    values['actor'] == actual_snapshot['played_character']['character_id'] and
                    values['actor'] == config['actor_id'] and values['paused'] is True and
                    values['date_raw'] == checkpoint[label]['date_raw'])
            gate(label + ' checkpoint revision request bound', request['tool'] == 'ck3_save_checkpoint' and
                 request['arguments']['expected_revision'] == snapshot['body']['revision'])
            connection = tuple(receipt['driver_state'][key] for key in ('pipe_name', 'connection_generation', 'bridge_pid'))
            driver_connections.append(connection)
            melted = out / (label + '-melted.ck3')
            argv = [str(args.rakaly.resolve()), 'melt', str(raw), '--unknown-key', 'stringify', '--format', 'ck3', '--out', str(melted)]
            write(out / (label + '-melt-command.json'), {'argv': argv, 'raw': identity(raw), 'rakaly': report['rakaly']})
            stdout, stderr = out / (label + '-melt.stdout.log'), out / (label + '-melt.stderr.log')
            with stdout.open('xb') as out_stream, stderr.open('xb') as err_stream:
                process = subprocess.run(argv, stdout=out_stream, stderr=err_stream, check=False)
            write(out / (label + '-melt-process.json'), {'returncode': process.returncode,
                  'stdout': identity(stdout), 'stderr': identity(stderr)})
            gate(label + ' real decoder exit0', process.returncode == 0 and melted.is_file())
            text = melted.read_text(encoding='utf-8-sig')
            chars = [character_snapshot(text, identifier) for identifier in (args.victim, args.related)]
            objects = {}
            for char in chars:
                path = out / (label + '-character-' + str(char['character_id']) + '-exact.txt')
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(char['raw_block'] + '\n')
                char['exact_extract'] = identity(path)
                del char['raw_block']
            for domain in ('combats', 'house_relations'):
                raw_block = extract_exact_indented_block(text, domain, 0)
                path = out / (label + '-' + domain + '-exact.txt')
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(raw_block + '\n')
                ast = parse_block(block_body(raw_block))
                objects[domain] = {'exact_extract': identity(path), 'entries': ast}
                if domain == 'combats':
                    matching = find_key_blocks(ast, str(checkpoint[label]['combat_id']))
                    gate(label + ' full generation combat saved', bool(matching))
                    objects['matched_combat_blocks'] = matching
            # Accolade availability must be explicit. Absent is not an invented empty database.
            matches = list(__import__('re').finditer(r'^\w*accolade\w*=\{', text, __import__('re').M))
            objects['accolade_top_level_names'] = [match.group(0).split('=')[0] for match in matches]
            for name in objects['accolade_top_level_names']:
                raw_block = extract_exact_indented_block(text, name, 0)
                path = out / (label + '-' + name + '-exact.txt')
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(raw_block + '\n')
                objects[name] = {'exact_extract': identity(path), 'entries': parse_block(block_body(raw_block))}
            parsed.append({'characters': chars, 'objects': objects})
            states.append({'label': label, 'raw_original': identity(raw), 'melted': identity(melted),
                           'native_save_receipt': freeze(receipt_path, out / (label + '-save-receipt-exact.json')),
                           'native_save_request': freeze(request_path, out / (label + '-save-request-exact.json')),
                           'snapshot_receipt': freeze(snapshot_path, out / (label + '-snapshot-exact.json')),
                           'projection': parsed[-1]})
        gate('save and trace exact same process connection', len(set(driver_connections)) == 1 and
             driver_connections[0] == tuple(trace_wrapper['driver_state'][key] for key in ('pipe_name', 'connection_generation', 'bridge_pid')))
        report['native_connection'] = driver_connections[0]
        report['saved_states'] = states
        report['complete_character_deltas'] = [{
            'character_id': args.victim if index == 0 else args.related,
            'all_scalar_leaf_deltas': delta(parsed[0]['characters'][index]['entries'], parsed[1]['characters'][index]['entries'])}
            for index in (0, 1)]
        report['all_house_database_deltas'] = delta(parsed[0]['objects']['house_relations']['entries'], parsed[1]['objects']['house_relations']['entries'])
        left = {row['path']: row['entries'] for row in parsed[0]['objects']['matched_combat_blocks']}
        right = {row['path']: row['entries'] for row in parsed[1]['objects']['matched_combat_blocks']}
        gate('same saved full combat paths', left.keys() == right.keys())
        report['all_saved_case_combat_deltas'] = [{'path': path, 'all_scalar_leaf_deltas': delta(left[path], right[path])} for path in left]
        journal = managed.get('scoped_transition_chain')
        if explicit_binding and journal is not None:
            gate('scoped journal exact declared event', journal['event_load_index'] == config['event_load_index'])
        report['scoped_journal_validation'] = validate_scoped_journal(journal, checkpoint, args.victim, args.related)
        report['original_scoped_transition_chain'] = journal
        before_victim, after_victim = parsed[0]['characters'][0], parsed[1]['characters'][0]
        report['observed_saved_death_transition'] = before_victim['status'] == 'ALIVE' and after_victim['status'] == 'DEAD'
        report['scoped_save_complete_selected_blocks_projected'] = True
        report['intraday_unpublished_fields_remain_unknown'] = True
        report['limits'] = ['Same-run saved full block differences are net observations, not per-write timing/cause.',
                            'Direct native char+D8/E4/E8 are base martial/learning/prowess; effective battle stats are separate entry fields.',
                            'Saved trait indices are lookup ordinals; compare native trait IDs using prearmed stable keys.',
                            'House effect invocation alone does not prove a persistent relation write.',
                            'A saved death date/reason/killer does not replace the typed native death request/commit tuple.',
                            'This verifies machine facts, not real UI, full panel or human signoff.',
                            'Historic R0139 or R0127 evidence never fills fields in a new run.']
        for source in report['verifier_sources']:
            gate('verifier source stable during execution', identity(Path(source['original']['path'])) == source['original'])
        report['status'] = 'PASS_SAME_RUN_SELECTED_SAVED_BLOCKS_AND_ORIGINAL_TRACE'
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        report['status'] = 'RED_INPUT_OR_FACT_GATE'
    write(out / 'knight-causal-run-verification.json', report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before-pair', 'after-pair', 'before-save', 'after-save', 'trace', 'rakaly', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-source-head', required=True)
    parser.add_argument('--expected-dll-sha256', required=True)
    parser.add_argument('--episode-character-id', type=int, required=True)
    parser.add_argument('--victim', type=int, required=True)
    parser.add_argument('--related', type=int, required=True)
    parser.add_argument('--day-finished', type=Path,
                        help='Required for explicit-binding saved-pair input; exact unique one-day-finished.json original.')
    args = parser.parse_args()
    report = verify(args)
    print(json.dumps({'status': report['status'], 'error': report.get('error'),
                      'receipt': identity(args.output_dir.resolve() / 'knight-causal-run-verification.json'),
                      'check_count': len(report['checks'])}))
    return 0 if report['status'].startswith('PASS') else 2


if __name__ == '__main__':
    raise SystemExit(main())
