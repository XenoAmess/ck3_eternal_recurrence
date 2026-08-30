#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate immutable fixed-slot scoreboard records and their CK3 GUI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


MOD_ROOT = Path(__file__).resolve().parent.parent
SLOT_COUNT = 80
TOGGLE_SIZE = (180, 44)
TOGGLE_POSITION = (-60, 90)
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_scoreboard_snapshot.py\n"
FIELDS = (
    "char",
    "title",
    "kpi",
    "rank",
    "values",
    "grade",
    "streak",
    "promotion",
    "pip",
)


def encoded(body: str) -> bytes:
    return BOM + (HEADER + body.rstrip() + "\n").encode("utf-8")


def var(prefix: str, slot: int, field: str) -> str:
    return f"zg361_sb_{prefix}_{slot:02d}_{field}"


def render_effects() -> bytes:
    lines: list[str] = [
        "# Fixed slots freeze values on the viewing character. Character references remain clickable,",
        "# but title/KPI/rank/values/grade/streak/status never read later live state.",
        "",
    ]
    for prefix in ("m", "r"):
        lines.append(f"zg361_clear_scoreboard_{prefix}_slots_effect = {{")
        for slot in range(1, SLOT_COUNT + 1):
            for field in FIELDS:
                lines.append(f"\tremove_variable = {var(prefix, slot, field)}")
        lines.extend(["}", ""])

    lines.extend(
        [
            "# Current scope = ranked official; ROOT = reviewing manager.",
            "zg361_write_managed_scoreboard_slot_effect = {",
            "\tsave_temporary_scope_as = zg361_scoreboard_snapshot_entry",
            "\troot = {",
        ]
    )
    for slot in range(1, SLOT_COUNT + 1):
        keyword = "if" if slot == 1 else "else_if"
        lines.extend(
            [
                f"\t\t{keyword} = {{",
                f"\t\t\tlimit = {{ has_variable = zg361_scoreboard_slot_cursor var:zg361_scoreboard_slot_cursor = {slot} }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'char')} value = scope:zg361_scoreboard_snapshot_entry }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'title')} value = scope:zg361_scoreboard_snapshot_entry.primary_title }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'kpi')} value = scope:zg361_scoreboard_snapshot_entry.var:zg361_kpi }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'rank')} value = scope:zg361_scoreboard_snapshot_entry.var:zg361_rank }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'values')} value = scope:zg361_scoreboard_snapshot_entry.var:zg361_values }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'grade')} value = 3.5 }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'streak')} value = 0 }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'promotion')} value = 0 }}",
                f"\t\t\tset_variable = {{ name = {var('m', slot, 'pip')} value = 0 }}",
                "\t\t\tif = {",
                "\t\t\t\tlimit = { scope:zg361_scoreboard_snapshot_entry.var:zg361_last_grade = 3 }",
                f"\t\t\t\tset_variable = {{ name = {var('m', slot, 'grade')} value = 3.75 }}",
                "\t\t\t\tif = {",
                "\t\t\t\t\tlimit = { scope:zg361_scoreboard_snapshot_entry = { has_variable = zg361_streak_top } }",
                f"\t\t\t\t\tset_variable = {{ name = {var('m', slot, 'streak')} value = scope:zg361_scoreboard_snapshot_entry.var:zg361_streak_top }}",
                "\t\t\t\t}",
                "\t\t\t}",
                "\t\t\telse_if = {",
                "\t\t\t\tlimit = { scope:zg361_scoreboard_snapshot_entry.var:zg361_last_grade = 1 }",
                f"\t\t\t\tset_variable = {{ name = {var('m', slot, 'grade')} value = 3.25 }}",
                "\t\t\t\tif = {",
                "\t\t\t\t\tlimit = { scope:zg361_scoreboard_snapshot_entry = { has_variable = zg361_streak_bottom } }",
                f"\t\t\t\t\tset_variable = {{ name = {var('m', slot, 'streak')} value = scope:zg361_scoreboard_snapshot_entry.var:zg361_streak_bottom }}",
                "\t\t\t\t}",
                "\t\t\t}",
                "\t\t\tif = {",
                "\t\t\t\tlimit = { scope:zg361_scoreboard_snapshot_entry = { has_character_modifier = zg361_promotion_track } }",
                f"\t\t\t\tset_variable = {{ name = {var('m', slot, 'promotion')} value = 1 }}",
                "\t\t\t}",
                "\t\t\tif = {",
                "\t\t\t\tlimit = { scope:zg361_scoreboard_snapshot_entry = { has_character_modifier = zg361_pip } }",
                f"\t\t\t\tset_variable = {{ name = {var('m', slot, 'pip')} value = 1 }}",
                "\t\t\t}",
                "\t\t}",
            ]
        )
    lines.extend(["\t}", "}", ""])

    lines.extend(
        [
            "# Current scope = player official; scope:zg361_scoreboard_source = reviewing manager.",
            "zg361_copy_received_scoreboard_slots_effect = {",
            "\tzg361_clear_scoreboard_r_slots_effect = yes",
        ]
    )
    for slot in range(1, SLOT_COUNT + 1):
        lines.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ scope:zg361_scoreboard_source = {{ has_variable = {var('m', slot, 'char')} }} }}",
            ]
        )
        for field in FIELDS:
            lines.append(
                f"\t\tset_variable = {{ name = {var('r', slot, field)} value = "
                f"scope:zg361_scoreboard_source.var:{var('m', slot, field)} }}"
            )
        lines.append("\t}")
    lines.extend(["}", ""])

    def append_case_slot_update(
        *, effect_name: str, comment: str, grade: str, streak: str, pip: int
    ) -> None:
        """Update only the frozen owner/cycle copy of the current subject's case."""

        lines.extend(
            [
                comment,
                f"{effect_name} = {{",
                "\tsave_temporary_scope_as = zg361_scoreboard_case_entry",
                "\tvar:zg361_result_case_owner = {",
            ]
        )
        for slot in range(1, SLOT_COUNT + 1):
            lines.extend(
                [
                    "\t\tif = {",
                    "\t\t\tlimit = {",
                    "\t\t\t\thas_variable = zg361_scoreboard_managed_cycle_serial",
                    "\t\t\t\tvar:zg361_scoreboard_managed_cycle_serial = scope:zg361_scoreboard_case_entry.var:zg361_result_cycle_serial",
                    f"\t\t\t\thas_variable = {var('m', slot, 'char')}",
                    f"\t\t\t\tvar:{var('m', slot, 'char')} = scope:zg361_scoreboard_case_entry",
                    "\t\t\t}",
                    f"\t\t\tset_variable = {{ name = {var('m', slot, 'grade')} value = {grade} }}",
                    f"\t\t\tset_variable = {{ name = {var('m', slot, 'streak')} value = {streak} }}",
                    f"\t\t\tset_variable = {{ name = {var('m', slot, 'pip')} value = {pip} }}",
                    "\t\t}",
                ]
            )
        lines.extend(["\t}"])

        # Only the current player subject owns a received mirror.  Updating it
        # directly avoids enumerating whoever happens to be the owner's current
        # vassal after a transfer.
        for slot in range(1, SLOT_COUNT + 1):
            lines.extend(
                [
                    "\tif = {",
                    "\t\tlimit = {",
                    "\t\t\thas_variable = zg361_scoreboard_received_owner",
                    "\t\t\tvar:zg361_scoreboard_received_owner = var:zg361_result_case_owner",
                    "\t\t\thas_variable = zg361_scoreboard_received_cycle_serial",
                    "\t\t\tvar:zg361_scoreboard_received_cycle_serial = var:zg361_result_cycle_serial",
                    f"\t\t\thas_variable = {var('r', slot, 'char')}",
                    f"\t\t\tvar:{var('r', slot, 'char')} = scope:zg361_scoreboard_case_entry",
                    "\t\t}",
                    f"\t\tset_variable = {{ name = {var('r', slot, 'grade')} value = {grade} }}",
                    f"\t\tset_variable = {{ name = {var('r', slot, 'streak')} value = {streak} }}",
                    f"\t\tset_variable = {{ name = {var('r', slot, 'pip')} value = {pip} }}",
                    "\t}",
                ]
            )
        lines.extend(["}", ""])

    append_case_slot_update(
        effect_name="zg361_update_settled_325_scoreboard_slots_effect",
        comment=(
            "# Current scope = player official after witnessed/acknowledged 3.25 settlement. "
            "Update only the frozen owner/cycle copies."
        ),
        grade="3.25",
        streak="scope:zg361_scoreboard_case_entry.var:zg361_streak_bottom",
        pip=1,
    )
    append_case_slot_update(
        effect_name="zg361_update_regraded_scoreboard_slots_effect",
        comment=(
            "# Current scope = successfully regraded official. Update only the frozen "
            "owner/cycle copies."
        ),
        grade="3.5",
        streak="0",
        pip=0,
    )
    return encoded("\n".join(lines))


def render_scripted_guis() -> bytes:
    lines: list[str] = []
    for source in ("managed", "received"):
        lines.extend(
            [
                f"zg361_scoreboard_{source}_shown_available_gui = {{",
                "\tscope = character",
                f"\tis_shown = {{ has_variable = zg361_scoreboard_{source}_shown_n }}",
                "}",
                "",
            ]
        )
    for prefix in ("m", "r"):
        for slot in range(1, SLOT_COUNT + 1):
            lines.extend(
                [
                    f"zg361_sb_{prefix}_{slot:02d}_available_gui = {{",
                    "\tscope = character",
                    f"\tis_shown = {{ has_variable = {var(prefix, slot, 'char')} }}",
                    "}",
                    "",
                    f"zg361_sb_{prefix}_{slot:02d}_title_available_gui = {{",
                    "\tscope = character",
                    f"\tis_shown = {{ has_variable = {var(prefix, slot, 'title')} }}",
                    "}",
                    "",
                    f"zg361_sb_{prefix}_{slot:02d}_promotion_gui = {{",
                    "\tscope = character",
                    f"\tis_shown = {{ has_variable = {var(prefix, slot, 'promotion')} var:{var(prefix, slot, 'promotion')} = 1 }}",
                    "}",
                    "",
                    f"zg361_sb_{prefix}_{slot:02d}_pip_gui = {{",
                    "\tscope = character",
                    f"\tis_shown = {{ has_variable = {var(prefix, slot, 'pip')} var:{var(prefix, slot, 'pip')} = 1 }}",
                    "}",
                    "",
                ]
            )
    return encoded("\n".join(lines))


def row_gui(prefix: str, slot: int) -> list[str]:
    available = f"zg361_sb_{prefix}_{slot:02d}_available_gui"
    title_available = f"zg361_sb_{prefix}_{slot:02d}_title_available_gui"
    promotion = f"zg361_sb_{prefix}_{slot:02d}_promotion_gui"
    pip = f"zg361_sb_{prefix}_{slot:02d}_pip_gui"
    slot_var = lambda field: var(prefix, slot, field)
    return [
        "button_tertiary = {",
        "\tsize = { 1120 68 }",
        "\tlayoutpolicy_horizontal = expanding",
        f"\tvisible = \"[GetScriptedGui('{available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"",
        f"\tdatacontext = \"[GetPlayer.MakeScope.Var('{slot_var('char')}').Char]\"",
        "\tonclick = \"[DefaultOnCharacterClick(Character.GetID)]\"",
        "\tonclick = \"[GetVariableSystem.Clear('zg361_scoreboard_open')]\"",
        "\tbackground = { using = Background_Area_Dark alpha = 0.6 }",
        "\tbackground = {",
        "\t\tvisible = \"[Character.IsPlayer]\"",
        "\t\ttexture = \"gfx/interface/colors/blue.dds\"",
        "\t\ttintcolor = { 0.55 0.72 1.0 0.35 }",
        "\t\tusing = Mask_Rough_Edges",
        "\t}",
        "\thbox = {",
        "\t\talwaystransparent = yes",
        "\t\tlayoutpolicy_horizontal = expanding",
        "\t\tspacing = 8",
        "\t\tmargin = { 8 4 }",
        f"\t\ttext_single = {{ alwaystransparent = yes min_width = 50 max_width = 50 text = \"[GetPlayer.MakeScope.Var('{slot_var('rank')}').GetValue|0]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        "\t\tportrait_head_small = { blockoverride \"portrait_button\" { alwaystransparent = yes } }",
        "\t\tvbox = {",
        "\t\t\talwaystransparent = yes min_width = 285 max_width = 285 layoutpolicy_vertical = expanding spacing = 1",
        "\t\t\ttext_single = { alwaystransparent = yes layoutpolicy_horizontal = expanding text = \"[Character.GetUINameNotMeNoTooltip]\" tooltip = \"[Character.GetUINameNotMeNoTooltip]\" default_format = \"#high\" align = nobaseline using = Font_Size_Medium fontsize_min = 12 autoresize = no }",
        f"\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[GetScriptedGui('{title_available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" datacontext = \"[GetPlayer.MakeScope.Var('{slot_var('title')}').Title]\" layoutpolicy_horizontal = expanding text = \"[Title.GetNameNoTierNoTooltip]\" default_format = \"#weak\" align = nobaseline using = Font_Size_Small fontsize_min = 10 autoresize = no }}",
        f"\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[Not(GetScriptedGui('{title_available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" layoutpolicy_horizontal = expanding text = \"zg361_scoreboard_dash\" default_format = \"#weak\" align = nobaseline using = Font_Size_Small fontsize_min = 10 autoresize = no }}",
        "\t\t}",
        f"\t\ttext_single = {{ alwaystransparent = yes min_width = 90 max_width = 90 text = \"[GetPlayer.MakeScope.Var('{slot_var('kpi')}').GetValue|1]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        f"\t\ttext_single = {{ alwaystransparent = yes min_width = 90 max_width = 90 text = \"[GetPlayer.MakeScope.Var('{slot_var('values')}').GetValue|0]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        f"\t\ttext_single = {{ alwaystransparent = yes min_width = 125 max_width = 125 text = \"[GetPlayer.MakeScope.Var('{slot_var('grade')}').GetValue|2]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        f"\t\ttext_single = {{ alwaystransparent = yes min_width = 95 max_width = 95 text = \"[GetPlayer.MakeScope.Var('{slot_var('streak')}').GetValue|0]\" align = center|nobaseline using = Font_Size_Medium }}",
        "\t\tvbox = {",
        "\t\t\talwaystransparent = yes min_width = 130 max_width = 130 layoutpolicy_vertical = expanding",
        f"\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[GetScriptedGui('{promotion}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_status_promotion\" align = center|nobaseline using = Font_Size_Small }}",
        f"\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[GetScriptedGui('{pip}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_status_pip\" align = center|nobaseline using = Font_Size_Small }}",
        f"\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[And(Not(GetScriptedGui('{promotion}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), Not(GetScriptedGui('{pip}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)))]\" text = \"zg361_scoreboard_dash\" default_format = \"#weak\" align = center|nobaseline using = Font_Size_Small }}",
        "\t\t}",
        "\t}",
        "}",
    ]


def tab_gui(prefix: str) -> list[str]:
    managed = prefix == "m"
    source = "managed" if managed else "received"
    shown_available = f"zg361_scoreboard_{source}_shown_available_gui"
    availability = (
        "zg361_scoreboard_managed_available_gui"
        if managed
        else "zg361_scoreboard_received_available_gui"
    )
    visible = (
        f"[And(GetScriptedGui('{availability}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End), "
        f"GetVariableSystem.HasValue('zg361_scoreboard_tab', '{source}'))]"
    )
    lines = [
        "vbox = {",
        "\tlayoutpolicy_horizontal = expanding",
        "\tlayoutpolicy_vertical = expanding",
        "\tspacing = 8",
        f"\tvisible = \"{visible}\"",
        "\thbox = {",
        "\t\tlayoutpolicy_horizontal = expanding spacing = 18 margin = { 18 0 }",
    ]
    if not managed:
        lines.extend(
            [
                "\t\ttext_single = { text = \"zg361_scoreboard_reviewer\" default_format = \"#weak\" align = nobaseline }",
                "\t\ttext_single = { text = \"[GetPlayer.MakeScope.Var('zg361_scoreboard_received_owner').Char.GetUINameNotMeNoTooltip]\" default_format = \"#high\" align = nobaseline }",
            ]
        )
    lines.extend(
        [
            "\t\ttext_single = { text = \"zg361_scoreboard_year\" default_format = \"#weak\" align = nobaseline }",
            f"\t\ttext_single = {{ text = \"[GetPlayer.MakeScope.Var('zg361_scoreboard_{source}_year').GetValue|0]\" default_format = \"#high\" align = nobaseline }}",
            "\t\ttext_single = { text = \"zg361_scoreboard_total\" default_format = \"#weak\" align = nobaseline }",
            f"\t\ttext_single = {{ visible = \"[GetScriptedGui('{shown_available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" raw_text = \"[GetPlayer.MakeScope.Var('zg361_scoreboard_{source}_shown_n').GetValue|0] / [GetPlayer.MakeScope.Var('zg361_scoreboard_{source}_n').GetValue|0]\" default_format = \"#high\" align = nobaseline }}",
            f"\t\ttext_single = {{ visible = \"[Not(GetScriptedGui('{shown_available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" text = \"[GetPlayer.MakeScope.Var('zg361_scoreboard_{source}_n').GetValue|0]\" default_format = \"#high\" align = nobaseline }}",
            "\t\texpand = {}",
        ]
    )
    for grade, field in (("375", "375_n"), ("35", "35_n"), ("325", "325_n")):
        lines.extend(
            [
                f"\t\ttext_single = {{ text = \"zg361_scoreboard_grade_{grade}\" align = nobaseline }}",
                f"\t\ttext_single = {{ text = \"[GetPlayer.MakeScope.Var('zg361_scoreboard_{source}_{field}').GetValue|0]\" default_format = \"#high\" align = nobaseline }}",
            ]
        )
    lines.extend(
        [
            "\t}",
            "\tdivider_light = { layoutpolicy_horizontal = expanding }",
            "\tzg361_scoreboard_columns = {}",
            "\tscrollbox = {",
            "\t\tlayoutpolicy_horizontal = expanding layoutpolicy_vertical = expanding",
            "\t\tblockoverride \"scrollbox_content\" {",
            "\t\t\tvbox = { layoutpolicy_horizontal = expanding spacing = 3",
        ]
    )
    for slot in range(1, SLOT_COUNT + 1):
        lines.extend("\t\t\t\t" + line for line in row_gui(prefix, slot))
    lines.extend(["\t\t\t}", "\t\t}", "\t}", "}"])
    return lines


def ledger_tab_gui() -> list[str]:
    labels = (
        ("evidence", "zg361_ledger_evidence"),
        ("trust", "zg361_ledger_trust"),
        ("admin_load", "zg361_ledger_admin_load"),
        ("appeal_risk", "zg361_ledger_appeal_risk"),
        ("delivery", "zg361_ledger_delivery"),
        ("stability", "zg361_ledger_stability"),
        ("tech_debt", "zg361_ledger_tech_debt"),
        ("data_quality", "zg361_ledger_data_quality"),
        ("burnout", "zg361_ledger_burnout"),
        ("talent", "zg361_ledger_talent"),
        ("hc_pressure", "zg361_ledger_hc_pressure"),
        ("pay_debt", "zg361_ledger_pay_debt"),
        ("policy_debt", "zg361_ledger_policy_debt"),
        ("budget_pressure", "zg361_ledger_budget_pressure"),
    )
    lines = [
        "vbox = {",
        "\tlayoutpolicy_horizontal = expanding layoutpolicy_vertical = expanding spacing = 14 margin = { 34 24 }",
        "\tvisible = \"[And(GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End), GetVariableSystem.HasValue('zg361_scoreboard_tab', 'system'))]\"",
        "\ttext_label_center = { layoutpolicy_horizontal = expanding text = \"zg361_ledger_title\" default_format = \"#high\" using = Font_Size_Large }",
        "\thbox = { layoutpolicy_horizontal = expanding spacing = 12",
        "\t\ttext_single = { text = \"zg361_ledger_configured\" default_format = \"#weak\" align = nobaseline }",
        "\t\ttext_single = { raw_text = \"[GetPlayer.MakeScope.Var('zg361_mechanism_configured_n').GetValue|0] / 361\" default_format = \"#high\" align = nobaseline }",
        "\t\texpand = {}",
        "\t\ttext_single = { text = \"zg361_ledger_checksum\" default_format = \"#weak\" align = nobaseline }",
        "\t\ttext_single = { text = \"[GetPlayer.MakeScope.Var('zg361_mechanism_checksum').GetValue|0]\" default_format = \"#high\" align = nobaseline }",
        "\t}",
        "\tdivider_light = { layoutpolicy_horizontal = expanding }",
        "\ttext_label_center = { layoutpolicy_horizontal = expanding text = \"zg361_ledger_explainer\" default_format = \"#weak\" using = Font_Size_Medium }",
        "\thbox = {",
        "\t\tlayoutpolicy_horizontal = expanding layoutpolicy_vertical = expanding spacing = 28",
    ]
    for column in (labels[:7], labels[7:]):
        lines.append("\t\tvbox = { layoutpolicy_horizontal = expanding layoutpolicy_vertical = expanding spacing = 6")
        for ledger, label in column:
            lines.extend(
                [
                    "\t\t\thbox = { layoutpolicy_horizontal = expanding spacing = 12 margin = { 12 6 }",
                    f"\t\t\t\ttext_single = {{ min_width = 280 text = \"{label}\" default_format = \"#weak\" align = nobaseline }}",
                    "\t\t\t\texpand = {}",
                    f"\t\t\t\ttext_single = {{ text = \"[GetPlayer.MakeScope.Var('zg361_org_{ledger}').GetValue|0]\" default_format = \"#high\" align = nobaseline }}",
                    "\t\t\t}",
                ]
            )
        lines.append("\t\t}")
    lines.extend(["\t}", "\ttext_label_center = { layoutpolicy_horizontal = expanding text = \"zg361_ledger_hint\" default_format = \"#weak\" using = Font_Size_Small }", "}"])
    return lines


def render_gui() -> bytes:
    toggle_width, toggle_height = TOGGLE_SIZE
    toggle_x, toggle_y = TOGGLE_POSITION
    toggle_hud_gate = (
        "[And(And(And(And(And(And(Not(IsPauseMenuShown), IsDefaultGUIMode), "
        "Not(IsGameViewOpen('struggle'))), "
        "Not(GreaterThan_CFixedPoint(GetPlayer.MakeScope.Var('hide_ui_main_tabs').GetValue, '(CFixedPoint)0'))), "
        "Not(IsRightWindowOpen)), Not(IsGameViewOpen('outliner'))), "
        "Not(IsGameViewOpen('barbershop')))]"
    )
    lines: list[str] = [
        "types ZG361ScoreboardTypes",
        "{",
        "\ttype zg361_scoreboard_columns = hbox {",
        "\t\tlayoutpolicy_horizontal = expanding spacing = 8 margin = { 8 0 }",
        "\t\ttext_single = { min_width = 50 max_width = 50 text = \"zg361_scoreboard_col_rank\" default_format = \"#weak\" align = center|nobaseline }",
        "\t\tspacer = { size = { 58 1 } }",
        "\t\ttext_single = { min_width = 285 max_width = 285 text = \"zg361_scoreboard_col_official\" default_format = \"#weak\" align = nobaseline }",
        "\t\ttext_single = { min_width = 90 max_width = 90 text = \"zg361_scoreboard_col_kpi\" default_format = \"#weak\" align = center|nobaseline }",
        "\t\ttext_single = { min_width = 90 max_width = 90 text = \"zg361_scoreboard_col_values\" default_format = \"#weak\" align = center|nobaseline }",
        "\t\ttext_single = { min_width = 125 max_width = 125 text = \"zg361_scoreboard_col_grade\" default_format = \"#weak\" align = center|nobaseline }",
        "\t\ttext_single = { min_width = 95 max_width = 95 text = \"zg361_scoreboard_col_streak\" default_format = \"#weak\" align = center|nobaseline }",
        "\t\ttext_single = { min_width = 130 max_width = 130 text = \"zg361_scoreboard_col_status\" default_format = \"#weak\" align = center|nobaseline }",
        "\t}",
        "}",
        "",
        "window = {",
        "\tname = \"zg361_scoreboard_window\"",
        "\tsize = { 100% 100% } layer = middle",
        "\tvisible = \"[GetPlayer.IsValid]\" alwaystransparent = yes",
        "\twidget = {",
        f"\t\tname = \"zg361_scoreboard_toggle\" size = {{ {toggle_width} {toggle_height} }} parentanchor = top|right position = {{ {toggle_x} {toggle_y} }}",
        f"\t\tvisible = \"{toggle_hud_gate}\" using = Animation_ShowHide_Quick",
        f"\t\tbutton_standard = {{ size = {{ {toggle_width} {toggle_height} }} visible = \"[GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_open\" onclick = \"[GetVariableSystem.Toggle('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'managed')]\" down = \"[GetVariableSystem.Exists('zg361_scoreboard_open')]\" tooltip = \"zg361_scoreboard_open_tooltip\" }}",
        f"\t\tbutton_standard = {{ size = {{ {toggle_width} {toggle_height} }} visible = \"[And(Not(GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" text = \"zg361_scoreboard_open\" onclick = \"[GetVariableSystem.Toggle('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'received')]\" down = \"[GetVariableSystem.Exists('zg361_scoreboard_open')]\" tooltip = \"zg361_scoreboard_open_tooltip\" }}",
        f"\t\tbutton_standard = {{ size = {{ {toggle_width} {toggle_height} }} visible = \"[And(And(Not(GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), Not(GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))), GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" text = \"zg361_scoreboard_open\" onclick = \"[GetVariableSystem.Toggle('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'system')]\" down = \"[GetVariableSystem.Exists('zg361_scoreboard_open')]\" tooltip = \"zg361_scoreboard_open_tooltip\" }}",
        "\t}",
        "\twidget = {",
        "\t\tname = \"zg361_scoreboard_modal\" size = { 100% 100% }",
        "\t\tvisible = \"[And(GetVariableSystem.Exists('zg361_scoreboard_open'), Or(Or(GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End), GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)))]\"",
        "\t\talwaystransparent = no filter_mouse = all using = Background_Full_Dim using = Animation_ShowHide_Quick",
        "\t\tbutton_normal = { size = { 100% 100% } onclick = \"[GetVariableSystem.Clear('zg361_scoreboard_open')]\" shortcut = close_window }",
        "\t\twidget = {",
        "\t\t\tname = \"zg361_scoreboard_panel\" size = { 1220 820 } parentanchor = center widgetanchor = center alwaystransparent = no filter_mouse = all using = Window_Background using = Window_Decoration_Spike",
        "\t\t\tvbox = {",
        "\t\t\t\tusing = Window_Margins spacing = 8",
        "\t\t\t\theader_pattern = { layoutpolicy_horizontal = expanding blockoverride \"header_text\" { text = \"zg361_scoreboard_title\" } blockoverride \"button_close\" { onclick = \"[GetVariableSystem.Clear('zg361_scoreboard_open')]\" shortcut = close_window } }",
        "\t\t\t\thbox = { layoutpolicy_horizontal = expanding",
        "\t\t\t\t\tbutton_tab = { layoutpolicy_horizontal = expanding visible = \"[GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_tab_managed\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'managed')]\" down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', 'managed')]\" }",
        "\t\t\t\t\tbutton_tab = { layoutpolicy_horizontal = expanding visible = \"[GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_tab_received\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'received')]\" down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', 'received')]\" }",
        "\t\t\t\t\tbutton_tab = { layoutpolicy_horizontal = expanding visible = \"[GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_tab_system\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'system')]\" down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', 'system')]\" }",
        "\t\t\t\t}",
    ]
    lines.extend("\t\t\t\t" + line for line in tab_gui("m"))
    lines.extend("\t\t\t\t" + line for line in tab_gui("r"))
    lines.extend("\t\t\t\t" + line for line in ledger_tab_gui())
    lines.extend(
        [
            "\t\t\t\ttext_label_center = { layoutpolicy_horizontal = expanding text = \"zg361_scoreboard_hint\" default_format = \"#weak\" using = Font_Size_Small }",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    return encoded("\n".join(lines))


def outputs() -> dict[Path, bytes]:
    return {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_generated_scoreboard_snapshots.txt": render_effects(),
        MOD_ROOT / "common" / "scripted_guis" / "zg361_generated_scoreboard_slots.txt": render_scripted_guis(),
        MOD_ROOT / "gui" / "zg361_scoreboard.gui": render_gui(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    mismatches: list[str] = []
    for path, data in outputs().items():
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                mismatches.append(path.relative_to(MOD_ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        print("RED: scoreboard snapshot projections are stale:")
        for mismatch in mismatches:
            print(f"  - {mismatch}")
        return 1
    print(f"GREEN: {'checked' if args.check else 'generated'} {SLOT_COUNT} immutable scoreboard slots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
