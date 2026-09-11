#!/usr/bin/env python3
"""Generate the maintained Auto Upgrade Buildings scripted effects."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auto_upgrade_buildings_data import CHAINS, BuildingChain


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "mod_auto_upgrade_buildings"
    / "common"
    / "scripted_effects"
    / "build_scripted_effect.txt"
)


def cost_token(item: BuildingChain, index: int) -> str:
    return f"{item.cost_family}_building_tier_{item.cost_tiers[index]}_cost"


def render_chain(item: BuildingChain) -> list[str]:
    lines = [f"# {item.label}", f"aub_upgrade_{item.name}_effect = {{"]
    for index, target_tier in enumerate(range(2, 9)):
        keyword = "if" if index == 0 else "else_if"
        cost = cost_token(item, index)
        lines.extend(
            [
                f"\t{keyword} = {{",
                "\t\tlimit = {",
                "\t\t\tOR = {",
                f"\t\t\t\tscope:aub_payer = {{ treasury >= {cost} }}",
                f"\t\t\t\tscope:aub_payer = {{ gold >= {cost} }}",
                "\t\t\t}",
                f"\t\t\thas_building = {item.name}_{target_tier - 1:02d}",
            ]
        )
        innovations = item.innovations[index]
        if innovations:
            lines.append("\t\t\tscope:aub_payer.culture = {")
            lines.extend(f"\t\t\t\thas_innovation = {value}" for value in innovations)
            lines.append("\t\t\t}")
        level = item.holding_levels[index]
        if level is not None:
            lines.append(
                f"\t\t\tbuilding_requirement_castle_city_church = {{ LEVEL = {level:02d} }}"
            )
        if item.payer_triggers:
            lines.append("\t\t\tscope:aub_payer = {")
            lines.extend(f"\t\t\t\t{value}" for value in item.payer_triggers)
            lines.append("\t\t\t}")
        lines.extend(
            [
                "\t\t}",
                f"\t\tadd_building = {item.name}_{target_tier:02d}",
                "\t\tif = {",
                f"\t\t\tlimit = {{ has_building = {item.name}_{target_tier:02d} }}",
                f"\t\t\taub_pay_building_cost_effect = {{ COST = {cost} }}",
                "\t\t}",
                "\t}",
            ]
        )
    lines.extend(["}", ""])
    return lines


def render() -> str:
    lines = [
        "# GENERATED FILE. DO NOT EDIT.",
        "# Source: tools/auto_upgrade_buildings_data.py",
        "",
        "aub_start_global_loop_effect = {",
        "\tif = {",
        "\t\tlimit = { NOT = { has_global_variable = aub_auto_build_loop_started } }",
        "\t\tset_global_variable = { name = aub_auto_build_loop_started value = 1 }",
        "\t\ttrigger_event = { id = auto_build.0005 days = 1 }",
        "\t}",
        "}",
        "",
        "aub_pay_building_cost_effect = {",
        "\tif = {",
        "\t\tlimit = { scope:aub_payer = { treasury >= $COST$ } }",
        "\t\tscope:aub_payer = { remove_short_term_treasury = $COST$ }",
        "\t}",
        "\telse = {",
        "\t\tscope:aub_payer = { remove_short_term_gold = $COST$ }",
        "\t}",
        "}",
        "",
    ]
    for item in CHAINS:
        lines.extend(render_chain(item))
    lines.extend(["aub_upgrade_all_supported_buildings_effect = {"])
    for item in CHAINS:
        lines.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ has_building_or_higher = {item.name}_01 }}",
                f"\t\taub_upgrade_{item.name}_effect = yes",
                "\t}",
            ]
        )
    lines.extend(["}", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = render().encode("utf-8-sig")
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print(f"STALE GENERATED FILE: {OUTPUT}", file=sys.stderr)
            return 1
        print(f"AUTO UPGRADE BUILDINGS GENERATOR OK: {len(CHAINS)} chains")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(expected)
    print(f"Generated {OUTPUT} ({len(CHAINS)} chains)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
