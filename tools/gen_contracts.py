#!/usr/bin/env python3
"""Generate contract events, persistence lessons, localization, and docs."""

from pathlib import Path

from contracts_data import CONTRACTS, MILESTONES


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
LANGS = ("simp_chinese", "english", "french", "german", "japanese", "korean", "polish", "russian", "spanish")
HEADER = "# GENERATED FILE - do not edit. Regenerate with tools/gen_contracts.py"


def generated_events():
    lines = [HEADER, "namespace = xar", ""]
    lines.extend([
        "xar.2000 = {",
        "\ttype = character_event",
        "\ttrigger = { is_ai = no }",
        "\ttheme = mental_health",
        "\toverride_background = { reference = xar_glassfire }",
        "\ttitle = xar.2000.title",
        "\tdesc = xar.2000.desc",
    ])
    for contract in CONTRACTS:
        lines.extend([
            "\toption = {",
            f"\t\tname = xar.2000.{contract['key']}",
            f"\t\txar_select_contract_{contract['key']}_effect = yes",
            "\t}",
        ])
    lines.extend(["}", ""])
    for contract in CONTRACTS:
        for index, milestone in enumerate(MILESTONES):
            event_id = 2100 + contract["id"] * 10 + index + 1
            lines.extend([
                f"xar.{event_id} = {{",
                "\ttype = character_event",
                "\ttrigger = { is_ai = no }",
                "\ttheme = mental_health",
                "\toverride_background = { reference = xar_glassfire }",
                "\ttitle = xar.contract.milestone.title",
                f"\tdesc = xar.contract.{contract['key']}.milestone.{milestone}",
                f"\toption = {{ name = xar.contract.milestone.{milestone}.ok }}",
                "}", "",
            ])
    for level in range(10, 101, 10):
        event_id = 2200 + level // 10
        token = "reroll" if (level // 10) % 2 else "seal"
        lines.extend([
            f"xar.{event_id} = {{",
            "\ttype = character_event",
            "\ttrigger = { is_ai = no }",
            "\ttheme = mental_health",
            "\toverride_background = { reference = xar_glassfire }",
            "\ttitle = xar.gaze.milestone.title",
            f"\tdesc = xar.gaze.milestone.{token}",
            f"\timmediate = {{ save_scope_value_as = {{ name = xar_gaze_level value = {level} }} }}",
            "\toption = { name = xar.gaze.milestone.ok }",
            "}", "",
        ])
    return "\n".join(lines)


def generated_decision():
    return "\n".join([
        HEADER,
        "xar_contract_select_decision = {",
        "\tpicture = {",
        '\t\treference = "gfx/interface/illustrations/decisions/decision_dynasty_house.dds"',
        "\t}",
        "\tsort_order = 11",
        "\tai_check_interval = 0",
        "\tdesc = xar_contract_select_decision_desc",
        "\tis_shown = { is_ai = no has_character_flag = xa_enabled global_var:xa_contract_id = 0 }",
        "\tis_valid_showing_failures_only = { is_ai = no has_character_flag = xa_enabled global_var:xa_contract_id = 0 }",
        "\tai_potential = { always = no }",
        "\teffect = {",
        "\t\thidden_effect = {",
        "\t\t\tset_global_variable = xa_open_contract_pending",
        "\t\t}",
        "\t}",
        "}", "",
    ])


def generated_effects():
    lines = [HEADER, "# Contract selection, behavioral progress, and Gaze unlocks.", ""]
    for contract in CONTRACTS:
        lines.extend([
            f"xar_select_contract_{contract['key']}_effect = {{",
            f"\tset_global_variable = {{ name = xa_contract_id value = {contract['id']} }}",
            "\tset_global_variable = { name = xa_contract_progress value = 0 }",
            "\t# XAR_ACCEPTANCE_ONLY_BEGIN",
            "\tif = {",
            "\t\tlimit = { has_global_variable = xa_full_ui_test_active }",
            f"\t\tif = {{ limit = {{ global_var:xa_contract_id = {contract['id']} }} debug_log = \"XAR: TEST PASS ui_contract_select\" }}",
            "\t\telse = { debug_log = \"XAR: TEST FAIL ui_contract_select\" }",
            "\t\tremove_global_variable = xa_full_ui_test_active",
            "\t\tremove_global_variable = xa_ui_test_stage",
            "\t}",
            "\t# XAR_ACCEPTANCE_ONLY_END",
            "}", "",
        ])
    lines.extend(["xar_add_contract_progress_effect = {", "\tif = {", "\t\tlimit = {",
                  "\t\t\tis_ai = no", "\t\t\thas_character_flag = xa_enabled",
                  "\t\t\tglobal_var:xa_contract_id = $ID$", "\t\t\tglobal_var:xa_contract_progress < 10",
                  "\t\t}", "\t\tchange_global_variable = { name = xa_contract_progress add = 1 }"])
    for contract in CONTRACTS:
        lines.extend(["\t\tif = {", f"\t\t\tlimit = {{ global_var:xa_contract_id = {contract['id']} }}"])
        for index, milestone in enumerate(MILESTONES):
            event_id = 2100 + contract["id"] * 10 + index + 1
            lines.extend(["\t\t\tif = {", f"\t\t\t\tlimit = {{ global_var:xa_contract_progress = {milestone} }}",
                          f"\t\t\t\tset_global_variable = xa_contract_pb_{contract['id']}_{milestone}",
                          "\t\t\t\t# XAR_ACCEPTANCE_ONLY_BEGIN",
                          "\t\t\t\tif = {",
                          "\t\t\t\t\tlimit = { NOT = { has_game_rule = xar_selftest } }",
                          f"\t\t\t\t\ttrigger_event = xar.{event_id}",
                          "\t\t\t\t}",
                          "\t\t\t\t# XAR_ACCEPTANCE_ONLY_END",
                          f"\t\t\t\t# XAR_RELEASE_ONLY trigger_event = xar.{event_id}"])
            if milestone == 10:
                lines.append(f"\t\t\t\tset_global_variable = xa_contract_complete_{contract['id']}")
            lines.append("\t\t\t}")
        lines.append("\t\t}")
    lines.extend(["\t}", "}", "", "xar_complete_bargain_pair_effect = {",
                  "\tadd_trait_xp = { trait = xar_glassfire_gaze value = 1 }"])
    for level in range(10, 101, 10):
        event_id = 2200 + level // 10
        token = "reroll" if (level // 10) % 2 else "seal"
        lines.extend(["\tif = {", "\t\tlimit = {",
                      f"\t\t\thas_trait_xp = {{ trait = xar_glassfire_gaze value >= {level} }}",
                      f"\t\t\tNOT = {{ has_character_flag = xa_gaze_milestone_{level} }}", "\t\t}",
                      f"\t\tadd_character_flag = xa_gaze_milestone_{level}",
                      f"\t\tchange_global_variable = {{ name = xa_{token}_tokens add = 1 }}",
                      "\t\t# XAR_ACCEPTANCE_ONLY_BEGIN",
                      "\t\tif = {", "\t\t\tlimit = { NOT = { has_game_rule = xar_selftest } }",
                      f"\t\t\ttrigger_event = xar.{event_id}", "\t\t}",
                      "\t\t# XAR_ACCEPTANCE_ONLY_END",
                      f"\t\t# XAR_RELEASE_ONLY trigger_event = xar.{event_id}", "\t}"])
    lines.extend(["}", ""])
    return "\n".join(lines)


def generated_lessons():
    lines = [HEADER, "# Permanent per-contract PB and first-completion collection bits.", ""]
    for contract in CONTRACTS:
        key = contract["key"]
        for milestone in MILESTONES:
            lines.extend([
                f"xar_contract_pb_{key}_{milestone} = {{",
                "\tchain = reactive_advice", "\tdelay = 0", "\tshown_in_encyclopedia = no",
                f"\ttrigger = {{ has_global_variable = xa_contract_pb_{contract['id']}_{milestone} }}",
                f"\txar_contract_pb_{key}_{milestone}_step = {{",
                "\t\ttext = \"xar_silent_step\"",
                "\t\ttrigger_transition = { target = lesson_finish trigger = { always = yes } }",
                "\t}", "}", "",
            ])
        lines.extend([
            f"xar_contract_complete_{key} = {{",
            "\tchain = reactive_advice", "\tdelay = 0", "\tshown_in_encyclopedia = no",
            f"\ttrigger = {{ has_global_variable = xa_contract_complete_{contract['id']} }}",
            f"\txar_contract_complete_{key}_step = {{",
            "\t\ttext = \"xar_silent_step\"",
            "\t\ttrigger_transition = { target = lesson_finish trigger = { always = yes } }",
            "\t}", "}", "",
        ])
    return "\n".join(lines)


def generated_custom_loc():
    lines = [HEADER, "xar_contract_name = {", "\ttype = character"]
    for contract in CONTRACTS:
        lines.append(f"\ttext = {{ trigger = {{ global_var:xa_contract_id = {contract['id']} }} localization_key = xar_contract_{contract['key']} }}")
    lines.extend(["\ttext = { localization_key = xar_contract_none fallback = yes }", "}", ""])
    lines.extend(["xar_contract_collection = {", "\ttype = character"])
    for mask in range(63, -1, -1):
        checks = []
        for index, contract in enumerate(CONTRACTS):
            check = f"is_tutorial_lesson_completed = xar_contract_complete_{contract['key']}"
            checks.append(check if mask & (1 << index) else f"NOT = {{ {check} }}")
        lines.append(f"\ttext = {{ trigger = {{ {' '.join(checks)} }} localization_key = xar_contract_collection_{mask} }}")
    lines.extend(["\ttext = { localization_key = xar_contract_collection_0 fallback = yes }", "}", ""])
    lines.extend(["xar_contract_grade = {", "\ttype = character",
                  "\ttext = { trigger = { global_var:xa_contract_progress >= 10 } localization_key = xar_contract_grade_s }",
                  "\ttext = { trigger = { global_var:xa_contract_progress >= 6 } localization_key = xar_contract_grade_a }",
                  "\ttext = { trigger = { global_var:xa_contract_progress >= 3 } localization_key = xar_contract_grade_c }",
                  "\ttext = { localization_key = xar_contract_grade_d fallback = yes }", "}", ""])
    lines.extend(["xar_contract_pb = {", "\ttype = character"])
    for contract in CONTRACTS:
        for milestone in reversed(MILESTONES):
            lines.append(
                f"\ttext = {{ trigger = {{ global_var:xa_contract_id = {contract['id']} "
                f"is_tutorial_lesson_completed = xar_contract_pb_{contract['key']}_{milestone} }} "
                f"localization_key = xar_contract_pb_{milestone} }}")
    lines.extend(["\ttext = { localization_key = xar_contract_pb_0 fallback = yes }", "}", ""])
    return "\n".join(lines)


def loc_lines(lang):
    zh = lang == "simp_chinese"
    lines = [f"l_{lang}:", " # GENERATED FILE - do not edit. Regenerate with tools/gen_contracts.py"]
    lines.extend([
        f' xar_contract_none:0 "{"尚未立契" if zh else "No contract"}"',
        f' xar_contract_select_decision:0 "{"选择本世契约" if zh else "Choose a Lifetime Contract"}"',
        f' xar_contract_select_decision_desc:0 "{"让琉焰卿为此生写下一项增量目标。" if zh else "Let the Glassfire Lord write an incremental goal for this life."}"',
        f' xar_contract_select_decision_tooltip:0 "{"选择战争、权谋、信仰、家族、治理或享乐契约" if zh else "Choose a war, intrigue, faith, family, stewardship, or revelry contract"}"',
        f' xar_contract_select_decision_confirm:0 "{"请他落笔" if zh else "Let him write"}"',
        f' xar.2000.title:0 "{"此生的典当" if zh else "This Life in Pawn"}"',
        f' xar.2000.desc:0 "{"旅人，终末的总账固然诱人，但我也喜欢看一簇火如何选择自己的风向。挑一项吧；每次进展都会添入本世分量。" if zh else "Traveler, the final ledger is tempting, but I also enjoy watching a flame choose its wind. Pick one; each step will add to this life’s weight."}"',
        f' xar.0010.desc_clean:0 "{"旅人，你的前世余烬仍在，只是这条赛道没有留下可典当的预算。很好——空着双手抵达终末，称出的分量才更有意思。第一道垂青，我照旧记在账上。" if zh else "Traveler, your former embers remain, but this track leaves no spendable inheritance. Good—arriving at the end empty-handed makes the weighing more interesting. I shall still place the first favor on account."}"',
        f' xar.contract.milestone.title:0 "{"契页发亮" if zh else "The Contract Gleams"}"',
        f' xar.contract.milestone.3.ok:0 "{"第一笔，记下了。" if zh else "The first entry is made."}"',
        f' xar.contract.milestone.6.ok:0 "{"墨迹正在变暖。" if zh else "The ink is growing warm."}"',
        f' xar.contract.milestone.10.ok:0 "{"这份典当，已经圆满。" if zh else "This pawn is complete."}"',
        f' xar.gaze.milestone.title:0 "{"琉焰之视·新痕" if zh else "Glassfire Gaze: A New Mark"}"',
        f' xar.gaze.milestone.reroll:0 "{"垂青与咒痕积成了新的眼力。琉焰卿赠你一次重抽；并非免费，只是账期更长。" if zh else "Favors and curse-marks sharpen your sight. The Glassfire Lord grants one reroll; not free, merely billed later."}"',
        f' xar.gaze.milestone.seal:0 "{"火痕闭合成一枚封印。你可免去一次强制咒痕，而代价仍会以更温柔的方式留下。" if zh else "The marks close into a seal. You may waive one mandatory curse; its price will linger more gently."}"',
        f' xar.gaze.milestone.ok:0 "{"我收下这份迟来的好意。" if zh else "I accept this belated kindness."}"',
        f' xar.0004.reroll:0 "{"消耗一次重抽，换一页垂青" if zh else "Spend one reroll for new favors"}"',
        f' xar.0005.seal:0 "{"消耗一枚封印，免去此道咒痕" if zh else "Spend one seal to waive this curse-mark"}"',
        ' xar_contract_grade_s:0 "S"', ' xar_contract_grade_a:0 "A"',
        ' xar_contract_grade_c:0 "C"', ' xar_contract_grade_d:0 "D"',
        ' xar_contract_pb_0:0 "PB 0"', ' xar_contract_pb_3:0 "PB 3"',
        ' xar_contract_pb_6:0 "PB 6"', ' xar_contract_pb_10:0 "PB 10"',
    ])
    for contract in CONTRACTS:
        name = contract["name_zh"] if zh else contract["name_en"]
        goal = contract["goal_zh"] if zh else contract["goal_en"]
        lines.append(f' xar_contract_{contract["key"]}:0 "{name}"')
        lines.append(f' xar.2000.{contract["key"]}:0 "{name}：{goal}"')
        narratives = contract["milestones_zh"] if zh else contract["milestones_en"]
        for milestone, narrative in zip(MILESTONES, narratives):
            lines.append(f' xar.contract.{contract["key"]}.milestone.{milestone}:0 "{narrative}"')
            lines.append(f' xar_contract_pb_{contract["key"]}_{milestone}:0 "XAR_SYNC_SENTINEL"')
            lines.append(f' xar_contract_pb_{contract["key"]}_{milestone}_step:0 "XAR_SYNC_SENTINEL"')
        lines.append(f' xar_contract_complete_{contract["key"]}:0 "XAR_SYNC_SENTINEL"')
        lines.append(f' xar_contract_complete_{contract["key"]}_step:0 "XAR_SYNC_SENTINEL"')
    collection = "已完成契约" if zh else "Completed contracts"
    none = "无" if zh else "none"
    for mask in range(64):
        names = [item["name_zh"] if zh else item["name_en"]
                 for index, item in enumerate(CONTRACTS) if mask & (1 << index)]
        lines.append(f' xar_contract_collection_{mask}:0 "{collection}: {" / ".join(names) if names else none}"')
    ledger = ("\\n本世契约" if zh else "\\nLifetime contract")
    lines.append(
        f' xar.contract.ledger:0 "{ledger}: #V [ROOT.Char.Custom(\'xar_contract_name\')]#! · '
        "[TopScope.GetValue('xar_contract_progress')|0]/10 · [ROOT.Char.Custom('xar_contract_grade')] · [ROOT.Char.Custom('xar_contract_pb')] · "
        "R [TopScope.GetValue('xar_rerolls')|0] · S [TopScope.GetValue('xar_seals')|0] · "
        "[ROOT.Char.Custom('xar_contract_collection')]\"")
    return "\n".join(lines) + "\n"


def generated_doc():
    lines = ["# 本世契约与长期解锁", "", "<!-- GENERATED FILE - do not edit. Regenerate with tools/gen_contracts.py -->", "",
             "每项进度按 10 分计入死亡分数；3/6/10 时触发反馈并永久保存该契约 PB，10 时完成图鉴位。", "",
             "| ID | 契约 | 行为目标 |", "|---:|---|---|"]
    for contract in CONTRACTS:
        lines.append(f"| {contract['id']} | {contract['name_zh']} | {contract['goal_zh']} |")
    lines.extend(["", "【琉焰之视】每 10 XP 交替解锁重抽与封印，共 10 个里程碑事件。", ""])
    return "\n".join(lines)


def write_bom(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8-sig", newline="\n")


def main():
    write_bom(MOD / "events/xar_generated_contract_events.txt", generated_events())
    write_bom(MOD / "common/decisions/xar_generated_contract_decisions.txt", generated_decision())
    write_bom(MOD / "common/scripted_effects/xar_generated_contract_effects.txt", generated_effects())
    write_bom(MOD / "common/tutorial_lessons/xar_generated_contract_lessons.txt", generated_lessons())
    write_bom(MOD / "common/customizable_localization/xar_generated_contract_loc.txt", generated_custom_loc())
    for lang in LANGS:
        write_bom(MOD / f"localization/{lang}/xar_generated_contracts_l_{lang}.yml", loc_lines(lang))
    (ROOT / "docs/contracts-and-progression.md").write_text(generated_doc(), encoding="utf-8", newline="\n")
    print("generated contracts: 6 archetypes, 18 goal events, 10 gaze events, 9 languages")


if __name__ == "__main__":
    main()
