#!/usr/bin/env python3
"""Static validation for the XenoAmess Quality of Life CK3 mod."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image

import build_xenoamess_quality_of_life_release as release
import gen_xqol_phase2


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "mod_xenoamess_quality_of_life"
GAME = ROOT / "Crusader Kings III" / "game"
APPOINTMENT_DIR = "common/succession_appointment"
APPOINTMENT_FILES = {
    "admin_governor.txt": 1,
    "meritocratic_governor.txt": 2,
    "celestial_governor.txt": 2,
}
LANGUAGES = (
    "english",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "simp_chinese",
    "spanish",
)
MARKER_BLOCK = re.compile(
    r"\r\n\r\n\t\t\t# XQOL_AUTO_APPOINTMENT_BEGIN\r\n"
    r".*?"
    r"# XQOL_AUTO_APPOINTMENT_END",
    re.DOTALL,
)
LOCALIZATION_KEY = re.compile(r'^ ([A-Za-z0-9_]+):\d+\s+"', re.MULTILINE)


def read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig")


def has_utf8_bom(path: Path) -> bool:
    return path.read_bytes().startswith(b"\xef\xbb\xbf")


def balanced_braces(text: str) -> bool:
    stripped = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    stripped = re.sub(r"(?m)#.*$", "", stripped)
    depth = 0
    for character in stripped:
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def check_appointment_overrides(errors: list[str]) -> None:
    total_blocks = 0
    for filename, expected_blocks in APPOINTMENT_FILES.items():
        mod_path = MOD / APPOINTMENT_DIR / filename
        game_path = GAME / APPOINTMENT_DIR / filename
        if not game_path.is_file():
            errors.append(f"exact-build vanilla appointment file missing: {game_path}")
            continue
        data = mod_path.read_bytes()
        if b"\n" in data.replace(b"\r\n", b""):
            errors.append(f"appointment override must retain vanilla CRLF endings: {filename}")
        text = data.decode("utf-8-sig")
        blocks = MARKER_BLOCK.findall(text)
        total_blocks += len(blocks)
        if len(blocks) != expected_blocks:
            errors.append(
                f"{filename}: expected {expected_blocks} controlled insertion blocks, got {len(blocks)}"
            )
        stripped = MARKER_BLOCK.sub("", text).encode("utf-8-sig")
        if stripped != game_path.read_bytes():
            errors.append(f"{filename}: stripping XQOL blocks does not reproduce vanilla bytes")
        for index, block in enumerate(blocks, start=1):
            required = (
                "is_ai = no",
                "has_variable = xqol_auto_appoint_successors_enabled",
                "subtract = {",
                "value = 1000000",
                "desc = xqol_auto_appointment_score_penalty_desc",
            )
            for token in required:
                if block.count(token) != 1:
                    errors.append(f"{filename} block {index}: expected one {token!r}")
            ruler_test = "top_liege = this" if filename == "admin_governor.txt" else "is_independent_ruler = yes"
            if block.count(ruler_test) != 1:
                errors.append(f"{filename} block {index}: missing exact sovereign test")
    if total_blocks != 5:
        errors.append(f"expected five appointment insertions, got {total_blocks}")


def check_localization(errors: list[str], *, release_localization: bool = False) -> None:
    contents: dict[str, str] = {}
    keys: dict[str, set[str]] = {}
    for language in LANGUAGES:
        path = MOD / "localization" / language / f"xqol_l_{language}.yml"
        if not path.is_file():
            errors.append(f"localization file missing: {path.relative_to(MOD)}")
            continue
        text = read_utf8(path)
        contents[language] = text
        keys[language] = set(LOCALIZATION_KEY.findall(text))
        if not text.startswith(f"l_{language}:\n") and not text.startswith(f"l_{language}:\r\n"):
            errors.append(f"localization header mismatch: {language}")
    if "english" not in keys:
        return
    for language, language_keys in keys.items():
        if language_keys != keys["english"]:
            errors.append(f"localization key set differs from English: {language}")
    required_keys = {
        "decision_group_type_xqol_quality_of_life",
        "xqol_auto_appointment_score_penalty_desc",
        "xqol_enable_auto_appointment_decision",
        "xqol_disable_auto_appointment_decision",
        "xqol_enable_no_vassal_transfers_decision",
        "xqol_disable_no_vassal_transfers_decision",
        "xqol_enable_auto_call_defenders_decision",
        "xqol_disable_auto_call_defenders_decision",
        "xqol_mass_conversion_decision",
        "xqol_bulk_demand_payment_full_decision",
        "xqol_bulk_demand_payment_any_decision",
        "xqol_bulk_ransom_full_decision",
        "xqol_bulk_ransom_any_decision",
        "xqol_bulk_release_terms_decision",
        "xqol_mass_conversion_results_desc",
    }
    missing = required_keys - keys["english"]
    if missing:
        errors.append(f"required localization keys missing: {sorted(missing)}")
    if release_localization:
        errors.extend(release.release_localization_errors(MOD))


def check_scripts(errors: list[str]) -> None:
    decisions = read_utf8(MOD / "common/decisions/xqol_decisions.txt")
    interactions = read_utf8(
        MOD / "common/character_interactions/xqol_generated_release_interactions.txt"
    )
    slider = read_utf8(
        MOD / "gui/event_window_widgets/xqol_conversion_threshold_slider.gui"
    )
    triggers = read_utf8(MOD / "common/scripted_triggers/xqol_triggers.txt")
    effects = read_utf8(MOD / "common/scripted_effects/xqol_effects.txt")
    on_actions = read_utf8(MOD / "common/on_action/xqol_on_actions.txt")
    decision_group = read_utf8(MOD / "common/decision_group_types/xqol_decision_group_types.txt")
    if "gui_tags = { big_button }" not in decision_group:
        errors.append("custom decision group must use the rendered big_button GUI tag")
    if decisions.count("ai_potential = { always = no }") != 12:
        errors.append("all twelve decisions must be impossible for AI")
    if "ai_frequency" in interactions or "ai_potential" in interactions:
        errors.append(
            "scripted-only hidden interactions must not opt into autonomous AI scheduling"
        )
    if interactions.count("ai_will_do = { base = 100 }") != 9:
        errors.append(
            "all nine hidden interactions must opt scripted run_interaction into AI replies"
        )
    if interactions.count("category = interaction_category_religion") != 2:
        errors.append("both conversion interactions must declare the religion category")
    if interactions.count("category = interaction_category_prison") != 7:
        errors.append("all seven release interactions must declare the prison category")
    if interactions.count("ignores_pending_interaction_block = yes") != 9:
        errors.append("all hidden interactions must support same-batch dispatch")
    if interactions.count("scope:actor = { xqol_human_ruler_trigger = yes }") != 18:
        errors.append("all nine hidden scripted interactions must require a human actor")
    if "FloatToInt(" in slider:
        errors.append("slider must not use the unavailable FloatToInt data function")
    if "GetProgressBarValueMaxScaled(" not in slider:
        errors.append("slider must route its value through a supported int32 scaler")
    if "PdxGetWidgetScreenSize" in slider:
        errors.append("slider must not mix local mouse coordinates with scaled screen dimensions")
    if "GetX_CVector2f(PdxGuiWidget.GetScaledMousePosition)" not in slider:
        errors.append("slider must derive its route from the scrollbar-local mouse position")
    if "FindChild('xqol_conversion_threshold_handle').GetScaledMousePosition" in slider:
        errors.append("slider must not subtract two cursor positions")
    if "raw_text = \"[GetPlayer.MakeScope.Var('xqol_mass_conversion_threshold_draft')" not in slider:
        errors.append("slider's dynamic percentage must use raw_text")
    if "size = { 404 28 }" in slider:
        errors.append("slider container must derive its size from its child scrollbar")
    if 'default_format = "#weak"' in slider:
        errors.append("slider help must not concatenate weak with nested dynamic formatting")
    for variable in (
        "xqol_auto_appoint_successors_enabled",
        "xqol_no_vassal_transfers_enabled",
        "xqol_auto_call_defenders_enabled",
    ):
        if f"set_variable = {variable}" not in decisions or f"remove_variable = {variable}" not in decisions:
            errors.append(f"decision toggle is not symmetric: {variable}")
    for government in (
        "administrative_government",
        "meritocratic_government",
        "celestial_government",
    ):
        if triggers.count(f"has_government = {government}") != 1:
            errors.append(f"supported-player trigger mismatch: {government}")
    for token in (
        "is_ai = no",
        "top_liege = this",
        "government_allows = administrative",
        "xqol_no_vassal_transfer_guard",
        "ai_should_not_transfer",
    ):
        if token not in triggers + effects:
            errors.append(f"required player/transfer guard token missing: {token}")
    if effects.count("add_character_flag = xqol_no_vassal_transfer_guard") != 1:
        errors.append("transfer ownership flag must have exactly one add site")
    if effects.count("remove_character_flag = xqol_no_vassal_transfer_guard") != 2:
        errors.append("transfer ownership flag must be cleared by decision and reconciliation")
    for hook in ("on_game_start_after_lobby", "on_vassal_change", "yearly_playable_pulse", "on_war_started"):
        if hook not in on_actions:
            errors.append(f"maintenance hook missing: {hook}")
    vanilla_interaction = read_utf8(GAME / "common/character_interactions/00_vassal_interactions.txt")
    if "grant_vassal_interaction" not in vanilla_interaction or "has_character_flag = ai_should_not_transfer" not in vanilla_interaction:
        errors.append("exact-build vanilla grant-vassal AI guard contract is missing")

    generated = gen_xqol_phase2.generated_payloads()
    for relative, text in generated.items():
        expected = b"\xef\xbb\xbf" + text.replace("\r\n", "\n").encode("utf-8")
        if (MOD / relative).read_bytes() != expected:
            errors.append(f"generated phase-two runtime drift: {relative}")

    release_interactions = read_utf8(
        MOD / "common/character_interactions/xqol_generated_release_interactions.txt"
    )
    for interaction in (
        "xqol_mass_conversion_courtier_interaction",
        "xqol_mass_conversion_ruler_interaction",
        "xqol_release_hook_recruit_conversion_interaction",
        "xqol_release_hook_recruit_interaction",
        "xqol_release_hook_conversion_interaction",
        "xqol_release_recruit_conversion_interaction",
        "xqol_release_hook_interaction",
        "xqol_release_recruit_interaction",
        "xqol_release_conversion_interaction",
    ):
        if release_interactions.count(f"{interaction} = {{") != 1:
            errors.append(f"generated interaction missing or duplicated: {interaction}")
    threshold_guis = read_utf8(
        MOD / "common/scripted_guis/xqol_generated_conversion_threshold_guis.txt"
    )
    if len(re.findall(r"(?m)^xqol_set_conversion_threshold_\d+_gui = \{$", threshold_guis)) != 101:
        errors.append("conversion threshold GUI must contain 101 literal setters")
    dispatch = read_utf8(
        MOD / "common/scripted_effects/xqol_generated_conversion_dispatch.txt"
    )
    if len(re.findall(r"(?m)^\t\t\d+ = \{", dispatch)) != 101:
        errors.append("conversion threshold dispatcher must contain 101 literal cases")
    for token in (
        "run_interaction = {",
        "interaction = demand_payment_interaction",
        "interaction = ransom_interaction",
        "send_threshold = decline",
        "execute_threshold = accept",
        "xqol_release_hook_recruit_conversion_interaction",
        "xqol_mass_conversion_pending",
        "add_to_list = xqol_conversion_courtier_candidates",
        "add_to_list = xqol_conversion_ruler_candidates",
        "list = xqol_conversion_courtier_candidates",
        "list = xqol_conversion_ruler_candidates",
        "NOT = { is_in_list = xqol_conversion_ruler_candidates }",
    ):
        if token not in effects:
            errors.append(f"phase-two runtime token missing: {token}")
    conversion_count = (
        "change_variable = { name = xqol_mass_conversion_pending add = 1 }"
    )
    first_dispatch = effects.find(
        "every_in_list = {\n\t\t\tlist = xqol_conversion_courtier_candidates"
    )
    if effects.count(conversion_count) != 3:
        errors.append("conversion candidate counter must cover all three candidate scans")
    if first_dispatch < 0:
        errors.append("conversion courtier dispatch loop missing")
    elif conversion_count in effects[first_dispatch:]:
        errors.append("conversion candidates must all be counted before dispatch begins")
    invalid_auto_call_check = re.compile(
        r"is_character_interaction_potentially_accepted\s*=\s*\{\s*"
        r"recipient\s*=\s*scope:recipient\s*"
        r"interaction\s*=\s*call_(?:ally|house_member_to_war)_interaction"
    )
    if invalid_auto_call_check.search(effects):
        errors.append("automatic calls must use interaction validity, not AI acceptance")
    for token in (
        "xqol_free_call_target_valid_trigger = yes",
        "xqol_free_house_call_target_valid_trigger = yes",
        "NOT = { was_called = scope:recipient }",
        "joiner_not_already_in_another_war_with_any_target_war_participants_trigger",
        "can_join_war_liege_vassal_check_trigger",
        "diarch_callable_in_internal_war_trigger = yes",
    ):
        if token not in triggers + effects:
            errors.append(f"automatic-call target gate missing: {token}")

    vanilla_contracts = {
        "common/on_action/war_on_actions.txt": ("on_war_started = {",),
        "common/character_interactions/00_alliance.txt": (
            "call_ally_interaction = {",
            "call_ally_interaction_effect = yes",
        ),
        "common/character_interactions/00_religious_interactions.txt": (
            "ask_for_conversion_courtier_interaction = {",
            "demand_conversion_vassal_ruler_interaction = {",
            "religion_demand_conversion_default_modifier = yes",
        ),
        "common/character_interactions/00_perk_interactions.txt": (
            "demand_payment_interaction = {",
            "golden_obligation_value",
        ),
        "common/character_interactions/00_prison_interactions.txt": (
            "ransom_interaction = {",
            "release_from_prison_interaction = {",
            "send_options_exclusive = no",
        ),
        "common/scripted_effects/00_prison_effects.txt": ("ransom_interaction_effect = {",),
    }
    for relative, required in vanilla_contracts.items():
        vanilla = read_utf8(GAME / relative)
        for token in required:
            if token not in vanilla:
                errors.append(f"exact-build phase-two vanilla contract missing {token!r}: {relative}")

    for relative in sorted(release.RUNTIME_FILES):
        path = MOD / relative
        if path.suffix.lower() not in {".gui", ".txt"}:
            continue
        if not balanced_braces(read_utf8(path)):
            errors.append(f"unbalanced braces: {path.relative_to(MOD)}")


def check_assets_and_descriptor(errors: list[str]) -> None:
    descriptor = read_utf8(MOD / "descriptor.mod")
    for token in (
        'version="1.1.0"',
        'name="XenoAmess的体验优化"',
        'picture="thumbnail.png"',
        'supported_version="1.19.0.6"',
    ):
        if descriptor.count(token) != 1:
            errors.append(f"descriptor token mismatch: {token}")
    if "remote_file_id" in descriptor:
        errors.append("source descriptor must not contain remote_file_id")
    thumbnail = MOD / "thumbnail.png"
    if thumbnail.stat().st_size >= 1024 * 1024:
        errors.append("thumbnail.png must be smaller than 1 MiB")
    with Image.open(thumbnail) as image:
        if image.size != (640, 640) or image.format != "PNG":
            errors.append(f"thumbnail must be a 640x640 PNG, got {image.size} {image.format}")
    for picture in re.findall(r'reference = "([^"]+)"', read_utf8(MOD / "common/decisions/xqol_decisions.txt")):
        if not (GAME / picture).is_file():
            errors.append(f"vanilla decision art missing: {picture}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-localization",
        action="store_true",
        help="reject English placeholders in all seven target languages",
    )
    args = parser.parse_args(argv)
    errors = release.release_source_errors(MOD)
    runtime_text = [
        MOD / relative
        for relative in release.RUNTIME_FILES
        if Path(relative).suffix.lower() in {".gui", ".txt", ".yml"}
    ]
    for path in runtime_text:
        if not has_utf8_bom(path):
            errors.append(f"runtime text lacks UTF-8 BOM: {path.relative_to(MOD)}")
    check_appointment_overrides(errors)
    check_localization(errors, release_localization=args.release_localization)
    check_scripts(errors)
    check_assets_and_descriptor(errors)
    if errors:
        print("XQOL STATIC VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "XQOL STATIC VALIDATION GREEN\n"
        f"Runtime files: {len(release.RUNTIME_FILES)}\n"
        "Appointment types: 5\n"
        "Controlled vanilla override files: 3\n"
        "Localization structures: 9\n"
        f"Release localization: {'GREEN' if args.release_localization else 'not requested'}\n"
        f"Thumbnail bytes: {(MOD / 'thumbnail.png').stat().st_size}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
