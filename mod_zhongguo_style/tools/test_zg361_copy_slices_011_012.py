#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exact copy regressions for the manual review of event-ledger slices 011-012."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from gen_361_mechanisms import (
    LEDGER_ONLY_MECHANISM_IDS,
    MOD_ROOT,
    effect_name,
    localization_values,
    principal_ledger_changes_cn,
)
from zg361_mechanism_data import load_mechanisms


REPO_ROOT = MOD_ROOT.parent
AUDITED_IDS = (
    232, 234, 235, 236, 241, 249, 256, 264, 265, 268,
    274, 276, 277, 280, 281, 283, 284, 285, 286, 287,
    288, 289, 290, 292, 297, 301, 302, 304, 306, 309,
)

# Each audited event has at least one exact player-facing repair anchored here.
EXPECTED_CN: dict[int, dict[str, tuple[str, ...]]] = {
    232: {"a": ("真实数据到达后再逐项对账",)},
    234: {
        "desc": ("两者矛盾时应启动校准并说明差异",),
        "a": ("先暂记", "待结果到期后再确认"),
    },
    235: {"desc": ("不能获得完整的最高档评价",)},
    236: {"a": ("期初写明各完成度对应分数",)},
    241: {
        "desc": ("项目上线后随即升迁或调任",),
        "b": ("未来收益全归首任责任人", "接任者独担运营与延迟副作用"),
    },
    249: {
        "a": ("设会议工时上限", "抵消工时", "责任人、议程与结论"),
    },
    256: {
        "desc": ("不直接处分未进入正式案卷的外部人员",),
        "b": ("正式受评组", "直接填末档"),
    },
    264: {"a": ("跟岗交接", "实操验收", "遗留清单")},
    265: {"desc": ("追回损失", "在品行评价中记责")},
    268: {"desc": ("新面试官先按中性基准评价",)},
    274: {"t": ("候选人还价与竞价上限",)},
    276: {
        "desc": ("原有低档记录不自动清零",),
        "b": ("清空原有低档记录与冲突",),
    },
    277: {"desc": ("先把现任压入低绩效并清退，再借机申请扩编",)},
    280: {"a": ("入列本轮奖金名单", "冻结", "折算的公式")},
    281: {"desc": ("管理者的承诺兑现信用",)},
    283: {
        "t": ("只升职责、不加俸的兑现期限",),
        "desc": ("只升职责却不加俸",),
    },
    284: {
        "t": ("降级后的薪俸分段递减",),
        "desc": ("分段递减会增加国库支出",),
    },
    285: {
        "desc": ("同为最高档", "逐项写明理由"),
        "a": ("薪俸区间位置", "逐项写明理由"),
    },
    286: {
        "t": ("高于薪俸上限时冻结、低于下限时追补",),
        "desc": ("薪俸区间外的例外到期必须重审",),
        "a": ("低于薪俸下限", "高于上限改发一次奖", "例外须设到期日"),
    },
    287: {
        "t": ("薪酬保密、职级薪俸区间公开与匿名分布",),
        "a": ("公开职级薪俸区间", "同岗匿名分布"),
        "b": ("职级薪俸区间全部保密",),
    },
    288: {"desc": ("持续处于较高档位的人才",)},
    289: {
        "desc": ("不能因此凭空改成最高档",),
        "a": ("薪俸区间", "算错只补钱不改榜"),
    },
    290: {"b": ("本轮最醒目的最高档者",)},
    292: {
        "a": ("由受奖者知情选择", "期权、限制份额或现金", "各自主要风险"),
    },
    297: {
        "desc": ("一次低档记录而全部没收",),
        "b": ("一次低档记录即取消全部未归属份额",),
    },
    301: {"desc": ("不再自动获得最高档",)},
    302: {"a": ("转型或新业务里程碑",)},
    304: {"t": ("项目与职能的双重管理",)},
    306: {
        "t": ("临时代管两组时的精力与目标拆分",),
        "desc": ("代管两组成功体现统筹能力",),
        "a": ("两组精力与目标占比", "给津贴、减目标或配副手", "设到期日"),
    },
    309: {
        "desc": ("增加述职机会", "边远团队的实际成果", "加剧人才流失"),
        "a": ("上司巡访", "主管工时", "实际成本"),
    },
}

FORBIDDEN_CN: dict[int, tuple[str, ...]] = {
    232: ("真数",),
    234: ("进入校准说明", "暂定认可到期再转正"),
    235: ("3.75",),
    236: ("冻结斜率",),
    241: ("发布即升走",),
    249: ("owner",),
    256: ("未建模", "正式 361 池"),
    264: ("影子跟岗",),
    265: ("追回国库", "扣价值观"),
    268: ("中性先验",),
    274: ("反录用邀约", "反 Offer"),
    276: ("3.25",),
    277: ("先做低人再扩编",),
    280: ("入池时",),
    281: ("经理兑现分",),
    283: ("干升职",),
    284: ("缓冲坡",),
    285: ("3.75", "理由码"),
    286: ("超带", "低带", "带外", "薪酬带"),
    287: ("密薪", "带宽"),
    288: ("3.5/3.75",),
    289: ("3.75", "带宽"),
    290: ("3.75",),
    292: ("分别冻结风险",),
    297: ("3.25",),
    301: ("3.75",),
    302: ("第二曲线",),
    304: ("双家长",),
    306: ("双帽", "经理容量"),
    309: ("补曝光", "硬成果", "外流", "曝光成本"),
}

EXPECTED_EN: dict[str, tuple[str, ...]] = {
    "zg361m.232.a": ("actual data", "item by item"),
    "zg361m.234.a": ("provisional", "result matures"),
    "zg361m.236.a": ("score for each completion level",),
    "zg361m.241.b": ("first owner", "successor bear operations and delayed side effects"),
    "zg361m.249.a": ("owner, agenda, and decision",),
    "zg361m.256.b": ("formal employee review cohort",),
    "zg361m.264.a": ("accompanied handover",),
    "zg361m.274.t": ("Candidate Counteroffer and Bidding Cap",),
    "zg361m.276.b": ("prior low-rating records",),
    "zg361m.280.a": ("current bonus list", "proration formula"),
    "zg361m.283.t": ("Duties-Only Promotion",),
    "zg361m.284.t": ("Staged Pay Reduction",),
    "zg361m.285.a": ("written reason",),
    "zg361m.286.t": ("Pay Range",),
    "zg361m.286.a": ("expiry for every exception",),
    "zg361m.287.t": ("Published Grade Ranges",),
    "zg361m.289.a": ("pay-range",),
    "zg361m.290.b": ("top-rated performers",),
    "zg361m.292.a": ("principal risk recorded",),
    "zg361m.297.b": ("one low rating",),
    "zg361m.302.a": ("new-business milestones",),
    "zg361m.304.t": ("Dual Project and Functional Management",),
    "zg361m.306.t": ("Two-Team Acting Lead",),
    "zg361m.306.a": ("reduce goals", "appoint a deputy", "expiry"),
    "zg361m.309.a": ("manager's workload",),
}


class CopyAuditSlices011012Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mechanisms = load_mechanisms(MOD_ROOT)
        cls.by_id = {mechanism.id: mechanism for mechanism in cls.mechanisms}
        cls.chinese = localization_values(cls.mechanisms, "simp_chinese")
        cls.english = localization_values(cls.mechanisms, "english")

    def test_all_thirty_manual_findings_have_exact_repairs(self) -> None:
        self.assertEqual(set(EXPECTED_CN), set(AUDITED_IDS))
        self.assertEqual(set(FORBIDDEN_CN), set(AUDITED_IDS))
        for mechanism_id in AUDITED_IDS:
            prefix = f"zg361m.{mechanism_id}"
            visible = "\n".join(
                self.chinese[f"{prefix}.{suffix}"]
                for suffix in ("t", "desc", "a", "b", "a.tt", "b.tt")
            )
            with self.subTest(mechanism=mechanism_id, check="forbidden"):
                for phrase in FORBIDDEN_CN[mechanism_id]:
                    self.assertNotIn(phrase, visible)
            for suffix, fragments in EXPECTED_CN[mechanism_id].items():
                value = self.chinese[f"{prefix}.{suffix}"]
                with self.subTest(mechanism=mechanism_id, key=suffix):
                    for fragment in fragments:
                        self.assertIn(fragment, value)

    def test_four_buttons_expose_action_object_and_principal_consequence(self) -> None:
        required = {
            "zg361m.241.b": ("未来收益", "首任责任人", "接任者", "运营", "延迟副作用"),
            "zg361m.249.a": ("会议工时上限", "抵消工时", "责任人", "议程", "结论"),
            "zg361m.292.a": ("受奖者", "期权", "限制份额", "现金", "主要风险"),
            "zg361m.306.a": ("两组", "精力", "目标", "津贴", "减目标", "副手", "到期日"),
        }
        for key, fragments in required.items():
            with self.subTest(key=key):
                for fragment in fragments:
                    self.assertIn(fragment, self.chinese[key])

    def test_buttons_match_the_bound_choice_effects(self) -> None:
        events = (MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt").read_text(
            encoding="utf-8-sig"
        )
        for mechanism_id in AUDITED_IDS:
            mechanism = self.by_id[mechanism_id]
            self.assertIn(mechanism_id, LEDGER_ONLY_MECHANISM_IDS)
            for choice in ("a", "b"):
                key = f"zg361m.{mechanism_id}.{choice}"
                with self.subTest(mechanism=mechanism_id, choice=choice):
                    self.assertIn(principal_ledger_changes_cn(mechanism, choice), self.chinese[key])
                    self.assertEqual(
                        events.count(f"custom_tooltip = {key}.tt"),
                        1,
                    )
                    self.assertEqual(
                        events.count(f"{effect_name(mechanism_id, choice)} = yes"),
                        1,
                    )

    def test_english_sync_and_other_languages_remain_english_placeholders(self) -> None:
        for mechanism_id in AUDITED_IDS:
            mechanism = self.by_id[mechanism_id]
            with self.subTest(mechanism=mechanism_id, language="english-description"):
                self.assertTrue(mechanism.description_en)
                self.assertTrue(
                    self.english[f"zg361m.{mechanism_id}.desc"].startswith(
                        mechanism.description_en
                    )
                )
        for key, fragments in EXPECTED_EN.items():
            with self.subTest(key=key, language="english"):
                for fragment in fragments:
                    self.assertIn(fragment, self.english[key])
        for language in (
            "french", "german", "japanese", "korean", "polish", "russian", "spanish"
        ):
            placeholders = localization_values(self.mechanisms, language)
            for mechanism_id in AUDITED_IDS:
                for suffix in ("t", "desc", "a", "b", "a.tt", "b.tt"):
                    key = f"zg361m.{mechanism_id}.{suffix}"
                    with self.subTest(language=language, key=key):
                        self.assertEqual(placeholders[key], self.english[key])

    def test_regenerated_ledgers_still_bind_exact_slice_membership(self) -> None:
        expected_ranges = {
            "events-011.json": set(range(232, 272)),
            "events-012.json": set(range(272, 312)),
        }
        combined: set[int] = set()
        for name, expected in expected_ranges.items():
            payload = json.loads(
                (
                    REPO_ROOT
                    / "docs"
                    / "content-audits"
                    / "zg361-copy-ledger"
                    / "events"
                    / name
                ).read_text(encoding="utf-8")
            )
            ids = {
                int(record["event_key"].removeprefix("zg361m."))
                for record in payload["records"]
            }
            with self.subTest(shard=name):
                self.assertEqual(ids, expected)
            combined.update(ids)
        self.assertTrue(set(AUDITED_IDS).issubset(combined))


if __name__ == "__main__":
    sys.exit(unittest.main())
