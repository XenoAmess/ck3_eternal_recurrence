"""Reuse product emitters/assertions through the public shared case interfaces.

This module owns no host, bridge, engine identity, process, screen input, queue,
allocator, SDK or cleanup. Those operations belong to the public CaseClient.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import re


def require(value, message):
    if not value:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def literal_inventory(repo, reference):
    """Read existing literal assertion lists; never import a legacy live runner."""
    path = Path(repo) / reference['path']
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == reference['name'] for t in node.targets):
            values = ast.literal_eval(node.value)
            require(isinstance(values, (list, tuple)) and all(isinstance(v, str) for v in values),
                    'Original marker list changed: ' + str(path))
            return list(values), pin(path)
    raise ValueError('Original product assertion list missing: ' + str(path))


def resolve_post_start(context):
    contract = copy.deepcopy(context['case_contract'])
    post = contract['post_start']
    actual = context['case_inputs'].get('post_start', {})
    require(set(actual) <= set(post), 'Unknown ordinary bookmark post-start field')
    for key, value in actual.items():
        require(post[key] is None or post[key] == value, 'Cannot overwrite original product post-start predicate')
        if post[key] is None:
            post[key] = value
    require(all(v is not None for v in post.values()),
            'Original ordinary bookmark government/tier/independence needs actual selected-bookmark input')
    require(type(post['independent']) is bool, 'Actual independence is a strict boolean')
    # Validation/standard tier definitions belong to the one selected helper.
    context = dict(context)
    context['case_contract'] = contract
    return context


def prepare_case(context):
    from ck3_mod_acceptance_prepare import invoke_fixture_prepare, materialize_fixture_profile
    context = resolve_post_start(context)
    config = context['case_contract']
    require(config['product'] == context['product'], 'Case crossed canonical product')
    inputs = context['case_inputs']
    product = Path(inputs['product_dir']).resolve()
    require((product / 'descriptor.mod').is_file(), 'Already built exact product projection required')
    output = Path(context['output'])
    emitter = config.get('fixture_emitter')
    emitted = None
    if emitter:
        generated = output / 'original-fixture-emission'
        args = [s.format(output=str(generated), repo=context['repo_root'], product_dir=str(product))
                for s in emitter['arguments']]
        emitted = invoke_fixture_prepare(context, Path(context['repo_root']) / emitter['path'], args)
        fixture = generated / emitter.get('fixture_subdir', '')
        receipt = read_json(Path(str(generated) + emitter['receipt_suffix']) if 'receipt_suffix' in emitter
                            else generated / emitter['receipt_relative'])
    else:
        # Product-only load boundary: no business effect, actor or marker setter.
        fixture = output / 'empty-load-carrier'
        fixture.mkdir()
        text = (product / 'descriptor.mod').read_text(encoding='utf-8-sig')
        text = re.sub(r'^\s*(?:path|remote_file_id)\s*=.*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*name\s*=.*$', 'name="Acceptance load carrier (no business scripts)"', text, flags=re.MULTILINE)
        (fixture / 'descriptor.mod').write_text(text, encoding='utf-8')
        receipt = {'required_markers': [], 'fixture_contains_business_effects': False}
    required = list(receipt.get('required_markers', receipt.get('expected_pass_markers', [])))
    source_pins = []
    if not required and config.get('marker_inventory'):
        required, source = literal_inventory(context['repo_root'], config['marker_inventory'])
        source_pins.append(source)
    for name in ('required_start', 'required_end', 'required_additional_marker'):
        if receipt.get(name):
            required.append(receipt[name])
    required += receipt.get('required_additional_markers', [])
    required = list(dict.fromkeys(required))
    require(required or config['acceptance_scope'] == 'static_and_basicload', 'Full business case has no original assertions')
    compiled = {
        'schema': 'ck3-mod-acceptance-product-assertions-v1', 'product': context['product'],
        'case': context['case'], 'config': config, 'required_markers': required,
        'product_marker_minimum': receipt.get('required_product_markers_minimum', {}),
        'original_receipt': receipt, 'assertion_source_pins': source_pins,
        'emitter': emitted, 'product_descriptor': pin(product / 'descriptor.mod'),
        'whole_product_release_pass': False,
    }
    write_once(fixture / '_case_contract.json', compiled)
    profile = materialize_fixture_profile(context, fixture, product, inputs['plain_configuration'])
    initial = output / 'initial-plan.json'
    write_once(initial, {'steps': []})
    startup = {'mode': 'fixture', 'state_dir': profile['state_dir'],
               'fixture_start_policy': profile['fixture_start_policy']}
    if config.get('frontend_rules'):
        rules = output / 'frontend-rules-plan.json'
        write_once(rules, {'schema': 'ck3-frontend-rules-plan-v1', 'schema_version': 1,
                           'rules': config['frontend_rules']})
        startup['frontend_rules_plan'] = str(rules)
    return {'startup': startup,
            'initial_plan': pin(initial), 'profile_preparation': profile,
            'assertion_contract': pin(Path(profile['profile']) / 'mod-content/fixture/_case_contract.json'),
            'business_contract_applicable': config['acceptance_scope'] != 'static_and_basicload',
            'runtime_status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False}


def compiled_contract(context):
    path = Path(context['state_dir']) / 'profile/mod-content/fixture/_case_contract.json'
    contract = read_json(path)
    require(contract['product'] == context['product'] and contract['case'] == context['case'],
            'Prepared assertion contract crossed product/case')
    return contract, pin(path)


def marker_observation(raw, compiled):
    text = raw.decode('utf-8-sig', errors='replace')
    counts = {marker: text.count(marker) for marker in compiled['required_markers']}
    duplicate = {marker: count for marker, count in counts.items() if count > 1}
    missing = [marker for marker, count in counts.items() if count == 0]
    minima = {marker: {'actual': text.count(marker), 'minimum': minimum}
              for marker, minimum in compiled['product_marker_minimum'].items()}
    failures = [line for line in text.splitlines() if any(prefix in line for prefix in compiled['config']['failure_prefixes'])
                and any(token in line for token in ('TEST FAIL', 'MECHANISM CASE FAIL', ': FAIL '))]
    return {'counts': counts, 'missing': missing, 'duplicates': duplicate, 'failure_lines': failures,
            'product_marker_minimum': minima, 'qualified': not missing and not duplicate and not failures
            and all(v['actual'] >= v['minimum'] for v in minima.values())}


def root_phase(client, context, name, requirements, snapshot, source_contract):
    response = client.root_checkpoint(name, {
        'product': context['product'], 'case': context['case'], 'scope': source_contract['config']['acceptance_scope'],
        'action': 'Use original production UI / typed current context and original verifiers; preserve actual evidence',
        'required_assertions': requirements, 'actual_snapshot': snapshot,
        'original_contract_sources': source_contract['config']['source_contracts'],
        'no_business_PASS_from_ACK': True, 'no_replay_after_submission': True,
    }, reserve=90)
    require(response.get('run_id') == context['run_id'] and response.get('reviewer') == '/root', 'Root phase crossed live scene')
    assertions = response.get('assertions', {})
    require(all(assertions.get(key) is True for key in requirements), 'Original product GUI/semantic requirements incomplete')
    require(response.get('evidence'), 'Actual original GUI/readback evidence required')
    for row in response['evidence']:
        actual = pin(row['path'])
        require(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'].lower(), 'Root evidence bytes changed')
    client.checkpoint(name + '-accepted', response)
    return response


def run_case(context, client):
    compiled, binding = compiled_contract(context)
    config = compiled['config']
    frame = client.snapshot(require_event_free=False)
    frames = [{'day': 0, 'snapshot': frame}]
    initial_date = frame.get('date_raw')
    require(type(initial_date) is int, 'Actual initial native calendar is required')
    phases = {}
    static_load_only = config['acceptance_scope'] == 'static_and_basicload'
    profile = Path(context['state_dir']) / 'profile'
    enabled = read_json(profile / 'dlc_load.json')['enabled_mods']
    require('mod/product.mod' in enabled, 'Actual prepared product is not mounted')
    require((profile / 'mod/product.mod').is_file() and (profile / 'mod-content/product/descriptor.mod').is_file(),
            'Actual product descriptors missing')
    observed = {'qualified': static_load_only, 'counts': {}, 'missing': [], 'duplicates': {}, 'failure_lines': [], 'product_marker_minimum': {}}
    if not static_load_only:
        sequence = 0
        while True:
            require(type(frame.get('date_raw')) is int and frame['date_raw'] >= initial_date,
                    'Actual native calendar moved backwards')
            day = (frame['date_raw'] - initial_date) / 24
            require(day <= config['maximum_natural_days'], 'Shared case natural calendar upper bound exceeded')
            observed = marker_observation(client.log_bytes(), compiled)
            require(not observed['failure_lines'] and not observed['duplicates'], 'Original product fixture failed; never replay')
            for phase in config['gui_phases']:
                if phase['id'] in phases:
                    continue
                ready = (phase.get('at_day') is not None and day >= phase['at_day']) or any(
                    observed['counts'].get(marker, 0) for marker in phase.get('when_markers', []))
                if ready:
                    phases[phase['id']] = root_phase(client, context, phase['id'], phase['requirements'], frame, compiled)
                    frame = client.snapshot(allow_actor_change=config.get('allow_actor_change', False), require_event_free=False)
                    frames.append({'day': day, 'after_gui': phase['id'], 'snapshot': frame})
                    require(type(frame.get('date_raw')) is int and frame['date_raw'] >= initial_date,
                            'Actual native calendar after GUI is required')
                    day = (frame['date_raw'] - initial_date) / 24
                    require(day <= config['maximum_natural_days'], 'GUI phase exceeded shared case calendar bound')
                    observed = marker_observation(client.log_bytes(), compiled)
            if observed['qualified'] and all(phase['id'] in phases for phase in config['gui_phases']):
                break
            require(day < config['maximum_natural_days'], 'Shared case day upper bound reached; missing original product assertions retained')
            # An actual event is handled by Root from its current instance. Never
            # invent an option index or claim that dispatch proves a GUI outcome.
            if frame.get('active_event') is not None:
                name = 'actual-event-boundary-' + str(sequence).zfill(3)
                phases[name] = root_phase(client, context, name, ['actual_current_event_resolved_with_typed_or_reviewed_original_evidence'], frame, compiled)
                frame = client.snapshot(allow_actor_change=config.get('allow_actor_change', False), require_event_free=True)
            sequence += 1
            step = {'id': 'product-natural-day-' + str(sequence).zfill(3), 'kind': 'advance_day',
                     'days': 1, 'timeout': context['case_spec']['budgets']['command_timeout']}
            if sequence in config.get('actor_transition_days', []):
                step['wait_for_played_character_change'] = True
            rows = client.execute_plan([step], step['id'])
            value = rows[0]['result']
            require(value.get('requested_days') == 1 and
                    (value.get('requested_interval_complete') is True or value.get('event_boundary') is not None),
                    'Neither actual day completion nor an actual event boundary was observed')
            before, after = value['before'], value['after']
            require(type(after.get('date_raw')) is int and type(before.get('date_raw')) is int,
                    'Actual natural interval is missing native calendar fields')
            elapsed = after['date_raw'] - before['date_raw']
            require(
                    ((24 <= elapsed < 48) if value.get('requested_interval_complete') is True
                     else 0 <= elapsed < 48), 'Actual natural interval/event boundary is malformed')
            if after.get('played_character', {}).get('alive') is False and config.get('continue_as_heir_requirements'):
                phases['original-continue-as-heir'] = root_phase(client, context, 'original-continue-as-heir',
                    config['continue_as_heir_requirements'], after, compiled)
            # Full actual rows remain retained by the common client. Refresh from
            # the same live owner, admitting only the original actor transition.
            frame = client.snapshot(allow_actor_change=config.get('allow_actor_change', False), require_event_free=False)
            frames.append({'day': (frame['date_raw'] - initial_date) / 24, 'sequence': sequence, 'snapshot': frame})
        observed = marker_observation(client.log_bytes(), compiled)
        require(observed['qualified'], 'Original marker assertions remain incomplete after GUI/day work')
    process = getattr(client, '_process', None)
    facts = {'schema': 'ck3-mod-acceptance-product-case-facts-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'compiled_contract': binding,
        'acceptance_scope': config['acceptance_scope'], 'business_contract_applicable': not static_load_only,
        'load_boundary_qualified': True, 'actual_native_frames': frames, 'actual_process': process,
        'enabled_mods': enabled, 'product_outer': pin(profile / 'mod/product.mod'),
        'product_inner': pin(profile / 'mod-content/product/descriptor.mod'),
        'marker_observation': observed, 'root_phases': phases,
        'case_contract_qualified': observed['qualified'], 'gui_contract_qualified': static_load_only or all(
            phase['id'] in phases for phase in config['gui_phases']),
        'result_boundary': 'LOAD_BOUNDARY_PASS' if static_load_only else 'SOURCE_CASE_OBSERVED_PENDING_PRODUCT_AGGREGATION',
        'pending_product_business': config.get('uncovered_product_business', []),
        'business_pass': False, 'product_release_pass': False}
    client.checkpoint('generic-product-case-result', facts)
    return facts


def verify_case(context):
    path = Path(context['output']) / 'generic-product-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False,
                'business_pass': False, 'product_release_pass': False, 'status': 'NOT_RUN'}
    facts = read_json(path)
    require(facts['run_id'] == context['run_id'] and facts['product'] == context['product'] and facts['case'] == context['case'],
            'Original actual case result crossed run/product/case')
    compiled, binding = compiled_contract(context)
    require(binding == facts['compiled_contract'], 'Prepared original assertion contract changed')
    for phase in facts['root_phases'].values():
        require(phase.get('run_id') == context['run_id'] and phase.get('reviewer') == '/root', 'Root evidence crossed session')
        for row in phase['evidence']:
            actual = pin(row['path'])
            require(actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'].lower(), 'Root evidence changed')
    # Complete product release aggregation is owned by Root, including distinct
    # business cells, current version credit and publication/cache obligations.
    result = copy.deepcopy(facts)
    result.update(business_pass=False, product_release_pass=False,
                  verification_scope=compiled['config']['acceptance_scope'])
    return result
