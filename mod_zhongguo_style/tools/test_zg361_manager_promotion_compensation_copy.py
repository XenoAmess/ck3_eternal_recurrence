#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focused copy gates for manager governance and promotion/compensation.

These checks read the generated Simplified Chinese files and the event files
that CK3 loads.  They keep the audit on the player-facing projection instead
of accepting a clean producer merely because its Python source looks right.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest


MOD_ROOT = Path(__file__).resolve().parents[1]
LOC_ROOT = MOD_ROOT / "localization" / "simp_chinese"

LOC_FILES = (
    LOC_ROOT / "zg361_manager_governance_l_simp_chinese.yml",
    LOC_ROOT / "zg361_feedback_promotion_pip_l_simp_chinese.yml",
    LOC_ROOT / "zg361_compensation_runtime_l_simp_chinese.yml",
)
EVENT_FILES = (
    MOD_ROOT / "events" / "zg361_manager_governance_runtime_events.txt",
    MOD_ROOT / "events" / "zg361_feedback_promotion_pip_runtime_events.txt",
    MOD_ROOT / "events" / "zg361_generated_compensation_runtime_events.txt",
)

LOC_ROW_RE = re.compile(r'^\s*(?P<key>[^\s:#]+):\d+\s+"(?P<value>.*)"\s*$')
OPENING_PUNCTUATION = frozenset("。！？；：，、,.!?;:)]}）】》〉」』”’…—-·/／")
VAGUE_OPTION_RE = re.compile(
    r"(?:"
    r"照所列事项续办"
    r"|劝候选硬上"
    r"|读取唯一案卷"
    r"|只能选择复核程序"
    r"|按\s*[ＡＢＣABC](?:做|办|执行|处理|走)?"
    r"|(?:接受安排|继续|照办)[。！]?$"
    r")",
    re.IGNORECASE,
)
COMPENSATION_STAGE_KEY_RE = re.compile(
    r"^zg361comp\.1\.(?:l[1-4]|ae[1-5]|af[1-5])$"
)
COMPENSATION_ROUTE_KEY_RE = re.compile(
    r"^zg361comp\.1\.(?:l[1-4]|ae[1-5]|af[1-5])\.r[123]$"
)


def read_localization() -> dict[str, str]:
    entries: dict[str, str] = {}
    for path in LOC_FILES:
        for row in path.read_text(encoding="utf-8-sig").splitlines():
            match = LOC_ROW_RE.match(row)
            if match is None:
                continue
            key = match.group("key")
            if key in entries:
                raise AssertionError(f"duplicate target localization key: {key}")
            entries[key] = match.group("value")
    return entries


def event_references(field: str) -> set[str]:
    pattern = re.compile(
        rf"(?<![\w]){re.escape(field)}\s*=\s*(zg361(?:mg|pp|comp)[\w.]+)\b"
    )
    references: set[str] = set()
    for path in EVENT_FILES:
        references.update(pattern.findall(path.read_text(encoding="utf-8-sig")))
    return references


def strip_markup(value: str) -> str:
    value = value.replace(r"\n", " ")
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = re.sub(r"\$[^$]+\$", "", value)
    value = re.sub(r"#[A-Za-z0-9_]+\s*|#!", "", value)
    return re.sub(r"\s+", " ", value).strip()


class ManagerPromotionCompensationCopyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loc = read_localization()
        cls.body_keys = event_references("desc")
        cls.option_keys = event_references("name")

    def test_generated_target_projection_is_fully_wired(self) -> None:
        self.assertFalse(self.body_keys - self.loc.keys())
        self.assertFalse(self.option_keys - self.loc.keys())
        compensation_bodies = {
            key for key in self.body_keys if COMPENSATION_STAGE_KEY_RE.fullmatch(key)
        }
        compensation_options = {
            key for key in self.option_keys if COMPENSATION_ROUTE_KEY_RE.fullmatch(key)
        }
        self.assertEqual(len(compensation_bodies), 14)
        self.assertEqual(len(compensation_options), 42)

    def test_no_target_body_starts_with_punctuation_or_empty_dynamic_copy(self) -> None:
        failures = []
        for key in sorted(self.body_keys):
            raw = self.loc[key].lstrip()
            if not raw or raw[0] in OPENING_PUNCTUATION or raw[0] in "[$@":
                failures.append(f"{key}: {self.loc[key]!r}")
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_target_bodies_do_not_copy_standard_titles_or_route_labels(self) -> None:
        failures = []
        for key in sorted(self.body_keys):
            if not key.endswith(".desc"):
                continue
            title_key = f"{key[:-5]}.t"
            if title_key not in self.loc:
                continue
            body = strip_markup(self.loc[key])
            title = strip_markup(self.loc[title_key])
            if len(title) >= 4 and title in body:
                failures.append(f"{key} repeats {title_key}: {title!r}")
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_visible_options_name_actions_instead_of_pointing_at_prose(self) -> None:
        failures = [
            f"{key}: {self.loc[key]!r}"
            for key in sorted(self.option_keys)
            if VAGUE_OPTION_RE.search(strip_markup(self.loc[key])) is not None
        ]
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_repaired_manager_and_promotion_actions_remain_explicit(self) -> None:
        expected = {
            "zg361mg.220.a": "归档本轮复核，将未结差异与公平性底账转入下期核验。",
            "zg361pp.166.b": "让候选包继续预审，失败理由照实归档。",
            "zg361pp.181.a": "暂记类别未查明，保留绩效结果且不转作错岗结论。",
            "zg361pp.187.a": "维持既定毕业标准，等待独立席提交结算回执。",
            "zg361pp.187.b": "申请程序复核，保留本人签字权且不预断毕业。",
        }
        self.assertEqual(
            {key: self.loc.get(key) for key in expected},
            expected,
        )

    def test_compensation_bodies_leave_amounts_and_dispositions_on_buttons(self) -> None:
        bodies = {
            key: strip_markup(self.loc[key])
            for key in self.body_keys
            if COMPENSATION_STAGE_KEY_RE.fullmatch(key)
        }
        options = {
            key: strip_markup(self.loc[key])
            for key in self.option_keys
            if COMPENSATION_ROUTE_KEY_RE.fullmatch(key)
        }
        self.assertEqual(len(bodies), 14)
        self.assertEqual(len(options), 42)
        self.assertTrue(all("[ROOT.Var" in self.loc[key] for key in bodies))
        missing_consequence = {
            key: value
            for key, value in options.items()
            if not any(
                marker in value
                for marker in (
                    "付",
                    "欠",
                    "追回",
                    "退回",
                    "份额",
                    "俸",
                    "回购",
                    "归属",
                )
            )
        }
        self.assertFalse(missing_consequence)
        for body_key, body in bodies.items():
            stem = body_key.removeprefix("zg361comp.1.")
            for route in (1, 2, 3):
                option = options[f"zg361comp.1.{stem}.r{route}"].rstrip("。！")
                self.assertNotIn(option, body, body_key)


if __name__ == "__main__":
    unittest.main()
