#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy gates for Incident, Manager/Governance, and Phase-Two Central UI."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_incident_platform_runtime as incident
import gen_361_manager_governance_runtime as governance
import gen_361_phase2_central_runtime as central


PUNCTUATION_OPENERS = tuple("。！？，；：.!?,;:)]}）】》〉」』”’…")
CHOICE_META = ("A/B", "路线甲", "路线乙", "业务对象", "案卷责任人", "按钮", "按A", "按 A")
TECHNICAL_SHORTCUTS = ("回写", "本卡", "玩家", "结算器", "运行时纵切", "脚本", "爆炸半径")


def parse_localization(text: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2)
        for row in text.splitlines()
        if (match := re.match(r'^ ([^:]+):0 "(.*)"$', row)) is not None
    }


def strip_markup(text: str) -> str:
    text = re.sub(r"\[[^]]+]", "", text)
    text = re.sub(r"#[A-Za-z_]+\s*|#!", "", text)
    return re.sub(r"\s+", " ", text).strip()


def family_rows(language: str) -> dict[str, dict[str, str]]:
    if language == "simp_chinese":
        governance_text = governance.CHINESE_LOC
        central_header = "l_simp_chinese"
    else:
        governance_text = governance.ENGLISH_LOC
        central_header = "l_english"
    return {
        "incident": incident._loc_rows(language),
        "governance": parse_localization(governance_text),
        "central": parse_localization(central.render_localization(language, central_header)),
    }


BODY_KEYS = {
    "incident": (
        "zg361ip.190.desc",
        "zg361ip.290.desc",
        "zg361ip.390.desc",
    ),
    "governance": (
        "zg361mg.120.desc",
        "zg361mg.120.desc_score_only",
        "zg361mg.120.desc_reasons_only",
        "zg361mg.120.desc_unavailable",
        "zg361mg.220.desc",
        "zg361mg.220.fairness_deferred",
        "zg361mg.220.fairness_remediation",
        "zg361mg.220.fairness_clear",
    ),
    "central": ("zg361_p2c_summary_desc",),
}

TITLE_FOR_BODY = {
    **{f"zg361ip.{event_id}.desc": f"zg361ip.{event_id}.t" for event_id in (190, 290, 390)},
    **{
        key: "zg361mg.120.t"
        for key in BODY_KEYS["governance"]
        if key.startswith("zg361mg.120.")
    },
    **{
        key: "zg361mg.220.t"
        for key in BODY_KEYS["governance"]
        if key.startswith("zg361mg.220.")
    },
    "zg361_p2c_summary_desc": "zg361_p2c_summary_title",
}

BUTTON_KEYS = {
    "incident": ("zg361ip.result.ok",),
    "governance": ("zg361mg.120.a", "zg361mg.220.a"),
    "central": ("zg361_p2c_summary_ack",),
}


class IncidentGovernanceCentralCopyTest(unittest.TestCase):
    def test_all_twelve_visible_body_variants_are_reviewed(self) -> None:
        rows = family_rows("simp_chinese")
        reviewed: list[str] = []
        for family, keys in BODY_KEYS.items():
            for key in keys:
                self.assertIn(key, rows[family])
                reviewed.append(rows[family][key])
        self.assertEqual(12, len(reviewed))
        self.assertEqual(12, len(set(reviewed)))

    def test_body_starts_with_prose_and_never_repeats_its_title(self) -> None:
        rows = family_rows("simp_chinese")
        for family, keys in BODY_KEYS.items():
            for key in keys:
                body = rows[family][key].lstrip()
                title = rows[family][TITLE_FOR_BODY[key]]
                with self.subTest(family=family, key=key):
                    self.assertTrue(body)
                    self.assertFalse(body.startswith(("[", *PUNCTUATION_OPENERS)))
                    self.assertNotIn(strip_markup(title), strip_markup(body))

    def test_body_neither_describes_abstract_choices_nor_copies_a_button(self) -> None:
        rows = family_rows("simp_chinese")
        for family, keys in BODY_KEYS.items():
            bodies = [rows[family][key] for key in keys]
            for body in bodies:
                for term in CHOICE_META:
                    self.assertNotIn(term, body, (family, term))
            for button_key in BUTTON_KEYS[family]:
                label = rows[family][button_key]
                if len(label) >= 6:
                    for body in bodies:
                        self.assertNotIn(label, body, (family, button_key))

    def test_all_four_buttons_name_short_concrete_actions(self) -> None:
        rows = family_rows("simp_chinese")
        expected = {
            "zg361ip.result.ok": "将这份结论封入簿册",
            "zg361mg.120.a": "归档本轮评定与现有依据。",
            "zg361mg.220.a": "归档本轮复核，照所列事项续办。",
            "zg361_p2c_summary_ack": "办结与未办，分别记清。",
        }
        for family, keys in BUTTON_KEYS.items():
            for key in keys:
                label = rows[family][key]
                with self.subTest(family=family, key=key):
                    self.assertEqual(expected[key], label)
                    self.assertLessEqual(len(strip_markup(label)), 32)
                    self.assertNotRegex(label, r"(?:路线[甲乙ABC]|按\s*[ABC]\s*(?:做|办|执行)?)")

    def test_final_chinese_contains_no_reviewed_technical_shortcuts(self) -> None:
        rows = family_rows("simp_chinese")
        for family_rows_map in rows.values():
            for key, value in family_rows_map.items():
                for term in TECHNICAL_SHORTCUTS:
                    with self.subTest(key=key, term=term):
                        self.assertNotIn(term, value)

    def test_english_projection_has_the_same_reviewed_surface(self) -> None:
        chinese = family_rows("simp_chinese")
        english = family_rows("english")
        for family in BODY_KEYS:
            self.assertEqual(set(chinese[family]), set(english[family]))
        self.assertEqual("Seal this finding in the record", english["incident"]["zg361ip.result.ok"])
        self.assertEqual(
            "Archive this cycle's finding and its surviving grounds.",
            english["governance"]["zg361mg.120.a"],
        )
        self.assertEqual(
            "Archive this review and carry its named work forward.",
            english["governance"]["zg361mg.220.a"],
        )


if __name__ == "__main__":
    unittest.main()
