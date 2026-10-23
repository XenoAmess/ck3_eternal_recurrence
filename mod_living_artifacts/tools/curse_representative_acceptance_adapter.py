"""Two real equipped curses, bounded payment and same-month reentry.

Session owns every native action, interruption and Save/Root exchange. The
existing typed historical checkpoint consumer is reused without running its
threshold scenario. This package never writes game state or loads another save.
"""
from __future__ import annotations

from dataclasses import dataclass
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
import suppression_timer_acceptance_adapter as natural
from acceptance_contract import CasePort, CheckResult, Frame, Object, Pin, array, field, integer, mapping, object_value, pin, read, require, text, utc_now, write_once
from checkpoint_callback import checked_pin, verify_readback
from checkpoint_producer import raw_object, stamp
from checkpoint_artifacts import SavedArtifact, SavedVariable, records
from management_event_contract import source_option_index
from prepare_fixture import FixtureEmission
from prepare_curse_fixture import INITIAL_GOLD, emit_fixture
from prepare_threshold_fixture import same_json, tree

CASE: Literal["curse_representative"] = "curse_representative"
CONTRACT_NAME = "curse_representative.contract.json"
RESULT_NAME = "living-artifacts-curse-representative-result.json"
CHECKS = ("CURSE-BLOOD-EQUIP-REMOVE", "CURSE-APPETITE-BOUNDED-PAYMENT", "CURSE-SAME-DATE-NO-RECHARGE", "CURSE-NEXT-DAY-NO-RECHARGE", "CURSE-CANDIDATE-PERSISTED-JUDGEMENT")
SOURCES = ("curse_representative_acceptance_adapter.py", "curse_representative.registry_stanza.json", "prepare_curse_fixture.py", "prepare_npc_fixture.py", "suppression_timer_acceptance_adapter.py", "suppression_timer.registry.json", "suppression_timer.contract.json", "acceptance_adapter.py", "acceptance_contract.py",
    "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py", "living_artifacts_content.py", "checkpoint_callback.py",
    "checkpoint_artifacts.py", "checkpoint_producer.py", "startup_actor_binding.py", "management_event_contract.py", "inventory_gui_contract.py",
    "native_interruption_contract.py", "threshold_acceptance_adapter.py", "prepare_threshold_fixture.py")


class CurseJournal(TypedDict):
    checkpoints: list[Pin]
    native_records: dict[str, Pin]
    natural_records: dict[str, Pin]


class CurseResult(TypedDict):
    schema: Literal["living-artifacts-curse-representative-result-v1"]
    product: Literal["living-artifacts"]
    case: Literal["curse_representative"]
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
    require(field(context, "product") == "living-artifacts" and field(context, "case") == CASE, "Select the actual curse representative case")
    config = mapping(field(context, "case_contract"), "curse contract")
    require(same_json(config, read(TOOLS / CONTRACT_NAME)), "Exact canonical curse contract required")
    integer(config["schema_version"], "curse schema", 1, 1)
    spec = field(context, "case_spec")
    require(field(spec, "id") == CASE, "Selected public case spec differs")
    tools = {text(item, "tool") for item in array(field(spec, "required_mcp_tools"), "declared tools")}
    require(set(core.REQUIRED_TOOLS) <= tools, "Every existing Session tool must be declared")
    for key, value in core.REQUIRED_OPT_INS.items():
        require(field(spec, key) is value, "Existing native action opt-in missing")
    require(core.ITEM in array(field(spec, "opt_in_read_only_mcp_tools"), "read-only opt-ins"), "Independent native equipment read required")
    require(config["required_checks"] == list(CHECKS) and config["whole_product_acceptance_credit"] is False, "Scoped curse checks required")
    integer(config["maximum_checkpoints"], "Save cap", 7, 7)
    require("ck3_query_campaign_root_context_v1" in tools, "Existing native health root query must be declared")
    return core.Contract(integer(config["maximum_natural_days"], "day cap", 17, 17), integer(config["max_public_calls"], "call cap", 420, 420),
        integer(config["day_timeout_seconds"], "single-day timeout", 60, 60), CHECKS,
        tuple(text(item, "deferred") for item in array(config["deferred_checks"], "deferred checks")))


def prepare_case(context: object) -> Object:
    validate_contract(context)
    values = mapping(context, "preparation context")
    output = Path(text(field(values, "output"), "preparation output")).resolve()
    fixture = emit_fixture(output / "external-curse-fixture", game=Path(text(field(values, "game_dir"), "game directory")) / "game")
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
    require(isinstance(state, Path) and state.resolve() == Path(text(field(context, "state_dir"), "state")).resolve(), "Curse crossed allocated state")
    root = state / "profile/mod-content/fixture"
    manifest = read(root / "_case_contract.json")
    require(set(manifest) == {"product", "case", "config", "fixture_emission", "caller_sources", "contract_source", "formal_files", "business_pass"} and
        manifest["product"] == "living-artifacts" and manifest["case"] == CASE and manifest["business_pass"] is False and
        same_json(manifest["config"], field(context, "case_contract")), "Curse deployed contract differs")
    callers = mapping(manifest["caller_sources"], "source closure")
    require(set(callers) == set(SOURCES), "Curse caller closure differs")
    refs = [core._checked_pin(callers[name], "curse source", TOOLS / name) for name in SOURCES]
    refs.append(core._checked_pin(manifest["contract_source"], "curse contract", TOOLS / CONTRACT_NAME))
    emission = mapping(manifest["fixture_emission"], "curse fixture")
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
    require(read(state / "profile/dlc_load.json") == {"enabled_mods": ["mod/product.mod", "mod/fixture.mod"], "disabled_dlcs": []}, "Only formal product and curse fixture may mount")
    prepared_pin = checked_pin(field(read(state / "preparation.json"), "preparation"), "actual shared preparation")
    prepared = read(Path(prepared_pin["path"]))
    require(field(prepared, "schema") == "ck3-mod-acceptance-prepared-fixture-v1" and
        Path(text(field(prepared, "state_dir"), "prepared state")).resolve() == state.resolve(), "Shared preparation crossed schema/state")
    loaded = {"mod/product.mod", "mod/fixture.mod", "dlc_load.json"}
    loaded.update("mod-content/product/" + relative for relative in mapping(manifest["formal_files"], "formal closure"))
    loaded.update("mod-content/fixture/" + relative for relative in set(emitted) | {"_case_contract.json"})
    table = mapping(field(prepared, "files"), "shared source table")
    require(loaded <= set(table), "Shared preparation omits loaded curse inputs")
    refs.extend(core._checked_pin(table[relative], "loaded shared input", state / "profile" / relative) for relative in sorted(loaded))
    source_record = read(root / "_fixture_sources.json")
    require(set(source_record) == {"schema", "machine_id", "observed_at_utc", "source_bindings", "qualification", "business_pass"} and
        source_record["schema"] == "living-artifacts-curse-input-sources-v1" and source_record["qualification"] == "initial-source-only" and
        source_record["business_pass"] is False, "Source-only initial qualification required")
    stamp(source_record["observed_at_utc"])
    runtime = read(Path(checked_pin(field(context, "runtime_manifest"), "runtime manifest")["path"]))
    require(text(source_record["machine_id"], "source machine") == text(field(runtime, "machine_id"), "target machine"), "Initial source qualification belongs to another machine")
    refs.extend(checked_pin(raw, "actual vanilla fixture source") for raw in mapping(source_record["source_bindings"], "fixture source bindings").values())
    return (*refs, prepared_pin, pin(root / "_case_contract.json"), pin(state / "profile/dlc_load.json"))


class CurseCheckpoint(TypedDict):
    base: historical.ThresholdCheckpoint
    appetite_native: Pin
    candidate_native: Pin
    health_native: Pin | None
    projection: Object | None


@dataclass(frozen=True)
class Health:
    raw: str | None
    unavailable_reason: str | None

    def to_json(self) -> Object:
        return {"status": "UNAVAILABLE" if self.raw is None else "available", "raw_decimal": self.raw,
                "scale": 100000, "unavailable_reason": self.unavailable_reason}


@dataclass(frozen=True)
class CurseObservation:
    base: historical.ThresholdObservation
    appetite: SavedArtifact
    appetite_equipped: bool
    candidate: SavedArtifact
    candidate_equipped: bool
    health: Health

    def to_json(self) -> Object:
        return {"base": self.base.to_json(), "appetite": self.appetite.to_json(), "appetite_equipped": self.appetite_equipped,
                "candidate": self.candidate.to_json(), "candidate_equipped": self.candidate_equipped, "health": self.health.to_json()}


def _item(melted: Path, reference: str) -> SavedArtifact:
    matches = [body for identity, body in records(melted, ("artifacts", "artifacts")) if identity == reference]
    require(len(matches) == 1, "One exact additional artifact record required")
    return SavedArtifact.parse(reference, matches[0])


def _reference(base: historical.ThresholdObservation, name: str) -> str:
    value = base.inputs.player_variables.get(name)
    require(value is not None, "Initial artifact reference missing: " + name)
    if value is None:
        raise ValueError(name)
    return value.artifact_reference(name)


def _equipped(reference: object, target: SavedArtifact, *, base: historical.ThresholdObservation, context: object, manifest: object) -> bool:
    frame, row, snapshot = historical._native(reference, context=context, manifest=manifest)
    require((frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) ==
        (base.frame.pid, base.frame.player_id, base.frame.generation_decimal, base.frame.date_raw), "Additional native artifact crossed scene")
    require(field(field(row, "plan"), "tool") == core.ITEM, "Independent personal artifact query required")
    result = mapping(field(row, "result"), "native artifact")
    require(result.get("available") is True and result.get("loaded_source_pins_verified") is True and result.get("read_only") is True and
        result.get("personally_owned") is True and result.get("inventory_artifact") is True and result.get("native_equipped_observed") is True and
        type(result.get("equipped")) is bool and integer(result.get("requested_artifact_id"), "artifact", 0) == int(target.artifact_id) and
        integer(result.get("played_character_id"), "owner", 1) == frame.player_id and target.owner_id == str(frame.player_id) and
        integer(result.get("date_raw"), "native date", 1) == frame.date_raw, "Independent owner/equipment authority unavailable")
    require(historical.native_vitals(snapshot) == base.native, "Additional native read changed paused wallet/stress")
    return result["equipped"] is True


def consume_health(reference: object, *, frame: Frame, context: object, manifest: object) -> Health:
    source = checked_pin(reference, "original health query")
    rows = array(field(raw_object(Path(source["path"])), "rows"), "health rows")
    require(len(rows) == 1, "Exactly one original health query required")
    row = mapping(rows[0], "original health row")
    require(field(field(row, "plan"), "tool") == "ck3_query_campaign_root_context_v1", "Existing root query required")
    after = Frame.parse(field(row, "after_snapshot"), run_id=text(field(context, "run_id"), "run"),
        machine_id=text(field(manifest, "machine_id"), "machine"), manifest=manifest)
    require((after.pid, after.player_id, after.generation_decimal, after.date_raw) ==
        (frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw), "Health query crossed process/actor/date")
    if row.get("ok") is not True or row.get("error") is not None:
        return Health(None, text(row.get("error"), "original health refusal"))
    result = mapping(field(row, "result"), "original campaign result")
    if result.get("status") != "available" or result.get("campaign_root_context_ready") is not True:
        return Health(None, "Original root query not available: " + str(result.get("status")))
    require(result.get("accepted") is True, "Native root query was not accepted")
    root = mapping(field(result, "campaign_root_context"), "actual campaign root")
    require(integer(root.get("player_character_id"), "root actor", 1) == frame.player_id and
        integer(root.get("date_raw"), "root date", 1) == frame.date_raw and
        integer(root.get("snapshot_revision"), "root native revision", 1) == after.native_revision,
        "Native health root identity/revision differs")
    provenance = mapping(field(root, "provenance"), "root provenance")
    game = mapping(field(manifest, "game"), "frozen game")
    require(field(provenance, "game_version") == field(game, "version") and field(provenance, "character_health_rva") == "0x28C64E0" and
        text(field(provenance, "executable_sha256"), "root EXE").lower() == text(field(game, "exe_sha256"), "frozen EXE").lower(),
        "Native health exact image differs")
    readiness = mapping(field(root, "readiness"), "root readiness")
    if readiness.get("player_health_ready") is not True or root.get("player_health") is None:
        return Health(None, "Original root health unavailable")
    require(readiness.get("same_frame_ready") is True and readiness.get("ready") is True, "Native health root is not a complete same-frame observation")
    health = mapping(root["player_health"], "native health")
    require(set(health) == {"raw", "scale"}, "Exact native health fixed point required")
    integer(health["scale"], "health scale", 100000, 100000)
    return Health(str(integer(health["raw"], "native health Q64", -(2**63), 2**63 - 1)), None)


def consume_observation(record: object, *, context: object, manifest: object, reviewer: str) -> CurseObservation:
    row = mapping(record, "curse checkpoint")
    require(set(row) == set(CurseCheckpoint.__required_keys__), "Closed curse checkpoint required")
    base = historical.consume_observation(row["base"], context=context, manifest=manifest, reviewer=reviewer)
    melted = Path(checked_pin(field(field(row["base"], "response"), "melted_save"), "verified melted save")["path"])
    appetite = _item(melted, _reference(base, "xalw_curse_fixture_appetite"))
    candidate = _item(melted, _reference(base, "xalw_curse_fixture_candidate"))
    require(len({base.sample.artifact_id, appetite.artifact_id, candidate.artifact_id}) == 3, "Distinct original items required")
    health = Health(None, "Health query not scheduled for this checkpoint") if row["health_native"] is None else consume_health(row["health_native"], frame=base.frame, context=context, manifest=manifest)
    actual = CurseObservation(base, appetite, _equipped(row["appetite_native"], appetite, base=base, context=context, manifest=manifest),
        candidate, _equipped(row["candidate_native"], candidate, base=base, context=context, manifest=manifest), health)
    require(row["projection"] is None or same_json(row["projection"], actual.to_json()), "Saved curse projection differs from original evidence")
    return actual


def _last_call(session: core.Session) -> Pin:
    return pin(session.client.output / f"xalw-core-{session.sequence:04d}.actual-results.json")


def _root_health(session: core.Session) -> Pin:
    """One existing read-only tool; no action, retry or alternative state machine."""
    session.budget(1)
    session.calls += 1
    name = f"curse-health-{session.checkpoint_observations:02d}"
    step: Object = {"id": name, "tool": "ck3_query_campaign_root_context_v1", "args": {"expected_revision": session.current().revision},
                    "fresh_revision": True, "continue_on_error": True, "timeout": 30}
    result = session.client.execute_plan([step], name, timeout=35)
    rows = array(result, "health actual rows")
    require(len(rows) == 1, "One health original row required")
    session.bind(field(rows[0], "after_snapshot"))
    reference = pin(session.client.output / (name + ".actual-results.json"))
    session.refs.append(reference)
    return reference


def _observe(session: core.Session, target: str | None, *, health: bool = False) -> tuple[CurseObservation, Pin]:
    session.snapshot()
    original = session.last_native_record
    if original is None:
        raise ValueError("Original paused frame missing")
    readback = session.checkpoint_readback(target)
    inputs, refs = verify_readback(readback.response, run_id=session.run_id, machine_id=session.machine_id,
        reviewer=session.client.operator_reviewer, frame=readback.frame, source_save=readback.source_save)
    require(target is None or target == inputs.target_id, "Original blood target changed")
    session.observe_item(inputs.target_id)
    base: historical.ThresholdCheckpoint = {"run_id": session.run_id, "machine_id": session.machine_id, "reviewer": session.client.operator_reviewer,
        "frame_native": original, "source_save": readback.source_save, "response": object_value(readback.response), "item_native": _last_call(session), "projection": None}
    appetite = inputs.player_variables["xalw_curse_fixture_appetite"].artifact_reference("appetite")
    candidate = inputs.player_variables["xalw_curse_fixture_candidate"].artifact_reference("candidate")
    session.observe_item(appetite)
    appetite_native = _last_call(session)
    session.observe_item(candidate)
    record: CurseCheckpoint = {"base": base, "appetite_native": appetite_native, "candidate_native": _last_call(session),
        "health_native": _root_health(session) if health else None, "projection": None}
    actual = consume_observation(record, context=session.context, manifest=session.client.manifest, reviewer=session.client.operator_reviewer)
    record["projection"] = actual.to_json()
    reference = write_once(session.client.output / f"curse-checkpoint-{session.checkpoint_observations:02d}.json", record)
    session.refs.extend((*refs, reference))
    return actual, reference


def _require_initial_wallet(initial: CurseObservation) -> None:
    expected = str(INITIAL_GOLD * 100000)
    require(initial.base.saved.gold_raw == initial.base.native.gold_raw == expected,
        f"Initial curse fixture wallet must be {INITIAL_GOLD} gold before the first equipment action; "
        f"saved Q100000={initial.base.saved.gold_raw}, native Q100000={initial.base.native.gold_raw}")


def _number(values: dict[str, SavedVariable], name: str) -> int | None:
    value = values.get(name)
    return None if value is None else value.integer_value(name)


def _payment(values: dict[str, SavedVariable]) -> str | None:
    value = values.get("xalw_content_payment")
    if value is None:
        return None
    require(value.kind == "value" and value.flag is None, "Actual numeric payment cache required")
    return "0" if value.raw_identity is None else value.raw_identity


def _candidate_judgement(item: SavedArtifact) -> Object:
    version = _number(item.variables, "xalw_schema_version")
    kind = item.variables.get("xalw_kind")
    require(version == 2 and kind is not None and kind.kind == "flag" and kind.flag in ("ordinary", "living"), "Candidate production judgement is unavailable")
    if kind is None:
        raise ValueError("Candidate kind missing")
    return {"artifact_id": item.artifact_id, "schema_version": version, "kind": kind.flag,
        "level": _number(item.variables, "xalw_level"), "growth_sequence": _number(item.variables, "xalw_growth_sequence"),
        "persisted_roll_fields": {key: value.to_json() for key, value in item.variables.items()
            if key.startswith(("xalw_affix_", "xalw_curse_")) or key in ("xalw_personality", "xalw_diet", "xalw_xp_in_level", "xalw_pending_xp")}}


def evaluate(context: object, *, manifest: object, reviewer: str, journal: object) -> Object:
    validate_contract(context)
    row = mapping(journal, "curse journal")
    require(set(row) == set(CurseJournal.__required_keys__), "Closed curse journal required")
    refs = [checked_pin(raw, "actual curse checkpoint") for raw in array(row["checkpoints"], "checkpoints")]
    require(len(refs) == len({ref["path"] for ref in refs}) == 7, "Seven distinct real Save readbacks required")
    saved = [read(Path(ref["path"])) for ref in refs]
    observations = [consume_observation(raw, context=context, manifest=manifest, reviewer=reviewer) for raw in saved]
    first, equipped, removed, before, charged, reentered, next_day = observations
    _require_initial_wallet(first)
    start = first.base.frame
    require(first.base.sample.date_literal == "1066.9.15", "Ordinary Robert initial date required")
    for actual, day in zip(observations, (0, 0, 0, 15, 16, 16, 17), strict=True):
        base = actual.base
        require((base.frame.pid, base.frame.player_id, base.frame.generation_decimal, base.sample.artifact_id, actual.appetite.artifact_id, actual.candidate.artifact_id) ==
            (start.pid, start.player_id, start.generation_decimal, first.base.sample.artifact_id, first.appetite.artifact_id, first.candidate.artifact_id), "Scene/original item drift")
        require(base.frame.date_raw - start.date_raw == day * 24, "Actual seven checkpoint calendar differs")
        require((base.sample.level, base.sample.xp, base.sample.pending, base.sample.growth_sequence) == (1, 0, 0, 0), "Unequipped blood item unexpectedly grew")
        require(_number(base.values, "xalw_curse_1") == 1 and _number(base.values, "xalw_curse_rank_1") == 3 and
            _number(actual.appetite.variables, "xalw_curse_1") == 2 and _number(actual.appetite.variables, "xalw_curse_rank_1") == 3,
            "Declared rank-three curse identities changed")
        require("xalw_content_blood_1_3_modifier" in base.modifiers and not actual.candidate_equipped, "Real blood modifier/candidate unequipped authority missing")
        require(_candidate_judgement(actual.candidate) == _candidate_judgement(first.candidate), "Original candidate was rejudged or grew while unequipped")
    require([item.base.sample.equipped for item in observations] == [False, True, False, False, False, False, False] and
        [item.appetite_equipped for item in observations] == [False, False, False, True, True, True, True], "Actual native equipment sequence differs")
    require(first.base.saved == equipped.base.saved == removed.base.saved, "Same paused health comparison changed wallet/stress")
    initial_health, equipped_health, removed_health = (item.health.raw for item in observations[:3])
    health_available = initial_health is not None and equipped_health is not None and removed_health is not None
    if initial_health is not None and equipped_health is not None and removed_health is not None:
        require(int(equipped_health) - int(initial_health) == -120000 and removed_health == initial_health, "Actual native blood health projection/removal differs from -1.2")
    require(0 < int(before.base.saved.gold_raw) < 50 * 100000, "Actual pre-month wallet is not a shortage input")
    values = [item.base.inputs.player_variables for item in observations]
    require(_payment(values[0]) is None and _payment(values[3]) is None, "Preloaded payment result forbidden")
    require(_number(values[3], "xalw_content_month_done") != 12802, "October was settled before the natural month boundary")
    require(_number(values[4], "xalw_content_month_done") == _number(values[5], "xalw_content_month_done") == _number(values[6], "xalw_content_month_done") == 12802,
        "Actual owner month guard differs")
    payment = _payment(values[4])
    require(payment is not None and 0 < int(payment) < 50 * 100000 and
        _number(values[4], "xalw_content_appetite_quote") == 50 and int(charged.base.saved.gold_raw) == 0,
        "Actual bounded shortage payment/quote/wallet differs")
    require(charged.base.saved.stress is not None and before.base.saved.stress is not None and charged.base.saved.stress > before.base.saved.stress,
        "Actual shortage stress increase unavailable; do not invent the adjusted +40 formula")
    charged_stress, before_stress = charged.base.saved.stress, before.base.saved.stress
    if charged_stress is None or before_stress is None:
        raise ValueError("Actual shortage stress unavailable")
    require(charged.base.saved == reentered.base.saved and _payment(values[5]) == payment and
        _number(values[5], "xalw_content_appetite_quote") == 50, "Same paused-date equipment/management charged twice")
    require(_payment(values[6]) == payment and _number(values[6], "xalw_content_appetite_quote") == 50,
        "Next-day same-month dispatch rewrote actual payment/quote")
    output = Path(text(field(context, "output"), "output"))
    require(same_json(row["native_records"], historical._native_files(output)), "Native original file closure differs")
    equip_intents: list[tuple[int, bool]] = []
    choices: list[tuple[str, int]] = []
    event_keys: dict[tuple[int, int], str] = {}
    for raw in mapping(row["native_records"], "original native records").values():
        frame, native_row, _ = historical._native(raw, context=context, manifest=manifest)
        plan = field(native_row, "plan")
        tool = field(plan, "tool")
        if tool == core.EQUIP:
            args = field(plan, "args")
            desired = field(args, "desired_equipped")
            require(type(desired) is bool, "Actual equipment boolean required")
            equip_intents.append((integer(field(args, "artifact_id"), "item", 0), desired is True))
        if tool == "ck3_query_current_event_window_context_v1":
            event = mapping(field(field(native_row, "result"), "current_event_window_context"), "actual event")
            if event.get("status") == "available":
                event_keys[(frame.date_raw, integer(field(event, "current_event_instance_id"), "instance", 1))] = text(field(event, "event_definition_key"), "event")
        if tool == "ck3_select_event_option":
            args = field(plan, "args")
            key = event_keys.get((frame.date_raw, integer(field(args, "event_instance_id"), "selected instance", 1)))
            require(key is not None, "Selection lacks its original native event identity")
            if key is None:
                raise ValueError("Native event identity missing")
            if key.startswith("xalw."):
                choices.append((key, integer(field(args, "option_number"), "actual option", 1)))
            else:
                require(frame.date_raw not in (start.date_raw, charged.base.frame.date_raw), "Unrelated event entered a paused comparison")
        if tool == "ck3_reply_pending_character_interaction":
            require(frame.date_raw not in (start.date_raw, charged.base.frame.date_raw), "Unrelated notification entered a paused comparison")
    a, b = int(first.base.sample.artifact_id), int(first.appetite.artifact_id)
    require(equip_intents == [(a, True), (a, False), (b, True), (b, False), (b, True)], "Extra/missing original equipment intent")
    require(choices == [("xalw.12", source_option_index("xalw.12", "xalw.12.open") + 1), ("xalw.10", source_option_index("xalw.10", "xalw.10.close") + 1)] * 2,
        "Only two normal management open/close choices permitted")
    hours = natural._audit_natural(mapping(row["natural_records"], "natural original files"), context=context, manifest=manifest, first=start, final=next_day.base.frame)
    return {"actual_natural_days": 17, "actual_natural_hours": hours, "actual_saved_observations": 7, "health_numeric_available": health_available,
        "native_health_expected_delta_raw_decimal": "-120000", "payment_raw_decimal": payment, "quote_gold": 50,
        "shortfall_stress_actual_delta": charged_stress - before_stress,
        "next_day_wallet_change_raw_decimal": str(int(next_day.base.saved.gold_raw) - int(charged.base.saved.gold_raw)),
        "next_day_stress_change": None if next_day.base.saved.stress is None else next_day.base.saved.stress - charged_stress,
        "next_day_world_change_policy": "No equality assumption; unchanged production month/payment/quote prove no repeated monthly dispatch",
        "candidate_judgement": _candidate_judgement(first.candidate), "candidate_first_unjudged_observation_credit": False,
        "checkpoints": [item.to_json() for item in observations], "NPC_combat_stacking_cold_suppression_release_credit": False}


def _checks(status: Literal["PASS", "FAIL", "BLOCKED"], error: str | None, observed: Object, refs: list[Pin]) -> list[CheckResult]:
    checks = [core._check(key, status, error, refs, observed) for key in CHECKS]
    if status == "PASS" and observed.get("health_numeric_available") is False:
        checks[0] = core._check(CHECKS[0], "BLOCKED", "Existing native CampaignRoot health unavailable; saved modifier/equipment projection retained", refs, observed)
    return checks


def run_case(context: object, client: object) -> Object:
    contract = validate_contract(context)
    if not isinstance(client, CasePort):
        raise ValueError("Existing shared CaseClient required")
    session = core.Session(context, client, contract)
    saves: list[Pin] = []
    journal: CurseJournal = {"checkpoints": saves, "native_records": {}, "natural_records": {}}
    status: Literal["PASS", "FAIL", "BLOCKED"] = "BLOCKED"
    error: str | None = None
    observed: Object = {}
    try:
        session.refs.extend(prepared_sources(context, client.state))
        first, reference = _observe(session, None, health=True)
        saves.append(reference)
        _require_initial_wallet(first)
        a, b, start = first.base.sample.artifact_id, first.appetite.artifact_id, first.base.frame.date_raw
        session.equip(a, True)
        _, reference = _observe(session, a, health=True)
        saves.append(reference)
        session.equip(a, False)
        _, reference = _observe(session, a, health=True)
        saves.append(reference)
        session.equip(b, True)
        natural._until(session, start + 15 * 24)
        _, reference = _observe(session, a)
        saves.append(reference)
        natural._until(session, start + 16 * 24)
        _, reference = _observe(session, a)
        saves.append(reference)
        session.equip(b, False)
        session.equip(b, True)
        for _ in range(2):
            session.open_management(b)
            session.select_management("xalw.10", "xalw.10.close", next_event=None)
        _, reference = _observe(session, a)
        saves.append(reference)
        natural._until(session, start + 17 * 24)
        _, reference = _observe(session, a)
        saves.append(reference)
        journal["native_records"] = historical._native_files(client.output)
        journal["natural_records"] = natural._natural_files(client.output)
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
    journal["natural_records"] = natural._natural_files(client.output)
    journal_ref = write_once(client.output / "curse-evidence-journal.json", journal)
    checks = _checks(status, error, observed, [*session.refs, journal_ref])
    if any(check["status"] == "BLOCKED" for check in checks):
        status = "BLOCKED"
        error = next(check["reason"] for check in checks if check["status"] == "BLOCKED")
    result: CurseResult = {"schema": "living-artifacts-curse-representative-result-v1", "product": "living-artifacts", "case": CASE,
        "run_id": session.run_id, "machine_id": session.machine_id, "reviewer": client.operator_reviewer, "observed_at_utc": utc_now(),
        "status": status, "checks": checks, "journal": journal_ref, "error": error, "actual_natural_days": session.days,
        "actual_public_calls_budgeted": session.calls, "actual_saved_observations": session.checkpoint_observations,
        "original_action_unknown": session.original_action_unknown, "case_contract_qualified": status == "PASS", "gui_contract_qualified": status == "PASS",
        "business_pass": False, "product_release_pass": False, "normal_close_owner": "shared entry/CaseClient", "normal_close_pending": True}
    write_once(client.output / RESULT_NAME, result)
    return object_value(result)


def verify_case(context: object) -> Object:
    contract = validate_contract(context)
    output = Path(text(field(context, "output"), "output"))
    if not (output / RESULT_NAME).is_file():
        return {"status": "NOT_RUN", "business_pass": False, "product_release_pass": False, "case_contract_qualified": False, "gui_contract_qualified": False}
    result = read(output / RESULT_NAME)
    require(set(result) == set(CurseResult.__required_keys__), "Closed retained curse result required")
    prepared_sources(context, Path(text(field(context, "state_dir"), "state")))
    runtime = read(Path(checked_pin(field(context, "runtime_manifest"), "runtime manifest")["path"]))
    require(result["schema"] == "living-artifacts-curse-representative-result-v1" and result["case"] == CASE and result["product"] == "living-artifacts" and
        result["run_id"] == field(context, "run_id") and result["machine_id"] == field(runtime, "machine_id") and result["business_pass"] is False and
        result["product_release_pass"] is False and result["normal_close_pending"] is True and result["normal_close_owner"] == "shared entry/CaseClient",
        "Retained scene/scope differs")
    integer(result["actual_natural_days"], "actual days", 0, contract.maximum_days)
    integer(result["actual_public_calls_budgeted"], "actual calls", 1, contract.max_calls)
    count = integer(result["actual_saved_observations"], "actual Saves", 0, 7)
    require(type(result["original_action_unknown"]) is bool and result["status"] in ("PASS", "FAIL", "BLOCKED"), "Retained status/types differ")
    stamp(result["observed_at_utc"])
    journal = read(Path(checked_pin(result["journal"], "retained journal")["path"]))
    observed: Object = {}
    checks = array(result["checks"], "retained checks")
    require(len(checks) == len(CHECKS), "Every scoped check required")
    if any(field(check, "status") == "PASS" for check in checks):
        require(count == 7 and result["actual_natural_days"] == 17 and result["original_action_unknown"] is False, "Completed evidence required")
        observed = evaluate(context, manifest=runtime, reviewer=text(result["reviewer"], "reviewer"), journal=journal)
    for check, key in zip(checks, CHECKS, strict=True):
        require(set(mapping(check, "check")) == set(CheckResult.__required_keys__) and field(check, "case_id") == key and
            field(check, "evidence_scope") == "fixture_live" and same_json(field(check, "observed"), observed), "Retained check/projection differs")
        for raw in array(field(check, "evidence"), "actual evidence"):
            checked_pin(raw, "retained source", allow_empty=True)
    if observed:
        expected = _checks("PASS", None, observed, [])
        require([field(check, "status") for check in checks] == [check["status"] for check in expected] and
            [field(check, "reason") for check in checks] == [check["reason"] for check in expected], "Retained scoped verdict differs")
    else:
        require(result["status"] in ("FAIL", "BLOCKED") and all(field(check, "status") == result["status"] and field(check, "reason") == result["error"] for check in checks), "Non-success branch differs")
    passed = all(field(check, "status") == "PASS" for check in checks)
    if result["status"] == "FAIL" and count == 7:
        try:
            evaluate(context, manifest=runtime, reviewer=text(result["reviewer"], "reviewer"), journal=journal)
        except ValueError:
            pass
        else:
            raise ValueError("Completed FAIL has no reproduced source contradiction")
    require(result["case_contract_qualified"] is passed and result["gui_contract_qualified"] is passed and
        result["status"] == ("PASS" if passed else "FAIL" if any(field(check, "status") == "FAIL" for check in checks) else "BLOCKED"), "Retained overall verdict differs")
    require(result["error"] is None if passed else result["error"] == next(field(check, "reason") for check in checks if field(check, "status") != "PASS") and
        type(result["error"]) is str and bool(result["error"]), "Retained overall reason differs")
    return result
