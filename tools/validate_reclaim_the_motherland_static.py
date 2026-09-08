#!/usr/bin/env python3
"""Static gate for the Reclaim the Motherland standalone mod."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import build_reclaim_the_motherland_release as builder
from PIL import Image

import compose_reclaim_the_motherland_key_art as key_art


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / builder.PRODUCT_ID
LANGUAGES = {language: f"l_{language}" for language in builder.LOCALIZATION_LANGUAGES}
LOC_KEYS = frozenset(
    {
        "rule_rmtm_hegemon_fate",
        "setting_rmtm_reclaim_the_motherland",
        "setting_rmtm_reclaim_the_motherland_desc",
        "setting_rmtm_vanilla_shattering",
        "setting_rmtm_vanilla_shattering_desc",
        "rmtm_claim_restoration_decision",
        "rmtm_claim_restoration_decision_confirm",
        "rmtm_claim_restoration_decision_desc",
        "rmtm_claim_restoration_decision_tooltip",
        "rmtm_restoration_title_prefix",
        "rmtm_restoration_hegemony_fallback_name",
        "rmtm_restoration_hegemony_fallback_name_adj",
        "rmtm_claim_mandate_blocked_by_restoration_tt",
        "dynastic_cycle_entered_chaos_hunagdi_tt",
    }
)


def text(relative: str) -> str:
    return (MOD / PureRelativePath(relative)).read_bytes().decode("utf-8-sig")


def PureRelativePath(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"expected a relative product path: {value}")
    return path


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


def validate() -> list[str]:
    errors = builder.release_source_errors(MOD)
    expected_descriptor = (
        'version="0.1.0"\n'
        'tags={\n\t"Gameplay"\n}\n'
        'name="Reclaim the Motherland — 重整河山"\n'
        'picture="thumbnail.png"\n'
        'supported_version="1.19.0.6"\n'
    )
    descriptor = text("descriptor.mod").replace("\r\n", "\n")
    if descriptor != expected_descriptor:
        errors.append("descriptor.mod fields or ordering differ from the 0.1.0 contract")
    thumbnail = MOD / "thumbnail.png"
    if not thumbnail.is_file():
        errors.append("thumbnail.png is missing")
    else:
        if thumbnail.stat().st_size >= 1_000_000:
            errors.append("thumbnail.png must be smaller than 1,000,000 bytes")
        with Image.open(thumbnail) as image:
            if image.size != (640, 640) or image.format != "PNG":
                errors.append(
                    f"thumbnail must be a 640x640 PNG, got {image.size} {image.format}"
                )
        if thumbnail.read_bytes() != key_art.rendered_bytes():
            errors.append("thumbnail.png is stale against generated key art")

    expected_runtime_files = frozenset(
        {
            "common/decisions/rmtm_restoration_decisions.txt",
            "common/decisions/zz_rmtm_mandate_override.txt",
            "common/game_rules/rmtm_game_rules.txt",
            "common/scripted_effects/rmtm_dynastic_cycle_effects.txt",
            "common/scripted_effects/rmtm_vanilla_compat_effects.txt",
            "common/scripted_effects/zz_rmtm_vanilla_overrides.txt",
            "common/scripted_triggers/rmtm_restoration_triggers.txt",
            "descriptor.mod",
            "localization/english/rmtm_l_english.yml",
            "localization/french/rmtm_l_french.yml",
            "localization/german/rmtm_l_german.yml",
            "localization/japanese/rmtm_l_japanese.yml",
            "localization/korean/rmtm_l_korean.yml",
            "localization/polish/rmtm_l_polish.yml",
            "localization/russian/rmtm_l_russian.yml",
            "localization/simp_chinese/rmtm_l_simp_chinese.yml",
            "localization/spanish/rmtm_l_spanish.yml",
            "thumbnail.png",
        }
    )
    if builder.RUNTIME_FILES != expected_runtime_files:
        errors.append("release allowlist is not the exact eighteen-file product inventory")
    if builder.SOURCE_ONLY_FILES != frozenset(
        {"README.md", "docs/acceptance-plan.md", "docs/acceptance-report.md"}
    ):
        errors.append("source-only product inventory mismatch")

    script_paths = sorted(
        relative for relative in builder.RUNTIME_FILES if relative.endswith(".txt")
    )
    scripts: dict[str, str] = {}
    definitions: dict[str, list[str]] = {}
    for relative in script_paths:
        value = text(relative)
        scripts[relative] = value
        if not balanced_braces(value):
            errors.append(f"unbalanced braces: {relative}")
        filename = Path(relative).name
        if not filename.startswith(("rmtm_", "zz_rmtm_")):
            errors.append(f"runtime script filename lacks the rmtm namespace: {relative}")
        for key in re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", value):
            definitions.setdefault(key, []).append(relative)

    duplicate_definitions = {
        key: paths for key, paths in definitions.items() if len(paths) != 1
    }
    if duplicate_definitions:
        errors.append(f"duplicate common definitions: {duplicate_definitions}")
    allowed_vanilla_overrides = {
        "situation_dynastic_cycle_claim_mandate_decision",
        "tgp_chaos_shattering_effect",
    }
    unnamespaced = sorted(
        key
        for key in definitions
        if not key.startswith("rmtm_") and key not in allowed_vanilla_overrides
    )
    if unnamespaced:
        errors.append(f"unexpected unnamespaced common definitions: {unnamespaced}")

    all_script = "\n".join(scripts.values())
    for required_definition in (
        "rmtm_hegemon_fate",
        "rmtm_holds_restoration_hegemony_trigger",
        "rmtm_claim_restoration_decision",
        "situation_dynastic_cycle_claim_mandate_decision",
        "rmtm_chaos_shattering_effect",
        "tgp_chaos_shattering_effect",
    ):
        if required_definition not in definitions:
            errors.append(f"required common definition missing: {required_definition}")

    rules = scripts.get("common/game_rules/rmtm_game_rules.txt", "")
    for fragment in (
        "default = rmtm_reclaim_the_motherland",
        "rmtm_reclaim_the_motherland = { }",
        "rmtm_vanilla_shattering = { }",
    ):
        if fragment not in rules:
            errors.append(f"game-rule contract missing: {fragment}")
    if rules.count("default =") != 1:
        errors.append("the product must expose exactly one defaulted game rule")

    restoration = scripts.get(
        "common/decisions/rmtm_restoration_decisions.txt", ""
    )
    for fragment in (
        "has_game_rule = rmtm_reclaim_the_motherland",
        "rmtm_holds_restoration_hegemony_trigger = yes",
        "percent >= claim_mandate_china_county_percentage_value",
        "tgp_claim_mandate_of_heaven_effect = yes",
        "list = rmtm_restoration_hegemonies",
        "destroy_title = prev",
    ):
        if fragment not in restoration:
            errors.append(f"restoration decision contract missing: {fragment}")

    mandate_override = scripts.get(
        "common/decisions/zz_rmtm_mandate_override.txt", ""
    )
    if mandate_override.count(
        "NOT = { rmtm_holds_restoration_hegemony_trigger = yes }"
    ) != 3:
        errors.append(
            "Claim the Mandate override must lock Later-Dynasty holders in shown, "
            "valid, and AI paths"
        )

    custom_shattering = scripts.get(
        "common/scripted_effects/rmtm_dynastic_cycle_effects.txt", ""
    )
    for fragment in (
        "participant_group_type = pro_hegemon_movement",
        "add_to_list = rmtm_loyal_direct_vassals",
        "create_dynamic_title = {",
        "tier = hegemony",
        "name = rmtm_restoration_hegemony",
        "move_title_name_to = scope:rmtm_restoration_hegemony_title",
        "set_title_prefix = rmtm_restoration_title_prefix",
        "destroy_title = title:h_china",
    ):
        if fragment not in custom_shattering:
            errors.append(f"custom shattering contract missing: {fragment}")
    if re.search(
        r"(?m)^\s*force_step_down_landed_titles\s*=", custom_shattering
    ):
        errors.append("custom shattering must not force the former hegemon to step down")

    for localization_reference in (
        "rmtm_restoration_title_prefix",
        "rmtm_restoration_hegemony_fallback_name",
        "rmtm_restoration_hegemony_fallback_name_adj",
    ):
        if localization_reference not in all_script:
            errors.append(
                f"runtime does not reference required localization: {localization_reference}"
            )

    localized: dict[str, dict[str, str]] = {}
    for language, header in LANGUAGES.items():
        relative = f"localization/{language}/rmtm_l_{language}.yml"
        value = text(relative)
        if not value.splitlines() or value.splitlines()[0] != f"{header}:":
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
        allowed_vanilla_loc_overrides = {"dynastic_cycle_entered_chaos_hunagdi_tt"}
        invalid_namespace = sorted(
            key
            for key in entries
            if not key.startswith(("rmtm_", "rule_rmtm_", "setting_rmtm_"))
            and key not in allowed_vanilla_loc_overrides
        )
        if invalid_namespace:
            errors.append(
                f"localization key lacks the rmtm namespace: {invalid_namespace}"
            )
        localized[language] = entries

    chinese = localized.get("simp_chinese", {})
    english = localized.get("english", {})
    required_chinese = {
        "rule_rmtm_hegemon_fate": "中华霸权统治者的命运",
        "setting_rmtm_reclaim_the_motherland": "重整河山",
        "setting_rmtm_vanilla_shattering": "群雄割据（原版）",
        "rmtm_claim_restoration_decision": "宣称复辟",
        "rmtm_restoration_title_prefix": "后",
        "dynastic_cycle_entered_chaos_hunagdi_tt": "天子退位并失去天命，天下由此分崩。",
    }
    required_english = {
        "rule_rmtm_hegemon_fate": "Fate of the Chinese Hegemon",
        "setting_rmtm_reclaim_the_motherland": "Reclaim the Motherland",
        "setting_rmtm_vanilla_shattering": "Vanilla Shattering",
        "rmtm_claim_restoration_decision": "Proclaim the Restoration",
        "rmtm_restoration_title_prefix": "Later ",
        "dynastic_cycle_entered_chaos_hunagdi_tt": "The emperor steps down and loses the Mandate, and All Under Heaven fractures.",
    }
    for key, expected in required_chinese.items():
        if chinese.get(key) != expected:
            errors.append(f"Simplified Chinese contract mismatch: {key}")
    for key, expected in required_english.items():
        if english.get(key) != expected:
            errors.append(f"English contract mismatch: {key}")
    if chinese and english and chinese == english:
        errors.append("Simplified Chinese localization must not be an English placeholder")
    errors.extend(builder.release_localization_errors(MOD))
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("RECLAIM THE MOTHERLAND STATIC VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "RECLAIM THE MOTHERLAND STATIC VALIDATION OK\n"
        f"Runtime files: {len(builder.RUNTIME_FILES)}\n"
        f"Languages: {len(LANGUAGES)}\n"
        f"Localization keys: {len(LOC_KEYS)}\n"
        f"Gameplay scripts: {sum(path.endswith('.txt') for path in builder.RUNTIME_FILES)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
