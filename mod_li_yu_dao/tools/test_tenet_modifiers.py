"""Focused tenet strength, native scope and rendering contracts; no CK3 required."""
from dataclasses import replace
from decimal import Decimal
import codecs
import re
from pathlib import Path
import tempfile
import unittest

import content_data as data
import gen_content as generator
import validate_static as static


class TenetModifierTests(unittest.TestCase):
    def test_actual_installed_source_reader_checks_container_line_and_missing_files(self):
        with tempfile.TemporaryDirectory(prefix='lyd-native-modifier-source-') as name:
            game = Path(name)
            tenets = game / 'common/religion/tenet_types'
            tenets.mkdir(parents=True)
            base = tenets / '00_tenet_types.txt'
            base.write_text('tenet_example = {\n character_modifier = {\n  popular_opinion_add = 5\n }\n}\n', encoding='utf-8')
            (tenets / '00_pam_tenets.txt').write_text('# no duplicate examples\n', encoding='utf-8')
            formats = game / 'common/modifier_definition_formats/00_definitions.txt'
            formats.parent.mkdir(parents=True)
            formats.write_text('monthly_income_mult = { percent = yes }\n', encoding='utf-8')
            specs = {
                'popular_opinion_add': replace(data.MODIFIER_SPECS['popular_opinion_add'],
                    stock_scope_sources=(('character_modifier', '00_tenet_types.txt', 3),)),
                'monthly_income_mult': replace(data.MODIFIER_SPECS['monthly_income_mult'],
                    stock_scope_sources=(('personal_tenet_modifier', '00_definitions.txt', 1),)),
            }
            report = static.validate_installed_tenet_modifiers(game, specs, data.GENERIC_CHARACTER_FORMAT_REFERENCES)
            self.assertEqual(report['errors'], [])
            self.assertEqual(report['same_container_references'], 1)
            self.assertEqual(report['generic_format_references'], 1)
            self.assertEqual(report['runtime'], 'NOT_RUN')
            self.assertEqual(len(report['files']), 3)
            base.write_text(base.read_text().replace('character_modifier', 'county_modifier'), encoding='utf-8')
            self.assertTrue(static.validate_installed_tenet_modifiers(game, specs, data.GENERIC_CHARACTER_FORMAT_REFERENCES)['errors'])
            base.write_text('tenet_example = {\n character_modifier = {\n  popular_opinion_add = 5\n }\n}\n', encoding='utf-8')
            self.assertTrue(static.validate_installed_tenet_modifiers(game, specs, frozenset())['errors'])
            formats.unlink()
            self.assertTrue(static.validate_installed_tenet_modifiers(game, specs, data.GENERIC_CHARACTER_FORMAT_REFERENCES)['errors'])

    def test_all_36_offer_meaningful_distinct_ordinary_and_personal_specialties(self):
        data.validate_tenet_effects()
        self.assertEqual(set(data.TENET_EFFECTS), {f'T{i:02}' for i in range(1, 37)})
        for code, effects in data.TENET_EFFECTS.items():
            for scope in ('character_modifier', 'personal_tenet_modifier'):
                values = getattr(effects, scope)
                self.assertGreaterEqual(len(values), 2, (code, scope))
                # A faith-level skill point, 15% specialization, +3 points or
                # comparable scalar must remain; a token +1% cannot pass.
                thresholds = {
                    'percent': Decimal('.15'), 'percentage_points': Decimal('.15'),
                    'points': Decimal('3'), 'per_devotion_level': Decimal('1'),
                    'monthly_points': Decimal('.1'), 'health': Decimal('.15'),
                    'days': Decimal('10'), 'percentage_point_number': Decimal('5'),
                }
                self.assertTrue(any(
                    Decimal(v.value) * data.MODIFIER_SPECS[v.key].favorable_sign
                    >= thresholds[data.MODIFIER_SPECS[v.key].unit] for v in values),
                    (code, scope))

    def test_units_distinguish_percent_fertility_scheme_points_health_and_days(self):
        zh = generator.tenet_effects_text(data.TENETS_BY_CODE['T01'], 'simp_chinese')
        self.assertIn('每月虔诚获取 +20%', zh)
        self.assertIn('正统性 +0.15点/月', zh)
        cases = (
            ('T01', 'Legitimacy +0.15 points/month'),
            ('T13', 'Fertility +20 percentage points'),
            ('T13', 'Health +0.25 points'),
            ('T29', 'Enemy hostile scheme success chance -10 percentage points'),
            ('T14', 'Learning scheme phase duration -15 days'),
        )
        for code, expected in cases:
            self.assertIn(expected, generator.tenet_effects_text(data.TENETS_BY_CODE[code], 'english'))

    def test_builder_defender_scholar_and_economic_archetypes_are_distinct(self):
        ordinary = lambda code: {v.key: v.value for v in data.TENET_EFFECTS[code].character_modifier}
        personal = lambda code: {v.key: v.value for v in data.TENET_EFFECTS[code].personal_tenet_modifier}
        county = lambda code: {v.key: v.value for v in data.TENET_EFFECTS[code].county_modifier}
        self.assertEqual(ordinary('T19')['church_holding_build_gold_cost'], '-0.30')
        self.assertEqual(ordinary('T19')['church_holding_build_speed'], '-0.30')
        self.assertEqual(ordinary('T25')['knight_limit'], '2')
        self.assertEqual(ordinary('T25')['prowess'], '4')
        self.assertEqual(personal('T28')['controlled_province_advantage'], '5')
        self.assertEqual(county('T28')['monthly_control_change_at_war_mult'], '-0.25')
        self.assertEqual(personal('T26')['max_learn_language_schemes_add'], '1')
        self.assertEqual(personal('T27')['domain_limit'], '1')
        self.assertNotIn('domain_limit', personal('T26'))

    def test_each_modifier_has_current_source_with_explicit_format_continuities(self):
        for effects in data.TENET_EFFECTS.values():
            for scope in data.MODIFIER_SCOPES:
                for item in getattr(effects, scope):
                    rows = [row for row in data.MODIFIER_SPECS[item.key].stock_scope_sources if row[0] == scope]
                    self.assertEqual(len(rows), 1)
                    if rows[0][1] == '00_definitions.txt':
                        self.assertIn((item.key, scope), data.GENERIC_CHARACTER_FORMAT_REFERENCES)
                    else:
                        self.assertIn(rows[0][1], ('00_pam_tenets.txt', '00_tenet_types.txt'))
                    self.assertGreater(rows[0][2], 0)
        for key in ('invented_tenet_gain_mult', 'epidemic_resistance'):
            table = dict(data.TENET_EFFECTS)
            table['T01'] = replace(table['T01'], personal_tenet_modifier=(
                data.NativeModifier(key, '1'), data.NativeModifier('monthly_income_mult', '-0.03')))
            with self.assertRaisesRegex(ValueError, 'same-scope stock evidence'):
                data.validate_tenet_effects(table)

    def test_florin_migration_keeps_generic_character_modifiers_and_new_economic_names(self):
        script = generator.render_tenets()
        for old in ('county_opinion_add', 'tax_mult', 'development_growth_factor',
                    'monthly_county_control_growth_factor', 'monthly_county_control_decline_at_war_factor'):
            self.assertNotRegex(script, r'\b' + old + r'\s*=')
        for key in ('popular_opinion_add', 'all_tax_mult', 'prosperity_growth_factor',
                    'monthly_control_change_when_below_baseline_mult', 'monthly_control_change_at_war_mult',
                    'monthly_income_mult', 'domain_limit'):
            self.assertRegex(script, r'\b' + key + r'\s*=')
        actual = {(key, scope) for key, spec in data.MODIFIER_SPECS.items()
                  for scope, name, _ in spec.stock_scope_sources if name == '00_definitions.txt'}
        self.assertEqual(actual, data.GENERIC_CHARACTER_FORMAT_REFERENCES)
        self.assertEqual(actual, {('monthly_income_mult', 'personal_tenet_modifier'),
                                  ('domain_limit', 'character_modifier'),
                                  ('all_tax_mult', 'personal_tenet_modifier')})

    def test_cost_is_modest_per_package_and_not_forced_into_every_scope(self):
        # Ordinary T01 and every county T06 effect are beneficial; the personal
        # upkeep is sufficient. Requiring a county penalty would be artificial.
        data.validate_tenet_effects()
        table = dict(data.TENET_EFFECTS)
        table['T01'] = replace(table['T01'], personal_tenet_modifier=(
            data.NativeModifier('monthly_legitimacy_add', '0.15'),
            data.NativeModifier('monthly_income_mult', '0.03')))
        with self.assertRaisesRegex(ValueError, 'modest package cost'):
            data.validate_tenet_effects(table)
        table['T01'] = replace(table['T01'], personal_tenet_modifier=(
            data.NativeModifier('monthly_legitimacy_add', '0.15'),
            data.NativeModifier('monthly_income_mult', '-0.20')))
        with self.assertRaisesRegex(ValueError, 'tradeoff exceeds'):
            data.validate_tenet_effects(table)
        table['T01'] = replace(table['T01'], personal_tenet_modifier=(
            data.NativeModifier('monthly_income_mult', '-0.03'),))
        with self.assertRaisesRegex(ValueError, 'real benefit'):
            data.validate_tenet_effects(table)

    def test_missing_personal_numbers_bad_values_and_duplicate_keys_are_rejected(self):
        table = dict(data.TENET_EFFECTS)
        table['T01'] = replace(table['T01'], personal_tenet_modifier=())
        with self.assertRaisesRegex(ValueError, 'missing native personal_tenet_modifier'):
            data.validate_tenet_effects(table)
        for value in ('NaN', '1e-2', '0', '0.31', '0.20 } extra = {', 0.20):
            table['T01'] = replace(data.TENET_EFFECTS['T01'], character_modifier=(
                data.NativeModifier('monthly_piety_gain_mult', value),))
            with self.assertRaises(ValueError):
                data.validate_tenet_effects(table)
        table['T01'] = replace(data.TENET_EFFECTS['T01'], personal_tenet_modifier=(
            data.NativeModifier('monthly_income_mult', '0.15'),
            data.NativeModifier('monthly_income_mult', '-0.03')))
        with self.assertRaisesRegex(ValueError, 'duplicate modifier key'):
            data.validate_tenet_effects(table)
        table = dict(data.TENET_EFFECTS)
        table['T02'] = table['T01']
        with self.assertRaisesRegex(ValueError, 'identical complete modifier package'):
            data.validate_tenet_effects(table)

    def test_native_parameters_and_virtues_preserve_actual_consumer_scope(self):
        script = generator.render_tenets()
        self.assertEqual(script.count('\ttraits = {'), 36)
        self.assertEqual(script.count('weight = 15 scale = 1'), 108)
        self.assertEqual(script.count('meditation_mechanics_active'), 8)
        self.assertEqual(script.count('piety_from_gifts_active'), 3)
        self.assertEqual(script.count('literalist_debate_enabled'), 3)
        for effects in data.TENET_EFFECTS.values():
            self.assertTrue(set(effects.virtues).isdisjoint(effects.sins))
            self.assertNotIn('piety_from_gifts_active', effects.personal_parameters)
            self.assertNotIn('literalist_debate_enabled', effects.personal_parameters)
        table = dict(data.TENET_EFFECTS)
        table['T06'] = replace(table['T06'], personal_parameters=('piety_from_gifts_active',))
        with self.assertRaisesRegex(ValueError, 'matching consumer scope'):
            data.validate_tenet_effects(table)
        table['T06'] = replace(data.TENET_EFFECTS['T06'], sins=('compassionate',))
        with self.assertRaisesRegex(ValueError, 'contradictory native virtue/sin'):
            data.validate_tenet_effects(table)

    def test_generation_keeps_native_containers_bilingual_unlocks_and_utf8_bom(self):
        script = generator.render_tenets()
        self.assertEqual(len(re.findall(r'^lyd_tenet_[a-z_]+ = \{$', script, re.M)), 36)
        self.assertEqual(script.count('\tcharacter_modifier = {'), 36)
        self.assertEqual(script.count('\tpersonal_tenet_modifier = {'), 36)
        self.assertEqual(script.count('\tcounty_modifier = {'),
                         sum(bool(e.county_modifier) for e in data.TENET_EFFECTS.values()))
        for language, scope_text in (
            ('simp_chinese', '仅主动选为个人信条的可玩角色'),
            ('english', 'only playable characters choosing it personally'),
        ):
            entries = generator.localization_entries(language)
            for tenet in data.ACTIVE_TENETS:
                self.assertIn(scope_text, entries[tenet.script_id + '_desc'])
                self.assertIn(f'$lyd_play_{tenet.slug}_decision$',
                              entries['doctrine_parameter_' + tenet.parameter_id])
        outputs = generator.build_outputs()
        self.assertEqual(outputs, generator.build_outputs())
        self.assertTrue(all(raw.startswith(codecs.BOM_UTF8) for raw in outputs.values()))
        self.assertIn('monthly_legitimacy_add = 0.15', script)


if __name__ == '__main__':
    unittest.main(verbosity=2)
