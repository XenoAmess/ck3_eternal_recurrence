"""Original ordinary-courtier async accept/refuse cell on the shared runtime."""
from __future__ import annotations
import json
from pathlib import Path

from ck3_mod_acceptance_prepare import materialize_fixture_profile, pin, write_json
from .xqol_scope import parse_song_scope

DATA = Path(__file__).with_name('xqol_ordinary_async.json')
PLAN = Path(__file__).with_name('xqol_ordinary_async.plan.json')
RULES = Path(__file__).with_name('xqol_ordinary_async.rules.json')
MARKERS = {
    'begin': 'ZQR120QUAL: SCOPE BEGIN actual_song_actor_D0',
    'pass': 'ZQR120QUAL: TEST PASS actual_song_actor_D0',
    'end': 'ZQR120QUAL: SCOPE END actual_song_actor_D0',
    'fail': 'ZQR120QUAL: TEST FAIL actual_song_actor_D0',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def scope(raw):
    proof = parse_song_scope(raw, {'scope_name': 'xqol_startup_actor', 'markers': MARKERS})
    require(proof is not None, 'Original actual Song startup scope missing')
    return proof


def validate_contract(context):
    contract = context['case_contract']
    require(contract == read(DATA), 'Selected ordinary async contract differs')
    require(context['case_spec']['budgets'] == contract['original_budgets'], 'Original4500/600 budgets changed')
    steps = read(PLAN)['steps']
    require(len(steps) == 30 and len({step['id'] for step in steps}) == 30 and
            sum(step.get('kind') == 'advance_day' for step in steps) == 12 and
            all(step.get('days') == 1 and step.get('timeout') == 300
                for step in steps if step.get('kind') == 'advance_day'), 'Original30/day12 once-plan changed')
    return contract, steps


def prepare_case(context):
    contract, _ = validate_contract(context)
    fixture = Path(context['repo_root']) / 'tools/fixtures/xqol_ordinary_async'
    actual = {path.relative_to(fixture).as_posix(): pin(path) for path in fixture.rglob('*') if path.is_file()}
    require(set(actual) == set(contract['fixture_files']) and all(
        all(actual[key][field] == expected[field] for field in ('bytes', 'sha256'))
        for key, expected in contract['fixture_files'].items()), 'Original ordinary fixture4 bytes changed')
    result = materialize_fixture_profile(context, fixture, context['case_inputs']['product_dir'],
                                         context['case_inputs']['plain_configuration'])
    product = {key.removeprefix('mod-content/product/'): row for key, row in result['files'].items()
               if key.startswith('mod-content/product/')}
    expected = context['case_inputs']['formal_product_files']
    require(len(product) == len(expected) == 27 and set(product) == set(expected) and all(
        all(product[key][field] == row[field] for field in ('bytes', 'sha256'))
        for key, row in expected.items()), 'Exact existing formal27 product required; no builder is run')
    output = Path(context['output'])
    handler = pin(Path(__file__)); handler['function'] = 'admit_startup_event'
    dependencies = [pin(path) for path in (DATA, PLAN, RULES, Path(__file__).with_name('xqol_scope.py'),
                    Path(__file__).parent.parent / 'ck3_mod_acceptance_prepare.py',
                    Path(__file__).with_name('__init__.py'))]
    hook = output / 'frontend-fixture-startup-case-contract.json'
    write_json(hook, {'schema': 'ck3-frontend-fixture-startup-case-contract-v1',
                     'state_dir': context['state_dir'], 'handler': handler, 'dependencies': dependencies})
    return {'startup': {'mode': 'fixture', 'state_dir': result['state_dir'],
                       'fixture_start_policy': result['fixture_start_policy'],
                       'startup_case_contract': pin(hook), 'frontend_rules_plan': pin(RULES)},
            'initial_plan': pin(PLAN), 'initial_plan_original_business': True,
            'profile': result, 'fixture_original_files': actual, 'formal_files_unchanged': 27,
            'original_day_count': 12, 'original_step_count': 30, 'runtime_status': 'NOT_RUN',
            'business_pass': False, 'product_release_pass': False}


def lookup(value, dotted):
    for part in dotted.split('.'):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def frame_identity(frame, context, binding, *, paused=True):
    require(isinstance(frame, dict), 'Actual native frame missing')
    require(frame.get('episode_projection') == 'native_campaign' and frame.get('map_ready') is True and
            frame.get('source') == 'injected-dll-named-pipe' and frame.get('backend_id') == 'native-headless' and
            frame.get('active_event') is None and (paused is None or frame.get('paused') is paused),
            'Original campaign/map/pause/event boundary changed')
    actor, diagnostics = frame['played_character'], frame['diagnostics']
    require(actor.get('source') == 'native' and actor.get('alive') is True and
            actor.get('character_id') == binding['actor_character_id'] and
            all(diagnostics.get(key) == binding[key] for key in ('bridge_pid', 'connection_generation')),
            'Original immutable Song actor/PID/generation changed')
    hello = diagnostics['hello']; game = context['shared_game']
    require(hello.get('pid') == binding['bridge_pid'] and hello.get('connection_generation') == binding['connection_generation'] and
            hello.get('expected_ck3_version') == game['version'] and hello.get('game_adapter_id') == 'ck3-' + game['version'] + '-msvc-x64' and
            str(hello.get('expected_ck3_sha256', '')).lower() == game['exe_sha256'].lower() and hello.get('ck3_build_match') is True,
            'Actual native build differs from the selected common runtime')
    require(type(frame.get('date_raw')) is int and frame['date_raw'] >= binding['date_raw'], 'Actual date regressed')
    require(type(frame.get('revision')) is int and frame['revision'] >= 0 and
            type(frame.get('native_revision')) is int and frame['native_revision'] > 0 and
            type(frame.get('local_player_id')) is int and frame['local_player_id'] >= 0 and
            isinstance(frame.get('snapshot_id'), str) and frame['snapshot_id'], 'Actual frame identity missing')
    pump = diagnostics.get('last_heartbeat', {}).get('main_thread_query_mailbox_v1', {}).get('pump_epochs')
    require(type(pump) is int and pump >= 0, 'Actual owner pump missing')
    return pump


def completed_observation(context, report, raw):
    contract, steps = validate_contract(context)
    require(not report.get('error') and report.get('status') not in ('ERROR', 'RED'), 'Actual host failure preserved; no business credit')
    state = report.get('frontend_fixture_business_context', {})
    require(state.get('status') == 'ACTUAL_FIXTURE_QUALIFIED_BUSINESS_CONTEXT_BOUND' and
            state.get('actual_current_actor_bound') is True and state.get('qualification_observed') is True and
            state.get('start_resubmitted') is False and state.get('episode_projection') == 'native_campaign',
            'Actual shared fixture binding missing')
    binding = state['binding']; proof = scope(raw)
    require(binding['actor_character_id'] == proof['runtime_character_id'] and all(
        type(binding.get(key)) is int and binding[key] > 0 for key in ('actor_character_id', 'bridge_pid', 'connection_generation')),
        'Original raw Song scope differs from actual native binding')
    require(len(raw) <= 64 * 1024 * 1024, 'Original debug log bound exceeded')
    lines = raw.splitlines()
    counts = {marker: sum(marker.encode('ascii') in line for line in lines)
              for marker in contract['required_startup'] + contract['required_markers'] + contract['forbidden_markers']}
    require(all(counts[marker] == 1 for marker in contract['required_startup'] + contract['required_markers']) and
            all(counts[marker] == 0 for marker in contract['forbidden_markers']), 'Original exact startup/final/FAIL0 assertions not proved')
    by_id = {}
    for row in report.get('steps', []):
        require(row.get('id') not in by_id, 'Actual step replay/duplicate')
        by_id[row.get('id')] = row
    results, completed = {}, []
    last_pump = -1
    for step in steps:
        row = by_id.get(step['id'])
        require(isinstance(row, dict) and row.get('finished_at'), 'Original once-plan has unfinished/missing row: ' + step['id'])
        if not step.get('continue_on_error', False):
            require(row.get('ok') is True and not row.get('error'), 'Original step failed: ' + step['id'])
        result = row.get('result')
        for key, expected in step.get('expect', {}).items():
            if isinstance(expected, dict) and set(expected) == {'$ref'}:
                require(expected['$ref'].startswith('results.'), 'Unexpected runtime reference')
                expected = lookup(results, expected['$ref'].removeprefix('results.'))
            require(lookup(result, key) == expected, 'Actual original expectation failed: ' + step['id'] + '/' + key)
        results[step['id']] = result
        frames = []
        if step['id'] == steps[0]['id']:
            require(result['date_raw'] == binding['date_raw'], 'Original D0 date differs from actual shared startup binder')
            frames.append((result, True))
        if step.get('kind') == 'advance_day':
            frames.extend((result[key], True if key != 'running_successor' else None)
                          for key in ('before', 'running_successor', 'after'))
            require(type(result.get('elapsed_hours')) is int and result['elapsed_hours'] >= 24 and
                    result['after']['date_raw'] - result['before']['date_raw'] == result['elapsed_hours'],
                    'Actual original natural one-day interval missing')
        if row.get('after_snapshot'):
            frames.append((row['after_snapshot'], True))
        for frame, paused in frames:
            pump = frame_identity(frame, context, binding, paused=paused)
            require(pump >= last_pump, 'Original native owner pump regressed')
            last_pump = pump
        completed.append(row)
    return {'original_step_count': len(completed), 'original_natural_day_count': 12,
            'actual_binding': binding, 'actual_actor_scope': proof, 'marker_counts': counts,
            'completed_initial_rows': completed, 'one_life_identity_claimed': False}


def run_case(context, client):
    report = client.guard()
    raw = client.log_bytes()
    observation = completed_observation(context, report, raw)
    output = Path(context['output'])
    debug = output / 'ordinary-async-debug-original.raw'
    with debug.open('xb') as stream:
        stream.write(raw)
    snapshot = output / 'ordinary-async-completed-native-report.json'
    write_json(snapshot, report)
    result = {'schema': 'ck3-xqol-ordinary-async-observation-v1', 'run_id': context['run_id'],
              'product': 'xqol', 'case': 'ordinary_async', 'observation': observation,
              'debug_original': pin(debug), 'completed_report': pin(snapshot), 'original_plan': pin(PLAN),
              'case_contract_qualified': True, 'gui_contract_qualified': True,
              'business_contract_applicable': True, 'business_pass': True, 'product_release_pass': False,
              'scope': 'Only original ordinary-courtier natural accept/refuse; public normal_close must still qualify',
              'no_initial_plan_requeue': True, 'does_not_credit': context['case_contract']['does_not_credit']}
    client.checkpoint('xqol-ordinary-async-result', result)
    return result


def verify_case(context):
    path = Path(context['output']) / 'xqol-ordinary-async-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False, 'business_pass': False,
                'product_release_pass': False, 'status': 'NOT_RUN'}
    result = read(path)
    require(result['run_id'] == context['run_id'] and result['case'] == 'ordinary_async', 'Original result crossed actual run/case')
    for name in ('debug_original', 'completed_report', 'original_plan'):
        require(pin(Path(result[name]['path'])) == result[name], 'Original observation bytes changed: ' + name)
    observation = completed_observation(context, read(result['completed_report']['path']), Path(result['debug_original']['path']).read_bytes())
    require(observation == result['observation'], 'Actual original ordinary async evidence changed')
    return {**result, 'product_release_pass': False}


def admit_startup_event(context, snapshot, event_context):
    """Original scope-bound sole first intro; shared host owns the once-selection."""
    log_path = (Path(context['state_dir']) / 'profile/logs/debug.log').resolve()
    raw = log_path.read_bytes()
    proof = scope(raw)
    played = snapshot.get('played_character', {})
    require(played.get('character_id') == proof['runtime_character_id'] and
            played.get('alive') is True and played.get('source') == 'native',
            'Focused guard startup intro differs from actual original Song scope')
    event = snapshot.get('active_event')
    require(isinstance(event, dict) and event.get('source') == 'native' and
            type(event.get('instance_id')) is int and event['instance_id'] == 1 and event.get('option_count') == 1,
            'Original sole first native intro contract changed')
    options = event.get('options')
    require(isinstance(options, list) and len(options) == 1 and options[0].get('enabled') is True and
            options[0].get('option_number') == 1 and options[0].get('index') == 0,
            'Original first intro must expose enabled public option1/native index0')
    typed = event_context.get('current_event_window_context', {})
    identity = typed.get('root_scope', {}).get('typed_identity', {})
    require(event_context.get('status') == 'available' and event_context.get('current_event_window_context_ready') is True and
            typed.get('schema') == 'current-event-window-context-v1' and typed.get('schema_version') == 1 and
            typed.get('status') == 'available' and typed.get('window_match_count') == 1 and
            typed.get('current_event_instance_id') == 1 and typed.get('snapshot_revision') == snapshot['native_revision'] and
            typed.get('date_raw') == snapshot['date_raw'] and identity.get('status') == 'available' and
            identity.get('kind') == 'character' and identity.get('character_id') == played['character_id'],
            'Actual typed intro context differs from the original Song scope-bound event')
    typed_options = typed.get('options')
    require(isinstance(typed_options, list) and len(typed_options) == 1 and all(
        typed_options[0].get(key) == value for key, value in {
            'rendered_index': 0, 'native_option_index': 0, 'shown': True, 'enabled': True,
            'fallback': False, 'cancel': False}.items()), 'Actual typed intro sole option is not enabled native index0')
    # The original parser/run_case retain full raw hex; startup carries its exact byte reference.
    proof = {key: value for key, value in proof.items() if key != 'raw_scope_block_hex'}
    proof['markers'] = {key: {'literal': marker, 'count': raw.count(marker.encode('ascii'))}
                        for key, marker in MARKERS.items()}
    proof['raw_scope_block_reference'] = {
        'path': str(log_path), 'byte_start': proof['byte_start'], 'byte_end': proof['byte_end'],
        'bytes': proof['byte_end'] - proof['byte_start'], 'sha256': proof['raw_scope_block_sha256']}
    return {'event_instance_id': event['instance_id'], 'option_number': 1,
            'proof': proof, 'business_pass': False}
