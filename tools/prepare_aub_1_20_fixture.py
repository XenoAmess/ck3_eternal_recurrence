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


def _validate_florin_gui_observer(source: Path) -> None:
    """Reject preparation that can operate production, resources or queues."""
    def inspect(block: Block, *, effects: bool = False) -> None:
        for entry in block.entries:
            key = entry.key
            controls = {"if", "else_if", "else", "limit", "random_player", "set_variable",
                        "trigger_event", "debug_log", "name", "effect", "hidden_effect", "immediate"}
            own_effect = key.startswith("aubgu_") and key.endswith("_effect")
            if effects and key not in controls and not own_effect:
                raise ValueError("GUI observer effect body contains an unreviewed operation")
            if key.startswith(("add_", "remove_", "change_", "set_")):
                if key != "set_variable" or not isinstance(entry.value, Block):
                    raise ValueError("GUI observer cannot mutate production or resource state")
                names = [item.value for item in entry.value.entries if item.key == "name"]
                if len(names) != 1 or not isinstance(names[0], str) or not names[0].startswith("aubgu_"):
                    raise ValueError("GUI observer may write only its aubgu-owned variables")
            if key.endswith("_effect") and key != "hidden_effect" and not key.startswith("aubgu_"):
                raise ValueError("GUI observer cannot call a production effect")
            if key == "trigger_event":
                if not isinstance(entry.value, Block):
                    raise ValueError("GUI observer event references must be explicit untimed blocks")
                ids = [item.value for item in entry.value.entries if item.key == "id"]
                if len(ids) != 1 or not isinstance(ids[0], str) or not re.fullmatch(r"aubgu\.[0-9]{1,4}", ids[0]):
                    raise ValueError("GUI observer cannot dispatch a production or foreign event")
                if any(item.key != "id" for item in entry.value.entries):
                    raise ValueError("GUI observer cannot schedule delayed events")
            if isinstance(entry.value, Block):
                child_effects = key in {"effect", "hidden_effect", "immediate", "option"} or own_effect
                child_effects = child_effects or (effects and key in {"if", "else_if", "else", "random_player"})
                inspect(entry.value, effects=child_effects)
    for path in sorted(source.rglob("*.txt")):
        inspect(parse_clausewitz(path.read_text(encoding="utf-8-sig")))


def prepare_gui(repo: Path, output: Path) -> Path:
    _validate_florin_gui_observer(repo / "tools/fixtures/auto_upgrade_buildings_florin_gui")
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_gui",
        contract="aub_florin_gui.json", case_id="production-decision-gui-1210",
        mode="florin-paused-production-gui-observer-only",
        entry="on_game_start_after_lobby -> actual Robert1128 disabled baseline -> known800 -> actual production Enable/observer810 -> actual Disable/observer820 -> same-day actual reenable/observer830 -> actual finalDisable/observer840; failedreadback -> known900",
        advance="Zero natural days throughout all business. The1-day case envelope never permits resuming to production day1; every observer requires exact baseline date/resources. Keep known windows and actual GUI actions manually paused; no manual SAVE or automatic unknown event choice.",
        rules="Fresh1066 Robert1128 alive/human and initial four production flags absent. Fixture is read-only for all production state, resources and queues; only aubgu-owned phase/baseline variables change. Actual production six-option/hover/default and representative preview selections, confirmation, Enable/Disable and same-day availability require independent Root GUI evidence. Two real default Enable/Disable cycles leave final disabled and legitimately preserve any queued day1 seeds until normal close; no seed/global cleanup or internal queue count claim. Original actual_decision_cooldown_readback remains mandatory as same-paused-day immediate re-enable behavior, because production source has no explicit cooldown field. No numeric getter, money/domain/succession or full-product credit.")


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
        entry="on_game_start_after_lobby -> normal Robert1128 -> granted c_pagan to burman002 -> actual player/Mandala government and100000gold -> explicit b_popa ownership and native herder9551 isolation -> aubma.2 day1 -> aubma.3 day2 -> one real auto_build.0004 -> aubma.800; preparation failure -> actual-player visible aubma.801",
        advance="At most2natural days for the two existing one-day preparation events; no extension for a prior failure. Stop on exact DONE or visible failure801. No manual Save or prepared effects credited as upgrades.",
        rules="1066 normal Robert1128 selection. Official grant of c_pagan to originally unlanded adult burman002, actual player switch/Mandala government and100000gold precede Native queries. Explicit b_popa title grant to the same payer follows government setup; only ancillary9551 is converted to native herder holding. Actual direct domain must be exactly9550+9551, while the full production holding/lease/construction/quota filter must qualify exactly9550; owner/title/lease/auto-created herder primary and inventory of excluded9551 read back before and after the scan. This corrects failed single-direct assumptions without dropping the one-scannable-province requirement. Preserve Pagan native holding03, Mandala03 and initialized great mandala_capital02; remove five unrelated districts via vanilla remove_district_type, add ordinary shrine1 only and join province culture high-medieval. Complete six-object/three-primary Pagan inventory includes target two districts5/2 and third great02/no03, unchanged across the scan. All four Native target gates precede one real0004; finite observations never dump saved targets. Great02->03 exists but is excluded as great_project. Preparation failures immediately show known Realm801 without more day events. Exact personal charge/count4; main03->04 is a terminal-edge representative and viharas2->3 differs from historical01->02. No primary forcing in either target district, direct chain call, terminal no-cascade or full product/publication credit.")


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


def prepare_duchy(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_duchy",
        contract="aub_florin_duchy.json", case_id="duchy-primary-1210",
        mode="florin-gui-timed-duchy-primary",
        entry="on_game_start_after_lobby -> aubd.1 -> known start closes at paused day0 -> actual Alt+S Trani duchy slot, military district selection and enabled stock Construct/Queue -> aubd.10 observes active/no-primary day1 -> aubd.20 -> own started -> aubd.30 daily<=14 -> aubd.100 -> own READY -> aubd.110 -> aubd.800; failure/partial -> aubd.900",
        advance="Keep day0 paused after the known start option; retain actual GUI military district/CanConstruct/Queue/active progress before resuming. At most22 natural days including day1 observation and21 completion polls; R22 actual GUI displayed18days with the unchanged -0.99 modifier, not a proven engine minimum. Stop on known DONE/failure/partial or unknown stock event; no manual SAVE or credited preparation.",
        rules="Fresh1066 Robert1128; actual owned/unleased Trani2619, c_apulia+d_apulia, independence and native holdingII required. Day0 province Burhs/castle_baileys, funds and character district_build_speed preparation precede actual stock-GUI military_duchy_capital_district first construction. No script first-tier can_start/start, ordinary/resource clearing or forced primary. Day1 only observes actual active construction without primary01; true timed completion and its actual District still require Native02. Freeze resources after all preparation, then one existing primary01->02 production chain with exact personal gold100/count1 and unchanged other resources. R19/R20 script-first-tier refusals remain distinct historical failures; no archery/full-scan or whole-product credit.")


def prepare_succession(repo: Path, output: Path) -> Path:
    return _prepare_florin_scene(repo, output, fixture="auto_upgrade_buildings_florin_succession",
        contract="aub_florin_succession.json", case_id="succession-bounded-1210",
        mode="florin-bounded-actual-succession",
        entry="on_game_start_after_lobby -> aubs.1 PREP -> known800 -> one initial production start and real death -> original Continue as sampled heir -> day2 known810/manual0004 -> known820/rearm/two helper reentries -> known825 -> daily3..16 -> day17 known830 or partial831; failure901",
        advance="At most17natural days from the actual initial seed. Preserve ordinary campaign lifecycle; actual default Continue, modal clearance, exact heir and date separately evidenced through authorized sharedGUI. Stop on known DONE/failure/partial or unknown stock interruption. No SAVE or old-seed deletion.",
        rules="Normal1066 Robert1128 remains original player. Formal grants, Native CastleII->III preparation and ordinary garrisonI require actual single owned/unleased Trani2619, closed2built/1primary inventory and sampled living unlanded heir. Preseed opposite heir policies; unchanged production on_death must inherit enabled/personal-only/pause and reuse original queued seed. First auto1->2, paused manual2->3 exact120/count1, disclosed ordinary rearm and original second auto1->2. Exact15-day qualification requires actual callback payer/source/count/dates1/2/16; missing callbacks give partial, never loopPASS. Event queue cardinality, all future cadence, full matrix and publication are not proven.")


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
    parser.add_argument("--scenario", choices=("core", "florin-gui", "florin-probe", "florin-money", "florin-ordinary", "florin-mandala", "florin-holdings", "florin-special", "florin-duchy", "florin-succession"), default="core")
    args = parser.parse_args()
    if args.scenario == "florin-gui":
        output = prepare_gui(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
    if args.scenario == "florin-succession":
        output = prepare_succession(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
    if args.scenario == "florin-duchy":
        output = prepare_duchy(args.repo, args.output)
        print(json.dumps({"prepared_fixture": str(output), "runtime_status": "NOT_RUN"}))
        return
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
