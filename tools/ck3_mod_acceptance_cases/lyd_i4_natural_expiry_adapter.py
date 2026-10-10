"""Observe an existing school cooldown through natural simulation and two SAVEs.

This is a partial existing-cooldown observation, never a fresh 365-day cycle.
Only the public CaseClient controls the shared runtime and normal shutdown.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ck3_mod_acceptance_cases import lyd_transaction_control_adapter as base

require = base.require


def contract():
    return base.read_json(Path(__file__).with_name('lyd_i4_natural_expiry.json'))


def validate_contract(context):
    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == 'i4-existing-school-cooldown', 'Selected natural observation differs')
    require(data == contract() and data['maximum_natural_days'] == 366 and
            data['scope'] == 'PARTIAL_EXISTING_COOLDOWN_OBSERVATION', 'Frozen partial observation contract differs')


def validate_origin(origin, seed, data):
    require(set(seed) == {'save', 'bytes', 'sha256', 'player_id', 'date_raw'} and
            {k: seed[k] for k in data['saved_campaign']} == data['saved_campaign'], 'Exact original0240 seed required')
    require(origin['schema'] == 'lyd.i3b0240.cached-baseline.v1' and
            all(origin['historical_save'][k] == seed[k] for k in ('bytes', 'sha256')) and
            origin['historical_frame']['actor'] == seed['player_id'] and
            origin['historical_frame']['date_raw'] == seed['date_raw'] and
            origin['historical_frame']['paused'] is True and
            origin['historical_frame']['active_event'] is None and
            origin['historical_frame']['pending_interaction'] is None, 'Original seed observation differs')
    require(origin['roles'] == data['origin_roles'], 'Headless Faith/Rite origin differs')
    flag = origin['school_study_CD']['lyd_school_cooldown']
    require(isinstance(flag, dict) and flag.get('present') is True and flag.get('type') is None and
            flag.get('entries') == [] and flag.get('identity') is None and
            isinstance(flag.get('tick'), str) and flag['tick'].isdigit() and
            flag.get('row_entries') == [{'key': 'flag', 'value': 'lyd_school_cooldown'},
                {'key': 'tick', 'value': flag['tick']}, {'key': 'data', 'value': []}],
            'Initial actual flag must be present in the qualified raw flag shape')
    return {'initial_flag_present': True, 'raw_tick_observed': flag['tick'],
            'expiry_date': None, 'remaining_days': None, 'tick_interpretation': 'UNQUALIFIED'}


def prepare_case(context):
    from ck3_mod_acceptance_prepare import materialize_product_profile, pin, write_json
    validate_contract(context)
    data, inputs, seed = context['case_contract'], context['case_inputs'], context['saved_campaign']
    require(set(inputs) == {'product_dir', 'product_inventory', 'plain_configuration', 'origin_metadata'},
            'Only formal product, four plain configurations and exact origin metadata are accepted')
    require({k: inputs['origin_metadata'][k] for k in ('bytes', 'sha256')} == data['origin_metadata_pin'],
            'Original0240 metadata pin differs')
    initial = validate_origin(base._checked_json(inputs['origin_metadata']), seed, data)
    seed_path, state, output = Path(seed['save']).resolve(), Path(context['state_dir']).resolve(), Path(context['output']).resolve()
    require(seed_path.is_file() and seed_path.stat().st_size == seed['bytes'] and
            not state.exists() and not seed_path.is_relative_to(state), 'Fresh state outside the original save required')
    inventory = base._checked_json(inputs['product_inventory'])
    require(isinstance(inventory.get('source_head'), str) and len(inventory['source_head']) == 40,
            'Actual production source HEAD required')
    product = Path(inputs['product_dir']).resolve()
    rows = base._inventory_rows(product, inventory['files'], len(inventory['files']))
    # Authenticate before the shared product-only copier. No fixture or overlay.
    for row in rows:
        raw = Path(row['path']).read_bytes()
        require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Production bytes differ')
    profile = materialize_product_profile(context, product, inputs['plain_configuration'])
    preparation = output / 'profile-preparation.json'
    write_json(preparation, {'schema': 'ck3-mod-acceptance-prepared-i4-natural-expiry-v1',
        **profile, 'saved_campaign': seed, 'source_head': inventory['source_head'],
        'source_inventory': inputs['product_inventory'], 'origin_metadata': inputs['origin_metadata'],
        'initial_flag': initial, 'runtime_status': 'NOT_RUN', 'business_pass': False})
    startup = state / 'preparation.json'
    write_json(startup, {'schema': 'ck3-mod-acceptance-profile-startup-evidence-v1',
        'profile_dir': profile['profile'], 'profile_files': list(profile['files']),
        'profile_input_sha256': {k: v['sha256'] for k, v in profile['files'].items()},
        'preparation': pin(preparation), 'runtime_status': 'NOT_RUN'})
    initial_plan = output / 'initial-plan.json'
    write_json(initial_plan, {'steps': []})
    return {'startup': {'mode': 'saved_campaign', 'state_dir': str(state),
        'saved_campaign': {**seed, 'save': str(seed_path), 'product_inventory': profile['product_inventory']['path']}},
        'initial_plan': pin(initial_plan), 'profile_preparation': pin(preparation),
        'startup_evidence': pin(startup), 'files': profile['files'], 'runtime_status': 'NOT_RUN',
        'business_contract_applicable': True, 'business_pass': False, 'product_release_pass': False}


def frame_identity(frame):
    return (frame['diagnostics']['bridge_pid'], frame['diagnostics']['connection_generation'],
            frame['played_character']['character_id'], frame['date_raw'])


def same_paused_identity(client, before, after):
    client.validate_frame(before)
    client.validate_frame(after)
    require(frame_identity(before) == frame_identity(after), 'Observation crossed actual paused actor/date/connection')


def observe_model(frame, model, decision_key):
    require(model.get('schema') == 'ck3-ingame-decision-item-v1' and model.get('read_only') is True and
            model.get('available') is True and model.get('decision_key') == decision_key and
            model.get('detail_decision_key') == decision_key and model.get('matching_row_count') == 1,
            'Exact selected school decision model unavailable')
    for key in ('owner_thread_verified', 'frame_verified', 'source_abi_pins_verified', 'gui_owner_binding_verified',
                'decisions_tree_complete', 'decisions_root_visible', 'row_owner_verified', 'detail_tree_complete',
                'detail_root_visible', 'detail_definition_available', 'detail_definition_matches_target',
                'detail_actor_binding_verified'):
        require(model.get(key) is True, 'Actual decision qualification missing: ' + key)
    expected = {'native_revision': frame['native_revision'], 'connection_generation': frame['diagnostics']['connection_generation'],
        'game_pid': frame['diagnostics']['bridge_pid'], 'played_character_id': frame['played_character']['character_id'],
        'date_raw': frame['date_raw'], 'detail_actor_reference_key': frame['played_character']['character_id']}
    require(all(type(model.get(k)) is type(v) and model[k] == v for k, v in expected.items()), 'Decision model frame differs')


def validate_selected(selected, action_frame, observation, decision_key):
    """Accept the official later proof without reinterpreting the original ACK."""
    require(selected.get('schema') == 'ck3-ingame-decision-item-action-v1' and
            selected.get('step') == 'select-ingame-decision-item-v1' and selected.get('action') == 'select' and
            selected.get('decision_key') == decision_key and selected.get('postcondition_verified') is True and
            selected.get('status') == 'verified_selected_detail' and selected.get('verification_pending') is False,
            'Official later selected-detail completion not proved; never replay')
    observe_model(action_frame, selected.get('later_actual_observation', {}), decision_key)
    require(frame_identity(observation['frame']) == frame_identity(action_frame), 'Selected detail crossed actual paused frame')
    observe_model(observation['frame'], observation['model_after'], decision_key)
    return {'completion_source': 'official_later_actual_observation_and_independent_current_model',
        'postcondition_verified': True, 'original_ack_selected_after_verified': selected.get('selected_after_verified'),
        'original_ack_unchanged': True, 'decision_key': decision_key}


def confirm_enabled(tree):
    """Read the stock footer using the same named anchors as ConfirmReceiver.

    Missing, truncated or ambiguous layouts never mean disabled or enabled.
    No receiver is invoked and available-model is never used as eligibility.
    """
    require(tree.get('schema') == 'ck3-native-gui-window-tree-inspection-v1' and
            tree.get('window_kind') == 'decision_detail' and tree.get('scope_root_name') == 'decisiondetail_view' and
            tree.get('read_only') is True and tree.get('accepted') is True and tree.get('status') == 'available' and
            tree.get('root_available') is True and tree.get('truncated') is False, 'Complete actual decision detail tree required')
    rows = tree.get('widgets')
    require(isinstance(rows, list) and tree.get('widget_count') == len(rows), 'Actual widget census differs')
    by_path = {row['child_path']: row for row in rows}
    require(len(by_path) == len(rows), 'Ambiguous widget paths')
    def named(name):
        matches = [row for row in rows if row['runtime_name'] == name]
        require(len(matches) == 1, 'Unique native footer anchor required: ' + name)
        return matches[0]['child_path']
    def parent(path):
        parts = path.rsplit('/', 1)
        require(len(parts) == 2 and parts[1].isdigit(), 'Native footer anchor path malformed')
        return parts[0], int(parts[1])
    footer, cost_index = parent(named('cost'))
    custom, back_index = parent(named('back'))
    regular, highlight_index = parent(named('cram_study_start_tutorial_highlight'))
    require((cost_index, back_index, highlight_index) == (0, 0, 2) and
            parent(regular) == (footer, 2) and parent(custom) == (footer, 3) and
            by_path[footer]['child_count'] == 7 and by_path[regular]['child_count'] == 3 and
            by_path[custom]['child_count'] == 2, 'Stock footer topology differs')
    require(by_path['']['runtime_name'] == 'decisiondetail_view' and by_path['']['effective_visible'] is True,
            'Actual selected detail root hidden')
    buttons = [by_path[branch + '/1'] for branch in (regular, custom)]
    require(all(row['runtime_name'] == '' and type(row.get('enabled')) is bool and
                type(row.get('effective_visible')) is bool for row in buttons), 'Stock confirm leaves malformed')
    visible = [row for row in buttons if row['effective_visible']]
    require(len(visible) == 1, 'Actual visible confirm is missing or ambiguous')
    return visible[0]['enabled']


def _call(client, name, tool, args, frame):
    rows = client.execute_plan([{'id': name, 'tool': tool, 'args': args, 'fresh_revision': False}], name)
    require(len(rows) == 1 and rows[0].get('ok') is True, 'Original public action failed; never replay')
    after = rows[0]['after_snapshot']
    same_paused_identity(client, frame, after)
    return rows[0]['result'], after


def observe_decision(client, data, ordinal):
    frame = client.snapshot()
    prefix = 'i4-school-observation-' + str(ordinal).zfill(4)
    model, frame_after = _call(client, prefix + '-model-before', 'ck3_query_ingame_decision_item_v1',
        {'decision_key': data['decision_key'], 'expected_revision': frame['revision']}, frame)
    observe_model(frame, model, data['decision_key'])
    tree, after_tree = _call(client, prefix + '-detail-tree', 'ck3_inspect_gui_window_tree_v1',
        {'window_kind': 'decision_detail'}, frame_after)
    final_model, after_model = _call(client, prefix + '-model-after', 'ck3_query_ingame_decision_item_v1',
        {'decision_key': data['decision_key'], 'expected_revision': after_tree['revision']}, after_tree)
    observe_model(after_tree, final_model, data['decision_key'])
    enabled = confirm_enabled(tree)
    proof = {'frame': after_model, 'model_before': model, 'detail_tree': tree,
        'model_after': final_model, 'confirm_enabled': enabled, 'decision_executed': False}
    client.checkpoint(prefix, proof)
    return proof


def validate_day(row, before, initial, elapsed, maximum_days):
    value = row['result']
    require(row.get('ok') is True and value.get('requested_days') == 1 and
            value.get('requested_interval_complete') is True and value.get('event_boundary') is None,
            'Actual one-day natural interval required; events fail closed')
    after = value['after']
    hours = value.get('elapsed_hours')
    require(frame_identity(value['before']) == frame_identity(before) and
            frame_identity(after)[:3] == frame_identity(initial)[:3] and
            value['before'].get('paused') is True and after.get('paused') is True and
            value['before'].get('active_event') is None and after.get('active_event') is None and
            type(hours) is int and 24 <= hours < 48 and after['date_raw'] - before['date_raw'] == hours and
            elapsed + hours == after['date_raw'] - initial['date_raw'] and
            0 < elapsed + hours <= maximum_days * 24, 'Natural duration/identity/cap differs')
    return elapsed + hours


def evaluate_saved(reader, actor, faith, rite, data, cooldown_present):
    require(actor['character_id'] == data['saved_campaign']['player_id'] and actor['rite_id'] == data['rite_id'] and
            isinstance(actor['landed_data'], list), 'Saved alive landed actor/Faith/Rite changed')
    require(actor['variables'].get('lyd_enabled', {}).get('present') is True, 'Saved membership flag missing')
    flag = actor['variables'].get('lyd_school_cooldown')
    if cooldown_present:
        require(isinstance(flag, dict) and flag.get('present') is True and flag.get('type') is None and
                flag.get('entries') == [] and flag.get('identity') is None and
                isinstance(flag.get('tick'), str) and flag['tick'].isdigit() and
                flag.get('row_entries') == [{'key': 'flag', 'value': 'lyd_school_cooldown'},
                    {'key': 'tick', 'value': flag['tick']}, {'key': 'data', 'value': []}],
                'Fresh initial SAVE must contain the actual unqualified raw cooldown flag')
    else:
        require(flag is None, 'Final SAVE still contains the cooldown flag')
    require(faith['id'] == data['faith_id'] and faith['heads']['religious_head'] == '4294967295' and
            faith['heads']['religious_head_title'] is None and faith['main_rite'] == str(data['rite_id']) and
            rite['id'] == data['rite_id'] and rite['faith'] == str(data['faith_id']), 'Saved headless Faith/main Rite binding changed')
    return {'school_cooldown_present': cooldown_present, 'raw_tick_observed': flag['tick'] if flag else None,
        'actor_id': actor['character_id'], 'faith_id': faith['id'],
        'rite_id': rite['id'], 'headless': True, 'membership_present': True, 'landed_alive': True,
        'expiry_date': None, 'remaining_days': None, 'other_eligibility_confirmed_by_actual_enabled_decision': not cooldown_present}


def read_saved(context, checkpoint, date_raw, data, cooldown_present):
    require(checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == date_raw and
            checkpoint.get('episode_projection') == 'native_campaign', 'Actual scoped saved checkpoint required')
    raw = Path(checkpoint['path']).read_bytes()  # Each new checkpoint body once; never open the original seed.
    require(len(raw) == checkpoint['size'] and hashlib.sha256(raw).hexdigest() == checkpoint['sha256'].lower() and
            not raw.startswith(b'PK'), 'Exact plain final checkpoint required')
    text, reader = raw.decode('utf-8-sig').replace('\r\n', '\n'), base._reader(context['repo_root'])
    actors = [reader.raw_character(cid, entries) for cid, entries in
        reader.records(reader.section(text, 'living', 'dead_unprunable'), 'living character')
        if cid == data['saved_campaign']['player_id']]
    require(len(actors) == 1, 'Unique saved actor required')
    faiths, rites = reader.graph(text, 'faiths', 'main_rite'), reader.graph(text, 'rites', 'faith')
    facts = evaluate_saved(reader, actors[0], faiths[data['faith_id']], rites[data['rite_id']], data, cooldown_present)
    retained = {k: checkpoint[k] for k in ('path', 'size', 'sha256', 'date_raw')}
    if cooldown_present:
        # The public tool reuses a fixed path. Preserve these already-read bytes
        # before advancing or submitting the distinct final SAVE.
        target = Path(context['output']) / 'initial-school-cooldown-checkpoint.ck3'
        require(target.resolve() != Path(checkpoint['path']).resolve(), 'Initial preservation must use a separate path')
        with target.open('xb') as stream:
            require(stream.write(raw) == len(raw), 'Initial checkpoint preservation incomplete')
        retained = {**retained, 'path': str(target.resolve())}
    return {**facts, 'checkpoint': {k: checkpoint[k] for k in ('path', 'size', 'sha256', 'date_raw')},
        'preserved_checkpoint': retained, 'save_body_reads': 1, 'baseline_body_reads': 0}


def run_case(context, client):
    validate_contract(context)
    data = context['case_contract']
    original_seed = {k: context['saved_campaign'][k] for k in ('save', 'bytes', 'sha256', 'player_id', 'date_raw')}
    origin = validate_origin(base._checked_json(context['case_inputs']['origin_metadata']), original_seed, data)
    client.retain_process()
    initial = client.snapshot()
    require(initial['played_character']['character_id'] == data['saved_campaign']['player_id'] and
            initial['date_raw'] == data['saved_campaign']['date_raw'], 'Initial loaded actor/date differs from exact seed')
    _, frame = _call(client, 'i4-school-open-decisions', 'ck3_open_ingame_decisions_v1',
        {'expected_revision': initial['revision']}, initial)
    selected, _ = _call(client, 'i4-school-select-detail', 'ck3_select_ingame_decision_item_v1',
        {'decision_key': data['decision_key'], 'expected_revision': frame['revision']}, frame)
    first = observe_decision(client, data, 0)
    selection_proof = validate_selected(selected, frame, first, data['decision_key'])
    require(first['confirm_enabled'] is False, 'Initially enabled decision cannot credit existing cooldown disappearance')
    initial_save, after_save = _call(client, 'i4-natural-initial-save-once', 'ck3_save_checkpoint',
        {'expected_revision': first['frame']['revision']}, first['frame'])
    require(initial_save.get('accepted') is True and initial_save.get('step') == 'save-checkpoint', 'Initial SAVE not accepted')
    initial_saved = read_saved(context, initial_save['checkpoint'], initial['date_raw'], data, True)
    client.checkpoint('i4-natural-origin', {'origin': origin, 'initial_frame': initial, 'decision': first,
        'initial_saved': initial_saved, 'selection_proof': selection_proof,
        'origin_metadata': context['case_inputs']['origin_metadata'], 'source_inventory': context['case_inputs']['product_inventory']})
    before, elapsed, intervals, final = after_save, 0, [], None
    for ordinal in range(1, data['maximum_natural_days'] + 1):
        require(elapsed + 24 <= data['maximum_natural_days'] * 24, 'Natural 366-day duration exhausted')
        row = client.advance_day(days=1, timeout=data['one_day_timeout'])
        elapsed = validate_day(row, before, initial, elapsed, data['maximum_natural_days'])
        proof = observe_decision(client, data, ordinal)
        require(frame_identity(proof['frame']) == frame_identity(row['result']['after']), 'Observation moved after natural pause')
        intervals.append({'step_id': row['id'], 'elapsed_hours': row['result']['elapsed_hours'],
            'date_raw': proof['frame']['date_raw'], 'confirm_enabled': proof['confirm_enabled']})
        before = proof['frame']
        if proof['confirm_enabled']:
            final = proof
            break
    require(final is not None, 'School decision never enabled within natural cap; preserve RED without replay')
    saved, _ = _call(client, 'i4-natural-final-save-once', 'ck3_save_checkpoint',
        {'expected_revision': final['frame']['revision']}, final['frame'])
    require(saved.get('accepted') is True and saved.get('step') == 'save-checkpoint', 'Original final SAVE not accepted')
    saved_facts = read_saved(context, saved['checkpoint'], final['frame']['date_raw'], data, False)
    facts = {'schema': 'ck3-mod-acceptance-i4-existing-cooldown-result-v1', 'run_id': context['run_id'],
        'product': context['product'], 'case': context['case'], 'scope': data['scope'],
        'case_contract_qualified': True, 'gui_contract_qualified': True, 'business_contract_applicable': True,
        'business_pass': True, 'product_release_pass': False, 'initial_flag': origin, 'initial_saved': initial_saved,
        'initial_confirm_enabled': False, 'final_confirm_enabled': True, 'natural_intervals': intervals,
        'elapsed_natural_hours': elapsed, 'elapsed_natural_days': elapsed / 24,
        'days_are_actual_simulation_duration': True, 'saved': saved_facts, 'normal_close_pending': True,
        'fresh_full_365_cycle': None, 'exact_expiry_date': None, 'cold_reload': None,
        'formal_I3b': None, 'C3': None, 'I4_complete': None, 'school_choice_actions': 0}
    client.checkpoint('i4-existing-school-cooldown-case-result', facts)
    return facts


def verify_case(context):
    validate_contract(context)
    path = Path(context['output']) / 'i4-existing-school-cooldown-case-result.json'
    if not path.is_file():
        return {'status': 'NOT_RUN_OR_PRESERVED_FAILURE', 'case_contract_qualified': False,
            'gui_contract_qualified': False, 'business_contract_applicable': True, 'business_pass': False,
            'product_release_pass': False}
    facts, data = base.read_json(path), context['case_contract']
    require(all(facts[k] == context[k] for k in ('run_id', 'product', 'case')) and facts['scope'] == data['scope'],
            'Natural observation crossed run/case')
    require(facts['initial_flag']['initial_flag_present'] is True and facts['initial_confirm_enabled'] is False and
            facts['final_confirm_enabled'] is True and facts['school_choice_actions'] == 0 and
            facts['initial_saved']['school_cooldown_present'] is True and facts['initial_saved']['headless'] is True and
            facts['initial_saved']['save_body_reads'] == 1 and facts['initial_saved']['baseline_body_reads'] == 0 and
            Path(facts['initial_saved']['preserved_checkpoint']['path']).resolve() !=
                Path(facts['saved']['checkpoint']['path']).resolve() and
            facts['saved']['save_body_reads'] == 1 and facts['saved']['baseline_body_reads'] == 0 and
            facts['saved']['school_cooldown_present'] is False and facts['saved']['headless'] is True,
            'Existing flag/decision/SAVE observations incomplete')
    intervals = facts['natural_intervals']
    require(isinstance(intervals, list) and 1 <= len(intervals) <= data['maximum_natural_days'] and
            len({row['step_id'] for row in intervals}) == len(intervals) and
            all(type(row['elapsed_hours']) is int and 24 <= row['elapsed_hours'] < 48 for row in intervals) and
            all(row['confirm_enabled'] is False for row in intervals[:-1]) and intervals[-1]['confirm_enabled'] is True and
            sum(row['elapsed_hours'] for row in intervals) == facts['elapsed_natural_hours'] and
            0 < facts['elapsed_natural_hours'] <= 24 * data['maximum_natural_days'] and
            facts['elapsed_natural_days'] == facts['elapsed_natural_hours'] / 24 and
            intervals[-1]['date_raw'] - data['saved_campaign']['date_raw'] == facts['elapsed_natural_hours'],
            'Contiguous bounded natural duration proof missing')
    prior = data['saved_campaign']['date_raw']
    for row in intervals:
        require(row['date_raw'] == prior + row['elapsed_hours'], 'Intermediate natural date gap')
        prior = row['date_raw']
    require(all(facts[k] is None for k in ('fresh_full_365_cycle', 'exact_expiry_date', 'cold_reload',
            'formal_I3b', 'C3', 'I4_complete')), 'Partial observation was promoted to unsupported credit')
    return {**facts, 'verification_scope': data['scope'] + '; shared normal close still required'}
