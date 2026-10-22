"""First bounded FULL must retain a verified checkpoint before its review hold.

Reservations are explicit operator admissions, not measured media headroom.
The original Queue owns every native call and its existing check_after guards.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Callable, Literal, Protocol, runtime_checkable

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, integer, json_object, need, parse_ref, record, text, utc,
)

POLICY_SCHEMA = "xar.current-saved-first-full-checkpoint-policy/v1"
RECEIPT_SCHEMA = "xar.current-saved-first-full-checkpoint-receipt/v1"


@dataclass(frozen=True, slots=True)
class FirstFullCheckpointPolicyV1:
    machine_id: str
    first_control_sequence: int
    baseline_completed_cycles: int
    review_at_utc: str
    budget_ref: ExactRefV1
    reserved_finalize_seconds: int
    reserved_finalize_bytes: int

    def __post_init__(self) -> None:
        text(self.machine_id); integer(self.first_control_sequence, 1)
        integer(self.baseline_completed_cycles, 0); utc(self.review_at_utc)
        integer(self.reserved_finalize_seconds, 1, 86400)
        integer(self.reserved_finalize_bytes, 1, (1 << 53) - 1)

    def to_wire(self) -> JsonObject:
        return {"schema": POLICY_SCHEMA, "machine_id": self.machine_id,
            "first_control_sequence": self.first_control_sequence,
            "baseline_completed_cycles": self.baseline_completed_cycles,
            "review_at_utc": self.review_at_utc, "budget_ref": self.budget_ref.to_wire(),
            "reserved_finalize_seconds": self.reserved_finalize_seconds,
            "reserved_finalize_bytes": self.reserved_finalize_bytes,
            "reservation_mode": "explicit_operator_admitted", "checkpoint_before_hold": True}


def parse_first_full_checkpoint_policy_v1(value: object) -> FirstFullCheckpointPolicyV1:
    row = record(value, {"schema", "machine_id", "first_control_sequence",
        "baseline_completed_cycles", "review_at_utc", "budget_ref",
        "reserved_finalize_seconds", "reserved_finalize_bytes", "reservation_mode",
        "checkpoint_before_hold"})
    need(row["schema"] == POLICY_SCHEMA and row["checkpoint_before_hold"] is True
         and row["reservation_mode"] == "explicit_operator_admitted", "first FULL checkpoint policy")
    return FirstFullCheckpointPolicyV1(text(row["machine_id"]),
        integer(row["first_control_sequence"], 1), integer(row["baseline_completed_cycles"], 0),
        utc(row["review_at_utc"]), parse_ref(row["budget_ref"]),
        integer(row["reserved_finalize_seconds"], 1), integer(row["reserved_finalize_bytes"], 1))


def require_first_full_checkpoint_binding_v1(value: object, budget: object, *,
    machine_id: str, first_control_sequence: int, baseline_completed_cycles: int,
    review_at_utc: str, budget_ref: ExactRefV1,
) -> FirstFullCheckpointPolicyV1:
    policy = parse_first_full_checkpoint_policy_v1(value)
    need(policy.machine_id == text(machine_id) and
         policy.first_control_sequence == integer(first_control_sequence, 1) and
         policy.baseline_completed_cycles == integer(baseline_completed_cycles, 0) and
         policy.review_at_utc == utc(review_at_utc) and policy.budget_ref == budget_ref,
         "first FULL policy bound to actual feeder admission")
    _require_budget_v1(policy, budget)
    return policy


def _require_budget_v1(policy: FirstFullCheckpointPolicyV1, value: object) -> None:
    budget = record(value)
    need(budget.get("machine_id") == policy.machine_id and
         datetime.fromisoformat(utc(budget.get("review_at_utc")).replace("Z", "+00:00")) >=
         datetime.fromisoformat(policy.review_at_utc.replace("Z", "+00:00")), "finalize budget machine/review")
    reservation = record(budget.get("first_full_checkpoint_reserve"),
        {"admissible", "seconds", "bytes", "reservation_mode"})
    need(reservation["admissible"] is True and
         integer(reservation["seconds"], 1, 86400) == policy.reserved_finalize_seconds and
         integer(reservation["bytes"], 1, (1 << 53) - 1) == policy.reserved_finalize_bytes and
         reservation["reservation_mode"] == "explicit_operator_admitted", "explicit source-bound finalize reservation")


class FinalizeMetadataIoV1(Protocol):
    def read(self, path: Path, limit: int) -> bytes: ...
    def create(self, path: Path, raw: bytes) -> None: ...
    def exists(self, path: Path) -> bool: ...


class LocalFinalizeMetadataIoV1:
    def read(self, path: Path, limit: int) -> bytes:
        integer(limit, 1, 1048576)
        before = path.stat()
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
            held = os.fstat(stream.fileno())
        after = path.stat()
        need(len(raw) <= limit and
             (before.st_ino, before.st_size, before.st_mtime_ns) ==
             (held.st_ino, held.st_size, held.st_mtime_ns) ==
             (after.st_ino, after.st_size, after.st_mtime_ns), "stable bounded finalize metadata")
        return raw

    def create(self, path: Path, raw: bytes) -> None:
        need(type(raw) is bytes and len(raw) <= 65536, "bounded finalize receipt")
        with path.open("xb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        need(self.read(path, 65536) == raw, "finalize exact write readback")

    def exists(self, path: Path) -> bool:
        return path.exists()


@runtime_checkable
class FinalizeQueueV1(Protocol):
    full_loop_state: dict[str, object]
    next_sequence: int
    loop_count: int
    launch: dict[str, object]
    _normal_cold: dict[str, object]
    async def generated(self, session: object, tool: str,
                        arguments: dict[str, object] | None = None) -> tuple[dict[str, object], Path]: ...
    def persist_loop_state(self) -> None: ...
    def finish_cumulative_checkpoint(self, saved: dict[str, object], response_path: Path) -> None: ...


def _bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def _object(raw: bytes) -> dict[str, object]:
    return record(json.loads(raw))


def require_first_full_checkpoint_policy_v1(queue: object, request: object, *,
    io: FinalizeMetadataIoV1 | None = None, now_utc: str | None = None,
    phase: Literal["before_full", "finalize"] = "before_full",
) -> FirstFullCheckpointPolicyV1:
    need(isinstance(queue, FinalizeQueueV1), "original Queue checkpoint capabilities")
    if not isinstance(queue, FinalizeQueueV1): raise ValueError("original Queue")
    policy = parse_first_full_checkpoint_policy_v1(record(queue._normal_cold["admission"])["first_full_checkpoint"])
    need(policy.machine_id == text(queue.launch.get("machine_id")), "finalize actual Game machine")
    row = record(request); sequence = integer(row.get("sequence"), 1)
    need(phase in ("before_full", "finalize"), "first FULL checkpoint phase")
    need(row.get("command") == "full_loop" and "tool" not in row, "finalize original FULL request")
    if phase == "before_full" and integer(queue.loop_count, 0) == 0:
        need(sequence == policy.first_control_sequence, "first FULL actual control matches checkpoint policy")
    storage = LocalFinalizeMetadataIoV1() if io is None else io
    raw = storage.read(Path(policy.budget_ref.path), 65536)
    need(len(raw) == policy.budget_ref.bytes and hashlib.sha256(raw).hexdigest() == policy.budget_ref.sha256,
         "finalize exact admitted budget")
    _require_budget_v1(policy, _object(raw))
    if sequence == policy.first_control_sequence:
        observed = integer(queue.full_loop_state.get("completed_cycles"), 0)
        need(observed == policy.baseline_completed_cycles if phase == "before_full"
             else observed > policy.baseline_completed_cycles,
             "first FULL checkpoint baseline")
    now = datetime.now(timezone.utc) if now_utc is None else datetime.fromisoformat(utc(now_utc).replace("Z", "+00:00"))
    remaining = (datetime.fromisoformat(policy.review_at_utc.replace("Z", "+00:00")) - now).total_seconds()
    need(remaining > (policy.reserved_finalize_seconds if sequence == policy.first_control_sequence
                      and phase == "before_full" else 0),
         "original review includes explicit finalize reserve")
    return policy


def first_full_checkpoint_cutoff_reached_v1(
    policy: FirstFullCheckpointPolicyV1, *, control_sequence: object,
    settled_cycles: object, state: object, now_utc: str | None = None,
) -> bool:
    """End first-FULL work at a settled boundary; in-flight work is never abandoned."""
    control = integer(control_sequence, 1)
    settled = integer(settled_cycles, 0)
    row = record(state)
    need({"pending_cycle", "pending_checkpoint"} <= set(row), "explicit cutoff pending state")
    if (control != policy.first_control_sequence or settled == 0
            or row["pending_cycle"] is not None or row["pending_checkpoint"] is not None):
        return False
    now = datetime.now(timezone.utc) if now_utc is None else datetime.fromisoformat(utc(now_utc).replace("Z", "+00:00"))
    cutoff = datetime.fromisoformat(policy.review_at_utc.replace("Z", "+00:00")) - timedelta(seconds=policy.reserved_finalize_seconds)
    return now >= cutoff


async def finalize_first_full_checkpoint_v1(queue: object, session: object, request: object, *,
    queue_root: Path, semantic_tool: str, save_tool: str,
    frame_reader: Callable[[object], dict[str, object]],
    io: FinalizeMetadataIoV1 | None = None, now_utc: str | None = None,
) -> JsonObject | None:
    storage = LocalFinalizeMetadataIoV1() if io is None else io
    policy = require_first_full_checkpoint_policy_v1(queue, request, io=storage, now_utc=now_utc, phase="finalize")
    if not isinstance(queue, FinalizeQueueV1): raise ValueError("original Queue")
    control = integer(record(request).get("sequence"), 1)
    if control != policy.first_control_sequence: return None
    state = queue.full_loop_state
    cycles = integer(state.get("completed_cycles"), 0)
    before = record(state.get("before")); date = integer(before.get("date_raw"), 0)
    need(cycles > policy.baseline_completed_cycles and state.get("pending_cycle") is None
         and state.get("pending_checkpoint") is None and state.get("terminal") is None,
         "first FULL settled without unresolved work")
    claim = queue_root / f"FIRST-FULL-CHECKPOINT-{control:06d}-STARTED.json"
    need(not storage.exists(claim), "original first FULL checkpoint cannot be resubmitted")
    at = datetime.now(timezone.utc).isoformat() if now_utc is None else utc(now_utc)
    storage.create(claim, _bytes({"machine_id": policy.machine_id, "observed_at_utc": at,
        "control_sequence": control, "completed_cycles": cycles, "status": "STARTED_NO_REPLAY"}))
    event_path = queue_root / f"CUMULATIVE-SAVE-{cycles:06d}.json"
    source = record(state.get("actual_saved_checkpoint_source") or {})
    # A SAVE already completed inside this exact FULL is reused, never repeated.
    if storage.exists(event_path):
        event = _object(storage.read(event_path, 16384))
        save_path = Path(text(event.get("save_response")))
        need(event.get("status") == "saved" and event.get("global_turn") == cycles
             and source.get("global_turn") == cycles and source.get("save_response") == str(save_path)
             and save_path.parent == queue_root.parent / "p37-responses"
             and integer(int(save_path.name.split("-", 1)[0]), 1) > control,
             "same first FULL original checkpoint source")
    else:
        state["pending_checkpoint"] = {"global_turn": cycles, "save_sequence": None,
                                       "reason": "first_full_checkpoint_before_hold"}
        queue.persist_loop_state()
        snapshot, semantic_path = await queue.generated(session, semantic_tool)
        actual = frame_reader(snapshot)
        need(snapshot.get("paused") is True and not isinstance(snapshot.get("active_event"), dict)
             and not isinstance(snapshot.get("pending_character_interaction"), dict)
             and all(actual.get(k) == before.get(k) for k in ("date_raw", "actor_character_id", "episode_run_id")),
             "first FULL safe-save original paused semantic")
        pending = record(state["pending_checkpoint"])
        pending["semantic_response"] = str(semantic_path)
        pending["save_sequence"] = integer(queue.next_sequence, 1)
        state["pending_checkpoint"] = pending; queue.persist_loop_state()
        saved, save_path = await queue.generated(session, save_tool,
            {"expected_revision": integer(snapshot.get("revision"), 1)})
        queue.finish_cumulative_checkpoint(saved, save_path)
        event = _object(storage.read(event_path, 16384))
    persisted_raw = storage.read(queue_root / "ROOT-CUMULATIVE-LOOP-STATE.json", 65536)
    persisted = _object(persisted_raw); checkpoint = record(event.get("checkpoint"))
    need(event.get("status") == "saved" and integer(event.get("global_turn"), 0) == cycles
         and checkpoint.get("date_raw") == date
         and checkpoint.get("episode_character_id") == before.get("actor_character_id")
         and checkpoint.get("episode_run_id") == before.get("episode_run_id")
         and persisted.get("actual_saved_checkpoint") == checkpoint
         and state.get("actual_saved_checkpoint") == checkpoint
         and persisted.get("actual_saved_checkpoint_source") == {"global_turn": cycles,
             "semantic_response": event.get("semantic_response"), "save_response": event.get("save_response")}
         and persisted.get("pending_cycle") is None and persisted.get("pending_checkpoint") is None
         and persisted.get("completed_cycles") == cycles and persisted.get("before") == before,
         "original checkpoint event and persisted state exact readback")
    receipt: JsonObject = {"schema": RECEIPT_SCHEMA, "machine_id": policy.machine_id,
        "observed_at_utc": at, "status": "CHECKPOINT_VERIFIED", "control_sequence": control,
        "completed_cycles": cycles, "date_raw": date, "checkpoint_summary": {
            "date_raw": integer(checkpoint.get("date_raw"), 0, (1 << 53) - 1),
            "history_index": integer(checkpoint.get("history_index"), 0, (1 << 53) - 1),
            "size": integer(checkpoint.get("size"), 1, (1 << 53) - 1),
            "sha256": text(checkpoint.get("sha256"))},
        "semantic_response": text(event.get("semantic_response")), "save_response": text(event.get("save_response")),
        "event_path": str(event_path), "state_sha256": hashlib.sha256(persisted_raw).hexdigest(),
        "ordinary_cycle_credit": 0, "game_day_credit": 0, "original_actions_replayed": False}
    storage.create(queue_root / f"FIRST-FULL-CHECKPOINT-{control:06d}-VERIFIED.json", _bytes(receipt))
    return receipt


def require_first_full_checkpoint_hold_v1(result: object, control_sequence: int, *, expected_machine_id: str) -> None:
    row = record(result); proof = record(row.get("first_full_checkpoint"), {
        "schema", "machine_id", "observed_at_utc", "status", "control_sequence",
        "completed_cycles", "date_raw", "checkpoint_summary", "semantic_response", "save_response",
        "event_path", "state_sha256", "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed"})
    checkpoint = record(proof["checkpoint_summary"], {"date_raw", "history_index", "size", "sha256"})
    utc(proof["observed_at_utc"])
    integer(checkpoint["history_index"], 0, (1 << 53) - 1)
    integer(checkpoint["size"], 1, (1 << 53) - 1)
    for key, value in (("checkpoint SHA", checkpoint["sha256"]), ("state SHA", proof["state_sha256"])):
        need(re.fullmatch("[0-9a-f]{64}", text(value)) is not None, key)
    paths: list[PureWindowsPath | PurePosixPath] = []
    for key in ("semantic_response", "save_response", "event_path"):
        value = text(proof[key])
        path: PureWindowsPath | PurePosixPath = PureWindowsPath(value) if PureWindowsPath(value).is_absolute() else PurePosixPath(value)
        need(path.is_absolute() and ".." not in path.parts, "absolute original checkpoint evidence path")
        paths.append(path)
    semantic, saved, event = paths
    need(semantic.parent == saved.parent and semantic.parent.name == "p37-responses"
         and event.parent == saved.parent.parent / "p37-queue"
         and event.name == f"CUMULATIVE-SAVE-{integer(proof['completed_cycles'], 0):06d}.json",
         "same runtime checkpoint evidence paths")
    numbers: list[int] = []
    for path in (semantic, saved):
        need(re.fullmatch("[0-9]{4,}-1-result[.]json", path.name) is not None, "original response filename")
        numbers.append(integer(int(path.name.split("-", 1)[0]), 1, (1 << 53) - 1))
    need(integer(control_sequence, 1) < numbers[0] < numbers[1], "original SEM then SAVE after first FULL")
    need(proof.get("schema") == RECEIPT_SCHEMA and proof.get("status") == "CHECKPOINT_VERIFIED"
         and text(proof.get("machine_id")) == text(expected_machine_id)
         and integer(proof.get("control_sequence"), 1) == integer(control_sequence, 1)
         and integer(proof.get("completed_cycles"), 0) == integer(row.get("cumulative_cycles"), 0)
         and integer(proof.get("date_raw"), 0) == integer(row.get("actual_end_date_raw"), 0)
         and integer(checkpoint.get("date_raw"), 0) == integer(proof["date_raw"], 0)
         and integer(proof.get("ordinary_cycle_credit"), 0, 0) == 0
         and integer(proof.get("game_day_credit"), 0, 0) == 0
         and proof.get("original_actions_replayed") is False, "verified first FULL checkpoint before HOLD")


def render_first_full_checkpoint_queue_v1(material: bytes) -> bytes:
    source = material.decode("utf-8"); tree = ast.parse(source)
    methods = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "full_loop"
               and any(isinstance(x, ast.Name) and x.id == "control_sequence" for x in ast.walk(n))]
    need(len(methods) == 1 and "_first_checkpoint_v1" not in source, "unique original first FULL queue seam")
    node = methods[0]; lines = source.splitlines(keepends=True)
    consume = [n for n in node.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "control_sequence" for t in n.targets)]
    result = [n for n in node.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "result" for t in n.targets)]
    need(len(consume) == len(result) == 1, "original consume and final response assignments")
    insertion = result[0].lineno - 1
    end = result[0].end_lineno
    need(end is not None, "original result extent")
    if end is None: raise ValueError("result extent")
    lines[end:end] = ['        result["first_full_checkpoint"] = _first_checkpoint_receipt_v1\n']
    lines[insertion:insertion] = [
        '        _first_checkpoint_receipt_v1 = await _first_checkpoint_v1.finalize_first_full_checkpoint_v1(self, session, request, queue_root=Q, semantic_tool=SEMANTIC, save_tool=SAVE, frame_reader=lambda body: frame(body, semantic=True, expected_lifecycle=self.expected_lifecycle_binding))\n']
    gates = [n for n in ast.walk(node) if isinstance(n, ast.If)
             and len(n.body) == 1 and isinstance(n.body[0], ast.Break)
             and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                     and x.func.attr == "should_finish" for x in ast.walk(n.test))]
    need(len(gates) == 2, "two original settled generated-budget gates")
    gate = min(gates, key=lambda item: item.lineno)
    indent = " " * gate.col_offset
    lines[gate.lineno - 1:gate.lineno - 1] = [
        indent + 'if _first_checkpoint_v1.first_full_checkpoint_cutoff_reached_v1(_first_checkpoint_policy_v1, control_sequence=control_sequence, settled_cycles=settled, state=state):\n' + indent + '    break\n']
    lines[consume[0].lineno - 1:consume[0].lineno - 1] = [
        '        _first_checkpoint_policy_v1 = _first_checkpoint_v1.require_first_full_checkpoint_policy_v1(self, request)\n']
    futures = [n.end_lineno or n.lineno for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == "__future__"]
    lines[max(futures, default=0):max(futures, default=0)] = [
        'from tools.g2_saved_campaign import first_full_checkpoint_v1 as _first_checkpoint_v1\n']
    rendered = "".join(lines); compile(rendered, "<first FULL queue>", "exec")
    return rendered.encode()


def render_first_full_checkpoint_hold_v1(material: bytes) -> bytes:
    source = material.decode("utf-8"); tree = ast.parse(source)
    holds = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "c23_first_batch_hold"]
    need(len(holds) == 1, "one actual first FULL HOLD entry")
    lines = source.splitlines(keepends=True)
    lines.insert(holds[0].lineno, '    from tools.g2_saved_campaign.first_full_checkpoint_v1 import require_first_full_checkpoint_hold_v1\n    require_first_full_checkpoint_hold_v1(result, sequence, expected_machine_id=v["machine_id"])\n')
    output = "".join(lines); compile(output, "<first FULL HOLD>", "exec")
    return output.encode()
