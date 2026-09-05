#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Player-facing copy gates for the 40 workforce/endgame ruling cards."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_workforce_endgame_runtime as gen


PUNCTUATION_OPENERS = tuple("。！？，；：.!?,;:)]}）】》〉」』”’…")
CHINESE_TEMPLATE_TERMS = ("A/B", "路线甲", "路线乙", "业务对象", "案卷责任人", "按A", "按 A")
ENGLISH_TEMPLATE_TERMS = ("route A", "route B", "business object", "Case owner", "buttons")
FORBIDDEN_TECHNICAL_CN = ("回写", "本卡", "玩家", "结算器", "运行时纵切", "脚本")
FORBIDDEN_HANDOFF_TITLE_CN = ("PPT", "系统")
FORBIDDEN_HANDOFF_TITLE_EN = ("Slides", "System")


def literal_length(text: str) -> int:
    return len(re.sub(r"\[[^]]+]", "", text).strip())


class WorkforceEndgameCopyTest(unittest.TestCase):
    def test_all_forty_cards_have_unique_concrete_scenes(self) -> None:
        expected = set(gen.EXPECTED_MECHANISM_IDS)
        self.assertEqual(expected, set(gen.SCENE_CN))
        self.assertEqual(expected, set(gen.SCENE_EN))
        self.assertEqual(40, len(set(gen.SCENE_CN.values())))
        self.assertEqual(40, len(set(gen.SCENE_EN.values())))

    def test_bodies_open_with_prose_and_name_both_people(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                self.assertFalse(spec.desc_cn.startswith(("[", *PUNCTUATION_OPENERS)))
                self.assertFalse(spec.desc_en.startswith(("[", *PUNCTUATION_OPENERS)))
                for desc in (spec.desc_cn, spec.desc_en):
                    self.assertIn(f"[scope:{gen.PREFIX}_{spec.domain}_owner.GetShortUIName]", desc)
                    self.assertIn(f"[scope:{gen.PREFIX}_{spec.domain}_subject.GetShortUIName]", desc)

    def test_body_neither_repeats_title_nor_leaks_choices(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                self.assertNotIn(spec.title_cn, spec.desc_cn)
                self.assertNotIn(spec.title_en, spec.desc_en)
                for term in CHINESE_TEMPLATE_TERMS:
                    self.assertNotIn(term, spec.desc_cn)
                for term in ENGLISH_TEMPLATE_TERMS:
                    self.assertNotIn(term, spec.desc_en)
                for detail in spec.route_details_cn[:2]:
                    self.assertNotIn(detail, spec.desc_cn)
                for detail in spec.route_details_en[:2]:
                    self.assertNotIn(detail, spec.desc_en)

    def test_action_buttons_are_short_and_tooltips_keep_full_consequences(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                self.assertTrue(all(literal_length(label) <= 42 for label in spec.routes_cn))
                self.assertTrue(all(literal_length(label) <= 48 for label in spec.routes_en))
                self.assertIn("我", spec.routes_cn[2])
                self.assertIn("本局不再重提", spec.routes_cn[2])
                self.assertIn("制度债", spec.routes_cn[2])
                self.assertIn("I defer", spec.routes_en[2])
                self.assertIn("close it this reign", spec.routes_en[2])
                self.assertIn("policy debt", spec.routes_en[2])
                self.assertEqual(3, len(spec.route_details_cn))
                self.assertEqual(3, len(spec.route_details_en))
                self.assertTrue(all(detail.strip() for detail in spec.route_details_cn))
                self.assertTrue(all(detail.strip() for detail in spec.route_details_en))

    def test_simplified_chinese_uses_no_internal_technical_vocabulary(self) -> None:
        for spec in gen.MECHANISMS:
            fields = (spec.title_cn, spec.desc_cn, *spec.routes_cn, *spec.route_details_cn)
            for text in fields:
                for term in FORBIDDEN_TECHNICAL_CN:
                    with self.subTest(mid=spec.mid, term=term, text=text):
                        self.assertNotIn(term, text)

    def test_events_bind_one_tooltip_to_every_choice(self) -> None:
        events = gen.render_events().decode("utf-8-sig")
        for spec in gen.MECHANISMS:
            for letter in "abc":
                with self.subTest(mid=spec.mid, letter=letter):
                    self.assertEqual(
                        1,
                        events.count(f"custom_tooltip = {gen.NAMESPACE}.{spec.mid}.{letter}.tt"),
                    )

    def test_generated_localization_has_labels_and_tooltips_in_both_languages(self) -> None:
        for language in ("simp_chinese", "english"):
            text = gen.render_localization(language).decode("utf-8-sig")
            for spec in gen.MECHANISMS:
                self.assertIn(f" {gen.NAMESPACE}.{spec.mid}.desc:0", text)
                for letter in "abc":
                    self.assertIn(f" {gen.NAMESPACE}.{spec.mid}.{letter}:0", text)
                    self.assertIn(f" {gen.NAMESPACE}.{spec.mid}.{letter}.tt:0", text)

    def test_third_handoff_title_is_world_facing(self) -> None:
        chinese = gen.render_localization("simp_chinese").decode("utf-8-sig")
        english = gen.render_localization("english").decode("utf-8-sig")
        chinese_title = re.search(
            r'^ zg361we\.handoff\.3\.t:0 "(.*)"$', chinese, re.MULTILINE
        ).group(1)
        english_title = re.search(
            r'^ zg361we\.handoff\.3\.t:0 "(.*)"$', english, re.MULTILINE
        ).group(1)
        self.assertEqual("交接第三关：纸上谈兵不算实作", chinese_title)
        self.assertEqual("Handoff III: A Written Brief Is Not Practice", english_title)
        for term in FORBIDDEN_HANDOFF_TITLE_CN:
            self.assertNotIn(term, chinese_title)
        for term in FORBIDDEN_HANDOFF_TITLE_EN:
            self.assertNotIn(term, english_title)


if __name__ == "__main__":
    unittest.main()
