#!/usr/bin/env python3
"""Player-facing copy contracts for the six career-learning response cards."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_career_learning_runtime as generator


def entries(*, chinese: bool) -> dict[str, str]:
    return dict(generator.localization_entries(chinese))


class CareerLearningCopyTests(unittest.TestCase):
    def test_every_visible_response_has_a_distinct_authored_scene(self) -> None:
        self.assertEqual(
            set(generator.SUBJECT_RESPONSE_DESCRIPTIONS),
            set(generator.SUBJECT_RESPONSE_IDS),
        )
        for language_index in (0, 1):
            descriptions = [
                generator.SUBJECT_RESPONSE_DESCRIPTIONS[mechanism_id][language_index]
                for mechanism_id in sorted(generator.SUBJECT_RESPONSE_IDS)
            ]
            self.assertEqual(len(descriptions), len(set(descriptions)))

    def test_chinese_visible_copy_contains_no_developer_contract_template(self) -> None:
        visible = "\n".join(entries(chinese=True).values())
        forbidden = (
            "本案当事人是",
            "当前需要你回应",
            "不会因此获得考核他人的权限",
            "有钱的调任包",
            "绩效锅",
            "机制已合批",
            "证据路线",
            "业务回执",
            "状态报告",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, visible)

    def test_the_six_choices_disclose_their_material_stakes(self) -> None:
        chinese = entries(chinese=True)
        expected = {
            314: ("二十金", "本次考课不会因此改档"),
            315: ("九十日", "四成功劳", "六成"),
            318: ("两次正式求调", "日后即使撤回"),
            319: ("三十日调任", "九十日后按失约结案"),
            321: ("保留一条联络", "昔日案卷不会随之抹去"),
            333: ("公帑十八金", "九十日后须归还十八金", "官署裁撤"),
        }
        for mechanism_id, phrases in expected.items():
            description = chinese[f"zg361_cl_m{mechanism_id:03d}_desc"]
            for phrase in phrases:
                self.assertIn(phrase, description)

    def test_subject_buttons_describe_only_the_players_response(self) -> None:
        chinese = entries(chinese=True)
        self.assertEqual(chinese["zg361_cl_m314_route_b"], "谢绝调任，仍守本职")
        self.assertEqual(chinese["zg361_cl_m318_route_b"], "暂不递交，保留这次机会")
        self.assertEqual(chinese["zg361_cl_m319_route_a"], "拒绝挽留，启动三十日调任")
        self.assertEqual(chinese["zg361_cl_m321_route_b"], "退回名帖，就此别过")
        self.assertNotIn("经理", "\n".join(chinese.values()))

    def test_digest_reports_in_world_matters_not_pipeline_mechanics(self) -> None:
        chinese = entries(chinese=True)
        self.assertEqual(chinese["zg361_cl_digest_title"], "本轮人才安排已经登记")
        self.assertIn("内部调任", chinese["zg361_cl_digest_desc"])
        self.assertIn("进修培养", chinese["zg361_cl_digest_desc"])
        self.assertEqual(chinese["zg361_cl_digest_ack"], "收下案卷，照章续办。")


if __name__ == "__main__":
    unittest.main()
