#!/usr/bin/env python3
"""Repository-wide static release checks run before CK3 acceptance."""

import importlib.util
import re
import sys
from pathlib import Path

from PIL import Image

import build_release
import gen_contracts
import gen_pools
import gen_scoring
import gen_score_preview
import scoring_data
import validate_loc


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
LANGS = validate_loc.LANGS


def read(path):
    return path.read_text(encoding="utf-8-sig", errors="replace")


def normalized(text):
    return text.replace("\r\n", "\n")


def loc_format_tokens(value):
    """Tokens translators must preserve for CK3 formatting and interpolation."""
    return sorted(re.findall(r"\\n|\[[^\[\]]+\]|\$[\w.]+\$|#[A-Za-z]\w*|#!", value))


def load_highscore_generator():
    path = MOD / "tools" / "gen_highscore.py"
    spec = importlib.util.spec_from_file_location("xar_gen_highscore", path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
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


def top_level_keys(text, pattern):
    """Return top-level block keys matching pattern, ignoring nested blocks."""
    keys = []
    depth = 0
    for line in text.splitlines():
        if depth == 0:
            match = re.match(rf"\s*({pattern})\s*=\s*{{", line)
            if match:
                keys.append(match.group(1))
        depth += line.count("{") - line.count("}")
    return keys


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
        MOD / "common/scripted_effects/xar_generated_scoring_effects.txt":
            gen_scoring.generate_effects(),
        MOD / "common/script_values/xar_generated_score_preview.txt": gen_score_preview.generate(),
        ROOT / "docs/scoring-rules.md": gen_scoring.generate_doc(),
        MOD / "events/xar_generated_contract_events.txt": gen_contracts.generated_events(),
        MOD / "common/decisions/xar_generated_contract_decisions.txt": gen_contracts.generated_decision(),
        MOD / "common/scripted_effects/xar_generated_contract_effects.txt": gen_contracts.generated_effects(),
        MOD / "common/tutorial_lessons/xar_generated_contract_lessons.txt": gen_contracts.generated_lessons(),
        MOD / "common/customizable_localization/xar_generated_contract_loc.txt": gen_contracts.generated_custom_loc(),
        ROOT / "docs/contracts-and-progression.md": gen_contracts.generated_doc(),
    }
    for lang in gen_pools.LANGS:
        lines = ([f"l_{lang}:", f' xar_pool_invalid:0 "{gen_pools.POOL_INVALID[lang]}"', ""]
                 + gen_pools.gen_yml(gen_pools.B, "bless", lang) + [""]
                 + gen_pools.gen_yml(gen_pools.C, "curse", lang) + [""]
                 + gen_pools.gen_modifier_yml(lang))
        expected[MOD / f"localization/{lang}/xar_generated_pools_l_{lang}.yml"] = (
            "\n".join(lines) + "\n")
        expected[MOD / f"localization/{lang}/xar_generated_contracts_l_{lang}.yml"] = (
            gen_contracts.loc_lines(lang))

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
    for path in (MOD / "common/decisions").glob("*.txt"):
        text = read(path)
        for decision_id in top_level_keys(text, r"xar_\w+"):
            required.update({decision_id, f"{decision_id}_desc",
                             f"{decision_id}_tooltip", f"{decision_id}_confirm"})

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

    phase_one_loc_keys = {
        "xar.0010.title", "xar.0010.desc", "xar.0010.begin",
        "xar_ledger_decision", "xar_ledger_decision_desc",
        "xar_ledger_decision_tooltip", "xar_ledger_decision_confirm",
        "xar.0011.title", "xar.0011.desc", "xar.0011.desc_cap", "xar.0011.close",
    }
    for key in sorted(phase_one_loc_keys):
        english_tokens = loc_format_tokens(all_values["english"].get(key, ""))
        for lang in LANGS:
            actual_tokens = loc_format_tokens(all_values[lang].get(key, ""))
            if actual_tokens != english_tokens:
                errors.append(
                    f"loc format-token mismatch for '{key}' in {lang}: "
                    f"{actual_tokens} != {english_tokens}")

    for lang in LANGS:
        enabled_desc = all_values[lang].get("setting_xar_on_desc", "")
        if "tutorial" not in enabled_desc.lower():
                errors.append(f"enabled rule description lacks tutorial write prerequisite in {lang}")


def reference_model_checks(errors):
    try:
        scoring_data.assert_reference_vectors()
    except AssertionError as error:
        errors.append(f"scoring reference vector failed: {error}")


def mechanic_checks(errors):
    event_sources = {path: read(path) for path in (MOD / "events").glob("*.txt")}
    events = "\n".join(event_sources.values())
    event_blocks = {}
    for path, text in event_sources.items():
        for event_id in top_level_keys(text, r"xar\.\d+"):
            if event_id in event_blocks:
                errors.append(f"duplicate event '{event_id}' discovered in {path.relative_to(ROOT)}")
            event_blocks[event_id] = extract_block(text, event_id) or ""
    event_ids = list(event_blocks)
    if not event_ids:
        errors.append("no XAR events discovered")
    for event_id in event_ids:
        block = event_blocks[event_id]
        if not block or "trigger = { is_ai = no }" not in block:
            errors.append(f"event '{event_id}' lacks its AI guard")
    if "name = xar_curse_option_c" in events:
        errors.append("curse event still exposes a third option")
    if events.count("name = xar_curse_option_") != 2:
        errors.append("curse event must expose exactly two generated options")

    production_effects = read(MOD / "common/scripted_effects/xar_effects.txt")
    selftest = read(MOD / "common/scripted_effects/xar_selftest_effects.txt")
    shop = event_blocks.get("xar.0001", "")
    pact = event_blocks.get("xar.0002", "")
    first_life = event_blocks.get("xar.0010", "")
    ledger_event = event_blocks.get("xar.0011", "")

    shared_pact_effects = {
        "xar_enable_player_pact_effect",
        "xar_initialize_run_state_effect",
    }
    for effect in shared_pact_effects:
        call = f"{effect} = yes"
        if pact.count(call) != 1 or selftest.count(call) != 1:
            errors.append(f"production pact and selftest must each call shared '{effect}' once")
    enable_pact = extract_block(production_effects, "xar_enable_player_pact_effect") or ""
    if "add_character_flag = xa_enabled" not in enable_pact or "add_trait = xar_glassfire_gaze" not in enable_pact:
        errors.append("shared player pact effect lost its flag or trait")

    run_init = extract_block(production_effects, "xar_initialize_run_state_effect") or ""
    expected_run_init = {
        "xa_shop_page": "1", "xa_price_dip": "25", "xa_price_mar": "25",
        "xa_price_ste": "25", "xa_price_int": "25", "xa_price_lea": "25",
        "xa_price_pro": "25", "xa_price_gold": "25", "xa_price_pres": "15",
        "xa_price_pie": "15", "xa_price_inf": "15", "xa_price_dyn": "100",
        "xa_price_life": "100", "xa_price_reform": "1133",
        "xa_lifespan_bought": "0", "xa_bless_count": "0",
        "xa_bless_session": "0", "xa_bless_reject_count": "0",
        "xa_selected_bless_rarity": "0", "xa_score_baseline": "0",
        "xa_baseline_pending": "1",
        "xa_contract_id": "0", "xa_contract_progress": "0",
        "xa_reroll_tokens": "0", "xa_seal_tokens": "0",
        "xa_bless_a": "0", "xa_bless_b": "0", "xa_bless_c": "0",
        "xa_curse_a": "0", "xa_curse_b": "0",
        "xa_curse_a_rarity": "0", "xa_curse_b_rarity": "0",
    }
    actual_run_init = dict(re.findall(
        r"set_global_variable\s*=\s*\{\s*name\s*=\s*(xa_\w+)\s+value\s*=\s*(\d+)\s*\}",
        run_init,
    ))
    if actual_run_init != expected_run_init:
        errors.append("shared run/shop initialization is incomplete or has changed values")
    copied_init_names = {
        name for name in expected_run_init
        if name not in {
            "xa_contract_id", "xa_contract_progress", "xa_bless_a", "xa_bless_b",
            "xa_bless_c", "xa_curse_a", "xa_curse_b", "xa_curse_a_rarity",
            "xa_curse_b_rarity", "xa_reroll_tokens", "xa_seal_tokens",
        }
    }
    init_target_pattern = "|".join(map(re.escape, copied_init_names))
    copied_init = re.compile(
        rf"set_global_variable\s*=\s*\{{\s*name\s*=\s*(?:{init_target_pattern})\s+value\s*=\s*\d+"
    )
    if copied_init.search(pact) or copied_init.search(selftest):
        errors.append("pact event or selftest copied production run/shop initialization")

    shop_purchases = {
        "xar_buy_diplomacy_shop_item_effect": ("xa_price_dip", "add_diplomacy_skill = 1"),
        "xar_buy_martial_shop_item_effect": ("xa_price_mar", "add_martial_skill = 1"),
        "xar_buy_stewardship_shop_item_effect": ("xa_price_ste", "add_stewardship_skill = 1"),
        "xar_buy_intrigue_shop_item_effect": ("xa_price_int", "add_intrigue_skill = 1"),
        "xar_buy_learning_shop_item_effect": ("xa_price_lea", "add_learning_skill = 1"),
        "xar_buy_prowess_shop_item_effect": ("xa_price_pro", "add_prowess_skill = 1"),
        "xar_buy_gold_shop_item_effect": ("xa_price_gold", "add_gold = 100"),
        "xar_buy_prestige_shop_item_effect": ("xa_price_pres", "add_prestige = 100"),
        "xar_buy_piety_shop_item_effect": ("xa_price_pie", "add_piety = 100"),
        "xar_buy_influence_shop_item_effect": ("xa_price_inf", "change_influence = 100"),
        "xar_buy_dynasty_prestige_shop_item_effect": ("xa_price_dyn", "add_dynasty_prestige = 100"),
        "xar_buy_lifespan_shop_item_effect": ("xa_price_life", "xar_buy_lifespan_effect = yes"),
    }
    for effect, (price, reward) in shop_purchases.items():
        call = f"{effect} = yes"
        block = extract_block(production_effects, effect) or ""
        charge = (
            f"name = xa_local_points add = {{ value = global_var:{price} multiply = -1 }}"
        )
        inflation = re.search(
            rf"set_global_variable\s*=\s*\{{\s*name\s*=\s*{price}\s*"
            rf"value\s*=\s*\{{\s*value\s*=\s*global_var:{price}\s*"
            r"multiply\s*=\s*1\.2\s*ceiling\s*=\s*yes\s*\}\s*\}",
            block,
        )
        if shop.count(call) != 1:
            errors.append(f"shop must call production purchase '{effect}' exactly once")
        if charge not in block or reward not in block or not inflation:
            errors.append(f"production purchase '{effect}' lost charge, reward, or integer inflation")
        if "selftest" in block or "_test_" in block:
            errors.append(f"production purchase '{effect}' depends on a selftest marker")

    diplomacy_call = "xar_buy_diplomacy_shop_item_effect = yes"
    if selftest.count(diplomacy_call) != 1:
        errors.append("selftest 25->30/charge example does not call the production diplomacy purchase")
    copied_diplomacy = (
        "add_diplomacy_skill = 1",
        "value = global_var:xa_price_dip multiply = 1.2 ceiling = yes",
        "name = xa_local_points add = { value = global_var:xa_price_dip multiply = -1 }",
    )
    if any(fragment in shop or fragment in selftest for fragment in copied_diplomacy):
        errors.append("shop event or selftest copied the production diplomacy purchase body")
    if shop.count("ceiling = yes") != 0:
        errors.append("shop event contains copied price inflation instead of production effect calls")
    if shop.count("name = xa_test_ui_dip_applied value = 1") != 1:
        errors.append("production diplomacy option lost its outer selftest marker")

    blessing_init = extract_block(
        production_effects, "xar_initialize_blessing_session_effect") or ""
    finish_shop = extract_block(production_effects, "xar_finish_shop_effect") or ""
    if "name = xa_bless_session value = 0" not in blessing_init:
        errors.append("shared blessing-session initialization is missing")
    finish_requirements = (
        "global_var:xa_local_points > 0",
        "add_gold = { value = global_var:xa_local_points }",
        "name = xa_local_points value = 0",
        "xar_initialize_blessing_session_effect = yes",
    )
    if any(fragment not in finish_shop for fragment in finish_requirements):
        errors.append("production shop finish effect lost conversion, clearing, or blessing initialization")
    if "selftest" in finish_shop or "_test_" in finish_shop:
        errors.append("production shop finish effect depends on a selftest marker")
    if shop.count("xar_finish_shop_effect = yes") != 1:
        errors.append("shop finish option does not call the production finish effect exactly once")
    if "xar_initialize_blessing_session_effect = yes" not in first_life:
        errors.append("first-life event does not use shared blessing-session initialization")
    finish_order = [
        shop.find("xar_finish_shop_effect = yes"),
        shop.find("global_var:xa_local_points = 0"),
        shop.find("name = xa_bless_session value = 3"),
        shop.find("trigger_event = { id = xar.0004 }"),
    ]
    if any(index < 0 for index in finish_order) or finish_order != sorted(finish_order):
        errors.append("selftest shop finish assertions/session override no longer wrap the production effect")

    if "global_var:xa_local_points = 0" not in pact or "trigger_event = xar.0010" not in pact:
        errors.append("zero-budget production pact does not route to the first-life event")
    if pact.find("name = xa_local_points value = 200") > pact.find(
            "global_var:xa_local_points = 0"):
        errors.append("selftest UI override no longer precedes the first-life branch")
    if "name = xa_local_points value = 200" not in pact or "id = xar.0001" not in pact:
        errors.append("selftest production UI path no longer injects 200 and opens the shop")
    if "id = xar.0004" not in first_life:
        errors.append("first-life event does not enter the blessing flow")

    challenge_init = extract_block(production_effects, "xar_initialize_challenge_mode_effect") or ""
    for setting in ("xar_inherit_0", "xar_inherit_25", "xar_inherit_50", "xar_score_growth"):
        if f"has_game_rule = {setting}" not in challenge_init:
            errors.append(f"challenge initialization lacks {setting}")
    consumer = extract_block(production_effects, "xar_consume_import_effect") or ""
    budget_effect = extract_block(production_effects, "xar_calculate_inherited_budget_effect") or ""
    if "xar_calculate_inherited_budget_effect = yes" not in consumer:
        errors.append("import consumer does not call the shared inheritance calculator")
    for ratio in ("0.25", "0.5"):
        if f"multiply = {ratio} floor = yes" not in budget_effect:
            errors.append(f"inheritance budget lacks floor multiplier {ratio}")
    if "xa_local_points > global_var:xa_budget_cap" not in budget_effect:
        errors.append("inheritance budget lacks cap")
    baseline = extract_block(production_effects, "xar_capture_score_baseline_effect") or ""
    if "value = xar_current_score_base_value" not in baseline:
        errors.append("growth baseline does not use the read-only absolute score")
    if events.count("xar_capture_score_baseline_effect = yes") != 4:
        errors.append("growth baseline must be captured from decline, curses, and seal")

    decisions = "\n".join(read(path) for path in (MOD / "common/decisions").glob("*.txt"))
    decision_ids = top_level_keys(decisions, r"xar_\w+")
    if "xar_ledger_decision" not in decision_ids:
        errors.append("Glassfire Ledger decision missing")
    for decision_id in decision_ids:
        block = extract_block(decisions, decision_id) or ""
        shown = extract_block(block, "is_shown") or ""
        valid = extract_block(block, "is_valid_showing_failures_only") or ""
        ai_potential = extract_block(block, "ai_potential") or ""
        if not all("has_character_flag = xa_enabled" in guard and "is_ai = no" in guard
                   for guard in (shown, valid)):
            errors.append(f"decision '{decision_id}' lacks xa_enabled/is_ai player guards")
        if "always = no" not in ai_potential:
            errors.append(f"decision '{decision_id}' lacks disabled AI potential")
    if "trigger_event = xar.0011" not in decisions:
        errors.append("Glassfire Ledger decision does not open its event")
    if "trigger_event = xar.2000" not in decisions:
        errors.append("lifetime-contract decision does not open selection event")

    contract_events = [event_id for event_id in event_ids if event_id.startswith("xar.21")]
    gaze_events = [event_id for event_id in event_ids if event_id.startswith("xar.22")]
    if len(contract_events) != 18 or len(gaze_events) != 10:
        errors.append(f"contract narrative matrix must be 18+10 events, got {len(contract_events)}+{len(gaze_events)}")
    contract_effects = read(MOD / "common/scripted_effects/xar_generated_contract_effects.txt")
    if contract_effects.count("xar_select_contract_") != 6:
        errors.append("contract generator must emit six archetype selectors")
    if contract_effects.count("has_trait_xp = { trait = xar_glassfire_gaze value >=") != 10:
        errors.append("Glassfire Gaze must emit ten milestone unlock checks")
    contract_lessons = read(MOD / "common/tutorial_lessons/xar_generated_contract_lessons.txt")
    if contract_lessons.count("chain = reactive_advice") != 24:
        errors.append("contract persistence must contain 18 PB plus 6 collection lessons")

    on_actions = read(MOD / "common/on_action/xar_on_actions.txt")
    start = extract_block(on_actions, "xar_on_game_start") or ""
    death = extract_block(on_actions, "xar_on_death") or ""
    if "every_player" not in start:
        errors.append("game-start entry is no longer player-only")
    if "has_character_flag = xa_enabled" not in death or "is_ai = no" not in death:
        errors.append("death entry lost the player flag/is_ai dual gate")
    if death.count("trigger_event = xar.1001") != 1:
        errors.append("death fallback must contain exactly one synchronous xar.1001 trigger")
    if death.count("id = xar.1001") != 1 or death.count("days = 1") != 1:
        errors.append("heir settlement path must contain exactly one delayed one-day xar.1001 trigger")
    if ("limit = { exists = player_heir }" not in death
            or "XAR: no player heir; synchronous settlement fallback" not in death):
        errors.append("death settlement lacks the guarded no-heir fallback/debug marker")
    for hook in ("on_war_won_attacker", "on_war_won_defender", "on_hook_used",
                 "on_county_faith_change", "on_birth_mother", "on_birth_father",
                 "on_building_completed", "on_birthday"):
        if hook not in on_actions:
            errors.append(f"contract behavior hook missing: {hook}")

    trait = read(MOD / "common/traits/xar_traits.txt")
    thresholds = [int(value) for value in re.findall(
        r"(?m)^\s*(\d+)\s*=\s*{\s*stress_gain_mult\s*=\s*0\.1\s*}", trait)]
    if thresholds != list(range(10, 101, 10)):
        errors.append(f"Glassfire trait track must be 10..100 by 10, got {thresholds}")

    pools = read(MOD / "common/scripted_effects/xar_generated_pools_effects.txt")
    curse_draw = extract_block(pools, "xar_draw_curses_effect") or ""
    bless_draw = extract_block(pools, "xar_draw_blessings_effect") or ""
    for prefix, draw, slots in (("bless", bless_draw, ("a", "b", "c")),
                                ("curse", curse_draw, ("a", "b"))):
        for slot in slots:
            initializer = f"name = xa_{prefix}_{slot} value = -1"
            if draw.count(initializer) != 1:
                errors.append(f"{prefix} draw lacks first-run initializer for slot {slot}")

    generated_loc = read(MOD / "common/customizable_localization/xar_generated_loc.txt")
    import_check = extract_block(generated_loc, "xar_import_request_check") or ""
    if "has_global_variable = xa_import_requested" not in import_check:
        errors.append("import request localization reads xa_import_requested without an existence guard")
    if "xa_curse_c" in curse_draw:
        errors.append("generated curse draw still contains slot C")
    if curse_draw.count("random_list = {") != 2:
        errors.append("generated curse draw must contain exactly two random lists")
    if curse_draw.count("xa_selected_bless_rarity < 2") != 70 * 2:
        errors.append("common curse rarity guards are incomplete")
    if pools.count("xar_complete_bargain_pair_effect = yes") != 100:
        errors.append("each curse dispatcher branch must call the shared pair-completion effect")
    if "NOT = { OR = { has_trait = physique_good_1 has_trait = physique_good_2 has_trait = physique_good_3 } }" not in bless_draw:
        errors.append("ranked blessing traits do not exclude equal or stronger tiers")
    for modifier in ("xar_pb_life_2", "xar_leg_life"):
        if f"NOT = {{ has_character_modifier = {modifier} }}" not in bless_draw:
            errors.append(f"permanent blessing modifier is repeatable: {modifier}")
    if "NOT = { has_character_modifier = xar_pc_life }" not in curse_draw:
        errors.append("permanent curse modifier xar_pc_life is repeatable")
    if "modifier = { factor = 1.5 gold > 500 }" not in curse_draw:
        errors.append("gold-drain curses lost wealth-state weighting")
    for contract_id in range(1, 7):
        if f"global_var:xa_contract_id = {contract_id}" not in pools:
            errors.append(f"pool weighting lacks contract synergy for archetype {contract_id}")

    preview = read(MOD / "common/script_values/xar_generated_score_preview.txt")
    if re.search(r"\b(?:set|change|add|remove)_(?:global_)?variable\b", preview):
        errors.append("score preview contains a state-mutating variable effect")
    if "xar_current_score_value" not in preview:
        errors.append("score preview script value missing")
    hand_score_effects = read(MOD / "common/scripted_effects/xar_effects.txt")
    generated_score_effects = read(
        MOD / "common/scripted_effects/xar_generated_scoring_effects.txt")
    score_effects = generated_score_effects + "\n" + hand_score_effects
    if score_effects.count("xar_descendant_tier_count_effect = yes") != 1:
        errors.append("descendant title score is not using the single deduplicated traversal")
    compute_definitions = []
    for path in (MOD / "common/scripted_effects").rglob("*.txt"):
        matches = re.findall(r"(?m)^xar_compute_score_effect\s*=\s*{", read(path))
        compute_definitions.extend(path.relative_to(ROOT) for _ in matches)
    expected_compute_path = Path(
        "XenoAmess_s_Eternal_Recurrence/common/scripted_effects/"
        "xar_generated_scoring_effects.txt")
    if compute_definitions != [expected_compute_path]:
        errors.append(
            "xar_compute_score_effect must have exactly one generated definition, got "
            f"{compute_definitions}")
    adapter = extract_block(hand_score_effects, "xar_descendant_tier_count_effect") or ""
    adapter_tiers = re.findall(
        r"highest_held_title_tier >= (tier_\w+).*?name = xa_d_(t\d+)",
        adapter,
        re.DOTALL,
    )
    expected_adapter_tiers = [
        (rule.tier, rule.key) for rule in reversed(scoring_data.DESCENDANT_TITLE_TIERS)
    ]
    if adapter_tiers != expected_adapter_tiers:
        errors.append("hand-written descendant title adapter is stale against scoring_data")
    descendant_nodes = top_level_keys(generated_score_effects, r"xar_desc_node_l\d+")
    expected_nodes = [
        f"xar_desc_node_l{depth}"
        for depth in range(1, scoring_data.DESCENDANT_DEPTH + 1)
    ]
    if descendant_nodes != expected_nodes:
        errors.append("generated descendant traversal depth is stale against scoring_data")
    selftest = read(MOD / "common/scripted_effects/xar_selftest_effects.txt")
    ledger_test_markers = {
        "XAR: TEST PASS ledger_score_nonnegative",
        "XAR: TEST PASS ledger_projection",
        "XAR: TEST PASS ledger_record_unchanged",
    }
    if "xar_prepare_ledger_effect = yes" not in selftest or any(
            marker not in selftest for marker in ledger_test_markers):
        errors.append("selftest lacks production ledger assertions/markers")
    for variable in ("xa_ledger_score", "xa_ledger_candidate", "xa_ledger_next",
                     "xa_ledger_gap", "xa_ledger_at_cap", "xa_test_ledger_history"):
        if f"remove_global_variable = {variable}" not in selftest:
            errors.append(f"selftest does not clean temporary ledger variable '{variable}'")
    if "trigger_event = xar.0011" in selftest:
        errors.append("selftest must not open the ledger UI")

    highscore = load_highscore_generator()
    generated_effects = highscore.gen_effects()
    quantizer = extract_block(generated_effects, "xar_quantize_record_candidate_effect") or ""
    writer = extract_block(generated_effects, "xar_write_record_effect") or ""
    ledger = extract_block(generated_effects, "xar_prepare_ledger_effect") or ""
    thresholds = highscore.THRESHOLDS
    quantized_limits = [int(value) for value in re.findall(
        r"global_var:xa_run_score >= (\d+)", quantizer)]
    if quantized_limits != list(reversed(thresholds)):
        errors.append("record candidate quantizer does not cover every threshold")
    candidate_assignments = [int(value) for value in re.findall(
        r"name = xa_record_candidate value = (\d+)", quantizer)]
    if candidate_assignments != [0] + list(reversed(thresholds)):
        errors.append("record candidate quantizer assignments are incomplete")
    if f"global_var:xa_run_score >= {thresholds[-1]}" not in quantizer:
        errors.append("record candidate quantizer lacks cap branch")
    if "global_var:xa_record_candidate > global_var:xa_old_record" not in writer:
        errors.append("record writer lacks strict candidate > historical comparison")
    if "global_var:xa_run_score" in writer:
        errors.append("record writer still dispatches from the real run score")
    writer_candidates = [int(value) for value in re.findall(
        r"global_var:xa_record_candidate = (\d+)", writer)]
    if writer_candidates != list(reversed(thresholds)):
        errors.append("record writer candidate dispatcher does not cover every threshold")
    if "xar_quantize_record_candidate_effect = yes" not in score_effects:
        errors.append("production scoring does not quantize xa_record_candidate")
    if "value = global_var:xa_record_candidate" not in score_effects:
        errors.append("record delta is not based on xa_record_candidate")

    ledger_limits = [int(value) for value in re.findall(
        r"global_var:xa_ledger_score >= (\d+)", ledger)]
    if ledger_limits != list(reversed(thresholds)):
        errors.append("ledger tier projection does not cover every generated threshold")
    ledger_candidates = [int(value) for value in re.findall(
        r"name = xa_ledger_candidate value = (\d+)", ledger)]
    if ledger_candidates != [0] + list(reversed(thresholds)):
        errors.append("ledger candidate projection is not in generated parity")
    expected_next = [thresholds[0]] + [
        thresholds[min(index + 1, len(thresholds) - 1)]
        for index in range(len(thresholds) - 1, -1, -1)
    ]
    ledger_next = [int(value) for value in re.findall(
        r"name = xa_ledger_next value = (\d+)", ledger)]
    if ledger_next != expected_next:
        errors.append("ledger next-tier projection is not generated from adjacent thresholds")
    if "name = xa_ledger_at_cap value = 1" not in ledger or "name = xa_ledger_gap value = 0" not in ledger:
        errors.append("ledger projection lacks explicit cap state")
    forbidden_ledger_writes = ("xar_hs_ge_", "xa_global_record_imported", "xa_run_score",
                               "xa_record_candidate", "xa_old_record", "xa_local_points")
    if any(value in ledger for value in forbidden_ledger_writes):
        errors.append("ledger projection mutates or references protected record/resource state")
    ledger_write_targets = re.findall(
        r"(?:set|change|remove)_global_variable\s*=\s*(?:\{\s*name\s*=\s*)?(\w+)",
        ledger + ledger_event)
    if not ledger_write_targets or any(not target.startswith("xa_ledger_")
                                       for target in ledger_write_targets):
        errors.append("ledger view writes something other than dedicated xa_ledger_* display variables")
    if re.search(r"\b(?:add|change)_(?:gold|prestige|piety|influence|dynasty_prestige|\w+_skill)\b",
                 ledger + ledger_event):
        errors.append("ledger view changes player resources or skills")
    for field in ("xar_ledger_score", "xar_ledger_history", "xar_ledger_candidate",
                  "xar_ledger_next", "xar_ledger_gap", "xar_ledger_pairs",
                  "xar_ledger_refusals"):
        if field not in ledger_event:
            errors.append(f"ledger event missing display field '{field}'")

    import_gui = highscore.gen_guis()
    import_meta = highscore.gen_gui()
    consume = extract_block(score_effects, "xar_consume_import_effect") or ""
    for flag in ("xa_import_requested", "xa_import_ready", "xa_import_consumed"):
        if flag not in on_actions + import_gui + consume:
            errors.append(f"import protocol flag '{flag}' is not wired end-to-end")
    if "xar_import_request_check" not in import_meta or "[And(" not in import_meta:
        errors.append("GUI import states are not gated by the explicit request signal")
    if "global_var:xa_import_requested = 1" not in import_gui:
        errors.append("generated importer lacks its idempotent request guard")
    if "global_var:xa_import_ready = 1" not in consume or "global_var:xa_import_consumed = 0" not in consume:
        errors.append("import consumer lacks ready/unconsumed guard")
    if "xar_calculate_inherited_budget_effect = yes" not in consume:
        errors.append("import consumer does not calculate inherited shop points")
    if consume.find("name = xa_local_points") > consume.find("trigger_event = xar.0002"):
        errors.append("pact can open before imported shop points are assigned")

    if "global_var:xa_record_candidate > global_var:xa_old_record" not in death:
        errors.append("death hook does not use strict candidate record comparison")
    if "global_var:xa_run_score > global_var:xa_old_record" in on_actions + events:
        errors.append("production record comparison still uses the real run score")


def package_checks(errors):
    errors.extend(build_release.release_source_errors(MOD))
    descriptor = read(MOD / "descriptor.mod")
    if "remote_file_id" in descriptor:
        errors.append("repository descriptor.mod contains remote_file_id")
    if not re.search(r'(?m)^version="\d+\.\d+\.\d+"$', descriptor):
        errors.append("descriptor.mod lacks a semantic version")
    if 'picture="thumbnail.png"' not in descriptor:
        errors.append("descriptor.mod picture is not thumbnail.png")
    if 'supported_version="1.19.0.6"' not in descriptor:
        errors.append("descriptor.mod tested CK3 version changed without release QA update")
    thumbnail = MOD / "thumbnail.png"
    if thumbnail.exists() and thumbnail.stat().st_size >= 1_000_000:
        errors.append("thumbnail.png must remain below Steam's 1 MB limit")
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
    reference_model_checks(errors)
    mechanic_checks(errors)
    package_checks(errors)
    if errors:
        print("STATIC VALIDATION FAILED")
        for error in errors:
            print(f"  {error}")
        return 1
    print("STATIC VALIDATION OK: generated parity, BOM/loc, mechanics/AI, release allowlist/assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
