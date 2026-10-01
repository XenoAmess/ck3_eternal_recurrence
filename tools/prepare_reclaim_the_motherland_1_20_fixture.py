#!/usr/bin/env python3
"""Prepare RMTM's disposable official-engine fixture; never launch or inject CK3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fixture_engine_prepare as prep

START = '''on_game_start_after_lobby = { on_actions = { rqa120_start } }
rqa120_start = {
    effect = {
        debug_log = "RQA120: TEST BEGIN engine_startup"
        random_player = { trigger_event = { id = rqa120.1 } }
    }
}
'''

CONTINUE = '''rqa120_continue_decision = {
    picture = { reference = "gfx/interface/illustrations/decisions/decision_realm.dds" }
    decision_group_type = rqa_acceptance
    sort_order = 1
    ai_check_interval = 0
    desc = rqa120_continue_decision_desc
    selection_tooltip = rqa120_continue_decision_tooltip
    is_shown = { is_ai = no has_character_flag = rqa120_ui_checkpoint }
    is_valid = { rmtm_holds_restoration_hegemony_trigger = yes }
    effect = {
        remove_character_flag = rqa120_ui_checkpoint
        set_variable = { name = rqa120_stage value = 5 }
        trigger_event = { id = rqa120.2 days = 1 }
    }
    ai_potential = { always = no }
}
'''


def event(name: str, body: str) -> str:
    return f"{name} = {{\n    type = character_event\n    hidden = yes\n    immediate = {{\n{body}\n    }}\n}}\n"


def events(ui_checkpoints: bool) -> str:
    initialize = '''        add_character_flag = rqa_initialize_pending
        rqa_initialize_effect = yes
        random_player = {
            set_variable = { name = rqa120_stage value = 1 }
            set_variable = { name = rqa120_ticks value = 0 }
            trigger_event = { id = rqa120.2 days = 1 }
        }'''
    checkpoint = ('''            add_character_flag = rqa120_ui_checkpoint
            set_variable = { name = rqa120_stage value = 90 }
            debug_log = "RQA120: TEST READY ui_after_chaos"''' if ui_checkpoints else
                  '''            set_variable = { name = rqa120_stage value = 5 }''')
    tick = '''        change_variable = { name = rqa120_ticks add = 1 }
        if = {
            limit = { var:rqa120_stage = 1 has_character_flag = rqa_ready_to_enter_chaos }
            add_character_flag = rqa_chaos_pending
            rqa_enter_chaos_effect = yes
            set_variable = { name = rqa120_stage value = 2 }
        }
        else_if = {
            limit = { var:rqa120_stage = 2 has_character_flag = rqa_dispatch_chaos_event_pending }
            rqa_dispatch_chaos_event_effect = yes
            set_variable = { name = rqa120_stage value = 3 }
        }
        else_if = {
            limit = {
                var:rqa120_stage = 3
                has_character_flag = rqa_waiting_for_chaos
                NOT = { has_title = title:h_china }
                rmtm_holds_restoration_hegemony_trigger = yes
            }
            rqa_verify_chaos_effect = yes
            if = {
                limit = {
                    government_has_flag = government_is_celestial
                    government_has_flag = government_uses_ministry_budget
                    tgp_has_access_to_ministry_trigger = yes
                    primary_title = global_var:rmtm_ministry_entitlement_title
                }
                debug_log = "RQA120: TEST PASS later_ministry_budget_gate"
            }
            else = { debug_log = "RQA120: TEST FAIL later_ministry_budget_gate" }
            rqa_execute_vassalization_probe_effect = yes
            set_variable = { name = rqa120_stage value = 4 }
        }
        else_if = {
            limit = { var:rqa120_stage = 4 has_character_flag = rqa_waiting_for_vassalization_probe }
            rqa_verify_vassalization_probe_effect = yes
CHECKPOINT
        }
        else_if = {
            limit = { var:rqa120_stage = 5 has_character_flag = rqa_ready_for_succession }
            primary_title.current_heir = {
                set_variable = { name = rqa120_stage value = 6 }
                set_variable = { name = rqa120_ticks value = 0 }
                trigger_event = { id = rqa120.2 days = 3 }
            }
            add_character_flag = rqa_succession_pending
            # The existing effect changes the player and kills this predecessor.
            rqa_execute_succession_effect = yes
            set_variable = { name = rqa120_stage value = 99 }
        }
        else_if = {
            limit = {
                var:rqa120_stage = 6
                has_character_flag = rqa_waiting_for_recent_independence_expiry
                var:rqa_defecting_direct.primary_title = {
                    NOT = { exists = var:rmtm_recently_independent_from_restoration_hegemony }
                }
                var:rqa_control_ruler.primary_title = {
                    NOT = { exists = var:rmtm_recently_independent_from_restoration_hegemony }
                }
            }
            rqa_verify_recent_independence_expiry_effect = yes
            add_character_flag = rqa_threshold_pending
            rqa_prepare_threshold_effect = yes
            set_variable = { name = rqa120_stage value = 7 }
        }
        else_if = {
            limit = { var:rqa120_stage = 7 has_character_flag = rqa_waiting_for_restoration }
            rqa120_production_restoration_effect = yes
            if = {
                limit = { NOT = { exists = var:rqa_later_title.holder } }
                debug_log = "RQA120: TEST PASS restoration_later_title_unheld"
            }
            else = { debug_log = "RQA120: TEST FAIL restoration_later_title_unheld" }
            rqa_verify_restoration_effect = yes
            set_variable = { name = rqa120_stage value = 99 }
            debug_log = "RQA120: TEST DONE core"
        }
        if = {
            limit = { is_alive = yes var:rqa120_stage < 90 }
            if = {
                limit = { var:rqa120_ticks < 60 }
                trigger_event = { id = rqa120.2 days = 1 }
            }
            else = {
                debug_log = "RQA120: TEST FAIL driver_timeout"
                set_variable = { name = rqa120_stage value = 99 }
            }
        }'''.replace("CHECKPOINT", checkpoint)
    return "namespace = rqa120\n\n" + event("rqa120.1", initialize) + "\n" + event("rqa120.2", tick)


def prepare(repo: Path, output: Path, ui_checkpoints: bool, duration: int) -> dict:
    repo, output = prep.checked_output(repo, output)
    if not 10 <= duration <= 30:
        raise ValueError("compressed political-memory duration must be between 10 and 30 days")
    source = repo / "tools/fixtures/reclaim_the_motherland_acceptance"
    files = [source / "descriptor.mod", source / "common/scripted_effects/rqa_effects.txt",
             source / "common/scripted_triggers/rqa_triggers.txt", source / "common/script_values/rqa_values.txt",
             source / "common/decision_group_types/rqa_decision_group_types.txt", source / "events/rqa_events.txt",
             *sorted((source / "localization").rglob("*.yml"))]
    prep.copy_files(source, output, files)
    prep.write_script(output, "common/script_values/rqa_values.txt",
                      f"# External acceptance-only timer compression: production remains 1825 days.\nrmtm_recent_independence_duration_days = {duration}\n")
    body, proof = prep.decision_effect(repo, "mod_reclaim_the_motherland", "common/decisions/rmtm_restoration_decisions.txt", "rmtm_claim_restoration_decision")
    prep.write_script(output, "common/scripted_effects/rqa120_production_effects.txt", f"# Exact production decision-effect excerpt; UI/validity is not executed.\nrqa120_production_restoration_effect = {{\n{body}\n}}\n")
    prep.write_script(output, "common/on_action/rqa120_on_actions.txt", START)
    prep.write_script(output, "events/rqa120_events.txt", events(ui_checkpoints))
    if ui_checkpoints:
        prep.write_script(output, "common/decisions/rqa120_decisions.txt", CONTINUE)
        for language, title, confirm, description in (
            ("english", "Continue RMTM Core Acceptance", "Continue with the succession", "Observe the ministry budget and offer acceptance reasons first. Released targets: [ROOT.Var('rqa_vassalization_target_a').Char.GetShortUIName] and [ROOT.Var('rqa_vassalization_target_b').Char.GetShortUIName]. Continue after capturing the UI."),
            ("simp_chinese", "继续重整河山核心验收", "继续继承验收", "先查看三省六部预算与提议附庸的接受理由。已释放目标：[ROOT.Var('rqa_vassalization_target_a').Char.GetShortUIName]、[ROOT.Var('rqa_vassalization_target_b').Char.GetShortUIName]。完成界面取证后继续。"),
        ):
            loc = f'l_{language}:\n rqa120_continue_decision:0 "{title}"\n rqa120_continue_decision_desc:0 "{description}"\n rqa120_continue_decision_tooltip:0 "{title}"\n rqa120_continue_decision_confirm:0 "{confirm}"\n'
            prep.write_script(output, f"localization/{language}/rqa120_l_{language}.yml", loc)
    markers = prep.required_markers(repo / "tools/run_reclaim_the_motherland_acceptance.py")
    markers += ["RQA120: TEST BEGIN engine_startup", "RQA120: TEST PASS later_ministry_budget_gate",
                "RQA120: TEST PASS restoration_later_title_unheld", "RQA120: TEST DONE core"]
    if ui_checkpoints:
        markers.append("RQA120: TEST READY ui_after_chaos")
    return prep.finish_receipt(repo, source, output, files, {
        "product":"mod_reclaim_the_motherland", "ui_checkpoints":ui_checkpoints,
        "bookmark":"1066-09-15; begin as any human ruler except the Song emperor",
        "entry":"on_game_start_after_lobby -> rqa120.1 -> daily hidden rqa120.2; successor driver is explicitly scheduled before predecessor death",
        "expected_game_days":duration + 5, "max_game_days":120,
        "game_rules":{"rmtm_hegemon_fate":"rmtm_reclaim_the_motherland", "rmtm_pro_hegemon_choice":"rmtm_divided_hearts"},
        "required_markers":markers, "reject_markers":["RQA: TEST FAIL", "RQA120: TEST FAIL"],
        "production_effect_projections":[proof],
        "timer_compression":{"production_days":1825, "prepared_fixture_days":duration, "reason":"preserve recent independence through the daily driver, then observe actual engine expiry"},
        "coverage":"Existing production shattering/offer interaction/succession/restoration consequences and ministry entitlement/budget flags. Government budget UI, numeric acceptance reasons and production decision clicks remain separate UI checks.",
        "ui_steps":["Close the native Chaos notification to allow time to advance.",
                    "At READY ui_after_chaos pause, inspect Later title empty de jure and retained personal/loyal realm.",
                    "Open Three Departments and Six Ministries; capture nine incumbents and the budget controls.",
                    "Use the target names in Continue RMTM Core Acceptance to open the real offer-vassalization dialog; capture recent independence -50, fixed ordinary rank +10 when difference >1, and absence of celestial/hegemony perks.",
                    "Click the fixture Continue decision after UI capture; close informational events as needed; advance until core DONE.",
                    "In an additional UI attempt inspect the production restoration decision validity and confirmation at its threshold state."],
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ui-checkpoints", action="store_true")
    parser.add_argument("--compressed-days", type=int, default=14)
    args = parser.parse_args()
    receipt = prepare(args.repo, args.output, args.ui_checkpoints, args.compressed_days)
    print(json.dumps({"prepared_fixture":receipt["prepared_fixture"], "runtime_status":"NOT_RUN", "ui_checkpoints":args.ui_checkpoints}))


if __name__ == "__main__":
    main()
