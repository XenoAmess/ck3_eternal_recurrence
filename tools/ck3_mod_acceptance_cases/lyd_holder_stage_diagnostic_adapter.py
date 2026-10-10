"""One D2b holder/resolve diagnostic; preserve changed cache/AST before assessment.

The four script logs describe every_title_heir scopes, never four native actor
cache snapshots. This case does not certify the formal institution or product.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ck3_mod_acceptance_cases import lyd_transaction_control_adapter as base

require = base.require


def contract():
    return base.read_json(Path(__file__).with_name('lyd_holder_stage_diagnostic.json'))


def validate_contract(context):
    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == 'holder-stage-diagnostic', 'Holder diagnostic case differs')
    require(data == contract(), 'Holder diagnostic contract differs from frozen data')
    require(data['business_contract_applicable'] is False and data['maximum_natural_days'] == 0,
            'Diagnostic has no formal/product or natural-day credit')


def prepare_case(context):
    from ck3_mod_acceptance_prepare import CONFIG_NAMES, checked_copy, pin, write_json, _outer_from_inner
    validate_contract(context)
    data, inputs = context['case_contract'], context['case_inputs']
    require(set(inputs) == {'product_dir', 'product_inventory', 'overlay_dir', 'plain_configuration'} and
            set(inputs['plain_configuration']) == set(CONFIG_NAMES), 'Four explicit profile configurations required')
    seed = context['saved_campaign']
    require(set(seed) == {'save', 'bytes', 'sha256', 'player_id', 'date_raw'} and
            {key: seed[key] for key in data['saved_campaign']} == data['saved_campaign'], 'Exact R34 D2a unheld seed required')
    seed_path = Path(seed['save']).resolve()
    require(seed_path.is_file() and seed_path.stat().st_size == seed['bytes'], 'Original external seed size differs')
    state, output = Path(context['state_dir']).resolve(), Path(context['output']).resolve()
    require(not state.exists() and not seed_path.is_relative_to(state), 'Unused prepared state outside original seed required')
    production = base._checked_json(inputs['product_inventory'])
    require(production['source_head'] == data['production_source_head'], 'Reviewed 71-file production HEAD differs')
    product, overlay = Path(inputs['product_dir']).resolve(), Path(inputs['overlay_dir']).resolve()
    product_rows = base._inventory_rows(product, production['files'], 71)
    overlay_rows = base._inventory_rows(overlay, data['overlay_files'], 6)
    profile = state / 'profile'
    profile.mkdir(parents=True)
    for name in CONFIG_NAMES:
        checked_copy(inputs['plain_configuration'][name], profile / name)
    products, enabled = [], []
    for name, root, rows in (('product', product, product_rows), ('holder_stage_diagnostic', overlay, overlay_rows)):
        target = profile / 'mod-content' / name
        for row in rows:
            checked_copy(row, target / Path(row['path']).relative_to(root))
        outer = profile / 'mod' / (name + '.mod')
        outer.parent.mkdir(exist_ok=True)
        with outer.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(_outer_from_inner(target / 'descriptor.mod', target))
        products.extend([pin(outer), *[pin(path) for path in sorted(target.rglob('*')) if path.is_file()]])
        enabled.append('mod/' + name + '.mod')
    write_json(profile / 'dlc_load.json', {'enabled_mods': enabled, 'disabled_dlcs': []})
    inventory_path = output / 'saved-product-inventory.json'
    write_json(inventory_path, {'schema': 'ck3-saved-campaign-product-only-profile-v1',
        'profile_path': str(profile), 'enabled_mods': enabled, 'product_files': products})
    files = {path.relative_to(profile).as_posix(): pin(path) for path in sorted(profile.rglob('*')) if path.is_file()}
    preparation = output / 'profile-preparation.json'
    write_json(preparation, {'schema': 'ck3-mod-acceptance-prepared-holder-stage-diagnostic-v1',
        'state_dir': str(state), 'profile_dir': str(profile), 'files': files,
        'product_inventory': inputs['product_inventory'], 'overlay_files': data['overlay_files'],
        'saved_product_inventory': pin(inventory_path), 'saved_campaign': seed,
        'runtime_status': 'NOT_RUN', 'business_pass': False, 'product_release_pass': False})
    startup = state / 'preparation.json'
    write_json(startup, {'schema': 'ck3-mod-acceptance-profile-startup-evidence-v1',
        'profile_dir': str(profile), 'profile_files': list(files),
        'profile_input_sha256': {name: row['sha256'] for name, row in files.items()},
        'preparation': pin(preparation), 'runtime_status': 'NOT_RUN'})
    hook = output / 'saved-startup-case-contract.json'
    write_json(hook, {'schema': 'ck3-saved-campaign-startup-case-contract-v1', 'state_dir': str(state),
        'handler': {**pin(__file__), 'function': 'admit_saved_startup_event'},
        'dependencies': [pin(Path(__file__).with_name('lyd_holder_stage_diagnostic.json')), pin(base.__file__)],
        'expected': data['expected']})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': str(state),
        'saved_campaign': {**seed, 'save': str(seed_path), 'product_inventory': str(inventory_path)},
        'saved_campaign_startup_case_contract': str(hook)}, 'initial_plan': pin(initial),
        'profile_preparation': pin(preparation), 'startup_evidence': pin(startup), 'files': files,
        'runtime_status': 'NOT_RUN', 'business_contract_applicable': False,
        'business_pass': False, 'product_release_pass': False}


def admit_saved_startup_event(context, snapshot, typed_event_packet):
    data = contract()
    require(context['expected'] == data['expected'], 'Saved startup expected identity differs')
    proof = base.observe_event(snapshot, typed_event_packet, context['expected'], data)
    return {**context['expected'], 'proof': proof, 'business_pass': False,
            'baseline_saved_campaign': data['saved_campaign']}


def observe_cache_after(frame, dto, data):
    for key, actual in {'queried_snapshot_id': frame['snapshot_id'], 'queried_revision': frame['revision'],
        'queried_native_revision': frame['native_revision'], 'date_raw': frame['date_raw'],
        'game_pid': frame['diagnostics']['bridge_pid'], 'connection_generation': frame['diagnostics']['connection_generation'],
        'player_character_id': data['expected']['actor_character_id']}.items():
        require(type(dto.get(key)) is type(actual) and dto[key] == actual, 'Cached succession frame differs: ' + key)
    cache = dto.get('native_result', {}).get('actor_cached_succession', {})
    ids, count = cache.get('complete_cached_successor_ids'), cache.get('native_count')
    require(cache.get('available') is True and cache.get('read_only') is True and cache.get('roster_complete') is True and
            type(count) is int and count >= 0 and isinstance(ids, list) and len(ids) == count and
            all(type(value) is int and value > 0 for value in ids) and len(set(ids)) == count,
            'Complete ordered after-cache unavailable')
    require(cache.get('played_character_id') == data['expected']['actor_character_id'] and
            cache.get('played_character_full_id') == data['expected']['actor_character_id'] and
            cache.get('date_raw') == data['expected']['date_raw'], 'Native cached actor/date differs')
    return ids


def evaluate_saved_diagnostic(reader, actor, titles, data):
    require(actor['character_id'] == data['expected']['actor_character_id'], 'Saved diagnostic actor differs')
    succession = reader.one(actor['landed_data'], 'succession', required=True)
    require(isinstance(succession, list) and all(row['key'] is None for row in succession), 'Saved succession shape differs')
    ids = [reader.scalar_id(row['value'], 'saved cached successor') for row in succession]
    observed = {}
    for title_id, before_hash in data['political_title_ast_sha256'].items():
        row = titles[int(title_id)]
        after_hash = reader.ast_sha(row['entries'])
        require(row['AST_sha256'] == after_hash, 'Saved political AST projection hash differs')
        observed[title_id] = {'before_AST_sha256': before_hash, 'after_AST_sha256': after_hash,
            'full_AST_equal': after_hash == before_hash, 'after_holder': row['holder'], 'after_AST': row['entries']}
    title = titles[data['new_title_id']]
    completed = reader.number(actor['variables'], data['control_completed_variable'], required=False)
    return {'complete_cached_successor_ids': ids, 'cache_equals_baseline': ids == data['baseline_cached_succession'],
        'actor_landed_data_AST': actor['landed_data'], 'actor_landed_data_AST_sha256': reader.ast_sha(actor['landed_data']),
        'political_titles': observed, 'political_full_AST_equal': all(row['full_AST_equal'] for row in observed.values()),
        'new_title_id': data['new_title_id'], 'new_title_holder': title['holder'], 'new_title_AST': title['entries'],
        'new_title_held_by_actor': title['holder'] == data['expected']['actor_character_id'],
        'control_completed_variable': data['control_completed_variable'], 'control_completed_value_observed': completed,
        'control_completed_value_is_not_a_success_requirement': True,
        'diagnostic_observation_only': True, 'cause': 'UNKNOWN', 'business_pass': False, 'product_release_pass': False}


def read_saved_diagnostic(repo_root, checkpoint, data):
    require(checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == data['expected']['date_raw'] and
            checkpoint.get('episode_projection') == 'native_campaign', 'Actual saved diagnostic checkpoint required')
    path = Path(checkpoint['path']).resolve()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(len(raw) == checkpoint['size'] and digest == checkpoint['sha256'].lower(), 'Actual checkpoint bytes/SHA differs')
    require(not raw.startswith(b'PK'), 'Existing reader requires a plain checkpoint')
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    reader, actor = base._reader(repo_root), None
    for identity, entries in reader.records(reader.section(text, 'living', 'dead_unprunable'), 'living character'):
        if identity == data['expected']['actor_character_id']:
            require(actor is None, 'Duplicate saved actor')
            actor = reader.raw_character(identity, entries)
    wanted = {int(key) for key in data['political_title_ast_sha256']} | {data['new_title_id']}
    titles = {}
    for identity, entries in reader.title_database_records(text):
        if identity in wanted:
            require(identity not in titles, 'Duplicate saved diagnostic title')
            titles[identity] = reader.title_row(identity, entries)
    require(actor is not None and set(titles) == wanted, 'Complete saved actor/seven political/new-title projection missing')
    facts = evaluate_saved_diagnostic(reader, actor, titles, data)
    return {**facts, 'checkpoint': {'path': str(path), 'bytes': len(raw), 'sha256': digest},
        'save_body_reads': 1, 'baseline_body_reads': 0}


def log_offsets(context):
    root = Path(context['state_dir']) / 'profile' / 'logs'
    return {str(root / name): (root / name).stat().st_size if (root / name).exists() else 0
            for name in ('debug.log', 'game.log')}


def stage_log_windows(offsets):
    windows = []
    for value, offset in offsets.items():
        path = Path(value)
        if not path.is_file():
            windows.append({'path': value, 'status': 'UNKNOWN', 'reason': 'log absent'})
            continue
        size = path.stat().st_size
        if size < offset:
            windows.append({'path': value, 'status': 'UNKNOWN', 'reason': 'log shortened', 'before_offset': offset, 'after_size': size})
            continue
        with path.open('rb') as stream:
            stream.seek(offset)
            raw = stream.read(4 * 1024 * 1024 + 1)
        truncated = len(raw) > 4 * 1024 * 1024
        raw = raw[:4 * 1024 * 1024]
        windows.append({'path': value, 'byte_offset': offset, 'bytes': len(raw), 'window_sha256': hashlib.sha256(raw).hexdigest(),
            'source_after_size': size, 'truncated': truncated, 'text': raw.decode('utf-8', errors='backslashreplace'),
            'scope_full_ID_and_iterator_order_qualification': 'UNKNOWN',
            'script_getter_lazy_recalculation_possible': True, 'intermediate_actor_cache_observed': False})
    return windows


def run_case(context, client):
    validate_contract(context)
    data = context['case_contract']
    client.retain_process()
    before = client.snapshot(require_event_free=False)
    event = base._call(client, 'holder-diagnostic-initial-event', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': data['expected']['event_instance_id'], 'expected_revision': before['revision']})
    admitted = admit_saved_startup_event({'expected': data['expected']}, before, event)
    cache_before = base._call(client, 'holder-diagnostic-cache-before', 'ck3_query_actor_cached_succession_v1',
        {'expected_revision': before['revision']})
    ids_before = base.observe_cache(before, cache_before, data)
    offsets = log_offsets(context)
    client.checkpoint('holder-diagnostic-before', {'frame': before, 'admission': admitted, 'cache': cache_before, 'log_offsets': offsets})
    selected = base._call(client, 'holder-diagnostic-select-once', 'ck3_select_event_option',
        {'event_instance_id': data['expected']['event_instance_id'], 'option_number': 1, 'expected_revision': before['revision']})
    require(selected.get('accepted') is True and selected.get('event_instance_id') == data['expected']['event_instance_id'] and
            selected.get('option_number') == 1 and selected.get('option_index') == 0, 'Original once-only selection ACK differs; never replay')
    after, instance = base.observe_terminal(client, data)
    terminal = base._call(client, 'holder-diagnostic-terminal-event', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': instance, 'expected_revision': after['revision']})
    expected_terminal = {**data['expected'], 'event_definition_key': data['terminal_event_definition_key'], 'event_instance_id': instance}
    terminal_proof = base.observe_event(after, terminal, expected_terminal, data)
    cache_after = base._call(client, 'holder-diagnostic-cache-after', 'ck3_query_actor_cached_succession_v1',
        {'expected_revision': after['revision']})
    ids_after = observe_cache_after(after, cache_after, data)
    client.checkpoint('holder-diagnostic-after', {'frame': after, 'selected': selected, 'terminal_event': terminal,
        'terminal_proof': terminal_proof, 'cache': cache_after, 'baseline_equal_observed': ids_before == ids_after})
    # No cache-count/equality or political-protection gate precedes this one SAVE.
    saved = base._call(client, 'holder-diagnostic-save-once', 'ck3_save_checkpoint', {'expected_revision': after['revision']})
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original save was not accepted')
    saved_facts = read_saved_diagnostic(context['repo_root'], saved['checkpoint'], data)
    logs = stage_log_windows(offsets)
    client.checkpoint('holder-diagnostic-script-scope-log-windows', {'windows': logs,
        'stages': data['log_stages'], 'intermediate_actor_cache_observed': False, 'cause': 'UNKNOWN'})
    facts = {'schema': 'ck3-mod-acceptance-holder-stage-diagnostic-result-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'case_contract_qualified': True,
        'gui_contract_qualified': True, 'diagnostic_capture_complete': True, 'selected_option_number': 1,
        'business_actions_submitted': 1, 'terminal_event_instance_id': instance, 'stopped_at_definition': data['terminal_event_definition_key'],
        'cache_before_ids': ids_before, 'cache_after_ids': ids_after, 'cache_changed': ids_before != ids_after,
        'saved_cache_equals_after_native': saved_facts['complete_cached_successor_ids'] == ids_after,
        'saved': saved_facts, 'script_scope_logs_checkpoint': 'holder-diagnostic-script-scope-log-windows.json',
        'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False,
        'normal_close_pending': True, 'formal_institution_pass': None, 'C3': None, 'I4': None, 'cause': 'UNKNOWN'}
    client.checkpoint('holder-stage-diagnostic-case-result', facts)
    return facts


def verify_case(context):
    validate_contract(context)
    path = Path(context['output']) / 'holder-stage-diagnostic-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False, 'business_contract_applicable': False,
            'business_pass': False, 'product_release_pass': False, 'status': 'NOT_RUN_OR_PRESERVED_FAILURE'}
    facts, data = base.read_json(path), context['case_contract']
    require(all(facts.get(key) == context[key] for key in ('run_id', 'product', 'case')), 'Diagnostic crossed case/run')
    require(facts.get('diagnostic_capture_complete') is True and facts.get('business_actions_submitted') == 1 and
            facts.get('selected_option_number') == 1 and facts.get('stopped_at_definition') == 'lyd_factory_diag.2' and
            facts.get('cache_before_ids') == data['baseline_cached_succession'], 'Once-only D2b diagnostic evidence missing')
    saved = facts['saved']
    require(saved.get('save_body_reads') == 1 and saved.get('baseline_body_reads') == 0 and
            set(saved.get('political_titles', {})) == set(data['political_title_ast_sha256']) and
            saved.get('diagnostic_observation_only') is True, 'Complete saved diagnostic projection missing')
    return {**facts, 'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False,
        'formal_institution_pass': None, 'C3': None, 'I4': None, 'cause': 'UNKNOWN',
        'verification_scope': 'capture_of_one_D2b_holder_resolve; changed_cache_or_AST_is_an_observation; shared_normal_close_separate'}
