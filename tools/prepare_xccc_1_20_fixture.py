"""Prepare XCCC scripted entry plus real production event choice for CK3 1.20."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from fixture_engine_prepare import checked_output, copy_files, decision_effect, finish_receipt, replace_once, required_markers, write_script

ON_ACTION = '''on_game_start_after_lobby = {
    on_actions = { xca120_start }
}

xca120_start = {
    effect = { random_player = { trigger_event = { id = xca120.1 } } }
}
'''
EVENTS = '''namespace = xca120

xca120.1 = {
    type = character_event
    hidden = yes
    immediate = {
        debug_log = "XCA120: TEST BEGIN engine_startup"
        add_character_flag = xca_initialize_pending
        xca_initialize_effect = yes
        character:han_8052 = { trigger_event = { id = xca120.2 days = 1 } }
    }
}

xca120.2 = {
    type = character_event
    hidden = yes
    immediate = {
        xca_setup_effect = yes
        if = {
            limit = { exists = scope:xca_official }
            scope:xca_official = { trigger_event = { id = xca120.3 days = 1 } }
        }
        else = { debug_log = "XCA120: TEST FAIL official_target_unavailable" }
    }
}

xca120.3 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                is_ai = no
                is_landed = yes
                is_independent_ruler = no
                government_has_flag = government_has_merit
                has_tgp_dlc_trigger = yes
                is_capable_adult = yes
                is_imprisoned = no
                is_at_war = no
                NOT = { has_character_flag = xccc_never_corrupt }
                has_character_flag = xca_verify_policy_pending
            }
            # Fixture supplies a clean choice prestate; the actual product event
            # must apply the selected trait. No PASS postcondition is supplied.
            remove_trait = xccc_corruption_1
            remove_trait = xccc_corruption_2
            remove_trait = xccc_corruption_3
            remove_trait = xccc_corruption_4
            debug_log = "XCA120: TEST PASS production_decision_eligibility"
            debug_log = "XCA120: TEST READY production_corruption_event"
__PRODUCTION_EFFECT__
            set_variable = { name = xca120_choice_wait value = 0 }
            trigger_event = { id = xca120.4 days = 1 }
        }
        else = { debug_log = "XCA120: TEST FAIL production_decision_eligibility" }
    }
}

xca120.4 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = { has_character_flag = xca_verify_policy_pending has_trait = xccc_corruption_4 }
            xca_verify_policy_effect = yes
        }
        else_if = {
            limit = { has_character_flag = xca_verify_policy_pending var:xca120_choice_wait < 10 }
            change_variable = { name = xca120_choice_wait add = 1 }
            trigger_event = { id = xca120.4 days = 1 }
        }
        else = { debug_log = "XCA120: TEST FAIL production_choice_timeout" }
    }
}
'''

def prepare(repo: Path, output: Path) -> dict:
    repo, output = checked_output(repo, output)
    source = repo / "tools/fixtures/celestial_commerce_corruption_acceptance"
    files = sorted(path for path in source.rglob("*") if path.is_file()
                   and (path.name == "descriptor.mod" or path.relative_to(source).parts[0] == "localization"
                        or path.relative_to(source).parts[:2] == ("common", "scripted_effects")))
    copy_files(source, output, files)
    effects = (source / "common/scripted_effects/xca_effects.txt").read_text(encoding="utf-8-sig")
    old = "XCA: TEST PASS production_decision_event_round_trip"
    new = "XCA: TEST PASS scripted_decision_effect_event_result"
    effects = replace_once(effects, old, new)
    write_script(output, "common/scripted_effects/xca_effects.txt", effects)
    body, provenance = decision_effect(repo, "mod_celestial_commerce_corruption",
                                       "common/decisions/xccc_corruption_decision.txt", "xccc_corruption_policy_decision")
    write_script(output, "common/on_action/xca120_on_actions.txt", ON_ACTION)
    write_script(output, "events/xca120_events.txt", EVENTS.replace("__PRODUCTION_EFFECT__", "\n".join("            " + line for line in body.splitlines())))
    markers = [new if marker == old else marker for marker in required_markers(repo / "tools/run_celestial_commerce_corruption_acceptance.py")]
    return finish_receipt(repo, source, output, files, {
        "product": "mod_celestial_commerce_corruption", "mode": "scripted-decision-entry-real-event-choice",
        "entry": "post-lobby -> xca_initialize_effect -> Song at D1 xca_setup_effect -> official at D2 production decision effect -> actual xccc.1001 option -> original verifier",
        "required_markers": ["XCA120: TEST BEGIN engine_startup", "XCA120: TEST PASS production_decision_eligibility", "XCA120: TEST READY production_corruption_event", *markers],
        "rules": "vanilla declared defaults; 1066 ordinary player outside Song; Song han_8052 initially AI; TGP runtime DLC required",
        "production_decision_effect": provenance,
        "production_builder": "tools/build_celestial_commerce_corruption_release.py",
        "production_government_contract": "Use current exact 1.20 full celestial government + sole barter=yes; obligations unchanged. Existing static contract remains authoritative, not rewritten by fixture.",
        "real_choice": "Inspect actual xccc.1001 instance and enabled option named xccc.1001.d (fourth tier); select via UI or existing native event-option tool. Advance one day for original trait + 0.75-0.25=0.50 verification.",
        "marker_policy": "Each required marker once; no XCA or XCA120 TEST FAIL. Eligibility failure is a fixture precondition until actual state is audited.",
        "ui_not_executed_by_fixture": ["production decision opening/confirm", "three-year decision cooldown", "all other tax-tier UI choices"],
        "player_switch_policy": "Actual scripted player changes may be observed as played_character_changed terminal by native one-life driver; preserve production policy.",
    })

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = prepare(args.repo, args.output)
    print(json.dumps({"prepared_fixture": receipt["prepared_fixture"], "runtime_status": "NOT_RUN"}))

if __name__ == "__main__":
    main()
