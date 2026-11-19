"""Validate de jure conquest's player, target, outcome and packaging contracts."""

from __future__ import annotations

import argparse
import io
from collections.abc import Iterator
from typing import Literal, TypedDict
import hashlib
import json
from pathlib import Path
import re
import sys

from product import CB_CONTRACT, EXPECTED_GAME_VERSION, LANGUAGES, ROOT, RUNTIME_FILES, SOURCE, SUPPORTED_VERSION, UPSTREAM_ITEM_ID, VERSION

sys.path.insert(0, str(ROOT / "tools"))
from extract_auto_upgrade_buildings import Block, Entry, ExtractionError, parse_clausewitz
from translate_localization_minimax import parse_ck3_localization

DEFAULT_GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III")
VANILLA_HASHES: dict[str, str] = {'game/common/casus_belli_types/_casus_belli.info': 'b2dca405667a9917cc88e3dcf2a9aef54ac216f82c49e74b5459d45ab0694006', 'game/common/casus_belli_types/00_invasion_war.txt': 'ddf5e871a44382dac37a48c2efe3d29f5384d80afda190a2a5f76a8628776335', 'game/common/casus_belli_types/00_religious_war.txt': '731b7554b81ca95dd1e5150636f552e8e84d758b1a03d6b44cf7cdb4e5f7a102', 'game/common/casus_belli_types/00_dejure_war.txt': '8845415e78bf69ca62144758c36b131cb0fbf4f5d5e98fe5fb40725fd5b19eed', 'game/common/on_action/war_on_actions.txt': 'd90b0d6d9c63f09a37a0b9eff485d6c0004411d08127eeb2d3833fa2b21db28b', 'game/common/scripted_effects/00_war_effects.txt': '6741fbd7477f0e995c783d70f148d8fe6017d0046ed5261811496ff67d455807', 'game/common/scripted_effects/00_casus_belli_effects.txt': 'ca301ea28dfcd29995972ded9a51d5b9c5a3f180901d938c0acac02ccc55856f', 'game/common/scripted_effects/00_accolades_scripted_effects.txt': '14f55d1163d773900d2be778e9815616fe30a19cf648404769d80efc3ef2e787', 'game/common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt': 'e32cb4689912f2e947dc41ba99f54b94d6936298dfadfdf1dca3e87e82a7668e', 'game/common/scripted_effects/01_dlc_fp1_scripted_effects.txt': '440bda9974bed482b305d55f26d6a69dc144ae590ce89337f1640056b0921d4a', 'game/common/scripted_effects/07_dlc_ep3_scripted_effects.txt': '7d2b758d3edfa0ea124d5c76aed92ad0b5054db578759c17d3e0c54b5e6f0d2a', 'game/common/script_values/99_casus_belli_values.txt': 'd3c920b32669eb6d82f9f569c20c63a0627452480f566784b41f91ff4450da0f', 'game/common/script_values/00_war_values.txt': 'f8fc912174740be27fe8f323ae52ac39903d0580a72dc27a415f7aaa4509acbf', 'game/common/script_values/01_dynamic_values.txt': 'e782c5a720b2704e23feef3add2252a059aa8340c9f43b216ea9fc28eb91559c', 'game/common/script_values/00_stress_values.txt': '821a0b77244fc5ee2d87d339cb24dbef00787b83d44ec2df9215fc1a93aec2d4', 'game/common/opinion_modifiers/00_war_opinions.txt': '750864482d2d6c5d268424a1e03cba24301dedf853722d7fc12cb6f9fbcc68dc', 'game/common/story_cycles/ep3_story_cycle_frankokratia.txt': '333577c6b7f47de46422a5ca2ac0f116829ff7c7c604eb16e9eefb17e6997839'}


class StaticReport(TypedDict):
    result: Literal["RED", "GREEN"]
    layer: Literal["L0-static"]
    errors: list[str]
    runtime_allowlist_count: int
    checked_runtime_file_count: int
    release_localization: bool
    runtime_sha256: dict[str, str]
    vanilla_sha256: dict[str, str]
    live: Literal["NOT_RUN"]


def one(block: Block, key: str) -> Entry:
    entries = [entry for entry in block.entries if entry.key == key]
    if len(entries) != 1:
        raise ValueError(f"expected one {key}, found {len(entries)}")
    return entries[0]


def as_block(value: str | Block | None, context: str) -> Block:
    if not isinstance(value, Block):
        raise ValueError(f"{context} must be a block")
    return value


def block(parent: Block, key: str) -> Block:
    return as_block(one(parent, key).value, key)


def scalar_value(parent: Block, key: str) -> str:
    value = one(parent, key).value
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a scalar")
    return value


def scalar(block: Block, key: str, expected: str) -> None:
    if one(block, key).value != expected:
        raise ValueError(f"{key} must equal {expected}")


def descendants(block: Block) -> Iterator[Entry]:
    for entry in block.entries:
        yield entry
        if isinstance(entry.value, Block):
            yield from descendants(entry.value)


def localization(path: Path) -> dict[str, str]:
    # File format only: no translation-quality, terminology or live-language gate.
    parse_ck3_localization(path)
    value = path.read_text(encoding="utf-8-sig")
    language = path.parent.name
    if value.splitlines()[0] != f"l_{language}:":
        raise ValueError(f"wrong localization header: {path.name}")
    result = {}
    for line in value.splitlines()[1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r' ([A-Za-z0-9_]+):0 "((?:[^"\\]|\\.)*)"\s*', line)
        if not match or match.group(1) in result:
            raise ValueError(f"invalid or duplicate localization row: {path.name}: {line}")
        result[match.group(1)] = match.group(2)
    return result


def validate(game: Path | None = DEFAULT_GAME, *, release_localization: bool = False) -> StaticReport:
    errors: list[str] = []
    scripts: dict[str, Block] = {}
    hashes: dict[str, str] = {}
    for relative in sorted(RUNTIME_FILES):
        if relative.startswith("localization/") and not release_localization and relative.split("/")[1] not in {"english", "simp_chinese"}:
            continue
        path = SOURCE / relative
        if not path.is_file():
            errors.append(f"missing runtime file: {relative}")
            continue
        data = path.read_bytes()
        hashes[relative] = hashlib.sha256(data).hexdigest()
        if path.suffix in {".txt", ".yml"} and not data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"missing BOM: {relative}")
        if path.suffix in {".txt", ".mod", ".yml"}:
            value = data.decode("utf-8-sig")
            if "remote_file_id" in value or UPSTREAM_ITEM_ID in value:
                errors.append(f"upstream publishing identity in runtime: {relative}")
            if path.suffix == ".txt":
                try:
                    scripts[relative] = parse_clausewitz(value)
                except ExtractionError as error:
                    errors.append(f"parse: {relative}: {error}")
    try:
        descriptor = (SOURCE / "descriptor.mod").read_bytes()
        if descriptor.startswith(b"\xef\xbb\xbf"):
            raise ValueError("descriptor must not have BOM")
        expected = f'version="{VERSION}"\ntags={{\n\t"Balance"\n}}\nname="公国／王国／帝国法理征服（XenoAmess维护版）"\nsupported_version="{SUPPORTED_VERSION}"\npicture="thumbnail.png"\n'
        from workshop_compatibility_tags import render_workshop_descriptor_bytes
        expected = render_workshop_descriptor_bytes(expected.encode("utf-8")).decode("utf-8")
        if descriptor.decode("utf-8") != expected:
            raise ValueError("descriptor identity changed")
        english = localization(SOURCE / "localization/english/greatwar_l_english.yml")
        chinese = localization(SOURCE / "localization/simp_chinese/greatwar_l_simp_chinese.yml")
        if english.keys() != chinese.keys():
            raise ValueError("English/Chinese localization keys differ")
        if release_localization:
            for language in LANGUAGES:
                entries = localization(SOURCE / f"localization/{language}/greatwar_l_{language}.yml")
                if entries.keys() != english.keys():
                    raise ValueError(f"release localization keys differ: {language}")
        for tier, contract in CB_CONTRACT.items():
            top = scripts[f"common/casus_belli_types/{tier}_de_jure_greatwar.txt"]
            if [entry.key for entry in top.entries] != [f"{tier}_de_jure_greatwar"]:
                raise ValueError(f"public CB ID changed: {tier}")
            cb = block(top, f"{tier}_de_jure_greatwar")
            if len({entry.key for entry in cb.entries}) != len(cb.entries):
                raise ValueError(f"duplicate CB fields: {tier}")
            scalar(cb, "ai", "no")
            scalar(cb, "is_great_holy_war", "no")
            scalar(cb, "check_all_defenders_for_ticking_war_score", "yes")
            scalar(cb, "use_de_jure_wargoal_only", "yes")
            allowed = block(cb, "allowed_for_character")
            scalar(allowed, "is_ai", "no")
            prestige = one(allowed, "prestige_level")
            if prestige.operator != ">=" or prestige.value != contract["prestige_level"]:
                raise ValueError(f"prestige level changed: {tier}")
            scalar(block(block(cb, "valid_to_start"), "scope:target"), "tier", f"tier_{tier}")
            cost = block(cb, "cost")
            scalar(block(cost, "piety"), "value", contract["piety"])
            scalar(block(block(cost, "prestige"), "add"), "value", contract["prestige"])
            scalar(block(cb, "mutually_exclusive_titles"), "always", "yes")
            declaration = block(cb, "on_declaration")
            scalar(block(declaration, "djc_join_de_jure_defenders"), "WAR", "root.war")
            for key in ["war_name", "cb_name", "on_victory_desc", "on_white_peace_desc", "on_defeat_desc"]:
                loc_key = scalar_value(cb, key).strip('"')
                if loc_key not in english:
                    raise ValueError(f"unlocalized {tier}.{key}: {loc_key}")
            for key in ["on_victory", "on_white_peace", "on_defeat"]:
                branch = block(block(cb, key), "if")
                scalar(block(branch, "limit"), "exists", "root.war")
        effects = scripts["common/scripted_effects/djc_war_effects.txt"]
        if [entry.key for entry in effects.entries] != ["djc_join_de_jure_defenders", "djc_transfer_de_jure_counties"]:
            raise ValueError("shared helper IDs changed")
        for effect in effects.entries:
            branch = block(as_block(effect.value, effect.key), "if")
            scalar(block(branch, "limit"), "exists", "$WAR$")
        raw_hook = (SOURCE / "common/on_action/greatwar.txt").read_text(encoding="utf-8-sig")
        if "primary_attacker = { is_ai = no }" not in raw_hook:
            raise ValueError("compatibility war-start hook lacks player guard")
        if "scope:war.casus_belli = {" in raw_hook:
            raise ValueError("war-start hook must not reconstruct the native declaration target list")
        raw_effects = (SOURCE / "common/scripted_effects/djc_war_effects.txt").read_text(encoding="utf-8-sig")
        for fragment in ["top_liege = {", "NOT = { is_participant_in_war = scope:djc_current_war }", "this != scope:attacker", "NOT = { is_vassal_or_below_of = scope:attacker }", "is_defender_in_war = scope:djc_current_war", "resolve_title_and_vassal_change = scope:change"]:
            if fragment not in raw_effects:
                raise ValueError(f"title/participant contract missing: {fragment}")
        if "vassals_taken" in raw_effects:
            raise ValueError("unused upstream temporary vassal list must not return")
        joining = block(block(effects, "djc_join_de_jure_defenders"), "if")
        native_goals = block(joining, "every_in_list")
        scalar(native_goals, "list", "target_titles")
        goal_capture = block(block(native_goals, "scope:djc_current_war"), "set_variable")
        scalar(goal_capture, "name", "djc_goal_title")
        scalar(goal_capture, "value", "scope:djc_native_goal")
    except (OSError, KeyError, AttributeError, ValueError) as error:
        errors.append(str(error))
    vanilla: dict[str, str] = {}
    if game is not None:
        for relative, expected in VANILLA_HASHES.items():
            path = game / relative
            if not path.is_file():
                errors.append(f"missing vanilla input: {relative}")
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            vanilla[relative] = digest
            if expected and digest != expected:
                errors.append(f"exact-build vanilla differs: {relative}")
        settings = game / "launcher/launcher-settings.json"
        try:
            version_data: object = json.loads(settings.read_text(encoding="utf-8-sig"))
            if not isinstance(version_data, dict) or type(version_data.get("rawVersion")) is not str or version_data.get("rawVersion") != EXPECTED_GAME_VERSION:
                errors.append(f"installed game version is not reviewed {EXPECTED_GAME_VERSION}")
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"installed game version metadata invalid: {error}")
    return {"result": "RED" if errors else "GREEN", "layer": "L0-static", "errors": errors, "runtime_allowlist_count": len(RUNTIME_FILES), "checked_runtime_file_count": len(hashes), "release_localization": release_localization, "runtime_sha256": hashes, "vanilla_sha256": vanilla, "live": "NOT_RUN"}


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME, help="CK3 installation root containing game/ and launcher/")
    parser.add_argument("--no-installed-game", action="store_true")
    parser.add_argument("--release-localization", action="store_true", help="check all nine localization file formats and keys; no semantic review or game launch")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = validate(None if args.no_installed_game else args.game, release_localization=args.release_localization)
    if args.report:
        if args.report.exists():
            parser.error("report target already exists; use a fresh attempt")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
