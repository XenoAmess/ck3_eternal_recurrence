#!/usr/bin/env python3
"""Project the frozen CK3 1.20.0.2 governors with five XQOL score insertions."""

from __future__ import annotations

import argparse
from pathlib import Path

from xqol_vanilla_contract import GAME, ROOT, require_sources


MOD = ROOT / "mod_xenoamess_quality_of_life"
DIRECTORY = "common/succession_appointment"
FILES = {"admin_governor.txt": 1, "meritocratic_governor.txt": 2, "celestial_governor.txt": 2}
ANCHOR = "\t\t\tadd = appointment_score_final_factors"


def insertion(filename: str) -> str:
    ruler_test = "top_liege = this" if filename == "admin_governor.txt" else "is_independent_ruler = yes"
    return (
        "\n\n\t\t\t# XQOL_AUTO_APPOINTMENT_BEGIN\n"
        "\t\t\tif = {\n\t\t\t\tlimit = {\n"
        f"\t\t\t\t\t{ruler_test}\n"
        "\t\t\t\t\tis_ai = no\n"
        "\t\t\t\t\thas_variable = xqol_auto_appoint_successors_enabled\n"
        "\t\t\t\t}\n\t\t\t\tsubtract = {\n"
        "\t\t\t\t\tvalue = 1000000\n"
        "\t\t\t\t\tdesc = xqol_auto_appointment_score_penalty_desc\n"
        "\t\t\t\t}\n\t\t\t}\n"
        "\t\t\t# XQOL_AUTO_APPOINTMENT_END"
    ).replace("\n", "\r\n")


def generated_payloads() -> dict[str, bytes]:
    require_sources()
    result = {}
    for filename, count in FILES.items():
        data = (GAME / DIRECTORY / filename).read_bytes()
        text = data.decode("utf-8-sig")
        if text.count(ANCHOR) != count or "XQOL_AUTO_APPOINTMENT" in text:
            raise ValueError(f"native appointment insertion anchor changed: {filename}")
        if b"\n" in data.replace(b"\r\n", b""):
            raise ValueError(f"native appointment line endings changed: {filename}")
        result[f"{DIRECTORY}/{filename}"] = text.replace(ANCHOR, ANCHOR + insertion(filename)).encode("utf-8-sig")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payloads = generated_payloads()
        for relative, data in payloads.items():
            path = MOD / relative
            if args.check:
                if path.read_bytes() != data:
                    raise ValueError(f"generated appointment drift: {relative}")
            else:
                path.write_bytes(data)
    except (OSError, ValueError) as error:
        print(f"XQOL APPOINTMENT PROJECTION RED: {error}")
        return 1
    print(f"XQOL APPOINTMENT PROJECTION {'CURRENT' if args.check else 'GENERATED'}: 3 files / 5 insertions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
