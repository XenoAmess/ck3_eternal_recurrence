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
from typing import Callable, Literal, Protocol, TypeAlias, runtime_checkable

from tools.g2_saved_campaign.file_stat_identity_v1 import (
    SCHEMA as STAT_SCHEMA, FileStatIdentityV1, parse_file_stat_identity_v1,
)

JsonValue: TypeAlias = "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
JsonObject: TypeAlias = dict[str, JsonValue]
MAX_SAFE = (1 << 53) - 1
MAX_FILE = 1048576
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


MAX_ORIGINAL_RESPONSE_BYTES_V1 = 2 * 1024 * 1024
MAX_SDK_SOURCE_BYTES_V1 = 2 * 1024 * 1024


@runtime_checkable
class SdkSourceReaderV1(BasisReaderV1, Protocol):
    def read_sdk_source(self, reference: ExactRefV1, limit: int) -> bytes: ...


def exact_sdk_source_bytes_v1(reader: BasisReaderV1, reference: ExactRefV1) -> bytes:
    """Read an independently authorized SDK source, never generic/RPC fallback."""
    need(isinstance(reference, ExactRefV1), "SDK source exact reference contract")
    parse_ref(reference.to_wire())
    need(reference.bytes <= MAX_SDK_SOURCE_BYTES_V1, "bounded original SDK source")
    need(isinstance(reader, SdkSourceReaderV1), "explicit SDK-source reader required")
    if not isinstance(reader, SdkSourceReaderV1):
        raise ValueError("explicit SDK-source reader required")
    raw = reader.read_sdk_source(reference, MAX_SDK_SOURCE_BYTES_V1)
    need(type(raw) is bytes and len(raw) == reference.bytes
         and hashlib.sha256(raw).hexdigest() == reference.sha256, "exact original SDK source")
    return raw


@runtime_checkable
class OriginalResponseReaderV1(BasisReaderV1, Protocol):
    def read_response(self, reference: ExactRefV1, limit: int) -> bytes: ...


def original_response_evidence_v1(reader: BasisReaderV1, reference: ExactRefV1) -> dict[str, object]:
    """A separate bounded RPC-evidence capability, not a larger source limit."""
    need(reference.bytes <= MAX_ORIGINAL_RESPONSE_BYTES_V1, "bounded original RPC evidence")
    if reference.bytes <= 1048576:
        return evidence(reader, reference, 1048576)
    need(isinstance(reader, OriginalResponseReaderV1), "explicit original-response reader required")
    if not isinstance(reader, OriginalResponseReaderV1):
        raise ValueError("explicit original-response reader required")
    raw = reader.read_response(reference, MAX_ORIGINAL_RESPONSE_BYTES_V1)
    need(len(raw) == reference.bytes and hashlib.sha256(raw).hexdigest() == reference.sha256,
         "exact original RPC evidence")
    return record(parse_json(raw))


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


# A later CAP guard failure is a different wire contract from the v1 SEM failure.
CAP_PRETRANSPORT_FAILURE_EPOCH_SCHEMA = "xar.current-saved-cap-pretransport-failure-epoch/v2"
CAP_PRETRANSPORT_FAILURE_QUALIFICATION_SCHEMA = "xar.current-saved-cap-pretransport-basis-qualification/v2"


@dataclass(frozen=True)
class CapPretransportFailureRefsV2:
    business_basis: ExactRefV1
    driver_review: ExactRefV1
    history_tail: ExactRefV1
    closure_index: ExactRefV1
    launch: ExactRefV1
    semantic_response: ExactRefV1
    semantic_after: ExactRefV1
    capability_rejection: ExactRefV1
    first_exception: ExactRefV1
    inflight: ExactRefV1
    before_action: ExactRefV1
    halt: ExactRefV1
    request_inventory: ExactRefV1
    sdk_closed: ExactRefV1
    supervisor_closed: ExactRefV1
    game_exit: ExactRefV1
    next: ExactRefV1
    canonical_qualification: ExactRefV1

    def items(self) -> tuple[tuple[str, ExactRefV1], ...]:
        return (("business_basis", self.business_basis), ("driver_review", self.driver_review),
            ("history_tail", self.history_tail), ("closure_index", self.closure_index),
            ("launch", self.launch), ("semantic_response", self.semantic_response),
            ("semantic_after", self.semantic_after), ("capability_rejection", self.capability_rejection),
            ("first_exception", self.first_exception), ("inflight", self.inflight),
            ("before_action", self.before_action), ("halt", self.halt),
            ("request_inventory", self.request_inventory), ("sdk_closed", self.sdk_closed),
            ("supervisor_closed", self.supervisor_closed), ("game_exit", self.game_exit),
            ("next", self.next), ("canonical_qualification", self.canonical_qualification))

    def to_wire(self) -> JsonObject:
        return {key: ref.to_wire() for key, ref in self.items()}


def parse_cap_pretransport_failure_refs_v2(value: object) -> CapPretransportFailureRefsV2:
    names = {"business_basis", "driver_review", "history_tail", "closure_index", "launch",
        "semantic_response", "semantic_after", "capability_rejection", "first_exception",
        "inflight", "before_action", "halt", "request_inventory", "sdk_closed",
        "supervisor_closed", "game_exit", "next", "canonical_qualification"}
    row = record(value, names)
    return CapPretransportFailureRefsV2(parse_ref(row["business_basis"]), parse_ref(row["driver_review"]),
        parse_ref(row["history_tail"]), parse_ref(row["closure_index"]), parse_ref(row["launch"]),
        parse_ref(row["semantic_response"]), parse_ref(row["semantic_after"]),
        parse_ref(row["capability_rejection"]), parse_ref(row["first_exception"]),
        parse_ref(row["inflight"]), parse_ref(row["before_action"]), parse_ref(row["halt"]),
        parse_ref(row["request_inventory"]), parse_ref(row["sdk_closed"]),
        parse_ref(row["supervisor_closed"]), parse_ref(row["game_exit"]), parse_ref(row["next"]),
        parse_ref(row["canonical_qualification"]))


@dataclass(frozen=True)
class CapPretransportFailureEpochV2:
    machine_id: str
    observed_at_utc: str
    refs: CapPretransportFailureRefsV2
    driver_payload_flags: ReadonlyClosedDriverFlagsV1

    def __post_init__(self) -> None:
        text(self.machine_id)
        utc(self.observed_at_utc)

    def to_wire(self) -> JsonObject:
        return {"schema": CAP_PRETRANSPORT_FAILURE_EPOCH_SCHEMA, "machine_id": self.machine_id,
            "observed_at_utc": self.observed_at_utc, "status": "CLOSED_CAP_PRETRANSPORT_GUARD_FAILURE",
            "refs": self.refs.to_wire(), "driver_payload_flags": self.driver_payload_flags.to_wire(),
            "new_ordinary_cycle_credit": 0, "new_game_day_credit": 0,
            "new_checkpoint_credit": 0, "original_requests_replayed": False}


def parse_cap_pretransport_failure_epoch_v2(
    value: object, *, expected_machine_id: str,
) -> CapPretransportFailureEpochV2:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "status", "refs",
        "driver_payload_flags", "new_ordinary_cycle_credit", "new_game_day_credit",
        "new_checkpoint_credit", "original_requests_replayed"})
    need(row["schema"] == CAP_PRETRANSPORT_FAILURE_EPOCH_SCHEMA
        and row["status"] == "CLOSED_CAP_PRETRANSPORT_GUARD_FAILURE"
        and row["machine_id"] == expected_machine_id, "explicit CAP pretransport failure epoch")
    for key in ("new_ordinary_cycle_credit", "new_game_day_credit", "new_checkpoint_credit"):
        need(integer(row[key]) == 0, "failed cold initialization gives no credit")
    need(row["original_requests_replayed"] is False, "no replay of failed original requests")
    return CapPretransportFailureEpochV2(text(row["machine_id"]), utc(row["observed_at_utc"]),
        parse_cap_pretransport_failure_refs_v2(row["refs"]),
        parse_readonly_closed_driver_flags_v1(row["driver_payload_flags"]))


@dataclass(frozen=True)
class ValidatedCapPretransportFailureEpochV2:
    epoch: CapPretransportFailureEpochV2
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
    previous_history_count: int
    history_rows: tuple[JsonObject, ...]


def _cap_restore_row_v2(
    value: object, *, checkpoint: JsonObject, index: int, previous_pid: int, current_pid: int,
) -> JsonObject:
    # Reuse the strict original row consumer with an index-only checkpoint view;
    # its checkpoint payload still must equal the real saved checkpoint.
    row = record(value, {"index", "command", "ok", "result"})
    result = record(row["result"], {"step", "accepted", "status", "backend_id", "source",
        "checkpoint", "restored_date_raw", "map_ready", "lifecycle"})
    lifecycle = record(result["lifecycle"], {"previous_pid", "pid"})
    need(integer(row["index"], 1) == index and row["command"] == "restore-checkpoint"
        and row["ok"] is True and result["step"] == "restore-checkpoint"
        and result["accepted"] is True and result["status"] == "restored"
        and result["backend_id"] == "native-headless" and result["source"] == "native-session-cold-start"
        and canonical_json_v1(result["checkpoint"]) == canonical_json_v1(checkpoint)
        and integer(result["restored_date_raw"]) == integer(checkpoint["date_raw"])
        and result["map_ready"] is True
        and integer(lifecycle["previous_pid"], 1, 2**32-1) == previous_pid
        and integer(lifecycle["pid"], 1, 2**32-1) == current_pid,
        "one exact additional restore bookkeeping row, never a business command")
    return json_object(row)


def _cap_guard_source_v2(
    index_refs: dict[str, object], failure: dict[str, object], *, reader: BasisReaderV1,
    root: Path, inflight: dict[str, object],
) -> None:
    """Bind the actual exception path to the original guard before its await."""
    import ast
    guard_ref = parse_ref(index_refs["guard_source"])
    queue_ref = parse_ref(index_refs["queue_source"])
    need(Path(guard_ref.path).resolve() == (root/"tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py").resolve()
        and Path(queue_ref.path).resolve() == (root/"root_p37c23_sdk_queue.py").resolve(),
        "original runtime sources, not a repaired public copy")
    guard = exact_read(reader, guard_ref, 196608).decode("utf-8")
    queue = exact_read(reader, queue_ref, 1048576).decode("utf-8")
    tree = ast.parse(guard)
    guards = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_inflight_guard"]
    encoders = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_json_bytes"]
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "call_tool" and n.body
        and any(isinstance(a, ast.Await) for a in ast.walk(n))]
    need(len(guards) == len(encoders) == len(calls) == 1, "unique original guard and transport consumer")
    body = ast.get_source_segment(guard, guards[0])
    need(body is not None and '_json_bytes(context.get("request"))' in body,
        "this failure is the original nested-request guard, not every CAP error")
    guard_calls = [n for n in ast.walk(calls[0]) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == "guard_current_saved_request_v1"]
    awaits = [n for n in ast.walk(calls[0]) if isinstance(n, ast.Await)
        and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
        and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == "self"
        and n.value.func.attr == "_call"]
    need(len(guard_calls) == len(awaits) == 1 and guard_calls[0].lineno < awaits[0].lineno,
        "the original guard precedes the only SDK transport await")
    trace = text(failure.get("traceback"))
    need(guard_ref.path.replace("\\", "/") in trace.replace("\\", "/")
        and queue_ref.path.replace("\\", "/") in trace.replace("\\", "/")
        and "in _inflight_guard" in trace and "in guard_current_saved_request_v1" in trace
        and "in call_tool" in trace and "in call" in trace
        and "_json_bytes(context.get(\"request\"))" in trace,
        "actual traceback reaches the original pretransport guard")
    need("request" not in inflight, "original Queue INFLIGHT is flat")
    namespace: dict[str, object] = {"json": json, "json_object": json_object}
    exec(compile(ast.Module(body=[encoders[0]], type_ignores=[]), "<original CAP encoder>", "exec"), namespace)
    encoder = namespace["_json_bytes"]
    need(isinstance(encoder, FunctionType), "original encoder function")
    if not isinstance(encoder, FunctionType):
        raise ValueError("original encoder")
    try:
        encoder(inflight.get("request"))
    except ValueError as error:
        need(str(error) == "object", "exact original pretransport failure")
    else:
        raise ValueError("original source no longer reproduces the recorded failure")
    need(any(isinstance(n, ast.AsyncFunctionDef) and n.name == "call" for n in ast.walk(ast.parse(queue))),
        "original Queue call consumer exists")


def _validate_cap_failure_evidence_v1(
    epoch: CapPretransportFailureEpochV2 | CapPostresponseFailureEpochV3, *, reader: BasisReaderV1,
) -> ValidatedCapPretransportFailureEpochV2 | ValidatedCapPostresponseFailureEpochV3:
    """Immutable historical evidence; current Driver stat is deliberately separate."""
    r = epoch.refs
    postresponse = isinstance(epoch, CapPostresponseFailureEpochV3)
    cap_ref = epoch.refs.capability_response if isinstance(epoch, CapPostresponseFailureEpochV3) else epoch.refs.capability_rejection
    cap_key = "capability_response" if postresponse else "capability_rejection"
    old = decode_current_saved_basis_v1(exact_read(reader, r.business_basis, 65536),
        expected_machine_id=epoch.machine_id)
    prior: ValidatedReadonlyColdFailureEpochV1 | ValidatedCapPretransportFailureEpochV2
    if postresponse:
        parent = parse_cap_pretransport_failure_epoch_v2(
            parse_json(exact_read(reader, old.refs.closure, 65536)), expected_machine_id=epoch.machine_id)
        prior = validate_cap_pretransport_failure_evidence_v2(parent, reader=reader)
    else:
        prior_epoch = parse_readonly_cold_failure_epoch_v1(
            parse_json(exact_read(reader, old.refs.closure, 65536)), expected_machine_id=epoch.machine_id)
        prior = validate_readonly_cold_failure_evidence_v1(prior_epoch, reader=reader)
    need(old.refs.driver == prior.driver_ref and old.refs.driver_close == prior.epoch.refs.driver_review
        and old.driver_identity == prior.driver_identity and old.refs.save == prior.save_ref
        and old.save_identity == prior.save_identity and old.next_sequence == prior.next_sequence
        and old.completed_cycles == prior.business_basis.completed_cycles
        and old.origin == prior.business_basis.origin and old.frame == prior.business_basis.frame
        and old.progress == prior.business_basis.progress and old.unknown_requests == prior.business_basis.unknown_requests
        and canonical_json_v1(old.checkpoint) == canonical_json_v1(prior.business_basis.checkpoint)
        and canonical_json_v1(old.campaign_goal_anchor) == canonical_json_v1(prior.business_basis.campaign_goal_anchor),
        "prior failed epoch retains the original saved business basis")
    prior_proof = evidence(reader, prior.epoch.refs.canonical_qualification, 16384)
    need(old.refs == replace(prior.business_basis.refs, driver=prior.driver_ref,
        driver_close=prior.epoch.refs.driver_review, closure=old.refs.closure,
        next=prior.epoch.refs.next, checkpoint_validator=parse_ref(prior_proof["validator"])),
        "prior immutable business references must remain exact")
    launch = evidence(reader, r.launch, 32768)
    pid = integer(launch.get("pid"), 1, 2**32-1)
    game = ReadonlyColdClosedGameV1(pid, _closed_filetime_v1(launch.get("creation_filetime")),
        text(launch.get("creation_date")))
    root = Path(r.launch.path).parent
    need(Path(r.launch.path).name == "ROOT-ACTUAL-GAME-LAUNCH-C23.json"
        and launch.get("machine_id") == epoch.machine_id and launch.get("old_save_loaded") is True
        and launch.get("load_save_name") == "xar_checkpoint" and launch.get("nonwar_only") is False
        and pid != prior.old_game.pid, "new actual cold Game identity")
    semseq = old.next_sequence
    semrequest: JsonObject = {"sequence": semseq, "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}}
    caprequest: JsonObject = {"sequence": semseq+1, "tool": "ck3_get_capabilities", "arguments": {}}
    semrow = evidence(reader, r.semantic_response, 262144)
    need(canonical_json_v1(semrow.get("request")) == canonical_json_v1(semrequest), "actual first SEM request")
    semantic = completed_body(semrow, "ck3_take_semantic_snapshot_private_v1")
    need(integer(semantic.get("date_raw")) == old.frame.date_raw
        and integer(semantic.get("episode_character_id"), 1) == old.frame.actor_character_id
        and semantic.get("episode_run_id") == old.frame.episode_run_id
        and semantic.get("paused") is True and semantic.get("map_ready") is True
        and semantic.get("one_life_terminal") is False
        and canonical_json_v1(semantic.get("campaign_goal")) == canonical_json_v1(old.campaign_goal_anchor),
        "SEM is a complete paused read of the unchanged saved frontier")
    after = evidence(reader, r.semantic_after, 16384)
    need(after.get("tool") == semrequest["tool"] and after.get("actual_status") == "cold_readiness_verified"
        and integer(after.get("loading_attempts")) == 0 and integer(after.get("new_business_credit")) == 0
        and after.get("response") == r.semantic_response.path
        and Path(text(after.get("request"))).resolve() == (root/"p37-requests"/f"{semseq:04d}-1-result.json").resolve(),
        "actual successful SEM postcheck marker, no business credit")
    cap = evidence(reader, cap_ref, 262144 if postresponse else 16384)
    need(canonical_json_v1(cap.get("request")) == canonical_json_v1(caprequest), "exact CAP request")
    failure = evidence(reader, r.first_exception, 16384)
    error = record(failure.get("exception_tree"))
    need(failure.get("replay_allowed") is False
        and canonical_json_v1(failure.get("request_identity")) == canonical_json_v1({
            "sequence": semseq+1, "tool": "ck3_get_capabilities", "command": None})
        and failure.get("traceback_truncated") is False and failure.get("locals_captured") is False,
        "exact retained CAP failure identity")
    if postresponse:
        capability = completed_body(cap, "ck3_get_capabilities")
        control = record(capability.get("native_session_control"))
        need(capability.get("episode_run_id") == old.frame.episode_run_id
            and integer(capability.get("episode_character_id"),1) == old.frame.actor_character_id
            and capability.get("episode_identity_pending") is False and capability.get("one_life_terminal") is False
            and control.get("driver_state_restored") is True and control.get("driver_state_restore_kind") == "cold_checkpoint"
            and control.get("episode_binding_state") == "active_resumed" and control.get("driver_state_error") is None
            and control.get("cold_candidate_rejection") is None,
            "completed CAP proves the actual restored saved episode")
        for body in (semantic, capability):
            diag = record(body.get("diagnostics")); hello = record(diag.get("hello"))
            need(integer(diag.get("bridge_pid"),1) == integer(hello.get("pid"),1) == pid
                and diag.get("pipe_name") == launch.get("pipe")
                and integer(diag.get("connection_generation"),1) == integer(hello.get("connection_generation"),1),
                "both completed reads belong to this exact Native Game and connection")
        need(failure.get("stage") == "request_dispatch" and error.get("type") == "KeyError"
            and error.get("message") == "'state'", "exact postresponse local governance failure")
    else:
        need("result" not in cap and cap.get("client_error") == "ValueError('object')"
            and cap.get("replay_allowed") is False, "CAP has no native result and must not be replayed")
        need(failure.get("stage") == "sdk_call" and error.get("type") == "ValueError"
            and error.get("message") == "object", "exact CAP pretransport guard exception")
    flat = evidence(reader, r.inflight, 16384)
    record(flat, {"sequence", "tool", "arguments", "request_file", "at_utc", "replay_allowed"})
    need(integer(flat["sequence"], 1) == semseq+1 and flat["tool"] == "ck3_get_capabilities"
        and record(flat["arguments"]) == {} and flat["replay_allowed"] is False
        and Path(text(flat["request_file"])).resolve() == (root/"p37-requests"/f"{semseq+1:04d}-1-result.json").resolve()
        and canonical_json_v1(evidence(reader, r.before_action, 16384)) == canonical_json_v1(flat),
        "the exact original flat CAP INFLIGHT and before-action remain retained")
    utc(flat["at_utc"])
    need(Path(r.inflight.path).resolve() == (root/"p37-queue"/f"INFLIGHT-{semseq+1:04d}.json").resolve()
        and Path(r.before_action.path).resolve() == (root/"p37-queue"/f"{semseq+1:04d}-before-action.json").resolve()
        and Path(r.semantic_after.path).resolve() == (root/"p37-queue"/f"{semseq:04d}-after-result.json").resolve(),
        "original Queue receipt paths")
    halt = evidence(reader, r.halt, 16384)
    need(halt.get("error_type") == ("KeyError" if postresponse else "RuntimeError")
        and halt.get("message") == ("'state'" if postresponse else "client outcome unknown; original request must not be resent")
        and halt.get("first_exception_receipt") == r.first_exception.path
        and canonical_json_v1(halt.get("original_request")) == canonical_json_v1(caprequest)
        and halt.get("original_response") == cap_ref.path
        and halt.get("replay_allowed") is False and halt.get("sdk_kept_alive_for_original_collection") is True
        and integer(halt.get("next_sequence"), 1) == semseq+2,
        "HALT and unknown original outcome remain immutable")
    inventory = evidence(reader, r.request_inventory, 16384)
    need(inventory.get("schema") == "xar.current-saved-closed-request-inventory/v1"
        and inventory.get("machine_id") == epoch.machine_id and inventory.get("reviewer") == "/root"
        and inventory.get("closed_directory_snapshot") is True
        and Path(text(inventory.get("runtime_root"))).resolve() == root.resolve()
        and integer(inventory.get("epoch_start_sequence"), 1) == semseq
        and rows(inventory.get("unmatched_new_request_files")) == []
        and rows(inventory.get("unmatched_new_response_files")) == [], "closed query-only request inventory")
    utc(inventory.get("observed_at_utc"))
    reqrefs = tuple(parse_ref(v) for v in rows(inventory.get("request_refs")))
    outrefs = tuple(parse_ref(v) for v in rows(inventory.get("response_refs")))
    need(len(reqrefs) == len(outrefs) == 2 and outrefs == (r.semantic_response, cap_ref),
        "only the original SEM and CAP, no action or FULL request")
    for ref, expected in zip(reqrefs, (semrequest, caprequest)):
        seq = integer(expected["sequence"], 1)
        need(Path(ref.path).resolve() == (root/"p37-requests"/f"{seq:04d}-1-result.json").resolve()
            and canonical_json_v1(evidence(reader, ref, 16384)) == canonical_json_v1(expected), "actual request bytes")
    for ref, seq in zip(outrefs, (semseq, semseq+1)):
        need(Path(ref.path).resolve() == (root/"p37-responses"/f"{seq:04d}-1-result.json").resolve(), "response path")
    nextseq = integer(evidence(reader, r.next, 16384).get("next_sequence"), 1)
    need(nextseq == semseq+2, "both consumed sequence numbers remain consumed")
    sdk = evidence(reader, r.sdk_closed, 16384)
    need(sdk.get("machine_id") == epoch.machine_id and sdk.get("status") == "ACTUAL_BOTH_SDK_EXITS_OBSERVED"
        and sdk.get("normal") is False and integer(sdk.get("launcher_exit_code")) == 1, "actual abnormal SDK shutdown")
    processes: list[ReadonlyColdClosedSdkV1] = []
    for item in rows(sdk.get("processes")):
        proc = record(item)
        role = proc.get("role")
        if role == "sdk_queue":
            typed_role: Literal["sdk_queue", "sdk_application"] = "sdk_queue"
            code = 1
        elif role == "sdk_application":
            typed_role = "sdk_application"
            code = 0
        else:
            raise ValueError("closed SDK role")
        need(proc.get("kernel_exit_observed") is True and integer(proc.get("wait_result")) == 0
            and integer(proc.get("exit_code")) == code and "observation_error" in proc
            and proc["observation_error"] is None, "actual SDK 1/0 kernel exits")
        processes.append(ReadonlyColdClosedSdkV1(typed_role, integer(proc.get("pid"), 1, 2**32-1),
            _closed_filetime_v1(proc.get("creation_filetime")), text(proc.get("executable")), code))
    need(len(processes) == 2 and {p.role for p in processes} == {"sdk_queue", "sdk_application"}
        and len({p.pid for p in processes}) == 2 and pid not in {p.pid for p in processes}, "distinct closed processes")
    supervisor = evidence(reader, r.supervisor_closed, 16384)
    cleanup = record(supervisor.get("owned_cleanup"))
    phase = record(supervisor.get("known_preload_phase"))
    if postresponse:
        game_exit_code, game_forced, game_classification = _cap_postresponse_game_exit_v3(
            r.game_exit, game=game, machine_id=epoch.machine_id, reader=reader)
    else:
        need(r.game_exit == r.supervisor_closed,"original v2 combined Game close source")
        game_exit_code, game_forced, game_classification = 1, True, "FORCED_OWNED_GAME_CLEANUP"
    need(supervisor.get("machine_id") == epoch.machine_id
        and supervisor.get("cleanup_classification") == game_classification
        and canonical_json_v1(sdk_without_launcher_v1(record(supervisor.get("sdk_actual_exit"))))
        == canonical_json_v1(sdk_without_launcher_v1(sdk))
        and integer(cleanup.get("ck3_pid"), 1) == pid and integer(cleanup.get("ck3_exit_code")) == game_exit_code
        and integer(cleanup.get("job_active_processes_final")) == 0
        and cleanup.get("tree_gone") is True and cleanup.get("cleanup_proven") is True
        and cleanup.get("ok") is True and rows(cleanup.get("contract_errors")) == []
        and cleanup.get("ck3_creation_date") == game.creation_date, "actual forced owned Game exit, Job0")
    for name in ("before", "after"):
        observed = record(phase.get(name))
        need(integer(observed.get("pid"), 1) == pid
            and _closed_filetime_v1(observed.get("creation_filetime")) == game.creation_filetime, "closed Game generation")
    index = evidence(reader, r.closure_index, 32768)
    if postresponse:
        need(index.get("failure_phase") == "CAP_POSTRESPONSE_LOCAL_CHECK_AFTER"
            and index.get("capability_after_result_absent") is True
            and index.get("normal_cold_bound_absent") is True
            and index.get("Game_normal_wm_close_qualified") is (game_classification == "NORMAL_GAME_CLOSE_OBSERVED"),
            "completed CAP failed only its local postcheck before BOUND")
    need(index.get("schema") == ("xar.readonly-cap-postresponse-abort-closure/v3" if postresponse else "xar.readonly-cap-pretransport-abort-closure/v2")
        and index.get("status") == ("CLOSED_CAP_POSTRESPONSE_LOCAL_FAILURE" if postresponse else "CLOSED_CAP_PRETRANSPORT_GUARD_FAILURE")
        and index.get("machine_id") == epoch.machine_id
        and parse_ref(index.get("original_basis_ref")) == r.business_basis
        and integer(index.get("next_sequence"), 1) == nextseq
        and integer(index.get("business_completed_cycles")) == old.completed_cycles
        and integer(index.get("business_date_raw")) == old.frame.date_raw
        and index.get("original_whole_wall_origin") == old.origin.original_wall_origin_utc
        and index.get("SDK_exit_codes") == [1, 0] and all(type(v) is int for v in rows(index["SDK_exit_codes"]))
        and index.get("SDK_normal") is False and integer(index.get("Game_exit_code")) == game_exit_code
        and index.get("Game_forced") is game_forced and integer(index.get("Game_Job_active_final")) == 0
        and index.get("all_owned_Tasks_actual_absent") is True and integer(index.get("owned_Task_count")) == 2
        and index.get("original_requests_replayed") is False, "explicit CAP-only failed epoch closure")
    for key in ("new_ordinary_cycle_credit", "new_game_day_credit", "new_checkpoint_credit"):
        need(integer(index.get(key)) == 0, "no failed-epoch gameplay or checkpoint credit")
    indexrefs = record(index.get("refs"), {"launch", "sdk_pair", "sdk_closed", "supervisor_sdk_exits",
        "supervisor_closed", "game_exit", "first_exception", "semantic_response", cap_key,
        "inflight", "next", "driver_review", "history_tail", "supervisor_spec", "display_spec",
        "supervisor_task_closed", "display_task_closed", "supervisor_unregister", "display_unregister",
        "screen_release", "recording_completed", "semantic_after", "before_action", "halt",
        "request_inventory", "queue_source"} | ({"cold_resume_source", "owner_source"} if postresponse else {"guard_source"}))
    for key, value in indexrefs.items():
        exact_read(reader, parse_ref(value), 1048576 if key in ("guard_source", "queue_source", "cold_resume_source", "owner_source") else 65536)
    for name in ("launch", "sdk_closed", "supervisor_closed", "game_exit", "first_exception",
        "semantic_response", "semantic_after", cap_key, "inflight", "before_action", "halt",
        "request_inventory", "next", "driver_review", "history_tail"):
        need(parse_ref(indexrefs[name]) == dict(r.items())[name], "closure reference binding: "+name)
    if postresponse:
        _cap_postresponse_source_v3(indexrefs, failure, reader=reader, root=root, governance_ref=old.refs.governance)
    else:
        _cap_guard_source_v2(indexrefs, failure, reader=reader, root=root, inflight=flat)
    review = evidence(reader, r.driver_review, 16384)
    need(review.get("schema") == ("xar.readonly-cap-postresponse-Driver-SAVE-review/v3" if postresponse else "xar.readonly-cap-pretransport-Driver-SAVE-review/v2")
        and review.get("status") == ("CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_AFTER_CAP_POSTCHECK_FAILURE" if postresponse else "CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_AFTER_CAP_GUARD_FAILURE")
        and review.get("machine_id") == epoch.machine_id
        and parse_ref(review.get("original_business_review")) == old.refs.driver_close, "actual changed Driver review")
    driver = record(review.get("Driver")); saved = record(review.get("SAVE"))
    driver_ref = parse_ref(driver.get("ref")); save_ref = parse_ref(saved.get("ref"))
    driver_id = parse_file_stat_identity_v1(driver.get("identity"), schema=STAT_SCHEMA)
    save_id = parse_file_stat_identity_v1(saved.get("identity"), schema=STAT_SCHEMA)
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
        "changed Driver retains the exact saved checkpoint and business state")
    history_count = integer(driver.get("command_history_count"), 1)
    tail = evidence(reader, r.history_tail, 32768)
    need(tail.get("schema") == ("xar.readonly-cap-postresponse-history-tail/v3" if postresponse else "xar.readonly-cap-pretransport-history-tail/v2")
        and tail.get("machine_id") == epoch.machine_id and parse_ref(tail.get("driver_review")) == r.driver_review
        and parse_file_stat_identity_v1(tail.get("driver_identity"), schema=STAT_SCHEMA) == driver_id
        and integer(tail.get("checkpoint_history_index"), 1) == integer(cp["history_index"], 1)
        and integer(tail.get("command_history_count"), 1) == history_count
        and history_count == prior.history_count+1, "restore lineage is retained plus one row")
    tailrows = rows(tail.get("post_checkpoint_history"))
    oldtail = rows(evidence(reader, prior.epoch.refs.history_tail, 16384).get("post_checkpoint_history"))
    need(len(tailrows) == len(oldtail)+1 and len(tailrows) == history_count-integer(cp["history_index"], 1)
        and canonical_json_v1(tailrows[:-1]) == canonical_json_v1(oldtail), "all proved previous restore rows remain exact")
    last = _cap_restore_row_v2(tailrows[-1], checkpoint=json_object(cp), index=history_count,
        previous_pid=prior.old_game.pid, current_pid=pid)
    raw = evidence(reader, parse_ref(review.get("raw_observation")), 16384)
    flags = record(raw.get("driver_payload_flags"))
    need(raw.get("schema") == "xar.raw-closed-driver-observation/v1"
        and raw.get("status") == "OBSERVED_NOT_QUALIFIED" and raw.get("machine_id") == epoch.machine_id
        and parse_ref(raw.get("Driver_ref")) == driver_ref
        and parse_file_stat_identity_v1(raw.get("Driver_identity"), schema=STAT_SCHEMA) == driver_id
        and parse_file_stat_identity_v1(raw.get("SAVE_identity"), schema=STAT_SCHEMA) == save_id
        and integer(raw.get("format_version")) == 2 and integer(raw.get("command_history_count")) == history_count
        and canonical_json_v1(raw.get("last_checkpoint")) == canonical_json_v1(cp)
        and canonical_json_v1(raw.get("post_checkpoint_history")) == canonical_json_v1(tailrows)
        and canonical_json_v1(raw.get("recorded_identity")) == canonical_json_v1(identity)
        and canonical_json_v1(raw.get("campaign_goal")) == canonical_json_v1(old.campaign_goal_anchor)
        and raw.get("session_binding_present") is False and raw.get("session_binding_value") is None
        and "session_binding_value" in raw and "session_binding" not in rows(raw.get("payload_top_keys"))
        and rows(flags.get("rollback_war_failures")) == [], "actual closed Driver witness matches the new epoch")
    for key in ("managed_restore_transaction", "rollback_war_failure", "succession_expectation"):
        need(key in flags and flags[key] is None, "actual Driver unresolved flag: "+key)
    if isinstance(epoch, CapPostresponseFailureEpochV3):
        checked3 = ValidatedCapPostresponseFailureEpochV3(epoch, old, driver_ref, driver_id, save_ref, save_id,
            history_count, last, game, tuple(sorted(processes, key=lambda p:p.role)), nextseq,
            text(identity.get("pipe_name")), prior.history_count, tuple(json_object(row) for row in tailrows))
        validate_cap_postresponse_canonical_reuse_v3(checked3, reader=reader)
        return checked3
    checked = ValidatedCapPretransportFailureEpochV2(epoch, old, driver_ref, driver_id, save_ref, save_id,
        history_count, last, game, tuple(sorted(processes, key=lambda p:p.role)), nextseq,
        text(identity.get("pipe_name")), prior.history_count, tuple(json_object(row) for row in tailrows))
    validate_cap_pretransport_canonical_reuse_v2(checked, reader=reader)
    return checked

def validate_cap_pretransport_failure_evidence_v2(
    epoch: CapPretransportFailureEpochV2, *, reader: BasisReaderV1,
) -> ValidatedCapPretransportFailureEpochV2:
    result = _validate_cap_failure_evidence_v1(epoch, reader=reader)
    if not isinstance(result, ValidatedCapPretransportFailureEpochV2):
        raise ValueError("pretransport evidence must retain its v2 type")
    return result

def validate_cap_postresponse_failure_evidence_v3(
    epoch: CapPostresponseFailureEpochV3, *, reader: BasisReaderV1,
) -> ValidatedCapPostresponseFailureEpochV3:
    result = _validate_cap_failure_evidence_v1(epoch, reader=reader)
    if not isinstance(result, ValidatedCapPostresponseFailureEpochV3):
        raise ValueError("postresponse evidence must retain its v3 type")
    return result



def validate_cap_pretransport_failure_epoch_v2(
    epoch: CapPretransportFailureEpochV2, *, reader: BasisReaderV1,
) -> ValidatedCapPretransportFailureEpochV2:
    checked = validate_cap_pretransport_failure_evidence_v2(epoch, reader=reader)
    need(reader.stat(checked.driver_ref.path) == checked.driver_identity
        and reader.stat(checked.save_ref.path) == checked.save_identity, "current closed Driver/SAVE identity")
    return checked


def validate_cap_pretransport_failure_driver_v2(
    validated: ValidatedCapPretransportFailureEpochV2, payload: object,
) -> None:
    row = record(payload)
    history = rows(row.get("command_history"))
    need(len(history) == validated.history_count
        and canonical_json_v1(history[-len(validated.history_rows):]) == canonical_json_v1(list(validated.history_rows)),
        "actual Driver full history agrees with every retained restore row")
    for name in ("managed_restore_transaction", "rollback_war_failure", "succession_expectation"):
        need(name in row and row[name] is None, "closed Driver unresolved transaction: "+name)
    need("session_binding" not in row, "no invented Driver session binding")


def validate_cap_pretransport_canonical_reuse_v2(
    validated: ValidatedCapPretransportFailureEpochV2, *, reader: BasisReaderV1,
) -> JsonObject:
    r = validated.epoch.refs
    proof = evidence(reader, r.canonical_qualification, 16384)
    prior_epoch = parse_readonly_cold_failure_epoch_v1(parse_json(exact_read(
        reader, validated.business_basis.refs.closure, 65536)), expected_machine_id=validated.epoch.machine_id)
    previous = evidence(reader, prior_epoch.refs.canonical_qualification, 16384)
    review = evidence(reader, r.driver_review, 16384)
    root_reads = integer(review.get("raw_Driver_body_read_count"), 1)
    need(proof.get("schema") == "xar.closed-cap-pretransport-save-identity-reuse/v2"
        and proof.get("status") == "PREVIOUS_CANONICAL_SAVE_IDENTITY_REUSED"
        and proof.get("machine_id") == validated.epoch.machine_id
        and proof.get("validation_mode") == "previous_canonical_save_identity_reuse"
        and proof.get("current_canonical_API_executed") is False
        and parse_ref(proof.get("previous_canonical_qualification")) == prior_epoch.refs.canonical_qualification
        and parse_ref(proof.get("driver_review")) == r.driver_review
        and parse_ref(proof.get("history_tail")) == r.history_tail
        and canonical_json_v1(proof.get("checkpoint")) == canonical_json_v1(validated.business_basis.checkpoint)
        and parse_file_stat_identity_v1(proof.get("Driver_identity"), schema=STAT_SCHEMA) == validated.driver_identity
        and parse_file_stat_identity_v1(proof.get("SAVE_identity"), schema=STAT_SCHEMA) == validated.save_identity
        and _readonly_stat_v1(previous.get("SAVE_identity")) == validated.save_identity
        and integer(proof.get("Driver_full_read_count"), 1) == root_reads
        and integer(proof.get("Driver_full_read_bytes")) == integer(review.get("Driver_body_bytes_read"))
        == validated.driver_ref.bytes*root_reads
        and integer(proof.get("SAVE_full_hash_count")) == 0 and integer(proof.get("SAVE_full_hash_bytes")) == 0
        and integer(review.get("SAVE_full_hash_count")) == 0 and integer(review.get("SAVE_body_bytes_read")) == 0
        and proof.get("SAVE_hash_reused_by_exact_identity") is True
        and proof.get("original_checkpoint_unchanged") is True
        and parse_ref(proof.get("validator")) == validated.business_basis.refs.checkpoint_validator,
        "previous canonical SAVE identity reused, no new canonical call or SAVE hash claimed")
    for key in ("new_ordinary_cycle_credit", "new_game_day_credit", "actual_constructor_or_Game_RPC_calls"):
        need(integer(proof.get(key)) == 0, "evidence gives no gameplay credit")
    utc(proof.get("observed_at_utc"))
    return json_object(proof)


def build_cap_pretransport_failure_basis_v2(
    validated: ValidatedCapPretransportFailureEpochV2, *, epoch_ref: ExactRefV1,
    observed_at_utc: str, sidecars: tuple[ExactRefV1, ...], reader: BasisReaderV1,
) -> CurrentSavedBasisV1:
    checked = validate_cap_pretransport_failure_epoch_v2(validated.epoch, reader=reader)
    need(checked == validated, "validated v2 evidence must be authentic")
    need(parse_cap_pretransport_failure_epoch_v2(parse_json(exact_read(reader, epoch_ref, 65536)),
        expected_machine_id=validated.epoch.machine_id) == validated.epoch, "exact v2 epoch bytes")
    for ref in sidecars:
        item = evidence(reader, ref, 65536)
        need("pending" not in item or item["pending"] is None, "no pending sidecar")
    old = validated.business_basis
    refs = replace(old.refs, driver=validated.driver_ref, driver_close=validated.epoch.refs.driver_review,
        closure=epoch_ref, next=validated.epoch.refs.next)
    return CurrentSavedBasisV1(old.machine_id, utc(observed_at_utc), old.origin, old.frame,
        old.completed_cycles, json_object(old.checkpoint), json_object(old.campaign_goal_anchor), refs,
        validated.driver_identity, validated.save_identity, validated.next_sequence, old.progress,
        old.unknown_requests, sidecars)


@dataclass(frozen=True)
class CapPretransportFailureQualificationV2:
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
        need(integer(self.root_driver_body_reads, 1) >= 1 and integer(self.root_save_hash_reads) == 0,
            "actual Root Driver reads and zero SAVE hashes")
        for count in (self.driver_body_reads, self.canonical_checkpoint_validator_calls, self.save_hash_reads):
            need(integer(count) == 0, "metadata creates no body read or canonical call")
        need(self.driver_identity_before == self.driver_identity_after
            and self.save_identity_before == self.save_identity_after, "stable metadata identity")

    def to_wire(self) -> JsonObject:
        return {"schema": CAP_PRETRANSPORT_FAILURE_QUALIFICATION_SCHEMA,
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "basis_ref": self.basis_ref.to_wire(), "epoch_ref": self.epoch_ref.to_wire(),
            "canonical_qualification_ref": self.canonical_qualification_ref.to_wire(),
            "driver_ref": self.driver_ref.to_wire(), "save_ref": self.save_ref.to_wire(),
            "driver_identity_before": json_object(self.driver_identity_before.to_wire()),
            "driver_identity_after": json_object(self.driver_identity_after.to_wire()),
            "save_identity_before": json_object(self.save_identity_before.to_wire()),
            "save_identity_after": json_object(self.save_identity_after.to_wire()),
            "validator_source_ref": self.validator_source_ref.to_wire(),
            "driver_history_rows": self.driver_history_rows, "root_driver_body_reads": self.root_driver_body_reads,
            "root_save_hash_reads": self.root_save_hash_reads, "driver_body_reads": self.driver_body_reads,
            "canonical_checkpoint_validator_calls": self.canonical_checkpoint_validator_calls,
            "save_hash_reads": self.save_hash_reads,
            "read_count_scope": "metadata_only_previous_canonical_save_identity_reuse"}


def parse_cap_pretransport_failure_qualification_v2(
    value: object, *, expected_machine_id: str,
) -> CapPretransportFailureQualificationV2:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "basis_ref", "epoch_ref",
        "canonical_qualification_ref", "driver_ref", "save_ref", "driver_identity_before",
        "driver_identity_after", "save_identity_before", "save_identity_after", "validator_source_ref",
        "driver_history_rows", "root_driver_body_reads", "root_save_hash_reads", "driver_body_reads",
        "canonical_checkpoint_validator_calls", "save_hash_reads", "read_count_scope"})
    need(row["schema"] == CAP_PRETRANSPORT_FAILURE_QUALIFICATION_SCHEMA
        and row["machine_id"] == expected_machine_id
        and row["read_count_scope"] == "metadata_only_previous_canonical_save_identity_reuse",
        "explicit v2 CAP failure qualification")
    return CapPretransportFailureQualificationV2(text(row["machine_id"]), utc(row["observed_at_utc"]),
        parse_ref(row["basis_ref"]), parse_ref(row["epoch_ref"]), parse_ref(row["canonical_qualification_ref"]),
        parse_ref(row["driver_ref"]), parse_ref(row["save_ref"]),
        parse_file_stat_identity_v1(row["driver_identity_before"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["driver_identity_after"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_before"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_after"], schema=STAT_SCHEMA),
        parse_ref(row["validator_source_ref"]), integer(row["driver_history_rows"], 1),
        integer(row["root_driver_body_reads"]), integer(row["root_save_hash_reads"]),
        integer(row["driver_body_reads"]), integer(row["canonical_checkpoint_validator_calls"]),
        integer(row["save_hash_reads"]))


def build_cap_pretransport_failure_qualification_v2(
    validated: ValidatedCapPretransportFailureEpochV2, basis: CurrentSavedBasisV1, *,
    basis_ref: ExactRefV1, reader: BasisReaderV1, observed_at_utc: str,
) -> CapPretransportFailureQualificationV2:
    expected = build_cap_pretransport_failure_basis_v2(validated, epoch_ref=basis.refs.closure,
        observed_at_utc=basis.observed_at_utc, sidecars=basis.sidecars, reader=reader)
    need(canonical_json_v1(expected.to_wire()) == canonical_json_v1(basis.to_wire())
        and canonical_json_v1(parse_json(exact_read(reader, basis_ref, 65536))) == canonical_json_v1(basis.to_wire()),
        "qualification binds the exact new basis without new business credit")
    proof = validate_cap_pretransport_canonical_reuse_v2(validated, reader=reader)
    return CapPretransportFailureQualificationV2(basis.machine_id, utc(observed_at_utc), basis_ref,
        basis.refs.closure, validated.epoch.refs.canonical_qualification, basis.refs.driver, basis.refs.save,
        basis.driver_identity, basis.driver_identity, basis.save_identity, basis.save_identity,
        basis.refs.checkpoint_validator, validated.history_count, integer(proof["Driver_full_read_count"], 1), 0)

CAP_POSTRESPONSE_FAILURE_EPOCH_SCHEMA="xar.current-saved-cap-postresponse-failure-epoch/v3"
CAP_POSTRESPONSE_FAILURE_QUALIFICATION_SCHEMA="xar.current-saved-cap-postresponse-basis-qualification/v3"

@dataclass(frozen=True)
class CapPostresponseFailureRefsV3:
    business_basis: ExactRefV1
    driver_review: ExactRefV1
    history_tail: ExactRefV1
    closure_index: ExactRefV1
    launch: ExactRefV1
    semantic_response: ExactRefV1
    semantic_after: ExactRefV1
    capability_response: ExactRefV1
    first_exception: ExactRefV1
    inflight: ExactRefV1
    before_action: ExactRefV1
    halt: ExactRefV1
    request_inventory: ExactRefV1
    sdk_closed: ExactRefV1
    supervisor_closed: ExactRefV1
    game_exit: ExactRefV1
    next: ExactRefV1
    canonical_qualification: ExactRefV1

    def items(self) -> tuple[tuple[str, ExactRefV1], ...]:
        return (("business_basis", self.business_basis), ("driver_review", self.driver_review),
            ("history_tail", self.history_tail), ("closure_index", self.closure_index),
            ("launch", self.launch), ("semantic_response", self.semantic_response),
            ("semantic_after", self.semantic_after), ("capability_response", self.capability_response),
            ("first_exception", self.first_exception), ("inflight", self.inflight),
            ("before_action", self.before_action), ("halt", self.halt),
            ("request_inventory", self.request_inventory), ("sdk_closed", self.sdk_closed),
            ("supervisor_closed", self.supervisor_closed), ("game_exit", self.game_exit),
            ("next", self.next), ("canonical_qualification", self.canonical_qualification))

    def to_wire(self) -> JsonObject:
        return {key: ref.to_wire() for key, ref in self.items()}


def parse_cap_postresponse_failure_refs_v3(value: object) -> CapPostresponseFailureRefsV3:
    names = {"business_basis", "driver_review", "history_tail", "closure_index", "launch",
        "semantic_response", "semantic_after", "capability_response", "first_exception",
        "inflight", "before_action", "halt", "request_inventory", "sdk_closed",
        "supervisor_closed", "game_exit", "next", "canonical_qualification"}
    row = record(value, names)
    return CapPostresponseFailureRefsV3(parse_ref(row["business_basis"]), parse_ref(row["driver_review"]),
        parse_ref(row["history_tail"]), parse_ref(row["closure_index"]), parse_ref(row["launch"]),
        parse_ref(row["semantic_response"]), parse_ref(row["semantic_after"]),
        parse_ref(row["capability_response"]), parse_ref(row["first_exception"]),
        parse_ref(row["inflight"]), parse_ref(row["before_action"]), parse_ref(row["halt"]),
        parse_ref(row["request_inventory"]), parse_ref(row["sdk_closed"]),
        parse_ref(row["supervisor_closed"]), parse_ref(row["game_exit"]), parse_ref(row["next"]),
        parse_ref(row["canonical_qualification"]))


@dataclass(frozen=True)
class CapPostresponseFailureEpochV3:
    machine_id: str
    observed_at_utc: str
    refs: CapPostresponseFailureRefsV3
    driver_payload_flags: ReadonlyClosedDriverFlagsV1

    def __post_init__(self) -> None:
        text(self.machine_id)
        utc(self.observed_at_utc)

    def to_wire(self) -> JsonObject:
        return {"schema": CAP_POSTRESPONSE_FAILURE_EPOCH_SCHEMA, "machine_id": self.machine_id,
            "observed_at_utc": self.observed_at_utc, "status": "CLOSED_CAP_POSTRESPONSE_LOCAL_FAILURE",
            "refs": self.refs.to_wire(), "driver_payload_flags": self.driver_payload_flags.to_wire(),
            "new_ordinary_cycle_credit": 0, "new_game_day_credit": 0,
            "new_checkpoint_credit": 0, "original_requests_replayed": False}


def parse_cap_postresponse_failure_epoch_v3(
    value: object, *, expected_machine_id: str,
) -> CapPostresponseFailureEpochV3:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "status", "refs",
        "driver_payload_flags", "new_ordinary_cycle_credit", "new_game_day_credit",
        "new_checkpoint_credit", "original_requests_replayed"})
    need(row["schema"] == CAP_POSTRESPONSE_FAILURE_EPOCH_SCHEMA
        and row["status"] == "CLOSED_CAP_POSTRESPONSE_LOCAL_FAILURE"
        and row["machine_id"] == expected_machine_id, "explicit CAP pretransport failure epoch")
    for key in ("new_ordinary_cycle_credit", "new_game_day_credit", "new_checkpoint_credit"):
        need(integer(row[key]) == 0, "failed cold initialization gives no credit")
    need(row["original_requests_replayed"] is False, "no replay of failed original requests")
    return CapPostresponseFailureEpochV3(text(row["machine_id"]), utc(row["observed_at_utc"]),
        parse_cap_postresponse_failure_refs_v3(row["refs"]),
        parse_readonly_closed_driver_flags_v1(row["driver_payload_flags"]))


@dataclass(frozen=True)
class ValidatedCapPostresponseFailureEpochV3:
    epoch: CapPostresponseFailureEpochV3
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
    previous_history_count: int
    history_rows: tuple[JsonObject, ...]


def validate_cap_postresponse_failure_epoch_v3(
    epoch: CapPostresponseFailureEpochV3, *, reader: BasisReaderV1,
) -> ValidatedCapPostresponseFailureEpochV3:
    checked = validate_cap_postresponse_failure_evidence_v3(epoch, reader=reader)
    need(reader.stat(checked.driver_ref.path) == checked.driver_identity
        and reader.stat(checked.save_ref.path) == checked.save_identity, "current closed Driver/SAVE identity")
    return checked


def validate_cap_postresponse_failure_driver_v3(
    validated: ValidatedCapPostresponseFailureEpochV3, payload: object,
) -> None:
    row = record(payload)
    history = rows(row.get("command_history"))
    need(len(history) == validated.history_count
        and canonical_json_v1(history[-len(validated.history_rows):]) == canonical_json_v1(list(validated.history_rows)),
        "actual Driver full history agrees with every retained restore row")
    for name in ("managed_restore_transaction", "rollback_war_failure", "succession_expectation"):
        need(name in row and row[name] is None, "closed Driver unresolved transaction: "+name)
    need("session_binding" not in row, "no invented Driver session binding")


def build_cap_postresponse_failure_basis_v3(
    validated: ValidatedCapPostresponseFailureEpochV3, *, epoch_ref: ExactRefV1,
    observed_at_utc: str, sidecars: tuple[ExactRefV1, ...], reader: BasisReaderV1,
) -> CurrentSavedBasisV1:
    checked = validate_cap_postresponse_failure_epoch_v3(validated.epoch, reader=reader)
    need(checked == validated, "validated v3 evidence must be authentic")
    need(parse_cap_postresponse_failure_epoch_v3(parse_json(exact_read(reader, epoch_ref, 65536)),
        expected_machine_id=validated.epoch.machine_id) == validated.epoch, "exact v3 epoch bytes")
    for ref in sidecars:
        item = evidence(reader, ref, 65536)
        need("pending" not in item or item["pending"] is None, "no pending sidecar")
    old = validated.business_basis
    refs = replace(old.refs, driver=validated.driver_ref, driver_close=validated.epoch.refs.driver_review,
        closure=epoch_ref, next=validated.epoch.refs.next)
    return CurrentSavedBasisV1(old.machine_id, utc(observed_at_utc), old.origin, old.frame,
        old.completed_cycles, json_object(old.checkpoint), json_object(old.campaign_goal_anchor), refs,
        validated.driver_identity, validated.save_identity, validated.next_sequence, old.progress,
        old.unknown_requests, sidecars)


@dataclass(frozen=True)
class CapPostresponseFailureQualificationV3:
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
        need(integer(self.root_driver_body_reads, 1) >= 1 and integer(self.root_save_hash_reads) == 0,
            "actual Root Driver reads and zero SAVE hashes")
        for count in (self.driver_body_reads, self.canonical_checkpoint_validator_calls, self.save_hash_reads):
            need(integer(count) == 0, "metadata creates no body read or canonical call")
        need(self.driver_identity_before == self.driver_identity_after
            and self.save_identity_before == self.save_identity_after, "stable metadata identity")

    def to_wire(self) -> JsonObject:
        return {"schema": CAP_POSTRESPONSE_FAILURE_QUALIFICATION_SCHEMA,
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "basis_ref": self.basis_ref.to_wire(), "epoch_ref": self.epoch_ref.to_wire(),
            "canonical_qualification_ref": self.canonical_qualification_ref.to_wire(),
            "driver_ref": self.driver_ref.to_wire(), "save_ref": self.save_ref.to_wire(),
            "driver_identity_before": json_object(self.driver_identity_before.to_wire()),
            "driver_identity_after": json_object(self.driver_identity_after.to_wire()),
            "save_identity_before": json_object(self.save_identity_before.to_wire()),
            "save_identity_after": json_object(self.save_identity_after.to_wire()),
            "validator_source_ref": self.validator_source_ref.to_wire(),
            "driver_history_rows": self.driver_history_rows, "root_driver_body_reads": self.root_driver_body_reads,
            "root_save_hash_reads": self.root_save_hash_reads, "driver_body_reads": self.driver_body_reads,
            "canonical_checkpoint_validator_calls": self.canonical_checkpoint_validator_calls,
            "save_hash_reads": self.save_hash_reads,
            "read_count_scope": "metadata_only_previous_canonical_save_identity_reuse"}


def parse_cap_postresponse_failure_qualification_v3(
    value: object, *, expected_machine_id: str,
) -> CapPostresponseFailureQualificationV3:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "basis_ref", "epoch_ref",
        "canonical_qualification_ref", "driver_ref", "save_ref", "driver_identity_before",
        "driver_identity_after", "save_identity_before", "save_identity_after", "validator_source_ref",
        "driver_history_rows", "root_driver_body_reads", "root_save_hash_reads", "driver_body_reads",
        "canonical_checkpoint_validator_calls", "save_hash_reads", "read_count_scope"})
    need(row["schema"] == CAP_POSTRESPONSE_FAILURE_QUALIFICATION_SCHEMA
        and row["machine_id"] == expected_machine_id
        and row["read_count_scope"] == "metadata_only_previous_canonical_save_identity_reuse",
        "explicit v2 CAP failure qualification")
    return CapPostresponseFailureQualificationV3(text(row["machine_id"]), utc(row["observed_at_utc"]),
        parse_ref(row["basis_ref"]), parse_ref(row["epoch_ref"]), parse_ref(row["canonical_qualification_ref"]),
        parse_ref(row["driver_ref"]), parse_ref(row["save_ref"]),
        parse_file_stat_identity_v1(row["driver_identity_before"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["driver_identity_after"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_before"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_after"], schema=STAT_SCHEMA),
        parse_ref(row["validator_source_ref"]), integer(row["driver_history_rows"], 1),
        integer(row["root_driver_body_reads"]), integer(row["root_save_hash_reads"]),
        integer(row["driver_body_reads"]), integer(row["canonical_checkpoint_validator_calls"]),
        integer(row["save_hash_reads"]))


def build_cap_postresponse_failure_qualification_v3(
    validated: ValidatedCapPostresponseFailureEpochV3, basis: CurrentSavedBasisV1, *,
    basis_ref: ExactRefV1, reader: BasisReaderV1, observed_at_utc: str,
) -> CapPostresponseFailureQualificationV3:
    expected = build_cap_postresponse_failure_basis_v3(validated, epoch_ref=basis.refs.closure,
        observed_at_utc=basis.observed_at_utc, sidecars=basis.sidecars, reader=reader)
    need(canonical_json_v1(expected.to_wire()) == canonical_json_v1(basis.to_wire())
        and canonical_json_v1(parse_json(exact_read(reader, basis_ref, 65536))) == canonical_json_v1(basis.to_wire()),
        "qualification binds the exact new basis without new business credit")
    proof = validate_cap_postresponse_canonical_reuse_v3(validated, reader=reader)
    return CapPostresponseFailureQualificationV3(basis.machine_id, utc(observed_at_utc), basis_ref,
        basis.refs.closure, validated.epoch.refs.canonical_qualification, basis.refs.driver, basis.refs.save,
        basis.driver_identity, basis.driver_identity, basis.save_identity, basis.save_identity,
        basis.refs.checkpoint_validator, validated.history_count, integer(proof["Driver_full_read_count"], 1), 0)



def _cap_postresponse_game_exit_v3(
    reference: ExactRefV1, *, game: ReadonlyColdClosedGameV1,
    machine_id: str, reader: BasisReaderV1,
) -> tuple[int, bool, str]:
    value = evidence(reader, reference, 16384)
    forced = value.get("forced_owned_job_cleanup"); normal = value.get("normal_wm_close_qualified")
    code = integer(value.get("exit_code"),0,2**32-1)
    need(type(forced) is bool and type(normal) is bool
        and value.get("machine_id") == machine_id and value.get("kernel_signaled") is True
        and integer(value.get("pid"),1) == game.pid
        and _closed_filetime_v1(value.get("creation_filetime")) == game.creation_filetime
        and value.get("sdk_actual_exit_status") == "ACTUAL_BOTH_SDK_EXITS_OBSERVED",
        "exact independently observed closed Game generation")
    if forced is True:
        need(normal is False,"forced cleanup is not a qualified normal close")
        return code,True,"FORCED_OWNED_GAME_CLEANUP"
    if normal is True:
        need(code == 0,"qualified normal WM_CLOSE exited successfully")
        return code,False,"NORMAL_GAME_CLOSE_OBSERVED"
    return code,False,"GAME_EXIT_OBSERVED_NORMAL_CLOSE_NOT_QUALIFIED"


def validate_cap_postresponse_canonical_reuse_v3(
    validated: ValidatedCapPostresponseFailureEpochV3, *, reader: BasisReaderV1,
) -> JsonObject:
    r = validated.epoch.refs
    proof = evidence(reader, r.canonical_qualification, 16384)
    prior_epoch = parse_cap_pretransport_failure_epoch_v2(parse_json(exact_read(
        reader, validated.business_basis.refs.closure, 65536)), expected_machine_id=validated.epoch.machine_id)
    previous = evidence(reader, prior_epoch.refs.canonical_qualification, 16384)
    review = evidence(reader, r.driver_review, 16384)
    root_reads = integer(review.get("raw_Driver_body_read_count"), 1)
    need(proof.get("schema") == "xar.closed-cap-postresponse-save-identity-reuse/v3"
        and proof.get("status") == "PREVIOUS_CANONICAL_SAVE_IDENTITY_REUSED"
        and proof.get("machine_id") == validated.epoch.machine_id
        and proof.get("validation_mode") == "previous_canonical_save_identity_reuse"
        and proof.get("current_canonical_API_executed") is False
        and parse_ref(proof.get("previous_canonical_qualification")) == prior_epoch.refs.canonical_qualification
        and parse_ref(proof.get("driver_review")) == r.driver_review
        and parse_ref(proof.get("history_tail")) == r.history_tail
        and canonical_json_v1(proof.get("checkpoint")) == canonical_json_v1(validated.business_basis.checkpoint)
        and parse_file_stat_identity_v1(proof.get("Driver_identity"), schema=STAT_SCHEMA) == validated.driver_identity
        and parse_file_stat_identity_v1(proof.get("SAVE_identity"), schema=STAT_SCHEMA) == validated.save_identity
        and parse_file_stat_identity_v1(previous.get("SAVE_identity"), schema=STAT_SCHEMA) == validated.save_identity
        and integer(proof.get("Driver_full_read_count"), 1) == root_reads
        and integer(proof.get("Driver_full_read_bytes")) == integer(review.get("Driver_body_bytes_read"))
        == validated.driver_ref.bytes*root_reads
        and integer(proof.get("SAVE_full_hash_count")) == 0 and integer(proof.get("SAVE_full_hash_bytes")) == 0
        and integer(review.get("SAVE_full_hash_count")) == 0 and integer(review.get("SAVE_body_bytes_read")) == 0
        and proof.get("SAVE_hash_reused_by_exact_identity") is True
        and proof.get("original_checkpoint_unchanged") is True
        and parse_ref(proof.get("validator")) == validated.business_basis.refs.checkpoint_validator,
        "previous canonical SAVE identity reused, no new canonical call or SAVE hash claimed")
    for key in ("new_ordinary_cycle_credit", "new_game_day_credit", "actual_constructor_or_Game_RPC_calls"):
        need(integer(proof.get(key)) == 0, "evidence gives no gameplay credit")
    utc(proof.get("observed_at_utc"))
    return json_object(proof)


def _cap_postresponse_source_v3(
    refs: dict[str, object], failure: dict[str, object], *, reader: BasisReaderV1,
    root: Path, governance_ref: ExactRefV1,
) -> None:
    import ast
    cold_ref = parse_ref(refs["cold_resume_source"]); owner_ref = parse_ref(refs["owner_source"])
    queue_ref = parse_ref(refs["queue_source"])
    need(Path(cold_ref.path).resolve() == (root/"root_p37c23_cold_resume.py").resolve()
        and Path(owner_ref.path).resolve() == (root/"tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py").resolve()
        and Path(queue_ref.path).resolve() == (root/"root_p37c23_sdk_queue.py").resolve(),
        "original frozen postcheck source identities")
    cold = ast.parse(exact_read(reader,cold_ref,1048576))
    methods = [n for n in ast.walk(cold) if isinstance(n,ast.FunctionDef) and n.name == "check_after"]
    need(len(methods) == 1,"one original cold check_after")
    assignments = [n for n in ast.walk(methods[0]) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id == "self"
                and t.attr == "governance_result_state" for t in n.targets)]
    expected = ast.parse("self.governance_result_state = copy.deepcopy(cold['governance']['state'])").body[0]
    need(len(assignments) == 1 and ast.dump(assignments[0],include_attributes=False)
        == ast.dump(expected,include_attributes=False),"actual legacy CAP governance consumer")
    trace = text(failure.get("traceback"))
    need(str(Path(cold_ref.path)) in trace
        and "line "+str(assignments[0].lineno)+", in check_after" in trace,
        "the retained exception identifies the exact failing postresponse assignment")
    tree = ast.parse(exact_read(reader,owner_ref,1048576))
    inputs = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == "cold_inputs_v1"]
    need(len(inputs) == 1,"one original owner cold input producer")
    returns = [n for n in ast.walk(inputs[0]) if isinstance(n,ast.Return) and isinstance(n.value,ast.Tuple)]
    need(len(returns) == 1 and isinstance(returns[0].value,ast.Tuple)
        and len(returns[0].value.elts) == 5
        and ast.unparse(returns[0].value.elts[1]) == "_clone(inputs.governance)",
        "the failed epoch really supplied unprojected governance, without a new wire alias")
    governance = evidence(reader,governance_ref,262144)
    need("state" not in governance and "governance_result_state" in governance
        and "pending_focus" in governance,"the exact source omits the legacy state field")


CONTINUITY_FORWARD_SCHEMA = "xar.current-saved-continuity-basis-forward/v1"
CONTINUITY_FORWARD_QUALIFICATION_SCHEMA = "xar.current-saved-continuity-basis-qualification/v1"


@dataclass(frozen=True, slots=True)
class CurrentSavedContinuityForwardV1:
    machine_id: str
    observed_at_utc: str
    original_basis_ref: ExactRefV1
    original_validation_ref: ExactRefV1
    continuity_binding_ref: ExactRefV1
    ledger_ref: ExactRefV1

    def to_wire(self) -> JsonObject:
        return {"schema": CONTINUITY_FORWARD_SCHEMA, "machine_id": text(self.machine_id),
            "observed_at_utc": utc(self.observed_at_utc),
            "original_basis_ref": self.original_basis_ref.to_wire(),
            "original_validation_ref": self.original_validation_ref.to_wire(),
            "continuity_binding_ref": self.continuity_binding_ref.to_wire(),
            "ledger_ref": self.ledger_ref.to_wire(), "scope": "continuity_metadata_forward_only",
            "new_ordinary_cycle_credit": 0, "new_game_day_credit": 0,
            "new_Driver_or_SAVE_identity_claimed": False, "original_actions_replayed": False}


def parse_current_saved_continuity_forward_v1(
    value: object, *, expected_machine_id: str,
) -> CurrentSavedContinuityForwardV1:
    r = record(value, {"schema", "machine_id", "observed_at_utc", "original_basis_ref",
        "original_validation_ref", "continuity_binding_ref", "ledger_ref", "scope",
        "new_ordinary_cycle_credit", "new_game_day_credit",
        "new_Driver_or_SAVE_identity_claimed", "original_actions_replayed"})
    need(r["schema"] == CONTINUITY_FORWARD_SCHEMA and r["machine_id"] == expected_machine_id
         and r["scope"] == "continuity_metadata_forward_only"
         and integer(r["new_ordinary_cycle_credit"], 0, 0) == 0
         and integer(r["new_game_day_credit"], 0, 0) == 0
         and r["new_Driver_or_SAVE_identity_claimed"] is False
         and r["original_actions_replayed"] is False, "continuity-only basis forward")
    return CurrentSavedContinuityForwardV1(text(r["machine_id"]), utc(r["observed_at_utc"]),
        parse_ref(r["original_basis_ref"]), parse_ref(r["original_validation_ref"]),
        parse_ref(r["continuity_binding_ref"]), parse_ref(r["ledger_ref"]))


def _continuity_forward_head_v1(
    forward: CurrentSavedContinuityForwardV1, original: CurrentSavedBasisV1, *,
    reader: BasisReaderV1,
) -> JsonObject:
    from tools.g2_saved_campaign.current_saved_continuity_v1 import (
        continuity_digest_v1, _state, validate_continuity_source_identities_v1,
    )
    binding = record(evidence(reader, forward.continuity_binding_ref, 32768),
        {"schema", "machine_id", "canonical_path", "anchor_ref", "anchor_digest", "anchor_sequence",
         "snapshot_ref", "event_refs", "source_index_refs", "head_sequence", "head_digest",
         "missing_source_indexes", "snapshot_needs_recovery", "ready", "ledger_writes", "source_identities"})
    canonical = Path(text(binding.get("canonical_path"))).resolve()
    need(all(Path(reference.path).resolve() != canonical
             for reference in (forward.ledger_ref, original.refs.ledger)),
         "immutable retained head and historical anchor must not be the mutable canonical path")
    need(binding.get("schema") == "xar.current-saved-continuity-binding/v1"
         and binding.get("machine_id") == original.machine_id
         and parse_ref(binding.get("anchor_ref")) == original.refs.ledger
         and binding.get("ready") is True and binding.get("snapshot_needs_recovery") is False
         and rows(binding.get("missing_source_indexes")) == []
         and integer(binding.get("ledger_writes"), 0, 0) == 0,
         "captured ready continuity lineage")
    # This historical replay reads immutable anchor/events and the retained
    # head copy. The mutable canonical snapshot is provenance, never reread as
    # though its old bytes should remain current after a legitimate commit.
    index_refs = tuple(parse_ref(x) for x in rows(binding.get("source_index_refs")))
    indexes = {x.path: x for x in index_refs}
    need(len(indexes) == len(index_refs), "unique captured source indexes")
    events = tuple(parse_ref(x) for x in rows(binding.get("event_refs")))
    need(len(events) <= 256 and len({x.path for x in events}) == len(events), "finite unique event chain")
    snapshot = parse_ref(binding.get("snapshot_ref"))
    need(Path(snapshot.path).resolve() == Path(text(binding["canonical_path"])).resolve(),
         "captured snapshot is the canonical path")
    expected_refs = (original.refs.ledger, snapshot, *events, *index_refs)
    captured: dict[str, tuple[ExactRefV1, FileStatIdentityV1]] = {}
    for value in rows(binding.get("source_identities")):
        item = record(value, {"reference", "identity"}); reference = parse_ref(item["reference"])
        captured_identity = parse_file_stat_identity_v1(item["identity"], schema=STAT_SCHEMA)
        need(reference.path not in captured and captured_identity.bytes == reference.bytes,
             "unique captured source identity with exact length")
        captured[reference.path] = (reference, captured_identity)
    need({path: reference for path, (reference, _) in captured.items()}
         == {reference.path: reference for reference in expected_refs},
         "captured identities bind exactly the immutable chain and historical snapshot")
    captured_sources = tuple(captured.values())
    validate_continuity_source_identities_v1(captured_sources, mutable_snapshot_ref=snapshot, reader=reader)
    state = _state(evidence(reader, original.refs.ledger, 65536), original.machine_id)
    need(binding.get("anchor_digest") == continuity_digest_v1(state)
         and integer(binding.get("anchor_sequence")) == integer(state.get("sequence")),
         "exact original continuity anchor")
    origin = (state.get("window_id"), state.get("start_date_raw"), state.get("target_date_raw"))
    for event_ref in events:
        event = record(evidence(reader, event_ref, 65536), {"sequence", "at_utc", "kind", "details", "identity", "previous_sha256", "after"})
        utc(event["at_utc"])
        need(Path(event_ref.path).resolve() == (Path(text(binding.get("canonical_path"))).with_name("ROOT-CONTINUITY-WINDOW-EVENTS") / f"{integer(state.get('sequence')) + 1:08d}.json").resolve(), "canonical committed event path")
        sequence = integer(state.get("sequence")) + 1
        details = json_object(event.get("details")); kind = text(event.get("kind"))
        need(bool(details.get("source")), "committed event exact source")
        identity = continuity_digest_v1({"kind": kind, "details": details})
        need(integer(event.get("sequence"), 1) == sequence
             and event.get("previous_sha256") == continuity_digest_v1(state)
             and event.get("identity") == identity, "exact committed continuity event chain")
        state = _state(event.get("after"), original.machine_id)
        need(integer(state.get("sequence"), 1) == sequence
             and state.get("last_event_identity") == identity
             and state.get("machine_id") == original.machine_id
             and (state.get("window_id"), state.get("start_date_raw"), state.get("target_date_raw")) == origin,
             "event preserves original campaign/window")
        key = continuity_digest_v1({"kind": kind, "evidence_id": text(details.get("evidence_id"))})
        path = str(Path(event_ref.path).parent / ("source-" + key + ".json"))
        need(path in indexes, "captured source index missing")
        index = record(evidence(reader, indexes.pop(path), 65536), {"sequence", "identity"})
        need(integer(index.get("sequence"), 1) == sequence and index.get("identity") == identity,
             "source index/event binding")
    need(not indexes and integer(binding.get("head_sequence")) == integer(state.get("sequence"))
         and binding.get("head_digest") == continuity_digest_v1(state),
         "complete captured head and index chain")
    head = json_object(evidence(reader, forward.ledger_ref, 65536))
    need((snapshot.bytes, snapshot.sha256) == (forward.ledger_ref.bytes, forward.ledger_ref.sha256),
         "retained head bytes match the captured canonical snapshot")
    need(canonical_json_v1(head) == canonical_json_v1(state),
         "retained ledger must be the exact committed head")
    need(head.get("machine_id") == original.machine_id
         and integer(head.get("start_date_raw")) == original.origin.start_date_raw
         and integer(head.get("target_date_raw")) == original.origin.target_date_raw
         and integer(head.get("target_days"), 1) == original.origin.target_days
         and integer(head.get("last_settled_cycles")) == original.completed_cycles
         and integer(head.get("last_settled_date_raw")) == original.frame.date_raw,
         "ledger forward may align only already proven settled business")
    validate_continuity_source_identities_v1(captured_sources, mutable_snapshot_ref=snapshot, reader=reader)
    return head


def build_current_saved_continuity_forward_basis_v1(
    forward: CurrentSavedContinuityForwardV1, *, forward_ref: ExactRefV1,
    reader: BasisReaderV1,
) -> CurrentSavedBasisV1:
    need(parse_current_saved_continuity_forward_v1(evidence(reader, forward_ref, 16384),
        expected_machine_id=forward.machine_id) == forward, "exact metadata-forward source")
    original = decode_current_saved_basis_v1(exact_read(reader, forward.original_basis_ref, 65536),
        expected_machine_id=forward.machine_id)
    head = _continuity_forward_head_v1(forward, original, reader=reader)
    return replace(original, observed_at_utc=forward.observed_at_utc,
        refs=replace(original.refs, ledger=forward.ledger_ref, closure=forward_ref),
        progress=replace(original.progress, ledger_cycles=integer(head["last_settled_cycles"]),
                         ledger_date_raw=integer(head["last_settled_date_raw"])))


def validate_current_saved_continuity_forward_basis_v1(
    basis: CurrentSavedBasisV1, *, reader: BasisReaderV1,
) -> CurrentSavedContinuityForwardV1:
    forward = parse_current_saved_continuity_forward_v1(evidence(reader, basis.refs.closure, 16384),
        expected_machine_id=basis.machine_id)
    expected = build_current_saved_continuity_forward_basis_v1(
        forward, forward_ref=basis.refs.closure, reader=reader)
    need(canonical_json_v1(expected.to_wire()) == canonical_json_v1(basis.to_wire()),
         "metadata forward preserves every non-ledger business/unknown/identity field")
    return forward


@dataclass(frozen=True, slots=True)
class CurrentSavedContinuityQualificationV1:
    machine_id: str
    observed_at_utc: str
    basis_ref: ExactRefV1
    forward_ref: ExactRefV1
    original_validation_ref: ExactRefV1
    driver_ref: ExactRefV1
    save_ref: ExactRefV1
    driver_identity_after: FileStatIdentityV1
    save_identity_after: FileStatIdentityV1
    validator_source_ref: ExactRefV1

    def to_wire(self) -> JsonObject:
        return {"schema": CONTINUITY_FORWARD_QUALIFICATION_SCHEMA,
            "machine_id": text(self.machine_id), "observed_at_utc": utc(self.observed_at_utc),
            "basis_ref": self.basis_ref.to_wire(), "forward_ref": self.forward_ref.to_wire(),
            "original_validation_ref": self.original_validation_ref.to_wire(),
            "driver_ref": self.driver_ref.to_wire(), "save_ref": self.save_ref.to_wire(),
            "driver_identity_after": json_object(self.driver_identity_after.to_wire()),
            "save_identity_after": json_object(self.save_identity_after.to_wire()),
            "validator_source_ref": self.validator_source_ref.to_wire(),
            "qualification_scope": "continuity_metadata_only_original_business_qualification_required",
            "driver_body_reads": 0, "save_hash_reads": 0, "new_credit": 0}


def parse_current_saved_continuity_qualification_v1(
    value: object, *, expected_machine_id: str,
) -> CurrentSavedContinuityQualificationV1:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "basis_ref", "forward_ref",
        "original_validation_ref", "driver_ref", "save_ref", "driver_identity_after",
        "save_identity_after", "validator_source_ref", "qualification_scope",
        "driver_body_reads", "save_hash_reads", "new_credit"})
    need(row["schema"] == CONTINUITY_FORWARD_QUALIFICATION_SCHEMA
         and row["machine_id"] == expected_machine_id
         and row["qualification_scope"] == "continuity_metadata_only_original_business_qualification_required",
         "distinct continuity metadata qualification")
    for name in ("driver_body_reads", "save_hash_reads", "new_credit"):
        integer(row[name], 0, 0)
    return CurrentSavedContinuityQualificationV1(text(row["machine_id"]), utc(row["observed_at_utc"]),
        parse_ref(row["basis_ref"]), parse_ref(row["forward_ref"]), parse_ref(row["original_validation_ref"]),
        parse_ref(row["driver_ref"]), parse_ref(row["save_ref"]),
        parse_file_stat_identity_v1(row["driver_identity_after"], schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_after"], schema=STAT_SCHEMA),
        parse_ref(row["validator_source_ref"]))


def build_current_saved_continuity_qualification_v1(
    basis: CurrentSavedBasisV1, *, basis_ref: ExactRefV1, observed_at_utc: str,
    reader: BasisReaderV1,
) -> CurrentSavedContinuityQualificationV1:
    forward = validate_current_saved_continuity_forward_basis_v1(basis, reader=reader)
    need(decode_current_saved_basis_v1(exact_read(reader, basis_ref, 65536),
        expected_machine_id=basis.machine_id) == basis, "exact forwarded basis")
    from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
        parse_basis_qualification_v1, validate_current_saved_cold_inputs_v1,
    )
    previous = parse_basis_qualification_v1(evidence(reader, forward.original_validation_ref, 16384),
        expected_machine_id=basis.machine_id)
    need(previous.basis_ref == forward.original_basis_ref
         and previous.driver_ref == basis.refs.driver and previous.save_ref == basis.refs.save
         and previous.driver_identity_after == basis.driver_identity
         and previous.save_identity_after == basis.save_identity,
         "retain the original business qualification and file identities")
    original = decode_current_saved_basis_v1(exact_read(reader, forward.original_basis_ref, 65536),
        expected_machine_id=basis.machine_id)
    validate_current_saved_cold_inputs_v1(original, basis_ref=forward.original_basis_ref,
        validation_ref=forward.original_validation_ref, reader=reader)
    return CurrentSavedContinuityQualificationV1(basis.machine_id, utc(observed_at_utc), basis_ref,
        basis.refs.closure, forward.original_validation_ref, basis.refs.driver, basis.refs.save,
        basis.driver_identity, basis.save_identity, basis.refs.checkpoint_validator)


READONLY_PREFIX_UNKNOWN_EPOCH_SCHEMA = "xar.current-saved-readonly-prefix-unknown-epoch/v1"
READONLY_PREFIX_UNKNOWN_QUALIFICATION_SCHEMA = "xar.current-saved-readonly-prefix-unknown-basis-qualification/v1"


@dataclass(frozen=True)
class ReadonlyPrefixDriverFlagsV1:
    managed_restore_transaction: None
    rollback_war_failure: None
    succession_expectation: JsonObject|None
    rollback_war_failures: tuple[JsonObject,...]
    session_binding_present: Literal[False]
    def to_wire(self)->JsonObject:
        need(self.managed_restore_transaction is None and self.rollback_war_failure is None
            and not self.rollback_war_failures and self.session_binding_present is False,"no unresolved Driver transaction")
        return {"managed_restore_transaction":None,"rollback_war_failure":None,
            "succession_expectation":self.succession_expectation,"rollback_war_failures":[],
            "session_binding_present":False}

def parse_readonly_prefix_driver_flags_v1(value:object)->ReadonlyPrefixDriverFlagsV1:
    row=record(value,{"managed_restore_transaction","rollback_war_failure","succession_expectation",
        "rollback_war_failures","session_binding_present"})
    need(row["managed_restore_transaction"] is None and row["rollback_war_failure"] is None
        and rows(row["rollback_war_failures"])==[] and row["session_binding_present"] is False,
        "Driver flags preserve no pending transaction")
    expectation=None
    if row["succession_expectation"] is not None:
        from xar_autoplayer.bridge.succession_transition_contract import normalize_succession_expectation_v1
        expectation=json_object(normalize_succession_expectation_v1(row["succession_expectation"]))
        need(canonical_json_v1(expectation)==canonical_json_v1(row["succession_expectation"]),
            "original SDK succession expectation contract")
    return ReadonlyPrefixDriverFlagsV1(None,None,expectation,(),False)


@dataclass(frozen=True)
class ReadonlyPrefixUnknownRefsV1:
    business_basis: ExactRefV1
    prefix: ExactRefV1
    raw_state: ExactRefV1
    raw_governance: ExactRefV1
    unknown_request: ExactRefV1
    unknown_response: ExactRefV1
    unknown_inflight: ExactRefV1
    first_exception: ExactRefV1
    inflight: ExactRefV1
    halt: ExactRefV1
    failed_full_response: ExactRefV1
    request_inventory: ExactRefV1
    driver_review: ExactRefV1
    history_tail: ExactRefV1
    closure_index: ExactRefV1
    launch: ExactRefV1
    sdk_closed: ExactRefV1
    supervisor_closed: ExactRefV1
    game_exit: ExactRefV1
    next: ExactRefV1
    canonical_qualification: ExactRefV1

    def items(self) -> tuple[tuple[str,ExactRefV1],...]:
        return (("business_basis",self.business_basis),("prefix",self.prefix),("raw_state",self.raw_state),
            ("raw_governance",self.raw_governance),("unknown_request",self.unknown_request),
            ("unknown_response",self.unknown_response),("unknown_inflight",self.unknown_inflight),("first_exception",self.first_exception),
            ("inflight",self.inflight),("halt",self.halt),("failed_full_response",self.failed_full_response),
            ("request_inventory",self.request_inventory),("driver_review",self.driver_review),
            ("history_tail",self.history_tail),("closure_index",self.closure_index),("launch",self.launch),
            ("sdk_closed",self.sdk_closed),("supervisor_closed",self.supervisor_closed),
            ("game_exit",self.game_exit),("next",self.next),("canonical_qualification",self.canonical_qualification))
    def to_wire(self) -> JsonObject:
        return {name:ref.to_wire() for name,ref in self.items()}

_PREFIX_REF_NAMES = ("business_basis","prefix","raw_state","raw_governance","unknown_request",
    "unknown_response","unknown_inflight","first_exception","inflight","halt","failed_full_response","request_inventory",
    "driver_review","history_tail","closure_index","launch","sdk_closed","supervisor_closed","game_exit",
    "next","canonical_qualification")

def parse_readonly_prefix_unknown_refs_v1(value:object) -> ReadonlyPrefixUnknownRefsV1:
    row=record(value,set(_PREFIX_REF_NAMES))
    return ReadonlyPrefixUnknownRefsV1(*(parse_ref(row[name]) for name in _PREFIX_REF_NAMES))


@dataclass(frozen=True)
class ReadonlyUnknownSidecarV1:
    previous_snapshot: ExactRefV1
    current_snapshot: ExactRefV1
    live_path: str
    def to_wire(self)->JsonObject:
        text(self.live_path)
        return {"previous_snapshot":self.previous_snapshot.to_wire(),"current_snapshot":self.current_snapshot.to_wire(),
            "live_path":self.live_path,"changed":(self.previous_snapshot.bytes,self.previous_snapshot.sha256)!=(self.current_snapshot.bytes,self.current_snapshot.sha256),"attribution":"UNKNOWN_REQUEST_EFFECT_NOT_INFERRED"}

def parse_readonly_unknown_sidecar_v1(value:object)->ReadonlyUnknownSidecarV1:
    row=record(value,{"previous_snapshot","current_snapshot","live_path","changed","attribution"})
    item=ReadonlyUnknownSidecarV1(parse_ref(row["previous_snapshot"]),parse_ref(row["current_snapshot"]),text(row["live_path"]))
    need(canonical_json_v1(row)==canonical_json_v1(item.to_wire()),"exact sidecar observation, no inferred business result")
    return item

@dataclass(frozen=True)
class ReadonlyPrefixUnknownEpochV1:
    machine_id: str
    observed_at_utc: str
    refs: ReadonlyPrefixUnknownRefsV1
    driver_payload_flags: ReadonlyPrefixDriverFlagsV1
    sidecar_observations: tuple[ReadonlyUnknownSidecarV1,...] = ()
    def to_wire(self) -> JsonObject:
        text(self.machine_id);utc(self.observed_at_utc)
        return {"schema":READONLY_PREFIX_UNKNOWN_EPOCH_SCHEMA,"machine_id":self.machine_id,
            "observed_at_utc":self.observed_at_utc,"status":"CLOSED_READONLY_SETTLED_PREFIX_WITH_UNKNOWN",
            "refs":self.refs.to_wire(),"driver_payload_flags":self.driver_payload_flags.to_wire(),
            "sidecar_observations":[item.to_wire() for item in self.sidecar_observations],
            "new_ordinary_cycle_credit":0,"new_game_day_credit":0,"new_checkpoint_credit":0,
            "unknown_side_effects_inferred":False,"original_unknown_replayed":False,
            "next_cold_requires_original_checkpoint":True}

def parse_readonly_prefix_unknown_epoch_v1(value:object,*,expected_machine_id:str) -> ReadonlyPrefixUnknownEpochV1:
    row=record(value,{"schema","machine_id","observed_at_utc","status","refs","driver_payload_flags",
        "new_ordinary_cycle_credit","new_game_day_credit","new_checkpoint_credit","sidecar_observations",
        "unknown_side_effects_inferred","original_unknown_replayed","next_cold_requires_original_checkpoint"})
    need(row["schema"]==READONLY_PREFIX_UNKNOWN_EPOCH_SCHEMA and row["machine_id"]==expected_machine_id
        and row["status"]=="CLOSED_READONLY_SETTLED_PREFIX_WITH_UNKNOWN"
        and row["unknown_side_effects_inferred"] is False and row["original_unknown_replayed"] is False
        and row["next_cold_requires_original_checkpoint"] is True,"one explicit readonly-prefix/unknown contract")
    for name in ("new_ordinary_cycle_credit","new_game_day_credit","new_checkpoint_credit"):
        need(integer(row[name])==0,"projection adds no credit")
    return ReadonlyPrefixUnknownEpochV1(text(row["machine_id"]),utc(row["observed_at_utc"]),
        parse_readonly_prefix_unknown_refs_v1(row["refs"]),parse_readonly_prefix_driver_flags_v1(row["driver_payload_flags"]),
        tuple(parse_readonly_unknown_sidecar_v1(item) for item in rows(row["sidecar_observations"])))

@dataclass(frozen=True)
class ValidatedReadonlyPrefixUnknownEpochV1:
    epoch: ReadonlyPrefixUnknownEpochV1
    business_basis: CurrentSavedBasisV1
    driver_ref: ExactRefV1
    driver_identity: FileStatIdentityV1
    save_ref: ExactRefV1
    save_identity: FileStatIdentityV1
    history_count: int
    history_rows: tuple[dict[str,object],...]
    old_game: ReadonlyColdClosedGameV1
    sdk_processes: tuple[ReadonlyColdClosedSdkV1,...]
    next_sequence: int
    pipe_name: str
    frame: SavedFrameV1
    completed_cycles: int
    seed: JsonObject
    governance: JsonObject
    progress: ProgressReconciliationV1
    unknown_requests: tuple[UnknownHistoricalRequestV1,...]

@dataclass(frozen=True)
class ReadonlyPrefixProjectionsV1:
    seed: JsonObject
    governance: JsonObject

def _prefix_classifier_v1(reference:ExactRefV1,queue_ref:ExactRefV1,*,reader:BasisReaderV1) -> FunctionType:
    import ast
    source=exact_read(reader,reference,524288)
    tree=ast.parse(source)
    need(all(isinstance(n,(ast.FunctionDef,ast.Assign)) or
        (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))
        for n in tree.body),"original classifier is a definitions/alias-only module")
    original=ast.parse(exact_read(reader,queue_ref,1048576))
    scope:dict[str,object]={"__name__":"_readonly_prefix_classifier","__file__":queue_ref.path,
        "json":json,"hashlib":hashlib,"Path":Path,"re":re,"datetime":datetime,"timezone":timezone}
    functions=[n for n in original.body if isinstance(n,ast.FunctionDef)
        and (n.name.startswith("classify_") or n.name=="frame")]
    constants=[]
    for node in original.body:
        if isinstance(node,ast.Assign) and all(isinstance(t,ast.Name) and t.id.isupper() for t in node.targets):
            try:value=ast.literal_eval(node.value)
            except (ValueError,TypeError):continue
            constants.append(node)
    exec(compile(ast.Module(body=[*constants,*functions],type_ignores=[]),queue_ref.path,"exec"),scope)
    exec(compile(tree,reference.path,"exec"),scope)
    fn=scope.get("classify_auto_result_credit_v1")
    if not isinstance(fn,FunctionType) or fn.__globals__ is not scope:
        raise ValueError("actual original classifier function")
    return fn

@dataclass(frozen=True, slots=True)
class SettledObservationEffectV1:
    selected_step: str
    effect: Literal["native_observation", "formal_ledger_readback"]
    counted_flags: tuple[str, ...]
    protocol_sequence: str | None = None

    def to_wire(self) -> JsonObject:
        return {"selected_step": self.selected_step, "effect": self.effect,
            "counted_flags": list(self.counted_flags), "protocol_sequence": self.protocol_sequence,
            "new_gameplay_action_claimed": False, "new_credit_granted": 0}


def project_current_saved_settled_observation_v1(
    body: object, observation: object, *, frame: SavedFrameV1,
) -> SettledObservationEffectV1:
    """Recognize qualified read APIs, never a general query-name exemption."""
    source = record(body); credit = record(observation)
    step = text(source.get("selected_step"))
    need(credit.get("submitted_pending") is False
         and credit.get("business_success_inferred") is False
         and credit.get("replay_allowed") is False, "original settled observation")
    flags = tuple(key for key in ("typed_nonmaterial_observation", "existing_focus_verified", "primitive_accepted")
                  if credit.get(key) is True)
    need(bool(flags) and all(key not in credit or type(credit[key]) is bool for key in
         ("typed_nonmaterial_observation", "existing_focus_verified", "primitive_accepted")),
         "typed original ordinary-credit flags")
    for key in ("lifestyle_material_verified", "council_material_verified", "construction_start_verified",
                "construction_completion_verified", "crown_material_verified", "existing_typed_material_verified",
                "date_advance_observed"):
        if key in credit:
            need(exact_bool(credit[key]) is False, "material or advancing prefix needs a saved frontier")
    if credit.get("primitive_accepted") is not True:
        need(credit.get("primitive_accepted") is False, "original non-submitting credit")
        return SettledObservationEffectV1(step, "native_observation", flags)
    need(source.get("status") == "executed" and credit.get("selected_step") == step,
         "qualified accepted read source and classifier operation")
    result = record(source.get("result"))
    need(result.get("accepted") is True, "accepted read result required")
    if step == "query-observed-first-heir-marriage-result-v1-private":
        status = result.get("status")
        need(result.get("schema") == "xar.ck3.observed-first-heir-marriage-private-action.v1"
             and integer(result.get("schema_version"), 1, 1) == 1
             and result.get("step") == step and result.get("private_build") is True
             and result.get("advertised") is False and result.get("cold_recovery") is True
             and status in ("marriage", "betrothal", "pending")
             and result.get("material_result") is (status != "pending")
             and integer(result.get("pre_native_revision"), 0, 0) == 0
             and integer(result.get("post_native_revision"), 1) == frame.native_revision,
             "existing bilateral relation cold readback, not marriage submission")
        for key in ("heir_character_id", "candidate_character_id"):
            integer(result.get(key), 1, 2**32-1)
        return SettledObservationEffectV1(step, "formal_ledger_readback", flags)
    if step == "query-army-strengths-v1":
        need(result.get("status") == "available" and bool(rows(result.get("armies"))),
             "typed ordinary Army observation")
        for value in rows(result["armies"]):
            integer(record(value).get("army_id"), 1, 2**32-1)
        return SettledObservationEffectV1(step, "native_observation", flags)
    need(result.get("step") == step and result.get("backend_id") == "native-headless",
         "exact native read operation")
    sequence = str(integer(result.get("query_sequence"), 1, 2**64-1))
    if step == "query-player-mercenary-context-v1":
        need(result.get("status") == "completed" and result.get("read_only") is True
             and integer(result.get("snapshot_revision"), 1) == frame.native_revision
             and integer(result.get("date_raw")) == frame.date_raw
             and bool(record(result.get("player_mercenary_context"))),
             "native mercenary observation, no hire operation")
    elif re.fullmatch(r"query-war-termination-options-[1-9][0-9]*", step):
        war_id = integer(int(step.rsplit("-", 1)[1]), 1, 2**32-1)
        need(result.get("status") == "available"
             and integer(record(result.get("war_termination_options")).get("war_id"), 1) == war_id,
             "war termination options query, no submission")
    elif re.fullmatch(r"query-route-contact-horizon-v1-(0|[1-9][0-9]*)-to-[1-9][0-9]*-h-[1-9][0-9]*(?:-[1-9][0-9]*)+", step):
        from xar_autoplayer.bridge.war_contract import parse_query_route_contact_horizon_step
        parsed: object = parse_query_route_contact_horizon_step(step)
        need(parsed is not None and result.get("status") == "available"
             and integer(result.get("snapshot_revision"), 1) == frame.native_revision
             and bool(record(result.get("route_contact_horizon"))), "typed route preview, no movement or advance")
    else:
        raise ValueError("primitive acceptance is not a qualified read-only operation")
    return SettledObservationEffectV1(step, "native_observation", flags, sequence)


@dataclass(frozen=True, slots=True)
class UnknownOriginalResponseV1:
    sequence: int
    kind: Literal["client_error_without_result", "returned_sdk_error"]
    error_type: str

    def to_wire(self) -> JsonObject:
        return {"sequence": self.sequence, "kind": self.kind, "error_type": self.error_type,
            "ordinary_cycle_credit": 0, "game_day_credit": 0, "replay_allowed": False,
            "actual_gameplay_effects_inferred": False}


def project_current_saved_unknown_response_v1(
    request: object, response: object, *, expected_sequence: object,
) -> UnknownOriginalResponseV1:
    req = record(request); row = record(response); sequence = integer(expected_sequence, 1)
    need(integer(req.get("sequence"), 1) == sequence and req.get("tool") == "ck3_auto_turn"
         and record(req.get("arguments")) == {}
         and canonical_json_v1(row.get("request")) == canonical_json_v1(req), "exact original unknown AUTO")
    if "result" not in row:
        need(type(row.get("client_error")) is str and row.get("replay_allowed") is False,
             "original client error without a returned result")
        return UnknownOriginalResponseV1(sequence, "client_error_without_result", "client_error")
    result = record(row["result"]); content = record(result.get("structured_content"))
    need(("client_error" not in row or row["client_error"] is None)
         and result.get("is_error") is True and result.get("result_type") == "complete",
         "returned tool error remains unknown, never a successful result")
    return UnknownOriginalResponseV1(sequence, "returned_sdk_error", text(content.get("error_type")))


def validate_current_saved_unknown_failure_v1(
    failure: object, control_failure: object, *, outcome: UnknownOriginalResponseV1,
    unknown_request: object, unknown_response: ExactRefV1,
) -> None:
    row = record(failure); control = record(control_failure); request = record(unknown_request)
    full = record(control.get("request"))
    need(full.get("command") == "full_loop" and integer(full.get("sequence"), 1) < outcome.sequence
         and "result" not in control and type(control.get("client_error")) is str
         and control.get("replay_allowed") is False, "failed control never claims a successful batch")
    need(row.get("replay_allowed") is False and row.get("traceback_truncated") is False
         and row.get("locals_captured") is False, "complete original unknown failure evidence")
    identity = record(row.get("request_identity"), {"sequence", "tool", "command"})
    child = {"sequence": integer(request.get("sequence"), 1), "tool": "ck3_auto_turn", "command": None}
    need(integer(child["sequence"], 1) == outcome.sequence, "unknown failure sequence")
    if row.get("stage") == "sdk_call" and canonical_json_v1(identity) == canonical_json_v1(child):
        return
    parent = {"sequence": integer(full["sequence"], 1), "tool": None, "command": "full_loop"}
    need(outcome.kind == "returned_sdk_error" and row.get("stage") == "request_dispatch"
         and canonical_json_v1(identity) == canonical_json_v1(parent)
         and control.get("original_response") == unknown_response.path,
         "original control failure binds the retained child error, not an invented child traceback")


@dataclass(frozen=True, slots=True)
class TaskClosureObservationV1:
    machine_id: str
    transport: Literal["original_cli", "subprocess"]
    process_exit_code: int | None
    task_name: str | None
    observed_at_utc: str | None


def validate_current_saved_closed_task_absence_v1(
    value: object, *, machine_id: str, nonce: str, spec_sha256: str,
) -> TaskClosureObservationV1:
    """An original CLI receipt is distinct from a subprocess transport receipt."""
    row = record(value)
    if "stdout" in row:
        process_exit_code: int | None = integer(row.get("returncode"), 0, 0)
        transport: Literal["original_cli", "subprocess"] = "subprocess"
        original = record(parse_json(text(row["stdout"]).encode()))
    else:
        process_exit_code = None
        transport = "original_cli"
        original = record(value, {"machine_id", "utc", "task_name", "operation", "actual"})
        utc(original["utc"])
        need(original["task_name"] == "XARG2ManagedOwner-"+text(nonce)
             and original["operation"] == "unregister", "original canonical Task unregister operation")
        actual = record(original["actual"])
        integer(actual.get("instances"), 0, 0)
        arguments = text(actual.get("arguments"))
        need(arguments.split().count("--spec-sha") == 1
             and re.search(r"(?:^|\s)--spec-sha "+digest(spec_sha256)+r"(?:\s|$)", arguments) is not None,
             "actual Task action binds the exact original SPEC bytes")
    need(original.get("machine_id") == machine_id and record(original.get("actual")).get("absent_after") is True,
         "actual original Task absence on this machine")
    if "operation" in original:
        need(original["operation"] == "unregister", "original Task operation")
    task_name = text(original["task_name"]) if "task_name" in original else None
    if task_name is not None:
        need(task_name == "XARG2ManagedOwner-"+text(nonce), "original Task nonce")
    observed_at = utc(original["utc"]) if "utc" in original else None
    return TaskClosureObservationV1(text(machine_id), transport, process_exit_code, task_name, observed_at)


def _readonly_prefix_v1(
    epoch:ReadonlyPrefixUnknownEpochV1,old:CurrentSavedBasisV1,game:ReadonlyColdClosedGameV1,
    *,reader:BasisReaderV1,
) -> tuple[SavedFrameV1,int,JsonObject,JsonObject,tuple[UnknownHistoricalRequestV1,...]]:
    r=epoch.refs;prefix=evidence(reader,r.prefix,65536);state=evidence(reader,r.raw_state,262144)
    gov=evidence(reader,r.raw_governance,262144);seed=evidence(reader,old.refs.seed,262144)
    oldgov=evidence(reader,old.refs.governance,262144)
    need(prefix.get("schema")=="xar.readonly-settled-prefix-evidence/v1"
        and prefix.get("machine_id")==epoch.machine_id
        and parse_ref(prefix.get("business_basis"))==r.business_basis,"original business prefix source")
    root=Path(r.launch.path).parent
    bound_ref=parse_ref(prefix.get("cold_bound"));bound=evidence(reader,bound_ref,65536)
    frame=parse_frame(bound.get("opening_frame"));cp=record(seed.get("actual_saved_checkpoint"))
    need(bound.get("machine_id")==epoch.machine_id
        and bound.get("schema")=="xar.c23.normal-checkpoint-cold-bound/v1"
        and integer(bound.get("completed_cycles"))==old.completed_cycles
        and integer(bound.get("T0_date_raw"))==old.origin.start_date_raw
        and canonical_json_v1(bound.get("checkpoint"))==canonical_json_v1(cp)
        and integer(bound.get("new_ordinary_cycle_credit"))==0 and bound.get("AUTO_or_MET_replayed") is False,
        "actual old checkpoint and new cold opening")
    semref=parse_ref(prefix.get("semantic_response"));capref=parse_ref(prefix.get("capability_response"))
    need(semref.path==bound.get("semantic_response")
        and Path(semref.path).resolve()==(root/"p37-responses"/f"{old.next_sequence:04d}-1-result.json").resolve()
        and Path(capref.path).resolve()==(root/"p37-responses"/f"{old.next_sequence+1:04d}-1-result.json").resolve(),
        "original first read-only SEM/CAP slots")
    sem=completed_body(evidence(reader,semref,1048576),"ck3_take_semantic_snapshot_private_v1")
    cap=completed_body(evidence(reader,capref,1048576),"ck3_get_capabilities")
    need(integer(sem.get("date_raw"))==frame.date_raw and sem.get("paused") is True
        and sem.get("map_ready") is True and sem.get("episode_run_id")==frame.episode_run_id
        and integer(sem.get("episode_character_id"),1)==frame.actor_character_id
        and record(cap.get("native_session_control")).get("driver_state_restored") is True
        and cap.get("episode_run_id")==frame.episode_run_id and integer(cap.get("episode_character_id"),1)==frame.actor_character_id,
        "actual cold restore was read back, without a business credit")
    need((frame.date_raw,frame.actor_character_id,frame.episode_run_id)==
        (old.frame.date_raw,old.frame.actor_character_id,old.frame.episode_run_id),"same saved business frame")
    pin_ref=parse_ref(prefix.get("classifier_pin"));pin=evidence(reader,pin_ref,16384)
    cls_ref=parse_ref(prefix.get("classifier_source"))
    need(Path(pin_ref.path).resolve()==(root/"ROOT-P37C23-CLASSIFIER-PIN.json").resolve()
        and Path(cls_ref.path).resolve()==Path(text(pin.get("source"))).resolve()
        and cls_ref.sha256==pin.get("sha256") and pin.get("machine_id")==epoch.machine_id,"actual original classifier pin")
    queue_ref=parse_ref(record(evidence(reader,r.closure_index,65536).get("refs")).get("queue_source"))
    need(Path(queue_ref.path).resolve()==(root/"root_p37c23_sdk_queue.py").resolve(),"original classifier base namespace")
    classify=_prefix_classifier_v1(cls_ref,queue_ref,reader=reader)
    counts={key:integer(value) for key,value in record(seed.get("counts")).items()}
    entries=rows(prefix.get("entries"));need(1<=len(entries)<=30,"bounded verified prefix")
    previous_sequence=old.next_sequence-1;last_metrics=""
    state_gov=json_object(oldgov.get("governance_result_state")) if oldgov.get("governance_result_state") is not None else None
    focus=json_object(oldgov.get("pending_focus")) if oldgov.get("pending_focus") is not None else None
    for offset,value in enumerate(entries,1):
        item=record(value,{"event","auto","metrics","auto_plan","auto_after","metrics_after","ordinary_credit","readonly_save_skip"})
        event_ref=parse_ref(item["event"]);event=evidence(reader,event_ref,32768)
        ar=parse_ref(item["auto"]);mr=parse_ref(item["metrics"])
        auto=original_response_evidence_v1(reader,ar);metrics=original_response_evidence_v1(reader,mr)
        auto_request=record(auto.get("request"));metric_request=record(metrics.get("request"))
        seq=integer(auto_request.get("sequence"),1)
        need(seq>previous_sequence and auto_request.get("tool")=="ck3_auto_turn"
            and record(auto_request.get("arguments"))=={} and metric_request.get("tool")=="root_current_runtime_metrics"
            and record(metric_request.get("arguments"))=={} and integer(metric_request.get("sequence"),1)==seq+1,
            "original AUTO and following METRICS sequence")
        body=completed_body(auto,"ck3_auto_turn");metric_body=completed_body(metrics,"root_current_runtime_metrics")
        need(metric_body.get("paused") is True and metric_body.get("map_ready") is True
            and metric_body.get("actor_alive") is True and integer(metric_body.get("bridge_pid"),1)==game.pid,
            "actual paused same-Game metrics")
        after=parse_frame({key:metric_body[key] for key in ("snapshot_id","revision","native_revision","date_raw","actor_character_id","episode_run_id")})
        need(Path(ar.path).resolve()==(root/"p37-responses"/f"{seq:04d}-1-result.json").resolve()
            and Path(mr.path).resolve()==(root/"p37-responses"/f"{seq+1:04d}-1-result.json").resolve()
            and Path(event_ref.path).name==f"CUMULATIVE-TURN-{old.completed_cycles+offset:06d}.json",
            "one actual cycle source")
        outcome=classify(body,state=state_gov,pending_focus=focus,initial_frame=frame.to_wire(),game_pid=game.pid)
        need(isinstance(outcome,tuple) and len(outcome)==3,"original classifier returns observation/state/focus")
        if not isinstance(outcome,tuple) or len(outcome)!=3:raise ValueError("classifier result")
        observation=json_object(outcome[0]);state_gov=None if outcome[1] is None else json_object(outcome[1])
        focus=None if outcome[2] is None else json_object(outcome[2])
        effect=project_current_saved_settled_observation_v1(body,observation,frame=frame)
        need(canonical_json_v1(event.get("observation"))==canonical_json_v1(observation),
            "original classifier independently confirms the exact settled observation")
        need(parse_frame(event.get("before"))==frame and parse_frame(event.get("after"))==after
            and integer(event.get("global_turn"),1)==old.completed_cycles+offset
            and integer(event.get("auto_sequence"),1)==seq and event.get("stage")=="auto_verified"
            and event.get("auto_response")==ar.path and event.get("after_metrics_response")==mr.path
            and event.get("business_success_inferred") is False and integer(event.get("date_delta_raw"))==0
            and (after.date_raw,after.actor_character_id,after.episode_run_id)==
                (old.frame.date_raw,old.frame.actor_character_id,old.frame.episode_run_id),
            "verified prefix settles no day, actor transition or inferred success")
        plan=evidence(reader,parse_ref(item["auto_plan"]),65536)
        planned=completed_body(plan,"ck3_plan_turn") if record(plan.get("request")).get("tool")=="ck3_plan_turn" else record(record(plan.get("result")).get("structured_content"))
        need(plan.get("source")=="actual GameplayBridgeService.before_submit callback"
            and plan.get("game_pid")==game.pid and record(plan.get("request")).get("parent_sequence")==seq
            and planned.get("selected_step")==body.get("selected_step")==event.get("selected_step"),"actual original before-submit plan")
        for key,ref,tool in (("auto_after",ar,"ck3_auto_turn"),("metrics_after",mr,"root_current_runtime_metrics")):
            marker=evidence(reader,parse_ref(item[key]),16384)
            need(marker.get("response")==ref.path and marker.get("tool")==tool,"actual accepted source postcheck")
        credit=evidence(reader,parse_ref(item["ordinary_credit"]),16384)
        need(credit.get("source_response")==ar.path and canonical_json_v1(credit.get("observation"))==canonical_json_v1(observation),
            "actual original ordinary credit, not a new credit")
        for flag,counter in (("typed_nonmaterial_observation","typed_nonmaterial_observation_turns"),
                             ("existing_focus_verified","existing_focus_verified_turns"),
                             ("primitive_accepted","primitive_accepted_turns")):
            if flag in effect.counted_flags:counts[counter]=counts.get(counter,0)+1
        need(canonical_json_v1(event.get("cumulative_observation_counts"))==canonical_json_v1(counts),"original cumulative counters")
        if item["readonly_save_skip"] is not None:
            skip=evidence(reader,parse_ref(item["readonly_save_skip"]),16384)
            need(skip.get("status")=="unchanged_readonly_evidence_chain"
                and integer(skip.get("global_turn"),1)==old.completed_cycles+offset
                and canonical_json_v1(skip.get("frame"))==canonical_json_v1(after.to_wire())
                and skip.get("new_gameplay_mutations_observed") is False and skip.get("last_actual_checkpoint_retained") is True,
                "actual readonly checkpoint skip, no SAVE")
            counts["checkpoint_readonly_skipped"]=counts.get("checkpoint_readonly_skipped",0)+1
        frame=after;previous_sequence=seq+1;last_metrics=mr.path
    count=old.completed_cycles+len(entries)
    pending=record(state.get("pending_cycle"))
    unknown=integer(pending.get("auto_sequence"),1);request=evidence(reader,r.unknown_request,16384)
    response=evidence(reader,r.unknown_response,16384)
    need(integer(state.get("completed_cycles"))==count and parse_frame(state.get("before"))==frame
        and state.get("before_metrics_response")==last_metrics and canonical_json_v1(state.get("counts"))==canonical_json_v1(counts)
        and canonical_json_v1(state.get("actual_saved_checkpoint"))==canonical_json_v1(cp)
        and canonical_json_v1(state.get("campaign_goal_anchor"))==canonical_json_v1(old.campaign_goal_anchor)
        and integer(state.get("start_date_raw"))==old.origin.start_date_raw
        and state.get("checkpoint_dirty_since_save") is False
        and pending.get("stage")=="auto_unsettled" and integer(pending.get("global_turn"),1)==count+1
        and parse_frame(pending.get("before"))==frame and pending.get("before_metrics_response")==last_metrics
        and unknown==previous_sequence+1,"the exact live state retains the next unknown outside the settled prefix")
    for key in ("pending_checkpoint","terminal","pending_natural_succession","pending_unsafe_route_halt"):
        need(state.get(key) is None,"no other pending branch")
    project_current_saved_unknown_response_v1(request,response,expected_sequence=unknown)
    need(Path(r.unknown_request.path).resolve()==(root/"p37-requests"/f"{unknown:04d}-1-result.json").resolve()
        and Path(r.unknown_response.path).resolve()==(root/"p37-responses"/f"{unknown:04d}-1-result.json").resolve(),
        "exact retained unknown request slot")
    need(integer(gov.get("completed_cycles"))==count
        and canonical_json_v1(gov.get("pending_cycle"))==canonical_json_v1(pending),"raw governance retains pending")
    need(gov.get("schema")=="g2.queue.governance-sidecar/v1","one raw sidecar contract")
    for source_key,key in (("state","governance_result_state"),("pending_focus","pending_focus")):
        need(source_key in gov and key in oldgov,"required raw and original governance fields")
        need(canonical_json_v1(gov[source_key])==canonical_json_v1(state_gov if key=="governance_result_state" else focus),"unknown result never enters governance")
    projected=json_object(state);projected["pending_cycle"]=None
    projected["unknown_before_cold_projection"]={"unknown_sequence":unknown,"raw_state":r.raw_state.to_wire(),
        "original_response":r.unknown_response.to_wire(),"replayed":False,"cycle_credit":0,"day_credit":0}
    projected_gov:JsonObject={"schema":"xar.readonly-prefix-governance-projection/v1","completed_cycles":count,"pending_cycle":None,
        "governance_result_state":state_gov,"pending_focus":focus,"source_epoch":r.raw_governance.to_wire(),
        "new_business_credit":0}
    unknowns=(*old.unknown_requests,UnknownHistoricalRequestV1(unknown,r.raw_state))
    need(len({u.sequence for u in unknowns})==len(unknowns),"unknown lineage unique and retained")
    return frame,count,projected,projected_gov,unknowns

def _native_history_json_v1(value:object,depth:int=0)->JsonValue:
    """Separate exact legacy Native JSON domain; never the cross-JS safe domain."""
    need(depth<=64,"bounded Native JSON depth")
    if value is None or type(value) is bool or type(value) is str:return value
    if type(value) is int:
        need(-(1<<63)<=value<1<<64,"exact Native integer range");return value
    if type(value) is float:
        need(math.isfinite(value),"finite Native scalar");return value
    if isinstance(value,list):
        need(len(value)<=8192,"bounded Native list")
        return [_native_history_json_v1(x,depth+1) for x in value]
    row=record(value)
    return {key:_native_history_json_v1(item,depth+1) for key,item in row.items()}

MAX_CLOSED_HISTORY_DOCUMENT_BYTES_V1 = 131072
MAX_CLOSED_HISTORY_RAW_BYTES_V1 = 2 * 1024 * 1024


def decode_readonly_prefix_history_v1(value:object)->list[dict[str,object]]:
    import base64,zlib
    row=record(value)
    payload=row.get("payload")
    need(type(payload) is str,"exact encoded Native history")
    if not isinstance(payload,str):raise ValueError("history text")
    need(len(payload)<=262144 and len(payload)%4==0,"bounded base64 boundary")
    packed=base64.b64decode(payload,validate=True)
    need(len(packed)<=196608 and base64.b64encode(packed).decode()==payload,"canonical bounded base64")
    decoder=zlib.decompressobj();raw=decoder.decompress(packed,MAX_CLOSED_HISTORY_RAW_BYTES_V1+1)
    need(len(raw)<=MAX_CLOSED_HISTORY_RAW_BYTES_V1 and decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
        "one bounded complete compressed history")
    need(row.get("schema")=="xar.raw-closed-driver-history-opaque/v1" and row.get("encoding")=="zlib+base64"
        and integer(row.get("decoded_bytes"))==len(raw) and row.get("decoded_sha256")==hashlib.sha256(raw).hexdigest(),
        "exact decoded history bytes")
    result=rows(parse_json(raw));need(len(result)==integer(row.get("row_count"),0,8192),"actual history count")
    _native_history_json_v1(result)
    parsed: list[dict[str, object]] = []
    for item in result:
        native = record(item)
        fields = {"index", "command", "ok", "result"}
        if native.get("ok") is False:
            fields.add("error")
            text(native.get("error"))
        parsed.append(record(native, fields))
    return parsed

def _exact_native_json_v1(value:object)->bytes:
    return json.dumps(_native_history_json_v1(value),ensure_ascii=False,sort_keys=True,
        separators=(",",":"),allow_nan=False).encode()


def _validate_settled_prefix_history_v1(
    history: list[dict[str, object]], *, epoch: ReadonlyPrefixUnknownEpochV1,
    frame: SavedFrameV1, reader: BasisReaderV1,
) -> None:
    """Bind native history to original observations; an error suffix earns nothing."""
    prefix = evidence(reader, epoch.refs.prefix, 65536)
    observed: dict[str, list[dict[str, object]]] = {}
    for item in rows(prefix.get("entries")):
        response = original_response_evidence_v1(reader, parse_ref(record(item).get("auto")))
        body = completed_body(response, "ck3_auto_turn")
        if type(body.get("result")) is dict:
            observed.setdefault(text(body.get("selected_step")), []).append(record(body["result"]))
    unknown = evidence(reader, epoch.refs.unknown_response, 16384)
    content: dict[str, object] | None = None
    if "result" in unknown:
        content = record(record(unknown["result"]).get("structured_content"))
    failed = False
    for h in history:
        result = record(h["result"]); command = text(h["command"])
        need(not failed, "the retained unknown failure is the final history row")
        if h["ok"] is False:
            need(content is not None, "a native failure needs its original returned tool error")
            if content is None:
                raise ValueError("original error diagnostics required")
            plan = evidence(reader, parse_ref(prefix.get("unknown_plan")), 65536)
            planned = record(record(plan.get("result")).get("structured_content"))
            request = evidence(reader, epoch.refs.unknown_request, 16384)
            need(plan.get("source") == "actual GameplayBridgeService.before_submit callback"
                 and integer(record(plan.get("request")).get("parent_sequence"), 1)
                 == integer(request.get("sequence"), 1)
                 and integer(plan.get("game_pid"), 1)
                 == integer(evidence(reader, epoch.refs.launch, 16384).get("pid"), 1)
                 and planned.get("selected_step") == command,
                 "native failure belongs to the retained original unknown plan")
            diagnostics = record(content.get("diagnostics"))
            need(any(_exact_native_json_v1(value) == _exact_native_json_v1(result)
                     for value in diagnostics.values()), "complete original native error is preserved exactly")
            error_prefix = text(content.get("error_type"))+": "
            need(text(h.get("error")).startswith(error_prefix), "original native error type")
            if "original_error" in result:
                need(h["error"] == error_prefix+text(result["original_error"]), "original native error message")
            failed = True
            continue
        need(h["ok"] is True, "typed native history outcome")
        if command in {"query-campaign-root-context-v1", "query-war-results-window-v1",
                       "query-war-declared-overview-v1"}:
            need(result.get("step") == command and result.get("accepted") is True
                 and integer(result.get("date_raw")) == frame.date_raw,
                 "original same-date query bookkeeping")
            if command != "query-campaign-root-context-v1":
                need(result.get("operation") == "query" and all(result.get(key) is False
                    for key in ("dispatch_attempted", "dispatch_invoked", "native_handled")),
                    "query bookkeeping is not a window mutation")
            continue
        candidates = observed.get(command, [])
        if any(_exact_native_json_v1(result) == _exact_native_json_v1(value) for value in candidates):
            continue
        need(command == "query-army-strengths-v1", "history needs an exact original settled observation")
        from xar_autoplayer.bridge.army_query_history_store import build_army_query_history_summary, _ARMY_FIELDS
        from xar_autoplayer.bridge.army_strengths_mcp_result import _SUMMARY_ARMY_FIELDS
        need(result.get("history_summary_schema") == "xar.ck3.army-query-history-summary.v1"
             and result.get("accepted") is True and result.get("status") == "available"
             and result.get("backend_id") == "native-headless"
             and result.get("queried_snapshot_id") == frame.snapshot_id
             and integer(result.get("queried_revision"), 1) == frame.revision
             and integer(result.get("queried_native_revision"), 1) == frame.native_revision,
             "original compact Army query summary belongs to the settled frame")
        matched = False
        for value in candidates:
            if (integer(value.get("query_sequence"), 1, 2**64-1)
                != integer(result.get("query_sequence"), 1, 2**64-1)):
                continue
            need(value.get("army_strengths_profile") == result.get("army_strengths_profile")
                 and value.get("army_observed_phase_coverage") == result.get("army_observed_phase_coverage"),
                 "original Army result profile")
            source = record(value.get("source"))
            need(integer(source.get("revision"), 1) == frame.revision
                 and integer(source.get("native_revision"), 1) == frame.native_revision
                 and value.get("result_location") == "compact_mcp_summary", "original MCP Army projection source")
            preserved = exact_bool(result.get("full_result_preserved"))
            reference = record(result.get("raw_result_reference")) if preserved else None
            reason = text(result["unavailable_reason"]) if "unavailable_reason" in result else None
            diagnostic = record(result["history_storage_diagnostic"]) if "history_storage_diagnostic" in result else None
            projected = build_army_query_history_summary({**result, "army_strengths": rows(value.get("armies"))},
                reference, unavailable_reason=reason, diagnostic=diagnostic)
            # The Driver and MCP intentionally retain different lossy projections.
            # Compare their complete shared field set, never invent omitted fields.
            common = set(_ARMY_FIELDS).intersection(_SUMMARY_ARMY_FIELDS)
            left = rows(result.get("armies")); right = rows(projected.get("armies"))
            equivalent = len(left) == len(right)
            for first, second in zip(left, right):
                a = record(first); z = record(second)
                equivalent = equivalent and common <= set(a) and common <= set(z)
                if equivalent:
                    equivalent = _exact_native_json_v1({k:a[k] for k in common}) == _exact_native_json_v1({k:z[k] for k in common})
            if (equivalent and _exact_native_json_v1({k:v for k,v in projected.items() if k != "armies"})
                    == _exact_native_json_v1({k:v for k,v in result.items() if k != "armies"})):
                matched = True
                break
        need(matched, "actual SDK history projection agrees with the original complete Army result")

def _validate_readonly_prefix_unknown_evidence_v1(
    epoch:ReadonlyPrefixUnknownEpochV1,*,reader:BasisReaderV1,trail:tuple[str,...],
)->ValidatedReadonlyPrefixUnknownEpochV1:
    need(parse_readonly_prefix_unknown_epoch_v1(epoch.to_wire(),expected_machine_id=epoch.machine_id)==epoch,"typed epoch")
    r=epoch.refs;old=decode_current_saved_basis_v1(exact_read(reader,r.business_basis,65536),expected_machine_id=epoch.machine_id)
    need(len(trail)<32 and r.business_basis.path not in trail,"bounded acyclic epoch lineage")
    lineage_basis=old
    forward_seen:set[str]=set()
    closure=evidence(reader,lineage_basis.refs.closure,65536)
    while closure.get("schema")==CONTINUITY_FORWARD_SCHEMA:
        need(len(forward_seen)<16 and lineage_basis.refs.closure.path not in forward_seen,
             "bounded acyclic continuity metadata lineage")
        forward_seen.add(lineage_basis.refs.closure.path)
        forward=validate_current_saved_continuity_forward_basis_v1(lineage_basis,reader=reader)
        lineage_basis=decode_current_saved_basis_v1(exact_read(reader,forward.original_basis_ref,65536),
            expected_machine_id=epoch.machine_id)
        closure=evidence(reader,lineage_basis.refs.closure,65536)
    prior:ValidatedCapPostresponseFailureEpochV3|ValidatedReadonlyPrefixUnknownEpochV1
    if closure.get("schema")==CAP_POSTRESPONSE_FAILURE_EPOCH_SCHEMA:
        prior=validate_cap_postresponse_failure_evidence_v3(
            parse_cap_postresponse_failure_epoch_v3(closure,expected_machine_id=epoch.machine_id),reader=reader)
        need(lineage_basis.refs==replace(prior.business_basis.refs,driver=prior.driver_ref,
            driver_close=prior.epoch.refs.driver_review,closure=lineage_basis.refs.closure,next=prior.epoch.refs.next)
            and lineage_basis.origin==prior.business_basis.origin and lineage_basis.frame==prior.business_basis.frame
            and lineage_basis.progress==prior.business_basis.progress and lineage_basis.unknown_requests==prior.business_basis.unknown_requests,
            "historical saved business references remain exact")
    elif closure.get("schema")==READONLY_PREFIX_UNKNOWN_EPOCH_SCHEMA:
        prior=_validate_readonly_prefix_unknown_evidence_v1(
            parse_readonly_prefix_unknown_epoch_v1(closure,expected_machine_id=epoch.machine_id),
            reader=reader,trail=(*trail,r.business_basis.path))
        _check_readonly_prefix_basis_v1(prior,lineage_basis,reader=reader)
    else:raise ValueError("qualified closed business lineage required; no unknown epoch alias")
    need(old.refs.driver==prior.driver_ref and old.driver_identity==prior.driver_identity
        and old.refs.save==prior.save_ref and old.save_identity==prior.save_identity
        and old.next_sequence==prior.next_sequence,"exact validated historical business basis")
    need(tuple(item.previous_snapshot for item in epoch.sidecar_observations)==old.sidecars
        and len({item.live_path.casefold() for item in epoch.sidecar_observations})==len(epoch.sidecar_observations),
        "all historical sidecars have one actual live-slot observation")
    for sidecar in epoch.sidecar_observations:
        parse_readonly_unknown_sidecar_v1(sidecar.to_wire())
        historical=evidence(reader,sidecar.previous_snapshot,262144)
        current=evidence(reader,sidecar.current_snapshot,262144)
        need(("pending" in historical)==("pending" in current),"missing versus nullable sidecar pending preserved")
        if "pending" in current:need(current["pending"] is None,"original sidecar pending must be settled")
    launch=evidence(reader,r.launch,32768);pid=integer(launch.get("pid"),1,2**32-1)
    game=ReadonlyColdClosedGameV1(pid,_closed_filetime_v1(launch.get("creation_filetime")),text(launch.get("creation_date")))
    need(launch.get("machine_id")==epoch.machine_id and launch.get("old_save_loaded") is True
        and launch.get("load_save_name")=="xar_checkpoint" and launch.get("nonwar_only") is False
        and pid!=prior.old_game.pid,"new managed checkpoint Game")
    frame,count,seed,gov,unknowns=_readonly_prefix_v1(epoch,old,game,reader=reader)
    state=evidence(reader,r.raw_state,262144);pending=record(state["pending_cycle"])
    unknown=integer(pending["auto_sequence"],1);request=evidence(reader,r.unknown_request,16384)
    row=evidence(reader,r.unknown_response,16384);flat=evidence(reader,r.unknown_inflight,16384)
    outcome=project_current_saved_unknown_response_v1(request,row,expected_sequence=unknown)
    need(integer(flat.get("sequence"),1)==unknown and flat.get("tool")=="ck3_auto_turn"
        and record(flat.get("arguments"))=={} and flat.get("request_file")==r.unknown_request.path
        and flat.get("replay_allowed") is False,"original unknown INFLIGHT")
    failure=evidence(reader,r.first_exception,16384)
    failed=evidence(reader,r.failed_full_response,16384)
    validate_current_saved_unknown_failure_v1(failure,failed,outcome=outcome,
        unknown_request=request,unknown_response=r.unknown_response)
    halt=evidence(reader,r.halt,16384);nextseq=integer(evidence(reader,r.next,16384).get("next_sequence"),1)
    need(canonical_json_v1(halt.get("original_request"))==canonical_json_v1(request)
        and halt.get("original_response")==r.unknown_response.path and halt.get("replay_allowed") is False
        and halt.get("sdk_kept_alive_for_original_collection") is True
        and halt.get("first_exception_receipt")==r.first_exception.path
        and integer(halt.get("next_sequence"),1)==nextseq==unknown+1,"unknown remains consumed and unreplayed")
    full_request=record(failed.get("request"))
    need(full_request.get("command")=="full_loop" and integer(full_request.get("sequence"),1)<unknown
        and "result" not in failed and failed.get("replay_allowed") is False,"failed FULL is not a successful checkpoint frontier")
    parent=evidence(reader,r.inflight,16384)
    need(canonical_json_v1(parent.get("request"))==canonical_json_v1(full_request)
        and parent.get("control_only") is True and parent.get("original_action_replay_allowed") is False,
        "original FULL control remains inflight; never marked successful")
    inv=evidence(reader,r.request_inventory,32768)
    need(inv.get("machine_id")==epoch.machine_id and inv.get("all_owned_writers_closed") is True
        and integer(inv.get("next_sequence"),1)==nextseq and integer(inv.get("unknown_sequence"),1)==unknown
        and inv.get("original_unknown_replayed") is False,"closed exact request inventory")
    observed=tuple(parse_ref(x) for x in rows(inv.get("request_files")))
    need(len({x.path for x in observed})==len(observed) and r.unknown_request in observed,"unique unknown slot retained")
    requests=[evidence(reader,ref,16384) for ref in observed]
    need(sorted(integer(item.get("sequence"),1) for item in requests)==list(range(old.next_sequence,nextseq)),
        "all original requests form the exact closed sequence interval")
    sdk=evidence(reader,r.sdk_closed,16384);processes=[]
    need(sdk.get("machine_id")==epoch.machine_id and sdk.get("status")=="ACTUAL_BOTH_SDK_EXITS_OBSERVED",
        "actual closed SDK pair")
    for item in rows(sdk.get("processes")):
        p=record(item);role=p.get("role")
        if role=="sdk_queue":kind:Literal["sdk_queue","sdk_application"]="sdk_queue"
        elif role=="sdk_application":kind="sdk_application"
        else:raise ValueError("SDK role")
        code=integer(p.get("exit_code"),0,2**32-1)
        need(p.get("kernel_exit_observed") is True and integer(p.get("wait_result"),0,0)==0
            and "observation_error" in p and p["observation_error"] is None,"actual closed SDK handle")
        processes.append(ReadonlyColdClosedSdkV1(kind,integer(p.get("pid"),1,2**32-1),
            _closed_filetime_v1(p.get("creation_filetime")),text(p.get("executable")),code))
    need(len(processes)==2 and {p.role for p in processes}=={"sdk_queue","sdk_application"}
        and len({p.pid for p in processes})==2 and pid not in {p.pid for p in processes}
        and sdk.get("normal") is all(p.exit_code==0 for p in processes),"exact SDK closure classification")
    supervisor=evidence(reader,r.supervisor_closed,16384);cleanup=record(supervisor.get("owned_cleanup"))
    exitcode,forced,classification=_cap_postresponse_game_exit_v3(r.game_exit,game=game,machine_id=epoch.machine_id,reader=reader)
    need(supervisor.get("machine_id")==epoch.machine_id and supervisor.get("cleanup_classification")==classification
        and canonical_json_v1(sdk_without_launcher_v1(record(supervisor.get("sdk_actual_exit"))))
        ==canonical_json_v1(sdk_without_launcher_v1(sdk))
        and integer(cleanup.get("ck3_pid"),1)==pid and integer(cleanup.get("ck3_exit_code"))==exitcode
        and integer(cleanup.get("job_active_processes_final"),0,0)==0
        and cleanup.get("tree_gone") is True and cleanup.get("cleanup_proven") is True
        and cleanup.get("ok") is True and rows(cleanup.get("contract_errors"))==[],"actual owned Game cleanup")
    index=evidence(reader,r.closure_index,65536)
    need(index.get("schema")=="xar.readonly-prefix-unknown-abort-closure/v1"
        and index.get("status")=="CLOSED_READONLY_SETTLED_PREFIX_WITH_UNKNOWN"
        and index.get("machine_id")==epoch.machine_id and parse_ref(index.get("original_basis_ref"))==r.business_basis
        and index.get("original_whole_wall_origin")==old.origin.original_wall_origin_utc
        and integer(index.get("next_sequence"),1)==nextseq
        and integer(index.get("last_saved_checkpoint_baseline_cycles"))==old.completed_cycles
        and integer(index.get("business_completed_cycles"))==count and integer(index.get("business_date_raw"))==frame.date_raw
        and canonical_json_v1(index.get("pending_unknown_cycle"))==canonical_json_v1(pending)
        and index.get("unknown_side_effects_inferred") is False and index.get("failed_FULL_claimed_successful") is False
        and index.get("original_requests_replayed") is False and index.get("all_owned_Tasks_actual_absent") is True
        and integer(index.get("Game_exit_code"))==exitcode and index.get("Game_forced") is forced
        and integer(index.get("Game_Job_active_final"),0,0)==0,"explicit closed prefix/unknown summary")
    for key in ("new_ordinary_cycle_credit","new_game_day_credit","new_checkpoint_credit","new_game_days"):
        need(integer(index.get(key))==0,"no new projection credit")
    linked=record(index.get("refs"))
    for key,ref in r.items():
        if key not in {"business_basis","prefix","closure_index","unknown_inflight"}:
            need(parse_ref(linked.get(key))==ref,"exact source binding: "+key)
    tasks=record(index.get("tasks"));need(len(tasks)==integer(index.get("owned_Task_count"),1,8),"all owned Tasks")
    for value in tasks.values():
        task=record(value,{"spec","closed","unregistered","child_exit_code"})
        spec=evidence(reader,parse_ref(task["spec"]),16384)
        closed=evidence(reader,parse_ref(task["closed"]),16384)
        unreg=evidence(reader,parse_ref(task["unregistered"]),16384)
        validate_current_saved_closed_task_absence_v1(unreg,machine_id=epoch.machine_id,
            nonce=text(spec.get("nonce")),spec_sha256=parse_ref(task["spec"]).sha256)
        need(spec.get("machine_id")==epoch.machine_id and closed.get("machine_id")==epoch.machine_id
            and closed.get("nonce")==spec.get("nonce") and integer(closed.get("child_exit_code"))==integer(task["child_exit_code"])
            ,"actual closed and absent owned Task")
    for key in ("screen_release","recording_shutdown","independent_recording_closed","sdk_pair"):
        exact_read(reader,parse_ref(linked.get(key)),262144)
    review=evidence(reader,r.driver_review,16384);driver=record(review.get("Driver"));saved=record(review.get("SAVE"))
    dr=parse_ref(driver.get("ref"));sr=parse_ref(saved.get("ref"))
    di=parse_file_stat_identity_v1(driver.get("identity"),schema=STAT_SCHEMA)
    si=parse_file_stat_identity_v1(saved.get("identity"),schema=STAT_SCHEMA)
    cp=record(completed_body(evidence(reader,old.refs.save_response),"ck3_save_checkpoint")["checkpoint"])
    identity=record(driver.get("recorded_identity"));history=decode_readonly_prefix_history_v1(
        evidence(reader,r.history_tail,MAX_CLOSED_HISTORY_DOCUMENT_BYTES_V1))
    need(review.get("schema")=="xar.readonly-prefix-unknown-driver-save-review/v1"
        and review.get("status")=="CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_WITH_UNKNOWN_REQUEST"
        and review.get("machine_id")==epoch.machine_id and parse_ref(review.get("post_checkpoint_history_opaque"))==r.history_tail
        and sr==old.refs.save and si==old.save_identity and dr.path==old.refs.driver.path and di.bytes==dr.bytes
        and integer(driver.get("format_version"),2,2)==2 and canonical_json_v1(driver.get("last_checkpoint"))==canonical_json_v1(cp)
        and integer(identity.get("bridge_pid"),1)==pid and integer(identity.get("episode_character_id"),1)==old.frame.actor_character_id
        and identity.get("episode_run_id")==old.frame.episode_run_id
        and driver.get("session_binding_present") is False,"actual new Driver and exact same saved checkpoint")
    expected_flags=epoch.driver_payload_flags.to_wire()
    actual_flags=record(driver.get("payload_flags"));actual_flags["session_binding_present"]=driver.get("session_binding_present")
    need(canonical_json_v1(actual_flags)==canonical_json_v1(expected_flags),"all actual nullable Driver flags retained")
    expectation=epoch.driver_payload_flags.succession_expectation
    if expectation is not None:
        eb=record(expectation.get("binding"))
        need(integer(eb.get("episode_character_id"),1)==frame.actor_character_id and eb.get("episode_run_id")==frame.episode_run_id
            and integer(eb.get("date_raw"))==frame.date_raw,"current expectation observation belongs to the actual saved episode")
    n=integer(driver.get("command_history_count"),1);cpindex=integer(cp.get("history_index"),1)
    # The unchanged native cold-restorer retains proven restore rows and drops
    # later query bookkeeping, then renumbers the retained rows after the CP.
    retained=[record(item) for item in prior.history_rows if item.get("command")=="restore-checkpoint"]
    for position,item in enumerate(retained,cpindex+1):item["index"]=position
    need(len(history)==n-cpindex and len(history)>len(retained)
        and _exact_native_json_v1(history[:len(retained)])==_exact_native_json_v1(retained),
        "the original cold restore lineage projection remains exact")
    tail=history[len(retained):]
    _cap_restore_row_v2(tail[0],checkpoint=json_object(cp),index=cpindex+len(retained)+1,
        previous_pid=prior.old_game.pid,current_pid=pid)
    for offset,h in enumerate(history,cpindex+1):
        need(integer(h["index"],1)==offset and type(h["ok"]) is bool,"contiguous exact history records")
    _validate_settled_prefix_history_v1(tail[1:], epoch=epoch, frame=frame, reader=reader)
    opaque=evidence(reader,r.history_tail,MAX_CLOSED_HISTORY_DOCUMENT_BYTES_V1)
    need(opaque.get("machine_id")==epoch.machine_id and parse_ref(opaque.get("Driver_ref"))==dr
        and parse_file_stat_identity_v1(opaque.get("Driver_identity"),schema=STAT_SCHEMA)==di
        and integer(opaque.get("checkpoint_history_index"),1)==cpindex
        and integer(opaque.get("command_history_count"),1)==n,"opaque history belongs to this exact Driver")
    raw=evidence(reader,parse_ref(review.get("raw_observation")),32768)
    need(raw.get("schema")=="xar.raw-closed-driver-observation/v2" and raw.get("machine_id")==epoch.machine_id
        and parse_ref(raw.get("Driver_ref"))==dr
        and parse_file_stat_identity_v1(raw.get("Driver_identity"),schema=STAT_SCHEMA)==di
        and parse_file_stat_identity_v1(raw.get("SAVE_identity"),schema=STAT_SCHEMA)==si
        and integer(raw.get("command_history_count"))==n
        and canonical_json_v1(raw.get("last_checkpoint"))==canonical_json_v1(cp)
        and canonical_json_v1(raw.get("recorded_identity"))==canonical_json_v1(identity)
        and canonical_json_v1(raw.get("campaign_goal"))==canonical_json_v1(old.campaign_goal_anchor)
        and canonical_json_v1(raw.get("driver_payload_flags"))==canonical_json_v1(driver.get("payload_flags"))
        and parse_ref(raw.get("post_checkpoint_history_opaque"))==r.history_tail
        and raw.get("session_binding_present") is False and raw.get("session_binding_value") is None
        and "session_binding" not in rows(raw.get("payload_top_keys")),"original single-read Driver witness")
    proof=evidence(reader,r.canonical_qualification,16384)
    need(proof.get("schema")=="xar.closed-readonly-prefix-save-identity-reuse/v1"
        and proof.get("machine_id")==epoch.machine_id and proof.get("validation_mode")=="previous_canonical_save_identity_reuse"
        and proof.get("current_canonical_API_executed") is False
        and parse_ref(proof.get("previous_canonical_qualification"))==prior.epoch.refs.canonical_qualification
        and parse_ref(proof.get("driver_review"))==r.driver_review and parse_ref(proof.get("history_tail"))==r.history_tail
        and parse_file_stat_identity_v1(proof.get("Driver_identity"),schema=STAT_SCHEMA)==di
        and parse_file_stat_identity_v1(proof.get("SAVE_identity"),schema=STAT_SCHEMA)==si
        and canonical_json_v1(proof.get("checkpoint"))==canonical_json_v1(old.checkpoint)
        and parse_ref(proof.get("validator"))==old.refs.checkpoint_validator
        and proof.get("SAVE_hash_reused_by_exact_identity") is True and proof.get("original_checkpoint_unchanged") is True
        and integer(proof.get("Driver_full_read_count"),1)==integer(review.get("raw_Driver_body_read_count"),1)
        and integer(proof.get("Driver_full_read_bytes"))==integer(review.get("Driver_body_bytes_read"))==dr.bytes*integer(proof.get("Driver_full_read_count"),1)
        and integer(proof.get("SAVE_full_hash_count"),0,0)==0 and integer(review.get("SAVE_full_hash_count"),0,0)==0,
        "previous canonical qualification reused honestly; no new SAVE hash or canonical call")
    progress=replace(old.progress,settled_cycles=count,settled_date_raw=frame.date_raw)
    # History is deliberately opaque exact Native JSON; it is never counted as a result.
    return ValidatedReadonlyPrefixUnknownEpochV1(epoch,old,dr,di,sr,si,n,tuple(history),game,
        tuple(sorted(processes,key=lambda p:p.role)),nextseq,text(identity.get("pipe_name")),
        frame,count,seed,gov,progress,unknowns)

def validate_readonly_prefix_unknown_epoch_v1(
    epoch:ReadonlyPrefixUnknownEpochV1,*,reader:BasisReaderV1,
)->ValidatedReadonlyPrefixUnknownEpochV1:
    checked=validate_readonly_prefix_unknown_evidence_v1(epoch,reader=reader)
    need(reader.stat(checked.driver_ref.path)==checked.driver_identity
        and reader.stat(checked.save_ref.path)==checked.save_identity,"actual closed Driver/SAVE identities")
    return checked

def build_readonly_prefix_unknown_projections_v1(
    validated:ValidatedReadonlyPrefixUnknownEpochV1,*,reader:BasisReaderV1,
)->ReadonlyPrefixProjectionsV1:
    need(validate_readonly_prefix_unknown_evidence_v1(validated.epoch,reader=reader)==validated,"authentic prefix evidence")
    return ReadonlyPrefixProjectionsV1(json_object(validated.seed),json_object(validated.governance))

def build_readonly_prefix_unknown_basis_v1(
    validated:ValidatedReadonlyPrefixUnknownEpochV1,*,epoch_ref:ExactRefV1,seed_ref:ExactRefV1,
    governance_ref:ExactRefV1,observed_at_utc:str,sidecars:tuple[ExactRefV1,...],reader:BasisReaderV1,
)->CurrentSavedBasisV1:
    need(validate_readonly_prefix_unknown_epoch_v1(validated.epoch,reader=reader)==validated,"authentic closed prefix")
    return _readonly_prefix_basis_value_v1(validated,epoch_ref=epoch_ref,seed_ref=seed_ref,
        governance_ref=governance_ref,observed_at_utc=observed_at_utc,sidecars=sidecars,reader=reader)

def _readonly_prefix_basis_value_v1(
    validated:ValidatedReadonlyPrefixUnknownEpochV1,*,epoch_ref:ExactRefV1,seed_ref:ExactRefV1,
    governance_ref:ExactRefV1,observed_at_utc:str,sidecars:tuple[ExactRefV1,...],reader:BasisReaderV1,
)->CurrentSavedBasisV1:
    need(parse_readonly_prefix_unknown_epoch_v1(parse_json(exact_read(reader,epoch_ref,65536)),
        expected_machine_id=validated.epoch.machine_id)==validated.epoch,"exact generic epoch source")
    need(canonical_json_v1(evidence(reader,seed_ref,262144))==canonical_json_v1(validated.seed)
        and canonical_json_v1(evidence(reader,governance_ref,262144))==canonical_json_v1(validated.governance),
        "only exact typed projected seed/governance may be consumed")
    old=validated.business_basis;r=validated.epoch.refs
    need(sidecars==tuple(item.current_snapshot for item in validated.epoch.sidecar_observations),"current sidecars are provenance, never inferred business")
    refs=replace(old.refs,settled_state=r.raw_state,seed=seed_ref,governance=governance_ref,
        driver=validated.driver_ref,driver_close=r.driver_review,closure=epoch_ref,next=r.next)
    return CurrentSavedBasisV1(old.machine_id,utc(observed_at_utc),old.origin,validated.frame,
        validated.completed_cycles,json_object(old.checkpoint),json_object(old.campaign_goal_anchor),refs,
        validated.driver_identity,validated.save_identity,validated.next_sequence,validated.progress,validated.unknown_requests,sidecars)

def validate_readonly_prefix_unknown_evidence_v1(
    epoch:ReadonlyPrefixUnknownEpochV1,*,reader:BasisReaderV1,
)->ValidatedReadonlyPrefixUnknownEpochV1:
    return _validate_readonly_prefix_unknown_evidence_v1(epoch,reader=reader,trail=())

def _check_readonly_prefix_basis_v1(
    validated:ValidatedReadonlyPrefixUnknownEpochV1,basis:CurrentSavedBasisV1,*,reader:BasisReaderV1,
)->None:
    expected=_readonly_prefix_basis_value_v1(validated,epoch_ref=basis.refs.closure,
        seed_ref=basis.refs.seed,governance_ref=basis.refs.governance,
        observed_at_utc=basis.observed_at_utc,sidecars=basis.sidecars,reader=reader)
    need(canonical_json_v1(expected.to_wire())==canonical_json_v1(basis.to_wire()),
        "complete original basis lineage and exact verified prefix projection")

def validate_readonly_prefix_unknown_basis_v1(
    basis:CurrentSavedBasisV1,*,reader:BasisReaderV1,
)->ValidatedReadonlyPrefixUnknownEpochV1:
    epoch=parse_readonly_prefix_unknown_epoch_v1(evidence(reader,basis.refs.closure,65536),
        expected_machine_id=basis.machine_id)
    checked=validate_readonly_prefix_unknown_evidence_v1(epoch,reader=reader)
    _check_readonly_prefix_basis_v1(checked,basis,reader=reader)
    return checked

@dataclass(frozen=True)
class ReadonlyPrefixUnknownQualificationV1:
    machine_id: str
    observed_at_utc: str
    basis_ref: ExactRefV1
    epoch_ref: ExactRefV1
    canonical_qualification_ref: ExactRefV1
    driver_ref: ExactRefV1
    save_ref: ExactRefV1
    driver_identity_after: FileStatIdentityV1
    save_identity_after: FileStatIdentityV1
    validator_source_ref: ExactRefV1
    driver_history_rows: int
    root_driver_body_reads: int
    def to_wire(self)->JsonObject:
        text(self.machine_id);utc(self.observed_at_utc)
        integer(self.driver_history_rows,1);integer(self.root_driver_body_reads,1)
        return {"schema":READONLY_PREFIX_UNKNOWN_QUALIFICATION_SCHEMA,
            "machine_id":self.machine_id,"observed_at_utc":self.observed_at_utc,
            "basis_ref":self.basis_ref.to_wire(),"epoch_ref":self.epoch_ref.to_wire(),
            "canonical_qualification_ref":self.canonical_qualification_ref.to_wire(),
            "driver_ref":self.driver_ref.to_wire(),"save_ref":self.save_ref.to_wire(),
            "driver_identity_after":json_object(self.driver_identity_after.to_wire()),
            "save_identity_after":json_object(self.save_identity_after.to_wire()),
            "validator_source_ref":self.validator_source_ref.to_wire(),
            "driver_history_rows":self.driver_history_rows,"root_driver_body_reads":self.root_driver_body_reads,
            "driver_body_reads":0,"save_hash_reads":0,"canonical_checkpoint_validator_calls":0,
            "read_count_scope":"metadata_only_previous_canonical_save_identity_reuse",
            "unknown_request_qualified":False,"new_credit":0}

def parse_readonly_prefix_unknown_qualification_v1(value:object,*,expected_machine_id:str)->ReadonlyPrefixUnknownQualificationV1:
    row=record(value,{"schema","machine_id","observed_at_utc","basis_ref","epoch_ref",
        "canonical_qualification_ref","driver_ref","save_ref","driver_identity_after","save_identity_after",
        "validator_source_ref","driver_history_rows","root_driver_body_reads","driver_body_reads",
        "save_hash_reads","canonical_checkpoint_validator_calls","read_count_scope","unknown_request_qualified","new_credit"})
    result=ReadonlyPrefixUnknownQualificationV1(text(row["machine_id"]),utc(row["observed_at_utc"]),
        parse_ref(row["basis_ref"]),parse_ref(row["epoch_ref"]),parse_ref(row["canonical_qualification_ref"]),
        parse_ref(row["driver_ref"]),parse_ref(row["save_ref"]),
        parse_file_stat_identity_v1(row["driver_identity_after"],schema=STAT_SCHEMA),
        parse_file_stat_identity_v1(row["save_identity_after"],schema=STAT_SCHEMA),
        parse_ref(row["validator_source_ref"]),integer(row["driver_history_rows"],1),
        integer(row["root_driver_body_reads"],1))
    need(result.machine_id==expected_machine_id and canonical_json_v1(result.to_wire())==canonical_json_v1(row),
        "one exact prefix/unknown metadata qualification; zero new credit and body reads")
    return result

def build_readonly_prefix_unknown_qualification_v1(
    validated:ValidatedReadonlyPrefixUnknownEpochV1,basis:CurrentSavedBasisV1,*,
    basis_ref:ExactRefV1,observed_at_utc:str,reader:BasisReaderV1,
)->ReadonlyPrefixUnknownQualificationV1:
    expected=build_readonly_prefix_unknown_basis_v1(validated,epoch_ref=basis.refs.closure,
        seed_ref=basis.refs.seed,governance_ref=basis.refs.governance,
        observed_at_utc=basis.observed_at_utc,sidecars=basis.sidecars,reader=reader)
    need(canonical_json_v1(expected.to_wire())==canonical_json_v1(basis.to_wire())
        and canonical_json_v1(parse_json(exact_read(reader,basis_ref,65536)))==canonical_json_v1(basis.to_wire()),
        "exact projected basis with no unknown result credit")
    proof=evidence(reader,validated.epoch.refs.canonical_qualification,16384)
    return ReadonlyPrefixUnknownQualificationV1(basis.machine_id,utc(observed_at_utc),basis_ref,
        basis.refs.closure,validated.epoch.refs.canonical_qualification,basis.refs.driver,basis.refs.save,
        basis.driver_identity,basis.save_identity,basis.refs.checkpoint_validator,validated.history_count,
        integer(proof["Driver_full_read_count"],1))
