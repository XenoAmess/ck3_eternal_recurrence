"""Render source-bound Living Artifacts content; qualification is reported separately.

This module never changes the installed game. Native producer patches are returned
to the formal builder, which verifies the shared SourcePatch hash and recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from living_artifacts_model import Language, SourcePatch

ContentKind = Literal["affix", "curse"]
ScopeKind = Literal["artifact", "character", "county", "secret"]


@dataclass(frozen=True)
class ContentDefinition:
    number: int
    key: str
    kind: ContentKind
    chinese_name: str
    english_name: str
    chinese_description: str
    english_description: str


@dataclass(frozen=True)
class StateField:
    name: str
    scope: ScopeKind
    value_type: Literal["integer", "number", "scope", "flag", "timed_flag"]
    purpose: str


@dataclass(frozen=True)
class ContentGap:
    content_key: str
    requirement: str
    reason: str


AFFIXES: tuple[ContentDefinition, ...] = (
    ContentDefinition(1, "blood_dividend", "affix", "血宴分红", "Blood Dividend", "亲自指挥获胜后获得10/20/30金币和8压力。", "A personally commanded victory grants 10/20/30 gold and 8 stress."),
    ContentDefinition(2, "funeral_choir", "affix", "丧钟合唱", "Funeral Choir", "记住真实战死的骑士，并在之后的原生决斗中发出回声。", "Remembers knights who genuinely fell in battle and echoes in a later native duel."),
    ContentDefinition(3, "table_crasher", "affix", "蹭饭王", "Table Crasher", "完成宴会时替主人结酒账，并讨好一名真实宾客。", "Pays an extra wine bill after a completed feast and pleases a real guest."),
    ContentDefinition(4, "borrowed_voice", "affix", "借来的嗓子", "Borrowed Voice", "原生拉拢成功后获得25/50/75威望，失去5/10/15恐怖值。", "A successful native sway grants 25/50/75 prestige and costs 5/10/15 dread."),
    ContentDefinition(5, "copper_stomach", "affix", "铜胃偷工", "Copper Stomach", "直属建设真正完工时吐出10/20/30金币，当地控制力下降2/3/4。", "Completed direct-domain construction yields 10/20/30 gold and costs 2/3/4 control."),
    ContentDefinition(6, "dream_credit", "affix", "梦中高利贷", "Dream Credit", "每年可能借到25/50/75金币，以后十二期各偿3/5/7金币。", "May lend 25/50/75 gold annually; twelve later instalments cost 3/5/7 each."),
    ContentDefinition(7, "secret_sniffer", "affix", "秘密嗅探器", "Secret Sniffer", "收藏实际获知的秘密，新主人可能真正听见其中一条。", "Stores genuinely discovered secrets; a new owner may actually learn one."),
    ContentDefinition(8, "alibi", "affix", "不在场证明", "Alibi", "针对主人的原生敌对计谋实际被发现后，恐怖值+5/10/15、威望-15/30/45；不猜测主谋。", "An actually discovered hostile scheme against the owner grants 5/10/15 dread and costs 15/30/45 prestige; never guesses its owner."),
    ContentDefinition(9, "map_chewer", "affix", "嚼地图", "Map Chewer", "真正抵达未记录目的地时获得20/35/50学识经验及8压力。", "A genuine new destination grants 20/35/50 learning experience and 8 stress."),
    ContentDefinition(10, "ink_addiction", "affix", "墨水成瘾", "Ink Addiction", "实际解锁生活技能后，365日月度学识生活方式经验增加5/10/15%，损失40/60/80威望。", "A genuine perk unlock grants 5/10/15% monthly learning lifestyle experience for 365 days and costs 40/60/80 prestige."),
    ContentDefinition(11, "unseemly_laughter", "affix", "笑到失态", "Unseemly Laughter", "精神崩溃真正结算后减压10/15/20，失去20/35/50威望。", "After an actual mental break resolves, loses 10/15/20 stress and 20/35/50 prestige."),
    ContentDefinition(12, "jealous_prima", "affix", "嫉妒的首席", "Jealous Prima", "争夺另一件活装备的能力；连续三月会影响下一次自然突变。", "Competes with another living item; three consecutive months affect the next natural mutation."),
)

ENABLED_COMBOS: tuple[str, ...] = (
    "victors_requiem", "credit_inspection", "under_table_prompt", "let_it_cry",
)

CURSES: tuple[ContentDefinition, ...] = (
    ContentDefinition(1, "blood_tithe", "curse", "鲜血什一税", "Blood Tithe", "穿戴健康-0.4/-0.8/-1.2；亲自获胜后压力+15/+25/+40。", "While equipped: -0.4/-0.8/-1.2 health; personally commanded victories add 15/25/40 stress."),
    ContentDefinition(2, "aristocratic_appetite", "curse", "贵族胃", "Aristocratic Appetite", "每月收固定15/30/50或正月收入20/35/50%中的较高额；不足再加15/25/40压力。", "Monthly: the greater of 15/30/50 gold or 20/35/50% positive income; shortage adds 15/25/40 stress."),
    ContentDefinition(3, "fickle_body", "curse", "善变之躯", "Fickle Body", "夺去本件1/2/3个稳定异能槽的正面效果，其他正事件机会乘75/50/25%；季度压力+15/+25/+40。", "Disables 1/2/3 stable positive slots; other positive events have 75/50/25% their chance; quarterly stress +15/25/40."),
    ContentDefinition(4, "telltale", "curse", "大嘴巴", "Telltale", "隐秘度-10/-20/-30个百分点；季度20/35/50%机会公开真实自身秘密。", "Secrecy -10/-20/-30 points; quarterly 20/35/50% chance to expose a real personal secret."),
    ContentDefinition(5, "runaway", "curse", "离家出走", "Runaway", "正面持续收益乘90/80/70%；季度10/20/35%机会把原件带到合法新主手中。", "Positive passive benefits at 90/80/70%; quarterly 10/20/35% chance to move the original item to a legal recipient."),
    ContentDefinition(6, "jealous_lover", "curse", "妒侣", "Jealous Lover", "真实配偶好感光环-15/-30/-50，年度还可能对配偶或情人留下两年怨恨。", "Real spouses receive -15/-30/-50 equipped opinion; yearly resentment can affect spouses or lovers."),
    ContentDefinition(7, "rust_hunger", "curse", "锈蚀饥饿", "Rust Hunger", "每装备月额外耗损2/4/7耐久；月结发现原件耐久回升时，年度可能索取5/10/15金币和15/25/40压力。", "Loses 2/4/7 durability each equipped month; an observed recovery can annually cost 5/10/15 gold and 15/25/40 stress."),
    ContentDefinition(8, "unquiet_realm", "curse", "失眠之国", "Unquiet Realm", "控制力月增长-0.2/-0.4/-0.7；季度可能损失10/20/35控制力与15/30/50民众好感。", "Monthly control growth -0.2/-0.4/-0.7; quarterly may lose 10/20/35 control and 15/30/50 popular opinion."),
)

STATE_FIELDS: tuple[StateField, ...] = (
    StateField("xalw_content_month_done", "character", "integer", "Last real monthly dispatch; never advanced by UI inspection."),
    StateField("xalw_content_rank", "character", "integer", "Transient selected rank for a real source callback."),
    StateField("xalw_content_source", "character", "scope", "Transient selected equipped artifact reference."),
    StateField("xalw_content_loan_principal_year", "character", "integer", "Annual original-borrower principal opportunity."),
    StateField("xalw_content_loan_instalment", "character", "integer", "Actual original-borrower instalment size."),
    StateField("xalw_content_loan_periods", "character", "integer", "Number of future instalment obligations remaining."),
    StateField("xalw_content_loan_arrears", "character", "number", "Unpaid amounts; cannot be reassigned with the artifact."),
    StateField("xalw_content_loan_due", "character", "number", "Current payment including older unpaid amounts."),
    StateField("xalw_content_payment", "character", "number", "Current bounded actual payment."),
    StateField("xalw_content_appetite_quote", "character", "number", "Frozen quote before the monthly deduction."),
    StateField("xalw_content_blood_cooldown", "character", "timed_flag", "Ninety-day real-victory curse event cooldown."),
    StateField("xalw_content_dividend_cooldown", "character", "timed_flag", "Ninety-day real-victory positive event cooldown."),
    StateField("xalw_content_sway_cooldown", "character", "timed_flag", "180-day actual successful sway cooldown."),
    StateField("xalw_content_build_cooldown", "character", "timed_flag", "180-day actual building completion cooldown."),
) + tuple(
    StateField("xalw_content_" + key, "character", "integer", "Calendar-year source opportunity ledger; follows the character.")
    for family in ("dividend", "blood", "sway", "build", "destination", "ink", "feast", "laughter", "alibi", "secret", "funeral", "exposure", "realm", "lover")
    for key in (family + "_year", family + "_count")
) + tuple(
    StateField("xalw_content_" + family + "_cooldown", "character", "timed_flag", "Real source callback cooldown; transferring an item does not reset it.")
    for family in ("destination", "ink", "feast", "laughter", "alibi", "secret", "funeral", "prompt")
) + tuple(
    StateField("xalw_content_" + key, "character", "number", "Original borrower payment/credit ledger; remains after unequip or transfer.")
    for key in ("loan_credit", "loan_credit_used", "loan_bad_debt", "build_credit", "build_reward")
) + tuple(
    StateField("xalw_content_" + key, "artifact", "scope", "A reference to a genuinely observed game object; always validate existence before use.")
    for key in ("previous_owner", "prima_target", "feast_guest", *(f"secret_{i}" for i in range(1, 4)), *(f"memory_{i}" for i in range(1, 4)), *(f"destination_{i}" for i in range(1, 9)))
) + tuple(
    StateField("xalw_content_" + key, "artifact", "integer", "Persistent original-item ability/projection state; never creates an extra growth transaction.")
    for key in ("fickle_rank", "runaway_rank", "rust_rank", "inherited_rank", "recovery_year", "prima_streak", "prima_last_month", "ink_slot", "ink_rank", "ink_effective_rank", "prima_slot", "prima_rank", "prima_effective_rank", "echo_power", "echo_slot", "jealous_slot", *(f"disabled_{i}" for i in range(1, 4)), *(f"memory_prowess_{i}" for i in range(1, 4)))
) + tuple(
    StateField("xalw_content_" + key, "artifact", "timed_flag", "Timed original-item state; original calendar expiry continues while unequipped.")
    for key in ("ink_active", "prima_active", "echo_active", "runaway_cooldown")
) + (
    StateField("xalw_content_last_equipped_durability", "artifact", "number", "Last actually equipped monthly durability observation; repair is inferred only from a later increase."),
    StateField("xalw_content_secret_pending_owner", "artifact", "flag", "One first-equipped-month attempt for this native ownership change; not an immediate equip hook."),
    StateField("xalw_content_observed_liege", "character", "scope", "Knight's genuine living every_knight membership observation."),
    StateField("xalw_content_observed_prowess", "character", "number", "Knight's last genuinely living prowess observation; not a death-time reconstruction."),
    StateField("xalw_content_last_wine_host", "character", "scope", "Real feast guest relation, expires after 730 days."),
    StateField("xalw_content_wine_guest_cooldown", "character", "timed_flag", "A real feast guest can receive the wine benefit once per 730 days across hosts."),
)

# Missing production coverage is explicit and is consumed by the release gate.
# Rendering a prototype does not qualify it or enable an incomplete core ability.
CONTENT_GAPS: tuple[ContentGap, ...] = ()
# Empty means that the revised production source contracts are emitted. It is
# not a runtime PASS: every content-acceptance case must still be observed.


def _effect(name: str, body: str) -> str:
    return f"{name} = {{\n{body}\n}}\n"


def _rank_cases(body_by_rank: tuple[str, ...], variable: str = "xalw_content_rank") -> str:
    if len(body_by_rank) != 3:
        raise ValueError("Content rank rendering requires exactly three branches")
    return "\n".join(
        f"if = {{ limit = {{ var:{variable} = {rank} }}\n{body}\n}}"
        for rank, body in enumerate(body_by_rank, start=1)
    )


def _present_condition(fields: tuple[str, ...], condition: str) -> str:
    """Create an actual lazy trigger branch; sibling guards do not short-circuit."""
    presence = " ".join(f"has_variable = {field}" for field in fields)
    return (
        "AND = { trigger_if = { limit = { " + presence + " }\n" + condition
        + "\n} trigger_else = { always = no } }"
    )


def _slot_condition(kind: ContentKind, slot: int, condition: str) -> str:
    """Leave an empty slot absent and read its ID/rank only in a lazy branch."""
    stem = "xalw_affix" if kind == "affix" else "xalw_curse"
    return _present_condition((f"{stem}_{slot}", f"{stem}_rank_{slot}"), condition)


def _selector(kind: ContentKind, number: int) -> str:
    slots = range(1, 7) if kind == "affix" else range(1, 3)
    stem = "xalw_affix" if kind == "affix" else "xalw_curse"
    pieces = ["save_scope_as = xalw_content_actor", "set_variable = { name = xalw_content_rank value = 0 }", "remove_variable = xalw_content_source", "set_variable = { name = xalw_content_slot value = 0 }"]
    checks: list[str] = []
    for slot in slots:
        condition = _slot_condition(kind, slot, f"var:{stem}_{slot} = {number} var:{stem}_rank_{slot} > scope:xalw_content_actor.var:xalw_content_rank")
        checks.append(
            f"if = {{ limit = {{ {condition} }}\n"
            "save_scope_as = xalw_content_candidate\n"
            f"scope:xalw_content_actor = {{ set_variable = {{ name = xalw_content_rank value = scope:xalw_content_candidate.var:{stem}_rank_{slot} }} "
            f"set_variable = {{ name = xalw_content_source value = scope:xalw_content_candidate }} set_variable = {{ name = xalw_content_slot value = {slot} }} }}\n}}"
        )
    pieces.append("every_character_artifact = { limit = { is_equipped = yes xalw_is_living_trigger = yes }\n" + "\n".join(checks) + "\n}")
    if kind == "affix":
        blocked = " ".join(f"var:xalw_content_disabled_{i} ?= scope:xalw_content_actor.var:xalw_content_slot" for i in range(1, 4))
        pieces.append("set_variable = { name = xalw_content_effective_rank value = var:xalw_content_rank }")
        disabled = _present_condition(("xalw_content_source",), f"var:xalw_content_source = {{ OR = {{ {blocked} }} }}")
        jealous = _present_condition(("xalw_content_jealous_slot",), "var:xalw_content_jealous_slot = scope:xalw_content_actor.var:xalw_content_slot")
        jealous_source = _present_condition(("xalw_content_source",), f"var:xalw_content_source = {{ {jealous} }}")
        pieces.append(f"if = {{ limit = {{ {disabled} }} set_variable = {{ name = xalw_content_effective_rank value = 0 }} }}")
        pieces.append(f"else_if = {{ limit = {{ {jealous_source} }} change_variable = {{ name = xalw_content_effective_rank add = -1 }} }}")
    return "\n".join(pieces)


def _positive_gate(body: str, base: int = 100) -> str:
    chance = f"""value = {base}
if = {{ limit = {{ var:xalw_content_source = {{ var:xalw_resonance < 40 }} }} multiply = 0.5 }}
else_if = {{ limit = {{ var:xalw_content_source = {{ var:xalw_resonance < 80 }} }} multiply = 0.75 }}
if = {{ limit = {{ var:xalw_content_source = {{ xalw_is_growth_suppressed_trigger = yes }} }} multiply = 0.5 }}"""
    for rank, factor in ((1, "0.75"), (2, "0.5"), (3, "0.25")):
        chance += f"\nif = {{ limit = {{ var:xalw_content_effective_rank > 0 var:xalw_content_source = {{ var:xalw_content_fickle_rank ?= {rank} }} }} multiply = {factor} }}"
    return f"random = {{ chance = {{ {chance} }}\n{body}\n}}"


def _annual_reset(key: str) -> str:
    return f"""if = {{
 limit = {{ NOT = {{ var:xalw_content_{key}_year ?= current_year }} }}
 set_variable = {{ name = xalw_content_{key}_year value = current_year }}
 set_variable = {{ name = xalw_content_{key}_count value = 0 }}
}}"""


def _counted_event(key: str, days: int, annual: int, body: str, positive: bool) -> str:
    complete = (
        f"set_variable = {{ name = xalw_content_{key}_cooldown value = yes days = {days} }}\n"
        f"change_variable = {{ name = xalw_content_{key}_count add = 1 }}\n{body}"
    )
    if positive:
        complete = _positive_gate(complete)
    return _annual_reset(key) + f"""\nif = {{
limit = {{ var:xalw_content_rank > 0 NOT = {{ has_variable = xalw_content_{key}_cooldown }} var:xalw_content_{key}_count < {annual} }}
{complete}
}}"""


def _paired_rank(number: int) -> str:
    pieces = ["set_variable = { name = xalw_content_combo_rank value = 0 }"]
    for slot in range(1, 7):
        blocked = " ".join(f"var:xalw_content_disabled_{i} ?= {slot}" for i in range(1, 4))
        condition = _slot_condition("affix", slot, f"var:xalw_affix_{slot} = {number} NOR = {{ {blocked} }}")
        pieces.append(f"""var:xalw_content_source = {{ save_scope_as = xalw_content_pair_item if = {{ limit = {{ {condition} }}
scope:xalw_content_actor = {{ set_variable = {{ name = xalw_content_combo_rank value = scope:xalw_content_pair_item.var:xalw_affix_rank_{slot} }}
if = {{ limit = {{ scope:xalw_content_pair_item = {{ var:xalw_content_jealous_slot ?= {slot} }} }} change_variable = {{ name = xalw_content_combo_rank add = -1 }} }}
set_variable = {{ name = xalw_content_combo_rank value = {{ value = var:xalw_content_combo_rank min = 0 max = var:xalw_content_effective_rank }} }} }}
}} }}""")
    return "\n".join(pieces)


def _render_source_handlers() -> str:
    blood_positive = _selector("affix", 1) + "\n" + _counted_event(
        "dividend", 90, 2,
        _rank_cases(tuple(f"add_gold = {amount}" for amount in (10, 20, 30)), "xalw_content_effective_rank") + "\nadd_stress = 8",
        True,
    )
    blood_curse = _selector("curse", 1) + "\n" + _counted_event(
        "blood", 90, 4,
        _rank_cases(tuple(f"add_stress = {amount}" for amount in (15, 25, 40))),
        False,
    )
    winner = "side_commander ?= {\nif = { limit = { is_alive = yes }\n" + blood_positive + "\n" + blood_curse + "\n}\n}"
    sway_reward = _paired_rank(3) + """
if = { limit = { var:xalw_content_combo_rank > 0 var:xalw_content_source = { var:xalw_content_feast_guest ?= scope:target } NOT = { has_variable = xalw_content_prompt_cooldown } }
set_variable = { name = xalw_content_prompt_cooldown value = yes days = 365 }
var:xalw_content_source = { remove_variable = xalw_content_feast_guest }
add_stress = 5
""" + _rank_cases(tuple(f"scope:target = {{ add_opinion = {{ target = scope:xalw_content_actor modifier = xalw_content_opinion_plus_{opinion}_2y }} }}" for opinion in (5, 10, 15)), "xalw_content_combo_rank") + "\n}\nelse = {\n" + _rank_cases(tuple(f"add_prestige = {prestige}" for prestige in (25, 50, 75)), "xalw_content_effective_rank") + "\n}"
    sway = "scope:owner ?= {\n" + _selector("affix", 4) + "\n" + _counted_event(
        "sway", 180, 2,
        sway_reward + "\n" + _rank_cases(tuple(f"add_dread = -{dread}" for dread in (5, 10, 15))),
        True,
    ) + "\n}"
    build_reward = _paired_rank(6) + _rank_cases(tuple(f"set_variable = {{ name = xalw_content_build_reward value = {gold} }}" for gold in (10, 20, 30)), "xalw_content_effective_rank") + """
if = { limit = { var:xalw_content_combo_rank > 0
trigger_if = { limit = { has_variable = xalw_content_loan_periods has_variable = xalw_content_loan_arrears has_variable = xalw_content_loan_instalment has_variable = xalw_content_loan_credit }
OR = { var:xalw_content_loan_periods > 0 var:xalw_content_loan_arrears > 0 }
} trigger_else = { always = no } }
set_variable = { name = xalw_content_build_credit value = { value = var:xalw_content_loan_periods multiply = var:xalw_content_loan_instalment add = var:xalw_content_loan_arrears subtract = var:xalw_content_loan_credit min = 0 max = var:xalw_content_build_reward } }
change_variable = { name = xalw_content_loan_credit add = var:xalw_content_build_credit }
} else = { add_gold = var:xalw_content_build_reward }
"""
    building = """save_scope_as = xalw_content_province
county = { save_scope_as = xalw_content_county }
county.holder ?= {
""" + _selector("affix", 5) + "\n" + _counted_event(
        "build", 180, 2,
        "set_variable = { name = xalw_content_build_reward value = 0 }\n" + build_reward + "\n" + _rank_cases(tuple(f"scope:xalw_content_county = {{ change_county_control = -{control} }}" for control in (2, 3, 4))),
        True,
    ) + "\n}"
    remembered = "\n".join(f"var:xalw_content_destination_{slot} ?= scope:xalw_content_destination" for slot in range(1, 9))
    shifts = "\n".join(
        f"if = {{ limit = {{ exists = var:xalw_content_destination_{slot - 1} }} set_variable = {{ name = xalw_content_destination_{slot} value = var:xalw_content_destination_{slot - 1} }} }}"
        for slot in range(8, 1, -1)
    )
    remember = "var:xalw_content_source = {\n" + shifts + "\nset_variable = { name = xalw_content_destination_1 value = scope:xalw_content_destination }\n}"
    arrival_body = "current_travel_plan.current_location = { save_scope_as = xalw_content_destination }\n" + _selector("affix", 9)
    new_destination = _present_condition(("xalw_content_source",), f"var:xalw_content_source = {{ NOR = {{ {remembered} }} }}")
    arrival_body += f"\nif = {{ limit = {{ var:xalw_content_rank > 0 {new_destination} }}\n"
    arrival_body += _counted_event(
        "destination", 90, 3,
        _rank_cases(tuple(f"add_learning_lifestyle_xp = {amount}" for amount in (20, 35, 50)), "xalw_content_effective_rank") + "\nadd_stress = 8\n" + remember,
        True,
    ) + "\n}"
    return "\n".join((
        _effect("xalw_content_combat_winner_effect", winner),
        _effect("xalw_content_sway_success_effect", sway),
        _effect("xalw_content_building_completed_effect", building),
        _effect("xalw_content_arrival_effect", arrival_body),
    ))


def _render_loan_monthly() -> str:
    payment = """if = {
limit = { OR = { var:xalw_content_loan_periods > 0 var:xalw_content_loan_arrears > 0 } }
set_variable = { name = xalw_content_loan_due value = var:xalw_content_loan_arrears }
if = {
 limit = { var:xalw_content_loan_periods > 0 }
 change_variable = { name = xalw_content_loan_due add = var:xalw_content_loan_instalment }
 change_variable = { name = xalw_content_loan_periods add = -1 }
}
set_variable = { name = xalw_content_loan_credit_used value = { value = var:xalw_content_loan_credit max = var:xalw_content_loan_due } }
change_variable = { name = xalw_content_loan_credit subtract = var:xalw_content_loan_credit_used }
change_variable = { name = xalw_content_loan_due subtract = var:xalw_content_loan_credit_used }
""" + _bounded_payment("xalw_content_loan_due", "add_stress = 5") + """
set_variable = { name = xalw_content_loan_arrears value = { value = var:xalw_content_loan_due subtract = var:xalw_content_payment min = 0 } }
}
"""
    setup = "\n".join(
        f"if = {{ limit = {{ NOT = {{ has_variable = {field} }} }} set_variable = {{ name = {field} value = 0 }} }}"
        for field in ("xalw_content_loan_periods", "xalw_content_loan_arrears", "xalw_content_loan_instalment", "xalw_content_loan_credit")
    )
    borrow = _selector("affix", 6) + """
if = {
limit = { age >= 18 var:xalw_content_rank > 0 NOT = { var:xalw_content_loan_principal_year ?= current_year } }
# The first eligible calendar-month opportunity is consumed even if the roll fails.
set_variable = { name = xalw_content_loan_principal_year value = current_year }
if = { limit = { var:xalw_content_loan_periods = 0 var:xalw_content_loan_arrears = 0 }
""" + _positive_gate(_rank_cases(tuple(f"add_gold = {principal}" for principal in (25, 50, 75)), "xalw_content_effective_rank") + "\n" + _rank_cases(tuple(
        f"set_variable = {{ name = xalw_content_loan_instalment value = {instalment} }}\nset_variable = {{ name = xalw_content_loan_periods value = 12 }}"
        for instalment in (3, 5, 7)
    ))) + "\n}\n}"
    return setup + "\n" + payment + "\n" + borrow


def _render_curse_calendar() -> str:
    quarter = "OR = { current_month = 1 current_month = 4 current_month = 7 current_month = 10 }"
    pieces = [f"if = {{ limit = {{ {quarter} }}"]
    pieces.append(_selector("curse", 3))
    pieces.append(_rank_cases(tuple(f"add_stress = {stress}" for stress in (15, 25, 40))))
    pieces.append(_selector("curse", 4))
    expose_body = """clear_saved_scope = xalw_content_exposure
random_secret = { limit = { is_known_by = scope:xalw_content_actor } save_scope_as = xalw_content_exposure }
if = { limit = { exists = scope:xalw_content_exposure } scope:xalw_content_exposure = { expose_secret = scope:xalw_content_actor } }
else { $MISSING$ }
"""
    for rank, chance, stress in ((1, 20, 15), (2, 35, 25), (3, 50, 40)):
        body = expose_body.replace("$MISSING$", f"add_stress = {stress}").replace("else {", "else = {")
        pieces.append(f"if = {{ limit = {{ var:xalw_content_rank = {rank} }} " + _annual_reset("exposure") + f"\nif = {{ limit = {{ var:xalw_content_exposure_count < 2 }} random = {{ chance = {chance} change_variable = {{ name = xalw_content_exposure_count add = 1 }}\n{body}\n}} }} }}")
    pieces.append(_selector("curse", 8))
    for rank, chance, control, opinion, stress in ((1, 25, 10, 15, 15), (2, 40, 20, 30, 25), (3, 60, 35, 50, 40)):
        pieces.append(f"if = {{ limit = {{ var:xalw_content_rank = {rank} }}\n" + _annual_reset("realm") + f"""
if = {{ limit = {{ var:xalw_content_realm_count < 2 }} random = {{ chance = {chance}
change_variable = {{ name = xalw_content_realm_count add = 1 }}
if = {{ limit = {{ any_held_title = {{ tier = tier_county }} }}
random_held_title = {{ limit = {{ tier = tier_county }}
change_county_control = -{control}
add_county_modifier = {{ modifier = xalw_content_realm_{rank}_modifier years = 2 }}
}} }} else = {{ add_stress = {stress} }}
}} }} }}""")
    pieces.append("every_character_artifact = { limit = { is_equipped = yes xalw_is_living_trigger = yes NOT = { has_variable = xalw_content_runaway_cooldown } } save_scope_as = xalw_content_runaway_item")
    for slot in range(1, 3):
        for rank, chance, stress in ((1, 10, 20), (2, 20, 35), (3, 35, 60)):
            condition = _slot_condition("curse", slot, f"var:xalw_curse_{slot} = 5 var:xalw_curse_rank_{slot} = {rank}")
            pieces.append(f"""if = {{ limit = {{ {condition} }} random = {{ chance = {chance}
clear_saved_scope = xalw_content_runaway_recipient
scope:xalw_content_actor = {{ random_courtier = {{ limit = {{ is_alive = yes is_adult = yes is_imprisoned = no }} save_scope_as = xalw_content_runaway_recipient }} }}
scope:xalw_content_actor = {{ add_stress = {stress} }}
if = {{ limit = {{ exists = scope:xalw_content_runaway_recipient }}
set_variable = {{ name = xalw_content_runaway_cooldown value = yes years = 3 }}
set_owner = scope:xalw_content_runaway_recipient
}}
}} }}""")
    pieces.append("}\n}")
    pieces.append(_selector("curse", 6))
    pieces.append(_annual_reset("lover"))
    pieces.append("""if = { limit = { var:xalw_content_rank > 0 var:xalw_content_lover_count = 0 }
set_variable = { name = xalw_content_lover_count value = 1 }
every_spouse = { limit = { is_alive = yes } add_to_list = xalw_content_partners }
every_relation = { type = lover limit = { is_alive = yes NOT = { any_in_list = { list = xalw_content_partners this = prev } } } add_to_list = xalw_content_partners }
if = { limit = { any_in_list = { list = xalw_content_partners always = yes } }
set_variable = { name = xalw_content_partner_remaining value = var:xalw_content_rank }
while = { limit = { var:xalw_content_partner_remaining > 0 any_in_list = { list = xalw_content_partners NOT = { has_variable = xalw_content_partner_selected } } }
random_in_list = { list = xalw_content_partners limit = { NOT = { has_variable = xalw_content_partner_selected } }
set_variable = { name = xalw_content_partner_selected value = yes days = 1 }
""" + "\n".join(
        f"if = {{ limit = {{ scope:xalw_content_actor.var:xalw_content_rank = {rank} }} add_opinion = {{ target = scope:xalw_content_actor modifier = xalw_content_opinion_minus_{amount}_2y }} }}"
        for rank, amount in ((1, 15), (2, 30), (3, 50))
    ) + "\n}\nchange_variable = { name = xalw_content_partner_remaining add = -1 }\n}\n}\nelse = {\n" + _rank_cases(tuple(f"add_stress = {stress}" for stress in (20, 35, 60))) + "\n}\n}")
    return "\n".join(pieces)


def _render_rust_monthly() -> str:
    entries: list[str] = ["save_scope_as = xalw_content_rust_item", "set_variable = { name = xalw_content_rust_rank value = 0 }"]
    for slot in range(1, 3):
        condition = _slot_condition("curse", slot, f"var:xalw_curse_{slot} = 7")
        entries.append(f"if = {{ limit = {{ {condition} }} set_variable = {{ name = xalw_content_rust_rank value = var:xalw_curse_rank_{slot} }} }}")
    entries.append("if = { limit = { var:xalw_content_rust_rank > 0 }")
    for rank, chance, cost, stress in ((1, 30, 5, 15), (2, 60, 10, 25), (3, 100, 15, 40)):
        pay = f"set_variable = {{ name = xalw_content_recovery_quote value = {cost} }}\n" + _bounded_payment("xalw_content_recovery_quote", "")
        recovered = _present_condition(("xalw_content_last_equipped_durability",), "artifact_durability > var:xalw_content_last_equipped_durability")
        entries.append(f"""if = {{ limit = {{ var:xalw_content_rust_rank = {rank} {recovered} NOT = {{ var:xalw_content_recovery_year ?= current_year }} }}
random = {{ chance = {chance}
set_variable = {{ name = xalw_content_recovery_year value = current_year }}
scope:xalw_content_actor = {{ {pay}\nadd_stress = {stress} }}
}} }}""")
    for rank, loss in ((1, 2), (2, 4), (3, 7)):
        entries.append(f"if = {{ limit = {{ var:xalw_content_rust_rank = {rank} }} add_durability = -{loss} }}")
    entries.append("""if = { limit = { artifact_durability > 0 } set_variable = { name = xalw_content_last_equipped_durability value = artifact_durability } }
else = { add_to_list = xalw_content_broken_items }
}""")
    return "every_character_artifact = { limit = { is_equipped = yes xalw_is_living_trigger = yes }\n" + "\n".join(entries) + "\n}\nevery_in_list = { list = xalw_content_broken_items scope:xalw_content_actor = { destroy_artifact = prev } }"


def _artifact_projection() -> str:
    pieces: list[str] = ["set_variable = { name = xalw_content_fickle_rank value = 0 }", "set_variable = { name = xalw_content_runaway_rank value = 0 }"]
    for slot in range(1, 3):
        for rank in range(1, 4):
            for kind in ("blood", "control", "secrecy", "spouse"):
                pieces.append(f"remove_artifact_modifier = xalw_content_{kind}_{slot}_{rank}_modifier")
        for number, kind in ((1, "blood"), (8, "control"), (4, "secrecy"), (6, "spouse")):
            for rank in range(1, 4):
                condition = _slot_condition("curse", slot, f"var:xalw_curse_{slot} = {number} var:xalw_curse_rank_{slot} = {rank}")
                pieces.append(f"if = {{ limit = {{ {condition} }} add_artifact_modifier = xalw_content_{kind}_{slot}_{rank}_modifier }}")
        for number, cache in ((3, "fickle"), (5, "runaway")):
            condition = _slot_condition("curse", slot, f"var:xalw_curse_{slot} = {number}")
            pieces.append(f"if = {{ limit = {{ {condition} }} set_variable = {{ name = xalw_content_{cache}_rank value = {{ value = var:xalw_content_{cache}_rank max = 3 min = var:xalw_curse_rank_{slot} }} }} }}")
    for disabled in range(1, 4):
        entries: list[str] = []
        eligible: list[str] = []
        for slot in range(1, 7):
            no_duplicate = " ".join(f"NOT = {{ var:xalw_content_disabled_{other} ?= {slot} }}" for other in range(1, 4))
            test = _slot_condition("affix", slot, f"var:xalw_affix_{slot} > 0 {no_duplicate}")
            eligible.append(f"AND = {{ {test} }}")
            entries.append(f"1 = {{ trigger = {{ {test} }} set_variable = {{ name = xalw_content_disabled_{disabled} value = {slot} }} }}")
        pieces.append(f"if = {{ limit = {{ is_equipped = yes var:xalw_content_fickle_rank >= {disabled} NOT = {{ has_variable = xalw_content_disabled_{disabled} }} OR = {{ {' '.join(eligible)} }} }} random_list = {{ {' '.join(entries)} }} }}")
    pieces.append("if = { limit = { var:xalw_content_fickle_rank = 0 } " + " ".join(f"remove_variable = xalw_content_disabled_{i}" for i in range(1, 4)) + " }")
    for feature, number in (("ink", 10), ("prima", 12)):
        pieces.append(f"set_variable = {{ name = xalw_content_{feature}_effective_rank value = 0 }}")
        for slot in range(1, 7):
            disabled_slots_text = " ".join(f"var:xalw_content_disabled_{i} ?= {slot}" for i in range(1, 4))
            slot_condition = _slot_condition("affix", slot, f"var:xalw_affix_{slot} = {number}")
            feature_condition = _present_condition((f"xalw_content_{feature}_active", f"xalw_content_{feature}_rank", f"xalw_content_{feature}_slot"), f"var:xalw_content_{feature}_slot = {slot} {slot_condition}")
            pieces.append(f"""if = {{ limit = {{ {feature_condition} }}
set_variable = {{ name = xalw_content_{feature}_effective_rank value = var:xalw_content_{feature}_rank }}
if = {{ limit = {{ OR = {{ {disabled_slots_text} }} }} set_variable = {{ name = xalw_content_{feature}_effective_rank value = 0 }} }}
else_if = {{ limit = {{ var:xalw_content_jealous_slot ?= {slot} }} change_variable = {{ name = xalw_content_{feature}_effective_rank add = -1 }} }}
}}""")
        for rank in range(1, 4):
            for scale in range(4):
                name = f"xalw_content_{feature}_{rank}_{scale}_modifier"
                pieces.append(f"remove_artifact_modifier = {name}")
                pieces.append(f"if = {{ limit = {{ var:xalw_content_{feature}_effective_rank = {rank} var:xalw_content_runaway_rank = {scale} }} add_artifact_modifier = {name} }}")
    for power in range(1, 7):
        for scale in range(4):
            pieces.append(f"remove_artifact_modifier = xalw_content_echo_{power}_{scale}_modifier")
            slots = " ".join(_slot_condition("affix", slot, f"var:xalw_content_echo_slot ?= {slot} var:xalw_affix_{slot} = 2 NOR = {{ " + " ".join(f"var:xalw_content_disabled_{i} ?= {slot}" for i in range(1, 4)) + " }") for slot in range(1, 7))
            echo_condition = _present_condition(("xalw_content_echo_active", "xalw_content_echo_power"), f"var:xalw_content_echo_power = {power} var:xalw_content_runaway_rank = {scale} OR = {{ {slots} }}")
            pieces.append(f"if = {{ limit = {{ {echo_condition} }} add_artifact_modifier = xalw_content_echo_{power}_{scale}_modifier }}")
    return "\n".join(pieces)


def _bounded_payment(quote_variable: str, on_shortfall: str) -> str:
    return (
        f"set_variable = {{ name = xalw_content_payment value = {{ value = gold min = 0 max = var:{quote_variable} }} }}\n"
        "remove_short_term_gold = var:xalw_content_payment\n"
        f"if = {{ limit = {{ var:xalw_content_payment < var:{quote_variable} }}\n{on_shortfall}\n}}"
    )


def _render_secondary_handlers() -> str:
    perk_body = _rank_cases(tuple(f"add_prestige = -{cost}" for cost in (40, 60, 80))) + """
var:xalw_content_source = {
set_variable = { name = xalw_content_ink_active value = yes days = 365 }
set_variable = { name = xalw_content_ink_rank value = scope:xalw_content_actor.var:xalw_content_rank }
set_variable = { name = xalw_content_ink_slot value = scope:xalw_content_actor.var:xalw_content_slot }
xalw_refresh_artifact_effect = yes
trigger_event = { id = xalw.1000 days = 365 }
}
"""
    perk = _selector("affix", 10) + "\n" + _counted_event("ink", 365, 1, perk_body, True)
    feast_body = _rank_cases(tuple(f"set_variable = {{ name = xalw_content_wine_quote value = {cost} }}" for cost in (10, 15, 20))) + """
if = { limit = { gold >= var:xalw_content_wine_quote }
clear_saved_scope = xalw_content_guest
scope:activity = { random_attending_character = { limit = { is_alive = yes is_adult = yes this != scope:xalw_content_actor NOT = { has_variable = xalw_content_wine_guest_cooldown } } save_scope_as = xalw_content_guest } }
if = { limit = { exists = scope:xalw_content_guest }
remove_short_term_gold = var:xalw_content_wine_quote
""" + _rank_cases(tuple(
        f"scope:xalw_content_guest = {{ add_opinion = {{ target = scope:xalw_content_actor modifier = xalw_content_opinion_plus_{opinion}_2y }} }}"
        for opinion in (10, 15, 20)
    ), "xalw_content_effective_rank") + """
scope:xalw_content_guest = { set_variable = { name = xalw_content_last_wine_host value = scope:xalw_content_actor days = 730 } set_variable = { name = xalw_content_wine_guest_cooldown value = yes days = 730 } }
var:xalw_content_source = { set_variable = { name = xalw_content_feast_guest value = scope:xalw_content_guest days = 365 } }
}
}
"""
    feast = _selector("affix", 3) + "\n" + _counted_event("feast", 180, 2, feast_body, True)
    laughter_reward = _paired_rank(12) + """
if = { limit = { var:xalw_content_combo_rank > 0 var:xalw_content_source = { has_variable = xalw_content_prima_active exists = var:xalw_content_prima_target } }
""" + _rank_cases(tuple(f"add_stress = -{stress}" for stress in (5, 7, 10)), "xalw_content_effective_rank") + "\n" + _rank_cases(tuple(f"add_prestige = -{cost}" for cost in (10, 18, 25))) + """
var:xalw_content_source = {
remove_variable = xalw_content_prima_active
var:xalw_content_prima_target = { remove_variable = xalw_content_jealous_slot xalw_refresh_artifact_effect = yes }
xalw_refresh_artifact_effect = yes
}
} else = {
""" + _rank_cases(tuple(f"add_stress = -{stress}" for stress in (10, 15, 20)), "xalw_content_effective_rank") + "\n" + _rank_cases(tuple(f"add_prestige = -{cost}" for cost in (20, 35, 50))) + "\n}"
    laughter = _selector("affix", 11) + "\n" + _counted_event("laughter", 180, 2, laughter_reward, True)
    hostile = " ".join(f"scheme_type = {key}" for key in ("abduct", "claim_throne", "overthrow_regent", "disbelieve_mandala", "fabricate_hook", "murder", "seize_realm", "steal_back_artifact", "steal_herd", "coup_ceremonial_liege", "celestial_siphon_treasury"))
    alibi = f"if = {{ limit = {{ OR = {{ {hostile} }} }} scheme_target_character ?= {{\n" + _selector("affix", 8) + "\n" + _counted_event("alibi", 365, 1,
        _rank_cases(tuple(f"add_dread = {dread}" for dread in (5, 10, 15)), "xalw_content_effective_rank") + "\n" +
        _rank_cases(tuple(f"add_prestige = -{cost}" for cost in (15, 30, 45))), True) + "\n} }"
    return "\n".join((
        _effect("xalw_content_perk_unlocked_effect", "if = { limit = { is_alive = yes }\n" + perk + "\n}"),
        _effect("xalw_content_feast_completed_effect", "if = { limit = { is_alive = yes }\n" + feast + "\n}"),
        _effect("xalw_content_mental_break_chosen_effect", "if = { limit = { is_alive = yes }\n" + laughter + "\n}"),
        _effect("xalw_content_scheme_discovered_effect", alibi),
    ))


def _render_secret_handlers() -> str:
    memory = "\n".join(
        f"if = {{ limit = {{ scope:xalw_content_actor.var:xalw_content_rank >= {slot} exists = var:xalw_content_secret_{slot - 1} }} set_variable = {{ name = xalw_content_secret_{slot} value = var:xalw_content_secret_{slot - 1} }} }}"
        for slot in (3, 2)
    )
    discover = """save_scope_as = xalw_content_discovered_secret
scope:discoverer ?= {
if = { limit = { is_alive = yes NOT = { has_variable = xalw_content_secret_transfer_guard } }
""" + _selector("affix", 7) + "\n" + _counted_event("secret", 180, 2,
        _rank_cases(tuple(f"add_intrigue_lifestyle_xp = {xp}" for xp in (30, 60, 90)), "xalw_content_effective_rank") + "\nadd_stress = 8\nscope:xalw_content_discovered_secret = { secret_owner ?= { add_opinion = { target = scope:xalw_content_actor modifier = xalw_content_opinion_minus_5_1y } } }\nif = { limit = { var:xalw_content_effective_rank > 0 } var:xalw_content_source = {\n" + memory + """
set_variable = { name = xalw_content_secret_1 value = scope:xalw_content_discovered_secret }
} }
""", True) + "\n} }"
    inherit: list[str] = ["every_character_artifact = { limit = { is_equipped = yes xalw_is_living_trigger = yes has_variable = xalw_content_secret_pending_owner } save_scope_as = xalw_content_inherited_item", "remove_variable = xalw_content_secret_pending_owner", "set_variable = { name = xalw_content_inherited_rank value = 0 }"]
    for slot in range(1, 7):
        disabled = " ".join(f"var:xalw_content_disabled_{i} ?= {slot}" for i in range(1, 4))
        condition = _slot_condition("affix", slot, f"var:xalw_affix_{slot} = 7")
        inherit.append(f"if = {{ limit = {{ {condition} }} set_variable = {{ name = xalw_content_inherited_rank value = var:xalw_affix_rank_{slot} }} if = {{ limit = {{ OR = {{ {disabled} }} }} set_variable = {{ name = xalw_content_inherited_rank value = 0 }} }} else_if = {{ limit = {{ var:xalw_content_jealous_slot ?= {slot} }} change_variable = {{ name = xalw_content_inherited_rank add = -1 }} }} }}")
    inherit.extend(("clear_saved_scope = xalw_content_inherited_secret",))
    for slot in (3, 2, 1):
        available = _present_condition((f"xalw_content_secret_{slot}",), f"var:xalw_content_secret_{slot} ?= {{ NOT = {{ is_known_by = scope:xalw_content_actor }} }}")
        inherit.append(f"if = {{ limit = {{ var:xalw_content_inherited_rank >= {slot} {available} }} var:xalw_content_secret_{slot} = {{ save_scope_as = xalw_content_inherited_secret }} }}")
    for rank, chance in ((1, 20), (2, 35), (3, 50)):
        inherit.append(f"""if = {{ limit = {{ var:xalw_content_inherited_rank = {rank} exists = scope:xalw_content_inherited_secret }}
random = {{ chance = {{ value = {chance}
if = {{ limit = {{ var:xalw_resonance < 40 }} multiply = 0.5 }}
else_if = {{ limit = {{ var:xalw_resonance < 80 }} multiply = 0.75 }}
if = {{ limit = {{ xalw_is_growth_suppressed_trigger = yes }} multiply = 0.5 }}
if = {{ limit = {{ var:xalw_content_fickle_rank ?= 1 }} multiply = 0.75 }}
else_if = {{ limit = {{ var:xalw_content_fickle_rank ?= 2 }} multiply = 0.5 }}
else_if = {{ limit = {{ var:xalw_content_fickle_rank ?= 3 }} multiply = 0.25 }}
}}
scope:xalw_content_actor = {{ set_variable = {{ name = xalw_content_secret_transfer_guard value = yes }} }}
scope:xalw_content_inherited_secret = {{ reveal_to = scope:xalw_content_actor }}
scope:xalw_content_actor = {{ remove_variable = xalw_content_secret_transfer_guard add_stress = 8 }}
if = {{ limit = {{ trigger_if = {{ limit = {{ has_variable = xalw_content_previous_owner }} var:xalw_content_previous_owner ?= {{ is_alive = yes }} }} trigger_else = {{ always = no }} }} var:xalw_content_previous_owner = {{ add_opinion = {{ target = scope:xalw_content_actor modifier = xalw_content_opinion_minus_10_2y }} }} }}
}} }}""")
    inherit.append("}")
    return _effect("xalw_content_secret_discovered_effect", discover) + "\n" + _effect("xalw_content_secret_inheritance_effect", "\n".join(inherit))


def _render_knight_handlers() -> str:
    # A monthly living observation is never represented as death-time prowess.
    memory_body = """clear_saved_scope = xalw_content_fallen_knight
random_in_list = { list = knights limit = { is_alive = no var:xalw_content_observed_liege ?= scope:xalw_content_actor has_variable = xalw_content_observed_prowess } save_scope_as = xalw_content_fallen_knight }
if = { limit = { exists = scope:xalw_content_fallen_knight }
""" + _rank_cases(tuple(f"add_prestige = {xp}" for xp in (30, 60, 90)), "xalw_content_effective_rank") + """
add_stress = 12
if = { limit = { var:xalw_content_effective_rank > 0 } var:xalw_content_source = {
""" + "\n".join(
        f"if = {{ limit = {{ scope:xalw_content_actor.var:xalw_content_rank >= {slot} exists = var:xalw_content_memory_{slot - 1} has_variable = xalw_content_memory_prowess_{slot - 1} }} set_variable = {{ name = xalw_content_memory_{slot} value = var:xalw_content_memory_{slot - 1} }} set_variable = {{ name = xalw_content_memory_prowess_{slot} value = var:xalw_content_memory_prowess_{slot - 1} }} }}"
        for slot in (3, 2)
    ) + """
set_variable = { name = xalw_content_memory_1 value = scope:xalw_content_fallen_knight }
set_variable = { name = xalw_content_memory_prowess_1 value = scope:xalw_content_fallen_knight.var:xalw_content_observed_prowess }
} }
set_variable = { name = xalw_content_survivor_count value = 0 }
every_in_list = { list = knights limit = { is_alive = yes var:xalw_content_observed_liege ?= scope:xalw_content_actor scope:xalw_content_actor.var:xalw_content_survivor_count < 3 }
add_opinion = { target = scope:xalw_content_actor modifier = xalw_content_opinion_minus_5_2y }
scope:xalw_content_actor = { change_variable = { name = xalw_content_survivor_count add = 1 } }
}
}
"""
    fallen = "any_in_list = { list = knights is_alive = no var:xalw_content_observed_liege ?= scope:xalw_content_actor has_variable = xalw_content_observed_prowess }"
    finished = "save_scope_as = xalw_content_actor\nremove_variable = xalw_content_requiem_opportunity\nif = { limit = { is_alive = yes scope:combat_side = { side_commander = scope:xalw_content_actor } }\n"
    combo_memory = memory_body.replace("add_stress = 12", "add_stress = 10").replace("add_opinion = { target = scope:xalw_content_actor modifier = xalw_content_opinion_minus_5_2y }", "# The shared requiem removes the survivor opinion penalty.")
    finished += _annual_reset("dividend") + "\n" + _annual_reset("funeral") + "\n" + _selector("affix", 1)
    finished += "\nremove_variable = xalw_content_victor_item\nif = { limit = { exists = var:xalw_content_source var:xalw_content_effective_rank > 0 } set_variable = { name = xalw_content_victor_item value = var:xalw_content_source } }\n" + _selector("affix", 2)
    same_victor_item = _present_condition(("xalw_content_source", "xalw_content_victor_item"), "var:xalw_content_source = var:xalw_content_victor_item")
    finished += f"\nif = {{ limit = {{ scope:victory = yes {fallen} {same_victor_item} var:xalw_content_effective_rank > 0 NOT = {{ has_variable = xalw_content_dividend_cooldown }} NOT = {{ has_variable = xalw_content_funeral_cooldown }} var:xalw_content_dividend_count < 2 var:xalw_content_funeral_count < 2 }}\n"
    finished += "set_variable = { name = xalw_content_requiem_opportunity value = yes }\n" + _positive_gate("set_variable = { name = xalw_content_dividend_cooldown value = yes days = 90 }\nset_variable = { name = xalw_content_funeral_cooldown value = yes days = 180 }\nchange_variable = { name = xalw_content_dividend_count add = 1 }\nchange_variable = { name = xalw_content_funeral_count add = 1 }\n" + _selector("affix", 1) + "\n" + _rank_cases(tuple(f"add_gold = {gold}" for gold in (5, 10, 15)), "xalw_content_effective_rank") + "\n" + _selector("affix", 2) + "\n" + combo_memory) + "\n}\n"
    finished += _selector("affix", 1) + "\nif = { limit = { scope:victory = yes NOT = { has_variable = xalw_content_requiem_opportunity } }\n" + _counted_event("dividend", 90, 2,
        _rank_cases(tuple(f"add_gold = {gold}" for gold in (10, 20, 30)), "xalw_content_effective_rank") + "\nadd_stress = 8", True) + "\n}\n"
    finished += _selector("curse", 1) + "\nif = { limit = { scope:victory = yes }\n" + _counted_event("blood", 90, 4, _rank_cases(tuple(f"add_stress = {stress}" for stress in (15, 25, 40))), False) + "\n}\n"
    finished += _selector("affix", 2) + f"\nif = {{ limit = {{ {fallen} NOT = {{ has_variable = xalw_content_requiem_opportunity }} }}\n" + _counted_event("funeral", 180, 2, memory_body, True) + "\n}\n}"
    memory_conditions = tuple(_present_condition((f"xalw_content_memory_{slot}", f"xalw_content_memory_prowess_{slot}"), f"var:xalw_content_memory_{slot} ?= {{ is_alive = no }}") for slot in range(1, 4))
    available_memories = " ".join(f"AND = {{ scope:xalw_content_actor.var:xalw_content_effective_rank >= {slot} {condition} }}" for slot, condition in enumerate(memory_conditions, start=1))
    choose_memory = "random_list = {\n" + "\n".join(f"1 = {{ trigger = {{ var:xalw_content_effective_rank >= {slot} var:xalw_content_source = {{ {condition} }} }} set_variable = {{ name = xalw_content_echo_memory_slot value = {slot} }} set_variable = {{ name = xalw_content_echo_power value = {{ value = var:xalw_content_source.var:xalw_content_memory_prowess_{slot} multiply = 0.25 round = yes min = 0 }} }} }}" for slot, condition in enumerate(memory_conditions, start=1)) + "\n}"
    has_memory = _present_condition(("xalw_content_source",), f"var:xalw_content_source = {{ OR = {{ {available_memories} }} }}")
    duel = _selector("affix", 2) + f"\nif = {{ limit = {{ var:xalw_content_effective_rank > 0 {has_memory} }}\n" + _positive_gate(choose_memory + "\n" + _rank_cases(tuple(f"set_variable = {{ name = xalw_content_echo_power value = {{ value = var:xalw_content_echo_power max = {cap} }} }}" for cap in (2, 4, 6)), "xalw_content_effective_rank") + "\n" + "\n".join(
        f"if = {{ limit = {{ var:xalw_content_echo_power = {power} }} var:xalw_content_source = {{ set_variable = {{ name = xalw_content_echo_power value = {power} }} set_variable = {{ name = xalw_content_echo_slot value = scope:xalw_content_actor.var:xalw_content_slot }} set_variable = {{ name = xalw_content_echo_active value = yes days = 30 }} xalw_refresh_artifact_effect = yes trigger_event = {{ id = xalw.1002 days = 30 }} }} }}" for power in range(1, 7)
    ) + """
add_stress = 10
var:xalw_content_source = {
""" + "\n".join(
        f"if = {{ limit = {{ scope:xalw_content_actor.var:xalw_content_echo_memory_slot = {slot} }} remove_variable = xalw_content_memory_{slot} remove_variable = xalw_content_memory_prowess_{slot} }}"
        for slot in (1, 2, 3)
    ) + "\n}") + "\n}"
    cleanup = "every_character_artifact = { limit = { xalw_is_living_trigger = yes } remove_variable = xalw_content_echo_active xalw_refresh_artifact_effect = yes }"
    return "\n".join((_effect("xalw_content_army_finished_effect", finished), _effect("xalw_content_duel_start_effect", duel), _effect("xalw_content_duel_cleanup_effect", cleanup)))


def _render_jealous_monthly() -> str:
    target_slots = " ".join(_slot_condition("affix", slot, f"var:xalw_affix_{slot} > 0") for slot in range(1, 7))
    choose_slot = " ".join(f"1 = {{ trigger = {{ {_slot_condition('affix', slot, f'var:xalw_affix_{slot} > 0')} }} set_variable = {{ name = xalw_content_jealous_slot value = {slot} days = 30 }} }}" for slot in range(1, 7))
    return _selector("affix", 12) + """
save_scope_value_as = { name = xalw_content_previous_month value = { value = xalw_current_month_value subtract = 1 } }
if = { limit = { var:xalw_content_rank > 0 }
clear_saved_scope = xalw_content_jealous_target
random_character_artifact = { limit = { is_equipped = yes xalw_is_living_trigger = yes this != scope:xalw_content_actor.var:xalw_content_source OR = { """ + target_slots + """ } } save_scope_as = xalw_content_jealous_target }
if = { limit = { exists = scope:xalw_content_jealous_target }
""" + _positive_gate("""
var:xalw_content_source = {
if = { limit = { var:xalw_content_prima_target ?= scope:xalw_content_jealous_target
trigger_if = { limit = { has_variable = xalw_content_prima_last_month has_variable = xalw_content_prima_streak }
var:xalw_content_prima_last_month = scope:xalw_content_previous_month
} trigger_else = { always = no } }
change_variable = { name = xalw_content_prima_streak add = 1 }
} else = { set_variable = { name = xalw_content_prima_streak value = 1 } }
set_variable = { name = xalw_content_prima_target value = scope:xalw_content_jealous_target }
set_variable = { name = xalw_content_prima_last_month value = xalw_current_month_value }
set_variable = { name = xalw_content_prima_active value = yes days = 30 }
set_variable = { name = xalw_content_prima_rank value = scope:xalw_content_actor.var:xalw_content_rank }
set_variable = { name = xalw_content_prima_slot value = scope:xalw_content_actor.var:xalw_content_slot }
xalw_refresh_artifact_effect = yes
trigger_event = { id = xalw.1001 days = 30 }
}
scope:xalw_content_jealous_target = {
random_list = { """ + choose_slot + """ }
xalw_refresh_artifact_effect = yes
trigger_event = { id = xalw.1001 days = 30 }
}
""") + "\n}\n}"


def _render_mutation_preference() -> str:
    candidates: list[str] = []
    eligible: list[str] = []
    for slot in range(1, 7):
        matching = " ".join(_slot_condition("affix", other, f"var:xalw_affix_{other} = scope:xalw_content_mutating_item.var:xalw_affix_{slot}") for other in range(1, 7))
        condition = _slot_condition("affix", slot, f"var:xalw_affix_{slot} > 0 var:xalw_content_prima_target = {{ OR = {{ {matching} }} }}")
        eligible.append(condition)
        candidates.append(f"1 = {{ trigger = {{ {condition} }} set_variable = {{ name = xalw_content_preferred_mutation_slot value = {slot} }} }}")
    return """remove_variable = xalw_content_preferred_mutation_slot
save_scope_as = xalw_content_mutating_item
save_scope_value_as = { name = xalw_content_previous_month value = { value = xalw_current_month_value subtract = 1 } }
if = { limit = { is_equipped = yes
trigger_if = { limit = { has_variable = xalw_content_prima_streak has_variable = xalw_content_prima_last_month has_variable = xalw_content_prima_target }
var:xalw_content_prima_streak >= 3 exists = var:xalw_content_prima_target var:xalw_content_prima_last_month >= scope:xalw_content_previous_month
} trigger_else = { always = no } }
set_variable = { name = xalw_content_prima_streak value = 0 }
if = { limit = { OR = { """ + " ".join(eligible) + """ } }
random = { chance = 60 random_list = { """ + " ".join(candidates) + "\n} } } }"


def render_content_effects() -> str:
    """Render the revised native-source contracts; runtime qualification is separate."""
    effects: list[str] = [
        "# Native-source content. Structural checks never replace runtime acceptance.\n",
        _effect("xalw_content_refresh_artifact_effect", _artifact_projection()),
        _effect("xalw_content_on_equip_effect", _artifact_projection()),
        _effect("xalw_content_on_owner_changed_effect", "scope:old_owner ?= { save_scope_as = xalw_content_old_owner }\nif = { limit = { exists = scope:xalw_content_old_owner } set_variable = { name = xalw_content_previous_owner value = scope:xalw_content_old_owner } }\nset_variable = { name = xalw_content_secret_pending_owner value = yes }\nremove_variable = xalw_content_ink_active\nremove_variable = xalw_content_prima_active\nremove_variable = xalw_content_echo_active\n" + _artifact_projection()),
    ]
    monthly = ["# Character root; monthly source is guarded independently of the caller.", "save_scope_as = xalw_content_actor", _render_loan_monthly()]
    monthly.append(_selector("curse", 2))
    appetite: list[str] = []
    for rank, fixed, fraction, stress in ((1, 15, "0.20", 15), (2, 30, "0.35", 25), (3, 50, "0.50", 40)):
        quote = f"set_variable = {{ name = xalw_content_appetite_quote value = {{ value = monthly_character_income min = 0 multiply = {fraction} min = {fixed} round = yes }} }}"
        appetite.append(f"if = {{ limit = {{ var:xalw_content_rank = {rank} }}\n{quote}\n{_bounded_payment('xalw_content_appetite_quote', f'add_stress = {stress}')}\n}}")
    monthly.append("\n".join(appetite))
    validate_references = "every_character_artifact = { limit = { is_equipped = yes xalw_is_living_trigger = yes }\n" + "\n".join(f"if = {{ limit = {{ has_variable = xalw_content_{kind}_{slot} NOT = {{ exists = var:xalw_content_{kind}_{slot} }} }} remove_variable = xalw_content_{kind}_{slot} }}" for kind in ("secret", "memory") for slot in range(1, 4)) + "\n}"
    monthly.extend((_render_curse_calendar(), validate_references, "xalw_content_secret_inheritance_effect = yes", _render_jealous_monthly(), "every_knight = { limit = { is_alive = yes } set_variable = { name = xalw_content_observed_liege value = scope:xalw_content_actor } set_variable = { name = xalw_content_observed_prowess value = prowess } }", _render_rust_monthly()))
    month_body = "\n".join(monthly)
    effects.append(_effect("xalw_content_monthly_effect", f"""if = {{
limit = {{ is_alive = yes NOT = {{ var:xalw_content_month_done ?= xalw_current_month_value }} }}
set_variable = {{ name = xalw_content_month_done value = xalw_current_month_value }}
{month_body}
}}"""))
    effects.append(_render_source_handlers())
    effects.extend((_render_secondary_handlers(), _render_secret_handlers(), _render_knight_handlers()))
    effects.append(_effect("xalw_content_prepare_mutation_effect", _render_mutation_preference()))
    effects.append(_effect("xalw_content_borrower_died_effect", """
if = { limit = { has_variable = xalw_content_loan_periods has_variable = xalw_content_loan_instalment has_variable = xalw_content_loan_arrears has_variable = xalw_content_loan_credit }
set_variable = { name = xalw_content_loan_bad_debt value = { value = var:xalw_content_loan_periods multiply = var:xalw_content_loan_instalment add = var:xalw_content_loan_arrears subtract = var:xalw_content_loan_credit min = 0 } }
}
"""))
    return "\n".join(effects)


def render_content_on_actions() -> str:
    """Only add native hooks whose producers/scopes have been read and recorded."""
    bindings = (
        ("sway_success", "sway_success"),
        ("on_building_completed", "building_completed"),
        ("on_travel_plan_arrival", "arrival"),
        ("on_army_combat_finished", "army_finished"),
        ("on_scheme_discovered", "scheme_discovered"),
        ("on_death", "borrower_died"),
    )
    return "\n".join(
        f"{native} = {{ on_actions = {{ xalw_content_{name} }} }}\n"
        f"xalw_content_{name} = {{ effect = {{ xalw_content_{name}_effect = yes }} }}"
        for native, name in bindings
    ) + "\n"


def render_content_modifiers() -> str:
    """Native artifact modifiers provide immediate engine-managed equip removal."""
    values: list[str] = []
    for slot in range(1, 3):
        for rank, health, control, secrecy, spouse in ((1, "-0.4", "-0.2", -10, -15), (2, "-0.8", "-0.4", -20, -30), (3, "-1.2", "-0.7", -30, -50)):
            values.append(f"xalw_content_blood_{slot}_{rank}_modifier = {{ health = {health} }}")
            values.append(f"xalw_content_control_{slot}_{rank}_modifier = {{ monthly_county_control_growth_add = {control} }}")
            values.append(f"xalw_content_secrecy_{slot}_{rank}_modifier = {{ owned_scheme_secrecy_add = {secrecy} }}")
            values.append(f"xalw_content_spouse_{slot}_{rank}_modifier = {{ spouse_opinion = {spouse} }}")
    for rank in range(1, 4):
        values.append(f"xalw_content_realm_{rank}_modifier = {{ county_opinion_add = {(-15, -30, -50)[rank - 1]} }}")
        for scale, factor in ((0, 1.0), (1, 0.9), (2, 0.8), (3, 0.7)):
            values.append(f"xalw_content_ink_{rank}_{scale}_modifier = {{ monthly_learning_lifestyle_xp_gain_mult = {rank * 0.05 * factor:.4f} }}")
            values.append(f"xalw_content_prima_{rank}_{scale}_modifier = {{ prowess_no_portrait = {int((rank + 1) * factor)} }}")
    for power in range(1, 7):
        for scale, factor in ((0, 1.0), (1, 0.9), (2, 0.8), (3, 0.7)):
            values.append(f"xalw_content_echo_{power}_{scale}_modifier = {{ prowess_no_portrait = {power * factor:.2f} }}")
    return "\n".join(values) + "\n"


def render_content_opinions() -> str:
    """Opinion effects have no invented punishment/crime flags."""
    return "\n".join(
        f"xalw_content_opinion_{'plus' if amount > 0 else 'minus'}_{abs(amount)}_{years}y = {{ opinion = {amount} years = {years} stacking = no }}"
        for amount in (-50, -30, -15, -10, -5, 5, 10, 15, 20)
        for years in (1, 2)
    ) + "\n"


def render_content_events() -> str:
    """Reserve the assigned event range; no unproved synthetic producer is emitted."""
    return """namespace = xalw
xalw.1000 = {
scope = artifact
hidden = yes
immediate = { xalw_refresh_artifact_effect = yes }
}
xalw.1001 = {
scope = artifact
hidden = yes
immediate = { xalw_refresh_artifact_effect = yes }
}
xalw.1002 = {
scope = artifact
hidden = yes
immediate = { xalw_refresh_artifact_effect = yes }
}
"""


def render_content_localization(language: Language) -> dict[str, str]:
    if language not in ("simp_chinese", "english"):
        raise ValueError(f"Unsupported content language: {language}")
    values: dict[str, str] = {}
    for definition in (*AFFIXES, *CURSES):
        prefix = f"xalw_{definition.kind}_{definition.number}"
        values[f"{prefix}_name"] = definition.chinese_name if language == "simp_chinese" else definition.english_name
        values[f"{prefix}_desc"] = definition.chinese_description if language == "simp_chinese" else definition.english_description
    for slot in range(1, 3):
        for rank in range(1, 4):
            for kind, chinese, english in (("blood", "鲜血什一税", "Blood Tithe"), ("control", "失眠之国", "Unquiet Realm"), ("secrecy", "大嘴巴", "Telltale"), ("spouse", "妒侣", "Jealous Lover")):
                values[f"xalw_content_{kind}_{slot}_{rank}_modifier"] = chinese if language == "simp_chinese" else english
    for rank in range(1, 4):
        values[f"xalw_content_realm_{rank}_modifier"] = "失眠之国：旧日惊扰" if language == "simp_chinese" else "Unquiet Realm: Lasting Disturbance"
        for scale in range(4):
            for feature, chinese, english in (("ink", "墨水成瘾", "Ink Addiction"), ("prima", "嫉妒的首席", "Jealous Prima")):
                values[f"xalw_content_{feature}_{rank}_{scale}_modifier"] = chinese if language == "simp_chinese" else english
    for power in range(1, 7):
        for scale in range(4):
            values[f"xalw_content_echo_{power}_{scale}_modifier"] = "丧钟：死者的回声" if language == "simp_chinese" else "Funeral Choir: Echo of the Fallen"
    for amount in (-50, -30, -15, -10, -5, 5, 10, 15, 20):
        for years in (1, 2):
            values[f"xalw_content_opinion_{'plus' if amount > 0 else 'minus'}_{abs(amount)}_{years}y"] = ("活物留下的好意" if amount > 0 else "活物留下的怨恨") if language == "simp_chinese" else ("Kindness Left by a Living Artifact" if amount > 0 else "Resentment Left by a Living Artifact")
    return values


def get_content_patches(game: Path) -> tuple[SourcePatch, ...]:
    """Return only reviewed literal-SHA source projections; never trust a fresh hash."""
    if not game.is_dir():
        raise ValueError(f"Game source root does not exist: {game}")
    from ck3_text_projection import Block, blocks, digest, normalize

    parsed_blocks: dict[str, tuple[Block, ...]] = {}

    def direct_children(source: str, parent: Block | None) -> tuple[Block, ...]:
        found: list[Block] = []
        boundary_start = parent.opening if parent is not None else -1
        boundary_end = parent.end if parent is not None else len(source) + 1
        all_blocks = parsed_blocks.get(source)
        if all_blocks is None:
            all_blocks = tuple(blocks(source))
            parsed_blocks[source] = all_blocks
        for block in all_blocks:
            if boundary_start < block.start and block.end < boundary_end:
                if not any(item.opening < block.start < item.end for item in found):
                    found.append(block)
        return tuple(found)

    def append_callback(source: str, top: Block, child_key: str, callback: str) -> tuple[int, str]:
        found = [child for child in direct_children(source, top) if child.key == child_key]
        if len(found) > 1:
            raise ValueError(f"Ambiguous production callback {top.key}.{child_key}")
        if found:
            return found[0].end - 1, f"\n\t{callback} = yes\n"
        return top.end - 1, f"\n\t{child_key} = {{ {callback} = yes }}\n"

    patches: list[SourcePatch] = []
    for binding in SOURCE_BINDINGS:
        source = normalize((game / binding.relative_path).read_text(encoding="utf-8-sig"))
        if digest(source) != binding.sha256:
            raise ValueError(f"Content producer changed: {binding.relative_path}")
        inserts: list[tuple[int, str]] = []
        top_blocks = direct_children(source, None)
        if binding.family == "secret":
            inserts.extend(append_callback(source, top, "on_discover", "xalw_content_secret_discovered_effect") for top in top_blocks)
        elif binding.family == "perk":
            inserts.extend(append_callback(source, top, "effect", "xalw_content_perk_unlocked_effect") for top in top_blocks)
        elif binding.family == "feast":
            if len(top_blocks) != 1:
                raise ValueError("Expected a single native feast activity definition")
            inserts.append(append_callback(source, top_blocks[0], "on_complete", "xalw_content_feast_completed_effect"))
        elif binding.family == "stress":
            for top in top_blocks:
                for child in direct_children(source, top):
                    if child.key == "option":
                        inserts.append((child.end - 1, "\n\thidden_effect = { xalw_content_mental_break_chosen_effect = yes }\n"))
        else:
            start_anchor = "# Configure starting bonus/threshold variables."
            if source.count(start_anchor) != 1:
                raise ValueError("Single combat configuration anchor is ambiguous")
            inserts.append((source.index(start_anchor), "scope:sc_attacker = { xalw_content_duel_start_effect = yes }\n\t\tscope:sc_defender = { xalw_content_duel_start_effect = yes }\n\t\t"))
            cleanup = [top for top in top_blocks if top.key == "remove_single_combat_info_effect"]
            if len(cleanup) != 1:
                raise ValueError("Single combat cleanup producer is ambiguous")
            inserts.append((cleanup[0].end - 1, "\n\tscope:sc_attacker = { if = { limit = { is_alive = yes } xalw_content_duel_cleanup_effect = yes } }\n\tscope:sc_defender = { if = { limit = { is_alive = yes } xalw_content_duel_cleanup_effect = yes } }\n"))
        if not inserts:
            raise ValueError(f"No native producers found: {binding.relative_path}")
        projected = source
        for position, addition in sorted(inserts, reverse=True):
            projected = projected[:position] + addition + projected[position:]
        blocks(projected)
        patches.append(SourcePatch(binding.relative_path, binding.sha256, ((source, projected),)))
    return tuple(patches)


@dataclass(frozen=True)
class ContentSourceBinding:
    relative_path: str
    sha256: str
    family: Literal["secret", "perk", "feast", "stress", "duel"]


SOURCE_BINDINGS: tuple[ContentSourceBinding, ...] = (
    ContentSourceBinding("common/activities/activity_types/feast.txt", "948ff37e08fa6426c12d11554785c81b65d4595f5e2f6367afccfa91da3b058d", "feast"),
    ContentSourceBinding("common/secret_types/00_secret_types.txt", "a88dbbd075b1beda99ec15ffb32a7db2d23c49e7ea21798494b6b64cff6f2069", "secret"),
    ContentSourceBinding("common/secret_types/00_bastard_secrets.txt", "f5d8970aa62f2987e57f4808ed694daf4aebb4b0fb94539dba84a00dea3ff14f", "secret"),
    ContentSourceBinding("common/secret_types/dynastic_cycle_secrets.txt", "0033b55f0e0a7f5588d16062545359e1595d13b2f931d2812284b77073954d91", "secret"),
    ContentSourceBinding("common/scripted_effects/00_single_combat_effects.txt", "ad9ea3686167effc327802dffe4091d90d82935a035448fc3bc9ad2ebbb550b9", "duel"),
    ContentSourceBinding("events/stress_events/stress_threshold_events.txt", "a7bbf5307c62fdef9d90f8c591081c8c43d4b763eee57d0e7db7b5d20f9c7138", "stress"),
    ContentSourceBinding("events/stress_events/stress_threshold_prison_events.txt", "377b30d55f3066e25bd73d155259616843833762910819dd60a13ed5de35d14f", "stress"),
    ContentSourceBinding("events/stress_events/stress_threshold_special_events.txt", "5d1061732ba1a2ccdc5a2d279c783f0260842b9095a961b7177514ba3d3ea916", "stress"),
) + tuple(ContentSourceBinding("common/lifestyle_perks/" + name, sha256, "perk") for name, sha256 in (
    ("00_diplomacy_1_foreign_affairs_tree_perks.txt", "698583496ea1d149b23b726ba544176df3f4aa7b8090d171d40a85f7e84cc3a9"),
    ("00_diplomacy_2_majesty_tree_perks.txt", "dc9473b6fb07db890eb62fa6c36e845b8b67a81db870cf72c03c79597fd41bf6"),
    ("00_diplomacy_3_family_tree_perks.txt", "b4f34759b284904ee2ca0374a14642fd62ee645b6737a80ed4a3c2759807376d"),
    ("00_intrigue_1_skulduggery_tree_perks.txt", "33686477df9bee8897c66959d643ac0772ea67f480f795f28b37c32e04f5cb63"),
    ("00_intrigue_2_temptation_tree_perks.txt", "91dd9a6de9f8f88021e434986283f933729efa4713f0be0d1412a192d22b379f"),
    ("00_intrigue_3_intimidation_tree_perks.txt", "b6bbc57ca7809395f12b8423dcbcfcfd7c21d1a383dbbb9c431560d4ce22fd47"),
    ("00_learning_1_medicine_tree_perks.txt", "0b27116205d2d38c68310721be132374032515bf7bb01e309829d0f2255bb9cb"),
    ("00_learning_2_scholarship_tree_perks.txt", "0706135c762ac4d30f214dc33e0fb1d822b140e48ae596c5fa839d922cac4367"),
    ("00_learning_3_theology_tree_perks.txt", "bd65d0caa3f9bf46a3a68ceb939d98074f4306fa7cfecdb73d79e67fb644d14a"),
    ("00_martial_1_strategy_tree_perks.txt", "8ab9fcd47490c3c5ab44e20ef1ae7ee1715e02c6d224be74045dfdaced2fbe85"),
    ("00_martial_2_authority_tree_perks.txt", "de661b047853bbe2e1c74c3d112109adef2cf19b49feb9a5901ed816277069ad"),
    ("00_martial_3_chivalry_tree_perks.txt", "8a69af9665a14049b3828dab99e26fb0abcfe8fa0bf945bbe8b27319c8416cf9"),
    ("00_stewardship_1_wealth_tree_perks.txt", "8038dcc6cd14b31c169cfdde5d8b9ebf4bb76915d5799f341cb86c642d3f83aa"),
    ("00_stewardship_2_domain_tree_perks.txt", "127c28c330ab1028558ee4b114c11982800d6b7465eb532eb56a725f9ec61e9f"),
    ("00_stewardship_3_duty_tree_perks.txt", "d68c34617f297fc558ab19000b0f74a533c44e2a002223cd2d0d3e336f34dd4b"),
    ("00_wanderer_1_surveyor_tree_perks.txt", "772e4aaa28e7a77df42ea38ee77cae6d6b064cdde22b46a2bec5a85d015b1a48"),
    ("00_wanderer_2_wayfarer_tree_perks.txt", "3c9ce5eef3df1949f73ff8299ee31359fe0e4e4954761bcfeb140e0fa89f4e4b"),
    ("00_wanderer_3_voyager_tree_perks.txt", "f1c01f401d55124ef929862323304996432a4cb86dcd72a4dc238b283d04d62e"),
))
