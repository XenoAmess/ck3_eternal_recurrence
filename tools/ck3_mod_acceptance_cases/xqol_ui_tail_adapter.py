"""Original Song readonly9/UI25 in a fresh scene, with explicit prior-core evidence."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

from ck3_mod_acceptance_prepare import invoke_fixture_prepare, materialize_fixture_profile, pin, write_json
from . import xqol_adapter as original
from .xqol_scope import parse_song_scope
from .xqol_ui import Controller, STAGES

MARKERS = {
    'begin': 'ZQAUITAIL: SCOPE BEGIN actual_song_actor',
    'pass': 'ZQAUITAIL: SCOPE PASS actual_song_actor',
    'end': 'ZQAUITAIL: SCOPE END actual_song_actor',
    'fail': 'ZQAUITAIL: TEST FAIL actual_song_actor',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def checked_json(row):
    require(pin(row['path']) == row, 'Pinned prior source evidence changed')
    return read(row['path'])



def prior_formal_binding(context, receipt, source_formal):
    expected = context['case_inputs']['formal_product_files']
    fields = ('bytes', 'sha256')
    require(set(source_formal) == set(expected) == set(receipt['formal_product_files']) and len(expected) == 27 and
            all(all(source_formal[key][field] == receipt['formal_product_files'][key][field]
                    for field in fields) for key in expected), 'Prior actual core formal27 source pins changed')
    changed = [key for key in sorted(expected)
               if any(source_formal[key][field] != expected[key][field] for field in fields)]
    if not changed:
        return {'mode': 'exact_formal27'}
    generated_relative = 'common/character_interactions/xqol_generated_release_interactions.txt'
    dispatch_relative = 'common/scripted_effects/xqol_conversion_effects.txt'
    if changed == [generated_relative, dispatch_relative]:
        old_pins = {generated_relative: {'bytes': 14134, 'sha256': '456dbf029c115393dd04b83707802f029799ec5021a66b76959d8e3460573f0a'},
                    dispatch_relative: {'bytes': 7458, 'sha256': '0a4f93d7019afe94cfff76f7f6129023dc08b07c96dcf61ea170a5e5c40ec7db'}}
        new_pins = {generated_relative: {'bytes': 14943, 'sha256': '9992b5c91f2f482eb2165d33c9066978c2ca3757a281f8d0f4e99096a168bb73'},
                    dispatch_relative: {'bytes': 8127, 'sha256': '608c7e6811b7444274947c82ba63439cabd4887e61bcb978bf196d738fe72d5f'}}
        # This fixed two-file transform retains only R33 defense23/reverse/final6.
        # It grants no conversion, UI, source-case or normal-close result.
        require(context['case_inputs']['prior_core_evidence']['sha256'] ==
                '3be254579a2a5004b6dbb15c48e5ec619f784503f2b75fe854e936bd0547dbe1' and
                receipt['source_prepared']['sha256'] ==
                '28e7bfca6b7165a749a4311c7182387d9a368ad8b1067175dcb9d600f6b1dfd5' and
                receipt['source_run_id'] == '4-8e1c2f1861--xenoamess-quality-of-life--R0033' and
                all(all(source_formal[relative][field] == old_pins[relative][field] and
                        expected[relative][field] == new_pins[relative][field]
                        for field in fields) for relative in changed),
                'Only the fixed R33 stock-admission and pending-condition source equivalence is allowed')
        current = {}
        for relative in changed:
            path = Path(context['case_inputs']['product_dir']) / relative
            current[relative] = pin(path)
            require(all(current[relative][field] == new_pins[relative][field] for field in fields),
                    'Actual two-file conversion bytes must equal the fixed reviewed pins')
            raw = path.read_bytes()
            if relative == dispatch_relative:
                require(raw.count(b'\t\t\t\t# Full stock admission is checked before creating a pending reply.\n\t\t\t\tis_character_interaction_valid = {\n\t\t\t\t\trecipient = scope:xqol_conversion_candidate\n\t\t\t\t\tinteraction = ask_for_conversion_courtier_interaction\n\t\t\t\t}\n') == 1, 'Fixed stock admission guard count changed')
                raw = raw.replace(b'\t\t\t\t# Full stock admission is checked before creating a pending reply.\n\t\t\t\tis_character_interaction_valid = {\n\t\t\t\t\trecipient = scope:xqol_conversion_candidate\n\t\t\t\t\tinteraction = ask_for_conversion_courtier_interaction\n\t\t\t\t}\n', b'')
                require(raw.count(b'\t\t\t\t# Full stock admission is checked before creating a pending reply.\n\t\t\t\tis_character_interaction_valid = {\n\t\t\t\t\trecipient = scope:xqol_conversion_candidate\n\t\t\t\t\tinteraction = demand_conversion_vassal_ruler_interaction\n\t\t\t\t}\n') == 2, 'Fixed stock admission guard count changed')
                raw = raw.replace(b'\t\t\t\t# Full stock admission is checked before creating a pending reply.\n\t\t\t\tis_character_interaction_valid = {\n\t\t\t\t\trecipient = scope:xqol_conversion_candidate\n\t\t\t\t\tinteraction = demand_conversion_vassal_ruler_interaction\n\t\t\t\t}\n', b'')
                require(raw.count(b'send_threshold = decline') == 3, 'Fixed conversion send count changed')
                raw = raw.replace(b'send_threshold = decline', b'execute_threshold = decline')
            else:
                require(raw.count(b'\tis_valid = {\n\t\tscope:actor = { xqol_human_ruler_trigger = yes }\n\t\tscope:actor.faith != scope:recipient.faith\n\t\tscope:recipient = { is_courtier_of = scope:actor }\n\t\tscope:recipient = { is_ruler = no }\n\t\tscope:recipient = { is_imprisoned = no }\n\t\ttrigger_if = {\n\t\t\tlimit = { is_ai = yes }\n\t\t\tis_adult = yes\n\t\t}\n\t\tvalid_demand_conversion_conditions_trigger = yes\n\t}') == 1, 'Fixed private ongoing condition block changed')
                raw = raw.replace(b'\tis_valid = {\n\t\tscope:actor = { xqol_human_ruler_trigger = yes }\n\t\tscope:actor.faith != scope:recipient.faith\n\t\tscope:recipient = { is_courtier_of = scope:actor }\n\t\tscope:recipient = { is_ruler = no }\n\t\tscope:recipient = { is_imprisoned = no }\n\t\ttrigger_if = {\n\t\t\tlimit = { is_ai = yes }\n\t\t\tis_adult = yes\n\t\t}\n\t\tvalid_demand_conversion_conditions_trigger = yes\n\t}', b'\tis_valid = {\n\t\tscope:actor = { xqol_human_ruler_trigger = yes }\n\t\tscope:actor = {\n\t\t\tis_character_interaction_valid = {\n\t\t\t\trecipient = scope:recipient\n\t\t\t\tinteraction = ask_for_conversion_courtier_interaction\n\t\t\t}\n\t\t}\n\t}', 1)
                require(raw.count(b'\tis_valid = {\n\t\tscope:actor = { xqol_human_ruler_trigger = yes }\n\t\tscope:puppet_or_actor ?= {\n\t\t\tNOT = { faith = scope:recipient.faith }\n\t\t}\n\t\tscope:recipient = {\n\t\t\tOR = {\n\t\t\t\ttarget_is_liege_or_above = scope:puppet_or_actor\n\t\t\t\tis_tributary_of = scope:puppet_or_actor\n\t\t\t}\n\t\t\tis_ai = yes\n\t\t\tis_ruler = yes\n\t\t}\n\t\ttrigger_if = {\n\t\t\tlimit = { is_ai = yes }\n\t\t\tis_adult = yes\n\t\t}\n\t\tvalid_demand_conversion_conditions_trigger = yes\n\t\ttrigger_if = {\n\t\t\tlimit = { scope:is_puppet_action ?= yes }\n\t\t\tscope:puppet_or_actor = {\n\t\t\t\tinfluence >= demand_conversion_influence_cost_value\n\t\t\t}\n\t\t}\n\t\ttrigger_if = {\n\t\t\tlimit = {\n\t\t\t\tscope:puppet_or_actor.domicile ?= {\n\t\t\t\t\tdomicile_uses_culture_and_faith = yes\n\t\t\t\t}\n\t\t\t\tscope:recipient = {\n\t\t\t\t\tis_ruler = yes\n\t\t\t\t\tgovernment_has_flag = government_is_in_steppe\n\t\t\t\t}\n\t\t\t}\n\t\t\tcustom_tooltip = {\n\t\t\t\ttext = nomads_must_inspire_tt\n\t\t\t\talways = no\n\t\t\t}\n\t\t}\n\t}') == 1, 'Fixed private ongoing condition block changed')
                raw = raw.replace(b'\tis_valid = {\n\t\tscope:actor = { xqol_human_ruler_trigger = yes }\n\t\tscope:puppet_or_actor ?= {\n\t\t\tNOT = { faith = scope:recipient.faith }\n\t\t}\n\t\tscope:recipient = {\n\t\t\tOR = {\n\t\t\t\ttarget_is_liege_or_above = scope:puppet_or_actor\n\t\t\t\tis_tributary_of = scope:puppet_or_actor\n\t\t\t}\n\t\t\tis_ai = yes\n\t\t\tis_ruler = yes\n\t\t}\n\t\ttrigger_if = {\n\t\t\tlimit = { is_ai = yes }\n\t\t\tis_adult = yes\n\t\t}\n\t\tvalid_demand_conversion_conditions_trigger = yes\n\t\ttrigger_if = {\n\t\t\tlimit = { scope:is_puppet_action ?= yes }\n\t\t\tscope:puppet_or_actor = {\n\t\t\t\tinfluence >= demand_conversion_influence_cost_value\n\t\t\t}\n\t\t}\n\t\ttrigger_if = {\n\t\t\tlimit = {\n\t\t\t\tscope:puppet_or_actor.domicile ?= {\n\t\t\t\t\tdomicile_uses_culture_and_faith = yes\n\t\t\t\t}\n\t\t\t\tscope:recipient = {\n\t\t\t\t\tis_ruler = yes\n\t\t\t\t\tgovernment_has_flag = government_is_in_steppe\n\t\t\t\t}\n\t\t\t}\n\t\t\tcustom_tooltip = {\n\t\t\t\ttext = nomads_must_inspire_tt\n\t\t\t\talways = no\n\t\t\t}\n\t\t}\n\t}', b'\tis_valid = {\n\t\tscope:actor = { xqol_human_ruler_trigger = yes }\n\t\tscope:actor = {\n\t\t\tis_character_interaction_valid = {\n\t\t\t\trecipient = scope:recipient\n\t\t\t\tinteraction = demand_conversion_vassal_ruler_interaction\n\t\t\t}\n\t\t}\n\t}', 1)
            require(len(raw) == old_pins[relative]['bytes'] and
                    hashlib.sha256(raw).hexdigest() == old_pins[relative]['sha256'],
                    'Fixed conversion transforms must restore the complete original R33 source bytes')
        return {'mode': 'r33_scoped_conversion_stock_pending_only', 'changed_files': changed,
                'source_pins': old_pins, 'current_pins': current, 'restored_source_pins': old_pins,
                'unchanged_formal_files': 25, 'reused_scope': 'defense23/reverse/final6 only',
                'conversion_reply_credit': False}
    relative = 'common/scripted_effects/xqol_conversion_effects.txt'
    old = {'bytes': 7458, 'sha256': '0a4f93d7019afe94cfff76f7f6129023dc08b07c96dcf61ea170a5e5c40ec7db'}
    new = {'bytes': 7449, 'sha256': '438a44f036d3545a48d0619a526073db3829c19a6c93fab2bece19ab2bc385be'}
    # This one equivalence preserves only R33 defense23/reverse/final6, whose
    # frozen source does not call the three conversion dispatchers. No AI
    # conversion, UI, source-case PASS or normal-close proof is inherited.
    require(changed == [relative] and
            context['case_inputs']['prior_core_evidence']['sha256'] ==
            '3be254579a2a5004b6dbb15c48e5ec619f784503f2b75fe854e936bd0547dbe1' and
            receipt['source_prepared']['sha256'] ==
            '28e7bfca6b7165a749a4311c7182387d9a368ad8b1067175dcb9d600f6b1dfd5' and
            receipt['source_run_id'] == '4-8e1c2f1861--xenoamess-quality-of-life--R0033' and
            all(source_formal[relative][field] == old[field] and expected[relative][field] == new[field]
                for field in fields), 'Only the fixed R33 conversion send-threshold source equivalence is allowed')
    path = Path(context['case_inputs']['product_dir'])/relative
    raw = path.read_bytes()
    restored = raw.replace(b'send_threshold = decline', b'execute_threshold = decline')
    require(len(raw) == new['bytes'] and hashlib.sha256(raw).hexdigest() == new['sha256'] and
            raw.count(b'send_threshold = decline') == 3 and len(restored) == old['bytes'] and
            hashlib.sha256(restored).hexdigest() == old['sha256'],
            'Actual conversion source must reverse exactly three send thresholds to the original R33 bytes')
    return {'mode': 'r33_scoped_conversion_send_only', 'changed_file': relative,
            'source_pin': old, 'current_pin': pin(path), 'restored_source_pin': old,
            'unchanged_formal_files': 26, 'reused_scope': 'defense23/reverse/final6 only',
            'conversion_reply_credit': False}

def prior_core(context):
    evidence = context['case_inputs']['prior_core_evidence']
    receipt = checked_json(evidence)
    require(receipt.get('schema') == 'ck3-xqol-prior-core-partial-evidence-v1' and
            receipt.get('source_case') == 'defense_and_ui' and receipt.get('source_run_id') and
            receipt.get('source_case_acceptance_pass') is False and
            receipt.get('normal_close_qualified') is False,
            'Prior partial core must retain its actual incomplete source-case result')
    prepared = checked_json(receipt['source_prepared'])
    source_formal = {key.removeprefix('mod-content/product/'): value
                    for key, value in prepared['preparation']['profile']['files'].items()
                    if key.startswith('mod-content/product/')}
    formal_binding = prior_formal_binding(context, receipt, source_formal)
    source = receipt['source_rows']
    day = checked_json(source['actual-day-005.json'])
    final = checked_json(source['actual-original-final6-results.json'])
    failure = checked_json(source['case-error-preserved.json'])
    close = checked_json(source['normal-close-result.json'])
    contract = read(Path(__file__).with_name('xqol_defense_and_ui.json'))
    require(day['proven_days'] == final['proven_days'] == receipt['proven_days'] == 5 and
            set(day['counts']['required']) == set(contract['required_markers']) and
            set(day['counts']['forbidden']) == set(contract['forbidden_markers']) and
            all(type(v) is int and v == 1 for v in day['counts']['required'].values()) and
            all(type(v) is int and v == 0 for v in day['counts']['forbidden'].values()) and
            receipt['counts'] == day['counts'], 'Original prior core23/F5/five-day facts changed')
    require(final.get('original23_verified') is True and final.get('product_pass') is False and
            len(final['rows']) == 6 and all(row.get('ok') is True and not row.get('error') and
            row.get('finished_at') for row in final['rows']), 'Original prior final6 is incomplete')
    require(failure.get('run_id') == receipt['source_run_id'] and failure.get('business_pass') is False and
            close.get('normal_close_qualified') is False,
            'Original failed case/normal-close facts must not be rewritten')
    return {'receipt': evidence, 'source_run_id': receipt['source_run_id'],
            'formal_source_binding': formal_binding,
            'final6': source['actual-original-final6-results.json'],
            'core23': True, 'forbidden5': True, 'natural_days': 5, 'final6_qualified': True,
            'source_case_acceptance_pass': False, 'source_normal_close_qualified': False}


def scope(raw):
    proof = parse_song_scope(raw, {'scope_name': 'xqol_startup_actor', 'markers': MARKERS})
    require(proof is not None, 'Actual original Song scope proof missing')
    return proof


def validate_contract(context):
    contract = context['case_contract']
    require(contract['acceptance_scope'] == 'original_song_ui_tail' and
            contract['readonly_step_count'] == 9 and contract['gui25_order'] == STAGES and
            contract['guards_independent_supplement_required'] is True,
            'Original readonly9/UI25 and independent guard boundary changed')
    require(context['case_spec']['budgets'] == {'command_timeout': 300, 'readiness_timeout': 400,
            'timeout': 3000, 'poll_interval': 0.05, 'hold_seconds': 1800}, 'Original QOL wall-clock bounds changed')


def prepare_case(context):
    validate_contract(context)
    prior = prior_core(context)
    output = Path(context['output']); fixture = output/'song-ui-only-fixture'
    emitter = Path(context['repo_root'])/'tools/prepare_xqol_ui_fixture.py'
    emitted = invoke_fixture_prepare(context, emitter, ['--repo', context['repo_root'], '--output', fixture])
    profile = materialize_fixture_profile(context, fixture, context['case_inputs']['product_dir'],
                                          context['case_inputs']['plain_configuration'])
    actual = {key.removeprefix('mod-content/product/'): row for key, row in profile['files'].items()
              if key.startswith('mod-content/product/')}
    expected = context['case_inputs']['formal_product_files']
    require(len(actual) == len(expected) == 27 and set(actual) == set(expected) and
            all(all(actual[key][field] == expected[key][field] for field in ('bytes', 'sha256')) for key in expected),
            'Existing exact formal27 product required; no release builder is used')
    hook = output/'frontend-fixture-startup-case-contract.json'
    handler = pin(Path(__file__)); handler['function'] = 'admit_startup_event'
    dependencies = [pin(path) for path in (
        Path(__file__).with_name('xqol_scope.py'), Path(__file__).with_name('xqol_adapter.py'),
        Path(__file__).with_name('xqol_ui.py'), Path(__file__).with_name('xqol_original_plans.json'),
        Path(__file__).with_name('xqol_defense_and_ui.json'),
        Path(__file__).parent.parent/'ck3_mod_acceptance_prepare.py', Path(__file__).with_name('__init__.py'))]
    write_json(hook, {'schema': 'ck3-frontend-fixture-startup-case-contract-v1', 'state_dir': context['state_dir'],
                      'handler': handler, 'dependencies': dependencies})
    initial = output/'initial-plan.json'; write_json(initial, {'steps': []})
    return {'startup': {'mode': 'fixture', 'state_dir': profile['state_dir'],
                        'fixture_start_policy': profile['fixture_start_policy'], 'startup_case_contract': pin(hook)},
            'initial_plan': pin(initial), 'profile': profile, 'emitter': emitted, 'prior_core': prior,
            'formal_product_unchanged': True, 'coverage': 'original_song_readonly9_ui25_only',
            'runtime_status': 'NOT_RUN', 'business_pass': False}


def admit_startup_event(context, snapshot, event_context):
    """Pure scope-bound first intro proof; the existing shared host owns selection."""
    log_path = (Path(context['state_dir']) / 'profile/logs/debug.log').resolve()
    raw = log_path.read_bytes()
    proof = scope(raw)
    played = snapshot.get('played_character', {})
    require(played.get('character_id') == proof['runtime_character_id'] and played.get('alive') is True and
            played.get('source') == 'native', 'Intro is not bound to the actual original Song scope')
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
    require(isinstance(typed_options, list) and len(typed_options) == 1 and all(typed_options[0].get(key) == value for
            key, value in {'rendered_index': 0, 'native_option_index': 0, 'shown': True,
                          'enabled': True, 'fallback': False, 'cancel': False}.items()),
            'Actual typed intro sole option is not enabled native index0')
    # The original parser/run_case retain full raw hex; startup carries its exact byte reference.
    proof = {key: value for key, value in proof.items() if key != 'raw_scope_block_hex'}
    proof['markers'] = {key: {'literal': marker, 'count': raw.count(marker.encode('ascii'))}
                        for key, marker in MARKERS.items()}
    proof['raw_scope_block_reference'] = {
        'path': str(log_path), 'byte_start': proof['byte_start'], 'byte_end': proof['byte_end'],
        'bytes': proof['byte_end'] - proof['byte_start'], 'sha256': proof['raw_scope_block_sha256']}
    return {'event_instance_id': event['instance_id'], 'option_number': 1, 'proof': proof, 'business_pass': False}


def readonly9(context):
    """Only rebind the three obsolete defense anchors to this real Song frame."""
    steps = copy.deepcopy(original.plans(context)['readonly9']['steps'])
    prefixes = tuple('results.'+name+'.' for name in
                     ('qol-defense-initial-map', 'qol-defense-song-ui-map', 'qol-defense-final-map'))
    changed = []
    def visit(value):
        if isinstance(value, dict):
            if set(value) == {'$ref'} and isinstance(value['$ref'], str):
                for prefix in prefixes:
                    if value['$ref'].startswith(prefix):
                        old = value['$ref']; new = 'results.qolu-ui-anchor.'+old[len(prefix):]
                        changed.append({'from': old, 'to': new}); return {'$ref': new}
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, list): return [visit(item) for item in value]
        return value
    steps = visit(steps)
    require(len(steps) == 9 and changed, 'Original readonly9 anchor contract changed')
    return steps, changed


def run_case(context, client):
    validate_contract(context); prior = prior_core(context)
    proof = scope(client.log_bytes())
    rows = client.execute_plan([{'id': 'qolu-ui-anchor', 'tool': 'ck3_take_snapshot',
        'args': {'include_native_command_history': False}, 'fresh_revision': True}], 'qolu-ui-anchor')
    anchor = client.validate_frame(rows[0]['result'])
    require(anchor['played_character']['character_id'] == proof['runtime_character_id'], 'Actual Song scope/native actor mismatch')
    root_row = client.execute_plan([{'id': 'qolu-actual-song-root', 'tool': 'ck3_query_campaign_root_context_v1',
                                   'fresh_revision': True}], 'qolu-actual-song-root')[0]
    current = client.validate_frame(root_row['after_snapshot'])
    require(original.projection(current) == original.projection(anchor), 'Actual Song root changed owner/actor/date')
    holders = []
    for ordinal, title_id in enumerate(original.owned_hegemony_ids(root_row['result'], current, proof['runtime_character_id']), 1):
        phase = 'qolu-actual-owned-hegemony-'+str(ordinal)
        row = client.execute_plan([{'id': phase, 'tool': 'ck3_query_title_holder_v1',
            'args': {'title_id': title_id}, 'fresh_revision': True}], phase)[0]
        current = client.validate_frame(row['after_snapshot'])
        require(original.projection(current) == original.projection(anchor), 'Actual title holder readback changed owner/actor/date')
        holders.append(row)
        if row['result'].get('title_holder', {}).get('title_key') == 'h_china': break
    title_proof = original.prove_original_song_holding(root_row['result'], [row['result'] for row in holders],
                                                      current, proof['runtime_character_id'])
    client.checkpoint('actual-original-song-h-china-title-proof', {'proof': title_proof,
        'campaign_root_row': root_row, 'title_holder_rows': holders})
    steps, rebindings = readonly9(context)
    readonly = client.execute_plan(steps, 'qolu-original-song-readonly9')
    require(len(readonly) == 9 and readonly[0].get('ok') is True and readonly[-1].get('ok') is True,
            'Original readonly9 endpoints failed')
    before = client.validate_frame(readonly[0]['result']); after = client.validate_frame(readonly[-1]['result'])
    require(original.projection(before) == original.projection(after) == original.projection(anchor),
            'Original readonly9 changed actual Song owner/actor/date')
    client.checkpoint('actual-original-readonly9-results', {'rows': readonly, 'anchor_rebindings': rebindings,
        'optional_query_gaps': [row['id'] for row in readonly if not row.get('ok')], 'product_pass': False})
    client.checkpoint('root-same-live-required-ui-awaiting', {'run_id': client.frozen['run_id'], 'reviewer': '/root',
        **client._process, 'original_hold_deadline': client._hold, 'scope_proof': {'song': proof},
        'original_gui25_required': True, 'prior_core_external_reference': prior,
        'no_current_defense_or_final6_execution': True})
    ui = Controller(context, client, prior_final6=prior['final6']).run()
    result = {'case_contract_qualified': True, 'gui_contract_qualified': ui['gui_contract_qualified'],
        'actual_song_scope': proof, 'title_proof': title_proof, 'original_readonly9': True, 'gui25': ui,
        'prior_core': prior, 'new_scene_does_not_replay_core': True,
        'guards_independent_supplement_required': True, 'business_contract_applicable': False, 'business_pass': False,
        'source_R33_case_remains_incomplete': True, 'normal_close_still_required': True}
    client.checkpoint('qol-ui-tail-result', result)
    return result


def verify_case(context):
    validate_contract(context); prior = prior_core(context)
    path = Path(context['output'])/'qol-ui-tail-result.json'
    if not path.is_file():
        return {'case_contract_qualified': False, 'gui_contract_qualified': False, 'business_pass': False, 'status': 'NOT_RUN'}
    result = read(path)
    require(result['prior_core'] == prior and result.get('original_readonly9') is True and
            result.get('new_scene_does_not_replay_core') is True and result.get('source_R33_case_remains_incomplete') is True,
            'Explicit prior-core/fresh UI scene boundary changed')
    return {**result, 'business_pass': False, 'product_release_pass': False,
            'aggregation_scope': 'Prior partial core plus fresh UI tail; original R33 RED retained. Guards require independent actual supplement.'}
