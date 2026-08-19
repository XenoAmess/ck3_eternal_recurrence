#!/usr/bin/env python3
"""Repository-wide static release checks run before CK3 acceptance."""

import importlib.util
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image

import build_release
import gen_balance_wire
import gen_contracts
import gen_no_heir_gui
import gen_pools
import gen_scoring
import gen_score_preview
import scoring_data
import validate_loc


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
LANGS = validate_loc.LANGS
POOL_SEMANTIC_CONTRACT = ROOT / "tools/pool_semantic_contract.sha256"


def read(path):
    return path.read_text(encoding="utf-8-sig", errors="replace")


def normalized(text):
    return text.replace("\r\n", "\n")


def compact_script(text):
    return re.sub(r"\s+", " ", text).strip()


def pool_semantic_digest(prefix, wire_id, entry):
    code = gen_pools.entry_code(None, entry)
    modifier_definitions = {}
    if entry[1] == "mod":
        modifier_definitions[entry[2][0]] = compact_script(entry[2][1])
    for modifier in re.findall(
            r"add_character_modifier\s*=\s*\{\s*modifier\s*=\s*(\w+)", code):
        if modifier in gen_pools.EXTRA_MODIFIERS:
            modifier_definitions[modifier] = compact_script(
                gen_pools.EXTRA_MODIFIERS[modifier])
    payload = {
        "stable_id": f"{prefix}.{wire_id:03d}",
        "wire_id": wire_id,
        "rarity": entry[0],
        "family": entry[1],
        "effect": compact_script(code),
        "conditions": gen_pools.entry_conditions(entry),
        "base_weight": gen_pools.WEIGHTS[entry[0]],
        "weight_modifiers": gen_pools.entry_weight_modifiers(entry, prefix),
        "modifier_definitions": modifier_definitions,
        "name_simp_chinese": entry[3]["simp_chinese"],
        "name_english": entry[3]["english"],
        "summary_simp_chinese": gen_pools.entry_summary(None, entry, "simp_chinese"),
        "summary_english": gen_pools.entry_summary(None, entry, "english"),
    }
    serialized = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def render_pool_semantic_contract():
    lines = [
        "# Frozen reviewed semantics for 100 blessing + 100 curse stable IDs.",
        ("# Update only after reviewing docs/blessing-curse-pools.md and "
         "generated dispatcher diffs."),
    ]
    for prefix, pool in (("bless", gen_pools.B), ("curse", gen_pools.C)):
        for wire_id, entry in enumerate(pool):
            lines.append(
                f"{prefix}.{wire_id:03d} "
                f"{pool_semantic_digest(prefix, wire_id, entry)}")
    return "\n".join(lines) + "\n"


def expected_pool_draw_branch(prefix, slot, prior, wire_id, entry):
    conditions = [
        f"NOT = {{ global_var:xa_{prefix}_{prior_slot} = {wire_id} }}"
        for prior_slot in prior
    ]
    conditions.extend(gen_pools.entry_conditions(entry))
    if prefix == "curse" and entry[0] == "c":
        conditions.append("global_var:xa_selected_bless_rarity < 2")
    trigger = f"trigger = {{ {' '.join(conditions)} }} " if conditions else ""
    modifiers = "".join(
        f"modifier = {{ factor = {factor} {condition} }} "
        for condition, factor in gen_pools.entry_weight_modifiers(entry, prefix)
    )
    rarity = ""
    if prefix == "curse":
        rarity = (
            f" set_global_variable = {{ name = xa_{prefix}_{slot}_rarity "
            f"value = {gen_pools.RARITY_LEVEL[entry[0]]} }}")
    return (
        f"{gen_pools.WEIGHTS[entry[0]]} = {{ {trigger}{modifiers}"
        f"set_global_variable = {{ name = xa_{prefix}_{slot} value = {wire_id} }}"
        f"{rarity} }}")


def expected_pool_apply_branch(prefix, wire_id, entry):
    code = gen_pools.entry_code(None, entry)
    if prefix == "bless":
        code += (
            "\nset_global_variable = { name = xa_selected_bless_rarity "
            f"value = {gen_pools.RARITY_LEVEL[entry[0]]} }}")
    else:
        code += "\nxar_complete_bargain_pair_effect = yes"
    code += (
        "\n# XAR_ACCEPTANCE_ONLY_BEGIN\n"
        "if = {\n"
        "limit = { has_global_variable = xa_scoring_matrix_active }\n"
        f'debug_log = "XAR: TEST PASS pool_dispatch_{prefix}_{wire_id:03d}"\n'
        "}\n"
        "# XAR_ACCEPTANCE_ONLY_END"
    )
    return (
        f"if = {{ limit = {{ global_var:xa_{prefix}_$SLOT$ = {wire_id} }} "
        f"{code} }}")


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


def extract_named_option(text, name):
    """Return the balanced option block containing one exact option name."""
    for match in re.finditer(r"(?m)^\s*option\s*=\s*\{", text):
        start = text.index("{", match.start())
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    block = text[match.start():index + 1]
                    if re.search(
                            rf"(?m)^\s*name\s*=\s*{re.escape(name)}\s*$", block):
                        return block
                    break
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
        MOD / "common/script_values/xar_acceptance_balance_wire_values.txt":
            gen_balance_wire.generated_values(),
        MOD / "common/scripted_effects/xar_acceptance_balance_wire_effects.txt":
            gen_balance_wire.generated_effect(),
        ROOT / "docs/scoring-rules.md": gen_scoring.generate_doc(),
        MOD / "events/xar_generated_contract_events.txt": gen_contracts.generated_events(),
        MOD / "common/decisions/xar_generated_contract_decisions.txt": gen_contracts.generated_decision(),
        MOD / "common/scripted_effects/xar_generated_contract_effects.txt": gen_contracts.generated_effects(),
        MOD / "common/traits/xar_traits.txt": gen_contracts.generated_trait(),
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
        "xar.no_heir_settlement.desc",
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
    production_event_text = build_release.render_release_bytes(
        MOD / "events/xar_events.txt", "events/xar_events.txt"
    ).decode("utf-8-sig")
    production_bless_event = extract_block(production_event_text, "xar.0004") or ""
    production_curse_event = extract_block(production_event_text, "xar.0005") or ""
    production_reopen_event = extract_block(production_event_text, "xar.0006") or ""

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
        "xa_price_grand_tribute": "10000",
        "xa_price_borrowed_generation": "50000",
        "xa_price_sixfold_apotheosis": "100000",
        "xa_price_reroll": "200", "xa_price_seal": "300",
        "xa_price_dread": "250", "xa_price_legitimacy": "500",
        "xa_price_tyranny": "1000",
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
        "xar_buy_reroll_shop_item_effect": ("xa_price_reroll", "name = xa_reroll_tokens add = 1"),
        "xar_buy_seal_shop_item_effect": ("xa_price_seal", "name = xa_seal_tokens add = 1"),
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

    fixed_purchases = {
        "xar_buy_faith_reformation_shop_item_effect": (
            "xa_price_reform", "set_global_variable = xa_bought_reformation",
            ("modifier = xar_free_faith_reformation",)),
        "xar_buy_grand_tribute_shop_item_effect": (
            "xa_price_grand_tribute", "add_character_flag = xa_bought_grand_tribute",
            ("add_prestige = 1500", "add_piety = 1500",
             "change_influence = 1500", "add_dynasty_prestige = 1500")),
        "xar_buy_borrowed_generation_shop_item_effect": (
            "xa_price_borrowed_generation",
            "add_character_flag = xa_bought_borrowed_generation",
            ("xar_buy_lifespan_effect = yes",)),
        "xar_buy_sixfold_apotheosis_shop_item_effect": (
            "xa_price_sixfold_apotheosis",
            "add_character_flag = xa_bought_sixfold_apotheosis",
            ("add_diplomacy_skill = 30", "add_martial_skill = 30",
             "add_stewardship_skill = 30", "add_intrigue_skill = 30",
              "add_learning_skill = 30", "add_prowess_skill = 30")),
        "xar_buy_dread_shop_item_effect": (
            "xa_price_dread", "add_character_flag = xa_bought_dread",
            ("add_dread = 20",)),
        "xar_buy_legitimacy_shop_item_effect": (
            "xa_price_legitimacy", "add_character_flag = xa_bought_legitimacy",
            ("add_legitimacy = 100",)),
        "xar_buy_tyranny_shop_item_effect": (
            "xa_price_tyranny", "add_character_flag = xa_bought_tyranny",
            ("add_tyranny = -10",)),
    }
    for effect, (price, ownership, rewards) in fixed_purchases.items():
        call = f"{effect} = yes"
        block = extract_block(production_effects, effect) or ""
        charge = f"name = xa_local_points add = {{ value = global_var:{price} multiply = -1 }}"
        if shop.count(call) != 1 or selftest.count(call) != 1:
            errors.append(f"shop and selftest must each call fixed purchase '{effect}' once")
        if charge not in block or ownership not in block or any(
                reward not in block for reward in rewards):
            errors.append(f"fixed purchase '{effect}' lost charge, ownership, or reward")
        if "multiply = 1.2" in block or "selftest" in block or "_test_" in block:
            errors.append(f"fixed purchase '{effect}' contains inflation or test-only behavior")
    borrowed = extract_block(
        production_effects, "xar_buy_borrowed_generation_shop_item_effect") or ""
    if borrowed.count("xar_buy_lifespan_effect = yes") != 25:
        errors.append("Borrowed Generation must fill exactly 25 lifespan stacks")
    if "global_var:xa_lifespan_bought < 25" not in shop:
        errors.append("Borrowed Generation shop option lacks its 25-stack guard")
    if "XAR: TEST PASS shop_high_tier_bundle" not in selftest:
        errors.append("selftest lacks the full high-tier shop bundle assertion")
    if "XAR: TEST PASS shop_expanded_inventory" not in selftest:
        errors.append("selftest lacks expanded shop inventory assertions")
    if "global_var:xa_shop_page < 4" not in shop:
        errors.append("shop navigation does not expose page 4")

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

    # Production meetings contain one blessing/curse pair. Every terminal route
    # independently schedules the same real three-year reset; no route loops in-session.
    scheduling_routes = (
        (production_bless_event, "xar.0004.decline"),
        (production_curse_event, "xar_curse_option_a"),
        (production_curse_event, "xar_curse_option_b"),
        (production_curse_event, "xar.0005.seal"),
    )
    schedule = "trigger_event = { id = xar.0006 days = 1095 }"
    for event, option_name in scheduling_routes:
        option = extract_named_option(event, option_name) or ""
        if option.count(schedule) != 1:
            errors.append(
                f"production route '{option_name}' must schedule xar.0006 at 1095 days once")
        if "trigger_event = xar.0004" in option or "id = xar.0004" in option:
            errors.append(f"production route '{option_name}' reopens inside the same meeting")
    if production_event_text.count(schedule) != 4:
        errors.append("production bargain flow must contain exactly four 1095-day scheduling routes")
    for option_name in ("xar_bless_option_a", "xar_bless_option_b", "xar_bless_option_c"):
        option = extract_named_option(production_bless_event, option_name) or ""
        if (option.count("xar_apply_blessing_effect") != 1
                or option.count("trigger_event = { id = xar.0005 }") != 1
                or "xar.0006" in option):
            errors.append(
                f"production blessing route '{option_name}' must dispatch once into one curse")
    if (production_reopen_event.count("name = xa_bless_session value = 0") != 1
            or production_reopen_event.count("trigger_event = { id = xar.0004 }") != 1):
        errors.append("production xar.0006 must reset session to 0 and reopen xar.0004 once")
    if "name = xa_bless_session value = 3" in production_event_text:
        errors.append("production bargain flow still contains the old three-pair session override")

    challenge_init = extract_block(production_effects, "xar_initialize_challenge_mode_effect") or ""
    game_rules = read(MOD / "common/game_rules/xar_game_rules.txt")
    inheritance_rule = extract_block(game_rules, "xar_inheritance") or ""
    score_rule = extract_block(game_rules, "xar_score_basis") or ""
    if "default = xar_inherit_100" not in inheritance_rule:
        errors.append("recommended inheritance default must be 100%")
    if "default = xar_score_growth" not in score_rule:
        errors.append("recommended score default must be lifetime growth")
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
    if "xa_budget_cap" in production_effects + events:
        errors.append("inheritance budget still contains a spending cap")
    if "global_var:xa_global_record_imported" not in budget_effect:
        errors.append("100% inheritance no longer copies the full imported record")
    baseline = extract_block(production_effects, "xar_capture_score_baseline_effect") or ""
    if "value = xar_current_score_base_value" not in baseline:
        errors.append("growth baseline does not use the read-only absolute score")
    opening_baseline_calls = sum(
        event_blocks.get(event_id, "").count("xar_capture_score_baseline_effect = yes")
        for event_id in ("xar.0004", "xar.0005")
    )
    if opening_baseline_calls != 4:
        errors.append("growth baseline must be captured from decline, curses, and seal")
    death_waiter = event_blocks.get("xar.0008", "")
    destructive_sweep_order = [
        death_waiter.find("xar_test_sweep_effect = yes"),
        death_waiter.find("name = xa_score_basis value = 0"),
        death_waiter.find("value = xar_current_score_value"),
    ]
    if (any(index < 0 for index in destructive_sweep_order)
            or destructive_sweep_order != sorted(destructive_sweep_order)):
        errors.append("selftest must isolate its destructive pool sweep from growth-track assertions")
    for marker in ("XAR: TEST PASS default_growth_track",
                   "XAR: TEST PASS growth_contract_points",
                   "XAR: TEST PASS growth_baseline_zero",
                   "XAR: TEST PASS growth_score_delta"):
        if marker not in selftest:
            errors.append(f"selftest lacks recommended-track assertion '{marker}'")

    decisions = "\n".join(read(path) for path in (MOD / "common/decisions").glob("*.txt"))
    decision_ids = top_level_keys(decisions, r"xar_\w+")
    if "xar_ledger_decision" not in decision_ids:
        errors.append("Glassfire Ledger decision missing")
    for decision_id in decision_ids:
        block = extract_block(decisions, decision_id) or ""
        shown = extract_block(block, "is_shown") or ""
        valid = extract_block(block, "is_valid_showing_failures_only") or ""
        ai_potential = extract_block(block, "ai_potential") or ""
        effect = extract_block(block, "effect") or ""
        hidden_effect = extract_block(effect, "hidden_effect") or ""
        if not all("has_character_flag = xa_enabled" in guard and "is_ai = no" in guard
                   for guard in (shown, valid)):
            errors.append(f"decision '{decision_id}' lacks xa_enabled/is_ai player guards")
        if "always = no" not in ai_potential:
            errors.append(f"decision '{decision_id}' lacks disabled AI potential")
        if "trigger_event = xar." in effect and "trigger_event = xar." not in hidden_effect:
            errors.append(
                f"decision '{decision_id}' exposes event immediate effects to tooltip preview")
    decision_bridges = read(
        MOD / "common/scripted_guis/xar_decision_bridges.txt")
    decision_bridge_gui = read(MOD / "gui/xar_decision_bridge.gui")
    decision_registry = read(MOD / "gui/scripted_widgets/xar_scripted_widgets.txt")
    no_heir_gui = read(MOD / "gui/xar_no_heir_settlement.gui")
    succession_override = read(MOD / "gui/window_succession_event.gui")
    if "set_global_variable = xa_open_ledger_pending" not in decisions:
        errors.append("Glassfire Ledger decision does not request its GUI bridge")
    if "set_global_variable = xa_open_contract_pending" not in decisions:
        errors.append("lifetime-contract decision does not request its GUI bridge")
    if "trigger_event = xar.0012" not in decision_bridges:
        errors.append("Glassfire Ledger GUI bridge does not open its preparation event")
    if "trigger_event = xar.2000" not in decision_bridges:
        errors.append("lifetime-contract GUI bridge does not open selection event")
    if ("xar_open_ledger_gui" not in decision_bridge_gui
            or "xar_open_contract_gui" not in decision_bridge_gui
            or "gui/xar_decision_bridge.gui = xar_decision_bridge_window"
            not in decision_registry):
        errors.append("decision GUI bridge window is not fully registered")
    no_heir_gui_requirements = (
        "type xar_no_heir_settlement_widget = widget",
        "SuccessionEventWindow.GetDeadCharacter.IsValid",
        "Not( SuccessionEventWindow.GetDeadCharacter.IsAlive )",
        "Not( SuccessionEventWindow.GetPlayerHeir.IsValid )",
        "GetTrait( 'xar_glassfire_gaze' )",
        "GetPlayer.MakeScope.Var('xar_no_heir_score').GetValue",
        "Localize('xar.no_heir.footer')", "SuccessionEventWindow.GoToMenu",
    )
    if any(token not in no_heir_gui for token in no_heir_gui_requirements):
        errors.append("no-heir settlement widget lost its XAR gate, content, or exit")
    expected_override = (
        "# GENERATED FILE - native 1.19 succession window plus XAR no-heir widget\n"
        + gen_no_heir_gui.render())
    if normalized(succession_override) != normalized(expected_override):
        errors.append("native succession override is stale; run gen_no_heir_gui.py")
    if succession_override.count("xar_no_heir_settlement_widget = {}") != 1:
        errors.append("native succession override must inject exactly one no-heir widget")

    contract_events = [event_id for event_id in event_ids if event_id.startswith("xar.21")]
    gaze_events = [event_id for event_id in event_ids if event_id.startswith("xar.22")]
    if len(contract_events) != 18 or len(gaze_events) != 10:
        errors.append(f"contract narrative matrix must be 18+10 events, got {len(contract_events)}+{len(gaze_events)}")
    contract_effects = read(MOD / "common/scripted_effects/xar_generated_contract_effects.txt")
    if contract_effects.count("xar_select_contract_") != 6:
        errors.append("contract generator must emit six archetype selectors")
    if contract_effects.count("has_trait_xp = { trait = xar_glassfire_gaze value >=") != 10:
        errors.append("Glassfire Gaze must emit ten milestone unlock checks")
    pair_effect = extract_block(contract_effects, "xar_complete_bargain_pair_effect") or ""
    if not all(token in pair_effect for token in (
            "is_ai = no", "has_character_flag = xa_enabled",
            "has_trait = xar_glassfire_gaze")):
        errors.append("Glassfire pair completion lost its player/trait guard")
    for milestone in gen_contracts.GAZE_MILESTONES:
        for token, amount in (("reroll", milestone["rerolls"]),
                              ("seal", milestone["seals"])):
            expected = f"name = xa_{token}_tokens add = {amount}"
            if amount and expected not in pair_effect:
                errors.append(
                    f"Glassfire {milestone['xp']} XP reward lacks {amount} {token} token(s)")
    contract_lessons = read(MOD / "common/tutorial_lessons/xar_generated_contract_lessons.txt")
    if contract_lessons.count("chain = reactive_advice") != 24:
        errors.append("contract persistence must contain 18 PB plus 6 collection lessons")

    on_actions = read(MOD / "common/on_action/eternal_recurrence_on_actions.txt")
    score_snapshot_event = extract_block(events, "xar.1002") or ""
    score_compute_event = extract_block(events, "xar.1000") or ""
    score_dispatch_event = extract_block(events, "xar.1003") or ""
    start = extract_block(on_actions, "xar_on_game_start") or ""
    death = extract_block(on_actions, "xar_on_death") or ""
    if "every_player" not in start:
        errors.append("game-start entry is no longer player-only")
    if "has_character_flag = xa_enabled" not in death or "is_ai = no" not in death:
        errors.append("death entry lost the player flag/is_ai dual gate")
    if (death.count("trigger_event = xar.1000") != 1
            or "xar_compute_score_effect = yes" not in score_compute_event
            or "trigger_event = xar.1003" not in score_compute_event):
        errors.append("death scoring must cross the synchronous xar.1000 commit boundary")
    if (score_dispatch_event.count("id = xar.1001") != 1
            or score_dispatch_event.count("days = 1") != 1):
        errors.append("heir settlement path must contain exactly one delayed one-day xar.1001 trigger")
    if ("limit = { exists = player_heir }" not in score_dispatch_event
            or "XAR: no player heir; synchronous settlement fallback" not in score_dispatch_event
            or "trigger_event = xar.1002" not in score_dispatch_event):
        errors.append("death settlement lacks the guarded no-heir fallback/debug marker")
    for variable in ("score", "subtotal", "candidate", "old", "delta", "pairs",
                     "refusals", "contract"):
        if f"name = xar_no_heir_{variable}" not in score_snapshot_event:
            errors.append(f"no-heir settlement lacks '{variable}' event-root snapshot")
    death_probe_effect = read(
        MOD / "common/scripted_effects/xar_acceptance_death_effects.txt")
    death_probe_events = read(MOD / "events/xar_acceptance_events.txt")
    death_probe_on_action = read(
        MOD / "common/on_action/xar_acceptance_on_actions.txt")
    if not all(token in death_probe_effect for token in (
            "character:1132", "is_ai = yes", "add_character_flag = xa_enabled",
            "death = { death_reason = death_old_age }")):
        errors.append("actual AI death probe lost its flagged Roger death precondition")
    if not all(token in death_probe_on_action for token in (
            "has_character_flag = xa_test_ai_death_target", "is_ai = yes",
            "XAR: TEST AI death observed by on_death")):
        errors.append("actual AI death observer lost its runtime guards")
    if not all(token in death_probe_events for token in (
            "NOT = { exists = player_heir }", "add_trait = disinherited",
            "XAR: TEST PASS no_heir_precondition")):
        errors.append("no-heir acceptance probe lost its engine precondition")
    if ("XAR: TEST PASS no_heir_synchronous_return" not in score_snapshot_event
            or "XAR: TEST no-heir snapshot committed" not in score_snapshot_event):
        errors.append("no-heir synchronous-return instrumentation is incomplete")
    bargain_probe_effect = read(
        MOD / "common/scripted_effects/xar_acceptance_bargain_effects.txt")
    bargain_probe_event = read(MOD / "events/xar_acceptance_bargain_events.txt")
    consume_import = extract_block(production_effects, "xar_consume_import_effect") or ""
    bargain_requirements = (
        "global_var:xa_global_record_imported = 2",
        "xar_acceptance_bargain_reopen_start_effect = yes",
    )
    if any(token not in consume_import for token in bargain_requirements):
        errors.append("bargain-reopen threshold-2 bootstrap is not isolated from main selftest")
    for pair in range(1, 4):
        for phase in ("open", "before_curse", "after_curse", "no_early_1094",
                      "reopen_1095"):
            marker = f"XAR: TEST PASS bargain_pair_{pair}_{phase}"
            if marker not in bargain_probe_effect:
                errors.append(f"bargain-reopen probe lacks marker '{marker}'")
    if ("id = xar.0903 days = 1094" not in bargain_probe_effect
            or "value = current_date" not in bargain_probe_effect
            or bargain_probe_effect.count("subtract = global_var:xa_bargain_pair_start_date") != 2
            or bargain_probe_effect.count("global_var:xa_bargain_elapsed_days = 1094") != 3
            or bargain_probe_effect.count("global_var:xa_bargain_elapsed_days = 1095") != 3
            or "trigger = { is_ai = no }" not in bargain_probe_event
            or "has_character_flag = xa_enabled" not in bargain_probe_event
            or "XAR: TEST PASS bargain_pair_3_full_reopen" not in bargain_probe_effect):
        errors.append("bargain-reopen day-1094/player guard/full-third-reopen probe is incomplete")
    progression_probe = read(
        MOD / "common/scripted_effects/xar_acceptance_progression_effects.txt")
    progression_requirements = (
        "global_var:xa_global_record_imported = 3",
        "xar_acceptance_progression_start_effect = yes",
    )
    if any(token not in consume_import for token in progression_requirements):
        errors.append("progression-ui threshold-3 bootstrap is not isolated from selftest")
    for marker in (
            "progression_initial", "progression_contract_3",
            "progression_contract_6", "progression_contract_10",
            "progression_gaze_10", "progression_ledger_state"):
        if f"XAR: TEST PASS {marker}" not in progression_probe:
            errors.append(f"progression-ui probe lacks marker '{marker}'")
    if not all(token in progression_probe for token in (
            "is_ai = no", "xar_add_contract_progress_effect = { ID = 5 }",
            "xar_complete_bargain_pair_effect = yes",
            "has_global_variable = xa_contract_pb_5_10",
            "has_global_variable = xa_contract_complete_5",
            "has_character_flag = xa_gaze_milestone_10",
            "XAR: TEST DONE progression-ui")):
        errors.append("progression-ui state or player guard probe is incomplete")
    generated_contract_events = read(
        MOD / "events/xar_generated_contract_events.txt")
    if (generated_contract_events.count(
            "has_global_variable = xa_progression_ui_active") != 19
            or generated_contract_events.count(
                "xar_acceptance_progression_contract_") != 18
            or generated_contract_events.count(
                "xar_acceptance_progression_gaze_10_effect = yes") != 1):
        errors.append("generated milestone events lost progression-ui option hooks")
    if contract_effects.count(
            "has_global_variable = xa_progression_ui_active") != 28:
        errors.append("generated production dispatchers lost progression-ui event routing")
    release_contract_effects = build_release.render_release_bytes(
        MOD / "common/scripted_effects/xar_generated_contract_effects.txt",
        "common/scripted_effects/xar_generated_contract_effects.txt",
    ).decode("utf-8-sig")
    production_milestone_ids = [
        2100 + contract["id"] * 10 + index + 1
        for contract in gen_contracts.CONTRACTS
        for index, _ in enumerate(gen_contracts.MILESTONES)
    ] + list(range(2201, 2211))
    for event_id in production_milestone_ids:
        if release_contract_effects.count(f"trigger_event = xar.{event_id}") != 1:
            errors.append(
                f"release progression dispatcher must trigger xar.{event_id} exactly once")
    scoring_probe_effect = read(
        MOD / "common/scripted_effects/xar_acceptance_scoring_effects.txt")
    scoring_probe_events = read(MOD / "events/xar_acceptance_scoring_events.txt")
    scoring_requirements = (
        "global_var:xa_global_record_imported = 4",
        "xar_acceptance_scoring_matrix_start_effect = yes",
    )
    if any(token not in consume_import for token in scoring_requirements):
        errors.append("scoring-matrix threshold-4 bootstrap is not isolated from selftest")
    if not all(token in scoring_probe_effect for token in (
            "is_ai = no", "exists = dynasty", "exists = house",
            "set_global_variable = xa_scoring_matrix_active",
            "trigger_event = xar.0910")):
        errors.append("scoring-matrix setup lost its player/family guard or event entry")
    scoring_event_requirements = (
        "xar_compute_score_effect = yes", "value = global_var:xa_a_dyn add = 7",
        "value = global_var:xa_a_hou add = 7", "father = root",
        "father = scope:xar_matrix_left", "mother = scope:xar_matrix_right",
        "death = { death_reason = death_old_age }",
        "global_var:xa_test_scoring_preview_after >= global_var:xa_test_scoring_preview_low",
        "global_var:xa_run_score >= global_var:xa_test_scoring_parity_low",
        "xar_test_dispatcher_sweep_effect = yes",
        "XAR: TEST PASS scoring_descendant_matrix",
        "XAR: TEST PASS scoring_dispatcher_state",
        "XAR: TEST DONE scoring-matrix",
    )
    if any(token not in scoring_probe_events for token in scoring_event_requirements):
        errors.append("scoring-matrix descendant/preview/dispatcher chain is incomplete")
    if scoring_probe_events.count("create_character = {") != 9:
        errors.append("scoring-matrix pedigree must contain eight controls plus one dead parent")
    balance_effects = read(
        MOD / "common/scripted_effects/xar_acceptance_balance_effects.txt")
    balance_fixture_requirements = (
        "has_game_rule = xar_balance_count", "character:212892",
        "has_game_rule = xar_balance_king", "character:214",
        "has_game_rule = xar_balance_emperor", "character:1316",
        "has_game_rule = xar_balance_synthetic", "create_character = {",
        "set_player_character = scope:xar_balance_synthetic_ruler",
        "has_title = title:c_olomouc", "has_title = title:c_prerov",
        "XAR: BALANCE FIXTURE count PASS",
        "XAR: BALANCE FIXTURE king PASS",
        "XAR: BALANCE FIXTURE emperor PASS",
        "XAR: BALANCE FIXTURE synthetic PASS",
    )
    if any(token not in death_probe_on_action for token in balance_fixture_requirements):
        errors.append("balance fixture switch/synthetic assertions are incomplete")
    if not all(token in balance_effects for token in (
            "add_character_flag = xa_balance_fixture_player",
            "id = xar.0927 days = 10950", "id = xar.0928 days = 14600")):
        errors.append("balance fixture lacks its 30/40-year sampling schedule")
    balance_event_requirements = (
        "xar.0920", "xar_compute_score_effect = yes", "xar.0921",
        "XAR: BALANCE SAMPLE BEGIN",
        "xar_acceptance_balance_emit_wire_effect = yes",
        "XAR: BALANCE SAMPLE END", "XAR: BALANCE MIN 30",
        "XAR: BALANCE DONE horizon_40", "XAR: BALANCE DONE natural_death",
        "XAR: BALANCE DONE early_death",
    )
    if any(token not in death_probe_events for token in balance_event_requirements):
        errors.append("balance score/sample/endpoint event chain is incomplete")
    fixture_rule = extract_block(game_rules, "xar_balance_fixture") or ""
    if any(setting not in fixture_rule for setting in (
            "xar_balance_none", "xar_balance_count", "xar_balance_king",
            "xar_balance_emperor", "xar_balance_synthetic")):
        errors.append("development balance fixture rule lost a setting")
    if (events.count("name = xa_balance_sample_kind value = 1") != 3
            or "name = xa_balance_sample_kind value = 5" not in events
            or "name = xa_balance_sample_kind value = 4" not in score_dispatch_event):
        errors.append("balance sampling is not attached to all pair/death production exits")
    for hook in ("on_war_won_attacker", "on_war_won_defender", "on_hook_used",
                 "on_county_faith_change", "on_birth_mother", "on_birth_father",
                 "on_building_completed", "on_birthday"):
        if hook not in on_actions:
            errors.append(f"contract behavior hook missing: {hook}")

    trait = read(MOD / "common/traits/xar_traits.txt")
    trait_track = extract_block(trait, "track") or ""
    thresholds = [int(value) for value in re.findall(
        r"(?m)^\s*(\d+)\s*=\s*{", trait_track)]
    if thresholds != list(range(10, 101, 10)):
        errors.append(f"Glassfire trait track must be 10..100 by 10, got {thresholds}")
    for milestone in gen_contracts.GAZE_MILESTONES:
        block = extract_block(trait_track, str(milestone["xp"])) or ""
        for modifier, value in milestone["modifiers"]:
            if f"{modifier} = {value}" not in block:
                errors.append(
                    f"Glassfire {milestone['xp']} XP lacks growth reward {modifier}={value}")

    pools = read(MOD / "common/scripted_effects/xar_generated_pools_effects.txt")
    curse_draw = extract_block(pools, "xar_draw_curses_effect") or ""
    bless_draw = extract_block(pools, "xar_draw_blessings_effect") or ""
    bless_apply = extract_block(pools, "xar_apply_blessing_effect") or ""
    curse_apply = extract_block(pools, "xar_apply_curse_effect") or ""
    try:
        gen_pools.validate(gen_pools.B, "bless")
        gen_pools.validate(gen_pools.C, "curse")
    except AssertionError as exc:
        errors.append(f"pool data contract invalid: {exc}")
    frozen_pool_digests = {}
    if not POOL_SEMANTIC_CONTRACT.exists():
        errors.append("frozen 200-ID pool semantic contract is missing")
    else:
        for line in read(POOL_SEMANTIC_CONTRACT).splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2 or not re.fullmatch(r"(?:bless|curse)\.\d{3}", parts[0]):
                errors.append(f"invalid pool semantic contract row: {line}")
                continue
            frozen_pool_digests[parts[0]] = parts[1]
    expected_stable_ids = [
        f"{prefix}.{wire_id:03d}"
        for prefix in ("bless", "curse") for wire_id in range(100)
    ]
    if sorted(frozen_pool_digests) != expected_stable_ids:
        errors.append("pool semantic contract must contain bless.000..curse.099 exactly once")
    for prefix, pool, draw, apply, slots in (
            ("bless", gen_pools.B, bless_draw, bless_apply,
             (("a", ()), ("b", ("a",)), ("c", ("a", "b")))),
            ("curse", gen_pools.C, curse_draw, curse_apply,
             (("a", ()), ("b", ("a",)))),):
        apply_guards = [int(value) for value in re.findall(
            rf"global_var:xa_{prefix}_\$SLOT\$ = (\d+)", apply)]
        if apply_guards != list(range(100)):
            errors.append(f"{prefix} apply dispatcher guards are not exact wire IDs 0..99")
        compact_apply = compact_script(apply)
        compact_draw = compact_script(draw)
        for wire_id, entry in enumerate(pool):
            stable_id = f"{prefix}.{wire_id:03d}"
            digest = pool_semantic_digest(prefix, wire_id, entry)
            if frozen_pool_digests.get(stable_id) != digest:
                errors.append(f"frozen pool semantics changed for {stable_id}")
            expected_apply = compact_script(
                expected_pool_apply_branch(prefix, wire_id, entry))
            if compact_apply.count(expected_apply) != 1:
                errors.append(f"{stable_id} is not mapped to its exact apply effect")
            for slot, prior in slots:
                expected_draw = compact_script(expected_pool_draw_branch(
                    prefix, slot, prior, wire_id, entry))
                if compact_draw.count(expected_draw) != 1:
                    errors.append(
                        f"{stable_id} draw semantics drifted in {prefix} slot {slot}")
    if (bless_apply.count("name = xa_bless_session add = 1") != 1
            or bless_apply.count("name = xa_bless_count add = 1") != 1):
        errors.append("blessing dispatcher must advance cumulative count/session exactly once")
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
    if pools.count("XAR: TEST PASS pool_dispatch_bless_") != 100:
        errors.append("blessing dispatcher lacks 100 acceptance branch markers")
    if pools.count("XAR: TEST PASS pool_dispatch_curse_") != 100:
        errors.append("curse dispatcher lacks 100 acceptance branch markers")
    dispatcher_sweep = extract_block(pools, "xar_test_dispatcher_sweep_effect") or ""
    if (dispatcher_sweep.count("xar_apply_blessing_effect = { SLOT = a }") != 100
            or dispatcher_sweep.count("xar_apply_curse_effect = { SLOT = a }") != 100
            or "XAR: TEST PASS pool_dispatch_all_200" not in dispatcher_sweep):
        errors.append("acceptance dispatcher sweep does not cross all 200 production branches")
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
    if "subtract = { value = global_var:xa_score_baseline }\n\t\tmin = 0" not in preview:
        errors.append("score preview growth subtraction lacks a zero lower bound")
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
    production_child_lists = generated_score_effects.count("every_child = {")
    production_dead_inclusive = len(re.findall(
        r"every_child\s*=\s*\{\s*even_if_dead\s*=\s*yes",
        generated_score_effects))
    expected_child_lists = scoring_data.DESCENDANT_DEPTH * 2
    if (production_child_lists != expected_child_lists
            or production_dead_inclusive != expected_child_lists):
        errors.append(
            "production descendant traversal/cleanup must cross every dead intermediate")
    if (generated_score_effects.count("limit = { is_alive = yes }") < 5
            or generated_score_effects.count(
                "remove_character_flag = xar_desc_counted") != 5):
        errors.append("descendant cleanup must skip flag effects on dead scopes")
    preview_child_lists = preview.count("every_child = {")
    preview_dead_inclusive = len(re.findall(
        r"every_child\s*=\s*\{\s*even_if_dead\s*=\s*yes", preview))
    if (preview_child_lists != scoring_data.DESCENDANT_DEPTH
            or preview_dead_inclusive != scoring_data.DESCENDANT_DEPTH):
        errors.append("score preview descendant traversal must cross dead intermediates")
    preview_parent_lists = preview.count("any_parent = {")
    preview_dead_parents = len(re.findall(
        r"any_parent\s*=\s*\{\s*even_if_dead\s*=\s*yes", preview))
    if not preview_parent_lists or preview_parent_lists != preview_dead_parents:
        errors.append("score preview pedigree dedup excludes a dead parent path")
    count_adapter = extract_block(hand_score_effects, "xar_desc_count_self") or ""
    adapter_requirements = (
        "is_alive = yes", "NOT = { has_character_flag = xar_desc_counted }",
        "add_character_flag = xar_desc_counted",
        "xar_descendant_tier_count_effect = yes",
        "change_global_variable = { name = xa_a_dyn add = 1 }",
        "change_global_variable = { name = xa_a_hou add = 1 }",
    )
    if (any(token not in count_adapter for token in adapter_requirements)
            or count_adapter.count("xar_descendant_tier_count_effect = yes") != 1):
        errors.append("hand-written descendant dedup/blood adapter is incomplete")
    expected_log_thresholds = [2 ** exponent for exponent in range(1, 31)]
    production_log_thresholds = [int(value) for value in re.findall(
        r"\$SRC\$ >= (\d+)", generated_score_effects)]
    if production_log_thresholds != expected_log_thresholds:
        errors.append("production log2 ladder is not the reviewed 2^1..2^30 boundary set")
    for source in ("gold", "prestige", "piety", "influence", "realm_size"):
        preview_thresholds = [int(value) for value in re.findall(
            rf"limit = \{{ {source} >= (\d+) \}}", preview)]
        if preview_thresholds != expected_log_thresholds:
            errors.append(f"score preview {source} log2 ladder has boundary drift")
    if ("value = global_var:xa_contract_progress min = 0 max = 10"
            not in generated_score_effects
            or "value = global_var:xa_contract_progress min = 0 max = 10"
            not in preview):
        errors.append("contract score is not clamped to its reviewed 0..10 boundary")
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
    ledger = extract_block(generated_effects, "xar_project_ledger_effect") or ""
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
    if "subtract = global_var:xa_score_baseline min = 0" not in generated_score_effects:
        errors.append("production growth score lacks a zero lower bound")
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
    if "max = 0" in ledger:
        errors.append("ledger gap uses max=0 as an upper bound instead of min=0 as a lower bound")
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

    if "global_var:xa_record_candidate > global_var:xa_old_record" not in score_dispatch_event:
        errors.append("death settlement dispatcher does not use strict candidate record comparison")
    if "global_var:xa_run_score > global_var:xa_old_record" in on_actions + events:
        errors.append("production record comparison still uses the real run score")


def package_checks(errors):
    errors.extend(build_release.release_source_errors(MOD))
    try:
        release_entries = build_release.release_entries(MOD)
        errors.extend(build_release.release_projection_errors(release_entries))
    except ValueError as exc:
        errors.append(f"release projection invalid: {exc}")
    descriptor = read(MOD / "descriptor.mod")
    if "remote_file_id" in descriptor:
        errors.append("repository descriptor.mod contains remote_file_id")
    if not re.search(r'(?m)^version="\d+\.\d+\.\d+"$', descriptor):
        errors.append("descriptor.mod lacks a semantic version")
    if 'picture="thumbnail.png"' not in descriptor:
        errors.append("descriptor.mod picture is not thumbnail.png")
    if 'supported_version="1.19.0.6"' not in descriptor:
        errors.append("descriptor.mod tested CK3 version changed without release QA update")
    official_ci = read(ROOT / ".github/workflows/static-ci.yml")
    ci_requirements = (
        "runs-on: windows-latest", "pull_request:", "workflow_dispatch:",
        "tools/requirements-static.txt", "python -m compileall -q tools",
        "python tools/validate_static.py", "scoring_data.assert_reference_vectors()",
        "python tools/build_release.py --check", "python tools/build_release.py --release",
        "actions/upload-artifact@v4", "dist/*.zip", "dist/*.manifest.json",
    )
    if any(token not in official_ci for token in ci_requirements):
        errors.append("official-runner CI lost a static, release, or artifact gate")
    if "self-hosted" in official_ci or "run_acceptance.py" in official_ci:
        errors.append("official-runner CI must not claim CK3 desktop acceptance")
    if (ROOT / ".github/workflows/ck3-self-hosted-ci.yml").exists():
        errors.append("unavailable self-hosted CK3 workflow still exists")
    acceptance_runner = read(ROOT / "tools/run_acceptance.py")
    if "click_ratio(0.38, 0.72)" in acceptance_runner:
        errors.append("acceptance runner still uses the stale blind event-recovery click")
    if not all(token in acceptance_runner for token in (
            "capture_stall_and_recover", "_annotated.png", "_ocr.json",
            "remained stalled after 3 screenshot-guided recoveries",
            "0.34 <= x_ratio <= 0.74", "box_height_ratio <= 0.035",
            "0.75 if x_ratio <= 0.49 else 0.84",
            "inspect stall_selftest_*.png/json", "HUD_DATE_REGION",
            "read_hud_game_day", "HUD date already advancing at speed 5",
            "HUD date advanced after timeline play", "GetForegroundWindow",
            "AttachThreadInput", "CK3 could not obtain foreground")):
        errors.append("acceptance runner lost screenshot-guided stall diagnostics")
    speed_control = acceptance_runner.partition(
        "def set_speed_five_and_unpause")[2].partition("\ndef ")[0]
    if not all(token in speed_control for token in (
            "read_hud_game_date", "timeline_play", "timeline play")):
        errors.append("speed-5 control lacks OCR-targeted unpause verification")
    lobby_navigation = acceptance_runner.partition(
        "def navigate_lobby")[2].partition("\ndef ")[0]
    if ("main-menu New Game" not in lobby_navigation
            or "click_until_ocr_appears" not in lobby_navigation
            or "pyautogui.click(*new_game)" in lobby_navigation):
        errors.append("lobby navigation lacks an OCR-verified New Game transition")
    if not all(token in acceptance_runner for token in (
            '"progression-ui": 3', "def run_progression_ui",
            "wait_for_contract_lessons", "open_native_ledger",
            "progression_ledger_pixels", "xar_contract_complete_steward",
            "XAR: TEST DONE progression-ui")):
        errors.append("acceptance runner lacks progression milestone/PB pixel coverage")
    if not all(token in acceptance_runner for token in (
            '"scoring-matrix": 4', "def run_scoring_matrix",
            "pool_dispatchers", "expected_pool_markers",
            "XAR: TEST DONE scoring-matrix")):
        errors.append("acceptance runner lacks scoring/dedup/200-dispatcher coverage")
    if not all(token in acceptance_runner for token in (
            '"balance-long": 0', "BALANCE_FIXTURES", "declared_vanilla_rule_defaults",
            "set_balance_applied_rules", "def run_balance_long",
            "decode_balance_wire_sample", "cadence_1095_days",
            "XAR: BALANCE DONE horizon_40", "--balance-smoke-pairs")):
        errors.append("acceptance runner lacks the declared-default passive balance matrix")
    balance_matrix_runner = read(ROOT / "tools/run_balance_matrix.py")
    if not all(token in balance_matrix_runner for token in (
            'FIXTURES = ("count", "king", "emperor", "synthetic")',
            '"--scenario", "balance-long"', "balance-matrix.json",
            "instrumented engineering samples")):
        errors.append("serial balance matrix aggregator is incomplete")
    restore_watchdog = read(ROOT / "tools/restore_watchdog.py")
    autosave_protection = (
        "SAVE_GAMES_DIR", 'glob("autosave*.ck3")', "autosaves.ready",
        "autosave backup verification failed", "restore_autosaves(backup)",
        "DLC_LOAD_JSON", "set_enabled_mod_profile", "ugc_3784706360.mod",
    )
    if (any(token not in acceptance_runner for token in autosave_protection)
            or any(token not in restore_watchdog for token in (
                'glob("autosave*.ck3")', "autosaves.ready",
                "autosave restore verification failed"))):
        errors.append("acceptance runner/watchdog lacks atomic autosave isolation")
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
    if sys.argv[1:] == ["--print-pool-contract"]:
        print(render_pool_semantic_contract(), end="")
        sys.exit(0)
    sys.exit(main())
