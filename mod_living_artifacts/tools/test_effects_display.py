"""Regress the reported sparse-slot gap and missing ordinary artifact effects.

These tests resolve generated display strings against fixtures. They do not
claim CK3 rendering, save loading, or runtime gameplay qualification.
"""
from __future__ import annotations

from pathlib import Path
import re
import tempfile
import unittest

import living_artifacts_core as core
from generate import apply_source_patches
from test_core_generation import Script


def resolve_summary(values: dict[str, str], powers: dict[int, int], curses: dict[int, int]) -> str:
    def expand(value: str) -> str:
        value = re.sub(r"\$([^$]+)\$", lambda m: expand(values[m[1]]), value)
        def slot(match: re.Match[str]) -> str:
            kind, number = match[1].lower(), int(match[2])
            chosen = (powers if kind == "affix" else curses).get(number)
            return expand(values[f"xalw_{kind}_{number}_{chosen}_line"]) if chosen else ""
        value = re.sub(r"\[ROOT.Artifact.Custom\('Xalw(Affix|Curse)([1-6])'\)\]", slot, value)
        value = re.sub(r"\[ROOT.Artifact.MakeScope.Var\('xalw_(?:affix|curse)_rank_[1-6]'\).GetValue\|0\]", "2", value)
        return value.replace("\\n", "\n")
    return expand(values["xalw_effects_summary"])


class EffectsDisplayTests(unittest.TestCase):
    def test_sparse_slots_do_not_reserve_empty_rows(self) -> None:
        for language in ("simp_chinese", "english"):
            values = core.render_core_localization(language)
            from living_artifacts_content import render_content_localization
            values.update(render_content_localization(language))
            for powers, curses in (({}, {}), ({1: 5}, {1: 1}), ({6: 12}, {2: 8}),
                                    ({1: 1, 3: 5, 6: 12}, {2: 8}),
                                    ({i: i for i in range(1, 7)}, {1: 1, 2: 2})):
                with self.subTest(language=language, powers=powers, curses=curses):
                    text = resolve_summary(values, powers, curses)
                    self.assertNotIn("\n\n", text)
                    self.assertEqual(text.count("\n"), 2 * (len(powers) + len(curses)))
                    self.assertNotIn("ROOT.", text)
                    for number in powers.values():
                        self.assertIn(values[f"xalw_affix_{number}_name"], text)
                    for number in curses.values():
                        self.assertIn(values[f"xalw_curse_{number}_name"], text)
                    self.assertNotIn("')]\\n[xalw_artifact.Custom('XalwCurses')", values['xalw.10.desc'])

    def test_effects_summary_is_living_only_and_empty_for_ordinary_items(self) -> None:
        script = Script(core.render_core_custom_localization())
        effect = script.named('XalwEffects')
        entries = script.children(effect)
        self.assertEqual(len(entries), 2)
        self.assertEqual(script.scalar(script.child(entries[0], 'trigger'), 'xalw_is_living_trigger').value, 'yes')
        self.assertEqual(script.scalar(entries[1], 'fallback').value, 'yes')
        self.assertEqual(script.scalar(entries[1], 'localization_key').value, 'xalw_effects_empty')
        self.assertEqual(core.render_core_localization('simp_chinese')['xalw_effects_empty'], '')

    def test_details_projection_preserves_numeric_effects_and_rejects_other_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            patches = core.get_core_patches(game)
            self.assertEqual(len(patches), 1)
            before, after = patches[0].replacements[0]
            self.assertIn('[Artifact.GetModifierEffects]', after)
            self.assertIn("[Artifact.Custom('XalwEffects')]", after)
            self.assertEqual(after.replace("[Artifact.Custom('XalwEffects')]", ''), before)
            path = game / patches[0].relative_path
            path.parent.mkdir(parents=True)
            path.write_text(before, encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'SHA-256 changed'):
                apply_source_patches(game, patches)


if __name__ == '__main__':
    unittest.main()
