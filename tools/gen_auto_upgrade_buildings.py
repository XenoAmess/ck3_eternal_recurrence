#!/usr/bin/env python3
"""Generate all CK3 1.19.0.6 Auto Upgrade Buildings runtime branches."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auto_upgrade_buildings_data import CHAINS, EDGES, BuildingChain, BuildingEdge


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod_auto_upgrade_buildings"
EFFECT_OUTPUT = MOD / "common" / "scripted_effects" / "build_scripted_effect.txt"
TRIGGER_OUTPUT = MOD / "common" / "scripted_triggers" / "aub_building_triggers.txt"


def _indent_body(value: str, tabs: int) -> list[str]:
    prefix = "\t" * tabs
    return [prefix + line for line in value.splitlines()]


def trigger_name(edge: BuildingEdge) -> str:
    return f"aub_can_upgrade_to_{edge.target}_trigger"


def chain_effect_name(chain: BuildingChain) -> str:
    return f"aub_upgrade_chain_{chain.root}_effect"


def render_triggers() -> str:
    lines = [
        "# GENERATED FILE. DO NOT EDIT.",
        "# Source: tools/auto_upgrade_buildings_1_19_0_6.json",
        "# Every trigger reproduces the target building's four vanilla construction gates.",
        "",
    ]
    for edge in EDGES:
        lines.append(f"{trigger_name(edge)} = {{")
        if not edge.gates:
            lines.append("\talways = yes")
        else:
            for field, body in edge.gates:
                lines.append(f"\t# vanilla {field}")
                lines.extend(_indent_body(body, 1))
        lines.extend(["}", ""])
    return "\n".join(lines)


def _resource_limits(edge: BuildingEdge) -> list[str]:
    resources = dict(edge.resources)
    lines = [
        "\t\t\tOR = {",
        f"\t\t\t\tscope:aub_payer = {{ treasury >= {resources['gold']} }}",
        f"\t\t\t\tscope:aub_payer = {{ gold >= {resources['gold']} }}",
        "\t\t\t}",
    ]
    if "prestige" in resources:
        lines.append(
            f"\t\t\tscope:aub_payer = {{ prestige >= {resources['prestige']} }}"
        )
    if "piety" in resources:
        lines.append(f"\t\t\tscope:aub_payer = {{ piety >= {resources['piety']} }}")
    return lines


def _payment_call(edge: BuildingEdge) -> str:
    resources = dict(edge.resources)
    arguments = [f"GOLD = {resources['gold']}"]
    if "prestige" in resources:
        arguments.append(f"PRESTIGE = {resources['prestige']}")
        effect = "aub_pay_gold_prestige_building_cost_effect"
    elif "piety" in resources:
        arguments.append(f"PIETY = {resources['piety']}")
        effect = "aub_pay_gold_piety_building_cost_effect"
    else:
        effect = "aub_pay_gold_building_cost_effect"
    return f"{effect} = {{ {' '.join(arguments)} }}"


def render_chain(chain: BuildingChain) -> list[str]:
    lines = [
        f"# {chain.root}: {len(chain.edges)} frozen upgrade edge(s)",
        f"{chain_effect_name(chain)} = {{",
    ]
    for index, edge in enumerate(chain.edges):
        keyword = "if" if index == 0 else "else_if"
        lines.extend(
            [
                f"\t{keyword} = {{",
                "\t\tlimit = {",
                f"\t\t\thas_building = {edge.source}",
                f"\t\t\t{trigger_name(edge)} = yes",
            ]
        )
        lines.extend(_resource_limits(edge))
        lines.append("\t\t}")
        if edge.target_type == "special":
            # Special buildings occupy their own fixed slot. CK3's generic
            # add_building effect refuses to replace an occupied special slot;
            # vanilla scripted upgrades remove the old tier and then use
            # add_special_building for the new tier.
            lines.extend(
                [
                    f"\t\tremove_building = {edge.source}",
                    "\t\tscope:aub_payer = { save_scope_as = character }",
                    f"\t\tadd_special_building = {edge.target}",
                ]
            )
        else:
            lines.extend(
                [
                    "\t\tscope:aub_payer = { save_scope_as = character }",
                    f"\t\tadd_building = {edge.target}",
                ]
            )
        lines.extend(
            [
                "\t\tif = {",
                f"\t\t\tlimit = {{ has_building = {edge.target} }}",
                f"\t\t\t{_payment_call(edge)}",
                "\t\t}",
            ]
        )
        if edge.target_type == "special":
            # A failed engine insertion must not silently destroy the source
            # special building and is never charged.
            lines.extend(
                [
                    "\t\telse = {",
                    "\t\t\tscope:aub_payer = { save_scope_as = character }",
                    f"\t\t\tadd_special_building = {edge.source}",
                    "\t\t}",
                ]
            )
        lines.append("\t}")
    lines.extend(["}", ""])
    return lines


def render_effects() -> str:
    lines = [
        "# GENERATED FILE. DO NOT EDIT.",
        "# Source: tools/auto_upgrade_buildings_1_19_0_6.json",
        "",
        "aub_start_global_loop_effect = {",
        "\tif = {",
        "\t\tlimit = { NOT = { has_global_variable = aub_auto_build_loop_started } }",
        "\t\tset_global_variable = { name = aub_auto_build_loop_started value = 1 }",
        "\t\ttrigger_event = { id = auto_build.0005 days = 1 }",
        "\t}",
        "}",
        "",
        "aub_pay_gold_building_cost_effect = {",
        "\tif = {",
        "\t\tlimit = { scope:aub_payer = { treasury >= $GOLD$ } }",
        "\t\tscope:aub_payer = { remove_short_term_treasury = $GOLD$ }",
        "\t}",
        "\telse = {",
        "\t\tscope:aub_payer = { remove_short_term_gold = $GOLD$ }",
        "\t}",
        "}",
        "",
        "aub_pay_gold_prestige_building_cost_effect = {",
        "\taub_pay_gold_building_cost_effect = { GOLD = $GOLD$ }",
        "\tscope:aub_payer = {",
        "\t\tadd_prestige = {",
        "\t\t\tvalue = $PRESTIGE$",
        "\t\t\tmultiply = -1",
        "\t\t}",
        "\t}",
        "}",
        "",
        "aub_pay_gold_piety_building_cost_effect = {",
        "\taub_pay_gold_building_cost_effect = { GOLD = $GOLD$ }",
        "\tscope:aub_payer = {",
        "\t\tadd_piety = {",
        "\t\t\tvalue = $PIETY$",
        "\t\t\tmultiply = -1",
        "\t\t}",
        "\t}",
        "}",
        "",
    ]
    for chain in CHAINS:
        lines.extend(render_chain(chain))
    lines.append("aub_upgrade_all_supported_buildings_effect = {")
    for chain in CHAINS:
        lines.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ has_building_or_higher = {chain.root} }}",
                f"\t\t{chain_effect_name(chain)} = yes",
                "\t}",
            ]
        )
    lines.extend(["}", ""])
    return "\n".join(lines)


def render() -> str:
    """Backward-compatible name for callers validating the effect output."""
    return render_effects()


def generated_outputs() -> dict[Path, bytes]:
    return {
        EFFECT_OUTPUT: render_effects().encode("utf-8-sig"),
        TRIGGER_OUTPUT: render_triggers().encode("utf-8-sig"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = generated_outputs()
    if args.check:
        stale = [path for path, expected in outputs.items() if not path.is_file() or path.read_bytes() != expected]
        if stale:
            for path in stale:
                print(f"STALE GENERATED FILE: {path}", file=sys.stderr)
            return 1
        print(f"AUTO UPGRADE BUILDINGS GENERATOR OK: {len(CHAINS)} chains, {len(EDGES)} edges")
        return 0
    for path, expected in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected)
        print(f"Generated {path}")
    print(f"Inventory: {len(CHAINS)} chains, {len(EDGES)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
