#!/usr/bin/env python3
"""Generate the read-only score formula used by the Glassfire Gaze tooltip."""

from pathlib import Path

import scoring_data as schema


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = (ROOT / "XenoAmess_s_Eternal_Recurrence" / "common" /
          "script_values" / "xar_generated_score_preview.txt")


def add_log2_steps(lines, source, multiplier, indent="\t"):
    for exponent in range(1, schema.LOG2_MAX_EXPONENT + 1):
        lines.extend([
            f"{indent}if = {{",
            f"{indent}\tlimit = {{ {source} >= {2 ** exponent} }}",
            f"{indent}\tadd = {multiplier}",
            f"{indent}}}",
        ])


def ancestor_within(max_depth):
    branches = []
    for depth in range(max_depth + 1):
        branch = "this = scope:xar_score_preview_root"
        for _ in range(depth):
            branch = f"any_parent = {{ {branch} }}"
        branches.append(branch)
    return f"OR = {{ {' '.join(branches)} }}"


def canonical_descendant_path(depth, parent_scope):
    # Use the shortest route from the root; prefer the father when both routes
    # have equal length. This deduplicates pedigrees without tooltip mutations.
    return (
        "OR = { "
        f"AND = {{ father ?= {{ this = scope:{parent_scope} }} "
        f"NOT = {{ mother ?= {{ {ancestor_within(depth - 2)} }} }} }} "
        f"AND = {{ mother ?= {{ this = scope:{parent_scope} }} "
        f"NOT = {{ father ?= {{ {ancestor_within(depth - 1)} }} }} }} "
        "}"
    )


def descendant_list(remaining, depth=1, indent="\t"):
    parent_scope = f"xar_score_preview_parent_{depth}"
    lines = [f"{indent}save_temporary_scope_as = {parent_scope}",
             f"{indent}every_child = {{"]
    body_indent = indent + "\t"
    if depth > 1:
        lines.extend([
            f"{body_indent}if = {{",
            f"{body_indent}\tlimit = {{ {canonical_descendant_path(depth, parent_scope)} }}",
        ])
        body_indent += "\t"
    lines.append(f"{body_indent}add = xar_current_descendant_score_value")
    if remaining > 1:
        lines.extend(descendant_list(remaining - 1, depth + 1, body_indent))
    if depth > 1:
        lines.append(f"{indent}\t}}")
    lines.append(f"{indent}}}")
    return lines


def generate():
    lines = [
        "# GENERATED FILE - do not edit. Regenerate with tools/gen_score_preview.py",
        "# Pure formulas only: trait hover evaluates these without changing game state.",
        "",
        "# Current scope is one descendant; root family scopes are saved by the caller.",
        "xar_current_descendant_score_value = {",
        "\tvalue = 0",
        "\tif = {",
        "\t\tlimit = { is_alive = yes }",
        "\t\tif = {",
        "\t\t\tlimit = {",
        "\t\t\t\texists = scope:xar_score_preview_dyn",
        "\t\t\t\texists = dynasty",
        "\t\t\t\tdynasty = { this = scope:xar_score_preview_dyn }",
        "\t\t\t}",
        f"\t\t\tadd = {schema.DYNASTY_DESCENDANT_COEFFICIENT}",
        "\t\t}",
        "\t\tif = {",
        "\t\t\tlimit = {",
        "\t\t\t\texists = scope:xar_score_preview_house",
        "\t\t\t\texists = house",
        "\t\t\t\thouse = { this = scope:xar_score_preview_house }",
        "\t\t\t}",
        f"\t\t\tadd = {schema.HOUSE_DESCENDANT_COEFFICIENT}",
        "\t\t}",
    ]
    for index, rule in enumerate(reversed(schema.DESCENDANT_TITLE_TIERS)):
        keyword = "if" if index == 0 else "else_if"
        lines.extend([
            f"\t\t{keyword} = {{",
            f"\t\t\tlimit = {{ highest_held_title_tier >= {rule.tier} }}",
            f"\t\t\tadd = {rule.coefficient}",
            "\t\t}",
        ])
    lines.extend([
        "\t}",
        "}",
        "",
        "xar_current_score_base_value = {",
        "\tvalue = 0",
        "\tsave_temporary_scope_as = xar_score_preview_root",
        "\tif = { limit = { exists = dynasty } dynasty = { save_temporary_scope_as = xar_score_preview_dyn } }",
        "\tif = { limit = { exists = house } house = { save_temporary_scope_as = xar_score_preview_house } }",
        "",
        "\t# Attributes.",
    ])
    for rule in schema.ATTRIBUTES:
        if rule.coefficient == 1:
            lines.append(f"\tadd = {rule.source}")
        else:
            lines.append(
                f"\tadd = {{ value = {rule.source} multiply = {rule.coefficient} }}")

    lines.extend(["", "\t# Resources: floor(log2(value)) times the scoring coefficient."])
    for rule in schema.RESOURCES:
        lines.append(f"\t# {rule.source}")
        add_log2_steps(lines, rule.source, rule.coefficient)

    lines.extend(["", "\t# Held titles."])
    for rule in schema.HELD_TITLE_TIERS:
        lines.append(
            f"\tevery_held_title = {{ limit = {{ tier = {rule.tier} }} add = {rule.coefficient} }}")

    lines.extend([
        "",
        (f"\t# Living descendants through {schema.DESCENDANT_DEPTH} generations: "
         "blood and highest title."),
    ])
    lines.extend(descendant_list(schema.DESCENDANT_DEPTH))
    lines.extend([
        "",
        "\t# Landed realm size.",
        "\tif = {",
        "\t\tlimit = { is_landed = yes }",
    ])
    add_log2_steps(lines, "realm_size", schema.REALM_SIZE_COEFFICIENT, "\t\t")
    lines.extend([
        "\t}",
        "",
        "\t# Incremental lifetime-contract behavior.",
        f"\tadd = {{ value = global_var:xa_contract_progress multiply = {schema.CONTRACT_PROGRESS_COEFFICIENT} }}",
        "}",
        "",
        "xar_current_score_value = {",
        "\tvalue = xar_current_score_base_value",
        "\tif = {",
        "\t\tlimit = { global_var:xa_score_basis = 1 }",
        "\t\tsubtract = { value = global_var:xa_score_baseline }",
        "\t\tmax = 0",
        "\t}",
        "",
        ("\t# Each declined blessing session removes "
         f"{schema.REFUSAL_MULTIPLIER_PER_COUNT * 100} percent; never below zero."),
        "\tif = {",
        "\t\tlimit = { global_var:xa_bless_reject_count > 0 }",
        "\t\tmultiply = {",
        "\t\t\tvalue = 1",
        ("\t\t\tsubtract = { value = global_var:xa_bless_reject_count "
         f"multiply = {schema.REFUSAL_MULTIPLIER_PER_COUNT} }}"),
        "\t\t\tmin = 0",
        "\t\t}",
        "\t}",
        "}",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generate(), encoding="utf-8-sig", newline="\n")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
