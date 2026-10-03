"""Generate the first playable, player-initiated Confucian content iteration.

This package provides the free-chronology sample. Native reunion/schism probes
remain external until their CK3 semantics have been observed in the game.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content_data import MAIN_RITE_ID, PARENT_FAITH, PRACTICES, SAMPLE_RITES, SAMPLE_TENETS

SOURCE = Path(__file__).resolve().parents[1]
HEADER = "# GENERATED FILE: edit tools/gen_runtime.py and run it again.\n"
STUDY_COOLDOWN_DAYS = 180
SCHOOL_COOLDOWN_DAYS = 365


def encoded(text: str) -> bytes:
    return text.replace("\r\n", "\n").encode("utf-8-sig")


def practice_event_id(index: int) -> str:
    return f"lyd.{100 + index}"


def build_outputs() -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}

    def script(path: str, text: str) -> None:
        outputs[path] = encoded(HEADER + text.strip() + "\n")

    script("common/religion/faith_types/lyd_faiths.txt", f"""
{PARENT_FAITH} = {{
    faith_details = {{
        religion = confucianism_religion
        color = {{ 236 190 85 }}
        icon = jingxue
    }}
    main_rite = {MAIN_RITE_ID}
    historical = no
    # Retain the game's Confucian site set in this iteration.
    eminent_holy_sites = {{ qufu chang_an }}
    holy_sites = {{ luoyang bianliang mount_qingcheng }}
}}
""")
    permitted = " ".join(tenet.script_id for tenet in SAMPLE_TENETS)
    script("history/faiths/lyd_faith_history.txt", f"""
{PARENT_FAITH} = {{
    1.1.1 = {{
        main_rite = {MAIN_RITE_ID}
        permitted = {{ {permitted} }}
    }}
}}
""")
    script("common/scripted_triggers/lyd_player_triggers.txt", """
lyd_is_player_trigger = {
    is_ai = no
    is_landed = yes
    is_alive = yes
    is_adult = yes
}
lyd_can_enter_trigger = {
    lyd_is_player_trigger = yes
    faith = { religion = religion:confucianism_religion }
    NOT = { has_character_flag = lyd_enabled }
}
lyd_can_use_school_trigger = {
    lyd_is_player_trigger = yes
    has_character_flag = lyd_enabled
    faith = { religion = religion:confucianism_religion }
}
lyd_can_change_school_trigger = {
    lyd_can_use_school_trigger = yes
    NOT = { has_character_flag = lyd_school_cooldown }
}
lyd_can_study_trigger = {
    lyd_can_use_school_trigger = yes
    NOT = { has_character_flag = lyd_study_cooldown }
}
""")
    script("common/scripted_effects/lyd_entry_effects.txt", f"""
lyd_enter_effect = {{
    if = {{
        limit = {{ lyd_can_enter_trigger = yes }}
        set_character_rite = rite:{MAIN_RITE_ID}
        add_character_flag = lyd_enabled
        trigger_event = lyd.1
    }}
}}
lyd_open_school_effect = {{
    if = {{
        limit = {{ lyd_can_change_school_trigger = yes }}
        trigger_event = lyd.10
    }}
}}
lyd_open_study_effect = {{
    if = {{
        limit = {{ lyd_can_study_trigger = yes }}
        {' '.join(f'if = {{ limit = {{ rite = rite:{p.rite_id} }} trigger_event = {practice_event_id(i)} }}' for i, p in enumerate(PRACTICES))}
    }}
}}
""")
    school_effects = []
    for rite in SAMPLE_RITES:
        school_effects.append(f"""
lyd_adopt_{rite.slug}_effect = {{
    if = {{
        limit = {{ lyd_can_change_school_trigger = yes NOT = {{ rite = rite:{rite.script_id} }} }}
        set_character_rite = rite:{rite.script_id}
        add_character_flag = {{ flag = lyd_school_cooldown days = {SCHOOL_COOLDOWN_DAYS} }}
    }}
}}
""")
    script("common/scripted_effects/lyd_school_effects.txt", "".join(school_effects))
    practice_effects: list[str] = []
    for practice in PRACTICES:
        for option in practice.options:
            mutations = []
            for field, value in (("add_gold", -option.gold_cost), ("add_piety", option.piety_change),
                                 ("add_prestige", option.prestige_change), ("change_stress", option.stress_change),
                                 ("add_learning_lifestyle_xp", option.learning_xp)):
                if value:
                    mutations.append(f"{field} = {value}")
            practice_effects.append(f"""
{practice.script_id}_{option.key}_effect = {{
    if = {{
        limit = {{
            lyd_can_study_trigger = yes
            rite = rite:{practice.rite_id}
            gold >= {option.gold_cost}
        }}
        {' '.join(mutations)}
        add_character_flag = {practice.completion_flag}
        add_character_flag = {{ flag = lyd_study_cooldown days = {STUDY_COOLDOWN_DAYS} }}
    }}
}}
""")
    for index in range(0, len(practice_effects), 8):
        script(f"common/scripted_effects/lyd_practice_{index // 8 + 1}_effects.txt", "".join(practice_effects[index:index + 8]))

    def decision(identifier: str, gate: str, effect: str, extra: str = "") -> str:
        return f"""
{identifier} = {{
    desc = {identifier}_desc
    selection_tooltip = {identifier}_tooltip
    confirm_text = {identifier}_confirm
    is_shown = {{ lyd_is_player_trigger = yes {gate} }}
    is_valid = {{ {gate} {extra} }}
    effect = {{ {effect} = yes }}
    ai_will_do = {{ base = 0 }}
}}
"""
    sample_gate = "OR = { " + " ".join(f"rite = rite:{r.script_id}" for r in SAMPLE_RITES) + " }"
    # Keep disabled decisions visible: the validity panel explains cooldowns.
    script("common/decisions/lyd_decisions.txt", "".join((
        decision("lyd_enter_decision", "lyd_can_enter_trigger = yes", "lyd_enter_effect"),
        decision("lyd_change_school_decision", "lyd_can_use_school_trigger = yes", "lyd_open_school_effect", "lyd_can_change_school_trigger = yes"),
        decision("lyd_study_decision", "lyd_can_use_school_trigger = yes", "lyd_open_study_effect", f"lyd_can_study_trigger = yes {sample_gate}"),
    )))
    script("common/character_interactions/lyd_interactions.txt", "# No independent NPC interaction entry points in iteration 1.\n")
    events = ["namespace = lyd\n", """
lyd.1 = {
    type = character_event
    title = lyd_welcome_t
    desc = lyd_welcome_desc
    theme = faith
    trigger = { lyd_can_use_school_trigger = yes }
    option = { name = lyd_welcome_continue }
}
lyd.10 = {
    type = character_event
    title = lyd_choose_school_t
    desc = lyd_choose_school_desc
    theme = faith
    trigger = { lyd_can_change_school_trigger = yes }
"""]
    for rite in SAMPLE_RITES:
        events.append(f"""
    option = {{
        name = lyd_adopt_{rite.slug}
        trigger = {{ lyd_can_change_school_trigger = yes NOT = {{ rite = rite:{rite.script_id} }} }}
        custom_tooltip = lyd_adopt_school_tt
        lyd_adopt_{rite.slug}_effect = yes
    }}
""")
    events.append("    option = { name = lyd_cancel }\n}\n")
    for i, practice in enumerate(PRACTICES):
        events.append(f"""
{practice_event_id(i)} = {{
    type = character_event
    title = {practice.script_id}_t
    desc = {practice.script_id}_desc
    theme = faith
    trigger = {{ lyd_can_study_trigger = yes rite = rite:{practice.rite_id} }}
""")
        for option in practice.options:
            events.append(f"""
    option = {{
        name = {practice.script_id}_{option.key}
        trigger = {{ lyd_can_study_trigger = yes gold >= {option.gold_cost} }}
        custom_tooltip = {practice.script_id}_{option.key}_tt
        custom_tooltip = lyd_study_cooldown_tt
        {practice.script_id}_{option.key}_effect = yes
    }}
""")
        events.append("    option = { name = lyd_cancel }\n}\n")
    script("events/lyd_events.txt", "".join(events))

    loc = {
        PARENT_FAITH: ("儒家共宗", "The Confucian Communion"),
        PARENT_FAITH + "_adj": ("儒家共宗", "Confucian Communion"),
        PARENT_FAITH + "_adherent": ("儒者", "Confucian"),
        PARENT_FAITH + "_adherent_plural": ("儒者", "Confucians"),
        PARENT_FAITH + "_desc": ("诸儒以经典、礼仪与修身为共同根基。各家可以同尊先圣而解释天、性、心与祭礼有别；共宗不要求诸家只存一说。", "The traditions share the classics, ritual and self-cultivation, while differing over Heaven, nature, mind and sacrifice. Communion need not erase their differences."),
        "lyd_enter_decision": ("入儒门，习经礼", "Enter the Confucian Tradition"),
        "lyd_enter_decision_desc": ("立志以经典、礼仪与修身为本，加入儒家共宗，从孔门经礼开始问学。", "Join the Confucian Communion through study, ritual and self-cultivation, beginning with the Kongmen tradition."),
        "lyd_enter_decision_tooltip": ("加入儒家共宗的孔门经礼", "Join the Kongmen rite of the Confucian Communion"),
        "lyd_enter_decision_confirm": ("由我践行", "Begin my practice"),
        "lyd_change_school_decision": ("择师问道", "Seek a Tradition"),
        "lyd_change_school_decision_desc": ("审读诸家经说，选择自己信从的礼仪与学统。", "Examine the teachings and choose a tradition to follow."),
        "lyd_change_school_decision_tooltip": ("选择礼仪与学统", "Choose a rite and tradition"),
        "lyd_change_school_decision_confirm": ("考察诸家", "Examine the teachings"),
        "lyd_study_decision": ("践礼修身", "Practice Ritual and Cultivation"),
        "lyd_study_decision_desc": ("将所学用于祭礼、讲学与日常省察。依自己所从学统决定此次修习的方式。", "Apply your tradition through offerings, teaching and reflection."),
        "lyd_study_decision_tooltip": ("依当前礼仪进行一次修习", "Practice according to your current rite"),
        "lyd_study_decision_confirm": ("躬行所学", "Put learning into practice"),
        "lyd_welcome_t": ("学为君子", "Learning to Cultivate Virtue"),
        "lyd_welcome_desc": ("读经不只是识字，奉祀不只是陈列供品。仁、敬与礼须在日用之间践行。我当问师求义，又将所得反诸自身。", "Reading must extend beyond words, and offerings beyond their display. Humaneness, reverence and ritual are cultivated in everyday conduct. I shall seek understanding and examine myself."),
        "lyd_welcome_continue": ("学而时习之", "Learn and practice regularly"),
        "lyd_choose_school_t": ("诸儒之学", "The Confucian Traditions"),
        "lyd_choose_school_desc": ("同读圣贤之书，诸家所重各有不同：仁与礼、性与教、天与祭、理与心。此番改从学统，当先明其义。", "The traditions emphasize different readings of humaneness, ritual, nature, teaching, Heaven, principle and mind. I must understand a teaching before following it."),
        "lyd_adopt_school_tt": ("改从此礼仪；一年内不能再次择师。", "Adopt this rite. You may seek another tradition after one year."),
        "lyd_study_cooldown_tt": ("完成此次修习后，180 天内不能再次践礼修身。", "Completing this practice prevents another cultivation session for 180 days."),
        "lyd_cancel": ("容我再思", "I will consider this further"),
    }
    for rite in SAMPLE_RITES:
        loc[f"lyd_adopt_{rite.slug}"] = (rite.name_zh, rite.name_en)
    for language, column in (("simp_chinese", 0), ("english", 1)):
        lines = [f"l_{language}:", " # GENERATED FILE: edit tools/gen_runtime.py"]
        for key, value in loc.items():
            escaped = value[column].replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f' {key}:0 "{escaped}"')
        outputs[f"localization/{language}/lyd_runtime_l_{language}.yml"] = encoded("\n".join(lines) + "\n")
    return outputs


def generate_runtime(output_dir: Path = SOURCE, *, check: bool = False) -> list[str]:
    mismatches = []
    for relative, payload in build_outputs().items():
        path = output_dir / relative
        if check:
            if not path.is_file() or path.read_bytes() != payload:
                mismatches.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=SOURCE)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = generate_runtime(args.output_dir, check=args.check)
    if mismatches:
        print("Generated runtime differs: " + ", ".join(mismatches))
        return 1
    print(f"Runtime {'verified' if args.check else 'generated'}: {len(SAMPLE_RITES)} schools, {len(PRACTICES)} practice events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
