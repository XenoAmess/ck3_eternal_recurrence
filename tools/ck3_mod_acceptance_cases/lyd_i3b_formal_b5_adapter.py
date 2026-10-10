"""Candidate B5 cold persistence, using the public CaseClient and original B4 readers.

No factory, option selection, calendar or holder mutation. Source-only until adopted.
Historical B3 is the protection/reader origin; only a verified B4 SAVE is the cold seed.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from ck3_mod_acceptance_cases import lyd_i3b_formal_adapter as b4

require = b4.require

TITLE_VERSION = '1.20.0.4'
TITLE_EXE_SHA256 = '98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
TITLE_BINDING_BYTES = 902
TITLE_BINDING_SHA256 = 'daf0c2cdd1d6ef4409d11140dca0fdbbccc77f13066c73d14873d30a4731be2d'
TITLE_EVIDENCE_BYTES = 2504
TITLE_EVIDENCE_SHA256 = '283f6326bf97488f5e00a4be293a96afbca8d8716df9284825a32bafe73fefa6'


def title_binding(reader=None):
    value = checked({'path': str(Path(__file__).with_name('lyd_i3b_saved_title_binding_v1.json')),
        'bytes': TITLE_BINDING_BYTES, 'sha256': TITLE_BINDING_SHA256})
    proof = checked({'path': str(Path(__file__).with_name('lyd_i3b_saved_title_binding_v1.evidence.json')),
        'bytes': TITLE_EVIDENCE_BYTES, 'sha256': TITLE_EVIDENCE_SHA256})
    require(value['schema'] == 'lyd.native-title.saved-field-binding.v1' and
        value['source_head'] == (reader.HEAD if reader is not None else '632f0a57a07aa6299052004589ed6f7632e7d8f7') and
        value['evidence_sha256'] == TITLE_EVIDENCE_SHA256 and
        proof['game_version'] == TITLE_VERSION and proof['executable_sha256'] == TITLE_EXE_SHA256,
        'Exact reviewed saved Title mapping/evidence/reader identity required')
    return value


def title_build_matches(query, title):
    outer = query.get('native_result', {})
    return all(value.get('game_version') == TITLE_VERSION and
        isinstance(value.get('executable_sha256'), str) and
        value['executable_sha256'].lower() == TITLE_EXE_SHA256 for value in (outer, title))



def contract():
    return b4.load_json(Path(__file__).with_name('lyd_i3b_formal_b5.json'))


def validate_contract(context):
    data = context['case_contract']
    require(data == contract() and context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == 'i3b-formal-b5' and
            data['maximum_natural_days'] == data['factory_actions'] == data['event_selections'] == 0,
            'Exact paused B5-only contract required')


def checked(row):
    require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'Actual ref3 required')
    return b4._control()._checked_json(row)


def argument(argv, key):
    require(argv.count(key) == 1 and argv.index(key) + 1 < len(argv), 'Exact original argv field required: ' + key)
    return argv[argv.index(key) + 1]


def validate_pass(facts, data):
    require(facts.get('case') == 'i3b-formal-b4' and facts.get('product') == 'li-yu-dao' and
            all(facts.get(k) is True for k in ('B4_pass', 'business_pass', 'case_contract_qualified',
                'gui_contract_qualified', 'case_acceptance_pass')) and
            facts.get('business_actions_submitted') == 1 and facts.get('selected_option_number') == 1,
            'Actual public verified B4 PASS required; historical RED is not a seed')
    close = facts.get('normal_close') or {}
    require(close.get('normal_close_qualified') is True and
            close.get('retained_handle', {}).get('actual_retained_os0') is True and
            bool(close.get('native_zero_proof')) and bool(close.get('host_finished_at')) and
            close.get('managed_thread_finished') is True and close.get('cleanup_ok') is True and
            not close.get('host_error') and
            bool(close.get('root_normal_gui_review') or close.get('normal_quit_automation')),
            'Original B4 normal closure required, never administrative failure cleanup')
    for key, count in (('fresh_B3', 87), ('B4', 88)):
        saved = facts[key]
        require(len(saved['protection_checks']) == count and saved['protection_match'] is True and
                all(row.get('matches') is True for row in saved['protection_checks']) and
                bool(saved['saved_business_checks']) and saved['saved_business_match'] is True and
                all(row.get('matches') is True for row in saved['saved_business_checks']),
                'Original complete 87/88 B4 protection and business checks required')
        require(saved['complete_cached_successor_ids'] == data['baseline_cached_succession'],
                'Original B4 saved ordered45 differs')
    require(facts['cache_before_ids'] == facts['cache_after_ids'] == data['baseline_cached_succession'],
            'Original B4 native ordered45 differs')
    title = facts['B4']['new_title_id']
    require(type(title) is int and 0 < title < 2**32 - 1, 'Actual dynamic B4 Title required')
    terminal = facts['terminal']
    require(terminal['event_definition_key'] == 'lyd.431' and
            type(terminal['event_instance_id']) is int and terminal['event_instance_id'] > 0 and
            terminal['root_character_id'] == data['expected']['root_character_id'] and
            terminal['native_option_indices'] == [0] and terminal['actual_numeric_terms'] ==
            {k: data['round'][k] for k in ('serial', 'nonce')}, 'Original B4 terminal identity differs')
    return title


def upstream(context):
    inputs = context['case_inputs']
    require(set(inputs) == {'B4_verified_origin'}, 'B5 takes one explicit B4 evidence bundle')
    bundle = inputs['B4_verified_origin']
    require(isinstance(bundle, dict) and set(bundle) == {'prepared_case', 'run_context', 'public_verify_command'},
            'B4 prepared/context/actual recorded verify refs required')
    prepared, run, command = (checked(bundle[k]) for k in ('prepared_case', 'run_context', 'public_verify_command'))
    require(prepared.get('schema') == 'ck3-mod-acceptance-prepared-case-v1' and
            prepared.get('case') == 'i3b-formal-b4' and prepared.get('product') == 'li-yu-dao' and
            run.get('schema') == 'ck3-mod-acceptance-run-context-v1' and
            run.get('case') == 'i3b-formal-b4' and run.get('product') == 'li-yu-dao' and
            run.get('prepared_case') == bundle['prepared_case'], 'B4 prepared/run binding differs')
    require(context.get('runtime_manifest') == prepared['runtime_manifest'],
            'B5 must retain the exact B4 shared source/host/native/game manifest')
    argv = command.get('argv', [])
    require(command.get('exit_code') == 0 and isinstance(argv, list) and
            all(isinstance(v, str) and v for v in argv), 'Actual completed original public verify command required')
    entries = [i for i, value in enumerate(argv) if Path(value).name == 'ck3_mod_acceptance.py']
    require(len(entries) == 1 and argv[entries[0] + 1] == 'verify' and
            argument(argv, '--product') == 'li-yu-dao' and argument(argv, '--case') == 'i3b-formal-b4' and
            Path(argument(argv, '--prepared-case')).resolve() == Path(bundle['prepared_case']['path']).resolve() and
            Path(argument(argv, '--run-context')).resolve() == Path(bundle['run_context']['path']).resolve(),
            'Original public B4 verify argv crossed prepared/context/case')
    facts = checked(command['stdout'])
    frozen = checked(run['frozen_argv'])
    require(facts.get('run_id') == run['run_id'] == frozen['run_id'] and
            Path(run['run_dir']).resolve().name == run['run_id'] and
            frozen['runtime_manifest'] == prepared['runtime_manifest'], 'Original B4 allocation/runtime differs')
    data = b4.contract()
    require(checked(prepared['contract']) == data, 'Original B4 formal contract differs')
    b4.validate_origin(prepared['case_inputs'], prepared['startup']['saved_campaign'], data)
    title = validate_pass(facts, data)
    checkpoint = facts['B4']['checkpoint']
    require(set(checkpoint) == {'path', 'bytes', 'sha256'} and type(checkpoint['bytes']) is int and
            checkpoint['bytes'] > 0 and isinstance(checkpoint['sha256'], str) and len(checkpoint['sha256']) == 64 and
            Path(checkpoint['path']).resolve().is_relative_to(Path(run['run_dir']).resolve() / 'case-output/checkpoints'),
            'Actual independently preserved B4 SAVE required')
    seed = context['saved_campaign']
    require({k: seed[k] for k in ('bytes', 'sha256')} == {k: checkpoint[k] for k in ('bytes', 'sha256')} and
            Path(seed['save']).resolve() == Path(checkpoint['path']).resolve() and
            seed['player_id'] == data['expected']['actor_character_id'] and seed['date_raw'] == data['expected']['date_raw'],
            'Cold input must be this exact verified B4 SAVE')
    expected = {**data['expected'], 'event_definition_key': 'lyd.431',
        'event_instance_id': facts['terminal']['event_instance_id'], 'native_option_indices': [0]}
    return {'bundle': bundle, 'prepared': prepared, 'facts': facts, 'data': data, 'title_id': title,
            'expected': expected, 'verification': command['stdout']}


def prepare_case(context):
    from ck3_mod_acceptance_prepare import CONFIG_NAMES, checked_copy, pin, write_json, _outer_from_inner
    validate_contract(context)
    origin = upstream(context)  # Reject absent/RED B4 before any profile write.
    data, inputs, seed = origin['data'], origin['prepared']['case_inputs'], context['saved_campaign']
    state, output = Path(context['state_dir']).resolve(), Path(context['output']).resolve()
    seed_path = Path(seed['save']).resolve()
    require(not state.exists() and seed_path.is_file() and seed_path.stat().st_size == seed['bytes'] and
            not seed_path.is_relative_to(state), 'Unused state and exact external B4 seed required')
    require(set(inputs['plain_configuration']) == set(CONFIG_NAMES), 'Original four configurations required')
    production = checked(inputs['product_inventory'])
    require(production['source_head'] == data['production_source_head'], 'Same formal product projection required')
    product = Path(inputs['product_dir']).resolve()
    rows = b4._control()._inventory_rows(product, production['files'], data['production_file_count'])
    profile, target = state / 'profile', state / 'profile/mod-content/product'
    profile.mkdir(parents=True)
    for name in CONFIG_NAMES:
        checked_copy(inputs['plain_configuration'][name], profile / name)
    for row in rows:
        checked_copy(row, target / Path(row['path']).relative_to(product))
    outer = profile / 'mod/product.mod'
    outer.parent.mkdir()
    with outer.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_outer_from_inner(target / 'descriptor.mod', target))
    write_json(profile / 'dlc_load.json', {'enabled_mods': ['mod/product.mod'], 'disabled_dlcs': []})
    inventory = output / 'saved-product-inventory.json'
    write_json(inventory, {'schema': 'ck3-saved-campaign-product-only-profile-v1', 'profile_path': str(profile),
        'enabled_mods': ['mod/product.mod'], 'product_files': [pin(outer), *[pin(p) for p in sorted(target.rglob('*')) if p.is_file()]]})
    files = {p.relative_to(profile).as_posix(): pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    preparation = state / 'preparation.json'
    write_json(preparation, {'schema': 'ck3-mod-acceptance-profile-startup-evidence-v1', 'profile_dir': str(profile),
        'profile_files': list(files), 'profile_input_sha256': {name: row['sha256'] for name, row in files.items()},
        'B4_verified_origin': context['case_inputs']['B4_verified_origin'], 'saved_campaign': seed,
        'runtime_manifest': context['runtime_manifest'],
        'expected': origin['expected'], 'new_title_id': origin['title_id'], 'runtime_status': 'NOT_RUN'})
    hook = output / 'saved-startup-case-contract.json'
    write_json(hook, {'schema': 'ck3-saved-campaign-startup-case-contract-v1', 'state_dir': str(state),
        'handler': {**pin(__file__), 'function': 'admit_saved_startup_event'},
        'dependencies': [pin(Path(__file__).with_name('lyd_i3b_formal_b5.json')), pin(Path(b4.__file__)),
            pin(Path(b4.__file__).with_name('lyd_i3b_formal_b4.json')),
            pin(Path(b4.__file__).with_name('lyd_transaction_control_adapter.py')), pin(preparation),
            pin(Path(__file__).with_name('lyd_i3b_saved_title_binding_v1.json')),
            pin(Path(__file__).with_name('lyd_i3b_saved_title_binding_v1.evidence.json'))],
        'expected': origin['expected']})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': str(state),
        'saved_campaign': {**seed, 'save': str(seed_path), 'product_inventory': str(inventory)},
        'saved_campaign_startup_case_contract': str(hook)}, 'initial_plan': pin(initial),
        'startup_evidence': pin(preparation), 'profile_preparation': pin(preparation), 'files': files,
        'runtime_status': 'NOT_RUN', 'business_contract_applicable': True, 'business_pass': False,
        'product_release_pass': False}


def admit_saved_startup_event(context, snapshot, typed_event_packet):
    prepared = b4.load_json(Path(context['state_dir']) / 'preparation.json')
    origin = upstream({'case_inputs': {'B4_verified_origin': prepared['B4_verified_origin']},
                       'saved_campaign': prepared['saved_campaign'], 'runtime_manifest': prepared['runtime_manifest']})
    require(context['expected'] == prepared['expected'] == origin['expected'] and
            prepared['new_title_id'] == origin['title_id'], 'Actual B4 terminal/Title startup binding differs')
    proof = b4.observe_event(snapshot, typed_event_packet, origin['expected'], origin['data'], result=True)
    return {**origin['expected'], 'proof': {**proof, 'upstream_B4_verification': origin['verification'],
        'new_title_id': origin['title_id']}, 'business_pass': False}


def native_title_matches(frame, query, origin):
    title = b4.observe_title(frame, query, origin['data'], absent=False)
    props, laws = title.get('title_properties', {}), title.get('title_laws', {})
    return bool(title_build_matches(query, title) and
        title.get('head_title_full_id') == origin['title_id'] and
        title.get('native_title_holder_full_id') == origin['data']['expected']['actor_character_id'] and
        props.get('available') is True and all(props.get(k) is True for k in origin['data']['title_properties']) and
        laws.get('available') is True and laws.get('temporal_head_of_faith_succession_law_member') is True and
        {'native_definition_id': 95, 'key': 'temporal_head_of_faith_succession_law'} in laws.get('complete_laws', []))


def read_cold_saved(context, checkpoint, frame, assembly, title_query, origin):
    """One new body read; reuse original parser, raw_scan and full88 protection functions."""
    data, old = origin['data'], origin['prepared']
    _, baseline, request = b4.validate_origin(old['case_inputs'], old['startup']['saved_campaign'], data)
    request = deepcopy(request)
    require(checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == data['expected']['date_raw'] and
            checkpoint.get('episode_projection') == 'native_campaign', 'Actual paused cold checkpoint required')
    path = Path(checkpoint['path']).resolve()
    require(path != Path(context['saved_campaign']['save']).resolve(), 'Never overwrite/read the B4 seed as a new SAVE')
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    require(len(raw) == checkpoint['size'] and sha == checkpoint['sha256'] and not raw.startswith(b'PK'),
            'New plain cold checkpoint size/SHA differs')
    preserved = Path(context['output']) / 'checkpoints/B5-cold-result.ck3'
    preserved.parent.mkdir(parents=True, exist_ok=True)
    with preserved.open('xb') as stream:
        stream.write(raw)
    reader = b4._control()._reader(context['repo_root'])
    identity = {'actor_id': data['expected']['actor_character_id'], 'faith_id': data['faith_id'],
        'main_rite_id': data['main_rite_id'], 'pid': frame['diagnostics']['bridge_pid'],
        'session_id': context['run_id'], 'revision': frame['revision'], 'checkpoint_id': str(path)}
    native = b4.native_predicates(frame, assembly, identity, sha, data, reader)
    request.update(mode='future_actual', stage='success_postcommit', identity=identity,
        save={'path': str(preserved), 'bytes': len(raw), 'sha256': sha}, native_title_binding=title_binding(reader),
        native_reference_binding={'schema': 'lyd.saved-native-reference-binding.v1', 'source_head': reader.HEAD,
            'evidence_sha256': old['case_inputs']['formal_b3_qualification']['sha256'], 'title_type': 'lt'},
        native_predicates=None, output=None)
    text = raw.decode('utf-8-sig')
    state = reader.observe_text(text, request, sha)
    scan = b4.raw_scan(text, {'played_character_id': identity['actor_id']}, baseline, reader)
    protection = b4.evaluate_protection(scan, baseline, state, reader)
    require(len(protection['checks']) == 88, 'Original full88 protection census differs')
    saved_title = state.get('native_title') or {}
    saved_ids = [reader.scalar_id(row['value'], 'saved successor') for row in
                 reader.one(state['actor']['landed_data'], 'succession', required=True)]
    joined = (scan['faith_id'] == 107 and scan['rite_id'] == 169 and
        scan['current_head'] == saved_title.get('title_id') == origin['title_id'] and
        saved_title.get('holder') == identity['actor_id'] and
        scan['faith_members'] == sorted(row['character_id'] for row in native['characters']) and
        native_title_matches(frame, title_query, origin))
    return {'checkpoint': request['save'], 'identity': identity, 'new_title_id': saved_title.get('title_id'),
        'retained_native_title': saved_title,
        'saved_title_field_qualification': saved_title.get('qualification'),
        'saved_business_checks': state['checks'], 'saved_business_match': all(r['matches'] for r in state['checks']),
        'protection_checks': protection['checks'], 'protection_match': protection['protection_checks_match'],
        'complete_cached_successor_ids': saved_ids, 'native_saved_Faith_Title_join': joined,
        'complete_native_Faith_predicates': native, 'saved_body_reads': 1, 'baseline_body_reads': 0}


def saved_title_qualified(saved):
    value = saved.get('saved_title_field_qualification')
    if not (isinstance(value, dict) and value.get('status') == 'QUALIFIED_OBSERVATION' and
            value.get('law_matches_factory_contract') is True and
            value.get('properties_match_factory_contract') is True):
        return False
    binding = title_binding()
    properties = value.get('properties')
    return bool(value.get('binding') == binding and isinstance(properties, dict) and
        set(properties) == set(binding['properties']) and
        type(value.get('law')) is list and
        value['law'] == ['temporal_head_of_faith_succession_law'] and
        all(isinstance(properties[name], dict) and
            set(properties[name]) == {'raw', 'value', 'path'} and
            properties[name]['value'] is True and
            type(properties[name]['raw']) is str and properties[name]['raw'] == spec['true_token'] and
            type(properties[name]['path']) is list and properties[name]['path'] == spec['path']
            for name, spec in binding['properties'].items()))


def assessment(facts, origin):
    saved, wanted = facts['cold_saved'], origin['data']['baseline_cached_succession']
    require(len(saved['protection_checks']) == 88, 'Complete88 cold protection required')
    return bool(saved_title_qualified(saved) and
        all(r.get('matches') is True for r in saved['protection_checks']) and
        saved['protection_match'] is True and bool(saved['saved_business_checks']) and
        all(r.get('matches') is True for r in saved['saved_business_checks']) and saved['saved_business_match'] is True and
        saved['native_saved_Faith_Title_join'] is True and saved['new_title_id'] == origin['title_id'] and
        facts['initial_native_title_match'] is True and facts['cache_before_ids'] == facts['cache_after_ids'] ==
        saved['complete_cached_successor_ids'] == wanted and saved['saved_body_reads'] == 1 and
        saved['baseline_body_reads'] == 0 and facts['factory_actions'] == facts['event_selections'] == facts['natural_days'] == 0)


def run_case(context, client):
    validate_contract(context)
    origin = upstream(context)
    client.retain_process()
    before = client.snapshot(require_event_free=False)
    event = b4._call(client, 'i3b-b5-cold-431', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': origin['expected']['event_instance_id'], 'expected_revision': before['revision']})
    b4.observe_event(before, event, origin['expected'], origin['data'], result=True)
    title = b4._call(client, 'i3b-b5-title-before', 'ck3_query_confucian_religious_title_v1', {'expected_revision': before['revision']})
    initial_title_match = native_title_matches(before, title, origin)
    cache_before = b4.observe_cache(before, b4._call(client, 'i3b-b5-cache-before',
        'ck3_query_actor_cached_succession_v1', {'expected_revision': before['revision']}))
    saved = b4._call(client, 'i3b-b5-only-save', 'ck3_save_checkpoint', {'expected_revision': before['revision']})
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original B5 SAVE not accepted')
    frame = client.snapshot(require_event_free=False)
    require(frame['date_raw'] == before['date_raw'] == origin['expected']['date_raw'], 'Cold SAVE changed paused date')
    event = b4._call(client, 'i3b-b5-after-save-431', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': origin['expected']['event_instance_id'], 'expected_revision': frame['revision']})
    b4.observe_event(frame, event, origin['expected'], origin['data'], result=True)
    assembly = b4._call(client, 'i3b-b5-G2', 'ck3_query_confucian_assembly_predicates_v1', {'expected_revision': frame['revision']})
    title = b4._call(client, 'i3b-b5-G3', 'ck3_query_confucian_religious_title_v1', {'expected_revision': frame['revision']})
    cache_after = b4.observe_cache(frame, b4._call(client, 'i3b-b5-cache-after',
        'ck3_query_actor_cached_succession_v1', {'expected_revision': frame['revision']}))
    cold = read_cold_saved(context, saved['checkpoint'], frame, assembly, title, origin)
    facts = {'schema': 'ck3-lyd-i3b-formal-b5-result-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'upstream_B4_verification': origin['verification'],
        'cold_seed': {k: context['saved_campaign'][k] for k in ('save', 'bytes', 'sha256')},
        'cache_before_ids': cache_before, 'cache_after_ids': cache_after, 'initial_native_title_match': initial_title_match,
        'cold_saved': cold, 'factory_actions': 0, 'event_selections': 0, 'natural_days': 0,
        'business_contract_applicable': True, 'formal_institution_pass': False, 'C3_pass': False,
        'I4_pass': False, 'product_release_pass': False, 'normal_close': 'PENDING_SHARED_ORIGINAL_CLOSE'}
    facts['saved_title_fields_qualified'] = saved_title_qualified(cold)
    facts['known_limitations'] = ([] if facts['saved_title_fields_qualified'] else
        ['Independent saved Title four-attribute/law95 qualification absent or not true'])
    passed = assessment(facts, origin)
    facts.update(B5_pass=passed, case_contract_qualified=passed, gui_contract_qualified=passed, business_pass=passed)
    client.checkpoint('i3b-formal-b5-case-result', facts)
    return facts


def verify_case(context, client=None):
    validate_contract(context)
    path = Path(context['output']) / 'i3b-formal-b5-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False, 'B5_pass': False,
            'business_contract_applicable': True, 'business_pass': False, 'product_release_pass': False,
            'status': 'NO_ACTUAL_VERIFIED_B4_OR_B5_RESULT'}
    origin = upstream(context)
    facts = b4.load_json(path)
    require(all(facts.get(k) == context[k] for k in ('run_id', 'product', 'case')) and
            facts['upstream_B4_verification'] == origin['verification'] and facts['cold_seed'] ==
            {k: context['saved_campaign'][k] for k in ('save', 'bytes', 'sha256')}, 'B5 result crossed run/B4/seed')
    passed = assessment(facts, origin)
    require(all(facts.get(k) is passed for k in ('B5_pass', 'business_pass', 'case_contract_qualified', 'gui_contract_qualified')),
            'B5 assessment differs from full saved/native evidence')
    return {**facts, 'formal_institution_pass': False, 'C3_pass': False, 'I4_pass': False,
        'product_release_pass': False, 'verification_scope': 'B5 only; shared original normal closure remains mandatory'}
