#!/usr/bin/env python3
"""
Generator for XenoAmess's Eternal Recurrence global high-score storage.

Global cross-save storage uses tutorial lesson completion bits, persisted by the
engine in <user dir>/tutorial.txt (completed_lessons list). Bits are write-once,
so the record is stored as monotonic THRESHOLDS: bit xar_hs_ge_<t> completed
iff record >= t. Thresholds are cumulative tiers (step, count), chained:

  (1,100) (5,100) (10,100) (50,100) (100,100) (500,100) (1000,100)

i.e. 1..100 by 1, 105..600 by 5, 610..1600 by 10, ... cap 167,600, 700 bits.
To extend the cap later, append a tier; completed bits persist in tutorial.txt.

is_tutorial_lesson_completed is an INTERFACE trigger (forbidden in game-state
script), so reading the record goes through a GUI bridge:
  customizable_localization (interface triggers OK) -> GUI state trigger_when
  -> GetScriptedGui().Execute -> scripted_gui effect -> set_global_variable.
The record is detected via the single "top threshold" (t completed, next not),
so exactly one import state fires per record change.

Writing: xar_write_record_effect sets every threshold bit <= run score; only
newly crossed thresholds fire lesson popups (completed lessons never refire),
which the autoclicker state in gui/window_tutorial.gui completes automatically.

Outputs (regenerate with: py gen_highscore.py):
  common/tutorial_lessons/xar_highscore.txt
  common/customizable_localization/xar_generated_loc.txt
  common/scripted_guis/xar_generated_guis.txt
  common/scripted_effects/xar_generated_effects.txt
  gui/xar_meta.gui
  localization/english/xar_generated_l_english.yml
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
SHOP_PENDING_VAR = "xa_shop_pending"
SCORE_VAR = "xa_run_score"


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
    return "\n".join(lines)


def gen_guis() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "# Executed via GetScriptedGui().Execute from the GUI import states.",
        "# Sets the imported record value; at game start (shop pending) also copies",
        "# it into this run's spendable points (the shop event itself is fired",
        "# separately by the game-start on_action with a 1-day delay).",
        "",
    ]
    for t in [0] + THRESHOLDS:
        lines.append(f"xar_import_{t}_gui = {{")
        lines.append("\tscope = character")
        lines.append("\tis_shown = { always = yes }")
        lines.append("\teffect = {")
        lines.append(f'\t\tdebug_log = "XAR: import state fired k={t}"')
        lines.append("\t\tset_global_variable = {")
        lines.append(f"\t\t\tname = {RECORD_VAR}")
        lines.append(f"\t\t\tvalue = {t}")
        lines.append("\t\t}")
        lines.append("\t\tif = {")
        lines.append(f"\t\t\tlimit = {{ has_global_variable = {SHOP_PENDING_VAR} }}")
        lines.append(f"\t\t\tremove_global_variable = {SHOP_PENDING_VAR}")
        lines.append("\t\t\tset_global_variable = {")
        lines.append(f"\t\t\t\tname = {LOCAL_POINTS_VAR}")
        lines.append(f"\t\t\t\tvalue = {t}")
        lines.append("\t\t\t}")
        lines.append("\t\t}")
        lines.append("\t}")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def gen_effects() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "# Completes only the single HIGHEST threshold bit <= run score (descending",
        "# else_if chain). Record semantics are identical to setting all lower bits,",
        "# since the record always lands exactly on a threshold. If that bit is",
        "# already completed the lesson does not refire, so <= 1 popup per death.",
        "",
        "xar_write_record_effect = {",
    ]
    for i, t in enumerate(reversed(THRESHOLDS)):
        keyword = "if" if i == 0 else "else_if"
        lines.append(f"\t{keyword} = {{")
        lines.append(f"\t\tlimit = {{ global_var:{SCORE_VAR} >= {t} }}")
        lines.append(f"\t\tset_global_variable = {BIT_PREFIX}{t}")
        lines.append("\t}")
    lines.append("}")
    lines.append("")

    # Parameterized floor(log2) effect (script values have no log function).
    # floor(log2(x)) == count of powers of two <= x; x < 2 yields 0.
    lines.append("# Parameterized floor(log2($SRC$)) into global var $VAR$.")
    lines.append("# Call: xar_log2_floor_effect = { SRC = gold VAR = xa_l_gold }")
    lines.append("xar_log2_floor_effect = {")
    lines.append("\tset_global_variable = {")
    lines.append("\t\tname = $VAR$")
    lines.append("\t\tvalue = 0")
    lines.append("\t}")
    for n in range(1, 31):
        lines.append("\tif = {")
        lines.append(f"\t\tlimit = {{ $SRC$ >= {2 ** n} }}")
        lines.append("\t\tchange_global_variable = {")
        lines.append("\t\t\tname = $VAR$")
        lines.append("\t\t\tadd = 1")
        lines.append("\t\t}")
        lines.append("\t}")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def gen_gui() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_highscore.py",
        "#",
        "# Import side of the global high-score storage: exactly one top-threshold",
        "# custom localization returns the sentinel; its state then runs the",
        "# matching scripted gui which writes the record into game state.",
        "# (The write side's autoclicker lives in the window_tutorial.gui override,",
        "#  since the Tutorial datacontext only exists on the tutorial window.)",
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
    ]
    for t in [0] + THRESHOLDS:
        lines.append("")
        lines.append("\tstate = {")
        lines.append(f'\t\tname = "xar_import_{t}"')
        lines.append(f'\t\ttrigger_when = "[EqualTo_string( GetPlayer.Custom(\'xar_record_level\'), Localize(\'{LEVEL_KEY_PREFIX}{t}\') )]"')
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
    lines.append("")
    return "\n".join(lines)


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
    write(os.path.join("gui", "xar_meta.gui"), gen_gui(), bom=False)
    write(os.path.join("localization", "english", "xar_generated_l_english.yml"), gen_loc("english"))
    write(os.path.join("localization", "simp_chinese", "xar_generated_l_simp_chinese.yml"), gen_loc("simp_chinese"))
