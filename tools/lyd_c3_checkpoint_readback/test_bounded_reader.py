"""Small synthetic serializer/error fixtures only; no actual save or native calls."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import challenger_reader as r

HERE = Path(__file__).resolve().parent
POLITICAL = list(range(100, 107))
BINDING = {'authority': 'SYNTHETIC_TEST_ONLY', 'fixture_only': True,
           'title_variable_type': 'title',
           'collection': {'path': ['synthetic_native_collection'], 'encoding': 'anonymous_scalars', 'absence_means_empty': False},
           'sponsor_title_path': ['synthetic_native_sponsor']}

def e(key, value):
    return {'key': key, 'value': value}

def variables(values):
    return [e('data', [e(None, [e('flag', json.dumps(name)), e('data', [e('type', kind), e('identity', ident)])]) for name, kind, ident in values])]

def lists(values):
    return [e('list', [e(None, [e('name', json.dumps(name))] + [e('item', [e('type', kind), e('identity', i)]) for i in ids]) for name, kind, ids in values])]

def render(rows, depth=0):
    lines = []
    prefix = '\t' * depth
    for row in rows:
        name = '' if row['key'] is None else str(row['key']) + '='
        value = row['value']
        if isinstance(value, list):
            lines.extend([prefix + name + '{', render(value, depth + 1).rstrip('\n'), prefix + '}'])
        else:
            lines.append(prefix + name + str(value))
    return '\n'.join(lines) + '\n'

def fixture(stage='REGISTER', serial=5, claim_id='902', head_yes=1, delegate_yes=1, player_yes=1):
    claimed = stage in {'REGISTER', 'ACTIVE', 'READY', 'CANCELLED'}
    active = stage in {'ACTIVE', 'READY'}
    recognized = stage == 'RECOGNIZED'
    retired = stage in {'WITHDRAWN', 'RECOGNIZED'}
    av = [('lyd_i3b_result_head_title', 'title', '901'), ('lyd_i3b_result_code', 'value', '100000')]
    if claimed:
        av += [('lyd_c3_claim_title', 'title', claim_id), ('lyd_c3_claim_faith', 'faith', '11'), ('lyd_c3_claim_rite', 'rite', '1'), ('lyd_c3_claim_registration_result', 'value', '100000')]
    if active or stage in {'CANCELLED', 'RECOGNIZED'}:
        av += [('lyd_c3_serial', 'value', str(serial * 100000))]
    actor_lists = []
    rite_values = []
    dormant_values = []
    if active:
        av += [('lyd_c3_active', 'value', '100000'), ('lyd_c3_round_faith', 'faith', '11'), ('lyd_c3_round_main', 'rite', '1'), ('lyd_c3_round_head', 'char', '8'), ('lyd_c3_round_title', 'title', '901'), ('lyd_c3_head_yes', 'value', str(head_yes * 100000)), ('lyd_c3_affected_owner', 'char', '7'), ('lyd_c3_affected_serial', 'value', str(serial * 100000)), ('lyd_c3_affected_rite', 'rite', '1'), ('lyd_c3_player_yes', 'value', str(player_yes * 100000))]
        actor_lists = [('lyd_c3_rites', 'rite', ['1', '2']), ('lyd_c3_players', 'char', ['7'])]
        rite_values = [('lyd_c3_proposal_owner', 'char', '7'), ('lyd_c3_lock_serial', 'value', str(serial * 100000)), ('lyd_c3_delegate_required', 'value', '100000'), ('lyd_c3_delegate', 'char', '7'), ('lyd_c3_delegate_yes', 'value', str(delegate_yes * 100000))]
        dormant_values = [('lyd_c3_proposal_owner', 'char', '7'), ('lyd_c3_lock_serial', 'value', str(serial * 100000)), ('lyd_c3_delegate_required', 'value', '0'), ('lyd_c3_delegate_yes', 'value', '0')]
    actor_alive = [e('variables', variables(av) + lists(actor_lists))]
    domain = [e(None, str(i)) for i in POLITICAL] + ([e(None, claim_id)] if claimed else []) + ([e(None, '901')] if recognized or stage == 'PRE_HANDOFF' else [])
    actor = [e('rite', '1'), e('alive_data', actor_alive), e('landed_data', [e('domain', domain), e('synthetic_primary', '100'), e('synthetic_capital', '100')])]
    char = lambda name: [e('rite', '1'), e('first_name', json.dumps(name)), e('alive_data', [])]
    head_holder = '7' if recognized or stage == 'PRE_HANDOFF' else '8'
    coll = [claim_id, '903'] if claimed else ['903']
    faith_values = [('lyd_c3_recognized_leader', 'char', '7')] if recognized else []
    faith = [e('main_rite', '1'), e('religious_head', head_holder), e('religious_head_title', '901'), e('synthetic_native_collection', [e(None, x) for x in coll]), e('variables', variables(faith_values))]
    rite = [e('faith', '11'), e('head_of_rite', '7'), e('variables', variables(rite_values))]
    dormant = [e('faith', '11'), e('head_of_rite', '4294967295'), e('variables', variables(dormant_values))]
    titles = [e(str(i), [e('holder', '7'), e('synthetic_label', json.dumps('political' + str(i)))]) for i in POLITICAL]
    titles += [e('107', [e('holder', '8'), e('synthetic_label', '"NPC_nonreligious"')]),
               e('901', [e('holder', head_holder), e('variables', variables([('lyd_c2_owned_head_title', 'value', '100000'), ('lyd_c2_owner_faith', 'faith', '11')]))]),
               e('903', [e('holder', '9'), e('synthetic_native_sponsor', '903'), e('synthetic_label', '"another_challenger"')])]
    if claimed or retired:
        titles.append(e(claim_id, [e('holder', '7' if claimed else '4294967295'), e('synthetic_native_sponsor', claim_id), e('variables', variables([('lyd_c3_owned_claim_title', 'value', '100000'), ('lyd_c3_owner_faith', 'faith', '11'), ('lyd_c3_owner_rite', 'rite', '1')]))]))
    text = 'date=1.1.1\ncurrently_played_characters={ 7 }\n'
    text += render([e('meta_data', [e('version', '"1.20.0.3"'), e('save_game_version', '17'), e('meta_date', '1.1.1')]), e('played_character', [e('character', '7')]), e('faiths', [e('database', [e('11', faith)])]), e('rites', [e('database', [e('1', rite), e('2', dormant)])])])
    text += 'living={\n' + render([e('7', actor), e('8', char('incumbent')), e('9', char('other_claimant'))]) + '}\ndead_unprunable={\n}\n'
    text += 'landed_titles={\n' + render(titles) + '}\ndynasties={\n}\n'
    return text

def state(stage='REGISTER', before=None, **kwargs):
    return r.project(fixture(stage, **kwargs), 7, 8, POLITICAL, BINDING,
                     list(before['characters']) if before else [], list(before['titles']) if before else [])

def change_var(snapshot, name, value, container=None):
    row = (container if container is not None else snapshot['actor_variables'])[name]
    row['number'] = str(value)
    row['identity'] = str(int(value) * 100000)

class ReaderFixtureTests(unittest.TestCase):
    def test_complete_two_challengers_not_first(self):
        before = state('HANDOFF')
        current = state('REGISTER', before)
        result = r.assert_graph(current, 'REGISTER', before)
        self.assertEqual(result['full_native_challenger_items'], ['902', '903'])
        self.assertEqual([x['title_id'] for x in current['native_challenger_titles']], ['902', '903'])
        self.assertIsNone(result['native_business_credit'])

    def test_discover_never_promotes_native_field(self):
        discovered = r.project(fixture(), 7, 8, POLITICAL)
        self.assertEqual(discovered['faiths']['11']['native_challengers']['status'], 'UNKNOWN_SERIALIZATION')
        self.assertIsNone(discovered['faiths']['11']['native_challengers']['items'])
        with self.assertRaisesRegex(r.ReadError, 'typed I3b result Title|unqualified'):
            r.assert_graph(discovered, 'REGISTER')
        self.assertIsNone(discovered['native_title'])
        self.assertEqual(discovered['partial_native_title']['title_id'], '901')
        self.assertEqual(discovered['result_head_title_reference']['type'], 'title')

    def test_saved_title_typename_is_supplied_not_guessed(self):
        binding = dict(BINDING, title_variable_type='synthetic_title_scope')
        current = r.project(fixture().replace('type=title', 'type=synthetic_title_scope'), 7, 8, POLITICAL, binding)
        self.assertEqual(current['native_title']['title_id'], '901')
        self.assertEqual(r.assert_graph(current, 'REGISTER')['status'], 'SAVED_GRAPH_ASSERTIONS_MATCH')
        with self.assertRaisesRegex(r.ReadError, 'wrong typed'):
            r.project(fixture().replace('type=title', 'type=char'), 7, 8, POLITICAL, BINDING)

    def test_unrelated_zero_database_record_is_preserved_losslessly(self):
        text = fixture().replace('faiths={\n\tdatabase={\n', 'faiths={\n\tdatabase={\n\t\t0={\n\t\t\tmain_rite=0\n\t\t}\n').replace('rites={\n\tdatabase={\n', 'rites={\n\tdatabase={\n\t\t0={\n\t\t\tfaith=0\n\t\t}\n')
        current = r.project(text, 7, 8, POLITICAL, BINDING)
        self.assertEqual(current['all_rite_parents']['0'], '0')
        self.assertEqual(current['all_faith_mains']['0'], {'status': 'VALUE', 'identity': '0'})
        self.assertEqual(r.assert_graph(current, 'REGISTER')['status'], 'SAVED_GRAPH_ASSERTIONS_MATCH')

    def test_unreferenced_actor_title_is_preserved_without_role_invention(self):
        orphan = render([e('999', [e('holder', '7'), e('variables', variables([('lyd_c2_owned_head_title', 'value', '100000'), ('lyd_c2_owner_faith', 'faith', '11')]))])])
        text = fixture().replace('landed_titles={\n', 'landed_titles={\n' + orphan)
        current = r.project(text, 7, 8, POLITICAL, BINDING)
        self.assertIn('999', [row['title_id'] for row in current['actor_other_held_titles']])
        self.assertEqual(current['native_title']['title_id'], '901')
        self.assertNotIn('999', current['faiths']['11']['native_challengers']['items'])

    def test_all_supported_collection_encodings(self):
        self.assertEqual(r.collection([e('synthetic_native_collection', [e(None, '902'), e(None, '903')])], BINDING['collection'])['items'], ['902', '903'])
        repeated = {'path': ['native'], 'encoding': 'repeated_scalar'}
        self.assertEqual(r.collection([e('native', '902'), e('native', '903')], repeated)['items'], ['902', '903'])
        records = {'path': ['native'], 'encoding': 'anonymous_records', 'item_title_path': ['exact_title']}
        self.assertEqual(r.collection([e('native', [e(None, [e('exact_title', '902')]), e(None, [e('exact_title', '903')])])], records)['items'], ['902', '903'])

    def test_empty_missing_unknown_are_distinct(self):
        self.assertEqual(r.collection([e('synthetic_native_collection', [])], BINDING['collection'])['items'], [])
        with self.assertRaisesRegex(r.ReadError, 'missing'):
            r.collection([], BINDING['collection'])
        allowed = dict(BINDING['collection'], absence_means_empty=True)
        self.assertEqual(r.collection([], allowed)['status'], 'QUALIFIED_ABSENT_EMPTY')
        with self.assertRaisesRegex(r.ReadError, 'encoding'):
            r.collection([e('synthetic_native_collection', [])], dict(BINDING['collection'], encoding='invented'))

    def test_duplicate_native_item_rejected(self):
        with self.assertRaisesRegex(r.ReadError, 'duplicate'):
            r.collection([e('synthetic_native_collection', [e(None, '902'), e(None, '902')])], BINDING['collection'])

    def test_bad_record_title_shape_rejected(self):
        binding = {'path': ['native'], 'encoding': 'anonymous_records', 'item_title_path': ['exact_title']}
        with self.assertRaisesRegex(r.ReadError, 'nonunique'):
            r.collection([e('native', [e(None, [e('exact_title', '902'), e('exact_title', '903')])])], binding)

    def test_handoff_preserves_actor_landed_except_religious_title(self):
        before = state('PRE_HANDOFF')
        after = state('HANDOFF', before)
        self.assertEqual(r.assert_graph(after, 'HANDOFF', before)['status'], 'SAVED_GRAPH_ASSERTIONS_MATCH')

    def test_withdraw_removes_only_exact_native_title(self):
        before = state('REGISTER')
        after = state('WITHDRAWN', before)
        self.assertEqual(r.assert_graph(after, 'WITHDRAW', before)['full_native_challenger_items'], ['903'])
        self.assertEqual(after['watched_title_records']['902']['holder']['status'], 'INVALID_SENTINEL')

    def test_repeat_register_fresh_title_keeps_other_challenger(self):
        old = state('REGISTER')
        retired = state('WITHDRAWN', old)
        new = state('REGISTER', retired, claim_id='904')
        self.assertEqual(r.assert_graph(new, 'REGISTER', retired)['full_native_challenger_items'], ['904', '903'])

    def test_foreign_collection_loss_rejected(self):
        before = state('HANDOFF')
        after = state('REGISTER', before)
        after['faiths']['11']['native_challengers']['items'] = ['902']
        with self.assertRaisesRegex(r.ReadError, 'beyond exact'):
            r.assert_graph(after, 'REGISTER', before)

    def test_foreign_challenger_ast_mutation_rejected(self):
        before = state('HANDOFF')
        after = state('REGISTER', before)
        after['titles']['903']['entries'][0]['value'] = '8'
        with self.assertRaisesRegex(r.ReadError, 'another challenger'):
            r.assert_graph(after, 'REGISTER', before)

    def test_foreign_sponsor_changed_rejected(self):
        before = state('HANDOFF')
        after = state('REGISTER', before)
        after['native_challenger_sponsors']['903'] = '107'
        with self.assertRaisesRegex(r.ReadError, 'sponsorship'):
            r.assert_graph(after, 'REGISTER', before)

    def test_typed_title_scope_confusion_rejected(self):
        text = fixture().replace('flag="lyd_i3b_result_head_title"\n\t\t\t\t\t\tdata={\n\t\t\t\t\t\t\ttype=title', 'never_matching')
        wrong = state()
        wrong['actor_variables']['lyd_i3b_result_head_title']['type'] = 'char'
        with self.assertRaisesRegex(r.ReadError, 'wrong typed'):
            r.typed_var(wrong['actor_variables'], 'lyd_i3b_result_head_title', 'title')

    def test_switch_exact_I3b_title_in_transition_rejected(self):
        before = state('HANDOFF')
        after = copy.deepcopy(before)
        after['identity']['I3b_result_head_title'] = '999'
        after['native_title']['title_id'] = '999'
        after['faiths']['11']['head_title']['identity'] = '999'
        with self.assertRaisesRegex(r.ReadError, 'typed identity'):
            r.assert_graph(after, 'HANDOFF', before)

    def test_political_full_AST_and_holder_mutation_rejected(self):
        before = state('HANDOFF')
        after = state('REGISTER', before)
        after['protected_titles'][0]['entries'].append(e('injected', 'yes'))
        with self.assertRaisesRegex(r.ReadError, 'full Title AST'):
            r.assert_graph(after, 'REGISTER', before)

    def test_NPC_nonreligious_full_AST_mutation_rejected(self):
        before = state('HANDOFF')
        after = state('REGISTER', before)
        after['titles']['107']['entries'].append(e('injected', 'yes'))
        with self.assertRaisesRegex(r.ReadError, 'NPC nonreligious'):
            r.assert_graph(after, 'REGISTER', before)

    def test_unrelated_marked_office_is_not_domain_exception(self):
        before = state('HANDOFF')
        after = copy.deepcopy(before)
        before['actor_landed_data'][0]['value'].append(e(None, '999'))
        before['titles']['999'] = copy.deepcopy(before['native_title'])
        before['titles']['999']['variables']['lyd_c3_owned_claim_title'] = {'type': 'value', 'identity': '100000', 'number': '1'}
        with self.assertRaisesRegex(r.ReadError, 'landed AST'):
            r.compare_protection(after, before)

    def test_actor_primary_capital_field_change_rejected_without_guessing_key(self):
        before = state('HANDOFF')
        after = state('REGISTER', before)
        after['actor_landed_data'][1]['value'] = '999'
        with self.assertRaisesRegex(r.ReadError, 'landed AST'):
            r.assert_graph(after, 'REGISTER', before)

    def test_main_native_HoR_must_remain_actor(self):
        current = state()
        current['rites']['1']['HoR']['identity'] = '8'
        with self.assertRaisesRegex(r.ReadError, 'HoR protection'):
            r.assert_graph(current, 'REGISTER')

    def test_other_Rite_HoR_drift_rejected(self):
        before = state('HANDOFF')
        after = state('REGISTER', before)
        after['rites']['2']['HoR'] = {'status': 'VALUE', 'identity': '8'}
        with self.assertRaisesRegex(r.ReadError, 'HoR graph changed'):
            r.assert_graph(after, 'REGISTER', before)

    def test_ready_requires_real_saved_yes_fields(self):
        ready = state('READY')
        self.assertEqual(r.assert_graph(ready, 'ROUND_READY', expected_serial=5)['status'], 'SAVED_GRAPH_ASSERTIONS_MATCH')
        no = state('READY', head_yes=0)
        with self.assertRaisesRegex(r.ReadError, 'not released'):
            r.assert_graph(no, 'ROUND_READY')
        self.assertEqual(r.assert_graph(no, 'ROUND_ACTIVE')['status'], 'SAVED_GRAPH_ASSERTIONS_MATCH')
        self.assertFalse(r.assert_graph(no, 'ROUND_ACTIVE')['NPC_AI_choice_receipt_verified'])

    def test_missing_human_consent_rejected(self):
        with self.assertRaisesRegex(r.ReadError, 'human has not consented'):
            r.assert_graph(state('READY', player_yes=0), 'ROUND_READY')

    def test_missing_delegate_consent_rejected(self):
        with self.assertRaisesRegex(r.ReadError, 'delegate has not consented'):
            r.assert_graph(state('READY', delegate_yes=0), 'ROUND_READY')

    def test_stale_Rite_lock_serial_rejected(self):
        current = state('ACTIVE')
        change_var(current, 'lyd_c3_lock_serial', 4, current['rites']['1']['variables'])
        with self.assertRaisesRegex(r.ReadError, 'owner/serial'):
            r.assert_graph(current, 'ROUND_ACTIVE')

    def test_known_follower_cannot_be_dormant(self):
        current = state('ACTIVE')
        change_var(current, 'lyd_c3_delegate_required', 0, current['rites']['1']['variables'])
        with self.assertRaisesRegex(r.ReadError, 'dormant'):
            r.assert_graph(current, 'ROUND_ACTIVE')

    def test_cancel_repeat_fresh_serial_and_old329_preservation(self):
        previous = state('ACTIVE', serial=5)
        cancelled = state('CANCELLED', previous, serial=5)
        r.assert_graph(cancelled, 'ROUND_CANCELLED', previous)
        new = state('ACTIVE', cancelled, serial=6)
        self.assertEqual(r.assert_repeat_round(cancelled, new)['new_serial'], '6')
        self.assertFalse(r.assert_stale_timeout_preservation(new, copy.deepcopy(new), 5)['actual_old_event_delivery_verified'])
        damaged = copy.deepcopy(new)
        damaged['actor_variables'].pop('lyd_c3_active')
        with self.assertRaises(r.ReadError):
            r.assert_stale_timeout_preservation(new, damaged, 5)
        with self.assertRaisesRegex(r.ReadError, 'fresh serial'):
            r.assert_repeat_round(cancelled, state('ACTIVE', cancelled, serial=5))

    def test_recognition_matches_exact_pre_ready_title_serial_and_cleanup(self):
        before = state('READY', serial=5)
        after = state('RECOGNIZED', before, serial=5)
        self.assertEqual(r.assert_graph(after, 'RECOGNIZE', before, expected_serial=5)['status'], 'SAVED_GRAPH_ASSERTIONS_MATCH')
        with self.assertRaisesRegex(r.ReadError, 'serial mismatch'):
            r.assert_graph(after, 'RECOGNIZE', before, expected_serial=4)
        damaged = copy.deepcopy(after)
        damaged['rites']['1']['variables']['lyd_c3_lock_serial'] = before['rites']['1']['variables']['lyd_c3_lock_serial']
        with self.assertRaisesRegex(r.ReadError, 'remains after release'):
            r.assert_graph(damaged, 'RECOGNIZE', before)

    def test_reload_projection_identity_and_graph_matches_no_process_claim(self):
        before = state('REGISTER')
        after = r.project(fixture('REGISTER'), 7, 8, POLITICAL, BINDING)
        result = r.assert_graph(after, 'REGISTER', before)
        self.assertIsNone(result['native_business_credit'])
        self.assertNotIn('PID', result)

    def test_bounds_and_lexical_errors(self):
        for raw in ('{ a="unfinished }', '{ a=1 # unsupported }', '{ { a=1 }', '{ a=1 } extra'):
            with self.assertRaises(ValueError):
                r.bounded_parse(raw)
        with patch.object(r, 'MAX_TOKENS', 2):
            with self.assertRaisesRegex(r.ReadError, 'token limit'):
                r.bounded_parse('{ a=1 }')
        with patch.object(r, 'MAX_DEPTH', 1):
            with self.assertRaisesRegex(r.ReadError, 'depth'):
                r.bounded_parse('{ nested={ } }')

    def test_duplicate_native_record_rejected(self):
        with self.assertRaisesRegex(r.ReadError, 'duplicate'):
            r.record_index('1={\n}\n1={\n}\n')

    def test_unbound_actual_request_rejects_before_save_open(self):
        request = {'schema': 'lyd.c3.checkpoint-reader-request.v1', 'source_head': r.SOURCE_HEAD, 'phase': 'REGISTER', 'actor_id': None, 'incumbent_id': None, 'political_title_ids': [None] * 7, 'save': None, 'schema_binding': None, 'before_state': None, 'expected_serial': None, 'output': None}
        path = HERE / 'fixtures/unbound-request.json'
        with patch.object(r, 'pinned_ref', side_effect=AssertionError('must not read save')):
            with self.assertRaisesRegex(r.ReadError, 'fully bound identities'):
                r.main(path)

    def test_unqualified_title_mapping_rejects_before_save_open(self):
        binding = {'authority': 'ROOT_ACTUAL_NATIVE_SERIALIZATION_CROSSCHECK', 'fixture_only': False,
                   'title_variable_type': None, 'collection': BINDING['collection'],
                   'qualification_evidence': {'path': 'SYNTHETIC_UNUSED', 'bytes': 0, 'sha256': '0' * 64}}
        with patch.object(r, 'pinned_ref', side_effect=[json.dumps(binding).encode(), b'']) as refs:
            with self.assertRaisesRegex(r.ReadError, 'qualified Title typename'):
                r.main(HERE / 'fixtures/bound-identities-unqualified-title.json')
            self.assertEqual(refs.call_count, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
