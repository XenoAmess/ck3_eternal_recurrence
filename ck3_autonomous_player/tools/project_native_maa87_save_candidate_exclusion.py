"""Freeze save-side exclusion evidence for two MAA 87 +5% script candidates.

This is a read-only projection of paired saves and game scripts. It deliberately
does not attribute the native 26.25 toughness result to any remaining source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
IDENTITY_SHA256 = "69B906918120294000C8BB821A1AEEFE43BD210FB14610E8EACC1B0CFC1BC210"
V3_SHA256 = {
    11: "50F1FE7946F846E237AAC2003B98BF540363C133AA8EE93AB69F388E2472E2BE",
    21: "A8B257EE743B593DBE145ED2D6E152DC7791C092EB0B6C95BE8943B1C23AE1E1",
}
EP1_KEY = b"ep1_flavor_2020_both_modifier"
BLACKSMITHS_02 = b'type="blacksmiths_02"'
BLACKSMITHS_01 = b'type="blacksmiths_01"'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def paired_case(day: int, source: dict, v3_path: Path) -> dict:
    melted = Path(source["rakaly_melted"]["path"]).read_bytes()
    raw = Path(source["source_save"]["path"]).read_bytes()
    require(sha256(raw) == source["source_save"]["sha256"], f"day {day} raw save changed")
    require(sha256(melted) == source["rakaly_melted"]["sha256"], f"day {day} melted save changed")
    require(sha256(v3_path.read_bytes()) == V3_SHA256[day], f"day {day} v3 changed")
    response = json.loads(v3_path.read_text(encoding="utf-8"))
    body = response["body"]
    matches = [(army, regiment)
               for army in body["combat_simulation_inputs"]["base_inputs"]["armies"]
               for regiment in army["regiments"] if regiment["regiment_id"] == 87]
    require(response["result"] == "CALL_COMPLETED" and body["status"] == "available"
            and body["target_province_id"] == 2633 and len(matches) == 1,
            f"day {day} v3 identity changed")
    army, regiment = matches[0]
    require(army["army_id"] == 16777221 and army["owner"]["character_id"] == 31549
            and regiment["effective_stats"]["toughness_raw"] == 2625000,
            f"day {day} v3 regiment/owner/toughness changed")
    marker = b"\n\t31549={\n"
    start = melted.find(marker)
    require(start >= 0 and melted.find(marker, start + 1) < 0,
            f"day {day} owner block not unique")
    end = melted.find(b"\n\t}\n", start + len(marker))
    require(end > start, f"day {day} owner block did not close")
    owner = melted[start:end]
    require(b"\n\t\tculture=7\n" in owner and b"\n\t\t\tunits={\n\t\t\t\t16777221\n" in owner,
            f"day {day} owner/culture/army save identity changed")
    require(EP1_KEY not in melted, f"day {day} EP1 timed modifier now serialized")
    require(BLACKSMITHS_02 not in melted, f"day {day} blacksmiths_02 now serialized")
    require(BLACKSMITHS_01 in melted and b"\n\t\ttimed_modifier={\n" in melted,
            f"day {day} positive-control serialization missing")
    return {
        "source_day": day,
        "source_save_sha256": source["source_save"]["sha256"],
        "melted_sha256": source["rakaly_melted"]["sha256"],
        "v3_sha256": V3_SHA256[day],
        "owner_character_id": 31549,
        "owner_culture_id_in_save": 7,
        "regiment_id": 87,
        "army_id": 16777221,
        "target_province_id": 2633,
        "effective_toughness_raw": 2625000,
        "ep1_modifier_serialized_count": melted.count(EP1_KEY),
        "blacksmiths_02_building_serialized_count": melted.count(BLACKSMITHS_02),
        "blacksmiths_01_positive_control_count": melted.count(BLACKSMITHS_01),
        "timed_modifier_positive_control_count": melted.count(b"\n\t\ttimed_modifier={\n"),
        "ep1_key_in_owner_record": EP1_KEY in owner,
    }


def project(args: argparse.Namespace) -> dict:
    require(sha256(args.exe.read_bytes()) == EXE_SHA256, "CK3 EXE is not the exact build")
    identity_bytes = args.identity_sidecar.read_bytes()
    require(sha256(identity_bytes) == IDENTITY_SHA256, "source-save identity sidecar changed")
    identity = json.loads(identity_bytes)
    require(identity["maa_type"]["key"] == "mubarizun"
            and identity["maa_type"]["base_toughness"] == 25,
            "MAA type/base changed")
    sources = {row["source_day"]: row for row in identity["source_cases"]}
    require(set(sources) == {11, 21}, "source day set changed")
    game = args.game_root
    modifiers = (game / "common/modifiers/01_dlc_ep1_modifiers.txt").read_bytes()
    event = (game / "events/dlc/ep1/ep1_flavor_events.txt").read_bytes()
    buildings = (game / "common/buildings/00_duchy_capital_buildings.txt").read_bytes()
    require(b"ep1_flavor_2020_both_modifier = {" in modifiers
            and b"army_toughness_mult = 0.05" in modifiers
            and b"modifier = ep1_flavor_2020_both_modifier" in event
            and b"add_character_modifier = {" in event
            and b"years = 5" in event,
            "EP1 scripted candidate changed")
    require(b"blacksmiths_02 = {" in buildings
            and b"heavy_infantry_toughness_mult = 0.05" in buildings
            and b"parameter = better_blacksmith_buildings" in buildings,
            "blacksmiths_02 scripted candidate changed")
    cases = [paired_case(day, sources[day], getattr(args, f"day{day}_v3"))
             for day in (11, 21)]
    return {
        "schema": "ck3.maa87_save_candidate_exclusion.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "identity_sidecar_sha256": IDENTITY_SHA256,
        "script_sha256": {
            "common/modifiers/01_dlc_ep1_modifiers.txt": sha256(modifiers),
            "events/dlc/ep1/ep1_flavor_events.txt": sha256(event),
            "common/buildings/00_duchy_capital_buildings.txt": sha256(buildings),
        },
        "frozen_cases": cases,
        "excluded_at_serialized_save_boundary": [
            "ep1_flavor_2020_both_modifier",
            "blacksmiths_02 character_culture_modifier +0.05",
        ],
        "same_frame_native_modifier_source_proven": False,
        "fixed_enum_values_observed": False,
        "effective_type_class_row_observed": False,
        "army_and_target_contributions_observed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--identity-sidecar", type=Path, required=True)
    parser.add_argument("--day11-v3", type=Path, required=True)
    parser.add_argument("--day21-v3", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check-sidecar", type=Path)
    args = parser.parse_args()
    result = project(args)
    if args.check_sidecar:
        require(json.loads(args.check_sidecar.read_text(encoding="utf-8")) == result,
                "save candidate exclusion sidecar changed")
        print(json.dumps({"ok": True, "sidecar_sha256": sha256(args.check_sidecar.read_bytes())}))
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"output": str(args.output), "sha256": sha256(args.output.read_bytes())}))


if __name__ == "__main__":
    main()
