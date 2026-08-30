#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate immutable fixed-slot scoreboard records and their CK3 GUI."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys


MOD_ROOT = Path(__file__).resolve().parent.parent
SLOT_COUNT = 80
TOGGLE_SIZE = (180, 44)
TOGGLE_POSITION = (-60, 90)
BOM = b"\xef\xbb\xbf"
HEADER = "# GENERATED FILE — edit tools/gen_scoreboard_snapshot.py\n"
DETAIL_PAGES = ("facts", "peer", "quota", "audit")
SENSITIVE_RECEIVED_FIELDS = frozenset(
    {"evaluator_id", "raw_comment", "recusal_identity"}
)


@dataclass(frozen=True)
class FieldSpec:
    """One immutable scoreboard field and its real product source."""

    name: str
    source_var: str
    page: str
    kind: str = "number"
    mutable: bool = False


BASE_FIELDS = (
    FieldSpec("char", "", "summary", "character"),
    FieldSpec("title", "", "summary", "title"),
    FieldSpec("kpi", "zg361_kpi", "summary"),
    FieldSpec("rank", "zg361_rank", "summary"),
    FieldSpec("values", "zg361_values", "summary"),
    FieldSpec("grade", "zg361_last_grade", "summary", "grade"),
    FieldSpec("streak", "", "summary"),
    FieldSpec("promotion", "", "summary"),
    FieldSpec("pip", "", "summary"),
)

# Only variables already written by zg361_effects.txt are projected.  B1 peer,
# conflict and recusal data deliberately remain unavailable until their runtime
# exists; the GUI must never manufacture those records from policy markers.
CASE_FIELDS = (
    FieldSpec("case_owner", "zg361_result_case_owner", "facts", "character"),
    FieldSpec("cycle_serial", "zg361_result_cycle_serial", "facts"),
    FieldSpec("case_serial", "zg361_result_case_serial", "facts"),
    FieldSpec("kpi_frozen", "zg361_result_kpi_frozen", "facts"),
    FieldSpec("values_frozen", "zg361_result_values_frozen", "facts"),
    FieldSpec("evidence_governance", "zg361_result_evidence_governance", "facts"),
    FieldSpec("evidence_capability", "zg361_result_evidence_capability", "facts"),
    FieldSpec("evidence_growth", "zg361_result_evidence_growth", "facts"),
    FieldSpec("evidence_superior", "zg361_result_evidence_superior", "facts"),
    FieldSpec("evidence_values", "zg361_result_evidence_values", "facts"),
    FieldSpec("evidence_collaboration", "zg361_result_evidence_collaboration", "facts"),
    FieldSpec("evidence_jingcha", "zg361_result_evidence_jingcha", "facts"),
    FieldSpec("evidence_organization", "zg361_result_evidence_organization", "facts"),
    FieldSpec("cohort_n", "zg361_result_cohort_n_frozen", "quota"),
    FieldSpec("absolute_grade", "zg361_result_absolute_grade", "quota", "grade"),
    FieldSpec("final_grade", "zg361_result_grade", "quota", "grade", True),
    FieldSpec("grade_reason", "zg361_result_grade_reason", "quota"),
    FieldSpec("case_state", "zg361_result_case_state", "audit", "number", True),
    FieldSpec(
        "delivery_method", "zg361_result_delivery_method", "audit", "number", True
    ),
    FieldSpec("appeal_open", "zg361_result_appeal_open", "audit", "number", True),
    FieldSpec(
        "appeal_outcome", "zg361_result_appeal_outcome", "audit", "number", True
    ),
    FieldSpec(
        "settlement_serial",
        "zg361_result_settlement_posted_serial",
        "audit",
        "number",
        True,
    ),
    FieldSpec(
        "refund_serial", "zg361_result_refund_posted_serial", "audit", "number", True
    ),
    FieldSpec(
        "salary_cut_active", "zg361_result_salary_cut_active", "audit", "number", True
    ),
    FieldSpec(
        "treasury_paid", "zg361_result_treasury_paid", "audit", "number", True
    ),
    FieldSpec("gold_paid", "zg361_result_gold_paid", "audit", "number", True),
    FieldSpec("merit_paid", "zg361_result_merit_paid", "audit", "number", True),
    FieldSpec(
        "treasury_refunded",
        "zg361_result_treasury_refunded",
        "audit",
        "number",
        True,
    ),
    FieldSpec(
        "gold_refunded", "zg361_result_gold_refunded", "audit", "number", True
    ),
    FieldSpec(
        "merit_refunded", "zg361_result_merit_refunded", "audit", "number", True
    ),
)
MUTABLE_CASE_FIELDS = tuple(field for field in CASE_FIELDS if field.mutable)
FIELDS = tuple(field.name for field in BASE_FIELDS)


def fixed_var(prefix: str, field: str) -> str:
    return f"zg361_sb_{prefix}_{field}"


def encoded(body: str) -> bytes:
    return BOM + (HEADER + body.rstrip() + "\n").encode("utf-8")


def var(prefix: str, slot: int, field: str) -> str:
    return f"zg361_sb_{prefix}_{slot:02d}_{field}"


def append_field_copy(
    lines: list[str],
    *,
    indent: str,
    destination: str,
    field: FieldSpec,
    source_scope: str = "",
) -> None:
    """Copy one existing variable without turning absence into a fabricated zero."""

    has_source = (
        f"{source_scope} = {{ has_variable = {field.source_var} }}"
        if source_scope
        else f"has_variable = {field.source_var}"
    )
    source_value = (
        f"{source_scope}.var:{field.source_var}"
        if source_scope
        else f"var:{field.source_var}"
    )
    if field.kind != "grade":
        lines.append(
            f"{indent}if = {{ limit = {{ {has_source} }} "
            f"set_variable = {{ name = {destination} value = {source_value} }} }}"
        )
        return
    lines.extend(
        [
            f"{indent}if = {{",
            f"{indent}\tlimit = {{ {has_source} }}",
            f"{indent}\tset_variable = {{ name = {destination} value = 3.5 }}",
            f"{indent}\tif = {{",
            f"{indent}\t\tlimit = {{ {source_value} = 3 }}",
            f"{indent}\t\tset_variable = {{ name = {destination} value = 3.75 }}",
            f"{indent}\t}}",
            f"{indent}\telse_if = {{",
            f"{indent}\t\tlimit = {{ {source_value} = 1 }}",
            f"{indent}\t\tset_variable = {{ name = {destination} value = 3.25 }}",
            f"{indent}\t}}",
            f"{indent}}}",
        ]
    )


def render_effects() -> bytes:
    lines: list[str] = [
        "# Fixed slots freeze values on the viewing character. Character references remain clickable,",
        "# but title/KPI/rank/values/grade/streak/status never read later live state.",
        "",
        "# One selected-case buffer backs all four internal detail pages.",
        "zg361_clear_scoreboard_detail_effect = {",
    ]
    for field in ("valid", "source", "slot", "char", "title", "rank"):
        lines.append(f"\tremove_variable = {fixed_var('detail', field)}")
    for field in CASE_FIELDS:
        lines.append(f"\tremove_variable = {fixed_var('detail', field.name)}")
    lines.extend(
        [
            "}",
            "",
            "# Received detail is a self-only allowlist, never a second copy of the team's case files.",
            "zg361_clear_scoreboard_self_effect = {",
        ]
    )
    for field in ("char", "title", "rank"):
        lines.append(f"\tremove_variable = {fixed_var('self', field)}")
    for field in CASE_FIELDS:
        lines.append(f"\tremove_variable = {fixed_var('self', field.name)}")
    lines.extend(["}", ""])

    for prefix in ("m", "r"):
        lines.append(f"zg361_clear_scoreboard_{prefix}_slots_effect = {{")
        lines.append("\tzg361_clear_scoreboard_detail_effect = yes")
        if prefix == "r":
            lines.append("\tzg361_clear_scoreboard_self_effect = yes")
        for slot in range(1, SLOT_COUNT + 1):
            for field in BASE_FIELDS:
                lines.append(f"\tremove_variable = {var(prefix, slot, field.name)}")
            if prefix == "m":
                for field in CASE_FIELDS:
                    lines.append(f"\tremove_variable = {var(prefix, slot, field.name)}")
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
            ]
        )
        for field in CASE_FIELDS:
            append_field_copy(
                lines,
                indent="\t\t\t",
                destination=var("m", slot, field.name),
                field=field,
                source_scope="scope:zg361_scoreboard_snapshot_entry",
            )
        lines.append("\t\t}")
    lines.extend(["\t}", "}", ""])

    lines.extend(
        [
            "# Current scope = player official; scope:zg361_scoreboard_source = reviewing manager.",
            "zg361_copy_received_scoreboard_slots_effect = {",
            "\tzg361_clear_scoreboard_r_slots_effect = yes",
            "\tsave_temporary_scope_as = zg361_scoreboard_self_entry",
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\thas_variable = zg361_result_case_owner",
            "\t\t\thas_variable = zg361_result_cycle_serial",
            "\t\t\thas_variable = zg361_result_case_serial",
            "\t\t\tscope:zg361_scoreboard_source = { has_variable = zg361_scoreboard_managed_cycle_serial }",
            "\t\t}",
            "\t\tif = {",
            "\t\t\tlimit = { var:zg361_result_case_owner = scope:zg361_scoreboard_source }",
            "\t\t\tif = {",
            "\t\t\t\tlimit = { scope:zg361_scoreboard_source = { var:zg361_scoreboard_managed_cycle_serial = root.var:zg361_result_cycle_serial } }",
            f"\t\t\t\tset_variable = {{ name = {fixed_var('self', 'char')} value = scope:zg361_scoreboard_self_entry }}",
            f"\t\t\t\tset_variable = {{ name = {fixed_var('self', 'title')} value = scope:zg361_scoreboard_self_entry.primary_title }}",
            "\t\t\t\tif = {",
            "\t\t\t\t\tlimit = { has_variable = zg361_result_rank_frozen }",
            f"\t\t\t\t\tset_variable = {{ name = {fixed_var('self', 'rank')} value = var:zg361_result_rank_frozen }}",
            "\t\t\t\t}",
        ]
    )
    for field in CASE_FIELDS:
        append_field_copy(
            lines,
            indent="\t\t\t\t",
            destination=fixed_var("self", field.name),
            field=field,
        )
    lines.extend(["\t\t\t}", "\t\t}", "\t}"])
    for slot in range(1, SLOT_COUNT + 1):
        lines.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ scope:zg361_scoreboard_source = {{ has_variable = {var('m', slot, 'char')} }} }}",
            ]
        )
        for field in BASE_FIELDS:
            lines.append(
                f"\t\tset_variable = {{ name = {var('r', slot, field.name)} value = "
                f"scope:zg361_scoreboard_source.var:{var('m', slot, field.name)} }}"
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
                ]
            )
            for field in MUTABLE_CASE_FIELDS:
                append_field_copy(
                    lines,
                    indent="\t\t\t",
                    destination=var("m", slot, field.name),
                    field=field,
                    source_scope="scope:zg361_scoreboard_case_entry",
                )
            lines.append("\t\t}")
        lines.extend(
            [
                "\t\tif = {",
                "\t\t\tlimit = {",
                f"\t\t\t\thas_variable = {fixed_var('detail', 'valid')}",
                f"\t\t\t\thas_variable = {fixed_var('detail', 'char')}",
                f"\t\t\t\tvar:{fixed_var('detail', 'char')} = scope:zg361_scoreboard_case_entry",
                f"\t\t\t\thas_variable = {fixed_var('detail', 'cycle_serial')}",
                f"\t\t\t\tvar:{fixed_var('detail', 'cycle_serial')} = scope:zg361_scoreboard_case_entry.var:zg361_result_cycle_serial",
                "\t\t\t}",
            ]
        )
        for field in MUTABLE_CASE_FIELDS:
            append_field_copy(
                lines,
                indent="\t\t\t",
                destination=fixed_var("detail", field.name),
                field=field,
                source_scope="scope:zg361_scoreboard_case_entry",
            )
        lines.extend(["\t\t}", "\t}"])

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
        lines.extend(
            [
                "\tif = {",
                "\t\tlimit = {",
                f"\t\t\thas_variable = {fixed_var('self', 'char')}",
                f"\t\t\tvar:{fixed_var('self', 'char')} = scope:zg361_scoreboard_case_entry",
                "\t\t\thas_variable = zg361_scoreboard_received_cycle_serial",
                "\t\t\tvar:zg361_scoreboard_received_cycle_serial = var:zg361_result_cycle_serial",
                "\t\t}",
            ]
        )
        for field in MUTABLE_CASE_FIELDS:
            append_field_copy(
                lines,
                indent="\t\t",
                destination=fixed_var("self", field.name),
                field=field,
                source_scope="scope:zg361_scoreboard_case_entry",
            )
        lines.extend(["\t}"])
        lines.extend(
            [
                "\tif = {",
                "\t\tlimit = {",
                f"\t\t\thas_variable = {fixed_var('detail', 'valid')}",
                f"\t\t\thas_variable = {fixed_var('detail', 'source')}",
                f"\t\t\tvar:{fixed_var('detail', 'source')} = 2",
                f"\t\t\thas_variable = {fixed_var('detail', 'char')}",
                f"\t\t\tvar:{fixed_var('detail', 'char')} = scope:zg361_scoreboard_case_entry",
                f"\t\t\thas_variable = {fixed_var('detail', 'cycle_serial')}",
                f"\t\t\tvar:{fixed_var('detail', 'cycle_serial')} = scope:zg361_scoreboard_case_entry.var:zg361_result_cycle_serial",
                "\t\t}",
            ]
        )
        for field in MUTABLE_CASE_FIELDS:
            append_field_copy(
                lines,
                indent="\t\t",
                destination=fixed_var("detail", field.name),
                field=field,
                source_scope="scope:zg361_scoreboard_case_entry",
            )
        lines.extend(["\t}", "}", ""])

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
    lines.extend(
        [
            "zg361_scoreboard_detail_available_gui = {",
            "\tscope = character",
            f"\tis_shown = {{ has_variable = {fixed_var('detail', 'valid')} var:{fixed_var('detail', 'valid')} = 1 has_variable = {fixed_var('detail', 'char')} }}",
            "}",
            "",
            "zg361_scoreboard_detail_managed_gui = {",
            "\tscope = character",
            f"\tis_shown = {{ has_variable = {fixed_var('detail', 'valid')} var:{fixed_var('detail', 'valid')} = 1 has_variable = {fixed_var('detail', 'source')} var:{fixed_var('detail', 'source')} = 1 }}",
            "}",
            "",
            "zg361_scoreboard_detail_received_gui = {",
            "\tscope = character",
            f"\tis_shown = {{ has_variable = {fixed_var('detail', 'valid')} var:{fixed_var('detail', 'valid')} = 1 has_variable = {fixed_var('detail', 'source')} var:{fixed_var('detail', 'source')} = 2 }}",
            "}",
            "",
            "zg361_scoreboard_detail_title_available_gui = {",
            "\tscope = character",
            f"\tis_shown = {{ has_variable = {fixed_var('detail', 'title')} }}",
            "}",
            "",
            "zg361_sb_self_available_gui = {",
            "\tscope = character",
            "\tis_shown = {",
            f"\t\thas_variable = {fixed_var('self', 'char')}",
            f"\t\thas_variable = {fixed_var('self', 'case_owner')}",
            f"\t\thas_variable = {fixed_var('self', 'cycle_serial')}",
            f"\t\thas_variable = {fixed_var('self', 'case_serial')}",
            "\t}",
            "}",
            "",
        ]
    )
    for field in CASE_FIELDS:
        lines.extend(
            [
                f"zg361_sb_detail_{field.name}_available_gui = {{",
                "\tscope = character",
                f"\tis_shown = {{ has_variable = {fixed_var('detail', field.name)} }}",
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

    for slot in range(1, SLOT_COUNT + 1):
        lines.extend(
            [
                f"zg361_sb_m_{slot:02d}_select_gui = {{",
                "\tscope = character",
                "\tis_shown = {",
                f"\t\thas_variable = {var('m', slot, 'char')}",
                f"\t\thas_variable = {var('m', slot, 'rank')}",
                f"\t\thas_variable = {var('m', slot, 'case_owner')}",
                f"\t\thas_variable = {var('m', slot, 'cycle_serial')}",
                f"\t\thas_variable = {var('m', slot, 'case_serial')}",
                "\t}",
                "\teffect = {",
                "\t\tzg361_clear_scoreboard_detail_effect = yes",
                f"\t\tset_variable = {{ name = {fixed_var('detail', 'source')} value = 1 }}",
                f"\t\tset_variable = {{ name = {fixed_var('detail', 'slot')} value = {slot} }}",
                f"\t\tset_variable = {{ name = {fixed_var('detail', 'char')} value = var:{var('m', slot, 'char')} }}",
                "\t\tif = {",
                f"\t\t\tlimit = {{ has_variable = {var('m', slot, 'title')} }}",
                f"\t\t\tset_variable = {{ name = {fixed_var('detail', 'title')} value = var:{var('m', slot, 'title')} }}",
                "\t\t}",
                f"\t\tset_variable = {{ name = {fixed_var('detail', 'rank')} value = var:{var('m', slot, 'rank')} }}",
            ]
        )
        for field in CASE_FIELDS:
            lines.append(
                f"\t\tif = {{ limit = {{ has_variable = {var('m', slot, field.name)} }} "
                f"set_variable = {{ name = {fixed_var('detail', field.name)} value = var:{var('m', slot, field.name)} }} }}"
            )
        lines.extend(
            [
                f"\t\tset_variable = {{ name = {fixed_var('detail', 'valid')} value = 1 }}",
                "\t}",
                "}",
                "",
            ]
        )

    lines.extend(
        [
            "zg361_sb_self_select_gui = {",
            "\tscope = character",
            "\tis_shown = {",
            f"\t\thas_variable = {fixed_var('self', 'char')}",
            f"\t\thas_variable = {fixed_var('self', 'case_owner')}",
            f"\t\thas_variable = {fixed_var('self', 'cycle_serial')}",
            f"\t\thas_variable = {fixed_var('self', 'case_serial')}",
            "\t}",
            "\teffect = {",
            "\t\tzg361_clear_scoreboard_detail_effect = yes",
            f"\t\tset_variable = {{ name = {fixed_var('detail', 'source')} value = 2 }}",
            f"\t\tset_variable = {{ name = {fixed_var('detail', 'slot')} value = 0 }}",
            f"\t\tset_variable = {{ name = {fixed_var('detail', 'char')} value = var:{fixed_var('self', 'char')} }}",
            "\t\tif = {",
            f"\t\t\tlimit = {{ has_variable = {fixed_var('self', 'title')} }}",
            f"\t\t\tset_variable = {{ name = {fixed_var('detail', 'title')} value = var:{fixed_var('self', 'title')} }}",
            "\t\t}",
            "\t\tif = {",
            f"\t\t\tlimit = {{ has_variable = {fixed_var('self', 'rank')} }}",
            f"\t\t\tset_variable = {{ name = {fixed_var('detail', 'rank')} value = var:{fixed_var('self', 'rank')} }}",
            "\t\t}",
        ]
    )
    for field in CASE_FIELDS:
        lines.append(
            f"\t\tif = {{ limit = {{ has_variable = {fixed_var('self', field.name)} }} "
            f"set_variable = {{ name = {fixed_var('detail', field.name)} value = var:{fixed_var('self', field.name)} }} }}"
        )
    lines.extend(
        [
            f"\t\tset_variable = {{ name = {fixed_var('detail', 'valid')} value = 1 }}",
            "\t}",
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
    selector = (
        f"zg361_sb_m_{slot:02d}_select_gui"
        if prefix == "m"
        else "zg361_sb_self_select_gui"
    )
    detail_visible = (
        f"[GetScriptedGui('{selector}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]"
        if prefix == "m"
        else f"[And(Character.IsPlayer, GetScriptedGui('{selector}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]"
    )
    slot_var = lambda field: var(prefix, slot, field)
    return [
        "hbox = {",
        "\tsize = { 1120 68 } layoutpolicy_horizontal = expanding spacing = 8",
        f"\tvisible = \"[GetScriptedGui('{available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"",
        f"\tdatacontext = \"[GetPlayer.MakeScope.Var('{slot_var('char')}').Char]\"",
        "\tbutton_tertiary = {",
        "\t\tsize = { 1014 68 }",
        "\t\tonclick = \"[DefaultOnCharacterClick(Character.GetID)]\"",
        "\t\tonclick = \"[GetVariableSystem.Clear('zg361_scoreboard_open')]\"",
        "\t\tonclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\"",
        "\t\tonclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\"",
        "\t\tbackground = { using = Background_Area_Dark alpha = 0.6 }",
        "\t\tbackground = {",
        "\t\t\tvisible = \"[Character.IsPlayer]\"",
        "\t\t\ttexture = \"gfx/interface/colors/blue.dds\"",
        "\t\t\ttintcolor = { 0.55 0.72 1.0 0.35 }",
        "\t\t\tusing = Mask_Rough_Edges",
        "\t\t}",
        "\t\thbox = {",
        "\t\t\talwaystransparent = yes layoutpolicy_horizontal = expanding spacing = 8 margin = { 8 4 }",
        f"\t\t\ttext_single = {{ alwaystransparent = yes min_width = 50 max_width = 50 text = \"[GetPlayer.MakeScope.Var('{slot_var('rank')}').GetValue|0]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        "\t\t\tportrait_head_small = { blockoverride \"portrait_button\" { alwaystransparent = yes } }",
        "\t\t\tvbox = {",
        "\t\t\t\talwaystransparent = yes min_width = 285 max_width = 285 layoutpolicy_vertical = expanding spacing = 1",
        "\t\t\t\ttext_single = { alwaystransparent = yes layoutpolicy_horizontal = expanding text = \"[Character.GetUINameNotMeNoTooltip]\" tooltip = \"[Character.GetUINameNotMeNoTooltip]\" default_format = \"#high\" align = nobaseline using = Font_Size_Medium fontsize_min = 12 autoresize = no }",
        f"\t\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[GetScriptedGui('{title_available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" datacontext = \"[GetPlayer.MakeScope.Var('{slot_var('title')}').Title]\" layoutpolicy_horizontal = expanding text = \"[Title.GetNameNoTierNoTooltip]\" default_format = \"#weak\" align = nobaseline using = Font_Size_Small fontsize_min = 10 autoresize = no }}",
        f"\t\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[Not(GetScriptedGui('{title_available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" layoutpolicy_horizontal = expanding text = \"zg361_scoreboard_dash\" default_format = \"#weak\" align = nobaseline using = Font_Size_Small fontsize_min = 10 autoresize = no }}",
        "\t\t\t}",
        f"\t\t\ttext_single = {{ alwaystransparent = yes min_width = 90 max_width = 90 text = \"[GetPlayer.MakeScope.Var('{slot_var('kpi')}').GetValue|1]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        f"\t\t\ttext_single = {{ alwaystransparent = yes min_width = 90 max_width = 90 text = \"[GetPlayer.MakeScope.Var('{slot_var('values')}').GetValue|0]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        f"\t\t\ttext_single = {{ alwaystransparent = yes min_width = 125 max_width = 125 text = \"[GetPlayer.MakeScope.Var('{slot_var('grade')}').GetValue|2]\" default_format = \"#high\" align = center|nobaseline using = Font_Size_Medium }}",
        f"\t\t\ttext_single = {{ alwaystransparent = yes min_width = 95 max_width = 95 text = \"[GetPlayer.MakeScope.Var('{slot_var('streak')}').GetValue|0]\" align = center|nobaseline using = Font_Size_Medium }}",
        "\t\t\tvbox = {",
        "\t\t\t\talwaystransparent = yes min_width = 130 max_width = 130 layoutpolicy_vertical = expanding",
        f"\t\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[GetScriptedGui('{promotion}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_status_promotion\" align = center|nobaseline using = Font_Size_Small }}",
        f"\t\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[GetScriptedGui('{pip}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_status_pip\" align = center|nobaseline using = Font_Size_Small }}",
        f"\t\t\t\ttext_single = {{ alwaystransparent = yes visible = \"[And(Not(GetScriptedGui('{promotion}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), Not(GetScriptedGui('{pip}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)))]\" text = \"zg361_scoreboard_dash\" default_format = \"#weak\" align = center|nobaseline using = Font_Size_Small }}",
        "\t\t\t}",
        "\t\t}",
        "\t}",
        f"\tbutton_standard = {{ name = \"zg361_scoreboard_detail_button_{prefix}_{slot:02d}\" size = {{ 98 60 }} visible = \"{detail_visible}\" text = \"zg361_scoreboard_detail_open\" tooltip = \"zg361_scoreboard_detail_open_tooltip\" onclick = \"[GetScriptedGui('{selector}').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'detail')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" }}",
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
    detail_source = f"zg361_scoreboard_detail_{source}_gui"
    visible = (
        f"[And(And(GetScriptedGui('{availability}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End), "
        f"GetVariableSystem.HasValue('zg361_scoreboard_tab', '{source}')), "
        f"Not(And(GetVariableSystem.HasValue('zg361_scoreboard_view', 'detail'), "
        f"GetScriptedGui('{detail_source}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))))]"
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


def detail_field_row(field: FieldSpec) -> list[str]:
    available = f"zg361_sb_detail_{field.name}_available_gui"
    value_var = fixed_var("detail", field.name)
    lines = [
        "hbox = { layoutpolicy_horizontal = expanding spacing = 16 margin = { 28 7 }",
        f"\ttext_single = {{ min_width = 390 max_width = 390 text = \"zg361_scoreboard_detail_field_{field.name}\" default_format = \"#weak\" align = nobaseline }}",
        "\texpand = {}",
    ]
    if field.kind == "character":
        lines.append(
            f"\ttext_single = {{ visible = \"[GetScriptedGui('{available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"[GetPlayer.MakeScope.Var('{value_var}').Char.GetUINameNotMeNoTooltip]\" default_format = \"#high\" align = nobaseline }}"
        )
    else:
        value_format = "2" if field.kind == "grade" else "0"
        lines.append(
            f"\ttext_single = {{ visible = \"[GetScriptedGui('{available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"[GetPlayer.MakeScope.Var('{value_var}').GetValue|{value_format}]\" default_format = \"#high\" align = nobaseline }}"
        )
    lines.extend(
        [
            f"\ttext_single = {{ visible = \"[Not(GetScriptedGui('{available}').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" text = \"zg361_scoreboard_detail_unavailable\" default_format = \"#weak\" align = nobaseline }}",
            "}",
        ]
    )
    return lines


def detail_page_gui(page: str) -> list[str]:
    fields = tuple(field for field in CASE_FIELDS if field.page == page)
    lines = [
        "vbox = {",
        f"\tname = \"zg361_scoreboard_detail_page_{page}\"",
        "\tlayoutpolicy_horizontal = expanding layoutpolicy_vertical = expanding spacing = 8",
        f"\tvisible = \"[GetVariableSystem.HasValue('zg361_scoreboard_detail_tab', '{page}')]\"",
        f"\ttext_label_center = {{ layoutpolicy_horizontal = expanding text = \"zg361_scoreboard_detail_{page}_hint\" default_format = \"#weak\" using = Font_Size_Small }}",
        "\tscrollbox = {",
        "\t\tlayoutpolicy_horizontal = expanding layoutpolicy_vertical = expanding",
        "\t\tblockoverride \"scrollbox_content\" {",
        "\t\t\tvbox = { layoutpolicy_horizontal = expanding spacing = 3",
    ]
    if fields:
        for field in fields:
            lines.extend("\t\t\t\t" + line for line in detail_field_row(field))
    else:
        lines.append(
            "\t\t\t\ttext_label_center = { layoutpolicy_horizontal = expanding margin = { 40 40 } text = \"zg361_scoreboard_detail_unavailable\" default_format = \"#weak\" using = Font_Size_Medium }"
        )
    lines.extend(["\t\t\t}", "\t\t}", "\t}", "}"])
    return lines


def detail_gui() -> list[str]:
    managed_visible = (
        "And(GetVariableSystem.HasValue('zg361_scoreboard_tab', 'managed'), "
        "GetScriptedGui('zg361_scoreboard_detail_managed_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))"
    )
    received_visible = (
        "And(GetVariableSystem.HasValue('zg361_scoreboard_tab', 'received'), "
        "GetScriptedGui('zg361_scoreboard_detail_received_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))"
    )
    lines = [
        "vbox = {",
        "\tname = \"zg361_scoreboard_detail_panel\"",
        "\tlayoutpolicy_horizontal = expanding layoutpolicy_vertical = expanding spacing = 10 margin = { 20 8 }",
        f"\tvisible = \"[And(GetVariableSystem.HasValue('zg361_scoreboard_view', 'detail'), Or({managed_visible}, {received_visible}))]\"",
        "\thbox = { layoutpolicy_horizontal = expanding spacing = 14",
        "\t\tbutton_standard = { name = \"zg361_scoreboard_detail_back\" size = { 118 44 } text = \"zg361_scoreboard_detail_back\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" }",
        f"\t\tportrait_head_small = {{ datacontext = \"[GetPlayer.MakeScope.Var('{fixed_var('detail', 'char')}').Char]\" blockoverride \"portrait_button\" {{ alwaystransparent = yes }} }}",
        "\t\tvbox = { layoutpolicy_horizontal = expanding spacing = 2",
        f"\t\t\ttext_single = {{ text = \"[GetPlayer.MakeScope.Var('{fixed_var('detail', 'char')}').Char.GetUINameNotMeNoTooltip]\" default_format = \"#high\" align = nobaseline using = Font_Size_Large }}",
        f"\t\t\ttext_single = {{ visible = \"[GetScriptedGui('zg361_scoreboard_detail_title_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" datacontext = \"[GetPlayer.MakeScope.Var('{fixed_var('detail', 'title')}').Title]\" text = \"[Title.GetNameNoTierNoTooltip]\" default_format = \"#weak\" align = nobaseline using = Font_Size_Small }}",
        "\t\t}",
        "\t}",
        "\tdivider_light = { layoutpolicy_horizontal = expanding }",
        "\thbox = { layoutpolicy_horizontal = expanding",
    ]
    for page in DETAIL_PAGES:
        lines.append(
            f"\t\tbutton_tab = {{ name = \"zg361_scoreboard_detail_tab_{page}\" layoutpolicy_horizontal = expanding text = \"zg361_scoreboard_detail_tab_{page}\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', '{page}')]\" down = \"[GetVariableSystem.HasValue('zg361_scoreboard_detail_tab', '{page}')]\" }}"
        )
    lines.extend(["\t}"])
    for page in DETAIL_PAGES:
        lines.extend("\t" + line for line in detail_page_gui(page))
    lines.append("}")
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
    overlay_gate = (
        "And(And(And(And(And(And(Not(IsPauseMenuShown), IsDefaultGUIMode), "
        "Not(IsGameViewOpen('struggle'))), "
        "Not(GreaterThan_CFixedPoint(GetPlayer.MakeScope.Var('hide_ui_main_tabs').GetValue, '(CFixedPoint)0'))), "
        "Not(IsRightWindowOpen)), Not(IsGameViewOpen('outliner'))), "
        "Not(IsGameViewOpen('barbershop')))"
    )
    toggle_hud_gate = f"[{overlay_gate}]"
    any_surface = (
        "Or(Or(GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End), "
        "GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), "
        "GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))"
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
        "\t\ttext_single = { min_width = 98 max_width = 98 text = \"zg361_scoreboard_col_dossier\" default_format = \"#weak\" align = center|nobaseline }",
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
        f"\t\tbutton_standard = {{ size = {{ {toggle_width} {toggle_height} }} visible = \"[GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_open\" onclick = \"[GetVariableSystem.Toggle('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'managed')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" down = \"[GetVariableSystem.Exists('zg361_scoreboard_open')]\" tooltip = \"zg361_scoreboard_open_tooltip\" }}",
        f"\t\tbutton_standard = {{ size = {{ {toggle_width} {toggle_height} }} visible = \"[And(Not(GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" text = \"zg361_scoreboard_open\" onclick = \"[GetVariableSystem.Toggle('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'received')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" down = \"[GetVariableSystem.Exists('zg361_scoreboard_open')]\" tooltip = \"zg361_scoreboard_open_tooltip\" }}",
        f"\t\tbutton_standard = {{ size = {{ {toggle_width} {toggle_height} }} visible = \"[And(And(Not(GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)), Not(GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))), GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End))]\" text = \"zg361_scoreboard_open\" onclick = \"[GetVariableSystem.Toggle('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'system')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" down = \"[GetVariableSystem.Exists('zg361_scoreboard_open')]\" tooltip = \"zg361_scoreboard_open_tooltip\" }}",
        "\t}",
        "\twidget = {",
        "\t\tname = \"zg361_scoreboard_modal\" size = { 100% 100% }",
        f"\t\tvisible = \"[And(And(GetVariableSystem.Exists('zg361_scoreboard_open'), {any_surface}), {overlay_gate})]\"",
        "\t\talwaystransparent = no filter_mouse = all using = Background_Full_Dim using = Animation_ShowHide_Quick",
        "\t\tbutton_normal = { size = { 100% 100% } onclick = \"[GetVariableSystem.Clear('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" shortcut = close_window }",
        "\t\twidget = {",
        "\t\t\tname = \"zg361_scoreboard_panel\" size = { 1220 820 } parentanchor = center widgetanchor = center alwaystransparent = no filter_mouse = all using = Window_Background using = Window_Decoration_Spike",
        "\t\t\tvbox = {",
        "\t\t\t\tusing = Window_Margins spacing = 8",
        "\t\t\t\theader_pattern = { layoutpolicy_horizontal = expanding blockoverride \"header_text\" { text = \"zg361_scoreboard_title\" } blockoverride \"button_close\" { onclick = \"[GetVariableSystem.Clear('zg361_scoreboard_open')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" shortcut = close_window } }",
        "\t\t\t\thbox = { layoutpolicy_horizontal = expanding",
        "\t\t\t\t\tbutton_tab = { layoutpolicy_horizontal = expanding visible = \"[GetScriptedGui('zg361_scoreboard_managed_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_tab_managed\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'managed')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', 'managed')]\" }",
        "\t\t\t\t\tbutton_tab = { layoutpolicy_horizontal = expanding visible = \"[GetScriptedGui('zg361_scoreboard_received_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_tab_received\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'received')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', 'received')]\" }",
        "\t\t\t\t\tbutton_tab = { layoutpolicy_horizontal = expanding visible = \"[GetScriptedGui('zg361_mechanism_ledger_available_gui').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" text = \"zg361_scoreboard_tab_system\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_tab', 'system')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_view', 'list')]\" onclick = \"[GetVariableSystem.Set('zg361_scoreboard_detail_tab', 'facts')]\" down = \"[GetVariableSystem.HasValue('zg361_scoreboard_tab', 'system')]\" }",
        "\t\t\t\t}",
    ]
    lines.extend("\t\t\t\t" + line for line in tab_gui("m"))
    lines.extend("\t\t\t\t" + line for line in tab_gui("r"))
    lines.extend("\t\t\t\t" + line for line in detail_gui())
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
