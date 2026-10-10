"""One paused formal I3b B4 commit, with fresh B3 and complete saved protection.

Historical B3 qualifies the seed's origin. It cannot replace the current
typed review, fresh G2/G3, saved precommit state or the original full checks.
The shared entry alone owns startup, budgets and original normal closure.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import time


def require(value, message):
    if not value:
        raise ValueError(message)


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def contract():
    return load_json(Path(__file__).with_name('lyd_i3b_formal_b4.json'))


def _control():
    path = Path(__file__).with_name('lyd_transaction_control_adapter.py')
    spec = importlib.util.spec_from_file_location('_lyd_i3b_shared_case_primitives', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_contract(context):
    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == 'i3b-formal-b4', 'Formal B4 selection differs')
    require(data == contract() and data['business_contract_applicable'] is True and
            data['maximum_natural_days'] == 0, 'Frozen formal paused contract differs')


def checked_input(inputs, key, data):
    row = inputs[key]
    require({k: row[k] for k in ('bytes', 'sha256')} == data['input_pins'][key],
            'Reviewed formal input signature differs: ' + key)
    return _control()._checked_json(row)


def validate_origin(inputs, seed, data):
    require({k: seed[k] for k in data['saved_campaign']} == data['saved_campaign'], 'Signed seed differs')
    origin = checked_input(inputs, 'formal_b3_qualification', data)
    require(origin.get('qualification_status') == 'FORMAL_NATIVE_CALLBACK_SAVED_MANDATE_PASS' and
            origin.get('qualification_pass') is True and origin.get('formal_mandate_credit') is True and
            origin.get('actual_checkpoint_sha256') == seed['sha256'] and
            origin.get('actor_id') == data['expected']['actor_character_id'] and
            origin.get('actual_round') == {**data['round'], 'result_code': None} and
            origin.get('missing_actual_observations') == [], 'Seed has no complete signed formal origin')
    baseline = checked_input(inputs, 'protection_baseline', data)
    request = checked_input(inputs, 'reader_request', data)
    require(baseline['schema'] == 'lyd.i3b0240.cached-baseline.v1' and
            sorted(map(int, baseline['political7'])) == data['political_title_ids'] and
            request['schema'] == 'lyd.i3b.checkpoint-reader-request.v2' and
            request['stage'] == 'signed_precommit' and request['expected'] == data['round'] and
            request['save']['sha256'] == seed['sha256'], 'Original complete protection/reader input differs')
    return origin, baseline, request


def prepare_case(context):
    from ck3_mod_acceptance_prepare import CONFIG_NAMES, checked_copy, pin, write_json, _outer_from_inner
    validate_contract(context)
    data, inputs, seed = context['case_contract'], context['case_inputs'], context['saved_campaign']
    require(set(inputs) == {'product_dir', 'product_inventory', 'plain_configuration',
                            'formal_b3_qualification', 'protection_baseline', 'reader_request'},
            'Formal B4 requires only the formal product and complete signed/protection inputs')
    require(set(inputs['plain_configuration']) == set(CONFIG_NAMES), 'Four explicit configurations required')
    validate_origin(inputs, seed, data)
    seed_path, state, output = Path(seed['save']).resolve(), Path(context['state_dir']).resolve(), Path(context['output']).resolve()
    require(seed_path.is_file() and seed_path.stat().st_size == seed['bytes'] and
            not state.exists() and not seed_path.is_relative_to(state), 'Unused profile/external signed seed required')
    control = _control()
    production = control._checked_json(inputs['product_inventory'])
    require(production['source_head'] == data['production_source_head'], 'Reviewed formal source differs')
    product = Path(inputs['product_dir']).resolve()
    product_rows = control._inventory_rows(product, production['files'], data['production_file_count'])
    profile, target = state / 'profile', state / 'profile/mod-content/product'
    profile.mkdir(parents=True)
    for name in CONFIG_NAMES:
        checked_copy(inputs['plain_configuration'][name], profile / name)
    for row in product_rows:
        checked_copy(row, target / Path(row['path']).relative_to(product))
    outer = profile / 'mod/product.mod'
    outer.parent.mkdir(exist_ok=True)
    with outer.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_outer_from_inner(target / 'descriptor.mod', target))
    enabled = ['mod/product.mod']
    write_json(profile / 'dlc_load.json', {'enabled_mods': enabled, 'disabled_dlcs': []})
    inventory = output / 'saved-product-inventory.json'
    write_json(inventory, {'schema': 'ck3-saved-campaign-product-only-profile-v1',
        'profile_path': str(profile), 'enabled_mods': enabled,
        'product_files': [pin(outer), *[pin(p) for p in sorted(target.rglob('*')) if p.is_file()]]})
    files = {p.relative_to(profile).as_posix(): pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    prepared = output / 'profile-preparation.json'
    write_json(prepared, {'schema': 'ck3-mod-acceptance-prepared-i3b-formal-b4-v1',
        'state_dir': str(state), 'profile_dir': str(profile), 'files': files,
        'formal_inputs': inputs, 'saved_campaign': seed, 'saved_product_inventory': pin(inventory),
        'runtime_status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False})
    startup = state / 'preparation.json'
    write_json(startup, {'schema': 'ck3-mod-acceptance-profile-startup-evidence-v1',
        'profile_dir': str(profile), 'profile_files': list(files),
        'profile_input_sha256': {name: row['sha256'] for name, row in files.items()},
        'preparation': pin(prepared), 'runtime_status': 'NOT_RUN'})
    hook = output / 'saved-startup-case-contract.json'
    write_json(hook, {'schema': 'ck3-saved-campaign-startup-case-contract-v1', 'state_dir': str(state),
        'handler': {**pin(__file__), 'function': 'admit_saved_startup_event'},
        'dependencies': [pin(Path(__file__).with_name('lyd_i3b_formal_b4.json')),
                         pin(Path(__file__).with_name('lyd_transaction_control_adapter.py'))],
        'expected': data['expected']})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': str(state),
        'saved_campaign': {**seed, 'save': str(seed_path), 'product_inventory': str(inventory)},
        'saved_campaign_startup_case_contract': str(hook)}, 'initial_plan': pin(initial),
        'profile_preparation': pin(prepared), 'startup_evidence': pin(startup), 'files': files,
        'runtime_status': 'NOT_RUN', 'business_contract_applicable': True,
        'business_pass': False, 'product_release_pass': False}


def observe_event(frame, packet, expected, data, *, result=False):
    # The existing typed/current frame, option and actor checks are reused.
    # Formal events contain an actor scope and numeric terms, without a pre-created Title.
    control = _control()
    require(frame.get('paused') is True and frame.get('map_ready') is True and
            frame.get('episode_projection') == 'native_campaign' and
            frame.get('played_character', {}).get('character_id') == expected['actor_character_id'] and
            frame.get('date_raw') == expected['date_raw'] and
            frame.get('active_event', {}).get('instance_id') == expected['event_instance_id'],
            'Actual paused actor/date/event differs')
    for key, frame_key in (('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'),
                            ('queried_native_revision', 'native_revision')):
        require(type(packet.get(key)) is type(frame[frame_key]) and packet[key] == frame[frame_key], 'Typed event frame differs')
    event = packet.get('current_event_window_context', {})
    require(packet.get('status') == 'available' and event.get('status') == 'available' and
            event.get('schema') == 'current-event-window-context-v1' and event.get('window_match_count') == 1 and
            event.get('event_definition_key') == expected['event_definition_key'] and
            event.get('current_event_instance_id') == expected['event_instance_id'] and
            event.get('snapshot_revision') == frame['native_revision'] and event.get('date_raw') == frame['date_raw'],
            'Current formal definition/instance/frame unavailable')
    control._scope(event.get('root_scope'), 'character', 'character_id', expected['root_character_id'])
    scopes = event.get('saved_scopes', [])
    def unique(name):
        rows = [row.get('scope') for row in scopes if row.get('name') == name]
        require(len(rows) == 1, 'Unique formal scope required: ' + name)
        return rows[0]
    control._scope(unique('lyd_i3b_actor'), 'character', 'character_id', expected['actor_character_id'])
    prefix = 'lyd_i3b_result_event_' if result else 'lyd_i3b_event_'
    numeric = {}
    for key in ('serial', 'nonce') if result else ('serial', 'nonce', 'phase'):
        scope = unique(prefix + key)
        value = scope.get('numeric_value', {})
        wanted = data['round'][key]
        require(scope.get('status') == 'available' and scope.get('type_key') == 'value' and
                value == {'raw_fixed_point': str(wanted * 100000), 'scale': 100000,
                          'decimal_value': str(wanted), 'integer_value': str(wanted)}, 'Actual numeric formal scope differs: ' + key)
        numeric[key] = wanted
    require(all(event.get('readiness', {}).get(k) is True for k in
                ('event_definition_identity_ready', 'root_scope_ready', 'saved_scopes_ready', 'option_presentation_ready')),
            'Complete formal identity/option presentation unavailable')
    options = event.get('options', [])
    require(len(options) == len(expected['native_option_indices']), 'Exact formal option census differs')
    for rendered, (row, index) in enumerate(zip(options, expected['native_option_indices'])):
        require(type(row.get('native_option_index')) is int and row['native_option_index'] == index and
                type(row.get('rendered_index')) is int and row['rendered_index'] == rendered and
                row.get('shown') is True and row.get('enabled') is True and
                row.get('fallback') is False and row.get('cancel') is False, 'Formal enabled option identity differs')
    return {'event_definition_key': expected['event_definition_key'], 'event_instance_id': expected['event_instance_id'],
        'root_character_id': expected['root_character_id'], 'native_option_indices': expected['native_option_indices'],
        'actual_numeric_terms': numeric, 'queried_revision': frame['revision'],
        'queried_native_revision': frame['native_revision'], 'actions_submitted': 0}


def admit_saved_startup_event(context, snapshot, typed_event_packet):
    data = contract()
    require(context['expected'] == data['expected'], 'Saved formal startup identity differs')
    proof = observe_event(snapshot, typed_event_packet, context['expected'], data)
    return {**context['expected'], 'proof': proof, 'business_pass': False}


def observe_query(frame, query, nested):
    for key, actual in {'queried_snapshot_id': frame['snapshot_id'], 'queried_revision': frame['revision'],
        'queried_native_revision': frame['native_revision'], 'date_raw': frame['date_raw'],
        'game_pid': frame['diagnostics']['bridge_pid'],
        'connection_generation': frame['diagnostics']['connection_generation'],
        'player_character_id': frame['played_character']['character_id']}.items():
        require(type(query.get(key)) is type(actual) and query[key] == actual, 'Read-only query crossed actual frame: ' + key)
    payload = query.get('native_result', {}).get(nested, {})
    require(payload.get('available') is True and payload.get('date_raw') == frame['date_raw'], 'Actual native query unavailable')
    return payload


def observe_cache(frame, query):
    payload = observe_query(frame, query, 'actor_cached_succession')
    ids = payload.get('complete_cached_successor_ids')
    require(payload.get('read_only') is True and payload.get('roster_complete') is True and
            isinstance(ids, list) and all(type(i) is int and 0 < i < 2**32-1 for i in ids) and
            len(set(ids)) == len(ids) == payload.get('native_count'), 'Complete ordered actual cache required')
    return ids


def observe_title(frame, query, data, *, absent):
    payload = observe_query(frame, query, 'confucian_religious_title')
    require(payload.get('graph_available') is True and payload.get('faith_full_id') == data['faith_id'] and
            payload.get('legal_head_title_absent') is absent, 'Actual religious Title presence/Faith differs')
    if absent:
        require(payload.get('head_title_full_id') is None and payload.get('native_title_holder_full_id') is None,
                'Precommit native head must be absent')
    return payload


def native_predicates(frame, query, identity, checkpoint_sha, data, reader):
    payload = observe_query(frame, query, 'confucian_assembly_predicates')
    require(payload.get('read_only') is True and payload.get('predicates_complete') is True and
            payload.get('faith_id') == data['faith_id'] and payload.get('played_rite_id') == data['main_rite_id'],
            'Complete fresh native assembly predicates required')
    ids, rites = payload['complete_native_faith_member_ids'], payload['complete_native_faith_rite_ids']
    members, rite_rows = payload['members'], payload['rites']
    require(len(ids) == len(set(ids)) == data['faith_member_count'] and
            [row['character_id'] for row in members] == ids and rites == [data['main_rite_id']] and
            [row['rite_id'] for row in rite_rows] == rites, 'Complete fresh native Faith roster differs')
    require(all(row.get('complete') is True and row.get('alive') is True and
                row.get('faith_id') == data['faith_id'] and row.get('rite_id') in rites and
                all(type(row.get(k)) is bool for k in ('adult', 'imprisoned', 'incapable', 'is_ai')) and
                type(row.get('effective_learning')) is int for row in members) and
            all(row.get('complete') is True and row['native_county_count'] == len(row['county_title_ids']) for row in rite_rows),
            'Incomplete actual member/county predicates')
    return {'schema': 'lyd.i3b.native-predicates.v1', 'source_head': reader.HEAD,
        'checkpoint_sha256': checkpoint_sha, 'identity': identity, 'complete_current_faith_roster': True,
        'human_character_ids': [row['character_id'] for row in members if row['is_ai'] is False],
        'characters': [{**{k: row[k] for k in ('character_id', 'alive', 'adult', 'imprisoned', 'incapable', 'is_ai')},
                        'learning': row['effective_learning']} for row in members],
        'rite_counties': {str(row['rite_id']): row['native_county_count'] for row in rite_rows},
        'evidence_sha256': hashlib.sha256(json.dumps(query, sort_keys=True).encode()).hexdigest()}


def read_saved(context, checkpoint, frame, assembly, title_query, data, *, post):
    control = _control()
    inputs = context['case_inputs']
    origin, baseline, request = validate_origin(inputs, context['saved_campaign'], data)
    require(checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == data['expected']['date_raw'] and
            checkpoint.get('episode_projection') == 'native_campaign', 'Actual original paused checkpoint required')
    path = Path(checkpoint['path']).resolve()
    require(path != Path(context['saved_campaign']['save']).resolve(), 'Original signed seed cannot be the new SAVE output')
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    require(len(raw) == checkpoint['size'] and sha == checkpoint['sha256'] and not raw.startswith(b'PK'),
            'Actual new plain checkpoint bytes/SHA differs')
    preserved = Path(context['output']) / 'checkpoints' / ('B4-factory-result.ck3' if post else 'B3-fresh-signed.ck3')
    preserved.parent.mkdir(parents=True, exist_ok=True)
    with preserved.open('xb') as stream:
        stream.write(raw)
    reader = control._reader(context['repo_root'])
    identity = {'actor_id': data['expected']['actor_character_id'], 'faith_id': data['faith_id'],
        'main_rite_id': data['main_rite_id'], 'pid': frame['diagnostics']['bridge_pid'],
        'session_id': context['run_id'], 'revision': frame['revision'], 'checkpoint_id': str(path)}
    request.update(mode='future_actual', stage='success_postcommit' if post else 'signed_precommit',
        identity=identity, save={'path': str(preserved), 'bytes': len(raw), 'sha256': sha}, native_title_binding=None,
        native_reference_binding={'schema': 'lyd.saved-native-reference-binding.v1', 'source_head': reader.HEAD,
            'evidence_sha256': inputs['formal_b3_qualification']['sha256'], 'title_type': 'lt'}, output=None)
    request['native_predicates'] = None if post else native_predicates(frame, assembly, identity, sha, data, reader)
    text = raw.decode('utf-8-sig')
    state = reader.observe_text(text, request, sha)
    scan = raw_scan(text, {'played_character_id': identity['actor_id']}, baseline, reader)
    protection = evaluate_protection(scan, baseline, state, reader)
    expected_protection_count = 88 if post else 87
    require(len(protection['checks']) == expected_protection_count, 'Original complete 87/88 protection census differs')
    if post:
        title = observe_title(frame, title_query, data, absent=False)
        saved_title = state.get('native_title')
        props, laws = title['title_properties'], title['title_laws']
        reader.add_check(state['checks'], 'actual_title_succession_law',
            laws.get('available') is True and laws.get('temporal_head_of_faith_succession_law_member') is True and
            {'native_definition_id': 95, 'key': 'temporal_head_of_faith_succession_law'} in laws.get('complete_laws', []))
        reader.add_check(state['checks'], 'actual_title_four_properties', props.get('available') is True and
            all(props.get(k) is True for k in data['title_properties']))
        reader.add_check(state['checks'], 'fresh_native_saved_title_holder_join', saved_title is not None and
            title.get('head_title_full_id') == saved_title['title_id'] and
            title.get('native_title_holder_full_id') == saved_title['holder'] == identity['actor_id'])
    else:
        observe_title(frame, title_query, data, absent=True)
    saved_ids = [reader.scalar_id(row['value'], 'saved successor') for row in reader.one(state['actor']['landed_data'], 'succession', required=True)]
    return {'stage': state['stage'], 'checkpoint': request['save'], 'identity': identity,
        'saved_business_checks': state['checks'], 'saved_business_match': all(r['matches'] for r in state['checks']),
        'protection_checks': protection['checks'], 'protection_match': protection['protection_checks_match'],
        'complete_cached_successor_ids': saved_ids,
        'new_title_id': state['native_title']['title_id'] if post and state.get('native_title') else None,
        'saved_body_reads': 1, 'baseline_body_reads': 0, 'original_checkpoint_path': str(path),
        'historical_origin_only': inputs['formal_b3_qualification'],
        'formal_institution_pass': False, 'product_release_pass': False}


def _call(client, name, tool, args):
    return _control()._call(client, name, tool, args)


def _fresh_saved_bundle(context, client, data, name, *, post):
    before = client.snapshot(require_event_free=False)
    saved = _call(client, name + '-save', 'ck3_save_checkpoint', {'expected_revision': before['revision']})
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original save not accepted')
    frame = client.snapshot(require_event_free=False)
    require(frame['date_raw'] == before['date_raw'] == data['expected']['date_raw'], 'Paused SAVE changed date')
    assembly = None if post else _call(client, name + '-G2', 'ck3_query_confucian_assembly_predicates_v1', {'expected_revision': frame['revision']})
    title = _call(client, name + '-G3', 'ck3_query_confucian_religious_title_v1', {'expected_revision': frame['revision']})
    facts = read_saved(context, saved['checkpoint'], frame, assembly, title, data, post=post)
    client.checkpoint(name + '-saved-facts', facts)
    return frame, facts


def run_case(context, client):
    validate_contract(context)
    data = context['case_contract']
    client.retain_process()
    before = client.snapshot(require_event_free=False)
    event = _call(client, 'i3b-b4-initial-430', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': data['expected']['event_instance_id'], 'expected_revision': before['revision']})
    observe_event(before, event, data['expected'], data)
    frame, pre = _fresh_saved_bundle(context, client, data, 'i3b-b4-fresh-B3', post=False)
    require(pre['protection_match'] is True and pre['saved_business_match'] is True and
            pre['complete_cached_successor_ids'] == data['baseline_cached_succession'], 'Fresh saved B3/87 protections failed')
    cache_before = observe_cache(frame, _call(client, 'i3b-b4-cache-before', 'ck3_query_actor_cached_succession_v1',
        {'expected_revision': frame['revision']}))
    require(cache_before == pre['complete_cached_successor_ids'], 'Fresh B3 native and saved cache differ')
    review = _call(client, 'i3b-b4-current-430', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': data['expected']['event_instance_id'], 'expected_revision': frame['revision']})
    observe_event(frame, review, data['expected'], data)
    # This sole business mutation is never replayed, including an unknown ACK.
    selected = _call(client, 'i3b-b4-submit-once', 'ck3_select_event_option',
        {'event_instance_id': data['expected']['event_instance_id'], 'option_number': 1, 'expected_revision': frame['revision']})
    require(selected.get('accepted') is True and selected.get('option_index') == 0 and
            selected.get('option_number') == 1 and selected.get('event_instance_id') == data['expected']['event_instance_id'],
            'Single formal submit identity/ACK differs; never replay')
    cutoff = time.monotonic() + min(60, client.guard() - 90)
    while True:
        after = client.snapshot(require_event_free=False)
        require(after['date_raw'] == data['expected']['date_raw'], 'Formal submit advanced date')
        instance = (after.get('active_event') or {}).get('instance_id')
        if type(instance) is int and instance != data['expected']['event_instance_id']:
            break
        require(time.monotonic() < cutoff, 'Original 60s terminal deadline elapsed; submit never replayed')
        time.sleep(.5)
    packet = _call(client, 'i3b-b4-terminal-event', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': instance, 'expected_revision': after['revision']})
    terminal_expected = {**data['expected'], 'event_definition_key': 'lyd.431',
        'event_instance_id': instance, 'native_option_indices': [0]}
    terminal = observe_event(after, packet, terminal_expected, data, result=True)
    cache_after = observe_cache(after, _call(client, 'i3b-b4-cache-after', 'ck3_query_actor_cached_succession_v1',
        {'expected_revision': after['revision']}))
    # A complete but changed native cache is RED; still preserve the B4 SAVE/checks.
    _, post = _fresh_saved_bundle(context, client, data, 'i3b-b4-post', post=True)
    passed = (post['protection_match'] is True and post['saved_business_match'] is True and
              cache_after == cache_before == post['complete_cached_successor_ids'])
    facts = {'schema': 'ck3-lyd-i3b-formal-b4-result-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'case_contract_qualified': passed,
        'gui_contract_qualified': passed, 'business_contract_applicable': True, 'business_pass': passed,
        'B4_pass': passed, 'B5_pass': False, 'formal_institution_pass': False, 'C3_pass': False, 'I4_pass': False,
        'product_release_pass': False, 'normal_close': 'PENDING_SHARED_ORIGINAL_CLOSE',
        'business_actions_submitted': 1, 'selected_option_number': 1, 'terminal': terminal,
        'cache_before_ids': cache_before, 'cache_after_ids': cache_after, 'fresh_B3': pre, 'B4': post,
        'next_B5_requires': 'new cold run with this exact B4 PASS, saved checkpoint and dynamic Title pins'}
    client.checkpoint('i3b-formal-b4-case-result', facts)
    return facts


def verify_case(context, client=None):
    validate_contract(context)
    path = Path(context['output']) / 'i3b-formal-b4-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False,
            'business_contract_applicable': True, 'business_pass': False, 'product_release_pass': False,
            'status': 'NOT_RUN_OR_PRESERVED_FAILURE'}
    facts, data = load_json(path), context['case_contract']
    require(all(facts.get(k) == context[k] for k in ('run_id', 'product', 'case')), 'B4 result crossed case/run')
    require(facts.get('business_actions_submitted') == 1 and facts.get('selected_option_number') == 1,
            'Once-only formal submit proof absent')
    for key, count in (('fresh_B3', 87), ('B4', 88)):
        saved = facts[key]
        require(len(saved['protection_checks']) == count and
                saved['protection_match'] is all(row['matches'] is True for row in saved['protection_checks']) and
                saved['saved_business_match'] is all(row['matches'] is True for row in saved['saved_business_checks']),
                'Full saved checks/assessment disagree')
    expected = (facts['fresh_B3']['protection_match'] is True and facts['fresh_B3']['saved_business_match'] is True and
        facts['B4']['protection_match'] is True and facts['B4']['saved_business_match'] is True and
        facts['cache_before_ids'] == facts['cache_after_ids'] == data['baseline_cached_succession'] ==
        facts['B4']['complete_cached_successor_ids'])
    require(facts.get('business_pass') is expected and facts.get('B4_pass') is expected, 'B4 result assessment differs')
    return {**facts, 'formal_institution_pass': False, 'B5_pass': False, 'C3_pass': False,
        'I4_pass': False, 'product_release_pass': False,
        'verification_scope': 'formal B4 only; original shared normal-close and a separate B5 cold run remain required'}


# Existing R29 complete protection comparisons; only explicit reader injection changed.
need = require

def exact_number(value):
    if value is None:return None
    if isinstance(value,list):
        need(len(value)==1 and value[0]['key']=='value','unsupported actual resource numeric structure')
        value=value[0]['value']
    need(isinstance(value,str),'unsupported actual resource numeric shape')
    return str(Decimal(value))


def raw_scan(text,binding,original_baseline,reader):
    """Actual save framing/AST helpers are unchanged existing reader functions."""
    text=text.replace('\r\n','\n')
    faiths=reader.graph(text,'faiths','main_rite');rites=reader.graph(text,'rites','faith')
    parents={rid:reader.scalar_id(row['faith'],'Rite parent',absent=True,allow_zero=True) for rid,row in rites.items()}
    actor_id=reader.valid_id(binding['played_character_id'], 'saved played actor')
    living={};count=0;section_count=0;excluded_explicit_dead=[];unclassified=[]
    protected_ids={int(k) for k in original_baseline['character_protections']}
    # Faith is taken from the actual played actor's saved Rite, never a hint.
    actor=None
    for cid,entries in reader.records(reader.section(text,'living','dead_unprunable'),'living character'):
        section_count+=1
        if not reader.saved_character_is_alive(cid,entries):
            excluded_explicit_dead.append({'character_id':cid,'AST_sha256':reader.ast_sha(entries),'dead_data':reader.one(entries,'dead_data')})
            continue
        count+=1
        row=reader.raw_character(cid,entries)
        if row['rite_id'] is None or row['rite_id'] not in parents or parents[row['rite_id']] is None:
            unclassified.append(cid)
        if cid==actor_id:actor=row
        # Keep compact membership identities for all world living records. Full
        # ASTs are retained only for current Faith members/protected characters.
        living[cid]={'rite_id':row['rite_id'],'faith_id':parents.get(row['rite_id'])}
        if cid in protected_ids:living[cid]['record']=row
    need(actor is not None,'actual played actor is not a living saved record')
    rite_id=actor['rite_id'];faith_id=parents.get(rite_id)
    need(faith_id is not None and faith_id in faiths,'actual saved actor Faith/Rite not classifiable')
    # Full selected Faith ASTs require a second numeric-record pass on the same
    # verified byte buffer, never a second file read or altered parser.
    selected_ids={cid for cid,row in living.items() if row['faith_id']==faith_id}|protected_ids
    selected={actor_id:actor}
    for cid,entries in reader.records(reader.section(text,'living','dead_unprunable'),'living character'):
        if cid in selected_ids: selected[cid]=reader.raw_character(cid,entries)
    faith_members=sorted(cid for cid,row in living.items() if row['faith_id']==faith_id)
    actual_rites=sorted(rid for rid,fid in parents.items() if fid==faith_id)
    humans=[reader.scalar_id(r['value'],'saved currently played character') for r in reader.exact_root_block(text,'currently_played_characters')]
    current_head=reader.saved_faith_religious_title_reference(faiths[faith_id],faith_id)['full_id']
    held_by_protected={cid:[] for cid in protected_ids};titles={}
    political_ids={int(k) for k in original_baseline['political7']}
    for tid,entries in reader.title_database_records(text):
        holder=reader.native_link_id(reader.one(entries,'holder'),'saved Title holder')
        if holder in held_by_protected:held_by_protected[holder].append(tid)
        if tid in political_ids or tid==current_head:titles[tid]=reader.title_row(tid,entries)
    return {'text':text,'actor':actor,'faith_id':faith_id,'rite_id':rite_id,'faiths':faiths,'rites':rites,
            'parents':parents,'selected':selected,'living_count':count,'living_section_count':section_count,'excluded_explicit_dead':excluded_explicit_dead,'unclassified':unclassified,
            'faith_members':faith_members,'actual_rites':actual_rites,'humans':humans,
            'titles':titles,'current_head':current_head,'held_by_protected':held_by_protected}


def evaluate_protection(scan,baseline,state,reader):
    checks=[]
    def compare(name,actual,wanted):
        checks.append({'name':name,'matches':actual==wanted,'observed':actual,'expected':wanted})
    for tid,expected in baseline['political7'].items():
        actual=scan['titles'].get(int(tid))
        compare('political_'+tid+'_full_AST',actual['AST_sha256'] if actual else None,expected['AST_sha256'])
        compare('political_'+tid+'_holder',str(actual['holder']) if actual else None,expected['holder'])
    protected_characters={}
    for cid,expected in baseline['character_protections'].items():
        actual=scan['selected'].get(int(cid));need(actual is not None,'protected actual character missing '+cid)
        top={k:reader.one(actual['entries'],k) for k in expected['protected_top']}
        alive={k:reader.one(actual['alive_data'],k) for k in expected['protected_alive']}
        compare('character_'+cid+'_rite',str(actual['rite_id']),expected['rite'])
        for k,wanted in expected['protected_top'].items():compare('character_'+cid+'_top_'+k,top[k],wanted)
        for k,wanted in expected['protected_alive'].items():compare('character_'+cid+'_alive_'+k,alive[k],wanted)
        protected_characters[cid]={'entries':actual['entries'],'AST_sha256':actual['AST_sha256'],
                                   'protected_top':top,'protected_alive':alive,
                                   'actual_all_held_title_ids':sorted(scan['held_by_protected'][int(cid)])}
    post=state['stage'] in ('success_postcommit','partial_postcommit')
    expected_title=state.get('native_title');added=expected_title['title_id'] if post and expected_title else None
    actor=scan['actor'];landed=actor['landed_data']
    need(isinstance(landed,list),'actual actor landed_data absent')
    projected=[]
    for expected in baseline['actor_protected_landed']:
        value=deepcopy(reader.one(landed,expected['key']))
        if expected['key']=='domain' and added is not None and isinstance(value,list):
            value=[r for r in value if not(r['key'] is None and r['value']==str(added))]
        projected.append({'key':expected['key'],'value':value})
    compare('actor_complete_protected_landed_projection',projected,baseline['actor_protected_landed'])
    expected_held=sorted(int(i) for i in baseline['actor_domain_ids'])
    actual_held=sorted(scan['held_by_protected'][actor['character_id']])
    compare('actor_actual_all_held_title_set_except_actual_new_religious_T',
            [i for i in actual_held if i!=added],expected_held)
    graphs={}
    for kind in ('faiths','rites'):
        graphs[kind]={}
        for gid,expected in baseline['graphs'][kind].items():
            actual=scan[kind].get(int(gid));need(actual is not None,'protected graph absent '+kind+'/'+gid)
            graphs[kind][gid]=actual
            current=(kind=='faiths' and int(gid)==scan['faith_id']) or (kind=='rites' and int(gid) in scan['actual_rites'])
            if current:
                new_faith=kind=='faiths' and int(gid)==scan['faith_id'] and state.get('saved_faith_semantics_version')=='v2'
                wanted=expected['tenet_doctrine_rows'] if new_faith else reader.replace_no_head(expected['tenet_doctrine_rows']) if state['stage']=='success_postcommit' else expected['tenet_doctrine_rows']
                compare(kind+'_'+gid+'_complete_tenet_status_projection',actual['tenet_doctrine_rows'],wanted)
            else:compare(kind+'_'+gid+'_complete_AST',actual['AST_sha256'],expected['AST_sha256'])
    variables=actor['variables']
    numeric_names=('lyd_i3b_serial','lyd_i3b_nonce','lyd_i3b_phase','lyd_i3b_active','lyd_i3b_authority_mode',
                   'lyd_i3b_result_serial','lyd_i3b_result_nonce','lyd_i3b_result_code','lyd_i3b_result_authority_mode')
    def currency(key,leaf):
        return exact_number(reader.one(reader.one(actor['alive_data'],key) or [],leaf))
    wallet={'gold':currency('gold','value'),'piety':currency('piety','currency'),'prestige':currency('prestige','currency')}
    xp=exact_number(reader.one(reader.one(actor['alive_data'],'lifestyle_xp') or [],'learning_lifestyle'))
    stress=exact_number(reader.one(actor['alive_data'],'stress'))
    for key,wanted in baseline['wallet'].items():compare('historical_0240_wallet_'+key,wallet[key],wanted)
    compare('learning_XP_unchanged',xp,baseline['XP']);compare('saved_stress_unchanged',stress,baseline['saved_stress'])
    for key,wanted in baseline['C2_history'].items():compare('C2_history_'+key,variables.get(key),wanted)
    compare('C2_nonce_serial',variables.get('lyd_c2_serial'),baseline['C2_nonce_serial'])
    compare('reset_count',variables.get('lyd_r4_reset_count'),baseline['reset_count'])
    for key,wanted in baseline['school_study_CD'].items():compare('school_study_CD_'+key,variables.get(key),wanted)
    for rid,expected in baseline['Rite_CD_locks'].items():
        observed={key:scan['rites'][int(rid)]['variables'].get(key) for key in expected}
        compare('Rite_'+rid+'_complete_existing_CD_locks',observed,expected)
    if state.get('faith_expected_factory_AST_delta') is not None:
        compare('current_Faith_full_AST_only_declared_factory_delta',state['faith_expected_factory_AST_delta']['matches'],True)
    return {'schema':'lyd.actual-i3b-checkpoint-typed-protection.v2',
            'Faith_direct_effective_observation':deepcopy(state.get('faith_doctrine_observation')),
            'Faith_declared_factory_AST_delta':deepcopy(state.get('faith_expected_factory_AST_delta')),
            'identity':state['identity'],
            'stage':state['stage'],'checkpoint_sha256':state['checkpoint_sha256'],'actor':actor,
            'wallet':wallet,'learning_XP_saved':xp,'stress_saved':stress,'commit_fee_delta':None,
            'fee_delta_qualification':'Requires an independently bound B3/B4 or B5 same-date pair; historical baseline comparison is separately labeled.',
            'typed_round_fields':{k:variables.get(k) for k in variables if k.startswith('lyd_i3b_')},
            'round_numeric_fields':{k:reader.number(variables,k,required=False) for k in numeric_names},
            'C2_history':{k:variables.get(k) for k in baseline['C2_history']},
            'C2_serial':variables.get('lyd_c2_serial'),'reset':variables.get('lyd_r4_reset_count'),
            'school_study_CD':{k:variables.get(k) for k in baseline['school_study_CD']},
            'protected_characters':protected_characters,'protected_graphs':graphs,
            'protected_political_titles':{str(tid):scan['titles'].get(tid) for tid in sorted(int(k) for k in baseline['political7'])},
            'actor_actual_all_held_title_ids':actual_held,'actual_added_religious_title':added,
            'checks':checks,'protection_checks_match':all(r['matches'] for r in checks),
            'actual_pass':None,'formal_mandate_credit':None,'saved_native_Title_field_paths':None}
