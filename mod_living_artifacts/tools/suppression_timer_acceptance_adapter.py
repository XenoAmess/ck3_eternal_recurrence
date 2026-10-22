"""One ordinary paid suppression, renewal, expiry and restored monthly growth.

Session owns every native action, interruption and Save/Root exchange. The
existing typed historical checkpoint consumer is reused without running its
threshold scenario. This package never writes game state or loads another save.
"""
from __future__ import annotations

from datetime import date
import importlib
import json
from pathlib import Path
import sys
from typing import Literal, TypedDict

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import acceptance_adapter as core
import threshold_acceptance_adapter as historical
from acceptance_contract import CasePort, CheckResult, Frame, Object, Pin, array, field, integer, mapping, object_value, pin, read, require, text, utc_now, write_once
from checkpoint_callback import checked_pin, verify_readback
from checkpoint_producer import raw_object, stamp
from management_event_contract import source_option_index
from prepare_fixture import FixtureEmission, emit_fixture
from prepare_threshold_fixture import same_json, tree

CASE: Literal["suppression_timer"] = "suppression_timer"
CONTRACT_NAME = "suppression_timer.contract.json"
RESULT_NAME = "living-artifacts-suppression-timer-result.json"
CHECKS = ("TIMER-FIRST-PAID-90-DAYS", "TIMER-RENEW-ADDS-90-DAYS", "TIMER-OLD-EVENT-KEEPS-RENEWED-DEADLINE", "TIMER-NATURAL-EXPIRY", "TIMER-NEXT-MONTH-GROWTH")
SOURCES = ("suppression_timer_acceptance_adapter.py", "suppression_timer.registry.json", "acceptance_adapter.py", "acceptance_contract.py",
    "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py", "living_artifacts_content.py", "checkpoint_callback.py",
    "checkpoint_artifacts.py", "checkpoint_producer.py", "startup_actor_binding.py", "management_event_contract.py", "inventory_gui_contract.py",
    "native_interruption_contract.py", "threshold_acceptance_adapter.py", "prepare_threshold_fixture.py")


class TimerJournal(TypedDict):
    checkpoints: list[Pin]
    suppress: Pin | None
    renew: Pin | None
    native_records: dict[str, Pin]
    natural_records: dict[str, Pin]


class TimerResult(TypedDict):
    schema: Literal["living-artifacts-suppression-timer-result-v1"]
    product: Literal["living-artifacts"]
    case: Literal["suppression_timer"]
    run_id: str
    machine_id: str
    reviewer: str
    observed_at_utc: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    checks: list[CheckResult]
    journal: Pin
    error: str | None
    actual_natural_days: int
    actual_public_calls_budgeted: int
    actual_saved_observations: int
    original_action_unknown: bool
    case_contract_qualified: bool
    gui_contract_qualified: bool
    business_pass: Literal[False]
    product_release_pass: Literal[False]
    normal_close_owner: Literal["shared entry/CaseClient"]
    normal_close_pending: Literal[True]


def validate_contract(context: object) -> core.Contract:
    require(field(context, "product") == "living-artifacts" and field(context, "case") == CASE, "Select the actual suppression_timer case")
    config = mapping(field(context, "case_contract"), "timer contract")
    require(same_json(config, read(TOOLS / CONTRACT_NAME)), "Exact canonical timer contract required")
    integer(config["schema_version"], "timer schema", 1, 1)
    require(same_json(field(context, "case_spec"), read(TOOLS / "suppression_timer.registry.json")), "Exact standalone registry stanza required")
    spec = field(context, "case_spec")
    tools = {text(item, "tool") for item in array(field(spec, "required_mcp_tools"), "declared tools")}
    require(set(core.REQUIRED_TOOLS) <= tools, "Every existing Session tool must be declared")
    for key, value in core.REQUIRED_OPT_INS.items():
        require(field(spec, key) is value, "Existing native action opt-in missing")
    require(core.ITEM in array(field(spec, "opt_in_read_only_mcp_tools"), "read-only opt-ins"), "Independent native equipment read required")
    require(config["required_checks"] == list(CHECKS) and config["whole_product_acceptance_credit"] is False, "Scoped timer checks required")
    integer(config["maximum_checkpoints"], "Save cap", 7, 7)
    return core.Contract(integer(config["maximum_natural_days"], "day cap", 212, 212), integer(config["max_public_calls"], "call cap", 1200, 1200),
        integer(config["day_timeout_seconds"], "single-day timeout", 60, 60), CHECKS,
        tuple(text(item, "deferred") for item in array(config["deferred_checks"], "deferred checks")))


def prepare_case(context: object) -> Object:
    validate_contract(context)
    values = mapping(context, "preparation context")
    output = Path(text(field(values, "output"), "preparation output")).resolve()
    fixture = emit_fixture(output / "external-timer-fixture")
    root = Path(fixture["fixture_root"])
    product = Path(text(field(field(values, "case_inputs"), "product_dir"), "formal staging")).resolve()
    write_once(root / "_case_contract.json", {"product": "living-artifacts", "case": CASE, "config": field(values, "case_contract"),
        "fixture_emission": fixture, "caller_sources": {name: pin(TOOLS / name) for name in SOURCES}, "contract_source": pin(TOOLS / CONTRACT_NAME),
        "formal_files": tree(product), "business_pass": False})
    preparation = importlib.import_module("ck3_mod_acceptance_prepare")
    if not isinstance(preparation, core.Preparation):
        raise ValueError("Existing shared fixture preparation API required")
    prepared = object_value(preparation.materialize_fixture_profile(values, root, product, field(field(values, "case_inputs"), "plain_configuration")))
    return object_value({"startup": {"mode": "fixture", "state_dir": prepared["state_dir"], "fixture_start_policy": prepared["fixture_start_policy"]},
        "initial_plan": write_once(output / "initial-plan.json", {"steps": []}), "profile_preparation": prepared, "fixture_emission": fixture,
        "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False})


def prepared_sources(context: object, state: Path) -> tuple[Pin, ...]:
    validate_contract(context)
    require(isinstance(state, Path) and state.resolve() == Path(text(field(context, "state_dir"), "state")).resolve(), "Timer crossed allocated state")
    root = state / "profile/mod-content/fixture"
    manifest = read(root / "_case_contract.json")
    require(set(manifest) == {"product", "case", "config", "fixture_emission", "caller_sources", "contract_source", "formal_files", "business_pass"} and
        manifest["product"] == "living-artifacts" and manifest["case"] == CASE and manifest["business_pass"] is False and
        same_json(manifest["config"], field(context, "case_contract")), "Timer deployed contract differs")
    callers = mapping(manifest["caller_sources"], "source closure")
    require(set(callers) == set(SOURCES), "Timer caller closure differs")
    refs = [core._checked_pin(callers[name], "timer source", TOOLS / name) for name in SOURCES]
    refs.append(core._checked_pin(manifest["contract_source"], "timer contract", TOOLS / CONTRACT_NAME))
    emission = mapping(manifest["fixture_emission"], "unchanged core fixture")
    require(set(emission) == set(FixtureEmission.__required_keys__) and type(emission["schema_version"]) is int and emission["schema_version"] == 2 and
        emission["input_origin"] == "fixture_generated" and emission["business_acceptance"] == "NOT_ASSESSED" and emission["game_started"] is False,
        "Initial fixture cannot grant business credit")
    emitted = mapping(emission["files"], "fixture files")
    for deployed, originals, extra in ((root, emitted, {"_case_contract.json"}), (state / "profile/mod-content/product", mapping(manifest["formal_files"], "formal files"), set())):
        require(set(tree(deployed)) == set(originals) | extra, "Exact deployed input closure differs")
        for relative, raw in originals.items():
            require(not Path(relative).is_absolute() and ".." not in Path(relative).parts, "Input path escaped deployment")
            original = checked_pin(raw, "original input")
            copied = pin(deployed / relative)
            require((copied["bytes"], copied["sha256"]) == (original["bytes"], original["sha256"]), "Loaded input bytes differ")
            refs.append(copied)
    require(read(state / "profile/dlc_load.json") == {"enabled_mods": ["mod/product.mod", "mod/fixture.mod"], "disabled_dlcs": []}, "Only formal product and unchanged core fixture may mount")
    prepared_pin = checked_pin(field(read(state / "preparation.json"), "preparation"), "actual shared preparation")
    prepared = read(Path(prepared_pin["path"]))
    require(field(prepared, "schema") == "ck3-mod-acceptance-prepared-fixture-v1" and
        Path(text(field(prepared, "state_dir"), "prepared state")).resolve() == state.resolve(), "Shared preparation crossed schema/state")
    loaded = {"mod/product.mod", "mod/fixture.mod", "dlc_load.json"}
    loaded.update("mod-content/product/" + relative for relative in mapping(manifest["formal_files"], "formal closure"))
    loaded.update("mod-content/fixture/" + relative for relative in set(emitted) | {"_case_contract.json"})
    table = mapping(field(prepared, "files"), "shared source table")
    require(loaded <= set(table), "Shared preparation omits loaded timer inputs")
    refs.extend(core._checked_pin(table[relative], "loaded shared input", state / "profile" / relative) for relative in sorted(loaded))
    return (*refs, prepared_pin, pin(root / "_case_contract.json"), pin(state / "profile/dlc_load.json"))


def _value(observation: historical.ThresholdObservation, name: str) -> int | None:
    variable = observation.values.get(name)
    return None if variable is None else variable.integer_value(name)


def _last_call(session: core.Session) -> Pin:
    return pin(session.client.output / f"xalw-core-{session.sequence:04d}.actual-results.json")


def _observe(session: core.Session, target: str | None) -> tuple[historical.ThresholdObservation, Pin]:
    session.snapshot()
    original = session.last_native_record
    if original is None:
        raise ValueError("Original paused native frame missing")
    readback = session.checkpoint_readback(target)
    inputs, refs = verify_readback(readback.response, run_id=session.run_id, machine_id=session.machine_id, reviewer=session.client.operator_reviewer,
        frame=readback.frame, source_save=readback.source_save)
    require(target is None or target == inputs.target_id, "Same actual target required")
    session.observe_item(inputs.target_id)
    record: historical.ThresholdCheckpoint = {"run_id": session.run_id, "machine_id": session.machine_id, "reviewer": session.client.operator_reviewer,
        "frame_native": original, "source_save": readback.source_save, "response": object_value(readback.response), "item_native": _last_call(session), "projection": None}
    actual = historical.consume_observation(record, context=session.context, manifest=session.client.manifest, reviewer=session.client.operator_reviewer)
    record["projection"] = actual.to_json()
    ref = write_once(session.client.output / f"timer-checkpoint-{session.checkpoint_observations:02d}.json", record)
    session.refs.extend((*refs, ref))
    return actual, ref


def _natural_files(output: Path) -> dict[str, Pin]:
    paths = (*output.glob("case-natural-day-*.actual-results.json"), *output.glob("case-natural-day-*.native-day-projection.json"),
        *output.glob("case-snapshot-*.native-day-boundary.json"))
    return {path.name: pin(path) for path in sorted(paths)}


def _calendar(literal: str) -> date:
    year, month, day = (int(part) for part in literal.split("."))
    return date(year, month, day)


def _until(session: core.Session, target_raw: int) -> None:
    while session.current().date_raw < target_raw:
        session.advance_one()
    require(session.current().date_raw < target_raw + 24, "Natural interval overshot its intended calendar day")


def _same_native(left: object, right: object) -> bool:
    # Both values originate in bounded duplicate-key-checked raw JSON or the
    # shared pure projection. Compare entirely in Python; native FILETIME/Q64
    # integers must not pass through the safe-number public JSON encoder.
    return json.dumps(left, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(right, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _audit_natural(row: dict[str, object], *, context: object, manifest: object, first: Frame, final: Frame) -> int:
    """Reconsume existing shared native-day projections, not a second day engine."""
    from ck3_mod_acceptance_native_day import project_native_day, project_pre_day_event_boundary

    output = Path(text(field(context, "output"), "output"))
    require(same_json(row, _natural_files(output)), "Original natural file closure differs")
    total, expected = 0, first.date_raw
    snapshots: dict[tuple[int, int, int], dict[str, object]] = {}
    for path in output.glob("case-snapshot-*.actual-results.json"):
        _, original, snapshot = historical._native(pin(path), context=context, manifest=manifest)
        require(field(field(original, "plan"), "tool") == "ck3_take_snapshot", "Original snapshot tool required")
        frame = Frame.parse(snapshot, run_id=text(field(context, "run_id"), "run"), machine_id=text(field(manifest, "machine_id"), "machine"), manifest=manifest)
        snapshots[(frame.date_raw, frame.revision, frame.native_revision)] = mapping(snapshot, "original native snapshot")
    projected: list[tuple[int, int, dict[str, object]]] = []
    used_intents: set[str] = set()
    for name, raw in row.items():
        if not name.endswith((".native-day-projection.json", ".native-day-boundary.json")):
            continue
        record = raw_object(Path(checked_pin(raw, "original natural projection")["path"]))
        require(set(record) == {"raw_public_row_path", "projection_source", "row"}, "Closed shared natural projection required")
        retained = mapping(record["row"], "retained natural row")
        before = mapping(field(field(retained, "result"), "before"), "actual natural before frame")
        frame = Frame.parse(before, run_id=text(field(context, "run_id"), "run"), machine_id=text(field(manifest, "machine_id"), "machine"), manifest=manifest)
        require((frame.pid, frame.player_id, frame.generation_decimal) == (first.pid, first.player_id, first.generation_decimal), "Natural owner drift")
        require(_same_native(snapshots.get((frame.date_raw, frame.revision, frame.native_revision)), before), "Natural before frame has no original snapshot")
        source = Path(text(record["raw_public_row_path"], "original natural row path")).resolve()
        require(source.parent == output.resolve() and (source.name in row or source.name in historical._native_files(output)), "Natural source escaped retained closure")
        original_rows = array(field(raw_object(source), "rows"), "original natural rows")
        require(len(original_rows) == 1, "Exactly one original natural row required")
        original = mapping(original_rows[0], "original natural row")
        if record["projection_source"] == "actual-life-advance-one-day":
            require(source.name == name.replace(".native-day-projection.json", ".actual-results.json"), "Natural projection points at another intent")
            require(source.name not in used_intents, "Cannot replay a natural intent")
            used_intents.add(source.name)
            reproduced = project_native_day(original, before, allow_event_boundary=True)
        else:
            require(record["projection_source"] == "actual-pre-day-snapshot-event-boundary", "Unknown natural projection source")
            reproduced = project_pre_day_event_boundary(before, mapping(field(retained, "after_snapshot"), "event boundary"), snapshot_step_id=text(field(retained, "id"), "snapshot step"))
        require(_same_native(reproduced, retained), "Shared natural projection differs from original producer")
        after = mapping(field(field(retained, "result"), "after"), "natural after")
        ordinal = source.name.split(".", 1)[0].rsplit("-", 1)[1]
        require(ordinal.isdigit(), "Original shared intent ordinal required")
        projected.append((frame.date_raw, int(ordinal), after))
    require(bool(projected), "Actual native natural-day files are missing")
    require(used_intents == {name for name in row if name.endswith(".actual-results.json")}, "Natural raw intents lack a matching validated projection")
    for start, _, after in sorted(projected, key=lambda item: (item[0], item[1])):
        end = integer(after.get("date_raw"), "actual natural end", start, start + 24)
        require(start == expected, "Natural intervals have a gap, overlap or replay")
        total += end - start
        expected = end
    require(expected == final.date_raw and total == final.date_raw - first.date_raw, "Natural intervals do not cover the observed save interval")
    return total


def evaluate(context: object, *, manifest: object, reviewer: str, journal: object) -> Object:
    validate_contract(context)
    row = mapping(journal, "timer journal")
    require(set(row) == set(TimerJournal.__required_keys__), "Closed timer journal required")
    refs = [checked_pin(raw, "actual timer checkpoint") for raw in array(row["checkpoints"], "actual checkpoint refs")]
    require(len(refs) == len({ref["path"] for ref in refs}) == 7, "Seven separate actual Save readbacks required")
    observations = [historical.consume_observation(read(Path(ref["path"])), context=context, manifest=manifest, reviewer=reviewer) for ref in refs]
    first, paid, window, renewed, old_event, expired, grown = observations
    start = _calendar(first.sample.date_literal)
    require(first.sample.date_literal == "1066.9.15" and not first.sample.equipped and
        (first.sample.level, first.sample.xp, first.sample.pending, first.sample.growth_sequence) == (1, 92, 0, 0), "Unchanged core initial input required")
    initial_day = first.inputs.player_variables.get("xalw_fixture_initial_day")
    require(initial_day is not None, "Saved initial current_date anchor missing")
    if initial_day is None:
        raise ValueError("Initial date anchor unavailable")
    anchor = initial_day.integer_value("xalw_fixture_initial_day")
    expected_days = (0, 0, 60, 60, 90, 180)
    for actual, day in zip(observations[:6], expected_days, strict=True):
        require((actual.frame.pid, actual.frame.player_id, actual.frame.generation_decimal, actual.sample.artifact_id, actual.sample.owner_id) ==
            (first.frame.pid, first.frame.player_id, first.frame.generation_decimal, first.sample.artifact_id, first.sample.owner_id), "Same actual process, actor, item and owner required")
        require((_calendar(actual.sample.date_literal) - start).days == day and
            day * 24 <= actual.frame.date_raw - first.frame.date_raw < (day + 1) * 24, "Actual calendar/native timer day differs")
        require((actual.sample.level, actual.sample.xp, actual.sample.pending, actual.sample.growth_sequence) == (1, 92, 0, 0), "Growth occurred before natural renewed expiry")
    require(all(actual.sample.equipped for actual in observations[1:]), "Same weapon must remain equipped during the timer test")
    require(_value(first, "xalw_growth_suppressed_until") is None and _value(first, "xalw_suppression_chain") == 0 and
        _value(first, "xalw_suppression_timer_sequence") is None, "No preloaded suppression terminal state permitted")
    originals = mapping(row["native_records"], "native file closure")
    output = Path(text(field(context, "output"), "output"))
    require(same_json(originals, historical._native_files(output)), "Original native action/snapshot closure differs")
    selections: list[int] = []
    equip: list[bool] = []
    event_keys: dict[tuple[int, int], str] = {}
    for raw in originals.values():
        source = Path(checked_pin(raw, "original native record")["path"])
        native_rows = array(field(raw_object(source), "rows"), "original native rows")
        require(len(native_rows) == 1, "One native row required")
        native_row = mapping(native_rows[0], "native row")
        tool = field(field(native_row, "plan"), "tool")
        if tool == "ck3_query_current_event_window_context_v1" and native_row.get("ok") is True:
            frame, _, _ = historical._native(raw, context=context, manifest=manifest)
            event = mapping(field(field(native_row, "result"), "current_event_window_context"), "actual event")
            if event.get("status") == "available":
                event_keys[(frame.date_raw, integer(field(event, "current_event_instance_id"), "instance", 1))] = text(field(event, "event_definition_key"), "event definition")
        elif tool == "ck3_select_event_option":
            frame, _, _ = historical._native(raw, context=context, manifest=manifest)
            args = field(field(native_row, "plan"), "args")
            key = event_keys.get((frame.date_raw, integer(field(args, "event_instance_id"), "selected instance", 1)))
            require(key is not None, "Selection lacks its actual native event query")
            if key in ("xalw.10", "xalw.11", "xalw.12"):
                selections.append(integer(field(args, "option_number"), "native option", 1))
            else:
                require(frame.date_raw not in (first.frame.date_raw, window.frame.date_raw), "Unrelated event entered a paused payment comparison")
        elif tool == core.EQUIP:
            historical._native(raw, context=context, manifest=manifest)
            desired = field(field(native_row, "plan"), "args")
            require(type(field(desired, "desired_equipped")) is bool, "Original equipment boolean required")
            equip.append(field(desired, "desired_equipped") is True)
        elif tool == "ck3_reply_pending_character_interaction":
            frame, _, _ = historical._native(raw, context=context, manifest=manifest)
            require(frame.date_raw not in (first.frame.date_raw, window.frame.date_raw), "Unrelated notification entered a paused payment comparison")
    require(equip == [True] and selections == [source_option_index("xalw.12", "xalw.12.open") + 1,
        source_option_index("xalw.10", "xalw.10.suppress") + 1, source_option_index("xalw.12", "xalw.12.open") + 1,
        source_option_index("xalw.10", "xalw.10.renew") + 1], "Extra/missing feeding, training, suppression, renewal or equipment intent")
    historical._action_proof(row["suppress"], "xalw.10.suppress", context=context, manifest=manifest, frame=first.frame)
    historical._action_proof(row["renew"], "xalw.10.renew", context=context, manifest=manifest, frame=window.frame)
    require(paid.frame.date_raw == first.frame.date_raw and renewed.frame.date_raw == window.frame.date_raw, "Payment comparisons must use the same paused date")
    require(int(paid.saved.gold_raw) - int(first.saved.gold_raw) == -25 * 100000 and
        int(paid.saved.prestige_raw) - int(first.saved.prestige_raw) == -50 * 100000, "First actual suppression cost differs")
    require(int(renewed.saved.gold_raw) - int(window.saved.gold_raw) == -45 * 100000 and
        int(renewed.saved.prestige_raw) - int(window.saved.prestige_raw) == -50 * 100000, "Actual renewal cost differs")
    require(_value(paid, "xalw_growth_suppressed_until") == _value(window, "xalw_growth_suppressed_until") == anchor + 90 and
        _value(paid, "xalw_suppression_chain") == _value(window, "xalw_suppression_chain") == 1, "First actual 90-day deadline changed before renewal")
    require(_value(renewed, "xalw_growth_suppressed_until") == _value(old_event, "xalw_growth_suppressed_until") == anchor + 180 and
        _value(renewed, "xalw_suppression_chain") == _value(old_event, "xalw_suppression_chain") == 2, "Renewal must add 90 to the old deadline; old event must not clear it")
    require(all(_value(actual, "xalw_suppression_timer_sequence") == 1 for actual in observations[1:]), "Renewal/expiry must preserve the original timer sequence")
    require(_value(expired, "xalw_growth_suppressed_until") is None and _value(grown, "xalw_growth_suppressed_until") is None and
        _value(expired, "xalw_suppression_chain") == _value(grown, "xalw_suppression_chain") == 2, "Natural expiry must remove only the deadline")
    last_date = _calendar(expired.sample.date_literal)
    next_month = date(last_date.year + (last_date.month == 12), last_date.month % 12 + 1, 1)
    total_days = (next_month - start).days
    require(180 < total_days <= 212 and _calendar(grown.sample.date_literal) == next_month and
        total_days * 24 <= grown.frame.date_raw - first.frame.date_raw < (total_days + 1) * 24, "Last Save must be the first calendar month after real expiry")
    require((grown.frame.pid, grown.frame.player_id, grown.frame.generation_decimal, grown.sample.artifact_id, grown.sample.owner_id) ==
        (first.frame.pid, first.frame.player_id, first.frame.generation_decimal, first.sample.artifact_id, first.sample.owner_id) and
        (grown.sample.level, grown.sample.xp, grown.sample.pending, grown.sample.growth_sequence) == (2, 0, 0, 1) and
        grown.sample.last_month == grown.sample.month and _value(grown, "xalw_unsuppressed_equipped_months") == 1,
        "First unsuppressed equipped month must automatically grow L1/92 to L2/0")
    require(window.sample.last_month == window.sample.month and old_event.sample.last_month == old_event.sample.month and
        expired.sample.last_month == expired.sample.month, "Monthly bookkeeping must continue while growth is suppressed")
    hours = _audit_natural(mapping(row["natural_records"], "natural file closure"), context=context, manifest=manifest, first=first.frame, final=grown.frame)
    return {"actual_natural_days": total_days, "actual_natural_hours": hours, "actual_saved_observations": 7,
        "target_artifact_id": first.sample.artifact_id, "initial_date_anchor": anchor, "original_deadline": anchor + 90, "renewed_deadline": anchor + 180,
        "old_timer_did_not_clear_renewal": True, "timer_sequence_preserved": 1, "first_cost_gold": 25, "renewal_cost_gold": 45,
        "initial": first.to_json(), "paid": paid.to_json(), "window": window.to_json(), "renewed": renewed.to_json(), "old_event": old_event.to_json(),
        "expired": expired.to_json(), "grown": grown.to_json(), "stress_formula_credit": False, "cold_transfer_NPC_release_credit": False}


def _state(actual: historical.ThresholdObservation, *, deadline: int | None, chain: int, phase: str) -> None:
    if not (actual.sample.equipped and (actual.sample.level, actual.sample.xp, actual.sample.pending, actual.sample.growth_sequence) == (1, 92, 0, 0) and
            _value(actual, "xalw_growth_suppressed_until") == deadline and _value(actual, "xalw_suppression_chain") == chain and
            _value(actual, "xalw_suppression_timer_sequence") == 1):
        raise core.CaseFailed("Actual suppression state contradicts production behavior at " + phase)


def run_case(context: object, client: object) -> Object:
    contract = validate_contract(context)
    if not isinstance(client, CasePort):
        raise ValueError("Actual shared CaseClient required")
    session = core.Session(context, client, contract)
    saves: list[Pin] = []
    journal: TimerJournal = {"checkpoints": saves, "suppress": None, "renew": None, "native_records": {}, "natural_records": {}}
    status: Literal["PASS", "FAIL", "BLOCKED"] = "BLOCKED"
    error: str | None = None
    observed: Object = {}
    try:
        session.refs.extend(prepared_sources(context, client.state))
        session.snapshot()
        first, reference = _observe(session, None)
        saves.append(reference)
        require(first.sample.date_literal == "1066.9.15" and (first.sample.level, first.sample.xp, first.sample.equipped) == (1, 92, False), "Unchanged core fixture required")
        if int(first.saved.gold_raw) < 70 * 100000 or int(first.saved.prestige_raw) < 100 * 100000:
            raise core.CaseBlocked("Actual initial resources cannot pay both ordinary suppression choices")
        target, start_raw = first.sample.artifact_id, first.frame.date_raw
        session.equip(target, True)
        journal["suppress"] = historical._action(session, target, "xalw.10.suppress")
        paid, reference = _observe(session, target)
        saves.append(reference)
        anchor_variable = first.inputs.player_variables.get("xalw_fixture_initial_day")
        if anchor_variable is None:
            raise core.CaseBlocked("Saved initial current_date anchor missing")
        anchor = anchor_variable.integer_value("xalw_fixture_initial_day")
        _state(paid, deadline=anchor + 90, chain=1, phase="first paid suppression")
        if not (int(paid.saved.gold_raw) - int(first.saved.gold_raw) == -25 * 100000 and
                int(paid.saved.prestige_raw) - int(first.saved.prestige_raw) == -50 * 100000):
            raise core.CaseFailed("First actual suppression cost differs; no renewal permitted")
        _until(session, start_raw + 60 * 24)
        window, reference = _observe(session, target)
        saves.append(reference)
        _state(window, deadline=anchor + 90, chain=1, phase="real renewal window")
        journal["renew"] = historical._action(session, target, "xalw.10.renew")
        renewed, reference = _observe(session, target)
        saves.append(reference)
        _state(renewed, deadline=anchor + 180, chain=2, phase="paid renewal")
        if not (int(renewed.saved.gold_raw) - int(window.saved.gold_raw) == -45 * 100000 and
                int(renewed.saved.prestige_raw) - int(window.saved.prestige_raw) == -50 * 100000):
            raise core.CaseFailed("Actual renewal cost differs")
        _until(session, start_raw + 90 * 24)
        old_event, reference = _observe(session, target)
        saves.append(reference)
        _state(old_event, deadline=anchor + 180, chain=2, phase="original timer date")
        _until(session, start_raw + 180 * 24)
        expired, reference = _observe(session, target)
        saves.append(reference)
        _state(expired, deadline=None, chain=2, phase="natural renewed expiry")
        expiry_date = _calendar(expired.sample.date_literal)
        next_month = date(expiry_date.year + (expiry_date.month == 12), expiry_date.month % 12 + 1, 1)
        remaining_days = (next_month - expiry_date).days
        _until(session, start_raw + (180 + remaining_days) * 24)
        _, reference = _observe(session, target)
        saves.append(reference)
        journal["native_records"] = historical._native_files(client.output)
        journal["natural_records"] = _natural_files(client.output)
        try:
            observed = evaluate(context, manifest=client.manifest, reviewer=client.operator_reviewer, journal=journal)
        except ValueError as failure:
            raise core.CaseFailed(str(failure)) from failure
        status = "PASS"
    except core.CaseFailed as failure:
        status, error = "FAIL", str(failure)
    except (core.CaseBlocked, ValueError, OSError, TimeoutError, KeyError, StopIteration) as failure:
        error = type(failure).__name__ + ": " + str(failure)
    journal["native_records"] = historical._native_files(client.output)
    journal["natural_records"] = _natural_files(client.output)
    journal_ref = write_once(client.output / "timer-evidence-journal.json", journal)
    checks = [core._check(check, status, error, [*session.refs, journal_ref], observed) for check in CHECKS]
    if session.start is not None and session.owner is not None:
        session.days = (session.current().date_raw - session.start.date_raw) // 24
    result: TimerResult = {"schema": "living-artifacts-suppression-timer-result-v1", "product": "living-artifacts", "case": CASE,
        "run_id": session.run_id, "machine_id": session.machine_id, "reviewer": client.operator_reviewer, "observed_at_utc": utc_now(), "status": status,
        "checks": checks, "journal": journal_ref, "error": error, "actual_natural_days": session.days, "actual_public_calls_budgeted": session.calls,
        "actual_saved_observations": session.checkpoint_observations, "original_action_unknown": session.original_action_unknown,
        "case_contract_qualified": status == "PASS", "gui_contract_qualified": status == "PASS", "business_pass": False, "product_release_pass": False,
        "normal_close_owner": "shared entry/CaseClient", "normal_close_pending": True}
    write_once(client.output / RESULT_NAME, result)
    return object_value(result)


def verify_case(context: object) -> Object:
    contract = validate_contract(context)
    output = Path(text(field(context, "output"), "output"))
    if not (output / RESULT_NAME).is_file():
        return {"status": "NOT_RUN", "case_contract_qualified": False, "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False}
    result = read(output / RESULT_NAME)
    require(set(result) == set(TimerResult.__required_keys__), "Closed retained timer result required")
    prepared_sources(context, Path(text(field(context, "state_dir"), "state")))
    runtime = read(Path(checked_pin(field(context, "runtime_manifest"), "runtime manifest")["path"]))
    require(result["schema"] == "living-artifacts-suppression-timer-result-v1" and result["product"] == "living-artifacts" and result["case"] == CASE and
        result["run_id"] == field(context, "run_id") and result["machine_id"] == field(runtime, "machine_id") and
        result["status"] in ("PASS", "FAIL", "BLOCKED") and result["business_pass"] is False and result["product_release_pass"] is False and
        result["normal_close_owner"] == "shared entry/CaseClient" and result["normal_close_pending"] is True, "Retained timer scene/scope differs")
    days = integer(result["actual_natural_days"], "actual natural days", 0, contract.maximum_days)
    integer(result["actual_public_calls_budgeted"], "actual budgeted calls", 1, contract.max_calls)
    saves = integer(result["actual_saved_observations"], "actual Saves", 0, 7)
    require(type(result["original_action_unknown"]) is bool, "Exact unknown-intent boolean required")
    stamp(result["observed_at_utc"])
    complete = saves == 7 and days >= 180 and result["original_action_unknown"] is False
    journal = read(Path(checked_pin(result["journal"], "original timer journal")["path"]))
    observed = evaluate(context, manifest=runtime, reviewer=text(result["reviewer"], "reviewer"), journal=journal) if result["status"] == "PASS" else {}
    if result["status"] == "FAIL" and complete:
        try:
            evaluate(context, manifest=runtime, reviewer=text(result["reviewer"], "reviewer"), journal=journal)
        except ValueError:
            pass
        else:
            raise ValueError("Retained complete FAIL has no reproduced evidence contradiction")
    passed = result["status"] == "PASS"
    require(result["case_contract_qualified"] is passed and result["gui_contract_qualified"] is passed and (not passed or complete), "Retained timer qualification differs")
    require(not passed or integer(observed["actual_natural_days"], "recomputed days") == days, "Actual timer duration differs")
    require(result["error"] is None if passed else type(result["error"]) is str and bool(result["error"]), "PASS/error branch differs")
    checks = array(result["checks"], "actual timer checks")
    require(len(checks) == len(CHECKS), "Every scoped timer check required")
    for check, key in zip(checks, CHECKS, strict=True):
        require(set(mapping(check, "check")) == set(CheckResult.__required_keys__) and field(check, "case_id") == key and field(check, "status") == result["status"] and
            field(check, "evidence_scope") == "fixture_live" and field(check, "reason") == result["error"] and same_json(field(check, "observed"), observed), "Retained check differs from actual evidence")
        refs = array(field(check, "evidence"), "actual evidence")
        require(not passed or result["journal"] in refs, "PASS requires the original evidence journal")
        for raw in refs:
            checked_pin(raw, "retained evidence", allow_empty=True)
    return result
