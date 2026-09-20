#!/usr/bin/env python3
"""Static release gate for Celestial Commerce & Corruption."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

from PIL import Image

import build_celestial_commerce_corruption_release as builder
import compose_celestial_commerce_corruption_workshop_media as workshop_media
from translate_localization_minimax import protected_tokens


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / builder.PRODUCT_ID
GAME_GOVERNMENTS = (
    ROOT / "Crusader Kings III/game/common/governments/00_government_types.txt",
    Path(
        "C:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/"
        "governments/00_government_types.txt"
    ),
)
SCRIPT_PATHS = (
    "common/decisions/xccc_corruption_decision.txt",
    "common/governments/xccc_celestial_government.txt",
    "common/script_values/xccc_corruption_values.txt",
    "common/subject_contracts/contracts/xccc_celestial_obligations.txt",
    "common/traits/xccc_corruption_traits.txt",
    "events/xccc_corruption_events.txt",
)
LOCALIZATIONS = {
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
ASSET_SHA256 = {
    "thumbnail.png": "a6205829885cc1a6b81c89eddfac47e17ea1b0c0fee3de8a30b54471934b0621",
    "gfx/interface/illustrations/decisions/xccc_corruption_decision.dds": (
        "39e44af5f66c508e1efba0162d621dae8463e121c4b268db0294953ed3dfbe6d"
    ),
    "gfx/interface/icons/traits/xccc_corruption_1.dds": (
        "c08fa745cceefab0ed2195d68339b93ff6c66c557e66b219baafc814893ffd5f"
    ),
    "gfx/interface/icons/traits/xccc_corruption_2.dds": (
        "9f5fe76d509d5a5b4d9152a02ca93368196a1d86397f35bb5e6abfe97ba96511"
    ),
    "gfx/interface/icons/traits/xccc_corruption_3.dds": (
        "1fbea2e1e4be09964b4c0d3bb29e525e199d00a20da9056052d4e5f06a04b9c7"
    ),
    "gfx/interface/icons/traits/xccc_corruption_4.dds": (
        "b602b9aa183f77309279ea7646184996a4435e605ed47ba1187928205a03aa3c"
    ),
}
EXPECTED_LOC_KEYS = {
    "xccc_corruption_policy_decision",
    "xccc_corruption_policy_decision_desc",
    "xccc_corruption_policy_decision_tooltip",
    "xccc_corruption_policy_decision_confirm",
    "xccc_corruption_policy_effect_tooltip",
    *(f"trait_xccc_corruption_{tier}" for tier in range(1, 5)),
    *(f"trait_xccc_corruption_{tier}_desc" for tier in range(1, 5)),
    *(f"trait_xccc_corruption_{tier}_character_desc" for tier in range(1, 5)),
    "xccc.1001.t",
    "xccc.1001.desc",
    *(f"xccc.1001.{option}" for option in "abcdef"),
    *(f"xccc.1001.{option}.tt" for option in "abcdef"),
}


def read_text(relative: str) -> str:
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


def extract_named_block(value: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", value)
    if match is None:
        raise ValueError(f"missing block: {name}")
    start = match.start()
    brace = value.find("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(brace, len(value)):
        char = value[index]
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
            if depth == 0:
                return value[start : index + 1]
    raise ValueError(f"unterminated block: {name}")


def semantic_tokens(value: str) -> list[str]:
    uncommented = "\n".join(line.split("#", 1)[0] for line in value.splitlines())
    return re.findall(r'"(?:[^"\\]|\\.)*"|>=|<=|!=|[={}<>]|[^\s={}<>]+', uncommented)


def loc_entries(value: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in value.splitlines()[1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r' ([A-Za-z0-9_.]+):0 "((?:[^"\\]|\\.)*)"', line)
        if match is None:
            raise ValueError(f"invalid localization row: {line!r}")
        key, localized = match.groups()
        if key in entries:
            raise ValueError(f"duplicate localization key: {key}")
        entries[key] = localized
    return entries


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    errors = builder.release_source_errors(MOD)
    expected_descriptor = (
        'version="1.0.0"\n'
        'tags={\n'
        '\t"Gameplay"\n'
        '\t"Balance"\n'
        '\t"Decisions"\n'
        '\t"Events"\n'
        '\t"1.19 \'Scribe\'"\n'
        '}\n'
        'name="天朝制允许经商&贪腐框架（XenoAmess维护版）"\n'
        'picture="thumbnail.png"\n'
        'supported_version="1.19.0.6"\n'
    )
    if read_text("descriptor.mod").replace("\r\n", "\n") != expected_descriptor:
        errors.append("descriptor.mod fields or ordering differ from the release contract")

    for relative in SCRIPT_PATHS:
        raw = (MOD / relative).read_bytes()
        try:
            value = raw.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            errors.append(f"invalid UTF-8: {relative}: {error}")
            continue
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            errors.append(f"UTF-16 is forbidden: {relative}")
        if "\ufffd" in value or "\x00" in value:
            errors.append(f"replacement or NUL character found: {relative}")
        if not balanced_braces(value):
            errors.append(f"unbalanced braces: {relative}")

    decision = read_text(SCRIPT_PATHS[0])
    for fragment in (
        "xccc_corruption_policy_decision = {",
        "cooldown = { years = 3 }",
        "ai_check_interval = 36",
        "government_has_flag = government_has_merit",
        "has_tgp_dlc_trigger = yes",
        "trigger_event = { id = xccc.1001 }",
    ):
        if fragment not in decision:
            errors.append(f"decision contract missing: {fragment}")
    if re.search(r"ai_check_interval\s*=\s*\{", decision):
        errors.append("ai_check_interval must use the CK3 1.19 integer-month syntax")

    government = read_text(SCRIPT_PATHS[1])
    if government.count("barter = yes") != 1:
        errors.append("celestial government must enable barter exactly once")
    for fragment in (
        "allow_as_base_for_baronies = no",
        "allow_accolades = yes",
        "accolades = -1",
        "house_aspirations = yes",
        "has_special_house_aspirations",
    ):
        if fragment not in government:
            errors.append(f"CK3 1.19 celestial government field missing: {fragment}")
    if "active_accolades" in government:
        errors.append("obsolete active_accolades modifier remains")
    vanilla_path = next((path for path in GAME_GOVERNMENTS if path.is_file()), None)
    if vanilla_path is not None:
        vanilla = vanilla_path.read_bytes().decode("utf-8-sig")
        try:
            vanilla_block = extract_named_block(vanilla, "celestial_government")
            maintained_block = extract_named_block(government, "celestial_government")
            maintained_without_barter = maintained_block.replace("barter = yes", "", 1)
            if semantic_tokens(maintained_without_barter) != semantic_tokens(vanilla_block):
                errors.append(
                    "celestial government differs from installed CK3 beyond barter = yes"
                )
        except ValueError as error:
            errors.append(f"cannot compare installed celestial government: {error}")

    values = read_text(SCRIPT_PATHS[2])
    expected_values = {
        "xccc_celestial_tax_default": "0.75",
        "xccc_corruption_1_tax_deduction": "0.05",
        "xccc_corruption_2_tax_deduction": "0.10",
        "xccc_corruption_3_tax_deduction": "0.15",
        "xccc_corruption_4_tax_deduction": "0.25",
    }
    for key, amount in expected_values.items():
        if not re.search(rf"(?m)^{re.escape(key)}\s*=\s*{re.escape(amount)}\s*$", values):
            errors.append(f"script value mismatch: {key} = {amount}")

    obligations = read_text(SCRIPT_PATHS[3])
    if obligations.count("celestial_obligations = {") != 1:
        errors.append("celestial_obligations must be overridden exactly once")
    if obligations.count("subtract = xccc_corruption_") != 4:
        errors.append("all four corruption tax deductions must be wired")
    if "value = xccc_celestial_tax_default" not in obligations or "min = 0" not in obligations:
        errors.append("celestial tax baseline or lower bound is missing")

    traits = read_text(SCRIPT_PATHS[4])
    events = read_text(SCRIPT_PATHS[5])
    for tier in range(1, 5):
        trait = f"xccc_corruption_{tier}"
        if traits.count(f"{trait} = {{") != 1:
            errors.append(f"trait definition missing or duplicated: {trait}")
        if events.count(f"add_trait = {trait}") != 1:
            errors.append(f"event does not add {trait} exactly once")
        if events.count(f"remove_trait = {trait}") != 5:
            errors.append(f"event does not remove {trait} on all five other choices")
    for modifier in (
        "monthly_barter_goods",
        "monthly_barter_goods_mult",
        "monthly_merit",
        "build_speed",
        "build_gold_cost",
    ):
        if modifier not in traits:
            errors.append(f"maintained corruption modifier missing: {modifier}")
    if "namespace = xccc" not in events or "xccc.1001 = {" not in events:
        errors.append("xccc event namespace contract is broken")
    if "add_character_flag = xccc_never_corrupt" not in events:
        errors.append("permanent opt-out flag is not wired")

    forbidden_runtime = (
        MOD / "common/activities/activity_types/feast.txt",
        MOD / "gui/window_county_view.gui",
    )
    for path in forbidden_runtime:
        if path.exists():
            errors.append(f"stale full-file override is forbidden: {path.relative_to(MOD)}")
    joined_scripts = "\n".join(read_text(relative) for relative in SCRIPT_PATHS)
    for stale in ("tanguan", "tan.", "active_accolades", "ai_check_interval = {"):
        if stale in joined_scripts:
            errors.append(f"stale upstream token remains: {stale}")

    localized: dict[str, dict[str, str]] = {}
    for language, header in LOCALIZATIONS.items():
        relative = f"localization/{language}/xccc_l_{language}.yml"
        raw = (MOD / relative).read_bytes()
        if not raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"localization lacks UTF-8 BOM: {relative}")
        value = raw.decode("utf-8-sig")
        if value.splitlines()[0] != f"{header}:":
            errors.append(f"wrong localization header: {relative}")
            continue
        try:
            entries = loc_entries(value)
        except ValueError as error:
            errors.append(f"{relative}: {error}")
            continue
        if set(entries) != EXPECTED_LOC_KEYS:
            missing = sorted(EXPECTED_LOC_KEYS - set(entries))
            extra = sorted(set(entries) - EXPECTED_LOC_KEYS)
            errors.append(f"localization key mismatch: {relative}: missing={missing} extra={extra}")
        if any(not localized_value.strip() for localized_value in entries.values()):
            errors.append(f"blank localization value: {relative}")
        localized[language] = entries
    english = localized.get("english", {})
    for language, entries in localized.items():
        if set(entries) != set(english):
            errors.append(f"localization key inventory mismatch: {language}")
            continue
        if language != "english" and entries == english:
            errors.append(f"English placeholder localization remains: {language}")
        for key, source in english.items():
            candidate = entries[key]
            if sorted(protected_tokens(candidate)) != sorted(protected_tokens(source)):
                errors.append(f"protected token mismatch: {language}:{key}")
            if re.findall(r"\d+(?:\.\d+)?", candidate) != re.findall(
                r"\d+(?:\.\d+)?", source
            ):
                errors.append(f"numeric contract mismatch: {language}:{key}")
    script_expectations = {
        "japanese": r"[\u3040-\u30ff]",
        "korean": r"[\uac00-\ud7a3]",
        "russian": r"[\u0400-\u04ff]",
        "simp_chinese": r"[\u4e00-\u9fff]",
    }
    for language, pattern in script_expectations.items():
        entries = localized.get(language, {})
        if entries and not any(re.search(pattern, value) for value in entries.values()):
            errors.append(f"{language} localization lacks its expected script")

    for relative, expected in ASSET_SHA256.items():
        path = MOD / relative
        if path.is_file() and sha256(path) != expected:
            errors.append(f"upstream-derived asset changed without an audited replacement: {relative}")
    thumbnail = MOD / "thumbnail.png"
    if thumbnail.stat().st_size >= 1_000_000:
        errors.append("thumbnail must remain below 1,000,000 bytes")
    try:
        with Image.open(thumbnail) as image:
            image.load()
            if image.size != (642, 642) or image.mode not in {"RGB", "RGBA"}:
                errors.append(f"thumbnail must be 642x642 RGB/RGBA, got {image.size} {image.mode}")
    except OSError as error:
        errors.append(f"cannot decode thumbnail.png: {error}")
    for relative in ASSET_SHA256:
        if relative.endswith(".dds") and not (MOD / relative).read_bytes().startswith(b"DDS "):
            errors.append(f"invalid DDS header: {relative}")

    workshop_image = workshop_media.DEFAULT_OUTPUT / workshop_media.OUTPUT_NAME
    screenshot_ledger = ROOT / "workshop/celestial_commerce_corruption_screenshots.md"
    if not workshop_image.is_file():
        errors.append("initial release requires the tracked gameplay Workshop JPEG")
    else:
        try:
            with Image.open(workshop_image) as image:
                image.load()
                expected_size = (
                    workshop_media.CROP[2] - workshop_media.CROP[0],
                    workshop_media.CROP[3] - workshop_media.CROP[1],
                )
                if image.size != expected_size or image.mode != "RGB":
                    errors.append(
                        f"Workshop JPEG must be {expected_size} RGB, got "
                        f"{image.size} {image.mode}"
                    )
        except OSError as error:
            errors.append(f"cannot decode Workshop gameplay JPEG: {error}")
        if workshop_image.stat().st_size >= workshop_media.MAX_BYTES:
            errors.append("Workshop gameplay JPEG must remain below 2,000,000 bytes")
        if screenshot_ledger.is_file():
            ledger = screenshot_ledger.read_text(encoding="utf-8")
            digest = workshop_media.sha256_file(workshop_image).upper()
            if digest not in ledger or "result `GREEN`" not in ledger:
                errors.append("Workshop screenshot ledger is stale against the JPEG")
        else:
            errors.append("initial release requires the Workshop screenshot ledger")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("CELESTIAL COMMERCE & CORRUPTION STATIC VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "CELESTIAL COMMERCE & CORRUPTION STATIC VALIDATION OK\n"
        f"Runtime files: {len(builder.RUNTIME_FILES)}\n"
        f"Release languages: {len(LOCALIZATIONS)}\n"
        "Compatibility delta: celestial_government barter = yes only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
