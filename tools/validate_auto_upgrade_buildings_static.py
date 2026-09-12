#!/usr/bin/env python3
"""Static and installed-vanilla gate for Auto Upgrade Buildings."""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

import build_auto_upgrade_buildings_release as builder
import gen_auto_upgrade_buildings as generator
from auto_upgrade_buildings_data import CHAINS


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod_auto_upgrade_buildings"
FIXTURE = ROOT / "tools" / "fixtures" / "auto_upgrade_buildings_acceptance"
WORKSHOP_DESCRIPTION = ROOT / "workshop" / "auto_upgrade_buildings_description.bbcode"
DEFAULT_GAME_ROOT = Path(
    r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game"
)
LOC_KEYS = {
    "enable_auto_build",
    "enable_auto_build_tooltip",
    "enable_auto_build_desc",
    "enable_auto_build_text",
    "enable_auto_build_confirm",
    "disable_auto_build",
    "disable_auto_build_tooltip",
    "disable_auto_build_desc",
    "disable_auto_build_text",
    "disable_auto_build_confirm",
}


def text(relative: str) -> str:
    return (MOD / relative).read_bytes().decode("utf-8-sig")


def balanced_braces(value: str) -> bool:
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for char in value:
        if comment:
            if char == "\n":
                comment = False
            continue
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and char == "#":
            comment = True
        elif not quoted and char == "{":
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0 and not quoted


def localization_entries(value: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in value.splitlines()[1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r' ([A-Za-z0-9_]+):0 "((?:[^"\\]|\\.)*)"\s*', line)
        if match is None:
            raise ValueError(f"invalid localization row: {line!r}")
        key = match.group(1)
        if key in entries:
            raise ValueError(f"duplicate localization key: {key}")
        entries[key] = match.group(2)
    return entries


def extract_block(value: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", value)
    if match is None:
        return None
    depth = 0
    quoted = False
    escaped = False
    comment = False
    started = False
    for index in range(match.start(), len(value)):
        char = value[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and char == "#":
            comment = True
        elif not quoted and char == "{":
            started = True
            depth += 1
        elif not quoted and char == "}":
            depth -= 1
            if started and depth == 0:
                return value[match.start() : index + 1]
    return None


def validate_vanilla(game_root: Path) -> tuple[list[str], bool]:
    buildings = game_root / "common" / "buildings"
    innovations = game_root / "common" / "culture" / "innovations"
    if not buildings.is_dir() or not innovations.is_dir():
        return [], False
    errors: list[str] = []
    building_texts = [
        path.read_text(encoding="utf-8-sig", errors="strict")
        for path in sorted(buildings.glob("*.txt"))
    ]
    innovation_text = "\n".join(
        path.read_text(encoding="utf-8-sig", errors="strict")
        for path in sorted(innovations.rglob("*.txt"))
    )
    known_innovations = set(
        re.findall(r"(?m)^(innovation_[A-Za-z0-9_]+)\s*=\s*\{", innovation_text)
    )
    for item in CHAINS:
        for index, tier in enumerate(range(1, 9)):
            name = f"{item.name}_{tier:02d}"
            matches = [block for value in building_texts if (block := extract_block(value, name))]
            if len(matches) != 1:
                errors.append(f"vanilla building definition count is {len(matches)}: {name}")
                continue
            if tier >= 2:
                expected_cost = (
                    f"{item.cost_family}_building_tier_{item.cost_tiers[index - 1]}_cost"
                )
                if re.search(rf"(?m)^\s*cost_gold\s*=\s*{re.escape(expected_cost)}\s*$", matches[0]) is None:
                    errors.append(f"vanilla cost drift: {name} != {expected_cost}")
        for gate in item.innovations:
            for innovation in gate or ():
                if innovation not in known_innovations:
                    errors.append(f"vanilla innovation missing: {innovation}")
    return list(dict.fromkeys(errors)), True


def validate(game_root: Path = DEFAULT_GAME_ROOT) -> tuple[list[str], bool]:
    errors = builder.source_errors(MOD)
    descriptor = text("descriptor.mod").replace("\r\n", "\n")
    expected_descriptor = (
        'version="1.19.0"\n'
        'tags={\n\t"Balance"\n}\n'
        'name="自动升级建筑（XenoAmess维护版）"\n'
        'supported_version="1.19.0.6"\n'
    )
    if descriptor != expected_descriptor:
        errors.append("descriptor.mod differs from the 1.19.0.6 maintenance contract")

    decisions = text("common/decisions/build_decision.txt")
    events = text("events/auto_build.txt")
    effects = text("common/scripted_effects/build_scripted_effect.txt")
    for relative, value in (
        ("common/decisions/build_decision.txt", decisions),
        ("events/auto_build.txt", events),
        ("common/scripted_effects/build_scripted_effect.txt", effects),
    ):
        if not balanced_braces(value):
            errors.append(f"unbalanced Clausewitz text: {relative}")
    if (MOD / "common/scripted_effects/build_scripted_effect.txt").read_bytes() != generator.render().encode("utf-8-sig"):
        errors.append("generated scripted effects are stale")

    if re.findall(r"(?m)^auto_build\.(\d+)\s*=\s*\{", events) != [
        "0003",
        "0004",
        "0005",
    ]:
        errors.append("event inventory must preserve compatibility 0003/0004 and unique loop 0005")
    combined = decisions + "\n" + events + "\n" + effects
    if "AUBT:" in combined or "aubt_" in combined or "aubt." in combined:
        errors.append("acceptance fixture markers leaked into production runtime")
    if "prev" in combined:
        errors.append("implicit prev scope is forbidden")
    if re.search(r"(?<!directly_owned_)every_province\s*=", events):
        errors.append("global every_province scan is forbidden")
    required_event_fragments = (
        "every_directly_owned_province = {",
        "has_ongoing_construction = no",
        "save_scope_as = aub_payer",
        "save_scope_as = holder",
        "save_scope_as = build_owner",
        "has_holding_type = castle_holding",
        "has_holding_type = city_holding",
        "has_holding_type = church_holding",
        "scope = none",
        "any_player = {",
        "every_player = {",
        "trigger_event = { id = auto_build.0005 days = 15 }",
        "remove_global_variable = aub_auto_build_loop_started",
    )
    for fragment in required_event_fragments:
        if fragment not in events:
            errors.append(f"runtime loop contract missing: {fragment}")
    if combined.count("has_character_flag = enable_auto_build") < 5:
        errors.append("enable_auto_build compatibility flag is not fully wired")
    if decisions.count("is_ai = no") < 4 or events.count("is_ai = no") < 4:
        errors.append("human-player gates are incomplete")
    if "id = auto_build.0003" not in decisions:
        errors.append("enable decision does not enter the compatibility loop seed")
    if "ai_check_frequency" in decisions or decisions.count("ai_check_interval = 0") != 2:
        errors.append("decisions must use CK3 1.19 ai_check_interval syntax")
    if "auto_build.0001" in events:
        errors.append("unreferenced upstream auto_build.0001 must not be restored")
    if effects.count("aub_start_global_loop_effect = {") != 1:
        errors.append("global loop seed effect must be defined exactly once")
    if effects.count("aub_upgrade_") != 43 * 2 + 1:
        errors.append("generated building chain call/definition inventory drifted")

    languages = (
        ("english", "l_english"),
        ("french", "l_french"),
        ("german", "l_german"),
        ("japanese", "l_japanese"),
        ("korean", "l_korean"),
        ("polish", "l_polish"),
        ("russian", "l_russian"),
        ("simp_chinese", "l_simp_chinese"),
        ("spanish", "l_spanish"),
    )
    localized_entries: dict[str, dict[str, str]] = {}
    for language, header in languages:
        relative = f"localization/{language}/auto_build_l_{language}.yml"
        value = text(relative)
        if value.splitlines()[0] != f"{header}:":
            errors.append(f"wrong localization header: {relative}")
            continue
        try:
            entries = localization_entries(value)
        except ValueError as error:
            errors.append(f"{relative}: {error}")
            continue
        if set(entries) != LOC_KEYS:
            errors.append(f"localization key inventory mismatch: {relative}")
        if any(not item.strip() for item in entries.values()):
            errors.append(f"blank localization value: {relative}")
        localized_entries[language] = entries

    english_entries = localized_entries.get("english", {})
    for language, _ in languages:
        entries = localized_entries.get(language, {})
        if language not in {"english", "simp_chinese"}:
            for key in sorted(LOC_KEYS & english_entries.keys() & entries.keys()):
                if entries[key] == english_entries[key]:
                    errors.append(f"English localization placeholder remains: {language}:{key}")
        for key in sorted(LOC_KEYS & english_entries.keys() & entries.keys()):
            tokens = (r"\n",)
            if language != "simp_chinese":
                tokens += ("CK3", "1.19.0.6", "Mandala")
            for token in tokens:
                if entries[key].count(token) != english_entries[key].count(token):
                    errors.append(
                        f"localization protected-token mismatch: {language}:{key}:{token}"
                    )

    thumbnail = MOD / "thumbnail.png"
    data = thumbnail.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24:
        errors.append("thumbnail.png is not a PNG")
    elif struct.unpack(">II", data[16:24]) != (600, 600):
        errors.append("upstream thumbnail.png must remain 600x600")

    fixture_files = {
        "descriptor.mod",
        "common/on_action/aubt_on_actions.txt",
        "events/aubt_events.txt",
        "localization/english/aubt_l_english.yml",
        "localization/simp_chinese/aubt_l_simp_chinese.yml",
    }
    actual_fixture_files = {
        path.relative_to(FIXTURE).as_posix()
        for path in FIXTURE.rglob("*")
        if path.is_file()
    } if FIXTURE.is_dir() else set()
    if actual_fixture_files != fixture_files:
        errors.append(
            "acceptance fixture inventory mismatch: "
            f"{sorted(actual_fixture_files)} != {sorted(fixture_files)}"
        )
    fixture_script = ""
    for relative in sorted(actual_fixture_files):
        path = FIXTURE / relative
        payload = path.read_bytes()
        if path.suffix.lower() in {".txt", ".yml"} and not payload.startswith(b"\xef\xbb\xbf"):
            errors.append(f"acceptance fixture lacks UTF-8 BOM: {relative}")
        value = payload.decode("utf-8-sig", errors="replace")
        if path.suffix.lower() == ".txt":
            fixture_script += value + "\n"
            if not balanced_braces(value):
                errors.append(f"acceptance fixture has unbalanced braces: {relative}")
    for marker in (
        "AUBT: TEST BEGIN source-live",
        "AUBT: TEST PASS treasury_priority_one_tier",
        "AUBT: TEST PASS disabled_zero_side_effect",
        "AUBT: TEST PASS personal_gold_fallback",
        "AUBT: TEST PASS reenabled_loop_stopped_cleanly",
        "AUBT: TEST PASS insufficient_funds_no_change",
        "AUBT: TEST DONE source-live",
    ):
        if fixture_script.count(marker) != 1:
            errors.append(f"acceptance fixture marker count drifted: {marker}")
    if "on_game_start_after_lobby = {" not in fixture_script:
        errors.append("acceptance fixture is not wired to the post-lobby start")
    for fragment in (
        "change_government = celestial_government",
        "has_treasury = yes",
        "change_government = feudal_government",
    ):
        if fragment not in fixture_script:
            errors.append(f"acceptance resource-route contract missing: {fragment}")
    if re.search(r"(?m)^\s*remove_gold\s*=", fixture_script):
        errors.append("acceptance fixture uses unsupported CK3 1.19 remove_gold effect")

    if not WORKSHOP_DESCRIPTION.is_file():
        errors.append("Auto Upgrade Buildings Workshop description is missing")
    else:
        workshop_description = WORKSHOP_DESCRIPTION.read_text(encoding="utf-8")
        for fragment in (
            "[h1]自动升级建筑（XenoAmess维护版）[/h1]",
            "[h1]原作、致谢与授权[/h1]",
            "[url=https://steamcommunity.com/sharedfiles/filedetails/?id=3596580780]自动升级建筑（新版）[/url]",
            "致谢：[/b]感谢原 Mod 作者的创作与维护劳动，本维护版以原作提供的玩法和内容为基础。",
            "授权说明：[/b]本维护版已获得原 Mod 作者授权进行二次开发与发布。",
            "[url=https://github.com/XenoAmess/ck3_eternal_recurrence]源码与问题反馈[/url]",
        ):
            if workshop_description.count(fragment) != 1:
                errors.append(f"Workshop publication contract drifted: {fragment}")

    vanilla_errors, vanilla_checked = validate_vanilla(game_root)
    errors.extend(vanilla_errors)
    return errors, vanilla_checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME_ROOT)
    args = parser.parse_args(argv)
    errors, vanilla_checked = validate(args.game_root)
    if errors:
        print("AUTO UPGRADE BUILDINGS STATIC VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "AUTO UPGRADE BUILDINGS STATIC VALIDATION OK\n"
        f"Runtime files: {len(builder.RUNTIME_FILES)}\n"
        f"Building chains: {len(CHAINS)}\n"
        f"Installed vanilla 1.19 metadata checked: {'yes' if vanilla_checked else 'not installed'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
