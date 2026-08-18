#!/usr/bin/env python3
"""Generate production scoring effects and documentation from scoring_data."""

import runpy
from decimal import Decimal
from pathlib import Path

import scoring_data as schema


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
EFFECT_OUTPUT = MOD / "common/scripted_effects/xar_generated_scoring_effects.txt"
DOC_OUTPUT = ROOT / "docs/scoring-rules.md"


def number(value: Decimal) -> str:
    return format(value, "f").rstrip("0").rstrip(".") if "." in format(value, "f") else format(value, "f")


def value_expression(source: str, coefficient: Decimal) -> str:
    result = f"value = global_var:{source}"
    if coefficient != 1:
        result += f" multiply = {number(coefficient)}"
    return f"{{ {result} }}"


def set_global(lines, name, value, indent="\t"):
    lines.extend([
        f"{indent}set_global_variable = {{",
        f"{indent}\tname = {name}",
        f"{indent}\tvalue = {value}",
        f"{indent}}}",
    ])


def generate_effects() -> str:
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_scoring.py",
        "# Production death scoring mechanics generated from tools/scoring_data.py.",
        "# Descendant identity, dynasty, house, and title detection remain in the",
        "# hand-written xar_desc_count_self/xar_descendant_tier_count_effect adapters.",
        "",
        "xar_compute_score_effect = {",
        "\tsave_scope_as = xar_dead",
        "",
        "\t# Attributes.",
    ]
    score_variables = []
    for rule in schema.ATTRIBUTES:
        set_global(lines, f"xa_a_{rule.suffix}", f"{{ value = {rule.source} }}")
        set_global(
            lines,
            f"xa_p_{rule.suffix}",
            value_expression(f"xa_a_{rule.suffix}", rule.coefficient),
        )
        score_variables.append(f"xa_p_{rule.suffix}")

    lines.extend([
        "",
        "\t# Living descendants: same dynasty and same house (extra).",
    ])
    set_global(lines, "xa_a_dyn", "0")
    set_global(lines, "xa_a_hou", "0")
    for rule in schema.DESCENDANT_TITLE_TIERS:
        lines.append(f"\tset_global_variable = {{ name = xa_d_{rule.key} value = 0 }}")
    lines.extend([
        "\tsave_temporary_scope_as = xar_score_dead",
        "\tif = { limit = { exists = dynasty }",
        "\t\tdynasty = { save_temporary_scope_as = xar_score_dyn }",
        "\t}",
        "\tif = { limit = { exists = house }",
        "\t\thouse = { save_temporary_scope_as = xar_score_house }",
        "\t}",
        "\tevery_child = {",
        "\t\teven_if_dead = yes",
        "\t\txar_desc_node_l1 = yes",
        "\t}",
        "\txar_desc_clean_root = yes",
    ])
    set_global(
        lines, "xa_p_dyn",
        value_expression("xa_a_dyn", schema.DYNASTY_DESCENDANT_COEFFICIENT))
    set_global(
        lines, "xa_p_hou",
        value_expression("xa_a_hou", schema.HOUSE_DESCENDANT_COEFFICIENT))
    score_variables.extend(("xa_p_dyn", "xa_p_hou"))

    lines.extend(["", "\t# Resources: floor(log2(value)) times coefficient."])
    for rule in schema.RESOURCES:
        set_global(lines, f"xa_a_{rule.suffix}", f"{{ value = {rule.source} }}")
        lines.append(
            f"\txar_log2_floor_effect = {{ SRC = {rule.source} VAR = xa_l_{rule.suffix} }}")
        set_global(
            lines,
            f"xa_p_{rule.suffix}",
            value_expression(f"xa_l_{rule.suffix}", rule.coefficient),
        )
        score_variables.append(f"xa_p_{rule.suffix}")

    lines.extend(["", "\t# Titles held at death."])
    for rule in schema.HELD_TITLE_TIERS:
        set_global(lines, f"xa_n_{rule.key}", "0")
        lines.extend([
            "\tevery_held_title = {",
            f"\t\tlimit = {{ tier = {rule.tier} }}",
            f"\t\tchange_global_variable = {{ name = xa_n_{rule.key} add = 1 }}",
            "\t}",
        ])
        set_global(
            lines,
            f"xa_p_{rule.key}",
            value_expression(f"xa_n_{rule.key}", rule.coefficient),
        )
        score_variables.append(f"xa_p_{rule.key}")

    lines.extend([
        "",
        "\t# Living descendants by highest held title tier; buckets come from",
        "\t# the same deduplicated traversal used for blood points.",
    ])
    for index, rule in enumerate(schema.DESCENDANT_TITLE_TIERS, 1):
        set_global(
            lines,
            f"xa_p_d{index}",
            value_expression(f"xa_d_{rule.key}", rule.coefficient),
        )
        score_variables.append(f"xa_p_d{index}")

    lines.extend(["", "\t# Realm size (landed only)."])
    for name in ("xa_a_realm", "xa_l_realm", "xa_p_realm"):
        set_global(lines, name, "0")
    lines.extend([
        "\tif = {",
        "\t\tlimit = { is_landed = yes }",
    ])
    set_global(lines, "xa_a_realm", "{ value = realm_size }", "\t\t")
    lines.append("\t\txar_log2_floor_effect = { SRC = realm_size VAR = xa_l_realm }")
    set_global(
        lines,
        "xa_p_realm",
        value_expression("xa_l_realm", schema.REALM_SIZE_COEFFICIENT),
        "\t\t",
    )
    lines.append("\t}")
    score_variables.append("xa_p_realm")

    lines.extend(["", "\t# Selected lifetime contract: incremental behavior progress."])
    set_global(
        lines, "xa_a_contract",
        "{ value = global_var:xa_contract_progress min = 0 max = 10 }")
    set_global(
        lines,
        "xa_p_contract",
        value_expression("xa_a_contract", schema.CONTRACT_PROGRESS_COEFFICIENT),
    )
    score_variables.append("xa_p_contract")

    lines.extend(["", "\t# Absolute subtotal, selected track subtotal, and refusal penalty."])
    set_global(lines, "xa_absolute_score_before_reject", "0")
    for variable in score_variables:
        lines.append(
            ("\tchange_global_variable = { name = xa_absolute_score_before_reject "
             f"add = {{ value = global_var:{variable} }} }}"))
    set_global(lines, "xa_score_before_reject", "{ value = global_var:xa_absolute_score_before_reject }")
    lines.extend([
        "\tif = {",
        "\t\tlimit = { global_var:xa_score_basis = 1 }",
    ])
    set_global(
        lines,
        "xa_score_before_reject",
        ("{ value = global_var:xa_absolute_score_before_reject "
         "subtract = global_var:xa_score_baseline min = 0 }"),
        "\t\t",
    )
    lines.append("\t}")
    set_global(lines, "xa_absolute_score", "{ value = global_var:xa_absolute_score_before_reject }")
    set_global(lines, "xa_run_score", "{ value = global_var:xa_score_before_reject }")
    lines.extend([
        "\tif = {",
        "\t\tlimit = { global_var:xa_bless_reject_count > 0 }",
        "\t\tchange_global_variable = {",
        "\t\t\tname = xa_absolute_score",
        "\t\t\tmultiply = {",
        "\t\t\t\tvalue = 1",
        ("\t\t\t\tsubtract = { value = global_var:xa_bless_reject_count "
         f"multiply = {number(schema.REFUSAL_MULTIPLIER_PER_COUNT)} }}"),
        "\t\t\t\tmin = 0",
        "\t\t\t}",
        "\t\t}",
        "\t\tchange_global_variable = {",
        "\t\t\tname = xa_run_score",
        "\t\t\tmultiply = {",
        "\t\t\t\tvalue = 1",
        ("\t\t\t\tsubtract = { value = global_var:xa_bless_reject_count "
         f"multiply = {number(schema.REFUSAL_MULTIPLIER_PER_COUNT)} }}"),
        "\t\t\t\tmin = 0",
        "\t\t\t}",
        "\t\t}",
        "\t}",
        "\txar_quantize_record_candidate_effect = yes",
        "",
        "\t# Quantized record and delta.",
        "\tif = {",
        "\t\tlimit = { NOT = { has_global_variable = xa_global_record_imported } }",
        "\t\tset_global_variable = { name = xa_global_record_imported value = 0 }",
        "\t}",
    ])
    set_global(lines, "xa_old_record", "{ value = global_var:xa_global_record_imported }")
    set_global(
        lines,
        "xa_score_delta",
        "{ value = global_var:xa_record_candidate subtract = global_var:xa_old_record }",
    )
    lines.extend(["}", ""])

    lines.extend([
        "# Parameterized floor(log2($SRC$)) into global var $VAR$.",
        "xar_log2_floor_effect = {",
        "\tset_global_variable = { name = $VAR$ value = 0 }",
    ])
    for exponent in range(1, schema.LOG2_MAX_EXPONENT + 1):
        lines.extend([
            "\tif = {",
            f"\t\tlimit = {{ $SRC$ >= {2 ** exponent} }}",
            "\t\tchange_global_variable = { name = $VAR$ add = 1 }",
            "\t}",
        ])
    lines.extend(["}", ""])

    lines.extend([
        "# Mechanical depth expansion around the hand-written descendant adapter.",
    ])
    for depth in range(1, schema.DESCENDANT_DEPTH + 1):
        lines.extend([
            f"xar_desc_node_l{depth} = {{",
            "\txar_desc_count_self = yes",
        ])
        if depth < schema.DESCENDANT_DEPTH:
            lines.extend([
                "\tevery_child = {",
                "\t\teven_if_dead = yes",
                f"\t\txar_desc_node_l{depth + 1} = yes",
                "\t}",
            ])
        lines.extend(["}", ""])
    lines.extend([
        "xar_desc_clean_root = {",
        "\tevery_child = {",
        "\t\teven_if_dead = yes",
        "\t\txar_desc_clean_l1 = yes",
        "\t}",
        "}",
        "",
    ])
    for depth in range(1, schema.DESCENDANT_DEPTH + 1):
        lines.extend([
            f"xar_desc_clean_l{depth} = {{",
            "\tif = {",
            "\t\tlimit = { is_alive = yes }",
            "\t\tremove_character_flag = xar_desc_counted",
            "\t}",
        ])
        if depth < schema.DESCENDANT_DEPTH:
            lines.extend([
                "\tevery_child = {",
                "\t\teven_if_dead = yes",
                f"\t\txar_desc_clean_l{depth + 1} = yes",
                "\t}",
            ])
        lines.extend(["}", ""])
    return "\n".join(lines)


def record_cap() -> int:
    namespace = runpy.run_path(str(MOD / "tools/gen_highscore.py"))
    return namespace["THRESHOLDS"][-1]


def generate_doc() -> str:
    lines = [
        "<!-- GENERATED FILE - do not edit. Regenerate with tools/gen_scoring.py -->",
        "# 算分规则（完整版）",
        "",
        "死亡时（`on_death`）结算当局分数。所有 `log₂` 均**向下取整**（生成的幂阶梯实现）。",
        "实现本体：`common/scripted_effects/xar_generated_scoring_effects.txt`（`xar_compute_score_effect`）。",
        "",
        "## 属性",
        "",
        "| 条目 | 计分 |",
        "|---|---|",
    ]
    lines.extend(f"| {rule.label} | 每 1 点 = {number(rule.coefficient)} 分 |"
                 for rule in schema.ATTRIBUTES)
    lines.extend([
        "",
        "## 血脉（仅限你的后代，须在世）",
        "",
        "| 条目 | 计分 |",
        "|---|---|",
        f"| 每个在世的宗族成员（且为你后代） | {number(schema.DYNASTY_DESCENDANT_COEFFICIENT)} 分 |",
        ("| 每个在世的家族成员（且为你后代） | 额外 "
         f"{number(schema.HOUSE_DESCENDANT_COEFFICIENT)} 分（与宗族叠加） |"),
        "",
        (f"后代判定从死者的 `every_child` 向下展开 {schema.DESCENDANT_DEPTH} 代；遍历包含"
          "已故中间节点，但只有在世后代得分。死亡结算用临时 flag 去重并在结算后清理。"
          "特质 hover 的只读 script value "
         "不能写 flag，因此按最短血缘路径去重，同深度路径优先父系；近亲谱系下仍与结算保持同一人只计一次。"),
        "",
        "## 资源（log₂ 向下取整后乘系数）",
        "",
        "| 条目 | 计分 |",
        "|---|---|",
    ])
    lines.extend(
        f"| {rule.label} | ⌊log₂({rule.label})⌋ × {number(rule.coefficient)} |"
        for rule in schema.RESOURCES)
    lines.extend([
        "",
        "## 死时持有头衔（每个头衔按档位计）",
        "",
        "| 档位 | 每个 |",
        "|---|---|",
    ])
    lines.extend(f"| {rule.label} | {number(rule.coefficient)} 分 |"
                 for rule in schema.HELD_TITLE_TIERS)
    lines.extend([
        "",
        "## 后代成就（每个在世后代按其最高头衔档位计，只计最高档一次）",
        "",
        "| 档位 | 每人 |",
        "|---|---|",
    ])
    lines.extend(f"| {rule.label} | {number(rule.coefficient)} 分 |"
                 for rule in schema.DESCENDANT_TITLE_TIERS)
    lines.extend([
        "",
        (f"后代沿 `every_child` 展开 {schema.DESCENDANT_DEPTH} 代，与血脉分共用同一去重遍历；"
         "同一后代只按最高头衔计一次，无头衔不计分。"),
        "",
        "## 领地（仅有地角色）",
        "",
        "| 条目 | 计分 |",
        "|---|---|",
        ("| 领地规模（realm_size，含封臣伯爵领数） | ⌊log₂(realm_size)⌋ × "
         f"{number(schema.REALM_SIZE_COEFFICIENT)} |"),
        "",
        "## 总分与纪录",
        "",
        (f"- **本世契约**：每点行为进度 = {number(schema.CONTRACT_PROGRESS_COEFFICIENT)} 分，"
         "每局最多 10 点。契约见 [contracts-and-progression.md](contracts-and-progression.md)。"),
        "- **绝对小计** = 以上全部条目之和（允许小数，如 0.1 系条目）。",
        "- **成长小计** = max(0, 绝对小计 − 开局商店与首对交易结束时的基线)。",
        "- **赛道小计**由游戏规则选择绝对或成长口径；0%/25%/50% 向下取整，100% 完整继承，预算不另设上限。",
        ("- **最终总分**：每次在祝福窗口选择「什么都不领」扣 "
         f"{number(schema.REFUSAL_MULTIPLIER_PER_COUNT * 100)}%（加算；拒绝 N 次 = 小计 × "
         f"max(0, 1 − N × {number(schema.REFUSAL_MULTIPLIER_PER_COUNT)})）。"
         "接受祝福/诅咒组合不再直接改变分数。"
         "池子见 [blessing-curse-pools.md](blessing-curse-pools.md)。"),
        ("- **候选余烬位阶** = 不高于最终总分的最大现有持久层阈值；"
         f"达到或超过上限时为 {record_cap():,}。"),
        "- **历史余烬位阶** = 本局开局时从 tutorial lesson 位导入的量化纪录。",
        ("- **位阶差值** = 候选余烬位阶 − 历史余烬位阶；仅严格大于 0 时写入并宣布新纪录。"
         "同一阈值区间内真实总分提高不算破纪录。"),
        "",
        "游戏内死亡结算事件会展示当局每一项的实际数值与完整展开公式，无需手算。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    EFFECT_OUTPUT.write_text(generate_effects(), encoding="utf-8-sig", newline="\n")
    DOC_OUTPUT.write_text(generate_doc(), encoding="utf-8", newline="\n")
    print(f"wrote {EFFECT_OUTPUT.relative_to(ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
