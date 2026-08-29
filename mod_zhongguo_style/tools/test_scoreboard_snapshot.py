#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for immutable scoreboard and review-regression projections."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

from gen_scoreboard_snapshot import (
    MOD_ROOT,
    SLOT_COUNT,
    TOGGLE_POSITION,
    TOGGLE_SIZE,
    outputs,
    row_gui,
)


class ScoreboardSnapshotTests(unittest.TestCase):
    def test_exact_slots_and_no_live_score_reads(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode("utf-8-sig")
        for prefix in ("m", "r"):
            for slot in range(1, SLOT_COUNT + 1):
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_char", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_kpi", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_grade", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_title", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_promotion", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_pip", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_char", gui)
        self.assertNotIn("GetList('zg361_scoreboard_managed')", gui)
        self.assertNotIn("Character.MakeScope.Var('zg361_kpi')", gui)
        self.assertNotIn("Character.MakeScope.Var('zg361_rank')", gui)
        self.assertNotIn("Character.GetPrimaryTitle", gui)
        self.assertNotIn("GetScriptedGui('zg361_scoreboard_promotion_gui')", gui)
        self.assertNotIn("GetScriptedGui('zg361_scoreboard_pip_gui')", gui)
        self.assertNotIn("zg361_scoreboard_former_official", gui)
        self.assertIn(".Var('zg361_sb_m_01_title').Title", gui)
        self.assertIn("zg361_scoreboard_managed_shown_n", gui)
        self.assertIn("zg361_scoreboard_received_shown_n", gui)
        self.assertEqual(
            effects.count(
                "limit = { has_variable = zg361_scoreboard_slot_cursor "
                "var:zg361_scoreboard_slot_cursor ="
            ),
            SLOT_COUNT,
        )

    def test_checked_in_projection_is_current(self) -> None:
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in outputs().items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])

    def test_eighty_row_cap_is_explicitly_reported_as_shown_over_full(self) -> None:
        product_effects = (
            MOD_ROOT / "common" / "scripted_effects" / "zg361_effects.txt"
        ).read_text(encoding="utf-8-sig")
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        self.assertRegex(
            product_effects,
            re.compile(
                r"name\s*=\s*zg361_scoreboard_managed_shown_n\s+"
                r"value\s*=\s*\{\s*value\s*=\s*var:zg361_cohort_n\s+"
                r"max\s*=\s*80\s*\}",
                re.S,
            ),
        )
        self.assertRegex(
            product_effects,
            re.compile(
                r"ordered_in_list\s*=\s*\{.*?"
                r"list\s*=\s*zg361_scoreboard_candidates.*?"
                r"max\s*=\s*\{\s*"
                r"value\s*=\s*list_size:zg361_scoreboard_candidates\s+"
                r"max\s*=\s*80\s*\}",
                re.S,
            ),
        )
        self.assertNotIn(
            "var:zg361_scoreboard_managed_shown_n > 80", product_effects
        )
        for source in ("managed", "received"):
            shown = f"zg361_scoreboard_{source}_shown_n"
            total = f"zg361_scoreboard_{source}_n"
            self.assertRegex(gui, re.compile(rf"Var\('{shown}'\).*? / .*?Var\('{total}'\)"))
            shown_available = f"zg361_scoreboard_{source}_shown_available_gui"
            self.assertIn(f"GetScriptedGui('{shown_available}').IsShown", gui)
            self.assertRegex(
                gui,
                re.compile(
                    rf"Not\(GetScriptedGui\('{shown_available}'\).*?"
                    rf"Var\('{total}'\)"
                ),
            )

    def test_toggle_is_hud_aligned_and_suppressed_by_native_overlays(self) -> None:
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        width, height = TOGGLE_SIZE
        x, y = TOGGLE_POSITION
        self.assertIn(
            f'name = "zg361_scoreboard_toggle" size = {{ {width} {height} }} '
            f"parentanchor = top|right position = {{ {x} {y} }}",
            gui,
        )
        toggle = re.search(
            r'name = "zg361_scoreboard_toggle"(?P<body>.*?)\n\t\}', gui, re.S
        )
        self.assertIsNotNone(toggle)
        body = toggle.group("body") if toggle else ""
        for gate in (
            "Not(IsPauseMenuShown)",
            "IsDefaultGUIMode",
            "Not(IsGameViewOpen('struggle'))",
            "hide_ui_main_tabs",
            "Not(IsRightWindowOpen)",
            "Not(IsGameViewOpen('outliner'))",
            "Not(IsGameViewOpen('barbershop'))",
        ):
            self.assertIn(gate, body)
        self.assertIn("using = Animation_ShowHide_Quick", body)

        # CK3 lays this HUD out in a 1920x1080 reference space. The toggle's
        # right edge stays 60 units left of the screen, clearing the native
        # 50-unit main-tab rail; 1440p scales the same safe rectangle by 4/3.
        logical_width, logical_height = 1920, 1080
        left = logical_width + x - width
        right = logical_width + x
        top = y
        bottom = y + height
        self.assertEqual((left, right, top, bottom), (1680, 1860, 90, 134))
        self.assertGreaterEqual(logical_width - right, 50)
        self.assertGreaterEqual(left, 0)
        self.assertLessEqual(bottom, logical_height)
        scale_1440p = 2560 / logical_width
        self.assertEqual(
            tuple(round(value * scale_1440p) for value in (left, right, top, bottom)),
            (2240, 2480, 120, 179),
        )

    def test_all_interactive_controls_keep_the_modal_contract(self) -> None:
        gui = outputs()[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode(
            "utf-8-sig"
        )
        toggle = re.search(
            r'name = "zg361_scoreboard_toggle"(?P<body>.*?)\n\t\}', gui, re.S
        )
        self.assertIsNotNone(toggle)
        self.assertEqual(
            (toggle.group("body") if toggle else "").count("button_standard = {"),
            3,
        )
        toggle_body = toggle.group("body") if toggle else ""
        self.assertIn("zg361_mechanism_ledger_available_gui", toggle_body)
        self.assertIn(
            "GetVariableSystem.Set('zg361_scoreboard_tab', 'system')",
            toggle_body,
        )
        self.assertIn(
            "Not(GetScriptedGui('zg361_scoreboard_managed_available_gui')",
            toggle_body,
        )
        self.assertIn(
            "Not(GetScriptedGui('zg361_scoreboard_received_available_gui')",
            toggle_body,
        )
        self.assertEqual(gui.count("button_tertiary = {"), SLOT_COUNT * 2)
        self.assertEqual(
            gui.count('onclick = "[DefaultOnCharacterClick(Character.GetID)]"'),
            SLOT_COUNT * 2,
        )
        # Every row opens the frozen character, then dismisses the modal.
        row_pattern = re.compile(
            r"button_tertiary\s*=\s*\{.*?"
            r"onclick\s*=\s*\"\[DefaultOnCharacterClick\(Character.GetID\)\]\".*?"
            r"onclick\s*=\s*\"\[GetVariableSystem.Clear\('zg361_scoreboard_open'\)\]\"",
            re.S,
        )
        self.assertEqual(len(row_pattern.findall(gui)), SLOT_COUNT * 2)
        for tab in ("managed", "received", "system"):
            self.assertIn(
                f"onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', '{tab}')]\"",
                gui,
            )
            self.assertIn(
                f"down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', '{tab}')]\"",
                gui,
            )
        self.assertIn(
            'button_normal = { size = { 100% 100% } onclick = '
            '"[GetVariableSystem.Clear(\'zg361_scoreboard_open\')]" '
            'shortcut = close_window }',
            gui,
        )
        self.assertRegex(
            gui,
            re.compile(
                r'blockoverride\s+"button_close"\s*\{.*?'
                r"GetVariableSystem.Clear\('zg361_scoreboard_open'\).*?"
                r'shortcut\s*=\s*close_window',
                re.S,
            ),
        )
        self.assertNotIn('shortcut = "close_window"', gui)
        modal = re.search(
            r'name = "zg361_scoreboard_modal"(?P<body>.*?)\n\t\twidget = \{',
            gui,
            re.S,
        )
        self.assertIsNotNone(modal)
        self.assertIn(
            "GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown",
            modal.group("body") if modal else "",
        )

    def test_row_content_cannot_intercept_the_character_button(self) -> None:
        # The whole row is the button.  Every rendered leaf must pass pointer
        # input through to it; otherwise clicking the visible name/KPI/grade
        # only shows a tooltip and never executes DefaultOnCharacterClick.
        row = row_gui("m", 1)
        interactive_leaves = [
            line
            for line in row
            if "text_single = {" in line or "portrait_head_small = {" in line
        ]
        self.assertEqual(len(interactive_leaves), 12)
        for line in interactive_leaves:
            self.assertIn("alwaystransparent = yes", line)
        portrait = next(line for line in interactive_leaves if "portrait_head_small" in line)
        self.assertIn('blockoverride "portrait_button"', portrait)


def _calibrate_demote_fixture(rows: list[dict[str, int | bool]]) -> bool:
    """Mirror the CK3 selector: freeze both real candidates, then swap once."""
    demotable = [row for row in rows if row["grade"] == 2 and not row["newcomer"]]
    rescuable = [row for row in rows if row["grade"] == 1]
    if not demotable or not rescuable:
        return False
    demote = max(demotable, key=lambda row: int(row["rank"]))
    rescue = min(rescuable, key=lambda row: int(row["rank"]))
    rescue["grade"] = 2
    demote["grade"] = 1
    return True


class ReviewRegressionTests(unittest.TestCase):
    def test_calibration_c_all_newcomer_fixture_is_noop(self) -> None:
        rows = [
            {"rank": 1, "grade": 3, "newcomer": True},
            {"rank": 2, "grade": 2, "newcomer": True},
            {"rank": 3, "grade": 2, "newcomer": True},
        ]
        before = [dict(row) for row in rows]
        self.assertFalse(_calibrate_demote_fixture(rows))
        self.assertEqual(rows, before)

    def test_calibration_c_mixed_fixture_is_atomic_and_protects_newcomer(self) -> None:
        rows = [
            {"rank": 7, "grade": 2, "newcomer": True},
            {"rank": 8, "grade": 2, "newcomer": False},
            {"rank": 9, "grade": 1, "newcomer": False},
        ]
        counts_before = {grade: sum(row["grade"] == grade for row in rows) for grade in (1, 2, 3)}
        self.assertTrue(_calibrate_demote_fixture(rows))
        counts_after = {grade: sum(row["grade"] == grade for row in rows) for grade in (1, 2, 3)}
        self.assertEqual(counts_after, counts_before)
        self.assertEqual(rows[0]["grade"], 2)
        self.assertEqual(rows[1]["grade"], 1)
        self.assertEqual(rows[2]["grade"], 2)

    def test_product_and_live_fixture_use_the_atomic_contract(self) -> None:
        effects = (MOD_ROOT / "common" / "scripted_effects" / "zg361_effects.txt").read_text(
            encoding="utf-8-sig"
        )
        events = (MOD_ROOT / "events" / "zg361_events.txt").read_text(
            encoding="utf-8-sig"
        )
        fixture = (
            MOD_ROOT.parent
            / "tools"
            / "fixtures"
            / "zg361_acceptance"
            / "common"
            / "scripted_effects"
            / "zga_effects.txt"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("trigger = { zg361_can_calibrate_demote_trigger = yes }", events)
        self.assertIn("save_temporary_scope_as = zg361_calibration_demote_target", effects)
        self.assertIn("save_temporary_scope_as = zg361_calibration_rescue_target", effects)
        assignment_at = effects.index("zg361_assign_pending_grades_effect = yes")
        calibration_at = effects.index(
            "trigger_event = { id = zg361.10", assignment_at
        )
        self.assertNotIn(
            "remove_character_flag = zg361_newcomer_this_cycle",
            effects[assignment_at:calibration_at],
        )
        self.assertRegex(
            effects,
            re.compile(
                r"NOT\s*=\s*\{\s*has_variable\s*=\s*zg361_prev_merit_level\s*\}.*?"
                r"root\s*=\s*\{\s*has_character_flag\s*=\s*"
                r"zg361_review_baseline_initialized\s*\}.*?"
                r"add_character_flag\s*=\s*zg361_newcomer_this_cycle",
                re.S,
            ),
        )
        assignment = re.search(
            r"zg361_assign_pending_grades_effect\s*=\s*\{(?P<body>.*?)^\}",
            effects,
            re.M | re.S,
        )
        self.assertIsNotNone(assignment)
        assignment_body = assignment.group("body") if assignment else ""
        self.assertRegex(
            assignment_body,
            re.compile(
                r"every_in_list\s*=\s*\{\s*"
                r"list\s*=\s*zg361_cohort.*?"
                r"NOT\s*=\s*\{\s*has_character_flag\s*=\s*"
                r"zg361_newcomer_this_cycle\s*\}.*?"
                r"add_to_list\s*=\s*zg361_bottom_candidates",
                re.S,
            ),
        )
        self.assertRegex(
            assignment_body,
            re.compile(
                r"ordered_in_list\s*=\s*\{\s*"
                r"list\s*=\s*zg361_bottom_candidates.*?"
                r"max\s*=\s*list_size:zg361_bottom_candidates",
                re.S,
            ),
        )
        zero_based_gate = (
            "root.var:zg361_bottom_cursor < root.var:zg361_bottom_slots"
        )
        bottom_increment = (
            "root = { change_variable = { name = zg361_bottom_cursor add = 1 } }"
        )
        self.assertIn(zero_based_gate, assignment_body)
        self.assertIn(bottom_increment, assignment_body)
        self.assertLess(
            assignment_body.index(zero_based_gate),
            assignment_body.index(bottom_increment),
        )
        self.assertNotIn(
            "zg361_bottom_cursor <= root.var:zg361_bottom_slots",
            assignment_body,
        )
        settlement = re.search(
            r"zg361_apply_pending_grades_effect\s*=\s*\{(?P<body>.*?)^\}",
            effects,
            re.M | re.S,
        )
        self.assertIsNotNone(settlement)
        self.assertIn(
            "add_character_flag = zg361_review_baseline_initialized",
            settlement.group("body") if settlement else "",
        )
        self.assertRegex(
            settlement.group("body") if settlement else "",
            re.compile(
                r"zg361_apply_grade_effect\s*=\s*yes\s*"
                r"remove_character_flag\s*=\s*zg361_newcomer_this_cycle"
            ),
        )
        self.assertRegex(
            effects,
            re.compile(
                r"zg361_calibrate_demote_effect\s*=.*?"
                r"NOT\s*=\s*\{\s*has_character_flag\s*=\s*zg361_newcomer_this_cycle.*?"
                r"scope:zg361_calibration_rescue_target\s*=.*?pending_grade\s+value\s*=\s*2.*?"
                r"scope:zg361_calibration_demote_target\s*=.*?pending_grade\s+value\s*=\s*1",
                re.S,
            ),
        )
        fixture_regression = re.search(
            r"zga_verify_calibration_c_regressions_effect\s*=\s*\{"
            r"(?P<body>.*?)^\}",
            fixture,
            re.M | re.S,
        )
        self.assertIsNotNone(fixture_regression)
        fixture_body = fixture_regression.group("body") if fixture_regression else ""
        self.assertIn(
            "var:zga_all_new_protected_actual = var:zg361_cohort_n", fixture_body
        )
        self.assertEqual(fixture_body.count("zga_original_pending_grade"), 9)
        self.assertIn(
            "var:zga_mixed_35_actual = var:zga_mixed_35_actual_before",
            fixture_body,
        )
        self.assertIn(
            "var:zga_mixed_325_actual = var:zga_mixed_325_actual_before",
            fixture_body,
        )
        self.assertNotIn(
            "change_variable = { name = zg361_pending_35_n", fixture_body
        )
        self.assertNotIn(
            "change_variable = { name = zg361_pending_325_n", fixture_body
        )
        for marker in (
            "calibration_c_all_newcomer_noop",
            "calibration_c_mixed_newcomer_atomic_swap",
        ):
            self.assertIn(f"ZGA: TEST PASS {marker}", fixture)


if __name__ == "__main__":
    sys.exit(unittest.main())
