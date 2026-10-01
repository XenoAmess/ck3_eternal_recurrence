"""Prepare the existing AUB core engine matrix for CK3 1.20; never launch."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from fixture_engine_prepare import checked_output, copy_files, finish_receipt, replace_once, required_markers, write_script

OLD_MARKER = "AUBT: TEST PASS native_decision_priority_continue_selection"
NEW_MARKER = "AUBT: TEST PASS scripted_policy_baseline_seeded"
ON_ACTION = '''on_game_start_after_lobby = {
    on_actions = { aubt120_start }
}

aubt120_start = {
    effect = {
        random_player = {
            debug_log = "AUBT120: TEST BEGIN engine_startup"
            trigger_event = { id = aubt.0 days = 1 }
        }
    }
}
'''

def prepare(repo: Path, output: Path) -> dict:
    repo, output = checked_output(repo, output)
    source = repo / "tools/fixtures/auto_upgrade_buildings_acceptance"
    files = sorted(path for path in source.rglob("*") if path.is_file())
    copy_files(source, output, files)
    events_path = source / "events/aubt_events.txt"
    events = events_path.read_text(encoding="utf-8-sig")
    events = replace_once(events, OLD_MARKER, NEW_MARKER)
    events = replace_once(events, "AUBT: TEST FAIL native_decision_priority_continue_selection",
                          "AUBT: TEST FAIL scripted_policy_baseline_seeded")
    write_script(output, "events/aubt_events.txt", events)
    write_script(output, "common/on_action/aubt_on_actions.txt", ON_ACTION)
    markers = [NEW_MARKER if marker == OLD_MARKER else marker
               for marker in required_markers(repo / "tools/run_auto_upgrade_buildings_acceptance.py")]
    return finish_receipt(repo, source, output, files, {
        "product": "mod_auto_upgrade_buildings", "mode": "scripted-core-engine",
        "entry": "on_game_start_after_lobby -> aubt120_start -> aubt.0 at day 1 -> existing matrix",
        "rules": "vanilla declared defaults; no AUB game rule; choose an ordinary 1066 ruler (Heinrich IV has character ID 1316)",
        "required_markers": ["AUBT120: TEST BEGIN engine_startup", *markers],
        "marker_policy": "Each required marker exactly once; no AUBT or AUBT120 TEST FAIL. Succession requires actual original Continue as heir UI before aubt.12.",
        "production_builder": "tools/build_auto_upgrade_buildings_release.py",
        "production_graph": {"definitions": 989, "edges": 605, "chains": 165},
        "coverage": "Existing funds/domain/quota/main/ordinary/special/tribal/Mandala/negative-gate/succession representative matrix; no all-165-chains live claim.",
        "ui_not_executed_by_fixture": ["enable/disable decision surface", "decision cooldown", "original Continue as heir"],
        "advance_policy": "Advance until exact markers, retaining date_raw and event interruptions; do not equate submitted time-control with completed matrix.",
        "preserved_assertions": "All original event conditions and production calls retained; only startup dispatch and misleading decision marker label changed.",
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
