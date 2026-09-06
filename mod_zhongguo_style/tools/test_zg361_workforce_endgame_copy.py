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
FORBIDDEN_TECHNICAL_CN = (
    "回写", "本卡", "玩家", "结算器", "运行时纵切", "脚本", "背 C", "旧 3.25",
)
FORBIDDEN_HANDOFF_TITLE_CN = ("PPT", "系统")
FORBIDDEN_HANDOFF_TITLE_EN = ("Slides", "System")


def literal_length(text: str) -> int:
    return len(re.sub(r"\[[^]]+]", "", text).strip())


def localization_rows(language: str) -> dict[str, str]:
    text = gen.render_localization(language).decode("utf-8-sig")
    return {
        match.group(1): match.group(2)
        for row in text.splitlines()[1:]
        if (match := re.match(r'^ ([^:]+):0 "(.*)"$', row)) is not None
    }


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
                    owner = f"{gen.PREFIX}_{spec.domain}_owner"
                    subject = f"{gen.PREFIX}_{spec.domain}_subject"
                    self.assertIn(f"[{owner}.GetShortUIName]", desc)
                    self.assertIn(f"[{subject}.GetShortUIName]", desc)
                    self.assertNotIn(f"[scope:{owner}.GetShortUIName]", desc)
                    self.assertNotIn(f"[scope:{subject}.GetShortUIName]", desc)

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
            visible_letters = "a" if spec.mid == 274 else "abc"
            for letter in visible_letters:
                with self.subTest(mid=spec.mid, letter=letter):
                    self.assertEqual(
                        1,
                        events.count(f"custom_tooltip = {gen.NAMESPACE}.{spec.mid}.{letter}.tt"),
                    )
            if spec.mid == 274:
                self.assertNotIn(f"custom_tooltip = {gen.NAMESPACE}.274.b.tt", events)
                self.assertNotIn(f"custom_tooltip = {gen.NAMESPACE}.274.c.tt", events)

    def test_generated_localization_has_labels_and_tooltips_in_both_languages(self) -> None:
        for language in ("simp_chinese", "english"):
            text = gen.render_localization(language).decode("utf-8-sig")
            for spec in gen.MECHANISMS:
                self.assertIn(f" {gen.NAMESPACE}.{spec.mid}.desc:0", text)
                for letter in "abc":
                    self.assertIn(f" {gen.NAMESPACE}.{spec.mid}.{letter}:0", text)
                    self.assertIn(f" {gen.NAMESPACE}.{spec.mid}.{letter}.tt:0", text)

    def test_audited_tooltips_state_only_real_consequences(self) -> None:
        rows = localization_rows("simp_chinese")
        expected_tokens = {
            "zg361we.244.a.tt": ("5 日工时", "10 金币"),
            "zg361we.247.b.tt": ("一年", "不设中途复盘"),
            "zg361we.254.a.tt": ("缩减目标", "20 金币", "下一周期到期"),
            "zg361we.254.b.tt": ("维持原目标", "绕过正式编制审查", "下一周期到期"),
            "zg361we.255.a.tt": ("混合方案", "全周期成本 100"),
            "zg361we.257.a.tt": ("公开统一门槛", "下一周期再完成转正"),
            "zg361we.257.b.tt": ("经理提名", "下一周期再完成转正"),
            "zg361we.259.b.tt": ("供应商合同账", "不处分甲方一线人员"),
            "zg361we.262.b.tt": ("接收方单独定档", "借出方不记功"),
            "zg361we.267.b.tt": ("支付此前预留的 5 金币内推奖",),
            "zg361we.271.b.tt": ("预留 5 金币", "封票时才支付"),
            "zg361we.274.a.tt": ("候选已接受", "共支付 15 金币", "正式名额转为在岗"),
            "zg361we.276.b.tt": ("旧绩效档位", "完整保留"),
            "zg361we.277.b.tt": ("名额仍转入冻结", "不会增加可招聘名额或立即招人"),
            "zg361we.355.a.tt": ("新目标定为 120", "预留 10 金币", "下一周期"),
            "zg361we.356.b.tt": ("申报顺延一轮", "真实完成周期", "撤销重复信用"),
            "zg361we.361.a.tt": ("支付 5 金币", "10 治理工时"),
            "zg361we.361.b.tt": ("支付 10 金币", "10 治理工时"),
        }
        for key, tokens in expected_tokens.items():
            with self.subTest(key=key):
                for token in tokens:
                    self.assertIn(token, rows[key])
        self.assertNotIn("无限期", rows["zg361we.247.b.tt"])
        self.assertNotIn("清除", rows["zg361we.276.b.tt"])
        self.assertNotIn("自动补岗", rows["zg361we.277.b.tt"])
        self.assertNotIn("抬高下一轮目标", rows["zg361we.356.b.tt"])

    def test_audited_subject_roles_and_handoff_evidence_are_explicit(self) -> None:
        rows = localization_rows("simp_chinese")
        role_tokens = {
            254: "外包人员 [zg361_we_ac_subject.GetShortUIName]",
            256: "外部执行者 [zg361_we_ac_subject.GetShortUIName]",
            257: "外部成员 [zg361_we_ac_subject.GetShortUIName]",
            261: "实际执行者 [zg361_we_ac_subject.GetShortUIName]",
            264: "供应商 [zg361_we_ac_subject.GetShortUIName]",
            266: "候选人 [zg361_we_ad_subject.GetShortUIName]",
        }
        for mid, token in role_tokens.items():
            self.assertIn(token, rows[f"zg361we.{mid}.desc"])
        self.assertIn("案头文书尚待核验", rows["zg361we.handoff.1.owner.desc"])
        self.assertIn("案卷尚未确认", rows["zg361we.handoff.3.owner.desc"])

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

    def test_every_visible_body_passes_the_same_literal_review(self) -> None:
        rows = localization_rows("simp_chinese")
        main_bodies = {f"zg361we.{mid}.desc" for mid in gen.EXPECTED_MECHANISM_IDS}
        handoff_bodies = {
            f"zg361we.handoff.{step}.{viewer}.desc"
            for step in (1, 2, 3)
            for viewer in ("subject", "owner")
        }
        body_keys = main_bodies | handoff_bodies
        self.assertEqual(46, len(body_keys))
        self.assertTrue(body_keys.issubset(rows))
        self.assertEqual(46, len({rows[key] for key in body_keys}))
        for key in sorted(body_keys):
            body = rows[key].lstrip()
            with self.subTest(key=key):
                self.assertTrue(body)
                self.assertFalse(body.startswith(("[", *PUNCTUATION_OPENERS)))
                for term in CHINESE_TEMPLATE_TERMS:
                    self.assertNotIn(term, body)
        for step in (1, 2, 3):
            title = rows[f"zg361we.handoff.{step}.t"]
            for viewer in ("subject", "owner"):
                self.assertNotIn(title, rows[f"zg361we.handoff.{step}.{viewer}.desc"])

    def test_every_visible_button_names_an_action_outside_the_body(self) -> None:
        rows = localization_rows("simp_chinese")
        main_buttons = {
            f"zg361we.{mid}.{letter}"
            for mid in gen.EXPECTED_MECHANISM_IDS
            for letter in "abc"
        }
        handoff_buttons = {
            f"zg361we.handoff.{step}.{viewer}.{outcome}"
            for step in (1, 2, 3)
            for viewer in ("subject", "owner")
            for outcome in ("complete", "refuse")
        }
        button_keys = main_buttons | handoff_buttons
        self.assertEqual(132, len(button_keys))
        self.assertTrue(button_keys.issubset(rows))
        for key in sorted(button_keys):
            label = rows[key]
            with self.subTest(key=key):
                self.assertTrue(label.strip())
                self.assertLessEqual(literal_length(label), 42)
                self.assertNotRegex(label, r"(?:路线[甲乙ABC]|按\s*[ABC]\s*(?:做|办|执行)?)")
        for mid in gen.EXPECTED_MECHANISM_IDS:
            body = rows[f"zg361we.{mid}.desc"]
            for letter in "abc":
                label = rows[f"zg361we.{mid}.{letter}"]
                if len(label) >= 6:
                    self.assertNotIn(label, body, (mid, letter))
        for step in (1, 2, 3):
            bodies = " ".join(
                rows[f"zg361we.handoff.{step}.{viewer}.desc"]
                for viewer in ("subject", "owner")
            )
            for viewer in ("subject", "owner"):
                for outcome in ("complete", "refuse"):
                    label = rows[f"zg361we.handoff.{step}.{viewer}.{outcome}"]
                    self.assertNotIn(label, bodies, (step, viewer, outcome))

    def test_final_chinese_projection_contains_no_reviewed_technical_shortcuts(self) -> None:
        rows = localization_rows("simp_chinese")
        forbidden = (*FORBIDDEN_TECHNICAL_CN, "PPT", "群里", "知识库", "@")
        for key, value in rows.items():
            for term in forbidden:
                with self.subTest(key=key, term=term):
                    self.assertNotIn(term, value)

    def test_defer_tooltips_never_wrap_titles_with_nested_quotes(self) -> None:
        chinese = localization_rows("simp_chinese")
        english = localization_rows("english")
        for mid in gen.EXPECTED_MECHANISM_IDS:
            cn = chinese[f"zg361we.{mid}.c.tt"]
            en = english[f"zg361we.{mid}.c.tt"]
            with self.subTest(mid=mid):
                self.assertTrue(cn.startswith("这项裁决保持未决："))
                self.assertTrue(en.startswith("This ruling remains unresolved."))
                self.assertNotIn(gen.by_id()[mid].title_cn, cn)
                self.assertNotIn(gen.by_id()[mid].title_en, en)
                self.assertNotIn("““", cn)
                self.assertNotIn("””", cn)
        for mid in (244, 273, 360):
            self.assertNotRegex(chinese[f"zg361we.{mid}.c.tt"], r"[“”][^“”]*[“”][^“”]*[“”]")

    def test_overtime_card_names_only_the_two_executable_settlements(self) -> None:
        chinese = localization_rows("simp_chinese")
        english = localization_rows("english")
        self.assertEqual("额外工时如何兑现", chinese["zg361we.246.t"])
        self.assertEqual("支付 15 金币结清五日工时", chinese["zg361we.246.a"])
        self.assertEqual("记入 5 日未来调休", chinese["zg361we.246.b"])
        self.assertNotIn("目标减免", chinese["zg361we.246.desc"])
        self.assertNotIn("三选一", chinese["zg361we.246.a.tt"])
        self.assertEqual("How Extra Hours Are Settled", english["zg361we.246.t"])

        route_a = gen.render_route_effect(gen.by_id()[246], 1)
        route_b = gen.render_route_effect(gen.by_id()[246], 2)
        self.assertIn("remove_short_term_gold = 15", route_a)
        self.assertIn("m246_compensation_route value = 1", route_a)
        self.assertIn("m246_compensation_route value = 2", route_b)
        self.assertIn("leave_bank add = 5", route_b)

    def test_contract_type_card_buttons_match_each_executable_effect(self) -> None:
        chinese = localization_rows("simp_chinese")
        english = localization_rows("english")

        self.assertEqual(
            "锁定补位合同类型、责任归属与变更规则",
            chinese["zg361we.260.a"],
        )
        self.assertEqual(
            "沿用补位合同类型，不冻结责任与变更规则",
            chinese["zg361we.260.b"],
        )
        self.assertIn("立即冻结合同类型、责任归属与变更规则", chinese["zg361we.260.a.tt"])
        self.assertIn("不冻结责任归属与变更规则", chinese["zg361we.260.b.tt"])
        self.assertEqual(
            "Lock contract type, ownership, and change rules",
            english["zg361we.260.a"],
        )
        self.assertEqual(
            "Keep contract type; leave ownership/change open",
            english["zg361we.260.b"],
        )

        spec = gen.by_id()[260]
        route_a = gen.render_route_effect(spec, 1)
        route_b = gen.render_route_effect(spec, 2)
        route_c = gen.render_route_effect(spec, 3)
        inherited_type = (
            "set_variable = { name = zg361_we_m260_contract_type "
            "value = var:zg361_we_m254_contract_type }"
        )
        self.assertIn(inherited_type, route_a)
        self.assertIn("m260_ownership_frozen value = 1", route_a)
        self.assertIn("m260_change_rule_frozen value = 1", route_a)
        self.assertIn(inherited_type, route_b)
        self.assertIn("m260_ownership_frozen value = 0", route_b)
        self.assertIn("m260_change_rule_frozen value = 0", route_b)
        self.assertNotIn(inherited_type, route_c)
        self.assertIn("m260_debt_open value = 1", route_c)
        self.assertIn("m260_debt_due_cycle", route_c)


if __name__ == "__main__":
    unittest.main()
