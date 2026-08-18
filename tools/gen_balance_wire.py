#!/usr/bin/env python3
"""Generate localization-free acceptance telemetry for long balance runs."""

from pathlib import Path

from balance_wire_data import FIELD_SPECS


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
HEADER = "# GENERATED FILE - do not edit. Regenerate with tools/gen_balance_wire.py"


def value_body(expression, scale, bit=None):
    lines = [f"\tvalue = {expression}"]
    if scale != 1:
        lines.extend([f"\tmultiply = {scale}", "\tfloor = yes"])
    lines.append("\tabs = yes")
    if bit is not None:
        lines.extend([f"\tdivide = {1 << bit}", "\tfloor = yes", "\tmodulo = 2"])
    return lines


def generated_values():
    lines = [HEADER, "# One independent modulo projection per field/bit.", ""]
    for name, expression, scale, bits, _ in FIELD_SPECS:
        for bit in range(bits):
            lines.append(f"xar_balance_wire_{name}_b{bit} = {{")
            lines.extend(value_body(expression, scale, bit))
            lines.extend(["}", ""])
        lines.append(f"xar_balance_wire_{name}_overflow = {{")
        lines.extend(value_body(expression, scale))
        lines.extend([f"\tsubtract = {1 << bits}", "}", ""])
    return "\n".join(lines)


def generated_effect():
    lines = [HEADER, "xar_acceptance_balance_emit_wire_effect = {"]
    for name, expression, _, bits, signed in FIELD_SPECS:
        if signed:
            lines.extend([
                "\tif = {",
                f"\t\tlimit = {{ {expression} < 0 }}",
                f'\t\tdebug_log = "XAR: BALANCE DATA|field={name}|sign=-"',
                "\t}",
            ])
        for bit in range(bits):
            lines.extend([
                "\tif = {",
                f"\t\tlimit = {{ xar_balance_wire_{name}_b{bit} = 1 }}",
                f'\t\tdebug_log = "XAR: BALANCE DATA|field={name}|bit={bit}"',
                "\t}",
            ])
        lines.extend([
            "\tif = {",
            f"\t\tlimit = {{ xar_balance_wire_{name}_overflow >= 0 }}",
            f'\t\tdebug_log = "XAR: BALANCE WIRE FAIL overflow_{name}"',
            "\t}",
        ])
    lines.extend(["}", ""])
    return "\n".join(lines)


def write_bom(path, content):
    path.write_text(content, encoding="utf-8-sig", newline="\n")


def main():
    write_bom(
        MOD / "common/script_values/xar_acceptance_balance_wire_values.txt",
        generated_values())
    write_bom(
        MOD / "common/scripted_effects/xar_acceptance_balance_wire_effects.txt",
        generated_effect())
    print(f"generated balance wire: {len(FIELD_SPECS)} fields")


if __name__ == "__main__":
    main()
