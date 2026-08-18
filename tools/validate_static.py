#!/usr/bin/env python3
"""Repository-wide static release checks run before CK3 acceptance."""

import importlib.util
import re
import sys
from pathlib import Path

from PIL import Image

import gen_pools
import gen_score_preview
import validate_loc


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
LANGS = validate_loc.LANGS


def read(path):
    return path.read_text(encoding="utf-8-sig", errors="replace")


def normalized(text):
    return text.replace("\r\n", "\n")


def load_highscore_generator():
    path = MOD / "tools" / "gen_highscore.py"
    spec = importlib.util.spec_from_file_location("xar_gen_highscore", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_block(text, key):
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*{{", text)
    if not match:
        return None
    start = text.index("{", match.start())
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[match.start():index + 1]
    return None


def generated_checks(errors):
    expected = {
        MOD / "common/scripted_effects/xar_generated_pools_effects.txt":
            gen_pools.gen_effects(gen_pools.B, "bless", "xar_draw_blessings_effect", "xar_apply_blessing_effect")
            + "\n" + gen_pools.gen_effects(gen_pools.C, "curse", "xar_draw_curses_effect", "xar_apply_curse_effect")
            + gen_pools.gen_sweep(),
        MOD / "common/customizable_localization/xar_generated_pool_loc.txt":
            gen_pools.gen_custom_loc(gen_pools.B, "bless") + "\n"
            + gen_pools.gen_custom_loc(gen_pools.C, "curse"),
        MOD / "common/modifiers/xar_generated_pool_modifiers.txt": gen_pools.gen_modifiers(),
        ROOT / "docs/blessing-curse-pools.md": gen_pools.gen_doc(),
        MOD / "common/script_values/xar_generated_score_preview.txt": gen_score_preview.generate(),
    }
    for lang in gen_pools.LANGS:
        lines = ([f"l_{lang}:", f' xar_pool_invalid:0 "{gen_pools.POOL_INVALID[lang]}"', ""]
                 + gen_pools.gen_yml(gen_pools.B, "bless", lang) + [""]
                 + gen_pools.gen_yml(gen_pools.C, "curse", lang) + [""]
                 + gen_pools.gen_modifier_yml(lang))
        expected[MOD / f"localization/{lang}/xar_generated_pools_l_{lang}.yml"] = (
            "\n".join(lines) + "\n")

    highscore = load_highscore_generator()
    expected.update({
        MOD / "common/tutorial_lessons/xar_highscore.txt": highscore.gen_lessons(),
        MOD / "common/customizable_localization/xar_generated_loc.txt": highscore.gen_custom_loc(),
        MOD / "common/scripted_guis/xar_generated_guis.txt": highscore.gen_guis(),
        MOD / "common/scripted_effects/xar_generated_effects.txt": highscore.gen_effects(),
        MOD / "gui/xar_meta.gui": highscore.gen_gui(),
        MOD / "gui/xar_trait_test.gui": highscore.gen_trait_test_gui(),
    })
    for lang in LANGS:
        expected[MOD / f"localization/{lang}/xar_generated_l_{lang}.yml"] = highscore.gen_loc(lang)

    for path, wanted in expected.items():
        if not path.exists():
            errors.append(f"generated output missing: {path.relative_to(ROOT)}")
        elif normalized(read(path)) != normalized(wanted):
            errors.append(f"generated output stale: {path.relative_to(ROOT)}")


def encoding_and_loc_checks(errors):
    for path in MOD.rglob("*"):
        if path.suffix.lower() not in {".txt", ".gui", ".yml"}:
            continue
        if not path.read_bytes().startswith(b"\xef\xbb\xbf"):
            errors.append(f"missing UTF-8 BOM: {path.relative_to(ROOT)}")

    all_values = {lang: {} for lang in LANGS}
    for lang in LANGS:
        for path in (MOD / "localization" / lang).glob("*.yml"):
            text = read(path)
            if not text.startswith(f"l_{lang}:"):
                errors.append(f"bad yml language header: {path.relative_to(ROOT)}")
            for match in re.finditer(r'(?m)^\s*([\w.]+):\d+\s+"(.*)"\s*$', text):
                key = match.group(1)
                if key in all_values[lang]:
                    errors.append(f"duplicate loc key '{key}' in {lang}")
                all_values[lang][key] = match.group(2)

    required = set()
    for path in (MOD / "events").glob("*.txt"):
        text = read(path)
        required.update(re.findall(
            r"(?m)^\s*(?:title|desc|name|custom_tooltip)\s*=\s*(xar[\w.]+)\s*$", text))
    for path in (MOD / "gui").rglob("*.gui"):
        required.update(re.findall(r"Localize\(\s*'([^']+)'\s*\)", read(path)))

    custom_defined = set()
    for path in (MOD / "common/customizable_localization").glob("*.txt"):
        text = read(path)
        custom_defined.update(re.findall(r"(?m)^(xar_\w+)\s*=\s*{", text))
        required.update(re.findall(r"localization_key\s*=\s*(xar_\w+)", text))
    for key in custom_defined:
        for lang in LANGS:
            if key in all_values[lang]:
                errors.append(f"custom resolver '{key}' masked by {lang} yml")

    trait_text = read(MOD / "common/traits/xar_traits.txt")
    trait_keys = re.findall(r"(?m)^(xar_\w+)\s*=\s*{", trait_text)
    for key in trait_keys:
        required.update({f"trait_{key}", f"trait_{key}_desc"})
    required.update(re.findall(r"desc\s*=\s*(trait_xar_\w+)", trait_text))
    required.update({"trait_track_xar_glassfire_gaze", "trait_track_xar_glassfire_gaze_desc"})

    required.update({
        "rule_xar_enabled", "setting_xar_on", "setting_xar_on_desc",
        "setting_xar_off", "setting_xar_off_desc", "setting_xar_selftest",
        "setting_xar_selftest_desc",
    })
    required.update(validate_loc.collect_modifier_keys())

    for key in sorted(required):
        for lang in LANGS:
            if key not in all_values[lang]:
                errors.append(f"loc key '{key}' missing in {lang}")


def mechanic_checks(errors):
    events = read(MOD / "events/xar_events.txt")
    for event_id in ("xar.0001", "xar.0002", "xar.0003", "xar.0004", "xar.0005",
                     "xar.0006", "xar.0007", "xar.0008", "xar.0009", "xar.1001"):
        block = extract_block(events, event_id)
        if not block or "trigger = { is_ai = no }" not in block:
            errors.append(f"event '{event_id}' lacks its AI guard")
    if "name = xar_curse_option_c" in events:
        errors.append("curse event still exposes a third option")
    if events.count("name = xar_curse_option_") != 2:
        errors.append("curse event must expose exactly two generated options")

    on_actions = read(MOD / "common/on_action/xar_on_actions.txt")
    start = extract_block(on_actions, "xar_on_game_start") or ""
    death = extract_block(on_actions, "xar_on_death") or ""
    if "every_player" not in start:
        errors.append("game-start entry is no longer player-only")
    if "has_character_flag = xa_enabled" not in death or "is_ai = no" not in death:
        errors.append("death entry lost the player flag/is_ai dual gate")

    trait = read(MOD / "common/traits/xar_traits.txt")
    thresholds = [int(value) for value in re.findall(
        r"(?m)^\s*(\d+)\s*=\s*{\s*stress_gain_mult\s*=\s*0\.1\s*}", trait)]
    if thresholds != list(range(10, 101, 10)):
        errors.append(f"Glassfire trait track must be 10..100 by 10, got {thresholds}")

    pools = read(MOD / "common/scripted_effects/xar_generated_pools_effects.txt")
    curse_draw = extract_block(pools, "xar_draw_curses_effect") or ""
    if "xa_curse_c" in curse_draw:
        errors.append("generated curse draw still contains slot C")
    if curse_draw.count("random_list = {") != 2:
        errors.append("generated curse draw must contain exactly two random lists")
    if curse_draw.count("xa_selected_bless_rarity < 2") != 70 * 2:
        errors.append("common curse rarity guards are incomplete")
    if pools.count("add_trait_xp = { trait = xar_glassfire_gaze value = 1 }") != 100:
        errors.append("each of the 100 curse dispatcher branches must grant exactly 1 trait XP")

    preview = read(MOD / "common/script_values/xar_generated_score_preview.txt")
    if re.search(r"\b(?:set|change|add|remove)_(?:global_)?variable\b", preview):
        errors.append("score preview contains a state-mutating variable effect")
    if "xar_current_score_value" not in preview:
        errors.append("score preview script value missing")
    score_effects = read(MOD / "common/scripted_effects/xar_effects.txt")
    if score_effects.count("xar_descendant_tier_count_effect = yes") != 1:
        errors.append("descendant title score is not using the single deduplicated traversal")


def package_checks(errors):
    descriptor = read(MOD / "descriptor.mod")
    if "remote_file_id" in descriptor:
        errors.append("repository descriptor.mod contains remote_file_id")
    expected_images = {
        MOD / "thumbnail.png": (640, 640),
        MOD / "gfx/interface/icons/traits/glassfire_trait.dds": (120, 120),
        MOD / "gfx/interface/icons/trait_level_tracks/xar_glassfire_gaze.dds": (120, 120),
        MOD / "gfx/interface/illustrations/event_scenes/xar_glassfire_avatar.dds": (1592, 848),
    }
    for path, size in expected_images.items():
        if not path.exists():
            errors.append(f"asset missing: {path.relative_to(ROOT)}")
            continue
        try:
            with Image.open(path) as image:
                if image.size != size:
                    errors.append(f"asset size {path.relative_to(ROOT)}: {image.size} != {size}")
        except OSError as error:
            errors.append(f"asset unreadable {path.relative_to(ROOT)}: {error}")


def main():
    errors = []
    if validate_loc.main() != 0:
        errors.append("focused localization validation failed")
    generated_checks(errors)
    encoding_and_loc_checks(errors)
    mechanic_checks(errors)
    package_checks(errors)
    if errors:
        print("STATIC VALIDATION FAILED")
        for error in errors:
            print(f"  {error}")
        return 1
    print("STATIC VALIDATION OK: generated parity, BOM/loc, mechanics/AI, package/assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
