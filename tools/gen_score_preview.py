#!/usr/bin/env python3
"""Generate the read-only score formula used by the Glassfire Gaze tooltip."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = (ROOT / "XenoAmess_s_Eternal_Recurrence" / "common" /
          "script_values" / "xar_generated_score_preview.txt")


def add_log2_steps(lines, source, multiplier, indent="\t"):
    for exponent in range(1, 31):
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
    # have equal length. This deduplicates consanguineous pedigrees without
    # mutating character flags from a tooltip script value.
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
        "\t\t\tadd = 0.1",
        "\t\t}",
        "\t\tif = {",
        "\t\t\tlimit = {",
        "\t\t\t\texists = scope:xar_score_preview_house",
        "\t\t\t\texists = house",
        "\t\t\t\thouse = { this = scope:xar_score_preview_house }",
        "\t\t\t}",
        "\t\t\tadd = 0.1",
        "\t\t}",
        "\t\tif = {",
        "\t\t\tlimit = { highest_held_title_tier >= tier_hegemony }",
        "\t\t\tadd = 10",
        "\t\t}",
        "\t\telse_if = {",
        "\t\t\tlimit = { highest_held_title_tier >= tier_empire }",
        "\t\t\tadd = 5",
        "\t\t}",
        "\t\telse_if = {",
        "\t\t\tlimit = { highest_held_title_tier >= tier_kingdom }",
        "\t\t\tadd = 2.5",
        "\t\t}",
        "\t\telse_if = {",
        "\t\t\tlimit = { highest_held_title_tier >= tier_duchy }",
        "\t\t\tadd = 1",
        "\t\t}",
        "\t\telse_if = {",
        "\t\t\tlimit = { highest_held_title_tier >= tier_county }",
        "\t\t\tadd = 0.25",
        "\t\t}",
        "\t}",
        "}",
        "",
        "xar_current_score_value = {",
        "\tvalue = 0",
        "\tsave_temporary_scope_as = xar_score_preview_root",
        "\tif = { limit = { exists = dynasty } dynasty = { save_temporary_scope_as = xar_score_preview_dyn } }",
        "\tif = { limit = { exists = house } house = { save_temporary_scope_as = xar_score_preview_house } }",
        "",
        "\t# Attributes.",
        "\tadd = diplomacy",
        "\tadd = martial",
        "\tadd = stewardship",
        "\tadd = intrigue",
        "\tadd = learning",
        "\tadd = prowess",
        "",
        "\t# Resources: floor(log2(value)) times the scoring coefficient.",
    ]
    for source, multiplier in (("gold", 5), ("prestige", 3), ("piety", 3),
                               ("influence", 3)):
        lines.append(f"\t# {source}")
        add_log2_steps(lines, source, multiplier)

    lines.extend([
        "",
        "\t# Held titles.",
        "\tevery_held_title = { limit = { tier = tier_county } add = 1 }",
        "\tevery_held_title = { limit = { tier = tier_duchy } add = 2.5 }",
        "\tevery_held_title = { limit = { tier = tier_kingdom } add = 5 }",
        "\tevery_held_title = { limit = { tier = tier_empire } add = 10 }",
        "\tevery_held_title = { limit = { tier = tier_hegemony } add = 20 }",
        "",
        "\t# Living descendants through five generations: blood and highest title.",
    ])
    lines.extend(descendant_list(5))
    lines.extend([
        "",
        "\t# Landed realm size.",
        "\tif = {",
        "\t\tlimit = { is_landed = yes }",
    ])
    add_log2_steps(lines, "realm_size", 10, "\t\t")
    lines.extend([
        "\t}",
        "",
        "\t# Each declined blessing session removes one percent; never below zero.",
        "\tif = {",
        "\t\tlimit = { global_var:xa_bless_reject_count > 0 }",
        "\t\tmultiply = {",
        "\t\t\tvalue = 1",
        "\t\t\tsubtract = { value = global_var:xa_bless_reject_count multiply = 0.01 }",
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
