#!/usr/bin/env python3
"""Prepare XQOL's disposable official-engine fixture; never launch or inject CK3."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import fixture_engine_prepare as prep

START = '''on_game_start_after_lobby = { on_actions = { zqa120_start } }
zqa120_start = {
    effect = {
        debug_log = "ZQA120: TEST BEGIN engine_startup"
        random_player = { trigger_event = { id = zqa120.1 days = 1 } }
    }
}
'''

RITE_CHECK = '''
        if = {
            limit = {
                var:xqol_last_bulk_release_count = 7
                var:zqa_release_hrc_target = { rite = root.rite }
                var:zqa_release_hc_target = { rite = root.rite }
                var:zqa_release_rc_target = { rite = root.rite }
                var:zqa_release_c_target = { rite = root.rite }
            }
            debug_log = "ZQA120: TEST PASS release_conversion_rite_matched"
        }
        else = { debug_log = "ZQA120: TEST FAIL release_conversion_rite_matched" }
'''

RITE_PROBE = '''zqa120_accepted_rite_probe_effect = {
    save_scope_as = actor
    save_scope_as = puppet_or_actor
    create_character = {
        name = "ZQA120 Accepted Rite Probe"
        gender = male
        age = 30
        random_traits = no
        location = root.capital_province
        culture = root.culture
        faith = faith:catholic
        save_scope_as = zqa120_rite_subject
    }
    add_courtier = scope:zqa120_rite_subject
    scope:zqa120_rite_subject = { save_scope_as = recipient }
    set_variable = { name = xqol_mass_conversion_pending value = 1 }
    set_variable = { name = xqol_mass_conversion_accepted value = 0 }
    set_variable = { name = xqol_mass_conversion_refused value = 0 }
    set_variable = { name = zqa120_rite_subject value = scope:zqa120_rite_subject }
    scope:recipient = { xqol_mass_conversion_courtier_accepted_effect = yes }
    debug_log = "ZQA120: TEST READY accepted_conversion_rite"
}
zqa120_verify_accepted_rite_probe_effect = {
    if = {
        limit = {
            var:zqa120_rite_subject = { faith = root.faith rite = root.rite }
            var:xqol_mass_conversion_accepted = 1
            NOT = { has_variable = xqol_mass_conversion_pending }
        }
        debug_log = "ZQA120: TEST PASS accepted_conversion_faith_and_rite"
    }
    else = { debug_log = "ZQA120: TEST FAIL accepted_conversion_faith_and_rite" }
    remove_variable = zqa120_rite_subject
}
'''


def event(name: str, body: str) -> str:
    return f"{name} = {{\n    type = character_event\n    hidden = yes\n    immediate = {{\n{body}\n    }}\n}}\n"


def events(governors_only: bool) -> str:
    initialize = '''        if = {
        limit = { NOT = { has_character_flag = zqa_fixture_initialized } }
        add_character_flag = zqa_initialize_pending
        zqa_initialize_effect = yes
        random_player = {
            set_variable = { name = zqa120_stage value = 1 }
            set_variable = { name = zqa120_ticks value = 0 }
            trigger_event = { id = zqa120.2 days = 1 }
        }
        }'''
    after_disable = ('''                    debug_log = "ZQA120: TEST DONE governor_core"
                    set_variable = { name = zqa120_stage value = 99 }''' if governors_only else
                     '''                    zqa_setup_payment_matrix_effect = yes
                     save_scope_value_as = { name = zqa120_payment_expected_gold value = var:zqa_payment_expected_gold }
                     save_scope_value_as = { name = zqa120_payment_expected_count value = var:zqa_payment_expected_count }
                     xqol_bulk_demand_payment_full_effect = yes
                     zqa120_payment_full_diagnostic_effect = yes
                     zqa_verify_payment_full_effect = yes
                     xqol_bulk_demand_payment_any_effect = yes
                     zqa_verify_payment_any_effect = yes
                     set_variable = { name = xqol_mass_conversion_threshold value = 50 }
                     xqol_bulk_conversion_dispatch_effect = yes
                     set_variable = { name = zqa120_stage value = 5 }''')
    tick = '''        change_variable = { name = zqa120_ticks add = 1 }
        if = {
            limit = { var:zqa120_stage = 1 has_character_flag = zqa_await_product_toggles }
            zqa120_enable_appointment_effect = yes
            zqa120_enable_transfer_effect = yes
            zqa120_enable_defenders_effect = yes
            debug_log = "ZQA120: TEST PASS production_enable_effects_invoked"
            set_variable = { name = zqa120_stage value = 11 }
        }
        else_if = {
            limit = { var:zqa120_stage = 11 has_character_flag = zqa_await_product_toggles }
            debug_log = "ZQA120: OBSERVED enabled_governor_current_scopes"
            var:zqa120_removal_incumbent = { debug_log_scopes = yes }
            var:zqa120_baseline_heir = { debug_log_scopes = yes }
            var:zqa120_removal_title = { debug_log_scopes = yes current_heir = { debug_log_scopes = yes } }
            zqa_run_enabled_matrix_effect = yes
            set_variable = { name = zqa120_stage value = 2 }
        }
        else_if = {
            limit = {
                var:zqa120_stage = 2
                has_character_flag = zqa_await_death_settlement
                var:zqa_death_title = {
                    exists = holder
                    NOT = { holder = root }
                    NOT = { holder = root.var:zqa_death_incumbent }
                }
            }
            zqa_verify_death_settlement_effect = yes
            zqa120_disable_appointment_effect = yes
            zqa120_disable_transfer_effect = yes
            zqa120_disable_defenders_effect = yes
            debug_log = "ZQA120: TEST PASS production_disable_effects_invoked"
            zqa_verify_disabled_matrix_effect = yes
AFTER_DISABLE
        }
        else_if = {
            limit = { var:zqa120_stage = 3 has_character_flag = zqa_await_payment_full }
            zqa_verify_payment_full_effect = yes
            xqol_bulk_demand_payment_any_effect = yes
            set_variable = { name = zqa120_stage value = 4 }
        }
        else_if = {
            limit = { var:zqa120_stage = 4 has_character_flag = zqa_await_payment_any }
            zqa_verify_payment_any_effect = yes
            set_variable = { name = xqol_mass_conversion_threshold value = 50 }
            xqol_bulk_conversion_dispatch_effect = yes
            set_variable = { name = zqa120_stage value = 5 }
        }
        else_if = {
            limit = {
                var:zqa120_stage = 5
                has_character_flag = zqa_await_conversion_matrix
                NOT = { has_variable = xqol_mass_conversion_pending }
                has_variable = xqol_mass_conversion_accepted
                has_variable = xqol_mass_conversion_refused
            }
            zqa_verify_conversion_matrix_effect = yes
            xqol_bulk_ransom_full_effect = yes
            set_variable = { name = zqa120_stage value = 6 }
        }
        else_if = {
            limit = { var:zqa120_stage = 6 has_character_flag = zqa_await_ransom_full }
            zqa_verify_ransom_full_effect = yes
            xqol_bulk_ransom_any_effect = yes
            set_variable = { name = zqa120_stage value = 7 }
        }
        else_if = {
            limit = { var:zqa120_stage = 7 has_character_flag = zqa_await_ransom_any }
            zqa_verify_ransom_any_effect = yes
            xqol_bulk_release_terms_effect = yes
            set_variable = { name = zqa120_stage value = 8 }
        }
        else_if = {
            limit = { var:zqa120_stage = 8 has_character_flag = zqa_await_release_matrix }
            zqa_verify_release_matrix_effect = yes
            set_variable = { name = zqa120_stage value = 9 }
        }
        else_if = {
            limit = { var:zqa120_stage = 9 has_variable = zqa120_rite_subject }
            zqa120_verify_accepted_rite_probe_effect = yes
            set_variable = { name = zqa120_stage value = 99 }
            debug_log = "ZQA120: TEST DONE core"
        }
        if = {
            limit = { var:zqa120_stage < 99 }
            if = {
                limit = { var:zqa120_ticks < 60 }
                trigger_event = { id = zqa120.2 days = 1 }
            }
            else = {
                debug_log = "ZQA120: TEST FAIL driver_timeout"
                set_variable = { name = zqa120_stage value = 99 }
            }
        }'''.replace("AFTER_DISABLE", after_disable)
    return "namespace = zqa120\n\n" + event("zqa120.1", initialize) + "\n" + event("zqa120.2", tick)


def payment_diagnostic() -> str:
    checks = {
        "count": "var:xqol_last_bulk_payment_count = var:zqa_payment_expected_count",
        "actor_gold": "gold >= var:zqa_payment_expected_gold NOT = { gold > var:zqa_payment_expected_gold }",
        "full_hook_consumed": "NOT = { has_usable_hook = var:zqa_payment_full_target }",
        "any_hook_preserved": "has_usable_hook = var:zqa_payment_any_target",
        "one_hook_preserved": "has_usable_hook = var:zqa_payment_one_gold_target",
        "full_wallet": "var:zqa_payment_full_target = { gold < 1 }",
        "any_wallet": "var:zqa_payment_any_target = { gold >= 2 NOT = { gold > 2 } }",
        "one_wallet": "var:zqa_payment_one_gold_target = { gold >= 1 NOT = { gold > 1 } }",
    }
    lines = ["zqa120_payment_full_diagnostic_effect = {",
             "\tsave_scope_value_as = { name = zqa120_payment_actual_gold value = gold }",
             "\tsave_scope_value_as = { name = zqa120_payment_actual_count value = var:xqol_last_bulk_payment_count }"]
    for short in ("full", "any", "one_gold"):
        lines.append(f"\tvar:zqa_payment_{short}_target = {{ save_scope_as = zqa120_payment_{short}_target save_scope_value_as = {{ name = zqa120_payment_{short}_wallet value = gold }} }}")
    for name, condition in checks.items():
        lines.append(f'\tif = {{ limit = {{ {condition} }} debug_log = "ZQA120: OBSERVED payment_{name}_PASS" }} else = {{ debug_log = "ZQA120: OBSERVED payment_{name}_FAIL" }}')
    lines += ['\tdebug_log = "ZQA120: OBSERVED payment_full_transaction_scopes"', "\tdebug_log_scopes = yes", "}"]
    return "\n".join(lines) + "\n"


def prepare(repo: Path, output: Path, scenario: str) -> dict:
    repo, output = prep.checked_output(repo, output)
    source = repo / "tools/fixtures/xqol_acceptance"
    files = [source / "descriptor.mod", *sorted((source / "common/scripted_effects").glob("*.txt")),
             *sorted((source / "localization").rglob("*.yml"))]
    prep.copy_files(source, output, files)
    base_path = output / "common/scripted_effects/zqa_effects.txt"
    base = base_path.read_text(encoding="utf-8-sig")
    # This fixture excludes the legacy defense GUI/decisions; their separate
    # initializer is unreachable here and must not leave orphan flag contracts.
    for key in ("zqa_defense_initialize_effect", "zqa_defense_setup_after_switch_effect"):
        defense_init = prep.balanced_excerpt(base, rf"^{key}\s*=\s*\{{")
        base = prep.replace_once(base, defense_init, "# Legacy defense initializer/callback excluded from this core fixture.")
    base = base.replace("golden_obligation_value", "xqol_full_golden_obligation_value")
    # The 1.20 native quote reads actor (strong hooks) and recipient (rich
    # courtiers). Compute expected native transfers in that same context.
    payment_setup = prep.balanced_excerpt(base, r"^zqa_setup_payment_matrix_effect\s*=\s*\{")
    changed_payment = prep.replace_once(payment_setup, "zqa_setup_payment_matrix_effect = {", "zqa_setup_payment_matrix_effect = {\n\tsave_scope_as = actor\n\tsave_scope_as = puppet_or_actor")
    expected_loop = prep.balanced_excerpt(changed_payment, r"^\tevery_hooked_character\s*=\s*\{")
    loop_body = expected_loop[expected_loop.index("{") + 1:expected_loop.rfind("}")]
    changed_loop = "\tevery_hooked_character = {\n\t\tsave_scope_as = recipient\n\t\tif = {" + "\n".join("\t" + line if line else line for line in loop_body.splitlines()) + "\n\t\t}\n\t}"
    changed_loop = prep.replace_once(changed_loop, "add = scope:zqa_payment_expected_candidate.xqol_full_golden_obligation_value", """add = {
                    if = {
                        limit = { scope:zqa_payment_expected_candidate = { gold > golden_obligation_value } }
                        value = scope:zqa_payment_expected_candidate.golden_obligation_value
                    }
                    else = { value = scope:zqa_payment_expected_candidate.gold floor = yes }
                }""")
    changed_payment = prep.replace_once(changed_payment, expected_loop, changed_loop)
    base = prep.replace_once(base, payment_setup, changed_payment)
    # Baselines must refer to actual appointment governors, not estate titles
    # or frail randomly chosen incumbents. Preserve the strict heir assertion.
    init = prep.balanced_excerpt(base, r"^zqa_initialize_effect\s*=\s*\{")
    guard = ("is_ai = yes\n{indent}age < 60\n{indent}health >= 4\n"
             "{indent}OR = {{ has_realm_law = appointment_succession_law "
             "has_realm_law = celestial_appointment_succession_law "
             "has_realm_law = celestial_military_appointment_succession_law }}\n"
             "{indent}primary_title = {{ is_landless_type_title = no }}")
    changed_init = re.sub(r"(?m)^(\t+)is_landed = yes$", lambda m: m[0] + "\n" + m[1] + guard.format(indent=m[1]), init)
    proof = '''
            scope:zqa_vanilla_removal_incumbent = {
                debug_log = "ZQA120: OBSERVED baseline_incumbent_scope"
                debug_log_scopes = yes
                primary_title = { save_scope_as = zqa120_removal_title debug_log_scopes = yes }
                primary_title.current_heir = { save_scope_as = zqa120_baseline_heir debug_log_scopes = yes }
            }
            scope:zqa_song_emperor = {
                set_variable = { name = zqa120_removal_incumbent value = scope:zqa_vanilla_removal_incumbent }
                set_variable = { name = zqa120_removal_title value = scope:zqa120_removal_title }
                set_variable = { name = zqa120_baseline_heir value = scope:zqa120_baseline_heir }
            }
'''
    changed_init = prep.replace_once(changed_init, '\t\t\tdebug_log = "ZQA: TEST PASS vanilla_baseline_heirs_recorded"', proof + '\t\t\tdebug_log = "ZQA: TEST PASS vanilla_baseline_heirs_recorded"')
    base = prep.replace_once(base, init, changed_init)
    death = prep.balanced_excerpt(base, r"^zqa_run_enabled_matrix_effect\s*=\s*\{")
    death_changed = prep.replace_once(death, "\t\t\tis_ai = yes\n\t\t\tis_landed = yes", "\t\t\tis_ai = yes\n\t\t\tis_landed = yes\n\t\t\t" + guard.format(indent="\t\t\t") + "\n\t\t\tNOT = { has_character_flag = zqa_removal_incumbent_subject }")
    base = prep.replace_once(base, death, death_changed)
    # The driver invokes the next setup once; the original callback had chained it.
    base = prep.replace_once(base, "\tzqa_setup_payment_matrix_effect = yes\n", "\t# The 1.20 hidden driver chooses the next matrix.\n")
    if scenario == "administrative":
        original = prep.balanced_excerpt(base, r"^zqa_initialize_effect\s*=\s*\{")
        changed = prep.replace_once(original, "character:han_8052", "title:e_byzantium.holder")
        changed = prep.replace_once(changed, "has_title = title:h_china", "has_title = title:e_byzantium")
        changed = prep.replace_once(changed, "has_government = celestial_government", "government_has_mechanic = administrative")
        changed = changed.replace("exact_build_song_emperor", "selected_administrative_ruler")
        base = prep.replace_once(base, original, changed)
    interaction_path = output / "common/scripted_effects/zqa_phase2_interaction_effects.txt"
    interactions = interaction_path.read_text(encoding="utf-8-sig")
    interactions = prep.replace_once(interactions, "\t\tremove_variable = zqa_release_hrc_target\n", RITE_CHECK + "\t\tremove_variable = zqa_release_hrc_target\n")
    interactions = prep.replace_once(interactions, "\t\tzqa_setup_defense_matrix_effect = yes\n", "\t\tzqa120_accepted_rite_probe_effect = yes\n")
    for path, text in ((base_path, base), (interaction_path, interactions)):
        text = text.replace("save_scope_as = actor\n", "save_scope_as = actor\n\tsave_scope_as = puppet_or_actor\n")
        path.write_text(text, encoding="utf-8-sig", newline="\n")
    projections = []
    effects = []
    for short, decision in (
        ("enable_appointment", "xqol_enable_auto_appointment_decision"),
        ("enable_transfer", "xqol_enable_no_vassal_transfers_decision"),
        ("enable_defenders", "xqol_enable_auto_call_defenders_decision"),
        ("disable_appointment", "xqol_disable_auto_appointment_decision"),
        ("disable_transfer", "xqol_disable_no_vassal_transfers_decision"),
        ("disable_defenders", "xqol_disable_auto_call_defenders_decision"),
    ):
        body, proof = prep.decision_effect(repo, "mod_xenoamess_quality_of_life", "common/decisions/xqol_decisions.txt", decision)
        effects.append(f"zqa120_{short}_effect = {{\n{body}\n}}\n")
        projections.append(proof)
    prep.write_script(output, "common/scripted_effects/zqa120_production_effects.txt", "\n".join(effects) + "\n" + RITE_PROBE + "\n" + payment_diagnostic())
    prep.write_script(output, "common/on_action/zqa120_on_actions.txt", START)
    prep.write_script(output, "events/zqa120_events.txt", events(scenario == "administrative"))
    markers = prep.required_markers(repo / "tools/run_xenoamess_quality_of_life_acceptance.py")
    boundary = markers.index("ZQA: TEST PASS conversion_threshold_50_filtered")
    if scenario == "administrative":
        markers = markers[:boundary - 3]
        markers = [item.replace("exact_build_song_emperor", "selected_administrative_ruler") for item in markers]
        markers.append("ZQA120: TEST DONE governor_core")
    else:
        markers = markers[:markers.index("ZQA: TEST PASS defense_fixture_setup")]
        markers += ["ZQA120: TEST PASS release_conversion_rite_matched", "ZQA120: TEST PASS accepted_conversion_faith_and_rite", "ZQA120: TEST DONE core"]
    markers += ["ZQA120: TEST BEGIN engine_startup", "ZQA120: TEST PASS production_enable_effects_invoked", "ZQA120: TEST PASS production_disable_effects_invoked"]
    return prep.finish_receipt(repo, source, output, files, {
        "product":"mod_xenoamess_quality_of_life", "scenario":scenario,
        "bookmark":"1066-09-15; begin as any human ruler except the fixture target (Song emperor / Byzantine emperor)",
        "entry":"on_game_start_after_lobby -> zqa120.1 -> daily hidden zqa120.2",
        "max_game_days":60, "expected_game_days":"governors 3-8; full core 10-40 depending AI conversion reply",
        "game_rules":{}, "required_markers":markers,
        "reject_markers":["ZQA: TEST FAIL", "ZQA120: TEST FAIL"],
        "production_effect_projections":projections,
        "coverage":"Production effect consequences and existing engine predicates; decision clicks, conversion slider, native reply UI and governor nomination panels are not executed. Defense-war matrix is not run.",
        "governor_boundary":"1066 selected ruler's native current-heir/removal/death paths are exercised; this does not identify every appointment family or prove all three governor panels.",
        "rite_boundary":"Batch conversion keeps its acceptance/refusal assertion; an additional deterministic production accepted-outcome call proves faith+rite, not an AI reply or GUI click.",
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", choices=("celestial", "administrative"), default="celestial")
    args = parser.parse_args()
    receipt = prepare(args.repo, args.output, args.scenario)
    print(json.dumps({"prepared_fixture":receipt["prepared_fixture"], "scenario":args.scenario, "runtime_status":"NOT_RUN"}))


if __name__ == "__main__":
    main()
