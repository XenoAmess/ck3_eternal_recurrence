"""Reconsume original Save/melt/native files, then compare a real cold Save."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from acceptance_contract import Frame, Object, Pin, array, field, integer, mapping, native_id, object_value, read, require, text
from checkpoint_artifacts import SavedArtifact, SavedInputs, SavedVariable
from checkpoint_callback import CheckpointSample, checked_pin, verify_readback
from checkpoint_producer import declared_pin, raw_object
from living_artifacts_model import FEEDING_XP, PERSONAL_TYPES, Rarity

CORE_FIELDS = {"schema_version", "run_id", "machine_id", "observed_at_utc", "native_date_raw", "sample", "saved_inputs",
               "readback_response", "original_native_frame_record", "expected_material_rarities", "current_native_artifact_variable_query"}
THRESHOLD_FIELDS = {"run_id", "machine_id", "reviewer", "frame_native", "source_save", "response", "item_native", "projection"}


class ColdCheckpoint(TypedDict):
    schema: Literal["living-artifacts-cold-checkpoint-v1"]
    run_id: str
    machine_id: str
    reviewer: str
    source_save: Pin
    response: Object
    frame_native: Pin
    save_native: Pin
    item_native: Pin
    expected_material_rarities: list[Rarity]
    projection: Object


class PersistenceCheck(TypedDict):
    case_id: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    evidence_scope: Literal["saved_campaign_cold"]
    reason: str | None
    observed: Object


def rarities(value: object) -> tuple[Rarity, ...]:
    result: list[Rarity] = []
    for raw in array(value, "actual surviving material rarities"):
        if raw == "common" and type(raw) is str:
            result.append("common")
        elif raw == "masterwork" and type(raw) is str:
            result.append("masterwork")
        elif raw == "famed" and type(raw) is str:
            result.append("famed")
        elif raw == "illustrious" and type(raw) is str:
            result.append("illustrious")
        else:
            raise ValueError("Unknown native surviving rarity")
    require(len(result) == len(set(result)), "Repeated native surviving rarity")
    return tuple(result)


def native_row(reference: object, *, run_id: str, machine_id: str, manifest: object,
               tool: str) -> tuple[Frame, dict[str, object], object, Pin]:
    source = checked_pin(reference, "original native " + tool)
    rows = array(field(raw_object(Path(source["path"])), "rows"), "original native rows")
    require(len(rows) == 1, "Exactly one retained original native row required")
    row = mapping(rows[0], "original native row")
    require(field(field(row, "plan"), "tool") == tool and row.get("ok") is True and row.get("error") is None,
            "Original native operation differs or failed: " + tool)
    snapshot = field(row, "result") if tool == "ck3_take_snapshot" else field(row, "after_snapshot")
    frame = Frame.parse(snapshot, run_id=run_id, machine_id=machine_id, manifest=manifest)
    return frame, row, snapshot, source


@dataclass(frozen=True)
class ObservedCheckpoint:
    run_id: str
    frame: Frame
    sample: CheckpointSample
    inputs: SavedInputs
    load_save: Pin
    response: Object
    remaining: tuple[Rarity, ...]
    evidence: tuple[Pin, ...]
    log_streams: tuple[Pin, Pin]

    @property
    def artifact(self) -> SavedArtifact:
        return next(item for item in self.inputs.artifacts if item.artifact_id == self.inputs.target_id)

    def projection(self) -> Object:
        return {"sample": self.sample.to_json(), "saved_inputs": self.inputs.to_json(),
                "current_native_artifact_variable_query": False, "cold_reload_qualification": False}


def consume_checkpoint(record: object, *, run_id: str, machine_id: str, reviewer: str, manifest: object,
                       save_native: object, item_native: object) -> ObservedCheckpoint:
    """All source formats enter the same actual callback/native consumer path."""
    row = mapping(record, "source checkpoint observation")
    require(row.get("run_id") == run_id and row.get("machine_id") == machine_id, "Checkpoint crossed its original run/machine")
    if set(row) == CORE_FIELDS:
        integer(row["schema_version"], "original observer schema", 2, 2)
        require(row["current_native_artifact_variable_query"] is False, "Saved observation must not claim a current variable getter")
        response = row["readback_response"]
        original_frame = row["original_native_frame_record"]
        remaining = rarities(row["expected_material_rarities"])
    elif set(row) == THRESHOLD_FIELDS:
        require(row["reviewer"] == reviewer and row["item_native"] == item_native, "Threshold original reviewer/item source differs")
        response, original_frame, remaining = row["response"], row["frame_native"], tuple(FEEDING_XP)
    else:
        require(set(row) == set(ColdCheckpoint.__required_keys__) and row.get("schema") == "living-artifacts-cold-checkpoint-v1" and
                row["reviewer"] == reviewer and row["save_native"] == save_native and row["item_native"] == item_native,
                "Closed original core/threshold/cold checkpoint observation required")
        response, original_frame = row["response"], row["frame_native"]
        remaining = rarities(row["expected_material_rarities"])
    save_frame, save_row, _, save_ref = native_row(save_native, run_id=run_id, machine_id=machine_id, manifest=manifest, tool="ck3_save_checkpoint")
    checkpoint = field(field(save_row, "result"), "checkpoint")
    require(field(checkpoint, "status") == "saved" and field(field(field(save_row, "result"), "materialization"), "available") is True,
            "Original actual Save was not materialized")
    # The original MCP save slot can later be overwritten. Its declared Pin
    # remains bound to the actual request and producer's retained raw copy.
    original_source = declared_pin({"path": field(checkpoint, "path"), "bytes": field(checkpoint, "size"), "sha256": field(checkpoint, "sha256")}, "actual original Save")
    if "source_save" in row:
        require(row["source_save"] == original_source, "Persisted checkpoint source differs from actual Save")
    require(integer(field(checkpoint, "date_raw"), "actual Save date") == save_frame.date_raw,
            "Actual saved checkpoint date differs from native frame")
    frame, _, _, frame_ref = native_row(original_frame, run_id=run_id, machine_id=machine_id, manifest=manifest, tool="ck3_take_snapshot")
    require((frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) ==
            (save_frame.pid, save_frame.player_id, save_frame.generation_decimal, save_frame.date_raw), "Original Save crossed paused observation identity/date")
    inputs, refs = verify_readback(response, run_id=run_id, machine_id=machine_id, reviewer=reviewer,
        frame=frame, source_save=original_source, expected_material_rarities=remaining)
    process = read(Path(checked_pin(field(response, "process_receipt"), "verified melt process")["path"]))
    request = read(Path(checked_pin(field(process, "request"), "verified original request")["path"]))
    require(field(request, "original_native_frame_record") == frame_ref and
            (field(request, "expected_target_id") is None or field(request, "expected_target_id") == inputs.target_id),
            "Original producer request does not bind this actual observation frame/target")
    item_frame, item_row, _, item_ref = native_row(item_native, run_id=run_id, machine_id=machine_id, manifest=manifest,
        tool="ck3_query_player_artifact_personal_use_v1")
    require((item_frame.pid, item_frame.player_id, item_frame.generation_decimal, item_frame.date_raw) ==
            (frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw), "Original item read crossed paused Save identity/date")
    native = field(item_row, "result")
    require(field(native, "available") is True and field(native, "read_only") is True and field(native, "loaded_source_pins_verified") is True and
            field(native, "personally_owned") is True and field(native, "inventory_artifact") is True and type(field(native, "equipped")) is bool and
            native_id(field(native, "requested_artifact_id"), "actual target", allow_zero=True) == int(inputs.target_id) and
            native_id(field(native, "played_character_id"), "item player") == frame.player_id and
            integer(field(native, "date_raw"), "item date") == frame.date_raw, "Actual native owner/equipment source is unavailable")
    owned = {str(native_id(item, "actual owned artifact", allow_zero=True)) for item in array(field(native, "owned_ids"), "actual inventory")}
    require({item.artifact_id for item in inputs.artifacts} <= owned, "Actual native inventory lost a saved input")
    target = next(item for item in inputs.artifacts if item.artifact_id == inputs.target_id)
    actual = ObservedCheckpoint(run_id, frame, CheckpointSample.from_saved(target, inputs, native_equipped=field(native, "equipped") is True), inputs,
        checked_pin(field(response, "source_save"), "retained original Save copy"), object_value(response), remaining, (*refs, frame_ref, save_ref, item_ref),
        (checked_pin(field(process, "stdout"), "verified producer stdout", allow_empty=True),
         checked_pin(field(process, "stderr"), "verified producer stderr", allow_empty=True)))
    if set(row) == CORE_FIELDS:
        require(row["sample"] == actual.sample.to_json() and row["saved_inputs"] == actual.inputs.to_json() and
                integer(row["native_date_raw"], "observer date") == frame.date_raw, "Original observer projection differs from actual sources")
    elif set(row) == set(ColdCheckpoint.__required_keys__):
        require(row["projection"] == actual.projection(), "Cold projection differs from actual producer/consumer sources")
    return actual


def variable_json(values: dict[str, SavedVariable], name: str) -> Object:
    value = values.get(name)
    return {"present": value is not None, "value": None if value is None else value.to_json()}


def feature_available(value: SavedVariable | None, name: str) -> bool:
    if value is None:
        return False
    if name == "xalw_feeding_imprint":
        return value.kind == "flag" and value.raw_identity is None and value.flag in PERSONAL_TYPES
    try:
        amount = value.integer_value(name)
    except ValueError:
        return False
    return amount > 0 if name == "xalw_growth_suppressed_until" else amount >= 0


def compare_persistence(before: ObservedCheckpoint, after: ObservedCheckpoint) -> tuple[PersistenceCheck, ...]:
    require(before.frame.date_raw == after.frame.date_raw and before.inputs.player_id == after.inputs.player_id and
            before.inputs.target_id == after.inputs.target_id and before.run_id != after.run_id and
            before.load_save["path"] != after.load_save["path"],
            "Cold comparison requires same saved actor/target/date and a new scene's actual Save")
    checks: list[PersistenceCheck] = []

    def append(key: str, matches: bool, available: bool, observed: Object) -> None:
        status: Literal["PASS", "FAIL", "BLOCKED"] = "BLOCKED" if not available else "PASS" if matches else "FAIL"
        checks.append({"case_id": key, "status": status, "evidence_scope": "saved_campaign_cold",
            "reason": None if status == "PASS" else "Source Save lacks a valid typed value for this feature" if status == "BLOCKED" else "Actual cold serialization differs from source",
            "observed": observed})

    before_sample, after_sample = before.sample.to_json(), after.sample.to_json()
    append("COLD-GROWTH-STATE", before_sample == after_sample, True, {"before": before_sample, "after": after_sample})
    before_vars, after_vars = before.artifact.variables, after.artifact.variables
    append("COLD-ALL-ARTIFACT-VARIABLES", before_vars == after_vars and before.artifact.name == after.artifact.name,
        True, {"before": before.artifact.to_json(), "after": after.artifact.to_json()})
    for key, name in (("COLD-SUPPRESSION-DEADLINE", "xalw_growth_suppressed_until"),
                      ("COLD-SUPPRESSION-TIMER-SEQUENCE", "xalw_suppression_timer_sequence"),
                      ("COLD-FEEDING-IMPRINT", "xalw_feeding_imprint")):
        a, b = variable_json(before_vars, name), variable_json(after_vars, name)
        append(key, a == b, feature_available(before_vars.get(name), name), {"variable": name, "before": a, "after": b,
            "scope": "actual saved presence/type/raw identity/flag; does not credit four independent rarity-specific imprints or timer firing"})
    append("COLD-SURVIVING-MATERIALS", before.remaining == after.remaining and
        {item.artifact_id for item in before.inputs.artifacts} == {item.artifact_id for item in after.inputs.artifacts},
        True, {"before": list(before.remaining), "after": list(after.remaining)})
    return tuple(checks)
