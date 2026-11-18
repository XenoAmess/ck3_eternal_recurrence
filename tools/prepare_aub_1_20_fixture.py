"""Prepare the existing AUB core engine matrix for CK3 1.20; never launch."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from fixture_engine_prepare import checked_output, copy_files, engine_identity, finish_receipt, replace_once, required_markers, write_script

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

def _prepare_florin_scene(repo: Path, output: Path, *, fixture: str, contract: str,
                          case_id: str, mode: str, entry: str, advance: str) -> Path:
    repo, output = checked_output(repo, output)
    if engine_identity(repo)["game_version"] != "1.21.0":
        raise ValueError("Florin scene requires exact CK3 1.21.0")
    source = repo / "tools/fixtures" / fixture
    files = sorted(path for path in source.rglob("*") if path.is_file())
    raw: object = json.loads((repo / "tools/ck3_mod_acceptance_cases" / contract).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("product") != "auto-upgrade-buildings" or raw.get("case") != case_id:
        raise ValueError("Florin scene case identity differs")
    scope = raw.get("scope")
    raw_markers = raw.get("required_markers")
    if not isinstance(scope, str) or not isinstance(raw_markers, list) or not raw_markers or raw.get("full_product_pass_from_cell") is not False:
        raise ValueError("Florin probe case scope or markers differ")
    markers: list[str] = []
    for marker in raw_markers:
        if not isinstance(marker, str) or not marker:
            raise ValueError("Florin scene markers must be nonempty strings")
        markers.append(marker)
    if len(markers) != len(set(markers)):
        raise ValueError("Florin scene markers must be unique")
    if not files or any(path.suffix not in {".mod", ".txt", ".yml"} for path in files):
        raise ValueError("Florin fixture must contain only declared text assets")
    for path in files:
        if path.suffix == ".mod":
            copy_files(source, output, [path])
        else:
            write_script(output, path.relative_to(source).as_posix(), path.read_text(encoding="utf-8-sig"))
    receipt: dict[str, object] = {
        "product": "mod_auto_upgrade_buildings", "mode": mode,
        "required_markers": markers,
        "entry": entry,
        "rules": "1066 Robert of Apulia, historical character1128, original castle capital; vanilla rules.",
        "scope": scope, "full_product_pass_from_cell": False,
        "advance_policy": advance,
    }
    finish_receipt(repo, source, output, files, receipt)
    return output


def prepare_probe(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_probe",
        contract="aub_florin_probe.json", case_id="district-probe-1210",
        mode="florin-district-native-probe",
        entry="on_game_start_after_lobby -> random_player -> aubf.1",
        advance="Zero-day synchronous probe; no manual Save; at most one natural day if required by startup.")


def prepare_money(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_money",
        contract="aub_florin_money.json", case_id="money-domain-1210",
        mode="florin-original-money-domain-matrix",
        entry="Actual production enable UI with treasury-first/continue -> isolated fixture start decision -> original aubt.0..6 money/domain events",
        advance="Keep paused for actual production selection and fixture start; then at most180natural days. Stop on failure, interruption, or exact DONE; no manual Save.")


def prepare(repo: Path, output: Path) -> dict[str, object]:
    repo, output = checked_output(repo, output)
    if engine_identity(repo)["game_version"].startswith("1.21."):
        raise ValueError("Full legacy AUB fixture is not migrated to Florin; choose an explicit partial Florin scene")
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
    receipt: dict[str, object] = {
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
    }
    finish_receipt(repo, source, output, files, receipt)
    return receipt

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", choices=("core", "florin-probe", "florin-money"), default="core")
    args = parser.parse_args()
    if args.scenario == "florin-probe":
        output = prepare_probe(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
    if args.scenario == "florin-money":
        output = prepare_money(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
    receipt = prepare(args.repo, args.output)
    print(json.dumps({"prepared_fixture": receipt["prepared_fixture"], "runtime_status": "NOT_RUN"}))

if __name__ == "__main__":
    main()
