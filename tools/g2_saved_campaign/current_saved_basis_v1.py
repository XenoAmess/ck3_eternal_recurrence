"""Current saved facts, exact evidence and JSON; no request submission."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from types import FunctionType
from typing import Callable, Literal, Protocol, TypeAlias

from tools.g2_saved_campaign.file_stat_identity_v1 import (
    SCHEMA as STAT_SCHEMA, FileStatIdentityV1, parse_file_stat_identity_v1,
)

JsonValue: TypeAlias = "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
JsonObject: TypeAlias = dict[str, JsonValue]
MAX_SAFE = (1 << 53) - 1
BASIS_SCHEMA = "xar.current-saved-basis/v1"


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def record(value: object, fields: set[str] | None = None) -> dict[str, object]:
    if type(value) is not dict or not isinstance(value, dict):
        raise ValueError("object")
    out: dict[str, object] = {}
    for key, item in value.items():
        need(type(key) is str, "text object key")
        if not isinstance(key, str):
            raise ValueError("key")
        out[key] = item
    need(fields is None or set(out) == fields, "exact fields required")
    return out


def integer(value: object, minimum: int = 0, maximum: int = MAX_SAFE) -> int:
    if type(value) is not int:
        raise ValueError("integer")
    need(minimum <= value <= maximum, "integer range")
    return value


def exact_bool(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("exact bool")
    return value


def text(value: object) -> str:
    if type(value) is not str:
        raise ValueError("text")
    need(bool(value) and len(value) <= 32768, "nonempty bounded text")
    return value


def utc(value: object) -> str:
    result = text(value)
    try:
        date = datetime.fromisoformat(result.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("ISO observation time") from error
    need(date.tzinfo is not None and date.utcoffset() == timezone.utc.utcoffset(date), "UTC time")
    return result


def json_value(value: object) -> JsonValue:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        need(-MAX_SAFE <= value <= MAX_SAFE, "JSON integer loses precision")
        return value
    if type(value) is float:
        need(math.isfinite(value), "finite JSON number")
        return value
    if isinstance(value, list):
        return [json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in record(value).items()}
    raise ValueError("JSON type domain required; tuples are internal only")


def canonical_json_v1(value: object) -> bytes:
    return json.dumps(json_value(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def json_object(value: object) -> JsonObject:
    return {key: json_value(item) for key, item in record(value).items()}


def rows(value: object) -> list[object]:
    need(type(value) is list, "JSON array required")
    if not isinstance(value, list):
        raise ValueError("array")
    return list(value)


def digest(value: object) -> str:
    result = text(value)
    need(re.fullmatch("[0-9a-f]{64}", result) is not None, "canonical SHA256")
    return result


def unique_pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in items:
        need(key not in out, "duplicate JSON field")
        out[key] = value
    return out


def parse_json(raw: bytes) -> object:
    need(type(raw) is bytes, "bytes required")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)


@dataclass(frozen=True, slots=True)
class ExactRefV1:
    path: str
    bytes: int
    sha256: str

    def __post_init__(self) -> None:
        text(self.path)
        integer(self.bytes)
        digest(self.sha256)

    def to_wire(self) -> JsonObject:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


def parse_ref(value: object) -> ExactRefV1:
    row = record(value, {"path", "bytes", "sha256"})
    return ExactRefV1(text(row["path"]), integer(row["bytes"]), digest(row["sha256"]))


@dataclass(frozen=True, slots=True)
class CampaignOriginV1:
    start_date_raw: int
    target_date_raw: int
    target_days: int
    original_wall_origin_utc: str
    campaign_id: str

    def __post_init__(self) -> None:
        integer(self.start_date_raw)
        integer(self.target_date_raw)
        integer(self.target_days, 1)
        utc(self.original_wall_origin_utc)
        text(self.campaign_id)
        need(self.target_date_raw - self.start_date_raw == 24 * self.target_days,
             "original target/date relationship")

    def to_wire(self) -> JsonObject:
        return {"start_date_raw": self.start_date_raw, "target_date_raw": self.target_date_raw,
                "target_days": self.target_days, "original_wall_origin_utc": self.original_wall_origin_utc,
                "campaign_id": self.campaign_id}


def parse_origin(value: object) -> CampaignOriginV1:
    r = record(value, {"start_date_raw", "target_date_raw", "target_days",
                      "original_wall_origin_utc", "campaign_id"})
    return CampaignOriginV1(integer(r["start_date_raw"]), integer(r["target_date_raw"]),
        integer(r["target_days"], 1), utc(r["original_wall_origin_utc"]), text(r["campaign_id"]))


@dataclass(frozen=True, slots=True)
class SavedFrameV1:
    snapshot_id: str
    revision: int
    native_revision: int
    date_raw: int
    actor_character_id: int
    episode_run_id: str

    def __post_init__(self) -> None:
        text(self.snapshot_id)
        integer(self.revision, 1)
        integer(self.native_revision, 1)
        integer(self.date_raw)
        integer(self.actor_character_id, 1)
        text(self.episode_run_id)
        need(self.snapshot_id == "native:" + str(self.native_revision), "native snapshot identity")

    def to_wire(self) -> JsonObject:
        return {"snapshot_id": self.snapshot_id, "revision": self.revision,
                "native_revision": self.native_revision, "date_raw": self.date_raw,
                "actor_character_id": self.actor_character_id, "episode_run_id": self.episode_run_id}


def parse_frame(value: object) -> SavedFrameV1:
    r = record(value, {"snapshot_id", "revision", "native_revision", "date_raw",
                      "actor_character_id", "episode_run_id"})
    return SavedFrameV1(text(r["snapshot_id"]), integer(r["revision"], 1),
        integer(r["native_revision"], 1), integer(r["date_raw"]),
        integer(r["actor_character_id"], 1), text(r["episode_run_id"]))


@dataclass(frozen=True, slots=True)
class UnknownHistoricalRequestV1:
    sequence: int
    evidence_ref: ExactRefV1

    def __post_init__(self) -> None:
        integer(self.sequence, 1)

    def to_wire(self) -> JsonObject:
        return {"sequence": self.sequence, "evidence_ref": self.evidence_ref.to_wire(),
                "status": "unknown", "replayed": False, "cycle_credit": 0, "day_credit": 0}


def parse_unknown(value: object) -> UnknownHistoricalRequestV1:
    r = record(value, {"sequence", "evidence_ref", "status", "replayed", "cycle_credit", "day_credit"})
    need(r["status"] == "unknown" and r["replayed"] is False
         and integer(r["cycle_credit"]) == 0 and integer(r["day_credit"]) == 0,
         "unknown history stays unknown and uncredited")
    return UnknownHistoricalRequestV1(integer(r["sequence"], 1), parse_ref(r["evidence_ref"]))


REF_FIELDS = ("settled_state", "seed", "governance", "semantic_response", "save_response",
              "settled_full_response", "driver", "save", "driver_close", "closure",
              "ledger", "next", "origin_ledger", "wall_origin", "checkpoint_validator")


@dataclass(frozen=True, slots=True)
class BasisRefsV1:
    settled_state: ExactRefV1
    seed: ExactRefV1
    governance: ExactRefV1
    semantic_response: ExactRefV1
    save_response: ExactRefV1
    settled_full_response: ExactRefV1
    driver: ExactRefV1
    save: ExactRefV1
    driver_close: ExactRefV1
    closure: ExactRefV1
    ledger: ExactRefV1
    next: ExactRefV1
    origin_ledger: ExactRefV1
    wall_origin: ExactRefV1
    checkpoint_validator: ExactRefV1

    def to_wire(self) -> JsonObject:
        return {name: value.to_wire() for name, value in self.items()}

    def items(self) -> tuple[tuple[str, ExactRefV1], ...]:
        return (("settled_state", self.settled_state), ("seed", self.seed),
                ("governance", self.governance), ("semantic_response", self.semantic_response),
                ("save_response", self.save_response), ("settled_full_response", self.settled_full_response),
                ("driver", self.driver), ("save", self.save), ("driver_close", self.driver_close),
                ("closure", self.closure), ("ledger", self.ledger), ("next", self.next),
                ("origin_ledger", self.origin_ledger), ("wall_origin", self.wall_origin),
                ("checkpoint_validator", self.checkpoint_validator))


def parse_refs(value: object) -> BasisRefsV1:
    r = record(value, set(REF_FIELDS))
    return BasisRefsV1(*(parse_ref(r[name]) for name in REF_FIELDS))


@dataclass(frozen=True, slots=True)
class ProgressReconciliationV1:
    ledger_cycles: int
    ledger_date_raw: int
    settled_cycles: int
    settled_date_raw: int
    full_sequence: int
    checkpoint_count_before: int
    checkpoint_count_after: int
    maintenance_save_already_accounted: bool

    def __post_init__(self) -> None:
        integer(self.checkpoint_count_before)
        integer(self.checkpoint_count_after)
        need(type(self.maintenance_save_already_accounted) is bool, "exact accounting flag")
        need(self.checkpoint_count_after == self.checkpoint_count_before + (0 if self.maintenance_save_already_accounted else 1), "one actual maintenance SAVE")
        integer(self.ledger_cycles)
        integer(self.ledger_date_raw)
        integer(self.settled_cycles)
        integer(self.settled_date_raw)
        integer(self.full_sequence, 1)
        need(self.ledger_cycles <= self.settled_cycles and self.ledger_date_raw <= self.settled_date_raw,
             "historical ledger must not lead actual settled state")

    def to_wire(self) -> JsonObject:
        return {"ledger_cycles": self.ledger_cycles, "ledger_date_raw": self.ledger_date_raw,
                "settled_cycles": self.settled_cycles, "settled_date_raw": self.settled_date_raw,
                "full_sequence": self.full_sequence, "checkpoint_count_before": self.checkpoint_count_before,
                "checkpoint_count_after": self.checkpoint_count_after,
                "maintenance_save_already_accounted": self.maintenance_save_already_accounted}


def parse_progress(value: object) -> ProgressReconciliationV1:
    r = record(value, {"ledger_cycles", "ledger_date_raw", "settled_cycles",
                      "settled_date_raw", "full_sequence", "checkpoint_count_before", "checkpoint_count_after",
                      "maintenance_save_already_accounted"})
    return ProgressReconciliationV1(integer(r["ledger_cycles"]), integer(r["ledger_date_raw"]),
        integer(r["settled_cycles"]), integer(r["settled_date_raw"]), integer(r["full_sequence"], 1),
        integer(r["checkpoint_count_before"]), integer(r["checkpoint_count_after"]),
        exact_bool(r["maintenance_save_already_accounted"]))


def checkpoint_anchor(value: object) -> JsonObject:
    r = record(value, {"name", "load_save_name", "path", "size", "sha256",
                      "saved_date_raw", "history_index", "succession_lifecycle"})
    need(r["name"] == "xar_checkpoint.ck3" and r["load_save_name"] == "xar_checkpoint",
         "canonical checkpoint name")
    text(r["path"])
    integer(r["size"], 1)
    digest(r["sha256"])
    integer(r["saved_date_raw"])
    integer(r["history_index"], 1)
    life = r["succession_lifecycle"]
    need(life is None or type(life) is dict, "explicit nullable checkpoint lifecycle")
    return json_object(r)


@dataclass(frozen=True, slots=True)
class CurrentSavedBasisV1:
    machine_id: str
    observed_at_utc: str
    origin: CampaignOriginV1
    frame: SavedFrameV1
    completed_cycles: int
    checkpoint: JsonObject
    campaign_goal_anchor: JsonObject
    refs: BasisRefsV1
    driver_identity: FileStatIdentityV1
    save_identity: FileStatIdentityV1
    next_sequence: int
    progress: ProgressReconciliationV1
    unknown_requests: tuple[UnknownHistoricalRequestV1, ...]
    sidecars: tuple[ExactRefV1, ...]

    def __post_init__(self) -> None:
        text(self.machine_id)
        utc(self.observed_at_utc)
        integer(self.completed_cycles)
        integer(self.next_sequence, 1)
        need(self.completed_cycles == self.progress.settled_cycles
             and self.frame.date_raw == self.progress.settled_date_raw
             and self.frame.date_raw >= self.origin.start_date_raw, "one current saved frontier")
        cp = checkpoint_anchor(self.checkpoint)
        need(cp["saved_date_raw"] == self.frame.date_raw
             and cp["path"] == self.refs.save.path and cp["size"] == self.refs.save.bytes
             and cp["sha256"] == self.refs.save.sha256
             and self.driver_identity.bytes == self.refs.driver.bytes
             and self.save_identity.bytes == self.refs.save.bytes, "checkpoint and identity binding")
        goal = record(self.campaign_goal_anchor)
        need(goal.get("campaign_id") == self.origin.campaign_id
             and integer(goal.get("current_character_id"), 1) == self.frame.actor_character_id,
             "campaign/episode lineage")
        need(len({item.sequence for item in self.unknown_requests}) == len(self.unknown_requests)
             and all(item.sequence < self.next_sequence for item in self.unknown_requests),
             "bounded unique historical requests")
        need(len(self.unknown_requests) <= 64 and len(self.sidecars) <= 64, "bounded evidence set")
        need(len({item.path for item in self.sidecars}) == len(self.sidecars), "unique sidecars")

    def to_wire(self) -> JsonObject:
        return {"schema": BASIS_SCHEMA, "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
                "origin": self.origin.to_wire(), "frame": self.frame.to_wire(),
                "completed_cycles": self.completed_cycles, "checkpoint": json_object(self.checkpoint),
                "campaign_goal_anchor": json_object(self.campaign_goal_anchor), "refs": self.refs.to_wire(),
                "identity_schema": STAT_SCHEMA, "driver_identity": json_object(self.driver_identity.to_wire()),
                "save_identity": json_object(self.save_identity.to_wire()), "next_sequence": self.next_sequence,
                "progress": self.progress.to_wire(), "unknown_requests": [item.to_wire() for item in self.unknown_requests],
                "sidecars": [item.to_wire() for item in self.sidecars],
                "ordinary_cycle_credit": 0, "game_day_credit": 0, "original_actions_replayed": False,
                "power_loss_durability": "not_asserted"}


def parse_current_saved_basis_v1(value: object, *, expected_machine_id: str) -> CurrentSavedBasisV1:
    r = record(value, {"schema", "machine_id", "observed_at_utc", "origin", "frame",
        "completed_cycles", "checkpoint", "campaign_goal_anchor", "refs", "identity_schema",
        "driver_identity", "save_identity", "next_sequence", "progress", "unknown_requests",
        "sidecars", "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed", "power_loss_durability"})
    need(r["schema"] == BASIS_SCHEMA and text(r["machine_id"]) == text(expected_machine_id),
         "current basis schema/machine")
    need(r["identity_schema"] == STAT_SCHEMA and integer(r["ordinary_cycle_credit"]) == 0
         and integer(r["game_day_credit"]) == 0 and r["original_actions_replayed"] is False
         and r["power_loss_durability"] == "not_asserted",
         "cold snapshot adds no progress or replay")
    return CurrentSavedBasisV1(text(r["machine_id"]), utc(r["observed_at_utc"]),
        parse_origin(r["origin"]), parse_frame(r["frame"]), integer(r["completed_cycles"]),
        checkpoint_anchor(r["checkpoint"]), json_object(r["campaign_goal_anchor"]),
        parse_refs(r["refs"]), parse_file_stat_identity_v1(r["driver_identity"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(r["save_identity"], schema=STAT_SCHEMA), integer(r["next_sequence"], 1),
        parse_progress(r["progress"]), tuple(parse_unknown(item) for item in rows(r["unknown_requests"])),
        tuple(parse_ref(item) for item in rows(r["sidecars"])))


def encode_current_saved_basis_v1(value: CurrentSavedBasisV1) -> bytes:
    checked = parse_current_saved_basis_v1(value.to_wire(), expected_machine_id=value.machine_id)
    return canonical_json_v1(checked.to_wire())


def decode_current_saved_basis_v1(raw: bytes, *, expected_machine_id: str) -> CurrentSavedBasisV1:
    need(type(raw) is bytes and len(raw) <= 65536, "bounded basis JSON bytes")
    return parse_current_saved_basis_v1(parse_json(raw), expected_machine_id=expected_machine_id)


class BasisReaderV1(Protocol):
    def read(self, reference: ExactRefV1, limit: int) -> bytes: ...
    def stat(self, path: str) -> FileStatIdentityV1: ...


@dataclass(frozen=True, slots=True)
class CheckpointEnvironmentV1:
    profile_dir: Path


CheckpointFunctionV1: TypeAlias = Callable[[CheckpointEnvironmentV1, str, object], object]


@dataclass(frozen=True, slots=True)
class PinnedCheckpointValidatorV1:
    source_ref: ExactRefV1
    function: CheckpointFunctionV1

    def validate(self, payload: object, *, profile_dir: Path, pipe_name: str) -> JsonObject:
        if not isinstance(self.function, FunctionType):
            raise ValueError("validator function")
        need(Path(self.function.__code__.co_filename).resolve() == Path(self.source_ref.path).resolve(),
             "SDK validator origin differs")
        return checkpoint_anchor(self.function(CheckpointEnvironmentV1(profile_dir), pipe_name, payload))


@dataclass(frozen=True, slots=True)
class CurrentSavedBasisInputsV1:
    machine_id: str
    observed_at_utc: str
    origin: CampaignOriginV1
    refs: BasisRefsV1
    driver_identity: FileStatIdentityV1
    save_identity: FileStatIdentityV1
    unknown_requests: tuple[UnknownHistoricalRequestV1, ...]
    sidecars: tuple[ExactRefV1, ...]


@dataclass(frozen=True, slots=True)
class ValidatedCurrentSavedBasisV1:
    basis: CurrentSavedBasisV1
    driver_history_rows: int
    driver_body_reads: int
    canonical_checkpoint_validator_calls: int


def exact_read(reader: BasisReaderV1, reference: ExactRefV1, limit: int) -> bytes:
    need(reference.bytes <= limit, "evidence byte limit")
    raw = reader.read(reference, limit)
    need(type(raw) is bytes and len(raw) == reference.bytes
         and hashlib.sha256(raw).hexdigest() == reference.sha256, "evidence bytes/SHA drift")
    return raw


def evidence(reader: BasisReaderV1, reference: ExactRefV1, limit: int = 262144) -> dict[str, object]:
    return record(parse_json(exact_read(reader, reference, limit)))


def clean_state(state: dict[str, object]) -> None:
    need(state.get("schema") == "g2.queue.cumulative-loop/v1", "actual queue state schema")
    for name in ("pending_cycle", "pending_checkpoint", "terminal"):
        need(name in state and state[name] is None, "required settled-state null: " + name)
    for name in ("pending_natural_succession", "pending_unsafe_route_halt"):
        need(name not in state or state[name] is None, "optional state retains absence: " + name)


def completed_body(row: dict[str, object], tool: str) -> dict[str, object]:
    need("client_error" not in row or row["client_error"] is None, "original client error")
    request = record(row.get("request"))
    result = record(row.get("result"))
    need(request.get("tool") == tool and result.get("is_error") is False
         and result.get("result_type") == "complete", "actual completed native response")
    return record(result.get("structured_content"))


def qualify_current_saved_basis_v1(
    inputs: CurrentSavedBasisInputsV1, *, reader: BasisReaderV1,
    checkpoint_validator: PinnedCheckpointValidatorV1,
) -> ValidatedCurrentSavedBasisV1:
    return _derive(inputs, reader=reader, checkpoint_validator=checkpoint_validator)


def build_current_saved_basis_v1(
    inputs: CurrentSavedBasisInputsV1, *, reader: BasisReaderV1,
    checkpoint_validator: PinnedCheckpointValidatorV1,
) -> CurrentSavedBasisV1:
    return _derive(inputs, reader=reader, checkpoint_validator=checkpoint_validator).basis


def validate_current_saved_basis_files_v1(
    basis: CurrentSavedBasisV1, *, reader: BasisReaderV1,
    checkpoint_validator: PinnedCheckpointValidatorV1,
) -> ValidatedCurrentSavedBasisV1:
    checked = parse_current_saved_basis_v1(basis.to_wire(), expected_machine_id=basis.machine_id)
    inputs = CurrentSavedBasisInputsV1(checked.machine_id, checked.observed_at_utc, checked.origin,
        checked.refs, checked.driver_identity, checked.save_identity, checked.unknown_requests, checked.sidecars)
    result = _derive(inputs, reader=reader, checkpoint_validator=checkpoint_validator)
    need(canonical_json_v1(result.basis.to_wire()) == canonical_json_v1(checked.to_wire()),
         "current basis differs from actual evidence")
    return result


def _derive(
    inputs: CurrentSavedBasisInputsV1, *, reader: BasisReaderV1,
    checkpoint_validator: PinnedCheckpointValidatorV1,
) -> ValidatedCurrentSavedBasisV1:
    text(inputs.machine_id)
    utc(inputs.observed_at_utc)
    r = inputs.refs
    need(checkpoint_validator.source_ref == r.checkpoint_validator, "one SDK validator source")
    exact_read(reader, r.checkpoint_validator, 65536)
    seed = evidence(reader, r.seed)
    state = evidence(reader, r.settled_state)
    clean_state(seed)
    clean_state(state)
    count = integer(state.get("completed_cycles"))
    frame = parse_frame(state.get("before"))
    need(integer(seed.get("completed_cycles")) == count and parse_frame(seed.get("before")) == frame
         and seed.get("start_date_raw") == state.get("start_date_raw") == inputs.origin.start_date_raw,
         "saved seed retains actual settled frontier")
    goal = json_object(seed.get("campaign_goal_anchor"))
    need(canonical_json_v1(goal) == canonical_json_v1(state.get("campaign_goal_anchor")),
         "goal lineage unchanged by SAVE")
    changed = {"actual_saved_checkpoint", "actual_saved_checkpoint_source", "counts",
               "checkpoint_calendar_v1", "checkpoint_dirty_since_save", "checkpoint_due_after_readonly_chain"}
    for name in (set(seed) | set(state)) - changed:
        need(name in seed and name in state and canonical_json_v1(seed[name]) == canonical_json_v1(state[name]),
             "maintenance SAVE preserves other state: " + name)
    full = evidence(reader, r.settled_full_response)
    request = record(full.get("request")); result = record(full.get("result"))
    full_body = record(result.get("structured_content"))
    need(request.get("command") == "full_loop" and result.get("is_error") is False
         and full_body.get("status") == "bounded_loop_finished"
         and integer(full_body.get("cumulative_cycles")) == count
         and integer(full_body.get("actual_end_date_raw")) == frame.date_raw
         and parse_frame(full_body.get("actual_end_frame")) == frame
         and full_body.get("replay_allowed") is False, "final actual FULL/Queue agreement")
    full_sequence = integer(request.get("sequence"), 1)
    semantic_row = evidence(reader, r.semantic_response)
    semantic_sequence = integer(record(semantic_row.get("request")).get("sequence"), 1)
    semantic = completed_body(semantic_row, "ck3_take_semantic_snapshot_private_v1")
    need(integer(semantic.get("date_raw")) == frame.date_raw
         and integer(semantic.get("episode_character_id"), 1) == frame.actor_character_id
         and semantic.get("episode_run_id") == frame.episode_run_id
         and canonical_json_v1(semantic.get("campaign_goal")) == canonical_json_v1(goal)
         and semantic.get("map_ready") is True,
         "actual saved semantic actor/date/goal")
    save_row = evidence(reader, r.save_response)
    save_request = record(save_row.get("request"))
    save_sequence = integer(save_request.get("sequence"), 1)
    save_args = record(save_request.get("arguments"))
    need(integer(save_args.get("expected_revision"), 1) == integer(semantic.get("revision"), 1),
         "SAVE binds actual final SEM revision")
    save = completed_body(save_row, "ck3_save_checkpoint")
    cp = record(save.get("checkpoint"))
    need(cp.get("status") == "saved"
         and canonical_json_v1(cp) == canonical_json_v1(seed.get("actual_saved_checkpoint"))
         and integer(cp.get("date_raw")) == frame.date_raw
         and integer(cp.get("episode_character_id"), 1) == frame.actor_character_id
         and cp.get("episode_run_id") == frame.episode_run_id
         and canonical_json_v1(cp.get("succession_lifecycle")) == canonical_json_v1(semantic.get("succession_lifecycle")), "actual new saved checkpoint")
    governance = evidence(reader, r.governance)
    need("pending_cycle" in governance and governance["pending_cycle"] is None
         and integer(governance.get("completed_cycles")) == count, "settled governance")
    ledger = evidence(reader, r.ledger)
    origin_ledger = evidence(reader, r.origin_ledger)
    for old in (ledger, origin_ledger):
        need(old.get("machine_id") == inputs.machine_id
             and integer(old.get("start_date_raw")) == inputs.origin.start_date_raw
             and integer(old.get("target_date_raw")) == inputs.origin.target_date_raw
             and integer(old.get("target_days"), 1) == inputs.origin.target_days, "original ledger origin/target")
    wall = evidence(reader, r.wall_origin)
    need(wall.get("schema") == "xar.c23.canonical-cold-prelaunch/v1"
         and wall.get("machine_id") == inputs.machine_id
         and wall.get("original_wall_start_utc") == inputs.origin.original_wall_origin_utc,
         "explicit historical wall-origin adapter")
    old_counts = record(state.get("counts")); new_counts = record(seed.get("counts"))
    for name, number in old_counts.items():
        integer(number)
        need(name == "checkpoint_saved" or integer(new_counts.get(name)) == number, "other counters unchanged")
    need(set(old_counts) == set(new_counts), "counter keys unchanged")
    old_count = integer(old_counts.get("checkpoint_saved"))
    new_count = integer(new_counts.get("checkpoint_saved"))
    accounted = (canonical_json_v1(state.get("actual_saved_checkpoint")) == canonical_json_v1(cp)
        and state.get("checkpoint_dirty_since_save") is False and "checkpoint_calendar_v1" in state
        and integer(record(state["checkpoint_calendar_v1"]).get("last_saved_date_raw")) == frame.date_raw)
    progress = ProgressReconciliationV1(integer(ledger.get("last_settled_cycles")),
        integer(ledger.get("last_settled_date_raw")), count, frame.date_raw, full_sequence,
        old_count, new_count, accounted)
    for reference in (r.driver_close, r.closure):
        closed = evidence(reader, reference)
        need(closed.get("machine_id") == inputs.machine_id, "closure source machine")
    next_row = evidence(reader, r.next, 16384)
    next_sequence = integer(next_row.get("next_sequence"), 1)
    need(full_sequence < semantic_sequence < save_sequence < next_sequence,
         "strict FULL < final SEM < SAVE < unused NEXT order")
    for unknown in inputs.unknown_requests:
        old = evidence(reader, unknown.evidence_ref)
        pending = record(old.get("pending_cycle"))
        need(integer(pending.get("auto_sequence"), 1) == unknown.sequence
             and pending.get("stage") == "auto_unsettled", "preserved actual unknown request")
    for reference in inputs.sidecars:
        sidecar = evidence(reader, reference, 65536)
        need("pending" not in sidecar or sidecar["pending"] is None, "optional sidecar pending must be null")
    for name, expected in (("driver", inputs.driver_identity), ("save", inputs.save_identity)):
        reference = r.driver if name == "driver" else r.save
        need(expected.bytes == reference.bytes and reader.stat(reference.path) == expected,
             "current " + name + " stat identity")
    payload = evidence(reader, r.driver, 134217728)
    history = rows(payload.get("command_history"))
    need(integer(payload.get("format_version")) == 2 and canonical_json_v1(payload.get("last_checkpoint")) == canonical_json_v1(cp),
         "closed Driver actual last checkpoint")
    profile_dir = Path(r.save.path).parent.parent
    pipe_name = text(payload.get("pipe_name"))
    anchor = checkpoint_validator.validate(payload, profile_dir=profile_dir, pipe_name=pipe_name)
    need(anchor["path"] == r.save.path and anchor["size"] == r.save.bytes
         and anchor["sha256"] == r.save.sha256 and anchor["saved_date_raw"] == frame.date_raw
         and anchor["history_index"] == cp.get("history_index"), "canonical SDK SAVE anchor")
    need(reader.stat(r.driver.path) == inputs.driver_identity
         and reader.stat(r.save.path) == inputs.save_identity, "stable identities across validator")
    basis = CurrentSavedBasisV1(inputs.machine_id, inputs.observed_at_utc, inputs.origin, frame,
        count, anchor, goal, r, inputs.driver_identity, inputs.save_identity,
        next_sequence, progress, inputs.unknown_requests, inputs.sidecars)
    return ValidatedCurrentSavedBasisV1(basis, len(history), 1, 1)



# A failed cold-start observation is a new process epoch, never new gameplay.
READONLY_COLD_FAILURE_EPOCH_SCHEMA = "xar.current-saved-readonly-cold-failure-epoch/v1"


@dataclass(frozen=True)
class ReadonlyColdFailureRefsV1:
    business_basis: ExactRefV1
    driver_review: ExactRefV1
    history_tail: ExactRefV1
    closure_index: ExactRefV1
    launch: ExactRefV1
    semantic_response: ExactRefV1
    capability_rejection: ExactRefV1
    first_exception: ExactRefV1
    inflight: ExactRefV1
    request_inventory: ExactRefV1
    sdk_closed: ExactRefV1
    supervisor_closed: ExactRefV1
    game_exit: ExactRefV1
    next: ExactRefV1
    canonical_qualification: ExactRefV1

    def items(self) -> tuple[tuple[str, ExactRefV1], ...]:
        return (
            ("business_basis", self.business_basis),
            ("driver_review", self.driver_review),
            ("history_tail", self.history_tail),
            ("closure_index", self.closure_index),
            ("launch", self.launch),
            ("semantic_response", self.semantic_response),
            ("capability_rejection", self.capability_rejection),
            ("first_exception", self.first_exception),
            ("inflight", self.inflight),
            ("request_inventory", self.request_inventory),
            ("sdk_closed", self.sdk_closed),
            ("supervisor_closed", self.supervisor_closed),
            ("game_exit", self.game_exit),
            ("next", self.next),
            ("canonical_qualification", self.canonical_qualification),
        )

    def to_wire(self) -> JsonObject:
        return {name: value.to_wire() for name, value in self.items()}


def parse_readonly_cold_failure_refs_v1(value: object) -> ReadonlyColdFailureRefsV1:
    names = {"business_basis", "driver_review", "history_tail", "closure_index", "launch",
        "semantic_response", "capability_rejection", "first_exception", "inflight",
        "request_inventory", "sdk_closed", "supervisor_closed", "game_exit", "next", "canonical_qualification"}
    row = record(value, names)
    return ReadonlyColdFailureRefsV1(
        parse_ref(row["business_basis"]), parse_ref(row["driver_review"]),
        parse_ref(row["history_tail"]), parse_ref(row["closure_index"]),
        parse_ref(row["launch"]), parse_ref(row["semantic_response"]),
        parse_ref(row["capability_rejection"]), parse_ref(row["first_exception"]),
        parse_ref(row["inflight"]), parse_ref(row["request_inventory"]),
        parse_ref(row["sdk_closed"]), parse_ref(row["supervisor_closed"]),
        parse_ref(row["game_exit"]), parse_ref(row["next"]), parse_ref(row["canonical_qualification"]))


@dataclass(frozen=True)
class ReadonlyClosedDriverFlagsV1:
    managed_restore_transaction: None
    rollback_war_failure: None
    succession_expectation: None
    session_binding_present: Literal[False]

    def __post_init__(self) -> None:
        need(self.managed_restore_transaction is None and self.rollback_war_failure is None
            and self.succession_expectation is None and self.session_binding_present is False,
            "explicit closed Driver has no unresolved transaction")

    def to_wire(self) -> JsonObject:
        return {"managed_restore_transaction": None, "rollback_war_failure": None,
            "succession_expectation": None, "session_binding_present": False}


def parse_readonly_closed_driver_flags_v1(value: object) -> ReadonlyClosedDriverFlagsV1:
    row = record(value, {"managed_restore_transaction", "rollback_war_failure",
        "succession_expectation", "session_binding_present"})
    need(row["managed_restore_transaction"] is None and row["rollback_war_failure"] is None
        and row["succession_expectation"] is None and row["session_binding_present"] is False,
        "actual closed Driver flags, missing is not null")
    return ReadonlyClosedDriverFlagsV1(None, None, None, False)


@dataclass(frozen=True)
class ReadonlyColdFailureEpochV1:
    machine_id: str
    observed_at_utc: str
    refs: ReadonlyColdFailureRefsV1
    driver_payload_flags: ReadonlyClosedDriverFlagsV1

    def __post_init__(self) -> None:
        text(self.machine_id)
        utc(self.observed_at_utc)

    def to_wire(self) -> JsonObject:
        return {"schema": READONLY_COLD_FAILURE_EPOCH_SCHEMA, "machine_id": self.machine_id,
            "observed_at_utc": self.observed_at_utc,
            "status": "CLOSED_READONLY_INIT_POSTCHECK_FAILURE", "refs": self.refs.to_wire(),
            "driver_payload_flags": self.driver_payload_flags.to_wire(),
            "new_ordinary_cycle_credit": 0, "new_game_day_credit": 0,
            "new_checkpoint_credit": 0, "original_requests_replayed": False}


def parse_readonly_cold_failure_epoch_v1(
    value: object, *, expected_machine_id: str,
) -> ReadonlyColdFailureEpochV1:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "status", "refs",
        "new_ordinary_cycle_credit", "new_game_day_credit", "new_checkpoint_credit",
        "original_requests_replayed", "driver_payload_flags"})
    need(row["schema"] == READONLY_COLD_FAILURE_EPOCH_SCHEMA
        and row["status"] == "CLOSED_READONLY_INIT_POSTCHECK_FAILURE"
        and row["machine_id"] == expected_machine_id, "explicit readonly failure epoch")
    for name in ("new_ordinary_cycle_credit", "new_game_day_credit", "new_checkpoint_credit"):
        need(integer(row[name]) == 0, "readonly initialization grants no credit")
    need(row["original_requests_replayed"] is False, "failed requests are not replayed")
    return ReadonlyColdFailureEpochV1(text(row["machine_id"]), utc(row["observed_at_utc"]),
        parse_readonly_cold_failure_refs_v1(row["refs"]),
        parse_readonly_closed_driver_flags_v1(row["driver_payload_flags"]))


def _closed_filetime_v1(value: object) -> str:
    # Existing Python process receipts use integers; the shared DTO is JSON-safe.
    if type(value) is int:
        need(0 < value < 2**64, "closed process FILETIME")
        return str(value)
    result = text(value)
    need(re.fullmatch(r"[1-9][0-9]{0,19}", result) is not None
        and int(result) < 2**64, "canonical closed process FILETIME")
    return result


@dataclass(frozen=True)
class ReadonlyColdClosedGameV1:
    pid: int
    creation_filetime: str
    creation_date: str


@dataclass(frozen=True)
class ReadonlyColdClosedSdkV1:
    role: Literal["sdk_queue", "sdk_application"]
    pid: int
    creation_filetime: str
    executable: str
    exit_code: int


@dataclass(frozen=True)
class ValidatedReadonlyColdFailureEpochV1:
    epoch: ReadonlyColdFailureEpochV1
    business_basis: CurrentSavedBasisV1
    driver_ref: ExactRefV1
    driver_identity: FileStatIdentityV1
    save_ref: ExactRefV1
    save_identity: FileStatIdentityV1
    history_count: int
    history_row: JsonObject
    old_game: ReadonlyColdClosedGameV1
    sdk_processes: tuple[ReadonlyColdClosedSdkV1, ...]
    next_sequence: int
    pipe_name: str


def _readonly_restore_row_v1(
    value: object, *, checkpoint: JsonObject, previous_pid: int, current_pid: int,
) -> JsonObject:
    row = record(value, {"index", "command", "ok", "result"})
    result = record(row["result"], {"step", "accepted", "status", "backend_id", "source",
        "checkpoint", "restored_date_raw", "map_ready", "lifecycle"})
    lifecycle = record(result["lifecycle"], {"previous_pid", "pid"})
    need(integer(row["index"], 1) == integer(checkpoint["history_index"], 1) + 1
        and row["command"] == "restore-checkpoint" and row["ok"] is True
        and result["step"] == "restore-checkpoint" and result["accepted"] is True
        and result["status"] == "restored" and result["backend_id"] == "native-headless"
        and result["source"] == "native-session-cold-start"
        and canonical_json_v1(result["checkpoint"]) == canonical_json_v1(checkpoint)
        and integer(result["restored_date_raw"]) == integer(checkpoint["date_raw"])
        and result["map_ready"] is True
        and integer(lifecycle["previous_pid"], 1, 2**32-1) == previous_pid
        and integer(lifecycle["pid"], 1, 2**32-1) == current_pid,
        "only the exact cold restore bookkeeping row is permitted after SAVE")
    return json_object(row)


def _readonly_stat_v1(value: object) -> FileStatIdentityV1:
    row = record(value, {"bytes", "file_id", "mtime_ns", "device", "links"})
    device = text(row["device"])
    need(re.fullmatch(r"(?:0|[1-9][0-9]*)", device) is not None
        and integer(row["links"], 1) == 1, "closed OS device and single link")
    return parse_file_stat_identity_v1(
        {key: row[key] for key in ("bytes", "file_id", "mtime_ns")}, schema=STAT_SCHEMA)


def validate_readonly_cold_failure_evidence_v1(
    epoch: ReadonlyColdFailureEpochV1, *, reader: BasisReaderV1,
) -> ValidatedReadonlyColdFailureEpochV1:
    """Validate immutable small receipts without current Driver stat or body I/O."""
    r = epoch.refs
    old = decode_current_saved_basis_v1(exact_read(reader, r.business_basis, 65536),
        expected_machine_id=epoch.machine_id)
    launch = evidence(reader, r.launch, 32768)
    pid = integer(launch.get("pid"), 1, 2**32-1)
    game = ReadonlyColdClosedGameV1(pid, _closed_filetime_v1(launch.get("creation_filetime")),
        text(launch.get("creation_date")))
    need(launch.get("machine_id") == epoch.machine_id and launch.get("old_save_loaded") is True
        and launch.get("load_save_name") == "xar_checkpoint" and launch.get("nonwar_only") is False,
        "actual fresh saved Game for failed cold epoch")
    root = Path(r.launch.path).parent
    need(Path(r.launch.path).name == "ROOT-ACTUAL-GAME-LAUNCH-C23.json",
        "actual launch reference")
    semrow = evidence(reader, r.semantic_response, 262144)
    semseq = old.next_sequence
    semrequest = {"sequence": semseq, "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}}
    caprequest = {"sequence": semseq + 1, "tool": "ck3_get_capabilities", "arguments": {}}
    need(canonical_json_v1(record(semrow.get("request"))) == canonical_json_v1(semrequest), "original first SEM identity")
    semantic = completed_body(semrow, "ck3_take_semantic_snapshot_private_v1")
    need(integer(semantic.get("date_raw")) == old.frame.date_raw
        and integer(semantic.get("episode_character_id"), 1) == old.frame.actor_character_id
        and semantic.get("episode_run_id") == old.frame.episode_run_id
        and semantic.get("paused") is True and semantic.get("map_ready") is True
        and semantic.get("one_life_terminal") is False
        and canonical_json_v1(semantic.get("campaign_goal")) == canonical_json_v1(old.campaign_goal_anchor),
        "completed observation does not change the saved business frontier")
    cap = evidence(reader, r.capability_rejection, 16384)
    need(canonical_json_v1(record(cap.get("request"))) == canonical_json_v1(caprequest) and "result" not in cap
        and cap.get("client_error") == "C11 normal checkpoint cold denied: fresh cold SEM then CAP required"
        and cap.get("replay_allowed") is False
        and cap.get("original_response") == r.semantic_response.path,
        "CAP was locally rejected without a new RPC result")
    failure = evidence(reader, r.first_exception, 16384)
    tree = record(failure.get("exception_tree"))
    need(failure.get("stage") == "request_dispatch" and failure.get("replay_allowed") is False
        and canonical_json_v1(record(failure.get("request_identity"))) == canonical_json_v1({
            "sequence": semseq, "tool": semrequest["tool"], "command": None})
        and tree.get("type") == "ValueError"
        and tree.get("message") == "founding score anchor requires actual paused1066 frame",
        "explicit completed-SEM score postcheck failure")
    inflight = evidence(reader, r.inflight, 16384)
    need(integer(inflight.get("sequence"), 1) == semseq and inflight.get("tool") == semrequest["tool"]
        and record(inflight.get("arguments")) == {}
        and inflight.get("scope") == "cold-start-readiness-only"
        and inflight.get("outer_sequence_consumed") is False
        and integer(inflight.get("business_credit")) == 0
        and inflight.get("original_P01_response_replayed") is False,
        "retained readiness failure is not a business attempt")
    inventory = evidence(reader, r.request_inventory, 16384)
    need(inventory.get("schema") == "xar.current-saved-closed-request-inventory/v1"
        and inventory.get("machine_id") == epoch.machine_id and inventory.get("reviewer") == "/root"
        and inventory.get("closed_directory_snapshot") is True
        and Path(text(inventory.get("runtime_root"))).resolve() == root.resolve()
        and integer(inventory.get("epoch_start_sequence"), 1) == semseq
        and rows(inventory.get("unmatched_new_request_files")) == []
        and rows(inventory.get("unmatched_new_response_files")) == [],
        "actual closed request inventory")
    utc(inventory.get("observed_at_utc"))
    reqrefs = tuple(parse_ref(v) for v in rows(inventory.get("request_refs")))
    outrefs = tuple(parse_ref(v) for v in rows(inventory.get("response_refs")))
    need(len(reqrefs) == len(outrefs) == 2 and outrefs == (r.semantic_response, r.capability_rejection),
        "exactly the original SEM and locally rejected CAP")
    for reference, expected in zip(reqrefs, (semrequest, caprequest)):
        sequence = integer(expected["sequence"], 1)
        need(Path(reference.path).resolve() == (root/"p37-requests"/f"{sequence:04d}-1-result.json").resolve()
            and canonical_json_v1(evidence(reader, reference, 16384)) == canonical_json_v1(expected), "actual request inventory source")
    for reference, sequence in zip(outrefs, (semseq, semseq+1)):
        need(Path(reference.path).resolve() == (root/"p37-responses"/f"{sequence:04d}-1-result.json").resolve(),
            "actual response inventory source")
    need(inflight.get("request_file") == reqrefs[0].path, "original readiness request file")
    nextseq = integer(evidence(reader, r.next, 16384).get("next_sequence"), 1)
    need(nextseq == semseq + 2, "failed numbers consumed once without replay")
    sdk = evidence(reader, r.sdk_closed, 16384)
    need(sdk.get("machine_id") == epoch.machine_id
        and sdk.get("status") == "ACTUAL_BOTH_SDK_EXITS_OBSERVED"
        and sdk.get("normal") is False and integer(sdk.get("launcher_exit_code")) == 1,
        "abnormal SDK shutdown is preserved")
    processes: list[ReadonlyColdClosedSdkV1] = []
    for value in rows(sdk.get("processes")):
        row = record(value)
        role = row.get("role")
        if role == "sdk_queue":
            typed_role: Literal["sdk_queue", "sdk_application"] = "sdk_queue"
            expected_code = 1
        elif role == "sdk_application":
            typed_role = "sdk_application"
            expected_code = 0
        else:
            raise ValueError("exact closed SDK role")
        need(row.get("kernel_exit_observed") is True and integer(row.get("wait_result")) == 0
            and integer(row.get("exit_code")) == expected_code
            and "observation_error" in row and row["observation_error"] is None,
            "actual closed SDK 1/0 pair, not normal 0/0")
        processes.append(ReadonlyColdClosedSdkV1(typed_role, integer(row.get("pid"), 1, 2**32-1),
            _closed_filetime_v1(row.get("creation_filetime")), text(row.get("executable")), expected_code))
    need(len(processes) == 2 and {p.role for p in processes} == {"sdk_queue", "sdk_application"}
        and len({(p.pid, p.creation_filetime) for p in processes}) == 2, "two distinct closed SDK processes")
    supervisor = evidence(reader, r.supervisor_closed, 16384)
    need(r.game_exit == r.supervisor_closed, "Game exit is the actual supervisor cleanup receipt")
    phase = record(supervisor.get("known_preload_phase"))
    before_game = record(phase.get("before")); after_game = record(phase.get("after"))
    cleanup = record(supervisor.get("owned_cleanup"))
    need(supervisor.get("machine_id") == epoch.machine_id
        and supervisor.get("cleanup_classification") == "FORCED_OWNED_GAME_CLEANUP"
        and canonical_json_v1(sdk_without_launcher_v1(record(supervisor.get("sdk_actual_exit"))))
        == canonical_json_v1(sdk_without_launcher_v1(sdk))
        and integer(cleanup.get("ck3_pid"), 1) == pid and integer(cleanup.get("ck3_exit_code")) == 1
        and integer(cleanup.get("job_active_processes_final")) == 0
        and cleanup.get("tree_gone") is True and cleanup.get("cleanup_proven") is True
        and cleanup.get("ok") is True and rows(cleanup.get("contract_errors")) == []
        and cleanup.get("ck3_creation_date") == game.creation_date
        and integer(before_game.get("pid"), 1) == integer(after_game.get("pid"), 1) == pid
        and _closed_filetime_v1(before_game.get("creation_filetime")) == game.creation_filetime
        and _closed_filetime_v1(after_game.get("creation_filetime")) == game.creation_filetime,
        "forced Game exit1/Job0 is preserved")
    utc(supervisor.get("observed_at_utc"))
    index = evidence(reader, r.closure_index, 32768)
    need(index.get("schema") == "xar.readonly-cold-init-postcheck-abort-closure/v1"
        and index.get("status") == "CLOSED_NO_BUSINESS_PROGRESS"
        and index.get("machine_id") == epoch.machine_id
        and parse_ref(index.get("original_basis_ref")) == r.business_basis
        and integer(index.get("next_sequence"), 1) == nextseq
        and integer(index.get("business_completed_cycles")) == old.completed_cycles
        and integer(index.get("business_date_raw")) == old.frame.date_raw
        and index.get("original_whole_wall_origin") == old.origin.original_wall_origin_utc
        and index.get("SDK_exit_codes") == [1, 0] and all(type(v) is int for v in rows(index["SDK_exit_codes"]))
        and index.get("SDK_normal") is False and integer(index.get("Game_exit_code")) == 1
        and index.get("Game_forced") is True and integer(index.get("Game_Job_active_final")) == 0
        and index.get("all_owned_Tasks_actual_absent") is True and integer(index.get("owned_Task_count")) == 2
        and index.get("original_requests_replayed") is False, "explicit readonly abort closure")
    for name in ("new_ordinary_cycle_credit", "new_game_day_credit", "new_checkpoint_credit"):
        need(integer(index.get(name)) == 0, "abort epoch adds no progress")
    indexrefs = record(index.get("refs"))
    need(set(indexrefs) == {"launch", "sdk_pair", "sdk_closed", "supervisor_sdk_exits",
        "supervisor_closed", "game_exit", "first_exception", "semantic_response",
        "capability_rejection", "inflight", "next", "driver_review", "history_tail",
        "supervisor_spec", "display_spec", "supervisor_task_closed", "display_task_closed",
        "supervisor_unregister", "display_unregister", "screen_release", "recording_completed"},
        "complete readonly closed epoch evidence inventory")
    for value in indexrefs.values():
        exact_read(reader, parse_ref(value), 65536)
    for name in ("launch", "sdk_closed", "supervisor_closed", "game_exit", "first_exception",
                 "semantic_response", "capability_rejection", "inflight", "next", "driver_review", "history_tail"):
        need(parse_ref(indexrefs.get(name)) == dict(r.items())[name], "closure/index evidence binding: "+name)
    review = evidence(reader, r.driver_review, 16384)
    need(review.get("schema") == "xar.readonly-cold-epoch-Driver-SAVE-review/v1"
        and review.get("status") == "CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_AFTER_READONLY_INIT"
        and review.get("machine_id") == epoch.machine_id
        and parse_ref(review.get("original_business_review")) == old.refs.driver_close,
        "actual readonly Driver/SAVE review")
    driver = record(review.get("Driver")); saved = record(review.get("SAVE"))
    driver_ref = parse_ref(driver.get("ref")); save_ref = parse_ref(saved.get("ref"))
    driver_id = _readonly_stat_v1(driver.get("identity"))
    save_id = _readonly_stat_v1(saved.get("identity"))
    cp = record(completed_body(evidence(reader, old.refs.save_response), "ck3_save_checkpoint")["checkpoint"])
    identity = record(driver.get("recorded_identity"))
    need(save_ref == old.refs.save and save_id == old.save_identity
        and driver_ref.path == old.refs.driver.path and driver_id.bytes == driver_ref.bytes
        and driver_id != old.driver_identity and integer(driver.get("format_version")) == 2
        and canonical_json_v1(driver.get("last_checkpoint")) == canonical_json_v1(cp)
        and integer(identity.get("bridge_pid"), 1) == pid
        and integer(identity.get("episode_character_id"), 1) == old.frame.actor_character_id
        and identity.get("episode_run_id") == old.frame.episode_run_id
        and "session_binding" in rows(driver.get("absent_payload_fields"))
        and integer(review.get("actual_saved_cycles")) == old.completed_cycles
        and integer(review.get("actual_saved_days")) == (old.frame.date_raw-old.origin.start_date_raw)//24
        and review.get("unknown10565_replayed") is False
        and review.get("original_whole_wall_origin") == old.origin.original_wall_origin_utc,
        "current Driver retains the exact saved business checkpoint")
    history_count = integer(driver.get("command_history_count"), 1)
    tail = evidence(reader, r.history_tail, 16384)
    need(tail.get("schema") == "xar.readonly-cold-epoch-history-tail/v1"
        and tail.get("machine_id") == epoch.machine_id and parse_ref(tail.get("driver_review")) == r.driver_review
        and _readonly_stat_v1(tail.get("driver_identity")) == driver_id
        and integer(tail.get("checkpoint_history_index"), 1) == integer(cp["history_index"], 1)
        and integer(tail.get("command_history_count"), 1) == history_count
        and history_count == integer(cp["history_index"], 1)+1, "one actual post-checkpoint restore row")
    tailrows = rows(tail.get("post_checkpoint_history"))
    need(len(tailrows) == 1, "one post-checkpoint history row")
    previous = record(evidence(reader, old.refs.driver_close).get("Driver"))
    previous_identity = record(previous.get("recorded_identity"))
    history_row = _readonly_restore_row_v1(tailrows[0], checkpoint=json_object(cp),
        previous_pid=integer(previous_identity.get("bridge_pid"), 1), current_pid=pid)
    validated = ValidatedReadonlyColdFailureEpochV1(epoch, old, driver_ref, driver_id, save_ref, save_id,
        history_count, history_row, game, tuple(sorted(processes,key=lambda p:p.role)), nextseq,
        text(identity.get("pipe_name")))
    validate_readonly_canonical_qualification_v1(validated, reader=reader)
    return validated


def validate_readonly_cold_failure_epoch_v1(
    epoch: ReadonlyColdFailureEpochV1, *, reader: BasisReaderV1,
) -> ValidatedReadonlyColdFailureEpochV1:
    """Cold qualification adds current stat checks to immutable closed evidence."""
    result = validate_readonly_cold_failure_evidence_v1(epoch, reader=reader)
    need(reader.stat(result.driver_ref.path) == result.driver_identity
        and reader.stat(result.save_ref.path) == result.save_identity,
        "closed current Driver/SAVE identities")
    return result


def sdk_without_launcher_v1(sdk: dict[str, object]) -> dict[str, object]:
    """The supervisor embeds the same SDK report without launcher-only fields."""
    normalized: list[dict[str, object]] = []
    for value in rows(sdk.get("processes")):
        row = record(value)
        row["creation_filetime"] = _closed_filetime_v1(row.get("creation_filetime"))
        integer(row.get("pid"), 1, 2**32-1)
        integer(row.get("exit_code"))
        integer(row.get("wait_result"))
        need(row.get("kernel_exit_observed") is True
            and "observation_error" in row and row["observation_error"] is None,
            "SDK embedded kernel proof")
        normalized.append(row)
    return {"status": sdk["status"], "processes": normalized, "normal": sdk["normal"]}


def validate_readonly_cold_failure_driver_v1(
    validated: ValidatedReadonlyColdFailureEpochV1, payload: object,
) -> None:
    row = record(payload)
    history = rows(row.get("command_history"))
    need(len(history) == validated.history_count
        and canonical_json_v1(history[-1]) == canonical_json_v1(validated.history_row),
        "actual full Driver agrees with bounded history evidence")
    for name in ("managed_restore_transaction", "rollback_war_failure", "succession_expectation"):
        need(name in row and row[name] is None, "no unresolved Driver transaction: "+name)
    need("session_binding" not in row, "no fabricated Driver session binding")


READONLY_COLD_FAILURE_QUALIFICATION_SCHEMA = "xar.current-saved-readonly-failure-basis-qualification/v1"


def validate_readonly_canonical_qualification_v1(
    validated: ValidatedReadonlyColdFailureEpochV1, *, reader: BasisReaderV1,
) -> JsonObject:
    r = validated.epoch.refs
    proof = evidence(reader, r.canonical_qualification, 16384)
    need(proof.get("schema") == "xar.closed-readonly-epoch-canonical-checkpoint-qualification/v1"
        and proof.get("machine_id") == validated.epoch.machine_id
        and proof.get("status") == "ACTUAL_CLOSED_DRIVER_CANONICAL_SAVE_VALIDATED"
        and parse_ref(proof.get("driver_review")) == r.driver_review
        and parse_ref(proof.get("history_tail")) == r.history_tail
        and canonical_json_v1(proof.get("checkpoint")) == canonical_json_v1(validated.business_basis.checkpoint)
        and _readonly_stat_v1(proof.get("Driver_identity")) == validated.driver_identity
        and _readonly_stat_v1(proof.get("SAVE_identity")) == validated.save_identity
        and integer(proof.get("Driver_full_read_count"), 1) == 1
        and integer(proof.get("SAVE_full_hash_count"), 1) == 1
        and integer(proof.get("Driver_full_read_bytes"), 1) == validated.driver_ref.bytes
        and integer(proof.get("SAVE_full_hash_bytes"), 1) == validated.save_ref.bytes
        and proof.get("original_checkpoint_unchanged") is True,
        "actual successful Root canonical qualification, not cached SHA")
    for key in ("new_ordinary_cycle_credit", "new_game_day_credit", "actual_constructor_or_Game_RPC_calls"):
        need(integer(proof.get(key)) == 0, "canonical read gives no gameplay credit")
    integer(proof.get("total_Root_A23_Driver_full_reads"), 1)
    integer(proof.get("total_Root_A23_SAVE_full_hashes"), 1)
    validator = parse_ref(proof.get("validator"))
    exact_read(reader, validator, 65536)
    need(Path(validator.path).name == "cold_checkpoint_validator.py", "original canonical validator source")
    return json_object(proof)


def build_readonly_cold_failure_basis_v1(
    validated: ValidatedReadonlyColdFailureEpochV1, *, epoch_ref: ExactRefV1,
    observed_at_utc: str, sidecars: tuple[ExactRefV1, ...], reader: BasisReaderV1,
) -> CurrentSavedBasisV1:
    """Bind the real completed canonical receipt without another large body read."""
    checked = validate_readonly_cold_failure_evidence_v1(validated.epoch, reader=reader)
    need(checked == validated, "validated epoch must match its immutable evidence")
    encoded = parse_readonly_cold_failure_epoch_v1(
        parse_json(exact_read(reader, epoch_ref, 65536)),
        expected_machine_id=validated.epoch.machine_id)
    need(encoded == validated.epoch, "new basis binds exact epoch")
    need(reader.stat(validated.driver_ref.path) == validated.driver_identity
        and reader.stat(validated.save_ref.path) == validated.save_identity,
        "current closed identities before metadata construction")
    proof = validate_readonly_canonical_qualification_v1(validated, reader=reader)
    old = validated.business_basis
    for reference in sidecars:
        item = evidence(reader, reference, 65536)
        need("pending" not in item or item["pending"] is None, "closed sidecar pending must be absent/null")
    refs = replace(old.refs, driver=validated.driver_ref,
        driver_close=validated.epoch.refs.driver_review, closure=epoch_ref,
        next=validated.epoch.refs.next, checkpoint_validator=parse_ref(proof["validator"]))
    return CurrentSavedBasisV1(old.machine_id, utc(observed_at_utc), old.origin, old.frame,
        old.completed_cycles, json_object(old.checkpoint), json_object(old.campaign_goal_anchor), refs,
        validated.driver_identity, validated.save_identity, validated.next_sequence, old.progress,
        old.unknown_requests, sidecars)


@dataclass(frozen=True)
class ReadonlyColdFailureQualificationV1:
    machine_id: str
    observed_at_utc: str
    basis_ref: ExactRefV1
    epoch_ref: ExactRefV1
    canonical_qualification_ref: ExactRefV1
    driver_ref: ExactRefV1
    save_ref: ExactRefV1
    driver_identity_before: FileStatIdentityV1
    driver_identity_after: FileStatIdentityV1
    save_identity_before: FileStatIdentityV1
    save_identity_after: FileStatIdentityV1
    validator_source_ref: ExactRefV1
    driver_history_rows: int
    root_driver_body_reads: int
    root_save_hash_reads: int
    driver_body_reads: int = 0
    canonical_checkpoint_validator_calls: int = 0
    save_hash_reads: int = 0

    def __post_init__(self) -> None:
        text(self.machine_id)
        utc(self.observed_at_utc)
        integer(self.driver_history_rows, 1)
        integer(self.root_driver_body_reads, 1)
        integer(self.root_save_hash_reads, 1)
        for value in (self.driver_body_reads, self.canonical_checkpoint_validator_calls, self.save_hash_reads):
            need(integer(value) == 0, "metadata construction does not redo canonical I/O")
        need(self.driver_identity_before == self.driver_identity_after
            and self.save_identity_before == self.save_identity_after, "stable readonly metadata identities")

    def to_wire(self) -> JsonObject:
        return {"schema": READONLY_COLD_FAILURE_QUALIFICATION_SCHEMA,
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "basis_ref": self.basis_ref.to_wire(), "epoch_ref": self.epoch_ref.to_wire(),
            "canonical_qualification_ref": self.canonical_qualification_ref.to_wire(),
            "driver_ref": self.driver_ref.to_wire(), "save_ref": self.save_ref.to_wire(),
            "driver_identity_before": json_object(self.driver_identity_before.to_wire()),
            "driver_identity_after": json_object(self.driver_identity_after.to_wire()),
            "save_identity_before": json_object(self.save_identity_before.to_wire()),
            "save_identity_after": json_object(self.save_identity_after.to_wire()),
            "validator_source_ref": self.validator_source_ref.to_wire(),
            "driver_history_rows": self.driver_history_rows,
            "root_driver_body_reads": self.root_driver_body_reads,
            "root_save_hash_reads": self.root_save_hash_reads,
            "driver_body_reads": self.driver_body_reads,
            "canonical_checkpoint_validator_calls": self.canonical_checkpoint_validator_calls,
            "save_hash_reads": self.save_hash_reads,
            "read_count_scope": "metadata_build_only_bound_Root_canonical_receipt"}


def parse_readonly_cold_failure_qualification_v1(
    value: object, *, expected_machine_id: str,
) -> ReadonlyColdFailureQualificationV1:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "basis_ref", "epoch_ref",
        "canonical_qualification_ref", "driver_ref", "save_ref", "driver_identity_before",
        "driver_identity_after", "save_identity_before", "save_identity_after", "validator_source_ref",
        "driver_history_rows", "root_driver_body_reads", "root_save_hash_reads", "driver_body_reads",
        "canonical_checkpoint_validator_calls", "save_hash_reads", "read_count_scope"})
    need(row["schema"] == READONLY_COLD_FAILURE_QUALIFICATION_SCHEMA
        and row["machine_id"] == expected_machine_id
        and row["read_count_scope"] == "metadata_build_only_bound_Root_canonical_receipt",
        "explicit readonly failure basis qualification")
    return ReadonlyColdFailureQualificationV1(text(row["machine_id"]), utc(row["observed_at_utc"]),
        parse_ref(row["basis_ref"]), parse_ref(row["epoch_ref"]), parse_ref(row["canonical_qualification_ref"]),
        parse_ref(row["driver_ref"]), parse_ref(row["save_ref"]),
        parse_file_stat_identity_v1(row["driver_identity_before"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["driver_identity_after"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_before"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_after"], schema=STAT_SCHEMA),
        parse_ref(row["validator_source_ref"]), integer(row["driver_history_rows"], 1),
        integer(row["root_driver_body_reads"], 1), integer(row["root_save_hash_reads"], 1),
        integer(row["driver_body_reads"]), integer(row["canonical_checkpoint_validator_calls"]),
        integer(row["save_hash_reads"]))


def build_readonly_cold_failure_qualification_v1(
    validated: ValidatedReadonlyColdFailureEpochV1, basis: CurrentSavedBasisV1, *,
    basis_ref: ExactRefV1, reader: BasisReaderV1, observed_at_utc: str,
) -> ReadonlyColdFailureQualificationV1:
    expected = build_readonly_cold_failure_basis_v1(validated,
        epoch_ref=basis.refs.closure, observed_at_utc=basis.observed_at_utc,
        sidecars=basis.sidecars, reader=reader)
    need(canonical_json_v1(expected.to_wire()) == canonical_json_v1(basis.to_wire()),
        "qualification preserves the exact saved business and failed-epoch basis")
    need(canonical_json_v1(parse_json(exact_read(reader, basis_ref, 65536))) == canonical_json_v1(basis.to_wire()),
        "qualification binds actual new basis bytes")
    need(basis.refs.closure.path != validated.epoch.refs.closure_index.path
        and basis.refs.driver == validated.driver_ref and basis.refs.save == validated.save_ref,
        "new epoch is separate from original closure and business evidence")
    proof = validate_readonly_canonical_qualification_v1(validated, reader=reader)
    need(reader.stat(basis.refs.driver.path) == basis.driver_identity
        and reader.stat(basis.refs.save.path) == basis.save_identity, "stable closed metadata identities")
    return ReadonlyColdFailureQualificationV1(basis.machine_id, utc(observed_at_utc), basis_ref,
        basis.refs.closure, validated.epoch.refs.canonical_qualification, basis.refs.driver, basis.refs.save,
        basis.driver_identity, basis.driver_identity, basis.save_identity, basis.save_identity,
        basis.refs.checkpoint_validator, validated.history_count,
        integer(proof["total_Root_A23_Driver_full_reads"], 1),
        integer(proof["total_Root_A23_SAVE_full_hashes"], 1))
