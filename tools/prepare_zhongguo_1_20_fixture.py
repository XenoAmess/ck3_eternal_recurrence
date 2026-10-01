"""Prepare the existing 361 assessment/board/Jingcha core for CK3 1.20."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

from fixture_engine_prepare import checked_output, copy_files, finish_receipt, write_script

ON_ACTION = '''on_game_start_after_lobby = {
    on_actions = { zga120_start }
}

zga120_start = {
    effect = { random_player = { trigger_event = { id = zga120.1 } } }
}
'''

EVENTS = '''namespace = zga120

zga120.1 = {
    type = character_event
    hidden = yes
    immediate = {
        debug_log = "ZGA120: TEST BEGIN engine_startup"
        add_character_flag = zga_initialize_pending
        zga_initialize_effect = yes
        character:han_8052 = { trigger_event = { id = zga120.2 days = 1 } }
    }
}

zga120.2 = {
    type = character_event
    hidden = yes
    immediate = {
        zga_prepare_player_review_effect = yes
        debug_log = "ZGA120: TEST READY production_calibration"
        set_variable = { name = zga120_board_wait value = 0 }
        trigger_event = { id = zga120.3 days = 1 }
    }
}

zga120.3 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                has_character_flag = zga_waiting_for_scoreboard
                has_variable = zg361_sb_m_01_char
            }
            zga_verify_player_review_effect = yes
            debug_log = "ZGA120: TEST PASS scripted_review_scoreboard_verified"
            trigger_event = { id = zga120.4 days = 11 }
        }
        else_if = {
            limit = { var:zga120_board_wait < 30 }
            change_variable = { name = zga120_board_wait add = 1 }
            trigger_event = { id = zga120.3 days = 1 }
        }
        else = { debug_log = "ZGA120: TEST FAIL calibration_or_scoreboard_timeout" }
    }
}

zga120.4 = {
    type = character_event
    hidden = yes
    immediate = {
        if = {
            limit = {
                this = character:han_8052
                has_character_flag = zga_player_review_verified
                has_character_flag = zga_jingcha_mandate_issued
            }
            debug_log = "ZGA120: TEST PASS scripted_jingcha_dispatch_state"
            debug_log = "ZGA120: TEST DONE core_engine"
        }
        else = { debug_log = "ZGA120: TEST FAIL scripted_jingcha_dispatch_state" }
    }
}
'''


def core_markers(runner: Path) -> list[str]:
    for node in ast.parse(runner.read_text(encoding="utf-8-sig")).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "REQUIRED_FIXTURE_MARKERS"
            for target in node.targets
        ):
            return list(ast.literal_eval(node.value))
    raise ValueError("existing 361 core marker inventory is unavailable")


def prepare(repo: Path, output: Path) -> dict:
    repo, output = checked_output(repo, output)
    source = repo / "tools/fixtures/zg361_acceptance"
    files = sorted(
        path for path in source.rglob("*") if path.is_file()
        and (path.name == "descriptor.mod"
             or path.relative_to(source).parts[0] in {"localization", "events"}
             or path.relative_to(source).parts[:2] in {
                 ("common", "scripted_effects"), ("common", "modifiers")})
    )
    copy_files(source, output, files)
    write_script(output, "common/on_action/zga120_on_actions.txt", ON_ACTION)
    write_script(output, "events/zga120_events.txt", EVENTS)
    markers = core_markers(repo / "tools/run_zhongguo_acceptance.py")
    cases = [f"ZGA: MECHANISM CASE PASS {number:03d}" for number in range(1, 362)]
    return finish_receipt(repo, source, output, files, {
        "product": "mod_zhongguo_style", "mode": "scripted-assessment-board-jingcha-core",
        "entry": "post-lobby initialize -> Song D1 original review preparation -> actual zg361.10.a -> original scoreboard verifier -> original D+10 Jingcha dispatcher",
        "required_markers": [
            "ZGA120: TEST BEGIN engine_startup",
            "ZGA120: TEST READY production_calibration",
            "ZGA120: TEST PASS scripted_review_scoreboard_verified",
            "ZGA120: TEST PASS scripted_jingcha_dispatch_state",
            "ZGA120: TEST DONE core_engine",
            "ZGA: TEST PASS clean_jingcha_dispatch_scheduled",
            "ZGA: TEST PASS jingcha_mandate_issued",
            "ZGA: TEST PASS clean_jingcha_dispatched", *markers, *cases,
        ],
        "required_product_markers_minimum": {
            "ZG361: annual review tick": 2,
            "ZG361: scoreboard published": 1,
            "ZG361M: REFERENCE CHARTER COMPLETE 361": 2,
        },
        "rules": "vanilla declared defaults including zg361_on and strict bottom ratio; ordinary 1066 player outside Song; han_8052 initially AI",
        "marker_policy": "Each fixture marker once; no ZGA/ZGA120 TEST FAIL or ZGA MECHANISM CASE FAIL. Retain strict 23-person 7/14/2 and historical whitelist assertions unchanged; mismatch requires precondition/product audit, not fixture refresh.",
        "production_builder": "tools/build_mod_zhongguo_style_release.py",
        "real_choices": [
            "At actual zg361.10 instance select zg361.10.a direct publication; preserve event instance/option identity and fresh native revision or reviewed UI evidence.",
            "At actual zg361.40 instance choose zg361.40.a to open the original free activity planner. Planner inspection/hosting/completion requires real UI; the script dispatcher marker does not prove these outcomes.",
        ],
        "advance_policy": "Advance one day at a time around calibration; pause after board verification for UI audit; Jingcha is due ten actual days after verification. The added core completion check is due one day later, so the real popup must be handled before reaching it.",
        "ui_not_executed_by_fixture": [
            "manual review decision and same-year decision surface",
            "scoreboard opening, tabs, rows, closing, ACL and low-resolution geometry",
            "Jingcha activity planner, host action, completion and refusal branches",
        ],
        "late_fixture_boundary": "Original Jingcha carrier still schedules the historical D+90 personal-result pending flag. No GUI observer is mounted to consume that flag, so personal-result and six-card promo chain are outside this core entry. Their original assertions are preserved in copied files without claiming execution.",
        "native_boundary": "Generic current-build map/event controls only; no old 1.19 Zhongguo named-widget ABI or automatic provider readiness change.",
        "baseline_model_audit": "Existing 52 failures plus one error in content/model audit remains recorded; this fixture neither refreshes that contract nor reclassifies it as new-version incompatibility.",
        "preserved_assertions": "All copied original effect, generated case, modifier and event bytes unchanged; additions are separate hidden startup/observation events.",
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
