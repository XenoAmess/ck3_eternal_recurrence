#!/usr/bin/env python3
"""Generate the one-launch live fixture for all ZhongGuo 361 mechanisms."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MOD_ROOT = ROOT / "mod_zhongguo_style"
FIXTURE_ROOT = ROOT / "tools" / "fixtures" / "zg361_acceptance"
sys.path.insert(0, str(MOD_ROOT / "tools"))

from zg361_mechanism_data import LEDGERS, load_mechanisms, mechanism_deltas  # noqa: E402


BOM = b"\xef\xbb\xbf"
SCOREBOARD_SLOT_COUNT = 80
OUTPUT = (
    FIXTURE_ROOT
    / "common"
    / "scripted_effects"
    / "zga_generated_361_cases.txt"
)


def expected_portfolio() -> tuple[int, dict[str, int]]:
    mechanisms = load_mechanisms(MOD_ROOT)
    checksum = sum(
        mechanism.id * {"a": 1, "b": 2, "c": 3}[mechanism.reference_choice]
        for mechanism in mechanisms
    )
    ledgers = {
        ledger: sum(
            mechanism_deltas(mechanism, mechanism.reference_choice).get(ledger, 0)
            for mechanism in mechanisms
        )
        for ledger in LEDGERS
    }
    return checksum, ledgers


def exact_portfolio_limits(checksum: int, ledgers: dict[str, int]) -> list[str]:
    limits = [
        "has_variable = zg361_mechanism_configured_n",
        "var:zg361_mechanism_configured_n = 361",
        "has_variable = zg361_mechanism_checksum",
        f"var:zg361_mechanism_checksum = {checksum}",
    ]
    for ledger in LEDGERS:
        limits.extend(
            (
                f"has_variable = zg361_org_{ledger}",
                f"var:zg361_org_{ledger} = {ledgers[ledger]}",
            )
        )
    return limits


def render_mechanism_batch() -> list[str]:
    mechanisms = load_mechanisms(MOD_ROOT)
    checksum, ledgers = expected_portfolio()
    lines = [
        "zga_verify_361_mechanism_batch_effect = {",
        '\tdebug_log = "ZGA: MECHANISM BATCH BEGIN 361"',
        "\tzg361_adopt_reference_charter_effect = yes",
    ]
    choice_values = {"a": 1, "b": 2, "c": 3}
    for mechanism in mechanisms:
        value = choice_values[mechanism.reference_choice]
        lines.extend(
            (
                "\tif = {",
                "\t\tlimit = {",
                f"\t\t\thas_variable = zg361_mechanism_{mechanism.id:03d}_choice",
                f"\t\t\tvar:zg361_mechanism_{mechanism.id:03d}_choice = {value}",
                "\t\t}",
                f'\t\tdebug_log = "ZGA: MECHANISM CASE PASS {mechanism.id:03d}"',
                "\t}",
                f'\telse = {{ debug_log = "ZGA: MECHANISM CASE FAIL {mechanism.id:03d}" }}',
            )
        )
    lines.extend(("\tif = {", "\t\tlimit = {"))
    lines.extend(f"\t\t\t{limit}" for limit in exact_portfolio_limits(checksum, ledgers))
    lines.extend(
        (
            "\t\t}",
            '\t\tdebug_log = "ZGA: MECHANISM LEDGER PASS"',
            "\t}",
            '\telse = { debug_log = "ZGA: MECHANISM LEDGER FAIL" }',
            "",
            "\t# Reapplying the turnkey charter must be a complete no-op.",
            "\tzg361_adopt_reference_charter_effect = yes",
            "\tif = {",
            "\t\tlimit = {",
        )
    )
    lines.extend(f"\t\t\t{limit}" for limit in exact_portfolio_limits(checksum, ledgers))
    lines.extend(
        (
            "\t\t}",
            '\t\tdebug_log = "ZGA: MECHANISM IDEMPOTENCE PASS"',
            "\t}",
            '\telse = { debug_log = "ZGA: MECHANISM IDEMPOTENCE FAIL" }',
            '\tdebug_log = "ZGA: MECHANISM BATCH DONE 361"',
            "}",
            "",
        )
    )
    return lines


def render_scoreboard_verifier() -> list[str]:
    lines = [
        "zga_verify_fixed_scoreboard_slots_effect = {",
        "\tset_variable = { name = zga_board_rows value = 0 }",
        "\tset_variable = { name = zga_board_valid_rows value = 0 }",
        "\tset_variable = { name = zga_board_375 value = 0 }",
        "\tset_variable = { name = zga_board_35 value = 0 }",
        "\tset_variable = { name = zga_board_325 value = 0 }",
    ]
    for slot in range(1, SCOREBOARD_SLOT_COUNT + 1):
        stem = f"zg361_sb_m_{slot:02d}"
        lines.extend(
            (
                "\tif = {",
                f"\t\tlimit = {{ has_variable = {stem}_char }}",
                "\t\tchange_variable = { name = zga_board_rows add = 1 }",
                f'\t\tdebug_log = "ZGA: DATA player_scoreboard_row {slot:02d}"',
                "\t\tif = {",
                "\t\t\tlimit = {",
                f"\t\t\t\thas_variable = {stem}_kpi",
                f"\t\t\t\thas_variable = {stem}_rank",
                f"\t\t\t\thas_variable = {stem}_values",
                f"\t\t\t\thas_variable = {stem}_grade",
                f"\t\t\t\thas_variable = {stem}_streak",
                f"\t\t\t\thas_variable = {stem}_title",
                f"\t\t\t\thas_variable = {stem}_promotion",
                f"\t\t\t\thas_variable = {stem}_pip",
                f"\t\t\t\tvar:{stem}_rank = {slot}",
                "\t\t\t}",
                "\t\t\tchange_variable = { name = zga_board_valid_rows add = 1 }",
                "\t\t}",
                "\t\tif = {",
                f"\t\t\tlimit = {{ var:{stem}_grade = 3.75 }}",
                "\t\t\tchange_variable = { name = zga_board_375 add = 1 }",
                f'\t\t\tdebug_log = "ZGA: DATA player_grade_375 {slot:02d}"',
                "\t\t}",
                "\t\telse_if = {",
                f"\t\t\tlimit = {{ var:{stem}_grade = 3.5 }}",
                "\t\t\tchange_variable = { name = zga_board_35 add = 1 }",
                f'\t\t\tdebug_log = "ZGA: DATA player_grade_35 {slot:02d}"',
                "\t\t}",
                "\t\telse_if = {",
                f"\t\t\tlimit = {{ var:{stem}_grade = 3.25 }}",
                "\t\t\tchange_variable = { name = zga_board_325 add = 1 }",
                f'\t\t\tdebug_log = "ZGA: DATA player_grade_325 {slot:02d}"',
                "\t\t}",
                "\t}",
            )
        )
    lines.extend(("}", ""))
    return lines


def render() -> bytes:
    lines = [
        "# GENERATED FILE — edit tools/gen_zhongguo_acceptance_cases.py",
        "# External fixture assertions only; every state transition under test lives in the product.",
        "",
    ]
    lines.extend(render_mechanism_batch())
    lines.extend(render_scoreboard_verifier())
    return BOM + ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    expected = render()
    if arguments.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print(f"RED: stale generated fixture: {OUTPUT.relative_to(ROOT)}")
            return 1
        print(f"GREEN: checked 361 live cases and {SCOREBOARD_SLOT_COUNT} fixed scoreboard slots")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(expected)
    print(f"GREEN: generated 361 live cases and {SCOREBOARD_SLOT_COUNT} fixed scoreboard slots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
