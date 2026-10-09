"""Two original guard assertions through the public runtime; no defense replay."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

from ck3_mod_acceptance_prepare import invoke_fixture_prepare, materialize_fixture_profile, pin, write_json
from .xqol_scope import parse_song_scope

ENABLED = 'ZQA: TEST PASS transfer_guard_enabled_and_preexisting_preserved'
DISABLED = 'ZQA: TEST PASS transfer_guard_disabled_and_preexisting_preserved'
MARKERS = {
    'begin': 'ZQAGUARD: SCOPE BEGIN actual_song_actor',
    'pass': 'ZQAGUARD: SCOPE PASS actual_song_actor',
    'end': 'ZQAGUARD: SCOPE END actual_song_actor',
    'fail': 'ZQAGUARD: TEST FAIL actual_song_actor',
}
REQUIRED = ['ZQAGUARD: TEST BEGIN focused_guards', ENABLED, DISABLED, 'ZQAGUARD: TEST DONE focused_guards']


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def scope(raw):
    proof = parse_song_scope(raw, {'scope_name': 'xqol_startup_actor', 'markers': MARKERS})
    require(proof is not None, 'Original actual Song startup scope proof missing')
    return proof


def prepare_case(context):
    config = context['case_contract']
    require(config['original_required_markers'] == [ENABLED, DISABLED] and config['maximum_natural_days'] == 2,
            'Only the original two guards assertions and two scheduled days are admitted')
    require(context['case_spec']['budgets'] == {
        'command_timeout': 300, 'readiness_timeout': 400, 'timeout': 3000,
        'poll_interval': 0.05, 'hold_seconds': 1800}, 'Focused cell may not extend original QOL wall-clock bounds')
    output = Path(context['output'])
    fixture = output / 'focused-guards-fixture'
    emitter = Path(context['repo_root']) / 'tools/prepare_xqol_guards_fixture.py'
    emitted = invoke_fixture_prepare(context, emitter, ['--repo', context['repo_root'], '--output', fixture])
    projection = read(fixture / 'projection-receipt.json')
    require(projection['assertions'] == [ENABLED, DISABLED], 'Original guard assertion projection differs')
    profile = materialize_fixture_profile(context, fixture, context['case_inputs']['product_dir'],
                                          context['case_inputs']['plain_configuration'])
    actual_product = {key.removeprefix('mod-content/product/'): row for key, row in profile['files'].items()
                      if key.startswith('mod-content/product/')}
    expected = context['case_inputs']['formal_product_files']
    require(len(actual_product) == len(expected) == 27 and set(actual_product) == set(expected),
            'Exact existing formal27 tree required; no builder is run')
    require(all(all(actual_product[key][field] == expected[key][field] for field in ('bytes', 'sha256'))
                for key in expected), 'Focused guard cell changed formal product bytes')
    hook = output / 'frontend-fixture-startup-case-contract.json'
    handler = pin(Path(__file__)); handler['function'] = 'admit_startup_event'
    dependencies = [pin(path) for path in (
        Path(__file__).with_name('xqol_scope.py'),
        Path(__file__).parent.parent / 'ck3_mod_acceptance_prepare.py',
        Path(__file__).with_name('__init__.py'))]
    write_json(hook, {'schema': 'ck3-frontend-fixture-startup-case-contract-v1',
                      'state_dir': context['state_dir'], 'handler': handler, 'dependencies': dependencies})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'fixture', 'state_dir': profile['state_dir'],
                        'fixture_start_policy': profile['fixture_start_policy'],
                        'startup_case_contract': pin(hook)},
            'initial_plan': pin(initial), 'profile': profile, 'emitter': emitted,
            'projection_receipt': pin(fixture / 'projection-receipt.json'),
            'formal_product_unchanged': True, 'coverage': 'original_guards_only',
            'runtime_status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False}


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


def observe(raw):
    require(len(raw) <= 64 * 1024 * 1024, 'Original debug log bound exceeded')
    text = raw.decode('utf-8-sig', errors='replace')
    failures = [line for line in text.splitlines() if 'ZQA: TEST FAIL' in line or 'ZQAGUARD: TEST FAIL' in line]
    counts = {marker: text.count(marker) for marker in REQUIRED}
    require(not failures and not any(value > 1 for value in counts.values()),
            'Original focused guard FAIL/duplicate observed; no replay')
    return {'counts': counts, 'failures': failures, 'qualified': all(value == 1 for value in counts.values())}


def subject_proof(raw, stage):
    begin = ('ZQAGUARD: OBSERVED ' + stage + ' SUBJECTS BEGIN').encode()
    end = ('ZQAGUARD: OBSERVED ' + stage + ' SUBJECTS END').encode()
    require(raw.count(begin) == raw.count(end) == 1, 'Actual subject observation missing/duplicate')
    start = raw.index(begin); finish = raw.index(end, start) + len(end)
    block = raw[start:finish]
    found = {}
    for role in ('preexisting', 'owned'):
        role_begin = ('ZQAGUARD: SUBJECT ' + role + ' BEGIN').encode()
        role_end = ('ZQAGUARD: SUBJECT ' + role + ' END').encode()
        require(block.count(role_begin) == block.count(role_end) == 1, 'Original subject must be uniquely observed: ' + role)
        part = block[block.index(role_begin):block.index(role_end)]
        ids = re.findall(rb'(?m)^\[\d{2}:\d{2}:\d{2}\]\[D\]\[effectimpl\.cpp:\d+\]: [^\r\n]*?\(Internal ID: ([1-9][0-9]*)(?: - Historical ID [^)]*)?\)', part)
        require(len(ids) == 1 and 1 <= int(ids[0]) <= 2**31 - 1, 'Actual subject current fullID format unavailable')
        found[role] = int(ids[0])
    require(found['preexisting'] != found['owned'], 'Original owned/external subjects must be distinct')
    return {'subject_ids': found, 'bytes': len(block), 'sha256': hashlib.sha256(block).hexdigest(),
            'raw_block_hex': block.hex()}


def run_case(context, client):
    initial = client.snapshot()
    proof = scope(client.log_bytes())
    require(initial['played_character']['character_id'] == proof['runtime_character_id'], 'Actual guarded actor differs from original Song scope')
    rows = []
    for day in range(3):
        raw = client.log_bytes()
        observed = observe(raw)
        if observed['qualified']:
            break
        require(day < 2, 'Two focused natural days exhausted; original guard assertions remain missing')
        rows.append(client.advance_day(1, timeout=300))
    final = client.snapshot()
    require(final['played_character']['character_id'] == proof['runtime_character_id'] and
            0 <= final['date_raw'] - initial['date_raw'] < 72, 'Original focused actor/calendar boundary changed')
    enabled = subject_proof(raw, 'enabled'); disabled = subject_proof(raw, 'disabled')
    require(enabled['subject_ids'] == disabled['subject_ids'], 'Guard verification changed subjects between on/off')
    frozen = Path(context['output']) / 'guards-debug-original.raw'
    with frozen.open('xb') as stream:
        stream.write(raw)
    result = {'schema': 'ck3-xqol-focused-guards-observation-v1', 'run_id': context['run_id'],
              'product': 'xqol', 'case': 'guards_focused', 'coverage': 'original_guards_only',
              'actual_actor_scope': proof, 'before': initial, 'after': final,
              'original_natural_day_rows': rows, 'debug_original': pin(frozen),
              'marker_observation': observed, 'enabled_subjects': enabled, 'disabled_subjects': disabled,
              'case_contract_qualified': True, 'gui_contract_qualified': True, 'business_contract_applicable': False,
              'gui_scope': 'No additional GUI assertions in this focused fixture cell; normal GUI Quit still mandatory',
              'business_pass': False, 'product_release_pass': False,
              'does_not_retroactively_rewrite_defense_and_ui_result': True}
    client.checkpoint('xqol-focused-guards-result', result)
    return result


def verify_case(context):
    path = Path(context['output']) / 'xqol-focused-guards-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False, 'business_pass': False, 'status': 'NOT_RUN'}
    result = read(path)
    require(result['run_id'] == context['run_id'] and result['case'] == 'guards_focused', 'Focused result crossed actual run/case')
    require(pin(result['debug_original']['path']) == result['debug_original'], 'Actual original guard log bytes changed')
    raw = Path(result['debug_original']['path']).read_bytes()
    require(observe(raw)['qualified'] and scope(raw) == result['actual_actor_scope'], 'Original actual guard assertions/scope not proved')
    require(subject_proof(raw, 'enabled') == result['enabled_subjects'] and
            subject_proof(raw, 'disabled') == result['disabled_subjects'] and
            result['enabled_subjects']['subject_ids'] == result['disabled_subjects']['subject_ids'], 'Actual original guard subject proof changed')
    return {**result, 'business_pass': False, 'product_release_pass': False,
            'aggregation_scope': 'Focused guard supplement only; Root must retain original R33 GAP/partial facts and shared normal0 evidence'}
