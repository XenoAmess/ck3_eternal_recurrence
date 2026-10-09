"""Saved D2a empty-transaction control through the public CaseClient only.

Preparation chooses no host, native binary or machine. Admission is a pure
observation; the sole business step is public option 1. This control cannot
certify the formal institution or the whole product.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def contract():
    return read_json(Path(__file__).with_name('lyd_transaction_control.json'))


def validate_contract(context):
    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == 'transaction-only-control', 'Selected control case differs')
    require(data == contract(), 'Transaction control contract differs from frozen data')
    require(data['business_contract_applicable'] is False and data['maximum_natural_days'] == 0,
            'Control has no whole-product or natural-day credit')


def _checked_json(row):
    raw = Path(row['path']).read_bytes()
    require(type(row['bytes']) is int and len(raw) == row['bytes'] and
            hashlib.sha256(raw).hexdigest() == row['sha256'].lower(), 'Frozen JSON input changed')
    return json.loads(raw)


def _relative(value):
    require(isinstance(value, str) and value and '\\' not in value and ':' not in value,
            'Exact relative POSIX file path required')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == value,
            'Input file escaped mod root')
    return path


def _inventory_rows(root, rows, count):
    require(isinstance(rows, list) and len(rows) == count, 'Exact mod file census differs')
    paths = []
    for row in rows:
        relative = _relative(row['path']).as_posix()
        require(type(row['bytes']) is int and row['bytes'] >= 0 and
                re.fullmatch('[0-9a-f]{64}', str(row['sha256'])), 'Exact file bytes/SHA required')
        paths.append(relative)
    require(len(set(paths)) == count and 'descriptor.mod' in paths, 'Duplicate file or missing descriptor')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(actual == set(paths), 'Actual mod file census differs from reviewed inventory')
    return [{'path': str(root / row['path']), 'bytes': row['bytes'], 'sha256': row['sha256']} for row in rows]


def prepare_case(context):
    # Shared preparation primitives authenticate/copy ordinary inputs only.
    from ck3_mod_acceptance_prepare import CONFIG_NAMES, checked_copy, pin, write_json, _outer_from_inner
    validate_contract(context)
    data, inputs = context['case_contract'], context['case_inputs']
    require(set(inputs) == {'product_dir', 'product_inventory', 'overlay_dir', 'plain_configuration'},
            'Control requires reviewed product, overlay and four plain configurations')
    require(set(inputs['plain_configuration']) == set(CONFIG_NAMES), 'All four explicit configurations required')
    seed = context['saved_campaign']
    require(set(seed) == {'save', 'bytes', 'sha256', 'player_id', 'date_raw'} and
            {k: seed[k] for k in data['saved_campaign']} == data['saved_campaign'], 'Exact R34 D2a saved seed required')
    seed_path = Path(seed['save']).resolve()
    require(seed_path.is_file() and seed_path.stat().st_size == seed['bytes'], 'Original external seed size differs')
    state, output = Path(context['state_dir']).resolve(), Path(context['output']).resolve()
    require(not state.exists(), 'Unused prepared state required')
    require(not seed_path.is_relative_to(state), 'Seed must remain outside unused prepared profile')
    production = _checked_json(inputs['product_inventory'])
    require(production['source_head'] == data['production_source_head'], 'Reviewed formal production HEAD differs')
    product, overlay = Path(inputs['product_dir']).resolve(), Path(inputs['overlay_dir']).resolve()
    product_rows = _inventory_rows(product, production['files'], data['production_file_count'])
    overlay_rows = _inventory_rows(overlay, data['overlay_files'], 6)
    profile = state / 'profile'
    profile.mkdir(parents=True)
    for name in CONFIG_NAMES:
        checked_copy(inputs['plain_configuration'][name], profile / name)
    products, enabled = [], []
    for name, rows in (('product', product_rows), ('transaction_control', overlay_rows)):
        target = profile / 'mod-content' / name
        root = product if name == 'product' else overlay
        for row in rows:
            checked_copy(row, target / Path(row['path']).relative_to(root))
        outer = profile / 'mod' / (name + '.mod')
        outer.parent.mkdir(exist_ok=True)
        with outer.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(_outer_from_inner(target / 'descriptor.mod', target))
        products.extend([pin(outer), *[pin(p) for p in sorted(target.rglob('*')) if p.is_file()]])
        enabled.append('mod/' + name + '.mod')
    write_json(profile / 'dlc_load.json', {'enabled_mods': enabled, 'disabled_dlcs': []})
    inventory_path = output / 'saved-product-inventory.json'
    write_json(inventory_path, {'schema': 'ck3-saved-campaign-product-only-profile-v1',
        'profile_path': str(profile), 'enabled_mods': enabled, 'product_files': products})
    # Complete profile inventory includes both mods, both outer descriptors,
    # all four configurations and dlc_load. Saves/logs/run remain absent.
    files = {p.relative_to(profile).as_posix(): pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    preparation = output / 'profile-preparation.json'
    write_json(preparation, {'schema': 'ck3-mod-acceptance-prepared-transaction-control-v1',
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
        'dependencies': [pin(Path(__file__).with_name('lyd_transaction_control.json'))],
        'expected': data['expected']})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': str(state),
        'saved_campaign': {**seed, 'save': str(seed_path), 'product_inventory': str(inventory_path)},
        'saved_campaign_startup_case_contract': str(hook)},
        'initial_plan': pin(initial), 'profile_preparation': pin(preparation),
        'startup_evidence': pin(startup), 'files': files, 'runtime_status': 'NOT_RUN',
        'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False}


def _positive(value, label):
    require(type(value) is int and value > 0, 'Positive integer required: ' + label)
    return value


def _scope(scope, kind, identity_key, identity):
    require(isinstance(scope, dict) and scope.get('status') == 'available' and scope.get('type_key') == kind,
            'Typed scope unavailable: ' + kind)
    typed = scope.get('typed_identity', {})
    require(typed.get('status') == 'available' and typed.get('kind') == kind and
            type(typed.get(identity_key)) is int and typed[identity_key] == identity, 'Typed scope identity differs')


def observe_event(snapshot, packet, expected, data):
    actor, instance = expected['actor_character_id'], expected['event_instance_id']
    for key in ('revision', 'native_revision', 'date_raw'):
        _positive(snapshot.get(key), key)
    require(snapshot.get('paused') is True and snapshot.get('map_ready') is True and
            snapshot.get('episode_projection') == 'native_campaign', 'Exact paused campaign required')
    require(snapshot['played_character']['character_id'] == actor and
            snapshot['active_event']['instance_id'] == instance and snapshot['date_raw'] == expected['date_raw'],
            'Actual actor/event/date differs')
    for key, snapshot_key in (('queried_snapshot_id', 'snapshot_id'), ('queried_revision', 'revision'),
                              ('queried_native_revision', 'native_revision')):
        require(type(packet.get(key)) is type(snapshot[snapshot_key]) and packet[key] == snapshot[snapshot_key],
                'Typed event queried frame differs: ' + key)
    event = packet.get('current_event_window_context', {})
    require(packet.get('status') == 'available' and event.get('schema') == 'current-event-window-context-v1' and
            event.get('status') == 'available' and event.get('event_definition_key') == expected['event_definition_key'] and
            event.get('current_event_instance_id') == instance and event.get('window_match_count') == 1 and
            event.get('date_raw') == expected['date_raw'] and event.get('snapshot_revision') == snapshot['native_revision'],
            'Exact current event definition/instance/frame unavailable')
    _scope(event.get('root_scope'), 'character', 'character_id', expected['root_character_id'])
    scopes = event.get('saved_scopes', [])
    for name, kind, key, identity in (('lyd_i3b_actor', 'character', 'character_id', actor),
                                    (data['new_title_scope'], 'landed_title', 'title_id', data['new_title_id'])):
        matches = [row for row in scopes if row.get('name') == name]
        require(len(matches) == 1, 'Unique saved scope required: ' + name)
        _scope(matches[0].get('scope'), kind, key, identity)
    readiness = event.get('readiness', {})
    require(all(readiness.get(key) is True for key in ('event_definition_identity_ready', 'root_scope_ready',
                'saved_scopes_ready', 'option_presentation_ready')), 'Typed current-event readiness missing')
    options = event.get('options', [])
    require(len(options) == len(expected['native_option_indices']), 'Exact option census differs')
    for rendered, (row, native) in enumerate(zip(options, expected['native_option_indices'])):
        require(type(row.get('native_option_index')) is int and row['native_option_index'] == native and
                type(row.get('rendered_index')) is int and row['rendered_index'] == rendered and
                row.get('shown') is True and row.get('enabled') is True and
                row.get('fallback') is False and row.get('cancel') is False, 'Exact shown enabled option differs')
    return {'queried_snapshot_id': snapshot['snapshot_id'], 'queried_revision': snapshot['revision'],
        'queried_native_revision': snapshot['native_revision'], 'new_title_scope': data['new_title_scope'],
        'new_title_id': data['new_title_id'], 'root_character_id': actor,
        'event_definition_key': event['event_definition_key'], 'event_instance_id': instance,
        'native_option_indices': [row['native_option_index'] for row in options], 'actions_submitted': 0}


def admit_saved_startup_event(context, snapshot, typed_event_packet):
    data = contract()
    require(context['expected'] == data['expected'], 'Saved startup expected identity differs')
    proof = observe_event(snapshot, typed_event_packet, context['expected'], data)
    proof['baseline_saved_campaign'] = data['saved_campaign']
    proof['production_source_head'] = data['production_source_head']
    return {**context['expected'], 'proof': proof, 'business_pass': False}


def observe_cache(frame, dto, data):
    for key, actual in {'queried_snapshot_id': frame['snapshot_id'], 'queried_revision': frame['revision'],
        'queried_native_revision': frame['native_revision'], 'date_raw': frame['date_raw'],
        'game_pid': frame['diagnostics']['bridge_pid'], 'connection_generation': frame['diagnostics']['connection_generation'],
        'player_character_id': data['expected']['actor_character_id']}.items():
        require(type(dto.get(key)) is type(actual) and dto[key] == actual, 'Cached succession frame differs: ' + key)
    cache = dto.get('native_result', {}).get('actor_cached_succession', {})
    ids = cache.get('complete_cached_successor_ids')
    require(cache.get('available') is True and cache.get('read_only') is True and cache.get('roster_complete') is True and
            type(cache.get('native_count')) is int and cache['native_count'] == 45 and isinstance(ids, list) and
            all(type(value) is int and value > 0 for value in ids) and ids == data['baseline_cached_succession'],
            'Complete ordered cached succession differs from original 45')
    require(cache.get('played_character_id') == data['expected']['actor_character_id'] and
            cache.get('played_character_full_id') == data['expected']['actor_character_id'] and
            cache.get('date_raw') == data['expected']['date_raw'], 'Native cached actor/date differs')
    return ids


def _reader(repo_root):
    path = Path(repo_root) / 'tools/lyd_i3b_checkpoint_readback/reader/i3b_checkpoint_reader.py'
    spec = importlib.util.spec_from_file_location('_transaction_control_saved_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_saved_control(reader, actor, titles, data):
    require(actor['character_id'] == data['expected']['actor_character_id'], 'Saved actor differs')
    require(reader.number(actor['variables'], data['completed_variable']) == 1, 'Saved empty transaction completion is not 1')
    succession = reader.one(actor['landed_data'], 'succession', required=True)
    require(isinstance(succession, list) and all(row['key'] is None for row in succession), 'Saved succession list shape differs')
    ids = [reader.scalar_id(row['value'], 'saved cached successor') for row in succession]
    require(ids == data['baseline_cached_succession'], 'Saved complete ordered succession differs')
    require(titles[data['new_title_id']]['holder'] is None, 'Saved new title acquired a holder')
    observed = {}
    for title_id, expected in data['political_title_ast_sha256'].items():
        row = titles[int(title_id)]
        actual = reader.ast_sha(row['entries'])
        require(actual == expected and row['AST_sha256'] == actual, 'Political complete AST differs: ' + title_id)
        observed[title_id] = actual
    return {'completed_variable': data['completed_variable'], 'completed_value': 1,
        'new_title_id': data['new_title_id'], 'new_title_holder': None,
        'political_title_ast_sha256': observed, 'complete_cached_successor_ids': ids,
        'political_full_ast_equal': True, 'saved_control_qualified': True,
        'business_pass': False, 'product_release_pass': False}


def read_saved_control(repo_root, checkpoint, data):
    require(checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == data['expected']['date_raw'] and
            checkpoint.get('episode_projection') == 'native_campaign', 'Actual saved campaign checkpoint required')
    path = Path(checkpoint['path']).resolve()
    # This is the one independent saved-body read. No baseline body is read.
    raw = path.read_bytes()
    require(len(raw) == checkpoint['size'] and hashlib.sha256(raw).hexdigest() == checkpoint['sha256'].lower(),
            'Actual checkpoint bytes/SHA differs')
    require(not raw.startswith(b'PK'), 'Plain checkpoint required by the existing reader')
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    reader, actor = _reader(repo_root), None
    for identity, entries in reader.records(reader.section(text, 'living', 'dead_unprunable'), 'living character'):
        if identity == data['expected']['actor_character_id']:
            require(actor is None, 'Duplicate saved actor')
            actor = reader.raw_character(identity, entries)
    wanted = {int(key) for key in data['political_title_ast_sha256']} | {data['new_title_id']}
    titles = {}
    for identity, entries in reader.title_database_records(text):
        if identity in wanted:
            require(identity not in titles, 'Duplicate saved control title')
            titles[identity] = reader.title_row(identity, entries)
    require(actor is not None and set(titles) == wanted, 'Complete saved actor/title control missing')
    facts = evaluate_saved_control(reader, actor, titles, data)
    return {**facts, 'checkpoint': {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
        'save_body_reads': 1, 'baseline_body_reads': 0}


def _call(client, name, tool, args, timeout=60):
    rows = client.execute_plan([{'id': name, 'tool': tool, 'args': args, 'fresh_revision': False}], name, timeout=timeout)
    require(len(rows) == 1 and rows[0].get('ok') is True, 'Original once-only tool result failed; never replay')
    return rows[0]['result']


def observe_terminal(client, data):
    """Read at most 60s under the original CaseClient Quit reserve; no action."""
    deadline, observations, ordinal = time.monotonic() + 60, [], 0
    while time.monotonic() < deadline:
        client.guard()
        ordinal += 1
        actual = _call(client, 'transaction-control-terminal-snapshot-' + str(ordinal).zfill(4),
            'ck3_take_snapshot', {'include_native_command_history': False}, timeout=deadline - time.monotonic())
        actual = client.validate_frame(actual, require_event_free=False)
        require(actual['played_character']['character_id'] == data['expected']['actor_character_id'] and
                actual['date_raw'] == data['expected']['date_raw'], 'Terminal observation changed actor/date')
        active = actual.get('active_event')
        observations.append(actual)
        if active is not None:
            instance = _positive(active.get('instance_id'), 'terminal event instance')
            if instance != data['expected']['event_instance_id']:
                client.checkpoint('transaction-control-terminal-observations', {'snapshots': observations,
                    'read_only': True, 'maximum_seconds': 60, 'actions_submitted': 0})
                return actual, instance
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(.5, remaining))
    raise TimeoutError('Terminal event not observed within original 60s bound; selection never replayed')


def run_case(context, client):
    validate_contract(context)
    data = context['case_contract']
    client.retain_process()
    before = client.snapshot(require_event_free=False)
    event = _call(client, 'transaction-control-initial-event', 'ck3_query_current_event_window_context_v1',
        {'event_instance_id': data['expected']['event_instance_id'], 'expected_revision': before['revision']})
    admitted = admit_saved_startup_event({'state_dir': context['state_dir'], 'expected': data['expected']}, before, event)
    cache_before = _call(client, 'transaction-control-cache-before', 'ck3_query_actor_cached_succession_v1',
                         {'expected_revision': before['revision']})
    ids_before = observe_cache(before, cache_before, data)
    client.checkpoint('transaction-control-before', {'frame': before, 'admission': admitted, 'cache': cache_before})
    selected = _call(client, 'transaction-control-select-once', 'ck3_select_event_option',
        {'event_instance_id': data['expected']['event_instance_id'], 'option_number': 1, 'expected_revision': before['revision']})
    require(selected.get('accepted') is True and selected.get('event_instance_id') == data['expected']['event_instance_id'] and
            selected.get('option_number') == 1 and selected.get('option_index') == 0, 'Original selection ACK differs; never replay')
    after, instance = observe_terminal(client, data)
    terminal = _call(client, 'transaction-control-terminal-event', 'ck3_query_current_event_window_context_v1',
                      {'event_instance_id': instance, 'expected_revision': after['revision']})
    expected_terminal = {**data['expected'], 'event_definition_key': data['terminal_event_definition_key'],
                         'event_instance_id': instance}
    terminal_proof = observe_event(after, terminal, expected_terminal, data)
    cache_after = _call(client, 'transaction-control-cache-after', 'ck3_query_actor_cached_succession_v1',
                        {'expected_revision': after['revision']})
    ids_after = observe_cache(after, cache_after, data)
    require(ids_before == ids_after, 'Cached succession changed after the single transaction')
    client.checkpoint('transaction-control-after', {'frame': after, 'selected': selected,
        'terminal_event': terminal, 'terminal_proof': terminal_proof, 'cache': cache_after})
    saved = _call(client, 'transaction-control-save-once', 'ck3_save_checkpoint', {'expected_revision': after['revision']})
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original save was not accepted')
    saved_facts = read_saved_control(context['repo_root'], saved['checkpoint'], data)
    facts = {'schema': 'ck3-mod-acceptance-transaction-control-result-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'case_contract_qualified': True,
        'gui_contract_qualified': True, 'transaction_control_pass': True, 'selected_option_number': 1,
        'business_actions_submitted': 1, 'terminal_event_instance_id': instance,
        'cache_before_ids': ids_before, 'cache_after_ids': ids_after, 'saved': saved_facts,
        'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False,
        'normal_close_pending': True, 'formal_institution_pass': None, 'C3': None, 'I4': None}
    client.checkpoint('transaction-control-case-result', facts)
    return facts


def verify_case(context):
    validate_contract(context)
    path = Path(context['output']) / 'transaction-control-case-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False,
            'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False,
            'status': 'NOT_RUN_OR_PRESERVED_FAILURE'}
    facts, data = read_json(path), context['case_contract']
    require(all(facts.get(key) == context[key] for key in ('run_id', 'product', 'case')), 'Control result crossed case/run')
    require(facts.get('transaction_control_pass') is True and facts.get('business_actions_submitted') == 1 and
            facts.get('selected_option_number') == 1 and facts.get('cache_before_ids') == data['baseline_cached_succession'] and
            facts.get('cache_after_ids') == data['baseline_cached_succession'], 'Complete once-only control proof missing')
    saved = facts['saved']
    require(saved.get('saved_control_qualified') is True and saved.get('political_full_ast_equal') is True and
            saved.get('political_title_ast_sha256') == data['political_title_ast_sha256'] and
            saved.get('completed_variable') == data['completed_variable'] and saved.get('completed_value') == 1 and
            saved.get('new_title_id') == data['new_title_id'] and saved.get('new_title_holder') is None and
            saved.get('complete_cached_successor_ids') == data['baseline_cached_succession'] and
            saved.get('save_body_reads') == 1 and saved.get('baseline_body_reads') == 0, 'Independent saved control proof missing')
    return {**facts, 'business_contract_applicable': False, 'business_pass': False, 'product_release_pass': False,
        'verification_scope': 'empty_transaction_control_only; public original normal-close boundary required'}
