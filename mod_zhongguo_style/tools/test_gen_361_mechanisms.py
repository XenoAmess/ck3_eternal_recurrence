#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 tests for the complete 361 mechanism projection."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

from gen_361_mechanisms import (
    FULL_LEDGER_TOOLTIP_MECHANISM_IDS,
    MOD_ROOT,
    LEDGER_ONLY_MECHANISM_IDS,
    choice_button_cn,
    choice_button_en,
    effect_name,
    full_ledger_changes_cn,
    full_ledger_changes_en,
    localization_values,
    naturalize_mechanism_chinese,
    outputs,
    principal_ledger_changes_cn,
)
from zg361_mechanism_data import (
    ACCEPTANCE_FIELDS,
    AcceptanceContract,
    LEDGERS,
    MECHANISM_COUNT,
    PROFILE_DELTAS,
    load_acceptance_contracts,
    load_mechanisms,
    mechanism_deltas,
)
from zg361_phase2_runtime_data import PHASE2_RUNTIME_SPECS
from zg361_localization_style import normalize_player_chinese
from zg361_readiness_data import (
    CUMULATIVE_COUNTS,
    READINESS_BY_ID,
    ReadinessLevel,
    ids_at_least,
)


def valid_acceptance_payload(mechanism_id: int) -> dict[str, object]:
    return {
        "acceptance_cn": f"机制 {mechanism_id:03d} 必须冻结具体案卷并核对结果。",
        "semantic_family": f"family_{mechanism_id:03d}",
        "required_state": [f"case_{mechanism_id:03d}_id 与 review_serial"],
        "visible_feedback": [f"显示机制 {mechanism_id:03d} 的具体案卷结果"],
        "batch_assertions": [f"机制 {mechanism_id:03d} 的案卷只结算一次"],
    }


class MechanismGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mechanisms = load_mechanisms(MOD_ROOT)
        cls.rendered = outputs(cls.mechanisms)
        cls.effects = "\n".join(
            payload.decode("utf-8-sig")
            for path, payload in sorted(cls.rendered.items())
            if path.parent == MOD_ROOT / "common" / "scripted_effects"
            and path.name.startswith("zg361_generated_mechanism_")
            and path.name.endswith("_effects.txt")
        )

    def test_exact_catalogue(self) -> None:
        self.assertEqual(len(self.mechanisms), MECHANISM_COUNT)
        self.assertEqual([item.id for item in self.mechanisms], list(range(1, 362)))
        self.assertEqual(len({item.title_cn for item in self.mechanisms}), 361)
        self.assertEqual(len({item.title_en for item in self.mechanisms}), 361)

    def test_every_choice_is_reviewed_and_specific(self) -> None:
        generic = {
            "Adopt the evidence-led policy",
            "Prioritize the short-term result",
        }
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertNotIn(mechanism.option_a_en, generic)
                self.assertNotIn(mechanism.option_b_en, generic)
                self.assertNotEqual(mechanism.option_a_cn, mechanism.option_b_cn)
                self.assertNotEqual(mechanism.option_a_en, mechanism.option_b_en)
                self.assertIn(mechanism.profile, PROFILE_DELTAS)
                self.assertIn(mechanism.reference_choice, {"a", "b", "c"})

    def test_audit_007_008_copy_closures_are_projected(self) -> None:
        chinese = localization_values(self.mechanisms, "simp_chinese")
        expected = {
            "zg361m.74.desc": "只冻结今后裁撤个案的处理政策",
            "zg361m.74.a": "确立公开裁撤政策",
            "zg361m.74.b": "确立洗低成绩裁撤政策",
            "zg361m.75.desc": "只冻结今后自愿离开个案的处理政策",
            "zg361m.75.a": "确立自愿离开政策",
            "zg361m.75.b": "确立强硬离开政策",
            "zg361m.76.b.tt": "人事复核官",
            "zg361m.79.desc": "隔级下属的档位",
            "zg361m.84.desc": "尚未归属的奖金形成离职即损失的束缚",
            "zg361m.85.b.tt": "临时加价挽留",
            "zg361m.87.t": "薪酬区间与区间内位置",
            "zg361m.87.a.tt": "区间内位置",
            "zg361m.87.b.tt": "不超过区间上限",
            "zg361m.92.b.tt": "造成管理失当",
            "zg361m.93.desc": "取消保护并全额降职降俸",
            "zg361m.93.b": "一律撤权并全额降职降俸",
            "zg361m.94.a.tt": "薪酬区间",
            "zg361m.97.desc": "未获通过的晋升提名",
            "zg361m.99.b.tt": "年度编制使用率",
            "zg361m.100.a": "书面特批有据可查的关键岗位",
            "zg361m.101.desc": "一个编制名额不等于简单增添一名人手",
            "zg361m.104.b.tt": "集中招募可立即履职的成熟人才",
            "zg361m.107.b.tt": "钦定一名接班人",
            "zg361m.110.b.tt": "仅凭一句“高潜”评价",
            "zg361m.111.desc": "离任者日后取得高成就",
            "zg361m.112.t": "留任访谈",
            "zg361m.112.desc": "未兑现承诺形成可见债务",
            "zg361m.112.b.tt": "紧急挽留条件",
            "zg361m.114.t": "经理育才功绩",
            "zg361m.114.a.tt": "育才功绩、补岗优先与跨团队信誉",
            "zg361m.114.b.tt": "损害育才功绩与跨团队信誉",
            "zg361m.115.desc": "申请本身不会立即调动人选或授予头衔",
            "zg361m.119.a": "按结果追记招聘各环节表现",
            "zg361m.121.desc": "不必直接断送仕途",
            "zg361m.121.a.tt": "试管一个小团队一周期",
            "zg361m.122.b.tt": "硬结果的权重提高到过半",
            "zg361m.124.desc": "尚无成熟继任者的优秀经理会长期无法升任",
            "zg361m.126.desc": "低产但顺从者会拖累结果",
            "zg361m.129.desc": "重复提交晋升申请",
            "zg361m.132.desc": "项目发起人或担保人的信任",
            "zg361m.132.a.tt": "项目发起人或担保人复核",
            "zg361m.133.desc": "公开追责会",
            "zg361m.135.desc": "虚假的乐观预期",
            "zg361m.136.a.tt": "不提前分完全部档位名额",
            "zg361m.138.a.tt": "余下名额依小数余数大小分配",
            "zg361m.139.desc": "从下一轮预借一个档位名额",
            "zg361m.139.a.tt": "换负责人、重组或解散均不免批准经理的债",
            "zg361m.140.desc": "原团队与新团队",
            "zg361m.140.a.tt": "在校准会议发起时冻结",
            "zg361m.141.t": "高层保荐与否决名单",
            "zg361m.141.desc": "不能直接改档",
            "zg361m.141.a": "书面复议建议",
            "zg361m.141.b": "直接干预隔级下属的档位",
            "zg361m.143.t": "截止后重大事件的对称处理",
            "zg361m.143.desc": "重大成功与重大事故必须使用同一门槛",
            "zg361m.145.t": "同档内的影子排序",
            "zg361m.145.desc": "同属 3.5 档的人",
            "zg361m.145.a": "培养排序",
            "zg361m.145.b": "同档人员排出优先与末位",
            "zg361m.150.b": "口头保证下轮补回 3.75 档",
        }
        for key, fragment in expected.items():
            with self.subTest(key=key):
                self.assertIn(fragment, chinese[key])

        audited_ids = {
            74, 75, 76, 79, 84, 85, 87, 92, 93, 94, 97, 99, 100,
            101, 104, 107, 110, 111, 112, 114, 115, 119, 121, 122,
            124, 126, 129, 132, 133, 135, 136, 138, 139, 140, 141,
            143, 145, 150,
        }
        audited_copy = "\n".join(
            chinese[f"zg361m.{mechanism_id}.{suffix}"]
            for mechanism_id in audited_ids
            for suffix in ("t", "desc", "a", "a.tt", "b", "b.tt")
        )
        for stale_phrase in (
            "反 offer", "薪酬带宽", "带顶", "制造坏管理", "失败提包",
            "多生成一个角色", "集中购买", "一位太子", "一句高潜",
            "事后出现高成就", "Stay Interview", "饼债", "瞬移角色",
            "职业死亡", "养兔子", "纵容野狗", "自杀式降档", "批斗会",
            "孙级", "召集令", "欠债换老板", "保送", "必杀", "红线",
            "三档之内", "B 加减序列",
        ):
            with self.subTest(stale_phrase=stale_phrase):
                self.assertNotIn(stale_phrase, audited_copy)

        english = localization_values(self.mechanisms, "english")
        french_placeholder = localization_values(self.mechanisms, "french")
        self.assertIn("only freezes the policy", english["zg361m.74.desc"])
        self.assertIn("cannot alter it directly", english["zg361m.141.desc"])
        self.assertEqual(
            french_placeholder["zg361m.141.desc"],
            english["zg361m.141.desc"],
        )
        for mechanism_id in range(72, 152):
            for choice in ("a", "b"):
                key = f"zg361m.{mechanism_id}.{choice}"
                with self.subTest(key=key, issue="truncated-action"):
                    self.assertNotIn("…", chinese[key])
        self.assertNotIn("保护老员，", chinese["zg361m.118.b.tt"])

    def test_acceptance_contracts_are_typed_complete_and_specific(self) -> None:
        for mechanism in self.mechanisms:
            contract = mechanism.acceptance_contract
            with self.subTest(mechanism=mechanism.id):
                self.assertIsInstance(contract, AcceptanceContract)
                self.assertTrue(contract.acceptance_cn)
                self.assertTrue(contract.semantic_family)
                self.assertTrue(contract.required_state)
                self.assertTrue(contract.visible_feedback)
                self.assertTrue(contract.batch_assertions)
                for values in (
                    contract.required_state,
                    contract.visible_feedback,
                    contract.batch_assertions,
                ):
                    self.assertTrue(all(isinstance(value, str) and value for value in values))

    def test_acceptance_loader_rejects_missing_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            payload = {
                f"{mechanism_id:03d}": valid_acceptance_payload(mechanism_id)
                for mechanism_id in range(1, MECHANISM_COUNT)
            }
            (folder / "acceptance_001_360.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "exactly 001..361"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            duplicate = {"001": valid_acceptance_payload(1)}
            for name in ("acceptance_a.json", "acceptance_b.json"):
                (folder / name).write_text(
                    json.dumps(duplicate, ensure_ascii=False), encoding="utf-8"
                )
            with self.assertRaisesRegex(ValueError, "duplicate acceptance contract"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_missing_or_wrong_typed_field(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            missing = valid_acceptance_payload(1)
            del missing["visible_feedback"]
            (folder / "acceptance_missing.json").write_text(
                json.dumps({"001": missing}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "fields mismatch"):
                load_acceptance_contracts(folder)

        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            wrong_type = valid_acceptance_payload(1)
            wrong_type["required_state"] = "not a list"
            (folder / "acceptance_wrong_type.json").write_text(
                json.dumps({"001": wrong_type}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "must be a non-empty list"):
                load_acceptance_contracts(folder)

    def test_acceptance_loader_rejects_generic_variable_change_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw_folder:
            folder = Path(raw_folder)
            generic = valid_acceptance_payload(1)
            generic["batch_assertions"] = ["变量变化"]
            (folder / "acceptance_generic.json").write_text(
                json.dumps({"001": generic}, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "generic variable-change claim"):
                load_acceptance_contracts(folder)

    def test_shared_ledgers_have_real_tradeoffs(self) -> None:
        for mechanism in self.mechanisms:
            choices = {
                choice: mechanism_deltas(mechanism, choice)
                for choice in ("a", "b", "c")
            }
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(len({tuple(sorted(value.items())) for value in choices.values()}), 3)
                for deltas in choices.values():
                    self.assertTrue(deltas)
                    self.assertTrue(set(deltas).issubset(LEDGERS))
                # At least one route carries an explicit cost/risk, preventing a no-brainer trio.
                self.assertTrue(
                    any(
                        value > 0
                        for choice in choices.values()
                        for key, value in choice.items()
                        if key
                        in {
                            "admin_load",
                            "appeal_risk",
                            "tech_debt",
                            "burnout",
                            "hc_pressure",
                            "pay_debt",
                            "policy_debt",
                            "budget_pressure",
                        }
                    )
                )

    def test_generated_runtime_coverage(self) -> None:
        event_path = MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt"
        events = self.rendered[event_path].decode("utf-8-sig")
        effects = self.effects
        for mechanism in self.mechanisms:
            with self.subTest(mechanism=mechanism.id):
                self.assertEqual(events.count(f"zg361m.{mechanism.id} = {{"), 1)
                for choice in ("a", "b", "c"):
                    self.assertEqual(effects.count(f"{effect_name(mechanism.id, choice)} = {{"), 1)
                    self.assertIn(
                        f"custom_tooltip = zg361m.{mechanism.id}.{choice}.tt",
                        events,
                    )
                self.assertEqual(
                    effects.count(f"zg361_mechanism_{mechanism.id:03d}_ai_effect = {{"),
                    1,
                )
                self.assertIn(f"ZG361M: CASE {mechanism.id:03d}", effects)

    def test_org_climate_thresholds_do_not_read_unset_ledgers(self) -> None:
        effects = self.effects
        climate = effects.split("zg361_refresh_org_climate_effect = {", 1)[1]
        expected = (
            ("trust", 20, "zg361_org_high_trust"),
            ("admin_load", 35, "zg361_org_admin_overload"),
            ("burnout", 20, "zg361_org_burnout_crisis"),
            ("stability", 20, "zg361_org_delivery_stable"),
            ("tech_debt", 20, "zg361_org_tech_debt_crisis"),
            ("talent", 20, "zg361_org_talent_healthy"),
        )
        for ledger, threshold, modifier in expected:
            variable = f"zg361_org_{ledger}"
            guarded = (
                "\tif = {\n"
                "\t\tlimit = {\n"
                "\t\t\ttrigger_if = {\n"
                f"\t\t\t\tlimit = {{ has_variable = {variable} }}\n"
                f"\t\t\t\tvar:{variable} >= {threshold}\n"
                "\t\t\t}\n"
                "\t\t\ttrigger_else = { always = no }\n"
                "\t\t}\n"
                f"\t\tadd_character_modifier = {{ modifier = {modifier} years = 1 }}\n"
                "\t}"
            )
            with self.subTest(ledger=ledger):
                self.assertIn(guarded, climate)
                self.assertNotIn(
                    f"\t\tlimit = {{ var:{variable} >= {threshold} }}", climate
                )

    def test_player_decisions_hide_internal_pending_flags(self) -> None:
        decisions_path = (
            MOD_ROOT / "common" / "decisions" / "zg361_mechanism_decisions.txt"
        )
        decisions = self.rendered[decisions_path].decode("utf-8-sig")
        for decision_key, flag, description_key in (
            (
                "zg361_next_mechanism_decision",
                "zg361_mechanism_next_pending",
                "zg361_next_mechanism_decision_ready",
            ),
            (
                "zg361_reference_charter_decision",
                "zg361_reference_charter_pending",
                "zg361_reference_charter_decision_ready",
            ),
        ):
            region = decisions.split(f"{decision_key} = {{", 1)[1].split("\n}", 1)[0]
            with self.subTest(decision=decision_key):
                self.assertEqual(region.count("custom_description = {"), 2)
                self.assertEqual(region.count(f"text = {description_key}"), 2)
                self.assertEqual(region.count(f"has_character_flag = {flag}"), 2)

    def test_policy_localization_renders_ids_and_line_breaks_literally(self) -> None:
        chinese_path = (
            MOD_ROOT
            / "localization"
            / "simp_chinese"
            / "zg361_mechanisms_l_simp_chinese.yml"
        )
        english_path = (
            MOD_ROOT
            / "localization"
            / "english"
            / "zg361_mechanisms_l_english.yml"
        )
        chinese = self.rendered[chinese_path].decode("utf-8-sig")
        english = self.rendered[english_path].decode("utf-8-sig")
        self.assertIn('zg361m.1.t:0 "第001号 · 绩效指标分项证据单"', chinese)
        self.assertIn('zg361m.3.t:0 "第003号 · 期中面谈与目标重置"', chinese)
        self.assertIn('zg361m.1.t:0 "No.001 · Itemized KPI Evidence Sheet"', english)
        self.assertIn(
            'zg361_next_mechanism_decision_confirm:0 "打开下一项制度评审"',
            chinese,
        )
        self.assertIn(
            'zg361_reference_charter_decision_confirm:0 "采用全部 361 项推荐默认值，立即写入组织账本"',
            chinese,
        )
        self.assertIn(
            'zg361_next_mechanism_decision_confirm:0 "Open the next policy review"',
            english,
        )
        self.assertIn(
            'zg361_reference_charter_decision_confirm:0 "Adopt all 361 recommended defaults and write them to the organizational ledger"',
            english,
        )
        for empty_slogan in (
            "叫下一位产品经理进来",
            "我全都要，现在就要",
            "Bring in the next policy owner",
            "Ship the entire portfolio",
        ):
            with self.subTest(empty_slogan=empty_slogan):
                self.assertNotIn(empty_slogan, chinese + english)
        self.assertIn(
            'zg361m.1.desc:0 "高低分必须附具体事例；申诉、绩效改进计划和晋升包复用同一份冻结证据，杜绝让下一年的现值改写旧案。"',
            chinese,
        )
        for key in ("zg361m.18.a", "zg361m.71.a", "zg361m.206.a"):
            self.assertIn(f'{key}:0 "', chinese)
        self.assertIn("主要账簿变动：", chinese)
        self.assertIn("完整账簿变动：", chinese)
        self.assertIn(
            'zg361m.347.t:0 "第347号 · 经理人工调整额度"',
            chinese,
        )
        self.assertIn(
            'zg361m.18.c:0 "搁置本局提案；主要账簿变动：行政负担-1、制度债+3"',
            chinese,
        )
        self.assertNotIn("决策：", chinese)
        self.assertNotIn("后果：", chinese)
        self.assertNotIn("登记路线甲倾向", chinese)
        self.assertNotIn("登记路线乙倾向", chinese)
        self.assertNotIn("／P0】", chinese)
        self.assertNotIn("／P1】", chinese)
        self.assertNotIn("／P2】", chinese)
        self.assertNotIn("CK3", chinese)
        self.assertNotIn("GUI", chinese)
        self.assertNotIn("Override", chinese)
        for untranslated_term in (
            "HC",
            "PIP",
            "owner",
            "KPI",
            "Offer",
            "sponsor",
            "backfill",
            "Cliff",
            "FIFO",
            "WIP",
            "SLA",
            "toil",
            "onboarding",
            "Check-in",
            "玩家",
            "脚本",
            "回写",
            "本卡",
            "结算器",
            "运行时纵切",
            "OKR",
            "HR",
            " vs ",
            " ID",
            "cohort",
            "PPT",
            "原生治理成果",
        ):
            with self.subTest(untranslated_term=untranslated_term):
                self.assertNotIn(untranslated_term, chinese)
        for raw_grade_phrase in (
            "背 C",
            "C 档",
            "员工 C",
            "填 C",
            "免 C",
            "的 C",
        ):
            with self.subTest(raw_grade_phrase=raw_grade_phrase):
                self.assertNotIn(raw_grade_phrase, chinese)
        self.assertIsNone(re.search(r"(?<![A-Za-z])live(?![A-Za-z])", chinese))
        self.assertIn('zg361m.18.a:0 "', english)
        self.assertIn("main ledger changes:", english)
        self.assertIn("Full ledger changes:", english)
        self.assertIn(
            'zg361m.18.c:0 "Shelve this policy; main ledger changes: administrative load-1, policy debt+3"',
            english,
        )
        self.assertNotIn("Record route A preference", english)
        self.assertNotIn("Record route B preference", english)
        self.assertNotIn("执行人物", chinese)
        self.assertNotIn("一键部署《大厂全家桶》", chinese)
        self.assertNotIn("。 本项", chinese)
        self.assertNotIn(r"\\n", chinese)
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}
        long_buttons = []
        for line in chinese.splitlines():
            if not line.startswith(" zg361m."):
                continue
            if any(f".{choice}:0 \"" in line for choice in ("a", "b")):
                value = line.split(':0 "', 1)[1].removesuffix('"')
                if len(value) > 50:
                    long_buttons.append((line.split(":", 1)[0], value))
            if ".desc:0 " not in line:
                continue
            key, value = line.split(':0 "', 1)
            mechanism_id = int(key.removeprefix(" zg361m.").removesuffix(".desc"))
            description = value.removesuffix('"')
            with self.subTest(mechanism_id=mechanism_id):
                self.assertFalse(description.startswith(("。", "，", "；", "：", "！", "？")))
                self.assertNotIn(mechanisms_by_id[mechanism_id].title_cn, description)
                self.assertNotIn(mechanisms_by_id[mechanism_id].decision_cn, description)
        self.assertEqual(long_buttons, [])
        for path, rendered in self.rendered.items():
            if path.name.startswith("zg361_mechanisms_l_"):
                text = rendered.decode("utf-8-sig")
                title_lines = [
                    line
                    for line in text.splitlines()
                    if line.startswith(" zg361m.") and ".t:0 " in line
                ]
                with self.subTest(language=path.parent.name):
                    self.assertEqual(len(title_lines), 361)
                    self.assertFalse(any(':0 "#' in line for line in title_lines))

    def test_events_312_to_361_use_plain_player_facing_policy_copy(self) -> None:
        chinese = localization_values(self.mechanisms, "simp_chinese")
        expected_tokens = {
            "zg361m.312.a.tt": ("薪酬区间", "内部公示期"),
            "zg361m.314.desc": ("迁居与安置成本",),
            "zg361m.315.desc": ("试岗失败后返岗", "不应自动判为未达标"),
            "zg361m.316.t": ("薪酬区间衔接",),
            "zg361m.316.b": ("新岗位薪酬区间", "重新核定全部薪俸"),
            "zg361m.318.t": ("申请频次", "名额占用"),
            "zg361m.318.a": ("高潜力人选", "不占正式名额"),
            "zg361m.319.t": ("一次挽留方案",),
            "zg361m.319.a": ("可兑现的挽留方案",),
            "zg361m.324.t": ("结课、应用与业务结果",),
            "zg361m.324.desc": ("刷课时、刷证书的漏洞",),
            "zg361m.328.desc": ("跨组评判尺度的一致性",),
            "zg361m.328.b": ("所有工时",),
            "zg361m.330.t": ("衰退业务人员转训",),
            "zg361m.330.desc": ("仍具潜力的人才",),
            "zg361m.331.desc": ("创新项目储备",),
            "zg361m.331.a": ("学习工时",),
            "zg361m.333.t": ("留任与返还约定",),
            "zg361m.333.desc": ("返还义务能保护培训投入",),
            "zg361m.334.desc": ("加重提名人的责任", "没有门路的项目"),
            "zg361m.334.b": ("有权势的提名人",),
            "zg361m.335.desc": ("未使用的急件名额",),
            "zg361m.335.a": ("预留少量急件名额",),
            "zg361m.336.t": ("需求受理门槛",),
            "zg361m.339.desc": ("工期报得过分宽松", "没有说明原因的超时"),
            "zg361m.339.a": ("故意虚增工期",),
            "zg361m.340.b": ("更多尾部延期",),
            "zg361m.345.desc": ("考核通知在短期内接连出现",),
            "zg361m.346.desc": ("正式考核中只结算一次",),
            "zg361m.346.a": ("年末只结算一次",),
            "zg361m.347.a.tt": ("只准少量调整", "事后核验准确性"),
            "zg361m.349.desc": ("耗审计人力",),
            "zg361m.351.desc": ("事先登记的规则和结果",),
            "zg361m.351.a.tt": ("事先登记规则", "决定是否推广"),
            "zg361m.352.a": ("附换算说明", "从新一轮重新记账"),
            "zg361m.354.a": ("复核审计",),
            "zg361m.355.t": ("目标自动加码",),
            "zg361m.355.desc": ("过度加码目标", "压低上报产出"),
            "zg361m.356.desc": ("限制目标自动加码",),
            "zg361m.356.a": ("限制目标自动加码",),
            "zg361m.358.desc": ("申诉不应加重原处理", "新发生的造假仍须另案追究"),
            "zg361m.359.t": ("名额返还与重新送达",),
            "zg361m.359.a.tt": ("档位边缘的受评者", "重新送达"),
            "zg361m.359.b.tt": ("档位边缘的受评者", "不向受影响者重新送达"),
            "zg361m.360.desc": ("高档人才比例", "伤害管理层信任"),
            "zg361m.360.a.tt": ("责任记入组织账簿",),
            "zg361m.360.b.tt": ("守住高档人才比例",),
            "zg361m.361.a.tt": ("人员信任和福祉",),
            "zg361m.361.b.tt": ("守住高档人才比例",),
        }
        for key, tokens in expected_tokens.items():
            with self.subTest(key=key):
                for token in tokens:
                    self.assertIn(token, chinese[key])

        reviewed_copy = "\n".join(chinese[key] for key in expected_tokens)
        for internal_or_broken in (
            "免费瞬移", "3.25", "岗位带宽", "占位费", "高潜一次", "不占槽",
            "反录用邀约", "结课 / 应用", "所有容量", "健康人才", "创新管线",
            "提名担保人债", "未用槽", "急件槽", "准入完成定义", "故意留水",
            "交付尾差", "事件风暴", "正式周期消费", "调整点", "命中率",
            "组织容量", "预注册", "可比映射", "元审计", "目标棘轮", "重棘轮",
            "违法免疫", "边界人", "连环程序", "人才密度叙事", "组织温度",
        ):
            with self.subTest(forbidden=internal_or_broken):
                self.assertNotIn(internal_or_broken, reviewed_copy)

        english = localization_values(self.mechanisms, "english")
        english_tokens = {
            "zg361m.316.t": ("Pay-Range Alignment",),
            "zg361m.318.t": ("Application Frequency and Quota Use",),
            "zg361m.318.a.tt": ("outside the quota",),
            "zg361m.319.t": ("Retention Offer",),
            "zg361m.333.t": ("Retention and Repayment Terms",),
            "zg361m.336.t": ("Demand Intake Requirements",),
            "zg361m.346.a.tt": ("count it only once at year-end",),
            "zg361m.347.t": ("Limit on Manual Manager Adjustments",),
            "zg361m.347.a.tt": ("verify accuracy later",),
            "zg361m.351.a.tt": ("Record rules, control groups, and end dates", "agreed results"),
            "zg361m.352.a.tt": ("conversion note", "fresh record"),
            "zg361m.354.a": ("independent follow-up audit",),
            "zg361m.355.t": ("Automatic Target Increases",),
            "zg361m.356.a.tt": ("limit automatic target increases",),
            "zg361m.359.t": ("Returning Quota and Renotifying",),
            "zg361m.359.b.tt": ("without notifying the people affected",),
            "zg361m.360.a.tt": ("record their responsibility in the organizational ledger",),
            "zg361m.360.b.tt": ("target share of top-rated talent",),
            "zg361m.361.a.tt": ("staff trust, and well-being",),
            "zg361m.361.b.tt": ("target share of top-rated talent",),
        }
        for key, tokens in english_tokens.items():
            with self.subTest(key=key):
                for token in tokens:
                    self.assertIn(token, english[key])
        reviewed_english = "\n".join(english[key] for key in english_tokens).lower()
        for internal_or_broken in (
            "pay-band mapping", "slot cost", "counteroffer", "definition of ready",
            "manager override budget", "preregister", "meta-audit", "target ratchet",
            "quota reflow", "talent-density narrative", "management-score cost",
        ):
            with self.subTest(forbidden=internal_or_broken):
                self.assertNotIn(internal_or_broken, reviewed_english)

    def test_every_policy_surface_has_self_contained_copy(self) -> None:
        opening_punctuation = tuple("。！？；：，、,.!?;:)]}）】》〉」』”’…—-·/／")
        dynamic_openers = tuple("[$@")
        generic_button = re.compile(
            r"^(?:(?:按|照|选|走|采用)\s*[ＡＢＣABC](?:做|办|执行|处理|路线)?"
            r"|路线\s*[甲乙丙ＡＢＣABC]|照办|同意|执行|确定|就这么办|好|可以|知道了)"
            r"[。！？]?$",
            re.IGNORECASE,
        )
        body_choice_meta = re.compile(
            r"(?:路线\s*[甲乙丙ＡＢＣABC]|方案\s*[甲乙丙ＡＢＣABC]"
            r"|按\s*[ＡＢＣABC](?:做|办|执行|处理|走)?|(?:下方|以下).{0,8}按钮)",
            re.IGNORECASE,
        )
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}

        for language in ("simp_chinese", "english"):
            values = localization_values(self.mechanisms, language)
            for key, value in values.items():
                if not (key.endswith(".desc") or key.endswith("_desc")):
                    continue
                with self.subTest(language=language, key=key):
                    visible = value.strip()
                    self.assertTrue(visible)
                    self.assertFalse(visible.startswith(opening_punctuation))
                    self.assertFalse(visible.startswith(dynamic_openers))

            for mechanism_id, mechanism in mechanisms_by_id.items():
                prefix = f"zg361m.{mechanism_id}"
                title = values[f"{prefix}.t"].split(" · ", 1)[-1]
                description = values[f"{prefix}.desc"]
                with self.subTest(language=language, mechanism=mechanism_id):
                    self.assertGreaterEqual(len(description.split(r"\n", 1)[0]), 24)
                    self.assertNotIn(title.casefold(), description.casefold())
                    self.assertIsNone(body_choice_meta.search(description))
                    for route_meta in (
                        "两条路线",
                        "现状路线",
                        "任何路线",
                        "你必须决定",
                        "选择写回",
                        "选择后只能",
                    ):
                        self.assertNotIn(route_meta, description)
                    for choice in ("a", "b", "c"):
                        button = values[f"{prefix}.{choice}"]
                        button_core = re.sub(
                            r"(?:（仅记账）| \(ledger only\))[。！？.!?]?$",
                            "",
                            button,
                        ).rstrip("。！？；.!?; ")
                        self.assertIsNone(generic_button.fullmatch(button.strip()))
                        self.assertNotIn(button_core.casefold(), description.casefold())
                        if language == "simp_chinese":
                            self.assertFalse(button_core.endswith("后"))

                    if language == "simp_chinese":
                        for choice in ("a", "b"):
                            button = values[f"{prefix}.{choice}"]
                            expected = principal_ledger_changes_cn(mechanism, choice)
                            self.assertIn(expected, button)
                            self.assertEqual(
                                button.rstrip("。"),
                                normalize_player_chinese(
                                    choice_button_cn(
                                        mechanism,
                                        choice,
                                        ledger_only=mechanism_id
                                        in LEDGER_ONLY_MECHANISM_IDS,
                                    )
                                ),
                            )
                        self.assertIn("搁置本局提案", values[f"{prefix}.c"])
                        self.assertIn("主要账簿变动：", values[f"{prefix}.c"])

    def test_every_route_exposes_principal_and_exact_full_ledger_deltas(self) -> None:
        languages = (
            "simp_chinese",
            "english",
            "french",
            "german",
            "japanese",
            "korean",
            "polish",
            "russian",
            "spanish",
        )
        for language in languages:
            values = localization_values(self.mechanisms, language)
            for mechanism in self.mechanisms:
                for choice in ("a", "b", "c"):
                    prefix = f"zg361m.{mechanism.id}.{choice}"
                    with self.subTest(
                        language=language, mechanism=mechanism.id, choice=choice
                    ):
                        if language == "simp_chinese":
                            self.assertIn("主要账簿变动：", values[prefix])
                            self.assertIn(
                                f"完整账簿变动：{full_ledger_changes_cn(mechanism, choice)}。",
                                values[f"{prefix}.tt"],
                            )
                            if choice in ("a", "b"):
                                self.assertEqual(
                                    values[prefix].rstrip("。"),
                                    normalize_player_chinese(
                                        choice_button_cn(
                                            mechanism,
                                            choice,
                                            ledger_only=mechanism.id
                                            in LEDGER_ONLY_MECHANISM_IDS,
                                        )
                                    ),
                                )
                        else:
                            self.assertIn("main ledger changes:", values[prefix])
                            self.assertIn(
                                f"Full ledger changes: {full_ledger_changes_en(mechanism, choice)}.",
                                values[f"{prefix}.tt"],
                            )
                            if choice in ("a", "b"):
                                self.assertEqual(
                                    values[prefix],
                                    choice_button_en(
                                        mechanism,
                                        choice,
                                        ledger_only=mechanism.id
                                        in LEDGER_ONLY_MECHANISM_IDS,
                                ),
                            )

    def test_audit_005_006_tooltips_match_actual_choice_effect_deltas(self) -> None:
        for mechanism in self.mechanisms[:71]:
            for choice in ("a", "b", "c"):
                name = effect_name(mechanism.id, choice)
                start = self.effects.index(f"{name} = {{")
                end = self.effects.index("\n}\n", start) + 2
                block = self.effects[start:end]
                pairs = re.findall(
                    r"change_variable = \{ name = zg361_org_(\w+) add = (-?\d+) \}",
                    block,
                )
                with self.subTest(mechanism=mechanism.id, choice=choice):
                    self.assertEqual(len(pairs), len(set(key for key, _value in pairs)))
                    self.assertEqual(
                        {key: int(value) for key, value in pairs},
                        mechanism_deltas(mechanism, choice),
                    )

    def test_manual_audit_005_006_copy_fixes_are_closed(self) -> None:
        chinese = localization_values(self.mechanisms, "simp_chinese")
        english = localization_values(self.mechanisms, "english")
        exact_cn = {
            "zg361m.7.t": "独立提交的 360 邀评",
            "zg361m.13.t": "分层公开与黑箱告知",
            "zg361m.15.t": "绩效改进任务书",
            "zg361m.25.t": "高绩效人才被挖与加码挽留",
            "zg361m.33.t": "管理者画像与可解释裁定理由",
            "zg361m.35.t": "严格 361 与混合门槛",
            "zg361m.41.t": "新人首轮保护与末档风险",
            "zg361m.45.t": "无预警低评与反馈欠账",
            "zg361m.52.t": "保留评价分布，不只看均分",
            "zg361m.62.t": "直属上司与项目上司的目标冲突",
            "zg361m.65.t": "空降主管与随任亲信",
        }
        exact_en = {
            "zg361m.7.t": "Independently Submitted 360 Review Invitations",
            "zg361m.13.t": "Tiered Disclosure or Black-Box Notice",
            "zg361m.15.t": "Performance Improvement Charter",
            "zg361m.25.t": "Poaching High Performers and Retention Counteroffers",
            "zg361m.33.t": "Manager Archetypes and Explainable Rulings",
            "zg361m.35.t": "Strict 361 or Hybrid Thresholds",
            "zg361m.41.t": "First-Cycle Newcomer Protection and Bottom-Tier Risk",
            "zg361m.45.t": "Unwarned Low Ratings and Feedback Debt",
            "zg361m.52.t": "Preserve the Rating Distribution, Not Just the Mean",
            "zg361m.62.t": "Goal Conflict Between Direct and Project Superiors",
            "zg361m.65.t": "Parachute Manager and Accompanying Loyalists",
        }
        for key, expected in exact_cn.items():
            self.assertTrue(chinese[key].endswith(expected), (key, chinese[key]))
        for key, expected in exact_en.items():
            self.assertTrue(english[key].endswith(expected), (key, english[key]))

        required_cn = {
            "zg361m.19.a.tt": "提交晋升案卷",
            "zg361m.24.a": "约定交接与补岗",
            "zg361m.23.desc": "夸大预期收益",
            "zg361m.23.b.tt": "透支编制信用，并提高倦怠风险",
            "zg361m.25.b.tt": "跨团队报复",
            "zg361m.27.desc": "独立提交的 360 互评",
            "zg361m.27.a.tt": "成果归口人、主责者、协作者、救火者与阻塞责任人",
            "zg361m.31.desc": "进入评议名单",
            "zg361m.31.a.tt": "送入评议名单",
            "zg361m.32.b.tt": "把下属的个案层层归罪于经理",
            "zg361m.33.a.tt": "裁定理由",
            "zg361m.33.b.tt": "上司个人意志更鲜明",
            "zg361m.35.desc": "强制分布可以提高人才密度，也会制造内耗与牺牲者",
            "zg361m.40.desc": "离任者垫档",
            "zg361m.42.b.tt": "下调整组互评权重",
            "zg361m.49.a.tt": "互评分别提交、统一封存",
            "zg361m.50.a.tt": "筛查异常互评关系",
            "zg361m.54.desc": "迫使所有人把工时耗在汇报上，反而压低真实产出",
            "zg361m.56.desc": "如实让功",
            "zg361m.61.a.tt": "复杂协作另附索引与附录",
            "zg361m.62.b.tt": "服从直属上司并暂停项目上司的交付要求",
            "zg361m.63.a.tt": "危机时调整权重的条件",
            "zg361m.68.desc": "可信参考",
        }
        for key, expected in required_cn.items():
            self.assertIn(expected, chinese[key], (key, chinese[key]))

        forbidden = (
            "背靠背 360 邀评",
            "给背靠背 360",
            "PIP 改进任务书",
            "提包",
            "夸大成功",
            "推高薪酬、空心承诺和团队报复",
            "讨论桌",
            "理由码",
            "人物更强烈",
            "死人头",
            "整组降权",
            "不得惊讶",
            "互评背靠背封存",
            "筛查评价对",
            "评价形状",
            "汇报均衡",
            "正确让功",
            "实线上司",
            "虚线交付",
            "危机改权条件",
            "旧部包",
            "可信先验",
            "back…",
        )
        joined = "\n".join(chinese[f"zg361m.{i}.{suffix}"] for i in range(1, 72) for suffix in ("t", "desc", "a", "b", "a.tt", "b.tt"))
        for phrase in forbidden:
            self.assertNotIn(phrase, joined)

        chinese = localization_values(self.mechanisms, "simp_chinese")
        descriptions = [
            chinese[f"zg361m.{mechanism.id}.desc"]
            for mechanism in self.mechanisms
        ]
        self.assertEqual(len(set(descriptions)), MECHANISM_COUNT)
        joined = "\n".join(chinese.values())
        for malformed in (
            "责任责任人",
            "编号 发奖",
            "经理人工 调整权限 预算",
            "穷尽私下沟通和正式申诉后。",
        ):
            with self.subTest(malformed=malformed):
                self.assertNotIn(malformed, joined)
        for mechanism in self.mechanisms:
            description = chinese[f"zg361m.{mechanism.id}.desc"]
            with self.subTest(mechanism=mechanism.id, field="source-copy"):
                self.assertNotIn(
                    naturalize_mechanism_chinese(mechanism.title_cn),
                    description,
                )
                self.assertNotIn(
                    naturalize_mechanism_chinese(mechanism.decision_cn),
                    description,
                )

    def test_192_228_tooltips_add_complete_ledger_and_case_boundary(self) -> None:
        self.assertEqual(FULL_LEDGER_TOOLTIP_MECHANISM_IDS, frozenset(range(192, 229)))
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}
        chinese = localization_values(self.mechanisms, "simp_chinese")
        english = localization_values(self.mechanisms, "english")
        placeholder = localization_values(self.mechanisms, "german")
        reviewed = 0
        for mechanism_id in FULL_LEDGER_TOOLTIP_MECHANISM_IDS:
            mechanism = mechanisms_by_id[mechanism_id]
            for choice in ("a", "b"):
                reviewed += 1
                key = f"zg361m.{mechanism_id}.{choice}.tt"
                source_cn = naturalize_mechanism_chinese(
                    mechanism.option_a_cn if choice == "a" else mechanism.option_b_cn
                ).rstrip("。！？；")
                source_en = (
                    mechanism.option_a_en if choice == "a" else mechanism.option_b_en
                ).rstrip(".!?; ")
                with self.subTest(mechanism=mechanism_id, choice=choice):
                    self.assertGreater(len(mechanism_deltas(mechanism, choice)), 2)
                    self.assertNotIn(source_cn, chinese[key])
                    self.assertNotIn(source_en, english[key])
                    self.assertIn(full_ledger_changes_cn(mechanism, choice), chinese[key])
                    self.assertIn(full_ledger_changes_en(mechanism, choice), english[key])
                    self.assertIn("只设定今后案卷的制度规则", chinese[key])
                    self.assertIn("without an opened case", english[key])
                    self.assertEqual(placeholder[key], english[key])
        self.assertEqual(reviewed, 74)

    def test_events_009_010_manual_copy_findings_stay_closed(self) -> None:
        chinese = localization_values(self.mechanisms, "simp_chinese")
        expected_snippets = {
            "zg361m.154.t": "逐项完整纪要",
            "zg361m.158.b": "核心辅导和游说资源",
            "zg361m.161.desc": "陪跑安排若得逞",
            "zg361m.162.b": "有强势提名担保人的候选人",
            "zg361m.163.a.tt": "候选人最近两轮履历，或其在现级别的完整履历",
            "zg361m.172.t": "评委投票规则",
            "zg361m.178.desc": "只具备其中一项证据",
            "zg361m.181.t": "能力、意愿、目标与岗职四向诊断",
            "zg361m.186.desc": "目标锁变成永久免疫",
            "zg361m.191.desc": "完成必要交接后的合理退出",
            "zg361m.192.t": "能力分层急务轮值",
            "zg361m.193.t": "值守补偿办法",
            "zg361m.199.a": "风险基线与观察期",
            "zg361m.200.a": "超出日常职权",
            "zg361m.205.t": "重复运维工时比例上限",
            "zg361m.208.a": "逐步替换旧系统",
            "zg361m.209.desc": "耗用国库资金",
            "zg361m.214.a": "检验场景选择是否合理",
            "zg361m.215.t": "退役旧系统也算交付",
            "zg361m.219.desc": "少量客群的深度使用",
            "zg361m.219.a": "防止浅接入刷数的约束指标",
            "zg361m.223.a": "需改造就回馈原方案；关键差异另行申请例外",
            "zg361m.224.desc": "选定一个主方案可释放维护成本",
            "zg361m.225.a": "无法兼容的安全或性能要求",
            "zg361m.228.t": "共享平台事故的波及范围与责任",
        }
        for key, snippet in expected_snippets.items():
            with self.subTest(key=key):
                self.assertIn(snippet, chinese[key])

        joined = "\n".join(chinese.values())
        for stale_copy in (
            "录音式完整纪要",
            "陪跑成功能",
            "强提名担保人的人",
            "两轮或本级完整履历",
            "只强一项的候选",
            "目标锁变永久免疫",
            "真实健康退出",
            "急务值守轮盘",
            "值守津贴 / 调休二选一",
            "重复运维（重复运维）",
            "但花国库",
            "反校验证选择",
            "退役旧制度也算交付",
            "深度少客群",
            "检索复用、贡献改造与差异例外",
            "选一释放维护成本",
            "只有硬差异获批",
            "中台事故的爆炸半径责任",
        ):
            with self.subTest(stale_copy=stale_copy):
                self.assertNotIn(stale_copy, joined)

    def test_machine_manifest_maps_every_id(self) -> None:
        manifest_path = MOD_ROOT / "docs" / "361-mechanism-manifest.json"
        manifest = json.loads(self.rendered[manifest_path].decode("utf-8"))
        self.assertEqual(manifest["schema"], 5)
        self.assertEqual(manifest["mechanism_count"], 361)
        self.assertEqual(manifest["runtime_plan"]["coverage"], 361)
        self.assertEqual(manifest["runtime_plan"]["domain_count"], 38)
        self.assertIn("does not change domain_runtime", manifest["runtime_plan"]["claim_boundary"])
        self.assertEqual([item["id"] for item in manifest["items"]], list(range(1, 362)))
        self.assertEqual({item["live_wave"] for item in manifest["items"]}, {1, 2, 3, 4})
        phase2_ids = {int(mechanism_id) for mechanism_id in PHASE2_RUNTIME_SPECS}
        mechanisms_by_id = {mechanism.id: mechanism for mechanism in self.mechanisms}
        for item in manifest["items"]:
            self.assertEqual(len(item["implementation"]["choice_effects"]), 3)
            self.assertEqual(item["runtime_plan"]["status"], "contract-complete")
            self.assertNotIn("case.transition", item["runtime_plan"]["primitive_recipe"])
            self.assertEqual(
                item["runtime_plan"]["transition_owner"],
                "stage_dispatcher",
            )
            self.assertEqual(set(item["runtime_plan"]["choice_transitions"]), {"a", "b", "c"})
            self.assertIn("not a claim", item["runtime_plan"]["claim_boundary"])
            record = READINESS_BY_ID[item["id"]]
            expected_evidence = {
                ReadinessLevel.DESIGN_ONLY: "none",
                ReadinessLevel.PYTHON_L0: "python-l0",
                ReadinessLevel.CK3_STATIC_READY: "static-ready",
                ReadinessLevel.CENTRAL_WIRED: "static-ready",
                ReadinessLevel.CK3_LIVE: "fixture-live",
            }[record.level]
            self.assertEqual(
                item["status"]["domain_runtime"],
                "partial"
                if record.level >= ReadinessLevel.CK3_STATIC_READY
                else "not-implemented",
            )
            self.assertEqual(item["status"]["runtime_evidence"], expected_evidence)
            self.assertEqual(item["readiness"], record.manifest_payload())
            self.assertNotIsInstance(item["status"], str)
            if item["id"] in phase2_ids:
                self.assertIsInstance(item["runtime_contract"], dict)
                self.assertEqual(
                    set(item["runtime_contract"]),
                    {
                        "object_type",
                        "owner_binding",
                        "subject_binding",
                        "cycle_binding",
                        "case_binding",
                        "hook",
                        "states",
                        "feedback",
                        "permissions",
                    },
                )
            else:
                self.assertNotIn("runtime_contract", item)
            self.assertEqual(
                tuple(item["acceptance_contract"]), ACCEPTANCE_FIELDS
            )
            self.assertEqual(
                item["acceptance_contract"],
                mechanisms_by_id[item["id"]].acceptance_contract.manifest_payload(),
            )
        self.assertEqual(
            manifest["acceptance"]["run_id"],
            "zga_20260829_061314_ea5f04ad",
        )
        self.assertIn(
            "1083",
            manifest["acceptance"]["claim_boundary"],
        )
        static_ids = list(ids_at_least(ReadinessLevel.CK3_STATIC_READY))
        self.assertEqual(manifest["phase2_static"]["mechanism_ids"], static_ids)
        self.assertEqual(
            manifest["phase2_static"]["count"],
            CUMULATIVE_COUNTS["ck3-static-ready"],
        )
        self.assertEqual(
            manifest["phase2_static"]["evidence"],
            "at-least-ck3-static-ready",
        )
        self.assertEqual(
            manifest["readiness"]["cumulative_counts"],
            dict(CUMULATIVE_COUNTS),
        )
        self.assertIn(
            "do not prove complete semantics",
            manifest["phase2_static"]["claim_boundary"],
        )

    def test_checked_in_projection_is_current(self) -> None:
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in self.rendered.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])


if __name__ == "__main__":
    sys.exit(unittest.main())
