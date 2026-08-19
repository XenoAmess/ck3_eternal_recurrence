# -*- coding: utf-8 -*-
# 奖池生成器：从 pools_data.py 的 100+100 数据表产出全部 GENERATED 文件。
#
#   py tools/gen_pools.py          （在仓库根目录跑；用任意 python3，无三方依赖）
#
# 产出：
#   common/scripted_effects/xar_generated_pools_effects.txt   — 抽取×2 + 发放×2
#   common/customizable_localization/xar_generated_pool_loc.txt — 5 槽位解析器
#   common/modifiers/xar_generated_pool_modifiers.txt          — 池修正定义
#   localization/<lang>/xar_generated_pools_l_<lang>.yml       — 200 键 × 9 语言
#   docs/blessing-curse-pools.md                               — 权威表重写
# 另：从手写 localization/<lang>/xar_l_<lang>.yml 剥掉旧 xar_bless_N/xar_curse_N 键。
#
# 旧手写文件（xar_bless_curse_effects.txt、xar_loc.txt 槽位段、xar_modifiers.txt
# 池修正）由人工删除——见 docs/blessing-curse-pools.md 的实现位置节。

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pools_data import B, C, LANGS, SUM_T, ATTR_WORD, EXTRA_MODIFIERS, EXTRA_MODIFIER_NAMES, WEIGHTS, S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "XenoAmess_s_Eternal_Recurrence")

HEADER = "# GENERATED FILE - do not edit. Regenerate with tools/gen_pools.py\n"
RARITY_ZH = {"c": "普通", "r": "稀有", "l": "传说"}
RARITY_LEVEL = {"c": 0, "r": 1, "l": 2}
RARITY_LABEL = {
    "c": {"simp_chinese": "普通", "english": "Common", "french": "Commun", "german": "Gewöhnlich", "japanese": "一般", "korean": "일반", "polish": "Zwykłe", "russian": "Обычное", "spanish": "Común"},
    "r": {"simp_chinese": "稀有", "english": "Rare", "french": "Rare", "german": "Selten", "japanese": "希少", "korean": "희귀", "polish": "Rzadkie", "russian": "Редкое", "spanish": "Raro"},
    "l": {"simp_chinese": "传说", "english": "Legendary", "french": "Légendaire", "german": "Legendär", "japanese": "伝説", "korean": "전설", "polish": "Legendarne", "russian": "Легендарное", "spanish": "Legendario"},
}
FAMILY_LABEL = {
    "gold": {"simp_chinese": "财富", "english": "Wealth"},
    "prestige": {"simp_chinese": "威望", "english": "Prestige"},
    "piety": {"simp_chinese": "信仰", "english": "Faith"},
    "influence": {"simp_chinese": "权谋", "english": "Influence"},
    "skill": {"simp_chinese": "属性", "english": "Skill"},
    "xp": {"simp_chinese": "生活方式", "english": "Lifestyle"},
    "trait": {"simp_chinese": "特质", "english": "Trait"},
    "mod": {"simp_chinese": "修正", "english": "Modifier"},
    "dynasty": {"simp_chinese": "宗族", "english": "Dynasty"},
    "stress_b": {"simp_chinese": "压力", "english": "Stress"},
    "stress_c": {"simp_chinese": "压力", "english": "Stress"},
    "golddrain": {"simp_chinese": "财富", "english": "Wealth"},
    "custom": {"simp_chinese": "秘契", "english": "Pact"},
}

# Reviewed release localization for generated pool family prefixes.
FAMILY_LABEL_TRANSLATIONS = {'french': {'gold': 'Richesse',
            'prestige': 'Prestige',
            'piety': 'Foi',
            'influence': 'Influence',
            'skill': 'Compétence',
            'xp': 'Mode de vie',
            'trait': 'Trait',
            'mod': 'Modificateur',
            'dynasty': 'Dynastie',
            'stress_b': 'Stress',
            'stress_c': 'Stress',
            'golddrain': 'Richesse',
            'custom': 'Pacte'},
 'german': {'gold': 'Wohlstand',
            'prestige': 'Prestige',
            'piety': 'Glaube',
            'influence': 'Einfluss',
            'skill': 'Fähigkeit',
            'xp': 'Lebensstil',
            'trait': 'Eigenschaft',
            'mod': 'Modifikator',
            'dynasty': 'Dynastie',
            'stress_b': 'Stress',
            'stress_c': 'Stress',
            'golddrain': 'Wohlstand',
            'custom': 'Pakt'},
 'japanese': {'gold': '富',
              'prestige': '威信',
              'piety': '信仰',
              'influence': '影響力',
              'skill': '技能',
              'xp': '生活方式',
              'trait': '特性',
              'mod': '修正',
              'dynasty': '王朝',
              'stress_b': 'ストレス',
              'stress_c': 'ストレス',
              'golddrain': '富',
              'custom': '契約'},
 'korean': {'gold': '재력',
             'prestige': '위신',
             'piety': '신앙',
             'influence': '영향력',
             'skill': '능력치',
             'xp': '생활 방식',
            'trait': '특성',
            'mod': '수정치',
            'dynasty': '왕조',
            'stress_b': '스트레스',
            'stress_c': '스트레스',
            'golddrain': '재력',
            'custom': '계약'},
 'polish': {'gold': 'Bogactwo',
            'prestige': 'Prestiż',
            'piety': 'Wiara',
            'influence': 'Wpływy',
            'skill': 'Umiejętność',
            'xp': 'Styl życia',
            'trait': 'Cecha',
            'mod': 'Modyfikator',
            'dynasty': 'Dynastia',
            'stress_b': 'Stres',
            'stress_c': 'Stres',
            'golddrain': 'Bogactwo',
            'custom': 'Pakt'},
 'russian': {'gold': 'Богатство',
             'prestige': 'Престиж',
             'piety': 'Вера',
             'influence': 'Влияние',
             'skill': 'Навык',
             'xp': 'Образ жизни',
             'trait': 'Черта',
             'mod': 'Модификатор',
             'dynasty': 'Династия',
             'stress_b': 'Стресс',
             'stress_c': 'Стресс',
             'golddrain': 'Богатство',
             'custom': 'Пакт'},
 'spanish': {'gold': 'Riqueza',
             'prestige': 'Prestigio',
             'piety': 'Fe',
             'influence': 'Influencia',
             'skill': 'Habilidad',
             'xp': 'Estilo de vida',
             'trait': 'Rasgo',
             'mod': 'Modificador',
             'dynasty': 'Dinastía',
             'stress_b': 'Estrés',
             'stress_c': 'Estrés',
             'golddrain': 'Riqueza',
             'custom': 'Pacto'}}
for language, labels in FAMILY_LABEL_TRANSLATIONS.items():
    for family, label in labels.items():
        FAMILY_LABEL[family][language] = label

# A visible diagnostic for an impossible slot ID. Resolver keys intentionally
# have no same-named static yml entry: such entries mask SCOPE.Custom at runtime.
POOL_INVALID = {
    "simp_chinese": "#R 奖池索引无效#!",
    "english": "#R INVALID POOL SELECTION#!",
    "french": "#R SÉLECTION DE TABLE INVALIDE#!",
    "german": "#R UNGÜLTIGE POOLAUSWAHL#!",
    "japanese": "#R 無効な抽選結果#!",
    "korean": "#R 잘못된 추첨 결과#!",
    "polish": "#R NIEPRAWIDŁOWY WYBÓR PULI#!",
    "russian": "#R НЕВЕРНЫЙ ВЫБОР ИЗ ПУЛА#!",
    "spanish": "#R SELECCIÓN DE RESERVA NO VÁLIDA#!",
}
SHOP_MODIFIER_NAMES = {
    "xar_free_faith_reformation": {
        "simp_chinese": "无价的宗教改革", "english": "Free Faith Reformation",
        "french": "Réforme religieuse gratuite", "german": "Kostenlose Glaubensreform",
        "japanese": "無償の宗教改革", "korean": "무료 신앙 개혁",
        "polish": "Darmowa reforma wiary", "russian": "Бесплатная реформа веры",
        "spanish": "Reforma religiosa gratuita",
    },
    "lifespan": {
        "simp_chinese": "借来的寿命", "english": "Borrowed Lifespan",
        "french": "Longévité empruntée", "german": "Geliehene Lebenszeit",
        "japanese": "借りた寿命", "korean": "빌린 수명",
        "polish": "Pożyczone życie", "russian": "Одолженная жизнь",
        "spanish": "Vida prestada",
    },
}

FAMILY_ZH = {
    "gold": "遗金系（add_gold）", "prestige": "颂歌系（add_prestige）", "piety": "祷声系（add_piety）",
    "influence": "耳语系（change_influence）", "skill": "馈赠系（六维 add_X_skill）",
    "xp": "残页系（生活方式经验）", "trait": "特质系（add_trait）", "mod": "修正系（10 年 modifier）",
    "dynasty": "宗门系（add_dynasty_prestige）", "stress_b": "抚平系（add_stress 减压）",
    "custom": "特殊/传说",
    "golddrain": "漏金系（月收入修正）", "stress_c": "压契系（add_stress 加压）",
}


def entry_code(pool, entry):
    rarity, family, mag, names = entry[0], entry[1], entry[2], entry[3]
    if family == "gold":
        return f"add_gold = {mag}"
    if family == "prestige":
        return f"add_prestige = {mag}"
    if family == "piety":
        return f"add_piety = {mag}"
    if family == "influence":
        return f"change_influence = {mag}"
    if family in ("skill", "xp"):
        effect, v = mag
        return f"{effect} = {v}"
    if family == "dynasty":
        return f"dynasty ?= {{ add_dynasty_prestige = {mag} }}"
    if family == "golddrain":
        return mag
    if family in ("stress_b", "stress_c"):
        return f"add_stress = {mag}"
    if family in ("trait", "custom"):
        return mag
    if family == "mod":
        mid, fields = mag
        return f"add_character_modifier = {{ modifier = {mid} days = 3650 }}"
    raise ValueError(f"unknown family {family}")


def entry_summary(pool, entry, lang):
    family, mag = entry[1], entry[2]
    effect_to_attr = {
        "add_diplomacy_skill": "dip", "add_martial_skill": "mar", "add_stewardship_skill": "ste",
        "add_intrigue_skill": "int", "add_learning_skill": "lea", "add_prowess_skill": "pro",
        "add_diplomacy_lifestyle_xp": "dip", "add_martial_lifestyle_xp": "mar",
        "add_stewardship_lifestyle_xp": "ste", "add_intrigue_lifestyle_xp": "int",
        "add_learning_lifestyle_xp": "lea",
    }
    if family == "skill":
        effect, v = mag
        return f"{S(v)} {ATTR_WORD[effect_to_attr[effect]][lang]}"
    if family == "xp":
        effect, v = mag
        suffix = {"simp_chinese": "经验", "english": "XP", "french": "XP", "german": "EP", "japanese": "経験値",
                  "korean": "경험치", "polish": "PD", "russian": "опыта", "spanish": "EXP"}[lang]
        attr_word = ATTR_WORD[effect_to_attr[effect]][lang]
        return f"{S(v)} {attr_word}{suffix}" if lang == "simp_chinese" else f"{S(v)} {attr_word} {suffix}"
    if family == "golddrain":
        return entry[4][lang]
    if family == "stress_c":
        return SUM_T["stress_b"][lang](S(mag))
    if family in SUM_T:
        return SUM_T[family][lang](S(mag))
    # trait/mod/custom: 摘要是元组第 5 元素（完整 9 语言 dict）
    return entry[4][lang]


def loc_line(entry, lang):
    names = entry[3]
    s = entry_summary(None, entry, lang)
    rarity = RARITY_LABEL[entry[0]][lang]
    family = FAMILY_LABEL[entry[1]].get(lang, FAMILY_LABEL[entry[1]]["english"])
    # Square brackets are localization commands, not decorative punctuation.
    prefix = f"#high {rarity} - {family}:#! "
    if lang in ("simp_chinese", "japanese"):
        return f"{prefix}{names[lang]}（{s}）"
    return f"{prefix}{names[lang]} ({s})"


def entry_conditions(entry):
    """Hard-filter only entries that would be a complete no-op right now."""
    family = entry[1]
    if family == "trait":
        trait = re.search(r"add_trait\s*=\s*(\w+)", entry_code(None, entry)).group(1)
        ranked = {
            "physique_good_1": ("physique_good_1", "physique_good_2", "physique_good_3"),
            "physique_good_2": ("physique_good_2", "physique_good_3"),
            "physique_good_3": ("physique_good_3",),
            "beauty_good_1": ("beauty_good_1", "beauty_good_2", "beauty_good_3"),
            "beauty_good_2": ("beauty_good_2", "beauty_good_3"),
            "intellect_good_1": ("intellect_good_1", "intellect_good_2", "intellect_good_3"),
            "intellect_good_2": ("intellect_good_2", "intellect_good_3"),
            "physique_bad_1": ("physique_bad_1", "physique_bad_2", "physique_bad_3"),
            "beauty_bad_1": ("beauty_bad_1", "beauty_bad_2", "beauty_bad_3"),
            "beauty_bad_2": ("beauty_bad_2", "beauty_bad_3"),
            "intellect_bad_1": ("intellect_bad_1", "intellect_bad_2", "intellect_bad_3"),
            "intellect_bad_2": ("intellect_bad_2", "intellect_bad_3"),
        }
        blocked = ranked.get(trait, (trait,))
        if len(blocked) == 1:
            return [f"NOT = {{ has_trait = {trait} }}"]
        checks = " ".join(f"has_trait = {item}" for item in blocked)
        return [f"NOT = {{ OR = {{ {checks} }} }}"]
    if family == "mod":
        modifier = entry[2][0]
        return [f"NOT = {{ has_character_modifier = {modifier} }}"]
    if family == "dynasty":
        return ["exists = dynasty"]
    if family == "stress_b":
        return ["stress > 0"]
    code = entry_code(None, entry)
    modifiers = re.findall(r"add_character_modifier\s*=\s*\{\s*modifier\s*=\s*(\w+)", code)
    conditions = [f"NOT = {{ has_character_modifier = {modifier} }}" for modifier in modifiers]
    if "dynasty ?=" in code:
        conditions.append("exists = dynasty")
    return conditions


def entry_weight_modifiers(entry, pool_kind):
    """Small visible-state nudges; rarity remains the dominant weight."""
    family = entry[1]
    rules = {
        "gold": ("gold < 100", 2),
        "golddrain": ("gold > 500", 1.5),
        "piety": ("piety < 100", 2),
        "prestige": ("prestige < 100", 2),
        "stress_b": ("stress >= 50", 2),
        "stress_c": ("stress >= 200", 0.25),
    }
    modifiers = [rules[family]] if family in rules else []
    code = entry_code(None, entry)
    contract_id = None
    if "martial" in code or "prowess" in code:
        contract_id = 1
    elif "intrigue" in code or "diplomacy" in code:
        contract_id = 2
    elif family in ("piety",):
        contract_id = 3
    elif family == "dynasty" or "fertility" in code:
        contract_id = 4
    elif family in ("gold", "golddrain") or "stewardship" in code:
        contract_id = 5
    elif family in ("stress_b", "stress_c"):
        contract_id = 6
    if contract_id:
        modifiers.append((f"global_var:xa_contract_id = {contract_id}",
                          2 if pool_kind == "bless" else 1.5))
    return modifiers


def validate(pool, label):
    assert len(pool) == 100, f"{label}: {len(pool)} != 100"
    counts = {"c": 0, "r": 0, "l": 0}
    for e in pool:
        counts[e[0]] += 1
        assert e[0] in WEIGHTS, e
        assert set(e[3].keys()) == set(LANGS), f"{label} names langs: {e[3]['simp_chinese']}"
        assert entry_code(None, e), e
        for lang in LANGS:
            s = entry_summary(None, e, lang)
            assert s and '"' not in s, f"{label} summary bad: {e[3]['simp_chinese']} {lang}"
            assert '"' not in e[3][lang], f"{label} name has quote: {e[3][lang]}"
    assert counts == {"c": 70, "r": 25, "l": 5}, f"{label} rarity: {counts}"


def write_bom(path, text):
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write(text)


def gen_effects(pool, var_prefix, draw_name, apply_name):
    lines = [HEADER]
    slots = (("a", ()), ("b", ("a",))) if var_prefix == "curse" else (
        ("a", ()), ("b", ("a",)), ("c", ("a", "b")))
    lines.append(f"# Draw: {len(slots)} distinct entries without replacement (weights c=10/r=3/l=1).\n")
    lines.append(f"{draw_name} = {{")
    # First-ever production draws have no historical slot globals. Initialize
    # them to an impossible ID before distinctness triggers read prior slots.
    for slot, _ in slots:
        lines.append(
            f"\tset_global_variable = {{ name = xa_{var_prefix}_{slot} value = -1 }}")
    for slot, prior in slots:
        lines.append("\trandom_list = {")
        for i, e in enumerate(pool):
            conditions = []
            if prior:
                conditions += [f"NOT = {{ global_var:xa_{var_prefix}_{p} = {i} }}" for p in prior]
            conditions += entry_conditions(e)
            # A legendary blessing (level 2) requires at least a rare curse
            # (level 1). Common/rare blessings leave the full curse pool valid.
            if var_prefix == "curse" and e[0] == "c":
                conditions.append("global_var:xa_selected_bless_rarity < 2")
            cond = f"trigger = {{ {' '.join(conditions)} }} " if conditions else ""
            rarity_effect = (
                f" set_global_variable = {{ name = xa_{var_prefix}_{slot}_rarity value = {RARITY_LEVEL[e[0]]} }}"
                if var_prefix == "curse" else "")
            modifiers = "".join(
                f"modifier = {{ factor = {factor} {trigger} }} "
                for trigger, factor in entry_weight_modifiers(e, var_prefix))
            lines.append(
                f"\t\t{WEIGHTS[e[0]]} = {{ {cond}{modifiers}"
                f"set_global_variable = {{ name = xa_{var_prefix}_{slot} value = {i} }}"
                f"{rarity_effect} }}")
        lines.append("\t}")
        # Defensive fallback: applicability must never expose the -1 diagnostic.
        candidates = [i for i, e in enumerate(pool)
                      if not entry_conditions(e) and (var_prefix != "curse" or e[0] != "c")]
        lines.append(f"\tif = {{ limit = {{ global_var:xa_{var_prefix}_{slot} = -1 }}")
        for index, candidate in enumerate(candidates[:len(prior) + 1]):
            keyword = "if" if index == 0 else "else_if"
            distinct = " ".join(
                f"NOT = {{ global_var:xa_{var_prefix}_{p} = {candidate} }}" for p in prior)
            limit = distinct or "always = yes"
            rarity = RARITY_LEVEL[pool[candidate][0]]
            lines.append(f"\t\t{keyword} = {{ limit = {{ {limit} }} set_global_variable = {{ name = xa_{var_prefix}_{slot} value = {candidate} }}")
            if var_prefix == "curse":
                lines.append(f"\t\t\tset_global_variable = {{ name = xa_{var_prefix}_{slot}_rarity value = {rarity} }}")
            lines.append("\t\t}")
        lines.append(f'\t\tdebug_log = "XAR: pool fallback {var_prefix} {slot}"')
        lines.append("\t}")
    lines.append("}\n")
    slot_help = "a/b" if var_prefix == "curse" else "a/b/c"
    lines.append(f"# Apply by slot ($SLOT$ = {slot_help}).")
    lines.append(f"{apply_name} = {{")
    for i, e in enumerate(pool):
        code = entry_code(None, e)
        if var_prefix == "bless":
            code += f"\nset_global_variable = {{ name = xa_selected_bless_rarity value = {RARITY_LEVEL[e[0]]} }}"
        else:
            code += "\nxar_complete_bargain_pair_effect = yes"
        lines.extend([
            "\tif = {",
            f"\t\tlimit = {{ global_var:xa_{var_prefix}_$SLOT$ = {i} }}",
            *[f"\t\t{line}" for line in code.splitlines()],
            "\t\t# XAR_ACCEPTANCE_ONLY_BEGIN",
            "\t\tif = {",
            "\t\t\tlimit = { has_global_variable = xa_scoring_matrix_active }",
            f'\t\t\tdebug_log = "XAR: TEST PASS pool_dispatch_{var_prefix}_{i:03d}"',
            "\t\t}",
            "\t\t# XAR_ACCEPTANCE_ONLY_END",
            "\t}",
        ])
    if var_prefix == "bless":
        lines.append("\tchange_global_variable = { name = xa_bless_session add = 1 }")
        lines.append("\tchange_global_variable = { name = xa_bless_count add = 1 }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def gen_sweep():
    """Self-test sweep: run EVERY pool entry's code inline (no slot vars, no
    counters) so the acceptance runner's error.log scan gets true runtime
    coverage of all 200 branches. Called by xar.0008 before the scripted death."""
    out = ["", "# XAR_ACCEPTANCE_ONLY_BEGIN",
           "# Self-test sweep: every entry applied in sequence (runtime coverage)."]
    out.append("xar_test_sweep_effect = {")
    for pool, prefix in ((B, "bless"), (C, "curse")):
        out.append(f"\t# --- {prefix} pool ---")
        for i, e in enumerate(pool):
            code = entry_code(None, e).replace("\n", "\n\t")
            out.append(f"\t# {i}")
            out.append(f"\t{code}")
    out.append('\tdebug_log = "XAR: TEST sweep complete"')
    out.append("}")
    out.extend(["", "# Production dispatcher reachability for every stable wire ID.",
                "xar_test_dispatcher_sweep_effect = {"])
    for pool, prefix, apply_name in (
            (B, "bless", "xar_apply_blessing_effect"),
            (C, "curse", "xar_apply_curse_effect")):
        out.append(f"\t# --- {prefix} dispatcher ---")
        for i, _ in enumerate(pool):
            out.append(
                f"\tset_global_variable = {{ name = xa_{prefix}_a value = {i} }}")
            out.append(f"\t{apply_name} = {{ SLOT = a }}")
    out.append('\tdebug_log = "XAR: TEST PASS pool_dispatch_all_200"')
    out.append("}")
    out.append("# XAR_ACCEPTANCE_ONLY_END")
    return "\n".join(out) + "\n"


def gen_custom_loc(pool, prefix):
    out = [HEADER, f"# Option slot resolvers for the {prefix} pool (100 branches each + fallback)."]
    slots = ("a", "b") if prefix == "curse" else ("a", "b", "c")
    for slot in slots:
        out.append(f"xar_{prefix}_slot_{slot} = {{")
        out.append("\ttype = character")
        for i in range(len(pool)):
            out.append(f"\ttext = {{")
            out.append(f"\t\ttrigger = {{ global_var:xa_{prefix}_{slot} = {i} }}")
            out.append(f"\t\tlocalization_key = xar_{prefix}_{i}")
            out.append(f"\t}}")
        out.append("\ttext = { localization_key = xar_pool_invalid fallback = yes }")
        out.append("}")
    return "\n".join(out) + "\n"


def gen_modifiers():
    out = [HEADER, "# Pool modifiers (10-year unless noted; permanents carry no days)."]
    for e in B + C:
        if e[1] == "mod":
            mid, fields = e[2]
            out.append(f"{mid} = {{ {fields} }}")
    for mid, fields in EXTRA_MODIFIERS.items():
        out.append(f"{mid} = {{ {fields} }}")
    return "\n".join(out) + "\n"


def gen_yml(pool, prefix, lang):
    # Event options use ordinary static keys which invoke the dynamic resolver.
    # The resolver keys themselves must not also exist in yml: static loc wins.
    slots = ("a", "b") if prefix == "curse" else ("a", "b", "c")
    lines = [f' xar_{prefix}_option_{slot}:0 "[SCOPE.Custom(\'xar_{prefix}_slot_{slot}\')]"'
             for slot in slots]
    # actual per-entry names resolved by the custom localization
    lines += [f' xar_{prefix}_{i}:0 "{loc_line(e, lang)}"' for i, e in enumerate(pool)]
    return lines


def gen_modifier_yml(lang):
    """Modifier name keys for pool and shop modifiers."""
    lines = []
    for e in B + C:
        if e[1] == "mod":
            mid, _ = e[2]
            lines.append(f' {mid}:0 "{e[3][lang]}"')
    for mid, names in EXTRA_MODIFIER_NAMES.items():
        lines.append(f' {mid}:0 "{names[lang]}"')
    lines.append(
        f' xar_free_faith_reformation:0 "{SHOP_MODIFIER_NAMES["xar_free_faith_reformation"][lang]}"')
    for index in range(1, 51):
        lines.append(f' xar_lifespan_{index:02d}:0 "{SHOP_MODIFIER_NAMES["lifespan"][lang]}"')
    return lines


def gen_doc():
    out = ["# 祝福 / 诅咒奖池（权威表）",
           "",
           "**本文件是奖池的唯一权威定义，由 `tools/gen_pools.py` 从 `tools/pools_data.py` 导出，勿手改。**",
           "",
           "## 规则框架",
           "",
           "- 商店「开始此生」后琉焰卿开启**垂青会**（`xar.0004`）：展示祝福池随机 3 项（无放回）+ 「什么都不要」",
           "- 选中祝福 → 立即发放 → 必须再从诅咒池随机 2 项中选 1（`xar.0005`）；拥有封印时可消耗封印免除本次咒痕",
           "- 两项诅咒的稀有度均不得低于所选祝福稀有度减 1：传说祝福只会抽到稀有/传说诅咒；普通/稀有祝福允许全池",
           "- 每场垂青会恰好**一对祝福/诅咒**；成交或拒绝后散场，**3 年后**（1095 天）琉焰卿再度现身（`xar.0006` 重置会话）",
           "- 每完成一对祝福/诅咒，琉焰之视获得 **1 经验**；每拒绝一次祝福会，**最终结算总分 -1%**（加算，最低为 0）",
           "- 角色死亡 → 结算后进入观察者模式，计时自然作废",
           "",
           "## 数值与稀有度",
           "",
           "- **同类型奖励：祝福量级 = 诅咒量级 × 0.75**（整数类凑整：属性 +3/−4）",
           "- 稀有度：**普通 70 项（权重 10）/ 稀有 25 项（权重 3）/ 传说 5 项（权重 1）**（两池各自）",
           "- 传说诅咒护栏：痛而不毁档——不碰即死/绝育/削头衔",
           "- 金币诅咒只走月收入 drain（1.19 无合规一次性扣金：add_gold 拒负值、remove_gold 已移除）",
           ""]
    for pool, prefix, title in ((B, "bless", "祝福池"), (C, "curse", "诅咒池")):
        out.append(f"## {title}（100 项）")
        out.append("")
        out.append("| 稳定 ID | wire id | 稀有度 | 标签 | 名称 | 效果 |")
        out.append("|---|---:|---|---|---|---|")
        for i, e in enumerate(pool):
            code = entry_code(None, e).replace("\n", " + ")
            stable_id = f"{prefix}.{i:03d}"
            out.append(f"| `{stable_id}` | {i} | {RARITY_ZH[e[0]]} | {FAMILY_LABEL[e[1]]['simp_chinese']} | {e[3]['simp_chinese']} | `{code}` |")
        out.append("")
    out += [
        "## 实现位置",
        "",
        "- 数据表：`tools/pools_data.py`（改条目改这里，再跑 `py tools/gen_pools.py`）",
        "- 抽取/发放：`common/scripted_effects/xar_generated_pools_effects.txt`（GENERATED）",
        "- 选项槽文本：`common/customizable_localization/xar_generated_pool_loc.txt`（GENERATED）",
        "- 修正：`common/modifiers/xar_generated_pool_modifiers.txt`（GENERATED）",
        "- loc：`localization/<lang>/xar_generated_pools_l_<lang>.yml`（GENERATED，9 语言；含动态 wrapper + 池条目名 + 修正名）",
        "- 事件：`events/xar_events.txt`（xar.0004 / xar.0005 / xar.0006，手写不变）",
        "- 拒绝扣分：`xar_compute_score_effect` 末尾 ×max(0, 1 - 0.01 × xa_bless_reject_count)",
        ("- 稳定 ID 语义契约：`tools/pool_semantic_contract.sha256`。普通生成不会改它；"
         "只有人工审阅本表与 dispatcher diff 后，才用 "
         "`py tools/validate_static.py --print-pool-contract` 输出的新值更新。"),
    ]
    return "\n".join(out) + "\n"


def strip_old_keys():
    pat = re.compile(r"(?m)^\s*xar_(bless|curse)_\d+:0 .*\r?\n?")
    for lang in LANGS:
        p = os.path.join(MOD, "localization", lang, f"xar_l_{lang}.yml")
        with open(p, "r", encoding="utf-8-sig") as f:
            content = f.read()
        new, n = pat.subn("", content)
        if n:
            with open(p, "w", encoding="utf-8-sig", newline="") as f:
                f.write(new)
        print(f"  stripped {n} old keys from xar_l_{lang}.yml")


def main():
    validate(B, "bless")
    validate(C, "curse")
    print("validated: 100 + 100, rarity 70/25/5 per pool, 9 langs complete")

    write_bom(os.path.join(MOD, "common", "scripted_effects", "xar_generated_pools_effects.txt"),
              gen_effects(B, "bless", "xar_draw_blessings_effect", "xar_apply_blessing_effect")
              + "\n" + gen_effects(C, "curse", "xar_draw_curses_effect", "xar_apply_curse_effect")
              + gen_sweep())
    write_bom(os.path.join(MOD, "common", "customizable_localization", "xar_generated_pool_loc.txt"),
              gen_custom_loc(B, "bless") + "\n" + gen_custom_loc(C, "curse"))
    write_bom(os.path.join(MOD, "common", "modifiers", "xar_generated_pool_modifiers.txt"),
              gen_modifiers())
    for lang in LANGS:
        lines = ([f"l_{lang}:"]
                 + [f' xar_pool_invalid:0 "{POOL_INVALID[lang]}"']
                 + [""]
                 + gen_yml(B, "bless", lang)
                 + [""]
                 + gen_yml(C, "curse", lang)
                 + [""]
                 + gen_modifier_yml(lang))
        write_bom(os.path.join(MOD, "localization", lang, f"xar_generated_pools_l_{lang}.yml"),
                  "\n".join(lines) + "\n")
    write_bom(os.path.join(ROOT, "docs", "blessing-curse-pools.md"), gen_doc())
    print("generated: effects / custom loc / modifiers / 9 yml / doc")

    strip_old_keys()
    print("done")


if __name__ == "__main__":
    main()
