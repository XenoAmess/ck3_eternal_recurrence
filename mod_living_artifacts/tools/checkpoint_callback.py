"""Closed Root readback callback; only real retained checkpoint files qualify.

The public client owns the actual Save command. Root runs the already acquired
official melter under the common storage policy and returns pinned evidence.
No game launch/control transport or current native variable getter is created.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias, TypedDict

from acceptance_contract import Frame, Object, Pin, decimal_id, field, integer, mapping, pin, read, require, text
from checkpoint_artifacts import SavedArtifact, SavedInputs, inspect_inputs
from living_artifacts_model import FEEDING_XP, Rarity


class ReadbackRequestBody(TypedDict):
    schema: Literal["living-artifacts-checkpoint-readback-request-v1"]
    run_id: str
    machine_id: str
    pid: int
    connection_generation: str
    actor_character_id: int
    date_raw: int
    actual_source_save: Pin
    expected_target_id: str | None
    required_response_schema: Literal["living-artifacts-checkpoint-readback-v1"]
    required_unknown_token_policy: Literal["error"]
    original_native_frame_record: Pin
    observation_number: int
    storage_policy: Literal["docs/storage-retention-policy.json"]
    business_pass: Literal[False]


class RootReadbackRequest(ReadbackRequestBody):
    original_hold_deadline: float
    reserve_seconds: int
    operator_reviewer: str


class CompletedReadbackResponse(TypedDict):
    schema: Literal["living-artifacts-checkpoint-readback-v1"]
    schema_version: Literal[1]
    status: Literal["completed"]
    run_id: str
    machine_id: str
    reviewer: str
    pid: int
    connection_generation: str
    actor_character_id: int
    date_raw: int
    source_save: Pin
    melted_save: Pin
    melter: Pin
    command: Pin
    process_receipt: Pin


class BlockedReadbackResponse(TypedDict):
    schema: Literal["living-artifacts-checkpoint-readback-v1"]
    schema_version: Literal[1]
    status: Literal["blocked"]
    run_id: str
    machine_id: str
    reviewer: str
    pid: int
    connection_generation: str
    actor_character_id: int
    date_raw: int
    reason: str
    evidence: list[Pin]


ReadbackResponse: TypeAlias = CompletedReadbackResponse | BlockedReadbackResponse


class FileIdentity(TypedDict):
    device_id_decimal: str
    file_id_decimal: str
    mtime_ns_decimal: str
    size_bytes: int


class MeltProcessReceipt(TypedDict):
    schema: Literal["living-artifacts-checkpoint-melt-process-v2"]
    machine_id: str
    run_id: str
    exit_code: int | None
    status: Literal["exited", "timeout", "output_limit", "launch_failed"]
    failure: str | None
    process_pid: int | None
    raw: Pin
    melted: Pin | None
    melter: Pin
    command: Pin
    stdout: Pin
    stderr: Pin
    request: Pin
    spec: Pin
    storage_check: Pin
    source_file_identity: FileIdentity
    started_at_utc: str
    finished_at_utc: str
    game_commands_sent: Literal[False]


def checked_pin(value: object, label: str, *, allow_empty: bool = False) -> Pin:
    row = mapping(value, label)
    require(set(row) == {"path", "bytes", "sha256"}, "Exact file pin required: " + label)
    path = Path(text(row["path"], label + " path")).resolve()
    integer(row["bytes"], label + " bytes", 0 if allow_empty else 1)
    actual = pin(path)
    require(actual == row, "Retained readback file changed: " + label)
    return actual


@dataclass(frozen=True)
class VerifiedCheckpoint:
    """Verified file/provenance boundary; no product-state or native NPC credit."""
    source_save: Pin
    melted_save: Pin
    evidence: tuple[Pin, ...]
    log_streams: tuple[Pin, Pin]


def verify_checkpoint(value: object, *, run_id: str, machine_id: str, reviewer: str,
                      frame: Frame, source_save: Pin) -> VerifiedCheckpoint:
    row = mapping(value, "Root checkpoint readback")
    status = field(row, "status")
    expected = BlockedReadbackResponse.__required_keys__ if status == "blocked" else CompletedReadbackResponse.__required_keys__
    require(set(row) == set(expected) and row["schema"] == "living-artifacts-checkpoint-readback-v1" and
            integer(row["schema_version"], "readback schema", 1, 1) == 1 and status in ("completed", "blocked"), "Closed checkpoint readback branch required")
    require(row["run_id"] == run_id and row["machine_id"] == machine_id and row["reviewer"] == reviewer and
            integer(row["pid"], "readback PID", 1) == frame.pid and
            decimal_id(row["connection_generation"], "readback generation") == frame.generation_decimal and
            integer(row["actor_character_id"], "readback actor", 1, 2**32 - 2) == frame.player_id and
            integer(row["date_raw"], "readback date") == frame.date_raw, "Checkpoint readback crossed actual scene identity/date")
    if status == "blocked":
        from acceptance_contract import array
        for reference in array(row["evidence"], "blocked readback evidence"):
            checked_pin(reference, "blocked readback evidence", allow_empty=True)
        raise ValueError("Root checkpoint readback BLOCKED: " + text(row["reason"], "specific actual readback blocker"))
    raw = checked_pin(row["source_save"], "retained original save")
    require(raw["bytes"] == source_save["bytes"] and raw["sha256"] == source_save["sha256"], "Root readback is from another actual MCP checkpoint")
    melted = checked_pin(row["melted_save"], "melted save")
    melter = checked_pin(row["melter"], "official melter")
    command = checked_pin(row["command"], "original melt argv")
    process = checked_pin(row["process_receipt"], "original melt process receipt")
    argv_value = read(Path(command["path"]))
    require(set(argv_value) == {"argv"}, "Melt command receipt must retain the exact argv")
    argv = field(argv_value, "argv")
    require(argv == [melter["path"], "melt", raw["path"], "--format", "ck3", "--unknown-key", "error", "-o", melted["path"]],
            "Melt must use the pinned input and strict unknown-token policy")
    receipt = read(Path(process["path"]))
    require(set(receipt) == set(MeltProcessReceipt.__required_keys__) and
            receipt["schema"] == "living-artifacts-checkpoint-melt-process-v2" and receipt["machine_id"] == machine_id and
            receipt["run_id"] == run_id and integer(receipt["exit_code"], "actual melt exit", 0, 0) == 0 and
            receipt["status"] == "exited" and receipt["failure"] is None and receipt["game_commands_sent"] is False and
            receipt["raw"] == raw and receipt["melted"] == melted and receipt["melter"] == melter and receipt["command"] == command,
            "Original successful melt receipt differs from its retained inputs")
    integer(receipt["process_pid"], "actual melter process PID", 1, 2**32 - 1)
    text(receipt["started_at_utc"], "melt start time")
    text(receipt["finished_at_utc"], "melt finish time")
    more: list[Pin] = []
    for name in ("stdout", "stderr", "request", "spec", "storage_check"):
        more.append(checked_pin(receipt[name], "retained process " + name, allow_empty=name in ("stdout", "stderr")))
    original_request = read(Path(more[2]["path"]))
    require(original_request.get("run_id") == run_id and original_request.get("machine_id") == machine_id and
            original_request.get("operator_reviewer") == reviewer and integer(field(original_request, "pid"), "request PID", 1) == frame.pid and
            integer(field(original_request, "actor_character_id"), "request actor", 1) == frame.player_id and
            integer(field(original_request, "date_raw"), "request date") == frame.date_raw and
            field(original_request, "connection_generation") == frame.generation_decimal and field(original_request, "actual_source_save") == source_save,
            "Retained original Root request differs from this actual observation")
    identity = mapping(receipt["source_file_identity"], "source file identity")
    require(set(identity) == set(FileIdentity.__required_keys__) and integer(identity["size_bytes"], "original source bytes", 1) == raw["bytes"], "Original source identity is incomplete")
    for name in ("device_id_decimal", "file_id_decimal", "mtime_ns_decimal"):
        decimal_id(identity[name], name, allow_zero=True)
    return VerifiedCheckpoint(raw, melted, (raw, melted, melter, command, process, *more), (more[0], more[1]))


def verify_readback(value: object, *, run_id: str, machine_id: str, reviewer: str, frame: Frame,
                    source_save: Pin, expected_material_rarities: tuple[Rarity, ...] = tuple(FEEDING_XP)) -> tuple[SavedInputs, tuple[Pin, ...]]:
    verified = verify_checkpoint(value, run_id=run_id, machine_id=machine_id, reviewer=reviewer, frame=frame, source_save=source_save)
    result = inspect_inputs(Path(verified.melted_save["path"]), player_id=frame.player_id, expected_material_rarities=expected_material_rarities)
    return result, verified.evidence


@dataclass(frozen=True)
class CheckpointSample:
    artifact_id: str
    owner_id: str
    date_literal: str
    equipped: bool
    level: int
    xp: int
    pending: int
    growth_sequence: int
    last_month: int
    resonance: int
    durability_decimal: str

    @property
    def month(self) -> int:
        year, month, _ = (int(piece) for piece in self.date_literal.split("."))
        return year * 12 + month

    @classmethod
    def from_saved(cls, item: SavedArtifact, inputs: SavedInputs, *, native_equipped: bool) -> CheckpointSample:
        values: list[int] = []
        for name in ("xalw_level", "xalw_xp_in_level", "xalw_pending_xp", "xalw_growth_sequence", "xalw_last_settled_month", "xalw_resonance"):
            require(name in item.variables, "Required actual saved numeric variable is missing: " + name)
            values.append(item.variables[name].integer_value(name))
        level, xp, pending, growth, month, resonance = values
        require(level >= 1 and 0 <= xp < 100 * level and pending == 0 and growth >= 0 and 0 <= resonance <= 100,
                "Actual saved post-settlement state violates numeric invariants")
        return cls(item.artifact_id, item.owner_id, inputs.date_literal, native_equipped,
                   level, xp, pending, growth, month, resonance, item.durability_decimal)

    def to_json(self) -> Object:
        return {"authority": "actual-checkpoint-with-independent-native-owner-and-equipment", "artifact_id": self.artifact_id,
                "owner_id": self.owner_id, "saved_date": self.date_literal, "month": self.month, "equipped": self.equipped,
                "level": self.level, "xp": self.xp, "pending": self.pending, "growth_sequence": self.growth_sequence,
                "last_month": self.last_month, "resonance": self.resonance, "durability_decimal": self.durability_decimal,
                "current_native_artifact_variable_query": False}
