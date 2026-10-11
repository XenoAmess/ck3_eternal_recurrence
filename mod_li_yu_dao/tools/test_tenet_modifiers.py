"""Focused numeric tenet contract; no installed CK3 or external B paths needed."""
from dataclasses import replace
from decimal import Decimal
import re
import unittest

import content_data as data
import gen_content as generator


class TenetModifierTests(unittest.TestCase):
    def test_all_36_have_distinct_native_personal_and_ordinary_tradeoffs(self):
        data.validate_tenet_effects()
        self.assertEqual(set(data.TENET_EFFECTS), {f'T{i:02}' for i in range(1, 37)})
        for effects in data.TENET_EFFECTS.values():
            self.assertGreaterEqual(len(effects.character_modifier), 2)
            self.assertGreaterEqual(len(effects.personal_tenet_modifier), 2)

    def test_units_do_not_confuse_multipliers_points_or_monthly_values(self):
        t1 = data.TENETS_BY_CODE['T01']
        zh = generator.tenet_effects_text(t1, 'simp_chinese')
        en = generator.tenet_effects_text(t1, 'english')
        self.assertIn('每月虔诚获取 +5%', zh)
        self.assertIn('正统性 +0.05点/月', zh)
        self.assertIn('Legitimacy +0.05 points/month', en)
        self.assertIn('Fertility +5 percentage points', generator.tenet_effects_text(data.TENETS_BY_CODE['T13'], 'english'))
        self.assertIn('Enemy hostile scheme success chance -3 percentage points', generator.tenet_effects_text(data.TENETS_BY_CODE['T29'], 'english'))

    def test_discount_and_control_tradeoffs_preserve_real_polarity(self):
        t19 = data.TENET_EFFECTS['T19']
        self.assertEqual({v.key: v.value for v in t19.character_modifier}, {
            'church_holding_build_gold_cost': '-0.05', 'church_holding_build_speed': '0.05'})
        t28 = generator.tenet_effects_text(data.TENETS_BY_CODE['T28'], 'simp_chinese')
        self.assertIn('每月控制力增长 +4%', t28)
        self.assertIn('赋税 -2%', t28)

    def test_personal_flag_alone_cannot_satisfy_real_personal_effect_requirement(self):
        table = dict(data.TENET_EFFECTS)
        table['T01'] = replace(table['T01'], personal_tenet_modifier=())
        with self.assertRaisesRegex(ValueError, 'missing native personal_tenet_modifier'):
            data.validate_tenet_effects(table)

    def test_unsupported_or_wrong_scope_modifier_is_rejected(self):
        for key in ('invented_tenet_gain_mult', 'county_opinion_add'):
            table = dict(data.TENET_EFFECTS)
            table['T01'] = replace(table['T01'], personal_tenet_modifier=(
                data.NativeModifier(key, '1'), data.NativeModifier('monthly_income_mult', '-0.02')))
            with self.assertRaisesRegex(ValueError, 'same-scope stock evidence'):
                data.validate_tenet_effects(table)

    def test_no_cost_or_duplicate_package_is_rejected(self):
        table = dict(data.TENET_EFFECTS)
        table['T01'] = replace(table['T01'], personal_tenet_modifier=(
            data.NativeModifier('monthly_legitimacy_add', '0.05'), data.NativeModifier('monthly_income_mult', '0.02')))
        with self.assertRaisesRegex(ValueError, 'both a benefit and a cost'):
            data.validate_tenet_effects(table)
        table = dict(data.TENET_EFFECTS)
        table['T02'] = table['T01']
        with self.assertRaisesRegex(ValueError, 'identical complete modifier package'):
            data.validate_tenet_effects(table)

    def test_bad_values_and_duplicate_keys_are_rejected(self):
        for value in ('NaN', '1e-2', '0', '0.11', '0.05 } extra = {', 0.05):
            table = dict(data.TENET_EFFECTS)
            table['T01'] = replace(table['T01'], character_modifier=(
                data.NativeModifier('monthly_piety_gain_mult', value), data.NativeModifier('stress_loss_mult', '-0.05')))
            with self.assertRaises(ValueError):
                data.validate_tenet_effects(table)
        table = dict(data.TENET_EFFECTS)
        table['T01'] = replace(table['T01'], personal_tenet_modifier=(
            data.NativeModifier('monthly_income_mult', '0.02'), data.NativeModifier('monthly_income_mult', '-0.01')))
        with self.assertRaisesRegex(ValueError, 'duplicate modifier key'):
            data.validate_tenet_effects(table)

    def test_generation_emits_actual_native_containers_and_bilingual_scope_text(self):
        script = generator.render_tenets()
        self.assertEqual(len(re.findall(r'^lyd_tenet_[a-z_]+ = \{$', script, re.M)), 36)
        self.assertEqual(script.count('\tcharacter_modifier = {'), 36)
        self.assertEqual(script.count('\tpersonal_tenet_modifier = {'), 36)
        self.assertEqual(script.count('\tcounty_modifier = {'), 13)
        for language, scope_text in [('simp_chinese', '仅主动选为个人信条的可玩角色'), ('english', 'only playable characters choosing it personally')]:
            entries = generator.localization_entries(language)
            for tenet in data.ACTIVE_TENETS:
                self.assertIn(scope_text, entries[tenet.script_id + '_desc'])
        # A scalar monthly legitimacy bonus must not be serialized as +5%.
        self.assertIn('monthly_legitimacy_add = 0.05', script)


if __name__ == '__main__':
    unittest.main(verbosity=2)
