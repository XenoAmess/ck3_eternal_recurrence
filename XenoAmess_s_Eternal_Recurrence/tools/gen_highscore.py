#!/usr/bin/env python3
"""
Generator for Glassfire Lord's Eternal Recurrence global high-score storage.

Global cross-save storage uses tutorial lesson completion bits, persisted by the
engine in <user dir>/tutorial.txt (completed_lessons list). Bits are write-once,
so the record is stored as monotonic THRESHOLDS: bit xar_hs_ge_<t> completed
iff record >= t. Thresholds are cumulative tiers (step, count), chained:

  (1,100) (5,100) (10,100) (50,100) (100,100) (500,100) (1000,100)

  i.e. 1..100 by 1, 105..600 by 5, 610..1600 by 10, ... cap 166,600, 700 bits.
To extend the cap later, append a tier; completed bits persist in tutorial.txt.

is_tutorial_lesson_completed is an INTERFACE trigger (forbidden in game-state
script), so reading the record goes through a GUI bridge:
  customizable_localization (interface triggers OK) -> GUI state trigger_when
  -> GetScriptedGui().Execute -> scripted_gui effect -> set_global_variable.
The record is detected via the highest completed threshold. Import states are
gated by an explicit game-state request, so GUI creation and on_action order do
not matter.

Writing: xar_quantize_record_candidate_effect first maps the real run score to
the highest existing threshold <= score (capped at the last threshold). The
writer compares and dispatches only that quantized candidate.

Outputs (regenerate with: py gen_highscore.py):
  common/tutorial_lessons/xar_highscore.txt
  common/customizable_localization/xar_generated_loc.txt
  common/scripted_guis/xar_generated_guis.txt
  common/scripted_effects/xar_generated_effects.txt
  gui/xar_meta.gui
  localization/english/xar_generated_l_english.yml

The generated effects also expose a read-only ledger projection. It maps the
current score preview to candidate/next tiers from this same THRESHOLDS table;
the xa_ledger_* globals are temporary event display values, never record bits.
"""

import os

MOD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIERS = [(1, 100), (5, 100), (10, 100), (50, 100), (100, 100), (500, 100), (1000, 100)]

BIT_PREFIX = "xar_hs_ge_"
STEP_TEXT_KEY = "xar_silent_step"
SENTINEL = "XAR_SYNC_SENTINEL"
TOP_SENTINEL_KEY = "xar_top_bit_sentinel"  # unused, kept for reference
LEVEL_KEY_PREFIX = "xar_rec_"
RECORD_VAR = "xa_global_record_imported"
LOCAL_POINTS_VAR = "xa_local_points"
SCORE_VAR = "xa_run_score"
CANDIDATE_VAR = "xa_record_candidate"
OLD_RECORD_VAR = "xa_old_record"
IMPORT_REQUESTED_VAR = "xa_import_requested"
IMPORT_READY_VAR = "xa_import_ready"
IMPORT_CONSUMED_VAR = "xa_import_consumed"
IMPORT_REQUEST_KEY = "xar_import_request_on"
IMPORT_IDLE_KEY = "xar_import_request_off"
LEDGER_SCORE_VAR = "xa_ledger_score"
LEDGER_CANDIDATE_VAR = "xa_ledger_candidate"
LEDGER_NEXT_VAR = "xa_ledger_next"
LEDGER_GAP_VAR = "xa_ledger_gap"
LEDGER_CAP_VAR = "xa_ledger_at_cap"


def build_thresholds():
    thresholds = []
    current = 0
    for step, count in TIERS:
        for _ in range(count):
            current += step
            thresholds.append(current)
    return thresholds


THRESHOLDS = build_thresholds()


def gen_lessons() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        f"# {len(THRESHOLDS)} threshold bits, cap {THRESHOLDS[-1]}.",
        "# Bit xar_hs_ge_<t> completed <=> global high score >= t.",
        "",
    ]
    for t in THRESHOLDS:
        lines.append(f"{BIT_PREFIX}{t} = {{")
        lines.append("\tchain = reactive_advice")
        lines.append("\tdelay = 0")
        lines.append("\tshown_in_encyclopedia = no")
        lines.append("")
        lines.append("\ttrigger = {")
        lines.append(f"\t\thas_global_variable = {BIT_PREFIX}{t}")
        lines.append("\t}")
        lines.append("")
        lines.append(f"\txar_hs_ge_step_{t} = {{")
        lines.append(f'\t\ttext = "{STEP_TEXT_KEY}"')
        lines.append("")
        lines.append("\t\t# Auto-completes as soon as the step is shown: trigger transitions")
        lines.append("\t\t# proceed automatically when the trigger is fulfilled, no click needed.")
        lines.append("\t\ttrigger_transition = {")
        lines.append("\t\t\ttarget = lesson_finish")
        lines.append("\t\t\ttrigger = { always = yes }")
        lines.append("\t\t}")
        lines.append("\t}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def gen_custom_loc() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "# Single descending first_valid localization: returns the level key of the",
        "# HIGHEST completed threshold (bits may be sparse, since writing completes",
        "# only the single highest threshold <= score). Exactly one text matches.",
        "",
        "xar_record_level = {",
        "\ttype = character",
    ]
    for t in reversed(THRESHOLDS):
        lines.append("\ttext = {")
        lines.append(f"\t\ttrigger = {{ is_tutorial_lesson_completed = {BIT_PREFIX}{t} }}")
        lines.append(f"\t\tlocalization_key = {LEVEL_KEY_PREFIX}{t}")
        lines.append("\t}")
    lines.append(f"\ttext = {{ localization_key = {LEVEL_KEY_PREFIX}0 }}")
    lines.append("}")
    lines.append("")
    lines.extend([
        "# Import request signal. The record-level states stay dormant until the",
        "# game-start on_action explicitly requests an import.",
        "xar_import_request_check = {",
        "\ttype = character",
        "\ttext = {",
        "\t\ttrigger = {",
        f"\t\t\thas_global_variable = {IMPORT_REQUESTED_VAR}",
        f"\t\t\tglobal_var:{IMPORT_REQUESTED_VAR} = 1",
        "\t\t}",
        f"\t\tlocalization_key = {IMPORT_REQUEST_KEY}",
        "\t}",
        f"\ttext = {{ localization_key = {IMPORT_IDLE_KEY} fallback = yes }}",
        "}",
        "",
        "# Test-only bridge signal: asks xar_meta to open the player character window.",
        "xar_trait_hover_check = {",
        "\ttype = character",
        "\ttext = {",
        "\t\ttrigger = { has_character_flag = xa_trait_hover_test_pending }",
        "\t\tlocalization_key = xar_trait_hover_sentinel",
        "\t}",
        "\ttext = { localization_key = xar_trait_hover_off fallback = yes }",
        "}",
        "",
    ])
    return "\n".join(lines)


def gen_guis() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "# Executed via GetScriptedGui().Execute from request-gated GUI states.",
        "# The request guard makes duplicate execution a no-op. Once the highest",
        "# completed lesson is imported, the shared consumer copies accurate points",
        "# and starts the selected game-rule flow synchronously from ready state.",
        "",
    ]
    for t in [0] + THRESHOLDS:
        lines.append(f"xar_import_{t}_gui = {{")
        lines.append("\tscope = character")
        lines.append(f"\tis_shown = {{ global_var:{IMPORT_REQUESTED_VAR} = 1 }}")
        lines.append("\teffect = {")
        lines.append("\t\tif = {")
        lines.append(f"\t\t\tlimit = {{ global_var:{IMPORT_REQUESTED_VAR} = 1 }}")
        lines.append(f'\t\t\tdebug_log = "XAR: import state fired k={t}"')
        lines.append("\t\t\tset_global_variable = {")
        lines.append(f"\t\t\t\tname = {RECORD_VAR}")
        lines.append(f"\t\t\t\tvalue = {t}")
        lines.append("\t\t\t}")
        lines.append(f"\t\t\tset_global_variable = {{ name = {IMPORT_REQUESTED_VAR} value = 0 }}")
        lines.append(f"\t\t\tset_global_variable = {{ name = {IMPORT_READY_VAR} value = 1 }}")
        lines.append("\t\t\txar_consume_import_effect = yes")
        lines.append("\t\t}")
        lines.append("\t}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def gen_effects() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "# Quantizes the real run score to the greatest existing threshold <= score.",
        "# A score at or above the storage cap maps to the cap.",
        "",
        "xar_quantize_record_candidate_effect = {",
        f"\tset_global_variable = {{ name = {CANDIDATE_VAR} value = 0 }}",
    ]
    for i, t in enumerate(reversed(THRESHOLDS)):
        keyword = "if" if i == 0 else "else_if"
        lines.append(f"\t{keyword} = {{")
        lines.append(f"\t\tlimit = {{ global_var:{SCORE_VAR} >= {t} }}")
        lines.append(f"\t\tset_global_variable = {{ name = {CANDIDATE_VAR} value = {t} }}")
        lines.append("\t}")
    lines.extend([
        "}",
        "",
        "# Writes only a strictly higher quantized candidate. Dispatch is based on",
        "# candidate equality, never on the real run score.",
        "xar_write_record_effect = {",
        "\tif = {",
        f"\t\tlimit = {{ global_var:{CANDIDATE_VAR} > global_var:{OLD_RECORD_VAR} }}",
    ])
    for i, t in enumerate(reversed(THRESHOLDS)):
        keyword = "if" if i == 0 else "else_if"
        lines.append(f"\t\t{keyword} = {{")
        lines.append(f"\t\t\tlimit = {{ global_var:{CANDIDATE_VAR} = {t} }}")
        lines.append(f"\t\t\tset_global_variable = {BIT_PREFIX}{t}")
        lines.append("\t\t}")
    lines.append("\t}")
    lines.append("}")
    lines.append("")

    # Ledger projection: evaluate the expensive current-score script value once,
    # then map it through the same threshold table as record quantization. These
    # globals exist only to render the event and are cleared when it closes.
    lines.extend([
        "# Read-only ledger projection generated from THRESHOLDS.",
        "# xa_ledger_* are temporary display values; this never writes record bits.",
        "xar_prepare_ledger_effect = {",
        f"\tset_global_variable = {{ name = {LEDGER_SCORE_VAR} value = xar_current_score_value }}",
        f"\tset_global_variable = {{ name = {LEDGER_CANDIDATE_VAR} value = 0 }}",
        f"\tset_global_variable = {{ name = {LEDGER_NEXT_VAR} value = {THRESHOLDS[0]} }}",
        "\tset_global_variable = {",
        f"\t\tname = {LEDGER_GAP_VAR}",
        f"\t\tvalue = {{ value = {THRESHOLDS[0]} subtract = global_var:{LEDGER_SCORE_VAR} min = 0 }}",
        "\t}",
        f"\tset_global_variable = {{ name = {LEDGER_CAP_VAR} value = 0 }}",
    ])
    for index in range(len(THRESHOLDS) - 1, -1, -1):
        threshold = THRESHOLDS[index]
        next_threshold = THRESHOLDS[min(index + 1, len(THRESHOLDS) - 1)]
        keyword = "if" if index == len(THRESHOLDS) - 1 else "else_if"
        lines.append(f"\t{keyword} = {{")
        lines.append(f"\t\tlimit = {{ global_var:{LEDGER_SCORE_VAR} >= {threshold} }}")
        lines.append(
            f"\t\tset_global_variable = {{ name = {LEDGER_CANDIDATE_VAR} value = {threshold} }}")
        lines.append(
            f"\t\tset_global_variable = {{ name = {LEDGER_NEXT_VAR} value = {next_threshold} }}")
        if index == len(THRESHOLDS) - 1:
            lines.append(f"\t\tset_global_variable = {{ name = {LEDGER_GAP_VAR} value = 0 }}")
            lines.append(f"\t\tset_global_variable = {{ name = {LEDGER_CAP_VAR} value = 1 }}")
        else:
            lines.extend([
                "\t\tset_global_variable = {",
                f"\t\t\tname = {LEDGER_GAP_VAR}",
                f"\t\t\tvalue = {{ value = {next_threshold} subtract = global_var:{LEDGER_SCORE_VAR} min = 0 }}",
                "\t\t}",
            ])
        lines.append("\t}")
    lines.append("}")
    lines.append("")

    # Lifespan purchase: applies the next modifier in the series (same-modifier
    # reapplication does not stack, so there are 50 distinct modifiers).
    lines.append("# Lifespan purchase: +1 Health per stack, 50 stacks max.")
    lines.append("xar_buy_lifespan_effect = {")
    lines.append("\tchange_global_variable = {")
    lines.append("\t\tname = xa_lifespan_bought")
    lines.append("\t\tadd = 1")
    lines.append("\t}")
    for i in range(1, 51):
        lines.append("\tif = {")
        lines.append(f"\t\tlimit = {{ global_var:xa_lifespan_bought = {i} }}")
        lines.append(f"\t\tadd_character_modifier = {{ modifier = xar_lifespan_{i:02d} }}")
        lines.append("\t}")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def gen_gui() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "#",
        "# Import side of the global high-score storage: exactly one highest-threshold",
        "# custom localization returns the sentinel. A separate request signal gates",
        "# every state, so states cannot consume the record before game start asks.",
        "# The write-side lesson completes itself through trigger_transition.",
        "window = {",
        '\tname = "xar_meta_window"',
        "\tsize = { 1 1 }",
        "\tlayer = tutorial",
        "\tposition = { 0 0 }",
        "",
        "\t# No background and pass-through clicks: registered via scripted_widgets",
        "\t# so it exists (states evaluate) but renders nothing visible.",
        '\tvisible = "[GetPlayer.IsValid]"',
        "\talwaystransparent = yes",
        "",
        "\tstate = {",
        "\t\tname = _show",
        "\t\tusing = Animation_FadeIn_Quick",
        "\t}",
        "",
        "\tstate = {",
        "\t\tname = _hide",
        "\t\tusing = Animation_FadeOut_Quick",
        "\t}",
        "",
        "\t# After the player confirms the result event, switch to observer mode",
        "\t# (the save is over: they must not keep playing as the heir).",
        "\tstate = {",
        '\t\tname = "xar_exit_to_menu"',
        '\t\ttrigger_when = "[EqualTo_string( GetPlayer.Custom(\'xar_quit_check\'), Localize(\'xar_quit_sentinel\') )]"',
        '\t\ton_start = "[ExecuteConsoleCommand(\'observe\')]"',
        "\t}",
    ]
    for t in [0] + THRESHOLDS:
        lines.append("")
        lines.append("\tstate = {")
        lines.append(f'\t\tname = "xar_import_{t}"')
        lines.append(
            f'\t\ttrigger_when = "[And( EqualTo_string( GetPlayer.Custom(\'xar_record_level\'), '
            f'Localize(\'{LEVEL_KEY_PREFIX}{t}\') ), EqualTo_string( GetPlayer.Custom(\'xar_import_request_check\'), '
            f'Localize(\'{IMPORT_REQUEST_KEY}\') ) )]"')
        lines.append(f'\t\ton_start = "[GetScriptedGui(\'xar_import_{t}_gui\').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"')
        lines.append("\t}")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def gen_loc(lang: str) -> str:
    lines = [
        f"l_{lang}:",
        " # GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        " # Lesson and step names share one sentinel string (no brackets, those",
        " # would be parsed as loc commands).",
    ]
    for t in THRESHOLDS:
        lines.append(f' {BIT_PREFIX}{t}:0 "{SENTINEL}"')
        lines.append(f' xar_hs_ge_step_{t}:0 "{SENTINEL}"')
    lines.append("")
    lines.append(" # Unique level keys returned by xar_record_level (contents must differ")
    lines.append(" # per level so GUI import states can tell which threshold matched).")
    lines.append(" # NOTE: custom localization validates keys against the CURRENT language,")
    lines.append(" # so these must exist in every language file, with identical contents.")
    for t in [0] + THRESHOLDS:
        lines.append(f' {LEVEL_KEY_PREFIX}{t}:0 "XAR_LEVEL_{t}"')
    lines.append(f' {IMPORT_REQUEST_KEY}:0 "XAR_IMPORT_REQUESTED"')
    lines.append(f' {IMPORT_IDLE_KEY}:0 "XAR_IMPORT_IDLE"')
    lines.append(' xar_trait_hover_sentinel:0 "XAR_TRAIT_HOVER_OPEN"')
    lines.append(' xar_trait_hover_off:0 "XAR_TRAIT_HOVER_OFF"')
    lines.append("")
    return "\n".join(lines)


def gen_trait_test_gui() -> str:
    return "\n".join([
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "# Acceptance-only button. It is invisible in normal play because its",
        "# trigger variable is set only by the self-test curse option.",
        "window = {",
        '\tname = "xar_trait_test_window"',
        "\tsize = { 64 64 }",
        "\tlayer = tutorial",
        "\tparentanchor = center",
        "\tposition = { 0 0 }",
        '\tvisible = "[GetPlayer.IsValid]"',
        "",
        "\tbutton_standard = {",
        '\t\tname = "xar_open_trait_test_character"',
        "\t\tsize = { 100% 100% }",
        '\t\tvisible = "[EqualTo_string( GetPlayer.Custom(\'xar_trait_hover_check\'), Localize(\'xar_trait_hover_sentinel\') )]"',
        '\t\tonclick = "[DefaultOnCharacterClick(GetPlayer.GetID)]"',
        "\t}",
        "}",
        "",
    ])


def write(rel_path: str, content: str, bom: bool = True) -> None:
    path = os.path.join(MOD_ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    enc = "utf-8-sig" if bom else "utf-8"
    with open(path, "w", encoding=enc, newline="\n") as f:
        f.write(content)
    print(f"wrote {rel_path} ({len(content)} bytes)")


if __name__ == "__main__":
    print(f"generating threshold storage: {len(THRESHOLDS)} bits, cap {THRESHOLDS[-1]}")
    write(os.path.join("common", "tutorial_lessons", "xar_highscore.txt"), gen_lessons())
    write(os.path.join("common", "customizable_localization", "xar_generated_loc.txt"), gen_custom_loc())
    write(os.path.join("common", "scripted_guis", "xar_generated_guis.txt"), gen_guis())
    write(os.path.join("common", "scripted_effects", "xar_generated_effects.txt"), gen_effects())
    write(os.path.join("gui", "xar_meta.gui"), gen_gui())
    write(os.path.join("gui", "xar_trait_test.gui"), gen_trait_test_gui())
    # Custom localization validates keys against the CURRENT language with no
    # English fallback, so generated loc must exist for every vanilla language.
    for lang in ("english", "french", "german", "japanese", "korean", "polish",
                 "russian", "simp_chinese", "spanish"):
        write(os.path.join("localization", lang, f"xar_generated_l_{lang}.yml"), gen_loc(lang))
