"""Current saved facts, exact evidence and JSON; no request submission."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from types import FunctionType
from typing import Callable, Protocol, TypeAlias

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

