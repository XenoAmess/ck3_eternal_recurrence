"""Original religion gates and Rite outcomes on the one shared runtime."""
from __future__ import annotations
import json
from pathlib import Path
import shutil

from ck3_mod_acceptance_prepare import materialize_fixture_profile, pin, write_json
from .xqol_scope import parse_song_scope

MARKERS = {
    'begin': 'ZQREL: SCOPE BEGIN actual_song_actor',
    'pass': 'ZQREL: SCOPE PASS actual_song_actor',
    'end': 'ZQREL: SCOPE END actual_song_actor',
    'fail': 'ZQREL: TEST FAIL actual_song_actor',
}
BUDGETS = {'command_timeout': 300, 'readiness_timeout': 400, 'timeout': 3000,
           'poll_interval': 0.05, 'hold_seconds': 1800}


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def scope(raw):
    proof = parse_song_scope(raw, {'scope_name': 'xqol_startup_actor', 'markers': MARKERS})
    require(proof is not None, 'Actual original Song religion scope proof is missing')
    return proof


def validate_contract(context):
    contract = context['case_contract']
    require(context['case'] == contract['case'] and contract['formal_file_count'] == 27,
            'Original religion case/formal27 contract differs')
    require(context['case_spec']['budgets'] == BUDGETS, 'Original QOL wall-clock budget changed')
    require(contract['maximum_natural_days'] == (60 if context['case'] == 'religion_rite_outcomes' else 0),
            'Original religion calendar boundary changed')


def prepare_case(context):
    validate_contract(context)
    contract = context['case_contract']
    output = Path(context['output'])
    original = Path(context['repo_root']) / 'tools/ck3_mod_acceptance_cases/xqol_religion_cases' / contract['case'] / 'fixture'
    fixture = output / 'original-religion-fixture'
    shutil.copytree(original, fixture)
    profile = materialize_fixture_profile(context, fixture, context['case_inputs']['product_dir'],
                                          context['case_inputs']['plain_configuration'])
    actual = {key.removeprefix('mod-content/product/'): row for key, row in profile['files'].items()
              if key.startswith('mod-content/product/')}
    expected = context['case_inputs']['formal_product_files']
    require(len(actual) == len(expected) == 27 and set(actual) == set(expected) and all(
        all(actual[key][field] == expected[key][field] for field in ('bytes', 'sha256')) for key in expected),
        'Existing formal27 changed; no builder or replacement product is admitted')
    hook = output / 'frontend-fixture-startup-case-contract.json'
    handler = pin(__file__); handler['function'] = 'admit_startup_event'
    dependencies = [pin(path) for path in (Path(__file__).with_name('xqol_scope.py'),
                    Path(__file__).parent.parent / 'ck3_mod_acceptance_prepare.py',
                    Path(__file__).with_name('__init__.py'))]
    write_json(hook, {'schema': 'ck3-frontend-fixture-startup-case-contract-v1',
                     'state_dir': context['state_dir'], 'handler': handler, 'dependencies': dependencies})
    initial = output / 'initial-plan.json'; write_json(initial, {'steps': []})
    return {'startup': {'mode': 'fixture', 'state_dir': profile['state_dir'],
                        'fixture_start_policy': profile['fixture_start_policy'], 'startup_case_contract': pin(hook)},
            'initial_plan': pin(initial), 'profile': profile, 'formal_product_unchanged': True,
            'coverage': contract['acceptance_scope'], 'runtime_status': 'NOT_RUN',
            'business_pass': False, 'product_release_pass': False}


def admit_startup_event(context, snapshot, event_context):
    """Same sole native intro admission as the original public QOL case."""
    log_path = (Path(context['state_dir']) / 'profile/logs/debug.log').resolve()
    raw = log_path.read_bytes()
    proof = scope(raw)
    played = snapshot.get('played_character', {})
    require(played.get('character_id') == proof['runtime_character_id'] and
            played.get('alive') is True and played.get('source') == 'native', 'Actual Song actor differs')
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
            'fallback': False, 'cancel': False}.items()), 'Original typed intro option differs')
    # The original parser/run_case retain full raw hex; startup carries its exact byte reference.
    proof = {key: value for key, value in proof.items() if key != 'raw_scope_block_hex'}
    proof['markers'] = {key: {'literal': marker, 'count': raw.count(marker.encode('ascii'))}
                        for key, marker in MARKERS.items()}
    proof['raw_scope_block_reference'] = {
        'path': str(log_path), 'byte_start': proof['byte_start'], 'byte_end': proof['byte_end'],
        'bytes': proof['byte_end'] - proof['byte_start'], 'sha256': proof['raw_scope_block_sha256']}
    return {'event_instance_id': event['instance_id'], 'option_number': 1,
            'proof': proof, 'business_pass': False}


def observe(raw, contract):
    require(len(raw) <= 64 * 1024 * 1024, 'Original debug log bound exceeded')
    text = raw.decode('utf-8-sig', errors='replace')
    failures = [line for line in text.splitlines() if any(marker in line for marker in contract['forbidden'])]
    counts = {marker: text.count(marker) for marker in contract['required']}
    require(not failures and not any(count > 1 for count in counts.values()), 'Original religion FAIL/duplicate; no replay')
    return {'counts': counts, 'failures': failures, 'qualified': all(count == 1 for count in counts.values())}


def literal_plan(contract):
    steps = []
    for label, literals, expected in (('required', contract['required'], 1), ('forbidden', contract['forbidden'], 0)):
        expectation = {'schema': 'xar.ck3.engine-log-literals/v1', 'exists': True,
                       'log_name': 'debug.log', 'read_only': True}
        for number, literal in enumerate(literals):
            expectation['matches.' + str(number) + '.literal'] = literal
            expectation['matches.' + str(number) + '.line_count'] = expected
        steps.append({'id': contract['case'] + '-' + label + '-literals',
                      'tool': 'ck3_query_engine_log_literals_v1',
                      'args': {'log_name': 'debug.log', 'literals': literals, 'sample_limit': 2}, 'expect': expectation})
    return steps


def run_case(context, client):
    validate_contract(context)
    contract = context['case_contract']
    before = client.snapshot(); proof = scope(client.log_bytes())
    require(before['played_character']['character_id'] == proof['runtime_character_id'] and
            before['date_raw'] == contract['expected_start_date_raw'], 'Original actual D0 actor/calendar not proved')
    days = []
    for day in range(contract['maximum_natural_days'] + 1):
        raw = client.log_bytes(); observed = observe(raw, contract)
        if observed['qualified']:
            break
        require(day < contract['maximum_natural_days'], 'Original religion day limit exhausted; no replay')
        days.append(client.advance_day(1, timeout=300))
    plan = contract.get('original_plan', literal_plan(contract))
    literal_rows = client.execute_plan(plan, contract['case'] + '-original-literals')
    after = client.snapshot()
    require(after['played_character']['character_id'] == proof['runtime_character_id'] and
            after['date_raw'] - before['date_raw'] == sum(row['result']['elapsed_hours'] for row in days),
            'Actual original religion actor/calendar drifted outside submitted natural days')
    frozen = Path(context['output']) / 'religion-debug-original.raw'
    with frozen.open('xb') as stream:
        stream.write(raw)
    result = {'schema': 'ck3-xqol-original-religion-case-observation-v1', 'run_id': context['run_id'],
              'product': 'xqol', 'case': contract['case'], 'coverage': contract['acceptance_scope'],
              'actual_actor_scope': proof, 'before': before, 'after': after, 'natural_days': days,
              'debug_original': pin(frozen), 'marker_observation': observed, 'literal_rows': literal_rows,
              'gaps': contract['gaps'], 'case_contract_qualified': True, 'gui_contract_qualified': True,
              'gui_scope': 'No GUI business claim in this scoped cell; shared normal GUI Quit remains required',
              'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False}
    client.checkpoint('xqol-religion-result', result)
    return result


def verify_case(context):
    path = Path(context['output']) / 'xqol-religion-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False, 'business_pass': False, 'status': 'NOT_RUN'}
    result = read(path); contract = context['case_contract']
    require(result['run_id'] == context['run_id'] and result['case'] == contract['case'], 'Religion result crossed actual run/case')
    require(pin(result['debug_original']['path']) == result['debug_original'], 'Actual original religion raw bytes changed')
    raw = Path(result['debug_original']['path']).read_bytes()
    require(observe(raw, contract)['qualified'] and scope(raw) == result['actual_actor_scope'], 'Original religion assertions/scope not proved')
    return {**result, 'business_pass': False, 'product_release_pass': False,
            'aggregation_scope': 'Only this original religion boundary; no product/core/GUI/tooltip acceptance inferred'}
