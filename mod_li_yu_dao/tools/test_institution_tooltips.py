"""Granular institution requirements against actual generated policy ASTs.

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
    'common/scripted_triggers/lyd_i3b_institution_triggers.txt': 'ac31d6bd19b3d897f37a9229027cafe797d4ed43cce970355879da629464c286',
    'common/script_values/lyd_i3b_institution_values.txt': '61df8e591ac291644b103279d69665ed35f68c4f3aa63e286576583c8fae0156',
    'common/scripted_effects/lyd_i3b_terms_effects.txt': '00216b79ad3c3db91d9bc172f29e5a21982abf104ffc6862d3e2edf370562d8c',
    'common/scripted_effects/lyd_i3b_setup_effects.txt': 'fa913461b91dbd8a876dd4fac320c6f3d5a15222afd650b4fc68276e8cad03c7',
    'common/scripted_effects/lyd_i3b_response_effects.txt': 'cb5e9f9cc16cd6d12ffabf191e34490769bd1f6cc320dfdf0e0e3dde003b11e6',
    'common/scripted_effects/lyd_i3b_commit_effects.txt': 'dd327b875eb0c374937461a8d8cde8a384a994911260d9065fa2b51387a68d3c',
    'common/character_interactions/lyd_i3b_nomination_interactions.txt': '410ebb1a28542f160a9b45a49c017d15dacc39c375c4d358616301c577c2bb98',
    'events/lyd_i3b_institution_events.txt': '954219d1bfee6242d0135c7d4426202259e63f01989c22153cf19036bbfbe116',
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

    def visible_result(self, suffix, state):
        actor, _, _, _, globals_, env = state
        engine = TooltipPolicy(self.defs, actor, globals_, env.copy())
        visible = Block([e for e in self.validity(suffix).entries
                         if e.key != 'hidden_trigger'])
        return engine.block(visible, actor)

    def original_result(self, suffix, state):
        actor, _, _, _, globals_, env = state
        engine = PolicyAST(self.defs, actor, globals_, env.copy())
        return engine.block(one(self.validity(suffix), 'hidden_trigger'), actor)

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
                self.assertEqual(one(self.validity(suffix), 'hidden_trigger'), parse_clausewitz(gate))
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
        for path, digest in UNCHANGED_POLICY.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256(self.outputs[path]).hexdigest(), digest)
                self.assertEqual((SOURCE / path).read_bytes(), self.outputs[path])

    def test_requirements_are_separate_localized_and_generated(self):
        for suffix, count in [('begin', 25), ('nominate_self', 9)]:
            rows = self.rows(suffix)
            self.assertEqual(len(rows), count)
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


if __name__ == '__main__':
    unittest.main()
