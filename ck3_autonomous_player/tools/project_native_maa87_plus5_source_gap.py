"""Audit why paired offline evidence cannot identify MAA 87's +5% source.

Reports script candidates and exact missing live values; no candidate is
classified as active merely because its literal matches 25 -> 26.25.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


IDENTITY_SHA = "69B906918120294000C8BB821A1AEEFE43BD210FB14610E8EACC1B0CFC1BC210"
V3_SHAS = {
    11: "50F1FE7946F846E237AAC2003B98BF540363C133AA8EE93AB69F388E2472E2BE",
    21: "A8B257EE743B593DBE145ED2D6E152DC7791C092EB0B6C95BE8943B1C23AE1E1",
}
SOURCES = {
    "generic_army": "common/modifiers/01_dlc_ep1_modifiers.txt",
    "heavy_infantry": "common/buildings/00_duchy_capital_buildings.txt",
}


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def line_window(path: Path, marker: str, required: str, max_lines: int) -> dict:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    windows = [(i + 1, lines[i:i + max_lines]) for i, line in enumerate(lines)
               if line.strip() == marker]
    hits = [(line, window) for line, window in windows
            if any(row.strip() == required for row in window)]
    require(len(hits) == 1, f"script candidate ambiguous: {path}: {marker}")
    line, window = hits[0]
    return {"line": line, "modifier_line": line + next(
        offset for offset, row in enumerate(window) if row.strip() == required)}


def project(args: argparse.Namespace) -> dict:
    require(digest(args.identity_sidecar) == IDENTITY_SHA, "source-save identity sidecar changed")
    identity = json.loads(args.identity_sidecar.read_text(encoding="utf-8"))
    require(identity["maa_type"]["key"] == "mubarizun"
            and identity["maa_type"]["base_toughness"] == 25
            and identity["source_save_identity_only"], "source-save identity gate changed")
    rows = []
    for day in (11, 21):
        path = getattr(args, f"day{day}_v3")
        require(digest(path) == V3_SHAS[day], f"frozen day{day} v3 SHA changed")
        response = json.loads(path.read_text(encoding="utf-8"))
        body = response["body"]
        require(response["result"] == "CALL_COMPLETED" and body["status"] == "available"
                and body["target_province_id"] == 2633, f"day{day} v3 status/target changed")
        armies = body["combat_simulation_inputs"]["base_inputs"]["armies"]
        matches = [(army, row) for army in armies for row in army["regiments"]
                   if row["regiment_id"] == 87]
        require(len(matches) == 1, f"day{day} RegimentID 87 count changed")
        army, row = matches[0]
        stats = row["effective_stats"]
        require(army["army_id"] == 16777221
                and army["owner"]["character_id"] == 31549
                and row["maa_type"] == {"status": "absent", "key": None,
                                        "unavailable_reason": None}
                and row["kind"]["value"] == "men_at_arms"
                and stats["source_target_province_id"] == 2633
                and stats["damage_raw"] == 4500000
                and stats["toughness_raw"] == 2625000,
                f"day{day} MAA 87 identity/final stats changed")
        require(not any("modifier" in key or "component" in key for key in stats),
                f"day{day} effective_stats now contains a decomposition")
        rows.append({"source_day": day, "v3_sha256": V3_SHAS[day],
                     "army_id": 16777221, "owner_character_id": 31549,
                     "regiment_id": 87, "target_province_id": 2633,
                     "effective_toughness_raw": 2625000,
                     "modifier_components_in_regiment_stats": False})

    generic = args.game_root / SOURCES["generic_army"]
    heavy = args.game_root / SOURCES["heavy_infantry"]
    generic_lines = line_window(generic, "ep1_flavor_2020_both_modifier = {",
                                "army_toughness_mult = 0.05", 7)
    heavy_lines = line_window(heavy, "character_culture_modifier = {",
                              "heavy_infantry_toughness_mult = 0.05", 7)
    # There can be other character_culture_modifier blocks. The selected one
    # has this explicit culture parameter immediately above the heavy-infantry line.
    heavy_rows = heavy.read_text(encoding="utf-8-sig").splitlines()
    require(heavy_rows[heavy_lines["line"]].strip() ==
            "parameter = better_blacksmith_buildings", "culture gate changed")
    require(2500000 * 105000 // 100000 == 2625000, "Q100000 witness changed")
    return {
        "schema": "ck3.maa87_plus5_source_gap.v1",
        "identity_sidecar_sha256": IDENTITY_SHA,
        "source_save_type_key": "mubarizun",
        "base_toughness": 25,
        "current_effective_toughness_raw": 2625000,
        "q100000_arithmetic_witness": "2500000*105000/100000=2625000",
        "frozen_v3_cases": rows,
        "script_candidates_not_proven_active": [
            {"source_class": "generic_army", "relative_path": SOURCES["generic_army"],
             "file_sha256": digest(generic), "modifier_key": "ep1_flavor_2020_both_modifier",
             "literal": "army_toughness_mult = 0.05", **generic_lines},
            {"source_class": "heavy_infantry", "relative_path": SOURCES["heavy_infantry"],
             "file_sha256": digest(heavy), "gate": "better_blacksmith_buildings",
             "literal": "heavy_infantry_toughness_mult = 0.05", **heavy_lines},
        ],
        "next_probe_rvas": {
            "outer_regiment_and_target_identity": "0x239CAE0",
            "maa_aggregator_with_regiment_pointer": "0x2C8F1A0",
            "class_modifier_reader": "0x2C8D6A0",
            "native_modifier_value_helper": "0x2940E80",
            "toughness_enum_operands": ["0x2C8D8E0", "0x2C8D902", "0x2C8D92B"],
            "class_dynamic_toughness_enum_operands": ["0x2C8D94D", "0x2C8D97E"],
            "pre_apply_modifier_vector": "0x2C8F7B1",
            "fixed_point_apply": "0x2C8F7B9",
            "target_province_vector": "0x2C8F8FF",
        },
        "same_frame_modifier_source_proven": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-sidecar", type=Path, required=True)
    parser.add_argument("--day11-v3", type=Path, required=True)
    parser.add_argument("--day21-v3", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--output", type=Path)
    modes.add_argument("--check-sidecar", type=Path)
    args = parser.parse_args()
    result = project(args)
    if args.check_sidecar:
        require(json.loads(args.check_sidecar.read_text(encoding="utf-8")) == result,
                "gap sidecar differs from source projection")
        print(json.dumps({"ok": True, "sidecar_sha256": digest(args.check_sidecar)}))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))


if __name__ == "__main__":
    main()
