"""Public LYD 0.1.2 representatives, using the selected CaseClient only.

The existing fixture changes the selected human's rite to original jingxue.
All enrollment, belief choices, practices and mandates use production UI/tools.
ROOT reviews unsupported wallet/modifier/SAVE fields; ACKs never prove effects.
"""
from __future__ import annotations

from pathlib import Path
import math
import time

from ck3_mod_acceptance_cases import generic_product_adapter as generic
from ck3_mod_acceptance_cases import lyd_i3b_formal_adapter as formal
from ck3_mod_acceptance_cases._business import check_evidence, pin, require, write_once

CASE = 'release012-keypaths'
RESULT = 'lyd-release012-keypaths-result.json'
RELIGION = 'ck3_query_player_religion_context_v1'
PERSONAL = 'ck3_query_player_religion_personal_parameters_v1'
TITLE = 'ck3_query_confucian_religious_title_v1'
CACHE = 'ck3_query_actor_cached_succession_v1'
EVENT = 'ck3_query_current_event_window_context_v1'
PROPERTIES = ('destroy_if_invalid_heir', 'no_automatic_claims',
              'definitive_form', 'always_follows_primary_heir')
NAVIGATION_DECISIONS = frozenset((
    'lyd_change_school_decision', 'lyd_play_quiet_self_attainment_decision',
    'lyd_play_sage_transmission_decision'))
NOMINATION_INTERACTION = 'lyd_i3b_nominate_interaction'


def prepare_case(context):
    data = context['case_contract']
    require(context['product'] == data['product'] == 'li-yu-dao' and
            context['case'] == data['case_id'] == CASE, 'Wrong product case')
    require(data['maximum_natural_days'] == 0 and
            data['expected_actor_character_id'] is None, 'Runtime binds its actual selected actor')
    return generic.prepare_case(context)


def binding(frame):
    actor, diag = frame.get('played_character', {}), frame.get('diagnostics', {})
    value = {key: value for key, value in (
        ('game_pid', diag.get('bridge_pid')), ('generation', diag.get('connection_generation')),
        ('actor', actor.get('character_id')), ('date_raw', frame.get('date_raw')),
        ('revision', frame.get('revision')), ('native_revision', frame.get('native_revision')))}
    require(all(type(v) is int and v > 0 for v in value.values()) and
            frame.get('paused') is True and actor.get('alive') is True,
            'Actual living paused selected-player identity missing')
    return value


def same_scene(initial, frame):
    actual = binding(frame)
    require(all(actual[key] == initial[key] for key in ('game_pid', 'generation', 'actor', 'date_raw')),
            'Keypath crossed original owner, actor or paused calendar')
    require(actual['revision'] >= initial['revision'] and
            actual['native_revision'] >= initial['native_revision'], 'Frame revision moved backwards')
    return actual


def call(client, initial, name, tool, arguments=None):
    frame = client.snapshot(require_event_free=False)
    same_scene(initial, frame)
    args = dict(arguments or {}, expected_revision=frame['revision'])
    rows = client.execute_plan([{'id': name, 'tool': tool, 'args': args,
                                'fresh_revision': False}], name)
    require(len(rows) == 1 and rows[0].get('id') == name and rows[0].get('ok') is True and
            not rows[0].get('error'), 'Original public call failed; never replay: ' + name)
    after = client.validate_frame(rows[0]['after_snapshot'], require_event_free=False)
    same_scene(initial, after)
    return frame, rows[0]


def religion(client, initial, name, *, personal=False):
    frame, row = call(client, initial, name, PERSONAL if personal else RELIGION)
    value = row['result']
    require(value.get('available') is True and value.get('read_only') is True and
            value.get('played_character_id') == initial['actor'] and
            value.get('date_raw') == initial['date_raw'] and
            value.get('snapshot_revision') == frame['native_revision'],
            'Actual religion/personal query lost selected actor/frame')
    if not personal:
        require(value.get('faith_key') == 'confucian_faith', 'Original Confucian faith required')
    return value


def navigate(client, initial, name, decision_key, *, deadline=None):
    def guard_navigation_call():
        if deadline is not None:
            require(deadline - time.time() >= 300 and client.remaining() > 900,
                    'Navigation call needs 300s on the original phase and more than 900s total reserve')

    guard_navigation_call()
    call(client, initial, name + '-open', 'ck3_open_ingame_decisions_v1')
    guard_navigation_call()
    frame, row = call(client, initial, name + '-model', 'ck3_query_ingame_decision_item_v1',
                      {'decision_key': decision_key})
    model = row['result']
    require(model.get('schema') == 'ck3-ingame-decision-item-v1' and
            model.get('read_only') is True and model.get('available') is True and
            model.get('decision_key') == decision_key, 'Exact decision model unavailable')
    expected = {'game_pid': initial['game_pid'], 'connection_generation': initial['generation'],
                'played_character_id': initial['actor'], 'date_raw': initial['date_raw'],
                'native_revision': frame['native_revision']}
    require(all(type(model.get(k)) is int and model[k] == v for k, v in expected.items()) and
            all(model.get(k) is True for k in ('owner_thread_verified', 'frame_verified',
                'source_abi_pins_verified', 'gui_owner_binding_verified', 'decisions_tree_complete',
                'decisions_root_visible', 'row_owner_verified')), 'Decision model owner/frame differs')
    guard_navigation_call()
    _, selected = call(client, initial, name + '-select', 'ck3_select_ingame_decision_item_v1',
                       {'decision_key': decision_key})
    action = selected['result']
    require(action.get('decision_key') == decision_key and action.get('action') == 'select' and
            action.get('status') in {'observed_postcondition', 'acknowledged_verification_pending',
                                     'verified_selected_detail'}, 'Navigation ACK absent; never replay')
    # available and pending selection do not certify the actual Confirm button.
    return row


def current_event(client, initial, name):
    frame = client.snapshot(require_event_free=False)
    same_scene(initial, frame)
    active = frame.get('active_event')
    if active is None:
        return None
    instance = active.get('instance_id')
    require(type(instance) is int and instance > 0, 'Actual event instance missing')
    before, row = call(client, initial, name, EVENT, {'event_instance_id': instance})
    packet, event = row['result'], row['result'].get('current_event_window_context', {})
    require(before.get('active_event', {}).get('instance_id') == instance and
            (row['after_snapshot'].get('active_event') or {}).get('instance_id') == instance and
            packet.get('status') == 'available' and event.get('schema') == 'current-event-window-context-v1' and
            event.get('status') == 'available' and event.get('window_match_count') == 1 and
            event.get('current_event_instance_id') == instance and
            event.get('date_raw') == before['date_raw'] and
            event.get('snapshot_revision') == before['native_revision'] and
            packet.get('queried_revision') == before['revision'] and
            packet.get('queried_native_revision') == before['native_revision'] and
            packet.get('queried_snapshot_id') == before['snapshot_id'], 'Fresh typed event differs')
    require(event.get('root_scope', {}).get('typed_identity', {}).get('character_id') == initial['actor'] and
            all(event.get('readiness', {}).get(k) is True for k in
                ('event_definition_identity_ready', 'root_scope_ready', 'saved_scopes_ready',
                 'option_presentation_ready')), 'Typed player event identity incomplete')
    return {'frame': before, 'event': event, 'row': row}


def option_arguments(packet, choice, allowed, consumed, *, commit_admitted=False):
    event, frame = packet['event'], packet['frame']
    definition, index = choice.get('event_definition_key'), choice.get('native_option_index')
    require(type(index) is int and index >= 0 and definition == event['event_definition_key'] and
            index in allowed.get(definition, []), 'Choice is outside reviewed production phase')
    require(definition != 'lyd.430' or index != 0 or commit_admitted,
            'Factory needs fresh actual precommit protection/quorum review')
    key = (event['current_event_instance_id'], index)
    require(key not in consumed, 'Submitted option cannot be replayed')
    options = [o for o in event.get('options', [])
               if type(o.get('native_option_index')) is int and o['native_option_index'] == index]
    require(len(options) == 1 and options[0].get('shown') is True and options[0].get('enabled') is True,
            'Requested original option is not actually shown/enabled')
    rendered = options[0].get('rendered_index')
    require(type(rendered) is int and rendered >= 0, 'Actual rendered option index missing')
    active = frame.get('active_event') or {}
    require(active.get('instance_id') == key[0], 'Snapshot event instance differs')
    native = active.get('options', [])
    # The public service passes N-1 to the authored native option selector.
    # rendered_index only describes presentation after hidden options are removed.
    number = index + 1
    visible = [o for o in native if type(o.get('index')) is int and o['index'] == index]
    numbered = [o for o in native if o.get('option_number') == number]
    require(len(visible) == len(numbered) == 1 and visible[0] is numbered[0] and
            type(visible[0].get('option_number')) is int and
            visible[0].get('enabled') is True, 'Snapshot/public option mapping differs')
    return {'option_number': number, 'event_instance_id': key[0],
            'expected_revision': frame['revision']}, key


def validate_option_ack(row, args, key):
    result = row.get('result') or {}
    require(row.get('ok') is True and result.get('accepted') is True and
            result.get('event_instance_id') == key[0] and
            type(result.get('option_number')) is int and
            result['option_number'] == args['option_number'] and
            type(result.get('option_index')) is int and result['option_index'] == key[1],
            'Original choice differs from intent; never replay')
    selection = result.get('event_selection')
    if selection is not None:
        require(isinstance(selection, dict), 'Original native selection malformed; never replay')
        if 'selected_native_option_index' in selection:
            selected = selection['selected_native_option_index']
            require(type(selected) is int and selected == key[1],
                    'Original native choice differs from intent; never replay')


def native_head_bundle(client, initial, name):
    frame, cache_row = call(client, initial, name + '-cache', CACHE)
    cache = formal.observe_cache(frame, cache_row['result'])
    frame, title_row = call(client, initial, name + '-title', TITLE)
    title = formal.observe_query(frame, title_row['result'], 'confucian_religious_title')
    frame, assembly_row = call(client, initial, name + '-assembly',
                               'ck3_query_confucian_assembly_predicates_v1')
    assembly = formal.observe_query(frame, assembly_row['result'], 'confucian_assembly_predicates')
    require(assembly.get('predicates_complete') is True,
            'Fresh complete actual Faith/rite/elector predicates required')
    frame, save_row = call(client, initial, name + '-save', 'ck3_save_checkpoint')
    saved = save_row['result']
    require(saved.get('accepted') is True and saved.get('checkpoint', {}).get('status') == 'saved',
            'Original actual SAVE failed')
    return {'cache': cache, 'title': title, 'assembly': assembly, 'save': saved['checkpoint'],
            'SAVE_body_read_by_adapter': False}


def head_qualified(before, after, actor, faith):
    title = after['title']
    return (before['title'].get('legal_head_title_absent') is True and
        before['title'].get('head_title_full_id') is None and
        type(title.get('head_title_full_id')) is int and title['head_title_full_id'] > 0 and
        title.get('legal_head_title_absent') is False and title.get('graph_available') is True and
        title.get('faith_full_id') == faith and title.get('native_title_holder_full_id') == actor and
        title.get('title_properties', {}).get('available') is True and
        all(title.get('title_properties', {}).get(k) is True for k in PROPERTIES) and
        title.get('title_laws', {}).get('available') is True and
        title.get('title_laws', {}).get('temporal_head_of_faith_succession_law_member') is True and
        {'native_definition_id': 95, 'key': 'temporal_head_of_faith_succession_law'} in
            title.get('title_laws', {}).get('complete_laws', []) and before['cache'] == after['cache'])


def other_rite_nominee(roster, recipient_id):
    """Bind one requested recipient to a fresh complete original-Faith roster."""
    require(type(recipient_id) is int and 0 < recipient_id < 2**32 - 1 and
            roster.get('predicates_complete') is True and
            type(roster.get('played_rite_id')) is int and
            type(roster.get('faith_id')) is int, 'Fresh complete Faith roster required')
    candidates = [rite for rite in roster.get('rites', [])
                  if rite.get('dormant') is False and rite.get('rite_id') != roster['played_rite_id'] and
                  isinstance(rite.get('suggested_nominee'), dict) and
                  rite['suggested_nominee'].get('character_id') == recipient_id and
                  rite['suggested_nominee'].get('rite_id') == rite.get('rite_id') and
                  rite['suggested_nominee'].get('faith_id') == roster['faith_id'] and
                  rite['suggested_nominee'].get('is_ai') is True]
    require(len(candidates) == 1, 'Recipient is not the fresh qualified other-rite nominee')
    return candidates[0]['suggested_nominee']


def review_cell(context, client, initial, phase, consumed, before_head=None):
    """Finite ROOT UI/semantic review; unknown Python data stays in original hold."""
    attempts, actions, last_error = 0, 0, None
    commit_event, precommit, factory_submitted, precommit_requested = None, None, False, False
    initial_requested = before_head is not None
    phase_options = set()
    navigation_intents = set()
    nomination_intents, nominated_recipients = set(), set()
    last_nomination = None
    navigation_keys = phase.get('navigation_decision_keys', [])
    navigation_limit = phase.get('maximum_navigation_actions', 0)
    navigation_enabled = (phase['id'] == 'preparation' and type(navigation_keys) is list and
        all(type(key) is str for key in navigation_keys) and
        0 < len(navigation_keys) == len(set(navigation_keys)) <= len(NAVIGATION_DECISIONS) and
        set(navigation_keys) <= NAVIGATION_DECISIONS and type(navigation_limit) is int and
        0 < navigation_limit <= len(navigation_keys))
    # The caller's existing finite phase clock is captured once, never renewed
    # by navigation, observe, a new ROOT response or a pending selection ACK.
    navigation_deadline = getattr(client, 'phase_deadline', None)
    last_navigation = None
    while True:
        attempts += 1
        name = 'release012-' + phase['id'] + '-' + str(attempts).zfill(4)
        frame = client.snapshot(require_event_free=False)
        same_scene(initial, frame)
        packet = None
        try:
            packet = current_event(client, initial, name + '-typed')
        except ValueError as error:
            # A rejected completed read is never reissued under the same ID.
            # ROOT can fix Python/inspect the current scene before a fresh read.
            last_error = str(error)
        response = client.root_checkpoint(name, {
            'schema': 'lyd-release012-root-cell-v1', 'phase': phase['id'],
            'requirements': phase['requirements'], 'instructions': phase['instructions'],
            'actual_start_binding': initial, 'actual_before_binding': binding(frame),
            'actual_typed_event': packet, 'actual_initial_political_bundle': before_head,
            'initial_political_bundle_requested': initial_requested,
            'optional_observations': phase.get('optional_observations', []),
            'actual_precommit_bundle': precommit,
            'last_contract_error': last_error, 'submitted_option_actions': actions,
            'decision_navigation': {'allowed_keys': navigation_keys if navigation_enabled else [],
                'maximum_actions': navigation_limit if navigation_enabled else 0,
                'submitted_actions': len(navigation_intents), 'last_navigation': last_navigation,
                'request_fields': ['decision_key', 'navigation_intent_id'],
                'opens_detail_only_no_Confirm_options_or_qualification': True},
            'other_rite_nomination': {'interaction_key': NOMINATION_INTERACTION,
                'submitted_recipient_ids': sorted(nominated_recipients),
                'last_nomination': last_nomination,
                'request_fields': ['recipient_id', 'nomination_intent_id'],
                'only_fresh_suggested_other_rite_AI_nominee': True,
                'pending_ACK_is_not_acceptance': True},
            'responses': ['complete', 'partial', 'skip', 'abort', 'observe', 'choose_option',
                          'read_precommit', 'admit_commit'] +
                         (['enter_institution'] if phase['id'] == 'institution' else []) +
                         (['nominate_other_rite'] if phase['id'] == 'institution' else []) +
                         (['navigate_decision'] if navigation_enabled else []),
            'choose_option': 'Supply exact current event_definition_key/native_option_index; adapter freshly re-queries and maps authored native index to public number. No guessed tuple or replay.',
            'unavailable_native_fields': 'Wallets, effective modifiers, complete saved political AST/heirs/laws require actual original GUI/new SAVE evidence.',
            'original_hold_deadline_unchanged': True, 'whole_product_pass_inferred': False,
        }, reserve=600)
        require(response.get('run_id') == context['run_id'] and
                response.get('reviewer') == client.operator_reviewer, 'ROOT response crossed live owner')
        status = response.get('status')
        if status == 'observe':
            continue
        if status == 'nominate_other_rite':
            try:
                recipient, intent = response.get('recipient_id'), response.get('nomination_intent_id')
                require(phase['id'] == 'institution' and before_head is not None and
                        not factory_submitted and callable(getattr(client, 'read_readiness', None)),
                        'Nomination requires entered institution and fresh full readiness')
                require(type(recipient) is int and type(intent) is str and 0 < len(intent) <= 128 and
                        Path(intent).name == intent and intent not in nomination_intents and
                        recipient not in nominated_recipients,
                        'Nomination intent/recipient missing or already consumed; never replay')
                require(len(nomination_intents) < 8 and
                        type(navigation_deadline) in (int, float) and
                        math.isfinite(navigation_deadline) and
                        navigation_deadline - time.time() >= 300 and client.remaining() > 900,
                        'Nomination needs original phase and normal-Quit reserve')
                refs = response.get('evidence')
                require(type(refs) is list and refs, 'Nomination needs actual ROOT UI/source evidence')
                for ref in refs:
                    check_evidence(ref)
                require(client.snapshot(require_event_free=False).get('active_event') is None,
                        'Resolve current event before ordinary interaction')
                readiness = client.read_readiness(name + '-nomination-readiness')
                nominee = other_rite_nominee(readiness['roster'], recipient)
                args = {'interaction_key': NOMINATION_INTERACTION, 'recipient_id': recipient}
                query_frame, query_row = call(client, initial, name + '-nomination-query',
                    'ck3_query_character_interaction_ordinary_v1', args)
                query = query_row['result']
                terms = query.get('character_interaction_ordinary_context') or {}
                require(query.get('status') == 'available' and
                        query.get('queried_revision') == query_frame['revision'] and
                        query.get('queried_native_revision') == query_frame['native_revision'] and
                        terms.get('interaction_key') == NOMINATION_INTERACTION and
                        terms.get('recipient_id') == recipient and
                        terms.get('player_character_id') == initial['actor'] and
                        terms.get('ready_to_initiate') is True and
                        terms.get('shown') is True and terms.get('can_send') is True and
                        terms.get('auto_accept') is True and
                        terms.get('ordinary_context_supported') is True,
                        'Actual exact nomination interaction unavailable or not sendable')
                nomination_intents.add(intent)
                nominated_recipients.add(recipient)  # consume before once-only public submission
                intent_path = Path(context['output']) / (name + '-nomination-intent.json')
                write_once(intent_path, {'run_id': context['run_id'],
                    'reviewer': client.operator_reviewer, 'phase': phase['id'],
                    'interaction_key': NOMINATION_INTERACTION, 'recipient_id': recipient,
                    'nominee': nominee, 'nomination_intent_id': intent,
                    'original_phase_deadline': navigation_deadline,
                    'query_frame': binding(query_frame), 'query_status': query['status'],
                    'evidence': refs, 'NPC_acceptance_or_business_credit': False})
                _, receipt_row = call(client, initial, name + '-nomination-send',
                    'ck3_initiate_character_interaction_ordinary_v1', args)
                receipt = receipt_row['result']
                ack = receipt.get('character_interaction_ordinary_initiation') or {}
                receipt_path = Path(context['output']) / (name + '-nomination-receipt.json')
                write_once(receipt_path, {'run_id': context['run_id'],
                    'interaction_key': NOMINATION_INTERACTION, 'recipient_id': recipient,
                    'status': receipt.get('status'), 'queue_result': ack.get('native_queue_result'),
                    'dispatch_invoked': ack.get('dispatch_invoked'),
                    'action_request_id': receipt.get('action_request_id'),
                    'action_claim_path': receipt.get('action_claim_path'),
                    'business_postcondition_verified': False})
                last_nomination = {'recipient_id': recipient, 'intent': pin(intent_path),
                    'receipt': pin(receipt_path), 'NPC_acceptance_verified': False}
                last_error = None
            except ValueError as error:
                last_error = str(error)
            continue
        if status == 'navigate_decision':
            try:
                key, intent = response.get('decision_key'), response.get('navigation_intent_id')
                require(navigation_enabled and type(key) is str and key in navigation_keys,
                        'Decision navigation is not declared for this phase/key')
                require(type(intent) is str and 0 < len(intent) <= 128 and
                        Path(intent).name == intent and intent not in navigation_intents,
                        'Navigation intent missing or already consumed; never replay')
                require(len(navigation_intents) < navigation_limit, 'Phase navigation action limit reached')
                require(type(navigation_deadline) in (int, float) and math.isfinite(navigation_deadline) and
                        navigation_deadline - time.time() >= 300 and client.remaining() > 900,
                        'Navigation needs 300s on the original phase and more than 900s total reserve')
                refs = response.get('evidence')
                require(type(refs) is list and refs, 'Navigation needs actual ROOT source/UI evidence')
                for ref in refs:
                    check_evidence(ref)
                navigation_intents.add(intent)  # consume BEFORE any original public submission
                write_once(Path(context['output']) / (name + '-navigation-intent.json'), {
                    'run_id': context['run_id'], 'reviewer': client.operator_reviewer,
                    'phase': phase['id'], 'decision_key': key, 'navigation_intent_id': intent,
                    'original_phase_deadline': navigation_deadline, 'evidence': refs,
                    'Confirm_or_event_option_authorized': False, 'qualification_assigned': False})
                navigate(client, initial, name + '-navigation', key, deadline=navigation_deadline)
                last_navigation = {'decision_key': key, 'navigation_intent_id': intent,
                    'detail_navigation_completed': True, 'Confirm_performed': False,
                    'event_option_submitted': False, 'qualification_assigned': False}
                last_error = None
            except ValueError as error:
                last_error = str(error)
            continue
        if status in {'enter_institution', 'choose_option', 'read_precommit', 'admit_commit'}:
            try:
                evidence = response.get('evidence', [])
                require(evidence, 'Action needs actual reviewed original source/UI evidence')
                for ref in evidence:
                    check_evidence(ref)
                if status == 'enter_institution':
                    require(phase['id'] == 'institution' and not initial_requested and
                            not precommit_requested and not factory_submitted and actions == 0,
                            'Initial institution bundle is once-only and precedes production actions')
                    initial_requested = True
                    before_head = native_head_bundle(client, initial, name + '-initial')
                    continue
                require(phase['id'] != 'institution' or before_head is not None,
                        'Enter institution and review its initial bundle before production actions')
                if status == 'read_precommit':
                    require(phase['id'] == 'institution' and not precommit_requested and not factory_submitted,
                            'One fresh signed-precommit bundle only; no SAVE replay')
                    precommit_requested = True
                    precommit = native_head_bundle(client, initial, name + '-signed-precommit')
                    require(precommit['cache'] == before_head['cache'] and
                            precommit['title'].get('legal_head_title_absent') is True,
                            'Precommit political cache/head changed')
                    continue
                if status == 'admit_commit':
                    require(phase['id'] == 'institution' and precommit is not None and not factory_submitted and
                            all(response.get('facts', {}).get(k) is True for k in
                                ('fresh_precommit_SAVE_all_political_AST_heirs_laws_preserved',
                                 'production_quorum_and_all_human_consent_actual',
                                 'actual_serial_nonce_and_all_rite_signatures_current')),
                            'Fresh complete actual mandate/protection review missing')
                    require(packet is not None and packet['event']['event_definition_key'] == 'lyd.430',
                            'Commit admission needs actual current 430')
                    commit_event = (packet['event']['current_event_instance_id'],
                                    packet['event'].get('saved_scopes'))
                    continue
                require(actions < phase['maximum_option_actions'], 'Representative action limit reached')
                signature = (response.get('event_definition_key'), response.get('native_option_index'))
                require(phase['id'] == 'institution' or signature not in phase_options,
                        'This representative option was already submitted; no second payment')
                packet = current_event(client, initial, name + '-choice-fresh')
                require(packet is not None, 'Current event absent')
                is_factory = (response.get('event_definition_key') == 'lyd.430' and
                              response.get('native_option_index') == 0)
                actual_commit = (packet['event']['current_event_instance_id'], packet['event'].get('saved_scopes'))
                admitted = commit_event is not None and actual_commit == commit_event and not factory_submitted
                args, key = option_arguments(packet, response, phase.get('allowed_options', {}),
                                              consumed, commit_admitted=admitted)
            except ValueError as error:
                last_error = str(error)
                continue
            consumed.add(key)  # intent is consumed BEFORE the once-only public submission
            phase_options.add(signature)
            if is_factory:
                factory_submitted = True
            write_once(Path(context['output']) / (name + '-choice-intent.json'), args)
            rows = client.execute_plan([{'id': name + '-choice', 'tool': 'ck3_select_event_option',
                'args': args, 'fresh_revision': False}], name + '-choice')
            row = rows[0]
            validate_option_ack(row, args, key)
            after = client.validate_frame(row['after_snapshot'], require_event_free=False)
            same_scene(initial, after)
            require((after.get('active_event') or {}).get('instance_id') != key[0],
                    'Submitted original event still present; never repeat its action')
            actions += 1
            last_error = None
            continue
        require(status in {'complete', 'partial', 'skip', 'abort'}, 'Unknown ROOT disposition')
        refs = response.get('evidence', [])
        if status in {'complete', 'partial'}:
            require(isinstance(refs, list) and refs, 'Actual evidence required, not fixture/ACK')
            for ref in refs:
                check_evidence(ref)
        after = client.snapshot(require_event_free=False)
        same_scene(initial, after)
        facts = response.get('facts', {})
        qualified = status == 'complete' and isinstance(facts, dict) and all(
            facts.get(k) is True for k in phase['requirements'])
        if phase['id'] == 'institution':
            qualified = qualified and before_head is not None
        observations = {key: facts.get(key) if type(facts.get(key)) is bool else None
                        for key in phase.get('optional_observations', [])} if isinstance(facts, dict) else {
                            key: None for key in phase.get('optional_observations', [])}
        result = {'phase': phase['id'], 'status': status, 'qualified': qualified,
            'before_native_binding': initial, 'after_native_binding': binding(after),
            'review': response, 'submitted_option_actions': actions, 'last_contract_error': last_error,
            'submitted_navigation_actions': len(navigation_intents), 'last_navigation': last_navigation,
            'submitted_nomination_actions': len(nomination_intents), 'last_nomination': last_nomination,
            'optional_observations': observations, 'actual_initial_political_bundle': before_head,
            'fresh_signed_precommit_bundle': precommit, 'factory_submitted_by_adapter': factory_submitted}
        return result


def run_case(context, client):
    compiled, contract_pin = generic.compiled_contract(context)
    data = compiled['config']
    require(data['case_id'] == CASE, 'Wrong prepared keypath contract')
    initial_frame = client.snapshot(require_event_free=False)
    client.validate_frame(initial_frame, require_event_free=False)
    initial = binding(initial_frame)
    result = {'schema': 'lyd-release012-keypaths-result-v1', 'run_id': context['run_id'],
        'case': CASE, 'assertion_contract': contract_pin, 'actual_start_binding': initial,
        'cells': [], 'business_pass': False, 'whole_product_release_pass': False,
        'formal_B4_B5_C3_credit': False, 'full_T33_second_stage_credit': False,
        'all36_live_effect_credit': False, 'new_head_title_id': None}
    consumed = set()
    original = religion(client, initial, 'release012-original-religion')
    result['original_religion'] = original
    for phase in data['phases']:
        if phase.get('decision_key'):
            try:
                navigate(client, initial, 'release012-' + phase['id'], phase['decision_key'])
            except ValueError as error:
                client.checkpoint('release012-' + phase['id'] + '-navigation-gap', {
                    'error': str(error), 'action_replayed': False, 'business_pass': False})
        cell = review_cell(context, client, initial, phase, consumed)
        if phase['id'] == 'entry' and cell['qualified']:
            actual = religion(client, initial, 'release012-enrolled-religion')
            cell['actual_enrolled_religion'] = actual
            cell['qualified'] = (actual['faith_id'] == original['faith_id'] and
                                 actual['rite_id'] != original['rite_id'])
        if phase['id'] == 'personal_T01' and cell['qualified']:
            keys = religion(client, initial, 'release012-personal-T01', personal=True)
            cell['qualified'] = 'lyd_tenet_reverent_heaven' in keys.get('personal_tenet_keys', [])
            cell['actual_personal_parameters'] = keys
        if phase['id'] == 'institution' and cell['qualified']:
            before_head = cell['actual_initial_political_bundle']
            after_head = native_head_bundle(client, initial, 'release012-post-institution')
            cell['actual_before_head'], cell['actual_after_head'] = before_head, after_head
            cell['qualified'] = head_qualified(before_head, after_head, initial['actor'], original['faith_id'])
            if cell['qualified']:
                result['new_head_title_id'] = after_head['title']['head_title_full_id']
        result['cells'].append(cell)
        write_once(Path(context['output']) / (phase['id'] + '-cell-result.json'), cell)
        if cell['status'] == 'abort' or phase['id'] in {'baseline', 'entry'} and not cell['qualified']:
            break
    required = [p['id'] for p in data['phases'] if p.get('required') is True]
    result['case_contract_qualified'] = all(any(c['phase'] == p and c['qualified'] for c in result['cells'])
                                               for p in required)
    result['gui_contract_qualified'] = result['case_contract_qualified']
    result['runtime_status'] = 'REPRESENTATIVE_OBSERVED' if result['case_contract_qualified'] else 'PARTIAL_OR_RED'
    write_once(Path(context['output']) / RESULT, result)
    return result


def verify_case(context):
    compiled, contract_pin = generic.compiled_contract(context)
    result = generic.read_json(Path(context['output']) / RESULT)
    require(result.get('run_id') == context['run_id'] and result.get('case') == CASE and
            result.get('assertion_contract') == contract_pin, 'Keypath result/contract crossed run')
    for cell in result['cells']:
        same_scene(result['actual_start_binding'], {
            'played_character': {'character_id': cell['after_native_binding']['actor'], 'alive': True},
            'paused': True, 'revision': cell['after_native_binding']['revision'],
            'native_revision': cell['after_native_binding']['native_revision'],
            'date_raw': cell['after_native_binding']['date_raw'],
            'diagnostics': {'bridge_pid': cell['after_native_binding']['game_pid'],
                            'connection_generation': cell['after_native_binding']['generation']}})
        for ref in cell['review'].get('evidence', []):
            check_evidence(ref)
    required = [p['id'] for p in compiled['config']['phases'] if p.get('required') is True]
    qualified = all(any(c['phase'] == p and c['qualified'] is True for c in result['cells']) for p in required)
    return {**result, 'case_contract_qualified': qualified, 'gui_contract_qualified': qualified,
        'business_pass': False, 'whole_product_release_pass': False,
        'formal_B4_B5_C3_credit': False, 'normal_close_independently_required': True,
        'evidence': [pin(Path(context['output']) / RESULT), contract_pin]}
