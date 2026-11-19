"""Prepare the existing AUB core engine matrix for CK3 1.20; never launch."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from extract_auto_upgrade_buildings import Block, parse_clausewitz
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

def _validate_florin_event_ids(source: Path) -> None:
    """Reject IDs that the current engine refuses before materializing a scene."""
    pattern = re.compile(r"([A-Za-z_][A-Za-z_0-9]*)\.([0-9]+)")
    definitions: set[str] = set()

    def check_reference(block: Block) -> None:
        for entry in block.entries:
            if isinstance(entry.value, Block):
                check_reference(entry.value)
            elif entry.key == "id":
                if entry.value is None:
                    raise ValueError("Invalid Florin event ID: missing scalar")
                match = pattern.fullmatch(entry.value)
                if match is not None and not 1 <= int(match[2]) < 10000:
                    raise ValueError(f"Invalid Florin event ID: {entry.value}")

    for path in sorted(source.rglob("*.txt")):
        block = parse_clausewitz(path.read_text(encoding="utf-8-sig"))
        check_reference(block)
        if path.parent != source / "events":
            continue
        namespaces = [entry.value for entry in block.entries if entry.key == "namespace"]
        if len(namespaces) != 1 or not isinstance(namespaces[0], str):
            raise ValueError(f"Exactly one event namespace required: {path}")
        for entry in block.entries:
            if entry.key == "namespace":
                continue
            match = pattern.fullmatch(entry.key)
            if match is None or match[1] != namespaces[0] or not 1 <= int(match[2]) < 10000:
                raise ValueError(f"Invalid Florin event ID: {entry.key}")
            if entry.key in definitions:
                raise ValueError(f"Duplicate Florin event ID: {entry.key}")
            definitions.add(entry.key)
            if isinstance(entry.value, Block):
                fields = {field.key: field.value for field in entry.value.entries}
                if fields.get("type") == "character_event" and fields.get("hidden") != "yes":
                    theme = fields.get("theme")
                    if not isinstance(theme, str) or not theme:
                        raise ValueError(f"Visible Florin character event requires a theme: {entry.key}")


def _prepare_florin_scene(repo: Path, output: Path, *, fixture: str, contract: str,
                          case_id: str, mode: str, entry: str, advance: str,
                          rules: str = "1066 Robert of Apulia, historical character1128, original castle capital; vanilla rules.") -> Path:
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
    _validate_florin_event_ids(source)
    for path in files:
        if path.suffix == ".mod":
            copy_files(source, output, [path])
        else:
            write_script(output, path.relative_to(source).as_posix(), path.read_text(encoding="utf-8-sig"))
    receipt: dict[str, object] = {
        "product": "mod_auto_upgrade_buildings", "mode": mode,
        "required_markers": markers,
        "entry": entry,
        "rules": rules,
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
        entry="Actual production enable UI with treasury-first/continue -> isolated fixture start decision -> aubt.900 (original aubt.0) -> original aubt.1..6 money/domain events",
        advance="Keep paused for actual production selection and fixture start; then at most180natural days. Stop on failure, interruption, or exact DONE; no manual Save.",
        rules="1066 select Robert1128 normally; fixture switches current player to landed Roger1132 and uses the official create/becomes_independent/resolve transaction before any day or government change. Actual player/top_liege, Catholic faith, owned castle and existing head bull cooldowns must read back. Independent/has_treasury must remain true after government change, outside unrelated merit-career vassal dispatch. Robert intro remains AI. Vanilla game rules and original17 money predicates unchanged; no old actor qualification reused.")


def prepare_ordinary(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_ordinary",
        contract="aub_florin_ordinary.json", case_id="ordinary-matrix-1210",
        mode="florin-original-ordinary-building-quota-matrix",
        entry="on_game_start_after_lobby -> actual Roger1132 and independence -> aubq.1 -> known visible aubq.800",
        advance="Synchronous paused startup matrix; no calendar resumption needed. At most1natural day if required by startup; no manual Save.",
        rules="1066 normal Robert1128 selection; official switch/independence to landed Roger1132 before any day. Explicit fixture personal-only baseline, then native-qualified District main/quota/negative/oath/city matrix. Production GUI is separate coverage; no credited preparation effects.")


def prepare_mandala(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_mandala",
        contract="aub_florin_mandala.json", case_id="mandala-matrix-1210",
        mode="florin-four-mandala-production-edges",
        entry="on_game_start_after_lobby -> normal Robert1128 -> granted c_pagan to burman002 -> return b_popa9551 to burman001 -> actual player switch and100000gold -> aubma.2 day1 -> aubma.3 day2 -> one real auto_build.0004 -> aubma.800; any preparation failure -> actual-player visible aubma.801",
        advance="At most2natural days for the two existing one-day preparation events; no extension for a prior failure. Stop on exact DONE or visible failure801. No manual Save or prepared effects credited as upgrades.",
        rules="1066 normal Robert1128 selection. Official granted title transactions give existing Pagan county/province9550 to originally unlanded adult burman002 and return extra Popa9551/barony b_popa to burman001; then set_player_character, explicit Mandala government and100000gold before any Native target query. Actual player, owner, returned Popa and sole direct province remain required after an event boundary. Preserve native holding03, Mandala03 and the initialized great district mandala_capital02; remove five declared unrelated districts through vanilla remove_district_type, add ordinary shrine1 only, and join province culture high-medieval. Require the complete six-object/three-primary province inventory, including five buildings/two primaries in the two target districts and actual great02/no03 in the third district, before and after the scan. All four native target gates must read back before one production0004; finite precondition observations never dump all saved targets per building. The snapshot excludes the great02->03 edge as great_project, not as no-next-building. Preparation failures immediately route the actual player to known visible Realm event801 with no further day scheduling. Exact personal charge and count4; main03->04 is a terminal-edge representative, viharas2->3 differs from historical01->02. No primary downgrade/add/remove, direct chain call, terminal no-cascade credit or full product/publication credit.")


def prepare_holdings(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_holdings",
        contract="aub_florin_holdings.json", case_id="holding-types-1210",
        mode="florin-four-holding-type-cells",
        entry="on_game_start_after_lobby -> actual Roger1132 and independence -> aube.1 -> known visible aube.800",
        advance="Synchronous paused startup; at most1natural day if required by startup. No manual Save.",
        rules="1066 normal Robert1128 selection and official switch/independence to Roger1132. Actual converted native primary sources, true government/faith/rite/ownership/native target readbacks and exact production-chain payments required. Current lodge1->2 replaces legacy longhouses. Every actual direct province is converted and read before real character0004 nomad/herder exclusion scans. No primary forcing, credited preparation, GUI policy, Native ABI or full product acceptance.")


def prepare_special(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_special",
        contract="aub_florin_special.json", case_id="special-owned-1210",
        mode="florin-owned-special-gold-cell",
        entry="on_game_start_after_lobby -> actual Roger1132 -> official county/barony grant -> aubsp.2 day1 -> known visible aubsp.800",
        advance="At most1natural day after official title transfer. Success and every preparation failure immediately show known completion; no manual Save.",
        rules="Normal1066 Robert1128 selection and official switch/independence to Roger1132. Existing c_jingzhao and b_zhouzhi transferred by stock granted transaction, then actual player/independence/direct unleased10148 readback. Native CastleII-or-higher and current existing special-marketI preserved. Province innovation_currency_02 precedes full Native marketII gate. Actual special District chain and precise gold800/count1; no foreign payer, special slot/source force, full product or GUI policy credit.")


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
    parser.add_argument("--scenario", choices=("core", "florin-probe", "florin-money", "florin-ordinary", "florin-mandala", "florin-holdings", "florin-special"), default="core")
    args = parser.parse_args()
    if args.scenario == "florin-special":
        output = prepare_special(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
    if args.scenario == "florin-holdings":
        output = prepare_holdings(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
    if args.scenario == "florin-mandala":
        output = prepare_mandala(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
    if args.scenario == "florin-ordinary":
        output = prepare_ordinary(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
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
