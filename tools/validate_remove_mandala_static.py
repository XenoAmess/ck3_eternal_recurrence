#!/usr/bin/env python3
"""Static release gate for the standalone Mandala Purge mod."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

import build_remove_mandala_release as builder
import compose_remove_mandala_key_art as art


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod_remove_mandala"
LOC_KEYS = {
    "rule_mrm_remove_mandala",
    "setting_mrm_enabled",
    "setting_mrm_enabled_desc",
    "setting_mrm_disabled",
    "setting_mrm_disabled_desc",
}
LANGUAGES = {
    "english": "l_english",
    "french": "l_french",
    "german": "l_german",
    "japanese": "l_japanese",
    "korean": "l_korean",
    "polish": "l_polish",
    "russian": "l_russian",
    "simp_chinese": "l_simp_chinese",
    "spanish": "l_spanish",
}


def text(relative: str) -> str:
    return (MOD / relative).read_bytes().decode("utf-8-sig")


def balanced_braces(value: str) -> bool:
    depth = 0
    for line in value.splitlines():
        line = line.split("#", 1)[0]
        quoted = False
        escaped = False
        for char in line:
            if escaped:
                escaped = False
            elif char == "\\" and quoted:
                escaped = True
            elif char == '"':
                quoted = not quoted
            elif not quoted and char == "{":
                depth += 1
            elif not quoted and char == "}":
                depth -= 1
                if depth < 0:
                    return False
    return depth == 0


def loc_entries(value: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in value.splitlines()[1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r' ([A-Za-z0-9_]+):0 "((?:[^"\\]|\\.)*)"', line)
        if match is None:
            raise ValueError(f"invalid localization row: {line!r}")
        if match.group(1) in entries:
            raise ValueError(f"duplicate localization key: {match.group(1)}")
        entries[match.group(1)] = match.group(2)
    return entries


def validate() -> list[str]:
    errors = builder.release_source_errors(MOD)
    descriptor = text("descriptor.mod")
    expected_descriptor = (
        'version="1.0.0"\n'
        'tags={\n\t"Gameplay"\n}\n'
        'name="Mandala Purge — 肃清曼荼罗伪信"\n'
        'picture="thumbnail.png"\n'
        'supported_version="1.19.0.6"\n'
    )
    if descriptor.replace("\r\n", "\n") != expected_descriptor:
        errors.append("descriptor.mod fields or ordering differ from the release contract")

    script_paths = [
        "common/game_rules/mrm_game_rules.txt",
        "common/on_action/mrm_on_actions.txt",
        "common/scripted_effects/mrm_effects.txt",
        "events/mrm_events.txt",
    ]
    for relative in script_paths:
        if not balanced_braces(text(relative)):
            errors.append(f"unbalanced braces: {relative}")
    all_script = "\n".join(text(relative) for relative in script_paths)
    written_governments = re.findall(
        r"change_government\s*=\s*([A-Za-z0-9_]+)", all_script
    )
    if not written_governments or set(written_governments) != {"wanua_government"}:
        errors.append(
            "every product government transition must target only wanua_government: "
            f"{written_governments}"
        )

    rules = text(script_paths[0])
    for fragment in (
        "mrm_remove_mandala = {",
        "categories = {\n\t\tgame_modes",
        "default = mrm_enabled",
        "mrm_enabled = { }",
        "mrm_disabled = { }",
    ):
        if fragment not in rules:
            errors.append(f"game-rule contract missing: {fragment}")
    if rules.count("default =") != 1:
        errors.append("the product must expose exactly one defaulted game rule")

    effects = text(script_paths[2])
    for fragment in (
        "mrm_sweep_rulers_effect = {",
        "every_ruler = {",
        "has_government = mandala_government",
        "mandala_nuke_mandala_decrees_effect = yes",
        "change_government = wanua_government",
        "mrm_sweep_holdings_effect = {",
        "every_province = {",
        "has_holding_type = temple_citadel_holding",
        "set_holding_type = castle_holding",
    ):
        if fragment not in effects:
            errors.append(f"map-sweep contract missing: {fragment}")
    government_targets = re.findall(r"change_government\s*=\s*([A-Za-z0-9_]+)", effects)
    if government_targets != ["wanua_government"]:
        errors.append(f"unexpected government targets: {government_targets}")

    on_actions = text(script_paths[1])
    for fragment in (
        "on_game_start_after_lobby = {",
        "yearly_global_pulse = {",
        "on_government_change = {",
        "mrm_government_redirect_dispatch",
        "government_has_flag = government_is_mandala",
        "is_ai = yes",
        "trigger_event = { id = mrm.1 }",
        "trigger_event = { id = mrm.2 days = 1 }",
        "trigger_event = { id = mrm.4 }",
        "trigger_event = { id = mrm.5 days = 2 }",
        "NOT = { has_global_variable = mrm_monthly_loop_started }",
        "set_global_variable = mrm_monthly_loop_started",
        "trigger_event = { on_action = mrm_monthly_dispatch months = 1 }",
        "change_government = wanua_government",
    ):
        if fragment not in on_actions:
            errors.append(f"on-action contract missing: {fragment}")
    if on_actions.count("on_action = mrm_monthly_dispatch months = 1") != 2:
        errors.append("monthly rootless loop must be seeded once and reschedule itself once")
    if "effect = {\n\t\tchange_government = mandala_government" in on_actions:
        errors.append("Mandala government writes are forbidden")

    events = text(script_paths[3])
    event_ids = re.findall(r"(?m)^mrm\.(\d+)\s*=\s*\{", events)
    if event_ids != ["1", "2", "3", "4", "5", "6"]:
        errors.append(f"expected exactly six ordered sweep events, got {event_ids}")
    if events.count("scope = none") != 6 or events.count("hidden = yes") != 6:
        errors.append("all six sweep events must be rootless and hidden")
    if events.count("mrm_sweep_rulers_effect = yes") != 3:
        errors.append("start/day-one/monthly ruler events are not wired exactly once")
    if events.count("mrm_sweep_holdings_effect = yes") != 3:
        errors.append("start/day-two/yearly holding events are not wired exactly once")

    localized: dict[str, dict[str, str]] = {}
    for language, header in LANGUAGES.items():
        relative = f"localization/{language}/mrm_l_{language}.yml"
        value = text(relative)
        if value.splitlines()[0] != f"{header}:":
            errors.append(f"wrong localization header: {relative}")
            continue
        try:
            entries = loc_entries(value)
        except ValueError as error:
            errors.append(f"{relative}: {error}")
            continue
        if set(entries) != LOC_KEYS:
            errors.append(f"localization key inventory mismatch: {relative}")
        if any(not item.strip() for item in entries.values()):
            errors.append(f"blank localization value: {relative}")
        localized[language] = entries
    zh = localized.get("simp_chinese", {})
    if zh.get("rule_mrm_remove_mandala") != "肃清曼荼罗伪信":
        errors.append("the Simplified Chinese rule name is not the requested exact text")
    if zh.get("setting_mrm_enabled_desc") != (
        "妄图在人间封神者，终归是幻梦一场。去剥离那层虚妄的光晕，还世界以真实。"
    ):
        errors.append("the Simplified Chinese enabled description is not exact")
    english = localized.get("english", {})
    for language, entries in localized.items():
        if language not in {"english", "simp_chinese"} and entries == english:
            errors.append(f"English placeholder localization remains: {language}")

    thumbnail = MOD / "thumbnail.png"
    if thumbnail.read_bytes() != art.rendered_bytes():
        errors.append("thumbnail.png is stale against generated key art")
    with Image.open(thumbnail) as image:
        image.load()
        if image.size != (640, 640) or image.mode != "RGB":
            errors.append(f"thumbnail must be 640x640 RGB, got {image.size} {image.mode}")
    if thumbnail.stat().st_size >= 1_000_000:
        errors.append("thumbnail must remain below 1,000,000 bytes")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("MANDALA PURGE STATIC VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "MANDALA PURGE STATIC VALIDATION OK\n"
        f"Runtime files: {len(builder.RUNTIME_FILES)}\n"
        f"Languages: {len(LANGUAGES)}\n"
        "Sweep events: 6"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
