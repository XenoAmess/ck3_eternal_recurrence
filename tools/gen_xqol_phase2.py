#!/usr/bin/env python3
"""Generate the repetitive phase-two runtime for XenoAmess Quality of Life."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "mod_xenoamess_quality_of_life"
BOM = b"\xef\xbb\xbf"

OUTPUTS = {
    "common/character_interactions/xqol_generated_release_interactions.txt",
    "common/scripted_effects/xqol_generated_conversion_dispatch.txt",
    "common/scripted_guis/xqol_generated_conversion_threshold_guis.txt",
    "gui/event_window_widgets/xqol_conversion_threshold_slider.gui",
}

TERMS = (
    ("hook_recruit_conversion", True, True, True),
    ("hook_recruit", True, True, False),
    ("hook_conversion", True, False, True),
    ("recruit_conversion", False, True, True),
    ("hook", True, False, False),
    ("recruit", False, True, False),
    ("conversion", False, False, True),
)


def render_release_acceptance(*, hook: bool, recruit: bool, conversion: bool) -> str:
    blocks = [
        "\tbase = 100",
        "\tmodifier = {",
        "\t\tadd = -20",
        "\t\tscope:recipient = { has_trait = ambitious }",
        "\t\tdesc = RECIPIENT_IS_AMBITIOUS",
        "\t}",
    ]
    if conversion:
        blocks.extend(
            (
                "\tmodifier = {",
                "\t\tadd = -20",
                "\t\tscope:recipient = { ai_zeal <= 20 }",
                "\t\tdesc = CONVERSION_NEGATIVE_REASON",
                "\t}",
                "\tmodifier = {",
                "\t\tadd = {",
                "\t\t\tvalue = scope:recipient.ai_zeal",
                "\t\t\tif = {",
                "\t\t\t\tlimit = {",
                "\t\t\t\t\tscope:recipient.faith = {",
                "\t\t\t\t\t\tfaith_hostility_level = {",
                "\t\t\t\t\t\t\ttarget = scope:actor.faith",
                "\t\t\t\t\t\t\tvalue = faith_astray_level",
                "\t\t\t\t\t\t}",
                "\t\t\t\t\t}",
                "\t\t\t\t}",
                "\t\t\t\tmultiply = -1",
                "\t\t\t}",
                "\t\t\telse = { multiply = -2 }",
                "\t\t}",
                "\t\tscope:recipient = { ai_zeal > 20 }",
                "\t\tdesc = CONVERSION_NEGATIVE_REASON",
                "\t}",
            )
        )
    if hook:
        blocks.extend(
            (
                "\tmodifier = {",
                "\t\tadd = {",
                "\t\t\tvalue = -50",
                "\t\t\tif = {",
                "\t\t\t\tlimit = { scope:recipient = { ai_vengefulness > 0 } }",
                "\t\t\t\tsubtract = scope:recipient.ai_vengefulness",
                "\t\t\t}",
                "\t\t}",
                "\t\tdesc = GAIN_HOOK_NEGATIVE_REASON",
                "\t}",
            )
        )
    if recruit:
        blocks.extend(
            (
                "\tmodifier = {",
                "\t\tadd = -10",
                "\t\tNOT = {",
                "\t\t\tscope:actor = {",
                "\t\t\t\tculture = { has_cultural_parameter = can_recruit_prisoners_easily }",
                "\t\t\t}",
                "\t\t}",
                "\t\tdesc = RECRUITMET_NEGATIVE_REASON",
                "\t}",
            )
        )
    return "\n".join(blocks)


def render_release_interaction(name: str, hook: bool, recruit: bool, conversion: bool) -> str:
    validity = ["xqol_release_base_valid_trigger = yes"]
    if hook:
        validity.append("xqol_release_hook_valid_trigger = yes")
    if recruit:
        validity.append("xqol_release_recruit_valid_trigger = yes")
    if conversion:
        validity.append("xqol_release_conversion_valid_trigger = yes")
    validity_text = "\n".join(f"\t\t\t{line}" for line in validity)
    return f"""xqol_release_{name}_interaction = {{
\thidden = yes
\tcommon_interaction = no
\tuse_diplomatic_range = no

\tis_shown = {{
\t\tscope:recipient = {{
{validity_text}
\t\t}}
\t}}

\tis_valid = {{
\t\tscope:recipient = {{
{validity_text}
\t\t}}
\t}}

\tai_accept = {{
{render_release_acceptance(hook=hook, recruit=recruit, conversion=conversion)}
\t}}

\ton_accept = {{
\t\txqol_release_prisoner_terms_effect = {{
\t\t\tHOOK = {'yes' if hook else 'no'}
\t\t\tRECRUIT = {'yes' if recruit else 'no'}
\t\t\tCONVERSION = {'yes' if conversion else 'no'}
\t\t}}
\t}}

\tai_potential = {{ always = no }}
\tai_frequency = 0
\tai_will_do = {{ base = 0 }}
}}"""


def render_release_interactions() -> str:
    body = "\n\n".join(
        (
            render_conversion_interaction("courtier", 1, 5),
            render_conversion_interaction("ruler", 4, 9),
            *(render_release_interaction(*term) for term in TERMS),
        )
    )
    return "# GENERATED FILE. Edit tools/gen_xqol_phase2.py, then regenerate.\n\n" + body + "\n"


def render_conversion_interaction(kind: str, minimum_days: int, maximum_days: int) -> str:
    if kind not in {"courtier", "ruler"}:
        raise ValueError(f"unsupported conversion interaction kind: {kind}")
    return f"""xqol_mass_conversion_{kind}_interaction = {{
\thidden = yes
\tuse_diplomatic_range = no
\tai_maybe = yes
\tcan_send_despite_rejection = yes
\tai_min_reply_days = {minimum_days}
\tai_max_reply_days = {maximum_days}

\tis_shown = {{
\t\tscope:actor = {{ xqol_human_ruler_trigger = yes }}
\t\tscope:recipient = {{ is_ai = yes }}
\t}}

\tis_valid = {{
\t\tscope:actor = {{
\t\t\tis_character_interaction_valid = {{
\t\t\t\trecipient = scope:recipient
\t\t\t\tinteraction = {'ask_for_conversion_courtier_interaction' if kind == 'courtier' else 'demand_conversion_vassal_ruler_interaction'}
\t\t\t}}
\t\t}}
\t}}

\tai_accept = {{
\t\tbase = 0
\t\tmodifier = {{
\t\t\tadd = 50
\t\t\tdesc = EDUCATE_CHILD_ACTOR_IS_MY_LIEGE
\t\t}}
\t\treligion_demand_conversion_default_modifier = yes
\t}}

\ton_accept = {{
\t\txqol_mass_conversion_{kind}_accepted_effect = yes
\t}}

\ton_decline = {{
\t\txqol_mass_conversion_declined_effect = yes
\t}}

\tai_potential = {{ always = no }}
\tai_frequency = 0
\tai_will_do = {{ base = 0 }}
}}"""


def render_conversion_dispatch() -> str:
    cases = "\n".join(
        f"\t\t{value} = {{ xqol_bulk_conversion_threshold_effect = {{ THRESHOLD = {value} }} }}"
        for value in range(101)
    )
    return f"""# GENERATED FILE. Edit tools/gen_xqol_phase2.py, then regenerate.

xqol_bulk_conversion_dispatch_effect = {{
\tswitch = {{
\t\ttrigger = var:xqol_mass_conversion_threshold_draft
{cases}
\t\tfallback = {{ xqol_bulk_conversion_threshold_effect = {{ THRESHOLD = 50 }} }}
\t}}
}}
"""


def render_threshold_guis() -> str:
    entries = []
    for value in range(101):
        entries.append(
            f"""xqol_set_conversion_threshold_{value}_gui = {{
\tscope = character
\tis_shown = {{
\t\tis_ai = no
\t\thas_variable = xqol_mass_conversion_threshold_draft
\t}}
\teffect = {{
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tis_ai = no
\t\t\t\thas_variable = xqol_mass_conversion_threshold_draft
\t\t\t}}
\t\t\tset_variable = {{ name = xqol_mass_conversion_threshold_draft value = {value} }}
\t\t}}
\t}}
}}"""
        )
    return (
        "# GENERATED FILE. Edit tools/gen_xqol_phase2.py, then regenerate.\n\n"
        + "\n\n".join(entries)
        + "\n"
    )


def render_slider_widget() -> str:
    states = "\n".join(
        f"""\tstate = {{
\t\tname = \"xqol_conversion_threshold_route_{value}\"
\t\ttrigger_when = \"[GetVariableSystem.HasValue('xqol_conversion_threshold_route', '{value}')]\"
\t\ton_start = \"[GetScriptedGui('xqol_set_conversion_threshold_{value}_gui').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\"
\t\ton_start = \"[GetVariableSystem.Clear('xqol_conversion_threshold_route')]\"
\t\tduration = 0.01
\t}}"""
        for value in range(101)
    )
    callback = (
        "[GetVariableSystem.Set('xqol_conversion_threshold_route', "
        "IntToString(GetProgressBarValueMaxScaled(Min_float(Max_float(Multiply_float(Divide_float("
        "Subtract_float(GetX_CVector2f(PdxGuiWidget.GetScaledMousePosition), '(float)2'), "
        "Subtract_float(IntToFloat(GetX_CVector2i(PdxGetWidgetScreenSize(PdxGuiWidget.Self))), "
        "'(float)4')), '(float)100'), '(float)0'), '(float)100'), "
        "'(float)100', '(int32)100')))]"
    )
    return f"""# GENERATED FILE. Edit tools/gen_xqol_phase2.py, then regenerate.

vbox = {{
\tname = \"xqol_conversion_threshold_slider\"
\tlayoutpolicy_horizontal = expanding
\tspacing = 8

\tdivider_light = {{ layoutpolicy_horizontal = expanding }}

\ttext_single = {{
\t\tlayoutpolicy_horizontal = expanding
\t\ttext = xqol_mass_conversion_threshold_label
\t\talign = center|nobaseline
\t\tdefault_format = \"#T\"
\t}}

\ttext_single = {{
\t\tlayoutpolicy_horizontal = expanding
\t\traw_text = \"[GetPlayer.MakeScope.Var('xqol_mass_conversion_threshold_draft').GetValue|0]%\"
\t\talign = center|nobaseline
\t\tdefault_format = \"#V\"
\t}}

\tcontainer = {{
\t\tlayoutpolicy_horizontal = expanding
\t\tsize = {{ 404 28 }}

\t\tscrollbar = {{
\t\t\tname = \"xqol_conversion_threshold_scrollbar\"
\t\t\tparentanchor = center
\t\t\tdirection = horizontal
\t\t\tsize = {{ 404 20 }}
\t\t\tmin = 0
\t\t\tmax = 100
\t\t\tstep = 1
\t\t\tpage = 10
\t\t\twheelstep = 0
\t\t\ttracknavigation = direct
\t\t\tvalue = \"[FixedPointToFloat(GetPlayer.MakeScope.Var('xqol_mass_conversion_threshold_draft').GetValue)]\"
\t\t\tonchangestart = \"[GetVariableSystem.Clear('xqol_conversion_threshold_route')]\"
\t\t\tonchangefinish = \"{callback}\"

\t\t\ttrack = {{
\t\t\t\tbutton = {{
\t\t\t\t\tsize = {{ 404 14 }}
\t\t\t\t\ttexture = \"gfx/interface/progressbars/progress_black.dds\"
\t\t\t\t\teffectname = \"NoHighlight\"
\t\t\t\t\tspriteType = Corneredtiled
\t\t\t\t\tspriteborder = {{ 6 6 }}
\t\t\t\t}}
\t\t\t}}

\t\t\tslider = {{
\t\t\t\tbutton = {{
\t\t\t\t\tname = \"xqol_conversion_threshold_handle\"
\t\t\t\t\tsize = {{ 4 20 }}
\t\t\t\t\ttexture = \"gfx/interface/scrollbars/scrollbar_slider.dds\"
\t\t\t\t\tspriteType = Corneredstretched
\t\t\t\t\tspriteborder = {{ 3 3 }}
\t\t\t\t\tframesize = {{ 12 40 }}
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t}}

\ttext_multi = {{
\t\tlayoutpolicy_horizontal = expanding
\t\ttext = xqol_mass_conversion_threshold_help
\t\talign = center|nobaseline
\t\tautoresize = yes
\t\tdefault_format = \"#weak\"
\t}}

{states}
}}
"""


def generated_payloads() -> dict[str, str]:
    return {
        "common/character_interactions/xqol_generated_release_interactions.txt": render_release_interactions(),
        "common/scripted_effects/xqol_generated_conversion_dispatch.txt": render_conversion_dispatch(),
        "common/scripted_guis/xqol_generated_conversion_threshold_guis.txt": render_threshold_guis(),
        "gui/event_window_widgets/xqol_conversion_threshold_slider.gui": render_slider_widget(),
    }


def write_outputs(*, check: bool) -> bool:
    changed: list[str] = []
    for relative, text in generated_payloads().items():
        path = MOD / relative
        expected = BOM + text.replace("\r\n", "\n").encode("utf-8")
        actual = path.read_bytes() if path.is_file() else None
        if actual == expected:
            continue
        changed.append(relative)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if changed:
        action = "would update" if check else "updated"
        print(f"XQOL phase-two generator {action}: " + ", ".join(changed))
        return False
    print(f"XQOL phase-two generated runtime is current ({len(OUTPUTS)} files)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = write_outputs(check=args.check)
    return 0 if current or not args.check else 1


if __name__ == "__main__":
    raise SystemExit(main())
