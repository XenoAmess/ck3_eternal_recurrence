"""One public fixture case, existing decision tools and finite ROOT GUI reviews.

No SDK construction, input injection, save parser, process or lease ownership.
ROOT confirms decisions/selects actual event options and personal beliefs through
the official GUI. A fixture marker, navigation ACK or tooltip number is no proof
that the actor receives an effective modifier.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from ck3_mod_acceptance_cases import generic_product_adapter as generic
from ck3_mod_acceptance_cases._business import check_evidence, pin, require, write_once


CASE = 'vanilla-faith-feedback'
RESULT = 'lyd-vanilla-feedback-case-result.json'
DECISIONS = {
    'entry': 'lyd_enter_decision',
    'school': 'lyd_change_school_decision',
    'declare': 'lyd_c3_declare_claim_decision',
    'challenger': 'lyd_c3_register_challenger_decision',
    'withdraw': 'lyd_c3_withdraw_claim_decision',
}
TOOLS = ['ck3_take_snapshot', 'ck3_open_ingame_decisions_v1',
         'ck3_query_ingame_decision_item_v1', 'ck3_select_ingame_decision_item_v1']
PHASES = {
    'baseline': (['original_jingxue_daoxue_and_main_rite_preserved', 'no_head_of_faith_observed'],
                 'jingxue'),
    'entry': (['entry_changed_only_self_rite', 'existing_permitted_statuses_preserved',
               'personal_tenet_T01_known_and_permitted'], 'lyd_rite_kongmen'),
    'school': (['school_changed_only_self_rite', 'core_T14_effective_actor_modifier_observed'], 'lyd_rite_zhuxi'),
    'personal': (['T01_actually_selected_in_personal_beliefs', 'personal_T01_effective_actor_modifier_observed',
                  'no_head_of_faith_observed'], 'lyd_rite_zhuxi'),
    'declare': (['no_head_of_faith_observed', 'claim_declared_once_without_native_office'], 'lyd_rite_zhuxi'),
    'challenger': (['no_head_of_faith_observed', 'challenger_disabled_for_missing_head',
                    'sixteen_condition_tooltip_actually_read', 'no_challenger_registration_invoked'], 'lyd_rite_zhuxi'),
    'withdraw': (['self_claim_withdrawn', 'no_native_office_or_title_created'], 'lyd_rite_zhuxi'),
}
BASE_FACTS = ['official_GUI_personally_reviewed', 'same_paused_owner_and_actor',
              'faith_identity_preserved', 'original_rites_not_modified']
MODIFIERS = {
    'school': {'cultural_head_fascination_mult': '0.06', 'monthly_piety_gain_mult': '-0.04'},
    'personal': {'monthly_legitimacy_add': '0.05', 'monthly_income_mult': '-0.02'},
}


def prepare_case(context):
    config = context['case_contract']
    require(context['product'] == 'li-yu-dao' and context['case'] == CASE and
            config['case_id'] == CASE and config['expected_actor_character_id'] == 29829,
            'Feedback case identity changed')
    return generic.prepare_case(context)


def frame_binding(frame):
    actor = frame.get('played_character', {})
    diag = frame.get('diagnostics', {})
    result = {'game_pid': diag.get('bridge_pid'), 'connection_generation': diag.get('connection_generation'),
              'actor_character_id': actor.get('character_id'), 'date_raw': frame.get('date_raw'),
              'revision': frame.get('revision')}
    require(all(type(value) is int and value > 0 for value in result.values()), 'Actual feedback frame identity missing')
    require(result['actor_character_id'] == 29829 and actor.get('alive') is True and frame.get('paused') is True,
            'Feedback needs original living paused Robert 29829')
    return result


def same_owner(before, after):
    require(all(before[key] == after[key] for key in
                ('game_pid', 'connection_generation', 'actor_character_id', 'date_raw')),
            'Feedback phase crossed owner/actor/date')


def decision(client, phase, frame, *, select=True, opened=False):
    """Existing public tool routing only. Selection navigates; ROOT confirms."""
    key = DECISIONS[phase]
    if not opened:
        step_id = 'feedback-' + phase + '-open'
        row = client.execute_plan([{'id': step_id, 'kind': 'tool', 'tool': TOOLS[1],
            'args': {'expected_revision': frame_binding(frame)['revision']}, 'fresh_revision': False}], step_id)[0]
        require(row.get('ok') is True, 'Original decision open failed; never replay')
        frame = client.snapshot()
    step_id = 'feedback-' + phase + '-query'
    row = client.execute_plan([{'id': step_id, 'kind': 'tool', 'tool': TOOLS[2],
        'args': {'decision_key': key, 'expected_revision': frame_binding(frame)['revision']},
        'fresh_revision': False}], step_id)[0]
    model = row.get('result')
    require(row.get('ok') is True and isinstance(model, dict) and
            model.get('schema') == 'ck3-ingame-decision-item-v1' and model.get('read_only') is True and
            model.get('available') is True and
            model.get('decision_key') == key, 'Actual decision unavailable/wrong target; no fallback action')
    expected = {'game_pid': frame['diagnostics']['bridge_pid'],
                'connection_generation': frame['diagnostics']['connection_generation'],
                'played_character_id': frame['played_character']['character_id'],
                'date_raw': frame['date_raw'], 'native_revision': frame['native_revision']}
    require(all(type(model.get(k)) is int and model[k] == v for k, v in expected.items()) and
            all(model.get(k) is True for k in ('owner_thread_verified', 'frame_verified',
                'source_abi_pins_verified', 'gui_owner_binding_verified', 'decisions_tree_complete',
                'decisions_root_visible', 'row_owner_verified')), 'Decision query owner/model proof differs')
    # Native query service already enforces its complete typed frame contract.
    # It does not expose IsValid: ROOT must read the actual detail before Confirm.
    if select:
        frame = client.snapshot()
        step_id = 'feedback-' + phase + '-select'
        selected = client.execute_plan([{'id': step_id, 'kind': 'tool', 'tool': TOOLS[3],
            'args': {'decision_key': key, 'expected_revision': frame_binding(frame)['revision']},
            'fresh_revision': False}], step_id)[0]
        value = selected.get('result', {})
        require(selected.get('ok') is True and value.get('schema') == 'ck3-ingame-decision-item-action-v1' and
                value.get('decision_key') == key and
                value.get('action') == 'select' and value.get('status') in
                {'observed_postcondition', 'acknowledged_verification_pending', 'verified_selected_detail'},
                'Decision navigation not acknowledged; never replay')
    return client.snapshot(require_event_free=False), row


def modifier_qualified(phase, response):
    expected = MODIFIERS.get(phase)
    if expected is None:
        return True
    observed = response.get('effective_modifier_contributions')
    if not isinstance(observed, dict) or set(observed) != set(expected):
        return False
    source = 'lyd_tenet_investigate_principle' if phase == 'school' else 'lyd_tenet_reverent_heaven'
    for key, amount in expected.items():
        row = observed[key]
        if not isinstance(row, dict) or row.get('source_tenet_key') != source or row.get('effective_on_actor') is not True or row.get('evidence_kind') != 'actual_actor_modifier_breakdown':
            return False
        value = row.get('value')
        if not isinstance(value, str):
            return False
        try:
            if not Decimal(value).is_finite() or Decimal(value) != Decimal(amount):
                return False
        except InvalidOperation:
            return False
    return True


def review_phase(context, client, phase, frame, records):
    before = frame_binding(frame)
    requirements, rite = PHASES[phase]
    request = {'schema': 'lyd-vanilla-feedback-root-checkpoint-v1', 'phase': phase,
        'requirements': BASE_FACTS + requirements, 'before_native_binding': before,
        'expected_actor': 29829, 'expected_faith_key': 'confucian_faith', 'expected_rite_key': rite,
        'expected_effective_contributions': MODIFIERS.get(phase),
        'actions': 'Official GUI only: confirm the exact selected decision once and resolve actual shown enabled event options, or inspect/select personal beliefs. Challenger is inspect-only; never invoke its disabled action.',
        'effect_evidence': 'Actual actor modifier contribution with source attribution; tenet description, fixture flag and ACK are insufficient. Unobservable values must be null/false and remain RED.',
        'same_frame_GUI_qualification': False, 'no_automatic_retry': True,
        'personal_tenet_mutation_typed_capability': 'ABSENT; use ROOT official Personal Beliefs GUI',
        'no_HoF_before_declare_required': True, 'business_pass_inferred': False}
    response = client.root_checkpoint('feedback-' + phase, request)
    write_once(Path(context['output']) / ('feedback-' + phase + '-review-preserved.json'), response)
    require(response.get('run_id') == context['run_id'] and response.get('reviewer') == client.operator_reviewer and
            response.get('status') == 'complete', 'ROOT review pending/wrong scene')
    facts = response.get('facts', {})
    require(isinstance(facts, dict) and all(type(facts.get(key)) is bool for key in BASE_FACTS + requirements),
            'Every review fact needs explicit true/false; UNKNOWN is not PASS')
    require(all(facts[key] is True for key in BASE_FACTS), 'Feedback identity/faith preservation not proven')
    require(response.get('before_native_binding') == before and
            response.get('actor_character_id') == 29829 and response.get('faith_key') == 'confucian_faith' and
            response.get('rite_key') == rite, 'GUI review crossed actual before owner or expected faith/rite')
    evidence = response.get('evidence')
    require(isinstance(evidence, list) and evidence, 'Actual original GUI evidence required')
    for item in evidence:
        check_evidence(item)
    after_frame = client.snapshot()
    after = frame_binding(after_frame)
    same_owner(before, after)
    qualified = all(facts[key] is True for key in requirements) and modifier_qualified(phase, response)
    record = {'phase': phase, 'before_native_binding': before, 'after_native_binding': after,
              'GUI_same_frame_qualified': False, 'review': response, 'qualified': qualified}
    records.append(record)
    write_once(Path(context['output']) / ('feedback-' + phase + '-observation.json'), record)
    # Hard prerequisites protect later mutation even when effect observations fail.
    if phase in {'baseline', 'personal', 'declare', 'challenger'}:
        require(facts['no_head_of_faith_observed'] is True, 'Actual no-HoF prerequisite not proven')
    if phase == 'declare':
        require(facts['claim_declared_once_without_native_office'] is True, 'Cannot inspect/withdraw an unverified claim')
    return after_frame


def run_case(context, client):
    compiled, contract_pin = generic.compiled_contract(context)
    require(compiled['config']['case_id'] == CASE, 'Wrong prepared feedback contract')
    records = []
    result = {'schema': 'lyd-vanilla-feedback-case-result-v1', 'product': 'li-yu-dao', 'case': CASE,
              'run_id': context['run_id'], 'assertion_contract': contract_pin,
              'observations': records, 'runtime_status': 'RUNNING', 'case_contract_qualified': False,
              'gui_contract_qualified': False, 'business_pass': False, 'whole_product_release_pass': False,
              'formal_B4_B5_C3_credit': False, 'fixture_marker_is_effect_proof': False}
    try:
        frame = client.snapshot(require_event_free=False)
        frame_binding(frame)
        # The first checkpoint may consume actual ordinary welcome events through
        # ROOT GUI. No event index/definition or same-frame GUI proof is invented.
        frame = review_phase(context, client, 'baseline', frame, records)
        for phase in ('entry', 'school'):
            frame, _ = decision(client, phase, frame)
            frame = review_phase(context, client, phase, frame, records)
        frame = review_phase(context, client, 'personal', frame, records)
        frame, _ = decision(client, 'declare', frame)
        frame = review_phase(context, client, 'declare', frame, records)
        frame, _ = decision(client, 'challenger', frame, select=True)
        frame = review_phase(context, client, 'challenger', frame, records)
        frame, _ = decision(client, 'withdraw', frame, opened=True)
        frame = review_phase(context, client, 'withdraw', frame, records)
        qualified = len(records) == len(PHASES) and all(row['qualified'] for row in records)
        result.update(runtime_status='REPRESENTATIVE_OBSERVED' if qualified else 'REPRESENTATIVE_RED',
                      case_contract_qualified=qualified, gui_contract_qualified=qualified)
    except BaseException as error:
        result.update(runtime_status='RED', error=type(error).__name__ + ': ' + str(error))
        write_once(Path(context['output']) / RESULT, result)
        raise
    write_once(Path(context['output']) / RESULT, result)
    return result


def verify_case(context):
    compiled, current = generic.compiled_contract(context)
    result = generic.read_json(Path(context['output']) / RESULT)
    require(result.get('run_id') == context['run_id'] and result.get('case') == CASE and
            result.get('assertion_contract') == current, 'Feedback result/contract binding changed')
    observations = result.get('observations', [])
    require([row.get('phase') for row in observations] == list(PHASES), 'Incomplete feedback phases')
    for row in observations:
        same_owner(row['before_native_binding'], row['after_native_binding'])
        for evidence in row['review']['evidence']:
            check_evidence(evidence)
        require(row['qualified'] is True, 'Actual representative failed: ' + row['phase'])
    return {'case_contract_qualified': True, 'gui_contract_qualified': True,
            'business_pass': False, 'whole_product_release_pass': False,
            'scope': 'representative feedback only; normal close independently required',
            'evidence': [pin(Path(context['output']) / RESULT), current]}
