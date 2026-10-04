"""Authoritative runtime contract for 超人强. No mutable game state here."""
from decimal import Decimal

SEX_EXPERIENCE_VARIABLE = "sxad_sex_experience"
SEX_EXPERIENCE_MAXIMUM = 92_233_720_368_547
MINIMUM_AGE = 18
SKILLS = ("diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess")
TRANSFER_ATTRIBUTES = (*SKILLS, "health")
HEALTH_TRANSFER_AMOUNT = Decimal("0.00075")
HEALTH_DONOR_MINIMUM = Decimal("3.00075")
SKILL_BALANCE_MAXIMUM = 1_000_000
GAME_VERSION = "1.20.0.3"
ROMANCE_SOURCE_SHA256 = "a4a88fa0f36e95e865dcdd077dcb64f5985db1b9a441fcca1795494abda66211"
EXE_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
HOOKS = {
    "had_sex_with_effect": "sxad_record_pair_effect = { PARTNER = scope:had_sex_with_effect_partner }",
    "had_sex_with_unknown_effect": "sxad_record_unknown_effect = yes",
}

def toast_skill_rows() -> str:
    """Two rows of native skill labels, actual totals and signed ledger points."""
    entries = [
        f"@skill_{skill}_icon! ${skill}$ "
        f"[recipient.MakeScope.ScriptValue('sxad_{skill}_value')|0] "
        f"([recipient.MakeScope.ScriptValue('sxad_{skill}_balance_value')|+0])"
        for skill in SKILLS
    ]
    return "  ·  ".join(entries[:3]) + "\n" + "  ·  ".join(entries[3:])


def toast_health_row() -> str:
    return (
        "@health_icon! $game_concept_health$ "
        "[recipient.MakeScope.ScriptValue('sxad_health_value')|5] "
        "([recipient.MakeScope.ScriptValue('sxad_health_balance_value')|+5])"
    )


ZH = {
    "trait_sxad_sex_experience": "性经验",
    "trait_sxad_sex_experience_desc": "已记录的明确性行为次数。",
    "trait_sxad_sex_experience_character_desc": "已记录性经验：#V [SCOPE.ScriptValue('sxad_experience_value')|0]#! 次。",
    "sxad_view_experience_interaction": "查看性经验",
    "sxad_view_experience_interaction_desc": "以通知查看[recipient.GetShortUIName]的性经验与属性。",
    "sxad_view_experience_interaction_notification": "查看性经验",
    "sxad_view_experience_interaction_accept_tt": "查看[recipient.GetShortUIName]的记录。",
    "sxad_view_experience_toast_title": "[recipient.GetShortUIName] · 性经验 #V [recipient.MakeScope.ScriptValue('sxad_experience_value')|0]#! 次",
    "sxad_view_experience_toast_details": toast_skill_rows() + "\n" + toast_health_row() + "\n\n括号内为本模组累计净修正点。",
    "sxad_absorbed_skill_modifier": "超人强：吸收属性",
    "sxad_drained_skill_modifier": "超人强：流失属性",
}
EN = {
    "trait_sxad_sex_experience": "Sexual Experience",
    "trait_sxad_sex_experience_desc": "Recorded explicit sexual encounters.",
    "trait_sxad_sex_experience_character_desc": "Recorded sexual experience: #V [SCOPE.ScriptValue('sxad_experience_value')|0]#! encounters.",
    "sxad_view_experience_interaction": "View Sexual Experience",
    "sxad_view_experience_interaction_desc": "Show [recipient.GetShortUIName]'s sexual experience and skills in a notification.",
    "sxad_view_experience_interaction_notification": "View Sexual Experience",
    "sxad_view_experience_interaction_accept_tt": "View [recipient.GetShortUIName]'s record.",
    "sxad_view_experience_toast_title": "[recipient.GetShortUIName] · Sexual Experience #V [recipient.MakeScope.ScriptValue('sxad_experience_value')|0]#!",
    "sxad_view_experience_toast_details": toast_skill_rows() + "\n" + toast_health_row() + "\n\nParentheses show this mod's accumulated net modifier points.",
    "sxad_absorbed_skill_modifier": "Superman Qiang: Absorbed Skill",
    "sxad_drained_skill_modifier": "Superman Qiang: Drained Skill",
}

for _skill in TRANSFER_ATTRIBUTES:
    _label = "game_concept_health" if _skill == "health" else _skill
    ZH[f"sxad_{_skill}_gain_modifier"] = f"$sxad_absorbed_skill_modifier$：${_label}$"
    ZH[f"sxad_{_skill}_loss_modifier"] = f"$sxad_drained_skill_modifier$：${_label}$"
    EN[f"sxad_{_skill}_gain_modifier"] = f"$sxad_absorbed_skill_modifier$: ${_label}$"
    EN[f"sxad_{_skill}_loss_modifier"] = f"$sxad_drained_skill_modifier$: ${_label}$"
