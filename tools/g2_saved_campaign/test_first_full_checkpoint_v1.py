"""RAM integration of the archived Queue exit, original finish, and HOLD gate."""
from __future__ import annotations
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Protocol, runtime_checkable
from types import SimpleNamespace
import unittest

from tools.g2_saved_campaign import first_full_checkpoint_v1 as f
from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1, record
from tools.g2_saved_campaign.current_saved_campaign_preflight_v1 import decode_current_saved_historical_payload_v1

MACHINE = "fixture-machine"
NOW = "2026-10-22T05:00:00Z"
REVIEW = "2026-10-22T05:15:00Z"
ROOT = Path("D:/fixture/runtime")
Q = ROOT / "p37-queue"
HOLD_MATERIAL = b'def c23_first_batch_hold(v, sequence, result, response, fields):\n    expected = c23_gate_expected(v, sequence, result, response, fields)\n    marker = Path(v["continue_marker"])\n    status("root_review_hold", control_sequence=sequence, first_batch=expected,\n        next_control_sequence=result["next_sequence"], continue_marker=str(marker),\n        game_sdk_obs_calls=0, next_FULL_published=False)\n    while True:\n        if STOP.exists() or (N / "REQUEST-ADMISSION-CLOSED-C23").exists() or (N / "EXIT-SDK-P37C23").exists():\n            status("operator_stopped", control_sequence=sequence, first_batch_hold=True)\n            return False\n        if datetime.now(timezone.utc) >= datetime.fromisoformat(v["review_deadline_utc"].replace("Z", "+00:00")):\n            status("operator_stopped", control_sequence=sequence, first_batch_hold=True, original_review_deadline_reached=True)\n            return False\n        if marker.exists():\n            return c23_accept_continue(c23_checked_file(marker, 16384), expected)\n        time.sleep(.2)\n'


def wire(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class MemoryIo:
    def __init__(self) -> None:
        self.raw: dict[Path, bytes] = {}

    def read(self, path: Path, limit: int) -> bytes:
        value = self.raw[path]
        if len(value) > limit: raise ValueError("bounded metadata")
        return value

    def create(self, path: Path, raw: bytes) -> None:
        if path in self.raw: raise FileExistsError(path)
        self.raw[path] = raw

    def exists(self, path: Path) -> bool:
        return path in self.raw


@runtime_checkable
class Finish(Protocol):
    def __call__(self, queue: object, saved: dict[str, object], response_path: Path) -> None: ...


@runtime_checkable
class Exit(Protocol):
    async def __call__(self, queue: object, session: object,
                       request: dict[str, object], path: Path) -> dict[str, object]: ...


class QueueFixture:
    def __init__(self, io: MemoryIo, finish: Finish) -> None:
        self.io = io; self.finish = finish
        self.next_sequence = 163
        self.launch: dict[str, object] = {"machine_id": MACHINE}
        budget = {"machine_id": MACHINE, "review_at_utc": REVIEW,
            "first_full_checkpoint_reserve": {"admissible": True, "seconds": 30,
                "bytes": 1048576, "reservation_mode": "explicit_operator_admitted"}}
        raw = wire(budget); path = ROOT / "budget.json"; io.raw[path] = raw
        self.policy = f.FirstFullCheckpointPolicyV1(MACHINE, 101, 20, REVIEW,
            ExactRefV1(str(path), len(raw), hashlib.sha256(raw).hexdigest()), 30, 1048576)
        self._normal_cold: dict[str, object] = {"admission": {"first_full_checkpoint": self.policy.to_wire()}}
        self.full_loop_state: dict[str, object] = {"completed_cycles": 50, "start_date_raw": 900,
            "before": {"date_raw": 1000, "actor_character_id": 12, "episode_run_id": "ep"},
            "pending_cycle": None, "pending_checkpoint": None, "terminal": None,
            "counts": {"checkpoint_saved": 2}, "actual_saved_checkpoint_source": None}
        self.calls: list[str] = []
        self.recording_stopped = False; self.save_unknown = False
        self.wrong_semantic = False
        self.loop_count = 1; self.held_control: str | None = "0101-1-result.json"
        self.persist_loop_state()

    def persist_loop_state(self) -> None:
        self.io.raw[Q / "ROOT-CUMULATIVE-LOOP-STATE.json"] = wire(self.full_loop_state)

    def finish_cumulative_checkpoint(self, saved: dict[str, object], response_path: Path) -> None:
        self.finish(self, saved, response_path)

    async def generated(self, session: object, tool: str,
                        arguments: dict[str, object] | None = None) -> tuple[dict[str, object], Path]:
        del session
        if self.recording_stopped: raise RuntimeError("RecordingPaused")
        self.calls.append(tool)
        path = ROOT / "p37-responses" / f"{self.next_sequence:04d}-1-result.json"
        self.next_sequence += 1
        if tool == "SEM":
            row = {"paused": True, "revision": 7, **record(self.full_loop_state["before"])}
            if self.wrong_semantic: row["date_raw"] = 999
            return row, path
        if tool != "SAVE" or arguments != {"expected_revision": 7}: raise ValueError("wrong SAVE binding")
        if self.save_unknown: raise TimeoutError("SAVE original result unknown")
        return {"checkpoint": {"status": "saved", "date_raw": 1000,
            "episode_character_id": 12, "episode_run_id": "ep", "sha256": "a" * 64,
            "history_index": 80, "size": 100}}, path


def production() -> tuple[Finish, Exit]:
    archive = json.loads((Path(__file__).parent / "test_data/current_saved_sem11373_postcheck_v1.json").read_bytes())
    _, material = decode_current_saved_historical_payload_v1(archive["payloads"]["queue"])
    rendered = f.render_first_full_checkpoint_queue_v1(material)
    tree = ast.parse(rendered)
    finish = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "finish_cumulative_checkpoint")
    full = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "full_loop"
        and any(isinstance(x, ast.Name) and x.id == "_first_checkpoint_receipt_v1" for x in ast.walk(n)))
    # Execute the original final-response block. Planner/native boundaries are not replayed.
    first = next(i for i,n in enumerate(full.body) if isinstance(n, ast.Assign)
        and any(isinstance(x, ast.Name) and x.id == "_first_checkpoint_receipt_v1" for x in n.targets))
    body = full.body[first:]
    head = ast.parse("async def exit_queue(self, session, request, path):\n state=self.full_loop_state\n settled=30\n control_sequence=request['sequence']\n").body[0]
    if not isinstance(head, ast.AsyncFunctionDef): raise ValueError("test async boundary")
    head.body.extend(body)
    module = ast.fix_missing_locations(ast.Module(body=[finish, head], type_ignores=[]))
    namespace: dict[str, object] = {"__builtins__": __builtins__, "copy": copy, "Q": Q,
        "OUTBOX": ROOT / "p37-responses", "SEMANTIC": "SEM", "SAVE": "SAVE",
        "frame": lambda value, **kw: record(value),
        "_current_full_row_fields_v1": lambda: {},
        "checkpoint_saved": lambda state, checkpoint: None}
    exec(compile(module, "<archived original Queue exit>", "exec"), namespace)
    fn = namespace["finish_cumulative_checkpoint"]; exit_fn = namespace["exit_queue"]
    if not isinstance(fn, Finish) or not isinstance(exit_fn, Exit): raise ValueError("actual executable Queue functions")
    # Bind per-fixture IO only; execute the actual inserted finalizer and original finish.
    class Boundary:
        io: MemoryIo
        async def finalize_first_full_checkpoint_v1(self, queue: object, session: object, request: object,
                *, queue_root: Path, semantic_tool: str, save_tool: str,
                frame_reader: object) -> object:
            del frame_reader
            if not isinstance(queue, QueueFixture): raise ValueError("fixture Queue")
            namespace["atomic"] = lambda path, value, **kw: queue.io.create(path, wire(value))
            return await f.finalize_first_full_checkpoint_v1(queue, session, request,
                queue_root=queue_root, semantic_tool=semantic_tool, save_tool=save_tool,
                frame_reader=record, io=queue.io, now_utc=NOW)
    namespace["_first_checkpoint_v1"] = Boundary()
    return fn, exit_fn


class FirstFullCheckpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_archived_queue_exit_original_finish_then_verified_hold(self) -> None:
        finish, exit_fn = production(); io = MemoryIo(); q = QueueFixture(io, finish)
        result = await exit_fn(q, None, {"sequence": 101, "command": "full_loop"}, ROOT / "p37-responses/0101-1-result.json")
        f.require_first_full_checkpoint_hold_v1(result, 101, expected_machine_id=MACHINE)
        status: list[object] = []
        namespace: dict[str, object] = {"Path": Path, "N": ROOT,
            "STOP": SimpleNamespace(exists=lambda: True),
            "status": lambda value, **kw: status.append(value),
            "c23_gate_expected": lambda *args: {}}
        exec(compile(f.render_first_full_checkpoint_hold_v1(HOLD_MATERIAL),
                     "<actual frozen HOLD consumer>", "exec"), namespace)
        hold = namespace["c23_first_batch_hold"]
        if not callable(hold): raise ValueError("actual HOLD entry")
        hold({"machine_id": MACHINE, "continue_marker": str(ROOT / "continue")},
             101, result, ROOT / "response.json", {})
        self.assertEqual(status, ["root_review_hold", "operator_stopped"])
        status.clear()
        with self.assertRaises(ValueError):
            hold({"machine_id": MACHINE}, 101, {}, ROOT / "response.json", {})
        self.assertEqual(status, [])
        for key in record(result["first_full_checkpoint"]):
            changed = copy.deepcopy(result); proof = record(changed["first_full_checkpoint"])
            del proof[key]; changed["first_full_checkpoint"] = proof
            with self.assertRaises(ValueError):
                f.require_first_full_checkpoint_hold_v1(changed, 101, expected_machine_id=MACHINE)
        for key, value in (("observed_at_utc", True), ("semantic_response", "relative.json"),
                           ("save_response", 1), ("event_path", "../event.json"), ("state_sha256", "bad")):
            changed = copy.deepcopy(result); proof = record(changed["first_full_checkpoint"])
            proof[key] = value; changed["first_full_checkpoint"] = proof
            with self.assertRaises(ValueError):
                f.require_first_full_checkpoint_hold_v1(changed, 101, expected_machine_id=MACHINE)
        for checkpoint_key, checkpoint_value in (("history_index", True), ("history_index", 1.0), ("size", "100"), ("size", False), ("sha256", "bad")):
            changed = copy.deepcopy(result); proof = record(changed["first_full_checkpoint"])
            checkpoint = record(proof["checkpoint_summary"]); checkpoint[checkpoint_key] = checkpoint_value
            proof["checkpoint_summary"] = checkpoint; changed["first_full_checkpoint"] = proof
            with self.assertRaises(ValueError):
                f.require_first_full_checkpoint_hold_v1(changed, 101, expected_machine_id=MACHINE)
        f.require_first_full_checkpoint_hold_v1(json.loads(wire(result)), 101, expected_machine_id=MACHINE)
        for key, value in (("control_sequence", True), ("machine_id", "other"), ("date_raw", 999)):
            changed = copy.deepcopy(result); proof = record(changed["first_full_checkpoint"])
            proof[key] = value; changed["first_full_checkpoint"] = proof
            with self.assertRaises(ValueError):
                f.require_first_full_checkpoint_hold_v1(changed, 101, expected_machine_id=MACHINE)
        self.assertEqual(q.calls, ["SEM", "SAVE"])
        self.assertEqual(q.full_loop_state["completed_cycles"], 50)
        self.assertEqual(record(q.full_loop_state["counts"])["checkpoint_saved"], 3)
        self.assertIsNone(q.full_loop_state["pending_checkpoint"])
        with self.assertRaisesRegex(ValueError, "cannot be resubmitted"):
            await exit_fn(q, None, {"sequence": 101, "command": "full_loop"}, ROOT / "duplicate.json")
        self.assertEqual(q.calls, ["SEM", "SAVE"])

    async def test_recording_terminal_and_unknown_save_never_hold_or_repeat(self) -> None:
        for kind in ("recording", "unknown", "wrong_semantic"):
            finish, exit_fn = production(); io = MemoryIo(); q = QueueFixture(io, finish)
            q.recording_stopped = kind == "recording"; q.save_unknown = kind == "unknown"
            q.wrong_semantic = kind == "wrong_semantic"
            request: dict[str, object] = {"sequence": 101, "command": "full_loop"}
            with self.assertRaises((RuntimeError, TimeoutError, ValueError)):
                await exit_fn(q, None, request, ROOT / "out.json")
            self.assertEqual(q.full_loop_state["completed_cycles"], 50)
            self.assertEqual(record(q.full_loop_state["counts"])["checkpoint_saved"], 2)
            calls = list(q.calls)
            with self.assertRaises(ValueError): await exit_fn(q, None, request, ROOT / "again.json")
            self.assertEqual(q.calls, calls)

    async def test_policy_roundtrip_wrong_scalar_binding_and_missing_proof(self) -> None:
        finish, _ = production(); io = MemoryIo(); q = QueueFixture(io, finish)
        self.assertEqual(f.parse_first_full_checkpoint_policy_v1(json.loads(wire(q.policy.to_wire()))), q.policy)
        for key, value in (("first_control_sequence", True), ("reserved_finalize_bytes", 1.0),
                           ("checkpoint_before_hold", None)):
            row: dict[str, object] = dict(q.policy.to_wire()); row[key] = value
            with self.assertRaises(ValueError): f.parse_first_full_checkpoint_policy_v1(row)
        with self.assertRaises(ValueError):
            f.require_first_full_checkpoint_hold_v1({"cumulative_cycles": 50, "actual_end_date_raw": 1000},
                101, expected_machine_id=MACHINE)
        q.loop_count = 0; q.full_loop_state["completed_cycles"] = 20
        with self.assertRaisesRegex(ValueError, "actual control matches"):
            f.require_first_full_checkpoint_policy_v1(q, {"sequence": 102, "command": "full_loop"}, io=io, now_utc=NOW)
        self.assertEqual(q.calls, [])

    async def test_current_plan_requires_deployed_shared_source(self) -> None:
        from tools.g2_saved_campaign.test_current_saved_campaign_cold_v1 import plan
        from tools.g2_saved_campaign import prepare_current_saved_campaign_cold_v1 as producer
        current = plan()
        self.assertEqual(len(current.source_rows), 15)
        self.assertEqual(producer.MAX_CURRENT_SAVED_CLOSURE_V1, 67)
        self.assertEqual(producer.parse_plan_v1(current.to_wire()), current)
        old = current.to_wire()
        old["source_rows"] = [r.to_wire() for r in current.source_rows
            if not r.relative_path.endswith("/first_full_checkpoint_v1.py")]
        with self.assertRaises(ValueError): producer.parse_plan_v1(old)


if __name__ == "__main__": unittest.main()
