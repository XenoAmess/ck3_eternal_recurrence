"""Granular institution requirements and original-player route policy ASTs.

Synthetic scope evaluation checks UI/authorization equivalence, not CK3 UI,
native head creation, scholarly votes or a live institution outcome.
"""
import hashlib
from pathlib import Path
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE.parent / 'tools'))
from extract_auto_upgrade_buildings import Block, Entry, parse_clausewitz
from test_content_leadership import Corpus, one, scalar
from test_institution_detached import PolicyAST, Scope, world
import gen_institution

DECISIONS = 'common/decisions/lyd_i3b_institution_decisions.txt'
UNCHANGED_POLICY = {
    'common/script_values/lyd_i3b_institution_values.txt': '61df8e591ac291644b103279d69665ed35f68c4f3aa63e286576583c8fae0156',
    'common/scripted_effects/lyd_i3b_setup_effects.txt': 'fa913461b91dbd8a876dd4fac320c6f3d5a15222afd650b4fc68276e8cad03c7',
    'common/scripted_effects/lyd_i3b_response_effects.txt': 'cb5e9f9cc16cd6d12ffabf191e34490769bd1f6cc320dfdf0e0e3dde003b11e6',
    'common/scripted_effects/lyd_i3b_commit_effects.txt': 'dd327b875eb0c374937461a8d8cde8a384a994911260d9065fa2b51387a68d3c',
    'common/character_interactions/lyd_i3b_nomination_interactions.txt': '410ebb1a28542f160a9b45a49c017d15dacc39c375c4d358616301c577c2bb98',
}
# The new support/progress tests invert only declared UI/AI additions before
# comparing these old ASTs. Authority, callbacks and player options stay frozen.
PREVIOUS_PRESENTATION_AST = {
    'common/scripted_effects/lyd_i3b_terms_effects.txt': '91505124f0c4a32218398b0bab359694bc80b9e7b8a96b27180b93e346c4c69e',
    'events/lyd_i3b_institution_events.txt': '49ecae7bfd0906752bbac20e75a8aca99bce3415054c2fd17e380f85bba6160c',
}


class TooltipPolicy(PolicyAST):
    """Reuse the existing policy evaluator; unwrap only UI metadata."""
    def entry(self, entry, current):
        if entry.key == 'custom_description':
            return self.block(Block([e for e in entry.value.entries
                                     if e.key not in {'text', 'subject'}]), current)
        return super().entry(entry, current)


class InstitutionTooltipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = gen_institution.build_outputs()
        cls.defs = Corpus().triggers
        cls.decisions = {e.key: e.value for e in parse_clausewitz(
            cls.outputs[DECISIONS].decode('utf-8-sig')).entries}

    def validity(self, suffix):
        return one(self.decisions[f'lyd_i3b_{suffix}_decision'], 'is_valid')

    def rows(self, suffix):
        return {scalar(e.value, 'text'): e.value
                for e in self.validity(suffix).entries
                if e.key == 'custom_description'}

    def summary_key(self, suffix):
        prefix = 'begin' if suffix == 'begin' else 'nominate'
        return f'lyd_i3b_{prefix}_complete_tt'

    def complete_gate(self, suffix):
        summary = self.rows(suffix)[self.summary_key(suffix)]
        return Block(tuple(e for e in summary.entries if e.key not in {'text', 'subject'}))

    def visible_result(self, suffix, state):
        actor, _, _, _, globals_, env = state
        engine = TooltipPolicy(self.defs, actor, globals_, env.copy())
        visible = Block([e for e in self.validity(suffix).entries
                         if scalar(e.value, 'text') != self.summary_key(suffix)])
        return engine.block(visible, actor)

    def original_result(self, suffix, state):
        actor, _, _, _, globals_, env = state
        engine = PolicyAST(self.defs, actor, globals_, env.copy())
        return engine.block(self.complete_gate(suffix), actor)

    def nomination_world(self):
        state = world(detached=False, active=True)
        state[0].variables['lyd_i3b_phase'] = 1
        state[3].variables.pop('lyd_i3b_delegate')
        return state

    def test_complete_authorization_and_effect_rechecks_remain(self):
        expected = {
            'begin': 'lyd_i3b_can_begin_trigger = yes',
            'nominate_self': 'lyd_i3b_current_trigger = { ACTOR = root } lyd_i3b_elector_trigger = yes var:lyd_i3b_phase = 1 rite = { NOT = { has_variable = lyd_i3b_delegate } var:lyd_i3b_dormant = 0 }',
        }
        for suffix, gate in expected.items():
            with self.subTest(suffix=suffix):
                self.assertEqual(self.complete_gate(suffix), parse_clausewitz(gate))
                original = parse_clausewitz('hidden_effect = { if = { limit = { lyd_i3b_actor_trigger = yes ' + gate + ' } lyd_i3b_' + suffix + '_effect = yes } }')
                self.assertEqual(one(self.decisions[f'lyd_i3b_{suffix}_decision'], 'effect'), original)

    def test_begin_visible_checks_match_actual_policy_counterexamples(self):
        changes = [
            ('baseline', lambda a,n,f,r,g,e: None),
            ('learning5', lambda a,n,f,r,g,e: a.fields.update(learning=5)),
            ('imprisoned', lambda a,n,f,r,g,e: a.fields.update(is_imprisoned=True)),
            ('child', lambda a,n,f,r,g,e: a.fields.update(is_adult=False)),
            ('dead', lambda a,n,f,r,g,e: a.fields.update(is_alive=False)),
            ('unlanded', lambda a,n,f,r,g,e: a.fields.update(is_landed=False)),
            ('incapable', lambda a,n,f,r,g,e: a.fields['traits'].add('incapable')),
            ('count', lambda a,n,f,r,g,e: a.fields.update(highest_held_title_tier=2)),
            ('gender', lambda a,n,f,r,g,e: r.fields.update(allowed_gender=False)),
            ('not_joined', lambda a,n,f,r,g,e: a.fields['flags'].clear()),
            ('head', lambda a,n,f,r,g,e: f.fields.update(religious_head=n)),
            ('empty_head_title', lambda a,n,f,r,g,e: f.fields.update(religious_head_title=Scope('office'))),
            ('challenger', lambda a,n,f,r,g,e: f.fields['challengers'].append(Scope('challenger', {'holder': n}))),
            ('own_office', lambda a,n,f,r,g,e: a.fields['held_titles'].append(Scope('office', {'is_head_of_faith': True}))),
            ('claim', lambda a,n,f,r,g,e: a.variables.update(lyd_c3_claim_title=Scope('claim'))),
            ('own_round', lambda a,n,f,r,g,e: a.variables.update(lyd_i3b_active=1)),
            ('c2_round', lambda a,n,f,r,g,e: a.variables.update(lyd_c2_active=1)),
            ('c3_round', lambda a,n,f,r,g,e: a.variables.update(lyd_c3_active=1)),
            ('rite_lock', lambda a,n,f,r,g,e: r.variables.update(lyd_c2_proposal_owner=n)),
            ('faith_doctrine', lambda a,n,f,r,g,e: f.fields.update(doctrines={'doctrine_temporal_head'})),
            ('rite_doctrine', lambda a,n,f,r,g,e: r.fields['doctrines'].add('doctrine_spiritual_head')),
            ('foreign_rite', lambda a,n,f,r,g,e: f.fields['rites'].append(Scope('foreign', {'faith': f}))),
        ]
        for route in ('legacy', 'detached', 'vanilla'):
            for name, change in changes:
                with self.subTest(route=route, name=name):
                    state = world(detached=route == 'detached', active=False)
                    if route == 'vanilla':
                        state[4]['faith:lyd_common_faith'] = Scope('unusedLegacyFaith')
                        state[4]['faith:confucian_faith'] = state[2]
                    change(*state)
                    self.assertEqual(self.visible_result('begin', state), self.original_result('begin', state))
                    engine = TooltipPolicy(self.defs, state[0], state[4], state[5].copy())
                    self.assertEqual(engine.block(self.validity('begin'), state[0]), self.original_result('begin', state))
        for field, value in [('learning', 5), ('is_imprisoned', True)]:
            state = world(detached=False, active=False)
            state[0].fields[field] = value
            self.assertTrue(self.visible_result('begin', state), field)

    def test_nomination_visible_checks_match_actual_full_gate(self):
        changes = [
            ('baseline', lambda a,n,f,r,g,e: None),
            ('learning5', lambda a,n,f,r,g,e: (a.fields.update(learning=5), a.variables.update(lyd_i3b_was_elector=0))),
            ('imprisoned', lambda a,n,f,r,g,e: (a.fields.update(is_imprisoned=True), a.variables.update(lyd_i3b_was_elector=0))),
            ('sealed', lambda a,n,f,r,g,e: a.variables.update(lyd_i3b_phase=2)),
            ('delegate', lambda a,n,f,r,g,e: r.variables.update(lyd_i3b_delegate=n)),
            ('dormant', lambda a,n,f,r,g,e: r.variables.update(lyd_i3b_dormant=1)),
            ('drifted', lambda a,n,f,r,g,e: a.variables.update(lyd_i3b_faith=Scope('differentFaith'))),
        ]
        for name, change in changes:
            with self.subTest(name=name):
                state = self.nomination_world()
                change(*state)
                self.assertEqual(self.visible_result('nominate_self', state), self.original_result('nominate_self', state))
                engine = TooltipPolicy(self.defs, state[0], state[4], state[5].copy())
                self.assertEqual(engine.block(self.validity('nominate_self'), state[0]), self.original_result('nominate_self', state))
        self.assertTrue(self.visible_result('nominate_self', self.nomination_world()))

    def test_learning_and_free_status_have_distinct_red_rows(self):
        state = self.nomination_world()
        state[0].fields.update(learning=5, is_imprisoned=True)
        engine = TooltipPolicy(self.defs, state[0], state[4], state[5].copy())
        rows = self.rows('nominate_self')
        self.assertFalse(engine.entry(parse_clausewitz('custom_description = { text = ignored learning >= 15 }').entries[0], state[0]))
        for key in ('learning', 'free'):
            self.assertFalse(engine.entry(Entry(
                'custom_description', '=', rows[f'lyd_i3b_nominate_{key}_tt']), state[0]))
        self.assertTrue(engine.entry(Entry(
            'custom_description', '=', rows['lyd_i3b_nominate_adult_tt']), state[0]))

    def test_policy_rosters_votes_and_callbacks_are_byte_unchanged(self):
        # The separate original-player tests invert only the reviewed I3b actor
        # and mode-2 changes against the existing frozen trigger AST hash.
        for path, digest in UNCHANGED_POLICY.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256(self.outputs[path]).hexdigest(), digest)
                self.assertEqual((SOURCE / path).read_bytes(), self.outputs[path])

    def test_requirements_are_separate_localized_and_generated(self):
        for suffix, count in [('begin', 25), ('nominate_self', 9)]:
            rows = self.rows(suffix)
            self.assertEqual(len(rows), count + 1)
            self.assertEqual([entry.key for entry in self.validity(suffix).entries],
                             ['custom_description'] * (count + 1))
            self.assertEqual(scalar(self.validity(suffix).entries[-1].value, 'text'), self.summary_key(suffix))
            self.assertNotIn('hidden_trigger', self.outputs[DECISIONS].decode('utf-8-sig'))
            for language in ('simp_chinese', 'english'):
                raw = self.outputs[f'localization/{language}/lyd_i3b_institution_l_{language}.yml']
                self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
                text = raw.decode('utf-8-sig')
                for key in rows:
                    self.assertEqual(text.count(f' {key}:0 "'), 1, key)
        for path, payload in self.outputs.items():
            self.assertEqual((SOURCE / path).read_bytes(), payload, path)

    def test_zero_scholar_guidance_preserves_real_eligibility(self):
        cn = self.outputs['localization/simp_chinese/lyd_i3b_institution_l_simp_chinese.yml'].decode('utf-8-sig')
        seal = next(line for line in cn.splitlines() if line.startswith(' lyd_i3b_seal_valid_tt:'))
        for term in ('先撤回', '重新发起', '实际学识至少15', '同信仰同礼仪', '不算休眠', '不能补假票', '三分之二'):
            self.assertIn(term, seal)
        self.assertIn('生活方式经验不等于达标', seal)
        nominate = next(line for line in cn.splitlines() if line.startswith(' lyd_i3b_nominate_learning_tt:'))
        self.assertIn('不能自提名', nominate)
        self.assertIn('不保证直接增加学识', nominate)


def original_confucian_world(rite_name='jingxue', active=False):
    """Synthetic untouched original Faith; no admission flag or fixture credit."""
    actor, npc, faith, old, globals_, env = world(detached=False, active=active)
    globals_['faith:lyd_common_faith'] = Scope('unused_legacy_faith')
    globals_['faith:confucian_faith'] = faith
    originals = {}
    for name in ('jingxue', 'daoxue'):
        rite = Scope(name, {'faith': faith,
                           'doctrines': {'doctrine_no_head', 'doctrine_theocracy_lay_clergy'},
                           'rite_counties': 0, 'allowed_gender': True})
        originals[name] = rite
        globals_['rite:' + name] = rite
        faith.fields['rites'].append(rite)
    chosen = originals[rite_name]
    faith.fields['main_rite'] = originals['jingxue']
    old.fields['rite_counties'] = 0
    chosen.fields['rite_counties'] = 1
    for member in (actor, npc):
        member.fields['rite'] = chosen
        member.fields['flags'] = set()
        if active:
            member.variables['lyd_i3b_member_rite'] = chosen
    actor.variables.update(lyd_i3b_actor_rite=chosen,
                           lyd_i3b_main=originals['jingxue'],
                           lyd_i3b_authority_mode=2,
                           lyd_i3b_result_authority_mode=2)
    if active:
        actor.lists['lyd_i3b_rites'] = faith.fields['rites'][:]
        for rite in faith.fields['rites']:
            live = rite is chosen
            rite.variables.update(lyd_i3b_owner=actor, lyd_i3b_serial=7,
                                  lyd_i3b_counties=int(live),
                                  lyd_i3b_dormant=int(not live),
                                  lyd_i3b_total=2 if live else 0,
                                  lyd_i3b_yes=2 if live else 0,
                                  lyd_i3b_signed=int(live))
            rite.variables.pop('lyd_i3b_delegate', None)
            if live:
                rite.variables['lyd_i3b_delegate'] = actor
    return actor, npc, faith, chosen, globals_, env


class OriginalConfucianInitiationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defs = Corpus().triggers
        InstitutionTooltipTests.setUpClass()
        cls.ui = InstitutionTooltipTests()

    def policy(self, state, trigger='lyd_i3b_can_begin_trigger'):
        return PolicyAST(self.defs, state[0], state[4], state[5].copy()).run(trigger)

    def test_untouched_jingxue_and_daoxue_can_begin_without_admission_or_learning15(self):
        for rite in ('jingxue', 'daoxue'):
            with self.subTest(rite=rite):
                state = original_confucian_world(rite)
                state[0].fields['learning'] = 5
                self.assertFalse(self.policy(state, 'lyd_c3_player_actor_trigger'))
                self.assertTrue(self.policy(state))
                decision = self.ui.decisions['lyd_i3b_begin_decision']
                engine = TooltipPolicy(self.defs, state[0], state[4], state[5].copy())
                self.assertTrue(engine.block(one(decision, 'is_shown'), state[0]))
                self.assertTrue(engine.block(one(decision, 'is_valid'), state[0]))

    def test_supported_mod_rite_on_original_faith_needs_no_admission_flag(self):
        state = world(detached=False, active=False)
        state[4]['faith:lyd_common_faith'] = Scope('unused_legacy_faith')
        state[4]['faith:confucian_faith'] = state[2]
        state[0].fields['flags'].clear()
        self.assertTrue(self.policy(state))

    def test_original_route_retains_player_duchy_gender_and_office_guards(self):
        changes = (
            ('AI', lambda a,n,f,r,g,e: a.fields.update(is_ai=True)),
            ('dead', lambda a,n,f,r,g,e: a.fields.update(is_alive=False)),
            ('child', lambda a,n,f,r,g,e: a.fields.update(is_adult=False)),
            ('unlanded', lambda a,n,f,r,g,e: a.fields.update(is_landed=False)),
            ('incapable', lambda a,n,f,r,g,e: a.fields['traits'].add('incapable')),
            ('count', lambda a,n,f,r,g,e: a.fields.update(highest_held_title_tier=2)),
            ('gender', lambda a,n,f,r,g,e: r.fields.update(allowed_gender=False)),
            ('office', lambda a,n,f,r,g,e: a.fields['held_titles'].append(Scope('other_head', {'is_head_of_faith': True}))),
            ('pending', lambda a,n,f,r,g,e: a.variables.update(lyd_c3_active=1)),
        )
        for name, change in changes:
            with self.subTest(reason=name):
                state = original_confucian_world()
                change(*state)
                self.assertFalse(self.policy(state))
                self.assertFalse(self.ui.visible_result('begin', state))

    def test_foreign_faith_unsupported_or_incompatible_rites_cannot_begin(self):
        changes = (
            ('foreign_faith', lambda a,n,f,r,g,e: g.update({'faith:confucian_faith': Scope('other_faith')})),
            ('wrong_religion', lambda a,n,f,r,g,e: a.fields.update(religion='religion:other')),
            ('unsupported_actor', lambda a,n,f,r,g,e: a.fields.update(rite=Scope('foreign_rite', {'faith': f, 'allowed_gender': True}))),
            ('foreign_rite_in_roster', lambda a,n,f,r,g,e: f.fields['rites'].append(Scope('foreign_rite', {'faith': f}))),
            ('incompatible_original', lambda a,n,f,r,g,e: r.fields['doctrines'].add('doctrine_spiritual_head')),
            ('existing_head', lambda a,n,f,r,g,e: f.fields.update(religious_head=n)),
            ('existing_challenger', lambda a,n,f,r,g,e: f.fields['challengers'].append(Scope('challenger', {'holder': n}))),
        )
        for name, change in changes:
            with self.subTest(reason=name):
                state = original_confucian_world()
                change(*state)
                self.assertFalse(self.policy(state))

    def test_legacy_and_detached_still_need_the_original_admission_and_authority(self):
        for detached in (False, True):
            state = world(detached=detached, active=False)
            self.assertTrue(self.policy(state))
            state[0].fields['flags'].clear()
            self.assertFalse(self.policy(state))
        state = world(detached=True, active=False)
        state[3].fields['head_of_rite'] = state[1]
        self.assertFalse(self.policy(state))

    def test_captured_mode2_keeps_exact_actor_rite_and_original_main(self):
        for rite in ('jingxue', 'daoxue'):
            state = original_confucian_world(rite, active=True)
            self.assertTrue(self.policy(state, 'lyd_i3b_current_trigger'))
            state[0].fields['rite'] = state[4]['rite:daoxue' if rite == 'jingxue' else 'rite:jingxue']
            self.assertFalse(self.policy(state, 'lyd_i3b_captured_authority_trigger'))
            self.assertFalse(self.policy(state, 'lyd_i3b_current_trigger'))
        state = original_confucian_world(active=True)
        state[2].fields['main_rite'] = state[4]['rite:daoxue']
        self.assertFalse(self.policy(state, 'lyd_i3b_current_trigger'))

    def test_original_route_still_requires_real_scholars_quorum_and_every_player_consent(self):
        for reason in ('no_scholars', 'no_delegate', 'quorum', 'human_consent', 'political_holder'):
            with self.subTest(reason=reason):
                state = original_confucian_world(active=True)
                self.assertTrue(self.policy(state, 'lyd_i3b_ready_trigger'))
                actor, npc, _, rite, _, _ = state
                if reason == 'no_scholars':
                    for member in (actor, npc):
                        member.fields['learning'] = 5
                        member.variables['lyd_i3b_was_elector'] = 0
                    rite.variables.update(lyd_i3b_total=0, lyd_i3b_yes=0)
                    rite.variables.pop('lyd_i3b_delegate')
                elif reason == 'no_delegate':
                    rite.variables.pop('lyd_i3b_delegate')
                elif reason == 'quorum':
                    rite.variables['lyd_i3b_yes'] = 1
                elif reason == 'human_consent':
                    actor.variables['lyd_i3b_player_yes'] = 0
                else:
                    actor.lists['lyd_i3b_political_titles'][0].fields['holder'] = npc
                self.assertFalse(self.policy(state, 'lyd_i3b_ready_trigger'))

    def test_full_trigger_delta_inverts_exactly_and_global_c3_is_unchanged(self):
        from test_c3_i3b_preview_scope import I3, BASELINE_AST_SHA256, strip_declared
        tree = parse_clausewitz(gen_institution.build_outputs()[I3].decode('utf-8-sig'))
        original = strip_declared(tree, I3)
        self.assertEqual(hashlib.sha256(repr(original).encode('utf-8')).hexdigest(),
                         BASELINE_AST_SHA256[I3])
        self.assertEqual(self.defs['lyd_c3_player_actor_trigger'], parse_clausewitz('''
            is_ai = no is_alive = yes is_adult = yes is_landed = yes
            NOT = { has_trait = incapable }
            religion = religion:confucianism_religion
            has_character_flag = lyd_enabled lyd_member_rite_trigger = yes
        '''))


class SupportPolicy(PolicyAST):
    """Evaluate generated chance predicates with directional NPC opinions."""
    def entry(self, entry, current):
        if entry.key == 'opinion':
            target = self.resolve(scalar(entry.value, 'target'), current)
            if target is None:
                raise AssertionError('Opinion read before candidate scope exists')
            comparison = next(e for e in entry.value.entries if e.key == 'value')
            value = current.fields['opinions'][target]
            threshold = int(comparison.value)
            return {'>=': value >= threshold, '<=': value <= threshold}[comparison.operator]
        return super().entry(entry, current)


class InstitutionSupportProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = gen_institution.build_outputs()
        cls.events = {e.key: e.value for e in parse_clausewitz(
            cls.outputs['events/lyd_i3b_institution_events.txt'].decode('utf-8-sig')).entries
            if isinstance(e.value, Block)}
        cls.terms = parse_clausewitz(cls.outputs[
            'common/scripted_effects/lyd_i3b_terms_effects.txt'].decode('utf-8-sig'))
        cls.defs = Corpus().triggers

    def chances(self, event_id):
        return {scalar(option, 'name'): one(option, 'ai_chance')
                for option in [e.value for e in self.events[f'lyd.{event_id}'].entries if e.key == 'option']
                if any(e.key == 'ai_chance' for e in option.entries)}

    def weight(self, chance, opinion=0, learning=15, npc_learning=15, missing_actor=False):
        actor = Scope('candidate', {'learning': learning, 'opinions': {}})
        npc = Scope('voter', {'learning': npc_learning, 'opinions': {actor: opinion}})
        actor.fields['opinions'][npc] = 100  # Reverse opinion must not matter.
        env = {} if missing_actor else {'scope:lyd_i3b_actor': actor}
        engine = SupportPolicy({}, npc, {}, env)
        result = float(scalar(chance, 'base'))
        for modifier in [e.value for e in chance.entries if e.key == 'modifier']:
            condition = Block(tuple(e for e in modifier.entries if e.key != 'factor'))
            if engine.block(condition, npc):
                result *= float(scalar(modifier, 'factor'))
        return result

    def test_three_npc_events_share_bounded_weights_and_human_choice_stays_unweighted(self):
        expected = None
        for event_id, yes_name in [(410, 'lyd_i3b_yes'), (411, 'lyd_i3b_yes'), (413, 'lyd_i3b_sign')]:
            choices = self.chances(event_id)
            pair = (choices[yes_name], choices['lyd_i3b_no'])
            if expected is not None:
                self.assertEqual(pair, expected)
            expected = pair
            self.assertEqual([len([e for e in c.entries if e.key == 'modifier']) for c in pair], [4, 4])
            self.assertEqual([self.weight(c) for c in pair], [60, 40])
        self.assertEqual(self.chances(412), {})
        self.assertEqual(self.weight(self.chances(413)['lyd_i3b_wait']), 0)

    def test_directional_opinion_thresholds_are_exact(self):
        chances = self.chances(411)
        for opinion, weights in [(-50, (30, 60)), (-49, (60, 40)), (49, (60, 40)), (50, (90, 30))]:
            with self.subTest(opinion=opinion):
                self.assertEqual(tuple(self.weight(chances[k], opinion) for k in ('lyd_i3b_yes', 'lyd_i3b_no')), weights)

    def test_learning_is_candidate_learning_with_exact_10_and_20_boundaries(self):
        chances = self.chances(411)
        for learning, weights in [(9, (48, 44)), (10, (60, 40)), (19, (60, 40)), (20, (75, 36))]:
            with self.subTest(learning=learning):
                self.assertEqual(tuple(self.weight(chances[k], learning=learning, npc_learning=100)
                                       for k in ('lyd_i3b_yes', 'lyd_i3b_no')), weights)

    def test_extreme_support_refusal_and_absent_scope_never_force_an_answer(self):
        yes, no = self.chances(411)['lyd_i3b_yes'], self.chances(411)['lyd_i3b_no']
        for opinion in (-100, -50, -49, 0, 49, 50, 100):
            for learning in (0, 9, 10, 19, 20, 100):
                y, n = self.weight(yes, opinion, learning), self.weight(no, opinion, learning)
                self.assertGreaterEqual(y, 24)
                self.assertLessEqual(y, 112.5)
                self.assertGreaterEqual(n, 27)
                self.assertLessEqual(n, 66)
        self.assertEqual(self.weight(yes, missing_actor=True), 60)
        self.assertEqual(self.weight(no, missing_actor=True), 40)

    def progress(self, state):
        actor, _, _, _, globals_, env = state
        engine = PolicyAST(self.defs, actor, globals_, env.copy())
        rows = []

        def execute(body, current):
            branch = None
            for entry in body.entries:
                key, value = entry.key, entry.value
                if key == 'variable':
                    continue
                if key == 'save_scope_as':
                    engine.env['scope:' + value] = current
                elif key == 'custom_tooltip':
                    rows.append((engine.env.get('scope:lyd_i3b_progress_rite'), value,
                                 engine.env.get('scope:lyd_i3b_progress_delegate')))
                elif key in {'if', 'else_if', 'else'}:
                    take = key == 'else' or engine.block(one(value, 'limit'), current)
                    if key != 'if':
                        take = not branch and take
                    branch = take if key == 'if' else branch or take
                    if take:
                        execute(Block(tuple(e for e in value.entries if e.key != 'limit')), current)
                elif key == 'every_in_list':
                    for item in current.lists.get(scalar(value, 'variable'), []):
                        execute(value, item)
                elif key == 'hidden_effect':
                    execute(value, current)
                else:
                    target = engine.resolve(key, current)
                    if not isinstance(target, Scope) or not isinstance(value, Block):
                        raise AssertionError('Unexpected state-changing or unknown progress operation: ' + key)
                    execute(value, target)
        execute(one(self.terms, 'lyd_i3b_show_terms_effect'), actor)
        return rows

    def test_progress_uses_actual_captured_counts_and_changes_no_round_state(self):
        state = original_confucian_world(active=True)
        actor, npc, faith, rite, _, _ = state
        rite.variables.update(lyd_i3b_yes=1, lyd_i3b_total=3, lyd_i3b_signed=0, lyd_i3b_delegate=npc)
        scopes = [actor, npc, faith] + faith.fields['rites']
        before = [(dict(s.variables), {k: list(v) for k, v in s.lists.items()}) for s in scopes]
        rows = self.progress(state)
        own = [(key, delegate) for r, key, delegate in rows if r is rite]
        self.assertIn(('lyd_i3b_progress_count_tt', None), own)
        self.assertIn(('lyd_i3b_progress_no_quorum_tt', None), own)
        self.assertIn(('lyd_i3b_progress_delegate_tt', npc), own)
        self.assertIn(('lyd_i3b_progress_unsigned_tt', npc), own)
        self.assertEqual(before, [(dict(s.variables), {k: list(v) for k, v in s.lists.items()}) for s in scopes])
        rite.variables.update(lyd_i3b_yes=2, lyd_i3b_signed=1)
        keys = {key for r, key, _ in self.progress(state) if r is rite}
        self.assertIn('lyd_i3b_progress_quorum_tt', keys)
        self.assertIn('lyd_i3b_progress_signed_tt', keys)

    def test_progress_missing_foreign_or_old_round_fields_are_unknown_not_zero(self):
        for change in (lambda a, r: r.variables.pop('lyd_i3b_yes'),
                       lambda a, r: r.variables.update(lyd_i3b_owner=Scope('foreign')),
                       lambda a, r: r.variables.update(lyd_i3b_serial=6),
                       lambda a, r: a.variables.pop('lyd_i3b_active')):
            state = original_confucian_world(active=True)
            change(state[0], state[3])
            own = [key for r, key, _ in self.progress(state) if r is state[3]]
            self.assertIn('lyd_i3b_progress_unknown_tt', own)
            self.assertNotIn('lyd_i3b_progress_count_tt', own)

    def test_zero_electors_no_delegate_and_dormant_are_distinct(self):
        state = original_confucian_world(active=True)
        rite = state[3]
        rite.variables.update(lyd_i3b_yes=0, lyd_i3b_total=0, lyd_i3b_signed=0)
        rite.variables.pop('lyd_i3b_delegate')
        keys = {key for r, key, _ in self.progress(state) if r is rite}
        self.assertIn('lyd_i3b_progress_no_quorum_tt', keys)
        self.assertIn('lyd_i3b_progress_no_delegate_tt', keys)
        self.assertIn('lyd_i3b_progress_unsigned_tt', keys)
        dormant = state[4]['rite:daoxue']
        keys = {key for r, key, _ in self.progress(state) if r is dormant}
        self.assertIn('lyd_i3b_progress_dormant_tt', keys)
        self.assertNotIn('lyd_i3b_progress_quorum_tt', keys)
        self.assertNotIn('lyd_i3b_progress_signed_tt', keys)

    def test_old_terms_callbacks_and_player_choices_survive_only_declared_additions(self):
        body = one(self.terms, 'lyd_i3b_show_terms_effect')
        self.assertEqual([e.key for e in body.entries], ['hidden_effect', 'custom_tooltip', 'custom_tooltip', 'every_in_list'])
        self.assertEqual(body.entries[0].value, parse_clausewitz('save_scope_as = lyd_i3b_progress_actor'))
        rites = body.entries[-1].value
        self.assertEqual(rites.entries[-3].value, parse_clausewitz('save_scope_as = lyd_i3b_progress_rite'))
        self.assertEqual([e.key for e in rites.entries[-2:]], ['if', 'else'])
        old_terms = Block((Entry('lyd_i3b_show_terms_effect', '=', Block((body.entries[1],
            Entry('every_in_list', '=', Block(rites.entries[:-3]))))),))
        self.assertEqual(hashlib.sha256(repr(old_terms).encode()).hexdigest(),
                         PREVIOUS_PRESENTATION_AST['common/scripted_effects/lyd_i3b_terms_effects.txt'])

        def strip_chances(body):
            entries = []
            for e in body.entries:
                if e.key == 'ai_chance':
                    value = Block(tuple(x for x in e.value.entries if x.key != 'modifier'))
                else:
                    value = strip_chances(e.value) if isinstance(e.value, Block) else e.value
                entries.append(Entry(e.key, e.operator, value))
            return Block(tuple(entries))
        events = parse_clausewitz(self.outputs['events/lyd_i3b_institution_events.txt'].decode('utf-8-sig'))
        self.assertEqual(hashlib.sha256(repr(strip_chances(events)).encode()).hexdigest(),
                         PREVIOUS_PRESENTATION_AST['events/lyd_i3b_institution_events.txt'])

    def test_progress_localization_reads_variables_and_explains_non_guaranteed_support(self):
        for language in ('simp_chinese', 'english'):
            loc = self.outputs[f'localization/{language}/lyd_i3b_institution_l_{language}.yml'].decode('utf-8-sig')
            for key in ('count', 'dormant', 'quorum', 'no_quorum', 'delegate', 'no_delegate', 'signed', 'unsigned', 'unknown'):
                self.assertEqual(loc.count(f' lyd_i3b_progress_{key}_tt:0 "'), 1)
            self.assertIn("lyd_i3b_progress_rite.MakeScope.Var('lyd_i3b_yes').GetValue|0", loc)
            self.assertIn("lyd_i3b_progress_rite.MakeScope.Var('lyd_i3b_total').GetValue|0", loc)
            self.assertIn('60/40' if language == 'english' else '60／40', loc)


if __name__ == '__main__':
    unittest.main()
