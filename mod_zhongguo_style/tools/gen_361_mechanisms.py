#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the playable, data-driven implementation of all 361 mechanisms."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from zg361_mechanism_data import (
    LEDGERS,
    MECHANISM_COUNT,
    Mechanism,
    load_mechanisms,
    mechanism_deltas,
)


MOD_ROOT = Path(__file__).resolve().parent.parent
GENERATED_HEADER = "# GENERATED FILE — edit tools/zg361_mechanism_data.py or tools/mechanism_choices/*.json\n"
BOM = b"\xef\xbb\xbf"


def script_text(body: str) -> bytes:
    return BOM + (GENERATED_HEADER + body.rstrip() + "\n").encode("utf-8")


def yml_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def loc_line(key: str, value: str) -> str:
    return f' {key}:0 "{yml_escape(value)}"'


def effect_name(mechanism_id: int, choice: str) -> str:
    return f"zg361_mechanism_{mechanism_id:03d}_choice_{choice}_effect"


def mechanism_choice_effect(mechanism: Mechanism, choice: str) -> str:
    deltas = mechanism_deltas(mechanism, choice)
    choice_value = {"a": 1, "b": 2, "c": 3}[choice]
    checksum_add = mechanism.id * choice_value
    lines = [
        f"{effect_name(mechanism.id, choice)} = {{",
        "\tif = {",
        f"\t\tlimit = {{ NOT = {{ has_variable = zg361_mechanism_{mechanism.id:03d}_choice }} }}",
        "\t\tzg361_init_org_ledger_effect = yes",
        f"\t\tset_variable = {{ name = zg361_mechanism_{mechanism.id:03d}_choice "
        f"value = {choice_value} }}",
    ]
    for ledger, delta in deltas.items():
        lines.append(
            f"\t\tchange_variable = {{ name = zg361_org_{ledger} add = {delta} }}"
        )
    lines.extend(
        [
            "\t\tchange_variable = { name = zg361_mechanism_configured_n add = 1 }",
            f"\t\tchange_variable = {{ name = zg361_mechanism_checksum add = {checksum_add} }}",
            f'\t\tdebug_log = "ZG361M: CASE {mechanism.id:03d} CHOICE {choice.upper()} APPLIED"',
            "\t}",
            "}",
        ]
    )
    return "\n".join(lines)


def ai_resolver(mechanism: Mechanism) -> str:
    return "\n".join(
        [
            f"zg361_mechanism_{mechanism.id:03d}_ai_effect = {{",
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\tOR = {",
            "\t\t\t\thas_trait = just",
            "\t\t\t\thas_trait = honest",
            "\t\t\t\thas_trait = diligent",
            "\t\t\t\thas_trait = compassionate",
            "\t\t\t}",
            "\t\t}",
            f"\t\t{effect_name(mechanism.id, 'a')} = yes",
            "\t}",
            "\telse_if = {",
            "\t\tlimit = {",
            "\t\t\tOR = {",
            "\t\t\t\thas_trait = arbitrary",
            "\t\t\t\thas_trait = callous",
            "\t\t\t\thas_trait = deceitful",
            "\t\t\t\thas_trait = ambitious",
            "\t\t\t}",
            "\t\t}",
            f"\t\t{effect_name(mechanism.id, 'b')} = yes",
            "\t}",
            "\telse_if = {",
            "\t\tlimit = {",
            "\t\t\thas_variable = zg361_org_budget_pressure",
            "\t\t\tvar:zg361_org_budget_pressure >= 25",
            "\t\t}",
            f"\t\t{effect_name(mechanism.id, 'c')} = yes",
            "\t}",
            "\telse = {",
            f"\t\t{effect_name(mechanism.id, mechanism.reference_choice)} = yes",
            "\t}",
            "}",
        ]
    )


def render_effects(mechanisms: list[Mechanism]) -> bytes:
    lines = [
        "# Shared organizational ledger and all mechanism state transitions.",
        "",
        "zg361_init_org_ledger_effect = {",
    ]
    for ledger in LEDGERS:
        lines.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ NOT = {{ has_variable = zg361_org_{ledger} }} }}",
                f"\t\tset_variable = {{ name = zg361_org_{ledger} value = 0 }}",
                "\t}",
            ]
        )
    for variable in ("zg361_mechanism_configured_n", "zg361_mechanism_checksum"):
        lines.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ NOT = {{ has_variable = {variable} }} }}",
                f"\t\tset_variable = {{ name = {variable} value = 0 }}",
                "\t}",
            ]
        )
    lines.extend(["}", ""])

    for mechanism in mechanisms:
        lines.append(f"# {mechanism.id:03d} {mechanism.title_cn}")
        for choice in ("a", "b", "c"):
            lines.extend([mechanism_choice_effect(mechanism, choice), ""])
        lines.extend([ai_resolver(mechanism), ""])

    lines.extend(
        [
            "# Trigger the first unresolved player-facing policy card.",
            "zg361_mechanism_dispatch_next_effect = {",
            "\tzg361_init_org_ledger_effect = yes",
        ]
    )
    for index, mechanism in enumerate(mechanisms):
        keyword = "if" if index == 0 else "else_if"
        lines.extend(
            [
                f"\t{keyword} = {{",
                f"\t\tlimit = {{ NOT = {{ has_variable = zg361_mechanism_{mechanism.id:03d}_choice }} }}",
                f"\t\ttrigger_event = {{ id = zg361m.{mechanism.id} days = 1 }}",
                "\t}",
            ]
        )
    lines.extend(
        [
            "\telse = {",
            '\t\tdebug_log = "ZG361M: all 361 mechanisms already configured"',
            "\t}",
            "}",
            "",
            "# AI managers configure twelve consecutive cards per completed review.",
            "zg361_mechanism_ai_batch_effect = {",
            "\tzg361_init_org_ledger_effect = yes",
            "\tif = {",
            "\t\tlimit = { NOT = { has_variable = zg361_mechanism_ai_batch } }",
            "\t\tset_variable = { name = zg361_mechanism_ai_batch value = 0 }",
            "\t}",
        ]
    )
    batch_size = 12
    for batch_index, start in enumerate(range(0, len(mechanisms), batch_size)):
        keyword = "if" if batch_index == 0 else "else_if"
        chunk = mechanisms[start : start + batch_size]
        lines.extend(
            [
                f"\t{keyword} = {{",
                f"\t\tlimit = {{ var:zg361_mechanism_ai_batch = {batch_index} }}",
            ]
        )
        for mechanism in chunk:
            lines.append(f"\t\tzg361_mechanism_{mechanism.id:03d}_ai_effect = yes")
        lines.extend(
            [
                "\t\tchange_variable = { name = zg361_mechanism_ai_batch add = 1 }",
                "\t}",
            ]
        )
    lines.extend(["\tzg361_refresh_org_climate_effect = yes", "}", ""])

    lines.extend(
        [
            "# Turnkey deployment: a real player choice and the live acceptance batch entry.",
            "zg361_adopt_reference_charter_effect = {",
            "\tzg361_init_org_ledger_effect = yes",
        ]
    )
    for mechanism in mechanisms:
        lines.append(f"\t{effect_name(mechanism.id, mechanism.reference_choice)} = yes")
    lines.extend(
        [
            "\tzg361_refresh_org_climate_effect = yes",
            '\tdebug_log = "ZG361M: REFERENCE CHARTER COMPLETE 361"',
            "}",
            "",
            "zg361_refresh_org_climate_effect = {",
            "\tremove_character_modifier = zg361_org_high_trust",
            "\tremove_character_modifier = zg361_org_admin_overload",
            "\tremove_character_modifier = zg361_org_burnout_crisis",
            "\tremove_character_modifier = zg361_org_delivery_stable",
            "\tremove_character_modifier = zg361_org_tech_debt_crisis",
            "\tremove_character_modifier = zg361_org_talent_healthy",
            "\tif = {",
            "\t\tlimit = { var:zg361_org_trust >= 20 }",
            "\t\tadd_character_modifier = { modifier = zg361_org_high_trust years = 1 }",
            "\t}",
            "\tif = {",
            "\t\tlimit = { var:zg361_org_admin_load >= 35 }",
            "\t\tadd_character_modifier = { modifier = zg361_org_admin_overload years = 1 }",
            "\t}",
            "\tif = {",
            "\t\tlimit = { var:zg361_org_burnout >= 20 }",
            "\t\tadd_character_modifier = { modifier = zg361_org_burnout_crisis years = 1 }",
            "\t}",
            "\tif = {",
            "\t\tlimit = { var:zg361_org_stability >= 20 }",
            "\t\tadd_character_modifier = { modifier = zg361_org_delivery_stable years = 1 }",
            "\t}",
            "\tif = {",
            "\t\tlimit = { var:zg361_org_tech_debt >= 20 }",
            "\t\tadd_character_modifier = { modifier = zg361_org_tech_debt_crisis years = 1 }",
            "\t}",
            "\tif = {",
            "\t\tlimit = { var:zg361_org_talent >= 20 }",
            "\t\tadd_character_modifier = { modifier = zg361_org_talent_healthy years = 1 }",
            "\t}",
            "}",
        ]
    )
    return script_text("\n".join(lines))


def render_values() -> bytes:
    body = r'''# Shared ledgers feed both the manager's own review and the team's climate.

zg361_manager_mechanism_kpi_value = {
	value = 0
	if = { limit = { has_variable = zg361_org_delivery } add = { value = var:zg361_org_delivery multiply = 0.12 } }
	if = { limit = { has_variable = zg361_org_stability } add = { value = var:zg361_org_stability multiply = 0.10 } }
	if = { limit = { has_variable = zg361_org_trust } add = { value = var:zg361_org_trust multiply = 0.08 } }
	if = { limit = { has_variable = zg361_org_talent } add = { value = var:zg361_org_talent multiply = 0.08 } }
	if = { limit = { has_variable = zg361_org_data_quality } add = { value = var:zg361_org_data_quality multiply = 0.05 } }
	if = { limit = { has_variable = zg361_org_evidence } add = { value = var:zg361_org_evidence multiply = 0.05 } }
	if = { limit = { has_variable = zg361_org_burnout } subtract = { value = var:zg361_org_burnout multiply = 0.10 } }
	if = { limit = { has_variable = zg361_org_tech_debt } subtract = { value = var:zg361_org_tech_debt multiply = 0.08 } }
	if = { limit = { has_variable = zg361_org_pay_debt } subtract = { value = var:zg361_org_pay_debt multiply = 0.08 } }
	if = { limit = { has_variable = zg361_org_appeal_risk } subtract = { value = var:zg361_org_appeal_risk multiply = 0.08 } }
	if = { limit = { has_variable = zg361_org_policy_debt } subtract = { value = var:zg361_org_policy_debt multiply = 0.06 } }
	if = { limit = { has_variable = zg361_org_admin_load } subtract = { value = var:zg361_org_admin_load multiply = 0.04 } }
	min = -50
	max = 30
}

zg361_team_mechanism_kpi_value = {
	value = 0
	if = { limit = { liege = { has_variable = zg361_org_trust } } add = { value = liege.var:zg361_org_trust multiply = 0.03 } }
	if = { limit = { liege = { has_variable = zg361_org_stability } } add = { value = liege.var:zg361_org_stability multiply = 0.03 } }
	if = { limit = { liege = { has_variable = zg361_org_talent } } add = { value = liege.var:zg361_org_talent multiply = 0.02 } }
	if = { limit = { liege = { has_variable = zg361_org_burnout } } subtract = { value = liege.var:zg361_org_burnout multiply = 0.04 } }
	if = { limit = { liege = { has_variable = zg361_org_tech_debt } } subtract = { value = liege.var:zg361_org_tech_debt multiply = 0.03 } }
	if = { limit = { liege = { has_variable = zg361_org_policy_debt } } subtract = { value = liege.var:zg361_org_policy_debt multiply = 0.03 } }
	min = -25
	max = 15
}
'''
    return script_text(body)


def render_modifiers() -> bytes:
    body = r'''zg361_org_high_trust = {
	direct_vassal_opinion = 5
	monthly_prestige = 0.2
}

zg361_org_admin_overload = {
	stewardship = -1
	stress_gain_mult = 0.1
}

zg361_org_burnout_crisis = {
	diplomacy = -1
	stress_gain_mult = 0.25
}

zg361_org_delivery_stable = {
	stewardship = 1
	monthly_prestige = 0.1
}

zg361_org_tech_debt_crisis = {
	stewardship = -1
	learning = -1
}

zg361_org_talent_healthy = {
	diplomacy = 1
	stress_gain_mult = -0.05
}
'''
    return script_text(body)


def render_events(mechanisms: list[Mechanism]) -> bytes:
    lines = ["namespace = zg361m", ""]
    for mechanism in mechanisms:
        lines.extend(
            [
                f"# {mechanism.id:03d} {mechanism.title_cn}",
                f"zg361m.{mechanism.id} = {{",
                "\ttype = character_event",
                "\ttheme = crown",
                f"\ttitle = zg361m.{mechanism.id}.t",
                f"\tdesc = zg361m.{mechanism.id}.desc",
                "\ttrigger = {",
                "\t\thas_game_rule = zg361_on",
                "\t\tzg361_is_celestial_liege_trigger = yes",
                f"\t\tNOT = {{ has_variable = zg361_mechanism_{mechanism.id:03d}_choice }}",
                "\t}",
            ]
        )
        for choice in ("a", "b", "c"):
            lines.extend(
                [
                    "\toption = {",
                    f"\t\tname = zg361m.{mechanism.id}.{choice}",
                    f"\t\tcustom_tooltip = zg361_mechanism_choice_{choice}_tt",
                    f"\t\t{effect_name(mechanism.id, choice)} = yes",
                    "\t\tzg361_refresh_org_climate_effect = yes",
                ]
            )
            if choice == "a":
                lines.extend(
                    [
                        "\t\tai_chance = {",
                        "\t\t\tbase = 55",
                        "\t\t\tmodifier = { add = 35 has_trait = just }",
                        "\t\t\tmodifier = { add = 25 has_trait = diligent }",
                        "\t\t}",
                    ]
                )
            elif choice == "b":
                lines.extend(
                    [
                        "\t\tai_chance = {",
                        "\t\t\tbase = 35",
                        "\t\t\tmodifier = { add = 35 has_trait = arbitrary }",
                        "\t\t\tmodifier = { add = 25 has_trait = ambitious }",
                        "\t\t}",
                    ]
                )
            else:
                lines.extend(
                    [
                        "\t\tai_chance = {",
                        "\t\t\tbase = 10",
                        "\t\t\tmodifier = {",
                        "\t\t\t\tadd = 25",
                        "\t\t\t\thas_variable = zg361_org_budget_pressure",
                        "\t\t\t\tvar:zg361_org_budget_pressure >= 25",
                        "\t\t\t}",
                        "\t\t}",
                    ]
                )
            lines.append("\t}")
        lines.extend(["}", ""])
    return script_text("\n".join(lines))


def render_decisions() -> bytes:
    body = r'''# Optional acceleration tools. Normal reviews still surface one policy card at a time.

zg361_next_mechanism_decision = {
	decision_group_type = zg361
	picture = { reference = "gfx/interface/illustrations/decisions/decision_realm.dds" }
	ai_check_interval = 0
	cooldown = { days = 30 }
	is_shown = {
		zg361_is_celestial_liege_trigger = yes
		has_game_rule = zg361_on
		trigger_if = {
			limit = { has_variable = zg361_mechanism_configured_n }
			var:zg361_mechanism_configured_n < 361
		}
	}
	is_valid = { NOT = { has_character_flag = zg361_mechanism_next_pending } }
	is_valid_showing_failures_only = { NOT = { has_character_flag = zg361_mechanism_next_pending } }
	effect = { add_character_flag = zg361_mechanism_next_pending }
}

zg361_reference_charter_decision = {
	decision_group_type = zg361
	picture = { reference = "gfx/interface/illustrations/decisions/decision_realm.dds" }
	ai_check_interval = 0
	cooldown = { years = 50 }
	is_shown = {
		zg361_is_celestial_liege_trigger = yes
		has_game_rule = zg361_on
		trigger_if = {
			limit = { has_variable = zg361_mechanism_configured_n }
			var:zg361_mechanism_configured_n < 361
		}
	}
	is_valid = {
		prestige >= 250
		NOT = { has_character_flag = zg361_reference_charter_pending }
	}
	is_valid_showing_failures_only = { prestige >= 250 }
	cost = { prestige = 250 }
	effect = { add_character_flag = zg361_reference_charter_pending }
}
'''
    return script_text(body)


def render_scripted_guis() -> bytes:
    body = r'''zg361_mechanism_next_bridge_gui = {
	scope = character
	is_shown = { is_ai = no has_character_flag = zg361_mechanism_next_pending }
	effect = {
		remove_character_flag = zg361_mechanism_next_pending
		zg361_mechanism_dispatch_next_effect = yes
	}
}

zg361_reference_charter_bridge_gui = {
	scope = character
	is_shown = { is_ai = no has_character_flag = zg361_reference_charter_pending }
	effect = {
		remove_character_flag = zg361_reference_charter_pending
		zg361_adopt_reference_charter_effect = yes
	}
}

zg361_mechanism_ledger_available_gui = {
	scope = character
	is_shown = {
		has_game_rule = zg361_on
		zg361_is_celestial_liege_trigger = yes
		has_variable = zg361_mechanism_configured_n
	}
}
'''
    return script_text(body)


def render_bridge_gui() -> bytes:
    body = r'''window = {
	name = "zg361_mechanism_bridge_window"
	size = { 1 1 }
	layer = tutorial
	position = { 0 0 }
	visible = "[GetPlayer.IsValid]"
	alwaystransparent = yes

	state = { name = _show using = Animation_FadeIn_Quick }
	state = { name = _hide using = Animation_FadeOut_Quick }
	state = {
		name = "zg361_mechanism_next"
		trigger_when = "[GetScriptedGui('zg361_mechanism_next_bridge_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		on_start = "[GetScriptedGui('zg361_mechanism_next_bridge_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
	}
	state = {
		name = "zg361_reference_charter"
		trigger_when = "[GetScriptedGui('zg361_reference_charter_bridge_gui').IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		on_start = "[GetScriptedGui('zg361_reference_charter_bridge_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
	}
}
'''
    return script_text(body)


def localization_values(
    mechanisms: list[Mechanism], language: str
) -> dict[str, str]:
    is_chinese = language == "simp_chinese"
    is_english = language == "english"
    # Release translation replaces these structurally valid English placeholders
    # in the other seven languages.
    common = {
        "zg361_next_mechanism_decision": "召开下一项制度评审" if is_chinese else "Review the Next Performance Policy",
        "zg361_next_mechanism_decision_desc": "从尚未定案的 361 机制中提取下一项，作出会进入组织账本的真实选择。" if is_chinese else "Open the next unresolved item in the 361 policy catalogue and make a choice that enters the organizational ledger.",
        "zg361_next_mechanism_decision_tooltip": "打开下一项 361 制度卡片。" if is_chinese else "Open the next 361 policy card.",
        "zg361_next_mechanism_decision_confirm": "叫下一位产品经理进来" if is_chinese else "Bring in the next policy owner",
        "zg361_reference_charter_decision": "一键部署《大厂全家桶》" if is_chinese else "Deploy the Reference 361 Charter",
        "zg361_reference_charter_decision_desc": "一次性采用 361 项推荐默认值。省下三十年开会时间，也会立刻背上完整的行政、预算和组织后果。" if is_chinese else "Adopt the recommended default for all 361 policies at once. It saves decades of meetings and immediately carries the full administrative, fiscal, and organizational consequences.",
        "zg361_reference_charter_decision_tooltip": "一次结算全部 361 项，不是纯展示按钮。" if is_chinese else "Resolve all 361 items in one real, state-changing batch.",
        "zg361_reference_charter_decision_confirm": "我全都要，现在就要" if is_chinese else "Ship the entire portfolio",
        "zg361_mechanism_choice_a_tt": "长期路线：证据、信任或能力更强，但要支付行政、预算或短期交付成本。" if is_chinese else "Durable route: improves evidence, trust, or capability while consuming administrative, fiscal, or short-term delivery capacity.",
        "zg361_mechanism_choice_b_tt": "冲刺路线：眼前结果更漂亮，但把风险、倦怠、技术债或申诉债留给未来。" if is_chinese else "Sprint route: improves the immediate result while carrying risk, burnout, technical debt, or appeal debt into later reviews.",
        "zg361_mechanism_choice_c_tt": "暂缓路线：现在少开一场会，但明确增加制度债；它会进入你自己的上司考核。" if is_chinese else "Deferral route: saves effort now but records policy debt that feeds your own superior's next review.",
        "zg361_scoreboard_tab_system": "制度驾驶舱" if is_chinese else "Policy Cockpit",
        "zg361_ledger_title": "361 制度账本：漂亮报表下面那一层" if is_chinese else "361 Policy Ledger: What Sits Beneath the Dashboard",
        "zg361_ledger_configured": "已定案机制" if is_chinese else "Configured mechanisms",
        "zg361_ledger_checksum": "组合校验码" if is_chinese else "Portfolio checksum",
        "zg361_ledger_explainer": "正值不都代表好事：行政负担、申诉风险、技术债、倦怠、HC 压力、薪酬债、制度债和预算压力越高越危险。" if is_chinese else "Positive is not always good: administrative load, appeal risk, technical debt, burnout, HC pressure, pay debt, policy debt, and budget pressure become dangerous as they rise.",
        "zg361_ledger_evidence": "证据质量" if is_chinese else "Evidence quality",
        "zg361_ledger_trust": "组织信任" if is_chinese else "Organizational trust",
        "zg361_ledger_admin_load": "绩效行政负担" if is_chinese else "Performance administration load",
        "zg361_ledger_appeal_risk": "申诉与程序风险" if is_chinese else "Appeal and process risk",
        "zg361_ledger_delivery": "真实交付价值" if is_chinese else "Delivered value",
        "zg361_ledger_stability": "稳定性" if is_chinese else "Stability",
        "zg361_ledger_tech_debt": "技术债" if is_chinese else "Technical debt",
        "zg361_ledger_data_quality": "数据可信度" if is_chinese else "Data quality",
        "zg361_ledger_burnout": "组织倦怠" if is_chinese else "Organizational burnout",
        "zg361_ledger_talent": "人才健康" if is_chinese else "Talent health",
        "zg361_ledger_hc_pressure": "HC 压力" if is_chinese else "Headcount pressure",
        "zg361_ledger_pay_debt": "薪酬债" if is_chinese else "Pay debt",
        "zg361_ledger_policy_debt": "制度债" if is_chinese else "Policy debt",
        "zg361_ledger_budget_pressure": "预算压力" if is_chinese else "Budget pressure",
        "zg361_ledger_hint": "这些账会进入团队下一轮 KPI，也会进入上司对你的管理绩效考核。" if is_chinese else "These ledgers feed the team's next KPI and your superior's assessment of your management performance.",
    }
    modifier_loc = {
        "zg361_org_high_trust": "组织信任：这届管理层说话还算数" if is_chinese else "Organizational Trust: Management Keeps Its Word",
        "zg361_org_high_trust_desc": "证据、反馈与兑现形成正循环。" if is_chinese else "Evidence, feedback, and delivery reinforce one another.",
        "zg361_org_admin_overload": "绩效行政过载" if is_chinese else "Performance Administration Overload",
        "zg361_org_admin_overload_desc": "大家忙着解释为什么大家都在忙。" if is_chinese else "Everyone is busy explaining why everyone is busy.",
        "zg361_org_burnout_crisis": "组织倦怠危机" if is_chinese else "Organizational Burnout Crisis",
        "zg361_org_burnout_crisis_desc": "在线时长很漂亮，人的电量不太漂亮。" if is_chinese else "Online hours look excellent; human batteries do not.",
        "zg361_org_delivery_stable": "稳定交付文化" if is_chinese else "Stable Delivery Culture",
        "zg361_org_delivery_stable_desc": "不是每次上线都要先准备一份检讨。" if is_chinese else "Not every release begins with drafting an apology.",
        "zg361_org_tech_debt_crisis": "技术债利滚利" if is_chinese else "Compounding Technical Debt",
        "zg361_org_tech_debt_crisis_desc": "昨日的捷径已成为今日的收费站。" if is_chinese else "Yesterday's shortcut has become today's toll gate.",
        "zg361_org_talent_healthy": "人才梯队健康" if is_chinese else "Healthy Talent Pipeline",
        "zg361_org_talent_healthy_desc": "明星、接班人和普通人都还有路可走。" if is_chinese else "Stars, successors, and steady contributors can all see a path forward.",
    }
    common.update(modifier_loc)
    values = dict(common)

    for mechanism in mechanisms:
        if is_chinese:
            title = f"#{mechanism.id:03d} · {mechanism.title_cn}"
            desc = (
                f"【{mechanism.group_code} · {mechanism.group_title}／{mechanism.priority}】\\n\\n"
                f"决策：{mechanism.decision_cn}\\n\\n后果：{mechanism.consequence_cn}"
            )
            option_a = mechanism.option_a_cn
            option_b = mechanism.option_b_cn
            option_c = "这季度先不碰，登记制度债"
        else:
            title = f"#{mechanism.id:03d} · {mechanism.title_en}"
            desc = (
                f"[{mechanism.group_code} / {mechanism.priority}] This policy is implemented through the shared "
                "organizational ledger. Its selected rule changes delivery, evidence, trust, workload, risk, "
                "talent, or fiscal pressure and therefore affects later team results and the manager's own review."
            )
            option_a = mechanism.option_a_en
            option_b = mechanism.option_b_en
            option_c = "Defer it and record explicit policy debt"
        values.update(
            {
                f"zg361m.{mechanism.id}.t": title,
                f"zg361m.{mechanism.id}.desc": desc,
                f"zg361m.{mechanism.id}.a": option_a,
                f"zg361m.{mechanism.id}.b": option_b,
                f"zg361m.{mechanism.id}.c": option_c,
            }
        )
    return values


RELEASE_TRANSLATION_LANGUAGES = {
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
}


def release_translation_source_sha256(mechanisms: list[Mechanism]) -> str:
    payload = {
        "english": localization_values(mechanisms, "english"),
        "simp_chinese": localization_values(mechanisms, "simp_chinese"),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_release_translation(
    mechanisms: list[Mechanism], language: str, expected_keys: tuple[str, ...]
) -> dict[str, str] | None:
    path = MOD_ROOT / "tools" / "mechanism_translations" / f"{language}.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise ValueError(f"invalid release translation schema: {path}")
    if payload.get("language") != language:
        raise ValueError(f"release translation language mismatch: {path}")
    expected_digest = release_translation_source_sha256(mechanisms)
    if payload.get("source_sha256") != expected_digest:
        raise ValueError(f"stale release translation source hash: {path}")
    translations = payload.get("translations")
    if not isinstance(translations, dict):
        raise ValueError(f"release translation values must be an object: {path}")
    if tuple(translations) != expected_keys:
        missing = sorted(set(expected_keys) - set(translations))
        extra = sorted(set(translations) - set(expected_keys))
        raise ValueError(
            f"release translation key/order mismatch: {path}; missing={missing} extra={extra}"
        )
    if not all(isinstance(value, str) and value for value in translations.values()):
        raise ValueError(f"release translation contains empty/non-string value: {path}")
    return translations


def render_localization(mechanisms: list[Mechanism], language: str) -> bytes:
    values = localization_values(mechanisms, language)
    if language in RELEASE_TRANSLATION_LANGUAGES:
        translated = load_release_translation(mechanisms, language, tuple(values))
        if translated is not None:
            values = translated
    lines = [f"l_{language}:"]
    lines.extend(loc_line(key, value) for key, value in values.items())
    return BOM + ("\n".join(lines) + "\n").encode("utf-8")


def wave_for(mechanism_id: int) -> int:
    if (
        1 <= mechanism_id <= 18
        or 37 <= mechanism_id <= 53
        or 69 <= mechanism_id <= 81
        or 135 <= mechanism_id <= 204
    ):
        return 1
    if (
        19 <= mechanism_id <= 25
        or mechanism_id == 34
        or 82 <= mechanism_id <= 120
        or 129 <= mechanism_id <= 130
        or 254 <= mechanism_id <= 333
    ):
        return 2
    if (
        26 <= mechanism_id <= 31
        or 54 <= mechanism_id <= 68
        or 121 <= mechanism_id <= 128
        or 131 <= mechanism_id <= 134
        or 205 <= mechanism_id <= 253
        or 334 <= mechanism_id <= 354
    ):
        return 3
    return 4


def manifest_payload(mechanisms: list[Mechanism]) -> dict[str, object]:
    items = []
    for mechanism in mechanisms:
        items.append(
            {
                "id": mechanism.id,
                "group": mechanism.group_code,
                "group_title": mechanism.group_title,
                "priority": mechanism.priority,
                "title_cn": mechanism.title_cn,
                "title_en": mechanism.title_en,
                "profile": mechanism.profile,
                "reference_choice": mechanism.reference_choice,
                "implementation": {
                    "event": f"zg361m.{mechanism.id}",
                    "choice_effects": [
                        effect_name(mechanism.id, choice) for choice in ("a", "b", "c")
                    ],
                    "ai_effect": f"zg361_mechanism_{mechanism.id:03d}_ai_effect",
                    "policy_variable": f"zg361_mechanism_{mechanism.id:03d}_choice",
                    "debug_marker": f"ZG361M: CASE {mechanism.id:03d}",
                },
                "actor_boundary": "celestial duke-or-higher manager; counts/barons remain assessed-only",
                "state_changes": {
                    choice: mechanism_deltas(mechanism, choice) for choice in ("a", "b", "c")
                },
                "player_path": "annual review card or next-policy decision",
                "ai_path": "twelve-card annual background batch",
                "live_wave": wave_for(mechanism.id),
                "status": "fixture-live",
            }
        )
    return {
        "schema": 1,
        "mechanism_count": MECHANISM_COUNT,
        "source": "docs/361-expansion-options.md",
        "acceptance": {
            "scope": "reference choice for every mechanism executed in one real CK3 fixture batch",
            "report": "docs/testing-report-2026-08-29.md",
            "run_id": "zga_20260829_061314_ea5f04ad",
            "report_sha256": "DCCF8B87D990BA3ED3074FAE3391E5004E6CD8B07A5C80750BC344E7F9024C25",
            "claim_boundary": "fixture-live does not mean all 1083 A/B/C branches were manually clicked",
        },
        "generated_files": [],
        "items": items,
    }


def render_manifest_md(mechanisms: list[Mechanism], payload: dict[str, object]) -> bytes:
    lines = [
        "# 361 机制实现映射",
        "",
        "> GENERATED FILE — edit the numbered design document or reviewed choice JSON.",
        "",
        "状态口径：本表当前 `fixture-live` 表示 361 项各自的参考路线已在同一次真实 CK3 夹具批次中逐号执行，",
        "并验证唯一状态与组织账后果；它不表示 1083 个 A/B/C 分支都经过人工 UI 点选。证据见",
        "`docs/testing-report-2026-08-29.md`，run `zga_20260829_061314_ea5f04ad`。",
        "",
        "| ID | 机制 | 组 | P | Profile | 玩家入口 | AI 入口 | 实机波次 | 状态 |",
        "|---:|---|---|---|---|---|---|---:|---|",
    ]
    for mechanism in mechanisms:
        lines.append(
            f"| {mechanism.id:03d} | {mechanism.title_cn} | {mechanism.group_code} | "
            f"{mechanism.priority} | `{mechanism.profile}` | `zg361m.{mechanism.id}` | "
            f"`zg361_mechanism_{mechanism.id:03d}_ai_effect` | {wave_for(mechanism.id)} | fixture-live |"
        )
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    lines.extend(["", f"Manifest semantic SHA-256: `{digest}`", ""])
    return ("\n".join(lines)).encode("utf-8")


def outputs(mechanisms: list[Mechanism]) -> dict[Path, bytes]:
    payload = manifest_payload(mechanisms)
    result: dict[Path, bytes] = {
        MOD_ROOT / "common" / "scripted_effects" / "zg361_generated_mechanism_effects.txt": render_effects(mechanisms),
        MOD_ROOT / "common" / "script_values" / "zg361_generated_mechanism_values.txt": render_values(),
        MOD_ROOT / "common" / "modifiers" / "zg361_generated_mechanism_modifiers.txt": render_modifiers(),
        MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt": render_events(mechanisms),
        MOD_ROOT / "common" / "decisions" / "zg361_mechanism_decisions.txt": render_decisions(),
        MOD_ROOT / "common" / "scripted_guis" / "zg361_generated_mechanism_guis.txt": render_scripted_guis(),
        MOD_ROOT / "gui" / "zg361_mechanism_bridge.gui": render_bridge_gui(),
    }
    for language in (
        "english",
        "simp_chinese",
        "french",
        "german",
        "japanese",
        "korean",
        "polish",
        "russian",
        "spanish",
    ):
        result[
            MOD_ROOT
            / "localization"
            / language
            / f"zg361_mechanisms_l_{language}.yml"
        ] = render_localization(mechanisms, language)
    payload["generated_files"] = sorted(
        path.relative_to(MOD_ROOT).as_posix() for path in result
    )
    manifest_json = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    result[MOD_ROOT / "docs" / "361-mechanism-manifest.json"] = manifest_json.encode("utf-8")
    result[MOD_ROOT / "docs" / "361-mechanism-implementation-manifest.md"] = render_manifest_md(
        mechanisms, payload
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--allow-generic", action="store_true")
    args = parser.parse_args(argv)
    try:
        mechanisms = load_mechanisms(
            MOD_ROOT, require_reviewed_choices=not args.allow_generic
        )
        rendered = outputs(mechanisms)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"RED: {error}")
        return 1

    mismatches: list[str] = []
    for path, data in rendered.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                mismatches.append(path.relative_to(MOD_ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if mismatches:
        print("RED: generated files are stale:")
        for mismatch in mismatches:
            print(f"  - {mismatch}")
        return 1
    verb = "checked" if args.check else "generated"
    print(f"GREEN: {verb} {MECHANISM_COUNT} mechanisms across {len(rendered)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
