"""Seven real Save readbacks for threshold growth and the first suppression month.

Saved projections are historical observations. Native equipment and wallet/stress
reads are independent; an adjusted stress formula and effective health are not
inferred from those differences. Shared Session owns every action and interruption.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sys
from typing import Final, Literal, TypedDict

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import acceptance_adapter as core
from acceptance_contract import CasePort, CheckResult, Frame, Object, Pin, array, decimal_id, field, integer, mapping, native_id, object_value, pin, read, require, text, utc_now, write_once
from checkpoint_artifacts import SavedInputs, SavedVariable, one, parse_block, records, scalar, structured
from checkpoint_callback import CheckpointSample, checked_pin, verify_readback
from checkpoint_producer import declared_pin, raw_object, stamp
from management_event_contract import management_choice, source_option_index
from prepare_threshold_fixture import CASE, CONTRACT_NAME, SOURCES, prepare_inputs, prepared_sources, same_json

RESULT_NAME = "living-artifacts-threshold-result.json"
CHECKS = ("THRESHOLD-AUTOMATIC-11", "THRESHOLD-CURSE-HUNGER-PROJECTION", "TRAIN-ACTUAL-XP-WALLET", "TRAIN-ACTUAL-STRESS",
          "SUPPRESS-ACTUAL-WALLET-90-DAY", "SUPPRESS-ACTUAL-STRESS", "SUPPRESS-EQUIPMENT-PERSISTENCE", "SUPPRESS-MONTHLY-PAUSE")
DATES = ("1066.9.15", "1066.10.1", "1066.10.1", "1066.10.1", "1066.10.1", "1066.10.1", "1066.11.1")
DAYS = (0, 16, 16, 16, 16, 16, 47)
ZERO_GOLD_GAME: Final[tuple[str, str]] = (
    "1.20.0.4", "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518")


class ThresholdCheckpoint(TypedDict):
    run_id: str
    machine_id: str
    reviewer: str
    frame_native: Pin
    source_save: Pin
    response: Object
    item_native: Pin
    projection: Object | None


class ActionEvidence(TypedDict):
    option: str
    before_event: Pin
    submission: Pin


class ThresholdJournal(TypedDict):
    checkpoints: list[Pin]
    train: Pin | None
    suppress: Pin | None
    native_records: dict[str, Pin]


@dataclass(frozen=True)
class Vitals:
    gold_raw: str
    prestige_raw: str
    stress: int | None

    def to_json(self) -> Object:
        return {"gold_raw_decimal": self.gold_raw, "prestige_raw_decimal": self.prestige_raw, "scale": 100000, "stress_points": self.stress}

    @classmethod
    def parse(cls, value: object) -> Vitals:
        row = mapping(value, "vitals projection")
        require(set(row) == {"gold_raw_decimal", "prestige_raw_decimal", "scale", "stress_points"}, "Closed vitals required")
        integer(row["scale"], "Q scale", 100000, 100000)
        amounts: list[str] = []
        for key in ("gold_raw_decimal", "prestige_raw_decimal"):
            amount = text(row[key], key)
            require(re.fullmatch(r"-?(0|[1-9][0-9]*)", amount) is not None and amount != "-0" and -(2**63) <= int(amount) < 2**63,
                "Canonical exact signed Q64 decimal required")
            amounts.append(amount)
        stress = None if row["stress_points"] is None else integer(row["stress_points"], "stress", 0, 2**31 - 1)
        return cls(amounts[0], amounts[1], stress)


def native_vitals(snapshot: object) -> Vitals:
    amounts: list[str] = []
    for key in ("played_character_gold", "played_character_prestige"):
        row = mapping(field(snapshot, key), "actual native " + key)
        require(set(row) == {"raw", "scale"}, "Exact native Q fields required")
        integer(row["scale"], "native scale", 100000, 100000)
        amounts.append(str(integer(row["raw"], "actual Q64", -(2**63), 2**63 - 1)))
    actor = mapping(field(snapshot, "played_character"), "actual native actor")
    stress = None if actor.get("stress_points") is None else integer(actor["stress_points"], "actual native stress", 0, 2**31 - 1)
    return Vitals(amounts[0], amounts[1], stress)


def _saved_q(value: object) -> str:
    require(type(value) is str, "Saved decimal scalar required")
    try:
        amount = Decimal(str(value)) * 100000
    except InvalidOperation as error:
        raise ValueError("Invalid saved currency") from error
    require(amount.is_finite() and amount == amount.to_integral_value() and -(2**63) <= amount < 2**63, "Saved currency exceeds Q64 precision")
    return str(int(amount))


@dataclass(frozen=True)
class SavedVitalsSource:
    """Internal corroboration assembled only after both native and Save guards."""

    melted_save: Pin
    frame: Frame
    readback_actor_id: int
    readback_date_raw: int
    native: Vitals
    game_version: str
    exe_sha256: str


def saved_vitals(melted: Path, player_id: str, *, source: SavedVitalsSource | None = None) -> Vitals:
    bodies = [body for identity, body in records(melted, ("living",)) if identity == player_id]
    require(len(bodies) == 1, "One exact saved actor required")
    alive = structured(one(parse_block(bodies[0][bodies[0].index("{"):]), "alive_data"), "alive data")
    gold_value = one(alive, "gold", required=False)
    if gold_value is None:
        # R19's qualified 1.20.0.4 Save omits the entire gold block at zero.
        # This is not a generic missing-field default: two independently bound
        # native reads and the original Save/readback scene must corroborate it.
        require(isinstance(source, SavedVitalsSource), "Missing saved gold requires qualified same-scene zero corroboration")
        if source is None:
            raise ValueError("Missing saved gold source")
        require((source.game_version, source.exe_sha256) == ZERO_GOLD_GAME,
            "Saved zero-gold omission requires the qualified exact CK3 source")
        reference = checked_pin(source.melted_save, "saved zero-gold original melt")
        require(Path(reference["path"]).resolve() == melted.resolve(), "Saved zero-gold melt source differs")
        require(decimal_id(player_id, "saved actor") == str(integer(source.readback_actor_id, "readback actor", 1)) ==
            str(integer(source.frame.player_id, "native actor", 1)) and
            integer(source.readback_date_raw, "readback date") == integer(source.frame.date_raw, "native date"),
            "Saved zero-gold actor/date differs from the verified native frame")
        native = Vitals.parse(source.native.to_json())
        require(native.gold_raw == "0", "Missing saved gold is not corroborated by native zero")
        gold_raw = "0"
    else:
        gold = structured(gold_value, "saved gold")
        gold_raw = _saved_q(scalar(one(gold, "value"), "saved gold value"))
    prestige = structured(one(alive, "prestige"), "saved prestige")
    stress_value = one(alive, "stress", required=False)
    # Absence is unavailable, not an invented zero. The fixture requests nonzero input.
    stress: int | None = None
    if stress_value is not None:
        raw = scalar(stress_value, "saved stress")
        require(re.fullmatch(r"0|[1-9][0-9]*", raw) is not None, "Exact saved stress integer required")
        stress = integer(int(raw), "saved stress points", 0, 2**31 - 1)
    return Vitals(gold_raw, _saved_q(scalar(one(prestige, "currency"), "saved prestige currency")), stress)


def _value(values: dict[str, SavedVariable], name: str) -> int:
    require(name in values, "Missing actual saved variable: " + name)
    return values[name].integer_value(name)


def _optional_value(values: dict[str, SavedVariable], name: str) -> int | None:
    return _value(values, name) if name in values else None


def _boolean(values: dict[str, SavedVariable], name: str) -> bool:
    if name not in values:
        return False
    variable = values[name]
    require(variable.kind == "boolean" and variable.raw_identity == "1" and variable.flag is None, "Exact saved true boolean required: " + name)
    return True


@dataclass(frozen=True)
class ThresholdObservation:
    frame: Frame
    sample: CheckpointSample
    inputs: SavedInputs
    saved: Vitals
    native: Vitals
    modifiers: tuple[str, ...]

    @property
    def values(self) -> dict[str, SavedVariable]:
        return next(item for item in self.inputs.artifacts if item.artifact_id == self.inputs.target_id).variables

    def to_json(self) -> Object:
        return {"sample": self.sample.to_json(), "saved_inputs": self.inputs.to_json(), "saved_vitals": self.saved.to_json(),
            "native_vitals": self.native.to_json(), "saved_artifact_modifiers": list(self.modifiers),
            "authority": "historical-save-plus-same-paused-date-native-read", "effective_health_or_AI_pass": False}


def _native(reference: object, *, context: object, manifest: object) -> tuple[Frame, dict[str, object], object]:
    source = checked_pin(reference, "original native row")
    rows = array(field(raw_object(Path(source["path"])), "rows"), "native rows")
    require(len(rows) == 1, "Exactly one native row required")
    row = mapping(rows[0], "original native row")
    require(row.get("ok") is True and row.get("error") is None, "Successful original native row required")
    snapshot = field(row, "result") if field(field(row, "plan"), "tool") == "ck3_take_snapshot" else field(row, "after_snapshot")
    frame = Frame.parse(snapshot, run_id=text(field(context, "run_id"), "run"), machine_id=text(field(manifest, "machine_id"), "machine"), manifest=manifest)
    return frame, row, snapshot


def consume_observation(record: object, *, context: object, manifest: object, reviewer: str) -> ThresholdObservation:
    row = mapping(record, "threshold checkpoint")
    require(set(row) == set(ThresholdCheckpoint.__required_keys__) and
        row["run_id"] == field(context, "run_id") and row["machine_id"] == field(manifest, "machine_id") and row["reviewer"] == reviewer, "Closed checkpoint scene required")
    frame, original, snapshot = _native(row["frame_native"], context=context, manifest=manifest)
    require(field(field(original, "plan"), "tool") == "ck3_take_snapshot", "Actual original paused snapshot required")
    inputs, _ = verify_readback(row["response"], run_id=text(row["run_id"], "run"), machine_id=text(row["machine_id"], "machine"),
        reviewer=reviewer, frame=frame, source_save=declared_pin(row["source_save"], "actual Save"))
    item_frame, item_row, item_snapshot = _native(row["item_native"], context=context, manifest=manifest)
    require((item_frame.pid, item_frame.player_id, item_frame.generation_decimal, item_frame.date_raw) ==
        (frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) and field(field(item_row, "plan"), "tool") == core.ITEM, "Independent original native item read crossed scene")
    native = field(item_row, "result")
    require(field(native, "available") is True and field(native, "read_only") is True and field(native, "loaded_source_pins_verified") is True and
        field(native, "personally_owned") is True and field(native, "inventory_artifact") is True and type(field(native, "equipped")) is bool and
        native_id(field(native, "requested_artifact_id"), "target", allow_zero=True) == int(inputs.target_id) and
        integer(field(native, "played_character_id"), "item actor", 1) == frame.player_id and integer(field(native, "date_raw"), "item date", 1) == frame.date_raw,
        "Native ownership/equipment source unavailable")
    owned = {str(native_id(item, "owned item", allow_zero=True)) for item in array(field(native, "owned_ids"), "native inventory")}
    require({item.artifact_id for item in inputs.artifacts} <= owned, "Actual native materials/target disappeared")
    target = next(item for item in inputs.artifacts if item.artifact_id == inputs.target_id)
    melted_reference = checked_pin(field(row["response"], "melted_save"), "already verified melted save")
    melted = Path(melted_reference["path"])
    target_blocks = [body for identity, body in records(melted, ("artifacts", "artifacts")) if identity == inputs.target_id]
    require(len(target_blocks) == 1, "Exactly one saved target record required")
    modifiers = one(parse_block(target_blocks[0][target_blocks[0].index("{"):]), "modifiers", required=False)
    modifier_entries = () if modifiers is None else structured(modifiers, "artifact modifiers")
    require(all(entry.key is None for entry in modifier_entries), "Anonymous saved native artifact modifiers required")
    names = tuple(scalar(entry.value, "artifact modifier") for entry in modifier_entries)
    native_values = native_vitals(snapshot)
    require(native_values == native_vitals(item_snapshot), "Independent native paused vitals differ")
    game = field(manifest, "game")
    source = SavedVitalsSource(melted_reference, frame,
        integer(field(row["response"], "actor_character_id"), "readback actor", 1),
        integer(field(row["response"], "date_raw"), "readback date"), native_values,
        text(field(game, "version"), "verified game version"), text(field(game, "exe_sha256"), "verified game EXE SHA").lower())
    actual = ThresholdObservation(frame, CheckpointSample.from_saved(target, inputs, native_equipped=field(native, "equipped") is True), inputs,
        saved_vitals(melted, inputs.player_id, source=source), native_values, names)
    require(actual.saved.gold_raw == actual.native.gold_raw and actual.saved.prestige_raw == actual.native.prestige_raw,
        "Saved/native paused wallet changed across the observation")
    require(actual.saved.stress is None or actual.native.stress is None or actual.saved.stress == actual.native.stress, "Saved/native stress disagree")
    require(row["projection"] is None or same_json(row["projection"], actual.to_json()), "Persisted threshold projection differs from actual sources")
    return actual


def validate_contract(context: object) -> core.Contract:
    require(field(context, "product") == "living-artifacts" and field(context, "case") == CASE, "Select actual threshold_suppression case")
    config = mapping(field(context, "case_contract"), "threshold contract")
    require(same_json(config, read(TOOLS / CONTRACT_NAME)), "Canonical threshold contract required")
    integer(config["schema_version"], "schema", 1, 1)
    spec = field(context, "case_spec")
    require(field(spec, "id") == CASE, "Selected public case spec differs")
    declared = {text(item, "tool") for item in array(field(spec, "required_mcp_tools"), "declared tools")}
    require(set(core.REQUIRED_TOOLS) <= declared, "Declare existing Session tools")
    require(core.ITEM in array(field(spec, "opt_in_read_only_mcp_tools"), "read-only tools"), "Independent native item read opt-in required")
    for name, expected in core.REQUIRED_OPT_INS.items():
        require(field(spec, name) is expected, "Original action opt-in missing")
    return core.Contract(47, 480, 60, CHECKS, tuple(text(item, "deferred") for item in array(config["deferred_checks"], "deferred")))


def prepare_case(context: object) -> Object:
    validate_contract(context)
    return prepare_inputs(context)


def _last_call(session: core.Session) -> Pin:
    return pin(session.client.output / f"xalw-core-{session.sequence:04d}.actual-results.json")


def _observe(session: core.Session, target: str | None) -> tuple[ThresholdObservation, Pin]:
    session.snapshot()
    original = session.last_native_record
    if original is None:
        raise ValueError("Original native snapshot missing")
    readback = session.checkpoint_readback(target)
    inputs, refs = verify_readback(readback.response, run_id=session.run_id, machine_id=session.machine_id, reviewer=session.client.operator_reviewer,
        frame=readback.frame, source_save=readback.source_save)
    require(target is None or inputs.target_id == target, "Actual target reference changed")
    session.observe_item(inputs.target_id)
    row: ThresholdCheckpoint = {"run_id": session.run_id, "machine_id": session.machine_id, "reviewer": session.client.operator_reviewer,
        "frame_native": original, "source_save": readback.source_save, "response": object_value(readback.response), "item_native": _last_call(session), "projection": None}
    actual = consume_observation(row, context=session.context, manifest=session.client.manifest, reviewer=session.client.operator_reviewer)
    row["projection"] = actual.to_json()
    reference = write_once(session.client.output / f"threshold-checkpoint-{session.checkpoint_observations:02d}.json", row)
    session.refs.extend((*refs, reference))
    return actual, reference


def _native_files(output: Path) -> dict[str, Pin]:
    return {path.name: pin(path) for path in sorted((*output.glob("xalw-core-*.actual-results.json"), *output.glob("case-snapshot-*.actual-results.json")))}


def _action(session: core.Session, target: str, option: str) -> Pin:
    session.open_management(target)
    session.management_choice("xalw.10", option)
    before = _last_call(session)
    refs_before = len(session.refs)
    session.select_management("xalw.10", option, next_event=None)
    submissions: list[Pin] = []
    for ref in session.refs[refs_before:]:
        if ref["path"].endswith(".actual-results.json"):
            _, row, _ = _native(ref, context=session.context, manifest=session.client.manifest)
            if field(field(row, "plan"), "tool") == "ck3_select_event_option":
                submissions.append(ref)
    require(len(submissions) == 1, "Exactly one original training/suppression intent required")
    evidence: ActionEvidence = {"option": option, "before_event": before, "submission": submissions[0]}
    return write_once(session.client.output / ("threshold-action-" + option.rsplit(".", 1)[1] + ".json"), evidence)


def _action_proof(reference: object, option: str, *, context: object, manifest: object, frame: Frame) -> None:
    row = read(Path(checked_pin(reference, "original action proof")["path"]))
    require(set(row) == set(ActionEvidence.__required_keys__) and row["option"] == option, "Closed actual action proof required")
    before, query, _ = _native(row["before_event"], context=context, manifest=manifest)
    current = field(field(query, "result"), "current_event_window_context")
    instance = integer(field(current, "current_event_instance_id"), "actual instance", 1)
    choice = management_choice(field(query, "result"), frame=before, instance_id=instance, event_key="xalw.10", option_key=option)
    after, submitted, _ = _native(row["submission"], context=context, manifest=manifest)
    require((before.pid, before.player_id, before.generation_decimal, before.date_raw) == (frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) ==
        (after.pid, after.player_id, after.generation_decimal, after.date_raw) and field(field(query, "plan"), "tool") == "ck3_query_current_event_window_context_v1" and
        field(field(submitted, "plan"), "tool") == "ck3_select_event_option", "Original action crossed scene/tool")
    args = field(field(submitted, "plan"), "args")
    require(integer(field(args, "event_instance_id"), "submitted instance", 1) == choice.instance_id and
        integer(field(args, "option_number"), "source native option", 1) == source_option_index("xalw.10", option) + 1, "Original source option differs")


def _check(check_id: str, passed: bool, message: str, refs: list[Pin], observed: Object) -> CheckResult:
    return core._check(check_id, "PASS" if passed else "FAIL", None if passed else message, refs, observed)


def evaluate(context: object, *, manifest: object, reviewer: str, journal: object) -> list[CheckResult]:
    validate_contract(context)
    row = mapping(journal, "threshold journal")
    require(set(row) == set(ThresholdJournal.__required_keys__), "Closed threshold journal required")
    refs = [checked_pin(raw, "threshold checkpoint") for raw in array(row["checkpoints"], "seven checkpoint refs")]
    require(len(refs) == 7, "Seven actual independent Save readbacks required")
    observations = [consume_observation(read(Path(ref["path"])), context=context, manifest=manifest, reviewer=reviewer) for ref in refs]
    first = observations[0]
    require(len({ref["path"] for ref in refs}) == 7, "Cannot reuse an observation")
    for actual, date, days in zip(observations, DATES, DAYS, strict=True):
        require((actual.frame.pid, actual.frame.player_id, actual.frame.generation_decimal, actual.sample.artifact_id, actual.sample.owner_id) ==
            (first.frame.pid, first.frame.player_id, first.frame.generation_decimal, first.sample.artifact_id, first.sample.owner_id) and
            actual.frame.date_raw - first.frame.date_raw == days * 24 and actual.sample.date_literal == date, "Crossed actual target/actor/calendar")
    require((first.sample.level, first.sample.xp, first.sample.pending, first.sample.growth_sequence, first.sample.equipped) == (10, 992, 0, 0, False) and
        _value(first.values, "xalw_suppression_chain") == 0 and _optional_value(first.values, "xalw_growth_suppressed_until") is None and
        _value(first.values, "xalw_curse_1") == 1 and _value(first.values, "xalw_curse_rank_1") == 2 and
        not _boolean(first.inputs.player_variables, "xalw_training_cooldown"), "Initial inputs differ; no terminal credit")
    originals = mapping(row["native_records"], "complete native file closure")
    require(same_json(originals, _native_files(Path(text(field(context, "output"), "output")))), "Original action/snapshot file closure differs")
    selected: list[str] = []
    equip: list[bool] = []
    event_keys: dict[tuple[int, int], str] = {}
    for raw in originals.values():
        # Keep an original unavailable read / proven pre-intent inventory refusal
        # in the closure. It is not a successful native action. Session owns its
        # source-bound fallback and unknown-intent policy; do not reject that route.
        original_rows = array(field(raw_object(Path(checked_pin(raw, "original native audit file")["path"])), "rows"), "native audit rows")
        require(len(original_rows) == 1, "Exactly one original native audit row required")
        native_row = mapping(original_rows[0], "native audit row")
        plan = field(native_row, "plan")
        tool = field(plan, "tool")
        if tool == "ck3_query_current_event_window_context_v1" and native_row.get("ok") is True:
            frame, _, _ = _native(raw, context=context, manifest=manifest)
            event = mapping(field(field(native_row, "result"), "current_event_window_context"), "queried event")
            if event.get("status") == "available":
                require(integer(field(event, "date_raw"), "queried actual event date", 1) == frame.date_raw and
                    integer(field(event, "schema_version"), "queried event version", 1, 1) == 1, "Event audit crossed actual native date/schema")
                event_keys[(frame.date_raw, integer(field(event, "current_event_instance_id"), "queried instance", 1))] = text(field(event, "event_definition_key"), "queried event definition")
        elif tool == "ck3_select_event_option":
            frame, _, _ = _native(raw, context=context, manifest=manifest)
            args = field(plan, "args")
            number = integer(field(args, "option_number"), "original selected native index", 1)
            key = event_keys.get((frame.date_raw, integer(field(args, "event_instance_id"), "selected instance", 1)))
            require(key is not None, "Original event selection lacks its actual native definition query")
            if key in ("xalw.10", "xalw.11", "xalw.12"):
                selected.append(str(number))
            else:
                require(frame.date_raw != first.frame.date_raw + 16 * 24, "Unrelated event entered the same paused cost window")
        elif tool == core.EQUIP:
            _native(raw, context=context, manifest=manifest)
            desired = field(field(plan, "args"), "desired_equipped")
            require(type(desired) is bool, "Actual equip boolean required")
            equip.append(desired is True)
    require(selected == [str(source_option_index("xalw.12", "xalw.12.open") + 1), str(source_option_index("xalw.10", "xalw.10.train") + 1),
        str(source_option_index("xalw.12", "xalw.12.open") + 1), str(source_option_index("xalw.10", "xalw.10.suppress") + 1)] and equip == [True, False, True],
        "Extra/missing feeding, permission, training, suppression or equipment intent")
    grown, trained, suppressed, removed, restored, final = observations[1:]
    _action_proof(row["train"], "xalw.10.train", context=context, manifest=manifest, frame=grown.frame)
    _action_proof(row["suppress"], "xalw.10.suppress", context=context, manifest=manifest, frame=trained.frame)
    anchor = _value(first.inputs.player_variables, "xalw_fixture_initial_day")
    deadline = anchor + 16 + 90
    observed: Object = {"actual_natural_days": 47, "actual_saved_observations": 7, "target_artifact_id": first.sample.artifact_id,
        "stress_adjustment_formula": "unavailable; actual same-paused-date saved/native delta only", "effective_health_credit": False,
        "expiry_renewal_transfer_NPC_credit": False, "initial": first.to_json(), "grown": grown.to_json(), "trained": trained.to_json(),
        "suppressed": suppressed.to_json(), "final": final.to_json()}
    checks: list[CheckResult] = []
    checks.append(_check(CHECKS[0], (grown.sample.level, grown.sample.xp, grown.sample.pending, grown.sample.growth_sequence, grown.sample.equipped) ==
        (11, 0, 0, 1, True), "Monthly +8 did not automatically resolve L10/992 to L11/0", refs, observed))
    blood = _value(grown.values, "xalw_curse_rank_1")
    projected = _value(grown.values, "xalw_curse_1") == 1 and blood in (2, 3) and f"xalw_content_blood_1_{blood}_modifier" in grown.modifiers and "xalw_hunger_1_modifier" in grown.modifiers
    checks.append(_check(CHECKS[1], projected, "Actual saved heavy blood curse / L11 hunger projection missing", refs, observed))
    train_ok = (trained.sample.equipped and (trained.sample.level, trained.sample.xp, trained.sample.pending, trained.sample.growth_sequence) == (11, 25, 0, 1) and
        int(trained.saved.prestige_raw) - int(grown.saved.prestige_raw) == -50 * 100000 and trained.saved.gold_raw == grown.saved.gold_raw and _boolean(trained.inputs.player_variables, "xalw_training_cooldown"))
    checks.append(_check(CHECKS[2], train_ok, "Actual training XP/prestige/cooldown differs", refs, observed))
    suppress_ok = ((suppressed.sample.level, suppressed.sample.xp, suppressed.sample.pending, suppressed.sample.growth_sequence) == (11, 25, 0, 1) and
        int(suppressed.saved.gold_raw) - int(trained.saved.gold_raw) == -75 * 100000 and int(suppressed.saved.prestige_raw) - int(trained.saved.prestige_raw) == -50 * 100000 and
        _value(suppressed.values, "xalw_suppression_chain") == 1 and _value(suppressed.values, "xalw_growth_suppressed_until") == deadline and _value(suppressed.values, "xalw_suppression_timer_sequence") == 1 and
        "xalw_hunger_2_modifier" in suppressed.modifiers)
    for index, before, after in ((3, grown, trained), (5, trained, suppressed)):
        if before.saved.stress is None or after.saved.stress is None or before.native.stress is None or after.native.stress is None:
            checks.append(core._check(CHECKS[index], "BLOCKED", "Actual saved/native stress field unavailable; missing is not zero", refs, observed))
        else:
            delta = after.saved.stress - before.saved.stress
            details = dict(observed)
            details["actual_stress_delta_points"] = delta
            checks.append(_check(CHECKS[index], delta >= 0 and delta == after.native.stress - before.native.stress,
                "Actual stress difference is inconsistent/reversed; no adjusted formula claimed", refs, details))
    checks.append(_check(CHECKS[4], suppress_ok, "Actual first suppression costs/90-day deadline/chain/hunger differ", refs, observed))
    equipment_ok = not removed.sample.equipped and restored.sample.equipped and all(
        (item.sample.level, item.sample.xp, item.sample.pending, item.sample.growth_sequence, _value(item.values, "xalw_growth_suppressed_until"), _value(item.values, "xalw_suppression_chain"),
         _value(item.values, "xalw_suppression_timer_sequence"), item.saved.gold_raw, item.saved.prestige_raw, item.saved.stress) ==
        (11, 25, 0, 1, deadline, 1, 1, suppressed.saved.gold_raw, suppressed.saved.prestige_raw, suppressed.saved.stress) for item in (removed, restored))
    checks.append(_check(CHECKS[6], equipment_ok, "Unequip/re-equip reset suppression or charged/refunded its actual cost", refs, observed))
    checks.append(_check(CHECKS[7], final.sample.equipped and (final.sample.level, final.sample.xp, final.sample.pending, final.sample.growth_sequence) == (11, 25, 0, 1) and
        final.sample.last_month == 12803 and _value(final.values, "xalw_growth_suppressed_until") == deadline and _value(final.values, "xalw_suppression_chain") == 1 and
        _value(final.values, "xalw_suppression_timer_sequence") == 1 and "xalw_hunger_2_modifier" in final.modifiers,
        "Suppressed equipped target gained monthly XP or lost its existing timer", refs, observed))
    return sorted(checks, key=lambda check: CHECKS.index(check["case_id"]))


class ThresholdResult(TypedDict):
    schema: Literal["living-artifacts-threshold-case-result-v1"]
    product: Literal["living-artifacts"]
    case: Literal["threshold_suppression"]
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
    business_pass: Literal[False]
    product_release_pass: Literal[False]
    normal_close_owner: Literal["shared entry/CaseClient"]
    normal_close_pending: Literal[True]


def _overall(checks: list[CheckResult]) -> Literal["PASS", "FAIL", "BLOCKED"]:
    return "FAIL" if any(check["status"] == "FAIL" for check in checks) else "BLOCKED" if any(check["status"] == "BLOCKED" for check in checks) else "PASS"


def run_case(context: object, client: object) -> Object:
    contract = validate_contract(context)
    if not isinstance(client, CasePort):
        raise ValueError("Actual shared CaseClient required")
    session = core.Session(context, client, contract)
    saves: list[Pin] = []
    journal: ThresholdJournal = {"checkpoints": [], "train": None, "suppress": None, "native_records": {}}
    status: Literal["PASS", "FAIL", "BLOCKED"] = "BLOCKED"
    error: str | None = None
    checks: list[CheckResult] = []
    try:
        session.refs.extend(prepared_sources(context, client.state))
        session.snapshot()
        initial, reference = _observe(session, None)
        saves.append(reference)
        require(initial.sample.date_literal == DATES[0] and (initial.sample.level, initial.sample.xp, initial.sample.equipped) == (10, 992, False), "Initial real threshold input differs")
        target = initial.sample.artifact_id
        session.equip(target, True)
        for _ in range(16):
            session.advance_one()
        grown, reference = _observe(session, target)
        saves.append(reference)
        if (grown.sample.level, grown.sample.xp, grown.sample.growth_sequence) != (11, 0, 1):
            raise core.CaseFailed("Automatic L11 growth failed; no training/suppression intent permitted")
        journal["train"] = _action(session, target, "xalw.10.train")
        trained, reference = _observe(session, target)
        saves.append(reference)
        if (trained.sample.level, trained.sample.xp) != (11, 25):
            raise core.CaseFailed("Actual training XP failed; no suppression intent permitted")
        journal["suppress"] = _action(session, target, "xalw.10.suppress")
        suppressed, reference = _observe(session, target)
        saves.append(reference)
        require(_value(suppressed.values, "xalw_suppression_chain") == 1, "Suppression did not bind actual target")
        session.equip(target, False)
        _, reference = _observe(session, target)
        saves.append(reference)
        session.equip(target, True)
        _, reference = _observe(session, target)
        saves.append(reference)
        for _ in range(31):
            session.advance_one()
        _, reference = _observe(session, target)
        saves.append(reference)
        journal["checkpoints"] = saves
        journal["native_records"] = _native_files(client.output)
        checks = evaluate(context, manifest=client.manifest, reviewer=client.operator_reviewer, journal=journal)
        status = _overall(checks)
        if status != "PASS":
            error = "One or more independent threshold checks did not pass"
    except core.CaseFailed as failure:
        status, error = "FAIL", str(failure)
    except (core.CaseBlocked, ValueError, OSError, TimeoutError, KeyError, StopIteration) as failure:
        error = type(failure).__name__ + ": " + str(failure)
    journal["checkpoints"] = saves
    journal["native_records"] = _native_files(client.output)
    journal_ref = write_once(client.output / "threshold-evidence-journal.json", journal)
    if not checks:
        failed_cell = CHECKS[0] if error is not None and "Automatic L11 growth failed" in error else CHECKS[2]
        checks = [core._check(check, "FAIL" if status == "FAIL" and check == failed_cell else "BLOCKED",
            error if check == failed_cell or status != "FAIL" else "Not reached after the recorded original failure: " + str(error), [*session.refs, journal_ref], {}) for check in CHECKS]
    if session.start is not None and session.owner is not None:
        session.days = (session.current().date_raw - session.start.date_raw) // 24
    result: ThresholdResult = {"schema": "living-artifacts-threshold-case-result-v1", "product": "living-artifacts", "case": "threshold_suppression",
        "run_id": session.run_id, "machine_id": session.machine_id, "reviewer": client.operator_reviewer, "observed_at_utc": utc_now(), "status": status,
        "checks": checks, "journal": journal_ref, "error": error, "actual_natural_days": session.days, "actual_public_calls_budgeted": session.calls,
        "actual_saved_observations": session.checkpoint_observations, "original_action_unknown": session.original_action_unknown,
        "case_contract_qualified": status == "PASS", "business_pass": False, "product_release_pass": False,
        "normal_close_owner": "shared entry/CaseClient", "normal_close_pending": True}
    write_once(client.output / RESULT_NAME, result)
    return object_value(result)


def verify_case(context: object) -> Object:
    contract = validate_contract(context)
    output = Path(text(field(context, "output"), "output"))
    if not (output / RESULT_NAME).is_file():
        return {"status": "NOT_RUN", "case_contract_qualified": False, "business_pass": False, "product_release_pass": False}
    result = read(output / RESULT_NAME)
    require(set(result) == set(ThresholdResult.__required_keys__), "Closed threshold result required")
    prepared_sources(context, Path(text(field(context, "state_dir"), "state")))
    runtime = read(Path(checked_pin(field(context, "runtime_manifest"), "runtime manifest")["path"]))
    require(result["schema"] == "living-artifacts-threshold-case-result-v1" and result["product"] == "living-artifacts" and result["case"] == CASE and
        result["run_id"] == field(context, "run_id") and result["machine_id"] == field(runtime, "machine_id") and
        result["status"] in ("PASS", "FAIL", "BLOCKED") and result["business_pass"] is False and result["product_release_pass"] is False and
        result["normal_close_owner"] == "shared entry/CaseClient" and result["normal_close_pending"] is True, "Retained threshold scene/scope differs")
    days = integer(result["actual_natural_days"], "actual days", 0)
    integer(result["actual_public_calls_budgeted"], "actual calls", 1, contract.max_calls)
    saves = integer(result["actual_saved_observations"], "actual saves", 0, 7)
    require(type(result["original_action_unknown"]) is bool, "Exact unknown status required")
    stamp(result["observed_at_utc"])
    checks = array(result["checks"], "actual checks")
    require(len(checks) == len(CHECKS) and [field(check, "case_id") for check in checks] == list(CHECKS), "Every independent check required")
    journal = read(Path(checked_pin(result["journal"], "retained threshold journal")["path"]))
    complete = saves == 7 and days == 47 and result["original_action_unknown"] is False
    if complete:
        actual = evaluate(context, manifest=runtime, reviewer=text(result["reviewer"], "reviewer"), journal=journal)
        require(same_json(checks, actual) and result["status"] == _overall(actual), "Retained threshold checks differ from actual source recomputation")
    else:
        require(result["status"] != "PASS", "Incomplete/unknown attempt cannot pass")
        for check in checks:
            require(set(mapping(check, "incomplete check")) == set(CheckResult.__required_keys__) and field(check, "status") in ("FAIL", "BLOCKED") and
                field(check, "evidence_scope") == "fixture_live" and field(check, "observed") == {},
                "Incomplete attempt cannot introduce unsupported independent PASS observations")
            text(field(check, "reason"), "specific incomplete check reason")
            for reference in array(field(check, "evidence"), "retained incomplete evidence"):
                checked_pin(reference, "incomplete evidence", allow_empty=True)
        require(result["status"] == ("FAIL" if any(field(check, "status") == "FAIL" for check in checks) else "BLOCKED"), "Incomplete overall status differs from checks")
    require(result["case_contract_qualified"] is (result["status"] == "PASS"), "Qualification differs")
    if result["status"] == "PASS":
        require(result["error"] is None, "PASS cannot carry an error")
    else:
        text(result["error"], "actual failure")
    return result
