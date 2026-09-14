#!/usr/bin/env python3
"""Static release gate for Tributary Expansion Directives."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

import build_tributary_expansion_directives_release as builder
import compose_tributary_expansion_directives_key_art as art
from translate_localization_minimax import protected_tokens


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / builder.PRODUCT_ID
SCRIPT_PATHS = (
    "common/casus_belli_types/ted_tributary_expansion_casus_belli.txt",
    "common/character_interactions/ted_tributary_expansion_interactions.txt",
    "common/script_values/ted_tributary_expansion_values.txt",
    "common/scripted_triggers/ted_tributary_expansion_triggers.txt",
)
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


def subsidy_reference(monthly_income: float) -> int:
    value = min(500, max(50, monthly_income * 12))
    return int((value + 4.999999) // 5 * 5)


def validate() -> list[str]:
    errors = builder.release_source_errors(MOD)
    descriptor = text("descriptor.mod")
    expected_descriptor = (
        'version="1.0.0"\n'
        'tags={\n\t"Gameplay"\n}\n'
        'name="Tributary Expansion Directives — 驱策朝贡国"\n'
        'picture="thumbnail.png"\n'
        'supported_version="1.19.0.6"\n'
    )
    if descriptor.replace("\r\n", "\n") != expected_descriptor:
        errors.append("descriptor.mod fields or ordering differ from the release contract")

    for relative in SCRIPT_PATHS:
        if not balanced_braces(text(relative)):
            errors.append(f"unbalanced braces: {relative}")
    scripts = "\n".join(text(relative) for relative in SCRIPT_PATHS)
    top_level = re.findall(r"(?m)^(ted_[A-Za-z0-9_]+)\s*=\s*\{", scripts)
    if len(top_level) != len(set(top_level)):
        errors.append("duplicate top-level ted script key")
    if any(not key.startswith("ted_") for key in top_level):
        errors.append("non-ted top-level key found")

    interaction = text(SCRIPT_PATHS[1])
    required_interaction = (
        "ted_issue_expansion_directive_interaction = {",
        "target_filter = secondary_recipient_realm_titles",
        "every_character_to_title_neighboring_county = {",
        "is_tributary_of = scope:actor",
        "cost = { prestige = 150 }",
        "cooldown_against_recipient = { years = 5 }",
        "flag = offer_war_subsidy",
        "ai_instant_response = yes",
        "can_send_despite_rejection = yes",
        "casus_belli = ted_directed_county_expansion_cb",
        "defender = scope:secondary_recipient",
        "target_titles = { scope:target }",
        "target_title = scope:target",
    )
    for fragment in required_interaction:
        if fragment not in interaction:
            errors.append(f"interaction contract missing: {fragment}")
    if interaction.count("start_war = {") != 1:
        errors.append("the interaction must contain exactly one start_war path")
    if interaction.count("pay_short_term_gold = {") != 1:
        errors.append("the subsidy must have exactly one transfer path")
    on_accept = interaction.index("\ton_accept = {")
    on_decline = interaction.index("\ton_decline = {")
    ai_potential = interaction.index("\tai_potential = {")
    if "pay_short_term_gold" not in interaction[on_accept:on_decline]:
        errors.append("the subsidy is not confined to acceptance")
    if "pay_short_term_gold" in interaction[on_decline:ai_potential]:
        errors.append("the decline path must not transfer gold")
    if interaction.count("add_prestige = 150") != 2:
        errors.append("accept/decline invalidation must each refund exactly 150 prestige")
    if interaction.count("remove_interaction_cooldown_against = {") != 2:
        errors.append("accept/decline invalidation must each clear recipient cooldown")

    values = text(SCRIPT_PATHS[2])
    for fragment in ("multiply = 12", "min = 50", "max = 500", "ceiling = yes"):
        if fragment not in values:
            errors.append(f"subsidy formula missing: {fragment}")
    expected_vectors = {0: 50, 1: 50, 10: 120, 41.67: 500, 100: 500}
    for income, expected in expected_vectors.items():
        if subsidy_reference(income) != expected:
            errors.append(f"subsidy reference vector failed: {income} -> {expected}")

    cb = text(SCRIPT_PATHS[0])
    for fragment in (
        "group = conquest",
        "has_character_flag = ted_directed_expansion_authorized",
        "target_title_tier = county",
        "holder = scope:attacker",
        "on_victory = {",
        "on_white_peace = {",
        "on_defeat = {",
        "add_truce_attacker_victory_effect = yes",
        "add_truce_white_peace_effect = yes",
        "add_truce_attacker_defeat_effect = yes",
        "on_primary_attacker_death = inherit",
        "on_primary_defender_death = inherit",
    ):
        if fragment not in cb:
            errors.append(f"CB contract missing: {fragment}")
    if re.search(r"(?m)^\tcost\s*=", cb):
        errors.append("the directed CB must not charge a second war cost")

    localized: dict[str, dict[str, str]] = {}
    for language, header in LANGUAGES.items():
        relative = (
            f"localization/{language}/ted_tributary_expansion_l_{language}.yml"
        )
        value = text(relative)
        if value.splitlines()[0] != f"{header}:":
            errors.append(f"wrong localization header: {relative}")
            continue
        try:
            entries = loc_entries(value)
        except ValueError as error:
            errors.append(f"{relative}: {error}")
            continue
        if any(not item.strip() for item in entries.values()):
            errors.append(f"blank localization value: {relative}")
        localized[language] = entries
    english = localized.get("english", {})
    for language, entries in localized.items():
        if set(entries) != set(english):
            errors.append(f"localization key inventory mismatch: {language}")
            continue
        if language not in {"english", "simp_chinese"} and entries == english:
            errors.append(f"English placeholder localization remains: {language}")
        for key, source in english.items():
            if sorted(protected_tokens(entries[key])) != sorted(protected_tokens(source)):
                errors.append(f"protected token mismatch: {language}:{key}")
    korean = localized.get("korean", {})
    if korean and not any(re.search(r"[가-힣]", value) for value in korean.values()):
        errors.append("Korean localization contains no Hangul")

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
        print("TRIBUTARY EXPANSION DIRECTIVES STATIC VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "TRIBUTARY EXPANSION DIRECTIVES STATIC VALIDATION OK\n"
        f"Runtime files: {len(builder.RUNTIME_FILES)}\n"
        f"Languages: {len(LANGUAGES)}\n"
        "Directed wars: one county per accepted order"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
