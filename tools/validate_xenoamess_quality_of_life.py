#!/usr/bin/env python3
"""Static validation for the XenoAmess Quality of Life CK3 mod."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

import build_xenoamess_quality_of_life_release as release


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


def check_localization(errors: list[str]) -> None:
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
        "xqol_quality_of_life",
        "xqol_auto_appointment_score_penalty_desc",
        "xqol_enable_auto_appointment_decision",
        "xqol_disable_auto_appointment_decision",
        "xqol_enable_no_vassal_transfers_decision",
        "xqol_disable_no_vassal_transfers_decision",
    }
    missing = required_keys - keys["english"]
    if missing:
        errors.append(f"required localization keys missing: {sorted(missing)}")
    english_body = contents["english"].splitlines()[1:]
    for language in set(LANGUAGES) - {"english", "simp_chinese"}:
        if contents.get(language, "").splitlines()[1:] != english_body:
            errors.append(f"daily-development placeholder must equal English: {language}")


def check_scripts(errors: list[str]) -> None:
    decisions = read_utf8(MOD / "common/decisions/xqol_decisions.txt")
    triggers = read_utf8(MOD / "common/scripted_triggers/xqol_triggers.txt")
    effects = read_utf8(MOD / "common/scripted_effects/xqol_effects.txt")
    on_actions = read_utf8(MOD / "common/on_action/xqol_on_actions.txt")
    decision_group = read_utf8(MOD / "common/decision_group_types/xqol_decision_group_types.txt")
    if "gui_tags = { big_button }" not in decision_group:
        errors.append("custom decision group must use the rendered big_button GUI tag")
    if decisions.count("ai_potential = { always = no }") != 4:
        errors.append("all four decisions must be impossible for AI")
    for variable in (
        "xqol_auto_appoint_successors_enabled",
        "xqol_no_vassal_transfers_enabled",
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
    for hook in ("on_game_start_after_lobby", "on_vassal_change", "yearly_playable_pulse"):
        if hook not in on_actions:
            errors.append(f"maintenance hook missing: {hook}")
    vanilla_interaction = read_utf8(GAME / "common/character_interactions/00_vassal_interactions.txt")
    if "grant_vassal_interaction" not in vanilla_interaction or "has_character_flag = ai_should_not_transfer" not in vanilla_interaction:
        errors.append("exact-build vanilla grant-vassal AI guard contract is missing")
    for path in (MOD / "common").rglob("*.txt"):
        if not balanced_braces(read_utf8(path)):
            errors.append(f"unbalanced braces: {path.relative_to(MOD)}")


def check_assets_and_descriptor(errors: list[str]) -> None:
    descriptor = read_utf8(MOD / "descriptor.mod")
    for token in (
        'version="1.0.0"',
        'name="XenoAmess 的生活质量"',
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


def main() -> int:
    errors = release.release_source_errors(MOD)
    runtime_text = [
        path
        for path in MOD.rglob("*")
        if path.is_file() and path.suffix.lower() in {".txt", ".yml"}
        and ("common" in path.parts or "localization" in path.parts)
    ]
    for path in runtime_text:
        if not has_utf8_bom(path):
            errors.append(f"runtime text lacks UTF-8 BOM: {path.relative_to(MOD)}")
    check_appointment_overrides(errors)
    check_localization(errors)
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
        f"Thumbnail bytes: {(MOD / 'thumbnail.png').stat().st_size}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
