"""Authoritative runtime contract for 超人强. No mutable game state here."""

SEX_EXPERIENCE_VARIABLE = "sxad_sex_experience"
SEX_EXPERIENCE_MAXIMUM = 92_233_720_368_547
MINIMUM_AGE = 18
SKILLS = ("diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess")
SKILL_BALANCE_MAXIMUM = 1_000_000
GAME_VERSION = "1.20.0.3"
ROMANCE_SOURCE_SHA256 = "a4a88fa0f36e95e865dcdd077dcb64f5985db1b9a441fcca1795494abda66211"
EXE_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
HOOKS = {
    "had_sex_with_effect": "sxad_record_pair_effect = { PARTNER = scope:had_sex_with_effect_partner }",
    "had_sex_with_unknown_effect": "sxad_record_unknown_effect = yes",
}

ZH = {
    "trait_sxad_sex_experience": "性经验",
    "trait_sxad_sex_experience_desc": "记录启用《超人强》后，模组捕获的明确性行为次数。仅统计在世、18岁及以上角色。双方经验不同，经验较高者从对方一项可转移属性中吸取1个修正点。基础属性保持原值；原版百分比修正和取整继续生效，面板数值不保证每次恰好变化1点。",
    "trait_sxad_sex_experience_character_desc": "启用后累计性经验：#V [SCOPE.ScriptValue('sxad_experience_value')|0]#! 次。\n\n$trait_sxad_sex_experience_desc$",
    "sxad_view_experience_interaction": "查看性经验",
    "sxad_view_experience_interaction_desc": "查看[recipient.GetShortUIName]启用《超人强》后的累计次数和当前属性。查看不会改变经验或属性。",
    "sxad_view_experience_interaction_notification": "查看性经验",
    "sxad_view_experience_interaction_accept_tt": "查看[recipient.GetShortUIName]的性经验记录。",
    "sxad.1.t": "超人强：性经验记录",
    "sxad.1.desc": "[scope:sxad_view_subject.GetShortUIName]启用模组后累计的性经验为 #V [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_experience_value')|0]#! 次。\n\n当前属性：外交 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_diplomacy_value')|0]，军事 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_martial_value')|0]，管理 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_stewardship_value')|0]，谋略 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_intrigue_value')|0]，学识 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_learning_value')|0]，勇武 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_prowess_value')|0]。\n\n本模组累计净修正：外交 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_diplomacy_balance_value')|0]，军事 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_martial_balance_value')|0]，管理 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_stewardship_balance_value')|0]，谋略 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_intrigue_balance_value')|0]，学识 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_learning_balance_value')|0]，勇武 [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_prowess_balance_value')|0]。\n\n只记录模组启用后实际进入原版统一效果的明确性行为，不推算过去经历，也不模拟日常夫妻性生活。已知双方各加1次；匿名对象只给已知一方加1次。行为前经验较高者等概率吸取一项可转移属性的1个修正点；经验相等时不吸取。基础属性保持原值；百分比修正和取整可能使面板变化不是1点。",
    "sxad.1.a": "知道了",
    "sxad_absorbed_skill_modifier": "超人强：吸收属性",
    "sxad_drained_skill_modifier": "超人强：流失属性",
}
EN = {
    "trait_sxad_sex_experience": "Sexual Experience",
    "trait_sxad_sex_experience_desc": "Counts explicit sexual encounters captured after enabling Superman Qiang, for living characters aged 18 or older. When their experience differs, the more experienced partner takes one transferable skill modifier point. Base skills retain their original values; vanilla percentage modifiers and rounding still apply, so the displayed total may not change by exactly one point.",
    "trait_sxad_sex_experience_character_desc": "Recorded sexual experience: #V [SCOPE.ScriptValue('sxad_experience_value')|0]#! encounters.\n\n$trait_sxad_sex_experience_desc$",
    "sxad_view_experience_interaction": "View Sexual Experience",
    "sxad_view_experience_interaction_desc": "View [recipient.GetShortUIName]'s recorded encounters and current skills. Viewing changes neither experience nor skills.",
    "sxad_view_experience_interaction_notification": "View Sexual Experience",
    "sxad_view_experience_interaction_accept_tt": "View [recipient.GetShortUIName]'s sexual experience record.",
    "sxad.1.t": "Superman Qiang: Experience Record",
    "sxad.1.desc": "[scope:sxad_view_subject.GetShortUIName] has #V [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_experience_value')|0]#! recorded encounters since enabling the mod.\n\nCurrent skills: Diplomacy [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_diplomacy_value')|0], Martial [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_martial_value')|0], Stewardship [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_stewardship_value')|0], Intrigue [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_intrigue_value')|0], Learning [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_learning_value')|0], Prowess [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_prowess_value')|0].\n\nNet modifiers accumulated by this mod: Diplomacy [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_diplomacy_balance_value')|0], Martial [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_martial_balance_value')|0], Stewardship [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_stewardship_balance_value')|0], Intrigue [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_intrigue_balance_value')|0], Learning [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_learning_balance_value')|0], Prowess [scope:sxad_view_subject.MakeScope.ScriptValue('sxad_prowess_balance_value')|0].\n\nOnly explicit encounters reaching the vanilla shared effect are counted. Past encounters are not estimated and routine married life is not simulated. Known partners each gain one encounter; anonymous partners add one only to the known character. The partner with more experience before the encounter takes one modifier point from a uniformly selected transferable skill. Equal experience causes no transfer. Base skills retain their original values; percentages and rounding can make the displayed change differ from one point.",
    "sxad.1.a": "Understood",
    "sxad_absorbed_skill_modifier": "Superman Qiang: Absorbed Skill",
    "sxad_drained_skill_modifier": "Superman Qiang: Drained Skill",
}

for _skill in SKILLS:
    ZH[f"sxad_{_skill}_gain_modifier"] = f"$sxad_absorbed_skill_modifier$：${_skill}$"
    ZH[f"sxad_{_skill}_loss_modifier"] = f"$sxad_drained_skill_modifier$：${_skill}$"
    EN[f"sxad_{_skill}_gain_modifier"] = f"$sxad_absorbed_skill_modifier$: ${_skill}$"
    EN[f"sxad_{_skill}_loss_modifier"] = f"$sxad_drained_skill_modifier$: ${_skill}$"
