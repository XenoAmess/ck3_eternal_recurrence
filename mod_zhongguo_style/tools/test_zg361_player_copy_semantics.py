#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Player-copy contracts for semantic dossier values and safe sentence starts."""

from __future__ import annotations

from pathlib import Path
import re
import unittest

from gen_361_b1_runtime import outputs as b1_outputs
from gen_scoreboard_snapshot import (
    B1_OBJECT_FIELDS,
    CASE_FIELDS,
    MOD_ROOT,
    SEMANTIC_FIELD_VALUES,
    outputs as scoreboard_outputs,
)


class PlayerCopySemanticTests(unittest.TestCase):
    def test_every_semantic_value_has_chinese_and_english_copy(self) -> None:
        rendered = b1_outputs()
        chinese = rendered[
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_b1_l_simp_chinese.yml"
        ].decode("utf-8-sig")
        english = rendered[
            MOD_ROOT / "localization" / "english" / "zg361_b1_l_english.yml"
        ].decode("utf-8-sig")
        self.assertIn("zg361_scoreboard_detail_value_unknown:0", chinese)
        self.assertIn("zg361_scoreboard_detail_value_unknown:0", english)
        for field, values in SEMANTIC_FIELD_VALUES.items():
            for _value, slug in values:
                key = f"zg361_scoreboard_detail_value_{field}_{slug}:0"
                with self.subTest(field=field, slug=slug):
                    self.assertIn(key, chinese)
                    self.assertIn(key, english)

    def test_semantic_fields_never_render_raw_numbers(self) -> None:
        rendered = scoreboard_outputs()
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode("utf-8-sig")
        scripted = rendered[
            MOD_ROOT
            / "common"
            / "scripted_guis"
            / "zg361_generated_scoreboard_slots.txt"
        ].decode("utf-8-sig")
        schema = {field.name for field in CASE_FIELDS + B1_OBJECT_FIELDS}
        self.assertTrue(set(SEMANTIC_FIELD_VALUES) <= schema)
        for field, values in SEMANTIC_FIELD_VALUES.items():
            value_var = f"zg361_sb_detail_{field}"
            with self.subTest(field=field):
                self.assertNotIn(
                    f"Var('{value_var}').GetValue",
                    gui,
                    "player UI must not expose an enum/boolean as a raw number",
                )
                for value, slug in values:
                    self.assertIn(
                        f"zg361_sb_detail_{field}_{slug}_gui = {{",
                        scripted,
                    )
                    self.assertIn(
                        f"var:{value_var} = {value}",
                        scripted,
                    )
                    self.assertIn(
                        f'text = "zg361_scoreboard_detail_value_{field}_{slug}"',
                        gui,
                    )

    def test_receipt_serials_stay_out_of_player_gui(self) -> None:
        gui = scoreboard_outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        hidden = {
            "settlement_serial",
            "refund_serial",
            "b1_fact_sheet_serial",
            "b1_self_receipt_serial",
            "b1_peer_receipt_serial",
            "b1_shadow_receipt_serial",
            "b1_band_receipt_serial",
            "b1_141_agenda_reason",
            "b1_144_fact_reason",
        }
        for field in hidden:
            with self.subTest(field=field):
                self.assertNotIn(f"zg361_scoreboard_detail_field_{field}", gui)
                self.assertNotIn(f"zg361_sb_detail_{field}", gui)

    def test_targeted_descriptions_have_stable_text_before_dynamic_names(self) -> None:
        rendered = b1_outputs()
        documents = {
            path.as_posix(): path.read_text(encoding="utf-8-sig")
            for path in (
                MOD_ROOT / "localization" / "simp_chinese" / "zg361_l_simp_chinese.yml",
                MOD_ROOT / "localization" / "english" / "zg361_l_english.yml",
            )
        }
        for language in ("simp_chinese", "english"):
            path = MOD_ROOT / "localization" / language / f"zg361_b1_l_{language}.yml"
            documents[path.as_posix()] = rendered[path].decode("utf-8-sig")
        dynamic_start = re.compile(r'^\s*[^#\s][^:]*\.desc:0\s+"\[')
        for source, document in documents.items():
            offenders = [
                (line_no, line)
                for line_no, line in enumerate(
                    document.splitlines(), 1
                )
                if dynamic_start.search(line)
            ]
            self.assertEqual(offenders, [], source)

    def test_shadow_grade_is_a_rating_not_an_internal_code(self) -> None:
        rendered = b1_outputs()
        events = rendered[MOD_ROOT / "events" / "zg361_b1_runtime_events.txt"].decode(
            "utf-8-sig"
        )
        chinese = rendered[
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_b1_l_simp_chinese.yml"
        ].decode("utf-8-sig")
        self.assertIn("desc = zg361b1.201.grade_375", events)
        self.assertIn("desc = zg361b1.201.grade_35", events)
        self.assertIn("desc = zg361b1.201.grade_325", events)
        self.assertNotIn("影子档代码", chinese)
        self.assertNotIn("自评选择码", chinese)
        self.assertNotIn("互评分布形态码", chinese)

    def test_core_scoreboard_copy_uses_player_facing_terms(self) -> None:
        rendered = b1_outputs()
        generated_chinese = rendered[
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_b1_l_simp_chinese.yml"
        ].decode("utf-8-sig")
        generated_english = rendered[
            MOD_ROOT / "localization" / "english" / "zg361_b1_l_english.yml"
        ].decode("utf-8-sig")
        core_chinese = (
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_l_simp_chinese.yml"
        ).read_text(encoding="utf-8-sig")
        core_english = (
            MOD_ROOT / "localization" / "english" / "zg361_l_english.yml"
        ).read_text(encoding="utf-8-sig")

        self.assertIn("进绩效改进计划", core_chinese)
        self.assertNotIn("入PIP", core_chinese)
        self.assertNotIn("received 案卷", core_chinese)
        self.assertNotIn("B1 案卷身份", core_chinese)
        self.assertNotIn("B1 互评证据", generated_chinese)
        self.assertNotIn("enter a PIP", core_english)
        self.assertNotIn("received dossier", core_english)
        self.assertNotIn("B1 case identity", core_english)
        self.assertNotIn("B1 Peer Evidence", generated_english)


if __name__ == "__main__":
    unittest.main()
