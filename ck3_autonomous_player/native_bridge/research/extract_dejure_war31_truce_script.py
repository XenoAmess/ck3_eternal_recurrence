"""Freeze the stock 1.19.0.6 War 31 de-jure victory truce script chain.

This reads game text and the Git-frozen R0221 request. It never evaluates CK3
script values, calls game code, or predicts a persisted truce expiry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


STOCK_SHA256 = {
    "common/casus_belli_types/00_dejure_war.txt": "D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE",
    "common/scripted_effects/00_war_effects.txt": "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D",
    "common/script_values/00_war_values.txt": "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B",
}
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
REQUEST_ID = "WAR-INPUT-R0221-WAR31-20260927"


def _block(source: str, name: str) -> str:
    starts = list(re.finditer(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", source))
    if len(starts) != 1:
        raise ValueError(f"expected exactly one {name} block, found {len(starts)}")
    opening = source.index("{", starts[0].start())
    return _block_at(source, opening, name)


def _block_at(source: str, opening: int, name: str) -> str:
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : index]
    raise ValueError(f"unterminated {name} block")


def _assignment(source: str, key: str, expected_value: str) -> None:
    matches = re.findall(rf"(?m)^\s*{re.escape(key)}\s*=\s*([^#\r\n]+)", source)
    if [value.strip() for value in matches] != [expected_value]:
        raise ValueError(f"unexpected {key} assignment: {matches!r}")


def extract(game_dir: Path, request_path: Path) -> dict[str, object]:
    sources: dict[str, str] = {}
    for relative, expected_hash in STOCK_SHA256.items():
        raw = (game_dir / "game" / relative).read_bytes()
        if hashlib.sha256(raw).hexdigest().upper() != expected_hash:
            raise ValueError(f"wrong stock build or changed game script: {relative}")
        sources[relative] = raw.decode("utf-8-sig")
    exe = game_dir / "binaries/ck3.exe"
    if hashlib.sha256(exe.read_bytes()).hexdigest().upper() != EXE_SHA256:
        raise ValueError("CK3 executable differs from frozen 1.19.0.6 build")

    request_raw = request_path.read_bytes()
    request = json.loads(request_raw)
    frame = request["reproduction"]
    if (
        request["request_id"] != REQUEST_ID
        or request["source"]["ck3_exe_sha256"] != EXE_SHA256
        or frame["war_id"] != 16777231
        or frame["casus_belli_key"] != "individual_county_de_jure_cb"
        or frame["player_side"] != "defender"
        or not frame["player_is_primary_war_leader"]
        or frame["played_character_id"] != 29829
        or frame["primary_opponent_character_id"] != 30097
    ):
        raise ValueError("R0221 identity is not the frozen primary-defender War 31 frame")

    cb = _block(sources["common/casus_belli_types/00_dejure_war.txt"], frame["casus_belli_key"])
    victory = _block(cb, "on_victory")
    _assignment(victory, "add_truce_attacker_victory_effect", "yes")

    effect = _block(sources["common/scripted_effects/00_war_effects.txt"], "add_truce_attacker_victory_effect")
    if len(re.findall(r"(?m)^\s*add_truce_one_way\s*=\s*\{", effect)) != 1:
        raise ValueError("victory effect does not contain exactly one one-way truce leaf")
    attacker_scopes = [
        _block_at(effect, effect.index("{", match.start()), "scope:attacker")
        for match in re.finditer(r"(?m)^\s*scope:attacker\s*=\s*\{", effect)
    ]
    matching_scopes = [scope for scope in attacker_scopes if "add_truce_one_way = {" in scope]
    if len(matching_scopes) != 1:
        raise ValueError("one-way truce is not uniquely within attacker scope")
    truce = _block(matching_scopes[0], "add_truce_one_way")
    for key, expected in (
        ("character", "scope:defender"),
        ("days", "standard_truce_duration_days"),
        ("war", "root.war"),
        ("result", "victory"),
    ):
        _assignment(truce, key, expected)

    duration = _block(sources["common/script_values/00_war_values.txt"], "standard_truce_duration_days")
    for required in (
        "value = 1825", "has_perk = flexible_truces_perk", "add = -450",
        "truces_by_involved_or_interlopers_within_region_shorter", "add = -900",
        "truces_by_involved_or_interlopers_within_region_longer", "add = 900",
        "government_is_nomadic", "subtract = 730", "min = 730",
        "using_cb = fp2_border_raid", "multiply = 2",
    ):
        if required not in duration:
            raise ValueError(f"duration formula changed: {required}")

    return {
        "schema": "xar.ck3.war31.dejure_truce_script.v1",
        "source": "stock-ck3-1.19.0.6-scripts-plus-R0221-identity",
        "exe_sha256": EXE_SHA256,
        "stock_script_sha256": STOCK_SHA256,
        "request_id": REQUEST_ID,
        "request_sha256": hashlib.sha256(request_raw).hexdigest().upper(),
        "war_id": frame["war_id"],
        "paused_date_raw": frame["paused_date_raw"],
        "scripted_on_victory": {
            "outcome": "attacker_victory",
            "effect": "add_truce_attacker_victory_effect",
            "truce_owner_role": "primary_attacker",
            "truce_owner_character_id": frame["primary_opponent_character_id"],
            "toward_role": "primary_defender",
            "toward_character_id": frame["played_character_id"],
            "direction": "one_way",
            "result_argument": "victory",
            "days_script_value": "standard_truce_duration_days",
        },
        "duration_formula": {
            "base_days": 1825,
            "attacker_flexible_truces_perk_add_days": -450,
            "shorter_struggle_add_days": -900,
            "longer_struggle_add_days": 900,
            "both_nomadic_subtract_days": 730,
            "minimum_days_before_border_raid_multiplier": 730,
            "matching_border_raid_war_multiplier": 2,
            "dynamic_conditions_observed_in_R0221": False,
        },
        "actual_evaluated_days": None,
        "actual_expiry_date_raw": None,
        "material_terms_status": "script_static_only_not_applied_or_observed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(extract(args.game_dir, args.request), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
