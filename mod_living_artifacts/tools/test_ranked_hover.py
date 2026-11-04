"""Current-tier display tests; do not award native hover/render qualification."""
from __future__ import annotations

import unittest

import living_artifacts_core as core
from living_artifacts_content import render_content_localization
from living_artifacts_display import current_rank_text, RANKED_NUMBERS
from test_core_generation import Script


class RankedHoverTests(unittest.TestCase):
    def test_current_values_keep_common_signs_decimals_and_fixed_numbers(self) -> None:
        for source, expected in (
            ('金币10/20/30，控制2/3/4，固定8压力', '金币#V 20#!，控制#V 3#!，固定8压力'),
            ('威望-15/30/45；恐怖+5/10/15', '威望#V -30#!；恐怖#V +10#!'),
            ('health -0.4/-0.8/-1.2, 365 days', 'health #V -0.8#!, 365 days'),
            ('santé -0,4/-0,8/-1,2, 12 mois', 'santé #V -0,8#!, 12 mois'),
            ('75/50/25% sie/er', '#V 50#!% sie/er'),
        ):
            with self.subTest(source=source):
                self.assertEqual(current_rank_text(source, 2), expected)
        self.assertEqual(current_rank_text('90/80/70%', 1), '#V 90#!%')
        self.assertEqual(current_rank_text('90/80/70%', 3), '#V 70#!%')

    def test_brief_entries_link_to_static_current_rank_descriptions(self) -> None:
        for language in ('simp_chinese', 'english'):
            values = {**core.render_core_localization(language), **render_content_localization(language)}
            line = values['xalw_affix_1_5_rank_2_line']
            self.assertIn('#TOOLTIP:xalw_affix_5_rank_2_desc', line)
            self.assertIn('#V 2#!', line)
            self.assertNotIn('10/20/30', line)
            self.assertNotIn('$xalw_affix_5_desc$', line)
            self.assertEqual(line.count('\\n'), 1)
            body = values['xalw_affix_5_rank_2_desc']
            self.assertIn('#V 20#!', body)
            self.assertIn('#V 3#!', body)
            self.assertNotIn('ROOT.', body)
            self.assertNotIn('MakeScope', body)
            self.assertIsNone(RANKED_NUMBERS.search(body))

    def test_real_selector_requires_both_matching_id_and_rank(self) -> None:
        script = Script(core.render_core_custom_localization())
        for kind, slot, item, rank in (('Affix', 1, 5, 2), ('Affix', 6, 12, 3), ('Curse', 2, 1, 1)):
            entries = script.children(script.named(f'Xalw{kind}{slot}'))
            selected = []
            for entry in entries:
                triggers = [child for child in script.children(entry) if child.key == 'trigger']
                if not triggers:
                    continue
                predicates = {value.key: value.value for value in script.scalars(triggers[0])}
                if predicates == {f'var:xalw_{kind.lower()}_{slot}': str(item), f'var:xalw_{kind.lower()}_rank_{slot}': str(rank)}:
                    selected.append(script.scalar(entry, 'localization_key').value)
            self.assertEqual(selected, [f'xalw_{kind.lower()}_{slot}_{item}_rank_{rank}_line'])

    def test_all_power_and_curse_tiers_have_materialized_hover_text(self) -> None:
        for language in ('simp_chinese', 'english'):
            values = render_content_localization(language)
            for kind, count in (('affix', 12), ('curse', 8)):
                for item in range(1, count + 1):
                    for rank in (1, 2, 3):
                        body = values[f'xalw_{kind}_{item}_rank_{rank}_desc']
                        self.assertIsNone(RANKED_NUMBERS.search(body), body)
                        self.assertNotIn('ROOT.', body)
                        self.assertIn(f'#V {rank}#!', body)


if __name__ == '__main__':
    unittest.main()
