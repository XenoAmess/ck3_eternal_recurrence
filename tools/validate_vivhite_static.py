#!/usr/bin/env python3
"""Static release validation for the standalone Vivhite courtier mod."""

from __future__ import annotations

import re
import struct
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath


sys.dont_write_bytecode = True
from PIL import Image  # noqa: E402

import build_vivhite_release as build_release  # noqa: E402
import gen_vivhite_courtier as generator  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / build_release.PRODUCT_ID
ORIGINAL_MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
ACCEPTANCE_FIXTURE = ROOT / "tools" / "fixtures" / "vivhite_acceptance"
ACCEPTANCE_RUNNER = ROOT / "tools" / "run_vivhite_acceptance.py"
PROCESS_WATCHDOG = ROOT / "tools" / "process_watchdog.py"
UTF8_BOM = b"\xef\xbb\xbf"
DUAL_ONLY_BEGIN = "# ERVA_DUAL_ONLY_BEGIN"
DUAL_ONLY_END = "# ERVA_DUAL_ONLY_END"
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
OTHER_LANGUAGES = tuple(
    language for language in LANGUAGES if language not in {"english", "simp_chinese"}
)
DESCRIPTOR_FIELDS = {
    "version": "1.0.0",
    "name": "琉焰卿的永恒轮回：典造琉焰廷臣·白绮特供版",
    "picture": "thumbnail.png",
    "supported_version": "1.19.0.6",
}
GROUP_KEY = "decision_group_type_ervc_courtier_creator"
DECISION_TITLE_KEY = "ervc_courtier_creator_decision"
ENGLISH_GROUP_BRANDING = (
    "@ervc_decision_group_icon! Eternal Recurrence: "
    "Glassfire Courtier Creator - Vivhite Edition"
)
CHINESE_GROUP_BRANDING = (
    "@ervc_decision_group_icon! 琉焰卿的永恒轮回：典造琉焰廷臣·白绮特供版"
)
EXPECTED_LOC_KEYS = frozenset(
    {
        GROUP_KEY,
        "ervc_courtier_creator_decision",
        "ervc_courtier_creator_decision_desc",
        "ervc_courtier_creator_decision_tooltip",
        "ervc_courtier_creator_decision_confirm",
        "ervc.cc.title",
        "ervc.cc.intro",
        "ervc.cc.sex",
        "ervc.cc.age",
        "ervc.cc.base_stats",
        "ervc.cc.education.help",
        "ervc.cc.commander.help",
        "ervc.cc.physical.help",
        "ervc.cc.personality.help",
        "ervc.cc.other.help",
        "ervc.cc.origin.help",
        "ervc.cc.culture",
        "ervc.cc.faith",
        "ervc.cc.dynasty_house",
        "ervc.cc.lowborn",
        "ervc.cc.same_house",
        "ervc.cc.price",
        "ervc.cc.confirm",
        "ervc.cc.cancel",
        "ervc.cc.insufficient_gold",
        "ervc.cc.invalid_configuration",
        "ervc.cc.toast.title",
        "ervc.cc.toast.desc",
        *{f"ervc.cc.tab.{name}" for name in (
            "basic", "education", "commander", "physical", "personality",
            "other", "origin",
        )},
        *{f"ervc.cc.skill.{name}" for name in (
            "diplomacy", "martial", "stewardship", "intrigue", "learning",
            "prowess",
        )},
        *{f"ervc.cc.numeric.{name}" for name in (
            "minus_10", "minus_1", "plus_1", "plus_10",
        )},
    }
)
EXPECTED_TABS = {
    "basic", "education", "commander", "physical", "personality", "other",
    "origin",
}
OPTIONAL_TRANSLATED_DIGITS = {
    # These quantities are words in English but conventionally digits in Japanese.
    "ervc.cc.base_stats": {"6"},
    "ervc.cc.education.help": {"1"},
}
SKILLS = (
    "diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess",
)
CATALOGS = ("education", "commander", "physical", "personality", "other")
FORBIDDEN_SUBSYSTEM_DIRECTORIES = {
    "common/customizable_localization",
    "common/event_backgrounds",
    "common/game_rules",
    "common/modifiers",
    "common/on_action",
    "common/traits",
    "common/tutorial_lessons",
    "events",
    "images",
    "tools",
}
EXPECTED_ACCEPTANCE_FIXTURE_FILES = frozenset(
    {
        "descriptor.mod",
        "common/game_rules/erva_acceptance_game_rules.txt",
        "common/decision_group_types/erva_acceptance_decision_group_types.txt",
        "common/decisions/erva_acceptance_decisions.txt",
        "common/scripted_effects/erva_acceptance_effects.txt",
        "common/scripted_guis/erva_acceptance_guis.txt",
        "common/scripted_triggers/erva_acceptance_triggers.txt",
        "events/erva_acceptance_events.txt",
        "gui/erva_acceptance_bridge.gui",
        "gui/scripted_widgets/erva_acceptance_scripted_widgets.txt",
        "localization/english/erva_acceptance_l_english.yml",
        "localization/simp_chinese/erva_acceptance_l_simp_chinese.yml",
    }
)
STANDALONE_ACCEPTANCE_MARKERS = (
    "ERVA: TEST BEGIN standalone",
    "ERVA: TEST PASS ai_fixture_ready",
    "ERVA: TEST PASS ai_guard",
    "ERVA: TEST PASS cancel_zero_side_effect",
    "ERVA: TEST PASS insufficient_119_blocked",
    "ERVA: TEST PASS default_120_one_delivery_one_charge",
    "ERVA: TEST PASS selected_faith_aluk",
    "ERVA: TEST PASS custom_348_ready",
    "ERVA: TEST PASS custom_configuration_retained",
    "ERVA: TEST PASS custom_configuration_reopened",
    "ERVA: TEST PASS custom_348_one_delivery_one_charge",
    "ERVA: TEST DONE standalone",
)
DUAL_ACCEPTANCE_MARKERS = (
    "ERVA: TEST BEGIN dual",
    "ERVA: TEST PASS ervc_custom_348_staged",
    "ERVA: TEST PASS ervc_configuration_retained",
    "ERVA: TEST PASS xar_default_isolated_from_ervc",
    "ERVA: TEST PASS xar_configuration_retained",
    "ERVA: TEST PASS ervc_state_retained_after_xar",
    "ERVA: TEST PASS ervc_348_one_delivery_one_charge",
    "ERVA: TEST PASS xar_state_retained_after_ervc",
    "ERVA: TEST PASS xar_120_one_delivery_one_charge",
    "ERVA: TEST DONE dual",
)


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def normalized(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def relative(path: Path, root: Path = ROOT) -> str:
    return Path(path).relative_to(root).as_posix()


def require_tokens(
    errors: list[str], text: str, tokens: tuple[str, ...] | list[str], label: str
) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        errors.append(f"{label} missing required token(s): {missing}")


def _structural_text(text: str) -> str:
    """Blank comments and quoted text while retaining lines and script syntax."""
    output: list[str] = []
    in_string = False
    escaped = False
    in_comment = False
    for character in text:
        if in_comment:
            if character == "\n":
                in_comment = False
                output.append(character)
            else:
                output.append(" ")
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            output.append("\n" if character == "\n" else " ")
            continue
        if character == "#":
            in_comment = True
            output.append(" ")
        elif character == '"':
            in_string = True
            output.append(" ")
        else:
            output.append(character)
    return "".join(output)


def brace_error(text: str) -> str | None:
    structural = _structural_text(text)
    stack: list[int] = []
    line = 1
    for character in structural:
        if character == "\n":
            line += 1
        elif character == "{":
            stack.append(line)
        elif character == "}":
            if not stack:
                return f"unexpected closing brace on line {line}"
            stack.pop()
    if stack:
        return f"unclosed opening brace on line {stack[-1]}"
    return None


def _block_end(text: str, opening: int) -> int | None:
    depth = 0
    in_string = False
    escaped = False
    in_comment = False
    for index in range(opening, len(text)):
        character = text[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == "#":
            in_comment = True
        elif character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def extract_block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*{{", text)
    if match is None:
        return ""
    opening = text.find("{", match.start(), match.end())
    ending = _block_end(text, opening)
    return text[match.start():ending] if ending is not None else ""


def extract_block_from_match(text: str, match: re.Match[str] | None) -> str:
    if match is None:
        return ""
    opening = text.find("{", match.start(), match.end())
    ending = _block_end(text, opening)
    return text[match.start():ending] if ending is not None else ""


def top_level_keys(text: str, pattern: str = r"[A-Za-z_][\w.]*") -> list[str]:
    structural = _structural_text(text)
    keys: list[str] = []
    depth = 0
    for line in structural.splitlines():
        if depth == 0:
            match = re.match(rf"\s*({pattern})\s*=\s*{{", line)
            if match:
                keys.append(match.group(1))
        depth += line.count("{") - line.count("}")
    return keys


def package_checks(errors: list[str], report: dict[str, object]) -> None:
    errors.extend(build_release.release_source_errors(MOD))
    if not MOD.is_dir():
        return

    actual_files = {
        path.relative_to(MOD).as_posix() for path in MOD.rglob("*") if path.is_file()
    }
    if actual_files != build_release.RUNTIME_FILES:
        errors.append(
            "runtime inventory is not the exact 27-file allowlist: "
            f"missing={sorted(build_release.RUNTIME_FILES - actual_files)}, "
            f"extra={sorted(actual_files - build_release.RUNTIME_FILES)}"
        )
    report["files"] = len(actual_files)

    for forbidden in sorted(FORBIDDEN_SUBSYSTEM_DIRECTORIES):
        if (MOD / PurePosixPath(forbidden)).exists():
            errors.append(f"forbidden standalone subsystem path exists: {forbidden}")

    descriptor_path = MOD / "descriptor.mod"
    if descriptor_path.is_file():
        descriptor_bytes = descriptor_path.read_bytes()
        if descriptor_bytes.startswith(UTF8_BOM):
            errors.append("descriptor.mod must not have a UTF-8 BOM")
        try:
            descriptor = normalized(descriptor_bytes.decode("utf-8"))
        except UnicodeDecodeError as error:
            errors.append(f"descriptor.mod is not UTF-8: {error}")
            descriptor = ""
        if "remote_file_id" in descriptor:
            errors.append("canonical descriptor.mod contains remote_file_id")
        for field, expected in DESCRIPTOR_FIELDS.items():
            values = re.findall(
                rf'(?m)^{re.escape(field)}="([^"\n]+)"$', descriptor
            )
            if values != [expected]:
                errors.append(
                    f"descriptor.mod {field} must be exactly {expected!r}, got {values}"
                )
        if not re.search(r'(?ms)^tags=\{\n\s*"Gameplay"\n\}$', descriptor):
            errors.append("descriptor.mod tags must contain exactly Gameplay")

    bom_count = 0
    for relative_path in sorted(build_release.RUNTIME_FILES):
        path = MOD / PurePosixPath(relative_path)
        if not path.is_file():
            continue
        if path.suffix.lower() in {".txt", ".gui", ".yml"}:
            if not path.read_bytes().startswith(UTF8_BOM):
                errors.append(f"loadable text lacks UTF-8 BOM: {relative_path}")
            else:
                bom_count += 1
        if path.suffix.lower() in {".txt", ".gui"}:
            try:
                issue = brace_error(read_text(path))
            except UnicodeDecodeError as error:
                errors.append(f"loadable text is not UTF-8: {relative_path}: {error}")
                continue
            if issue:
                errors.append(f"unbalanced braces in {relative_path}: {issue}")
    report["bom_files"] = bom_count

    thumbnail = MOD / "thumbnail.png"
    if thumbnail.is_file() and thumbnail.stat().st_size >= 1_000_000:
        errors.append("thumbnail.png must remain below 1 MB")


def generator_checks(errors: list[str], report: dict[str, object]) -> None:
    try:
        source, traits = generator.load_snapshot()
        catalogs, union = generator.build_catalogs(traits)
        conflicts = generator.build_conflicts(traits, union)
        pairs = generator.conflict_pairs(union, conflicts)
        rendered, counts, digest, rendered_pair_count = generator.render_all()
    except (OSError, ValueError) as error:
        errors.append(f"Vivhite generator API validation failed: {error}")
        return

    expected_source = {
        "game_version": generator.EXPECTED_SOURCE_VERSION,
        "file": generator.EXPECTED_SOURCE_FILE,
        "sha256": generator.EXPECTED_SOURCE_SHA256,
    }
    if source != expected_source:
        errors.append(f"trait snapshot source metadata drifted: {source} != {expected_source}")
    if len(traits) != generator.EXPECTED_TRAIT_COUNT:
        errors.append(
            f"trait snapshot count is {len(traits)}, expected {generator.EXPECTED_TRAIT_COUNT}"
        )
    actual_counts = {name: len(catalogs[name]) for name in generator.CATALOG_NAMES}
    if actual_counts != generator.EXPECTED_COUNTS or counts != generator.EXPECTED_COUNTS:
        errors.append(
            f"catalog counts drifted: API={actual_counts}, render={counts}, "
            f"expected={generator.EXPECTED_COUNTS}"
        )
    if len(union) != 224:
        errors.append(f"trait catalog union is {len(union)}, expected 224")
    if len(pairs) != 95 or rendered_pair_count != 95:
        errors.append(
            f"trait conflict count drifted: API={len(pairs)}, render={rendered_pair_count}, expected=95"
        )
    if digest != generator.EXPECTED_SOURCE_SHA256:
        errors.append("generator reported an unexpected source snapshot SHA-256")

    expected_outputs = {
        "common/scripted_effects/ervc_generated_courtier_catalog_effects.txt",
        "common/scripted_triggers/ervc_generated_courtier_catalog_triggers.txt",
        "common/script_values/ervc_generated_courtier_catalog_values.txt",
    }
    rendered_paths = {path.relative_to(MOD).as_posix() for path in rendered}
    if rendered_paths != expected_outputs:
        errors.append(f"generator output inventory drifted: {sorted(rendered_paths)}")
    for path, content in rendered.items():
        if not generator.generated_file_matches(path, content):
            errors.append(f"generated output stale: {relative(path)}")

    report["traits"] = len(union)
    report["conflicts"] = len(pairs)


def parse_localization(path: Path, language: str, errors: list[str]) -> dict[str, str]:
    try:
        text = normalized(read_text(path))
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"cannot read localization/{language}/{path.name}: {error}")
        return {}
    lines = text.splitlines()
    expected_header = f"l_{language}:"
    if not lines or lines[0] != expected_header:
        errors.append(f"{path.name} must begin exactly with {expected_header}")
    values: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r'\s+([A-Za-z0-9_.]+):(\d+)\s+"(.*)"\s*', line)
        if match is None:
            errors.append(f"malformed localization line {relative(path)}:{line_number}")
            continue
        key, version, value = match.groups()
        if version != "0":
            errors.append(f"localization key {key!r} in {language} must use :0")
        if key in values:
            errors.append(f"duplicate localization key {key!r} in {language}")
        values[key] = value
    return values


def localization_tokens(value: str) -> list[str]:
    return sorted(re.findall(r"\[[^\[\]]+\]|\$[^$]+\$|@[A-Za-z0-9_]+!", value))


def numeric_literals(value: str) -> set[str]:
    return set(re.findall(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?", value))


def localization_checks(errors: list[str], report: dict[str, object]) -> None:
    localization_root = MOD / "localization"
    actual_languages = {
        path.name for path in localization_root.iterdir() if path.is_dir()
    } if localization_root.is_dir() else set()
    if actual_languages != set(LANGUAGES):
        errors.append(
            f"localization languages must be exactly {list(LANGUAGES)}; "
            f"got {sorted(actual_languages)}"
        )

    all_values: dict[str, dict[str, str]] = {}
    for language in LANGUAGES:
        directory = localization_root / language
        expected_name = f"ervc_l_{language}.yml"
        files = sorted(path.name for path in directory.glob("*.yml")) if directory.is_dir() else []
        if files != [expected_name]:
            errors.append(
                f"{language} localization file inventory must be [{expected_name!r}], got {files}"
            )
        path = directory / expected_name
        values = parse_localization(path, language, errors) if path.is_file() else {}
        all_values[language] = values
        keys = set(values)
        if keys != EXPECTED_LOC_KEYS or len(values) != 45:
            errors.append(
                f"{language} localization must contain the exact 45 standalone keys; "
                f"missing={sorted(EXPECTED_LOC_KEYS - keys)}, "
                f"extra={sorted(keys - EXPECTED_LOC_KEYS)}, count={len(values)}"
            )

    english = all_values.get("english", {})
    chinese = all_values.get("simp_chinese", {})
    if english.get(GROUP_KEY) != ENGLISH_GROUP_BRANDING:
        errors.append("English decision-group branding is not the fixed Vivhite value")
    if chinese.get(GROUP_KEY) != CHINESE_GROUP_BRANDING:
        errors.append("Simplified Chinese decision-group branding is not the fixed Vivhite value")

    placeholders: list[str] = []
    for language in OTHER_LANGUAGES:
        value = all_values.get(language, {}).get(GROUP_KEY, "")
        if value == ENGLISH_GROUP_BRANDING:
            placeholders.append(language)
        elif not value.startswith("@ervc_decision_group_icon! "):
            errors.append(f"{language} decision-group branding lost its icon prefix")

    inherited_keys = EXPECTED_LOC_KEYS - {GROUP_KEY, DECISION_TITLE_KEY}
    for language in LANGUAGES:
        original_path = (
            ORIGINAL_MOD / "localization" / language / f"xar_l_{language}.yml"
        )
        original = parse_localization(original_path, language, errors)
        standalone = all_values.get(language, {})
        for key in sorted(inherited_keys):
            original_key = key.replace("ervc", "xar", 1)
            expected = original.get(original_key)
            if expected is None:
                errors.append(
                    f"frozen original localization lacks inherited key {original_key!r} "
                    f"in {language}"
                )
                continue
            expected = expected.replace("xar_cc_", "ervc_cc_")
            if standalone.get(key) != expected:
                errors.append(
                    f"standalone localization drifted from frozen original for "
                    f"{key!r} in {language}"
                )

    for key in sorted(EXPECTED_LOC_KEYS):
        english_value = english.get(key, "")
        expected_tokens = localization_tokens(english_value)
        expected_numbers = numeric_literals(english_value)
        allowed_numbers = expected_numbers | OPTIONAL_TRANSLATED_DIGITS.get(key, set())
        for language in LANGUAGES:
            value = all_values.get(language, {}).get(key, "")
            if localization_tokens(value) != expected_tokens:
                errors.append(
                    f"protected localization token mismatch for {key!r} in {language}: "
                    f"{localization_tokens(value)} != {expected_tokens}"
                )
            actual_numbers = numeric_literals(value)
            if not expected_numbers.issubset(actual_numbers) or not actual_numbers.issubset(allowed_numbers):
                errors.append(
                    f"numeric literal mismatch for {key!r} in {language}: "
                    f"required={sorted(expected_numbers)}, actual={sorted(actual_numbers)}, "
                    f"allowed={sorted(allowed_numbers)}"
                )

    protected = {
        "ervc.cc.physical.help": "$trait_impotent$",
        "ervc.cc.commander.help": (
            "[GetPlayer.MakeScope.Var('ervc_cc_commander_count').GetValue|0]"
        ),
        "ervc.cc.personality.help": (
            "[GetPlayer.MakeScope.Var('ervc_cc_personality_count').GetValue|0]"
        ),
    }
    for language in LANGUAGES:
        for key, token in protected.items():
            if all_values.get(language, {}).get(key, "").count(token) != 1:
                errors.append(
                    f"{language} {key!r} must preserve exactly one {token!r}"
                )

    gui = read_text(MOD / "gui/ervc_courtier_creator.gui")
    referenced = set(re.findall(r"Localize\(\s*'([^']+)'\s*\)", gui))
    referenced.update(
        {
            GROUP_KEY,
            "ervc_courtier_creator_decision",
            "ervc_courtier_creator_decision_desc",
            "ervc_courtier_creator_decision_tooltip",
            "ervc_courtier_creator_decision_confirm",
            "ervc.cc.insufficient_gold",
            "ervc.cc.invalid_configuration",
            "ervc.cc.toast.title",
            "ervc.cc.toast.desc",
        }
    )
    if referenced != EXPECTED_LOC_KEYS:
        errors.append(
            "runtime localization references do not match the 45-key contract: "
            f"unreferenced={sorted(EXPECTED_LOC_KEYS - referenced)}, "
            f"unexpected={sorted(referenced - EXPECTED_LOC_KEYS)}"
        )

    report["languages"] = len(all_values)
    report["loc_keys"] = len(EXPECTED_LOC_KEYS)
    report["inherited_loc_keys"] = len(inherited_keys)
    report["placeholders"] = placeholders


def _expected_scripted_gui_ids() -> set[str]:
    identifiers = {
        "ervc_cc_window_gate_gui",
        "ervc_cc_cancel_gui",
        "ervc_cc_confirm_gui",
        "ervc_cc_toggle_trait_gui",
        "ervc_cc_trait_selected_gui",
        "ervc_cc_choose_male_gui",
        "ervc_cc_choose_female_gui",
        "ervc_cc_select_culture_gui",
        "ervc_cc_culture_selected_gui",
        "ervc_cc_select_faith_gui",
        "ervc_cc_faith_selected_gui",
        "ervc_cc_choose_lowborn_gui",
        "ervc_cc_choose_same_house_gui",
        "ervc_cc_lowborn_selected_gui",
        "ervc_cc_same_house_selected_gui",
    }
    for numeric in ("age", *SKILLS):
        for action in ("minus_10", "minus_1", "plus_1", "plus_10"):
            identifiers.add(f"ervc_cc_{numeric}_{action}_gui")
    return identifiers


def mechanics_checks(errors: list[str], report: dict[str, object]) -> None:
    decision_text = read_text(
        MOD / "common/decisions/ervc_courtier_creator_decisions.txt"
    )
    bridge_text = read_text(
        MOD / "common/scripted_guis/ervc_decision_bridge_guis.txt"
    )
    triggers = read_text(
        MOD / "common/scripted_triggers/ervc_courtier_creator_triggers.txt"
    )
    values = read_text(MOD / "common/script_values/ervc_courtier_creator_values.txt")
    effects = read_text(
        MOD / "common/scripted_effects/ervc_courtier_creator_effects.txt"
    )
    scripted_guis = read_text(
        MOD / "common/scripted_guis/ervc_courtier_creator_guis.txt"
    )
    generated_effects = read_text(
        MOD / "common/scripted_effects/ervc_generated_courtier_catalog_effects.txt"
    )
    generated_triggers = read_text(
        MOD / "common/scripted_triggers/ervc_generated_courtier_catalog_triggers.txt"
    )
    generated_values = read_text(
        MOD / "common/script_values/ervc_generated_courtier_catalog_values.txt"
    )
    gui = read_text(MOD / "gui/ervc_courtier_creator.gui")
    bridge_gui = read_text(MOD / "gui/ervc_decision_bridge.gui")
    registry = read_text(MOD / "gui/scripted_widgets/ervc_scripted_widgets.txt")
    group_text = read_text(
        MOD / "common/decision_group_types/ervc_decision_group_types.txt"
    )
    texticons = read_text(MOD / "gui/ervc_texticons.gui")

    decision_ids = top_level_keys(decision_text, r"ervc_[A-Za-z0-9_]+")
    if decision_ids != ["ervc_courtier_creator_decision"]:
        errors.append(f"standalone decision inventory drifted: {decision_ids}")
    decision = extract_block(decision_text, "ervc_courtier_creator_decision")
    shown = extract_block(decision, "is_shown")
    valid = extract_block(decision, "is_valid_showing_failures_only")
    effect = extract_block(decision, "effect")
    hidden_effect = extract_block(effect, "hidden_effect")
    ai_potential = extract_block(decision, "ai_potential")
    for label, guard in (("shown", shown), ("valid", valid)):
        require_tokens(
            errors,
            guard,
            (
                "is_ai = no",
                "is_alive = yes",
                "NOT = { has_character_flag = ervc_cc_open }",
                "NOT = { has_character_flag = ervc_cc_open_pending }",
            ),
            f"decision {label} player gate",
        )
    require_tokens(
        errors,
        decision,
        (
            "ai_check_interval = 0",
            "decision_group_type = ervc_courtier_creator",
            'reference = "gfx/interface/illustrations/decisions/decision_ervc_courtier.dds"',
        ),
        "standalone decision",
    )
    if "always = no" not in ai_potential:
        errors.append("standalone decision AI potential is not disabled")
    require_tokens(
        errors,
        hidden_effect,
        ("is_ai = no", "is_alive = yes", "add_character_flag = ervc_cc_open_pending"),
        "deferred decision effect",
    )
    if any(
        token in effect
        for token in (
            "ervc_cc_initialize_effect",
            "create_character",
            "remove_short_term_gold",
        )
    ):
        errors.append("decision preview performs initialization or transaction side effects")

    group = extract_block(group_text, "ervc_courtier_creator")
    require_tokens(
        errors, group, ("sort_order = 150", "gui_tags = { big_button }"),
        "decision group",
    )
    if "important_decision_group" in group:
        errors.append("standalone utility decision must not be important by default")
    require_tokens(
        errors,
        texticons,
        (
            "icon = ervc_decision_group_icon",
            'texture = "gfx/interface/icons/traits/ervc_glassfire_icon.dds"',
            "size = { 25 25 }",
            "offset = { 0 6 }",
            "fontsize = 16",
        ),
        "decision-group text icon",
    )

    bridge = extract_block(bridge_text, "ervc_cc_open_bridge_gui")
    bridge_shown = extract_block(bridge, "is_shown")
    bridge_effect = extract_block(bridge, "effect")
    require_tokens(
        errors,
        bridge_shown,
        (
            "is_ai = no",
            "is_alive = yes",
            "has_character_flag = ervc_cc_open_pending",
            "NOT = { has_character_flag = ervc_cc_open }",
        ),
        "decision bridge shown gate",
    )
    bridge_order = [
        bridge_effect.find("remove_character_flag = ervc_cc_open_pending"),
        bridge_effect.find("ervc_cc_initialize_effect = yes"),
        bridge_effect.find("ervc_cc_rebuild_trait_catalogs_effect = yes"),
        bridge_effect.find("ervc_cc_rebuild_culture_faith_catalogs_effect = yes"),
        bridge_effect.find("add_character_flag = ervc_cc_open"),
    ]
    if any(index < 0 for index in bridge_order) or bridge_order != sorted(bridge_order):
        errors.append("decision bridge must initialize all catalogs before opening the modal")
    require_tokens(
        errors, bridge_effect, ("is_ai = no", "is_alive = yes"),
        "decision bridge execution gate",
    )
    require_tokens(
        errors,
        bridge_gui,
        (
            "GetPlayer.IsValid",
            "ervc_cc_open_bridge_gui",
            "GuiScope.SetRoot( GetPlayer.MakeScope )",
        ),
        "player-rooted invisible bridge",
    )
    registry_lines = {
        line.strip() for line in normalized(registry).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    expected_registry = {
        "gui/ervc_decision_bridge.gui = ervc_decision_bridge_window",
        "gui/ervc_courtier_creator.gui = ervc_courtier_creator_window",
    }
    if registry_lines != expected_registry:
        errors.append(f"scripted-widget registry drifted: {sorted(registry_lines)}")

    access = extract_block(triggers, "ervc_cc_ui_access_trigger")
    require_tokens(
        errors,
        access,
        ("is_ai = no", "is_alive = yes", "has_character_flag = ervc_cc_open"),
        "courtier UI access trigger",
    )
    if "xa_enabled" in access:
        errors.append("standalone UI incorrectly depends on xa_enabled")

    global_sources = "\n".join((effects, triggers, scripted_guis, gui))
    if any(
        token in global_sources
        for token in (
            "set_global_variable",
            "has_global_variable",
            "remove_global_variable",
            "global_var:",
        )
    ):
        errors.append("standalone creator uses forbidden scalar global state")
    global_lists = set(
        re.findall(
            r"(?:clear_global_variable_list\s*=\s*"
            r"|(?:add_to_global_variable_list|any_in_global_list)\s*=\s*\{[^}]*?"
            r"(?:name|variable)\s*=\s*"
            r"|is_target_in_global_variable_list\s*=\s*\{[^}]*?name\s*=\s*"
            r"|GetGlobalList\('\s*)(ervc_cc_[A-Za-z0-9_]+)",
            global_sources,
            re.DOTALL,
        )
    )
    expected_global_lists = {
        "ervc_cc_catalog_cultures",
        "ervc_cc_catalog_culture_heritages",
    }
    if global_lists != expected_global_lists:
        errors.append(
            f"standalone must use exactly its two read-only global culture lists: "
            f"{sorted(global_lists)}"
        )

    initialize = extract_block(effects, "ervc_cc_initialize_effect")
    rebuild_origins = extract_block(
        effects, "ervc_cc_rebuild_culture_faith_catalogs_effect"
    )
    require_tokens(
        errors,
        initialize,
        (
            "NOT = { has_character_flag = ervc_cc_v2_initialized }",
            "name = ervc_cc_female value = 0",
            "name = ervc_cc_age value = 30",
            "name = ervc_cc_same_house value = 0",
            "name = ervc_cc_selected_culture value = root.culture",
            "name = ervc_cc_selected_faith value = root.faith",
            "trait:education_martial_3",
            "name = ervc_cc_selected_education",
            "name = ervc_cc_commander_count value = 0",
            "name = ervc_cc_personality_count value = 0",
            "add_character_flag = ervc_cc_v2_initialized",
        ),
        "creator defaults",
    )
    for skill in SKILLS:
        if f"name = ervc_cc_{skill} value = 6" not in initialize:
            errors.append(f"creator default for {skill} must remain six")
    require_tokens(
        errors,
        rebuild_origins,
        (
            "clear_global_variable_list = ervc_cc_catalog_cultures",
            "clear_global_variable_list = ervc_cc_catalog_culture_heritages",
            "every_culture_global = {",
            "has_same_culture_heritage = prev",
            "every_religion_global = {",
            "every_faith = {",
            "name = ervc_cc_catalog_faiths",
        ),
        "culture and faith catalog rebuild",
    )

    configuration = extract_block(triggers, "ervc_cc_valid_configuration_trigger")
    compact_configuration = compact(configuration)
    require_tokens(
        errors,
        compact_configuration,
        (
            "is_ai = no",
            "is_alive = yes",
            "has_character_flag = ervc_cc_v2_initialized",
            "OR = { var:ervc_cc_female = 0 var:ervc_cc_female = 1 }",
            "var:ervc_cc_age >= 0",
            "var:ervc_cc_age <= 120",
            "exists = var:ervc_cc_selected_culture",
            "exists = var:ervc_cc_selected_faith",
            "name = ervc_cc_catalog_cultures",
            "name = ervc_cc_catalog_faiths",
            "var:ervc_cc_same_house = 0",
            "var:ervc_cc_same_house = 1",
            "var:ervc_cc_age >= 16",
            "var:ervc_cc_age < 16",
            "name = ervc_cc_selected_education value = 1",
            "name = ervc_cc_selected_commander value <= 2",
            "name = ervc_cc_selected_personality value <= 3",
            "ervc_cc_selected_traits_compatible_trigger = yes",
        ),
        "final configuration gate",
    )
    for skill in SKILLS:
        require_tokens(
            errors,
            configuration,
            (f"var:ervc_cc_{skill} >= 0", f"var:ervc_cc_{skill} <= 100"),
            f"{skill} range gate",
        )
    for catalog in CATALOGS:
        require_tokens(
            errors,
            configuration,
            (
                f"ervc_selected_list = ervc_cc_selected_{catalog}",
                f"ervc_catalog_list = ervc_cc_catalog_{catalog}",
            ),
            f"{catalog} selected-list validation",
        )
    selected_list_validation = extract_block(
        triggers, "ervc_cc_selected_list_valid_trigger"
    )
    if (
        "any_in_list" not in selected_list_validation
        or "count = all" not in selected_list_validation
        or "every_in_list" in selected_list_validation
    ):
        errors.append("selected-list validation must use trigger-form any_in_list count=all")

    cost = extract_block(values, "ervc_courtier_creator_cost")
    require_tokens(
        errors,
        compact(cost),
        (
            "value = 50",
            "add = ervc_cc_arbitrary_age_cost",
            "add = ervc_cc_selected_trait_cost",
            *tuple(f"add = ervc_cc_{skill}_skill_cost" for skill in SKILLS),
            "subtract = 88",
            "round = yes",
            "min = 0",
        ),
        "courtier price wiring",
    )
    age_cost = extract_block(values, "ervc_cc_arbitrary_age_cost")
    require_tokens(
        errors,
        age_cost,
        (
            "var:ervc_cc_age <= 18",
            "add = 60",
            "var:ervc_cc_age <= 30",
            "multiply = 2.5",
            "var:ervc_cc_age < 45",
            "multiply = 2",
        ),
        "native arbitrary-age price anchors",
    )
    trait_cost_entries = generated_values.count(
        "ervc_cc_trait_is_selected_trigger = { ervc_trait = trait:"
    )
    if trait_cost_entries != 224:
        errors.append(f"generated selected-trait price wiring has {trait_cost_entries} entries, expected 224")
    if generated_effects.count("add_to_variable_list = {") != 224:
        errors.append("generated trait catalogs do not contain exactly 224 additions")
    if "ervc_cc_selected_traits_compatible_trigger" not in generated_triggers:
        errors.append("generated conflict compatibility trigger is missing")

    preconfirm = "\n".join((decision, bridge, scripted_guis, gui))
    forbidden_preconfirm = (
        "create_character",
        "remove_short_term_gold",
        "add_courtier",
        "death = {",
        "send_interface_toast",
    )
    leaked = [token for token in forbidden_preconfirm if token in preconfirm]
    if leaked:
        errors.append(f"transaction side effect exists before final confirmation: {leaked}")

    purchase = extract_block(effects, "ervc_cc_complete_purchase_effect")
    require_tokens(
        errors,
        purchase,
        (
            "ervc_cc_ui_access_trigger = yes",
            "ervc_cc_valid_configuration_trigger = yes",
            "gold >= ervc_courtier_creator_cost",
            "exists = var:ervc_cc_selected_culture",
            "exists = var:ervc_cc_selected_faith",
        ),
        "final transaction revalidation",
    )
    transaction_order = [
        purchase.find("remove_character_flag = ervc_cc_open"),
        purchase.find("create_character = {"),
        purchase.find("exists = scope:ervc_cc_created_courtier"),
        purchase.find("add_courtier = scope:ervc_cc_created_courtier"),
        purchase.rfind("is_courtier_of = root"),
        purchase.find("add_diplomacy_skill = scope:ervc_cc_purchase_diplomacy"),
        purchase.find(
            "ervc_cc_apply_selected_trait_list_effect = { ervc_list = ervc_cc_selected_education }"
        ),
        purchase.find("set_house = root.house"),
        purchase.find("flag = blocked_from_leaving"),
        purchase.find("remove_short_term_gold = ervc_courtier_creator_cost"),
    ]
    if (
        any(index < 0 for index in transaction_order)
        or transaction_order != sorted(transaction_order)
    ):
        errors.append("courtier delivery/configuration must complete before the one gold charge")
    if purchase.count("create_character = {") != 1:
        errors.append("final transaction must create exactly one character")
    if purchase.count("remove_short_term_gold = ervc_courtier_creator_cost") != 1:
        errors.append("final transaction must contain exactly one charge")
    if purchase.count("death = { death_reason = death_vanished }") != 1:
        errors.append("failed delivery must contain exactly one vanished rollback")

    create = extract_block(purchase, "create_character")
    require_tokens(
        errors,
        create,
        (
            "employer = root",
            "culture = root.var:ervc_cc_selected_culture",
            "faith = root.var:ervc_cc_selected_faith",
            "dynasty = none",
            "age = root.var:ervc_cc_age",
            "random_traits = no",
            "diplomacy = 0",
            "martial = 0",
            "stewardship = 0",
            "intrigue = 0",
            "learning = 0",
            "prowess = 0",
            "save_scope_as = ervc_cc_created_courtier",
        ),
        "deterministic created-courtier base",
    )
    for skill in SKILLS:
        if f"add_{skill}_skill = scope:ervc_cc_purchase_{skill}" not in purchase:
            errors.append(f"final transaction does not apply selected {skill}")
    for catalog in CATALOGS:
        if f"LIST = ervc_cc_selected_{catalog}" in purchase:
            errors.append(f"stale uppercase trait-list parameter remains for {catalog}")
        if (
            f"ervc_cc_apply_selected_trait_list_effect = "
            f"{{ ervc_list = ervc_cc_selected_{catalog} }}"
            not in purchase
        ):
            errors.append(f"final transaction does not apply the {catalog} trait list")
    require_tokens(
        errors,
        purchase,
        (
            "add_courtier = scope:ervc_cc_created_courtier",
            "set_house = root.house",
            "flag = blocked_from_leaving",
            "years = 25",
            "force_character_skill_recalculation = yes",
            "send_interface_toast = {",
        ),
        "delivered-courtier attachment",
    )
    apply_list = extract_block(effects, "ervc_cc_apply_selected_trait_list_effect")
    if "add_trait = scope:ervc_cc_selected_trait" not in apply_list:
        errors.append("selected trait scopes are not applied to the created courtier")

    success_match = re.search(
        r"(?ms)^\s*if\s*=\s*\{\s*limit\s*=\s*\{\s*"
        r"scope:ervc_cc_created_courtier\s*=\s*\{\s*is_courtier_of\s*=\s*root",
        purchase,
    )
    success_block = extract_block_from_match(purchase, success_match)
    else_matches = list(re.finditer(r"(?m)^\s*else\s*=\s*\{", purchase))
    failure_block = extract_block_from_match(
        purchase, else_matches[-1] if else_matches else None
    )
    if (
        "remove_short_term_gold = ervc_courtier_creator_cost" not in success_block
        or "death_vanished" in success_block
    ):
        errors.append("successful delivery branch does not own the sole charge")
    if (
        "death = { death_reason = death_vanished }" not in failure_block
        or "remove_short_term_gold" in failure_block
        or "send_interface_toast" in failure_block
    ):
        errors.append("failed delivery must vanish the character without charge or receipt")

    runtime_transaction_sources = "\n".join(
        (
            decision_text,
            bridge_text,
            triggers,
            values,
            effects,
            scripted_guis,
            generated_effects,
            generated_triggers,
            generated_values,
            gui,
            bridge_gui,
        )
    )
    for token, expected_count in (
        ("create_character = {", 1),
        ("remove_short_term_gold = ervc_courtier_creator_cost", 1),
        ("death = { death_reason = death_vanished }", 1),
    ):
        actual_count = runtime_transaction_sources.count(token)
        if actual_count != expected_count:
            errors.append(
                f"standalone runtime contains {actual_count} occurrences of {token!r}, expected {expected_count}"
            )

    gui_ids = set(top_level_keys(scripted_guis, r"ervc_cc_[A-Za-z0-9_]+_gui"))
    expected_gui_ids = _expected_scripted_gui_ids()
    if gui_ids != expected_gui_ids:
        errors.append(
            f"scripted GUI inventory drifted: missing={sorted(expected_gui_ids - gui_ids)}, "
            f"extra={sorted(gui_ids - expected_gui_ids)}"
        )
    for gui_id in sorted(gui_ids):
        block = extract_block(scripted_guis, gui_id)
        shown_guard = extract_block(block, "is_shown")
        valid_guard = extract_block(block, "is_valid")
        if "ervc_cc_ui_access_trigger = yes" not in shown_guard:
            errors.append(f"scripted GUI {gui_id} lacks the player-only shown gate")
        if gui_id != "ervc_cc_window_gate_gui" and (
            "ervc_cc_ui_access_trigger = yes" not in valid_guard
        ):
            errors.append(f"scripted GUI {gui_id} lacks the player-only validity gate")
        if f"GetScriptedGui('{gui_id}')" not in gui:
            errors.append(f"scripted GUI {gui_id} is not wired to the modal")

    cancel = extract_block(scripted_guis, "ervc_cc_cancel_gui")
    confirm = extract_block(scripted_guis, "ervc_cc_confirm_gui")
    if (
        "remove_character_flag = ervc_cc_open" not in cancel
        or "ervc_cc_complete_purchase_effect" in cancel
        or "remove_short_term_gold" in cancel
    ):
        errors.append("creator cancellation is not side-effect free")
    require_tokens(
        errors,
        confirm,
        (
            "ervc_cc_ui_access_trigger = yes",
            "ervc_cc_valid_configuration_trigger = yes",
            "gold >= ervc_courtier_creator_cost",
            "ervc_cc_complete_purchase_effect = yes",
        ),
        "final confirmation GUI",
    )
    if runtime_transaction_sources.count("ervc_cc_complete_purchase_effect = yes") != 1:
        errors.append("final purchase effect must have exactly one runtime caller")

    tabs = set(
        re.findall(
            r"GetVariableSystem\.(?:Set|HasValue)\('ervc_cc_tab', '([a-z_]+)'\)",
            gui,
        )
    )
    if tabs != EXPECTED_TABS or gui.count("button_tab = {") != 7:
        errors.append(
            f"creator must expose exactly seven tabs: tabs={sorted(tabs)}, "
            f"buttons={gui.count('button_tab = {')}"
        )
    for tab in EXPECTED_TABS:
        if f'name = "ervc_cc_{tab}_tab"' not in gui and tab != "basic":
            errors.append(f"creator tab pane missing: {tab}")
    require_tokens(
        errors,
        gui,
        (
            "ervc_cc_window_gate_gui",
            "filter_mouse = all",
            "ervc_courtier_creator_cost",
            "Scope.Trait",
            "Trait.MakeScope",
            'blockoverride "faith_context"',
            "GetPlayer.MakeScope.Var('ervc_cc_selected_faith').Faith",
            "Scope.Culture.GetHeritage",
            "CulturePillar.GetCulturesWithPillar",
            "Culture.GetTemplate",
            "Culture.MakeScope",
            "GetGlobalList('ervc_cc_catalog_culture_heritages')",
            "Scope.Faith",
            "Faith.MakeScope",
            "Faith.GetIcon",
            "progressbar_standard",
        ),
        "dynamic catalog and selected-faith GUI context",
    )
    for catalog in CATALOGS:
        if f"GetList('ervc_cc_catalog_{catalog}')" not in gui:
            errors.append(f"GUI does not render the {catalog} trait catalog")

    action_deltas = {
        "minus_10": -10,
        "minus_1": -1,
        "plus_1": 1,
        "plus_10": 10,
    }
    for numeric in ("age", *SKILLS):
        maximum = 120 if numeric == "age" else 100
        for action, delta in action_deltas.items():
            gui_id = f"ervc_cc_{numeric}_{action}_gui"
            block = compact(extract_block(scripted_guis, gui_id))
            expected_adjustment = (
                "ervc_cc_adjust_numeric_variable_effect = { "
                f"ervc_variable = ervc_cc_{numeric} ervc_delta = {delta} "
                f"ervc_min = 0 ervc_max = {maximum} }}"
            )
            if expected_adjustment not in block:
                errors.append(
                    f"numeric action {gui_id} is not clamped to 0..{maximum} by {delta}"
                )
            if f"GetScriptedGui('{gui_id}')" not in gui:
                errors.append(f"numeric action {gui_id} is not present in the modal")
    if "TryStartRulerDesigning" in runtime_transaction_sources:
        errors.append("standalone creator must not invoke the lobby-only Ruler Designer")

    report["tabs"] = len(tabs)


def isolation_checks(errors: list[str]) -> None:
    text_parts: list[str] = []
    for relative_path in sorted(build_release.RUNTIME_FILES):
        path = MOD / PurePosixPath(relative_path)
        if path.is_file() and path.suffix.lower() in build_release.TEXT_SUFFIXES:
            text_parts.append(read_text(path))
    runtime_text = "\n".join(text_parts)

    explicit_forbidden = (
        "xa_enabled",
        "XenoAmess_s_Eternal_Recurrence",
        "XAR_ACCEPTANCE_ONLY",
        "ACCEPTANCE_ONLY",
        "debug_log",
        "selftest",
        "erva_",
        "ERVA:",
        "ERVA_",
    )
    for token in explicit_forbidden:
        if token in runtime_text:
            errors.append(f"forbidden original/development dependency in runtime: {token}")

    subsystem_identifier = re.compile(
        r"\b(?:[A-Za-z][A-Za-z0-9]*_)+(?:recurrence|shop|scoring|score|"
        r"contract|ledger|tutorial)(?:_[A-Za-z0-9]+)*\b",
        re.IGNORECASE,
    )
    matches = sorted(set(subsystem_identifier.findall(runtime_text)))
    if matches:
        errors.append(f"forbidden non-courtier subsystem identifier(s): {matches}")
    hook_patterns = {
        "event dispatch": r"\btrigger_event\s*=",
        "event namespace": r"(?m)^\s*namespace\s*=",
        "on-action hook": r"\bon_actions?\s*=",
        "tutorial completion hook": r"\b(?:is_tutorial_lesson_completed|trigger_transition)\b",
        "original tutorial data context": r"\bTutorial\.",
    }
    for label, pattern in hook_patterns.items():
        if re.search(pattern, runtime_text):
            errors.append(f"standalone runtime contains forbidden {label}")


def _runtime_vfs_paths(mod: Path) -> dict[str, str]:
    paths: dict[str, str] = {}
    if not mod.is_dir():
        return paths
    for path in mod.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(mod).as_posix()
        root = PurePosixPath(relative_path).parts[0]
        if root in {"common", "events", "gfx", "gui", "localization"} or relative_path in {
            "descriptor.mod", "thumbnail.png"
        }:
            paths[relative_path.casefold()] = relative_path
    return paths


def _common_definitions(mod: Path) -> dict[str, list[str]]:
    definitions: dict[str, list[str]] = defaultdict(list)
    common = mod / "common"
    if not common.is_dir():
        return definitions
    for path in common.rglob("*.txt"):
        for key in top_level_keys(read_text(path)):
            definitions[key.casefold()].append(path.relative_to(mod).as_posix())
    return definitions


def _localization_names(mod: Path) -> set[str]:
    names: set[str] = set()
    localization = mod / "localization"
    if not localization.is_dir():
        return names
    for path in localization.rglob("*.yml"):
        text = read_text(path)
        names.update(
            key.casefold()
            for key in re.findall(r'(?m)^\s*([A-Za-z0-9_.]+):\d+\s+"', text)
        )
    return names


def _gui_declaration_names(mod: Path) -> tuple[set[str], list[str]]:
    names: set[str] = set()
    unnamespaced: list[str] = []
    gui_root = mod / "gui"
    if not gui_root.is_dir():
        return names, unnamespaced
    for path in gui_root.rglob("*.gui"):
        text = read_text(path)
        structural = _structural_text(text)
        declarations = re.findall(r"\btypes?\s+([A-Za-z_][A-Za-z0-9_]*)", structural)
        declarations.extend(
            re.findall(r'(?m)^\s*name\s*=\s*"?([A-Za-z_][A-Za-z0-9_]*)"?', text)
        )
        declarations.extend(
            re.findall(r'\bblock\s+"([A-Za-z_][A-Za-z0-9_]*)"', text)
        )
        declarations.extend(
            re.findall(r"(?m)^\s*icon\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", text)
        )
        for name in declarations:
            if name in {"_show", "_hide"}:
                continue
            names.add(name.casefold())
            if mod == MOD and not name.startswith("ervc_"):
                unnamespaced.append(f"{path.relative_to(mod).as_posix()}: {name}")
    registry = gui_root / "scripted_widgets"
    if registry.is_dir():
        for path in registry.glob("*.txt"):
            for name in re.findall(r"(?m)^\s*gui/[^=]+\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", read_text(path)):
                names.add(name.casefold())
                if mod == MOD and not name.startswith("ervc_"):
                    unnamespaced.append(f"{path.relative_to(mod).as_posix()}: {name}")
    return names, unnamespaced


def namespace_collision_checks(errors: list[str]) -> None:
    if not ORIGINAL_MOD.is_dir():
        errors.append(f"original mod is unavailable for collision checks: {ORIGINAL_MOD}")
        return

    standalone_paths = _runtime_vfs_paths(MOD)
    original_paths = _runtime_vfs_paths(ORIGINAL_MOD)
    allowed_root_collisions = {"descriptor.mod", "thumbnail.png"}
    path_collisions = sorted(
        key
        for key in standalone_paths.keys() & original_paths.keys()
        if key not in allowed_root_collisions
    )
    if path_collisions:
        errors.append(
            "standalone VFS paths collide with the original mod: "
            f"{[standalone_paths[key] for key in path_collisions]}"
        )

    standalone_definitions = _common_definitions(MOD)
    original_definitions = _common_definitions(ORIGINAL_MOD)
    duplicate_definitions = {
        name: paths for name, paths in standalone_definitions.items() if len(paths) != 1
    }
    if duplicate_definitions:
        errors.append(f"duplicate standalone common definitions: {duplicate_definitions}")
    unnamespaced_definitions = sorted(
        name for name in standalone_definitions if not name.startswith("ervc_")
    )
    if unnamespaced_definitions:
        errors.append(
            f"standalone common definitions are not ervc-namespaced: {unnamespaced_definitions}"
        )
    definition_collisions = sorted(
        standalone_definitions.keys() & original_definitions.keys()
    )
    if definition_collisions:
        errors.append(
            f"standalone common definitions collide with the original mod: {definition_collisions}"
        )

    loc_collisions = sorted(
        _localization_names(MOD) & _localization_names(ORIGINAL_MOD)
    )
    if loc_collisions:
        errors.append(
            f"standalone localization keys collide with the original mod: {loc_collisions}"
        )

    standalone_gui_names, unnamespaced_gui = _gui_declaration_names(MOD)
    original_gui_names, _ = _gui_declaration_names(ORIGINAL_MOD)
    if unnamespaced_gui:
        errors.append(f"standalone GUI declaration lacks ervc namespace: {unnamespaced_gui}")
    gui_collisions = sorted(standalone_gui_names & original_gui_names)
    if gui_collisions:
        errors.append(
            f"standalone GUI names collide with the original mod: {gui_collisions}"
        )


def _project_acceptance_fixture(text: str, include_dual: bool, label: str) -> str:
    output: list[str] = []
    inside_dual = False
    begin_count = 0
    end_count = 0
    for line in text.splitlines(keepends=True):
        marker = line.strip()
        if marker == DUAL_ONLY_BEGIN:
            if inside_dual:
                raise ValueError(f"nested dual-only marker in {label}")
            inside_dual = True
            begin_count += 1
            continue
        if marker == DUAL_ONLY_END:
            if not inside_dual:
                raise ValueError(f"unmatched dual-only end in {label}")
            inside_dual = False
            end_count += 1
            continue
        if include_dual or not inside_dual:
            output.append(line)
    if inside_dual or begin_count != end_count:
        raise ValueError(f"unbalanced dual-only markers in {label}")
    return "".join(output)


def acceptance_harness_checks(errors: list[str], report: dict[str, object]) -> None:
    if not ACCEPTANCE_FIXTURE.is_dir():
        errors.append(f"Vivhite acceptance fixture is missing: {ACCEPTANCE_FIXTURE}")
        return
    if not ACCEPTANCE_RUNNER.is_file():
        errors.append(f"Vivhite acceptance runner is missing: {ACCEPTANCE_RUNNER}")
        return
    if not PROCESS_WATCHDOG.is_file():
        errors.append(f"acceptance process watchdog is missing: {PROCESS_WATCHDOG}")
    if MOD in ACCEPTANCE_FIXTURE.parents or ACCEPTANCE_FIXTURE in MOD.parents:
        errors.append("acceptance fixture must remain outside the 27-file product root")

    actual_files = {
        path.relative_to(ACCEPTANCE_FIXTURE).as_posix()
        for path in ACCEPTANCE_FIXTURE.rglob("*")
        if path.is_file()
    }
    if actual_files != EXPECTED_ACCEPTANCE_FIXTURE_FILES:
        errors.append(
            "acceptance fixture inventory mismatch: "
            f"missing={sorted(EXPECTED_ACCEPTANCE_FIXTURE_FILES - actual_files)}, "
            f"extra={sorted(actual_files - EXPECTED_ACCEPTANCE_FIXTURE_FILES)}"
        )

    fixture_texts: list[str] = []
    standalone_fixture_texts: list[str] = []
    for relative_path in sorted(actual_files):
        path = ACCEPTANCE_FIXTURE / PurePosixPath(relative_path)
        data = path.read_bytes()
        if relative_path != "descriptor.mod" and path.suffix.lower() in {
            ".txt", ".gui", ".yml",
        } and not data.startswith(UTF8_BOM):
            errors.append(f"acceptance fixture lacks UTF-8 BOM: {relative_path}")
        text = data.decode("utf-8-sig")
        fixture_texts.append(text)
        try:
            standalone_projection = _project_acceptance_fixture(
                text, include_dual=False, label=relative_path
            )
            dual_projection = _project_acceptance_fixture(
                text, include_dual=True, label=relative_path
            )
        except ValueError as error:
            errors.append(f"acceptance fixture projection failed: {error}")
            standalone_projection = text
            dual_projection = text
        standalone_fixture_texts.append(standalone_projection)
        for mode, projection in (
            ("standalone", standalone_projection), ("dual", dual_projection)
        ):
            if DUAL_ONLY_BEGIN in projection or DUAL_ONLY_END in projection:
                errors.append(
                    f"acceptance fixture {relative_path} retains marker in {mode} projection"
                )
            if path.suffix.lower() in {".txt", ".gui"}:
                issue = brace_error(projection)
                if issue:
                    errors.append(
                        f"acceptance fixture {relative_path} {mode} projection: {issue}"
                    )
        if "remote_file_id" in text or build_release.ORIGINAL_WORKSHOP_ITEM_ID in text:
            errors.append(f"acceptance fixture contains Workshop identity: {relative_path}")
        if path.suffix.lower() in {".txt", ".gui"}:
            issue = brace_error(text)
            if issue:
                errors.append(f"acceptance fixture {relative_path}: {issue}")

    fixture_paths = _runtime_vfs_paths(ACCEPTANCE_FIXTURE)
    for product_root, label in ((MOD, "Vivhite"), (ORIGINAL_MOD, "original")):
        collisions = sorted(
            key
            for key in fixture_paths.keys() & _runtime_vfs_paths(product_root).keys()
            if key != "descriptor.mod"
        )
        if collisions:
            errors.append(
                f"acceptance fixture VFS paths collide with {label}: "
                f"{[fixture_paths[key] for key in collisions]}"
            )

    fixture_definitions = _common_definitions(ACCEPTANCE_FIXTURE)
    duplicate_definitions = {
        name: paths for name, paths in fixture_definitions.items() if len(paths) != 1
    }
    if duplicate_definitions:
        errors.append(
            f"duplicate acceptance fixture common definitions: {duplicate_definitions}"
        )
    unnamespaced_definitions = sorted(
        name for name in fixture_definitions if not name.startswith("erva_")
    )
    if unnamespaced_definitions:
        errors.append(
            "acceptance fixture common definitions are not erva-namespaced: "
            f"{unnamespaced_definitions}"
        )
    product_definitions = (
        set(_common_definitions(MOD)) | set(_common_definitions(ORIGINAL_MOD))
    )
    definition_collisions = sorted(set(fixture_definitions) & product_definitions)
    if definition_collisions:
        errors.append(
            f"acceptance fixture definitions collide with products: {definition_collisions}"
        )

    fixture_gui_names, _ = _gui_declaration_names(ACCEPTANCE_FIXTURE)
    unnamespaced_gui = sorted(
        name for name in fixture_gui_names if not name.startswith("erva_")
    )
    if unnamespaced_gui:
        errors.append(
            f"acceptance fixture GUI declarations are not erva-namespaced: {unnamespaced_gui}"
        )
    product_gui_names = (
        _gui_declaration_names(MOD)[0] | _gui_declaration_names(ORIGINAL_MOD)[0]
    )
    gui_collisions = sorted(fixture_gui_names & product_gui_names)
    if gui_collisions:
        errors.append(f"acceptance fixture GUI names collide with products: {gui_collisions}")

    localization = _localization_names(ACCEPTANCE_FIXTURE)
    invalid_loc = sorted(
        key
        for key in localization
        if not key.startswith((
            "erva_", "rule_erva_", "setting_erva_", "decision_group_type_erva_"
        ))
    )
    if invalid_loc:
        errors.append(
            f"acceptance fixture localization is not erva-namespaced: {invalid_loc}"
        )
    loc_collisions = sorted(
        localization
        & (_localization_names(MOD) | _localization_names(ORIGINAL_MOD))
    )
    if loc_collisions:
        errors.append(
            f"acceptance fixture localization collides with products: {loc_collisions}"
        )

    fixture_text = "\n".join(fixture_texts)
    standalone_fixture_text = "\n".join(standalone_fixture_texts)
    original_references = sorted(
        set(re.findall(r"\b(?:xar_|xa_)[A-Za-z0-9_]*", standalone_fixture_text))
    )
    if original_references:
        errors.append(
            "standalone acceptance projection retains original runtime references: "
            f"{original_references}"
        )
    runner = read_text(ACCEPTANCE_RUNNER)
    for marker in (*STANDALONE_ACCEPTANCE_MARKERS, *DUAL_ACCEPTANCE_MARKERS):
        if marker not in fixture_text:
            errors.append(f"acceptance fixture lacks marker: {marker}")
        if marker not in runner:
            errors.append(f"acceptance runner lacks marker contract: {marker}")

    required_runner_tokens = (
        '"vivhite-alone", ("vivhite",)',
        '("original", "vivhite")',
        '("vivhite", "original")',
        "enabled_mods.append(f\"mod/{FIXTURE_OUTER_NAME}\")",
        "build_vivhite_release.build_release",
        "build_release.build_release",
        "acceptance.configure_runtime_userdir(userdir)",
        "acceptance.launch_ck3_process(False)",
        "acceptance.stop_ck3_process(",
        "protected_snapshot",
        "verify_protected_storage",
        "real_workshop_snapshot",
        "runtime_trees_unchanged",
        "POSTFLIGHT_STABILITY_SECONDS = 5",
        "fixture_last",
        "verify_runtime_load_order",
        '"database_conflicts.log"',
        '"allowed_project_diagnostics"',
        "acceptance.start_process_watchdog(pid_path)",
        "ensure_test_paths_safe",
        "steam_workshop_app_roots",
        "installed_game_version",
        "expected_executable_sha256",
        "required_quiet_period_seconds",
        "except BaseException",
        '"workshop_item_id": None',
    )
    require_tokens(errors, runner, required_runner_tokens, "Vivhite acceptance runner")
    forbidden_runner_tokens = (
        "sync_repo_to_ugc(", "acceptance.kill_ck3(", "taskkill /IM",
        build_release.ORIGINAL_WORKSHOP_ITEM_ID,
    )
    leaked = [token for token in forbidden_runner_tokens if token in runner]
    if leaked:
        errors.append(f"Vivhite acceptance runner contains unsafe token(s): {leaked}")
    if PROCESS_WATCHDOG.is_file():
        watchdog = read_text(PROCESS_WATCHDOG)
        require_tokens(
            errors,
            watchdog,
            (
                "WaitForSingleObject",
                "ParentProcessId",
                '["taskkill", "/F", "/T", "/PID", str(ck3_pid)]',
                ".watchdog_error",
            ),
            "acceptance process watchdog",
        )
        if '"/IM"' in watchdog:
            errors.append("acceptance process watchdog must never kill by image name")
    if any("erva" in path for path in build_release.RUNTIME_FILES):
        errors.append("acceptance fixture leaked into the exact 27-file release allowlist")
    report["acceptance_fixture_files"] = len(actual_files)


def _dds_header(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 128 or data[:4] != b"DDS ":
        raise ValueError("missing DDS signature/header")
    return {
        "data": data,
        "header_size": struct.unpack_from("<I", data, 4)[0],
        "height": struct.unpack_from("<I", data, 12)[0],
        "width": struct.unpack_from("<I", data, 16)[0],
        "pixel_format_size": struct.unpack_from("<I", data, 76)[0],
        "pixel_flags": struct.unpack_from("<I", data, 80)[0],
        "fourcc": data[84:88],
        "rgb_bits": struct.unpack_from("<I", data, 88)[0],
        "masks": struct.unpack_from("<IIII", data, 92),
    }


def asset_checks(errors: list[str], report: dict[str, object]) -> None:
    thumbnail = MOD / "thumbnail.png"
    icon = MOD / "gfx/interface/icons/traits/ervc_glassfire_icon.dds"
    decision = MOD / "gfx/interface/illustrations/decisions/decision_ervc_courtier.dds"

    if thumbnail.is_file():
        data = thumbnail.read_bytes()
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append("thumbnail.png has an invalid PNG signature")
        try:
            with Image.open(thumbnail) as image:
                image.load()
                if image.format != "PNG" or image.size != (640, 640):
                    errors.append(
                        f"thumbnail.png must be 640x640 PNG, got {image.format} {image.size}"
                    )
        except OSError as error:
            errors.append(f"thumbnail.png is unreadable: {error}")

    expected_dds = {
        icon: {
            "size": (120, 120),
            "pixel_flags": 0x41,
            "fourcc": b"\0\0\0\0",
            "rgb_bits": 32,
            "masks": (0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000),
            "data_size": 128 + 120 * 120 * 4,
            "label": "unique trait icon",
        },
        decision: {
            "size": (1100, 440),
            "pixel_flags": 0x4,
            "fourcc": b"DXT1",
            "rgb_bits": 24,
            "masks": (0, 0, 0, 0),
            "data_size": 128 + ((1100 + 3) // 4) * ((440 + 3) // 4) * 8,
            "label": "unique decision art",
        },
    }
    for path, expected in expected_dds.items():
        if not path.is_file():
            errors.append(f"asset missing: {relative(path)}")
            continue
        try:
            header = _dds_header(path)
        except ValueError as error:
            errors.append(f"{expected['label']} invalid: {error}")
            continue
        actual_size = (header["width"], header["height"])
        if header["header_size"] != 124 or header["pixel_format_size"] != 32:
            errors.append(f"{expected['label']} has a nonstandard DDS header")
        for field in ("pixel_flags", "fourcc", "rgb_bits", "masks"):
            if header[field] != expected[field]:
                errors.append(
                    f"{expected['label']} {field} is {header[field]!r}, expected {expected[field]!r}"
                )
        if actual_size != expected["size"]:
            errors.append(
                f"{expected['label']} dimensions are {actual_size}, expected {expected['size']}"
            )
        if len(header["data"]) != expected["data_size"]:
            errors.append(
                f"{expected['label']} byte size is {len(header['data'])}, expected {expected['data_size']}"
            )
        try:
            with Image.open(path) as image:
                image.load()
                if image.format != "DDS" or image.size != expected["size"]:
                    errors.append(
                        f"{expected['label']} is not Pillow-readable DDS {expected['size']}"
                    )
        except OSError as error:
            errors.append(f"{expected['label']} is unreadable: {error}")
    report["assets"] = 3


def main() -> int:
    errors: list[str] = []
    report: dict[str, object] = {}
    checks = (
        ("package", package_checks),
        ("generator", generator_checks),
        ("localization", localization_checks),
        ("mechanics", mechanics_checks),
        ("isolation", lambda found, _report: isolation_checks(found)),
        ("namespace collision", lambda found, _report: namespace_collision_checks(found)),
        ("acceptance harness", acceptance_harness_checks),
        ("assets", asset_checks),
    )
    for label, check in checks:
        try:
            check(errors, report)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            errors.append(f"{label} checks could not complete: {error}")

    placeholders = report.get("placeholders", [])
    if errors:
        print(f"VIVHITE STATIC RED: {len(errors)} error(s)")
        for error in errors:
            print(f"  ERROR: {error}")
        if placeholders:
            print(
                "  INFO: accepted English edition-group placeholders (not translations): "
                + ", ".join(placeholders)
            )
        return 1

    placeholder_text = ", ".join(placeholders) if placeholders else "none"
    print(
        "VIVHITE STATIC GREEN: "
        f"{report.get('files')} files, {report.get('bom_files')} BOM text, "
        f"{report.get('traits')} traits/{report.get('conflicts')} conflicts, "
        f"{report.get('languages')}x{report.get('loc_keys')} localization, "
        f"{report.get('tabs')} tabs, 3 assets, "
        f"{report.get('acceptance_fixture_files')} external fixture files"
    )
    print(
        "Accepted English edition-group placeholders (not translations): "
        f"{placeholder_text}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
