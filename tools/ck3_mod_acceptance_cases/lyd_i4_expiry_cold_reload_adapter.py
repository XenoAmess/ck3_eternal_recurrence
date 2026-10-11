"""Public cold persistence of this run's qualified partial I4 natural expiry.

Reuse CaseClient and the natural case's decision/parser predicates. The adapter
never opens the expiry seed; ordinary public saved-input SHA admission remains.
One new cold SAVE is read once to observe the actually reloaded serialization,
including HoR which the upstream final observation did not explicitly qualify.
"""
import hashlib
import json
import os
from pathlib import Path

from ck3_mod_acceptance_cases import lyd_i3b_formal_b5_adapter as b5
from ck3_mod_acceptance_cases import lyd_i4_natural_expiry_adapter as natural

require = natural.require
checked = b5.checked
CREDIT_LIMITS = ('fresh_full_365_cycle', 'exact_expiry_date', 'formal_I3b', 'C3', 'I4_complete')


def contract():
    return natural.base.read_json(Path(__file__).with_name('lyd_i4_expiry_cold_reload.json'))


def validate_contract(context):
    data = context['case_contract']
    require(data == contract() and context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == 'i4-expiry-cold-reload' and
            data['maximum_natural_days'] == data['school_choice_actions'] == 0,
            'Exact partial I4 cold persistence contract required')


def qualified_normal_close(close):
    require(isinstance(close, dict) and close.get('normal_close_qualified') is True and
            close.get('retained_handle', {}).get('actual_retained_os0') is True and
            bool(close.get('native_zero_proof')) and bool(close.get('host_finished_at')) and
            close.get('managed_thread_finished') is True and close.get('cleanup_ok') is True and
            not close.get('host_error') and
            bool(close.get('root_normal_gui_review') or close.get('normal_quit_automation')),
            'Original qualified normal GUI/retained OS0/native0 close required')


def command_bytes(row):
    require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'Original command source/stdio ref3 required')
    raw = Path(row['path']).read_bytes()
    require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'].lower(),
            'Original command source/stdio bytes changed')
    return raw


def verified_public_argv(command, context, frozen):
    """Read the one authenticated existing wrapper marker; never execute it."""
    argv = command.get('argv', [])
    require(command.get('exit_code') == 0 and isinstance(argv, list) and
            all(isinstance(value, str) and value for value in argv), 'Original terminal public command exit0 required')
    direct = [i for i, value in enumerate(argv) if Path(value).name == 'ck3_mod_acceptance.py' and
              i + 1 < len(argv) and argv[i + 1] == 'verify']
    if len(direct) == 1:
        return argv  # Preserve the existing direct-public-CLI route and its downstream identity guards.
    require(len(argv) > 9 and argv[1:4] == ['-B', '-X', 'utf8'] and
            Path(argv[4]).name == 'with_selected_environment.py' and argv[5] == '--entry' and
            argv[7:9] == ['--execute', '--'] and argv[9] == 'verify',
            'Original existing wrapper must execute one explicit public verify')
    command_bytes({'path': argv[4], 'bytes': 2905,
        'sha256': '4e98c85d8aa9784b5b0f2958944affbb43ac489d0081b9c54e3fd0c99672a096'})
    public_args = argv[9:]
    runtime_path = Path(b5.argument(public_args, '--runtime')).resolve()
    runtime = natural.base.read_json(runtime_path)
    require(runtime.get('schema') == 'ck3-mod-acceptance-runtime-v1' and
            runtime['manifest'] == context['runtime_manifest'] == frozen['runtime_manifest'],
            'Original wrapper selected a different runtime manifest')
    manifest = checked(runtime['manifest'])
    require(manifest.get('schema') == 'ck3-mod-acceptance-shared-runtime-v1', 'Original selected shared manifest required')
    from ck3_mod_acceptance import path_at
    paths = {key: path_at(value, runtime_path.parent) for key, value in runtime['paths'].items()}
    parts = [paths[row['path_key']] if 'path_key' in row else paths[row['root_key']] / row['relative_path']
             for row in manifest['entry_environment']['PYTHONPATH_parts']]
    environment = {'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': os.pathsep.join(map(str, parts))}
    require(environment == frozen['runtime_environment'] and
            paths['source_root'] == Path(frozen['source_root']).resolve(),
            'Original wrapper environment/source differs from actual frozen binding')
    repo = path_at(runtime['repo_root'], runtime_path.parent)
    entry = repo / 'tools/ck3_mod_acceptance.py'
    python = path_at(runtime['python'], runtime_path.parent)
    require(repo == Path(context['repo_root']).resolve() == Path(command['cwd']).resolve() and
            Path(argv[6]).resolve() == entry and Path(argv[0]).resolve() == python == Path(frozen['argv'][0]).resolve(),
            'Original wrapper entry/python/cwd crossed the selected public runtime')
    records = []
    for line in command_bytes(command['stderr']).decode('utf-8-sig').splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get('mode') in ('EXECUTE_ONCE', 'EMIT_ONLY'):
            records.append(row)
    require(len(records) == 1, 'Exactly one original wrapper execution marker required')
    marker = records[0]
    expected = [str(python), '-B', '-X', 'utf8', str(entry), *public_args]
    require(marker.get('mode') == 'EXECUTE_ONCE' and marker.get('public_argv') == expected and
            marker.get('environment_applied_to_public_process') is True and
            marker.get('selected_runtime_environment') == environment and Path(marker['cwd']).resolve() == repo and
            marker.get('queue_mode') == 'Selected by CaseClient before each submission; no retry fallback' and
            marker.get('business_acceptance') == 'NOT_ASSESSED',
            'Original wrapper EXECUTE_ONCE public argv/cwd/environment marker differs')
    return marker['public_argv']


def upstream(context):
    """Authenticate original public verify, natural evidence and final SAVE descriptor."""
    validate_contract(context)
    inputs, data = context['case_inputs'], context['case_contract']
    require(set(inputs) == {'natural_expiry_verified_origin', 'expected_upstream_run_id'} and
            isinstance(inputs['expected_upstream_run_id'], str) and bool(inputs['expected_upstream_run_id']),
            'Explicit actual natural-expiry run and evidence bundle required')
    bundle = inputs['natural_expiry_verified_origin']
    require(isinstance(bundle, dict) and set(bundle) == {'prepared_case', 'run_context', 'public_verify_command'},
            'Original prepared/context/completed public verify ref3 required')
    prepared, run, command = (checked(bundle[k]) for k in ('prepared_case', 'run_context', 'public_verify_command'))
    require(prepared.get('schema') == 'ck3-mod-acceptance-prepared-case-v1' and
            prepared.get('product') == run.get('product') == data['product'] and
            prepared.get('case') == run.get('case') == data['upstream_case'] and
            run.get('schema') == 'ck3-mod-acceptance-run-context-v1' and
            run.get('prepared_case') == bundle['prepared_case'], 'Original natural prepared/run binding differs')
    require(context.get('runtime_manifest') == prepared['runtime_manifest'],
            'Cold case must retain the exact qualified natural shared runtime manifest')
    argv = command.get('argv', [])
    require(command.get('exit_code') == 0 and isinstance(argv, list) and
            all(isinstance(value, str) and value for value in argv), 'Original public verify exit0 required')
    frozen = checked(run['frozen_argv'])
    argv = verified_public_argv(command, context, frozen)
    entries = [i for i, value in enumerate(argv) if Path(value).name == 'ck3_mod_acceptance.py']
    require(len(entries) == 1 and entries[0] + 1 < len(argv) and argv[entries[0] + 1] == 'verify' and
            b5.argument(argv, '--product') == data['product'] and
            b5.argument(argv, '--case') == data['upstream_case'] and
            Path(b5.argument(argv, '--prepared-case')).resolve() == Path(bundle['prepared_case']['path']).resolve() and
            Path(b5.argument(argv, '--run-context')).resolve() == Path(bundle['run_context']['path']).resolve(),
            'Original public verify argv crossed product/case/prepared/run')
    facts = checked(command['stdout'])
    require(run.get('run_id') == inputs['expected_upstream_run_id'] and
            facts.get('run_id') == run['run_id'] == frozen['run_id'] and
            Path(run['run_dir']).resolve().name == run['run_id'] and
            frozen['runtime_manifest'] == prepared['runtime_manifest'], 'Original selected allocation/runtime differs')
    original_contract = checked(prepared['contract'])
    require(original_contract == natural.contract(), 'Original natural observation contract differs')
    original = natural.verify_case({'case_contract': original_contract, 'product': data['product'],
        'case': data['upstream_case'], 'run_id': run['run_id'], 'output': str(Path(run['run_dir']) / 'case-output')})
    require(all(facts.get(key) == value for key, value in original.items()),
            'Original verify stdout differs from retained natural case observations')
    require(facts.get('product') == data['product'] and facts.get('case') == data['upstream_case'] and
            facts.get('scope') == 'PARTIAL_EXISTING_COOLDOWN_OBSERVATION' and
            all(facts.get(key) is True for key in ('case_contract_qualified', 'gui_contract_qualified',
                'business_pass', 'case_acceptance_pass')) and facts.get('product_release_pass') is False,
            'Actual partial natural-expiry public PASS required')
    qualified_normal_close(facts.get('normal_close'))
    checkpoint = facts['saved']['checkpoint']
    require(set(checkpoint) == {'path', 'size', 'sha256', 'date_raw'} and
            type(checkpoint['size']) is int and checkpoint['size'] > 0 and
            type(checkpoint['date_raw']) is int and checkpoint['date_raw'] > 0 and
            isinstance(checkpoint['sha256'], str) and len(checkpoint['sha256']) == 64 and
            all(c in '0123456789abcdef' for c in checkpoint['sha256'].lower()), 'Actual final SAVE descriptor required')
    seed = context['saved_campaign']
    require(set(seed) in ({'save', 'bytes', 'sha256', 'player_id', 'date_raw'},
                         {'save', 'bytes', 'sha256', 'player_id', 'date_raw', 'product_inventory'}) and
            Path(seed['save']).resolve() == Path(checkpoint['path']).resolve() and
            seed['bytes'] == checkpoint['size'] and seed['sha256'].lower() == checkpoint['sha256'].lower() and
            seed['date_raw'] == checkpoint['date_raw'] == facts['natural_intervals'][-1]['date_raw'] and
            seed['player_id'] == original_contract['saved_campaign']['player_id'] == data['actor_id'],
            'Cold seed must be this exact qualified expiry final SAVE, never0240/initial/failed world')
    return {'bundle': bundle, 'prepared': prepared, 'facts': facts, 'checkpoint': checkpoint,
            'verification': command['stdout'], 'seed': {k: seed[k] for k in ('save', 'bytes', 'sha256', 'player_id', 'date_raw')}}


def prepare_case(context):
    from ck3_mod_acceptance_prepare import materialize_product_profile, pin, write_json
    origin = upstream(context)  # No writes before actual expiry/verify/normal-close qualification.
    inputs, seed = origin['prepared']['case_inputs'], origin['seed']
    source = Path(seed['save']).resolve()
    state, output = Path(context['state_dir']).resolve(), Path(context['output']).resolve()
    require(source.is_file() and source.stat().st_size == seed['bytes'] and not state.exists() and
            not source.is_relative_to(state), 'Unused state outside actual expiry SAVE required')
    inventory = checked(inputs['product_inventory'])
    product = Path(inputs['product_dir']).resolve()
    rows = natural.base._inventory_rows(product, inventory['files'], len(inventory['files']))
    for row in rows:
        raw = Path(row['path']).read_bytes()
        require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Original formal product bytes differ')
    profile = materialize_product_profile(context, product, inputs['plain_configuration'])
    preparation = output / 'profile-preparation.json'
    write_json(preparation, {'schema': 'ck3-mod-acceptance-prepared-i4-expiry-cold-v1', **profile,
        'saved_campaign': seed, 'source_inventory': inputs['product_inventory'],
        'natural_expiry_verified_origin': origin['bundle'], 'runtime_status': 'NOT_RUN', 'business_pass': False})
    startup = state / 'preparation.json'
    write_json(startup, {'schema': 'ck3-mod-acceptance-profile-startup-evidence-v1',
        'profile_dir': profile['profile'], 'profile_files': list(profile['files']),
        'profile_input_sha256': {key: row['sha256'] for key, row in profile['files'].items()},
        'preparation': pin(preparation), 'runtime_status': 'NOT_RUN'})
    initial = output / 'initial-plan.json'
    write_json(initial, {'steps': []})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': str(state), 'saved_campaign': {
        **seed, 'save': str(source), 'product_inventory': profile['product_inventory']['path']}},
        'initial_plan': pin(initial), 'profile_preparation': pin(preparation), 'startup_evidence': pin(startup),
        'files': profile['files'], 'runtime_status': 'NOT_RUN', 'business_contract_applicable': True,
        'business_pass': False, 'product_release_pass': False}


def evaluate_cold_saved(reader, actor, faith, rite, data):
    facts = natural.evaluate_saved(reader, actor, faith, rite, data, False)
    require(rite['heads']['head_of_rite'] == str(data['head_of_rite_id']), 'Actual cold saved HoR differs')
    return {**facts, 'head_of_rite_id': data['head_of_rite_id'], 'head_of_rite_explicitly_observed': True}


def read_cold_saved(context, checkpoint, date_raw, data, seed):
    require(checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == date_raw and
            checkpoint.get('episode_projection') == 'native_campaign', 'Actual paused cold SAVE required')
    path = Path(checkpoint['path']).resolve()
    require(path != Path(seed['save']).resolve(), 'Never overwrite or parse the expiry seed as the cold SAVE')
    raw = path.read_bytes()  # One new cold serialization read; no seed read or copy.
    require(len(raw) == checkpoint['size'] and hashlib.sha256(raw).hexdigest() == checkpoint['sha256'].lower() and
            not raw.startswith(b'PK'), 'Actual new plain cold SAVE size/SHA differs')
    text, reader = raw.decode('utf-8-sig').replace('\r\n', '\n'), natural.base._reader(context['repo_root'])
    actors = [reader.raw_character(cid, entries) for cid, entries in
        reader.records(reader.section(text, 'living', 'dead_unprunable'), 'living character') if cid == data['actor_id']]
    require(len(actors) == 1, 'Unique actual cold saved actor required')
    faiths, rites = reader.graph(text, 'faiths', 'main_rite'), reader.graph(text, 'rites', 'faith')
    facts = evaluate_cold_saved(reader, actors[0], faiths[data['faith_id']], rites[data['rite_id']], data)
    return {**facts, 'checkpoint': {key: checkpoint[key] for key in ('path', 'size', 'sha256', 'date_raw')},
        'save_body_reads': 1, 'baseline_body_reads': 0, 'additional_checkpoint_copies': 0}


def assessment(facts, origin, data):
    seed, saved, initial, observation = origin['seed'], facts['cold_saved'], facts['initial_frame'], facts['decision']
    frame = observation['frame']
    require(initial['paused'] is True and frame['paused'] is True and
            initial.get('active_event') is None and frame.get('active_event') is None and
            natural.frame_identity(initial) == natural.frame_identity(frame) and
            frame['played_character']['character_id'] == seed['player_id'] == data['actor_id'] and
            frame['date_raw'] == seed['date_raw'] == saved['checkpoint']['date_raw'], 'Cold loaded paused identity/date differs')
    for model in (observation['model_before'], observation['model_after']):
        natural.observe_model(frame, model, data['decision_key'])
    require(natural.confirm_enabled(observation['detail_tree']) is True and observation['confirm_enabled'] is True and
            observation['decision_executed'] is False, 'Actual cold selected school decision is not enabled/read-only')
    require(saved['school_cooldown_present'] is False and saved['raw_tick_observed'] is None and
            saved['actor_id'] == data['actor_id'] and saved['faith_id'] == data['faith_id'] and saved['rite_id'] == data['rite_id'] and
            saved['head_of_rite_id'] == data['head_of_rite_id'] and
            all(saved.get(key) is True for key in ('headless', 'membership_present', 'landed_alive', 'head_of_rite_explicitly_observed')) and
            saved['save_body_reads'] == 1 and saved['baseline_body_reads'] == 0 and saved['additional_checkpoint_copies'] == 0 and
            Path(saved['checkpoint']['path']).resolve() != Path(seed['save']).resolve(), 'Cold saved persistence predicates differ')
    require(facts['natural_days'] == facts['school_choice_actions'] == 0 and
            facts['cold_SAVE_actions'] == 1 and all(facts[key] is None for key in CREDIT_LIMITS) and
            facts['product_release_pass'] is False, 'Partial cold observation acquired unsupported mutation/credit')
    return True


def run_case(context, client):
    origin, data = upstream(context), {**context['case_contract'], 'saved_campaign': context['saved_campaign']}
    client.retain_process()
    initial = client.snapshot()
    require(initial['played_character']['character_id'] == data['actor_id'] and initial['date_raw'] == origin['seed']['date_raw'],
            'Actually loaded cold player/date differs from qualified expiry SAVE')
    _, frame = natural._call(client, 'i4-cold-open-decisions', 'ck3_open_ingame_decisions_v1',
        {'expected_revision': initial['revision']}, initial)
    selected, _ = natural._call(client, 'i4-cold-select-detail', 'ck3_select_ingame_decision_item_v1',
        {'decision_key': data['decision_key'], 'expected_revision': frame['revision']}, frame)
    decision = natural.observe_decision(client, data, 0)
    selection = natural.validate_selected(selected, frame, decision, data['decision_key'])
    require(decision['confirm_enabled'] is True, 'Cold school decision is not actually enabled')
    saved, _ = natural._call(client, 'i4-cold-only-save-once', 'ck3_save_checkpoint',
        {'expected_revision': decision['frame']['revision']}, decision['frame'])
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original cold SAVE not accepted')
    cold = read_cold_saved(context, saved['checkpoint'], initial['date_raw'], data, origin['seed'])
    facts = {'schema': 'ck3-mod-acceptance-i4-expiry-cold-result-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'scope': data['scope'],
        'upstream_natural_verification': origin['verification'], 'cold_seed': origin['seed'],
        'initial_frame': initial, 'decision': decision, 'selection_proof': selection, 'cold_saved': cold,
        'natural_days': 0, 'school_choice_actions': 0, 'cold_SAVE_actions': 1,
        **{key: None for key in CREDIT_LIMITS}, 'product_release_pass': False, 'business_contract_applicable': True,
        'normal_close_pending': True}
    passed = assessment(facts, origin, data)
    facts.update(cold_reload_persistence_pass=passed, case_contract_qualified=passed, gui_contract_qualified=passed, business_pass=passed)
    client.checkpoint('i4-expiry-cold-reload-case-result', facts)
    return facts


def verify_case(context):
    validate_contract(context)
    path = Path(context['output']) / 'i4-expiry-cold-reload-case-result.json'
    if not path.is_file():
        return {'status': 'NOT_RUN_OR_PRESERVED_FAILURE', 'case_contract_qualified': False, 'gui_contract_qualified': False,
            'business_contract_applicable': True, 'business_pass': False, 'product_release_pass': False}
    origin, facts = upstream(context), natural.base.read_json(path)
    require(all(facts.get(key) == context[key] for key in ('run_id', 'product', 'case')) and
            facts['scope'] == context['case_contract']['scope'] and facts['upstream_natural_verification'] == origin['verification'] and
            facts['cold_seed'] == origin['seed'], 'Cold result crossed run/origin/seed')
    passed = assessment(facts, origin, context['case_contract'])
    require(all(facts.get(key) is passed for key in ('cold_reload_persistence_pass', 'case_contract_qualified',
        'gui_contract_qualified', 'business_pass')), 'Cold result assessment differs from actual observations')
    return {**facts, 'verification_scope': context['case_contract']['scope'] + '; shared original normal close still required'}
