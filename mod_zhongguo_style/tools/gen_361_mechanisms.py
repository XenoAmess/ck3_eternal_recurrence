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
from zg361_phase2_runtime_data import PHASE2_RUNTIME_SPECS
from zg361_domain_data import (
    DOMAIN_SPECS,
    RUNTIME_PLAN_SCHEMA,
    build_runtime_plans,
)
from zg361_operation_registry import primitive_recipe_for
from zg361_effect_sharding import MAX_EFFECTS_PER_SHARD, plan_effect_shards
from zg361_localization_style import normalize_player_chinese
from zg361_readiness_data import (
    CENTRAL_WIRING_BOUNDARY,
    CUMULATIVE_COUNTS,
    EXPECTED_CUMULATIVE_RANGES,
    EXPECTED_EXCLUSIVE_RANGES,
    EXCLUSIVE_COUNTS,
    LATEST_PRODUCT_ACCEPTANCE,
    LEVELS,
    LIVE_BOUNDARY,
    MECHANISM_COUNT as READINESS_MECHANISM_COUNT,
    READINESS_BY_ID,
    RECENT_PRODUCT_ACCEPTANCE_ATTEMPTS,
    ReadinessLevel,
    format_ranges,
    ids_at_least,
    ids_at_level,
)


MOD_ROOT = Path(__file__).resolve().parent.parent
EFFECTS_DIR = MOD_ROOT / "common" / "scripted_effects"
GENERATED_HEADER = "# GENERATED FILE — edit tools/zg361_mechanism_data.py or tools/mechanism_choices/*.json\n"
BOM = b"\xef\xbb\xbf"
LEGACY_EFFECTS_PATH = EFFECTS_DIR / "zg361_generated_mechanism_effects.txt"
EFFECT_SHARD_GLOB = "zg361_generated_mechanism_*_effects.txt"

# These catalogue choices currently have no domain-specific consumer.  They
# are still real policy-ledger choices, but must never tell the player that a
# payment, appointment, transfer, hire, refund or other concrete business
# action has already happened.  Keep this list explicit until each item gains
# a typed consumer and is removed by the corresponding implementation change.
LEDGER_ONLY_MECHANISM_IDS = frozenset(
    (*range(18, 32), 38, 39, 42, *range(44, 47), *range(48, 53),
     *range(54, 69), *range(82, 135), *range(146, 192),
     *range(229, 345), *range(355, 358), 360, 361)
)

LEDGER_LABELS_CN = {
    "evidence": "证据",
    "trust": "信任",
    "admin_load": "行政负担",
    "appeal_risk": "申诉风险",
    "delivery": "交付",
    "stability": "稳定",
    "tech_debt": "技术债",
    "data_quality": "数据质量",
    "burnout": "倦怠",
    "talent": "人才",
    "hc_pressure": "编制压力",
    "pay_debt": "薪酬债",
    "policy_debt": "制度债",
    "budget_pressure": "预算压力",
}
POSITIVE_LEDGERS = frozenset(
    {"evidence", "trust", "delivery", "stability", "data_quality", "talent"}
)


def script_text(body: str) -> bytes:
    return BOM + (GENERATED_HEADER + body.rstrip() + "\n").encode("utf-8")


def yml_escape(text: str) -> str:
    # CK3 localization interprets a single literal ``\n`` sequence as a line
    # break. Escape all other backslashes while preserving that engine token.
    return r"\n".join(
        part.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        for part in text.split(r"\n")
    )


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
        ]
    )
    for ledger, threshold, modifier in (
        ("trust", 20, "zg361_org_high_trust"),
        ("admin_load", 35, "zg361_org_admin_overload"),
        ("burnout", 20, "zg361_org_burnout_crisis"),
        ("stability", 20, "zg361_org_delivery_stable"),
        ("tech_debt", 20, "zg361_org_tech_debt_crisis"),
        ("talent", 20, "zg361_org_talent_healthy"),
    ):
        variable = f"zg361_org_{ledger}"
        lines.extend(
            [
                "\tif = {",
                "\t\tlimit = {",
                "\t\t\ttrigger_if = {",
                f"\t\t\t\tlimit = {{ has_variable = {variable} }}",
                f"\t\t\t\tvar:{variable} >= {threshold}",
                "\t\t\t}",
                "\t\t\ttrigger_else = { always = no }",
                "\t\t}",
                f"\t\tadd_character_modifier = {{ modifier = {modifier} years = 1 }}",
                "\t}",
            ]
        )
    lines.append("}")
    return script_text("\n".join(lines))


def effect_purpose(name: str) -> str:
    """Map every mechanism definition to a small, stable purpose family."""

    if name == "zg361_init_org_ledger_effect":
        return "ledger_bootstrap"
    prefix = "zg361_mechanism_"
    if name.startswith(prefix) and len(name) >= len(prefix) + 3:
        digits = name[len(prefix) : len(prefix) + 3]
        if digits.isdigit():
            mechanism_id = int(digits)
            if 1 <= mechanism_id <= MECHANISM_COUNT:
                first = ((mechanism_id - 1) // 2) * 2 + 1
                last = min(first + 1, MECHANISM_COUNT)
                return f"policy_{first:03d}_{last:03d}"
    helpers = {
        "zg361_mechanism_dispatch_next_effect": "player_dispatch",
        "zg361_mechanism_ai_batch_effect": "ai_batch",
        "zg361_adopt_reference_charter_effect": "reference_charter",
        "zg361_refresh_org_climate_effect": "org_climate",
    }
    try:
        return helpers[name]
    except KeyError as error:
        raise ValueError(f"unclassified mechanism scripted effect: {name}") from error


def effect_shard_outputs(mechanisms: list[Mechanism]) -> dict[Path, bytes]:
    """Render purpose-grouped effect files with a 1-10 definition boundary."""

    shards = plan_effect_shards(
        render_effects(mechanisms),
        generated_header=GENERATED_HEADER,
        classify=effect_purpose,
    )
    rendered: dict[Path, bytes] = {}
    for index, shard in enumerate(shards, start=1):
        if not 1 <= len(shard.names) <= MAX_EFFECTS_PER_SHARD:
            raise ValueError(f"mechanism shard {index} violates the 1-10 effect boundary")
        part = f"_part_{shard.part:02d}" if shard.part > 1 else ""
        path = EFFECTS_DIR / (
            f"zg361_generated_mechanism_{index:03d}_{shard.purpose}{part}_effects.txt"
        )
        rendered[path] = script_text(
            f"# Purpose shard: {shard.purpose.replace('_', ' ')}.\n"
            f"# Boundary contract: 1-10 top-level effects; this file has {len(shard.names)}.\n\n"
            f"{shard.body}"
        )
    return rendered


def generated_effect_residue(expected: set[Path]) -> tuple[Path, ...]:
    candidates = set(EFFECTS_DIR.glob(EFFECT_SHARD_GLOB))
    if LEGACY_EFFECTS_PATH.exists():
        candidates.add(LEGACY_EFFECTS_PATH)
    return tuple(sorted(candidates - expected))


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
                    f"\t\tcustom_tooltip = zg361m.{mechanism.id}.{choice}.tt",
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


def naturalize_mechanism_chinese(text: str) -> str:
    """Remove implementation jargon and raw grade codes from visible copy."""

    natural = text
    for source, replacement in (
        ("经理人工 Override 预算", "经理人工调整额度"),
        (
            "Override 命中后续好结果会提高信用，翻案则降低下轮额度",
            "人工调整若被后续结果证明合理会提高信用，遭翻案则降低下轮额度",
        ),
        (
            "穷尽私下沟通和正式申诉后，允许附冻结证据的实名长文进入受控复核，并投入调解与事实核查",
            "穷尽私下沟通与正式申诉后，凭冻结证据实名公开并接受调解复核",
        ),
        (
            "激进目标提高 3.75 与“高潜”上限但失败风险更高；保守目标容易完成但不能只靠完成率获得头档",
            "目标强度同时改变高潜上限、失败风险与完成难度；完成率本身不足以换取头档",
        ),
        (
            "玩家真正做“为什么是他，不是别人”的人事决定",
            "边界人选的档位将牵动实际任免",
        ),
        (
            "不再把所有明星都逼成经理；两条路线待遇可相当，但管理权、风险和考核表不同",
            "明星不必一律转任经理；管理线与专家线待遇可以相当，但权责、风险和考核表不同",
        ),
        (
            "玩家必须决定是否容忍能打但破坏协作的人",
            "能打却破坏协作的人正在逼迫组织表态",
        ),
        (
            "重做容易成为宏大晋升项目也可能烂尾，渐进收益小却稳定；现状路线把节省资源换成持续利息",
            "重做可能成为宏大晋升项目，也可能烂尾；渐进改造收益较小但稳定，维持现状则会积累持续利息",
        ),
        (
            "中央全包鼓励采用也掩盖浪费，分摊促节制却诱发绕平台；任何路线都保持总体国库守恒",
            "中央全包鼓励采用也掩盖浪费，分摊促节制却诱发绕平台；无论如何裁定，总体国库都必须守恒",
        ),
        (
            "降门槛缩短空岗却提高试用失败和导师成本，坚持门槛则让现团队继续超负荷；选择写回 HC 判断",
            "降门槛缩短空岗却提高试用失败和导师成本，坚持门槛则让现团队继续超负荷；最终裁定会进入下一轮编制判断",
        ),
        (
            "冒险型人才可能押注组织增长，保守者换确定性；选择不改变原绩效，也不能由经理强迫接“纸面财富”",
            "冒险型人才可能押注组织增长，保守者更看重确定性；个人偏好不改变原绩效，经理也不能强迫其接受“纸面财富”",
        ),
        (
            "换份额缓解当前国库并增加留任，也把未来波动转给个人；选择后只能按既定退出规则处理",
            "换份额缓解当前国库并增加留任，也把未来波动转给个人；裁定一经写入，只能按既定退出规则处理",
        ),
        ("风险和责任 owner", "风险与责任人"),
        ("责任责任人", "责任人"),
        ("编号 发奖", "编号发奖"),
        ("事件窗口读取下一年的 live 值", "让下一年的现值改写旧案"),
        ("玩家真正做", "最终仍由你作出"),
        ("年度目标责任书：OKR 方向 + KPI 结果", "年度目标责任书：目标方向与绩效结果"),
        ("探索型 OKR 与承诺型 KPI 双赛道", "探索目标与承诺绩效双赛道"),
        ("隔级校准 / HR 政委席", "隔级校准与人事监督席"),
        ("业务经理 vs 政委", "业务经理与人事监督席"),
        ("原生治理成果", "实际治理成果"),
        ("唯一责任 ID", "唯一责任编号"),
        ("唯一贡献 ID", "唯一贡献编号"),
        ("项目 ID", "项目编号"),
        ("未来 cohort", "下一批受评人"),
        ("正式 cohort", "正式受评组"),
        ("旧 cohort", "原受评组"),
        ("进 cohort", "进入受评组"),
        (
            "堵住“招一批新人专门背 C”的玩法；招聘质量差会回写招聘经理和导师，而不是给老员工腾出虚假好档。",
            "团队不能靠让一批新人承担末档来保护老员工；招聘失误会追究招聘经理和导师的责任。",
        ),
        ("封建头衔不被脚本非法剥夺", "封建头衔不会因此被违规剥夺"),
        ("招聘质量回写", "招聘质量追责"),
        ("面试判断的延迟回写", "面试判断的延迟校正"),
        ("供下轮回写", "供下轮复核"),
        ("在其后续成就出现时回写原人才判断", "据其后续成就校正原人才判断"),
        ("回写招聘经理和导师", "追记招聘经理和导师的责任"),
        ("回写导师贡献", "归入导师贡献记录"),
        ("回写判断信用", "校正判断信用"),
        ("回写信用", "校正信用"),
        ("回写原经理和制度气候", "追记原经理责任并校正制度评价"),
        ("回写给对应面试官", "追记到对应面试官名下"),
        ("回写培训责任人", "追记培训责任人"),
        ("回写命中率", "据后续结果校正命中率"),
        (
            "另行回写招聘和导师且不占正式 C 档",
            "另行追究招聘与导师责任，且不占正式末档名额",
        ),
        (
            "不能用“外包不行”替代事实，也不能把供应商违约算成甲方一线官员的 C",
            "不能用“外包不行”替代事实，也不能因供应商违约直接把甲方一线官员列入末档",
        ),
        ("“背 C”与护人", "末档归属与护人"),
        ("“离职者背 C”灰色操作", "用离职者填末档的灰色操作"),
        ("招一批新人专门背 C", "让一批新人被列入末档"),
        ("专招新人背 C", "专招新人充当末档"),
        ("弱势者专背 C", "弱势者专门承担末档"),
        ("不占正式 C 档", "不占正式末档名额"),
        ("自动判员工 C", "自动判员工为末档"),
        ("填满 C 档", "填满末档名额"),
        ("把 C 直接压给", "把末档直接压给"),
        ("偶然背 C", "偶然被列入末档"),
        ("替人背 C", "替人承担末档"),
        ("轮流背 C", "轮流承担末档"),
        ("同步背 C", "同步被列入末档"),
        ("硬背 C", "硬压末档"),
        ("背 C 者", "被列入末档者"),
        ("背 C", "被列入末档"),
        ("填 C", "填末档"),
        ("免 C", "免于末档"),
        ("的 C", "的末档"),
        ("（CC）", ""),
        ("AI 经理", "其他主管"),
        ("CK3 合法头衔", "可授予的正式头衔"),
        ("CK3", "现行制度"),
        ("GUI", "案卷"),
        ("live", "当前"),
        ("设计稿", "草案"),
        ("Override", "调整权限"),
        ("Check-in", "面谈"),
        ("cohort", "受评组"),
        ("PPT", "陈述材料"),
        ("HR", "人事部门"),
        (" vs ", "与"),
        (" ID", "编号"),
        ("blocker", "阻塞责任人"),
        ("运行时纵切", "当前处理链"),
        ("结算器", "结算结果"),
        ("本卡", "这份案卷"),
        ("玩家", "你"),
        ("脚本", "制度规则"),
        ("回写", "追记"),
    ):
        natural = natural.replace(source, replacement)
    return natural


def player_facing_mechanism_context_cn(mechanism: Mechanism) -> str:
    """Project one mechanism consequence into natural, in-world event copy."""

    return naturalize_mechanism_chinese(mechanism.consequence_cn)


def concise_choice_cn(choice: str, *, max_length: int) -> str:
    """Keep an executable action and its principal cost on the event button."""

    clean = naturalize_mechanism_chinese(choice).rstrip("。！？；")
    for verbose, concise in (
        (
            "逐项核验连续高绩效、价值观、PIP、任职年限和合法空缺后才允许提包",
            "核验业绩、品行、改进状态、年限与空缺后再提包",
        ),
        (
            "触发冲突即让两位上司联合裁定优先级、责任和证据归属",
            "由两位上司联合裁定冲突的优先级与归属",
        ),
        (
            "为加俸、专业级、代理权和正式空缺分别写清权限、现金与兑现日期",
            "分别写清加俸、专业级、代理权及空缺的权责与兑现日",
        ),
        (
            "放出优秀人才可获得育人分、backfill 优先和跨组信用",
            "放行优秀人才，换取育人分、补岗优先与跨组信用",
        ),
        (
            "等新人完成爬坡后，把成功、错岗或失败按证据追记 HC 提出者、选人者与批准者，承担延迟核算",
            "爬坡后再追究招聘各环节责任，承担延迟核算",
        ),
    ):
        clean = clean.replace(verbose, concise)
    if len(clean) <= max_length:
        return clean

    action = clean.split("，", 1)[0]
    consequence = ""
    for marker in ("，却", "，但", "，承担", "，接受", "并承担", "并接受", "，风险"):
        if marker not in clean:
            continue
        tail = clean.split(marker, 1)[1]
        if marker in ("，却", "，但"):
            consequence = f"但{tail}"
        elif marker in ("，承担", "，接受"):
            consequence = f"承担{tail}"
        elif marker in ("并承担", "并接受"):
            consequence = f"承担{tail}"
        else:
            consequence = f"风险{tail}"
        break
    if not consequence:
        candidate = action if len(action) < len(clean) else clean
        return fit_choice_action_cn(candidate, max_length=max_length)
    summary = f"{action}；{consequence}" if consequence else action
    candidate = summary if len(summary) < len(clean) else clean
    return fit_choice_action_cn(candidate, max_length=max_length)


def fit_choice_action_cn(action: str, *, max_length: int) -> str:
    """Fit one concrete action without moving its choice back into the body."""

    clean = action.rstrip("。！？；，、 ")
    if len(clean) <= max_length:
        return clean
    for delimiter in ("；", "，"):
        clause = clean.split(delimiter, 1)[0].rstrip("。！？；，、 ")
        if 6 <= len(clause) <= max_length:
            return clause
    return clean[: max_length - 1].rstrip("。！？；，、 ") + "…"


def principal_ledger_changes_cn(mechanism: Mechanism, choice: str) -> str:
    """Expose the largest benefit and cost actually written by one choice."""

    deltas = mechanism_deltas(mechanism, choice)

    def is_benefit(item: tuple[str, int]) -> bool:
        ledger, delta = item
        return (ledger in POSITIVE_LEDGERS and delta > 0) or (
            ledger not in POSITIVE_LEDGERS and delta < 0
        )

    ranked = list(deltas.items())
    benefits = [item for item in ranked if is_benefit(item)]
    costs = [item for item in ranked if not is_benefit(item)]

    def largest(items: list[tuple[str, int]]) -> tuple[str, int] | None:
        if not items:
            return None
        return max(items, key=lambda item: abs(item[1]))

    selected = [item for item in (largest(benefits), largest(costs)) if item]
    if len(selected) < 2:
        for item in sorted(ranked, key=lambda item: abs(item[1]), reverse=True):
            if item not in selected:
                selected.append(item)
            if len(selected) == 2:
                break
    return "、".join(
        f"{LEDGER_LABELS_CN[ledger]}{delta:+d}" for ledger, delta in selected
    )


def choice_button_cn(
    mechanism: Mechanism, choice: str, *, ledger_only: bool, max_length: int = 49
) -> str:
    """Render action plus ledger result within 50 glyphs after punctuation."""

    source = mechanism.option_a_cn if choice == "a" else mechanism.option_b_cn
    ledger = principal_ledger_changes_cn(mechanism, choice)
    tail = f"；{'仅记账，' if ledger_only else ''}{ledger}"
    action = concise_choice_cn(source, max_length=max_length - len(tail))
    return f"{action}{tail}"


def concise_choice_en(choice: str) -> str:
    """English counterpart of :func:`concise_choice_cn`."""

    clean = choice.rstrip(".!?; ")
    if len(clean) <= 92:
        return clean
    action = clean.split(",", 1)[0]
    consequence = ""
    lowered = clean.lower()
    for marker in (
        ", while ",
        ", but ",
        ", accepting ",
        ", risking ",
        ", marking ",
        ", and fund ",
    ):
        index = lowered.find(marker)
        if index < 0:
            continue
        tail = clean[index + len(marker) :]
        if marker == ", while ":
            consequence = f"while {tail}"
        elif marker == ", but ":
            consequence = f"but {tail}"
        elif marker == ", accepting ":
            consequence = f"accepting {tail}"
        elif marker == ", marking ":
            consequence = f"marking {tail}"
        elif marker == ", and fund ":
            consequence = f"fund {tail}"
        else:
            consequence = f"risking {tail}"
        break
    if not consequence:
        return clean
    summary = f"{action}; {consequence}" if consequence else action
    return summary if len(summary) < len(clean) else clean


def complete_sentence_cn(text: str) -> str:
    clean = naturalize_mechanism_chinese(text).rstrip()
    return clean if clean.endswith(("。", "！", "？", "；")) else clean + "。"


def complete_sentence_en(text: str) -> str:
    clean = text.rstrip()
    return clean if clean.endswith((".", "!", "?", ";")) else clean + "."


def localization_values(
    mechanisms: list[Mechanism], language: str
) -> dict[str, str]:
    is_chinese = language == "simp_chinese"
    is_english = language == "english"
    # Release translation replaces these structurally valid English placeholders
    # in the other seven languages.
    common = {
        "zg361_next_mechanism_decision": "召开下一项制度评审" if is_chinese else "Review the Next Performance Policy",
        "zg361_next_mechanism_decision_desc": "考功司仍有制度悬而未决。召开评审会后，裁定会立即记入组织账簿；只有已经立案的具体事项，才会据此办理款项、人事或职位变动。" if is_chinese else "The policy office still has unresolved matters. A ruling enters the organizational ledger immediately; payments, personnel actions, or position changes occur only when a concrete case already exists.",
        "zg361_next_mechanism_decision_tooltip": "从未定案制度中打开下一项评审。" if is_chinese else "Open the next unresolved policy for review.",
        "zg361_next_mechanism_decision_confirm": "打开下一项制度评审" if is_chinese else "Open the next policy review",
        "zg361_reference_charter_decision": "颁行《三六一考功章程》" if is_chinese else "Enact the Reference 361 Charter",
        "zg361_reference_charter_decision_desc": "考功司已汇编一套包含 361 项制度的参考章程。颁行后，各项推荐裁定与相应制度债会立即记入组织账簿；没有具体案卷时，不会据此发放款项，也不会办理任命、招募、调岗或退款。" if is_chinese else "The policy office has compiled a reference charter covering all 361 matters. Enacting it records every recommended ruling and related policy debt immediately; without a concrete case, it issues no payment, appointment, hire, transfer, or refund.",
        "zg361_reference_charter_decision_tooltip": "将 361 项推荐裁定一并记入组织账簿；具体事项仍须另有案卷。" if is_chinese else "Record all 361 recommended rulings in the organizational ledger; concrete actions still require a separate case.",
        "zg361_reference_charter_decision_confirm": "采用全部 361 项推荐默认值，立即写入组织账本" if is_chinese else "Adopt all 361 recommended defaults and write them to the organizational ledger",
        "zg361_mechanism_choice_a_tt": "审慎办理会改善证据、信任或组织能力，但也会消耗行政、财政或短期交付能力。" if is_chinese else "Careful handling improves evidence, trust, or capability while consuming administrative, fiscal, or short-term delivery capacity.",
        "zg361_mechanism_choice_b_tt": "从速办理能换取眼前结果，却会把风险、倦怠、技术债或申诉债留给以后。" if is_chinese else "Expedited handling improves the immediate result while carrying risk, burnout, technical debt, or appeal debt into later reviews.",
        "zg361_mechanism_choice_c_tt": "本局搁置：本项不会自动再次提案；立即登记制度债，并进入你自己的上司考核。" if is_chinese else "Shelve for this campaign: this item will not be proposed again automatically; policy debt is recorded immediately and feeds your superior's review.",
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
        ledger_only = mechanism.id in LEDGER_ONLY_MECHANISM_IDS
        if is_chinese:
            title_cn = naturalize_mechanism_chinese(mechanism.title_cn)
            title = f"#{mechanism.id:03d} · {title_cn}"
            desc = player_facing_mechanism_context_cn(mechanism)
            if ledger_only:
                desc += "\\n\\n这项裁定只记入组织账簿；没有具体案卷时，不会据此发放款项，也不会办理任命、招募、调岗或退款。"
                option_a = choice_button_cn(mechanism, "a", ledger_only=True)
                option_b = choice_button_cn(mechanism, "b", ledger_only=True)
                tooltip_a = f"{complete_sentence_cn(mechanism.option_a_cn)}这项裁定只记入组织账簿；没有具体案卷时，不会据此办理款项、人事或职位变动。"
                tooltip_b = f"{complete_sentence_cn(mechanism.option_b_cn)}这项裁定只记入组织账簿；没有具体案卷时，不会据此办理款项、人事或职位变动。"
            else:
                option_a = choice_button_cn(mechanism, "a", ledger_only=False)
                option_b = choice_button_cn(mechanism, "b", ledger_only=False)
                tooltip_a = complete_sentence_cn(mechanism.option_a_cn)
                tooltip_b = complete_sentence_cn(mechanism.option_b_cn)
            option_c = "搁置本局提案；制度债+3、行政负担-1"
            tooltip_c = "关闭本局内的这项提案；它不会自动再次出现，组织账本的制度债增加 3，行政负担减少 1。"
        else:
            title = f"#{mechanism.id:03d} · {mechanism.title_en}"
            desc = (
                "This dispute will shape later reviews and change the organization's trust, workload, risk, "
                "talent, or fiscal pressure."
            )
            if ledger_only:
                desc += " This ruling updates only the organizational ledger; without a connected case, it will not issue payments, appointments, hires, transfers, or refunds."
                option_a = f"{concise_choice_en(mechanism.option_a_en)} (ledger only)"
                option_b = f"{concise_choice_en(mechanism.option_b_en)} (ledger only)"
                tooltip_a = f"{complete_sentence_en(mechanism.option_a_en)} This item updates only the organizational ledger and does not execute a concrete business action."
                tooltip_b = f"{complete_sentence_en(mechanism.option_b_en)} This item updates only the organizational ledger and does not execute a concrete business action."
            else:
                option_a = concise_choice_en(mechanism.option_a_en)
                option_b = concise_choice_en(mechanism.option_b_en)
                tooltip_a = complete_sentence_en(mechanism.option_a_en)
                tooltip_b = complete_sentence_en(mechanism.option_b_en)
            option_c = "Close this policy for the campaign and record one policy debt"
            tooltip_c = "Close this proposal for the current campaign. It will not return automatically, and one policy debt is recorded."
        values.update(
            {
                f"zg361m.{mechanism.id}.t": title,
                f"zg361m.{mechanism.id}.desc": desc,
                f"zg361m.{mechanism.id}.a": option_a,
                f"zg361m.{mechanism.id}.b": option_b,
                f"zg361m.{mechanism.id}.c": option_c,
                f"zg361m.{mechanism.id}.a.tt": tooltip_a,
                f"zg361m.{mechanism.id}.b.tt": tooltip_b,
                f"zg361m.{mechanism.id}.c.tt": tooltip_c,
            }
        )
    if is_chinese:
        normalized = {
            key: normalize_player_chinese(value) for key, value in values.items()
        }
        for key, value in tuple(normalized.items()):
            if key.startswith("zg361m.") and key.endswith((".a", ".b")):
                if not value.endswith(("。", "！", "？", "；", ".", "!", "?")):
                    normalized[key] = value + "。"
        return normalized
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
        # Daily Chinese/English development deliberately leaves the other seven
        # languages as English placeholders.  The release-localization workflow
        # refreshes and validates this digest before those translations ship.
        return None
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
    for key, value in values.items():
        # A leading ASCII # starts CK3 localization formatting and swallowed
        # the visible mechanism number. Keep translation source hashes stable,
        # but render a language-appropriate literal prefix into the game yml.
        if key.startswith("zg361m.") and key.endswith(".t"):
            event_id = key.removeprefix("zg361m.").removesuffix(".t")
            raw_prefix = f"#{int(event_id):03d}"
            if value.startswith(raw_prefix):
                safe_prefix = (
                    f"第{int(event_id):03d}号"
                    if language == "simp_chinese"
                    else f"No.{int(event_id):03d}"
                )
                value = safe_prefix + value[len(raw_prefix) :]
        lines.append(loc_line(key, value))
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


def implementation_status(mechanism_id: int) -> dict[str, str]:
    """Project the ordered readiness ledger into the legacy status fields."""

    record = READINESS_BY_ID[mechanism_id]
    runtime_evidence = {
        ReadinessLevel.DESIGN_ONLY: "none",
        ReadinessLevel.PYTHON_L0: "python-l0",
        ReadinessLevel.CK3_STATIC_READY: "static-ready",
        ReadinessLevel.CENTRAL_WIRED: "static-ready",
        ReadinessLevel.CK3_LIVE: "fixture-live",
    }[record.level]
    return {
        "catalogue": "complete",
        "policy_configuration": "fixture-live",
        "ledger_projection": "fixture-live",
        "domain_runtime": (
            "partial"
            if record.level >= ReadinessLevel.CK3_STATIC_READY
            else "not-implemented"
        ),
        "player_visible_loop": "partial",
        "runtime_evidence": runtime_evidence,
    }


def runtime_contract(mechanism_id: int) -> dict[str, object] | None:
    """Serialize only the four source-backed first-slice contracts."""
    spec = PHASE2_RUNTIME_SPECS.get(f"{mechanism_id:03d}")
    if spec is None:
        return None
    return {
        "object_type": spec.object_type,
        "owner_binding": spec.owner_binding,
        "subject_binding": spec.subject_binding,
        "cycle_binding": spec.cycle_binding,
        "case_binding": spec.case_binding,
        "hook": spec.hook,
        "states": list(spec.states),
        "feedback": list(spec.feedback),
        "permissions": {
            "player_manager": spec.permissions.player_manager,
            "ai_manager": spec.permissions.ai_manager,
            "subject": spec.permissions.subject,
            "count_baron": spec.permissions.count_baron,
        },
    }


def manifest_payload(
    mechanisms: list[Mechanism],
    runtime_plans: list[dict[str, object]],
) -> dict[str, object]:
    plans_by_id = {int(plan["id"]): plan for plan in runtime_plans}
    items = []
    for mechanism in mechanisms:
        plan = plans_by_id[mechanism.id]
        planned_currencies = sorted(
            {
                str(transaction["currency"])
                for choice in plan["choices"].values()
                for transaction in choice["transactions"]
            }
        )
        item = {
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
            "acceptance_contract": mechanism.acceptance_contract.manifest_payload(),
            "runtime_plan": {
                "status": "contract-complete",
                "source": (
                    "tools/mechanism_runtime/runtime_001_120.json"
                    if mechanism.id <= 120
                    else "tools/mechanism_runtime/runtime_121_240.json"
                    if mechanism.id <= 240
                    else "tools/mechanism_runtime/runtime_241_361.json"
                ),
                "domain": plan["domain"],
                "object_type": plan["object_type"],
                "operation_key": plan["operation_key"],
                "primitive_recipe": plan["primitive_recipe"],
                "semantic_family": plan["semantic_family"],
                "trigger_hook": plan["trigger_hook"],
                "transition_owner": plan["transition_owner"],
                "planned_currencies": planned_currencies,
                "choice_transitions": {
                    choice_name: {
                        "from": choice["allowed_from_states"],
                        "to": choice["to_state"],
                        "deadline_kind": choice["deadline"]["kind"],
                    }
                    for choice_name, choice in plan["choices"].items()
                },
                "claim_boundary": (
                    "The typed runtime contract is complete; it is not a claim that "
                    "the CK3 domain effect, event, GUI surface, or live acceptance exists."
                ),
            },
            "status": implementation_status(mechanism.id),
            "readiness": READINESS_BY_ID[mechanism.id].manifest_payload(),
        }
        contract = runtime_contract(mechanism.id)
        if contract is not None:
            item["runtime_contract"] = contract
        items.append(item)
    return {
        "schema": 5,
        "mechanism_count": MECHANISM_COUNT,
        "source": "docs/361-expansion-options.md",
        "acceptance_contract_source": "tools/mechanism_acceptance/acceptance_*.json",
        "status_boundary": {
            "catalogue": "The numbered design and reviewed choice copy are complete.",
            "policy_configuration": "Every reference choice ran in the frozen CK3 fixture.",
            "ledger_projection": "Choice variables, aggregate ledgers, checksum, and idempotence ran in the frozen CK3 fixture.",
            "runtime_plan": "All 361 mechanisms have a validated domain/hook/typed-operation/deadline/transaction/feedback/acceptance contract; this is design coverage, not CK3 implementation readiness.",
            "domain_runtime": f"{CUMULATIVE_COUNTS[ReadinessLevel.CK3_STATIC_READY.key]} mechanisms have at least a committed partial CK3 product projection; {MECHANISM_COUNT - CUMULATIVE_COUNTS[ReadinessLevel.CK3_STATIC_READY.key]} still have no CK3 domain runtime. Partial does not mean complete.",
            "player_visible_loop": "Generic policy cards and ledger climate feedback remain partial; static or central wiring does not by itself complete the per-ID player loop.",
            "runtime_evidence": f"The ordered tools/zg361_readiness_data.py ledger is authoritative: {CUMULATIVE_COUNTS[ReadinessLevel.PYTHON_L0.key]} Python L0, {CUMULATIVE_COUNTS[ReadinessLevel.CK3_STATIC_READY.key]} CK3 static, {CUMULATIVE_COUNTS[ReadinessLevel.CENTRAL_WIRED.key]} central-hook reachable, and {CUMULATIVE_COUNTS[ReadinessLevel.CK3_LIVE.key]} bounded fixture-live.",
        },
        "acceptance": {
            "scope": "legacy reference-choice configuration and aggregate-ledger fixture only",
            "logical_group_semantics": "live_wave is a coverage grouping inside that single CK3 run, not a separate game launch",
            "report": "docs/testing-report-2026-08-29.md",
            "run_id": "zga_20260829_061314_ea5f04ad",
            "report_sha256": "DCCF8B87D990BA3ED3074FAE3391E5004E6CD8B07A5C80750BC344E7F9024C25",
            "claim_boundary": "fixture-live applies only to policy_configuration and ledger_projection; it does not prove the 361 domain runtimes, player-visible semantic loops, or all 1083 A/B/C branches",
        },
        "readiness": {
            "schema": 1,
            "authority": "tools/zg361_readiness_data.py",
            "mechanism_count": READINESS_MECHANISM_COUNT,
            "ordered_levels": [level.key for level in LEVELS],
            "exclusive_counts": dict(EXCLUSIVE_COUNTS),
            "cumulative_counts": dict(CUMULATIVE_COUNTS),
            "exclusive_ranges": dict(EXPECTED_EXCLUSIVE_RANGES),
            "cumulative_ranges": dict(EXPECTED_CUMULATIVE_RANGES),
            "central_wiring_boundary": CENTRAL_WIRING_BOUNDARY,
            "live_boundary": LIVE_BOUNDARY,
            "legacy_fixture_boundary": "The 361 generic policy cards and aggregate ledger fixture do not promote domain readiness.",
            "partial_live_notes": {
                "018": "receipt/refund is fixture-live; reopening zg361.53 remains static-ready",
            },
        },
        "phase2_static": {
            "mechanism_ids": list(ids_at_least(ReadinessLevel.CK3_STATIC_READY)),
            "count": CUMULATIVE_COUNTS[ReadinessLevel.CK3_STATIC_READY.key],
            "evidence": "at-least-ck3-static-ready",
            "source": "tools/zg361_readiness_data.py",
            "tests": "tools/test_zg361_readiness_data.py",
            "claim_boundary": "CK3 static and central wiring do not prove complete semantics or live behavior; only four explicitly bounded slices have fixture evidence.",
        },
        "runtime_plan": {
            "schema": RUNTIME_PLAN_SCHEMA,
            "coverage": 361,
            "domain_count": len(DOMAIN_SPECS),
            "domain_source": "tools/mechanism_domains/domains.json",
            "mechanism_sources": [
                "tools/mechanism_runtime/runtime_001_120.json",
                "tools/mechanism_runtime/runtime_121_240.json",
                "tools/mechanism_runtime/runtime_241_361.json",
            ],
            "authority": "tools/zg361_domain_data.py + tools/zg361_operation_registry.py + numbered acceptance contracts",
            "claim_boundary": "runtime-contract-complete does not change domain_runtime or player-visible-loop readiness",
        },
        "generated_files": [],
        "items": items,
    }


def render_runtime_plan_files(
    mechanisms: list[Mechanism],
    runtime_plans: list[dict[str, object]],
) -> dict[Path, bytes]:
    domain_payload = {
        "schema": RUNTIME_PLAN_SCHEMA,
        "generated": True,
        "authority": "tools/zg361_domain_data.py + tools/zg361_operation_registry.py",
        "domain_count": len(DOMAIN_SPECS),
        "mechanism_count": len(mechanisms),
        "claim_boundary": (
            "Validated design contract only; domain_runtime readiness remains governed "
            "by product script and CK3 evidence."
        ),
        "domains": [domain.manifest_payload() for domain in DOMAIN_SPECS],
    }
    rendered: dict[Path, bytes] = {
        MOD_ROOT / "tools" / "mechanism_domains" / "domains.json": (
            json.dumps(domain_payload, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
    }
    for first_id, last_id in ((1, 120), (121, 240), (241, 361)):
        rows = [
            plan
            for plan in runtime_plans
            if first_id <= int(plan["id"]) <= last_id
        ]
        payload = {
            "schema": RUNTIME_PLAN_SCHEMA,
            "generated": True,
            "authority": (
                "tools/zg361_domain_data.py + tools/zg361_operation_registry.py + tools/mechanism_acceptance/acceptance_*.json"
            ),
            "id_range": [first_id, last_id],
            "count": len(rows),
            "claim_boundary": (
                "runtime-contract-complete only; CK3 runtime status is recorded separately "
                "in docs/361-mechanism-manifest.json"
            ),
            "items": rows,
        }
        rendered[
            MOD_ROOT
            / "tools"
            / "mechanism_runtime"
            / f"runtime_{first_id:03d}_{last_id:03d}.json"
        ] = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return rendered


def render_manifest_md(mechanisms: list[Mechanism], payload: dict[str, object]) -> bytes:
    lines = [
        "# 361 机制实现映射",
        "",
        "> GENERATED FILE — edit the numbered design document, reviewed choice JSON, acceptance-contract JSON, domain data, or `tools/zg361_readiness_data.py`.",
        "",
        "状态口径：361 项目录文案为 `complete`；参考政策配置和共享账本投影为 `fixture-live`；",
        "361/361 已有 `contract-complete` 的领域/状态/操作/期限/事务/反馈设计合同；这不等于游戏实现。",
        f"当前累计门为 Python L0 `{CUMULATIVE_COUNTS[ReadinessLevel.PYTHON_L0.key]}/{MECHANISM_COUNT}`、CK3 static `{CUMULATIVE_COUNTS[ReadinessLevel.CK3_STATIC_READY.key]}/{MECHANISM_COUNT}`、central-wired `{CUMULATIVE_COUNTS[ReadinessLevel.CENTRAL_WIRED.key]}/{MECHANISM_COUNT}`、bounded fixture-live `{CUMULATIVE_COUNTS[ReadinessLevel.CK3_LIVE.key]}/{MECHANISM_COUNT}`。",
        "`central-wired` 只表示中央产品 hook 可达，不表示逐号语义完整；#018 只有 receipt/refund 为 fixture-live，`.53` 重开仍为 static-ready。",
        "旧 361 政策卡与共享账本 fixture 只证明配置投影，不得提升领域运行时。完整分层见 `361-phase2-coverage-ledger.md`。",
        "",
        "| ID | 机制 | 组 | P | Profile | 玩家入口 | AI 入口 | 同批逻辑组 | 目录 | 配置 | 账本 | 运行设计 | 领域 | 玩家闭环 | 最高证据 |",
        "|---:|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|",
    ]
    for mechanism in mechanisms:
        status = implementation_status(mechanism.id)
        readiness = READINESS_BY_ID[mechanism.id]
        lines.append(
            f"| {mechanism.id:03d} | {mechanism.title_cn} | {mechanism.group_code} | "
            f"{mechanism.priority} | `{mechanism.profile}` | `zg361m.{mechanism.id}` | "
            f"`zg361_mechanism_{mechanism.id:03d}_ai_effect` | {wave_for(mechanism.id)} | "
            f"complete | fixture-live | fixture-live | contract-complete | {status['domain_runtime']} | "
            f"{status['player_visible_loop']} | `{readiness.level.key}` |"
        )
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    lines.extend(["", f"Manifest semantic SHA-256: `{digest}`", ""])
    return ("\n".join(lines)).encode("utf-8")


def render_readiness_ledger(mechanisms: list[Mechanism]) -> bytes:
    """Render the human-readable projection of the unique readiness source."""

    mechanism_by_id = {mechanism.id: mechanism for mechanism in mechanisms}
    all_ids = set(range(1, MECHANISM_COUNT + 1))
    snapshot = LATEST_PRODUCT_ACCEPTANCE
    drained_events = ", ".join(f"`{key}`" for key in snapshot.drained_event_keys)
    cleared_signatures = "、".join(
        f"`{signature}`" for signature in snapshot.cleared_product_signatures
    )
    snapshot_evidence = "<br>".join(f"`{path}`" for path in snapshot.evidence)
    lines = [
        "# 361 二期实现覆盖账本",
        "",
        "> GENERATED FILE — edit only `tools/zg361_readiness_data.py`, then run `py tools/gen_361_mechanisms.py`.",
        "",
        "本账本记录每个编号当前达到的最高证据层。五层严格有序且互斥；累计门表示达到该层或更高层的编号数。",
        "旧 361 张政策卡与共享组织账的 fixture-live 不属于领域运行时证据，不进入下列升级计数。",
        "",
        f"- `{CENTRAL_WIRING_BOUNDARY}`。",
        f"- `{LIVE_BOUNDARY}`。",
        "- #018 只有 receipt/refund 达到 fixture-live；关闭后重开 `zg361.53` 仍为 static-ready。",
        "",
        "## R111–R118 增量全量候选验收记录（不改变逐号等级）",
        "",
        "八轮均使用独立冻结的 release-identical 产品树、原生 MCP-only 驱动和串行 CK3 启动门禁；`ocr_used=false`、",
        "`image_used=false`、`coordinates_used=false`。验收时间轴默认使用 `set-speed-5` 快进，仅在有界事件捕获窗口按 runner",
        "合同降速。各轮 loader 均完成 303/303 database nodes，项目归属 loader match 为 0；这只证明加载门 GREEN，不能覆盖随后",
        "发生的产品运行时 RED，也不能声称全量验收 GREEN。",
        "",
        "| 轮次 | 精确产品身份 | loader / 运行结果 | 已修与下一轮边界 |",
        "|---|---|---|---|",
    ]
    for attempt in RECENT_PRODUCT_ACCEPTANCE_ATTEMPTS:
        lines.append(
            f"| `{attempt.run_id}` · `{attempt.observed_at}` | commit `{attempt.product_commit}` · "
            f"projection `{attempt.projection}` · {attempt.verified_file_count} files · source tree "
            f"`{attempt.product_tree_sha256}` · manifest file SHA-256 "
            f"`{attempt.release_manifest_sha256}` | {attempt.loader_and_result} | "
            f"{attempt.closure_boundary} |"
        )
    lines.extend(
        [
        "",
        "可核验证据：`Z:\\\\b3r111`–`Z:\\\\b3r116` 的 `evidence-index.json`、`report.json`、",
        "`cell/02_loader_error_scan.json`、`cell/03_loader_gate.json`、`cell/final_error.log`；以及 `Z:\\\\p2r111`–`Z:\\\\p2r116`",
        "的 `phase2-product-projection.json` 与 `p.manifest.json`。",
        "R116 续跑证据：`Z:\\\\b3r116_resume1\\report.json`、`03_promotion_source_production_entry.json`，以及",
        "`Z:\\\\b3r116_native_state\\profile\\logs\\error.log` / `debug.log` 的 11:46–11:47 运行时增量。",
        "R117 证据：`Z:\\\\b3r117\\evidence-index.json`、`report.json`、`cell/02_loader_error_scan.json`、",
        "`cell/03_loader_gate.json`、`cell/03_promotion_source_production_entry.json`；同 PID 续跑见",
        "`Z:\\\\b3r117_resume1\\report.json` 及 `03_promotion_source_production_entry.json`；冻结产品身份见",
        "`Z:\\\\p2r117\\phase2-product-projection.json` 与 `Z:\\\\p2r117\\p.manifest.json`。",
        "R118 证据：`Z:\\\\b3r118\\evidence-index.json`、`report.json`、`cell/02_loader_error_scan.json`、",
        "`cell/03_loader_gate.json`、`cell/03_promotion_source_production_entry.json`；续跑见",
        "`Z:\\\\b3r118_resume1\\report.json`、`Z:\\\\b3r118_resume2\\report.json` 及各自的",
        "`03_promotion_source_production_entry.json`；冻结产品身份见 `Z:\\\\p2r118\\phase2-product-projection.json` 与",
        "`Z:\\\\p2r118\\p.manifest.json`。",
        "",
        "## R120 专用管理者 seed 的 harness RED（不改变逐号等级）",
        "",
        "- `2026-09-06 14:41–14:45 Asia/Shanghai` 对冻结 commit",
        "  `12405873745ea7df5cd399f4d25a4f91d4da2273` 执行专用 player-manager seed 捕获。预检",
        "  `Z:\\\\p2m120_a\\preflight.json` 为 GREEN；冻结源 ZIP SHA-256 为",
        "  `77b9d5a8a076a9e4fe2b88c0fe9467efab9c4cd1b421a235ee3fe5ce88cb91a3`，源码树为",
        "  `213e3db0dd69cfb504fd599c7bf7df91d5656b567f61c153c48f0dec47c4a283`。",
        "- live 完成 loader 303/303、fatal=0、项目 loader blocking diagnostics=0，原生 paused",
        "  application-main/readiness 为 GREEN。随后看到存档中已经排队的 `zg361b2.40`；其 event key、instance、",
        "  date、root、manager/subject saved scopes、三个 authored options 等身份检查全部为 true，只有",
        "  `source_save_sha256` 为 false。runner 中该事件合同仍绑定旧 source SHA-256",
        "  `233e70536d736c32efb9bbd20ef4bab9e0be8f96ee13524707b9ee31e319dc9c`，本轮 exact source 实际为",
        "  `8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9`，因此在发送事件选择前 fail-closed。",
        "  结论是已知前置事件的 **harness identity-contract RED / seed 未评估**，不是产品 RED，也没有到达",
        "  `zga_phase2_manager_seed.10/.11/.1` 或生成候选 seed；本轮不构成完整迁移树 GREEN。",
        "- production projection 为 `phase2-full-release-r120-1240587`，1,031 files / 31,183,422 bytes，产品树",
        "  `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1`，projection manifest SHA-256",
        "  `b80bb8ebda083abe70acbeb17ae0faf2d269b089adfd78beb1b430a23bf2d55c`。关键 B2 产品字节等价检查 GREEN；",
        "  runtime product/fixture 结束后仍分别为 `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1` /",
        "  `07228b54b3a3da71d648301e494068a3852d5c9f1ed3f64de9699eebd9b18428`，外部依赖未变，源码 before/after",
        "  manifest 文件 SHA-256 均为 `8b8b169b75e39bd672698b5cab7fc4e23924057782d3355511fdbf03815245f2`。",
        "- managed cleanup GREEN：Frontend warmup PID `43576` 与 final PID `85688` 均已回收，final CK3 inventory",
        "  为空。主要证据 SHA-256：`runner-report.json`",
        "  `deb968923ca92a9546ccafd5a11606d300bceedcf7f1270e41e7636a7bf3af55`、native readiness",
        "  `32d37408d783c73826a86b7f99d565a3f530f90fec0c8b07db8845c9db5e9aef`、event identity",
        "  `aae555d9b9e14c2c218e400c9a93670ae9381d63861649cb7f59fe6cb12ea52f`、cleanup",
        "  `d362ce8ce064b4b3fa9675d701edd958570f93db4ccc1b462786cedcfe00b648`、relay",
        "  `0fcd537f849c64fbcbadbd7f9342c1f6a78c66eacf4719dc745807a64a30873a`。",
        "",
        "## R121 专用管理者 seed 的前置原版事件 RED（不改变逐号等级）",
        "",
        "- `2026-09-06 14:54–14:58 Asia/Shanghai` 对冻结 commit",
        "  `cf6063ba7f8b90e286262da96ca03735d0b2541f` 执行第二次专用 player-manager seed 捕获；预检",
        "  `Z:\\\\p2m121_pre_a\\\\preflight.json` 为 GREEN，且未启动 CK3。冻结源 ZIP SHA-256 为",
        "  `dc15d01b79d5c9eb586ef8dfdddbdcfd5b170d961f9143256e9052028efe2493`，源码树为",
        "  `7edb7d88a83df637d7ee7b2051e68dd11f7ed8f7a65dac4ed7c9a68654871f72`。",
        "- live 完成 loader 303/303、fatal=0、项目 loader blocking diagnostics=0，并达到 paused",
        "  application-main/native readiness GREEN。runner 对已知 `zg361b2.40` 完成 exact drain：source save SHA、",
        "  event key/instance/date、root、manager/subject saved scopes、三个 authored options 与选择前状态检查均吻合。",
        "  随后出现原版 `ep3_interactions_events.0630`；该事件不在 seed runner 的已知前置事件合同内，因此 runner 按",
        "  unknown prerequisite event fail-closed。`zga_phase2_manager_seed.10/.11/.1`、manager handoff、最终 seed",
        "  和候选合同均未到达。结论是 **scenario/harness RED，不是产品 RED**，也不是完整迁移树 GREEN。",
        "- production projection 为 `phase2-full-release-r121-cf6063b`，1,031 files / 31,183,422 bytes，产品树",
        "  `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1`，projection manifest SHA-256",
        "  `15edd426cb213e74b6d8eb41fb03c4e5b0e28e9996d8471ca3cae97f16c3e642`，release manifest / ZIP SHA-256",
        "  分别为 `1aec6b6a7c7ce8af42085d7fc0866e04ed255b9b3dca002d70fc5c8581077b33` /",
        "  `12ebe06039167f1ac968916de56a4100a0281e933df112a7e2e1e2f60d8735b6`。关键 B2 产品字节等价检查 GREEN；",
        "  runtime product/fixture 结束后仍分别为 `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1` /",
        "  `07228b54b3a3da71d648301e494068a3852d5c9f1ed3f64de9699eebd9b18428`，外部依赖未变，源码 before/after",
        "  manifest 文件 SHA-256 均为 `ed1611e885761f7f563c72fa37ef77a8fa6f34411c211127d5b6ae4d188212b1`。",
        "- managed cleanup GREEN，restart_count=0：Frontend warmup PID `182292` 与 final PID `135672` 均已回收，",
        "  final CK3 inventory 为空。主要证据 SHA-256：preflight",
        "  `f319a2d180ed9c8b2e04b7fce3d15b7d427d33d4efd040e656d89254062f41e4`、runner report",
        "  `8ca41f5e86b06ad6ccf2bee0203c7845e4bc8f6c19ebfa623d9be29a0ed6d64a`、native readiness",
        "  `08002b1b296b0804c0a635b6e8b49211e666b41dea6955e23f058f4bbcc81f05`、loader scan",
        "  `dcc08459de97e74be3cd0ecf28dc3f656ddcdd472e5073a0912e2232c1ef04b7`、exact `zg361b2.40` drain",
        "  `cf2bac10ffbe2f764d4813c139b8ea41d3064146c3b52b11a7e9f52a9f6e53b7`、cleanup",
        "  `5d91ec292e216edec6ac0b0985ae1f2af979a648f1235e8b2e9514bc15158ca2`、relay",
        "  `fed8d98503928cabbfc9079d1a019aa8ad7c1a6c911194012a7af36301bc709e`。",
        "",
        "## R122 专用管理者 seed 的不可变日期 RED（不改变逐号等级）",
        "",
        "- `2026-09-06 15:19–15:23 Asia/Shanghai` 对冻结 commit",
        "  `30ad33788f949729f5412688b39603ccdf5c2bfa` 执行 preemptive player-manager seed 捕获。预检",
        "  `Z:\\\\p2m122_pre_a\\\\preflight.json` 为 GREEN 且未启动 CK3；冻结源 ZIP SHA-256 为",
        "  `08fdb70659a3a7718866252b525ee5d78201eda0c2ebcc014faf07659bca28f7`，源码树为",
        "  `3893e981ed607d8104487da0744865651ff9bded29a7d93bf00519e373344f96`。",
        "- live 完成 loader 303/303、fatal=0、项目 loader diagnostics=0，并达到 paused application-main/native",
        "  readiness GREEN。不可变源日期 `53147016` 的重复 paused snapshot（包括前两次检查）均无 active event，",
        "  CK3 debug/error log 中也没有 `ZGAP2MANAGERSEED` 标记；因此 preemptive handoff 没有在源日期执行。runner 随后按",
        "  合同以 5 速 resume，至 `53147040` 才看到首个稍后事件 `zg361b2.40`。required-date 门立即 fail-closed，",
        "  `known_visible_event_drain_allowed=false`；全程零事件选择、零 drain，manager handoff/final seed 未到达，",
        "  candidate absent。结论是 **scenario/harness RED，不是产品 RED**，也不提升逐号 readiness。",
        "- production projection 为 `phase2-full-release-r122-30ad337`，1,031 files / 31,183,422 bytes，产品树",
        "  `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1`，projection manifest SHA-256",
        "  `ef8f00e27f0a8c2998a77030b4a8af36bfeb4846cf7b4903dd535b9c66364814`，release manifest / ZIP SHA-256",
        "  分别为 `c2fb8f13fcf9ae296b4fbd3228e5358a6282307c26f4261f47b9cfa07b190c06` /",
        "  `12ebe06039167f1ac968916de56a4100a0281e933df112a7e2e1e2f60d8735b6`。关键 B2 产品字节等价检查 GREEN；",
        "  runtime product/fixture 结束后仍分别为 `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1` /",
        "  `72accc5a975482790932714481cf3879604abdf83031ab3214b92eeff03f33d2`，外部依赖未变，源码 before/after",
        "  manifest 文件 SHA-256 均为 `54e1dcb2e42b4a0ee8c329a8260615058125ad1d0a4279100a63083893d71474`。",
        "- managed cleanup GREEN，restart_count=0：Frontend warmup PID `101784` 与 final PID `177256` 均已回收，",
        "  final CK3 inventory 为空。主要证据 SHA-256：preflight",
        "  `5a97b9a9b50058ccf1aa0a3f2ec1acf1d96b6ab42d52f116ac3154a4360bd728`、runner report",
        "  `720f9dc6b6a45e2a2ebfbb62046cb812812e8886a18dc89a2f856f5b7605eb60`、native readiness",
        "  `61c6134802e2f04f8b4253ab3a1a91bb6adc2aec05c344a2e5a78dbeb015679c`、loader scan",
        "  `7d136c5f75b6e7c17ded971cd1bb07c7218c3ef3ffaad8e9dda8d56ba0fcd931`、preemptive contract",
        "  `e837b96ea421f48cb181b4765c7c0a81f41b6c4c3c6fcf442bf8e186586df8b0`、bootstrap wait",
        "  `be504ddb5b688bb073b2b737ffaac7d5b34668df14849ac8eefbbc3a5e327c1f`、cleanup",
        "  `2aa007f5d12d15d22535ff38000b3c04b942b903c030b3c39cba2cf3b8eececb`、relay",
        "  `ad58c138c07dc45fabbba899498e03d32b2705c7e64ae885251b3f03336ded9f`。",
        "",
        "## R123 专用管理者 seed 的 PIP 拒绝路线 RED（不改变逐号等级）",
        "",
        "- `2026-09-06 15:43–15:47 Asia/Shanghai` 对冻结 commit",
        "  `550d9ef1f12ee1fae8113b6a9d867ba5c7a3a147` 执行 exact-PIP-refusal player-manager seed 捕获。首次无启动预检",
        "  `Z:\\\\p2m123_pre_a\\\\preflight.json` 因 pipe name 不符合唯一格式而 harness RED，未跨越 CK3 启动边界；修正后第二次预检",
        "  `Z:\\\\p2m123_pre2_a\\\\preflight.json` 为 GREEN，同样未启动 CK3。冻结源 ZIP/源码树 SHA-256 为",
        "  `228513b2b10567c86fd288773d3b0ef49516f091cd28a3017eab43eb716b6508` /",
        "  `abc320466dd660106b6261300df64ec17ae467d60d328225600be557de2de4dc`。",
        "- live 完成 loader 303/303、fatal=0、项目 loader blocking diagnostics=0，并达到 paused",
        "  application-main/native readiness GREEN。玩法事件识别与 option 选择仅使用 MCP/native；顶层 OCR/image",
        "  只用于非玩法的 legal-consent gate，coordinates=false。runner 以 5 速到达精确日期 `53147040`，",
        "  对 `zg361b2.40` 的 source/event/root/manager/subject/options 身份合同全部验真，并成功选择 authored",
        "  option 3/native index 2；该 exact PIP-refusal drain 操作本身为 GREEN。",
        "- drain 之后，`53147040` 的重复 paused snapshot 均无 active event，CK3 debug/error log 中",
        "  `ZGAP2MANAGERSEED` marker 数为零。恢复 5 速后日期到达 `53147136`，已越过合同硬上限 `53147040`，",
        "  仍未达到 `zga_phase2_manager_seed.10/.11/.1`。runner 在 manager handoff 和候选合同生成前 fail-closed，",
        "  candidate absent。结论是 **scenario/harness RED，不是产品 RED**，也不提升逐号 readiness。",
        "- production projection 为 `phase2-full-release-r123-550d9ef`，1,031 files / 31,183,422 bytes，产品树",
        "  `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1`，projection manifest SHA-256",
        "  `e0272b2307cfc40a25e635053403fc8ad532298a0b4b85ce83188ba44a7b7eec`，release manifest / ZIP SHA-256",
        "  分别为 `a94e9e6b72182a538c79ba45c1d53424bf2feef6e245a19933c1bfbc1681630c` /",
        "  `12ebe06039167f1ac968916de56a4100a0281e933df112a7e2e1e2f60d8735b6`。关键 B2 产品字节等价检查 GREEN；",
        "  runtime product/fixture 结束后仍分别为 `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1` /",
        "  `8cfa3a3cb30afe411bc802503383b76d6adadf14678198fa469b014b97974666`，外部依赖未变，源码 before/after",
        "  manifest 文件 SHA-256 均为 `3a25e3077f1603fece951732bcdafe94648622970fa588fe09c4f5bfcf2371f7`。",
        "- managed cleanup GREEN，restart_count=0：Frontend warmup PID `93696` 与 final PID `182168` 均已回收，",
        "  final CK3 inventory 为空。主要证据 SHA-256：首次/第二次 preflight",
        "  `6344b2884899546fa21ea90390e804ebcc2cbf81130c7daabb1d70047f83cedd` /",
        "  `7d3de1995b02cbc42f2d1a3c36900f24f8c1205226940b21d01e901392cb7af9`、runner report",
        "  `c1b129b57fbd1bc185836386c7a9e5f6eeb6ad95c609e7f950b2f6e3c870a241`、native readiness",
        "  `8f6d73bf7a7717ac24dce40102a5a046728135cce773e6a3da5df4704555f72a`、loader scan",
        "  `6d64a6f1b55ef89641b3752345ada59593f01e81203cdf966285cde481ffece2`、transition contract",
        "  `864f84ef520ead5bd73e516d43243c22badc32b8f391b64273b4550b3bb083ed`、exact option-3 drain",
        "  `dd0639f98842223a145c3fcd8d25343f2ffee99c3f77bfe38169057227a1521b`、bootstrap wait",
        "  `d41b4cb91b89fa4c30a464fb2564a6bda3ee5b5d716f231b0bd583c14502779e`、cleanup",
        "  `e33a55f61f14bac05146f682de3f4f78e6e4c8b579046bdebbf4984470d3f40c`、relay",
        "  `731a09fbab60347aae753425cd942fe7de1a31ab7785208f3a8d6dc5cd7bc6b4`。",
        "",
        "## R125 直接管理者 seed 的安全帧越界 RED（不改变逐号等级）",
        "",
        "- `2026-09-06 16:20–16:23 Asia/Shanghai` 对冻结 commit",
        "  `31f4163dbed5918962c422b57ad92932458c2b2b` 执行 direct-already-player-manager seed 捕获。无启动预检",
        "  `Z:\\\\p2m125_pre_a\\\\preflight.json` 为 GREEN，`ck3_launch_attempted=false`、`launch_boundary=not-crossed`；冻结源",
        "  ZIP/源码树 SHA-256 为 `cf7ffb56dcfc1e413f290c168717a844433ef1599d1f0dbd6e87bfda82be5b82` /",
        "  `ded6aa41ec3aeda8f0ca3d1850c1f51169684998c1949f74d22a9e6d67365d47`。",
        "- live 完成 loader 303/303、fatal=0、项目归属 blocking matches=0，并达到 paused application-main/native readiness",
        "  GREEN。首个 paused typed snapshot 精确位于 `53164440`，played CharacterID 为 `29037`，active event 为空；直接管理者",
        "  source/entry-route 合同为 GREEN，但 fixture `zga_phase2_manager_seed.1` 未在该源帧出现。fixture/GUI 均已加载，然而全部",
        "  `ZGAP2MANAGERSEED` 成功/RED marker 都为零。直接 `-load_save` 不经过该路线依赖的 lobby hook，而 load-safe GUI 当时又只接受",
        "  旧 terminal-PIP subject，因此 R125 证明的是直接管理者缺少可执行 activation carrier；它**没有**证明任何管理者资格门失败，",
        "  也没有证明这些门已被求值。",
        "- runner 随后尝试合同要求的时间推进；下一帧已在未暂停状态到达 `53164488`，超过唯一安全源日期 `53164440`，且仍无",
        "  active event。runner 立即通过 MCP/native 提交强制保护性暂停并 fail-closed；没有选择任何事件选项，也没有生成候选。",
        "  结论是 **scenario/seed harness RED，不是产品 RED**，不构成完整迁移树 GREEN，也不提升逐号 readiness。",
        "- 顶层 `ocr_used=true` / `image_used=true` 仅属于非玩法 legal-consent gate；玩法状态、推进尝试与保护性暂停均只使用",
        "  MCP/native，`coordinates_used=false`。production projection 为 `phase2-full-release-r125-31f4163`，1,031 files /",
        "  31,183,422 bytes，产品树 `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1`，projection manifest",
        "  SHA-256 `6d8b5e55f41055da8dff7501073387da929d3e3f9a66835bb06775e786810a79`，release manifest / ZIP SHA-256",
        "  分别为 `d012206a97a75730075a34278ecd438d76c5a01094a7e60d4ee06f92c6e6f413` /",
        "  `12ebe06039167f1ac968916de56a4100a0281e933df112a7e2e1e2f60d8735b6`。关键 B2 产品字节等价检查 GREEN；",
        "  runtime product/fixture 结束后仍分别为 `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1` /",
        "  `7eb72b0861d547d597b485fd2468972b724edfb22e77be67e7bca80d55f0ad86`，外部依赖未变；源码 before/after",
        "  manifest 文件 SHA-256 均为 `2aea4ad462a71125799c1f99631c0c14063512d6d9f5d7829b87e086f0dafbf1`。",
        "- managed cleanup GREEN，restart_count=0：Frontend warmup PID `80116` 与 final PID `183912` 均已回收，final CK3",
        "  inventory 为空。主要证据 SHA-256：preflight",
        "  `e3082dcfe8a0856bfb62b8ce9143158d5181159916698b127ef8bbd4a34d3df9`、runner report",
        "  `ba6e10aac872f935fcd7380ae43bb63d8384287c4395c74941a43b8c61df1939`、native readiness",
        "  `ba40300323f825aba86c82efd0e96b83991ef736994d26bc18c61b1fb194629d`、loader scan",
        "  `246a6158dfeaf6b540de3ce0ad8e5d68d5c09662c614b95cb2bd328561ea1b53`、bootstrap wait",
        "  `3b9f01903b382cb7ef8b604ee0f05101a1fc68895051329d73447c5eb9728afc`、direct source",
        "  `b88d365ba5b782963241366f9577f90e418ff0de39da5b894c007cbb3b9c5bb0`、transition contract",
        "  `e715a463326b96e34f395a604ff69a543c076414462038256deb9e9f37846ae1`、cleanup",
        "  `4a973d653d1fb1c0b8daa230eda86375604144b5d6a5267dba3a055af6aa3305`、relay",
        "  `2c6d703bfedc21cf2dbe09d3f957f2c7fc0b47e0aec27aa88e2dc6442fa607b0`。",
        "",
        "## R126 load-safe 直接管理者门禁诊断 RED（不改变逐号等级）",
        "",
        "- `2026-09-06 16:38–16:42 Asia/Shanghai` 对冻结 commit",
        "  `e670e502461cc8f85218d028033cb3cdb1c61495` 执行 R107 direct-player-manager source 的 load-safe carrier",
        "  诊断。无启动预检 `Z:\\\\p2m126_pre2_a\\\\preflight.json` 为 GREEN，`ck3_launch_attempted=false`、",
        "  `launch_boundary=not-crossed`；冻结源 ZIP/源码树 SHA-256 为",
        "  `d049d419a473af7af676534d6bb8cd704c6e62d690389291cce7fcb49a7decb7` /",
        "  `71bea66709388396e355e03ff5c062fc54b546e5d9433391d1001bccb1bda30b`。",
        "- live 完成 loader 303/303、fatal=0、项目归属 blocking matches=0，并达到 paused application-main/native readiness",
        "  GREEN。首个 paused typed snapshot 精确位于 `53164440`、revision 4，played CharacterID 为 `29037`，active event",
        "  为空且尚未发送玩法输入。load-safe carrier 随后确实执行，并一次性记录八项门禁：`celestial=PASS`、",
        "  `review_now=RED`、`prestige_150=PASS`、`b1_inactive=RED`、`review_in_progress_inactive=PASS`、",
        "  `p2c_inactive=PASS`、`pp_inactive=PASS`、`direct_reviewable_vassal=PASS`。",
        "- marker 证明 R126 carrier 已进入实机、管理者门禁链已被求值，也把 source 状态错配精确收敛为：冻结 R107 source",
        "  此刻正处活动 B1，因此 review-now 条件与 B1-inactive 条件同时失败，最终 fixture",
        "  `zga_phase2_manager_seed.1` 按门禁没有触发。结论是 **scenario/seed harness RED，不是产品 RED**；不构成完整迁移树",
        "  GREEN，也不提升任何逐号 readiness。",
        "- runner 按合同尝试必要推进后，下一帧已在未暂停状态到达 `53164488`，超过唯一安全源日期 `53164440`，且仍无",
        "  active event；runner 立即通过 MCP/native 提交保护性暂停并 fail-closed，没有选择事件选项，也没有生成候选。顶层",
        "  `ocr_used=true` / `image_used=true` 仅属于非玩法 legal-consent gate；玩法状态、推进与保护性暂停均只使用 MCP/native，",
        "  `coordinates_used=false`。",
        "- production projection 为 `phase2-full-release-r126-e670e50`，1,031 files / 31,183,422 bytes，产品树",
        "  `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1`，projection manifest SHA-256",
        "  `aadf48112920e7ac74a7fd8503bc13011e693a471daa324708646c7348ab99da`，release manifest / ZIP SHA-256 分别为",
        "  `d3661baec68ebf28f43ca64fb75f6dad39aded77fc60a376d7024371a7cd5b9c` /",
        "  `12ebe06039167f1ac968916de56a4100a0281e933df112a7e2e1e2f60d8735b6`。关键 B2 产品字节等价检查 GREEN；runtime",
        "  product/fixture 结束后仍分别为 `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1` /",
        "  `ba4522d027a939f127b60fc764eb18d68779addb0c075e04aebc867aa00d3c0a`，外部依赖未变；源码 before/after manifest",
        "  文件 SHA-256 均为 `faba9718db0ec46d698f1c576adf3f5f841e312d86ac99607b41d93dcc35efcc`。",
        "- managed cleanup GREEN，restart_count=0：Frontend warmup PID `154964` 与 final PID `181508` 均已回收，final CK3",
        "  inventory 为空。主要证据 SHA-256：preflight",
        "  `572f5f2c93ab819e86aec096bce6e21eb4e590b13cb834a2e918062b7f547bde`、runner report",
        "  `7c7489ec658aeb8629282e77771f0326cd1b2fb46450ea939cae288ee48b7cc7`、native readiness",
        "  `c86028f4a3e821dd6756da1a5494c324529b5240e66e66f7c17cc1afa37a5278`、loader scan",
        "  `8be29b36233b007dd439eeaa8b5787c89394d93fe0b45756e96623eb51589926`、bootstrap wait",
        "  `7e97f9c0d9dd54f7cf73d4ef4bfefeb820aec3886179a63d4c3d23699311c7f5`、direct source",
        "  `b88d365ba5b782963241366f9577f90e418ff0de39da5b894c007cbb3b9c5bb0`、transition contract",
        "  `39408cd0b34fc46a7f95ec8968a70e2712d2a9b048ff27ab39314885802282fd`、debug gate log",
        "  `fe1c39e5adc1ef46a19e7c0d00f3f7087147feb79ab1e4778d1cbb47bc2e17be`、cleanup",
        "  `dddc6dc8f294b16a9cfa911e7db0e01bc963910b314197c8c1261bef0734a78d`、relay",
        "  `22eb83f820d5830b844a95f20685bbf556ba9288621295e6867f9e1df8ffb518`。",
        "",
        "## R127 精确 PIP 后切换管理者门禁诊断 RED（不改变逐号等级）",
        "",
        "- `2026-09-06 16:59–17:02 Asia/Shanghai` 对冻结 commit",
        "  `4b8513e036f94563259c8f4ee0367e07fd48362d` 执行 restored terminal-PIP player-manager seed",
        "  捕获。无启动预检 `Z:\\\\p2m127_pre_a\\\\preflight.json` 为 GREEN；冻结源 ZIP/源码树 SHA-256 为",
        "  `b6710b8e96ef52028f31444f58e5771b72e71f53fe9e1c371be9224595357157` /",
        "  `61834c4b0659981ff771e9848ee0cfb8271045d30e09ea5df650a7712719eb78`。",
        "- live 完成 loader 303/303、fatal=0、项目 blocking matches=0 和 paused native readiness GREEN。",
        "  runner 以 5 速从 `53147016` 到达 `zg361b2.40@53147040`，用 MCP 验真 source `29037`、manager",
        "  `32904` 后成功选择 authored option 3 / native index 2；postcondition verified，事件关闭后仍暂停。",
        "- post-switch 14 项门禁为 12 PASS / 2 RED：`review_now=RED`、`b1_inactive=RED`；其余 human、alive、",
        "  landed、owner/pending、celestial、game rule、prestige、review-progress/P2C/PP inactive 与 subject binding",
        "  均 PASS。因此最终 `.1` 正确未出现。这是 **fixture/seed target-state RED，不是 loader、解析或产品 RED**，",
        "  不提升逐号 readiness，也不授权放宽 `.100`。",
        "- projection `phase2-full-release-r127-4b8513e` 为 1,031 files，产品树",
        "  `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1`；projection/release manifest/ZIP",
        "  SHA-256 分别为 `de3a83c3c81c9dd8554816c0111e85bcccb27bfd76ee4301b2d6705f9ebb29d3`、",
        "  `8d6957762ae3d612e0a23d88d78929178a226eacc5fc16b2e5ca2ab8badfc564`、",
        "  `12ebe06039167f1ac968916de56a4100a0281e933df112a7e2e1e2f60d8735b6`。产品/fixture/source 前后不变。",
        "- cleanup GREEN、`restart_count=0`，warmup PID `170108` 与 final PID `85140` 均已回收。玩法 MCP-only、",
        "  `coordinates_used=false`；OCR/image 仅用于 legal-consent 且零点击。证据 SHA-256：preflight",
        "  `32e9eb3451073d3a10005cf739e83bf55b462c0a48ce53d9ddeaf5abd5079d9f`、runner",
        "  `43311d147adcd82f032a63543dfd9d6cf8103b77c60b2e3b6ab11f0aee06b786`、native readiness",
        "  `b39425bfbe31fb9248c23590b77e881fd8ad76074f8944f9239784ead6595778`、loader scan",
        "  `a6b39bb1d5953e0ddbed6816d6c837693f6018c30a95950dec8ac5a7d8b66374`、exact drain",
        "  `5767434396318974ed8c1b802cf94091879ab47762cf9eea7a7ebfe2a41f2cdd`、manager route",
        "  `f5b8f0094a1b36e26b886c2c94a324abaf2ed5830745b12b8587be1622c4cf40`、debug gate log",
        "  `52cc1006df9ca2150eed156ccd9d67c14da1f7a99663ee03918c033640164f73`、cleanup",
        "  `e306f17618fd9f3075c12253af0220656437fd8774dfbe7d73d7113b256205a3`、relay",
        "  `0bd5e3f432f7606b560b6cadd25f5c2aff811ed0f92ee8334e5965ba6a023fbb`。",
        "",
        "## R128 R119 多人本地玩家恢复 readiness RED（不改变逐号等级）",
        "",
        "- `2026-09-06 17:25–17:32 Asia/Shanghai` 对冻结 commit",
        "  `2273c6061b4235c66a93eec026116523d670ba27` 执行 clean R119 player-manager seed probe。无启动预检",
        "  `Z:\\p2m128_pre_a\\preflight.json` 为 GREEN；源存档为 26,325,927 bytes / SHA-256",
        "  `bf5960b7194e1222029add884743c688fee0d86f95559670c587317461519e74`，冻结源 ZIP/源码树 SHA-256 为",
        "  `9c369c2cd3aa53bfc553efc9cf2ff2c39fb7147dfdbffb87d312d0a59d2f34cf` /",
        "  `a8f89ab8ff15705da62fa945a65c1a89d0e1ebc4d76c318b2f288e8db2988717`。",
        "- live 完成 loader 303/303、fatal=0 并到达 `In Game`；exact-build bridge connected、",
        "  semantic_state_available=true。但 native readiness 在 180 秒后 RED：末帧 `date_raw=51848904`、speed 3、",
        "  paused、`local_player_id=1`、`map_ready=true`，而 `played_character=null`；main-thread mailbox",
        "  `installed=false`、`ready=false`、pump epoch=0，无法建立 application-main stable binding。",
        "- 这是 **multiplayer local-player restoration/native-readiness RED，不是产品 parser 或 loader RED**；没有进入",
        "  5 速、事件选择、管理者门禁或任何业务验收门，不提升逐号 readiness。正式 loader-error batch scan 在",
        "  readiness 之后，本轮未执行，因此不声称项目 blocking matches=0。",
        "- projection/release manifest/ZIP SHA-256 为",
        "  `508f1ff3950cd19032b49cc9e25014c4192bb14a4296db808e5fcd49a8ec1b72`、",
        "  `57fcad53f65657fe1006b40ac8b3e7218d88c0ed9e0a8cd3b7ead2ba7cf71e6f`、",
        "  `12ebe06039167f1ac968916de56a4100a0281e933df112a7e2e1e2f60d8735b6`。runtime product/fixture 结束后仍为",
        "  `55a08b950cb3fabd5628913a191214d60b2f8b973c72a4788fd8769536a35db1` /",
        "  `cee41a7ce842d1e649637717d918961a314d6374f9b86fa5f3655801b4a7465d`，source before/after manifest SHA-256",
        "  均为 `96da308db88e6deeaede32fecc7f26c2d1a0fb68563ac2cd02135c3ce71846c6`。",
        "- cleanup GREEN、`restart_count=0`；warmup PID `40864` 与 final PID `56312` 均已回收，final inventory 与后续",
        "  process check 均无 CK3。玩法 MCP-only、`coordinates_used=false`；OCR/image 仅用于 legal-consent 且零点击。",
        "  证据 SHA-256：preflight `1169dc20d7dc61b01a96ff6dd825977bdb0e692dc475f98b37e561330ca24b97`、runner",
        "  `e012598262ef8625bc89b55fd2549a0252242256162de9d9897d1262430469f6`、native readiness",
        "  `24ff1d90c84b6d5b336e7fe6cb9d208dd6996e343fc196409c5ef30d49e3c819`、critical-B2 equivalence",
        "  `e971dd76e2660b81785a2d67de769b2e8ac8768329776685082a5c76a0b9f565`、cleanup",
        "  `5de75f59e7f7690ea33249321407a990ffe7f8477952e48c942a1b5b57a88d0b`、relay",
        "  `f20abffead4234eab9309a2607f5e44fabb9f1853808ebdc312e8e4cf568174c`。",
        "",
        "## R107 基线完整产品验收快照（不改变逐号等级）",
        "",
        "| 项 | 实证 |",
        "|---|---|",
        f"| 运行 | `{snapshot.run_id}` · `{snapshot.observed_at}` · `{snapshot.result}` |",
        f"| 产品身份 | commit `{snapshot.product_commit}` · projection `{snapshot.projection}` · {snapshot.verified_file_count} files · tree `{snapshot.product_tree_sha256}` · manifest `{snapshot.release_manifest_sha256}` |",
        f"| CK3 loader | exact build 完成 {snapshot.loader_database_nodes}/{snapshot.loader_database_nodes} database nodes，fatal={snapshot.loader_fatal_count} |",
        f"| 实机时间轴 | 默认 {snapshot.speed} 速，{snapshot.observation_days} 游戏日，{snapshot.native_observations} 次 native/MCP 观测，精确处理 {len(snapshot.drained_event_keys)} 次事件：{drained_events} |",
        f"| 已闭合回归 | 产品签名归零：{cleared_signatures} |",
        f"| 证据 | {snapshot_evidence} |",
        f"| 边界 | {snapshot.boundary} |",
        "",
        "## 最高状态（互斥）",
        "",
        "| 状态 | 数量 | 精确 ID ranges |",
        "|---|---:|---|",
        ]
    )
    for level in LEVELS:
        lines.append(
            f"| `{level.key}` | {EXCLUSIVE_COUNTS[level.key]} | "
            f"{format_ranges(ids_at_level(level)) or '无'} |"
        )
    lines.extend(
        [
            "",
            "## 累计证据门",
            "",
            "| 证据门 | 已达到 | 尚缺 | 已达到 ranges | 尚缺 ranges |",
            "|---|---:|---:|---|---|",
        ]
    )
    for level in LEVELS:
        reached = set(ids_at_least(level))
        missing = all_ids - reached
        lines.append(
            f"| `{level.key}` | {len(reached)} | {len(missing)} | "
            f"{format_ranges(reached)} | {format_ranges(missing) or '无'} |"
        )
    lines.extend(
        [
            "",
            "## 逐号状态",
            "",
            "| ID | 机制 | 最高状态 | 包 | 证据 | 边界说明 |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for mechanism_id, record in READINESS_BY_ID.items():
        mechanism = mechanism_by_id[mechanism_id]
        evidence = "<br>".join(f"`{path}`" for path in record.evidence)
        lines.append(
            f"| {mechanism_id:03d} | {mechanism.title_cn} | `{record.level.key}` | "
            f"`{record.package}` | {evidence} | {record.note} |"
        )
    lines.append("")
    return BOM + ("\n".join(lines)).encode("utf-8")


def outputs(mechanisms: list[Mechanism]) -> dict[Path, bytes]:
    runtime_plans = build_runtime_plans(mechanisms)
    for plan in runtime_plans:
        plan["primitive_recipe"] = list(primitive_recipe_for(plan))
    payload = manifest_payload(mechanisms, runtime_plans)
    result: dict[Path, bytes] = {
        MOD_ROOT / "common" / "script_values" / "zg361_generated_mechanism_values.txt": render_values(),
        MOD_ROOT / "common" / "modifiers" / "zg361_generated_mechanism_modifiers.txt": render_modifiers(),
        MOD_ROOT / "events" / "zg361_generated_mechanism_events.txt": render_events(mechanisms),
        MOD_ROOT / "common" / "decisions" / "zg361_mechanism_decisions.txt": render_decisions(),
        MOD_ROOT / "common" / "scripted_guis" / "zg361_generated_mechanism_guis.txt": render_scripted_guis(),
        MOD_ROOT / "gui" / "zg361_mechanism_bridge.gui": render_bridge_gui(),
    }
    result.update(effect_shard_outputs(mechanisms))
    result.update(render_runtime_plan_files(mechanisms, runtime_plans))
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
    result[MOD_ROOT / "docs" / "361-phase2-coverage-ledger.md"] = (
        render_readiness_ledger(mechanisms)
    )
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

    expected_effects = {path for path in rendered if path.parent == EFFECTS_DIR}
    residue = generated_effect_residue(expected_effects)
    if args.check:
        mismatches = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, data in rendered.items()
            if not path.is_file() or path.read_bytes() != data
        ]
        if mismatches or residue:
            print("RED: generated files are stale:")
            for mismatch in mismatches:
                print(f"  - {mismatch}")
            for path in residue:
                print(f"  - LEGACY_OR_UNEXPECTED {path.relative_to(MOD_ROOT).as_posix()}")
            return 1
    else:
        for path in residue:
            payload = path.read_bytes()
            if path != LEGACY_EFFECTS_PATH and not payload.startswith(
                BOM + GENERATED_HEADER.encode("utf-8")
            ):
                raise RuntimeError(f"refusing to remove unowned effect file: {path}")
            path.unlink()
        for path, data in rendered.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    verb = "checked" if args.check else "generated"
    print(f"GREEN: {verb} {MECHANISM_COUNT} mechanisms across {len(rendered)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
