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

    def test_visible_descriptions_have_a_stable_narrative_opening(self) -> None:
        chinese = entries(chinese=True)
        english = entries(chinese=False)
        punctuation = tuple("。！？；，,.!?;:：")
        for mechanism_id in sorted(generator.SUBJECT_RESPONSE_IDS):
            key = f"zg361_cl_m{mechanism_id:03d}_desc"
            for description in (chinese[key], english[key]):
                self.assertFalse(description.startswith("["), key)
                self.assertFalse(description.startswith(punctuation), key)
                self.assertNotEqual(description, chinese[f"zg361_cl_m{mechanism_id:03d}_title"])
                self.assertNotEqual(description, english[f"zg361_cl_m{mechanism_id:03d}_title"])

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
            "后台办理",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, visible)

    def test_the_six_choices_disclose_their_material_stakes(self) -> None:
        chinese = entries(chinese=True)
        expected = {
            314: ("二十金", "本次考课档次不受这次答复影响"),
            315: ("九十日", "四成功劳", "六成"),
            318: ("两次正式求调", "日后即使撤回"),
            319: ("三十日内办结", "九十日仍未交付", "按失约结案"),
            321: ("仍能联络", "昔日案卷仍旧留存"),
            333: ("公帑十八金", "九十日后归还十八金", "官署裁撤"),
        }
        for mechanism_id, phrases in expected.items():
            description = chinese[f"zg361_cl_m{mechanism_id:03d}_desc"]
            for phrase in phrases:
                self.assertIn(phrase, description)

    def test_subject_buttons_describe_only_the_players_response(self) -> None:
        chinese = entries(chinese=True)
        self.assertEqual(chinese["zg361_cl_m314_route_a"], "接受调任；公帑支十五金、主官私库支五金")
        self.assertEqual(chinese["zg361_cl_m314_route_b"], "谢绝调任，仍守本职且考课不改档")
        self.assertEqual(chinese["zg361_cl_m315_route_b"], "终止试任，按约回任且不记低档")
        self.assertEqual(chinese["zg361_cl_m318_route_b"], "暂不递交，保留这次求调名额")
        self.assertEqual(chinese["zg361_cl_m319_route_a"], "拒绝挽留，启动三十日调任")
        self.assertEqual(chinese["zg361_cl_m319_route_b"], "接受挽留；若九十日未兑现，按失约追责")
        self.assertEqual(chinese["zg361_cl_m321_route_b"], "退回名帖，终止往来且保留昔日案卷")
        self.assertEqual(chinese["zg361_cl_m333_route_b"], "提前离任，九十日后归还十八金")
        self.assertNotIn("经理", "\n".join(chinese.values()))

    def test_digest_reports_in_world_matters_not_pipeline_mechanics(self) -> None:
        chinese = entries(chinese=True)
        self.assertEqual(chinese["zg361_cl_digest_title"], "本轮人才安排已经登记")
        self.assertIn("六宗涉及调任、试任、求调、挽留、旧部往来或培训旧约", chinese["zg361_cl_digest_desc"])
        self.assertIn("其余十六宗依既定章程直接办结", chinese["zg361_cl_digest_desc"])
        self.assertIn("逐案保留期限与回执", chinese["zg361_cl_digest_desc"])
        self.assertIn("保护工时只有在当事人或主官处于战事时才可借用", chinese["zg361_cl_digest_desc"])
        self.assertIn("无战事的申请按未履约入账", chinese["zg361_cl_digest_desc"])
        self.assertIn("内部调任", chinese["zg361_cl_digest_desc"])
        self.assertIn("进修培养", chinese["zg361_cl_digest_desc"])
        self.assertEqual(chinese["zg361_cl_digest_ack"], "收下案卷，照章续办。")


if __name__ == "__main__":
    unittest.main()
