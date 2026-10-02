"""Validate de jure conquest's player, target, outcome and packaging contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from product import CB_CONTRACT, LANGUAGES, ROOT, RUNTIME_FILES, SOURCE, SUPPORTED_VERSION, UPSTREAM_ITEM_ID, VERSION

sys.path.insert(0, str(ROOT / "tools"))
from extract_auto_upgrade_buildings import Block, Entry, ExtractionError, parse_clausewitz
from translate_localization_minimax import parse_ck3_localization

DEFAULT_GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III")
VANILLA_HASHES = {
    "game/common/casus_belli_types/_casus_belli.info": "270343ebae0f8ebd2e4d24f9f839a7c77cb663836d9b36af6d5138a58755bb05",
    "game/common/casus_belli_types/00_invasion_war.txt": "4dc22705345fbe614f755d2b8510fd5e4dde51991e72d4d71f6faeafacd39abc",
    "game/common/casus_belli_types/00_religious_war.txt": "5c4b6af8742f65a720529434a2997e83ec93b6cfa8d594204ca914ae6c359d33",
    "game/common/casus_belli_types/00_dejure_war.txt": "18c0d3647fd936b37e3d26e28980ec45657841414d6397667891ad2e73ac1f85",
}


def one(block: Block, key: str) -> Entry:
    entries = [entry for entry in block.entries if entry.key == key]
    if len(entries) != 1:
        raise ValueError(f"expected one {key}, found {len(entries)}")
    return entries[0]


def scalar(block: Block, key: str, expected: str) -> None:
    if one(block, key).value != expected:
        raise ValueError(f"{key} must equal {expected}")


def descendants(block: Block):
    for entry in block.entries:
        yield entry
        if isinstance(entry.value, Block):
            yield from descendants(entry.value)


def localization(path: Path) -> dict[str, str]:
    # Use the same strict parser as formal translation, before extra checks.
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


def validate(game: Path | None = DEFAULT_GAME, *, release_localization: bool = False) -> dict:
    errors = []
    scripts = {}
    hashes = {}
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
                if language not in {"english", "simp_chinese"} and entries == english:
                    raise ValueError(f"release localization is an English placeholder: {language}")
        for tier, contract in CB_CONTRACT.items():
            top = scripts[f"common/casus_belli_types/{tier}_de_jure_greatwar.txt"]
            if [entry.key for entry in top.entries] != [f"{tier}_de_jure_greatwar"]:
                raise ValueError(f"public CB ID changed: {tier}")
            cb = top.entries[0].value
            if len({entry.key for entry in cb.entries}) != len(cb.entries):
                raise ValueError(f"duplicate CB fields: {tier}")
            scalar(cb, "ai", "no")
            scalar(cb, "is_great_holy_war", "no")
            scalar(cb, "check_all_defenders_for_ticking_war_score", "yes")
            scalar(cb, "use_de_jure_wargoal_only", "yes")
            allowed = one(cb, "allowed_for_character").value
            scalar(allowed, "is_ai", "no")
            prestige = one(allowed, "prestige_level")
            if prestige.operator != ">=" or prestige.value != contract["prestige_level"]:
                raise ValueError(f"prestige level changed: {tier}")
            scalar(one(one(cb, "valid_to_start").value, "scope:target").value, "tier", f"tier_{tier}")
            cost = one(cb, "cost").value
            scalar(one(cost, "piety").value, "value", contract["piety"])
            scalar(one(one(cost, "prestige").value, "add").value, "value", contract["prestige"])
            for key in ["war_name", "cb_name", "on_victory_desc", "on_white_peace_desc", "on_defeat_desc"]:
                loc_key = one(cb, key).value.strip('"')
                if loc_key not in english:
                    raise ValueError(f"unlocalized {tier}.{key}: {loc_key}")
            for key in ["on_victory", "on_white_peace", "on_defeat"]:
                branch = one(one(cb, key).value, "if").value
                scalar(one(branch, "limit").value, "exists", "root.war")
        effects = scripts["common/scripted_effects/djc_war_effects.txt"]
        if [entry.key for entry in effects.entries] != ["djc_join_de_jure_defenders", "djc_transfer_de_jure_counties"]:
            raise ValueError("shared helper IDs changed")
        for effect in effects.entries:
            branch = one(effect.value, "if").value
            scalar(one(branch, "limit").value, "exists", "$WAR$")
        raw_hook = (SOURCE / "common/on_action/greatwar.txt").read_text(encoding="utf-8-sig")
        if "scope:war.casus_belli = {" not in raw_hook or "primary_attacker = { is_ai = no }" not in raw_hook:
            raise ValueError("war-start hook lacks CB scope or player guard")
        raw_effects = (SOURCE / "common/scripted_effects/djc_war_effects.txt").read_text(encoding="utf-8-sig")
        for fragment in ["top_liege = {", "NOT = { is_participant_in_war = scope:djc_current_war }", "this != scope:attacker", "NOT = { is_vassal_or_below_of = scope:attacker }", "is_defender_in_war = scope:djc_current_war", "resolve_title_and_vassal_change = scope:change"]:
            if fragment not in raw_effects:
                raise ValueError(f"title/participant contract missing: {fragment}")
        if "vassals_taken" in raw_effects:
            raise ValueError("unused upstream temporary vassal list must not return")
    except (OSError, KeyError, AttributeError, ValueError) as error:
        errors.append(str(error))
    vanilla = {}
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
        if not settings.is_file() or json.loads(settings.read_text(encoding="utf-8-sig")).get("rawVersion") != "1.20.0.3":
            errors.append("installed game version is not frozen 1.20.0.3")
    return {"result": "RED" if errors else "GREEN", "layer": "L0-static", "errors": errors, "runtime_allowlist_count": len(RUNTIME_FILES), "checked_runtime_file_count": len(hashes), "release_localization": release_localization, "runtime_sha256": hashes, "vanilla_sha256": vanilla, "live": "NOT_RUN"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
    parser.add_argument("--no-installed-game", action="store_true")
    parser.add_argument("--release-localization", action="store_true")
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
